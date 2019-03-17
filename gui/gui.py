import argparse
import tkinter as tk
from tkinter import ttk, messagebox
from xml.etree import ElementTree
import sys

from PIL import ImageTk

import camera
import renderer
import osm_helper


class Gui:
    def __init__(self, file, loglevel, dimensions, center=None, zoom=None):
        self.file = file
        self.loglevel = loglevel
        self.camera = camera.Camera(dimensions=dimensions)
        self.def_zoom = zoom if zoom is not None else self.camera.zoom_level
        self.def_center = center
        self.element_tree = None
        self.renderer = None
        self._raw_image, self._image = None, None

        osm_helper.nulano_log = self.log

        # Create GUI:

        self.root = tk.Tk()
        self.root.geometry('x'.join(map(str, dimensions)))

        self.panel = tk.Label(self.root)
        self.panel.bind('<ButtonRelease-2>', func=self.panel_center)
        self.panel.bind('<ButtonRelease-1>', func=self.panel_zoom_in)
        self.panel.bind('<ButtonRelease-3>', func=self.panel_zoom_out)
        self.panel.grid(row=0, column=0, columnspan=2, sticky='nesw')
        self.root.rowconfigure(index=0, weight=1)

        self.status = tk.Label(self.root, bd=1, relief='sunken', anchor='w')
        self.status.grid(row=1, column=0, sticky='nesw')
        self.root.columnconfigure(index=0, weight=1)

        self.progress = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress, max=1.0)
        self.progress_bar.grid(row=1, column=1, sticky='nesw')

        self.menu = tk.Menu(self.root)

        self.menu_file = tk.Menu(self.menu, tearoff=0)
        self.menu_file.add_command(label="Exit", command=self.root.quit)
        self.menu.add_cascade(label='File', menu=self.menu_file)

        self.menu_view = tk.Menu(self.menu, tearoff=0)
        self.menu_view.add_command(label="Recenter", command=self.menu_view_recenter)
        self.menu_view.add_command(label="Reset Zoom", command=self.menu_view_zoom_reset)
        self.menu_view.add_command(label="Zoom In", command=self.menu_view_zoom_in)
        self.menu_view.add_command(label="Zoom Out", command=self.menu_view_zoom_out)
        self.menu.add_cascade(label='View', menu=self.menu_view)

        self.menu_help = tk.Menu(self.menu, tearoff=0)
        if arg_parser is not None:
            self.menu_help.add_command(label='Launch Options...', command=self.menu_help_args)
        self.menu_help.add_command(label='Controls...', command=self.menu_help_controls)
        self.menu_help.add_command(label="About...", command=self.menu_help_about)
        self.menu.add_cascade(label='Help', menu=self.menu_help)

        self.root.config(menu=self.menu)

    def load_map(self):

        def renderer_callback(now, max, cur):
            self.log('processing map: {}/{} ({})'.format(now, max, cur))
            self.status.config(text='loading map: {} ({}/{})'.format(cur, now, max))
            self.progress.set(now / max)
            self.root.update()

        self.log('using map:', self.file)
        self.log('-- parsing map')
        renderer_callback(0, 1, 'parsing xml')

        try:
            self.element_tree = ElementTree.parse(self.file)
        except FileNotFoundError:
            self.log('File {} does not exist.'.format(self.file), level=3)
            self.log(level=3)
            self.log('Use "{0} -f FILE" to specify a map file or "{0} -h" to show help.'.format(sys.argv[0]), level=3)
            sys.exit(1)

        self.log('-- processing map')

        renderer.nulano_gui_callback = renderer_callback
        self.renderer = renderer.Renderer(self.camera, self.element_tree)
        if self.def_center is None:
            self.renderer.center_camera()
            self.def_center = self.camera.px_to_gps(self._center_px())
        else:
            self.camera.center_at(self.def_center[0], self.def_center[1])
        self.camera.zoom_level = self.def_zoom

        self.log('-- map loaded')

    def render(self):
        self.log('-- rendering...')
        center_deg = self.camera.px_to_gps(self._center_px())
        self.status.config(text='Center: (lat={}, lon={}), Zoom: {}, px/m={}'
                           .format(center_deg[0], center_deg[1], self.camera.zoom_level, self.camera.px_per_meter()))
        self.progress.set(0)
        self.root.update()

        self.camera.px_width, self.camera.px_height = self.panel.winfo_width(), self.panel.winfo_height()
        self._raw_image = self.renderer.render()
        self._image = ImageTk.PhotoImage(self._raw_image)
        self.panel.configure(image=self._image)

        self.progress.set(1)
        self.root.update()
        self.log('-- rendering done')

    def start(self):
        self.load_map()
        self.render()
        self.root.mainloop()

    def log(self, *msg, level=0, **kwargs):
        if level >= self.loglevel:
            print(['[info]', '[warn]', '[error]', '[critical]'][level], *msg, **kwargs)

    def _center_px(self):
        return self.camera.px_width / 2, self.camera.px_height / 2

    def panel_zoom_in(self, event):
        self.camera.zoom_in((event.x, event.y))
        self.render()

    def panel_zoom_out(self, event):
        self.camera.zoom_out((event.x, event.y))
        self.render()

    def panel_center(self, event):
        point = self.camera.px_to_gps((event.x, event.y))
        self.camera.center_at(point[0], point[1])
        self.render()

    def menu_help_about(self):
        if arg_parser is None:
            messagebox.showinfo(title='About', message='Map viewer GUI made by Nulano.')
        else:
            messagebox.showinfo(title='About', message=arg_parser.description)

    def menu_help_controls(self):
        messagebox.showinfo(title='Controls', message=
                            'Left-click to zoom in to point\n'
                            'Right-click to zoom out to point\n'
                            'Middle-click to center at point')

    def menu_help_args(self):
        if arg_parser is None:
            self.log('arg_parser is None', level=1)
        else:
            messagebox.showinfo(title='Launch Options', message=arg_parser.format_help())

    def menu_view_recenter(self):
        self.camera.center_at(self.def_center[0], self.def_center[1])
        self.render()

    def menu_view_zoom_reset(self):
        self.camera.zoom_level = self.def_zoom
        self.render()

    def menu_view_zoom_in(self):
        self.camera.zoom_in((self.camera.px_width/2, self.camera.px_height/2))
        self.render()

    def menu_view_zoom_out(self):
        self.camera.zoom_out((self.camera.px_width/2, self.camera.px_height/2))
        self.render()


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='OSM Map viewer GUI made by Nulano (2019)')
    arg_parser.add_argument('-f', '--map', default='maps/bratislava.osm', help='the OpenStreetMap xml file to use', dest='file')
    arg_parser.add_argument('-q', action='store_const', const=1, default=0, help='suppress info messages', dest='loglevel')
    arg_parser.add_argument('-Q', action='store_const', const=100, help='suppress ALL messages', dest='loglevel')
    arg_parser.add_argument('--dimensions', default=(800, 600), nargs=2, type=int, help='use this resolution at startup', metavar=('X', 'Y'))
    arg_parser.add_argument('--center', nargs=2, type=float, help='center map at %(metavar) at startup', metavar=('LAT', 'LON'))
    arg_parser.add_argument('--zoom', type=int, help='zoom map at level %(metavar) at startup', metavar='ZOOM')
    args = arg_parser.parse_args()
    gui = Gui(file=args.file, loglevel=args.loglevel, dimensions=args.dimensions, center=args.center, zoom=args.zoom)
    gui.start()
