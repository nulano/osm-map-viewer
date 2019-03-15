import geometry


def close_enough(x, y):
    if abs(x - y) < 10**(-6):
        return True
    if abs(x) > abs(y):
        x, y = y, x
    return x / y >= 1 - 10**(-6)

print('testing geometry.distance')
test_count = 0
correct_tests = 0
failure = None
with open('testdata/distance.in', 'r') as f:
    for line in f:
        ax, ay, bx, by, expected = map(float, line.split())
        result = geometry.distance((ax, ay), (bx, by))
        fail = None
        if not isinstance(result, float):
            fail = 'expected float, got {}'.format(type(result))
        elif not close_enough(result, expected):
            fail = 'expected {}, got {}'.format(expected, result)
        else:
            correct_tests += 1
        test_count += 1
        if failure is None and fail is not None:
            failure = 'for a = {}, b = {}: {}'.format((ax, ay), (bx, by), fail)

print('{} out of {} test cases correct.'.format(correct_tests, test_count))
if failure is not None:
    print('First failed test: {}'.format(failure))
