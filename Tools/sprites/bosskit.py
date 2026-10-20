"""Drawing helpers shared by the four world bosses and their hazards.

Big bosses read as volumes, not flat blobs: each body part is drawn on its own layer in one base colour,
then `part` lights its top-left rim, shades its bottom-right rim and gives it a darker inner outline before
it is laid over the parts behind it.
"""
from __future__ import annotations

import math
from typing import Callable

from PIL import Image

import palette as P
from draw import Canvas, noise, r, see_through

Ramp = dict  # base colour -> (light or None, dark or None)


def _bbox(img: Image.Image, pad: int) -> tuple[int, int, int, int] | None:
    box = img.getbbox()
    if box is None:
        return None
    return (max(0, box[0] - pad), max(0, box[1] - pad), min(img.width, box[2] + pad), min(img.height, box[3] + pad))


def shade(img: Image.Image, ramp: Ramp, up: int = 2, down: int = 3, left: int = 1, right: int = 2) -> None:
    """Rim-lights pixels near the layer's top/left edge and shades those near its bottom/right edge."""
    box = _bbox(img, 0)
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
            if colour[3] == 0 or colour not in ramp:
                continue
            light, dark = ramp[colour]
            if dark and (any(empty(x, y + k) for k in range(1, down + 1))
                         or any(empty(x + k, y) for k in range(1, right + 1))):
                changes.append((x, y, dark))
            elif light and (any(empty(x, y - k) for k in range(1, up + 1))
                            or any(empty(x - k, y) for k in range(1, left + 1))):
                changes.append((x, y, light))
    for x, y, colour in changes:
        px[x, y] = colour


def outline(img: Image.Image, colour, only_below: bool = False) -> None:
    """1px outline around a layer (cheaper than Canvas.outline: works inside the bounding box)."""
    box = _bbox(img, 1)
    if box is None:
        return
    px = img.load()
    w, h = img.size
    edge = []
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            if px[x, y][3]:
                continue
            around = ((x, y - 1),) if only_below else ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
            if any(0 <= nx < w and 0 <= ny < h and px[nx, ny][3] for nx, ny in around):
                edge.append((x, y))
    for x, y in edge:
        px[x, y] = colour


class part:
    """`with part(c, ramp, edge) as p:` draw on `p`; on exit it is shaded, outlined and laid onto `c`."""

    def __init__(self, dst: Canvas, ramp: Ramp | None = None, edge=None, up: int = 2, down: int = 3,
                 left: int = 1, right: int = 2, alpha: int | None = None, ramp2: Ramp | None = None):
        self.dst, self.ramp, self.edge = dst, ramp or {}, edge
        self.args = (up, down, left, right)
        self.alpha = alpha
        self.ramp2 = ramp2   # a second, narrower ramp applied on top: deeper shade right at the rim

    def __enter__(self) -> Canvas:
        self.layer = Canvas(*self.dst.size)
        return self.layer

    def __exit__(self, *exc) -> None:
        img = self.layer.img
        if self.ramp:
            shade(img, self.ramp, *self.args)
        if self.ramp2:
            up, down, left, right = self.args
            shade(img, self.ramp2, max(1, up // 2), max(1, down // 2), max(1, left // 2), max(1, right // 2))
        if self.edge:
            outline(img, self.edge)
        if self.alpha is not None:
            img = see_through(img, self.alpha)
        self.dst.paste(img)


def blob(c: Canvas, x: float, y: float, rx: float, ry: float, colour, seed: int, tufts: int = 12,
         size: float = 2.5) -> None:
    """An ellipse with a tufted, furry edge."""
    c.ellipse(x, y, rx, ry, colour)
    rnd = noise(seed)
    for k in range(tufts):
        a = k / tufts * math.tau + rnd() * 0.4
        rad = size * (0.6 + rnd() * 0.6)
        c.ellipse(x + math.cos(a) * (rx - rad * 0.5), y + math.sin(a) * (ry - rad * 0.5), rad, rad, colour)


def tube(c: Canvas, points: list[tuple[float, float, float]], colour) -> None:
    """Overlapping discs along (x, y, radius) points, interpolated so there are no gaps."""
    for (x0, y0, r0), (x1, y1, r1) in zip(points, points[1:]):
        steps = max(1, r(math.hypot(x1 - x0, y1 - y0) / 1.5))
        for i in range(steps + 1):
            t = i / steps
            rad = r0 + (r1 - r0) * t
            c.ellipse(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, rad, rad, colour)


def bezier(points: list[tuple[float, ...]], n: int) -> list[tuple[float, ...]]:
    """`n` samples along a Bezier curve through control points of any dimension (x, y, radius...)."""
    out = []
    for i in range(n):
        t = i / (n - 1)
        pts = [list(p) for p in points]
        while len(pts) > 1:
            pts = [[a + (b - a) * t for a, b in zip(p, q)] for p, q in zip(pts, pts[1:])]
        out.append(tuple(pts[0]))
    return out


def fur(c: Canvas, box: tuple[float, float, float, float], on, colour, seed: int, count: int,
        length: int = 3) -> None:
    """Short strokes of `colour` over pixels of `on` inside `box`: fur texture."""
    rnd = noise(seed)
    px = c.img.load()
    w, h = c.size
    for _ in range(count):
        x, y = box[0] + rnd() * (box[2] - box[0]), box[1] + rnd() * (box[3] - box[1])
        dx = (rnd() - 0.5) * 2
        for k in range(length):
            xx, yy = r(x + dx * k * 0.5), r(y + k)
            if 0 <= xx < w and 0 <= yy < h and px[xx, yy] == on:
                px[xx, yy] = colour


def halo(image: Image.Image, colours: list, alpha: int = 120) -> Image.Image:
    """A soft glow: rings of the given colours (inner first) around the figure, see-through, under it."""
    c = Canvas(*image.size)
    c.paste(image)
    rings = Image.new("RGBA", image.size, P.CLEAR)
    for k, colour in enumerate(colours):
        before = c.img.copy()
        outline(c.img, colour)
        ring = Image.new("RGBA", image.size, P.CLEAR)
        ring.paste(c.img, mask=Image.eval(before.getchannel("A"), lambda a: 0 if a else 255))
        rings.alpha_composite(see_through(ring, max(30, alpha - k * 30)))
    out = Image.new("RGBA", image.size, P.CLEAR)
    out.alpha_composite(rings)
    out.alpha_composite(image)
    return out


def flame(c: Canvas, x: float, bottom: float, height: float, width: float, step: int, seed: int,
          colours=(P.RED, P.LAVA, P.LAVA_L, P.YELLOW)) -> None:
    """A licking flame tongue standing on `bottom`; `step` animates the flicker."""
    rnd = noise(seed * 31 + step)
    for k, colour in enumerate(colours):
        scale = 1 - k * 0.24
        hh, ww = height * scale, width * scale
        sway = (rnd() - 0.5) * width * 0.6
        c.poly([(x - ww, bottom), (x - ww * 0.7, bottom - hh * 0.45), (x + sway, bottom - hh),
                (x + ww * 0.7, bottom - hh * 0.5), (x + ww, bottom)], colour)
        c.ellipse(x, bottom - ww * 0.6, ww, ww * 0.7, colour)


def flame_jet(c: Canvas, start: tuple[float, float], length: float, spread: float, step: int, seed: int,
              colours=(P.RED, P.LAVA, P.LAVA_L, P.YELLOW), droop: float = 0.0) -> None:
    """A jet of fire (or frost) blasting to the right from `start`, widening and billowing at the end."""
    rnd = noise(seed + step * 7)
    x0, y0 = start
    puffs = []
    n = max(6, int(length / 1.5))
    for k in range(n):
        t = k / (n - 1)
        rad = 1.5 + spread * t * (0.6 + rnd() * 0.5)
        x = min(x0 + t * length, c.size[0] - 3 - rad)        # billows up against the frame edge, never past it
        y = y0 + droop * t * t + (rnd() - 0.5) * spread * t
        puffs.append((x, y, rad))
    for k, colour in enumerate(colours):
        scale = 1 - k * 0.22
        for x, y, rad in puffs:
            c.ellipse(x - k * 1.5, y, max(0.6, rad * scale), max(0.6, rad * scale * 0.85), colour)


def smoke(c: Canvas, cx: float, cy: float, width: float, height: float, seed: int, colours, count: int = 10) -> None:
    rnd = noise(seed)
    for _ in range(count):
        x = cx + (rnd() - 0.5) * width
        y = cy + (rnd() - 0.5) * height
        rad = 2 + rnd() * min(width, height) * 0.25
        c.ellipse(x, y, rad, rad * 0.8, colours[int(rnd() * len(colours)) % len(colours)])


def crystal(c: Canvas, base: tuple[float, float], tip: tuple[float, float], width: float,
            light=P.ICE_L, mid=P.CYAN, dark=P.BLUE, shine=P.WHITE) -> None:
    """A faceted ice crystal from `base` to `tip`: light face, dark face and a glint."""
    bx, by = base
    tx, ty = tip
    dx, dy = tx - bx, ty - by
    n = math.hypot(dx, dy) or 1
    nx, ny = -dy / n * width, dx / n * width
    mid_pt = (bx + dx * 0.3, by + dy * 0.3)
    c.poly([(bx, by), (mid_pt[0] + nx, mid_pt[1] + ny), (tx, ty), (mid_pt[0] - nx, mid_pt[1] - ny)], mid)
    c.poly([(bx, by), (mid_pt[0] - nx, mid_pt[1] - ny), (tx, ty)], light)
    c.poly([(bx + dx * 0.15, by + dy * 0.15), (mid_pt[0] + nx, mid_pt[1] + ny), (tx, ty)], dark)
    c.line((bx + dx * 0.2, by + dy * 0.2), (bx + dx * 0.7, by + dy * 0.7), shine)


def acorn(c: Canvas, x: float, y: float, s: float, gold: bool = False, angle: float = 0.0) -> None:
    """An acorn centred on (x, y), `s` = 1 is about 10x12. Glossy brown nut, crosshatched cap, stem."""
    nut, nut_l, nut_d = (P.GOLD, P.YELLOW, P.GOLD_D) if gold else (P.SQ_FUR, P.SQ_FUR_L, P.SQ_FUR_D)
    cap, cap_d = (P.BROWN, P.BROWN_D)
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))

    def at(dx: float, dy: float) -> tuple[float, float]:
        return (x + dx * ca - dy * sa, y + dx * sa + dy * ca)

    body = [at(math.cos(a) * 4.5 * s, 1.2 * s + math.sin(a) * (4.6 if math.sin(a) > 0 else 3.6) * s)
            for a in [k / 16 * math.tau for k in range(16)]]
    c.poly(body, nut)
    c.poly([at(-3.5 * s, 2 * s), at(-1 * s, 4.5 * s), at(-2.6 * s, 4 * s)], nut_d)
    c.poly([at(1.5 * s, 4.6 * s), at(3.8 * s, 1.5 * s), at(4.3 * s, 0.2 * s), at(3.4 * s, 3 * s)], nut_d)
    c.poly([at(-2.6 * s, -0.5 * s), at(-1.6 * s, -1 * s), at(-1.2 * s, 2 * s), at(-2.2 * s, 2.6 * s)], nut_l)
    c.poly([at(0, 6.6 * s), at(-0.8 * s, 5.6 * s), at(0.8 * s, 5.6 * s)], nut_d)            # point
    capshape = [at(math.cos(a) * 5.6 * s, -1.6 * s + math.sin(a) * 3 * s) for a in
                [math.pi + k / 10 * math.pi for k in range(11)]]
    capshape += [at(5.4 * s, -0.6 * s), at(-5.4 * s, -0.6 * s)]
    c.poly(capshape, cap)
    c.line(at(-5 * s, -0.8 * s), at(5 * s, -0.8 * s), cap_d, max(1, r(s * 0.8)))
    if s >= 1.4:
        for k in range(-2, 3):                                                         # cap texture
            c.px(*at(k * 2 * s, -2.6 * s), cap_d)
            c.px(*at(k * 2 * s + s, -3.6 * s), P.BROWN_L)
    c.line(at(0, -4.4 * s), at(0.8 * s, -6.4 * s), cap_d, max(1, r(s * 0.7)))       # stem
