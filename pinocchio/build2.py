"""Versi 2: "Firash masuk ke dalam buku cerita kertas".

Lapisan (belakang -> depan):
  rakaman asal (bilik sebenar, 60 fps)            <- ffmpeg
  BACK  : dunia kertas + tulisan di belakang murid  <- HyperFrames (lutsinar di bahagian bilik sebenar)
  CUT   : murid dipotong (remove-background) + garis putih pelekat  <- ffmpeg
  FRONT : pembuka/penutup, headline slam, doodle boil, ombak depan  <- HyperFrames (lutsinar)

  python3 build2.py preview   # hf2/index.html dengan semua lapisan (pratonton/snapshot)
  python3 build2.py back      # hf2/index.html lapisan BACK sahaja (render .mov lutsinar)
  python3 build2.py front     # hf2/index.html lapisan FRONT sahaja (render .mov lutsinar)
  python3 build2.py track     # work/track.json kedudukan kepala daripada potongan
  python3 build2.py final back.mov front.mov out.mp4

Peraturan: persembahan asal penuh & berterusan; hanya latar ditukar dan grafik ditindih.
Masa dalam senarai ialah masa rakaman (p). Masa video = p + T0.
"""
import json, math, os, random, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build as v1  # pembuka, penutup, lower-third diguna semula

HF = os.path.join(HERE, "hf2")
v1.HF = HF
T0, PERF, CLOSE, TOTAL = v1.T0, v1.PERF, v1.CLOSE, v1.TOTAL
SRC = v1.SRC
CUT = os.path.join(HERE, "work", "cut", "firash_cut.webm")
TRACK = os.path.join(HERE, "work", "track.json")

R = random.Random(5)


def a(p):
    return round(p + T0, 3)


def write(name, body):
    os.makedirs(os.path.join(HF, "compositions"), exist_ok=True)
    open(os.path.join(HF, "compositions", f"{name}.html"), "w").write(body)


# ============================================================ gaya bersama
CSS = """
#root{position:absolute;inset:0;overflow:hidden;}
.L{position:absolute;inset:0;}
.L svg{position:absolute;inset:0;width:1920px;height:1080px;overflow:visible;}
.hl{position:absolute;font-family:'Archivo Black',sans-serif;line-height:1;white-space:nowrap;
  letter-spacing:.01em;opacity:0;}
.hand{font-family:'Caveat',cursive;font-weight:700;}
.tape{position:absolute;width:110px;height:34px;background:rgba(255,246,214,.78);
  box-shadow:0 2px 4px rgba(0,0,0,.18);}
.photo{position:absolute;background:#fffaf0;padding:14px 14px 46px 14px;
  box-shadow:6px 9px 0 rgba(40,25,10,.28);opacity:0;}
.photo img{display:block;width:100%;height:100%;object-fit:cover;}
.grain{position:absolute;inset:0;width:1920px;height:1080px;mix-blend-mode:multiply;opacity:.55;}
"""
FONTS = """@font-face{font-family:'Caveat';src:url('assets/fonts/Caveat-700-latin.woff2') format('woff2');font-weight:700;font-display:block;}"""

BOIL_JS = """
var __renders=[];
function onUpd(fn){__renders.push(fn);}
tl.eventCallback("onUpdate",function(){for(var i=0;i<__renders.length;i++)__renders[i]();});
function hh(n,s){var x=Math.sin(n*127.1+(s||1)*311.7)*43758.5453;return (x-Math.floor(x))*2-1;}
function boil(sel,amp,rot,seed,t0,t1){var els=gsap.utils.toArray(sel);onUpd(function(){var t=tl.time();
  if(t<t0||t>t1)return;var st=Math.floor(t*30/3);for(var i=0;i<els.length;i++){
  gsap.set(els[i],{x:hh(st*3+i*97,seed)*amp,y:hh(st*3+1+i*97,seed)*amp,rotation:hh(st*3+2+i*97,seed)*rot});}});}
"""


def shadowed(d, fill, dy=9, dx=4, op=.28, extra=""):
    """bentuk kertas: bayang keras di bawah + bentuk utama"""
    return (f'<path d="{d}" fill="#1a0f05" opacity="{op}" transform="translate({dx},{dy})"/>'
            f'<path d="{d}" fill="{fill}" {extra}/>')


def hills(y, amp, waves, seed, h=1080):
    rr = random.Random(seed)
    pts = [(0, y)]
    n = 24
    ph = rr.uniform(0, 6.28)
    for i in range(1, n + 1):
        x = 1920 * i / n
        pts.append((x, y - amp * math.sin(ph + waves * 6.283 * i / n) - rr.uniform(-amp * .15, amp * .15)))
    d = f"M-40 {h+40} L-40 {pts[0][1]:.0f} " + " ".join(f"L{x:.0f} {yy:.0f}" for x, yy in pts) + f" L1960 {pts[-1][1]:.0f} L1960 {h+40} Z"
    return d


def wave_path(y, amp, n, seed, h=1080, w=1920):
    rr = random.Random(seed)
    d = f"M-60 {h+40} L-60 {y}"
    step = (w + 120) / n
    for i in range(n):
        x0 = -60 + i * step
        d += f" Q{x0+step/2:.0f} {y-amp*rr.uniform(.8,1.2):.0f} {x0+step:.0f} {y}"
    return d + f" L{w+60} {h+40} Z"


def star(cx, cy, r1, r2, n=5, rot=-90):
    pts = []
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r2
        ang = math.radians(rot + i * 180 / n)
        pts.append(f"{cx + r*math.cos(ang):.1f} {cy + r*math.sin(ang):.1f}")
    return "M" + " L".join(pts) + " Z"


def circle(cx, cy, r):
    return f"M{cx-r} {cy} a{r} {r} 0 1 0 {2*r} 0 a{r} {r} 0 1 0 {-2*r} 0 Z"


def rect(x, y, w, h, rx=0):
    if rx:
        return (f"M{x+rx} {y} H{x+w-rx} Q{x+w} {y} {x+w} {y+rx} V{y+h-rx} Q{x+w} {y+h} {x+w-rx} {y+h} "
                f"H{x+rx} Q{x} {y+h} {x} {y+h-rx} V{y+rx} Q{x} {y} {x+rx} {y} Z")
    return f"M{x} {y} H{x+w} V{y+h} H{x} Z"


def jagged_v(x, amp, seed):
    """garis koyakan menegak (untuk peralihan torn paper)"""
    rr = random.Random(seed)
    pts = []
    y = -20
    while y < 1100:
        pts.append((x + rr.uniform(-amp, amp), y))
        y += rr.uniform(18, 46)
    return pts


# ============================================================ teks headline
def headline(hid, text, x, y, size, color, rot, t, hold, tl="tl", edge="#2b1606", outline="#fff6e0", kind="slam", anchor="left"):
    """perkataan 'headline storm': slam masuk, getar kecil (boil), kemudian hanyut & pudar."""
    tx = "translateX(-50%)" if anchor == "center" else ""
    side = f"right:{x}px;" if anchor == "right" else f"left:{x}px;"
    st = (f"{side}top:{y}px;font-size:{size}px;color:{color};"
          f"text-shadow:-3px -3px 0 {outline},3px -3px 0 {outline},-3px 3px 0 {outline},3px 3px 0 {outline},0 4px 0 {outline},"
          f"{9}px {12}px 0 {edge};")
    inner = f'<div id="{hid}i" style="display:inline-block">{text}</div>'
    wrap = f'<div id="{hid}" class="hl" style="{st}"><div id="{hid}r" style="transform:rotate({rot}deg) {tx};display:inline-block">{inner}</div></div>'
    if kind == "slam":
        js = (f'{tl}.fromTo("#{hid}",{{opacity:0,scale:2.4}},{{opacity:1,scale:1,duration:.32,ease:"back.out(2.2)"}},{t:.2f});'
              f'{tl}.to("#{hid}",{{opacity:0,y:-30,duration:.5,ease:"power2.in"}},{t+hold:.2f});')
    elif kind == "drop":
        js = (f'{tl}.fromTo("#{hid}",{{opacity:0,y:-260}},{{opacity:1,y:0,duration:.55,ease:"bounce.out"}},{t:.2f});'
              f'{tl}.to("#{hid}",{{opacity:0,y:40,duration:.45,ease:"power2.in"}},{t+hold:.2f});')
    else:  # slide
        js = (f'{tl}.fromTo("#{hid}",{{opacity:0,x:-220}},{{opacity:1,x:0,duration:.45,ease:"power3.out"}},{t:.2f});'
              f'{tl}.to("#{hid}",{{opacity:0,x:120,duration:.45,ease:"power2.in"}},{t+hold:.2f});')
    js += f'boil("#{hid}i",2.2,1.1,{abs(hash(hid))%97+1},{t:.2f},{t+hold+.5:.2f});'
    return wrap, js


def photo(pid, src, x, y, w, h, rot, t_in, t_out, pos="50% 50%", tl="tl"):
    html = (f'<div id="{pid}" class="photo" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;transform:rotate({rot}deg)">'
            f'<img src="assets/img/{src}" style="object-position:{pos}"/>'
            f'<div class="tape" style="left:{w/2-55:.0f}px;top:-16px;transform:rotate({-rot*1.5:.1f}deg)"></div></div>')
    js = (f'{tl}.fromTo("#{pid}",{{opacity:0,y:-60,rotation:{rot-14}}},{{opacity:1,y:0,rotation:{rot},duration:.6,ease:"back.out(1.7)"}},{t_in:.2f});'
          f'{tl}.to("#{pid}",{{opacity:0,y:30,duration:.4,ease:"power2.in"}},{t_out:.2f});')
    return html, js


# ============================================================ babak dunia kertas (BACK)
# masa: (id, p0, p1, entrance)
WORLD = [
    ("w-frame", 0.0, 15.9, "none"),
    ("w-workshop", 15.0, 32.9, "rip"),
    ("w-night", 32.4, 49.7, "slide-down"),
    ("w-morning", 49.2, 59.3, "slide-right"),
    ("w-road", 58.8, 67.5, "slide-right"),
    ("w-theater", 67.0, 85.9, "curtain"),
    ("w-spot", 85.4, 97.5, "fade"),
    ("w-theater2", 97.0, 107.6, "fade"),
    ("w-carnival", 107.1, 138.6, "slide-up"),
    ("w-sea", 138.1, 151.0, "slide-down"),
    ("w-belly", 150.5, 168.3, "iris"),
    ("w-sea2", 167.8, 190.6, "burst"),
    ("w-home", 190.1, 213.0, "slide-right"),
    ("w-moral", 212.5, 233.9, "rip"),
]


def entrance_js(kind, sel="#scene"):
    if kind == "rip":
        # koyakan kertas: clip-path poligon bergerigi bergerak dari kiri ke kanan
        return ('var jag=[];var rr=7;for(var k=0;k<=40;k++){jag.push(k);}'
                'var stp={p:0};onUpd(function(){var p=stp.p;var pts=[];var X=-80+p*2120;'
                'pts.push("0px 0px");pts.push(X+"px 0px");for(var k=0;k<=40;k++){var yy=k*27;pts.push((X+hh(k,3)*26)+"px "+yy+"px");}'
                'pts.push(X+"px 1080px");pts.push("0px 1080px");'
                f'document.querySelector("{sel}").style.clipPath=p>=1?"none":"polygon("+pts.join(",")+")";}});'
                'tl.fromTo(stp,{p:0},{p:1,duration:.9,ease:"power2.inOut"},0);')
    if kind == "slide-down":
        return f'tl.fromTo("{sel}",{{yPercent:-100,rotation:-2}},{{yPercent:0,rotation:0,duration:.6,ease:"steps(8)"}},0);'
    if kind == "slide-up":
        return f'tl.fromTo("{sel}",{{yPercent:100,rotation:2}},{{yPercent:0,rotation:0,duration:.6,ease:"steps(8)"}},0);'
    if kind == "slide-right":
        return f'tl.fromTo("{sel}",{{xPercent:100,rotation:3}},{{xPercent:0,rotation:0,duration:.6,ease:"steps(8)"}},0);'
    if kind == "curtain":
        return f'tl.fromTo("{sel}",{{opacity:0}},{{opacity:1,duration:.4}},0);'
    if kind == "fade":
        return f'tl.fromTo("{sel}",{{opacity:0}},{{opacity:1,duration:.45}},0);'
    if kind == "iris":
        return ('var ir={r:0};onUpd(function(){'
                f'document.querySelector("{sel}").style.clipPath=ir.r>=1?"none":"circle("+(ir.r*1250)+"px at 1500px 420px)";}});'
                'tl.fromTo(ir,{r:0},{r:1,duration:.7,ease:"power2.in"},0);')
    if kind == "burst":
        return f'tl.fromTo("{sel}",{{scale:1.25,opacity:0}},{{scale:1,opacity:1,duration:.4,ease:"power3.out"}},0);'
    return ""


def grain():
    return '<img class="grain" src="assets/img/paper-grain.png"/>'


def scene(sid, p0, p1, entrance, svg, extra_html="", extra_js="", bg="#000", use_grain=True):
    dur = round(p1 - p0, 3)
    body = f'''<template>
<style>{FONTS}{CSS}</style>
<div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">
<div id="scene" class="L" style="background:{bg}">
<div class="L" id="{sid}-art"><svg viewBox="0 0 1920 1080">{svg}</svg></div>
{extra_html}
{grain() if use_grain else ""}
</div>
</div>
<script>
const tl = gsap.timeline({{paused:true}});
{BOIL_JS}
{entrance_js(entrance)}
{extra_js}
tl.set({{}},{{}},{dur-0.01:.2f});
window.__timelines["{sid}"] = tl;
</script>
</template>'''
    write(sid, body)
    return dur


def words_js(sid, items, p0):
    """items: (teks, p, x, y, saiz, warna, rot, tahan, jenis)"""
    H, J = [], []
    for k, it in enumerate(items):
        txt, p, x, y, size, col, rot, hold = it[:8]
        kind = it[8] if len(it) > 8 else "slam"
        anc = "left"
        if x >= 1000:
            anc, x = "right", 70 + (k % 3) * 30
        h, j = headline(f"{sid}-h{k}", txt, x, y, size, col, rot, p - p0, hold, kind=kind, anchor=anc)
        H.append(h); J.append(j)
    return "\n".join(H), "\n".join(J)


# ---------------------------------------------------------------- setiap babak
def w_frame(p0, p1):
    # meja kertas kraft + bingkai emas berlubang (bilik sebenar kelihatan di dalam) => frame break
    fx, fy, fw, fh = 300, 318, 1320, 700
    svg = (f'<defs><mask id="hole"><rect x="0" y="0" width="1920" height="1080" fill="#fff"/>'
           f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="6" fill="#000"/></mask></defs>'
           f'<g mask="url(#hole)">'
           f'<rect x="0" y="0" width="1920" height="1080" fill="#e9cf9b"/>'
           + "".join(f'<path d="{star(R.uniform(40,1880),R.uniform(30,1050),R.uniform(8,16),R.uniform(3,6))}" fill="{R.choice(["#f7b733","#fc4a1a","#4abdac","#ffffff"])}" opacity=".55"/>' for _ in range(40))
           + f'<rect x="{fx-34}" y="{fy-34}" width="{fw+68}" height="{fh+68}" rx="14" fill="#1a0f05" opacity=".3" transform="translate(8,12)"/>'
           f'<rect x="{fx-34}" y="{fy-34}" width="{fw+68}" height="{fh+68}" rx="14" fill="#c9962f"/>'
           f'<rect x="{fx-22}" y="{fy-22}" width="{fw+44}" height="{fh+44}" rx="10" fill="#f1cf6b"/>'
           f'<rect x="{fx-12}" y="{fy-12}" width="{fw+24}" height="{fh+24}" rx="8" fill="#8f6416"/>'
           + "".join(f'<path d="{circle(cx, cy, 16)}" fill="#fff1b8" stroke="#8f6416" stroke-width="4"/>' for cx, cy in [(fx-17, fy-17), (fx+fw+17, fy-17), (fx-17, fy+fh+17), (fx+fw+17, fy+fh+17)])
           + '</g>')
    html = ('<div id="wf-title" class="hl" style="left:960px;top:70px;font-size:96px;color:#fc4a1a;transform:translateX(-50%) rotate(-2deg);'
            'text-shadow:-4px -4px 0 #fff6e0,4px -4px 0 #fff6e0,-4px 4px 0 #fff6e0,4px 4px 0 #fff6e0,10px 13px 0 #2b1606;opacity:1">'
            '<span class="hand" style="font-family:Caveat;font-size:74px;color:#2b1606;text-shadow:none">once upon a time…</span></div>')
    cov, cov_js = photo("wf-cov", "book-cover.webp", 1690, 700, 190, 250, 7, 0.4, p1 - p0 - .6)
    js = ('tl.fromTo("#wf-title",{opacity:0,y:-30},{opacity:1,y:0,duration:.6,ease:"back.out(2)"},0.3);'
          'boil("#wf-title",1.6,.6,4,0,20);' + cov_js)
    return scene("w-frame", p0, p1, "none", svg, html + cov, js, bg="transparent", use_grain=False)


def workshop_svg(morning=False):
    wall = "#c98b4f" if not morning else "#e3a865"
    o = [f'<rect width="1920" height="1080" fill="{wall}"/>']
    for i in range(9):  # papan dinding
        o.append(f'<rect x="{i*215}" y="0" width="8" height="1080" fill="#9c6331" opacity=".55"/>')
    # tingkap
    o.append(shadowed(rect(1180, 120, 300, 260, 12), "#7a4a20"))
    o.append(f'<rect x="1196" y="136" width="268" height="228" rx="6" fill="{"#28346e" if not morning else "#9fd9f2"}"/>')
    if morning:
        o.append(f'<path d="{circle(1400,200,40)}" fill="#ffd34d"/>')
    else:
        o.append(f'<path d="{circle(1400,200,30)}" fill="#fff3c4"/>')
    o.append('<rect x="1326" y="136" width="10" height="228" fill="#7a4a20"/><rect x="1196" y="246" width="268" height="10" fill="#7a4a20"/>')
    # rak & barang
    for (y, x0, x1) in [(300, 60, 560), (520, 60, 560), (560, 1460, 1880)]:
        o.append(shadowed(rect(x0, y, x1 - x0, 22, 4), "#6e3f18"))
    for k, x in enumerate([90, 200, 330, 450]):  # jam
        o.append(shadowed(circle(x + 40, 255, 38), ["#f2d48b", "#e86a3a", "#6fb8a4", "#f7e2a8"][k]))
        o.append(f'<path id="hand{k}" d="M{x+40} 255 L{x+40} 228" stroke="#2b1606" stroke-width="6" stroke-linecap="round"/>')
    for k, x in enumerate([100, 230, 360, 470]):  # boneka kecil di rak bawah
        col = ["#e74c3c", "#3498db", "#f1c40f", "#9b59b6"][k]
        o.append(shadowed(circle(x + 25, 450, 22), "#f6d7b0"))
        o.append(shadowed(f"M{x} 520 L{x+25} 470 L{x+50} 520 Z", col))
    for k, x in enumerate([1500, 1620, 1740]):  # tin cat
        o.append(shadowed(rect(x, 480, 70, 80, 8), ["#e86a3a", "#4abdac", "#f7b733"][k]))
    # lantai & meja kerja di belakang
    o.append(shadowed(rect(-20, 860, 1960, 240), "#7c4a22", dy=-6))
    o.append(shadowed(rect(1250, 700, 640, 40, 6), "#8a5426"))
    o.append(shadowed(rect(1290, 740, 30, 160), "#6e3f18"))
    o.append(shadowed(rect(1820, 740, 30, 160), "#6e3f18"))
    # lampu gantung
    o.append('<g id="lamp"><path d="M960 0 L960 120" stroke="#2b1606" stroke-width="5"/>'
             + shadowed("M900 170 Q960 90 1020 170 Z", "#2f5d50") + '<ellipse cx="960" cy="178" rx="62" ry="12" fill="#ffe7a0"/></g>')
    if not morning:
        o.append('<ellipse id="glow" cx="960" cy="420" rx="520" ry="420" fill="#ffd27a" opacity=".16"/>')
    else:
        o.append('<path id="rays" d="M1330 250 L700 1080 L1100 1080 Z M1330 250 L1180 1080 L1500 1080 Z" fill="#fff4c2" opacity=".22"/>')
    return "".join(o)


def w_workshop(p0, p1):
    W = [("GEPPETTO", 19.3, 70, 560, 104, "#f7b733", -4, 4.2),
         ("PUPPETS!", 21.9, 1300, 600, 100, "#fc4a1a", 5, 3.6),
         ("I WISH…", 27.2, 90, 600, 104, "#ffffff", -3, 3.0),
         ("A REAL BOY", 29.6, 1240, 860, 98, "#4abdac", 3, 2.6)]
    h, j = words_js("w-workshop", W, p0)
    ph, pj = photo("ws-ph", "workshop.jpg", 1490, 70, 360, 220, 4, 20.5 - p0, p1 - p0 - .9)
    js = j + pj + ('tl.fromTo("#lamp",{rotation:-3,svgOrigin:"960 0"},{rotation:3,duration:1.6,ease:"steps(6)",yoyo:true,repeat:9},0);'
                   'tl.fromTo("#glow",{opacity:.1},{opacity:.2,duration:1.2,ease:"steps(4)",yoyo:true,repeat:13},0);'
                   + "".join(f'tl.fromTo("#hand{k}",{{rotation:0,svgOrigin:"{[130,240,370,490][k]} 255"}},{{rotation:360,duration:{6+k},ease:"steps(12)",repeat:2}},0);' for k in range(4)))
    return scene("w-workshop", p0, p1, "rip", workshop_svg(), h + ph, js)


def w_morning(p0, p1):
    W = [("HAPPY!", 54.4, 1290, 560, 130, "#f7b733", 6, 3.6),
         ("DANCE", 56.5, 120, 560, 112, "#fc4a1a", -6, 2.4, "drop"),
         ("& SING!", 57.9, 140, 690, 104, "#4abdac", -2, 1.6, "drop")]
    h, j = words_js("w-morning", W, p0)
    ph, pj = photo("mo-ph", "workshop.jpg", 1490, 70, 360, 220, -3, 0.5, p1 - p0 - .9, pos="60% 35%")
    js = j + pj + 'tl.fromTo("#rays",{opacity:.12},{opacity:.28,duration:1,ease:"steps(4)",yoyo:true,repeat:9},0);'
    return scene("w-morning", p0, p1, "slide-right", workshop_svg(True), h + ph, js)


def w_night(p0, p1):
    o = ['<rect width="1920" height="1080" fill="#14224f"/>',
         shadowed(hills(860, 50, 1.5, 2), "#1d3a6e"), shadowed(hills(930, 40, 2.2, 3), "#0f2550")]
    o.append(shadowed(circle(1650, 180, 90), "#fff3c4"))
    o.append(f'<path d="{circle(1690,160,80)}" fill="#14224f"/>')
    for i in range(46):
        o.append(f'<path class="tw" d="{star(R.uniform(30,1890),R.uniform(20,700),R.uniform(7,15),R.uniform(3,6))}" fill="#ffe9a8"/>')
    # rumah kecil
    o.append(shadowed(rect(130, 640, 330, 260), "#5a3a2a"))
    o.append(shadowed("M110 650 L295 500 L480 650 Z", "#8b2f2f"))
    o.append('<rect id="win" x="250" y="720" width="90" height="90" fill="#ffd27a"/>')
    o.append('<g id="fairy"><ellipse cx="1460" cy="420" rx="120" ry="120" fill="#7fd3ff" opacity=".18"/>'
             '<ellipse cx="1460" cy="420" rx="60" ry="60" fill="#bdeaff" opacity=".45"/>'
             f'<path d="{star(1460,420,34,13)}" fill="#ffffff"/></g>')
    W = [("THE FAIRY", 34.2, 80, 300, 110, "#7fd3ff", -4, 3.4),
         ("✦ MAGIC ✦", 38.3, 1220, 640, 96, "#f7b733", 4, 2.2),
         ("I CAN MOVE!", 40.3, 70, 520, 108, "#ffffff", -3, 2.6, "drop"),
         ("ONE DAY…", 43.7, 1230, 600, 100, "#7fd3ff", 3, 2.4),
         ("A REAL BOY", 46.0, 90, 600, 104, "#f7b733", -2, 2.6)]
    h, j = words_js("w-night", W, p0)
    ph, pj = photo("ni-ph", "fairy.jpg", 60, 60, 360, 240, -4, 35.0 - p0, p1 - p0 - .9, pos="75% 40%")
    js = j + pj + ('tl.fromTo(".tw",{opacity:1},{opacity:.35,duration:.5,ease:"steps(2)",yoyo:true,repeat:33,stagger:{each:.07,from:"random"}},0);'
                   'tl.fromTo("#fairy",{x:300,y:-120},{x:0,y:0,duration:2.4,ease:"steps(12)"},1.4);'
                   'tl.to("#fairy",{x:-40,y:20,duration:1.4,ease:"steps(6)",yoyo:true,repeat:9},3.8);')
    return scene("w-night", p0, p1, "slide-down", "".join(o), h + ph, js)


def w_road(p0, p1):
    o = ['<rect width="1920" height="1080" fill="#8fd3f4"/>',
         shadowed(circle(1650, 170, 85), "#ffd34d")]
    for k in range(4):
        cx = R.uniform(100, 1500); cy = R.uniform(80, 300)
        o.append(f'<g class="cloud">{shadowed(f"M{cx} {cy} a60 45 0 0 1 110 -20 a55 45 0 0 1 100 30 a45 35 0 0 1 -10 60 H{cx-20} a40 35 0 0 1 20 -70 Z", "#ffffff")}</g>')
    o.append(shadowed(hills(700, 60, 1.2, 7), "#7cc576"))
    o.append(shadowed(rect(1480, 470, 240, 190), "#e86a3a"))  # sekolah
    o.append(shadowed("M1460 480 L1600 380 L1740 480 Z", "#8b2f2f"))
    o.append('<rect x="1570" y="560" width="60" height="100" fill="#5a3a2a"/><rect x="1510" y="510" width="44" height="40" fill="#fff3c4"/><rect x="1646" y="510" width="44" height="40" fill="#fff3c4"/>')
    o.append(shadowed(hills(820, 45, 2.0, 8), "#5fae5a"))
    o.append(shadowed("M760 1080 Q900 900 1180 820 L1330 820 Q1100 920 1160 1080 Z", "#e8d3a0"))
    o.append(shadowed(hills(960, 30, 3.0, 9), "#4a9a4a"))
    html = '<img id="walker" src="assets/img/pinocchio.png" style="position:absolute;left:1400px;top:560px;height:250px"/>'
    W = [("TO SCHOOL!", 61.7, 90, 300, 116, "#fc4a1a", -4, 4.4)]
    h, j = words_js("w-road", W, p0)
    js = j + ('tl.fromTo(".cloud",{x:0},{x:180,duration:9,ease:"steps(30)"},0);'
              'tl.fromTo("#walker",{x:0},{x:-1250,duration:8.2,ease:"steps(40)"},0.2);'
              'tl.fromTo("#walker",{y:0},{y:-14,duration:.25,ease:"steps(2)",yoyo:true,repeat:31},0.2);')
    return scene("w-road", p0, p1, "slide-right", "".join(o), html + h, js)


def theater_svg(dark=False):
    o = [f'<rect width="1920" height="1080" fill="{"#2a0d14" if not dark else "#0b0610"}"/>']
    if not dark:
        for i in range(12):
            o.append(f'<path class="bulb" d="{circle(160 + i*145, 90, 13)}" fill="#ffd34d"/>')
    o.append(shadowed(rect(-20, 880, 1960, 220), "#6e3f18" if not dark else "#2a1a10", dy=-6))
    o.append('<ellipse id="spot" cx="960" cy="930" rx="520" ry="70" fill="#fff2c4" opacity="%s"/>' % (".35" if dark else ".22"))
    o.append('<path id="beam" d="M960 -40 L560 940 L1360 940 Z" fill="#fff2c4" opacity="%s"/>' % (".16" if dark else ".08"))
    if not dark:
        # langsir kiri & kanan berlipat
        for side in (0, 1):
            g = []
            for k in range(5):
                x = (k * 70) if side == 0 else (1920 - (k + 1) * 70)
                g.append(shadowed(f"M{x} -10 Q{x+35} 500 {x+10 if side==0 else x+60} 1090 L{x+70 if side==0 else x+70} 1090 Q{x+60} 500 {x+70} -10 Z", "#a3152b" if k % 2 else "#c21f37", dx=6 if side == 0 else -6))
            o.append(f'<g id="cur{side}">' + "".join(g) + "</g>")
        o.append(shadowed("M-20 -10 H1940 V120 Q1700 190 1440 120 Q1200 190 960 120 Q720 190 480 120 Q240 190 -20 120 Z", "#8c1024"))
        # boneka-boneka kecil tergantung (tali)
        for k, x in enumerate([420, 1500]):
            o.append(f'<g class="pup"><path d="M{x} 120 L{x} 380" stroke="#f2d48b" stroke-width="3"/>'
                     + shadowed(circle(x, 410, 30), "#f6d7b0") + shadowed(f"M{x-40} 520 L{x} 440 L{x+40} 520 Z", ["#3498db", "#f1c40f"][k]) + '</g>')
    return "".join(o)


def w_theater(p0, p1):
    W = [("PUPPET SHOW!", 67.7, 1180, 210, 92, "#f7b733", 4, 3.6),
         ("SING!", 69.5, 90, 520, 110, "#ffffff", -5, 1.8, "drop"),
         ("DANCE!", 70.4, 1330, 560, 110, "#4abdac", 5, 2.0, "drop"),
         ("STROMBOLI", 73.3, 70, 330, 110, "#fc4a1a", -3, 3.0),
         ("LOCKED!", 76.4, 1300, 600, 116, "#ffffff", 4, 3.4),
         ("JIMINY CRICKET", 80.1, 60, 720, 80, "#7cc576", -2, 2.6),
         ("THE FAIRY!", 82.3, 1270, 300, 96, "#7fd3ff", 3, 2.6)]
    h, j = words_js("w-theater", W, p0)
    js = j + ('tl.fromTo("#cur0",{x:620},{x:0,duration:.8,ease:"steps(8)"},0);'
              'tl.fromTo("#cur1",{x:-620},{x:0,duration:.8,ease:"steps(8)"},0);'
              'tl.fromTo(".bulb",{opacity:1},{opacity:.4,duration:.4,ease:"steps(2)",yoyo:true,repeat:47,stagger:{each:.1}},0);'
              'tl.fromTo(".pup",{rotation:-4,svgOrigin:"960 120"},{rotation:4,duration:.8,ease:"steps(4)",yoyo:true,repeat:23},0);')
    return scene("w-theater", p0, p1, "curtain", theater_svg(), h, js)


def w_spot(p0, p1):
    W = [("A LIE!", 87.3, 110, 400, 140, "#fc4a1a", -5, 2.6),
         ("BIGGER", 88.9, 1280, 560, 120, "#f7b733", 5, 3.2),
         ("& BIGGER!", 90.2, 90, 620, 120, "#ffffff", -4, 2.4),
         ("NEVER AGAIN!", 92.3, 1180, 260, 100, "#7fd3ff", 3, 3.4)]
    h, j = words_js("w-spot", W, p0)
    ph, pj = photo("sp-ph", "fairy.jpg", 70, 60, 330, 230, -5, 88.0 - p0, p1 - p0 - .9, pos="35% 40%")
    js = j + pj + 'tl.fromTo("#beam",{opacity:.1},{opacity:.22,duration:.5,ease:"steps(3)",yoyo:true,repeat:21},0);'
    return scene("w-spot", p0, p1, "fade", theater_svg(True), h + ph, js)


def w_theater2(p0, p1):
    W = [("✦ MAGIC ✦", 98.6, 1230, 260, 96, "#7fd3ff", 4, 2.4),
         ("THE CAGE OPENED!", 101.5, 70, 300, 84, "#f7b733", -3, 3.2),
         ("FREE!", 105.4, 1360, 600, 140, "#7cc576", 6, 1.8, "drop")]
    h, j = words_js("w-theater2", W, p0)
    ph, pj = photo("t2-ph", "fairy.jpg", 1480, 620, 340, 230, -4, 97.6 - p0, p1 - p0 - .9, pos="75% 40%")
    js = j + pj + ('tl.fromTo(".bulb",{opacity:1},{opacity:.4,duration:.4,ease:"steps(2)",yoyo:true,repeat:25,stagger:{each:.1}},0);'
                   'tl.fromTo(".pup",{rotation:-4,svgOrigin:"960 120"},{rotation:4,duration:.8,ease:"steps(4)",yoyo:true,repeat:13},0);')
    return scene("w-theater2", p0, p1, "fade", theater_svg(), h + ph, js)


def w_carnival(p0, p1):
    o = ['<rect width="1920" height="1080" fill="#3b1f5c"/>']
    for i in range(30):
        o.append(f'<path d="{star(R.uniform(30,1890),R.uniform(20,420),R.uniform(5,10),R.uniform(2,4))}" fill="#ffe9a8" opacity=".8"/>')
    # roda Ferris
    o.append('<g id="ferris">')
    o.append(f'<path d="{circle(1520,360,250)}" fill="none" stroke="#f7b733" stroke-width="14"/>')
    for k in range(12):
        ang = k * math.pi / 6
        x = 1520 + 250 * math.cos(ang); y = 360 + 250 * math.sin(ang)
        o.append(f'<path d="M1520 360 L{x:.0f} {y:.0f}" stroke="#f7b733" stroke-width="6"/>')
        o.append(f'<path d="{circle(round(x), round(y), 26)}" fill="{["#fc4a1a","#4abdac","#ffffff","#e84393"][k%4]}"/>')
    o.append('</g>')
    o.append(shadowed("M1460 360 L1360 900 L1400 900 L1520 400 L1640 900 L1680 900 L1580 360 Z", "#8e44ad"))
    # khemah berjalur
    for (x, w, h_, c1, c2) in [(60, 420, 360, "#fc4a1a", "#fff3c4"), (430, 320, 280, "#4abdac", "#fff3c4")]:
        stripes = "".join(f'<path d="M{x+w/2} {900-h_} L{x+i*w/6} 900 L{x+(i+1)*w/6} 900 Z" fill="{c1 if i%2 else c2}"/>' for i in range(6))
        o.append(f'<path d="M{x+w/2} {900-h_} L{x} 900 L{x+w} 900 Z" fill="#1a0f05" opacity=".3" transform="translate(6,9)"/>' + stripes)
        o.append(f'<path d="M{x+w/2} {900-h_-60} L{x+w/2} {900-h_} L{x+w/2+50} {900-h_-35} Z" fill="#f7b733"/>')
    # bendera rentang
    o.append('<path d="M-20 120 Q960 260 1940 120" stroke="#fff3c4" stroke-width="4" fill="none"/>')
    for k in range(20):
        x = k * 100 + 20; y = 120 + 140 * math.sin(math.pi * (x + 20) / 1960) * .95
        o.append(f'<path class="flag" d="M{x} {y:.0f} L{x+60} {y:.0f} L{x+30} {y+60:.0f} Z" fill="{["#fc4a1a","#f7b733","#4abdac","#e84393"][k%4]}"/>')
    o.append(shadowed(rect(-20, 880, 1960, 220), "#2b1340", dy=-6))
    W = [("SOME BOYS", 111.2, 1150, 650, 100, "#f7b733", 4, 2.8),
         ("LET'S PLAY!", 113.6, 70, 560, 104, "#4abdac", -4, 2.6),
         ("GO HOME NOW!", 116.4, 1130, 300, 92, "#ffffff", 3, 3.2),
         ("I LIKE HERE!", 123.7, 70, 300, 98, "#e84393", -3, 2.6),
         ("DONKEYS!", 128.5, 1210, 640, 126, "#f7b733", 5, 3.0),
         ("EARS & A TAIL", 132.2, 60, 640, 90, "#ffffff", -3, 2.4),
         ("RUN HOME!", 134.5, 1240, 300, 104, "#4abdac", 4, 3.4)]
    h, j = words_js("w-carnival", W, p0)
    js = j + ('tl.fromTo("#ferris",{rotation:0,svgOrigin:"1520 360"},{rotation:120,duration:31,ease:"steps(90)"},0);'
              'tl.fromTo(".flag",{rotation:-6,transformOrigin:"50% 0%"},{rotation:6,duration:.5,ease:"steps(2)",yoyo:true,repeat:61,stagger:.03},0);')
    return scene("w-carnival", p0, p1, "slide-up", "".join(o), h, js)


def sea_svg(storm=False):
    o = [f'<rect width="1920" height="1080" fill="{"#9fd9f2" if not storm else "#5d7fa8"}"/>']
    if not storm:
        o.append(shadowed(circle(320, 170, 80), "#ffd34d"))
    o.append('<g id="whale">' + shadowed("M1250 560 Q1300 380 1560 390 Q1780 400 1820 520 Q1880 470 1930 430 L1900 560 Q1860 640 1560 650 Q1300 650 1250 560 Z", "#3f5f8f")
             + f'<path d="{circle(1360,500,12)}" fill="#fff"/><path d="M1300 590 Q1380 620 1470 590" stroke="#1d2f4f" stroke-width="7" fill="none"/></g>')
    for k, (y, col) in enumerate([(640, "#3a8fd1"), (720, "#2c77b8"), (800, "#1f5f9a")]):
        o.append(f'<g class="wv wv{k}">' + shadowed(wave_path(y, 36, 14 - k * 2, 30 + k), col) + '</g>')
    return "".join(o)


def w_sea(p0, p1):
    # dinding headline "SWALLOWED BY A WHALE" (headline wall) pada 138.7–145
    rows = []
    for r in range(7):
        txt = " SWALLOWED BY A WHALE! ·" * 6
        rows.append(f'<div class="wallrow" id="wr{r}" style="position:absolute;left:-400px;top:{r*155-20}px;font-family:Archivo Black;font-size:118px;'
                    f'white-space:nowrap;color:{["#fff3c4","#f7b733"][r%2]};-webkit-text-stroke:3px #2b1606;opacity:.95">{txt}</div>')
    wall = f'<div id="wall" style="position:absolute;inset:0;background:#1f5f9a;opacity:0">{"".join(rows)}</div>'
    W = [("A LETTER!", 138.7, 80, 260, 100, "#fff3c4", -3, 1.4),
         ("FIND GEPPETTO!", 146.2, 60, 300, 92, "#fc4a1a", -3, 1.6),
         ("INTO THE SEA!", 148.1, 1180, 300, 92, "#ffffff", 3, 2.2)]
    h, j = words_js("w-sea", W, p0)
    t1 = 140.2 - p0; t2 = 145.0 - p0
    js = j + (f'tl.fromTo("#wall",{{opacity:0}},{{opacity:1,duration:.25,ease:"steps(2)"}},{t1:.2f});'
              + "".join(f'tl.fromTo("#wr{r}",{{x:{0 if r%2 else -600}}},{{x:{-600 if r%2 else 0},duration:{t2-t1+.4:.2f},ease:"none"}},{t1:.2f});' for r in range(7))
              + f'tl.to("#wall",{{opacity:0,duration:.3,ease:"steps(2)"}},{t2:.2f});'
              + ''.join(f'tl.fromTo(".wv{k}",{{x:0,y:0}},{{x:{30-k*20},y:{8+k*3},duration:.7,ease:"steps(3)",yoyo:true,repeat:17}},0);' for k in range(3))
              + 'tl.fromTo("#whale",{x:500},{x:0,duration:6,ease:"steps(20)"},4);')
    return scene("w-sea", p0, p1, "slide-down", sea_svg(), h + wall, js)


def w_belly(p0, p1):
    o = ['<rect width="1920" height="1080" fill="#2a0f1c"/>',
         '<ellipse cx="960" cy="560" rx="1100" ry="640" fill="#4a1a2e"/>']
    for k in range(9):  # tulang rusuk
        x = 120 + k * 210
        o.append(shadowed(f"M{x} -20 Q{x+90} 300 {x+20} 560 L{x+48} 560 Q{x+120} 300 {x+30} -20 Z", "#e8d8c0"))
    o.append(shadowed(wave_path(900, 18, 10, 77), "#1d4f6e", dy=-6))
    o.append(shadowed("M1380 860 L1820 860 L1760 940 L1440 940 Z", "#8a5426"))  # bot Geppetto
    o.append(f'<g id="fire">{shadowed("M1560 860 Q1540 780 1590 720 Q1600 790 1630 760 Q1660 820 1640 860 Z", "#fc4a1a")}'
             f'<path d="M1580 860 Q1575 810 1600 780 Q1610 820 1625 860 Z" fill="#f7b733"/></g>')
    W = [("GULP!", 151.9, 1250, 260, 150, "#f7b733", 5, 2.2),
         ("GEPPETTO!", 155.3, 80, 300, 116, "#fff3c4", -4, 2.8),
         ("FIRE!", 161.6, 110, 600, 140, "#fc4a1a", -5, 3.2)]
    h, j = words_js("w-belly", W, p0)
    js = j + (f'tl.fromTo("#fire",{{opacity:0,scale:.3,svgOrigin:"1600 860"}},{{opacity:1,scale:1,duration:.5,ease:"steps(4)"}},{160.8-p0:.2f});'
              f'tl.fromTo("#fire path",{{scaleY:.9,svgOrigin:"1600 860"}},{{scaleY:1.15,duration:.2,ease:"steps(2)",yoyo:true,repeat:30}},{161.3-p0:.2f});')
    return scene("w-belly", p0, p1, "iris", "".join(o), h, js)


def w_sea2(p0, p1):
    W = [("ESCAPE!", 172.9, 90, 300, 130, "#fff3c4", -4, 2.6),
         ("ANGRY WHALE!", 176.6, 70, 600, 100, "#fc4a1a", -3, 3.0),
         ("SWIM!", 180.3, 1340, 280, 130, "#ffffff", 5, 2.2),
         ("PULLED OUT!", 184.7, 90, 300, 104, "#f7b733", -3, 2.6),
         ("…FELL DOWN", 189.0, 1180, 300, 96, "#ffffff", 3, 1.4)]
    h, j = words_js("w-sea2", W, p0)
    js = j + (''.join(f'tl.fromTo(".wv{k}",{{x:0,y:0}},{{x:{40-k*25},y:{12+k*4},duration:.5,ease:"steps(3)",yoyo:true,repeat:45}},0);' for k in range(3))
              + f'tl.fromTo("#whale",{{x:0,rotation:0,svgOrigin:"1560 520"}},{{x:-120,rotation:-6,duration:.6,ease:"steps(3)",yoyo:true,repeat:19}},{176.1-p0:.2f});')
    return scene("w-sea2", p0, p1, "burst", sea_svg(True), h, js)


def w_home(p0, p1):
    o = ['<rect width="1920" height="1080" fill="#3a2a4f"/>']
    o.append(shadowed(rect(1180, 120, 300, 260, 12), "#7a4a20"))
    o.append('<rect x="1196" y="136" width="268" height="228" rx="6" fill="#14224f"/>')
    for i in range(10):
        o.append(f'<path d="{star(R.uniform(1205,1455),R.uniform(145,355),6,2.5)}" fill="#ffe9a8"/>')
    o.append('<path d="M-20 140 Q960 300 1940 140" stroke="#2b1606" stroke-width="3" fill="none"/>')
    for k in range(11):  # tanglung
        x = 60 + k * 180; y = 140 + 150 * math.sin(math.pi * (x + 20) / 1960) * .95
        o.append(f'<g class="lan">{shadowed(f"M{x-24} {y+10:.0f} h48 v50 h-48 Z", ["#f7b733","#fc4a1a","#4abdac"][k%3])}'
                 f'<ellipse cx="{x}" cy="{y+35:.0f}" rx="40" ry="40" fill="#ffd27a" opacity=".2"/></g>')
    o.append(shadowed(rect(-20, 870, 1960, 230), "#6e3f18", dy=-6))
    o.append('<g id="gold" opacity="0"><rect x="-1200" y="-1400" width="4320" height="3900" fill="#ffd27a" opacity=".55"/>'
             + "".join(f'<path d="M960 400 L{960+2600*math.cos(k*math.pi/9):.0f} {400+2600*math.sin(k*math.pi/9):.0f} L{960+2600*math.cos(k*math.pi/9+.12):.0f} {400+2600*math.sin(k*math.pi/9+.12):.0f} Z" fill="#fff6d0" opacity=".5"/>' for k in range(18))
             + '</g>')
    conf = "".join(f'<path class="conf" d="{rect(round(R.uniform(40,1880)), -40, 16, 26, 3)}" fill="{R.choice(["#fc4a1a","#f7b733","#4abdac","#e84393","#ffffff"])}"/>' for _ in range(60))
    o.append(f'<g id="confetti" opacity="0">{conf}</g>')
    W = [("BACK HOME", 191.3, 80, 300, 104, "#f7b733", -3, 3.4),
         ("✦ MAGIC ✦", 196.0, 1230, 280, 100, "#7fd3ff", 4, 3.0),
         ("HAPPY!", 205.0, 1300, 560, 140, "#f7b733", 5, 2.6),
         ("SANG", 207.8, 90, 520, 120, "#fc4a1a", -5, 1.6, "drop"),
         ("& DANCED", 209.0, 80, 660, 110, "#4abdac", -3, 2.6, "drop"),
         ("ALL NIGHT!", 210.4, 1220, 300, 104, "#ffffff", 3, 2.0)]
    h, j = words_js("w-home", W, p0)
    rb = 195.3 - p0
    js = j + (f'tl.fromTo("#gold",{{opacity:0}},{{opacity:1,duration:.5,ease:"steps(4)"}},{rb:.2f});'
              f'tl.fromTo("#gold",{{rotation:0,svgOrigin:"960 400"}},{{rotation:20,duration:6,ease:"steps(24)"}},{rb:.2f});'
              f'tl.to("#gold",{{opacity:0,duration:.6,ease:"steps(4)"}},{201.0-p0:.2f});'
              f'tl.fromTo("#confetti",{{opacity:0}},{{opacity:1,duration:.2}},{201.0-p0:.2f});'
              f'tl.fromTo(".conf",{{y:0,rotation:0}},{{y:1200,rotation:540,duration:4.5,ease:"steps(30)",stagger:{{each:.18,repeat:1}}}},{201.0-p0:.2f});'
              'tl.fromTo(".lan",{y:0},{y:-8,duration:.6,ease:"steps(3)",yoyo:true,repeat:35,stagger:.1},0);')
    return scene("w-home", p0, p1, "slide-right", "".join(o), h, js)


def w_moral(p0, p1):
    o = ['<rect width="1920" height="1080" fill="#f3e2b8"/>']
    for i in range(36):
        o.append(f'<path d="{star(R.uniform(30,1890),R.uniform(20,1060),R.uniform(8,16),R.uniform(3,6))}" fill="{R.choice(["#f7b733","#fc4a1a","#4abdac"])}" opacity=".35"/>')
    o.append(shadowed(rect(-20, 900, 1960, 200), "#d9b878", dy=-6))
    html = ('<div id="mo-title" class="hl" style="left:960px;top:52px;font-size:84px;color:#2c4f9e;opacity:0;'
            'text-shadow:-3px -3px 0 #fff6e0,3px -3px 0 #fff6e0,-3px 3px 0 #fff6e0,3px 3px 0 #fff6e0,9px 12px 0 #2b1606">'
            '<div style="transform:translateX(-50%) rotate(-2deg)">MORAL OF THE STORY</div></div>')
    W = [("BE HONEST", 217.1, 70, 300, 104, "#fc4a1a", -4, 15.6),
         ("LISTEN TO", 221.0, 1300, 300, 88, "#2c4f9e", 4, 11.7),
         ("GOOD ADVICE", 221.6, 1250, 410, 88, "#2c4f9e", 3, 11.1),
         ("LOVE OUR", 225.3, 80, 560, 96, "#e84393", -3, 7.4),
         ("FAMILY", 226.4, 120, 670, 104, "#e84393", -2, 6.3),
         ("LEARN FROM", 228.9, 1270, 560, 86, "#2a9d8f", 3, 3.8),
         ("OUR MISTAKES", 230.6, 1230, 670, 86, "#2a9d8f", 2, 2.1)]
    h, j = words_js("w-moral", W, p0)
    js = j + ('tl.fromTo("#mo-title",{opacity:0,y:-40},{opacity:1,y:0,duration:.5,ease:"back.out(2)"},0.6);'
              'boil("#mo-title",1.6,.6,9,0.6,30);'
              # buku ditutup: dunia kertas melipat (rotateY) mendedahkan bilik sebenar
              f'tl.to("#scene",{{rotationY:-92,transformOrigin:"0% 50%",transformPerspective:2200,duration:.9,ease:"power2.in"}},{233.0-p0:.2f});')
    return scene("w-moral", p0, p1, "rip", "".join(o), html + h, js)


BUILDERS = {"w-frame": w_frame, "w-workshop": w_workshop, "w-night": w_night, "w-morning": w_morning, "w-road": w_road,
            "w-theater": w_theater, "w-spot": w_spot, "w-theater2": w_theater2, "w-carnival": w_carnival, "w-sea": w_sea,
            "w-belly": w_belly, "w-sea2": w_sea2, "w-home": w_home, "w-moral": w_moral}


# ============================================================ FRONT: doodle & slam
def load_track():
    if os.path.exists(TRACK):
        return json.load(open(TRACK))
    return None


def track_at(tr, p):
    """kedudukan kepala (cx, top, h) pada masa rakaman p"""
    if not tr:
        return 960, 260, 200
    i = min(len(tr["t"]) - 1, max(0, int(round(p * tr["hz"]))))
    return tr["cx"][i], tr["top"][i], tr["hh"][i]


def follow_js(el, p0, p1, tr, dx=0, dy=0, tl="tl"):
    """GSAP keyframes supaya doodle ikut kepala (kemaskini 10 Hz, ease steps => rasa stop-motion)"""
    if not tr:
        return ""
    ks = []
    p = p0
    while p <= p1:
        cx, top, hh_ = track_at(tr, p)
        ks.append((p - p0, cx + dx, top + dy))
        p += 0.1
    js = f'tl.set("{el}",{{x:{ks[0][1]:.0f},y:{ks[0][2]:.0f}}},0);'
    for k in range(1, len(ks)):
        js += f'tl.set("{el}",{{x:{ks[k][1]:.0f},y:{ks[k][2]:.0f}}},{ks[k][0]:.2f});'
    return js


def doodle_scene(sid, p0, p1, svg_inner, w, h, follow=None, extra_html="", extra_js="", stroke="#fff6e0"):
    """doodle tangan (boil) - kotak SVG w x h, diletak mengikut kepala (follow=(dx,dy)) atau tetap"""
    dur = round(p1 - p0, 3)
    tr = load_track()
    pos_js = follow_js(f"#{sid}-pos", 0 + p0, p1, tr, *follow) if follow else ""
    # follow_js guna masa relatif dari p0
    pos_js = pos_js.replace("},0);", "},0);", 1)
    body = f'''<template>
<style>{FONTS}{CSS}
#{sid}-pos{{position:absolute;left:0;top:0;width:{w}px;height:{h}px;margin-left:-{w//2}px;}}
#{sid}-pos path{{fill:none;stroke:{stroke};stroke-width:9;stroke-linecap:round;stroke-linejoin:round;}}
#{sid}-pos .ink{{stroke:#2b1606;stroke-width:17;}}
</style>
<div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">
<div id="{sid}-pos"><div id="{sid}-w" style="position:absolute;inset:0;opacity:0"><div id="{sid}-b" style="position:absolute;inset:0">
<svg viewBox="0 0 {w} {h}" style="position:absolute;inset:0;width:{w}px;height:{h}px;overflow:visible">{svg_inner}</svg>
</div></div></div>
{extra_html}
</div>
<script>
const tl = gsap.timeline({{paused:true}});
{BOIL_JS}
{pos_js}
tl.fromTo("#{sid}-w",{{opacity:0,scale:.4}},{{opacity:1,scale:1,duration:.35,ease:"back.out(2.4)"}},0);
boil("#{sid}-b",2.6,1.2,{abs(hash(sid))%50+1},0,{dur});
{extra_js}
tl.to("#{sid}-w",{{opacity:0,duration:.3}},{dur-0.35:.2f});
window.__timelines["{sid}"] = tl;
</script>
</template>'''
    write(sid, body)
    return dur


def ink(d):
    """garis doodle: garis gelap tebal di bawah + garis cerah"""
    return f'<path class="ink" d="{d}"/><path d="{d}"/>'


def slam_scene(sid, p0, dur, text, x, y, size, color, rot, shake=False):
    h, j = headline(f"{sid}-t", text, x, y, size, color, rot, 0.0, dur - .6, anchor="center")
    js = j
    if shake:
        js += f'tl.fromTo("#{sid}-t",{{x:-14}},{{x:14,duration:.05,ease:"steps(1)",yoyo:true,repeat:9}},.3);'
    body = f'''<template>
<style>{FONTS}{CSS}</style>
<div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">{h}</div>
<script>
const tl = gsap.timeline({{paused:true}});
{BOIL_JS}
{js}
window.__timelines["{sid}"] = tl;
</script>
</template>'''
    write(sid, body)
    return dur


def front_scenes():
    tr = load_track()
    S = []
    # headline slam di bahagian atas (tidak menutup muka)
    for sid, p, dur, txt, x, y, size, col, rot, shake in [
        ("f-pin", 14.8, 1.6, "PINOCCHIO!", 960, 60, 150, "#fc4a1a", -3, False),
        ("f-no", 120.8, 1.5, "NO!", 1560, 120, 200, "#fc4a1a", 6, True),
        ("f-splash", 149.6, 1.4, "SPLASH!", 960, 50, 170, "#7fd3ff", -3, False),
        ("f-achoo", 167.1, 1.9, "ACHOO!", 960, 40, 210, "#f7b733", -4, True),
        ("f-real", 199.4, 2.2, "A REAL BOY!", 960, 50, 150, "#f7b733", -2, False),
    ]:
        S.append((sid, a(p), slam_scene(sid, p, dur, txt, x, y, size, col, rot, shake)))
    # doodle: hidung memanjang (ikut kepala)
    nose = (ink("M20 60 Q60 40 110 52") + ink("M110 52 L 380 50") + ink("M110 70 L380 62") + ink("M380 50 Q400 56 380 62"))
    nj = 'tl.fromTo("#nose-grow",{scaleX:.25,transformOrigin:"0% 50%"},{scaleX:.55,duration:.3,ease:"steps(2)"},0.6);' \
         'tl.to("#nose-grow",{scaleX:.85,duration:.3,ease:"steps(2)"},1.6);tl.to("#nose-grow",{scaleX:1.15,duration:.3,ease:"steps(2)"},2.6);'
    S.append(("d-nose", a(87.6), doodle_scene("d-nose", 87.6, 96.4, f'<g id="nose-grow">{nose}</g>', 420, 120,
                                               follow=(150, 120), extra_js=nj)))
    # telinga & ekor keldai
    ears = ink("M70 230 Q20 90 60 10 Q110 90 120 220") + ink("M240 220 Q250 90 300 10 Q340 90 290 230")
    S.append(("d-ears", a(131.4), doodle_scene("d-ears", 131.4, 136.2, ears, 360, 260, follow=(0, -160))))
    # sangkar di sekeliling murid (bar di sisi & atas, bukan di muka)
    bars = "".join(ink(f"M{x} 40 L{x} 900") for x in (40, 110, 180, 980, 1050, 1120)) + ink("M40 40 Q580 -140 1120 40") + ink("M40 900 L1120 900")
    S.append(("d-cage", a(76.6), doodle_scene("d-cage", 76.6, 101.9, bars, 1160, 940, follow=(0, -120),
                                               extra_js='tl.to("#d-cage-b",{y:-900,rotation:12,opacity:0,duration:.8,ease:"power2.in"},' + f'{101.9-76.6-1.0:.2f});')))
    # not muzik & bintang (tetap, di sisi)
    notes = (ink("M40 160 L40 40 L120 20 L120 140") + ink(f"M{20} 160 a20 15 0 1 0 40 0 a20 15 0 1 0 -40 0") + ink("M100 140 a20 15 0 1 0 40 0 a20 15 0 1 0 -40 0")
             + ink("M260 120 L260 20") + ink("M240 120 a20 15 0 1 0 40 0 a20 15 0 1 0 -40 0") + ink("M260 20 Q300 40 290 80"))
    for sid, p0, p1, x, y in [("d-notes1", 55.8, 59.0, 1450, 300), ("d-notes2", 207.0, 212.3, 300, 250)]:
        S.append((sid, a(p0), doodle_scene(sid, p0, p1, notes, 320, 200, extra_js=f'tl.set("#{sid}-pos",{{x:{x},y:{y}}},0);')))
    sparkle = "".join(ink(f"M{cx} {cy-30} L{cx} {cy+30} M{cx-30} {cy} L{cx+30} {cy} M{cx-18} {cy-18} L{cx+18} {cy+18} M{cx-18} {cy+18} L{cx+18} {cy-18}") for cx, cy in [(60, 60), (200, 140), (110, 230)])
    for sid, p0, p1 in [("d-wand", 38.2, 41.0), ("d-magic", 195.8, 200.6), ("d-happy", 53.6, 55.6)]:
        S.append((sid, a(p0), doodle_scene(sid, p0, p1, sparkle, 260, 280, follow=(230, -60))))
    # ombak depan semasa babak laut (menutup hujung bawah)
    for sid, p0, p1 in [("f-wave1", 148.0, 151.0), ("f-wave2", 167.9, 190.6)]:
        dur = round(p1 - p0, 3)
        body = f'''<template><style>{CSS}</style>
<div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">
<div id="{sid}-g" class="L" style="opacity:0"><svg viewBox="0 0 1920 1080">{shadowed(wave_path(985, 34, 9, 91), "#2c77b8", dy=-8)}</svg></div></div>
<script>const tl = gsap.timeline({{paused:true}});
tl.fromTo("#{sid}-g",{{opacity:0,y:120}},{{opacity:1,y:0,duration:.5,ease:"steps(4)"}},0);
tl.fromTo("#{sid}-g",{{x:0}},{{x:-60,duration:.5,ease:"steps(3)",yoyo:true,repeat:{int(dur/.5)-2}}},.5);
tl.to("#{sid}-g",{{opacity:0,y:120,duration:.4,ease:"steps(3)"}},{dur-.45:.2f});
window.__timelines["{sid}"] = tl;</script></template>'''
        write(sid, body)
        S.append((sid, a(p0), dur))
    return S


# ============================================================ root
def build(mode):
    os.makedirs(os.path.join(HF, "assets", "img"), exist_ok=True)
    back, front = [], []
    if mode in ("preview", "back"):
        for sid, p0, p1, ent in WORLD:
            back.append((sid, a(p0), BUILDERS[sid](p0, p1)))
    if mode in ("preview", "front"):
        front.append(("opening", 0, v1.opening()))
        front.append(("nameplate", a(4.2), v1.lowerthird(4.2, 11.2)))
        front += front_scenes()
        front.append(("closing", round(T0 + PERF, 3), v1.closing()))
    hosts = []
    z = 10
    for sid, st, du in back:
        hosts.append(f'<div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{st}" data-duration="{du}" data-track-index="2" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index:{z}"></div>'); z += 1
    media = ""
    if mode == "preview":
        cutv = os.path.exists(os.path.join(HF, "assets", "footage", "cut_preview.webm"))
        media = (f'<video id="perf" class="clip" src="assets/footage/performance.mp4" data-start="{T0}" data-duration="{PERF}" data-track-index="1" muted playsinline style="position:absolute;left:0;top:0;width:1920px;height:1080px;z-index:2"></video>'
                 f'<video id="cutv" class="clip" src="assets/footage/cut_preview.webm" data-start="{T0}" data-duration="{PERF}" data-track-index="3" muted playsinline style="position:absolute;left:0;top:0;width:1920px;height:1080px;z-index:40"></video>' if cutv else '')
        media += (f'<audio id="mix" class="clip" src="assets/audio/mix.wav" data-start="0" data-duration="{TOTAL}" data-track-index="20" data-volume="1"></audio>')
    z = 60
    for sid, st, du in front:
        hosts.append(f'<div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{st}" data-duration="{du}" data-track-index="4" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index:{z}"></div>'); z += 1
    html = f'''<!doctype html>
<html lang="en"><head><meta charset="UTF-8"/><meta name="viewport" content="width=1920, height=1080"/>
<script src="assets/vendor/gsap.min.js"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box;}}html,body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:{"#000" if mode=="preview" else "transparent"};}}#root{{position:absolute;inset:0;}}</style>
</head><body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
{media}
{chr(10).join(hosts)}
</div>
<script>window.__timelines=window.__timelines||{{}};window.__timelines["main"]=gsap.timeline({{paused:true}});</script>
</body></html>'''
    open(os.path.join(HF, "index.html"), "w").write(html)
    print(mode, "ok", len(back), "back", len(front), "front")


# ============================================================ penjejakan kepala
def track():
    """baca alfa potongan pada 10 Hz -> bahagian atas kepala & pusat muka"""
    import numpy as np
    hz = 10
    w, h = 480, 270
    cmd = ["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", CUT, "-vf", f"fps={hz},scale={w}:{h},alphaextract,format=gray",
           "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, check=True, capture_output=True).stdout
    n = len(raw) // (w * h)
    A = np.frombuffer(raw[: n * w * h], dtype=np.uint8).reshape(n, h, w)
    T, CX, TOP, HH = [], [], [], []
    last = (960, 260, 200)
    for i in range(n):
        m = A[i] > 128
        rows = np.where(m.sum(1) > 3)[0]
        if len(rows) == 0:
            cx, top, hh_ = last
        else:
            top = rows[0]
            band = m[top: top + 40]  # kepala + topi (~160 px skala penuh)
            cols = np.where(band.sum(0) > 2)[0]
            cx = (cols.min() + cols.max()) / 2 if len(cols) else last[0] / 4
            # lebar kepala sebagai anggaran saiz
            hh_ = (cols.max() - cols.min()) if len(cols) else last[2] / 4
            cx, top, hh_ = cx * 4, top * 4, hh_ * 4
        T.append(i / hz); CX.append(float(cx)); TOP.append(float(top)); HH.append(float(hh_))
        last = (cx, top, hh_)
    # licinkan (median 5)
    def smooth(v):
        v = np.array(v); out = v.copy()
        for i in range(len(v)):
            out[i] = np.median(v[max(0, i - 2): i + 3])
        return [round(float(x), 1) for x in out]
    json.dump({"hz": hz, "t": T, "cx": smooth(CX), "top": smooth(TOP), "hh": smooth(HH)}, open(TRACK, "w"))
    print("track ok", n)


# ============================================================ eksport akhir
def final(back_mov, front_mov, out):
    grade = open(os.path.join(HERE, "grade.txt")).read().strip()
    g_novig = ",".join(f for f in grade.split(",") if not f.startswith("vignette"))
    crf = os.environ.get("CRF", "18")
    pad = f"tpad=start_duration={T0}:start_mode=clone:stop_duration={CLOSE+0.5}:stop_mode=clone"
    # potongan: gred sama (tanpa vignet) + garis putih pelekat 7 px + bayang lembut
    fc = (
        f"[0:v]{g_novig},fps=60,{pad},trim=0:{TOTAL},setpts=PTS-STARTPTS[base];"
        f"[1:v]fps=60,format=yuva444p,setpts=PTS-STARTPTS[back];"
        f"[2:v]format=yuva444p,{g_novig.replace('hqdn3d=1.2:1.2:2.5:2.5,','')},fps=60,{pad.replace('clone','black')},trim=0:{TOTAL},setpts=PTS-STARTPTS,split=3[c0][c1][c2];"
        # alfa: buang sisa kecil & lembutkan
        f"[c1]alphaextract,dilation,dilation,dilation,dilation,dilation,dilation,dilation,gblur=sigma=1.2,lut=y='if(gt(val,90),255,0)',gblur=sigma=0.8[olA];"
        f"color=c=white:s=1920x1080:r=60:d={TOTAL}[ow];[ow][olA]alphamerge[outline];"
        f"[c2]alphaextract,dilation,dilation,dilation,gblur=sigma=10,lut=y='val*0.45'[shA];"
        f"color=c=0x1a0f05:s=1920x1080:r=60:d={TOTAL}[sc];[sc][shA]alphamerge[shadow];"
        # garis & bayang hanya semasa dunia kertas (selepas koyakan); bingkai pada 0–15.9 tanpa garis
        f"[base][back]overlay=0:0:format=auto[b1];"
        f"[b1][shadow]overlay=10:14:format=auto:enable='between(t,{a(15.4)},{a(233.6)})'[b2];"
        f"[b2][outline]overlay=0:0:format=auto:enable='between(t,{a(15.4)},{a(233.6)})'[b3];"
        f"[b3][c0]overlay=0:0:format=auto:enable='between(t,{T0},{T0+PERF})'[b4];"
        f"[3:v]fps=60,format=yuva444p,setpts=PTS-STARTPTS[front];"
        f"[b4][front]overlay=0:0:format=auto,vignette=angle=PI/7:mode=forward,format=yuv420p[vout]"
    )
    cmd = ["ffmpeg", "-v", "error", "-stats", "-y", "-i", SRC, "-i", back_mov, "-c:v", "libvpx-vp9", "-i", CUT, "-i", front_mov,
           "-i", os.path.join(HERE, "work", "mix.wav"),
           "-filter_complex", fc, "-map", "[vout]", "-map", "4:a",
           "-c:v", "libx264", "-preset", "medium", "-crf", crf, "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "60",
           "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-t", str(TOTAL), out]
    subprocess.run(cmd, check=True)
    print("final ok", out)


if __name__ == "__main__":
    w = sys.argv[1]
    if w in ("preview", "back", "front"):
        build(w)
    elif w == "track":
        track()
    elif w == "final":
        final(sys.argv[2], sys.argv[3], sys.argv[4])
