"""The app icon: the caped kitten leaping up and to the right, eyes shut with joy and mouth wide open,
over a bright sky with a castle on a floating island, waterfalls and grassy brick blocks.

Drawn on a 128x128 grid and scaled up by whole pixels (8x to 1024). Fully opaque and full-bleed: iOS
applies its own rounded mask, so ears, paw and castle stay inside the outer 10% (x and y in 13...115).
"""
from __future__ import annotations

import math

from PIL import Image, ImageFilter

import palette as P
from draw import Canvas, noise

N = 128


# ---------------------------------------------------------------------------------------------------
# Helpers

def blob(c: Canvas, cx: float, cy: float, rx: float, ry: float, angle: float, colour) -> None:
    """A filled ellipse rotated by `angle` degrees (clockwise)."""
    a = math.radians(angle)
    pts = []
    for k in range(48):
        t = k / 48 * math.tau
        x, y = math.cos(t) * rx, math.sin(t) * ry
        pts.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
    c.poly(pts, colour)


def rot(cx: float, cy: float, angle: float):
    """Maps head-local offsets (x right, y down, unrotated) to icon pixels, for the tilted head."""
    a = math.radians(angle)

    def f(dx: float, dy: float) -> tuple[float, float]:
        return (cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a))
    return f


def bezier(p0, p1, p2, t):
    u = 1 - t
    return (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0], u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])


def arc(c: Canvas, f, cx: float, cy: float, r: float, a0: float, a1: float, colour, width: int = 2) -> None:
    """An arc in head-local space; angles in degrees, 0 = right, 90 = down."""
    prev = None
    for k in range(13):
        a = math.radians(a0 + (a1 - a0) * k / 12)
        p = f(cx + math.cos(a) * r, cy + math.sin(a) * r)
        if prev:
            c.line(prev, p, colour, width)
        prev = p


def paw_pad(c: Canvas, x: float, y: float, s: float, angle: float) -> None:
    """A white paw seen from below: a pink pad and four toe beans."""
    f = rot(x, y, angle)
    blob(c, x, y, 7.5 * s, 8.5 * s, angle, P.FUR_WHITE)
    blob(c, *f(0, 2.6 * s), 3.4 * s, 2.6 * s, angle, P.PINK)
    for dx, dy in ((-4.4, -2.2), (-1.6, -4.6), (1.6, -4.6), (4.4, -2.2)):
        blob(c, *f(dx * s, dy * s), 1.4 * s, 1.6 * s, angle, P.PINK)


# ---------------------------------------------------------------------------------------------------
# Background

def sky() -> Canvas:
    c = Canvas(N, N)
    bands = (P.ICON_SKY_TOP, P.ICON_SKY, P.ICON_SKY_L, P.ICON_HAZE)
    edges = (0, 34, 70, 96, N)
    for i, colour in enumerate(bands):                     # bands with a dithered seam between them
        c.rect(0, edges[i], N - 1, edges[i + 1] - 1, colour)
        if i:
            for x in range(0, N, 2):
                c.px(x, edges[i], bands[i - 1])
                c.px(x + 1, edges[i] + 1, bands[i - 1])

    def cloud(x, y, w, puffs):
        for dx, r in puffs:
            c.ellipse(x + dx, y - r * 0.6, r, r * 0.8, P.WHITE)
        c.rect(x - 2, y - 1, x + w, y + 2, P.WHITE)
        c.rect(x - 1, y + 2, x + w - 1, y + 3, P.BLUE_L)

    cloud(4, 16, 30, ((2, 6), (10, 8), (19, 7), (27, 5)))
    cloud(14, 30, 16, ((2, 4), (8, 6), (14, 4)))
    cloud(84, 10, 34, ((3, 5), (12, 7), (22, 6), (31, 4)))
    for x, y in ((50, 9), (56, 7), (44, 13)):              # little puffs
        c.rect(x, y, x + 2, y + 1, P.WHITE)

    # Soft distant cliffs along the horizon, two shades.
    rnd = noise(41)
    for colour, base, amp, step in ((P.ICON_CLIFF_L, 78, 10, 7), (P.ICON_CLIFF, 90, 9, 5)):
        x = 0
        while x < N:
            w = step + int(rnd() * step)
            top = base - int(rnd() * amp)
            c.rect(x, top, x + w, N - 1, colour)
            c.rect(x, top, x + w, top, P.ICON_HAZE if colour == P.ICON_CLIFF_L else P.ICON_CLIFF_L)
            x += w
    return c


def island(c: Canvas, x0: int, x1: int, y: int, depth: int) -> None:
    """A floating island: a grass cap over rock tapering to a point."""
    mid = (x0 + x1) / 2
    c.poly([(x0, y), (x1, y), (mid + 2, y + depth), (mid - 2, y + depth)], P.BROWN)
    c.poly([(x0, y), (mid - 1, y), (mid - 2, y + depth)], P.BROWN_D)
    c.rect(x0 - 1, y - 2, x1 + 1, y + 1, P.GREEN)
    c.rect(x0 - 1, y - 3, x1 + 1, y - 3, P.GREEN_L)
    for x in range(x0, x1 + 1, 3):
        c.px(x, y + 2, P.GREEN_D)


def waterfall(c: Canvas, x: int, y0: int, y1: int, w: int) -> None:
    c.rect(x, y0, x + w - 1, y1, P.BLUE_L)
    for k in range(w):
        c.line((x + k, y0 + (k * 5) % 7), (x + k, y1 - (k * 3) % 5), P.WHITE if k % 2 else P.CYAN)
    c.ellipse(x + w / 2, y1, w / 2 + 2, 2, P.WHITE)       # spray at the foot


def castle(c: Canvas, x: int, y: int) -> None:
    """A small castle on a floating island, red cone roofs and a flag; (x, y) is the island's top left."""
    island(c, x, x + 18, y, 12)
    stone, shade = P.SAND, P.BROWN_L
    c.rect(x + 2, y - 10, x + 16, y - 3, stone)            # curtain wall
    for k in range(4):
        c.rect(x + 2 + k * 4, y - 11, x + 3 + k * 4, y - 11, stone)
    c.rect(x + 8, y - 7, x + 10, y - 3, P.BROWN_D)          # gate
    for tx, h in ((x + 1, 15), (x + 7, 20), (x + 14, 16)):
        c.rect(tx, y - h, tx + 3, y - 3, stone)
        c.rect(tx, y - h, tx, y - 3, shade)
        c.px(tx + 2, y - h + 3, P.BROWN_D)                 # window
        c.poly([(tx - 1, y - h), (tx + 4, y - h), (tx + 1.5, y - h - 6)], P.RED)
        c.poly([(tx - 1, y - h), (tx + 1.5, y - h), (tx + 1.5, y - h - 6)], P.RED_D)
    c.line((x + 8.5, y - 26), (x + 8.5, y - 29), P.BROWN_D)
    c.rect(x + 9, y - 29, x + 11, y - 28, P.RED)


def block(c: Canvas, x0: int, y0: int, x1: int, y1: int) -> None:
    """A chunky grass-topped brick block."""
    c.rect(x0, y0, x1, y1, P.BROWN)
    for row, y in enumerate(range(y0 + 6, y1 + 1, 6)):     # brick courses
        c.rect(x0, y, x1, y, P.BROWN_D)
        for x in range(x0 + (row % 2) * 5, x1, 10):
            c.rect(x, y - 5, x, y, P.BROWN_D)
            c.rect(x + 1, y - 5, x + 3, y - 5, P.BROWN_L)
    c.rect(x0, y0, x1, y0 + 4, P.GREEN)                    # grass cap with a ragged lip
    c.rect(x0, y0, x1, y0, P.LEAF_L)
    c.rect(x0, y0 + 1, x1, y0 + 1, P.GREEN_L)
    for x in range(x0, x1 + 1, 2):
        c.rect(x, y0 + 5, x, y0 + 5 + (x * 7 % 3), P.GREEN)
        c.px(x + 1, y0 + 2, P.GREEN_L)


def leaf(c: Canvas, x: float, y: float, angle: float) -> None:
    blob(c, x, y, 3.2, 1.6, angle, P.GREEN_L)
    f = rot(x, y, angle)
    c.line(f(-3, 0), f(3, 0), P.GREEN)


def background() -> Canvas:
    c = sky()
    # Floating islands with waterfalls on the right, castle on the top one.
    waterfall(c, 111, 64, 94, 4)
    castle(c, 101, 62)
    island(c, 100, 116, 84, 8)
    waterfall(c, 105, 88, 110, 4)
    island(c, 6, 18, 58, 7)
    # Grassy brick blocks: lower left (tall, and a slab in front) and lower right.
    block(c, -1, 80, 22, N)
    block(c, -1, 106, 58, N)
    block(c, 82, 112, N, N)
    for x, y, a in ((24, 72, -30), (40, 102, 20), (88, 100, -50)):
        leaf(c, x, y, a)
    return c


# ---------------------------------------------------------------------------------------------------
# The kitten

TILT = 22   # the head tilts this many degrees clockwise


def kitten() -> Canvas:
    fur, fur_l, fur_d, stripe = P.GINGER, P.GINGER_L, P.GINGER_D, P.GINGER_DD
    white = P.FUR_WHITE
    c = Canvas(N, N)

    # Tail: a fluffy plume rising behind the head, curling at its white tip (top left).
    tail = Canvas(N, N)                                     # outlined on its own, so it parts from the head
    p0, p1, p2 = (40, 56), (24, 4), (11, 34)
    for k in range(29):
        t = k / 28
        x, y = bezier(p0, p1, p2, t)
        r = 6 + 3.5 * math.sin(t * math.pi * 0.9) - 3.5 * max(0.0, t - 0.8) / 0.2
        colour = white if t > 0.88 else (stripe if k in (7, 8, 15, 16) else fur)
        tail.ellipse(x, y, r, r, colour)
    for k in range(5):                                      # fluffy tufts along the outer edge
        x, y = bezier(p0, p1, p2, 0.2 + k * 0.15)
        tail.poly([(x - 6, y - 2), (x - 11, y - 5), (x - 5, y - 6)], fur)
    x, y = bezier(p0, p1, p2, 0.5)
    blob(tail, x + 1, y, 3, 2, -40, fur_l)
    c.paste(tail.outline())

    # Cape: streaming back to the left from the shoulders, rippling, light top edge.
    top, bottom = [], []
    for k in range(13):
        t = k / 12
        x = 62 - t * 56
        y = 66 - t * 8 + math.sin(t * 7.0) * 3.5 * t
        w = 7 + 9 * t
        top.append((x, y - w / 2))
        bottom.append((x + t * 3, y + w / 2))
    tip = [(6, 52), (2, 60), (8, 58), (5, 67)]              # ragged end
    c.poly(top + tip + bottom[::-1], P.CAPE)
    c.poly([((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in zip(top, bottom)] + bottom[::-1], P.CAPE_D)
    for a, b in zip(top, top[1:]):
        c.line(a, b, P.CAPE_L, 2)

    # Body: a round striped barrel angled down-left, white chest.
    blob(c, 57, 80, 21, 17, -38, fur)
    blob(c, 55, 85, 17, 10, -38, fur_d)
    blob(c, 58, 79, 18, 14, -38, fur)
    for k in range(4):                                      # bands across the body
        x, y = 44 + k * 6, 70 + k * 6
        c.line((x, y), (x + 5, y - 7), stripe, 2)
    blob(c, 70, 76, 7, 9, -38, white)

    # Satchel at the hip, behind the strap.
    c.rect(34, 70, 47, 83, P.BROWN)
    c.rect(34, 70, 47, 75, P.BROWN_D)
    c.rect(35, 83, 46, 83, P.BROWN_D)
    c.rect(39, 74, 41, 76, P.GOLD)

    # Hind leg tucked under, its paw toward us showing beans.
    blob(c, 54, 92, 9, 7, 40, fur)
    c.line((50, 89), (56, 95), stripe, 2)
    paw_pad(c, 60, 98, 1.0, -20)

    # Strap across the body with a gold buckle.
    c.line((46, 72), (74, 91), P.BROWN_D, 5)
    c.line((46, 71), (74, 90), P.BROWN, 3)
    c.line((47, 70), (75, 89), P.BROWN_L, 1)
    c.rect(63, 80, 69, 86, P.GOLD)
    c.rect(65, 82, 67, 84, P.BROWN_D)
    c.px(63, 80, P.YELLOW)

    # The other forepaw, tucked under the chin.
    blob(c, 66, 70, 6.5, 5.5, -20, white)
    c.line((63, 72), (64, 74), P.FUR_WHITE_D)
    c.line((67, 73), (68, 75), P.FUR_WHITE_D)

    # Head: round, tilted, fluffy cheeks; pink-lined ears.
    hx, hy = 70, 41
    f = rot(hx, hy, TILT)
    for base0, tip_, base1 in (((-21, -8), (-10, -33), (-2, -19)), ((8, -19), (24, -28), (22, -4))):
        c.poly([f(*base0), f(*tip_), f(*base1)], fur)
        c.poly([f(base0[0] * 0.8 + base1[0] * 0.2, base0[1] * 0.8 + base1[1] * 0.2 - 1),
                f(tip_[0] * 0.92 + (base0[0] + base1[0]) * 0.04, tip_[1] * 0.92 + (base0[1] + base1[1]) * 0.04 + 1),
                f(base1[0] * 0.8 + base0[0] * 0.2, base1[1] * 0.8 + base0[1] * 0.2 - 1)], P.PINK)
        mid0 = ((base0[0] * 2 + tip_[0]) / 3, (base0[1] * 2 + tip_[1]) / 3)
        mid1 = ((base1[0] * 2 + tip_[0]) / 3, (base1[1] * 2 + tip_[1]) / 3)
        c.line(f(*mid0), f((mid0[0] + mid1[0]) / 2, (mid0[1] + mid1[1]) / 2 + 3), white, 2)   # ear fluff
    blob(c, hx, hy, 26, 21.5, TILT, fur)
    for dx, dy in ((-25, 6), (-22, 13), (24, 9), (19, 17)):  # cheek tufts
        x, y = f(dx, dy)
        out = -4 if dx < 0 else 4
        c.poly([(x, y - 3), (x + out, y + 1), (x, y + 3)], fur)
    blob(c, *f(-6, -12), 11, 5, TILT, fur_l)                # light on the crown
    for k in range(3):                                      # forehead stripes
        c.line(f(-6 + k * 5, -20), f(-5 + k * 5, -13), stripe, 2)
    for k in range(2):                                      # cheek stripes
        c.line(f(-25, 0 + k * 5), f(-18, 1 + k * 5), stripe, 2)

    # White blaze and a big white muzzle and chin.
    c.poly([f(1, -21), f(5, -21), f(9, -2), f(-3, -2)], white)
    blob(c, *f(4, 8), 15, 11, TILT, white)
    blob(c, *f(2, 13), 11, 8, TILT, white)

    # Eyes squeezed shut with joy: two upturned arcs.
    arc(c, f, -9, -1, 5, 200, 340, P.OUTLINE, 2)
    arc(c, f, 15, -1, 5, 200, 340, P.OUTLINE, 2)
    # Pink nose, then a wide open mouth: dark inside, pink tongue, one little fang.
    blob(c, *f(3, 3), 2.5, 1.8, TILT, P.PINK)
    c.poly([f(-5, 7), f(11, 7), f(9, 13), f(3, 17), f(-3, 13)], P.ICON_MOUTH)
    blob(c, *f(3, 14), 5, 2.6, TILT, P.PINK)
    c.poly([f(-3, 7), f(0, 7), f(-1.5, 10)], white)
    c.line(f(3, 4), f(3, 7), P.ICON_MOUTH)
    # Blush.
    blob(c, *f(-14, 7), 3, 1.6, TILT, P.PINK)
    blob(c, *f(20, 6), 2.5, 1.5, TILT, P.PINK)

    # Scarf knotted round the neck.
    c.line(f(-16, 22), f(12, 23), P.CAPE, 4)
    c.line(f(-15, 20), f(10, 21), P.CAPE_L, 1)
    blob(c, *f(-12, 25), 3.5, 2.5, TILT, P.CAPE_D)

    # Near foreleg stretched forward and up, paw toward us with its beans showing.
    c.line((76, 62), (96, 68), fur, 9)
    for k in range(3):
        x = 80 + k * 5
        c.line((x, 58 + k * 1.5), (x - 1, 66 + k * 1.5), stripe, 2)
    paw_pad(c, 101, 69, 1.0, -30)
    return c


def glow(cat: Image.Image) -> Image.Image:
    """A soft pale halo around the kitten: two rings, partly see-through, to lift it off the sky."""
    alpha = cat.getchannel("A")
    out = Image.new("RGBA", cat.size, (0, 0, 0, 0))
    for size, a in ((9, 70), (5, 150)):
        ring = alpha.filter(ImageFilter.MaxFilter(size)).point(lambda v, a=a: a if v else 0)
        layer = Image.new("RGBA", cat.size, P.ICON_GLOW[:3] + (0,))
        layer.putalpha(ring)
        out.alpha_composite(layer)
    return out


CAT_SHIFT = (2, 6)   # the whole kitten, moved so its ear tip and paws keep clear of the outer 10%


def draw_icon() -> Image.Image:
    out = background().img.copy()
    drawn = kitten().outline()
    whiskers = Canvas(N, N)                                 # over the outline, so they read as fine lines
    f = rot(70, 41, TILT)
    for dy, dx2, dy2 in ((4, 34, -2), (8, 35, 6), (6, -22, 1), (10, -21, 5)):
        start = f(14 if dx2 > 0 else -12, dy)
        whiskers.line(start, f(dx2, dy + dy2), P.WHITE)
    cat = Image.new("RGBA", (N, N), P.CLEAR)
    cat.alpha_composite(drawn.img, CAT_SHIFT)
    lines = Image.new("RGBA", (N, N), P.CLEAR)
    lines.alpha_composite(whiskers.img, CAT_SHIFT)
    out.alpha_composite(glow(cat))
    out.alpha_composite(cat)
    out.alpha_composite(lines)
    return out.convert("RGB").convert("RGBA")
