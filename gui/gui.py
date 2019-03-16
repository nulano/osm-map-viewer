import tkinter as tk
from xml.etree import ElementTree

from PIL import ImageTk

from camera import Camera
from renderer import Renderer

if __name__ != '__main__':
    raise AssertionError('gui can only be used as __main__ module')


def render(camera, renderer, panel):
    print('rendering...')
    renderer.center_camera()
    panel.raw_image = renderer.render()
    panel.image = ImageTk.PhotoImage(panel.raw_image)
    panel.configure(image=panel.image)
    print('rendering done')


#file = '../artists/testdata/lafranconi.osm'
file = 'map.osm'
dimensions = (800, 600)

print('-- parsing map')
element_tree = ElementTree.parse(file)
print('-- processing map')
camera = Camera(dimensions=dimensions)
renderer = Renderer(camera, element_tree)
print('-- map loaded')

root = tk.Tk()
root.geometry('x'.join([str(x) for x in dimensions]))
panel = tk.Label(root)
panel.pack(side='bottom', fill='both', expand='yes')
render(camera, renderer, panel)
root.mainloop()
