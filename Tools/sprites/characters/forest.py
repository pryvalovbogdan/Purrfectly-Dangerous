"""World 1, the forest: the Squirrel Thief (running and on a branch) and its acorns, the Spiky Hedgehog Cat,
rose bushes, stumps, spilled milk and the crumbling bridge. Creatures are drawn facing right and mirrored on
export; the other forest critters are in `forest_critters.py`."""
from __future__ import annotations

import math

from PIL import Image

import palette as P
from critters import ear, face, ramp, shaded, sparkle
from draw import Canvas, noise, shatter, vanish
from sprite import Sprite, single
import woodland as W


# --- squirrel thief, acorns ---------------------------------------------------------------------

FUR = ramp((P.RUST_L, P.RUST, P.RUST_D), (P.FUR_WHITE, P.CREAM, P.CREAM_D))
NUT = ramp((P.PLANK_L, P.PLANK, P.PLANK_D), (P.BARK_L, P.BARK, P.BARK_D))


def bushy_tail(c: Canvas, base: tuple[float, float], sway: float, size: float = 1.0) -> None:
    """The Squirrel Thief's huge tail: rises behind the rump and curls forward at the top."""
    bx, by = base
    path = [(0, 0), (-2.5, -2.5), (-4.5, -5.5), (-5.5, -9), (-5, -12.5), (-3, -15), (0, -15.5), (1.5, -13.5)]
    pts = [(bx + x * size + sway * (i / len(path)) ** 1.5 * 2, by + y * size) for i, (x, y) in enumerate(path)]
    with shaded(c, FUR, up=2, down=2, right=2) as p:
        for i, (x, y) in enumerate(pts):
            rad = (2.2 + 1.6 * math.sin(i / (len(pts) - 1) * math.pi * 0.9)) * size
            p.ellipse(x, y, rad, rad, P.RUST)
    for (x0, y0), (x1, y1) in zip(pts[2:-2], pts[3:-1]):                # the paler curl inside the tail
        c.line((x0 + 1.4 * size, y0 + 0.5), (x1 + 1.4 * size, y1 + 0.5), P.RUST_L)
    c.px(pts[-1][0] - 0.5, pts[-1][1] + 1, P.CREAM_D)
    for k in (2, 3, 4, 5):                                              # fur tufts along the back of the tail
        c.px(pts[k][0] - 3 * size, pts[k][1] + (k % 2), P.RUST_D)


def _leg_points(hip, thigh_angle: float, bend: float, thigh: float = 3.5, shin: float = 3.5):
    knee = (hip[0] + math.sin(math.radians(thigh_angle)) * thigh, hip[1] + math.cos(math.radians(thigh_angle)) * thigh)
    shin_angle = thigh_angle - bend
    ankle = (knee[0] + math.sin(math.radians(shin_angle)) * shin, knee[1] + math.cos(math.radians(shin_angle)) * shin)
    return knee, ankle


def squirrel(c: Canvas, x: float, ground: float, phase: float = 0.0, *, sway: float = 0, arm: float = 40,
             eye: str = "open", mouth: str = "w", holding: bool = False, lift: float = 0, run: bool = True) -> dict:
    """The Squirrel Thief: an orange squirrel with a cat's face, cream muzzle and belly, a teal scarf
    and a tail as big as itself; about 26px tall (30 with its ears), feet on `ground` at `x`.

    Running, the legs stride: each has a thigh, a shin that folds back on the recovery stroke, and a long
    hind foot that lands flat."""
    stride = 48 if run else 8
    legs = []
    for ph, colour in ((phase + math.pi, P.RUST_D), (phase, P.RUST)):         # far leg first
        angle = math.sin(ph) * stride
        bend = (55 * max(0.0, -math.cos(ph)) + 10) if run else 5
        legs.append((angle, bend, colour))
    probe = [(_leg_points((0, 0), a, b)[1][1]) for a, b, _ in legs]
    hip_y = ground - max(probe) - lift - (abs(math.sin(phase)) * 1.0 if run else 0)
    hip = (x - 1.5, hip_y)
    gy = hip_y + 7                                                         # body reference line
    bushy_tail(c, (x - 5, gy - 4), sway, 1.02)

    def leg(on: Canvas, spec) -> None:
        angle, bend, colour = spec
        knee, ankle = _leg_points(hip, angle, bend)
        on.ellipse(hip[0] + (knee[0] - hip[0]) * 0.4, hip[1] + (knee[1] - hip[1]) * 0.4, 2.2, 2.2, colour)  # thigh
        on.line(hip, knee, colour, 3)
        on.line(knee, ankle, colour, 2)
        on.rect(ankle[0] - 1, ankle[1] - 0.5, ankle[0] + 3, ankle[1] + 0.5, colour)       # long hind foot

    with shaded(c, FUR, P.OUTLINE) as p:
        leg(p, legs[0])
    with shaded(c, FUR, up=2) as p:
        p.ellipse(x + 0.5, gy - 11, 6, 6.2, P.RUST)                      # body
        p.ellipse(x - 2, gy - 6.5, 4.4, 3.8, P.RUST)                      # haunch
    c.ellipse(x + 3, gy - 10.5, 2.2, 4, P.CREAM)                         # belly
    c.px(x + 2.5, gy - 13, P.FUR_WHITE)
    with shaded(c, FUR, P.OUTLINE) as p:
        leg(p, legs[1])
    hx, hy = x + 4, gy - 18.5
    with shaded(c, FUR, P.OUTLINE, up=2) as p:
        ear(p, hx - 4, hy - 4, 5.5, P.RUST, inner=P.PINK_D, lean=-1.2, half=2.6)
        ear(p, hx + 2.5, hy - 4.5, 5.5, P.RUST, inner=P.PINK_D, lean=0.4, half=2.6)
        p.ellipse(hx, hy, 6.2, 5.4, P.RUST)
        p.ellipse(hx + 4, hy + 2, 3.2, 2.4, P.RUST)                     # snout
    c.px(hx - 5.5, hy - 10, P.RUST_L)                                    # ear tufts
    c.px(hx - 5, hy - 9, P.RUST_L)
    c.px(hx + 3, hy - 10.5, P.RUST_L)
    c.ellipse(hx + 3.5, hy + 2.8, 3.2, 1.8, P.CREAM)                    # cream muzzle and cheek
    c.ellipse(hx - 3.5, hy + 1.5, 1.6, 1.2, P.CREAM)
    face(c, hx + 2, hy - 3, eyes=eye, mouth=mouth, gap=5, nose=P.BARK_DD, size=3)
    with shaded(c, ramp((P.CYAN, P.TEAL, P.DIST_D))) as p:              # teal scarf, its end streaming back
        p.rect(hx - 4, hy + 4.5, hx + 3, hy + 6, P.TEAL)
        p.line((hx - 4, hy + 5.5), (hx - 7 - abs(math.sin(phase)) * 2, hy + 7.5), P.TEAL, 2)
    sx, sy = x + 3, gy - 13
    rad = math.radians(arm)
    elbow = (sx + math.sin(rad) * 3, sy + math.cos(rad) * 3)
    hand = (elbow[0] + math.sin(rad + 0.5) * 2.5, elbow[1] + math.cos(rad + 0.5) * 2.5)
    with shaded(c, FUR, P.OUTLINE) as p:
        p.line((sx, sy), elbow, P.RUST, 2)
        p.line(elbow, hand, P.RUST, 2)
    c.px(hand[0], hand[1], P.CREAM_D)
    if holding:
        acorn_shape(c, hand[0] + 1.5, hand[1] - 2, 0.95)
    return {"hand": hand, "head": (hx, hy)}


def acorn_shape(c: Canvas, x: float, y: float, s: float = 1.0) -> None:
    """A glossy acorn standing upright, centred at (x, y), about 8*s px tall."""
    with shaded(c, NUT) as p:
        p.ellipse(x, y + 1 * s, 3.1 * s, 3.5 * s, P.PLANK)               # nut
        p.px(x, y + 4.6 * s, P.PLANK)
    c.px(x - 1.2 * s, y + 0.2 * s, P.PLANK_L)
    if s >= 0.9:
        c.px(x - 1.5 * s, y + 1.2 * s, P.WHITE)
    if s >= 1.2:
        c.px(x - 1.5 * s, y + 1.2 * s - 1, P.WHITE)
        c.line((x + 1.8 * s, y), (x + 1.4 * s, y + 3 * s), P.PLANK_D)
    with shaded(c, NUT) as p:
        p.ellipse(x, y - 1.8 * s, 3.8 * s, 1.9 * s, P.BARK)              # cap with a crosshatch
    for dx in ((-2, 0, 2) if s < 1.2 else (-2.4, -0.8, 0.8, 2.4)):     # crosshatched cap
        c.px(x + dx * s, y - 1.8 * s, P.BARK_D)
        if s >= 1.2:
            c.px(x + dx * s + 0.8 * s, y - 2.6 * s, P.BARK_D)
    c.px(x - 1 * s, y - 2.8 * s, P.BARK_L)
    c.rect(x - 0.4, y - 4.6 * s, x + 0.4, y - 3.6 * s, P.BARK_DD)      # stem


def rolling(draw_one, size: int, frames: int = 4, outline=P.OUTLINE) -> list[Image.Image]:
    """Frames of a round thing turning clockwise (it rolls right; mirrored, it rolls left)."""
    base = Canvas(size, size)
    draw_one(base)
    out = []
    centre = (size / 2 - 0.5, size / 2 - 0.5)
    for k in range(frames):
        c = Canvas(size, size)
        c.paste(base.img.rotate(-360 / frames * k, resample=Image.NEAREST, center=centre))
        out.append(c.outline(outline).img)
    return out


def squirrels() -> list[Sprite]:
    out = []
    size, cx, gy = (36, 36), 18, 34
    sq = Sprite("squirrel", size, faces_left=True, cx=cx, ground=gy)
    walk = []
    for i in range(6):
        p = i / 6 * math.tau
        c = Canvas(*size)
        squirrel(c, cx, gy, p, sway=math.sin(p) * 1.5, arm=70 + math.sin(p + math.pi) * 35, holding=False)
        walk.append(c.outline())
    sq.add("walk", walk, fps=10)
    dead = Canvas(*size)
    squirrel(dead, cx, gy, 0, eye="x", mouth="open", arm=110, run=False)
    dead.outline()
    sq.add("death", [vanish(dead.img, t / 3, depth=8) for t in range(4)], fps=10, loop=False)
    out.append(sq)

    # Sits on a branch: the frame's ground line is the top of the branch, which is drawn below it.
    size, cx, gy = (40, 40), 20, 32

    def branch(c: Canvas) -> None:
        with shaded(c, NUT, up=2) as p:
            p.poly([(0, 32), (39, 33), (39, 37), (0, 38)], P.BARK)
            p.line((28, 35), (34, 39), P.BARK, 2)
        c.line((5, 36), (33, 36), P.BARK_D)
        c.line((8, 34), (14, 34), P.BARK_L)
        for lx, ly in ((2, 30), (6, 31), (1, 35), (35, 31), (38, 29), (33, 28)):
            W.clump(c, lx, ly, 2.8)

    bs = Sprite("branch_squirrel", size, faces_left=True, cx=cx, ground=gy)

    def perched(arm: float, holding: bool, sway: float, eye: str = "open", lift: float = 0, mouth: str = "w",
                spark: bool = False) -> Image.Image:
        c = Canvas(*size)
        branch(c)
        hand = squirrel(c, cx, gy, 0, sway=sway, arm=arm, holding=holding, eye=eye, lift=lift, run=False,
                        mouth=mouth)["hand"]
        if spark:
            sparkle(c, hand[0] + 3, hand[1] - 2, P.YELLOW, big=True)
        return c.outline().img

    bs.add("idle", [perched(30, True, 0), perched(30, True, 1.5, eye="shut")], fps=3)
    bs.add("throw", [perched(-40, True, 0, eye="angry", mouth="flat"), perched(-130, True, -1, eye="angry"),
                     perched(140, False, 1, lift=1, mouth="open", spark=True), perched(90, False, 0.5)],
           fps=10, loop=False)
    branch_only = Canvas(*size)
    branch(branch_only)
    branch_only.outline()
    falling = []
    for t in range(4):
        body = Canvas(*size)
        squirrel(body, cx, gy, 0, eye="x", mouth="open", arm=110, run=False)
        body.outline()
        frame = branch_only.img.copy()
        frame.alpha_composite(vanish(body.img, t / 3, depth=-2))  # hops up and fades
        falling.append(frame)
    bs.add("death", falling, fps=10, loop=False)
    out.append(bs)

    def nut(c):
        acorn_shape(c, 6.5, 7, 1.3)

    acorn = Sprite("acorn", (14, 14), faces_left=True)
    acorn.add("roll", rolling(nut, 14), fps=14)
    acorn.add("death", [shatter(acorn.anims["roll"].frames[0], t / 3, 41, block=3, spread=0.6) for t in range(4)],
              fps=12, loop=False)
    out.append(acorn)

    def small_nut(c):
        acorn_shape(c, 6.5, 7, 1.25)

    thrown = Sprite("acorn_thrown", (14, 14), faces_left=True)
    thrown.add("fly", rolling(small_nut, 14), fps=16)
    out.append(thrown)
    return out


# --- spiky hedgehog cat ----------------------------------------------------------------------------

SPIKES = ramp((P.GOLD, P.RUST, P.RUST_D), (P.RUST_L, P.RUST_D, P.BARK_DD))
CAT = ramp((P.GINGER_L, P.PLANK_L, P.PLANK), (P.FUR_WHITE, P.CREAM, P.CREAM_D))


def quill(c: Canvas, base: tuple[float, float], a: float, length: float, colour) -> None:
    """One sharp quill: a narrow spine from `base` pointing along angle `a` (radians), with a pale tip."""
    ux, uy = math.cos(a), -math.sin(a)
    nx, ny = -uy, ux
    bx, by = base
    tip = (bx + ux * length, by + uy * length)
    c.poly([(bx + nx * 1.3, by + ny * 1.3), tip, (bx - nx * 1.3, by - ny * 1.3)], colour)
    c.px(tip[0] - ux * 1.2, tip[1] - uy * 1.2, P.RUST_L)


def spike_coat(c: Canvas, x: float, y: float, rx: float, ry: float, a0: float, a1: float, seed: int,
               wobble: int = 0, length: float = 6.5) -> None:
    """A coat of sharp quills: an ellipse with two rows of narrow spines between angles a0 and a1 (degrees,
    0 = right, counter-clockwise) swept back toward the tail, each outlined so they read apart."""
    rnd = noise(seed)
    with shaded(c, SPIKES, up=2, down=2, right=2) as p:
        p.ellipse(x, y, rx, ry, P.RUST)
    for half, colour in ((0, P.RUST_D), (1, P.RUST)):                          # two interleaved fans of quills
        with shaded(c, SPIKES, P.OUTLINE, up=1, down=1) as p:
            n = int((a1 - a0) / 24)
            for k in range(n + 1):
                deg = a0 + (a1 - a0) * k / n + half * 12 + ((k + wobble) % 2) * 2
                if deg > a1 + 6:
                    continue
                a = math.radians(deg)
                bx, by = x + math.cos(a) * rx * 0.7, y - math.sin(a) * ry * 0.7
                quill(p, (bx, by), a + math.radians(20), length + rnd() * 1.5 - half * 0.8, colour)
    for k in range(int((a1 - a0) / 30)):                                        # light catching the coat
        a = math.radians(a0 + 15 + k * 30)
        c.px(x + math.cos(a) * rx * 0.35, y - math.sin(a) * ry * 0.35, P.RUST_L)


def hedgehog_body(c: Canvas, x: float, gy: float, step: int, eye: str = "open", mouth: str = "w",
                  tuck: float = 0.0) -> None:
    """The Spiky Hedgehog Cat: a dome of sharp rusty quills with a round cat face at the front; `tuck`
    (0...1) pulls the face into the quills as it curls up."""
    with shaded(c, CAT, P.OUTLINE) as p:                                    # little feet
        for fx, up in ((x - 6, step % 2), (x + 3, (step + 1) % 2)):
            p.rect(fx, gy - up - 1.5, fx + 3, gy - up, P.PLANK)
    spike_coat(c, x - 1.5, gy - 8, 9.5, 7, 70, 230, 7, step)
    hx, hy = x + 7 - tuck * 4, gy - 7 + tuck
    k = 1 - tuck * 0.3
    with shaded(c, CAT, P.OUTLINE, up=2) as p:
        ear(p, hx - 3.5, hy - 4, 5 * (1 - tuck * 0.6), P.PLANK_L, inner=P.PINK_D, lean=-0.8, half=2.6)
        ear(p, hx + 3, hy - 4.2, 5 * (1 - tuck * 0.6), P.PLANK_L, inner=P.PINK_D, lean=0.8, half=2.6)
        p.ellipse(hx, hy, 6.5 * k, 5.5 * k, P.PLANK_L)
    c.ellipse(hx + 1, hy + 3, 3.2, 1.5, P.CREAM)
    if tuck < 0.7:
        face(c, hx + 1.5, hy - 2.5, eyes=eye, mouth=mouth, gap=5, nose=P.BARK_DD, size=3)


def hedgehog_ball(c: Canvas, x: float, y: float, rad: float, seed: int = 9) -> None:
    spike_coat(c, x, y, rad, rad, 0, 360, seed, length=5)
    c.ellipse(x + rad * 0.3, y + rad * 0.3, rad * 0.5, rad * 0.42, P.PLANK_L)   # tucked face
    c.px(x + rad * 0.5, y + rad * 0.15, P.BARK_DD)
    c.px(x + rad * 0.1, y + rad * 0.15, P.BARK_DD)
    c.px(x + rad * 0.3, y + rad * 0.5, P.PINK_D)


def hedgehog() -> Sprite:
    size, cx, gy = (36, 28), 18, 26
    sprite = Sprite("hedgehog", size, faces_left=True, cx=cx, ground=gy)
    walk = []
    for i in range(4):
        c = Canvas(*size)
        hedgehog_body(c, cx, gy - (i % 2) * 0.5, i)
        walk.append(c.outline().img)
    sprite.add("walk", walk, fps=8)

    def ball(rad: float, y: float) -> Image.Image:
        c = Canvas(*size)
        hedgehog_ball(c, cx, y, rad)
        return c.outline().img

    half = Canvas(*size)
    hedgehog_body(half, cx - 1, gy, 0, eye="shut", mouth="flat", tuck=0.5)
    sprite.add("curl", [half.outline().img, ball(7.5, gy - 11), ball(7, gy - 11)], fps=12, loop=False)

    def rolled_ball(c):
        hedgehog_ball(c, 17.5, 17.5, 7)

    frames = rolling(rolled_ball, 36)
    # Re-seat the rolling ball on the ground line of this frame size.
    rolled = []
    for f in frames:
        frame = Image.new("RGBA", size, P.CLEAR)
        box = f.getbbox()
        frame.alpha_composite(f.crop(box), (cx - (box[2] - box[0]) // 2, gy + 2 - (box[3] - box[1])))
        rolled.append(frame)
    sprite.add("rolled", rolled, fps=14)
    dead = Canvas(*size)
    hedgehog_body(dead, cx, gy, 0, eye="x", mouth="open")
    dead.outline()
    sprite.add("death", [vanish(dead.img, t / 3, depth=5) for t in range(4)], fps=10, loop=False)
    return sprite


# --- obstacles and ground pieces -----------------------------------------------------------------

def rose_bush() -> Sprite:
    """Thorny rose bush: low and wide (about 28x14), leafy clumps like the scenery, red roses, pale thorns."""
    c = Canvas(30, 16)
    dark = (P.KIT_GREEN_DD, P.KIT_GREEN_D, P.KIT_GREEN_D, P.KIT_GREEN, P.KIT_GREEN)
    for x, y, rad in sorted(((14, 6.5, 5.5), (8, 8, 5), (20, 7.5, 5), (4, 11, 3.8), (25, 11, 4), (11, 11, 4.5),
                             (18, 11, 4.5)), key=lambda b: b[1]):
        W.clump(c, x, y, rad)
    c.rect(2, 13, 27, 15, P.KIT_GREEN_DD)
    for x, y in ((3, 14), (8, 14), (14, 14), (20, 14), (26, 14)):
        W.clump(c, x, y, 2.4, dark)
    for x, y in ((3, 8), (9, 3), (15, 1), (21, 3), (26, 7), (1, 12), (28, 11)):
        c.px(x, y, P.CREAM)                                   # thorns sticking out
    for x, y in ((8, 6), (15, 4), (21, 7), (11, 11), (18, 10), (25, 11), (4, 10)):
        c.ellipse(x, y, 1.6, 1.4, P.RED)                     # roses
        c.px(x + 1, y + 1, P.RED_D)
        c.px(x - 0.5, y - 0.5, P.PINK)
    return single("bush", c.outline(), ground=15)


def stump() -> Sprite:
    """Mossy tree stump with flared roots (about 20x22), in the scenery's bark colours."""
    c = Canvas(22, 26)
    c.poly([(1, 25), (4, 20), (5, 7), (16, 7), (17, 20), (21, 25)], P.BARK)
    c.poly([(11, 7), (16, 7), (17, 20), (21, 25), (12, 25)], P.BARK_D)
    c.rect(5, 8, 6, 22, P.BARK_L)
    for x, top in ((8, 10), (11, 9), (14, 11)):              # bark grooves
        c.line((x, top), (x - 1 + (x % 2), 22), P.BARK_DD)
    c.line((4, 21), (1, 25), P.BARK_L)                       # root ridges
    c.line((17, 21), (20, 25), P.BARK_DD)
    c.line((9, 22), (8, 25), P.BARK_D)
    c.ellipse(10.5, 7, 6, 2.5, P.PLANK_L)                    # cut top with rings
    c.ellipse(10.5, 7, 4, 1.5, P.PLANK)
    c.ellipse(10.5, 7, 1.5, 0.6, P.PLANK_L)
    c.px(14, 6, P.PLANK_D)
    for x, y, rad in ((5, 8, 2), (8, 9, 1.5), (16, 8, 1.8)):  # moss drooping over the rim
        c.ellipse(x, y, rad, rad * 0.8, P.KIT_GREEN)
        c.px(x - 0.5, y - 0.5, P.LEAF_Y)
    c.line((5, 9), (5, 13), P.KIT_GREEN_D)
    c.ellipse(13, 15, 1.5, 2, P.KIT_GREEN_D)
    c.px(12.5, 14, P.KIT_GREEN)
    for x in (2, 5, 15, 19):                                 # grass at the foot
        c.line((x, 25), (x - 1, 22), P.KIT_GREEN)
        c.px(x, 23, P.KIT_GREEN_L)
    c.rect(18, 22, 18, 24, P.CREAM)                          # a toadstool
    c.ellipse(18, 21.5, 2, 1.2, P.RED)
    c.px(17.5, 21, P.WHITE)
    return single("stump", c.outline(), ground=25)


def slick(name: str, base, light, sheen, seed: int) -> Sprite:
    """A flat 32-wide puddle tile that repeats seamlessly; its bottom rows sink into the turf."""
    c = Canvas(32, 6)
    for x in range(32):
        top = 2 + round(math.sin(x / 32 * math.tau * 2) * 0.6 + math.sin(x / 32 * math.tau * 3 + 1) * 0.4)
        c.rect(x, top, x, 5, base)
        c.px(x, top, light)
    rnd = noise(seed)
    for _ in range(4):
        x, y = int(rnd() * 28), 3 + int(rnd() * 2)
        c.rect(x, y, x + 2 + int(rnd() * 3), y, sheen)
    return single(name, c, ground=3)


def milk() -> Sprite:
    """Spilled milk over the turf: a creamy puddle with a soft grey rim so it reads on bright grass, a
    bluish underside and a few drops; tiles seamlessly every 32 px, bottom 3 rows over the turf."""
    c = Canvas(32, 6)
    for x in range(32):
        top = 2 + round(math.sin(x / 32 * math.tau * 2) * 0.6 + math.sin(x / 32 * math.tau * 3 + 1) * 0.4)
        c.rect(x, top, x, 5, P.WHITE)
        c.px(x, top - 1, P.GREY_L)
        c.px(x, 5, P.CLOUD_S)
    for x in (6, 7, 19, 20, 21, 27):                         # glossy streaks
        c.px(x, 3, P.ICE_L)
    for x in (12, 13, 25):
        c.px(x, 4, P.CREAM)
    return single("milk", c, ground=3)


def platform(name: str, still: Canvas, anim: str, seed: int) -> Sprite:
    """A one-way platform: `still`, then `anim` frames as it cracks and drops away."""
    sprite = Sprite(name, still.size)
    sprite.add("still", [still.img], fps=1)
    cracked = still.img.copy()
    px = cracked.load()
    rnd = noise(seed)
    for k in range(3):
        x = int(6 + k * still.size[0] / 3 + rnd() * 4)
        for y in range(still.size[1]):
            if px[x, y][3]:
                px[x, y] = P.OUTLINE
    shaken = Image.new("RGBA", still.size, P.CLEAR)
    shaken.alpha_composite(cracked, (0, 1))
    frames = [cracked, shaken] + [shatter(cracked, t, seed, block=4, spread=0.15, gravity=1.5) for t in (0.4, 0.75)]
    sprite.add(anim, frames, fps=10, loop=False)
    return sprite


def bridge() -> Sprite:
    """A rope bridge segment: planks lashed with rope (walk surface = the top row), a post at the left,
    and rope swags hanging under the deck. Segments repeat, so the posts fall every 48 px."""
    w, h = 48, 12
    c = Canvas(w, h)
    for i, x in enumerate(range(4, w, 6)):
        c.rect(x, 1, x + 4, 5, P.PLANK_L if i % 2 else P.PLANK)
        c.rect(x, 1, x + 4, 1, P.PLANK_L)
        c.rect(x, 5, x + 4, 5, P.PLANK_D)
        c.px(x + 4, 2 + i % 3, P.PLANK_D)                   # grain
        c.px(x + 1, 3, P.PLANK_D if i % 2 else P.PLANK_L)
        c.rect(x + 5, 1, x + 5, 5, P.BARK_DD)                # gap between planks
    c.rect(0, 1, 3, 11, P.BARK)                              # post
    c.rect(0, 1, 0, 11, P.BARK_L)
    c.rect(3, 1, 3, 11, P.BARK_D)
    c.rect(0, 1, 3, 1, P.PLANK_L)
    c.rect(0, 3, 3, 3, P.SAND)                               # rope wrapped round the post
    c.rect(0, 5, 3, 5, P.SAND)
    c.line((4, 6), (47, 6), P.SAND)                          # rope binding under the planks
    for k, x in enumerate(range(9, w, 12)):                  # knots and hanging swags
        c.px(x, 6, P.CREAM)
        c.px(x, 7, P.SAND)
    for x0 in range(4, w - 4, 12):
        for k in range(13):
            x = x0 + k
            c.px(x, 7 + round(math.sin(k / 12 * math.pi) * 3), P.GOLD_D)
    c.px(2, 6, P.KIT_GREEN)                                  # a bit of moss on the post
    c.px(1, 8, P.KIT_GREEN_D)
    return platform("bridge", c.outline(), "crumble", 61)


def build() -> list[Sprite]:
    from characters.hedgehog_painted import NAMES as painted     # cut from the user's painted sheet instead
    from characters.squirrel_painted import NAMES as squirrel_painted
    from characters.branch_squirrel_painted import NAMES as branch_painted
    painted = painted | squirrel_painted | branch_painted
    sprites = [*squirrels(), hedgehog(), rose_bush(), stump(), milk(), bridge()]
    return [s for s in sprites if s.name not in painted]
