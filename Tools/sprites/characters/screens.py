"""Pieces for the start, level-complete and game-over screens (docs/concept/Purrfectly Dangerous Pixel Game
Screens.png and Pixel Cat Game Over Screen.png, reference only).

No text is drawn here: the game sets the title and button labels as styled text over these pieces, so display
names stay in Lore.json. The wreaths leave their middle clear for that text."""
from __future__ import annotations

import math

import palette as P
from draw import Canvas, noise, see_through
from sprite import Sprite, single
from characters import hero as H
from characters.props import paw

LEAF_FRONT = (P.LEAF_Y, P.KIT_GREEN_L, P.KIT_GREEN, P.KIT_GREEN_D)
LEAF_BACK = (P.KIT_GREEN_L, P.KIT_GREEN, P.KIT_GREEN_D, P.KIT_GREEN_DD)


# --- wreaths -----------------------------------------------------------------------------------------

def leaf(c: Canvas, x: float, y: float, angle: float, length: float, width: float, cols=LEAF_FRONT,
         edge=P.KIT_GREEN_DD) -> None:
    """A rounded, pointed leaf from its stem at (x, y) toward `angle` (radians, 0 = right, y down): lit half,
    shaded half, a vein and a bright tip; with `edge`, it gets its own dark rim so overlapping leaves separate."""
    tip_c, light, mid, dark = cols
    dx, dy = math.cos(angle), math.sin(angle)
    nx, ny = -dy, dx
    layer = Canvas(*c.size) if edge else c

    def at(t, side):
        return (x + dx * length * t + nx * width / 2 * side, y + dy * length * t + ny * width / 2 * side)
    lit_first = ny < 0 or (abs(ny) < 0.2 and nx < 0)
    a_side = [at(0, 0), at(0.2, 0.8), at(0.5, 1), at(0.78, 0.6), at(1, 0)]
    b_side = [at(0, 0), at(0.2, -0.8), at(0.5, -1), at(0.78, -0.6), at(1, 0)]
    layer.poly(a_side, light if lit_first else mid)
    layer.poly(b_side, mid if lit_first else light)
    layer.line(at(0.1, 0), at(0.85, 0), dark)
    shade = b_side if lit_first else a_side
    layer.line(shade[2], shade[3], dark)
    hi = a_side if lit_first else b_side
    for i in range(1, 4):                                 # a light rim along the lit edge
        layer.line(hi[i], hi[i + 1] if i < 3 else at(0.92, 0), tip_c)
    layer.px(*at(0.92, 0), tip_c)
    if edge:
        c.paste(layer.outline(edge))


def flower(c: Canvas, x: float, y: float, petal=P.WHITE, centre=P.GOLD, shade=P.CREAM_D) -> None:
    """A five-petal flower about 7 px across, dark-rimmed so it reads on the leaves."""
    layer = Canvas(*c.size)
    for k in range(5):
        a = -math.pi / 2 + k * math.tau / 5
        px, py = x + math.cos(a) * 2, y + math.sin(a) * 2
        layer.rect(px - 0.5, py - 0.5, px + 0.5, py + 0.5, petal)
    layer.rect(x - 1, y - 1, x + 1, y + 1, petal)
    layer.px(x, y, centre)
    layer.px(x + 1, y + 2, shade)
    c.paste(layer.outline(P.KIT_GREEN_DD))


def cluster(c: Canvas, x: float, y: float, angle: float, spread: float, count: int, size: float, seed: int) -> None:
    """A fan of big leaves from one point: `count` leaves around `angle` (radians, y down) within `spread`,
    the outer ones darker and drawn first, so the bright middle leaves sit on top."""
    rnd = noise(seed)
    order = sorted(range(count), key=lambda k: -abs(k - (count - 1) / 2))
    for k in order:
        t = 0.5 if count == 1 else k / (count - 1)
        a = angle + (t - 0.5) * spread + (rnd() - 0.5) * 0.25
        length = size * (0.8 + rnd() * 0.35) * (1.0 - abs(t - 0.5) * 0.35)
        cols = LEAF_FRONT if abs(t - 0.5) < 0.3 else LEAF_BACK
        leaf(c, x - math.cos(a) * 2, y - math.sin(a) * 2, a, length, length * (0.6 + rnd() * 0.1), cols)


def vine_curl(c: Canvas, x: float, y: float, length: int, direction: int, seed: int) -> None:
    """A thin vine hanging and curling, with small leaves along it."""
    rnd = noise(seed)
    a = math.pi / 2
    for k in range(length):
        x += math.cos(a) * 1.0
        y += math.sin(a) * 1.0
        c.px(x, y, P.KIT_GREEN_DD if k % 4 else P.KIT_GREEN_D)
        if k % 4 == 2:
            side = 1 if (k // 4) % 2 else -1
            c.px(x + side, y, P.KIT_GREEN_L if rnd() > 0.3 else P.LEAF_Y)
            c.px(x + side, y + 1, P.KIT_GREEN)
        a -= direction * (0.05 + k * 0.012)


def leaves_around(c: Canvas, w: int, h: int, seed: int, size: float, top: float, bottom: float) -> None:
    """Big leaves peeking out round the outside of a title, pointing outward from a rounded-rectangle edge (no
    band behind them): dense and largest at the two ends, `bottom` (0-1) of the bottom edge, `top` of the top.
    The middle stays empty: the letters are the shape."""
    rnd = noise(seed)
    cx, cy = w / 2, h / 2
    ax, by = w / 2 - size * 1.15, h / 2 - size * 0.85
    count = int((w + h) / size * 2.4)
    for layer in (0, 1):
        for i in range(count):
            t = (i + 0.5 * layer + rnd() * 0.3) / count * math.tau
            ct, st = math.cos(t), math.sin(t)
            x = cx + ax * math.copysign(abs(ct) ** 0.5, ct)          # a squarish superellipse
            y = cy + by * math.copysign(abs(st) ** 0.5, st)
            a = math.atan2(math.copysign(abs(st) ** 0.5, st) / by, math.copysign(abs(ct) ** 0.5, ct) / ax)
            end = abs(math.cos(a))
            up, down = -math.sin(a), math.sin(a)
            if up > 0.75 and rnd() > top:
                continue
            if down > 0.75 and rnd() > bottom * (0.35 + 0.65 * abs(x - cx) / ax):
                continue
            length = size * (0.75 + rnd() * 0.35) * (1 + 0.35 * end) * (0.85 if layer == 0 else 1)
            a += (rnd() - 0.5) * 0.8
            cols = LEAF_BACK if layer == 0 else LEAF_FRONT
            leaf(c, x - math.cos(a) * length * 0.3, y - math.sin(a) * length * 0.3, a, length,
                 length * (0.6 + rnd() * 0.1), cols)
    # bushy ends: rows of big leaves fanning outward, outer rows first, so inner ones lie over their stems
    for side in (-1, 1):
        for row in range(3):
            n = 5 - row
            for k in range(n):
                f = (k + 0.5) / n
                y = h * (0.16 + 0.68 * f) + (rnd() - 0.5) * 3
                x = cx + side * (ax - row * size * 0.55 - abs(f - 0.5) * size * 0.8)
                a = (0 if side > 0 else math.pi) + side * (f - 0.5) * 1.6 + (rnd() - 0.5) * 0.5
                length = size * (1.15 + rnd() * 0.3 - row * 0.1)
                leaf(c, x - math.cos(a) * length * 0.25, y - math.sin(a) * length * 0.25, a, length,
                     length * (0.62 + rnd() * 0.1), LEAF_BACK if row == 0 else LEAF_FRONT)


def wreath(name: str, w: int, h: int, seed: int, size: float, flowers: list, vines: list, top: float = 0.35,
           bottom: float = 0.8) -> Sprite:
    """Leaves, vines and a few white flowers around the outside of a title; the middle is fully transparent."""
    c = Canvas(w, h)
    for (x, y, d, n) in vines:
        vine_curl(c, x, y, n, d, seed + int(x))
    leaves_around(c, w, h, seed, size, top, bottom)
    for x, y in flowers:
        flower(c, x, y)
    c.outline()
    return single(name, c)


def fans_around(c: Canvas, w: int, h: int, box: tuple, size: float, seed: int, top: float, bottom: float) -> None:
    """Big broad leaves (about `size` px long) rooted just inside a centred title box of `box` (w, h), so the
    lettering hides their stems: deep fans at the two ends, a row peeking above the top edge (behind the cat),
    `bottom` (0-1) of a row along the bottom. Nothing reaches the middle of the box."""
    rnd = noise(seed)
    bw, bh = box
    x0, x1, y0, y1 = (w - bw) / 2, (w + bw) / 2, (h - bh) / 2, (h + bh) / 2
    cy = h / 2

    def put(x, y, a, length, cols):
        leaf(c, x, y, a, length, length * (0.62 + rnd() * 0.1), cols)

    for side in (-1, 1):                                     # the ends: three columns, deepest drawn first
        for col in (2, 1, 0):
            step = 6
            y = y0 - 2 + col * 2
            while y <= y1 - 1:
                t = max(-1.1, min(1.1, (y - cy) / (bh / 2)))
                inset = 4 + col * 5 + abs(t) * 6                 # the root line curves in toward the corners
                x = x0 + inset if side < 0 else x1 - inset
                a = (math.pi - t * 1.15) if side < 0 else (t * 1.15)
                a += (rnd() - 0.5) * 0.45
                bulge = 1.3 - 0.45 * abs(t)                      # longest at mid-height: a rounded outer edge
                put(x, y, a, (size * (0.9 + rnd() * 0.25) + col * 4) * bulge, LEAF_BACK if col else LEAF_FRONT)
                y += step + rnd() * 2
    for layer, cols in ((0, LEAF_BACK), (1, LEAF_FRONT)):   # along the top, densest behind the cat
        x = x0 + 18 + layer * 5
        while x < x1 - 18:
            near = 1 - min(1.0, abs(x - w / 2) / (bw * 0.3))
            if rnd() < top * (0.35 + 0.65 * near):
                tilt = (x - w / 2) / (bw / 2) * 0.6 + (rnd() - 0.5) * 0.8
                put(x, y0 + 5 + rnd() * 2, -math.pi / 2 + tilt, size * (0.6 + 0.3 * near + rnd() * 0.25), cols)
            x += 7 + rnd() * 4
    x = x0 + 20
    while x < x1 - 20:                                       # along the bottom, denser toward the ends
        edge = abs(x - w / 2) / (bw / 2)
        if rnd() < bottom * (0.4 + 0.6 * edge):
            put(x, y1 - 5, math.pi / 2 + (rnd() - 0.5) * 0.9, size * (0.7 + rnd() * 0.25), LEAF_FRONT)
        x += 9


def big_wreath(name: str, w: int, h: int, box: tuple, size: float, seed: int, flowers: list, top: float = 0.9,
               bottom: float = 0.7) -> Sprite:
    """Big broad leaves round the outside of a title box, with small white flowers; the middle is transparent."""
    c = Canvas(w, h)
    fans_around(c, w, h, box, size, seed, top, bottom)
    for x, y in flowers:
        flower(c, x, y)
    c.outline()
    return single(name, c)


TITLE_CAT = (64, 40)


def title_cat_frame(eyes: str) -> Canvas:
    """The hero up close, peeking over the title: head and shoulders, both front paws on the bottom edge, the
    red cape flaring out to the left. Drawn at this size (not scaled up). `eyes`: open | half | closed."""
    w, h = TITLE_CAT
    c = Canvas(w, h)
    hx, hy = 39, 20                                          # head centre

    # cape: a broad red wedge out to the left from behind the shoulders, lit along its top, notched at the end
    cape = Canvas(w, h)
    cape.poly([(31, 23), (18, 17), (6, 14), (2, 17), (4, 24), (12, 31), (24, 36), (32, 36)], P.CAPE)
    cape.poly([(31, 23), (18, 17), (6, 14), (2, 17), (10, 20), (22, 24), (30, 27)], P.CAPE_L)
    cape.poly([(4, 24), (12, 31), (24, 36), (32, 36), (28, 31), (14, 27)], P.CAPE_D)
    cape.line((8, 21), (26, 30), P.CAPE_D)                     # a fold
    cape.poly([(1, 18), (5, 20), (2, 23)], P.CLEAR)           # swallow-tail notch
    c.paste(cape.outline())

    body = Canvas(w, h)
    # shoulders and chest under the head
    body.ellipse(hx, 35, 14, 7, P.GINGER)
    body.ellipse(hx + 1, 36, 6, 5, P.FUR_WHITE)
    body.rect(hx + 9, 32, hx + 14, 38, P.GINGER_D)
    # ears: tall, pink inside, lit on the left
    for ex, tip, outer in ((27, (26, 1), -1), (51, (53, 2), 1)):
        if outer < 0:
            body.poly([(22, 13), tip, (34, 7)], P.GINGER)
            body.poly([(25, 11), (27, 4), (31, 8)], P.PINK)
            body.line((23, 11), (26, 3), P.GINGER_L)
        else:
            body.poly([(44, 7), tip, (56, 14)], P.GINGER)
            body.poly([(47, 8), (52, 5), (53, 11)], P.PINK)
            body.line((54, 5), (55, 12), P.GINGER_D)
    # head: a wide rounded shape, lit top-left, shaded on the right and under the cheeks
    body.ellipse(hx, hy, 17, 12.5, P.GINGER)
    body.ellipse(hx - 1, hy + 4, 17.5, 9, P.GINGER)
    body.ellipse(hx - 5, hy - 6, 8, 4, P.GINGER_L)
    body.poly([(hx + 13, hy - 6), (hx + 18, hy + 2), (hx + 16, hy + 10), (hx + 11, hy + 12)], P.GINGER_D)
    # tabby stripes on the forehead and cheeks
    for x0, y0, y1 in ((hx - 9, hy - 11, hy - 7), (hx - 5, hy - 12, hy - 8), (hx + 6, hy - 12, hy - 8),
                       (hx + 10, hy - 11, hy - 7)):
        body.rect(x0, y0, x0 + 1, y1, P.GINGER_DD)
    for y in (hy + 1, hy + 4):
        body.rect(hx - 17, y, hx - 13, y, P.GINGER_DD)
        body.rect(hx + 15, y, hx + 17, y, P.GINGER_DD)
    # white blaze down the face into a broad muzzle
    body.poly([(hx - 1, hy - 12), (hx + 3, hy - 12), (hx + 5, hy - 2), (hx - 3, hy - 2)], P.FUR_WHITE)
    body.ellipse(hx + 1, hy + 6, 10, 6.5, P.FUR_WHITE)
    body.rect(hx - 7, hy + 10, hx + 9, hy + 12, P.FUR_WHITE_D)
    body.ellipse(hx + 1, hy + 5, 9, 5.5, P.FUR_WHITE)
    # cheeks
    body.rect(hx - 8, hy + 4, hx - 6, hy + 5, P.PINK)
    body.rect(hx + 8, hy + 4, hx + 10, hy + 5, P.PINK)
    # eyes: big and dark with two shines; half shut = lid over the top; shut = a curved line
    for ex in (hx - 8, hx + 7):
        if eyes == "closed":
            body.rect(ex - 2, hy + 1, ex + 2, hy + 1, P.BLACK)
            body.px(ex - 3, hy, P.BLACK)
            body.px(ex + 3, hy, P.BLACK)
            continue
        body.rect(ex - 2, hy - 4, ex + 2, hy + 2, P.BLACK)
        body.rect(ex - 3, hy - 3, ex + 3, hy + 1, P.BLACK)
        if eyes == "half":
            body.rect(ex - 3, hy - 4, ex + 3, hy - 2, P.GINGER)
            body.rect(ex - 3, hy - 1, ex + 3, hy - 1, P.GINGER_DD)
            body.px(ex - 1, hy, P.WHITE)
        else:
            body.rect(ex - 2, hy - 3, ex - 1, hy - 2, P.WHITE)
            body.px(ex + 1, hy + 1, P.WHITE)
            body.px(ex + 2, hy - 1, P.NAVY)
    # nose and "w" smile
    body.rect(hx, hy + 3, hx + 2, hy + 3, P.PINK)
    body.px(hx + 1, hy + 4, P.PINK_D)
    for x, y in ((hx - 2, hy + 6), (hx - 1, hy + 7), (hx, hy + 6), (hx + 1, hy + 5), (hx + 2, hy + 6), (hx + 3, hy + 7),
                 (hx + 4, hy + 6)):
        body.px(x, y, P.PINK_D)
    c.paste(body.outline())

    # front paws resting on the edge: round, orange with white toes, toe gaps
    paws = Canvas(w, h)
    for px_ in (27, 51):
        paws.ellipse(px_, 35, 5.5, 3.5, P.GINGER)
        paws.rect(px_ - 5, 36, px_ + 5, 38, P.FUR_WHITE)
        paws.rect(px_ - 4, 32, px_ + 2, 32, P.GINGER_L)
        for tx in (px_ - 2, px_ + 1):
            paws.rect(tx, 36, tx, 38, P.FUR_WHITE_D)
    c.paste(paws.outline())
    return c


def title_cat() -> Sprite:
    sprite = Sprite("title_cat", TITLE_CAT, ground=TITLE_CAT[1] - 1)
    sprite.add("blink", [title_cat_frame(e) for e in ("open", "open", "half", "closed")], fps=6)
    return sprite


def stone_wreath() -> Sprite:
    """`title_wreath_stone`: a mossy grey boulder with an arched crown behind "game over", with clusters of big
    leaves and small white five-petal flowers round its edge. Its plain middle is left for the text."""
    w, h = 250, 120
    c = Canvas(w, h)
    rnd = noise(91)
    size = 14
    fans_around(c, w, h, (206, 76), size, 92, 0.8, 0.7)
    slab = Canvas(w, h)
    cx, cy, ax, by = w / 2, h / 2 + 4, w / 2 - 22, h / 2 - 16
    for y in range(h):
        for x in range(w):
            u = (x + 0.5 - cx) / ax
            crown = 9 * max(0.0, 1 - u * u * 2.2)             # the arch rises in the middle
            v = (y + 0.5 - cy) / (by + (crown if y < cy else 0))
            lump = math.sin(x * 0.55) * 0.03 + math.sin(y * 0.8 + x * 0.2) * 0.03
            if abs(u) ** 4 + abs(v) ** 4 <= 1 + lump:
                slab.px(x, y, P.ROCK)
    px = slab.img.load()

    def solid(x, y):
        return 0 <= x < w and 0 <= y < h and px[int(x), int(y)][3]
    changes = []
    for y in range(h):
        for x in range(w):
            if not solid(x, y):
                continue
            if not solid(x, y - 2) or not solid(x - 2, y):
                changes.append((x, y, P.ROCK_L))
            elif not solid(x, y + 3) or not solid(x + 3, y):
                changes.append((x, y, P.ROCK_D))
    for x, y, col in changes:
        px[x, y] = col
    for k in range(30):                                      # lumps and chips in a band round the rim
        a = rnd() * math.tau
        rr = 0.86 + rnd() * 0.08
        x, y = cx + math.cos(a) * ax * rr, cy + math.sin(a) * by * rr * (1.25 if math.sin(a) < 0 else 1)
        if not solid(x, y):
            continue
        rad = 2 + rnd() * 2.5
        slab.ellipse(x, y, rad, rad * 0.7, P.ROCK_D)
        slab.ellipse(x - 0.6, y - 0.6, rad - 1, rad * 0.7 - 1, P.ROCK)
        slab.px(x - rad * 0.5, y - rad * 0.4, P.ROCK_L)
    for k in range(10):                                      # cracks
        a = rnd() * math.tau
        x, y = cx + math.cos(a) * ax * 0.9, cy + math.sin(a) * by * 0.85
        if solid(x, y):
            slab.line((x, y), (x + rnd() * 4 - 2, y + 3), P.ROCK_DD)
    c.paste(slab.outline())
    for x in range(int(cx - ax + 6), int(cx + ax - 6)):      # moss over the crown
        top = next((y for y in range(h) if solid(x, y)), None)
        if top is None:
            continue
        depth = 2 + (math.sin(x * 0.7) + 1) * 1.5 + (4 if x % 17 < 3 else 0)
        c.rect(x, top, x, top + depth, P.KIT_GREEN_D)
        c.rect(x, top, x, top + depth - 2, P.KIT_GREEN)
        if x % 3 == 0:
            c.px(x, top, P.KIT_GREEN_L)
        if x % 11 == 0:
            c.px(x, top - 1, P.LEAF_Y)
    # fans of leaves over the four corners of the slab and a sprig on its crown
    for x, y, a in ((30, 26, -2.3), (w - 30, 26, -0.85), (26, h - 32, 2.5), (w - 26, h - 32, 0.65)):
        cluster(c, x, y, a, 1.5, 4, 15, int(x + y))
    cluster(c, w / 2, 14, -math.pi / 2, 1.0, 3, 9, 7)
    for x, y in ((24, 22), (w - 30, 34), (14, 56), (w - 14, 68), (52, 12), (w - 56, 11), (34, h - 14), (w - 34, h - 18),
                 (w / 2 + 16, 13)):
        flower(c, x, y)
    c.outline()
    return single("title_wreath_stone", c)


# --- icons --------------------------------------------------------------------------------------------

def icons() -> list[Sprite]:
    out = []

    trophy = Canvas(16, 16)                                  # gold cup on a stem and plinth
    for side in (-1, 1):                                     # handles
        trophy.ellipse(7.5 + side * 5.5, 5, 2, 2.5, P.GOLD_D)
        trophy.rect(7.5 + side * 5.5 - 0.5, 4, 7.5 + side * 5.5 + 0.5, 5, P.CLEAR)
    trophy.poly([(2, 1), (13, 1), (12, 7), (10, 9), (5, 9), (3, 7)], P.GOLD)
    trophy.poly([(9, 1), (13, 1), (12, 7), (10, 9), (9, 9)], P.GOLD_D)
    trophy.rect(2, 1, 13, 1, P.YELLOW)
    trophy.line((4, 2), (5, 6), P.YELLOW)
    trophy.rect(6, 9, 9, 11, P.GOLD_D)
    trophy.rect(7, 9, 7, 11, P.GOLD)
    trophy.rect(4, 12, 11, 14, P.BROWN)
    trophy.rect(4, 12, 11, 12, P.BROWN_L)
    out.append(single("icon_trophy", trophy.outline()))

    cat = Canvas(16, 16)                                     # black cat head, white eyes and mouth
    cat.poly([(1, 7), (2, 0), (6, 4)], P.SLATE)
    cat.poly([(14, 7), (13, 0), (9, 4)], P.SLATE)
    cat.ellipse(7.5, 8.5, 6.5, 5.5, P.SLATE)
    cat.poly([(2, 5), (2.5, 2), (5, 4)], P.NIGHT)
    cat.poly([(13, 5), (12.5, 2), (10, 4)], P.NIGHT)
    cat.rect(4, 4, 11, 4, P.GREY_D)                          # sheen on the crown
    for ex in (4, 10):                                       # happy closed eyes
        cat.px(ex, 8, P.WHITE)
        cat.px(ex + 1, 7, P.WHITE)
        cat.px(ex + 2, 8, P.WHITE)
    cat.px(6, 11, P.WHITE)
    cat.px(7, 12, P.WHITE)
    cat.px(8, 12, P.WHITE)
    cat.px(9, 11, P.WHITE)
    cat.px(3, 10, P.PINK_D)
    cat.px(12, 10, P.PINK_D)
    out.append(single("icon_cat", cat.outline()))

    retry = Canvas(16, 16)                                   # a thick ring, open at the top right, arrowhead
    for y in range(16):
        for x in range(16):
            dx, dy = x + 0.5 - 8, y + 0.5 - 9
            d = math.hypot(dx, dy)
            ang = math.atan2(dy, dx)
            if 3.0 <= d <= 6.2 and not (-1.5 < ang < 0.1):
                retry.px(x, y, P.GINGER_L if d < 4.1 else P.GINGER if d < 5.3 else P.GINGER_D)
    retry.poly([(8, -0.5), (13, 3.5), (8, 7.5)], P.GINGER)
    retry.line((8, 1), (11, 3.5), P.GINGER_L)
    out.append(single("icon_retry", retry.outline()))

    home = Canvas(16, 16)                                    # cream house, orange roof, brown door
    home.rect(3, 7, 12, 14, P.CREAM)
    home.rect(10, 7, 12, 14, P.CREAM_D)
    home.rect(10, 1, 11, 5, P.BROWN)                          # chimney
    home.poly([(-0.5, 8), (7.5, 0.5), (15.5, 8)], P.GINGER)
    home.poly([(7.5, 0.5), (15.5, 8), (12, 8)], P.GINGER_D)
    home.line((1, 7), (7.5, 1.5), P.GINGER_L)
    home.rect(6, 10, 9, 14, P.BROWN)
    home.rect(6, 10, 7, 14, P.BROWN_L)
    out.append(single("icon_home", home.outline()))

    play = Canvas(16, 16)                                    # cream play triangle
    play.poly([(3, 1), (14, 7.5), (3, 14)], P.CREAM)
    play.poly([(3, 9), (14, 7.5), (3, 14)], P.CREAM_D)
    play.line((4, 2), (4, 8), P.WHITE)
    out.append(single("icon_play", play.outline()))

    paw_c = Canvas(16, 16)                                   # orange paw print: a big pad and four toes
    paw_c.ellipse(7.5, 12, 3.6, 2.6, P.GINGER)
    paw_c.rect(6, 10, 8, 10, P.GINGER_L)
    for x, y in ((1.9, 7), (4.9, 2.6), (10.1, 2.6), (13.1, 7)):
        paw_c.ellipse(x, y, 1.2, 1.5, P.GINGER)
        paw_c.px(x - 0.5, y - 1, P.GINGER_L)
    out.append(single("icon_paw", paw_c.outline()))

    lock = Canvas(16, 16)                                    # padlock: steel shackle, gold body, keyhole
    lock.ellipse(7.5, 5, 4, 4, P.GREY)
    lock.ellipse(7.5, 5, 2, 2.4, P.CLEAR)
    lock.rect(5.5, 5, 9.5, 7, P.CLEAR)
    lock.px(4, 4, P.GREY_L)
    lock.px(5, 2, P.GREY_L)
    lock.rect(2, 7, 13, 14, P.GOLD)
    lock.rect(10, 7, 13, 14, P.GOLD_D)
    lock.rect(2, 7, 13, 7, P.YELLOW)
    lock.ellipse(7.5, 10, 1, 1, P.BROWN_D)
    lock.rect(7, 10, 8, 12, P.BROWN_D)
    out.append(single("icon_lock", lock.outline()))
    return out


# --- celebration bits ------------------------------------------------------------------------------

def confetti() -> list[Sprite]:
    """A paper piece tumbling: spins in the plane while flipping, so it narrows and shows its darker back."""
    out = []
    for name, front, back in (("red", P.CAPE_L, P.RED_D), ("yellow", P.YELLOW, P.GOLD_D), ("blue", P.BLUE, P.BLUE_D),
                              ("green", P.KIT_GREEN_L, P.KIT_GREEN_D)):
        sprite = Sprite(f"confetti_{name}", (8, 8))
        frames = []
        for i in range(6):
            c = Canvas(8, 8)
            spin = i / 6 * math.pi                           # half a turn in the plane per loop
            flip = math.cos(i / 6 * math.tau)                 # one full flip per loop
            half_l, half_w = 3.0, 1.6 * max(0.35, abs(flip))
            dx, dy = math.cos(spin), math.sin(spin)
            nx, ny = -dy, dx
            pts = [(3.5 + dx * sx * half_l + nx * sy * half_w, 3.5 + dy * sx * half_l + ny * sy * half_w)
                   for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            c.poly(pts, front if flip > 0 else back)
            if flip > 0.5:
                c.px(3.5 - dx * 2 - nx * 0.5, 3.5 - dy * 2 - ny * 0.5, P.WHITE)
            frames.append(c)
        sprite.add("loop", frames, fps=12)
        out.append(sprite)
    return out


def sparkle_big() -> Sprite:
    """A four-point twinkle that swells and shrinks."""
    sprite = Sprite("sparkle_big", (12, 12))
    frames = []
    for i, arm in enumerate((2, 4, 5, 3)):
        c = Canvas(12, 12)
        x = y = 5.5
        c.rect(x - 1, y - 1, x + 1, y + 1, P.YELLOW)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for k in range(1, arm + 1):
                col = P.WHITE if k < arm - 1 else P.YELLOW if k < arm else P.GOLD
                c.px(x + dx * (k + 0.5), y + dy * (k + 0.5), col)
        c.px(x - 0.5, y - 0.5, P.WHITE)
        c.px(x + 0.5, y + 0.5, P.WHITE)
        if arm >= 4:
            for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                c.px(x + dx * 1.5, y + dy * 1.5, P.YELLOW)
        frames.append(c)
    sprite.add("loop", frames, fps=8)
    return sprite


def sunburst() -> Sprite:
    """Soft pale rays fanning out behind the cheering cat; see-through, fading toward the ends."""
    size = 160
    c = Canvas(size, size)
    px = c.img.load()
    mid = (size - 1) / 2
    rays = 14
    for y in range(size):
        for x in range(size):
            dx, dy = x - mid, y - mid
            d = math.hypot(dx, dy)
            if d > mid:
                continue
            a = math.atan2(dy, dx) / math.tau * rays
            frac = a - math.floor(a)
            t = d / mid
            fall = 1 - t
            if d < 22:                                       # bright glow in the middle
                alpha = 90 if d < 14 else 70
                px[x, y] = (*P.CREAM[:3], alpha)
            elif frac < 0.5 and fall > 0.08:
                # three banded alpha steps, so the rays read as pixel art rather than a smooth gradient
                alpha = 64 if fall > 0.6 else 44 if fall > 0.35 else 26
                colour = P.YELLOW if frac < 0.12 or frac > 0.38 else P.CREAM
                px[x, y] = (*colour[:3], alpha)
    return single("sunburst", c)


def silhouette() -> Sprite:
    """The hero's idle pose filled in dark, for a locked skin."""
    frame = H.hero_frame(H.HeroPose(cape=88, cape_len=12, ripple=16, tail=-70, curl=16))
    out = frame.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r_, g, b, a = px[x, y]
            if a:
                px[x, y] = P.OUTLINE if (r_, g, b, 255) == P.OUTLINE else P.SLATE
    c = Canvas(*out.size)
    c.paste(out)
    for y in range(out.height):                              # a faint rim of light on the top-left edges
        for x in range(out.width):
            if px[x, y] == P.SLATE and (y == 0 or px[x, y - 1] == P.OUTLINE) and (x == 0 or px[x - 1, y] == P.OUTLINE):
                c.px(x, y, P.GREY_D)
    return single("cat_silhouette", c, cx=H.CX, ground=H.GROUND)


def sign_cat() -> Sprite:
    """A wooden signpost with a cat-face plaque; the post stands on the bottom row."""
    w, h = 18, 22
    c = Canvas(w, h)
    c.rect(7, 10, 9, h - 2, P.PLANK_D)                         # post
    c.rect(7, 10, 7, h - 2, P.PLANK)
    c.rect(7, 2, 9, 3, P.PLANK_D)                             # post top above the plaque
    c.rect(1, 3, 16, 12, P.PLANK)                             # plaque
    c.rect(1, 3, 16, 3, P.PLANK_L)
    c.rect(1, 3, 1, 12, P.PLANK_L)
    c.rect(1, 12, 16, 12, P.PLANK_D)
    c.rect(16, 4, 16, 12, P.PLANK_D)
    c.line((2, 7), (6, 7), P.PLANK_D)                         # wood grain
    c.line((12, 9), (15, 9), P.PLANK_D)
    for x, y in ((2, 4), (15, 4), (2, 11), (15, 11)):         # nail heads
        c.px(x, y, P.BARK_DD)
    # cat face burnt into the board
    c.poly([(5, 6), (5.5, 4), (7.5, 5.5)], P.BARK_D)
    c.poly([(12, 6), (11.5, 4), (9.5, 5.5)], P.BARK_D)
    c.ellipse(8.5, 8, 3.5, 2.6, P.BARK_D)
    c.px(7, 8, P.GOLD)
    c.px(10, 8, P.GOLD)
    c.px(8.5, 9.5, P.PLANK_L)
    c.rect(5, h - 2, 11, h - 2, P.KIT_GREEN)                  # tuft of grass at the foot
    c.px(6, h - 3, P.KIT_GREEN_L)
    c.px(10, h - 3, P.KIT_GREEN)
    c.outline()
    return single("sign_cat", c, ground=h - 1, cx=8)


def life_lost() -> Sprite:
    """A dark cat head silhouette with grey "x x" eyes: one per lost heart on the game-over screen."""
    c = Canvas(18, 16)
    c.poly([(1.5, 9), (2.5, 1), (7, 5)], P.NIGHT)
    c.poly([(15.5, 9), (14.5, 1), (10, 5)], P.NIGHT)
    c.ellipse(8.5, 9, 7.5, 5.5, P.NIGHT)
    c.rect(4, 5, 13, 5, P.SLATE)
    c.px(3, 3, P.SLATE)
    c.px(14, 3, P.SLATE)
    for ex in (4, 11):
        for k in range(3):
            c.px(ex + k, 7 + k, P.GREY)
            c.px(ex + 2 - k, 7 + k, P.GREY)
    c.px(8, 12, P.GREY_D)
    c.px(9, 12, P.GREY_D)
    c.outline()
    return single("life_lost", c)


def leaf_drift() -> Sprite:
    """A green leaf tumbling as it drifts: turns over and back across four frames."""
    sprite = Sprite("leaf_drift", (10, 8))
    frames = []
    for i, (a, squash) in enumerate(((-0.35, 1.0), (0.15, 0.55), (0.5, 1.0), (0.1, 0.6))):
        c = Canvas(10, 8)
        dx, dy = math.cos(a), math.sin(a)
        x0, y0 = 4.5 - dx * 3.5, 3.5 - dy * 3.5
        leaf(c, x0, y0, a, 7.5, 4.6 * squash, LEAF_FRONT if i % 2 == 0 else LEAF_BACK)
        c.outline()
        frames.append(c)
    sprite.add("loop", frames, fps=6)
    return sprite


def stars_dizzy() -> Sprite:
    """Three small yellow twinkles circling (over the knocked-out cat's head)."""
    sprite = Sprite("stars_dizzy", (16, 8))
    frames = []
    for i in range(4):
        c = Canvas(16, 8)
        for k in range(3):
            a = i / 4 * math.tau / 3 + k * math.tau / 3
            x, y = 7.5 + math.cos(a) * 5.5, 4 + math.sin(a) * 1.8
            front = math.sin(a) > -0.3
            c.px(x, y, P.WHITE if front else P.YELLOW)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c.px(x + dx, y + dy, P.YELLOW if front else P.GOLD)
        frames.append(c)
    sprite.add("loop", frames, fps=8)
    return sprite


def build() -> list[Sprite]:
    return [
        big_wreath("title_wreath", 280, 110, (230, 64), 15, 11,
                   flowers=[(14, 44), (266, 62), (40, 92), (238, 90), (120, 18), (166, 16), (22, 70), (258, 36)]),
        big_wreath("title_wreath_small", 240, 96, (192, 54), 13, 23,
                   flowers=[(12, 40), (228, 56), (36, 80), (204, 78), (104, 16), (140, 15)]),
        title_cat(),
        stone_wreath(),
        *icons(),
        *confetti(),
        sparkle_big(),
        sunburst(),
        silhouette(),
        sign_cat(),
        life_lost(),
        leaf_drift(),
        stars_dizzy(),
    ]
