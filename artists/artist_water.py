from artists_util import ArtistArea, TagMatches, TagPresent


class ArtistWaterArea(ArtistArea):
    def __init__(self):
        super().__init__(fill='#ade')
        self.filter += TagMatches('natural', ('water', 'bay', 'spring', 'hot_spring', 'blowhole')) \
                   .Or(TagMatches('landuse', ('basin', 'reservoir'))) \
                   .Or(TagMatches('waterway', ('riverbank', )))


_all = {'water': ArtistWaterArea()}
