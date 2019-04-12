from util_artist import Base, Feature, StyleArea, StyleLine

_land_types = [
    # land designation / zoning
    Feature('landuse',  'military',                                 StyleArea('#fdd', 0, False)),
    Feature('landuse',  'industrial port',                          StyleArea('#ffc', 0, False)),
    Feature('landuse',  'retail commercial',                        StyleArea('#cff', 0, False)),
    Feature('amenity',  'school kindergarten college university',   StyleArea('#fcf', 0, False)),
    Feature('amenity',  'hospital',                                 StyleArea('#ddf', 0, False)),
    Feature('leisure',  'park',                                     StyleArea('#dfd', 0, False)),
    Feature('landuse',  'brownfield construction',                  StyleArea('#cca', 0, False)),

    # land areas
    Feature('landuse',  'forest',                                   StyleArea('#ada', 0, False)),
    Feature('natural',  'wood scrub heath moor',                    StyleArea('#ada', 0, False)),
    Feature('landuse',  'grass meadow village_green',               StyleArea('#cfc', 0, False)),
    Feature('natural',  'grassland',                                StyleArea('#cfc', 0, False)),
    Feature('landuse',  'vineyard orchard plant_nursery',           StyleArea('#7d7', 0, False)),
    Feature('landuse',  'cemetery',                                 StyleArea('#5a5', 0, False)),
    Feature('amenity',  'grave_yard',                               StyleArea('#5a5', 0, False)),
    Feature('landuse',  'allotments',                               StyleArea('#beb', 0, False)),
    Feature('leisure',  'garden',                                   StyleArea('#beb', 0, False)),

    # water features
    Feature('natural',  'water bay spring hot_spring blowhole',     StyleArea('#ade', 0, False)),
    Feature('landuse',  'basin reservoir',                          StyleArea('#ade', 0, False)),
    Feature('waterway', 'riverbank',                                StyleArea('#ade', 0, False)),
    Feature('waterway', 'stream canal',                             StyleLine('#ade', 3, 0.000)),
    Feature('waterway', 'river',                                    StyleLine('#ade', 5, 0.000)),
    Feature('man_made', 'pier',                                     StyleArea('#eed', 0, False)),  # TODO can be line
]


class A0_landArtist(Base):
    def __init__(self):
        super().__init__(_land_types)

    def __str__(self):
        return "Land Types"
