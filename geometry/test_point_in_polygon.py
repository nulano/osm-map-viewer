import geometry

print('testing geometry.point_in_polygon')
test_count = 0
correct_tests = 0
failure = None
with open('testdata/point_in.in', 'r') as f:
    count = int(f.readline())
    for i in range(count):
        node_count = int(f.readline())
        polygon = []
        for j in range(node_count):
            x, y = map(float, f.readline().split())
            polygon.append((x, y))
        query_count = int(f.readline())
        for j in range(query_count):
            x, y, exp = map(float, f.readline().split())
            expected = exp == 1
            result = geometry.point_in_polygon((x, y), polygon)
            fail = None
            if not isinstance(result, bool):
                fail = 'expected bool, got {}'.format(type(result))
            elif result != expected:
                fail = 'expected {}, got {}'.format(expected, result)
            else:
                correct_tests += 1
            test_count += 1
            if failure is None and fail is not None:
                failure = 'for polygon:\n{}\n and point {}: {}'.format(polygon, (x, y), fail)
        f.readline()
        

print('{} out of {} test cases correct.'.format(correct_tests, test_count))
if failure is not None:
    print('First failed test: {}'.format(failure))
