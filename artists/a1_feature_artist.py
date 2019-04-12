from util_artist import Base, Feature, StyleOutlined, StyleArea, StyleLine, StylePoint

_land_types = [
    # buildings, built-up areas
    Feature('leisure',  'stadium sports_centre',            StyleArea('#efb', 0, False)),
    Feature('man_made', 'bridge',                           StyleArea('#ddc', 0, False)),
    Feature('aeroway',  'apron helipad',                    StyleArea('#bbb', 0, False)),
    Feature('aeroway',  'taxiway',                          StyleLine('#aaa', 5, 0.000)),
    Feature('aeroway',  'runway',                           StyleLine('#aaa', 7, 0.000)),
    Feature('highway',  'footway pedestrian',               StyleArea('#ccc', 0, True)),
    Feature('building', None,                               StyleOutlined('#ddc', 8, '#ccb', 0.150)),
    Feature('building', 'church cathedral chapel mosque '
                        'synagogue temple shrine '
                        'hospital',                         StyleOutlined('#ccb', 0, '#bba', 0.150)),
    Feature('leisure',  'pitch track',                      StyleOutlined('#df8', 0, '#de8', 0.150)),
    Feature('leisure',  'playground',                       StyleOutlined('#cfc', 0, '#beb', 0.150)),
    Feature('amenity',  'parking',                          StyleArea('#eef', 0, False)),

    # small features
    Feature('barrier',  'wall fence handrail',              StyleLine('#daa', 1, 0.300)),
    Feature('barrier',  'city_wall',                        StyleLine('#d44', 3, 0.200)),
    Feature('barrier',  'hedge',                            StyleLine('#ada', 2, 0.300)),
    Feature('natural',  'tree_row',                         StyleLine('#ada', 4, 0.300)),
    Feature('natural',  'tree',                             StylePoint('#ada', 4, 0.500)),
]


class A1_featureArtist(Base):
    def __init__(self):
        super().__init__(_land_types)

    def __str__(self):
        return "Features"
