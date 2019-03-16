from xml.etree.ElementTree import Element

from PIL.ImageDraw import ImageDraw

from location_filter import Rectangle
from osm_helper import OsmHelper, tag_dict


class ArtistArea:
    def __init__(self, fill='#fff', outline=None):
        self.fill = fill
        self.outline = outline
        self.filter = IsArea

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        return self.filter.test(element, osm_helper)

    def draws_at_zoom(self, element: Element, zoom: int, osm_helper: OsmHelper):
        return True  # TODO

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
            image_draw.polygon([camera.gps_to_px(point) for point in poly], fill=self.fill, outline=self.outline)

    def approx_location(self, element: Element, osm_helper: OsmHelper):
        return []  # TODO


class ElementFilter:
    def __init__(self, func=lambda t, e, o: True):
        self.func = func

    def __call__(self, tags: dict, element: Element, osm_helper: OsmHelper):
        return self.func(tags, element, osm_helper)

    # convenience for testing
    def test(self, element: Element, osm_helper: OsmHelper):
        return self(tag_dict(element), element, osm_helper)

    def And(self, other):
        return ElementFilter(lambda t, e, o: self(t, e, o) and other(t, e, o))

    def Or(self, other):
        return ElementFilter(lambda t, e, o: self(t, e, o) or other(t, e, o))

    # convenience for +=
    def __add__(self, other): return self.And(other)


IsPoint = ElementFilter(lambda t, e, o: e.tag == 'node')
IsWay = ElementFilter(lambda t, e, o: e.tag == 'way' and e.attrib.get('area') != 'yes')
IsArea = ElementFilter(lambda t, e, o: e.tag == 'way' or (e.tag == 'relation' and t.get('type') == 'multipolygon'))


def TagMatches(tag, values):
    return ElementFilter(lambda t, e, o: t.get(tag) in values)


def TagPresent(tag):
    return ElementFilter(lambda t, e, o: tag in t)
