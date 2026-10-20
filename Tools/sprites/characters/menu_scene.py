"""The start screen's backdrop as one static picture (docs/concept/Purrfectly Dangerous Pixel Game Screens.png):
a big tree with a red-roofed house and a cat signpost on the left; pines, blue mountains and a river in the
middle; the castle on its cliff with a waterfall, wooden bridges, bushes and flowers on the right.

`menu_scene_portrait` (210x230) and `menu_scene_landscape` (440x150) are opaque and stand on the ground line:
their bottom row sits directly on top of `ground_forest`. Their top rows are `menu_sky`'s bottom colour, so
`menu_sky` (16x64, full-row bands) can fill the screen above. `menu_clouds` drift over the sky and
`menu_waterfall` shimmers in place over the waterfall (offsets in WATERFALL below). Nothing wraps or scrolls,
so no landmark is ever cut by a strip edge."""
from __future__ import annotations

import math

import palette as P
from draw import Canvas, noise
from sprite import Sprite, single
import woodland as W

# The waterfall overlay, and where its top-left corner sits inside each scene (x, y from the top-left).
FALL_W, FALL_H = 12, 44
WATERFALL = {"portrait": (126, 162), "landscape": (286, 78)}

SKY_STOPS = (P.SKY, P.SKY_S1, P.SKY_M, P.SKY_S2, P.SKY_L, P.SKY_S3, P.SKY_HL, P.SKY_S4, P.SKY_HAZE)


def sky_rows(c: Canvas, horizon: int) -> None:
    """Full-row bands from `P.SKY` at the top to haze at `horizon`; never dithered, never stretched."""
    w, h = c.size
    for y in range(h):
        t = min(0.999, y / horizon)
        steps = (0.36, 0.5, 0.6, 0.68, 0.76, 0.83, 0.89, 0.95)   # where each next band starts (share of the way)
        colour = SKY_STOPS[sum(t >= edge for edge in steps)]
        c.rect(0, y, w - 1, y, colour)


def peaks(c: Canvas, base: float, specs: list) -> None:
    """Blue mountains: (x, height, half width) each, lit on the left face, snowy hazed tips."""
    for x, hgt, half in specs:
        top = base - hgt
        c.poly([(x - half, base), (x - half * 0.45, top + hgt * 0.4), (x, top), (x + half * 0.35, top + hgt * 0.3),
                (x + half, base)], P.MOUNT)
        c.poly([(x - half, base), (x - half * 0.45, top + hgt * 0.4), (x, top), (x - half * 0.1, base)], P.MOUNT_L)
        c.poly([(x, top), (x + half * 0.35, top + hgt * 0.3), (x + half, base), (x + half * 0.3, base)], P.MOUNT_D)
        c.poly([(x - half * 0.16, top + hgt * 0.18), (x, top), (x + half * 0.14, top + hgt * 0.16),
                (x, top + hgt * 0.24)], P.SKY_HAZE)


def pine(c: Canvas, x: float, base: float, tall: float, cols=(P.KIT_GREEN_DD, P.KIT_GREEN_D, P.KIT_GREEN)) -> None:
    """A layered pine, lit on the left; outlined by the caller."""
    dark, mid, light = cols
    c.rect(x - 1, base - 5, x + 1, base, P.BARK_D)
    tiers = 4
    for k in range(tiers):
        t = base - 4 - tall + k * tall * 0.22
        half = 3 + k * tall * 0.07
        bottom = t + tall * 0.32
        c.poly([(x - half, bottom), (x, t), (x + half, bottom)], mid)
        c.poly([(x, t), (x + half, bottom), (x + half * 0.2, bottom)], dark)
        c.line((x - half + 1, bottom - 1), (x - 1, t + 2), light)
        c.px(x - half * 0.5, bottom - 1, P.LEAF_Y if k % 2 == 0 else light)


def house(c: Canvas, x: float, base: float, w: int = 22, roof=(P.RED, P.RED_D, P.CAPE_L)) -> None:
    """A little timber house with a red tiled roof, a lit window and a door; `x` is its middle."""
    wl, wr, wt = x - w / 2, x + w / 2, base - w * 0.6
    c.rect(wl, wt, wr, base, P.CASTLE)
    c.rect(wr - w * 0.3, wt, wr, base, P.CASTLE_D)
    c.rect(wl, wt, wl, base, P.PLANK_D)
    c.rect(wr, wt, wr, base, P.PLANK_D)
    c.rect(wl, wt + (base - wt) / 2, wr, wt + (base - wt) / 2, P.PLANK_D)       # beam
    c.rect(wl + 3, wt + 3, wl + 6, wt + 6, P.BARK_DD)                           # window
    c.rect(wl + 4, wt + 4, wl + 5, wt + 5, P.LANTERN)
    c.rect(x + 2, base - 7, x + 5, base, P.BARK_D)                               # door
    c.rect(x + 3, base - 6, x + 4, base, P.BARK)
    c.rect(wr - 5, wt - w * 0.55, wr - 3, wt - 3, P.STONE)                      # chimney
    c.rect(wr - 6, wt - w * 0.55 - 1, wr - 2, wt - w * 0.55, P.STONE_D)
    light, dark, edge = roof[0], roof[1], roof[2]
    apex = wt - w * 0.5
    c.poly([(wl - 3, wt + 1), (x, apex), (wr + 3, wt + 1)], light)
    c.poly([(x, apex), (wr + 3, wt + 1), (x + 1, wt + 1)], dark)
    for k in range(1, 4):                                                       # tile rows
        yy = apex + k * (wt + 1 - apex) / 4
        half = (yy - apex) / (wt + 1 - apex) * (w / 2 + 3)
        c.line((x - half, yy), (x + half, yy), dark)
    c.line((wl - 2, wt), (x - 1, apex + 1), edge)


def walkway(c: Canvas, x0: float, x1: float, deck: float, ground: float, posts: int = 12) -> None:
    """A wooden bridge: plank deck, two rails, posts down to `ground` and cross braces."""
    for k in range(int(x0), int(x1) + 1, posts):
        c.rect(k, deck - 8, k + 1, deck - 1, P.PLANK)
        c.rect(k, deck + 3, k + 1, ground, P.BARK_D)
        c.px(k, deck - 8, P.PLANK_L)
    c.rect(x0, deck, x1, deck + 2, P.PLANK)
    c.rect(x0, deck, x1, deck, P.PLANK_L)
    c.rect(x0, deck + 2, x1, deck + 2, P.PLANK_D)
    for k in range(int(x0), int(x1), 4):
        c.px(k, deck + 1, P.PLANK_D)
    c.rect(x0, deck - 7, x1 + 1, deck - 6, P.PLANK_L)
    c.rect(x0, deck - 4, x1 + 1, deck - 4, P.PLANK)
    for k in range(int(x0) + posts // 2, int(x1), posts):     # rail posts between the piles
        c.rect(k, deck - 8, k, deck - 1, P.PLANK)


def signpost(c: Canvas, x: float, ground: float) -> None:
    """The wooden cat sign (a bigger cousin of `sign_cat`); `x` is the post's middle."""
    top = ground - 46
    c.rect(x - 1.5, top + 8, x + 1.5, ground, P.PLANK_D)
    c.rect(x - 1.5, top + 8, x - 1.5, ground, P.PLANK)
    c.rect(x - 1.5, top - 2, x + 1.5, top, P.PLANK_D)
    pl, pr, pt, pb = x - 12, x + 12, top, top + 18
    c.rect(pl, pt, pr, pb, P.PLANK)
    c.rect(pl, pt, pr, pt, P.PLANK_L)
    c.rect(pl, pt, pl, pb, P.PLANK_L)
    c.rect(pl, pb, pr, pb, P.PLANK_D)
    c.rect(pr, pt + 1, pr, pb, P.PLANK_D)
    c.line((pl + 2, pt + 5), (pl + 6, pt + 5), P.PLANK_D)
    c.line((pr - 6, pt + 13), (pr - 2, pt + 13), P.PLANK_D)
    for nx, ny in ((pl + 1, pt + 1), (pr - 1, pt + 1), (pl + 1, pb - 1), (pr - 1, pb - 1)):
        c.px(nx, ny, P.BARK_DD)
    # a cat face burnt into the board
    c.poly([(x - 7, pt + 9), (x - 6, pt + 3), (x - 2, pt + 6)], P.BARK_D)
    c.poly([(x + 7, pt + 9), (x + 6, pt + 3), (x + 2, pt + 6)], P.BARK_D)
    c.ellipse(x, pt + 10, 6, 4.5, P.BARK_D)
    c.rect(x - 3.5, pt + 9, x - 2.5, pt + 10, P.GOLD)
    c.rect(x + 2.5, pt + 9, x + 3.5, pt + 10, P.GOLD)
    c.px(x, pt + 12, P.PINK_D)


def waterfall_frame(c: Canvas, x: float, y: float, phase: int) -> None:
    """The falling water at (x, y): streaks that run down 2 px per phase (a loop of 4), foam at the foot."""
    c.rect(x + 1, y, x + FALL_W - 2, y + FALL_H - 6, P.WATER)
    c.rect(x + 1, y, x + 2, y + FALL_H - 6, P.WATER_D)
    c.rect(x + FALL_W - 3, y, x + FALL_W - 2, y + FALL_H - 6, P.WATER_D)
    for k, col in enumerate((P.WATER_L, P.WHITE, P.WATER_L, P.CYAN, P.WHITE, P.WATER_L)):
        sx = x + 2 + k * (FALL_W - 4) / 6
        for yy in range(int(FALL_H - 6)):
            if ((yy - phase * 2) + k * 3) % 8 < 5:
                c.px(sx, y + yy, col)
    c.rect(x, y, x + FALL_W - 1, y + 1, P.WATER_L)                         # the lip
    c.rect(x + 1, y, x + FALL_W - 2, y, P.WHITE)
    foot = y + FALL_H - 6
    for k in range(5):                                                        # foam churning at the foot
        fx = x + 1 + k * 2.5 + (phase + k) % 2
        fy = foot + (k + phase) % 3
        c.ellipse(fx, fy + 1, 1.6, 1.4, P.WHITE if (k + phase) % 2 else P.CLOUD_S)
    c.rect(x, foot + 4, x + FALL_W - 1, foot + 5, P.CLOUD_S)
    c.px(x + (phase * 3) % FALL_W, foot + 5, P.WHITE)


def small_castle(c: Canvas, x: float, base: float) -> None:
    """A distant grey stone castle with red cone roofs and flags, about 46 wide and 44 tall; `x` is its middle."""
    c.rect(x - 20, base - 12, x + 20, base, P.CASTLE)
    c.rect(x + 8, base - 12, x + 20, base, P.CASTLE_D)
    for k in range(9):                                       # battlements
        c.rect(x - 20 + k * 5, base - 14, x - 18 + k * 5, base - 12, P.CASTLE)
    c.ellipse(x, base - 3, 3, 4, P.MOUNT_DD)                  # gate
    c.rect(x - 3, base - 3, x + 3, base, P.MOUNT_DD)
    for tx, w, hgt in ((-19, 5, 24), (-9, 6, 32), (1, 7, 40), (11, 6, 30), (20, 5, 22)):
        left, right, top = x + tx - w / 2, x + tx + w / 2, base - hgt
        c.rect(left, top, right, base - 8, P.CASTLE)
        c.rect(left, top, left, base - 8, P.CASTLE_L)
        c.rect(right - w * 0.35, top, right, base - 8, P.CASTLE_D)
        c.poly([(left - 1.5, top), (x + tx, top - w * 1.5), (right + 1.5, top)], P.RED)
        c.poly([(x + tx, top - w * 1.5), (right + 1.5, top), (x + tx + 0.5, top)], P.RED_D)
        c.rect(x + tx - 0.5, top + 3, x + tx + 0.5, top + 5, P.MOUNT_DD)
        if hgt >= 30:
            fy = top - w * 1.5
            c.line((x + tx, fy), (x + tx, fy - 4), P.CASTLE_D)
            c.rect(x + tx + 1, fy - 4, x + tx + 2, fy - 3, P.RED)


def cloud_bank(c: Canvas, specs: list, seed: int) -> None:
    for k, (x, base, w, h) in enumerate(specs):
        W.cumulus(c, x, base, w, h, seed + k)


def outlined(c: Canvas, draw) -> None:
    """Draws one element on its own layer, outlines it in the kit's dark green, lays it on `c`."""
    layer = Canvas(*c.size)
    draw(layer)
    c.paste(layer.outline(P.WOOD_OUT))


def scene(w: int, h: int, L: dict, seed: int) -> Canvas:
    """Composes the start-screen picture from the layout `L` (x/y positions for each landmark)."""
    c = Canvas(w, h)
    sky_rows(c, L["horizon"])
    cloud_bank(c, L["clouds"], seed)

    far = Canvas(w, h)                                               # mountains and the distant forest
    peaks(far, L["mount_base"], L["mountains"])
    rnd = noise(seed + 1)
    band_top = L["band_top"]
    far.rect(0, band_top + 10, w - 1, h - 1, P.DIST_D)
    for i in range(int(w / 11) + 2):
        x = i * 11 + rnd() * 6 - 4
        top = band_top - rnd() * 10
        W.round_tree(far, x, h, top, 16 + rnd() * 8, seed + 10 + i, W.DISTANT, (P.DIST_DD, P.DIST_DD), (3, 6))
    for x, tall in L["far_pines"]:
        pine(far, x, band_top + 16, tall, (P.DIST_DD, P.DIST_D, P.DIST_L))
    c.paste(W.haze(far, P.SKY_HAZE, 0.12))

    # the cliff, the castle on top of it, and the waterfall down its face
    cl, cr, ct, cb = L["cliff"]
    cliff = Canvas(w, h)
    cliff.poly([(cl - 6, cb), (cl, ct + 6), (cl + 6, ct), (cr, ct), (cr, cb)], P.ROCK)
    for k in range(int(cl), int(cr), 6):                                # strata and light ledges
        cliff.line((k, ct + 4), (k - 2 + (k % 3), cb), P.ROCK_D)
        cliff.line((k + 2, ct + 5), (k + 1, ct + 14 + (k * 7) % 12), P.ROCK_L)
    for k in range(3):
        yy = ct + 12 + k * 11
        cliff.line((cl + 2 + k * 3, yy), (cr, yy - 2), P.ROCK_D)
    cliff.rect(cl + 4, ct, cr, ct + 3, P.KIT_GREEN)
    cliff.rect(cl + 4, ct, cr, ct, P.KIT_GREEN_L)
    for k in range(int(cl + 5), int(cr), 3):
        cliff.rect(k, ct + 4, k, ct + 4 + (k * 5) % 4, P.KIT_GREEN_D)
    for k in range(int(cl + 8), int(cr), 9):                       # moss running down the face
        for j in range(4 + (k * 3) % 7):
            cliff.px(k + (j % 2), ct + 5 + j, P.KIT_GREEN_D)
    for k in range(int(cl) - 4, int(cr) + 8, 13):                  # bushes along its foot
        W.canopy(cliff, k, cb - 4, 16, 10, k + 3, W.LEAVES, (3, 5))
    c.paste(W.haze(cliff.outline(P.WOOD_OUT), P.SKY_HAZE, 0.06))
    castle = Canvas(w, h)
    small_castle(castle, L["castle"], ct + 1)
    for tx in L["castle_trees"]:
        W.canopy(castle, tx, ct - 3, 10, 8, int(tx), W.LEAVES, (2, 4))
    c.paste(W.haze(castle.outline(P.MOUNT_DD), P.SKY_HAZE, 0.08))

    # the river, from the waterfall's pool across the middle
    rx0, rx1, ry0, ry1 = L["river"]
    c.rect(rx0, ry0, rx1, ry1, P.WATER)
    c.rect(rx0, ry0, rx1, ry0, P.WATER_L)
    c.rect(rx0, ry1 - 2, rx1, ry1, P.WATER_D)
    for k in range(int((rx1 - rx0) / 5)):
        x, y = rx0 + rnd() * (rx1 - rx0 - 6), ry0 + 2 + rnd() * (ry1 - ry0 - 5)
        c.line((x, y), (x + 2 + rnd() * 4, y), P.WHITE if k % 3 == 0 else P.WATER_L)
    fx, fy = WATERFALL[L["name"]]                                    # (identical to menu_waterfall's frame 0)
    waterfall_frame(c, fx, fy, 0)

    for x, tall in L["pines"]:                                         # green pines in the middle distance
        outlined(c, lambda layer, x=x, tall=tall: pine(layer, x, L["pine_base"], tall))
    for x, top, wd in L["round_trees"]:
        outlined(c, lambda layer, x=x, top=top, wd=wd: W.round_tree(layer, x, L["pine_base"] + 6, top, wd,
                                                                    int(x) + 70, size=(4, 7)))

    # the big tree on the left with the house in its branches
    tx, crown_top, crown_w, crown_h = L["tree"]
    deck = L["deck"]

    def big_tree(layer):
        W.gnarled_tree(layer, tx, h - 1, crown_top, 13, crown_w, crown_h, seed + 30, vines=3)
        layer.rect(tx - 20, deck, tx + 18, deck + 3, P.KIT_GREEN)          # grassy platform
        layer.rect(tx - 20, deck, tx + 18, deck, P.KIT_GREEN_L)
        layer.rect(tx - 20, deck + 3, tx + 18, deck + 4, P.PLANK_D)
        for k in range(int(tx - 19), int(tx + 18), 3):
            layer.px(k, deck + 4 + (k % 2), P.KIT_GREEN_D)
        for px_ in (tx - 16, tx + 14):
            layer.line((px_, deck + 5), (tx + (3 if px_ > tx else -3), deck + 16), P.BARK_D, 2)
        house(layer, L["house"], deck - 1)
    outlined(c, big_tree)

    # the cottage, the walkway and the sign on the left; the bridge on the right
    outlined(c, lambda layer: house(layer, L["cottage"], L["cottage_base"], 16))
    for x0, x1, dk in L["walkways"]:
        outlined(c, lambda layer, x0=x0, x1=x1, dk=dk: walkway(layer, x0, x1, dk, h - 1))
    outlined(c, lambda layer: signpost(layer, L["sign"], h - 1))

    # bushes and flowers along the front, a solid band on the bottom rows to meet the ground's turf
    from characters.screens import flower
    front = Canvas(w, h)
    front.rect(0, h - 5, w - 1, h - 1, P.KIT_GREEN_D)
    rnd = noise(seed + 50)
    for i in range(int(w / 16) + 2):
        x = i * 16 + rnd() * 8 - 4
        if any(lo < x < hi for lo, hi in L["clear"]):
            continue
        bw, bh = 18 + rnd() * 12, 12 + rnd() * 9
        W.canopy(front, x, h - bh / 2 + 1, bw, bh + 2, seed + 60 + i, size=(3, 6))
    outline = front.outline(P.WOOD_OUT)
    c.paste(outline)
    colours = ((P.PINK, P.GOLD), (P.WHITE, P.GOLD), (P.YELLOW, P.ORANGE), (P.BLUE, P.YELLOW), (P.PINK, P.YELLOW))
    for k in range(int(w / 9)):
        x = 4 + rnd() * (w - 8)
        if any(lo < x < hi for lo, hi in L["clear"]):
            continue
        petal, centre = colours[k % len(colours)]
        flower(c, x, h - 4 - rnd() * 9, petal, centre, P.CREAM_D)
    c.rect(0, h - 2, w - 1, h - 1, P.KIT_GREEN_DD)                      # under the ground tile's turf
    return c


# Landmarks keep inside the middle of each picture (x 7-202 of the portrait's 210, x 54-386 of the landscape's
# 440), so whichever screen width shows only part of it, nothing is cut; the sides are forest, cliff and river.
PORTRAIT = dict(
    name="portrait", horizon=180,
    clouds=[(77, 128, 70, 30), (157, 118, 80, 34), (31, 112, 44, 18), (196, 98, 30, 14), (117, 70, 34, 13)],
    mount_base=176, mountains=[(71, 34, 34), (107, 40, 36), (139, 26, 26)], band_top=170,
    far_pines=[(59, 26), (95, 22), (4, 24)],
    cliff=(111, 210, 160, 204), castle=161, castle_trees=(143, 191),
    river=(71, 192, 196, 212), pines=[(63, 44), (85, 36), (196, 52)], pine_base=212,
    round_trees=[(183, 176, 26)],
    tree=(33, 40, 50, 46), deck=118, house=33,
    cottage=60, cottage_base=196, walkways=[(52, 92, 198), (141, 210, 196)], sign=31,
    clear=[],
)

LANDSCAPE = dict(
    name="landscape", horizon=112,
    clouds=[(170, 62, 70, 28), (260, 56, 80, 32), (350, 50, 70, 30), (90, 40, 40, 16), (230, 24, 36, 13),
            (20, 70, 50, 20), (420, 66, 50, 20)],
    mount_base=106, mountains=[(170, 30, 36), (210, 38, 40), (254, 28, 30), (290, 22, 26)], band_top=94,
    far_pines=[(150, 22), (200, 20), (274, 18), (14, 22), (40, 20), (420, 22)],
    cliff=(276, 440, 76, 122), castle=334, castle_trees=(312, 368),
    river=(200, 440, 114, 132), pines=[(146, 40), (168, 34), (190, 28), (376, 42), (16, 38), (36, 30), (426, 36)],
    pine_base=132,
    round_trees=[(256, 96, 26), (366, 100, 24), (6, 98, 24), (430, 100, 22)],
    tree=(84, 4, 56, 42), deck=72, house=84,
    cottage=120, cottage_base=120, walkways=[(106, 154, 126), (312, 440, 116)], sign=86,
    clear=[],
)


def menu_sky() -> Sprite:
    """16x64 sky for the top of the screen: four full-row bands ending in the scenes' top colour."""
    c = Canvas(16, 64)
    for k, colour in enumerate((P.SKY_T2, P.SKY_T3, P.SKY, P.SKY)):
        c.rect(0, k * 16, 15, k * 16 + 15, colour)
    return single("menu_sky", c)


def menu_clouds() -> Sprite:
    """A puffy cumulus to drift over the sky: overlapping round puffs, white on top, blue-shaded underneath,
    transparent all round with no straight edges."""
    w, h = 120, 40
    c = Canvas(w, h)
    balls = [(16, 27, 9), (30, 21, 12), (48, 15, 14), (66, 18, 13), (82, 22, 11), (97, 26, 9), (108, 29, 6),
             (40, 28, 9), (60, 29, 10), (78, 29, 9), (24, 31, 6), (92, 31, 6)]
    for x, y, rad in balls:
        c.ellipse(x, y + 1.5, rad, rad * 0.8, P.CLOUD_D)
    for x, y, rad in balls:
        c.ellipse(x - 0.5, y, rad - 0.5, rad * 0.8 - 0.5, P.CLOUD_S)
    for x, y, rad in balls:
        c.ellipse(x - rad * 0.2, y - rad * 0.25, rad * 0.75, rad * 0.6, P.WHITE)
    return single("menu_clouds", c)


def menu_waterfall() -> Sprite:
    sprite = Sprite("menu_waterfall", (FALL_W, FALL_H))
    frames = []
    for phase in range(4):
        c = Canvas(FALL_W, FALL_H)
        waterfall_frame(c, 0, 0, phase)
        frames.append(c)
    sprite.add("loop", frames, fps=8)
    return sprite


def build() -> list[Sprite]:
    return [
        single("menu_scene_portrait", scene(210, 230, PORTRAIT, 700)),
        single("menu_scene_landscape", scene(440, 150, LANDSCAPE, 800)),
        menu_sky(),
        menu_clouds(),
        menu_waterfall(),
    ]
