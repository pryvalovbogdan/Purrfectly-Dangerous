"""World 2 boss: a fluffy white ice dragon with crystal whiskers and horns (190x134; about 100 long
and 90 tall with wings up). Fans ice shards, sweeps frost breath along the ground and dives."""
from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image

import palette as P
from draw import Canvas, noise, r, see_through, tint
from sprite import Sprite

SIZE = (190, 134)
CX, GROUND = 90, 130


@dataclass
class DragonPose:
    lift: float = 0
    crouch: float = 0
    tilt: float = 0            # degrees the whole dragon pitches nose-down (dive)
    head_dx: float = 0
    head_dy: float = 0
    jaw: float = 0             # 0 shut ... 1 wide open
    wing: float = 0            # -1 folded down ... 1 raised high
    tail: float = 0
    eye: str = "open"          # open | shut | x
    glow: int = 0              # crystals glowing (charging shards)
    breath: int = 0            # frost puff at the mouth (frame index + 1)
    shards: int = 0            # shards hovering in front (charging)


def fluffy(c: Canvas, x: float, y: float, rx: float, ry: float, color, seed: int, tufts: int = 14) -> None:
    """An ellipse with a tufted edge."""
    c.ellipse(x, y, rx, ry, color)
    rnd = noise(seed)
    for k in range(tufts):
        a = k / tufts * math.tau + rnd() * 0.3
        rad = 2 + rnd() * 2.5
        c.ellipse(x + math.cos(a) * (rx - 1), y + math.sin(a) * (ry - 1), rad, rad, color)


def crystal(c: Canvas, base: tuple, tip: tuple, width: float, glow: bool = False) -> None:
    bx, by = base
    tx, ty = tip
    dx, dy = tx - bx, ty - by
    n = math.hypot(dx, dy) or 1
    nx, ny = -dy / n * width, dx / n * width
    mid = (bx + dx * 0.35, by + dy * 0.35)
    c.poly([(bx, by), (mid[0] + nx, mid[1] + ny), (tx, ty), (mid[0] - nx, mid[1] - ny)], P.CYAN if not glow else P.ICE_L)
    c.poly([(bx, by), (mid[0] + nx, mid[1] + ny), (tx, ty)], P.BLUE if not glow else P.CYAN)
    c.px(mid[0] - nx * 0.4, mid[1] - ny * 0.4, P.WHITE)


def underside(img: Image.Image, depth: int = 3) -> None:
    """Shades the lower rim of every white shape blue, so the fluffy white body has volume."""
    px = img.load()
    w, h = img.size
    light = {P.WHITE: P.ICE_L, P.ICE_L: P.BLUE_L}
    changes = []
    for y in range(h):
        for x in range(w):
            colour = px[x, y]
            if colour in light:
                below = [px[x, y + k][3] if y + k < h else 0 for k in range(1, depth + 1)]
                if not all(below):
                    changes.append((x, y, light[colour]))
    for x, y, colour in changes:
        px[x, y] = colour


def dragon(pose: DragonPose) -> Image.Image:
    big = Canvas(*SIZE)
    c = big
    x0 = CX
    gy = GROUND - pose.lift
    cr = pose.crouch
    glow = pose.glow > 0

    # Far wing first, a darker copy shifted back.
    def wing(shift: float, color, light, edge):
        sx, sy = x0 - 4 + shift, gy - 44 + cr
        lift = pose.wing
        elbow = (sx - 14 + shift * 0.2, sy - 26 - lift * 18)
        tip = (sx - 46, sy - 22 - lift * 34)
        fingers = [(sx - 50, sy - 4 - lift * 18), (sx - 40, sy + 6 - lift * 6), (sx - 24, sy + 10)]
        c.poly([(sx, sy), elbow, tip, *fingers, (sx - 6, sy + 8)], color)
        c.line((sx, sy), elbow, light, 3)
        c.line(elbow, tip, light, 2)
        for f in fingers:
            c.line(elbow, f, edge)
        for f in (tip, *fingers):
            crystal(c, (f[0] + 3, f[1]), (f[0] - 4, f[1] + 3), 1.5, glow)

    wing(8, P.BLUE_L, P.ICE_L, P.BLUE)

    # Tail curling along the ground behind, crystal spikes on top.
    pts = []
    for k in range(16):
        t = k / 15
        tx = x0 - 26 - t * 52
        ty = gy - 22 + t * 18 - math.sin(t * math.pi * 1.2 + pose.tail) * 5 + (t ** 3) * -10
        pts.append((tx, ty, 9 - t * 6))
    for i, (tx, ty, rad) in enumerate(pts):
        c.ellipse(tx, ty, rad, rad, P.ICE_L if i % 2 else P.WHITE)
    for i in (3, 7, 11):
        tx, ty, rad = pts[i]
        crystal(c, (tx, ty - rad + 1), (tx - 3, ty - rad - 6), 2, glow)
    tx, ty, _ = pts[-1]
    crystal(c, (tx + 1, ty), (tx - 7, ty - 5), 2.5, glow)

    # Far legs.
    for lx in (x0 - 20, x0 + 14):
        c.rect(lx - 3, gy - 18 + cr, lx + 3, gy - 2, P.BLUE_L)
        c.ellipse(lx + 2, gy - 2, 5, 2.5, P.BLUE_L)

    # Body.
    fluffy(c, x0, gy - 32 + cr, 31, 19 - cr * 0.3, P.ICE_L, 201, 18)
    fluffy(c, x0 + 2, gy - 34 + cr, 26, 15, P.WHITE, 202, 14)
    c.ellipse(x0 + 4, gy - 20 + cr, 22, 6, P.BLUE_L)                  # belly shadow
    for k in range(4):                                               # back crests
        bx = x0 - 14 + k * 9
        crystal(c, (bx, gy - 48 + cr + abs(k - 1.5)), (bx - 4, gy - 58 + cr), 2.5, glow)

    # Near legs: thick, furry, with blue claws.
    for lx, step in ((x0 - 16, 0), (x0 + 18, 1)):
        fluffy(c, lx, gy - 16 + cr * 0.5, 7, 9 - cr * 0.3, P.WHITE, 210 + step, 8)
        c.rect(lx - 4, gy - 10, lx + 4, gy - 2, P.WHITE)
        c.ellipse(lx + 2, gy - 2, 6, 2.5, P.ICE_L)
        for k in range(3):
            c.rect(lx + 2 + k * 3, gy - 1, lx + 3 + k * 3, gy, P.ICE_D)

    # Neck and head.
    hx, hy = x0 + 46 + pose.head_dx, gy - 64 + cr + pose.head_dy
    for k in range(9):
        t = k / 8
        nx = x0 + 20 + (hx - 6 - (x0 + 20)) * t
        ny = gy - 40 + cr + (hy + 4 - (gy - 40 + cr)) * t - math.sin(t * math.pi) * 6
        fluffy(c, nx, ny, 10 - t * 2, 10 - t * 2, P.WHITE if k % 2 else P.ICE_L, 220 + k, 7)
        if k in (2, 4, 6):
            crystal(c, (nx - 6, ny - 6), (nx - 13, ny - 11), 2, glow)

    # Horns (back), skull, snout and jaw.
    crystal(c, (hx - 6, hy - 7), (hx - 22, hy - 18), 3.5, glow)
    crystal(c, (hx - 1, hy - 9), (hx - 12, hy - 24), 3, glow)
    fluffy(c, hx, hy, 12, 10, P.WHITE, 230, 10)
    jaw_drop = pose.jaw * 9
    c.poly([(hx + 4, hy + 3), (hx + 22, hy + 3 + jaw_drop * 0.6), (hx + 20, hy + 7 + jaw_drop),
            (hx + 4, hy + 8)], P.ICE_L)                               # lower jaw
    if pose.jaw > 0.2:
        c.poly([(hx + 6, hy + 3), (hx + 21, hy + 3), (hx + 20, hy + 3 + jaw_drop * 0.7)], P.ICE_D)
        for k in range(3):
            c.px(hx + 10 + k * 4, hy + 4, P.WHITE)
    c.ellipse(hx + 13, hy - 1, 11, 5, P.WHITE)                      # upper snout
    c.ellipse(hx + 14, hy + 1, 9, 2.5, P.ICE_L)
    c.rect(hx + 21, hy - 3, hx + 22, hy - 2, P.ICE_D)               # nostril
    c.ellipse(hx - 4, hy + 2, 4, 3, P.ICE_L)                        # cheek fluff
    ex, ey = hx + 3, hy - 4
    if pose.eye == "open":
        c.ellipse(ex, ey, 3, 3, P.CYAN)
        c.rect(ex, ey - 2, ex + 1, ey + 2, P.NAVY)
        c.px(ex - 1, ey - 2, P.WHITE)
        c.line((ex - 4, ey - 5), (ex + 4, ey - 3), P.BLUE_D, 2)      # frosty brow
    elif pose.eye == "shut":
        c.line((ex - 3, ey), (ex + 3, ey + 1), P.NAVY, 2)
    else:
        c.line((ex - 2, ey - 2), (ex + 2, ey + 2), P.NAVY)
        c.line((ex - 2, ey + 2), (ex + 2, ey - 2), P.NAVY)
    # Crystal whiskers: two long drooping strands from the snout, a crystal bead at each end.
    for k, (length, droop) in enumerate(((22, 12), (16, 16))):
        wx, wy = hx + 16 - k * 3, hy + 2 + k
        prev = (wx, wy)
        for i in range(1, 9):
            t = i / 8
            p = (wx + length * t * 0.7 - k * 6 * t, wy + droop * t * t + math.sin(t * 3 + pose.tail) * 1.5)
            c.line(prev, p, P.CYAN if i % 3 else P.ICE_L)
            prev = p
        crystal(c, (prev[0], prev[1] - 1), (prev[0] + 1, prev[1] + 5), 1.8, glow)

    wing(0, P.ICE_L, P.WHITE, P.BLUE_L)

    if pose.shards:
        for k in range(pose.shards):
            a = math.radians(-50 + k * 25)
            sx, sy = hx + 28 + math.cos(a) * 10, hy + 2 + math.sin(a) * 14
            crystal(c, (sx - 4, sy), (sx + 5, sy), 2, True)
    if pose.breath:
        rnd = noise(240 + pose.breath)
        for k in range(5):
            px = hx + 22 + k * 3 + pose.breath
            py = hy + 6 + k * 2.5 + rnd() * 2
            c.ellipse(px, py, 2 + k * 0.6, 2 + k * 0.5, P.WHITE if k % 2 else P.ICE_L)

    underside(big.img)
    big.outline(P.ICE_D)
    img = big.img
    if pose.tilt:
        img = img.rotate(-pose.tilt, resample=Image.NEAREST, center=(CX, GROUND - pose.lift - 40))
    return img


def build() -> list[Sprite]:
    boss = Sprite("boss_icedragon", SIZE, faces_left=True, cx=CX, ground=GROUND)
    boss.add("idle", [dragon(DragonPose(wing=w, tail=t, head_dy=dy, eye=e)) for w, t, dy, e in (
        (0.0, 0.0, 0, "open"), (0.2, 0.5, -1, "open"), (0.35, 1.0, -1, "open"), (0.2, 1.5, 0, "open"),
        (0.0, 2.0, 1, "open"), (-0.1, 2.5, 1, "shut"))], fps=6)

    boss.add("shards", [dragon(p) for p in (
        DragonPose(wing=0.5, head_dx=-4, head_dy=-4, glow=1, crouch=2),
        DragonPose(wing=0.9, head_dx=-8, head_dy=-8, glow=1, crouch=3, shards=1),
        DragonPose(wing=1.0, head_dx=-8, head_dy=-9, glow=1, crouch=3, shards=3),
        DragonPose(wing=0.8, head_dx=4, head_dy=-2, jaw=1, glow=1, shards=5),
        DragonPose(wing=0.4, head_dx=6, head_dy=0, jaw=0.8),
        DragonPose(wing=0.1, head_dx=2, jaw=0.3),
    )], fps=10, loop=False)

    boss.add("breath", [dragon(p) for p in (
        DragonPose(wing=0.4, head_dx=-6, head_dy=-6, crouch=1),
        DragonPose(wing=0.6, head_dx=-8, head_dy=-8, crouch=2, jaw=0.3),
        DragonPose(wing=0.2, head_dx=4, head_dy=18, jaw=1, breath=1),
        DragonPose(wing=0.1, head_dx=6, head_dy=22, jaw=1, breath=2),
        DragonPose(wing=0.0, head_dx=7, head_dy=24, jaw=1, breath=3),
        DragonPose(wing=0.1, head_dx=6, head_dy=22, jaw=1, breath=2),
        DragonPose(wing=0.2, head_dx=4, head_dy=16, jaw=0.6, breath=1),
        DragonPose(wing=0.1, head_dx=0, head_dy=4, jaw=0.2),
    )], fps=10, loop=False)

    boss.add("dive", [dragon(p) for p in (
        DragonPose(crouch=6, wing=1.0, head_dy=4),
        DragonPose(lift=10, wing=-0.6, head_dy=-6),
        DragonPose(lift=26, wing=1.0, head_dy=-4, jaw=0.5),
        DragonPose(lift=24, wing=0.6, tilt=24, jaw=1, head_dx=4),
        DragonPose(lift=10, wing=0.4, tilt=30, jaw=1, head_dx=6),
        DragonPose(crouch=4, wing=0.2, tilt=6, jaw=0.4),
    )], fps=8, loop=False)

    hurt = dragon(DragonPose(eye="shut", jaw=0.6, head_dx=-6, head_dy=-4, wing=0.7, crouch=2))
    boss.add("hurt", [tint(hurt, P.WHITE, 0.8), hurt], fps=10)

    frames = []
    for k in range(8):
        t = k / 7
        img = dragon(DragonPose(eye="x", jaw=0.5, wing=-0.4 - t * 0.6, head_dy=t * 34, head_dx=t * 4,
                                crouch=min(10, t * 14)))
        if k == 0:
            img = tint(img, P.WHITE, 0.7)
        elif k >= 3:
            img = see_through(img, r(255 * (1 - (k - 2) / 6)))
        frame = Canvas(*SIZE)
        frame.paste(img)
        rnd = noise(300 + k)
        for _ in range(int(t * 30)):                                   # bursting into snowflakes
            frame.px(36 + rnd() * 120, GROUND - 10 - rnd() * 80 + t * 10, P.WHITE)
        frames.append(frame.img)
    boss.add("death", frames, fps=8, loop=False)
    return [boss]
