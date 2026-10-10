import sys
from PIL import Image, ImageDraw
out = sys.argv[1]; files = sys.argv[2:]
ims = [Image.open(f).convert('RGB') for f in files]
cols = 2 if len(ims) > 1 else 1
rows = (len(ims) + cols - 1) // cols
w = max(i.width for i in ims); h = max(i.height for i in ims)
S = Image.new('RGB', (w * cols, h * rows), (255, 255, 255))
d = ImageDraw.Draw(S)
for k, im in enumerate(ims):
    x, y = (k % cols) * w, (k // cols) * h
    S.paste(im, (x, y)); d.text((x + 6, y + 4), files[k].split('/')[-1], fill=(0, 0, 0))
S.save(out, quality=88)
print(out, S.size)
