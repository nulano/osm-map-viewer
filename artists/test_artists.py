from collections import defaultdict
import sys

from artist_test_camera import BoxCamera
from location_filter import Rectangle
import xml.etree.ElementTree as ET
import osm_helper
import PIL.Image
import PIL.ImageDraw


print('testing', sys.argv)


with open('testdata/input.in', 'r') as f:
    test_cases = int(f.readline())
    for i in range(test_cases):
        osm_filename = f.readline().rstrip()
        min_lat, min_lon, max_lat, max_lon = map(float, f.readline().split())
        png_filename = f.readline().rstrip()
        width, height = map(int, f.readline().split())
        
        cam = BoxCamera(Rectangle(min_lat, min_lon, max_lat, max_lon), (width, height))
        zoom = int(f.readline())
        artists = {arg: __import__(arg)() for arg in sys.argv}
        tree = ET.parse(osm_filename)
        helper = osm_helper.OsmHelper(tree)
        
        root = tree.getroot()
        to_draw = defaultdict(list)
        skipped = []  # TODO print these
        for element in root:
            for name, artist in artists.items():
                if artist.wants_element(element, helper):
                    if artist.draws_at_zoom(element, zoom, helper):
                        to_draw[name].append(element)
                    break
            else:
                skipped.append(element)
        
        im1 = PIL.Image.new('RGB', (width, height))
        draw = PIL.ImageDraw.Draw(im1)
        for name, artist in artists.items():
            artist.draw(to_draw[name], helper, cam, draw)
        
        im2 = PIL.Image.open(png_filename)
        
        im3 = PIL.Image.new('RGB', (width*2+4, height+2))
        im3.paste(im1, (1,1))
        im3.paste(im2, (width+3, 1))
        print('Your output on the left, full map on the right. Close the image and press enter (in console) to continue.')
        im3.show()
        f.readline()

    input()
