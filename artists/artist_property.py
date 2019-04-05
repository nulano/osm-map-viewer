from artists_util import Base, Feature, StyleComp, StyleArea, StyleLine, FilterTrue

_property_types = [
    Feature('building', None,          StyleComp(StyleArea('#ddc', 0), StyleLine('#ccb', 1, float('inf'))), FilterTrue),
    Feature('leisure', 'pitch track',  StyleComp(StyleArea('#df8', 0), StyleLine('#de8', 1, float('inf'))), FilterTrue),
    Feature('leisure', 'playground',   StyleComp(StyleArea('#cfc', 0), StyleLine('#beb', 1, float('inf'))), FilterTrue),
    Feature('amenity', 'parking',      StyleComp(StyleArea('#eef', 0)                                    ), FilterTrue),
]


class ArtistProperty(Base):
    def __init__(self):
        super().__init__(_property_types)
