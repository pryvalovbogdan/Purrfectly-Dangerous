"""World 1, the forest: squirrels, acorns, hedgehogs, rose bushes, stumps, spilled milk and the
crumbling bridge. Creatures are drawn facing right and mirrored on export."""
from __future__ import annotations

import math

from PIL import Image

import palette as P
from draw import Canvas, noise, shatter, vanish
from sprite import Sprite, single


# --- squirrels -----------------------------------------------------------------------------------

def bushy_tail(c: Canvas, base: tuple[float, float], sway: float, size: float = 1.0) -> None:
    """A big S-shaped squirrel tail rising behind `base` (which is at the rump)."""
    bx, by = base
    path = [(0, 0), (-2, -3), (-3.5, -6.5), (-3.5, -10), (-2, -13), (0.5, -14.5), (2.5, -14)]
    pts = [(bx + x * size + sway * (i / len(path)) ** 1.5 * 2, by + y * size) for i, (x, y) in enumerate(path)]
    for i, (x, y) in enumerate(pts):
        rad = (2.4 + 1.3 * math.sin(i / (len(pts) - 1) * math.pi)) * size
        c.ellipse(x, y, rad, rad, P.RUST)
    for i, (x, y) in enumerate(pts[1:-1], 1):
        rad = (1.0 + 0.7 * math.sin(i / (len(pts) - 1) * math.pi)) * size
        c.ellipse(x + 0.8 * size, y + 0.3, rad, rad, P.RUST_L)
    tx, ty = pts[-1]
    c.px(tx + 1.5 * size, ty + 1, P.RUST_D)
    c.px(pts[2][0] - 2.5 * size, pts[2][1], P.RUST_D)
    c.px(pts[3][0] - 2.8 * size, pts[3][1] + 1, P.RUST_D)


def squirrel(c: Canvas, x: float, ground: float, phase: float = 0.0, *, helmet: bool = True, sway: float = 0,
             arm: float = 40, eye: str = "open", holding: bool = False, lift: float = 0, spear: bool = True) -> dict:
    """An upright squirrel about 18px tall (20 with its tail), feet on `ground` at `x`."""
    bob = abs(math.sin(phase)) * 1.2 + lift
    gy = ground - bob
    bushy_tail(c, (x - 4.5, gy - 3), sway, 0.78)
    far = -math.sin(phase) * 2
    near = math.sin(phase) * 2
    c.rect(x - 1 + far, gy - 1 - max(0, math.cos(phase)) * 1.2, x + 2 + far, gy, P.RUST_D)
    c.ellipse(x, gy - 6, 3.8, 4.6, P.RUST)                  # body
    c.ellipse(x + 1.6, gy - 5.5, 1.6, 3.2, P.CREAM)         # belly
    c.ellipse(x - 1.6, gy - 3, 2.6, 2.6, P.RUST)            # haunch
    c.px(x - 2.5, gy - 4, P.RUST_L)
    lift_near = max(0, -math.cos(phase)) * 1.2
    c.rect(x - 1 + near, gy - 1 - lift_near, x + 3 + near, gy - lift_near, P.RUST_D)
    hx, hy = x + 2, gy - 12.5
    c.poly([(hx - 2.8, hy - 2), (hx - 2.2, hy - 6), (hx - 0.3, hy - 2.5)], P.RUST)      # ear
    c.px(hx - 2, hy - 3.5, P.RUST_D)
    c.ellipse(hx, hy, 3.4, 3.1, P.RUST)
    c.ellipse(hx + 2.8, hy + 0.8, 1.9, 1.5, P.RUST)          # snout
    c.rect(hx + 1.5, hy + 2, hx + 3.5, hy + 2.5, P.CREAM)    # chin
    c.px(hx + 4.6, hy + 0.2, P.BLACK)
    c.px(hx - 1.5, hy + 0.5, P.RUST_L)                      # cheek
    if eye == "x":
        for dx, dy in ((0, -2), (1, -1), (0, -1), (1, -2)):
            c.px(hx + dx + 0.5, hy + dy + 0.5, P.BLACK)
    else:
        c.rect(hx + 0.5, hy - 1.5, hx + 1.5, hy + 0.5, P.BLACK)
        c.px(hx + 1.5, hy - 1.5, P.WHITE)
    if helmet:                                              # an acorn cap worn as a helmet
        c.ellipse(hx - 0.5, hy - 2.4, 3.4, 1.8, P.BROWN)
        c.rect(hx - 3.8, hy - 2, hx + 2.8, hy - 1.5, P.BROWN_D)
        for dx in (-2, 0, 1.5):
            c.px(hx + dx, hy - 3.3, P.BROWN_L)
        c.px(hx - 0.5, hy - 4.6, P.BROWN_D)
    sx, sy = x + 2, gy - 7.5
    rad = math.radians(arm)
    hand = (sx + math.sin(rad) * 3, sy + math.cos(rad) * 3)
    c.line((sx, sy), hand, P.RUST_D, 2)
    if spear:                                               # a twig spear, held point-forward
        c.line((hand[0] - 2, hand[1] + 3), (hand[0] + 4, hand[1] - 6), P.BROWN_D)
        c.px(hand[0] + 4.5, hand[1] - 7, P.GREY_L)
    if holding:
        acorn_shape(c, hand[0] + 1, hand[1] - 2.5, 0.75)
    return {"hand": hand, "head": (hx, hy)}


def acorn_shape(c: Canvas, x: float, y: float, s: float = 1.0) -> None:
    """An acorn standing upright, centred at (x, y), about 8*s px tall."""
    c.ellipse(x, y + 1 * s, 3.2 * s, 3.6 * s, P.GOLD_D)
    c.ellipse(x - 0.8 * s, y + 0.5 * s, 1.4 * s, 2.2 * s, P.SAND)
    c.px(x, y + 4.5 * s, P.BROWN)
    c.ellipse(x, y - 1.8 * s, 3.8 * s, 1.9 * s, P.BROWN_D)
    c.rect(x - 2.5 * s, y - 2.2 * s, x + 2.5 * s, y - 2.2 * s, P.BROWN)
    c.rect(x - 0.4, y - 4.6 * s, x + 0.4, y - 3.6 * s, P.BROWN_D)


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
        squirrel(c, 13, 24, p, sway=math.sin(p) * 1.5, arm=50 + math.sin(p) * 10)
        walk.append(c.outline())
    sq.add("walk", walk, fps=10)
    dead = Canvas(26, 26)
    squirrel(dead, 13, 24, 0, eye="x", arm=150, spear=False)
    dead.outline()
    sq.add("death", [vanish(dead.img, t / 3, depth=6) for t in range(4)],
           fps=10, loop=False)
    out.append(sq)

    # Sits on a branch: the frame's ground line is the top of the branch, which is drawn below it.
    size, cx, gy = (32, 32), 16, 26

    def branch(c: Canvas) -> None:
        c.poly([(0, 26), (31, 27), (31, 30), (0, 31)], P.BROWN)
        c.line((0, 27), (31, 28), P.BROWN_L)
        c.line((4, 30), (28, 29), P.BROWN_D)
        c.line((22, 28), (27, 31), P.BROWN)
        for lx, ly in ((2, 24), (5, 25), (1, 28), (28, 25), (30, 23)):
            c.ellipse(lx, ly, 2, 1.5, P.GREEN)
            c.px(lx - 0.5, ly - 0.5, P.LEAF_L)

    bs = Sprite("branch_squirrel", size, faces_left=True, cx=cx, ground=gy)

    def perched(arm: float, holding: bool, sway: float, eye: str = "open", lift: float = 0) -> Image.Image:
        c = Canvas(*size)
        branch(c)
        squirrel(c, cx, gy, 0, helmet=False, sway=sway, arm=arm, holding=holding, eye=eye, spear=False, lift=lift)
        return c.outline().img

    bs.add("idle", [perched(30, True, 0), perched(30, True, 1.5)], fps=3)
    bs.add("throw", [perched(-40, True, 0), perched(-110, True, -1), perched(140, False, 1, lift=1),
                     perched(90, False, 0.5)], fps=10, loop=False)
    branch_only = Canvas(*size)
    branch(branch_only)
    branch_only.outline()
    falling = []
    for t in range(4):
        body = Canvas(*size)
        squirrel(body, cx, gy, 0, helmet=False, eye="x", arm=160, spear=False)
        body.outline()
        frame = branch_only.img.copy()
        frame.alpha_composite(vanish(body.img, t / 3, depth=-8))  # hops up and fades
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


# --- hedgehog ------------------------------------------------------------------------------------

def hedgehog_body(c: Canvas, x: float, gy: float, step: int, eye: str = "open") -> None:
    rnd = noise(7)
    # Spiky coat: a dome with spines fanning back.
    for k in range(13):
        a = math.radians(200 + k * 11)
        bx, by = x - 1 + math.cos(a) * 6, gy - 5 + math.sin(a) * 5
        tip = (x - 1 + math.cos(a - 0.35) * 10, gy - 5 + math.sin(a - 0.35) * 8.5)
        c.line((bx, by), tip, P.BROWN_D if k % 2 else P.BROWN, 2)
        c.px(tip[0], tip[1], P.SAND)
    c.ellipse(x - 1, gy - 5, 7, 5, P.BROWN)
    for _ in range(9):
        c.px(x - 6 + rnd() * 9, gy - 9 + rnd() * 5, P.BROWN_D)
    # Face and feet.
    c.ellipse(x + 5, gy - 3.5, 3.2, 2.6, P.SAND)
    c.poly([(x + 6, gy - 5), (x + 10.5, gy - 3), (x + 6, gy - 1.5)], P.SAND)
    c.px(x + 10.5, gy - 3, P.BLACK)
    c.px(x + 7, gy - 1.5, P.PINK_D)
    if eye == "x":
        c.px(x + 6, gy - 5, P.BLACK)
        c.px(x + 5, gy - 4, P.BLACK)
    else:
        c.rect(x + 6, gy - 5, x + 6, gy - 4, P.BLACK)
    c.px(x + 3.5, gy - 3, P.PINK)
    for fx, up in ((x - 4, step % 2), (x + 3, (step + 1) % 2)):
        c.rect(fx, gy - up, fx + 1.5, gy - up, P.BROWN_D)


def hedgehog_ball(c: Canvas, x: float, y: float, rad: float) -> None:
    for k in range(16):
        a = k / 16 * math.tau
        tip = (x + math.cos(a) * (rad + 2.5), y + math.sin(a) * (rad + 2.5))
        c.line((x + math.cos(a) * rad * 0.6, y + math.sin(a) * rad * 0.6), tip, P.BROWN_D if k % 2 else P.BROWN, 2)
        c.px(tip[0], tip[1], P.SAND)
    c.ellipse(x, y, rad, rad, P.BROWN)
    c.ellipse(x + rad * 0.35, y + rad * 0.35, rad * 0.45, rad * 0.4, P.SAND)   # tucked face
    c.px(x + rad * 0.6, y + rad * 0.2, P.BLACK)


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
    hedgehog_body(half, cx - 1, gy, 0)
    sprite.add("curl", [half.outline().img, ball(5.5, gy - 7), ball(5, gy - 7.5)], fps=12, loop=False)

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
    hedgehog_body(dead, cx, gy, 0, eye="x")
    dead.outline()
    sprite.add("death", [vanish(dead.img, t / 3, depth=4) for t in range(4)],
               fps=10, loop=False)
    return sprite


# --- obstacles and ground pieces -----------------------------------------------------------------

def rose_bush() -> Sprite:
    """Thorny rose bush: low and wide (about 26x13)."""
    c = Canvas(30, 16)
    for x, y, rad in ((6, 10, 5), (13, 8, 6), (20, 9, 5.5), (25, 11, 4), (9, 12, 4), (17, 12, 4)):
        c.ellipse(x, y, rad, rad * 0.85, P.GREEN_D)
    for x, y, rad in ((5, 9, 2.5), (12, 6, 3), (19, 7, 2.5), (24, 10, 2)):
        c.ellipse(x, y, rad, rad * 0.8, P.GREEN)
        c.px(x - 1, y - 1, P.LEAF_L)
    c.rect(2, 14, 28, 15, P.MOSS)
    for x, y in ((3, 6), (10, 3), (17, 3), (23, 5), (27, 8), (1, 11), (15, 13), (28, 13)):
        c.px(x, y, P.SAND)                                  # thorns sticking out
    for x, y in ((8, 7), (16, 5), (22, 8), (12, 11), (26, 12)):
        c.ellipse(x, y, 1.5, 1.5, P.RED)                    # roses
        c.px(x - 0.5, y - 0.5, P.PINK)
    return single("bush", c.outline(), ground=15)


def stump() -> Sprite:
    """Tree stump: tall (about 16x22)."""
    c = Canvas(22, 26)
    c.poly([(2, 25), (4, 22), (4, 6), (17, 6), (17, 22), (20, 25)], P.BROWN)
    c.rect(4, 6, 6, 24, P.BROWN_D)
    for x in (9, 13, 16):
        c.line((x, 9), (x, 22), P.BROWN_D)
    c.line((11, 8), (11, 15), P.BROWN_L)
    c.ellipse(10.5, 6, 6.5, 2.5, P.SAND)                    # cut top with rings
    c.ellipse(10.5, 6, 4, 1.4, P.BROWN_L)
    c.ellipse(10.5, 6, 1.5, 0.6, P.SAND)
    c.ellipse(5, 23, 3, 1.5, P.MOSS)                        # moss and a toadstool at the foot
    c.ellipse(16, 12, 1.5, 2, P.MOSS)
    c.rect(18, 22, 18, 24, P.CREAM)
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
    w, h = 48, 12
    c = Canvas(w, h)
    for i, x in enumerate(range(0, w, 6)):
        dy = (i % 3 == 1) * 0.5
        c.rect(x, 2 + dy, x + 4, 6 + dy, P.BROWN_L if i % 2 else P.BROWN)
        c.px(x + 1, 3 + dy, P.SAND)
        c.px(x + 4, 6 + dy, P.BROWN_D)
    c.line((0, 1), (47, 1), P.SAND)                          # rope along the top
    c.line((0, 7), (47, 7), P.BROWN_D)
    for x in (3, 21, 39):                                    # broken plank ends hanging down
        c.rect(x, 8, x + 1, 10, P.BROWN_D)
    return platform("bridge", c.outline(), "crumble", 61)


def build() -> list[Sprite]:
    milk = slick("milk", P.WHITE, P.ICE_L, P.CREAM, 51)
    return [*squirrels(), hedgehog(), rose_bush(), stump(), milk, bridge()]
