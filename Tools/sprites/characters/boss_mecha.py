"""World 4 boss: a giant robotic mouse with a furnace in its chest and a segmented metal tail
(168x124; about 110 long, 92 tall). Fires rockets from its back pods, sweeps its tail along the
ground, and in its last phase opens its chest to expose the core."""
from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image

import palette as P
from draw import Canvas, noise, r, see_through, shatter, tint
from sprite import Sprite

SIZE = (168, 124)
CX, GROUND = 84, 120


@dataclass
class MechaPose:
    bob: float = 0
    core: float = 0.3          # furnace glow 0...1
    hatch: float = 0           # chest plate 0 shut ... 1 open (core exposed)
    pods: float = 0            # rocket pods 0 shut ... 1 open
    rocket: int = 0            # rocket leaving the pod (frame index + 1)
    tail: float = 0            # 0 curled up behind ... 1 swept forward along the ground
    jaw: float = 0
    eye_colour: tuple = P.RED
    steam: int = 0
    shake: float = 0


def rivet_row(c: Canvas, x0: float, x1: float, y: float, step: int = 5) -> None:
    for x in range(int(x0), int(x1), step):
        c.px(x, y, P.IRON_L)
        c.px(x + 1, y + 1, P.IRON_D)


def mecha(pose: MechaPose) -> Image.Image:
    c = Canvas(*SIZE)
    x = CX + pose.shake
    gy = GROUND
    by = gy - 44 + pose.bob

    # Tail: segments from the rump; curled up behind at rest, swept low and forward when attacking.
    t = pose.tail
    segs = []
    for k in range(14):
        u = k / 13
        rest = (x - 36 - math.sin(u * math.pi * 0.9) * 26 - u * 8, by + 6 - u * 44 + math.sin(u * math.pi) * 6)
        sweep = (x - 30 - u * 30 + u * u * 4, gy - 6 - (1 - u) * 14)
        segs.append((rest[0] + (sweep[0] - rest[0]) * t, rest[1] + (sweep[1] - rest[1]) * t, 5 - u * 2.5))
    for k, (sx, sy, rad) in enumerate(segs):
        c.ellipse(sx, sy, rad, rad, P.IRON if k % 2 else P.IRON_L)
        c.px(sx, sy, P.IRON_D)
    tx, ty, _ = segs[-1]
    px, py, _ = segs[-2]
    ang = math.atan2(ty - py, tx - px)
    tip = (tx + math.cos(ang) * 10, ty + math.sin(ang) * 10)
    nx, ny = -math.sin(ang) * 4, math.cos(ang) * 4
    c.poly([(tx + nx, ty + ny), tip, (tx - nx, ty - ny)], P.GREY_L)                 # blade at the tip
    c.line((tx, ty), tip, P.WHITE)

    # Far leg and arm.
    c.rect(x + 8, by + 18, x + 16, gy - 6, P.IRON_D)
    c.ellipse(x + 14, gy - 3, 9, 3.5, P.IRON_D)

    # Rocket pods on the back.
    for k, dx in enumerate((-24, -10)):
        px0, py0 = x + dx, by - 26 - k * 2
        open_y = pose.pods * 5
        c.rect(px0 - 5, py0 - 8, px0 + 5, py0 + 6, P.IRON_D)
        c.rect(px0 - 5, py0 - 8 - open_y, px0 + 5, py0 - 6 - open_y, P.IRON_L)       # lid
        for j in range(2):
            c.ellipse(px0 - 2 + j * 4, py0 - 4, 1.5, 1.5, P.MAROON if pose.pods > 0.3 else P.IRON)
        if pose.rocket and k == (pose.rocket - 1) % 2:
            ry = py0 - 12 - pose.rocket * 6
            c.rect(px0 - 1.5, ry, px0 + 1.5, ry + 8, P.GREY_L)
            c.poly([(px0 - 1.5, ry), (px0, ry - 4), (px0 + 1.5, ry)], P.RED)
            c.ellipse(px0, ry + 11, 2.5, 3.5, P.LAVA)
            c.ellipse(px0, ry + 10, 1.2, 2, P.LAVA_L)

    # Smokestack.
    c.rect(x - 34, by - 30, x - 29, by - 12, P.IRON_D)
    c.rect(x - 35, by - 32, x - 28, by - 30, P.IRON)
    if pose.steam:
        rnd = noise(500 + pose.steam)
        for k in range(3):
            c.ellipse(x - 32 - k * 3 + rnd() * 2, by - 36 - k * 6 - pose.steam, 3 + k, 2.5 + k * 0.8, P.GREY)

    # Hull.
    c.ellipse(x, by, 36, 26, P.IRON)
    c.ellipse(x - 4, by - 8, 28, 15, P.IRON_L)
    c.ellipse(x, by + 12, 30, 12, P.IRON_D)
    c.ellipse(x, by - 2, 33, 23, P.IRON)
    c.ellipse(x - 6, by - 10, 22, 9, P.IRON_L)
    c.line((x - 20, by - 20), (x - 26, by + 14), P.IRON_D)                          # plate seams
    c.line((x + 2, by - 24), (x - 2, by + 20), P.IRON_D)
    rivet_row(c, x - 30, x + 28, by + 16, 6)
    rivet_row(c, x - 20, x + 16, by - 20, 6)
    c.rect(x - 14, by + 4, x - 10, by + 8, P.GOLD_D)                                 # brass vent
    c.line((x - 14, by + 6), (x - 10, by + 6), P.IRON_D)

    # Furnace core in the chest, behind a grate (or a hinged plate when shut tight).
    fx, fy = x + 16, by + 2
    glow = pose.core
    c.ellipse(fx, fy, 11, 11, P.IRON_D)
    c.ellipse(fx, fy, 8.5, 8.5, P.RED if glow < 0.5 else P.LAVA)
    c.ellipse(fx, fy, 5 + glow * 2, 5 + glow * 2, P.LAVA if glow < 0.7 else P.LAVA_L)
    if glow > 0.6:
        c.ellipse(fx, fy, 2.5, 2.5, P.WHITE)
    if pose.hatch < 1:
        for k in range(-2, 3):                                                      # grate bars
            c.line((fx + k * 3.5, fy - 8), (fx + k * 3.5, fy + 8), P.IRON_D, 2)
        if pose.hatch > 0:
            c.poly([(fx - 11, fy - 11), (fx + 11 - pose.hatch * 16, fy - 11 - pose.hatch * 6),
                    (fx + 11 - pose.hatch * 16, fy + 11 - pose.hatch * 6), (fx - 11, fy + 11)], P.IRON_L)
    else:
        c.poly([(fx - 12, fy - 12), (fx - 20, fy - 18), (fx - 20, fy + 6), (fx - 12, fy + 12)], P.IRON_L)
        for k in range(5):                                                          # sparks off the core
            a = k * 1.3 + glow * 3
            c.px(fx + math.cos(a) * 14, fy + math.sin(a) * 13, P.LAVA_L)

    # Near leg: a piston leg with a big clawed foot.
    lx = x - 12
    c.rect(lx - 6, by + 16, lx + 4, gy - 8, P.IRON)
    c.rect(lx - 6, by + 16, lx - 4, gy - 8, P.IRON_L)
    c.rect(lx - 3, gy - 12, lx + 1, gy - 6, P.GREY_L)                                 # piston rod
    c.ellipse(lx + 2, gy - 3, 12, 3.5, P.IRON)
    for k in range(3):
        c.poly([(lx + 9 + k * 3, gy - 4), (lx + 14 + k * 3, gy), (lx + 9 + k * 3, gy)], P.GREY_L)

    # Head: a pointed snout with whisker wires, two round ears, a visor eye.
    hx, hy = x + 36, by - 16
    for ex, ey, rad in ((hx - 16, hy - 18, 10), (hx - 2, hy - 20, 9)):
        c.ellipse(ex, ey, rad, rad, P.IRON)
        c.ellipse(ex, ey, rad - 3.5, rad - 3.5, P.MAROON)
        c.ellipse(ex - 2, ey - 2, rad - 6, rad - 6, P.RED_D)
        c.px(ex - rad + 2, ey - 2, P.IRON_L)
    c.ellipse(hx - 6, hy, 16, 13, P.IRON)
    c.ellipse(hx - 8, hy - 5, 10, 5, P.IRON_L)
    jaw = pose.jaw * 7
    c.poly([(hx + 2, hy + 4), (hx + 30, hy + 4 + jaw * 0.6), (hx + 26, hy + 8 + jaw), (hx, hy + 10)], P.IRON_D)
    if pose.jaw > 0.2:
        c.poly([(hx + 4, hy + 4), (hx + 28, hy + 4), (hx + 26, hy + 4 + jaw * 0.7)], P.MAROON)
    for k in range(4):
        c.poly([(hx + 6 + k * 5, hy + 4), (hx + 8 + k * 5, hy + 7), (hx + 10 + k * 5, hy + 4)], P.WHITE)
    c.poly([(hx + 2, hy - 8), (hx + 32, hy + 2), (hx + 30, hy + 5), (hx + 2, hy + 6)], P.IRON)   # snout
    c.line((hx + 4, hy - 6), (hx + 30, hy + 2), P.IRON_L)
    c.ellipse(hx + 32, hy + 3, 3, 2.5, P.IRON_D)                                    # nose
    c.px(hx + 33, hy + 2, P.GREY_L)
    for k in (-1, 1):                                                               # whisker wires
        c.line((hx + 22, hy + 3), (hx + 38, hy + 1 + k * 5), P.GREY_L)
    c.rect(hx - 6, hy - 6, hx + 6, hy - 1, P.IRON_D)                                # visor
    c.rect(hx - 4, hy - 5, hx + 4, hy - 2, pose.eye_colour)
    c.rect(hx + 2, hy - 5, hx + 3, hy - 4, P.LAVA_L if pose.eye_colour == P.RED else pose.eye_colour)
    rivet_row(c, hx - 18, hx, hy + 8, 5)

    # Near arm with a three-claw grabber.
    ax, ay = x + 26, by + 10
    c.line((ax - 8, ay - 4), (ax, ay + 6), P.IRON_L, 4)
    c.line((ax, ay + 6), (ax + 8, ay + 4), P.IRON, 3)
    for k in range(3):
        c.line((ax + 8, ay + 4), (ax + 12, ay + 1 + k * 3), P.GREY_L)
    c.outline()
    return c.img


def build() -> list[Sprite]:
    boss = Sprite("boss_mecha", SIZE, faces_left=True, cx=CX, ground=GROUND)
    boss.add("idle", [mecha(MechaPose(bob=b, core=g, steam=s)) for b, g, s in
                      ((0, 0.3, 1), (-1, 0.4, 2), (-1, 0.5, 3), (0, 0.4, 0))], fps=5)
    boss.add("rockets", [mecha(p) for p in (
        MechaPose(pods=0.5, core=0.5),
        MechaPose(pods=1.0, core=0.6, bob=1),
        MechaPose(pods=1.0, rocket=1, core=0.7, bob=1, shake=-1),
        MechaPose(pods=1.0, rocket=2, core=0.6, shake=1),
        MechaPose(pods=1.0, rocket=3, core=0.5, steam=2),
        MechaPose(pods=0.4, core=0.4, steam=3),
    )], fps=10, loop=False)
    boss.add("tail", [mecha(p) for p in (
        MechaPose(tail=-0.15, bob=1, jaw=0.3),
        MechaPose(tail=0.2, bob=1, jaw=0.6),
        MechaPose(tail=0.6, jaw=1, shake=-1),
        MechaPose(tail=1.0, jaw=1, shake=1),
        MechaPose(tail=0.8, jaw=0.6),
        MechaPose(tail=0.3, jaw=0.2),
    )], fps=10, loop=False)
    boss.add("core", [mecha(MechaPose(hatch=1, core=g, bob=b, jaw=j, eye_colour=P.LAVA_L))
                      for g, b, j in ((0.7, 0, 0.3), (1.0, -1, 0.5), (0.8, -1, 0.4), (1.0, 0, 0.6))], fps=8)
    hurt = mecha(MechaPose(core=0.9, jaw=0.8, shake=-2, eye_colour=P.WHITE))
    boss.add("hurt", [tint(hurt, P.WHITE, 0.8), hurt], fps=10)

    # Sparks, shakes, then bursts apart in smoke.
    broken = mecha(MechaPose(core=1.0, jaw=1, hatch=1, eye_colour=P.IRON_D))
    frames = [tint(broken, P.WHITE, 0.7)]
    for k in range(1, 8):
        t = k / 7
        frame = Canvas(*SIZE)
        if k < 3:
            frame.paste(mecha(MechaPose(core=1.0, jaw=1, hatch=1, eye_colour=P.IRON_D, shake=(-2, 2)[k % 2])))
        else:
            frame.paste(shatter(broken, (t - 0.3) / 0.7, 520, block=6, spread=0.2, gravity=0.8,
                                origin=(CX + 16, GROUND - 42)))
        rnd = noise(530 + k)
        for _ in range(4 + k):                                                      # smoke and flashes
            sx, sy = CX - 32 + rnd() * 80, GROUND - 20 - rnd() * 60
            frame.ellipse(sx, sy, 3 + rnd() * 4, 3 + rnd() * 3, P.GREY_D if rnd() > 0.3 else P.LAVA)
        frames.append(see_through(frame.img, r(255 * (1 - max(0, t - 0.5)))))
    boss.add("death", frames, fps=10, loop=False)
    return [boss]
