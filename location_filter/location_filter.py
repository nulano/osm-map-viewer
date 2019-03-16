import math

from osm_helper import OsmHelper


class Rectangle:
    def __init__(self, min_lat: float, min_lon: float, max_lat: float, max_lon: float):
        self.min_lat = min_lat
        self.min_lon = min_lon
        self.max_lat = max_lat
        self.max_lon = max_lon 


class LocationFilter:
    def __init__(self, typical_query_size: float, bounding_box: Rectangle, draw_pairs: list, osm_helper: OsmHelper):
        self.typical_query_size = typical_query_size
        self.bounding_box = bounding_box
        self.draw_pairs = [(element, artist, artist.approx_location(element, osm_helper)) for element, artist in draw_pairs]

    # TODO close_enough
    def get_pairs(self, rectangle: Rectangle):
        out = []
        for element, artist, approx_location in self.draw_pairs:
            for bb in approx_location:
                if max(rectangle.min_lat, bb.min_lat) > min(rectangle.max_lat, bb.max_lat) \
                or max(rectangle.min_lon, bb.min_lon) > min(rectangle.max_lon, bb.max_lon):
                    break
            else:
                out.append((element, artist))
        return out
