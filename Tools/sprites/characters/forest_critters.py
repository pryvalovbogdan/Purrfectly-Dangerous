"""World 1, the Purrwood forest critters (from the forest enemy atlas in docs/concept/): the cat slime,
mushroom cat, forest bat, plant cat, bee cat, stump cat, snail cat and spider cat, and the spores,
stings and leaves they throw. Drawn facing right with light from the top-left; mirrored on export.

Gameplay hitboxes (w x h, anchored at the feet) are noted on each sprite; the body covers them."""
from __future__ import annotations

import math

from PIL import Image

import palette as P
from critters import ear, face, ramp, shaded, sparkle
from draw import Canvas, see_through, tint, vanish
from sprite import Sprite

EDGE = P.OUTLINE


def framed(size, draw) -> Image.Image:
    c = Canvas(*size)
    draw(c)
    return c.outline(EDGE).img


# --- slime [14x10] -------------------------------------------------------------------------------

SLIME_RAMP = ramp((P.SLIME_L, P.SLIME, P.SLIME_D))


def slime_body(c: Canvas, cx: float, gy: float, sx: float = 1.0, sy: float = 1.0, eyes: str = "open",
               mouth: str = "smile") -> None:
    """A glossy lime blob with cat ears, base on `gy`; `sx`/`sy` squash and stretch it."""
    height = 11 * sy                     # a dome: an ellipse cut flat at the ground, widest at the base
    ry = height * 0.72
    rx = 7.0 * sx / 0.92
    ey = gy - height + ry
    top = gy - height + 1
    with shaded(c, SLIME_RAMP, up=1, down=1) as p:
        ear(p, cx - 3.5 * sx, top + 2.5, 5.5, P.SLIME, inner=None, lean=-1.2, half=3)
        ear(p, cx + 4 * sx, top + 2.5, 5.5, P.SLIME, inner=None, lean=1.2, half=3)
        p.ellipse(cx, ey, rx, ry, P.SLIME)
        p.rect(0, gy + 1, p.size[0], p.size[1], P.CLEAR)
    c.rect(cx - 3.5 * sx - 1, top - 0.5, cx - 3.5 * sx - 1, top + 0.5, P.SLIME_D)   # inner ears
    c.rect(cx + 4 * sx + 1, top - 0.5, cx + 4 * sx + 1, top + 0.5, P.SLIME_D)
    for x in range(int(cx - rx * 0.88), int(cx + rx * 0.88) + 1):   # the wet rim it slides on
        c.px(x, gy, P.SLIME_RIM)
    c.px(cx - rx * 0.8, gy - 1, P.SLIME_RIM)
    c.rect(cx - 5 * sx, top + 3, cx - 5 * sx + 1, top + 4, P.WHITE)  # gloss
    c.px(cx - 6 * sx, top + 6, P.SLIME_L)
    c.px(cx + 5 * sx, gy - 2, P.SLIME_D)
    c.px(cx + 3 * sx, gy - 1, P.SLIME_D)
    face(c, cx + 2, gy - 6 * sy - 0.5, eyes=eyes, mouth=mouth, gap=5, nose=None, blush=P.GOLD)


def slime() -> Sprite:
    size, cx, gy = (24, 20), 12, 18
    sprite = Sprite("slime", size, faces_left=True, cx=cx, ground=gy)
    squash = ((1.12, 0.85, "w"), (1.0, 1.0, "smile"), (0.9, 1.15, "open"), (1.0, 1.0, "smile"))
    sprite.add("walk", [framed(size, lambda c, s=s: slime_body(c, cx, gy, s[0], s[1], mouth=s[2]))
                        for s in squash], fps=8)

    def melt(t: float):
        def draw(c):
            slime_body(c, cx, gy, 1.0 + t * 0.15, max(0.35, 1.0 - t * 0.75), eyes="x", mouth="flat")
            for k, (dx, dy) in enumerate(((-6, -9), (5, -11), (-1, -13))):
                if t > 0:
                    sparkle(c, cx + dx * 0.8, gy + dy + 2 - t * 2, P.SLIME_L)
        return draw

    frames = [tint(framed(size, melt(0)), P.WHITE, 0.6)] + [framed(size, melt(t)) for t in (0.4, 0.75, 1.0)]
    frames[2] = see_through(frames[2], 180)
    frames[3] = see_through(frames[3], 80)
    sprite.add("death", frames, fps=10, loop=False)
    return sprite


# --- mushroom cat [14x16] + spore ----------------------------------------------------------------

CAP_RAMP = ramp((P.CAPE_L, P.RED, P.CAPE_D))
CREAM_RAMP = ramp((P.FUR_WHITE, P.CREAM, P.CREAM_D))


def mushroom_cap(c: Canvas, x: float, y: float, w: float = 10, h: float = 7, tilt: float = 0) -> None:
    """A red cap with white spots; (x, y) is the centre of its underside."""
    with shaded(c, CAP_RAMP, EDGE, up=2, down=2) as p:
        p.ellipse(x + tilt * 0.5, y - h + 1.5, w, h, P.RED)
    # Gills along the flat underside.
    c.rect(x - w + 2, y, x + w - 2, y + 1, P.CREAM_D)
    c.rect(x - w + 2, y + 1, x + w - 2, y + 1, P.SAND)
    for sx, sy, sr in ((-5, -6, 1.6), (1.5, -8.5, 1.4), (6, -4.5, 1.6), (-1.5, -3, 1.0), (-8, -2.5, 0.8),
                       (4, -9.5, 0.6)):
        if sr >= 1:
            c.ellipse(x + sx + tilt * 0.3, y + sy, sr, sr * 0.9, P.WHITE)
        else:
            c.px(x + sx + tilt * 0.3, y + sy, P.WHITE)


def mushroom_cat_frame(bob: float = 0, squat: float = 0, cap_lift: float = 0, tilt: float = 0, eyes: str = "open",
                       mouth: str = "w", step: int = 0, puff: float = 0) -> Image.Image:
    size, cx, gy = (28, 28), 14, 26
    c = Canvas(*size)
    body_top = gy - 11 + squat
    # Thin tail curling up and away behind it.
    tail = [(cx - 5, gy - 2), (cx - 9, gy - 4), (cx - 11, gy - 7), (cx - 11, gy - 9 - bob), (cx - 10, gy - 10 - bob)]
    for a, b in zip(tail, tail[1:]):
        c.line(a, b, P.CREAM_D)
    with shaded(c, CREAM_RAMP) as p:
        p.ellipse(cx, gy - 4.5 + squat / 2, 6, 5 - squat / 2, P.CREAM)
        p.rect(cx - 5, body_top, cx + 5, gy - 5, P.CREAM)
        p.rect(cx - 5, gy - 1, cx + 5, gy, P.CREAM)
    lift = step % 2
    c.rect(cx - 5, gy, cx - 1, gy, P.CREAM_D)                              # two stubby feet
    c.rect(cx + 1, gy, cx + 5, gy, P.CREAM_D)
    c.px(cx, gy, EDGE)
    if lift:
        c.rect(cx - 5, gy, cx - 1, gy, P.CLEAR)
    c.px(cx + 5, gy - 4, P.CREAM_D)                                        # near paw
    c.px(cx + 6, gy - 4, P.CREAM)
    face(c, cx + 2, body_top + 4, eyes=eyes, mouth=mouth, gap=4)
    mushroom_cap(c, cx, body_top - cap_lift + bob, w=10, h=6, tilt=tilt)
    if puff:
        for dx, dy, rad in ((8, -6, 1.8), (10, -3.5, 1.2), (10, -9, 1.0)):
            c.ellipse(cx + dx * puff, gy + dy, rad, rad, P.YARN_L)
            c.px(cx + dx * puff - 0.5, gy + dy - 0.5, P.WHITE)
    return c.outline(EDGE).img


def mushroom_cat() -> Sprite:
    sprite = Sprite("mushroom_cat", (28, 28), faces_left=True, cx=14, ground=26)
    sprite.add("idle", [mushroom_cat_frame(0), mushroom_cat_frame(1, step=1)], fps=3)
    sprite.add("throw", [mushroom_cat_frame(squat=1, tilt=-2, eyes="shut", mouth="flat"),
                         mushroom_cat_frame(squat=2, tilt=-3, eyes="shut", mouth="flat"),
                         mushroom_cat_frame(cap_lift=2, tilt=2, eyes="open", mouth="open", puff=1.0),
                         mushroom_cat_frame(cap_lift=1, eyes="open", mouth="w")], fps=8, loop=False)
    dead = mushroom_cat_frame(squat=2, eyes="x", mouth="flat")
    frames = [tint(dead, P.WHITE, 0.6)] + [vanish(dead, t, depth=6, flash=False) for t in (0.35, 0.65, 0.95)]
    sprite.add("death", frames, fps=10, loop=False)
    return sprite


def spore() -> Sprite:
    sprite = Sprite("spore", (10, 10), faces_left=True)
    frames = []
    for k in range(4):
        c = Canvas(10, 10)
        wob = (0, 0.4, 0, -0.4)[k]
        for i in range(5):
            a = i / 5 * math.tau + k * 0.6
            c.ellipse(4.5 + math.cos(a) * 2, 4.5 + math.sin(a) * 2, 1.6 + wob, 1.6 + wob, P.YARN_L)
        c.ellipse(4.5, 4.5, 2.2, 2.2, P.PINK)
        c.px(3.5, 3.5, P.WHITE)
        c.px(4.5 + math.cos(k * 1.6) * 2, 4.5 + math.sin(k * 1.6) * 2, P.WHITE)
        c.outline(P.YARN_D)
        frames.append(c.img)
    sprite.add("fly", frames, fps=10)
    return sprite


# --- forest bat [14x10] ---------------------------------------------------------------------------

BAT_RAMP = ramp((P.PLANK_L, P.PLANK, P.PLANK_D))
WING_RAMP = ramp((P.BATWING_L, P.BATWING, P.BATWING_D))


def bat_wing(c: Canvas, root: tuple[float, float], side: int, flap: float, far: bool) -> None:
    """A scalloped membrane wing; side +1 spreads right, -1 left; flap 1 = raised, -1 = lowered."""
    rx, ry = root
    span = 12 if not far else 11
    tip = (rx + side * span, ry - 3 - flap * 5)
    elbow = (rx + side * span * 0.45, ry - 3.5 - flap * 3.5)
    low = ry + 2 - flap * 1.5
    pts = [root, elbow, tip]
    # Scallops between the finger tips along the trailing edge.
    for k, t in enumerate((0.8, 0.62, 0.42, 0.22)):
        depth = 2.5 if k % 2 == 0 else 0
        x = rx + side * span * t
        y = tip[1] + (low - tip[1]) * (1 - t) + 2 + depth - (flap * 2 if k % 2 else 0)
        pts.append((x, y))
    pts.append((rx, ry + 3))
    with shaded(c, WING_RAMP, EDGE, up=1, down=1) as p:
        p.poly(pts, P.BATWING_D if far else P.BATWING)
    c.line(root, elbow, P.BATWING_D)
    c.line(elbow, tip, P.BATWING_D)
    for t in (0.62, 0.22):                               # finger bones
        c.line(elbow, (rx + side * span * t, tip[1] + (low - tip[1]) * (1 - t) + 2), P.BATWING_D)


def forest_bat_frame(flap: float, eyes: str = "open", mouth: str = "w", bob: float = 0) -> Image.Image:
    size, cx, gy = (34, 24), 17, 18
    c = Canvas(*size)
    y = gy + bob
    bat_wing(c, (cx - 2, y - 7), -1, flap, far=False)
    bat_wing(c, (cx + 2, y - 7), 1, flap * 0.85, far=True)
    with shaded(c, BAT_RAMP, EDGE) as p:
        p.ellipse(cx - 1, y - 4, 4, 3.5, P.PLANK)                   # body
        p.rect(cx - 3, y - 1, cx - 2, y, P.PLANK)                   # feet dangling
        p.rect(cx + 0, y - 1, cx + 1, y, P.PLANK)
    with shaded(c, BAT_RAMP, EDGE) as p:
        ear(p, cx - 2, y - 11, 4, P.PLANK, inner=None, lean=-0.5, half=2)
        ear(p, cx + 4, y - 11, 4, P.PLANK, inner=None, lean=0.5, half=2)
        p.ellipse(cx + 1, y - 8, 5.5, 4.5, P.PLANK)                 # big round head
    c.px(cx - 2, y - 13, P.PINK_D)
    c.px(cx + 4, y - 13, P.PINK_D)
    c.ellipse(cx + 2, y - 5.5, 2.5, 1.2, P.PLANK_L)                 # muzzle
    face(c, cx + 3, y - 9, eyes=eyes, mouth=mouth, gap=4, nose=P.BARK_DD)
    return c.outline(EDGE).img


def forest_bat() -> Sprite:
    sprite = Sprite("forest_bat", (34, 24), faces_left=True, cx=17, ground=18)
    sprite.add("fly", [forest_bat_frame(f, bob=b) for f, b in ((1, 0), (0.2, 0), (-0.9, -1), (0.2, -1))], fps=12)
    dead = forest_bat_frame(-0.5, eyes="x", mouth="open")
    sprite.add("death", [tint(dead, P.WHITE, 0.6), vanish(dead, 0.45, depth=6, flash=False),
                         vanish(dead, 0.9, depth=6, flash=False)], fps=10, loop=False)
    return sprite


# --- plant cat [14x22] -----------------------------------------------------------------------------

LEAF_RAMP = ramp((P.KIT_GREEN_L, P.KIT_GREEN, P.KIT_GREEN_D), (P.LEAF_Y, P.KIT_GREEN_L, P.KIT_GREEN))
HEAD_RAMP = ramp((P.CAPE_L, P.RED, P.CAPE_D))


def leaf_shape(c: Canvas, base: tuple[float, float], angle: float, length: float, width: float, colour) -> None:
    """A rounded, pointed leaf from `base` toward `angle` degrees (0 = right, 90 = up)."""
    a = math.radians(angle)
    ux, uy = math.cos(a), -math.sin(a)
    nx, ny = -uy, ux
    bx, by = base
    side = [(0.2, 0.6), (0.4, 0.95), (0.6, 1.0), (0.8, 0.7)]
    pts = [base]
    pts += [(bx + ux * length * t + nx * width * w, by + uy * length * t + ny * width * w) for t, w in side]
    pts.append((bx + ux * length, by + uy * length))
    pts += [(bx + ux * length * t - nx * width * w, by + uy * length * t - ny * width * w) for t, w in reversed(side)]
    c.poly(pts, colour)


def plant_stem(c: Canvas, cx: float, gy: float, sway: float, droop: float = 0) -> tuple[float, float]:
    """Curved stem with a pair of big leaves halfway up; returns the top of the stem."""
    top = (cx + sway, gy - 12 + droop)
    mid = (cx - 1 + sway * 0.3, gy - 6)
    with shaded(c, LEAF_RAMP, EDGE) as p:
        p.line((cx, gy), mid, P.KIT_GREEN, 2)
        p.line(mid, top, P.KIT_GREEN, 2)
    with shaded(c, LEAF_RAMP, EDGE) as p:
        leaf_shape(p, (mid[0] + 1, mid[1] - 0.5), 35 - droop * 12, 8, 2.6, P.KIT_GREEN)
        leaf_shape(p, (mid[0] - 0.5, mid[1] - 0.5), 145 + droop * 12, 8, 2.6, P.KIT_GREEN)
    for side in (-1, 1):                                                                   # leaf veins
        c.line((mid[0] + side * 1.5, mid[1] - 1.5), (mid[0] + side * 5, mid[1] - 4 + droop * 1.5), P.KIT_GREEN_D)
    c.line((cx - 3, gy), (cx + 3, gy), P.KIT_GREEN_D)                                      # roots in the soil
    c.px(cx - 2, gy - 1, P.KIT_GREEN)
    c.px(cx + 2, gy - 1, P.KIT_GREEN)
    return top


def plant_spots(c: Canvas, x: float, y: float) -> None:
    for dx, dy in ((-4, -1), (-1, -3), (-2, 1), (1, -4)):
        c.px(x + dx, y + dy, P.PINK)


def plant_cat_frame(mode: str, k: int = 0) -> Image.Image:
    """mode: bud (closed), open (opening by k = 0, 1), bite (k = 0 wide, 1 snap, 2 recover), dead (k = 0...3)."""
    size, cx, gy = (32, 32), 14, 30
    c = Canvas(*size)
    sway = (0, 1)[k % 2] if mode == "bud" else (1 if mode == "open" else 0)
    lunge = {"bite": (2, 4, 1)}.get(mode, (0, 0, 0))[min(k, 2)]
    droop = k * 1.2 if mode == "dead" else 0
    top = plant_stem(c, cx, gy, sway + lunge * 0.5, droop)
    hx, hy = top[0] + 1 + lunge + droop * 0.8, top[1] - 5 + droop * 0.8
    if mode == "bud":
        with shaded(c, HEAD_RAMP, EDGE, up=2) as p:
            ear(p, hx - 3, hy - 4, 3, P.RED, inner=None, lean=-0.5, half=1.8)
            ear(p, hx + 3, hy - 4, 3, P.RED, inner=None, lean=0.5, half=1.8)
            p.ellipse(hx, hy, 5, 5.5, P.RED)
            p.poly([(hx - 2, hy - 5), (hx, hy - 8), (hx + 2, hy - 5)], P.RED)
        c.line((hx, hy - 6), (hx - 2, hy + 4), P.CAPE_D)              # folded petals
        c.line((hx + 3, hy - 3), (hx + 1, hy + 4), P.CAPE_D)
        c.px(hx - 3, hy - 1, P.PINK)
        c.px(hx + 2, hy - 3, P.PINK)
        c.px(hx - 1, hy + 2, P.PINK)
        with shaded(c, LEAF_RAMP, EDGE) as p:                         # green sepals cupping the bud
            for side in (-1, 1):
                leaf_shape(p, (hx, hy + 5), 90 + side * 55, 5, 1.6, P.KIT_GREEN)
            p.ellipse(hx, hy + 5, 2.5, 1.2, P.KIT_GREEN)
        return c.outline(EDGE).img
    # An open head: a round red cat head with a wedge of mouth cut in from the front.
    gape = {"open": (1.2, 3), "bite": (5.5, 0.6, 3), "dead": (1.5, 1.5, 1.5, 1.5)}[mode][k]
    size_r = 6 + min(gape, 4) * 0.3
    with shaded(c, LEAF_RAMP, EDGE) as p:                             # leafy collar under the head
        for side in (-1, 1):
            leaf_shape(p, (hx - 1, hy + 4), 90 + side * 70, 5, 1.8, P.KIT_GREEN)
    with shaded(c, HEAD_RAMP, EDGE, up=2) as p:
        ear(p, hx - 4, hy - size_r + 2, 4, P.RED, inner=P.CAPE_D, lean=-0.8, half=2.2)
        ear(p, hx + 2, hy - size_r + 1.5, 4, P.RED, inner=P.CAPE_D, lean=0.6, half=2.2)
        p.ellipse(hx, hy, size_r + 0.5, size_r, P.RED)
    hinge = (hx - 2, hy + 1)
    front = hx + size_r + 2
    up, down = (hy + 1 - gape * 1.1, hy + 1 + gape * 0.9)
    plant_spots(c, hx - 1, hy - 1)
    if gape >= 1:
        c.poly([hinge, (front, up), (front, down)], P.CLEAR)          # cut the mouth out...
        mouth = Canvas(*size)
        mouth.poly([hinge, (front - 1, up + 0.5), (front - 1, down - 0.5)], P.MAROON)   # ...and fill it in dark
        if gape > 2:
            mouth.ellipse(hinge[0] + (front - hinge[0]) * 0.55, down - 1.5, 2.5, 1, P.PINK_D)   # tongue
        c.paste(mouth)
        n = int((front - hinge[0]) // 2)
        for i in range(1, n + 1):                                    # teeth along both lips
            t = i * 2 / (front - hinge[0])
            c.px(hinge[0] + (front - 1 - hinge[0]) * t, hinge[1] + (up + 1 - hinge[1]) * t, P.WHITE)
            if gape > 2:
                c.px(hinge[0] + (front - 1 - hinge[0]) * t - 1, hinge[1] + (down - 1 - hinge[1]) * t, P.WHITE)
    eyes = "x" if mode == "dead" else ("angry" if mode == "bite" else "open")
    face(c, hx + 2, hy - 3 - (1 if gape > 3 else 0), eyes=eyes, mouth=None, gap=4, nose=None, blush=None)
    return c.outline(EDGE).img


def plant_cat() -> Sprite:
    sprite = Sprite("plant_cat", (32, 32), faces_left=True, cx=14, ground=30)
    sprite.add("idle", [plant_cat_frame("bud", 0), plant_cat_frame("bud", 1)], fps=3)
    sprite.add("warn", [plant_cat_frame("open", 0), plant_cat_frame("open", 1)], fps=6)
    sprite.add("bite", [plant_cat_frame("bite", k) for k in range(3)], fps=10, loop=False)
    frames = [tint(plant_cat_frame("dead", 0), P.WHITE, 0.6)]
    frames += [plant_cat_frame("dead", 1), see_through(plant_cat_frame("dead", 2), 170),
               see_through(plant_cat_frame("dead", 3), 80)]
    sprite.add("death", frames, fps=8, loop=False)
    return sprite


# --- bee cat [14x12] + sting ---------------------------------------------------------------------

BEE_RAMP = ramp((P.YELLOW, P.GOLD, P.GOLD_D), (P.GREY_D, P.SLATE, P.BLACK))


def bee_wings(size, root: tuple[float, float], flap: float) -> Image.Image:
    """Two translucent blue wing lobes rising from the back; flap 1 = up, -1 = swept down and back."""
    c = Canvas(*size)
    rx, ry = root
    for dx, scale, colour in ((-2.5, 0.85, P.BLUE), (0.5, 1.0, P.BLUE_L)):
        cx_, cy_ = rx + dx - (1 - flap) * 1.2, ry - 4 - flap * 1.5
        c.ellipse(cx_, cy_, (2.6 + (1 - flap) * 0.6) * scale, (3.8 - (1 - flap) * 0.7) * scale, colour)
        c.px(cx_ - 0.5, cy_ - 1.5, P.WHITE)
    c.outline(P.BLUE_D)
    return see_through(c.img, 190)


def bee_cat_frame(flap: float, bob: float = 0, sting: float = 0, eyes: str = "open", mouth: str = "w",
                  wings: bool = True) -> Image.Image:
    """sting: 0 = rest, -1 = abdomen cocked back, 1 = curled under with the stinger thrust forward."""
    size, cx, gy = (28, 22), 13, 19
    y = gy + bob
    c = Canvas(*size)
    ax, ay = cx - 3 + max(0, sting) * 1.5, y - 4 - max(0, -sting) * 1.5 + max(0, sting) * 0.5
    if sting > 0.5:
        base, tip = (ax + 1, ay + 3), (ax + 5, y - 1.5)
    else:
        base, tip = (ax - 4, ay + 1), (ax - 7.5, ay + 2 - sting * 2)
    c.line(base, tip, P.SLATE, 2)                                           # stinger
    c.px(tip[0], tip[1], P.GREY_L)
    with shaded(c, BEE_RAMP, EDGE) as p:
        p.ellipse(ax, ay, 5, 4.2, P.GOLD)                                     # striped abdomen
    for sx in (-3, 0.5):
        for yy in range(int(ay - 5), int(ay + 6)):
            for xx in (ax + sx, ax + sx + 1):
                if c.img.getpixel((round(xx), yy))[:3] in (P.GOLD[:3], P.GOLD_D[:3], P.YELLOW[:3]):
                    c.px(xx, yy, P.SLATE if c.img.getpixel((round(xx), yy))[:3] != P.GOLD_D[:3] else P.BLACK)
    c.rect(ax - 2, y - 1, ax - 1, y, P.SLATE)                                 # dangling legs
    c.rect(ax + 2, y - 1, ax + 3, y, P.SLATE)
    if wings:
        c.paste(bee_wings(size, (ax + 1, ay - 2 + max(0, -sting) * 1.5), flap))
    with shaded(c, BEE_RAMP, EDGE) as p:
        ear(p, cx + 1, y - 12, 3.5, P.GOLD, inner=None, lean=-0.5, half=2)
        ear(p, cx + 6.5, y - 12, 3.5, P.GOLD, inner=None, lean=0.5, half=2)
        p.ellipse(cx + 3.5, y - 8.5, 5.5, 4.5, P.GOLD)                       # big round head
    c.px(cx + 1, y - 14, P.ORANGE)
    c.px(cx + 6.5, y - 14, P.ORANGE)
    c.ellipse(cx + 5, y - 6, 2.5, 1.2, P.YELLOW)                             # muzzle
    face(c, cx + 5.5, y - 10, eyes=eyes, mouth=mouth, gap=4, nose=P.ORANGE)
    if sting > 0.5:
        sparkle(c, tip[0] + 2, tip[1] - 1, P.YELLOW)
    return c.outline(EDGE).img


def bee_cat() -> Sprite:
    sprite = Sprite("bee_cat", (28, 22), faces_left=True, cx=13, ground=19)
    sprite.add("fly", [bee_cat_frame(f, b) for f, b in ((1, 0), (0, 0), (-1, -1), (0, -1))], fps=14)
    sprite.add("throw", [bee_cat_frame(1, 0, -1, eyes="angry", mouth="flat"),
                         bee_cat_frame(-1, 0, 1, eyes="angry", mouth="fangs"),
                         bee_cat_frame(0, 0, 0.3, mouth="w")], fps=10, loop=False)
    dead = bee_cat_frame(-1, 0, 0, eyes="x", mouth="open")
    frames = [tint(dead, P.WHITE, 0.6)]
    for t in (0.35, 0.65, 0.95):
        frames.append(vanish(bee_cat_frame(-1, 0, 0, eyes="x", mouth="open", wings=t < 0.5), t, depth=7, flash=False))
    sprite.add("death", frames, fps=10, loop=False)
    return sprite


def sting() -> Sprite:
    """A glowing stinger dart, point first (right; mirrored it flies left), with a short sparkling trail."""
    sprite = Sprite("sting", (12, 6), faces_left=True)
    frames = []
    for k in range(4):
        out = Canvas(12, 6)
        out.ellipse(7, 2.5, 3.5 + (k % 2) * 0.7, 2.4, (*P.ORANGE[:3], 140))      # soft glow
        c = Canvas(12, 6)
        c.poly([(3, 2), (7, 1), (11, 2.5), (7, 4), (3, 3)], P.GOLD)
        c.rect(4, 2, 9, 2, P.YELLOW)
        c.rect(6, 2, 8, 3, P.YELLOW)
        c.px(7, 2, P.WHITE)
        c.px(8, 2, P.WHITE)
        c.outline(P.GOLD_D)
        for j, (tx, ty) in enumerate(((1, 2), (0, 3), (2, 3))):               # sparkling trail
            if (j + k) % 2 == 0:
                c.px(tx, ty, P.YELLOW)
        out.paste(c)
        frames.append(out.img)
    sprite.add("fly", frames, fps=12)
    return sprite


# --- stump cat [16x22] + leaf ----------------------------------------------------------------------

BARK_RAMP = ramp((P.BARK_L, P.BARK, P.BARK_D), (P.PLANK_L, P.PLANK, P.PLANK_D))


def stump_cat_frame(squash: float = 0, eyes: str = "glow", mouth: str = "shut", sway: int = 0, shine: int = 0) -> Image.Image:
    size, cx, gy = (28, 30), 14, 28
    c = Canvas(*size)
    top = gy - 19 + squash
    with shaded(c, BARK_RAMP, EDGE, up=1, down=1, right=2) as p:
        p.poly([(cx - 10, gy), (cx - 8, gy - 3), (cx - 7.5, top + 1), (cx + 7.5, top + 1), (cx + 8, gy - 3),
                (cx + 10, gy)], P.BARK)                                       # trunk with flared roots
        ear(p, cx - 5, top + 1, 4, P.BARK, inner=None, lean=-0.5, half=2.5)
        ear(p, cx + 5, top + 1, 4, P.BARK, inner=None, lean=0.5, half=2.5)
    for x, t in ((cx - 4, 4), (cx - 1, 7), (cx + 3, 5), (cx + 6, 3)):        # bark grooves
        c.line((x, top + t), (x + (1 if x % 2 else -1) * 0.5, gy - 2), P.BARK_D)
    c.line((cx - 9, gy - 1), (cx - 7, gy - 3), P.BARK_L)                    # roots
    c.line((cx + 8, gy - 1), (cx + 7, gy - 3), P.BARK_DD)
    c.px(cx - 1, gy, P.BARK_D)
    c.px(cx + 3, gy, P.BARK_D)
    with shaded(c, BARK_RAMP) as p:                                          # cut top with rings
        p.ellipse(cx, top + 1.5, 7.5, 2, P.PLANK)
    c.ellipse(cx, top + 1.5, 4.5, 1, P.PLANK_L)
    c.rect(cx - 1, top + 1.5, cx + 1, top + 1.5, P.PLANK)
    with shaded(c, LEAF_RAMP, EDGE) as p:                                    # sprouting leaves
        p.line((cx - 3, top + 1), (cx - 3, top - 2), P.KIT_GREEN)
        leaf_shape(p, (cx - 3, top - 2), 130 + sway * 8, 5, 2, P.KIT_GREEN)
        leaf_shape(p, (cx - 3, top - 2), 60 + sway * 8, 4, 1.6, P.KIT_GREEN)
        leaf_shape(p, (cx + 7, top + 2), 30 - sway * 6, 3, 1.3, P.KIT_GREEN)
    ey = top + 8                                                             # hollow eyes with a green glow
    for ex in (cx - 4, cx + 2):
        c.ellipse(ex + 0.5, ey + 0.5, 1.8, 1.8, P.BARK_DD)
        if eyes == "glow":
            c.rect(ex, ey, ex + 1, ey + 1, P.LEAF_Y)
            c.px(ex + (1 if shine else 0), ey, P.WHITE)
        elif eyes == "angry":
            c.rect(ex, ey + 1, ex + 1, ey + 1, P.LEAF_Y)
        elif eyes == "x":
            c.px(ex, ey, P.LEAF_Y)
            c.px(ex + 1, ey + 1, P.LEAF_Y)
    my = ey + 5
    if mouth == "shut":
        c.rect(cx - 1, my, cx + 1, my, P.BARK_DD)
    else:
        c.ellipse(cx, my + 0.5, 1.8, 1.8, P.BARK_DD)
        c.px(cx, my + 1, P.KIT_GREEN)
    c.px(cx - 6, ey + 3, P.BARK_D)                                           # cheek knots
    c.px(cx + 5, ey + 3, P.BARK_D)
    for gx in (cx - 9, cx - 5, cx + 9):                                      # grass at the foot
        c.line((gx, gy), (gx - 1, gy - 2), P.KIT_GREEN)
    return c.outline(EDGE).img


def stump_cat() -> Sprite:
    sprite = Sprite("stump_cat", (28, 30), faces_left=True, cx=14, ground=28)
    sprite.add("idle", [stump_cat_frame(0, sway=0), stump_cat_frame(0, sway=1, shine=1)], fps=3)
    sprite.add("throw", [stump_cat_frame(1, eyes="angry"), stump_cat_frame(0, mouth="open", sway=1),
                         stump_cat_frame(0, mouth="shut")], fps=8, loop=False)
    still = stump_cat_frame(1, eyes="x", mouth="open")
    frames = [tint(still, P.WHITE, 0.6)]
    frames += [vanish(still, t, depth=9, flash=False) for t in (0.3, 0.6, 0.9)]   # sinks back into the soil
    sprite.add("death", frames, fps=10, loop=False)
    return sprite


def leaf() -> Sprite:
    sprite = Sprite("leaf", (10, 8), faces_left=True)
    frames = []
    for k, ang in enumerate((10, -10, -25, -5)):
        c = Canvas(10, 8)
        a = math.radians(ang)
        base = (5 - math.cos(a) * 4, 4 + math.sin(a) * 4)
        with shaded(c, LEAF_RAMP) as p:
            leaf_shape(p, base, ang, 8, 2.6 - (k == 2) * 0.6, P.KIT_GREEN)
        c.line(base, (base[0] + math.cos(a) * 6, base[1] - math.sin(a) * 6), P.KIT_GREEN_D)
        frames.append(c.outline(EDGE).img)
    sprite.add("fly", frames, fps=10)
    return sprite


# --- snail cat [18x12] -----------------------------------------------------------------------------

SHELL_RAMP = ramp((P.SHELL_L, P.SHELL, P.SHELL_D))
GINGER_RAMP = ramp((P.GINGER_L, P.GINGER, P.GINGER_D), (P.FUR_WHITE, P.CREAM, P.CREAM_D))


def snail_shell(c: Canvas, x: float, y: float, rad: float, turn: float = 0) -> None:
    with shaded(c, SHELL_RAMP, EDGE, up=2, down=2, right=2) as p:
        p.ellipse(x, y, rad, rad, P.SHELL)
    for i in range(36):                                                      # the spiral groove
        t = i / 35
        a = turn + t * math.tau * 2.1
        rr = rad * (0.85 - t * 0.78)
        c.px(x + math.cos(a) * rr, y + math.sin(a) * rr, P.SHELL_DD)
    c.px(x - rad * 0.55, y - rad * 0.6, P.SHELL_L)
    c.px(x - rad * 0.4, y - rad * 0.75, P.LEAF_Y)


def snail_cat_frame(stretch: float = 0, head: float = 1.0, eyes: str = "open", mouth: str = "w", peek: int = -1,
                    shell_drop: float = 0) -> Image.Image:
    """head: 1 = out, 0 = hidden; peek >= 0 shows eyes in the shell mouth (hidden, peeking)."""
    size, cx, gy = (32, 20), 15, 18
    c = Canvas(*size)
    sx, sy, srad = cx - 4, gy - 7 + shell_drop, 6
    if head > 0:
        front = cx + 8 + stretch
        with shaded(c, GINGER_RAMP, EDGE) as p:                              # low slug body along the ground
            p.ellipse(cx - 1 + stretch * 0.5, gy - 2, 9 + stretch * 0.5, 2.5, P.GINGER)
            p.rect(cx - 9, gy - 1, front, gy, P.GINGER)
            p.poly([(cx - 9, gy - 1), (cx - 11 - stretch * 0.3, gy), (cx - 9, gy)], P.GINGER)   # tail tip
        c.rect(cx - 6, gy, front - 1, gy, P.CREAM_D)                          # cream foot
        snail_shell(c, sx, sy, srad, turn=stretch * 0.2)
        hx, hy = front - 1.5 + (1 - head) * -5, gy - 5 + (1 - head) * 2
        with shaded(c, GINGER_RAMP, EDGE) as p:
            ear(p, hx - 2.5, hy - 3, 3.5 * head, P.GINGER, inner=P.PINK, lean=-0.5, half=2)
            ear(p, hx + 2.5, hy - 3, 3.5 * head, P.GINGER, inner=P.PINK, lean=0.5, half=2)
            p.ellipse(hx, hy, 4.5 * (0.6 + head * 0.4), 3.8 * (0.6 + head * 0.4), P.GINGER)
        c.ellipse(hx + 0.5, hy + 2.2, 2.2 * head, 1.0 * head, P.CREAM)
        face(c, hx + 1.5, hy - 1, eyes=eyes, mouth=mouth, gap=3)
    if head <= 0:
        snail_shell(c, sx, sy, srad + 0.5)
        with shaded(c, GINGER_RAMP, EDGE) as p:                              # a sliver of body under the shell
            p.rect(sx - 6, gy - 1, sx + 8, gy, P.GINGER)
        if peek >= 0:                                                         # eyes peering out from under it
            c.ellipse(sx + 5, gy - 2, 2.8, 1.6, P.OUTLINE)
            c.px(sx + 4 + peek, gy - 2, P.YELLOW)
            c.px(sx + 6 + peek, gy - 2, P.YELLOW)
    return c.outline(EDGE).img


def snail_cat() -> Sprite:
    sprite = Sprite("snail_cat", (32, 20), faces_left=True, cx=15, ground=18)
    sprite.add("walk", [snail_cat_frame(s) for s in (0, 1, 2, 1)], fps=6)
    sprite.add("hide", [snail_cat_frame(0, 0.6, eyes="shut", mouth="flat"), snail_cat_frame(0, 0.25, eyes="shut", mouth=None),
                        snail_cat_frame(0, 0)], fps=10, loop=False)
    sprite.add("shell", [snail_cat_frame(0, 0, peek=0), snail_cat_frame(0, 0, peek=1)], fps=3)
    dead = snail_cat_frame(0, 1, eyes="x", mouth="open")
    frames = [tint(dead, P.WHITE, 0.6)] + [vanish(dead, t, depth=5, flash=False) for t in (0.35, 0.65, 0.95)]
    sprite.add("death", frames, fps=10, loop=False)
    return sprite


# --- spider cat [14x12] ----------------------------------------------------------------------------

SPIDER_RAMP = ramp((P.SPIDER_L, P.SPIDER, P.SPIDER_D))


def spider_legs(c: Canvas, cx: float, y: float, mode: str, step: int, side_only: int, floor: float = 99) -> None:
    """Four long legs on one side (`side_only` -1 = back/far, 1 = front/near), two segments each."""
    side = side_only
    for i in range(4):
        root = (cx - 1 + side * 2, y - 6 + i * 0.7)
        if mode == "walk":
            lift = 1.5 if (i + step + (side > 0)) % 2 else 0
            knee = (root[0] + side * (5 + i * 0.9), root[1] - 3 - lift)
            foot = (knee[0] + side * 2.5, y - lift * 0.5)
        elif mode == "hang":
            knee = (root[0] + side * (5 + i * 0.9), root[1] - 1 + i * 0.8 + step * 0.5)
            foot = (knee[0] + side * 0.5, knee[1] + 4 - step * 0.5)
        else:                                                                 # drop: legs flung up
            knee = (root[0] + side * (5 + i * 0.9), root[1] - 3 - step)
            foot = (knee[0] + side * 2, knee[1] - 3 + i * 0.8)
        foot = (foot[0], min(foot[1], floor))
        colour = (P.VIOLET if i % 2 == 0 else P.PURPLE_L) if side > 0 else (P.PURPLE if i % 2 == 0 else P.VIOLET)
        c.line(root, knee, colour, 1)
        c.line(knee, foot, colour, 1)
        c.px(foot[0], foot[1], P.PINK)


def spider_cat_frame(mode: str, step: int = 0, eyes: str = "glow", mouth: str = "fangs", thread: bool = True) -> Image.Image:
    size, cx, gy = (32, 44), 16, 41
    y = gy - (1 if mode == "walk" and step % 2 else 0) - (2 if mode != "walk" else 0)
    c = Canvas(*size)
    if mode != "walk" and thread:
        top_y = y - 13
        c.line((cx + 1, 0), (cx + 1, top_y), P.GREY_L)
        for ty in range(3, int(top_y), 6):                                   # a glint running down the silk
            c.px(cx + 1, ty, P.WHITE)
    legs = Canvas(*size)
    spider_legs(legs, cx, y, mode, step, -1, gy - 0.6)
    spider_legs(legs, cx + 1, y, mode, step + 1, 1, gy - 0.6)
    legs.outline(EDGE)
    c.paste(legs)
    with shaded(c, SPIDER_RAMP, EDGE) as p:
        p.ellipse(cx - 3, y - 5, 5, 4.5, P.SPIDER)                            # round abdomen
    c.px(cx - 5, y - 7, P.VIOLET)
    c.px(cx - 4, y - 8, P.VIOLET)
    with shaded(c, SPIDER_RAMP, EDGE) as p:
        ear(p, cx - 1, y - 10, 4, P.SPIDER, inner=None, lean=-0.5, half=2)
        ear(p, cx + 5, y - 10, 4, P.SPIDER, inner=None, lean=0.5, half=2)
        p.ellipse(cx + 2, y - 6, 5.5, 4.8, P.SPIDER)                          # big cat head
    c.px(cx - 1, y - 12, P.VIOLET)
    c.px(cx + 5, y - 12, P.VIOLET)
    c.ellipse(cx + 2.5, y - 4, 2.5, 1.1, P.BATWING_L)                          # pale muzzle
    face(c, cx + 4, y - 8, eyes=eyes, mouth=mouth, gap=4, eye=P.YELLOW, nose=P.PINK_D, blush=None)
    if eyes == "glow":
        c.px(cx + 4, y - 7, P.OUTLINE)                                        # slit pupils
        c.px(cx, y - 7, P.OUTLINE)
    return c.outline(EDGE).img


def spider_cat() -> Sprite:
    sprite = Sprite("spider_cat", (32, 44), faces_left=True, cx=16, ground=41)
    sprite.add("hang", [spider_cat_frame("hang", 0), spider_cat_frame("hang", 1)], fps=3)
    sprite.add("drop", [spider_cat_frame("drop", 0, eyes="wide", mouth="open"),
                        spider_cat_frame("drop", 1, eyes="wide", mouth="open")], fps=8)
    sprite.add("walk", [spider_cat_frame("walk", k) for k in range(4)], fps=10)
    dead = spider_cat_frame("walk", 0, eyes="x", mouth="open")
    frames = [tint(dead, P.WHITE, 0.6)] + [vanish(dead, t, depth=4, flash=False) for t in (0.35, 0.65, 0.95)]
    sprite.add("death", frames, fps=10, loop=False)
    return sprite


def build() -> list[Sprite]:
    return [slime(), mushroom_cat(), spore(), forest_bat(), plant_cat(), bee_cat(), sting(), stump_cat(), leaf(),
            snail_cat(), spider_cat()]
