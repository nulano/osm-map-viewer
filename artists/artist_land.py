from xml.etree.ElementTree import Element

from location_filter import Rectangle
from osm_helper import OsmHelper, tag_dict
from artist_base import ArtistArea


class ArtistGrass(ArtistArea):
    def __init__(self): super().__init__()

    def wants_element_tags(self, tags: dict):
        return tags.get('landuse') in ('grass', 'meadow', 'village_green') \
            or tags.get('natural') in ('grassland', )

    def draw_poly(self, poly: list, image_draw): image_draw.polygon(poly, fill='#dfd')


class ArtistOrchard(ArtistArea):
    def __init__(self): super().__init__()

    def wants_element_tags(self, tags: dict):
        return tags.get('landuse') in ('vineyard', 'orchard', 'plant_nursery')

    def draw_poly(self, poly: list, image_draw): image_draw.polygon(poly, fill='#7d7')


class ArtistForest(ArtistArea):
    def __init__(self):
        super().__init__()

    def wants_element_tags(self, tags: dict):
        return tags.get('landuse') == 'forest' \
            or tags.get('natural') in ('wood', 'scrub', 'heath', 'moor')

    def draw_poly(self, poly: list, image_draw): image_draw.polygon(poly, fill='#ada')


class ArtistMountain(ArtistArea):
    def __init__(self): super().__init__()

    def wants_element_tags(self, tags: dict):
        return tags.get('natural') in ('bare_rock', 'scree', 'shingle', 'rock', 'stone', 'cave_entrance')

    def draw_poly(self, poly: list, image_draw): image_draw.polygon(poly, fill='#777')


_all = {'grass': ArtistGrass(),
        'orchard': ArtistOrchard(),
        'Forest': ArtistForest(),
        'mountain': ArtistMountain()}
