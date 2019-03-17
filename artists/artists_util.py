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
        outlines = []
        for el in elements:
            if el.tag == 'relation':
                polys += osm_helper.multipolygon_to_wsps(el)
                outlines += osm_helper.multipolygon_to_polygons(el)
            elif el.tag == 'way':
                way = osm_helper.way_coordinates(el)
                polys.append(way)
                outlines.append(way)
            else:
                print('warn: unknown type:', el.tag, '(in', self.__class__.__qualname__, 'draw)')
        for poly in polys:
            image_draw.polygon([camera.gps_to_px(point) for point in poly], fill=self.fill)
        if self.outline is not None:
            for line in outlines:
                image_draw.line([camera.gps_to_px(point) for point in line], fill=self.outline, width=1)

    def approx_location(self, element: Element, osm_helper: OsmHelper):
        points = []
        if element.tag == 'relation':
            points = [pt for poly in osm_helper.multipolygon_to_wsps(element) for pt in poly]
        elif element.tag == 'way':
            points = osm_helper.way_coordinates(element)
        else:
            print('warn: unknown type:', element.tag, '(in', self.__class__.__qualname__, 'approx_location)')
        if len(points) == 0:
            return []
        from operator import itemgetter
        return [Rectangle(min(points, key=itemgetter(0))[0], min(points, key=itemgetter(1))[1],
                          max(points, key=itemgetter(0))[0], max(points, key=itemgetter(1))[1])]


class ArtistWay:
    def __init__(self, fill='#fff', width=3, min_ppm=0):
        self.fill = fill
        self.width = width
        self.min_ppm = min_ppm
        self.filter = IsWay

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        return self.filter.test(element, osm_helper)

    def draws_at_zoom(self, element: Element, zoom: int, osm_helper: OsmHelper):
        from camera import Camera  # FIXME yuck!
        return Camera(zoom_level=zoom).px_per_meter() >= self.min_ppm

    def draw(self, elements: Element, osm_helper: OsmHelper, camera, image_draw: ImageDraw):
        lines = []
        for el in elements:
            if el.tag == 'way':
                lines.append([camera.gps_to_px(point) for point in osm_helper.way_coordinates(el)])
            else:
                print('warn: unknown type:', el.tag, '(in', self.__class__.__qualname__, 'draw)')
        for line in lines:
            image_draw.line(line, fill=self.fill, width=self.width, joint='curve')

    def approx_location(self, element: Element, osm_helper: OsmHelper):
        points = []
        if element.tag == 'way':
            points = osm_helper.way_coordinates(element)
        else:
            print('warn: unknown type:', element.tag, '(in', self.__class__.__qualname__, 'approx_location)')
        if len(points) == 0:
            return []
        from operator import itemgetter
        return [Rectangle(min(points, key=itemgetter(0))[0], min(points, key=itemgetter(1))[1],
                          max(points, key=itemgetter(0))[0], max(points, key=itemgetter(1))[1])]


class ElementFilterBase:
    def __call__(self, tags: dict, element: Element, osm_helper: OsmHelper):
        raise NotImplementedError

    # convenience for testing
    def test(self, element: Element, osm_helper: OsmHelper):
        return self(tag_dict(element), element, osm_helper)

    def And(self, other):
        class AndFilter(ElementFilterBase):
            def __init__(self, a, b):
                self.a, self.b = a, b

            def __call__(self, tags: dict, element: Element, osm_helper: OsmHelper):
                return self.a(tags, element, osm_helper) and self.b(tags, element, osm_helper)

        return AndFilter(self, other)

    def Or(self, other):
        class OrFilter(ElementFilterBase):
            def __init__(self, a, b):
                self.a, self.b = a, b

            def __call__(self, tags: dict, element: Element, osm_helper: OsmHelper):
                return self.a(tags, element, osm_helper) or self.b(tags, element, osm_helper)

        return OrFilter(self, other)

    def Not(self):
        class NotFilter(ElementFilterBase):
            def __init__(self, wrap):
                self.wrap = wrap

            def __call__(self, tags: dict, element: Element, osm_helper: OsmHelper):
                return not self.wrap(tags, element, osm_helper)

        return NotFilter(self)

    # convenience for +=
    def __add__(self, other): return self.And(other)


class ElementFilter(ElementFilterBase):
    def __init__(self, func=lambda t, e, o: True):
        self.func = func

    def __call__(self, tags: dict, element: Element, osm_helper: OsmHelper):
        return self.func(tags, element, osm_helper)


class _IsPoint(ElementFilterBase):
    def __call__(self, tags: dict, element: Element, osm_helper: OsmHelper):
        return element.tag == 'node'


class _IsWay(ElementFilterBase):
    def __call__(self, tags: dict, element: Element, osm_helper: OsmHelper):
        return element.tag == 'way' and element.attrib.get('area') != 'yes'


class _IsArea(ElementFilterBase):
    def __call__(self, tags: dict, element: Element, osm_helper: OsmHelper):
        return (element.tag == 'way') or (element.tag == 'relation' and tags.get('type') == 'multipolygon')


IsPoint = _IsPoint()
IsWay = _IsWay()
IsArea = _IsArea()


class TagMatches(ElementFilterBase):
    def __init__(self, tag, values):
        self.tag, self.values = tag, values

    def __call__(self, tags: dict, element: Element, osm_helper: OsmHelper):
        return tags.get(self.tag) in self.values


class TagPresent(ElementFilterBase):
    def __init__(self, tag):
        self.tag = tag

    def __call__(self, tags: dict, element: Element, osm_helper: OsmHelper):
        return self.tag in tags
