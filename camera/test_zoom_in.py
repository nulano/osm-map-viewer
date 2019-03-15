import camera
import PIL.Image, PIL.ImageDraw

width, height = 100, 100

def close_enough(x, y):
    if abs(x - y) < 10**(-6):
        return True
    if abs(x) > abs(y):
        x, y = y, x
    return x / y >= 1 - 10**(-6)

def norm_longitude(longitude):
    while longitude > 180:
        longitude -= 360
    while longitude < -180:
        longitude += 360
    return longitude

class World:
    def __init__(self, image, min_lat, min_lon, max_lat, max_lon):
        self.image = image
        self.min_lat = min_lat
        self.min_lon = min_lon
        self.max_lat = max_lat
        self.max_lon = max_lon
    
    def get_color(self, gps):
        lattitude, longitude = gps
        im_width, im_height = self.image.size
        y = int((self.max_lat - lattitude) / (self.max_lat - self.min_lat) * im_height)
        x = int(norm_longitude(longitude - self.min_lon) / norm_longitude(self.max_lon - self.min_lon) * im_width)
        if x < 0 or x >= im_width or y < 0 or y >= im_height:
            return 'black'
        return self.image.getpixel((x, y))
    
    def draw(self, camera):
        result = PIL.Image.new('RGB', (width, height))
        draw = PIL.ImageDraw.Draw(result)
        
        for y in range(height):
            for x in range(width):
                gps = camera.px_to_gps((x, y))
                draw.point([(x, y)], self.get_color(gps))
                
                px = camera.gps_to_px(gps)
                if not close_enough(px[0], x) or not close_enough(px[1], y):
                    return 'inconsistent conversions:\n   {}\n-> {}\n-> {}'.format((x, y), gps, px)
        return result


print('testing camera.zoom_in')
test_count = 0
correct_tests = 0
failure = None

with open('testdata/zoom_in.in', 'r') as f:
    world_count = int(f.readline())
    for i in range(world_count):
        tokens = f.readline().split()
        image_file = tokens[0]
        min_lat, min_lon, max_lat, max_lon = map(float, tokens[1:5])
        world = World(PIL.Image.open(image_file), min_lat, min_lon, max_lat, max_lon)
        testcases_count = int(f.readline())
        for j in range(testcases_count):
            tokens = f.readline().split()
            lat, lon = float(tokens[0]), float(tokens[1])
            zoom = min(int(tokens[2]), camera.MAX_ZOOM_LEVEL)
            reference_file = tokens[3]
            cam = camera.Camera(lat, lon, zoom, (width, height))
            pix_x, pix_y = map(float, f.readline().split())
            cam.zoom_in((pix_x, pix_y))
            result = world.draw(cam)
            if isinstance(result, str):
                print('fail for lattitude={}, longitude={}, zoom={}, dimensions={}: {}'.format(lat, lon, zoom, (width, height), result))
            else:
                im2 = PIL.Image.open(reference_file)
                im3 = PIL.Image.new('RGB', (204, 102))
                im3.paste(result, (1,1))
                im3.paste(im2, (103, 1))
                print('Your output on the left, expected on the right. Close the image and press enter (in console) to continue.')
                im3.show()
                input()
