"""World 3, the haunted museum: skeleton mice and their bones, flying skulls, the cursed bell, gravestones
and the vanishing platform. The ghost cat, bat and the other museum critters are in `haunted_critters.py`."""
from __future__ import annotations

import math

from PIL import Image

import palette as P
from draw import Canvas, see_through, shatter, tint
from sprite import Sprite, single

def skeleton_mouse_frame(arm: float, holding: bool, bob: float = 0, step: int = 0) -> Canvas:
    """An upright mouse skeleton, about 18px tall: round-eared skull, ribs, a long bony tail."""
    c = Canvas(24, 28)
    x, gy = 12, 26 - bob
    for k in range(9):                                     # tail bones curling behind
        tx, ty = x - 3 - k * 0.9, gy - 2 - math.sin(k / 8 * math.pi) * 5 - (step % 2) * (k > 5)
        c.px(tx, ty, P.GREY_L if k % 2 else P.WHITE)
    c.line((x - 1, gy - 5), (x - 2, gy), P.GREY_L)          # legs
    c.line((x + 1, gy - 5), (x + 2, gy), P.WHITE)
    c.rect(x - 3, gy, x - 1, gy, P.GREY_L)
    c.rect(x + 1, gy, x + 3, gy, P.WHITE)
    c.ellipse(x, gy - 6, 2.5, 1.2, P.GREY_L)                # pelvis
    c.line((x, gy - 6), (x, gy - 13), P.WHITE)              # spine and ribs
    for k in range(3):
        y = gy - 8 - k * 2
        c.line((x - 2.5 + k * 0.3, y), (x + 2.5 - k * 0.3, y), P.WHITE)
    hx, hy = x + 1.5, gy - 16.5                              # skull with two big round ears
    c.ellipse(hx - 3.5, hy - 3, 2.4, 2.4, P.WHITE)
    c.ellipse(hx - 3.5, hy - 3, 1.2, 1.2, P.LILAC_D)
    c.ellipse(hx - 0.5, hy - 4, 2.2, 2.2, P.GREY_L)
    c.ellipse(hx, hy, 3.2, 2.8, P.WHITE)
    c.poly([(hx + 2, hy - 2), (hx + 6, hy + 0.5), (hx + 2, hy + 2.5)], P.WHITE)
    c.px(hx + 6, hy + 0.5, P.SLATE)
    c.rect(hx + 0.5, hy - 1.5, hx + 1.5, hy - 0.5, P.NIGHT)  # eye socket with a glint
    c.px(hx + 1, hy - 1, P.SPIRIT)
    c.rect(hx + 2.5, hy + 1.5, hx + 4.5, hy + 1.5, P.GREY)   # teeth line
    sx, sy = x + 0.5, gy - 12
    rad = math.radians(arm)
    elbow = (sx + math.sin(rad) * 3, sy + math.cos(rad) * 3)
    hand = (elbow[0] + math.sin(rad + 0.5) * 3, elbow[1] + math.cos(rad + 0.5) * 3)
    c.line((sx, sy), elbow, P.WHITE)
    c.line(elbow, hand, P.WHITE)
    if holding:
        bone_shape(c, hand[0], hand[1] - 1, 0.6, 3)
    return c.outline(P.NIGHT)


def bone_shape(c: Canvas, x: float, y: float, angle: float, half: float = 3.5) -> None:
    dx, dy = math.cos(angle) * half, math.sin(angle) * half
    c.line((x - dx, y - dy), (x + dx, y + dy), P.WHITE, 2)
    for sx in (-1, 1):
        ex, ey = x + dx * sx, y + dy * sx
        nx, ny = -math.sin(angle), math.cos(angle)
        c.rect(ex + nx - 0.5, ey + ny - 0.5, ex + nx + 0.5, ey + ny + 0.5, P.CREAM)
        c.rect(ex - nx - 0.5, ey - ny - 0.5, ex - nx + 0.5, ey - ny + 0.5, P.CREAM)


def skeleton_mouse() -> Sprite:
    sprite = Sprite("skeleton_mouse", (24, 28), faces_left=True, cx=12, ground=26)
    sprite.add("idle", [skeleton_mouse_frame(30, True).img, skeleton_mouse_frame(36, True, 0.5, 1).img], fps=3)
    sprite.add("throw", [skeleton_mouse_frame(a, h).img for a, h in ((-40, True), (-150, True), (150, False),
                                                                      (80, False))], fps=10, loop=False)
    still = skeleton_mouse_frame(30, False).img
    # Clatters into a heap of bones and fades.
    frames = [tint(still, P.WHITE, 0.7)]
    for t in (0.4, 0.75):
        frames.append(shatter(still, t, 111, block=3, spread=0.12, gravity=0.7))
    frames.append(see_through(shatter(still, 0.95, 111, block=3, spread=0.12, gravity=0.7), 110))
    sprite.add("death", frames, fps=10, loop=False)
    return sprite


def bone() -> Sprite:
    sprite = Sprite("bone", (10, 10), faces_left=True)
    frames = []
    for k in range(4):
        c = Canvas(10, 10)
        bone_shape(c, 4.5, 4.5, -k * math.pi / 4)
        frames.append(c.outline(P.NIGHT).img)
    sprite.add("fly", frames, fps=16)
    return sprite


def skull_frame(step: int, eye: str = "open") -> Canvas:
    c = Canvas(20, 14)
    x, y = 12, 7
    for k in range(4):                                     # ghost fire streaming behind
        fx = x - 4 - k * 2
        h = 3.2 - k * 0.6 + ((step + k) % 2) * 0.6
        c.ellipse(fx, y + (k % 2) * 0.5 - 0.5, 1.6, h, P.VIOLET if k < 2 else P.PURPLE)
    c.ellipse(x, y - 0.5, 4.5, 4.2, P.WHITE)
    c.rect(x - 1, y + 2, x + 4, y + 5, P.WHITE)            # jaw
    c.rect(x - 1, y + 3.5, x + 4, y + 3.5, P.GREY_L)
    for tx in (0, 2, 4):
        c.px(x - 1 + tx, y + 4.5, P.GREY_L)
    c.rect(x - 3.5, y - 2, x - 2.5, y + 1, P.LILAC_D)
    if eye == "x":
        c.px(x + 2, y - 1, P.NIGHT)
    else:
        c.rect(x + 1, y - 2, x + 3, y, P.NIGHT)
        c.px(x + 2, y - 1, P.SPIRIT if step % 2 else P.VIOLET)
    c.px(x + 4, y + 1, P.NIGHT)
    return c.outline(P.NIGHT)


def skull() -> Sprite:
    sprite = Sprite("skull", (20, 14), faces_left=True, cx=12, ground=12)
    sprite.add("fly", [skull_frame(i).img for i in range(4)], fps=12)
    sprite.add("death", [shatter(skull_frame(0).img, t / 2, 121, block=3, spread=0.8) for t in range(3)],
               fps=12, loop=False)
    return sprite


def bell_frame(swing: float, rings: int = 0) -> Image.Image:
    """A cracked bronze bell on a chain; `swing` in degrees, `rings` draws sound rings below."""
    size = (24, 30)
    body = Canvas(*size)
    cx = 12
    for y in range(0, 9, 2):                                # chain
        body.rect(cx - 0.5, y, cx + 0.5, y + 0.5, P.GREY)
    body.poly([(cx - 3, 10), (cx + 3, 10), (cx + 5, 17), (cx + 7, 21), (cx - 7, 21), (cx - 5, 17)], P.GOLD_D)
    body.ellipse(cx, 11, 3.5, 2.5, P.GOLD_D)
    body.poly([(cx - 2, 10), (cx, 10), (cx - 2, 19), (cx - 4, 19)], P.GOLD)
    body.rect(cx - 7, 20, cx + 7, 21, P.BROWN)
    body.line((cx + 2, 12), (cx + 3, 15), P.BROWN_D)        # crack
    body.line((cx + 3, 15), (cx + 2, 17), P.BROWN_D)
    body.ellipse(cx, 22.5, 1.5, 1.5, P.BROWN_D)             # clapper
    body.px(cx - 4, 18, P.SPIRIT)                           # a ghostly rune glowing on it
    body.px(cx - 3, 17, P.SPIRIT)
    body.outline()
    out = Canvas(*size)
    out.paste(body.img.rotate(swing, resample=Image.NEAREST, center=(cx, 0)))
    for k in range(rings):
        rad = 4 + k * 3
        for a in range(0, 180, 12):
            ang = math.radians(a)
            out.px(cx + math.cos(ang) * (rad + 4), 23 + math.sin(ang) * rad * 0.45, P.VIOLET if k % 2 else P.LILAC)
    return out.img


def bell() -> Sprite:
    sprite = Sprite("bell", (24, 30), ground=29)
    sprite.add("idle", [bell_frame(-3), bell_frame(3)], fps=2)
    sprite.add("ring", [bell_frame(-14, 1), bell_frame(0, 2), bell_frame(14, 3), bell_frame(0, 2)], fps=10,
               loop=False)
    return sprite


def tombstone() -> Sprite:
    """A gothic violet gravestone (about 14x22): a pointed top with two cat ears, a glowing magenta cat crest,
    a stepped plinth and a candle stub at its foot."""
    c = Canvas(20, 26)
    c.poly([(3, 23), (3, 9), (6, 5), (10, 2), (14, 5), (17, 9), (17, 23)], P.HM_STONE)
    c.poly([(5, 6), (4, 1), (8, 4)], P.HM_STONE)              # ears
    c.poly([(15, 6), (16, 1), (12, 4)], P.HM_STONE_D)
    c.poly([(3, 23), (3, 9), (6, 5), (7, 5), (5, 10), (5, 23)], P.HM_STONE_L)   # lit side
    c.poly([(15, 9), (17, 9), (17, 23), (15, 23)], P.HM_STONE_D)
    c.ellipse(10, 12, 3.5, 3, P.HM_GLASS_D)                   # the crest: a glowing cat face
    c.ellipse(10, 12, 2.5, 2, P.HM_GLASS)
    c.poly([(7, 11), (7.5, 8), (9, 10)], P.HM_GLASS)
    c.poly([(13, 11), (12.5, 8), (11, 10)], P.HM_GLASS)
    c.px(9, 12, P.HM_GLASS_L)
    c.px(11, 12, P.HM_GLASS_L)
    c.line((7, 17), (13, 17), P.HM_STONE_D)                   # carved lines
    c.line((8, 19), (12, 19), P.HM_STONE_D)
    c.line((14, 6), (13, 9), P.HM_STONE_D)                    # crack
    c.rect(1, 22, 19, 25, P.HM_STONE_D)                       # plinth
    c.rect(1, 22, 19, 22, P.HM_STONE_L)
    c.rect(2, 24, 18, 24, P.HM_STONE_DD)
    c.rect(16, 19, 17, 21, P.HM_WAX)                          # a candle stub at the foot, small and calm
    c.px(16, 18, P.HM_FLAME)
    c.px(18, 21, P.HM_WAX_D)
    return single("tombstone", c.outline(P.HM_STONE_DD), ground=25)


def vanish_platform() -> Sprite:
    """48x10 floating stone slab (walk surface = the lit top row): bricks with two candles set in niches in its
    face, and a rocky underside glowing magenta. It fades out with a pink spirit flicker."""
    w, h = 48, 10
    c = Canvas(w, h)
    c.poly([(2, 6), (46, 6), (40, 8), (30, 9), (24, 9), (12, 8)], P.HM_STONE_D)    # rocky underside
    for x, d in ((9, 1), (16, 2), (23, 3), (31, 2), (38, 1)):
        c.poly([(x - 2, 7), (x + 2, 7), (x, 7 + d)], P.HM_STONE_DD)
        c.px(x, 7, P.HM_GLASS_D)
    for k, x in enumerate(range(0, w, 12)):                    # the slab's bricks
        x1 = min(x + 11, w - 1)
        c.rect(x, 1, x1, 5, P.HM_STONE)
        c.rect(x, 1, x1, 1, P.HM_STONE_L)
        c.rect(x, 5, x1, 5, P.HM_STONE_D)
        c.rect(x1, 1, x1, 5, P.HM_STONE_DD)
    c.rect(0, 0, w - 1, 0, P.HM_STONE_TOP)                     # lit walk surface
    for x in (7, 39):                                         # candles in niches in the face
        c.rect(x - 2, 2, x + 2, 5, P.HM_STONE_DD)
        c.rect(x - 1, 4, x, 5, P.HM_WAX)
        c.px(x - 1, 3, P.HM_FLAME)
        c.px(x, 3, P.HM_FLAME_D)
    slab = c.outline(P.HM_STONE_DD).img
    under = Canvas(w, h)                                      # the magenta glow under it, blended behind
    under.ellipse(24, 8, 22, 2.5, (P.HM_GLASS[0], P.HM_GLASS[1], P.HM_GLASS[2], 70))
    under.paste(slab)
    still = under.img
    sprite = Sprite("vanish", still.size)
    sprite.add("solid", [still], fps=1)
    sprite.add("fading", [see_through(still, 255), see_through(tint(still, P.HM_GLASS_L, 0.4), 190),
                          see_through(still, 120), see_through(tint(still, P.HM_GLASS_L, 0.4), 60)], fps=8)
    return sprite


def build() -> list[Sprite]:
    return [skeleton_mouse(), bone(), skull(), bell(), tombstone(), vanish_platform()]
