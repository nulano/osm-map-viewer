from operator import itemgetter
from typing import List
from weakref import WeakKeyDictionary
from xml.etree.ElementTree import Element

from PIL.ImageDraw import ImageDraw

from base_artist import BaseArtist, element_to_polygons, transform_shapes, FontItalic
from camera import Camera
from geometry import polygon_centroid, polygon_area
from osm_helper import OsmHelper, tag_dict


class A6_addressArtist(BaseArtist):
    def __init__(self):
        super().__init__([])
        self.map = WeakKeyDictionary()
        self.font = FontItalic(10)

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        tags = tag_dict(element)
        return 'addr:housenumber' in tags

    def draws_at_zoom(self, element: Element, zoom: int, osm_helper: OsmHelper):
        import camera
        return camera.Camera(zoom_level=zoom).px_per_meter() > 1

    def draw(self, elements: List[Element], osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        for element in elements:
            point = None
            if element.tag == 'node':
                point = camera.gps_to_px((float(element.attrib['lat']), float(element.attrib['lon'])))
            else:
                polygons = [(polygon, polygon_area(polygon)) for polygon in
                            transform_shapes(element_to_polygons(element, osm_helper), camera)]
                if len(polygons) > 0:
                    polygon = max(polygons, key=itemgetter(1))
                    point = polygon_centroid(polygon[0])
            if point is not None:
                x, y = point
                text = tag_dict(element).get('addr:housenumber', '')
                width, height = image_draw.textsize(text, font=self.font)
                image_draw.text((x - width // 2, y - height // 2), text=text, fill='#aaa', font=self.font)

    def __str__(self):
        return "Addresses"
