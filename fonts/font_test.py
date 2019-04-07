import sys

from PIL import Image, ImageDraw, ImageFont

size = int(sys.argv[2]) if len(sys.argv) >= 3 else 48
fontname = sys.argv[1] if len(sys.argv) >= 2 else 'Symbola.ttf'

font = ImageFont.truetype(fontname, size=size)

text = ''' Unicode pictogram test:
Letters: P H BUS
Sans-serif: 𝗣 𝗛 𝗕𝗨𝗦
Crosses: † ✝
Amenity: 🚻 🖂 ⛲ ⛹ 🎓 🎒
Entertainment: 🎨 🎡 🎢 🎜 🎬 🎭 🎰 🎲
Sport: 🎳 🎾 🏓 🏸 🚩
Restaurants: 🍽 🍴 🍵 🍶 🍷 🍺 🍾
Transport: ⛽ 🚂 🚁 🚃 🚋 🚌 🚖 🛪
'''.splitlines()

image = Image.new('RGB', (1000, 600), '#fff')
draw = ImageDraw.Draw(image, 'RGBA')
for i, line in enumerate(text):
    draw.text((0, i * size), line, fill='#000', font=font)
image.save(fontname + '.png')
