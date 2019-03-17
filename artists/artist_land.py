from artists_util import ArtistArea, TagMatches, ArtistWay


class ArtistMountain(ArtistArea):
    def __init__(self):
        super().__init__(fill='#777')
        self.filter += TagMatches('natural', ('bare_rock', 'scree', 'shingle', 'rock', 'stone', 'cave_entrance'))


class ArtistForest(ArtistArea):
    def __init__(self):
        super().__init__(fill='#ada')
        self.filter += TagMatches('landuse', ('forest', )) \
                   .Or(TagMatches('natural', ('wood', 'scrub', 'heath', 'moor')))


class ArtistIndustrial(ArtistArea):
    def __init__(self):
        super().__init__(fill='#ffc')
        self.filter += TagMatches('landuse', ('industrial', 'port'))


class ArtistCommercial(ArtistArea):
    def __init__(self):
        super().__init__(fill='#cff')
        self.filter += TagMatches('landuse', ('retail', 'commercial'))


class ArtistEducation(ArtistArea):
    def __init__(self):
        super().__init__(fill='#fcf')
        self.filter += TagMatches('amenity', ('college', 'kindergarten', 'school', 'university'))


class ArtistGrass(ArtistArea):
    def __init__(self):
        super().__init__(fill='#dfd')
        self.filter += TagMatches('landuse', ('grass', 'meadow', 'village_green')) \
                   .Or(TagMatches('natural', ('grassland', )))


class ArtistOrchard(ArtistArea):
    def __init__(self):
        super().__init__(fill='#7d7')
        self.filter += TagMatches('landuse', ('vineyard', 'orchard', 'plant_nursery'))


class ArtistCemetery(ArtistArea):
    def __init__(self):
        super().__init__(fill='#5a5')
        self.filter += TagMatches('landuse', ('cemetery',)).Or(TagMatches('amenity', ('grave_yard', )))


class ArtistPark(ArtistArea):
    def __init__(self):
        super().__init__(fill='#cfc')
        self.filter += TagMatches('leisure', ('park', ))


class ArtistGarden(ArtistArea):
    def __init__(self):
        super().__init__(fill='#beb')
        self.filter += TagMatches('leisure', ('garden', ))


class ArtistWaterArea(ArtistArea):
    def __init__(self):
        super().__init__(fill='#ade')
        self.filter += TagMatches('natural', ('water', 'bay', 'spring', 'hot_spring', 'blowhole')) \
                   .Or(TagMatches('landuse', ('basin', 'reservoir'))) \
                   .Or(TagMatches('waterway', ('riverbank', )))


class ArtistWaterWay(ArtistWay):
    def __init__(self, types, width=5):
        super().__init__(fill='#ade', width=width)
        self.filter += TagMatches('waterway', types)


_all = {
    'mountain': ArtistMountain(),
    'forest': ArtistForest(),
    'industrial': ArtistIndustrial(),
    'commercial': ArtistCommercial(),
    'school': ArtistEducation(),
    'grass': ArtistGrass(),
    'orchard': ArtistOrchard(),
    'cemetery': ArtistCemetery(),
    'park': ArtistPark(),
    'garden': ArtistGarden(),
    'water': ArtistWaterArea(),
    'water_line_small': ArtistWaterWay(width=3, types=('stream', 'canal')),
    'water_line':  ArtistWaterWay(width=5, types=('river', ))
}
