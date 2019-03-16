from artist_base import ArtistArea


class ArtistWater(ArtistArea):
    def __init__(self): super().__init__()

    def wants_element_tags(self, tags: dict):
        return tags.get('natural') in ('water', 'bay', 'spring', 'hot_spring', 'blowhole') \
            or tags.get('landuse') in ('basin', 'reservoir') \
            or tags.get('waterway')

    def draw_poly(self, poly: list, image_draw): image_draw.polygon(poly, fill='#ade')


_all = {'water': ArtistWater()}
