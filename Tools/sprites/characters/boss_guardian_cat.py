"""Sakura route level 3 boss: the Sakura Guardian Cat (160x136), after docs/concept/Sakura Guardian Cat Boss Sprite Sheet.png.

A cream-white chibi shrine-cat spirit with big red eyes, a gold crown with a red jewel, red markings on its forehead and
cheeks, pink cheeks and ear insides, a red collar with a big gold bell, and a fan of big fluffy pink cherry-blossom
tails. At rest it sits under a small red torii with a glowing red paper lantern hanging from each end. For its attacks
the torii fades away and it floats and runs with its tails fanned out behind:
it spits glowing blossom bolts, spins in a petal storm, raises a giant glowing paw print and slams the ground, calls
the torii back to fire a pink laser from its mouth, and summons small pink spirit kittens. Drawn facing right."""
from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image

import palette as P
from bosskit import bezier, blob, flame, halo, part, tube
from characters.boss_kitsune import blossom, glow, petal
from draw import Canvas, noise, r, see_through, tint
from sprite import Sprite

SIZE = (160, 136)
CX, GROUND = 76, 132
# Suggested hitbox: 56 wide x 64 tall on the ground (baseY 0), centred on CX: the sitting body and the head up to the
# brow. The ears, crown, tails, torii and lanterns stick out of it.
HITBOX = (56, 64)

EDGE = P.GC_LINE
FUR = {P.GC_FUR: (P.WHITE, P.GC_FUR_S)}
FUR2 = {P.GC_FUR_S: (None, P.GC_FUR_D)}
PINK = {P.SK_PINK: (P.SK_PINK_L, P.SK_PINK_D)}
PINK2 = {P.SK_PINK_D: (None, P.KT_MAGENTA)}
GOLD = {P.GOLD: (P.YELLOW, P.GOLD_D)}
TORII = {P.GC_TORII: (P.GC_TORII_L, P.GC_TORII_D)}
KASAGI = {P.GC_KASAGI: (P.GC_KASAGI_L, None)}
LANTERN = {P.GC_LANTERN: (P.GC_LANTERN_L, P.GC_LANTERN_D)}
STONE = {P.GC_STONE: (P.GC_STONE_L, P.GC_STONE_D)}
MARK = {P.GC_MARK: (P.SK_RED_L, P.GC_MARK_D)}
ENERGY = (P.KT_MAGENTA, P.SK_PINK, P.SK_PINK_L, P.WHITE)
BLOSSOM_TAIL = (P.SK_PINK_L, P.WHITE, P.KT_MAGENTA)
BLOSSOM_BOLT = (P.SK_PINK_L, P.WHITE, P.KT_MAGENTA)


@dataclass
class CatPose:
    step: int = 0                # drifting petals, swaying tails and lanterns
    stance: str = "sit"          # sit | float | crouch | lie
    torii: int = 0               # torii opacity 0...255 (it fades out for the attacks and back in for the beam)
    torii_drop: float = 0        # the torii sinking into the ground (death)
    flare: float = 0             # lanterns flaring 0...1
    lift: float = 0              # body off the ground
    bob: float = 0
    dx: float = 0
    stride: float | None = None  # run phase in radians (float stance)
    tails: float = 0             # 0 resting ... 1 fanned up wide
    tail_turn: float = 0         # degrees: the whole fan swung round (spin)
    eye: str = "open"            # open | wide | narrow | shut | hurt | x | glow
    mouth: str = "smile"         # smile | open | shut
    head_dx: float = 0
    head_dy: float = 0
    paw_up: float = 0            # near forepaw raised high (slam) 0...1; -1 = slammed onto the ground
    paw_print: float = 0         # the giant glowing paw print over the raised paw 0...1
    burst: int = 0               # slam impact (frame index + 1)
    charge: float = 0            # pink light gathering at the mouth 0...1
    beam: float = 0              # the laser out to the frame edge 0...1
    volley: int = 0              # blossom bolts leaving the mouth (frame index + 1)
    spin: float = 0              # petal-storm rings round it 0...1
    swirl: float = 0             # summon swirl 0...1
    spirits: int = 0             # spirit kittens round it
    aura: float = 0              # enrage: pink flames rising round it 0...1
    crown_off: float = 0         # crown knocked off (death) 0...1
    pile: float = 0              # petals heaped on the ground (death)


# --- shared pieces (also used by boss_hazards) -------------------------------------------------------------------

def bolt(c: Canvas, x: float, y: float, s: float, step: int, trail: int = -1) -> None:
    """A glowing pink blossom bolt centred on (x, y) with a streaming trail on side `trail` (-1 left, 1 right)."""
    tr = Canvas(*c.size)
    for k in range(4):
        tx = x + trail * (4 + k * 2.6) * s
        tr.ellipse(tx, y + ((step + k) % 3 - 1) * 0.4, (2.2 - k * 0.45) * s, (1.6 - k * 0.3) * s,
                   (P.SK_PINK_L, P.SK_PINK, P.SK_PINK, P.KT_MAGENTA)[k])
    c.paste(tr)
    glow(c, x, y, 5.2 * s, 120 + (step % 2) * 30, P.SK_PINK)
    head = Canvas(*c.size)
    blossom(head, x, y, 4.4 * s, step * 0.35, BLOSSOM_BOLT)
    c.paste(head.outline(P.KT_MAGENTA_D))


def paw_print(c: Canvas, x: float, y: float, s: float, step: int = 0) -> None:
    """A big glowing pink paw print centred on (x, y): main pad and four toe beans, about 20x18 at s=1."""
    g = Canvas(*c.size)
    pads = [(x, y + 3 * s, 6 * s, 4.8 * s)] + [(x + dx * s, y + dy * s, 2.4 * s, 2.8 * s)
                                               for dx, dy in ((-6.5, -2.5), (-2.4, -6.4), (2.4, -6.4), (6.5, -2.5))]
    for px_, py_, rx, ry in pads:
        g.ellipse(px_, py_, rx + 2.5 * s, ry + 2.5 * s, P.SK_PINK)
    c.paste(see_through(g.img, 110 + (step % 2) * 30))
    for colour, grow in ((P.KT_MAGENTA, 1.0), (P.SK_PINK, 0.0), (P.SK_PINK_L, -0.9)):
        for px_, py_, rx, ry in pads:
            c.ellipse(px_ - (0.4 if grow < 0 else 0), py_ - (0.4 if grow < 0 else 0),
                      max(0.6, rx + grow * s), max(0.6, ry + grow * s), colour)
    c.ellipse(x - 1.5 * s, y + 1.5 * s, max(0.6, 1.5 * s), max(0.6, 1 * s), P.WHITE)


def spirit_kitten(c: Canvas, x: float, ground: float, step: int, s: float = 1.0, alpha: int = 235) -> None:
    """A small glowing pink spirit kitten running to the right, its feet on `ground`, about 16x13 at s=1."""
    k = Canvas(*c.size)
    run = step % 4
    y = ground - 6 * s - (1 if run in (1, 2) else 0) * s
    body = Canvas(*c.size)
    legs = ((-3.5, 2.5), (-2, -1.5), (2.5, 2), (4, -2))[run]
    with part(body, {P.SK_PINK_L: (P.WHITE, P.SK_PINK)}, P.KT_MAGENTA_D, up=1, down=1, left=1, right=1) as b:
        tube(b, [(x - 5 * s, y - 1 * s, 1.4 * s), (x - 8 * s, y - 4 * s, 1.3 * s),
                 (x - 7 * s + (run % 2) * s, y - 7 * s, 1.1 * s)], P.SK_PINK_L)                   # curled tail up
        for lx, sw in ((x - 3 * s, legs[0]), (x + 3 * s, legs[1])):                              # legs
            b.line((lx, y + 1 * s), (lx + sw * s, ground - 1), P.SK_PINK_L, max(1, r(1.8 * s)))
        b.ellipse(x, y, 5 * s, 3.4 * s, P.SK_PINK_L)                                               # body
        b.ellipse(x + 5 * s, y - 3 * s, 4 * s, 3.6 * s, P.SK_PINK_L)                               # head
        b.poly([(x + 2 * s, y - 5 * s), (x + 2.5 * s, y - 9.5 * s), (x + 5 * s, y - 6 * s)], P.SK_PINK_L)
        b.poly([(x + 5.5 * s, y - 6 * s), (x + 8 * s, y - 9.5 * s), (x + 8.5 * s, y - 4.5 * s)], P.SK_PINK_L)
    body.px(x + 6.5 * s, y - 3.5 * s, P.KT_MAGENTA_D)                                              # eye
    body.px(x + 3.5 * s, y - 3.5 * s, P.KT_MAGENTA_D)
    body.px(x + 8.5 * s, y - 2 * s, P.SK_PINK)                                                     # nose
    k.paste(body)
    for i in range(2):                                                                             # sparkles behind
        k.px(x - 9 * s - i * 3 - run % 2, y + 1 - i * 3 + run % 2, P.WHITE if i == 0 else P.SK_PINK_L)
    c.paste(see_through(k.img, alpha))


# --- the torii and its lanterns ----------------------------------------------------------------------------------

def lantern(c: Canvas, x: float, y: float, step: int, flare: float) -> None:
    """A glowing red paper lantern centred on (x, y), about 12x18 with its gold caps and tassel."""
    glow(c, x, y, 8 + (step % 2), 60, P.GC_LANTERN)
    if flare > 0.5:                                                                # flaring: short rays of light
        n = 2 + flare * 4
        for a in range(8):
            ang = a * math.tau / 8 + step * 0.2
            x0, y0 = x + math.cos(ang) * 9, y + math.sin(ang) * 11
            c.line((x0, y0), (x0 + math.cos(ang) * n, y0 + math.sin(ang) * n), P.GC_LANTERN_L if a % 2 else P.GC_LANTERN_W)
    with part(c, LANTERN, EDGE, up=1, down=1, left=1, right=1) as k:
        k.ellipse(x, y, 6, 7.5, P.GC_LANTERN)
        k.rect(x - 5.5, y - 5, x + 5.5, y + 5, P.GC_LANTERN)
    c.ellipse(x - 0.5, y, 3.4, 5, P.GC_LANTERN_L)                                  # the light inside
    c.ellipse(x - 0.5, y, 1.4 + flare, 2.6 + flare, P.GC_LANTERN_W)
    for dy in (-4, 0, 4):                                                          # paper ribs
        c.line((x - 5, y + dy), (x - 4, y + dy), P.GC_LANTERN_D)
        c.line((x + 3, y + dy), (x + 5, y + dy), P.GC_LANTERN_D)
    with part(c, GOLD, EDGE, up=1, down=1, left=1, right=1) as k:                  # gold caps
        k.rect(x - 4, y - 9, x + 4, y - 7, P.GOLD)
        k.rect(x - 4, y + 7, x + 4, y + 9, P.GOLD)
    c.line((x, y + 10), (x, y + 13), P.GC_MARK)                                   # tassel
    c.px(x, y + 14, P.GOLD)


def torii(step: int, flare: float) -> Image.Image:
    """The small red torii the cat sits under: two pillars on stone footings, two beams, a black upswept top
    beam, a gold plaque, and a red paper lantern hanging at each end."""
    c = Canvas(*SIZE)
    g = GROUND
    pl, pr = CX - 42, CX + 44
    for side, x in ((-1, pl - 13), (1, pr + 13)):                                 # lanterns, behind the beams
        sway = math.sin(step * 0.9 + side) * 1.2
        c.line((x, g - 101), (x + sway, g - 66), P.GC_KASAGI)
        lantern(c, x + sway, g - 56, step, flare)
    with part(c, STONE, EDGE, up=1, down=1, left=1, right=1) as k:
        for x in (pl, pr):
            k.rect(x - 6, g - 5, x + 6, g, P.GC_STONE)
    with part(c, TORII, EDGE, up=1, down=1, left=1, right=2) as k:
        for x in (pl, pr):
            k.poly([(x - 3, g - 96), (x + 3, g - 96), (x + 4, g - 6), (x - 4, g - 6)], P.GC_TORII)
        k.rect(pl - 10, g - 86, pr + 10, g - 83, P.GC_TORII)                      # nuki, the lower tie beam
        k.rect(pl - 11, g - 96, pr + 11, g - 93, P.GC_TORII)                      # the upper beam
    with part(c, KASAGI, EDGE, up=1, down=1, left=1, right=1) as k:              # black top beam, ends swept up
        k.poly([(pl - 18, g - 107), (pl - 8, g - 103), (pr + 8, g - 103), (pr + 18, g - 107), (pr + 16, g - 101),
                (pr + 8, g - 97), (pl - 8, g - 97), (pl - 16, g - 101)], P.GC_KASAGI)
    with part(c, GOLD, EDGE, up=1, down=1, left=1, right=1) as k:                # the plaque
        k.rect(CX - 3, g - 96, CX + 5, g - 84, P.GOLD)
    c.rect(CX - 1, g - 94, CX + 3, g - 86, P.GC_KASAGI)
    c.px(CX + 1, g - 92, P.SK_PINK)
    c.px(CX + 1, g - 89, P.SK_PINK)
    for x in (pl, pr):                                                            # gold caps where beams meet
        c.line((x - 3, g - 93), (x + 3, g - 93), P.GOLD_D)
    return c.img


# --- the cat -----------------------------------------------------------------------------------------------------

def layout(pose: CatPose) -> dict:
    g = GROUND
    yo = -pose.lift + pose.bob
    if pose.stance == "sit":
        return {"head": (CX + 4, g - 50 + yo, 3), "body": [(CX + 2, g - 18 + yo, 19, 17), (CX - 10, g - 12 + yo, 12, 11)],
                "root": (CX - 10, g - 18 + yo),
                "tails": [(15, 50, 11, 12), (200, 36, 10, 8), (160, 44, 12, 10), (122, 50, 12, -10)],
                "hind": [], "fore": [((CX + 8, g - 14 + yo), (CX + 8, g - 3 + yo)),
                                     ((CX + 18, g - 14 + yo), (CX + 19, g - 3 + yo))]}
    if pose.stance == "lie":
        return {"head": (CX + 16, g - 19 + yo, 4), "body": [(CX - 6, g - 11 + yo, 24, 10), (CX - 20, g - 11 + yo, 11, 10)],
                "root": (CX - 24, g - 12 + yo), "tails": [(178, 34, 9, 6), (150, 32, 9, -6), (196, 26, 7, 5)],
                "hind": [], "fore": [((CX + 4, g - 6 + yo), (CX + 36, g - 3 + yo))]}
    low = 6 if pose.stance == "crouch" else 0
    s = math.sin(pose.stride) * 7 if pose.stride is not None else 0
    up = abs(math.cos(pose.stride)) * 2 if pose.stride is not None else 0
    hx, hy = CX + 16, g - 52 + yo + low * 1.3
    return {"head": (hx, hy, 6), "body": [(CX - 2, g - 26 + yo + low, 20, 14), (CX - 14, g - 24 + yo + low, 12, 12)],
            "root": (CX - 18, g - 28 + yo + low),
            "tails": [(214, 32, 9, 6), (186, 40, 11, 8), (158, 44, 12, 8), (130, 42, 11, 8), (104, 34, 9, 6)],
            "hind": [((CX - 12, g - 20 + yo + low), (CX - 22 - s, g - 2 - up + yo * 0.4)),
                     ((CX + 2, g - 18 + yo + low), (CX + 4 + s, g - 2 - (2 - up) + yo * 0.4))],
            "fore": [((CX + 8, g - 30 + yo + low), (CX + 22 + s * 0.3, g - 26 + yo + low))]}


def tail(c: Canvas, root, ang: float, length: float, rad: float, curl: float, seed: int, step: int) -> None:
    """One big fluffy pink cherry-blossom tail from `root` toward `ang` degrees (0 right, 90 up), curling at the tip."""
    a = math.radians(ang)
    ux, uy = math.cos(a), -math.sin(a)
    nx, ny = -uy, ux
    x0, y0 = root
    sway = math.sin(step * 0.9 + seed) * 1.5
    ctrl = [(x0, y0, rad * 0.5), (x0 + ux * length * 0.4, y0 + uy * length * 0.4, rad),
            (x0 + ux * length * 0.85 + nx * curl * 0.6, y0 + uy * length * 0.85 + ny * curl * 0.6, rad * 1.0),
            (x0 + ux * length + nx * (curl * 1.5 + sway), y0 + uy * length + ny * (curl * 1.5 + sway), rad * 0.6)]
    pts = bezier(ctrl, 16)
    with part(c, PINK, P.KT_MAGENTA_D, up=2, down=3, left=2, right=2, ramp2=PINK2) as k:
        for i, (x, y, rr) in enumerate(pts):
            blob(k, x, y, rr * 0.9, rr * 0.9, P.SK_PINK, seed * 31 + i, 7, max(1.5, rr * 0.45))
    rnd = noise(seed * 7)
    for i in range(1, 15, 2):                                                     # soft fluff clumps
        x, y, rr = pts[i]
        side = 1 if i % 4 == 1 else -1
        cx_, cy_ = x + nx * side * rr * 0.35, y + ny * side * rr * 0.35
        c.line((cx_ - ux * 1.5 - 1, cy_ - uy * 1.5 - 1), (cx_ + ux * 1.5 - 1, cy_ + uy * 1.5 - 1), P.SK_PINK_L)
        c.px(cx_ + 1, cy_ + 1, P.SK_PINK_D)
    for i in range(2, 15, 3):                                                     # blossoms in the fluff
        x, y, rr = pts[i]
        blossom(c, x + (rnd() - 0.5) * rr, y + (rnd() - 0.5) * rr, 2.0 + rnd() * 0.8, i + step * 0.2, BLOSSOM_TAIL)
    x, y, rr = pts[-2]
    c.px(x, y, P.WHITE)


def crown(cr: float, top: float) -> Image.Image:
    """The gold crown on its own layer: a band with three points, a red jewel and a gold knob."""
    c = Canvas(*SIZE)
    with part(c, GOLD, EDGE, up=1, down=1, left=1, right=1) as k:
        k.poly([(cr - 12, top + 4), (cr + 12, top + 4), (cr + 11, top), (cr - 11, top)], P.GOLD)
        k.poly([(cr - 11, top), (cr - 9, top - 7), (cr - 5, top)], P.GOLD)
        k.poly([(cr + 5, top), (cr + 9, top - 7), (cr + 11, top)], P.GOLD)
        k.poly([(cr - 5, top), (cr, top - 12), (cr + 5, top)], P.GOLD)
        k.ellipse(cr, top - 14, 1.6, 1.6, P.GOLD)
    with part(c, MARK, EDGE, up=1, down=1, left=1, right=1) as k:
        k.ellipse(cr, top - 2, 2.6, 3, P.GC_MARK)
    c.px(cr - 1, top - 3, P.WHITE)
    c.px(cr - 9, top - 2, P.GC_MARK)
    c.px(cr + 9, top - 2, P.GC_MARK)
    c.line((cr - 10, top + 3), (cr + 10, top + 3), P.GOLD_D)
    return c.img


def head(c: Canvas, hx: float, hy: float, turn: float, pose: CatPose) -> None:
    fx = hx + turn
    for tip, base in (((hx - 16, hy - 29), [(hx - 21, hy - 8), (hx - 5, hy - 15)]),
                      ((hx + 14 + turn * 0.5, hy - 29), [(hx + 3 + turn * 0.5, hy - 15), (hx + 20, hy - 8)])):
        with part(c, FUR, EDGE, up=1, down=1, left=1, right=1, ramp2=FUR2) as k:
            k.poly([base[0], tip, base[1]], P.GC_FUR)
        mx, my = (base[0][0] + base[1][0]) / 2, (base[0][1] + base[1][1]) / 2
        c.poly([(mx - 3.5, my - 1), (tip[0] + (mx - tip[0]) * 0.25, tip[1] + 5), (mx + 3.5, my - 1)], P.SK_PINK)
        c.line((tip[0], tip[1] + 1), (tip[0] + (mx - tip[0]) * 0.15, tip[1] + 3), P.GC_MARK)
    with part(c, FUR, EDGE, up=2, down=3, left=2, right=3, ramp2=FUR2) as k:
        blob(k, hx, hy, 21, 17, P.GC_FUR, 1600, 12, 2.2)
        k.poly([(hx - 17, hy + 1), (hx - 25, hy + 5), (hx - 18, hy + 7), (hx - 23, hy + 10), (hx - 15, hy + 10)], P.GC_FUR)
        k.poly([(hx + 17, hy + 1), (hx + 25, hy + 5), (hx + 18, hy + 7), (hx + 23, hy + 10), (hx + 15, hy + 10)], P.GC_FUR)
    # Red markings: a flame mark on the brow, two stripes on each cheek; pink blush.
    c.poly([(fx, hy - 15), (fx + 2.2, hy - 10), (fx, hy - 6), (fx - 2.2, hy - 10)], P.GC_MARK)
    c.px(fx, hy - 10, P.SK_RED_L)
    c.px(fx - 5, hy - 9, P.GC_MARK)
    c.px(fx + 5, hy - 9, P.GC_MARK)
    for dy in (0, 3):
        c.line((hx - 20, hy + 1 + dy), (hx - 15, hy + 2 + dy), P.GC_MARK)
        c.line((hx + 15, hy + 2 + dy), (hx + 20, hy + 1 + dy), P.GC_MARK)
    c.ellipse(fx - 11, hy + 7, 2.5, 1.2, P.SK_PINK)
    c.ellipse(fx + 11, hy + 7, 2.5, 1.2, P.SK_PINK)
    # Eyes.
    for side, ex in ((-1, fx - 9), (1, fx + 8)):
        ey = hy + 1
        e = pose.eye
        if e in ("open", "wide", "narrow", "glow"):
            c.ellipse(ex, ey, 5, 4.5, P.GC_EYE)
            if e == "glow":
                glow(c, ex, ey, 6, 90, P.GC_EYE)
                c.ellipse(ex, ey, 5, 4.5, P.GC_EYE)
                c.ellipse(ex, ey, 2.6, 2.6, P.GC_EYE_L)
                c.rect(ex, ey - 2, ex, ey + 2, P.WHITE)
            else:
                c.ellipse(ex, ey + 2.5, 3, 1.5, P.GC_EYE_L)
                c.rect(ex - 0.5, ey - 3, ex + 0.5, ey + 2, P.GC_EYE_D)                 # slit pupil
                c.px(ex - 2 * side - 1, ey - 2, P.WHITE)
                c.px(ex - 2 * side - 1, ey - 1, P.WHITE)
            outer, inner = ex + 6 * side, ex - 6 * side
            if e == "wide":
                c.line((ex - 5, ey - 5), (ex + 5, ey - 5), EDGE)
            else:
                cut = 2 if e == "narrow" else 0
                # The lid slants down toward the nose: a sly, fierce look.
                c.poly([(outer, ey - 7), (inner, ey - 7), (inner, ey - 3 + cut), (outer, ey - 6 + cut)], P.GC_FUR)
                c.line((outer, ey - 5 + cut), (inner, ey - 2 + cut), EDGE)
                c.line((outer, ey - 6 + cut), (inner, ey - 3 + cut), EDGE)
            c.px(outer, ey + 1, EDGE)                                            # lash at the outer corner
            c.px(outer, ey, EDGE)
        elif e == "shut":
            c.line((ex - 4, ey), (ex, ey + 2), EDGE)
            c.line((ex, ey + 2), (ex + 4, ey), EDGE)
        elif e == "hurt":                                                         # squeezed shut: > <
            d = -side
            c.line((ex - 3 * d, ey - 3), (ex + 2 * d, ey), EDGE)
            c.line((ex + 2 * d, ey), (ex - 3 * d, ey + 3), EDGE)
        else:
            c.line((ex - 3, ey - 3), (ex + 3, ey + 3), P.GC_EYE_D)
            c.line((ex - 3, ey + 3), (ex + 3, ey - 3), P.GC_EYE_D)
    # Nose and mouth.
    c.poly([(fx - 1.5, hy + 5), (fx + 1.5, hy + 5), (fx, hy + 6.5)], P.SK_PINK_D)
    if pose.mouth == "open":
        c.ellipse(fx, hy + 10, 3.6, 3, P.GC_EYE_D)
        c.ellipse(fx, hy + 11.5, 2, 1, P.SK_PINK)
        c.px(fx - 2, hy + 8, P.WHITE)
        c.px(fx + 2, hy + 8, P.WHITE)
    elif pose.mouth == "smile":
        c.line((fx - 4, hy + 7), (fx - 2, hy + 9), EDGE)
        c.line((fx - 2, hy + 9), (fx, hy + 7), EDGE)
        c.line((fx, hy + 7), (fx + 2, hy + 9), EDGE)
        c.line((fx + 2, hy + 9), (fx + 4, hy + 7), EDGE)
        c.px(fx + 2, hy + 10, P.WHITE)
    else:
        c.line((fx - 3, hy + 8), (fx + 3, hy + 8), EDGE)
    # Red collar and the big gold bell.
    with part(c, MARK, EDGE, up=1, down=1) as k:
        tube(k, [(hx - 13, hy + 13, 2), (fx, hy + 16, 2.3), (hx + 15, hy + 13, 2)], P.GC_MARK)
    bx, by = fx, hy + 20
    with part(c, GOLD, EDGE, up=1, down=1, left=1, right=1) as k:
        k.ellipse(bx, by, 4.5, 4.5, P.GOLD)
    c.line((bx - 3, by + 1), (bx + 3, by + 1), P.GC_GOLD_DD)
    c.line((bx, by + 2), (bx, by + 3), P.GC_GOLD_DD)
    c.px(bx - 2, by - 2, P.WHITE)
    # Blossoms tucked by the ears.
    blossom(c, hx - 16, hy - 11, 4.4, 0.3 + pose.step * 0.1, (P.SK_PINK, P.SK_PINK_L, P.WHITE))
    blossom(c, hx - 10, hy - 16, 2.6, 1.0, (P.SK_PINK_L, P.WHITE, P.KT_MAGENTA))


def cat(pose: CatPose) -> Image.Image:
    out = Canvas(*SIZE)
    g = GROUND
    L = layout(pose)
    hx, hy, turn = L["head"]
    hx, hy = hx + pose.dx + pose.head_dx, hy + pose.head_dy
    rx_, ry_ = L["root"]
    root = (rx_ + pose.dx, ry_)

    if pose.aura:                                                 # enrage: pink flames rising behind
        fire = Canvas(*SIZE)
        rnd = noise(1610 + pose.step)
        for i in range(9):
            x = CX - 48 + i * 12 + rnd() * 4
            h = (50 + rnd() * 34) * pose.aura * (1 - abs(i - 4) * 0.08)
            flame(fire, x, g, h, 7 + rnd() * 3, pose.step + i, 1620 + i, colours=ENERGY)
        aura_img = see_through(fire.img, 200)
    if pose.torii:
        t = torii(pose.step, pose.flare)
        if pose.torii_drop:
            moved = Image.new("RGBA", SIZE, P.CLEAR)
            moved.alpha_composite(t.crop((0, 0, SIZE[0], SIZE[1] - r(pose.torii_drop))), (0, r(pose.torii_drop)))
            t = moved
        out.paste(t if pose.torii >= 255 else see_through(t, pose.torii))
    if pose.aura:
        out.paste(aura_img)                                       # in front of the torii, behind the cat
    if pose.swirl:                                                # summon: a pink swirl behind
        sw = Canvas(*SIZE)
        for k in range(40):
            t = k / 39
            a = pose.step * 0.9 + t * math.tau * 1.3
            rad = 44 * pose.swirl * (0.55 + 0.45 * t)
            sw.ellipse(CX + 4 + math.cos(a) * rad, g - 46 + math.sin(a) * rad * 0.75, 3 + 3 * t, 2.5 + 2 * t,
                       P.SK_PINK if k % 3 else P.SK_PINK_L)
        out.paste(see_through(sw.img, 150))
    rings = []
    if pose.spin:                                                 # petal-storm rings, back halves behind the cat
        back, front = Canvas(*SIZE), Canvas(*SIZE)
        for j, (yy, rad) in enumerate(((g - 14, 46), (g - 38, 52), (g - 64, 44))):
            for k in range(72):
                t = k / 71
                a = pose.step * 1.3 + j * 2.1 + t * math.tau * 0.8 * pose.spin
                thick = 0.6 + 2.2 * math.sin(math.pi * t) * pose.spin
                x, y = CX + 2 + math.cos(a) * rad, yy + math.sin(a) * rad * 0.22 - j * 0
                layer = front if math.sin(a) > 0 else back
                layer.ellipse(x, y, thick + 0.6, thick, P.KT_MAGENTA)
                layer.ellipse(x, y - 0.4, thick * 0.55, thick * 0.5, P.SK_PINK_L)
                if k % 12 == 5:
                    petal(layer, x + 2, y - 3, k + j)
        out.paste(see_through(back.img, 210))
        rings.append(front)

    c = Canvas(*SIZE)
    spread = pose.tails
    for k, (ang, ln, rad, curl) in enumerate(L["tails"]):
        a = ang + pose.tail_turn
        if pose.stance != "lie":
            a += (ang - 150) * (0.12 if pose.stance == "sit" else 0.35) * spread                       # fan out wider
        tail(c, root, a, ln * (1 + 0.12 * spread), rad, curl, 1630 + k, pose.step)

    far = Canvas(*SIZE)                                           # far legs, in shadow
    for top, foot in L["hind"][:1]:
        with part(far, FUR, EDGE, down=2, right=1, ramp2=FUR2) as k:
            tube(k, [(top[0] + pose.dx, top[1], 5), (foot[0] + pose.dx, foot[1] - 2, 3)], P.GC_FUR)
            k.ellipse(foot[0] + pose.dx + 2, foot[1] - 1, 4.5, 2.5, P.GC_FUR)
    if L["fore"] and pose.stance in ("float", "crouch"):
        (sx, sy), (px_, py_) = L["fore"][0]
        with part(far, FUR, EDGE, down=2, right=1, ramp2=FUR2) as k:
            tube(k, [(sx + 5 + pose.dx, sy - 2, 4), (px_ + 6 + pose.dx, py_ - 3, 3.2)], P.GC_FUR)
            k.ellipse(px_ + 7 + pose.dx, py_ - 3, 4, 3.2, P.GC_FUR)
    c.paste(tint(far.img, P.GC_FUR_D, 0.3))

    with part(c, FUR, EDGE, up=3, down=4, left=3, right=4, ramp2=FUR2) as k:
        for i, (bx, by, brx, bry) in enumerate(L["body"]):
            blob(k, bx + pose.dx, by, brx, bry, P.GC_FUR, 1640 + i, 12, 2.4)
    bx, by, brx, bry = L["body"][-1]                              # red flame marks and a pink blossom on the haunch
    bx += pose.dx
    for i in range(3):
        c.line((bx - 6 + i * 4, by + 4 - i), (bx - 3 + i * 4, by - 2 - i), P.GC_MARK)
    blossom(c, bx + 2, by - 4, 3.6, 0.6, (P.SK_PINK, P.SK_PINK_L, P.KT_MAGENTA))
    for top, foot in L["hind"][1:]:
        with part(c, FUR, EDGE, down=2, right=1, ramp2=FUR2) as k:
            tube(k, [(top[0] + pose.dx, top[1], 5.5), (foot[0] + pose.dx, foot[1] - 2, 3.4)], P.GC_FUR)
            k.ellipse(foot[0] + pose.dx + 2, foot[1] - 1, 5, 2.6, P.GC_FUR)

    def forepaw(i: int, top, foot) -> None:
        sx, sy = top[0] + pose.dx, top[1]
        fx, fy = foot[0] + pose.dx, foot[1]
        if i == len(L["fore"]) - 1 and pose.paw_up > 0:
            fx, fy = fx + (CX + 46 - fx) * pose.paw_up, fy + (g - 70 - fy) * pose.paw_up
        elif i == len(L["fore"]) - 1 and pose.paw_up < 0:
            fx, fy = CX + 38 + pose.dx, g - 3
        with part(c, FUR, EDGE, down=2, right=1, ramp2=FUR2) as k:
            tube(k, [(sx, sy, 4.5), (fx, fy, 3.4)], P.GC_FUR)
            k.ellipse(fx + 1, fy, 5, 3.6, P.GC_FUR)
        for t in range(2):
            c.line((fx + 1 + t * 2.5, fy + 1), (fx + 1 + t * 2.5, fy + 3), P.GC_FUR_D)

    raised = pose.paw_up > 0                                     # the raised paw goes up behind the head
    if raised:
        forepaw(len(L["fore"]) - 1, *L["fore"][-1])
    head(c, hx, hy, turn, pose)
    for i, (top, foot) in enumerate(L["fore"]):
        if not (raised and i == len(L["fore"]) - 1):
            forepaw(i, top, foot)
    c.outline(EDGE)

    crown_img = crown(hx + turn * 0.4, hy - 17)
    if pose.crown_off:
        cr = crown_img.rotate(pose.crown_off * 70, resample=Image.NEAREST, center=(hx, hy - 20))
        crown_img = Image.new("RGBA", SIZE, P.CLEAR)
        crown_img.alpha_composite(cr, (r(pose.crown_off * 26), r(pose.crown_off * (g - 8 - (hy - 20)))))
    if pose.crown_off >= 0.5:                                     # knocked off: lying on the ground in front
        out.paste(c)
        out.paste(crown_img)
    else:
        c.paste(crown_img)
        if pose.aura:                                             # enraged: a pink glow round the whole figure
            out.paste(halo(c.img, [P.SK_PINK_L, P.SK_PINK, P.KT_MAGENTA], r(110 + 80 * pose.aura)))
        else:
            out.paste(c)
    for front in rings:
        out.paste(see_through(front.img, 235))
    if pose.aura:                                                 # sparks and petals rising round it
        rnd = noise(1615 + pose.step)
        for i in range(r(14 * pose.aura)):
            x, y = CX - 50 + rnd() * 100, g - 4 - rnd() * 90
            if i % 3:
                petal(out, x, y, i + pose.step)
            else:
                out.px(x, y, P.WHITE)
                out.px(x, y + 1, P.SK_PINK_L)
    if pose.paw_print and pose.paw_up > 0:                        # the giant paw print over the raised paw
        paw_print(out, CX + 50 + pose.dx, g - 92 + (1 - pose.paw_print) * 6, 0.7 + 0.6 * pose.paw_print, pose.step)

    fx = hx + turn + 24                                           # in front of the mouth
    fy = hy + 9
    if pose.charge:
        glow(out, fx, fy, 4 + pose.charge * 7, 140, P.SK_PINK)
        out.ellipse(fx, fy, 1.5 + pose.charge * 3, 1.5 + pose.charge * 3, P.SK_PINK_L)
        out.ellipse(fx, fy, 0.6 + pose.charge * 1.5, 0.6 + pose.charge * 1.5, P.WHITE)
        for i in range(6):
            a = i * math.tau / 6 + pose.step * 0.7
            d = 9 + (1 - pose.charge) * 6
            out.px(fx + math.cos(a) * d, fy + math.sin(a) * d * 0.8, P.WHITE if i % 2 else P.SK_PINK_L)
    if pose.beam:
        end = SIZE[0] - 10
        start = fx - 6
        length = (end - start) * pose.beam
        bm = Canvas(*SIZE)
        bm.rect(start, fy - 6, start + length, fy + 6, P.KT_MAGENTA)
        out.paste(see_through(bm.img, 110))
        out.rect(start, fy - 4, start + length, fy + 4, P.KT_MAGENTA)
        out.rect(start, fy - 3, start + length, fy + 3, P.SK_PINK)
        out.rect(start, fy - 2, start + length, fy + 2, P.SK_PINK_L)
        out.rect(start, fy - 1, start + length, fy + 1, P.WHITE)
        for i in range(int(length / 6)):                                          # ripples running along it
            x = start + 3 + i * 6 + pose.step % 2 * 3
            out.px(x, fy - 4, P.SK_PINK)
            out.px(x + 2, fy + 4, P.SK_PINK)
        glow(out, start, fy, 7, 150, P.SK_PINK)
        out.ellipse(start, fy, 3.5, 3.5, P.SK_PINK_L)
        out.ellipse(start, fy, 2, 2, P.WHITE)
        hx2 = min(start + length, SIZE[0] - 14)
        glow(out, hx2, fy, 11, 140, P.SK_PINK)
        blossom(out, hx2, fy, 10, pose.step * 0.4, (P.KT_MAGENTA, P.SK_PINK_L, P.WHITE))
        blossom(out, hx2, fy, 6, pose.step * 0.4 + 0.6, (P.SK_PINK_L, P.WHITE, P.WHITE))
        rnd = noise(1650 + pose.step)
        for i in range(6):
            petal(out, start + rnd() * length, fy - 6 + rnd() * 12, i + pose.step)
    if pose.volley:
        v = pose.volley
        for j, dy in enumerate((-9, 0, 9) if v > 1 else (0,)):
            x = fx + 4 + (v - 1) * 16 + abs(dy) * 0.4
            bolt(out, min(x, SIZE[0] - 10), fy + dy * (v - 1) * 0.6, 1.3, pose.step + j, -1)
    if pose.paw_up < 0 or pose.burst:                             # slam impact in front
        b = max(1, pose.burst)
        energy = Canvas(*SIZE)
        bx2 = CX + 44 + pose.dx
        h = (66, 54, 30)[b - 1]
        flame(energy, bx2, g, h, 9, b, 1660, colours=ENERGY)
        for i, dx2 in enumerate((-12, -6, 7, 13)):
            flame(energy, bx2 + dx2 * 1.2, g, h * (0.45 if abs(dx2) > 8 else 0.6), 4, b + i, 1661 + i,
                  colours=ENERGY)
        out.paste(see_through(energy.img, 225))
        out.rect(bx2 - 1, g - h * 0.8, bx2 + 1, g, P.WHITE)                    # the bright core of the pillar
        paw_print(out, bx2, g - 4, 0.45, b)
        rnd = noise(1670 + b)
        for i in range(12):
            a = rnd() * math.pi
            d = 8 + b * 8 + rnd() * 10
            petal(out, bx2 + math.cos(a) * d, g - 2 - math.sin(a) * d * 0.7, i)
    for k, (x, y) in enumerate(((CX + 52, g), (CX + 40, g - 78), (CX - 44, g - 84))[:pose.spirits]):
        spirit_kitten(out, x, y, pose.step + k, 1.3, 255)
    if pose.pile:
        rnd = noise(1680)
        for i in range(int(70 * pose.pile)):
            x = CX - 34 + rnd() * 84
            h = (1 - abs(x - CX - 8) / 44) * 14 * pose.pile
            y = g - rnd() * max(1.0, h)
            if i % 7 == 0:
                blossom(out, x, y - 1, 2.5, i)
            else:
                petal(out, x, y, i)
    rnd = noise(1690)
    for i in range(8):                                            # petals drifting past
        x = 8 + rnd() * 140 + pose.step * 2 - (i % 3) * pose.step
        y = 8 + rnd() * 100 + pose.step * 1.5
        petal(out, x % 144 + 6, y % 104 + 6, i + pose.step)
    out.rect(0, g + 1, SIZE[0] - 1, SIZE[1] - 1, P.CLEAR)
    return out.img


def flash(image: Image.Image, amount: float) -> Image.Image:
    """Hit flash toward white that keeps the dark outline."""
    out = tint(image, P.WHITE, amount)
    src, dst = image.load(), out.load()
    for y in range(image.height):
        for x in range(image.width):
            if src[x, y] == EDGE:
                dst[x, y] = src[x, y]
    return out


def build() -> list[Sprite]:
    boss = Sprite("boss_guardian_cat", SIZE, faces_left=True, cx=CX, ground=GROUND)
    boss.add("idle", [cat(CatPose(step=k, torii=255, bob=(0, -1, -1, 0)[k], tails=(0, 0.1, 0.2, 0.1)[k],
                                  flare=(0, 0.3, 0.5, 0.2)[k], eye="shut" if k == 3 else "open")) for k in range(4)],
              fps=5)

    # Floating run with the tails out (the torii stays behind).
    boss.add("walk", [cat(CatPose(step=k, stance="float", stride=k * math.tau / 6, lift=2, bob=-(k % 2), tails=0.3))
                      for k in range(6)], fps=10)

    # Wind-up: the torii fades away as it drops into its floating stance.
    boss.add("prepare", [cat(CatPose(step=k, stance=s, torii=t, tails=f, eye="narrow", mouth="shut"))
                         for k, (s, t, f) in enumerate((("sit", 170, 0.3), ("crouch", 90, 0.6), ("crouch", 0, 0.9)))],
              fps=8, loop=False)

    # ATTACK 1, sakura projectiles: light gathers at the mouth, three glowing blossom bolts fan out.
    boss.add("volley", [cat(p) for p in (
        CatPose(step=0, stance="crouch", tails=0.6, charge=0.4, eye="narrow", mouth="open"),
        CatPose(step=1, stance="crouch", tails=0.9, charge=0.9, eye="wide", mouth="open", head_dy=-1),
        CatPose(step=2, stance="float", lift=2, tails=1.0, volley=1, eye="wide", mouth="open", dx=2),
        CatPose(step=3, stance="float", lift=2, tails=0.9, volley=2, eye="wide", mouth="open", dx=2),
        CatPose(step=4, stance="float", lift=2, tails=0.6, volley=3, eye="open", dx=1),
        CatPose(step=5, stance="float", lift=1, tails=0.3, eye="open"),
    )], fps=10, loop=False)

    # ATTACK 2, petal storm: it spins, its tails sweeping round through pink rings of petals.
    boss.add("spin", [cat(CatPose(step=k, stance="float", lift=(2, 4, 6, 6, 4, 2)[k], spin=sp, tail_turn=k * 55,
                                  tails=0.6, eye="narrow" if k in (0, 5) else "wide", mouth="smile"))
                      for k, sp in enumerate((0.4, 0.8, 1.0, 1.0, 1.0, 0.5))], fps=12, loop=False)

    # ATTACK 3, giant paw slam: a paw raised under a big glowing paw print, a leap, the slam and a pillar of pink.
    boss.add("slam", [cat(p) for p in (
        CatPose(step=0, stance="crouch", tails=0.4, eye="narrow", mouth="shut"),
        CatPose(step=1, stance="float", lift=2, paw_up=0.5, paw_print=0.4, tails=0.6, eye="wide", mouth="open"),
        CatPose(step=2, stance="float", lift=6, paw_up=1.0, paw_print=1.0, tails=0.8, eye="wide", mouth="open"),
        CatPose(step=3, stance="float", lift=12, paw_up=1.0, paw_print=1.0, tails=1.0, eye="glow", mouth="open"),
        CatPose(step=4, stance="crouch", paw_up=-1, burst=1, tails=0.6, eye="narrow", mouth="open"),
        CatPose(step=5, stance="crouch", paw_up=-1, burst=2, tails=0.5, eye="narrow", mouth="smile"),
        CatPose(step=6, stance="float", lift=1, burst=3, tails=0.4, eye="open"),
        CatPose(step=7, stance="float", lift=2, tails=0.3, eye="open"),
    )], fps=10, loop=False)

    # ATTACK 4, torii laser: the torii comes back, the lanterns flare, light gathers and a pink beam fires.
    boss.add("beam", [cat(p) for p in (
        CatPose(step=0, torii=90, tails=0.2, eye="narrow", mouth="shut"),
        CatPose(step=1, torii=180, flare=0.4, charge=0.3, tails=0.4, eye="narrow", mouth="open"),
        CatPose(step=2, torii=255, flare=0.8, charge=0.7, tails=0.6, eye="glow", mouth="open"),
        CatPose(step=3, torii=255, flare=1.0, charge=1.0, tails=0.7, eye="glow", mouth="open"),
        CatPose(step=4, torii=255, flare=1.0, beam=1.0, tails=0.8, eye="glow", mouth="open", head_dx=-1),
        CatPose(step=5, torii=255, flare=0.8, beam=1.0, tails=0.8, eye="glow", mouth="open", head_dx=-1),
        CatPose(step=6, torii=255, flare=0.3, beam=0.35, tails=0.4, eye="open", mouth="open"),
    )], fps=10, loop=False)

    # Summon sakura spirits: a pink swirl, and small spirit kittens appear round it.
    boss.add("summon", [cat(CatPose(step=k, stance="float", lift=3 + k % 2, swirl=sw, spirits=s, tails=t, eye=e,
                                    mouth=m))
                        for k, (sw, s, t, e, m) in enumerate((
                            (0.4, 0, 0.5, "shut", "shut"), (0.8, 0, 0.9, "wide", "open"), (1.0, 1, 1.0, "glow", "open"),
                            (0.8, 2, 1.0, "glow", "open"), (0.5, 3, 0.7, "open", "smile"),
                            (0.2, 3, 0.4, "open", "smile")))],
              fps=8, loop=False)

    # Phase change: back under the torii, the lanterns blaze, pink flames rise round it and its eyes glow.
    boss.add("enrage", [cat(CatPose(step=k, torii=255, flare=f, aura=a, tails=t, eye=e, mouth=m, dx=(0, 0, -1, 1, -1, 1)[k],
                                    bob=(0, 1, 0, 0, 0, 0)[k]))
                        for k, (f, a, t, e, m) in enumerate((
                            (0.3, 0.2, 0.3, "shut", "shut"), (0.6, 0.5, 0.6, "shut", "shut"),
                            (1.0, 0.9, 1.0, "glow", "open"), (1.0, 1.0, 1.0, "glow", "open"),
                            (1.0, 1.0, 1.0, "glow", "open"), (0.8, 0.8, 0.8, "glow", "smile")))],
              fps=8, loop=False)

    hurt = cat(CatPose(step=1, eye="hurt", mouth="open", head_dx=-3, head_dy=2, tails=0.5, bob=1))
    boss.add("hurt", [flash(hurt, 0.6), hurt], fps=10)

    # DEATH: slumps, the torii sinks away and the crown falls off, lies flat, then blows away as petals.
    frames = [flash(cat(CatPose(step=0, torii=255, eye="x", mouth="open")), 0.6),
              cat(CatPose(step=1, torii=170, torii_drop=8, eye="x", mouth="open", bob=3, head_dy=2, crown_off=0.2)),
              cat(CatPose(step=2, torii=80, torii_drop=24, stance="lie", eye="shut", mouth="shut", crown_off=0.6,
                          pile=0.15))]
    lying = cat(CatPose(step=3, stance="lie", eye="shut", mouth="shut", crown_off=1.0))
    for k in range(5):
        t = (k + 1) / 5
        frame = Canvas(*SIZE)
        frame.paste(see_through(lying, r(255 * (1 - t) ** 1.2)))
        heap = Canvas(*SIZE)
        rnd = noise(1700)
        for i in range(int(40 + 60 * min(1, t * 1.5))):
            x0, y0 = CX - 36 + rnd() * 84, GROUND - 26 + rnd() * 24
            fly = max(0.0, t - 0.4) * 2
            x, y = x0 - fly * (8 + rnd() * 30), y0 - fly * (rnd() * 40)
            if 2 <= x < SIZE[0] - 3 and 3 <= y <= GROUND and rnd() > fly * 0.6:
                if i % 6 == 0:
                    blossom(heap, x, y, 2.5, i)
                else:
                    petal(heap, x, y, i + k)
        frame.paste(heap)
        frames.append(frame.img)
    boss.add("death", frames, fps=8, loop=False)
    return [boss]
