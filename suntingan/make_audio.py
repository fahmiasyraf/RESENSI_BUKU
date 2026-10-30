import numpy as np, wave, sys
out = sys.argv[1]; SR = 48000
def write(name, x):
    x = np.clip(x, -1, 1); st = np.stack([x[0], x[1]], 1) if x.ndim == 2 else np.stack([x, x], 1)
    with wave.open(f"{out}/{name}", "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
def midi(n): return 440 * 2 ** ((n - 69) / 12)
def lowpass(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / np.sqrt(1 + (f / fc) ** 4), len(x))

# --- music: calm corporate piano + pad, 76 bpm, I-V-vi-IV in D major ---
bpm = 76; beat = 60 / bpm; bar = 4 * beat
dur = 300.0; N = int(dur * SR); t = np.arange(N) / SR
L = np.zeros(N); R = np.zeros(N)
prog = [[50, 62, 66, 69], [45, 61, 64, 69], [47, 62, 66, 71], [43, 59, 62, 67]]  # D A Bm G
def piano(f, length, vel):
    n = int(length * SR); tt = np.arange(n) / SR
    env = np.exp(-tt * 2.2) * (1 - np.exp(-tt * 300))
    s = sum(a * np.sin(2 * np.pi * f * k * tt) * np.exp(-tt * k * 0.8) for k, a in [(1, 1), (2, .35), (3, .12), (4, .05)])
    return vel * s * env
def add(buf, start, sig):
    i = int(start * SR); j = min(N, i + len(sig))
    if i < N: buf[i:j] += sig[:j - i]
nbars = int(dur / bar) + 1
for b in range(nbars):
    ch = prog[b % 4]; t0 = b * bar
    # pad (sustained, soft)
    n = int(bar * SR) + SR; tt = np.arange(n) / SR
    env = np.minimum(1, tt / 1.2) * np.minimum(1, np.maximum(0, (bar + 1 - tt) / 1.0))
    for k, note in enumerate(ch[1:]):
        f = midi(note); pad = sum(np.sin(2 * np.pi * f * d * tt + ph) for d, ph in [(1, 0), (1.004, 1), (0.996, 2)]) / 3
        add(L if k % 2 else R, t0, 0.045 * pad * env); add(R if k % 2 else L, t0, 0.03 * pad * env)
    # bass
    add(L, t0, piano(midi(ch[0] - 12), bar, 0.16)); add(R, t0, piano(midi(ch[0] - 12), bar, 0.16))
    # arpeggio piano in 8ths (enters after 4 bars)
    if b >= 2:
        pat = [ch[1], ch[2], ch[3], ch[2] + 12, ch[3], ch[2], ch[1] + 12, ch[2]]
        for i, nn in enumerate(pat):
            v = 0.10 if i % 2 == 0 else 0.07; pan = 0.5 + 0.25 * np.sin(i)
            s = piano(midi(nn), 2.0, v); add(L, t0 + i * beat / 2, s * (1 - pan) * 1.4); add(R, t0 + i * beat / 2, s * pan * 1.4)
mus = np.stack([lowpass(L, 5000), lowpass(R, 5000)])
mus /= np.abs(mus).max() * 1.12
fade = np.minimum(1, t / 3.0); mus *= fade
write("music_raw.wav", mus)

# --- whoosh (soft filtered noise sweep, 0.9 s) ---
n = int(0.9 * SR); tt = np.arange(n) / SR; rng = np.random.default_rng(1)
noise = rng.standard_normal(n)
X = np.fft.rfft(noise); f = np.fft.rfftfreq(n, 1 / SR)
w = np.fft.irfft(X * np.exp(-((f - 1800) / 1500) ** 2), n)
env = np.sin(np.pi * np.clip(tt / 0.9, 0, 1)) ** 2
wh = w * env; wh /= np.abs(wh).max(); pan = tt / 0.9
write("whoosh.wav", np.stack([wh * (1 - pan * .6) * .5, wh * (.4 + pan * .6) * .5]))
# --- soft chime/pop for graphics (0.8 s) ---
n = int(1.2 * SR); tt = np.arange(n) / SR
c = sum(a * np.sin(2 * np.pi * fr * tt) * np.exp(-tt * d) for fr, a, d in [(1318.5, 1, 5), (1975.5, .5, 7), (2637, .25, 9)])
c *= (1 - np.exp(-tt * 800)); c /= np.abs(c).max()
write("chime.wav", c * 0.45)
print("done")
