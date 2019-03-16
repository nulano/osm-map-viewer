from artists_util import ArtistArea, TagMatches, ArtistWay


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


_all = {'water': ArtistWaterArea(),
        'water_river':  ArtistWaterWay(width=5, types=('river', )),
        'water_stream': ArtistWaterWay(width=5, types=('stream', ))}
