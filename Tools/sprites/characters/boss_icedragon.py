"""World 2 boss: Glacipurr, a white-and-lavender ice dragon (190x134; about 120 long and 110 tall with its
wings raised). It sits up like a cat: a feline face with pointed ears, crystal horns and spines, big bat
wings with blue membranes and a tail curled along the ground. Fires ice shards, breathes a freezing cloud
and dives wrapped in crystals."""
from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image

import palette as P
from bosskit import bezier, blob, crystal, part, tube
from draw import Canvas, noise, r, see_through, shatter, tint
from sprite import Sprite

SIZE = (190, 134)
CX, GROUND = 90, 130

SCALES = {P.GL_WHITE: (None, P.GL_LAV_L)}
SCALES2 = {P.GL_LAV_L: (None, P.GL_LAV)}
WING2 = {P.GL_WING: (None, P.GL_WING_D)}
FAR = {P.GL_LAV: (None, P.GL_LAV_D)}


@dataclass
class DragonPose:
    lift: float = 0
    crouch: float = 0
    tilt: float = 0            # degrees the whole dragon pitches nose-down (dive)
    head_dx: float = 0
    head_dy: float = 0
    jaw: float = 0             # 0 shut ... 1 wide open
    wing: float = 0.3          # -1 folded ... 1 raised high
    tail: float = 0
    eye: str = "open"          # open | shut | x | angry
    glow: bool = False         # crystals lit up (charging)
    breath: int = 0            # freezing breath pouring from the mouth (frame index + 1)
    shards: int = 0            # shards forming in front of the mouth
    encased: bool = False      # wrapped in a shell of crystals (dive)


def ice(c: Canvas, base, tip, width: float, glow: bool) -> None:
    if glow:
        crystal(c, base, tip, width, light=P.WHITE, mid=P.ICE_L, dark=P.CYAN, shine=P.WHITE)
    else:
        crystal(c, base, tip, width, light=P.ICE_L, mid=P.CYAN, dark=P.BLUE, shine=P.WHITE)


def wing(c: Canvas, sx: float, sy: float, lift: float, far: bool) -> None:
    """A bat wing from the shoulder (sx, sy): a white arm bone, finger bones and blue membranes."""
    spread = (0.55 + 0.45 * (lift + 1) / 2) * (0.8 if far else 1.0)   # folded wings are smaller
    wrist = (sx - 20 * spread, sy - 40 * spread - 12 * lift)
    tips = [(wrist[0] - 56 * spread, wrist[1] - 12 * spread - 4 * lift), (wrist[0] - 66 * spread, wrist[1] + 36 * spread),
            (wrist[0] - 46 * spread, wrist[1] + 62 * spread), (wrist[0] - 16 * spread, wrist[1] + 72 * spread)]
    root = (sx - 4, sy + 18)
    outline = [(sx, sy), wrist, tips[0]]
    for a, b in zip(tips, tips[1:] + [root]):                  # scalloped trailing edge
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        outline += [(mid[0] + (wrist[0] - mid[0]) * 0.22, mid[1] + (wrist[1] - mid[1]) * 0.22), b]
    membrane, edge = (P.GL_LAV, P.GL_LAV_D) if far else (P.GL_WING, P.GL_DEEP)
    with part(c, FAR if far else WING2, edge, up=1, down=6, left=1, right=4) as k:
        k.poly(outline, membrane)
    if not far:                                                  # lighter panels near the arm bone
        for a, b in zip([wrist] + tips[:-1], tips):
            c.poly([wrist, ((wrist[0] * 2 + a[0]) / 3, (wrist[1] * 2 + a[1]) / 3),
                    ((wrist[0] * 2 + b[0]) / 3, (wrist[1] * 2 + b[1]) / 3)], P.GL_WING_L)
    bone, bone_d = (P.GL_LAV_L, P.GL_LAV) if far else (P.GL_WHITE, P.GL_LAV_L)
    with part(c, {bone: (None, bone_d)}, P.GL_LAV_D if far else P.GL_LAV, down=1, right=1) as k:
        k.line((sx, sy), wrist, bone, 5)
        for tip in tips:
            k.line(wrist, tip, bone, 2)
        k.ellipse(wrist[0], wrist[1], 3, 3, bone)
    if not far:
        ice(c, (wrist[0] + 1, wrist[1] - 1), (wrist[0] + 4, wrist[1] - 9), 2, False)


def dragon(pose: DragonPose) -> Image.Image:
    c = Canvas(*SIZE)
    gy = GROUND - pose.lift
    cr = pose.crouch
    glow = pose.glow
    hx, hy = 136 + pose.head_dx, gy - 90 + cr + pose.head_dy

    # Far wing, peeking up behind the shoulders.
    wing(c, 112, gy - 58 + cr, pose.wing, far=True)

    # Tail: along the ground behind, its tip curling up, crystal spines on top.
    sway = math.sin(pose.tail) * 4
    tail_pts = bezier([(64, gy - 16, 11), (34, gy - 2, 8), (10, gy - 4, 6), (8 + sway, gy - 28, 4),
                       (22 + sway, gy - 30, 3)], 22)
    with part(c, SCALES, P.GL_LAV_D, up=1, down=4, left=1, right=2, ramp2=SCALES2) as k:
        tube(k, tail_pts, P.GL_WHITE)
    for i in (3, 7, 11, 15):
        x, y, rad = tail_pts[i]
        ice(c, (x + 2, y - rad + 2), (x - 3, y - rad - 6 + i * 0.15), 2, glow)

    # Far legs.
    with part(c, FAR, P.GL_LAV_D) as k:
        k.ellipse(132, gy - 4, 8, 4, P.GL_LAV)
        k.line((128, gy - 34 + cr), (132, gy - 6), P.GL_LAV, 8)

    # Body: big round haunch, barrel chest rising into the neck.
    with part(c, SCALES, P.GL_LAV_D, up=2, down=12, left=2, right=8, ramp2=SCALES2) as k:
        blob(k, 96, gy - 30 + cr * 0.6, 32, 24 - cr * 0.3, P.GL_WHITE, 201, 16, 3)
        blob(k, 120, gy - 46 + cr * 0.8, 17, 24, P.GL_WHITE, 202, 10, 3)
    # Lavender rune swirls on the flank, like frost on glass.
    for k, (rx, ry, rad) in enumerate(((86, gy - 34, 7), (104, gy - 26, 4))):
        for i in range(10):
            a = i / 10 * math.tau * 0.8 + k
            c.px(rx + math.cos(a) * rad, ry + cr * 0.6 + math.sin(a) * rad * 0.8, P.GL_LAV)
    # Back crystals along the spine.
    for i in range(5):
        bx = 70 + i * 10
        by = gy - 52 + cr * 0.7 - math.sin(i / 4 * math.pi) * 4 - i * 2
        ice(c, (bx + 2, by + 4), (bx - 5, by - 10 - (i % 2) * 4), 3, glow)

    # Haunch and hind foot.
    with part(c, SCALES, P.GL_LAV_D, up=2, down=10, left=2, right=7, ramp2=SCALES2) as k:
        blob(k, 74, gy - 24 + cr * 0.4, 20, 19, P.GL_WHITE, 210, 10, 2.5)
        k.ellipse(86, gy - 4, 13, 4.5, P.GL_WHITE)
    c.line((62, gy - 30 + cr * 0.4), (70, gy - 38 + cr * 0.4), P.GL_LAV)
    for i in range(3):
        c.poly([(94 + i * 4, gy - 3), (98 + i * 4, gy), (94 + i * 4, gy)], P.BLUE)

    # Neck: curving up from the chest to the head, banded with lavender belly scales.
    neck = bezier([(120, gy - 50 + cr, 14), (128, gy - 70 + cr, 11), (hx - 14, hy + 20, 9), (hx - 6, hy + 4, 8)], 14)
    with part(c, SCALES, P.GL_LAV_D, up=2, down=4, left=2, right=6, ramp2=SCALES2) as k:
        tube(k, neck, P.GL_WHITE)
    for i in range(1, 13):                                      # banded belly scales down the throat
        x, y, rad = neck[i]
        c.line((x + rad * 0.15, y + rad * 0.3), (x + rad * 0.85, y - rad * 0.1), P.GL_LAV_L if i % 2 else P.GL_LAV, 1)
    for i in range(4):
        c.line((112 + i, gy - 44 + cr + i * 7), (126 - i, gy - 46 + cr + i * 7), P.GL_LAV_L)
    for i in (2, 5, 8, 11):                                     # crystal spines down the back of the neck
        x, y, rad = neck[i]
        ice(c, (x - rad + 3, y - 2), (x - rad - 6, y - 6), 2.2, glow)

    # Front legs, the near one in front of the chest.
    with part(c, SCALES, P.GL_LAV_D, up=1, down=3, left=1, right=3, ramp2=SCALES2) as k:
        blob(k, 124, gy - 40 + cr * 0.8, 10, 14, P.GL_WHITE, 215, 7, 2.5)       # chest
        k.line((126, gy - 30 + cr * 0.6), (128, gy - 6), P.GL_WHITE, 8)
        k.ellipse(131, gy - 4, 8, 4.5, P.GL_WHITE)
    for i in range(3):
        c.poly([(131 + i * 3, gy - 3), (135 + i * 3, gy), (131 + i * 3, gy)], P.BLUE)
    c.line((125, gy - 20 + cr * 0.5), (125, gy - 8), P.GL_LAV_L)

    # Head: crystal horns, cat ears, round skull, short cat muzzle and an open fanged jaw.
    ice(c, (hx - 8, hy - 6), (hx - 28, hy - 24), 4, glow)
    ice(c, (hx - 2, hy - 8), (hx - 14, hy - 30), 3.5, glow)
    with part(c, SCALES, P.GL_LAV_D, down=2, ramp2=SCALES2) as k:
        k.poly([(hx - 12, hy - 4), (hx - 6, hy - 22), (hx + 2, hy - 8)], P.GL_WHITE)
        k.poly([(hx - 2, hy - 8), (hx + 6, hy - 22), (hx + 10, hy - 6)], P.GL_WHITE)
    c.poly([(hx - 9, hy - 6), (hx - 6, hy - 17), (hx - 1, hy - 8)], P.PINK)
    c.poly([(hx + 1, hy - 8), (hx + 6, hy - 17), (hx + 8, hy - 7)], P.PINK)
    jaw = pose.jaw * 9
    if pose.jaw > 0.15:                                        # mouth interior behind the jaw
        c.poly([(hx + 2, hy + 4), (hx + 22, hy + 3), (hx + 20, hy + 5 + jaw), (hx + 4, hy + 9)], P.RED_D)
        c.poly([(hx + 6, hy + 5), (hx + 18, hy + 5), (hx + 16, hy + 4 + jaw)], P.PINK_D)
    with part(c, SCALES, P.GL_LAV_D, up=1, down=2, left=1, right=2, ramp2=SCALES2) as k:
        k.poly([(hx + 2, hy + 6), (hx + 22, hy + 6 + jaw * 0.8), (hx + 20, hy + 10 + jaw), (hx + 2, hy + 12)],
               P.GL_WHITE)                                      # lower jaw
    with part(c, SCALES, P.GL_LAV_D, up=2, down=3, left=2, right=2, ramp2=SCALES2) as k:
        blob(k, hx, hy, 14, 12, P.GL_WHITE, 230, 10, 2)
        k.poly([(hx + 2, hy - 8), (hx + 16, hy - 5), (hx + 25, hy - 1), (hx + 26, hy + 3), (hx + 24, hy + 6),
                (hx + 2, hy + 7)], P.GL_WHITE)                   # muzzle
        k.ellipse(hx + 8, hy - 7, 6, 2.5, P.GL_WHITE)             # brow ridge
        for i in range(3):                                      # spiky cheek ruff
            k.poly([(hx - 10, hy + 2 + i * 3), (hx - 20 - i * 2, hy + 4 + i * 5), (hx - 8, hy + 6 + i * 3)],
                   P.GL_WHITE)
    for i in range(2):                                          # fangs
        fx = hx + 10 + i * 9
        c.poly([(fx, hy + 6), (fx + 1, hy + 10 + (pose.jaw > 0.15)), (fx + 2, hy + 6)], P.WHITE)
    c.ellipse(hx + 23, hy, 1.5, 1, P.GL_DEEP)                    # nostril
    c.line((hx + 6, hy + 5), (hx + 22, hy + 5), P.GL_LAV)       # lip line
    ex, ey = hx + 5, hy - 3
    if pose.eye in ("open", "angry"):
        c.poly([(ex - 4, ey), (ex - 1, ey - 3), (ex + 4, ey - 2), (ex + 3, ey + 2), (ex - 2, ey + 2)],
               P.CYAN if not glow else P.ICE_L)
        c.rect(ex + 1, ey - 2, ex + 1, ey + 1, P.NAVY)
        c.px(ex - 2, ey - 1, P.WHITE)
        c.line((ex - 5, ey - 4 - 2 * (pose.eye == "angry")), (ex + 4, ey - 3), P.GL_DEEP)
    elif pose.eye == "shut":
        c.line((ex - 3, ey + 1), (ex + 3, ey), P.GL_DEEP, 2)
    else:
        c.line((ex - 2, ey - 2), (ex + 2, ey + 2), P.NAVY)
        c.line((ex - 2, ey + 2), (ex + 2, ey - 2), P.NAVY)

    # Near wing over the body.
    wing(c, 104, gy - 62 + cr, pose.wing, far=False)

    if pose.shards:
        for k in range(pose.shards):
            a = math.radians(-40 + k * 22)
            sx, sy = hx + 30 + math.cos(a) * 6, hy + 6 + math.sin(a) * 16
            ice(c, (sx - 5, sy), (sx + 7, sy), 2.5, True)
    if pose.breath:
        frost = Canvas(*SIZE)
        rnd = noise(240 + pose.breath)
        path = bezier([(hx + 22, hy + 8), (hx + 30, hy + 14), (hx + 28, gy - 14), (hx + 34, gy - 8)], 24)
        reach = 0.35 + pose.breath * 0.22
        puffs = []
        for i, (x, y) in enumerate(path):
            t = i / (len(path) - 1)
            if t > reach:
                break
            for _ in range(2):
                rad = 2.5 + t * 7 + rnd() * 2
                px_ = min(x + (rnd() - 0.5) * t * 8, 184 - rad)
                puffs.append((px_, min(y + (rnd() - 0.5) * 4, gy - rad), rad))
        for layer, colour in enumerate((P.GL_WING, P.BLUE_L, P.ICE_L, P.WHITE)):
            for x, y, rad in puffs:
                rr = rad * (1 - layer * 0.27)
                frost.ellipse(x - layer * 0.8, y - layer * 0.8, rr, rr * 0.85, colour)
        for i in range(6):                                      # glittering ice crystals in the cloud
            frost.px(hx + 24 + rnd() * 22, hy + 10 + rnd() * (gy - hy - 14), P.WHITE)
        frost.outline(P.GL_WING_D)
        c.paste(see_through(frost.img, 240))
    if pose.encased:                                            # a shell of crystals around the body
        for k in range(11):
            a = math.radians(-170 + k * 30)
            bx, by = 104 + math.cos(a) * 30, gy - 44 + math.sin(a) * 26
            ice(c, (bx, by), (bx + math.cos(a) * 18, by + math.sin(a) * 15), 3.6, k % 2 == 0)

    c.rect(0, gy + 1, SIZE[0] - 1, SIZE[1] - 1, P.CLEAR)
    c.outline(P.GL_EDGE)
    img = c.img
    if pose.tilt:
        img = img.rotate(-pose.tilt, resample=Image.NEAREST, center=(104, gy - 46))
    return img


def burst(c: Canvas, x: float, step: int) -> None:
    """Crystals erupting from the ground where it lands."""
    for k, (dx, h, lean) in enumerate(((-26, 14, -8), (-14, 22, -4), (0, 30, 0), (12, 22, 5), (24, 14, 9))):
        height = h * min(1.0, 0.5 + step * 0.25)
        ice(c, (x + dx, GROUND), (x + dx + lean, GROUND - height), 4, k % 2 == 0)


def build() -> list[Sprite]:
    boss = Sprite("boss_icedragon", SIZE, faces_left=True, cx=CX, ground=GROUND)
    boss.add("idle", [dragon(DragonPose(wing=w, tail=t, head_dy=dy, eye=e)) for w, t, dy, e in (
        (0.5, 0.0, 0, "open"), (0.65, 0.6, -1, "open"), (0.75, 1.2, -1, "open"), (0.65, 1.8, 0, "open"),
        (0.5, 2.4, 1, "open"), (0.4, 3.0, 1, "shut"))], fps=6)

    boss.add("shards", [dragon(p) for p in (
        DragonPose(wing=0.6, head_dx=-4, head_dy=-3, glow=True, crouch=2, eye="angry"),
        DragonPose(wing=0.9, head_dx=-6, head_dy=-5, glow=True, crouch=3, shards=1, eye="angry"),
        DragonPose(wing=1.0, head_dx=-6, head_dy=-6, glow=True, crouch=3, shards=3, jaw=0.3, eye="angry"),
        DragonPose(wing=0.7, head_dx=4, head_dy=2, jaw=1, glow=True, shards=5, eye="angry"),
        DragonPose(wing=0.4, head_dx=5, head_dy=2, jaw=0.7),
        DragonPose(wing=0.3, head_dx=2, jaw=0.2),
    )], fps=10, loop=False)

    boss.add("breath", [dragon(p) for p in (
        DragonPose(wing=0.5, head_dx=-6, head_dy=-4, crouch=1, jaw=0.2),
        DragonPose(wing=0.7, head_dx=-10, head_dy=-6, crouch=2, jaw=0.5, eye="angry"),
        DragonPose(wing=0.3, head_dx=0, head_dy=14, jaw=1, breath=1, eye="angry"),
        DragonPose(wing=0.2, head_dx=2, head_dy=18, jaw=1, breath=2, eye="angry"),
        DragonPose(wing=0.1, head_dx=2, head_dy=20, jaw=1, breath=3, eye="angry"),
        DragonPose(wing=0.2, head_dx=2, head_dy=18, jaw=1, breath=2, eye="angry"),
        DragonPose(wing=0.3, head_dx=0, head_dy=12, jaw=0.6, breath=1),
        DragonPose(wing=0.3, head_dx=0, head_dy=4, jaw=0.2),
    )], fps=10, loop=False)

    dive = []
    for k, p in enumerate((
        DragonPose(crouch=6, wing=0.9, head_dy=4, eye="angry"),
        DragonPose(lift=8, wing=-0.6, head_dy=8, eye="angry", glow=True),
        DragonPose(lift=12, wing=-1, tilt=14, head_dy=6, jaw=0.5, glow=True, encased=True, eye="angry"),
        DragonPose(lift=8, wing=-1, tilt=24, jaw=0.8, glow=True, encased=True, eye="angry"),
        DragonPose(crouch=4, wing=-0.2, tilt=8, jaw=0.6, eye="angry"),
        DragonPose(crouch=2, wing=0.4, jaw=0.2),
    )):
        frame = Canvas(*SIZE)
        frame.paste(dragon(p))
        if k >= 4:
            b = Canvas(*SIZE)
            burst(b, 150, k - 3)
            b.outline(P.GL_EDGE)
            frame.paste(b)
        dive.append(frame.img)
    boss.add("dive", dive, fps=8, loop=False)

    hurt = dragon(DragonPose(eye="shut", jaw=0.7, head_dx=-8, head_dy=-4, wing=0.8, crouch=2))
    boss.add("hurt", [tint(hurt, P.WHITE, 0.8), hurt], fps=10)

    # Slumps, freezes solid and shatters into crystals.
    frames = []
    for k in range(8):
        t = k / 7
        body = dragon(DragonPose(eye="x", jaw=0.5, wing=0.3 - min(1, t * 2) * 1.3, head_dy=min(1, t * 2) * 30,
                                 head_dx=min(1, t * 2) * 4, crouch=min(8, t * 16)))
        if k == 0:
            body = tint(body, P.WHITE, 0.7)
        elif k >= 3:
            body = tint(body, P.CYAN, min(0.6, (k - 2) * 0.2))
        if k >= 4:
            body = shatter(body, (k - 3) / 4, 310, block=6, spread=0.18, gravity=1.0, origin=(100, GROUND - 40))
        frame = Canvas(*SIZE)
        frame.paste(body)
        if k >= 3:
            b = Canvas(*SIZE)
            burst(b, 104, min(3, k - 2))
            b.outline(P.GL_EDGE)
            frame.paste(see_through(b.img, r(255 * (1 - max(0, t - 0.6) * 2))))
        frames.append(frame.img)
    boss.add("death", frames, fps=8, loop=False)
    return [boss]
