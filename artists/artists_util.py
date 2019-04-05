from collections import defaultdict, namedtuple
from typing import List
from weakref import WeakKeyDictionary
from xml.etree.ElementTree import Element

from PIL import ImageFont
from PIL.ImageDraw import ImageDraw

from camera import Camera
from geometry import polygon_area
from location_filter import Rectangle
from osm_helper import OsmHelper, tag_dict


def transform_shapes(shapes: list, camera: Camera):
    return [[camera.gps_to_px(point) for point in shape] for shape in shapes]


def element_to_polygons(element: Element, osm_helper: OsmHelper):
    if element.tag == 'relation' and tag_dict(element).get('type') == 'multipolygon':
        return osm_helper.multipolygon_to_wsps(element)
    elif element.tag == 'way':
        way = osm_helper.way_coordinates(element)
        if len(way) >= 4 and way[0] == way[-1]:
            return [way[:-1]]
    return []


def element_to_lines(element: Element, osm_helper: OsmHelper):
    if element.tag == 'relation' and tag_dict(element).get('type') == 'multipolygon':
        return [polygon + [polygon[0]] for polygon in osm_helper.multipolygon_to_polygons(element)]
    elif element.tag == 'way':
        return [osm_helper.way_coordinates(element)]
    return []


def element_to_points(element: Element, osm_helper: OsmHelper):
    if element.tag == 'relation' and tag_dict(element).get('type') == 'multipolygon':
        return [point for polygon in osm_helper.multipolygon_to_polygons(element) for point in polygon]
    elif element.tag == 'way':
        way = osm_helper.way_coordinates(element)
        if len(way) >= 2 and way[0] == way[-1]:
            return way[:-1]
        return way
    elif element.tag == 'node':
        return [(float(element.attrib['lat']), float(element.attrib['lon']))]
    return []


class StyleArea(namedtuple('StyleArea', 'fill min_area')):
    def draws_at_zoom(self, element: Element, camera: Camera, osm_helper: OsmHelper):
        if self.min_area == 0:
            return True
        area = sum(map(polygon_area, transform_shapes(element_to_polygons(element, osm_helper), camera)))
        return area >= self.min_area

    def draw(self, elements: List[Element], osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        polygons = []
        for element in elements:
            polygons += element_to_polygons(element, osm_helper)
        for polygon in transform_shapes(polygons, camera):
            image_draw.polygon(polygon, fill=self.fill)


class StyleLine(namedtuple('StyleLine', 'fill width min_ppm')):
    def draws_at_zoom(self, element: Element, camera: Camera, osm_helper: OsmHelper):
        return camera.px_per_meter() >= self.min_ppm

    def draw(self, elements: List[Element], osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        lines = []
        for element in elements:
            lines += element_to_lines(element, osm_helper)
        for line in transform_shapes(lines, camera):
            image_draw.line(line, fill=self.fill, width=self.width, joint='curve')


def StyleComp(*styles):
    class _StyleComp(namedtuple('StyleComp', 'styles')):
        def draws_at_zoom(self, element: Element, camera: Camera, osm_helper: OsmHelper):
            return any(map(lambda s: s.draws_at_zoom(element, camera, osm_helper), self.styles))

        def draw(self, elements: List[Element], osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
            for style in self.styles:
                style.draw(elements, osm_helper, camera, image_draw)
    return _StyleComp(tuple(styles))


Feature = namedtuple('Feature', 'key tags style additional_filter')
MappedFeature = namedtuple('MappedFeature', 'ordinal style additional_filter')


def explode_features(features: List[Feature]):
    exploded = defaultdict(dict)
    for i, (key, tags, style, additional) in enumerate(features):
        mapped = MappedFeature(i, style, additional)
        if tags is None:
            exploded[key] = defaultdict(lambda m=mapped: m)
        else:
            for value in (tags.replace(',', ' ').split() if isinstance(tags, str) else tags):
                exploded[key][value] = mapped
    return exploded


class ArtistBase:
    def __init__(self, features):
        self.styles = explode_features(features)
        self.map = WeakKeyDictionary()

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        tags = tag_dict(element)
        return self._wants_element(tags, element, osm_helper)

    def _wants_element(self, tags: dict, element: Element, osm_helper: OsmHelper):
        for key, features in self.styles.items():
            try:
                style: MappedFeature = features[tags[key]]
                if style and style.additional_filter(tags, element, osm_helper):
                    self.map[element] = style
                    return True
            except KeyError:
                pass
        return False

    def draws_at_zoom(self, element: Element, zoom: int, osm_helper: OsmHelper):
        # assumes consistent scale (e.g. cylindrical) transform
        return self.map[element].style.draws_at_zoom(element, Camera(zoom_level=zoom), osm_helper)

    def draw(self, elements: List[Element], osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        layers = defaultdict(list)
        for element in elements:
            layers[self.map[element]].append(element)
        for style in sorted(layers):
            style.style.draw(layers[style], osm_helper, camera, image_draw)

    def approx_location(self, element: Element, osm_helper: OsmHelper):
        points = element_to_points(element, osm_helper)
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
