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
    def draws_at_zoom(self, element, camera: Camera, osm_helper: OsmHelper):
        return camera.px_per_meter() >= self.min_ppm

    def draw(self, elements: List[Element], osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        if self.draws_at_zoom(None, camera, osm_helper):
            lines = []
            for element in elements:
                lines += element_to_lines(element, osm_helper)
            for line in transform_shapes(lines, camera):
                image_draw.line(line, fill=self.fill, width=self.width, joint='curve')


class StylePoint(namedtuple('StylePoint', 'fill width min_ppm')):
    def draws_at_zoom(self, element, camera: Camera, osm_helper: OsmHelper):
        return camera.px_per_meter() >= self.min_ppm

    def draw(self, elements: List[Element], osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        if self.draws_at_zoom(None, camera, osm_helper):
            points = []
            for element in elements:
                points += element_to_points(element, osm_helper)
            for x, y in transform_shapes([points], camera)[0]:
                x1, x2 = x - (self.width // 2), x + self.width - (self.width // 2)
                y1, y2 = y - (self.width // 2), y + self.width - (self.width // 2)
                image_draw.ellipse([(x1, y1), (x2, y2)], fill=self.fill, width=0)


def StyleComp(*styles):
    class _StyleComp(namedtuple('StyleComp', 'styles')):
        def draws_at_zoom(self, element: Element, camera: Camera, osm_helper: OsmHelper):
            return any(map(lambda s: s.draws_at_zoom(element, camera, osm_helper), self.styles))

        def draw(self, elements: List[Element], osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
            for style in self.styles:
                style.draw(elements, osm_helper, camera, image_draw)
    return _StyleComp(tuple(styles))


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
        return self._wants_element(tags, element, osm_helper)

    def _wants_element(self, tags: dict, element: Element, osm_helper: OsmHelper):
        for key, features in self.styles.items():
            try:
                self.map[element] = features[tags[key]]
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
