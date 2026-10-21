"""The jump buttons: a cat paw on a round disc, in each state (docs/concept/Pixel Art Jump Button UI Sheet.png,
top row). 48x48, round, transparent outside. Every circle and the paw are computed per pixel about the centre
(24, 24), so each button is exactly symmetric and the paw is pixel-identical in every state (the pressed ones
shift it down 1 px). Also `paw_trail`, the gold burst under the cat on a double jump."""
from __future__ import annotations

import math

import palette as P
from draw import Canvas
from sprite import Sprite, single

SIZE = 48
C = 24.0                     # centre, between pixels 23 and 24
R_DISC, R_SEAM, R_RING, R_EDGE, R_GLOW = 17.5, 18.8, 21.3, 22.7, 24.0


def _lit(dx: float, dy: float) -> float:
    """1 facing the top-left light, -1 facing away."""
    d = math.hypot(dx, dy) or 1.0
    return -(dx + dy) / (d * math.sqrt(2))


def disc(c: Canvas, face, face_l, ring, ring_l, ring_d, glow=None, glint: bool = False) -> None:
    """The button body: optional glow, dark outline, a lit ring, a dark seam, and the disc with a lit crescent."""
    for y in range(SIZE):
        for x in range(SIZE):
            dx, dy = x + 0.5 - C, y + 0.5 - C
            d = math.hypot(dx, dy)
            lit = _lit(dx, dy)
            if d < R_DISC:
                colour = face_l if (lit > 0.5 and d > R_DISC - 4) else face
            elif d < R_SEAM:
                colour = P.OUTLINE
            elif d < R_RING:
                colour = ring_l if lit > 0.45 else ring_d if lit < -0.45 else ring
                if d < R_SEAM + 0.9 and lit > 0.2:
                    colour = ring_l
            elif d < R_EDGE:
                colour = P.OUTLINE
            elif glow and d < R_GLOW:
                colour = (*glow[:3], 170 if d < 23.3 else 80)
            else:
                continue
            c.px(x, y, colour)
    if glint:                                                # a white glint running round the top-left of the ring
        for k in range(7):
            a = math.radians(205 + k * 7)
            rr = (R_SEAM + R_RING) / 2
            c.px(C - 0.5 + math.cos(a) * rr, C - 0.5 + math.sin(a) * rr, P.WHITE if 1 < k < 5 else ring_l)


# The paw: one cream silhouette (main pad + four toes) with coral pads inside.
TOES = ((14.5, 20.5), (19.5, 14.5), (28.5, 14.5), (33.5, 20.5))


def _in_paw(x: float, y: float) -> bool:
    if ((x - C) / 9.6) ** 2 + ((y - 28.0) / 7.6) ** 2 <= 1:
        return True
    if ((x - C) / 10.2) ** 2 + ((y - 21.5) / 6.5) ** 2 <= 1:     # fills between the toes: one soft blob
        return True
    return any((x - tx) ** 2 + (y - ty) ** 2 <= 4.5 ** 2 for tx, ty in TOES)


def _in_pad(x: float, y: float) -> bool:
    if ((x - C) / 5.6) ** 2 + ((y - 29.6) / 3.8) ** 2 <= 1:
        return True
    return any((x - lx) ** 2 + (y - 27.4) ** 2 <= 2.8 ** 2 for lx in (C - 3, C + 3))


def _in_bean(x: float, y: float) -> bool:
    return any((x - tx) ** 2 + (y - ty - 0.5) ** 2 <= 2.9 ** 2 for tx, ty in TOES)


PAW_COLOURS = {"fur": P.FUR_WHITE, "fur_d": P.CREAM_D, "pad": P.PAD, "pad_l": P.PAD_L, "pad_d": P.PAD_D}
GREY_PAW = {"fur": P.BTN_PAW_GREY_L, "fur_d": P.BTN_PAW_GREY, "pad": P.BTN_PAD_GREY, "pad_l": P.BTN_PAD_GREY_L,
            "pad_d": P.BTN_GREY}


def paw(c: Canvas, cols: dict, dy: int = 0) -> None:
    """The paw print, with a soft shadow on the disc below it; `dy` shifts it down (pressed)."""
    shadow = Canvas(SIZE, SIZE)
    layer = Canvas(SIZE, SIZE)
    for y in range(SIZE):
        for x in range(SIZE):
            px, py = x + 0.5, y + 0.5 - dy
            if _in_paw(px, py - 2):
                shadow.px(x, y, (0, 0, 0, 70))
            if not _in_paw(px, py):
                continue
            pad = _in_pad(px, py) or _in_bean(px, py)
            if pad:
                up_left = _in_pad(px - 1, py - 1) or _in_bean(px - 1, py - 1)
                down = _in_pad(px + 0.7, py + 1) or _in_bean(px + 0.7, py + 1)
                colour = cols["pad_l"] if not up_left else cols["pad_d"] if not down else cols["pad"]
            else:
                rim = not _in_paw(px + 1, py + 1) or not _in_paw(px + 1.5, py + 1.5)
                colour = cols["fur_d"] if rim else cols["fur"]
            layer.px(x, y, colour)
    c.paste(shadow)
    c.paste(layer.outline())


SPARKLES = ((11, 13), (36, 11), (10, 32), (38, 31), (31, 40))


def sparkle(c: Canvas, x: int, y: int, size: int, colours=(P.WHITE, P.YELLOW, P.GOLD), alpha: int = 255) -> None:
    """A four-point twinkle: 0 none, 1 a dot, 2 a small cross, 3 a bigger one, 4 a flash with a white core."""
    core, mid, tip = ((*col[:3], alpha) for col in colours)
    if size <= 0:
        return
    c.px(x, y, core if size >= 2 else mid)
    arms = size - 1 if size < 3 else size
    for k in range(1, arms + 1):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c.px(x + dx * k, y + dy * k, mid if k < arms else tip)
    if size >= 3:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c.px(x + dx, y + dy, core)
    if size >= 4:
        for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            c.px(x + dx, y + dy, mid)


TWINKLE = (0, 1, 2, 4, 3, 1)   # one sparkle across the six frames: grows, flashes, fades


def button(face, face_l, ring, ring_l, ring_d, glow=None, cols=PAW_COLOURS, dy=0, sparkles=None, frame=0,
           bright=False) -> Canvas:
    c = Canvas(SIZE, SIZE)
    disc(c, face, face_l, ring, ring_l, ring_d, glow, glint=sparkles is not None and frame == 3)
    paw(c, cols, dy)
    if sparkles == "twinkle":
        for k, (x, y) in enumerate(SPARKLES):
            size = TWINKLE[(frame + k * 2 + k // 3) % 6] + (1 if bright and frame % 2 == k % 2 else 0)
            sparkle(c, x, y, min(size, 4), (P.WHITE, P.WHITE if bright else P.YELLOW, P.YELLOW if bright else P.GOLD))
    elif sparkles == "faint":
        for x, y in SPARKLES[:3]:
            sparkle(c, x, y, 2, (P.WHITE, P.GREY_L, P.GREY), alpha=150)
    return c


def paw_trail() -> Sprite:
    """A small burst of gold sparkles flying out and up, with motion streaks below, popped at the cat's feet."""
    sprite = Sprite("paw_trail", (16, 16))
    frames = []
    for t in range(5):
        c = Canvas(16, 16)
        for k, sx in enumerate((5, 8, 11)):                   # streaks falling away below
            top = 9 + t + (k % 2)
            length = max(0, 5 - t + (k == 1))
            for j in range(length):
                c.px(sx, top + j, (*(P.GOLD if j == 0 else P.GOLD_D)[:3], 230 - j * 40))
        for k, deg in enumerate((-150, -90, -30)):            # three sparkles flying out and up
            a = math.radians(deg)
            rad = 2 + t * 1.5
            x, y = 7.5 + math.cos(a) * rad, 9 + math.sin(a) * rad
            size = ((2, 3, 3, 2, 1) if k == 1 else (1, 2, 3, 2, 1))[t]
            sparkle(c, round(x), round(y), size, (P.WHITE, P.YELLOW, P.GOLD), alpha=255 if t < 4 else 160)
        for deg in (-120, -60):                               # and two specks between them
            a = math.radians(deg)
            rad = 3 + t * 1.8
            if t > 0:
                c.px(7.5 + math.cos(a) * rad * 1.2, 9 + math.sin(a) * rad, (*P.YELLOW[:3], 255 - t * 40))
        frames.append(c)
    sprite.add("burst", frames, fps=12, loop=False)
    return sprite


def build() -> list[Sprite]:
    jump = (P.BTN_NAVY, P.BTN_NAVY_L, P.BTN_BLUE, P.BTN_BLUE_L, P.BTN_BLUE_D)
    pressed = (P.BTN_PURPLE, P.BTN_PURPLE_L, P.BTN_PINK, P.BTN_PINK_L, P.BTN_PINK_D)
    slate = (P.BTN_SLATE, P.BTN_SLATE_L, P.BTN_GREY, P.BTN_GREY_L, P.BTN_GREY_D)
    amber = (P.BTN_AMBER, P.BTN_AMBER_L, P.GOLD, P.YELLOW, P.GOLD_D)
    magenta = (P.BTN_MAGENTA, P.BTN_MAGENTA_L, P.GOLD, P.YELLOW, P.BTN_PINK_D)

    double = Sprite("button_double", (SIZE, SIZE))
    double.add("sparkle", [button(*amber, sparkles="twinkle", frame=f) for f in range(6)], fps=8)
    double_pressed = Sprite("button_double_pressed", (SIZE, SIZE))
    double_pressed.add("sparkle", [button(*magenta, glow=P.BTN_GLOW_PINK, dy=1, sparkles="twinkle", frame=f, bright=True)
                                   for f in range(6)], fps=8)
    return [
        single("button_jump", button(*jump)),
        single("button_jump_pressed", button(*pressed, glow=P.BTN_GLOW, dy=1)),
        single("button_jump_disabled", button(*slate, cols=GREY_PAW)),
        double,
        double_pressed,
        single("button_double_disabled", button(*slate, cols=GREY_PAW, sparkles="faint")),
        paw_trail(),
    ]
