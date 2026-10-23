"""Sakura world, level 2 (dusk) critters (from `docs/concept/Sakura World Level 2 Enemy Sprites.png`): the lantern
slime, ninja tanuki, sakura bat, shadow spirit and spike kappa, and the flames, spirit fireballs and spike balls
they throw.

Drawn facing right with light from the top-left and mirrored on export, with the level 1 helpers from
`sakura_critters.py` (blossoms, petals, glowing blossom shots, petal hurts and deaths, the pink crescent). The
level is a sunset, so every critter has a strong dark outline to read on peach, pink and violet."""
from __future__ import annotations

import math

from PIL import Image

import palette as P
from characters.sakura_critters import (EDGE, LACQUER, LEAF, PINK, RICE, blossom, crescent, hurt_frames, petal,
                                        petals, scatter)
from critters import ear, face, ramp, shaded, sparkle
from draw import Canvas, noise, see_through, tint, vanish
from sprite import Sprite

GLOW = ramp((P.WHITE, P.SK_GLOW, P.LANTERN), (P.SK_GLOW, P.LANTERN, P.ORANGE), (P.LANTERN, P.ORANGE, P.RUST))
FUR = ramp((P.GREY_L, P.GREY, P.GREY_D), (P.GREY, P.GREY_D, P.SLATE))
STRAW = ramp((P.PLANK_L, P.PLANK, P.PLANK_D))
CLOTH = ramp((P.NAVY, P.SLATE, P.BLACK))
NAVY_RAMP = ramp((P.BLUE_D, P.NAVY, P.NIGHT), (P.PURPLE, P.PURPLE_D, P.NIGHT))
MOSS = ramp((P.KIT_GREEN_L, P.KIT_GREEN, P.KIT_GREEN_D), (P.STONE_L, P.STONE, P.STONE_D))
WING = ramp((P.SK_PINK, P.SK_PINK_D, P.SK_PINK_DD), (P.SK_PINK_L, P.SK_PINK, P.SK_PINK_D))


def fireball(size, x: float, y: float, r: float, k: int, tail: float = 6, hot=P.SK_GLOW) -> Image.Image:
    """A pink fireball flying right, flames licking back from a hot pale core."""
    c = Canvas(*size)
    for i in range(int(tail)):
        t = i / tail
        rr = r * (1 - t) * 0.9
        if rr < 0.4:
            continue
        c.ellipse(x - 1 - i, y + math.sin(i * 1.2 + k) * 0.8 * t, rr, rr * 0.8, P.SK_PINK if t < 0.5 else P.SK_PINK_D)
    c.ellipse(x, y, r, r, P.SK_PINK)
    c.ellipse(x + 0.3, y - 0.3, r * 0.65, r * 0.65, P.SK_PINK_L)
    c.ellipse(x + 0.5, y - 0.5, max(0.6, r * 0.3), max(0.6, r * 0.3), hot)
    c.outline(P.SK_PINK_DD)
    return c.img


# --- lantern slime [20x16] + lantern_flame ---------------------------------------------------------

def lantern_slime_body(c: Canvas, cx: float, gy: float, sy: float = 1.0, lift: float = 0, eyes: str = "none",
                       mouth: str = "w", tilt: float = 0) -> None:
    """A round glowing paper lantern sitting like a slime, a red lacquered pagoda cap with a knob, a red
    blossom painted on its front and a pink blossom tucked on the cap. eyes 'none' shows the painted
    blossom; any other mood shows a face instead (hurt, death)."""
    base = gy - lift
    h = 15 * sy
    with shaded(c, GLOW, up=2, down=1) as p:
        p.ellipse(cx, base - h * 0.55, 9.5, h * 0.6, P.LANTERN)
        p.rect(cx - 7, base - 2, cx + 7, base, P.LANTERN)
    for dx in (-5, 0, 5):                                                     # paper ribs
        c.line((cx + dx, base - h + 2), (cx + dx * 1.1, base - 1), P.ORANGE)
    c.ellipse(cx - 1, base - h * 0.55, 4.5, h * 0.35, P.SK_GLOW)
    top = base - h - 0.5
    with shaded(c, LACQUER, EDGE, up=2) as p:                                 # the pagoda cap
        p.poly([(cx - 8 + tilt, top + 2), (cx - 4.5 + tilt, top - 1.5), (cx + 4.5 + tilt, top - 1.5), (cx + 8 + tilt, top + 2)],
               P.SK_LACQUER)
        p.rect(cx - 2.5 + tilt, top - 3.5, cx + 2.5 + tilt, top - 1.5, P.SK_LACQUER)
        p.ellipse(cx + tilt, top - 4.5, 1.3, 1.3, P.GOLD)
    with shaded(c, LACQUER, EDGE) as p:                                       # base rim
        p.rect(cx - 6, base - 0.5, cx + 6, base, P.SK_LACQUER_D)
    if eyes == "none":
        for i in range(5):                                                    # a red blossom painted on the paper
            a = 0.1 + i / 5 * math.tau - math.pi / 2
            c.ellipse(cx + 1 + math.cos(a) * 2, base - h * 0.5 + math.sin(a) * 2, 1.1, 1.1, P.RED)
        c.px(cx + 1, base - h * 0.5, P.RED_D)
    else:
        face(c, cx + 2, base - h * 0.55 - 1, eyes=eyes, mouth=mouth, gap=6, eye=P.SAKURA_EYE, nose=None, blush=P.RED,
             mouth_colour=P.SAKURA_EYE, size=3)
    blossom(c, cx + 5.5 + tilt, top, 1.8, turn=0.4)


def lantern_slime() -> Sprite:
    size, cx, gy = (34, 32), 17, 29
    sprite = Sprite("lantern_slime", size, faces_left=True, cx=cx, ground=gy + 1)

    def f(sy=1.0, lift=0, eyes="none", mouth="w", tilt=0, swoosh=False):
        c = Canvas(*size)
        lantern_slime_body(c, cx, gy, sy, lift, eyes, mouth, tilt)
        out = c.outline(EDGE).img
        if swoosh:
            s = crescent(size, cx - 4, gy - 10, 9, 110, 250, 1.8)
            s.alpha_composite(out)
            out = s
        return out

    sprite.add("idle", [f(), f(0.94)], fps=3)
    sprite.add("walk", [f(0.9), f(1.05, 2, tilt=0.5), f(1.0, 3), f(0.96, 1, tilt=-0.5)], fps=8)
    sprite.add("attack", [f(0.82, tilt=-1), f(1.08, 4, tilt=1, swoosh=True), f(0.86, 0, eyes="angry", mouth="open")],
               fps=8, loop=False)
    hurt = f(0.9, eyes="shut", mouth="open", tilt=-1)
    sprite.add("hurt", hurt_frames(hurt, [(cx - 10, gy - 16), (cx + 10, gy - 14), (cx + 1, gy - 24)]), fps=10, loop=False)
    still = f(0.6, eyes="shut", mouth="w")
    sprite.add("death", scatter(still, cx, gy, 911, depth=3), fps=8, loop=False)
    return sprite


def lantern_flame() -> Sprite:
    sprite = Sprite("lantern_flame", (12, 12), faces_left=True)
    frames = []
    for k in range(4):
        c = Canvas(12, 12)
        sway = (0, 1, 0, -1)[k]
        c.poly([(2.5, 10), (2.5, 6), (5.5 + sway, 1), (8.5, 6), (8.5, 10)], P.ORANGE)
        c.poly([(4, 10), (4, 7), (5.5 + sway * 0.6, 3.5), (7, 7), (7, 10)], P.LANTERN)
        c.rect(5, 8, 6, 10, P.SK_GLOW)
        c.ellipse(5.5, 8.5, 3, 2, P.ORANGE)
        c.ellipse(5.5, 8.5, 1.5, 1, P.SK_GLOW)
        c.outline(P.RUST_D)
        frames.append(c.img)
    sprite.add("fly", frames, fps=12)
    return sprite


# --- ninja tanuki [18x22] --------------------------------------------------------------------------

def tanuki_frame(step: int = 0, walk: bool = False, sword: str = "rest", eyes: str = "open", mouth: str = "w",
                 lean: float = 0, crouch: float = 0) -> Image.Image:
    """A round grey tanuki in a navy gi with a red scarf, a dark eye mask and a wide straw hat with a pink
    blossom; a ringed tail behind. sword: rest (held low behind), raised, slash (swept out front)."""
    size, x, gy = (48, 40), 18, 37
    c = Canvas(*size)
    x += lean
    by = gy + crouch
    lifts = ((step % 2) * 2, ((step + 1) % 2) * 2) if walk else (0, 0)
    with shaded(c, FUR, EDGE) as p:                                           # ringed tail
        p.ellipse(x - 9, by - 7, 4, 3.5, P.GREY)
    for dx in (-10.5, -7.5):
        c.line((x + dx, by - 10), (x + dx, by - 4), P.SLATE)
    if sword == "rest":
        with shaded(c, ramp((P.WHITE, P.GREY_L, P.GREY))) as p:
            p.line((x - 4, by - 10), (x - 13, by - 3), P.GREY_L, 2)
        c.line((x - 3, by - 11), (x - 5, by - 9), P.BROWN_D)
    with shaded(c, CLOTH, EDGE) as p:                                         # legs
        p.rect(x - 4, by - 6, x - 1, gy - lifts[0], P.SLATE)
        p.rect(x + 1, by - 6, x + 4, gy - lifts[1], P.SLATE)
        p.rect(x - 5, gy - 1.5 - lifts[0], x - 1, gy - lifts[0], P.BLACK)
        p.rect(x + 1, gy - 1.5 - lifts[1], x + 5, gy - lifts[1], P.BLACK)
    with shaded(c, CLOTH, up=2) as p:
        p.ellipse(x, by - 10, 6.5, 5.5, P.SLATE)                              # round body in a gi
    c.line((x - 1, by - 14), (x + 3, by - 7), P.NAVY)
    hx, hy = x + 3, by - 18
    with shaded(c, FUR, EDGE, up=2) as p:
        ear(p, hx - 4, hy - 3.5, 3.5, P.GREY, inner=P.SLATE, lean=-0.6, half=2)
        p.ellipse(hx, hy, 6, 5, P.GREY)
        p.ellipse(hx + 4, hy + 1.5, 2.6, 2, P.GREY_L)                         # snout
    c.ellipse(hx + 2, hy - 0.5, 4, 1.8, P.SLATE)                              # the dark eye mask
    if eyes == "x":
        c.px(hx + 1, hy - 1, P.WHITE)
        c.px(hx + 2, hy, P.WHITE)
        c.px(hx + 2, hy - 1, P.WHITE)
        c.px(hx + 1, hy, P.WHITE)
    elif eyes == "shut":
        c.rect(hx + 1, hy, hx + 3, hy, P.WHITE)
    else:
        c.rect(hx + 1, hy - 1, hx + 2, hy, P.WHITE)
        c.px(hx + 2, hy, P.BLACK)
        if eyes == "angry":
            c.line((hx, hy - 2), (hx + 3, hy - 1), P.BLACK)
    c.px(hx + 6.5, hy + 1, P.BLACK)                                           # nose
    if mouth == "open":
        c.px(hx + 4, hy + 3, P.SK_PINK_DD)
    with shaded(c, LACQUER, EDGE) as p:                                       # red scarf, its tail flying
        p.rect(hx - 4, hy + 4, hx + 3, hy + 5.5, P.SK_LACQUER)
        p.poly([(hx - 3, hy + 5), (hx - 9 - (step % 2), hy + 6), (hx - 8, hy + 8), (hx - 2, hy + 6.5)], P.SK_LACQUER)
    with shaded(c, STRAW, EDGE, up=2) as p:                                   # wide straw hat
        p.poly([(hx - 10, hy - 4), (hx - 1, hy - 10.5), (hx + 2, hy - 10.5), (hx + 10, hy - 3.5), (hx + 8, hy - 2.5),
                (hx - 8, hy - 3)], P.PLANK)
        p.ellipse(hx + 0.5, hy - 11, 1.6, 1.4, P.PLANK_D)
    for i in range(-8, 9, 3):                                                 # weave
        c.px(hx + i, hy - 4 - (8 - abs(i)) * 0.7, P.PLANK_D)
    blossom(c, hx + 3, hy - 9.5, 2, turn=step * 0.2)
    if sword in ("raised", "slash"):
        grip = (x + 5, by - 12) if sword == "slash" else (x + 2, by - 15)
        tip = (x + 17, by - 13) if sword == "slash" else (x - 6, by - 26)
        with shaded(c, ramp((P.WHITE, P.GREY_L, P.GREY))) as p:
            p.line(grip, tip, P.GREY_L, 2)
        c.line(grip, (grip[0] + (tip[0] - grip[0]) * 0.15, grip[1] + (tip[1] - grip[1]) * 0.15), P.BROWN_D, 2)
    with shaded(c, FUR, EDGE) as p:                                           # near paw
        paw = {"rest": (x + 5, by - 8), "raised": (x + 2, by - 15), "slash": (x + 5, by - 12)}[sword]
        p.ellipse(paw[0], paw[1], 1.8, 1.6, P.GREY)
    return c.outline(EDGE).img


def ninja_tanuki() -> Sprite:
    size, cx, gy = (48, 40), 18, 37
    sprite = Sprite("ninja_tanuki", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [tanuki_frame(), tanuki_frame(crouch=0.6, eyes="shut")], fps=3)
    sprite.add("walk", [tanuki_frame(k, walk=True) for k in range(4)], fps=8)
    slash = tanuki_frame(sword="slash", eyes="angry", mouth="open", lean=1)
    slash.alpha_composite(crescent(size, cx + 15, gy - 14, 7, -75, 80, 2.6))
    sprite.add("attack", [tanuki_frame(sword="raised", eyes="angry", lean=-1, crouch=1),
                          tanuki_frame(sword="raised", eyes="angry", lean=-1.5, crouch=1.5), slash,
                          tanuki_frame(sword="slash", lean=1)], fps=10, loop=False)
    hurt = tanuki_frame(eyes="shut", mouth="open", lean=-1.5)
    sprite.add("hurt", hurt_frames(hurt, [(cx + 13, gy - 26), (cx - 9, gy - 22), (cx + 14, gy - 8)]), fps=10, loop=False)
    sprite.add("death", scatter(tanuki_frame(eyes="x", mouth="open", crouch=3), cx, gy, 921, depth=5), fps=8, loop=False)
    return sprite


# --- sakura bat [18x14] ----------------------------------------------------------------------------

def pink_wing(c: Canvas, root, side: int, flap: float, far: bool, swept: float = 0) -> None:
    rx, ry = root
    span = (16 if not far else 14) * (1 - swept * 0.35)
    tip = (rx + side * span, ry - 4 - flap * 7 + swept * 5)
    elbow = (rx + side * span * 0.45, ry - 5 - flap * 5 + swept * 2)
    low = ry + 3 - flap * 2
    pts = [root, elbow, tip]
    fingers = []
    for kk, t in enumerate((0.82, 0.64, 0.44, 0.24)):
        x = rx + side * span * t
        y = tip[1] + (low - tip[1]) * (1 - t) + 2
        if kk % 2 == 0:
            pts.append((x, y + 3.5))
        else:
            pts.append((x, y))
            fingers.append((x, y))
    pts.append((rx, ry + 4))
    with shaded(c, WING, EDGE, up=1, down=1) as p:
        p.poly(pts, P.SK_PINK_D if far else P.SK_PINK)
    with shaded(c, ramp((P.SK_CROW_L, P.SK_CROW, P.SK_CROW_D))) as p:
        p.line(root, elbow, P.SK_CROW, 2)
        p.line(elbow, tip, P.SK_CROW, 1)
    for f in fingers:
        c.line(elbow, f, P.SK_PINK_DD)


def bat_frame(flap: float, eyes: str = "open", mouth: str = "w", bob: float = 0, dive: float = 0, k: int = 0,
              trail: bool = False) -> Image.Image:
    size, cx, gy = (46, 32), 23, 25
    c = Canvas(*size)
    y = gy + bob
    x = cx + dive * 3
    pink_wing(c, (x - 3, y - 9), -1, flap, False, dive)
    pink_wing(c, (x + 3, y - 9), 1, flap * 0.85, True, dive)
    with shaded(c, RICE, EDGE, up=2) as p:
        p.ellipse(x - 1, y - 5, 5, 4.2, P.SK_RICE_L)
        p.rect(x - 3, y - 1, x - 2, y, P.SK_RICE)
        p.rect(x + 1, y - 1, x + 2, y, P.SK_RICE)
    c.ellipse(x - 2, y - 3.5, 2, 1.4, P.SK_CROW_L)                            # a dark patch on its back
    with shaded(c, RICE, EDGE, up=2) as p:
        ear(p, x - 3.5, y - 14, 5, P.SK_RICE_L, inner=P.SK_PINK, lean=-1, half=2.6)
        ear(p, x + 5, y - 14, 5, P.SK_RICE_L, inner=P.SK_PINK, lean=1, half=2.6)
        p.ellipse(x + 1, y - 10, 6.5, 5.5, P.SK_RICE_L)
    face(c, x + 2.5, y - 11.5, eyes=eyes, mouth=mouth, gap=5, eye=P.SAKURA_EYE, nose=P.SK_PINK_D, blush=P.SK_PINK,
         mouth_colour=P.SAKURA_EYE, size=3)
    blossom(c, x + 0.5, y - 16, 1.8, turn=k * 0.3)
    out = c.outline(EDGE).img
    if trail:
        t = Canvas(*size)
        for i in range(3):
            t.line((x - 18 + i * 2, y - 14 + i * 3), (x - 8, y - 9 + i * 3), P.SK_PINK if i % 2 else P.SK_PINK_L)
        petals(t, x - 14, y - 8, 4, 3, 931 + k, k)
        tr = t.img
        tr.alpha_composite(out)
        out = tr
    return out


def sakura_bat() -> Sprite:
    size, cx, gy = (46, 32), 23, 25
    sprite = Sprite("sakura_bat", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("fly", [bat_frame(f, bob=b, k=i) for i, (f, b) in enumerate(((1, 0), (0.2, 0), (-0.9, -1), (0.2, -1)))],
               fps=12)
    sprite.add("attack", [bat_frame(1, "angry", bob=-1), bat_frame(-0.3, "angry", "open", dive=1, k=1, trail=True),
                          bat_frame(0.4, "angry", dive=0.4, k=2, trail=True)], fps=10, loop=False)
    hurt = bat_frame(0.6, "shut", "open")
    sprite.add("hurt", hurt_frames(hurt, [(cx - 6, gy - 22), (cx + 10, gy - 20), (cx + 4, gy - 2)]), fps=10, loop=False)
    dead = bat_frame(-0.5, "x", "open")
    sprite.add("death", [tint(dead, P.WHITE, 0.6), vanish(dead, 0.45, depth=8, flash=False),
                         vanish(dead, 0.9, depth=8, flash=False)], fps=10, loop=False)
    return sprite


# --- shadow spirit [16x20] + spirit_flame ----------------------------------------------------------

def spirit_frame(k: int = 0, bob: float = 0, mask: str = "calm", cast: int = 0, lean: float = 0) -> Image.Image:
    """A navy cloak of shadow that trails into wisps, a pale mask with slit eyes and a red stripe, and a pink
    blossom in its hood. cast 1-2 raises a little claw-hand with a pink flame gathering in it."""
    size, cx, gy = (38, 38), 17, 33
    c = Canvas(*size)
    y = gy + bob
    x = cx + lean
    with shaded(c, NAVY_RAMP, up=2) as p:
        for i, (dx, dy, r) in enumerate(((-6, -1, 2.5), (-9, -3, 2.2), (-10, -6, 1.8))):   # wisps trailing
            p.ellipse(x + dx - (k + i) % 2 * 0.5, y + dy + (k % 2), r, r, P.NAVY)
        p.ellipse(x - 1, y - 7, 6.5, 6.5, P.NAVY)                             # body
        p.ellipse(x + 1, y - 15, 7, 6.5, P.NAVY)                              # hood
        p.poly([(x - 5, y - 18), (x - 9, y - 23 + k % 2), (x - 3, y - 20)], P.NAVY)   # the hood's tip
    c.ellipse(x - 3, y - 4, 2, 1.5, P.PURPLE_D)
    c.px(x - 6, y - 9, P.PURPLE)
    with shaded(c, RICE, EDGE, up=2) as p:                                    # the mask
        p.ellipse(x + 3.5, y - 14, 4.5, 5.5, P.SK_RICE_L)
    c.line((x + 3, y - 19), (x + 4, y - 14), P.SK_LACQUER)                    # red stripe
    if mask == "angry":
        c.line((x + 1, y - 15), (x + 3, y - 14), P.BLACK)
        c.line((x + 5, y - 14), (x + 7, y - 15), P.BLACK)
    elif mask == "x":
        for ex in (x + 2, x + 6):
            c.px(ex - 0.5, y - 15, P.BLACK)
            c.px(ex + 0.5, y - 14, P.BLACK)
            c.px(ex + 0.5, y - 15, P.BLACK)
            c.px(ex - 0.5, y - 14, P.BLACK)
    else:
        c.line((x + 1, y - 14), (x + 3, y - 14), P.BLACK)
        c.line((x + 5, y - 14), (x + 7, y - 14), P.BLACK)
    if mask == "hurt":
        c.ellipse(x + 4, y - 11, 1, 1, P.BLACK)
    else:
        c.line((x + 3, y - 11), (x + 5, y - 11.5), P.BLACK)
    blossom(c, x - 1, y - 19, 2.6, turn=k * 0.25)
    if cast:
        with shaded(c, NAVY_RAMP, EDGE) as p:
            p.line((x + 3, y - 7), (x + 8, y - 8 - cast * 2), P.NAVY, 2)
    out = c.outline(EDGE).img
    if cast:
        out.alpha_composite(fireball(size, x + 11, y - 10 - cast * 2, 1.4 + cast * 0.8, k, tail=0))
        g = Canvas(*size)
        sparkle(g, x + 14, y - 15 - cast, P.SK_PINK_L)
        out.alpha_composite(g.img)
    return out


def shadow_spirit() -> Sprite:
    size, cx, gy = (38, 38), 17, 33
    sprite = Sprite("shadow_spirit", size, faces_left=True, cx=cx, ground=gy + 3)   # lowest wisp
    sprite.add("idle", [spirit_frame(0), spirit_frame(1, -1)], fps=4)
    sprite.add("cast", [spirit_frame(0, mask="angry", cast=1), spirit_frame(1, -1, mask="angry", cast=2),
                        spirit_frame(2, -1, mask="angry", cast=2)], fps=8, loop=False)
    throw = spirit_frame(3, mask="angry", lean=1)
    throw.alpha_composite(fireball(size, cx + 14, gy - 12, 3, 1, tail=8))
    sprite.add("attack", [spirit_frame(2, mask="angry", cast=2, lean=-1), throw, spirit_frame(0)], fps=8, loop=False)
    hurt = spirit_frame(1, mask="hurt", lean=-1)
    sprite.add("hurt", hurt_frames(hurt, [(cx + 10, gy - 26), (cx - 10, gy - 20), (cx + 11, gy - 4)]), fps=10, loop=False)
    sprite.add("death", scatter(spirit_frame(2, mask="x"), cx, gy, 941, depth=-4), fps=8, loop=False)
    return sprite


def spirit_flame() -> Sprite:
    sprite = Sprite("spirit_flame", (14, 12), faces_left=True)
    sprite.add("fly", [fireball((14, 12), 9.5, 5.5, 3.6, k, tail=8) for k in range(4)], fps=12)
    return sprite


# --- spike kappa [22x18] + spike_ball --------------------------------------------------------------

def shell(c: Canvas, cx: float, gy: float, opening: float = 0, k: int = 0, eyes: str = "none") -> None:
    """A mossy stone shell dome ringed with blossoms. opening 0 = shut; 0.5 = a dark mouth glowing with a pink
    flame; 1 = the dome gone and a pink lotus spread on its mossy rim."""
    with shaded(c, MOSS, EDGE) as p:                                          # mossy rim at the base
        p.ellipse(cx, gy - 2.5, 11, 3, P.KIT_GREEN)
    for i in range(-9, 10, 3):
        c.px(cx + i, gy - 1, P.KIT_GREEN_D)
    if opening < 1:
        with shaded(c, MOSS, up=2) as p:                                      # stone dome
            p.ellipse(cx, gy - 9, 10.5, 9, P.STONE)
            p.rect(0, gy - 3, p.size[0], p.size[1], P.CLEAR)
        for a, b in (((cx - 6, gy - 13), (cx - 2, gy - 9)), ((cx + 3, gy - 15), (cx + 6, gy - 10)), ((cx - 1, gy - 6), (cx + 3, gy - 5))):
            c.line(a, b, P.STONE_D)
        rnd = noise(951)
        for i in range(5):                                                    # moss patches
            c.ellipse(cx - 8 + rnd() * 16, gy - 14 + rnd() * 9, 1.6, 1.1, P.KIT_GREEN_D if i % 2 else P.KIT_GREEN)
        if opening > 0:                                                       # the mouth opening in front
            c.ellipse(cx + 1, gy - 6, 4, 3.5, P.NIGHT)
            c.rect(cx - 3, gy - 6, cx + 5, gy - 3, P.NIGHT)
            c.poly([(cx - 0.5, gy - 3), (cx + 1, gy - 7 - k % 2), (cx + 2.5, gy - 3)], P.SK_PINK)
            c.px(cx + 1, gy - 4, P.SK_GLOW)
        elif eyes != "none":
            face(c, cx + 2, gy - 9, eyes=eyes, mouth="open", gap=6, eye=P.SAKURA_EYE, nose=None, blush=P.SK_PINK,
                 mouth_colour=P.SAKURA_EYE, size=3)
        for bx, by, r in ((-6, -16, 2.4), (0, -18, 2.6), (6, -16, 2.4), (-10, -6, 2), (10, -7, 2)):
            blossom(c, cx + bx, gy + by, r, turn=bx * 0.1)
    else:                                                                     # the lotus spread open
        def petal_shape(p, ang, ln, w, colour):
            a_ = math.radians(ang)
            ux, uy = math.cos(a_), -math.sin(a_)
            nx, ny = -uy, ux
            bx, by = cx, gy - 4
            p.poly([(bx + nx * w * 0.5, by + ny * w * 0.5), (bx + ux * ln * 0.5 + nx * w, by + uy * ln * 0.5 + ny * w),
                    (bx + ux * ln, by + uy * ln), (bx + ux * ln * 0.5 - nx * w, by + uy * ln * 0.5 - ny * w),
                    (bx - nx * w * 0.5, by - ny * w * 0.5)], colour)
        with shaded(c, PINK, EDGE, up=2) as p:                                # back row, wide and low
            for ang in (165, 125, 55, 15):
                petal_shape(p, ang, 11, 3.6, P.SK_PINK)
        with shaded(c, PINK, EDGE, up=2) as p:                                # front row, taller
            for ang in (140, 90, 40):
                petal_shape(p, ang, 12 if ang == 90 else 10, 3.4, P.SK_PINK_L)
        c.ellipse(cx, gy - 5, 2.6, 1.8, P.SK_GLOW)
        c.px(cx, gy - 6, P.WHITE)


def kappa_frame(opening: float = 0, k: int = 0, eyes: str = "none", balls: int = 0) -> Image.Image:
    size, cx, gy = (40, 32), 19, 29
    c = Canvas(*size)
    shell(c, cx, gy, opening, k, eyes)
    out = c.outline(EDGE).img
    for i in range(balls):
        out.alpha_composite(spike_ball_img(size, cx + 7 + i * 6, gy - 14 - i * 5 + (i % 2) * 6, k + i))
    return out


def spike_ball_img(size, x: float, y: float, k: int) -> Image.Image:
    """A pink ball with eight short spikes, turning with `k`."""
    c = Canvas(*size)
    for i in range(8):
        a = i / 8 * math.tau + k * 0.4
        c.line((x + math.cos(a) * 2.5, y + math.sin(a) * 2.5), (x + math.cos(a) * 4.5, y + math.sin(a) * 4.5), P.SK_PINK_D)
    c.ellipse(x, y, 3, 3, P.SK_PINK)
    c.ellipse(x - 0.6, y - 0.6, 1.6, 1.6, P.SK_PINK_L)
    c.px(x - 1, y - 1, P.WHITE)
    c.outline(P.SK_PINK_DD)
    return c.img


def spike_kappa() -> Sprite:
    size, cx, gy = (40, 32), 19, 29
    sprite = Sprite("spike_kappa", size, faces_left=True, cx=cx, ground=gy + 1)
    sprite.add("closed", [kappa_frame(0), kappa_frame(0, 1)], fps=3)
    sprite.add("open", [kappa_frame(0.5, 0), kappa_frame(1.0, 1)], fps=6)
    sprite.add("attack", [kappa_frame(0.5, 0), kappa_frame(0.5, 1, balls=1), kappa_frame(0.5, 2, balls=2)], fps=8,
               loop=False)
    hurt = kappa_frame(0, eyes="shut")
    sprite.add("hurt", hurt_frames(hurt, [(cx + 11, gy - 20), (cx - 11, gy - 16), (cx + 12, gy - 4)]), fps=10, loop=False)
    sprite.add("death", scatter(kappa_frame(0, eyes="x"), cx, gy, 961, depth=5), fps=8, loop=False)
    return sprite


def spike_ball() -> Sprite:
    sprite = Sprite("spike_ball", (12, 12), faces_left=True)
    sprite.add("fly", [spike_ball_img((12, 12), 5.5, 5.5, k) for k in range(4)], fps=12)
    return sprite


def build() -> list[Sprite]:
    from characters.sakura_bat_painted import NAMES as painted     # cut from the user's painted sheet instead
    sprites = [lantern_slime(), lantern_flame(), ninja_tanuki(), sakura_bat(), shadow_spirit(), spirit_flame(),
               spike_kappa(), spike_ball()]
    return [s for s in sprites if s.name not in painted]
