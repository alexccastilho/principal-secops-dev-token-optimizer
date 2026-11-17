"""Draw the plugin icon (.claude-plugin/icon.png, 1024x1024).

Usage: python tools/make_icon.py .claude-plugin/icon.png   (requires Pillow: pip install pillow)
Author: Alex Camacho Castilho
"""
import sys
from PIL import Image, ImageDraw, ImageChops, ImageFilter

N = 4096
OUT = 1024

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))

def vgrad(size, top, bottom):
    w, h = size
    g = Image.new("RGBA", size)
    d = ImageDraw.Draw(g)
    for y in range(h):
        d.line([(0, y), (w, y)], fill=lerp(top, bottom, y / (h - 1)) + (255,))
    return g

def bezier(p0, p1, p2, p3, steps=200):
    pts = []
    for i in range(steps + 1):
        t = i / steps
        mt = 1 - t
        x = mt**3*p0[0] + 3*mt*mt*t*p1[0] + 3*mt*t*t*p2[0] + t**3*p3[0]
        y = mt**3*p0[1] + 3*mt*mt*t*p1[1] + 3*mt*t*t*p2[1] + t**3*p3[1]
        pts.append((x, y))
    return pts

def shield(cx, top, w, h):
    l, r = cx - w / 2, cx + w / 2
    bottom = top + h
    side = top + h * 0.48
    pts = []
    pts += bezier((cx, top), (cx + w * 0.18, top + h * 0.07), (r - w * 0.08, top + h * 0.06), (r, top + h * 0.09))
    pts += [(r, side)]
    pts += bezier((r, side), (r, top + h * 0.78), (cx + w * 0.22, top + h * 0.92), (cx, bottom))
    pts += bezier((cx, bottom), (cx - w * 0.22, top + h * 0.92), (l, top + h * 0.78), (l, side))
    pts += [(l, top + h * 0.09)]
    pts += bezier((l, top + h * 0.09), (l + w * 0.08, top + h * 0.06), (cx - w * 0.18, top + h * 0.07), (cx, top))
    return pts

def mask_from(draw_fn):
    m = Image.new("L", (N, N), 0)
    draw_fn(ImageDraw.Draw(m))
    return m

img = Image.new("RGBA", (N, N), (0, 0, 0, 0))

# Background: rounded square, deep navy gradient
bg_mask = mask_from(lambda d: d.rounded_rectangle([0, 0, N - 1, N - 1], radius=int(N * 0.22), fill=255))
img.paste(vgrad((N, N), (16, 36, 66), (7, 17, 34)), (0, 0), bg_mask)

# Soft glow behind the shield
glow = mask_from(lambda d: d.ellipse([N*0.14, N*0.12, N*0.86, N*0.88], fill=70)).filter(ImageFilter.GaussianBlur(N*0.08))
img.paste(Image.new("RGBA", (N, N), (25, 195, 166, 255)), (0, 0), ImageChops.multiply(glow, bg_mask))

# Shield: outer teal gradient, inner darker inset
cx = N / 2
outer = shield(cx, N * 0.15, N * 0.62, N * 0.72)
inner = shield(cx, N * 0.205, N * 0.53, N * 0.615)
outer_m = mask_from(lambda d: d.polygon(outer, fill=255))
inner_m = mask_from(lambda d: d.polygon(inner, fill=255))
img.paste(vgrad((N, N), (52, 225, 190), (12, 140, 130)), (0, 0), outer_m)
img.paste(vgrad((N, N), (12, 44, 72), (8, 26, 46)), (0, 0), inner_m)

# Code glyph </> inside the shield, white with rounded ends
d = ImageDraw.Draw(img)
sw = int(N * 0.052)
white = (240, 250, 255, 255)
yc = N * 0.47
hgt = N * 0.13
def stroke(pts):
    d.line(pts, fill=white, width=sw, joint="curve")
    for p in (pts[0], pts[-1]) if len(pts) == 2 else pts:
        d.ellipse([p[0] - sw / 2, p[1] - sw / 2, p[0] + sw / 2, p[1] + sw / 2], fill=white)
stroke([(cx - N * 0.11, yc - hgt), (cx - N * 0.205, yc), (cx - N * 0.11, yc + hgt)])
stroke([(cx + N * 0.11, yc - hgt), (cx + N * 0.205, yc), (cx + N * 0.11, yc + hgt)])
stroke([(cx + N * 0.04, yc - hgt * 1.12), (cx - N * 0.04, yc + hgt * 1.12)])

# Three small "token" bars under the glyph (economy), amber accent
amber = (255, 190, 70, 255)
by = N * 0.665
bw, bh, gap = N * 0.045, N * 0.022, N * 0.02
x0 = cx - (3 * bw + 2 * gap) / 2
for i in range(3):
    x = x0 + i * (bw + gap)
    d.rounded_rectangle([x, by, x + bw, by + bh], radius=int(bh / 2), fill=amber)

img = img.resize((OUT, OUT), Image.LANCZOS)
img.save(sys.argv[1], optimize=True)
print(sys.argv[1], img.size)
