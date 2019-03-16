from artist_base import ArtistArea


class ArtistPark(ArtistArea):
    def __init__(self):
        super().__init__()

    def wants_element_tags(self, tags: dict):
        return tags.get('leisure') in ('park',)

    def draw_poly(self, poly: list, image_draw):
        image_draw.polygon(poly, fill='#cfc')


class ArtistGarden(ArtistArea):
    def __init__(self):
        super().__init__()

    def wants_element_tags(self, tags: dict):
        return tags.get('leisure') in ('garden',)

    def draw_poly(self, poly: list, image_draw):
        image_draw.polygon(poly, fill='#beb')


class ArtistSchool(ArtistArea):
    def __init__(self):
        super().__init__()

    def wants_element_tags(self, tags: dict):
        return tags.get('amenity') in ('college', 'kindergarten', 'school', 'university')

    def draw_poly(self, poly: list, image_draw):
        image_draw.polygon(poly, fill='#fdf')


_all = {'school': ArtistSchool(),
        'park': ArtistPark(),
        'garden': ArtistGarden()}
