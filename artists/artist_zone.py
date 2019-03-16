from artist_base import ArtistArea, TagMatches


class ArtistPark(ArtistArea):
    def __init__(self):
        super().__init__(fill='#cfc')
        self.filter += TagMatches('leisure', ('park', ))


class ArtistGarden(ArtistArea):
    def __init__(self):
        super().__init__(fill='#beb')
        self.filter += TagMatches('leisure', ('garden', ))


class ArtistSchool(ArtistArea):
    def __init__(self):
        super().__init__(fill='#fdf')
        self.filter += TagMatches('amenity', ('college', 'kindergarten', 'school', 'university'))


_all = {'school': ArtistSchool(),
        'park': ArtistPark(),
        'garden': ArtistGarden()}
