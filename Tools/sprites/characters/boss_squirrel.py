"""World 1 boss: a giant crowned squirrel in an ermine collar (112x132; stands about 86px tall).

Throws acorns, curls up and rolls, and leaps up with a giant acorn to slam it down."""
from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image

import palette as P
from characters.forest import acorn_shape, bushy_tail
from draw import Canvas, r, see_through, tint
from sprite import Sprite

SIZE = (112, 132)
CX, GROUND = 52, 128


@dataclass
class KingPose:
    lift: float = 0
    squash: float = 0          # body lowered and widened (landing, crouch)
    near_arm: tuple = (30, 70)  # shoulder angle, elbow angle (absolute, 0 = down, + = forward)
    far_arm: tuple = (20, 60)
    holding: str = ""          # "" | "acorn" | "giant"
    hold_both: bool = False
    tail: float = 0
    eye: str = "open"          # open | shut | x | angry
    mouth: bool = False
    crown: bool = True
    breathe: float = 0


def crown(c: Canvas, x: float, y: float, tilt: float = 0) -> None:
    """A gold crown, 14 wide, its band's bottom-left corner at (x, y)."""
    c.poly([(x, y), (x + 14, y + tilt), (x + 14, y - 4 + tilt), (x, y - 4)], P.GOLD)
    for k, h in enumerate((5, 7, 5)):
        px = x + 1 + k * 6
        c.poly([(px - 1, y - 3 + tilt * k / 3), (px + 1, y - 3 - h + tilt * k / 3), (px + 3, y - 3 + tilt * k / 3)],
               P.GOLD)
        c.px(px + 1, y - 3 - h + tilt * k / 3, P.YELLOW)
    c.rect(x, y - 1 + tilt / 2, x + 14, y + tilt / 2, P.GOLD_D)
    c.rect(x + 2, y - 3, x + 3, y - 2, P.RED)
    c.rect(x + 6.5, y - 3 + tilt / 2, x + 7.5, y - 2 + tilt / 2, P.BLUE)
    c.rect(x + 11, y - 3 + tilt, x + 12, y - 2 + tilt, P.RED)
    c.px(x + 1, y - 4, P.YELLOW)


def king(pose: KingPose) -> Canvas:
    c = Canvas(*SIZE)
    x = CX
    gy = GROUND - pose.lift
    sq = pose.squash
    breathe = pose.breathe

    bushy_tail(c, (x - 15, gy - 16), pose.tail, 3.1)

    def arm(spec, color, paw):
        sx, sy = x + 7, gy - 44 + sq + breathe
        a1, a2 = math.radians(spec[0]), math.radians(spec[1])
        elbow = (sx + math.sin(a1) * 10, sy + math.cos(a1) * 10)
        hand = (elbow[0] + math.sin(a2) * 9, elbow[1] + math.cos(a2) * 9)
        c.line((sx, sy), elbow, color, 5)
        c.line(elbow, hand, color, 4)
        c.ellipse(hand[0], hand[1], 2.5, 2.5, paw)
        return hand

    far_hand = arm(pose.far_arm, P.RUST_D, P.RUST_D)

    # Haunch, big hind foot, body and belly.
    c.ellipse(x - 5, gy - 13 + sq * 0.3, 13 + sq * 0.3, 12 - sq * 0.3, P.RUST)
    c.ellipse(x + 3, gy - 2.5, 11, 3, P.RUST_D)
    c.ellipse(x + 1, gy - 30 + sq * 0.6 + breathe / 2, 15 + sq * 0.3, 21 - sq * 0.5 + abs(breathe) / 2, P.RUST)
    c.ellipse(x + 7, gy - 28 + sq * 0.6 + breathe / 2, 8, 16 - sq * 0.5, P.CREAM)
    c.ellipse(x + 5, gy - 18 + sq * 0.6, 5, 6, P.CREAM_D)
    c.ellipse(x - 8, gy - 16 + sq * 0.3, 6, 5, P.RUST_L)            # light on the haunch
    for k in range(3):
        c.line((x - 12 + k * 3, gy - 22 + k), (x - 10 + k * 3, gy - 30 + k), P.RUST_D)

    # A royal sash across the belly, with a gold acorn badge, and a gold collar.
    by = gy - 30 + sq * 0.6 + breathe / 2
    c.line((x - 9, by - 16), (x + 12, by + 10), P.RED, 5)
    c.line((x - 9, by - 18), (x + 13, by + 8), P.RED_D)
    c.ellipse(x + 3, by - 2, 3, 3, P.GOLD)
    c.ellipse(x + 3, by - 2, 1.5, 1.5, P.GOLD_D)
    hy = gy - 58 + sq + breathe
    c.ellipse(x + 3, hy + 12, 13, 3, P.GOLD_D)
    c.ellipse(x + 3, hy + 11.5, 12, 2, P.GOLD)
    c.rect(x + 8, hy + 13, x + 10, hy + 15, P.RED)

    # Head.
    hx = x + 7
    c.poly([(hx - 10, hy - 6), (hx - 9, hy - 19), (hx - 3, hy - 8)], P.RUST)               # ear with a tuft
    c.poly([(hx - 9.5, hy - 17), (hx - 11, hy - 22), (hx - 7, hy - 18)], P.RUST_D)
    c.px(hx - 8, hy - 11, P.PINK_D)
    c.ellipse(hx, hy, 13, 11, P.RUST)
    c.ellipse(hx + 6, hy + 4, 8, 5.5, P.CREAM)                                              # cheeks
    c.ellipse(hx + 12, hy, 5, 4, P.RUST)                                                    # snout
    c.ellipse(hx + 12, hy + 2, 4, 2, P.CREAM)
    c.rect(hx + 16, hy - 2, hx + 17, hy - 1, P.BLACK)                                       # nose
    c.rect(hx + 11, hy + 4, hx + 13, hy + 7, P.WHITE)                                       # buck teeth
    c.line((hx + 12, hy + 4), (hx + 12, hy + 7), P.CREAM_D)
    if pose.mouth:
        c.rect(hx + 8, hy + 4, hx + 10, hy + 6, P.RED_D)
    c.ellipse(hx - 6, hy + 3, 3, 2, P.RUST_L)
    ex, ey = hx + 4, hy - 4
    if pose.eye in ("open", "angry"):
        c.rect(ex, ey - 2, ex + 2, ey + 2, P.BLACK)
        c.px(ex + 2, ey - 2, P.WHITE)
        c.px(ex, ey + 2, P.WHITE)
        if pose.eye == "angry":
            c.line((ex - 2, ey - 5), (ex + 4, ey - 3), P.RUST_D, 2)
    elif pose.eye == "shut":
        c.line((ex - 1, ey), (ex + 3, ey + 1), P.BLACK)
    else:
        c.line((ex - 1, ey - 2), (ex + 3, ey + 2), P.BLACK)
        c.line((ex - 1, ey + 2), (ex + 3, ey - 2), P.BLACK)
    if pose.crown:
        crown(c, hx - 9, hy - 9, tilt=-1)

    near_hand = arm(pose.near_arm, P.RUST, P.RUST_D)
    if pose.holding == "acorn":
        acorn_shape(c, near_hand[0] + 1, near_hand[1] - 5, 1.4)
    elif pose.holding == "giant":
        mid = ((near_hand[0] + far_hand[0]) / 2, min(near_hand[1], far_hand[1]) - 10)
        acorn_shape(c, mid[0], mid[1], 2.6)
    return c


def finish(c: Canvas) -> Image.Image:
    return c.outline().img


def rolling_ball(step: int, frames: int) -> Image.Image:
    """Curled up into a ball of fur and tail; the crown stays on top as it rolls."""
    rad = 26
    ball = Canvas(SIZE[0], SIZE[0])
    m = SIZE[0] / 2
    ball.ellipse(m, m, rad, rad, P.RUST)
    ball.ellipse(m + 4, m + 5, rad * 0.55, rad * 0.5, P.CREAM)
    for k in range(18):                                    # tail wrapped around the outside
        a = math.radians(150 + k * 13)
        x, y = m + math.cos(a) * (rad - 3), m + math.sin(a) * (rad - 3)
        ball.ellipse(x, y, 5, 5, P.RUST_L if k % 3 else P.RUST)
    ball.ellipse(m + 14, m - 8, 5, 4, P.RUST)               # tucked snout
    ball.rect(m + 17, m - 10, m + 18, m - 9, P.BLACK)
    ball.line((m + 8, m - 12), (m + 12, m - 11), P.BLACK)   # shut eye
    for k in range(4):
        a = k * math.pi / 2 + 0.6
        ball.line((m + math.cos(a) * 8, m + math.sin(a) * 8), (m + math.cos(a) * 16, m + math.sin(a) * 16), P.RUST_D)
    turned = ball.img.rotate(-360 / frames * step, resample=Image.NEAREST, center=(m, m))
    c = Canvas(*SIZE)
    c.paste(turned, 0, GROUND - (m + rad))
    crown(c, CX - 7, GROUND - 2 * rad - 1 + (step % 2), tilt=(-1, 1)[step % 2])
    for k in range(3):                                      # dust kicked up behind
        c.ellipse(CX - rad - 6 - k * 6, GROUND - 2 - (k + step) % 2 * 2, 2.5 - k * 0.5, 2 - k * 0.4, P.SAND)
    return finish(c)


def build() -> list[Sprite]:
    boss = Sprite("boss_squirrel", SIZE, faces_left=True, cx=CX, ground=GROUND)

    boss.add("idle", [finish(king(KingPose(tail=t, breathe=b, eye=e)))
                      for t, b, e in ((0, 0, "open"), (2, -1, "open"), (3, -1, "open"), (1, 0, "shut"))], fps=4)

    boss.add("throw", [finish(king(p)) for p in (
        KingPose(near_arm=(40, 90), holding="acorn", eye="angry"),
        KingPose(near_arm=(-90, -150), holding="acorn", squash=2, eye="angry", tail=-2),
        KingPose(near_arm=(-150, -170), holding="acorn", squash=3, eye="angry", tail=-3, mouth=True),
        KingPose(near_arm=(110, 100), mouth=True, eye="angry", tail=3),
        KingPose(near_arm=(80, 70), mouth=True, tail=2),
        KingPose(near_arm=(40, 70), tail=0),
    )], fps=10, loop=False)

    boss.add("roll", [rolling_ball(k, 6) for k in range(6)], fps=14)

    boss.add("climb", [finish(king(p)) for p in (
        KingPose(squash=6, near_arm=(-20, -30), far_arm=(-10, -20), eye="angry", tail=-3),
        KingPose(lift=16, near_arm=(170, 175), far_arm=(165, 175), holding="giant", eye="angry", tail=-4),
        KingPose(lift=34, near_arm=(175, 180), far_arm=(170, 180), holding="giant", mouth=True, tail=-5),
        KingPose(lift=36, near_arm=(170, 175), far_arm=(165, 175), holding="giant", mouth=True, tail=-5),
        KingPose(lift=12, near_arm=(100, 110), far_arm=(90, 100), mouth=True, tail=4),
        KingPose(squash=5, near_arm=(60, 80), far_arm=(50, 70), eye="angry", tail=2),
    )], fps=8, loop=False)

    hurt = finish(king(KingPose(eye="shut", mouth=True, near_arm=(-20, 40), far_arm=(-30, 30), squash=2, tail=-3)))
    boss.add("hurt", [tint(hurt, P.WHITE, 0.8), hurt], fps=10)

    # Dazed, wobbles, and slumps away; the crown tumbles off and stays on the ground.
    dazed = finish(king(KingPose(eye="x", mouth=True, crown=False, near_arm=(10, 30), far_arm=(0, 20), squash=3)))
    frames = []
    for k in range(8):
        t = k / 7
        frame = Image.new("RGBA", SIZE, P.CLEAR)
        body = dazed.rotate((0, 3, -3, 5, 7, 9, 11, 12)[k], resample=Image.NEAREST, center=(CX, GROUND))
        if k >= 4:
            body = see_through(body, r(255 * (1 - (k - 3) / 5)))
        frame.alpha_composite(tint(body, P.WHITE, 0.7) if k == 0 else body)
        cc = Canvas(*SIZE)
        fall_y = min(GROUND - 3, GROUND - 75 + t * t * 140)
        crown(cc, CX + 18 + k * 2, fall_y, tilt=(k % 3) - 1)
        cc.outline()
        frame.alpha_composite(cc.img)
        frames.append(frame)
    boss.add("death", frames, fps=8, loop=False)
    return [boss]
