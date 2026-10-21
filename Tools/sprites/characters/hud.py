"""The in-game HUD, after docs/concept/Pixel Cat Platformer HUD Sprite Sheet.png: navy panels with a royal-blue
border (9-slice), the "LV" tab panel, glossy hearts and their lose/gain effects, the XP bar track and fill, and
the level-up arrows. The cat's head (`hud_cat`) is cut from the sheet by export.hud_cat(), not drawn here.

Panels are built from a mask by erosion: the outer ring is the dark outline, the next two the blue border (lit
where it faces up or left), then a dark inner line, then the navy fill. So the slice insets are exact."""
from __future__ import annotations

import math

import palette as P
from draw import Canvas, tint
from sprite import Sprite, single
from characters.buttons import sparkle

# --- panels --------------------------------------------------------------------------------------------


def rounded(w: int, h: int, x0: int, y0: int, x1: int, y1: int, r: float):
    """Mask test for a rounded rectangle covering pixels x0..x1-1, y0..y1-1 with corner radius r."""
    def inside(x: int, y: int) -> bool:
        px, py = x + 0.5, y + 0.5
        if not (x0 <= px <= x1 and y0 <= py <= y1):
            return False
        dx = max(x0 + r - px, 0, px - (x1 - r))
        dy = max(y0 + r - py, 0, py - (y1 - r))
        return dx * dx + dy * dy <= r * r
    return inside


def panel_from_mask(w: int, h: int, mask) -> Canvas:
    """Outline, 2 px blue border lit top-left, dark inner line, navy fill, all by erosion of `mask`."""
    depth = [[0] * w for _ in range(h)]
    cur = {(x, y) for y in range(h) for x in range(w) if mask(x, y)}
    level = 0
    while cur:
        level += 1
        for x, y in cur:
            depth[y][x] = level
        cur = {(x, y) for x, y in cur
               if all((nx, ny) in cur for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))}
    c = Canvas(w, h)
    for y in range(h):
        for x in range(w):
            d = depth[y][x]
            if d == 0:
                continue
            if d == 1:
                colour = P.OUTLINE
            elif d <= 3:
                def out(nx, ny):
                    return not (0 <= nx < w and 0 <= ny < h) or depth[ny][nx] == 0
                lit = out(x, y - d) or out(x - d, y)
                colour = P.BTN_BLUE_L if (lit and d == 2) else P.BTN_BLUE
                if not lit and (out(x, y + d) or out(x + d, y)) and d == 2:
                    colour = P.BTN_BLUE_D
            elif d == 4:
                colour = P.OUTLINE
            else:
                colour = P.BTN_NAVY
            c.px(x, y, colour)
    return c


PANEL = 24
PANEL_INSET = 6


def hud_panel() -> Sprite:
    return single("hud_panel", panel_from_mask(PANEL, PANEL, rounded(PANEL, PANEL, 0, 0, PANEL, PANEL, 4)))


TAB_W, TAB_H = 64, 32
TAB_TOP = 8            # the body's top edge; the tab rises above it on the left
TAB_LEFT_INSET, TAB_RIGHT_INSET = 50, 7


def hud_level_tab() -> Sprite:
    """The "LV" panel: a body with a raised tab on its top-left, the tab's right side sloping down into the body."""
    body = rounded(TAB_W, TAB_H, 0, TAB_TOP, TAB_W, TAB_H, 4)
    tab = rounded(TAB_W, TAB_H, 0, 0, 38, TAB_H, 4)

    def shoulder(x, y):
        # a 45-degree slope from the tab's top-right corner (x 38, y 0) down to the body's top (x 46, y 8)
        px, py = x + 0.5, y + 0.5
        return 35 <= px <= 46 and py >= px - 38 and y < TAB_H - 4

    def mask(x, y):
        return body(x, y) or tab(x, y) or shoulder(x, y)
    return single("hud_level_tab", panel_from_mask(TAB_W, TAB_H, mask))


# --- hearts --------------------------------------------------------------------------------------------

HEART_MASK = (
    "..111....111..",
    ".11111..11111.",
    "11111111111111",
    "11111111111111",
    "11111111111111",
    "11111111111111",
    ".111111111111.",
    "..1111111111..",
    "...11111111...",
    "....111111....",
    ".....1111.....",
    "......11......",
)
HW, HH = 16, 14
RED = (P.HEART_L, P.HEART, P.HEART_D)
DARK = (P.HEART_EMPTY_L, P.HEART_EMPTY, P.HEART_EMPTY_D)


def heart_canvas(left=RED, right=RED, shine: bool = True, ox: int = 0, oy: int = 0, size=(HW, HH)) -> Canvas:
    """The glossy heart at (ox, oy) in a canvas of `size`: lit top-left, shaded bottom-right, a white shine,
    a dark outline. `left`/`right` colour the two halves (a half heart is red left, dark right)."""
    c = Canvas(*size)
    cells = {(x, y) for y, row in enumerate(HEART_MASK) for x, ch in enumerate(row) if ch == "1"}
    for x, y in cells:
        ramp = left if x < 7 else right
        light, base, dark = ramp
        colour = base
        if (x + 1, y) not in cells or (x, y + 1) not in cells or (x + 1, y + 1) not in cells:
            colour = dark
        elif ((x - 1, y) not in cells or (x, y - 1) not in cells) and y < 7:
            colour = light
        c.px(ox + 1 + x, oy + 1 + y, colour)
    if left is not right:                                    # the split down the middle
        for y in range(2, 12):
            if (7, y) in cells:
                c.px(ox + 1 + 7, oy + 1 + y, right[2])
    if shine:
        for x, y in ((3, 2), (4, 2), (3, 3), (2, 3)):
            c.px(ox + x, oy + y + 1, P.WHITE)
        c.px(ox + 5, oy + 3, left[0])
    return c.outline()


def hearts() -> list[Sprite]:
    full = heart_canvas()
    half = heart_canvas(RED, DARK)
    empty = heart_canvas(DARK, DARK, shine=False)
    empty.px(3, 3, P.HEART_EMPTY_L)
    empty.px(4, 3, P.HEART_EMPTY_L)
    return [single("heart_full", full), single("heart_half", half), single("heart_empty", empty), heart_lose(),
            heart_gain()]


FX = (24, 22)          # effect frames; the heart sits at (4, 4) inside, so it lines up with a 16x14 heart


def heart_lose() -> Sprite:
    """The heart flashes, cracks down the middle, splits, and its halves fall away in pieces."""
    sprite = Sprite("heart_lose", FX)
    whole = heart_canvas(ox=4, oy=4, size=FX).img
    frames = [Canvas(*FX) for _ in range(5)]
    frames[0].paste(tint(whole, P.WHITE, 0.55))
    cracked = Canvas(*FX)
    cracked.paste(whole)
    for x, y in ((12, 5), (11, 7), (12, 9), (11, 11), (12, 13), (12, 15)):  # zig-zag crack
        cracked.px(x, y, P.OUTLINE)
        cracked.px(x + 1, y + 1, P.OUTLINE)
    frames[1] = cracked
    left = whole.crop((0, 0, 12, FX[1]))
    right = whole.crop((12, 0, FX[0], FX[1]))
    for i, (spread, drop, keep) in enumerate(((1, 0, 255), (2, 2, 210), (3, 4, 130)), start=2):
        f = Canvas(*FX)
        lcan, rcan = Canvas(*FX), Canvas(*FX)
        lcan.img.alpha_composite(left, (0, 0))
        rcan.img.alpha_composite(right, (12, 0))
        f.paste(lcan.img, -spread, drop)                      # the halves slide apart and drop
        f.paste(rcan.img, spread, drop + (i - 2))
        for k, (dx, dy) in enumerate(((-6, -4), (6, -5), (-8, 2), (8, 1))):   # chips flying out
            x, y = 12 + dx * (i - 1) * 0.5, 10 + dy * (i - 1) * 0.5 + (i - 2) ** 2
            f.px(x, y, P.HEART if k % 2 else P.HEART_L)
            f.px(x + 1, y, P.HEART_D)
        px = f.img.load()
        for y in range(FX[1]):
            for x in range(FX[0]):
                r_, g, b, a = px[x, y]
                if a:
                    px[x, y] = (r_, g, b, min(a, keep))
        frames[i] = f
    sprite.add("burst", frames, fps=12, loop=False)
    return sprite


def heart_gain() -> Sprite:
    """A heart with a pulsing gold glow round it and sparkles twinkling at its corners."""
    sprite = Sprite("heart_gain", FX)
    heart = heart_canvas(ox=4, oy=4, size=FX)
    cells = {(x, y) for x in range(FX[0]) for y in range(FX[1]) if heart.img.getpixel((x, y))[3]}
    frames = []
    for i in range(6):
        c = Canvas(*FX)
        pulse = (1, 2, 2, 1, 1, 2)[i]
        for x in range(FX[0]):                                # a glow halo hugging the outline
            for y in range(FX[1]):
                if (x, y) in cells:
                    continue
                near = min((abs(x - cx) + abs(y - cy) for cx, cy in cells
                            if abs(x - cx) <= 3 and abs(y - cy) <= 3), default=9)
                if near <= pulse:
                    c.px(x, y, (*P.YELLOW[:3], 170 if near == 1 else 90))
        c.paste(heart)
        for k, (sx, sy) in enumerate(((3, 3), (20, 2), (2, 17), (21, 16))):
            size = (0, 1, 2, 3, 2, 1)[(i + k * 2) % 6]
            sparkle(c, sx, sy, size, (P.WHITE, P.YELLOW, P.GOLD))
        frames.append(c)
    sprite.add("glow", frames, fps=10)
    return sprite


# --- XP bar ---------------------------------------------------------------------------------------------

BAR_W, BAR_H = 24, 10
BAR_INSET = 3            # 9-slice insets on every side; the fill area is x 2..21, y 2..7 (inside the light line)


def xp_bar_frame() -> Sprite:
    c = Canvas(BAR_W, BAR_H)
    outer = rounded(BAR_W, BAR_H, 0, 0, BAR_W, BAR_H, 2.5)
    inner = rounded(BAR_W, BAR_H, 1, 1, BAR_W - 1, BAR_H - 1, 2)
    track = rounded(BAR_W, BAR_H, 2, 2, BAR_W - 2, BAR_H - 2, 1.2)
    for y in range(BAR_H):
        for x in range(BAR_W):
            if track(x, y):
                c.px(x, y, P.HUD_TRACK)
            elif inner(x, y):
                c.px(x, y, P.HUD_TRACK_LINE)
            elif outer(x, y):
                c.px(x, y, P.OUTLINE)
    return single("xp_bar_frame", c)


def xp_bar_fill() -> Sprite:
    """A 1-px-wide slice of the yellow fill, 6 tall (the frame's track height): stretched sideways in code."""
    c = Canvas(1, 6)
    for y, colour in enumerate((P.HUD_FILL_YELLOW_L, P.HUD_FILL_YELLOW_L, P.HUD_FILL_YELLOW, P.HUD_FILL_YELLOW,
                                P.HUD_FILL_YELLOW, P.HUD_FILL_YELLOW_D)):
        c.px(0, y, colour)
    return single("xp_bar_fill", c)


# --- level up -------------------------------------------------------------------------------------------

LU_W, LU_H = 32, 28


def arrow(c: Canvas, x: float, y: float, alpha: int = 255) -> None:
    """A chunky gold up-arrow, its tip at (x, y), about 9 wide and 10 tall; outlined by the caller."""
    gold, light, dark = ((*col[:3], alpha) for col in (P.GOLD, P.YELLOW, P.GOLD_D))
    c.poly([(x, y), (x + 4.5, y + 5), (x - 4.5, y + 5)], gold)
    c.rect(x - 2, y + 5, x + 2, y + 9, gold)
    c.line((x - 1, y + 1), (x - 3.5, y + 4), light)
    c.rect(x - 2, y + 5, x - 1, y + 9, light)
    c.rect(x + 2, y + 5, x + 2, y + 9, dark)
    c.line((x + 1, y + 2), (x + 4, y + 5), dark)


def level_up_arrows() -> Sprite:
    """Two gold arrows rising, one a beat behind the other, with sparkles; they fade as they reach the top."""
    sprite = Sprite("level_up_arrows", (LU_W, LU_H))
    frames = []
    for i in range(6):
        c = Canvas(LU_W, LU_H)
        for k, (ax, lag) in enumerate(((9, 0), (23, 1))):
            t = max(0, i - lag)
            y = 16 - t * 3
            alpha = 255 if t < 4 else 150
            layer = Canvas(LU_W, LU_H)
            arrow(layer, ax, y, alpha)
            c.paste(layer.outline())
        for k, (sx, sy) in enumerate(((3, 20), (28, 18), (16, 6), (5, 8), (27, 4))):
            size = (0, 1, 2, 3, 2, 1)[(i + k * 2) % 6]
            sparkle(c, sx, sy, size, (P.WHITE, P.YELLOW, P.GOLD))
        frames.append(c)
    sprite.add("rise", frames, fps=10)
    return sprite


# --- boss HP bar (The Great Squirrel King sheet's middle bars; its banner and crown are cut image assets) ---

BOSS_W, BOSS_H = 40, 12
BOSS_INSET_X, BOSS_INSET_Y = 7, 4   # 9-slice insets; the fill area is x 7 to width-8, y 4-7 (4 rows)
CAP = 6                             # gold cap columns at each end (0-6 and width-7..width-1, inner line included)


def boss_bar_frame() -> Sprite:
    """A gold-and-wood frame: rounded gold end caps with a rivet, gold rims over wooden rails along the top and
    bottom, a dark line round a dark navy track."""
    w, h = BOSS_W, BOSS_H
    c = Canvas(w, h)
    outer = rounded(w, h, 0, 0, w, h, 4.5)
    rows = {1: P.GOLD, 2: P.PLANK, 3: P.OUTLINE, 4: P.HUD_TRACK, 5: P.HUD_TRACK, 6: P.HUD_TRACK, 7: P.HUD_TRACK,
            8: P.OUTLINE, 9: P.PLANK_D, 10: P.GOLD_D}
    for y in range(h):
        for x in range(w):
            if not outer(x, y):
                continue
            if not all(outer(nx, ny) for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))):
                c.px(x, y, P.OUTLINE)
                continue
            left_cap, right_cap = x <= CAP, x >= w - 1 - CAP
            if left_cap or right_cap:
                inner = (x == CAP or x == w - 1 - CAP) and 3 <= y <= 8
                if inner:
                    colour = P.OUTLINE
                elif y <= 2 or (left_cap and x <= 1):
                    colour = P.YELLOW                       # lit from the top-left
                elif y >= 9 or (right_cap and x >= w - 2):
                    colour = P.GOLD_D
                else:
                    colour = P.GOLD
                c.px(x, y, colour)
            else:
                c.px(x, y, rows.get(y, P.OUTLINE))
    c.rect(2, 1, CAP - 1, 1, P.YELLOW)
    for rx in (3, w - 5):                                   # rivets
        c.rect(rx, 5, rx + 1, 6, P.GOLD_D)
        c.px(rx, 5, P.YELLOW)
        c.px(rx + 1, 6, P.BROWN_D)
    for x in range(CAP + 3, w - CAP - 2, 9):                # wood grain on the rails
        c.px(x, 2, P.PLANK_D)
        c.px(x + 4, 9, P.BARK_D)
    return single("boss_bar_frame", c)


def fill_slice(name: str, colours) -> Sprite:
    c = Canvas(1, len(colours))
    for y, colour in enumerate(colours):
        c.px(0, y, colour)
    return single(name, c)


def boss_bars() -> list[Sprite]:
    return [
        boss_bar_frame(),
        fill_slice("boss_bar_fill", (P.HUD_FILL_RED_L, P.HUD_FILL_RED, P.HUD_FILL_RED, P.HUD_FILL_RED_D)),
        fill_slice("boss_bar_fill_low", (P.HUD_FILL_YELLOW_L, P.HUD_FILL_YELLOW, P.HUD_FILL_YELLOW,
                                         P.HUD_FILL_YELLOW_D)),
        fill_slice("boss_bar_flash", (P.WHITE, P.WHITE, P.WHITE, P.WHITE)),
    ]


def build() -> list[Sprite]:
    return [hud_panel(), hud_level_tab(), *hearts(), xp_bar_frame(), xp_bar_fill(), level_up_arrows(), *boss_bars()]
