from xml.etree.ElementTree import Element

from location_filter import Rectangle
from osm_helper import OsmHelper


class ArtistPark:
    def __init__(self):
        pass
    
    def wants_element(self, element: Element, osm_helper: OsmHelper):
        return False
    
    def draws_at_zoom(self, element: Element, zoom: int, osm_helper: OsmHelper):
        return True
    
    def draw(self, elements: Element, osm_helper: OsmHelper, camera, image_draw):
        pass
    
    def approx_location(self, element: Element, osm_helper: OsmHelper):
        return []
