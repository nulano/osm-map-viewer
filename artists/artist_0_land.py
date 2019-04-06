from artists_util import Base, Feature, StyleComp, StyleArea, StyleLine

_land_types = [
    # large land areas
    Feature('natural',  'bare_rock scree shingle rock stone',       StyleArea('#777', 0)),
    Feature('landuse',  'forest',                                   StyleArea('#ada', 0)),
    Feature('natural',  'wood scrub heath moor',                    StyleArea('#ada', 0)),

    # land designation / zoning
    Feature('landuse',  'military',                                 StyleArea('#fdd', 8)),
    Feature('landuse',  'industrial port',                          StyleArea('#ffc', 8)),
    Feature('landuse',  'retail commercial',                        StyleArea('#cff', 8)),
    Feature('amenity',  'school kindergarten college university',   StyleArea('#fcf', 8)),
    Feature('landuse',  'brownfield construction',                  StyleArea('#cca', 0)),

    # small land areas
    Feature('landuse',  'grass meadow village_green',               StyleArea('#dfd', 0)),
    Feature('natural',  'grassland',                                StyleArea('#dfd', 0)),
    Feature('landuse',  'vineyard orchard plant_nursery',           StyleArea('#7d7', 0)),
    Feature('landuse',  'cemetery',                                 StyleArea('#5a5', 0)),
    Feature('amenity',  'grave_yard',                               StyleArea('#5a5', 0)),
    Feature('landuse',  'allotments',                               StyleArea('#beb', 0)),
    Feature('leisure',  'park',                                     StyleArea('#cfc', 0)),

    # water features
    Feature('natural',  'water bay spring hot_spring blowhole',     StyleArea('#ade', 0)),
    Feature('landuse',  'basin reservoir',                          StyleArea('#ade', 0)),
    Feature('waterway', 'riverbank',                                StyleArea('#ade', 0)),
    Feature('waterway', 'stream canal',                             StyleLine('#ade', 3, 0.000)),
    Feature('waterway', 'river',                                    StyleLine('#ade', 5, 0.000)),
]


class ArtistLand(Base):
    def __init__(self):
        super().__init__(_land_types)
