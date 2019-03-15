import osm_helper
import xml.etree.ElementTree as ET
import PIL.Image, PIL.ImageDraw

def dicts_equal(dict1, dict2):
    for key in dict1:
        if key not in dict2:
            return False
        if dict1[key] != dict2[key]:
            return False
    if len(dict1) != len(dict2):
        return False
    return True

print('testing osm_helper.multipolygon_to_wsps')
test_count = 0
correct_tests = 0
failure = None

element_tree = ET.parse('testdata/map.osm')
root = element_tree.getroot()
helper = osm_helper.OsmHelper(element_tree)

for element in root:
    if element.tag == 'relation':
        td = osm_helper.tag_dict(element)
        if td['type'] == 'multipolygon' and 'test' in td:
            fail = None
            result = helper.multipolygon_to_wsps(element)
            im1 = PIL.Image.new('RGB', (500, 800))
            draw = PIL.ImageDraw.Draw(im1)
            draw.rectangle((0, 0, 499, 799), fill='white', outline='black')
            
            xs = [p[0] for polygon in result for p in polygon]
            ys = [p[1] for polygon in result for p in polygon]
            scale_x = 300 / (max(xs) - min(xs))
            delta_x = -min(xs)*scale_x + 100
            scale_y = 300 / (max(ys) - min(ys))
            delta_y = -min(ys)*scale_y + 250
            
            for polygon in result:
                draw.polygon([(x*scale_x + delta_x, y*scale_y + delta_y) for x, y in polygon], fill='red', outline='black')
            
            im2 = PIL.Image.open(td['test'])
        
            im3 = PIL.Image.new('RGB', (1000, 800))
            im3.paste(im1, (0,0))
            im3.paste(im2, (500, 0))
            print('Outline of your output on the left, outline of expected on the right. Close the image and press enter (in console) to continue.')
            im3.show()
            input()
