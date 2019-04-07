import math
from collections import defaultdict, namedtuple
from functools import partial
from typing import List, Tuple, Union
from weakref import WeakKeyDictionary
from xml.etree.ElementTree import Element

from PIL import ImageFont
from PIL.ImageDraw import ImageDraw

from camera import Camera
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
        return None
    from operator import itemgetter
    bbox = Rectangle(min(points, key=itemgetter(0))[0], min(points, key=itemgetter(1))[1],
                     max(points, key=itemgetter(0))[0], max(points, key=itemgetter(1))[1])
    return bbox


class StyleArea(namedtuple('StyleArea', 'fill min_area req_area_tag')):
    def draws_at_zoom(self, element: Element, camera: Camera, osm_helper: OsmHelper):
        if self.min_area == 0:
            return True
        bbox = element_to_bbox(element, osm_helper)
        if bbox is None:
            return False
        raw_area = (bbox.max_lat - bbox.min_lat) * (bbox.max_lon - bbox.min_lon)
        scale = (40000000 * camera.px_per_meter() / 360 / math.cos(math.radians(bbox.max_lat + bbox.min_lat) / 2)) ** 2
        return raw_area * scale >= self.min_area

    def draw(self, elements: List[Element], osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        polygons = []
        for element in elements:
            polygons += element_to_polygons(element, osm_helper)
        for polygon in transform_shapes(polygons, camera):
            image_draw.polygon(polygon, fill=self.fill)


class StyleLine(namedtuple('StyleLine', 'fill width min_ppm')):
    def draws_at_zoom(self, element: Union[Element, None], camera: Camera, osm_helper: OsmHelper):
        return camera.px_per_meter() >= self.min_ppm

    def draw(self, elements: List[Element], osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        if self.draws_at_zoom(None, camera, osm_helper):
            lines = []
            for element in elements:
                lines += element_to_lines(element, osm_helper)
            for line in transform_shapes(lines, camera):
                image_draw.line(line, fill=self.fill, width=self.width, joint='curve')


class StylePoint(namedtuple('StylePoint', 'fill width min_ppm')):
    def draws_at_zoom(self, element: Union[Element, None], camera: Camera, osm_helper: OsmHelper):
        return camera.px_per_meter() >= self.min_ppm

    def draw(self, elements: List[Element], osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        if self.draws_at_zoom(None, camera, osm_helper):
            points = []
            for element in elements:
                points += element_to_points(element, osm_helper)
            for x, y in transform_shapes([points], camera)[0]:
                x1, x2 = x - self.width / 2, x + self.width / 2
                y1, y2 = y - self.width / 2, y + self.width / 2
                image_draw.ellipse([(x1, y1), (x2, y2)], fill=self.fill, width=0)


class StyleOutlined(namedtuple('StyleOutlined', 'fill min_area outline min_ppm')):
    @property
    def area(self): return StyleArea(self.fill, self.min_area, False)

    @property
    def line(self): return StyleLine(self.outline, 1, self.min_ppm)

    def draws_at_zoom(self, element: Element, camera: Camera, osm_helper: OsmHelper):
        return self.line.draws_at_zoom(element, camera, osm_helper) or \
               self.area.draws_at_zoom(element, camera, osm_helper)

    def draw(self, elements: List[Element], osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        self.area.draw(elements, osm_helper, camera, image_draw)
        self.line.draw(elements, osm_helper, camera, image_draw)


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


class Base:
    def __init__(self, features):
        self.styles = explode_features(features)
        self.map = WeakKeyDictionary()

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        tags = tag_dict(element)
        for key, features in self.styles.items():
            try:
                self.map[element] = style = features[tags[key]]
                return not isinstance(style.style, StyleArea) or not style.style.req_area_tag or tags.get('area') == 'yes'
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
        bbox = element_to_bbox(element, osm_helper)
        return [bbox] if bbox is not None else []


class Font(dict):
    def __init__(self, name):
        super().__init__()
        self.name = name

    def __call__(self, size=24):
        return self[size]

    def __missing__(self, size):
        self[size] = font = ImageFont.truetype(font=self.name, size=size)
        return font


FontSymbol = Font('fonts/Symbola.ttf')
FontEmoji = Font('fonts/NotoEmoji-Regular.ttf')
FontItalic = Font('fonts/IBMPlexSansCondensed-MediumItalic.ttf')
