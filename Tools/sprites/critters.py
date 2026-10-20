"""Small helpers for the cute forest critters: shaded layers, cat faces, cat ears and sparkles.

Every critter is built from a few parts. Each part is drawn flat in one base colour on its own layer;
`shaded` then lights the rim that faces the light (top-left, as in the scenery) and darkens the far rim,
optionally gives the part a dark inner outline, and lays it onto the canvas. The final `Canvas.outline()`
adds the 1px dark outline around the whole figure.
"""
from __future__ import annotations

from contextlib import contextmanager

import palette as P
from draw import Canvas

Ramp = dict  # base colour -> (light or None, dark or None)


def ramp(*triples) -> Ramp:
    """`ramp((light, base, dark), ...)`: which colour each base turns into at the lit and shaded rims."""
    return {base: (light, dark) for light, base, dark in triples}


def _shade(c: Canvas, rmp: Ramp, up: int, down: int, left: int, right: int) -> None:
    img = c.img
    box = img.getbbox()
    if box is None:
        return
    px = img.load()
    w, h = img.size

    def empty(x: int, y: int) -> bool:
        return not (0 <= x < w and 0 <= y < h) or px[x, y][3] == 0

    changes = []
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            colour = px[x, y]
            if colour[3] == 0 or colour not in rmp:
                continue
            light, dark = rmp[colour]
            if dark and (any(empty(x, y + k) for k in range(1, down + 1))
                         or any(empty(x + k, y) for k in range(1, right + 1))):
                changes.append((x, y, dark))
            elif light and (any(empty(x, y - k) for k in range(1, up + 1))
                            or any(empty(x - k, y) for k in range(1, left + 1))):
                changes.append((x, y, light))
    for x, y, colour in changes:
        px[x, y] = colour


@contextmanager
def shaded(c: Canvas, rmp: Ramp | None = None, edge=None, up: int = 1, down: int = 2, left: int = 1,
           right: int = 1):
    """`with shaded(c, ramp, edge) as p:` draw on `p`; on exit it is shaded, outlined and laid onto `c`."""
    layer = Canvas(*c.size)
    yield layer
    if rmp:
        _shade(layer, rmp, up, down, left, right)
    if edge:
        # The part's outline only lands on what is already drawn (an inner contour line); around the
        # silhouette the figure's final `Canvas.outline()` draws it, so the outer edge stays 1px.
        before = layer.img.getchannel("A").load()
        layer.outline(edge)
        under = c.img.getchannel("A").load()
        lp = layer.img.load()
        w, h = layer.size
        for y in range(h):
            for x in range(w):
                if lp[x, y][3] and not before[x, y] and not under[x, y]:
                    lp[x, y] = P.CLEAR
    c.paste(layer)


def ear(c: Canvas, x: float, y: float, h: float, fur, inner=P.PINK, lean: float = 0.0,
        half: float | None = None) -> None:
    """A pointed cat ear whose base is centred on (x, y), `h` px tall and `2 * half` wide at the base."""
    half = h * 0.55 if half is None else half
    c.poly([(x - half, y + 0.5), (x + lean, y - h), (x + half, y + 0.5)], fur)
    if h >= 3 and inner:
        c.poly([(x - half * 0.4, y), (x + lean * 0.8, y - h + 1.5), (x + half * 0.45, y)], inner)


def face(c: Canvas, x: float, y: float, eyes: str = "open", mouth: str = "w", gap: int = 4, eye=P.BLACK,
         shine=P.WHITE, blush=P.PINK, nose=P.PINK_D, mouth_colour=P.OUTLINE, size: int = 2) -> None:
    """A cute cat face seen three-quarters from the right. (x, y) is the top-left pixel of the near
    eye's `size` x `size` block (2 or 3); the far eye sits `gap` px to its left.

    eyes: open (black with a shine), wide (taller), shut (happy arcs), x (defeated), angry (slanted),
    glow (coloured `eye` with no pupil shine).
    mouth: w (:3), smile, open (a small O), fangs, flat.
    """
    s = size
    for ex in (x - gap, x):
        if eyes == "x":
            for dx, dy in ((0, 0), (2, 0), (1, 1), (0, 2), (2, 2)):   # a 3x3 cross
                c.px(ex + dx - (1 if ex != x and s == 2 else 0), y + dy - 0.5, eye)
        elif eyes == "shut":
            c.px(ex, y + 1, eye)
            c.px(ex + 1, y, eye)
            if ex == x or s == 3:
                c.px(ex + 2, y + 1, eye)
        elif eyes == "angry":
            c.rect(ex, y + 1, ex + s - 1, y + s - 1, eye)     # slanted down toward the nose
            c.px(ex if ex != x else ex + s - 1, y, eye)
        else:
            c.rect(ex, y, ex + s - 1, y + s - 1, eye)
            if eyes == "wide":
                c.rect(ex, y - 1, ex + s - 1, y - 1, eye)
            if eyes != "glow":
                c.px(ex + s - 1, y - (1 if eyes == "wide" else 0), shine)
                if s == 3:
                    c.px(ex, y + 2, P.GREY_D if eye == P.BLACK else eye)
    if blush:
        c.px(x - gap - 1, y + s, blush)
        c.px(x + s, y + s, blush)
        if s == 3:
            c.px(x - gap - 2, y + s, blush)
            c.px(x + s + 1, y + s, blush)
    mx = x - gap / 2 + (s - 1) / 2
    my = y + s + (1 if s == 3 else 0)                       # big eyes leave a row before the nose
    if nose:
        c.px(mx, my, nose)
    if mouth == "w":
        c.px(mx - 1, my + 1, mouth_colour)
        c.px(mx + 1, my + 1, mouth_colour)
        if s == 3:
            c.px(mx - 2, my, mouth_colour)
            c.px(mx + 2, my, mouth_colour)
    elif mouth == "smile":
        c.rect(mx - 1, my + 1, mx + 1, my + 1, mouth_colour)
        if s == 3:
            c.px(mx - 2, my, mouth_colour)
            c.px(mx + 2, my, mouth_colour)
    elif mouth == "open":
        c.rect(mx - 0.5, my + 1, mx + 0.5, my + (3 if s == 3 else 2), P.RED_D)
        if s == 3:
            c.px(mx, my + 3, P.PINK_D)
    elif mouth == "fangs":
        c.rect(mx - 1, my + 1, mx + 1, my + 1, mouth_colour)
        c.px(mx - 1, my + 2, P.WHITE)
        c.px(mx + 1, my + 2, P.WHITE)
    elif mouth == "flat":
        c.rect(mx - 0.5, my + 1, mx + 0.5, my + 1, mouth_colour)


def sparkle(c: Canvas, x: float, y: float, colour=P.YELLOW, centre=P.WHITE, big: bool = False) -> None:
    """A tiny four-point twinkle like the ones floating around the atlas creatures."""
    c.px(x, y, centre)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        c.px(x + dx, y + dy, colour)
    if big:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            c.px(x + dx, y + dy, colour)
