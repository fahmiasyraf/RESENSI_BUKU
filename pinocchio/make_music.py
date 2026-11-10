"""Muzik latar fairytale disintesis sendiri (bebas hak cipta).

Waltz 3/4 lembut dalam F major: kotak muzik (FM bell), celesta, piano, pad string dan glockenspiel.
Guna: python3 make_music.py <out.wav> <durasi_saat>
"""
import sys, wave
import numpy as np

SR = 48000
out = sys.argv[1]
dur = float(sys.argv[2]) if len(sys.argv) > 2 else 260.0
N = int(dur * SR)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(7)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def add(start, sig, pan=0.0, gain=1.0):
    i = int(start * SR)
    if i >= N:
        return
    j = min(N, i + len(sig))
    s = sig[: j - i] * gain
    L[i:j] += s * np.sqrt(0.5 * (1 - pan))
    R[i:j] += s * np.sqrt(0.5 * (1 + pan))


def bell(f, length=2.5, bright=1.0):
    """Kotak muzik / celesta: FM dengan nisbah tidak harmonik, reput eksponen."""
    n = int(length * SR); t = np.arange(n) / SR
    idx = bright * 2.2 * np.exp(-t * 6)
    s = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * 3.5 * t))
    s += 0.25 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * 3)
    env = np.exp(-t * 2.4) * (1 - np.exp(-t * 900))
    return s * env


def piano(f, length=2.0, vel=1.0):
    n = int(length * SR); t = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * k * 0.9)
            for k, a in [(1, 1), (2, .4), (3, .15), (4, .06)])
    env = np.exp(-t * 1.6) * (1 - np.exp(-t * 400))
    return vel * s * env


def pad(freqs, length):
    n = int(length * SR); t = np.arange(n) / SR
    att = min(1.5, length / 3)
    env = np.minimum(1, t / att) * np.minimum(1, np.maximum(0, (length - t) / att))
    s = np.zeros(n)
    for f in freqs:
        for d, ph in [(1, 0), (1.003, 1.3), (0.997, 2.1)]:
            # gelombang gergaji lembut (3 harmonik) => tekstur string
            s += sum(np.sin(2 * np.pi * f * d * k * t + ph) / k ** 1.6 for k in (1, 2, 3))
    vib = 1 + 0.15 * np.sin(2 * np.pi * 0.25 * t)
    return s * env * vib / (len(freqs) * 3)


# ---- struktur ----
bpm = 84
beat = 60 / bpm
bar = 3 * beat
# I - vi - IV - V  |  I - iii - IV - V (F major)
prog = [
    [53, 65, 69, 72], [50, 62, 65, 69], [46, 62, 65, 70], [48, 60, 64, 67],
    [53, 65, 69, 72], [45, 60, 64, 69], [46, 62, 65, 70], [48, 60, 64, 70],
]
# melodi kotak muzik (dua frasa x 4 bar, nota per detik ketukan; None = rehat)
mel = [
    [77, 81, 84], [86, None, 84], [82, 81, 79], [79, None, None],
    [77, 81, 84], [88, 86, 84], [82, 84, 86], [84, None, None],
]
nbars = int(dur / bar) + 2
for b in range(nbars):
    t0 = b * bar
    ch = prog[b % len(prog)]
    # pad string
    add(t0, pad([midi(n) for n in ch[1:]], bar + 0.8), gain=0.11)
    # bas piano pada ketukan 1, kord pada 2 & 3 (waltz)
    add(t0, piano(midi(ch[0] - 12), bar * 1.2, 0.22))
    for k in (1, 2):
        for j, n in enumerate(ch[1:]):
            add(t0 + k * beat, piano(midi(n), beat * 1.5, 0.06), pan=(j - 1) * 0.3)
    # melodi kotak muzik
    phrase = mel[b % len(mel)]
    for k, n in enumerate(phrase):
        if n is not None:
            add(t0 + k * beat + rng.uniform(0, 0.012), bell(midi(n), 3.0), pan=0.25, gain=0.11)
    # glockenspiel berkilau tiap 4 bar
    if b % 4 == 3:
        for k, n in enumerate([96, 93, 89, 84]):
            add(t0 + 2 * beat + k * beat / 4, bell(midi(n), 1.6, 0.6), pan=-0.4, gain=0.045)

# reverb ringkas (jumlah lengahan berbilang, lowpass)
def reverb(x):
    y = x.copy()
    for d, g in [(0.031, .35), (0.047, .3), (0.071, .26), (0.113, .22), (0.173, .18), (0.257, .14), (0.389, .1)]:
        k = int(d * SR); y[k:] += g * x[:-k]
    return y

L = reverb(L); R = reverb(R[::1])
# lowpass lembut
def lowpass(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X / np.sqrt(1 + (f / fc) ** 4), len(x))
L = lowpass(L, 9000); R = lowpass(R, 9000)
st = np.stack([L, R], 1)
st /= np.max(np.abs(st)) * 1.12
# fade in/out
fi = int(1.5 * SR); fo = int(4 * SR)
st[:fi] *= np.linspace(0, 1, fi)[:, None]
st[-fo:] *= np.linspace(1, 0, fo)[:, None]
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
print("ok", out, dur)
