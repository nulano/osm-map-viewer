
files = [
    'artist_land',
    'artist_property',
    'artist_road'
]


def get_artists():
    artists = []
    for file in files:
        module = __import__(file, globals=globals())
        module_artists: dict = getattr(module, '_all')
        artists += module_artists.values()
    return artists
