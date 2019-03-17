from collections import defaultdict
from xml.etree.ElementTree import ElementTree

import PIL.Image
import PIL.ImageDraw

from camera import Camera
from location_filter import LocationFilter, Rectangle
from osm_helper import OsmHelper

from artists import get_artists


# fallback for incompatible gui implementations
def nulano_gui_callback(group: str = 'info', status: str = 'unknown', current: int = 0, maximum: int = 0):
    print('{}: {}/{}, ({})'.format(group, current, maximum, status))


class Renderer:
    def __init__(self, camera: Camera, element_tree: ElementTree):
        self.camera = camera
        self.element_tree = element_tree
        self.osm_helper = OsmHelper(element_tree)

        for element in element_tree.getroot():
            if element.tag == 'bounds':
                self.bounds = Rectangle(float(element.attrib['minlat']), float(element.attrib['minlon']),
                                        float(element.attrib['maxlat']), float(element.attrib['maxlon']))
                break
        else:
            raise AssertionError('no bounds tag in element_tree')

        draw_pairs = []
        artists = get_artists()
        for i, artist in enumerate(artists):
            nulano_gui_callback(group='loading map', status=artist.__class__.__qualname__, current=i, maximum=len(artists))
            for element in element_tree.getroot():
                if artist.wants_element(element, osm_helper=self.osm_helper):
                    draw_pairs += [(element, artist)]
        nulano_gui_callback(status='initializing location_filter', current=len(artists))
        self.filter = LocationFilter(0, self.bounds, draw_pairs, self.osm_helper)

    def center_camera(self):
        self.camera.center_at((self.bounds.min_lat + self.bounds.max_lat)/2,
                              (self.bounds.min_lon + self.bounds.max_lon)/2)

    def render(self):
        image = PIL.Image.new('RGB', (self.camera.px_width, self.camera.px_height), '#eed')
        draw = PIL.ImageDraw.Draw(image)
        groups = defaultdict(list)
        for element, artist in self.filter.get_pairs(self.camera.get_rect()):
            if artist.draws_at_zoom(element, self.camera.zoom_level, self.osm_helper):
                groups[artist] += [element]
        for i, (artist, elements) in enumerate(groups.items()):
            nulano_gui_callback(group='rendering', status=artist.__class__.__qualname__, current=i, maximum=len(groups))
            artist.draw(elements, self.osm_helper, self.camera, draw)
        return image
