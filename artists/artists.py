
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
        module_artists: list = getattr(module, '_all')
        artists += module_artists
    return artists
