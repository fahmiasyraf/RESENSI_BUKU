"""Kesan bunyi selak halaman buku (hingar ditapis + kibasan), disintesis sendiri."""
import sys, wave
import numpy as np
SR = 48000; rng = np.random.default_rng(3)
def write(path, x):
    st = np.stack([x, x * 0.92], 1); st /= np.max(np.abs(st)) * 1.05
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
def bandpass(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    return np.fft.irfft(X * ((f > lo) & (f < hi)) * np.exp(-((f - (lo + hi) / 2) / (hi - lo)) ** 2), len(x))
n = int(0.75 * SR); t = np.arange(n) / SR
noise = bandpass(rng.standard_normal(n), 900, 7000)
flutter = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 23 * t * (1 - t)))
env = np.minimum(1, t / 0.05) * np.exp(-((t - 0.28) / 0.2) ** 2)
snap = np.zeros(n); k = int(0.46 * SR); snap[k:k + 900] = rng.standard_normal(900) * np.exp(-np.arange(900) / 120)
write(sys.argv[1], noise * flutter * env + 0.6 * bandpass(snap, 400, 5000))
