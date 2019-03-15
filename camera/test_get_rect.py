import camera

print('testing camera.get_rect')

with open('testdata/get_rect.in', 'r') as f:
    test_count = int(f.readline())
    for i in range(test_count):
        tokens = f.readline().split()
        lat, lon = float(tokens[0]), float(tokens[1])
        zoom = min(int(tokens[2]), camera.MAX_ZOOM_LEVEL)
        width, height = int(tokens[3]), int(tokens[4])
        cam = camera.Camera(lat, lon, zoom, (width, height))
        result = cam.get_rect()
        res_str = 'min_lat={}, min_lon={}, max_lat={}, max_lon={}'.format(result.min_lat, result.min_lon, result.max_lat, result.max_lon)
        exp_str = 'min_lat={}, min_lon={}, max_lat={}, max_lon={}'.format(tokens[5], tokens[6], tokens[7], tokens[8])
        print ('For lattitude={}, longitude={}, zoom={}, dimensions={}'.format(lat, lon, zoom, (width, height)))
        print('got {}.\nA reasonable result would be {}\n'.format(res_str, exp_str))
