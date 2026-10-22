"""Sakura route boss: the Blossom Kitsune Guardian (150x120), after docs/concept/Sakura Fox Boss Sprite Sheet.png.

A white fox with soft cream fur shaded pink: three big round fluffy tails with magenta-pink tips, branching brown
antlers flowering with cherry blossoms, a dark purple scarf with a gold rope, a gold bell and red tassels, a pink
forehead mark, a narrow pink eye with a purple line, pink spots on its haunch, petals everywhere and a dark navy
outline. It sits like a shrine guardian (idle), walks, lunges with a big pink claw crescent, crouches and bursts
glowing blossoms, calls fox-spirit flames out of a pink swirl, and collapses into a pile of petals."""
from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image

import palette as P
from bosskit import bezier, blob, part, tube
from draw import Canvas, noise, r, see_through, tint
from sprite import Sprite

SIZE = (150, 120)
CX, GROUND = 72, 116
# Suggested hitbox: 50 wide x 70 tall on the ground (baseY 0), centred on CX: haunch, chest and neck. The tails,
# antlers and muzzle stick out of it.
HITBOX = (50, 70)

EDGE = P.KT_LINE
CREAM = {P.KT_CREAM: (P.WHITE, P.KT_CREAM_S)}
CREAM2 = {P.KT_CREAM_S: (None, P.KT_CREAM_D)}
TAIL = {P.KT_CREAM: (P.WHITE, P.KT_CREAM_S), P.SK_PINK: (P.SK_PINK_L, P.KT_MAGENTA),
        P.KT_MAGENTA: (P.SK_PINK, P.KT_MAGENTA_D)}
ANTLER = {P.KT_ANTLER: (P.KT_ANTLER_L, P.KT_ANTLER_D)}
SCARF = {P.KT_SCARF: (P.KT_SCARF_L, P.SAKURA_EYE)}


@dataclass
class FoxPose:
    step: int = 0               # drifting petals and tail sway
    stance: str = "sit"         # sit | stand | crouch | lie
    dx: float = 0               # whole body shifted (lunge)
    bob: float = 0
    stride: float | None = None  # walk phase in radians (stand only)
    tails: float = 0            # 0 resting ... 1 flared up (casting)
    head_dx: float = 0
    head_dy: float = 0
    eye: str = "open"           # open | wide | narrow | shut | x
    mouth: str = "shut"         # shut | open
    reach: float = 0            # near forepaw thrust forward (claw)
    slash: int = 0              # pink crescent: 0 none, 1 forming, 2 full, 3 breaking into petals
    bloom: float = 0            # blossom forming at the mouth 0...1; 2 = bursting
    swirl: float = 0            # pink spirit swirl round it (summon)
    spirits: int = 0            # fox-spirit flames
    pile: float = 0             # petals heaped on the ground (death)


# --- small pieces, shared with the hazards and the sakura spirit -----------------------------------------------

def blossom(c: Canvas, x: float, y: float, rad: float, turn: float = 0.0,
            colours=(P.SK_PINK, P.SK_PINK_L, P.WHITE)) -> None:
    """A five-petal cherry blossom centred on (x, y)."""
    outer, inner, heart = colours
    for k in range(5):
        a = turn + k * math.tau / 5 - math.pi / 2
        c.ellipse(x + math.cos(a) * rad * 0.55, y + math.sin(a) * rad * 0.55, rad * 0.5, rad * 0.5, outer)
    for k in range(5):
        a = turn + k * math.tau / 5 - math.pi / 2
        c.px(x + math.cos(a) * rad * 0.6, y + math.sin(a) * rad * 0.6, inner)
    c.ellipse(x, y, max(0.6, rad * 0.25), max(0.6, rad * 0.25), heart)
    if rad >= 3:
        c.px(x, y, P.YELLOW)


def petal(c: Canvas, x: float, y: float, turn: int) -> None:
    """A single drifting petal, 3 px."""
    c.px(x, y, P.SK_PINK_L)
    c.px(x + (1 if turn % 2 else -1), y, P.SK_PINK)
    c.px(x, y + (1 if turn % 3 else -1), P.KT_MAGENTA)


def glow(c: Canvas, x: float, y: float, rad: float, alpha: int = 110, colour=P.SK_PINK) -> None:
    g = Canvas(*c.size)
    g.ellipse(x, y, rad, rad, colour)
    c.paste(see_through(g.img, alpha))


def fox_flame(c: Canvas, x: float, y: float, s: float, step: int, seed: int, halo: bool = True) -> None:
    """A fox-spirit flame: pink flame licks streaming back from a little fox head with ears and a dark eye."""
    rnd = noise(seed + step)
    if halo:
        glow(c, x, y, 7 * s, 80)
    with part(c, {P.SK_PINK: (P.SK_PINK_L, P.KT_MAGENTA)}, P.KT_MAGENTA_D, up=1, down=1, left=1, right=1) as k:
        for i in range(3):                                                   # flame licks streaming back
            sway = (rnd() - 0.5) * 3 * s
            k.poly([(x - 2 * s, y - 3 * s + i * 2.5 * s), (x - (10 + i * 2) * s, y - (5 - i * 2.5) * s + sway),
                    (x - 3 * s, y + i * 2 * s)], P.SK_PINK)
        k.ellipse(x, y, 4.2 * s, 3.6 * s, P.SK_PINK)
        k.poly([(x - 3 * s, y - 2 * s), (x - 2.5 * s, y - 7.5 * s), (x, y - 3 * s)], P.SK_PINK)
        k.poly([(x + 1 * s, y - 3 * s), (x + 2.5 * s, y - 7.5 * s), (x + 3.5 * s, y - 2 * s)], P.SK_PINK)
        k.poly([(x + 2 * s, y - 1 * s), (x + 7 * s, y + 1 * s), (x + 2 * s, y + 3 * s)], P.SK_PINK)   # muzzle
    c.ellipse(x - 0.5 * s, y + 0.5 * s, 2 * s, 1.6 * s, P.SK_PINK_L)
    c.px(x + 1.5 * s, y - 0.5 * s, P.SAKURA_EYE)
    c.px(x + 6.5 * s, y + 1 * s, P.SAKURA_EYE)


# --- the fox ----------------------------------------------------------------------------------------------------

def stance_points(pose: FoxPose) -> dict:
    """Where the haunch, torso, chest, head, tail root and paws are for each stance (before `dx`)."""
    g = GROUND
    if pose.stance == "sit":
        return {"haunch": (58, g - 20, 19, 17), "torso": None, "chest": (80, g - 40, 13, 24),
                "head": (96, g - 68), "tail": (46, g - 24),
                "legs": [((84, g - 30), (85, g - 3)), ((91, g - 30), (93, g - 3))], "hind": [(60, g - 3)]}
    if pose.stance == "lie":
        return {"haunch": (50, g - 13, 15, 11), "torso": (70, g - 11, 26, 9), "chest": (92, g - 11, 12, 9),
                "head": (106, g - 15), "tail": (40, g - 14), "legs": [], "hind": [(56, g - 3), (98, g - 3)]}
    low = 8 if pose.stance == "crouch" else 0
    s = math.sin(pose.stride) * 6 if pose.stride is not None else 0
    lift = (abs(math.cos(pose.stride)) * 2 if pose.stride is not None else 0)
    return {"haunch": (54, g - 38 + low, 15, 15), "torso": (73, g - 40 + low, 22, 13),
            "chest": (94, g - 42 + low, 12, 15), "head": (110, g - 60 + low * 1.3), "tail": (42, g - 42 + low),
            "legs": [((50, g - 30 + low), (46 + s, g - 3 - lift)), ((94, g - 34 + low), (96 - s, g - 3)),
                     ((58, g - 30 + low), (58 - s, g - 3)), ((100, g - 34 + low), (102 + s, g - 3 - lift))],
            "hind": []}


def tint_at(t: float):
    return P.KT_CREAM if t < 0.62 else P.SK_PINK if t < 0.86 else P.KT_MAGENTA


def plume(c: Canvas, pts: list, seed: int) -> None:
    """One big fluffy tail: cream at the root, pink, then magenta at the curling tip, with flame-like tufts."""
    n = len(pts)
    with part(c, TAIL, EDGE, up=2, down=3, left=2, right=3) as k:
        for i, (x, y, rad) in enumerate(pts):
            k.ellipse(x, y, rad, rad, tint_at(i / (n - 1)))
        rnd = noise(seed)
        for i in range(3, n - 2, 2):                                      # tufts flicking off the edge
            x, y, rad = pts[i]
            px_, py_, _ = pts[i - 1]
            ln = math.hypot(x - px_, y - py_) or 1
            ux, uy = (x - px_) / ln, (y - py_) / ln
            nx, ny = -uy, ux
            side = 1 if i % 4 == 1 else -1
            bx, by = x + nx * side * rad * 0.8, y + ny * side * rad * 0.8
            back = 3 + rnd() * 3
            k.poly([(bx - ux * 3, by - uy * 3), (bx + nx * side * 4 - ux * back, by + ny * side * 4 - uy * back),
                    (bx + ux * 2, by + uy * 2)], tint_at(i / (n - 1)))
    for i in range(2, n - 3, 3):                                           # soft fur strands
        x, y, rad = pts[i]
        c.line((x - rad * 0.4, y - rad * 0.1), (x + rad * 0.1, y - rad * 0.5),
               P.KT_CREAM_S if i < n * 0.62 else P.SK_PINK_L)


def tails(c: Canvas, root, pose: FoxPose) -> None:
    rx, ry = root
    lift = pose.tails * 10
    sway = [math.sin(pose.step * 0.8 + k) * 2 for k in range(3)]
    if pose.stance == "sit":
        # One arcs up and curls forward over the back, one sweeps out left and up, one low along the ground.
        shapes = [[(rx, ry, 7), (rx - 14, ry - 36 - lift, 14), (rx - 4, ry - 62 - lift, 12),
                   (rx + 12 + sway[0], ry - 66 - lift, 5)],
                  [(rx, ry, 7), (rx - 24, ry - 14 - lift * 0.6, 13), (rx - 34, ry - 36 - lift, 10),
                   (rx - 22 + sway[1], ry - 50 - lift, 4)],
                  [(rx, ry + 4, 7), (rx - 22, ry + 12, 12), (rx - 36, ry + 4 - lift * 0.4, 9),
                   (rx - 32 + sway[2], ry - 10 - lift * 0.5, 4)]]
    elif pose.stance == "lie":
        shapes = [[(rx, ry, 6), (rx - 14, ry - 18, 12), (rx - 30, ry - 20, 11), (rx - 34 + sway[0], ry - 34, 5)],
                  [(rx, ry + 2, 6), (rx - 18, ry + 2, 11), (rx - 32, ry - 4, 9), (rx - 36 + sway[1], ry - 14, 4)]]
    else:
        shapes = [[(rx, ry, 7), (rx - 12, ry - 28 - lift, 13), (rx - 2, ry - 48 - lift, 11),
                   (rx + 12 + sway[0], ry - 50 - lift, 5)],
                  [(rx, ry, 7), (rx - 20, ry - 8 - lift * 0.6, 12), (rx - 30, ry - 26 - lift, 10),
                   (rx - 20 + sway[1], ry - 38 - lift, 4)],
                  [(rx, ry + 3, 7), (rx - 18, ry + 10, 11), (rx - 30, ry + 4, 9), (rx - 28 + sway[2], ry - 8, 4)]]
    for k, ctrl in enumerate(shapes):
        pts = bezier([(max(rad + 4, x), max(rad + 4, y), rad) for x, y, rad in ctrl], 20)
        plume(c, pts, 1200 + k)


def antler(c: Canvas, root, side: int, step: int) -> None:
    """A branching brown antler rising from behind the ear, blossoms on its tips."""
    x0, y0 = root
    beam = [(x0, y0), (x0 - 7 * side - 2, y0 - 11), (x0 - 11 * side - 6, y0 - 26)]
    tips = [beam[-1]]
    with part(c, ANTLER, EDGE, up=1, down=1, left=1, right=1) as k:
        k.line(beam[0], beam[1], P.KT_ANTLER, 3)
        k.line(beam[1], beam[2], P.KT_ANTLER, 2)
        for frac, bdx, bdy in ((0.3, 10, -5), (0.6, -9, -7), (0.8, 8, -8)):
            bx = beam[0][0] + (beam[2][0] - beam[0][0]) * frac
            by = beam[0][1] + (beam[2][1] - beam[0][1]) * frac
            tip = (bx + bdx * (1 if side > 0 else 0.7), by + bdy)
            k.line((bx, by), tip, P.KT_ANTLER, 1)
            tips.append(tip)
    for i, (tx, ty) in enumerate(tips):
        blossom(c, tx, ty, 2.6 if i == 0 else 2.0, step * 0.2 + i + side)
    blossom(c, (beam[1][0] + beam[2][0]) / 2, (beam[1][1] + beam[2][1]) / 2, 2.2, side)


def fox(pose: FoxPose) -> Image.Image:
    c = Canvas(*SIZE)
    g = GROUND
    pts = stance_points(pose)
    dx, b = pose.dx, pose.bob

    def at(p):
        return (p[0] + dx, p[1] + b)

    hx, hy = pts["head"][0] + dx + pose.head_dx, pts["head"][1] + b + pose.head_dy

    if pose.swirl:                                             # pink spirit swirl behind
        sw = Canvas(*SIZE)
        for k in range(40):
            t = k / 39
            a = pose.step * 0.9 + t * math.tau * 1.3
            rad = 40 * pose.swirl * (0.55 + 0.45 * t)
            x, y = CX + 8 + math.cos(a) * rad, g - 44 + math.sin(a) * rad * 0.8
            sw.ellipse(x, y, 3 + 3 * t, 2.5 + 2 * t, P.SK_PINK if k % 3 else P.SK_PINK_L)
        c.paste(see_through(sw.img, 170))

    tails(c, at(pts["tail"]), pose)

    # Far legs, body, near legs.
    legs = pts["legs"]
    far, near = (legs[:2], legs[2:]) if len(legs) == 4 else (legs[1:], legs[:1])
    def knee(top, foot, front: bool):
        """A bent joint between hip/shoulder and paw: hind knees bend back, elbows forward."""
        mx, my = (top[0] + foot[0]) / 2, (top[1] + foot[1]) / 2
        return (mx + (2 if front else -4), my)

    for top, foot in far:
        front = top[0] > CX
        with part(c, CREAM, EDGE, down=2, right=1, ramp2=CREAM2) as k:
            kn = knee(at(top), (foot[0] + dx, foot[1]), front)
            k.line(at(top), kn, P.KT_CREAM_S, 6 if not front else 5)
            k.line(kn, (foot[0] + dx, foot[1]), P.KT_CREAM_S, 4)
            k.ellipse(foot[0] + dx + 2, foot[1], 4, 2.5, P.KT_CREAM_S)
    hx0, hy0, hrx, hry = pts["haunch"]
    cx0, cy0, crx, cry = pts["chest"]
    nx, ny = (cx0 + dx + hx) / 2, (cy0 + b - cry * 0.6 + hy) / 2      # the neck, where the scarf goes
    with part(c, CREAM, EDGE, up=3, down=5, left=3, right=4, ramp2=CREAM2) as k:
        blob(k, hx0 + dx, hy0 + b, hrx, hry, P.KT_CREAM, 1210, 12, 2.5)
        if pts["torso"]:
            tx, ty, trx, tr_y = pts["torso"]
            blob(k, tx + dx, ty + b, trx, tr_y, P.KT_CREAM, 1211, 14, 2.5)
        blob(k, cx0 + dx, cy0 + b, crx, cry, P.KT_CREAM, 1212, 10, 2.5)
        for fx, fy in pts["hind"]:
            k.ellipse(fx + dx, fy, 10, 3.5, P.KT_CREAM)
        k.line((cx0 + dx, cy0 + b - cry * 0.5), (hx - 3, hy + 4), P.KT_CREAM, 13)
    # Pink markings: a blossom spot on the haunch, blush on the chest.
    blossom(c, hx0 + dx - 4, hy0 + b - 2, 4.5, 0.4, (P.SK_PINK, P.SK_PINK_L, P.KT_MAGENTA))
    c.ellipse(hx0 + dx + 6, hy0 + b + 6, 3, 2, P.SK_PINK_L)
    for top, foot in near:
        reach = pose.reach if (top, foot) == near[-1] else 0
        fpos = (foot[0] + dx + reach * 30, foot[1] - reach * 22)
        with part(c, CREAM, EDGE, down=2, right=1, ramp2=CREAM2) as k:
            kn = knee(at(top), fpos, top[0] > CX) if pose.stance != "sit" else ((at(top)[0] + fpos[0]) / 2,
                                                                                (at(top)[1] + fpos[1]) / 2)
            k.line(at(top), kn, P.KT_CREAM, 6)
            k.line(kn, fpos, P.KT_CREAM, 5)
            k.ellipse(fpos[0] + 2, fpos[1], 4.5, 2.8, P.KT_CREAM)
        c.px(fpos[0] + 4, fpos[1] + 1, P.SK_PINK)
        if reach > 0.5:                                         # claws out
            for i in range(3):
                c.line((fpos[0] + 5, fpos[1] - 2 + i * 2), (fpos[0] + 9, fpos[1] - 3 + i * 2.4), P.KT_MAGENTA_D)

    # Antlers behind the ears.
    antler(c, (hx - 6, hy - 9), 1, pose.step)
    antler(c, (hx + 1, hy - 10), -1, pose.step)

    # Head: tall ears (purple inside), cream skull, slim muzzle, the forehead mark and eye line.
    for ex, tip in ((hx - 6, (hx - 10, hy - 25)), (hx + 2, (hx + 3, hy - 26))):
        with part(c, CREAM, EDGE, up=1, down=1, ramp2=CREAM2) as k:
            k.poly([(ex - 5, hy - 5), tip, (ex + 5, hy - 7)], P.KT_CREAM)
        c.poly([(ex - 2.5, hy - 7), (tip[0] + (ex - tip[0]) * 0.2, tip[1] + 5), (ex + 2.5, hy - 8)], P.KT_PURPLE)
    with part(c, CREAM, EDGE, up=2, down=3, left=2, right=2, ramp2=CREAM2) as k:
        blob(k, hx, hy, 12.5, 10.5, P.KT_CREAM, 1220, 10, 2)
        k.poly([(hx + 3, hy - 5), (hx + 19, hy + 1), (hx + 19, hy + 4), (hx + 3, hy + 7)], P.KT_CREAM)
        for i in range(3):                                      # cheek ruff
            k.poly([(hx - 8, hy + 1 + i * 3), (hx - 16, hy + 5 + i * 4), (hx - 6, hy + 5 + i * 3)], P.KT_CREAM)
    c.poly([(hx + 1, hy - 12), (hx + 4, hy - 8), (hx + 2, hy - 4), (hx - 1, hy - 8)], P.KT_MAGENTA)  # forehead mark
    c.px(hx + 1, hy - 8, P.SK_PINK_L)
    c.ellipse(hx + 19, hy + 1.5, 1.6, 1.4, EDGE)                # nose
    if pose.mouth == "open":
        c.poly([(hx + 7, hy + 5), (hx + 18, hy + 4), (hx + 16, hy + 9), (hx + 8, hy + 8)], P.KT_MAGENTA_D)
        c.poly([(hx + 14, hy + 5), (hx + 15, hy + 7), (hx + 16, hy + 5)], P.WHITE)
    else:
        c.line((hx + 9, hy + 5), (hx + 17, hy + 4), P.KT_CREAM_D)
    ex, ey = hx + 5, hy - 1
    if pose.eye in ("open", "wide", "narrow"):
        h = {"open": 1.0, "wide": 1.5, "narrow": 0.5}[pose.eye]
        c.poly([(ex - 4, ey + 1), (ex + 1, ey - 2 * h), (ex + 5, ey - 1), (ex + 1, ey + 1.5 * h)], P.KT_EYE)
        c.px(ex + 1, ey - 0.5, P.SAKURA_EYE)
        c.px(ex, ey - 1, P.WHITE)
        c.line((ex - 7, ey - 1), (ex + 1, ey - 2.5 * h), P.KT_PURPLE)      # the purple eye line, flicked back
        c.line((ex + 1, ey - 2.5 * h), (ex + 6, ey - 1.5), P.KT_PURPLE)
    elif pose.eye == "shut":
        c.line((ex - 6, ey), (ex + 4, ey - 1), P.KT_PURPLE)
    else:
        c.line((ex - 2, ey - 2), (ex + 2, ey + 2), P.KT_PURPLE)
        c.line((ex - 2, ey + 2), (ex + 2, ey - 2), P.KT_PURPLE)

    # Scarf at the neck: dark purple, a gold rope, a gold bell with red tassels, a blossom pinned on.
    with part(c, SCARF, EDGE, up=1, down=1, left=1, right=1) as k:
        k.ellipse(nx + 1, ny, 11, 5.5, P.KT_SCARF)
        k.poly([(nx - 6, ny + 2), (nx - 2, ny + 11), (nx + 3, ny + 9), (nx + 1, ny + 3)], P.KT_SCARF)  # the drape
    c.line((nx - 7, ny - 2), (nx + 9, ny - 4), P.KT_SCARF_L)                                        # a fold
    c.line((nx - 8, ny + 4), (nx + 10, ny - 1), P.GOLD)
    c.line((nx - 7, ny + 5), (nx + 10, ny), P.GOLD_D)
    bell = (nx + 7, ny + 6)
    for i in (-1, 1):                                           # red tassels
        c.line((bell[0] + i, bell[1] + 3), (bell[0] + i * 2, bell[1] + 11), P.SK_LACQUER)
        c.px(bell[0] + i * 2, bell[1] + 11, P.SK_LACQUER_D)
    with part(c, {P.GOLD: (P.YELLOW, P.GOLD_D)}, EDGE, up=1, down=1, left=1, right=1) as k:
        k.ellipse(bell[0], bell[1], 3.6, 3.6, P.GOLD)
    c.line((bell[0] - 2, bell[1] + 1), (bell[0] + 2, bell[1] + 1), P.KT_ANTLER_D)
    c.px(bell[0], bell[1] + 2, P.KT_ANTLER_D)
    c.px(bell[0] - 1, bell[1] - 2, P.WHITE)
    blossom(c, nx - 6, ny + 2, 3.4, 0.2)

    # Effects in front.
    if pose.bloom:
        bx, by = min(hx + 24, SIZE[0] - 16), hy + 8
        if pose.bloom >= 2:                                    # the burst: a big glowing blossom and flying petals
            glow(c, bx, by, 11, 120)
            blossom(c, bx, by, 8, pose.step * 0.3, (P.SK_PINK, P.SK_PINK_L, P.WHITE))
            rnd = noise(1230 + pose.step)
            for i in range(8):
                a = i * math.tau / 8 + rnd()
                petal(c, bx + math.cos(a) * 11, by + math.sin(a) * 10, i)
        else:
            glow(c, bx, by, 4 + pose.bloom * 6, 120)
            blossom(c, bx, by, 2 + pose.bloom * 5, pose.step * 0.4, (P.SK_PINK_L, P.WHITE, P.WHITE))
    if pose.slash:
        sx, sy = min(CX + 52 + dx, SIZE[0] - 22), g - 32
        span = (0.55, 1.0, 1.0)[pose.slash - 1]
        arc = Canvas(*SIZE)
        for k in range(26):
            t = k / 25
            if pose.slash == 3 and k % 3:
                continue
            a = math.radians(-95 + 175 * span * t)
            thick = (4.5 if pose.slash == 2 else 2.5) * math.sin(math.pi * t) + 0.6
            x, y = sx + math.cos(a) * 15, sy + math.sin(a) * 27
            if x > SIZE[0] - 4 - thick:
                continue
            arc.ellipse(x, y, thick, thick, P.KT_MAGENTA)
            arc.ellipse(x - math.cos(a) * thick * 0.4, y - math.sin(a) * thick * 0.4, thick * 0.55, thick * 0.55,
                        P.SK_PINK_L)
            if pose.slash == 3:
                petal(arc, x + 2, y, k)
        c.paste(see_through(arc.img, 245))
    for k in range(pose.spirits):
        a = pose.step * 0.7 + k * math.tau / 3
        fox_flame(c, CX + 6 + math.cos(a) * 46, g - 60 + math.sin(a) * 16, 1.2, pose.step, 1240 + k)
    if pose.pile:                                               # the heap of petals it collapses into
        rnd = noise(1250)
        for i in range(int(70 * pose.pile)):
            x = CX - 30 + rnd() * 80
            h = (1 - abs(x - CX - 10) / 42) * 14 * pose.pile
            y = g - rnd() * max(1.0, h)
            if i % 7 == 0:
                blossom(c, x, y - 1, 2.5, i)
            else:
                petal(c, x, y, i)
    rnd = noise(1260)
    for i in range(9):                                          # petals drifting past
        x = 8 + rnd() * 134 + pose.step * 2 - (i % 3) * pose.step
        y = 10 + rnd() * 100 + pose.step * 1.5
        petal(c, x % 140 + 4, y % 102 + 6, i + pose.step)
    for i in range(5):                                          # and lying round its feet
        petal(c, CX - 30 + i * 15 + (i * 7) % 5, g - 1, i)

    c.rect(0, g + 1, SIZE[0] - 1, SIZE[1] - 1, P.CLEAR)
    c.outline(EDGE)
    return c.img


def flash(image: Image.Image, amount: float) -> Image.Image:
    """Hit flash toward pink-white that keeps the dark outline, so it still reads on the bright backdrop."""
    out = tint(image, P.SK_PINK_L, amount)
    src, dst = image.load(), out.load()
    for y in range(image.height):
        for x in range(image.width):
            if src[x, y] == EDGE:
                dst[x, y] = src[x, y]
    return out


def build() -> list[Sprite]:
    boss = Sprite("boss_kitsune", SIZE, faces_left=True, cx=CX, ground=GROUND)
    boss.add("idle", [fox(FoxPose(step=k, bob=(0, -1, -1, 0)[k], tails=(0, 0.15, 0.25, 0.1)[k],
                                  eye="shut" if k == 3 else "open")) for k in range(4)], fps=5)

    # Walking on all fours (the engine may not use it).
    boss.add("walk", [fox(FoxPose(step=k, stance="stand", stride=k * math.tau / 6, bob=-(k % 2), tails=0.1))
                      for k in range(6)], fps=10)

    # ATTACK 1, claw slash (GameScene plays it for `claw_slash` as "claw"): lunge, and a big pink crescent.
    boss.add("claw", [fox(p) for p in (
        FoxPose(step=0, stance="crouch", dx=-4, eye="narrow", tails=0.3),
        FoxPose(step=1, stance="stand", dx=2, reach=0.6, eye="wide", mouth="open", slash=1, tails=0.4),
        FoxPose(step=2, stance="stand", dx=6, reach=1.0, eye="wide", mouth="open", slash=2, tails=0.5),
        FoxPose(step=3, stance="crouch", dx=6, reach=0.8, eye="wide", mouth="open", slash=2, tails=0.6),
        FoxPose(step=4, stance="stand", dx=2, reach=0.2, eye="open", slash=3, tails=0.3),
        FoxPose(step=5, stance="sit", eye="open"),
    )], fps=10, loop=False)

    # ATTACK 2, sakura projectiles: crouch, a blossom gathers at the mouth, then bursts.
    boss.add("bloom", [fox(p) for p in (
        FoxPose(step=0, stance="crouch", tails=0.5, bloom=0.2, mouth="open", eye="narrow"),
        FoxPose(step=1, stance="crouch", tails=0.8, bloom=0.6, mouth="open", eye="wide", head_dy=-2),
        FoxPose(step=2, stance="crouch", tails=1.0, bloom=1.0, mouth="open", eye="wide", head_dy=-3),
        FoxPose(step=3, stance="stand", tails=1.0, bloom=2, mouth="open", eye="wide", dx=2),
        FoxPose(step=4, stance="stand", tails=0.6, bloom=2, eye="open", dx=1),
        FoxPose(step=5, stance="sit", tails=0.2, eye="open"),
    )], fps=10, loop=False)

    # ATTACK 3, summon sakura spirits: a pink swirl and fox-spirit flames.
    boss.add("summon", [fox(FoxPose(step=k, tails=t, head_dy=-dy, eye=e, mouth=m, swirl=sw, spirits=s, bob=-(k % 2)))
                        for k, (t, dy, e, m, sw, s) in enumerate((
                            (0.4, 1, "shut", "shut", 0.4, 0), (0.9, 2, "wide", "open", 0.8, 0),
                            (1.0, 3, "wide", "open", 1.0, 1), (1.0, 3, "wide", "open", 0.8, 2),
                            (0.7, 2, "open", "shut", 0.4, 3), (0.3, 1, "open", "shut", 0, 3)))],
              fps=8, loop=False)

    hurt = fox(FoxPose(step=1, eye="shut", mouth="open", head_dx=-4, head_dy=2, tails=0.6, bob=1))
    boss.add("hurt", [flash(hurt, 0.55), hurt], fps=10)

    # DEATH: sinks down, lies flat, and collapses into a heap of petals that blows away.
    frames = [flash(fox(FoxPose(step=0, stance="crouch", eye="x", mouth="open", tails=0.3)), 0.55)]
    frames.append(fox(FoxPose(step=1, stance="crouch", eye="x", mouth="open", tails=0.2, bob=3)))
    frames.append(fox(FoxPose(step=2, stance="lie", eye="shut", tails=0, pile=0.2)))
    lying = fox(FoxPose(step=3, stance="lie", eye="shut", tails=0))
    for k in range(5):
        t = (k + 1) / 5
        frame = Canvas(*SIZE)
        frame.paste(see_through(lying, r(255 * (1 - t) ** 1.2)))
        heap = Canvas(*SIZE)
        rnd = noise(1270)
        for i in range(int(40 + 60 * min(1, t * 1.5))):        # the body turning into petals
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
