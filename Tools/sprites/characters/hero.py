"""The kitten hero (40x28, an orange tabby on all fours) and its ball of yarn.

`cat()` draws a side-on cat from a `CatPose`; other modules reuse it (the ghost cats, the award icons).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

from PIL import Image

import palette as P
from draw import Canvas, end_of, see_through, tint
from sprite import Sprite

SIZE = (44, 28)
CX, GROUND = 23, 26


@dataclass(frozen=True)
class Coat:
    fur: tuple = P.GINGER
    fur_l: tuple = P.GINGER_L
    fur_d: tuple = P.GINGER_D
    stripe: tuple = P.GINGER_DD
    belly: tuple = P.CREAM
    belly_d: tuple = P.CREAM_D
    nose: tuple = P.PINK
    eye: tuple = P.BLACK
    shine: tuple = P.WHITE
    inner_ear: tuple = P.PINK


TABBY = Coat()


@dataclass(frozen=True)
class CatPose:
    """Angles in degrees: 0 = straight down, positive = forward (toward the nose).
    Each leg is (upper angle, lower angle), both absolute."""
    front_near: tuple = (8, 0)
    front_far: tuple = (-6, -6)
    back_near: tuple = (-6, 0)
    back_far: tuple = (8, 0)
    stretch: float = 0      # body longer (+) or bunched up (-)
    tilt: float = 0         # chest this many pixels higher than the rump (+ = nose up)
    lift: float = 0         # pixels above the ground
    tail: float = 50        # tail root angle above straight back (90 = straight up)
    curl: float = 9         # how much the tail bends forward per segment
    head_dx: float = 0
    head_dy: float = 0
    eye: str = "open"       # open | shut | x | wide
    mouth: bool = False
    ears_back: bool = False
    bib: bool = True


UPPER, LOWER = 3.5, 3.2


def _leg_end(start, leg) -> tuple[float, float]:
    knee = end_of(start, leg[0], UPPER)
    return end_of(knee, leg[1], LOWER)


def cat(c: Canvas, pose: CatPose, cx: float = CX, ground: float = GROUND, coat: Coat = TABBY) -> dict:
    """Draws a right-facing cat whose lowest paw rests on `ground` (minus `pose.lift`)."""
    half = 4.5 + pose.stretch / 2

    def anchors(by: float):
        chest = (cx + half, by - pose.tilt / 2)
        rump = (cx - half, by + pose.tilt / 2)
        shoulder = (chest[0] + 0.5, chest[1] + 2)
        hip = (rump[0] - 0.5, rump[1] + 2)
        return chest, rump, shoulder, hip

    _, _, shoulder0, hip0 = anchors(0.0)
    lowest = max(_leg_end(shoulder0, pose.front_near)[1], _leg_end(shoulder0, pose.front_far)[1],
                 _leg_end(hip0, pose.back_near)[1], _leg_end(hip0, pose.back_far)[1])
    by = ground - 0.5 - pose.lift - lowest
    chest, rump, shoulder, hip = anchors(by)

    def leg(start, spec, color, paw):
        knee = c.limb(start, spec[0], UPPER, color, 2)
        foot = c.limb(knee, spec[1], LOWER, color, 2)
        c.rect(foot[0] - 0.5, foot[1] - 0.5, foot[0] + 1.5, foot[1] + 0.5, paw)
        return foot

    # Far legs, darker, behind everything.
    leg((shoulder[0] - 1, shoulder[1]), pose.front_far, coat.fur_d, coat.belly_d)
    leg((hip[0] + 1, hip[1]), pose.back_far, coat.fur_d, coat.fur_d)

    # Tail: a chain of short segments that curls toward the tip, with a ringed tabby pattern.
    base = (rump[0] - 3, rump[1] - 1.5)
    angle = pose.tail
    point = base
    for i in range(10):
        rad = math.radians(angle)
        nxt = (point[0] - math.cos(rad) * 1.15, point[1] - math.sin(rad) * 1.15)
        color = coat.stripe if i in (4, 8, 9) else coat.fur
        c.rect(nxt[0] - 0.5, nxt[1] - 0.5, nxt[0] + 0.5, nxt[1] + 0.5, color)
        point = nxt
        angle += pose.curl
    tail_tip = point

    # Body: a capsule from rump to chest; the haunch is a touch bigger than the chest.
    steps = 10
    for i in range(steps + 1):
        t = i / steps
        x = rump[0] + (chest[0] - rump[0]) * t
        y = rump[1] + (chest[1] - rump[1]) * t
        c.ellipse(x, y, 3.2, 3.9 - t * 0.6, coat.fur)
    # Belly shadow, back highlight and tabby stripes across the back.
    for i in range(steps + 1):
        t = i / steps
        x = rump[0] + (chest[0] - rump[0]) * t
        y = rump[1] + (chest[1] - rump[1]) * t
        c.px(x, y + 3.2 - t * 0.6, coat.fur_d)
        if 0.15 < t < 0.85:
            c.px(x, y - 3.2 + t * 0.6, coat.fur_l)
    for t in (0.22, 0.45, 0.68):
        x = rump[0] + (chest[0] - rump[0]) * t
        y = rump[1] + (chest[1] - rump[1]) * t - 3.6 + t * 0.6
        c.rect(x, y + 1, x, y + 2.5, coat.stripe)
    if pose.bib:
        c.ellipse(chest[0] + 1.5, chest[1] + 1.5, 1.6, 2.0, coat.belly)

    leg(hip, pose.back_near, coat.fur, coat.belly)
    # Haunch over the top of the near hind leg.
    c.ellipse(rump[0] - 0.5, rump[1] + 0.5, 2.2, 2.4, coat.fur)
    c.px(rump[0] - 1, rump[1] + 0.5, coat.stripe)
    c.px(rump[0], rump[1] - 0.5, coat.stripe)
    leg(shoulder, pose.front_near, coat.fur, coat.belly)

    # Head, in front of the chest.
    hx, hy = chest[0] + 4.5 + pose.head_dx, chest[1] - 3.5 + pose.head_dy
    for ex, tip in ((hx - 3.0, -2.5), (hx + 1.0, -1.0)):
        if pose.ears_back:
            c.poly([(ex - 2, hy - 2), (ex - 3.5 + tip / 3, hy - 4.5), (ex + 1.5, hy - 3.5)], coat.fur)
        else:
            c.poly([(ex - 1.8, hy - 2), (ex - 0.5 + tip / 4, hy - 7), (ex + 1.8, hy - 2)], coat.fur)
            c.px(ex - 0.3 + tip / 6, hy - 4, coat.inner_ear)
    c.ellipse(hx, hy, 4.3, 3.6, coat.fur)
    c.ellipse(hx + 0.5, hy + 1.2, 4.6, 2.6, coat.fur)
    c.rect(hx - 1, hy - 3.5, hx - 1, hy - 2.5, coat.stripe)       # forehead stripes
    c.rect(hx + 1, hy - 3.5, hx + 1, hy - 3, coat.stripe)
    c.px(hx - 3.5, hy + 0.5, coat.stripe)                          # cheek stripe
    c.ellipse(hx + 3, hy + 1.8, 2.0, 1.4, coat.belly)              # muzzle
    c.px(hx + 4.5, hy + 0.5, coat.nose)
    if pose.mouth:
        c.rect(hx + 3, hy + 2.5, hx + 4, hy + 3, P.PINK_D)
    ex, ey = hx + 1.5, hy - 0.5
    if pose.eye == "open":
        c.rect(ex, ey - 1, ex + 1, ey + 1, coat.eye)
        c.px(ex + 1, ey - 1, coat.shine)
    elif pose.eye == "wide":
        c.rect(ex - 0.5, ey - 1.5, ex + 1, ey + 1, coat.eye)
        c.px(ex + 1, ey - 1.5, coat.shine)
        c.px(ex - 0.5, ey + 1, coat.shine)
    elif pose.eye == "shut":
        c.rect(ex - 0.5, ey + 0.5, ex + 1, ey + 0.5, coat.eye)
    elif pose.eye == "x":
        c.line((ex - 1, ey - 1), (ex + 1, ey + 1), coat.eye)
        c.line((ex - 1, ey + 1), (ex + 1, ey - 1), coat.eye)
    return {"head": (hx, hy), "chest": chest, "rump": rump, "tail_tip": tail_tip,
            "paw": _leg_end(shoulder, pose.front_near)}


def kitten(pose: CatPose, coat: Coat = TABBY, extras=()) -> Canvas:
    c = Canvas(*SIZE)
    joints = cat(c, pose, coat=coat)
    for extra in extras:
        extra(c, joints)
    return c.outline()


def gallop(phase: float, amount: float = 1.0) -> CatPose:
    """A rotary gallop: front and hind pairs swing against each other; extended in the air, gathered
    on the ground."""
    s = math.sin(phase)

    def front(p):
        sp = math.sin(p)
        upper = (48 if sp > 0 else 14) * sp * amount + 4
        fold = 75 * max(0.0, -math.sin(p + 0.8))
        return (upper, upper - fold)

    def back(p):
        sp = math.sin(p)
        upper = -(46 if sp > 0 else 12) * sp * amount
        hock = 55 * max(0.0, math.sin(p + math.pi - 0.6))
        return (upper, upper - hock)

    return CatPose(front_near=front(phase), front_far=front(phase - 0.7), back_near=back(phase),
                   back_far=back(phase - 0.7), stretch=2.2 * s * amount, lift=1.2 * max(0.0, s) * amount,
                   tilt=-0.8 * math.cos(phase), tail=38 + 14 * math.sin(phase + 1), head_dy=0.6 * math.cos(phase))


def ghostly(image: Image.Image, alpha: int) -> Image.Image:
    """Pale blue-white tint with partial alpha, for Ghost Dash."""
    out = tint(image, P.CYAN, 0.62)
    return see_through(out, alpha)


def build() -> list[Sprite]:
    hero = Sprite("hero", SIZE, cx=CX, ground=GROUND)

    run_poses = [gallop(i / 8 * math.tau) for i in range(8)]
    hero.add("run", [kitten(p) for p in run_poses], fps=14)

    def dust(n):
        def draw(c, joints):
            for i in range(n):
                x, y = CX + 10 + i * 3, GROUND - (i % 2) * 2
                c.rect(x, y - 1, x + 1, y, P.GREY_L)
        return draw

    # Skids to a halt: forepaws braced ahead, rump down.
    stop = []
    for i, step in enumerate((1, 2, 2, 1)):
        stop.append(kitten(CatPose(front_near=(45, 40), front_far=(38, 32), back_near=(20, -30), back_far=(28, -25),
                                   tilt=1.5, stretch=-0.5, tail=60, ears_back=i < 2), extras=[dust(step)]))
    hero.add("stop", stop, fps=10, loop=False)

    # Sits up, tail swishing, blinks.
    sit = dict(front_near=(6, 4), front_far=(0, -2), back_near=(80, -40), back_far=(75, -45), stretch=-2.5, tilt=5,
               curl=-17)
    hero.add("idle", [
        kitten(CatPose(**sit, tail=t, eye=e, head_dy=dy))
        for t, e, dy in ((-4, "open", 0), (2, "open", 0), (6, "open", 0.5), (2, "shut", 0.5))
    ], fps=4)

    # Take-off: hind legs still pushing, front paws tucked; then sailing.
    hero.add("jump", [
        kitten(CatPose(front_near=(70, 150), front_far=(60, 140), back_near=(-50, -60), back_far=(-40, -55),
                       stretch=1.5, tilt=3, tail=20, curl=4)),
        kitten(CatPose(front_near=(60, 130), front_far=(50, 120), back_near=(-35, -55), back_far=(-25, -50),
                       stretch=1, tilt=2, tail=28, curl=5)),
    ], fps=8)
    # Coming down: paws reaching for the ground, tail up for balance.
    hero.add("fall", [
        kitten(CatPose(front_near=(30, 15), front_far=(22, 8), back_near=(20, 0), back_far=(10, -5), tilt=-1.5,
                       tail=65, curl=10, eye="wide")),
        kitten(CatPose(front_near=(26, 12), front_far=(18, 6), back_near=(16, -2), back_far=(8, -8), tilt=-1.5,
                       tail=70, curl=12, eye="wide")),
    ], fps=8)

    # Double Pounce: curls into a ball and flips once in the air.
    ball = Canvas(*SIZE)
    bx, by = CX + 1, GROUND - 9
    ball.ellipse(bx, by, 7, 6.5, P.GINGER)
    ball.ellipse(bx - 1, by + 1, 5, 4.5, P.GINGER_D)
    ball.ellipse(bx + 2, by + 2, 2.5, 2, P.CREAM)
    for dx, dy in ((-5, -3), (-2, -6), (2, -6)):
        ball.rect(bx + dx, by + dy, bx + dx + 1, by + dy + 1, P.GINGER_DD)
    for i in range(12):                                  # tail wrapped around the outside
        a = math.radians(200 + i * 14)
        ball.rect(bx + math.cos(a) * 7 - 0.5, by + math.sin(a) * 6.5 - 0.5, bx + math.cos(a) * 7 + 0.5,
                  by + math.sin(a) * 6.5 + 0.5, P.GINGER_DD if i in (4, 8, 10, 11) else P.GINGER)
    ball.poly([(bx + 3, by - 5), (bx + 5, by - 9), (bx + 6, by - 4)], P.GINGER)       # ear sticking out
    ball.px(bx + 5, by - 6, P.PINK)
    ball.rect(bx + 4, by - 2, bx + 5, by - 2, P.BLACK)   # shut eye
    ball.px(bx + 6.5, by, P.PINK)
    spin = []
    for k in range(4):
        rotated = ball.img.rotate(-90 * k, resample=Image.NEAREST, center=(bx, by))
        c = Canvas(*SIZE)
        c.paste(rotated)
        spin.append(c.outline())
    hero.add("double", spin, fps=16)

    # Yarn Shot: rears up and bats the yarn forward with a front paw.
    throw = [
        CatPose(front_near=(60, 110), front_far=(10, 0), back_near=(10, -20), back_far=(20, -15), tilt=3, stretch=-1,
                tail=45),
        CatPose(front_near=(150, 160), front_far=(30, 20), back_near=(15, -25), back_far=(25, -20), tilt=5,
                stretch=-1, tail=55, mouth=True),
        CatPose(front_near=(95, 95), front_far=(20, 10), back_near=(5, -15), back_far=(15, -10), tilt=2, stretch=0.5,
                tail=50, mouth=True),
        CatPose(front_near=(40, 30), front_far=(5, 0), back_near=(0, -10), back_far=(10, -5), tilt=0.5, tail=45),
    ]
    hero.add("throw", [kitten(p) for p in throw], fps=16, loop=False)

    # Ghost Dash: a see-through kitten trailing two fading after-images.
    dash = []
    for i in range(4):
        pose = replace(gallop(math.pi / 2 + i * 0.4, 1.1), eye="shut", ears_back=True)
        body = kitten(pose).img
        frame = Image.new("RGBA", SIZE, P.CLEAR)
        for offset, alpha in ((-6, 55), (-3, 95)):
            shifted = Image.new("RGBA", SIZE, P.CLEAR)
            shifted.alpha_composite(ghostly(body, alpha), (offset - (i % 2), 0))
            frame.alpha_composite(shifted)
        frame.alpha_composite(ghostly(body, 170))
        dash.append(frame)
    hero.add("dash", dash, fps=16)

    # Super Pounce: fully stretched, forepaws reaching, hind legs streaming behind.
    pounce = []
    for i, (s, t) in enumerate(((3.0, 2.5), (4.5, 1.0), (4.5, 0.0), (3.5, -1.5))):
        pose = CatPose(front_near=(110 - i * 8, 100 - i * 8), front_far=(100 - i * 8, 92 - i * 8),
                       back_near=(-105, -95), back_far=(-95, -88), stretch=s, tilt=t, lift=2, tail=10, curl=2,
                       ears_back=True, eye="wide", mouth=i in (1, 2))
        pounce.append(kitten(pose, extras=[streaks(i)]))
    hero.add("pounce", pounce, fps=12)

    hurt_pose = CatPose(front_near=(-10, -25), front_far=(-15, -30), back_near=(-20, -35), back_far=(-10, -30),
                        tilt=1, stretch=-1, lift=2, tail=85, curl=0, eye="x", mouth=True, ears_back=True)
    hurt = kitten(hurt_pose).img
    hero.add("hurt", [tint(hurt, P.WHITE, 0.8), hurt], fps=10)
    hero.add("death", death_frames(hurt_pose), fps=8, loop=False)

    return [hero, yarn()]


def streaks(i: int):
    def draw(c, joints):
        x, y = joints["rump"]
        for k, dy in enumerate((-3, 0, 3)):
            length = 3 + (i + k) % 3
            c.line((x - 8 - length, y + dy), (x - 7, y + dy), P.WHITE if k != 1 else P.CREAM)
    return draw


def death_frames(hurt_pose: CatPose) -> list[Image.Image]:
    """Knocked over onto its back, paws up and dizzy, then fades away."""
    flat = Canvas(*SIZE)
    cat(flat, CatPose(front_near=(95, 95), front_far=(80, 85), back_near=(-95, -95), back_far=(-80, -85), stretch=1,
                      tail=-2, curl=1, eye="x", mouth=True, ears_back=True))
    lying = flat.outline().img

    def stars(image, t):
        c = Canvas(*SIZE)
        c.paste(image)
        hx = CX + 10
        for k in range(3):
            a = t + k * math.tau / 3
            x, y = hx + math.cos(a) * 5, GROUND - 14 + math.sin(a) * 1.5
            c.px(x, y, P.YELLOW)
            c.px(x, y - 1, P.GOLD)
        return c.img

    hurt = kitten(hurt_pose).img
    tumble = Image.new("RGBA", SIZE, P.CLEAR)
    tumble.alpha_composite(hurt.rotate(-60, resample=Image.NEAREST, center=(CX, GROUND - 8)), (0, 0))
    return [hurt, tumble, stars(lying, 0), stars(lying, 1.2), see_through(stars(lying, 2.4), 150), see_through(lying, 60)]


def yarn() -> Sprite:
    """The thrown ball of yarn (12x12): rolls with a loose end trailing; bursts into loops on impact."""
    sprite = Sprite("yarn", (12, 12))
    mid = 5.5
    fly = []
    for i in range(4):
        c = Canvas(12, 12)
        for k in range(5):                               # trailing strand behind the ball
            c.px(mid - 4 - k * 0.9, mid + 2 + math.sin(k * 1.4 + i * 1.6) * 1.2, P.YARN_D if k < 3 else P.YARN)
        c.ellipse(mid, mid, 4, 4, P.YARN)
        a = -i * math.pi / 4
        for k in range(3):                               # wound strands, turning as it rolls
            ang = a + k * math.pi / 3
            dx, dy = math.cos(ang), math.sin(ang)
            nx, ny = -dy, dx
            off = (k - 1) * 1.6
            c.line((mid + nx * off - dx * 3.2, mid + ny * off - dy * 3.2),
                   (mid + nx * off + dx * 3.2, mid + ny * off + dy * 3.2), P.YARN_D)
        c.px(mid - 1.5, mid - 2, P.YARN_L)
        c.px(mid - 2, mid - 1, P.YARN_L)
        fly.append(c.outline(P.OUTLINE))
    sprite.add("fly", fly, fps=14)

    impact = []
    for i in range(5):
        c = Canvas(12, 12)
        reach = 1.5 + i * 1.1
        for k in range(6):
            ang = k / 6 * math.tau + i * 0.4
            x, y = mid + math.cos(ang) * reach, mid + math.sin(ang) * reach
            if i < 3:
                c.ellipse(x, y, 1, 1, P.YARN if (k + i) % 2 else P.YARN_L)
            else:
                c.px(x, y, P.YARN_L if k % 2 else P.YARN)
        if i < 2:
            c.ellipse(mid, mid, 3 - i * 1.2, 3 - i * 1.2, P.YARN)
            c.px(mid - 1, mid - 1, P.YARN_L)
        impact.append(c)
    sprite.add("impact", impact, fps=18, loop=False)
    return sprite
