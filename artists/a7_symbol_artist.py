from collections import namedtuple
from operator import itemgetter
from typing import List
from xml.etree.ElementTree import Element

from PIL.ImageDraw import ImageDraw

from base_artist import BaseArtist, element_to_polygons, transform_shapes, Feature, FontSymbol, FontEmoji
from camera import Camera
from geometry import polygon_centroid, polygon_area
from osm_helper import OsmHelper


_symbol = namedtuple('symbol', 'fallback_text text font fill min_area min_ppm')
_symbols = [
    # Parks
    Feature('leisure', 'dog_park',          _symbol('D',  u'\U0001F43E',  FontSymbol(16), '#844',  200, 0.50)),

    # Amenities - Small
    Feature('amenity', 'pub',               _symbol('P',  u'\U0001F37A',  FontSymbol(16), '#844',  200, 0.50)),
    Feature('amenity', 'bar',               _symbol('B',  u'\U0001F377',  FontSymbol(16), '#844',  200, 0.50)),
    Feature('amenity', 'cafe',              _symbol('C',  u'\U0001F375',  FontSymbol(16), '#844',  200, 0.50)),
    Feature('amenity', 'fast_food',         _symbol('FF', u'\U0001F35F',  FontSymbol(16), '#844',  200, 0.50)),
    Feature('amenity', 'restaurant',        _symbol('R',  u'\U0001F374',  FontSymbol(16), '#844',  200, 0.50)),
    Feature('amenity', 'food_court',        _symbol('FC', u'\U0001F37D',  FontSymbol(20), '#844',  200, 0.25)),

    # Amenities - Large
    Feature('amenity', 'parking',           _symbol('P',  u'\U0001D5E3',  FontSymbol(12), '#44f',  200, 0.50)),
    Feature('amenity', 'place_of_worship',  _symbol('+',  u'\u271D',      FontSymbol(16), '#222',   20, 0.25)),
    Feature('amenity', 'hospital',          _symbol('H',  u'\U0001D5DB',  FontSymbol(12), '#f44',   20, 0.25)),
]


class A7_symbolArtist(BaseArtist):
    def __init__(self):
        super().__init__(_symbols)
        self._text_fallback = not _check_pil()

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
            area = max(area / style.min_area, (camera.px_per_meter() / style.min_ppm) ** 2)
            if point is not None and area > 1:
                labels.append((area, point, style))
        for area, (x, y), style in sorted(labels, key=itemgetter(0), reverse=True):
            width, height = image_draw.textsize(style.text, font=style.font)
            text = style.fallback_text if (self._text_fallback or style.font is None) else style.text
            image_draw.text((x - width // 2, y - height // 2), text=text, fill=style.fill, font=style.font)

    def __str__(self):
        return "Symbols"


def nulano_warn(title, message):
    try:
        from tkinter import messagebox as tkm
        tkm.showwarning(title, message)
    except (ImportError, RuntimeError):
        pass


def _check_pil():
    from sys import platform
    if platform != 'win32':
        return True

    from PIL import __version__ as pil_version
    major, minor, rest = pil_version.split('.', 2)
    major, minor = int(major), int(minor)
    if major > 6 or (major == 6 and minor >= 1):
        return True

    warning = 'Your version of PIL or Pillow ({}) has a problem with Unicode on Windows. ' \
              'Please update Pillow using the script in the "Pillow-update" directory.'.format(pil_version)

    from warnings import warn
    warn(warning, UserWarning, source=__name__)

    nulano_warn('Pillow bug', warning)

    return False
