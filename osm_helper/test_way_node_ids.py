import osm_helper
import xml.etree.ElementTree as ET

def dicts_equal(dict1, dict2):
    for key in dict1:
        if key not in dict2:
            return False
        if dict1[key] != dict2[key]:
            return False
    if len(dict1) != len(dict2):
        return False
    return True

print('testing osm_helper.way_node_ids')
test_count = 0
correct_tests = 0
failure = None

element_tree = ET.parse('testdata/map.osm')
root = element_tree.getroot()
helper = osm_helper.OsmHelper(element_tree)

with open('testdata/way_node_ids.out', 'r') as f:
    for element in root:
        if element.tag == 'way':
            fail = None
            result = helper.way_node_ids(element)
            expected = f.readline().split()
            
            if not isinstance(result, list):
                fail = 'expected list, got {}'.format(type(result))
            elif result != expected:
                fail = 'expected \n{},\n got \n{}\n'.format(expected, result)
            else:
                correct_tests += 1
            test_count += 1
            if failure is None and fail is not None:
                failure = 'for way with id={}: {}'.format(element.attrib['id'], fail)

print('{} out of {} test cases correct.'.format(correct_tests, test_count))
if failure is not None:
    print('First failed test: {}'.format(failure))
