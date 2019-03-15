import geometry
import PIL.ImageDraw

print('testing geometry.polygons_to_wsps')

with open('testdata/to_wsps.in', 'r') as f:
    test_count = int(f.readline())
    for i in range(test_count):
        polygons = []
        polygon_count = int(f.readline())
        for j in range(polygon_count):
            node_count = int(f.readline())
            polygon = []
            for k in range(node_count):
                x, y = map(float, f.readline().split())
                polygon.append((x, y))
            polygons.append(polygon)
        filename = f.readline().rstrip()
        f.readline()
        
        wsps = geometry.polygons_to_wsps(polygons)
        im1 = PIL.Image.new('RGB', (500, 800))
        draw = PIL.ImageDraw.Draw(im1)
        draw.rectangle((0, 0, 499, 799), fill='white', outline='black')
        for wsp in wsps:
            draw.polygon([(250 + x*10, 400 - y*10) for x, y in wsp], fill='red', outline='black')
        
        im2 = PIL.Image.open(filename)
        
        im3 = PIL.Image.new('RGB', (1000, 800))
        im3.paste(im1, (0,0))
        im3.paste(im2, (500, 0))
        print('Your output on the left, expected on the right. Close the image and press enter (in console) to continue.')
        im3.show()
        input()
        
