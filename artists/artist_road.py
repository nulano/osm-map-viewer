from xml.etree.ElementTree import Element

from location_filter import Rectangle
from osm_helper import OsmHelper, tag_dict
from PIL.ImageDraw import ImageDraw
from artist_base import ArtistArea


def _is_area(element: Element, tags: dict):
    if element.tag == 'way':
        return element.get('area') == 'yes'
    elif element.tag == 'relation':
        return element.get('type') == 'multipolygon'
    return None


class ArtistRoad:
    def __init__(self, types, color='#fff', width=3, bridge=False):
        self.types = types
        self.color = color
        self.width = width
        self.bridge = bridge

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        tags = tag_dict(element)
        return not _is_area(element, tags) \
            and tags.get('highway') in self.types \
            and (('bridge' in tags) == self.bridge)

    def draws_at_zoom(self, element: Element, zoom: int, osm_helper: OsmHelper):
        return True

    def draw(self, elements: Element, osm_helper: OsmHelper, camera, image_draw: ImageDraw):
        for el in elements:
            line = [camera.gps_to_px(point) for point in osm_helper.way_coordinates(el)]
            image_draw.line(line, fill=self.color, width=self.width, joint='curve')

    def approx_location(self, element: Element, osm_helper: OsmHelper):
        return []


class ArtistRoadArea(ArtistArea):
    def __init__(self, types, color, outline):
        super().__init__()
        self.types = types
        self.color = color
        self.outline = outline

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        tags = tag_dict(element)
        return _is_area(element, tags) \
            and tags.get('highway') in self.types

    def draw_poly(self, poly: list, image_draw: ImageDraw):
        image_draw.polygon(poly, fill=self.color, outline=self.outline)


_all = {'pedestrian': ArtistRoadArea(('pedestrian',), '#aaa', '#999')}


def _add(road, link, bridge):
    name, color, width, link_allow, types = road
    name = 'road_' + name

    if bridge:
        name += '_bridge'

    if link:
        if not link_allow:
            return
        name += '_link'
        types = tuple(tp + '_link' for tp in types)

    _all[name] = ArtistRoad(types, color, width, bridge)


_types = [
    ('ped_small', '#aaa', 1, False, ('footway', 'steps', 'path')),
    ('ped_large', '#aaa', 2, False, ('pedestrian',)),
    ('unknown',   '#888', 2, False, ('road',)),
    ('tiny',      '#fff', 2, False, ('service',)),
    ('ped_zone',  '#ddd', 3, False, ('living_street',)),
    ('small',     '#fff', 3, False, ('residential', 'unclassified')),
    ('normal',    '#fff', 5, True,  ('tertiary',)),
    ('main',      '#fea', 5, True,  ('secondary',)),
    ('primary',   '#fda', 5, True,  ('primary',)),
    ('highway',   '#d60', 8, True,  ('trunk',)),
    ('motorway',  '#fa0', 8, True,  ('motorway',))
]


for _road in _types:
    _add(_road, True,  False)
for _road in _types:
    _add(_road, False, False)
for _road in _types:
    _add(_road, True,  True)
for _road in _types:
    _add(_road, False, True)
