from collections import namedtuple, defaultdict
from weakref import WeakKeyDictionary
from xml.etree.ElementTree import Element

from PIL.ImageDraw import ImageDraw

from artists_util import ArtistArea, explode_tag_style_map
from camera import Camera
from location_filter import Rectangle
from osm_helper import OsmHelper, tag_dict


_road_type = namedtuple('road_type',                 'ordinal width fill outline outline_bridge min_ppm')
_road_types = explode_tag_style_map([
    ('highway', 'tertiary_link',                _road_type(None, 5, '#fff', '#aaa', '#666', 0.050)),
    ('highway', 'secondary_link',               _road_type(None, 5, '#fea', '#a94', '#666', 0.010)),
    ('highway', 'primary_link',                 _road_type(None, 5, '#fda', '#a84', '#666', 0.000)),
    ('highway', 'trunk_link',                   _road_type(None, 8, '#d60', '#830', '#666', 0.000)),
    ('highway', 'motorway_link',                _road_type(None, 8, '#fa0', '#a40', '#666', 0.000)),
    ('highway', 'footway steps path',           _road_type(None, 1, '#aaa', None,   None,   0.200)),
    ('highway', 'pedestrian',                   _road_type(None, 2, '#aaa', None,   None,   0.200)),
    ('highway', 'road',                         _road_type(None, 2, '#888', None,   None,   0.150)),
    ('highway', 'service',                      _road_type(None, 2, '#fff', '#ccc', '#ccc', 0.150)),
    ('highway', 'living_street',                _road_type(None, 5, '#ddd', None,   None,   0.150)),
    ('highway', 'residential unclassified',     _road_type(None, 3, '#fff', '#ccc', '#ccc', 0.100)),
    ('highway', 'tertiary',                     _road_type(None, 5, '#fff', '#aaa', '#666', 0.050)),
    ('highway', 'secondary',                    _road_type(None, 5, '#fea', '#a94', '#666', 0.010)),
    ('railway', 'tram',                         _road_type(None, 1, '#000', None,   None,   0.200)),
    ('railway', 'rail narrow_gauge turntable',  _road_type(None, 1, '#000', None,   None,   0.000)),
    ('highway', 'primary',                      _road_type(None, 5, '#fda', '#a84', '#666', 0.000)),
    ('highway', 'trunk',                        _road_type(None, 8, '#d60', '#830', '#666', 0.000)),
    ('highway', 'motorway',                     _road_type(None, 8, '#fa0', '#a40', '#666', 0.000))
])


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
            try:
                self.types[element] = types[tags[tag]]
                return True
            except KeyError:
                pass
        else:
            return False

    def draws_at_zoom(self, element: Element, zoom: int, osm_helper: OsmHelper):
        return Camera(zoom_level=zoom).px_per_meter() >= self.types[element].min_ppm

    def draw(self, elements: Element, osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        layers = defaultdict(lambda: defaultdict(list))
        for element in elements:
            tags = tag_dict(element)
            try:
                layer = int(tags['layer'])
            except (KeyError, ValueError):
                layer = 1 if tags.get('bridge') == 'yes'\
                    else -1 if tags.get('tunnel') == 'yes'\
                    else 0
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
