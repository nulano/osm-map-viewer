from collections import defaultdict
from datetime import timedelta
from operator import itemgetter
from time import time
from typing import Union
from xml.etree.ElementTree import ElementTree

import PIL.Image
import PIL.ImageDraw

from camera import Camera
from location_filter import LocationFilter, Rectangle
from osm_helper import OsmHelper

from artists import get_artists


# fallback for incompatible gui implementations
def nulano_gui_callback(group: str = 'info', status: str = 'unknown', current: Union[int, float] = 0, maximum: int = 0):
    print('{}: {}/{}, ({})'.format(group, current, maximum, status))


# fallback for incompatible gui implementations
def nulano_gui_log(message: str):
    print(message)


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
            points = [(float(element.attrib['lat']), float(element.attrib['lon']))
                      for element in element_tree.getroot() if element.tag == 'node']
            self.bounds = Rectangle(min(points, key=itemgetter(0))[0], min(points, key=itemgetter(1))[1],
                                    max(points, key=itemgetter(0))[0], max(points, key=itemgetter(1))[1])

        draw_pairs = []
        self.artists = get_artists()
        for i, artist in enumerate(self.artists):
            nulano_gui_callback(group='loading map', status=str(artist), current=i+1, maximum=len(self.artists))
            for element in element_tree.getroot():
                if artist.wants_element(element, osm_helper=self.osm_helper):
                    draw_pairs += [(element, artist)]

        nulano_gui_callback(status='initializing location filter', current=1)
        self.filter = LocationFilter(0.1, self.bounds, draw_pairs, self.osm_helper)
        self.zoom_cache = defaultdict(lambda: defaultdict(dict))

    def center_camera(self):
        self.camera.center_at((self.bounds.min_lat + self.bounds.max_lat)/2,
                              (self.bounds.min_lon + self.bounds.max_lon)/2)

    def render(self):
        image = PIL.Image.new('RGB', (self.camera.px_width, self.camera.px_height), '#eed')
        draw = PIL.ImageDraw.Draw(image, 'RGBA')
        groups = defaultdict(list)

        nulano_gui_callback(group='rendering', status='location filter', current=0)
        t = time()
        pairs = self.filter.get_pairs(self.camera.get_rect())
        nulano_gui_log('rendering: location filter took {}s'.format(timedelta(seconds=time()-t)))

        nulano_gui_callback(group='rendering', status='zoom filter', current=(0.5/len(self.artists)))
        t = time()
        for element, artist in pairs:
            zoom_filter = self.zoom_cache[artist][element]
            try:
                do_draw = zoom_filter[self.camera.zoom_level]
            except KeyError:
                zoom_filter[self.camera.zoom_level] = \
                    artist.draws_at_zoom(element, self.camera.zoom_level, self.osm_helper)
                do_draw = zoom_filter[self.camera.zoom_level]
            if do_draw:
                groups[artist] += [element]
        nulano_gui_log('rendering: zoom filter took {}s'.format(timedelta(seconds=time()-t)))

        for i, artist in enumerate(self.artists):
            nulano_gui_callback(group='rendering', status=str(artist), current=i+1, maximum=len(groups))
            t = time()
            artist.draw(groups[artist], self.osm_helper, self.camera, draw)
            nulano_gui_log('rendering: {} took {}s'.format(str(artist), timedelta(seconds=time()-t)))

        nulano_gui_callback(group='rendering', status='done', current=len(groups), maximum=len(groups))
        return image
