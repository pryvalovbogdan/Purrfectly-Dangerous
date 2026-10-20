"""Pickups, HUD and award art, the sparks around the kitten when it wins an ability, and boss hazards."""
from __future__ import annotations

import math

from PIL import ImageOps

import palette as P
from characters.forest import acorn_shape, rolling
from characters.citadel import flame_column
from draw import Canvas, noise, see_through
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


def heart(name: str, fill, shade) -> Sprite:
    c = Canvas(11, 10)
    c.ellipse(2.5, 2.5, 2, 2, fill)
    c.ellipse(6.5, 2.5, 2, 2, fill)
    c.poly([(0.5, 3.5), (8.5, 3.5), (4.5, 8)], fill)
    c.px(2, 2, shade)
    return single(name, c.outline())


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


def hazard(name: str, frames: list, fps: int = 10) -> Sprite:
    image = frames[0].img if hasattr(frames[0], "img") else frames[0]
    sprite = Sprite(f"hazard_{name}", image.size)
    sprite.add("fly", frames, fps=fps)
    return sprite


def hazards() -> list[Sprite]:
    """Boss hazards, named after the hazard kinds in Bosses.json and sized to their hitboxes. They travel
    toward the kitten (to the left), so each leads with its left edge; the frame's bottom is the
    hitbox's bottom."""
    out = []

    def nut(c):
        acorn_shape(c, 5.5, 6, 1.0)

    # Rolling is drawn clockwise; mirrored here so the acorns turn the way they roll (left).
    rolled = [ImageOps.mirror(f) for f in rolling(nut, 12)]
    out.append(hazard("acorn", rolled, fps=14))                  # the volley, low

    lob = []                                                     # the lob, high, with a speed trail
    for i, f in enumerate(rolled):
        c = Canvas(18, 14)
        for k in range(3):
            c.px(13 + k * 2, 5 + k + (i % 2), P.WHITE if k < 2 else P.ICE_L)
        c.paste(f, 0, 1)
        lob.append(c)
    out.append(hazard("acorn_high", lob, fps=14))

    giant = []                                                   # dropped by the king from above
    for i in range(2):
        c = Canvas(28, 34)
        for x in (5, 22):
            c.line((x, 0), (x, 4 + i * 2), P.WHITE)
        acorn_shape(c, 13.5, 19, 2.8)
        c.px(10 + i, 18, P.YELLOW)
        giant.append(c.outline())
    out.append(hazard("giant_acorn", giant, fps=8))

    shock = []
    for i in range(3):
        c = Canvas(24, 12)
        for k in range(5):
            height = (10, 8, 6, 4, 3)[k] - (i + k) % 2
            c.rect(2 + k * 4, 11 - height, 4 + k * 4, 11, (P.SAND, P.BROWN_L, P.BROWN, P.BROWN_D, P.BROWN_D)[k])
        for k in range(3):                                       # leaves flung up
            c.px(4 + k * 6 + i, 2 + (k + i) % 3, P.GREEN if k % 2 else P.LEAF_L)
        shock.append(c.outline())
    out.append(hazard("shockwave", shock, fps=12))

    def shard_at(c, x, y, i, length=12):
        c.poly([(x, y), (x + 5, y - 2.5), (x + length, y - 1), (x + length, y + 1), (x + 5, y + 2.5)], P.CYAN)
        c.poly([(x, y), (x + 5, y - 2.5), (x + length, y - 1), (x + 5, y)], P.ICE_L)
        c.px(x + 4 + i * 3, y - 1, P.WHITE)

    fan = []                                                     # a fan of shards, high (60x12)
    for i in range(2):
        c = Canvas(62, 12)
        for k, (x, y) in enumerate(((1, 6), (17, 3), (33, 8), (48, 4))):
            shard_at(c, x, y + (i + k) % 2 * 0.5, i)
        fan.append(c.outline(P.ICE_D))
    out.append(hazard("shard", fan, fps=8))

    spike = []                                                   # grows out of the iced floor (10x16)
    for height in (16, 15):
        c = Canvas(12, 18)
        c.poly([(1, 17), (5.5, 17 - height), (10, 17)], P.BLUE_L)
        c.poly([(1, 17), (5.5, 17 - height), (4, 17)], P.CYAN)
        c.line((6, 17 - height + 3), (7, 15), P.WHITE)
        spike.append(c.outline(P.ICE_D))
    out.append(hazard("ice_spike", spike, fps=6))

    breath = []                                                  # freezing breath rolling along the ground
    for i in range(3):
        c = Canvas(42, 13)
        rnd = noise(600 + i)
        for k in range(8):
            x = 4 + k * 4.6
            radius = 5.5 - k * 0.45 + rnd()
            c.ellipse(x, 12 - radius, radius, radius, (P.WHITE, P.ICE_L, P.BLUE_L)[(k + i) % 3])
        for k in range(4):
            c.px(4 + rnd() * 34, 2 + rnd() * 5, P.WHITE)
        breath.append(c.outline(P.BLUE))
    out.append(hazard("breath", breath, fps=10))

    wave = []                                                    # a spectral wave along the ground (12x12)
    for i in range(3):
        c = Canvas(16, 14)
        for k in range(3):
            height = 12 - k * 3 - (i + k) % 2
            c.ellipse(3 + k * 4, 13 - height / 2, 2.6, height / 2, (P.VIOLET, P.PURPLE, P.PURPLE_L)[(k + i) % 3])
        c.px(3, 3 + i % 2, P.SPIRIT)
        c.px(8, 6 - i % 2, P.SPIRIT)
        wave.append(see_through(c.outline(P.PURPLE_D).img, 225))
    out.append(hazard("wave", wave, fps=12))

    wisp = []                                                    # a ghost-fire wisp, high (12x12)
    for i in range(4):
        c = Canvas(18, 14)
        for k in range(4):
            c.ellipse(8 + k * 2.2, 7 + ((i + k) % 3 - 1) * 0.6, 2.4 - k * 0.45, 2 - k * 0.35,
                      P.VIOLET if k < 2 else P.PURPLE)
        c.ellipse(6, 7, 4.5, 4.5, P.LILAC)
        c.ellipse(5.5, 7, 2.8, 2.8, P.WHITE)
        c.px(4, 6, P.SPIRIT)
        c.px(6, 6, P.SPIRIT)
        wisp.append(see_through(c.outline(P.PURPLE).img, 230))
    out.append(hazard("wisp", wisp, fps=12))

    rocket = []                                                  # in flight from the back pods
    for i in range(3):
        c = Canvas(22, 10)
        for k in range(3):                                       # exhaust behind (to the right)
            c.ellipse(15 + k * 2.5, 4.5, 2.2 - k * 0.5 + (i + k) % 2 * 0.5, 1.8 - k * 0.4,
                      (P.LAVA_L, P.LAVA, P.RED)[k])
        c.rect(4, 3, 13, 6, P.GREY_L)
        c.rect(4, 5, 13, 6, P.GREY)
        c.poly([(0, 4.5), (4, 2.5), (4, 6.5)], P.RED)
        c.poly([(11, 3), (14, 0), (14, 3)], P.RED_D)
        c.poly([(11, 6), (14, 9), (14, 6)], P.RED_D)
        rocket.append(c.outline())
    out.append(hazard("rocket", rocket, fps=14))

    patch = []                                                   # where a rocket landed (10x18)
    for i in range(4):
        c = Canvas(14, 20)
        c.rect(0, 18, 13, 19, P.MAROON)
        c.rect(2, 18, 11, 18, P.LAVA)
        flame_column(c, 7, 18, 15 + (i % 2) * 2, i, width=4)
        patch.append(c)
    out.append(hazard("burning_patch", patch, fps=12))

    tail = []                                                    # the metal tail sweeping low (30x12)
    for i in range(2):
        c = Canvas(36, 13)
        for k in range(7):
            x = 10 + k * 3.8
            rad = 3 + k * 0.2
            c.ellipse(x, 7 + math.sin(k / 2 + i * math.pi) * 1.2, rad, rad, P.IRON if k % 2 else P.IRON_L)
        c.poly([(0, 7), (10, 3), (10, 11)], P.GREY_L)             # blade at the tip
        c.line((1, 7), (9, 7), P.WHITE)
        for k in range(2):
            c.px(16 + k * 10 + i * 3, 12, P.LAVA_L)                # sparks scraping the floor
        tail.append(c.outline())
    out.append(hazard("tail", tail, fps=10))

    claw = []                                                    # a grabber on a long arm, high (70x14)
    for i in range(2):
        c = Canvas(72, 15)
        for x in range(14, 72, 6):                               # telescoping arm
            c.rect(x, 5, x + 5, 9, P.IRON if (x // 6) % 2 else P.IRON_L)
            c.px(x + 1, 6, P.IRON_D)
        c.ellipse(12, 7, 4, 4, P.IRON)
        c.px(12, 7, P.LAVA)
        open_ = 2 - i
        for dy in (-1, 1):                                       # three-fingered claw
            c.line((10, 7 + dy * 2), (4, 7 + dy * (4 + open_)), P.GREY_L, 2)
            c.line((4, 7 + dy * (4 + open_)), (1, 7 + dy * (2 + open_)), P.GREY_L)
        c.line((9, 7), (2, 7), P.GREY_L, 2)
        claw.append(c.outline())
    out.append(hazard("claw", claw, fps=8))
    return out


def build() -> list[Sprite]:
    return [fish(), yarn_basket(), medal(), heart("heart_full", P.RED, P.WHITE),
            heart("heart_empty", P.SLATE, P.GREY_D), *ability_icons(), *sparks(), *hazards()]
