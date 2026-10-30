import numpy as np, sys, subprocess
from PIL import Image, ImageDraw, ImageFilter
out = sys.argv[1]; W, H = 1920, 1080; FPS = 30; DUR = 6.0
rng = np.random.default_rng(7)
def fbm(w, h, octaves=6, base=4):
    acc = np.zeros((h, w)); amp = 1; tot = 0
    for o in range(octaves):
        gs = base * 2 ** o
        g = rng.random((gs + 1, int(gs * w / h) + 2))
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += amp * np.asarray(im, float) / 255; tot += amp; amp *= 0.5
    return acc / tot
# sky gradient
y = np.linspace(0, 1, H)[:, None]
top = np.array([22, 92, 178]); bot = np.array([150, 200, 240])
sky = (top * (1 - y) + bot * y)[:, :, None].transpose(0, 2, 1).repeat(W, 1).reshape(H, W, 3) if False else np.repeat((top * (1 - y) + bot * y)[:, None, :], W, 1)
# clouds: two layers, wider than frame for panning
def cloud_layer(w, h, thr, soft, seed_shift):
    n = fbm(w, h, 7, 3)
    m = np.clip((n - thr) / soft, 0, 1) ** 1.4
    shade = 0.80 + 0.20 * fbm(w, h, 5, 6)
    rgb = np.stack([255 * shade, 255 * shade, 255 * np.minimum(1, shade * 1.02)], -1)
    return m, rgb
mb, cb = cloud_layer(W + 400, H, 0.55, 0.20, 0)
mf, cf = cloud_layer(W + 900, H, 0.66, 0.16, 1)
# airliner silhouette (side-ish view), drawn large then downsampled for AA
S4 = 4; PW, PH = 520 * S4, 170 * S4
pl = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); d = ImageDraw.Draw(pl)
def P(pts): return [(x * S4, yy * S4) for x, yy in pts]
body = (245, 247, 250, 255); shade = (200, 208, 218, 255); win = (60, 80, 110, 255)
d.polygon(P([(70, 120), (60, 70), (95, 72), (130, 102)]), fill=shade)                 # tail fin
d.rounded_rectangle((40 * S4, 95 * S4, 480 * S4, 128 * S4), radius=16 * S4, fill=body)  # fuselage
d.ellipse((450 * S4, 95 * S4, 510 * S4, 128 * S4), fill=body)                        # nose
d.polygon(P([(230, 115), (300, 115), (215, 160), (190, 160)]), fill=shade)           # wing
d.polygon(P([(60, 108), (110, 108), (78, 125), (55, 125)]), fill=shade)              # stabiliser
d.rounded_rectangle((235 * S4, 125 * S4, 285 * S4, 140 * S4), radius=7 * S4, fill=(170, 178, 190, 255))  # engine
for i in range(22): d.ellipse(((140 + i * 14) * S4, 103 * S4, (146 + i * 14) * S4, 109 * S4), fill=win)
d.polygon(P([(480, 104), (500, 106), (497, 111), (478, 110)]), fill=win)             # cockpit
d.rectangle((40 * S4, 116 * S4, 470 * S4, 119 * S4), fill=(20, 70, 150, 255))         # livery stripe
pl = pl.resize((PW // S4, PH // S4), Image.LANCZOS).rotate(6, resample=Image.BICUBIC, expand=True)
proc = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p",
    f"{out}/sky_plane.mp4"], stdin=subprocess.PIPE)
nf = int(DUR * FPS)
for k in range(nf):
    p = k / (nf - 1)
    ob = int(400 * p); of = int(900 * p)
    a = mb[:, ob:ob + W, None] * 0.85; img = sky * (1 - a) + cb[:, ob:ob + W] * a
    fr = Image.fromarray(img.astype(np.uint8)).convert("RGBA")
    # plane path: left-low to right-high, slight scale up
    px = int(-450 + p * (W + 300)); py = int(560 - p * 260)
    sc = 0.9 + 0.35 * p
    pls = pl.resize((int(pl.width * sc), int(pl.height * sc)), Image.LANCZOS)
    trail = Image.new("RGBA", (W, H), (255, 255, 255, 0)); td = ImageDraw.Draw(trail)
    tx, ty = px + int(60 * sc), py + int(110 * sc)
    td.line([(tx - 900, ty + 140), (tx, ty)], fill=(255, 255, 255, 120), width=int(7 * sc))
    fr.alpha_composite(trail.filter(ImageFilter.GaussianBlur(4)))
    fr.alpha_composite(pls, (px, py))
    img = np.asarray(fr.convert("RGB"), float)
    a = mf[:, of:of + W, None] * 0.9; img = img * (1 - a) + cf[:, of:of + W] * a
    proc.stdin.write(img.astype(np.uint8).tobytes())
proc.stdin.close(); proc.wait(); print("sky done")
