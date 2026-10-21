"""World 3, the Haunted Meowseum critters (from `docs/concept/Haunted Meowseum Enemy Sprite Showcase.png`): the
ghost cat, bat cat, haunted portrait, cursed armour, candle cat, poltergeist book, gargoyle cat and shadow cat,
and the spirit balls, magic shots, fire orbs and magic bolts they throw.

Drawn facing right with light from the top-left and mirrored on export. The museum is a dark purple interior,
so solid creatures get a dark 1px outline plus light rims, and spirits (the ghost, the shadow cat's smoke)
are see-through with a bright magenta-violet outline. Magic is magenta with a white core; slashes are
glowing magenta crescents laid on after the outline. Gameplay hitboxes (w x h, at the feet) are noted."""
from __future__ import annotations

import math

from PIL import Image

import palette as P
from critters import ear, face, ramp, shaded, sparkle
from draw import Canvas, noise, see_through, shatter, tint, vanish
from sprite import Sprite

EDGE = P.OUTLINE
STONE = ramp((P.HM_STONE_TOP, P.HM_STONE_L, P.HM_STONE), (P.HM_STONE_L, P.HM_STONE, P.HM_STONE_D),
             (P.HM_STONE, P.HM_STONE_D, P.HM_STONE_DD))
GREY_RAMP = ramp((P.GREY_L, P.GREY, P.GREY_D), (P.GREY, P.GREY_D, P.SLATE))
GOLD_RAMP = ramp((P.YELLOW, P.GOLD, P.GOLD_D), (P.GOLD, P.GOLD_D, P.RUST_D))
WAX = ramp((P.WHITE, P.HM_WAX, P.HM_WAX_D))
GHOST = ramp((P.WHITE, P.LILAC, P.LILAC_D))
NAVY_RAMP = ramp((P.SPIDER_L, P.SPIDER, P.SPIDER_D))
PINK_WING = ramp((P.HM_GLASS_L, P.HM_GLASS, P.HM_GLASS_D))
BOOK = ramp((P.PURPLE_L, P.PURPLE, P.PURPLE_D))
SHADOW = ramp((P.HM_FOG_D, P.HM_SIL, P.HM_SIL_D))
WARM = ramp((P.WHITE, P.GG_STONE_TOP, P.GG_STONE_L), (P.GG_STONE_TOP, P.GG_STONE_L, P.GG_STONE),
            (P.GG_STONE_L, P.GG_STONE, P.GG_STONE_D), (P.GG_STONE, P.GG_STONE_D, P.GG_STONE_DD))
WOOD = ramp((P.PLANK_L, P.PLANK, P.PLANK_D), (P.BARK_L, P.BARK_D, P.BARK_DD))


# --- shared helpers --------------------------------------------------------------------------------

def magic_sparkle(c: Canvas, x: float, y: float, big: bool = False) -> None:
    sparkle(c, x, y, P.HM_GLASS_L, big=big)


def arc_layer(size, cx: float, cy: float, r: float, a0: float, a1: float, thick: float) -> Image.Image:
    """A glowing magenta crescent (a slash), thickest in the middle, from a0 to a1 degrees (0 = right)."""
    c = Canvas(*size)
    steps = 48
    for i in range(steps + 1):
        t = i / steps
        a = math.radians(a0 + (a1 - a0) * t)
        w = thick * math.sin(math.pi * t) + 0.6
        c.ellipse(cx + math.cos(a) * r, cy - math.sin(a) * r, w, w, P.HM_GLASS)
    for i in range(steps + 1):
        t = i / steps
        a = math.radians(a0 + (a1 - a0) * t)
        w = thick * 0.55 * math.sin(math.pi * t)
        x, y = cx + math.cos(a) * (r + thick * 0.3), cy - math.sin(a) * (r + thick * 0.3)
        if w > 0.4:
            c.ellipse(x, y, w, w, P.HM_GLASS_L)
        if 0.3 < t < 0.7:
            c.px(x, y, P.WHITE)
    c.outline(P.HM_GLASS_D)
    return c.img


def with_overlay(img: Image.Image, *layers: Image.Image, sparks: list[tuple[float, float]] = ()) -> Image.Image:
    out = Canvas(*img.size)
    out.paste(img)
    for layer in layers:
        out.paste(layer)
    for x, y in sparks:
        magic_sparkle(out, x, y, big=True)
    return out.img


def hit_frames(hurt: Image.Image, sparks: list[tuple[float, float]]) -> list[Image.Image]:
    """Hit: a white flash of the flinch pose, then the flinch with magenta sparkles."""
    second = Canvas(*hurt.size)
    second.paste(hurt)
    for i, (x, y) in enumerate(sparks):
        magic_sparkle(second, x, y, big=i % 2 == 0)
    return [tint(hurt, P.WHITE, 0.65), second.img]


def dying(still: Image.Image, depth: float) -> list[Image.Image]:
    return [tint(still, P.WHITE, 0.6)] + [vanish(still, t, depth=depth, flash=False) for t in (0.35, 0.65, 0.95)]


def crumbling(still: Image.Image, seed: int) -> list[Image.Image]:
    """Stone breaking: a flash, then blocks that slump down and fade (gargoyle, armour)."""
    frames = [tint(still, P.WHITE, 0.6)]
    for t, keep in ((0.3, 255), (0.6, 210), (0.9, 120)):
        frames.append(see_through(shatter(still, t, seed, block=5, spread=0.12, gravity=1.0), keep))
    return frames


def rim(c: Canvas, colours) -> None:
    """Lights the 1-px inner edge of everything drawn so far: each pixel next to empty space takes `colours`
    (one colour, or a dict from base colour to its lighter one). Run it before the outline."""
    img = c.img
    px = img.load()
    w, h = img.size
    edge = []
    for y in range(h):
        for x in range(w):
            if not px[x, y][3]:
                continue
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if not (0 <= nx < w and 0 <= ny < h) or not px[nx, ny][3]:
                    edge.append((x, y))
                    break
    for x, y in edge:
        if isinstance(colours, dict):
            new = colours.get(px[x, y][:3] + (255,))
            if new:
                px[x, y] = new
        else:
            px[x, y] = colours


def orb(c: Canvas, x: float, y: float, r: float, k: int = 0, ring: bool = True) -> None:
    """A glowing magenta orb: soft halo, bright body, white core and a turning glint."""
    c.ellipse(x, y, r + 1, r + 1, (*P.HM_GLASS_D[:3], 150))
    c.ellipse(x, y, r, r, P.HM_GLASS)
    c.ellipse(x - 0.3, y - 0.3, r * 0.6, r * 0.6, P.HM_GLASS_L)
    c.ellipse(x - 0.5, y - 0.5, max(0.6, r * 0.25), max(0.6, r * 0.25), P.WHITE)
    if ring:
        a = k / 4 * math.tau
        c.px(x + math.cos(a) * r, y + math.sin(a) * r, P.WHITE)


def comet(size, x: float, y: float, r: float, tail: float, k: int) -> Image.Image:
    """An orb flying right with a fading magenta tail behind it."""
    c = Canvas(*size)
    for i in range(int(tail)):
        t = i / tail
        c.ellipse(x - 1 - i, y + math.sin(i * 0.9 + k) * 0.6 * t, r * (1 - t) * 0.9, r * (1 - t) * 0.9,
                  (*(P.HM_GLASS if t < 0.5 else P.HM_GLASS_D)[:3], int(230 * (1 - t) + 25)))
    orb(c, x, y, r, k)
    return c.img


# --- ghost cat [14x14] + spirit_ball ---------------------------------------------------------------

def ghost_body(c: Canvas, x: float, y: float, wisp: float, paw: float = 0, eyes: str = "open", mouth: str = "w") -> None:
    """A floating white cat: big head, little body, front paws, and a curling tail of mist instead of legs.
    (x, y) is the bottom of its body; `wisp` sways the misty tail."""
    with shaded(c, GHOST, up=2) as p:
        pts = [(x - 2, y - 3), (x - 6, y - 1), (x - 9, y + 1 + wisp * 0.5), (x - 12, y + 0 + wisp),
               (x - 13, y - 3 + wisp), (x - 12, y - 5 + wisp * 0.5)]
        for i, (px, py) in enumerate(pts):                                    # the misty tail
            r = 3.6 - i * 0.5
            p.ellipse(px, py, r, r * 0.9, P.LILAC)
        p.ellipse(x, y - 5, 5.5, 5, P.LILAC)                                  # body
        p.ellipse(x + 2.5, y - 1.5, 1.8, 1.4, P.LILAC)                         # front paws
        if paw:
            p.line((x + 4, y - 6), (x + 4 + paw * 6, y - 7), P.LILAC, 3)
            p.ellipse(x + 4.5 + paw * 6, y - 7, 1.8, 1.8, P.LILAC)
        else:
            p.ellipse(x + 5, y - 3, 1.8, 1.6, P.LILAC)
        ear(p, x - 1.5, y - 15, 5, P.LILAC, inner=P.HM_GLASS_L, lean=-0.8, half=2.6)
        ear(p, x + 6, y - 15, 5, P.LILAC, inner=P.HM_GLASS_L, lean=0.8, half=2.6)
        p.ellipse(x + 2.5, y - 11, 6.5, 5.5, P.LILAC)                         # big head
    c.ellipse(x + 3, y - 8, 3, 1.4, P.WHITE)
    for dx, dy in ((-3, -2), (0, -1), (-1, 1)):                                # wispy fur on the chest
        c.px(x + dx, y + dy, P.LILAC_D)
    face(c, x + 4, y - 12.5, eyes=eyes, mouth=mouth, gap=5, eye=P.INDIGO, nose=P.HM_GLASS_D, blush=P.HM_GLASS_L, size=3)


def ghost_cat_frame(step: int = 0, paw: float = 0, eyes: str = "open", mouth: str = "w", alpha: int = 200,
                    lean: float = 0) -> Image.Image:
    size, cx, gy = (38, 32), 19, 25
    c = Canvas(*size)
    bob = (0, -1, -1, 0)[step % 4]
    ghost_body(c, cx + lean, gy + bob, wisp=(-1, 0, 1, 0)[step % 4], paw=paw, eyes=eyes, mouth=mouth)
    c.outline(P.HM_GLASS)                                                     # bright spirit outline
    body = see_through(c.img, alpha)
    glow = Canvas(*size)                                                      # a soft violet aura around it
    glow.paste(c.img)
    glow.outline((*P.HM_FOG[:3], 90))
    out = Image.new("RGBA", size, P.CLEAR)
    aura = Image.new("RGBA", size, P.CLEAR)
    px, src = aura.load(), glow.img.load()
    orig = c.img.load()
    for yy in range(size[1]):
        for xx in range(size[0]):
            if src[xx, yy][3] and not orig[xx, yy][3]:
                px[xx, yy] = src[xx, yy]
    out.alpha_composite(aura)
    out.alpha_composite(body)
    return out


def ghost_cat() -> Sprite:
    size, cx, gy = (38, 32), 19, 25
    sprite = Sprite("ghost_cat", size, faces_left=True, cx=cx, ground=gy)
    floating = [ghost_cat_frame(k) for k in range(4)]
    sprite.add("float", floating, fps=6)
    # Blinking out: thinner and thinner (the game shows it as harmless while faded).
    sprite.add("fade", [see_through(floating[0], a) for a in (150, 100, 60, 30)], fps=10, loop=False)
    charge = Canvas(*size)
    charge.paste(ghost_cat_frame(1, paw=0.6, eyes="angry", mouth="open"))
    orb(charge, cx + 13, gy - 8, 2, 0)
    sprite.add("attack", [ghost_cat_frame(0, eyes="angry", mouth="flat", lean=-1), charge.img,
                          ghost_cat_frame(2, paw=1, eyes="open", mouth="open")], fps=8, loop=False)
    hurt = ghost_cat_frame(1, eyes="shut", mouth="open", lean=-1)
    sprite.add("hit", hit_frames(hurt, [(cx - 7, gy - 18), (cx + 12, gy - 16), (cx + 9, gy - 1)]), fps=10, loop=False)
    return sprite


def spirit_ball() -> Sprite:
    sprite = Sprite("spirit_ball", (10, 10), faces_left=True)
    frames = []
    for k in range(4):
        c = Canvas(10, 10)
        orb(c, 4.5, 4.5, 3.4 + (k % 2) * 0.3, k)
        c.ellipse(4.5, 4.5, 1.6, 1.6, P.HM_GLASS_D)                           # the dark eye of the spirit ball
        c.px(4.5, 4.5, P.WHITE)
        frames.append(c.img)
    sprite.add("fly", frames, fps=10)
    return sprite


# --- bat cat [14x10] -------------------------------------------------------------------------------

def bat_wing(c: Canvas, root: tuple[float, float], side: int, flap: float, far: bool, swept: float = 0) -> None:
    rx, ry = root
    span = (15 if not far else 13) * (1 - swept * 0.35)
    tip = (rx + side * span, ry - 3 - flap * 6 + swept * 4)
    elbow = (rx + side * span * 0.45, ry - 4 - flap * 4.5 + swept * 2)
    low = ry + 2.5 - flap * 2
    pts = [root, elbow, tip]
    fingers = []
    for k, t in enumerate((0.82, 0.62, 0.42, 0.22)):
        x = rx + side * span * t
        y = tip[1] + (low - tip[1]) * (1 - t) + 2
        if k % 2 == 0:
            pts.append((x, y + 3))
        else:
            pts.append((x, y))
            fingers.append((x, y))
    pts.append((rx, ry + 3))
    with shaded(c, PINK_WING, EDGE, up=1, down=1) as p:
        p.poly(pts, P.HM_GLASS_D if far else P.HM_GLASS)
    with shaded(c, NAVY_RAMP) as p:
        p.line(root, elbow, P.SPIDER, 2)
        p.line(elbow, tip, P.SPIDER, 1)
    for f in fingers:
        c.line(elbow, f, P.SPIDER)
    c.px(tip[0], tip[1], P.HM_GLASS_L)


def bat_frame(flap: float, eyes: str = "open", mouth: str = "fangs", bob: float = 0, dive: float = 0) -> Image.Image:
    size, cx, gy = (40, 28), 20, 22
    c = Canvas(*size)
    y = gy + bob
    x = cx + dive * 2
    bat_wing(c, (x - 3, y - 8), -1, flap, far=False, swept=dive)
    bat_wing(c, (x + 3, y - 8), 1, flap * 0.85, far=True, swept=dive)
    with shaded(c, NAVY_RAMP, EDGE, up=2) as p:
        p.ellipse(x - 1, y - 4, 4.5, 3.8, P.SPIDER)                           # body
    with shaded(c, PINK_WING, EDGE) as p:                                     # pink feet
        p.rect(x - 3, y - 1, x - 2, y, P.HM_GLASS)
        p.rect(x + 1, y - 1, x + 2, y, P.HM_GLASS)
    with shaded(c, NAVY_RAMP, EDGE, up=2) as p:
        ear(p, x - 3, y - 12.5, 5, P.SPIDER, inner=P.HM_GLASS, lean=-1, half=2.6)
        ear(p, x + 5, y - 12.5, 5, P.SPIDER, inner=P.HM_GLASS, lean=1, half=2.6)
        p.ellipse(x + 1, y - 9, 6.5, 5.5, P.SPIDER)                           # big round head
    c.ellipse(x + 2.5, y - 6.5, 2.4, 1.1, P.LILAC)                           # pale muzzle
    face(c, x + 3, y - 11, eyes=eyes, mouth=mouth, gap=5, eye=P.GOLD, nose=P.HM_GLASS_D, blush=P.HM_GLASS, size=3)
    if eyes in ("open", "angry"):                                              # dark pupils in the gold eyes
        c.px(x + 4, y - 10, P.BLACK)
        c.px(x - 1, y - 10, P.BLACK)
    return c.outline(EDGE).img


def bat() -> Sprite:
    size, cx, gy = (40, 28), 20, 22
    sprite = Sprite("bat", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("fly", [bat_frame(f, bob=b) for f, b in ((1, 0), (0.2, 0), (-0.9, -1), (0.2, -1))], fps=12)
    arc = arc_layer(size, cx + 7, gy - 7, 6, -60, 75, 2)
    sprite.add("attack", [bat_frame(1, eyes="angry", bob=-1), with_overlay(bat_frame(-0.3, eyes="angry", dive=1), arc),
                          bat_frame(0.4, eyes="angry", dive=0.4)], fps=10, loop=False)
    hurt = bat_frame(0.6, eyes="shut", mouth="open")
    sprite.add("hit", hit_frames(hurt, [(cx - 6, gy - 19), (cx + 9, gy - 17), (cx + 3, gy - 1)]), fps=10, loop=False)
    dead = bat_frame(-0.5, eyes="x", mouth="open")
    sprite.add("death", [tint(dead, P.WHITE, 0.6), vanish(dead, 0.45, depth=8, flash=False),
                         vanish(dead, 0.9, depth=8, flash=False)], fps=10, loop=False)
    return sprite


# --- haunted portrait [18x20] + magic_shot ---------------------------------------------------------

def portrait(eyes: str = "glow", mouth: str = "fangs", glow: bool = False) -> Image.Image:
    """A gilded frame (about 20x24) round a dark violet canvas with a black cat face and glowing pink eyes."""
    w, h = 24, 28
    c = Canvas(w, h)
    x0, y0, x1, y1 = 2, 3, 21, 26
    with shaded(c, GOLD_RAMP, EDGE, up=1, down=1) as p:
        p.rect(x0, y0, x1, y1, P.GOLD_D)
        for kx, ky in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):               # corner knobs
            p.ellipse(kx, ky, 1.8, 1.8, P.GOLD_D)
        p.poly([(11.5 - 3, y0), (11.5, y0 - 3), (11.5 + 3, y0)], P.GOLD_D)    # crest at the top
        p.poly([(11.5 - 2, y1), (11.5, y1 + 2), (11.5 + 2, y1)], P.GOLD_D)
    c.rect(x0 + 1, y0 + 1, x1 - 1, y0 + 1, P.GOLD)                              # gilt highlight and orange shade
    c.rect(x0 + 1, y0 + 1, x0 + 1, y1 - 1, P.GOLD)
    c.rect(x0 + 2, y1 - 1, x1 - 1, y1 - 1, P.ORANGE)
    c.rect(x1 - 1, y0 + 2, x1 - 1, y1 - 1, P.ORANGE)
    c.px(11.5, y0 - 1, P.HM_GLASS)
    c.rect(x0 + 3, y0 + 3, x1 - 3, y1 - 3, P.HM_SIL)                          # the painted canvas
    c.rect(x0 + 3, y0 + 3, x1 - 3, y0 + 3, P.GOLD_D)
    c.rect(x0 + 3, y0 + 3, x0 + 3, y1 - 3, P.GOLD_D)
    if glow:                                                                  # magic glowing behind the cat
        c.ellipse(11.5, 14, 7, 6.5, P.HM_CLOUD_D)
    for kx in (8, 15):
        ear(c, kx, 11, 4, P.BLACK, inner=P.HM_SIL_D, lean=-0.8 if kx < 10 else 0.8, half=2.2)
    c.ellipse(11.5, 15, 5, 4.5, P.BLACK)                                      # black cat face
    for ex in (8.5, 13.5):
        if eyes == "glow":
            c.rect(ex, 14, ex + 1, 15, P.HM_GLASS)
            c.px(ex + 1, 14, P.WHITE)
        elif eyes == "angry":
            c.rect(ex, 15, ex + 1, 15, P.HM_GLASS_L)
            c.px(ex + (1 if ex < 10 else 0), 14, P.HM_GLASS)
        elif eyes == "x":
            c.px(ex, 14, P.HM_GLASS)
            c.px(ex + 1, 15, P.HM_GLASS)
            c.px(ex + 1, 14, P.HM_GLASS_D)
            c.px(ex, 15, P.HM_GLASS_D)
        elif eyes == "shut":
            c.rect(ex, 15, ex + 1, 15, P.HM_GLASS_D)
    if mouth == "fangs":
        c.rect(10.5, 17.5, 12.5, 17.5, P.HM_GLASS_D)
        c.px(10.5, 18.5, P.WHITE)
        c.px(12.5, 18.5, P.WHITE)
    elif mouth == "open":
        c.ellipse(11.5, 18, 1.5, 1.2, P.HM_GLASS_D)
    for gx, gy_ in ((x0 + 1, 13), (x1 - 1, 15), (8, y1 - 1), (15, y0 + 1)):   # carved swirls on the gilt
        c.px(gx, gy_, P.GOLD_D)
    return c.outline(EDGE).img


def portrait_frame(tilt: float = 0, lift: float = 0, **kw) -> Image.Image:
    size, cx, gy = (36, 36), 16, 32
    art = portrait(**kw)
    if tilt:
        art = art.rotate(-tilt, resample=Image.NEAREST, expand=True)
    out = Image.new("RGBA", size, P.CLEAR)
    box = art.getbbox()
    piece = art.crop(box)
    out.alpha_composite(piece, (round(cx - (piece.width - 1) / 2), round(gy + 1 - piece.height - lift)))
    return out


def haunted_portrait() -> Sprite:
    size, cx, gy = (36, 36), 16, 32
    sprite = Sprite("haunted_portrait", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [portrait_frame(), portrait_frame(lift=1, eyes="shut")], fps=3)
    sprite.add("move", [portrait_frame(t, 1 if t == 0 and i else 0) for i, t in enumerate((0, 9, 0, -9))], fps=6)
    shot = comet(size, cx + 12, gy - 13, 2.2, 6, 0)
    sprite.add("attack", [portrait_frame(eyes="angry", glow=True),
                          with_overlay(portrait_frame(eyes="angry", mouth="open", glow=True), shot),
                          portrait_frame(-4, eyes="glow")], fps=8, loop=False)
    hurt = portrait_frame(-12, eyes="shut", mouth="open")
    sprite.add("hit", hit_frames(hurt, [(cx - 11, gy - 21), (cx + 12, gy - 18), (cx + 10, gy - 2)]), fps=10, loop=False)
    sprite.add("death", crumbling(portrait_frame(8, eyes="x", mouth="open"), 307), fps=10, loop=False)
    return sprite


def magic_shot() -> Sprite:
    sprite = Sprite("magic_shot", (12, 8), faces_left=True)
    sprite.add("fly", [comet((12, 8), 8, 3.5, 2.6, 7, k) for k in range(2)], fps=10)
    return sprite


# --- cursed armour [20x28] -------------------------------------------------------------------------

def plinth(c: Canvas, x: float, gy: float, grey: bool) -> None:
    rmp = GREY_RAMP if grey else STONE
    base = P.GREY if grey else P.HM_STONE_L
    with shaded(c, rmp, EDGE, up=1, down=1) as p:
        p.rect(x - 11, gy - 7, x + 11, gy, base)
        p.rect(x - 12, gy - 9, x + 12, gy - 7, base)
    c.rect(x - 12, gy - 9, x + 12, gy - 9, P.GREY_L if grey else P.HM_STONE_TOP)
    for px_ in (x - 6, x + 5):                                                 # carved panels
        c.rect(px_ - 3, gy - 5, px_ + 2, gy - 2, P.GREY_D if grey else P.HM_STONE_D)


def armour_body(c: Canvas, x: float, gy: float, grey: bool, step: int = 0, walk: bool = False, swing: float = 0,
                eyes: str = "glow") -> dict:
    """A broad armoured cat knight with a pointed-eared helm and a halberd. swing: 0 = held across the body,
    -1 = raised back, 1 = swept forward."""
    rmp = GREY_RAMP if grey else STONE
    base, dark, light = (P.GREY, P.GREY_D, P.GREY_L) if grey else (P.HM_STONE_L, P.HM_STONE, P.HM_STONE_TOP)
    lifts = ((step % 2) * 2, ((step + 1) % 2) * 2) if walk else (0, 0)
    with shaded(c, rmp, EDGE) as p:                                           # greaves and sabatons
        p.rect(x - 7, gy - 8, x - 3, gy - lifts[0], dark)
        p.rect(x + 2, gy - 8, x + 6, gy - lifts[1], base)
        p.rect(x - 8, gy - 1.5 - lifts[0], x - 2, gy - lifts[0], dark)
        p.rect(x + 1, gy - 1.5 - lifts[1], x + 8, gy - lifts[1], base)
    with shaded(c, rmp, up=2) as p:
        p.ellipse(x - 0.5, gy - 14, 9, 8, base)                               # breastplate
        p.ellipse(x - 1, gy - 9, 7, 3, base)                                  # faulds
    c.line((x - 1, gy - 20), (x - 1, gy - 8), dark)                            # plate seams
    c.line((x - 7, gy - 10), (x + 6, gy - 10), dark)
    for rx_ in (x - 5, x + 3):
        c.px(rx_, gy - 15, light)
    with shaded(c, rmp, EDGE, up=2) as p:                                     # pauldrons
        p.ellipse(x - 8, gy - 19, 3.5, 3, base)
        p.ellipse(x + 7, gy - 19, 3.5, 3, base)
    hx, hy = x + 1, gy - 25
    with shaded(c, rmp, EDGE, up=2) as p:                                     # cat helm
        ear(p, hx - 4, hy - 4, 5, base, inner=None, lean=-0.8, half=2.6)
        ear(p, hx + 4.5, hy - 4, 5, base, inner=None, lean=0.8, half=2.6)
        p.ellipse(hx, hy, 6.5, 6, base)
    c.rect(hx - 4, hy - 0.5, hx + 5, hy + 1.5, P.HM_STONE_DD if not grey else P.SLATE)   # visor slit
    for ex in (hx - 2, hx + 2.5):
        if grey:
            c.rect(ex, hy, ex + 1, hy + 1, P.GREY_D)
        elif eyes == "glow":
            c.rect(ex, hy, ex + 1, hy + 1, P.HM_GLASS)
            c.px(ex + 1, hy, P.WHITE)
        elif eyes == "shut":
            c.rect(ex, hy + 1, ex + 1, hy + 1, P.HM_GLASS_D)
        else:
            c.px(ex, hy, P.HM_GLASS)
            c.px(ex + 1, hy + 1, P.HM_GLASS)
    c.px(hx - 4, hy - 7, P.HM_GLASS_L if not grey else P.GREY_L)               # inner ears
    # Halberd held in both gauntlets.
    if swing > 0:
        butt, head = (x - 6, gy - 11), (x + 20, gy - 15)
    elif swing < 0:
        butt, head = (x + 6, gy - 8), (x - 4, gy - 33)
    else:
        butt, head = (x - 10, gy - 9), (x + 14, gy - 13)
    with shaded(c, WOOD) as p:
        p.line(butt, head, P.BARK_D if grey else P.PLANK_D, 2)
    dx, dy = head[0] - butt[0], head[1] - butt[1]
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    nx, ny = -uy, ux
    blade = [(head[0] - ux * 4 + nx * 1, head[1] - uy * 4 + ny * 1), (head[0] + ux * 3, head[1] + uy * 3),
             (head[0] - ux * 1 - nx * 5, head[1] - uy * 1 - ny * 5), (head[0] - ux * 5 - nx * 4, head[1] - uy * 5 - ny * 4)]
    with shaded(c, GREY_RAMP if grey else ramp((P.WHITE, P.LILAC, P.LILAC_D)), EDGE) as p:
        p.poly(blade, P.GREY if grey else P.LILAC)
    if not grey:
        c.px(head[0] - nx * 2, head[1] - ny * 2, P.HM_GLASS_L)
    hand = (x + 4, gy - 12) if swing >= 0 else (x + 3, gy - 14)
    with shaded(c, rmp, EDGE) as p:                                           # gauntlet over the shaft
        p.ellipse(hand[0], hand[1], 2.4, 2.2, base)
    return {"head": head}


def armour_frame(grey: bool = False, step: int = 0, walk: bool = False, swing: float = 0, eyes: str = "glow",
                 on_plinth: bool = False, lean: float = 0) -> Image.Image:
    size, cx, gy = (56, 50), 22, 47
    c = Canvas(*size)
    feet = gy
    if on_plinth:
        plinth(c, cx, gy, grey)
        feet = gy - 10
    armour_body(c, cx + lean, feet, grey, step, walk, swing, eyes)
    return c.outline(EDGE).img


def cursed_armor() -> Sprite:
    size, cx, gy = (56, 50), 22, 47
    sprite = Sprite("cursed_armor", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("statue", [armour_frame(grey=True, on_plinth=True)], fps=1)
    sprite.add("walk", [armour_frame(step=k, walk=True) for k in range(4)], fps=6)
    arc = arc_layer(size, cx + 18, gy - 18, 10, -60, 80, 2.8)
    sprite.add("attack", [armour_frame(swing=-1, lean=-1, eyes="angry"), armour_frame(swing=-1, lean=-2, eyes="angry"),
                          with_overlay(armour_frame(swing=1, lean=1, eyes="angry"), arc, sparks=[(cx + 27, gy - 32)]),
                          armour_frame(swing=0)], fps=8, loop=False)
    hurt = armour_frame(lean=-1.5, eyes="shut")
    sprite.add("hit", hit_frames(hurt, [(cx + 10, gy - 34), (cx - 12, gy - 26), (cx + 13, gy - 10)]), fps=10, loop=False)
    sprite.add("death", crumbling(armour_frame(eyes="x"), 311), fps=10, loop=False)
    return sprite


# --- candle cat [14x16] + fire_orb -----------------------------------------------------------------

def flame(c: Canvas, x: float, base: float, h: float, k: int) -> None:
    """A magenta candle flame with a white-hot core, flickering by frame `k`."""
    sway = (0, 1, 0, -1)[k % 4]
    c.poly([(x - 2.4, base), (x - 2.2, base - h * 0.45), (x + sway, base - h), (x + 2.2, base - h * 0.5),
            (x + 2.4, base)], P.HM_GLASS)
    c.poly([(x - 1.5, base), (x + sway * 0.5, base - h * 0.65), (x + 1.5, base)], P.HM_GLASS_L)
    c.rect(x - 0.5, base - 2, x + 0.5, base - 0.5, P.WHITE)
    c.px(x + sway * 1.5, base - h - 1.5, P.HM_GLASS_L)


def candle_body(c: Canvas, x: float, gy: float, k: int = 0, squash: float = 0, paw: float = 0, eyes: str = "open",
                mouth: str = "w", melt: float = 0) -> None:
    """A white wax cat whose head is the candle top: wax drips down its sides into a violet pool at the foot."""
    h = 1 - melt
    with shaded(c, ramp((P.PURPLE_L, P.PURPLE, P.PURPLE_D)), EDGE) as p:       # pooled violet wax at the foot
        p.ellipse(x, gy - 1.5, 7 + melt * 5, 2 + melt, P.PURPLE)
        p.rect(0, gy + 1, p.size[0], p.size[1], P.CLEAR)
    with shaded(c, WAX, up=2) as p:
        p.ellipse(x, gy - 5.5 * h, 5.5, max(1.5, 4.5 * h), P.HM_WAX)          # round wax body
        p.rect(x - 5, gy - 5 * h, x + 5, gy - 2, P.HM_WAX)
        if h > 0.3:
            ear(p, x - 4.5, gy - 16 * h + squash, 4.5 * h, P.HM_WAX, inner=P.HM_GLASS_L, lean=-1, half=2.4)
            ear(p, x + 5.5, gy - 16 * h + squash, 4.5 * h, P.HM_WAX, inner=P.HM_GLASS_L, lean=1, half=2.4)
        p.ellipse(x + 0.5, gy - 12 * h + squash, 7, 5.5 * max(h, 0.5), P.HM_WAX)   # big round head
        if paw:
            p.line((x + 5, gy - 8), (x + 5 + paw * 4, gy - 11 - paw * 2), P.HM_WAX, 2)
            p.ellipse(x + 5.5 + paw * 4, gy - 11.5 - paw * 2, 1.6, 1.6, P.HM_WAX)
        else:
            p.ellipse(x + 6, gy - 6, 1.6, 1.5, P.HM_WAX)
    for dx, ln in ((-4, 3), (-1, 4), (3, 2)):                                  # wax drips down the body
        c.line((x + dx, gy - 7 * h + squash + 1), (x + dx, gy - 7 * h + squash + ln), P.HM_WAX_D)
        c.px(x + dx, gy - 7 * h + squash + ln + 1, P.WHITE)
    if h > 0.3:
        face(c, x + 2, gy - 13.5 * h + squash, eyes=eyes, mouth=mouth, gap=5, eye=P.INDIGO, nose=P.HM_GLASS_D,
             blush=P.HM_GLASS_L, size=3)
    c.line((x + 0.5, gy - 17 * h + squash), (x + 0.5, gy - 18.5 * h + squash), P.SLATE)   # wick
    flame(c, x + 0.5, gy - 18 * h + squash, 6.5 * max(h, 0.6), k)


def candle_cat() -> Sprite:
    size, cx, gy = (28, 36), 13, 33
    sprite = Sprite("candle_cat", size, faces_left=True, cx=cx, ground=gy)

    def f(k=0, squash=0, paw=0, eyes="open", mouth="w", melt=0, dx=0):
        c = Canvas(*size)
        candle_body(c, cx + dx, gy, k, squash, paw, eyes, mouth, melt)
        return c.outline(EDGE).img

    sprite.add("idle", [f(0), f(1, eyes="shut")], fps=4)
    sprite.add("move", [f(k, squash=(0, 1, 0, 0.5)[k], dx=(0, 0.5, 1, 0.5)[k]) for k in range(4)], fps=8)
    fire = comet(size, cx + 10, gy - 13, 2.4, 5, 1)
    sprite.add("attack", [f(2, squash=1, eyes="angry", mouth="flat"), with_overlay(f(3, paw=1, eyes="angry", mouth="open"), fire),
                          f(0, paw=0.4)], fps=8, loop=False)
    hurt = f(1, squash=1, eyes="shut", mouth="open")
    sprite.add("hit", hit_frames(hurt, [(cx - 8, gy - 22), (cx + 9, gy - 18), (cx + 8, gy - 3)]), fps=10, loop=False)
    sprite.add("death", [tint(f(0, eyes="x", mouth="open"), P.WHITE, 0.6), f(1, eyes="x", mouth="open", melt=0.35),
                         see_through(f(2, eyes="x", mouth="open", melt=0.6), 200),
                         see_through(f(3, eyes="x", mouth="open", melt=0.8), 110)], fps=8, loop=False)
    return sprite


def fire_orb() -> Sprite:
    sprite = Sprite("fire_orb", (10, 10), faces_left=True)
    frames = []
    for k in range(4):
        c = Canvas(10, 10)
        for i, (dx, dy) in enumerate(((-3, -1), (-3.5, 1), (-2, -2.5))):     # flickering flame licks behind it
            c.ellipse(5 + dx - (k + i) % 2 * 0.5, 5 + dy, 1.4, 1.2, (*P.HM_GLASS_D[:3], 200))
        orb(c, 5.5, 5, 3, k)
        frames.append(c.img)
    sprite.add("fly", frames, fps=12)
    return sprite


# --- poltergeist book [16x14] + magic_bolt ---------------------------------------------------------

def book(c: Canvas, x: float, y: float, opening: float, k: int = 0, eyes: str = "glow") -> None:
    """A purple book with gold corners and a cat crest, floating; (x, y) is the middle of its spine bottom.
    opening: 0 = shut (we see the front cover), 1 = flung wide like wings with cream pages."""
    if opening < 0.15:
        with shaded(c, BOOK, EDGE, up=2) as p:
            p.rect(x - 7, y - 15, x + 7, y, P.PURPLE)                        # front cover
            p.rect(x - 9, y - 15, x - 7, y, P.PURPLE_D)                      # spine
        c.rect(x - 9, y - 13, x - 7, y - 13, P.GOLD)
        c.rect(x - 9, y - 3, x - 7, y - 3, P.GOLD)
        cover_x = x
    else:
        spread = 4 + opening * 7
        with shaded(c, BOOK, EDGE) as p:                                      # back cover, flung open
            p.poly([(x - 1, y - 15), (x - 1 - spread, y - 14 + opening * 3), (x - 1 - spread, y + 1 + opening * 2),
                    (x - 1, y)], P.PURPLE_D)
        with shaded(c, ramp((P.WHITE, P.CREAM, P.CREAM_D)), EDGE) as p:       # fanned pages
            p.poly([(x, y - 14), (x - spread + 1, y - 13 + opening * 3), (x - spread + 1, y + opening * 2),
                    (x, y - 1)], P.CREAM)
        for i in range(3):
            t = 0.3 + i * 0.25
            c.line((x - 1, y - 12 + i * 4), (x - spread * t, y - 11 + i * 4 + opening * t * 2), P.CREAM_D)
        cover_x = x + 1 + opening * 2
        with shaded(c, BOOK, EDGE, up=2) as p:                                # front cover, swung out a little
            p.poly([(x, y - 15), (cover_x + 13, y - 15 - opening * 2), (cover_x + 13, y - opening), (x, y)], P.PURPLE)
        cover_x += 6
    cx_ = cover_x
    lift = opening * 1.5 if opening >= 0.15 else 0
    for gx, gy_ in ((cx_ - 6, y - 14 - lift), (cx_ + 6, y - 14 - lift), (cx_ - 6, y - 1), (cx_ + 6, y - 1)):   # gold corners
        c.rect(gx - 0.5, gy_, gx + 0.5, gy_ + 1, P.GOLD)
    c.rect(cx_ - 7, y - 15 - lift, cx_ + 6.5, y - 15 - lift, P.GOLD_D)
    # The cat crest on the cover.
    ear(c, cx_ - 2.5, y - 10 - lift * 0.5, 2.5, P.GOLD, inner=None, lean=-0.5, half=1.4)
    ear(c, cx_ + 2.5, y - 10 - lift * 0.5, 2.5, P.GOLD, inner=None, lean=0.5, half=1.4)
    c.ellipse(cx_, y - 7.5 - lift * 0.5, 3.6, 3, P.GOLD)
    c.ellipse(cx_, y - 7.5 - lift * 0.5, 2.6, 2, P.PURPLE_D)
    for ex in (cx_ - 1.5, cx_ + 1.5):
        c.px(ex, y - 8 - lift * 0.5, P.HM_GLASS_L if eyes == "glow" else (P.GOLD if eyes == "x" else P.PURPLE))


def book_frame(opening: float, k: int = 0, bob: float = 0, eyes: str = "glow", glow: bool = False) -> Image.Image:
    size, cx, gy = (36, 28), 16, 24
    c = Canvas(*size)
    book(c, cx, gy + bob - (opening * 2 + 1 if opening >= 0.15 else 0), opening, k, eyes)
    out = c.outline(EDGE).img
    if glow:                                                                  # magic welling from the pages
        g = Canvas(*size)
        for i, (dx, dy) in enumerate(((-6, -18), (-3, -21), (-9, -16))):
            magic_sparkle(g, cx + dx, gy + bob + dy, big=i == 0)
        out.alpha_composite(g.img)
    return out


def poltergeist_book() -> Sprite:
    size, cx, gy = (36, 28), 16, 24
    sprite = Sprite("poltergeist_book", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [book_frame(0), book_frame(0, bob=-1)], fps=3)
    sprite.add("move", [book_frame(o, k, b) for k, (o, b) in enumerate(((0.3, 0), (1.0, -1), (0.6, -1), (0.2, 0)))], fps=8)
    bolt = comet(size, cx + 15, gy - 10, 2.3, 6, 2)
    sprite.add("attack", [book_frame(0.8, glow=True), with_overlay(book_frame(1.0, glow=True), bolt), book_frame(0.3)],
               fps=8, loop=False)
    hurt = book_frame(0.5, eyes="x")
    sprite.add("hit", hit_frames(hurt, [(cx + 13, gy - 19), (cx - 11, gy - 16), (cx + 14, gy - 3)]), fps=10, loop=False)
    # Death: the book bursts and its pages flutter away in a magenta flare.
    frames = [tint(book_frame(1.0, eyes="x"), P.WHITE, 0.6)]
    rnd = noise(331)
    pages = [(cx + (rnd() - 0.5) * 8, gy - 9 + (rnd() - 0.5) * 6, (rnd() - 0.5) * 3, -0.6 - rnd() * 1.1) for _ in range(6)]
    for t in (0.33, 0.66, 1.0):
        c = Canvas(*size)
        for i, (px_, py_, vx, vy) in enumerate(pages):
            x, y = px_ + vx * t * 6, py_ + vy * t * 6 + t * t * 6
            c.rect(x - 1.5, y - 1, x + 1.5, y + 1, P.CREAM)
            c.line((x - 1, y), (x + 1, y), P.CREAM_D)
        flare = max(0.0, 1 - t * 1.2)
        if flare:
            c.ellipse(cx, gy - 6, 6 * flare + 1, 7 * flare + 1, P.HM_GLASS)
            c.ellipse(cx, gy - 6, 3 * flare + 0.5, 4 * flare + 0.5, P.HM_GLASS_L)
        c.outline(EDGE)
        frames.append(see_through(c.img, int(255 * (1 - t * 0.6))))
    sprite.add("death", frames, fps=8, loop=False)
    return sprite


def magic_bolt() -> Sprite:
    sprite = Sprite("magic_bolt", (10, 10), faces_left=True)
    sprite.add("fly", [comet((10, 10), 6.5, 4.5, 2.6, 6, k) for k in range(2)], fps=10)
    return sprite


# --- gargoyle cat [20x24] --------------------------------------------------------------------------

def stone_wing(c: Canvas, root: tuple[float, float], spread: float) -> None:
    """A bony stone bat wing rising up and back from the shoulder; spread 0 = folded up, 1 = wide."""
    rx, ry = root
    span = 9 + spread * 8
    tip = (rx - span * 0.7, ry - 12 - spread * 2)
    pts = [root, (rx - 2, ry - 8 - spread * 2), tip]
    for t, d in ((0.85, 0), (0.6, 2.5), (0.35, 0)):
        pts.append((rx + (tip[0] - rx) * t - 1, ry - (12 + spread * 2) * t * 0.35 + d + 2))
    pts.append((rx - 1, ry + 2))
    with shaded(c, WARM, EDGE, up=1, down=1) as p:
        p.poly(pts, P.GG_STONE)
    for t in (0.85, 0.6):
        c.line((rx - 2, ry - 8 - spread * 2), (rx + (tip[0] - rx) * t - 1, ry - (12 + spread * 2) * t * 0.35 + 2),
               P.GG_STONE_D)
    c.px(tip[0], tip[1], P.GG_STONE_TOP)


def gargoyle_body(c: Canvas, x: float, gy: float, pose: str, step: int = 0, eyes: str = "glow", mouth: str = "fangs",
                  spread: float = 0) -> None:
    """A stone cat: sitting (on its pedestal), crouched to spring, mid-leap, or walking on four legs."""
    if pose == "leap":
        bx, by = x, gy - 12
        stone_wing(c, (bx - 2, by - 8), 1)
        with shaded(c, WARM, up=2) as p:
            p.ellipse(bx - 1, by - 3, 7, 4.5, P.GG_STONE_L)                  # stretched body
            p.line((bx + 4, by), (bx + 9, by + 3), P.GG_STONE_L, 3)           # forelegs reaching
            p.line((bx - 5, by), (bx - 10, by + 4), P.GG_STONE_L, 3)          # hind legs trailing
            p.line((bx - 7, by - 4), (bx - 12, by - 6), P.GG_STONE_L, 2)      # tail
        hx, hy = bx + 6, by - 7
    elif pose == "walk":
        bx, by = x, gy
        stone_wing(c, (bx - 3, by - 10), 0.2)
        lifts = ((step % 2) * 1.5, ((step + 1) % 2) * 1.5)
        with shaded(c, WARM, EDGE) as p:
            for lx, lf in ((bx - 6, lifts[0]), (bx + 3, lifts[1])):
                p.rect(lx, by - 6 - lf, lx + 2.5, by - lf, P.GG_STONE)
        with shaded(c, WARM, up=2) as p:
            p.ellipse(bx - 1, by - 8, 8, 4.5, P.GG_STONE_L)
            p.line((bx - 8, by - 9), (bx - 12, by - 13), P.GG_STONE_L, 2)
        with shaded(c, WARM, EDGE) as p:
            for lx, lf in ((bx - 4, lifts[1]), (bx + 5, lifts[0])):
                p.rect(lx, by - 6 - lf, lx + 2.5, by - lf, P.GG_STONE_L)
        hx, hy = bx + 6, by - 13
    else:                                                                     # sit (on the pedestal) or crouch
        crouch = 1.5 if pose == "crouch" else 0
        bx, by = x, gy - 10 + crouch
        stone_wing(c, (bx - 3, by - 11), spread)
        with shaded(c, WARM, up=2) as p:
            p.ellipse(bx - 1, by - 6.5, 6.5, 6.5, P.GG_STONE_L)               # haunch and chest
            p.ellipse(bx - 4, by - 3, 4, 3.5, P.GG_STONE_L)
            p.line((bx - 7, by - 1), (bx - 11, by - 4), P.GG_STONE_L, 2)      # tail curled on the plinth
        with shaded(c, WARM, EDGE) as p:                                     # front legs and paws
            p.rect(bx + 2, by - 6, bx + 4.5, by, P.GG_STONE_L)
            p.ellipse(bx + 3.8, by - 0.5, 2, 1, P.GG_STONE_L)
        hx, hy = bx + 4, by - 15 + crouch
    with shaded(c, WARM, EDGE, up=2) as p:
        ear(p, hx - 3.5, hy - 4, 5, P.GG_STONE_L, inner=P.HM_GLASS_D, lean=-1, half=2.6)
        ear(p, hx + 4, hy - 4, 5, P.GG_STONE_L, inner=P.HM_GLASS_D, lean=1, half=2.6)
        p.ellipse(hx, hy, 6, 5.2, P.GG_STONE_L)
    c.ellipse(hx + 1.5, hy + 2.5, 3, 1.5, P.GG_STONE_TOP)                     # muzzle
    for kx, ky in ((hx - 4, hy + 1), (hx - 2, hy - 3)):                         # weathering
        c.px(kx, ky, P.GG_STONE)
    eye_colour = P.HM_FLAME if eyes in ("glow", "angry") else P.GG_STONE_DD
    face(c, hx + 1.5, hy - 2, eyes="glow" if eyes == "glow" else eyes, mouth=mouth, gap=5, eye=eye_colour,
         nose=P.GG_STONE_D, blush=None, size=3)
    if eyes in ("glow", "angry"):                                             # amber eyes with a hot white core
        for ex in (hx + 1.5, hx - 3.5):
            c.px(ex + 1, hy - 1 if eyes == "glow" else hy, P.WHITE)
            c.px(ex + 2, hy - 2 if eyes == "glow" else hy - 1, P.HM_FLAME_D if eyes == "angry" else P.WHITE)


def pedestal(c: Canvas, x: float, gy: float) -> None:
    with shaded(c, STONE, EDGE, up=1, down=1) as p:
        p.rect(x - 9, gy - 8, x + 9, gy, P.HM_STONE)
        p.rect(x - 10, gy - 10, x + 10, gy - 8, P.HM_STONE_L)
    c.rect(x - 10, gy - 10, x + 10, gy - 10, P.HM_STONE_TOP)
    for px_ in (x - 5, x + 4):
        c.rect(px_ - 2.5, gy - 6, px_ + 2.5, gy - 2, P.HM_STONE_D)
        c.px(px_, gy - 4, P.HM_STONE)


def gargoyle_frame(pose: str = "sit", step: int = 0, eyes: str = "glow", mouth: str = "fangs", spread: float = 0,
                   trail: bool = False) -> Image.Image:
    size, cx, gy = (46, 46), 21, 43
    c = Canvas(*size)
    if pose in ("sit", "crouch"):
        pedestal(c, cx, gy)
    cat = Canvas(*size)
    gargoyle_body(cat, cx, gy, pose, step, eyes, mouth, spread)
    rim(cat, {P.GG_STONE_DD: P.GG_STONE_D, P.GG_STONE_D: P.GG_STONE, P.GG_STONE: P.GG_STONE_L,
              P.GG_STONE_L: P.GG_STONE_TOP, P.GG_STONE_TOP: P.WHITE})        # a light inner edge all round
    c.paste(cat)
    out = c.outline(EDGE).img
    if trail:                                                                 # a magenta streak behind the leap
        t = Canvas(*size)
        for i, (dx, dy, ln) in enumerate(((-13, -8, 5), (-11, -5, 7), (-14, -2, 4))):
            t.line((cx + dx - ln, gy + dy), (cx + dx, gy + dy - 3), P.HM_GLASS if i % 2 else P.HM_GLASS_D)
        out.alpha_composite(see_through(t.img, 200))
    return out


def gargoyle_cat() -> Sprite:
    size, cx, gy = (46, 46), 21, 43
    sprite = Sprite("gargoyle_cat", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [gargoyle_frame("sit", eyes="shut", mouth="flat")], fps=1)
    sprite.add("prepare", [gargoyle_frame("crouch", spread=0.3), gargoyle_frame("crouch", spread=0.6, eyes="angry")], fps=6)
    sprite.add("leap", [gargoyle_frame("leap", spread=1, trail=True), gargoyle_frame("leap", eyes="angry", trail=True),
                        gargoyle_frame("leap", mouth="open")], fps=8, loop=False)
    sprite.add("walk", [gargoyle_frame("walk", step=k) for k in range(4)], fps=6)
    hurt = gargoyle_frame("walk", eyes="shut", mouth="open")
    sprite.add("hit", hit_frames(hurt, [(cx + 12, gy - 24), (cx - 10, gy - 22), (cx + 14, gy - 8)]), fps=10, loop=False)
    sprite.add("death", crumbling(gargoyle_frame("walk", eyes="x", mouth="open"), 337), fps=10, loop=False)
    return sprite


# --- shadow cat [16x20] ----------------------------------------------------------------------------

def smoke(c: Canvas, x: float, y: float, w: float, seed: int, k: int = 0) -> None:
    """Curling violet smoke along `y`, about `w` wide."""
    rnd = noise(seed + k)
    for i in range(7):
        sx = x - w / 2 + rnd() * w
        r = 1.4 + rnd() * 1.8
        c.ellipse(sx, y - rnd() * 3, r, r * 0.8, P.HM_FOG_D if i % 2 else P.HM_FOG)
        c.px(sx - r * 0.3, y - rnd() * 3 - r * 0.5, P.HM_FOG_L)


def shadow_body(c: Canvas, x: float, gy: float, pose: str = "stand", step: int = 0, eyes: str = "glow",
                mouth: str = "fangs") -> None:
    """A black cat edged in violet light: a chunky stance, or a low stretched dash."""
    if pose == "dash":
        with shaded(c, SHADOW, up=2, down=1) as p:
            p.ellipse(x - 1, gy - 7, 9, 4.5, P.HM_SIL)                       # stretched body
            p.line((x + 5, gy - 5), (x + 10, gy - 1), P.HM_SIL, 3)            # forelegs reaching
            p.line((x - 6, gy - 5), (x - 11, gy - 2), P.HM_SIL, 3)            # hind legs pushing
            p.line((x - 9, gy - 9), (x - 14, gy - 12), P.HM_SIL, 2)           # tail
        hx, hy = x + 6, gy - 12
    else:
        lifts = ((step % 2) * 1.5, ((step + 1) % 2) * 1.5)
        with shaded(c, SHADOW, up=2, down=1) as p:
            p.line((x - 6, gy - 8), (x - 10, gy - 13 - (step % 2)), P.HM_SIL, 2)   # tail up
            p.ellipse(x - 0.5, gy - 8, 6.5, 6, P.HM_SIL)                     # body
            for lx, lf in ((x - 5, lifts[0]), (x + 2, lifts[1])):
                p.rect(lx, gy - 4 - lf, lx + 3, gy - lf, P.HM_SIL)
        hx, hy = x + 3, gy - 16
    with shaded(c, SHADOW, up=2, down=1) as p:
        ear(p, hx - 4, hy - 4, 5.5, P.HM_SIL, inner=P.HM_FOG_D, lean=-1, half=2.8)
        ear(p, hx + 4, hy - 4, 5.5, P.HM_SIL, inner=P.HM_FOG_D, lean=1, half=2.8)
        p.ellipse(hx, hy, 6.5, 5.5, P.HM_SIL)
    for ex in (hx - 3.5, hx + 1.5):                                            # glowing violet eyes
        if eyes == "glow":
            c.rect(ex, hy - 1, ex + 2, hy, P.HM_GLASS_L)
            c.rect(ex, hy - 1, ex + 2, hy - 1, P.WHITE)
        elif eyes == "angry":
            c.rect(ex, hy, ex + 2, hy, P.WHITE)
            c.px(ex + (2 if ex < hx else 0), hy - 1, P.HM_GLASS_L)
        elif eyes == "shut":
            c.rect(ex, hy, ex + 2, hy, P.HM_FOG_D)
        elif eyes == "x":
            c.px(ex, hy - 1, P.HM_FOG_L)
            c.px(ex + 2, hy - 1, P.HM_FOG_L)
            c.px(ex + 1, hy, P.HM_FOG_L)
            c.px(ex, hy + 1, P.HM_FOG_L)
            c.px(ex + 2, hy + 1, P.HM_FOG_L)
    if mouth == "fangs":
        c.rect(hx - 1, hy + 2.5, hx + 1, hy + 2.5, P.HM_FOG_D)
        c.px(hx - 1, hy + 3, P.WHITE)
        c.px(hx + 1, hy + 3, P.WHITE)
    elif mouth == "open":
        c.ellipse(hx, hy + 3, 1.2, 1, P.HM_GLASS_D)


def shadow_frame(pose: str = "stand", step: int = 0, eyes: str = "glow", mouth: str = "fangs", dx: float = 0,
                 alpha: int = 255, streaks: int = 0) -> Image.Image:
    size, cx, gy = (56, 34), 26, 31
    c = Canvas(*size)
    shadow_body(c, cx + dx, gy, pose, step, eyes, mouth)
    rim(c, {P.HM_SIL: P.HM_FOG, P.HM_SIL_D: P.HM_FOG, P.HM_FOG_D: P.HM_FOG_L, P.HM_FOG_DD: P.HM_FOG})   # bright violet rim
    c.outline(EDGE)
    body = c.img if alpha == 255 else see_through(c.img, alpha)
    out = Canvas(*size)
    smoke(out, cx + dx - 1, gy, 14, 401, step)                                # smoke curling at its feet
    if streaks:
        rnd = noise(409 + streaks)
        for i in range(5):
            y = gy - 4 - i * 3.5
            ln = 5 + rnd() * 4 * streaks
            out.line((cx + dx - 8 - ln, y), (cx + dx - 6, y), P.HM_FOG if i % 2 else P.HM_FOG_L)
            out.px(cx + dx - 8 - ln - 1, y, P.HM_FOG_D)
    out.paste(body)
    out.rect(0, gy + 2, size[0], size[1], P.CLEAR)                           # nothing below the ground line
    return out.img


def clear_below(img: Image.Image, y0: int) -> None:
    """Clears every row from `y0` down (smoke never sinks below the ground line)."""
    img.paste(P.CLEAR, (0, y0, img.width, img.height))


def shadow_cat() -> Sprite:
    size, cx, gy = (56, 34), 26, 31
    sprite = Sprite("shadow_cat", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [shadow_frame(step=0), shadow_frame(step=1, eyes="angry")], fps=3)

    def wisp(alpha):                                                          # only smoke and eyes, fading in
        c = Canvas(*size)
        smoke(c, cx, gy, 18, 417)
        smoke(c, cx + 1, gy - 7, 10, 419)
        for ex in (cx + 0, cx + 5):
            c.rect(ex, gy - 17, ex + 2, gy - 16, P.WHITE)
            c.rect(ex, gy - 16, ex + 2, gy - 16, P.HM_GLASS_L)
        out = see_through(c.img, alpha)
        clear_below(out, gy + 2)
        return out

    sprite.add("teleport", [wisp(230), shadow_frame("dash", dx=-2, alpha=150, streaks=2),
                            shadow_frame("dash", alpha=220, streaks=1), shadow_frame(eyes="angry")], fps=10, loop=False)
    arc = arc_layer(size, cx + 14, gy - 12, 10, -70, 80, 2.8)
    sprite.add("attack", [shadow_frame(eyes="angry", dx=-1), shadow_frame("dash", eyes="angry", streaks=2),
                          with_overlay(shadow_frame("dash", eyes="angry", mouth="open", dx=2, streaks=1), arc,
                                       sparks=[(cx + 25, gy - 25)]),
                          shadow_frame(eyes="glow")], fps=10, loop=False)
    hurt = shadow_frame(eyes="shut", mouth="open", dx=-1)
    sprite.add("hit", hit_frames(hurt, [(cx + 12, gy - 24), (cx - 9, gy - 22), (cx + 13, gy - 6)]), fps=10, loop=False)
    still = shadow_frame(eyes="x", mouth="open")
    frames = [tint(still, P.WHITE, 0.6)]
    for t in (0.35, 0.65, 0.95):                                              # dissolves into smoke
        c = Canvas(*size)
        smoke(c, cx, gy, 16 + t * 10, 431, int(t * 4))
        smoke(c, cx + 2, gy - 6 - t * 6, 10 + t * 8, 433, int(t * 4))
        frame = vanish(still, t, depth=-4, flash=False)
        frame.alpha_composite(see_through(c.img, int(240 * (1 - t * 0.7))))
        clear_below(frame, gy + 2)
        frames.append(frame)
    sprite.add("death", frames, fps=10, loop=False)
    return sprite


def build() -> list[Sprite]:
    return [ghost_cat(), spirit_ball(), bat(), haunted_portrait(), magic_shot(), cursed_armor(), candle_cat(), fire_orb(),
            poltergeist_book(), magic_bolt(), gargoyle_cat(), shadow_cat()]
