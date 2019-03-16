from artist_base import ArtistArea, TagMatches, TagPresent


class ArtistBuilding(ArtistArea):
    def __init__(self):
        super().__init__(fill='#ddc', outline='#ccb')
        self.filter += TagPresent('building')


class ArtistSportArea(ArtistArea):
    def __init__(self):
        super().__init__(fill='#ef9', outline='#de8')
        self.filter += TagMatches('leisure', ('pitch', 'track'))


class ArtistPlayground(ArtistArea):
    def __init__(self):
        super().__init__(fill='#cfc', outline='#beb')
        self.filter += TagMatches('leisure', ('playground', ))


class ArtistParking(ArtistArea):
    def __init__(self):
        super().__init__(fill='#eef')
        self.filter += TagMatches('amenity', ('parking', ))


_all = {'building': ArtistBuilding(),
        'sport': ArtistSportArea(),
        'playground': ArtistPlayground(),
        'parking': ArtistParking()}
