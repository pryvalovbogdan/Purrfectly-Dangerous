"""World 2's environment, the Frostpaw Mountains at night, after docs/concept/Frostpaw Mountains Pixel Tileset
Sheet.png (reference only): a navy sky with an aurora and a full moon, snowy peaks and a glowing ice castle,
a snowy pine forest with a lit hut, snow-capped indigo cobble ground, a frozen waterfall pit and snowy rock
terrain blocks. Same names, sizes and tiling contracts as the forest's (docs/sprite-spec.md); props and
enemies are in characters/frost.py."""
from __future__ import annotations

import math

import palette as P
from characters.scenery import LAYER_W, STONE_ROWS, flat, ground, smooth_sky
from characters.waterfall import colour_at, face, rock
from draw import Canvas, noise, see_through
from sprite import Sprite, single
import woodland as W

ROCK_BIG = (P.FR_ROCK_L, P.FR_ROCK, P.FR_ROCK_D)            # the big stones under the snow
ROCK_SMALL = (P.FR_ROCK, P.FR_ROCK_D, P.FR_ROCK_DD)         # the deep earth's smaller stones
SPECKS = (P.FR_ROCK_D, P.SNOW_DD, P.FR_ICE_D)


# --- shared snow and ice -------------------------------------------------------------------------------

def snow_cap(c: Canvas, width: int, depth: int, seed: int, icicles: bool = True, x0: int = 0) -> None:
    """A thick snow cap over rows 0..depth, with rounded drips below it and icicles. Wraps at `width`, so
    a tile of that width repeats seamlessly. Row 0 is the walk surface."""
    rnd = noise(seed)
    drips = []
    x = 0
    while x < width:                                        # rounded drips under the cap
        w = 4 + int(rnd() * 4)
        drips.append((x + w / 2, w / 2, 1.5 + rnd() * 2.5))
        x += w
    tips = [(int(rnd() * width), 3 + int(rnd() * 5)) for _ in range(max(1, width // 8))]

    def draw(shift):
        c.rect(x0 + shift, 0, x0 + shift + width - 1, depth, P.SNOW_L)
        for dx, rad, drop in drips:
            c.ellipse(x0 + shift + dx, depth, rad, drop, P.SNOW_L)
            c.ellipse(x0 + shift + dx + 0.5, depth + drop - 0.5, rad - 1, 1, P.SNOW)       # shaded underside
        c.rect(x0 + shift, 0, x0 + shift + width - 1, 1, P.WHITE)
        c.rect(x0 + shift, depth - 1, x0 + shift + width - 1, depth - 1, P.SNOW)
        if icicles:
            for tx, length in tips:
                ix = x0 + shift + tx
                c.poly([(ix - 1, depth + 1), (ix + 1, depth + 1), (ix, depth + 1 + length)], P.FR_ICE_L)
                c.line((ix, depth + 1), (ix, depth + length), P.FR_ICE_GLOW)
                c.px(ix - 1, depth + 1, P.WHITE)

    for shift in (-width, 0, width):
        draw(shift)
    for x in range(width):                                  # sparkles in the snow
        if (x * 7 + seed) % 11 == 0:
            c.px(x0 + x, 2 + (x * 3) % 3, P.WHITE)
        if (x * 5 + seed) % 13 == 0:
            c.px(x0 + x, 3, P.SNOW)


def icicle(c: Canvas, x: float, top: float, length: float) -> None:
    c.poly([(x - 1.5, top), (x + 1.5, top), (x, top + length)], P.FR_ICE_L)
    c.line((x - 0.5, top), (x, top + length - 1), P.FR_ICE_GLOW)
    c.px(x + 1, top, P.FR_ICE)


def frost_stones(c: Canvas, y0: int, first: int, rows: int) -> None:
    """Rows of small indigo cobbles 6 high, the same pattern as the forest's grey ones, so the ground tile's
    last rows run straight into the stacked earth tiles."""
    c.rect(0, y0, 31, y0 + rows * 6 - 1, P.FR_ROCK_DD)
    for k in range(rows):
        offset, widths = STONE_ROWS[(first + k) % 6]
        W.cobble_row(c, y0 + k * 6, 7, widths, offset, ROCK_SMALL, 170 + (first + k) % 6, specks=SPECKS)


# --- parallax ------------------------------------------------------------------------------------------

def stars(c: Canvas, seed: int, count: int, y1: int) -> None:
    rnd = noise(seed)
    for _ in range(count):
        x, y = rnd() * LAYER_W, rnd() * y1
        big = rnd() > 0.85
        c.px(x, y, P.STAR if rnd() > 0.4 else P.MOON_S)
        if big:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c.px(x + dx, y + dy, (P.MOON_D[0], P.MOON_D[1], P.MOON_D[2], 150))


def aurora(c: Canvas, base: float, swing: float, height: float, strength: float, phase: float) -> None:
    """A curtain of green and teal light hanging from a wavy upper edge: bright along that edge, fading
    downward in vertical rays, with a violet fringe above. Every wave has whole cycles across the strip, so
    it tiles."""
    for x in range(LAYER_W):
        t = x / LAYER_W * 2 * math.pi
        top = base + swing * math.sin(t * 2 + phase) + swing * 0.4 * math.sin(t * 5 + 1 + phase)
        fold = 0.5 + 0.5 * math.sin(t * 3 + phase)                      # brighter and dimmer stretches
        ray = 0.55 + 0.45 * math.sin(t * 37 + phase) * math.sin(t * 13)  # fine vertical rays
        strength_x = strength * (0.35 + 0.65 * fold) * (0.5 + 0.5 * ray)
        span = height * (0.5 + 0.5 * ray)
        for k in range(int(span)):
            f = 1 - k / span
            a = int(255 * strength_x * f ** 1.6)
            if a < 12:
                continue
            col = P.AURORA_L if k < 2 else P.AURORA if k < span * 0.4 else P.AURORA_T
            c.px(x, top + k, (col[0], col[1], col[2], a))
        for k in range(1, 4):
            c.px(x, top - k, (P.AURORA_V[0], P.AURORA_V[1], P.AURORA_V[2], int(70 * strength_x / k)))


def moon(c: Canvas, x: float, y: float, rad: float) -> None:
    halo = Canvas(*c.size)                                         # glow, blended over the aurora
    for r, a in ((rad + 9, 26), (rad + 5, 46), (rad + 2, 80)):
        layer = Canvas(*c.size)
        layer.ellipse(x, y, r, r, (P.MOON_D[0], P.MOON_D[1], P.MOON_D[2], a))
        halo.paste(layer)
    c.paste(halo)
    c.ellipse(x, y, rad, rad, P.MOON)
    c.ellipse(x + 2, y + 2, rad - 1, rad - 1, P.MOON_S)
    c.ellipse(x - 1, y - 1, rad - 2, rad - 2, P.MOON)
    for cx, cy, cr in ((-4, -3, 2.5), (3, 2, 3), (-2, 5, 1.6), (5, -5, 1.4), (-6, 3, 1.2)):  # craters
        c.ellipse(x + cx, y + cy, cr, cr, P.MOON_S)
        c.px(x + cx + cr * 0.4, y + cy + cr * 0.4, P.MOON_D)


def night_clouds() -> Canvas:
    """The 160-tall layer on the ground line (shows in landscape too): stars, the aurora and the moon."""
    c = Canvas(LAYER_W, 160)
    stars(c, 301, 70, 120)
    aurora(c, 6, 6, 52, 0.85, 0)
    moon(c, 252, 34, 13)
    wisps = Canvas(*c.size)                                   # thin clouds across the light, blended
    for x, y, w in ((214, 46, 30), (266, 52, 24), (40, 96, 50), (150, 104, 40)):
        for k in range(w):
            wisps.px(x + k, y + math.sin(k / 5) * 0.8, P.SNOW_DD)
            if 3 < k < w - 3:
                wisps.px(x + k, y + 1, P.FR_NIGHT_HAZE)
    c.paste(see_through(wisps.img, 100))
    return c


def night_puffs() -> Canvas:
    """The high layer (shows when the screen is tall): more stars and a fainter aurora."""
    c = Canvas(LAYER_W, 120)
    stars(c, 302, 60, 118)
    aurora(c, 50, 10, 46, 0.5, 2)
    return c


def ice_castle(c: Canvas, x: float, base: float) -> None:
    """The glowing ice castle: a wide hall, tall pointed spires, cyan windows, on an icy cliff."""
    glow = Canvas(*c.size)                                   # a soft halo of ice light behind it
    for r, a in ((60, 30), (46, 34), (32, 40)):
        glow.ellipse(x, base - 44, r, r * 0.85, (P.FR_ICE_GLOW[0], P.FR_ICE_GLOW[1], P.FR_ICE_GLOW[2], a))
    c.paste(glow)
    c.poly([(x - 44, base), (x - 38, base - 12), (x + 40, base - 12), (x + 48, base)], P.FR_ICE_D)   # cliff
    c.poly([(x - 38, base - 12), (x + 40, base - 12), (x + 36, base - 8), (x - 34, base - 8)], P.SNOW)
    for k in range(-34, 38, 6):
        c.line((x + k, base - 8), (x + k + 1, base - 2 - (k * 7) % 5), P.FR_ICE)
    towers = [(-26, 34, 6, 16), (-15, 54, 7, 20), (0, 76, 9, 26), (15, 54, 7, 20), (26, 34, 6, 16), (-34, 22, 4, 10),
              (34, 22, 4, 10), (-8, 40, 4, 12), (8, 40, 4, 12)]
    c.rect(x - 30, base - 30, x + 30, base - 12, P.FR_ICE)                                  # the hall
    c.rect(x - 30, base - 30, x + 30, base - 29, P.FR_ICE_L)
    for dx, h, w, roof in towers:
        tx, top = x + dx, base - 12 - h
        c.rect(tx - w / 2, top, tx + w / 2, base - 12, P.FR_ICE)
        c.rect(tx - w / 2, top, tx - w / 2 + 1, base - 12, P.FR_ICE_L)                        # lit side
        c.rect(tx + w / 2 - 1, top, tx + w / 2, base - 12, P.FR_ICE_D)
        c.poly([(tx - w / 2 - 1, top), (tx, top - roof), (tx + w / 2 + 1, top)], P.FR_ICE_L)  # spire
        c.poly([(tx, top - roof), (tx + w / 2 + 1, top), (tx + 0.5, top)], P.FR_ICE)
        c.px(tx, top - roof, P.WHITE)
        for wy in range(int(top + 4), int(base - 16), 7):                                     # windows
            c.rect(tx - 0.5, wy, tx + 0.5, wy + 2, P.FR_ICE_GLOW)
    c.ellipse(x, base - 18, 5, 6, P.FR_ICE_DD)                                                # gate
    c.ellipse(x, base - 18, 3, 4, P.FR_ICE_GLOW)
    for wx in (-22, -10, 10, 22):
        c.rect(x + wx - 1, base - 26, x + wx + 1, base - 21, P.FR_ICE_GLOW)
    c.rect(x + 36, base - 12, x + 40, base, P.FR_ICE_L)                                       # frozen falls
    c.line((x + 37, base - 12), (x + 37, base), P.WHITE)


def frost_far() -> Canvas:
    """Distant snowy peaks in two ranges, and the ice castle on its cliff."""
    h = 150
    c = Canvas(LAYER_W, h)
    W.mountains(c, h, 31, 5, (78, 112), (P.FR_MTN, P.FR_MTN_D, P.FR_MTN_DD), tips=P.SNOW)
    W.mountains(c, h, 32, 7, (44, 74), (P.FR_MTN_D, P.FR_MTN_DD, P.FR_ROCK_D), tips=P.SNOW_D)
    rnd = noise(33)
    streaks = Canvas(LAYER_W, h)                             # snow streaks down the faces, blended over them
    for _ in range(26):
        x, y = rnd() * LAYER_W, h - 40 - rnd() * 60
        for k in range(3 + int(rnd() * 4)):
            if c.img.getpixel((int(x - k * 0.6) % LAYER_W, int(y + k)))[3]:
                streaks.px(x - k * 0.6, y + k, P.SNOW)
    c.paste(see_through(streaks.img, 150))
    ice_castle(c, 196, h - 8)
    for k in range(26):                                      # a band of tiny distant pines along the foot
        px = k * LAYER_W / 26 + (k * 7) % 5
        def tree(x, k=k):
            th = 7 + (k * 5) % 6
            c.poly([(x - 3, h - 1), (x, h - 1 - th), (x + 3, h - 1)], P.FR_PINE_D)
            c.px(x, h - 1 - th, P.SNOW_D)
        W.wrapped(tree, px)
    c.rect(0, h - 3, LAYER_W - 1, h - 1, P.SNOW_D)
    return W.haze(c, P.FR_NIGHT_L, 0.22)


def snowy_pine(c: Canvas, x: float, base: float, h: float, spread: float) -> None:
    """A dark teal pine with snow lying on every tier."""
    c.rect(x - 1.5, base - 6, x + 1.5, base, P.BARK_D)
    tiers = 5
    for k in range(tiers):
        top = base - h + k * h * 0.17
        w = spread * (0.35 + k * 0.17)
        bottom = top + h * 0.26
        c.poly([(x - w, bottom), (x, top), (x + w, bottom)], P.FR_PINE)
        c.poly([(x, top), (x + w, bottom), (x + w * 0.35, bottom)], P.FR_PINE_D)
        c.poly([(x - w * 0.15, top + 1), (x, top), (x - w * 0.6, bottom - 1)], P.FR_PINE_L)
        c.poly([(x - w * 0.8, bottom - 1), (x - w * 0.3, top + h * 0.12), (x + w * 0.5, bottom - 2),   # snow
                (x + w * 0.85, bottom), (x - w, bottom)], P.SNOW)
        c.line((x - w * 0.8, bottom - 1), (x - w * 0.3, top + h * 0.12), P.SNOW_L)
    c.poly([(x - 1.5, base - h + 2), (x, base - h - 1), (x + 1.5, base - h + 2)], P.SNOW_L)


def hut(c: Canvas, x: float, base: float) -> None:
    """A small wooden hut with a snowy roof, lit windows and a lantern by the door (about 32x28)."""
    c.rect(x - 13, base - 15, x + 13, base, P.PLANK_D)
    for k, yy in enumerate(range(int(base - 15), int(base), 3)):
        c.rect(x - 13, yy, x + 13, yy + 1, P.PLANK if k % 2 else P.BARK)
    c.poly([(x - 17, base - 14), (x, base - 27), (x + 17, base - 14)], P.BARK_DD)   # roof
    c.poly([(x - 18, base - 13), (x - 15, base - 17), (x, base - 28), (x + 15, base - 17), (x + 18, base - 13),
            (x + 12, base - 15), (x, base - 25), (x - 12, base - 15)], P.SNOW_L)
    c.line((x - 15, base - 16), (x, base - 28), P.WHITE)
    for ix in (-14, -9, -3, 5, 11, 15):                                            # icicles off the eaves
        c.line((x + ix, base - 13), (x + ix, base - 11 - (ix * 3) % 3), P.FR_ICE_L)
    c.rect(x + 7, base - 31, x + 10, base - 23, P.FR_ROCK)                         # chimney with snow
    c.rect(x + 6, base - 32, x + 11, base - 31, P.SNOW_L)
    for wx in (x - 10, x + 4):
        c.rect(wx, base - 11, wx + 5, base - 6, P.BARK_DD)
        c.rect(wx + 1, base - 10, wx + 4, base - 7, P.LAMP)
        c.px(wx + 1, base - 10, P.LANTERN)
    c.rect(x - 3, base - 10, x + 1, base, P.BARK_DD)                               # door
    c.px(x + 3, base - 8, P.LAMP)                                                  # lantern
    c.rect(x - 15, base - 2, x + 15, base, P.SNOW_L)                               # snow banked against it


def snow_cliff(c: Canvas, x0: float, x1: float, top: float, base: float, seed: int) -> None:
    """A snow-capped shelf of rounded indigo boulders with icicles under its lip."""
    rnd = noise(seed)
    c.rect(x0, top, x1, base, P.FR_ROCK_DD)
    y = top + 3
    row = 0
    while y < base:
        x = x0 - (4 if row % 2 else 0)
        while x < x1:
            w = 8 + rnd() * 6
            hh = 7 + rnd() * 3
            bx0, bx1 = max(x, x0), min(x + w - 1, x1)
            if bx1 - bx0 >= 3:
                W.cobble(c, bx0, y, bx1, min(y + hh, base), ROCK_BIG if row < 2 else ROCK_SMALL)
            x += w
        y += 7
        row += 1
    c.ellipse((x0 + x1) / 2, top + 1, (x1 - x0) / 2 + 3, 4, P.SNOW_L)
    c.rect(x0 - 2, top - 1, x1 + 2, top + 3, P.SNOW_L)
    c.rect(x0 - 2, top - 2, x1 + 2, top - 1, P.WHITE)
    for ix in range(int(x0), int(x1), 5):
        icicle(c, ix + (ix * 3) % 3, top + 4, 3 + (ix * 7) % 6)


def frost_near() -> Canvas:
    """Snowy pine forest with snow-capped cliffs and, now and then, a cosy hut."""
    h = 130
    c = Canvas(LAYER_W, h)
    W.piece(c, lambda layer, px: snow_cliff(layer, px, px + 64, h - 44, h, 41), 20, outline=P.FR_ROCK_DD)
    W.piece(c, lambda layer, px: snow_cliff(layer, px, px + 40, h - 28, h, 42), 214, outline=P.FR_ROCK_DD)
    pines = [(8, 70, 22), (34, 62, 18), (106, 84, 26), (132, 58, 18), (178, 74, 22), (262, 90, 26), (292, 60, 18),
             (314, 68, 20)]
    for x, th, spread in pines:
        base = h - 44 if 20 <= x <= 84 else h - 28 if 214 <= x <= 254 else h - 2
        W.piece(c, lambda layer, px, th=th, spread=spread, base=base: snowy_pine(layer, px, base, th, spread), x,
                outline=P.FR_PINE_DD)
    W.piece(c, lambda layer, px: hut(layer, px, h - 3), 156, outline=P.FR_ROCK_DD)
    warm = Canvas(LAYER_W, h)                                # the hut's window light, blended over it
    warm.ellipse(150, h - 12, 9, 7, (P.LAMP[0], P.LAMP[1], P.LAMP[2], 40))
    c.paste(warm)
    c.rect(0, h - 4, LAYER_W - 1, h - 1, P.SNOW)                  # the snowy floor of the wood
    c.rect(0, h - 4, LAYER_W - 1, h - 4, P.SNOW_L)
    return W.haze(c, P.FR_NIGHT_L, 0.14)


def frost_bushes() -> Canvas:
    """Low snowy shrubs with a few ice crystals."""
    h = 20
    c = Canvas(LAYER_W, h)
    rnd = noise(51)
    x = 0
    while x < LAYER_W:
        w = 10 + rnd() * 14
        bh = 6 + rnd() * 6

        def shrub(layer, px, w=w, bh=bh):
            for k, dx in enumerate((-w / 4, 0, w / 4)):                   # three needle clumps
                layer.ellipse(px + dx, h - 1 - bh / 2 + abs(dx) / 4, w / 4 + 1, bh / 2, P.FR_PINE)
                layer.ellipse(px + dx - 1, h - bh / 2 + abs(dx) / 4, w / 4 - 1, bh / 2 - 2, P.FR_PINE_L)
            for dx in (-w / 4, 0, w / 4):                                 # snow lying on each clump's top
                layer.ellipse(px + dx, h - bh + 1.5 + abs(dx) / 4, w / 5, 1.6, P.SNOW)
                layer.ellipse(px + dx - 1, h - bh + 1 + abs(dx) / 4, w / 7, 1, P.SNOW_L)
        W.piece(c, shrub, x + w / 2, outline=P.FR_PINE_DD)
        if rnd() > 0.7:
            def crystal(layer, px):
                layer.poly([(px - 2, h - 1), (px, h - 9), (px + 2, h - 1)], P.FR_ICE_L)
                layer.line((px, h - 8), (px, h - 2), P.FR_ICE_GLOW)
                layer.poly([(px + 1, h - 1), (px + 4, h - 6), (px + 4, h - 1)], P.FR_ICE)
            W.piece(c, crystal, x + w + 2, outline=P.FR_ICE_DD)
        x += w + 6 + rnd() * 10
    return W.haze(c, P.FR_NIGHT_L, 0.06)


# --- ground --------------------------------------------------------------------------------------------

def frost_ground(c: Canvas) -> None:
    """Thick snow with drips and icicles over big indigo cobbles, then the smaller stones of the deep earth."""
    c.rect(0, 0, 31, 47, P.FR_ROCK_DD)
    for y0, offset, widths, seed in ((8, 0, [11, 10, 11], 103), (18, 6, [10, 12, 10], 104)):
        W.cobble_row(c, y0, 11, widths, offset, ROCK_BIG, seed, specks=SPECKS)
    W.cobble_row(c, 28, 3, [11, 10, 11], 2, ROCK_SMALL, 105)  # a thin course before the small stones
    frost_stones(c, 30, 1, 3)
    snow_cap(c, 32, 8, 7)


def frost_earth(c: Canvas) -> None:
    frost_stones(c, 0, 4, 6)                                 # continues the ground tile's rows 1, 2, 3


# --- frozen waterfall pit (the forest waterfall-pit contract) -----------------------------------------

ICE_BASE = [P.FR_ICE_L, P.FR_ICE_GLOW, P.WHITE, P.FR_ICE_L, P.FR_ICE, P.FR_ICE_L, P.FR_ICE_GLOW, P.SNOW_L,
            P.FR_ICE_L, P.FR_ICE, P.FR_ICE_D, P.FR_ICE, P.FR_ICE_L, P.FR_ICE_GLOW, P.WHITE, P.FR_ICE_L]


def ice_stream(width: int, seed: int, base: list) -> list:
    rnd = noise(seed)
    cols = []
    for x in range(width):
        light = base[x] in (P.WHITE, P.FR_ICE_GLOW, P.SNOW_L)
        start, length = int(rnd() * 16), 5 + int(rnd() * 6)
        choice = (P.FR_ICE_L, P.FR_ICE) if light else (P.WHITE, P.FR_ICE_GLOW)
        cols.append((base[x], [(start, length, choice[int(rnd() * 2)])]))
    return cols


def wall(name: str, rocks: list, snow: list, frost: list) -> Sprite:
    c = Canvas(8, 16)
    face(c, 0, 15)
    for points, ramp in rocks:
        rock(c, points, ramp)
    for x, y in snow:
        c.px(x, y, P.SNOW_L if y % 2 else P.SNOW)
    for x, y in frost:
        c.px(x, y, P.FR_ICE_L)
    return single(name, c)


def walls() -> list[Sprite]:
    a = wall("ravine_frost", [([(0, 0), (5, 0), (6, 2), (6, 6), (3, 7), (0, 6)], ROCK_BIG),
                              ([(0, 8), (4, 8), (6, 9), (6, 14), (4, 15), (0, 15)], ROCK_SMALL)],
             [(1, 0), (2, 0), (3, 0), (4, 1), (1, 8), (2, 8), (3, 8)], [(5, 4), (2, 12)])
    b = wall("ravine_frost_b", [([(0, 0), (6, 0), (6, 4), (4, 5), (0, 5)], ROCK_SMALL),
                                ([(0, 7), (3, 6), (6, 7), (6, 11), (2, 12), (0, 11)], ROCK_BIG),
                                ([(0, 13), (5, 13), (6, 14), (6, 15), (0, 15)], ROCK_SMALL)],
             [(2, 6), (3, 6), (1, 7), (4, 7), (0, 13), (1, 13), (2, 13)], [(4, 2), (3, 9)])
    return [a, b]


def ravine_rim() -> Sprite:
    """12x24 left top cap: snow over indigo rock on cols 0-7 and a snow cornice curling over the edge
    (cols 6-11) with icicles hanging from it."""
    c = Canvas(12, 24)
    face(c, 7, 23)
    rock(c, [(0, 7), (6, 7), (6, 14), (3, 15), (0, 14)], ROCK_BIG)
    rock(c, [(0, 16), (4, 16), (6, 17), (6, 23), (0, 23)], ROCK_SMALL)
    c.rect(0, 0, 8, 7, P.SNOW_L)
    c.rect(0, 0, 8, 1, P.WHITE)
    c.ellipse(8, 4, 4, 4.2, P.SNOW_L)                        # the cornice over the edge
    c.ellipse(9, 8.5, 2.6, 2, P.SNOW)
    c.ellipse(7.5, 3, 3, 2.5, P.WHITE)
    c.rect(0, 7, 6, 7, P.SNOW)
    for x, y, length in ((2, 8, 4), (5, 8, 6), (8, 10, 9), (10, 10, 13), (11, 9, 6)):
        icicle(c, x, y, length)
    c.px(3, 3, P.FR_ICE_GLOW)
    return single("ravine_frost_rim", c)


def ravine_icicles() -> Sprite:
    """6x24, the vines' slot: icicles hanging from a snow pad."""
    c = Canvas(6, 24)
    c.ellipse(2.5, 1, 2.5, 1.4, P.SNOW_L)
    c.rect(1, 0, 4, 0, P.WHITE)
    icicle(c, 1.5, 2, 21)
    icicle(c, 4.2, 2, 12)
    return single("ravine_frost_vines", c)


def ravine_back() -> Sprite:
    """16x16 far wall of the pit: dark ice-glazed rock blocks."""
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 15, P.FR_NIGHT_TOP)
    W.cobble_row(c, 0, 9, [16], 0, (P.FR_ROCK, P.FR_ROCK_D, P.FR_ROCK_DD), 141, specks=(P.FR_ICE_DD,), tile_w=16)
    W.cobble_row(c, 8, 9, [16], 8, (P.FR_ROCK, P.FR_ROCK_D, P.FR_ROCK_DD), 142, specks=(P.FR_ICE_DD,), tile_w=16)
    for x, y in ((5, 2), (6, 3), (12, 10), (13, 11), (2, 12)):
        c.px(x, y, P.FR_ICE_D)                               # ice glaze
    return single("ravine_frost_back", c)


def ravine_falls() -> list[Sprite]:
    cols = ice_stream(16, 177, ICE_BASE)
    falls = Sprite("ravine_frost_falls", (16, 16))
    frames = []
    for k in range(4):
        c = Canvas(16, 16)
        for x in range(16):
            for y in range(16):
                c.px(x, y, colour_at(cols[x], (y - 4 * k) % 16))
        frames.append(c)
    falls.add("flow", frames, fps=10)

    edge_cols = ice_stream(4, 178, [P.FR_ROCK_D, P.FR_ICE, P.FR_ICE_L, P.FR_ICE_GLOW])
    gaps = {0: [(0, 6), (9, 5)], 1: [(4, 3), (12, 2)], 2: [(8, 2)], 3: []}
    edge = Sprite("ravine_frost_falls_edge", (4, 16))
    frames = []
    for k in range(4):
        c = Canvas(4, 16)
        for x in range(4):
            for y in range(16):
                v = (y - 4 * k) % 16
                col = colour_at(edge_cols[x], v)
                if any((v - s) % 16 < n for s, n in gaps[x]):
                    col = P.FR_ROCK_DD if x == 0 else P.FR_ROCK_D
                c.px(x, y, col)
        frames.append(c)
    edge.add("flow", frames, fps=10)
    return [falls, edge]


def ravine_lip() -> Sprite:
    """16x6 brink: a snow ridge (row 0 = ground surface) over glowing ice, with little icicles hanging into
    the falling water and a glint sliding along."""
    sprite = Sprite("ravine_frost_lip", (16, 6))
    frames = []
    for k in range(4):
        c = Canvas(16, 6)
        for x in range(16):
            swell = round(0.6 + 0.6 * math.sin(2 * math.pi * x / 8))
            c.px(x, 1 - swell, P.SNOW_L)
            c.rect(x, 2 - swell, x, 2, P.WHITE)
            c.px(x, 3, P.FR_ICE_GLOW if (x + 4 * k) % 5 else P.WHITE)
        for x, length in ((2, 2), (6, 1), (9, 2), (13, 1)):
            c.line((x, 4), (x, 3 + length), P.FR_ICE_GLOW)
        frames.append(c)
    sprite.add("flow", frames, fps=10)
    return sprite


def ravine_surface() -> Sprite:
    """16x8 icy pool surface, `wave` 4: a pale crest over bright ice-blue water with floating ice chunks
    drifting along (4 px a frame, one tile per loop)."""
    sprite = Sprite("ravine_frost_surface", (16, 8))
    frames = []
    for k in range(4):
        c = Canvas(16, 8)
        for x in range(16):
            crest = 2 + round(math.sin((x / 16 + k / 4) * 2 * math.pi) * 0.6)
            c.px(x, crest, P.FR_ICE_GLOW)
            for y in range(crest + 1, 8):
                c.px(x, y, P.FR_ICE_L if y < 4 else P.FR_ICE if y < 7 else P.FR_ICE_D)
        for x0, w, y in ((1, 5, 1), (10, 3, 2)):             # floes riding the surface
            for d in range(w):
                xx = (x0 + d + 4 * k) % 16
                c.px(xx, y, P.WHITE)
                c.px(xx, y + 1, P.SNOW_L if 0 < d < w - 1 else P.SNOW)
            c.px((x0 + w + 4 * k) % 16, y + 1, P.SNOW_D)
        frames.append(c)
    sprite.add("wave", frames, fps=8)
    return sprite


def ravine_pool() -> Sprite:
    """16x24 icy plunge pool, `churn` 4: bubbles and drifting ice near the top, darkening to the deep row."""
    bands = [(0, 4, P.FR_ICE, P.FR_ICE), (4, 7, P.FR_ICE, P.FR_ICE_D), (7, 13, P.FR_ICE_D, P.FR_ICE_D),
             (13, 16, P.FR_ICE_D, P.FR_ICE_DD), (16, 24, P.FR_ICE_DD, P.FR_ICE_DD)]
    rnd = noise(155)
    bubbles = [(int(rnd() * 16), int(rnd() * 16), 1 + int(rnd() * 2)) for _ in range(8)]
    sprite = Sprite("ravine_frost_pool", (16, 24))
    frames = []
    for k in range(4):
        c = Canvas(16, 24)
        for y0, y1, a, b in bands:
            for y in range(y0, y1):
                for x in range(16):
                    c.px(x, y, b if (x + y) % 2 else a)
        for bx, by, size in bubbles:
            y = (by - 2 * k * size) % 16
            if y < 14:
                c.px(bx, y, P.WHITE if y < 4 else P.FR_ICE_GLOW if y < 9 else P.FR_ICE_L)
        for x0, y, n in ((3, 2, 4), (11, 6, 3)):
            for d in range(n):
                c.px((x0 + d + k) % 16, y, P.FR_ICE_L)
        frames.append(c)
    sprite.add("churn", frames, fps=8)
    return sprite


def ravine_splash() -> Sprite:
    """16x12 icy foam band, `splash` 4: churning white foam with sharp ice shards and spray above it."""
    sprite = Sprite("ravine_frost_splash", (16, 12))
    frames = []
    for k in range(4):
        c = Canvas(16, 12)
        c.rect(0, 8, 15, 11, P.WHITE)
        for x in range(16):
            if (x + k) % 3 == 0:
                c.px(x, 11, P.FR_ICE_GLOW)
            if (x * 5 + k) % 7 == 0:
                c.px(x, 10, P.SNOW_L)
        mounds = [((1 + k) % 16, 4.6 - (k % 2), 3.2), ((8 + 2 * k) % 16, 3.6 + (k % 2), 3.6), ((13 - k) % 16, 5.2, 2.6)]
        for mx, my, rad in mounds:
            for shift in (-16, 0, 16):
                c.ellipse(mx + shift + 0.6, my + 1.2, rad, rad * 0.8, P.FR_ICE_GLOW)
                c.ellipse(mx + shift, my + 0.6, rad - 0.4, rad * 0.75, P.WHITE)
        for sx, sh in (((4 + 3 * k) % 16, 5 + k % 2), ((11 + k) % 16, 4 + (k + 1) % 3)):   # ice shards
            for shift in (-16, 0, 16):
                c.poly([(sx + shift - 1, 7), (sx + shift, 7 - sh), (sx + shift + 1, 7)], P.FR_ICE_GLOW)
                c.px(sx + shift, 7 - sh + 1, P.WHITE)
        rnd = noise(190 + k)
        for _ in range(6):
            x, y = int(rnd() * 16), int(rnd() * 2)
            c.px(x, y, P.WHITE if rnd() > 0.4 else P.FR_ICE_GLOW)
        frames.append(c)
    sprite.add("splash", frames, fps=10)
    return sprite


def ravine_floor() -> Sprite:
    """16x16 pit bottom: the pool's deep colour with dark rock tops rising into it, then the earth's small
    indigo cobbles, with a ragged clear bottom so it sits on the earth below."""
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 4, P.FR_ICE_DD)
    c.rect(0, 5, 15, 11, P.FR_ROCK_DD)
    for x0, x1, y0 in ((0, 6, 2), (7, 15, 3)):
        W.cobble(c, x0, y0, x1, 10, ROCK_BIG)
        c.px(x0 + 2, y0, P.FR_ICE_L)                         # ice glint on the wet stone
        c.px(x0 + 3, y0, P.FR_ICE_GLOW)
    for x0, x1, y1 in ((0, 4, 14), (5, 10, 15), (11, 15, 13)):
        W.cobble(c, x0, 9, x1, y1, ROCK_SMALL)
    c.px(7, 12, P.SNOW_DD)
    return single("ravine_frost_floor", c)


def ravine_fallbacks() -> list[Sprite]:
    """`ravine_frost_fill` and `_deep`: still required for every ravine level and by the plain-pit path."""
    fill = Canvas(8, 48)
    for y0, y1, col in ((0, 39, P.FR_ROCK_D), (40, 40, P.FR_ICE_GLOW), (41, 43, P.FR_ICE_L), (44, 46, P.FR_ICE),
                        (47, 47, P.FR_ICE_D)):
        fill.rect(0, y0, 7, y1, col)
    deep = Canvas(16, 16)
    deep.rect(0, 0, 15, 15, P.FR_ICE_DD)
    for x0, y, n in ((2, 3, 4), (10, 9, 3), (5, 13, 4)):
        deep.rect(x0, y, x0 + n - 1, y, P.FR_ICE_D)
    return [single("ravine_frost_fill", fill), single("ravine_frost_deep", deep)]


# --- terrain blocks (the forest terrain contract) ------------------------------------------------------

def outline_left(c: Canvas, rows, colour=P.FR_ROCK_DD) -> None:
    for y in rows:
        for x in range(c.size[0]):
            if c.img.getpixel((x, y))[3]:
                c.px(x - 1, y, colour)
                break


def stone_end(c: Canvas, y0: int, y1: int) -> None:
    c.rect(4, y0, 7, y1, P.FR_ROCK_DD)
    W.cobble(c, 2, y0, 7, y1, ROCK_BIG)


def terrain_top() -> Sprite:
    """16x16: snow cap (row 0 = walk surface) with drips and icicles over one row of big indigo cobbles, which
    starts on a joint at x 0 and ends on a stone rim at row 15."""
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 15, P.FR_ROCK_DD)
    W.cobble_row(c, 7, 10, [7, 9], 0, ROCK_BIG, 205, specks=SPECKS, tile_w=16)
    snow_cap(c, 16, 6, 3)
    return single("terrain_frost_top", c)


def terrain_edge() -> Sprite:
    """8x16 left end cap: a rounded snow corner overhanging by one pixel, icicles over the side."""
    c = Canvas(8, 16)
    stone_end(c, 7, 15)
    outline_left(c, range(7, 16))
    starts = [3, 1, 0, 0, 0, 0, 1]
    for y, x0 in enumerate(starts):
        c.rect(x0, y, 7, y, P.WHITE if y < 2 else P.SNOW_L if y < 5 else P.SNOW)
    c.px(0, 4, P.SNOW)
    c.px(0, 5, P.SNOW_D)
    c.px(1, 6, P.SNOW_D)
    c.px(4, 1, P.FR_ICE_GLOW)
    c.ellipse(5, 7, 2, 1.2, P.SNOW)                          # a drip
    icicle(c, 1, 7, 5)
    icicle(c, 5, 8, 3)
    return single("terrain_frost_edge", c)


def terrain_wall() -> Sprite:
    """8x16 left side face: two outlined 8-row stone ends with snow on their tops and an icicle."""
    c = Canvas(8, 16)
    stone_end(c, 0, 7)
    stone_end(c, 8, 15)
    outline_left(c, range(16))
    for x, y in ((3, 0), (4, 0), (5, 0), (3, 8), (4, 8)):
        c.px(x, y, P.SNOW_L)
    c.px(2, 1, P.SNOW)
    icicle(c, 1, 9, 4)
    c.px(5, 4, P.FR_ICE_L)
    return single("terrain_frost_wall", c)


def terrain_fill() -> Sprite:
    """16x16 interior: two rows of 8-row indigo cobbles, light top at row 0, dark rim at row 15."""
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 15, P.FR_ROCK_DD)
    W.cobble_row(c, 0, 9, [9, 7], 2, ROCK_BIG, 206, specks=SPECKS, tile_w=16)
    W.cobble_row(c, 8, 9, [7, 9], 7, ROCK_BIG, 207, specks=SPECKS, tile_w=16)
    return single("terrain_frost_fill", c)


def build() -> list[Sprite]:
    return [
        *smooth_sky("frost", [P.FR_NIGHT_TOP, P.FR_NIGHT, P.FR_NIGHT_L, P.FR_NIGHT_HAZE]),
        single("bg_frost_puffs", night_puffs()),
        single("bg_frost_clouds", night_clouds()),
        single("bg_frost_far", frost_far()),
        single("bg_frost_near", frost_near()),
        single("bg_frost_bushes", frost_bushes()),
        *ground("frost", frost_ground, frost_earth),
        flat("ground_frost_fill", P.FR_ROCK_DD),
        *walls(), ravine_rim(), ravine_icicles(), ravine_back(), *ravine_falls(), ravine_lip(), ravine_surface(),
        ravine_pool(), ravine_splash(), ravine_floor(), *ravine_fallbacks(),
        terrain_top(), terrain_edge(), terrain_wall(), terrain_fill(),
    ]
