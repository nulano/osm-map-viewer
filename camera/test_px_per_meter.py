import camera

print('testing camera.px_per_meter')

with open('testdata/px_per_meter.out', 'r') as f:
    for i in range(min(16, camera.MAX_ZOOM_LEVEL+1)):
        cam = camera.Camera(zoom_level=i)
        result = cam.px_per_meter()
        expected = float(f.readline())
        print('Got {} for zoom level {}.\nA reasonable result would be {}\n'.format(result, i, expected))
