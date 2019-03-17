import argparse
import tkinter as tk
from collections import namedtuple
from queue import Queue
from threading import Thread
from tkinter import ttk, messagebox
from xml.etree import ElementTree
import sys

from PIL import ImageTk
import numpy as np

import camera
import renderer
import osm_helper


def log(*msg, level=0, **kwargs):
    global loglevel
    if level >= loglevel:
        print(['[info]', '[warn]', '[error]', '[critical]'][level], *msg, **kwargs)


_status = namedtuple('gui_worker_status', ('progress', 'status_message'))


class Gui:
    def __init__(self, file, dimensions, center=None, zoom=None):
        self.worker = GuiWorker()
        self.worker.task_load_map(file)
        if center is not None:
            self.worker.task_center_gps(center, setdefault=True)
        if zoom is not None:
            self.worker.task_zoom_set(zoom, setdefault=True)

        self.running = False
        self._raw_image, self._image = None, None

        self.root = tk.Tk()
        self.root.geometry('x'.join(map(str, dimensions)))
        self.root.bind('<Destroy>', func=lambda e: self.exit() if e.widget == self.root else None)

        self.panel = tk.Label(self.root)
        self.panel.bind('<ButtonRelease-2>', func=lambda e: self.worker.task_center((e.x, e.y)))
        self.panel.bind('<ButtonRelease-1>', func=lambda e: self.worker.task_zoom_in((e.x, e.y)))
        self.panel.bind('<ButtonRelease-3>', func=lambda e: self.worker.task_zoom_out((e.x, e.y)))
        self.panel.bind('<Configure>', func=lambda e: self.worker.task_resize(e.width, e.height))
        self.panel.grid(row=0, column=0, columnspan=2, sticky='nesw')
        self.root.rowconfigure(index=0, weight=1)
        self.root.bind('<p>', func=lambda e: self.worker.task_zoom_in(self.size / 2))
        self.root.bind('<o>', func=lambda e: self.worker.task_zoom_out(self.size / 2))
        self.root.bind('<Left>', func=lambda e: self.worker.task_center(self.size * (0.3, 0.5)))
        self.root.bind('<Right>', func=lambda e: self.worker.task_center(self.size * (0.7, 0.5)))
        self.root.bind('<Up>', func=lambda e: self.worker.task_center(self.size * (0.5, 0.3)))
        self.root.bind('<Down>', func=lambda e: self.worker.task_center(self.size * (0.5, 0.7)))

        self.status = tk.Label(self.root, bd=1, relief='sunken', anchor='w')
        self.status.grid(row=1, column=0, sticky='nesw')
        self.root.columnconfigure(index=0, weight=1)

        self.progress = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress, max=1.0)
        self.progress_bar.grid(row=1, column=1, sticky='nesw')

        self.menu = tk.Menu(self.root)

        self.menu_file = tk.Menu(self.menu, tearoff=0)
        self.menu_file.add_command(label="Exit", command=self.root.destroy)
        self.menu.add_cascade(label='File', menu=self.menu_file)

        self.menu_view = tk.Menu(self.menu, tearoff=0)
        self.menu_view.add_command(label="Recenter", command=self.worker.task_center_restore)
        self.menu_view.add_command(label="Reset Zoom", command=self.worker.task_zoom_restore)
        self.menu_view.add_command(label="Zoom In", command=lambda: self.worker.task_zoom_in(self.size / 2))
        self.menu_view.add_command(label="Zoom Out", command=lambda: self.worker.task_zoom_out(self.size / 2))
        self.menu.add_cascade(label='View', menu=self.menu_view)

        self.menu_help = tk.Menu(self.menu, tearoff=0)
        if arg_parser is not None:
            self.menu_help.add_command(label='Launch Options...', command=self.menu_help_args)
        self.menu_help.add_command(label='Controls...', command=self.menu_help_controls)
        self.menu_help.add_command(label="About...", command=self.menu_help_about)
        self.menu.add_cascade(label='Help', menu=self.menu_help)

        self.root.config(menu=self.menu)

    def start(self):
        self.root.update()
        Thread(name='worker', target=self.worker.run).start()

        self.running = True
        while self.running:
            self.root.update()
            while not self.worker.queue_status.empty():
                status: _status = self.worker.queue_status.get(block=False)
                self.progress.set(status.progress)
                self.status.config(text=status.status_message)
            while not self.worker.queue_results.empty():
                self._raw_image = self.worker.queue_results.get(block=False)
                self._image = ImageTk.PhotoImage(self._raw_image)
                self.panel.configure(image=self._image)

    def exit(self):
        self.worker(lambda: sys.exit(0))
        self.running = False

    @property
    def size(self):
        return np.array((self.panel.winfo_width(), self.panel.winfo_height()))

    @staticmethod
    def menu_help_about():
        if arg_parser is None:
            messagebox.showinfo(title='About', message='Map viewer GUI made by Nulano.')
        else:
            messagebox.showinfo(title='About', message=arg_parser.description)

    @staticmethod
    def menu_help_controls():
        messagebox.showinfo(title='Controls', message=
                            'Left-click to zoom in to point\n'
                            'Right-click to zoom out to point\n'
                            'Middle-click to center at point\n\n'
                            '<P> and <O> to zoom in and out\n'
                            'Arrow keys to move around')

    @staticmethod
    def menu_help_args():
        if arg_parser is None:
            log('arg_parser is None', level=1)
        else:
            messagebox.showinfo(title='Launch Options', message=arg_parser.format_help())


def _worker_task(func):
    def wrap(self, *args, **kwargs):
        self(lambda: func(self, *args, **kwargs))
    return wrap


class GuiWorker:
    def __init__(self):
        self.queue_tasks = Queue()
        self.queue_status = Queue()
        self.queue_results = Queue()

        self.camera = None
        self.renderer = None
        self.settings = {}

        renderer.nulano_gui_callback = self._status

    def __call__(self, task):
        self.queue_tasks.put(task)

    def run(self):
        while True:
            self._process_tasks()
            self._render()

    def _status(self, group: str = None, status: str = None, current: int = 0, maximum: int = 0):
        message = None if maximum == 0 else '{}/{}'.format(current, maximum)

        if status is not None:
            message = status if message is None else '{} ({})'.format(status, message)

        if group is not None:
            message = group if message is None else '{}: {}'.format(group, message)

        if message is not None:
            log(message)

        self.queue_status.put(_status(current / maximum if maximum != 0 else current, message))
    
    def _process_tasks(self):
        while True:
            self.queue_tasks.get(block=True)()
            if self.queue_tasks.empty():
                return
    
    def _render(self):
        log('-- rendering...')
        self.queue_results.put(self.renderer.render())
        center_deg = self.camera.px_to_gps((self.camera.px_width / 2, self.camera.px_height / 2))
        log('-- rendering done')
        self._status(status='lat={}, lon={}, zoom={}, px/m={}'
                            .format(center_deg[0], center_deg[1], self.camera.zoom_level, self.camera.px_per_meter()))

    @_worker_task
    def task_load_map(self, file):
        try:
            log('-- loading map:', file)
            self._status(status='parsing xml')
            element_tree = ElementTree.parse(file)
            self.camera = camera.Camera()
            self.renderer = renderer.Renderer(self.camera, element_tree)
            self.settings = {}
            self.renderer.center_camera()
            self.settings['zoom'] = self.camera.zoom_level
            log('-- map loaded')
        except FileNotFoundError:
            log('File {} does not exist.'.format(file), level=3)
            log(level=3)
            log('Use "{0} -f FILE" to specify a map file or "{0} -h" to show help.'.format(sys.argv[0]), level=3)
            sys.exit(1)

    @_worker_task
    def task_resize(self, width, height):
        self.camera.px_width, self.camera.px_height = width, height

    @_worker_task
    def task_center(self, point):
        self.camera.center_at(*self.camera.px_to_gps(point))

    @_worker_task
    def task_center_gps(self, point, setdefault=False):
        self.camera.center_at(*point)
        if setdefault:
            self.settings['center'] = point

    @_worker_task
    def task_center_restore(self):
        if 'center' in self.settings:
            self.camera.center_at(*self.settings['center'])
        else:
            self.renderer.center_camera()

    @_worker_task
    def task_zoom_in(self, point):
        self.camera.zoom_in(point)

    @_worker_task
    def task_zoom_out(self, point):
        self.camera.zoom_out(point)

    @_worker_task
    def task_zoom_set(self, zoom, setdefault=False):
        self.camera.zoom_level = zoom
        if setdefault:
            self.settings['zoom'] = zoom

    @_worker_task
    def task_zoom_restore(self):
        self.camera.zoom_level = self.settings['zoom']


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='OSM Map viewer GUI made by Nulano (2019)')
    arg_parser.add_argument('-f', '--map', default='maps/bratislava.osm', help='the OpenStreetMap xml file to use', dest='file')
    arg_parser.add_argument('-q', action='store_const', const=1, default=0, help='suppress info messages', dest='loglevel')
    arg_parser.add_argument('-Q', action='store_const', const=100, help='suppress ALL messages', dest='loglevel')
    arg_parser.add_argument('--dimensions', default=(800, 600), nargs=2, type=int, help='use this resolution at startup', metavar=('X', 'Y'))
    arg_parser.add_argument('--center', nargs=2, type=float, help='center map at %(metavar) at startup', metavar=('LAT', 'LON'))
    arg_parser.add_argument('--zoom', type=int, help='zoom map at level %(metavar) at startup', metavar='ZOOM')
    args = arg_parser.parse_args()

    loglevel = args.loglevel
    osm_helper.nulano_log = log

    gui = Gui(file=args.file, dimensions=args.dimensions, center=args.center, zoom=args.zoom)
    gui.start()
