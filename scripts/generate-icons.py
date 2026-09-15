"""Render the app's simple geometric espresso mark at favicon/PWA sizes."""
from pathlib import Path
from PIL import Image, ImageDraw

out = Path(__file__).resolve().parents[1] / 'coffee_app/public/icons'
out.mkdir(exist_ok=True)
scale = 4
im = Image.new('RGB', (512 * scale, 512 * scale), '#171717')
d = ImageDraw.Draw(im)
def box(coords): return tuple(int(v * scale) for v in coords)
# Solid demitasse, open handle, one rising steam stroke, and a fine saucer.
d.ellipse(box((287, 206, 378, 297)), fill='white')
d.ellipse(box((309, 228, 356, 275)), fill='#171717')
d.rounded_rectangle(box((146, 199, 324, 342)), radius=62*scale, fill='white')
d.rectangle(box((146, 199, 324, 268)), fill='white')
d.rounded_rectangle(box((225, 128, 245, 170)), radius=10*scale, fill='white')
d.rounded_rectangle(box((135, 365, 365, 380)), radius=7*scale, fill='white')
for name, size in [('espresso-192',192), ('espresso-512',512), ('espresso-maskable-512',512), ('espresso-apple',180), ('espresso-32',32)]:
    im.resize((size,size), Image.Resampling.LANCZOS).save(out / f'{name}.png')
im.resize((256,256), Image.Resampling.LANCZOS).save(out / 'espresso.ico', sizes=[(16,16),(32,32),(48,48)])
