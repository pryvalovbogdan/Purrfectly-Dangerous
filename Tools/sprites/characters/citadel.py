"""World 4, the citadel: flame vents, pistons, wall cannons and cannonballs, falling debris,
mechanical mice, spinning gears and the breakable crate wall."""
from __future__ import annotations

import math

from PIL import Image

import palette as P
from draw import Canvas, noise, shatter, tint, vanish
from sprite import Sprite, single


def flame_column(c: Canvas, cx: float, bottom: float, height: float, step: int, width: float = 5) -> None:
    rnd = noise(130 + step)
    for y in range(int(bottom - height), int(bottom) + 1):
        t = (bottom - y) / height                           # 0 at the base, 1 at the tip
        half = width * (1 - t * 0.55) + math.sin(y * 0.7 + step * 1.9) * 1.2
        wobble = math.sin(y * 0.33 + step * 1.3) * 1.5 * t
        c.rect(cx - half + wobble, y, cx + half + wobble, y, P.RED)
        c.rect(cx - half * 0.65 + wobble, y, cx + half * 0.65 + wobble, y, P.LAVA)
        if t < 0.75:
            c.rect(cx - half * 0.3 + wobble, y, cx + half * 0.3 + wobble, y, P.LAVA_L)
        if t < 0.35:
            c.rect(cx - half * 0.12 + wobble, y, cx + half * 0.12 + wobble, y, P.CC_LAVA_W)
    for _ in range(4):
        c.px(cx + (rnd() - 0.5) * width * 2.5, bottom - height - rnd() * 5, P.LAVA_L)
    for _ in range(3):                                      # embers along the sides
        c.px(cx + (rnd() - 0.5) * width * 3, bottom - rnd() * height, P.CC_EMBER)


def vent() -> Sprite:
    """A floor grate that fires a flame column about 12x60."""
    size, cx, gy = (22, 68), 11, 67

    def grate(glow) -> Canvas:
        c = Canvas(*size)
        c.rect(1, gy - 4, 20, gy, P.CC_STONE)                # charred stone housing
        c.rect(1, gy - 4, 20, gy - 4, P.CC_STONE_TOP)
        c.rect(1, gy, 20, gy, P.CC_STONE_D)
        c.rect(3, gy - 3, 18, gy - 1, P.IRON_D)              # iron grate over the glow
        for x in range(4, 19, 3):
            c.rect(x, gy - 3, x + 1, gy - 1, glow)
        for x in (2, 19):                                   # rivets
            c.px(x, gy - 2, P.CC_STONE_L)
        return c

    sprite = Sprite("vent", size, cx=cx, ground=gy)
    sprite.add("idle", [grate(P.IRON_D).outline().img], fps=1)
    warn = []
    for i in range(2):
        c = grate(P.LAVA if i else P.RED)
        for k in range(3):
            c.px(cx - 4 + k * 4 + i, gy - 7 - ((k + i) % 2) * 3, P.LAVA_L if i else P.LAVA)
        warn.append(c.outline().img)
    sprite.add("warn", warn, fps=8)
    fire = []
    for i in range(4):
        c = grate(P.LAVA_L)
        c.outline()
        flame_column(c, cx, gy - 4, 58 + (i % 2) * 3, i)
        fire.append(c.img)
    sprite.add("fire", fire, fps=14)
    return sprite


def piston() -> Sprite:
    """Hangs from the ceiling and slams down to the ground; the head is 20 wide, 72 tall slammed."""
    size, cx, gy = (24, 76), 12, 75

    def frame(head_bottom: float, light, dust: int = 0, shake: float = 0) -> Image.Image:
        c = Canvas(*size)
        top = head_bottom - 11
        c.rect(cx - 3 + shake, 0, cx + 2 + shake, top, P.IRON)        # shaft
        c.rect(cx - 3 + shake, 0, cx - 2 + shake, top, P.IRON_L)
        for y in range(3, int(top), 6):
            c.rect(cx - 3 + shake, y, cx + 2 + shake, y, P.IRON_D)
        c.rect(cx - 6 + shake, top - 3, cx + 5 + shake, top, P.CC_STONE)   # collar
        c.rect(2 + shake, top, 21 + shake, head_bottom, P.CC_STONE)        # charred iron head
        c.rect(2 + shake, top, 21 + shake, top + 1, P.CC_STONE_TOP)
        c.rect(2 + shake, top + 2, 2 + shake, head_bottom - 5, P.CC_STONE_L)
        c.rect(3 + shake, top + 6, 20 + shake, top + 6, P.CC_LAVA_D)       # a glowing seam
        c.px(8 + shake, top + 6, P.LAVA)
        c.px(16 + shake, top + 6, P.LAVA)
        for rx in (4, 19):                                                 # rivets
            c.px(rx + shake, top + 3, P.CC_STONE_L)
        for k in range(5):                                  # hazard stripes
            x = 3 + k * 4 + shake
            c.poly([(x, head_bottom - 3), (x + 2, head_bottom - 3), (x + 4, head_bottom), (x + 2, head_bottom)],
                   P.GOLD)
        c.rect(2 + shake, head_bottom - 4, 21 + shake, head_bottom - 4, P.IRON_D)
        c.ellipse(cx + shake, top + 4, 1.5, 1.5, light)     # warning lamp
        c.outline()
        for k in range(dust):
            for side in (-1, 1):
                x = cx + side * (12 + k * 2)
                c.rect(x - 0.5, gy - k - 1, x + 0.5, gy - k, P.GREY_L)
        return c.img

    sprite = Sprite("piston", size, cx=cx, ground=gy)
    sprite.add("up", [frame(20, P.IRON_D)], fps=1)
    sprite.add("warn", [frame(20, P.RED, shake=-1), frame(21, P.LAVA_L, shake=1)], fps=10)
    sprite.add("slam", [frame(50, P.LAVA_L), frame(75, P.LAVA_L, dust=1), frame(75, P.RED, dust=2)], fps=16,
               loop=False)
    return sprite


def cannon_body(c: Canvas, recoil: float = 0, flash: int = 0) -> None:
    gy = 19
    c.rect(2, gy - 5, 16, gy - 1, P.IRON_D)                 # carriage
    c.rect(2, gy - 5, 16, gy - 5, P.IRON)
    for wx in (5, 13):                                      # iron wheels
        c.ellipse(wx, gy - 2, 2.5, 2.5, P.CC_STONE)
        c.px(wx, gy - 2, P.CC_STONE_DD)
        c.px(wx - 1, gy - 3, P.CC_STONE_L)
    c.px(9, gy - 4, P.CC_BANNER)                            # a red cat crest on the carriage
    c.px(8, gy - 5, P.CC_BANNER)
    c.px(10, gy - 5, P.CC_BANNER)
    bx = 3 - recoil
    c.poly([(bx, gy - 12), (bx + 15, gy - 12.5), (bx + 15, gy - 7.5), (bx, gy - 7)], P.IRON)   # barrel
    c.rect(bx, gy - 12, bx + 15, gy - 12, P.IRON_L)
    c.rect(bx + 15, gy - 13.5, bx + 17, gy - 6.5, P.IRON_D)                                    # muzzle ring
    c.ellipse(bx + 1, gy - 9.5, 2.5, 3, P.IRON_D)
    c.px(bx + 6, gy - 11, P.LAVA)                            # glowing fuse
    c.px(bx + 7, gy - 13, P.LAVA_L)
    if flash:
        mx = bx + 19
        c.ellipse(mx + 1, gy - 10, 2.5 + flash, 2 + flash * 0.6, P.LAVA)
        c.ellipse(mx + 1, gy - 10, 1.2 + flash * 0.5, 1 + flash * 0.3, P.LAVA_L)


def cannon() -> Sprite:
    """Fires at head height: the muzzle is about 10 above the ground."""
    size = (30, 20)
    sprite = Sprite("cannon", size, faces_left=True, cx=10, ground=19)

    def frame(recoil=0, flash=0) -> Image.Image:
        c = Canvas(*size)
        cannon_body(c, recoil, 0)
        c.outline()
        if flash:
            cannon_body(c, recoil, flash)
        return c.img

    still = frame()
    sprite.add("idle", [still], fps=1)
    sprite.add("fire", [frame(0, 2), frame(2, 1), frame(1, 0)], fps=12, loop=False)
    sprite.add("death", [tint(still, P.WHITE, 0.7)] + [shatter(still, t / 3, 141, block=4, spread=0.7)
                                                       for t in (1, 2, 3)], fps=12, loop=False)
    return sprite


def cannonball() -> Sprite:
    sprite = Sprite("cannonball", (16, 10), faces_left=True)
    frames = []
    for i in range(4):
        c = Canvas(16, 10)
        for k in range(4):                                  # fire trail
            x = 8 - 2 - k * 2
            h = 2.6 - k * 0.5 + ((i + k) % 2) * 0.5
            c.ellipse(x, 4.5 + ((i + k) % 3 - 1) * 0.4, 1.8, h, P.LAVA if k < 2 else P.RED)
        c.ellipse(10.5, 4.5, 3.5, 3.5, P.IRON_D)
        c.ellipse(10, 4, 2, 2, P.IRON)
        c.px(9.5, 3, P.IRON_L)
        c.px(13, 6, P.LAVA)
        frames.append(c.outline().img)
    sprite.add("fly", frames, fps=14)
    return sprite


def debris() -> Sprite:
    """A broken chunk of masonry on a chain; hangs from above, falls and shatters."""
    size = (18, 22)
    sprite = Sprite("debris", size)

    def chunk(sway: float = 0, chain: bool = True) -> Image.Image:
        c = Canvas(*size)
        if chain:
            for y in range(0, 8, 2):
                c.rect(8.5 + sway * y / 8, y, 9.5 + sway * y / 8, y + 0.5, P.IRON if (y // 2) % 2 else P.IRON_L)
        c.poly([(3 + sway, 9), (14 + sway, 8), (16 + sway, 14), (13 + sway, 20), (5 + sway, 21), (2 + sway, 15)],
               P.CC_STONE)
        c.poly([(3 + sway, 9), (14 + sway, 8), (13 + sway, 11), (4 + sway, 12)], P.CC_STONE_L)
        c.line((8 + sway, 12), (10 + sway, 17), P.LAVA)                 # a glowing crack through the chunk
        c.line((10 + sway, 17), (7 + sway, 20), P.CC_LAVA_D)
        c.px(9 + sway, 14, P.LAVA_L)
        c.rect(12 + sway, 14, 13 + sway, 15, P.CC_STONE_D)
        return c.outline().img

    sprite.add("hang", [chunk(-0.5), chunk(0.5)], fps=3)
    loose = chunk(chain=False)
    fall = []
    for k in range(2):
        c = Canvas(*size)
        c.paste(loose, 0, 1)
        for x in (5, 12):
            c.line((x, 0), (x, 4 + k * 2), P.IRON_L)
        fall.append(c.img)
    sprite.add("fall", fall, fps=12)
    sprite.add("shatter", [shatter(loose, t, 151, block=3, spread=1.0, origin=(9, 22)) for t in (0, 0.3, 0.55, 0.8)],
               fps=14, loop=False)
    return sprite


def mech_mouse_frame(step: int, eye=P.RED) -> Canvas:
    c = Canvas(32, 20)
    x, gy = 15, 18
    bob = (0, 1, 0, 1)[step]
    for k in range(5):                                      # cable tail
        c.px(x - 8 - k, gy - 4 - math.sin(k * 0.8 + step) * 1.5, P.IRON_L)
    for wx, phase in ((x - 4, 0), (x + 4, 1)):              # wheels
        c.ellipse(wx, gy - 2, 2.5, 2.5, P.IRON_D)
        a = (step + phase) * math.pi / 2
        c.px(wx + math.cos(a) * 1.5, gy - 2 + math.sin(a) * 1.5, P.IRON_L)
    c.ellipse(x, gy - 6 - bob * 0.5, 8, 5, P.IRON)          # dome body
    c.ellipse(x - 1, gy - 8 - bob * 0.5, 5, 2.5, P.IRON_L)
    for rx in (-5, -1, 3):                                  # rivets
        c.px(x + rx, gy - 3 - bob * 0.5, P.IRON_D)
    c.poly([(x + 6, gy - 9), (x + 13, gy - 5), (x + 6, gy - 3)], P.IRON)   # pointed snout
    c.px(x + 13, gy - 5, P.LAVA)
    c.ellipse(x + 4, gy - 11 - bob * 0.5, 2.5, 2.5, P.IRON_L)               # round ear
    c.ellipse(x + 4, gy - 11 - bob * 0.5, 1.2, 1.2, P.MAROON)
    c.rect(x + 7, gy - 7, x + 8, gy - 6, eye)               # glowing eye
    c.rect(x - 4, gy - 13 - bob * 0.5, x - 3, gy - 10, P.GOLD_D)            # wind-up key
    key = step % 2
    c.rect(x - 6 + key, gy - 15, x - 1 - key, gy - 13, P.GOLD)
    for k in range(2):                                      # sparks off the wheels
        c.px(x - 10 - k * 2 - step % 2, gy - k, P.LAVA_L)
    return c.outline()


def mech_mouse() -> Sprite:
    sprite = Sprite("mech_mouse", (32, 20), faces_left=True, cx=15, ground=18)
    sprite.add("run", [mech_mouse_frame(i).img for i in range(4)], fps=16)
    broken = mech_mouse_frame(0, P.IRON_D).img
    sprite.add("death", [tint(broken, P.WHITE, 0.7)] + [shatter(broken, t / 3, 161, block=4, spread=0.1, gravity=0.6)
                                                        for t in (1, 2, 3)], fps=12, loop=False)
    return sprite


def gear() -> Sprite:
    """A big gear turning on a post: a tall obstacle (about 24x27)."""
    size, cx, cy, gy = (30, 30), 15, 14, 29
    sprite = Sprite("gear", size, cx=cx, ground=gy)
    frames = []
    teeth = 8
    for i in range(4):
        c = Canvas(*size)
        c.rect(cx - 2, cy, cx + 2, gy - 2, P.IRON_D)        # post and a charred stone foot
        c.rect(cx - 7, gy - 2, cx + 7, gy, P.CC_STONE)
        c.rect(cx - 7, gy - 2, cx + 7, gy - 2, P.CC_STONE_TOP)
        offset = i / 4 * math.tau / teeth
        for k in range(teeth):
            a = offset + k * math.tau / teeth
            c.line((cx + math.cos(a) * 8, cy + math.sin(a) * 8), (cx + math.cos(a) * 10.5, cy + math.sin(a) * 10.5),
                   P.IRON, 3)
            c.px(cx + math.cos(a) * 10.5, cy + math.sin(a) * 10.5, P.CC_EMBER)   # teeth glowing hot
        c.ellipse(cx, cy, 9, 9, P.GOLD_D)
        c.ellipse(cx, cy, 7, 7, P.GOLD)
        for k in range(4):                                  # spokes
            a = offset + k * math.pi / 2 + math.pi / 4
            c.line((cx, cy), (cx + math.cos(a) * 6, cy + math.sin(a) * 6), P.GOLD_D, 2)
        c.ellipse(cx, cy, 2.5, 2.5, P.IRON)
        c.px(cx - 1, cy - 1, P.IRON_L)
        c.px(cx - 4, cy - 5, P.YELLOW)
        frames.append(c.outline().img)
    sprite.add("spin", frames, fps=10)
    return sprite


def crate(c: Canvas, x: float, y: float, w: float, h: float, crest: bool = False) -> None:
    c.rect(x, y, x + w - 1, y + h - 1, P.BARK_D)            # scorched planks
    for k in range(1, 3):
        c.line((x, y + k * h / 3), (x + w - 1, y + k * h / 3), P.BARK_DD)
    c.line((x + 1, y + 1), (x + w - 2, y + h - 2), P.BARK, 2)                   # brace
    if crest:                                              # a red cat crest painted on it
        mx, my = x + w / 2, y + h / 2
        c.ellipse(mx, my, 3, 2.5, P.CC_BANNER)
        c.poly([(mx - 3, my - 1), (mx - 2.5, my - 5), (mx - 0.5, my - 2)], P.CC_BANNER)
        c.poly([(mx + 3, my - 1), (mx + 2.5, my - 5), (mx + 0.5, my - 2)], P.CC_BANNER)
        c.px(mx - 1, my, P.CC_BANNER_D)
        c.px(mx + 1, my, P.CC_BANNER_D)
    c.rect(x, y, x + w - 1, y + 1, P.IRON)                  # iron bands
    c.rect(x, y + h - 2, x + w - 1, y + h - 1, P.IRON)
    for cx in (x + 1, x + w - 2):
        c.px(cx, y + 0.5, P.IRON_L)
        c.px(cx, y + h - 1.5, P.IRON_L)


def crate_wall() -> Sprite:
    """Crates stacked far past jump height (about 18x120); only Super Pounce breaks it."""
    size, gy = (24, 124), 123
    c = Canvas(*size)
    for k in range(6):                                       # six crates, slightly staggered
        crate(c, 3 + (k % 2), gy - 19 - k * 20, 18, 20, crest=k in (1, 4))
    for x, y in ((8, 14), (10, 52), (7, 93)):                # paw-scratch marks
        for k in range(3):
            c.line((x + k * 2, y), (x + k * 2 + 2, y + 4), P.CC_EMBER)
    wall = c.outline().img
    sprite = Sprite("crate_wall", size, ground=gy)
    sprite.add("still", [wall], fps=1)
    frames = [tint(wall, P.WHITE, 0.6)]
    for t in (0.15, 0.35, 0.6, 0.9):                        # bursts away from the kitten (to the right)
        frames.append(shatter(wall, t, 171, block=5, spread=0.5, gravity=1.0, origin=(-10, 100)))
    sprite.add("break", frames, fps=14, loop=False)
    return sprite


def build() -> list[Sprite]:
    return [vent(), piston(), cannon(), cannonball(), debris(), mech_mouse(), gear(), crate_wall()]
