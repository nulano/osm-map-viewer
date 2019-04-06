from artists_util import Base, Feature, StyleOutlined, StyleArea, StyleLine, StylePoint

_land_types = [
    # buildings, built-up areas
    Feature('highway',  'pedestrian',                   StyleArea('#aaa', 0)),
    Feature('leisure',  'stadium sports_centre',        StyleArea('#efb', 0)),
    Feature('leisure',  'garden',                       StyleArea('#beb', 0)),
    Feature('man_made', 'bridge',                       StyleArea('#ddd', 0)),
    Feature('aeroway',  'apron',                        StyleArea('#bbb', 0)),
    Feature('aeroway',  'taxiway',                      StyleLine('#aaa', 5, 0.000)),
    Feature('aeroway',  'runway',                       StyleLine('#aaa', 7, 0.000)),
    Feature('building', None,                           StyleOutlined('#ddc', 4, '#ccb', 0.150)),
    Feature('leisure',  'pitch track',                  StyleOutlined('#df8', 4, '#de8', 0.150)),
    Feature('leisure',  'playground',                   StyleOutlined('#cfc', 4, '#beb', 0.150)),
    Feature('amenity',  'parking',                      StyleArea('#eef', 4)),

    # small features
    Feature('natural', 'tree_row',                      StyleLine('#ada', 4, 0.300)),
    Feature('natural', 'tree',                          StylePoint('#ada', 4, 0.500)),
]


class ArtistFeature(Base):
    def __init__(self):
        super().__init__(_land_types)
