from dataclasses import dataclass
from operator import itemgetter
from typing import List
from xml.etree.ElementTree import Element

from PIL.ImageDraw import ImageDraw

from base_artist import BaseArtist, element_to_polygons, FontItalic, BaseStyle, Feature, MappedFeature
from camera import Camera
from geometry import polygon_centroid, polygon_area
from osm_helper import OsmHelper

_KEY = 'addr:housenumber'


@dataclass(frozen=True)
class StyleAddress(BaseStyle):
    key: str
    font: object
    fill: str
    min_ppm: float

    def convert(self, element: Element, tags: dict, osm_helper: OsmHelper):
        if element.tag == 'node':
            return (float(element.attrib['lat']), float(element.attrib['lon'])), tags[self.key]
        else:
            polygons = [(polygon, polygon_area(polygon)) for polygon in element_to_polygons(element, osm_helper)]
            if len(polygons) > 0:
                polygon, area = max(polygons, key=itemgetter(1))
                return polygon_centroid(polygon), tags[self.key]

    def draws_at_zoom(self, feature, camera: Camera, osm_helper: OsmHelper):
        return camera.px_per_meter() >= self.min_ppm

    def draw(self, features: List, osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        for point, text in sorted(features, key=itemgetter(1)):
            x, y = camera.gps_to_px(point)
            width, height = image_draw.textsize(text, font=self.font)
            image_draw.text((x - width // 2, y - height // 2), text=text, fill=self.fill, font=self.font)

    # BaseArtist hack
    def items(self):
        return [(self.key, self)]

    # BaseArtist hack
    def __getitem__(self, item):
        return MappedFeature(0, self)


class A6_addressArtist(BaseArtist):
    def __init__(self):
        super().__init__([])
        self.styles = StyleAddress('addr:housenumber', FontItalic(10), '#aaa', 2)

    def __str__(self):
        return "Addresses"
