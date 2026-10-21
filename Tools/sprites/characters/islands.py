"""Themed floating islands and the citadel bridge: the same sizes, anchors and walk-surface rows as the forest's
`island` (48x24, top row = walk surface, placed like `bridge`) and `bridge` (48x12, still + crumble 4). The renderer
uses `<kind>_<theme>` when it exists."""
from __future__ import annotations

import math

import palette as P
from characters.forest import platform
from draw import Canvas, noise
from sprite import Sprite, single
import woodland as W

W_, H_ = 48, 24
# Half-widths of the rounded wedge under the top, rows 6-21 (as the forest island).
HALF = {y: hw for y, hw in zip(range(6, 22), (22, 22, 22, 21, 21, 20, 19, 18, 17, 15, 13, 11, 9, 7, 5, 3))}


def wedge(rows: list, mortar, outline) -> Canvas:
    """The island's underside: courses of stones (y0, height, widths, offset, ramp, seed) cut to the wedge."""
    stones = Canvas(W_, H_)
    stones.rect(0, 0, W_ - 1, H_ - 1, mortar)
    for y0, height, widths, offset, ramp, seed in rows:
        W.cobble_row(stones, y0, height, widths, offset, ramp, seed, tile_w=W_)
    body = Canvas(W_, H_)
    src = stones.img.load()
    for y, hw in HALF.items():
        for x in range(W_):
            if abs(x + 0.5 - W_ / 2) <= hw:
                body.px(x, y, src[x, y])
    return body


def slab_top(body: Canvas, rows: list, rounding=(2, 1, 0, 0, 0, 0, 1)) -> None:
    """A 7-row top (one colour per row) across cols 1-46 with rounded ends; row 0 is the walk surface."""
    for y, col in enumerate(rows):
        inset = rounding[y]
        body.rect(1 + inset, y, W_ - 2 - inset, y, col)


def finish(body: Canvas, outline) -> Canvas:
    """Outline the body, but keep the walk surface (row 0) free of a dark cap at its ends."""
    body.outline(outline)
    c = Canvas(W_, H_)
    c.paste(body)
    c.px(2, 0, P.CLEAR)
    c.px(W_ - 3, 0, P.CLEAR)
    return c


def icicle(c: Canvas, x: float, top: float, length: float) -> None:
    c.poly([(x - 1.5, top), (x + 1.5, top), (x, top + length)], P.FR_ICE_L)
    c.line((x - 0.5, top), (x, top + length - 1), P.FR_ICE_GLOW)


def island_frost() -> Sprite:
    """A snow-capped icy rock: thick snow on top, indigo stone and blue ice below, icicles hanging under it."""
    body = wedge([(6, 8, [9, 10, 9, 10, 10], 1, (P.FR_ROCK_L, P.FR_ROCK, P.FR_ROCK_D), 701),
                  (12, 7, [8, 9, 7, 9, 8, 7], 5, (P.FR_ICE_L, P.FR_ICE, P.FR_ICE_D), 702),
                  (17, 6, [7, 8, 8, 7], 9, (P.FR_ROCK, P.FR_ROCK_D, P.FR_ROCK_DD), 703)], P.FR_ROCK_DD, P.FR_ICE_DD)
    slab_top(body, [P.WHITE, P.WHITE, P.SNOW_L, P.SNOW_L, P.SNOW_L, P.SNOW, P.SNOW])
    for x in range(3, 45, 5):                                # snow drooping over the lip
        body.ellipse(x + 2, 7, 2.2, 1.6, P.SNOW_L)
        body.px(x + 2, 8, P.SNOW)
    c = finish(body, P.FR_ICE_DD)
    for x in (7, 19, 33, 41):                                # sparkles in the snow
        c.px(x, 2, P.FR_ICE_GLOW)
    for x, top, length in ((5, 9, 6), (12, 12, 8), (20, 16, 7), (27, 18, 6), (34, 14, 9), (42, 9, 5)):
        icicle(c, x, top, length)
    return single("island_frost", c)


def candle(c: Canvas, x: float, base: float, h: int) -> None:
    c.rect(x, base - h + 1, x + 1, base, P.HM_WAX)
    c.px(x + 1, base - h + 2, P.HM_WAX_D)
    c.px(x, base - h, P.HM_FLAME)
    c.px(x + 1, base - h, P.HM_FLAME_D)


def island_haunted() -> Sprite:
    """A floating chunk of violet masonry: a lit stone top, bricks and rough stone below, candles set in niches in
    its face (the top row stays a clear walk surface) and a purple glow underneath."""
    body = wedge([(6, 7, [12, 12, 12, 12], 2, (P.HM_STONE_L, P.HM_STONE, P.HM_STONE_D), 711),
                  (11, 7, [12, 12, 12, 12], 8, (P.HM_STONE, P.HM_STONE_D, P.HM_STONE_DD), 712),
                  (16, 7, [8, 9, 8, 9, 7, 7], 4, (P.HM_STONE, P.HM_STONE_D, P.HM_STONE_DD), 713)],
                 P.HM_STONE_DD, P.HM_STONE_DD)
    slab_top(body, [P.HM_STONE_TOP, P.HM_STONE_L, P.HM_STONE, P.HM_STONE, P.HM_STONE, P.HM_STONE_D, P.HM_STONE_D],
             rounding=(1, 0, 0, 0, 0, 0, 1))
    for x in range(1, 47, 12):                               # joints in the top slab
        body.rect(x, 1, x, 5, P.HM_STONE_DD)
    for x in (9, 24, 39):                                    # candle niches
        body.rect(x - 2, 2, x + 3, 5, P.HM_STONE_DD)
    c = finish(body, P.HM_STONE_DD)
    for x, h in ((9, 3), (24, 4), (39, 3)):
        candle(c, x, 5, h)
    glow = Canvas(W_, H_)                                    # purple glow under it, blended behind
    glow.ellipse(24, 19, 20, 5, (P.HM_FOG[0], P.HM_FOG[1], P.HM_FOG[2], 70))
    glow.ellipse(24, 21, 12, 3, (P.HM_GLASS[0], P.HM_GLASS[1], P.HM_GLASS[2], 70))
    glow.paste(c)
    for x, y in ((14, 16), (31, 17), (24, 21)):              # wisps dripping off the bottom
        glow.px(x, y + 1, P.HM_FOG_L)
    return single("island_haunted", glow)


def lava_drip(c: Canvas, x: float, top: float, length: float) -> None:
    c.poly([(x - 1.5, top), (x + 1.5, top), (x + 0.5, top + length), (x - 0.5, top + length)], P.LAVA)
    c.line((x, top), (x, top + length - 1), P.LAVA_L)
    c.px(x, top + length + 1, P.CC_LAVA_D)


def island_citadel() -> Sprite:
    """A charred rock chunk: a scorched stone top, dark cobbles with glowing cracks, lava dripping off it."""
    body = wedge([(6, 8, [9, 10, 9, 10, 10], 1, (P.CC_STONE_L, P.CC_STONE, P.CC_STONE_D), 721),
                  (12, 7, [8, 9, 7, 9, 8, 7], 5, (P.CC_STONE, P.CC_STONE_D, P.CC_STONE_DD), 722),
                  (17, 6, [7, 8, 8, 7], 9, (P.CC_STONE, P.CC_STONE_D, P.CC_STONE_DD), 723)], P.CC_STONE_DD,
                 P.CC_STONE_DD)
    slab_top(body, [P.CC_STONE_TOP, P.CC_STONE_L, P.CC_STONE, P.CC_STONE, P.CC_STONE_D, P.CC_STONE_D, P.CC_LAVA_DD],
             rounding=(1, 0, 0, 0, 0, 0, 1))
    for x in range(4, 46, 9):                                # cracks in the top slab
        body.line((x, 2), (x + 1, 4), P.CC_STONE_DD)
    c = finish(body, P.CC_STONE_DD)
    for x in (8, 21, 30, 40):                                # the glowing seam under the top
        c.px(x, 6, P.LAVA)
    for pts in (((14, 9), (15, 10), (15, 11), (16, 12)), ((30, 13), (31, 14), (30, 15)), ((22, 17), (23, 18))):
        for x, y in pts:                                     # glowing cracks in the underside
            c.px(x, y, P.LAVA)
        c.px(*pts[-1], P.LAVA_L)
    for x, top, length in ((6, 8, 5), (18, 14, 4), (25, 21, 2), (36, 13, 6), (43, 8, 3)):
        lava_drip(c, x, top, length)
    return single("island_citadel", c)


def bridge_citadel() -> Sprite:
    """48x12, like `bridge`: charred planks bolted to an iron frame (walk surface = top row), an iron post at the
    left with a chain wrapped round it, and chains hanging in swags under the deck. Crumbles like the bridge."""
    w, h = 48, 12
    c = Canvas(w, h)
    for i, x in enumerate(range(4, w, 6)):                    # charred planks
        c.rect(x, 1, x + 4, 5, P.BARK_D if i % 2 else P.BARK_DD)
        c.rect(x, 1, x + 4, 1, P.BARK)
        c.rect(x, 5, x + 4, 5, P.CC_STONE_DD)
        c.px(x + 1 + i % 3, 3, P.CC_LAVA_DD if i % 3 == 0 else P.BARK_DD)   # scorch marks, an ember
        c.rect(x + 5, 1, x + 5, 5, P.CC_STONE_DD)
    c.rect(4, 6, w - 1, 6, P.IRON)                            # the iron girder under the planks
    for x in range(6, w, 8):
        c.px(x, 6, P.IRON_L)                                  # bolts
    c.rect(0, 1, 3, 11, P.IRON_D)                             # the iron post
    c.rect(0, 1, 0, 11, P.IRON)
    c.rect(0, 1, 3, 1, P.IRON_L)
    for y in (3, 6, 9):                                       # chain wrapped round it
        c.rect(0, y, 3, y, P.IRON_L)
    for x0 in range(4, w - 4, 12):                            # chains hanging in swags
        for k in range(13):
            x = x0 + k
            y = 7 + round(math.sin(k / 12 * math.pi) * 3)
            c.px(x, y, P.IRON if k % 2 else P.IRON_L)
    c.px(2, 4, P.LAVA)                                        # an ember caught on the post
    return platform("bridge_citadel", c.outline(P.CC_STONE_DD), "crumble", 731)


def build() -> list[Sprite]:
    return [island_frost(), island_haunted(), island_citadel(), bridge_citadel()]
