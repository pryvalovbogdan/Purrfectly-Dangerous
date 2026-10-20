"""World 3, the haunted museum: ghost cats, bats, skeleton mice and their bones, flying skulls, the
cursed bell, gravestones and the vanishing platform."""
from __future__ import annotations

import math

from PIL import Image

import palette as P
from characters.hero import CatPose, Coat, cat
from draw import Canvas, see_through, shatter, tint, vanish
from sprite import Sprite, single

GHOST = Coat(fur=P.LILAC, fur_l=P.WHITE, fur_d=P.LILAC_D, stripe=P.VIOLET, belly=P.WHITE, belly_d=P.LILAC_D,
             nose=P.VIOLET, eye=P.INDIGO, shine=P.SPIRIT, inner_ear=P.VIOLET)


def ghost_cat_frame(step: int) -> Image.Image:
    """A see-through cat drifting forward, forepaws reaching, its back half trailing off in wisps."""
    size, cx, gy = (38, 26), 19, 22
    bob = (0, -1, -1, 0)[step]
    c = Canvas(*size)
    cat(c, CatPose(front_near=(70, 80), front_far=(60, 70), back_near=(-80, -95), back_far=(-70, -90), stretch=1,
                   tilt=1, tail=20 + step * 6, curl=6, eye="wide"), cx=cx, ground=gy + bob, coat=GHOST)
    for k in range(4):                                     # wispy hem under the body
        x = cx - 7 + k * 3
        c.line((x, gy - 3 + bob), (x - 2 - (step + k) % 2, gy + 1 + bob), P.LILAC_D)
    c.outline(P.PURPLE)
    return see_through(c.img, 205)


def ghost_cat() -> Sprite:
    sprite = Sprite("ghost_cat", (38, 26), faces_left=True, cx=19, ground=22)
    floating = [ghost_cat_frame(i) for i in range(4)]
    sprite.add("float", floating, fps=6)
    # Blinking out: thinner and thinner (the game shows it as harmless while faded).
    sprite.add("fade", [see_through(floating[0], a) for a in (150, 100, 60, 30)], fps=10, loop=False)
    return sprite


def bat_frame(wing: float, eye: str = "open") -> Canvas:
    """`wing` from -1 (down) to 1 (up)."""
    c = Canvas(22, 16)
    cx, cy = 11, 8
    tip = cy - wing * 6
    for side in (-1, 1):
        x0 = cx + side * 2
        pts = [(x0, cy - 1), (cx + side * 6, tip - 1), (cx + side * 10, tip + 1), (cx + side * 8, cy + 1 - wing),
               (cx + side * 6, cy + 2 - wing * 0.5), (cx + side * 4, cy + 1), (x0, cy + 2)]
        c.poly(pts, P.PURPLE_D)
        c.line((x0, cy - 1), (cx + side * 9, tip + 0.5), P.PURPLE)
    c.ellipse(cx, cy, 3, 3.5, P.PURPLE)
    c.poly([(cx - 2.5, cy - 2), (cx - 2, cy - 6), (cx - 0.5, cy - 3)], P.PURPLE)
    c.poly([(cx + 0.5, cy - 3), (cx + 2, cy - 6), (cx + 2.5, cy - 2)], P.PURPLE)
    if eye == "x":
        c.px(cx - 1, cy - 1, P.BLACK)
        c.px(cx + 1, cy - 1, P.BLACK)
    else:
        c.px(cx - 1, cy - 1, P.YELLOW)
        c.px(cx + 1, cy - 1, P.YELLOW)
    c.px(cx - 0.5, cy + 2, P.WHITE)
    c.px(cx + 0.5, cy + 2, P.WHITE)
    return c.outline()


def bat() -> Sprite:
    sprite = Sprite("bat", (22, 16), faces_left=True, cx=11, ground=13)
    fly = [bat_frame(w).img for w in (1, 0.3, -0.8, 0.3)]
    sprite.add("fly", fly, fps=12)
    sprite.add("death", [vanish(bat_frame(-0.3, "x").img, t / 2, depth=4) for t in range(3)], fps=10, loop=False)
    return sprite


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
    """A gravestone, tall (about 14x22), with a paw print carved in it."""
    c = Canvas(20, 26)
    c.poly([(3, 24), (3, 7), (6, 3), (10, 2), (14, 3), (17, 7), (17, 24)], P.GREY)
    c.poly([(3, 24), (3, 7), (6, 3), (7, 3), (5, 8), (5, 24)], P.GREY_D)
    c.rect(1, 23, 19, 25, P.SLATE)
    c.ellipse(10, 13.5, 2.4, 1.8, P.SLATE)                  # carved paw print
    for dx, dy in ((-3, -2), (-1, -4), (1.5, -4), (3.5, -2)):
        c.rect(10 + dx - 0.5, 13 + dy - 0.5, 10 + dx, 13 + dy, P.SLATE)
    c.line((7, 18), (15, 18), P.SLATE)
    c.line((8, 20), (14, 20), P.SLATE)
    c.line((14, 4), (12, 8), P.GREY_D)                      # crack
    for x, h in ((2, 2), (4, 3), (16, 2), (18, 3)):         # dead grass at the foot
        c.line((x, 24), (x + 1, 24 - h), P.PURPLE_D)
    c.rect(4, 20, 6, 22, P.MOSS)
    c.px(7, 22, P.MOSS)
    return single("tombstone", c.outline(), ground=25)


def vanish_platform() -> Sprite:
    w, h = 48, 10
    c = Canvas(w, h)
    c.rect(0, 1, w - 1, 7, P.INDIGO)
    c.rect(0, 1, w - 1, 1, P.LILAC_D)
    for x in range(0, w, 12):                               # stone blocks with a glowing rune each
        c.line((x, 1), (x, 7), P.NIGHT)
        c.px(x + 5, 4, P.SPIRIT)
        c.px(x + 6, 3, P.SPIRIT)
        c.px(x + 7, 4, P.SPIRIT)
    for x in (6, 20, 30, 42):
        c.rect(x, 8, x + 1, 8 + (x % 3 == 0), P.PURPLE_D)
    still = c.outline(P.NIGHT).img
    sprite = Sprite("vanish", still.size)
    sprite.add("solid", [still], fps=1)
    sprite.add("fading", [see_through(still, 255), see_through(tint(still, P.SPIRIT, 0.4), 190),
                          see_through(still, 120), see_through(tint(still, P.SPIRIT, 0.4), 60)], fps=8)
    return sprite


def build() -> list[Sprite]:
    return [ghost_cat(), bat(), skeleton_mouse(), bone(), skull(), bell(), tombstone(), vanish_platform()]
