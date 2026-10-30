"""Build the edited review video. Usage: build.py preview|final [seconds]"""
import sys, subprocess, os
MODE = sys.argv[1]; S = os.path.dirname(os.path.abspath(__file__)); A = f"{S}/assets"
RAW = f"{S}/src/raw.mp4"; DUR = 280.04; PRE, POST = 3.0, 4.0; TOTAL = PRE + DUR + POST

# ---- framing keyframes (raw time, zoom, centre x, centre y in the 1920x1080 frame) ----
WIDE, MED, CLOSE = (1.0, 960, 540), (1.3, 1030, 516), (1.6, 1030, 436)
# book shots: framed to keep the whole face in view (top edge ~ forehead) while the book fills the lower frame
def BOOK(z, x, y): return (1.45, x, 601)
KEYS = [(0, WIDE), (12, MED), (21.6, BOOK(1.8, 1000, 580)), (25.6, WIDE), (36, CLOSE),
        (41.8, BOOK(1.7, 1000, 620)), (45.2, WIDE), (53, MED), (61.6, BOOK(1.8, 970, 630)), (65, WIDE),
        (78, CLOSE), (92, MED), (104, WIDE), (115.3, BOOK(2.0, 1000, 770)), (118.8, MED), (132, CLOSE),
        (146, WIDE), (160, MED), (174, CLOSE), (188, WIDE), (200, MED), (216.3, BOOK(1.9, 860, 640)),
        (219.3, WIDE), (226.4, BOOK(1.9, 830, 660)), (229.4, CLOSE), (242, MED), (256, WIDE),
        (273.8, BOOK(1.9, 1030, 780)), (278.2, WIDE)]
BOOK_TIMES = [k[0] for k in KEYS if k[1] not in (WIDE, MED, CLOSE)]
D = 0.7  # transition length (s), smoothstep eased
def track(i, T="it"):
    expr = f"{KEYS[0][1][i]}"
    for (t, v), (_, pv) in zip(KEYS[1:], KEYS[:-1]):
        dv = v[i] - pv[i]
        if dv: c = f"clip(({T}-{t})/{D},0,1)"; expr += f"+({dv})*{c}*{c}*(3-2*{c})"
    return expr
Z, CX, CY = track(0), track(1), track(2)

SPLIT = (26.5, 33.5)      # split-screen: book panel + speaker
PLANE = (46.0, 52.0)      # B-roll panel: aircraft in the sky
LT = (1.5, 9.0)           # name/title lower third

g = open(f"{S}/grade.txt").read().strip().replace("[m0]", "[mask]")
f = []
f.append(f"[1:v]format=gray,loop=-1:1:0,fps=30,trim=duration={DUR},setpts=PTS-STARTPTS[mask]")
DBG = ",drawtext=fontfile=/usr/share/fonts/opentype/inter/Inter-Bold.otf:text=SRC%{pts}:fontsize=70:fontcolor=red:x=300:y=200" if os.environ.get("DBG") else ""
f.append(f"[0:v]setpts=PTS-STARTPTS,fps=30{DBG},{g},fps=30[graded]")
f.append("[graded]split[g1][g2]")
f.append(f"[g1]crop=1920:1080:0:4,zoompan=z='{Z}':x='clip(({CX})-iw/zoom/2,0,iw-iw/zoom)':y='clip(({CY})-ih/zoom/2,0,ih-ih/zoom)'"
         f":d=1:s=1920x1080:fps=30,setsar=1[zoomed]")
# split-screen
f.append("[g2]crop=960:1080:550:4,format=rgba,pad=1920:1080:960:0:color=black@0[side]")
f.append(f"[2:v]format=rgba,loop=-1:1:0,trim=duration={DUR}[spl]")
f.append(f"[side][spl]overlay=format=auto,fade=t=in:st={SPLIT[0]}:d=0.45:alpha=1,fade=t=out:st={SPLIT[1]-0.45}:d=0.45:alpha=1[splitv]")
f.append(f"[zoomed][splitv]overlay=enable='between(t,{SPLIT[0]},{SPLIT[1]})'[v1]")
# B-roll panel
f.append("[3:v]scale=640:360,format=rgba[sky];[sky][4:v]alphamerge[skym]")
f.append(f"[5:v]format=rgba,loop=-1:1:0,trim=duration=6[pf];[pf][skym]overlay=20:20,"
         f"fade=t=in:st=0:d=0.45:alpha=1,fade=t=out:st=5.5:d=0.5:alpha=1,setpts=PTS-STARTPTS+{PLANE[0]}/TB[panel]")
f.append(f"[v1][panel]overlay=50:390:eof_action=pass:enable='between(t,{PLANE[0]},{PLANE[1]})'[v2]")
# lower third + logo
f.append(f"[6:v]format=rgba,loop=-1:1:0,trim=duration={LT[1]+1},fade=t=in:st={LT[0]}:d=0.5:alpha=1,fade=t=out:st={LT[1]-0.5}:d=0.5:alpha=1[lt]")
f.append(f"[v2][lt]overlay=eof_action=pass:enable='lte(t,{LT[1]})'[v3]")
f.append(f"[7:v]scale=-1:150,format=rgba,loop=-1:1:0,trim=duration={DUR}[logo]")
f.append(f"[v3][logo]overlay=W-w-40:36,fade=t=in:st=0:d=0.5,fade=t=out:st={DUR-0.7}:d=0.7,format=yuv420p,setsar=1[body]")
# cards
f.append(f"[8:v]loop=-1:1:0,trim=duration={PRE},fps=30,format=yuv420p,setsar=1,fade=t=in:st=0:d=0.6,fade=t=out:st={PRE-0.5}:d=0.5[c1]")
f.append(f"[9:v]loop=-1:1:0,trim=duration={POST},fps=30,format=yuv420p,setsar=1,fade=t=in:st=0:d=0.6,fade=t=out:st={POST-0.8}:d=0.8[c2]")
f.append("[c1][body][c2]concat=n=3:v=1:a=0[vcat]")
if MODE == "preview":
    f.append("[10:v]format=rgba,loop=-1:1:0[wm];[vcat][wm]overlay=shortest=1,scale=960:540:flags=lanczos[vout]")
else:
    f.append("[vcat]null[vout]")
# ---- audio ----
ms = int(PRE * 1000)
f.append(f"[0:a]highpass=f=80,afftdn=nf=-25,equalizer=f=3000:t=q:w=1.5:g=2,"
         f"acompressor=threshold=-24dB:ratio=3:attack=10:release=200:makeup=3,loudnorm=I=-16:TP=-1.5:LRA=9,"
         f"aresample=48000,adelay={ms}|{ms},apad=whole_dur={TOTAL}[voice]")
f.append(f"[11:a]atrim=0:{TOTAL},volume='0.2+0.35*(1-clip((t-{PRE-0.6})/1,0,1))+0.35*clip((t-{PRE+DUR-0.3})/1,0,1)':eval=frame,"
         f"afade=t=out:st={TOTAL-2.2}:d=2.2[music]")
sfx_w = [PRE - 0.5, SPLIT[0] + PRE - 0.3, PLANE[0] + PRE - 0.3] + [t + PRE - 0.35 for t in BOOK_TIMES]
sfx_c = [LT[0] + PRE + 0.1, PRE + DUR + 0.2]
f.append(f"[12:a]asplit={len(sfx_w)}" + "".join(f"[wi{i}]" for i in range(len(sfx_w))))
f.append(f"[13:a]asplit={len(sfx_c)}" + "".join(f"[ci{i}]" for i in range(len(sfx_c))))
labels = []
for i, t in enumerate(sfx_w):
    d = int(t * 1000); f.append(f"[wi{i}]adelay={d}|{d},volume=0.22[w{i}]"); labels.append(f"[w{i}]")
for i, t in enumerate(sfx_c):
    d = int(t * 1000); f.append(f"[ci{i}]adelay={d}|{d},volume=0.18[c{i}]"); labels.append(f"[c{i}]")
f.append(f"[voice][music]{''.join(labels)}amix=inputs={2 + len(labels)}:normalize=0:duration=first,alimiter=limit=0.95,atrim=0:{TOTAL}[aout]")
open(f"{S}/graph_{MODE}.txt", "w").write(";\n".join(f))

inputs = [RAW, f"{A}/fillmask.png", f"{A}/split_left.png", f"{S}/broll/sky_plane.mp4", f"{A}/panel_mask.png",
          f"{A}/panel_frame.png", f"{A}/lower_third.png", f"{A}/logo_card.png", f"{A}/card_title.png", f"{A}/card_end.png",
          f"{A}/watermark.png", f"{S}/audio/music.wav", f"{S}/audio/whoosh.wav", f"{S}/audio/chime.wav"]
cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-stats", "-y"]
for p in inputs: cmd += ["-i", p]
if len(sys.argv) > 2: cmd += ["-t", sys.argv[2]]
cmd += ["-filter_complex_script", f"{S}/graph_{MODE}.txt", "-map", "[vout]", "-map", "[aout]"]
if MODE == "preview":
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "26", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", f"{S}/out/pratonton_resensi.mp4"]
else:
    cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", "18", "-profile:v", "high", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", f"{S}/out/RESENSI_BUKU_MERZ_final.mp4"]
os.makedirs(f"{S}/out", exist_ok=True)
subprocess.run(cmd, check=True)
