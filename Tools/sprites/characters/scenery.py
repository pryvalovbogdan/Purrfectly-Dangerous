"""Backdrops and ground tiles for the four worlds and the start screen.

Per theme: `bg_<theme>_sky` (a 200-tall gradient stretched across the screen, standing on the ground
line) and `bg_<theme>_sky_top` (its top colour, for any sky above it); `puffs`, `clouds`, `far`,
`near` and `bushes` strips, 320 wide and tiling horizontally, back to front; `ground_<theme>` (a
32x48 tile), `ground_<theme>_earth` (its lower part on its own) and `ground_<theme>_fill`; and
`ravine_<theme>` (the left wall of a pit, mirrored for the right), `ravine_<theme>_fill` (stretched
between the walls) and `ravine_<theme>_deep` (below that)."""
from __future__ import annotations

import math

import palette as P
from draw import Canvas, noise
from sprite import Sprite, single
import woodland as W

LAYER_W = 320
EARTH_TOP = 12


def wrapped(draw, x: float) -> None:
    """Calls `draw(x)` at x and one layer-width either side, so shapes crossing an edge tile seamlessly."""
    for offset in (-LAYER_W, 0, LAYER_W):
        draw(x + offset)


def flat(name: str, colour) -> Sprite:
    """One plain colour, for the game to stretch over an area."""
    c = Canvas(8, 8)
    c.rect(0, 0, 7, 7, colour)
    return single(name, c)


def sky(theme: str, stops: list) -> list[Sprite]:
    """Top-to-bottom gradient over 200 rows, dithered where one colour meets the next."""
    c = Canvas(16, 200)
    step = 200 / len(stops)
    for i, colour in enumerate(stops):
        c.rect(0, i * step, 15, (i + 1) * step, colour)
        if i:
            for y in range(int(i * step) - 3, int(i * step) + 3):
                for x in range(16):
                    if (x + y) % 2 == 0 and y < i * step:
                        c.px(x, y, colour)
                    elif (x + y) % 2 == 0 and y >= i * step and (x + y) % 4 == 0:
                        c.px(x, y, stops[i - 1])
    return [single(f"bg_{theme}_sky", c), flat(f"bg_{theme}_sky_top", stops[0])]


def smooth_sky(theme: str, stops: list, blend: int = 16) -> list[Sprite]:
    """Like `sky`, but each stop fades into the next over `blend` rows. The texture is stretched across
    the screen, so the blend is made of whole rows (thin lines of the next colour that thicken), never
    a checkerboard, which the stretch would smear into streaks."""
    c = Canvas(16, 200)
    step = 200 / len(stops)
    order = (0, 2, 1, 3)
    for y in range(200):
        i = min(int(y / step), len(stops) - 1)
        colour = stops[i]
        edge = (i + 1) * step
        if i + 1 < len(stops) and y > edge - blend / 2:
            t = (y - (edge - blend / 2)) / blend + 0.0
            colour = stops[i + 1] if order[y % 4] < t * 4 else colour
        elif i > 0 and y < i * step + blend / 2:
            t = 0.5 + (y - i * step) / blend
            colour = colour if order[y % 4] < t * 4 else stops[i - 1]
        c.rect(0, y, 15, y, colour)
    return [single(f"bg_{theme}_sky", c), flat(f"bg_{theme}_sky_top", stops[0])]


def puffs(theme: str, seed: int, colour, shade, moon=None) -> Sprite:
    """Small clouds on their own, for open sky above the horizon (and the moon, at night)."""
    height = 120
    c = Canvas(LAYER_W, height)
    rnd = noise(seed)
    if moon:
        c.ellipse(230, 40, 16, 16, moon[0])
        c.ellipse(225, 36, 4, 3, moon[1])
        c.ellipse(237, 47, 3, 2.5, moon[1])
        c.ellipse(236, 31, 2, 2, moon[1])
    for i in range(5):
        x = i * LAYER_W / 5 + rnd() * 30
        y = 24 + rnd() * (height - 44)
        w = 13 + rnd() * 11

        def one(px, y=y, w=w):
            c.ellipse(px, y + 1, w, w * 0.32, shade)
            c.ellipse(px, y, w, w * 0.32, colour)
            c.ellipse(px - w * 0.35, y - w * 0.22, w * 0.42, w * 0.36, colour)
            c.ellipse(px + w * 0.2, y - w * 0.32, w * 0.5, w * 0.46, colour)
        wrapped(one, x)
    return single(f"bg_{theme}_puffs", c)


def clouds(theme: str, height: int, seed: int, colour, shade) -> Sprite:
    """A bank of cloud: puffs along the top, solid below, so it can stand on the horizon."""
    c = Canvas(LAYER_W, height)
    rnd = noise(seed)
    top = height * 0.45
    c.rect(0, top + 6, LAYER_W - 1, height - 1, shade)
    for i in range(13):
        x = i * LAYER_W / 13 + rnd() * 10
        radius = 12 + rnd() * 14
        y = top + rnd() * 8

        def one(px, y=y, radius=radius):
            c.ellipse(px, y, radius, radius * 0.8, colour)
            c.ellipse(px + radius * 0.2, y + radius * 0.5, radius * 0.9, radius * 0.5, shade)
        wrapped(one, x)
    return single(f"bg_{theme}_clouds", c)


def castle(c: Canvas, x: float, base: float, s: float, colour, light=None, window=None, roof=None) -> None:
    """A distant castle silhouette, `s` scales it (1 = about 60 wide, 70 tall)."""
    c.rect(x - 22 * s, base - 30 * s, x + 22 * s, base, colour)
    for tx, w, h in ((-24, 7, 46), (-8, 8, 62), (10, 7, 52), (24, 6, 40)):
        left, right, top = x + (tx - w / 2) * s, x + (tx + w / 2) * s, base - h * s
        c.rect(left, top, right, base, colour)
        c.poly([(left - 1.5 * s, top), (x + tx * s, top - 12 * s), (right + 1.5 * s, top)], roof or colour)
        if light:
            c.rect(left, top, left + max(1, w * s * 0.25), base, light)
        if window:
            c.rect(x + tx * s - 0.5, top + 8 * s, x + tx * s + 0.5, top + 11 * s, window)
    for k in range(9):                                       # battlements
        c.rect(x - 22 * s + k * 5 * s, base - 33 * s, x - 20 * s + k * 5 * s, base - 30 * s, colour)
    if window:
        c.rect(x - 3 * s, base - 12 * s, x + 3 * s, base, window)


def hills(c: Canvas, height: int, seed: int, count: int, tall: tuple, colour, cap=None, light=None) -> None:
    rnd = noise(seed)
    for i in range(count):
        x = i * LAYER_W / count + rnd() * 20
        h = tall[0] + rnd() * (tall[1] - tall[0])
        w = h * (1.1 + rnd() * 0.6)

        def one(px, h=h, w=w):
            c.poly([(px - w, height), (px, height - h), (px + w, height)], colour)
            if light:
                c.poly([(px, height - h), (px + w * 0.15, height - h * 0.6), (px + w, height)], light)
            if cap:
                c.poly([(px - w * 0.28, height - h * 0.72), (px, height - h), (px + w * 0.28, height - h * 0.72),
                        (px + w * 0.1, height - h * 0.64), (px - w * 0.05, height - h * 0.7),
                        (px - w * 0.15, height - h * 0.62)], cap)
        wrapped(one, x)


def round_trees(theme: str, layer: str, height: int, seed: int, count: int, trunk, leaf, leaf_l, leaf_d,
                extra=None) -> Sprite:
    """Big leafy trees with clustered round canopies (the forest)."""
    c = Canvas(LAYER_W, height)
    rnd = noise(seed)
    for i in range(count):
        x = i * LAYER_W / count + rnd() * 16
        h = height * (0.6 + rnd() * 0.35)
        spread = 16 + rnd() * 10
        blobs = [(rnd() - 0.5, rnd(), 0.5 + rnd() * 0.4) for _ in range(6)]

        def one(px, h=h, spread=spread, blobs=blobs):
            top = height - h
            c.rect(px - 3, top + spread * 0.6, px + 3, height, trunk)
            c.poly([(px - 7, height), (px - 3, height - 8), (px + 3, height - 8), (px + 7, height)], trunk)
            c.line((px - 1, top + spread), (px - 1, height - 4), leaf_d)
            for dx, dy, rad in blobs:
                c.ellipse(px + dx * spread * 1.6, top + spread * 0.5 + dy * spread * 0.5, spread * rad,
                          spread * rad * 0.85, leaf_d)
            for dx, dy, rad in blobs:
                c.ellipse(px + dx * spread * 1.6 - 1, top + spread * 0.45 + dy * spread * 0.5 - 1,
                          spread * rad * 0.8, spread * rad * 0.7, leaf)
            for dx, dy, rad in blobs[:3]:
                c.ellipse(px + dx * spread * 1.6 - spread * rad * 0.3, top + spread * 0.3 + dy * spread * 0.45,
                          spread * rad * 0.35, spread * rad * 0.25, leaf_l)
        wrapped(one, x)
    if extra:
        extra(c)
    return single(f"bg_{theme}_{layer}", c)


def pines(theme: str, layer: str, height: int, seed: int, count: int, leaf, leaf_l, snow, trunk) -> Sprite:
    c = Canvas(LAYER_W, height)
    rnd = noise(seed)
    for i in range(count):
        x = i * LAYER_W / count + rnd() * 14
        h = height * (0.5 + rnd() * 0.45)
        spread = 9 + rnd() * 6

        def one(px, h=h, spread=spread):
            c.rect(px - 1.5, height - 8, px + 1.5, height, trunk)
            for k in range(4):
                top = height - h + k * h * 0.2
                w = spread * (0.5 + k * 0.22)
                c.poly([(px - w, top + h * 0.28), (px, top), (px + w, top + h * 0.28)], leaf)
                c.poly([(px, top), (px + w, top + h * 0.28), (px + w * 0.3, top + h * 0.28)], leaf_l)
                c.poly([(px - w * 0.55, top + h * 0.17), (px, top), (px + w * 0.55, top + h * 0.17),
                        (px + w * 0.2, top + h * 0.12), (px - w * 0.2, top + h * 0.14)], snow)
        wrapped(one, x)
    return single(f"bg_{theme}_{layer}", c)


def dead_trees(c: Canvas, height: int, seed: int, count: int, colour) -> None:
    rnd = noise(seed)
    for i in range(count):
        x = i * LAYER_W / count + rnd() * 30
        h = height * (0.45 + rnd() * 0.4)
        lean = (rnd() - 0.5) * 10
        branches = [(0.35 + rnd() * 0.5, (rnd() - 0.5) * 2, 8 + rnd() * 14) for _ in range(5)]

        def one(px, h=h, lean=lean, branches=branches):
            c.poly([(px - 4, height), (px + lean - 1, height - h), (px + lean + 1, height - h), (px + 4, height)],
                   colour)
            for t, side, length in branches:
                bx, by = px + lean * t, height - h * t
                ex, ey = bx + math.copysign(length, side), by - length * 0.6
                c.line((bx, by), (ex, ey), colour, 2)
                c.line((ex, ey), (ex + math.copysign(3, side), ey - 4), colour)
        wrapped(one, x)


def towers(c: Canvas, height: int, seed: int, count: int, colour, light, window, chains=None) -> None:
    rnd = noise(seed)
    for i in range(count):
        x = i * LAYER_W / count + rnd() * 16
        h = height * (0.3 + rnd() * 0.35)
        w = 8 + rnd() * 8
        lit = [rnd() > 0.45 for _ in range(8)]

        def one(px, h=h, w=w, lit=lit):
            c.rect(px - w, height - h, px + w, height, colour)
            c.rect(px - w, height - h, px - w + 2, height, light)
            for k in range(int(w * 2 / 4) + 1):                    # battlements
                c.rect(px - w + k * 4, height - h - 3, px - w + k * 4 + 1.5, height - h, colour)
            for row in range(int(h // 16)):
                if lit[row % 8]:
                    c.rect(px - 1, height - h + 8 + row * 16, px + 1, height - h + 12 + row * 16, window)
        wrapped(one, x)
    if chains:
        for k in range(4):
            x0 = k * 80 + 20
            for j in range(20):
                t = j / 19
                c.px(x0 + t * 40, height * 0.25 + math.sin(t * math.pi) * 14, chains)


def bushes(theme: str, height: int, seed: int, leaf, leaf_light, deco=None) -> Sprite:
    c = Canvas(LAYER_W, height)
    rnd = noise(seed)
    c.rect(0, height * 0.7, LAYER_W - 1, height - 1, leaf)
    for i in range(20):
        x = i * LAYER_W / 20 + rnd() * 8
        radius = height * (0.27 + rnd() * 0.23)
        y = height - radius * 0.6

        def one(px, y=y, radius=radius):
            c.ellipse(px, y, radius, radius, leaf)
            c.ellipse(px - radius * 0.25, y - radius * 0.35, radius * 0.45, radius * 0.35, leaf_light)
        wrapped(one, x)
    if deco:
        deco(c, rnd)
    return single(f"bg_{theme}_bushes", c)


# --- ground ----------------------------------------------------------------------------------------

def ground(theme: str, draw, draw_earth=None) -> list[Sprite]:
    """The 32x48 ground tile, and its lower part as a tile of its own for stacking underneath where the
    earth runs deeper than one tile. The game never cuts pieces out of a texture itself: on a device the
    atlas packs textures together and a cut-out shows its neighbours. `draw_earth`, if given, draws that
    32x36 tile itself (it must tile vertically and continue from the ground tile's bottom row)."""
    c = Canvas(32, 48)
    draw(c)
    earth = Canvas(32, 48 - EARTH_TOP)
    if draw_earth:
        draw_earth(earth)
    else:
        earth.paste(c.img.crop((0, EARTH_TOP, 32, 48)))
    return [single(f"ground_{theme}", c), single(f"ground_{theme}_earth", earth)]


# Deep forest earth: rows of grey cobbles, 6 high, whose pattern repeats every 6 rows (36 = the earth tile),
# so the ground tile's last rows lead straight into the stacked earth tiles below it.
STONE_ROWS = [(0, [11, 10, 11]), (5, [9, 12, 11]), (2, [12, 10, 10]), (7, [10, 11, 11]), (3, [11, 11, 10]),
              (8, [12, 9, 11])]
STONES = (P.STONE, P.STONE_D, P.STONE_DD)


def forest_stones(c: Canvas, y0: int, first: int, rows: int) -> None:
    c.rect(0, y0, 31, y0 + rows * 6 - 1, P.EARTH_DD)
    for k in range(rows):
        offset, widths = STONE_ROWS[(first + k) % 6]
        W.cobble_row(c, y0 + k * 6, 7, widths, offset, STONES, 70 + (first + k) % 6,
                     specks=(P.STONE_D, P.KIT_GREEN_D, P.GOLD_D))


def forest_ground(c: Canvas) -> None:
    """The kit's grass tile: thick turf with hanging tufts over big brown cobbles, then grey cobbles."""
    c.rect(0, 0, 31, 47, P.EARTH_DD)
    for y0, offset, widths, seed in ((9, 0, [11, 10, 11], 3), (19, 6, [10, 12, 10], 4)):
        W.cobble_row(c, y0, 11, widths, offset, (P.EARTH_L, P.EARTH, P.EARTH_D), seed,
                     specks=(P.EARTH_D, P.GOLD_D, P.KIT_GREEN_D))
    forest_stones(c, 30, 1, 3)
    for x in (4, 19, 27):                                    # earth crumbs where brown meets grey
        c.px(x, 30, P.EARTH_D)
        c.px(x + 1, 31, P.EARTH)
    W.grass_top(c, 32, 1)


def forest_earth(c: Canvas) -> None:
    forest_stones(c, 0, 4, 6)  # continues the ground tile's rows 1, 2, 3


def citadel_ground(c: Canvas) -> None:
    c.rect(0, 0, 31, 47, P.IRON_D)
    for y in range(8, 48, 8):                                # basalt bricks
        c.line((0, y), (31, y), P.NIGHT)
        off = 4 if (y // 8) % 2 else 12
        for x in range(off, 32, 16):
            c.line((x, y), (x, y + 7), P.NIGHT)
    for x, y in ((9, 19), (25, 36)):                         # glowing cracks in some bricks
        c.px(x, y, P.RED)
        c.px(x + 1, y + 1, P.LAVA)
        c.px(x + 1, y + 2, P.RED)
        c.px(x + 3, y + 1, P.RED)
    c.rect(0, 0, 31, 4, P.IRON)
    c.rect(0, 0, 31, 0, P.IRON_L)
    for x in (4, 20):
        c.rect(x, 1, x + 8, 3, P.IRON_L if x == 4 else P.IRON)
        c.px(x + 1, 2, P.IRON_D)
    c.rect(0, 5, 31, 5, P.MAROON)


def ravine(theme: str, top, top_light, rock, rock_dark, seed: int) -> Sprite:
    """Left wall of a ravine, as tall as the ground tile; the game mirrors it for the right wall."""
    c = Canvas(8, 48)
    rnd = noise(seed)
    for y in range(5, 48):
        reach = 1 + int(rnd() * 3) if y < 30 else int(rnd() * 2)
        c.rect(0, y, reach, y, rock if y < 18 else rock_dark)
        if y < 18:
            c.px(reach, y, rock_dark)
    for y, reach in enumerate((5, 5, 4, 3, 2)):
        c.rect(0, y, reach, y, top)
    c.rect(0, 0, 4, 0, top_light)
    return single(f"ravine_{theme}", c)


def ravine_fill(theme: str, upper, lower, lava: bool = False) -> Sprite:
    """The pit between the walls: horizontal bands only, so the game can stretch it to any width."""
    c = Canvas(8, 48)
    c.rect(0, 0, 7, 47, lower)
    c.rect(0, 0, 7, 15, upper)
    if lava:                                                 # a lava pool a little way down
        c.rect(0, 0, 7, 13, P.MAROON)
        c.rect(0, 14, 7, 47, P.RED)
        c.rect(0, 14, 7, 15, P.LAVA_L)
        c.rect(0, 16, 7, 20, P.LAVA)
        c.rect(0, 30, 7, 47, P.RED_D)
    return single(f"ravine_{theme}_fill", c)


# --- themes -----------------------------------------------------------------------------------------

def forest_clouds(name: str, height: int, clouds: list) -> Sprite:
    """Puffy cumulus: (x, base, width, height) each, white tops with blue undersides."""
    c = Canvas(LAYER_W, height)
    for k, (x, base, w, h) in enumerate(clouds):
        layer = Canvas(LAYER_W, height)
        W.wrapped(lambda px, base=base, w=w, h=h, k=k: W.cumulus(layer, px, base, w, h, 90 + k), x)
        c.paste(layer)
    return single(name, c)


def ramp_sky(theme: str, ramp: list) -> list[Sprite]:
    """A 200-row sky in plain full-row bands of a fine colour ramp, top to bottom. Neighbouring bands differ
    by only a few levels, so the blend reads as smooth: no dithered rows, which show up as hard stripes
    once the 16-wide texture is stretched across the screen. The top colour continues as `_sky_top`."""
    c = Canvas(16, 200)
    for y in range(200):
        c.rect(0, y, 15, y, ramp[min(len(ramp) - 1, y * len(ramp) // 200)])
    return [single(f"bg_{theme}_sky", c), flat(f"bg_{theme}_sky_top", ramp[0])]


def forest_far() -> Canvas:
    """Blue mountains, and the white hilltop castle on a rocky cliff with a waterfall in two drops. The
    castle (flags included) stays inside rows 2-41; the cliff runs to the bottom of the layer."""
    h = 110
    c = Canvas(LAYER_W, h)
    W.mountains(c, h, 4, 6, (70, 104), (P.MOUNT_L, P.MOUNT_L, P.MOUNT), tips=P.SKY_HAZE)
    W.mountains(c, h, 5, 5, (40, 72), (P.MOUNT_L, P.MOUNT, P.MOUNT_D), tips=P.MOUNT_L)
    top, left, right = 40, 188, 310
    falls = (282, 289)
    W.rock_cliff(c, left, right, top, 17, notch=falls)
    W.rim_bushes(c, [(198, 7), (207, 5), (274, 5), (300, 7)], top - 1, 140)
    W.hill_castle(c, 240, top + 1)
    W.cascade(c, falls[0], top, 64, falls[1] - falls[0] + 1, 1)
    ledge = Canvas(LAYER_W, h)                               # the ledge the first drop lands on
    ledge.rect(274, 65, 298, 68, P.CLIFF)
    ledge.rect(274, 65, 298, 65, P.FAR_GRASS)
    ledge.rect(274, 68, 298, 68, P.CLIFF_D)
    W.outline_wrapped(ledge, P.CLIFF_DD, wrap=False)
    c.paste(ledge)
    W.cascade(c, falls[0] + 2, 69, h - 3, 8, 4)
    W.cascade(c, falls[0], top, 64, falls[1] - falls[0] + 1, 1)  # redrawn so its foam sits over the ledge
    return W.haze(c, P.SKY_HAZE, 0.1)


def forest_near() -> Canvas:
    """A band of distant blue-green trees, then big gnarled trees with vines, a lantern, a log cabin with
    a fence and a lamp post: the busiest layer, but behind the play, so slightly hazed."""
    h = 150
    c = Canvas(LAYER_W, h)
    band = Canvas(LAYER_W, h)                               # distant forest
    rnd = noise(40)
    band.rect(0, h - 30, LAYER_W - 1, h - 1, P.DIST_D)       # solid below the crowns: no far-layer flecks
    for i in range(16):
        x = i * LAYER_W / 16 + rnd() * 10
        top = h - 36 - rnd() * 16
        w = 18 + rnd() * 10
        W.wrapped(lambda px, top=top, w=w, i=i: W.round_tree(band, px, h, top, w, 40 + i, W.DISTANT,
                                                              (P.DIST_DD, P.DIST_DD), (4, 7)), x)
    c.paste(band)

    def mid_tree(layer, px, k):
        W.round_tree(layer, px, h, h - 74 - k * 6, 34, 50 + k, size=(5, 8))

    for k, x in enumerate((186, 296)):
        W.piece(c, lambda layer, px, k=k: mid_tree(layer, px, k), x)
    W.piece(c, lambda layer, px: W.gnarled_tree(layer, px, h - 1, 4, 16, 96, 60, 61, vines=5), 52)
    W.piece(c, lambda layer, px: W.gnarled_tree(layer, px, h - 1, 14, 14, 78, 52, 77, vines=4, lantern=True),
            228)

    def homestead(layer, px):
        W.cabin(layer, px, h - 1)
        W.fence(layer, px + 24, px + 54, h - 1)
        W.lamp_post(layer, px - 26, h - 1)

    W.piece(c, homestead, 140)
    return W.haze(c, P.SKY_L, 0.08)


def forest_bushes() -> Canvas:
    """Low leafy bushes, flowers and red toadstools along the path; kept under about 16 px."""
    h = 24
    c = Canvas(LAYER_W, h)
    rnd = noise(22)
    for i in range(11):
        x = i * LAYER_W / 11 + rnd() * 12
        w = 14 + rnd() * 14
        tall = 9 + rnd() * 5

        def bush(layer, px, w=w, tall=tall, i=i):
            W.canopy(layer, px, h - tall / 2 + 1, w, tall + 2, 200 + i, size=(3, 5))
        W.piece(c, bush, x)
    for k in range(14):                                      # flowers on short stems
        x = rnd() * LAYER_W
        stem = 5 + rnd() * 6
        col = (P.PINK, P.WHITE, P.YELLOW, P.PINK, P.WHITE)[k % 5]

        def flower(layer, px, stem=stem, col=col):
            layer.line((px, h - 1), (px, h - stem), P.KIT_GREEN_D)
            layer.px(px - 1, h - 3, P.KIT_GREEN)
            layer.px(px + 1, h - 4, P.KIT_GREEN_L)
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                layer.px(px + dx, h - stem - 1 + dy, col)
            layer.px(px, h - stem - 1, P.GOLD if col != P.YELLOW else P.ORANGE)
        W.piece(c, flower, x)
    for k in range(5):                                       # red toadstools with white spots
        x = 30 + k * 64 + rnd() * 20
        big = 1 + (k % 2)

        def toadstool(layer, px, big=big):
            layer.rect(px - big, h - 4 - big, px + big - 1, h - 1, P.CREAM)
            layer.ellipse(px - 0.5, h - 5 - big * 1.5, 2 + big * 1.4, 1.2 + big, P.RED)
            layer.rect(px - 1 - big, h - 4 - big, px + big, h - 4 - big, P.RED_D)
            layer.px(px - big, h - 6 - big * 1.5, P.WHITE)
            layer.px(px + big, h - 5 - big, P.WHITE)
        W.piece(c, toadstool, x)
    return W.haze(c, P.SKY_L, 0.04)


def forest_ravine() -> list[Sprite]:
    """`ravine_forest_fill`, still required for every ravine level (the waterfall pit pieces, including the
    wall and deep water, are in characters/waterfall.py): far wall in shade, then the pool, then deep water."""
    fill = Canvas(8, 48)
    for y0, y1, col in ((0, 39, P.CLIFF_BACK), (40, 40, P.WHITE), (41, 41, P.WATER_L), (42, 44, P.WATER),
                        (45, 46, P.WATER_D), (47, 47, P.WATER_DD)):
        fill.rect(0, y0, 7, y1, col)
    return [single("ravine_forest_fill", fill)]


def forest() -> list[Sprite]:
    return [
        *ramp_sky("forest", P.SKY_RAMP),
        forest_clouds("bg_forest_puffs", 120, [(30, 50, 34, 16), (110, 90, 26, 12), (176, 40, 40, 18),
                                               (250, 80, 30, 14), (300, 30, 22, 10)]),
        forest_clouds("bg_forest_clouds", 150, [(20, 70, 62, 30), (92, 40, 40, 20), (150, 84, 74, 34),
                                                (222, 34, 46, 22), (282, 74, 56, 28), (120, 104, 36, 14)]),
        single("bg_forest_far", forest_far()),
        single("bg_forest_near", forest_near()),
        single("bg_forest_bushes", forest_bushes()),
        *ground("forest", forest_ground, forest_earth),
        flat("ground_forest_fill", P.EARTH_DD),
        *forest_ravine(),
    ]


def citadel() -> list[Sprite]:
    far_layer = Canvas(LAYER_W, 150)
    hills(far_layer, 150, 10, 4, (50, 90), P.MAROON)
    castle(far_layer, 150, 150, 1.5, P.NIGHT, P.MAROON, P.LAVA, P.NIGHT)
    for x in (60, 262):                                      # lava pouring from the rock
        top = 150 - 70
        far_layer.ellipse(x + 3, top, 5, 3, P.LAVA)
        far_layer.rect(x, top, x + 6, 149, P.LAVA)
        far_layer.rect(x + 2, top, x + 3, 149, P.LAVA_L)
        far_layer.ellipse(x + 3, 148, 9, 3, P.LAVA_L)

    near_layer = Canvas(LAYER_W, 150)
    towers(near_layer, 150, 11, 4, P.IRON_D, P.IRON, P.LAVA)

    def rubble(c, rnd):
        for k in range(14):
            x = rnd() * LAYER_W
            c.px(x, 16 + rnd() * 6, P.LAVA if k % 3 else P.LAVA_L)

    return [
        *sky("citadel", [P.NIGHT, P.MAROON, P.RED_D, P.RED]),
        puffs("citadel", 30, P.IRON_D, P.NIGHT),
        clouds("citadel", 150, 29, P.MAROON, P.RED_D),
        single("bg_citadel_far", far_layer),
        single("bg_citadel_near", near_layer),
        bushes("citadel", 22, 31, P.NIGHT, P.IRON_D, rubble),
        *ground("citadel", citadel_ground),
        flat("ground_citadel_fill", P.IRON_D),
        ravine("citadel", P.IRON, P.IRON_L, P.IRON_D, P.NIGHT, 16),
        ravine_fill("citadel", P.MAROON, P.RED_D, lava=True),
        flat("ravine_citadel_deep", P.RED_D),
    ]


# --- start screen -----------------------------------------------------------------------------------
# The strips start at the left edge of the screen, and an upright phone shows about the first 195 units, so the
# treehouse sits at the left and the castle with its waterfall at the right of that span (as in the start-screen
# reference); the rest of the 320 strip continues the forest for wide screens and the scroll.

def treehouse(c: Canvas, x: float, base: float) -> None:
    """A big leafy tree with a red-roofed cabin on a plank platform in its crown, a ladder down the trunk."""
    W.gnarled_tree(c, x, base, 26, 12, 64, 40, 301, vines=3)
    deck_y, hx = 50, x + 2
    for px_ in (hx - 13, hx + 12):                           # struts down to the trunk
        c.line((px_, deck_y + 1), (x + (2 if px_ > x else -2), deck_y + 12), P.BARK_D, 2)
    c.rect(hx - 16, deck_y, hx + 16, deck_y + 2, P.PLANK)     # platform
    c.rect(hx - 16, deck_y, hx + 16, deck_y, P.PLANK_L)
    c.rect(hx - 16, deck_y + 2, hx + 16, deck_y + 2, P.PLANK_D)
    for k in range(int(hx - 16), int(hx + 17), 4):
        c.px(k, deck_y + 1, P.PLANK_D)
    for k in range(int(hx - 16), int(hx + 17), 5):            # rail
        c.rect(k, deck_y - 5, k, deck_y - 1, P.PLANK_D)
    c.rect(hx - 16, deck_y - 5, hx - 7, deck_y - 5, P.PLANK_L)
    c.rect(hx + 8, deck_y - 5, hx + 16, deck_y - 5, P.PLANK_L)
    # cabin
    wl, wr, wt = hx - 9, hx + 9, deck_y - 15
    c.rect(wl, wt, wr, deck_y - 1, P.PLANK)
    for k, yy in enumerate(range(int(wt), int(deck_y), 3)):
        c.rect(wl, yy, wr, yy, P.PLANK_D)
    c.rect(wr - 4, wt, wr, deck_y - 1, P.PLANK_D)
    c.rect(wl + 3, wt + 4, wl + 7, wt + 8, P.BARK_DD)          # lit window
    c.rect(wl + 4, wt + 5, wl + 6, wt + 7, P.LANTERN)
    c.px(wl + 4, wt + 5, P.WHITE)
    c.rect(hx + 2, wt + 5, hx + 6, deck_y - 1, P.BARK_D)       # door
    c.rect(hx + 3, wt + 6, hx + 5, deck_y - 1, P.BARK)
    c.rect(wr - 3, wt - 12, wr - 1, wt - 4, P.STONE)           # chimney
    c.rect(wr - 4, wt - 13, wr, wt - 12, P.STONE_D)
    c.poly([(wl - 4, wt + 1), (hx, wt - 12), (wr + 4, wt + 1)], P.RED)     # red roof
    c.poly([(hx, wt - 12), (wr + 4, wt + 1), (hx + 1, wt + 1)], P.RED_D)
    for k in range(1, 4):                                    # shingle rows
        yy = wt - 12 + k * 3.3
        half = (yy - (wt - 12)) / 13 * (13 + 4)
        c.line((hx - half, yy), (hx + half, yy), P.RED_D if k % 2 else P.CAPE_D)
    c.line((wl - 3, wt), (hx - 1, wt - 11), P.CAPE_L)
    # leaves overlapping the platform's ends, and a ladder down the trunk
    W.clump(c, hx - 18, deck_y + 2, 6)
    W.clump(c, hx + 19, deck_y + 3, 6)
    for k in range(int(deck_y + 4), int(base - 2), 3):
        c.rect(x - 4, k, x + 1, k, P.PLANK_L)
    c.line((x - 4, deck_y + 3), (x - 4, base - 2), P.PLANK_D)
    c.line((x + 1, deck_y + 3), (x + 1, base - 2), P.PLANK_D)


def menu_clouds() -> Canvas:
    """Far layer: a cumulus bank, blue mountains, the castle with red cone roofs on a cliff and a waterfall;
    the treehouse tree at the left stands in front of it all (unhazed)."""
    h = 110
    c = Canvas(LAYER_W, h)
    far = Canvas(LAYER_W, h)
    for k, (x, base, w, ch) in enumerate(((40, 52, 70, 30), (120, 44, 60, 26), (200, 50, 80, 32), (280, 46, 60, 26),
                                          (90, 64, 50, 18), (250, 66, 56, 20))):
        layer = Canvas(LAYER_W, h)
        W.wrapped(lambda px, base=base, w=w, ch=ch, k=k: W.cumulus(layer, px, base, w, ch, 120 + k), x)
        far.paste(layer)
    W.mountains(far, h, 14, 6, (34, 56), (P.MOUNT_L, P.MOUNT_L, P.MOUNT), tips=P.SKY_HAZE)
    W.mountains(far, h, 15, 5, (22, 40), (P.MOUNT_L, P.MOUNT, P.MOUNT_D))
    top, left, right = 40, 106, 200                           # the castle cliff (the forest's rock and castle)
    falls = (180, 187)
    W.rock_cliff(far, left, right, top, 18, notch=falls)
    W.rim_bushes(far, [(114, 6), (192, 6)], top - 1, 150)
    W.hill_castle(far, 145, top + 1)
    W.cascade(far, falls[0], top, h - 3, falls[1] - falls[0] + 1, 2)
    W.haze(far, P.SKY_HAZE, 0.1)
    c.paste(far)
    W.piece(c, lambda layer, px: treehouse(layer, px, h - 1), 24)
    return c


def menu_horizon() -> Canvas:
    """Middle distance: a teal forest band and green pines, a lake, a red-roofed cottage, a wooden bridge over
    the water and lush round trees."""
    h = 80
    c = Canvas(LAYER_W, h)
    band = Canvas(LAYER_W, h)
    rnd = noise(140)
    band.rect(0, h - 22, 156, h - 1, P.DIST_D)
    band.rect(194, h - 22, LAYER_W - 1, h - 1, P.DIST_D)
    band.rect(157, h - 16, 193, h - 1, P.DIST_D)
    for i in range(18):
        x = i * LAYER_W / 18 + rnd() * 8
        top = h - 40 - rnd() * 12
        if 150 < x < 196:                                    # keep the waterfall's foot and the lake open
            top = h - 24
        W.wrapped(lambda px, top=top, i=i: W.round_tree(band, px, h, top, 18 + (i % 3) * 4, 140 + i, W.DISTANT,
                                                        (P.DIST_DD, P.DIST_DD), (4, 6)), x)
    c.paste(W.haze(band, P.SKY_HAZE, 0.08))
    # the lake, behind the near trees: a light rim, ripples
    c.rect(0, h - 12, LAYER_W - 1, h - 1, P.WATER)
    c.rect(0, h - 12, LAYER_W - 1, h - 12, P.WATER_L)
    for k in range(24):
        x, y = rnd() * LAYER_W, h - 10 + rnd() * 9
        c.line((x, y), (x + 3 + rnd() * 3, y), P.WATER_L if k % 3 else P.WHITE)

    def pine(layer, px, tall):
        layer.rect(px - 1, h - 6, px + 1, h - 1, P.BARK_D)
        for k in range(4):
            t = h - 6 - tall + k * tall * 0.24
            wdt = 3 + k * 2.2
            layer.poly([(px - wdt, t + tall * 0.3), (px, t), (px + wdt, t + tall * 0.3)], P.KIT_GREEN_D)
            layer.poly([(px - wdt * 0.2, t + 1), (px, t), (px + wdt * 0.9, t + tall * 0.28), (px + wdt * 0.2, t + tall * 0.28)],
                       P.KIT_GREEN_DD)
            layer.line((px - wdt + 1, t + tall * 0.3 - 1), (px - 1, t + 2), P.KIT_GREEN)
    for x, tall in ((46, 40), (106, 36), (236, 44), (300, 34)):
        W.piece(c, lambda layer, px, tall=tall: pine(layer, px, tall), x)

    def cottage(layer, px):
        base = h - 1
        layer.rect(px - 9, base - 12, px + 9, base, P.CASTLE)
        layer.rect(px + 4, base - 12, px + 9, base, P.CASTLE_D)
        layer.poly([(px - 12, base - 11), (px - 2, base - 22), (px + 8, base - 22), (px + 12, base - 11)], P.RED)
        layer.poly([(px + 2, base - 22), (px + 8, base - 22), (px + 12, base - 11), (px + 4, base - 11)], P.RED_D)
        layer.line((px - 11, base - 12), (px - 2, base - 21), P.CAPE_L)
        layer.rect(px - 6, base - 8, px - 3, base - 5, P.BARK_DD)
        layer.rect(px - 5, base - 7, px - 4, base - 6, P.LANTERN)
        layer.rect(px + 1, base - 7, px + 4, base, P.BARK)
    W.piece(c, cottage, 72)

    def bridge(layer, px, span):
        deck = h - 16
        for k in range(0, span + 1, 8):                       # piles in the water
            layer.rect(px + k, deck, px + k + 1, h - 1, P.BARK_D)
        layer.rect(px, deck, px + span, deck + 2, P.PLANK)
        layer.rect(px, deck, px + span, deck, P.PLANK_L)
        layer.rect(px, deck + 2, px + span, deck + 2, P.PLANK_D)
        for k in range(0, span + 1, 6):                       # rail posts and two rails
            layer.rect(px + k, deck - 8, px + k + 1, deck - 1, P.PLANK)
            layer.px(px + k, deck - 8, P.PLANK_L)
        layer.rect(px, deck - 7, px + span + 1, deck - 6, P.PLANK_L)
        layer.rect(px, deck - 4, px + span + 1, deck - 4, P.PLANK)
        for k in range(0, span, 12):                          # cross braces
            layer.line((px + k, deck - 6), (px + k + 6, deck - 1), P.PLANK_D)
    W.piece(c, lambda layer, px: bridge(layer, px, 52), 146)
    W.piece(c, lambda layer, px: bridge(layer, px, 26), 22)

    for k, (x, top, w) in enumerate(((128, 30, 26), (212, 22, 32), (268, 30, 26), (8, 34, 22))):
        W.piece(c, lambda layer, px, top=top, w=w, k=k: W.round_tree(layer, px, h - 1, top, w, 160 + k,
                                                                     size=(4, 7)), x)
    return W.haze(c, P.SKY_L, 0.05)


def menu_bushes() -> Canvas:
    """Front edge of the start screen: round bushes heavy with pink, white, yellow and blue flowers."""
    from characters.screens import flower
    h = 26
    c = Canvas(LAYER_W, h)
    rnd = noise(55)
    for i in range(12):
        x = i * LAYER_W / 12 + rnd() * 10
        w = 16 + rnd() * 16
        tall = 10 + rnd() * 8

        def bush(layer, px, w=w, tall=tall, i=i):
            W.canopy(layer, px, h - tall / 2 + 1, w, tall + 2, 400 + i, size=(3, 6))
        W.piece(c, bush, x)
    colours = ((P.PINK, P.GOLD), (P.WHITE, P.GOLD), (P.YELLOW, P.ORANGE), (P.BLUE, P.YELLOW), (P.PINK, P.YELLOW))
    for k in range(20):
        x = rnd() * LAYER_W
        y = h - 4 - rnd() * 10
        petal, centre = colours[k % len(colours)]
        layer = Canvas(LAYER_W, h)
        W.wrapped(lambda px, y=y, petal=petal, centre=centre: flower(layer, px, y, petal, centre, P.CREAM_D), x)
        c.paste(layer)
    return c


def menu() -> list[Sprite]:
    """The start screen, in the Purrwood look: treehouse, castle and waterfall, a bridge, trees and flowers."""
    return [
        single("bg_menu_sky", smooth_sky("menu", [P.SKY_TOP, P.SKY, P.SKY_L, P.SKY_L, P.SKY_HAZE])[0]
               .anims["still"].frames[0]),
        forest_clouds("bg_menu_puffs", 120, [(30, 40, 40, 18), (118, 92, 30, 13), (190, 30, 46, 20),
                                             (262, 84, 34, 15), (310, 50, 26, 11)]),
        single("bg_menu_clouds", menu_clouds()),
        single("bg_menu_horizon", menu_horizon()),
        single("bg_menu_bushes", menu_bushes()),
    ]


def build() -> list[Sprite]:
    return [*forest(), *citadel(), *menu()]   # frost: characters/frostpaw.py; haunted: characters/meowseum.py
