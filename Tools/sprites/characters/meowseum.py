"""World 3's environment, the Haunted Meowseum, after docs/concept/Haunted Meowseum Pixel Art Tileset.png (reference
only): a gothic museum hall of violet stone with magenta stained glass, candlelight, crimson cat-crest banners and gold
frames, opening onto a purple night with a huge pink moon. Same names, sizes and tiling contracts as the forest's
(docs/sprite-spec.md); props and enemies are in characters/haunted.py."""
from __future__ import annotations

import math

import palette as P
from characters.scenery import LAYER_W, flat, ground, smooth_sky
from characters.waterfall import colour_at
from draw import Canvas, noise, see_through
from sprite import Sprite, single
import woodland as W

STONE = (P.HM_STONE_L, P.HM_STONE, P.HM_STONE_D)
STONE_DARK = (P.HM_STONE, P.HM_STONE_D, P.HM_STONE_DD)


def rgba(col, a: int):
    return (col[0], col[1], col[2], a)


def glow(c: Canvas, x: float, y: float, rx: float, ry: float, col, a: int) -> None:
    """A see-through ellipse blended over what is already drawn (ImageDraw would replace the pixels and punch
    a hole instead)."""
    layer = Canvas(*c.size)
    layer.ellipse(x, y, rx, ry, rgba(col, a))
    c.paste(layer)


# --- bricks, candles and fog ----------------------------------------------------------------------------

def brick(c: Canvas, x0: float, y0: float, x1: float, y1: float, ramp=STONE, chip: bool = False) -> None:
    """A dressed stone brick: lit top row and left column, shaded bottom row and right column."""
    light, body, dark = ramp
    c.rect(x0, y0, x1, y1, body)
    c.rect(x0, y1, x1, y1, dark)
    c.rect(x1, y0, x1, y1, dark)
    c.rect(x0, y0, x1 - 1, y0, light)
    c.rect(x0, y0, x0, y1 - 1, light)
    if chip:
        c.px(x1 - 1, y0 + 1, dark)


def brick_row(c: Canvas, y0: int, height: int, widths: list, offset: int, ramp, seed: int, tile_w: int) -> None:
    """One course of bricks (each `height` rows including the mortar row below), wrapped at `tile_w`."""
    rnd = noise(seed)
    x = offset
    for w in widths:
        chip = rnd() > 0.6
        crack = rnd() > 0.75
        cx = rnd()
        for shift in (-tile_w, 0, tile_w):
            brick(c, x + shift, y0, x + shift + w - 2, y0 + height - 2, ramp, chip)
            if crack:
                px = x + shift + 2 + cx * (w - 5)
                c.line((px, y0 + 1), (px + 1, y0 + height - 3), ramp[2])
        x += w


def candle(c: Canvas, x: float, base: float, h: int, halo: bool = True) -> None:
    """A wax candle `h` tall standing on row `base`, with a drip, a flame and a soft halo."""
    if halo:
        glow(c, x + 0.5, base - h - 2, 4, 4, P.HM_FLAME, 46)
    c.rect(x, base - h + 1, x + 1, base, P.HM_WAX)
    c.px(x + 1, base - h + 2, P.HM_WAX_D)
    c.px(x - 1 if h % 2 else x + 2, base - h + 2, P.HM_WAX)                # a drip
    c.px(x, base - h, P.HM_FLAME)
    c.px(x, base - h - 1, P.HM_FLAME_D if h % 2 else P.HM_FLAME)
    c.px(x + 1, base - h, P.HM_FLAME_D)


def fog_band(c: Canvas, y: float, depth: float, seed: int, cols, alpha: int) -> None:
    """Rolling fog: overlapping puffs along a band, wrapped across the strip, laid over the layer at `alpha`."""
    rnd = noise(seed)
    band = Canvas(*c.size)
    x = 0
    while x < c.size[0]:
        r = 6 + rnd() * 8
        yy = y + rnd() * depth
        light, body = cols

        def puff(px, r=r, yy=yy):
            band.ellipse(px, yy + 1, r, r * 0.55, body)
            band.ellipse(px - 1, yy, r * 0.75, r * 0.4, light)
        W.wrapped(puff, x, c.size[0])
        x += r * 1.2
    c.paste(see_through(band.img, alpha))


# --- parallax ------------------------------------------------------------------------------------------

def stars(c: Canvas, seed: int, count: int, y1: int) -> None:
    rnd = noise(seed)
    for _ in range(count):
        x, y = rnd() * LAYER_W, rnd() * y1
        c.px(x, y, P.HM_MOON if rnd() > 0.5 else P.HM_FOG_L)
        if rnd() > 0.85:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c.px(x + dx, y + dy, rgba(P.HM_FOG_L, 120))


def big_moon(c: Canvas, x: float, y: float, rad: float) -> None:
    for r, a in ((rad + 14, 22), (rad + 8, 40), (rad + 3, 70)):
        glow(c, x, y, r, r, P.HM_MOON_D, a)
    c.ellipse(x, y, rad, rad, P.HM_MOON_S)
    c.ellipse(x - 2, y - 2, rad - 2, rad - 2, P.HM_MOON)
    for cx, cy, cr in ((-8, -5, 4), (6, 4, 5), (-3, 10, 3), (9, -9, 2.5), (-12, 6, 2), (2, -12, 2)):
        c.ellipse(x + cx, y + cy, cr, cr, P.HM_MOON_S)
        c.px(x + cx + cr * 0.4, y + cy + cr * 0.4, P.HM_MOON_D)


def haunted_clouds() -> Canvas:
    """The 150-tall layer on the ground line: stars, the huge pink moon and purple cloud banks."""
    c = Canvas(LAYER_W, 150)
    stars(c, 401, 60, 110)
    big_moon(c, 236, 30, 24)
    fog_band(c, 82, 16, 402, (P.HM_CLOUD_L, P.HM_CLOUD), 120)
    fog_band(c, 104, 12, 403, (P.HM_CLOUD, P.HM_CLOUD_D), 150)
    return c


def haunted_puffs() -> Canvas:
    c = Canvas(LAYER_W, 120)
    stars(c, 404, 70, 118)
    fog_band(c, 70, 20, 405, (P.HM_CLOUD, P.HM_CLOUD_D), 80)
    return c


def spire(c: Canvas, x: float, base: float, w: float, h: float, col, window=None) -> None:
    c.rect(x - w / 2, base - h, x + w / 2, base, col)
    c.poly([(x - w / 2 - 1, base - h), (x, base - h - w * 1.8), (x + w / 2 + 1, base - h)], col)
    c.line((x, base - h - w * 1.8), (x, base - h - w * 1.8 - 3), col)
    if window:
        for wy in range(int(base - h + 4), int(base - 6), 9):
            c.rect(x - 0.5, wy, x + 0.5, wy + 2, window)


def floating_island(c: Canvas, x: float, y: float, w: float) -> None:
    c.poly([(x - w / 2, y), (x + w / 2, y), (x + w / 4, y + w * 0.35), (x + 2, y + w * 0.7), (x - w / 3, y + w * 0.3)],
           P.HM_SIL_L)
    c.rect(x - w / 2, y - 2, x + w / 2, y, P.HM_STONE_D)
    c.rect(x - w / 2, y - 2, x + w / 2, y - 2, P.HM_STONE)
    for k in range(3):
        candle(c, x - w / 3 + k * w / 3, y - 3, 2 + k % 2)


def haunted_far() -> Canvas:
    """A distant spiky castle silhouette with lit windows, ruined towers and floating islands."""
    h = 140
    c = Canvas(LAYER_W, h)
    rnd = noise(411)
    for k in range(22):                                       # the jagged skyline of spires
        x = k * LAYER_W / 22 + rnd() * 8
        sh = 34 + rnd() * 46
        sw = 4 + rnd() * 5
        W.wrapped(lambda px, sh=sh, sw=sw: spire(c, px, h, sw, sh, P.HM_SIL), x)
    c.rect(0, h - 14, LAYER_W - 1, h - 1, P.HM_SIL)
    cx = 120                                                  # the great castle
    c.rect(cx - 40, h - 46, cx + 40, h, P.HM_SIL_D)
    for dx, sh, sw in ((-34, 72, 8), (-20, 92, 9), (0, 110, 12), (20, 92, 9), (34, 72, 8), (-44, 56, 6), (44, 56, 6),
                       (-10, 80, 6), (10, 80, 6)):
        spire(c, cx + dx, h, sw, sh, P.HM_SIL_D, P.HM_GLASS)
    c.ellipse(cx, h - 12, 6, 9, P.HM_FLAME_D)                # the lit gate
    c.ellipse(cx, h - 11, 4, 7, P.HM_FLAME)
    for wx in (-30, -16, 16, 30):
        c.rect(cx + wx - 1, h - 36, cx + wx + 1, h - 31, P.HM_GLASS)
    for ax in range(cx + 44, cx + 110, 14):                  # an arched bridge to a ruined tower
        c.rect(ax, h - 34, ax + 13, h - 30, P.HM_SIL_D)
        c.ellipse(ax + 7, h - 22, 5, 8, (0, 0, 0, 0))
    spire(c, cx + 116, h, 10, 70, P.HM_SIL_D, P.HM_GLASS_D)
    floating_island(c, 266, 52, 26)
    floating_island(c, 34, 68, 20)
    out = W.haze(c, P.HM_SKY_L, 0.2)
    return out


def arch_bay(c: Canvas, x0: float, x1: float, top: float, base: float, kind: str, seed: int) -> None:
    """One bay of the hall between two columns: a pointed arch, and in it a stained-glass window, an opening
    onto the night, a banner, a portrait or a cat statue."""
    mid, w = (x0 + x1) / 2, x1 - x0
    rnd = noise(seed)
    c.poly([(x0, base), (x0, top + 6), (mid, top - 6), (x1, top + 6), (x1, base)], P.HM_STONE_D)   # back wall
    for y in range(int(top + 8), int(base), 6):              # faint courses on it
        c.line((x0, y), (x1, y), P.HM_STONE_DD)
    if kind in ("window", "open"):
        wx0, wx1, wtop, wbot = mid - w * 0.28, mid + w * 0.28, top + 18, base - 26
        shape = [(wx0, wbot), (wx0, wtop + 10), (mid, wtop - 4), (wx1, wtop + 10), (wx1, wbot)]
        c.poly([(x + (1 if x > mid else -1) * 2, y - (2 if y < wtop + 10 else 0)) for x, y in shape], P.HM_STONE)
        if kind == "open":
            c.poly(shape, (0, 0, 0, 0))                       # see through to the night outside
            c.d.polygon([(round(x), round(y)) for x, y in shape], fill=(0, 0, 0, 0))
        else:
            glass = Canvas(*c.size)                           # leaded panes, clipped to the pointed window
            glass.poly(shape, P.HM_GLASS_D)
            for k, gy in enumerate(range(int(wtop - 4), int(wbot), 5)):
                for gx in range(int(wx0) + 1, int(wx1), 4):
                    col = (P.HM_GLASS, P.HM_GLASS_L, P.HM_GLASS_B, P.HM_GLASS)[(gx // 4 + k) % 4]
                    glass.rect(gx, gy + 1, gx + 2, gy + 3, col)
            mask = Canvas(*c.size)
            mask.poly(shape, P.WHITE)
            glass.img.putalpha(mask.img.getchannel("A"))
            c.paste(glass)
            c.line((mid, wtop - 3), (mid, wbot), P.HM_STONE_DD)
            c.ellipse(mid, wtop + 8, 4, 4, P.HM_GLASS_L)     # rose
            c.ellipse(mid, wtop + 8, 2, 2, P.HM_GLASS_B)
        c.rect(wx0 - 3, wbot, wx1 + 3, wbot + 2, P.HM_STONE)  # sill
        c.rect(wx0 - 3, wbot, wx1 + 3, wbot, P.HM_STONE_TOP)
    elif kind == "banner":
        bx0, bx1 = mid - 7, mid + 7
        c.rect(bx0 - 2, top + 14, bx1 + 2, top + 15, P.GOLD_D)          # rod
        c.poly([(bx0, top + 16), (bx1, top + 16), (bx1, base - 34), (mid, base - 28), (bx0, base - 34)], P.HM_CRIMSON)
        c.poly([(bx0, top + 16), (bx0 + 3, top + 16), (bx0 + 3, base - 32), (bx0, base - 34)], P.HM_CRIMSON_D)
        c.line((bx0 + 1, base - 34), (mid, base - 29), P.GOLD_D)
        c.line((mid, base - 29), (bx1 - 1, base - 34), P.GOLD_D)
        cy = top + 34                                         # the cat crest
        c.ellipse(mid, cy, 4, 3.5, P.GOLD)
        c.poly([(mid - 4, cy - 1), (mid - 3, cy - 6), (mid - 1, cy - 3)], P.GOLD)
        c.poly([(mid + 4, cy - 1), (mid + 3, cy - 6), (mid + 1, cy - 3)], P.GOLD)
        c.px(mid - 2, cy, P.HM_CRIMSON_D)
        c.px(mid + 2, cy, P.HM_CRIMSON_D)
    elif kind == "portrait":
        fx0, fx1, fy0, fy1 = mid - 9, mid + 9, top + 26, top + 48
        c.rect(fx0, fy0, fx1, fy1, P.GOLD_D)
        c.rect(fx0 + 1, fy0 + 1, fx1 - 1, fy1 - 1, P.GOLD)
        c.rect(fx0 + 3, fy0 + 3, fx1 - 3, fy1 - 3, P.HM_SIL)
        c.ellipse(mid, fy0 + 12, 4, 4, P.HM_STONE_DD)        # a cat's portrait
        c.poly([(mid - 4, fy0 + 10), (mid - 3, fy0 + 6), (mid - 1, fy0 + 9)], P.HM_STONE_DD)
        c.poly([(mid + 4, fy0 + 10), (mid + 3, fy0 + 6), (mid + 1, fy0 + 9)], P.HM_STONE_DD)
        c.px(mid - 2, fy0 + 12, P.HM_FLAME)
        c.px(mid + 2, fy0 + 12, P.HM_FLAME)
        c.rect(mid - 5, fy1 - 5, mid + 5, fy1 - 3, P.HM_CRIMSON_D)
    elif kind == "statue":
        px, pb = mid, base - 4
        c.rect(px - 8, pb - 14, px + 8, pb, P.HM_STONE)       # pedestal
        c.rect(px - 9, pb - 15, px + 9, pb - 13, P.HM_STONE_L)
        c.rect(px - 8, pb - 14, px - 6, pb, P.HM_STONE_L)
        c.rect(px + 6, pb - 14, px + 8, pb, P.HM_STONE_D)
        sy = pb - 15                                          # a sitting cat, pale marble
        c.ellipse(px, sy - 6, 5, 6, P.HM_STONE)              # a sitting cat in carved stone, gold eyes
        c.ellipse(px - 1, sy - 7, 3.5, 5, P.HM_STONE_L)
        c.ellipse(px + 1, sy - 15, 3.5, 3.2, P.HM_STONE_L)
        c.poly([(px - 2, sy - 17), (px - 2, sy - 21), (px, sy - 18)], P.HM_STONE_L)
        c.poly([(px + 2, sy - 18), (px + 4, sy - 21), (px + 4, sy - 17)], P.HM_STONE)
        c.line((px + 5, sy - 2), (px + 7, sy - 8), P.HM_STONE)
        c.px(px, sy - 15, P.GOLD)
        c.px(px + 2, sy - 15, P.GOLD)
    # the arch over the bay
    c.poly([(x0, top + 14), (mid, top), (x1, top + 14), (x1, top + 6), (mid, top - 6), (x0, top + 6)], P.HM_STONE)
    c.line((x0, top + 6), (mid, top - 6), P.HM_STONE_TOP)
    c.line((mid, top - 6), (x1, top + 6), P.HM_STONE_L)


def column(c: Canvas, x: float, top: float, base: float) -> None:
    c.rect(x - 5, top, x + 5, base, P.HM_STONE)
    c.rect(x - 5, top, x - 3, base, P.HM_STONE_L)
    c.rect(x + 3, top, x + 5, base, P.HM_STONE_D)
    for fx in (x - 1, x + 1):
        c.line((fx, top + 6), (fx, base - 8), P.HM_STONE_D)
    c.poly([(x - 4, top), (x, top - 14), (x + 4, top)], P.HM_STONE)   # pinnacle
    c.line((x, top - 14), (x - 3, top), P.HM_STONE_L)
    c.rect(x - 7, top, x + 7, top + 4, P.HM_STONE_L)           # capital
    c.rect(x - 7, top + 4, x + 7, top + 4, P.HM_STONE_D)
    c.rect(x - 7, base - 6, x + 7, base, P.HM_STONE_L)        # plinth
    c.rect(x - 7, base - 1, x + 7, base, P.HM_STONE_D)


def chandelier(c: Canvas, x: float, top: float, drop: float) -> None:
    c.line((x, top), (x, top + drop), P.GOLD_D)
    y = top + drop
    glow(c, x, y + 4, 18, 9, P.HM_FLAME, 40)                  # warm glow
    c.rect(x - 11, y + 2, x + 11, y + 3, P.GOLD_D)
    c.rect(x - 11, y + 2, x + 11, y + 2, P.GOLD)
    c.poly([(x - 6, y + 4), (x + 6, y + 4), (x, y + 9)], P.GOLD_D)
    for k in range(-2, 3):
        candle(c, x + k * 5, y + 1, 3 + (k % 2), halo=False)


def haunted_near() -> Canvas:
    """The museum hall: columns and pointed arches; bays with stained glass, a window onto the night, a crest
    banner, a gold-framed portrait and a cat statue; chandeliers between."""
    h = 120
    c = Canvas(LAYER_W, h)
    bays = ["window", "banner", "open", "statue", "window", "portrait"]
    xs = [k * LAYER_W / len(bays) for k in range(len(bays) + 1)]
    top = 40
    for k, kind in enumerate(bays):
        arch_bay(c, xs[k], xs[k + 1], top, h - 1, kind, 420 + k)
    for x in xs:
        W.wrapped(lambda px: column(c, px, top - 2, h - 1), x)
    for x, drop in (((xs[1] + xs[2]) / 2, 10), ((xs[4] + xs[5]) / 2, 14)):   # chandeliers hung from the arch keys
        W.wrapped(lambda px, drop=drop: chandelier(c, px, top - 5, drop), x)
    c.rect(0, h - 8, LAYER_W - 1, h - 1, P.HM_STONE_D)        # wainscot
    c.rect(0, h - 8, LAYER_W - 1, h - 8, P.HM_STONE_L)
    return W.haze(c, P.HM_SKY, 0.16)


def iron_fence(c: Canvas, x0: float, x1: float, base: float) -> None:
    c.rect(x0, base - 9, x1, base - 8, P.HM_SIL_D)
    for x in range(int(x0), int(x1) + 1, 3):
        c.line((x, base), (x, base - 12), P.HM_SIL_D)
        c.px(x, base - 13, P.HM_SIL)


def gargoyle(c: Canvas, x: float, base: float) -> None:
    c.rect(x - 5, base - 7, x + 5, base, P.HM_SIL_D)           # pedestal
    c.ellipse(x, base - 12, 5, 5, P.HM_SIL_D)                  # hunched body
    c.ellipse(x + 3, base - 17, 3, 3, P.HM_SIL_D)
    c.poly([(x + 1, base - 19), (x + 2, base - 23), (x + 3, base - 19)], P.HM_SIL_D)
    c.poly([(x + 4, base - 19), (x + 6, base - 23), (x + 6, base - 18)], P.HM_SIL_D)
    c.poly([(x - 3, base - 14), (x - 9, base - 21), (x - 6, base - 12)], P.HM_SIL_D)    # wing


def haunted_bushes() -> Canvas:
    """The front strip: low purple fog over iron fences and gargoyle silhouettes."""
    h = 22
    c = Canvas(LAYER_W, h)
    for x0, x1 in ((6, 70), (120, 170), (214, 290)):
        W.wrapped(lambda px, w=x1 - x0: iron_fence(c, px, px + w, h - 1), x0)
    for x in (92, 196, 306):
        W.wrapped(lambda px: gargoyle(c, px, h - 1), x)
    for x in (46, 180, 262):                                   # a candelabra now and then
        def candelabra(px):
            c.line((px, h - 1), (px, h - 9), P.GOLD_D)
            c.rect(px - 4, h - 9, px + 4, h - 9, P.GOLD_D)
            c.rect(px - 2, h - 1, px + 2, h - 1, P.GOLD_D)
            for dx in (-4, 0, 4):
                candle(c, px + dx, h - 10, 3 + (dx == 0))
        W.wrapped(candelabra, x)
    fog_band(c, h - 7, 4, 431, (P.HM_FOG, P.HM_FOG_D), 150)
    return c


# --- ground --------------------------------------------------------------------------------------------

def courses(c: Canvas, y0: int, count: int, first: int) -> None:
    """6-row brick courses alternating their joints; `first` = parity of the first course."""
    for k in range(count):
        odd = (first + k) % 2
        brick_row(c, y0 + k * 6, 6, [16, 16], 8 if odd else 0, STONE_DARK, 470 + (first + k) % 6, 32)


def haunted_ground(c: Canvas) -> None:
    """A violet stone floor: a lit top edge on a row of big capstones, then brick courses that carry on into the
    earth tile. (The crimson runner is on the terrain blocks, so it shows only now and then.)"""
    c.rect(0, 0, 31, 47, P.HM_STONE_DD)
    brick_row(c, 0, 12, [16, 16], 4, STONE, 461, 32)           # capstones
    c.rect(0, 0, 31, 0, P.HM_STONE_TOP)
    c.rect(0, 1, 31, 1, P.HM_STONE_L)
    for x in (9, 25):                                          # worn spots on the edge
        c.px(x, 1, P.HM_STONE)
    courses(c, 12, 6, 0)


def haunted_earth(c: Canvas) -> None:
    c.rect(0, 0, 31, 35, P.HM_STONE_DD)
    courses(c, 0, 6, 0)                                        # 6 courses: the parity carries on


# --- the ghost-fog pit (the forest waterfall-pit contract) --------------------------------------------

def pit_wall(name: str, offset: int) -> Sprite:
    """8x16 left pit wall: two brick courses ending in an outline on the pit side (col 7)."""
    c = Canvas(8, 16)
    c.rect(0, 0, 6, 15, P.HM_STONE_DD)
    for y0, off in ((0, offset), (8, 4 - offset)):
        brick(c, -8 + off, y0, -1 + off, y0 + 6, STONE_DARK)
        brick(c, off, y0, 6, y0 + 6, STONE)
    c.rect(7, 0, 7, 15, P.HM_SIL_D)
    c.px(6, 3, P.HM_FOG_D)                                     # fog clinging to the edge
    c.px(6, 11, P.HM_FOG_D)
    return single(name, c)


def pit_rim() -> Sprite:
    """12x24 left top cap: the floor's lit edge (row 0 = ground surface) on a capstone over bricks, ending in a
    carved corbel that juts over the pit with a lantern hanging under it."""
    c = Canvas(12, 24)
    c.rect(0, 0, 6, 23, P.HM_STONE_DD)
    brick(c, -4, 0, 8, 11, STONE)
    c.rect(0, 0, 8, 0, P.HM_STONE_TOP)
    c.rect(0, 1, 8, 1, P.HM_STONE_L)
    for y0 in (12, 18):
        brick(c, 0, y0, 6, y0 + 5, STONE_DARK)
    c.rect(7, 8, 7, 23, P.HM_SIL_D)
    c.poly([(8, 2), (11, 2), (11, 4), (9, 8), (8, 8)], P.HM_STONE)   # corbel
    c.line((8, 2), (11, 2), P.HM_STONE_TOP)
    c.px(10, 5, P.HM_STONE_D)
    c.line((10, 5), (10, 13), P.GOLD_D)                        # lantern on a chain
    c.rect(9, 14, 11, 18, P.HM_SIL_D)
    c.rect(10, 15, 10, 17, P.HM_FLAME)
    glow(c, 10, 16, 3.5, 4, P.HM_FLAME, 60)
    c.px(10, 19, P.GOLD_D)
    return single("ravine_haunted_rim", c)


def pit_chain() -> Sprite:
    """6x24, the vines' slot: an iron chain with a candle lantern at its end."""
    c = Canvas(6, 24)
    for y in range(0, 16, 2):
        c.rect(2, y, 3, y, P.GREY_D if (y // 2) % 2 else P.GREY)
        c.px(2 if (y // 2) % 2 else 3, y + 1, P.SLATE)
    glow(c, 2.5, 19, 3, 3.5, P.HM_FLAME, 50)
    c.rect(1, 16, 4, 22, P.HM_SIL_D)
    c.rect(2, 17, 3, 21, P.HM_FLAME)
    c.px(2, 18, P.HM_WAX)
    c.rect(1, 16, 4, 16, P.GOLD_D)
    c.rect(1, 22, 4, 22, P.GOLD_D)
    c.px(2, 23, P.GOLD_D)
    return single("ravine_haunted_vines", c)


def pit_back() -> Sprite:
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 15, P.HM_SIL_D)
    brick_row(c, 0, 8, [16], 0, (P.HM_STONE_D, P.HM_SIL_L, P.HM_SIL), 481, 16)
    brick_row(c, 8, 8, [16], 8, (P.HM_STONE_D, P.HM_SIL_L, P.HM_SIL), 482, 16)
    c.px(5, 4, P.HM_FOG_DD)
    c.px(12, 12, P.HM_FOG_DD)
    return single("ravine_haunted_back", c)


FOG_BASE = [P.HM_FOG, P.HM_FOG_L, P.HM_FOG, P.HM_FOG_D, P.HM_FOG, P.HM_FOG_L, P.HM_FOG_D, P.HM_FOG, P.HM_FOG_L,
            P.HM_FOG, P.HM_FOG_D, P.HM_FOG, P.HM_FOG_L, P.HM_FOG, P.HM_FOG_D, P.HM_FOG]


def fog_stream(width: int, seed: int, base: list) -> list:
    rnd = noise(seed)
    cols = []
    for x in range(width):
        start, length = int(rnd() * 16), 5 + int(rnd() * 7)
        mark = P.HM_FOG_L if base[x] in (P.HM_FOG_D, P.HM_FOG) else P.HM_GLASS_L
        cols.append((base[x], [(start, length, mark)]))
    return cols


def pit_falls() -> list[Sprite]:
    """The fog curtain (16x16, `flow` 4, tiles both ways): soft streaks of purple ghost-fog drifting down 4 px a
    frame, a little see-through; and its 4x16 edge, opaque, its gaps painted in the shaded wall colours."""
    cols = fog_stream(16, 491, FOG_BASE)
    falls = Sprite("ravine_haunted_falls", (16, 16))
    frames = []
    for k in range(4):
        c = Canvas(16, 16)
        for x in range(16):
            for y in range(16):
                v = (y - 4 * k) % 16
                col = colour_at(cols[x], v)
                c.px(x, y, rgba(col, 235 if col != P.HM_FOG_D else 215))
        frames.append(c)
    falls.add("flow", frames, fps=10)

    edge_cols = fog_stream(4, 492, [P.HM_SIL_L, P.HM_FOG_D, P.HM_FOG, P.HM_FOG_L])
    gaps = {0: [(0, 6), (9, 5)], 1: [(4, 3), (12, 2)], 2: [(8, 2)], 3: []}
    edge = Sprite("ravine_haunted_falls_edge", (4, 16))
    frames = []
    for k in range(4):
        c = Canvas(4, 16)
        for x in range(4):
            for y in range(16):
                v = (y - 4 * k) % 16
                col = colour_at(edge_cols[x], v)
                if any((v - s) % 16 < n for s, n in gaps[x]):
                    col = P.HM_SIL_D if x == 0 else P.HM_SIL
                c.px(x, y, col)
        frames.append(c)
    edge.add("flow", frames, fps=10)
    return [falls, edge]


def pit_lip() -> Sprite:
    """16x6: fog rolling over the brink in soft rounded puffs (row 0 = ground surface)."""
    sprite = Sprite("ravine_haunted_lip", (16, 6))
    frames = []
    for k in range(4):
        c = Canvas(16, 6)
        for shift in (-16, 0, 16):
            for px, r in (((2 + 4 * k) % 16, 2.6), ((9 + 4 * k) % 16, 3.2)):
                c.ellipse(px + shift, 3, r, 2.4, P.HM_FOG_L)
                c.ellipse(px + shift - 0.5, 2.5, r - 1, 1.4, P.HM_MOON)
        for x in range(16):
            if not c.img.getpixel((x, 4))[3]:
                c.px(x, 4, P.HM_FOG)
            c.px(x, 5, P.HM_FOG if (x + k) % 3 else P.HM_FOG_L)
        frames.append(c)
    sprite.add("flow", frames, fps=10)
    return sprite


def pit_surface() -> Sprite:
    """16x8 fog-pool surface, `wave` 4: curling swirls of pale fog over violet, drifting 4 px a frame."""
    sprite = Sprite("ravine_haunted_surface", (16, 8))
    frames = []
    for k in range(4):
        c = Canvas(16, 8)
        for x in range(16):
            crest = 2 + round(math.sin((x / 16 + k / 4) * 2 * math.pi) * 0.8)
            c.px(x, crest, P.HM_FOG_L)
            for y in range(crest + 1, 8):
                c.px(x, y, P.HM_FOG if y < 5 else P.HM_FOG_D)
        for shift in (-16, 0, 16):                           # two curls of fog
            for cx0, cy in ((3, 4), (11, 5)):
                cx = cx0 + 4 * k + shift
                for a in range(0, 300, 30):
                    rad = 1 + a / 150
                    ang = math.radians(a)
                    c.px(cx + math.cos(ang) * rad, cy + math.sin(ang) * rad * 0.7, P.HM_FOG_L)
        frames.append(c)
    sprite.add("wave", frames, fps=8)
    return sprite


def pit_pool() -> Sprite:
    """16x24 deep violet glow under the fog, `churn` 4: rising spirit sparks, darkening to the floor's colour."""
    bands = [(0, 4, P.HM_FOG_D, P.HM_FOG_D), (4, 8, P.HM_FOG_D, P.HM_FOG_DD), (8, 14, P.HM_FOG_DD, P.HM_FOG_DD),
             (14, 18, P.HM_FOG_DD, P.HM_SIL_L), (18, 24, P.HM_SIL_L, P.HM_SIL_L)]
    rnd = noise(493)
    sparks = [(int(rnd() * 16), int(rnd() * 16), 1 + int(rnd() * 2)) for _ in range(8)]
    sprite = Sprite("ravine_haunted_pool", (16, 24))
    frames = []
    for k in range(4):
        c = Canvas(16, 24)
        for y0, y1, a, b in bands:
            for y in range(y0, y1):
                for x in range(16):
                    c.px(x, y, b if (x + y) % 2 else a)
        for bx, by, size in sparks:
            y = (by - 2 * k * size) % 16
            if y < 14:
                c.px(bx, y, P.HM_GLASS_L if y < 5 else P.HM_FOG_L if y < 10 else P.HM_FOG)
        frames.append(c)
    sprite.add("churn", frames, fps=8)
    return sprite


def pit_splash() -> Sprite:
    """16x12 billowing fog band where the curtain meets the pool, `splash` 4, with spirit sparks above."""
    sprite = Sprite("ravine_haunted_splash", (16, 12))
    frames = []
    for k in range(4):
        c = Canvas(16, 12)
        c.rect(0, 8, 15, 11, P.HM_FOG_L)
        for x in range(16):
            if (x + k) % 3 == 0:
                c.px(x, 11, P.HM_FOG)
        mounds = [((1 + k) % 16, 4.6 - (k % 2), 3.4), ((8 + 2 * k) % 16, 3.6 + (k % 2), 3.8), ((13 - k) % 16, 5.2, 2.8)]
        for mx, my, rad in mounds:
            for shift in (-16, 0, 16):
                c.ellipse(mx + shift + 0.6, my + 1.2, rad, rad * 0.8, P.HM_FOG)
                c.ellipse(mx + shift, my + 0.6, rad - 0.4, rad * 0.75, P.HM_FOG_L)
                c.px(mx + shift - 1, my - 0.5, P.HM_MOON)
        rnd = noise(494 + k)
        for _ in range(5):
            c.px(int(rnd() * 16), int(rnd() * 3), P.HM_GLASS_L if rnd() > 0.5 else P.HM_FOG_L)
        frames.append(c)
    sprite.add("splash", frames, fps=10)
    return sprite


def pit_floor() -> Sprite:
    """16x16 dark stone floor of the abyss: the pool's last colour with broken flagstones rising into it, then
    bricks like the earth's with a ragged clear bottom."""
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 4, P.HM_SIL_L)
    c.rect(0, 5, 15, 11, P.HM_STONE_DD)
    brick(c, 0, 2, 6, 8, STONE_DARK)
    brick(c, 7, 3, 15, 9, STONE_DARK)
    c.px(2, 2, P.HM_FOG)
    c.px(9, 3, P.HM_FOG)
    for x0, x1, y1 in ((0, 4, 14), (5, 10, 15), (11, 15, 13)):
        brick(c, x0, 10, x1, y1, STONE_DARK)
    return single("ravine_haunted_floor", c)


def pit_fallbacks() -> list[Sprite]:
    fill = Canvas(8, 48)
    for y0, y1, col in ((0, 39, P.HM_SIL), (40, 41, P.HM_FOG_L), (42, 44, P.HM_FOG), (45, 47, P.HM_FOG_D)):
        fill.rect(0, y0, 7, y1, col)
    deep = Canvas(16, 16)
    deep.rect(0, 0, 15, 15, P.HM_FOG_DD)
    for x0, y, n in ((2, 3, 4), (10, 9, 3), (5, 13, 4)):
        deep.rect(x0, y, x0 + n - 1, y, P.HM_FOG_D)
    return [single("ravine_haunted_fill", fill), single("ravine_haunted_deep", deep)]


# --- terrain blocks (the forest terrain contract) ------------------------------------------------------

def terrain_top() -> Sprite:
    """16x16: a lit stone edge (row 0 = walk surface) and a crimson runner with gold trim and tassels, over one
    brick course that starts on a joint at x 0 and ends on a shaded row 15."""
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 15, P.HM_STONE_DD)
    brick_row(c, 7, 10, [7, 9], 0, STONE, 501, 16)
    c.rect(0, 0, 15, 0, P.HM_STONE_TOP)
    c.rect(0, 1, 15, 1, P.HM_STONE_L)
    c.rect(0, 2, 15, 2, P.GOLD_D)
    c.rect(0, 3, 15, 5, P.HM_CRIMSON)
    c.rect(0, 3, 15, 3, P.HM_CRIMSON_L)
    c.rect(0, 6, 15, 6, P.GOLD_D)
    for x in range(0, 16, 4):
        c.poly([(x, 7), (x + 3, 7), (x + 1.5, 9)], P.HM_CRIMSON_D)
        c.px(x + 1, 7, P.HM_CRIMSON)
    return single("terrain_haunted_top", c)


def terrain_end(c: Canvas, y0: int, y1: int) -> None:
    c.rect(4, y0, 7, y1, P.HM_STONE_DD)
    brick(c, 2, y0, 7, y1, STONE)
    c.rect(1, y0, 1, y1, P.HM_SIL_D)


def terrain_edge() -> Sprite:
    """8x16 left end cap: the stone edge and runner ending in a capstone that overhangs by a pixel, with a
    candle stub in its corner dripping wax down the side."""
    c = Canvas(8, 16)
    terrain_end(c, 7, 15)
    c.rect(0, 0, 7, 0, P.HM_STONE_TOP)
    c.rect(0, 1, 7, 1, P.HM_STONE_L)
    c.rect(1, 2, 7, 6, P.HM_STONE)
    c.rect(3, 2, 7, 2, P.GOLD_D)
    c.rect(3, 3, 7, 5, P.HM_CRIMSON)
    c.rect(3, 3, 7, 3, P.HM_CRIMSON_L)
    c.rect(3, 6, 7, 6, P.GOLD_D)
    c.poly([(3, 7), (6, 7), (4.5, 9)], P.HM_CRIMSON_D)
    c.rect(0, 0, 0, 6, P.HM_STONE_L)
    c.px(0, 6, P.HM_STONE_D)
    c.rect(1, 2, 1, 6, P.HM_STONE_D)
    c.rect(1, 2, 2, 2, P.HM_WAX)                                # wax pooled in the corner, running down the side
    c.rect(0, 3, 0, 9, P.HM_WAX)
    c.px(0, 10, P.HM_WAX_D)
    c.px(1, 3, P.HM_WAX_D)
    c.px(2, 1, P.HM_FLAME)                                      # the stub's flame, flush with the edge
    c.px(1, 1, P.HM_FLAME_D)
    return single("terrain_haunted_edge", c)


def terrain_wall() -> Sprite:
    """8x16 left side face: two outlined brick ends with a wax drip."""
    c = Canvas(8, 16)
    terrain_end(c, 0, 7)
    terrain_end(c, 8, 15)
    c.px(0, 0, P.HM_WAX_D)
    c.px(0, 1, P.HM_WAX)
    c.px(4, 11, P.HM_STONE_D)
    return single("terrain_haunted_wall", c)


def terrain_fill() -> Sprite:
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 15, P.HM_STONE_DD)
    brick_row(c, 0, 8, [9, 7], 2, STONE_DARK, 502, 16)
    brick_row(c, 8, 8, [7, 9], 7, STONE_DARK, 503, 16)
    return single("terrain_haunted_fill", c)


def build() -> list[Sprite]:
    return [
        *smooth_sky("haunted", [P.HM_SKY_TOP, P.HM_SKY, P.HM_SKY_L, P.HM_SKY_HAZE]),
        single("bg_haunted_puffs", haunted_puffs()),
        single("bg_haunted_clouds", haunted_clouds()),
        single("bg_haunted_far", haunted_far()),
        single("bg_haunted_near", haunted_near()),
        single("bg_haunted_bushes", haunted_bushes()),
        *ground("haunted", haunted_ground, haunted_earth),
        flat("ground_haunted_fill", P.HM_STONE_DD),
        pit_wall("ravine_haunted", 2), pit_wall("ravine_haunted_b", 0), pit_rim(), pit_chain(), pit_back(),
        *pit_falls(), pit_lip(), pit_surface(), pit_pool(), pit_splash(), pit_floor(), *pit_fallbacks(),
        terrain_top(), terrain_edge(), terrain_wall(), terrain_fill(),
    ]
