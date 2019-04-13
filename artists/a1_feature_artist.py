from base_artist import BaseArtist, Feature, StyleOutlined, StyleArea, StyleLine, StylePoint

_land_types = [
    # small features
    Feature('barrier',  'hedge',                            StyleLine('#ada',  3, 0.8, 0.50)),
    Feature('natural',  'tree_row',                         StyleLine('#ada',  5, 0.8, 0.50)),
    Feature('highway',  'pedestrian',                       StyleLine('#ccc',  5, 1.0, 0.30, skip_area=True)),
    Feature('barrier',  'wall fence handrail',              StyleLine('#daa',  1, 0.0, 0.50)),
    Feature('barrier',  'city_wall',                        StyleLine('#d44',  3, 0.0, 0.30)),
    Feature('natural',  'tree',                             StylePoint('#ada', 4, 0.75)),

    # buildings, man-made objects
    Feature('building', None,                               StyleOutlined('#ddc', 8, '#ccb', 0.50)),
    Feature('building', 'church cathedral chapel mosque '
                        'synagogue temple shrine '
                        'hospital',                         StyleOutlined('#ccb', 1, '#bba', 0.25)),
    Feature('leisure',  'pitch track',                      StyleOutlined('#df8', 4, '#de8', 0.50)),
    Feature('leisure',  'playground',                       StyleOutlined('#cfc', 4, '#beb', 0.50)),
    Feature('amenity',  'parking',                          StyleArea('#eef',  16)),
]


class A1_featureArtist(BaseArtist):
    def __init__(self):
        super().__init__(_land_types)

    def __str__(self):
        return "Features"
