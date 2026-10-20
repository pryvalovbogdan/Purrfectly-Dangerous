"""World 1 boss: a chubby orange squirrel king (112x132; stands about 92px tall with the crown).

Huge curled tail, cream belly and muzzle, a jewelled gold crown, a red cape trimmed with ermine, a red bow
at the collar, a pouch on his belt and an acorn sceptre. Throws acorns from the sceptre, curls into a
rolling ball, and climbs a tree to drop a giant acorn."""
from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image

import palette as P
from bosskit import acorn, bezier, blob, fur, part, tube
from draw import Canvas, noise, r, see_through, tint
from sprite import Sprite

SIZE = (112, 132)
CX, GROUND = 52, 128

FUR = {P.SQ_FUR: (P.SQ_FUR_L, P.SQ_FUR_D)}
CREAMY = {P.CREAM: (None, P.CREAM_D)}


@dataclass
class KingPose:
    lift: float = 0
    squash: float = 0           # body lowered and widened (landing, crouch)
    breathe: float = 0
    tail: float = 0             # sway of the tail's curl, in pixels
    cape: float = 0             # ripple phase of the cape hem
    hand: tuple = (10, 14)      # sceptre paw, relative to the shoulder
    sceptre: float = 8          # sceptre angle, degrees from upright (+ = forward)
    sceptre_len: float = 30
    glow: int = 0               # the sceptre's acorn shining (about to throw)
    nut: bool = False           # a fresh acorn sitting on the sceptre tip
    pouch_hand: tuple = (0, 30)  # the other paw, relative to its shoulder
    climbing: bool = False      # both paws up, gripping a trunk
    giant: bool = False         # hugging a giant golden acorn
    eye: str = "open"           # open | shut | angry | x | wince
    mouth: str = "smile"        # smile | open | shout | flat
    crown: bool = True
    crown_tilt: float = 0
    head_dx: float = 0


def crown(c: Canvas, x: float, y: float, tilt: float = 0) -> None:
    """A gold crown about 20 wide and 12 tall, centred on x, the band's bottom at y."""
    with part(c, {P.GOLD: (P.YELLOW, P.GOLD_D)}, P.GOLD_D, up=1, down=2, right=1) as k:
        k.poly([(x - 10, y), (x + 10, y + tilt), (x + 10, y - 5 + tilt), (x - 10, y - 5)], P.GOLD)
        for dx, h in ((-8, 6), (0, 9), (8, 6)):
            t = tilt * (dx + 10) / 20
            k.poly([(x + dx - 3.5, y - 4 + t), (x + dx, y - 4 - h + t), (x + dx + 3.5, y - 4 + t)], P.GOLD)
            k.ellipse(x + dx, y - 5 - h + t, 1.4, 1.4, P.GOLD)
    c.ellipse(x, y - 3 + tilt / 2, 2.4, 2.8, P.RED)                       # ruby in the middle
    c.px(x - 1, y - 4 + tilt / 2, P.CAPE_L)
    for dx in (-6, 6):
        c.rect(x + dx - 0.5, y - 3 + tilt * (dx + 10) / 20, x + dx + 0.5, y - 2 + tilt * (dx + 10) / 20, P.BLUE)
    c.line((x - 9, y - 1), (x + 9, y - 1 + tilt), P.GOLD_D)
    c.px(x - 1, y - 14 + tilt / 2, P.WHITE)


def tail(c: Canvas, gy: float, sway: float, seed: int = 11) -> None:
    """The great curled tail rising behind him, its tip rolled forward over his back."""
    ctrl = [(42, gy - 14, 7), (16, gy - 6, 12), (10, gy - 58, 16), (20, gy - 102, 13),
            (52 + sway, gy - 104, 9), (44 + sway, gy - 82, 5)]
    pts = bezier(ctrl, 26)
    with part(c, FUR, P.SQ_FUR_DD, up=3, down=3, left=3, right=2) as k:
        tube(k, pts, P.SQ_FUR)
        rnd = noise(seed)
        for x, y, rad in pts[2::2]:                                       # tufts along the outer edge
            a = rnd() * math.tau
            blob(k, x + math.cos(a) * rad * 0.7, y + math.sin(a) * rad * 0.7, rad * 0.45, rad * 0.45,
                 P.SQ_FUR, int(rnd() * 999), 6, 2)
    # A lighter stripe down the middle of the tail and the curl of the spiral.
    for j, (x0, y0, x1, y1) in enumerate(((22, 96, 44, 84), (28, 90, 40, 86))):   # the curl of the spiral
        curl = bezier([(x0 + sway * 0.8, gy - y0), (x1 + sway, gy - y0 - 8 + j * 4),
                       (x1 + 4 + sway, gy - y1 + 2), (x1 - 6 + sway, gy - y1 + 4)], 10)
        for a, b in zip(curl, curl[1:]):
            c.line(a, b, P.SQ_FUR_D, 2 - j)
            c.line((a[0] - 1, a[1] - 1), (b[0] - 1, b[1] - 1), P.SQ_FUR_L)
    for x, y, rad in pts[4:20:3]:                                         # fluffy bands of light fur
        c.line((x - rad * 0.6, y - rad * 0.2), (x - rad * 0.1, y - rad * 0.6), P.SQ_FUR_L, 2)
    fur(c, (0, gy - 115, 60, gy - 6), P.SQ_FUR, P.SQ_FUR_D, seed + 5, 35)
    fur(c, (0, gy - 115, 60, gy - 6), P.SQ_FUR, P.SQ_FUR_L, seed + 6, 30, 2)


def cape(c: Canvas, x: float, top: float, gy: float, ripple: float) -> None:
    """The red cape hanging from his shoulders, flaring behind him, its hem trimmed with ermine."""
    hem = []
    for k in range(9):
        t = k / 8
        hx = x - 30 + t * 64
        hem.append((hx, gy - 1 - abs(math.sin(t * math.pi * 2 + ripple)) * 3))
    with part(c, {P.CAPE: (P.CAPE_L, P.CAPE_D)}, P.CAPE_D, up=2, down=2, left=2, right=3) as k:
        k.poly([(x - 10, top), (x + 18, top), (x + 34, gy - 20), *reversed(hem), (x - 32, gy - 30)], P.CAPE)
    for (ax, ay), (bx, by) in zip(hem, hem[1:]):                          # ermine hem
        c.line((ax, ay - 1), (bx, by - 1), P.FUR_WHITE, 3)
    for hx, hy in hem[1:-1]:
        c.rect(hx, hy - 2, hx, hy - 1, P.BLACK)
    for k in range(3):                                                    # folds
        fx = x - 20 + k * 8
        c.line((fx + 6, top + 14), (fx - 2, gy - 8), P.CAPE_D)


def king(pose: KingPose) -> Canvas:
    c = Canvas(*SIZE)
    x = CX
    gy = GROUND - pose.lift
    sq = pose.squash
    bob = pose.breathe + sq
    hx, hy = x + 8 + pose.head_dx, gy - 64 + bob

    tail(c, gy + sq * 0.3, pose.tail)
    cape(c, x, gy - 52 + bob, gy, pose.cape)

    # Far foot, then the round body and haunch.
    with part(c, CREAMY, P.CREAM_D) as k:
        k.ellipse(x + 15, gy - 3, 8, 3.5, P.CREAM)
    with part(c, FUR, P.SQ_FUR_DD, up=3, down=4, left=3, right=3) as k:
        blob(k, x + 2, gy - 30 + sq * 0.5 + pose.breathe * 0.5, 24 + sq * 0.5, 28 - sq * 0.6, P.SQ_FUR, 21, 16, 2.5)
        blob(k, x - 8, gy - 14, 14, 13, P.SQ_FUR, 22, 8, 2)               # haunch
    with part(c, CREAMY, None, down=4) as k:
        blob(k, x + 9, gy - 27 + sq * 0.5 + pose.breathe * 0.5, 13 + sq * 0.3, 20 - sq * 0.5, P.CREAM, 23, 10, 2)
    fur(c, (x - 22, gy - 56, x + 26, gy - 4), P.SQ_FUR, P.SQ_FUR_D, 24, 45)
    fur(c, (x, gy - 46, x + 22, gy - 8), P.CREAM, P.CREAM_D, 25, 14, 2)
    c.line((x - 16, gy - 20), (x - 6, gy - 26), P.SQ_FUR_D)               # haunch crease
    with part(c, {P.CAPE: (P.CAPE_L, P.CAPE_D)}, P.CAPE_D, up=1, down=2, left=2, right=2) as k:   # mantle
        sway = math.sin(pose.cape) * 1.5
        k.poly([(x - 8, gy - 52 + bob), (x - 18, gy - 46 + bob), (x - 27 + sway, gy - 8), (x - 20 + sway, gy - 4),
                (x - 14, gy - 30)], P.CAPE)
        k.poly([(x + 20, gy - 50 + bob), (x + 26, gy - 38 + bob), (x + 30 + sway, gy - 6), (x + 24 + sway, gy - 4),
                (x + 22, gy - 30)], P.CAPE)
    c.line((x - 20, gy - 40 + bob), (x - 24, gy - 10), P.CAPE_D)
    with part(c, CREAMY, P.CREAM_D) as k:                                 # near foot
        k.ellipse(x - 4, gy - 3, 10, 3.5, P.CREAM)
    for t in range(3):
        c.line((x + 1 + t * 3, gy - 4), (x + 1 + t * 3, gy - 1), P.CREAM_D)

    # Belt with a gold buckle, and the pouch hanging from it.
    by = gy - 17 + sq * 0.6
    with part(c, {P.BROWN: (P.BROWN_L, None)}, P.BROWN_D) as k:
        k.poly([(x - 20, by - 3), (x + 24, by), (x + 24, by + 3), (x - 20, by)], P.BROWN)
    c.rect(x + 8, by - 2, x + 12, by + 2, P.GOLD)
    c.rect(x + 9, by - 1, x + 11, by + 1, P.BROWN_D)
    with part(c, {P.GOLD_D: (P.GOLD, P.BROWN_D)}, P.BROWN_D, up=3, down=2) as k:
        blob(k, x - 9, by + 6, 8, 7, P.GOLD_D, 26, 7, 2)
        k.poly([(x - 14, by), (x - 4, by), (x - 6, by + 3), (x - 12, by + 3)], P.GOLD_D)
    c.line((x - 13, by + 1), (x - 5, by + 1), P.CAPE)                     # drawstring
    c.px(x - 11, by + 6, P.YELLOW)
    c.px(x - 6, by + 8, P.YELLOW)

    def arm(shoulder, hand, colour=P.SQ_FUR, bend=(-3, 3)) -> None:
        elbow = ((shoulder[0] + hand[0]) / 2 + bend[0], (shoulder[1] + hand[1]) / 2 + bend[1])
        with part(c, FUR, P.SQ_FUR_DD, up=1, down=2) as k:
            k.line(shoulder, elbow, colour, 7)
            k.line(elbow, hand, colour, 6)
        with part(c, CREAMY, P.CREAM_D, down=2) as k:
            blob(k, hand[0], hand[1], 4, 3.5, P.CREAM, 27, 5, 1.2)

    lshoulder = (x - 6, gy - 50 + bob)
    rshoulder = (x + 16, gy - 44 + bob)
    if pose.climbing:
        arm(lshoulder, (x + 20, hy - 18))
    elif not pose.giant:
        arm(lshoulder, (lshoulder[0] + pose.pouch_hand[0], lshoulder[1] + pose.pouch_hand[1]), bend=(-7, 0))

    # Ermine collar and the red bow.
    with part(c, {P.FUR_WHITE: (None, P.FUR_WHITE_D)}, P.FUR_WHITE_D, down=2) as k:
        for i in range(7):
            blob(k, x - 12 + i * 6, gy - 50 + bob + abs(i - 3) * 0.6, 4, 3.5, P.FUR_WHITE, 30 + i, 5, 1.5)
    for i in (1, 4):
        c.rect(x - 12 + i * 6, gy - 50 + bob, x - 12 + i * 6, gy - 49 + bob, P.BLACK)
    bx, byy = x + 10, gy - 46 + bob
    with part(c, {P.CAPE: (P.CAPE_L, P.CAPE_D)}, P.CAPE_D, down=1) as k:
        k.poly([(bx, byy), (bx - 7, byy - 4), (bx - 7, byy + 4)], P.CAPE)
        k.poly([(bx, byy), (bx + 7, byy - 4), (bx + 7, byy + 4)], P.CAPE)
        k.poly([(bx - 1, byy + 1), (bx - 4, byy + 9), (bx - 1, byy + 7)], P.CAPE)
        k.poly([(bx + 1, byy + 1), (bx + 4, byy + 9), (bx + 1, byy + 7)], P.CAPE)
    c.ellipse(bx, byy, 2, 2, P.GOLD)
    c.px(bx - 1, byy - 1, P.YELLOW)

    # Sceptre arm: paw on a wooden staff topped with a big golden acorn.
    if pose.climbing:
        arm(rshoulder, (x + 30, hy - 8))
    elif pose.giant:
        pass
    else:
        hand = (rshoulder[0] + pose.hand[0], rshoulder[1] + pose.hand[1])
        a = math.radians(pose.sceptre)
        d = (math.sin(a), -math.cos(a))
        low = (hand[0] - d[0] * 12, hand[1] - d[1] * 12)
        top = (hand[0] + d[0] * pose.sceptre_len, hand[1] + d[1] * pose.sceptre_len)
        with part(c, {P.BROWN: (P.BROWN_L, P.BROWN_D)}, P.BROWN_D, up=1, down=1, left=1, right=1) as k:
            k.line(low, top, P.BROWN, 3)
        ring = (hand[0] + d[0] * (pose.sceptre_len - 4), hand[1] + d[1] * (pose.sceptre_len - 4))
        c.line((ring[0] - d[1] * 3, ring[1] + d[0] * 3), (ring[0] + d[1] * 3, ring[1] - d[0] * 3), P.GOLD, 2)
        head = (hand[0] + d[0] * (pose.sceptre_len + 6), hand[1] + d[1] * (pose.sceptre_len + 6))
        if pose.glow:                                                     # sparkles round the acorn
            for j in range(4 + pose.glow):
                a = j * math.tau / (4 + pose.glow) + pose.glow * 0.7
                sx, sy = head[0] + math.cos(a) * (8 + pose.glow), head[1] + math.sin(a) * (8 + pose.glow)
                c.line((sx - 1, sy), (sx + 1, sy), P.YELLOW)
                c.line((sx, sy - 1), (sx, sy + 1), P.YELLOW)
                c.px(sx, sy, P.WHITE)
        with part(c, {P.GOLD: (P.YELLOW, P.GOLD_D)}, P.GOLD_D, up=2, down=2, left=2, right=2) as k:
            acorn(k, head[0], head[1], 1.35, gold=True, angle=pose.sceptre)
        if pose.nut:
            acorn(c, head[0] + d[0] * 11, head[1] + d[1] * 11, 0.8, angle=pose.sceptre)
        arm(rshoulder, hand)
    # Head: ears, round fluffy head, cream muzzle and cheeks.
    for ex, ey, lean in ((hx - 12, hy - 13, -3), (hx + 7, hy - 15, 2)):
        with part(c, FUR, P.SQ_FUR_DD, down=1) as k:
            k.poly([(ex - 6, ey + 6), (ex + lean, ey - 10), (ex + 6, ey + 5)], P.SQ_FUR)
            k.poly([(ex + lean - 1, ey - 9), (ex + lean - 3, ey - 13), (ex + lean + 1, ey - 11)], P.SQ_FUR)
        c.poly([(ex - 3, ey + 4), (ex + lean * 0.8, ey - 6), (ex + 3, ey + 4)], P.PINK)
        c.line((ex - 2, ey + 3), (ex + lean * 0.6, ey - 4), P.PINK_D)
    with part(c, FUR, P.SQ_FUR_DD, up=2, down=3, left=2, right=2) as k:
        blob(k, hx, hy, 20, 17, P.SQ_FUR, 40, 14, 2.2)
        blob(k, hx + 15, hy + 4, 7, 6, P.SQ_FUR, 41, 5, 1.5)             # snout
    with part(c, CREAMY, None, down=2) as k:
        blob(k, hx + 9, hy + 7, 12, 7, P.CREAM, 42, 9, 1.8)              # muzzle and cheeks
        k.ellipse(hx + 17, hy + 4, 5, 3.5, P.CREAM)
    fur(c, (hx - 18, hy - 15, hx + 16, hy + 14), P.SQ_FUR, P.SQ_FUR_D, 43, 20, 2)
    c.ellipse(hx - 9, hy + 5, 4, 2.5, P.SQ_FUR_L)                         # rosy cheek
    c.ellipse(hx + 21, hy + 1, 2, 1.5, P.BROWN_D)                         # nose
    c.px(hx + 21, hy, P.BROWN_L)

    ex, ey = hx + 10, hy - 3
    if pose.eye in ("open", "angry"):
        c.ellipse(ex, ey, 3, 4, P.BLACK)
        c.rect(ex, ey - 3, ex + 1, ey - 2, P.WHITE)
        c.px(ex - 1, ey + 2, P.GREY_L)
        if pose.eye == "angry":
            c.line((ex - 5, ey - 8), (ex + 4, ey - 5), P.SQ_FUR_DD, 2)
        else:
            c.line((ex - 3, ey - 7), (ex + 3, ey - 7), P.SQ_FUR_D)
    elif pose.eye == "shut":
        c.line((ex - 3, ey + 1), (ex + 3, ey + 1), P.BLACK)
        c.px(ex - 3, ey, P.BLACK)
    elif pose.eye == "wince":
        c.line((ex - 3, ey - 3), (ex + 2, ey), P.BLACK)
        c.line((ex + 2, ey), (ex - 3, ey + 3), P.BLACK)
    else:
        c.line((ex - 3, ey - 3), (ex + 3, ey + 3), P.BLACK)
        c.line((ex - 3, ey + 3), (ex + 3, ey - 3), P.BLACK)

    mx, my = hx + 17, hy + 8
    if pose.mouth == "smile":
        c.line((mx - 4, my - 1), (mx - 2, my), P.BROWN_D)
        c.line((mx - 2, my), (mx, my - 1), P.BROWN_D)
    elif pose.mouth == "flat":
        c.line((mx - 4, my), (mx, my), P.BROWN_D)
    else:
        big = 2 if pose.mouth == "shout" else 1
        c.ellipse(mx - 2, my + big, 3, 1.5 + big, P.RED_D)
        c.rect(mx - 3, my - 1, mx - 1, my, P.WHITE)                      # buck teeth

    if pose.crown:
        crown(c, hx - 2, hy - 13, pose.crown_tilt)

    if pose.giant:                                                        # hugging the giant golden acorn
        gx, gy2 = x + 24, gy - 30 + bob
        arm(lshoulder, (gx - 12, gy2 + 2))
        with part(c, {P.GOLD: (P.YELLOW, P.GOLD_D)}, P.GOLD_D, up=3, down=3, left=3, right=3) as k:
            acorn(k, gx, gy2, 2.6, gold=True, angle=-15)
        arm(rshoulder, (gx + 4, gy2 + 12))
    return c


def finish(c: Canvas) -> Image.Image:
    """Trims anything that sank below the ground line (fur tufts, the cape hem), then outlines."""
    c.rect(0, GROUND + 1, SIZE[0] - 1, SIZE[1] - 1, P.CLEAR)
    return c.outline().img


def tree(c: Canvas, alpha: int = 255) -> None:
    """The oak he climbs: a thick trunk behind him and a crown of leaves."""
    t = Canvas(*SIZE)
    with part(t, {P.BROWN: (P.BROWN_L, P.BROWN_D)}, P.BROWN_D, up=1, down=1, left=3, right=3) as k:
        k.poly([(CX + 4, GROUND), (CX + 14, GROUND - 12), (CX + 16, 34), (CX + 36, 34), (CX + 38, GROUND - 12),
                (CX + 50, GROUND)], P.BROWN)
        k.line((CX + 24, 46), (CX - 8, 28), P.BROWN, 4)
    rnd = noise(70)
    for _ in range(14):                                                   # bark
        bx, by = CX + 18 + rnd() * 16, 40 + rnd() * 80
        t.line((bx, by), (bx + rnd() * 2 - 1, by + 4 + rnd() * 6), P.BROWN_D)
    with part(t, {P.GREEN: (P.LEAF_L, P.GREEN_D)}, P.FOREST, up=3, down=4, left=3, right=3) as k:
        for i, (lx, ly, lr) in enumerate(((CX - 12, 28, 16), (CX + 14, 22, 18), (CX + 36, 32, 13),
                                          (CX + 24, 42, 14), (CX - 26, 38, 9))):
            blob(k, lx, ly, lr, lr * 0.75, P.GREEN, 71 + i, 10, 3)
    fur(t, (CX - 40, 4, CX + 52, 56), P.GREEN, P.GREEN_D, 76, 40, 2)
    for i in range(6):
        t.px(CX - 20 + i * 11, 24 + (i * 7) % 16, P.LEAF_L)
    t.outline()
    c.paste(see_through(t.img, alpha) if alpha < 255 else t.img)


def rolling_ball(step: int, frames: int) -> Image.Image:
    """Curled up into a ball of fur wrapped in his tail, kicking up a trail of dust."""
    rad = 26
    m = 40
    ball = Canvas(2 * m, 2 * m)
    with part(ball, FUR, P.SQ_FUR_DD, up=4, down=4, left=4, right=4) as k:
        blob(k, m, m, rad, rad, P.SQ_FUR, 80, 18, 2.5)
    for j in range(3):                                                     # the tail wrapped round as a spiral
        pts = [(m + math.cos(a) * (rad - 4 - j * 7 - a * 1.2), m + math.sin(a) * (rad - 4 - j * 7 - a * 1.2))
               for a in [i / 12 * 3.4 for i in range(13)]]
        for a, b in zip(pts, pts[1:]):
            ball.line(a, b, P.SQ_FUR_D, 2)
            ball.line((a[0] - 1, a[1] - 1), (b[0] - 1, b[1] - 1), P.SQ_FUR_L)
    with part(ball, {P.CAPE: (P.CAPE_L, P.CAPE_D)}, P.CAPE_D) as k:       # a flap of cape
        k.poly([(m - 18, m + 8), (m - 4, m + 20), (m - 10, m + 24), (m - 22, m + 14)], P.CAPE)
    ball.ellipse(m + 12, m - 6, 6, 4, P.CREAM)                              # tucked snout
    ball.rect(m + 16, m - 8, m + 17, m - 7, P.BROWN_D)
    ball.line((m + 6, m - 12), (m + 10, m - 11), P.BLACK)                  # squeezed-shut eye
    fur(ball, (m - rad, m - rad, m + rad, m + rad), P.SQ_FUR, P.SQ_FUR_D, 81, 40, 2)
    turned = ball.img.rotate(-360 / frames * step, resample=Image.NEAREST, center=(m, m))
    c = Canvas(*SIZE)
    cx = CX + 4
    dust = Canvas(*SIZE)                                                  # dust kicked up behind
    rnd = noise(90 + step)
    for k in range(9):
        t = k / 8
        dx = cx - rad - 4 - t * 16
        size = 2.5 + t * 4 + rnd() * 1.5
        dust.ellipse(dx, GROUND - size * 0.8 - rnd() * 3 - (k + step) % 2, size, size * 0.8,
                     (P.SAND, P.CREAM_D, P.BROWN_L)[(k + step) % 3])
    dust.outline(P.BROWN)
    c.paste(see_through(dust.img, 210))
    for k in range(3):                                                    # speed lines
        ly = GROUND - 14 - k * 12
        c.line((cx - rad - 18 - (k + step) % 3 * 3, ly), (cx - rad - 6, ly), P.WHITE)
    c.paste(turned, cx - m, GROUND - rad - m)
    crown(c, cx + 2, GROUND - 2 * rad - 2 + (step % 2) * 2, tilt=(-2, 2)[step % 2])
    return finish(c)


def build() -> list[Sprite]:
    boss = Sprite("boss_squirrel", SIZE, faces_left=True, cx=CX, ground=GROUND)

    boss.add("idle", [finish(king(KingPose(tail=t, breathe=b, cape=w, eye=e, sceptre=s)))
                      for t, b, w, e, s in ((0, 0, 0, "open", 8), (2, -1, 0.8, "open", 9),
                                            (3, -1, 1.6, "open", 10), (1, 0, 2.4, "shut", 9))], fps=4)

    boss.add("throw", [finish(king(p)) for p in (
        KingPose(hand=(4, 4), sceptre=-10, glow=1, eye="angry", mouth="flat"),
        KingPose(hand=(-6, -10), sceptre=-55, glow=2, nut=True, squash=2, eye="angry", mouth="flat", tail=-2,
                 cape=0.6),
        KingPose(hand=(-2, -14), sceptre=-30, glow=3, nut=True, squash=3, eye="angry", mouth="shout", tail=-3,
                 cape=1.2),
        KingPose(hand=(6, 0), sceptre=45, glow=1, mouth="shout", eye="angry", tail=3, cape=1.8, sceptre_len=22),
        KingPose(hand=(12, 6), sceptre=38, glow=1, mouth="open", tail=2, cape=2.4, sceptre_len=24),
        KingPose(hand=(10, 14), sceptre=14, tail=1),
    )], fps=10, loop=False)

    boss.add("roll", [rolling_ball(k, 6) for k in range(6)], fps=14)

    # Scrambles up an oak, plucks a giant golden acorn from the leaves and drops it.
    climb = []
    for k, p in enumerate((
        KingPose(squash=6, climbing=True, eye="angry", mouth="flat", tail=-3),
        KingPose(lift=10, climbing=True, eye="angry", mouth="flat", tail=-4, cape=1),
        KingPose(lift=18, giant=True, eye="open", mouth="open", tail=-2, cape=2),
        KingPose(lift=18, giant=True, eye="angry", mouth="shout", tail=2, cape=3, squash=-2),
        KingPose(lift=16, hand=(10, -2), sceptre=48, sceptre_len=20, eye="angry", mouth="smile", tail=3),
        KingPose(squash=5, eye="open", mouth="smile", tail=1),
    )):
        frame = Canvas(*SIZE)
        tree(frame, (255, 255, 255, 255, 255, 110)[k])
        frame.paste(king(p))
        if k == 4:                                                         # the acorn just let go
            for j in range(3):
                frame.line((CX + 30 + j * 6, GROUND - 60 + j * 3), (CX + 30 + j * 6, GROUND - 46 + j * 3), P.WHITE)
        climb.append(finish(frame))
    boss.add("climb", climb, fps=8, loop=False)

    hurt = finish(king(KingPose(eye="wince", mouth="shout", hand=(2, 2), sceptre=-30, squash=2, tail=-3,
                                crown_tilt=-3, head_dx=-2)))
    boss.add("hurt", [tint(hurt, P.WHITE, 0.8), hurt], fps=10)

    # Dazed, topples over backwards and fades; the crown tumbles off and rolls away.
    dazed = finish(king(KingPose(eye="x", mouth="open", crown=False, hand=(8, 18), sceptre=30, squash=3)))
    frames = []
    for k in range(8):
        t = k / 7
        frame = Canvas(*SIZE)
        if k < 3:
            body = dazed.rotate((0, 3, -3)[k], resample=Image.NEAREST, center=(CX, GROUND))
        else:                                                              # flops down in a heap
            p = (k - 2) / 5
            squat = dazed.resize((r(SIZE[0] * (1 + p * 0.03)), r(SIZE[1] * (1 - p * 0.45))), Image.NEAREST)
            body = Image.new("RGBA", SIZE, P.CLEAR)
            body.alpha_composite(squat.crop((r((squat.width - SIZE[0]) / 2), 0,
                                             r((squat.width - SIZE[0]) / 2) + SIZE[0], squat.height)),
                                 (0, GROUND + 2 - r((GROUND + 2) * (1 - p * 0.45))))
        if k >= 5:
            body = see_through(body, r(255 * (1 - (k - 4) / 4.5)))
        body.paste(P.CLEAR, (0, GROUND + 2, SIZE[0], SIZE[1]))
        frame.paste(tint(body, P.WHITE, 0.7) if k == 0 else body)
        cc = Canvas(*SIZE)
        fall_y = min(GROUND - 1, GROUND - 92 + t * t * 160)
        crown(cc, CX + 20 + k * 3, fall_y, tilt=(0, -3, 3, -2, 2, 0, 0, 0)[k])
        if k in (1, 2):                                                    # dizzy stars
            for j in range(3):
                a = j * 2.1 + k
                frame.px(CX + 8 + math.cos(a) * 12, GROUND - 92 + math.sin(a) * 4, P.YELLOW)
        frame.paste(cc.outline().img)
        frames.append(frame.img)
    boss.add("death", frames, fps=8, loop=False)
    return [boss]
