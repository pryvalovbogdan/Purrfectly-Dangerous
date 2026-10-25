"""Sakura world, level 1 critters (from `docs/concept/Sakura World Level 1 Enemy Sprite Sheet.png`): the sakura
slime, sakura bunny, lantern spirit, bird crow, spike plant (a lotus bud) and rolling onigiri, the blossom shots
they fire, and the tiny sakura spirit the boss summons.

Drawn facing right with light from the top-left and mirrored on export. The world is bright pink and blue, so
every critter has a strong dark outline, light rims along its top edges and a pink blossom somewhere on it;
effects are petals and glowing blossoms. Gameplay hitboxes (w x h, at the feet) are noted on each sprite."""
from __future__ import annotations

import math

from PIL import Image

import palette as P
from critters import ear, face, ramp, shaded, sparkle
from draw import Canvas, noise, see_through, tint, vanish
from sprite import Sprite

EDGE = P.OUTLINE
PINK = ramp((P.SK_PINK_L, P.SK_PINK, P.SK_PINK_D), (P.WHITE, P.SK_PINK_L, P.SK_PINK), (P.SK_PINK, P.SK_PINK_D, P.SK_PINK_DD))
RICE = ramp((P.WHITE, P.SK_RICE_L, P.SK_RICE), (P.SK_RICE_L, P.SK_RICE, P.SK_RICE_D))
CROW = ramp((P.SK_CROW_L, P.SK_CROW, P.SK_CROW_D))
LEAF = ramp((P.KIT_GREEN_L, P.KIT_GREEN, P.KIT_GREEN_D))
LACQUER = ramp((P.CAPE_L, P.SK_LACQUER, P.SK_LACQUER_D))
NORI = ramp((P.SK_NORI_L, P.SK_NORI, P.BLACK))


# --- shared helpers --------------------------------------------------------------------------------

def blossom(c: Canvas, x: float, y: float, r: float = 2.0, turn: float = 0.0, glow: bool = False) -> None:
    """A five-petal cherry blossom centred on (x, y) with a pale centre."""
    for i in range(5):
        a = turn + i / 5 * math.tau - math.pi / 2
        c.ellipse(x + math.cos(a) * r * 0.9, y + math.sin(a) * r * 0.9, r * 0.65, r * 0.65,
                  P.SK_PINK_L if glow else P.SK_PINK)
    c.ellipse(x, y, max(0.6, r * 0.45), max(0.6, r * 0.45), P.SK_PINK_D if not glow else P.SK_PINK)
    c.px(x, y, P.YELLOW if not glow else P.WHITE)


def petal(c: Canvas, x: float, y: float, k: int = 0) -> None:
    """A single drifting petal, two pixels, turning with `k`."""
    c.px(x, y, P.SK_PINK_L)
    c.px(x + (1 if k % 2 else 0), y + (0 if k % 2 else 1), P.SK_PINK)


def petals(c: Canvas, cx: float, cy: float, spread: float, n: int, seed: int, k: int = 0) -> None:
    rnd = noise(seed)
    for i in range(n):
        petal(c, cx + (rnd() - 0.5) * spread * 2, cy + (rnd() - 0.5) * spread, k + i)


def glow_blossom(size, x: float, y: float, r: float, k: int, tail: float = 0) -> Image.Image:
    """A glowing pink blossom projectile, with a short trail of light behind it."""
    c = Canvas(*size)
    for i in range(int(tail)):
        t = i / max(tail, 1)
        c.ellipse(x - r - 1 - i, y + math.sin(i + k) * 0.5 * t, max(0.5, r * 0.5 * (1 - t)), max(0.5, r * 0.5 * (1 - t)),
                  (*P.SK_PINK[:3], int(230 - t * 130)))
    c.ellipse(x, y, r + 1, r + 1, (*P.SK_PINK[:3], 120))
    blossom(c, x, y, r * 0.8, turn=k * 0.3, glow=True)
    c.outline(P.SK_PINK_D)
    return c.img


def hurt_frames(hurt: Image.Image, pts) -> list[Image.Image]:
    """Hurt: a white flash of the flinch, then the flinch with petals bursting off it."""
    second = Canvas(*hurt.size)
    second.paste(hurt)
    for i, (x, y) in enumerate(pts):
        if i % 2:
            sparkle(second, x, y, P.SK_PINK_L)
        else:
            blossom(second, x, y, 1.4, turn=i)
    return [tint(hurt, P.WHITE, 0.65), second.img]


def scatter(still: Image.Image, cx: float, gy: float, seed: int, depth: float = 4) -> list[Image.Image]:
    """Death: a white flash, then it slumps and fades while petals scatter up and away."""
    frames = [tint(still, P.WHITE, 0.6)]
    for i, t in enumerate((0.35, 0.65, 0.95)):
        f = vanish(still, t, depth=depth, flash=False)
        p_ = Canvas(*still.size)
        rnd = noise(seed)
        for j in range(7):
            x0, y0 = cx + (rnd() - 0.5) * 16, gy - 4 - rnd() * 10
            vx, vy = (rnd() - 0.5) * 10, -3 - rnd() * 5
            petal(p_, x0 + vx * t, y0 + vy * t, j + i)
        f.alpha_composite(see_through(p_.img, int(255 * (1 - t * 0.5))))
        frames.append(f)
    return frames


# --- sakura slime [20x14] --------------------------------------------------------------------------

def slime_body(c: Canvas, cx: float, gy: float, sx: float = 1.0, sy: float = 1.0, eyes: str = "open",
               mouth: str = "w", k: int = 0) -> None:
    """A glossy pink dome with a cherry blossom on its crown."""
    height = 13 * sy
    ry = height * 0.75
    rx = 10 * sx / 0.92
    ey = gy - height + ry
    top = gy - height + 1
    with shaded(c, PINK, up=2, down=1) as p:
        p.ellipse(cx, ey, rx, ry, P.SK_PINK)
        p.rect(0, gy + 1, p.size[0], p.size[1], P.CLEAR)
    c.rect(cx - 6 * sx, top + 3, cx - 6 * sx + 1, top + 4, P.WHITE)            # gloss
    c.px(cx - 4 * sx, top + 2, P.WHITE)
    face(c, cx + 2, gy - 7.5 * sy, eyes=eyes, mouth=mouth, gap=6, eye=P.SAKURA_EYE, nose=None, blush=P.SK_PINK_D,
         mouth_colour=P.SAKURA_EYE, size=3)
    blossom(c, cx + 2, top, 3.4, turn=k * 0.2)


def sakura_slime() -> Sprite:
    size, cx, gy = (34, 28), 17, 25
    sprite = Sprite("sakura_slime", size, faces_left=True, cx=cx, ground=gy)

    def f(sx=1.0, sy=1.0, eyes="open", mouth="w", k=0, puffs=0):
        c = Canvas(*size)
        slime_body(c, cx, gy, sx, sy, eyes, mouth, k)
        out = c.outline(EDGE).img
        if puffs:
            p_ = Canvas(*size)
            petals(p_, cx + 12, gy - 9, 3, puffs, 801 + k, k)
            out.alpha_composite(p_.img)
        return out

    sprite.add("idle", [f(), f(1.04, 0.95, k=1)], fps=4)
    sprite.add("walk", [f(1.1, 0.86), f(0.94, 1.08, k=1), f(1.0, 1.0, mouth="open", k=2), f(0.96, 1.04, k=3)], fps=8)
    sprite.add("attack", [f(1.12, 0.84, eyes="angry", mouth="flat"), f(0.88, 1.12, eyes="angry", mouth="open", puffs=5, k=1),
                          f(1.04, 0.96, k=2)], fps=8, loop=False)
    hurt = f(1.1, 0.9, eyes="shut", mouth="open")
    sprite.add("hurt", hurt_frames(hurt, [(cx - 9, gy - 15), (cx + 9, gy - 14), (cx + 1, gy - 19)]), fps=10, loop=False)
    frames = [tint(f(eyes="x", mouth="open"), P.WHITE, 0.6)]
    for i, (sx, sy, keep) in enumerate(((1.1, 0.7, 255), (1.12, 0.45, 200), (1.12, 0.3, 100))):
        img = f(sx, sy, eyes="x", mouth="flat", k=i)
        p_ = Canvas(*size)
        petals(p_, cx, gy - 10 - i * 3, 8 + i * 2, 6, 811, i)
        img.alpha_composite(p_.img)
        frames.append(see_through(img, keep))
    sprite.add("death", frames, fps=10, loop=False)
    return sprite


# --- sakura bunny [18x20] --------------------------------------------------------------------------

def bunny_frame(pose: str = "sit", step: int = 0, eyes: str = "open", mouth: str = "w", lean: float = 0,
                trail: bool = False) -> Image.Image:
    """A white bunny with long pink-lined ears and a blossom at its neck. pose: sit (upright on its haunches),
    hop (a walk hop), run (stretched leap), lunge (attack), lie (defeated)."""
    size, cx, gy = (44, 36), 18, 33
    c = Canvas(*size)
    x = cx + lean
    if pose == "lie":
        with shaded(c, RICE, up=2) as p:
            p.ellipse(x, gy - 4, 9, 4, P.SK_RICE_L)
            p.ellipse(x + 8, gy - 5, 5, 4, P.SK_RICE_L)
            p.ellipse(x - 2, gy - 9, 5, 1.6, P.SK_RICE_L)                     # ears lying flat
        c.line((x - 5, gy - 9), (x + 1, gy - 9), P.SK_PINK_L)
        face(c, x + 9, gy - 6, eyes="shut", mouth="flat", gap=4, eye=P.SAKURA_EYE, blush=P.SK_PINK, size=2)
        blossom(c, x + 3, gy - 8, 2)
        return c.outline(EDGE).img
    stretch = {"sit": 0, "hop": 0.4, "run": 1.0, "lunge": 1.2}[pose]
    air = {"sit": 0, "hop": (0, 2, 3, 1)[step % 4], "run": (1, 3, 2, 0)[step % 4], "lunge": 2}[pose]
    by = gy - air
    with shaded(c, RICE, EDGE) as p:                                           # hind foot and tail
        p.ellipse(x - 5 - stretch * 3, by - 1.5, 3.5, 1.5, P.SK_RICE)
        p.ellipse(x - 9 - stretch * 2, by - 7, 2.2, 2.2, P.SK_RICE_L)
    with shaded(c, RICE, up=2) as p:
        p.ellipse(x - 1 - stretch, by - 7 + stretch, 7 + stretch * 3, 6 - stretch, P.SK_RICE_L)   # body
        p.ellipse(x - 4 - stretch * 2, by - 5, 4.5, 4.5, P.SK_RICE_L)                              # haunch
    with shaded(c, RICE, EDGE) as p:                                           # front paws
        fx = x + 4 + stretch * 6
        p.ellipse(fx, by - 1.5 - stretch * 2, 1.8, 1.4, P.SK_RICE_L)
    hx, hy = x + 4 + stretch * 5, by - 14 + stretch * 4
    ear_lean = -stretch * 4
    with shaded(c, RICE, EDGE, up=2) as p:                                     # long ears
        p.ellipse(hx - 2 + ear_lean, hy - 9, 1.8, 5.5, P.SK_RICE_L)
        p.ellipse(hx + 2 + ear_lean * 0.8, hy - 9.5, 1.8, 5.5, P.SK_RICE_L)
    c.ellipse(hx - 2 + ear_lean, hy - 9, 0.7, 3.8, P.SK_PINK_L)
    c.ellipse(hx + 2 + ear_lean * 0.8, hy - 9.5, 0.7, 3.8, P.SK_PINK_L)
    with shaded(c, RICE, EDGE, up=2) as p:
        p.ellipse(hx, hy, 6, 5, P.SK_RICE_L)                                   # round head
    face(c, hx + 1.5, hy - 1.5, eyes=eyes, mouth=mouth, gap=5, eye=P.SAKURA_EYE, nose=P.SK_PINK_D, blush=P.SK_PINK,
         mouth_colour=P.SAKURA_EYE, size=3)
    blossom(c, hx - 6.5, hy + 4.5, 2.3, turn=step * 0.3)                        # the blossom at the back of its neck
    out = c.outline(EDGE).img
    if trail:
        t = Canvas(*size)
        for i in range(3):
            t.line((x - 12 - i * 2, by - 4 - i * 3), (x - 7, by - 4 - i * 3), P.SK_PINK if i % 2 else P.SK_PINK_L)
        petals(t, x - 12, by - 2, 4, 3, 821 + step, step)
        trail_img = t.img
        trail_img.alpha_composite(out)
        out = trail_img
    return out


def crescent(size, cx: float, cy: float, r: float, a0: float, a1: float, thick: float) -> Image.Image:
    """A pink crescent swipe, thickest in the middle, with a white core."""
    c = Canvas(*size)
    for i in range(41):
        t = i / 40
        a = math.radians(a0 + (a1 - a0) * t)
        w = thick * math.sin(math.pi * t) + 0.5
        c.ellipse(cx + math.cos(a) * r, cy - math.sin(a) * r, w, w, P.SK_PINK)
        if w > 1.2:
            c.ellipse(cx + math.cos(a) * (r + thick * 0.3), cy - math.sin(a) * (r + thick * 0.3), w * 0.5, w * 0.5,
                      P.SK_PINK_L)
        if 0.35 < t < 0.65:
            c.px(cx + math.cos(a) * (r + thick * 0.3), cy - math.sin(a) * (r + thick * 0.3), P.WHITE)
    c.outline(P.SK_PINK_D)
    return c.img


def sakura_bunny() -> Sprite:
    size, cx, gy = (44, 36), 18, 33
    sprite = Sprite("sakura_bunny", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [bunny_frame("sit"), bunny_frame("sit", 1, eyes="shut")], fps=3)
    sprite.add("walk", [bunny_frame("hop", k) for k in range(4)], fps=8)
    sprite.add("run", [bunny_frame("run", k, trail=k % 2 == 0) for k in range(4)], fps=12)
    swipe = bunny_frame("lunge", 1, eyes="angry", mouth="open", lean=1, trail=True)
    swipe.alpha_composite(crescent(size, cx + 13, gy - 12, 6, -70, 75, 2.4))
    sprite.add("attack", [bunny_frame("sit", eyes="angry", mouth="flat", lean=-1), bunny_frame("lunge", 0, eyes="angry", trail=True),
                          swipe, bunny_frame("hop", 3)], fps=10, loop=False)
    hurt = bunny_frame("sit", eyes="shut", mouth="open", lean=-1)
    sprite.add("hurt", hurt_frames(hurt, [(cx + 12, gy - 26), (cx - 8, gy - 22), (cx + 13, gy - 8)]), fps=10, loop=False)
    lie = bunny_frame("lie")
    frames = [tint(bunny_frame("sit", eyes="x", mouth="open"), P.WHITE, 0.6), lie]
    for i, keep in enumerate((200, 100)):
        f = see_through(lie, keep)
        p_ = Canvas(*size)
        petals(p_, cx + 2, gy - 8 - i * 4, 10, 6, 831, i)
        f.alpha_composite(p_.img)
        frames.append(f)
    sprite.add("death", frames, fps=8, loop=False)
    return sprite


# --- lantern spirit [16x18] + blossom_shot ---------------------------------------------------------

def lantern_frame(bob: float = 0, eyes: str = "open", mouth: str = "w", glow: int = 0, k: int = 0, squash: float = 0,
                  sway: float = 0) -> Image.Image:
    """A paper lantern with a lacquered cap and base, a warm glowing body with a cute face, and a red bow
    with tassels hanging below. glow brightens it (attack wind-up)."""
    size, cx, gy = (34, 38), 17, 34
    c = Canvas(*size)
    y = gy + bob
    x = cx + sway
    body_top, body_bot = y - 22 + squash, y - 6
    with shaded(c, LACQUER, EDGE) as p:                                        # bow and tassels
        p.ellipse(x - 2.5, y - 3.5, 2.2, 1.6, P.SK_LACQUER)
        p.ellipse(x + 2.5, y - 3.5, 2.2, 1.6, P.SK_LACQUER)
        p.line((x - 1, y - 3), (x - 2.5 - sway * 0.3, y), P.SK_LACQUER, 1)
        p.line((x + 1, y - 3), (x + 2.5 - sway * 0.3, y), P.SK_LACQUER, 1)
    with shaded(c, ramp((P.WHITE, P.SK_GLOW, P.SK_PINK_L), (P.SK_GLOW, P.SK_PINK_L, P.SK_PINK)), up=1, down=1) as p:
        p.ellipse(x, (body_top + body_bot) / 2, 7.5, (body_bot - body_top) / 2, P.SK_PINK_L if not glow else P.SK_GLOW)
    for dy in (0.3, 0.6):                                                      # paper ribs
        ry_ = body_top + (body_bot - body_top) * dy
        c.line((x - 6, ry_), (x + 6, ry_), P.SK_PINK)
    c.ellipse(x - 1, (body_top + body_bot) / 2 + 1, 4 + glow, 3.5 + glow * 0.5, P.SK_GLOW if not glow else P.WHITE)
    with shaded(c, LACQUER, EDGE, up=2) as p:                                  # lacquered cap and base rim
        p.poly([(x - 6, body_top + 1), (x - 4, body_top - 2.5), (x + 4, body_top - 2.5), (x + 6, body_top + 1)], P.SK_LACQUER)
        p.rect(x - 1, body_top - 5, x + 1, body_top - 2.5, P.SK_LACQUER)
        p.rect(x - 5, body_bot - 0.5, x + 5, body_bot + 1.5, P.SK_LACQUER)
    face(c, x + 1.5, (body_top + body_bot) / 2 - 1.5, eyes=eyes, mouth=mouth, gap=5, eye=P.SAKURA_EYE,
         nose=None, blush=P.SK_PINK_D, mouth_colour=P.SAKURA_EYE, size=3)
    out = c.outline(EDGE).img
    if glow or k:
        g = Canvas(*size)
        for i in range(2 + glow):
            a = k * 0.7 + i * 2.2
            blossom(g, x + math.cos(a) * 11, y - 14 + math.sin(a) * 9, 1.3, turn=a)
        g.outline(P.SK_PINK_D)
        out.alpha_composite(g.img)
    return out


def lantern_spirit() -> Sprite:
    size, cx, gy = (34, 38), 17, 34
    sprite = Sprite("lantern_spirit", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [lantern_frame(0), lantern_frame(-1, eyes="shut")], fps=3)
    sprite.add("float", [lantern_frame((0, -1, -1, 0)[i], k=i + 1, sway=(0, 0.5, 0, -0.5)[i]) for i in range(4)], fps=6)
    shot = lantern_frame(0, eyes="angry", mouth="open", glow=1, k=2)
    shot.alpha_composite(glow_blossom(size, cx + 10, gy - 14, 2.8, 1, tail=3))
    sprite.add("attack", [lantern_frame(-1, eyes="angry", mouth="flat", glow=2, k=1, squash=1), shot, lantern_frame(0, k=3)],
               fps=8, loop=False)
    hurt = lantern_frame(0, eyes="x", mouth="open", sway=-1)
    sprite.add("hurt", hurt_frames(hurt, [(cx + 10, gy - 24), (cx - 10, gy - 20), (cx + 11, gy - 6)]), fps=10, loop=False)
    sprite.add("death", scatter(lantern_frame(2, eyes="x", mouth="open", squash=4), cx, gy, 841, depth=4), fps=8, loop=False)
    return sprite


def blossom_shot() -> Sprite:
    sprite = Sprite("blossom_shot", (12, 12), faces_left=True)
    frames = []
    for k in range(4):
        c = Canvas(12, 12)
        c.ellipse(5.5, 5.5, 5, 5, (*P.SK_PINK[:3], 110))
        blossom(c, 5.5, 5.5, 3.2, turn=k * 0.35, glow=True)
        c.outline(P.SK_PINK_D)
        frames.append(c.img)
    sprite.add("fly", frames, fps=10)
    return sprite


# --- bird crow [18x14] -----------------------------------------------------------------------------

def crow_wing(c: Canvas, root, flap: float, far: bool, swept: float = 0) -> None:
    """A feathered wing raised up and back from the shoulder, its long feathers tipped pink."""
    rx, ry = root
    span = (15 if not far else 12) * (1 - swept * 0.3)
    tip = (rx - span * 0.7, ry - 3 - flap * 11 + swept * 8)
    with shaded(c, CROW, EDGE, up=1, down=1) as p:
        p.poly([root, (rx - span * 0.3, ry - 4 - flap * 5 + swept * 3), tip, (rx - span * 0.9, ry + 1 - flap * 3 + swept * 3),
                (rx - span * 0.5, ry + 3 - flap * 1.5), (rx, ry + 3)], P.SK_CROW if not far else P.SK_CROW_D)
    for i in range(4):                                                         # feather tips with pink
        t = 0.45 + i * 0.17
        fx = rx + (tip[0] - rx) * t
        fy = ry + 2 + (tip[1] + 4 - ry - 2) * t
        c.line((fx, fy - 2), (fx - 1.5, fy + 1), P.SK_PINK_D if not far else P.SK_PINK_DD)
        c.px(fx - 1.5, fy + 1, P.SK_PINK)


def crow_frame(flap: float, bob: float = 0, eyes: str = "open", dive: float = 0, lines: bool = False, k: int = 0,
               fallen: bool = False) -> Image.Image:
    size, cx, gy = (48, 34), 22, 27
    c = Canvas(*size)
    y = gy + bob + dive * 2
    x = cx + dive * 2
    crow_wing(c, (x - 1, y - 9), flap, far=True, swept=dive)
    with shaded(c, CROW, EDGE) as p:                                           # tail feathers
        p.poly([(x - 6, y - 7), (x - 13, y - 9 + dive * 2), (x - 12, y - 5 + dive * 2), (x - 5, y - 4)], P.SK_CROW)
    with shaded(c, ramp((P.YELLOW, P.ORANGE, P.GINGER_D)), EDGE) as p:         # feet
        if not fallen:
            p.line((x - 1, y - 2), (x - 2, y), P.ORANGE, 1)
            p.line((x + 2, y - 2), (x + 1, y), P.ORANGE, 1)
    with shaded(c, CROW, up=2) as p:
        p.ellipse(x, y - 6, 7, 5, P.SK_CROW)                                   # body
        p.ellipse(x + 6.5, y - 10 + dive * 2, 4.5, 4, P.SK_CROW)               # head
    c.ellipse(x + 1, y - 4, 3.5, 2, P.SK_CROW_L)
    with shaded(c, ramp((P.YELLOW, P.ORANGE, P.GINGER_D)), EDGE) as p:         # beak
        p.poly([(x + 9.5, y - 11 + dive * 2), (x + 14, y - 9.5 + dive * 3), (x + 9.5, y - 8.5 + dive * 2)], P.ORANGE)
    if eyes == "x":
        c.px(x + 7, y - 12 + dive * 2, P.WHITE)
        c.px(x + 8, y - 11 + dive * 2, P.WHITE)
        c.px(x + 8, y - 12 + dive * 2, P.WHITE)
        c.px(x + 7, y - 11 + dive * 2, P.WHITE)
    elif eyes == "shut":
        c.rect(x + 7, y - 11 + dive * 2, x + 8, y - 11 + dive * 2, P.BLACK)
    else:
        c.rect(x + 8, y - 12 + dive * 2, x + 9, y - 11 + dive * 2, P.BLACK)
        c.px(x + 9, y - 12 + dive * 2, P.WHITE)
        if eyes == "angry":
            c.line((x + 6, y - 14 + dive * 2), (x + 9, y - 13 + dive * 2), P.SK_CROW_D)
    blossom(c, x + 3.5, y - 14.5 + dive * 2, 2.4, turn=k * 0.2)                  # the flower behind its eye
    crow_wing(c, (x + 1, y - 8), flap * 0.85, far=False, swept=dive)
    out = c.outline(EDGE).img
    if lines:                                                                  # speed lines and petals behind the dive
        t = Canvas(*size)
        for i in range(4):
            yy = y - 14 + i * 3.5
            t.line((x - 22 + i, yy - 4), (x - 9 + i, yy), P.SK_PINK if i % 2 else P.SK_PINK_L)
        petals(t, x - 14, y - 6, 5, 3, 851 + k, k)
        trail = t.img
        trail.alpha_composite(out)
        out = trail
    return out


def bird_crow() -> Sprite:
    size, cx, gy = (48, 34), 22, 27
    sprite = Sprite("bird_crow", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("fly", [crow_frame(f, b, k=i) for i, (f, b) in enumerate(((1, 0), (0.2, 0), (-0.8, -1), (0.2, -1)))], fps=10)
    sprite.add("attack", [crow_frame(1, -1, eyes="angry"), crow_frame(-0.2, 0, eyes="angry", dive=1, lines=True, k=1),
                          crow_frame(0.3, 0, eyes="angry", dive=0.5, lines=True, k=2)], fps=10, loop=False)
    hurt = crow_frame(0.6, eyes="shut")
    sprite.add("hurt", hurt_frames(hurt, [(cx + 12, gy - 20), (cx - 9, gy - 18), (cx + 10, gy - 2)]), fps=10, loop=False)
    sprite.add("death", scatter(crow_frame(-0.6, 2, eyes="x", fallen=True), cx, gy, 861, depth=6), fps=8, loop=False)
    return sprite


# --- spike plant [18x20] (a lotus bud) -------------------------------------------------------------

def lotus_frame(opening: float = 0, k: int = 0, eyes: str = "open", mouth: str = "w", squash: float = 0,
                spit: bool = False) -> Image.Image:
    """A pink lotus on broad green leaves: a tall pointed bud (closed) whose petals part to show a pale glowing
    heart with a little face (open)."""
    size, cx, gy = (36, 32), 16, 29
    c = Canvas(*size)
    with shaded(c, LEAF, EDGE) as p:                                           # leaves at the foot
        for side in (-1, 1):
            p.ellipse(cx + side * 6, gy - 2.5, 6, 2.4, P.KIT_GREEN)
        p.ellipse(cx, gy - 2, 4, 1.8, P.KIT_GREEN)
    c.line((cx - 9, gy - 2), (cx - 3, gy - 2.5), P.KIT_GREEN_D)
    c.line((cx + 3, gy - 2.5), (cx + 9, gy - 2), P.KIT_GREEN_D)
    base = gy - 4 + squash
    h = 15 - squash
    spread = opening * 6
    if opening > 0.2:                                                          # the open heart
        with shaded(c, ramp((P.WHITE, P.SK_GLOW, P.SK_PINK_L))) as p:
            p.ellipse(cx, base - h * 0.5, 5, 4.5, P.SK_GLOW)
        face(c, cx + 1.5, base - h * 0.5 - 1.5, eyes=eyes, mouth=mouth, gap=4, eye=P.SAKURA_EYE, nose=None,
             blush=P.SK_PINK, mouth_colour=P.SAKURA_EYE)
    with shaded(c, PINK, EDGE, up=2) as p:                                     # petals
        for side in (-1, 1):                                                   # outer petals, swinging out
            p.poly([(cx + side * 2, base), (cx + side * (5 + spread), base - h * 0.45),
                    (cx + side * (2 + spread * 1.2), base - h * (0.95 - opening * 0.2)), (cx + side * 0.5, base - h * 0.4)],
                   P.SK_PINK)
        if opening <= 0.2:                                                     # the closed middle petal
            p.poly([(cx - 4.5, base - 1), (cx - 5, base - h * 0.55), (cx, base - h), (cx + 5, base - h * 0.55),
                    (cx + 4.5, base - 1)], P.SK_PINK_L)
        else:                                                                  # a front petal cupping the heart
            p.poly([(cx - 4, base), (cx - 3, base - h * 0.35), (cx, base - h * 0.45), (cx + 3, base - h * 0.35),
                    (cx + 4, base)], P.SK_PINK_L)
    if opening <= 0.2:
        c.line((cx, base - h + 2), (cx, base - 2), P.SK_PINK)
        c.px(cx - 2, base - h * 0.6, P.WHITE)
    out = c.outline(EDGE).img
    if spit:
        out.alpha_composite(glow_blossom(size, cx + 12, base - h * 0.5, 2.6, k, tail=5))
    return out


def spike_plant() -> Sprite:
    size, cx, gy = (36, 32), 16, 29
    sprite = Sprite("spike_plant", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [lotus_frame(0), lotus_frame(0, squash=0.6)], fps=3)
    sprite.add("open", [lotus_frame(0.5), lotus_frame(1.0)], fps=6)
    sprite.add("attack", [lotus_frame(1.0, eyes="angry", mouth="flat", squash=1), lotus_frame(1.0, 1, eyes="angry", mouth="open", spit=True),
                          lotus_frame(0.8, 2)], fps=8, loop=False)
    hurt = lotus_frame(0.6, eyes="shut", mouth="open", squash=1)
    sprite.add("hurt", hurt_frames(hurt, [(cx + 10, gy - 18), (cx - 10, gy - 14), (cx + 11, gy - 4)]), fps=10, loop=False)
    sprite.add("death", scatter(lotus_frame(1.0, eyes="x", mouth="open", squash=4), cx, gy, 871, depth=5), fps=8, loop=False)
    return sprite


# --- rolling onigiri [18x16] -----------------------------------------------------------------------

def onigiri(c: Canvas, x: float, y: float, eyes: str = "open", mouth: str = "w", flower: bool = True, squash: float = 0) -> None:
    """A rounded triangular rice ball with a nori wrap at the bottom front and a blossom on top; (x, y) is
    its centre."""
    with shaded(c, RICE, up=2) as p:
        p.poly([(x - 8.5 - squash, y + 6), (x - 7, y - 2 + squash), (x - 2, y - 8 + squash * 1.5), (x + 2, y - 8 + squash * 1.5),
                (x + 7, y - 2 + squash), (x + 8.5 + squash, y + 6)], P.SK_RICE_L)
        p.ellipse(x, y + 2, 8.5 + squash, 5.5, P.SK_RICE_L)
    for gx, gy_ in ((-5, -1), (4, -3), (-2, 3), (6, 3), (-6, 4)):              # rice grains
        c.px(x + gx, y + gy_, P.SK_RICE_D)
    with shaded(c, NORI) as p:                                                 # nori wrap
        p.poly([(x + 1, y + 1.5), (x + 7.5, y + 1.5), (x + 8, y + 7.5), (x + 1, y + 7.5)], P.SK_NORI)
    c.line((x + 2, y + 2.5), (x + 6, y + 2.5), P.SK_NORI_L)
    face(c, x + 3.5, y - 2, eyes=eyes, mouth=mouth, gap=6, eye=P.SAKURA_EYE, nose=None, blush=P.SK_PINK,
         mouth_colour=P.SAKURA_EYE, size=3)
    if flower:
        blossom(c, x - 0.5, y - 8 + squash * 1.5, 2.6)


def onigiri_frame(eyes: str = "open", mouth: str = "w", squash: float = 0, dx: float = 0) -> Image.Image:
    size, cx, gy = (44, 28), 22, 25
    c = Canvas(*size)
    onigiri(c, cx + dx, gy - 9 + squash * 0.5, eyes, mouth, squash=squash)
    return c.outline(EDGE).img


def rolled(angle: float, eyes: str = "open", mouth: str = "w") -> Image.Image:
    """The onigiri turned by `angle` degrees about its middle, re-seated on the ground line."""
    size, cx, gy = (44, 28), 22, 25
    big = Canvas(32, 32)
    onigiri(big, 15.5, 16.5, eyes, mouth)
    big.outline(EDGE)
    turned = big.img.rotate(-angle, resample=Image.NEAREST, center=(15.5, 15.5))
    box = turned.getbbox()
    piece = turned.crop(box)
    out = Image.new("RGBA", size, P.CLEAR)
    out.alpha_composite(piece, (round(cx - piece.width / 2), gy + 2 - piece.height))
    return out


def dust(size, x: float, gy: float, k: int, long: bool = False) -> Image.Image:
    """Petal dust kicked up behind a rolling onigiri, and speed streaks for the charge."""
    c = Canvas(*size)
    for i, (dx, r) in enumerate(((-3, 2.4), (-7, 1.8), (-10, 1.3))):
        c.ellipse(x + dx - k % 2, gy - r - 0.5, r, r, P.SK_PINK_L if i % 2 else P.SK_RICE_L)
    petals(c, x - 6, gy - 5, 4, 3, 881 + k, k)
    if long:
        for i in range(3):
            c.line((x - 12 + i, gy - 6 - i * 3.5), (x - 4, gy - 6 - i * 3.5), P.SK_PINK if i % 2 else P.SK_PINK_L)
    c.outline(P.SK_PINK_D)
    return c.img


def rolling_onigiri() -> Sprite:
    size, cx, gy = (44, 28), 22, 25
    sprite = Sprite("rolling_onigiri", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [onigiri_frame(), onigiri_frame(eyes="shut", squash=0.6)], fps=3)
    roll = []
    for k in range(4):
        f = rolled(k * 90, eyes="shut" if k % 2 else "open")
        d = dust(size, cx - 8, gy, k)
        d.alpha_composite(f)
        roll.append(d)
    sprite.add("roll", roll, fps=12)
    attack = [onigiri_frame(eyes="angry", mouth="flat", squash=1, dx=-1)]
    for k in range(2):
        f = rolled(k * 120 + 45, eyes="angry", mouth="open")
        d = dust(size, cx - 8, gy, k, long=True)
        d.alpha_composite(f)
        attack.append(d)
    attack.append(onigiri_frame(dx=1))
    sprite.add("attack", attack, fps=10, loop=False)
    hurt = onigiri_frame(eyes="shut", mouth="open", squash=1)
    sprite.add("hurt", hurt_frames(hurt, [(cx + 11, gy - 17), (cx - 10, gy - 13), (cx + 12, gy - 4)]), fps=10, loop=False)
    sprite.add("death", scatter(onigiri_frame(eyes="x", mouth="open", squash=2), cx, gy, 891, depth=3), fps=8, loop=False)
    return sprite


# --- sakura spirit [12x12] (summoned by the boss) --------------------------------------------------

def spirit_frame(k: int = 0, bob: float = 0, eyes: str = "open") -> Image.Image:
    """A tiny fox-spirit flame, as the Blossom Kitsune summons them (docs/concept/Sakura Fox Boss Sprite Sheet.png):
    pink flame licks streaming back from a little fox head with pointed ears and a dark eye."""
    from characters.boss_kitsune import fox_flame
    size, cx, gy = (24, 24), 12, 18
    c = Canvas(*size)
    x, y = cx + 2, gy - 4 + bob
    fox_flame(c, x, y, 0.8, k, 905, halo=False)
    if eyes != "open":                                                         # cover the eye
        c.ellipse(x + 1.5, y - 0.5, 1, 1, P.SK_PINK)
        if eyes == "shut":
            c.line((x + 0.5, y - 0.5), (x + 2.5, y - 0.5), P.SAKURA_EYE)
        else:
            c.line((x + 0.5, y - 1.5), (x + 2.5, y + 0.5), P.SAKURA_EYE)
            c.line((x + 0.5, y + 0.5), (x + 2.5, y - 1.5), P.SAKURA_EYE)
    petal(c, cx - 7, gy - 1 + math.sin(k) * 1.5, k)
    c.outline(EDGE)
    out = Canvas(*size)                                                       # a soft pink glow under it
    out.ellipse(x - 2, y, 7, 6, P.SK_PINK)
    img = see_through(out.img, 70)
    img.alpha_composite(c.img)
    return img


def sakura_spirit() -> Sprite:
    size, cx, gy = (24, 24), 12, 18
    sprite = Sprite("sakura_spirit", size, faces_left=True, cx=cx, ground=gy + 2)   # lowest petal
    sprite.add("float", [spirit_frame(k, (0, -1, -1, 0)[k], "shut" if k == 3 else "open") for k in range(4)], fps=6)
    still = spirit_frame(0, eyes="x")
    frames = [tint(still, P.WHITE, 0.6)]
    for i, t in enumerate((0.5, 0.95)):
        f = vanish(still, t, depth=-3, flash=False)
        p_ = Canvas(*size)
        petals(p_, cx, gy - 8, 6 + i * 3, 5, 901, i)
        f.alpha_composite(see_through(p_.img, int(255 * (1 - t * 0.5))))
        frames.append(f)
    sprite.add("death", frames, fps=8, loop=False)
    return sprite


def build() -> list[Sprite]:
    from characters.bird_crow_painted import NAMES as crow
    from characters.boss_kitsune_painted import NAMES as kitsune   # cut from the user's painted sheets instead
    from characters.rolling_onigiri_painted import NAMES as onigiri
    from characters.sakura_bunny_painted import NAMES as bunny
    painted = kitsune | bunny | onigiri | crow
    sprites = [sakura_slime(), sakura_bunny(), lantern_spirit(), blossom_shot(), bird_crow(), spike_plant(),
               rolling_onigiri(), sakura_spirit()]
    return [s for s in sprites if s.name not in painted]
