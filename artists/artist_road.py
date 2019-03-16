from xml.etree.ElementTree import Element

from PIL.ImageDraw import ImageDraw

from artist_base import IsWay, TagMatches, ElementFilter, ArtistArea
from osm_helper import OsmHelper, tag_dict


class ArtistRoad:
    def __init__(self, types, color='#fff', width=3, bridge=False):
        self.color = color
        self.width = width
        self.bridge = bridge
        self.filter = IsWay\
            .And(TagMatches('highway', types))\
            .And(ElementFilter(lambda t, e, o: bridge == ('bridge' in t)))

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        return self.filter.test(element, osm_helper)

    def draws_at_zoom(self, element: Element, zoom: int, osm_helper: OsmHelper):
        return True  # TODO

    def draw(self, elements: Element, osm_helper: OsmHelper, camera, image_draw: ImageDraw):
        for el in elements:
            if el.tag == 'way':
                line = [camera.gps_to_px(point) for point in osm_helper.way_coordinates(el)]
                image_draw.line(line, fill=self.color, width=self.width, joint='curve')
            else:
                print('warn: invalid road tag type:', el.tag)

    def approx_location(self, element: Element, osm_helper: OsmHelper):
        return []  # TODO


class ArtistRoadArea(ArtistArea):
    def __init__(self, types, fill, outline):
        super().__init__(fill=fill, outline=outline)
        self.filter += TagMatches('highway', types)


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
