"""World 2, the frost: snowballs, sliding penguins, icicles, snowdrifts, ice patches and crumbling
ice ledges."""
from __future__ import annotations

import math

from PIL import Image

import palette as P
from characters.forest import platform, rolling, slick
from draw import Canvas, noise, shatter, vanish
from sprite import Sprite, single


def snowball() -> Sprite:
    def ball(c):
        c.ellipse(7.5, 7.5, 6.5, 6.5, P.ICE_L)
        c.ellipse(8.5, 8.5, 5, 5, P.WHITE)
        c.ellipse(9.5, 10, 3, 2.4, P.BLUE_L)
        rnd = noise(71)
        for _ in range(5):
            c.px(3 + rnd() * 10, 3 + rnd() * 10, P.BLUE_L)
        c.rect(4, 4, 5, 4, P.WHITE)
        c.px(11, 5, P.CYAN)                       # a pebble frozen in, so the roll shows

    sprite = Sprite("snowball", (16, 16), faces_left=True)
    roll = rolling(ball, 16, outline=P.ICE_D)
    sprite.add("roll", roll, fps=14)
    sprite.add("death", [shatter(roll[0], t / 3, 72, block=3, spread=0.8) for t in range(4)], fps=14, loop=False)
    return sprite


def penguin_body(c: Canvas, x: float, gy: float, step: int, eye: str = "open") -> None:
    """A penguin sliding on its belly, about 20x9, beak forward."""
    flap = (0, 1, 0, -1)[step % 4]
    c.poly([(x - 9, gy - 3), (x - 12, gy - 5 - flap), (x - 12, gy - 1 + flap)], P.ORANGE)    # feet trailing
    c.ellipse(x, gy - 4, 9, 4, P.NAVY)                       # back
    c.ellipse(x + 0.5, gy - 2.2, 8, 2.4, P.WHITE)            # belly on the ice
    c.ellipse(x + 7, gy - 5.5, 4, 3.5, P.NAVY)               # head
    c.ellipse(x + 8.5, gy - 4.2, 2.2, 1.8, P.WHITE)          # face
    c.poly([(x + 10.5, gy - 6), (x + 14, gy - 4.5), (x + 10.5, gy - 3.5)], P.ORANGE)          # beak
    if eye == "x":
        c.px(x + 8, gy - 7, P.BLACK)
        c.px(x + 9, gy - 6, P.BLACK)
    else:
        c.rect(x + 8.5, gy - 7, x + 9, gy - 6, P.BLACK)
        c.px(x + 9, gy - 7, P.WHITE)
    c.line((x - 1, gy - 6), (x - 6, gy - 8 - flap), P.SLATE, 2)                            # flipper swept back
    c.px(x - 3, gy - 7, P.BLUE_D)


def penguin() -> Sprite:
    size, cx, gy = (36, 16), 19, 14
    sprite = Sprite("penguin", size, faces_left=True, cx=cx, ground=gy)
    slide = []
    for i in range(4):
        c = Canvas(*size)
        penguin_body(c, cx, gy, i)
        c.outline()
        for k in range(3):                                    # snow spray kicked up behind
            x = cx - 12 - k * 2 - (i + k) % 2
            c.px(x, gy - 1 - k - (i % 2), P.WHITE if k != 1 else P.ICE_L)
        slide.append(c.img)
    sprite.add("slide", slide, fps=12)
    dead = Canvas(*size)
    penguin_body(dead, cx, gy, 0, eye="x")
    dead.outline()
    sprite.add("death", [vanish(dead.img, t / 3, depth=3) for t in range(4)], fps=10, loop=False)
    return sprite


def icicle_shape(c: Canvas, glint: int = -1) -> None:
    c.rect(0, 0, 11, 2, P.WHITE)                              # snow at the root
    c.rect(1, 3, 10, 3, P.ICE_L)
    for x, length, color in ((3, 12, P.BLUE_L), (6, 20, P.ICE_L), (9, 14, P.BLUE_L)):
        c.poly([(x - 2.5, 3), (x + 2.5, 3), (x, length)], color)
    c.poly([(3.5, 3), (6, 20), (5, 3)], P.CYAN)
    c.line((7, 5), (6.5, 15), P.WHITE)
    if glint >= 0:
        y = 6 + glint * 4
        c.px(6, y, P.WHITE)
        c.px(5, y, P.WHITE)
        c.px(7, y, P.WHITE)
        c.px(6, y - 1, P.WHITE)
        c.px(6, y + 1, P.WHITE)


def icicle() -> Sprite:
    """Hangs from above (the frame's top is the ceiling end); about 10x21."""
    size = (12, 22)
    sprite = Sprite("icicle", size)
    hang = []
    for glint in (-1, 1):
        c = Canvas(*size)
        icicle_shape(c, glint)
        hang.append(c.outline(P.ICE_D).img)
    sprite.add("hang", hang, fps=3)
    fall = []
    for k in range(2):
        c = Canvas(*size)
        c.paste(hang[0], 0, 2)
        for x in (2, 9):
            c.line((x, 0), (x, 2 + k), P.ICE_L)
        fall.append(c.img)
    sprite.add("fall", fall, fps=12)
    base = hang[0]
    sprite.add("shatter", [shatter(base, t / 3, 81, block=3, spread=1.0, origin=(6, 22)) for t in range(4)],
               fps=14, loop=False)
    return sprite


def snowdrift() -> Sprite:
    """A low snow mound (about 22x9)."""
    c = Canvas(24, 11)
    for x, y, rx, ry in ((6, 7, 5, 3.5), (12, 5.5, 7, 4.5), (18, 7, 5, 3.5)):
        c.ellipse(x, y, rx, ry, P.ICE_L)
    c.rect(1, 8, 22, 10, P.ICE_L)
    for x, y, rx, ry in ((5, 6, 2.5, 1.5), (11, 4, 3.5, 2), (17, 6, 2.5, 1.5)):
        c.ellipse(x, y, rx, ry, P.WHITE)
    c.line((3, 9), (20, 9), P.BLUE_L)
    c.px(15, 8, P.BLUE_L)
    c.px(8, 8, P.BLUE_L)
    c.px(13, 2, P.CYAN)
    return single("snowdrift", c.outline(P.ICE_D), ground=10)


def ice_ledge() -> Sprite:
    w, h = 48, 14
    c = Canvas(w, h)
    c.rect(0, 2, w - 1, 8, P.BLUE_L)
    c.rect(0, 6, w - 1, 8, P.CYAN)
    for x in range(0, w, 8):
        c.line((x + 2, 3), (x + 4, 7), P.ICE_L)
    for x, length in ((4, 4), (10, 2), (17, 5), (26, 3), (33, 5), (41, 3)):   # icicles under the slab
        c.poly([(x - 1.5, 9), (x + 1.5, 9), (x, 9 + length)], P.BLUE_L)
    rnd = noise(91)
    for x in range(w):                                    # lumpy snow on top
        top = 1 if rnd() > 0.35 else 0
        c.rect(x, top, x, 2, P.WHITE)
    return platform("ice_ledge", c.outline(P.ICE_D), "crumble", 93)


def build() -> list[Sprite]:
    return [snowball(), penguin(), icicle(), snowdrift(), slick("ice", P.CYAN, P.ICE_L, P.WHITE, 95), ice_ledge()]
