from artists_util import Base, Feature, StyleComp, StyleArea, StyleLine, FilterTrue

_property_types = [
    Feature('building', None,          StyleComp(StyleArea('#ddc', 4), StyleLine('#ccb', 1, 0.150)), FilterTrue),
    Feature('leisure', 'pitch track',  StyleComp(StyleArea('#df8', 4), StyleLine('#de8', 1, 0.150)), FilterTrue),
    Feature('leisure', 'playground',   StyleComp(StyleArea('#cfc', 4), StyleLine('#beb', 1, 0.150)), FilterTrue),
    Feature('amenity', 'parking',      StyleComp(StyleArea('#eef', 4)                             ), FilterTrue),
]


class ArtistProperty(Base):
    def __init__(self):
        super().__init__(_property_types)
