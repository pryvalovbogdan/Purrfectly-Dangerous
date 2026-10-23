"""Sakura world, level 3 (night) critters (from `docs/concept/Sakura World Level 3 Enemy Sprites.png`): the shadow
slime, samurai ronin, oni cat, tengu crow and spirit wisp, and the wisp's fireball and the oni's thrown rock.

Drawn facing right with light from the top-left and mirrored on export, with the level 1 helpers from
`sakura_critters.py` (blossoms, petals, petal hurts and deaths). The level is a dark blue-violet night, so the dark
critters get a very dark outline (`SN_LINE`) and a magenta moon-rim along their back and top (`moonrim`), and every
effect is a glowing magenta crescent, streak or flame. Gameplay hitboxes (w x h, at the feet) are noted per sprite."""
from __future__ import annotations

import math

from PIL import Image

import palette as P
from characters.sakura_critters import blossom, crescent, hurt_frames, petal, petals, scatter
from characters.sakura_world import recolour
from critters import ear, ramp, shaded, sparkle
from draw import Canvas, noise, see_through, tint, vanish
from sprite import Sprite

EDGE = P.SN_LINE
VIOLET = ramp((P.SN_VIOLET_L, P.SN_VIOLET, P.SN_VIOLET_D), (P.SN_VIOLET, P.SN_VIOLET_D, P.SN_VIOLET_DD))
FUR = ramp((P.SN_FUR_L, P.SN_FUR, P.SN_FUR_D), (P.SN_FUR, P.SN_FUR_D, P.SN_VIOLET_DD))
MASK = ramp((P.WHITE, P.SN_MASK, P.SN_MASK_D))
HAT = ramp((P.BARK_L, P.BARK, P.BARK_D))
WOOD = ramp((P.BARK_L, P.BARK, P.BARK_D), (P.BARK, P.BARK_D, P.BARK_DD))
LACQUER = ramp((P.CAPE_L, P.SK_LACQUER, P.SK_LACQUER_D))
HORN = ramp((P.SN_EYE_L, P.SN_HORN, P.SN_HORN_D))
STEEL = ramp((P.WHITE, P.GREY_L, P.GREY))
FLAME = ramp((P.SK_PINK_L, P.SN_MAGENTA, P.SN_MAGENTA_D), (P.WHITE, P.SK_PINK, P.SN_MAGENTA))
ROCK = ramp((P.SN_ROCK_L, P.SN_ROCK, P.SN_ROCK_D))
# The level-1 pink crescent and petals, turned magenta for the night.
MAGENTA = {P.SK_PINK: P.SN_MAGENTA, P.SK_PINK_L: P.SN_MAGENTA_L, P.SK_PINK_D: P.SN_MAGENTA_D}
DARK = {c[:3] for c in (P.SN_VIOLET, P.SN_VIOLET_D, P.SN_VIOLET_DD, P.SN_VIOLET_L, P.SN_FUR, P.SN_FUR_D, P.SN_FUR_L)}


def slash(size, cx: float, cy: float, r: float, a0: float, a1: float, thick: float) -> Image.Image:
    return recolour(crescent(size, cx, cy, r, a0, a1, thick), MAGENTA)


def moonrim(c: Canvas) -> Canvas:
    """Magenta moonlight along the back and top: every dark fur or body pixel with empty space above it or behind
    it (to its left) turns magenta. Run before the outline."""
    img = c.img
    px = img.load()
    w, h = img.size
    hits = []
    for y in range(h):
        for x in range(w):
            if px[x, y][3] and px[x, y][:3] in DARK:
                above = y == 0 or not px[x, y - 1][3]
                behind = x == 0 or not px[x - 1, y][3]
                if above or behind:
                    hits.append((x, y, P.SN_MAGENTA if above and behind else P.SN_MAGENTA_D))
    for x, y, col in hits:
        px[x, y] = col
    return c


def red_eyes(c: Canvas, x: float, y: float, gap: int, mood: str = "angry", size: int = 2) -> None:
    """Glowing red eyes, three-quarters from the right: the near eye at (x, y), the far one `gap` to its left.
    mood: angry (slanted brows), shut (a line), x (crosses), wide (round, no brow)."""
    for k, ex in enumerate((x - gap, x)):
        if mood == "x":
            for dx, dy in ((0, 0), (2, 0), (1, 1), (0, 2), (2, 2)):
                c.px(ex + dx, y + dy - 1, P.SN_EYE)
        elif mood == "shut":
            c.rect(ex, y + 1, ex + size, y + 1, P.SN_EYE)
        else:
            c.rect(ex, y, ex + size, y + size - 1, P.SN_EYE)
            c.px(ex + (1 if k else size - 1), y + size - 1, P.SN_EYE_L)
            if mood == "angry":                                         # brow low over the inner corner
                if k:
                    c.line((ex - 1, y), (ex + size, y - 1), EDGE)
                else:
                    c.line((ex + size + 1, y), (ex, y - 1), EDGE)


def aura(size, x: float, y: float, rx: float, ry: float, alpha: int = 70, colour=P.SN_MAGENTA) -> Image.Image:
    c = Canvas(*size)
    c.ellipse(x, y, rx, ry, colour)
    c.ellipse(x, y, rx * 0.65, ry * 0.65, colour)
    img = see_through(c.img, alpha)
    inner = Canvas(*size)
    inner.ellipse(x, y, rx * 0.6, ry * 0.6, colour)
    img.alpha_composite(see_through(inner.img, alpha // 2))
    return img


def under(base: Image.Image, top: Image.Image) -> Image.Image:
    out = base.copy()
    out.alpha_composite(top)
    return out


def streaks(size, x: float, y: float, n: int, length: float, k: int, seed: int, slope: float = 0.0) -> Image.Image:
    """Magenta speed streaks trailing left from (x, y), with petals."""
    c = Canvas(*size)
    for i in range(n):
        yy = y + i * 3 - n
        c.line((x - length + i * 2, yy - slope * length), (x - 2, yy), P.SN_MAGENTA if i % 2 else P.SN_MAGENTA_L)
    petals(c, x - length * 0.6, y, 4, 3, seed + k, k)
    return c.img


def magenta_fireball(size, x: float, y: float, r: float, k: int, tail: float = 7) -> Image.Image:
    """A glowing pink-magenta fireball flying right: a soft halo, flame licks streaming back, a white-hot core."""
    c = Canvas(*size)
    for i in range(int(tail)):
        t = i / tail
        rr = r * (1 - t) * 0.95
        if rr < 0.4:
            continue
        c.ellipse(x - 1 - i, y + math.sin(i * 1.3 + k * 1.6) * 0.9 * t, rr, rr * 0.8,
                  P.SN_MAGENTA if t < 0.45 else P.SN_MAGENTA_D)
    c.ellipse(x, y, r, r, P.SN_MAGENTA)
    c.ellipse(x + 0.3, y - 0.3, r * 0.7, r * 0.7, P.SK_PINK_L)
    c.ellipse(x + 0.5, y - 0.5, max(0.6, r * 0.35), max(0.6, r * 0.35), P.WHITE)
    c.outline(P.SN_MAGENTA_D)
    return under(aura(size, x - 1, y, r + 2.5, r + 1.5, 60), c.img)


# --- shadow slime [20x14] --------------------------------------------------------------------------

SLIME = (40, 34), 18, 30


def slime_frame(sx: float = 1.0, sy: float = 1.0, lift: float = 0, lean: float = 0, eyes: str = "angry", k: int = 0,
                mouth: bool = False) -> Image.Image:
    """A possessed slime: a dark violet dome with drips at its foot, magenta glitter swirling inside, glowing red
    angry eyes and a pink blossom on its crown."""
    size, cx, gy = SLIME
    c = Canvas(*size)
    base = gy - lift
    height = 14 * sy
    rx = 10.5 * sx
    x = cx + lean
    with shaded(c, VIOLET, up=2, down=1) as p:
        ry = height * 0.78
        p.ellipse(x, base - height + ry, rx, ry, P.SN_VIOLET)                 # a dome, cut flat at the foot
        p.rect(0, base + 1, p.size[0], p.size[1], P.CLEAR)
        p.ellipse(x - rx + 1, base - 1, 2.6, 1, P.SN_VIOLET)                  # drips spreading at the foot
        p.ellipse(x + rx - 1, base - 1, 2.6, 1, P.SN_VIOLET)
    rnd = noise(1301 + k)
    for i in range(6):                                                        # the possession swirling inside
        a = i / 6 * math.tau + k * 0.5
        c.px(x - 1 + math.cos(a) * rx * 0.55, base - height * 0.45 + math.sin(a) * height * 0.28,
             P.SN_MAGENTA_D if i % 2 else P.SN_VIOLET_DD)
    c.px(x - 3 + rnd() * 6, base - 3, P.SN_MAGENTA)
    top = base - height
    c.rect(x - rx * 0.6, top + 3, x - rx * 0.6 + 1, top + 4, P.SN_MAGENTA_L)  # gloss
    c.px(x - rx * 0.4, top + 2, P.SN_MAGENTA_L)
    red_eyes(c, x + 3, base - height * 0.55, 6, eyes)
    if mouth:
        my = base - height * 0.55 + 4
        c.line((x - 2, my), (x + 3, my), EDGE)
        c.px(x - 1, my - 1, P.WHITE)
        c.px(x + 2, my - 1, P.WHITE)
    blossom(c, x + 1, top, 2.7, turn=k * 0.25)
    moonrim(c)
    return c.outline(EDGE).img


def shadow_slime() -> Sprite:
    size, cx, gy = SLIME
    sprite = Sprite("shadow_slime", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [slime_frame(), slime_frame(1.05, 0.93, k=1)], fps=3)
    sprite.add("walk", [slime_frame(1.12, 0.84), slime_frame(0.92, 1.1, 2, 0.5, k=1), slime_frame(0.96, 1.05, 3, k=2),
                        slime_frame(1.04, 0.95, 1, -0.5, k=3)], fps=8)
    crouch = slime_frame(1.18, 0.78, eyes="angry", mouth=True)
    leap = under(streaks(size, cx - 5, gy - 9, 4, 10, 1, 1310, slope=0.15),
                 slime_frame(0.85, 1.12, 6, 2, mouth=True, k=1))
    leap.alpha_composite(slash(size, cx + 3, gy - 13, 12, -60, 65, 1.8))
    sprite.add("attack", [crouch, leap, slime_frame(1.14, 0.86, 0, 1, k=2)], fps=8, loop=False)
    hurt = slime_frame(1.1, 0.9, eyes="shut", mouth=True)
    sprite.add("hurt", hurt_frames(hurt, [(cx - 10, gy - 16), (cx + 11, gy - 14), (cx + 1, gy - 24)]), fps=10, loop=False)
    sprite.add("death", scatter(slime_frame(1.2, 0.6, eyes="x"), cx, gy, 1311, depth=3), fps=8, loop=False)
    return sprite


# --- samurai ronin [18x22] -------------------------------------------------------------------------

RONIN = (52, 40), 20, 37


def katana(c: Canvas, grip, tip) -> None:
    """A katana from its grip to its tip: a red-wrapped hilt, a gold guard and a bright curved-edge blade."""
    gx, gy_ = grip
    tx, ty = tip
    length = math.hypot(tx - gx, ty - gy_)
    ux, uy = (tx - gx) / length, (ty - gy_) / length
    with shaded(c, STEEL) as p:
        p.line((gx + ux * 2, gy_ + uy * 2), (tx, ty), P.GREY_L, 2)
    c.line((gx + ux * 3 - uy * 0.5, gy_ + uy * 3 + ux * 0.5), (tx - ux, ty - uy), P.WHITE)
    c.line((gx - ux * 3, gy_ - uy * 3), (gx, gy_), P.SK_LACQUER_D, 2)
    c.rect(gx + ux * 1.5 - 1, gy_ + uy * 1.5 - 1, gx + ux * 1.5, gy_ + uy * 1.5, P.GOLD)


def ronin_frame(step: int = 0, walk: bool = False, sword: str = "rest", eyes: str = "angry", lean: float = 0,
                crouch: float = 0) -> Image.Image:
    """A dark cat ronin: a wide red-brown straw hat with a blossom, a pale cat face with dark eyes, a red scarf
    streaming back, a dark violet gi and hakama, a thin tail. sword: rest (held forward, low), raised (over the
    shoulder), slash (swept out front), follow (pointing down in front)."""
    size, x, gy = RONIN
    c = Canvas(*size)
    x += lean
    by = gy + crouch
    lifts = ((0, 2, 0, 0)[step % 4], (0, 0, 0, 2)[step % 4]) if walk else (0, 0)
    strides = ((-1, 1, 0, -1)[step % 4], (1, -1, 0, 1)[step % 4]) if walk else (0, 0)
    with shaded(c, FUR, EDGE) as p:                                           # tail curling up behind
        pts = [(x - 5, by - 7), (x - 9, by - 9), (x - 11, by - 13), (x - 10, by - 16 + (step % 2))]
        for a, b in zip(pts, pts[1:]):
            p.line(a, b, P.SN_FUR, 2)
    with shaded(c, LACQUER, EDGE) as p:                                       # scarf tail, flying
        wave = (0, 1, 0, -1)[step % 4]
        p.poly([(x - 2, by - 17), (x - 10, by - 17 + wave), (x - 15, by - 14 - wave), (x - 13, by - 12 + wave),
                (x - 8, by - 14), (x - 2, by - 14)], P.SK_LACQUER)
    with shaded(c, VIOLET, EDGE) as p:                                        # hakama legs
        p.poly([(x - 4, by - 8), (x - 0.5, by - 8), (x - 1 + strides[0], gy - 1 - lifts[0]),
                (x - 6 + strides[0], gy - 1 - lifts[0])], P.SN_VIOLET_D)
        p.poly([(x + 0.5, by - 8), (x + 4, by - 8), (x + 6 + strides[1], gy - 1 - lifts[1]),
                (x + 1 + strides[1], gy - 1 - lifts[1])], P.SN_VIOLET)
        p.rect(x - 6 + strides[0], gy - 1 - lifts[0], x - 2 + strides[0], gy - lifts[0], P.SN_FUR_D)
        p.rect(x + 2 + strides[1], gy - 1 - lifts[1], x + 6 + strides[1], gy - lifts[1], P.SN_FUR_D)
    with shaded(c, VIOLET, up=2) as p:                                        # gi
        p.ellipse(x, by - 12, 6, 5.5, P.SN_VIOLET)
    c.line((x - 2, by - 16), (x + 3, by - 9), P.SN_VIOLET_D)                  # lapel
    c.rect(x - 5, by - 9, x + 5, by - 8, P.SN_MAGENTA_D)                      # obi
    hx, hy = x + 3, by - 21
    with shaded(c, FUR, EDGE, up=2) as p:                                     # head
        p.ellipse(hx, hy, 6, 5, P.SN_FUR)
    with shaded(c, MASK) as p:                                                # pale face
        p.ellipse(hx + 2.5, hy + 1, 4, 3.5, P.SN_MASK)
    if eyes == "x":
        for ex in (hx, hx + 4):
            c.px(ex - 0.5, hy - 0.5, EDGE)
            c.px(ex + 0.5, hy + 0.5, EDGE)
            c.px(ex + 0.5, hy - 0.5, EDGE)
            c.px(ex - 0.5, hy + 0.5, EDGE)
    elif eyes == "shut":
        c.rect(hx - 0.5, hy, hx + 0.5, hy, EDGE)
        c.rect(hx + 3.5, hy, hx + 4.5, hy, EDGE)
    else:
        c.rect(hx - 0.5, hy - 0.5, hx + 0.5, hy + 0.5, EDGE)
        c.rect(hx + 3.5, hy - 0.5, hx + 4.5, hy + 0.5, EDGE)
        c.px(hx + 4.5, hy - 0.5, P.SN_EYE)
        if eyes == "angry":
            c.line((hx - 1, hy - 2), (hx + 1, hy - 1), EDGE)
            c.line((hx + 3, hy - 1), (hx + 5, hy - 2), EDGE)
    c.px(hx + 6, hy + 1.5, P.SK_PINK_D)                                       # nose
    c.line((hx + 4, hy + 3), (hx + 5.5, hy + 3), EDGE)
    with shaded(c, LACQUER, EDGE) as p:                                       # scarf at the neck
        p.rect(hx - 5, hy + 4, hx + 3, hy + 5.5, P.SK_LACQUER)
    with shaded(c, HAT, EDGE, up=2) as p:                                     # wide conical straw hat
        p.poly([(hx - 12, hy - 2.5), (hx - 1, hy - 10), (hx + 2, hy - 10), (hx + 12, hy - 2), (hx + 10, hy - 1),
                (hx - 10, hy - 1.5)], P.BARK)
        p.ellipse(hx + 0.5, hy - 10.5, 1.5, 1.2, P.BARK_D)
    for i in range(-10, 11, 3):                                               # weave
        c.px(hx + i, hy - 2.5 - (10 - abs(i)) * 0.7, P.BARK_D)
    c.line((hx - 11, hy - 2), (hx + 11, hy - 1.5), P.BARK_DD)                 # brim shadow
    blossom(c, hx - 3, hy - 7.5, 2.2, turn=step * 0.2)
    grip = {"rest": (x + 6, by - 10), "raised": (x + 2, by - 17), "slash": (x + 7, by - 13),
            "follow": (x + 6, by - 9)}[sword]
    tip = {"rest": (x + 22, by - 6), "raised": (x - 9, by - 30), "slash": (x + 24, by - 15),
           "follow": (x + 18, gy - 1)}[sword]
    katana(c, grip, tip)
    with shaded(c, FUR, EDGE) as p:                                           # near paw on the hilt
        p.ellipse(grip[0], grip[1], 1.8, 1.6, P.SN_FUR)
    moonrim(c)
    return c.outline(EDGE).img


def samurai_ronin() -> Sprite:
    size, cx, gy = RONIN
    sprite = Sprite("samurai_ronin", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [ronin_frame(), ronin_frame(1, crouch=0.6, eyes="open")], fps=3)
    sprite.add("walk", [ronin_frame(k, walk=True) for k in range(4)], fps=8)
    cut = ronin_frame(sword="slash", lean=2)
    cut = under(streaks(size, cx - 2, gy - 12, 3, 10, 2, 1320), cut)
    cut.alpha_composite(slash(size, cx + 13, gy - 16, 13, -75, 80, 2.4))
    sprite.add("attack", [ronin_frame(sword="raised", lean=-1, crouch=1), ronin_frame(sword="raised", lean=-1.5, crouch=2),
                          cut, ronin_frame(sword="follow", lean=1, crouch=1)], fps=10, loop=False)
    hurt = ronin_frame(eyes="shut", lean=-1.5)
    sprite.add("hurt", hurt_frames(hurt, [(cx + 13, gy - 28), (cx - 10, gy - 24), (cx + 14, gy - 8)]), fps=10, loop=False)
    sprite.add("death", scatter(ronin_frame(eyes="x", sword="follow", crouch=3), cx, gy, 1321, depth=5), fps=8,
               loop=False)
    return sprite


# --- oni cat [26x30] -------------------------------------------------------------------------------

ONI = (76, 56), 30, 52


def tube(c: Canvas, a, b, rad: float, colour) -> None:
    """A rounded limb from a to b: discs stamped along the segment."""
    steps = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1])))
    for i in range(steps + 1):
        t = i / steps
        c.ellipse(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, rad, rad, colour)


def club(c: Canvas, grip, angle: float, length: float = 20) -> None:
    """A studded kanabo from the grip: `angle` 0 points straight up, positive leans it forward (clockwise). A
    magenta-wrapped handle, a thick dark-wood head with steel studs and pink blossoms tied on."""
    gx, gy_ = grip
    ux, uy = math.sin(math.radians(angle)), -math.cos(math.radians(angle))
    nx, ny = -uy, ux
    pts = []
    for t, w in ((-0.15, 1.2), (0.25, 1.6), (1.0, 3.6)):
        pts.append((gx + ux * length * t + nx * w, gy_ + uy * length * t + ny * w))
    for t, w in ((1.0, 3.6), (0.25, 1.6), (-0.15, 1.2)):
        pts.append((gx + ux * length * t - nx * w, gy_ + uy * length * t - ny * w))
    with shaded(c, WOOD, EDGE) as p:
        p.poly(pts, P.BARK)
        p.ellipse(gx + ux * length, gy_ + uy * length, 3.6, 3.6, P.BARK)
    c.line((gx - ux * 3, gy_ - uy * 3), (gx + ux * 3, gy_ + uy * 3), P.SN_MAGENTA_D, 2)   # wrapped handle
    for t in (0.45, 0.62, 0.8, 0.96):                                                     # studs
        for side in (-1, 1):
            w = 1.6 + (t - 0.25) * 2.6
            c.px(gx + ux * length * t + nx * w * 0.55 * side, gy_ + uy * length * t + ny * w * 0.55 * side, P.GREY_L)
    blossom(c, gx + ux * length * 0.55 + nx * 2.5, gy_ + uy * length * 0.55 + ny * 2.5, 1.8, turn=angle * 0.02)
    blossom(c, gx + ux * length * 0.85 - nx * 2.8, gy_ + uy * length * 0.85 - ny * 2.8, 1.6, turn=angle * 0.03)


def oni_frame(step: int = 0, walk: bool = False, pose: str = "rest", eyes: str = "angry", lean: float = 0,
              crouch: float = 0, mouth: str = "fangs") -> Image.Image:
    """A big, hunched, shaggy dark oni cat: two pink-red horns, a white oni mask face with red markings, glowing
    red eyes and fangs, a necklace of big red prayer beads, a red loincloth on a gold rope, heavy paws, a thick
    tail, and a studded kanabo club. pose: rest (club held up behind the head), raise (club high and back),
    swing (club swept forward), slam (club down on the ground in front)."""
    size, x, gy = ONI
    c = Canvas(*size)
    x += lean
    by = gy + crouch
    lifts = ((0, 2, 0, 0)[step % 4], (0, 0, 0, 2)[step % 4]) if walk else (0, 0)
    by += (0, 1, 0, 1)[step % 4] if walk else 0
    hx, hy = x + 10, by - 30
    grip, angle = {"rest": ((x + 2, by - 18), -32), "raise": ((x + 1, by - 33), -72),
                   "swing": ((x + 17, by - 18), 96), "slam": ((x + 17, by - 13), 112)}[pose]
    with shaded(c, FUR, EDGE) as p:                                           # thick tail behind
        p.line((x - 13, by - 12), (x - 19, by - 15), P.SN_FUR, 3)
        p.line((x - 19, by - 15), (x - 21, by - 22 + (step % 2)), P.SN_FUR, 3)
    far_hand = {"rest": (x + 14, by - 9), "raise": (x + 16, by - 12), "swing": (x + 14, by - 18),
                "slam": (x + 13, by - 11)}[pose]
    with shaded(c, FUR, EDGE) as p:                                           # far arm, a fist out front
        tube(p, (x + 2, by - 22), far_hand, 2.2, P.SN_FUR_D)
        p.ellipse(far_hand[0], far_hand[1], 2.6, 2.4, P.SN_FUR_D)
    with shaded(c, FUR, EDGE) as p:                                           # short legs, big paws
        p.rect(x - 11, by - 11, x - 4, gy - 2 - lifts[0], P.SN_FUR_D)
        p.rect(x + 2, by - 11, x + 9, gy - 2 - lifts[1], P.SN_FUR)
        p.ellipse(x - 6.5, gy - 1.5 - lifts[0], 4.5, 1.8, P.SN_FUR_D)
        p.ellipse(x + 5.5, gy - 1.5 - lifts[1], 4.5, 1.8, P.SN_FUR)
    for dx, lift in ((-4, lifts[0]), (-2, lifts[0]), (8, lifts[1]), (10, lifts[1])):
        c.px(x + dx - 1, gy - lift, P.SN_MASK_D)                              # claws
    with shaded(c, FUR, up=2) as p:                                           # big hunched body, shaggy back
        p.ellipse(x, by - 19, 15.5, 12, P.SN_FUR)
        for i in range(6):
            a = math.radians(120 + i * 18)
            p.ellipse(x + math.cos(a) * 14.5, by - 19 - math.sin(a) * 11.5, 2.6, 2.6, P.SN_FUR)
    with shaded(c, FUR) as p:                                                 # lighter chest
        p.ellipse(x + 7, by - 15, 6.5, 6, P.SN_FUR_L)
    with shaded(c, LACQUER, EDGE) as p:                                       # loincloth
        p.poly([(x - 13, by - 11), (x + 13, by - 11), (x + 12, by - 7), (x - 12, by - 7)], P.SK_LACQUER_D)
        p.poly([(x + 3, by - 8), (x + 9, by - 8), (x + 8, by - 2), (x + 4, by - 2)], P.SK_LACQUER)
    c.rect(x - 13, by - 12, x + 13, by - 11, P.GOLD_D)                        # rope belt
    c.px(x + 6, by - 12, P.GOLD)
    if pose in ("rest", "raise"):
        club(c, grip, angle)
    with shaded(c, HORN, EDGE) as p:                                          # horns, curving out
        p.poly([(hx - 5.5, hy - 7), (hx - 1.5, hy - 8.5), (hx - 3, hy - 12.5), (hx - 6.5, hy - 16.5), (hx - 6, hy - 11.5)],
               P.SN_HORN)
        p.poly([(hx + 2, hy - 8.5), (hx + 6, hy - 7), (hx + 6.5, hy - 11.5), (hx + 5.5, hy - 16.5), (hx + 3, hy - 12.5)],
               P.SN_HORN)
    c.px(hx - 6.5, hy - 15.5, P.SN_EYE_L)
    c.px(hx + 5.5, hy - 15.5, P.SN_EYE_L)
    with shaded(c, FUR, EDGE, up=2) as p:                                     # big head with a shaggy mane
        ear(p, hx - 9, hy - 3, 5, P.SN_FUR, inner=P.SN_VIOLET_D, lean=-2, half=2.6)
        ear(p, hx + 8, hy - 4, 4.5, P.SN_FUR, inner=P.SN_VIOLET_D, lean=1.5, half=2.4)
        p.ellipse(hx, hy, 10.5, 9.5, P.SN_FUR)
        for i in range(5):
            a = math.radians(110 + i * 28)
            p.ellipse(hx + math.cos(a) * 10, hy - math.sin(a) * 9, 2.4, 2.4, P.SN_FUR)
    with shaded(c, MASK, EDGE, up=2) as p:                                    # the white oni mask
        p.ellipse(hx + 3.5, hy + 1, 6, 6, P.SN_MASK)
        p.ellipse(hx + 7.5, hy + 3.5, 2.5, 2, P.SN_MASK)
    c.line((hx + 1, hy - 4), (hx + 3, hy - 2), P.SK_LACQUER)                  # red mask markings
    c.line((hx + 7, hy - 4), (hx + 6, hy - 2), P.SK_LACQUER)
    c.line((hx, hy + 3), (hx + 1, hy + 5), P.SK_LACQUER)
    if eyes in ("x", "shut"):
        red_eyes(c, hx + 6, hy - 1, 4, eyes)
    else:
        c.rect(hx + 1, hy - 1, hx + 3, hy + 1, EDGE)
        c.rect(hx + 6, hy - 1, hx + 8, hy + 1, EDGE)
        c.rect(hx + 2, hy, hx + 3, hy + 1, P.SN_EYE)
        c.rect(hx + 6, hy, hx + 7, hy + 1, P.SN_EYE)
        c.px(hx + 6, hy, P.SN_EYE_L)
        if eyes == "angry":                                                   # heavy red brows
            c.line((hx, hy - 3), (hx + 3, hy - 1), P.SK_LACQUER_D)
            c.line((hx, hy - 2), (hx + 3, hy - 1), EDGE)
            c.line((hx + 6, hy - 1), (hx + 9, hy - 3), P.SK_LACQUER_D)
            c.line((hx + 6, hy - 1), (hx + 9, hy - 2), EDGE)
    c.px(hx + 9, hy + 2.5, P.SK_PINK_D)                                       # nose
    if mouth == "fangs":
        c.line((hx + 3, hy + 5), (hx + 9, hy + 5), EDGE)
        c.px(hx + 4, hy + 6, P.WHITE)
        c.px(hx + 8, hy + 6, P.WHITE)
    else:                                                                     # roaring
        c.rect(hx + 4, hy + 4.5, hx + 9, hy + 6.5, EDGE)
        c.rect(hx + 5, hy + 5.5, hx + 8, hy + 6.5, P.SK_LACQUER_D)
        c.px(hx + 4, hy + 4.5, P.WHITE)
        c.px(hx + 9, hy + 4.5, P.WHITE)
    for i in range(6):                                                        # big prayer beads round the neck
        t = i / 5
        bx = x - 1 + t * 18
        bead_y = by - 22 + math.sin(t * math.pi) * 4
        c.ellipse(bx, bead_y, 1.9, 1.9, P.SK_LACQUER_D)
        c.ellipse(bx - 0.3, bead_y - 0.3, 1.3, 1.3, P.SN_MAGENTA if i == 3 else P.SK_LACQUER)
        c.px(bx - 0.6, bead_y - 0.6, P.SN_MAGENTA_L if i == 3 else P.CAPE_L)
    blossom(c, hx - 2, hy - 9, 2.2, turn=step * 0.2)
    if pose in ("swing", "slam"):
        club(c, grip, angle)
    with shaded(c, FUR, EDGE) as p:                                           # near arm and paw on the grip
        tube(p, (x + 4, by - 21), grip, 2.6, P.SN_FUR)
        p.ellipse(grip[0], grip[1], 3, 2.6, P.SN_FUR)
    moonrim(c)
    return c.outline(EDGE).img


def impact(size, x: float, gy: float, k: int) -> Image.Image:
    """Magenta ground burst and petals where the club lands."""
    c = Canvas(*size)
    for i, (dx, h) in enumerate(((-6, 4), (-3, 7), (0, 9), (3, 6), (6, 3))):
        c.poly([(x + dx - 1.2, gy), (x + dx + 1.2, gy), (x + dx + dx * 0.25, gy - h)],
               P.SN_MAGENTA if i % 2 else P.SN_MAGENTA_L)
    c.outline(P.SN_MAGENTA_D)
    petals(c, x, gy - 8, 7, 5, 1340 + k, k)
    return c.img


def oni_cat() -> Sprite:
    size, cx, gy = ONI
    sprite = Sprite("oni_cat", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [oni_frame(), oni_frame(1, crouch=0.6, eyes="open")], fps=3)
    sprite.add("walk", [oni_frame(k, walk=True) for k in range(4)], fps=7)
    swing = oni_frame(pose="swing", lean=1, mouth="roar")
    swing = under(slash(size, cx + 12, gy - 20, 20, 100, -35, 3.2), swing)
    slam = oni_frame(pose="slam", lean=2, crouch=1)
    slam.alpha_composite(impact(size, cx + 34, gy, 0))
    sprite.add("attack", [oni_frame(pose="raise", lean=-1, crouch=1, mouth="roar"),
                          oni_frame(pose="raise", lean=-2, crouch=2, mouth="roar"), swing, slam],
               fps=9, loop=False)
    hurt = oni_frame(eyes="shut", lean=-2, mouth="roar")
    sprite.add("hurt", hurt_frames(hurt, [(cx + 14, gy - 46), (cx - 14, gy - 34), (cx + 18, gy - 12)]), fps=10,
               loop=False)
    sprite.add("death", scatter(oni_frame(eyes="x", pose="slam", crouch=3, mouth="roar"), cx, gy, 1341, depth=6),
               fps=8, loop=False)
    return sprite


def oni_rock() -> Sprite:
    """12x12: a dark slate rock about 10x10 with a magenta rim, a glint and two petals, tumbling as it flies."""
    sprite = Sprite("oni_rock", (12, 12), faces_left=True)
    shape = [(-4, -1), (-2, -4), (2, -4), (4.5, -1), (3.5, 3), (0, 4.5), (-3.5, 3)]
    frames = []
    for k in range(4):
        c = Canvas(12, 12)
        a = k * math.pi / 2 + 0.3
        pts = [(5.5 + px * math.cos(a) - py * math.sin(a), 5.5 + px * math.sin(a) + py * math.cos(a)) for px, py in shape]
        with shaded(c, ROCK, up=1, down=1) as p:
            p.poly(pts, P.SN_ROCK)
        c.px(5.5 + math.cos(a) * 1.5, 5.5 + math.sin(a) * 1.5, P.SN_ROCK_D)  # a crack
        c.px(4, 3.5, P.SN_MAGENTA_L)
        c.outline(P.SN_MAGENTA_D)                                            # a magenta rim so it reads at night
        petal(c, 0 + (k % 2), 1 + (k // 2), k)
        petal(c, 1, 9 - (k % 2), k + 1)
        frames.append(under(aura((12, 12), 6, 6, 5.5, 5.5, 50), c.img))
    sprite.add("fly", frames, fps=12)
    return sprite


# --- tengu crow [18x14] ----------------------------------------------------------------------------

CROW = (54, 44), 27, 35
CROW_BODY = ramp((P.SN_VIOLET_L, P.SN_VIOLET, P.SN_VIOLET_D), (P.SN_VIOLET, P.SN_VIOLET_D, P.SN_VIOLET_DD))


def tengu_wing(c: Canvas, root, flap: float, far: bool, swept: float = 0) -> None:
    """A big ragged wing spread up and back from the shoulder: the arm to the wrist, five long primaries fanning
    from it with notches between them, and ragged secondaries back to the body; tipped magenta. flap 1 = raised
    high, -1 = swept down; swept folds it back for the dive."""
    rx, ry = root
    s = (1.0 if not far else 0.82) * (1 - swept * 0.25)
    elev = math.radians(20 + flap * 50 - swept * 30)                      # wing angle above the line back
    wrist = (rx - math.cos(elev) * 8 * s, ry - math.sin(elev) * 8 * s)
    tips = []
    for i, ln in enumerate((13, 14, 13, 11, 9)):
        a = elev + 0.2 - i * 0.24
        tips.append((wrist[0] - math.cos(a) * ln * s, wrist[1] - math.sin(a) * ln * s))
    outline = [root, wrist]
    for i, t in enumerate(tips):
        outline.append(t)
        if i + 1 < len(tips):
            mx, my = (t[0] + tips[i + 1][0]) / 2, (t[1] + tips[i + 1][1]) / 2
            outline.append((wrist[0] + (mx - wrist[0]) * 0.75, wrist[1] + (my - wrist[1]) * 0.75))
    low = (rx - 1, ry + 3)
    for j, drop in ((1, 2.5), (2, 2)):                                    # ragged secondaries
        t = j / 3
        outline.append((tips[-1][0] + (low[0] - tips[-1][0]) * t, tips[-1][1] + (low[1] - tips[-1][1]) * t + drop))
    outline.append(low)
    base = P.SN_VIOLET if not far else P.SN_VIOLET_D
    with shaded(c, CROW_BODY, EDGE, up=1, down=1) as p:
        p.poly(outline, base)
    for i, t in enumerate(tips):                                          # feather shafts and magenta tips
        c.line((wrist[0] + (t[0] - wrist[0]) * 0.4, wrist[1] + (t[1] - wrist[1]) * 0.4),
               (wrist[0] + (t[0] - wrist[0]) * 0.85, wrist[1] + (t[1] - wrist[1]) * 0.85), P.SN_VIOLET_DD)
        c.px(t[0], t[1], P.SN_MAGENTA if not far else P.SN_MAGENTA_D)
    c.line(root, wrist, P.SN_VIOLET_L if not far else P.SN_VIOLET)       # the lit leading edge


def crow_frame(flap: float, bob: float = 0, eyes: str = "open", dive: float = 0, lines: bool = False, k: int = 0,
               fallen: bool = False) -> Image.Image:
    """A dark violet crow in a white tengu mask: a long white beak-nose with red markings, a red eye ringed pink,
    a pink blossom behind the mask, ragged wings and tail tipped magenta, red talons."""
    size, cx, gy = CROW
    c = Canvas(*size)
    y = gy + bob + dive * 2
    x = cx + dive * 2
    tengu_wing(c, (x - 1, y - 10), flap, far=True, swept=dive)
    with shaded(c, CROW_BODY, EDGE) as p:                                      # tail feathers
        p.poly([(x - 6, y - 8), (x - 15, y - 10 + dive * 2), (x - 16, y - 7 + dive * 2), (x - 14, y - 4 + dive * 2),
                (x - 5, y - 4)], P.SN_VIOLET)
    c.px(x - 15, y - 9 + dive * 2, P.SN_MAGENTA)
    c.px(x - 14, y - 5 + dive * 2, P.SN_MAGENTA_D)
    if not fallen:                                                             # talons
        c.line((x - 1, y - 2), (x - 2, y), P.SK_LACQUER)
        c.line((x + 2, y - 2), (x + 1, y), P.SK_LACQUER)
        c.px(x - 3, y, P.SK_LACQUER_D)
        c.px(x, y, P.SK_LACQUER_D)
    with shaded(c, CROW_BODY, up=2) as p:
        p.ellipse(x, y - 7, 7, 5.5, P.SN_VIOLET)                               # body
        p.ellipse(x + 5.5, y - 12 + dive * 2, 5, 4.5, P.SN_VIOLET)             # head
    c.ellipse(x + 1, y - 5, 3.5, 2, P.SN_VIOLET_L)
    hy = y - 12 + dive * 2
    with shaded(c, MASK, EDGE, up=1) as p:                                     # white tengu mask with its long nose
        p.ellipse(x + 8, hy, 3.5, 3.5, P.SN_MASK)
        p.poly([(x + 9, hy - 1.5), (x + 13, hy), (x + 15.5, hy + 3 + dive), (x + 14, hy + 3 + dive), (x + 9, hy + 2.5)],
               P.SN_MASK)
    c.line((x + 10, hy + 2), (x + 14, hy + 2.5 + dive), P.SN_MASK_D)
    c.poly([(x + 6, hy - 2.5), (x + 7, hy - 6), (x + 8.5, hy - 3)], P.SN_MAGENTA)  # the mask's pink ear
    c.line((x + 6, hy - 3), (x + 8, hy - 1), P.SK_LACQUER)                     # red markings
    c.px(x + 11, hy + 0.5, P.SK_LACQUER)
    if eyes == "x":
        for dx, dy in ((0, 0), (1, 1), (1, 0), (0, 1)):
            c.px(x + 8 + dx, hy - 1 + dy, EDGE)
    elif eyes == "shut":
        c.rect(x + 7.5, hy, x + 9, hy, EDGE)
    else:
        c.rect(x + 8, hy - 1, x + 9, hy, P.SN_EYE)
        c.px(x + 9, hy - 1, P.SN_EYE_L)
        if eyes == "angry":
            c.line((x + 6.5, hy - 2.5), (x + 9.5, hy - 1.5), EDGE)
    blossom(c, x + 2, hy - 4, 2, turn=k * 0.2)
    tengu_wing(c, (x + 1, y - 9), flap * 0.85, far=False, swept=dive)
    moonrim(c)
    out = c.outline(EDGE).img
    if lines:
        out = under(streaks(size, x - 8, y - 9, 4, 14, k, 1350, slope=0.25), out)
    return out


def tengu_crow() -> Sprite:
    size, cx, gy = CROW
    sprite = Sprite("tengu_crow", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("fly", [crow_frame(f, b, k=i) for i, (f, b) in enumerate(((1, 0), (0.2, 0), (-0.8, -1), (0.2, -1)))],
               fps=10)
    sprite.add("idle", [crow_frame(0.6, 0, k=0), crow_frame(0.1, -1, k=1)], fps=4)
    sprite.add("attack", [crow_frame(1, -1, eyes="angry"), crow_frame(-0.2, 0, eyes="angry", dive=1, lines=True, k=1),
                          crow_frame(0.3, 0, eyes="angry", dive=0.5, lines=True, k=2)], fps=10, loop=False)
    hurt = crow_frame(0.6, eyes="shut")
    sprite.add("hurt", hurt_frames(hurt, [(cx + 13, gy - 22), (cx - 10, gy - 20), (cx + 10, gy - 2)]), fps=10, loop=False)
    sprite.add("death", scatter(crow_frame(-0.6, 2, eyes="x", fallen=True), cx, gy, 1351, depth=6), fps=8, loop=False)
    return sprite


# --- spirit wisp [14x16] + wisp_shot ---------------------------------------------------------------

WISP = (38, 38), 17, 33


def wisp_frame(k: int = 0, bob: float = 0, eyes: str = "open", mouth: str = "smile", swell: float = 0,
               lean: float = 0) -> Image.Image:
    """A pink flame spirit: a round glowing body whose flame licks stream up and back, a pale face with dark eyes
    and a little mouth, magenta at the rims, a soft pink glow round it."""
    size, cx, gy = WISP
    c = Canvas(*size)
    y = gy + bob
    x = cx + lean
    r = 6.5 + swell
    sway = (0, 1, 0, -1)[k % 4]
    with shaded(c, FLAME, up=2, down=1) as p:
        p.ellipse(x, y - r, r, r, P.SN_MAGENTA)
        p.poly([(x - r, y - r), (x - r - 4 + sway, y - r * 2 - 6), (x - 2, y - r * 1.6)], P.SN_MAGENTA)
        p.poly([(x - r * 0.6, y - r * 1.5), (x - 1 - sway, y - r * 2 - 10 - swell), (x + r * 0.5, y - r * 1.6)],
               P.SN_MAGENTA)
        p.poly([(x + 1, y - r * 1.7), (x + 4 + sway, y - r * 2 - 4), (x + r * 0.9, y - r * 1.2)], P.SN_MAGENTA)
    with shaded(c, FLAME) as p:                                               # the brighter heart
        p.ellipse(x + 0.5, y - r + 0.5, r * 0.72, r * 0.72, P.SK_PINK)
        p.poly([(x - r * 0.5, y - r * 1.3), (x - 1 - sway * 0.6, y - r * 2 - 5), (x + r * 0.3, y - r * 1.4)], P.SK_PINK)
    c.ellipse(x + 1, y - r + 1, r * 0.5, r * 0.45, P.SK_PINK_L)              # pale face
    ex, ey = x + 2.5, y - r
    if eyes == "x":
        for e in (ex - 4, ex):
            for dx, dy in ((0, 0), (1, 1), (1, 0), (0, 1)):
                c.px(e + dx, ey + dy - 1, P.SAKURA_EYE)
    elif eyes == "shut":
        c.rect(ex - 4, ey, ex - 3, ey, P.SAKURA_EYE)
        c.rect(ex, ey, ex + 1, ey, P.SAKURA_EYE)
    else:
        for e in (ex - 4, ex):
            c.rect(e, ey - 1, e + 1, ey + 0.5, P.SAKURA_EYE)
            c.px(e + 1, ey - 1, P.WHITE)
        if eyes == "angry":
            c.line((ex - 5, ey - 2.5), (ex - 3, ey - 1.5), P.SAKURA_EYE)
            c.line((ex, ey - 1.5), (ex + 2, ey - 2.5), P.SAKURA_EYE)
    if mouth == "open":
        c.rect(ex - 2, ey + 2, ex - 1, ey + 3, P.SAKURA_EYE)
    else:
        c.px(ex - 2.5, ey + 2, P.SAKURA_EYE)
        c.px(ex - 0.5, ey + 2, P.SAKURA_EYE)
        c.px(ex - 1.5, ey + 2.5, P.SAKURA_EYE)
    c.px(ex - 5, ey + 1.5, P.SN_MAGENTA)                                      # blush
    c.px(ex + 2, ey + 1.5, P.SN_MAGENTA)
    c.outline(P.SN_MAGENTA_D)
    out = under(aura(size, x, y - r - 2, r + 6, r + 7, 60 + int(swell * 20)), c.img)
    orbit = Canvas(*size)                                                     # petals and sparks drifting round it
    for i in range(3):
        a = k * 0.8 + i * 2.1
        petal(orbit, x + math.cos(a) * (r + 6), y - r - 2 + math.sin(a) * (r + 3), k + i)
    sparkle(orbit, x - r - 4, y - r * 2 - 2 + (k % 2), P.SN_MAGENTA_L, P.WHITE)
    out.alpha_composite(orbit.img)
    return out


def spirit_wisp() -> Sprite:
    size, cx, gy = WISP
    sprite = Sprite("spirit_wisp", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("float", [wisp_frame(k, (0, -1, -2, -1)[k]) for k in range(4)], fps=8)
    sprite.add("idle", [wisp_frame(0), wisp_frame(2, -1, eyes="shut")], fps=3)
    shot = wisp_frame(3, eyes="angry", mouth="open", lean=-1)
    shot.alpha_composite(magenta_fireball(size, cx + 13, gy - 9, 3, 1, tail=7))
    sprite.add("attack", [wisp_frame(1, -1, eyes="angry", mouth="open", swell=1.2), shot, wisp_frame(2)], fps=8,
               loop=False)
    hurt = wisp_frame(1, eyes="x", mouth="open", lean=-1)
    sprite.add("hurt", hurt_frames(hurt, [(cx + 11, gy - 24), (cx - 10, gy - 20), (cx + 11, gy - 4)]), fps=10, loop=False)
    sprite.add("death", scatter(wisp_frame(2, eyes="x", mouth="open", swell=-1), cx, gy, 1361, depth=-5), fps=8,
               loop=False)
    return sprite


def wisp_shot() -> Sprite:
    sprite = Sprite("wisp_shot", (14, 12), faces_left=True)
    sprite.add("fly", [magenta_fireball((14, 12), 9, 5.5, 3.2, k, tail=7) for k in range(4)], fps=12)
    return sprite


def build() -> list[Sprite]:
    return [shadow_slime(), samurai_ronin(), oni_cat(), oni_rock(), tengu_crow(), spirit_wisp(), wisp_shot()]
