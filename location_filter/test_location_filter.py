from location_filter import Rectangle, LocationFilter




class Dummy:
    def __init__(self, id):
        self.id = id
    
    def approx_location(self, obj, trash):
        return obj

def are_rects_equal(a, b):
    return a.min_lat == b.min_lat and a.min_lon == b.min_lon and a.max_lat == b.max_lat and a.max_lon == b.max_lon

def are_objects_equal(a, b):
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if not are_rects_equal(x, y):
            return False
    return True

def is_subset_of(a, b):
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if not are_objects_equal(x, y):
            return False
    return True

print('testing location_filter.LocationFilter')
expected_count = 0
found_count = 0
failed_to_find = 0

with open('testdata/input.in', 'r') as f:
    test_cases = int(f.readline())
    for i in range(test_cases):
        typical_query, min_lat, min_lon, max_lat, max_lon = map(float, f.readline().split())
        bounds = Rectangle(min_lat, min_lon, max_lat, max_lon)
        obj_count = int(f.readline())
        pairs = []
        for j in range(obj_count):
            rect_count = int(f.readline())
            obj = []
            for k in range(rect_count):
                min_lat, min_lon, max_lat, max_lon = map(float, f.readline().split())
                obj.append(Rectangle(min_lat, min_lon, max_lat, max_lon))
            pairs.append((obj, Dummy(j)))
        filt = LocationFilter(typical_query, bounds, pairs, None)
        
        query_count = int(f.readline())
        for j in range(query_count):
            min_lat, min_lon, max_lat, max_lon = map(float, f.readline().split())
            
            result = filt.get_pairs(Rectangle(min_lat, min_lon, max_lat, max_lon))
            result = [pair[1].id for pair in result]
            
            expected = list(map(int, f.readline().split()))
            
            expected_count += len(expected)
            found_count += len(result)
            intersection = list(set(result) & set(expected))
            failed_to_find += len(expected) - len(intersection)
                
        f.readline()

print('Should have found {} pairs'.format(expected_count))
print('Found {} pairs [{} times more]'.format(found_count, found_count/expected_count))
print('Failed to find {} pairs [{} of all]'.format(failed_to_find, failed_to_find/expected_count))
