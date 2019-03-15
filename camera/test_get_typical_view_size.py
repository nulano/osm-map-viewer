import camera

print('testing camera.get_typical_view_size')

with open('testdata/view_size.out', 'r') as f:
    for i in range(min(16, camera.MAX_ZOOM_LEVEL+1)):
        result = camera.get_typical_view_size(i)
        expected = float(f.readline())
        print('Got {} for zoom level {}.\nA reasonable result would be {}\n'.format(result, i, expected))
