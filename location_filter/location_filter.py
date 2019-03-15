import math

from osm_helper import OsmHelper


class Rectangle:
    def __init__(self, min_lat: float, min_lon: float, max_lat: float, max_lon: float):
        self.min_lat = min_lat
        self.min_lon = min_lon
        self.max_lat = max_lat
        self.max_lon = max_lon 


class LocationFilter:
    def __init__(self, typical_query_size: float, bounding_box: Rectangle,
                 draw_pairs: list, osm_helper: OsmHelper):
        self.typical_query_size = typical_query_size
        self.bounding_box = bounding_box
        self.draw_pairs = draw_pairs
        self.osm_helper = osm_helper

    # TODO close_enough
    def get_pairs(self, rectangle: Rectangle):
        out = []
        for el, artist in self.draw_pairs:
            for bb in artist.approx_location(el, self.osm_helper):
                if max(rectangle.min_lat, bb.min_lat) < min(rectangle.max_lat, bb.max_lat) \
                        and max(rectangle.min_lon, bb.min_lon) < min(rectangle.max_lon, bb.max_lon):
                    out.append((el, artist))
                    break
        return out
