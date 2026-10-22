"""Sakura route level 2 boss: the Sakura Toad Guardian (150x120), after docs/concept/Sakura Toad Guardian Sprite Sheet.png.

A squat crimson toad in three-quarter view facing right, darker red underneath, gold-orange speckles on its haunch and legs,
a cream belly and throat, heavy half-lidded golden eyes and a wide mouth. It wears a wide conical dark-brown straw hat
with gold rim stitching and a gold finial, piled with pink cherry blossoms, with a red paper lantern hanging from each
side of the brim, and a thick gold rope collar with a tassel on its chest. It sits on a mossy rock. Lashes a long
pink tongue with a lantern-ball tip, spits paper lanterns, and leaps to slam the ground so pink energy spikes, petals
and rocks burst out."""
from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image

import palette as P
from bosskit import blob, flame, part, tube
from characters.boss_kitsune import blossom, petal
from draw import Canvas, noise, r, see_through, tint
from sprite import Sprite

SIZE = (160, 136)
CX, GROUND = 76, 132
# Suggested hitbox: 60 wide x 60 tall on the ground (baseY 0), centred on CX: the body and face under the hat
# brim. The hat, lanterns and rock base stick out. This is the size Bosses.json already gives.
HITBOX = (60, 60)

EDGE = P.TD_LINE
RED = {P.TD_RED: (P.TD_RED_L, P.TD_RED_D)}
RED2 = {P.TD_RED_D: (None, P.TD_RED_DD)}
BELLY = {P.TD_BELLY: (P.WHITE, P.TD_BELLY_D)}
HAT = {P.TD_HAT: (P.TD_HAT_L, P.TD_HAT_D)}
ROPE = {P.TD_ROPE: (P.TD_ROPE_L, P.TD_ROPE_D)}
STONE = {P.TD_STONE: (P.TD_STONE_L, P.TD_STONE_D)}
PAPER = {P.TD_PAPER: (P.TD_PAPER_L, P.TD_RED_D)}


@dataclass
class ToadPose:
    step: int = 0
    lift: float = 0             # body off the rock (slam leap)
    squash: float = 0           # flattened (landing), negative = stretched (leap)
    breathe: float = 0          # throat puffing
    lean: float = 0             # face pushed forward (right)
    jaw: float = 0              # mouth open 0...1
    tongue: float = 0           # tongue lashed out 0...1
    charge: float = 0           # pink energy gathering at the mouth (prepare)
    eye: str = "half"           # half | wide | shut | x | star
    hat_tilt: float = 0         # degrees
    hat_off: float = 0          # hat tipping off (death) 0...1
    arms_up: float = 0          # front arms raised (slam leap) 0...1
    walk: float | None = None   # shuffle phase
    spit: int = 0               # a lantern leaving the mouth (frame index + 1)
    burst: int = 0              # slam impact (frame index + 1)
    rock_only: bool = False     # death's end: only the rock is left
    body_alpha: int = 255


def paper_lantern(c: Canvas, x: float, y: float, s: float = 1.0, glow_on: bool = True, crest: bool = True,
                  tall: float = 1.0) -> None:
    """A red paper lantern centred on (x, y), about 8x10 at s=1 (`tall` stretches it into a cylinder): dark caps,
    ribs, a white blossom crest."""
    if glow_on:
        g = Canvas(*c.size)
        g.ellipse(x, y, 6 * s, 6 * s, P.TD_FIRE_D)
        c.paste(see_through(g.img, 70))
    with part(c, PAPER, EDGE, up=1, down=1, left=1, right=1) as k:
        k.ellipse(x, y, 4 * s, 4.6 * s * tall, P.TD_PAPER)
        if tall > 1:
            k.rect(x - 3.6 * s, y - 3 * s * tall, x + 3.6 * s, y + 3 * s * tall, P.TD_PAPER)
    c.rect(x - 2.5 * s, y - 5 * s * tall, x + 2.5 * s, y - 4.2 * s * tall, P.TD_HAT_D)
    c.rect(x - 2.5 * s, y + 4.2 * s * tall, x + 2.5 * s, y + 5 * s * tall, P.TD_HAT_D)
    if s >= 1.2 and crest:
        blossom(c, x, y, 2.6 * s, 0.3, (P.WHITE, P.SK_RICE, P.TD_PAPER))
    elif crest:
        c.ellipse(x, y, 1.5 * s, 1.5 * s, P.WHITE)
        c.px(x, y, P.TD_SPECK)
    for side in (-1, 1):
        c.line((x + side * 2.6 * s, y - 3 * s * tall), (x + side * 2.6 * s, y + 3 * s * tall), P.TD_RED_D)


def lantern_ball(c: Canvas, x: float, y: float, step: int, halo: bool = True) -> None:
    """What the toad spits: a red paper lantern with a white blossom crest."""
    paper_lantern(c, x, y, 1.0 + (step % 2) * 0.05, glow_on=halo)


def rock(c: Canvas, x: float, y: float, s: float, seed: int) -> None:
    """A chunk of dark mossy stone."""
    with part(c, STONE, EDGE, up=1, down=1, left=1, right=1) as k:
        k.poly([(x - s * 1.2, y + s), (x - s, y - s * 0.7), (x + s * 0.3, y - s * 1.2), (x + s * 1.3, y - s * 0.2),
                (x + s, y + s)], P.TD_STONE)
    c.px(x - s * 0.5, y - s * 0.6, P.TD_MOSS)
    if seed % 2:
        c.px(x + s * 0.4, y - s * 0.8, P.TD_MOSS_L)


def base_rock(c: Canvas) -> None:
    """The wide mossy rock base under the whole body: several stones with moss and grass on top."""
    with part(c, STONE, EDGE, up=1, down=2, left=2, right=2) as k:
        for i, (dx, rx, ry) in enumerate(((-44, 12, 6), (-24, 15, 7), (0, 16, 7), (24, 14, 6), (44, 11, 5))):
            blob(k, CX + dx, GROUND - ry + 1, rx, ry, P.TD_STONE, 1400 + i, 7, 1.8)
    for dx in (-34, -12, 12, 34):                                          # cracks between the stones
        c.line((CX + dx, GROUND - 6), (CX + dx + 1, GROUND - 1), P.TD_STONE_D)
    with part(c, {P.TD_MOSS: (P.TD_MOSS_L, P.TD_MOSS_D)}, EDGE, up=1, down=1) as k:
        blob(k, CX, GROUND - 10, 50, 3, P.TD_MOSS, 1406, 18, 2)
    rnd = noise(1407)
    for _ in range(14):                                                    # grass blades and pebbles
        x = CX - 50 + rnd() * 100
        c.line((x, GROUND - 12), (x + rnd() * 2 - 1, GROUND - 15), P.TD_MOSS_L)
        c.px(CX - 50 + rnd() * 100, GROUND - 3 - rnd() * 3, P.TD_STONE_D)


def patches(c: Canvas, box, seed: int, count: int, only=None) -> None:
    """Painted gold-orange speckle patches (2-4 px blobs with a lighter heart) over the red skin inside `box`."""
    rnd = noise(seed)
    reds = [col[:3] for col in (only or (P.TD_RED, P.TD_RED_L, P.TD_RED_D))]
    for _ in range(count):
        x, y = box[0] + rnd() * (box[2] - box[0]), box[1] + rnd() * (box[3] - box[1])
        if c.img.getpixel((r(x), r(y)))[:3] not in reds:
            continue
        rad = 0.8 + rnd() * 1.4
        c.ellipse(x, y, rad + 0.4, rad, P.TD_ROPE_D)
        c.ellipse(x - 0.3, y - 0.3, rad * 0.6, rad * 0.5, P.TD_SPECK)


def blossom_cloud(c: Canvas, cx: float, cy: float, rx: float, ry: float, seed: int, step: int, n: int) -> None:
    """A loose cluster of cherry blossoms: a pink puff with blossoms all over it."""
    rnd = noise(seed)
    pts = [(cx + (rnd() - 0.5) * 2 * rx, cy + (rnd() - 0.5) * 2 * ry, 3.2 + rnd() * 1.6) for _ in range(n)]
    with part(c, {P.SK_PINK: (P.SK_PINK_L, P.KT_MAGENTA)}, P.KT_MAGENTA_D, up=2, down=2, left=1, right=1) as k:
        for x, y, rad in pts:
            k.ellipse(x, y, rad + 0.8, rad * 0.85, P.SK_PINK)
    for i, (x, y, rad) in enumerate(pts):
        blossom(c, x, y - 0.5, rad * 0.8, i * 0.7 + step * 0.1, (P.SK_PINK_L, P.WHITE, P.SK_PINK))


def hat(pose: ToadPose, brim, step: int) -> Image.Image:
    """The straw hat on its own layer (it tilts and tips off): a thick dark woven dome sitting on the head, its wide
    brim drooping at the edges, a gold rim band and finial, loose clouds of blossoms spilling over the top and the
    back side, and a red paper lantern hanging at a different height from each side."""
    c = Canvas(*SIZE)
    bx, by = brim
    rl, rr = 52, 44                                                       # brim reach behind / in front
    with part(c, HAT, EDGE, up=2, down=3, left=2, right=3) as k:
        k.poly([(bx - rl, by + 4), (bx - rl + 8, by - 1), (bx, by - 3), (bx + rr - 8, by - 1), (bx + rr, by + 3),
                (bx + rr - 10, by + 5), (bx, by + 6), (bx - rl + 10, by + 6)], P.TD_HAT)        # drooping brim
        k.ellipse(bx - 3, by - 6, 29, 16, P.TD_HAT)                       # the dome
        k.rect(bx - 32, by - 6, bx + 26, by + 2, P.TD_HAT)
    c.rect(bx - 31, by - 1, bx + 25, by + 1, P.TD_ROPE)                   # gold band round the crown
    c.line((bx - 31, by + 2), (bx + 25, by + 2), P.TD_ROPE_D)
    for i in range(0, 56, 4):                                             # rivets on the band
        c.px(bx - 30 + i, by, P.TD_ROPE_L)
    rnd = noise(1451)
    for _ in range(40):                                                   # the weave: short diagonal strokes
        x, y = bx - 30 + rnd() * 54, by - 20 + rnd() * 18
        if c.img.getpixel((r(x), r(y)))[:3] == P.TD_HAT[:3]:
            d = 1 if (int(x / 3) + int(y / 3)) % 2 else -1
            c.line((x, y), (x + 2 * d, y + 2), P.TD_HAT_D)
            c.px(x + d, y, P.TD_HAT_L)
    for i in range(30):                                                   # gold stitching on the brim edge
        t = i / 29
        x = bx - rl + 3 + t * (rl + rr - 6)
        c.px(x, by + 5 - math.sin(t * math.pi) * 1.5 + (2 if t < 0.08 or t > 0.92 else 0), P.TD_ROPE)
    with part(c, ROPE, EDGE, up=1, down=1, left=1, right=1) as k:          # gold finial
        k.ellipse(bx - 3, by - 24, 2.6, 3, P.TD_ROPE)
        k.rect(bx - 6, by - 22, bx, by - 20, P.TD_ROPE)
    # Loose blossom clouds: a big one on top, one spilling over the back, a small one at the front.
    blossom_cloud(c, bx - 6, by - 18, 15, 5, 1460, step, 12)
    blossom_cloud(c, bx - 30, by - 6, 9, 6, 1461, step, 8)
    blossom_cloud(c, bx - 44, by + 2, 6, 3, 1462, step, 4)
    blossom_cloud(c, bx + 14, by - 14, 6, 4, 1463, step, 4)
    for side, drop in ((-1, 18), (1, 12)):                                # lanterns at different heights
        lx = bx - (rl - 8) if side < 0 else bx + (rr - 6)
        sway = math.sin(step * 0.9 + side) * 1.2
        c.line((lx, by + 5), (lx + sway, by + drop - 6), P.TD_HAT_D)
        paper_lantern(c, lx + sway, by + drop, 1.05, glow_on=False, crest=True, tall=1.35)
        c.line((lx + sway, by + drop + 7), (lx + sway, by + drop + 10), P.TD_ROPE)
    c.outline(EDGE)
    img = c.img
    rot = pose.hat_tilt + pose.hat_off * 40
    if rot:
        img = img.rotate(-rot, resample=Image.NEAREST, center=(bx, by))
    if pose.hat_off:
        moved = Image.new("RGBA", SIZE, P.CLEAR)
        moved.alpha_composite(img, (r(pose.hat_off * 16), r(pose.hat_off * (GROUND - 10 - by))))
        img = moved
    return img


def toad(pose: ToadPose) -> Image.Image:
    out = Canvas(*SIZE)
    base_rock(out)
    out.outline(EDGE)
    if pose.rock_only:
        return out.img
    c = Canvas(*SIZE)
    g = GROUND - 11 - pose.lift                                          # the moss's top
    sq = pose.squash
    w = 1 + sq * 0.025
    ln = pose.lean
    wk = math.sin(pose.walk) * 2 if pose.walk is not None else 0
    hx, hy = CX + 14 + ln, g - 40 + sq * 0.9                             # centre of the big head, turned right
    up = pose.arms_up

    # Far side first, in shadow: the far front arm with its toes, the far eye bulge.
    with part(c, RED, EDGE, up=1, down=2, right=2, ramp2=RED2) as k:
        far = (CX + 44 - wk, g - 3 - up * 36)
        tube(k, [(CX + 34, g - 22, 4.5), (CX + 44, g - 12 - up * 22, 4), (far[0], far[1], 3)], P.TD_RED)
        k.ellipse(far[0] + 2, far[1], 5, 2.8, P.TD_RED)
        k.ellipse(hx - 14, hy - 14, 6.5, 5.5, P.TD_RED)                  # far eye bulge
    for t in range(2):
        c.ellipse(far[0] + 1 + t * 3, far[1] + (1 if not up else -2), 1.2, 1, P.TD_BELLY_D)
    c.img.paste(tint(c.img, P.TD_RED_DD, 0.35))                          # the far side sits in shadow

    # Body behind the head, the cream belly under the jaw.
    with part(c, RED, EDGE, up=4, down=7, left=3, right=6, ramp2=RED2) as k:
        blob(k, CX + 2, g - 24 + sq * 0.5, 30 * w, 22 - sq * 0.5, P.TD_RED, 1412, 14, 3)
    with part(c, BELLY, EDGE, down=3, right=3) as k:
        k.ellipse(CX + 18, g - 11 + sq * 0.3, 17 * w, 10 - sq * 0.3, P.TD_BELLY)
    c.line((CX + 6, g - 6), (CX + 30, g - 4), P.TD_BELLY_D)

    # The big near haunch at the back, its foot pointing forward.
    with part(c, RED, EDGE, up=4, down=6, left=4, right=4, ramp2=RED2) as k:
        blob(k, CX - 22 * w + wk, g - 19, 22 * w, 19, P.TD_RED, 1410, 12, 2.5)
        k.ellipse(CX - 8 + wk, g - 2, 15, 3.2, P.TD_RED)
    for t in range(3):
        c.ellipse(CX + 2 + wk + t * 3.5, g - 1, 1.3, 1, P.TD_BELLY_D)
    hxh, hyh = CX - 22 + wk, g - 21
    c.line((hxh - 14, hyh - 6), (hxh - 4, hyh - 15), P.TD_RED_L)          # rim light on the haunch

    # The huge head: wide, with a big cream jaw spanning the front and a wide mouth line across it.
    with part(c, RED, EDGE, up=4, down=4, left=3, right=4, ramp2=RED2) as k:
        blob(k, hx, hy, 30 * w, 21, P.TD_RED, 1414, 14, 2.5)
    jaw_open = pose.jaw * 9
    with part(c, BELLY, EDGE, down=3, right=2) as k:
        k.ellipse(hx + 5, hy + 9 + jaw_open * 0.5 + pose.breathe * 0.3, 24 + pose.breathe, 10 + pose.breathe,
                  P.TD_BELLY)
    c.line((hx - 14, hy + 15), (hx + 22, hy + 14), P.TD_BELLY_D)          # shading band on the jaw
    mouth_y = hy + 3
    if pose.jaw > 0.1:
        c.poly([(hx - 18, mouth_y), (hx + 30, mouth_y - 2), (hx + 26, mouth_y + jaw_open),
                (hx - 12, mouth_y + jaw_open * 0.8)], P.MAROON)
        c.ellipse(hx + 8, mouth_y + jaw_open * 0.6, 9, jaw_open * 0.35, P.TD_TONGUE)
    else:
        c.line((hx - 22, mouth_y - 3), (hx - 16, mouth_y), EDGE)
        c.line((hx - 16, mouth_y), (hx + 12, mouth_y), EDGE)
        c.line((hx + 12, mouth_y), (hx + 17, mouth_y + 1), EDGE)        # the pout
        c.line((hx + 17, mouth_y + 1), (hx + 29, mouth_y - 3), EDGE)
        c.line((hx - 14, mouth_y + 1), (hx + 26, mouth_y + 1), P.TD_BELLY_D)
    c.px(hx + 26, hy - 7, P.TD_RED_DD)                                   # nostrils
    c.px(hx + 20, hy - 7, P.TD_RED_DD)
    c.line((hx - 24, hy - 12), (hx - 14, hy - 19), P.TD_RED_L)            # rim light on the head top

    # Near front arm, tucked in front of the belly (raised for the slam).
    sh = (CX + 12, g - 22)
    hand = (CX + 24 + 10 * up, g - 3 - up * 44)
    elbow = (CX + 8 + 6 * up, g - 12 - up * 30)
    with part(c, RED, EDGE, up=2, down=3, left=1, right=2, ramp2=RED2) as k:
        tube(k, [(sh[0], sh[1], 5.5), (elbow[0], elbow[1], 4.8), (hand[0], hand[1], 3.4)], P.TD_RED)
        k.ellipse(hand[0] + 1, hand[1], 6, 3, P.TD_RED)
    for t in range(3):
        c.ellipse(hand[0] - 2 + t * 3, hand[1] + (1 if not up else -2), 1.2, 1, P.TD_BELLY_D)

    # Painted gold-orange patches on the haunch, back, head and arm, and a speckle-blossom on the haunch.
    patches(c, (hxh - 20, hyh - 18, hxh + 20, hyh + 18), 1413, 26)
    patches(c, (CX - 20, g - 46, CX + 30, g - 24), 1414, 12)
    patches(c, (hx - 28, hy - 20, hx - 6, hy - 6), 1415, 8)
    patches(c, (CX + 4, g - 26, CX + 40, g - 2), 1416, 10)
    blossom(c, hxh - 2, hyh, 5, 0.3, (P.TD_SPECK, P.TD_ROPE_L, P.TD_RED_D))

    # Gold rope collar under the jaw, across the chest, with the tassel.
    with part(c, ROPE, EDGE, up=1, down=1) as k:
        tube(k, [(hx - 28, hy + 15, 2.8), (hx - 2, hy + 23, 3), (hx + 24, hy + 18, 2.8)], P.TD_ROPE)
    for i in range(10):
        t = i / 9
        x = hx - 28 + t * 52
        y = hy + 15 + math.sin(t * math.pi) * 7 + t * 3
        c.line((x - 1, y - 1), (x + 1, y + 1), P.TD_ROPE_D)
    tx, ty = hx + 2, hy + 25
    with part(c, ROPE, EDGE, up=1, down=1, left=1, right=1) as k:
        k.ellipse(tx, ty, 2.6, 2.6, P.TD_ROPE)
        k.poly([(tx - 2, ty + 2), (tx + 2, ty + 2), (tx + 3.5, ty + 11), (tx - 3.5, ty + 11)], P.TD_ROPE)
    c.line((tx, ty + 3), (tx, ty + 10), P.TD_ROPE_D)

    # Eyes: the near one big and golden with a black slit and a thick dark lid; the far one smaller.
    for ex, ey, s in ((hx - 13, hy - 12, 0.7), (hx + 11, hy - 9, 1.0)):
        if s == 1.0:
            with part(c, RED, EDGE, up=2, down=1, ramp2=RED2) as k:
                k.ellipse(ex, ey, 10, 8, P.TD_RED)
        rx_, ry_ = 7.5 * s, 5.2 * s
        if pose.eye in ("half", "wide"):
            open_ = 1.0 if pose.eye == "wide" else 0.5
            c.ellipse(ex + 1, ey + 1, rx_, ry_, P.TD_EYE)
            c.ellipse(ex + 2, ey + 2, rx_ * 0.7, ry_ * 0.6, P.GOLD)
            c.rect(ex + 1 - rx_ * 0.7, ey + 1, ex + 1 + rx_ * 0.7, ey + 1 + max(1, s), EDGE)   # black slit
            lid = ey + 1 - ry_ * (1.6 * open_ - 0.6)
            c.rect(ex + 1 - rx_ - 1, ey - ry_ - 1, ex + 1 + rx_ + 1, lid, P.TD_RED_D)          # the heavy lid
            c.line((ex - rx_, lid), (ex + 2 + rx_, lid), EDGE)
            c.line((ex - rx_, lid + 1), (ex + 2 + rx_, lid + 1), EDGE)                     # thick lid edge
            c.px(ex + 3, ey + 3, P.WHITE)
        elif pose.eye == "shut":
            c.line((ex + 1 - rx_, ey + 1), (ex + 1 + rx_, ey + 1), EDGE)
            c.line((ex + 1 - rx_, ey + 2), (ex + 1 + rx_, ey + 2), EDGE)
        elif pose.eye == "star":
            c.ellipse(ex + 1, ey + 1, rx_, ry_, P.TD_EYE)
            c.line((ex - 3, ey - 2), (ex + 5, ey + 4), EDGE)
            c.line((ex - 3, ey + 4), (ex + 5, ey - 2), EDGE)
        else:
            c.line((ex - 3, ey - 3), (ex + 5, ey + 5), EDGE)
            c.line((ex - 3, ey + 5), (ex + 5, ey - 3), EDGE)

    # Tongue: a long pink tongue with a pink lantern-ball tip.
    if pose.tongue:
        reach = SIZE[0] - 12 - (hx + 26)
        tx2 = hx + 26 + reach * pose.tongue
        with part(c, {P.TD_TONGUE: (P.SK_PINK_L, P.TD_TONGUE_D)}, EDGE, up=1, down=1) as k:
            tube(k, [(hx + 18, mouth_y + 3, 2.6), (tx2, mouth_y + 1, 2.2)], P.TD_TONGUE)
        ball(c, tx2 + 2, mouth_y + 1, 1.0, pose.step)
    c.outline(EDGE)

    effects = Canvas(*SIZE)                                              # glows and energy, laid over the outline
    if pose.charge:
        g2 = Canvas(*SIZE)
        g2.ellipse(hx + 22, mouth_y + 2, 4 + pose.charge * 6, 4 + pose.charge * 6, P.SK_PINK)
        effects.paste(see_through(g2.img, 120))
        effects.ellipse(hx + 22, mouth_y + 2, 1.5 + pose.charge * 3, 1.5 + pose.charge * 3, P.SK_PINK_L)
        rnd = noise(1420 + pose.step)
        for i in range(5):
            a = i * math.tau / 5 + pose.step
            effects.px(hx + 22 + math.cos(a) * (6 + pose.charge * 6), mouth_y + 2 + math.sin(a) * 6, P.WHITE)
    if pose.spit:
        sx, sy = hx + 22 + pose.spit * 6, mouth_y - 2 - pose.spit * 5
        effects.line((hx + 18, mouth_y + 1), (sx - 5, sy + 3), P.SK_PINK)
        paper_lantern(effects, sx, sy, 1.15, glow_on=True)
        effects.outline(EDGE)
    if pose.burst:
        rnd = noise(1430 + pose.burst)
        energy = Canvas(*SIZE)
        for i in range(9):                                              # pink energy spikes bursting out
            x = CX - 56 + i * 14 + rnd() * 4
            h = (30 + rnd() * 26) * (1.0 if pose.burst < 3 else 0.55)
            flame(energy, x, GROUND - 6, h, 4 + rnd() * 2, pose.burst + i, 1440 + i,
                  colours=(P.KT_MAGENTA, P.SK_PINK, P.SK_PINK_L, P.WHITE))
        out.paste(see_through(energy.img, 230))
        for i in range(5):                                              # rocks flung out
            x = CX - 50 + i * 25 + rnd() * 6
            y = GROUND - 12 - pose.burst * (6 + i % 3 * 4) + pose.burst ** 2 * 1.5
            rock(effects, x, y, 3 + (i % 2), i)
        for i in range(10):
            petal(effects, CX - 50 + rnd() * 100, GROUND - 6 - rnd() * 50, i)

    body = c.img if pose.body_alpha >= 255 else see_through(c.img, pose.body_alpha)
    out.paste(body)
    brim = (hx - 4, hy - 23)                                             # sits on the head, the eyes peek out under it
    hat_img = hat(pose, brim, pose.step)
    out.paste(hat_img if pose.body_alpha >= 255 else see_through(hat_img, pose.body_alpha))
    out.paste(effects)
    return out.img


def ball(c: Canvas, x: float, y: float, s: float, step: int) -> None:
    """The pink lantern-ball on the tongue's tip: a round glowing pink paper lantern."""
    g = Canvas(*c.size)
    g.ellipse(x, y, 6 * s, 6 * s, P.SK_PINK)
    c.paste(see_through(g.img, 90))
    with part(c, {P.SK_PINK: (P.SK_PINK_L, P.KT_MAGENTA)}, P.KT_MAGENTA_D, up=1, down=1, left=1, right=1) as k:
        k.ellipse(x, y, 4 * s, 4 * s, P.SK_PINK)
    c.line((x - 3 * s, y), (x + 3 * s, y), P.KT_MAGENTA)
    c.line((x, y - 3 * s), (x, y + 3 * s), P.KT_MAGENTA)
    c.px(x - 1, y - 2, P.WHITE)


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
    boss.add("idle", [toad(ToadPose(step=k, breathe=(0, 1, 2, 1)[k], eye="shut" if k == 3 else "half"))
                      for k in range(4)], fps=5)
    boss.add("walk", [toad(ToadPose(step=k, walk=k * math.pi / 2, squash=(0, -1, 0, -1)[k], hat_tilt=(0, 2, 0, -2)[k]))
                      for k in range(4)], fps=8)
    boss.add("prepare", [toad(ToadPose(step=k, lean=2 + k, charge=(0.3, 0.7, 1.0)[k], eye="wide", jaw=0.3 * k,
                                       hat_tilt=-2 * k)) for k in range(3)], fps=8, loop=False)

    # Tongue attack (GameScene: tongue_strike -> "tongue"): charge at the mouth, then the tongue shoots out.
    boss.add("tongue", [toad(p) for p in (
        ToadPose(step=0, lean=2, charge=0.6, eye="wide", jaw=0.3, hat_tilt=-3),
        ToadPose(step=1, lean=4, jaw=0.7, eye="wide", tongue=0.25, hat_tilt=-4),
        ToadPose(step=2, lean=5, jaw=0.8, eye="wide", tongue=0.65, hat_tilt=-4),
        ToadPose(step=3, lean=6, jaw=0.8, eye="wide", tongue=1.0, hat_tilt=-5),
        ToadPose(step=4, lean=3, jaw=0.6, eye="half", tongue=0.4, hat_tilt=-2),
        ToadPose(step=5, lean=0, eye="half"),
    )], fps=10, loop=False)

    # Lantern projectile (GameScene: lantern_arc -> "lanterns").
    boss.add("lanterns", [toad(p) for p in (
        ToadPose(step=0, charge=0.4, breathe=2, eye="half", lean=-1),
        ToadPose(step=1, charge=0.8, breathe=3, eye="wide", lean=-2, hat_tilt=2),
        ToadPose(step=2, jaw=1, eye="wide", lean=3, spit=1, hat_tilt=-3),
        ToadPose(step=3, jaw=0.8, eye="wide", lean=3, spit=2, hat_tilt=-3),
        ToadPose(step=4, jaw=0.4, eye="half", spit=3),
        ToadPose(step=5, eye="half"),
    )], fps=10, loop=False)

    # Slam (GameScene: area_slam -> "slam"): crouch, leap with arms up, land, energy spikes, petals and rocks.
    boss.add("slam", [toad(p) for p in (
        ToadPose(step=0, squash=5, eye="half"),
        ToadPose(step=1, squash=-3, lift=12, arms_up=0.6, eye="wide", jaw=0.3, hat_tilt=-6),
        ToadPose(step=2, squash=-3, lift=24, arms_up=1.0, eye="wide", jaw=0.5, hat_tilt=2),
        ToadPose(step=3, squash=-2, lift=12, arms_up=0.6, eye="wide", jaw=0.6, hat_tilt=4),
        ToadPose(step=4, squash=7, eye="shut", jaw=0.6, burst=1, hat_tilt=-4),
        ToadPose(step=5, squash=5, eye="wide", jaw=0.4, burst=2),
        ToadPose(step=6, squash=2, eye="half", burst=3),
        ToadPose(step=7, eye="half"),
    )], fps=10, loop=False)

    hurt = toad(ToadPose(step=1, eye="star", jaw=0.6, lean=-4, hat_tilt=-12, squash=2))
    boss.add("hurt", [flash(hurt, 0.6), hurt], fps=10)

    # Slumps, the hat tips over, collapses, bursts into pink and leaves only the rocks.
    frames = [flash(toad(ToadPose(eye="x", jaw=0.5, squash=3)), 0.6),
              toad(ToadPose(step=1, eye="x", jaw=0.5, squash=6, hat_tilt=10)),
              toad(ToadPose(step=2, eye="shut", jaw=0.3, squash=9, hat_off=0.4)),
              toad(ToadPose(step=3, eye="shut", squash=11, hat_off=0.8))]
    for k, alpha in enumerate((170, 90, 30)):
        f = Canvas(*SIZE)
        f.paste(toad(ToadPose(step=4 + k, eye="shut", squash=11, hat_off=1.0, body_alpha=alpha, burst=k + 1)))
        frames.append(f.img)
    frames.append(toad(ToadPose(rock_only=True)))
    boss.add("death", frames, fps=8, loop=False)
    return [boss]
