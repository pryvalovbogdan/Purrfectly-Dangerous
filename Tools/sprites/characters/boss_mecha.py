"""World 4 boss: the Mecha-Mouser, a hunched gunmetal robot rat (168x124; about 112 tall).

Glowing red eyes, lava-lit seams between segmented armour plates, a molten furnace core in its chest, a long
segmented metal tail and a rocket launcher on its back. Launches rockets, sweeps its flaming tail along the
ground, and once its armour is broken opens its chest and breathes a flamethrower."""
from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image

import palette as P
from bosskit import bezier, blob, flame, flame_jet, part, smoke
from draw import Canvas, noise, r, see_through, shatter, tint
from sprite import Sprite

SIZE = (168, 124)
CX, GROUND = 84, 120

METAL = {P.GM: (P.GM_L, P.GM_D)}
DARK = {P.GM_D: (P.GM, P.GM_DD)}
FIRE = (P.RED, P.LAVA, P.LAVA_L, P.YELLOW)


@dataclass
class MechaPose:
    bob: float = 0
    lean: float = 0             # head and shoulders pushed forward
    core: float = 0.4           # furnace glow 0...1
    hatch: bool = False         # chest plate open, core exposed
    launcher: float = 0         # launcher angle raised, degrees
    rocket: int = 0             # rocket leaving the launcher (frame index + 1)
    tail: float = 0             # 0 curled up behind ... 1 swept along the ground in front
    tail_fire: int = 0          # flames running along the tail (frame index + 1)
    jaw: float = 0.2
    flamethrower: int = 0       # flame from the open mouth (frame index + 1)
    eye: str = "on"             # on | hot | flicker | off
    fist: float = 0             # near fist raised 0...1
    shake: float = 0


def seam(c: Canvas, a, b, hot: float) -> None:
    """A lava-lit joint between plates."""
    c.line(a, b, P.GM_DD)
    if hot > 0.1:
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        c.line(((a[0] + mid[0]) / 2, (a[1] + mid[1]) / 2), ((b[0] + mid[0]) / 2, (b[1] + mid[1]) / 2),
               P.LAVA if hot < 0.7 else P.LAVA_L)


def joint(c: Canvas, x: float, y: float, rad: float, glow: float) -> None:
    """A round armoured joint with a molten centre (knees, shoulder)."""
    with part(c, METAL, P.GM_DD, up=2, down=2, left=2, right=2) as k:
        k.ellipse(x, y, rad, rad, P.GM)
    c.ellipse(x, y, rad * 0.55, rad * 0.55, P.GM_DD)
    c.ellipse(x, y, rad * 0.4, rad * 0.4, P.RED if glow < 0.5 else P.LAVA)
    c.ellipse(x - rad * 0.1, y - rad * 0.1, rad * 0.2, rad * 0.2, P.LAVA_L)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        c.px(x + math.cos(a) * rad * 0.8, y + math.sin(a) * rad * 0.8, P.GM_L)


def tail_points(pose: MechaPose, x: float, gy: float, by: float) -> list[tuple[float, float, float]]:
    rest = [(x - 22, by + 34), (x - 58, by + 46), (x - 82, by + 12), (x - 74, by - 30), (x - 52, by - 46),
            (x - 44, by - 30)]
    sweep = [(x - 22, by + 34), (x - 40, gy - 4), (x - 4, gy - 8), (x + 28, gy - 6), (x + 50, gy - 10),
             (x + 62, gy - 8)]
    t = pose.tail
    ctrl = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for a, b in zip(rest, sweep)]
    pts = bezier(ctrl, 18)
    return [(px, min(py, gy - 4), 6 - i * 0.18) for i, (px, py) in enumerate(pts)]


def draw_tail(c: Canvas, pts, pose: MechaPose) -> None:
    for i, (tx, ty, rad) in enumerate(pts):
        with part(c, METAL if i % 2 else DARK, P.GM_DD, up=1, down=2, left=1, right=1) as k:
            k.ellipse(tx, ty, rad, rad, P.GM if i % 2 else P.GM_D)
        if i % 3 == 1:
            c.px(tx, ty, P.LAVA)
    tx, ty, _ = pts[-1]
    px, py, _ = pts[-2]
    ang = math.atan2(ty - py, tx - px)
    tip = (tx + math.cos(ang) * 9, ty + math.sin(ang) * 9)
    nx, ny = -math.sin(ang) * 4, math.cos(ang) * 4
    c.poly([(tx + nx, ty + ny), tip, (tx - nx, ty - ny)], P.GM_L)            # blade at the tip
    c.line((tx, ty), tip, P.LAVA_L)
    if pose.tail_fire:
        fire = Canvas(*SIZE)
        for i, (fx, fy, rad) in enumerate(pts[6:]):
            flame(fire, fx, fy + rad * 0.5, 6 + (i + pose.tail_fire) % 3 * 3, 3, pose.tail_fire + i, 600 + i, FIRE)
        c.paste(see_through(fire.img, 230))


def mecha(pose: MechaPose) -> Image.Image:
    c = Canvas(*SIZE)
    x = CX + pose.shake
    gy = GROUND
    by = 64 + pose.bob                                   # centre of the torso
    ln = pose.lean
    hx, hy = x + 26 + ln, 32 + pose.bob + ln * 0.4

    tail = tail_points(pose, x, gy, by)
    if pose.tail < 0.5:
        draw_tail(c, tail, pose)

    # Far arm and far leg.
    with part(c, DARK, P.GM_DD, down=2) as k:
        k.line((x + 14, by - 14), (x + 30 + ln, by), P.GM_D, 7)
        k.ellipse(x + 34 + ln, by + 2, 5, 5, P.GM_D)
        k.ellipse(x + 14, by + 36, 12, 12, P.GM_D)
        k.line((x + 16, by + 40), (x + 20, gy - 6), P.GM_D, 8)
        k.ellipse(x + 24, gy - 4, 10, 4, P.GM_D)
    for i in range(3):
        c.poly([(x + 26 + i * 4, gy - 4), (x + 30 + i * 4, gy), (x + 26 + i * 4, gy)], P.LAVA)

    # Torso: a big egg of armour plates leaning forward, with lava-lit seams.
    with part(c, METAL, P.GM_DD, up=3, down=6, left=3, right=5) as k:
        k.ellipse(x - 2 + ln * 0.3, by, 27, 34, P.GM)
        k.ellipse(x + 8 + ln * 0.6, by - 18, 20, 18, P.GM)
    for i in range(4):                                    # segmented belly plates, each catching the light
        yy = by + 6 + i * 7
        half = math.sqrt(max(0.0, 1 - ((yy - by) / 34) ** 2)) * 22
        with part(c, METAL, P.GM_DD, up=1, down=2, left=1, right=2) as k:
            k.poly([(x + 2 - half, yy - 3), (x + 6 + half * 0.9, yy - 5), (x + 6 + half * 0.9, yy + 2),
                    (x + 2 - half, yy + 3)], P.GM)
        seam(c, (x + 4 - half, yy + 4), (x + 6 + half * 0.9, yy + 3), pose.core * (1 if i % 2 else 0.6))
    seam(c, (x - 18, by - 26), (x - 26, by + 10), pose.core)
    seam(c, (x + 2, by - 30), (x + 22, by - 30), pose.core * 0.6)
    for i in range(4):                                    # rivets
        c.px(x - 20 + i * 6, by - 22 - (i % 2), P.GM_L)

    # Rocket launcher strapped to its back: a twin tube pointing up and forward.
    la = math.radians(42 + pose.launcher)
    base = (x - 20, by - 22)
    d = (math.cos(la), -math.sin(la))
    n = (-d[1], d[0])
    muzzle = (base[0] + d[0] * 26, base[1] + d[1] * 26)
    if pose.rocket:
        fired = Canvas(*SIZE)
        dist = 4 + pose.rocket * 4
        rx, ry = muzzle[0] + d[0] * dist, muzzle[1] + d[1] * dist
        flame_jet(fired, (rx - d[0] * 14, ry - d[1] * 14), 1, 4, pose.rocket, 640, FIRE)
        for k in range(4):
            fired.ellipse(rx - d[0] * (10 + k * 4), ry - d[1] * (10 + k * 4), 3 - k * 0.5, 3 - k * 0.5,
                          (P.LAVA_L, P.LAVA, P.RED, P.GM_D)[k])
        fired.line((rx - d[0] * 8, ry - d[1] * 8), (rx, ry), P.RED, 4)
        fired.poly([(rx + n[0] * 2, ry + n[1] * 2), (rx + d[0] * 5, ry + d[1] * 5), (rx - n[0] * 2, ry - n[1] * 2)],
                   P.GREY_L)
        fired.outline()
        c.paste(fired)
    with part(c, METAL, P.GM_DD, up=1, down=2, left=1, right=2) as k:
        for side in (-1, 1):
            o = (n[0] * side * 4.5, n[1] * side * 4.5)
            k.line((base[0] + o[0], base[1] + o[1]), (muzzle[0] + o[0], muzzle[1] + o[1]), P.GM, 8)
        k.rect(base[0] - 7, base[1] - 2, base[0] + 7, base[1] + 10, P.GM)
        k.line((base[0] + d[0] * 6 - n[0] * 9, base[1] + d[1] * 6 - n[1] * 9),
               (base[0] + d[0] * 6 + n[0] * 9, base[1] + d[1] * 6 + n[1] * 9), P.GM, 4)   # clamp band
    for side in (-1, 1):
        o = (n[0] * side * 4.5, n[1] * side * 4.5)
        c.ellipse(muzzle[0] + o[0], muzzle[1] + o[1], 3, 3, P.GM_DD)
        if not pose.rocket or side == 1:
            c.ellipse(muzzle[0] + o[0] - d[0], muzzle[1] + o[1] - d[1], 2, 2, P.RED)       # rocket nose inside
        c.line((base[0] + o[0] + d[0] * 8, base[1] + o[1] + d[1] * 8),
               (base[0] + o[0] + d[0] * 10, base[1] + o[1] + d[1] * 10), P.LAVA)

    # Molten core in the chest: behind a grate, or exposed and roaring.
    fx, fy = x + 14 + ln * 0.6, by - 6
    glow = pose.core
    c.ellipse(fx, fy, 10, 10, P.GM_DD)
    c.ellipse(fx, fy, 8, 8, P.RED if glow < 0.5 else P.LAVA)
    c.ellipse(fx, fy, 4 + glow * 3, 4 + glow * 3, P.LAVA if glow < 0.7 else P.LAVA_L)
    if glow > 0.6:
        c.ellipse(fx - 1, fy - 1, 2 + glow, 2 + glow, P.YELLOW)
    if not pose.hatch:
        for k in range(-2, 3):
            c.line((fx + k * 3.5, fy - 7), (fx + k * 3.5, fy + 7), P.GM_D, 2)
    else:
        with part(c, METAL, P.GM_DD) as k:                # chest plate swung open
            k.poly([(fx - 10, fy - 10), (fx - 18, fy - 16), (fx - 18, fy + 4), (fx - 10, fy + 10)], P.GM)
        for k in range(6):                                # sparks off the core
            a = k * 1.1 + glow * 3
            c.px(fx + math.cos(a) * 13, fy + math.sin(a) * 12, P.LAVA_L)

    # Near leg: a big thigh with a glowing knee joint, piston shin and clawed foot.
    with part(c, METAL, P.GM_DD, up=2, down=4, left=2, right=3) as k:
        k.ellipse(x - 8, by + 30, 16, 15, P.GM)
        k.line((x - 4, by + 40), (x, gy - 8), P.GM, 11)
        k.ellipse(x + 4, gy - 4, 13, 4.5, P.GM)
    joint(c, x - 6, by + 30, 8, pose.core)
    c.rect(x - 2, gy - 18, x + 1, gy - 9, P.GM_L)
    for i in range(4):
        c.poly([(x + 8 + i * 3.5, gy - 4), (x + 13 + i * 3.5, gy), (x + 8 + i * 3.5, gy)], P.LAVA_L)

    # Head: big round ears, a long armoured snout, glowing red eyes and a lava-lit mouth.
    for ex, ey, rad in ((hx - 14, hy - 16, 10), (hx + 2, hy - 18, 9)):
        with part(c, METAL, P.GM_DD, up=2, down=2, left=2, right=2) as k:
            k.ellipse(ex, ey, rad, rad, P.GM)
        c.ellipse(ex + 1, ey + 1, rad - 3.5, rad - 3.5, P.PINK_D)
        c.ellipse(ex + 2, ey + 2, rad - 6, rad - 6, P.RED_D)
    jaw = pose.jaw * 9
    if pose.jaw > 0.15:
        c.poly([(hx + 4, hy + 6), (hx + 30, hy + 8), (hx + 26, hy + 9 + jaw), (hx + 4, hy + 12)], P.MAROON)
        c.poly([(hx + 8, hy + 8), (hx + 24, hy + 9), (hx + 20, hy + 8 + jaw * 0.8)], P.LAVA)
    with part(c, METAL, P.GM_DD, up=1, down=2, left=1, right=2) as k:   # lower jaw
        k.poly([(hx, hy + 8), (hx + 26, hy + 9 + jaw), (hx + 24, hy + 13 + jaw), (hx, hy + 15)], P.GM)
    with part(c, METAL, P.GM_DD, up=2, down=3, left=2, right=3) as k:
        blob(k, hx - 2, hy, 16, 13, P.GM, 700, 8, 2)
        k.poly([(hx + 4, hy - 8), (hx + 22, hy - 2), (hx + 34, hy + 4), (hx + 34, hy + 8), (hx + 4, hy + 10)], P.GM)
    for i in range(4):                                   # fangs
        tx = hx + 10 + i * 5
        c.poly([(tx, hy + 8), (tx + 1.5, hy + 12), (tx + 3, hy + 8)], P.GREY_L)
    c.ellipse(hx + 34, hy + 5, 2.5, 2.5, P.GM_DD)                         # nose
    c.px(hx + 35, hy + 4, P.RED)
    seam(c, (hx + 6, hy - 6), (hx + 6, hy + 8), pose.core)
    seam(c, (hx - 14, hy + 4), (hx - 2, hy + 10), pose.core * 0.6)
    for k in (-1, 1):                                    # whisker wires
        c.line((hx + 26, hy + 6), (hx + 38, hy + 3 + k * 4), P.GM_L)
    ex, ey = hx + 10, hy - 3
    c.poly([(ex - 6, ey - 5), (ex + 8, ey - 2), (ex + 8, ey + 4), (ex - 6, ey + 4)], P.GM_DD)   # brow socket
    if pose.eye != "off":
        hot = pose.eye == "hot"
        c.ellipse(ex + 1, ey, 4, 3.5, P.LAVA if hot else P.RED)
        c.ellipse(ex + 2, ey, 2, 2, P.YELLOW if hot else P.LAVA_L)
        c.px(ex + 2, ey - 1, P.WHITE)
        if pose.eye == "flicker":
            c.line((ex - 3, ey), (ex + 5, ey), P.GM_DD)
    c.line((ex - 7, ey - 6), (ex + 8, ey - 3), P.GM_L)                  # brow plate edge
    c.ellipse(hx - 6, hy - 4, 3, 3, P.GM_D)                               # cheek bolt
    c.px(hx - 6, hy - 4, P.LAVA)

    # Near arm: shoulder plate, forearm and a clawed fist.
    sx, sy = x + 6 + ln * 0.6, by - 16
    fist = (x + 30 + ln + pose.fist * 4, by + 4 - pose.fist * 20)
    elbow = (x + 12 + ln * 0.8, by + 6 - pose.fist * 4)
    with part(c, METAL, P.GM_DD, up=1, down=2, left=1, right=2) as k:
        k.line((sx, sy), elbow, P.GM, 9)
        k.line(elbow, fist, P.GM, 8)
        blob(k, fist[0] + 2, fist[1], 6, 5.5, P.GM, 710, 5, 1.5)
    joint(c, sx, sy, 9, pose.core)
    for i in range(3):
        c.line((fist[0] + 5, fist[1] - 3 + i * 3), (fist[0] + 9, fist[1] - 2 + i * 3), P.LAVA_L)
    seam(c, (elbow[0] + 3, elbow[1] - 2), (elbow[0] + 6, elbow[1] + 3), pose.core)

    if pose.tail >= 0.5:
        draw_tail(c, tail, pose)

    if pose.flamethrower:
        fire = Canvas(*SIZE)
        flame_jet(fire, (hx + 26, hy + 11), 17 + pose.flamethrower % 2 * 2, 8, pose.flamethrower, 650, FIRE,
                  droop=16)
        c.paste(see_through(fire.img, 240))

    c.rect(0, gy + 1, SIZE[0] - 1, SIZE[1] - 1, P.CLEAR)
    c.outline()
    return c.img


def build() -> list[Sprite]:
    from characters.boss_mecha_painted import NAMES as painted   # cut from the user's painted sheet instead
    return [] if "boss_mecha" in painted else drawn()


def drawn() -> list[Sprite]:
    """The code-drawn Mecha-Mouser (kept for reference; `boss_mecha_painted.py` replaces it)."""
    boss = Sprite("boss_mecha", SIZE, faces_left=True, cx=CX, ground=GROUND)
    boss.add("idle", [mecha(MechaPose(bob=b, core=g, tail=t, eye=e)) for b, g, t, e in
                      ((0, 0.3, 0, "on"), (-1, 0.45, 0.04, "on"), (-1, 0.6, 0.08, "hot"), (0, 0.45, 0.04, "on"))],
              fps=5)
    boss.add("rockets", [mecha(p) for p in (
        MechaPose(launcher=6, core=0.5, eye="hot"),
        MechaPose(launcher=14, core=0.6, bob=1, eye="hot", lean=-2),
        MechaPose(launcher=14, rocket=1, core=0.7, bob=1, shake=-1, eye="hot", lean=-2),
        MechaPose(launcher=12, rocket=2, core=0.6, shake=1, eye="hot"),
        MechaPose(launcher=12, rocket=3, core=0.5),
        MechaPose(launcher=4, core=0.4),
    )], fps=10, loop=False)
    boss.add("tail", [mecha(p) for p in (
        MechaPose(tail=0.0, bob=1, jaw=0.4, lean=-3, eye="hot"),
        MechaPose(tail=0.25, bob=1, jaw=0.6, lean=-2, tail_fire=1, eye="hot"),
        MechaPose(tail=0.65, jaw=1, shake=-1, tail_fire=2, eye="hot", lean=2),
        MechaPose(tail=1.0, jaw=1, shake=1, tail_fire=3, eye="hot", lean=4),
        MechaPose(tail=0.85, jaw=0.6, tail_fire=4, lean=2),
        MechaPose(tail=0.35, jaw=0.3),
    )], fps=10, loop=False)
    boss.add("core", [mecha(MechaPose(hatch=True, core=g, bob=b, jaw=1, eye="hot", flamethrower=k + 1, lean=3,
                                      fist=0.3))
                      for k, (g, b) in enumerate(((0.8, 0), (1.0, -1), (0.9, -1), (1.0, 0)))], fps=8)
    hurt = mecha(MechaPose(core=0.9, jaw=0.8, shake=-2, eye="flicker", lean=-4, fist=0.5))
    boss.add("hurt", [tint(hurt, P.WHITE, 0.8), hurt], fps=10)

    # Sparks, shudders, slumps, and bursts apart in smoke and fire.
    broken = mecha(MechaPose(core=1.0, jaw=1, hatch=True, eye="off", bob=4, lean=-2))
    frames = [tint(mecha(MechaPose(core=1.0, jaw=1, eye="flicker")), P.WHITE, 0.7)]
    for k in range(1, 8):
        t = k / 7
        frame = Canvas(*SIZE)
        if k < 3:
            frame.paste(mecha(MechaPose(core=1.0, jaw=1, hatch=True, eye="flicker", shake=(-2, 2)[k % 2],
                                        bob=k * 2)))
        else:
            frame.paste(shatter(broken, (t - 0.3) / 0.7, 520, block=6, spread=0.15, gravity=0.8,
                                origin=(CX + 10, GROUND - 50)))
        puff = Canvas(*SIZE)
        smoke(puff, CX + 4, GROUND - 40 - k * 4, 60, 50, 530 + k, (P.GM_D, P.GREY_D, P.GM), 4 + k)
        smoke(puff, CX + 10, GROUND - 50, 40, 40, 560 + k, (P.LAVA, P.LAVA_L, P.RED), max(0, 4 - k // 2))
        frame.paste(see_through(puff.img, 200))
        frames.append(see_through(frame.img, r(255 * (1 - max(0, t - 0.5)))))
    boss.add("death", frames, fps=10, loop=False)
    return [boss]
