"""Final boss: the Void Cat (170x140; about 128 tall to the ear tips, 130 wide paw to paw).

After the giant cat in docs/concept/Void Cat Final Boss Tileset.png and the banner of
docs/concept/The Void Cat_ Final Boss Sprite Sheet.png (reference only): a huge shadowy cat of black-violet
smoke seen from the front, a starfield inside its body, blazing white-violet slanted eyes, two huge clawed
paws and a magenta portal swirling in its chest. A bright magenta rim and a violet glow keep it readable on
the dark purple backdrop. Slams shadow paws, calls down stars, opens portals and, in its last phase, flares
bright; it dies by dissolving into stars."""
from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image

import palette as P
from bosskit import bezier, blob, halo, outline, part, tube
from draw import Canvas, fade, noise, r, see_through, tint
from sprite import Sprite

SIZE = (170, 140)
CX, GROUND = 85, 136
# Suggested hitbox: 60 wide x 90 tall standing on the ground (baseY 0), centred on CX: the body column
# from the feet to the eyes. The paws, ears and glow stick out of it.
HITBOX = (60, 90)

SMOKE = {P.VC_SMOKE: (P.VC_SMOKE_L, P.VC_SMOKE_D)}
PAW = {P.VC_SMOKE: (P.VC_VIOLET, P.VC_SMOKE_D)}
BODY_COLOURS = (P.VC_SMOKE, P.VC_SMOKE_D, P.VC_SMOKE_L)


@dataclass
class VoidPose:
    step: int = 0               # animates the boiling smoke edge, the stars and the portal spin
    bob: float = 0
    eye: str = "open"           # open | wide | narrow | shut | x
    mouth: str = "shut"         # shut | open
    lpaw: tuple = (0, 0)        # offsets of the (viewer's) left and right paws from rest
    rpaw: tuple = (0, 0)
    lslam: float = 0            # 0 raised claws ... 1 flat on the ground
    rslam: float = 0
    portal: float = 1.0         # chest portal size
    side_portals: float = 0     # small portals opening on the ground at its sides
    slash: int = 0              # the claw-swipe crescent in front of it: 0 none, 1 forming, 2 full, 3 fading
    star_paw: int = 0           # stars gathering round the raised right paw (count)
    flare: float = 0            # last phase: the body flares bright


def star(c: Canvas, x: float, y: float, size: int, colour=P.VC_STAR) -> None:
    """A four-point twinkle (size 0 is a single pixel)."""
    c.px(x, y, P.WHITE if size else colour)
    for k in range(1, size + 1):
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            c.px(x + dx, y + dy, colour if k < size else P.VC_RIM_L)


def ring(c: Canvas, x: float, y: float, rad: float, spin: float, bright: float = 1.0, tall: float = 1.0) -> None:
    """A swirling magenta portal ring with a black heart and sparks running round it; `tall` stretches it
    into an upright oval (rad is the half-width)."""
    t = tall
    glow = Canvas(*c.size)
    glow.ellipse(x, y, rad + 3, rad * t + 3, P.VC_PORTAL_D)
    c.paste(see_through(glow.img, r(90 + 60 * bright)))
    c.ellipse(x, y, rad, rad * t, P.VC_PORTAL)
    c.ellipse(x, y, max(0, rad - 1.5), max(0, rad * t - 1.5), P.VC_PORTAL_D)
    c.ellipse(x, y, max(0, rad - 3), max(0, rad * t - 3), P.VC_BLACK)
    for k in range(10):                                      # swirl streaks on the ring
        a = spin + k * math.tau / 10
        c.line((x + math.cos(a) * rad, y + math.sin(a) * rad * t),
               (x + math.cos(a + 0.35) * (rad - 1.5), y + math.sin(a + 0.35) * (rad * t - 1.5)), P.VC_PORTAL_L)
    for k in range(3):
        a = spin * 1.6 + k * math.tau / 3
        c.px(x + math.cos(a) * (rad + 1), y + math.sin(a) * (rad * t + 1), P.WHITE)
    rnd = noise(int(spin * 10) + 41)
    for _ in range(3):                                       # a few stars deep inside
        c.px(x + (rnd() - 0.5) * rad, y + (rnd() - 0.5) * rad * t, P.VC_EYE_GLOW)


def arm(c: Canvas, shoulder, pos, side: int) -> None:
    """A huge smoky arm rising from behind the body's side to where the paw is (drawn behind the body)."""
    px, py = pos
    with part(c, PAW, P.VC_RIM, up=2, down=3, left=2, right=2) as k:
        tube(k, bezier([(shoulder[0], shoulder[1], 9), ((shoulder[0] + px) / 2 + side * 4, (shoulder[1] + py) / 2 + 4, 9),
                        (px, py, 10)], 10), P.VC_SMOKE)


def paw(c: Canvas, pos, side: int, slam: float, seed: int) -> None:
    """A round paw; four crescent claws hook down from it (shortened and splayed when slammed flat)."""
    px, py = pos
    with part(c, PAW, P.VC_RIM, up=2, down=3, left=2, right=2) as k:
        blob(k, px, py, 16, 14 - slam * 3, P.VC_SMOKE, seed, 12, 2.5)
    for t in range(3):                                       # toe creases
        c.line((px - 7 + t * 7, py + 2), (px - 7 + t * 7, py + 10 - slam * 3), P.VC_SMOKE_D)
    length = 14 * (1 - slam * 0.6)
    for t in range(4):                                       # crescent claws hooking down and inward
        bx, by = px - 11 + t * 7, py + 9 - slam * 3
        out = (t - 1.5) * 1.5
        pts = bezier([(bx, by, 2.4), (bx + out + side * 3, by + length * 0.5, 1.8),
                      (bx + out - side * 2 * (1 - slam), by + length, 0.5)], 8)
        tube(c, pts, P.VC_EYE_GLOW)
        for (x1, y1, _), (x2, y2, _) in zip(pts[:5], pts[1:6]):
            c.line((x1 - side * 0.8, y1), (x2 - side * 0.8, y2), P.VC_EYE)
        c.px(pts[-1][0], pts[-1][1], P.WHITE)


def voidcat(pose: VoidPose) -> Image.Image:
    c = Canvas(*SIZE)
    g = GROUND
    b = pose.bob
    hx, hy = CX + 3, g - 90 + b                             # head centre (turned a little to the right)
    step = pose.step

    # Smoke tendrils curling up off its back, behind everything.
    wisps = Canvas(*SIZE)
    for side in (-1, 1):
        sway = math.sin(step * 0.9 + side) * 3
        tube(wisps, bezier([(CX + side * 20, g - 90 + b, 5), (CX + side * 34 + sway, g - 104 + b, 4),
                            (CX + side * 28 + sway, g - 116 + b, 2.5), (CX + side * 36 + sway * 1.5, g - 122 + b, 1)],
                           12), P.VC_SMOKE_L)
    c.paste(see_through(wisps.img, 110))

    # Arms rise from behind the body's sides to the paws.
    lrest = (CX - 50 + pose.lpaw[0], g - 66 + b + pose.lpaw[1])
    rrest = (CX + 50 + pose.rpaw[0], g - 66 + b + pose.rpaw[1])
    arm(c, (CX - 22, g - 44 + b), lrest, -1)
    arm(c, (CX + 22, g - 44 + b), rrest, 1)

    # Body: one smoky silhouette from the pooled smoke at its feet up through the chest to the head and ears.
    with part(c, SMOKE, P.VC_SMOKE_D, up=3, down=5, left=3, right=4) as k:
        blob(k, CX, g - 26, 38, 26, P.VC_SMOKE, 900 + step % 4, 18, 3)                # pooled lower body
        blob(k, CX, g - 58 + b * 0.5, 33, 24, P.VC_SMOKE, 910 + step % 4, 14, 3)      # chest and shoulders
        blob(k, hx, hy, 27, 21, P.VC_SMOKE, 920, 14, 2.5)                             # head
        for side in (-1, 1):
            ex = hx + side * 15
            k.poly([(ex - side * 7, hy - 14), (ex + side * 4, hy - 38), (ex + side * 10, hy - 10)], P.VC_SMOKE)
            for t in range(3):                                                         # cheek ruff
                k.poly([(hx + side * 22, hy + t * 4 - 2), (hx + side * (32 + t * 2), hy + 4 + t * 5),
                        (hx + side * 20, hy + 6 + t * 4)], P.VC_SMOKE)
        rnd = noise(930 + step)
        for i in range(9):                                                             # smoke licking off the base
            x = CX - 40 + i * 10 + (rnd() - 0.5) * 4
            k.ellipse(x, g - 3 - rnd() * 4, 5 + rnd() * 3, 3.5, P.VC_SMOKE)
    for side in (-1, 1):                                    # inner ears, edged in magenta
        ex = hx + side * 15
        c.poly([(ex - side * 3, hy - 16), (ex + side * 4, hy - 32), (ex + side * 7, hy - 14)], P.VC_SMOKE_D)
        c.line((ex + side * 4, hy - 31), (ex + side * 6, hy - 16), P.VC_PORTAL_D)

    # Starfield inside the body, twinkling, and smoke swirling down into the chest portal.
    px0, py0 = CX, g - 34 + b * 0.5
    src = c.img.load()
    rnd = noise(940)
    for i in range(70):
        x, y = CX - 40 + rnd() * 80, g - 118 + rnd() * 112
        size = 1 if rnd() > 0.85 else 0
        phase = (i + step) % 5
        if src[r(x), r(y)][:3] in [col[:3] for col in BODY_COLOURS] and phase != 0:
            star(c, x, y, size if phase in (1, 3) else 0, (P.VC_STAR, P.VC_EYE_GLOW, P.VC_RIM_L)[i % 3])
    for k in range(3):
        rad = 22 + k * 7 + pose.portal * 2
        a0 = -step * 0.5 + k * 1.7
        pts = [(px0 + math.cos(a0 + t * 0.25) * (rad - t * 0.9), py0 + math.sin(a0 + t * 0.25) * (rad - t * 0.9) * 0.8)
               for t in range(10)]
        for p1, p2 in zip(pts, pts[1:]):
            if src[r(p1[0]), r(p1[1])][3]:
                c.line(p1, p2, P.VC_VIOLET if k % 2 else P.VC_SMOKE_L)
    ring(c, px0, py0, 13 * pose.portal, -step * 0.6, min(1.0, pose.portal - 0.4))

    # Face: glowing slanted eyes, a small pink nose, whiskers and a mouth.
    for side in (-1, 1):
        ex, ey = hx + side * 12, hy - 2
        glow = Canvas(*SIZE)
        glow.ellipse(ex, ey - 1, 9 + pose.flare * 3, 5 + pose.flare * 2, P.VC_RIM)
        c.paste(see_through(glow.img, r(40 + 60 * pose.flare)))
        if pose.eye == "shut":
            c.line((ex - 6, ey + 1), (ex + 6, ey + 1), P.VC_EYE_GLOW, 2)
            continue
        if pose.eye == "x":
            c.line((ex - 4, ey - 3), (ex + 4, ey + 3), P.VC_EYE, 2)
            c.line((ex - 4, ey + 3), (ex + 4, ey - 3), P.VC_EYE, 2)
            continue
        h = {"open": 1.0, "wide": 1.4, "narrow": 0.55}[pose.eye]
        # Outer corner high, inner corner low: a fierce slant.
        shape = [(ex + side * 8, ey - 5 * h), (ex - side * 7, ey + 1), (ex - side * 5, ey + 3 * h),
                 (ex + side * 5, ey + 2 * h)]
        c.poly(shape, P.VC_EYE_GLOW)
        inner = [(ex + side * 5.5, ey - 3 * h), (ex - side * 4.5, ey + 1), (ex - side * 3, ey + 2 * h),
                 (ex + side * 3.5, ey + 1.2 * h)]
        c.poly(inner, P.VC_EYE)
        c.px(ex + side * 2, ey - 1, P.WHITE)
    c.poly([(hx - 2.5, hy + 9), (hx + 2.5, hy + 9), (hx, hy + 12)], P.VC_NOSE)
    if pose.mouth == "open":
        c.ellipse(hx, hy + 17, 6, 4, P.VC_BLACK)
        c.ellipse(hx, hy + 18, 3, 2, P.VC_PORTAL_D)
        for side in (-1, 1):
            c.poly([(hx + side * 4, hy + 14), (hx + side * 2.5, hy + 19), (hx + side * 1.5, hy + 14)], P.VC_EYE)
    else:
        c.line((hx, hy + 12), (hx - 3, hy + 15), P.VC_SMOKE_L)
        c.line((hx, hy + 12), (hx + 3, hy + 15), P.VC_SMOKE_L)
    for side in (-1, 1):
        for t in range(3):
            c.line((hx + side * 9, hy + 11 + t * 2), (hx + side * 28, hy + 7 + t * 5), P.VC_VIOLET)

    # Paws: the far-left one, then the right one (which casts and calls the stars).
    paw(c, lrest, -1, pose.lslam, 950)
    paw(c, rrest, 1, pose.rslam, 951)
    for side, (sx, sy), slam in ((-1, lrest, pose.lslam), (1, rrest, pose.rslam)):
        if slam > 0.6:                                      # shadow smoke bursting from the impact
            puff = Canvas(*SIZE)
            rn = noise(960 + step + side)
            for _ in range(8):
                puff.ellipse(sx + (rn() - 0.5) * 34, g - 3 - rn() * 6, 3 + rn() * 3, 2.5, P.VC_SMOKE_L)
            puff.ellipse(sx, g - 2, 18, 2.5, P.VC_PORTAL_D)
            c.paste(see_through(puff.img, 220))
    if pose.star_paw:
        rnd = noise(970 + step)
        for k in range(pose.star_paw):
            a = step * 0.7 + k * math.tau / pose.star_paw
            star(c, rrest[0] + math.cos(a) * 20, rrest[1] - 6 + math.sin(a) * 14, 1 + (k + step) % 2)
        for k in range(pose.star_paw // 2):                  # stars streaking up into the sky
            sx, sy = rrest[0] - 14 + rnd() * 28, max(7, rrest[1] - 26 - rnd() * 20)
            c.line((sx, sy), (sx - 2, sy + 6), P.VC_RIM_L)
            star(c, sx, sy, 1)
    if pose.slash:                                          # a magenta crescent where the claws raked across
        arc = Canvas(*SIZE)
        span = (0.5, 1.0, 0.8)[pose.slash - 1]
        width = (2, 4, 2)[pose.slash - 1]
        sx, sy = CX + 28, g - 62
        for k in range(24):
            a = math.radians(-70 + 140 * span * k / 23)
            rad = 40
            thick = width * math.sin(math.pi * k / 23) + 0.6
            x, y = sx + math.cos(a) * rad, sy + math.sin(a) * rad
            arc.ellipse(x, y, thick, thick, P.VC_RIM_L if k % 5 else P.VC_EYE)
            arc.px(x - math.cos(a) * thick, y - math.sin(a) * thick, P.VC_EYE)
        c.paste(see_through(arc.img, (200, 255, 150)[pose.slash - 1]))
    if pose.side_portals > 0:
        for sx in (CX - 62, CX + 62):
            ring(c, sx, g - 14, 4 + 7 * pose.side_portals, step * 0.8 + sx, pose.side_portals)

    c.rect(0, g + 1, SIZE[0] - 1, SIZE[1] - 1, P.CLEAR)
    img = c.img
    if pose.flare:                                          # the last phase: lit up from within
        img = tint(img, P.VC_VIOLET, 0.35 * pose.flare)
    outline(img, P.VC_RIM)                                  # the bright magenta rim
    if pose.flare > 0.5:
        outline(img, P.VC_RIM_L)
    out = halo(img, [P.VC_VIOLET, P.VC_PORTAL_D], r(110 + 60 * pose.flare))
    out.paste(P.CLEAR, (0, GROUND + 2, SIZE[0], SIZE[1]))        # the rim under the feet, no glow below the floor
    return out


def flash(image: Image.Image, amount: float) -> Image.Image:
    """Hit flash that keeps the magenta rim, so the flashing cat still reads."""
    out = tint(image, P.WHITE, amount)
    src, dst = image.load(), out.load()
    for y in range(image.height):
        for x in range(image.width):
            if src[x, y][:3] == P.VC_RIM[:3]:
                dst[x, y] = src[x, y]
    return out


def build() -> list[Sprite]:
    boss = Sprite("boss_voidcat", SIZE, faces_left=True, cx=CX, ground=GROUND)
    boss.add("idle", [voidcat(VoidPose(step=k, bob=(0, -1, -2, -1)[k], eye="narrow" if k == 3 else "open",
                                       lpaw=(0, (0, -1, -2, -1)[k]), rpaw=(0, (0, -1, -2, -1)[(k + 2) % 4])))
                      for k in range(4)], fps=5)

    # Rears both paws up, then slams them down one after the other; shadow smoke bursts along the ground.
    boss.add("paws", [voidcat(p) for p in (
        VoidPose(step=0, lpaw=(-2, -10), rpaw=(2, -10), eye="wide"),
        VoidPose(step=1, lpaw=(-4, -20), rpaw=(4, -22), eye="wide", mouth="open", bob=-2),
        VoidPose(step=2, lpaw=(-2, -22), rpaw=(6, 38), rslam=1, eye="wide", mouth="open"),
        VoidPose(step=3, lpaw=(-6, 38), rpaw=(6, 38), lslam=1, rslam=1, eye="wide", mouth="open", bob=2),
        VoidPose(step=4, lpaw=(-6, 38), rpaw=(4, 30), lslam=1, rslam=0.7, eye="open", bob=2),
        VoidPose(step=5, lpaw=(-4, 20), rpaw=(2, 10), lslam=0.4, eye="open", bob=1),
        VoidPose(step=6, lpaw=(-2, 6), rpaw=(0, 2), eye="open"),
        VoidPose(step=7, eye="open"),
    )], fps=10, loop=False)

    # Raises its right paw and calls stars down from the void.
    boss.add("stars", [voidcat(p) for p in (
        VoidPose(step=0, rpaw=(4, -20), eye="wide"),
        VoidPose(step=1, rpaw=(6, -30), eye="wide", star_paw=3),
        VoidPose(step=2, rpaw=(6, -34), eye="wide", star_paw=5, mouth="open"),
        VoidPose(step=3, rpaw=(6, -34), eye="wide", star_paw=7, mouth="open", bob=-1),
        VoidPose(step=4, rpaw=(4, -26), eye="open", star_paw=4),
        VoidPose(step=5, rpaw=(2, -12), eye="open"),
    )], fps=8, loop=False)

    # The chest portal yawns open and small portals open on the ground at its sides.
    boss.add("portal", [voidcat(VoidPose(step=k, portal=pr, side_portals=sp, eye=e, mouth=m,
                                         lpaw=(-6 * sp, -10 * sp), rpaw=(6 * sp, -10 * sp)))
                        for k, (pr, sp, e, m) in enumerate(((1.1, 0, "open", "shut"), (1.3, 0.3, "wide", "shut"),
                                                            (1.5, 0.6, "wide", "open"), (1.6, 1.0, "wide", "open"),
                                                            (1.4, 0.8, "open", "open"), (1.2, 0.4, "open", "shut")))],
              fps=8, loop=False)

    # The final phase: the whole body flares bright and the eyes blaze.
    boss.add("phase", [voidcat(VoidPose(step=k, flare=f, eye="wide", mouth="open" if f > 0.6 else "shut",
                                        portal=1.0 + f * 0.4, bob=-(k % 2), lpaw=(-4 * f, -12 * f),
                                        rpaw=(4 * f, -12 * f)))
                       for k, f in enumerate((0.3, 0.6, 1.0, 0.8, 1.0, 0.7))], fps=8)

    # One big claw swipe across, paw raised and raked down through a magenta crescent.
    boss.add("swipe", [voidcat(p) for p in (
        VoidPose(step=0, rpaw=(-6, -24), eye="wide"),
        VoidPose(step=1, rpaw=(2, -32), eye="wide", mouth="open", bob=-1),
        VoidPose(step=2, rpaw=(8, -8), eye="wide", mouth="open", slash=1),
        VoidPose(step=3, rpaw=(6, 20), eye="wide", mouth="open", slash=2, bob=1),
        VoidPose(step=4, rpaw=(4, 12), eye="open", slash=3, bob=1),
        VoidPose(step=5, rpaw=(0, 4), eye="open"),
    )], fps=12, loop=False)

    hurt = voidcat(VoidPose(step=1, eye="shut", mouth="open", lpaw=(-4, -6), rpaw=(4, -8), bob=1))
    boss.add("hurt", [flash(hurt, 0.7), hurt], fps=10)

    # Cries out, then dissolves into stars that drift up and away.
    body = voidcat(VoidPose(step=2, eye="x", mouth="open", lpaw=(-4, -10), rpaw=(4, -12)))
    frames = []
    for k in range(10):
        t = k / 9
        frame = Canvas(*SIZE)
        if k == 0:
            frame.paste(flash(body, 0.7))
        elif t < 0.85:
            frame.paste(see_through(fade(body, 1 - t * 1.1), r(255 * (1 - t * 0.6))))
        rnd = noise(990)
        for i in range(60):
            x0, y0 = CX - 44 + rnd() * 88, GROUND - 120 + rnd() * 116
            vx, vy = (x0 - CX) * 0.25, -20 - rnd() * 30
            x, y = x0 + vx * t, y0 + vy * t
            if rnd() < t * 1.2 and 1 <= x < SIZE[0] - 2 and 2 <= y < SIZE[1] - 1 and rnd() > t * 0.7:
                star(frame, x, y, 1 if i % 4 == 0 else 0, (P.VC_STAR, P.VC_RIM_L, P.VC_EYE_GLOW)[i % 3])
        frames.append(frame.img)
    boss.add("death", frames, fps=10, loop=False)
    return [boss]
