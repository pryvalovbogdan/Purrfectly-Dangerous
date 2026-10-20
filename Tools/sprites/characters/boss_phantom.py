"""World 3 boss: a translucent royal cat in a cloak of purple smoke, a crown floating above her head
(84x126; about 90 tall). Summons ghost cats, teleports, and splits into copies (only the glowing one
can be hurt)."""
from __future__ import annotations

import math
from dataclasses import dataclass

from PIL import Image

import palette as P
from draw import Canvas, _paste_clipped, noise, r, see_through, tint
from sprite import Sprite

SIZE = (84, 126)
CX, GROUND = 40, 122


@dataclass
class PhantomPose:
    bob: float = 0
    wave: float = 0            # phase of the smoke hem
    paws: float = 0            # 0 folded ... 1 raised high (casting)
    eye: str = "open"          # open | shut | x
    mouth: bool = False
    crown_dy: float = 0
    orbs: int = 0              # spirit orbs circling (summon)
    orb_phase: float = 0


def crown(c: Canvas, x: float, y: float) -> None:
    """A floating crown, 16 wide, centred on x with its band's bottom at y."""
    c.rect(x - 8, y - 4, x + 7, y, P.GOLD)
    for k, h in enumerate((5, 8, 5)):
        px = x - 7 + k * 6.5
        c.poly([(px - 1.5, y - 3), (px + 1, y - 3 - h), (px + 3.5, y - 3)], P.GOLD)
        c.ellipse(px + 1, y - 3 - h, 1, 1, P.VIOLET)
    c.rect(x - 8, y - 1, x + 7, y, P.GOLD_D)
    c.rect(x - 1, y - 3, x + 0, y - 2, P.SPIRIT)
    c.rect(x - 6, y - 3, x - 5, y - 2, P.VIOLET)
    c.rect(x + 4, y - 3, x + 5, y - 2, P.VIOLET)


def phantom(pose: PhantomPose) -> Image.Image:
    c = Canvas(*SIZE)
    x = CX
    base = GROUND - 4 + pose.bob                      # the smoke hem floats above the ground
    top = base - 60

    # Ghostly tail curling out from behind the cloak.
    for k in range(14):
        t = k / 13
        tx = x - 18 - t * 12 + math.sin(t * 4 + pose.wave) * 2
        ty = top + 30 - t * 30 + math.cos(t * 3) * 2
        c.ellipse(tx, ty, 2.2 - t * 0.6, 2.2 - t * 0.6, P.LILAC_D if k % 4 else P.VIOLET)

    # Smoke cloak: a bell of overlapping puffs, darker toward the hem, curling at the bottom.
    rnd = noise(400)
    for k in range(10):
        t = k / 9
        width = 9 + t * 17
        y = top + t * 56
        for j in range(5):
            u = j / 4 - 0.5
            px = x + u * width * 1.6 + math.sin(t * 5 + pose.wave + j) * 1.5 * t - t * 2
            rad = 6 + t * 3 + rnd() * 2
            c.ellipse(px, y, rad, rad * 0.8, (P.PURPLE, P.PURPLE, P.PURPLE_D, P.INDIGO)[min(3, int(t * 3.5))])
    for k in range(6):                                 # wisps trailing off the hem
        wx = x - 26 + k * 10
        wy = base + math.sin(pose.wave + k * 1.3) * 2
        c.ellipse(wx, wy, 4, 2.5, P.INDIGO)
        c.ellipse(wx - 3, wy + 2, 2, 1.5, P.PURPLE_D)
    for k in range(4):                                 # light catching the folds
        fx = x - 8 + k * 6
        c.line((fx, top + 14), (fx - 2 + k, top + 44), P.VIOLET)
    c.ellipse(x + 2, top + 8, 14, 5, P.VIOLET)          # shoulders of the cloak
    c.ellipse(x + 2, top + 7, 11, 3, P.PURPLE_L)

    # Paws: ghostly forelegs reaching up out of the cloak when she casts.
    for side, dx in ((0, 6), (1, -4)):
        a = math.radians(30 + pose.paws * 120 - side * 15)
        sx, sy = x + dx, top + 12
        ex, ey = sx + math.sin(a) * 13, sy + math.cos(a) * 13
        c.line((sx, sy), (ex, ey), P.LILAC if side == 0 else P.LILAC_D, 4)
        c.ellipse(ex, ey, 2.5, 2.5, P.WHITE if side == 0 else P.LILAC)

    # Head.
    hx, hy = x + 4, top - 6
    c.ellipse(hx, hy + 9, 9, 3, P.WHITE)               # white ruff
    for ex, tip in ((hx - 7, -3), (hx + 4, 2)):
        c.poly([(ex - 3.5, hy - 5), (ex + tip / 2, hy - 18), (ex + 4, hy - 6)], P.LILAC)
        c.poly([(ex - 1.5, hy - 6), (ex + tip / 2, hy - 14), (ex + 2, hy - 6)], P.PINK)
    c.ellipse(hx, hy, 12, 10, P.LILAC)
    c.ellipse(hx + 1, hy + 3, 12, 7, P.LILAC)
    c.ellipse(hx + 5, hy + 5, 5, 3.5, P.WHITE)          # muzzle
    c.rect(hx + 7, hy + 2, hx + 8, hy + 3, P.PINK_D)
    for k in (-1, 1):                                    # whiskers
        c.line((hx + 9, hy + 5 + k), (hx + 17, hy + 4 + k * 3), P.WHITE)
    if pose.mouth:
        c.rect(hx + 4, hy + 7, hx + 7, hy + 8, P.PURPLE_D)
        c.px(hx + 5, hy + 8, P.WHITE)
    else:
        c.line((hx + 3, hy + 7), (hx + 7, hy + 7), P.PURPLE_D)
    for k in range(3):                                   # pale stripes on the brow
        c.line((hx - 4 + k * 3, hy - 9), (hx - 4 + k * 3, hy - 6), P.LILAC_D)
    for ex in (hx - 4, hx + 4):
        if pose.eye == "open":
            c.ellipse(ex, hy - 1, 2.5, 2.5, P.YELLOW)
            c.rect(ex, hy - 3, ex, hy + 1, P.NIGHT)       # slit pupil
            c.px(ex - 1, hy - 2, P.WHITE)
        elif pose.eye == "shut":
            c.line((ex - 2, hy), (ex + 2, hy - 1), P.NIGHT)
        else:
            c.line((ex - 2, hy - 2), (ex + 2, hy + 2), P.NIGHT)
            c.line((ex - 2, hy + 2), (ex + 2, hy - 2), P.NIGHT)

    crown(c, hx, hy - 19 + pose.crown_dy + math.sin(pose.wave) * 1.5)

    for k in range(pose.orbs):                           # spirit orbs circling her
        a = pose.orb_phase + k * math.tau / max(pose.orbs, 1)
        ox, oy = x + math.cos(a) * 30, top + 20 + math.sin(a) * 10
        c.ellipse(ox, oy, 3, 3, P.SPIRIT)
        c.px(ox - 1, oy - 1, P.WHITE)
    c.outline(P.NIGHT)
    # See-through, and thinner toward the smoky hem.
    out = see_through(c.img, 225)
    px = out.load()
    for y in range(out.height):
        fade = max(0.0, (y - (base - 14)) / 18)
        if fade <= 0:
            continue
        for xx in range(out.width):
            pr, pg, pb, pa = px[xx, y]
            if pa:
                px[xx, y] = (pr, pg, pb, r(pa * max(0.25, 1 - fade)))
    return out


def glow(image: Image.Image, colour, width: int = 2) -> Image.Image:
    """A soft halo around the figure (for the copy that can be hit)."""
    c = Canvas(*image.size)
    c.paste(image)
    for k in range(width):
        c.outline(colour)
    out = Image.new("RGBA", image.size, P.CLEAR)
    out.alpha_composite(see_through(c.img, 140))
    out.alpha_composite(image)
    return out


def build() -> list[Sprite]:
    boss = Sprite("boss_phantom", SIZE, faces_left=True, cx=CX, ground=GROUND)
    boss.add("idle", [phantom(PhantomPose(bob=b, wave=k * math.pi / 2, eye="shut" if k == 3 else "open"))
                      for k, b in enumerate((0, -1, -2, -1))], fps=5)

    boss.add("summon", [phantom(PhantomPose(bob=-k % 2, wave=k, paws=min(1, k / 2), mouth=k >= 2, orbs=min(k, 3),
                                            orb_phase=k * 0.9, crown_dy=-min(k, 2)))
                        for k in range(6)], fps=8, loop=False)

    # Melts into smoke and gathers again somewhere else.
    whole = phantom(PhantomPose(paws=0.4))
    teleport = [whole]
    for k, (keep, squash) in enumerate(((150, 0.75), (80, 0.45), (40, 0.25), (110, 0.6), (190, 0.9))):
        squashed = whole.resize((SIZE[0], max(1, r(SIZE[1] * squash))), Image.NEAREST)
        frame = Image.new("RGBA", SIZE, P.CLEAR)
        frame.alpha_composite(see_through(squashed, keep), (0, GROUND + 1 - squashed.height))
        smoke = Canvas(*SIZE)
        rnd = noise(420 + k)
        for _ in range(10):
            smoke.ellipse(CX - 24 + rnd() * 48, GROUND - 10 - rnd() * 40 * (1 - squash), 3 + rnd() * 3, 2.5,
                          P.PURPLE if rnd() > 0.5 else P.VIOLET)
        frame.alpha_composite(see_through(smoke.img, 160))
        teleport.append(frame)
    boss.add("teleport", teleport, fps=10, loop=False)

    boss.add("split", [glow(phantom(PhantomPose(bob=b, wave=k * math.pi / 2, paws=0.3)), P.SPIRIT, 1 + k % 2)
                       for k, b in enumerate((0, -1, -2, -1))], fps=6)

    hurt = phantom(PhantomPose(eye="shut", mouth=True, crown_dy=-3, paws=0.6))
    boss.add("hurt", [tint(hurt, P.WHITE, 0.8), hurt], fps=10)

    frames = []
    for k in range(8):
        t = k / 7
        body = phantom(PhantomPose(eye="x", mouth=True, crown_dy=-t * 6, paws=0.8, wave=k))
        rising = Image.new("RGBA", SIZE, P.CLEAR)
        _paste_clipped(rising, body, 0, -r(t * 14))
        faded = see_through(rising, r(255 * (1 - t))) if k else tint(rising, P.WHITE, 0.7)
        frames.append(faded)
    boss.add("death", frames, fps=8, loop=False)
    return [boss]
