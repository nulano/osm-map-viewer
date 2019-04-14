from dataclasses import dataclass
from operator import itemgetter
from typing import List
from xml.etree.ElementTree import Element

from PIL.ImageDraw import ImageDraw

from base_artist import BaseArtist, BaseStyle, Feature, FontSymbol, FontEmoji, element_to_polygons, element_to_area_m
from camera import Camera
from geometry import polygon_centroid, polygon_area
from osm_helper import OsmHelper

_pil_workaround = False


@dataclass(frozen=True)
class StyleSymbol(BaseStyle):
    text: str
    text_fallback: str
    font: object
    fill: str
    min_area: float
    min_ppm: float

    @property
    def _text(self):
        if _pil_workaround or self.font is None:
            return self.text_fallback
        else:
            return self.text

    def convert(self, element: Element, tags: dict, osm_helper: OsmHelper):
        if element.tag == 'node':
            return (float(element.attrib['lat']), float(element.attrib['lon'])), 0
        else:
            polygons = [(polygon, polygon_area(polygon)) for polygon in element_to_polygons(element, osm_helper)]
            if len(polygons) > 0:
                polygon, area = max(polygons, key=itemgetter(1))
                return polygon_centroid(polygon), element_to_area_m(element, osm_helper)

    def draws_at_zoom(self, feature, camera: Camera, osm_helper: OsmHelper):
        point, area = feature
        return camera.px_per_meter() >= self.min_ppm or area * (camera.px_per_meter() ** 2) >= self.min_area

    def draw(self, features: List, osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        for point, area in sorted(features, key=itemgetter(1)):
            x, y = camera.gps_to_px(point)
            width, height = image_draw.textsize(self._text, font=self.font)
            image_draw.text((x - width // 2, y - height // 2), text=self._text, fill=self.fill, font=self.font)


_symbols = [
    # Parks
    Feature('amenity', 'fountain',              StyleSymbol(u'\u26F2',      '',   FontSymbol(16), '#44f',  100, 2.00)),
    Feature('leisure', 'dog_park',              StyleSymbol(u'\U0001F43E',  'D',  FontSymbol(20), '#844',  100, 1.00)),

    # Amenities - Sustenance
    Feature('amenity', 'ice_cream',             StyleSymbol(u'\U0001F366',  'IC', FontEmoji(16),  '#844',  100, 1.00)),
    Feature('amenity', 'pub',                   StyleSymbol(u'\U0001F37A',  'P',  FontEmoji(16),  '#844',  100, 1.00)),
    Feature('amenity', 'bar',                   StyleSymbol(u'\U0001F377',  'B',  FontEmoji(16),  '#844',  100, 1.00)),
    Feature('amenity', 'cafe',                  StyleSymbol(u'\U0001F375',  'C',  FontEmoji(16),  '#844',  100, 1.00)),
    Feature('amenity', 'fast_food',             StyleSymbol(u'\U0001F35F',  'FF', FontEmoji(16),  '#844',  100, 1.00)),
    Feature('amenity', 'restaurant',            StyleSymbol(u'\U0001F374',  'R',  FontSymbol(20), '#844',  100, 1.00)),
    Feature('amenity', 'food_court',            StyleSymbol(u'\U0001F37D',  'FC', FontSymbol(28), '#844',  100, 0.25)),

    # Amenities - Entertainment, Arts & Culture
    Feature('leisure', 'adult_gaming_centre',   StyleSymbol(u'\U0001F3B0',  '?',  FontEmoji(16),  '#d80',  100, 1.00)),
    Feature('amenity', 'casino',                StyleSymbol(u'\U0001F3B2',  '?',  FontEmoji(16),  '#d80',  100, 1.00)),
    Feature('amenity', 'arts_centre',           StyleSymbol(u'\U0001F3A8',  'A',  FontEmoji(16),  '#d80',  100, 1.00)),
    Feature('amenity', 'theatre',               StyleSymbol(u'\U0001F3AD',  'T',  FontEmoji(16),  '#d80',  100, 1.00)),
    Feature('amenity', 'cinema',                StyleSymbol(u'\U0001F3AC',  'C',  FontEmoji(16),  '#d80',  100, 1.00)),

    # Amenities - Education

    # Amenities - Important
    Feature('amenity', 'parking',               StyleSymbol(u'\U0001D5E3',  'P',  FontSymbol(12), '#44f',  100, 0.50)),
    Feature('amenity', 'fuel',                  StyleSymbol(u'\u26FD',      'F',  FontEmoji(16),  '#44f',   50, 0.10)),
    Feature('amenity', 'place_of_worship',      StyleSymbol(u'\u271D',      '+',  FontSymbol(16), '#222',   16, 0.25)),
    Feature('amenity', 'hospital',              StyleSymbol(u'\U0001D5DB',  'H',  FontSymbol(16), '#f44',   16, 0.25)),
]


class A7_symbolArtist(BaseArtist):
    def __init__(self):
        super().__init__(_symbols)
        global _pil_workaround
        _pil_workaround = not _check_pil()

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
