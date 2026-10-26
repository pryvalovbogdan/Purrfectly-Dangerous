"""Sharky's water looks for two abilities (cosmetic only; the game draws them for the `sharky` skin).

`shot_wave` is his Yarn Shot: a small curling wave flying forward in place of the ball of yarn, same 12-point
height and centred anchor as `yarn`, bursting into a splash on impact. `water_slide` is the strip of water he
surfs on during a Ghost Dash: a sheet of water on the ground under his feet, a bow wave with spray at its front
and foam breaking up behind; its `splash` is the water bursting up as the dash starts, left behind as the world
scrolls on. Colours are the shark onesie's water (`P.SHARK_WATER`), outlined in the onesie's darkest blue.
"""
from __future__ import annotations

import math

import palette as P
from draw import Canvas, noise
from sprite import Sprite

W = P.SHARK_WATER                  # white foam, pale, mid and deep water
EDGE = P.SHARK_SUIT[3]


def _alpha(colour, a: int):
    return (*colour[:3], a)


def shot_wave() -> Sprite:
    """A curling wave (16x12) rolling right: a body that rises from a foamy tail to a crest whose white lip curls
    over a dark hollow, spray flicking ahead; on impact it bursts into droplets and a spreading ring of foam."""
    sprite = Sprite("shot_wave", (16, 12))
    fly = []
    for i in range(4):
        c = Canvas(16, 12)
        bob = (0, -1, 0, 1)[i] * 0.5
        cx, cy, rad = 9.5, 5.5 + bob, 4.2
        for x in range(1, 9):                             # the back of the wave, rising from a foamy tail
            top = round(10 - (x - 1) * 0.85 + 0.5 * math.sin(x * 1.4 + i * 1.6))
            for y in range(top, 11):
                depth = y - top
                c.px(x, y, W[0] if depth == 0 else W[1] if depth < 2 else W[2] if y < 10 else W[3])
        c.ellipse(cx, cy, rad, rad, W[2])                 # the barrel
        c.rect(cx - rad, cy, cx + 1, 10, W[2])
        c.rect(5, 9, 12, 10, W[3])
        for k in range(15):                               # the white lip curling over the top and down the front
            a = math.radians(190 + k * 16 + i * 4)        # from behind, over the top, round to the front
            for dr, colour in ((0, W[0]), (-1, W[1])):
                c.px(cx + math.cos(a) * (rad + dr), cy + math.sin(a) * (rad + dr), colour)
        c.ellipse(cx + 0.6, cy + 0.9, 1.6, 1.6, W[3])     # the dark hollow inside the curl
        c.px(cx - 1, cy + 3, W[1])                        # light catching the face
        c.px(cx - 2, cy + 2, W[1])
        tip = math.radians(190 + 14 * 16 + i * 4)
        c.px(cx + math.cos(tip) * rad, cy + math.sin(tip) * rad + 1, W[0])   # the tip dripping
        for x in range(1, 4):
            c.px(x, 10, W[0] if (x + i) % 2 else W[1])    # foam at the tail
        c.outline(EDGE)
        for k, (sx, sy) in enumerate(((15, 3 + i % 3), (14, 1 + (i // 2)), (15, 7 - i % 2))):   # spray ahead
            if (i + k) % 2 == 0:
                c.px(sx, sy, W[0] if k != 2 else W[1])
        c.px(0, 6 + (i % 3), _alpha(W[1], 200))           # a fleck left behind
        fly.append(c)
    sprite.add("fly", fly, fps=12)

    impact = []
    for i in range(5):
        c = Canvas(16, 12)
        mid_x, base = 8, 10
        if i < 2:                                         # the wave collapsing into a mound
            c.ellipse(mid_x, base - 2 + i, 4 - i, 3 - i, W[2])
            c.ellipse(mid_x - 1, base - 3 + i, 2 - i * 0.5, 1, W[1])
            c.px(mid_x - 1, base - 4 + i, W[0])
            c.outline(EDGE)
        reach = 2 + i * 1.5                               # droplets thrown up and out
        for k in range(6):
            a = math.radians(200 + k * 28)
            x = mid_x + math.cos(a) * reach
            y = base - 2 + math.sin(a) * reach * 1.1 + (i * i) * 0.25
            colour = W[0] if k % 2 else W[1]
            if i < 3:
                c.rect(x, y, x + 1, y + 1, colour) if k % 3 == 0 else c.px(x, y, colour)
            else:
                c.px(x, y, _alpha(colour, 255 - (i - 2) * 70))
        spread = 2 + i * 1.4                              # foam ring spreading along the bottom
        for dx in (-spread, -spread + 1, spread - 1, spread):
            c.px(mid_x + dx, base + 1, _alpha(W[0] if abs(dx) == spread else W[1], 255 - i * 40))
        impact.append(c)
    sprite.add("impact", impact, fps=18, loop=False)
    return sprite


# The strip: 60x14 points, the hero's body centre on x 40, his feet on row 10 (the sheet of water reaches a
# couple of rows into the ground below them); 34 points of water trail behind him, the bow wave 9 ahead.
SLIDE = (60, 14)
SLIDE_CX, SLIDE_GROUND = 40, 10
TAIL, FRONT = 4, 49


def _sheet_top(x: int, i: int) -> float:
    """Top row of the water sheet at column `x`: thin and broken at the tail, thick under the cat, a bow wave
    rising at the front."""
    t = (x - TAIL) / (FRONT - TAIL)
    top = SLIDE_GROUND + 1 - 2.6 * t ** 0.6 + 0.6 * math.sin(x * 0.7 - i * 1.6)
    if x > FRONT - 7:                                     # the bow wave
        u = (x - (FRONT - 7)) / 7
        top -= 4.5 * math.sin(u * math.pi * 0.85)
    return top


def water_slide() -> Sprite:
    sprite = Sprite("water_slide", SLIDE, cx=SLIDE_CX, ground=SLIDE_GROUND)
    bottom = SLIDE_GROUND + 2
    slide = []
    for i in range(4):
        c = Canvas(*SLIDE)
        rnd = noise(100 + i)
        for x in range(TAIL, FRONT + 1):
            if x < TAIL + 12 and (x * 7 + i * 3) % 5 == 0:   # the tail breaking up into separate puddles
                continue
            top = round(_sheet_top(x, i))
            for y in range(top, bottom + 1):
                depth = y - top
                foam = depth == 0 and ((x + i * 3) % 6 != 0 or x > FRONT - 5)
                colour = W[0] if foam else W[1] if depth < 2 else W[2] if y < bottom else W[3]
                c.px(x, y, colour)
        for x in range(TAIL + 4, FRONT - 6):              # streaks of foam streaming back through the water
            if (x + i * 3) % 7 == 0:
                c.px(x, bottom - 1, W[1])
                c.px(x + 1, bottom - 1, W[1])
        crest_y = round(_sheet_top(FRONT - 2, i))         # the bow wave's lip, tipping forward
        c.px(FRONT + 1, crest_y + 1, W[0])
        c.px(FRONT + 2, crest_y + 2, W[1])
        c.outline(EDGE)
        for k in range(7):                                # spray thrown up and forward off the bow
            x = FRONT - 3 + rnd() * 9
            y = crest_y - 1 - rnd() * 6
            if 0 <= y < SLIDE[1]:
                c.px(x, y, W[0] if k % 2 else W[1])
        for k in range(4):                                # foam flecks left behind at the tail
            c.px(TAIL - 3 + rnd() * 10, bottom - 1 - rnd() * 3, _alpha(W[0], 210))
        slide.append(c)
    sprite.add("slide", slide, fps=14)

    splash = []
    for i in range(5):
        c = Canvas(*SLIDE)
        rnd = noise(200 + i)
        spread = 6 + i * 4                                # a puddle spreading out under the feet
        c.rect(SLIDE_CX - spread, bottom - 1, SLIDE_CX + spread, bottom, W[2] if i < 3 else W[1])
        c.rect(SLIDE_CX - spread + 2, bottom - 1, SLIDE_CX + spread - 2, bottom - 1, W[1] if i < 3 else W[0])
        if i < 4:                                         # a crown of water thrown up round the feet
            rx, ry = 5 + i * 3.5, 3 + i * 1.6
            for k in range(9):
                a = math.radians(15 + k * 18.75)
                x, y = SLIDE_CX + math.cos(a) * rx, bottom - 1 - math.sin(a) * ry
                lean = math.cos(a) * 1.4
                length = max(1, 4 - i - abs(k - 4) * 0.4)
                c.line((x, y), (x + lean, y - length), W[0] if k % 2 else W[1])
            if i < 2:
                c.outline(EDGE)
        for k in range(12):                               # droplets flying up and back, falling as it ends
            a = math.radians(110 + rnd() * 60)
            dist = (3 + rnd() * 3) * (1 + i * 0.8)
            x = SLIDE_CX + math.cos(a) * dist * 1.6
            y = bottom - 2 - math.sin(a) * dist + i * i * 0.35
            if 0 <= y < SLIDE[1]:
                c.px(x, y, _alpha(W[0] if k % 2 else W[1], 255 if i < 3 else 255 - (i - 2) * 60))
        splash.append(c)
    sprite.add("splash", splash, fps=16, loop=False)
    return sprite


def build() -> list[Sprite]:
    return [shot_wave(), water_slide()]
