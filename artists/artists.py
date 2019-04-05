
files = [
    'artist_land',
    'artist_property',
    'artist_road',
    'artist_symbol'
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
