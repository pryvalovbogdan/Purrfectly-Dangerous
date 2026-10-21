"""World 4's environment, the Cataclysm Citadel, after docs/concept/Cataclysm Citadel Tileset Showcase.png (reference
only): a molten volcanic fortress under a crimson sky with a black eclipse. Charcoal and purple-black stone, glowing
lava, red cat-crest banners and iron chains. Same names, sizes and tiling contracts as the forest's
(docs/sprite-spec.md); props and enemies are in characters/citadel.py."""
from __future__ import annotations

import math

import palette as P
from characters.scenery import LAYER_W, STONE_ROWS, flat, ground, smooth_sky
from characters.waterfall import colour_at, face, rock
from draw import Canvas, noise, see_through
from sprite import Sprite, single
import woodland as W

STONE_BIG = (P.CC_STONE_L, P.CC_STONE, P.CC_STONE_D)
STONE_SMALL = (P.CC_STONE, P.CC_STONE_D, P.CC_STONE_DD)
SPECKS = (P.CC_STONE_DD, P.CC_LAVA_DD, P.CC_STONE_D)


def rgba(col, a: int):
    return (col[0], col[1], col[2], a)


def glow(c: Canvas, x: float, y: float, rx: float, ry: float, col, a: int) -> None:
    """A see-through ellipse blended over what is drawn (ImageDraw alone would punch a hole)."""
    layer = Canvas(*c.size)
    layer.ellipse(x, y, rx, ry, rgba(col, a))
    c.paste(layer)


def smoke_band(c: Canvas, y: float, depth: float, seed: int, cols, alpha: int) -> None:
    """Rolling smoke: overlapping puffs along a band, wrapped across the strip, laid over at `alpha`."""
    rnd = noise(seed)
    band = Canvas(*c.size)
    x = 0
    while x < c.size[0]:
        r = 7 + rnd() * 10
        yy = y + rnd() * depth
        light, body = cols

        def puff(px, r=r, yy=yy):
            band.ellipse(px, yy + 1, r, r * 0.5, body)
            band.ellipse(px - 2, yy - 1, r * 0.7, r * 0.32, light)
        W.wrapped(puff, x, c.size[0])
        x += r * 1.3
    c.paste(see_through(band.img, alpha))


def embers(c: Canvas, seed: int, count: int, y0: float, y1: float) -> None:
    rnd = noise(seed)
    for _ in range(count):
        c.px(rnd() * c.size[0], y0 + rnd() * (y1 - y0), P.CC_EMBER if rnd() > 0.4 else P.LAVA_L)


def lava_drip(c: Canvas, x: float, top: float, length: float) -> None:
    """A drop of lava hanging from a ledge: hot core, darker rim, a bead at the tip."""
    c.poly([(x - 1.5, top), (x + 1.5, top), (x + 0.5, top + length), (x - 0.5, top + length)], P.LAVA)
    c.line((x, top), (x, top + length - 1), P.LAVA_L)
    c.ellipse(x, top + length, 1, 1.2, P.LAVA)
    c.px(x, top + length + 1, P.CC_LAVA_D)


def crack(c: Canvas, x: float, y: float, steps: list, hot: bool = True) -> None:
    """A glowing crack: a zigzag of lava pixels (dull red embers when not `hot`)."""
    for dx, dy in steps:
        x, y = x + dx, y + dy
        c.px(x, y, P.LAVA if hot else P.CC_LAVA_DD)
    c.px(x, y, P.LAVA_L if hot else P.CC_LAVA_D)


# --- parallax ------------------------------------------------------------------------------------------

def eclipse(c: Canvas, x: float, y: float, rad: float) -> None:
    for r, a in ((rad + 16, 26), (rad + 9, 50), (rad + 4, 90)):        # the red corona, blended
        glow(c, x, y, r, r, P.CC_CORONA, a)
    c.ellipse(x, y, rad + 1.5, rad + 1.5, P.CC_CORONA_L)
    c.ellipse(x, y, rad + 0.5, rad + 0.5, P.CC_CORONA)
    c.ellipse(x + 1, y + 1, rad, rad, P.CC_ECLIPSE)
    for a in range(0, 360, 40):                                          # flares
        ang = math.radians(a + 10)
        c.px(x + math.cos(ang) * (rad + 3), y + math.sin(ang) * (rad + 3), P.CC_CORONA_L)


def citadel_clouds() -> Canvas:
    """The 150-tall layer on the ground line: the eclipse, smoke banks and drifting embers."""
    c = Canvas(LAYER_W, 150)
    smoke_band(c, 14, 10, 601, (P.CC_SMOKE, P.CC_SMOKE_D), 150)
    eclipse(c, 236, 40, 22)
    smoke_band(c, 70, 14, 602, (P.CC_SMOKE_L, P.CC_SMOKE), 130)
    smoke_band(c, 100, 10, 603, (P.CC_SMOKE, P.CC_SMOKE_D), 150)
    embers(c, 604, 30, 0, 140)
    return c


def citadel_puffs() -> Canvas:
    c = Canvas(LAYER_W, 120)
    smoke_band(c, 20, 30, 605, (P.CC_SMOKE, P.CC_SMOKE_D), 140)
    smoke_band(c, 70, 20, 606, (P.CC_SMOKE_D, P.CC_SKY_TOP), 160)
    embers(c, 607, 20, 0, 118)
    return c


def spiky_tower(c: Canvas, x: float, base: float, w: float, h: float, col, window=None) -> None:
    c.rect(x - w / 2, base - h, x + w / 2, base, col)
    c.poly([(x - w / 2 - 1, base - h), (x, base - h - w * 1.6), (x + w / 2 + 1, base - h)], col)
    for k in (-1, 1):                                                    # turret spikes
        c.poly([(x + k * w / 2 - 1, base - h + 3), (x + k * (w / 2 + 2), base - h - 4), (x + k * w / 2 + 1, base - h + 3)],
               col)
    if window:
        for wy in range(int(base - h + 5), int(base - 6), 10):
            c.rect(x - 0.5, wy, x + 0.5, wy + 2, window)


def cat_crest(c: Canvas, x: float, y: float, s: float, col) -> None:
    """A cat head outline glowing on the citadel's keep."""
    c.ellipse(x, y, 5 * s, 4 * s, col)
    c.poly([(x - 5 * s, y - 1), (x - 4 * s, y - 7 * s), (x - 1 * s, y - 3 * s)], col)
    c.poly([(x + 5 * s, y - 1), (x + 4 * s, y - 7 * s), (x + 1 * s, y - 3 * s)], col)
    c.ellipse(x, y + 0.5, 3.5 * s, 2.6 * s, P.CC_SIL)
    c.px(x - 2 * s, y, col)
    c.px(x + 2 * s, y, col)


def citadel_far() -> Canvas:
    """Jagged volcanic mountains glowing at their feet, and the spiky citadel with lit windows and a cat crest."""
    h = 150
    c = Canvas(LAYER_W, h)
    W.mountains(c, h, 611, 6, (70, 116), (P.CC_MTN_L, P.CC_MTN, P.CC_MTN_D))
    W.mountains(c, h, 612, 8, (40, 72), (P.CC_MTN, P.CC_MTN_D, P.CC_SIL_L))
    for x in (40, 290):                                                   # lava running down a slope
        c.line((x, h - 60), (x - 6, h - 1), P.LAVA)
        c.line((x + 1, h - 58), (x - 5, h - 1), P.CC_LAVA_D)
    rnd = noise(613)
    for k in range(16):                                                  # the citadel's outer spires
        x = 110 + k * 10 + rnd() * 4
        spiky_tower(c, x, h, 5 + rnd() * 3, 30 + rnd() * 40, P.CC_SIL_L, P.CC_LAVA_D if k % 3 == 0 else None)
    cx = 168
    c.rect(cx - 30, h - 70, cx + 30, h, P.CC_SIL)                        # the keep
    for dx, sh, sw in ((-24, 84, 8), (0, 104, 12), (24, 84, 8), (-12, 92, 6), (12, 92, 6)):
        spiky_tower(c, cx + dx, h, sw, sh, P.CC_SIL, P.LAVA if dx == 0 else P.CC_LAVA_D)
    cat_crest(c, cx, h - 58, 1.4, P.CC_LAVA_D)
    c.ellipse(cx, h - 14, 6, 10, P.CC_LAVA_D)                            # the gate, lit
    c.ellipse(cx, h - 13, 4, 8, P.LAVA)
    for wx in (-20, -8, 8, 20):
        c.rect(cx + wx - 1, h - 40, cx + wx + 1, h - 34, P.LAVA)
    glow(c, cx, h - 4, 70, 12, P.CC_SKY_HAZE, 60)                        # the lava sea's light at its foot
    return W.haze(c, P.CC_SKY_L, 0.2)


def bridge_span(c: Canvas, x0: float, x1: float, deck: float, base: float) -> None:
    """A stone bridge between two towers: a parapet, a deck and round arches below."""
    c.rect(x0, deck, x1, deck + 6, P.CC_STONE_D)
    c.rect(x0, deck, x1, deck, P.CC_STONE)
    for x in range(int(x0), int(x1), 4):                                 # parapet
        c.rect(x, deck - 3, x + 1, deck - 1, P.CC_STONE_D)
    c.rect(x0, deck - 1, x1, deck - 1, P.CC_STONE_D)
    span = x1 - x0
    n = max(1, round(span / 22))
    for k in range(n):                                                   # piers and arches
        ax0, ax1 = x0 + k * span / n, x0 + (k + 1) * span / n
        c.rect(ax0, deck + 6, ax0 + 3, base, P.CC_STONE_D)
        c.rect(ax0, deck + 6, ax0 + 1, base, P.CC_STONE)
        mid, rx = (ax0 + ax1) / 2 + 1.5, (ax1 - ax0) / 2 - 1.5
        c.rect(ax0 + 4, deck + 6, ax1 - 1, deck + 20, P.CC_STONE_D)                             # spandrel
        c.ellipse(mid, deck + 20, rx + 1, 10, P.CC_STONE)                                        # arch ring
        c.ellipse(mid, deck + 20, rx - 1, 8.5, (0, 0, 0, 0))                                     # the arch (a hole:
        c.rect(ax0 + 4, deck + 20, ax1 - 1, base, (0, 0, 0, 0))                                  # own layer)


def tower(c: Canvas, x: float, top: float, base: float, w: float, banner: bool) -> None:
    c.rect(x - w / 2, top, x + w / 2, base, P.CC_STONE_D)
    c.rect(x - w / 2, top, x - w / 2 + 1, base, P.CC_STONE)
    c.rect(x + w / 2 - 1, top, x + w / 2, base, P.CC_STONE_DD)
    for y in range(int(top + 6), int(base), 7):
        c.line((x - w / 2, y), (x + w / 2, y), P.CC_STONE_DD)
    for k in range(-1, 2):                                               # battlements
        c.rect(x + k * w / 3 - 1.5, top - 3, x + k * w / 3 + 1.5, top, P.CC_STONE_D)
    c.rect(x - 1, top + 8, x + 1, top + 13, P.LAVA)                      # a lit slit window
    c.rect(x - 4, top - 6, x + 4, top - 4, P.CC_STONE)                   # brazier bowl on top
    c.poly([(x - 3, top - 6), (x, top - 13), (x + 3, top - 6)], P.LAVA)
    c.poly([(x - 1.5, top - 6), (x, top - 10), (x + 1.5, top - 6)], P.LAVA_L)
    glow(c, x, top - 8, 7, 6, P.CC_EMBER, 50)
    if banner:
        bx0, bx1 = x - 4, x + 4
        c.poly([(bx0, top + 16), (bx1, top + 16), (bx1, top + 34), (x, top + 30), (bx0, top + 34)], P.CC_BANNER)
        c.line((bx0, top + 16), (bx1, top + 16), P.GOLD_D)
        c.ellipse(x, top + 23, 2, 1.8, P.GOLD)                            # the cat crest
        c.px(x - 2, top + 21, P.GOLD)
        c.px(x + 2, top + 21, P.GOLD)


def lavafall(c: Canvas, x: float, top: float, base: float, w: float) -> None:
    glow(c, x + w / 2, (top + base) / 2, w + 5, (base - top) / 2 + 4, P.CC_EMBER, 40)
    c.rect(x, top, x + w, base, P.LAVA)
    c.rect(x + 1, top, x + w - 2, base, P.LAVA_L)
    for k in range(int(top), int(base), 3):
        c.px(x + 1 + (k * 7) % max(1, int(w - 2)), k, P.CC_LAVA_W)
    c.rect(x - 1, top, x + w + 1, top + 1, P.LAVA)
    c.ellipse(x + w / 2, base, w, 3, P.LAVA_L)


def citadel_near() -> Canvas:
    """Arched stone bridges between towers, lavafalls pouring under them, braziers, banners and chains."""
    h = 150
    c = Canvas(LAYER_W, h)
    towers = [(20, 54, 16, True), (130, 40, 18, False), (214, 62, 14, True), (300, 48, 16, False)]
    falls = [(64, 82, 8), (170, 76, 10), (252, 90, 7)]
    for x, top, w in falls:
        W.wrapped(lambda px, top=top, w=w: lavafall(c, px, top, h, w), x)
    stone = Canvas(LAYER_W, h)                                           # bridges and towers on their own layer,
    for (xa, ta, wa, _), (xb, tb, wb, _) in zip(towers, towers[1:] + [(towers[0][0] + LAYER_W,) + towers[0][1:]]):
        deck = max(ta, tb) + 22                                          # so the arches open onto the lavafalls
        W.wrapped(lambda px, span=xb - xa - wa / 2 - wb / 2, deck=deck: bridge_span(stone, px, px + span, deck, h),
                  xa + wa / 2)
    for x, top, w, banner in towers:
        W.wrapped(lambda px, top=top, w=w, banner=banner: tower(stone, px, top, h, w, banner), x)
    c.paste(stone)
    for x, top, length in ((96, 50, 30), (182, 56, 22), (268, 44, 34)):  # chains hanging between towers
        def chain(px, top=top, length=length):
            for y in range(int(top), int(top + length), 2):
                c.rect(px, y, px + 1, y, P.IRON if (y // 2) % 2 else P.IRON_D)
            c.poly([(px - 2, top + length), (px + 3, top + length), (px + 0.5, top + length + 5)], P.IRON_D)
        W.wrapped(chain, x)
    embers(c, 621, 24, 20, 140)
    return W.haze(c, P.CC_SKY, 0.16)


def citadel_bushes() -> Canvas:
    """The front strip: low rock silhouettes and iron spikes, glowing with embers from below."""
    h = 22
    c = Canvas(LAYER_W, h)
    glow_layer = Canvas(LAYER_W, h)
    glow_layer.rect(0, h - 6, LAYER_W - 1, h - 1, rgba(P.CC_EMBER, 60))
    c.paste(glow_layer)
    rnd = noise(631)
    x = 0
    while x < LAYER_W:
        w = 10 + rnd() * 18
        rh = 5 + rnd() * 9

        def rocks(px, w=w, rh=rh):
            c.poly([(px - w / 2, h - 1), (px - w / 3, h - rh), (px, h - rh - 2), (px + w / 3, h - rh + 1),
                    (px + w / 2, h - 1)], P.CC_SIL)
            c.line((px - w / 3, h - rh), (px, h - rh - 2), P.CC_SIL_L)
            c.px(px - 2, h - 3, P.LAVA)
        W.wrapped(rocks, x + w / 2)
        if rnd() > 0.55:
            def spikes(px):
                c.rect(px - 6, h - 4, px + 6, h - 1, P.CC_SIL)
                for k in range(-5, 6, 3):
                    c.poly([(px + k - 1, h - 4), (px + k, h - 12), (px + k + 1, h - 4)], P.IRON_D)
                    c.px(px + k, h - 11, P.CC_LAVA_D)
            W.wrapped(spikes, x + w + 6)
        x += w + 10 + rnd() * 12
    embers(c, 632, 14, 0, h - 4)
    return c


# --- ground --------------------------------------------------------------------------------------------

def small_stones(c: Canvas, y0: int, first: int, rows: int) -> None:
    """Rows of small charcoal cobbles 6 high, the forest's pattern, with a glowing crack here and there."""
    c.rect(0, y0, 31, y0 + rows * 6 - 1, P.CC_STONE_DD)
    for k in range(rows):
        offset, widths = STONE_ROWS[(first + k) % 6]
        W.cobble_row(c, y0 + k * 6, 7, widths, offset, STONE_SMALL, 640 + (first + k) % 6, specks=SPECKS)


def citadel_ground(c: Canvas) -> None:
    """Dark cobbled stone: a lit cap course, lava dripping from its edge, glowing cracks, then small stones that
    run on into the earth tile."""
    c.rect(0, 0, 31, 47, P.CC_STONE_DD)
    W.cobble_row(c, 0, 10, [11, 10, 11], 0, STONE_BIG, 651)              # the cap course
    c.rect(0, 0, 31, 0, P.CC_STONE_TOP)
    W.cobble_row(c, 9, 11, [10, 12, 10], 5, STONE_SMALL, 652, specks=SPECKS)
    W.cobble_row(c, 19, 11, [11, 10, 11], 1, STONE_SMALL, 653, specks=SPECKS)
    small_stones(c, 30, 1, 3)
    c.rect(0, 8, 31, 8, P.CC_LAVA_DD)                                     # the seam under the cap, glowing
    for x in (3, 12, 21, 28):
        c.px(x, 8, P.LAVA)
    for x, length in ((5, 5), (17, 3), (26, 7)):                         # lava dripping from the cap edge
        lava_drip(c, x, 8, length)
    crack(c, 9, 22, [(0, 0), (1, 1), (0, 1), (1, 1), (-1, 1)], hot=False)
    crack(c, 24, 36, [(0, 0), (1, 0), (1, 1), (0, 1)], hot=False)


def citadel_earth(c: Canvas) -> None:
    small_stones(c, 0, 4, 6)
    crack(c, 14, 10, [(0, 0), (1, 1), (0, 1), (-1, 1)], hot=False)


# --- lava pit (the forest waterfall-pit contract) ------------------------------------------------------

def walls() -> list[Sprite]:
    out = []
    for name, rocks, cracks in (
            ("ravine_citadel", [([(0, 0), (5, 0), (6, 2), (6, 6), (3, 7), (0, 6)], STONE_BIG),
                                ([(0, 8), (4, 8), (6, 9), (6, 14), (4, 15), (0, 15)], STONE_SMALL)], [(2, 9)]),
            ("ravine_citadel_b", [([(0, 0), (6, 0), (6, 4), (4, 5), (0, 5)], STONE_SMALL),
                                  ([(0, 7), (3, 6), (6, 7), (6, 11), (2, 12), (0, 11)], STONE_BIG),
                                  ([(0, 13), (5, 13), (6, 14), (6, 15), (0, 15)], STONE_SMALL)], [(3, 1)])):
        c = Canvas(8, 16)
        face(c, 0, 15)
        for points, ramp in rocks:
            rock(c, points, ramp)
        for x, y in cracks:
            crack(c, x, y, [(0, 0), (1, 1), (0, 1)])
        c.px(6, 5, P.CC_LAVA_DD)                                         # lava light on the pit side
        c.px(6, 12, P.CC_LAVA_DD)
        out.append(single(name, c))
    return out


def pit_rim() -> Sprite:
    """12x24 left top cap: the ground's cap course (row 0 = ground surface) over rock, and a molten ledge jutting
    over the pit with lava dripping from it."""
    c = Canvas(12, 24)
    face(c, 9, 23)
    rock(c, [(0, 9), (6, 9), (6, 15), (3, 16), (0, 15)], STONE_BIG)
    rock(c, [(0, 17), (4, 17), (6, 18), (6, 23), (0, 23)], STONE_SMALL)
    W.cobble(c, -4, 0, 9, 8, STONE_BIG)
    c.rect(0, 0, 9, 0, P.CC_STONE_TOP)
    c.poly([(8, 1), (11, 2), (11, 5), (9, 8), (7, 8)], P.CC_STONE_D)      # the jutting ledge
    c.line((8, 1), (11, 2), P.CC_STONE_L)
    c.rect(0, 8, 9, 8, P.CC_LAVA_DD)
    c.px(4, 8, P.LAVA)
    for x, top, length in ((3, 8, 4), (8, 8, 7), (10, 5, 11)):
        lava_drip(c, x, top, length)
    return single("ravine_citadel_rim", c)


def pit_chain() -> Sprite:
    """6x24, the vines' slot: a heavy iron chain ending in a spiked weight."""
    c = Canvas(6, 24)
    for y in range(0, 17, 3):
        if (y // 3) % 2:
            c.rect(2, y, 3, y + 2, P.IRON)
            c.px(2, y, P.IRON_L)
        else:
            c.rect(1, y, 4, y + 2, P.IRON_D)
            c.rect(2, y + 1, 3, y + 1, P.CC_STONE_DD)
            c.px(1, y, P.IRON)
    c.ellipse(2.5, 20, 2.5, 2.5, P.IRON_D)
    c.px(1.5, 19, P.IRON)
    for x, y in ((0, 20), (5, 20), (2.5, 23)):
        c.px(x, y, P.IRON_L)
    return single("ravine_citadel_vines", c)


def pit_back() -> Sprite:
    """16x16 far wall of the pit: dark blocks lit red from the lava below."""
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 15, P.CC_SIL)
    W.cobble_row(c, 0, 9, [16], 0, (P.CC_LAVA_DD, P.CC_STONE_D, P.CC_SIL_L), 661, tile_w=16)
    W.cobble_row(c, 8, 9, [16], 8, (P.CC_LAVA_DD, P.CC_STONE_D, P.CC_SIL_L), 662, tile_w=16)
    c.px(6, 4, P.CC_LAVA_D)
    c.px(12, 12, P.CC_LAVA_D)
    return single("ravine_citadel_back", c)


LAVA_BASE = [P.LAVA, P.LAVA_L, P.CC_LAVA_W, P.LAVA_L, P.LAVA, P.CC_LAVA_D, P.LAVA, P.LAVA_L, P.LAVA, P.CC_EMBER,
             P.CC_LAVA_D, P.LAVA, P.LAVA_L, P.CC_LAVA_W, P.LAVA_L, P.LAVA]


def lava_stream(width: int, seed: int, base: list) -> list:
    rnd = noise(seed)
    cols = []
    for x in range(width):
        bright = base[x] in (P.CC_LAVA_W, P.LAVA_L)
        start, length = int(rnd() * 16), 5 + int(rnd() * 6)
        mark = (P.LAVA, P.CC_EMBER) if bright else (P.LAVA_L, P.CC_LAVA_W)
        cols.append((base[x], [(start, length, mark[int(rnd() * 2)])]))
    return cols


def pit_falls() -> list[Sprite]:
    """The lavafall curtain (16x16, `flow` 4, tiles both ways, streaks down 4 px a frame) and its opaque 4x16 edge,
    whose gaps are dark crust."""
    cols = lava_stream(16, 671, LAVA_BASE)
    falls = Sprite("ravine_citadel_falls", (16, 16))
    frames = []
    for k in range(4):
        c = Canvas(16, 16)
        for x in range(16):
            for y in range(16):
                c.px(x, y, colour_at(cols[x], (y - 4 * k) % 16))
        frames.append(c)
    falls.add("flow", frames, fps=10)
    edge_cols = lava_stream(4, 672, [P.CC_LAVA_DD, P.CC_LAVA_D, P.LAVA, P.LAVA_L])
    gaps = {0: [(0, 6), (9, 5)], 1: [(4, 3), (12, 2)], 2: [(8, 2)], 3: []}
    edge = Sprite("ravine_citadel_falls_edge", (4, 16))
    frames = []
    for k in range(4):
        c = Canvas(4, 16)
        for x in range(4):
            for y in range(16):
                v = (y - 4 * k) % 16
                col = colour_at(edge_cols[x], v)
                if any((v - s) % 16 < n for s, n in gaps[x]):
                    col = P.CC_STONE_DD if x == 0 else P.CC_SIL_L
                c.px(x, y, col)
        frames.append(c)
    edge.add("flow", frames, fps=10)
    return [falls, edge]


def pit_lip() -> Sprite:
    """16x6: lava welling over the brink (row 0 = ground surface) between lumps of dark crust."""
    sprite = Sprite("ravine_citadel_lip", (16, 6))
    frames = []
    for k in range(4):
        c = Canvas(16, 6)
        for x in range(16):
            swell = round(0.6 + 0.6 * math.sin(2 * math.pi * x / 8))
            c.px(x, 1 - swell, P.LAVA)
            c.rect(x, 2 - swell, x, 3, P.LAVA_L)
            c.px(x, 2, P.CC_LAVA_W if (x + 4 * k) % 5 == 0 else P.LAVA_L)
            c.rect(x, 4, x, 5, P.LAVA)
        for x0 in ((3 + 4 * k) % 16, (11 + 4 * k) % 16):               # crust lumps riding the flow
            c.rect(x0, 0, (x0 + 2) % 16 if x0 + 2 < 16 else 15, 1, P.CC_STONE_D)
            c.px(x0, 0, P.CC_STONE)
        frames.append(c)
    sprite.add("flow", frames, fps=10)
    return sprite


def pit_surface() -> Sprite:
    """16x8 molten surface, `wave` 4: bright lava with dark crust plates drifting 4 px a frame and a bubble that
    swells and pops."""
    sprite = Sprite("ravine_citadel_surface", (16, 8))
    frames = []
    for k in range(4):
        c = Canvas(16, 8)
        for x in range(16):
            crest = 2 + round(math.sin((x / 16 + k / 4) * 2 * math.pi) * 0.6)
            c.px(x, crest, P.CC_LAVA_W)
            for y in range(crest + 1, 8):
                c.px(x, y, P.LAVA_L if y < 4 else P.LAVA if y < 7 else P.CC_LAVA_D)
        for x0, w, y in ((1, 5, 3), (10, 3, 5)):                       # crust plates
            for d in range(w):
                xx = (x0 + d + 4 * k) % 16
                c.px(xx, y, P.CC_STONE_D)
                if 0 < d < w - 1:
                    c.px(xx, y + 1, P.CC_LAVA_DD)
        bx, size = 7, (0, 1, 2, 0)[k]                                    # a bubble
        if size:
            c.ellipse(bx, 2 - size / 2, size, size, P.LAVA)
            c.px(bx, 2 - size, P.CC_LAVA_W)
        else:
            c.px(bx - 1, 0, P.LAVA_L)
            c.px(bx + 1, 0, P.LAVA_L)
        frames.append(c)
    sprite.add("wave", frames, fps=8)
    return sprite


def pit_pool() -> Sprite:
    """16x24 lava pool under the surface, `churn` 4: bright with glowing veins, darkening to deep red on row 23."""
    bands = [(0, 5, P.LAVA, P.LAVA), (5, 9, P.LAVA, P.CC_LAVA_D), (9, 15, P.CC_LAVA_D, P.CC_LAVA_D),
             (15, 19, P.CC_LAVA_D, P.CC_LAVA_DD), (19, 24, P.CC_LAVA_DD, P.CC_LAVA_DD)]
    rnd = noise(673)
    bubbles = [(int(rnd() * 16), int(rnd() * 16), 1 + int(rnd() * 2)) for _ in range(8)]
    sprite = Sprite("ravine_citadel_pool", (16, 24))
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
                c.px(bx, y, P.CC_LAVA_W if y < 5 else P.LAVA_L)
        for x0, y, n in ((2, 3, 5), (9, 8, 4)):                          # veins drifting along
            for d in range(n):
                c.px((x0 + d + k) % 16, y + (d % 2), P.LAVA_L)
        frames.append(c)
    sprite.add("churn", frames, fps=8)
    return sprite


def pit_splash() -> Sprite:
    """16x12 band of boiling lava where the fall lands, `splash` 4, with sparks thrown up."""
    sprite = Sprite("ravine_citadel_splash", (16, 12))
    frames = []
    for k in range(4):
        c = Canvas(16, 12)
        c.rect(0, 8, 15, 11, P.LAVA_L)
        for x in range(16):
            if (x + k) % 3 == 0:
                c.px(x, 11, P.LAVA)
        mounds = [((1 + k) % 16, 4.6 - (k % 2), 3.2), ((8 + 2 * k) % 16, 3.6 + (k % 2), 3.6), ((13 - k) % 16, 5.2, 2.6)]
        for mx, my, rad in mounds:
            for shift in (-16, 0, 16):
                c.ellipse(mx + shift + 0.6, my + 1.2, rad, rad * 0.8, P.LAVA)
                c.ellipse(mx + shift, my + 0.6, rad - 0.4, rad * 0.75, P.LAVA_L)
                c.px(mx + shift - 1, my - 0.5, P.CC_LAVA_W)
        rnd = noise(674 + k)
        for _ in range(6):
            c.px(int(rnd() * 16), int(rnd() * 3), P.CC_EMBER if rnd() > 0.4 else P.LAVA_L)
        frames.append(c)
    sprite.add("splash", frames, fps=10)
    return sprite


def pit_floor() -> Sprite:
    """16x16 dark rock bottom under the lava: deep red with charred stone tops rising into it, then the earth's
    small cobbles with a ragged clear bottom."""
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 4, P.CC_LAVA_DD)
    c.rect(0, 5, 15, 11, P.CC_STONE_DD)
    for x0, x1, y0 in ((0, 6, 2), (7, 15, 3)):
        W.cobble(c, x0, y0, x1, 10, STONE_SMALL)
        c.px(x0 + 2, y0, P.CC_LAVA_D)                                    # lit by the lava above
        c.px(x0 + 3, y0, P.LAVA)
    for x0, x1, y1 in ((0, 4, 14), (5, 10, 15), (11, 15, 13)):
        W.cobble(c, x0, 9, x1, y1, STONE_SMALL)
    return single("ravine_citadel_floor", c)


def pit_fallbacks() -> list[Sprite]:
    fill = Canvas(8, 48)
    for y0, y1, col in ((0, 39, P.CC_SIL), (40, 40, P.CC_LAVA_W), (41, 43, P.LAVA_L), (44, 46, P.LAVA), (47, 47, P.CC_LAVA_D)):
        fill.rect(0, y0, 7, y1, col)
    deep = Canvas(16, 16)
    deep.rect(0, 0, 15, 15, P.CC_LAVA_DD)
    for x0, y, n in ((2, 3, 4), (10, 9, 3), (5, 13, 4)):
        deep.rect(x0, y, x0 + n - 1, y, P.CC_LAVA_D)
    return [single("ravine_citadel_fill", fill), single("ravine_citadel_deep", deep)]


# --- terrain blocks (the forest terrain contract) ------------------------------------------------------

def outline_left(c: Canvas, rows, colour=P.CC_STONE_DD) -> None:
    for y in rows:
        for x in range(c.size[0]):
            if c.img.getpixel((x, y))[3]:
                c.px(x - 1, y, colour)
                break


def stone_end(c: Canvas, y0: int, y1: int) -> None:
    c.rect(4, y0, 7, y1, P.CC_STONE_DD)
    W.cobble(c, 2, y0, 7, y1, STONE_BIG)


def terrain_top() -> Sprite:
    """16x16: a charred cap slab (row 0 = walk surface) with lava seeping from under it, over one row of cobbles
    that starts on a joint at x 0 and ends on a stone rim at row 15."""
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 15, P.CC_STONE_DD)
    W.cobble_row(c, 7, 10, [7, 9], 0, STONE_SMALL, 681, specks=SPECKS, tile_w=16)
    for x0, x1 in ((0, 7), (8, 15)):                                     # cap slabs
        c.rect(x0, 0, x1, 5, P.CC_STONE)
        c.rect(x0, 0, x1, 0, P.CC_STONE_TOP)
        c.rect(x0, 1, x0, 4, P.CC_STONE_L)
        c.rect(x1, 1, x1, 5, P.CC_STONE_D)
        c.rect(x0, 5, x1, 5, P.CC_STONE_D)
    c.rect(0, 6, 15, 6, P.CC_LAVA_DD)
    c.px(4, 6, P.LAVA)
    c.px(11, 6, P.LAVA)
    lava_drip(c, 4, 6, 4)
    lava_drip(c, 12, 6, 6)
    return single("terrain_citadel_top", c)


def terrain_edge() -> Sprite:
    """8x16 left end cap: the cap slab overhanging by a pixel, lava running down its side."""
    c = Canvas(8, 16)
    stone_end(c, 7, 15)
    outline_left(c, range(7, 16))
    c.rect(0, 0, 7, 5, P.CC_STONE)
    c.rect(0, 0, 7, 0, P.CC_STONE_TOP)
    c.rect(0, 1, 0, 4, P.CC_STONE_L)
    c.rect(0, 5, 7, 5, P.CC_STONE_D)
    c.px(0, 0, P.CC_STONE_L)
    c.rect(1, 6, 7, 6, P.CC_LAVA_DD)
    c.px(5, 6, P.LAVA)
    lava_drip(c, 1, 5, 6)
    return single("terrain_citadel_edge", c)


def terrain_wall() -> Sprite:
    """8x16 left side face: two outlined 8-row stone ends with a glowing crack."""
    c = Canvas(8, 16)
    stone_end(c, 0, 7)
    stone_end(c, 8, 15)
    outline_left(c, range(16))
    crack(c, 4, 9, [(0, 0), (1, 1), (0, 1)])
    return single("terrain_citadel_wall", c)


def terrain_fill() -> Sprite:
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 15, P.CC_STONE_DD)
    W.cobble_row(c, 0, 9, [9, 7], 2, STONE_SMALL, 682, specks=SPECKS, tile_w=16)
    W.cobble_row(c, 8, 9, [7, 9], 7, STONE_SMALL, 683, specks=SPECKS, tile_w=16)
    return single("terrain_citadel_fill", c)


def build() -> list[Sprite]:
    return [
        *smooth_sky("citadel", [P.CC_SKY_TOP, P.CC_SKY, P.CC_SKY_L, P.CC_SKY_HAZE]),
        single("bg_citadel_puffs", citadel_puffs()),
        single("bg_citadel_clouds", citadel_clouds()),
        single("bg_citadel_far", citadel_far()),
        single("bg_citadel_near", citadel_near()),
        single("bg_citadel_bushes", citadel_bushes()),
        *ground("citadel", citadel_ground, citadel_earth),
        flat("ground_citadel_fill", P.CC_STONE_DD),
        *walls(), pit_rim(), pit_chain(), pit_back(), *pit_falls(), pit_lip(), pit_surface(), pit_pool(), pit_splash(),
        pit_floor(), *pit_fallbacks(),
        terrain_top(), terrain_edge(), terrain_wall(), terrain_fill(),
    ]
