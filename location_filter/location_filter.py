import math

from osm_helper import OsmHelper


class Rectangle:
    def __init__(self, min_lat, min_lon, max_lat, max_lon):
        self.min_lat = min_lat
        self.min_lon = min_lon
        self.max_lat = max_lat
        self.max_lon = max_lon

    def intersects(self, other):
        return max(self.min_lat, other.min_lat) < min(self.max_lat, other.max_lat) \
                and max(self.min_lon, other.min_lon) < min(self.max_lon, other.max_lon) 


class LocationFilter:
    def __init__(self, typical_query_size: float, bounding_box: Rectangle,
                 draw_pairs: list, osm_helper: OsmHelper):
        self.typical_query_size = typical_query_size
        self.bounding_box = bounding_box
        self.draw_pairs = draw_pairs
        self.osm_helper = osm_helper
    
    def get_pairs(self, rectangle: Rectangle):
        out = []
        for el, artist in self.draw_pairs:
            for bb in artist.approx_location(el, self.osm_helper):
                if rectangle.intersects(bb):
                    out.append((el, artist))
                    break
        return out
