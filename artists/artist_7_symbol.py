from typing import List
from xml.etree.ElementTree import Element

from PIL.ImageDraw import ImageDraw

from artists_util import element_to_polygons, transform_shapes
from camera import Camera
from geometry import polygon_centroid
from osm_helper import OsmHelper, tag_dict


class ArtistSymbol:
    def __init__(self, text, color, size, key, values):
        self.text = text
        self.color = color
        self.size = size
        self.key, self.values = key, values

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        tags = tag_dict(element)
        return tags.get(self.key) in self.values

    def draws_at_zoom(self, element: Element, zoom: int, osm_helper: OsmHelper):
        return True

    def draw(self, elements: List[Element], osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        for element in elements:
            if element.tag == 'node':
                points = [(float(element.attrib['lat']), float(element.attrib['lon']))]
            else:
                polygons = element_to_polygons(element, osm_helper)
                points = [polygon_centroid(polygon) for polygon in polygons]
            for point in transform_shapes([points], camera)[0]:
                image_draw.point(point, fill='#444')
                image_draw.text(point, text=self.text, fill=self.color)

    def approx_location(self, element: Element, osm_helper: OsmHelper):
        return []


_all = [
    ArtistSymbol('P', '#88f', 16, 'amenity', ('parking',))
]
