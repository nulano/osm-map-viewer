from artists_util import ArtistArea, TagMatches


class ArtistGrass(ArtistArea):
    def __init__(self):
        super().__init__(fill='#dfd')
        self.filter += TagMatches('landuse', ('grass', 'meadow', 'village_green')) \
                   .Or(TagMatches('natural', ('grassland', )))


class ArtistOrchard(ArtistArea):
    def __init__(self):
        super().__init__(fill='#7d7')
        self.filter += TagMatches('landuse', ('vineyard', 'orchard', 'plant_nursery'))


class ArtistForest(ArtistArea):
    def __init__(self):
        super().__init__(fill='#ada')
        self.filter += TagMatches('landuse', ('forest', )) \
                   .Or(TagMatches('natural', ('wood', 'scrub', 'heath', 'moor')))


class ArtistMountain(ArtistArea):
    def __init__(self):
        super().__init__(fill='#777')
        self.filter += TagMatches('natural', ('bare_rock', 'scree', 'shingle', 'rock', 'stone', 'cave_entrance'))


_all = {'grass': ArtistGrass(),
        'orchard': ArtistOrchard(),
        'Forest': ArtistForest(),
        'mountain': ArtistMountain()}
