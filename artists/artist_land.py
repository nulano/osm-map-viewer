from artists_util import Base, Feature, StyleArea, StyleLine, FilterTrue, IsArea

_land_types = [
    Feature('natural', 'bare_rock scree shingle rock stone',       StyleArea('#777', 0), FilterTrue),
    Feature('landuse', 'forest',                                   StyleArea('#ada', 0), FilterTrue),
    Feature('natural', 'wood scrub heath moor',                    StyleArea('#ada', 0), FilterTrue),
    Feature('landuse', 'industrial port',                          StyleArea('#ffc', 8), FilterTrue),
    Feature('landuse', 'retail commercial',                        StyleArea('#cff', 8), FilterTrue),
    Feature('amenity', 'school kindergarten college university',   StyleArea('#fcf', 8), FilterTrue),
    Feature('landuse', 'grass meadow village_green',               StyleArea('#dfd', 0), FilterTrue),
    Feature('natural', 'grassland',                                StyleArea('#dfd', 0), FilterTrue),
    Feature('landuse', 'vineyard orchard plant_nursery',           StyleArea('#7d7', 0), FilterTrue),
    Feature('landuse', 'cemetary',                                 StyleArea('#5a5', 0), FilterTrue),
    Feature('amenity', 'grave_yard',                               StyleArea('#5a5', 0), FilterTrue),
    Feature('leisure', 'park',                                     StyleArea('#cfc', 0), FilterTrue),
    Feature('leisure', 'garden',                                   StyleArea('#beb', 0), FilterTrue),
    Feature('natural', 'water bay spring hot_spring blowhole',     StyleArea('#ade', 0), FilterTrue),
    Feature('landuse', 'basin reservoir',                          StyleArea('#ade', 0), FilterTrue),
    Feature('waterway', 'riverbank',                               StyleArea('#ade', 0), FilterTrue),
    Feature('waterway', 'stream canal',                            StyleLine('#ade', 3, 0), FilterTrue),
    Feature('waterway', 'river',                                   StyleLine('#ade', 5, 0), FilterTrue)
]


class ArtistLand(Base):
    def __init__(self):
        super().__init__(_land_types)

    # def _wants_element(self, tags: dict, element: Element, osm_helper: OsmHelper):
    #     return IsArea(tags, element, osm_helper) and super()._wants_element(tags, element, osm_helper)
