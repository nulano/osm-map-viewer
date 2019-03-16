import argparse
import tkinter as tk
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

        self.status = tk.Label(self.root, bd=1, relief='sunken', anchor='w')
        self.status.pack(side='bottom', fill='x')

        self.panel = tk.Label(self.root)
        self.panel.pack(side='bottom', fill='both', expand='yes')
        self.panel.bind('<ButtonRelease-2>', func=self.panel_center)
        self.panel.bind('<ButtonRelease-1>', func=self.panel_zoom_in)
        self.panel.bind('<ButtonRelease-3>', func=self.panel_zoom_out)

        self.menu = tk.Menu(self.root)

        self.menu_file = tk.Menu(self.menu, tearoff=0)
        self.menu_file.add_command(label="About", command=self.menu_about)
        self.menu_file.add_command(label="Exit", command=self.root.quit)
        self.menu.add_cascade(label='File', menu=self.menu_file)

        self.menu_view = tk.Menu(self.menu, tearoff=0)
        self.menu_view.add_command(label="Recenter", command=self.menu_view_recenter)
        self.menu_view.add_command(label="Zoom In", command=self.menu_view_zoom_in)
        self.menu_view.add_command(label="Zoom Out", command=self.menu_view_zoom_out)
        self.menu_view.add_command(label="Reset Zoom", command=self.menu_view_zoom_reset)
        self.menu.add_cascade(label='View', menu=self.menu_view)

        self.root.config(menu=self.menu)

    def load_map(self):
        def renderer_callback(now, max, cur):
            self.log('processing map: {}/{} (step {})'.format(now, max, cur))

        self.log('using map:', self.file)
        self.log('-- parsing map')

        try:
            self.element_tree = ElementTree.parse(self.file)
        except FileNotFoundError:
            self.log('File {} does not exist.'.format(self.file), level=3)
            self.log(level=3)
            self.log('Use \'{0} -f FILE\' to specify a map file or \'{0} -h\' to show help.'.format(sys.argv[0]), level=3)
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

        self.camera.px_width, self.camera.px_height = self.panel.winfo_width(), self.panel.winfo_height()
        self._raw_image = self.renderer.render()
        self._image = ImageTk.PhotoImage(self._raw_image)
        self.panel.configure(image=self._image)

        self.log('-- rendering done')
        self.update_status()

    def update_status(self):
        center_deg = self.camera.px_to_gps(self._center_px())
        self.status.config(text='Center: (lat={}, lon={}), Zoom: {}, px/m={}'
                           .format(center_deg[0], center_deg[1], self.camera.zoom_level, self.camera.px_per_meter()))

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

    def menu_about(self):
        pass  # FIXME

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
    arg_parser = argparse.ArgumentParser(description='Gui for map project. Made by Nulano 2019.')
    arg_parser.add_argument('-f', '--map', default='map.osm', help='the OpenStreetMap xml file to use', dest='file')
    arg_parser.add_argument('-q', action='store_const', const=1, default=0, help='suppress info messages', dest='loglevel')
    arg_parser.add_argument('-Q', action='store_const', const=100, help='suppress ALL messages', dest='loglevel')
    arg_parser.add_argument('--dimensions', default=(800, 600), nargs=2, type=int, help='use this resolution at startup', metavar=('X', 'Y'))
    arg_parser.add_argument('--center', nargs=2, type=float, help='center map at %(metavar) at startup', metavar=('LAT', 'LON'))
    arg_parser.add_argument('--zoom', type=int, help='zoom map at level %(metavar) at startup', metavar='ZOOM')
    args = arg_parser.parse_args()
    gui = Gui(file=args.file, loglevel=args.loglevel, dimensions=args.dimensions, center=args.center, zoom=args.zoom)
    gui.start()
