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
                print('warn: unknown type:', el.tag, '(in', self.__class__.__qualname__, 'draw)')
        for poly in polys:
            self.draw_poly([camera.gps_to_px(point) for point in poly], image_draw)

    def approx_location(self, element: Element, osm_helper: OsmHelper):
        return []  # TODO


class ElementFilter:

    def __init__(self):
        self.filters = []

    def __call__(self, tags: dict, element: Element, osm_helper: OsmHelper):
        try:
            for f in self.filters:
                if not f(tags, element, osm_helper):
                    return False
            else:
                return True
        except Exception:
            from traceback import print_exc
            print_exc(3)
            return False

    def IsPoint(self):
        self.filters.append(lambda t, e, o: e.tag == 'node')
        return self

    def IsWay(self):
        self.filters.append(lambda t, e, o: e.tag == 'way' and e.attrib.get('area') != 'yes')
        return self

    def IsArea(self):
        def func(tags: dict, element: Element, osm_helper: OsmHelper):
            if element.tag == 'way':
                return True  # FIXME only sometimes
            elif element.tag == 'relation':
                return tags.get('type') == 'multipolygon'
            else:
                return False

        self.filters.append(func)
        return self

    def Matches(self, func):
        self.filters.append(func)
        return self

    def TagMatches(self, tag, values):
        self.filters.append(lambda t, e, o: t.get(tag, None) in values)
        return self

    def HasTag(self, tag):
        self.filters.append(lambda t, e, o: tag in t)
        return self
