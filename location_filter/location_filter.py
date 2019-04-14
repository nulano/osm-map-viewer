from collections import defaultdict
from math import floor, ceil

from osm_helper import OsmHelper

CELL = 0.05


class Rectangle:
    def __init__(self, min_lat: float, min_lon: float, max_lat: float, max_lon: float):
        self.min_lat = min_lat
        self.min_lon = min_lon
        self.max_lat = max_lat
        self.max_lon = max_lon

    def __repr__(self):
        return 'Rectangle({}, {}, {}, {})'.format(repr(self.min_lat), repr(self.min_lon),
                                                  repr(self.max_lat), repr(self.max_lon))

    def __str__(self):
        return '[{}, {}, {}, {}]'.format(str(self.min_lat), str(self.min_lon), str(self.max_lat), str(self.max_lon))


class LocationFilter:
    def __init__(self, typical_query_size: float, bounding_box: Rectangle, draw_pairs: list, osm_helper: OsmHelper):
        self.typical_query_size = typical_query_size
        self.bounding_box = bounding_box
        self.boxes = defaultdict(list)
        self.unbounded = []
        self.pairs = draw_pairs
        for i, (element, artist) in enumerate(draw_pairs):
            location = artist.approx_location(element, osm_helper)
            for bbox in location:
                for lat in range(floor(bbox.min_lat / CELL), ceil(bbox.max_lat / CELL)):
                    for lon in range(floor(bbox.min_lon / CELL), ceil(bbox.max_lon / CELL)):
                        self.boxes[(lat, lon)].append((bbox, i))
            if len(location) == 0:
                self.unbounded.append(i)

    def get_pairs(self, rect: Rectangle):
        out = set(self.unbounded)
        for lat in range(floor(rect.min_lat / CELL), ceil(rect.max_lat / CELL)):
            for lon in range(floor(rect.min_lon / CELL), ceil(rect.max_lon / CELL)):
                for bbox, i in self.boxes[(lat, lon)]:
                    if max(rect.min_lat, bbox.min_lat) <= min(rect.max_lat, bbox.max_lat) \
                            and max(rect.min_lon, bbox.min_lon) <= min(rect.max_lon, bbox.max_lon):
                        out.add(i)
        return [self.pairs[i] for i in sorted(out)]
