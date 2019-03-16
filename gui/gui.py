import argparse
import tkinter as tk
from xml.etree import ElementTree

from PIL import ImageTk

from camera import Camera
from renderer import Renderer

if __name__ != '__main__':
    raise AssertionError('gui can only be used as a __main__ module')


def render(camera, renderer, panel):
    print('rendering...')
    renderer.center_camera()
    panel.raw_image = renderer.render()
    panel.image = ImageTk.PhotoImage(panel.raw_image)
    panel.configure(image=panel.image)
    print('rendering done')


arg_parser = argparse.ArgumentParser(description='Gui for map project. Made by Nulano 2019.')
arg_parser.add_argument('-f', '--map', default='map.osm', help='the OpenStreetMap xml file to use', dest='file')
arg_parser.add_argument('--dimensions', default=(800, 600), nargs=2, help='use this resolution at startup', metavar=('X', 'Y'))
args = arg_parser.parse_args()

print('-- parsing map')
element_tree = ElementTree.parse(args.file)
print('-- processing map')
camera = Camera(dimensions=args.dimensions)
renderer = Renderer(camera, element_tree)
print('-- map loaded')

root = tk.Tk()
root.geometry('x'.join([str(x) for x in args.dimensions]))
panel = tk.Label(root)
panel.pack(side='bottom', fill='both', expand='yes')
render(camera, renderer, panel)
root.mainloop()
