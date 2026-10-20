"""The app icon: the kitten's face over a ball of yarn, drawn at 64x64 so it stays bold when the
system shrinks it to a home-screen or settings icon."""
from __future__ import annotations

import math

from PIL import Image

import palette as P
from draw import Canvas


def draw_icon() -> Image.Image:
    sky = Canvas(64, 64)
    c = sky
    bands = (P.NAVY, P.BLUE_D, P.BLUE_D, P.BLUE, P.BLUE)
    for i, colour in enumerate(bands):                      # sky, dithered between bands
        c.rect(0, i * 13, 63, i * 13 + 13, colour)
        if i:
            for x in range(0, 64, 2):
                c.px(x + (i % 2), i * 13, bands[i - 1])
    c.ellipse(31.5, 34, 29, 27, P.BLUE_L)                    # halo behind the head
    c.ellipse(31.5, 34, 26, 24, P.BLUE)
    for x, y in ((6, 6), (56, 9), (9, 52), (58, 46), (50, 4)):
        c.px(x, y, P.WHITE)

    c = Canvas(64, 64)                                       # the kitten, outlined on its own layer
    # Ears.
    for side in (-1, 1):
        bx = 31.5 + side * 15
        c.poly([(bx - 8, 24), (bx + side * 3, 4), (bx + 8, 24)], P.GINGER)
        c.poly([(bx - 4, 22), (bx + side * 3, 9), (bx + 4, 22)], P.PINK)

    # Head: round, with fluffy cheeks.
    c.ellipse(31.5, 33, 22, 18, P.GINGER)
    c.ellipse(31.5, 39, 25, 13, P.GINGER)
    for side in (-1, 1):
        c.poly([(31.5 + side * 23, 38), (31.5 + side * 28, 42), (31.5 + side * 22, 45)], P.GINGER)
    c.ellipse(31.5, 47, 20, 5, P.GINGER_D)                   # shade under the chin
    c.ellipse(31.5, 45, 22, 5, P.GINGER)
    for dx in (-6, 0, 6):                                    # forehead stripes
        c.rect(31 + dx, 17, 32 + dx, 23 - abs(dx) // 3, P.GINGER_DD)
    for side in (-1, 1):                                     # cheek stripes
        for k in range(2):
            c.line((31.5 + side * 24, 34 + k * 4), (31.5 + side * 18, 35 + k * 4), P.GINGER_DD, 2)

    # Big eyes.
    for side in (-1, 1):
        ex = 31.5 + side * 10
        c.ellipse(ex, 33, 6, 7, P.OUTLINE)
        c.ellipse(ex, 33, 5, 6, P.LEAF_L)
        c.ellipse(ex, 34, 3, 5, P.BLACK)
        c.rect(ex - 3, 28, ex - 1, 30, P.WHITE)
        c.px(ex + 2, 37, P.WHITE)

    # Muzzle, nose and mouth, whiskers.
    c.ellipse(31.5, 43, 9, 5.5, P.CREAM)
    c.poly([(29, 39), (34, 39), (31.5, 42)], P.PINK)
    c.line((31.5, 42), (31.5, 44), P.OUTLINE)
    c.line((31.5, 44), (28.5, 46), P.OUTLINE)
    c.line((31.5, 44), (34.5, 46), P.OUTLINE)
    for side in (-1, 1):
        for k in (-1, 1):
            c.line((31.5 + side * 10, 43 + k), (31.5 + side * 19, 41 + k * 3), P.WHITE)

    # A ball of yarn in the corner, its loose thread trailing off.
    c.outline()
    yarn = Canvas(64, 64)
    yx, yy, rad = 51, 52, 10
    for k in range(14):
        yarn.px(yx - 11 - k, yy + 8 + math.sin(k * 0.8) * 1.2, P.YARN_L)
    yarn.ellipse(yx, yy, rad, rad, P.YARN)
    for k, (ox, oy) in enumerate(((-5, -5), (-2, -8), (2, -10))):        # wound strands: arcs
        for i in range(24):
            a = math.radians(-10 + i * 5)
            x, y = yx + ox + math.cos(a) * (rad + 1), yy + oy + 6 + math.sin(a) * (rad + 1)
            if (x - yx) ** 2 + (y - yy) ** 2 < (rad - 0.5) ** 2:
                yarn.px(x, y, P.YARN_D)
    for i in range(20):
        a = math.radians(100 + i * 6)
        x, y = yx + 7 + math.cos(a) * 12, yy - 4 + math.sin(a) * 12
        if (x - yx) ** 2 + (y - yy) ** 2 < (rad - 0.5) ** 2:
            yarn.px(x, y, P.YARN_D)
    yarn.ellipse(yx - 4, yy - 5, 2.5, 1.5, P.YARN_L)
    yarn.outline()
    c.paste(yarn)
    out = sky.img.copy()
    out.alpha_composite(c.img)
    return out
