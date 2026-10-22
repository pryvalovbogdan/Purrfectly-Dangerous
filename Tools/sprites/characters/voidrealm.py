"""World 5's environment, the Void, after docs/concept/Void Cat Final Boss Tileset.png (reference only): a cosmic void
with a spiral galaxy, a ringed planet and a black-hole portal ring; floating rock islands with ruined gothic towers; the
huge shadowy Void Cat watching with glowing eyes and claws; ruins and chained platforms; violet stone with gold trim and
magenta void energy. Same names, sizes and tiling contracts as the forest's (docs/sprite-spec.md), with `void`."""
from __future__ import annotations

import math

import palette as P
from characters.cataclysm import smoke_band
from characters.forest import platform
from characters.islands import finish, slab_top, wedge
from characters.meowseum import brick, brick_row, glow
from characters.scenery import LAYER_W, flat, ground, smooth_sky
from characters.waterfall import colour_at, face, rock
from draw import Canvas, noise, see_through
from sprite import Sprite, single
import woodland as W

BRICK = (P.VD_BRICK_L, P.VD_BRICK, P.VD_BRICK_D)
BRICK_DARK = (P.VD_BRICK, P.VD_BRICK_D, P.VD_BRICK_DD)
SPECKS = (P.VD_BRICK_DD, P.VD_CRYSTAL_D, P.VD_BRICK_D)


def rgba(col, a: int):
    return (col[0], col[1], col[2], a)


def crystal(c: Canvas, x: float, base: float, h: float, down: bool = False) -> None:
    """A violet crystal shard standing on `base` (or hanging from it when `down`)."""
    s = 1 if down else -1
    c.poly([(x - 1.5, base), (x, base + s * h), (x + 1.5, base)], P.VD_CRYSTAL)
    c.line((x - 0.5, base), (x - 0.2, base + s * (h - 1)), P.VD_CRYSTAL_L)
    c.px(x + 1, base + s, P.VD_CRYSTAL_D)


def stars(c: Canvas, seed: int, count: int, y1: float) -> None:
    rnd = noise(seed)
    for _ in range(count):
        x, y = rnd() * c.size[0], rnd() * y1
        c.px(x, y, P.VD_STAR if rnd() > 0.4 else P.VD_PLANET_L)
        if rnd() > 0.88:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c.px(x + dx, y + dy, rgba(P.VD_NEB_L, 120))


def nebula(c: Canvas, y: float, amp: float, thick: float, seed: int, cols, alpha: int, phase: float = 0) -> None:
    """A streak of glowing nebula across the strip (whole sine cycles, so it tiles), blended at `alpha`."""
    band = Canvas(*c.size)
    rnd = noise(seed)
    light, body = cols
    for x in range(c.size[0]):
        t = x / c.size[0] * 2 * math.pi
        yc = y + amp * math.sin(t * 2 + phase) + amp * 0.4 * math.sin(t * 5 + 1)
        w = thick * (0.6 + 0.4 * math.sin(t * 3 + phase))
        band.rect(x, yc - w, x, yc + w, body)
        band.rect(x, yc - w * 0.4, x, yc + w * 0.3, light)
        if rnd() > 0.93:
            band.px(x, yc + (rnd() - 0.5) * w * 3, P.VD_STAR)
    c.paste(see_through(band.img, alpha))


# --- parallax ------------------------------------------------------------------------------------------

def galaxy(c: Canvas, x: float, y: float, r: float) -> None:
    glow(c, x, y, r + 4, r * 0.6 + 2, P.VD_NEB_D, 60)
    for arm in (0, math.pi):
        for k in range(40):
            t = k / 40
            a = arm + t * 4.2
            rad = 1 + t * r
            c.px(x + math.cos(a) * rad, y + math.sin(a) * rad * 0.5, P.VD_NEB_L if t < 0.4 else P.VD_NEB)
    glow(c, x, y, 3, 2, P.VD_ENERGY_W, 200)
    c.px(x, y, P.VD_ENERGY_W)


def ringed_planet(c: Canvas, x: float, y: float, r: float) -> None:
    def ring(front: bool):
        for k in range(72):
            a = k / 72 * 2 * math.pi
            px, py = x + math.cos(a) * r * 2.1, y + math.sin(a) * r * 0.55 - math.cos(a) * r * 0.25
            if (math.sin(a) > 0) == front:
                c.px(px, py, P.VD_RING if front else P.VD_PLANET_D)
    ring(False)
    c.ellipse(x, y, r, r, P.VD_PLANET)
    c.ellipse(x - 1, y - 1, r - 1.5, r - 1.5, P.VD_PLANET_L)
    c.ellipse(x + 1.5, y + 1.5, r - 2.5, r - 2.5, P.VD_PLANET)
    ring(True)


def portal(c: Canvas, x: float, y: float, r: float) -> None:
    """The black-hole portal: a swirling magenta ring of light around a black core."""
    for rr, a in ((r + 14, 26), (r + 8, 50), (r + 3, 90)):
        glow(c, x, y, rr, rr, P.VD_NEB, a)
    c.ellipse(x, y, r + 2, r + 2, P.VD_RING)
    c.ellipse(x, y, r + 0.5, r + 0.5, P.VD_NEB)
    c.ellipse(x + 0.5, y + 0.5, r - 1, r - 1, P.VD_HOLE)
    for k in range(60):                                                   # swirling streaks feeding the ring
        a = k / 60 * 2 * math.pi
        rad = r + 3 + (k % 7)
        c.px(x + math.cos(a) * rad, y + math.sin(a) * rad, P.VD_NEB_L if k % 3 else P.VD_ENERGY_W)


def void_clouds() -> Canvas:
    """The 150-tall layer on the ground line: stars, nebula streaks, the galaxy, a ringed planet and the portal."""
    c = Canvas(LAYER_W, 150)
    stars(c, 801, 80, 140)
    nebula(c, 40, 10, 6, 802, (P.VD_NEB, P.VD_NEB_D), 110)
    nebula(c, 92, 8, 8, 803, (P.VD_NEB_B, P.VD_SKY_HAZE), 120, 1.5)
    galaxy(c, 50, 30, 16)
    ringed_planet(c, 140, 22, 6)
    portal(c, 244, 44, 20)
    return c


def void_puffs() -> Canvas:
    c = Canvas(LAYER_W, 120)
    stars(c, 804, 70, 118)
    nebula(c, 60, 14, 8, 805, (P.VD_NEB_D, P.VD_SKY_L), 100, 2.5)
    return c


def ruined_tower(c: Canvas, x: float, base: float, w: float, h: float, col, window=None) -> None:
    c.rect(x - w / 2, base - h, x + w / 2, base, col)
    for k in range(int(w // 3) + 1):                                     # broken top
        bx = x - w / 2 + k * 3
        c.rect(bx, base - h - (k * 5) % 4 - 1, bx + 1, base - h, col)
    if window:
        c.ellipse(x, base - h * 0.6, w * 0.22, w * 0.3, window)
        c.rect(x - w * 0.22, base - h * 0.6, x + w * 0.22, base - h * 0.45, window)


def floating_rock(c: Canvas, x: float, y: float, w: float, col, rim) -> None:
    c.poly([(x - w / 2, y), (x + w / 2, y), (x + w / 3, y + w * 0.35), (x + 2, y + w * 0.75),
            (x - w / 4, y + w * 0.4)], col)
    c.rect(x - w / 2, y - 1, x + w / 2, y, rim)


def void_cat(c: Canvas, x: float, base: float) -> None:
    """The Void Cat's shadow looming behind the world: a huge head with tall ears, glowing eyes high above the
    ruins and a faint grin, and two clawed paws; darker than the sky so it stays behind everything."""
    col, edge = P.VD_SIL, P.VD_SIL_L
    hy = base - 92                                                          # head centre
    c.ellipse(x, hy, 52, 40, col)
    c.poly([(x - 46, hy - 16), (x - 40, base - 149), (x - 16, hy - 32)], col)        # ears
    c.poly([(x + 46, hy - 16), (x + 40, base - 149), (x + 16, hy - 32)], col)
    c.ellipse(x, base - 30, 74, 34, col)                                    # shoulders and chest
    for side in (-1, 1):                                                    # paws with claws
        px = x + side * 82
        c.ellipse(px, base - 18, 18, 13, col)
        for k in range(4):
            cx = px - 10 + k * 7
            c.poly([(cx - 1.5, base - 10), (cx + 1.5, base - 10), (cx + side * 2, base - 1)], P.VD_NEB_D)
            c.px(cx + side * 2, base - 2, P.VD_NEB)
    c.line((x - 40, base - 149), (x - 46, hy - 16), edge)                   # rim light on the ears
    c.line((x + 40, base - 149), (x + 46, hy - 16), edge)
    c.line((x - 30, hy - 36), (x + 30, hy - 36), edge)
    for side in (-1, 1):                                                    # eyes
        ex, ey = x + side * 19, hy - 6
        glow(c, ex, ey, 14, 8, P.VD_NEB_D, 60)        # dimmer than the boss's own eyes, so the boss leads
        c.poly([(ex - side * 11, ey + 2), (ex + side * 9, ey - 5), (ex + side * 10, ey + 1), (ex - side * 5, ey + 5)],
               P.VD_NEB_D)
        c.poly([(ex - side * 7, ey + 2), (ex + side * 6, ey - 3), (ex + side * 6, ey + 1), (ex - side * 3, ey + 3)],
               P.VD_NEB)
    c.line((x - 12, hy + 18), (x, hy + 22), edge)                           # a faint grin
    c.line((x, hy + 22), (x + 12, hy + 18), edge)
    for k in range(3):                                                      # whiskers
        c.line((x - 22, hy + 12 + k * 3), (x - 50, hy + 8 + k * 5), edge)
        c.line((x + 22, hy + 12 + k * 3), (x + 50, hy + 8 + k * 5), edge)


def void_far() -> Canvas:
    """The Void Cat looming in the middle; floating rock islands with ruined towers either side."""
    h = 150
    c = Canvas(LAYER_W, h)
    void_cat(c, 160, h)
    for x, y, w, th in ((26, 70, 30, 26), (294, 60, 28, 32), (40, 112, 20, 16), (280, 108, 22, 18)):
        def isle(px, y=y, w=w, th=th):
            floating_rock(c, px, y, w, P.VD_SIL_L, P.VD_BRICK_D)
            ruined_tower(c, px - w / 5, y - 1, 7, th, P.VD_SIL_L, P.HM_GLASS_D)
            ruined_tower(c, px + w / 4, y - 1, 5, th * 0.6, P.VD_SIL_L)
        W.wrapped(isle, x)
    rnd = noise(811)
    for _ in range(14):                                                    # drifting rock chunks
        x, y, r = rnd() * LAYER_W, 20 + rnd() * 110, 1.5 + rnd() * 3
        W.wrapped(lambda px, y=y, r=r: c.ellipse(px, y, r, r * 0.8, P.VD_SIL_L), x)
    return W.haze(c, P.VD_SKY, 0.18)


def stained_window(c: Canvas, x: float, top: float, w: float, h: float) -> None:
    shape = [(x - w / 2, top + h), (x - w / 2, top + w / 2), (x, top), (x + w / 2, top + w / 2), (x + w / 2, top + h)]
    c.poly([(px + (1 if px > x else -1) * 2, py - (2 if py < top + w / 2 else 0)) for px, py in shape], P.VD_BRICK)
    glass = Canvas(*c.size)
    glass.poly(shape, P.HM_GLASS_D)
    for k, gy in enumerate(range(int(top - 2), int(top + h), 4)):
        for gx in range(int(x - w / 2) + 1, int(x + w / 2), 3):
            glass.rect(gx, gy + 1, gx + 1, gy + 2, (P.HM_GLASS, P.VD_NEB_L, P.VD_NEB_B)[(gx // 3 + k) % 3])
    mask = Canvas(*c.size)
    mask.poly(shape, P.WHITE)
    glass.img.putalpha(mask.img.getchannel("A"))
    c.paste(glass)
    c.line((x, top + 1), (x, top + h), P.VD_BRICK_DD)


def pillar(c: Canvas, x: float, top: float, base: float, w: float, brazier: bool) -> None:
    c.rect(x - w / 2, top, x + w / 2, base, P.VD_BRICK_D)
    c.rect(x - w / 2, top, x - w / 2 + 1, base, P.VD_BRICK)
    for y in range(int(top + 5), int(base), 6):
        c.line((x - w / 2, y), (x + w / 2, y), P.VD_BRICK_DD)
    c.rect(x - w / 2 - 2, top - 2, x + w / 2 + 2, top, P.VD_BRICK)
    c.rect(x - w / 2 - 2, top - 2, x + w / 2 + 2, top - 2, P.GOLD_D)
    if brazier:
        c.rect(x - 3, top - 5, x + 3, top - 3, P.GOLD_D)
        c.poly([(x - 2.5, top - 5), (x, top - 13), (x + 2.5, top - 5)], P.VD_NEB)
        c.poly([(x - 1, top - 5), (x, top - 10), (x + 1, top - 5)], P.VD_NEB_L)
        glow(c, x, top - 8, 7, 6, P.VD_NEB, 60)


def void_near() -> Canvas:
    """Ruins in front of the void: a broken gothic wall with stained glass, pillars with violet braziers, and
    floating platforms hanging on chains."""
    h = 130
    c = Canvas(LAYER_W, h)
    stone = Canvas(LAYER_W, h)

    def ruin_wall(px):
        stone.poly([(px, h), (px, h - 64), (px + 8, h - 74), (px + 20, h - 70), (px + 34, h - 82), (px + 52, h - 66),
                    (px + 60, h - 56), (px + 60, h)], P.VD_BRICK_D)
        for y in range(h - 70, h, 6):
            stone.line((px, y), (px + 60, y), P.VD_BRICK_DD)
        stained_window(stone, px + 18, h - 58, 12, 34)
        stained_window(stone, px + 42, h - 50, 10, 26)
    W.wrapped(ruin_wall, 10)
    for x, top, w, braz in ((96, h - 60, 10, True), (176, h - 40, 8, False), (204, h - 70, 12, True),
                            (306, h - 50, 9, True)):
        W.wrapped(lambda px, top=top, w=w, braz=braz: pillar(stone, px, top, h, w, braz), x)
    for x, y, w in ((126, 44, 34), (254, 30, 40)):                         # chained floating platforms
        def plat(px, y=y, w=w):
            for cx in (px - w / 2 + 3, px + w / 2 - 3):
                for yy in range(0, int(y), 2):
                    stone.rect(cx, yy, cx + 1, yy, P.IRON_D if (yy // 2) % 2 else P.IRON)
            floating_rock(stone, px, y + 4, w, P.VD_BRICK_D, P.VD_BRICK)
            stone.rect(px - w / 2, y, px + w / 2, y + 4, P.VD_BRICK)
            stone.rect(px - w / 2, y, px + w / 2, y, P.VD_BRICK_TOP)
            stone.rect(px - w / 2, y + 4, px + w / 2, y + 4, P.GOLD_D)
            for k in range(3):
                crystal(stone, px - w / 4 + k * w / 4, y + 8 + k % 2 * 2, 4 + k, down=True)
        W.wrapped(plat, x)
    c.paste(stone)
    return W.haze(c, P.VD_SKY, 0.12)


def void_bushes() -> Canvas:
    """The front strip: low dark rocks with violet crystals growing between them."""
    h = 22
    c = Canvas(LAYER_W, h)
    rnd = noise(831)
    x = 0
    while x < LAYER_W:
        w = 10 + rnd() * 16
        rh = 4 + rnd() * 8
        has_crystal = rnd() > 0.45

        def rocks(px, w=w, rh=rh, has_crystal=has_crystal):
            c.poly([(px - w / 2, h - 1), (px - w / 3, h - rh), (px + 1, h - rh - 2), (px + w / 3, h - rh + 1),
                    (px + w / 2, h - 1)], P.VD_SIL)
            c.line((px - w / 3, h - rh), (px + 1, h - rh - 2), P.VD_SIL_L)
            if has_crystal:
                glow(c, px + w / 4, h - 4, 5, 4, P.VD_CRYSTAL, 50)
                crystal(c, px + w / 4, h - 1, 7)
                crystal(c, px + w / 4 + 3, h - 1, 4)
        W.wrapped(rocks, x + w / 2)
        x += w + 8 + rnd() * 12
    return c


# --- ground --------------------------------------------------------------------------------------------

def courses(c: Canvas, y0: int, count: int) -> None:
    for k in range(count):
        brick_row(c, y0 + k * 6, 6, [16, 16], 8 if k % 2 else 0, BRICK_DARK, 840 + k % 6, 32)


def glow_crack(c: Canvas, x: float, y: float, steps: list, hot: bool) -> None:
    for dx, dy in steps:
        x, y = x + dx, y + dy
        c.px(x, y, P.VD_NEB if hot else P.VD_NEB_D)
    c.px(x, y, P.VD_NEB_L if hot else P.VD_NEB)


def void_ground(c: Canvas) -> None:
    """Dark violet bricks: a lit edge on capstones with a gold trim line, a glowing crack and a crystal in the
    capstone face, then 6-row courses that run on into the earth."""
    c.rect(0, 0, 31, 47, P.VD_BRICK_DD)
    brick_row(c, 0, 12, [16, 16], 4, BRICK, 851, 32)
    c.rect(0, 0, 31, 0, P.VD_BRICK_TOP)
    c.rect(0, 1, 31, 1, P.VD_BRICK_L)
    c.rect(0, 2, 31, 2, P.GOLD_D)                                         # gold trim
    for x in range(2, 32, 8):
        c.px(x, 2, P.GOLD)
    courses(c, 12, 6)
    glow_crack(c, 10, 5, [(0, 0), (1, 1), (0, 1), (1, 1)], hot=True)
    glow_crack(c, 22, 30, [(0, 0), (1, 1), (-1, 1)], hot=False)
    crystal(c, 26, 11, 4)                                                  # a crystal in a capstone joint


def void_earth(c: Canvas) -> None:
    c.rect(0, 0, 31, 35, P.VD_BRICK_DD)
    courses(c, 0, 6)
    glow_crack(c, 13, 14, [(0, 0), (1, 1), (0, 1)], hot=False)


# --- cosmic abyss pit (the forest waterfall-pit contract) ----------------------------------------------

def pit_walls() -> list[Sprite]:
    out = []
    for name, offset in (("ravine_void", 2), ("ravine_void_b", 0)):
        c = Canvas(8, 16)
        c.rect(0, 0, 6, 15, P.VD_BRICK_DD)
        for y0, off in ((0, offset), (8, 4 - offset)):
            brick(c, -8 + off, y0, -1 + off, y0 + 6, BRICK_DARK)
            brick(c, off, y0, 6, y0 + 6, BRICK)
        c.rect(7, 0, 7, 15, P.VD_SIL_D)
        c.px(6, 4 + offset, P.VD_CRYSTAL)                                  # crystal glints on the pit side
        c.px(6, 12 - offset, P.VD_NEB_D)
        out.append(single(name, c))
    return out


def pit_rim() -> Sprite:
    """12x24 left top cap: the lit edge and gold trim (row 0 = ground surface) on a capstone, and a cluster of
    crystals growing over the edge into the pit."""
    c = Canvas(12, 24)
    c.rect(0, 0, 6, 23, P.VD_BRICK_DD)
    brick(c, -4, 0, 8, 11, BRICK)
    c.rect(0, 0, 8, 0, P.VD_BRICK_TOP)
    c.rect(0, 1, 8, 1, P.VD_BRICK_L)
    c.rect(0, 2, 8, 2, P.GOLD_D)
    c.px(4, 2, P.GOLD)
    for y0 in (12, 18):
        brick(c, 0, y0, 6, y0 + 5, BRICK_DARK)
    c.rect(7, 12, 7, 23, P.VD_SIL_D)
    glow(c, 9, 12, 4, 6, P.VD_CRYSTAL, 70)
    for x, top, length in ((8, 8, 8), (10, 6, 12), (11, 9, 5), (7, 11, 4)):
        crystal(c, x, top, length, down=True)
    return single("ravine_void_rim", c)


def pit_chain() -> Sprite:
    """6x24, the vines' slot: a gold-linked chain ending in a small glowing crystal weight."""
    c = Canvas(6, 24)
    for y in range(0, 17, 3):
        if (y // 3) % 2:
            c.rect(2, y, 3, y + 2, P.GOLD_D)
            c.px(2, y, P.GOLD)
        else:
            c.rect(1, y, 4, y + 2, P.IRON_D)
            c.rect(2, y + 1, 3, y + 1, P.VD_BRICK_DD)
            c.px(1, y, P.IRON)
    glow(c, 2.5, 20, 3, 3.5, P.VD_CRYSTAL, 70)
    crystal(c, 2.5, 17, 6, down=True)
    return single("ravine_void_vines", c)


def pit_back() -> Sprite:
    """16x16: deep space seen past the pit's walls, tiling both ways: a few faint bricks of a far wall and stars."""
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 15, P.VD_SIL_D)
    for x, y, col in ((3, 2, P.VD_STAR), (11, 5, P.VD_PLANET_L), (6, 9, P.VD_STAR), (14, 12, P.VD_NEB_L), (1, 13, P.VD_PLANET),
                      (9, 14, P.VD_PLANET)):
        c.px(x, y, col)
    c.rect(0, 7, 15, 7, P.VD_SIL)
    c.rect(7, 0, 7, 6, P.VD_SIL)
    c.rect(0, 15, 15, 15, P.VD_SIL)
    return single("ravine_void_back", c)


ENERGY_BASE = [P.VD_NEB_D, P.VD_NEB, P.VD_NEB_L, P.VD_NEB, P.VD_NEB_B, P.VD_NEB_D, P.VD_NEB_B, P.VD_NEB, P.VD_NEB_D,
               P.VD_NEB_B, P.VD_NEB_D, P.VD_NEB, P.VD_NEB_L, P.VD_ENERGY_W, P.VD_NEB, P.VD_NEB_B]


def energy_stream(width: int, seed: int, base: list) -> list:
    rnd = noise(seed)
    cols = []
    for x in range(width):
        bright = base[x] in (P.VD_ENERGY_W, P.VD_NEB_L)
        start, length = int(rnd() * 16), 5 + int(rnd() * 6)
        mark = (P.VD_NEB, P.VD_NEB_D) if bright else (P.VD_NEB_L, P.VD_ENERGY_W)
        cols.append((base[x], [(start, length, mark[int(rnd() * 2)])]))
    return cols


def pit_falls() -> list[Sprite]:
    """The void-energy curtain (16x16, `flow` 4, tiles both ways, streaks down 4 px a frame) and its opaque 4x16
    edge whose gaps are deep space."""
    cols = energy_stream(16, 871, ENERGY_BASE)
    falls = Sprite("ravine_void_falls", (16, 16))
    frames = []
    for k in range(4):
        c = Canvas(16, 16)
        for x in range(16):
            for y in range(16):
                c.px(x, y, colour_at(cols[x], (y - 4 * k) % 16))
        frames.append(c)
    falls.add("flow", frames, fps=10)
    edge_cols = energy_stream(4, 872, [P.VD_SIL, P.VD_NEB_D, P.VD_NEB, P.VD_NEB_L])
    gaps = {0: [(0, 6), (9, 5)], 1: [(4, 3), (12, 2)], 2: [(8, 2)], 3: []}
    edge = Sprite("ravine_void_falls_edge", (4, 16))
    frames = []
    for k in range(4):
        c = Canvas(4, 16)
        for x in range(4):
            for y in range(16):
                v = (y - 4 * k) % 16
                col = colour_at(edge_cols[x], v)
                if any((v - s) % 16 < n for s, n in gaps[x]):
                    col = P.VD_SIL_D if x == 0 else P.VD_SIL
                c.px(x, y, col)
        frames.append(c)
    edge.add("flow", frames, fps=10)
    return [falls, edge]


def pit_lip() -> Sprite:
    """16x6: void energy welling over the brink (row 0 = ground surface) with sparks sliding along."""
    sprite = Sprite("ravine_void_lip", (16, 6))
    frames = []
    for k in range(4):
        c = Canvas(16, 6)
        for x in range(16):
            swell = round(0.6 + 0.6 * math.sin(2 * math.pi * x / 8))
            c.px(x, 1 - swell, P.VD_NEB)
            c.rect(x, 2 - swell, x, 3, P.VD_NEB_L)
            c.px(x, 2, P.VD_ENERGY_W if (x + 4 * k) % 5 == 0 else P.VD_NEB_L)
            c.rect(x, 4, x, 5, P.VD_NEB)
        frames.append(c)
    sprite.add("flow", frames, fps=10)
    return sprite


def pit_surface() -> Sprite:
    """16x8 swirling void surface, `wave` 4: a bright rim over violet, with spirals turning as they drift."""
    sprite = Sprite("ravine_void_surface", (16, 8))
    frames = []
    for k in range(4):
        c = Canvas(16, 8)
        for x in range(16):
            crest = 2 + round(math.sin((x / 16 + k / 4) * 2 * math.pi) * 0.7)
            c.px(x, crest, P.VD_NEB_L)
            for y in range(crest + 1, 8):
                c.px(x, y, P.VD_NEB if y < 4 else P.VD_NEB_D if y < 7 else P.VD_SIL_L)
        for shift in (-16, 0, 16):
            for cx0, cy in ((4, 5), (12, 4)):
                cx = cx0 + 4 * k + shift
                for a in range(0, 330, 30):
                    ang = math.radians(a + k * 90)
                    rad = 0.6 + a / 160
                    c.px(cx + math.cos(ang) * rad, cy + math.sin(ang) * rad * 0.6, P.VD_ENERGY_W if a < 90 else P.VD_NEB_L)
        frames.append(c)
    sprite.add("wave", frames, fps=8)
    return sprite


def pit_pool() -> Sprite:
    """16x24 starfield pool under the surface, `churn` 4: violet fading to the void, stars twinkling in it."""
    bands = [(0, 4, P.VD_NEB_D, P.VD_NEB_D), (4, 8, P.VD_NEB_D, P.VD_SIL_L), (8, 24, P.VD_SIL_L, P.VD_SIL_L)]
    rnd = noise(873)
    twinkles = [(int(rnd() * 16), 3 + int(rnd() * 20), int(rnd() * 4)) for _ in range(10)]
    sprite = Sprite("ravine_void_pool", (16, 24))
    frames = []
    for k in range(4):
        c = Canvas(16, 24)
        for y0, y1, a, b in bands:
            for y in range(y0, y1):
                for x in range(16):
                    c.px(x, y, b if (x + y) % 2 else a)
        for sx, sy, phase in twinkles:                     # each star flickers on its own beat
            lit = (k + phase) % 4
            if lit:
                c.px(sx, sy, P.VD_STAR if lit == 1 else P.VD_PLANET_L if lit == 2 else P.VD_NEB)
        frames.append(c)
    sprite.add("churn", frames, fps=8)
    return sprite


def pit_splash() -> Sprite:
    """16x12 band of void energy boiling where the curtain lands, `splash` 4, with sparks above."""
    sprite = Sprite("ravine_void_splash", (16, 12))
    frames = []
    for k in range(4):
        c = Canvas(16, 12)
        c.rect(0, 8, 15, 11, P.VD_NEB_L)
        for x in range(16):
            if (x + k) % 3 == 0:
                c.px(x, 11, P.VD_NEB)
        mounds = [((1 + k) % 16, 4.6 - (k % 2), 3.2), ((8 + 2 * k) % 16, 3.6 + (k % 2), 3.6), ((13 - k) % 16, 5.2, 2.6)]
        for mx, my, rad in mounds:
            for shift in (-16, 0, 16):
                c.ellipse(mx + shift + 0.6, my + 1.2, rad, rad * 0.8, P.VD_NEB)
                c.ellipse(mx + shift, my + 0.6, rad - 0.4, rad * 0.75, P.VD_NEB_L)
                c.px(mx + shift - 1, my - 0.5, P.VD_ENERGY_W)
        rnd = noise(874 + k)
        for _ in range(6):
            c.px(int(rnd() * 16), int(rnd() * 3), P.VD_ENERGY_W if rnd() > 0.5 else P.VD_NEB_L)
        frames.append(c)
    sprite.add("splash", frames, fps=10)
    return sprite


def pit_floor() -> Sprite:
    """16x16 bottom of the abyss: the pool's void colour with broken flagstones and crystal tips rising into it,
    then bricks with a ragged clear bottom."""
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 4, P.VD_SIL_L)
    c.rect(0, 5, 15, 11, P.VD_BRICK_DD)
    brick(c, 0, 2, 6, 8, BRICK_DARK)
    brick(c, 7, 3, 15, 9, BRICK_DARK)
    crystal(c, 6.5, 3, 3)
    c.px(2, 2, P.VD_NEB_D)
    for x0, x1, y1 in ((0, 4, 14), (5, 10, 15), (11, 15, 13)):
        brick(c, x0, 10, x1, y1, BRICK_DARK)
    return single("ravine_void_floor", c)


def pit_fallbacks() -> list[Sprite]:
    fill = Canvas(8, 48)
    for y0, y1, col in ((0, 39, P.VD_SIL_D), (40, 41, P.VD_NEB_L), (42, 44, P.VD_NEB), (45, 47, P.VD_NEB_D)):
        fill.rect(0, y0, 7, y1, col)
    deep = Canvas(16, 16)
    deep.rect(0, 0, 15, 15, P.VD_SIL_L)
    for x, y in ((3, 4), (11, 9), (7, 13)):
        deep.px(x, y, P.VD_STAR)
    return [single("ravine_void_fill", fill), single("ravine_void_deep", deep)]


# --- terrain blocks (the forest terrain contract) ------------------------------------------------------

def stone_end(c: Canvas, y0: int, y1: int) -> None:
    c.rect(4, y0, 7, y1, P.VD_BRICK_DD)
    brick(c, 2, y0, 7, y1, BRICK)
    c.rect(1, y0, 1, y1, P.VD_SIL_D)


def terrain_top() -> Sprite:
    """16x16: a lit stone edge (row 0 = walk surface) with gold trim on a capstone, crystals hanging under it over
    one brick course that starts on a joint at x 0 and ends on a shaded row 15."""
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 15, P.VD_BRICK_DD)
    brick_row(c, 7, 10, [7, 9], 0, BRICK_DARK, 881, 16)
    brick_row(c, 0, 7, [16], 0, BRICK, 882, 16)
    c.rect(0, 0, 15, 0, P.VD_BRICK_TOP)
    c.rect(0, 1, 15, 1, P.VD_BRICK_L)
    c.rect(0, 2, 15, 2, P.GOLD_D)
    c.px(8, 2, P.GOLD)
    crystal(c, 4, 6, 5, down=True)
    crystal(c, 12, 6, 3, down=True)
    return single("terrain_void_top", c)


def terrain_edge() -> Sprite:
    """8x16 left end cap: the capstone overhanging by a pixel, crystals growing from its underside."""
    c = Canvas(8, 16)
    stone_end(c, 7, 15)
    c.rect(0, 0, 7, 5, P.VD_BRICK)
    c.rect(0, 0, 7, 0, P.VD_BRICK_TOP)
    c.rect(0, 1, 7, 1, P.VD_BRICK_L)
    c.rect(0, 2, 7, 2, P.GOLD_D)
    c.rect(0, 3, 0, 5, P.VD_BRICK_L)
    c.rect(0, 6, 7, 6, P.VD_BRICK_D)
    crystal(c, 1.5, 6, 5, down=True)
    crystal(c, 5, 6, 3, down=True)
    return single("terrain_void_edge", c)


def terrain_wall() -> Sprite:
    c = Canvas(8, 16)
    stone_end(c, 0, 7)
    stone_end(c, 8, 15)
    glow_crack(c, 4, 9, [(0, 0), (1, 1), (0, 1)], hot=False)
    return single("terrain_void_wall", c)


def terrain_fill() -> Sprite:
    c = Canvas(16, 16)
    c.rect(0, 0, 15, 15, P.VD_BRICK_DD)
    brick_row(c, 0, 8, [9, 7], 2, BRICK_DARK, 883, 16)
    brick_row(c, 8, 8, [7, 9], 7, BRICK_DARK, 884, 16)
    return single("terrain_void_fill", c)


# --- platforms -----------------------------------------------------------------------------------------

def island_void() -> Sprite:
    """48x24 like `island`: a floating violet rock (top row = walk surface) with crystals growing underneath."""
    body = wedge([(6, 8, [9, 10, 9, 10, 10], 1, BRICK, 891), (12, 7, [8, 9, 7, 9, 8, 7], 5, BRICK_DARK, 892),
                  (17, 6, [7, 8, 8, 7], 9, BRICK_DARK, 893)], P.VD_BRICK_DD, P.VD_SIL_D)
    slab_top(body, [P.VD_BRICK_TOP, P.VD_BRICK_L, P.GOLD_D, P.VD_BRICK, P.VD_BRICK, P.VD_BRICK_D, P.VD_BRICK_D],
             rounding=(1, 0, 0, 0, 0, 0, 1))
    c = finish(body, P.VD_SIL_D)
    under = Canvas(48, 24)
    under.ellipse(24, 20, 16, 4, rgba(P.VD_CRYSTAL, 60))
    under.paste(c)
    for x, top, length in ((8, 8, 5), (16, 13, 6), (24, 20, 3), (31, 15, 6), (40, 9, 5), (21, 18, 4)):
        crystal(under, x, top, length, down=True)
    return single("island_void", under)


def bridge_void() -> Sprite:
    """48x12 like `bridge`: stone slabs with a gold-trimmed edge (walk surface = top row), a gold-capped post at the
    left, and gold chains hanging in swags under the deck. Crumbles like the bridge."""
    w, h = 48, 12
    c = Canvas(w, h)
    for i, x in enumerate(range(4, w, 8)):                    # stone slabs
        brick(c, x, 1, min(x + 7, w - 1), 5, BRICK)
    c.rect(4, 1, w - 1, 1, P.VD_BRICK_TOP)
    c.rect(4, 6, w - 1, 6, P.GOLD_D)                          # gold trim under the deck
    for x in range(7, w, 8):
        c.px(x, 6, P.GOLD)
    c.rect(0, 1, 3, 11, P.VD_BRICK_D)                         # post
    c.rect(0, 1, 0, 11, P.VD_BRICK)
    c.rect(0, 1, 3, 2, P.GOLD)
    c.px(1, 5, P.VD_CRYSTAL)
    for x0 in range(4, w - 4, 12):                            # gold chains in swags
        for k in range(13):
            c.px(x0 + k, 7 + round(math.sin(k / 12 * math.pi) * 3), P.GOLD if k % 2 else P.GOLD_D)
    return platform("bridge_void", c.outline(P.VD_SIL_D), "crumble", 895)


def build() -> list[Sprite]:
    return [
        *smooth_sky("void", [P.VD_SKY_TOP, P.VD_SKY, P.VD_SKY_L, P.VD_SKY_HAZE]),
        single("bg_void_puffs", void_puffs()),
        single("bg_void_clouds", void_clouds()),
        single("bg_void_far", void_far()),
        single("bg_void_near", void_near()),
        single("bg_void_bushes", void_bushes()),
        *ground("void", void_ground, void_earth),
        flat("ground_void_fill", P.VD_BRICK_DD),
        *pit_walls(), pit_rim(), pit_chain(), pit_back(), *pit_falls(), pit_lip(), pit_surface(), pit_pool(),
        pit_splash(), pit_floor(), *pit_fallbacks(),
        terrain_top(), terrain_edge(), terrain_wall(), terrain_fill(),
        island_void(), bridge_void(),
    ]
