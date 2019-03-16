from xml.etree.ElementTree import Element

from PIL.ImageDraw import ImageDraw

from location_filter import Rectangle
from osm_helper import OsmHelper, tag_dict

from artist_base import ArtistArea, ElementFilter


class ArtistBuilding:
    def __init__(self): pass

    def wants_element(self, element: Element, osm_helper: OsmHelper):
        return ElementFilter().IsArea().HasTag('building')(element, osm_helper)

    def draws_at_zoom(self, element: Element, zoom: int, osm_helper: OsmHelper):
        return True

    def draw(self, elements: Element, osm_helper: OsmHelper, camera, image_draw: ImageDraw):
        for el in elements:
            polys = []
            tags = tag_dict(el)
            if el.tag == 'relation':
                polys += osm_helper.multipolygon_to_wsps(el)
            elif el.tag == 'way':
                polys.append(osm_helper.way_coordinates(el))
            else:
                print('warn: unknown type:', el.tag, 'for ArtistBuilding')
            for poly in polys:
                image_draw.polygon([camera.gps_to_px(point) for point in poly], fill='#ddc', outline='#ccb')

    def approx_location(self, element: Element, osm_helper: OsmHelper):
        return []


class ArtistSportArea(ArtistArea):
    def __init__(self): super().__init__()

    def wants_element_tags(self, tags: dict):
        return tags.get('leisure') in ('pitch', 'track')

    def draw_poly(self, poly: list, image_draw: ImageDraw):
        image_draw.polygon(poly, fill='#ef9', outline='#de8')


class ArtistPlayground(ArtistArea):
    def __init__(self): super().__init__()

    def wants_element_tags(self, tags: dict):
        return tags.get('leisure') in ('playground',)

    def draw_poly(self, poly: list, image_draw: ImageDraw):
        image_draw.polygon(poly, fill='#cfc', outline='#beb')


class ArtistParking(ArtistArea):
    def __init__(self): super().__init__()

    def wants_element_tags(self, tags: dict):
        return tags.get('amenity') in ('parking',)

    def draw_poly(self, poly: list, image_draw):
        image_draw.polygon(poly, fill='#eef')


_all = {'building': ArtistBuilding(),
        'sport': ArtistSportArea(),
        'playground': ArtistPlayground(),
        'parking': ArtistParking()}
