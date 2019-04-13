from collections import namedtuple, defaultdict
from weakref import WeakKeyDictionary
from xml.etree.ElementTree import Element

from PIL.ImageDraw import ImageDraw

from base_artist import explode_features, transform_shapes, element_to_lines, element_to_polygons, MappedFeature
from camera import Camera
from location_filter import Rectangle
from osm_helper import OsmHelper, tag_dict


_road_type = namedtuple('road_type',                     'width exp fill outline outline_bridge min_ppm')
_road_types = explode_features([
    # pedestrian roads
    ('highway', 'footway steps path',           _road_type(1,  0.0, '#aaa', None,   None,   0.30)),

    # link roads
    ('highway', 'tertiary_link',                _road_type(8,  0.4, '#fff', '#aaa', '#666', 0.10)),
    ('highway', 'secondary_link',               _road_type(10, 0.4, '#fea', '#a94', '#666', 0.05)),
    ('highway', 'primary_link',                 _road_type(10, 0.4, '#fda', '#a84', '#666', 0.00)),
    ('highway', 'trunk_link',                   _road_type(12, 0.4, '#d60', '#830', '#666', 0.00)),
    ('highway', 'motorway_link',                _road_type(12, 0.4, '#fa0', '#a40', '#666', 0.00)),

    # small roads
    ('highway', 'road',                         _road_type(5,  0.4, '#888', None,   None,   0.20)),
    ('highway', 'service',                      _road_type(5,  0.4, '#fff', '#ccc', '#ccc', 0.20)),
    ('highway', 'living_street',                _road_type(12, 0.4, '#ddd', None,   None,   0.15)),
    ('highway', 'residential unclassified',     _road_type(7,  0.4, '#fff', '#ccc', '#ccc', 0.10)),

    # large roads
    ('highway', 'tertiary',                     _road_type(10, 0.4, '#fff', '#aaa', '#666', 0.10)),
    ('highway', 'secondary',                    _road_type(12, 0.4, '#fea', '#a94', '#666', 0.05)),
    ('highway', 'primary',                      _road_type(12, 0.4, '#fda', '#a84', '#666', 0.00)),
    ('highway', 'trunk',                        _road_type(20, 0.4, '#d60', '#830', '#666', 0.00)),
    ('highway', 'motorway',                     _road_type(20, 0.4, '#fa0', '#a40', '#666', 0.00)),

    # railroads
    ('railway', 'tram',                         _road_type(1,  0.0, '#444', None,   None,   0.15)),
    ('railway', 'rail narrow_gauge turntable',  _road_type(1,  0.0, '#222', None,   None,   0.00)),
])


class A4_roadArtist:
    def __init__(self):
        self.types = WeakKeyDictionary()

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        tags = tag_dict(element)
        if tags.get('area') == 'yes' and \
                not tags.get('railway') == 'turntable':
            return False
        for tag, types in _road_types.items():
            try:
                self.types[element] = types[tags[tag]]
                return True
            except KeyError:
                pass
        return False

    def draws_at_zoom(self, element: Element, zoom: int, osm_helper: OsmHelper):
        return Camera(zoom_level=zoom).px_per_meter() >= self.types[element].style.min_ppm

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
            road_type: MappedFeature = self.types[element]
            layers[layer][road_type] += transform_shapes(element_to_lines(element, osm_helper), camera)

        def draw_roads(color, width, roads):
            if color is not None:
                for road in roads:
                    image_draw.line(road, fill=color, width=width, joint='curve')

        for layer in range(-5, 7):
            # draw bridge outline
            if layer > 0:
                for road_type in sorted(layers[layer]):
                    width = road_type.style.width * (camera.px_per_meter() ** road_type.style.exp)
                    draw_roads(road_type.style.outline_bridge, int(width) + 2, layers[layer][road_type])

            # draw surface outline
            if layer == 0:
                for road_type in sorted(layers[layer]):
                    width = road_type.style.width * (camera.px_per_meter() ** road_type.style.exp)
                    draw_roads(road_type.style.outline, int(width) + 2, layers[layer][road_type])

            # draw tunnel line
            if layer < 0:
                for road_type in sorted(layers[layer]):
                    width = road_type.style.width * (camera.px_per_meter() ** road_type.style.exp)
                    draw_roads(road_type.style.fill + '8', int(width), layers[layer][road_type])

            # draw line
            if layer >= 0:
                for road_type in sorted(layers[layer]):
                    width = road_type.style.width * (camera.px_per_meter() ** road_type.style.exp)
                    draw_roads(road_type.style.fill, int(width), layers[layer][road_type])

    def approx_location(self, element: Element, osm_helper: OsmHelper):
        points = osm_helper.way_coordinates(element)
        if len(points) == 0:
            return []
        from operator import itemgetter
        return [Rectangle(min(points, key=itemgetter(0))[0], min(points, key=itemgetter(1))[1],
                          max(points, key=itemgetter(0))[0], max(points, key=itemgetter(1))[1])]

    def __str__(self):
        return "Roads"
