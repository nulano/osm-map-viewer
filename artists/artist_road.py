from xml.etree.ElementTree import Element

from PIL.ImageDraw import ImageDraw

from artists_util import IsWay, TagMatches, ElementFilter, ArtistArea
from location_filter import Rectangle
from osm_helper import OsmHelper


# TODO base on ArtistWay?
class ArtistRoad:
    def __init__(self, tag, types, color='#fff', width=3, min_ppm=0, bridge=False):
        self.color = color
        self.width = width
        self.min_ppm = min_ppm
        self.bridge = bridge
        self.filter = IsWay\
            .And(TagMatches(tag, types))\
            .And(ElementFilter(lambda t, e, o: bridge == ('bridge' in t)))\
            .And(TagMatches('tunnel', ('yes',)).Not())

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

        if self.width >= 5 and self.bridge:
            for line in lines:
                image_draw.line(line, fill='#666', width=self.width + 2, joint='curve')

        for line in lines:
            image_draw.line(line, fill=self.color, width=self.width, joint='curve')

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


class ArtistRoadArea(ArtistArea):
    def __init__(self, types, fill, outline):
        super().__init__(fill=fill, outline=outline)
        self.filter += TagMatches('highway', types).And(TagMatches('area', ('yes', )))


_all = {'pedestrian': ArtistRoadArea(('pedestrian',), '#aaa', '#999')}


def _add(road, link, bridge):
    name, color, width, min_ppm, link_allow, tag, types = road
    name = 'road_' + name

    if bridge:
        name += '_bridge'

    if link:
        if not link_allow:
            return
        name += '_link'
        types = tuple(tp + '_link' for tp in types)

    _all[name] = ArtistRoad(tag, types, color, width, min_ppm, bridge)


_types = [
    ('ped_small', '#aaa', 1, 0.200, False, 'highway', ('footway', 'steps', 'path')),
    ('ped_large', '#aaa', 2, 0.200, False, 'highway', ('pedestrian',)),
    ('unknown',   '#888', 2, 0.150, False, 'highway', ('road',)),
    ('tiny',      '#fff', 2, 0.150, False, 'highway', ('service',)),
    ('ped_zone',  '#ddd', 3, 0.150, False, 'highway', ('living_street',)),
    ('small',     '#fff', 3, 0.100, False, 'highway', ('residential', 'unclassified')),
    ('normal',    '#fff', 5, 0.050, True,  'highway', ('tertiary',)),
    ('main',      '#fea', 5, 0.010, True,  'highway', ('secondary',)),
    ('tram',      '#000', 1, 0.200, False, 'railway', ('tram',)),
    ('rail',      '#000', 1, 0.000, False, 'railway', ('rail', 'narrow_gauge', 'turntable')),
    ('primary',   '#fda', 5, 0.000, True,  'highway', ('primary',)),
    ('highway',   '#d60', 8, 0.000, True,  'highway', ('trunk',)),
    ('motorway',  '#fa0', 8, 0.000, True,  'highway', ('motorway',))
]


for _road in _types:
    _add(_road, True,  False)
for _road in _types:
    _add(_road, False, False)
for _road in _types:
    _add(_road, True,  True)
for _road in _types:
    _add(_road, False, True)
