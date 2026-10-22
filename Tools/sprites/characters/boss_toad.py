"""Sakura route level 2 boss: the Lantern Toad Guardian (150x120; about 100 tall to the lantern's roof).

No boss sheet; designed for the sunset world (docs/concept/Sakura World Level 2 Tileset Sheet.png) in the Blossom
Kitsune's style: a big round temple-guardian toad, moss-green on top and teal underneath, rim-lit warm by the sunset,
a cream belly, warts and blossoms on its back, big golden eyes, a red rope collar with gold trim and white paper
streamers, and a stone shrine lantern sitting on its head with a glowing window. Lashes a long tongue, spits arcing
lanterns, and leaps to slam the ground so rocks and pink blossom energy burst up."""
from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image

import palette as P
from bosskit import blob, flame, part, tube
from characters.boss_kitsune import blossom, glow, petal
from draw import Canvas, noise, r, see_through, tint
from sprite import Sprite

SIZE = (150, 120)
CX, GROUND = 66, 116
# Suggested hitbox: 60 wide x 60 tall on the ground (baseY 0), centred on CX: the round body and head. The lantern,
# hind foot and tongue stick out. This is the size Bosses.json already gives.
HITBOX = (60, 60)

EDGE = P.TD_LINE
MOSS = {P.TD_MOSS: (P.TD_SUN, P.TD_MOSS_D)}
MOSS2 = {P.TD_MOSS_D: (None, P.TD_TEAL)}
BELLY = {P.TD_BELLY: (P.WHITE, P.TD_BELLY_D)}
STONE = {P.TD_STONE: (P.TD_STONE_L, P.TD_STONE_D)}
ROPE = {P.SK_LACQUER: (P.CAPE_L, P.SK_LACQUER_D)}


@dataclass
class ToadPose:
    step: int = 0
    lift: float = 0             # off the ground (slam leap)
    squash: float = 0           # flattened and widened (landing), negative = stretched (take-off)
    breathe: float = 0          # throat puffing
    jaw: float = 0              # 0 shut ... 1 wide open
    tongue: float = 0           # tongue lashed out, 0 ... 1 (full reach)
    flame: float = 0.5          # lantern window glow 0...1
    eye: str = "open"           # open | wide | narrow | shut | x
    lean: float = 0             # head and front pushed forward
    lantern_tilt: float = 0     # degrees
    lantern_off: float = 0      # the lantern sliding off its head (death), 0...1
    spit: int = 0               # a lantern leaving the mouth (frame index + 1)
    burst: int = 0              # slam impact: rocks and pink energy (frame index + 1)


def stone_lantern(c: Canvas, x: float, base: float, flame: float, tilt: float, step: int, light: Canvas) -> None:
    """A small stone shrine lantern standing on (x, base): foot, post, firebox with a glowing window, a pointed roof
    with up-curled eaves and a knob."""
    lay = Canvas(*c.size)
    with part(lay, STONE, EDGE, up=1, down=1, left=1, right=1) as k:
        k.rect(x - 7, base - 3, x + 7, base, P.TD_STONE)                 # foot
        k.rect(x - 3, base - 9, x + 3, base - 3, P.TD_STONE)             # post
        k.rect(x - 6, base - 11, x + 6, base - 9, P.TD_STONE)            # platform
        k.rect(x - 5, base - 21, x + 5, base - 11, P.TD_STONE)           # firebox
        k.poly([(x - 11, base - 21), (x - 9, base - 24), (x, base - 30), (x + 9, base - 24), (x + 11, base - 21)],
               P.TD_STONE)                                                # roof
        k.ellipse(x, base - 31, 2, 2, P.TD_STONE)                         # knob
    lay.px(x - 11, base - 22, P.TD_STONE_L)                               # eaves curling up
    lay.px(x + 11, base - 22, P.TD_STONE_L)
    lay.rect(x - 3, base - 19, x + 3, base - 13, P.TD_FIRE_D if flame < 0.6 else P.TD_FIRE)   # the window
    lay.rect(x - 1, base - 18, x + 1, base - 14, P.TD_FIRE if flame < 0.6 else P.WHITE)
    lay.line((x, base - 19), (x, base - 13), P.TD_STONE_D)              # its lattice
    lay.px(x - 4, base - 6, P.TD_MOSS)                                     # moss on the stone
    lay.px(x + 5, base - 2, P.TD_MOSS)
    lay.px(x + 6, base - 2, P.TD_MOSS_L)
    if tilt:
        img = lay.img.rotate(-tilt, resample=Image.NEAREST, center=(x, base))
    else:
        img = lay.img
    light.ellipse(x, base - 16, 6 + flame * 3, 5 + flame * 3, P.TD_FIRE)       # glow, laid under the outline
    c.paste(img)


def toad(pose: ToadPose) -> Image.Image:
    c = Canvas(*SIZE)
    light = Canvas(*SIZE)
    effects = Canvas(*SIZE)
    g = GROUND - pose.lift
    sq = pose.squash
    ln = pose.lean
    w = 1 + sq * 0.02                                                     # width factor
    by = g - 30 + sq * 0.6                                               # body centre
    hx, hy = CX + 22 + ln, g - 44 + sq * 0.8 - pose.breathe * 0.3        # head centre (front of the body)

    # Hind leg folded at the back, the far front foot.
    with part(c, MOSS, EDGE, up=2, down=3, left=2, right=2, ramp2=MOSS2) as k:
        blob(k, CX - 26 * w, g - 14, 14 * w, 13, P.TD_MOSS, 1300, 8, 2.5)
        k.ellipse(CX - 18 * w, g - 3, 15 * w, 3.5, P.TD_MOSS)
        k.ellipse(CX + 38 * w + ln, g - 3, 7, 3, P.TD_MOSS_D)
    for i in range(3):                                                    # webbed toes on the hind foot
        c.line((CX - 6 * w + i * 4, g - 3), (CX - 4 * w + i * 4, g), P.TD_MOSS_D)

    # The round body.
    with part(c, MOSS, EDGE, up=4, down=6, left=4, right=5, ramp2=MOSS2) as k:
        blob(k, CX, by, 38 * w, 28 - sq * 0.5, P.TD_MOSS, 1301, 16, 3)
        blob(k, hx - 2, hy, 22 * w, 16 - sq * 0.3, P.TD_MOSS, 1302, 10, 2.5)
    rnd = noise(1310)
    for i in range(14):                                                   # warts on the back
        x, y = CX - 32 + rnd() * 52, by - 24 + rnd() * 24
        if c.img.getpixel((r(x), r(y)))[3]:
            c.ellipse(x, y, 1.6, 1.3, P.TD_MOSS_D)
            c.px(x - 0.5, y - 0.8, P.TD_MOSS_L)
    for i, (x, y) in enumerate(((CX - 20, by - 22), (CX - 4, by - 26), (CX - 30, by - 8))):   # blossoms on its back
        blossom(c, x, y + sq * 0.3, 3.2, i * 0.7 + pose.step * 0.15)

    # Cream belly and throat; the throat puffs out.
    with part(c, BELLY, EDGE, down=3, right=2) as k:
        k.ellipse(CX + 18 * w + ln * 0.5, g - 16, 18 * w, 12 - sq * 0.3, P.TD_BELLY)
        k.ellipse(hx + 6, hy + 11, 13 + pose.breathe * 2, 5 + pose.breathe * 2.5, P.TD_BELLY)
    for i in range(3):
        c.line((CX + 8 + i * 6, g - 22), (CX + 10 + i * 6, g - 10), P.TD_BELLY_D)

    # Mouth: a long wide line; open, a dark mouth with a pink tongue.
    jaw = pose.jaw * 10
    mx0, my = hx - 12, hy + 5
    if pose.jaw > 0.1:
        with part(c, {P.TD_TONGUE_D: (P.TD_TONGUE, None)}, EDGE) as k:
            k.poly([(mx0, my), (hx + 22, my - 2), (hx + 20, my + jaw), (mx0 + 6, my + jaw * 0.6)], P.TD_TONGUE_D)
        c.poly([(mx0 + 3, my + 1), (hx + 19, my - 1), (hx + 17, my + jaw - 1), (mx0 + 8, my + jaw * 0.6 - 1)],
               P.MAROON)
    else:
        c.line((mx0, my), (hx + 21, my - 2), EDGE)
        c.line((hx + 21, my - 2), (hx + 23, my - 4), EDGE)
    if pose.tongue:
        reach = SIZE[0] - 11 - (hx + 18)
        tx = hx + 18 + reach * pose.tongue
        ty = g - 6 if pose.tongue > 0.5 else my + jaw * 0.5
        with part(c, {P.TD_TONGUE: (P.SK_PINK_L, P.TD_TONGUE_D)}, EDGE, up=1, down=1, left=1, right=1) as k:
            tube(k, [(hx + 14, my + jaw * 0.4, 3.5), ((hx + 14 + tx) / 2, (my + ty) / 2 + 2, 2.8), (tx, ty, 3)],
                 P.TD_TONGUE)
            k.ellipse(tx, ty, 4.5, 4, P.TD_TONGUE)
        c.px(tx - 1, ty - 2, P.WHITE)

    # Front leg, chunky, toes spread.
    fx = CX + 30 * w + ln
    with part(c, MOSS, EDGE, up=2, down=2, left=1, right=2, ramp2=MOSS2) as k:
        k.line((fx - 6, g - 22 + sq * 0.5), (fx, g - 4), P.TD_MOSS, 8)
        k.ellipse(fx + 3, g - 3, 8, 3.5, P.TD_MOSS)
    for i in range(3):
        c.ellipse(fx + i * 4, g - 1, 1.5, 1.2, P.TD_MOSS_L)

    # Rope collar with gold trim and zig-zag paper streamers.
    with part(c, ROPE, EDGE, up=1, down=1) as k:
        tube(k, [(hx - 22, hy + 13, 2.4), (hx - 2, hy + 20, 2.6), (hx + 14, hy + 18, 2.4)], P.SK_LACQUER)
    for i in range(7):                                                   # gold-wrapped rope ticks
        t = i / 6
        x = hx - 22 + t * 36
        y = hy + 13 + math.sin(t * math.pi * 0.9) * 7 - t * 1
        c.px(x, y, P.GOLD)
    for sx in (hx - 8, hx + 8):                                         # shide: folded paper streamers
        top = hy + 21
        c.poly([(sx, top), (sx + 3, top), (sx + 3, top + 3), (sx + 1, top + 3), (sx + 1, top + 6), (sx + 4, top + 6),
                (sx + 4, top + 9), (sx + 1, top + 9)], P.WHITE)
        c.line((sx + 3, top + 1), (sx + 3, top + 3), P.SK_RICE_D)

    # The shrine lantern sitting on its head, tipping as it hops, sliding off when it dies.
    lx = hx - 1 + pose.lantern_off * 26
    lbase = hy - 15 + pose.lantern_off * (g - (hy - 15))
    stone_lantern(c, lx, lbase, pose.flame, pose.lantern_tilt + pose.lantern_off * 70, pose.step, light)

    # Eyes: two big golden domes bulging up from the top of the head.
    for i, (ex, ey) in enumerate(((hx - 10, hy - 13), (hx + 8, hy - 14))):
        with part(c, MOSS, EDGE, up=2, down=1, left=1, right=1, ramp2=MOSS2) as k:
            k.ellipse(ex, ey, 8, 7, P.TD_MOSS)
        if pose.eye in ("open", "wide", "narrow"):
            h = {"open": 1.0, "wide": 1.25, "narrow": 0.45}[pose.eye]
            c.ellipse(ex + 1, ey, 5.5, 5 * h, P.TD_EYE)
            c.ellipse(ex + 2, ey + 1, 4, 3.5 * h, P.GOLD)
            c.rect(ex, ey - 2 * h, ex + 3, ey + 1.5 * h, EDGE)          # wide toad pupil
            c.px(ex - 1, ey - 2 * h, P.WHITE)
            if pose.eye == "narrow":
                c.line((ex - 5, ey - 2), (ex + 6, ey - 3), P.TD_MOSS_D, 2)
        elif pose.eye == "shut":
            c.line((ex - 5, ey + 1), (ex + 6, ey), EDGE)
        else:
            c.line((ex - 2, ey - 3), (ex + 4, ey + 3), EDGE)
            c.line((ex - 2, ey + 3), (ex + 4, ey - 3), EDGE)
    c.ellipse(hx + 18, hy - 3, 1, 0.8, EDGE)                             # nostril

    if pose.spit:                                                         # a lantern leaving the mouth, arcing up
        sx, sy = hx + 22 + pose.spit * 6, my - 4 - pose.spit * 6
        lantern_ball(c, sx, sy, pose.step, halo=False)
        for i in range(3):
            c.px(sx - 6 - i * 3, sy + 3 + i * 2, P.TD_FIRE)
    if pose.burst:
        rnd = noise(1320 + pose.burst)
        energy = Canvas(*SIZE)                                          # laid over the outline (light has no edge)
        for i in range(10):                                             # pink blossom energy shooting up
            x = CX - 50 + i * 12 + rnd() * 4
            h = (34 + rnd() * 30) * (1.0 if pose.burst < 3 else 0.6)
            flame(energy, x, GROUND, h, 4 + rnd() * 2, pose.burst + i, 1330 + i,
                  colours=(P.KT_MAGENTA, P.SK_PINK, P.SK_PINK_L, P.WHITE))
            blossom(energy, x + (rnd() - 0.5) * 4, GROUND - h - 3, 2.5, i)
        effects.paste(energy.img)
        for i in range(5):                                              # rocks flung up
            x = CX - 40 + i * 20 + rnd() * 6
            y = GROUND - 10 - pose.burst * (8 + i % 3 * 5) + pose.burst ** 2 * 1.5
            rock(c, x, y, 2.5 + (i % 2), i)
        for i in range(8):
            petal(c, CX - 40 + rnd() * 90, GROUND - 4 - rnd() * 40, i)

    c.rect(0, GROUND + 1, SIZE[0] - 1, SIZE[1] - 1, P.CLEAR)
    c.outline(EDGE)
    out = see_through(light.img, r(30 + 60 * pose.flame))
    out.alpha_composite(see_through(effects.img, 220))           # the burst behind it
    out.alpha_composite(c.img)
    effects = Canvas(*SIZE)
    effects.rect(0, GROUND + 1, SIZE[0] - 1, SIZE[1] - 1, P.CLEAR)
    out.alpha_composite(effects.img)
    return out


def lantern_ball(c: Canvas, x: float, y: float, step: int, halo: bool = True) -> None:
    """A small round paper lantern, glowing (what the toad spits)."""
    if halo:
        glow(c, x, y, 6, 90, P.TD_FIRE_D)
    with part(c, {P.SK_LACQUER: (P.CAPE_L, P.SK_LACQUER_D)}, EDGE, up=1, down=1, left=1, right=1) as k:
        k.ellipse(x, y, 4, 3.6, P.SK_LACQUER)
    c.rect(x - 2, y - 4, x + 2, y - 4, P.GOLD)
    c.rect(x - 2, y + 4, x + 2, y + 4, P.GOLD)
    c.ellipse(x, y, 1.6, 2, P.TD_FIRE if step % 2 else P.YELLOW)
    c.line((x - 4, y), (x + 4, y), P.SK_LACQUER_D)


def rock(c: Canvas, x: float, y: float, s: float, seed: int) -> None:
    """A chunk of mossy stone."""
    with part(c, STONE, EDGE, up=1, down=1, left=1, right=1) as k:
        k.poly([(x - s * 1.2, y + s), (x - s, y - s * 0.7), (x + s * 0.3, y - s * 1.2), (x + s * 1.3, y - s * 0.2),
                (x + s, y + s)], P.TD_STONE)
    c.px(x - s * 0.5, y - s * 0.6, P.TD_MOSS)
    if seed % 2:
        c.px(x + s * 0.4, y - s * 0.8, P.TD_MOSS_L)


def flash(image: Image.Image, amount: float) -> Image.Image:
    out = tint(image, P.WHITE, amount)
    src, dst = image.load(), out.load()
    for y in range(image.height):
        for x in range(image.width):
            if src[x, y] == EDGE:
                dst[x, y] = src[x, y]
    return out


def build() -> list[Sprite]:
    boss = Sprite("boss_toad", SIZE, faces_left=True, cx=CX, ground=GROUND)
    boss.add("idle", [toad(ToadPose(step=k, breathe=(0, 1, 2, 1)[k], flame=(0.5, 0.7, 0.9, 0.6)[k],
                                    eye="shut" if k == 3 else "open")) for k in range(4)], fps=5)

    # Long tongue strike (GameScene: tongue_strike -> "tongue").
    boss.add("tongue", [toad(p) for p in (
        ToadPose(step=0, lean=-3, squash=2, eye="narrow", breathe=2),
        ToadPose(step=1, lean=2, jaw=0.8, eye="wide", tongue=0.2),
        ToadPose(step=2, lean=4, jaw=1, eye="wide", tongue=0.6),
        ToadPose(step=3, lean=5, jaw=1, eye="wide", tongue=1.0),
        ToadPose(step=4, lean=3, jaw=0.8, eye="open", tongue=0.4),
        ToadPose(step=5, lean=0, jaw=0.1, eye="open"),
    )], fps=10, loop=False)

    # Arcing lantern shots (GameScene: lantern_arc -> "lanterns").
    boss.add("lanterns", [toad(p) for p in (
        ToadPose(step=0, flame=0.8, breathe=2, eye="narrow"),
        ToadPose(step=1, flame=1.0, breathe=3, eye="wide", lean=-2),
        ToadPose(step=2, flame=1.0, jaw=1, eye="wide", lean=3, spit=1),
        ToadPose(step=3, flame=0.8, jaw=0.8, eye="wide", lean=2, spit=2),
        ToadPose(step=4, flame=0.6, jaw=0.4, eye="open", spit=3),
        ToadPose(step=5, flame=0.5, eye="open"),
    )], fps=10, loop=False)

    # Leaps and slams the ground: rocks and pink blossom energy burst up (GameScene: area_slam -> "slam").
    boss.add("slam", [toad(p) for p in (
        ToadPose(step=0, squash=5, eye="narrow"),
        ToadPose(step=1, squash=-3, lift=8, eye="wide", lantern_tilt=-6),
        ToadPose(step=2, squash=-2, lift=18, eye="wide", lantern_tilt=-10, jaw=0.3),
        ToadPose(step=3, squash=-1, lift=14, eye="wide", lantern_tilt=8, jaw=0.5),
        ToadPose(step=4, squash=7, eye="shut", jaw=0.6, burst=1, lantern_tilt=6, flame=1.0),
        ToadPose(step=5, squash=5, eye="wide", jaw=0.4, burst=2, flame=1.0),
        ToadPose(step=6, squash=2, eye="open", burst=3, flame=0.8),
        ToadPose(step=7, squash=0, eye="open"),
    )], fps=10, loop=False)

    hurt = toad(ToadPose(step=1, eye="shut", jaw=0.6, lean=-4, lantern_tilt=-12, squash=2, flame=0.2))
    boss.add("hurt", [flash(hurt, 0.6), hurt], fps=10)

    # Sags flat, the lantern topples off and goes out, then it fades into petals.
    frames = [flash(toad(ToadPose(eye="x", jaw=0.5, squash=3)), 0.6)]
    for k in range(1, 8):
        t = k / 7
        body = toad(ToadPose(step=k, eye="x", jaw=0.5, squash=3 + t * 6, lantern_off=min(1.0, t * 1.6),
                             flame=max(0.0, 0.5 - t)))
        frame = Canvas(*SIZE)
        frame.paste(see_through(body, r(255 * (1 - max(0.0, t - 0.35) / 0.65))) if t > 0.35 else body)
        rnd = noise(1340)
        for i in range(int(50 * t)):
            x, y = CX - 40 + rnd() * 90, GROUND - 4 - rnd() * 60 * t
            if 2 <= x < SIZE[0] - 3 and 2 <= y:
                petal(frame, x, y, i + k)
        frames.append(frame.img)
    boss.add("death", frames, fps=8, loop=False)
    return [boss]
