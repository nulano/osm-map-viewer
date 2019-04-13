import argparse
import tkinter as tk
from operator import itemgetter
from queue import Queue
from threading import Thread
from tkinter import ttk, messagebox, filedialog
from xml.etree import ElementTree
import sys

from PIL import ImageTk, ImageDraw
import numpy as np
from PIL import Image

import camera
from location_filter import Rectangle
import renderer
import osm_helper

loglevel = 0


def log(*msg, level=0, **kwargs):
    global loglevel
    if level >= loglevel:
        print(['[info]', '[warn]', '[error]', '[critical]'][level], *msg, **kwargs)


def start():
    global loglevel, arg_parser
    arg_parser = argparse.ArgumentParser(description='OSM Map viewer GUI made by Nulano (2019)')
    arg_parser.add_argument('-f', '--map', default='maps/bratislava.osm', help='the OpenStreetMap xml file to use', dest='file')
    arg_parser.add_argument('-q', action='store_const', const=1, default=0, help='suppress info messages', dest='loglevel')
    arg_parser.add_argument('-Q', action='store_const', const=100, help='suppress ALL messages', dest='loglevel')
    arg_parser.add_argument('--dimensions', default=(800, 600), nargs=2, type=int, help='use this resolution at startup', metavar=('X', 'Y'))
    arg_parser.add_argument('--center', nargs=2, type=float, help='center map at %(metavar)s at startup', metavar=('LAT', 'LON'))
    arg_parser.add_argument('--zoom', type=int, help='zoom map at level %(metavar)s at startup', metavar='ZOOM')
    arg_parser.add_argument('-F', '--search', help='search for object named %(metavar)s', dest='search_name', metavar='NAME')
    args = arg_parser.parse_args()

    loglevel = args.loglevel
    osm_helper.nulano_log = log  # patch osm_helper
    renderer.nulano_gui_log = log  # patch renderer

    gui = Gui(file=args.file, dimensions=args.dimensions)
    if args.search_name is not None:
        gui.worker.task_search_name(args.search_name)
    if args.center is not None:
        gui.worker.task_center_gps(args.center, setdefault=True)
    if args.zoom is not None:
        gui.worker.task_zoom_set(args.zoom, setdefault=True)
    gui.start()


def _worker_callback(func):
    def wrap(self, *args, **kwargs):
        self.queue_callback.put(lambda: func(self, *args, **kwargs))
    return wrap


def show_dialog(root, title, lines: dict, callback, text_submit='OK', text_cancel='Cancel'):
    dialog = tk.Toplevel(root, padx=5, pady=5)
    dialog.title(title)

    entries = []

    def submit(event=None):
        if callback(*[entry.get() for entry in entries]) != False:
            dialog.destroy()

    for row, (text, hint) in enumerate(lines.items()):
        label = tk.Label(dialog, text=text)
        label.grid(row=row, column=0, sticky='w')
        entry = tk.Entry(dialog)
        entry.insert(0, hint)
        entry.grid(row=row, column=1, sticky='we')
        entries.append(entry)

    buttons = tk.Frame(dialog, padx=5)
    btn_submit = tk.Button(buttons, text=text_submit)
    btn_submit.grid(row=0, column=0, sticky='nesw')
    buttons.columnconfigure(0, weight=1)
    if text_cancel is not None:
        btn_cancel = tk.Button(buttons, text=text_cancel, command=lambda: dialog.destroy())
        btn_cancel.grid(row=0, column=1, sticky='nesw')
        buttons.columnconfigure(1, weight=1)
    buttons.grid(row=len(lines), column=0, columnspan=2, sticky='nesw')
    btn_submit.config(command=submit)

    dialog.bind('<Return>', submit)
    dialog.transient(root)
    dialog.resizable(False, False)
    dialog.grab_set()
    dialog.update()

    x, y = root.winfo_rootx() + root.winfo_width() // 2, root.winfo_rooty() + root.winfo_height() // 2
    dialog.geometry('+{}+{}'.format(x - dialog.winfo_width() // 2, y - dialog.winfo_height() // 2))


class Gui:
    def __init__(self, file, dimensions):
        self.queue_callback = Queue()
        self.worker = GuiWorker(self)
        self.worker.task_load_map(file)

        self.root = tk.Tk()
        self.root.winfo_toplevel().title('OSM Map Viewer')
        self.root.geometry('x'.join(map(str, dimensions)))
        self.root.bind('<Destroy>', func=lambda e: self.exit() if e.widget == self.root else None)

        self.panel = tk.Label(self.root)
        self.panel.bind('<ButtonRelease-2>', func=lambda e: self.action_center((e.x, e.y)))
        self.panel.bind('<ButtonRelease-1>', func=lambda e: self.action_zoom_in((e.x, e.y)))
        self.panel.bind('<ButtonRelease-3>', func=lambda e: self.action_zoom_out((e.x, e.y)))
        self.panel.bind('<Configure>', func=lambda e: self.action_resize((e.width, e.height)))
        self.panel.grid(row=0, column=0, columnspan=2, sticky='nesw')
        self.root.rowconfigure(index=0, weight=1)
        self.root.bind('<p>', func=lambda e: self.action_zoom_in(self.size / 2))
        self.root.bind('<o>', func=lambda e: self.action_zoom_out(self.size / 2))
        self.root.bind('<Left>', func=lambda e: self.action_center(self.size * (0.3, 0.5)))
        self.root.bind('<Right>', func=lambda e: self.action_center(self.size * (0.7, 0.5)))
        self.root.bind('<Up>', func=lambda e: self.action_center(self.size * (0.5, 0.3)))
        self.root.bind('<Down>', func=lambda e: self.action_center(self.size * (0.5, 0.7)))

        self.status = tk.Label(self.root, bd=1, relief='sunken', anchor='w')
        self.status.grid(row=1, column=0, sticky='nesw')
        self.root.columnconfigure(index=0, weight=1)

        self.progress = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress, max=1.0)
        self.progress_bar.grid(row=1, column=1, sticky='nesw')

        self.menu = tk.Menu(self.root)

        self.menu_file = tk.Menu(self.menu, tearoff=0)
        self.menu_file.add_command(label='Open...', command=self.menu_file_open)
        self.menu_file.add_separator()
        self.menu_file.add_command(label='Exit', command=self.root.destroy)
        self.menu.add_cascade(label='File', menu=self.menu_file)

        self.menu_view = tk.Menu(self.menu, tearoff=0)
        self.menu_view.add_command(label='Recenter', command=self.worker.task_center_restore)
        self.menu_view.add_separator()
        self.menu_view.add_command(label='Zoom In', command=lambda: self.action_zoom_in(self.size / 2))
        self.menu_view.add_command(label='Zoom Out', command=lambda: self.action_zoom_out(self.size / 2))
        self.menu_view.add_command(label='Reset Zoom', command=self.worker.task_zoom_restore)
        self.menu.add_cascade(label='View', menu=self.menu_view)

        self.menu_search = tk.Menu(self.menu, tearoff=0)
        self.menu_search.add_command(label='Find Address...', command=self.menu_search_address)
        self.menu_search.add_command(label='Find by Name...', command=self.menu_search_name)
        self.menu_search.add_command(label='Hide Search', command=lambda: self.worker.task_search_hide())
        self.menu.add_cascade(label='Search', menu=self.menu_search)

        self.menu_help = tk.Menu(self.menu, tearoff=0)
        if arg_parser is not None:
            self.menu_help.add_command(label='Launch Options...', command=self.menu_help_args)
        self.menu_help.add_command(label='Controls...', command=self.menu_help_controls)
        self.menu_help.add_command(label='About...', command=self.menu_help_about)
        self.menu.add_cascade(label='Help', menu=self.menu_help)

        self.running = False
        self.preview(Image.new('RGB', (1, 1)))

        self.root.config(menu=self.menu)

    def start(self):
        self.root.update()
        Thread(name='worker', target=self.worker.run).start()

        self.running = True
        while self.running:
            try:
                self.root.update()
                while not self.queue_callback.empty():
                    self.queue_callback.get(block=False)()
            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                import traceback
                self.worker(lambda: sys.exit(0))
                messagebox.showerror(title='Gui has crashed', message=traceback.format_exc())
                self.root.destroy()
                raise

    def exit(self):
        self.worker(lambda: sys.exit(0))
        self.running = False

    # noinspection PyAttributeOutsideInit
    def preview(self, image, position=(0, 0), scale=1):
        self._image = image
        self._image_position, self._image_scale = position, scale

        center = self.size / 2
        half_size = np.array(image.size)
        if scale > 1:
            left, top = map(int, (-center - position) / scale + half_size / 2)
            right, bottom = map(int, (center - position) / scale + half_size / 2)
            canvas = image.crop((left, top, right, bottom)).resize(tuple(image.size))
        else:
            left, top = map(int, -half_size / 2 * scale + position + center)
            right, bottom = map(int, half_size / 2 * scale + position + center)
            if scale < 1:
                image = image.resize(((right - left), (bottom - top)))
            canvas = Image.new('RGB', tuple(self.size))
            canvas.paste(image, (left, top))

        self.panel.image = ImageTk.PhotoImage(canvas)
        self.panel.configure(image=self.panel.image)

    @_worker_callback
    def callback_status(self, progress, message):
        self.progress.set(progress)
        self.status.config(text=message)

    @_worker_callback
    def callback_render(self, image):
        self.preview(image)

    @_worker_callback
    def callback_crash(self, message):
        messagebox.showerror(title='Render thread has crashed', message=message)
        self.status.config(text='Render thread has crashed. Please restart the application.')

    @property
    def size(self):
        return np.array((self.panel.winfo_width(), self.panel.winfo_height()))

    def menu_file_open(self):
        file = filedialog.askopenfilename(initialdir='maps', title='Open Map...',
                                          filetypes=(('XML Map File', '*.osm'), ('All Files', '*.*')))
        if file:
            self.worker.task_load_map(file)
            self.worker.task_resize(self.root.winfo_width(), self.root.winfo_height())

    def action_resize(self, size):
        self.worker.task_resize(*size)
        self.preview(self._image, self._image_position, self._image_scale)

    def action_center(self, point):
        self.worker.task_center(point)
        x, y = self._image_position + (self.size / 2 - point)
        self.preview(self._image, (x, y), self._image_scale)

    def action_zoom_in(self, point):
        self.worker.task_zoom_in(point)
        self.scale_preview(point, 1.5)

    def action_zoom_out(self, point):
        self.worker.task_zoom_out(point)
        self.scale_preview(point, 1 / 1.5)

    def scale_preview(self, point, scale):
        point = np.array(point) - self.size / 2
        distance = (self._image_position - point) * scale
        self.preview(self._image, tuple(point + distance), self._image_scale * scale)

    def menu_help_about(self):
        if arg_parser is None:
            messagebox.showinfo(title='About', message='Map viewer GUI made by Nulano.')
        else:
            messagebox.showinfo(title='About', message=arg_parser.description)

    def menu_help_controls(self):
        messagebox.showinfo(title='Controls', message=
                            'Left-click to zoom in to point\n'
                            'Right-click to zoom out to point\n'
                            'Middle-click to center at point\n\n'
                            '<P> and <O> to zoom in and out\n'
                            'Arrow keys to move around')

    def menu_help_args(self):
        if arg_parser is None:
            log('arg_parser is None', level=1)
        else:
            messagebox.showinfo(title='Launch Options', message=arg_parser.format_help())

    def menu_search_address(self):
        show_dialog(self.root, 'Find address', {'Street:': 'Grösslingová', 'Number:': '18'},
                    lambda *a: all(a) and self.worker.task_search_address(*a), text_submit='Search')

    def menu_search_name(self):
        show_dialog(self.root, 'Find by name', {'Name:': 'GAMČA'},
                    lambda *a: all(a) and self.worker.task_search_name(*a), text_submit='Search')


def _worker_task(func):
    def wrap(self, *args, **kwargs):
        self(lambda: func(self, *args, **kwargs))
    return wrap


class GuiWorker:
    def __init__(self, gui):
        self.queue_tasks = Queue()

        self.element_tree = None
        self.osm_helper = None
        self.camera = None
        self.renderer = None
        self.settings = {}
        self.highlight = None
        self.selection = None

        self.gui = gui
        renderer.nulano_gui_callback = self._status  # patch renderer

        # patch symbol artist:
        try:
            import a7_symbol_artist
            a7_symbol_artist.nulano_warn = lambda title, message: gui.queue_callback.put(
                    lambda: messagebox.showwarning(title, message)
            )
        except ImportError:
            pass

    def __call__(self, task):
        self.queue_tasks.put(task)

    def run(self):
        try:
            while True:
                self._process_tasks()
                self._render()
        except SystemExit:
            raise
        except:
            import traceback
            self.gui.callback_crash(traceback.format_exc())
            raise

    def _status(self, group: str = None, status: str = None, current: int = 0, maximum: int = 0):
        message = None if maximum == 0 else '{}/{}'.format(current, maximum)

        if status is not None:
            message = status if message is None else '{} ({})'.format(status, message)

        if group is not None:
            message = group if message is None else '{}: {}'.format(group, message)

        if message is not None:
            log(message)

        self.gui.callback_status(current / maximum if maximum != 0 else current, message)
    
    def _process_tasks(self):
        while True:
            self.queue_tasks.get(block=True)()
            if self.queue_tasks.empty():
                return
    
    def _render(self):
        if self.renderer is None:
            self._status('No map file open')
            self.gui.queue_callback.put(self.gui.menu_file_open)
            return

        log('-- rendering...')
        image = self.renderer.render()
        image_draw = ImageDraw.Draw(image, 'RGBA')
        if isinstance(self.highlight, tuple):
            x, y = self.renderer.camera.gps_to_px(self.highlight)
            image_draw.ellipse(((x - 5, y - 5), (x + 5, y + 5)), fill='#f00')
        elif isinstance(self.highlight, Rectangle):
            a, b = (self.highlight.max_lat, self.highlight.min_lon), (self.highlight.min_lat, self.highlight.max_lon)
            image_draw.ellipse((self.camera.gps_to_px(a), self.camera.gps_to_px(b)), width=2, outline='#f00')

        log('-- rendering done')
        if self.queue_tasks.empty():
            self.gui.callback_render(image)
            center_deg = self.camera.px_to_gps((self.camera.px_width / 2, self.camera.px_height / 2))
            status = 'lat={0:.4f}, lon={1:.4f}, zoom={2}, px/m={3:.3f}' \
                .format(center_deg[0], center_deg[1], self.camera.zoom_level, self.camera.px_per_meter())
            if self.selection is not None:
                status = '{}, selected: {}'.format(status, self.selection)
            self._status(status=status)

    @_worker_task
    def task_load_map(self, file):
        try:
            self.camera = camera.Camera()

            self.element_tree = None
            self.osm_helper = None
            self.renderer = None

            from gc import collect as gc_collect
            gc_collect()

            log('-- loading map:', file)
            self._status(status='parsing xml')
            self.element_tree = ElementTree.parse(file)
            gc_collect()
            self.renderer = renderer.Renderer(self.camera, self.element_tree)
            try:
                self.osm_helper = self.renderer.osm_helper
            except AttributeError:
                log('Could not find OsmHelper in Renderer, creating a duplicate in Gui', level=2)
                self.osm_helper = osm_helper.OsmHelper(self.element_tree)
            self.settings = {}
            self.renderer.center_camera()
            self.settings['zoom'] = self.camera.zoom_level
            log('-- map loaded')
        except FileNotFoundError:
            log('File {} does not exist.'.format(file), level=3)
            log(level=3)
            log('Use "{0} -f FILE" to specify a map file or "{0} -h" to show help.'.format(sys.argv[0]), level=3)

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

    def _select(self, element, name=None):
        self.highlight, self.selection = None, None
        if element is None:
            return
        if not name:
            name = osm_helper.tag_dict(element).get('name')

        if element.tag == 'node':
            self.highlight = (float(element.attrib['lat']), float(element.attrib['lon']))
            self.camera.center_at(*self.highlight)
            self.selection = name
        else:
            points = []
            tp = element.tag
            if element.tag == 'way':
                points = self.osm_helper.way_coordinates(element)
            elif element.tag == 'relation':
                tags = osm_helper.tag_dict(element)
                tp = '{}:{}'.format(element.tag, tags.get('type'))
                if tags.get('type') == 'multipolygon':
                    points = [point for polygon in self.osm_helper.multipolygon_to_polygons(element) for point in polygon]
            if len(points) == 0:
                log('Don\'t know how to select element {} of type {}'.format(name, tp), level=1)
            else:
                rect = Rectangle(min(points, key=itemgetter(0))[0], min(points, key=itemgetter(1))[1],
                                 max(points, key=itemgetter(0))[0], max(points, key=itemgetter(1))[1])
                self.highlight = rect
                self.camera.center_at((rect.min_lat + rect.max_lat) / 2, (rect.min_lon + rect.max_lon) / 2)
                self.selection = name
        log('Selected {} at {}'.format(self.highlight, self.selection))

    @_worker_task
    def task_search_hide(self):
        self._select(None, None)

    @_worker_task
    def task_search_address(self, street: str, number: str):
        street, number = street.lower(), number.lower()
        self._status(status='Searching for address: {}, {}'.format(street, number))
        self._select(None)
        for element in self.element_tree.getroot():
            tags = osm_helper.tag_dict(element)
            addr_street, addr_number = tags.get('addr:street', ''), tags.get('addr:housenumber', '')
            address = ' '.join(filter(lambda x: x, [addr_street, addr_number]))
            if street in addr_street.lower() and number in addr_number.lower().split('/'):
                log('Found {}'.format(address))
                self._select(element, address)
                return
        log('Search unsuccessful')

    @_worker_task
    def task_search_name(self, target: str):
        target = target.lower()
        self._status(status='Searching for name: {}'.format(target))
        self._select(None)
        best, best_len = None, 1000
        for element in self.element_tree.getroot():
            tags = osm_helper.tag_dict(element)
            names = filter(lambda i: 'name' in i[0], tags.items())
            for key, name in names:
                if target in name.lower():
                    match = len(name)
                    if element.tag == 'node':
                        match += 0.5
                    if element.tag == 'relation':
                        match -= 0.5
                    if match < best_len:
                        best, best_len = element, match
        if best is None:
            log('Search unsuccessful')
        self._select(best)


if __name__ == '__main__':
    start()
