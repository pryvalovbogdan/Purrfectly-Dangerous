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
    for i, (x, y) in enumerate(pts[2:-2], 2):                           # the paler curl inside the tail
        c.px(x + 1.2 * size, y + 0.5, P.RUST_L)
    c.px(pts[-1][0] - 0.5, pts[-1][1] + 1, P.CREAM_D)
    c.px(pts[3][0] - 2.5 * size, pts[3][1] - 1, P.RUST_D)
    c.px(pts[4][0] - 2.5 * size, pts[4][1] + 1, P.RUST_D)


def squirrel(c: Canvas, x: float, ground: float, phase: float = 0.0, *, sway: float = 0, arm: float = 40,
             eye: str = "open", mouth: str = "w", holding: bool = False, lift: float = 0, run: bool = True) -> dict:
    """The Squirrel Thief: an orange squirrel with a cat's face, cream muzzle and belly, a teal scarf
    and a tail as big as itself; about 18px tall (22 with its tail), feet on `ground` at `x`."""
    bob = (abs(math.sin(phase)) * 1.2 if run else 0) + lift
    gy = ground - bob
    bushy_tail(c, (x - 3.5, gy - 3), sway, 0.76)
    swing = math.sin(phase) * (45 if run else 0)

    def leg(on: Canvas, angle: float, colour) -> None:
        knee = on.limb((x - 1, gy - 4), angle, 2.5, colour, 2)
        foot = on.limb(knee, angle - 30, 2, colour, 2)
        on.rect(foot[0] - 0.5, foot[1] - 0.5, foot[0] + 1.5, foot[1] + 0.5, colour)

    leg(c, -swing - 5, P.RUST_D)
    with shaded(c, FUR) as p:
        p.ellipse(x, gy - 7, 4.2, 4.8, P.RUST)                           # body
        p.ellipse(x - 1.5, gy - 4, 3, 2.6, P.RUST)                       # haunch
    c.ellipse(x + 1.8, gy - 6.5, 1.6, 3, P.CREAM)                       # belly
    with shaded(c, FUR) as p:
        leg(p, swing + 5, P.RUST)
    hx, hy = x + 2.5, gy - 13
    with shaded(c, FUR, P.OUTLINE) as p:
        ear(p, hx - 3, hy - 3, 3.5, P.RUST, inner=P.PINK_D, lean=-0.8, half=1.8)
        ear(p, hx + 2, hy - 3.5, 3.5, P.RUST, inner=P.PINK_D, lean=0.3, half=1.8)
        p.ellipse(hx, hy, 4.6, 4, P.RUST)
        p.ellipse(hx + 3, hy + 1.5, 2.5, 1.8, P.RUST)                   # snout
    c.px(hx - 3.5, hy - 7, P.RUST_L)                                     # ear tufts
    c.ellipse(hx + 2.5, hy + 2, 2.4, 1.3, P.CREAM)                      # cream muzzle
    c.px(hx - 3, hy + 1, P.CREAM)
    face(c, hx + 2, hy - 1.5, eyes=eye, mouth=mouth, gap=4, nose=P.BARK_DD)
    c.rect(hx - 3, hy + 3.5, hx + 2, hy + 4, P.TEAL)                    # teal scarf, its end streaming back
    c.line((hx - 3, hy + 4), (hx - 5 - abs(math.sin(phase)) * 1.5, hy + 5.5), P.TEAL)
    c.px(hx + 1, hy + 4, P.DIST_D)
    sx, sy = x + 2, gy - 8
    rad = math.radians(arm)
    hand = (sx + math.sin(rad) * 3.5, sy + math.cos(rad) * 3.5)
    c.line((sx, sy), hand, P.RUST_D, 2)
    if holding:
        acorn_shape(c, hand[0] + 1, hand[1] - 1.5, 0.7)
    return {"hand": hand, "head": (hx, hy)}


def acorn_shape(c: Canvas, x: float, y: float, s: float = 1.0) -> None:
    """A glossy acorn standing upright, centred at (x, y), about 8*s px tall."""
    with shaded(c, NUT) as p:
        p.ellipse(x, y + 1 * s, 3.1 * s, 3.5 * s, P.PLANK)               # nut
        p.px(x, y + 4.6 * s, P.PLANK)
    c.px(x - 1.2 * s, y + 0.2 * s, P.PLANK_L)
    if s >= 0.9:
        c.px(x - 1.5 * s, y + 1.2 * s, P.WHITE)
    with shaded(c, NUT) as p:
        p.ellipse(x, y - 1.8 * s, 3.8 * s, 1.9 * s, P.BARK)              # cap with a crosshatch
    for dx in (-2, 0, 2):
        c.px(x + dx * s, y - 1.8 * s, P.BARK_D)
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
    sq = Sprite("squirrel", (26, 26), faces_left=True, cx=13, ground=24)
    walk = []
    for i in range(6):
        p = i / 6 * math.tau
        c = Canvas(26, 26)
        squirrel(c, 13, 24, p, sway=math.sin(p) * 1.5, arm=60 + math.sin(p) * 25, holding=False)
        walk.append(c.outline())
    sq.add("walk", walk, fps=10)
    dead = Canvas(26, 26)
    squirrel(dead, 13, 24, 0, eye="x", mouth="open", arm=150, run=False)
    dead.outline()
    sq.add("death", [vanish(dead.img, t / 3, depth=6) for t in range(4)], fps=10, loop=False)
    out.append(sq)

    # Sits on a branch: the frame's ground line is the top of the branch, which is drawn below it.
    size, cx, gy = (32, 32), 16, 26

    def branch(c: Canvas) -> None:
        with shaded(c, NUT) as p:
            p.poly([(0, 26), (31, 27), (31, 30), (0, 31)], P.BARK)
            p.line((22, 28), (27, 31), P.BARK, 2)
        c.line((4, 29), (26, 29), P.BARK_D)
        for lx, ly in ((2, 24), (5, 25), (1, 28), (28, 25), (30, 23)):
            W.clump(c, lx, ly, 2.2)

    bs = Sprite("branch_squirrel", size, faces_left=True, cx=cx, ground=gy)

    def perched(arm: float, holding: bool, sway: float, eye: str = "open", lift: float = 0, mouth: str = "w",
                spark: bool = False) -> Image.Image:
        c = Canvas(*size)
        branch(c)
        hand = squirrel(c, cx, gy, 0, sway=sway, arm=arm, holding=holding, eye=eye, lift=lift, run=False,
                        mouth=mouth)["hand"]
        if spark:
            sparkle(c, hand[0] + 3, hand[1] - 2, P.YELLOW)
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
        squirrel(body, cx, gy, 0, eye="x", mouth="open", arm=160, run=False)
        body.outline()
        frame = branch_only.img.copy()
        frame.alpha_composite(vanish(body.img, t / 3, depth=-4))  # hops up and fades
        falling.append(frame)
    bs.add("death", falling, fps=10, loop=False)
    out.append(bs)

    def nut(c):
        acorn_shape(c, 5.5, 6, 1.0)

    acorn = Sprite("acorn", (12, 12), faces_left=True)
    acorn.add("roll", rolling(nut, 12), fps=14)
    acorn.add("death", [shatter(acorn.anims["roll"].frames[0], t / 3, 41, block=3, spread=0.6) for t in range(4)],
              fps=12, loop=False)
    out.append(acorn)

    def small_nut(c):
        acorn_shape(c, 4.5, 5, 0.8)

    thrown = Sprite("acorn_thrown", (10, 10), faces_left=True)
    thrown.add("fly", rolling(small_nut, 10), fps=16)
    out.append(thrown)
    return out


# --- spiky hedgehog cat ----------------------------------------------------------------------------

SPIKES = ramp((P.GOLD, P.RUST, P.RUST_D), (P.RUST_L, P.RUST_D, P.BARK_DD))
CAT = ramp((P.GINGER_L, P.PLANK_L, P.PLANK), (P.FUR_WHITE, P.CREAM, P.CREAM_D))


def spike_coat(c: Canvas, x: float, y: float, rx: float, ry: float, a0: float, a1: float, seed: int,
               wobble: int = 0) -> None:
    """A spiny coat: an ellipse with triangular spines fanning out between angles a0 and a1 (degrees,
    0 = right, counter-clockwise), shaded light at the top-left."""
    rnd = noise(seed)
    with shaded(c, SPIKES, up=2, down=2, right=2) as p:
        p.ellipse(x, y, rx, ry, P.RUST)
        n = int((a1 - a0) / 17)
        for k in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * k / n + ((k + wobble) % 2) * 4)
            ux, uy = math.cos(a), -math.sin(a)
            nx, ny = -uy, ux
            bx, by = x + ux * (rx - 1), y + uy * (ry - 1)
            length = 3 + rnd() * 1.2
            tip = (bx + ux * length - nx * 1.2, by + uy * length - ny * 1.2)   # swept back slightly
            p.poly([(bx + nx * 1.6, by + ny * 1.6), tip, (bx - nx * 1.6, by - ny * 1.6)], P.RUST)
    for k in range(int((a1 - a0) / 25)):                                     # inner spine strokes
        a = math.radians(a0 + 10 + k * 25)
        c.line((x + math.cos(a) * rx * 0.3, y - math.sin(a) * ry * 0.3),
               (x + math.cos(a) * rx * 0.75, y - math.sin(a) * ry * 0.75), P.RUST_D)
        c.px(x + math.cos(a - 0.2) * rx * 0.6, y - math.sin(a - 0.2) * ry * 0.6, P.RUST_L)


def hedgehog_body(c: Canvas, x: float, gy: float, step: int, eye: str = "open", mouth: str = "w",
                  tuck: float = 0.0) -> None:
    """The Spiky Hedgehog Cat: a dome of rusty spines with a round cat face at the front; `tuck` (0...1)
    pulls the face into the spines as it curls up."""
    for fx, up in ((x - 4, step % 2), (x + 3, (step + 1) % 2)):           # little feet
        c.rect(fx, gy - up - 1, fx + 2, gy - up, P.PLANK_D)
    spike_coat(c, x - 0.5, gy - 6, 7.5, 5.5, 60, 235, 7, step)
    hx, hy = x + 5 - tuck * 3, gy - 5.5 + tuck
    with shaded(c, CAT, P.OUTLINE) as p:
        ear(p, hx - 2.5, hy - 3, 3.2 * (1 - tuck * 0.6), P.PLANK_L, inner=P.PINK_D, lean=-0.5, half=1.8)
        ear(p, hx + 2.5, hy - 3.2, 3.2 * (1 - tuck * 0.6), P.PLANK_L, inner=P.PINK_D, lean=0.5, half=1.8)
        p.ellipse(hx, hy, 4.8 * (1 - tuck * 0.3), 4 * (1 - tuck * 0.3), P.PLANK_L)
    c.ellipse(hx + 0.5, hy + 2, 2.4, 1.1, P.CREAM)
    if tuck < 0.7:
        face(c, hx + 1.5, hy - 1.5, eyes=eye, mouth=mouth, gap=4, nose=P.BARK_DD)


def hedgehog_ball(c: Canvas, x: float, y: float, rad: float, seed: int = 9) -> None:
    spike_coat(c, x, y, rad, rad, 0, 360, seed)
    c.ellipse(x + rad * 0.3, y + rad * 0.3, rad * 0.45, rad * 0.4, P.PLANK_L)   # tucked face
    c.px(x + rad * 0.45, y + rad * 0.15, P.BARK_DD)
    c.px(x + rad * 0.15, y + rad * 0.15, P.BARK_DD)
    c.px(x + rad * 0.3, y + rad * 0.55, P.PINK_D)


def hedgehog() -> Sprite:
    size, cx, gy = (28, 22), 14, 20
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
    sprite.add("curl", [half.outline().img, ball(5.5, gy - 8), ball(5, gy - 8)], fps=12, loop=False)

    def rolled_ball(c):
        hedgehog_ball(c, 13.5, 13.5, 5)

    frames = rolling(rolled_ball, 28)
    # Re-seat the rolling ball on the ground line of this frame size.
    rolled = []
    for f in frames:
        frame = Image.new("RGBA", size, P.CLEAR)
        box = f.getbbox()
        frame.alpha_composite(f.crop(box), (cx - (box[2] - box[0]) // 2, gy + 1 - (box[3] - box[1])))
        rolled.append(frame)
    sprite.add("rolled", rolled, fps=14)
    dead = Canvas(*size)
    hedgehog_body(dead, cx, gy, 0, eye="x", mouth="open")
    dead.outline()
    sprite.add("death", [vanish(dead.img, t / 3, depth=4) for t in range(4)], fps=10, loop=False)
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
    return [*squirrels(), hedgehog(), rose_bush(), stump(), milk(), bridge()]
