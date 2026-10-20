"""Boss hazards in the boss-atlas style, named after the hazard kinds in Bosses.json and sized to their
hitboxes. They travel toward the kitten (to the left), so each leads with its left edge; the frame's bottom
is the hitbox's bottom. Drawn with the same helpers and colours as the bosses that throw them."""
from __future__ import annotations

import math

import palette as P
from bosskit import acorn, crystal, flame, part, tube
from draw import Canvas, noise, see_through
from sprite import Sprite

FIRE = (P.RED, P.LAVA, P.LAVA_L, P.YELLOW)
VIOLET_FIRE = (P.QN_PLUM, P.PURPLE, P.VIOLET, P.QN_ORB_L)
METAL = {P.GM: (P.GM_L, P.GM_D)}


def hazard(name: str, frames: list, fps: int = 10) -> Sprite:
    image = frames[0].img if hasattr(frames[0], "img") else frames[0]
    sprite = Sprite(f"hazard_{name}", image.size)
    sprite.add("fly", frames, fps=fps)
    return sprite


def ice(c: Canvas, base, tip, width: float, bright: bool = False) -> None:
    if bright:
        crystal(c, base, tip, width, light=P.WHITE, mid=P.GL2_CRY_L, dark=P.GL2_CRY)
    else:
        crystal(c, base, tip, width, light=P.GL2_CRY_L, mid=P.GL2_CRY, dark=P.GL2_CRY_D)


def acorns() -> list[Sprite]:
    rolled = []                                                  # the volley, low: rolls to the left
    for i in range(4):
        c = Canvas(12, 12)
        acorn(c, 6, 6.2, 0.72, angle=-90 * i)
        rolled.append(c.outline(P.BROWN_D))

    lob = []                                                     # the lob, high, with a speed trail
    for i in range(4):
        c = Canvas(18, 14)
        for k in range(3):
            y = 4 + k * 3 + (i + k) % 2
            c.line((12 + k, y), (16 - (i + k) % 2, y), P.WHITE if k != 1 else P.SAND)
        acorn(c, 6.5, 7, 0.75, angle=-90 * i)
        lob.append(c.outline(P.BROWN_D))

    giant = []                                                   # dropped from the oak, nose first
    for i in range(2):
        c = Canvas(28, 34)
        for x in (4, 23, 9 + i * 9):
            c.line((x, 1), (x, 4 + i * 2), P.WHITE)
        acorn(c, 14, 19, 1.9, angle=(i * 2 - 1) * 5)
        c.outline(P.BROWN_D)
        c.px(10 + i, 21, P.YELLOW)
        giant.append(c)

    shock = []                                                   # dust and leaves bursting along the ground
    for i in range(3):
        c = Canvas(24, 12)
        rnd = noise(610 + i)
        for k in range(6):
            x = 3 + k * 3.6
            rad = (5.2 - k * 0.7) * (0.85 + i * 0.1)
            c.ellipse(x, 11 - rad * 0.8, rad, rad * 0.8, (P.SAND, P.CREAM_D, P.BROWN_L)[(k + i) % 3])
        for k in range(3):
            c.px(5 + k * 6 + i + rnd() * 2, 1 + (k + i) % 3, P.GREEN if k % 2 else P.LEAF_L)
            c.px(8 + k * 5 + rnd() * 2, 3 + rnd() * 3, P.BROWN)
        shock.append(c.outline(P.BROWN))
    return [hazard("acorn", rolled, fps=14), hazard("acorn_high", lob, fps=14), hazard("giant_acorn", giant, fps=8),
            hazard("shockwave", shock, fps=12)]


def frost() -> list[Sprite]:
    fan = []                                                     # a volley of ice shards flying left (62x12)
    for i in range(2):
        c = Canvas(62, 12)
        for k, (x, y, length) in enumerate(((2, 6, 13), (17, 4, 11), (32, 7, 13), (47, 5, 11))):
            yy = y + ((i + k) % 2) * 0.6
            ice(c, (x + length, yy), (x, yy), 2.6, bright=(i + k) % 2 == 0)
            c.px(x + length + 2 + i, yy, P.GL2_CRY)                  # frost trail
        fan.append(c.outline(P.GL2_EDGE))

    spike = []                                                   # a crystal bursting from the iced floor
    for i, height in enumerate((16, 15)):
        c = Canvas(12, 18)
        ice(c, (6, 17), (6, 17 - height), 2.8, bright=i == 0)
        ice(c, (4, 17), (1.5, 8), 1.4)
        ice(c, (8, 17), (10.5, 10), 1.4)
        spike.append(c.outline(P.GL2_EDGE))

    breath = []                                                  # the freezing cloud rolling along the ground
    for i in range(3):
        c = Canvas(42, 13)
        rnd = noise(600 + i)
        puffs = []
        for k in range(9):
            x = 5 + k * 4.1
            rad = 5.5 - k * 0.32 + rnd() * 0.8
            puffs.append((x + rnd() - 0.5, 12 - rad, rad))
        for layer, colour in enumerate((P.GL2_MEM, P.GL2_MEM_L, P.BLUE_L, P.WHITE)):
            for x, y, rad in puffs:
                rr = rad * (1 - layer * 0.25)
                c.ellipse(x - layer * 0.6, y - layer * 0.6, rr, rr * 0.9, colour)
        for k in range(5):
            c.px(4 + rnd() * 34, 2 + rnd() * 6, P.WHITE)
        breath.append(c.outline(P.GL2_EDGE).img)
    return [hazard("shard", fan, fps=8), hazard("ice_spike", spike, fps=6), hazard("breath", breath, fps=10)]


def haunted() -> list[Sprite]:
    wave = []                                                    # a shadow crescent racing along the ground
    for i in range(3):
        c = Canvas(16, 14)
        trail = Canvas(16, 14)
        for k in range(3):
            trail.ellipse(11 + k * 2, 7 + (k - 1) * 3, 1.6, 1.2, P.QN_ORB if k == 1 else P.VIOLET)
        c.paste(see_through(trail.img, 150 + i * 30))
        with part(c, {P.PURPLE: (P.QN_ORB, P.QN_PLUM)}, P.QN_PLUM_D, up=1, down=1, left=2, right=1) as k:
            k.ellipse(7, 7, 6, 6.5, P.PURPLE)
        c.ellipse(9.5 + i * 0.4, 7, 5, 6, (0, 0, 0, 0))            # the bite that makes the crescent
        c.line((3, 4), (2, 8), P.QN_ORB_L)
        c.px(3 + i % 2, 10, P.QN_ORB_L)
        wave.append(see_through(c.outline(P.NIGHT).img, 235))

    wisp = []                                                    # a violet ghost-fire, head first
    for i in range(4):
        c = Canvas(18, 14)
        for k in range(4):
            c.ellipse(8 + k * 2.4, 7 + ((i + k) % 3 - 1) * 0.8, 2.6 - k * 0.5, 2.1 - k * 0.4,
                      (P.QN_ORB, P.VIOLET, P.PURPLE, P.QN_PLUM)[k])
        c.ellipse(6, 7, 4.5, 4.5, P.VIOLET)
        c.ellipse(5.5, 7, 3, 3, P.QN_ORB_L)
        c.ellipse(5, 6.5, 1.4, 1.4, P.WHITE)
        c.px(4, 5, P.QN_PLUM_D)                                    # a hollow ghost face
        c.px(6, 5, P.QN_PLUM_D)
        wisp.append(see_through(c.outline(P.QN_PLUM).img, 235))
    return [hazard("wave", wave, fps=12), hazard("wisp", wisp, fps=12)]


def citadel() -> list[Sprite]:
    rocket = []                                                  # a red rocket nose first, flames behind
    for i in range(3):
        c = Canvas(22, 10)
        for k in range(4):
            c.ellipse(15 + k * 1.8, 4.5, 2.6 - k * 0.5 + (i + k) % 2 * 0.4, 2 - k * 0.4,
                      (P.YELLOW, P.LAVA_L, P.LAVA, P.RED)[k])
        with part(c, {P.RED: (P.CAPE_L, P.RED_D)}, P.RED_D, up=1, down=1) as k:
            k.rect(4, 3, 13, 6, P.RED)
            k.poly([(0, 4.5), (4, 2.5), (4, 6.5)], P.RED)
        c.line((8, 3), (8, 6), P.GM_L)
        c.rect(12, 2, 13, 7, P.GM)
        c.poly([(10, 3), (14, 0), (14, 3)], P.GM_D)
        c.poly([(10, 6), (14, 9), (14, 6)], P.GM_D)
        c.px(2, 4, P.WHITE)
        rocket.append(c.outline())

    patch = []                                                   # where a rocket landed: a pool of fire
    for i in range(4):
        c = Canvas(14, 20)
        c.rect(0, 18, 13, 19, P.MAROON)
        c.rect(2, 18, 11, 18, P.LAVA)
        flame(c, 7, 18, 15 + (i % 2) * 2, 4.5, i, 660)
        flame(c, 3, 18, 7 + (i + 1) % 2 * 2, 2.2, i + 3, 661)
        flame(c, 11, 18, 8 + i % 2 * 2, 2.2, i + 5, 662)
        patch.append(c)

    tail = []                                                    # the segmented metal tail, blazing (30x12)
    for i in range(2):
        c = Canvas(36, 13)
        fire = Canvas(36, 13)
        for k in range(6):
            flame(fire, 12 + k * 4, 11, 6 + (i + k) % 3 * 2, 2.4, i + k, 670 + k)
        c.paste(see_through(fire.img, 230))
        pts = [(10 + k * 3.6, 8 + math.sin(k / 2 + i * math.pi) * 1.2, 3.2 - k * 0.15) for k in range(7)]
        for k, (x, y, rad) in enumerate(pts):
            with part(c, METAL, P.GM_DD, up=1, down=1, left=1, right=1) as layer:
                layer.ellipse(x, y, rad, rad, P.GM)
            if k % 2:
                c.px(x, y, P.LAVA)
        c.poly([(0, 8), (10, 4), (10, 12)], P.GM_L)               # blade at the tip
        c.line((1, 8), (9, 8), P.LAVA_L)
        for k in range(2):
            c.px(16 + k * 10 + i * 3, 12, P.LAVA_L)                # sparks scraping the floor
        tail.append(c.outline())

    claw = []                                                    # a grabber on a long arm, high (70x14)
    for i in range(2):
        c = Canvas(72, 15)
        for x in range(14, 72, 6):                               # telescoping arm
            with part(c, METAL, P.GM_DD, up=1, down=1) as layer:
                layer.rect(x, 5, x + 5, 9, P.GM)
            c.px(x, 7, P.LAVA if (x // 6 + i) % 2 else P.GM_DD)
        with part(c, METAL, P.GM_DD) as layer:
            layer.ellipse(12, 7, 4, 4, P.GM)
        c.px(12, 7, P.LAVA_L)
        open_ = 2 - i
        for dy in (-1, 1):                                       # three-fingered claw with hot tips
            c.line((10, 7 + dy * 2), (4, 7 + dy * (4 + open_)), P.GM_L, 2)
            c.line((4, 7 + dy * (4 + open_)), (1, 7 + dy * (2 + open_)), P.LAVA_L)
        c.line((9, 7), (2, 7), P.GM_L, 2)
        c.px(1, 7, P.LAVA_L)
        claw.append(c.outline())
    return [hazard("rocket", rocket, fps=14), hazard("burning_patch", patch, fps=12), hazard("tail", tail, fps=10),
            hazard("claw", claw, fps=8)]


def build() -> list[Sprite]:
    return [*acorns(), *frost(), *haunted(), *citadel()]
