import sys
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
src, out = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB")
# crop to non-white content
diff = ImageChops.difference(im, Image.new("RGB", im.size, (255,255,255))).convert("L")
bbox = diff.point(lambda v: 255 if v > 18 else 0).getbbox()
pad = 12
im = im.crop((bbox[0]-pad, bbox[1]-pad, bbox[2]+pad, bbox[3]+pad))
# white -> transparent (soft edge), keeps original colours
g = ImageChops.difference(im, Image.new("RGB", im.size, (255,255,255))).convert("L")
alpha = g.point(lambda v: 0 if v < 8 else min(255, int((v-8)*255/40)))
logo = im.copy(); logo.putalpha(alpha)
logo.save(f"{out}/logo_transparent.png")
# card version: logo on soft white rounded panel (readable on dark or bright backgrounds)
w, h = im.size; m = 28
card = Image.new("RGBA", (w+2*m, h+2*m), (0,0,0,0))
mask = Image.new("L", card.size, 0)
ImageDraw.Draw(mask).rounded_rectangle((0,0,card.size[0]-1,card.size[1]-1), radius=36, fill=250)
card.paste(Image.new("RGBA", card.size, (255,255,255,255)), (0,0), mask)
card.alpha_composite(logo, (m, m))
card.save(f"{out}/logo_card.png")
print("logo", im.size, "card", card.size)

# lower third, 1920x1080 transparent overlay
W, H = 1920, 1080
lt = Image.new("RGBA", (W, H), (0,0,0,0))
d = ImageDraw.Draw(lt)
F = "/usr/share/fonts/opentype/inter/"
fn = ImageFont.truetype(F+"Inter-Bold.otf", 46)
f2 = ImageFont.truetype(F+"Inter-SemiBold.otf", 32)
f3 = ImageFont.truetype(F+"Inter-Regular.otf", 30)
name = "MOHD FAHMI ASYRAF BIN MOHD NOR AZMI"
l2, l3 = "Nazir Sekolah", "Jemaah Nazir Negeri Terengganu"
x0, y0 = 110, 830
tw = max(d.textlength(name, fn), d.textlength(l2, f2)+40+d.textlength(l3, f3)) + 80
# shadow
sh = Image.new("RGBA", (W, H), (0,0,0,0))
ImageDraw.Draw(sh).rounded_rectangle((x0+6, y0+8, x0+tw+6, y0+150+8), 14, fill=(0,0,0,110))
lt.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
d.rounded_rectangle((x0, y0, x0+tw, y0+150), 14, fill=(13,33,66,232))          # navy panel
d.rectangle((x0, y0, x0+10, y0+150), fill=(245,196,0,255))                    # gold accent (Jata)
d.text((x0+40, y0+22), name, font=fn, fill=(255,255,255,255))
d.line((x0+40, y0+88, x0+tw-40, y0+88), fill=(245,196,0,200), width=2)
d.text((x0+40, y0+100), l2, font=f2, fill=(245,196,0,255))
d.text((x0+40+d.textlength(l2, f2)+20, y0+102), "|  "+l3, font=f3, fill=(225,232,245,255))
lt.save(f"{out}/lower_third.png")
