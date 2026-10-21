"""The forest ravine as a waterfall pit, after docs/concept/Orange Cat Waterfall Tileset.png (reference only).

One wide curtain fills the pit between two rough, mossy rock walls; the game mirrors the left-hand pieces
for the right side. See docs/sprite-spec.md for the tiling contract. Every animated piece loops in 4 frames
and tiles in every frame."""
from __future__ import annotations

import math

import palette as P
from draw import Canvas, noise
from sprite import Sprite, single
import woodland as W

TURF_ROWS = [P.KIT_GREEN_L, P.KIT_GREEN_L, P.KIT_GREEN, P.KIT_GREEN, P.KIT_GREEN, P.KIT_GREEN_D, P.KIT_GREEN_D]
GREY_ROCK = (P.STONE_L, P.STONE, P.STONE_D)
BROWN_ROCK = (P.EARTH_L, P.EARTH, P.EARTH_D)
MOSSY_ROCK = (P.STONE, P.STONE_D, P.STONE_DD)
BACK = (P.CLIFF_BACK_L, P.CLIFF_BACK, P.CLIFF_BACK_D)


# --- rock ----------------------------------------------------------------------------------------------

def rock(c: Canvas, points: list, ramp: tuple, x_max: int = 6) -> None:
    """A rough rock chunk: the polygon in the body colour, its top rim lit, its bottom and right rims
    shaded. Columns past `x_max` are left for the outline."""
    light, body, dark = ramp
    mask = Canvas(*c.size)
    mask.poly(points, body)
    m = mask.img.load()
    h = c.size[1]

    def inside(x: int, y: int) -> bool:
        return 0 <= x <= x_max and 0 <= y < h and m[x, y][3] > 0

    for y in range(h):
        for x in range(x_max + 1):
            if not inside(x, y):
                continue
            col = body
            if not inside(x, y + 1) or not inside(x + 1, y):
                col = dark
            if not inside(x, y - 1):
                col = light
            c.px(x, y, col)


def moss(c: Canvas, pixels: list) -> None:
    for x, y, shade in pixels:
        c.px(x, y, (P.KIT_GREEN_DD, P.KIT_GREEN_D, P.KIT_GREEN, P.KIT_GREEN_L)[shade])


def face(c: Canvas, y0: int, y1: int) -> None:
    """Crevice colour behind the rocks, and the dark outline on the pit side (col 7)."""
    c.rect(0, y0, 6, y1, P.OUTLINE)
    c.rect(7, y0, 7, y1, P.WOOD_OUT)


def wall_a() -> Sprite:
    """8x16 left pit wall; tiles vertically, with itself and with `ravine_forest_b` in any order."""
    c = Canvas(8, 16)
    face(c, 0, 15)
    rock(c, [(0, 0), (5, 0), (6, 2), (6, 6), (3, 7), (0, 6)], BROWN_ROCK)
    rock(c, [(0, 8), (4, 8), (6, 9), (6, 14), (4, 15), (0, 15)], MOSSY_ROCK)
    moss(c, [(1, 0, 2), (2, 0, 3), (3, 0, 2), (4, 1, 1), (1, 8, 3), (2, 8, 2), (3, 8, 2), (4, 9, 1), (1, 9, 1),
             (5, 12, 1), (5, 13, 0)])
    c.px(2, 3, P.EARTH_D)                                    # a crack
    c.px(3, 4, P.EARTH_D)
    c.px(2, 11, P.ROCK_D)
    return single("ravine_forest", c)


def wall_b() -> Sprite:
    """8x16 alternative wall tile: a grey boulder, a brown slab, then a small mossy stone."""
    c = Canvas(8, 16)
    face(c, 0, 15)
    rock(c, [(0, 0), (6, 0), (6, 4), (4, 5), (0, 5)], GREY_ROCK)
    rock(c, [(0, 7), (3, 6), (6, 7), (6, 11), (2, 12), (0, 11)], BROWN_ROCK)
    rock(c, [(0, 13), (5, 13), (6, 14), (6, 15), (0, 15)], MOSSY_ROCK)
    moss(c, [(1, 7, 2), (2, 6, 3), (3, 6, 2), (4, 7, 1), (5, 7, 1), (0, 13, 2), (1, 13, 3), (2, 13, 2),
             (3, 13, 2), (4, 13, 1), (5, 2, 1), (5, 3, 0)])
    c.px(3, 2, P.STONE_D)
    c.px(2, 9, P.EARTH_D)
    c.px(3, 9, P.EARTH_D)
    return single("ravine_forest_b", c)


def rim() -> Sprite:
    """12x24 left top cap: turf (row 0 = ground surface) over rock on cols 0-7, and a lush clump of moss and
    leaves hanging over the edge into the pit (cols 6-11) with vines trailing to the bottom row."""
    c = Canvas(12, 24)
    face(c, 7, 23)
    rock(c, [(0, 7), (6, 7), (6, 14), (3, 15), (0, 14)], BROWN_ROCK)
    rock(c, [(0, 16), (4, 16), (6, 17), (6, 23), (0, 23)], MOSSY_ROCK)
    for y in range(7):                                       # turf, in the same bands as the ground strip
        c.rect(0, y, 8, y, TURF_ROWS[y])
    for x in (1, 4, 6):
        c.px(x, 0, P.LEAF_Y)
    for x, length in ((1, 4), (4, 3)):                       # grass hanging over the rock
        for k in range(length):
            c.px(x, 7 + k, P.KIT_GREEN if k < length - 1 else P.KIT_GREEN_D)
        c.px(x + 1, 7, P.KIT_GREEN_D)
    W.clump(c, 8, 4, 4)                                      # the overhang curling over the lip
    W.clump(c, 9.5, 9.5, 3)
    W.clump(c, 7, 13, 2.6)
    W.clump(c, 10, 14, 1.8)
    for x, top, length, seed in ((10, 12, 11, 3), (7, 15, 7, 5)):   # vines trailing down
        W.vine(c, x, top, length, seed, flowers=True)
    c.px(6, 2, P.WHITE)                                      # a flower in the clump
    c.px(5, 3, P.WHITE)
    c.px(7, 3, P.WHITE)
    c.px(6, 3, P.YELLOW)
    return single("ravine_forest_rim", c)


def vines() -> Sprite:
    """6x24 hanging strands from a moss pad, placed now and then down the walls."""
    c = Canvas(6, 24)
    c.ellipse(2.5, 1, 2.5, 1.2, P.KIT_GREEN_D)
    c.rect(1, 0, 3, 0, P.KIT_GREEN)
    c.px(2, 0, P.KIT_GREEN_L)
    W.vine(c, 1, 2, 20, 6, flowers=True)
    W.vine(c, 4, 2, 13, 9)
    return single("ravine_forest_vines", c)


def back() -> Sprite:
    """16x16 far pit wall in shade, tiling both ways: big dark blocks with cracks and a little moss."""
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 15, P.CLIFF_BACK_DD)
    W.cobble_row(c, 0, 9, [16], 0, BACK, 41, specks=(P.CLIFF_BACK_D,), tile_w=16)
    W.cobble_row(c, 8, 9, [16], 8, BACK, 42, specks=(P.CLIFF_BACK_D,), tile_w=16)
    for x, y, col in ((6, 4, P.CLIFF_BACK_D), (7, 5, P.CLIFF_BACK_D), (12, 12, P.CLIFF_BACK_D), (3, 13, P.CLIFF_BACK_D),
                      (5, 0, P.MOSS), (6, 0, P.KIT_GREEN_DD), (13, 8, P.MOSS), (14, 8, P.KIT_GREEN_DD)):
        c.px(x, y, col)
    return single("ravine_forest_back", c)


# --- falling water -------------------------------------------------------------------------------------

def stream(width: int, seed: int, base: list, streak_count) -> list:
    """Per column: (base colour, [(start row, length, colour)]) on a 16-row loop."""
    rnd = noise(seed)
    cols = []
    for x in range(width):
        marks = []
        light = base[x] in (P.WHITE, P.FALL_STREAK, P.BLUE_L)
        for _ in range(streak_count(x)):
            start, length = int(rnd() * 16), 5 + int(rnd() * 6)
            # A streak contrasts with its column: darker runs in the bright columns, white ones in the blue.
            choice = (P.WATER_L, P.WATER) if light else (P.WHITE, P.FALL_STREAK)
            marks.append((start, length, choice[int(rnd() * 2)]))
        cols.append((base[x], marks))
    return cols


def colour_at(column, v: int):
    col = column[0]
    for start, length, mark in column[1]:
        if (v - start) % 16 < length:
            col = mark
    return col


# Brightness across the 16-px curtain: highlight columns at 2, 7 and 12, mid blues between.
FALL_BASE = [P.BLUE_L, P.WHITE, P.FALL_STREAK, P.WATER_L, P.WATER, P.WATER_L, P.FALL_STREAK, P.WHITE, P.BLUE_L,
             P.WATER_L, P.WATER, P.WATER_D, P.WATER_L, P.FALL_STREAK, P.WHITE, P.WATER_L]


def falls() -> Sprite:
    """16x16 curtain, `flow` 4: tiles both ways in every frame; streaks move down 4 px a frame."""
    cols = stream(16, 77, FALL_BASE, lambda x: 1)
    frames = []
    for k in range(4):
        c = Canvas(16, 16)
        for x in range(16):
            for y in range(16):
                c.px(x, y, colour_at(cols[x], (y - 4 * k) % 16))
        frames.append(c)
    sprite = Sprite("ravine_forest_falls", (16, 16))
    sprite.add("flow", frames, fps=10)
    return sprite


def falls_edge() -> Sprite:
    """4x16 soft edge where the curtain meets the left wall (col 0 = wall side), `flow` 4, tiling vertically.
    Opaque: its gaps are painted in the shaded back-wall colours, so it looks the same over anything."""
    cols = stream(4, 78, [P.CLIFF_BACK_D, P.WATER, P.WATER_L, P.BLUE_L], lambda x: 1 + (x > 0))
    gaps = {0: [(0, 6), (9, 5)], 1: [(4, 3), (12, 2)], 2: [(8, 2)], 3: []}
    frames = []
    for k in range(4):
        c = Canvas(4, 16)
        for x in range(4):
            for y in range(16):
                v = (y - 4 * k) % 16
                col = colour_at(cols[x], v)
                if any((v - s) % 16 < n for s, n in gaps[x]):
                    col = P.CLIFF_BACK_DD if x == 0 else P.CLIFF_BACK_D
                c.px(x, y, col)
        frames.append(c)
    sprite = Sprite("ravine_forest_falls_edge", (4, 16))
    sprite.add("flow", frames, fps=10)
    return sprite


def lip() -> Sprite:
    """16x6 rounded white-blue brink where the water spills over the rim, `flow` 4, tiling horizontally.
    Row 0 = the ground surface; rows 4-5 thin out so the curtain below shows through."""
    frames = []
    for k in range(4):
        c = Canvas(16, 6)
        for x in range(16):
            swell = round(0.6 + 0.6 * math.sin(2 * math.pi * x / 8))          # gentle bulges, period 8
            c.px(x, 1 - swell, P.BLUE_L)
            for y in range(2 - swell, 4):
                c.px(x, y, P.WHITE)
            c.px(x, 3, P.FALL_STREAK if (x + 4 * k) % 5 else P.WHITE)        # light sliding over the brink
            if (x + k) % 3:
                c.px(x, 4, P.WHITE if (x * 3 + k) % 4 == 0 else P.BLUE_L)
            if (x + k) % 4 == 0:
                c.px(x, 5, P.WHITE)
        frames.append(c)
    sprite = Sprite("ravine_forest_lip", (16, 6))
    sprite.add("flow", frames, fps=10)
    return sprite


# --- pool ----------------------------------------------------------------------------------------------

def surface() -> Sprite:
    """16x8 pool surface, `wave` 4, tiling horizontally: a white crest on a gentle wave over bright turquoise;
    row 7 = the plunge pool's top colour."""
    frames = []
    for k in range(4):
        c = Canvas(16, 8)
        for x in range(16):
            crest = 1 + round(math.sin((x / 16 + k / 4) * 2 * math.pi) * 0.8 + 0.2)
            c.px(x, crest, P.WHITE)
            for y in range(crest + 1, 8):
                c.px(x, y, P.BLUE_L if y == crest + 1 else P.POOL_L if y < 5 else P.POOL)
            if crest >= 1 and (x + k * 2) % 8 in (0, 1):
                c.px(x, crest - 1, P.BLUE_L)
        for x0, y in ((3, 4), (11, 6)):
            for d in range(3):
                c.px((x0 + k * 2 + d) % 16, y, P.WHITE)
        frames.append(c)
    sprite = Sprite("ravine_forest_surface", (16, 8))
    sprite.add("wave", frames, fps=8)
    return sprite


def pool() -> Sprite:
    """16x24 plunge pool under the surface, `churn` 4, tiling horizontally: churned turquoise with rising
    bubbles near the top, fading through blue to the deep colour on row 23 (where `ravine_forest_deep` starts)."""
    bands = [(0, 5, P.POOL, P.POOL), (5, 8, P.POOL, P.WATER), (8, 12, P.WATER, P.WATER), (12, 15, P.WATER, P.WATER_D),
             (15, 19, P.WATER_D, P.WATER_D), (19, 22, P.WATER_D, P.WATER_DD), (22, 24, P.WATER_DD, P.WATER_DD)]
    rnd = noise(55)
    bubbles = [(int(rnd() * 16), int(rnd() * 16), 1 + int(rnd() * 2)) for _ in range(9)]
    frames = []
    for k in range(4):
        c = Canvas(16, 24)
        for y0, y1, a, b in bands:
            for y in range(y0, y1):
                for x in range(16):
                    c.px(x, y, b if (x + y) % 2 else a)
        for bx, by, size in bubbles:                      # bubbles rise 2 or 4 px a frame on a 16-row loop
            y = (by - 2 * k * size) % 16
            if y < 14:
                col = P.WHITE if y < 5 else P.POOL_L if y < 10 else P.WATER_L
                c.px(bx, y, col)
                if size == 2 and y < 8:
                    c.px((bx + 1) % 16, y, col)
        for x0, y, n in ((2, 2, 5), (10, 5, 4)):          # foam swirls drifting along
            for d in range(n):
                c.px((x0 + d + k) % 16, y, P.POOL_L)
        frames.append(c)
    sprite = Sprite("ravine_forest_pool", (16, 24))
    sprite.add("churn", frames, fps=8)
    return sprite


def splash() -> Sprite:
    """16x12 foam band, `splash` 4, tiling horizontally: thick churning white foam (about rows 2-11) where the
    curtain hits the pool, with spray and droplets thrown up above it."""
    frames = []
    for k in range(4):
        c = Canvas(16, 12)
        c.rect(0, 8, 15, 11, P.WHITE)                       # the churning base
        for x in range(16):
            if (x + k) % 3 == 0:
                c.px(x, 11, P.BLUE_L)
            if (x * 5 + k) % 7 == 0:
                c.px(x, 10, P.BLUE_L)
        # Round foam mounds that boil up and sink, drawn wrapped so the band tiles.
        mounds = [((1 + k) % 16, 4.2 - (k % 2), 3.4), ((7 + 2 * k) % 16, 3.2 + (k % 2), 3.8), ((12 - k) % 16, 5, 2.8)]
        for mx, my, rad in mounds:
            for shift in (-16, 0, 16):
                c.ellipse(mx + shift + 0.6, my + 1.2, rad, rad * 0.8, P.BLUE_L)     # shade on the lower right
                c.ellipse(mx + shift, my + 0.6, rad - 0.4, rad * 0.75, P.WHITE)
                c.px(mx + shift + rad * 0.5, my + rad * 0.6, P.WATER_L)
        rnd = noise(90 + k)
        for _ in range(6):                                 # spray and droplets thrown up
            x, y = int(rnd() * 16), int(rnd() * 2)
            c.px(x, y, P.WHITE if rnd() > 0.4 else P.WATER_L)
            if rnd() > 0.6:
                c.px(x, y + 1, P.BLUE_L)
        frames.append(c)
    sprite = Sprite("ravine_forest_splash", (16, 12))
    sprite.add("splash", frames, fps=10)
    return sprite


def deep() -> Sprite:
    """16x16 deep water, tiling both ways: dark blue with a few faint light streaks."""
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 15, P.WATER_DD)
    for x0, y, n, col in ((2, 3, 4, P.WATER_D), (10, 7, 3, P.WATER_D), (5, 11, 5, P.WATER_D), (13, 14, 4, P.WATER_D),
                          (11, 3, 2, P.WATER_NIGHT), (1, 8, 2, P.WATER_NIGHT)):
        for d in range(n):
            c.px((x0 + d) % 16, y, col)
    c.px(3, 3, P.WATER)
    c.px(6, 11, P.WATER)
    return single("ravine_forest_deep", c)


def floor() -> Sprite:
    """16x16 pit bottom under the pool, tiling horizontally. Rows 0-4 are the pool's deep colour, with the
    rounded tops of big wet stones rising into it (a bumpy bed, not a flat line). Below them, smaller grey
    cobbles like the earth's. The bottom contour is the rounded undersides of those cobbles, left clear
    between them, so the floor sits on whatever earth row is below without a straight seam."""
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 4, P.WATER_DD)                          # the last of the pool
    c.rect(0, 5, 15, 11, P.EARTH_DD)                         # mortar behind the stones
    for x0, x1, y0 in ((0, 6, 2), (7, 15, 3)):               # big wet stones, tops in the water
        W.cobble(c, x0, y0, x1, 10, (P.STONE_L, P.STONE, P.STONE_D))
        c.px(x0 + 2, y0, P.WATER_L)                          # a wet glint
        c.px(x0 + 3, y0, P.BLUE_L)
        c.px(x1 - 1, y0 + 2, P.STONE_D)
    for x0, y in ((7, 1), (6, 2)):                           # silt between them
        c.px(x0, y + 2, P.WATER_NIGHT)
    for x0, x1, y1 in ((0, 4, 14), (5, 10, 15), (11, 15, 13)):  # earth-grey cobbles, ragged bottom
        W.cobble(c, x0, 9, x1, y1, (P.STONE, P.STONE_D, P.STONE_DD))
    c.px(7, 12, P.KIT_GREEN_D)                               # a speck of moss and one of gold, as in the earth
    c.px(2, 11, P.GOLD_D)
    c.px(4, 5, P.KIT_GREEN_D)                                # water weed on a stone
    c.px(4, 4, P.KIT_GREEN)
    return single("ravine_forest_floor", c)


def build() -> list[Sprite]:
    return [wall_a(), wall_b(), rim(), vines(), back(), falls(), falls_edge(), lip(), surface(), pool(), splash(),
            deep(), floor()]
