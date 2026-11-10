"""Penjana projek HyperFrames + campuran audio + eksport akhir untuk video bercerita PINOCCHIO.

  python3 build.py hf            # tulis hf/index.html + hf/compositions/*.html (pratonton, dengan rakaman)
  python3 build.py hf --overlay  # sama, tetapi rakaman/audio disembunyikan -> render lapisan lutsinar
  python3 build.py mix           # work/mix.wav + hf/assets/audio/mix.wav
  python3 build.py final         # gabung lapisan lutsinar atas rakaman asal 60 fps + mix.wav -> renders/

Peraturan: rakaman asal dimainkan penuh dan berterusan (tiada potongan). Semua grafik ialah tindanan.
Masa dalam CONFIG ialah masa rakaman asal (p); masa video = p + T0.
"""
import json, os, random, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
HF = os.path.join(HERE, "hf")
SRC = os.path.join(HERE, "sumber", "FIRASH_MIKAEL.mp4")

T0 = 6.0                 # pembuka
PERF = 237.48            # panjang rakaman asal
CLOSE = 5.0              # penutup
TOTAL = round(T0 + PERF + CLOSE, 2)

NAME1, NAME2 = "FIRASH MIKAEL", "BIN MOHD FAHMI ASYRAF"
CLASS = "CLASS : 2 IBNU ABBAS"
SCHOOL = "SK TOK JIRING"

CFG = json.load(open(os.path.join(HERE, "timing.json")))

# kedudukan bingkai buku cerita (kanan bawah, jauh dari murid & gerak tangan)
FX, FY, FW, FH = 1384, 596, 508, 382

rnd = random.Random(11)


def a(p):
    """masa rakaman -> masa video"""
    return round(p + T0, 3)


HEAD = """<template>
<style>
#root{position:absolute;inset:0;}
.serif{font-family:'Playfair Display',serif;}
.garamond{font-family:'EB Garamond',serif;}
.gold{color:#f2d48b;}
.spark{position:absolute;width:7px;height:7px;border-radius:50%;
  background:#fff1bf;
  box-shadow:0 0 8px 3px rgba(255,214,120,.6);opacity:0;}
.frame{position:absolute;left:%FX%px;top:%FY%px;width:%FW%px;height:%FH%px;opacity:0;}
.mat{position:absolute;inset:0;border-radius:18px;
  background:linear-gradient(160deg,#173273 0%,#0b1a45 100%);
  box-shadow:0 0 0 2px #e2bf68,0 0 0 6px rgba(9,20,52,.9),0 0 0 7.5px rgba(226,191,104,.65),
   0 0 42px 8px rgba(255,205,110,.32),0 20px 44px rgba(0,0,0,.45);}
.pages{position:absolute;left:13px;top:13px;right:13px;bottom:13px;perspective:1600px;}
.page{position:absolute;inset:0;border-radius:9px;overflow:hidden;transform-origin:0% 50%;background:#0b1838;}
.page img.fill{position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover;}
.shade{position:absolute;inset:0;background:linear-gradient(90deg,rgba(0,0,0,.0),rgba(0,0,0,.55));opacity:0;}
.glint{position:absolute;top:-20%;left:-60%;width:40%;height:140%;
  background:linear-gradient(100deg,rgba(255,255,255,0),rgba(255,240,200,.38),rgba(255,255,255,0));opacity:0;}
.parch{background:radial-gradient(ellipse at 50% 40%,#fbf0d2 0%,#f0dcaa 60%,#d9bd82 100%);}
.corner{position:absolute;width:26px;height:26px;border-color:#e2bf68;border-style:solid;opacity:.9;}
</style>
""".replace("%FX%", str(FX)).replace("%FY%", str(FY)).replace("%FW%", str(FW)).replace("%FH%", str(FH))


def sparks(prefix, cx, cy, spread, n, t, tl, size=1.0):
    """percikan cahaya keemasan di sekitar (cx,cy) pada masa t (masa scene)."""
    html, js = [], []
    for i in range(n):
        x = cx + rnd.uniform(-spread[0], spread[0]); y = cy + rnd.uniform(-spread[1], spread[1])
        dx = rnd.uniform(-40, 40); dy = rnd.uniform(-70, -25); d = rnd.uniform(0, .5)
        s = rnd.uniform(.6, 1.4) * size
        sid = f"{prefix}{i}"
        html.append(f'<div id="{sid}" class="spark" style="left:{x:.0f}px;top:{y:.0f}px"></div>')
        js.append(f'{tl}.fromTo("#{sid}",{{opacity:0,scale:.2,x:0,y:0}},{{opacity:1,scale:{s:.2f},x:{dx*.4:.0f},y:{dy*.4:.0f},duration:.45,ease:"power2.out"}},{t+d:.2f});'
                  f'{tl}.to("#{sid}",{{opacity:0,x:{dx:.0f},y:{dy:.0f},duration:1.1,ease:"power1.in"}},{t+d+.45:.2f});')
    return "\n".join(html), "\n".join(js)


def corners(prefix):
    o = []
    for k, (h, v) in enumerate([("left", "top"), ("right", "top"), ("left", "bottom"), ("right", "bottom")]):
        bw = f"border-{v}-width:2px;border-{h}-width:2px;border-{'bottom' if v=='top' else 'top'}-width:0;border-{'right' if h=='left' else 'left'}-width:0;"
        o.append(f'<div class="corner" style="{h}:-3px;{v}:-3px;{bw}"></div>')
    return "".join(o)


def write(name, body):
    os.makedirs(os.path.join(HF, "compositions"), exist_ok=True)
    open(os.path.join(HF, "compositions", f"{name}.html"), "w").write(body)


# ---------------------------------------------------------------- latar ajaib (pembuka & penutup)
def magic_bg(prefix, dur, tl):
    html = [f'''<div id="{prefix}-bg" style="position:absolute;inset:0;background:radial-gradient(ellipse at 50% 42%,#1f4597 0%,#0f2861 34%,#071437 70%,#030819 100%);"></div>
<div id="{prefix}-glow" style="position:absolute;left:460px;top:-260px;width:1000px;height:760px;border-radius:50%;background:radial-gradient(circle,rgba(255,206,120,.30) 0%,rgba(255,190,90,.10) 45%,rgba(255,190,90,0) 70%);"></div>''']
    js = [f'{tl}.fromTo("#{prefix}-glow",{{opacity:.55,scale:.96}},{{opacity:1,scale:1.04,duration:{dur/2:.2f},ease:"sine.inOut",yoyo:true,repeat:1}},0);']
    # bintang statik berkelip
    for i in range(70):
        x = rnd.uniform(20, 1900); y = rnd.uniform(20, 1060); s = rnd.choice([2, 2, 3, 3, 4])
        c = rnd.choice(["#ffffff", "#fff3c4", "#ffe08a"]); o = rnd.uniform(.25, .7)
        html.append(f'<div id="{prefix}-st{i}" style="position:absolute;left:{x:.0f}px;top:{y:.0f}px;width:{s}px;height:{s}px;border-radius:50%;background:{c};box-shadow:0 0 6px {c};opacity:{o:.2f}"></div>')
        tw = rnd.uniform(.8, 1.8)
        js.append(f'{tl}.to("#{prefix}-st{i}",{{opacity:{o*.25:.2f},duration:{tw:.2f},ease:"sine.inOut",yoyo:true,repeat:{int(dur/tw/2)*2+1}}},{rnd.uniform(0,1):.2f});')
    # zarah emas terapung naik
    for i in range(40):
        x = rnd.uniform(60, 1860); y = rnd.uniform(300, 1120); s = rnd.uniform(4, 10)
        html.append(f'<div id="{prefix}-pt{i}" class="spark" style="left:{x:.0f}px;top:{y:.0f}px;width:{s:.1f}px;height:{s:.1f}px"></div>')
        d0 = rnd.uniform(0, 1.5); rise = rnd.uniform(120, 320); drift = rnd.uniform(-60, 60)
        js.append(f'{tl}.fromTo("#{prefix}-pt{i}",{{opacity:0,x:0,y:0}},{{opacity:{rnd.uniform(.45,.95):.2f},x:{drift*.3:.0f},y:{-rise*.25:.0f},duration:1.2,ease:"sine.out"}},{d0:.2f});'
                  f'{tl}.to("#{prefix}-pt{i}",{{x:{drift:.0f},y:{-rise:.0f},opacity:0,duration:{dur-d0-1.3:.2f},ease:"sine.inOut"}},{d0+1.2:.2f});')
    return "\n".join(html), "\n".join(js)


def ornament(oid, y, w=520):
    return (f'<div id="{oid}" style="position:absolute;left:{960-w//2}px;top:{y}px;width:{w}px;height:14px;">'
            f'<div style="position:absolute;left:0;top:6px;width:{w//2-18}px;height:1.5px;background:linear-gradient(90deg,rgba(226,191,104,0),#e2bf68);"></div>'
            f'<div style="position:absolute;left:{w//2-6}px;top:1px;width:12px;height:12px;background:#f2d48b;transform:rotate(45deg);box-shadow:0 0 10px rgba(255,214,120,.8)"></div>'
            f'<div style="position:absolute;right:0;top:6px;width:{w//2-18}px;height:1.5px;background:linear-gradient(90deg,#e2bf68,rgba(226,191,104,0));"></div></div>')


TXT_GLOW = "text-shadow:0 0 22px rgba(255,212,128,.45),0 2px 6px rgba(0,0,0,.5);"


def opening():
    dur = T0 + 0.6
    bg, bgjs = magic_bg("op", dur, "tl")
    sp, spjs = sparks("op-sp", 960, 250, (380, 40), 22, 2.5, "tl", 1.3)
    letters = "".join(f'<span id="op-l{i}" style="display:inline-block">{c}</span>' for i, c in enumerate("PINOCCHIO"))
    body = HEAD + f'''<div id="root" data-composition-id="opening" data-width="1920" data-height="1080">
<div id="op-all" style="position:absolute;inset:0;">
{bg}
<div id="op-title" class="serif" style="position:absolute;left:0;width:1920px;top:188px;text-align:center;font-size:62px;font-weight:700;letter-spacing:.34em;padding-left:.34em;color:#f2d48b;{TXT_GLOW}">{letters}</div>
{ornament("op-orn1", 290)}
<div id="op-n1" class="serif" style="position:absolute;left:0;width:1920px;top:356px;text-align:center;font-size:96px;font-weight:900;color:#fff6dc;letter-spacing:.02em;{TXT_GLOW}">{NAME1}</div>
<div id="op-n2" class="serif" style="position:absolute;left:0;width:1920px;top:478px;text-align:center;font-size:56px;font-weight:700;color:#fff6dc;letter-spacing:.04em;{TXT_GLOW}">{NAME2}</div>
{ornament("op-orn2", 586, 300)}
<div id="op-cl" class="serif" style="position:absolute;left:0;width:1920px;top:632px;text-align:center;font-size:42px;font-weight:700;color:#f2d48b;letter-spacing:.08em;{TXT_GLOW}">{CLASS}</div>
<div id="op-sc" class="serif" style="position:absolute;left:0;width:1920px;top:708px;text-align:center;font-size:32px;font-weight:400;color:#f7ecd0;letter-spacing:.3em;padding-left:.3em;{TXT_GLOW}">{SCHOOL}</div>
{sp}
</div>
</div>
<script>
const tl = gsap.timeline({{paused:true}});
{bgjs}
tl.fromTo("#op-n1",{{opacity:0,y:18,filter:"blur(10px)"}},{{opacity:1,y:0,filter:"blur(0px)",duration:1.0,ease:"power2.out"}},0.35);
tl.fromTo("#op-n2",{{opacity:0,y:14,filter:"blur(8px)"}},{{opacity:1,y:0,filter:"blur(0px)",duration:.9,ease:"power2.out"}},0.75);
tl.fromTo("#op-orn2",{{opacity:0,scaleX:0}},{{opacity:1,scaleX:1,duration:.8,ease:"power2.out"}},1.15);
tl.fromTo("#op-cl",{{opacity:0,y:12}},{{opacity:1,y:0,duration:.7,ease:"power2.out"}},1.3);
tl.fromTo("#op-sc",{{opacity:0,y:12}},{{opacity:1,y:0,duration:.7,ease:"power2.out"}},1.65);
''' + "\n".join(f'tl.fromTo("#op-l{i}",{{opacity:0,y:-26,scale:1.25,filter:"blur(6px)"}},{{opacity:1,y:0,scale:1,filter:"blur(0px)",duration:.55,ease:"back.out(1.6)"}},{2.3+i*0.09:.2f});' for i in range(9)) + f'''
tl.fromTo("#op-orn1",{{opacity:0,scaleX:0}},{{opacity:1,scaleX:1,duration:.9,ease:"power2.out"}},2.5);
{spjs}
tl.to(["#op-title","#op-orn1","#op-n1","#op-n2","#op-orn2","#op-cl","#op-sc"],{{opacity:0,y:-10,duration:.55,ease:"power2.in",stagger:.03}},{T0-1.05:.2f});
tl.to("#op-all",{{opacity:0,duration:.75,ease:"power1.inOut"}},{T0-0.7:.2f});
window.__timelines["opening"] = tl;
</script>
</template>'''
    write("opening", body)
    return dur


def closing():
    dur = CLOSE
    bg, bgjs = magic_bg("cl", dur, "tl")
    sp, spjs = sparks("cl-sp", 960, 260, (420, 40), 22, .9, "tl", 1.3)
    body = HEAD + f'''<div id="root" data-composition-id="closing" data-width="1920" data-height="1080">
<div id="cl-all" style="position:absolute;inset:0;">
{bg}
<div id="cl-ty" class="serif" style="position:absolute;left:0;width:1920px;top:206px;text-align:center;font-size:54px;font-weight:700;letter-spacing:.22em;padding-left:.22em;color:#f2d48b;{TXT_GLOW}">THANK YOU FOR WATCHING</div>
{ornament("cl-orn1", 300)}
<div id="cl-n1" class="serif" style="position:absolute;left:0;width:1920px;top:372px;text-align:center;font-size:86px;font-weight:900;color:#fff6dc;letter-spacing:.02em;{TXT_GLOW}">{NAME1}</div>
<div id="cl-n2" class="serif" style="position:absolute;left:0;width:1920px;top:482px;text-align:center;font-size:52px;font-weight:700;color:#fff6dc;letter-spacing:.04em;{TXT_GLOW}">{NAME2}</div>
{ornament("cl-orn2", 586, 300)}
<div id="cl-cl" class="serif" style="position:absolute;left:0;width:1920px;top:632px;text-align:center;font-size:42px;font-weight:700;color:#f2d48b;letter-spacing:.08em;{TXT_GLOW}">{CLASS}</div>
<div id="cl-sc" class="serif" style="position:absolute;left:0;width:1920px;top:708px;text-align:center;font-size:32px;font-weight:400;color:#f7ecd0;letter-spacing:.3em;padding-left:.3em;{TXT_GLOW}">{SCHOOL}</div>
<img id="cl-pin" src="assets/img/pinocchio.png" style="position:absolute;left:1560px;top:700px;height:330px;filter:drop-shadow(0 0 18px rgba(255,210,120,.45));opacity:0" />
{sp}
</div>
<div id="cl-black" style="position:absolute;inset:0;background:#000;opacity:0"></div>
</div>
<script>
const tl = gsap.timeline({{paused:true}});
tl.fromTo("#cl-all",{{opacity:0}},{{opacity:1,duration:.85,ease:"power1.inOut"}},0);
{bgjs}
tl.fromTo("#cl-ty",{{opacity:0,y:14,filter:"blur(8px)"}},{{opacity:1,y:0,filter:"blur(0px)",duration:.8,ease:"power2.out"}},0.55);
tl.fromTo("#cl-orn1",{{opacity:0,scaleX:0}},{{opacity:1,scaleX:1,duration:.8,ease:"power2.out"}},0.8);
tl.fromTo("#cl-n1",{{opacity:0,y:16}},{{opacity:1,y:0,duration:.8,ease:"power2.out"}},1.0);
tl.fromTo("#cl-n2",{{opacity:0,y:14}},{{opacity:1,y:0,duration:.8,ease:"power2.out"}},1.2);
tl.fromTo("#cl-orn2",{{opacity:0,scaleX:0}},{{opacity:1,scaleX:1,duration:.7,ease:"power2.out"}},1.4);
tl.fromTo("#cl-cl",{{opacity:0,y:12}},{{opacity:1,y:0,duration:.7,ease:"power2.out"}},1.5);
tl.fromTo("#cl-sc",{{opacity:0,y:12}},{{opacity:1,y:0,duration:.7,ease:"power2.out"}},1.7);
tl.fromTo("#cl-pin",{{opacity:0,x:40}},{{opacity:.95,x:0,duration:1.0,ease:"power2.out"}},1.6);
tl.to("#cl-pin",{{y:-10,duration:.7,ease:"sine.inOut",yoyo:true,repeat:1}},2.6);
{spjs}
tl.to("#cl-black",{{opacity:1,duration:.8,ease:"power1.in"}},{dur-0.85:.2f});
window.__timelines["closing"] = tl;
</script>
</template>'''
    write("closing", body)
    return dur


# ---------------------------------------------------------------- lower-third nama
def lowerthird(p0, p1):
    dur = p1 - p0
    body = HEAD + f'''<div id="root" data-composition-id="nameplate" data-width="1920" data-height="1080">
<div id="lt-box" style="position:absolute;left:70px;top:820px;width:560px;height:178px;opacity:0">
  <div id="lt-bg" style="position:absolute;inset:0;border-radius:14px;background:linear-gradient(100deg,rgba(9,22,60,.86) 0%,rgba(14,34,86,.78) 70%,rgba(14,34,86,0) 100%);"></div>
  <div id="lt-bar" style="position:absolute;left:0;top:14px;width:5px;height:150px;border-radius:3px;background:linear-gradient(#ffe7a6,#d7a64a);box-shadow:0 0 12px rgba(255,210,120,.7)"></div>
  <div id="lt-n1" class="serif" style="position:absolute;left:30px;top:16px;font-size:44px;font-weight:900;color:#fff6dc;letter-spacing:.02em;{TXT_GLOW}">{NAME1}</div>
  <div id="lt-n2" class="serif" style="position:absolute;left:30px;top:72px;font-size:28px;font-weight:700;color:#fff6dc;letter-spacing:.04em;">{NAME2}</div>
  <div id="lt-sub" class="serif" style="position:absolute;left:30px;top:120px;font-size:22px;font-weight:700;color:#f2d48b;letter-spacing:.1em;">2 IBNU ABBAS &nbsp;·&nbsp; {SCHOOL}</div>
</div>
</div>
<script>
const tl = gsap.timeline({{paused:true}});
tl.fromTo("#lt-box",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:.6,ease:"power2.out"}},0);
tl.fromTo("#lt-bar",{{scaleY:0}},{{scaleY:1,duration:.6,ease:"power2.out"}},.1);
tl.fromTo(["#lt-n1","#lt-n2","#lt-sub"],{{opacity:0,x:-14}},{{opacity:1,x:0,duration:.5,stagger:.12,ease:"power2.out"}},.25);
tl.to("#lt-box",{{opacity:0,x:-20,duration:.45,ease:"power2.in"}},{dur-0.5:.2f});
window.__timelines["nameplate"] = tl;
</script>
</template>'''
    write("nameplate", body)
    return dur


# ---------------------------------------------------------------- buku cerita (PiP)
PAGE_KINDS = {
    # jenis -> (html dalam .page, js ken-burns diberi (id, t0, t1))
}


def page_html(pid, kind, opts):
    if kind == "cover":
        # kulit buku 3:4 di tengah halaman biru diraja dengan bintang
        ih = FH - 26 - 28; iw = round(ih * 0.75); left = (FW - 26 - iw) // 2
        stars = "".join(f'<div style="position:absolute;left:{rnd.uniform(4,470):.0f}px;top:{rnd.uniform(4,340):.0f}px;width:3px;height:3px;border-radius:50%;background:#ffe9b0;opacity:{rnd.uniform(.3,.8):.2f}"></div>' for _ in range(26))
        return (f'<div style="position:absolute;inset:0;background:radial-gradient(ellipse at 50% 45%,#22489a,#0b1a45 75%)">{stars}</div>'
                f'<div id="{pid}-book" style="position:absolute;left:{left}px;top:14px;width:{iw}px;height:{ih}px;perspective:900px;">'
                f'<img id="{pid}-img" src="assets/img/book-cover.webp" style="position:absolute;inset:0;width:100%;height:100%;border-radius:4px 8px 8px 4px;box-shadow:-6px 8px 18px rgba(0,0,0,.5),inset 6px 0 8px rgba(0,0,0,.25);transform-origin:0% 50%" />'
                f'<div id="{pid}-gl" class="glint"></div></div>')
    if kind == "img":
        pos = opts.get("pos", "50% 50%")
        return f'<img id="{pid}-img" class="fill" src="assets/img/{opts["src"]}" style="object-position:{pos}" />'
    if kind == "walk":
        return (f'<div class="parch" style="position:absolute;inset:0"></div>'
                f'<div style="position:absolute;left:60px;right:60px;bottom:34px;height:22px;border-radius:50%;background:radial-gradient(ellipse,rgba(120,80,30,.35),rgba(120,80,30,0) 70%)"></div>'
                f'<img id="{pid}-img" src="assets/img/pinocchio.png" style="position:absolute;left:{(FW-26)//2-110}px;top:22px;height:316px" />')
    raise ValueError(kind)


def page_js(pid, kind, opts, t0, t1, tl):
    d = max(.5, t1 - t0)
    if kind == "cover":
        return (f'{tl}.fromTo("#{pid}-img",{{rotationY:-24,scale:.9}},{{rotationY:0,scale:1,duration:1.2,ease:"power2.out"}},{t0:.2f});'
                f'{tl}.fromTo("#{pid}-gl",{{opacity:0,x:0}},{{opacity:1,x:520,duration:1.3,ease:"power1.inOut"}},{t0+1.1:.2f});'
                f'{tl}.to("#{pid}-gl",{{opacity:0,duration:.2}},{t0+2.45:.2f});'
                f'{tl}.fromTo("#{pid}-book",{{scale:1}},{{scale:1.05,duration:{d:.2f},ease:"none"}},{t0:.2f});')
    if kind == "img":
        z0, z1 = opts.get("zoom", (1.04, 1.14)); x0, x1 = opts.get("pan", (0, 0)); y0, y1 = opts.get("panY", (0, 0))
        return f'{tl}.fromTo("#{pid}-img",{{scale:{z0},xPercent:{x0},yPercent:{y0}}},{{scale:{z1},xPercent:{x1},yPercent:{y1},duration:{d:.2f},ease:"none"}},{t0:.2f});'
    if kind == "walk":
        steps = max(1, int(d / .5))
        return (f'{tl}.fromTo("#{pid}-img",{{x:90}},{{x:-90,duration:{d:.2f},ease:"none"}},{t0:.2f});'
                f'{tl}.fromTo("#{pid}-img",{{y:0,rotation:-2}},{{y:-12,rotation:2,duration:.25,ease:"sine.inOut",yoyo:true,repeat:{steps*2-1}}},{t0:.2f});')
    raise ValueError(kind)


def storybook(sid, p0, p1, pages):
    """pages: senarai (kind, opts, p_turn_in). Halaman pertama pada p0; halaman i bertukar masuk pada p_turn_in."""
    dur = round(p1 - p0, 3)
    starts = [0.0] + [round(pg[2] - p0, 3) for pg in pages[1:]]
    ends = starts[1:] + [dur]
    html, js = [], []
    n = len(pages)
    for i, (kind, opts, _) in enumerate(pages):
        pid = f"{sid}-p{i}"
        html.append(f'<div id="{pid}" class="page" style="z-index:{n-i}">{page_html(pid, kind, opts)}<div id="{pid}-sh" class="shade"></div></div>')
        js.append(page_js(pid, kind, opts, starts[i], ends[i] + 1.0, "tl"))
        if i < n - 1:
            t = ends[i] - 0.45
            js.append(f'tl.fromTo("#{pid}",{{rotationY:0,opacity:1}},{{rotationY:-96,duration:.95,ease:"power2.inOut"}},{t:.2f});'
                      f'tl.to("#{pid}",{{opacity:0,duration:.2}},{t+.75:.2f});'
                      f'tl.fromTo("#{pid}-sh",{{opacity:0}},{{opacity:.6,duration:.9,ease:"power1.in"}},{t:.2f});')
            s_html, s_js = sparks(f"{sid}-s{i}-", FX + FW / 2, FY + 40, (FW / 2, 50), 10, t + .3, "tl", .9)
            html.append(s_html); js.append(s_js)
    s_html, s_js = sparks(f"{sid}-in-", FX + FW / 2, FY + FH / 2, (FW / 2 + 20, FH / 2 + 10), 16, .1, "tl", 1.0)
    body = HEAD + f'''<div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">
<div id="{sid}-fr" class="frame">
  <div class="mat"></div>
  <div class="pages">{"".join(h for h in html if 'class="page"' in h)}</div>
  {corners(sid)}
</div>
{s_html}
{"".join(h for h in html if 'class="page"' not in h)}
</div>
<script>
const tl = gsap.timeline({{paused:true}});
tl.fromTo("#{sid}-fr",{{opacity:0,y:28,scale:.93,rotationX:8}},{{opacity:1,y:0,scale:1,rotationX:0,duration:.75,ease:"power2.out"}},0);
{s_js}
{"".join(js)}
tl.to("#{sid}-fr",{{opacity:0,y:16,scale:.96,duration:.5,ease:"power2.in"}},{dur-0.55:.2f});
window.__timelines["{sid}"] = tl;
</script>
</template>'''
    write(sid, body)
    return dur


# ---------------------------------------------------------------- kad pengajaran moral
def moral(p0, p1, title, items):
    dur = round(p1 - p0, 3)
    L, T, W = 1360, 300, 516
    rows = []
    for i, (txt, pt) in enumerate(items):
        rows.append(f'<div id="mo-i{i}" style="position:absolute;left:34px;top:{112+i*78}px;width:{W-60}px;opacity:0">'
                    f'<div style="position:absolute;left:0;top:13px;width:12px;height:12px;background:#f2d48b;transform:rotate(45deg);box-shadow:0 0 10px rgba(255,214,120,.8)"></div>'
                    f'<div class="serif" style="position:absolute;left:30px;top:0;width:{W-100}px;font-size:31px;line-height:1.15;font-weight:700;color:#fff6dc">{txt}</div></div>')
    h = 112 + len(items) * 78 + 20
    js = "".join(f'tl.fromTo("#mo-i{i}",{{opacity:0,x:22}},{{opacity:1,x:0,duration:.6,ease:"power2.out"}},{pt-p0:.2f});' for i, (_, pt) in enumerate(items))
    sp, spjs = sparks("mo-sp", L + W / 2, T + 40, (W / 2, 40), 14, .2, "tl", 1.0)
    body = HEAD + f'''<div id="root" data-composition-id="moral" data-width="1920" data-height="1080">
<div id="mo-card" style="position:absolute;left:{L}px;top:{T}px;width:{W}px;height:{h}px;opacity:0">
  <div class="mat"></div>
  {corners("mo")}
  <div id="mo-t" class="serif" style="position:absolute;left:0;width:{W}px;top:26px;text-align:center;font-size:40px;font-weight:700;color:#f2d48b;letter-spacing:.04em;{TXT_GLOW}">{title}</div>
  <div style="position:absolute;left:{W//2-130}px;top:84px;width:260px;height:1.5px;background:linear-gradient(90deg,rgba(226,191,104,0),#e2bf68,rgba(226,191,104,0))"></div>
  {"".join(rows)}
</div>
{sp}
</div>
<script>
const tl = gsap.timeline({{paused:true}});
tl.fromTo("#mo-card",{{opacity:0,y:26,scale:.94}},{{opacity:1,y:0,scale:1,duration:.75,ease:"power2.out"}},0);
{spjs}
{js}
tl.to("#mo-card",{{opacity:0,y:14,duration:.5,ease:"power2.in"}},{dur-0.55:.2f});
window.__timelines["moral"] = tl;
</script>
</template>'''
    write("moral", body)
    return dur


# ---------------------------------------------------------------- tag tajuk kecil sepanjang persembahan
def tag(p0, p1):
    dur = round(p1 - p0, 3)
    body = HEAD + f'''<div id="root" data-composition-id="booktag" data-width="1920" data-height="1080">
<div id="tg-box" style="position:absolute;left:64px;top:50px;height:52px;width:300px;opacity:0">
  <div style="position:absolute;inset:0;border-radius:26px;background:linear-gradient(90deg,rgba(9,22,60,.72),rgba(9,22,60,.0));"></div>
  <div style="position:absolute;left:22px;top:20px;width:11px;height:11px;background:#f2d48b;transform:rotate(45deg);box-shadow:0 0 10px rgba(255,214,120,.9)"></div>
  <div class="serif" style="position:absolute;left:48px;top:9px;font-size:27px;font-weight:700;letter-spacing:.24em;color:#f2d48b;{TXT_GLOW}">PINOCCHIO</div>
</div>
</div>
<script>
const tl = gsap.timeline({{paused:true}});
tl.fromTo("#tg-box",{{opacity:0,x:-16}},{{opacity:.9,x:0,duration:.8,ease:"power2.out"}},0);
tl.to("#tg-box",{{opacity:.75,duration:{max(1,dur-2):.2f},ease:"none"}},.9);
tl.to("#tg-box",{{opacity:0,duration:.5}},{dur-0.6:.2f});
window.__timelines["booktag"] = tl;
</script>
</template>'''
    write("booktag", body)
    return dur


# ---------------------------------------------------------------- root
def build_hf(overlay=False):
    scenes = []  # (id, abs_start, dur, track)
    scenes.append(("opening", 0, opening(), 10))
    c = CFG
    scenes.append(("booktag", a(c["tag"][0]), tag(*c["tag"]), 2))
    scenes.append(("nameplate", a(c["nameplate"][0]), lowerthird(*c["nameplate"]), 3))
    for k, sb in enumerate(c["books"]):
        sid = f"book{k+1}"
        pages = [(pg["kind"], pg, pg["at"]) for pg in sb["pages"]]
        scenes.append((sid, a(sb["start"]), storybook(sid, sb["start"], sb["end"], pages), 4 + k % 2))
    mo = c["moral"]
    scenes.append(("moral", a(mo["start"]), moral(mo["start"], mo["end"], mo["title"], [(i["text"], i["at"]) for i in mo["items"]]), 6))
    scenes.append(("closing", round(T0 + PERF, 3), closing(), 10))

    hid = ' data-hidden' if overlay else ''
    hosts = "\n".join(
        f'<div id="{sid}" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{st}" data-duration="{du}" '
        f'data-track-index="{tr}" data-track-kind="graphics" data-width="1920" data-height="1080" style="z-index:{10+i}"></div>'
        for i, (sid, st, du, tr) in enumerate(scenes))
    html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1920, height=1080" />
<script src="assets/vendor/gsap.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:{'transparent' if overlay else '#000'};}}
#root{{position:absolute;inset:0;}}
.still{{position:absolute;left:0;top:0;width:1920px;height:1080px;object-fit:contain;}}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
<img id="first-frame" class="clip still" src="assets/footage/first.jpg" data-start="{T0-1.2:.2f}" data-duration="1.2" data-track-index="0" style="z-index:1"{hid} />
<video id="perf" class="clip" src="assets/footage/performance.mp4" data-start="{T0}" data-duration="{PERF}" data-track-index="1" muted playsinline style="position:absolute;left:0;top:0;width:1920px;height:1080px;object-fit:contain;z-index:2"{hid}></video>
<img id="last-frame" class="clip still" src="assets/footage/last.jpg" data-start="{T0+PERF:.3f}" data-duration="{CLOSE}" data-track-index="0" style="z-index:3"{hid} />
<audio id="mix" class="clip" src="assets/audio/mix.wav" data-start="0" data-duration="{TOTAL}" data-track-index="20" data-volume="1"{hid}></audio>
{hosts}
</div>
<script>
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = gsap.timeline({{paused:true}});
</script>
</body>
</html>
'''
    open(os.path.join(HF, "index.html"), "w").write(html)
    print("hf ok", "overlay" if overlay else "preview", TOTAL, [s[0] for s in scenes])


# ---------------------------------------------------------------- audio
def build_mix():
    w = os.path.join(HERE, "work")
    sfx = os.path.join(HF, "assets", "sfx")
    c = CFG
    # (fail, masa video, gain)
    cues = [(f"{sfx}/sparkle.mp3", 2.35, .45), (f"{sfx}/chime.mp3", 0.45, .30), (f"{sfx}/whoosh.mp3", T0 - 0.95, .22)]
    for sb in c["books"]:
        cues.append((f"{sfx}/sparkle.mp3", a(sb["start"]), .16))
        for pg in sb["pages"][1:]:
            cues.append((f"{sfx}/page_turn.wav", a(pg["at"]) - 0.45, .22))
    cues.append((f"{sfx}/sparkle.mp3", a(c["moral"]["start"]), .16))
    cues += [(f"{sfx}/sparkle.mp3", T0 + PERF + 0.85, .4), (f"{sfx}/chime.mp3", T0 + PERF + 1.0, .3)]

    ins = ["-i", SRC, "-i", f"{w}/music_raw.wav"]
    for f, _, _ in cues:
        ins += ["-i", f]
    e = T0 + PERF
    # muzik: penuh di pembuka, sangat perlahan semasa bercerita (dan diduck oleh suara), naik semula di penutup
    mvol = (f"if(lt(t,{T0-0.8}),0.62,"
            f"if(lt(t,{T0+1.2}),0.62-(0.62-0.055)*(t-{T0-0.8})/2.0,"
            f"if(lt(t,{e-0.6}),0.055,"
            f"if(lt(t,{e+0.6}),0.055+(0.6-0.055)*(t-{e-0.6})/1.2,0.6))))")
    fc = [f"[0:a]highpass=f=70,volume=-4.6dB,alimiter=limit=0.89:level=false,adelay={int(T0*1000)}|{int(T0*1000)},apad=whole_dur={TOTAL},asplit=2[v][vsc]",
          f"[1:a]atrim=0:{TOTAL},volume='{mvol}':eval=frame,afade=t=out:st={TOTAL-2.2}:d=2.2[m0]",
          "[m0][vsc]sidechaincompress=threshold=0.03:ratio=4:attack=20:release=400:makeup=1[m]"]
    labs = []
    for k, (f, t, g) in enumerate(cues):
        fc.append(f"[{k+2}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={g},adelay={int(t*1000)}|{int(t*1000)}[s{k}]")
        labs.append(f"[s{k}]")
    fc.append(f"[v][m]{''.join(labs)}amix=inputs={2+len(cues)}:normalize=0:duration=first,atrim=0:{TOTAL},alimiter=limit=0.93:level=false[out]")
    out = f"{w}/mix.wav"
    cmd = ["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fc), "-map", "[out]", "-ar", "48000", "-ac", "2", out]
    subprocess.run(cmd, check=True)
    os.makedirs(os.path.join(HF, "assets", "audio"), exist_ok=True)
    subprocess.run(["cp", out, os.path.join(HF, "assets", "audio", "mix.wav")], check=True)
    print("mix ok", out)


# ---------------------------------------------------------------- eksport akhir
def build_final(overlay_path, out):
    grade = open(os.path.join(HERE, "grade.txt")).read().strip()
    fc = (f"[0:v]{grade},fps=60,tpad=start_duration={T0}:start_mode=clone:stop_duration={CLOSE+0.5}:stop_mode=clone,trim=0:{TOTAL},setpts=PTS-STARTPTS[base];"
          f"[1:v]fps=60,format=yuva444p,setpts=PTS-STARTPTS[ov];"
          f"[base][ov]overlay=0:0:format=auto:shortest=0,format=yuv420p[vout]")
    cmd = ["ffmpeg", "-v", "error", "-stats", "-y", "-i", SRC, "-i", overlay_path, "-i", os.path.join(HERE, "work", "mix.wav"),
           "-filter_complex", fc, "-map", "[vout]", "-map", "2:a",
           "-c:v", "libx264", "-preset", "medium", "-crf", os.environ.get("CRF", "17"), "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", "60",
           "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-t", str(TOTAL), out]
    subprocess.run(cmd, check=True)
    print("final ok", out)


if __name__ == "__main__":
    what = sys.argv[1]
    if what == "hf":
        build_hf("--overlay" in sys.argv)
    elif what == "mix":
        build_mix()
    elif what == "final":
        build_final(sys.argv[2], sys.argv[3])
