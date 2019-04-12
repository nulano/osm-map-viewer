
files = [
    'a0_land_artist',
    'a1_feature_artist',
    'a4_road_artist',
    'a6_address_artist',
    'a7_symbol_artist',
]


def get_artists():
    artists = []
    for file in files:
        module = __import__(file, globals=globals())
        module_artists: list = getattr(module, '_all', None)
        if module_artists is None:
            module_artists = map(lambda n: getattr(module, n)(), filter(lambda n: 'Artist' in n, dir(module)))
        artists += module_artists
    return artists
