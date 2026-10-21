"""Drawing helpers for World 1's look (the forest kit): leafy canopies with yellow-green tips, gnarled
trunks, hanging vines, cumulus clouds, blue mountains, a white castle, cobbles, grass fringe, water.

Strips are LAYER_W wide and tile horizontally, so everything that can cross an edge is drawn through
`wrapped()` and outlined with `outline_wrapped()`, which treats the left and right edges as neighbours."""
from __future__ import annotations

import math

from PIL import Image, ImageDraw

import palette as P
from draw import Canvas, noise, tint

LAYER_W = 320


def wrapped(draw, x: float, width: int = LAYER_W) -> None:
    for offset in (-width, 0, width):
        draw(x + offset)


def outline_wrapped(c: Canvas, colour, wrap: bool = True) -> Canvas:
    """1px outline around everything drawn; with `wrap`, column 0 and the last column touch."""
    src = c.img.load()
    w, h = c.img.size
    edge = []
    for y in range(h):
        for x in range(w):
            if src[x, y][3]:
                continue
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if wrap:
                    nx %= w
                if 0 <= nx < w and 0 <= ny < h and src[nx, ny][3]:
                    edge.append((x, y))
                    break
    for x, y in edge:
        src[x, y] = colour
    return c


def piece(c: Canvas, draw, x: float, outline=P.WOOD_OUT) -> None:
    """Draws one outlined element (wrapped across the strip edges) onto strip `c`."""
    layer = Canvas(*c.size)
    wrapped(lambda px: draw(layer, px), x, c.size[0])
    if outline:
        outline_wrapped(layer, outline)
    c.paste(layer)


def haze(c: Canvas, colour, amount: float) -> Canvas:
    """Pushes a whole layer toward the air colour, so it sits behind the outlined characters."""
    c.img = tint(c.img, colour, amount)
    c.d = ImageDraw.Draw(c.img)
    return c


# --- leaves ------------------------------------------------------------------------------------------

LEAVES = (P.KIT_GREEN_DD, P.KIT_GREEN_D, P.KIT_GREEN, P.KIT_GREEN_L, P.LEAF_Y)
DISTANT = (P.DIST_DD, P.DIST_D, P.DIST, P.DIST_L, P.DIST_L)


def clump(c: Canvas, x: float, y: float, rad: float, cols=LEAVES) -> None:
    """One rounded bunch of leaves, lit from the top left: dark rim, mid body, light cap, bright tips."""
    dd, d, m, l, y_ = cols
    c.ellipse(x, y, rad, rad * 0.82, dd)
    c.ellipse(x - 0.5, y - 1, rad - 1, rad * 0.82 - 1, d)
    c.ellipse(x - 1, y - rad * 0.28, rad * 0.78, rad * 0.55, m)
    c.ellipse(x - rad * 0.3, y - rad * 0.45, rad * 0.46, rad * 0.3, l)
    if rad >= 4 and y_ != l:
        hx, hy = x - rad * 0.35, y - rad * 0.5
        for dx, dy in ((0, 0), (1, 0), (0, 1), (-1, 1)):
            c.px(hx + dx, hy + dy, y_)
    # leaf notches along the lower rim make the edge read as leaves, not a ball
    for k in range(3):
        a = math.radians(40 + k * 50)
        c.px(x + math.cos(a) * rad * 0.7, y + math.sin(a) * rad * 0.6, dd)


def canopy(c: Canvas, cx: float, cy: float, w: float, h: float, seed: int, cols=LEAVES,
           size: tuple = (5, 9)) -> list:
    """A rounded crown of overlapping clumps, drawn top to bottom so each bunch overlaps the one above.
    Returns points along its underside, for vines."""
    rnd = noise(seed)
    pts = []
    count = int(w * h / (size[1] * size[1]) * 2.2) + 4
    for _ in range(count):
        a, d = rnd() * math.tau, math.sqrt(rnd())
        pts.append((cx + math.cos(a) * d * (w / 2 - size[0]), cy + math.sin(a) * d * (h / 2 - size[0]),
                    size[0] + rnd() * (size[1] - size[0])))
    # a scalloped rim so the silhouette is lumpy all round
    for k in range(14):
        a = k / 14 * math.tau
        pts.append((cx + math.cos(a) * (w / 2 - size[0] * 0.8), cy + math.sin(a) * (h / 2 - size[0] * 0.8),
                    size[0] + rnd() * 2))
    pts.sort(key=lambda p: p[1])
    dd, d, m, l, y_ = cols
    for x, y, rad in pts:
        depth = (y - (cy - h / 2)) / h
        if depth > 0.62:
            shade = (dd, dd, dd, d, d)
        elif depth > 0.38:
            shade = (dd, d, d, m, m)
        else:
            shade = cols
        clump(c, x, y, rad, shade)
    under = sorted((p for p in pts if p[1] > cy + h * 0.15), key=lambda p: p[0])
    return [(x, y + rad * 0.7) for x, y, rad in under]


def vine(c: Canvas, x: float, top: float, length: float, seed: int, flowers: bool = False) -> None:
    """A vine hanging straight down with leaves either side."""
    rnd = noise(seed)
    for k in range(int(length)):
        y = top + k
        sway = math.sin(k * 0.35 + seed) * 0.6
        c.px(x + sway, y, P.KIT_GREEN_DD)
        if k % 3 == 0:
            side = -1 if (k // 3) % 2 else 1
            col = P.KIT_GREEN_L if rnd() > 0.4 else P.KIT_GREEN
            if flowers and rnd() > 0.8:
                col = P.PINK
            elif rnd() > 0.9:
                col = P.GOLD
            c.px(x + sway + side, y, col)
            c.px(x + sway + side * 1.6, y + 1, P.KIT_GREEN)
    c.px(x, top + length, P.KIT_GREEN_L)


# --- trees -------------------------------------------------------------------------------------------

def gnarled_tree(c: Canvas, x: float, base: float, top: float, trunk_w: float, crown_w: float, crown_h: float,
                 seed: int, vines: int = 4, lantern: bool = False) -> None:
    """A big old tree: a thick twisting trunk with flared roots, limbs into a wide leafy crown, vines."""
    rnd = noise(seed)
    crown_cy = top + crown_h / 2
    trunk_top = crown_cy + crown_h * 0.2
    phase, amp = rnd() * math.tau, 4 + rnd() * 3

    def centre(y: float) -> float:
        t = (y - trunk_top) / (base - trunk_top)
        return x + math.sin(t * math.pi * 1.2 + phase) * amp

    # limbs: forking from the trunk into the crown, drawn over its shaded underside like the kit's trees
    limbs = []
    fork = trunk_top + (base - trunk_top) * 0.18
    for side, reach, lift in ((-1, 0.36, 0.12), (1, 0.34, 0.18), (-0.2 if rnd() > 0.5 else 0.25, 0.1, -0.05)):
        ex = x + side * crown_w * (reach + rnd() * 0.06)
        ey = crown_cy + crown_h * lift
        limbs.append(((centre(fork + 6), fork + 6), (ex, ey)))

    def draw_limbs():
        for (sx, sy), (ex, ey) in limbs:
            steps = 16
            pts = []
            for i in range(steps + 1):
                t = i / steps
                pts.append((sx + (ex - sx) * t, sy + (ey - sy) * t - math.sin(t * math.pi) * 5,
                            trunk_w * 0.55 * (1 - t * 0.6)))
            for colour, dx, dy in ((P.BARK_D, 1, 1), (P.BARK, 0, 0)):
                for px, py, wdt in pts:
                    c.rect(px - wdt / 2 + dx, py - wdt / 2 + dy, px + wdt / 2 + dx - 1, py + wdt / 2 + dy - 1, colour)
            for px, py, wdt in pts[::2]:
                c.px(px - wdt / 2, py - wdt / 2 + 1, P.BARK_L)

    # trunk, row by row, flaring into roots at the bottom
    grooves = [(-0.35 + k * 0.3, rnd() * 6) for k in range(4)]
    y = int(trunk_top)
    while y <= base:
        t = (y - trunk_top) / (base - trunk_top)
        half = trunk_w / 2 * (1 + 1.6 * max(0.0, (t - 0.7) / 0.3) ** 2) * (1 + 0.35 * max(0.0, 0.3 - t) / 0.3)
        cxy = centre(y)
        left, right = cxy - half, cxy + half
        c.rect(left, y, right, y, P.BARK)
        c.rect(right - half * 0.65, y, right, y, P.BARK_D)
        c.rect(left, y, left + 1.5, y, P.BARK_L)
        for f, ph in grooves:
            if math.sin(y * 0.45 + ph) > -0.55:
                g = (f + t * 1.4 + 0.5) % 1.0 - 0.5
                gx = cxy + g * half * 1.8 + math.sin(y * 0.2 + ph)
                if left + 1 < gx < right - 1:
                    c.px(gx, y, P.BARK_DD if gx > cxy else P.BARK_D)
        y += 1
    # roots
    for k, side in enumerate((-1, -0.5, 0.6, 1)):
        bx = centre(base)
        c.poly([(bx + side * trunk_w * 0.5, base - 12), (bx + side * trunk_w * 1.6, base - 1),
                (bx + side * trunk_w * 1.75, base), (bx + side * trunk_w * 0.4, base)],
               P.BARK if side < 0 else P.BARK_D)
        c.line((bx + side * trunk_w * 0.55, base - 10), (bx + side * trunk_w * 1.5, base - 1),
               P.BARK_L if side < 0 else P.BARK_DD)
    # a hollow and moss on the bark
    hy = trunk_top + (base - trunk_top) * (0.45 + rnd() * 0.15)
    c.ellipse(centre(hy) + 1, hy, 2, 3, P.BARK_DD)
    c.px(centre(hy), hy - 2, P.BARK_D)
    for _ in range(5):
        my = trunk_top + (base - trunk_top) * rnd()
        c.ellipse(centre(my) - trunk_w * 0.25 + rnd() * 3, my, 1.5, 1, P.KIT_GREEN_D)
        c.px(centre(my) - trunk_w * 0.25 + rnd() * 3, my - 1, P.KIT_GREEN)
    # crown, then vines from its underside
    under = canopy(c, x, crown_cy, crown_w, crown_h, seed + 1)
    draw_limbs()
    for (_, _), (ex, ey) in limbs:
        clump(c, ex - 2, ey - 3, 7, (P.KIT_GREEN_DD, P.KIT_GREEN_D, P.KIT_GREEN_D, P.KIT_GREEN, P.KIT_GREEN))
        clump(c, ex + 4, ey - 1, 5, (P.KIT_GREEN_DD, P.KIT_GREEN_D, P.KIT_GREEN, P.KIT_GREEN_L, P.KIT_GREEN_L))
    if under and vines:
        step = max(1, len(under) // vines)
        for k, (vx, vy) in enumerate(under[::step][:vines]):
            vine(c, vx, vy - 2, 10 + rnd() * 18, seed + k, flowers=k % 2 == 0)
    if lantern:
        (sx, sy), (ex, ey) = limbs[1]
        lx, ly = sx + (ex - sx) * 0.6, sy + (ey - sy) * 0.6 - math.sin(0.6 * math.pi) * 5
        hang_lantern(c, lx, ly + 2, 10)


def hang_lantern(c: Canvas, x: float, y: float, rope: float) -> None:
    c.line((x, y), (x, y + rope), P.BARK_DD)
    lantern(c, x, y + rope)


def lantern(c: Canvas, x: float, y: float) -> None:
    """A small lantern, its top at y."""
    c.rect(x - 2, y, x + 2, y + 1, P.BARK_DD)
    c.rect(x - 2, y + 2, x + 2, y + 6, P.LANTERN)
    c.rect(x - 1, y + 3, x + 1, y + 5, P.WHITE)
    c.px(x - 2, y + 4, P.GOLD_D)
    c.px(x + 2, y + 4, P.GOLD_D)
    c.rect(x - 2, y + 7, x + 2, y + 7, P.BARK_DD)


def round_tree(c: Canvas, x: float, base: float, top: float, w: float, seed: int, cols=LEAVES,
               trunk=(P.BARK, P.BARK_D), size=(5, 9)) -> None:
    """A smaller round tree with a straight trunk (the middle distance)."""
    h = (base - top) * 0.62
    c.rect(x - 2, top + h * 0.6, x + 2, base, trunk[0])
    c.rect(x + 1, top + h * 0.6, x + 2, base, trunk[1])
    c.poly([(x - 5, base), (x - 2, base - 5), (x + 2, base - 5), (x + 5, base)], trunk[0])
    canopy(c, x, top + h / 2, w, h, seed, cols, size)


# --- buildings and wood ------------------------------------------------------------------------------

def cabin(c: Canvas, x: float, base: float) -> None:
    """A log cabin with a mossy gable roof, lit windows, a porch rail and a chimney (about 46x44)."""
    wall_l, wall_r, wall_top = x - 18, x + 18, base - 24
    c.rect(x + 10, base - 46, x + 14, base - 30, P.STONE)                  # chimney
    c.rect(x + 13, base - 46, x + 14, base - 30, P.STONE_D)
    c.rect(x + 9, base - 47, x + 15, base - 46, P.STONE_D)
    c.rect(wall_l, wall_top, wall_r, base, P.PLANK_D)
    for k, yy in enumerate(range(int(wall_top), int(base), 3)):             # logs
        c.rect(wall_l, yy, wall_r, yy + 1, P.PLANK if k % 2 else P.PLANK_L)
        c.px(wall_l + 1, yy, P.PLANK_L)
        c.ellipse(wall_l, yy + 1, 1.5, 1.2, P.PLANK_L)                     # log ends
        c.ellipse(wall_r, yy + 1, 1.5, 1.2, P.PLANK)
    # gable: front triangle of vertical boards under the roof
    c.poly([(wall_l + 2, wall_top), (x, base - 42), (wall_r - 2, wall_top)], P.PLANK)
    for bx in range(int(wall_l + 5), int(wall_r - 3), 3):
        c.line((bx, wall_top), (bx, base - 40), P.PLANK_D)
    c.poly([(wall_l + 2, wall_top), (x, base - 42), (x - 1, base - 42), (wall_l + 1, wall_top)], P.PLANK_D)
    c.rect(x - 3, base - 34, x + 3, base - 29, P.BARK_DD)                    # attic window
    c.rect(x - 2, base - 33, x + 2, base - 30, P.LANTERN)
    c.line((x, base - 33), (x, base - 30), P.PLANK_D)
    # roof: two slopes of mossy shingles overhanging the walls
    for side in (-1, 1):
        roof = [(x, base - 45), (x + side * 24, wall_top + 2), (x + side * 24, wall_top + 5),
                (x, base - 41)]
        c.poly(roof, P.BARK_D if side < 0 else P.BARK_DD)
        for k in range(1, 6):
            t = k / 6
            c.line((x + side * 24 * t, base - 45 + (wall_top + 2 - base + 45) * t),
                   (x + side * 24 * t, base - 42 + (wall_top + 5 - base + 42) * t),
                   P.BARK_DD if side < 0 else P.BARK_D)
    for mx, my in ((-14, -27), (-8, -33), (12, -29), (-19, -24), (6, -37)):  # moss on the roof
        c.ellipse(x + mx, base + my, 2.5, 1.2, P.KIT_GREEN_D)
        c.px(x + mx - 1, base + my - 1, P.KIT_GREEN)
    # windows and door
    for wx in (wall_l + 4, wall_r - 10):
        c.rect(wx, base - 18, wx + 6, base - 12, P.BARK_DD)
        c.rect(wx + 1, base - 17, wx + 5, base - 13, P.LANTERN)
        c.rect(wx + 1, base - 17, wx + 2, base - 16, P.WHITE)
        c.line((wx + 3, base - 17), (wx + 3, base - 13), P.PLANK_D)
        c.line((wx + 1, base - 15), (wx + 5, base - 15), P.PLANK_D)
        c.rect(wx - 1, base - 11, wx + 7, base - 10, P.PLANK_D)              # sill
    c.rect(x - 3, base - 14, x + 3, base, P.BARK_D)
    c.rect(x - 2, base - 13, x + 2, base, P.BARK)
    c.line((x, base - 13), (x, base), P.BARK_D)
    c.px(x + 1, base - 7, P.GOLD)
    # porch: a step and a rail in front
    c.rect(wall_l - 3, base - 2, wall_r + 3, base, P.PLANK_D)
    c.rect(wall_l - 3, base - 2, wall_r + 3, base - 2, P.PLANK)
    for px in (wall_l - 3, wall_l + 6, wall_r - 6, wall_r + 3):
        c.rect(px, base - 8, px + 1, base - 2, P.PLANK)
    c.rect(wall_l - 3, base - 8, wall_l + 7, base - 7, P.PLANK_L)
    c.rect(wall_r - 6, base - 8, wall_r + 4, base - 7, P.PLANK_L)


def fence(c: Canvas, x0: float, x1: float, base: float, height: float = 10) -> None:
    for px in range(int(x0), int(x1) + 1, 6):
        c.rect(px, base - height, px + 1, base, P.PLANK)
        c.px(px, base - height, P.PLANK_L)
        c.px(px + 1, base - height - 1, P.PLANK_L)
        c.px(px + 1, base - 2, P.PLANK_D)
    for ry in (base - height + 2, base - height * 0.4):
        c.rect(x0, ry, x1 + 1, ry + 1, P.PLANK_L)
        c.rect(x0, ry + 1, x1 + 1, ry + 1, P.PLANK)


def lamp_post(c: Canvas, x: float, base: float) -> None:
    c.rect(x - 1, base - 20, x, base, P.BARK_D)
    c.rect(x - 1, base - 20, x + 5, base - 19, P.BARK_D)
    hang_lantern(c, x + 4, base - 19, 2)


# --- sky, mountains, castle --------------------------------------------------------------------------

def cumulus(c: Canvas, x: float, base: float, w: float, h: float, seed: int) -> None:
    """A puffy cloud with a flat base: white tops, blue-shaded underside (no dark outline)."""
    rnd = noise(seed)
    balls = []
    n = max(3, int(w / 9))
    for i in range(n):
        t = (i + 0.5) / n
        bx = x - w / 2 + t * w + (rnd() - 0.5) * 4
        rad = (h * 0.45) * (0.55 + 0.45 * math.sin(t * math.pi)) * (0.8 + rnd() * 0.35)
        balls.append((bx, base - rad * 0.75, rad))
    for k in range(max(1, n // 3)):                      # a second tier on top
        bx = x - w * 0.25 + rnd() * w * 0.5
        rad = h * (0.32 + rnd() * 0.15)
        balls.append((bx, base - h + rad * 1.05, rad))
    layer = Canvas(*c.size)
    for bx, by, rad in balls:
        layer.ellipse(bx, by, rad, rad * 0.9, P.CLOUD_D)
    for bx, by, rad in balls:
        layer.ellipse(bx - 0.5, by - 1.2, rad - 0.8, rad * 0.9 - 1.2, P.CLOUD_S)
    for bx, by, rad in balls:
        layer.ellipse(bx - rad * 0.2, by - rad * 0.3, rad * 0.75, rad * 0.62, P.WHITE)
    px = layer.img.load()
    W, H = layer.img.size
    for yy in range(max(0, int(base) + 1), H):           # flat base
        for xx in range(W):
            px[xx, yy] = P.CLEAR
    for xx in range(W):
        if 0 <= int(base) < H and px[xx, int(base)][3]:
            px[xx, int(base)] = P.CLOUD_D
    c.paste(layer)


def mountains(c: Canvas, base: float, seed: int, count: int, tall: tuple, cols: tuple, tips=None) -> None:
    """A row of jagged peaks, lit on the left face; `cols` = (light face, body, shadow face)."""
    rnd = noise(seed)
    light, body, dark = cols
    for i in range(count):
        x = i * LAYER_W / count + rnd() * 18
        h = tall[0] + rnd() * (tall[1] - tall[0])
        w = h * (0.9 + rnd() * 0.5)
        jag = [(rnd() - 0.5) * 4 for _ in range(6)]

        def one(px, h=h, w=w, jag=jag):
            peak = (px, base - h)
            left = [(px - w, base), (px - w * 0.6, base - h * 0.45 + jag[0]), (px - w * 0.25, base - h * 0.8 + jag[1]),
                    peak]
            right = [peak, (px + w * 0.3, base - h * 0.72 + jag[2]), (px + w * 0.65, base - h * 0.35 + jag[3]),
                     (px + w, base)]
            c.poly(left + right[1:], body)
            c.poly(left + [(px - w * 0.05, base - h * 0.5 + jag[4]), (px - w * 0.2, base)], light)
            c.poly([peak] + right[1:] + [(px + w * 0.25, base), (px + w * 0.1, base - h * 0.55 + jag[5])], dark)
            # a ridge line on the lit face
            c.line(peak, (px - w * 0.15, base - h * 0.45), body)
            if tips:
                c.poly([peak, (px - w * 0.12, base - h * 0.84), (px - w * 0.02, base - h * 0.88),
                        (px + w * 0.08, base - h * 0.82)], tips)
        wrapped(one, x)


def castle(c: Canvas, x: float, base: float) -> None:
    """A white hilltop castle with red and blue cone roofs and flags (about 64x58)."""
    # curtain wall
    c.rect(x - 28, base - 16, x + 28, base, P.CASTLE)
    c.rect(x + 12, base - 16, x + 28, base, P.CASTLE_D)
    for k in range(12):
        c.rect(x - 28 + k * 5, base - 18, x - 26 + k * 5, base - 16, P.CASTLE)
    c.ellipse(x, base - 4, 4, 5, P.MOUNT_DD)                               # gate
    c.rect(x - 4, base - 4, x + 4, base, P.MOUNT_DD)
    towers = [(-26, 6, 30, P.RED), (-14, 7, 40, P.MOUNT_D), (-3, 9, 52, P.RED), (9, 7, 44, P.RED),
              (19, 6, 34, P.MOUNT_D), (27, 5, 26, P.RED)]
    for tx, w, h, roof in towers:
        left, right, top = x + tx - w / 2, x + tx + w / 2, base - h
        c.rect(left, top, right, base - 10, P.CASTLE)
        c.rect(left, top, left, base - 10, P.CASTLE_L)
        c.rect(right - w * 0.35, top, right, base - 10, P.CASTLE_D)
        c.rect(left - 1, top, right + 1, top + 1, P.CASTLE_L)
        rd = P.RED_D if roof == P.RED else P.MOUNT_DD
        c.poly([(left - 1.5, top), (x + tx, top - w * 1.6), (right + 1.5, top)], roof)
        c.poly([(x + tx, top - w * 1.6), (right + 1.5, top), (x + tx + 0.5, top)], rd)
        for wy in range(int(top + 4), int(base - 12), 7):
            c.rect(x + tx - 0.5, wy, x + tx + 0.5, wy + 2, P.MOUNT_DD)
        if h >= 40:                                                         # flag
            fy = top - w * 1.6
            c.line((x + tx, fy), (x + tx, fy - 5), P.CASTLE_D)
            c.rect(x + tx + 1, fy - 5, x + tx + 3, fy - 4, P.GOLD if roof == P.RED else P.RED)


def waterfall(c: Canvas, x: float, top: float, bottom: float, w: float = 7) -> None:
    c.rect(x, top, x + w, bottom, P.WATER)
    for k, col in enumerate((P.WHITE, P.WATER_L, P.WATER_L, P.WHITE, P.WATER_L)):
        sx = x + 1 + k * (w - 1) / 5
        for yy in range(int(top), int(bottom)):
            if (yy * 3 + k * 7) % 11 < 7:
                c.px(sx, yy, col)
    c.rect(x - 1, top, x + w + 1, top + 1, P.WATER_L)
    c.ellipse(x + w / 2, bottom, w * 0.9, 3, P.WHITE)
    c.ellipse(x + w / 2, bottom + 1, w * 0.6, 2, P.CLOUD_S)


# --- ground ------------------------------------------------------------------------------------------

def cobble(c: Canvas, x0: float, y0: float, x1: float, y1: float, cols: tuple) -> None:
    """A rounded stone between (x0, y0) and (x1, y1); `cols` = (light, body, dark)."""
    light, body, dark = cols
    cx, cy, rx, ry = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2
    c.ellipse(cx, cy, rx, ry, dark)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, dark)
    c.ellipse(cx - 0.5, cy - 0.5, rx - 0.5, ry - 0.5, body)
    c.rect(x0 + 1, y0 + 1, x1 - 2, y1 - 2, body)
    c.rect(x0 + 2, y0, x1 - 3, y0, light)
    c.rect(x0, y0 + 2, x0, y1 - 3, light)
    c.px(x0 + 1, y0 + 1, light)
    c.px(x0 + 2, y0 + 1, light)


def cobble_row(c: Canvas, y0: float, height: int, widths: list, offset: int, cols: tuple, seed: int,
               specks=(), tile_w: int = 32) -> None:
    rnd = noise(seed)
    x = offset
    for w in widths:
        def one(px, w=w):
            cobble(c, px, y0, px + w - 2, y0 + height - 2, cols)
        for shift in (-tile_w, 0, tile_w):
            one(x + shift)
        if specks and rnd() > 0.35:
            sx, sy = x + 2 + rnd() * (w - 5), y0 + 1 + rnd() * (height - 4)
            for shift in (-tile_w, 0, tile_w):
                c.px(sx + shift, sy, specks[int(rnd() * len(specks)) % len(specks)])
        x += w


def grass_top(c: Canvas, width: int, seed: int, flowers: bool = True) -> None:
    """Thick mossy turf on rows 0-6 with pointed tufts hanging over the earth to about row 12."""
    rnd = noise(seed)
    c.rect(0, 0, width - 1, 6, P.KIT_GREEN)
    c.rect(0, 0, width - 1, 1, P.KIT_GREEN_L)
    c.rect(0, 5, width - 1, 6, P.KIT_GREEN_D)
    for x in range(width):                                   # bright tips catching the light
        if (x * 5 + seed) % 7 < 3:
            c.px(x, 0, P.LEAF_Y)
        if (x * 3 + seed) % 5 == 0:
            c.px(x, 2, P.KIT_GREEN_L)
            c.px(x + 1, 1, P.LEAF_Y)
    x = 0
    while x < width:
        w = 5 + int(rnd() * 2)
        length = 5 + int(rnd() * 4)
        def tuft(px, w=w, length=length):
            for k in range(length):
                t = k / length
                half = (w - 1) / 2 * (1 - t * t)
                mid = px + (w - 1) / 2
                c.rect(mid - half, 5 + k, mid + half, 5 + k, P.KIT_GREEN)
                c.px(mid - half, 5 + k, P.KIT_GREEN_L if k < length - 2 else P.KIT_GREEN)
                if half >= 1:
                    c.px(mid + half, 5 + k, P.KIT_GREEN_D)
            c.px(px + (w - 1) / 2, 5 + length, P.KIT_GREEN_DD)
            c.px(px + 1, 6, P.LEAF_Y)
            c.px(px + w - 1, 5, P.KIT_GREEN_DD)            # the gap between two leaves
            c.px(px + w - 1, 6, P.KIT_GREEN_DD)
            c.px(px + 2, 3, P.KIT_GREEN_D)                   # leaf vein in the turf above
            c.px(px + 3, 4, P.KIT_GREEN_D)
            c.px(px + 1, 2, P.KIT_GREEN_L)
        for shift in (-width, 0, width):
            tuft(x + shift)
        x += w
    if flowers:
        for fx, col in ((7, P.PINK), (23, P.WHITE)):
            c.px(fx, 2, col)
            c.px(fx - 1, 3, col)
            c.px(fx + 1, 3, col)
            c.px(fx, 3, P.YELLOW)


def under_turf_shadow(c: Canvas, width: int, y0: int, y1: int, colour) -> None:
    """Darkens the transparent band under the turf before the cobbles are drawn into it."""
    c.rect(0, y0, width - 1, y1, colour)


# --- the forest's hilltop castle, cliff and waterfall (bg_forest_far) ------------------------------

def _tower(c: Canvas, cx: float, base: float, w: int, body: int, roof, flag=None, windows: bool = True,
           cone: float = 1.4) -> None:
    """One round tower: light left face, dark right face, a parapet ring, rows of dark windows, a cone
    roof shaded on the right and a flag. `body` = wall height above `base`; the cone is about 1.4*w tall."""
    left, right, top = cx - w / 2, cx + w / 2 - 1, base - body
    c.rect(left, top, right, base, P.CASTLE)
    c.rect(left, top, left, base, P.CASTLE_L)
    c.rect(right - max(1, w // 3) + 1, top, right, base, P.CASTLE_D)
    c.rect(left - 1, top - 2, right + 1, top, P.CASTLE)                 # parapet ring
    c.rect(left - 1, top - 2, right + 1, top - 2, P.CASTLE_L)
    c.rect(right, top - 2, right + 1, top, P.CASTLE_D)
    c.rect(left - 1, top, right + 1, top, P.CASTLE_D)
    if windows:
        for wy in range(int(top + 3), int(base - 3), 6):
            c.rect(cx - 0.5, wy, cx + 0.5 if w >= 6 else cx - 0.5, wy + 1, P.CASTLE_OUT)
    dark = P.RED_D if roof == P.RED else P.MOUNT_DD
    tip = top - 3 - round(w * cone)
    c.poly([(left - 1.5, top - 2), (cx - 0.5, tip), (right + 1.5, top - 2)], roof)
    c.poly([(cx - 0.5, tip), (right + 1.5, top - 2), (cx, top - 2)], dark)
    c.rect(left - 1, top - 3, right + 1, top - 3, dark)                  # eave
    if flag:
        c.line((cx - 0.5, tip - 1), (cx - 0.5, tip - 3), P.CASTLE_D)
        c.rect(cx + 0.5, tip - 3, cx + 2.5, tip - 2, flag)


def _crenels(c: Canvas, x0: float, x1: float, top: float) -> None:
    for x in range(int(x0), int(x1) + 1, 3):
        c.rect(x, top - 2, x + 1, top - 1, P.CASTLE)
        c.px(x, top - 2, P.CASTLE_L)


def hill_castle(c: Canvas, x: float, base: float, sw: float = 1.0, sh: float = 1.0) -> None:
    """A white castle seen from below the hill: at scale 1 about 60 wide and 39 tall from `base` to its highest
    flag (`sw`/`sh` stretch it across/up for bigger pictures). A tall central tower behind a keep, towers
    stepping down to each side, a crenellated curtain wall with a gate arch in front. Three depth layers,
    each outlined, so the towers read in front of one another."""
    w, h = c.size

    def X(v: float) -> float:
        return x + v * sw

    def Y(v: float) -> float:
        return base - v * sh

    def tower(layer, dx, lift, tw, body, roof, flag, windows=True):
        _tower(layer, X(dx), Y(lift), round(tw * sw), round(body * sh), roof, flag, windows, 1.4 * sh)

    # back: the central tower and the two outermost towers
    back = Canvas(w, h)
    tower(back, -0.5, 10, 8, 12, P.RED, P.GOLD)
    tower(back, -25, 4, 5, 12, P.MOUNT_D, P.RED)
    tower(back, 24, 4, 5, 11, P.RED, P.GOLD)
    outline_wrapped(back, P.CASTLE_OUT, wrap=False)
    c.paste(back)
    # middle: the keep, with a tower at each shoulder
    mid = Canvas(w, h)
    mid.rect(X(-11), Y(14), X(10), base, P.CASTLE)
    mid.rect(X(-11), Y(14), X(-11), base, P.CASTLE_L)
    mid.rect(X(4), Y(14), X(10), base, P.CASTLE_D)
    _crenels(mid, X(-11), X(9), Y(14))
    for wx in (-7, -2, 3):                                                # a row of tall windows
        mid.rect(X(wx), Y(12), X(wx) + 1, Y(10), P.CASTLE_OUT)
    tower(mid, -16, 2, 7, 17, P.MOUNT_D, P.RED)
    tower(mid, 15, 2, 7, 16, P.RED, P.GOLD)
    outline_wrapped(mid, P.CASTLE_OUT, wrap=False)
    c.paste(mid)
    # front: the curtain wall, gate arch and two little corner turrets
    front = Canvas(w, h)
    front.rect(X(-26), Y(8), X(25), base, P.CASTLE)
    front.rect(X(10), Y(8), X(25), base, P.CASTLE_D)
    front.rect(X(-26), Y(8), X(25), Y(8), P.CASTLE_L)
    _crenels(front, X(-26), X(24), Y(8))
    front.ellipse(x - 0.5, base - 4 * sh, 3 * sw, 3 * sh, P.CASTLE_OUT)       # gate arch
    front.rect(x - 3.5 * sw, base - 4 * sh, x + 2.5 * sw, base, P.CASTLE_OUT)
    front.rect(x - 2.5 * sw, base - 3 * sh, x + 1.5 * sw, base, P.BARK_D)
    front.line((x - 0.5, base - 3 * sh), (x - 0.5, base), P.BARK_DD)
    front.rect(x - 4.5 * sw, Y(7), x + 3.5 * sw, Y(7), P.CASTLE_D)          # arch stones
    for tx, roof in ((-28, P.RED), (27, P.MOUNT_D)):
        tower(front, tx, 0, 4, 11, roof, None, windows=False)
    outline_wrapped(front, P.CASTLE_OUT, wrap=False)
    c.paste(front)


def rock_cliff(c: Canvas, left: float, right: float, top: float, seed: int, notch: tuple | None = None,
               bottom: int | None = None) -> None:
    """A rocky cliff from `top` to the bottom of the layer: a grass cap with a bright rim, chunky rock
    faces lit on the left and shaded on the right, ledges with moss, and grass tufts over the edge. It reaches
    row `bottom` (default: the bottom of the canvas)."""
    w, h = c.size
    if bottom is not None:
        h = bottom + 1
    rnd = noise(seed)
    face = Canvas(w, h)
    face.poly([(left, h), (left + 3, top + 10), (left + 8, top + 2), (right - 8, top + 2), (right - 2, top + 12),
               (right + 2, h)], P.CLIFF_D)
    x = left + 2
    while x < right - 2:                                     # columns of rock, each a chunky block
        cw = 6 + int(rnd() * 9)
        y0 = top + 3 + int(rnd() * 9)
        lean = (rnd() - 0.5) * 4
        recessed = rnd() > 0.65                              # set back: darker, no lit face
        body, lit = (P.CLIFF_D, P.CLIFF) if recessed else (P.CLIFF, P.CLIFF_L)
        face.poly([(x, y0 + 1), (x + 1, y0), (x + cw - 2, y0), (x + cw - 1, y0 + 2), (x + cw - 1 + lean, h),
                   (x + lean, h)], body)
        face.poly([(x, y0 + 1), (x + 2, y0), (x + 2 + lean, h), (x + lean, h)], lit)
        face.poly([(x + cw - 3, y0 + 1), (x + cw - 1, y0 + 2), (x + cw - 1 + lean, h), (x + cw - 3 + lean, h)],
                  P.CLIFF_DD if recessed else P.CLIFF_D)
        if not recessed:                                     # grass on the column's top step
            face.rect(x + 1, y0 - 1, x + cw - 3, y0, P.FAR_GRASS)
            face.px(x + 1, y0 - 1, P.KIT_GREEN_L)
        y = y0 + 9 + int(rnd() * 10)
        while y < h - 6:                                     # a few ledges, staggered column to column
            t = (y - y0) / max(1, h - y0)
            x1, x2 = x + 1 + lean * t, x + cw - 3 + lean * t
            face.line((x1, y), (x2, y + 1), P.CLIFF_DD)
            face.line((x1, y - 1), (x2 - 1, y), lit)
            if rnd() > 0.5:
                face.rect(x1 + 1, y - 2, x1 + 2 + int(rnd() * 3), y - 2, P.FAR_GRASS)
                face.px(x1 + 1, y - 1, P.KIT_GREEN_D)
            y += 12 + int(rnd() * 12)
        x += cw
    for _ in range(4):                                       # boulders jutting out of the face
        bx = left + 10 + rnd() * (right - left - 20)
        by = top + 16 + rnd() * (h - top - 30)
        r = 3 + rnd() * 2
        face.ellipse(bx, by, r + 1, r * 0.8, P.CLIFF_DD)
        face.ellipse(bx - 0.5, by - 0.5, r, r * 0.7, P.CLIFF)
        face.ellipse(bx - r * 0.35, by - r * 0.35, r * 0.5, r * 0.3, P.CLIFF_L)
        face.rect(bx - r + 1, by - r * 0.8, bx + r - 2, by - r * 0.8, P.FAR_GRASS)
    for _ in range(9):                                       # moss trailing down from the rim
        mx = left + 8 + rnd() * (right - left - 16)
        length = 3 + int(rnd() * 7)
        face.line((mx, top + 3), (mx, top + 3 + length), P.KIT_GREEN_D)
        face.px(mx + 1, top + 3 + length // 2, P.FAR_GRASS)
    # grass cap
    face.rect(left + 6, top - 1, right - 6, top + 3, P.FAR_GRASS)
    face.rect(left + 6, top - 1, right - 6, top - 1, P.KIT_GREEN_L)
    face.rect(left + 6, top + 3, right - 6, top + 3, P.KIT_GREEN_D)
    for k in range(int(left + 7), int(right - 7), 3):          # tufts over the edge
        face.rect(k, top + 4, k + 1, top + 4 + (k * 7) % 3, P.FAR_GRASS)
        face.px(k + 1, top + 5 + (k * 7) % 3, P.KIT_GREEN_D)
    if notch:                                                # where the stream cuts the rim
        face.rect(notch[0] - 1, top - 1, notch[1] + 1, top + 3, P.CLIFF_D)
    outline_wrapped(face, P.CLIFF_DD, wrap=False)
    c.paste(face)


def rim_bushes(c: Canvas, xs: list, top: float, seed: int) -> None:
    """Small round bushes and trees standing on the cliff's rim, in the distant greens."""
    layer = Canvas(*c.size)
    for k, (bx, size) in enumerate(xs):
        canopy(layer, bx, top - size * 0.45, size * 1.6, size, seed + k, DISTANT, (2, 4))
    outline_wrapped(layer, P.CLIFF_DD, wrap=False)
    c.paste(layer)


def cascade(c: Canvas, x: float, top: float, bottom: float, w: int, seed: int) -> None:
    """A waterfall several px wide: a white lip, streaks of light water running down, a pale left edge and a
    darker right edge, and a foam cloud with spray at its foot (on `bottom`)."""
    c.rect(x, top, x + w - 1, bottom, P.WATER)
    c.rect(x, top, x, bottom, P.WATER_L)
    c.rect(x + w - 1, top, x + w - 1, bottom, P.WATER_D)
    for k in range(1, w - 1):                                # streaks, offset per column
        for y in range(int(top), int(bottom)):
            v = (y + k * 5 + seed) % 9
            if v < 4:
                c.px(x + k, y, P.WHITE if (k + seed) % 3 == 0 and v < 2 else P.WATER_L)
    c.rect(x - 1, top - 1, x + w, top, P.WHITE)               # the lip
    c.rect(x, top + 1, x + w - 1, top + 1, P.WATER_L)
    c.ellipse(x + w / 2 - 0.5, bottom, w / 2 + 3, 2.5, P.CLOUD_S)  # foam at the foot
    c.ellipse(x + w / 2 - 0.5, bottom - 1, w / 2 + 2, 2, P.WHITE)
    for dx, dy in ((-4, -3), (w + 2, -4), (-2, -5), (w, -2)):
        c.px(x + dx, bottom + dy, P.WHITE)
