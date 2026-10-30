import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
A = sys.argv[1]; cover = Image.open(sys.argv[2]).convert("RGB")
W, H = 1920, 1080; F = "/usr/share/fonts/opentype/inter/"
def font(n, s): return ImageFont.truetype(F + n, s)
NAVY, NAVY2, GOLD, WHITE = (13, 33, 66), (24, 58, 110), (245, 196, 0), (255, 255, 255)
def bg(w=W, h=H):
    im = Image.new("RGB", (w, h), NAVY); d = ImageDraw.Draw(im)
    for y in range(h):
        k = y / h; d.line((0, y, w, y), fill=tuple(int(NAVY[i] * (1 - k) + NAVY2[i] * k) for i in range(3)))
    return im
def shadowed(base, img, xy, r=18):
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((xy[0] + 10, xy[1] + 14, xy[0] + img.width + 10, xy[1] + img.height + 14), fill=(0, 0, 0, 150))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(r))); base.alpha_composite(img.convert("RGBA"), xy)
logo = Image.open(f"{A}/logo_card.png")
def put_logo(im, h=150):
    l = logo.resize((int(logo.width * h / logo.height), h), Image.LANCZOS); im.alpha_composite(l, (W - l.width - 40, 36))

def card(title_lines, sub, path, kicker):
    im = bg().convert("RGBA"); d = ImageDraw.Draw(im)
    ch = 700; c = cover.resize((int(cover.width * ch / cover.height), ch), Image.LANCZOS)
    shadowed(im, c, (230, (H - ch) // 2))
    x = 230 + c.width + 120; y = 330
    d.text((x, y), kicker, font=font("Inter-SemiBold.otf", 34), fill=GOLD); y += 70
    d.rectangle((x, y, x + 90, y + 6), fill=GOLD); y += 40
    for t, f in title_lines:
        d.text((x, y), t, font=f, fill=WHITE); y += f.size + 18
    y += 20
    for s in sub:
        d.text((x, y), s, font=font("Inter-Regular.otf", 34), fill=(205, 216, 235)); y += 50
    put_logo(im); im.convert("RGB").save(path)
card([("#MERZ", font("Inter-Bold.otf", 96)), ("Anak Penoreh", font("Inter-Bold.otf", 76)), ("Kini Pilot", font("Inter-Bold.otf", 76))],
     ["Mohd Ezairol Rezan Zainol"], f"{A}/card_title.png", "ULASAN BUKU")
card([("Terima kasih", font("Inter-Bold.otf", 84))],
     ["MOHD FAHMI ASYRAF BIN MOHD NOR AZMI", "Nazir Sekolah", "Jemaah Nazir Negeri Terengganu"], f"{A}/card_end.png", "ULASAN BUKU  ·  #MERZ ANAK PENOREH KINI PILOT")

# split-screen left panel (960 wide, rest transparent)
sp = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sp.paste(bg(960, H), (0, 0))
d = ImageDraw.Draw(sp); ch = 560; c = cover.resize((int(cover.width * ch / cover.height), ch), Image.LANCZOS)
shadowed(sp, c, ((960 - c.width) // 2, 150))
y = 150 + ch + 50
for t, f, col in [("#MERZ: ANAK PENOREH KINI PILOT", font("Inter-Bold.otf", 42), WHITE), ("Mohd Ezairol Rezan Zainol", font("Inter-Regular.otf", 32), GOLD)]:
    tw = d.textlength(t, font=f); d.text(((960 - tw) / 2, y), t, font=f, fill=col); y += f.size + 22
d.rectangle((956, 0, 963, H), fill=GOLD)
sp.save(f"{A}/split_left.png")

# B-roll panel: rounded mask + white frame
PW, PH = 640, 360
m = Image.new("L", (PW, PH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, PW - 1, PH - 1), 22, fill=255); m.save(f"{A}/panel_mask.png")
fr = Image.new("RGBA", (PW + 40, PH + 40), (0, 0, 0, 0)); sh = Image.new("RGBA", fr.size, (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle((14, 18, PW + 26, PH + 30), 26, fill=(0, 0, 0, 140)); fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
ImageDraw.Draw(fr).rounded_rectangle((14, 14, PW + 26, PH + 26), 26, fill=WHITE); fr.save(f"{A}/panel_frame.png")

# preview watermark
wm = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(wm); f = font("Inter-Bold.otf", 64)
t = "PRATONTON"; d.text((40, 40), t, font=f, fill=(255, 255, 255, 70), stroke_width=2, stroke_fill=(0, 0, 0, 60)); wm.save(f"{A}/watermark.png")
print("cards ok")
