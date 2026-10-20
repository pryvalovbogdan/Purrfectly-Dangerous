"""Raised and sunken forest ground and the floating island, in the Purrwood kit look.

Tiling contract (see docs/sprite-spec.md): a block's interior is `terrain_forest_fill` behind a row of
`terrain_forest_top` tiles; its ends are `terrain_forest_edge` (left; mirrored for the right) over a column
of `terrain_forest_wall`. The end pieces only paint the outer three columns (a 1 px grass overhang in col 0,
a dark earth outline in col 1, a shaded rim in col 2) plus moss, tufts, vines and roots; everything from
col 3 inward is left clear so the block's own top/fill (or the base ground) shows through and no seam can
form. The top and fill tiles start every cobble row on a joint at x 0 and end each tile on a stone's
dark bottom rim, so they stack on each other and on `ground_forest_earth` without half stones."""
from __future__ import annotations

import palette as P
from draw import Canvas, noise
from sprite import Sprite, single
import woodland as W

BROWN = (P.EARTH_L, P.EARTH, P.EARTH_D)
SPECKS = (P.EARTH_D, P.GOLD_D, P.KIT_GREEN_D)
# Turf rows 0-6 use the same bands as the base ground's grass (woodland.grass_top).
TURF_ROWS = [P.KIT_GREEN_L, P.KIT_GREEN_L, P.KIT_GREEN, P.KIT_GREEN, P.KIT_GREEN, P.KIT_GREEN_D, P.KIT_GREEN_D]


def flower(c: Canvas, x: int, y: int, petal) -> None:
    """A tiny hanging flower: three petals around a yellow eye."""
    c.px(x, y, P.YELLOW)
    c.px(x - 1, y, petal)
    c.px(x + 1, y, petal)
    c.px(x, y + 1, petal)


def top() -> Sprite:
    """16x16, tiles horizontally: thick turf (row 0 = walk surface) with tufts over one brown cobble row."""
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 15, P.EARTH_DD)
    W.cobble_row(c, 7, 10, [7, 9], 0, BROWN, 5, specks=SPECKS, tile_w=16)  # rows 7-15, joint at x 0
    W.grass_top(c, 16, 2, flowers=False)
    flower(c, 11, 10, P.PINK)                                # a flower dangling from a tuft tip
    c.px(11, 9, P.KIT_GREEN_D)
    return single("terrain_forest_top", c)


def outline_left(c: Canvas, rows, colour=P.WOOD_OUT) -> None:
    """Dark outline one pixel left of the leftmost opaque pixel of each row."""
    for y in rows:
        for x in range(c.size[0]):
            if c.img.getpixel((x, y))[3]:
                c.px(x - 1, y, colour)
                break


def stone_end(c: Canvas, y0: int, y1: int) -> None:
    """The rounded end of a cobble row at the block's side (cols 2-7, right column = a joint)."""
    c.rect(4, y0, 7, y1, P.EARTH_DD)
    W.cobble(c, 2, y0, 7, y1, BROWN)


def edge() -> Sprite:
    """8x16, the left end cap: a rounded grass lip overhanging the stone side by two pixels, tufts and a
    flower over the corner, a root poking out of the side."""
    c = Canvas(8, 16)
    stone_end(c, 7, 15)                                      # the band's cobble row, ending in a rounded stone
    c.px(4, 11, P.GOLD_D)
    outline_left(c, range(7, 16))
    starts = [3, 1, 0, 0, 0, 0, 1]                           # rounded turf corner
    for y, x0 in enumerate(starts):
        c.rect(x0, y, 7, y, TURF_ROWS[y])
    for x, y, col in ((2, 0, P.KIT_GREEN), (1, 1, P.KIT_GREEN), (0, 2, P.KIT_GREEN),   # lit rim of the lip
                      (3, 0, P.LEAF_Y), (6, 0, P.LEAF_Y), (2, 1, P.LEAF_Y), (5, 2, P.KIT_GREEN_L),
                      (0, 4, P.KIT_GREEN_D), (0, 5, P.KIT_GREEN_DD), (1, 6, P.KIT_GREEN_DD),  # shaded underside
                      (3, 3, P.KIT_GREEN_D), (4, 4, P.KIT_GREEN_D)):                        # leaf vein
        c.px(x, y, col)
    for x, length in ((1, 4), (5, 5)):                       # tufts hanging over the face
        for k in range(length):
            c.px(x, 6 + k, P.KIT_GREEN if k < length - 2 else P.KIT_GREEN_D)
            if k < length - 2:
                c.px(x + 1, 6 + k, P.KIT_GREEN_D)
        c.px(x, 6 + length, P.KIT_GREEN_DD)
        c.px(x, 6, P.LEAF_Y)
    c.px(2, 6, P.KIT_GREEN)
    flower(c, 4, 1, P.WHITE)                                 # a tiny flower on the corner
    c.px(0, 13, P.BARK)                                      # a root poking out of the side
    c.px(1, 13, P.BARK_D)
    c.px(0, 14, P.BARK_D)
    c.px(1, 12, P.BARK_D)
    return single("terrain_forest_edge", c)


def wall() -> Sprite:
    """8x16, the left side face, tiling vertically: the rounded ends of two 8-row cobble rows (the fill's
    rows), outlined, with a moss patch and a short vine hanging from it."""
    c = Canvas(8, 16)
    stone_end(c, 0, 7)
    stone_end(c, 8, 15)
    outline_left(c, range(16))
    for x, y, col in ((3, 0, P.KIT_GREEN_L), (4, 0, P.KIT_GREEN), (5, 0, P.KIT_GREEN_D), (2, 1, P.KIT_GREEN),
                      (3, 1, P.KIT_GREEN), (4, 1, P.KIT_GREEN_D), (1, 2, P.KIT_GREEN), (2, 2, P.KIT_GREEN_D),
                      (1, 3, P.KIT_GREEN_D)):
        c.px(x, y, col)                                      # moss over the top of a stone
    # A vine hanging from moss on the lower stone. It stays between the scallops (rows 7-8 and 15-0, where
    # the rounded stone ends leave the outer columns clear), so it never frames a gap that reads as a hole.
    c.px(2, 9, P.KIT_GREEN)
    c.px(1, 9, P.KIT_GREEN_D)
    for k, y in enumerate(range(10, 14)):
        c.px(0, y, P.KIT_GREEN_D if k % 2 else P.KIT_GREEN)
    c.px(1, 11, P.KIT_GREEN_L)
    c.px(0, 14, P.KIT_GREEN_L)
    c.px(2, 13, P.KIT_GREEN_D)                               # a streak of moss on the lower stone
    c.px(3, 12, P.KIT_GREEN_D)
    c.px(4, 12, P.KIT_GREEN_DD)
    return single("terrain_forest_wall", c)


def fill() -> Sprite:
    """16x16, tiling both ways: two rows of brown cobbles; the bottom row ends on a stone rim, so it sits
    on ground_forest_earth (which starts on a stone top) like the ground tile's own brown-to-grey change."""
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 15, P.EARTH_DD)
    W.cobble_row(c, 0, 9, [9, 7], 2, BROWN, 6, specks=SPECKS, tile_w=16)
    W.cobble_row(c, 8, 9, [7, 9], 7, BROWN, 7, specks=SPECKS, tile_w=16)
    return single("terrain_forest_fill", c)


def island() -> Sprite:
    """48x24 floating island: grass top (row 0 = walk surface) over a rounded underside of earth and rock,
    with vines hanging from both sides and roots from the tip."""
    w, h = 48, 24
    body = Canvas(w, h)                                      # the underside: cobbles cut to a rounded wedge
    stones = Canvas(w, h)
    stones.rect(0, 0, w - 1, h - 1, P.EARTH_DD)
    W.cobble_row(stones, 6, 8, [9, 10, 9, 10, 10], 1, BROWN, 21, specks=SPECKS, tile_w=48)
    W.cobble_row(stones, 12, 7, [8, 9, 7, 9, 8, 7], 5, BROWN, 22, specks=SPECKS, tile_w=48)
    W.cobble_row(stones, 17, 6, [7, 8, 8, 7], 9, (P.STONE_L, P.STONE, P.STONE_D), 23, tile_w=48)
    half = {y: hw for y, hw in zip(range(6, 22), (22, 22, 22, 21, 21, 20, 19, 18, 17, 15, 13, 11, 9, 7, 5, 3))}
    src = stones.img.load()
    for y, hw in half.items():
        for x in range(w):
            if abs(x + 0.5 - w / 2) <= hw:
                body.px(x, y, src[x, y])
    turf = Canvas(44, 14)
    W.grass_top(turf, 44, 4, flowers=False)
    body.paste(turf, 2, 0)
    for y, inset in enumerate((2, 1, 0, 0, 0, 0, 1)):        # round the turf ends past the earth
        for k in range(inset):
            body.px(1 + k, y, P.CLEAR)
            body.px(w - 2 - k, y, P.CLEAR)
        body.px(1 + inset, y, TURF_ROWS[y])
        body.px(w - 2 - inset, y, TURF_ROWS[y])
    body.px(1, 5, P.KIT_GREEN_DD)
    body.px(w - 2, 5, P.KIT_GREEN_DD)
    body.outline(P.EARTH_DD)
    c = Canvas(w, h)
    c.paste(body)
    c.px(2, 0, P.CLEAR)                                      # no dark outline on the walk surface
    c.px(w - 3, 0, P.CLEAR)
    flower(c, 15, 2, P.PINK)
    flower(c, 35, 2, P.WHITE)
    W.vine(c, 3, 6, 15, 3, flowers=True)                     # vines hanging from both sides
    W.vine(c, 44, 6, 12, 5, flowers=True)
    W.vine(c, 33, 15, 6, 8)
    c.px(23, 22, P.BARK_D)                                   # roots from the tip
    c.px(24, 23, P.BARK_D)
    c.px(26, 22, P.BARK_D)
    c.px(26, 23, P.BARK_DD)
    return single("island", c)


def build() -> list[Sprite]:
    return [top(), edge(), wall(), fill(), island()]
