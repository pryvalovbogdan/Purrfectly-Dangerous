"""World 1, the Purrwood forest critters (from the forest enemy atlas in docs/concept/): the cat slime,
mushroom cat, forest bat, plant cat, bee cat, stump cat, snail cat and spider cat, and the spores,
stings and leaves they throw. Drawn facing right with light from the top-left; mirrored on export.

Gameplay hitboxes (w x h, anchored at the feet) are noted on each sprite; the body covers them. Every
body part gets a light rim along its top edge (`shaded`) and the figure a dark 1px outline, so the
critters stand out against the green forest."""
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


def dying(still: Image.Image, depth: float) -> list[Image.Image]:
    """Death: a white flash, then it sinks by `depth` while fading out."""
    return [tint(still, P.WHITE, 0.6)] + [vanish(still, t, depth=depth, flash=False) for t in (0.35, 0.65, 0.95)]


# --- slime [20x14] -------------------------------------------------------------------------------

SLIME_RAMP = ramp((P.SLIME_L, P.SLIME, P.SLIME_D))


def slime_body(c: Canvas, cx: float, gy: float, sx: float = 1.0, sy: float = 1.0, eyes: str = "open",
               mouth: str = "smile") -> None:
    """A glossy lime blob with cat ears, base on `gy`; `sx`/`sy` squash and stretch it."""
    height = 15 * sy                     # a dome: an ellipse cut flat at the ground, widest at the base
    ry = height * 0.72
    rx = 10.2 * sx / 0.92
    ey = gy - height + ry
    top = gy - height + 1
    with shaded(c, SLIME_RAMP, up=2, down=1) as p:
        ear(p, cx - 5 * sx, top + 3.5, 7, P.SLIME, inner=None, lean=-1.5, half=3.8)
        ear(p, cx + 5.5 * sx, top + 3.5, 7, P.SLIME, inner=None, lean=1.5, half=3.8)
        p.ellipse(cx, ey, rx, ry, P.SLIME)
        p.rect(0, gy + 1, p.size[0], p.size[1], P.CLEAR)
    for ex, lean in ((cx - 5 * sx, -1), (cx + 5.5 * sx, 1)):                    # inner ears
        c.poly([(ex - 1.2, top + 2), (ex + lean * 1.5, top - 1.5), (ex + 1.2, top + 2)], P.SLIME_D)
    for x in range(int(cx - rx * 0.86), int(cx + rx * 0.86) + 1):             # the wet rim it slides on
        c.px(x, gy, P.SLIME_RIM)
    c.rect(cx - rx * 0.8, gy - 1, cx - rx * 0.8 + 1, gy - 1, P.SLIME_RIM)
    c.rect(cx - 7 * sx, top + 4, cx - 7 * sx + 1, top + 6, P.WHITE)             # gloss
    c.px(cx - 5 * sx, top + 4, P.WHITE)
    c.px(cx - 8 * sx, top + 8, P.SLIME_L)
    for bx, by in ((6, -3), (4, -2), (8, -5)):                                   # bubbles inside
        c.px(cx + bx * sx, gy + by, P.SLIME_L)
    face(c, cx + 2, gy - 9 * sy, eyes=eyes, mouth=mouth, gap=6, nose=None, blush=P.GOLD, size=3)


def slime() -> Sprite:
    size, cx, gy = (30, 24), 15, 22
    sprite = Sprite("slime", size, faces_left=True, cx=cx, ground=gy)
    squash = ((1.1, 0.86, "w"), (1.0, 1.0, "smile"), (0.9, 1.14, "open"), (1.0, 1.0, "smile"))
    sprite.add("walk", [framed(size, lambda c, s=s: slime_body(c, cx, gy, s[0], s[1], mouth=s[2]))
                        for s in squash], fps=8)

    def melt(t: float):
        def draw(c):
            slime_body(c, cx, gy, 1.0 + t * 0.12, max(0.35, 1.0 - t * 0.75), eyes="x", mouth="flat")
            if t > 0:
                for dx, dy in ((-8, -12), (6, -14), (-1, -17)):
                    sparkle(c, cx + dx, gy + dy + 3 - t * 2, P.SLIME_L)
        return draw

    frames = [tint(framed(size, melt(0)), P.WHITE, 0.6)] + [framed(size, melt(t)) for t in (0.4, 0.75, 1.0)]
    frames[2] = see_through(frames[2], 180)
    frames[3] = see_through(frames[3], 80)
    sprite.add("death", frames, fps=10, loop=False)
    return sprite


# --- mushroom cat [18x22] + spore ----------------------------------------------------------------

CAP_RAMP = ramp((P.CAPE_L, P.RED, P.CAPE_D))
CREAM_RAMP = ramp((P.FUR_WHITE, P.CREAM, P.CREAM_D))


def mushroom_cap(c: Canvas, x: float, y: float, w: float = 13, h: float = 8.5, tilt: float = 0) -> None:
    """A red cap with white spots; (x, y) is the centre of its underside."""
    for xx in range(int(x - w + 4), int(x + w - 3)):                            # its shadow on the face
        if c.img.getpixel((xx, int(y + 2)))[3]:
            c.px(xx, y + 2, P.CREAM_D)
    with shaded(c, CAP_RAMP, up=2, down=2) as p:
        p.ellipse(x + tilt * 0.5, y - h + 0.5, w, h, P.RED)
    c.rect(x - w + 3, y, x + w - 3, y, P.CREAM_D)                               # gills on the underside
    c.rect(x - w + 4, y + 1, x + w - 4, y + 1, P.SAND)
    for gx in range(int(x - w + 5), int(x + w - 4), 3):
        c.px(gx, y + 1, P.CREAM_D)
    for sx, sy, sr in ((-7, -7.5, 2.2), (1.5, -11.5, 1.9), (8, -6, 2.1), (-1.5, -4, 1.4), (-10.5, -3, 1.0),
                       (5, -13, 0.9), (-4, -12.5, 1.0), (11, -2.5, 0.8)):
        if sr >= 1:
            c.ellipse(x + sx + tilt * 0.3, y + sy, sr, sr * 0.9, P.WHITE)
            c.px(x + sx + tilt * 0.3 + sr * 0.5, y + sy + sr * 0.6, P.PALE)     # spot shading
        else:
            c.px(x + sx + tilt * 0.3, y + sy, P.WHITE)


def mushroom_cat_frame(bob: float = 0, squat: float = 0, cap_lift: float = 0, tilt: float = 0, eyes: str = "open",
                       mouth: str = "w", step: int = 0, puff: float = 0) -> Image.Image:
    """A round little cream cat wearing a big red toadstool cap."""
    size, cx, gy = (34, 34), 17, 32
    c = Canvas(*size)
    ry = 7.5 - squat * 0.5
    tail = [(cx - 7, gy - 2), (cx - 11, gy - 3), (cx - 14, gy - 5), (cx - 15, gy - 8 - bob), (cx - 14, gy - 10 - bob)]
    with shaded(c, CREAM_RAMP) as p:                                            # thin curling tail
        for a, b in zip(tail, tail[1:]):
            p.line(a, b, P.CREAM, 2)
    with shaded(c, CREAM_RAMP, up=2) as p:
        p.ellipse(cx, gy - ry + 0.5, 9.5, ry, P.CREAM)                           # round body
    lift = step % 2                                                             # round feet
    c.ellipse(cx - 4, gy - 1 - lift, 2.6, 1.4, P.CREAM_D)
    c.ellipse(cx + 4, gy - 1, 2.6, 1.4, P.CREAM_D)
    c.rect(cx - 0.5, gy - 1, cx - 0.5, gy, EDGE)
    c.ellipse(cx + 7, gy - 4.5, 1.6, 1.4, P.CREAM_D)                            # near paw
    c.px(cx + 6, gy - 5, P.CREAM)
    c.ellipse(cx + 1, gy - 3.5, 3, 2, P.FUR_WHITE)                               # pale tummy
    cap_y = gy - 2 * ry + 3 - cap_lift + bob
    face(c, cx + 2, cap_y + 4, eyes=eyes, mouth=mouth, gap=5, size=3)
    mushroom_cap(c, cx, cap_y, tilt=tilt)
    if puff:
        for dx, dy, rad in ((10.5, -8, 2.3), (12, -4.5, 1.4), (12, -11.5, 1.2)):
            c.ellipse(cx + dx * puff, gy + dy, rad, rad, P.YARN_L)
            c.px(cx + dx * puff - 0.5, gy + dy - 0.5, P.WHITE)
        sparkle(c, cx + 12, gy - 15, P.PINK)
    return c.outline(EDGE).img


def mushroom_cat() -> Sprite:
    sprite = Sprite("mushroom_cat", (34, 34), faces_left=True, cx=17, ground=32)
    sprite.add("idle", [mushroom_cat_frame(0), mushroom_cat_frame(1, step=1)], fps=3)
    sprite.add("throw", [mushroom_cat_frame(squat=1, tilt=-2, eyes="shut", mouth="flat"),
                         mushroom_cat_frame(squat=2, tilt=-3, eyes="shut", mouth="flat"),
                         mushroom_cat_frame(cap_lift=2, tilt=2, eyes="open", mouth="open", puff=1.0),
                         mushroom_cat_frame(cap_lift=1, eyes="open", mouth="w")], fps=8, loop=False)
    sprite.add("death", dying(mushroom_cat_frame(squat=2, eyes="x", mouth="flat"), 8), fps=10, loop=False)
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


# --- forest bat [18x14] ---------------------------------------------------------------------------

BAT_RAMP = ramp((P.PLANK_L, P.PLANK, P.PLANK_D))
WING_RAMP = ramp((P.BATWING_L, P.BATWING, P.BATWING_D))


def bat_wing(c: Canvas, root: tuple[float, float], side: int, flap: float, far: bool) -> None:
    """A scalloped membrane wing; side +1 spreads right, -1 left; flap 1 = raised, -1 = lowered."""
    rx, ry = root
    span = 18 if not far else 16
    tip = (rx + side * span, ry - 4 - flap * 7)
    elbow = (rx + side * span * 0.45, ry - 5 - flap * 5)
    low = ry + 3 - flap * 2
    pts = [root, elbow, tip]
    fingers = []
    for k, t in enumerate((0.82, 0.64, 0.44, 0.24)):                            # scalloped trailing edge
        x = rx + side * span * t
        y = tip[1] + (low - tip[1]) * (1 - t) + 2
        if k % 2 == 0:
            pts.append((x, y + 3.5))
        else:
            pts.append((x, y))
            fingers.append((x, y))
    pts.append((rx, ry + 4))
    with shaded(c, WING_RAMP, EDGE, up=1, down=1) as p:
        p.poly(pts, P.BATWING_D if far else P.BATWING)
    with shaded(c, WING_RAMP) as p:                                            # the arm along the top
        p.line(root, elbow, P.BATWING_D, 2)
        p.line(elbow, tip, P.BATWING_D, 1)
    for f in fingers:                                                           # finger bones
        c.line(elbow, f, P.BATWING_D)
    c.px(tip[0], tip[1], P.BATWING_L)
    c.px(elbow[0], elbow[1] - 1, P.BATWING_L)


def forest_bat_frame(flap: float, eyes: str = "open", mouth: str = "fangs", bob: float = 0) -> Image.Image:
    size, cx, gy = (46, 32), 23, 25
    c = Canvas(*size)
    y = gy + bob
    bat_wing(c, (cx - 3, y - 10), -1, flap, far=False)
    bat_wing(c, (cx + 3, y - 10), 1, flap * 0.85, far=True)
    with shaded(c, BAT_RAMP, EDGE, up=2) as p:
        p.ellipse(cx - 1, y - 5, 5.5, 5, P.PLANK)                               # body
    with shaded(c, BAT_RAMP, EDGE) as p:                                        # little feet dangling
        p.rect(cx - 4, y - 1, cx - 2, y, P.PLANK)
        p.rect(cx + 1, y - 1, cx + 3, y, P.PLANK)
    c.ellipse(cx, y - 4.5, 2.5, 3, P.PLANK_L)                                   # chest
    with shaded(c, BAT_RAMP, EDGE, up=2) as p:
        ear(p, cx - 3.5, y - 15, 6, P.PLANK, inner=P.PINK_D, lean=-1, half=3)
        ear(p, cx + 5.5, y - 15, 6, P.PLANK, inner=P.PINK_D, lean=1, half=3)
        p.ellipse(cx + 1, y - 11, 7.5, 6.2, P.PLANK)                           # big round head
    c.px(cx - 4.5, y - 20, P.PLANK_L)                                           # ear tufts
    c.px(cx + 6.5, y - 20, P.PLANK_L)
    c.ellipse(cx + 2, y - 7.5, 3.5, 1.6, P.PLANK_L)                             # muzzle
    face(c, cx + 3, y - 12.5, eyes=eyes, mouth=mouth, gap=6, nose=P.BARK_DD, size=3)
    return c.outline(EDGE).img


def forest_bat() -> Sprite:
    sprite = Sprite("forest_bat", (46, 32), faces_left=True, cx=23, ground=25)
    sprite.add("fly", [forest_bat_frame(f, bob=b) for f, b in ((1, 0), (0.2, 0), (-0.9, -1), (0.2, -1))], fps=12)
    dead = forest_bat_frame(-0.5, eyes="x", mouth="open")
    sprite.add("death", [tint(dead, P.WHITE, 0.6), vanish(dead, 0.45, depth=8, flash=False),
                         vanish(dead, 0.9, depth=8, flash=False)], fps=10, loop=False)
    return sprite


# --- plant cat [18x30] -----------------------------------------------------------------------------

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


def leaf_with_vein(c: Canvas, base, angle: float, length: float, width: float) -> None:
    with shaded(c, LEAF_RAMP, EDGE, up=2) as p:
        leaf_shape(p, base, angle, length, width, P.KIT_GREEN)
    a = math.radians(angle)
    c.line((base[0] + math.cos(a) * 1.5, base[1] - math.sin(a) * 1.5),
           (base[0] + math.cos(a) * length * 0.75, base[1] - math.sin(a) * length * 0.75), P.KIT_GREEN_D)


def plant_stem(c: Canvas, cx: float, gy: float, sway: float, droop: float = 0) -> tuple[float, float]:
    """A tall curving stem with two pairs of leaves and a tuft at the foot; returns the top of the stem."""
    top = (cx + sway, gy - 17 + droop)
    low = (cx - 1 + sway * 0.2, gy - 6)
    mid = (cx + 0.5 + sway * 0.6, gy - 12 + droop * 0.5)
    with shaded(c, LEAF_RAMP, EDGE) as p:
        p.line((cx, gy), low, P.KIT_GREEN, 3)
        p.line(low, mid, P.KIT_GREEN, 3)
        p.line(mid, top, P.KIT_GREEN, 2)
    for ang, ln in ((150, 6), (25, 5), (100, 4)):                               # tuft at the foot
        leaf_with_vein(c, (cx, gy), ang, ln, 1.6)
    leaf_with_vein(c, (low[0] - 0.5, low[1]), 150 + droop * 12, 12, 3.6)       # big lower pair
    leaf_with_vein(c, (low[0] + 1, low[1]), 30 - droop * 12, 12, 3.6)
    leaf_with_vein(c, (mid[0] - 0.5, mid[1]), 140 + droop * 10, 8, 2.6)         # smaller upper pair
    leaf_with_vein(c, (mid[0] + 1, mid[1]), 40 - droop * 10, 8, 2.6)
    c.rect(cx - 4, gy, cx + 4, gy, P.KIT_GREEN_DD)                              # roots in the soil
    return top


def plant_spots(c: Canvas, x: float, y: float) -> None:
    for dx, dy in ((-5, -2), (-2, -5), (-3, 1), (2, -6), (-6, 2)):
        c.px(x + dx, y + dy, P.PINK)
        c.px(x + dx + 1, y + dy, P.PINK)


def plant_cat_frame(mode: str, k: int = 0) -> Image.Image:
    """mode: bud (closed), open (opening by k = 0, 1), bite (k = 0 wide, 1 snap, 2 recover), dead (k = 0...3)."""
    size, cx, gy = (40, 42), 18, 40
    c = Canvas(*size)
    sway = (0, 1)[k % 2] if mode == "bud" else (1 if mode == "open" else 0)
    lunge = {"bite": (3, 5, 1)}.get(mode, (0, 0, 0))[min(k, 2)]
    droop = k * 1.5 if mode == "dead" else 0
    top = plant_stem(c, cx, gy, sway + lunge * 0.6, droop)
    hx, hy = top[0] + 1 + lunge + droop, top[1] - 7 + droop
    if mode == "bud":
        with shaded(c, HEAD_RAMP, EDGE, up=2) as p:
            ear(p, hx - 4, hy - 6, 4, P.RED, inner=None, lean=-0.6, half=2.4)
            ear(p, hx + 4, hy - 6, 4, P.RED, inner=None, lean=0.6, half=2.4)
            p.ellipse(hx, hy, 7, 7.5, P.RED)
            p.poly([(hx - 3, hy - 7), (hx, hy - 11), (hx + 3, hy - 7)], P.RED)
        for a, b in (((hx, hy - 9), (hx - 3, hy + 5)), ((hx + 4, hy - 5), (hx + 2, hy + 5)),
                     ((hx - 4, hy - 4), (hx - 6, hy + 3))):                     # folded petals
            c.line(a, b, P.CAPE_D)
        for dx, dy in ((-4, -1), (2, -4), (-1, 3), (4, 1)):
            c.px(hx + dx, hy + dy, P.PINK)
        for side in (-1, 1):                                                    # green sepals cupping the bud
            leaf_with_vein(c, (hx, hy + 7), 90 + side * 55, 7, 2.2)
        with shaded(c, LEAF_RAMP, EDGE) as p:
            p.ellipse(hx, hy + 7, 3.5, 1.6, P.KIT_GREEN)
        return c.outline(EDGE).img
    # An open head: a round red cat head with a wedge of mouth cut in from the front.
    gape = {"open": (1.5, 4), "bite": (7.5, 0.8, 4), "dead": (2, 2, 2, 2)}[mode][k]
    rad = 8 + min(gape, 5) * 0.3
    for side in (-1, 1):                                                        # leafy collar under the head
        leaf_with_vein(c, (hx - 1, hy + 6), 90 + side * 72, 7, 2.4)
    with shaded(c, HEAD_RAMP, EDGE, up=2) as p:
        ear(p, hx - 5, hy - rad + 3, 5.5, P.RED, inner=P.CAPE_D, lean=-1, half=3)
        ear(p, hx + 3, hy - rad + 2, 5.5, P.RED, inner=P.CAPE_D, lean=0.8, half=3)
        p.ellipse(hx, hy, rad + 0.5, rad, P.RED)
    hinge = (hx - 3, hy + 1.5)
    front = hx + rad + 3
    up, down = (hy + 1.5 - gape * 1.1, hy + 1.5 + gape * 0.9)
    plant_spots(c, hx - 1, hy - 1)
    if gape >= 1:
        c.poly([hinge, (front, up), (front, down)], P.CLEAR)                    # cut the mouth out...
        mouth = Canvas(*size)
        mouth.poly([hinge, (front - 1, up + 0.5), (front - 1, down - 0.5)], P.MAROON)   # ...and fill it in dark
        if gape > 2:
            mouth.ellipse(hinge[0] + (front - hinge[0]) * 0.55, down - 2, 3.5, 1.4, P.PINK_D)   # tongue
            mouth.px(hinge[0] + (front - hinge[0]) * 0.45, down - 2.5, P.PINK)
        c.paste(mouth)
        n = int((front - hinge[0]) // 2.5)
        for i in range(1, n + 1):                                               # pointed teeth on both lips
            t = i * 2.5 / (front - hinge[0])
            ux, uy = hinge[0] + (front - 1 - hinge[0]) * t, hinge[1] + (up + 1 - hinge[1]) * t
            c.px(ux, uy, P.WHITE)
            if gape > 2.5:
                c.px(ux, uy + 1, P.WHITE)
                lx, ly = hinge[0] + (front - 1 - hinge[0]) * t - 1, hinge[1] + (down - 1 - hinge[1]) * t
                c.px(lx, ly, P.WHITE)
                c.px(lx, ly - 1, P.WHITE)
    eyes = "x" if mode == "dead" else ("angry" if mode == "bite" else "open")
    face(c, hx + 2, hy - 5 - (1 if gape > 4 else 0), eyes=eyes, mouth=None, gap=5, nose=None, blush=None, size=3)
    return c.outline(EDGE).img


def plant_cat() -> Sprite:
    sprite = Sprite("plant_cat", (40, 42), faces_left=True, cx=18, ground=40)
    sprite.add("idle", [plant_cat_frame("bud", 0), plant_cat_frame("bud", 1)], fps=3)
    sprite.add("warn", [plant_cat_frame("open", 0), plant_cat_frame("open", 1)], fps=6)
    sprite.add("bite", [plant_cat_frame("bite", k) for k in range(3)], fps=10, loop=False)
    frames = [tint(plant_cat_frame("dead", 0), P.WHITE, 0.6)]
    frames += [plant_cat_frame("dead", 1), see_through(plant_cat_frame("dead", 2), 170),
               see_through(plant_cat_frame("dead", 3), 80)]
    sprite.add("death", frames, fps=8, loop=False)
    return sprite


# --- bee cat [18x16] + sting ---------------------------------------------------------------------

BEE_RAMP = ramp((P.YELLOW, P.GOLD, P.GOLD_D), (P.GREY_D, P.SLATE, P.BLACK))


def bee_wings(size, root: tuple[float, float], flap: float) -> Image.Image:
    """Two big translucent blue wings rising from the back, veined; flap 1 = up, -1 = swept back."""
    c = Canvas(*size)
    rx, ry = root
    for dx, scale, colour in ((-3.5, 0.82, P.BLUE), (0.5, 1.0, P.BLUE_L)):
        cx_, cy_ = rx + dx - (1 - flap) * 1.8, ry - 6 - flap * 2
        wx, wy = (4.4 + (1 - flap) * 0.8) * scale, (6.4 - (1 - flap) * 1.0) * scale
        c.ellipse(cx_, cy_, wx, wy, colour)
        c.line((rx + dx * 0.3, ry), (cx_ - wx * 0.2, cy_ - wy * 0.6), P.BLUE)   # vein
        c.px(cx_ - wx * 0.4, cy_ - wy * 0.5, P.WHITE)
        c.px(cx_ - wx * 0.4 + 1, cy_ - wy * 0.5 - 1, P.WHITE)
    c.outline(P.BLUE_D)
    return see_through(c.img, 200)


def bee_cat_frame(flap: float, bob: float = 0, sting: float = 0, eyes: str = "open", mouth: str = "w",
                  wings: bool = True) -> Image.Image:
    """sting: 0 = rest, -1 = abdomen cocked back, 1 = curled under with the stinger thrust forward."""
    size, cx, gy = (38, 30), 19, 26
    y = gy + bob
    c = Canvas(*size)
    ax, ay = cx - 4 + max(0, sting) * 2, y - 6 - max(0, -sting) * 2 + max(0, sting) * 0.5
    if sting > 0.5:
        base, tip = (ax + 2, ay + 4), (ax + 7, y - 1)
    else:
        base, tip = (ax - 6, ay + 1), (ax - 10, ay + 2.5 - sting * 2.5)
    c.line(base, tip, P.SLATE, 2)                                              # stinger
    c.px(tip[0], tip[1], P.GREY_L)
    with shaded(c, BEE_RAMP, EDGE, up=2) as p:
        p.ellipse(ax, ay, 7, 5.8, P.GOLD)                                       # striped abdomen
    for sx in (-4.5, -0.5, 3.5):
        for yy in range(int(ay - 7), int(ay + 7)):
            for xx in (ax + sx, ax + sx + 1):
                col = c.img.getpixel((round(xx), yy))[:3]
                if col in (P.GOLD[:3], P.YELLOW[:3]):
                    c.px(xx, yy, P.SLATE if col == P.GOLD[:3] else P.GREY_D)
                elif col == P.GOLD_D[:3]:
                    c.px(xx, yy, P.BLACK)
    with shaded(c, BEE_RAMP, EDGE) as p:                                        # dangling legs
        for lx in (ax - 3, ax + 1, ax + 5):
            p.rect(lx, y - 1.5, lx + 1, y, P.SLATE)
    if wings:
        c.paste(bee_wings(size, (ax + 1, ay - 3 + max(0, -sting) * 2), flap))
    with shaded(c, BEE_RAMP, EDGE, up=2) as p:
        ear(p, cx + 0.5, y - 16, 5, P.GOLD, inner=P.ORANGE, lean=-0.8, half=2.8)
        ear(p, cx + 8.5, y - 16, 5, P.GOLD, inner=P.ORANGE, lean=0.8, half=2.8)
        p.ellipse(cx + 4.5, y - 11, 7.2, 6, P.GOLD)                             # big round head
    c.ellipse(cx + 6, y - 7.5, 3.5, 1.6, P.YELLOW)                             # muzzle
    for dx in (-1, 1):                                                          # little antennae
        c.line((cx + 4 + dx * 2, y - 17), (cx + 4 + dx * 3.5, y - 20), P.SLATE)
        c.px(cx + 4 + dx * 3.5, y - 20.5, P.GOLD)
    face(c, cx + 6, y - 13, eyes=eyes, mouth=mouth, gap=5, nose=P.ORANGE, size=3)
    if sting > 0.5:
        sparkle(c, tip[0] + 2, tip[1] - 2, P.YELLOW, big=True)
    return c.outline(EDGE).img


def bee_cat() -> Sprite:
    sprite = Sprite("bee_cat", (38, 30), faces_left=True, cx=19, ground=26)
    sprite.add("fly", [bee_cat_frame(f, b) for f, b in ((1, 0), (0, 0), (-1, -1), (0, -1))], fps=14)
    sprite.add("throw", [bee_cat_frame(1, 0, -1, eyes="angry", mouth="flat"),
                         bee_cat_frame(-1, 0, 1, eyes="angry", mouth="fangs"),
                         bee_cat_frame(0, 0, 0.3, mouth="w")], fps=10, loop=False)
    dead = bee_cat_frame(-1, 0, 0, eyes="x", mouth="open")
    frames = [tint(dead, P.WHITE, 0.6)]
    for t in (0.35, 0.65, 0.95):
        frames.append(vanish(bee_cat_frame(-1, 0, 0, eyes="x", mouth="open", wings=t < 0.5), t, depth=9, flash=False))
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


# --- stump cat [20x28] + leaf ----------------------------------------------------------------------

BARK_RAMP = ramp((P.BARK_L, P.BARK, P.BARK_D), (P.PLANK_L, P.PLANK, P.PLANK_D))


def stump_cat_frame(squash: float = 0, eyes: str = "glow", mouth: str = "shut", sway: int = 0, shine: int = 0) -> Image.Image:
    size, cx, gy = (34, 38), 17, 36
    c = Canvas(*size)
    top = gy - 26 + squash
    with shaded(c, BARK_RAMP, EDGE, up=2, down=1, right=2) as p:
        p.poly([(cx - 13, gy), (cx - 10.5, gy - 4), (cx - 10, top + 1), (cx + 10, top + 1), (cx + 10.5, gy - 4),
                (cx + 13, gy)], P.BARK)                                         # trunk with flared roots
        ear(p, cx - 7, top + 1.5, 5.5, P.BARK, inner=None, lean=-0.8, half=3.2)
        ear(p, cx + 7, top + 1.5, 5.5, P.BARK, inner=None, lean=0.8, half=3.2)
    for ex in (cx - 7, cx + 7):                                                 # inner ears
        c.line((ex, top - 2), (ex, top), P.BARK_DD)
    for x, t in ((cx - 7, 6), (cx - 3, 10), (cx + 1, 15), (cx + 5, 7), (cx + 8, 4)):   # bark grooves
        c.line((x, top + t), (x + (1 if x % 2 else -1) * 0.6, gy - 3), P.BARK_D)
    c.line((cx - 9, top + 4), (cx - 9, top + 12), P.BARK_L)
    c.line((cx - 12, gy - 1), (cx - 9.5, gy - 4), P.BARK_L)                     # roots
    c.line((cx + 11, gy - 1), (cx + 9.5, gy - 4), P.BARK_DD)
    for rx_ in (cx - 4, cx + 3):
        c.line((rx_, gy), (rx_, gy - 2), P.BARK_D)
    with shaded(c, BARK_RAMP) as p:                                             # cut top with rings
        p.ellipse(cx, top + 2, 10, 2.8, P.PLANK)
    c.ellipse(cx, top + 2, 7, 1.8, P.PLANK_L)
    c.ellipse(cx, top + 2, 4, 1, P.PLANK)
    c.rect(cx - 1, top + 2, cx + 1, top + 2, P.PLANK_D)
    with shaded(c, LEAF_RAMP, EDGE, up=2) as p:                                 # sprouting leaves
        p.line((cx - 4, top + 2), (cx - 4, top - 3), P.KIT_GREEN)
        leaf_shape(p, (cx - 4, top - 3), 135 + sway * 8, 7, 2.6, P.KIT_GREEN)
        leaf_shape(p, (cx - 4, top - 3), 55 + sway * 8, 6, 2.2, P.KIT_GREEN)
        leaf_shape(p, (cx + 9, top + 3), 35 - sway * 6, 4.5, 1.7, P.KIT_GREEN)
    with shaded(c, LEAF_RAMP) as p:                                             # moss on the bark
        p.ellipse(cx - 9, gy - 7, 2, 1.5, P.KIT_GREEN)
        p.ellipse(cx + 8, gy - 3, 2.5, 1.5, P.KIT_GREEN)
    ey = top + 9                                                                # hollow eyes with a green glow
    for ex in (cx - 6, cx + 3):
        c.ellipse(ex + 1, ey + 1, 2.6, 2.6, P.BARK_DD)
        if eyes == "glow":
            c.rect(ex, ey, ex + 2, ey + 2, P.LEAF_Y)
            c.px(ex + (2 if shine else 0), ey, P.WHITE)
            c.px(ex + 1, ey + 2, P.KIT_GREEN_L)
        elif eyes == "angry":
            c.rect(ex, ey + 1, ex + 2, ey + 2, P.LEAF_Y)
        elif eyes == "x":
            for dx, dy in ((0, 0), (2, 0), (1, 1), (0, 2), (2, 2)):
                c.px(ex + dx, ey + dy, P.LEAF_Y)
    my = ey + 7
    if mouth == "shut":
        c.rect(cx - 2, my, cx + 2, my, P.BARK_DD)
        c.px(cx - 3, my - 1, P.BARK_DD)
        c.px(cx + 3, my - 1, P.BARK_DD)
    else:
        c.ellipse(cx, my + 0.5, 2.5, 2.5, P.BARK_DD)
        c.px(cx, my + 1, P.KIT_GREEN)
        c.px(cx + 1, my, P.KIT_GREEN_L)
    c.ellipse(cx - 8, ey + 4, 1, 1, P.BARK_D)                                   # cheek knots
    c.ellipse(cx + 7, ey + 4, 1, 1, P.BARK_D)
    for gx in (cx - 12, cx - 7, cx + 12):                                       # grass at the foot
        c.line((gx, gy), (gx - 1, gy - 3), P.KIT_GREEN)
        c.px(gx - 1, gy - 3, P.KIT_GREEN_L)
    return c.outline(EDGE).img


def stump_cat() -> Sprite:
    sprite = Sprite("stump_cat", (34, 38), faces_left=True, cx=17, ground=36)
    sprite.add("idle", [stump_cat_frame(0, sway=0), stump_cat_frame(0, sway=1, shine=1)], fps=3)
    sprite.add("throw", [stump_cat_frame(1, eyes="angry"), stump_cat_frame(0, mouth="open", sway=1),
                         stump_cat_frame(0, mouth="shut")], fps=8, loop=False)
    sprite.add("death", dying(stump_cat_frame(1, eyes="x", mouth="open"), 12), fps=10, loop=False)  # sinks into the soil
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


# --- snail cat [24x16] -----------------------------------------------------------------------------

SHELL_RAMP = ramp((P.SHELL_L, P.SHELL, P.SHELL_D))
GINGER_RAMP = ramp((P.GINGER_L, P.GINGER, P.GINGER_D), (P.FUR_WHITE, P.CREAM, P.CREAM_D))


def snail_shell(c: Canvas, x: float, y: float, rad: float, turn: float = 0) -> None:
    """A round green shell with a smooth spiral groove, lit along the outer side of each whorl."""
    with shaded(c, SHELL_RAMP, EDGE, up=2, down=2, right=2) as p:
        p.ellipse(x, y, rad, rad, P.SHELL)
    pts = []
    for i in range(121):
        t = i / 120
        a = turn + math.pi * 0.9 + t * math.tau * 2.2
        rr = rad * (0.86 - t * 0.8)
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr, a, rr))
    for (x0, y0, a0, r0), (x1, y1, _, _) in zip(pts, pts[1:]):              # the groove
        c.line((x0, y0), (x1, y1), P.SHELL_DD)
    for xx, yy, a, rr in pts[4:100:3]:                                       # the ridge beside it catches light
        if math.sin(a) < 0.3 and math.cos(a) < 0.5:
            c.px(x + math.cos(a) * (rr + 1.2), y + math.sin(a) * (rr + 1.2), P.SHELL_L)
    c.px(x - rad * 0.55, y - rad * 0.65, P.LEAF_Y)
    c.px(x - rad * 0.45, y - rad * 0.75, P.LEAF_Y)


def snail_cat_frame(stretch: float = 0, head: float = 1.0, eyes: str = "open", mouth: str = "w", peek: int = -1,
                    shell_drop: float = 0) -> Image.Image:
    """head: 1 = out, 0 = hidden; peek >= 0 shows eyes in the shell mouth (hidden, peeking)."""
    size, cx, gy = (40, 26), 20, 24
    c = Canvas(*size)
    sx, sy, srad = cx - 4, gy - 10 + shell_drop, 8.5
    if head > 0:
        front = cx + 11 + stretch
        with shaded(c, GINGER_RAMP, EDGE, up=2) as p:                       # low slug body along the ground
            p.ellipse(cx - 1 + stretch * 0.5, gy - 2.5, 12 + stretch * 0.5, 3.2, P.GINGER)
            p.rect(cx - 12, gy - 1, front, gy, P.GINGER)
            p.poly([(cx - 12, gy - 2), (cx - 15 - stretch * 0.3, gy), (cx - 12, gy)], P.GINGER)   # tail tip
        c.rect(cx - 9, gy, front - 1, gy, P.CREAM_D)                            # cream foot
        c.rect(cx + 2, gy - 1, front - 2, gy - 1, P.CREAM)
        snail_shell(c, sx, sy, srad, turn=stretch * 0.15)
        hx, hy = front - 2 + (1 - head) * -7, gy - 7 + (1 - head) * 3
        hs = 0.6 + head * 0.4
        with shaded(c, GINGER_RAMP, EDGE, up=2) as p:
            ear(p, hx - 3.5, hy - 4, 5 * head, P.GINGER, inner=P.PINK, lean=-0.8, half=2.8)
            ear(p, hx + 3.5, hy - 4, 5 * head, P.GINGER, inner=P.PINK, lean=0.8, half=2.8)
            p.ellipse(hx, hy, 6 * hs, 5 * hs, P.GINGER)
        c.ellipse(hx + 1, hy + 3, 3 * head, 1.4 * head, P.CREAM)
        if head > 0.5:
            face(c, hx + 1.5, hy - 2, eyes=eyes, mouth=mouth, gap=5, size=3)
        else:
            face(c, hx + 1, hy - 1, eyes=eyes, mouth=mouth, gap=3)
    if head <= 0:
        snail_shell(c, sx, sy, srad + 0.5)
        with shaded(c, GINGER_RAMP, EDGE) as p:                                 # a sliver of body under the shell
            p.rect(sx - 8, gy - 1, sx + 11, gy, P.GINGER)
        if peek >= 0:                                                           # eyes peering out from under it
            c.ellipse(sx + 7, gy - 3, 3.8, 2, P.OUTLINE)
            c.rect(sx + 5 + peek, gy - 3, sx + 5 + peek, gy - 2, P.YELLOW)
            c.rect(sx + 8 + peek, gy - 3, sx + 8 + peek, gy - 2, P.YELLOW)
    return c.outline(EDGE).img


def snail_cat() -> Sprite:
    sprite = Sprite("snail_cat", (40, 26), faces_left=True, cx=20, ground=24)
    sprite.add("walk", [snail_cat_frame(s) for s in (0, 1, 2, 1)], fps=6)
    sprite.add("hide", [snail_cat_frame(0, 0.6, eyes="shut", mouth="flat"),
                        snail_cat_frame(0, 0.25, eyes="shut", mouth=None), snail_cat_frame(0, 0)], fps=10, loop=False)
    sprite.add("shell", [snail_cat_frame(0, 0, peek=0), snail_cat_frame(0, 0, peek=1)], fps=3)
    sprite.add("death", dying(snail_cat_frame(0, 1, eyes="x", mouth="open"), 7), fps=10, loop=False)
    return sprite


# --- spider cat [18x16] ----------------------------------------------------------------------------

SPIDER_RAMP = ramp((P.SPIDER_L, P.SPIDER, P.SPIDER_D))


def spider_legs(c: Canvas, cx: float, y: float, mode: str, step: int, side: int, floor: float) -> None:
    """Three long jointed legs on one side (-1 = back/far, 1 = front/near): a thigh rising to a high knee,
    a shin down to the ankle and a short pointed foot. Each leg is outlined on its own so they read apart."""
    for i in (2, 1, 0):
        root = (cx + side * (3.5 + i * 1.2), y - 7 + i * 0.8)
        spread = 5.5 + i * 2.8
        if mode == "walk":
            lift = 2 if (i + step + (side > 0)) % 2 else 0
            knee = (root[0] + side * spread, root[1] - 8 - lift + i * 1.5)
            ankle = (knee[0] + side * 2.5, y - 2 - lift * 0.6)
            foot = (ankle[0] + side * 1.5, y - lift * 0.4)
        elif mode == "hang":
            knee = (root[0] + side * spread * 0.8, root[1] - 4 + i * 1.5 + step * 0.5)
            ankle = (knee[0] + side * 1, knee[1] + 6 - step * 0.5)
            foot = (ankle[0] - side * 1, ankle[1] + 2)
        else:                                                                    # drop: legs flung up
            knee = (root[0] + side * spread, root[1] - 9 - step + i * 1.5)
            ankle = (knee[0] + side * 2, knee[1] - 3 + i * 2)
            foot = (ankle[0] + side * 1, ankle[1] - 1.5)
        foot = (foot[0], min(foot[1], floor))
        ankle = (ankle[0], min(ankle[1], floor))
        near = side > 0
        colour = (P.VIOLET if i % 2 == 0 else P.PURPLE_L) if near else (P.PURPLE if i % 2 == 0 else P.SPIDER_L)
        with shaded(c, None, EDGE) as p:
            p.line(root, knee, colour, 2)
            p.line(knee, ankle, colour, 1)
            p.line(ankle, foot, P.PINK_D if near else P.PURPLE, 1)
            p.px(knee[0], knee[1], P.PINK if near else P.VIOLET)                 # knee joint
            p.px(foot[0], foot[1], P.PINK)


def spider_cat_frame(mode: str, step: int = 0, eyes: str = "glow", mouth: str = "fangs", thread: bool = True) -> Image.Image:
    size, cx, gy = (50, 56), 25, 52
    y = gy - (1 if mode == "walk" and step % 2 else 0) - (3 if mode != "walk" else 0)
    c = Canvas(*size)
    if mode != "walk" and thread:
        top_y = y - 17
        c.line((cx + 2, 0), (cx + 2, top_y), P.GREY_L)
        for ty in range(3, int(top_y), 6):                                     # a glint running down the silk
            c.px(cx + 2, ty, P.WHITE)
    spider_legs(c, cx, y, mode, step, -1, gy)
    spider_legs(c, cx + 1, y, mode, step + 1, 1, gy)
    with shaded(c, SPIDER_RAMP, EDGE, up=2) as p:
        p.ellipse(cx - 4, y - 7.5, 6.5, 5.8, P.SPIDER)                         # round abdomen
    for dx, dy in ((-7, -9), (-6, -10), (-4, -11), (-8, -6)):                    # violet markings
        c.px(cx + dx, y + dy, P.VIOLET)
    with shaded(c, SPIDER_RAMP, EDGE, up=2) as p:
        ear(p, cx - 1.5, y - 13, 5.5, P.SPIDER, inner=P.VIOLET, lean=-0.8, half=3)
        ear(p, cx + 7.5, y - 13, 5.5, P.SPIDER, inner=P.VIOLET, lean=0.8, half=3)
        p.ellipse(cx + 3, y - 8, 7.5, 6.5, P.SPIDER)                           # big cat head
    c.ellipse(cx + 3.5, y - 4.5, 3.5, 1.6, P.BATWING_L)                         # pale muzzle
    face(c, cx + 5, y - 10.5, eyes=eyes, mouth=mouth, gap=6, eye=P.YELLOW, nose=P.PINK_D, blush=None, size=3)
    if eyes == "glow":
        c.rect(cx + 6, y - 10.5, cx + 6, y - 8.5, P.OUTLINE)                  # slit pupils
        c.rect(cx, y - 10.5, cx, y - 8.5, P.OUTLINE)
        c.px(cx + 7, y - 10.5, P.WHITE)
        c.px(cx + 1, y - 10.5, P.WHITE)
    return c.outline(EDGE).img


def spider_cat() -> Sprite:
    sprite = Sprite("spider_cat", (50, 56), faces_left=True, cx=25, ground=52)
    sprite.add("hang", [spider_cat_frame("hang", 0), spider_cat_frame("hang", 1)], fps=3)
    sprite.add("drop", [spider_cat_frame("drop", 0, eyes="wide", mouth="open"),
                        spider_cat_frame("drop", 1, eyes="wide", mouth="open")], fps=8)
    sprite.add("walk", [spider_cat_frame("walk", k) for k in range(4)], fps=10)
    sprite.add("death", dying(spider_cat_frame("walk", 0, eyes="x", mouth="open"), 5), fps=10, loop=False)
    return sprite


def build() -> list[Sprite]:
    return [slime(), mushroom_cat(), spore(), forest_bat(), plant_cat(), bee_cat(), sting(), stump_cat(), leaf(),
            snail_cat(), spider_cat()]
