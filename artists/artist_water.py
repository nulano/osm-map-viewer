from artists_util import ArtistArea, TagMatches, TagPresent


class ArtistWater(ArtistArea):
    def __init__(self):
        super().__init__(fill='#ade')
        self.filter += TagMatches('natural', ('water', 'bay', 'spring', 'hot_spring', 'blowhole')) \
                   .Or(TagMatches('landuse', ('basin', 'reservoir'))) \
                   .Or(TagPresent('waterway'))


_all = {'water': ArtistWater()}
