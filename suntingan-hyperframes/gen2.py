"""Generate the social-style (TikTok-like) HyperFrames cut of the #MERZ book review.

The speaker sits in a rounded video frame that moves between layouts while the backdrop
behind it changes every few seconds; word-by-word captions run along the bottom.
All times come from the word-level transcript (raw footage seconds); OFF shifts them
onto the film clock (the 3 s title card plays first).
Usage: gen2.py <project_dir> [--preview]
"""
import json, os, sys, html
from PIL import Image, ImageFilter, ImageEnhance

P = sys.argv[1]
PREVIEW = "--preview" in sys.argv
OFF, RAW, POST = 3.0, 280.04, 4.0
TOTAL = round(OFF + RAW + POST, 2)
NAVY, GOLD, INK = "#0D2142", "#F5C400", "#FFFFFF"
NAME = "MOHD FAHMI ASYRAF BIN MOHD NOR AZMI"
ROLE = "Nazir Sekolah · Jemaah Nazir Negeri Terengganu"
BOOK = "#MERZ: Anak Penoreh Kini Pilot"
AUTHOR = "Mohd Ezairol Rezan Zainol"

def A(t): return round(t + OFF, 3)
def write(path, text):
    os.makedirs(os.path.dirname(f"{P}/{path}"), exist_ok=True)
    open(f"{P}/{path}", "w").write(text)

# start from a clean scene folder (intro/outro are shared with gen.py)
for f in os.listdir(f"{P}/compositions"):
    if f not in ("intro.html", "outro.html"): os.remove(f"{P}/compositions/{f}")

# ---------------- backdrop photos: cover-cropped 1920x1080, toned down so the frame pops ----------------
def bg_photo(src, dst, blur=0, dim=0.78):
    if os.path.exists(f"{P}/{dst}"): return
    im = Image.open(f"{P}/{src}").convert("RGB")
    s = max(1920 / im.width, 1080 / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    l, t = (im.width - 1920) // 2, (im.height - 1080) // 2
    im = im.crop((l, t, l + 1920, t + 1080))
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    ImageEnhance.Brightness(im).enhance(dim).save(f"{P}/{dst}", quality=90)
os.makedirs(f"{P}/assets/bg", exist_ok=True)
for k in ("getah", "pesawat", "kampung", "murid"):
    bg_photo(f"assets/img/broll-{k}.jpg", f"assets/bg/{k}.jpg", blur=2)
bg_photo("assets/img/kulit-buku.jpg", "assets/bg/kulit.jpg", blur=34, dim=0.6)

# ---------------- transcript -> caption words (spelling fixed by position) ----------------
W = json.load(open(f"{P}/transcript.json")); W = W["words"] if isinstance(W, dict) else W
FIX = {26: "Penoreh", 29: "hasil", 30: "nukilan", 31: "Mohd", 32: "Ezairol", 33: "Zainol.", 42: "penoreh",
       56: "menerbangkan", 67: "filem.", 93: "sederhana", 110: "penghalang", 115: "kejayaan.", 132: "juga",
       133: "pekerja", 167: "kerjaya", 174: "pelbagai", 176: "komersial", 177: "ke serata", 208: "serba kekurangan",
       219: "kekurangan.", 234: "Mohd", 235: "Ezairol", 286: "peringkat", 291: "pengorbanannya", 299: "terlibat",
       334: "juga", 355: "doktor,", 419: "menentukan", 423: "tuju", 457: "Sekian"}
MERGE = {170: "juruterbang", 283: "juruterbang.", 356: "juruterbang,", 435: "juruterbang"}  # "jurur" + "terbang"
words, i = [], 0
while i < len(W):
    w = W[i]
    if i in MERGE:
        words.append(dict(text=MERGE[i], start=w["start"], end=W[i + 1]["end"])); i += 2; continue
    words.append(dict(text=FIX.get(i, w["text"]), start=w["start"], end=w["end"])); i += 1
KEYWORDS = {"pilot", "penoreh", "getah", "juruterbang", "pesawat", "kampung", "kejayaan", "26,000", "polis",
            "proses", "bermimpi", "keberanian", "kesanggupan", "keazaman", "inspirasi", "murid", "pemimpin",
            "doktor", "kisah", "benar", "#merz"}
def is_key(t): return t.lower().strip(".,?!") in KEYWORDS

groups, cur = [], []
for j, w in enumerate(words):
    cur.append(w)
    nxt = words[j + 1] if j + 1 < len(words) else None
    chars = sum(len(x["text"]) + 1 for x in cur)
    brk = (nxt is None or len(cur) >= 4 or w["text"][-1] in ".,?!" or (nxt["start"] - w["end"]) >= 0.15
           or chars + len(nxt["text"]) > 26)
    if brk: groups.append(cur); cur = []

# ---------------- window layouts (speaker frame) and inner framings ----------------
# window: scale, centre x, centre y, rotation (deg) — transform origin is the frame's centre
LAY = {"C": (0.70, 960, 440, 0), "CL": (0.68, 960, 446, -1.6), "CR": (0.68, 960, 446, 1.4),
       "R": (0.59, 1314, 515, 0), "F": (1.0, 960, 540, 0)}
WIDE, MED, CLOSE = (1.0, 960, 540), (1.3, 1030, 516), (1.6, 1030, 436)
def BOOKF(x): return (1.45, x, 601)

CARDS = [  # raw start, duration — the frame moves right while a card sits on the left
    (15.4, 7.85), (26.6, 6.0), (33.4, 7.0), (51.4, 5.6), (76.6, 16.8), (103.6, 8.2), (116.2, 15.7),
    (133.2, 20.9), (155.2, 21.4), (186.0, 12.6), (199.6, 10.8), (237.6, 13.5), (260.6, 10.6)]
BOOKS = [(23.3, 26.3, 1000), (41.8, 45.2, 1000), (61.6, 65.0, 970), (216.3, 219.3, 860),
         (226.4, 229.4, 830), (273.8, 278.2, 1030)]
spans = sorted([(s, s + d, "R", MED) for s, d in CARDS] + [(a, b, "F", BOOKF(x)) for a, b, x in BOOKS])
keys, t, k = [], 0.0, 0
center_cycle = [("C", WIDE), ("CL", MED), ("C", CLOSE), ("CR", MED), ("C", MED), ("CL", CLOSE)]
def fill(a, b):
    global k
    n = max(1, round((b - a) / 6.5))
    for m in range(n):
        if b - a < 2.5 and keys: return
        keys.append((a + m * (b - a) / n, *center_cycle[k % len(center_cycle)])); k += 1
for a, b, lay, fr in spans:
    if a - t > 0.5: fill(t, a)
    keys.append((a - 0.35 if lay == "R" else a, lay, fr)); t = b
if RAW - t > 0.5: fill(t, RAW)

D = 0.6  # every move is one eased tween
cam_js = []
def win_vals(lay):
    s, cx, cy, r = LAY[lay]; return s, cx - 960, cy - 540, r
def cam_vals(fr):
    z, cx, cy = fr
    x, y = z * (960 - cx), z * (540 - cy)
    mx, my = 960 * (z - 1), 540 * (z - 1)
    return z, round(max(-mx, min(mx, x)), 1), round(max(-my, min(my, y)), 1)
s0, x0, y0, r0 = win_vals(keys[0][1]); z0, cx0, cy0 = cam_vals(keys[0][2])
cam_js.append(f'      tl.set("#win", {{ scale: {s0}, x: {x0}, y: {y0}, rotation: {r0}, borderRadius: 44, transformOrigin: "50% 50%" }}, 0);')
cam_js.append(f'      tl.set("#cam", {{ scale: {z0}, x: {cx0}, y: {cy0}, transformOrigin: "50% 50%" }}, 0);')
prev = keys[0]
for tk, lay, fr in keys[1:]:
    s, x, y, r = win_vals(lay); z, cx, cy = cam_vals(fr)
    tt = max(0, A(tk))
    cam_js.append(f'      tl.to("#win", {{ scale: {s}, x: {x}, y: {y}, rotation: {r}, borderRadius: {0 if lay == "F" else 44}, duration: {D}, ease: "power3.inOut" }}, {tt});')
    cam_js.append(f'      tl.to("#cam", {{ scale: {z}, x: {cx}, y: {cy}, duration: {D}, ease: "power3.inOut" }}, {tt});')

# ---------------- backdrop segments (raw start, kind, palette/photo, big word) ----------------
PAL = {"A": ("#0B1D3A", "#1E4FD8", "#3EC5FF", "#F5C400"), "B": ("#062A30", "#0FB5A8", "#3EC5FF", "#A7F3D0"),
       "C": ("#3A1600", "#FF8A00", "#F5C400", "#FF4D6D"), "D": ("#1B0B3A", "#7C3AED", "#EC4899", "#3EC5FF"),
       "E": ("#052E1C", "#22C55E", "#A3E635", "#0EA5E9"), "F": ("#3A0B16", "#FF4D6D", "#FF8A00", "#F5C400")}
SEG = [(0, "mesh", "A", ""), (4.0, "mesh", "B", "ULASAN BUKU"), (11.6, "mesh", "C", "#MERZ"), (15.4, "photo", "kulit", ""),
       (23.3, "mesh", "D", "#MERZ"), (26.6, "photo", "getah", ""), (33.4, "photo", "pesawat", ""),
       (40.4, "mesh", "A", "KISAH BENAR"), (46.0, "mesh", "B", ""), (51.4, "photo", "kampung", ""),
       (57.0, "mesh", "C", "CABARAN"), (63.0, "mesh", "D", ""), (69.0, "mesh", "E", "BERUSAHA"),
       (76.6, "mesh", "A", ""), (85.0, "mesh", "C", "26,000"), (93.4, "mesh", "B", ""), (98.0, "mesh", "D", "PILOT"),
       (103.6, "video", "sky", ""), (111.8, "mesh", "A", ""), (116.2, "mesh", "B", "01"), (124.0, "mesh", "C", ""),
       (131.9, "mesh", "D", "02"), (140.0, "mesh", "A", ""), (147.0, "mesh", "E", "DISIPLIN"), (155.2, "mesh", "F", "03"),
       (163.0, "mesh", "B", "PROSES"), (169.4, "photo", "pesawat", ""), (176.6, "mesh", "C", "PENDIDIKAN"),
       (186.0, "photo", "murid", ""), (198.6, "mesh", "D", "MASA DEPAN"), (204.0, "mesh", "A", ""),
       (210.4, "mesh", "B", "KISAH BENAR"), (216.3, "mesh", "C", ""), (222.0, "mesh", "E", ""), (226.4, "mesh", "F", ""),
       (232.0, "mesh", "D", "MESEJ"), (237.6, "mesh", "A", "HALA TUJU"), (244.0, "mesh", "B", ""), (251.1, "mesh", "C", ""),
       (256.0, "photo", "pesawat", ""), (260.6, "mesh", "E", "MIMPI"), (265.0, "mesh", "F", "AZAM"),
       (271.2, "photo", "kulit", "")]
WIPES = ['inset(0 100% 0 0)', 'inset(0 0 0 100%)', 'circle(0% at 50% 50%)', 'inset(100% 0 0 0)', 'inset(0 0 100% 0)']
WIPE_TO = {'inset(0 100% 0 0)': 'inset(0 0% 0 0)', 'inset(0 0 0 100%)': 'inset(0 0 0 0%)',
           'circle(0% at 50% 50%)': 'circle(75% at 50% 50%)', 'inset(100% 0 0 0)': 'inset(0% 0 0 0)', 'inset(0 0 100% 0)': 'inset(0 0 0% 0)'}
# soft colour blobs as pre-rendered PNGs: images are cheap to capture, CSS gradients/blur are not
def blob_png(hexc):
    path = f"assets/bg/blob-{hexc.strip('#')}.png"
    if not os.path.exists(f"{P}/{path}"):
        import math
        N = 512; r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
        im = Image.new("RGBA", (N, N))
        px = im.load()
        for yy in range(N):
            for xx in range(N):
                d = math.hypot(xx - N / 2, yy - N / 2) / (N / 2)
                px[xx, yy] = (r, g, b, int(255 * max(0.0, 1 - d) ** 1.8))
        im.save(f"{P}/{path}")
    return path

BD_CSS = """
#root { position: absolute; inset: 0; overflow: hidden; }
.seg { position: absolute; inset: 0; opacity: 0; overflow: hidden; }
.mesh { position: absolute; inset: 0; }
.blob { position: absolute; width: 1300px; height: 1300px; opacity: .9; }
.blob.small { width: 900px; height: 900px; opacity: .7; }
.photo { position: absolute; inset: 0; width: 1920px; height: 1080px; object-fit: cover; }
.bigword { position: absolute; left: -200px; right: -200px; top: 340px; text-align: center; white-space: nowrap;
  font-family: Inter, sans-serif; font-weight: 900; font-size: 300px; line-height: 1; letter-spacing: -.02em;
  color: transparent; -webkit-text-stroke: 4px rgba(255,255,255,.28); }
"""
CHAP = 6  # segments per backdrop scene keeps each capture's heavy-overlay count small
bd_hosts = []
for c0 in range(0, len(SEG), CHAP):
    ci = c0 // CHAP
    chunk = list(range(c0, min(c0 + CHAP, len(SEG))))
    cst = 0.0 if c0 == 0 else SEG[c0][0] - 0.3                      # chapter opens with its first wipe
    cen = SEG[chunk[-1] + 1][0] + 0.35 if chunk[-1] + 1 < len(SEG) else RAW
    cid = f"backdrop{ci}"
    bd_html, bd_js = [], []
    for n in chunk:
        st, kind, key, word = SEG[n]
        en = SEG[n + 1][0] if n + 1 < len(SEG) else RAW
        dur = en - st + 0.6
        lst = round(st - cst, 3)                                      # local scene time
        sid = f"bd{n}"
        if kind == "mesh":
            base, c1, c2, c3 = PAL[key]
            inner = (f'<div class="mesh" style="background:{base}">'
                     f'<img id="{sid}-b1" class="blob" src="{blob_png(c1)}" alt="" style="left:-200px;top:-260px">'
                     f'<img id="{sid}-b2" class="blob" src="{blob_png(c2)}" alt="" style="left:900px;top:240px">'
                     f'<img id="{sid}-b3" class="blob small" src="{blob_png(c3)}" alt="" style="left:300px;top:520px"></div>')
            sgn = 1 if n % 2 else -1
            for bi, (dx, dy) in enumerate([(sgn * 260, 160), (-sgn * 300, -180), (sgn * 420, -120)], 1):
                bd_js.append(f'    tl.fromTo("#{sid}-b{bi}", {{ x: 0, y: 0 }}, {{ x: {dx}, y: {dy}, duration: {dur:.2f}, ease: "sine.inOut" }}, {max(0, lst):.2f});')
        elif kind == "photo":
            inner = f'<img id="{sid}-img" class="photo" src="assets/bg/{key}.jpg" alt="">'
            bd_js.append(f'    tl.fromTo("#{sid}-img", {{ scale: 1.04 }}, {{ scale: 1.12, duration: {dur:.2f}, ease: "none" }}, {max(0, lst):.2f});')
        else:
            inner = (f'<video id="{sid}-vid" class="clip photo" src="assets/broll/sky-plane.mp4" data-start="{max(0, lst - 0.3):.2f}" '
                     f'data-duration="{min(dur + 0.3, 9.0):.2f}" muted playsinline></video>')
        if word:
            inner += f'<div id="{sid}-w" class="bigword">{html.escape(word)}</div>'
            bd_js.append(f'    tl.fromTo("#{sid}-w", {{ x: {120 if n % 2 else -120} }}, {{ x: {-120 if n % 2 else 120}, duration: {dur:.2f}, ease: "none" }}, {max(0, lst):.2f});')
        bd_html.append(f'    <div id="{sid}" class="seg" style="z-index:{n + 1}">{inner}</div>')
        t_in = max(0, lst - 0.3)
        bd_js.append(f'    tl.set("#{sid}", {{ opacity: 1 }}, {t_in:.2f});')
        if n > 0:
            w0 = WIPES[n % len(WIPES)]
            bd_js.append(f'    tl.fromTo("#{sid}", {{ clipPath: "{w0}" }}, {{ clipPath: "{WIPE_TO[w0]}", duration: 0.55, ease: "power3.inOut" }}, {t_in:.2f});')
        if n > c0:
            bd_js.append(f'    tl.set("#bd{n - 1}", {{ opacity: 0 }}, {lst + 0.35:.2f});')
    write(f"compositions/{cid}.html", f"""<template>
  <style>{BD_CSS}</style>
  <div id="root" data-composition-id="{cid}" data-width="1920" data-height="1080" data-layout-ignore>
{chr(10).join(bd_html)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{chr(10).join(bd_js)}
    window.__timelines["{cid}"] = tl;
  </script>
</template>
""")
    bd_hosts.append(f'      <div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html" data-start="{A(cst)}" '
                    f'data-duration="{round(cen - cst, 3)}" data-track-index="{20 + ci}" data-track-kind="graphics" '
                    f'data-width="1920" data-height="1080" style="z-index:{1 + ci}"></div>')

# ---------------- captions: one scene, one group visible at a time ----------------
cap_html, cap_js = [], []
for g, grp in enumerate(groups):
    st = max(0.1, grp[0]["start"] - 0.05)
    nxt = groups[g + 1][0]["start"] - 0.05 if g + 1 < len(groups) else RAW
    en = min(nxt, grp[-1]["end"] + 0.35)
    spans_ = "".join(f'<span id="c{g}w{j}" class="cw{" key" if is_key(w["text"]) else ""}">{html.escape(w["text"])}</span>'
                     for j, w in enumerate(grp))
    cap_html.append(f'    <div id="c{g}" class="cg"><div class="pill">{spans_}</div></div>')
    cap_js.append(f'    tl.set("#c{g}", {{ visibility: "visible", opacity: 1 }}, {st:.3f});')
    cap_js.append(f'    tl.fromTo("#c{g} .pill", {{ scale: 0.92, y: 10 }}, {{ scale: 1, y: 0, duration: 0.18, ease: "back.out(1.6)" }}, {st:.3f});')
    for j, w in enumerate(grp):
        ws = max(st, w["start"] - 0.03)
        on = "#F5C400"
        cap_js.append(f'    tl.fromTo("#c{g}w{j}", {{ color: "rgba(255,255,255,.5)", scale: 1 }}, {{ color: "{on}", scale: 1.08, duration: 0.08, ease: "power2.out" }}, {ws:.3f});')
        settle = "#F5C400" if is_key(w["text"]) else "#FFFFFF"
        cap_js.append(f'    tl.to("#c{g}w{j}", {{ color: "{settle}", scale: 1, duration: 0.12, ease: "power2.out" }}, {max(ws + 0.09, w["end"]):.3f});')
    cap_js.append(f'    tl.to("#c{g}", {{ opacity: 0, duration: 0.1, ease: "power2.in" }}, {en - 0.1:.3f});')
    cap_js.append(f'    tl.set("#c{g}", {{ visibility: "hidden" }}, {en:.3f});')
CAP_CSS = """
#root { position: absolute; inset: 0; }
.cg { position: absolute; left: 0; right: 0; bottom: 64px; text-align: center; visibility: hidden; overflow: visible; }
.pill { display: inline-block; padding: 12px 30px 14px; border-radius: 22px; background: rgba(8,12,28,.82);
  box-shadow: 0 10px 30px rgba(0,0,0,.35); }
.cw { display: inline-block; margin: 0 .3em; font-family: Inter, sans-serif; font-weight: 900; font-size: 60px;
  line-height: 1.1; color: rgba(255,255,255,.5); }
"""
write("compositions/captions.html", f"""<template>
  <style>{CAP_CSS}</style>
  <div id="root" data-composition-id="captions" data-width="1920" data-height="1080">
{chr(10).join(cap_html)}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{chr(10).join(cap_js)}
    window.__timelines["captions"] = tl;
  </script>
</template>
""")

# ---------------- cards on the left (white, playful tilt) ----------------
SCENES = [
  dict(id="lt", kind="lt", start=4.0, dur=7.4),
  dict(id="booksplit", kind="book", start=15.4, dur=7.85),
  dict(id="br-getah", kind="label", start=26.6, dur=6.0, kicker="Latar belakang", label="Anak penoreh getah"),
  dict(id="br-pesawat", kind="label", start=33.4, dur=7.0, kicker="Kini", label="Juruterbang ke seluruh dunia"),
  dict(id="br-kampung", kind="label", start=51.4, dur=5.6, kicker="Membesar sebagai", label="Anak kampung"),
  dict(id="jobs", kind="card", start=76.6, dur=16.8, kicker="Tidak memilih pekerjaan", title="Bermula dari bawah",
       items=[(77.3, "Pengawal keselamatan"), (80.4, "Pekerja kilang"), (81.2, "Batu Pahat, Johor")],
       stat=dict(t=86.6, value=26000, label="permohonan menyertai pasukan polis", chip=(92.0, "Antara yang terpilih"))),
  dict(id="br-pesawat2", kind="label", start=103.6, dur=8.2, kicker="Dari polis kepada", label="Juruterbang pesawat komersial"),
  dict(id="lesson1", kind="card", start=116.2, dur=15.7, kicker="Pengajaran 1",
       title="Kejayaan tidak ditentukan oleh latar belakang keluarga",
       items=[(122.0, "Kekurangan hari ini bukan masa depan kita")]),
  dict(id="lesson2", kind="card", start=133.2, dur=20.9, kicker="Pengajaran 2", title="Jangan malu untuk bermula dari bawah",
       items=[(142.1, "Pengawal keselamatan"), (143.9, "Pekerja kilang")],
       sub=[(150.5, "Disiplin"), (151.5, "Kematangan"), (152.9, "Ketahanan diri")]),
  dict(id="lesson3", kind="card", start=155.2, dur=21.4, kicker="Pengajaran 3",
       title="Kejayaan ialah satu proses, bukan datang tiba-tiba",
       steps=[(164.3, "Anak kampung"), (165.7, "Pekerja biasa"), (167.2, "Pegawai polis"), (169.6, "Juruterbang")]),
  dict(id="br-murid", kind="label", start=186.0, dur=12.6, kicker="Di sekolah kita", label="Murid daripada pelbagai latar belakang"),
  dict(id="future", kind="card", start=199.6, dur=10.8, kicker="Murid biasa hari ini", title="Mungkin pemimpin masa akan datang",
       items=[(205.4, "Doktor"), (205.9, "Juruterbang"), (208.4, "Pemimpin")]),
  dict(id="quote", kind="quote", start=237.6, dur=13.5),
  dict(id="values", kind="card", start=260.6, dur=10.6, kicker="Buku ini kisah tentang", title="",
       items=[(261.2, "Keberanian untuk bermimpi"), (264.2, "Kesanggupan bermula dari bawah"), (267.3, "Keazaman mengubah kehidupan")]),
]
CARD_CSS = f"""
#root {{ position: absolute; inset: 0; font-family: Inter, sans-serif; color: {NAVY}; }}
.card {{ position: absolute; left: 64px; top: 236px; width: 620px; padding: 36px 40px 40px; background: #fff;
  border-radius: 28px; box-shadow: 0 30px 70px rgba(0,0,0,.35); }}
.kicker {{ display: inline-block; font-weight: 900; font-size: 28px; letter-spacing: .04em; text-transform: uppercase;
  color: {NAVY}; background: {GOLD}; border-radius: 999px; padding: 8px 22px; }}
.title {{ margin-top: 18px; font-weight: 900; font-size: 50px; line-height: 1.08; letter-spacing: -.015em; }}
.w {{ display: inline-block; margin-right: .24em; }}
.items {{ margin-top: 22px; display: flex; flex-direction: column; gap: 12px; }}
.item {{ display: flex; align-items: center; gap: 16px; font-weight: 800; font-size: 32px; background: #EEF2F8;
  border-radius: 16px; padding: 14px 20px; }}
.dot {{ width: 16px; height: 16px; border-radius: 50%; background: {GOLD}; flex: none; }}
.subrow {{ margin-top: 16px; display: flex; gap: 10px; flex-wrap: wrap; }}
.chip {{ font-weight: 800; font-size: 28px; color: #fff; background: {NAVY}; border-radius: 999px; padding: 8px 20px; }}
.stat {{ margin-top: 22px; }}
.stat .num {{ font-weight: 900; font-size: 100px; line-height: 1; color: {NAVY}; font-variant-numeric: tabular-nums;
  background: linear-gradient(transparent 62%, {GOLD} 62%); display: inline-block; padding: 0 6px; }}
.stat .lbl {{ margin-top: 8px; font-weight: 700; font-size: 28px; color: #3B4A66; }}
.steps {{ margin-top: 24px; display: flex; flex-direction: column; }}
.step {{ display: flex; align-items: center; gap: 18px; font-weight: 800; font-size: 32px; height: 62px; }}
.step .n {{ width: 50px; height: 50px; border-radius: 50%; border: 4px solid {GOLD}; display: flex; align-items: center;
  justify-content: center; font-size: 28px; font-weight: 900; flex: none; }}
.step.last .n {{ background: {GOLD}; }}
"""
def words_html(text, extra=""):
    return "".join(f'<span class="w{extra}">{html.escape(w)}</span>' for w in text.split())
def scene(sid, body, js, css=""):
    return f"""<template>
  <style>{CARD_CSS}{css}</style>
  <div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">
{body}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{js}
    window.__timelines["{sid}"] = tl;
  </script>
</template>
"""
def pop_in(sel, dur, rot=-1.5):
    # arrives with a springy pop and a slight tilt; leaves faster
    return (f'    tl.fromTo("{sel}", {{ opacity: 0, scale: 0.85, rotation: {rot - 4}, y: 30 }}, {{ opacity: 1, scale: 1, rotation: {rot}, y: 0, duration: 0.5, ease: "back.out(1.5)" }}, 0);\n'
            f'    tl.to("{sel}", {{ opacity: 0, scale: 0.9, y: 20, duration: 0.28, ease: "power3.in" }}, {dur - 0.34:.2f});\n')
def title_in(sel, t0=0.2):
    return f'    tl.fromTo("{sel} .w", {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.22, ease: "back.out(2)", stagger: 0.06 }}, {t0});\n'
def item_in(sel, t):
    return f'    tl.fromTo("{sel}", {{ opacity: 0, x: -24, scale: 0.9 }}, {{ opacity: 1, x: 0, scale: 1, duration: 0.32, ease: "back.out(1.8)" }}, {t:.2f});\n'

def build(s):
    sid, st, dur, k_ = s["id"], s["start"], s["dur"], s["kind"]
    if k_ == "lt":
        css = f"""
#lt-box {{ position: absolute; left: 330px; bottom: 300px; display: flex; flex-direction: column; align-items: flex-start; gap: 8px; }}
#lt-name {{ background: #fff; color: {NAVY}; font-weight: 900; font-size: 44px; padding: 12px 26px; border-radius: 16px; white-space: nowrap; }}
#lt-role {{ background: {GOLD}; color: {NAVY}; font-weight: 800; font-size: 28px; padding: 8px 20px; border-radius: 999px; margin-left: 18px; white-space: nowrap; }}
"""
        body = f'    <div id="lt-box"><div id="lt-name">{html.escape(NAME)}</div><div id="lt-role">{html.escape(ROLE)}</div></div>'
        js = (f'    tl.fromTo("#lt-box", {{ rotation: -2, transformOrigin: "0 100%" }}, {{ rotation: -2, duration: 0.01 }}, 0);\n'
              f'    tl.fromTo("#lt-name", {{ opacity: 0, x: -60, scale: 0.8 }}, {{ opacity: 1, x: 0, scale: 1, duration: 0.5, ease: "back.out(1.6)" }}, 0.1);\n'
              f'    tl.fromTo("#lt-role", {{ opacity: 0, x: -40 }}, {{ opacity: 1, x: 0, duration: 0.4, ease: "back.out(1.6)" }}, 0.35);\n'
              f'    tl.to("#lt-box", {{ opacity: 0, x: -40, duration: 0.3, ease: "power3.in" }}, {dur - 0.36:.2f});\n')
        return scene(sid, body, js, css)
    if k_ == "book":
        css = f"""#{sid}-card {{ text-align: center; }}
#{sid}-cover {{ height: 400px; border-radius: 8px; box-shadow: 0 18px 40px rgba(0,0,0,.35); display: block; margin: 18px auto 0; }}
#{sid}-t {{ margin-top: 22px; font-weight: 900; font-size: 40px; line-height: 1.1; }}
#{sid}-a {{ margin-top: 8px; font-weight: 700; font-size: 28px; color: #3B4A66; }}"""
        body = (f'    <div id="{sid}-card" class="card"><div class="kicker">Buku pilihan</div>'
                f'<img id="{sid}-cover" src="assets/img/kulit-buku.jpg" alt="Kulit buku">'
                f'<div id="{sid}-t">{words_html(BOOK)}</div><div id="{sid}-a">{html.escape(AUTHOR)}</div></div>')
        js = pop_in(f"#{sid}-card", dur) + title_in(f"#{sid}-t", 0.6)
        js += f'    tl.fromTo("#{sid}-cover", {{ y: 30, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.5, ease: "back.out(1.6)" }}, 0.25);\n'
        return scene(sid, body, js, css)
    if k_ == "label":
        css = f"""#{sid}-card {{ top: 300px; }}
#{sid}-l {{ margin-top: 16px; font-weight: 900; font-size: 54px; line-height: 1.08; }}"""
        body = (f'    <div id="{sid}-card" class="card"><div class="kicker">{html.escape(s["kicker"])}</div>'
                f'<div id="{sid}-l">{words_html(s["label"])}</div></div>')
        return scene(sid, body, pop_in(f"#{sid}-card", dur, -2) + title_in(f"#{sid}-l", 0.25), css)
    if k_ == "quote":
        l1 = "Kita mungkin tidak mampu memilih di mana kita dilahirkan,"
        l2 = "tetapi kita masih boleh berusaha untuk menentukan ke mana hala tuju kehidupan kita."
        l2h = words_html(l2).replace('<span class="w">hala</span><span class="w">tuju</span>',
                                     '<span class="w hl">hala</span><span class="w hl">tuju</span>')
        css = f"""#{sid}-card {{ top: 210px; }}
#{sid}-l1, #{sid}-l2 {{ margin-top: 16px; font-weight: 800; font-size: 38px; line-height: 1.25; }}
#{sid}-l2 .hl {{ background: {GOLD}; border-radius: 6px; padding: 0 6px; }}"""
        body = (f'    <div id="{sid}-card" class="card"><div class="kicker">Mesej penutup</div>'
                f'<div id="{sid}-l1">{words_html(l1)}</div><div id="{sid}-l2">{l2h}</div></div>')
        js = pop_in(f"#{sid}-card", dur, -1)
        js += f'    tl.fromTo("#{sid}-l1 .w", {{ opacity: 0.15 }}, {{ opacity: 1, duration: 0.2, ease: "power2.out", stagger: 0.42 }}, {237.9 - st:.2f});\n'
        js += f'    tl.fromTo("#{sid}-l2 .w", {{ opacity: 0.15 }}, {{ opacity: 1, duration: 0.2, ease: "power2.out", stagger: 0.47 }}, {243.0 - st:.2f});\n'
        return scene(sid, body, js, css)
    body = [f'    <div id="{sid}-card" class="card">', f'      <div class="kicker">{html.escape(s["kicker"])}</div>']
    js = pop_in(f"#{sid}-card", dur)
    if s.get("title"):
        body.append(f'      <div id="{sid}-title" class="title">{words_html(s["title"])}</div>'); js += title_in(f"#{sid}-title")
    if s.get("items"):
        body.append('      <div class="items">')
        for i_, (t_, txt) in enumerate(s["items"]):
            body.append(f'        <div id="{sid}-i{i_}" class="item"><span class="dot"></span>{html.escape(txt)}</div>')
            js += item_in(f"#{sid}-i{i_}", max(0.3, t_ - st))
        body.append("      </div>")
    if s.get("sub"):
        body.append('      <div class="subrow">')
        for i_, (t_, txt) in enumerate(s["sub"]):
            body.append(f'        <span id="{sid}-s{i_}" class="chip">{html.escape(txt)}</span>')
            js += f'    tl.fromTo("#{sid}-s{i_}", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2)" }}, {t_ - st:.2f});\n'
        body.append("      </div>")
    if s.get("stat"):
        k2 = s["stat"]; lt_ = k2["t"] - st
        body.append(f'      <div id="{sid}-stat" class="stat"><div id="{sid}-num" class="num">0</div><div class="lbl">{html.escape(k2["label"])}</div></div>')
        body.append(f'      <div class="subrow"><span id="{sid}-chip" class="chip">{html.escape(k2["chip"][1])}</span></div>')
        js += f'    tl.fromTo("#{sid}-stat", {{ opacity: 0, y: 16 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: "back.out(1.6)" }}, {lt_:.2f});\n'
        js += (f'    const {sid}N = {{ v: 0 }}; const {sid}El = document.getElementById("{sid}-num");\n'
               f'    tl.fromTo({sid}N, {{ v: 0 }}, {{ v: {k2["value"]}, duration: 1.2, ease: "power3.out", '
               f'onUpdate: () => {{ {sid}El.textContent = Math.round({sid}N.v).toLocaleString("en-US"); }} }}, {lt_:.2f});\n')
        js += f'    tl.fromTo("#{sid}-chip", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "back.out(2)" }}, {k2["chip"][0] - st:.2f});\n'
    if s.get("steps"):
        body.append('      <div class="steps">')
        for i_, (t_, txt) in enumerate(s["steps"]):
            last = " last" if i_ == len(s["steps"]) - 1 else ""
            body.append(f'        <div id="{sid}-st{i_}" class="step{last}"><span class="n">{i_ + 1}</span>{html.escape(txt)}</div>')
            js += item_in(f"#{sid}-st{i_}", t_ - st)
        body.append("      </div>")
    body.append("    </div>")
    return scene(sid, "\n".join(body), js)

for s in SCENES: write(f"compositions/{s['id']}.html", build(s))

# ---------------- root ----------------
hosts = [f'      <div id="intro" data-composition-id="intro" data-composition-src="compositions/intro.html" data-start="0" '
         f'data-duration="{OFF}" data-track-index="10" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index:80"></div>',
         f'      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html" data-start="{OFF}" '
         f'data-duration="{RAW}" data-track-index="4" data-track-kind="captions" data-width="1920" data-height="1080" style="z-index:62"></div>']
for i_, s in enumerate(SCENES):
    hosts.append(f'      <div id="{s["id"]}" data-composition-id="{s["id"]}" data-composition-src="compositions/{s["id"]}.html" '
                 f'data-start="{A(s["start"])}" data-duration="{s["dur"]}" data-track-index="{11 + i_}" data-track-kind="graphics" '
                 f'data-width="1920" data-height="1080" style="z-index:60"></div>')
hosts.extend(bd_hosts)
hosts.append(f'      <div id="outro" data-composition-id="outro" data-composition-src="compositions/outro.html" data-start="{A(RAW)}" '
             f'data-duration="{POST}" data-track-index="40" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index:80"></div>')

sfx = []
SFX_LEN = {"assets/sfx/whoosh.mp3": 0.575, "assets/sfx/whoosh-cinematic.mp3": 5.544, "assets/sfx/pop.mp3": 0.72}
def place(sid, src, film_t, peak, vol=0.3, rate=1.0):
    lane = 60 + len(sfx) % 3
    sfx.append(f'      <audio id="{sid}" class="clip" src="{src}" data-start="{max(0, round(film_t - peak + 0.033, 3))}" '
               f'data-duration="{round(SFX_LEN[src] / rate, 3)}" data-volume="{vol}" data-playback-rate="{rate}" data-track-index="{lane}"></audio>')
place("sfx-open", "assets/sfx/whoosh-cinematic.mp3", OFF - 0.1, 2.503, 0.25)
rates = [1.0, 0.88, 1.12]
for n_, s in enumerate(x for x in SCENES if x["kind"] != "lt"):
    place(f"sfx-{s['id']}", "assets/sfx/pop.mp3" if s["kind"] == "card" else "assets/sfx/whoosh.mp3",
          A(s["start"]) + 0.12, 0.12 if s["kind"] == "card" else 0.162 / rates[n_ % 3], 0.28, 1.0 if s["kind"] == "card" else rates[n_ % 3])
for a, b, x in BOOKS:
    place(f"sfx-book{int(a)}", "assets/sfx/whoosh.mp3", A(a) + 0.3, 0.162 / 0.88, 0.25, 0.88)
place("sfx-stat", "assets/sfx/pop.mp3", A(86.6) + 0.05, 0.12, 0.3)
place("sfx-end", "assets/sfx/whoosh.mp3", A(RAW), 0.162 / 0.88, 0.3, 0.88)

music_auto = json.dumps({"version": 1, "lanes": [{"target": "volume", "points": [
    {"t": 0, "v": 0.5}, {"t": OFF - 0.6, "v": 0.5}, {"t": OFF + 0.4, "v": 0.15},
    {"t": A(RAW) - 0.4, "v": 0.15}, {"t": A(RAW) + 0.3, "v": 0.5}, {"t": TOTAL, "v": 0.5}]}]}).replace('"', "&quot;")
watermark = ('      <div id="wm" class="clip" data-start="0" data-duration="%s" data-track-index="90" data-layout-ignore '
             'style="position:absolute;left:40px;top:28px;z-index:99;font:900 56px Inter,sans-serif;'
             'color:rgba(255,255,255,.32);letter-spacing:.06em;">PRATONTON</div>' % TOTAL) if PREVIEW else ""

write("index.html", f"""<!doctype html>
<html lang="ms">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #0B1D3A; }}
      #root {{ width: 100%; height: 100%; position: relative; font-family: Inter, sans-serif; }}
      #win {{ position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; overflow: hidden; z-index: 50;
        border-radius: 44px; box-shadow: 0 0 0 14px #fff, 0 50px 120px rgba(0,0,0,.5); background: #000; }}
      #cam {{ position: absolute; inset: 0; }}
      #footage {{ position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; object-fit: cover; }}
      #logo-bug {{ position: absolute; right: 40px; top: 32px; z-index: 70; height: 138px; background: #fff;
        border-radius: 18px; padding: 10px 16px; box-shadow: 0 8px 24px rgba(0,0,0,.25); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
      <div id="win" data-layout-allow-overflow>
        <div id="cam">
          <video id="footage" class="clip" src="assets/footage/review_graded.mp4" data-start="{OFF}" data-duration="{RAW}"
            data-track-index="1" muted playsinline></video>
        </div>
      </div>
      <img id="logo-bug" class="clip" src="assets/img/logo-jnnt.png" alt="Logo Kementerian Pendidikan, Jemaah Nazir Negeri Terengganu"
        data-start="{OFF}" data-duration="{RAW}" data-track-index="2">
{chr(10).join(hosts)}
{watermark}
      <audio id="voice" class="clip" src="assets/audio/voice.wav" data-start="{OFF}" data-duration="279.98" data-volume="1" data-track-index="50"></audio>
      <audio id="music" class="clip" src="assets/audio/music.m4a" data-start="0" data-duration="{TOTAL}" data-volume="1"
        data-fade-out="2.5" data-track-index="51" data-automation="{music_auto}"></audio>
{chr(10).join(sfx)}
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
{chr(10).join(cam_js)}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
""")
print("ok", TOTAL, "groups", len(groups), "layout keys", len(keys), "segments", len(SEG))
