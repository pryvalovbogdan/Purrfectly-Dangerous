"""World 2, the Frostpaw Mountains critters (from `docs/concept/Frostpaw Mountains Enemy Sprite Sheet.png`):
the ice slime, snow cat, ice bat, ice golem, penguin soldier, snowy owl, ice hedgehog, snowman, icicle plant
and mini yeti, and the spears, icicles, snowballs and ice bolts they throw.

Drawn facing right with light from the top-left and mirrored on export. They play at night over a dark
navy sky and white snow, so every part gets a light rim along its top edge (`shaded`), white fur is shaded
in blues, ice is a saturated blue ramp, and the figure has a dark 1px outline. Slash arcs are glowing ice
crescents laid on after the outline. Gameplay hitboxes (w x h, at the feet) are noted on each sprite."""
from __future__ import annotations

import math

from PIL import Image

import palette as P
from critters import ear, face, ramp, shaded, sparkle
from draw import Canvas, noise, see_through, shatter, tint, vanish
from sprite import Sprite

EDGE = P.OUTLINE
FUR = ramp((P.WHITE, P.SNOW_L, P.SNOW), (P.SNOW_L, P.SNOW, P.SNOW_D), (P.SNOW, P.SNOW_D, P.SNOW_DD))
ICE = ramp((P.FR_ICE_GLOW, P.FR_ICE_L, P.FR_ICE), (P.FR_ICE_L, P.FR_ICE, P.FR_ICE_D),
           (P.FR_ICE, P.FR_ICE_D, P.FR_ICE_DD))
ROCK = ramp((P.FR_ROCK_L, P.FR_ROCK, P.FR_ROCK_D), (P.FR_ROCK, P.FR_ROCK_D, P.FR_ROCK_DD))
ORANGE_RAMP = ramp((P.YELLOW, P.ORANGE, P.GINGER_D))
TWIG = ramp((P.BARK_L, P.BARK_D, P.BARK_DD))


# --- shared helpers --------------------------------------------------------------------------------

def fluffy(c: Canvas, x: float, y: float, rx: float, ry: float, colour, seed: int, tufts: int = 14,
           size: float = 1.6, a0: float = 0, a1: float = 360) -> None:
    """An ellipse with a tufted edge (fur, snow): small bumps all round, or only between a0 and a1 degrees."""
    c.ellipse(x, y, rx, ry, colour)
    rnd = noise(seed)
    for k in range(tufts):
        a = math.radians(a0 + (a1 - a0) * (k + 0.5) / tufts) + (rnd() - 0.5) * 0.2
        rad = size * (0.7 + rnd() * 0.6)
        c.ellipse(x + math.cos(a) * (rx - rad * 0.4), y - math.sin(a) * (ry - rad * 0.4), rad, rad, colour)


def shard(c: Canvas, base: tuple[float, float], angle: float, length: float, width: float, colour) -> None:
    """A pointed ice crystal from `base` toward `angle` degrees (0 = right, 90 = up)."""
    a = math.radians(angle)
    ux, uy = math.cos(a), -math.sin(a)
    nx, ny = -uy, ux
    bx, by = base
    c.poly([(bx + nx * width, by + ny * width), (bx + ux * length * 0.7 + nx * width, by + uy * length * 0.7 + ny * width),
            (bx + ux * length, by + uy * length),
            (bx + ux * length * 0.7 - nx * width, by + uy * length * 0.7 - ny * width), (bx - nx * width, by - ny * width)],
           colour)


def crystals(c: Canvas, pieces: list[tuple[float, float, float, float, float]], seed: int = 0) -> None:
    """A cluster of ice shards [(x, y, angle, length, width)], each with a lit left facet and a glint."""
    with shaded(c, ICE, EDGE, up=1, down=1) as p:
        for x, y, ang, ln, w in pieces:
            shard(p, (x, y), ang, ln, w, P.FR_ICE)
    for x, y, ang, ln, w in pieces:                                    # the lit facet down the middle
        a = math.radians(ang)
        c.line((x + math.cos(a) * ln * 0.15, y - math.sin(a) * ln * 0.15),
               (x + math.cos(a) * ln * 0.75, y - math.sin(a) * ln * 0.75), P.FR_ICE_L)
        c.px(x + math.cos(a) * ln * 0.55 - 0.5, y - math.sin(a) * ln * 0.55, P.WHITE)


def arc_layer(size, cx: float, cy: float, r: float, a0: float, a1: float, thick: float) -> Image.Image:
    """A glowing ice crescent (a slash), thickest in the middle, from a0 to a1 degrees (0 = right, 90 = up)."""
    c = Canvas(*size)
    steps = 48
    for i in range(steps + 1):
        t = i / steps
        a = math.radians(a0 + (a1 - a0) * t)
        w = thick * math.sin(math.pi * t) + 0.6
        x, y = cx + math.cos(a) * r, cy - math.sin(a) * r
        c.ellipse(x, y, w, w, P.FR_ICE)
    for i in range(steps + 1):
        t = i / steps
        a = math.radians(a0 + (a1 - a0) * t)
        w = thick * 0.55 * math.sin(math.pi * t)
        x, y = cx + math.cos(a) * (r + thick * 0.3), cy - math.sin(a) * (r + thick * 0.3)
        if w > 0.4:
            c.ellipse(x, y, w, w, P.FR_ICE_GLOW)
        if 0.3 < t < 0.7:
            c.px(x, y, P.WHITE)
    c.outline(P.FR_ICE_D)
    return c.img


def with_arc(img: Image.Image, arc: Image.Image, sparks: list[tuple[float, float]] = ()) -> Image.Image:
    out = Canvas(*img.size)
    out.paste(img)
    out.paste(arc)
    for x, y in sparks:
        sparkle(out, x, y, P.FR_ICE_GLOW, big=True)
    return out.img


def hit_frames(hurt: Image.Image, sparks: list[tuple[float, float]]) -> list[Image.Image]:
    """Hit: a white flash of the flinch pose, then the flinch with ice sparkles bursting off it."""
    second = Canvas(*hurt.size)
    second.paste(hurt)
    for i, (x, y) in enumerate(sparks):
        sparkle(second, x, y, P.FR_ICE_GLOW, big=i % 2 == 0)
    return [tint(hurt, P.WHITE, 0.65), second.img]


def dying(still: Image.Image, depth: float) -> list[Image.Image]:
    """Death: a white flash, then it sinks by `depth` while fading out."""
    return [tint(still, P.WHITE, 0.6)] + [vanish(still, t, depth=depth, flash=False) for t in (0.35, 0.65, 0.95)]


def crumbling(still: Image.Image, seed: int) -> list[Image.Image]:
    """Death for ice and rock: a white flash, then it breaks into chunks that drop and fade."""
    frames = [tint(still, P.WHITE, 0.6)]
    for t, keep in ((0.3, 255), (0.6, 200), (0.9, 110)):
        frames.append(see_through(shatter(still, t, seed, block=4, spread=0.25, gravity=0.8), keep))
    return frames


def snow_puff(c: Canvas, x: float, y: float, w: float) -> None:
    """A little drift of snow whose flat bottom is row `y`."""
    with shaded(c, FUR, EDGE) as p:
        fluffy(p, x, y, w, w * 0.55, P.SNOW_L, int(x * 7 + w), tufts=6, size=1.2, a0=0, a1=180)
        p.rect(0, y + 1, p.size[0], p.size[1], P.CLEAR)


# --- ice slime [20x14] -----------------------------------------------------------------------------

def ice_slime_body(c: Canvas, cx: float, gy: float, sx: float = 1.0, sy: float = 1.0, lift: float = 0,
                   eyes: str = "open", mouth: str = "smile") -> None:
    """An icy blue dome with a crystal peak, snow clinging to its foot; `sx`/`sy` squash and stretch."""
    base = gy - lift
    height = 13 * sy
    ry = height * 0.72
    rx = 10 * sx / 0.92
    ey = base - height + ry
    top = base - height + 1
    with shaded(c, ICE, up=2, down=1) as p:                                   # a gumdrop: dome rising to a peak
        p.ellipse(cx, ey, rx, ry, P.FR_ICE_L)
        p.poly([(cx - 6 * sx, top + 6), (cx + 0.5, top - 3 * sy), (cx + 6 * sx, top + 6)], P.FR_ICE_L)
        p.rect(0, base + 1, p.size[0], p.size[1], P.CLEAR)
    crystals(c, [(cx + 0.5, top - 1, 92, 6 * sy, 2), (cx - 2.5, top + 1, 130, 4.5, 1.6), (cx + 3, top + 1, 55, 4.5, 1.6)])
    c.rect(cx - 7 * sx, top + 5, cx - 7 * sx + 1, top + 7, P.WHITE)            # gloss
    c.px(cx - 5 * sx, top + 4, P.WHITE)
    c.px(cx - 8 * sx, top + 9, P.FR_ICE_GLOW)
    for bx, by in ((6, -3), (4, -2), (8, -5)):                                  # frozen bubbles inside
        c.px(cx + bx * sx, base + by, P.FR_ICE_GLOW)
    face(c, cx + 2, base - 8 * sy, eyes=eyes, mouth=mouth, gap=6, nose=None, blush=P.PINK, size=3)
    if lift < 1:                                                                # snow at its foot
        snow_puff(c, cx - rx * 0.85, base, 3)
        snow_puff(c, cx + rx * 0.8, base, 2.5)


def ice_slime() -> Sprite:
    size, cx, gy = (34, 34), 17, 31
    sprite = Sprite("ice_slime", size, faces_left=True, cx=cx, ground=gy)

    def f(sx, sy, lift=0, eyes="open", mouth="smile"):
        c = Canvas(*size)
        ice_slime_body(c, cx, gy, sx, sy, lift, eyes, mouth)
        return c.outline(EDGE).img

    sprite.add("idle", [f(1, 1), f(1.04, 0.95)], fps=3)
    sprite.add("walk", [f(1.1, 0.86, 0, mouth="w"), f(0.92, 1.1, 2), f(1.0, 1.0, 4, mouth="open"), f(0.95, 1.05, 1)],
               fps=8)
    sprite.add("attack", [f(1.16, 0.8, 0, eyes="angry", mouth="flat"), f(0.88, 1.14, 7, eyes="angry", mouth="open"),
                          f(1.14, 0.84, 0, eyes="shut", mouth="w")], fps=8, loop=False)
    hurt = f(1.1, 0.9, eyes="shut", mouth="open")
    sprite.add("hit", hit_frames(hurt, [(cx - 9, gy - 15), (cx + 8, gy - 17), (cx, gy - 20)]), fps=10, loop=False)

    def melt(t: float) -> Image.Image:
        c = Canvas(*size)
        ice_slime_body(c, cx, gy, 1.0 + t * 0.12, max(0.35, 1.0 - t * 0.7), eyes="x", mouth="flat")
        if t > 0:
            for dx, dy in ((-8, -13), (6, -15), (-1, -19)):
                sparkle(c, cx + dx, gy + dy + 3 - t * 2, P.FR_ICE_GLOW)
        return c.outline(EDGE).img

    frames = [tint(melt(0), P.WHITE, 0.6), melt(0.4), see_through(melt(0.75), 180), see_through(melt(1.0), 80)]
    sprite.add("death", frames, fps=10, loop=False)
    return sprite


# --- snow cat [20x20] ------------------------------------------------------------------------------

def snow_cat_frame(step: int = 0, walk: bool = False, crouch: float = 0, paw: float = 0, head_back: float = 0,
                   eyes: str = "open", mouth: str = "w", scarf_wave: int = 0) -> Image.Image:
    """A fluffy white cat on four stubby legs with a big head and a blue scarf.
    paw: 0 = standing, 1 = front paw raised, 2 = front paw slashing forward."""
    size, x, gy = (40, 34), 16, 31
    c = Canvas(*size)
    by = gy - crouch
    with shaded(c, FUR, EDGE) as p:                                          # big fluffy tail curling up
        for i, (tx, ty, r) in enumerate(((-8, -7, 2.4), (-10.5, -9.5, 2.6), (-11.5, -13, 2.6), (-10.5, -16, 2.3),
                                         (-8.5, -17.5, 1.8))):
            p.ellipse(x + tx - (scarf_wave % 2) * (i > 2), by + ty, r, r, P.SNOW_L)
    lifts = [0, 0, 0, 0]
    if walk:
        lifts = [(step % 2) * 1.5, ((step + 1) % 2) * 1.5, ((step + 1) % 2) * 1.5, (step % 2) * 1.5]
    with shaded(c, FUR, EDGE) as p:                                          # far legs (darker, behind)
        for lx, lift in ((x - 5, lifts[1]), (x + 3, lifts[3])):
            p.rect(lx, by - 5 - lift, lx + 2.5, by - lift, P.SNOW)
    with shaded(c, FUR, up=2) as p:
        fluffy(p, x - 1, by - 7.5, 8, 5.5, P.SNOW_L, 11, tufts=10, size=1.5)   # body
    with shaded(c, FUR, EDGE) as p:                                          # near legs with round paws
        legs = [(x - 7, lifts[0]), (x + 1, lifts[2])]
        if paw == 0:
            legs.append((x + 4.5, 0)) if False else None
        for lx, lift in legs:
            p.rect(lx, by - 5 - lift, lx + 3, by - lift, P.SNOW_L)
            p.ellipse(lx + 1.5, by - lift - 1, 2, 1, P.SNOW_L)
        if paw:                                                               # the slashing front paw
            ang = 60 if paw == 1 else 100
            end = (x + 6 + math.sin(math.radians(ang)) * 6, by - 9 - math.cos(math.radians(ang)) * 6)
            p.line((x + 5, by - 8), end, P.SNOW_L, 3)
            p.ellipse(end[0], end[1], 1.8, 1.8, P.SNOW_L)
    if paw:
        for k in range(3):                                                    # claws
            c.px(end[0] + 2, end[1] - 1 + k, P.FR_ICE_D)
    hx, hy = x + 5 - head_back, by - 15
    with shaded(c, FUR, EDGE, up=2) as p:
        ear(p, hx - 4.5, hy - 4.5, 6, P.SNOW_L, inner=P.PINK, lean=-1, half=3)
        ear(p, hx + 4, hy - 5, 6, P.SNOW_L, inner=P.PINK, lean=1, half=3)
        fluffy(p, hx, hy, 7, 6.2, P.SNOW_L, 23, tufts=12, size=1.4)
    c.ellipse(hx + 1.5, hy + 3, 3.5, 1.8, P.WHITE)                           # muzzle
    face(c, hx + 2, hy - 2.5, eyes=eyes, mouth=mouth, gap=5, nose=P.PINK_D, size=3)
    with shaded(c, ICE, EDGE) as p:                                          # blue scarf, its end streaming back
        p.rect(hx - 6, hy + 5, hx + 3, hy + 7, P.FR_ICE)
        tail_y = hy + 7 + (scarf_wave % 2)
        p.poly([(hx - 5, hy + 6), (hx - 10, tail_y + 1), (hx - 10, tail_y + 3), (hx - 4, hy + 8)], P.FR_ICE)
    c.line((hx - 3, hy + 6), (hx + 2, hy + 6), P.FR_ICE_L)
    c.px(hx - 9, tail_y + 2, P.FR_ICE_L)
    return c.outline(EDGE).img


def snow_cat() -> Sprite:
    size, cx, gy = (40, 34), 16, 31
    sprite = Sprite("snow_cat", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [snow_cat_frame(), snow_cat_frame(eyes="shut", scarf_wave=1)], fps=3)
    sprite.add("walk", [snow_cat_frame(k, walk=True, scarf_wave=k) for k in range(4)], fps=8)
    arc = arc_layer(size, cx + 10, gy - 11, 7.5, -70, 70, 2.2)
    sprite.add("attack", [snow_cat_frame(crouch=1, head_back=1, eyes="angry", mouth="flat"),
                          snow_cat_frame(paw=1, eyes="angry", mouth="fangs"),
                          with_arc(snow_cat_frame(paw=2, eyes="angry", mouth="fangs"), arc, [(cx + 18, gy - 23)]),
                          snow_cat_frame(scarf_wave=1)], fps=10, loop=False)
    hurt = snow_cat_frame(crouch=1, head_back=2, eyes="shut", mouth="open")
    sprite.add("hit", hit_frames(hurt, [(cx + 12, gy - 24), (cx - 2, gy - 26), (cx + 15, gy - 14)]), fps=10, loop=False)
    sprite.add("death", dying(snow_cat_frame(crouch=2, eyes="x", mouth="open"), 6), fps=10, loop=False)
    return sprite


# --- ice bat [18x14] -------------------------------------------------------------------------------

def ice_wing(c: Canvas, root: tuple[float, float], side: int, flap: float, far: bool, swept: float = 0) -> None:
    """A scalloped ice-blue membrane wing; side +1 spreads right, -1 left; flap 1 = raised, -1 = lowered;
    `swept` folds it back along the body for a dive."""
    rx, ry = root
    span = (18 if not far else 16) * (1 - swept * 0.35)
    tip = (rx + side * span, ry - 4 - flap * 7 + swept * 5)
    elbow = (rx + side * span * 0.45, ry - 5 - flap * 5 + swept * 2)
    low = ry + 3 - flap * 2
    pts = [root, elbow, tip]
    fingers = []
    for k, t in enumerate((0.82, 0.64, 0.44, 0.24)):
        x = rx + side * span * t
        y = tip[1] + (low - tip[1]) * (1 - t) + 2
        if k % 2 == 0:
            pts.append((x, y + 3.5))
        else:
            pts.append((x, y))
            fingers.append((x, y))
    pts.append((rx, ry + 4))
    with shaded(c, ICE, EDGE, up=1, down=1) as p:
        p.poly(pts, P.FR_ICE if far else P.FR_ICE_L)
    with shaded(c, ICE) as p:                                                 # the arm along the top
        p.line(root, elbow, P.FR_ICE_D, 2)
        p.line(elbow, tip, P.FR_ICE_D, 1)
    for f in fingers:
        c.line(elbow, f, P.FR_ICE_D)
    c.px(tip[0], tip[1], P.WHITE)
    c.px(elbow[0], elbow[1] - 1, P.FR_ICE_GLOW)


def ice_bat_frame(flap: float, eyes: str = "open", mouth: str = "fangs", bob: float = 0, dive: float = 0) -> Image.Image:
    size, cx, gy = (46, 32), 23, 25
    c = Canvas(*size)
    y = gy + bob
    x = cx + dive * 2
    ice_wing(c, (x - 3, y - 10), -1, flap, far=False, swept=dive)
    ice_wing(c, (x + 3, y - 10), 1, flap * 0.85, far=True, swept=dive)
    with shaded(c, FUR, EDGE, up=2) as p:
        fluffy(p, x - 1, y - 5.5, 5.5, 4.3, P.SNOW_L, 31, tufts=8, size=1.2)   # body
    with shaded(c, ORANGE_RAMP, EDGE) as p:                                    # little feet
        p.rect(x - 4, y - 1, x - 2, y, P.PINK_D)
        p.rect(x + 1, y - 1, x + 3, y, P.PINK_D)
    with shaded(c, FUR, EDGE, up=2) as p:
        ear(p, x - 3.5, y - 15, 6, P.SNOW_L, inner=P.PINK, lean=-1, half=3)
        ear(p, x + 5.5, y - 15, 6, P.SNOW_L, inner=P.PINK, lean=1, half=3)
        fluffy(p, x + 1, y - 11, 7.5, 6.2, P.SNOW_L, 37, tufts=12, size=1.3)  # big round head
    c.ellipse(x + 1, y - 15.5, 3, 1.2, P.SNOW_D)                              # a frosty blue cap of fur
    c.ellipse(x + 2, y - 7.5, 3.5, 1.6, P.WHITE)                              # muzzle
    face(c, x + 3, y - 12.5, eyes=eyes, mouth=mouth, gap=6, nose=P.PINK_D, size=3)
    return c.outline(EDGE).img


def ice_bat() -> Sprite:
    size, cx, gy = (46, 32), 23, 25
    sprite = Sprite("ice_bat", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("fly", [ice_bat_frame(f, bob=b) for f, b in ((1, 0), (0.2, 0), (-0.9, -1), (0.2, -1))], fps=12)
    sprite.add("attack", [ice_bat_frame(1, eyes="angry", bob=-1), ice_bat_frame(-0.3, eyes="angry", bob=0, dive=1),
                          ice_bat_frame(0.4, eyes="angry", bob=0, dive=0.4)], fps=10, loop=False)
    hurt = ice_bat_frame(0.6, eyes="shut", mouth="open")
    sprite.add("hit", hit_frames(hurt, [(cx - 6, gy - 22), (cx + 10, gy - 20), (cx + 4, gy - 3)]), fps=10, loop=False)
    dead = ice_bat_frame(-0.5, eyes="x", mouth="open")
    sprite.add("death", [tint(dead, P.WHITE, 0.6), vanish(dead, 0.45, depth=8, flash=False),
                         vanish(dead, 0.9, depth=8, flash=False)], fps=10, loop=False)
    return sprite


# --- ice golem [26x30] -----------------------------------------------------------------------------

GOLEM = ramp((P.FR_MTN_L, P.FR_MTN, P.FR_MTN_D), (P.FR_MTN, P.FR_MTN_D, P.FR_MTN_DD))


def ice_golem_frame(step: int = 0, walk: bool = False, punch: float = 0, eyes: str = "glow", lean: float = 0) -> Image.Image:
    """A hunched boulder of blue-grey rock with ice crystals growing from its head and back, glowing eyes
    and ice-knuckled fists. punch: 0 = arms down, -1 = fist drawn back, 1 = fist thrust forward."""
    size, x, gy = (52, 42), 22, 39
    c = Canvas(*size)
    bob = (step % 2) * 1 if walk else 0
    by = gy - bob
    x += lean
    lifts = ((step % 2) * 2, ((step + 1) % 2) * 2) if walk else (0, 0)
    with shaded(c, GOLEM, EDGE) as p:                                         # far arm behind
        p.ellipse(x - 10, by - 13, 3.5, 5, P.FR_MTN_D)
        p.ellipse(x - 11, by - 7, 3.8, 3.2, P.FR_MTN_D)
    with shaded(c, GOLEM, EDGE) as p:                                         # stubby legs
        p.rect(x - 8, by - 6, x - 3, gy - lifts[0], P.FR_MTN)
        p.rect(x + 2, by - 6, x + 7, gy - lifts[1], P.FR_MTN)
    crystals(c, [(x - 8, by - 21, 115, 9, 2.6), (x - 4, by - 23, 98, 8, 2.4), (x - 12, by - 16, 150, 7, 2.2)])
    with shaded(c, GOLEM, up=2) as p:
        p.ellipse(x - 1, by - 15, 11, 10, P.FR_MTN)                          # boulder body
    for a, b in (((x - 6, by - 12), (x - 2, by - 9)), ((x - 3, by - 19), (x, by - 15)), ((x + 2, by - 9), (x + 5, by - 6))):
        c.line(a, b, P.FR_MTN_D)                                              # cracks
    with shaded(c, GOLEM, EDGE, up=2) as p:
        p.ellipse(x + 4, by - 23, 6.5, 5.5, P.FR_MTN)                        # head
    crystals(c, [(x + 3, by - 27, 95, 8, 2.6), (x, by - 26, 130, 5.5, 1.8), (x + 7, by - 26, 55, 5, 1.8)])
    for ex in (x + 2, x + 7):                                                 # glowing eyes in dark sockets
        c.ellipse(ex + 0.5, by - 22.5, 1.8, 1.5, P.FR_ROCK_DD)
        if eyes == "glow":
            c.rect(ex, by - 23, ex + 1, by - 22, P.FR_ICE_GLOW)
            c.px(ex + 1, by - 23, P.WHITE)
        elif eyes == "angry":
            c.rect(ex, by - 22, ex + 1, by - 22, P.FR_ICE_GLOW)
        elif eyes == "x":
            c.px(ex, by - 23, P.FR_ICE_GLOW)
            c.px(ex + 1, by - 22, P.FR_ICE_GLOW)
        elif eyes == "shut":
            c.rect(ex - 0.5, by - 22, ex + 1.5, by - 22, P.FR_ICE_L)
    c.rect(x + 3, by - 19.5, x + 6, by - 19.5, P.FR_ROCK_DD)                 # mouth
    # Near arm with an ice-knuckled fist.
    sh = (x + 7, by - 14)
    if punch > 0:
        fist = (x + 14 + punch * 4, by - 16)
    elif punch < 0:
        fist = (x - 1, by - 17)
    else:
        fist = (x + 11, by - 5)
    with shaded(c, GOLEM, EDGE) as p:
        p.line(sh, fist, P.FR_MTN, 5)
        p.ellipse(fist[0], fist[1], 3.6, 3.4, P.FR_MTN)
    crystals(c, [(fist[0] + 1, fist[1] - 2, 70, 4, 1.4), (fist[0] + 2.5, fist[1] - 0.5, 20, 4, 1.4)])
    return c.outline(EDGE).img


def ice_golem() -> Sprite:
    size, cx, gy = (52, 42), 22, 39
    sprite = Sprite("ice_golem", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [ice_golem_frame(), ice_golem_frame(lean=-0.6)], fps=3)
    sprite.add("walk", [ice_golem_frame(k, walk=True) for k in range(4)], fps=6)
    arc = arc_layer(size, cx + 17, gy - 17, 6.5, -60, 70, 2.2)
    sprite.add("attack", [ice_golem_frame(punch=-1, lean=-1, eyes="angry"), ice_golem_frame(punch=0.5, eyes="angry"),
                          with_arc(ice_golem_frame(punch=1, lean=1, eyes="angry"), arc, [(cx + 23, gy - 30), (cx + 21, gy - 4)]),
                          ice_golem_frame(punch=0.3)], fps=8, loop=False)
    hurt = ice_golem_frame(lean=-1.5, eyes="shut")
    sprite.add("hit", hit_frames(hurt, [(cx + 12, gy - 32), (cx - 12, gy - 28), (cx + 14, gy - 12)]), fps=10, loop=False)
    sprite.add("death", dying(ice_golem_frame(eyes="x"), 9), fps=10, loop=False)
    return sprite


# --- penguin soldier [18x24] + spear ---------------------------------------------------------------

PENGUIN = ramp((P.FR_ICE, P.FR_ICE_D, P.FR_ICE_DD), (P.FR_ICE_L, P.FR_ICE, P.FR_ICE_D))


def ice_spear(c: Canvas, butt: tuple[float, float], tip: tuple[float, float]) -> None:
    """A wooden shaft with a long ice blade at `tip`."""
    with shaded(c, TWIG) as p:
        p.line(butt, tip, P.BARK_D, 2)
    dx, dy = tip[0] - butt[0], tip[1] - butt[1]
    ln = math.hypot(dx, dy)
    ang = math.degrees(math.atan2(-dy, dx))
    c.rect(tip[0] - dx / ln * 1.5 - 1, tip[1] - dy / ln * 1.5 - 1, tip[0] - dx / ln * 1.5 + 1,
           tip[1] - dy / ln * 1.5 + 1, P.FR_ICE_D)                            # binding
    crystals(c, [(tip[0], tip[1], ang, 7, 1.8)])


def penguin_soldier_frame(step: int = 0, walk: bool = False, spear: str = "up", lean: float = 0, eyes: str = "open",
                          mouth: str = None) -> Image.Image:
    """spear: up (held upright beside it), back (drawn back level), thrust (stabbed forward), none."""
    size, x, gy = (48, 34), 16, 31
    c = Canvas(*size)
    sway = (0, 1, 0, -1)[step % 4] if walk else 0
    x += lean + sway * 0.5
    lift = ((step % 2) * 1.5, ((step + 1) % 2) * 1.5) if walk else (0, 0)
    with shaded(c, ORANGE_RAMP, EDGE) as p:                                   # orange feet
        p.ellipse(x - 3, gy - lift[0] - 1, 2.6, 1, P.ORANGE)
        p.ellipse(x + 3, gy - lift[1] - 1, 2.6, 1, P.ORANGE)
    if spear == "up":
        ice_spear(c, (x + 12.5, gy - 1), (x + 13, gy - 21))
    with shaded(c, PENGUIN, up=2) as p:
        p.ellipse(x, gy - 11, 7.5, 10.5, P.FR_ICE_D)                         # egg body
        p.ellipse(x - 5, gy - 4, 3, 2.5, P.FR_ICE_D)                          # tail
    with shaded(c, FUR) as p:
        p.ellipse(x + 2, gy - 7.5, 5, 7, P.SNOW_L)                            # white belly
        p.ellipse(x + 3.5, gy - 15, 4.2, 3, P.SNOW_L)                         # white face patch
    crystals(c, [(x - 2, gy - 20.5, 105, 4.5, 1.4), (x + 1, gy - 20.5, 80, 3.5, 1.2)])   # frosty crest
    c.px(x - 4, gy - 18, P.FR_ICE)
    c.px(x - 3, gy - 19, P.FR_ICE_L)
    face(c, x + 4.5, gy - 16, eyes=eyes, mouth=mouth, gap=3, nose=None, blush=P.PINK)
    with shaded(c, ORANGE_RAMP, EDGE) as p:                                   # beak
        p.poly([(x + 7, gy - 14), (x + 11.5, gy - 12.5), (x + 7, gy - 11.5)], P.ORANGE)
    hand = {"up": (x + 11.5, gy - 8), "back": (x + 1, gy - 8), "thrust": (x + 9, gy - 9), "none": (x + 4, gy - 5)}[spear]
    if spear == "back":
        ice_spear(c, (x - 10, gy - 7), (x + 13, gy - 9))
    elif spear == "thrust":
        ice_spear(c, (x - 3, gy - 8), (x + 20, gy - 10))
    with shaded(c, PENGUIN, EDGE) as p:                                       # near flipper gripping the shaft
        p.line((x, gy - 10), hand, P.FR_ICE_D, 3)
    return c.outline(EDGE).img


def penguin_soldier() -> Sprite:
    size, cx, gy = (48, 34), 16, 31
    sprite = Sprite("penguin_soldier", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [penguin_soldier_frame(), penguin_soldier_frame(eyes="shut")], fps=3)
    sprite.add("walk", [penguin_soldier_frame(k, walk=True) for k in range(4)], fps=8)
    thrust = Canvas(*size)
    thrust.paste(penguin_soldier_frame(spear="thrust", lean=1, eyes="angry"))
    sparkle(thrust, cx + 24, gy - 16, P.FR_ICE_GLOW, big=True)
    sprite.add("attack", [penguin_soldier_frame(spear="back", lean=-1, eyes="angry"),
                          penguin_soldier_frame(spear="back", lean=-2, eyes="angry"), thrust.img,
                          penguin_soldier_frame(spear="up", eyes="open")], fps=8, loop=False)
    hurt = penguin_soldier_frame(spear="none", lean=-1, eyes="shut", mouth="open")
    sprite.add("hit", hit_frames(hurt, [(cx + 8, gy - 24), (cx - 7, gy - 20), (cx + 11, gy - 6)]), fps=10, loop=False)
    sprite.add("death", dying(penguin_soldier_frame(spear="none", eyes="x", mouth="open"), 7), fps=10, loop=False)
    return sprite


def spear() -> Sprite:
    """The thrown ice spear tip: a long faceted blade pointing right (mirrored it flies left)."""
    sprite = Sprite("spear", (16, 6), faces_left=True)
    frames = []
    for k in range(2):
        c = Canvas(16, 6)
        c.poly([(1, 2.5), (5, 1), (14, 2.5), (5, 4)], P.FR_ICE)
        c.line((3, 2), (12, 2), P.FR_ICE_L)
        c.line((4, 3), (11, 3), P.FR_ICE_D)
        c.px(8 + k * 2, 2, P.WHITE)
        c.px(6, 2, P.FR_ICE_GLOW)
        c.outline(P.FR_ICE_DD)
        c.px(0, 2 + k, P.FR_ICE_GLOW)                                          # frost trail
        frames.append(c.img)
    sprite.add("fly", frames, fps=10)
    return sprite


# --- snowy owl [20x16] + icicle_shot ---------------------------------------------------------------

def owl_wing(c: Canvas, root: tuple[float, float], side: int, flap: float, far: bool) -> None:
    """A broad feathered wing: a fan of rounded feathers whose tips spread out at the end."""
    rx, ry = root
    span = 16 if not far else 14
    tip = (rx + side * span, ry - 5 - flap * 8)
    with shaded(c, FUR, EDGE, up=1, down=1) as p:
        colour = P.SNOW if far else P.SNOW_L
        p.poly([root, (rx + side * span * 0.5, ry - 4 - flap * 6), tip, (rx + side * span * 0.85, ry + 2 - flap * 3),
                (rx + side * span * 0.5, ry + 4 - flap * 1.5), (rx, ry + 4)], colour)
        for k in range(5):                                                    # feather tips along the trailing edge
            t = 0.35 + k * 0.15
            fx = rx + side * span * t
            fy = ry + 4 - flap * 1.5 + (tip[1] + 2 - (ry + 4 - flap * 1.5)) * ((t - 0.35) / 0.65) + 1.5
            p.ellipse(fx, fy, 1.6, 2.2, colour)
    for k in range(4):                                                        # feather lines
        t = 0.4 + k * 0.15
        a = (rx + side * span * (t - 0.12), ry - 1 - flap * 4 * t)
        b = (rx + side * span * t, ry + 3 - flap * 2.5 * t)
        c.line(a, b, P.SNOW_D)
    c.px(tip[0] - side, tip[1] + 1, P.PALE_D)


def snowy_owl_frame(flap: float, bob: float = 0, eyes: str = "open", holding: bool = False, tilt: float = 0) -> Image.Image:
    size, cx, gy = (46, 36), 23, 28
    c = Canvas(*size)
    y = gy + bob
    x = cx + tilt
    owl_wing(c, (x - 3, y - 10), -1, flap, far=False)
    owl_wing(c, (x + 3, y - 10), 1, flap * 0.85, far=True)
    with shaded(c, ORANGE_RAMP, EDGE) as p:                                   # talons
        p.rect(x - 3, y - 1.5, x - 1, y, P.GOLD_D)
        p.rect(x + 1, y - 1.5, x + 3, y, P.GOLD_D)
    if holding:
        icicle_shape(c, x, y + 0, 0.8)
    with shaded(c, FUR, up=2) as p:
        fluffy(p, x, y - 8, 7, 7.5, P.SNOW_L, 41, tufts=12, size=1.3)          # round body
        ear(p, x - 3.5, y - 15, 4.5, P.SNOW_L, inner=None, lean=-1.2, half=2.4)   # ear tufts
        ear(p, x + 4.5, y - 15, 4.5, P.SNOW_L, inner=None, lean=1.2, half=2.4)
    for k, (dx, dy) in enumerate(((-3, -4), (0, -3), (3, -4), (-1.5, -1.5), (1.5, -1.5))):   # chest speckles
        c.px(x + dx, y + dy, P.SNOW_D)
    c.px(x - 3.5, y - 18, P.PINK)
    c.px(x + 5, y - 18, P.PINK)
    with shaded(c, FUR) as p:
        p.ellipse(x + 1, y - 11, 5.5, 4.2, P.WHITE)                           # face disc
    face(c, x + 3, y - 12.5, eyes=eyes, mouth=None, gap=5, nose=None, blush=P.PINK, size=3)
    c.rect(x + 0.5, y - 8.5, x + 1.5, y - 8.5, P.ORANGE)                         # little hooked beak
    c.px(x + 1, y - 7.5, P.GINGER_D)
    return c.outline(EDGE).img


def icicle_shape(c: Canvas, x: float, top: float, s: float = 1.0) -> None:
    """A falling icicle, point down, about 6*s wide and 12*s tall, its top centred on (x, top)."""
    with shaded(c, ICE, EDGE) as p:
        p.poly([(x - 3 * s, top), (x + 3 * s, top), (x + 1.2 * s, top + 8 * s), (x, top + 12 * s),
                (x - 1.2 * s, top + 8 * s)], P.FR_ICE_L)
    c.line((x - 1 * s, top + 1), (x - 0.3 * s, top + 8 * s), P.WHITE)
    c.line((x + 1.5 * s, top + 1), (x + 0.5 * s, top + 7 * s), P.FR_ICE)


def snowy_owl() -> Sprite:
    size, cx, gy = (46, 36), 23, 28
    sprite = Sprite("snowy_owl", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("fly", [snowy_owl_frame(f, b) for f, b in ((1, 0), (0.2, 0), (-0.9, -1), (0.2, -1))], fps=10)
    sprite.add("attack", [snowy_owl_frame(1, -1, eyes="angry", holding=True),
                          snowy_owl_frame(-0.8, 0, eyes="angry"),
                          snowy_owl_frame(0.3, -1, eyes="open")], fps=8, loop=False)
    hurt = snowy_owl_frame(0.5, eyes="shut", tilt=-1)
    sprite.add("hit", hit_frames(hurt, [(cx - 8, gy - 24), (cx + 9, gy - 22), (cx + 6, gy - 2)]), fps=10, loop=False)
    sprite.add("death", dying(snowy_owl_frame(-0.6, eyes="x"), 8), fps=10, loop=False)
    return sprite


def icicle_shot() -> Sprite:
    """A falling icicle, point down: 8x14 frame, the frame bottom is the tip."""
    sprite = Sprite("icicle_shot", (8, 14), faces_left=True)
    frames = []
    for k in range(2):
        c = Canvas(8, 14)
        icicle_shape(c, 3.5, 0.5, 1.0)
        c.px(3, 3 + k * 3, P.WHITE)
        frames.append(c.outline(EDGE).img)
    sprite.add("fly", frames, fps=8)
    return sprite


# --- ice hedgehog [20x16] --------------------------------------------------------------------------

def ice_quill(c: Canvas, base, a: float, length: float, colour) -> None:
    ux, uy = math.cos(a), -math.sin(a)
    nx, ny = -uy, ux
    bx, by = base
    tip = (bx + ux * length, by + uy * length)
    c.poly([(bx + nx * 1.5, by + ny * 1.5), tip, (bx - nx * 1.5, by - ny * 1.5)], colour)
    c.px(tip[0] - ux * 1.2, tip[1] - uy * 1.2, P.WHITE)


def ice_coat(c: Canvas, x: float, y: float, rx: float, ry: float, a0: float, a1: float, seed: int, wobble: int = 0,
             length: float = 6.5) -> None:
    """A coat of crystal quills: a pale body with two interleaved fans of ice spines swept back."""
    rnd = noise(seed)
    with shaded(c, FUR, up=2, down=2) as p:
        p.ellipse(x, y, rx, ry, P.SNOW)
    for half, colour in ((0, P.FR_ICE), (1, P.FR_ICE_L)):
        with shaded(c, ICE, EDGE, up=1, down=1) as p:
            n = int((a1 - a0) / 24)
            for k in range(n + 1):
                deg = a0 + (a1 - a0) * k / n + half * 12 + ((k + wobble) % 2) * 2
                if deg > a1 + 6:
                    continue
                a = math.radians(deg)
                bx, by = x + math.cos(a) * rx * 0.7, y - math.sin(a) * ry * 0.7
                ice_quill(p, (bx, by), a + math.radians(20), length + rnd() * 1.5 - half * 0.8, colour)


def ice_hedgehog_body(c: Canvas, x: float, gy: float, step: int, eyes: str = "open", mouth: str = "w",
                      tuck: float = 0.0) -> None:
    with shaded(c, FUR, EDGE) as p:                                           # little feet
        for fx, up in ((x - 6, step % 2), (x + 3, (step + 1) % 2)):
            p.rect(fx, gy - up - 1.5, fx + 3, gy - up, P.SNOW)
    ice_coat(c, x - 1.5, gy - 8, 9.5, 7, 70, 230, 17, step)
    hx, hy = x + 7 - tuck * 4, gy - 7 + tuck
    k = 1 - tuck * 0.3
    with shaded(c, FUR, EDGE, up=2) as p:
        ear(p, hx - 3.5, hy - 4, 5 * (1 - tuck * 0.6), P.SNOW_L, inner=P.PINK, lean=-0.8, half=2.6)
        ear(p, hx + 3, hy - 4.2, 5 * (1 - tuck * 0.6), P.SNOW_L, inner=P.PINK, lean=0.8, half=2.6)
        p.ellipse(hx, hy, 6.5 * k, 5.5 * k, P.SNOW_L)
    c.ellipse(hx + 2, hy + 2.5, 3.2, 1.5, P.WHITE)
    c.px(hx + 5, hy + 1, P.PINK_D)
    if tuck < 0.7:
        face(c, hx + 1.5, hy - 2.5, eyes=eyes, mouth=mouth, gap=5, nose=P.PINK_D, size=3)


def ice_ball(c: Canvas, x: float, y: float, rad: float, seed: int = 19) -> None:
    ice_coat(c, x, y, rad, rad, 0, 360, seed, length=5)
    with shaded(c, FUR) as p:
        p.ellipse(x + rad * 0.3, y + rad * 0.3, rad * 0.5, rad * 0.42, P.SNOW_L)   # tucked face
    c.px(x + rad * 0.5, y + rad * 0.15, P.BLACK)
    c.px(x + rad * 0.1, y + rad * 0.15, P.BLACK)
    c.px(x + rad * 0.3, y + rad * 0.5, P.PINK_D)


def ice_hedgehog() -> Sprite:
    size, cx, gy = (36, 28), 18, 26
    sprite = Sprite("ice_hedgehog", size, faces_left=True, cx=cx, ground=gy)

    def body(step=0, eyes="open", mouth="w", tuck=0.0, dx=0):
        c = Canvas(*size)
        ice_hedgehog_body(c, cx + dx, gy - (step % 2) * 0.5, step, eyes, mouth, tuck)
        return c.outline(EDGE).img

    def ball(rad, y):
        c = Canvas(*size)
        ice_ball(c, cx, y, rad)
        return c.outline(EDGE).img

    sprite.add("walk", [body(k) for k in range(4)], fps=8)
    sprite.add("curl", [body(0, "shut", "flat", 0.5, -1), ball(7.5, gy - 11), ball(7, gy - 11)], fps=12, loop=False)
    # Rolling: the ball turns and frosty speed streaks trail behind it.
    base = Canvas(36, 36)
    ice_ball(base, 17.5, 17.5, 7)
    roll = []
    for k in range(4):
        spun = Canvas(36, 36)
        spun.paste(base.img.rotate(-90 * k, resample=Image.NEAREST, center=(17, 17)))
        spun.outline(EDGE)
        box = spun.img.getbbox()
        piece = spun.img.crop(box)
        frame = Canvas(*size)
        for i, (sy, ln) in enumerate(((-12, 6), (-8, 8), (-4, 5), (-15, 3))):   # streaks behind (left)
            x0 = cx - (box[2] - box[0]) // 2 + 1 - (k % 2)
            frame.line((max(1, x0 - ln), gy + sy), (x0 - 1, gy + sy), P.FR_ICE_L if i % 2 else P.FR_ICE_GLOW)
            if x0 - ln - 2 >= 1:
                frame.px(x0 - ln - 2, gy + sy, P.WHITE)
        frame.paste(piece, cx - (box[2] - box[0]) // 2 + 2, gy + 2 - (box[3] - box[1]))
        roll.append(frame.img)
    sprite.add("roll", roll, fps=14)
    hurt = body(1, "shut", "open", 0.2, -1)
    sprite.add("hit", hit_frames(hurt, [(cx + 11, gy - 20), (cx - 4, gy - 22), (cx + 13, gy - 9)]), fps=10, loop=False)
    sprite.add("death", dying(body(0, "x", "open"), 5), fps=10, loop=False)
    return sprite


# --- snowman [20x30] + snowball_shot ---------------------------------------------------------------

def snowman_frame(step: int = 0, walk: bool = False, arm: str = "rest", squash: float = 0, eyes: str = "open",
                  mouth: str = "smile", lean: float = 0) -> Image.Image:
    """Two snowballs, a blue beanie with a pompom, a blue scarf, a carrot nose and twig arms.
    arm: rest, back (wound up with a snowball), throw (flung forward), up (both up)."""
    size, x, gy = (44, 44), 20, 41
    c = Canvas(*size)
    hop = ((0, 1.5, 3, 1.5)[step % 4]) if walk else 0
    by = gy - hop
    x += lean
    sq = squash + (0.15 if walk and step % 4 == 0 else 0)
    hx, hy = x + 1, by - 21 + sq * 4

    def twig(start, angle, length, colour=P.BARK_D):
        end = (start[0] + math.cos(math.radians(angle)) * length, start[1] - math.sin(math.radians(angle)) * length)
        c.line(start, end, colour)                                          # a thin forked twig
        mid = (start[0] + (end[0] - start[0]) * 0.6, start[1] + (end[1] - start[1]) * 0.6)
        c.line(mid, (mid[0] + math.cos(math.radians(angle + 45)) * 3, mid[1] - math.sin(math.radians(angle + 45)) * 3),
               colour)
        c.line(end, (end[0] + math.cos(math.radians(angle - 40)) * 2.5, end[1] - math.sin(math.radians(angle - 40)) * 2.5),
               colour)
        c.line(end, (end[0] + math.cos(math.radians(angle + 35)) * 2.5, end[1] - math.sin(math.radians(angle + 35)) * 2.5),
               colour)
        return end

    far = {"rest": 150, "back": 160, "throw": 150, "up": 120}[arm] + (step % 2) * 8
    twig((x - 6, by - 14 + sq * 2), far, 7, P.BARK_DD)
    with shaded(c, FUR, up=2) as p:
        p.ellipse(x, by - 7.5 + sq, 9.5 + sq * 2, 7.5 - sq * 1.5, P.SNOW_L)     # bottom ball
    with shaded(c, FUR, up=2) as p:
        p.ellipse(hx, hy, 7, 6.8, P.SNOW_L)                                   # head
    for k in range(3):                                                        # coal buttons
        c.ellipse(x + 3, by - 12 + k * 3.2 + sq, 0.8, 0.8, P.SLATE)
    with shaded(c, ICE, EDGE, up=2) as p:                                     # blue beanie
        p.ellipse(hx - 0.5, hy - 7, 6.2, 4.5, P.FR_ICE_D)
        p.rect(hx - 7, hy - 5.5, hx + 6.5, hy - 3.5, P.FR_ICE)
        p.rect(0, hy - 3, p.size[0], p.size[1], P.CLEAR)
    for k in range(-6, 7, 2):                                                 # knitted fold
        c.px(hx + k, hy - 4.5, P.FR_ICE_L)
    with shaded(c, FUR, EDGE) as p:
        p.ellipse(hx - 4.5, hy - 12, 2.2, 2, P.WHITE)                         # pompom
    face(c, hx + 1.5, hy - 1, eyes=eyes, mouth=mouth, gap=5, eye=P.BLACK, nose=None, blush=P.PINK, size=3)
    with shaded(c, ORANGE_RAMP, EDGE) as p:                                   # carrot nose
        p.poly([(hx + 4, hy + 2), (hx + 10, hy + 3.5), (hx + 4, hy + 4)], P.ORANGE)
    with shaded(c, ICE, EDGE) as p:                                           # scarf with a hanging end
        p.rect(hx - 6, hy + 5, hx + 5, hy + 7, P.FR_ICE)
        p.rect(hx - 4, hy + 7, hx - 2, hy + 12 - (step % 2), P.FR_ICE)
    c.line((hx - 5, hy + 5), (hx + 4, hy + 5), P.FR_ICE_L)
    c.px(hx - 3, hy + 9, P.FR_ICE_D)
    near = {"rest": 25, "back": 140, "throw": 10, "up": 60}[arm] - (step % 2) * 8
    end = twig((x + 6, by - 13 + sq * 2), near, 8)
    if arm == "back":
        snowball_shape(c, end[0] + 1, end[1] - 1, 3.2)
    return c.outline(EDGE).img


def snowball_shape(c: Canvas, x: float, y: float, r: float) -> None:
    with shaded(c, FUR, EDGE, up=2) as p:
        p.ellipse(x, y, r, r, P.SNOW_L)
    c.px(x - r * 0.4, y - r * 0.4, P.WHITE)


def snowman() -> Sprite:
    size, cx, gy = (44, 44), 20, 41
    sprite = Sprite("snowman", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [snowman_frame(), snowman_frame(1, eyes="shut")], fps=3)
    sprite.add("walk", [snowman_frame(k, walk=True) for k in range(4)], fps=8)
    release = Canvas(*size)
    release.paste(snowman_frame(arm="throw", lean=1, eyes="angry", mouth="open"))
    snowball_shape(release, cx + 17, gy - 20, 3.4)
    sparkle(release, cx + 20, gy - 25, P.FR_ICE_GLOW)
    sprite.add("attack", [snowman_frame(arm="back", lean=-1, eyes="angry", mouth="flat"),
                          snowman_frame(arm="back", lean=-1.5, squash=0.2, eyes="angry", mouth="flat"),
                          release.img, snowman_frame(arm="rest")], fps=8, loop=False)
    hurt = snowman_frame(arm="up", lean=-1, squash=0.25, eyes="shut", mouth="open")
    sprite.add("hit", hit_frames(hurt, [(cx + 10, gy - 33), (cx - 9, gy - 26), (cx + 12, gy - 10)]), fps=10, loop=False)
    sprite.add("death", dying(snowman_frame(arm="up", eyes="x", mouth="open"), 12), fps=10, loop=False)
    return sprite


def snowball_shot() -> Sprite:
    sprite = Sprite("snowball_shot", (10, 10), faces_left=True)
    frames = []
    for k in range(4):
        c = Canvas(10, 10)
        with shaded(c, FUR, up=2) as p:
            p.ellipse(4.5, 4.5, 3.8, 3.8, P.SNOW_L)
        a = k / 4 * math.tau
        c.px(4.5 + math.cos(a) * 2, 4.5 + math.sin(a) * 2, P.SNOW_D)        # a lump turning as it flies
        c.px(3, 3, P.WHITE)
        frames.append(c.outline(EDGE).img)
    sprite.add("fly", frames, fps=12)
    return sprite


# --- icicle plant [18x24] + icicle_bolt ------------------------------------------------------------

def icicle_plant_frame(mode: str = "closed", k: int = 0, eyes: str = "open", mouth: str = "w") -> Image.Image:
    """mode: closed (a tall crystal bud), open (crystal petals spread round a round snowy face), shoot
    (k = 0 charge, 1 fire, 2 recoil)."""
    size, x, gy = (38, 36), 16, 33
    c = Canvas(*size)
    snow_puff(c, x - 5, gy, 5)
    snow_puff(c, x + 5, gy, 4.5)
    with shaded(c, ICE, EDGE) as p:                                           # stem
        p.line((x, gy - 1), (x + 0.5, gy - 9), P.FR_ICE_D, 2)
    crystals(c, [(x - 1, gy - 4, 160, 8, 2.4), (x + 1, gy - 4, 20, 8, 2.4)])  # icy leaves
    by = gy - 17
    glint = k % 2
    if mode == "closed":
        crystals(c, [(x - 2, by + 6, 115, 10, 3), (x + 2, by + 6, 65, 10, 3), (x, by + 7, 90, 16, 4.2)])
        c.px(x - 1, by - 2 - glint * 3, P.WHITE)
        if glint:
            sparkle(c, x + 6, by - 6, P.FR_ICE_GLOW)
        return c.outline(EDGE).img
    spread = {"open": (0.6, 1.0), "shoot": (1.0, 1.1, 0.9)}[mode][k]
    crystals(c, [(x - 4, by + 5, 90 + 62 * spread, 11, 3), (x + 4, by + 5, 90 - 62 * spread, 11, 3),
                 (x - 3, by + 2, 90 + 30 * spread, 11, 2.6), (x + 3, by + 2, 90 - 30 * spread, 10, 2.6)])
    recoil = -1 if mode == "shoot" and k == 1 else 0
    hx, hy = x + 1 + recoil, by - 1
    with shaded(c, FUR, EDGE, up=2) as p:
        ear(p, hx - 3.5, hy - 4.5, 4, P.SNOW_L, inner=P.FR_ICE_L, lean=-0.8, half=2.2)
        ear(p, hx + 3.5, hy - 4.5, 4, P.SNOW_L, inner=P.FR_ICE_L, lean=0.8, half=2.2)
        fluffy(p, hx, hy, 6, 5.5, P.SNOW_L, 53, tufts=10, size=1.2)
    if mode == "shoot":
        eyes, mouth = "angry", ("open" if k < 2 else "flat")
    face(c, hx + 1.5, hy - 2, eyes=eyes, mouth=mouth, gap=5, nose=None, blush=P.FR_ICE_L, size=3)
    out = c.outline(EDGE).img
    if mode == "shoot" and k < 2:                                            # the bolt forms, then leaves
        glow = Canvas(*size)
        if k == 0:
            glow.ellipse(hx + 7, hy + 2, 2, 2, P.FR_ICE_GLOW)
            glow.px(hx + 7, hy + 2, P.WHITE)
            glow.outline(P.FR_ICE)
            sparkle(glow, hx + 10, hy - 2, P.FR_ICE_GLOW)
        else:
            bolt_shape(glow, hx + 8, hy + 2, 0)
            glow.outline(P.FR_ICE_DD)
        out.alpha_composite(glow.img)
    return out


def bolt_shape(c: Canvas, x: float, y: float, k: int) -> None:
    """A horizontal ice bolt about 12x5 whose point is at the right, starting at x."""
    c.poly([(x, y - 1.5), (x + 7, y - 2.5), (x + 11, y), (x + 7, y + 2.5), (x, y + 1.5)], P.FR_ICE_L)
    c.line((x + 1, y - 0.5), (x + 9, y - 0.5), P.WHITE)
    c.line((x + 1, y + 1), (x + 7, y + 1.5), P.FR_ICE)
    c.px(x + 4 + k * 2, y - 1, P.FR_ICE_GLOW)


def icicle_plant() -> Sprite:
    size, cx, gy = (38, 36), 16, 33
    sprite = Sprite("icicle_plant", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("closed", [icicle_plant_frame("closed", 0), icicle_plant_frame("closed", 1)], fps=3)
    sprite.add("open", [icicle_plant_frame("open", 0), icicle_plant_frame("open", 1)], fps=6)
    sprite.add("attack", [icicle_plant_frame("shoot", k) for k in range(3)], fps=8, loop=False)
    hurt = icicle_plant_frame("open", 1, eyes="shut", mouth="open")
    sprite.add("hit", hit_frames(hurt, [(cx + 10, gy - 26), (cx - 9, gy - 22), (cx + 11, gy - 10)]), fps=10, loop=False)
    sprite.add("death", dying(icicle_plant_frame("open", 1, eyes="x", mouth="open"), 9), fps=10, loop=False)
    return sprite


def icicle_bolt() -> Sprite:
    sprite = Sprite("icicle_bolt", (14, 7), faces_left=True)
    frames = []
    for k in range(2):
        c = Canvas(14, 7)
        bolt_shape(c, 2, 3, k)
        c.outline(P.FR_ICE_DD)
        c.px(0, 2 + k * 2, P.FR_ICE_GLOW)                                     # frost trail
        frames.append(c.img)
    sprite.add("fly", frames, fps=10)
    return sprite


# --- mini yeti [30x34] -----------------------------------------------------------------------------

def mini_yeti_frame(step: int = 0, walk: bool = False, swipe: float = 0, eyes: str = "glow", mouth: str = "fangs",
                    lean: float = 0, slump: float = 0) -> Image.Image:
    """A hunched white yeti with long arms, a dark face with golden eyes, and ice-blue fur at its fists and
    feet. swipe: 0 = arms hanging, -1 = arm drawn back, 1 = arm swept forward."""
    size, x, gy = (60, 46), 22, 43
    c = Canvas(*size)
    bob = (step % 2) if walk else 0
    by = gy - bob + slump
    x += lean
    lifts = ((step % 2) * 2, ((step + 1) % 2) * 2) if walk else (0, 0)
    with shaded(c, FUR, EDGE) as p:                                           # far arm behind
        p.line((x - 7, by - 21), (x - 11, by - 6), P.SNOW, 5)
        fluffy(p, x - 11, by - 4, 3, 2.6, P.SNOW, 61, tufts=5, size=1)
    with shaded(c, FUR, EDGE) as p:                                           # short legs
        fluffy(p, x - 6, by - 4 - lifts[0], 4, 4, P.SNOW_L, 63, tufts=6, size=1.1)
        fluffy(p, x + 5, by - 4 - lifts[1], 4, 4, P.SNOW_L, 65, tufts=6, size=1.1)
        p.rect(0, gy + 1, p.size[0], p.size[1], P.CLEAR)
    for fx, lift in ((x - 6, lifts[0]), (x + 5, lifts[1])):                   # icy toes
        c.rect(fx - 2, gy - lift, fx + 2, gy - lift, P.FR_ICE_L)
    with shaded(c, FUR, up=2) as p:
        fluffy(p, x - 2, by - 14, 12, 10.5, P.SNOW_L, 67, tufts=16, size=1.8)    # shaggy body
        fluffy(p, x - 3, by - 23, 9, 7, P.SNOW_L, 68, tufts=12, size=1.8)        # hunched shoulders
        fluffy(p, x + 5.5, by - 25, 8.5, 7.5, P.SNOW_L, 69, tufts=13, size=1.6)  # hooded head
    for a, b in (((x - 9, by - 20), (x - 7, by - 13)), ((x - 4, by - 11), (x - 3, by - 5)),
                 ((x - 1, by - 19), (x, by - 14)), ((x - 11, by - 12), (x - 10, by - 7))):
        c.line(a, b, P.SNOW)                                                  # fur strands
    with shaded(c, ROCK, EDGE) as p:                                          # dark face
        p.ellipse(x + 7, by - 23.5, 5, 4.8, P.FR_ROCK_D)
    c.ellipse(x + 8, by - 20.5, 3.4, 1.8, P.FR_ROCK)                          # lighter muzzle
    c.rect(x + 4, by - 27, x + 10, by - 27, P.FR_ROCK_DD)                     # heavy brow
    for ex in (x + 5, x + 9):
        if eyes == "glow":
            c.rect(ex, by - 26, ex + 1, by - 25, P.GOLD)
            c.px(ex + 1, by - 26, P.YELLOW)
        elif eyes == "angry":
            c.rect(ex, by - 25, ex + 1, by - 25, P.GOLD)
            c.px(ex + (1 if ex == x + 5 else 0), by - 26, P.GOLD)
        elif eyes == "shut":
            c.rect(ex, by - 25, ex + 1, by - 25, P.FR_ROCK_DD)
        elif eyes == "x":
            c.px(ex, by - 26, P.GOLD)
            c.px(ex + 1, by - 25, P.GOLD)
            c.px(ex + 1, by - 26, P.GOLD_D)
            c.px(ex, by - 25, P.GOLD_D)
    if mouth == "fangs":
        c.rect(x + 6, by - 20.5, x + 10, by - 20.5, P.FR_ROCK_DD)
        c.px(x + 6, by - 20, P.WHITE)
        c.px(x + 10, by - 20, P.WHITE)
    elif mouth == "open":
        c.ellipse(x + 8, by - 20, 1.8, 1.3, P.MAROON)
        c.px(x + 7, by - 21, P.WHITE)
        c.px(x + 9, by - 21, P.WHITE)
    else:
        c.rect(x + 6, by - 20.5, x + 10, by - 20.5, P.FR_ROCK_DD)
    # Near arm: a long shaggy arm, knuckles down at rest, ending in a fist rimed with ice.
    sh = (x + 6, by - 16)
    if swipe > 0:
        fist = (x + 18 + swipe * 3, by - 22)
    elif swipe < 0:
        fist = (x - 3, by - 28)
    else:
        fist = (x + 13, gy - 4.5)
    with shaded(c, FUR, EDGE) as p:
        p.line(sh, fist, P.SNOW_L, 6)
        fluffy(p, fist[0], fist[1], 3.4, 3.2, P.SNOW_L, 71, tufts=6, size=1.2)
    for dx in (-1, 1, 3):                                                     # icy claws
        c.px(fist[0] + dx, fist[1] + 2.5, P.FR_ICE_L)
    c.px(fist[0] + 2, fist[1] - 2, P.FR_ICE_GLOW)
    return c.outline(EDGE).img


def mini_yeti() -> Sprite:
    size, cx, gy = (60, 46), 22, 43
    sprite = Sprite("mini_yeti", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [mini_yeti_frame(), mini_yeti_frame(slump=1, eyes="shut")], fps=3)
    sprite.add("walk", [mini_yeti_frame(k, walk=True) for k in range(4)], fps=6)
    arc = arc_layer(size, cx + 20, gy - 18, 11, -70, 80, 3)
    sprite.add("attack", [mini_yeti_frame(swipe=-1, lean=-1, eyes="angry"),
                          mini_yeti_frame(swipe=-1, lean=-2, eyes="angry", mouth="open"),
                          with_arc(mini_yeti_frame(swipe=1, lean=1, eyes="angry", mouth="open"), arc,
                                   [(cx + 31, gy - 32), (cx + 28, gy - 4)]),
                          mini_yeti_frame(swipe=0.4)], fps=8, loop=False)
    hurt = mini_yeti_frame(lean=-2, eyes="shut", mouth="open")
    sprite.add("hit", hit_frames(hurt, [(cx + 14, gy - 36), (cx - 13, gy - 30), (cx + 16, gy - 12)]), fps=10, loop=False)
    sprite.add("death", dying(mini_yeti_frame(slump=2, eyes="x", mouth="open"), 8), fps=10, loop=False)
    return sprite


def build() -> list[Sprite]:
    return [ice_slime(), snow_cat(), ice_bat(), ice_golem(), penguin_soldier(), spear(), snowy_owl(), icicle_shot(),
            ice_hedgehog(), snowman(), snowball_shot(), icicle_plant(), icicle_bolt(), mini_yeti()]
