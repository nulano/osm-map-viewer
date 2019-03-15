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

print('testing osm_helper.tag_dict')
test_count = 0
correct_tests = 0
failure = None

element_tree = ET.parse('testdata/map.osm')
root = element_tree.getroot()

with open('testdata/tag_dict.out', 'r', encoding="utf8") as f:
    for element in root:
        fail = None
        result = osm_helper.tag_dict(element)
        
        expected = {}
        expected_count = int(f.readline())
        for i in range(expected_count):
            key = f.readline().rstrip()
            value = f.readline().rstrip()
            expected[key] = value
        
        if not isinstance(result, dict):
            fail = 'expected dictionary, got {}'.format(type(result))
        elif not dicts_equal(result, expected):
            fail = 'expected \n{},\n got \n{}\n'.format(expected, result)
        else:
            correct_tests += 1
        test_count += 1
        if failure is None and fail is not None:
            failure = 'for {} with id={}: {}'.format(element.tag, element.attrib['id'], fail)

print('{} out of {} test cases correct.'.format(correct_tests, test_count))
if failure is not None:
    print('First failed test: {}'.format(failure))
