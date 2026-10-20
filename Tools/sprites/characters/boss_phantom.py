"""World 3 boss: the Phantom Cat Queen (84x126; about 100 tall with the crown and staff).

A pale lilac cat queen in a gold crown and a purple gown under a dark cloak with a high collar. She holds a
staff with a glowing magenta orb, floats on purple smoke and glows softly. Summons ghost cats, sends shadow
waves and teleports in a burst of violet flame; when she splits, only the brightly glowing copy is real."""
from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image

import palette as P
from bosskit import bezier, blob, flame, halo, part, tube
from draw import Canvas, _paste_clipped, noise, r, see_through, tint
from sprite import Sprite

SIZE = (84, 126)
CX, GROUND = 40, 122

CLOAK = {P.QN_PLUM: (P.PURPLE, P.QN_PLUM_D)}
ROBE = {P.PURPLE: (P.VIOLET, P.PURPLE_D)}
GOWN = {P.QN_GOWN: (P.WHITE, P.QN_GOWN_D)}
FURL = {P.LILAC: (P.WHITE, P.LILAC_D)}
VIOLET_FIRE = (P.QN_PLUM, P.PURPLE, P.VIOLET, P.QN_ORB_L)


@dataclass
class QueenPose:
    bob: float = 0
    wave: float = 0            # phase of the cloak, smoke and hem
    cast: float = 0            # 0 paw at her waist ... 1 raised high, casting
    staff: float = 4           # staff lean, degrees (+ = forward)
    orb: int = 0               # orb brightness 0...3
    eye: str = "open"          # open | shut | x | angry
    mouth: str = "smile"       # smile | open | flat
    crown_dy: float = 0
    spirits: int = 0           # little ghost cats gathering (summon)
    spirit_phase: float = 0


def crown(c: Canvas, x: float, y: float) -> None:
    """Gold crown, 14 wide, centred on x, band bottom at y, a violet gem on the tall middle point."""
    with part(c, {P.GOLD: (P.YELLOW, P.GOLD_D)}, P.GOLD_D, up=1, down=1, right=1) as k:
        k.rect(x - 7, y - 3, x + 7, y, P.GOLD)
        for dx, h in ((-6, 4), (0, 8), (6, 4)):
            k.poly([(x + dx - 2.5, y - 2), (x + dx, y - 3 - h), (x + dx + 2.5, y - 2)], P.GOLD)
            k.px(x + dx, y - 3 - h, P.GOLD)
    c.ellipse(x, y - 4, 1.6, 2, P.VIOLET)
    c.px(x, y - 5, P.QN_ORB_L)
    c.line((x - 6, y - 1), (x + 6, y - 1), P.GOLD_D)


def ghost_kitten(c: Canvas, x: float, y: float, s: float, seed: int) -> None:
    """A little floating ghost-cat head with a wispy tail: what she summons."""
    rnd = noise(seed)
    with part(c, {P.LILAC: (P.WHITE, P.LILAC_D)}, P.VIOLET, down=2) as k:
        k.poly([(x - 5 * s, y - 2 * s), (x - 4 * s, y - 8 * s), (x - 1 * s, y - 4 * s)], P.LILAC)
        k.poly([(x + 5 * s, y - 2 * s), (x + 4 * s, y - 8 * s), (x + 1 * s, y - 4 * s)], P.LILAC)
        k.ellipse(x, y, 5.5 * s, 4.5 * s, P.LILAC)
        tube(k, [(x - 3 * s, y + 3 * s, 2.5 * s), (x - 7 * s, y + 6 * s, 1.5 * s),
                 (x - 9 * s - rnd() * 2, y + 4 * s, 0.6 * s)], P.LILAC)
    c.rect(x - 2.5 * s, y - 0.5 * s, x - 1.5 * s, y + 0.5 * s, P.NIGHT)
    c.rect(x + 1.5 * s, y - 0.5 * s, x + 2.5 * s, y + 0.5 * s, P.NIGHT)
    c.px(x, y + 2 * s, P.PINK_D)


def queen(pose: QueenPose) -> Canvas:
    c = Canvas(*SIZE)
    x = CX
    b = pose.bob
    gy = GROUND
    hem = gy - 12 + b                                   # the gown's hem floats above the smoke
    hx, hy = x + 3, 44 + b

    # Cloak: dark plum, falling from the collar and flaring into curling ends on both sides.
    sway = math.sin(pose.wave) * 2
    with part(c, CLOAK, P.QN_PLUM_D, up=1, down=3, left=2, right=3) as k:
        k.poly([(x - 8, 58 + b), (x + 12, 58 + b), (x + 26 + sway, hem - 6), (x + 20 + sway, hem + 2),
                (x - 18 - sway, hem + 2), (x - 25 - sway, hem - 8)], P.QN_PLUM)
        for side, cx0 in ((-1, x - 23 - sway), (1, x + 24 + sway)):      # curled ends
            curl = [(cx0 + side * math.cos(a) * (5 - a * 0.8), hem - 8 + math.sin(a) * (5 - a * 0.8), 2.2 - a * 0.25)
                    for a in [i / 8 * 5 for i in range(9)]]
            tube(k, curl, P.QN_PLUM)
    for k in range(3):                                   # folds lit violet
        fx = x - 16 + k * 14
        c.line((fx + 4, 66 + b), (fx - 2 - sway, hem - 4), P.PURPLE)

    # Staff, held out in front: dark rod with gold bands, the orb on top.
    a = math.radians(pose.staff)
    hand = (x + 22 - pose.cast * 2, 78 + b)
    d = (math.sin(a), -math.cos(a))
    top = (hand[0] + d[0] * 48, hand[1] + d[1] * 48)
    low = (hand[0] - d[0] * 36, hand[1] - d[1] * 36)
    with part(c, {P.QN_PLUM_D: (P.QN_PLUM, None)}, None) as k:
        k.line(low, top, P.QN_PLUM_D, 2)
    for t in (0.15, 0.55, 0.9):
        p = (low[0] + (top[0] - low[0]) * t, low[1] + (top[1] - low[1]) * t)
        c.line((p[0] - 2, p[1]), (p[0] + 2, p[1]), P.GOLD, 2)
    c.poly([(top[0] - 4, top[1] + 2), (top[0], top[1] - 2), (top[0] + 4, top[1] + 2), (top[0], top[1] + 4)], P.GOLD)

    # Gown: a pale lilac bell skirt under a purple overskirt.
    with part(c, GOWN, P.QN_GOWN_D, up=1, down=3, left=2, right=4) as k:
        k.poly([(x - 6, 74 + b), (x + 8, 74 + b), (x + 18 + sway * 0.5, hem), (x - 16 - sway * 0.5, hem)], P.QN_GOWN)
        for i in range(5):                                # scalloped hem
            k.ellipse(x - 13 + i * 7 - sway * 0.3, hem, 3.5, 2.5, P.QN_GOWN)
    for i in range(3):
        fx = x - 6 + i * 6
        c.line((fx + 1, 80 + b), (fx - 2 + i * 2, hem - 2), P.QN_GOWN_D)
    with part(c, ROBE, P.PURPLE_D, up=1, down=2, left=1, right=2) as k:    # overskirt panels
        k.poly([(x - 6, 74 + b), (x - 2, 74 + b), (x - 10 - sway * 0.5, hem - 4), (x - 17 - sway * 0.5, hem - 2)],
               P.PURPLE)
        k.poly([(x + 6, 74 + b), (x + 9, 74 + b), (x + 20 + sway * 0.5, hem - 2), (x + 13 + sway * 0.5, hem - 4)],
               P.PURPLE)

    # Bodice with a gold belt and brooch.
    with part(c, ROBE, P.PURPLE_D, up=1, down=2, left=1, right=2) as k:
        k.poly([(x - 7, 60 + b), (x + 9, 60 + b), (x + 8, 76 + b), (x - 6, 76 + b)], P.PURPLE)
    c.line((x - 6, 74 + b), (x + 8, 74 + b), P.GOLD)
    c.px(x + 1, 75 + b, P.YELLOW)
    for i in range(3):
        c.px(x + 1, 63 + i * 3 + b, P.VIOLET)

    # Far paw: at her waist, or raised to cast.
    shoulder = (x - 6, 62 + b)
    paw = (x - 8 - pose.cast * 8, 76 + b - pose.cast * 30)
    elbow = ((shoulder[0] + paw[0]) / 2 - 5 + pose.cast * 2, (shoulder[1] + paw[1]) / 2 + 2)
    with part(c, ROBE, P.PURPLE_D, down=1) as k:
        k.line(shoulder, elbow, P.PURPLE, 5)
        k.line(elbow, paw, P.PURPLE, 5)
        k.poly([(paw[0] - 3, paw[1] + 1), (paw[0] + 3, paw[1] + 1), (paw[0] + 4, paw[1] + 4), (paw[0] - 4, paw[1] + 4)],
               P.PURPLE)
    with part(c, FURL, P.LILAC_D, down=1) as k:
        k.ellipse(paw[0], paw[1] - 1, 2.5, 2.5, P.LILAC)
    if pose.cast > 0.5:                                    # violet fire gathering in the raised paw
        fire = Canvas(*SIZE)
        flame(fire, paw[0], paw[1] - 2, 9 + pose.orb, 3, int(pose.wave * 3), 7, colours=VIOLET_FIRE)
        c.paste(see_through(fire.img, 220))

    # High collar: two dark flared wings standing up behind her head, lit violet inside.
    with part(c, CLOAK, P.QN_PLUM_D, up=1, down=1) as k:
        for side in (-1, 1):                               # a fan of stiff points framing the face
            bx = x + 2 + side * 3
            k.poly([(bx, 64 + b), (bx + side * 13, 56 + b), (bx + side * 17, 46 + b), (bx + side * 13, 48 + b),
                    (bx + side * 14, 40 + b), (bx + side * 9, 46 + b), (bx + side * 6, 52 + b)], P.QN_PLUM)
    for side in (-1, 1):
        bx = x + 2 + side * 3
        c.poly([(bx + side * 2, 60 + b), (bx + side * 12, 54 + b), (bx + side * 13, 49 + b), (bx + side * 6, 54 + b)],
               P.VIOLET)

    # Head: tall ears, lilac face, white muzzle, amber eyes.
    for ex, tilt in ((hx - 8, -4), (hx + 7, 3)):
        with part(c, FURL, P.LILAC_D, down=1) as k:
            k.poly([(ex - 5, hy - 5), (ex + tilt, hy - 19), (ex + 5, hy - 6)], P.LILAC)
        c.poly([(ex - 2.5, hy - 6), (ex + tilt * 0.8, hy - 15), (ex + 2.5, hy - 7)], P.PINK)
    with part(c, FURL, P.LILAC_D, up=2, down=3, left=2, right=2) as k:
        blob(k, hx, hy, 11, 9.5, P.LILAC, 330, 10, 1.6)
        for i in range(3):                                 # cheek tufts
            k.poly([(hx - 8, hy + 2 + i * 2), (hx - 14, hy + 5 + i * 3), (hx - 7, hy + 5 + i * 2)], P.LILAC)
    with part(c, {P.WHITE: (None, P.LILAC)}, None, down=2) as k:
        k.ellipse(hx + 5, hy + 5, 5, 3.5, P.WHITE)
        k.ellipse(hx + 1, hy + 6, 3, 2.5, P.WHITE)
    c.rect(hx + 8, hy + 3, hx + 9, hy + 3, P.PINK_D)             # nose
    for i in (-1, 1):                                            # whiskers
        c.line((hx + 10, hy + 5 + i), (hx + 13, hy + 5 + i * 2), P.LILAC_D)
    if pose.mouth == "smile":
        c.line((hx + 4, hy + 7), (hx + 6, hy + 8), P.PURPLE_D)
        c.line((hx + 6, hy + 8), (hx + 8, hy + 7), P.PURPLE_D)
    elif pose.mouth == "open":
        c.ellipse(hx + 6, hy + 8, 2, 1.5, P.PURPLE_D)
        c.px(hx + 5, hy + 7, P.WHITE)
    else:
        c.line((hx + 4, hy + 8), (hx + 8, hy + 8), P.PURPLE_D)
    for ex in (hx - 2, hx + 6):
        if pose.eye in ("open", "angry"):
            c.ellipse(ex, hy, 2.5, 3, P.ORANGE)
            c.ellipse(ex, hy + 0.5, 1.5, 2, P.YELLOW)
            c.rect(ex, hy - 1, ex, hy + 2, P.NIGHT)
            c.px(ex - 1, hy - 2, P.WHITE)
            c.line((ex - 3, hy - 3), (ex + 2, hy - 3), P.QN_PLUM_D)             # lashes
            if pose.eye == "angry":
                c.line((ex - 3, hy - 4), (ex + 2, hy - 3 + (1 if ex > hx else -1)), P.QN_PLUM_D)
        elif pose.eye == "shut":
            c.line((ex - 2, hy + 1), (ex + 2, hy), P.NIGHT)
        else:
            c.line((ex - 2, hy - 2), (ex + 2, hy + 2), P.NIGHT)
            c.line((ex - 2, hy + 2), (ex + 2, hy - 2), P.NIGHT)
    crown(c, hx, hy - 11 + pose.crown_dy)

    # Near arm: purple sleeve to the paw on the staff.
    shoulder = (x + 8, 62 + b)
    with part(c, ROBE, P.PURPLE_D, down=1) as k:
        k.line(shoulder, (hand[0] - 4, hand[1] - 3), P.PURPLE, 5)
        k.poly([(hand[0] - 8, hand[1] - 5), (hand[0] - 2, hand[1] - 7), (hand[0], hand[1]), (hand[0] - 6, hand[1] + 1)],
               P.PURPLE)
    with part(c, FURL, P.LILAC_D, down=1) as k:
        k.ellipse(hand[0], hand[1] - 1, 2.8, 2.5, P.LILAC)

    # The orb, with a glow around it that grows when she casts.
    orb = Canvas(*SIZE)
    orb_c = (top[0] + d[0] * 5, top[1] + d[1] * 5)
    rad = 4 + pose.orb * 0.5
    orb.ellipse(orb_c[0], orb_c[1], rad + 3 + pose.orb, rad + 3 + pose.orb, P.VIOLET)
    orb.ellipse(orb_c[0], orb_c[1], rad + 1.5 + pose.orb * 0.5, rad + 1.5 + pose.orb * 0.5, P.QN_ORB)
    c.glow = see_through(orb.img, 60 + pose.orb * 20)         # laid on after the outline: light has no edge
    c.ellipse(orb_c[0], orb_c[1], rad, rad, P.QN_ORB)
    c.ellipse(orb_c[0] - 1, orb_c[1] - 1, rad * 0.5, rad * 0.5, P.QN_ORB_L)
    c.px(orb_c[0] - 2, orb_c[1] - 2, P.WHITE)

    for k in range(pose.spirits):                          # ghost kittens gathering around her
        ang = pose.spirit_phase + k * math.tau / 3
        ghost_kitten(c, x + math.cos(ang) * 26, 70 + math.sin(ang) * 30 + b, 0.8 + k * 0.15, 350 + k)
    return c


def smoke_base(c: Canvas, wave: float, bob: float) -> None:
    """The purple smoke she floats on, curling at the edges."""
    s = Canvas(*SIZE)
    rnd = noise(380)
    for k in range(11):
        t = k / 10
        x = CX - 26 + t * 54 + math.sin(wave + k) * 1.5
        y = GROUND - 4 - abs(math.sin(t * math.pi)) * 5 + math.cos(wave * 1.3 + k * 2) * 1.2
        rad = 3 + abs(math.sin(t * math.pi)) * 4 + rnd() * 1.5
        s.ellipse(x, y, rad, rad * 0.7, (P.QN_PLUM, P.PURPLE, P.INDIGO)[k % 3])
    for k in range(5):
        s.ellipse(CX - 16 + k * 8 + math.sin(wave + k) * 2, GROUND - 9 + bob, 2.5, 1.8, P.VIOLET)
    s.outline(P.QN_PLUM_D)
    c.paste(see_through(s.img, 220))


def finish(c: Canvas, pose: QueenPose, glow: bool = True) -> Image.Image:
    full = Canvas(*SIZE)
    smoke_base(full, pose.wave, pose.bob)
    c.outline(P.NIGHT)
    full.paste(c)
    if getattr(c, "glow", None) is not None:
        full.paste(c.glow)
    img = full.img
    return halo(img, [P.VIOLET, P.PURPLE], 70) if glow else img


def draw(pose: QueenPose) -> Image.Image:
    return finish(queen(pose), pose)


def violet_burst(step: int, height: float, seed: int) -> Image.Image:
    """A burst of violet flame on the ground (teleporting, and her defeat)."""
    c = Canvas(*SIZE)
    for k, (dx, h) in enumerate(((-18, 0.5), (-10, 0.8), (-2, 1.0), (6, 0.85), (14, 0.6), (22, 0.4))):
        flame(c, CX + dx, GROUND - 2, height * h, 5, step + k, seed + k, colours=VIOLET_FIRE)
    rnd = noise(seed + step)
    for _ in range(8):                                     # sparks
        c.px(CX - 22 + rnd() * 44, GROUND - 10 - rnd() * height * 1.1, P.QN_ORB_L)
    return see_through(c.img, 230)


def build() -> list[Sprite]:
    boss = Sprite("boss_phantom", SIZE, faces_left=True, cx=CX, ground=GROUND)
    boss.add("idle", [draw(QueenPose(bob=b, wave=k * math.pi / 2, orb=(1, 2, 1, 0)[k],
                                     eye="shut" if k == 3 else "open"))
                      for k, b in enumerate((0, -1, -2, -1))], fps=5)

    boss.add("summon", [draw(QueenPose(bob=-(k % 2), wave=k, cast=min(1, k / 2), mouth="open" if k >= 2 else "smile",
                                       orb=min(3, k), spirits=min(3, max(0, k - 1)), spirit_phase=k * 0.6,
                                       crown_dy=-min(k, 2) * 0.5, eye="angry" if k >= 2 else "open"))
                        for k in range(6)], fps=8, loop=False)

    # Vanishes into a burst of violet flame and reappears.
    teleport = []
    for k, (keep, fire) in enumerate(((255, 0), (150, 34), (0, 44), (0, 30), (140, 22), (255, 10))):
        pose = QueenPose(cast=0.8 if k in (0, 5) else 0.6, orb=3, wave=k, eye="angry", mouth="open")
        body = draw(pose)
        frame = Image.new("RGBA", SIZE, P.CLEAR)
        if keep:
            frame.alpha_composite(see_through(body, keep) if keep < 255 else body)
        if fire:
            frame.alpha_composite(violet_burst(k, fire, 420))
        teleport.append(frame)
    boss.add("teleport", teleport, fps=10, loop=False)

    # The real copy: a bright halo and sparkles that the look-alikes don't have.
    split = []
    for k, b in enumerate((0, -1, -2, -1)):
        pose = QueenPose(bob=b, wave=k * math.pi / 2, orb=3, staff=6)
        img = halo(finish(queen(pose), pose, glow=False), [P.QN_ORB_L, P.QN_ORB, P.VIOLET], 200)
        c = Canvas(*SIZE)
        c.paste(img)
        rnd = noise(460 + k)
        for _ in range(6):
            sx, sy = CX - 26 + rnd() * 54, 26 + rnd() * 90
            c.line((sx - 1, sy), (sx + 1, sy), P.QN_ORB_L)
            c.line((sx, sy - 1), (sx, sy + 1), P.QN_ORB_L)
        split.append(c.img)
    boss.add("split", split, fps=6)

    hurt = draw(QueenPose(eye="shut", mouth="open", crown_dy=-3, cast=0.6, staff=-6))
    boss.add("hurt", [tint(hurt, P.WHITE, 0.8), hurt], fps=10)

    # Rises and fades away inside a column of violet flame.
    frames = []
    for k in range(8):
        t = k / 7
        body = draw(QueenPose(eye="x", mouth="open", crown_dy=-t * 6, cast=0.9, wave=k, staff=-10 * t))
        rising = Image.new("RGBA", SIZE, P.CLEAR)
        _paste_clipped(rising, body, 0, -r(t * 12))
        faded = see_through(rising, r(255 * (1 - t))) if k else tint(rising, P.WHITE, 0.7)
        if k:
            faded.alpha_composite(violet_burst(k, 20 + 40 * math.sin(t * math.pi), 480))
        frames.append(faded)
    boss.add("death", frames, fps=8, loop=False)
    return [boss]
