from base_artist import BaseArtist, Feature, StyleArea, StyleLine

_land_types = [
    # land designation / zoning
    Feature('landuse',  'military',                                 StyleArea('#fdd',   4)),
    Feature('landuse',  'industrial port',                          StyleArea('#ffc',   4)),
    Feature('landuse',  'retail commercial',                        StyleArea('#cff',   4)),
    Feature('amenity',  'school kindergarten college university',   StyleArea('#fcf',   4)),
    Feature('amenity',  'hospital',                                 StyleArea('#ddf',   4)),
    Feature('leisure',  'park',                                     StyleArea('#dfd',   4)),
    Feature('landuse',  'brownfield construction',                  StyleArea('#cca',   4)),

    # land areas
    Feature('landuse',  'forest',                                   StyleArea('#ada',   0)),
    Feature('natural',  'wood scrub heath moor',                    StyleArea('#ada',   0)),
    Feature('landuse',  'grass meadow village_green',               StyleArea('#cfc',   0)),
    Feature('natural',  'grassland',                                StyleArea('#cfc',   0)),
    Feature('landuse',  'vineyard orchard plant_nursery',           StyleArea('#7d7',   4)),
    Feature('landuse',  'cemetery',                                 StyleArea('#5a5',   4)),
    Feature('amenity',  'grave_yard',                               StyleArea('#5a5',   4)),
    Feature('landuse',  'allotments',                               StyleArea('#beb',   4)),
    Feature('leisure',  'garden',                                   StyleArea('#beb',   4)),

    # water features
    Feature('natural',  'water bay spring hot_spring blowhole',     StyleArea('#ade',   0)),
    Feature('landuse',  'basin reservoir',                          StyleArea('#ade',   0)),
    Feature('waterway', 'riverbank',                                StyleArea('#ade',   0)),
    Feature('waterway', 'stream canal',                             StyleLine('#ade',  6, 0.4, 0.00)),
    Feature('waterway', 'river',                                    StyleLine('#ade', 10, 0.4, 0.00)),
    Feature('man_made', 'pier',                                     StyleArea('#eed',   4)),  # TODO can also be line

    # built-up areas
    Feature('leisure',  'stadium sports_centre',                    StyleArea('#efb',   4)),
    Feature('man_made', 'bridge',                                   StyleArea('#ddc', 100)),
    Feature('aeroway',  'apron helipad',                            StyleArea('#bbb',   4)),
    Feature('aeroway',  'taxiway',                                  StyleLine('#aaa', 15, 0.5, 0.00)),
    Feature('aeroway',  'runway',                                   StyleLine('#aaa', 50, 0.5, 0.00)),
    Feature('highway',  'footway pedestrian',                       StyleArea('#ccc',   4, require_area=True)),
]


class A0_landArtist(BaseArtist):
    def __init__(self):
        super().__init__(_land_types)

    def __str__(self):
        return "Land Types"
