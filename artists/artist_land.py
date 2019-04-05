from collections import namedtuple, defaultdict
from weakref import WeakKeyDictionary
from xml.etree.ElementTree import Element

from PIL.ImageDraw import ImageDraw

from artists_util import ArtistArea, TagMatches, ArtistWay, explode_tag_style_map, FilterTrue, IsArea, \
    element_to_polygons, element_to_lines, transform_shapes, element_to_points
from camera import Camera
from geometry import polygon_area
from location_filter import Rectangle
from osm_helper import OsmHelper, tag_dict

_area_type = namedtuple('area_type',
                        'ordinal fill min_area outline outline_min_area outline_width additional_filter')
_area_types = explode_tag_style_map([
    ('natural', 'bare_rock scree shingle rock stone',       _area_type(None, '#777', 0, None,  0, 1, FilterTrue)),
    ('landuse', 'forest',                                   _area_type(None, '#ada', 0, None,  0, 1, FilterTrue)),
    ('natural', 'wood scrub heath moor',                    _area_type(None, '#ada', 0, None,  0, 1, FilterTrue)),
    ('landuse', 'industrial port',                          _area_type(None, '#ffc', 0, None,  0, 1, FilterTrue)),
    ('landuse', 'retail commercial',                        _area_type(None, '#cff', 0, None,  0, 1, FilterTrue)),
    ('amenity', 'school kindergarten college university',   _area_type(None, '#fcf', 0, None,  0, 1, FilterTrue)),
    ('landuse', 'grass meadow village_green',               _area_type(None, '#dfd', 0, None,  0, 1, FilterTrue)),
    ('natural', 'grassland',                                _area_type(None, '#dfd', 0, None,  0, 1, FilterTrue)),
    ('landuse', 'vineyard orchard plant_nursery',           _area_type(None, '#7d7', 0, None,  0, 1, FilterTrue)),
    ('landuse', 'cemetary',                                 _area_type(None, '#5a5', 0, None,  0, 1, FilterTrue)),
    ('amenity', 'grave_yard',                               _area_type(None, '#5a5', 0, None,  0, 1, FilterTrue)),
    ('leisure', 'park',                                     _area_type(None, '#cfc', 0, None,  0, 1, FilterTrue)),
    ('leisure', 'garden',                                   _area_type(None, '#beb', 0, None,  0, 1, FilterTrue)),
])


class ArtistLand:
    def __init__(self):
        self.types = WeakKeyDictionary()

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        tags = tag_dict(element)
        if not IsArea(tags, element, osm_helper):
            return False
        for tag, types in _area_types.items():
            try:
                style: _area_type = types[tags[tag]]
            except KeyError:
                continue
            if style.additional_filter(tags, element, osm_helper):
                self.types[element] = style
                return True
        else:
            return False

    def draws_at_zoom(self, element: Element, zoom: int, osm_helper: OsmHelper):
        style = self.types[element]
        if style.min_area == 0:
            return True
        # assumes consistent scale (e.g. cylindrical) transform
        camera = Camera(zoom_level=zoom)
        area = sum(map(polygon_area, transform_shapes(element_to_polygons(element, osm_helper), camera)))
        return area >= style.min_area

    def draw(self, elements: Element, osm_helper: OsmHelper, camera: Camera, image_draw: ImageDraw):
        element_groups = defaultdict(list)
        for element in elements:
            element_groups[self.types[element]].append(element)
        for style in sorted(element_groups):
            polygons, outlines = [], []
            for element in element_groups[style]:
                shape = transform_shapes(element_to_polygons(element, osm_helper), camera)
                area = sum(map(polygon_area, shape))
                if area >= style.min_area and style.fill is not None:
                    polygons += shape
                if area >= style.outline_min_area and style.outline is not None:
                    outlines += transform_shapes(element_to_lines(element, osm_helper), camera)
            for polygon in polygons:
                image_draw.polygon(polygon, fill=style.fill)
            for outline in outlines:
                image_draw.line(outline, fill=style.outline, width=style.outline_width)

    def approx_location(self, element: Element, osm_helper: OsmHelper):
        points = element_to_points(element, osm_helper)
        if len(points) == 0:
            return []
        from operator import itemgetter
        return [Rectangle(min(points, key=itemgetter(0))[0], min(points, key=itemgetter(1))[1],
                          max(points, key=itemgetter(0))[0], max(points, key=itemgetter(1))[1])]


class ArtistWaterArea(ArtistArea):
    def __init__(self):
        super().__init__(fill='#ade')
        self.filter += TagMatches('natural', ('water', 'bay', 'spring', 'hot_spring', 'blowhole')) \
                   .Or(TagMatches('landuse', ('basin', 'reservoir'))) \
                   .Or(TagMatches('waterway', ('riverbank', )))


class ArtistWaterWay(ArtistWay):
    def __init__(self, types, width=5):
        super().__init__(fill='#ade', width=width)
        self.filter += TagMatches('waterway', types)


_all = [
    ArtistLand(),
    ArtistWaterArea(),
    ArtistWaterWay(width=3, types=('stream', 'canal')),
    ArtistWaterWay(width=5, types=('river', ))
]
