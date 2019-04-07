from collections import namedtuple
from operator import itemgetter
from typing import List
from weakref import WeakKeyDictionary
from xml.etree.ElementTree import Element

from PIL.ImageDraw import ImageDraw

from artists_util import element_to_polygons, transform_shapes, explode_features, Feature, font_bold
from camera import Camera
from geometry import polygon_centroid, polygon_area
from osm_helper import OsmHelper, tag_dict


_symbol = namedtuple('symbol', 'text font fill')
_symbols = explode_features([
    Feature('amenity', 'parking', _symbol('P', font_bold(12), '#44f'))
])


class ArtistSymbol:
    def __init__(self):
        self.map = WeakKeyDictionary()

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        tags = tag_dict(element)
        for key, types in _symbols.items():
            try:
                self.map[element] = types[tags[key]]
                return True
            except KeyError:
                pass
        return False

    def draws_at_zoom(self, element: Element, zoom: int, osm_helper: OsmHelper):
        return True

    def draw(self, elements: List[Element], osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        labels = []
        for element in elements:
            point, area = None, 0
            if element.tag == 'node':
                point = camera.gps_to_px((float(element.attrib['lat']), float(element.attrib['lon'])))
                area = 100 * camera.px_per_meter() ** 2
            else:
                polygons = [(polygon, polygon_area(polygon)) for polygon in
                            transform_shapes(element_to_polygons(element, osm_helper), camera)]
                if len(polygons) > 0:
                    polygon = max(polygons, key=itemgetter(1))
                    point, area = polygon_centroid(polygon[0]), polygon[1]
            if area > 200:
                labels.append((area, point, self.map[element].style))
        for area, point, style in sorted(labels, reverse=True):
            image_draw.text(point, text=style.text, fill=style.fill, font=style.font)

    def approx_location(self, element: Element, osm_helper: OsmHelper):
        return []
