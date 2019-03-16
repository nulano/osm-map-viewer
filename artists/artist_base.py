from xml.etree.ElementTree import Element

from PIL.ImageDraw import ImageDraw

from location_filter import Rectangle
from osm_helper import OsmHelper, tag_dict


class ArtistArea:
    def __init__(self): pass

    def draw_poly(self, poly: list, image_draw: ImageDraw): pass

    def wants_element_tags(self, tags: dict): return False

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        return self.wants_element_tags(tag_dict(element))

    def draws_at_zoom(self, element: Element, zoom: int, osm_helper: OsmHelper):
        return True

    def draw(self, elements: Element, osm_helper: OsmHelper, camera, image_draw: ImageDraw):
        polys = []
        for el in elements:
            if el.tag == 'relation':
                polys += osm_helper.multipolygon_to_wsps(el)
            elif el.tag == 'way':
                polys.append(osm_helper.way_coordinates(el))
            else:
                print('unknown type:', el.tag)
        for poly in polys:
            self.draw_poly([camera.gps_to_px(point) for point in poly], image_draw)

    def approx_location(self, element: Element, osm_helper: OsmHelper):
        return []
