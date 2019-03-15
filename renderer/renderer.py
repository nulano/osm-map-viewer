from xml.etree.ElementTree import ElementTree

import PIL.Image
import PIL.ImageDraw

from camera import Camera
from osm_helper import OsmHelper


class Renderer:
    def __init__(self, camera: Camera, element_tree: ElementTree):
        self.camera = camera
        self.element_tree = element_tree
        self.osm_helper = OsmHelper(element_tree)

    def center_camera(self):
        for el in self.element_tree:
            if el.tag == 'bounds':
                lat = ((el.attrib['minlat']) + (el.attrib['maxlat'])) / 2
                lon = ((el.attrib['minlon']) + (el.attrib['maxlon'])) / 2
                self.camera.center_at(lat, lon)

    def render(self):
        im1 = PIL.Image.new('RGB', (self.camera.px_width, self.camera.px_height))
        draw = PIL.ImageDraw.Draw(im1)
        for artist in artists:
            artist.draw(to_draw[name], helper, cam, draw)
