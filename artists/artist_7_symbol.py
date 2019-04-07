from collections import namedtuple
from operator import itemgetter
from typing import List
from weakref import WeakKeyDictionary
from xml.etree.ElementTree import Element

from PIL.ImageDraw import ImageDraw

from artists_util import element_to_polygons, transform_shapes, explode_features, Feature, FontSymbol, FontEmoji
from camera import Camera
from geometry import polygon_centroid, polygon_area
from osm_helper import OsmHelper, tag_dict


_symbol = namedtuple('symbol', 'text font fill weight min_area')
_symbols = explode_features([
    Feature('amenity', 'parking', _symbol(u'\U0001D5E3', FontSymbol(12), '#44f', 0.005, 100)),
    Feature('amenity', 'hospital', _symbol(u'\U0001D5DB', FontSymbol(12), '#f44', 0.05, 400)),
    Feature('amenity', 'place_of_worship', _symbol(u'\u271D', FontSymbol(16), '#222', 0.05, 100)),
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
            else:
                polygons = [(polygon, polygon_area(polygon)) for polygon in
                            transform_shapes(element_to_polygons(element, osm_helper), camera)]
                if len(polygons) > 0:
                    polygon = max(polygons, key=itemgetter(1))
                    point, area = polygon_centroid(polygon[0]), polygon[1]
            style: _symbol = self.map[element].style
            area = max(area, style.min_area * camera.px_per_meter() ** 2) * style.weight
            if point is not None and area > 1:
                labels.append((area, point, style))
        for area, (x, y), style in sorted(labels, key=itemgetter(0), reverse=True):
            width, height = image_draw.textsize(style.text, font=style.font)
            image_draw.text((x - width // 2, y - height // 2),
                            text=style.text, fill=style.fill, font=style.font)

    def approx_location(self, element: Element, osm_helper: OsmHelper):
        return []
