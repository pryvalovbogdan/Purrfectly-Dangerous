"""World 4, the Cataclysm Citadel critters (from `docs/concept/Cataclysm Citadel Enemy Sprite Sheet.png`): the
lava slime, fire imp, stone guard, hell hound, ember bat, flame archer, chainsaw cat and fire wisp, and the lava
globs, fireballs, magma blasts and flame arrows they throw.

Drawn facing right with light from the top-left and mirrored on export. The citadel burns under a crimson sky,
so the critters are black and charcoal stone with an ember rim along their silhouette, a dark 1px outline
round that, and lava that runs from deep red through orange and yellow to a white-hot core. Gameplay
hitboxes (w x h, at the feet) are noted on each sprite."""
from __future__ import annotations

import math

from PIL import Image

import palette as P
from critters import ear, face, ramp, rim, shaded, sparkle
from draw import Canvas, noise, see_through, tint, vanish
from sprite import Sprite

EDGE = P.OUTLINE
COAL = ramp((P.CC_STONE, P.CC_STONE_D, P.CC_STONE_DD), (P.CC_STONE_L, P.CC_STONE, P.CC_STONE_D))
ROCK = ramp((P.CC_STONE_L, P.CC_STONE, P.CC_STONE_D), (P.CC_STONE_TOP, P.CC_STONE_L, P.CC_STONE))
LAVA_RAMP = ramp((P.LAVA_L, P.LAVA, P.CC_LAVA_D), (P.CC_LAVA_W, P.LAVA_L, P.LAVA), (P.LAVA, P.CC_LAVA_D, P.CC_LAVA_DD))
CAPE_RAMP = ramp((P.CAPE_L, P.CAPE, P.CAPE_D))
WOOD = ramp((P.PLANK_L, P.PLANK, P.PLANK_D), (P.BARK_L, P.BARK_D, P.BARK_DD))
EMBER_RIM = {P.CC_STONE_DD: P.CC_LAVA_D, P.CC_STONE_D: P.CC_LAVA_D, P.CC_STONE: P.CC_EMBER, P.CC_STONE_L: P.CC_EMBER}


# --- shared helpers --------------------------------------------------------------------------------

def flame(c: Canvas, x: float, base: float, h: float, w: float, k: int = 0, lean: float = 0) -> None:
    """One licking flame from a base `w` wide up to a tip `h` above it: deep red, orange, yellow and a
    white-hot core. `k` flickers it, `lean` tilts the tip."""
    sway = (0, 0.8, 0, -0.8)[k % 4] + lean
    for scale, colour in ((1.0, P.CC_LAVA_D), (0.75, P.LAVA), (0.5, P.LAVA_L), (0.25, P.CC_LAVA_W)):
        hw, hh = w * scale, h * scale
        c.poly([(x - hw, base), (x - hw * 0.8, base - hh * 0.45), (x + sway * scale, base - hh - (1 - scale) * h * 0.1),
                (x + hw * 0.8, base - hh * 0.5), (x + hw, base)], colour)


def blaze(c: Canvas, x0: float, x1: float, base: float, h: float, k: int, seed: int, n: int = 5, lean: float = 0) -> None:
    """A row of flames between x0 and x1 (a mane, burning ground)."""
    rnd = noise(seed)
    for i in range(n):
        t = (i + 0.5) / n
        flame(c, x0 + (x1 - x0) * t, base + rnd() * 1.5, h * (0.6 + rnd() * 0.6), 1.8 + rnd() * 1.2, k + i, lean)


def fireball(c: Canvas, x: float, y: float, r: float, k: int = 0) -> None:
    """A molten ball: a red rim, orange body, yellow inside and a white-hot heart with a turning glint."""
    c.ellipse(x, y, r, r, P.CC_LAVA_D)
    c.ellipse(x + 0.2, y - 0.2, r * 0.78, r * 0.78, P.LAVA)
    c.ellipse(x + 0.3, y - 0.3, r * 0.5, r * 0.5, P.LAVA_L)
    c.ellipse(x + 0.3, y - 0.3, max(0.6, r * 0.25), max(0.6, r * 0.25), P.CC_LAVA_W)
    a = k / 4 * math.tau
    c.px(x + math.cos(a) * r * 0.75, y + math.sin(a) * r * 0.75, P.CC_LAVA_W)


def comet(size, x: float, y: float, r: float, tail: float, k: int) -> Image.Image:
    """A fireball flying right with a tapering flame tail behind it."""
    c = Canvas(*size)
    for i in range(int(tail)):
        t = i / tail
        rr = r * (1 - t) * 0.95
        if rr < 0.4:
            continue
        colour = P.LAVA_L if t < 0.25 else (P.LAVA if t < 0.55 else P.CC_LAVA_D)
        c.ellipse(x - 1 - i, y + math.sin(i * 1.3 + k) * 0.7 * t, rr, rr, colour)
    fireball(c, x, y, r, k)
    c.outline(P.CC_LAVA_DD)
    return c.img


def embers(c: Canvas, pts) -> None:
    for i, (x, y) in enumerate(pts):
        sparkle(c, x, y, P.CC_EMBER, centre=P.CC_LAVA_W, big=i % 2 == 0)


def hit_frames(hurt: Image.Image, sparks) -> list[Image.Image]:
    """Hit: a white flash of the flinch pose, then the flinch with embers bursting off it."""
    second = Canvas(*hurt.size)
    second.paste(hurt)
    embers(second, sparks)
    return [tint(hurt, P.WHITE, 0.65), second.img]


def burning(still: Image.Image, cx: float, gy: float, width: float, seed: int, depth: float = 6) -> list[Image.Image]:
    """Death: a white flash, then it sinks and fades while flames rise from where it stood."""
    frames = [tint(still, P.WHITE, 0.6)]
    for i, t in enumerate((0.35, 0.65, 0.95)):
        body = vanish(still, t, depth=depth, flash=False)
        fire = Canvas(*still.size)
        h = 10 * (1 - t * 0.6) + 3
        blaze(fire, cx - width / 2, cx + width / 2, gy, h, i, seed, n=4)
        fire.outline(P.CC_LAVA_DD)
        body.alpha_composite(see_through(fire.img, int(255 * (1 - t * 0.55))))
        frames.append(body)
    return frames


def glowing_eyes(c: Canvas, xs, y: float, mood: str = "glow", size: int = 2) -> None:
    """Molten eyes: yellow with a white-hot core (glow), slanted (angry), shut, or crossed (x)."""
    for i, ex in enumerate(xs):
        if mood == "glow":
            c.rect(ex, y, ex + size - 1, y + size - 1, P.LAVA_L)
            c.px(ex + size - 1, y, P.CC_LAVA_W)
        elif mood == "angry":
            c.rect(ex, y + 1, ex + size - 1, y + size - 1, P.LAVA_L)
            c.px(ex + (size - 1 if i == 0 else 0), y, P.LAVA)
            c.px(ex + (0 if i == 0 else size - 1), y + size - 1, P.CC_LAVA_W)
        elif mood == "shut":
            c.rect(ex, y + size - 1, ex + size - 1, y + size - 1, P.LAVA)
        elif mood == "x":
            c.px(ex, y, P.LAVA)
            c.px(ex + size - 1, y + size - 1, P.LAVA)
            c.px(ex + size - 1, y, P.LAVA)
            c.px(ex, y + size - 1, P.LAVA)


def finish(c: Canvas, rim_map=EMBER_RIM) -> Image.Image:
    """Ember rim along the silhouette, then the dark outline."""
    rim(c, rim_map)
    return c.outline(EDGE).img


# --- lava slime [20x14] + lava_glob ----------------------------------------------------------------

def lava_slime_body(c: Canvas, cx: float, gy: float, sx: float = 1.0, sy: float = 1.0, k: int = 0, eyes: str = "open",
                    mouth: str = "w") -> None:
    """A molten dome with cat ears, a black crust on top and a pool of lava at its foot."""
    height = 14 * sy
    ry = height * 0.72
    rx = 10 * sx / 0.92
    ey = gy - height + ry
    top = gy - height + 1
    with shaded(c, LAVA_RAMP, EDGE) as p:                                     # the lava pool it slides in
        p.ellipse(cx, gy - 0.5, rx + 3, 1.6, P.LAVA)
        p.rect(0, gy + 1, p.size[0], p.size[1], P.CLEAR)
    with shaded(c, LAVA_RAMP, up=2, down=1) as p:
        ear(p, cx - 5 * sx, top + 3.5, 6.5, P.LAVA, inner=None, lean=-1.4, half=3.4)
        ear(p, cx + 5.5 * sx, top + 3.5, 6.5, P.LAVA, inner=None, lean=1.4, half=3.4)
        p.ellipse(cx, ey, rx, ry, P.LAVA)
        p.rect(0, gy, p.size[0], p.size[1], P.CLEAR)
    rnd = noise(503 + k)
    for i in range(4):                                                        # cooling black crust on the crown
        bx = cx - 5 * sx + i * 3.2 * sx + rnd() * 1.2
        by = top + 1.5 + abs(i - 1.5) * 1.2 + rnd() * 0.5
        c.ellipse(bx, by, 1.3 + rnd() * 0.6, 0.8, P.CC_STONE_D)
        c.px(bx - 0.5, by - 0.5, P.CC_STONE)
    for bx, by in ((-6, -4), (6, -3), (3, -6)):                               # bubbling hot spots
        c.px(cx + bx * sx, gy + by, P.CC_LAVA_W)
    face(c, cx + 2, gy - 7.5 * sy, eyes=eyes, mouth=mouth, gap=6, eye=P.CC_STONE_DD, shine=P.CC_LAVA_W, nose=None,
         blush=P.LAVA_L, mouth_colour=P.CC_STONE_DD, size=3)


def lava_slime() -> Sprite:
    size, cx, gy = (36, 30), 17, 27
    sprite = Sprite("lava_slime", size, faces_left=True, cx=cx, ground=gy)

    def f(sx=1.0, sy=1.0, k=0, eyes="open", mouth="w", glob=None):
        c = Canvas(*size)
        lava_slime_body(c, cx, gy, sx, sy, k, eyes, mouth)
        for i, (x, y) in enumerate(((cx - 8, gy - 17), (cx + 8, gy - 18))):     # embers rising off it
            c.px(x + (k + i) % 2, y - k % 3, P.CC_EMBER)
        out = finish(c, {P.CC_LAVA_D: P.LAVA, P.LAVA: P.LAVA_L})
        if glob:
            out.alpha_composite(comet(size, glob[0], glob[1], 3, 6, k))
        return out

    sprite.add("idle", [f(1, 1, 0), f(1.04, 0.95, 1)], fps=4)
    sprite.add("move", [f(1.1, 0.86, 0), f(0.94, 1.08, 1), f(1.0, 1.0, 2, mouth="open"), f(0.96, 1.04, 3)], fps=8)
    sprite.add("attack", [f(1.12, 0.84, 0, eyes="angry", mouth="flat"), f(0.9, 1.12, 1, eyes="angry", mouth="open",
                                                                             glob=(cx + 12, gy - 9)),
                          f(1.05, 0.95, 2, eyes="open")], fps=8, loop=False)
    hurt = f(1.1, 0.9, 1, eyes="shut", mouth="open")
    sprite.add("hit", hit_frames(hurt, [(cx - 9, gy - 16), (cx + 9, gy - 15), (cx + 1, gy - 20)]), fps=10, loop=False)
    frames = [tint(f(1, 1, 0, eyes="x", mouth="flat"), P.WHITE, 0.6), f(1.1, 0.7, 1, eyes="x", mouth="flat"),
              see_through(f(1.12, 0.45, 2, eyes="x", mouth="flat"), 200), see_through(f(1.12, 0.3, 3, eyes="x", mouth="flat"), 100)]
    sprite.add("death", frames, fps=10, loop=False)
    return sprite


def lava_glob() -> Sprite:
    sprite = Sprite("lava_glob", (10, 10), faces_left=True)
    frames = []
    for k in range(4):
        c = Canvas(10, 10)
        fireball(c, 4.5, 4.5, 3.4 + (k % 2) * 0.3, k)
        c.px(1, 4 + k % 2, P.LAVA)                                           # a drip trailing off
        frames.append(c.outline(P.CC_LAVA_DD).img)
    sprite.add("fly", frames, fps=10)
    return sprite


# --- fire imp [18x18] + fireball_shot --------------------------------------------------------------

def flame_wing(c: Canvas, root: tuple[float, float], side: int, flap: float, k: int, far: bool) -> None:
    """A wing of fire: a bony black arm with flame tongues streaming from it."""
    rx, ry = root
    span = 11 if not far else 9
    tip = (rx + side * span, ry - 6 - flap * 5)
    with shaded(c, COAL, EDGE) as p:
        p.line(root, ((rx + tip[0]) / 2, ry - 4 - flap * 3), P.CC_STONE_D, 2)
        p.line(((rx + tip[0]) / 2, ry - 4 - flap * 3), tip, P.CC_STONE_D, 1)
    fire = Canvas(*c.size)
    for i, t in enumerate((0.35, 0.65, 0.95)):
        bx = rx + (tip[0] - rx) * t
        by = ry - (4 + flap * 3) * t * 1.4
        h = (7 if not far else 5.5) * (1.1 - t * 0.3)
        flame(fire, bx, by + h * 0.9, h, 1.8, k + i, lean=-side * 1.5)
    fire.outline(P.CC_LAVA_DD)
    c.paste(see_through(fire.img, 235) if far else fire.img)


def fire_imp_frame(flap: float, k: int = 0, bob: float = 0, eyes: str = "glow", mouth: str = "fangs", arm: float = 0,
                   ball: bool = False, lean: float = 0) -> Image.Image:
    """A small horned black cat with flame wings, a glowing belly and a flame-tipped tail.
    arm: 0 = at its side, -1 = wound back, 1 = flung forward."""
    size, cx, gy = (44, 38), 20, 32
    c = Canvas(*size)
    x, y = cx + lean, gy + bob
    flame_wing(c, (x - 3, y - 11), -1, flap, k, far=False)
    flame_wing(c, (x + 2, y - 12), 1, flap * 0.8, k + 1, far=True)
    with shaded(c, COAL, EDGE) as p:                                          # tail with a flame tip
        p.line((x - 4, y - 4), (x - 9, y - 2), P.CC_STONE_D, 2)
        p.line((x - 9, y - 2), (x - 11, y - 6), P.CC_STONE_D, 1)
    with shaded(c, COAL, EDGE) as p:                                          # little legs
        p.rect(x - 3, y - 3, x - 1.5, y, P.CC_STONE_D)
        p.rect(x + 1, y - 3, x + 2.5, y, P.CC_STONE_D)
    with shaded(c, COAL, up=2) as p:
        p.ellipse(x, y - 6.5, 5, 4.5, P.CC_STONE_D)                           # body
    with shaded(c, LAVA_RAMP) as p:
        p.ellipse(x + 1, y - 5.5, 2.4, 2.8, P.LAVA)                           # glowing belly
    with shaded(c, ramp((P.CC_EMBER, P.LAVA, P.CC_LAVA_D)), EDGE) as p:       # curled horns
        p.poly([(x - 4, y - 16), (x - 7, y - 21), (x - 5, y - 21.5), (x - 2, y - 17)], P.LAVA)
        p.poly([(x + 4, y - 17), (x + 6, y - 22), (x + 8, y - 21), (x + 6.5, y - 16)], P.LAVA)
    with shaded(c, COAL, up=2) as p:
        ear(p, x - 4, y - 15, 4.5, P.CC_STONE_D, inner=P.CC_LAVA_D, lean=-0.8, half=2.4)
        ear(p, x + 5.5, y - 15, 4.5, P.CC_STONE_D, inner=P.CC_LAVA_D, lean=0.8, half=2.4)
        p.ellipse(x + 1, y - 12, 6.5, 5.5, P.CC_STONE_D)                     # big head
    glowing_eyes(c, (x - 2, x + 3), y - 14, eyes, size=3)
    if mouth == "fangs":
        c.rect(x, y - 9.5, x + 3, y - 9.5, P.CC_LAVA_D)
        c.px(x, y - 9, P.CC_LAVA_W)
        c.px(x + 3, y - 9, P.CC_LAVA_W)
    elif mouth == "open":
        c.ellipse(x + 1.5, y - 9, 1.4, 1, P.LAVA)
    hand = {0: (x + 5, y - 5), -1: (x - 1, y - 10), 1: (x + 9, y - 9)}[arm]
    with shaded(c, COAL, EDGE) as p:
        p.line((x + 3, y - 7), hand, P.CC_STONE_D, 2)
    out = finish(c)
    if ball:
        out.alpha_composite(comet(size, hand[0] + 3, hand[1] - 1, 2.6, 4, k))
    return out


def fire_imp() -> Sprite:
    size, cx, gy = (44, 38), 20, 32
    sprite = Sprite("fire_imp", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("fly", [fire_imp_frame(f, k, b) for k, (f, b) in enumerate(((1, 0), (0.3, 0), (-0.7, -1), (0.3, -1)))],
               fps=10)
    sprite.add("attack", [fire_imp_frame(0.8, 0, -1, eyes="angry", arm=-1, ball=True, lean=-1),
                          fire_imp_frame(-0.5, 1, 0, eyes="angry", mouth="open", arm=1, ball=True, lean=1),
                          fire_imp_frame(0.3, 2, 0, arm=0)], fps=8, loop=False)
    hurt = fire_imp_frame(0.5, 1, eyes="shut", mouth="open", lean=-1)
    sprite.add("hit", hit_frames(hurt, [(cx - 8, gy - 24), (cx + 10, gy - 22), (cx + 8, gy - 3)]), fps=10, loop=False)
    sprite.add("death", burning(fire_imp_frame(-0.6, 2, eyes="x", mouth="open"), cx, gy, 14, 521), fps=8, loop=False)
    return sprite


def fireball_shot() -> Sprite:
    sprite = Sprite("fireball_shot", (12, 10), faces_left=True)
    sprite.add("fly", [comet((12, 10), 8, 4.5, 3.3, 7, k) for k in range(4)], fps=12)
    return sprite


# --- stone guard [26x32] + magma_blast -------------------------------------------------------------

def seams(c: Canvas, lines) -> None:
    """Glowing lava cracks: an orange line with yellow-hot points along it."""
    for a, b in lines:
        c.line((a[0], a[1] + 1), (b[0], b[1] + 1), P.CC_LAVA_D)
        c.line(a, b, P.LAVA)
        c.px((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, P.CC_LAVA_W)


def stone_guard_frame(step: int = 0, walk: bool = False, punch: float = 0, eyes: str = "glow", lean: float = 0,
                      blast: float = 0, k: int = 0) -> Image.Image:
    """A hulking cat-eared golem of black stone plates split by glowing lava seams, with molten fists.
    punch: 0 = fists down, -1 = fist drawn back, 1 = thrust forward. blast: a magma ball forming at the fist."""
    size, x, gy = (60, 46), 22, 43
    c = Canvas(*size)
    bob = (step % 2) if walk else 0
    by = gy - bob
    x += lean
    lifts = ((step % 2) * 2, ((step + 1) % 2) * 2) if walk else (0, 0)
    with shaded(c, COAL, EDGE) as p:                                          # far arm behind
        p.ellipse(x - 11, by - 17, 4, 4, P.CC_STONE_D)
        p.line((x - 11, by - 15), (x - 12, by - 8), P.CC_STONE_D, 5)
        p.ellipse(x - 12, by - 7, 3.6, 3.2, P.CC_STONE_D)
    with shaded(c, ROCK, EDGE) as p:                                          # thick legs
        p.rect(x - 8, by - 8, x - 3, gy - lifts[0], P.CC_STONE)
        p.rect(x + 2, by - 8, x + 7, gy - lifts[1], P.CC_STONE)
        p.rect(x - 9, gy - 2 - lifts[0], x - 2, gy - lifts[0], P.CC_STONE)
        p.rect(x + 1, gy - 2 - lifts[1], x + 8, gy - lifts[1], P.CC_STONE)
    with shaded(c, ROCK, up=2) as p:
        p.ellipse(x - 0.5, by - 17, 11, 10, P.CC_STONE)                      # plated torso
        p.rect(x - 8, by - 10, x + 7, by - 7, P.CC_STONE)                      # belt
    with shaded(c, ROCK, EDGE, up=2) as p:                                    # cat head
        ear(p, x - 2, by - 31, 5, P.CC_STONE, inner=P.CC_LAVA_D, lean=-0.8, half=2.8)
        ear(p, x + 7.5, by - 31, 5, P.CC_STONE, inner=P.CC_LAVA_D, lean=0.8, half=2.8)
        p.ellipse(x + 3, by - 26, 7, 6, P.CC_STONE)
    seams(c, [((x - 6, by - 21), (x - 2, by - 16)), ((x - 2, by - 16), (x + 3, by - 18)), ((x - 7, by - 12), (x + 5, by - 12)),
              ((x + 4, by - 22), (x + 7, by - 15)), ((x - 6, by - 4), (x - 4, by - 1)), ((x + 3, by - 5), (x + 5, by - 2)),
              ((x - 1, by - 30), (x + 1, by - 27))])
    c.rect(x - 8, by - 9, x + 7, by - 9, P.CC_STONE_D)
    c.rect(x - 1, by - 10, x + 1, by - 8, P.LAVA)                             # belt buckle
    glowing_eyes(c, (x + 1, x + 6), by - 28, eyes)
    c.rect(x + 2, by - 23.5, x + 6, by - 23.5, P.CC_LAVA_D)                   # mouth
    sh = (x + 7, by - 19)
    if punch > 0:
        fist = (x + 15 + punch * 4, by - 18)
    elif punch < 0:
        fist = (x - 1, by - 21)
    else:
        fist = (x + 11, by - 7)
    with shaded(c, ROCK, EDGE) as p:
        p.ellipse(sh[0], sh[1], 4.2, 4, P.CC_STONE)                           # pauldron
        p.line(sh, fist, P.CC_STONE, 5)
        p.ellipse(fist[0], fist[1], 3.8, 3.6, P.CC_STONE)
    with shaded(c, LAVA_RAMP) as p:                                           # molten knuckles
        p.ellipse(fist[0] + 1.5, fist[1], 1.8, 2.6, P.LAVA)
    out = finish(c)
    if blast:
        b = Canvas(*size)
        fireball(b, fist[0] + 6 + blast * 2, fist[1], 2.5 + blast * 2, k)
        b.outline(P.CC_LAVA_DD)
        embers(b, [(fist[0] + 8, fist[1] - 7), (fist[0] + 11, fist[1] + 5)])
        out.alpha_composite(b.img)
    return out


def stone_guard() -> Sprite:
    size, cx, gy = (60, 46), 22, 43
    sprite = Sprite("stone_guard", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [stone_guard_frame(), stone_guard_frame(lean=-0.6, eyes="angry")], fps=3)
    sprite.add("walk", [stone_guard_frame(k, walk=True) for k in range(4)], fps=6)
    sprite.add("attack", [stone_guard_frame(punch=-1, lean=-1, eyes="angry"),
                          stone_guard_frame(punch=0.4, eyes="angry", blast=0.3),
                          stone_guard_frame(punch=1, lean=1, eyes="angry", blast=1, k=1),
                          stone_guard_frame(punch=0.3)], fps=8, loop=False)
    hurt = stone_guard_frame(lean=-1.5, eyes="shut")
    sprite.add("hit", hit_frames(hurt, [(cx + 13, gy - 34), (cx - 13, gy - 28), (cx + 15, gy - 12)]), fps=10, loop=False)
    sprite.add("death", burning(stone_guard_frame(eyes="x"), cx, gy, 20, 541, depth=10), fps=8, loop=False)
    return sprite


def magma_blast() -> Sprite:
    sprite = Sprite("magma_blast", (14, 12), faces_left=True)
    sprite.add("fly", [comet((14, 12), 9, 5.5, 4.4, 7, k) for k in range(4)], fps=12)
    return sprite


# --- hell hound [26x18] ----------------------------------------------------------------------------

def hound_frame(phase: float = 0, run: bool = False, k: int = 0, eyes: str = "glow", jaw: float = 0.3, crouch: float = 0,
                lunge: float = 0, breath: bool = False) -> Image.Image:
    """A lean black hound-cat on four legs with a flaming mane along its back, lava spots and glowing jaws.
    phase drives the gallop; jaw opens the mouth (0...1)."""
    size, cx, gy = (58, 34), 22, 31
    c = Canvas(*size)
    x = cx + lunge
    body_y = gy - 11 + crouch

    def leg(hip, ph, colour, front):
        swing = math.sin(ph) * (38 if run else 6)
        knee = (hip[0] + math.sin(math.radians(swing)) * 4.5, hip[1] + math.cos(math.radians(swing)) * 4.5)
        bend = (-35 if front else 40) * (max(0.0, -math.cos(ph)) if run else 0.2)
        foot = (knee[0] + math.sin(math.radians(swing + bend)) * 4.5, min(gy - 0.5, knee[1] + math.cos(math.radians(swing + bend)) * 4.5))
        c.line(hip, knee, colour, 3)
        c.line(knee, foot, colour, 2)
        c.rect(foot[0] - 0.5, foot[1] - 0.5, foot[0] + 2, foot[1] + 0.5, colour)

    lift = abs(math.sin(phase)) * 1.2 if run else 0
    hipb, hipf = (x - 8, body_y + 3 - lift), (x + 6, body_y + 3 - lift)
    mane = Canvas(*size)                                                      # the flaming mane, behind the body
    blaze(mane, x - 12, x + 6, body_y - 2 - lift, 9, k, 561, n=6, lean=-2 - (2 if run else 0))
    mane.outline(P.CC_LAVA_DD)
    c.paste(mane)
    leg(hipb, phase + math.pi, P.CC_STONE_DD, False)
    leg(hipf, phase, P.CC_STONE_DD, True)
    with shaded(c, COAL, EDGE) as p:                                          # tail
        p.line((x - 12, body_y - 1 - lift), (x - 17, body_y - 4 - lift), P.CC_STONE_D, 2)
    with shaded(c, COAL, up=2) as p:
        p.ellipse(x - 1, body_y - lift, 11, 5, P.CC_STONE_D)                  # long body
        p.ellipse(x - 8, body_y + 0.5 - lift, 5, 5, P.CC_STONE_D)             # haunch
    leg((hipb[0] + 2, hipb[1]), phase, P.CC_STONE_D, False)
    leg((hipf[0] + 2, hipf[1]), phase + math.pi, P.CC_STONE_D, True)
    for sx_, sy_ in ((-6, -2), (-2, 1), (3, -1), (-9, 2)):                    # lava spots
        c.rect(x + sx_, body_y + sy_ - lift, x + sx_ + 1, body_y + sy_ - lift, P.LAVA)
        c.px(x + sx_, body_y + sy_ - lift, P.LAVA_L)
    hx, hy = x + 11, body_y - 4 - lift + crouch * 0.5
    with shaded(c, COAL, EDGE, up=2) as p:
        ear(p, hx - 3, hy - 4, 5, P.CC_STONE_D, inner=P.CC_LAVA_D, lean=-1.2, half=2.6)
        ear(p, hx + 2, hy - 4.5, 5, P.CC_STONE_D, inner=P.CC_LAVA_D, lean=0.4, half=2.6)
        p.ellipse(hx, hy, 5.5, 4.5, P.CC_STONE_D)                             # head
        p.poly([(hx + 2, hy - 1), (hx + 9, hy + 0.5), (hx + 9, hy + 2), (hx + 2, hy + 2.5)], P.CC_STONE_D)   # snout
        p.poly([(hx + 1, hy + 2.5 + jaw * 2.5), (hx + 8, hy + 3 + jaw * 3.5), (hx + 8, hy + 4 + jaw * 3.5),
                (hx + 1, hy + 4.5)], P.CC_STONE_D)                             # lower jaw
    if jaw > 0.1:                                                             # glowing maw and fangs
        c.poly([(hx + 2, hy + 2.5), (hx + 8.5, hy + 2), (hx + 8.5, hy + 3 + jaw * 3.5), (hx + 2, hy + 3)], P.LAVA)
        c.line((hx + 3, hy + 2.5), (hx + 7, hy + 2.5 + jaw), P.LAVA_L)
        for fx in (hx + 4, hx + 7):
            c.px(fx, hy + 2.5, P.CC_LAVA_W)
            c.px(fx, hy + 2.5 + jaw * 3, P.CC_LAVA_W)
    c.px(hx + 9, hy + 0.5, P.CC_STONE_DD)                                     # nose
    glowing_eyes(c, (hx + 1,), hy - 2, eyes)
    out = finish(c)
    if breath:
        out.alpha_composite(comet(size, hx + 13, hy + 3, 3, 6, k))
    return out


def hell_hound() -> Sprite:
    size, cx, gy = (58, 34), 22, 31
    sprite = Sprite("hell_hound", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [hound_frame(k=0, jaw=0.3), hound_frame(k=1, jaw=0.5, eyes="angry")], fps=4)
    sprite.add("run", [hound_frame(i / 6 * math.tau, True, i, jaw=0.4) for i in range(6)], fps=12)
    sprite.add("attack", [hound_frame(k=0, crouch=2, lunge=-2, eyes="angry", jaw=0.2),
                          hound_frame(1.2, True, 1, eyes="angry", jaw=0.9, lunge=2),
                          hound_frame(2.2, True, 2, eyes="angry", jaw=1.0, lunge=4, breath=True),
                          hound_frame(k=3, jaw=0.4, lunge=1)], fps=10, loop=False)
    hurt = hound_frame(k=1, eyes="shut", jaw=0.6, crouch=1, lunge=-1)
    sprite.add("hit", hit_frames(hurt, [(cx + 14, gy - 24), (cx - 8, gy - 26), (cx + 16, gy - 6)]), fps=10, loop=False)
    sprite.add("death", burning(hound_frame(k=2, eyes="x", jaw=0.8, crouch=2), cx, gy, 24, 571), fps=8, loop=False)
    return sprite


# --- ember bat [18x14] -----------------------------------------------------------------------------

EMBER_WING = ramp((P.LAVA, P.CC_LAVA_D, P.CC_LAVA_DD), (P.LAVA_L, P.LAVA, P.CC_LAVA_D))


def ember_wing(c: Canvas, root, side: int, flap: float, far: bool, swept: float = 0) -> None:
    rx, ry = root
    span = (17 if not far else 15) * (1 - swept * 0.35)
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
    with shaded(c, EMBER_WING, EDGE, up=1, down=1) as p:
        p.poly(pts, P.CC_LAVA_D if far else P.LAVA)
    with shaded(c, COAL) as p:
        p.line(root, elbow, P.CC_STONE_D, 2)
        p.line(elbow, tip, P.CC_STONE_D, 1)
    for f in fingers:
        c.line(elbow, f, P.CC_STONE_D)
    c.px(tip[0], tip[1], P.LAVA_L)


def ember_bat_frame(flap: float, eyes: str = "glow", bob: float = 0, dive: float = 0, k: int = 0, trail: bool = False) -> Image.Image:
    size, cx, gy = (50, 34), 25, 27
    c = Canvas(*size)
    y = gy + bob
    x = cx + dive * 3
    ember_wing(c, (x - 3, y - 10), -1, flap, False, dive)
    ember_wing(c, (x + 3, y - 10), 1, flap * 0.85, True, dive)
    with shaded(c, COAL, EDGE, up=2) as p:
        p.ellipse(x - 1, y - 5, 5.5, 4.5, P.CC_STONE_D)
        p.rect(x - 4, y - 1, x - 2, y, P.CC_STONE_D)
        p.rect(x + 1, y - 1, x + 3, y, P.CC_STONE_D)
    with shaded(c, COAL, EDGE, up=2) as p:
        ear(p, x - 3.5, y - 15, 6, P.CC_STONE_D, inner=P.CC_LAVA_D, lean=-1, half=3)
        ear(p, x + 5.5, y - 15, 6, P.CC_STONE_D, inner=P.CC_LAVA_D, lean=1, half=3)
        p.ellipse(x + 1, y - 11, 7, 6, P.CC_STONE_D)
    glowing_eyes(c, (x - 2, x + 3), y - 13, eyes, size=3)
    c.rect(x, y - 8.5, x + 3, y - 8.5, P.CC_LAVA_D)
    c.px(x, y - 8, P.CC_LAVA_W)
    c.px(x + 3, y - 8, P.CC_LAVA_W)
    out = finish(c)
    if trail:                                                                 # a fire trail behind the dive
        t = Canvas(*size)
        for i in range(4):
            flame(t, x - 10 - i * 4, y - 4 - i * 2.5, 6 - i, 2.2 - i * 0.3, k + i, lean=-3)
        t.outline(P.CC_LAVA_DD)
        trail_img = see_through(t.img, 220)
        trail_img.alpha_composite(out)
        out = trail_img
    return out


def ember_bat() -> Sprite:
    size, cx, gy = (50, 34), 25, 27
    sprite = Sprite("ember_bat", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("fly", [ember_bat_frame(f, bob=b) for f, b in ((1, 0), (0.2, 0), (-0.9, -1), (0.2, -1))], fps=12)
    sprite.add("attack", [ember_bat_frame(1, "angry", -1), ember_bat_frame(-0.3, "angry", 0, 1, 1, trail=True),
                          ember_bat_frame(0.4, "angry", 0, 0.4, 2, trail=True)], fps=10, loop=False)
    hurt = ember_bat_frame(0.6, "shut")
    sprite.add("hit", hit_frames(hurt, [(cx - 6, gy - 22), (cx + 10, gy - 20), (cx + 4, gy - 2)]), fps=10, loop=False)
    dead = ember_bat_frame(-0.5, "x")
    sprite.add("death", [tint(dead, P.WHITE, 0.6), vanish(dead, 0.45, depth=8, flash=False),
                         vanish(dead, 0.9, depth=8, flash=False)], fps=10, loop=False)
    return sprite


# --- flame archer [16x24] + flame_arrow ------------------------------------------------------------

def bow(c: Canvas, x: float, y: float, draw_back: float, arrow: bool) -> None:
    """A recurve bow held upright at (x, y) with its string pulled back by `draw_back` px."""
    top, bot = (x - 1, y - 11), (x - 1, y + 11)
    with shaded(c, WOOD, EDGE) as p:
        p.line(top, (x + 2.5, y - 6), P.BARK_D, 2)
        p.line((x + 2.5, y - 6), (x + 3, y), P.BARK_D, 2)
        p.line((x + 3, y), (x + 2.5, y + 6), P.BARK_D, 2)
        p.line((x + 2.5, y + 6), bot, P.BARK_D, 2)
    c.px(x + 3, y - 1, P.GOLD)
    c.px(x + 3, y + 1, P.GOLD)
    nock = (x - 1 - draw_back, y)
    c.line(top, nock, P.CC_LAVA_W)
    c.line(nock, bot, P.CC_LAVA_W)
    if arrow:
        c.line(nock, (x + 7, y), P.BARK_L)
        flame(c, x + 8, y + 1.5, 3, 1.4, int(draw_back), lean=4)
        c.px(x + 8, y, P.CC_LAVA_W)


def flame_archer_frame(step: int = 0, walk: bool = False, draw_back: float = 0, arrow: bool = True, eyes: str = "glow",
                       lean: float = 0, k: int = 0) -> Image.Image:
    """A hooded cultist cat in a charcoal robe with a red cape and a glowing face, holding a bow."""
    size, x, gy = (46, 36), 16, 33
    c = Canvas(*size)
    x += lean
    sway = (0, 1, 0, -1)[step % 4] if walk else 0
    with shaded(c, CAPE_RAMP, EDGE) as p:                                     # cape streaming behind
        p.poly([(x - 3, gy - 19), (x - 9 - sway, gy - 4), (x - 7 - sway, gy - 1), (x - 1, gy - 6)], P.CAPE)
    lifts = ((step % 2) * 1.5, ((step + 1) % 2) * 1.5) if walk else (0, 0)
    with shaded(c, COAL, EDGE) as p:                                          # boots
        p.rect(x - 4, gy - 2 - lifts[0], x - 1, gy - lifts[0], P.CC_STONE_DD)
        p.rect(x + 1, gy - 2 - lifts[1], x + 4, gy - lifts[1], P.CC_STONE_DD)
    with shaded(c, COAL, up=2) as p:
        p.poly([(x - 5, gy - 16), (x + 5, gy - 16), (x + 6.5, gy - 2), (x - 6.5, gy - 2)], P.CC_STONE_D)   # robe
    c.rect(x - 1, gy - 14, x + 1, gy - 3, P.CC_BANNER)                        # red sash down the front
    c.line((x - 1, gy - 14), (x - 1, gy - 3), P.CC_BANNER_D)
    c.rect(x - 1, gy - 10, x + 1, gy - 10, P.GOLD)
    with shaded(c, COAL, EDGE, up=2) as p:                                    # hood with cat ears
        ear(p, x - 3.5, gy - 25, 5, P.CC_STONE_D, inner=P.CC_STONE_DD, lean=-0.8, half=2.6)
        ear(p, x + 4.5, gy - 25, 5, P.CC_STONE_D, inner=P.CC_STONE_DD, lean=0.8, half=2.6)
        p.ellipse(x + 0.5, gy - 20, 6.5, 6, P.CC_STONE_D)
    with shaded(c, LAVA_RAMP) as p:                                           # the glowing face in the hood
        p.ellipse(x + 2, gy - 19, 4, 3.6, P.CC_LAVA_D)
    glowing_eyes(c, (x, x + 3), gy - 20.5, eyes)
    c.px(x + 2, gy - 17, P.LAVA_L)
    hand = (x + 7, gy - 12)
    with shaded(c, COAL, EDGE) as p:                                          # arms holding the bow and string
        p.line((x + 2, gy - 14), hand, P.CC_STONE_D, 2)
        p.line((x + 1, gy - 13), (x + 6 - draw_back, gy - 12), P.CC_STONE_D, 2)
    bow(c, hand[0] + 1, hand[1], draw_back, arrow)
    return finish(c)


def flame_archer() -> Sprite:
    size, cx, gy = (46, 36), 16, 33
    sprite = Sprite("flame_archer", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [flame_archer_frame(), flame_archer_frame(eyes="angry", k=1)], fps=3)
    sprite.add("walk", [flame_archer_frame(k, walk=True) for k in range(4)], fps=8)
    release = Canvas(*size)
    release.paste(flame_archer_frame(draw_back=0, arrow=False, eyes="angry", lean=-1))
    release.paste(arrow_img(size, cx + 16, gy - 12, 0))
    sprite.add("attack", [flame_archer_frame(draw_back=2, eyes="angry"), flame_archer_frame(draw_back=4, eyes="angry"),
                          release.img, flame_archer_frame(draw_back=0, arrow=False)], fps=8, loop=False)
    hurt = flame_archer_frame(arrow=False, eyes="shut", lean=-1)
    sprite.add("hit", hit_frames(hurt, [(cx + 10, gy - 28), (cx - 9, gy - 24), (cx + 12, gy - 6)]), fps=10, loop=False)
    sprite.add("death", burning(flame_archer_frame(arrow=False, eyes="x"), cx, gy, 16, 591), fps=8, loop=False)
    return sprite


def arrow_img(size, x: float, y: float, k: int) -> Image.Image:
    """A flaming arrow flying right: shaft, fletching, and a burning head at x."""
    c = Canvas(*size)
    c.line((x - 12, y), (x - 1, y), P.BARK_L)
    c.px(x - 12, y - 1, P.CC_BANNER)
    c.px(x - 12, y + 1, P.CC_BANNER)
    c.px(x - 11, y - 1, P.CC_BANNER_D)
    flame(c, x, y + 1.5, 3, 1.5, k, lean=-3)
    c.poly([(x - 1, y - 1.5), (x + 2, y), (x - 1, y + 1.5)], P.LAVA_L)
    c.px(x, y, P.CC_LAVA_W)
    c.outline(P.CC_LAVA_DD)
    return c.img


def flame_arrow() -> Sprite:
    sprite = Sprite("flame_arrow", (16, 6), faces_left=True)
    sprite.add("fly", [arrow_img((16, 6), 13, 2.5, k) for k in range(2)], fps=10)
    return sprite


# --- chainsaw cat [26x30] --------------------------------------------------------------------------

def chainsaw(c: Canvas, grip: tuple[float, float], angle: float, length: float, k: int) -> tuple[float, float]:
    """A blocky motor housing at `grip` with a glowing bar running `length` px along `angle` degrees."""
    a = math.radians(angle)
    ux, uy = math.cos(a), -math.sin(a)
    nx, ny = -uy, ux
    gx, gy_ = grip
    start = (gx + ux * 4, gy_ + uy * 4)
    end = (start[0] + ux * length, start[1] + uy * length)
    bar = [(start[0] + nx * 2.5, start[1] + ny * 2.5), (end[0] + nx * 2.5, end[1] + ny * 2.5),
           (end[0] + ux * 2, end[1] + uy * 2), (end[0] - nx * 2.5, end[1] - ny * 2.5),
           (start[0] - nx * 2.5, start[1] - ny * 2.5)]
    with shaded(c, LAVA_RAMP, EDGE) as p:
        p.poly(bar, P.LAVA)
    c.line(start, end, P.LAVA_L)
    for i in range(int(length / 2)):                                          # the running chain's teeth
        t = (i * 2 + k) / length
        if t > 1:
            continue
        tx, ty = start[0] + (end[0] - start[0]) * t, start[1] + (end[1] - start[1]) * t
        c.px(tx + nx * 2.5, ty + ny * 2.5, P.CC_LAVA_W if i % 2 else P.CC_LAVA_DD)
        c.px(tx - nx * 2.5, ty - ny * 2.5, P.CC_LAVA_DD if i % 2 else P.CC_LAVA_W)
    with shaded(c, ROCK, EDGE, up=2) as p:                                    # motor housing
        p.ellipse(gx, gy_, 4.5, 4.2, P.CC_STONE)
        p.rect(gx - 4, gy_ - 3.5, gx + 4, gy_ + 3.5, P.CC_STONE)
    c.ellipse(gx, gy_, 1.6, 1.6, P.LAVA)
    c.px(gx, gy_, P.CC_LAVA_W)
    return end


def chainsaw_frame(step: int = 0, walk: bool = False, saw: str = "low", eyes: str = "glow", lean: float = 0, k: int = 0,
                   sparks: bool = False) -> Image.Image:
    """A horned executioner cat in black armour and a red cape, with a glowing chainsaw.
    saw: low (held angled down in front), up (raised for the swing), out (swept level, reaching far ahead)."""
    size, x, gy = (70, 48), 22, 45
    c = Canvas(*size)
    x += lean
    lifts = ((step % 2) * 2, ((step + 1) % 2) * 2) if walk else (0, 0)
    bob = (step % 2) if walk else 0
    by = gy - bob
    with shaded(c, CAPE_RAMP, EDGE) as p:                                     # red cape behind
        p.poly([(x - 5, by - 24), (x - 13 - (step % 2), by - 6), (x - 10, by - 2), (x - 2, by - 8)], P.CAPE)
    with shaded(c, COAL, EDGE) as p:                                          # armoured legs
        p.rect(x - 7, by - 9, x - 2, gy - lifts[0], P.CC_STONE_D)
        p.rect(x + 2, by - 9, x + 7, gy - lifts[1], P.CC_STONE_D)
        p.rect(x - 8, gy - 2 - lifts[0], x - 1, gy - lifts[0], P.CC_STONE_D)
        p.rect(x + 1, gy - 2 - lifts[1], x + 8, gy - lifts[1], P.CC_STONE_D)
    with shaded(c, COAL, up=2) as p:
        p.ellipse(x, by - 16, 9.5, 8.5, P.CC_STONE_D)                         # breastplate
        p.rect(x - 7, by - 10, x + 7, by - 7, P.CC_STONE_D)
    c.line((x, by - 23), (x, by - 9), P.CC_STONE)
    for rx_, ry_ in ((x - 5, by - 18), (x + 4, by - 14), (x - 4, by - 9), (x + 4, by - 9)):   # rivets
        c.px(rx_, ry_, P.CC_EMBER)
    with shaded(c, COAL, EDGE, up=2) as p:                                    # pauldrons
        p.ellipse(x - 8, by - 21, 4, 3.5, P.CC_STONE_D)
        p.ellipse(x + 7, by - 21, 4, 3.5, P.CC_STONE_D)
    hx, hy = x + 2, by - 28
    with shaded(c, ramp((P.CC_EMBER, P.LAVA, P.CC_LAVA_D)), EDGE) as p:      # curved horns
        p.poly([(hx - 4, hy - 3), (hx - 8, hy - 8), (hx - 9, hy - 12), (hx - 6, hy - 8), (hx - 2, hy - 5)], P.LAVA)
        p.poly([(hx + 4, hy - 4), (hx + 8, hy - 9), (hx + 9, hy - 13), (hx + 6, hy - 9), (hx + 2, hy - 5)], P.LAVA)
    with shaded(c, COAL, EDGE, up=2) as p:                                    # helmet with cat ears
        ear(p, hx - 3.5, hy - 4.5, 4, P.CC_STONE_D, inner=None, lean=-0.6, half=2.2)
        ear(p, hx + 4, hy - 4.5, 4, P.CC_STONE_D, inner=None, lean=0.6, half=2.2)
        p.ellipse(hx, hy, 6.5, 6, P.CC_STONE_D)
    c.rect(hx - 4, hy - 1, hx + 5, hy + 1, P.CC_STONE_DD)                    # visor
    glowing_eyes(c, (hx - 2, hx + 2.5), hy - 1, eyes)
    c.line((hx, hy - 6), (hx, hy - 2), P.CC_STONE)
    grip, angle, ln = {"low": ((x + 7, by - 11), -20, 18), "up": ((x + 3, by - 22), 60, 16),
                       "out": ((x + 9, by - 15), 2, 24)}[saw]
    end = chainsaw(c, grip, angle, ln, k)
    with shaded(c, COAL, EDGE) as p:                                          # gauntlets on the saw
        p.ellipse(grip[0] - 2, grip[1] + 2, 2.4, 2.2, P.CC_STONE_D)
    out = finish(c)
    if sparks:
        s = Canvas(*size)
        for i in range(4):
            flame(s, end[0] - 3 - i * 6, grip[1] + 3 - i * 0.3, 4 + i % 2, 1.6, k + i, lean=-4)
        embers(s, [(end[0] + 1, end[1] - 6), (end[0] - 7, end[1] + 6)])
        s.outline(P.CC_LAVA_DD)
        out.alpha_composite(see_through(s.img, 230))
    return out


def chainsaw_cat() -> Sprite:
    size, cx, gy = (70, 48), 22, 45
    sprite = Sprite("chainsaw_cat", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [chainsaw_frame(k=0), chainsaw_frame(k=1, eyes="angry")], fps=6)
    sprite.add("walk", [chainsaw_frame(i, walk=True, k=i) for i in range(4)], fps=8)
    sprite.add("attack", [chainsaw_frame(saw="up", lean=-1, eyes="angry", k=0),
                          chainsaw_frame(saw="out", lean=2, eyes="angry", k=1, sparks=True),
                          chainsaw_frame(saw="out", lean=3, eyes="angry", k=2, sparks=True),
                          chainsaw_frame(saw="low", k=3)], fps=10, loop=False)
    hurt = chainsaw_frame(lean=-1.5, eyes="shut", k=1)
    sprite.add("hit", hit_frames(hurt, [(cx + 10, gy - 38), (cx - 12, gy - 30), (cx + 13, gy - 22)]), fps=10, loop=False)
    sprite.add("death", burning(chainsaw_frame(eyes="x", k=2), cx, gy, 22, 611, depth=9), fps=8, loop=False)
    return sprite


# --- fire wisp [14x14] -----------------------------------------------------------------------------

def wisp_body(c: Canvas, x: float, y: float, k: int, swell: float = 1.0, eyes: str = "open", mouth: str = "w") -> None:
    """A floating flame with a cat face: a round fiery head whose ears and crown are flame tips, trailing
    licks of fire behind. (x, y) is the bottom of its body."""
    r = 6 * swell
    cy = y - r
    tail = Canvas(*c.size)
    for i in range(3):                                                        # licks of fire streaming behind
        flame(tail, x - 3 - i * 2.5, cy + 3 + i, 7 - i * 1.5, 2.2 - i * 0.4, k + i, lean=-5 - i)
    c.paste(tail)
    flame(c, x - 3.5 * swell, cy - r + 3, 5 * swell, 2.2 * swell, k, lean=-1)    # flame ears
    flame(c, x + 3.5 * swell, cy - r + 3, 5 * swell, 2.2 * swell, k + 1, lean=1)
    flame(c, x, cy - r + 2, 6 * swell, 2.4 * swell, k + 2)                      # crown
    c.ellipse(x, cy, r, r, P.LAVA)
    c.ellipse(x - 0.5, cy - 0.5, r * 0.75, r * 0.72, P.LAVA_L)
    c.ellipse(x - 1, cy - 1.5, r * 0.35, r * 0.3, P.CC_LAVA_W)
    face(c, x + 1, cy - 1, eyes=eyes, mouth=mouth, gap=5, eye=P.CC_LAVA_DD, shine=P.CC_LAVA_W, nose=None,
         blush=P.CC_LAVA_D, mouth_colour=P.CC_LAVA_DD, size=3)


def wisp_frame(k: int = 0, bob: float = 0, swell: float = 1.0, eyes: str = "open", mouth: str = "w",
               ring: float = 0) -> Image.Image:
    size, cx, gy = (50, 54), 25, 33
    c = Canvas(*size)
    wisp_body(c, cx, gy + bob, k, swell, eyes, mouth)
    out = c.outline(P.CC_LAVA_DD).img
    if ring:                                                                  # the burst: a ring of fire
        rr = ring
        ccy = gy - 6
        b = Canvas(*size)
        for i in range(28):
            a = i / 28 * math.tau
            x, y = cx + math.cos(a) * rr, ccy + math.sin(a) * rr * 0.9
            flame(b, x, y + 1.5, 4, 1.4, k + i, lean=math.cos(a) * 2)
        b.outline(P.CC_LAVA_DD)
        out.alpha_composite(see_through(b.img, 235))
    return out


def fire_wisp() -> Sprite:
    size, cx, gy = (50, 54), 25, 33
    sprite = Sprite("fire_wisp", size, faces_left=True, cx=cx, ground=gy)
    sprite.add("idle", [wisp_frame(0), wisp_frame(1, -1)], fps=6)
    sprite.add("move", [wisp_frame(k, (0, -1, -1, 0)[k]) for k in range(4)], fps=8)
    sprite.add("attack", [wisp_frame(0, swell=1.15, eyes="angry", mouth="flat"),
                          wisp_frame(1, swell=1.3, eyes="angry", mouth="open"),
                          wisp_frame(2, swell=1.1, eyes="angry", mouth="open", ring=12),
                          wisp_frame(3, swell=1.0, ring=19)], fps=10, loop=False)
    hurt = wisp_frame(1, eyes="shut", mouth="open")
    sprite.add("hit", hit_frames(hurt, [(cx - 9, gy - 18), (cx + 9, gy - 16), (cx + 7, gy - 3)]), fps=10, loop=False)
    still = wisp_frame(2, eyes="x", mouth="open")
    frames = [tint(still, P.WHITE, 0.6)]
    for i, t in enumerate((0.35, 0.65, 0.95)):                                # gutters out into embers
        f = vanish(still, t, depth=4, flash=False)
        e = Canvas(*size)
        embers(e, [(cx - 6 + i * 2, gy - 12 - i * 3), (cx + 5 - i, gy - 16 - i * 3), (cx + 1, gy - 6 - i * 4)])
        f.alpha_composite(see_through(e.img, int(255 * (1 - t * 0.6))))
        frames.append(f)
    sprite.add("death", frames, fps=10, loop=False)
    return sprite


# --- lingering hazards: lava_puddle [18x4], fire_ring [40x10] --------------------------------------

def lava_puddle() -> Sprite:
    """A glowing molten puddle, 20x6, bottom row on the ground: a crusted dark rim, orange lava, a yellow-hot
    middle and bubbles that swell and pop in turn."""
    w, h = 22, 8
    sprite = Sprite("lava_puddle", (w, h), ground=h - 1)
    frames = []
    for k in range(4):
        c = Canvas(w, h)
        c.ellipse(10.5, 5, 10, 2.6, P.CC_LAVA_D)
        c.rect(1, 5, 20, 7, P.CC_LAVA_D)
        c.ellipse(10.5, 5, 8.5, 1.8, P.LAVA)
        c.rect(3, 5, 18, 6, P.LAVA)
        c.ellipse(10.5 + (k % 2) - 0.5, 5, 5, 1, P.LAVA_L)
        c.rect(1, 7, 20, 7, P.CC_LAVA_DD)                                   # cooled crust at the edge
        for i, bx in enumerate((5, 10, 15)):                                # bubbles rising and popping
            stage = (k + i) % 4
            if stage == 1:
                c.px(bx, 4, P.CC_LAVA_W)
            elif stage == 2:
                c.rect(bx - 0.5, 3, bx + 0.5, 4, P.LAVA_L)
                c.px(bx, 3, P.CC_LAVA_W)
            elif stage == 3:
                c.px(bx - 1, 2, P.CC_EMBER)
                c.px(bx + 1, 1, P.LAVA)
        frames.append(c.outline(EDGE).img)
    sprite.add("burn", frames, fps=8)
    return sprite


def fire_ring() -> Sprite:
    """A ring of low flames on the ground seen from the side, about 42x12, bottom row on the ground: the far
    half burns lower and darker behind, the near half taller in front, over a glowing ring of embers."""
    w, h = 48, 16
    sprite = Sprite("fire_ring", (w, h), ground=h - 1)
    cx, cy, rx, ry = 23.5, 12.5, 18.5, 2.5
    frames = []
    for k in range(4):
        back, front = Canvas(w, h), Canvas(w, h)
        for i in range(14):
            a = i / 14 * math.tau + k * 0.12
            x, y = cx + math.cos(a) * rx, cy + math.sin(a) * ry
            near = math.sin(a) > 0
            flame(front if near else back, x, y + 1, (7.5 if near else 5) + (i + k) % 3 * 0.8, 1.8, k + i,
                  lean=math.cos(a) * 0.8)
        back.outline(P.CC_LAVA_DD)
        ring = Canvas(w, h)
        ring.ellipse(cx, cy, rx + 1, ry + 0.5, P.CC_LAVA_D)                # the burning ground under the ring
        ring.ellipse(cx, cy, rx - 1, ry - 0.8, (0, 0, 0, 0))
        out = Canvas(w, h)
        out.paste(ring)
        out.paste(see_through(back.img, 210))
        front.outline(P.CC_LAVA_DD)
        out.paste(front)
        frames.append(out.outline(EDGE).img)                                # dark edge so it reads on red
    sprite.add("burn", frames, fps=8)
    return sprite


def build() -> list[Sprite]:
    return [lava_slime(), lava_glob(), fire_imp(), fireball_shot(), stone_guard(), magma_blast(), hell_hound(), ember_bat(),
            flame_archer(), flame_arrow(), chainsaw_cat(), fire_wisp(), lava_puddle(), fire_ring()]
