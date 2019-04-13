import math
from collections import defaultdict, namedtuple
from dataclasses import dataclass
from typing import List, Tuple, Union, Any
from weakref import WeakKeyDictionary
from xml.etree.ElementTree import Element

from PIL import ImageFont
from PIL.ImageDraw import ImageDraw

from camera import Camera
from geometry import polygon_area
from location_filter import Rectangle
from osm_helper import OsmHelper, tag_dict


def transform_shapes(shapes: List[List[Tuple[float, float]]], camera: Camera):
    return [[camera.gps_to_px(point) for point in shape] for shape in shapes]


def _memoize(func):
    def memoized(element: Element, osm_helper, cache=WeakKeyDictionary()):
        try:
            return cache[element]
        except KeyError:
            cache[element] = out = func(element, osm_helper)
            return out

    return memoized


@_memoize
def element_to_polygons(element: Element, osm_helper: OsmHelper):
    if element.tag == 'relation' and tag_dict(element).get('type') == 'multipolygon':
        return [polygon[:-1] for polygon in osm_helper.multipolygon_to_wsps(element)]
    elif element.tag == 'way':
        way = osm_helper.way_coordinates(element)
        if len(way) >= 4 and way[0] == way[-1]:
            return [way[:-1]]
    return []


@_memoize
def element_to_area_m(element: Element, osm_helper: OsmHelper):
    area = sum(map(polygon_area, element_to_polygons(element, osm_helper)))
    bbox = element_to_bbox(element, osm_helper)
    scale = (40000000 / 360) ** 2 * math.cos(math.radians(bbox.max_lat + bbox.min_lat) / 2)
    return area * scale


@_memoize
def element_to_lines(element: Element, osm_helper: OsmHelper):
    if element.tag == 'relation' and tag_dict(element).get('type') == 'multipolygon':
        return osm_helper.multipolygon_to_polygons(element)
    elif element.tag == 'way':
        return [osm_helper.way_coordinates(element)]
    return []


@_memoize
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


@_memoize
def element_to_bbox(element: Element, osm_helper: OsmHelper):
    points = element_to_points(element, osm_helper)
    if len(points) == 0:
        return Rectangle(0, 0, 0, 0)
    from operator import itemgetter
    bbox = Rectangle(min(points, key=itemgetter(0))[0], min(points, key=itemgetter(1))[1],
                     max(points, key=itemgetter(0))[0], max(points, key=itemgetter(1))[1])
    return bbox


class BaseStyle:
    def wants_element(self, element: Element, tags: dict, osm_helper: OsmHelper):
        return True

    def convert(self, element: Element, tags: dict, osm_helper: OsmHelper):
        return element

    def draws_at_zoom(self, feature, camera: Camera, osm_helper: OsmHelper):
        return True

    def draw(self, features: List, osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        raise NotImplementedError


@dataclass(frozen=True)
class StyleArea(BaseStyle):
    fill: str
    min_area: float
    require_area: bool = False

    def wants_element(self, element: Element, tags: dict, osm_helper: OsmHelper):
        if element.tag == 'relation':
            return tags.get('type') == 'multipolygon'
        return element.tag == 'way' and (not self.require_area or tags.get('area') == 'yes')

    def convert(self, element: Element, tags: dict, osm_helper: OsmHelper):
        return element_to_polygons(element, osm_helper), element_to_area_m(element, osm_helper), element.attrib['id']

    def draws_at_zoom(self, feature, camera: Camera, osm_helper: OsmHelper):
        polygons, area, id = feature
        return area * (camera.px_per_meter() ** 2) >= self.min_area

    def draw(self, features: List, osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        for polygons, area, id in features:
            for polygon in transform_shapes(polygons, camera):
                image_draw.polygon(polygon, fill=self.fill)


@dataclass(frozen=True)
class StyleLine(BaseStyle):
    fill: str
    width: float
    exponent: float
    min_ppm: float
    skip_area: bool = False

    def wants_element(self, element: Element, tags: dict, osm_helper: OsmHelper):
        if self.skip_area:
            return element.tag == 'way' and tags.get('area') != 'yes'
        else:
            return element.tag == 'way' or (element.tag == 'relation' and tags.get('type') == 'multipolygon')

    def convert(self, element: Element, tags: dict, osm_helper: OsmHelper):
        return element_to_lines(element, osm_helper)

    def draws_at_zoom(self, feature, camera: Camera, osm_helper: OsmHelper):
        return camera.px_per_meter() >= self.min_ppm

    def draw(self, features: List, osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        width = int(self.width * (camera.px_per_meter() ** self.exponent))
        if self.draws_at_zoom(None, camera, osm_helper):
            for lines in features:
                for line in transform_shapes(lines, camera):
                    image_draw.line(line, fill=self.fill, width=width, joint='curve')


@dataclass(frozen=True)
class StylePoint(BaseStyle):
    fill: str
    width: float
    min_ppm: float
    require_node: bool = True

    def wants_element(self, element: Element, tags: dict, osm_helper: OsmHelper):
        return not self.require_node and element.tag == 'node'

    def convert(self, element: Element, tags: dict, osm_helper: OsmHelper):
        return element_to_points(element)

    def draws_at_zoom(self, feature, camera: Camera, osm_helper: OsmHelper):
        return camera.px_per_meter() >= self.min_ppm

    def draw(self, features: List, osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        if self.draws_at_zoom(None, camera, osm_helper):
            for points in features:
                for x, y in transform_shapes([points], camera)[0]:
                    x1, x2 = x - self.width / 2, x + self.width / 2
                    y1, y2 = y - self.width / 2, y + self.width / 2
                    image_draw.ellipse([(x1, y1), (x2, y2)], fill=self.fill, width=0)


@dataclass(frozen=True)
class StyleOutlined(BaseStyle):
    fill: str
    min_area: float
    outline: str
    min_ppm: float

    @property
    def area(self): return StyleArea(self.fill, self.min_area)

    @property
    def line(self): return StyleLine(self.outline, 1, 0, self.min_ppm)

    def wants_element(self, element: Element, tags: dict, osm_helper: OsmHelper):
        return self.area.wants_element(element, tags, osm_helper)

    def convert(self, element: Element, tags: dict, osm_helper: OsmHelper):
        return self.area.convert(element, tags, osm_helper), self.line.convert(element, tags, osm_helper)

    def draws_at_zoom(self, feature, camera: Camera, osm_helper: OsmHelper):
        feature_area, feature_line = feature
        return self.line.draws_at_zoom(feature_line, camera, osm_helper) or \
               self.area.draws_at_zoom(feature_area, camera, osm_helper)

    def draw(self, features: List, osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        features_area, features_line = zip(*features)
        self.area.draw(features_area, osm_helper, camera, image_draw)
        self.line.draw(features_line, osm_helper, camera, image_draw)


Feature = namedtuple('Feature', 'key tags style')
MappedFeature = namedtuple('MappedFeature', 'ordinal style')


def explode_features(features: List[Feature]):
    exploded = defaultdict(dict)
    for i, (key, tags, style) in enumerate(features):
        mapped = MappedFeature(i, style)
        if tags is None:
            exploded[key] = defaultdict(lambda m=mapped: m)
        else:
            for value in (tags.replace(',', ' ').split() if isinstance(tags, str) else tags):
                exploded[key][value] = mapped
    return exploded


class BaseArtist:
    def __init__(self, features=()):
        self.styles = explode_features(features)
        self.map = WeakKeyDictionary()
        self.data = WeakKeyDictionary()
        self._camera = Camera()

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        tags = tag_dict(element)
        for key, features in self.styles.items():
            try:
                feature: MappedFeature = features[tags[key]]
                if feature.style.wants_element(element, tags, osm_helper):
                    self.map[element] = feature
                    self.data[element] = feature.style.convert(element, tags, osm_helper), element_to_bbox(element, osm_helper)
                    return True
                return False
            except KeyError:
                pass
        return False

    def draws_at_zoom(self, element: Element, zoom: int, osm_helper: OsmHelper):
        feature, bbox = self.data[element]
        self._camera.zoom_level = zoom
        self._camera.center_at((bbox.min_lat + bbox.max_lat) / 2, (bbox.min_lon + bbox.max_lon) / 2)
        return self.map[element].style.draws_at_zoom(feature, self._camera, osm_helper)

    def draw(self, elements: List[Element], osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        layers = defaultdict(list)
        for element in elements:
            layers[self.map[element]].append(self.data[element][0])
        for style in sorted(layers):
            style.style.draw(layers[style], osm_helper, camera, image_draw)

    def approx_location(self, element: Element, osm_helper: OsmHelper):
        feature, bbox = self.data[element]
        return [bbox]

    def __str__(self):
        return 'BaseArtist'


class Font(dict):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __call__(self, size=24):
        return self[size]

    def __missing__(self, size):
        try:
            font = ImageFont.truetype(font=self.name, size=size)
        except IOError:
            font = None
            import traceback
            traceback.print_exc(chain=False)
        self[size] = font
        return font


FontSymbol = Font('fonts/Symbola.ttf')
FontEmoji = Font('fonts/NotoEmoji-Regular.ttf')
FontItalic = Font('fonts/IBMPlexSansCondensed-MediumItalic.ttf')
