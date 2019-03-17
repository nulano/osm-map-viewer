from collections import namedtuple, defaultdict
from weakref import WeakKeyDictionary
from xml.etree.ElementTree import Element

from PIL.ImageDraw import ImageDraw

from artists_util import ArtistArea
from location_filter import Rectangle
from osm_helper import OsmHelper, tag_dict


_road_base_type = namedtuple('road_base_type', ('tag', 'values', 'has_link',
                                                'width', 'fill', 'outline', 'outline_bridge', 'min_ppm'))
_road_base_types = [
    _road_base_type('highway', ('footway', 'steps', 'path'),          False, 1, '#aaa', None,   None,   0.200),
    _road_base_type('highway', ('pedestrian',),                       False, 2, '#aaa', None,   None,   0.200),
    _road_base_type('highway', ('road',),                             False, 2, '#888', None,   None,   0.150),
    _road_base_type('highway', ('service',),                          False, 2, '#fff', '#ccc', '#ccc', 0.150),
    _road_base_type('highway', ('living_street',),                    False, 5, '#ddd', None,   None,   0.150),
    _road_base_type('highway', ('residential', 'unclassified'),       False, 3, '#fff', '#ccc', '#ccc', 0.100),
    _road_base_type('highway', ('tertiary',),                         True,  5, '#fff', '#aaa', '#666', 0.050),
    _road_base_type('highway', ('secondary',),                        True,  5, '#fea', '#a94', '#666', 0.010),
    _road_base_type('railway', ('tram',),                             False, 1, '#000', None,   None,   0.200),
    _road_base_type('railway', ('rail', 'narrow_gauge', 'turntable'), False, 1, '#000', None,   None,   0.000),
    _road_base_type('highway', ('primary',),                          True,  5, '#fda', '#a84', '#666', 0.000),
    _road_base_type('highway', ('trunk',),                            True,  8, '#d60', '#830', '#666', 0.000),
    _road_base_type('highway', ('motorway',),                         True,  8, '#fa0', '#a40', '#666', 0.000)
]
_road_type = namedtuple('road_type', ('ordinal', 'width', 'fill', 'outline', 'outline_bridge', 'min_ppm'))
_road_types_count = 0
_road_types = defaultdict(dict)
def _road_type_add(btp: _road_base_type, link=False):
    global _road_types_count
    for v in btp.values:
        _road_types[btp.tag][v if not link else (v + '_link')] = \
            _road_type(_road_types_count, btp.width, btp.fill, btp.outline, btp.outline_bridge, btp.min_ppm)
        _road_types_count += 1
for tp in _road_base_types:
    if tp.has_link:
        _road_type_add(tp, link=True)
for tp in _road_base_types:
    _road_type_add(tp)


class ArtistRoad:
    def __init__(self):
        self.types = WeakKeyDictionary()

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        if element.tag != 'way':
            return False
        tags = tag_dict(element)
        if tags.get('area') == 'yes':
            return False
        for tag, types in _road_types.items():
            if tags.get(tag) in types:
                self.types[element] = types[tags.get(tag)]
                return True
        else:
            return False

    def draws_at_zoom(self, element: Element, zoom: int, osm_helper: OsmHelper):
        from camera import Camera  # FIXME yuck!
        return Camera(zoom_level=zoom).px_per_meter() >= self.types[element].min_ppm

    def draw(self, elements: Element, osm_helper: OsmHelper, camera, image_draw: ImageDraw):
        layers = defaultdict(lambda: defaultdict(list))
        for element in elements:
            tags = tag_dict(element)
            if tags.get('bridge') == 'yes':
                layer = int(tags.get('layer', 1))
            elif tags.get('tunnel') == 'yes':
                layer = int(tags.get('layer', -1))
            else:
                layer = int(tags.get('layer', 0))
            road_type: _road_type = self.types[element]
            layers[layer][road_type].append([camera.gps_to_px(point) for point in osm_helper.way_coordinates(element)])

        def draw_roads(color, width, roads):
            if color is not None:
                for road in roads:
                    image_draw.line(road, fill=color, width=width, joint='curve')

        for layer in range(-5, 7):
            # draw bridge outline
            if layer > 0:
                for road_type in sorted(layers[layer]):
                    draw_roads(road_type.outline_bridge, road_type.width + 2, layers[layer][road_type])

            # draw surface outline
            if layer == 0:
                for road_type in sorted(layers[layer]):
                    draw_roads(road_type.outline, road_type.width + 2, layers[layer][road_type])

            # draw line
            if layer >= 0:
                for road_type in sorted(layers[layer]):
                    draw_roads(road_type.fill, road_type.width, layers[layer][road_type])

    def approx_location(self, element: Element, osm_helper: OsmHelper):
        points = osm_helper.way_coordinates(element)
        if len(points) == 0:
            return []
        from operator import itemgetter
        return [Rectangle(min(points, key=itemgetter(0))[0], min(points, key=itemgetter(1))[1],
                          max(points, key=itemgetter(0))[0], max(points, key=itemgetter(1))[1])]


class ArtistRoadArea(ArtistArea):
    def __init__(self, types, fill, outline):
        super().__init__(fill=fill, outline=outline)
        self.types = types

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        tags = tag_dict(element)
        return ((element.tag == 'way' and tags.get('area') == 'yes')
             or (element.tag == 'relation' and tags.get('type') == 'multipolygon')) \
            and tags.get('highway') in self.types


_all = [
    ArtistRoadArea(('pedestrian',), '#aaa', '#999'),
    ArtistRoad()
]
