"""Generate the HyperFrames project for the #MERZ book review.

All times in SPEECH come from the word-level transcript (raw footage seconds).
OFF shifts them onto the film clock (the 3 s title card plays first).
Usage: gen.py <project_dir> [--preview]
"""
import json, os, sys, html

P = sys.argv[1]
PREVIEW = "--preview" in sys.argv
OFF = 3.0
RAW = 280.04
POST = 4.0
TOTAL = round(OFF + RAW + POST, 2)

NAVY, NAVY2, GOLD, INK = "#0D2142", "#183A6E", "#F5C400", "#FFFFFF"
NAME = "MOHD FAHMI ASYRAF BIN MOHD NOR AZMI"
ROLE = "Nazir Sekolah · Jemaah Nazir Negeri Terengganu"
BOOK = "#MERZ: Anak Penoreh Kini Pilot"
AUTHOR = "Mohd Ezairol Rezan Zainol"

def A(t):  # raw footage seconds -> film seconds
    return round(t + OFF, 3)

# ---------------- camera: framing states on the footage wrapper ----------------
WIDE, MED, CLOSE = (1.0, 960, 540), (1.3, 1030, 516), (1.6, 1030, 436)
SIDE, SIDE2 = (1.15, 830, 520), (1.3, 860, 470)      # speaker pushed right, cards on the left
SPLITF = (1.0, 550, 540)                               # speaker in the right half beside the book panel
def BOOKF(x): return (1.45, x, 601)                    # book fills the lower frame, whole face kept
CAM = [(0, WIDE), (11.6, MED), (15.4, SPLITF), (22.5, BOOKF(1000)), (26.2, SIDE), (40.6, CLOSE),
       (41.8, BOOKF(1000)), (45.4, MED), (51.0, SIDE), (57.2, MED), (61.6, BOOKF(970)), (65.0, WIDE),
       (69.0, CLOSE), (76.2, SIDE), (93.6, MED), (103.0, SIDE), (112.0, WIDE), (115.4, SIDE),
       (132.1, SIDE2), (154.4, SIDE), (176.8, MED), (185.4, SIDE), (210.6, CLOSE), (216.3, BOOKF(860)),
       (219.3, WIDE), (226.4, BOOKF(830)), (229.4, CLOSE), (237.2, SIDE), (251.3, MED), (260.4, SIDE),
       (271.3, WIDE), (273.8, BOOKF(1030)), (278.2, WIDE)]
BOOK_ZOOMS = [t for t, s in CAM if s[0] == 1.45]

def cam_xy(state, clamp=True):
    z, cx, cy = state
    x, y = z * (960 - cx), z * (540 - cy)
    if clamp:
        mx, my = 960 * (z - 1), 540 * (z - 1)
        x, y = max(-mx, min(mx, x)), max(-my, min(my, y))
    return z, round(x, 1), round(y, 1)

# ---------------- overlays (raw times from the transcript) ----------------
# kind card: kicker, title, items [(raw t, text)], optional sub [(raw t, text)]
SCENES = [
  dict(id="lt", src="compositions/lt-stack-bars.html", start=4.0, dur=7.4),
  dict(id="booksplit", kind="split", start=15.4, dur=7.85),
  dict(id="br-getah", kind="broll", start=26.6, dur=6.0, media="img", src="assets/img/broll-getah.jpg",
       caption="Anak penoreh getah", sfx=True),
  dict(id="br-pesawat", kind="broll", start=33.4, dur=7.0, media="video", src="assets/broll/sky-plane.mp4",
       caption="Juruterbang · pesawat ke seluruh dunia", sfx=True),
  dict(id="br-kampung", kind="broll", start=51.4, dur=5.6, media="img", src="assets/img/broll-kampung.jpg",
       caption="Membesar sebagai anak kampung", sfx=True),
  dict(id="jobs", kind="card", start=76.6, dur=16.8, kicker="Tidak memilih pekerjaan",
       title="Bermula dari bawah",
       items=[(77.3, "Pengawal keselamatan"), (80.4, "Pekerja kilang"), (81.2, "Batu Pahat, Johor")],
       stat=dict(t=86.6, value=26000, label="permohonan menyertai pasukan polis", chip=(92.0, "Antara yang terpilih"))),
  dict(id="br-pesawat2", kind="broll", start=103.6, dur=8.2, media="video", src="assets/broll/sky-plane.mp4",
       mstart=0.0, caption="Juruterbang pesawat komersial", sfx=True),
  dict(id="lesson1", kind="card", start=116.2, dur=15.7, kicker="Pengajaran 1",
       title="Kejayaan tidak ditentukan oleh latar belakang keluarga",
       items=[(122.0, "Kekurangan hari ini bukan masa depan kita")]),
  dict(id="lesson2", kind="card", start=133.2, dur=20.9, kicker="Pengajaran 2",
       title="Jangan malu untuk bermula dari bawah",
       items=[(142.1, "Pengawal keselamatan"), (143.9, "Pekerja kilang")],
       sub=[(150.5, "Disiplin"), (151.5, "Kematangan"), (152.9, "Ketahanan diri")]),
  dict(id="lesson3", kind="card", start=155.2, dur=21.4, kicker="Pengajaran 3",
       title="Kejayaan ialah satu proses, bukan datang tiba-tiba",
       steps=[(164.3, "Anak kampung"), (165.7, "Pekerja biasa"), (167.2, "Pegawai polis"), (169.6, "Juruterbang")]),
  dict(id="br-murid", kind="broll", start=186.0, dur=12.6, media="img", src="assets/img/broll-murid.jpg",
       caption="Murid daripada pelbagai latar belakang", sfx=True),
  dict(id="future", kind="card", start=199.6, dur=10.8, kicker="Murid biasa hari ini",
       title="Mungkin pemimpin masa akan datang",
       items=[(205.4, "Doktor"), (205.9, "Juruterbang"), (208.4, "Pemimpin")]),
  dict(id="quote", kind="quote", start=237.6, dur=13.5),
  dict(id="values", kind="card", start=260.6, dur=10.6, kicker="Buku ini kisah tentang",
       title="", items=[(261.2, "Keberanian untuk bermimpi"), (264.2, "Kesanggupan bermula dari bawah"),
                        (267.3, "Keazaman mengubah kehidupan")]),
]

BASE_CSS = f"""
#root {{ position: absolute; inset: 0; font-family: Inter, sans-serif; color: {INK}; }}
.card {{ position: absolute; left: 64px; top: 236px; width: 660px; padding: 40px 44px 44px;
  background: rgba(13,33,66,.9); border-radius: 18px; border-left: 8px solid {GOLD};
  box-shadow: 0 24px 60px rgba(0,0,0,.45); }}
.kicker {{ font-weight: 700; font-size: 28px; letter-spacing: .14em; text-transform: uppercase; color: {GOLD}; }}
.title {{ margin-top: 16px; font-weight: 900; font-size: 50px; line-height: 1.1; letter-spacing: -.01em; }}
.w {{ display: inline-block; margin-right: .24em; }}
.items {{ margin-top: 26px; display: flex; flex-direction: column; gap: 12px; }}
.item {{ display: flex; align-items: center; gap: 16px; font-weight: 700; font-size: 32px;
  background: rgba(255,255,255,.08); border-radius: 12px; padding: 14px 20px; }}
.dot {{ width: 14px; height: 14px; border-radius: 50%; background: {GOLD}; flex: none; }}
.subrow {{ margin-top: 18px; display: flex; gap: 10px; flex-wrap: wrap; }}
.chip {{ font-weight: 700; font-size: 28px; color: {NAVY}; background: {GOLD}; border-radius: 999px; padding: 8px 20px; }}
.stat {{ margin-top: 26px; }}
.stat .num {{ font-weight: 900; font-size: 96px; line-height: 1; color: {GOLD}; font-variant-numeric: tabular-nums; }}
.stat .lbl {{ margin-top: 6px; font-weight: 700; font-size: 28px; color: #D8E1F0; }}
.steps {{ margin-top: 28px; display: flex; flex-direction: column; gap: 0; }}
.step {{ display: flex; align-items: center; gap: 18px; font-weight: 700; font-size: 32px; height: 62px; }}
.step .n {{ width: 50px; height: 50px; border-radius: 50%; border: 3px solid {GOLD}; color: {GOLD};
  display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: 900; flex: none; }}
.step.last .n {{ background: {GOLD}; color: {NAVY}; }}
"""

def words(text):
    return "".join(f'<span class="w">{html.escape(w)}</span>' for w in text.split())

def scene_file(sid, body, css, js, extra_vars=""):
    return f"""<template>
  <style>{BASE_CSS}{css}
  </style>
  <div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080"{extra_vars}>
{body}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{js}
    window.__timelines["{sid}"] = tl;
  </script>
</template>
"""

def card_in(sel, dur):
    # arrive slow (long-tailed), leave clean and shorter
    return f"""    tl.fromTo("{sel}", {{ opacity: 0, x: -40, filter: "blur(8px)" }}, {{ opacity: 1, x: 0, filter: "blur(0px)", duration: 0.55, ease: "expo.out" }}, 0);
    tl.to("{sel}", {{ opacity: 0, x: -24, filter: "blur(8px)", duration: 0.3, ease: "power3.in" }}, {dur - 0.38:.2f});
"""

def title_in(sel, t0=0.18):
    return f"""    tl.fromTo("{sel} .w", {{ opacity: 0, filter: "blur(6px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.16, ease: "power4.out", stagger: 0.07 }}, {t0});
"""

def build_card(s):
    sid, st, dur = s["id"], s["start"], s["dur"]
    body = [f'    <div id="{sid}-card" class="card">', f'      <div class="kicker">{html.escape(s["kicker"])}</div>']
    if s.get("title"):
        body.append(f'      <div id="{sid}-title" class="title">{words(s["title"])}</div>')
    js = card_in(f"#{sid}-card", dur)
    if s.get("title"):
        js += title_in(f"#{sid}-title")
    if s.get("items"):
        body.append('      <div class="items">')
        for i, (t, txt) in enumerate(s["items"]):
            body.append(f'        <div id="{sid}-i{i}" class="item"><span class="dot"></span>{html.escape(txt)}</div>')
            js += f'    tl.fromTo("#{sid}-i{i}", {{ opacity: 0, x: -18, filter: "blur(6px)" }}, {{ opacity: 1, x: 0, filter: "blur(0px)", duration: 0.35, ease: "expo.out" }}, {max(0.3, t - st):.2f});\n'
        body.append("      </div>")
    if s.get("sub"):
        body.append('      <div class="subrow">')
        for i, (t, txt) in enumerate(s["sub"]):
            body.append(f'        <span id="{sid}-s{i}" class="chip">{html.escape(txt)}</span>')
            js += f'    tl.fromTo("#{sid}-s{i}", {{ opacity: 0, scale: 0.85 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "back.out(1.4)" }}, {t - st:.2f});\n'
        body.append("      </div>")
    if s.get("stat"):
        k = s["stat"]; lt = k["t"] - st
        body.append(f'      <div id="{sid}-stat" class="stat"><div id="{sid}-num" class="num">0</div>'
                    f'<div class="lbl">{html.escape(k["label"])}</div></div>')
        body.append(f'      <div class="subrow"><span id="{sid}-chip" class="chip">{html.escape(k["chip"][1])}</span></div>')
        js += f'    tl.fromTo("#{sid}-stat", {{ opacity: 0, y: 16 }}, {{ opacity: 1, y: 0, duration: 0.4, ease: "expo.out" }}, {lt:.2f});\n'
        js += (f'    const {sid}N = {{ v: 0 }}; const {sid}El = document.getElementById("{sid}-num");\n'
               f'    tl.fromTo({sid}N, {{ v: 0 }}, {{ v: {k["value"]}, duration: 1.2, ease: "power3.out", '
               f'onUpdate: () => {{ {sid}El.textContent = Math.round({sid}N.v).toLocaleString("en-US"); }} }}, {lt:.2f});\n')
        js += f'    tl.fromTo("#{sid}-chip", {{ opacity: 0, scale: 0.85 }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "back.out(1.4)" }}, {k["chip"][0] - st:.2f});\n'
    if s.get("steps"):
        body.append('      <div class="steps">')
        n = len(s["steps"])
        for i, (t, txt) in enumerate(s["steps"]):
            last = " last" if i == n - 1 else ""
            body.append(f'        <div id="{sid}-st{i}" class="step{last}"><span class="n">{i + 1}</span>{html.escape(txt)}</div>')
            js += f'    tl.fromTo("#{sid}-st{i}", {{ opacity: 0, x: -18 }}, {{ opacity: 1, x: 0, duration: 0.3, ease: "expo.out" }}, {t - st:.2f});\n'
        body.append("      </div>")
    body.append("    </div>")
    return scene_file(sid, "\n".join(body), "", js)

def build_broll(s):
    sid, dur = s["id"], s["dur"]
    if s["media"] == "video":
        media = (f'<video id="{sid}-v" class="clip" src="{s["src"]}" data-start="0" data-duration="{dur}" '
                 f'data-media-start="{s.get("mstart", 0)}" muted playsinline></video>')
    else:
        media = f'<img id="{sid}-v" src="{s["src"]}" alt="">'
    css = f"""
#{sid}-frame {{ position: absolute; left: 64px; top: 236px; width: 660px; }}
#{sid}-win {{ width: 660px; height: 400px; border-radius: 18px; overflow: hidden; border: 6px solid {INK};
  box-shadow: 0 24px 60px rgba(0,0,0,.45); background: {NAVY}; }}
#{sid}-kb {{ width: 100%; height: 100%; }}
#{sid}-kb img, #{sid}-kb video {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
#{sid}-cap {{ display: inline-block; margin-top: 16px; font-weight: 700; font-size: 28px; background: {NAVY};
  border-left: 6px solid {GOLD}; padding: 10px 20px; border-radius: 8px; }}
"""
    body = f"""    <div id="{sid}-frame">
      <div id="{sid}-win"><div id="{sid}-kb">{media}</div></div>
      <div id="{sid}-cap">{html.escape(s["caption"])}</div>
    </div>"""
    js = card_in(f"#{sid}-frame", dur)
    js += f'    tl.fromTo("#{sid}-kb", {{ scale: 1.0 }}, {{ scale: 1.07, duration: {dur:.2f}, ease: "none" }}, 0);\n'
    js += f'    tl.fromTo("#{sid}-cap", {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: 0.35, ease: "expo.out" }}, 0.35);\n'
    return scene_file(sid, body, css, js)

def build_split(s):
    sid, dur = s["id"], s["dur"]
    css = f"""
#{sid}-panel {{ position: absolute; left: 0; top: 0; width: 960px; height: 1080px;
  background: linear-gradient(180deg, {NAVY} 0%, {NAVY2} 100%); border-right: 8px solid {GOLD}; }}
#{sid}-cover {{ position: absolute; left: 50%; top: 120px; height: 600px; margin-left: -208px;
  box-shadow: 0 26px 60px rgba(0,0,0,.55); border-radius: 6px; }}
#{sid}-t {{ position: absolute; left: 0; right: 0; top: 770px; text-align: center; font-weight: 900; font-size: 46px; }}
#{sid}-a {{ position: absolute; left: 0; right: 0; top: 840px; text-align: center; font-weight: 700; font-size: 32px; color: {GOLD}; }}
"""
    body = f"""    <div id="{sid}-panel">
      <img id="{sid}-cover" src="assets/img/kulit-buku.jpg" alt="Kulit buku">
      <div id="{sid}-t">{words(BOOK)}</div>
      <div id="{sid}-a">{html.escape(AUTHOR)}</div>
    </div>"""
    js = f"""    tl.fromTo("#{sid}-panel", {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: 0.6, ease: "power3.out" }}, 0);
    tl.fromTo("#{sid}-cover", {{ opacity: 0, y: 40, filter: "blur(8px)" }}, {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.7, ease: "expo.out" }}, 0.35);
{title_in(f"#{sid}-t", 0.9)}    tl.fromTo("#{sid}-a", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: "power2.out" }}, 1.6);
    tl.to("#{sid}-panel", {{ clipPath: "inset(0 100% 0 0)", duration: 0.38, ease: "power3.in" }}, {dur - 0.42:.2f});
"""
    return scene_file(sid, body, css, js)

def build_quote(s):
    sid, st, dur = s["id"], s["start"], s["dur"]
    l1 = "Kita mungkin tidak mampu memilih di mana kita dilahirkan,"
    l2 = "tetapi kita masih boleh berusaha untuk menentukan ke mana hala tuju kehidupan kita."
    css = f"""
#{sid}-box {{ position: absolute; left: 64px; top: 200px; width: 700px; padding: 48px 48px 52px;
  background: rgba(13,33,66,.92); border-radius: 18px; border-left: 8px solid {GOLD}; box-shadow: 0 24px 60px rgba(0,0,0,.45); }}
#{sid}-mark {{ font-weight: 900; font-size: 120px; line-height: .6; color: {GOLD}; }}
#{sid}-l1, #{sid}-l2 {{ margin-top: 18px; font-weight: 700; font-size: 40px; line-height: 1.25; }}
#{sid}-l2 .hl {{ color: {GOLD}; }}
"""
    l2h = words(l2).replace('<span class="w">hala</span><span class="w">tuju</span>',
                            '<span class="w hl">hala</span><span class="w hl">tuju</span>')
    body = f"""    <div id="{sid}-box">
      <div id="{sid}-mark">&ldquo;</div>
      <div id="{sid}-l1">{words(l1)}</div>
      <div id="{sid}-l2">{l2h}</div>
    </div>"""
    js = card_in(f"#{sid}-box", dur)
    js += f'    tl.fromTo("#{sid}-l1 .w", {{ opacity: 0.18 }}, {{ opacity: 1, duration: 0.2, ease: "power2.out", stagger: 0.42 }}, {237.9 - st:.2f});\n'
    js += f'    tl.fromTo("#{sid}-l2 .w", {{ opacity: 0.18 }}, {{ opacity: 1, duration: 0.2, ease: "power2.out", stagger: 0.47 }}, {243.0 - st:.2f});\n'
    return scene_file(sid, body, css, js)

def build_bookend(sid, kicker, lines, sub):
    css = f"""
#{sid}-bg {{ position: absolute; inset: 0; background: linear-gradient(180deg, {NAVY} 0%, {NAVY2} 100%); }}
#{sid}-cover {{ position: absolute; left: 230px; top: 190px; height: 700px; box-shadow: 0 30px 70px rgba(0,0,0,.55); border-radius: 6px; }}
#{sid}-txt {{ position: absolute; left: 860px; top: 330px; width: 960px; }}
#{sid}-k {{ font-weight: 700; font-size: 32px; letter-spacing: .14em; color: {GOLD}; text-transform: uppercase; }}
#{sid}-rule {{ width: 96px; height: 7px; background: {GOLD}; margin: 26px 0 34px; }}
.{sid}-l {{ font-weight: 900; font-size: 84px; line-height: 1.08; }}
.{sid}-l.big {{ font-size: 108px; }}
#{sid}-sub {{ margin-top: 30px; font-size: 34px; color: #D8E1F0; line-height: 1.45; }}
#{sid}-logo {{ position: absolute; right: 48px; top: 40px; height: 140px; padding: 14px 20px; background: #fff; border-radius: 16px; }}
"""
    ls = "\n".join(f'        <div id="{sid}-l{i}" class="{sid}-l{" big" if i == 0 and len(lines) > 1 else ""}">{html.escape(t)}</div>'
                   for i, t in enumerate(lines))
    subh = "<br>".join(html.escape(x) for x in sub)
    body = f"""    <div id="{sid}-bg"></div>
    <img id="{sid}-logo" src="assets/img/logo-jnnt.png" alt="Logo Jemaah Nazir Negeri Terengganu">
    <img id="{sid}-cover" src="assets/img/kulit-buku.jpg" alt="Kulit buku">
    <div id="{sid}-txt">
      <div id="{sid}-k">{html.escape(kicker)}</div>
      <div id="{sid}-rule"></div>
{ls}
      <div id="{sid}-sub">{subh}</div>
    </div>"""
    js = f"""    tl.fromTo("#{sid}-cover", {{ opacity: 0, y: 50, filter: "blur(10px)" }}, {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.9, ease: "expo.out" }}, 0.1);
    tl.fromTo("#{sid}-k", {{ opacity: 0, filter: "blur(8px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.2, ease: "power4.out" }}, 0.35);
    tl.fromTo("#{sid}-rule", {{ scaleX: 0, transformOrigin: "0 50%" }}, {{ scaleX: 1, duration: 0.5, ease: "expo.out" }}, 0.45);
    tl.fromTo(".{sid}-l", {{ opacity: 0, filter: "blur(8px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.2, ease: "power4.out", stagger: 0.12 }}, 0.6);
    tl.fromTo("#{sid}-sub", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: "power2.out" }}, 0.55);
"""
    return scene_file(sid, body, css, js)

os.makedirs(f"{P}/compositions", exist_ok=True)
def write(path, text):
    open(f"{P}/{path}", "w").write(text)

for s in SCENES:
    k = s.get("kind")
    if k == "card": write(f"compositions/{s['id']}.html", build_card(s))
    elif k == "broll":
        path = f"{P}/compositions/{s['id']}.html"
        if os.path.exists(f"{P}/{s['src']}"): write(f"compositions/{s['id']}.html", build_broll(s))
        elif os.path.exists(path): os.remove(path)
    elif k == "split": write(f"compositions/{s['id']}.html", build_split(s))
    elif k == "quote": write(f"compositions/{s['id']}.html", build_quote(s))
write("compositions/intro.html", build_bookend("intro", "Ulasan buku", ["#MERZ", "Anak Penoreh", "Kini Pilot"], [AUTHOR]))
write("compositions/outro.html", build_bookend("outro", "Ulasan buku", ["Terima kasih"], [NAME, "Nazir Sekolah", "Jemaah Nazir Negeri Terengganu"]))

# ---------------- root composition ----------------
hosts = [f'      <div id="intro" data-composition-id="intro" data-composition-src="compositions/intro.html" data-start="0" '
         f'data-duration="{OFF}" data-track-index="10" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index:20"></div>']
for i, s in enumerate(SCENES):
    if s.get("kind") == "broll" and not os.path.exists(f"{P}/{s['src']}"):
        print("skip (no media yet):", s["id"]); continue
    src = s.get("src") if s["id"] == "lt" else f"compositions/{s['id']}.html"
    hosts.append(f'      <div id="{s["id"]}" data-composition-id="{s["id"]}" data-composition-src="{src}" '
                 f'data-start="{A(s["start"])}" data-duration="{s["dur"]}" data-track-index="{11 + i}" data-track-kind="graphics" '
                 f'data-width="1920" data-height="1080" style="z-index:{5 + (1 if s.get("kind") == "split" else 0)}"></div>')
hosts.append(f'      <div id="outro" data-composition-id="outro" data-composition-src="compositions/outro.html" data-start="{A(RAW)}" '
             f'data-duration="{POST}" data-track-index="40" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index:20"></div>')

# camera tweens on #cam (film time); D = transition length, eased both ways
D = 0.7
cam_js = []
z0, x0, y0 = cam_xy(CAM[0][1])
cam_js.append(f'      tl.set("#cam", {{ scale: {z0}, x: {x0}, y: {y0}, transformOrigin: "50% 50%" }}, 0);')
for t, st in CAM[1:]:
    z, x, y = cam_xy(st, clamp=(st != SPLITF))
    cam_js.append(f'      tl.to("#cam", {{ scale: {z}, x: {x}, y: {y}, duration: {D}, ease: "power2.inOut" }}, {A(t)});')

# sound: whooshes on panel entrances (peak 0.162 s lands one frame after the picture), pop on the stat
sfx = []
SFX_LEN = {"assets/sfx/whoosh.mp3": 0.575, "assets/sfx/whoosh-cinematic.mp3": 5.544, "assets/sfx/pop.mp3": 0.72}
def place(sid, src, film_t, peak, vol=0.35, rate=1.0):
    lane = 60 + len(sfx) % 3
    sfx.append(f'      <audio id="{sid}" class="clip" src="{src}" data-start="{max(0, round(film_t - peak + 0.033, 3))}" '
               f'data-duration="{round(SFX_LEN[src] / rate, 3)}" data-volume="{vol}" data-playback-rate="{rate}" data-track-index="{lane}"></audio>')
place("sfx-open", "assets/sfx/whoosh-cinematic.mp3", OFF - 0.1, 2.503, 0.25)
rates = [1.0, 0.88, 1.12]
n = 0
for s in SCENES:
    if s.get("kind") == "broll" and not os.path.exists(f"{P}/{s['src']}"): continue
    if s.get("kind") in ("split", "broll") or s["id"] in ("lesson1", "lesson2", "lesson3", "quote"):
        r = rates[n % 3]
        place(f"sfx-{s['id']}", "assets/sfx/whoosh.mp3", A(s["start"]) + 0.15, 0.162 / r, 0.3, r); n += 1
place("sfx-stat", "assets/sfx/pop.mp3", A(86.6) + 0.05, 0.12, 0.3)
place("sfx-end", "assets/sfx/whoosh.mp3", A(RAW), 0.162 / 0.88, 0.3, 0.88)

music_auto = json.dumps({"version": 1, "lanes": [{"target": "volume", "points": [
    {"t": 0, "v": 0.5}, {"t": OFF - 0.6, "v": 0.5}, {"t": OFF + 0.4, "v": 0.14},
    {"t": A(RAW) - 0.4, "v": 0.14}, {"t": A(RAW) + 0.3, "v": 0.5}, {"t": TOTAL, "v": 0.5}]}]}).replace('"', "&quot;")

watermark = ('      <div id="wm" class="clip" data-start="0" data-duration="%s" data-track-index="90" data-layout-ignore '
             'style="position:absolute;left:40px;top:28px;z-index:99;font:900 56px Inter,sans-serif;'
             'color:rgba(255,255,255,.32);letter-spacing:.06em;">PRATONTON</div>' % TOTAL) if PREVIEW else ""

index = f"""<!doctype html>
<html lang="ms">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #000; }}
      #root {{ width: 100%; height: 100%; position: relative; font-family: Inter, sans-serif; }}
      #bg {{ position: absolute; inset: 0; background: {NAVY}; }}
      #cam {{ position: absolute; inset: 0; z-index: 1; }}
      #footage {{ position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; object-fit: cover; }}
      #logo-bug {{ position: absolute; right: 40px; top: 32px; z-index: 30; height: 138px; background: #fff;
        border-radius: 14px; padding: 10px 16px; box-shadow: 0 8px 24px rgba(0,0,0,.25); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
      <div id="bg"></div>
      <div id="cam">
        <video id="footage" class="clip" src="assets/footage/review_graded.mp4" data-start="{OFF}" data-duration="{RAW}"
          data-track-index="1" muted playsinline></video>
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
"""
write("index.html", index)

# lower third: brand the registry block (name/role, colours, Inter) and hold it for the slot
lt = open(f"{P}/compositions/lt-stack-bars.html").read()
for a, b in [("Maya Chen", NAME), ("Host · Neuroscientist", ROLE), ("#141518", NAVY), ("#ffd23f", GOLD),
             ('"Archivo Black", sans-serif', "Inter, sans-serif"), ('"Space Mono", monospace', "Inter, sans-serif"),
             ("font-size: 52px;\n        font-weight: 400;", "font-size: 50px;\n        font-weight: 900;"),
             ('data-duration="4.8"', 'data-duration="7.4"'), ("}, 4.25);", "}, 6.85);"), ("}, 4.32);", "}, 6.92);"),
             ("}, 4.75);", "}, 7.35);"), ("letter-spacing: 0.06em;", "letter-spacing: 0.04em;"), ("font-size: 23px;", "font-size: 28px;"), ("gsap@3.14.2", "gsap@3.15.0")]:
    lt = lt.replace(a, b)
write("compositions/lt-stack-bars.html", lt)
print("ok", TOTAL, "book zooms:", BOOK_ZOOMS)
