"""Pickups, HUD and award art, and the sparks around the kitten when it wins an ability (boss hazards are in
boss_hazards.py)."""
from __future__ import annotations

import math

import palette as P
from draw import Canvas, see_through
from sprite import Sprite, single


def fish() -> Sprite:
    """The pickup: a little blue fish that bobs with a shine running along it (14x10)."""
    sprite = Sprite("fish", (16, 12))
    frames = []
    for i in range(6):
        c = Canvas(16, 12)
        dy = (0, 0, -1, -1, -1, 0)[i]
        c.poly([(1, 2 + dy), (4, 5.5 + dy), (1, 9 + dy)], P.BLUE)                 # tail
        c.ellipse(8, 5.5 + dy, 5.5, 3.5, P.BLUE)
        c.ellipse(8.5, 7 + dy, 4.5, 1.6, P.ICE_L)                                # belly
        c.poly([(6, 2.5 + dy), (9, 0.5 + dy), (10, 2.5 + dy)], P.BLUE_D)          # fin
        c.rect(11, 4 + dy, 11.5, 4.5 + dy, P.BLACK)                              # eye
        c.px(12, 4 + dy, P.WHITE)
        c.line((9.5, 3.5 + dy), (9.5, 7 + dy), P.BLUE_D)                           # gill
        shine = 4 + i * 1.6
        if shine < 13:
            c.px(shine, 3.5 + dy, P.WHITE)
            c.px(shine + 1, 3.5 + dy, P.CYAN)
        c.outline(P.NAVY)
        if i == 4:
            c.px(14, 1, P.YELLOW)
            c.px(13, 1, P.WHITE)
            c.px(15, 1, P.WHITE)
            c.px(14, 0, P.WHITE)
            c.px(14, 2, P.WHITE)
        frames.append(c.img)
    sprite.add("spin", frames, fps=10)
    return sprite


def yarn_basket() -> Sprite:
    """The level-up shrine: a wicker basket heaped with yarn, sparkling (26x26)."""
    sprite = Sprite("yarn_basket", (28, 28), ground=27)
    frames = []
    for glow in range(4):
        c = Canvas(28, 28)
        for x, y, rad, col, light in ((9, 13, 5, P.YARN, P.YARN_L), (18, 12, 5.5, P.BLUE, P.ICE_L),
                                      (13, 9, 4.5, P.GOLD, P.YELLOW)):
            c.ellipse(x, y, rad, rad, col)
            c.line((x - rad + 1.5, y - 1), (x + rad - 1.5, y + 1), light)
            c.line((x - 1, y - rad + 1.5), (x + 1, y + rad - 1.5), light)
        c.line((20, 6), (25, 1), P.GREY_L)                                          # knitting needles
        c.line((17, 5), (21, 0), P.GREY_L)
        c.px(25, 1, P.RED)
        c.px(21, 0, P.RED)
        c.poly([(3, 15), (25, 15), (23, 27), (5, 27)], P.BROWN_L)                    # basket
        for y in range(16, 27, 3):
            for x in range(4 + (y // 3) % 2 * 2, 24, 4):
                c.rect(x, y, x + 1, y + 1, P.BROWN)
        c.rect(2, 14, 26, 16, P.SAND)
        c.rect(2, 16, 26, 16, P.BROWN)
        c.line((6, 18), (6, 26), P.BROWN_D)
        c.outline()
        for k, (sx, sy) in enumerate(((2, 5), (25, 10), (5, 1), (22, 20))):
            if (k + glow) % 4 < 2:
                col = (P.WHITE, P.YELLOW)[(k + glow) % 2]
                c.px(sx, sy, col)
                c.px(sx - 1, sy, P.YARN_L)
                c.px(sx + 1, sy, P.YARN_L)
                c.px(sx, sy - 1, P.YARN_L)
                c.px(sx, sy + 1, P.YARN_L)
        frames.append(c.img)
    sprite.add("glow", frames, fps=6)
    return sprite


def paw(c: Canvas, x: float, y: float, s: float, colour) -> None:
    """A paw print centred on (x, y); about 9*s wide."""
    c.ellipse(x, y + 2 * s, 2.6 * s, 2.1 * s, colour)
    for dx, dy in ((-3.8, -1.6), (-1.5, -4.0), (1.5, -4.0), (3.8, -1.6)):
        c.ellipse(x + dx * s, y + dy * s, 0.95 * s, 1.15 * s, colour)


def medal() -> Sprite:
    """The end-screen award: a struck disc with a paw print, in three metals."""
    sprite = Sprite("medal", (32, 32))
    for name, face, shade, shine in (("bronze", P.BROWN_L, P.BROWN, P.SAND), ("silver", P.GREY_L, P.GREY, P.WHITE),
                                     ("gold", P.GOLD, P.GOLD_D, P.YELLOW)):
        c = Canvas(32, 32)
        c.ellipse(15.5, 15.5, 13, 13, shade)
        c.ellipse(15.5, 15.5, 10.5, 10.5, face)
        c.line((9, 9), (13, 6.5), shine)
        paw(c, 15.5, 16.5, 1.55, shade)
        c.px(13.5, 17, shine)
        sprite.add(name, [c.outline(P.OUTLINE)], fps=1)
    return sprite


def ability_icons() -> list[Sprite]:
    """What the award card shows for each ability; named after the ability ids."""
    # Yarn Shot: a ball of yarn flying, its thread trailing behind.
    shot = Canvas(24, 24)
    for k in range(3):
        shot.line((2, 8 + k * 4), (8 - k, 8 + k * 4), P.WHITE)
    for k in range(7):
        shot.px(5 + k, 16 + math.sin(k * 1.2) * 1.5, P.YARN_D)
    shot.ellipse(15, 11, 7, 7, P.YARN)
    for k in range(3):
        a = 0.6 + k * 0.5
        dx, dy = math.cos(a) * 6, math.sin(a) * 6
        shot.line((15 - dx + (k - 1) * 2, 11 - dy), (15 + dx + (k - 1) * 2, 11 + dy), P.YARN_D)
    shot.line((11, 7), (13, 5), P.YARN_L)
    shot.px(11, 8, P.YARN_L)

    # Double Pounce: two paw prints climbing, a curved arrow over them.
    double = Canvas(24, 24)
    paw(double, 6, 17, 1.1, P.GINGER)
    paw(double, 12.5, 8, 1.1, P.GINGER)
    for y in (5, 10):                                        # two chevrons: up, and up again
        double.line((18, y + 3), (20.5, y), P.WHITE, 2)
        double.line((20.5, y), (23, y + 3), P.WHITE, 2)

    # Ghost Dash: a see-through cat head with speed lines.
    ghost = Canvas(24, 24)
    for k in range(3):
        ghost.line((1, 9 + k * 4), (6 + k, 9 + k * 4), P.CYAN)
    ghost.poly([(9, 7), (11, 1), (14, 6)], P.ICE_L)
    ghost.poly([(16, 6), (20, 1), (21, 8)], P.ICE_L)
    ghost.ellipse(15.5, 12, 7.5, 6.5, P.ICE_L)
    ghost.ellipse(15.5, 18, 5, 3, P.ICE_L)
    for k in range(3):
        ghost.poly([(11 + k * 3, 19), (12.5 + k * 3, 23), (14 + k * 3, 19)], P.ICE_L)
    ghost.rect(12, 10, 13, 12, P.ICE_D)
    ghost.rect(18, 10, 19, 12, P.ICE_D)
    ghost.px(13, 10, P.WHITE)                                # shine, like the hero's eyes
    ghost.px(19, 10, P.WHITE)
    ghost.px(15.5, 14, P.PINK)
    ghost.line((10, 17), (21, 17), P.CAPE, 2)                # the hero's red scarf, knotted
    ghost.rect(10, 19, 11, 20, P.CAPE_D)
    ghost.px(11, 3, P.CYAN)
    ghost.px(19, 3, P.CYAN)
    ghost_icon = see_through(ghost.outline(P.BLUE_D).img, 230)

    # Super Pounce: a big paw, claws out, with speed streaks behind it.
    sup = Canvas(24, 24)
    for k in range(4):
        sup.line((1, 8 + k * 4), (5 + (k % 2) * 2, 8 + k * 4), P.YELLOW if k % 2 else P.WHITE)
    sup.ellipse(14, 13, 8, 8.5, P.GINGER)
    sup.ellipse(14, 16, 4, 3.2, P.PINK)
    for dx, dy in ((-5, -3), (-2, -6), (2, -6), (5, -3)):
        sup.ellipse(14 + dx, 13 + dy, 1.3, 1.5, P.PINK)
        sup.line((14 + dx * 1.3, 13 + dy * 1.5), (14 + dx * 1.6, 13 + dy * 1.9), P.WHITE)
    sup.px(10, 18, P.GINGER_L)
    return [single("ability_yarnShot", shot.outline()), single("ability_doublePounce", double.outline()),
            single("ability_ghostDash", ghost_icon), single("ability_superPounce", sup.outline())]


def sparks() -> list[Sprite]:
    """Bits thrown out around the kitten when an ability is won."""
    star = Canvas(9, 9)
    star.poly([(4, 0), (5, 3), (8, 3), (6, 5), (7, 8), (4, 6), (1, 8), (2, 5), (0, 3), (3, 3)], P.GOLD)
    star.rect(4, 3, 4, 4, P.YELLOW)

    ember = Canvas(6, 6)                                     # a curl of yarn
    ember.ellipse(2.5, 2.5, 2.5, 2.5, P.YARN)
    ember.px(2, 2, P.YARN_L)
    ember.line((1, 3), (4, 2), P.YARN_D)

    feather = Canvas(8, 5)
    feather.poly([(0, 2), (3, 0), (7, 1), (5, 4), (2, 4)], P.WHITE)
    feather.line((1, 2), (6, 2), P.BLUE_L)

    return [single("spark_star", star), single("spark_ember", ember), single("spark_feather", feather)]


def build() -> list[Sprite]:
    # heart_full / heart_empty are drawn with the rest of the HUD in hud.py.
    return [fish(), yarn_basket(), medal(), *ability_icons(), *sparks()]
