from collections import defaultdict
from functools import partial
from xml.etree.ElementTree import Element

from PIL import ImageFont
from PIL.ImageDraw import ImageDraw

from camera import Camera
from location_filter import Rectangle
from osm_helper import OsmHelper, tag_dict


def transform_shapes(shapes: list, camera: Camera):
    return [[camera.gps_to_px(point) for point in shape] for shape in shapes]


def element_to_polygons(element: Element, osm_helper: OsmHelper):
    out = []
    if element.tag == 'relation' and tag_dict(element).get('type') == 'multipolygon':
        out = osm_helper.multipolygon_to_wsps(element)
    elif element.tag == 'way':
        way = osm_helper.way_coordinates(element)
        if len(way) >= 4 and way[0] == way[-1]:
            out = [way[:-1]]
    return out


def element_to_lines(element: Element, osm_helper: OsmHelper):
    out = []
    if element.tag == 'relation' and tag_dict(element).get('type') == 'multipolygon':
        out = [polygon + [polygon[0]] for polygon in osm_helper.multipolygon_to_polygons(element)]
    elif element.tag == 'way':
        out = [osm_helper.way_coordinates(element)]
    return out


def element_to_points(element: Element, osm_helper: OsmHelper):
    out = []
    if element.tag == 'relation' and tag_dict(element).get('type') == 'multipolygon':
        out = [point for polygon in osm_helper.multipolygon_to_polygons(element) for point in polygon]
    elif element.tag == 'way':
        out = osm_helper.way_coordinates(element)
        if len(out) >= 2 and out[0] == out[-1]:
            out = out[:-1]
    else:
        raise NotImplementedError
    return out


class ArtistArea:
    def __init__(self, fill='#fff', outline=None):
        self.fill, self.outline = fill, outline
        self.filter = IsArea

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        return self.filter.test(element, osm_helper)

    def draws_at_zoom(self, element: Element, zoom: int, osm_helper: OsmHelper):
        return True

    def draw(self, elements: Element, osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        polygons, outlines = [], []
        for element in elements:
            polygons += element_to_polygons(element, osm_helper)
            if self.outline is not None:
                outlines += element_to_lines(element, osm_helper)
        for polygon in transform_shapes(polygons, camera):
            image_draw.polygon(polygon, fill=self.fill)
        for outline in transform_shapes(outlines, camera):
            image_draw.line(outline, fill=self.outline, width=1)

    def approx_location(self, element: Element, osm_helper: OsmHelper):
        points = element_to_points(element, osm_helper)
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

    def draw(self, elements: Element, osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        lines = []
        for element in elements:
            lines += element_to_lines(element, osm_helper)
        for line in transform_shapes(lines, camera):
            image_draw.line(line, fill=self.fill, width=self.width, joint='curve')

    def approx_location(self, element: Element, osm_helper: OsmHelper):
        points = element_to_points(element, osm_helper)
        if len(points) == 0:
            return []
        from operator import itemgetter
        return [Rectangle(min(points, key=itemgetter(0))[0], min(points, key=itemgetter(1))[1],
                          max(points, key=itemgetter(0))[0], max(points, key=itemgetter(1))[1])]


def explode_tag_style_map(data: list):
    count = 0
    exploded = defaultdict(dict)
    for tag, values, style in data:
        if isinstance(values, str):
            values = values.replace(',', ' ').split()
        for value in values:
            # noinspection PyProtectedMember
            exploded[tag][value] = style._replace(ordinal=count)
            count += 1
    return exploded


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


class _IsNode(ElementFilterBase):
    def __call__(self, tags: dict, element: Element, osm_helper: OsmHelper):
        return element.tag == 'node'


class _IsWay(ElementFilterBase):
    def __call__(self, tags: dict, element: Element, osm_helper: OsmHelper):
        return element.tag == 'way'


class _IsArea(ElementFilterBase):
    def __call__(self, tags: dict, element: Element, osm_helper: OsmHelper):
        if element.tag == 'way':
            nodes = element.findall('nd')
            return nodes[0].get('ref') == nodes[-1].get('ref')
        else:
            return element.tag == 'relation' and tags.get('type') == 'multipolygon'


class _FilterTrue(ElementFilterBase):
    def __call__(self, tags: dict, element: Element, osm_helper: OsmHelper):
        return True

    def test(self, element: Element, osm_helper: OsmHelper):
        return True


class _FilterFalse(ElementFilterBase):
    def __call__(self, tags: dict, element: Element, osm_helper: OsmHelper):
        return False

    def test(self, element: Element, osm_helper: OsmHelper):
        return False


IsNode = _IsNode()
IsWay = _IsWay()
IsArea = _IsArea()
FilterTrue = _FilterTrue()
FilterFalse = _FilterFalse()


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
