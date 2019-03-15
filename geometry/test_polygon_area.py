import geometry


def close_enough(x, y):
    if abs(x - y) < 10**(-6):
        return True
    if abs(x) > abs(y):
        x, y = y, x
    return x / y >= 1 - 10**(-6)

print('testing geometry.polygon_area')
test_count = 0
correct_tests = 0
failure = None
with open('testdata/area.in', 'r') as f:
    count = int(f.readline())
    for i in range(count):
        node_count = int(f.readline())
        polygon = []
        for j in range(node_count):
            x, y = map(float, f.readline().split())
            polygon.append((x, y))
        expected = float(f.readline())
        f.readline()
        result = geometry.polygon_area(polygon)
        fail = None
        if not isinstance(result, float):
            fail = 'expected float, got {}'.format(type(result))
        elif not close_enough(result, expected):
            fail = 'expected {}, got {}'.format(expected, result)
        else:
            correct_tests += 1
        test_count += 1
        if failure is None and fail is not None:
            failure = 'for polygon:\n{}\n {}'.format(polygon, fail)

print('{} out of {} test cases correct.'.format(correct_tests, test_count))
if failure is not None:
    print('First failed test: {}'.format(failure))
