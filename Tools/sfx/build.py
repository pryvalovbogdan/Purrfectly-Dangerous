#!/usr/bin/env python3
"""Generates the game's sound effects as small 8-bit-flavoured WAV files and the menu theme as AAC
(standard library plus macOS `afconvert`; a WAV theme alone would be over a megabyte of the app).

Everything is synthesised from fixed formulas and a fixed-seed noise generator, so every run writes
byte-identical WAVs. The names match `Sound` in App/Audio/Sound.swift.
"""
import math
import struct
import subprocess
import wave
from pathlib import Path

import music

RATE = 22050
OUT = Path(__file__).resolve().parents[2] / "App" / "Resources" / "Sounds"


class Noise:
    """Fixed-seed white noise: the same samples on every build."""

    def __init__(self, seed: int = 0x1234):
        self.state = seed

    def __call__(self) -> float:
        self.state = (self.state * 1103515245 + 12345) & 0x7FFFFFFF
        return self.state / 0x3FFFFFFF - 1


def envelope(i: int, count: int, attack: float = 0.004, release: float = 1.0) -> float:
    """Quick fade-in, then a fade-out over the last `release` share of the sound."""
    rise = min(1.0, i / RATE / attack) if attack > 0 else 1.0
    return rise * min(1.0, (count - i) / max(1, count * release))


def tone(start_hz: float, end_hz: float, seconds: float, shape: str = "square", volume: float = 0.5,
         duty: float = 0.5, curve: float = 1.0, vibrato: float = 0.0) -> list[float]:
    """A pitch sweep with a fade-out. `curve` below 1 moves the pitch fast first; shapes: square,
    triangle, sine."""
    samples, phase = [], 0.0
    count = int(RATE * seconds)
    for i in range(count):
        t = i / count
        hz = (start_hz + (end_hz - start_hz) * t ** curve) * (1 + vibrato * math.sin(2 * math.pi * 28 * i / RATE))
        phase += hz / RATE
        if shape == "square":
            value = 1.0 if phase % 1 < duty else -1.0
        elif shape == "triangle":
            value = 4 * abs(phase % 1 - 0.5) - 1
        else:
            value = math.sin(2 * math.pi * phase)
        samples.append(value * volume * envelope(i, count))
    return samples


def meow(points: list[tuple[float, float]], seconds: float, volume: float = 0.45, duty: float = 0.3,
         bright: float = 0.6) -> list[float]:
    """A pitch gliding through (time share, hz) points, voiced like a small cat: a soft pulse and a
    triangle through a filter that opens in the middle and closes at the end ("m-ia-ow")."""
    count = int(RATE * seconds)
    samples, phase, low = [], 0.0, 0.0
    for i in range(count):
        t = i / count
        hz = points[-1][1]
        for (t0, h0), (t1, h1) in zip(points, points[1:]):
            if t0 <= t <= t1:
                hz = h0 + (h1 - h0) * (t - t0) / max(t1 - t0, 1e-6)
                break
        phase += hz / RATE
        raw = 0.55 * (1.0 if phase % 1 < duty else -1.0) + 0.45 * (4 * abs(phase % 1 - 0.5) - 1)
        low += (math.sin(math.pi * min(1.0, t * 1.15)) * bright + 0.08) * (raw - low)
        samples.append(low * volume * envelope(i, count, attack=0.012, release=0.45))
    return samples


def whoosh(seconds: float, start: float, end: float, volume: float = 0.5, seed: int = 7) -> list[float]:
    """Band-limited noise whose brightness sweeps from `start` to `end` (0..1), swelling in the middle."""
    noise = Noise(seed)
    count = int(RATE * seconds)
    samples, low, lower = [], 0.0, 0.0
    for i in range(count):
        t = i / count
        cut = start + (end - start) * t
        low += cut * (noise() - low)
        lower += 0.5 * cut * (low - lower)
        samples.append((low - lower * 0.6) * volume * 2.2 * math.sin(math.pi * t) ** 1.5)
    return samples


def burst(seconds: float, volume: float, decay: float, rough: float = 1.0, seed: int = 3) -> list[float]:
    """A noise hit that dies away; `rough` below 1 holds each value longer for a grittier sound."""
    noise = Noise(seed)
    step = max(1, int(1 / max(rough, 0.05)))
    samples, held = [], 0.0
    for i in range(int(RATE * seconds)):
        if i % step == 0:
            held = noise()
        samples.append(held * volume * math.exp(-i / RATE * decay))
    return samples


def thud(start_hz: float, end_hz: float, seconds: float, volume: float = 0.8) -> list[float]:
    """A soft low drum: a sine that drops in pitch and dies away."""
    samples, phase = [], 0.0
    for i in range(int(RATE * seconds)):
        t = i / RATE
        phase += (end_hz + (start_hz - end_hz) * math.exp(-t * 30)) / RATE
        samples.append(math.sin(2 * math.pi * phase) * volume * math.exp(-t * 14))
    return samples


def chime(hz: float, seconds: float, volume: float = 0.4, decay: float = 6.0,
          partials: tuple[tuple[float, float], ...] = ((1, 1), (2.0, 0.35), (3.01, 0.15))) -> list[float]:
    """A bell-like note: a few sine partials dying away, the higher ones faster."""
    samples = []
    for i in range(int(RATE * seconds)):
        t = i / RATE
        value = sum(weight * math.sin(2 * math.pi * hz * ratio * t) * math.exp(-t * decay * ratio ** 0.5)
                    for ratio, weight in partials)
        samples.append(value * volume * min(1.0, t / 0.002))
    return samples


def later(samples: list[float], seconds: float) -> list[float]:
    return [0.0] * int(RATE * seconds) + samples


def mix(*layers: list[float]) -> list[float]:
    out = [0.0] * max(len(layer) for layer in layers)
    for layer in layers:
        for i, value in enumerate(layer):
            out[i] += value
    return out


def write(name: str, *parts: list[float]) -> None:
    samples = [s for part in parts for s in part]
    # Layered sounds can add up past full scale; bring those down instead of clipping them.
    peak = max((abs(s) for s in samples), default=0)
    if peak > 0.9:
        samples = [s * 0.9 / peak for s in samples]
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, s)) * 32000)) for s in samples))


def main() -> None:
    # The kitten: chirps and meows rather than beeps.
    write("jump", meow([(0, 620), (0.45, 940), (1, 820)], 0.13, volume=0.42))
    write("double_jump", meow([(0, 820), (0.35, 1320), (0.7, 1180), (1, 1260)], 0.15, volume=0.4, duty=0.2))
    write("yarn", mix(whoosh(0.2, 0.08, 0.5, 0.55, seed=11), tone(520, 300, 0.08, "triangle", 0.12)))
    write("dash", mix(whoosh(0.28, 0.6, 0.06, 0.6, seed=23), tone(1400, 500, 0.22, "sine", 0.08)))
    write("pounce", mix(tone(180, 640, 0.14, "square", 0.25, duty=0.25, curve=0.6), whoosh(0.22, 0.15, 0.4, 0.35, seed=5)))
    write("thump", mix(thud(140, 48, 0.22, 0.9), burst(0.08, 0.25, 40, rough=0.25)))
    write("hurt", meow([(0, 760), (0.25, 900), (1, 380)], 0.3, volume=0.5, duty=0.4, bright=0.8))
    write("stomp", mix(thud(260, 120, 0.12, 0.7), tone(300, 520, 0.08, "triangle", 0.25)))
    # Pickups and hits.
    write("fish", mix(chime(1568, 0.25, 0.28, 10), later(chime(2093, 0.25, 0.26, 10), 0.05),
                      later(chime(2637, 0.3, 0.24, 9), 0.1)))
    write("impact", mix(burst(0.09, 0.4, 45, rough=0.5, seed=9), tone(420, 200, 0.06, "triangle", 0.25)))
    write("block", chime(1900, 0.09, 0.3, 40, ((1, 1), (2.7, 0.4))))
    write("crash", mix(burst(0.45, 0.6, 9, rough=0.2, seed=31), thud(110, 40, 0.3, 0.8),
                       later(burst(0.1, 0.4, 30, rough=0.3, seed=32), 0.09),
                       later(burst(0.1, 0.3, 30, rough=0.3, seed=33), 0.18)))
    write("curl", mix(*[later(burst(0.03, 0.25, 80, seed=40 + n), n * 0.035) for n in range(4)]))
    # The world.
    write("cannon", mix(thud(120, 45, 0.25, 0.8), burst(0.22, 0.45, 16, rough=0.3, seed=51)))
    write("bell", mix(chime(660, 0.7, 0.35, 3.5, ((1, 1), (2.76, 0.45), (5.4, 0.2))), chime(664, 0.7, 0.2, 3.5, ((1, 1),))))
    write("flame", mix(whoosh(0.35, 0.05, 0.3, 0.6, seed=61), burst(0.35, 0.18, 6, rough=0.15, seed=62)))
    write("slam", mix(thud(160, 40, 0.25, 1.0), chime(300, 0.2, 0.18, 18, ((1, 1), (2.3, 0.6)))))
    write("shatter", mix(burst(0.25, 0.35, 14, seed=71),
                         *[later(chime(2200 + 340 * n, 0.12, 0.13, 30), 0.03 * n) for n in range(4)]))
    write("crumble", mix(*[later(burst(0.07, 0.3, 40, rough=0.2, seed=80 + n), n * 0.06) for n in range(5)]))
    # Bosses and the end of a level.
    write("boss_hit", mix(burst(0.16, 0.6, 22, rough=0.4, seed=91), tone(240, 90, 0.16, "square", 0.25, duty=0.3)))
    write("boss_roar", mix(burst(0.6, 0.5, 4, rough=0.08, seed=97), tone(150, 70, 0.6, "square", 0.25, duty=0.3, vibrato=0.08)))
    write("level_up", *[tone(hz, hz, 0.08, "square", 0.35, duty=0.25) for hz in (523, 659, 784)],
          mix(tone(1047, 1047, 0.25, "square", 0.35, duty=0.25), chime(2093, 0.3, 0.15, 8)))
    write("win", *[tone(hz, hz, 0.1, "triangle", 0.5) for hz in (523, 659, 784)],
          meow([(0, 1047), (0.6, 1175), (1, 1047)], 0.4, volume=0.5))
    write("lose", tone(392, 392, 0.14, "triangle", 0.45), tone(330, 330, 0.14, "triangle", 0.45),
          meow([(0, 520), (0.3, 600), (1, 260)], 0.55, volume=0.45, duty=0.4))

    write("menu_theme", music.render())
    wav, m4a = OUT / "menu_theme.wav", OUT / "menu_theme.m4a"
    subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", "-b", "48000", str(wav), str(m4a)], check=True)
    wav.unlink()
    print(f"wrote sounds to {OUT}")


if __name__ == "__main__":
    main()
