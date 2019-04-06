from xml.etree.ElementTree import Element

from PIL.ImageDraw import ImageDraw
import numpy as np

from artists_util import ElementFilterBase, IsArea, TagMatches
from camera import Camera
from osm_helper import OsmHelper, tag_dict


class ArtistSymbol:
    def __init__(self, text, color, size, filter: ElementFilterBase):
        self.text = text
        self.color = color
        self.size = size
        self.filter = filter

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        return self.filter.test(element, osm_helper)

    def draws_at_zoom(self, element: Element, zoom: int, osm_helper: OsmHelper):
        return True

    def draw(self, elements: list, osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        for element in elements:
            if element.tag == 'node':
                point = (float(element.attrib['lat']), float(element.attrib['lon']))
            elif element.tag == 'way':
                point = np.mean(np.array(osm_helper.way_coordinates(element)), axis=0)
            else:
                print('warn: unknown element', element.tag, 'in', self.__class__.__qualname__)
                continue
            image_draw.text(camera.gps_to_px(point), text=self.text, fill=self.color)

    def approx_location(self, element: Element, osm_helper: OsmHelper):
        return []


_all = [
    ArtistSymbol('P', '#88f', 16, TagMatches('amenity', ('parking', )))
]
