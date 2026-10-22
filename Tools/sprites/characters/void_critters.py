"""The final world, the Void (from `docs/concept/The Void Cat_ Final Boss Sprite Sheet.png`): the void slime, void
bat, void sentinel, rift hound, void mage, rift turret, void wisp and mini void cat, and the orbs, laser, bolts
and crystal shots they fire.

Drawn facing right with light from the top-left and mirrored on export. The backdrop is a dark cosmic purple,
so bodies are near-black violet with a bright magenta 1px rim (`critters.rim`), bright eyes and a dark outline;
energy runs magenta to pink to a white-hot core.

The bat, hound, wisp and mini void cat share their build with the citadel's ember bat and hell hound, the
citadel's fire wisp and the museum's shadow cat (the sheet draws them as the same creatures, gone over to the
void): those frames are drawn by the same code and then recoloured colour-for-colour into the void palette."""
from __future__ import annotations

import math

from PIL import Image

import palette as P
from characters import citadel_critters as CC
from characters import haunted_critters as HC
from critters import ear, face, ramp, rim, shaded, sparkle
from draw import Canvas, noise, see_through, tint, vanish
from sprite import Sprite

EDGE = P.OUTLINE
BODY = ramp((P.VD_BODY_L, P.VD_BODY, P.VD_BODY_D))
STONE = ramp((P.VD_STONE_L, P.VD_STONE, P.VD_STONE_D), (P.VD_VIO_L, P.VD_STONE_L, P.VD_STONE))
CRYSTAL = ramp((P.VD_VIO_L, P.VD_VIO, P.VD_VIO_D), (P.VD_PINK_L, P.VD_MAG_L, P.VD_MAG))
MAGENTA_RIM = {P.VD_BODY_D: P.VD_MAG_D, P.VD_BODY: P.VD_MAG, P.VD_BODY_L: P.VD_MAG, P.VD_STONE_D: P.VD_VIO,
               P.VD_STONE: P.VD_VIO_L, P.VD_STONE_L: P.VD_VIO_L}


# --- shared helpers --------------------------------------------------------------------------------

def recolour(img: Image.Image, mapping: dict) -> Image.Image:
    """The same pixels with each colour in `mapping` swapped for its void colour (alpha kept)."""
    out = img.copy()
    px = out.load()
    table = {k[:3]: v[:3] for k, v in mapping.items()}
    for y in range(out.height):
        for x in range(out.width):
            r_, g_, b_, a_ = px[x, y]
            if not a_:
                continue
            if (r_, g_, b_) in table:
                px[x, y] = (*table[(r_, g_, b_)], a_)
                continue
            for amount in (0.65, 0.6):                                        # a pixel of a white hit flash:
                src = tuple((v - 255 * amount) / (1 - amount) for v in (r_, g_, b_))   # undo the tint,
                match = next((k for k in table if all(abs(a - b) <= 4 for a, b in zip(k, src))), None)
                if match:                                                     # recolour, and tint again
                    px[x, y] = (*(round(v + (255 - v) * amount) for v in table[match]), a_)
                    break
    return out


def recoloured(sprite: Sprite, name: str, mapping: dict, only: tuple | None = None) -> Sprite:
    """A copy in void colours. A white hit flash cannot be recoloured cleanly (the tint blends the colours), so
    the hit flash is redone from the recoloured flinch frame after it."""
    out = Sprite(name, sprite.size, faces_left=True, cx=sprite.cx, ground=sprite.ground)
    for anim, data in sprite.anims.items():
        if only and anim not in only:
            continue
        frames = [recolour(f, mapping) for f in data.frames]
        if anim == "hit":
            frames[0] = tint(frames[1], P.WHITE, 0.65)
        out.add(anim, frames, fps=data.fps, loop=data.loop)
    return out


# Citadel colours (black stone, lava) to void colours (near-black violet, magenta).
FROM_CITADEL = {P.CC_STONE_DD: P.VD_BODY_D, P.CC_STONE_D: P.VD_BODY, P.CC_STONE: P.VD_BODY_L,
                P.CC_STONE_L: P.VD_VIO_D, P.CC_STONE_TOP: P.VD_VIO, P.CC_LAVA_DD: P.VD_MAG_DD, P.CC_LAVA_D: P.VD_MAG_D,
                P.LAVA: P.VD_MAG, P.LAVA_L: P.VD_MAG_L, P.CC_LAVA_W: P.WHITE, P.CC_EMBER: P.VD_MAG_L,
                P.CAPE: P.VD_MAG_D, P.CAPE_L: P.VD_MAG, P.CAPE_D: P.VD_MAG_DD}
# The same, but its fire burns violet (the rift hound's flames).
VIOLET_FIRE = {**FROM_CITADEL, P.CC_LAVA_D: P.VD_VIO_D, P.LAVA: P.VD_VIO, P.LAVA_L: P.VD_VIO_L, P.CC_EMBER: P.VD_MAG_L}
# Fire to a pink-white spirit flame (the void wisp).
SPIRIT_FIRE = {P.CC_LAVA_DD: P.VD_MAG_DD, P.CC_LAVA_D: P.VD_MAG_D, P.LAVA: P.VD_MAG, P.LAVA_L: P.VD_PINK_L,
               P.CC_LAVA_W: P.WHITE, P.CC_EMBER: P.VD_MAG_L}
# Museum shadow colours to void colours (the mini void cat).
FROM_SHADOW = {P.HM_SIL_L: P.VD_BODY_L, P.HM_SIL: P.VD_BODY, P.HM_SIL_D: P.VD_BODY_D, P.HM_FOG_L: P.VD_MAG_L,
               P.HM_FOG: P.VD_MAG, P.HM_FOG_D: P.VD_VIO_D, P.HM_FOG_DD: P.VD_MAG_DD, P.HM_GLASS_L: P.VD_MAG_L,
               P.HM_GLASS: P.VD_MAG, P.HM_GLASS_D: P.VD_MAG_D}


def orb(c: Canvas, x: float, y: float, r: float, k: int = 0, hollow: bool = True) -> None:
    """A void orb: a magenta ring of light round a dark heart, with a white-hot glint turning on the ring."""
    c.ellipse(x, y, r + 1, r + 1, (*P.VD_MAG_D[:3], 150))
    c.ellipse(x, y, r, r, P.VD_MAG)
    c.ellipse(x, y, r * 0.75, r * 0.75, P.VD_MAG_L)
    if hollow:
        c.ellipse(x, y, r * 0.45, r * 0.45, P.VD_BODY_D)
    else:
        c.ellipse(x, y, r * 0.4, r * 0.4, P.WHITE)
    a = k / 4 * math.tau
    c.px(x + math.cos(a) * r * 0.85, y + math.sin(a) * r * 0.85, P.WHITE)


def comet(size, x: float, y: float, r: float, tail: float, k: int, hollow: bool = True) -> Image.Image:
    """An orb flying right with a wavering magenta tail."""
    c = Canvas(*size)
    for i in range(int(tail)):
        t = i / tail
        rr = r * (1 - t) * 0.8
        if rr < 0.4:
            continue
        colour = P.VD_MAG_L if t < 0.3 else (P.VD_MAG if t < 0.6 else P.VD_MAG_D)
        c.ellipse(x - 1 - i, y + math.sin(i * 1.1 + k) * 0.8 * t, rr, rr, (*colour[:3], int(255 - t * 120)))
    orb(c, x, y, r, k, hollow)
    return c.img


def sparks(c: Canvas, pts) -> None:
    for i, (x, y) in enumerate(pts):
        sparkle(c, x, y, P.VD_MAG_L, big=i % 2 == 0)


def hit_frames(hurt: Image.Image, pts) -> list[Image.Image]:
    second = Canvas(*hurt.size)
    second.paste(hurt)
    sparks(second, pts)
    return [tint(hurt, P.WHITE, 0.65), second.img]


def dying(still: Image.Image, depth: float) -> list[Image.Image]:
    return [tint(still, P.WHITE, 0.6)] + [vanish(still, t, depth=depth, flash=False) for t in (0.35, 0.65, 0.95)]


def finish(c: Canvas, mapping=MAGENTA_RIM) -> Image.Image:
    rim(c, mapping)
    return c.outline(EDGE).img


def bright_eyes(c: Canvas, xs, y: float, mood: str = "glow", size: int = 2) -> None:
    for i, ex in enumerate(xs):
        if mood == "glow":
            c.rect(ex, y, ex + size - 1, y + size - 1, P.VD_MAG_L)
            c.rect(ex, y, ex + size - 1, y, P.WHITE)
        elif mood == "angry":
            c.rect(ex, y + 1, ex + size - 1, y + size - 1, P.WHITE)
            c.px(ex + (size - 1 if i == 0 else 0), y, P.VD_MAG_L)
        elif mood == "shut":
            c.rect(ex, y + size - 1, ex + size - 1, y + size - 1, P.VD_MAG)
        elif mood == "x":
            c.px(ex, y, P.VD_MAG_L)
            c.px(ex + size - 1, y + size - 1, P.VD_MAG_L)
            c.px(ex + size - 1, y, P.VD_MAG_L)
            c.px(ex, y + size - 1, P.VD_MAG_L)


# --- void slime [20x14] + void_orb -----------------------------------------------------------------

def void_slime_body(c: Canvas, cx: float, gy: float, sx: float = 1.0, sy: float = 1.0, k: int = 0, eyes: str = "glow",
                    mouth: str = "w") -> None:
    """A dark violet cat-eared dome with magenta starlight inside and a pool of void at its foot."""
    height = 14 * sy
    ry = height * 0.72
    rx = 10 * sx / 0.92
    ey = gy - height + ry
    top = gy - height + 1
    with shaded(c, ramp((P.VD_MAG, P.VD_MAG_D, P.VD_MAG_DD))) as p:            # the pool of void
        p.ellipse(cx, gy - 0.5, rx + 3, 1.6, P.VD_MAG_D)
        p.rect(0, gy + 1, p.size[0], p.size[1], P.CLEAR)
    with shaded(c, BODY, up=2, down=1) as p:
        ear(p, cx - 5 * sx, top + 3.5, 6.5, P.VD_BODY, inner=P.VD_MAG_D, lean=-1.4, half=3.4)
        ear(p, cx + 5.5 * sx, top + 3.5, 6.5, P.VD_BODY, inner=P.VD_MAG_D, lean=1.4, half=3.4)
        p.ellipse(cx, ey, rx, ry, P.VD_BODY)
        p.rect(0, gy, p.size[0], p.size[1], P.CLEAR)
    rnd = noise(701 + k)
    for i in range(6):                                                        # starlight swirling inside
        c.px(cx - 7 * sx + rnd() * 14 * sx, top + 3 + rnd() * (height - 6), P.VD_MAG_L if i % 2 else P.VD_VIO_L)
    c.rect(cx - 6 * sx, top + 4, cx - 6 * sx + 1, top + 5, P.VD_VIO)          # gloss
    bright_eyes(c, (cx - 4, cx + 2), gy - 8 * sy, eyes, size=3)
    if mouth == "w":
        c.px(cx - 1, gy - 3.5 * sy, P.VD_MAG)
        c.px(cx + 1, gy - 3.5 * sy, P.VD_MAG)
    elif mouth == "open":
        c.ellipse(cx, gy - 3.5 * sy, 1.4, 1.1, P.VD_MAG_L)
    elif mouth == "flat":
        c.rect(cx - 1, gy - 3.5 * sy, cx + 1, gy - 3.5 * sy, P.VD_MAG)


def void_slime() -> Sprite:
    size, cx, gy = (36, 30), 17, 27
    sprite = Sprite("void_slime", size, faces_left=True, cx=cx, ground=gy)

    def f(sx=1.0, sy=1.0, k=0, eyes="glow", mouth="w", shot=None):
        c = Canvas(*size)
        void_slime_body(c, cx, gy, sx, sy, k, eyes, mouth)
        for i, (x, y) in enumerate(((cx - 8, gy - 17), (cx + 8, gy - 18))):
            c.px(x + (k + i) % 2, y - k % 3, P.VD_MAG_L)
        out = finish(c)
        if shot:
            out.alpha_composite(comet(size, shot[0], shot[1], 3.2, 6, k))
        return out

    sprite.add("idle", [f(1, 1, 0), f(1.04, 0.95, 1)], fps=4)
    sprite.add("move", [f(1.1, 0.86, 0), f(0.94, 1.08, 1), f(1.0, 1.0, 2, mouth="open"), f(0.96, 1.04, 3)], fps=8)
    sprite.add("attack", [f(1.12, 0.84, 0, eyes="angry", mouth="flat"),
                          f(0.9, 1.12, 1, eyes="angry", mouth="open", shot=(cx + 12, gy - 9)), f(1.05, 0.95, 2)],
               fps=8, loop=False)
    hurt = f(1.1, 0.9, 1, eyes="shut", mouth="open")
    sprite.add("hit", hit_frames(hurt, [(cx - 9, gy - 16), (cx + 9, gy - 15), (cx + 1, gy - 20)]), fps=10, loop=False)
    sprite.add("death", [tint(f(1, 1, 0, eyes="x", mouth="flat"), P.WHITE, 0.6), f(1.1, 0.7, 1, eyes="x", mouth="flat"),
                         see_through(f(1.12, 0.45, 2, eyes="x", mouth="flat"), 200),
                         see_through(f(1.12, 0.3, 3, eyes="x", mouth="flat"), 100)], fps=10, loop=False)
    return sprite


def void_orb() -> Sprite:
    sprite = Sprite("void_orb", (12, 12), faces_left=True)
    frames = []
    for k in range(4):
        c = Canvas(12, 12)
        orb(c, 5.5, 5.5, 4.2 + (k % 2) * 0.3, k)
        frames.append(c.img)
    sprite.add("fly", frames, fps=10)
    return sprite


# --- void bat [18x14] (the citadel's ember bat, gone over to the void) -----------------------------

def void_bat() -> Sprite:
    sprite = recoloured(CC.ember_bat(), "void_bat", FROM_CITADEL)
    # Its attack fires a void orb: lay one in front of the dive.
    size, cx, gy = sprite.size, sprite.cx, sprite.ground
    frames = list(sprite.anims["attack"].frames)
    frames[2] = frames[2].copy()
    frames[2].alpha_composite(comet(size, cx + 18, gy - 8, 3.4, 7, 1))
    sprite.anims["attack"].frames = frames
    dead = recolour(CC.ember_bat_frame(-0.5, "x"), FROM_CITADEL)
    sprite.add("death", [tint(dead, P.WHITE, 0.6), vanish(dead, 0.45, depth=8, flash=False),
                         vanish(dead, 0.9, depth=8, flash=False)], fps=10, loop=False)
    return sprite


# --- void sentinel [20x22] + void_laser ------------------------------------------------------------

def sentinel_frame(bob: float = 0, glow: int = 0, eyes: str = "open", beam: float = 0, k: int = 0, tilt: float = 0) -> Image.Image:
    """A one-eyed cat bust of violet stone on a carved slab, a crystal-studded rock hanging beneath it, and
    small crystals orbiting it. glow 0...2 brightens the eye; beam draws the laser out to the right."""
    size, cx, gy = (60, 46), 20, 40
    c = Canvas(*size)
    y = gy + bob
    x = cx + tilt
    rnd = noise(731)
    for i in range(4):                                                        # orbiting crystals
        a = i / 4 * math.tau + k * 0.4
        ox, oy = x + math.cos(a) * 15, y - 13 + math.sin(a) * 6
        with shaded(c, CRYSTAL, EDGE) as p:
            p.poly([(ox, oy - 2.5), (ox + 1.6, oy), (ox, oy + 2.5), (ox - 1.6, oy)], P.VD_VIO)
    with shaded(c, STONE, EDGE) as p:                                         # hanging rock with crystals
        p.poly([(x - 7, y - 10), (x + 7, y - 10), (x + 4, y - 4), (x + 1, y), (x - 2, y - 2), (x - 5, y - 5)], P.VD_STONE)
    with shaded(c, CRYSTAL, EDGE) as p:
        p.poly([(x - 4, y - 8), (x - 3, y - 2), (x - 1.5, y - 8)], P.VD_VIO)
        p.poly([(x + 2, y - 8), (x + 3, y - 1), (x + 4.5, y - 8)], P.VD_MAG_L)
    with shaded(c, STONE, EDGE, up=2) as p:                                   # the carved slab
        p.rect(x - 11, y - 14, x + 11, y - 10, P.VD_STONE)
    for i, bx in enumerate(range(int(x - 10), int(x + 10), 4)):               # bricks, some glowing
        c.rect(bx, y - 13, bx + 2, y - 11, (P.GOLD_D, P.VD_STONE_L, P.VD_MAG_D, P.VD_STONE_L)[i % 4])
    with shaded(c, STONE, EDGE, up=2) as p:                                   # the cat bust
        p.ellipse(x, y - 17, 6, 3.5, P.VD_STONE)
        ear(p, x - 4.5, y - 26, 5, P.VD_STONE, inner=P.VD_MAG_D, lean=-1, half=2.8)
        ear(p, x + 4.5, y - 26, 5, P.VD_STONE, inner=P.VD_MAG_D, lean=1, half=2.8)
        p.ellipse(x, y - 22.5, 6.5, 5.5, P.VD_STONE)
    c.line((x - 5, y - 20), (x - 3, y - 18), P.VD_STONE_D)                    # chisel marks
    c.line((x + 4, y - 19), (x + 5, y - 17), P.VD_STONE_D)
    ex, ey = x + 1, y - 23                                                    # the one great eye
    c.ellipse(ex, ey, 3, 2.6, P.VD_BODY_D)
    if eyes == "x":
        c.px(ex - 1, ey - 1, P.VD_MAG_L)
        c.px(ex + 1, ey + 1, P.VD_MAG_L)
        c.px(ex + 1, ey - 1, P.VD_MAG_L)
        c.px(ex - 1, ey + 1, P.VD_MAG_L)
    elif eyes == "shut":
        c.rect(ex - 2, ey, ex + 2, ey, P.VD_MAG)
    else:
        c.ellipse(ex, ey, 2 + glow * 0.3, 1.8 + glow * 0.3, P.VD_MAG if glow < 2 else P.VD_MAG_L)
        c.ellipse(ex + 0.5, ey, 1, 1, P.WHITE if glow else P.VD_MAG_L)
        c.px(ex + 0.5, ey, P.VD_BODY_D if glow == 0 else P.WHITE)
    out = finish(c)
    if glow:                                                                  # charging sparkles round the eye
        g = Canvas(*size)
        sparks(g, [(ex + 5, ey - 4), (ex - 6, ey - 3)][:glow])
        out.alpha_composite(g.img)
    if beam:
        b = Canvas(*size)
        end = ex + 4 + beam * (size[0] - ex - 9)
        b.rect(ex + 3, ey - 1.5, end, ey + 1.5, P.VD_MAG_D)
        b.rect(ex + 3, ey - 1, end, ey + 1, P.VD_MAG)
        b.rect(ex + 3, ey, end, ey, P.WHITE)
        for i in range(int(ex + 6), int(end), 5):                             # sparkles riding the beam
            b.px(i + k % 2, ey - 1, P.VD_PINK_L)
        b.ellipse(end, ey, 2.6, 2.6, P.VD_MAG)
        b.ellipse(end, ey, 1.4, 1.4, P.WHITE)
        b.ellipse(ex + 3, ey, 2, 2, P.VD_MAG_L)
        out.alpha_composite(b.img)
    return out


def void_sentinel() -> Sprite:
    size, cx, gy = (60, 46), 20, 40
    sprite = Sprite("void_sentinel", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [sentinel_frame(0, k=0), sentinel_frame(-1, k=1)], fps=4)
    sprite.add("move", [sentinel_frame((0, -1, -1, 0)[i], k=i, tilt=(0, 0.5, 1, 0.5)[i]) for i in range(4)], fps=6)
    sprite.add("charge", [sentinel_frame(0, glow=1, k=0), sentinel_frame(-1, glow=2, k=1), sentinel_frame(-1, glow=2, k=2)],
               fps=8)
    sprite.add("attack", [sentinel_frame(0, glow=2, beam=0.35, k=0), sentinel_frame(0, glow=2, beam=1, k=1),
                          sentinel_frame(0, glow=1, k=2)], fps=10, loop=False)
    hurt = sentinel_frame(0, eyes="shut", tilt=-1)
    sprite.add("hit", hit_frames(hurt, [(cx + 10, gy - 30), (cx - 10, gy - 26), (cx + 12, gy - 6)]), fps=10, loop=False)
    sprite.add("death", dying(sentinel_frame(1, eyes="x"), 10), fps=10, loop=False)
    return sprite


def void_laser() -> Sprite:
    """A 16x4 beam segment that tiles end to end: a dark magenta edge, a bright body, a white-hot core line,
    and sparkles that run along it between the two frames."""
    sprite = Sprite("void_laser", (16, 4))
    frames = []
    for k in range(2):
        c = Canvas(16, 4)
        c.rect(0, 0, 15, 3, P.VD_MAG_D)
        c.rect(0, 1, 15, 2, P.VD_MAG)
        c.rect(0, 1, 15, 1, P.WHITE)
        for x in range(k * 4, 16, 8):
            c.px(x, 2, P.VD_PINK_L)
            c.px(x + 2, 0, P.VD_MAG)
        frames.append(c.img)
    sprite.add("fly", frames, fps=12)
    return sprite


# --- rift hound [26x18] (the citadel's hell hound with violet void fire) ---------------------------

def rift_hound() -> Sprite:
    sprite = recoloured(CC.hell_hound(), "rift_hound", VIOLET_FIRE, only=("idle", "run", "attack", "hit"))
    still = recolour(CC.hound_frame(k=2, eyes="x", jaw=0.8, crouch=2), VIOLET_FIRE)
    sprite.add("death", dying(still, 6), fps=8, loop=False)                    # fades into the void, no fire
    return sprite


# --- void mage [16x24] + void_bolt -----------------------------------------------------------------

def staff(c: Canvas, x: float, top: float, bottom: float, glow: int = 0, k: int = 0) -> None:
    """A dark staff topped with a hooked crescent holding a magenta orb."""
    with shaded(c, BODY, EDGE) as p:
        p.line((x, top + 3), (x, bottom), P.VD_BODY, 2)
        p.ellipse(x, top, 3, 3, P.VD_BODY)
        p.ellipse(x + 1, top - 0.5, 1.8, 1.8, P.CLEAR)
    c.ellipse(x + 1, top - 0.5, 1.4 + glow * 0.4, 1.4 + glow * 0.4, P.VD_MAG)
    c.px(x + 1, top - 0.5, P.WHITE)
    if glow:
        sparks(c, [(x + 4, top - 4)])


def portal(size, x: float, y: float, r: float, column: float, k: int) -> Image.Image:
    """A summoning ring on the ground (a flat ellipse of magenta light) with a pillar of light rising."""
    c = Canvas(*size)
    if column:
        c.rect(x - 1, y - column, x + 1, y, P.VD_MAG)
        c.rect(x, y - column, x, y, P.WHITE)
        orb(c, x, y - column - 2, 3, k, hollow=False)
    for ry, colour in ((r * 0.3, P.VD_MAG_D), (r * 0.3 - 0.6, P.VD_MAG)):
        c.ellipse(x, y, r, max(1, ry + 0.6), colour)
    c.ellipse(x, y, r - 2, max(0.5, r * 0.3 - 1.4), P.CLEAR)
    for i in range(3):
        a = k * 0.8 + i * 2.1
        c.px(x + math.cos(a) * r, y + math.sin(a) * r * 0.3, P.WHITE)
    return c.img


def mage_frame(step: int = 0, walk: bool = False, eyes: str = "glow", staff_up: float = 0, glow: int = 0, lean: float = 0,
               k: int = 0) -> Image.Image:
    """A hooded cultist cat in a dark violet robe with magenta trim, a glowing face and a staff."""
    size, x, gy = (50, 46), 16, 42
    c = Canvas(*size)
    x += lean
    sway = (0, 1, 0, -1)[step % 4] if walk else 0
    with shaded(c, ramp((P.VD_MAG, P.VD_MAG_D, P.VD_MAG_DD)), EDGE) as p:     # cloak tail behind
        p.poly([(x - 3, gy - 19), (x - 10 - sway, gy - 3), (x - 7 - sway, gy - 1), (x - 1, gy - 6)], P.VD_MAG_D)
    lifts = ((step % 2) * 1.5, ((step + 1) % 2) * 1.5) if walk else (0, 0)
    with shaded(c, BODY, EDGE) as p:
        p.rect(x - 4, gy - 2 - lifts[0], x - 1, gy - lifts[0], P.VD_BODY_D)
        p.rect(x + 1, gy - 2 - lifts[1], x + 4, gy - lifts[1], P.VD_BODY_D)
    with shaded(c, BODY, up=2) as p:
        p.poly([(x - 5, gy - 16), (x + 5, gy - 16), (x + 6.5, gy - 2), (x - 6.5, gy - 2)], P.VD_BODY)   # robe
    c.rect(x - 1, gy - 14, x + 1, gy - 3, P.VD_MAG_D)                         # magenta stole
    c.line((x + 1, gy - 14), (x + 1, gy - 3), P.VD_MAG)
    with shaded(c, BODY, EDGE, up=2) as p:                                    # hood with cat ears
        ear(p, x - 3.5, gy - 25, 5, P.VD_BODY, inner=P.VD_BODY_D, lean=-0.8, half=2.6)
        ear(p, x + 4.5, gy - 25, 5, P.VD_BODY, inner=P.VD_BODY_D, lean=0.8, half=2.6)
        p.ellipse(x + 0.5, gy - 20, 6.5, 6, P.VD_BODY)
    c.ellipse(x + 2, gy - 19, 4, 3.6, P.VD_BODY_D)                            # the shadowed face
    bright_eyes(c, (x, x + 3), gy - 20.5, eyes)
    sx = x + 7
    staff(c, sx, gy - 26 - staff_up * 3, gy - 1 - staff_up * 3, glow, k)
    with shaded(c, BODY, EDGE) as p:                                          # sleeve and paw on the staff
        p.line((x + 2, gy - 14), (sx - 1, gy - 13 - staff_up * 3), P.VD_BODY, 3)
    return finish(c)


def void_mage() -> Sprite:
    size, cx, gy = (50, 46), 16, 42
    sprite = Sprite("void_mage", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [mage_frame(), mage_frame(eyes="angry", k=1)], fps=3)
    sprite.add("walk", [mage_frame(i, walk=True, k=i) for i in range(4)], fps=8)
    summon = []
    for i, (r, col) in enumerate(((5, 0), (8, 4), (10, 12), (10, 18))):
        f = mage_frame(staff_up=1 if i else 0, glow=1, eyes="angry", lean=-1, k=i)
        f.alpha_composite(portal(size, cx + 17, gy - 3, r, col, i))
        summon.append(f)
    sprite.add("summon", summon, fps=8, loop=False)
    attack = [mage_frame(staff_up=1, glow=1, eyes="angry", k=0), mage_frame(staff_up=1, glow=2, eyes="angry", k=1)]
    shot = mage_frame(staff_up=0, glow=1, eyes="angry", lean=1, k=2)
    shot.alpha_composite(comet(size, cx + 26, gy - 26, 3.2, 8, 2))
    attack += [shot, mage_frame(k=3)]
    sprite.add("attack", attack, fps=8, loop=False)
    hurt = mage_frame(eyes="shut", lean=-1)
    sprite.add("hit", hit_frames(hurt, [(cx + 9, gy - 28), (cx - 9, gy - 24), (cx + 11, gy - 6)]), fps=10, loop=False)
    sprite.add("death", dying(mage_frame(eyes="x"), 8), fps=10, loop=False)
    return sprite


def void_bolt() -> Sprite:
    sprite = Sprite("void_bolt", (14, 10), faces_left=True)
    sprite.add("fly", [comet((14, 10), 9.5, 4.5, 3.6, 8, k) for k in range(4)], fps=12)
    return sprite


# --- rift turret [16x20] + crystal_shot ------------------------------------------------------------

def turret_frame(charge: float = 0, k: int = 0, bob: float = 0, flash: bool = False, eyes: str = "open") -> Image.Image:
    """A floating violet crystal with a glowing core, four crystal shards orbiting it on a dotted ring.
    charge 0...1 brightens the core and pulls the shards in."""
    size, cx, gy = (44, 44), 21, 34
    c = Canvas(*size)
    y = gy + bob
    cy = y - 11
    ring = 13 - charge * 2
    for i in range(16):                                                       # the dotted orbit
        a = i / 16 * math.tau + k * 0.2
        c.px(cx + math.cos(a) * ring, cy + math.sin(a) * ring, P.VD_VIO_D if i % 2 else P.VD_VIO)
    for i in range(4):                                                        # orbiting shards
        a = i / 4 * math.tau + math.pi / 4 + k * 0.35
        ox, oy = cx + math.cos(a) * ring, cy + math.sin(a) * ring
        with shaded(c, CRYSTAL, EDGE) as p:
            p.poly([(ox - math.cos(a) * 3, oy - math.sin(a) * 3), (ox - math.sin(a) * 1.6, oy + math.cos(a) * 1.6),
                    (ox + math.cos(a) * 3, oy + math.sin(a) * 3), (ox + math.sin(a) * 1.6, oy - math.cos(a) * 1.6)],
                   P.VD_VIO)
    with shaded(c, CRYSTAL, EDGE, up=2) as p:                                 # the big crystal
        p.poly([(cx, cy - 11), (cx + 6, cy - 2), (cx + 4, cy + 7), (cx, cy + 11), (cx - 4, cy + 7), (cx - 6, cy - 2)], P.VD_VIO)
    c.poly([(cx, cy - 11), (cx + 6, cy - 2), (cx, cy)], P.VD_VIO_L)           # facets
    c.poly([(cx, cy + 11), (cx + 4, cy + 7), (cx, cy)], P.VD_VIO_D)
    c.line((cx, cy - 10), (cx, cy + 10), P.VD_MAG_D)
    core = 2 + charge * 1.6
    c.ellipse(cx, cy, core + 0.8, core + 0.8, P.VD_MAG_D)
    c.ellipse(cx, cy, core, core, P.VD_MAG if charge < 0.6 else P.VD_MAG_L)
    if eyes == "x":
        c.px(cx - 1, cy - 1, P.WHITE)
        c.px(cx + 1, cy + 1, P.WHITE)
        c.px(cx + 1, cy - 1, P.WHITE)
        c.px(cx - 1, cy + 1, P.WHITE)
    elif eyes == "shut":
        c.rect(cx - 1, cy, cx + 1, cy, P.VD_BODY_D)
    else:
        c.ellipse(cx, cy, max(0.6, core * 0.45), max(0.6, core * 0.45), P.WHITE if charge > 0 else P.VD_BODY_D)
        c.px(cx + 0.5, cy - 0.5, P.WHITE)
    out = c.outline(EDGE).img
    if flash or charge > 0.5:
        g = Canvas(*size)
        sparks(g, [(cx + 8, cy - 9), (cx - 8, cy + 8)][:1 + int(flash)])
        out.alpha_composite(g.img)
    return out


def rift_turret() -> Sprite:
    size, cx, gy = (44, 44), 21, 34
    sprite = Sprite("rift_turret", size, faces_left=True, cx=cx, ground=gy + 1)   # the crystal tip; the shards orbit below
    sprite.add("idle", [turret_frame(0, 0), turret_frame(0, 1, -1)], fps=4)
    sprite.add("charge", [turret_frame(0.25, 0), turret_frame(0.5, 1), turret_frame(0.75, 2), turret_frame(1.0, 3)], fps=8)
    fire = turret_frame(1.0, 0, flash=True)
    fire.alpha_composite(shot_img(size, cx + 17, gy - 11, 0))
    sprite.add("attack", [turret_frame(1.0, 3, flash=True), fire, turret_frame(0.2, 1)], fps=10, loop=False)
    hurt = turret_frame(0, 2, eyes="shut")
    sprite.add("hit", hit_frames(hurt, [(cx + 11, gy - 26), (cx - 11, gy - 20), (cx + 12, gy - 4)]), fps=10, loop=False)
    sprite.add("death", dying(turret_frame(0, 1, eyes="x"), 4), fps=10, loop=False)
    return sprite


def shot_img(size, x: float, y: float, k: int) -> Image.Image:
    """A crystal arrowhead flying right with a dotted trail."""
    c = Canvas(*size)
    for i in range(3):
        c.px(x - 6 - i * 3 - k, y, P.VD_MAG if i < 2 else P.VD_MAG_D)
    c.line((x - 6, y), (x - 1, y), P.VD_MAG_L)
    c.poly([(x - 2, y - 2.5), (x + 3, y), (x - 2, y + 2.5), (x - 0.5, y)], P.VD_VIO_L)
    c.px(x + 1, y, P.WHITE)
    c.outline(P.VD_MAG_DD)
    return c.img


def crystal_shot() -> Sprite:
    sprite = Sprite("crystal_shot", (16, 6), faces_left=True)
    sprite.add("fly", [shot_img((16, 6), 12, 2.5, k) for k in range(2)], fps=10)
    return sprite


# --- void wisp [14x14] + homing_orb (the citadel's fire wisp as a pink-white spirit flame) ---------

def void_wisp() -> Sprite:
    size, cx, gy = (50, 54), 25, 33

    def wf(*a, **kw):
        return recolour(CC.wisp_frame(*a, **kw), SPIRIT_FIRE)

    sprite = Sprite("void_wisp", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [wf(0), wf(1, -1)], fps=6)
    sprite.add("move", [wf(k, (0, -1, -1, 0)[k]) for k in range(4)], fps=8)
    launch = wf(1, swell=1.15, eyes="angry", mouth="open")
    launch.alpha_composite(comet(size, cx + 13, gy - 7, 3.2, 8, 1, hollow=False))
    sprite.add("attack", [wf(0, swell=1.15, eyes="angry", mouth="flat"), launch, wf(2)], fps=8, loop=False)
    hurt = wf(1, eyes="shut", mouth="open")
    sprite.add("hit", hit_frames(hurt, [(cx - 9, gy - 18), (cx + 9, gy - 16), (cx + 7, gy - 3)]), fps=10, loop=False)
    sprite.add("death", dying(wf(2, eyes="x", mouth="open"), -4), fps=10, loop=False)          # rises and fades
    return sprite


def homing_orb() -> Sprite:
    """A bright orb with a curling trail behind it (it bends toward the kitten in flight)."""
    sprite = Sprite("homing_orb", (14, 12), faces_left=True)
    frames = []
    for k in range(4):
        c = Canvas(14, 12)
        for i in range(7):
            t = i / 7
            c.ellipse(9 - 1 - i * 1.2, 6 + math.sin(i * 0.9 + k * 1.5) * 1.6 * t, 2.4 * (1 - t) + 0.4, 2.4 * (1 - t) + 0.4,
                      (*(P.VD_PINK_L if t < 0.3 else P.VD_MAG)[:3], int(255 - t * 140)))
        orb(c, 9.5, 6, 3.4, k, hollow=False)
        frames.append(c.img)
    sprite.add("fly", frames, fps=12)
    return sprite


# --- mini void cat [18x20] (the museum's shadow cat, gone over to the void) ------------------------

def mini_void_cat() -> Sprite:
    return recoloured(HC.shadow_cat(), "mini_void_cat", FROM_SHADOW)


def build() -> list[Sprite]:
    return [void_slime(), void_orb(), void_bat(), void_sentinel(), void_laser(), rift_hound(), void_mage(), void_bolt(),
            rift_turret(), crystal_shot(), void_wisp(), homing_orb(), mini_void_cat()]
