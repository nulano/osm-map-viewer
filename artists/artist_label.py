from collections import namedtuple
from itertools import islice
from operator import itemgetter
from weakref import WeakKeyDictionary
from xml.etree.ElementTree import Element

from PIL.ImageDraw import ImageDraw
import numpy as np

import artists_polylabel
import geometry
from artists_util import explode_tag_style_map, font_bold
from camera import Camera
from osm_helper import OsmHelper, tag_dict


_symbol = namedtuple('symbol', 'ordinal text font fill')
_symbols = explode_tag_style_map([
    ('amenity', 'parking', _symbol(None, 'P', font_bold(16), '#44f'))
])


class ArtistLabel:
    def __init__(self):
        self.types = WeakKeyDictionary()

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        tags = tag_dict(element)
        for tag, types in _symbols.items():
            if tags.get(tag) in types:
                self.types[element] = types[tags.get(tag)]
                return True
        else:
            return False

    def draws_at_zoom(self, element: Element, zoom: int, osm_helper: OsmHelper):
        # from camera import Camera  # FIXME yuck!
        # return Camera(zoom_level=zoom).px_per_meter() >= self.types[element].min_ppm
        return True

    def draw(self, elements: list, osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        camera_size = (camera.px_width, camera.px_height)
        labels = []
        for element in elements:
            if element.tag == 'node':
                point = camera.gps_to_px((float(element.attrib['lat']), float(element.attrib['lon'])))
                if np.greater(point, 0).all() and np.less(point, camera_size).all():
                    labels.append((point, 4 * camera.px_per_meter(), self.types[element]))
            elif element.tag == 'way':
                polygon = np.clip([camera.gps_to_px(point) for point in osm_helper.way_coordinates(element)], 0, camera_size)
                point = artists_polylabel.polylabel([polygon])
                weight = geometry.polygon_area(polygon)
                labels.append((point, weight, self.types[element]))
            else:
                print('warn: unknown element', element.tag, 'in', self.__class__.__qualname__)
                continue
        print(labels)
        for point, weight, style in islice(sorted(labels, key=itemgetter(1), reverse=True), 4):
            image_draw.text(point, style.text, fill=style.fill, font=style.font)
            print(point)


    def approx_location(self, element: Element, osm_helper: OsmHelper):
        return []


_all = [
    ArtistLabel()
]
