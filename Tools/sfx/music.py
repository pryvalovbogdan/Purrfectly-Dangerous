"""The start and end screens' theme: an original, loopable, cosy chiptune (standard library only).

Warm and unhurried, like a cat asleep in the sun: F major at 96 BPM with a gentle swing, a soft
triangle-and-pulse lead, music-box arpeggios, a round triangle bass and brushed drums. Under it all
runs a low "purr": filtered noise pulsing at about 24 times a second, breathing in and out with each
bar. The loop is rendered so its end runs straight into its start, and every sound comes from fixed
formulas and a fixed-seed noise generator, so the track is identical on every build.
"""
import math

RATE = 22050
BPM = 96
EIGHTH = 60 / BPM / 2
BAR = EIGHTH * 8
SWING = 0.12  # share of an eighth that off-beat eighths are pushed late

# Chords as (bass root midi, chord tones for the arpeggio).
CHORDS = {
    "F": (41, [65, 69, 72, 77]),
    "Dm": (38, [62, 65, 69, 74]),
    "Bb": (46, [62, 65, 70, 74]),
    "C": (36, [60, 64, 67, 72]),
    "Am": (45, [60, 64, 69, 72]),
    "Gm": (43, [62, 67, 70, 74]),
}

# Lead melody, one bar per line: (midi note or None for a rest, length in eighths).
A = [
    [(72, 3), (69, 1), (70, 2), (72, 2)],
    [(74, 4), (72, 2), (69, 2)],
    [(70, 3), (69, 1), (67, 2), (65, 2)],
    [(67, 6), (None, 2)],
    [(72, 3), (69, 1), (70, 2), (72, 2)],
    [(77, 4), (76, 2), (74, 2)],
    [(72, 2), (70, 2), (69, 2), (67, 2)],
    [(65, 6), (None, 2)],
]
B = [
    [(69, 2), (70, 2), (72, 4)],
    [(74, 3), (72, 1), (70, 4)],
    [(67, 2), (69, 2), (70, 4)],
    [(72, 6), (None, 2)],
    [(74, 2), (76, 2), (77, 4)],
    [(76, 3), (74, 1), (72, 4)],
    [(70, 2), (69, 2), (67, 2), (64, 2)],
    [(65, 4), (None, 4)],
]
VERSE = ["F", "Dm", "Bb", "C", "F", "Dm", "Gm", "C"]
BRIDGE = ["Bb", "Gm", "C", "Am", "Bb", "C", "Gm", "F"]
SONG = [(A, VERSE), (B, BRIDGE)]


def hz(midi: float) -> float:
    return 440 * 2 ** ((midi - 69) / 12)


class Noise:
    """A fixed-seed generator, so the track is identical on every build."""

    def __init__(self, seed: int):
        self.state = seed

    def __call__(self) -> float:
        self.state = (self.state * 1103515245 + 12345) & 0x7FFFFFFF
        return self.state / 0x3FFFFFFF - 1


def swung(step: int) -> float:
    """Start of eighth `step` within a bar, in seconds, with the off-beats pushed late."""
    return step * EIGHTH + (SWING * EIGHTH if step % 2 else 0)


def render() -> list[float]:
    bars = sum(len(melody) for melody, _ in SONG)
    length = int(RATE * BAR * bars)
    lead = [0.0] * length
    rest = [0.0] * length

    def add(buffer, start_s, samples):
        start = int(start_s * RATE)
        for i, value in enumerate(samples):
            buffer[(start + i) % length] += value  # wraps, so tails ring into the loop's start

    def soft_lead(midi, seconds, volume):
        """Triangle with a little narrow pulse on top, a slow attack and a late, gentle vibrato."""
        count = int(seconds * RATE)
        out, phase = [], 0.0
        for i in range(count):
            t = i / RATE
            bend = 0.15 * math.sin(2 * math.pi * 5 * t) * min(1, max(0, t - 0.18) / 0.2)
            phase += hz(midi + bend) / RATE
            wave = 0.75 * (4 * abs(phase % 1 - 0.5) - 1) + 0.25 * (1 if phase % 1 < 0.125 else -1)
            env = min(1, t / 0.03) * min(1, (seconds - t) / 0.08) * (0.7 + 0.3 * math.exp(-t * 4))
            out.append(wave * volume * env)
        return out

    def music_box(midi, start_s, volume):
        """A plucked sine with a bright overtone, dying away like a music box tine."""
        count = int(0.6 * RATE)
        out = []
        for i in range(count):
            t = i / RATE
            out.append((math.sin(2 * math.pi * hz(midi) * t) + 0.3 * math.sin(2 * math.pi * hz(midi) * 4 * t)
                        * math.exp(-t * 18)) * volume * math.exp(-t * 7) * min(1, t / 0.002))
        add(rest, start_s, out)

    def bass(midi, seconds, start_s, volume):
        count = int(seconds * RATE)
        out, phase = [], 0.0
        for i in range(count):
            t = i / RATE
            phase += hz(midi) / RATE
            env = min(1, t / 0.01) * min(1, (seconds - t) / 0.05) * (0.6 + 0.4 * math.exp(-t * 5))
            out.append((4 * abs(phase % 1 - 0.5) - 1) * volume * env)
        add(rest, start_s, out)

    noise = Noise(0xCA7)

    def drum(kind, start_s):
        if kind == "kick":
            count, out, phase = int(0.18 * RATE), [], 0.0
            for i in range(count):
                t = i / RATE
                phase += (45 + 70 * math.exp(-t * 30)) / RATE
                out.append(math.sin(2 * math.pi * phase) * 0.45 * math.exp(-t * 16))
        else:
            # Brushes: soft, filtered noise.
            seconds, volume, decay = {"brush": (0.16, 0.12, 18), "tap": (0.05, 0.05, 70)}[kind]
            count, out, low = int(seconds * RATE), [], 0.0
            for i in range(count):
                low += 0.35 * (noise() - low)
                out.append(low * volume * math.exp(-i / RATE * decay) * min(1, i / RATE / 0.01))
        add(rest, start_s, out)

    bar_start = 0.0
    for melody, chords in SONG:
        for notes, chord in zip(melody, chords):
            root, tones = CHORDS[chord]
            step = 0
            for midi, eighths in notes:
                start = bar_start + swung(step)
                seconds = swung(step + eighths) - swung(step)
                if midi is not None:
                    add(lead, start, soft_lead(midi, seconds * 0.95, 0.2))
                step += eighths
            # music box: up the chord on the eighths, an octave up
            for step, index in enumerate([0, 1, 2, 3, 2, 1, 2, 3]):
                music_box(tones[index] + 12, bar_start + swung(step), 0.05)
            # bass: root on 1, fifth on 3 with a walk-up pickup
            bass(root, EIGHTH * 3, bar_start, 0.3)
            bass(root + 7, EIGHTH * 2, bar_start + swung(4), 0.26)
            bass(root + 12, EIGHTH, bar_start + swung(7), 0.2)
            # kick on 1 and 3, brush on 2 and 4, taps on the swung off-beats
            for step in range(8):
                start = bar_start + swung(step)
                if step in (0, 4):
                    drum("kick", start)
                if step in (2, 6):
                    drum("brush", start)
                if step % 2:
                    drum("tap", start)
            bar_start += BAR

    # the purr: low noise, amplitude-pulsed ~24 Hz, swelling in (inhale) and out (exhale) each bar
    purr_noise = Noise(0x9ED)
    low = lower = 0.0
    for i in range(length):
        t = i / RATE
        low += 0.05 * (purr_noise() - low)
        lower += 0.05 * (low - lower)
        breath = 0.5 - 0.5 * math.cos(2 * math.pi * (t / BAR))
        flutter = 0.55 + 0.45 * math.sin(2 * math.pi * 24 * t)
        rest[i] += lower * 1.6 * flutter * (0.35 + 0.65 * breath)

    # a soft echo on the lead, run twice round the loop so the start hears the end
    delay = int(EIGHTH * 3 * RATE)
    echo = [0.0] * length
    for _ in range(2):
        for i in range(length):
            echo[i] = lead[i] + 0.3 * echo[(i - delay) % length]
    mix = [echo[i] + rest[i] for i in range(length)]

    # warm low-pass, also run round the loop
    smoothed, value = [0.0] * length, 0.0
    for _ in range(2):
        for i in range(length):
            value += 0.35 * (mix[i] - value)
            smoothed[i] = value
    peak = max(abs(s) for s in smoothed) or 1
    return [s / peak * 0.85 for s in smoothed]
