#!/usr/bin/env python3
"""Procedural sounds for reply 27 (hand grenades), no downloaded audio. numpy + scipy + soundfile (OGG Vorbis).
   grenade_pin    pin pulled out of the UZRGM fuze (ring scrape + tink)
   grenade_throw  arm swing whoosh
   grenade_bounce steel body hitting the ground (clink + dull thud), 3 variants
   grenade_blast  ~60-200 g TNT at close range: very short sharp crack, punchy body, short tail
   flashbang      Zarya-2 / M84: 170+ dB bang, extremely sharp, no fragment whizz
   tinnitus       ringing in the ears after a stun grenade (3.9 kHz + 4.15 kHz beat), 7 s decay
   smoke_hiss     smoke composition burning in the can (broadband hiss, loop-friendly)
usage: ~/.cache/bpyenv/bin/python tools/make_sounds_r27.py
"""
import os
import numpy as np
from scipy import signal
import soundfile as sf

SR = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'mods', 'aiarsenal', 'src', 'main', 'resources',
                   'assets', 'aiarsenal', 'sounds')
rng = np.random.default_rng(27)


def noise(d):
    return rng.standard_normal(int(d * SR))


def env(d, a, tau):
    t = np.arange(int(d * SR)) / SR
    e = np.where(t < a, t / max(a, 1e-6), np.exp(-(t - a) / tau))
    return e


def lp(x, fc, order=3):
    b, a = signal.butter(order, min(fc / (SR / 2), 0.99), 'low')
    return signal.lfilter(b, a, x)


def hp(x, fc, order=2):
    b, a = signal.butter(order, min(fc / (SR / 2), 0.99), 'high')
    return signal.lfilter(b, a, x)


def bp(x, f1, f2, order=2):
    b, a = signal.butter(order, [f1 / (SR / 2), min(f2 / (SR / 2), 0.99)], 'band')
    return signal.lfilter(b, a, x)


def norm(x, peak=0.95):
    m = np.max(np.abs(x))
    return x * (peak / m) if m > 0 else x


def seq(parts, d):
    n = int(d * SR)
    x = np.zeros(n)
    for at, s in parts:
        j = int(at * SR)
        e = min(n, j + len(s))
        x[j:e] += s[:e - j]
    return x


def ring(d, freqs, tau, amp=1.0):
    t = np.arange(int(d * SR)) / SR
    x = np.zeros_like(t)
    for f, a in freqs:
        x += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28))
    return x * np.exp(-t / tau) * amp


def write(name, x):
    x = np.clip(x, -1, 1).astype(np.float32)
    p = os.path.join(OUT, name + '.ogg')
    sf.write(p, x, SR, format='OGG', subtype='VORBIS')
    print(name, round(len(x) / SR, 2), 's', os.path.getsize(p), 'B')


def pin():
    scrape = bp(noise(0.12), 2500, 9000) * env(0.12, 0.01, 0.04) * 0.5
    tink = ring(0.25, [(5200, 1.0), (7900, 0.5), (11200, 0.25)], 0.05) * 0.6
    click = bp(noise(0.02), 1500, 6000) * env(0.02, 0.0005, 0.004)
    return norm(seq([(0.0, click), (0.02, scrape), (0.14, tink)], 0.45), 0.8)


def throw():
    d = 0.4
    t = np.arange(int(d * SR)) / SR
    x = noise(d)
    # band sweeping up then down with the arm
    out = np.zeros_like(x)
    blocks = 20
    L = len(x) // blocks
    for i in range(blocks):
        f = 300 + 900 * np.sin(np.pi * i / blocks)
        out[i * L:(i + 1) * L] = bp(x, f, f * 2.2)[i * L:(i + 1) * L]
    return norm(out * np.sin(np.pi * t / d) ** 2, 0.6)


def bounce(k):
    f0 = [2900, 3400, 2500][k]
    clink = ring(0.3, [(f0, 1.0), (f0 * 1.52, 0.6), (f0 * 2.31, 0.3)], 0.035)
    thud = lp(noise(0.12), 260, 2) * env(0.12, 0.001, 0.025) * 2.5
    grit = bp(noise(0.08), 900, 4000) * env(0.08, 0.0005, 0.012) * 0.6
    return norm(clink * 0.7 + np.pad(thud, (0, len(clink) - len(thud))) + np.pad(grit, (0, len(clink) - len(grit))), 0.75)


def blast():
    d = 1.6
    n = int(d * SR)
    x = np.zeros(n)
    L = int(0.0006 * SR)
    x[:L] += np.linspace(1, -1, L) * 1.4                      # N-wave front
    x += hp(np.concatenate([noise(0.004) * env(0.004, 0.0001, 0.001), np.zeros(n - int(0.004 * SR))]), 3000) * 0.9
    x += lp(noise(d), 420, 3) * env(d, 0.001, 0.07) * 4.5     # body
    x += bp(noise(d), 400, 2600) * env(d, 0.0005, 0.03) * 1.0
    x += lp(noise(d), 160, 2) * env(d, 0.01, 0.35) * 1.2      # ground thump + tail
    # a few dirt / fragment ticks landing
    for i in range(14):
        at = 0.08 + rng.uniform(0, 0.9)
        j = int(at * SR)
        s = bp(noise(0.015), 1500, 6000) * env(0.015, 0.0003, 0.003) * rng.uniform(0.05, 0.18)
        x[j:j + len(s)] += s[:max(0, n - j)]
    return norm(np.tanh(norm(x) * 2.6), 0.98)


def flashbang():
    d = 1.3
    n = int(d * SR)
    x = np.zeros(n)
    L = int(0.0004 * SR)
    x[:L] += np.linspace(1, -1, L) * 1.6
    x += hp(np.concatenate([noise(0.006) * env(0.006, 0.0001, 0.0015), np.zeros(n - int(0.006 * SR))]), 2500) * 1.4
    x += lp(noise(d), 700, 3) * env(d, 0.0008, 0.05) * 4.0
    x += bp(noise(d), 1500, 7000) * env(d, 0.0004, 0.02) * 1.6
    x += lp(noise(d), 200, 2) * env(d, 0.01, 0.25) * 0.8
    x += ring(d, [(3900, 0.08)], 0.4)                          # hint of the ringing already
    return norm(np.tanh(norm(x) * 3.2), 0.99)


def tinnitus():
    d = 7.0
    t = np.arange(int(d * SR)) / SR
    x = np.sin(2 * np.pi * 3900 * t) * 0.7 + np.sin(2 * np.pi * 4150 * t) * 0.3 + np.sin(2 * np.pi * 7800 * t) * 0.05
    e = np.minimum(1.0, t / 0.15) * (0.55 * np.exp(-t / 1.6) + 0.45 * np.exp(-t / 4.5))
    hiss = hp(noise(d), 6000) * 0.04 * e
    return norm(x * e + hiss, 0.6)


def smoke_hiss():
    d = 4.0
    x = noise(d)
    h = bp(x, 1800, 9000) * 0.8 + bp(x, 400, 1800) * 0.35
    # slow sputter of the burning composition
    t = np.arange(int(d * SR)) / SR
    mod = 0.8 + 0.2 * np.sin(2 * np.pi * 2.3 * t) * np.sin(2 * np.pi * 0.7 * t + 1)
    for i in range(30):
        at = rng.uniform(0, d - 0.05)
        j = int(at * SR)
        s = bp(noise(0.03), 600, 3000) * env(0.03, 0.002, 0.008) * rng.uniform(0.3, 0.7)
        h[j:j + len(s)] += s
    h *= mod
    # crossfade the ends so the clip loops without a click
    f = int(0.25 * SR)
    w = np.linspace(0, 1, f)
    h[:f] = h[:f] * w + h[-f:] * (1 - w)
    return norm(h[:-f], 0.55)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    write('grenade_pin', pin())
    write('grenade_throw', throw())
    for k in range(3):
        write('grenade_bounce%d' % (k + 1), bounce(k))
    write('grenade_blast', blast())
    write('flashbang', flashbang())
    write('tinnitus', tinnitus())
    write('smoke_hiss', smoke_hiss())
