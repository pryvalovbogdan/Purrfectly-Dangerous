"""Boss and projectile frames cut from a user's painted sheet instead of drawn in code.

The boss counterpart of `sheet_hero.py` (which cuts the heroes; this module copies the ideas, not the code,
so either can change on its own). A boss sheet is a painting on a baked-in light checkerboard, one row
per animation. Each frame is given as a cell (a box in the sheet holding that frame only). For each cell:

1. `Cut.background` says which RGB pixels are checkerboard or ground shadow. A flood fill from the cell's
   border through those pixels clears what lies around the figure; the figure's dark outline stops it,
   so cream fur inside stays. Pockets the fill cannot reach (a gap between the legs closed off by a tail,
   checker inside the antlers) are cleared when they are mostly the checkerboard's grey squares.
   Projectiles have no dark outline, so they use `glow=True` instead: the figure is every coloured
   (not neutral) pixel, closed by a few pixels, plus the holes it encloses that are not mostly checkerboard
   grey (the white core of a crescent or a blossom).
2. The figure is the largest connected shape in the cell; `keep_all` also keeps every other shape of at
   least `min_bits` pixels (a pile of petals, spirits beside the fox), and `cleared` boxes are wiped by
   hand (a label pill, a loose petal that touches).
3. `place` scales a whole animation set by ONE factor and stands each figure on the ground row with its
   anchor (a sheet x per frame, usually the chest) on the sprite's `cx`; `fit` sizes a projectile into
   its small frame. Both downscale with LANCZOS (premultiplied by Pillow) and put the alpha back to hard
   0/255, so no glow halo shows on dark backgrounds.

Everything is plain arithmetic on the PNG, so the output is identical on every run.
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Callable

from PIL import Image, ImageChops, ImageFilter

HERE = Path(__file__).resolve().parent


def checkerboard(p: tuple) -> bool:
    """The light grey/white checkerboard baked into the user's boss sheets (a touch noisy), the blue-grey ground
    shadows and pale pink glow over the checkerboard. The figure's dark outline keeps the flood fill that uses
    this away from cream fur, a cream belly or white blossoms inside it."""
    r, g, b = p
    checker = max(p) - min(p) <= 14 and min(p) >= 180
    shadow = b >= g >= r - 4 and b - r <= 90 and max(p) >= 60
    haze = min(p) >= 185 and max(p) - min(p) <= 32 and b >= g - 2
    return checker or shadow or haze


@dataclass(frozen=True)
class Cut:
    """How one cell of the sheet is cut out."""
    box: tuple[int, int, int, int]          # x0, y0, x1, y1 in sheet pixels
    keep_all: bool = False                  # keep every shape of `min_bits`+ pixels, not just the largest
    min_bits: int = 30
    # Wiped by hand: sheet boxes (x0, y0, x1, y1), ellipses ("o", x, y, rx, ry) and boxes but for an ellipse
    # ("x", x0, y0, x1, y1, x, y, rx, ry: rounds off an end), everything left or right of a polyline
    # ("l" or "r", ((x, y), ...) from top to bottom; above and below it, straight up and down), e.g. a label pill, a summoned spirit joined to the
    # fox by glow, a tongue running into the next frame; what that leaves unconnected drops with loose petals.
    cleared: tuple = ()
    glow: bool = False                      # an effect with no dark outline (projectiles): see module doc
    close: int = 2                          # for `glow`: how far (sheet px) coloured strokes are joined
    chroma: int = 34                        # for `glow`: the least colourfulness that counts as the effect
    # Strands up to about 2×`thin` sheet pixels wide (glow wisps, petal chains reaching a neighbouring frame)
    # are cut off where they leave the figure: an opening (erode, grow back a little, keep what it covers).
    thin: int = 0
    alpha: int | None = None                # on a sheet with real transparency: this cell's own `BossSheet.alpha`
    core: int | None = None                 # and its own `BossSheet.core`
    # Figures that overlap their neighbours (lanterns crossing into the next frame): (own seed, neighbours' seeds,
    # half width), a seed being (centre x, ((x, y), ...) more points). Each figure grows from the core pixels within
    # `half width` of its centre (but 20 px clear of another figure's points) and within 6 px of its own points, all at once; see `cells(seeds=...)`.
    seeds: tuple | None = None


@dataclass
class Piece:
    """One cut-out figure at sheet resolution: opaque where kept, clear elsewhere."""
    image: Image.Image
    box: tuple[int, int, int, int]          # where it was in the sheet
    edge: int = 0                           # kept pixels on the cell's border (0 unless cut off)


@dataclass
class BossSheet:
    source: str                             # PNG next to this file
    background: Callable[[tuple], bool] = checkerboard   # checkerboard and ground-shadow pixels
    pocket_grey: int = 222                  # the checkerboard's grey squares are no lighter than this
    # A sheet with real transparency (the haze semi-transparent, the figure nearly opaque): a pixel belongs to the
    # figure when its painted alpha is at least `alpha` (no checkerboard rules). The figure is found among the
    # pixels of at least `core` alpha, where neighbours whose soft edges touch are still apart, then grown back out
    # over the pixels at `alpha` it touches.
    alpha: int | None = None
    core: int | None = None

    @cached_property
    def sheet(self) -> Image.Image:
        return Image.open(HERE / self.source).convert("RGBA" if self.alpha is not None else "RGB")

    def cut(self, cut: Cut) -> Piece:
        crop = self.sheet.crop(cut.box)
        w, h = crop.size
        px = crop.load()
        rgb = [[px[x, y][:3] for y in range(h)] for x in range(w)]
        seed = None
        if self.alpha is not None:
            level = cut.alpha if cut.alpha is not None else self.alpha
            keep = [[px[x, y][3] >= level for y in range(h)] for x in range(w)]
            if (cut.core or self.core) is not None:
                core = max(cut.core or self.core, level)
                seed = [[px[x, y][3] >= core for y in range(h)] for x in range(w)]
        else:
            keep = self._glow(rgb, cut) if cut.glow else self._unchecker(rgb, cut)
        if cut.thin:
            mask = Image.frombytes("L", (w, h), bytes(255 if keep[x][y] else 0 for y in range(h) for x in range(w)))
            body = mask.filter(ImageFilter.MinFilter(2 * cut.thin + 1)).filter(ImageFilter.MaxFilter(2 * cut.thin + 3))
            b = body.load()
            keep = [[keep[x][y] and b[x, y] > 0 for y in range(h)] for x in range(w)]
        for area in cut.cleared:
            if len(area) == 4:                                   # a box: x0, y0, x1, y1
                cx0, cy0, cx1, cy1 = area
                inside = lambda x, y: cx0 <= x < cx1 and cy0 <= y < cy1
            elif area[0] == "o":                                 # an ellipse: "o", centre x, y, radii x, y
                _, ex, ey, rx, ry = area
                inside = lambda x, y: ((x - ex) / rx) ** 2 + ((y - ey) / ry) ** 2 <= 1
            elif area[0] in ("l", "r"):  # left or right of a polyline ((x, y), ...) running down the sheet
                side, points = area[0], area[1]
                inside = lambda x, y, side=side, points=points: (x < _line_x(points, y)) == (side == "l")
            else:                       # a box but an ellipse in it: "x", x0, y0, x1, y1, centre x, y, radii x, y
                _, bx0, by0, bx1, by1, ex, ey, rx, ry = area
                inside = lambda x, y: (bx0 <= x < bx1 and by0 <= y < by1
                                       and ((x - ex) / rx) ** 2 + ((y - ey) / ry) ** 2 > 1)
            for x in range(w):
                for y in range(h):
                    if keep[x][y] and inside(x + cut.box[0], y + cut.box[1]):
                        keep[x][y] = False
                        if seed is not None:
                            seed[x][y] = False
        if seed is not None and cut.seeds is not None:
            own, others, half = cut.seeds
            x0, y0 = cut.box[:2]

            claimed = [pt for _, points in (own, *others) for pt in points]

            def start(c, points):
                # The seed: the core pixels in a band round the figure's centre, but not round a point another
                # figure claims (its spat lantern over this one's side); plus the figure's own points.
                mine = lambda x, y, r: any((x + x0 - px) ** 2 + (y + y0 - py) ** 2 <= r * r for px, py in points)
                near = lambda x, y: (mine(x, y, 6) or (abs(x + x0 - c) <= half and not any(
                    (x + x0 - px) ** 2 + (y + y0 - py) ** 2 <= 400 for px, py in claimed if (px, py) not in points)))
                return [(x, y) for x in range(w) for y in range(h) if keep[x][y] and seed[x][y] and near(x, y)]
            starts = [start(c, points) for c, points in (own, *others)]
            # A watershed: the painting's darkness is the height (the dark outlines are ridges), and every figure
            # floods from its seed at once, lowest first, so where two figures touch the border between them
            # follows their outlines rather than a straight line.
            height = [[255 - (299 * rgb[x][y][0] + 587 * rgb[x][y][1] + 114 * rgb[x][y][2]) // 1000
                       for y in range(h)] for x in range(w)]
            owner = [[-1] * h for _ in range(w)]
            queue, order = [], 0
            for i, start in enumerate(starts):
                for x, y in start:
                    if owner[x][y] < 0:
                        owner[x][y] = i
                        heapq.heappush(queue, (height[x][y], order, x, y, i))
                        order += 1
            while queue:
                level, _, x, y, i = heapq.heappop(queue)
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and keep[nx][ny] and owner[nx][ny] < 0:
                        owner[nx][ny] = i
                        heapq.heappush(queue, (max(level, height[nx][ny]), order, nx, ny, i))
                        order += 1
            mine = [(x, y) for x in range(w) for y in range(h) if owner[x][y] == 0]
            # Of what it reached, the figure is its largest connected part (a stray bit across a gap drops).
            parts = _shapes([[owner[x][y] == 0 for y in range(h)] for x in range(w)], w, h)
            figure = max(parts, key=len)
            rest = _shapes([[keep[x][y] and owner[x][y] < 0 for y in range(h)] for x in range(w)], w, h)
            rest += [p for p in parts if p is not figure]
            shapes = [figure] + sorted(rest, key=len, reverse=True)
        elif seed is not None:
            # The figure: the largest shape at `core`, grown back over the pixels at `alpha` it touches; then
            # the other shapes at `alpha` (petals) as usual.
            cores = _shapes([[keep[x][y] and seed[x][y] for y in range(h)] for x in range(w)], w, h)
            if not cores:
                raise ValueError(f"{self.source} {cut.box}: nothing found")
            figure = max(cores, key=len)
            # Other large core shapes, and those cut by the cell's sides, are neighbouring figures. All of them grow
            # at once, a ring of pixels per step, over the pixels at `alpha` nobody has yet, so each keeps its own
            # soft edge; small core shapes (a blossom on an antler, a petal) are taken by whoever reaches them.
            rivals = [shape for shape in cores if shape is not figure
                      and (len(shape) >= len(figure) // 4 or any(x in (0, w - 1) for x, _ in shape))]
            owner = [[-1] * h for _ in range(w)]
            for i, shape in enumerate([figure, *rivals]):
                for x, y in shape:
                    owner[x][y] = i
            ring = [(x, y, i) for i, shape in enumerate([figure, *rivals]) for x, y in shape]
            while ring:
                grown = []
                for x, y, i in ring:
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 <= nx < w and 0 <= ny < h and keep[nx][ny] and owner[nx][ny] < 0:
                            owner[nx][ny] = i
                            grown.append((nx, ny, i))
                ring = grown
            figure = [(x, y) for x in range(w) for y in range(h) if owner[x][y] == 0]
            owned = [[owner[x][y] >= 0 for y in range(h)] for x in range(w)]     # the rest: loose petals
            rest = _shapes([[keep[x][y] and not owned[x][y] for y in range(h)] for x in range(w)], w, h)
            shapes = [figure] + sorted(rest, key=len, reverse=True)
        else:
            shapes = _shapes(keep, w, h)
            if not shapes:
                raise ValueError(f"{self.source} {cut.box}: nothing found")
            shapes.sort(key=len, reverse=True)
        # Extra shapes (petals) cut by the cell's border belong half to a neighbouring frame: left out; with
        # `seeds`, so do those whose middle is nearer a neighbour's centre than this figure's.
        inner = lambda s: all(0 < x < w - 1 and 0 < y < h - 1 for x, y in s)
        if cut.seeds is not None:
            centre, near = cut.seeds[0][0], [c for c, _ in cut.seeds[1]]
            mid = lambda s: cut.box[0] + sum(x for x, _ in s) / len(s)
            ours = lambda s: all(abs(mid(s) - centre) <= abs(mid(s) - c) for c in near)
            inner = lambda s, inner=inner: inner(s) and ours(s)
        chosen = [shapes[0]] + ([s for s in shapes[1:] if len(s) >= cut.min_bits and inner(s)] if cut.keep_all else [])
        pixels = [p for s in chosen for p in s]
        left, top = min(x for x, _ in pixels), min(y for _, y in pixels)
        right, bottom = max(x for x, _ in pixels) + 1, max(y for _, y in pixels) + 1
        image = Image.new("RGBA", (right - left, bottom - top), (0, 0, 0, 0))
        out = image.load()
        for x, y in pixels:
            out[x - left, y - top] = (*rgb[x][y], 255)
        x0, y0 = cut.box[:2]
        # Pixels on the cell's border: a figure cut off by a straight line rather than its own edge.
        edge = sum(1 for x, y in pixels if x in (0, w - 1) or y in (0, h - 1))
        return Piece(image, (left + x0, top + y0, right + x0, bottom + y0), edge)

    def _unchecker(self, rgb, cut: Cut) -> list[list[bool]]:
        w, h = len(rgb), len(rgb[0])
        bg = [[self.background(rgb[x][y]) for y in range(h)] for x in range(w)]
        clear = [[False] * h for _ in range(w)]
        todo = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
        while todo:
            x, y = todo.pop()
            if clear[x][y] or not bg[x][y]:
                continue
            clear[x][y] = True
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h and not clear[nx][ny]:
                    todo.append((nx, ny))
        seen = [[False] * h for _ in range(w)]
        for sx in range(w):
            for sy in range(h):
                if seen[sx][sy] or clear[sx][sy] or not bg[sx][sy]:
                    continue
                pocket, todo = [], [(sx, sy)]
                seen[sx][sy] = True
                while todo:
                    x, y = todo.pop()
                    pocket.append((x, y))
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 <= nx < w and 0 <= ny < h and not seen[nx][ny] and not clear[nx][ny] and bg[nx][ny]:
                            seen[nx][ny] = True
                            todo.append((nx, ny))
                grey = sum(1 for x, y in pocket if max(rgb[x][y]) <= self.pocket_grey)
                if len(pocket) >= 12 and grey >= 0.3 * len(pocket):
                    for x, y in pocket:
                        clear[x][y] = True
        return [[not clear[x][y] for y in range(h)] for x in range(w)]

    def _glow(self, rgb, cut: Cut) -> list[list[bool]]:
        """Coloured pixels, closed by `close` px, with enclosed white cores filled in."""
        w, h = len(rgb), len(rgb[0])
        mask = Image.frombytes("L", (w, h), bytes(
            255 if max(rgb[x][y]) - min(rgb[x][y]) >= cut.chroma else 0 for y in range(h) for x in range(w)))
        if cut.close:
            n = 2 * cut.close + 1
            mask = mask.filter(ImageFilter.MaxFilter(n)).filter(ImageFilter.MinFilter(n))
        m = mask.load()
        solid = [[m[x, y] > 0 for y in range(h)] for x in range(w)]
        # Holes inside the effect: filled when they are its white core, left clear when they are mostly the
        # checkerboard's grey squares (the inside of a crescent, the gap between petals).
        seen = [[False] * h for _ in range(w)]
        keep = [[solid[x][y] for y in range(h)] for x in range(w)]
        for sx in range(w):
            for sy in range(h):
                if seen[sx][sy] or solid[sx][sy]:
                    continue
                hole, todo, outside = [], [(sx, sy)], False
                seen[sx][sy] = True
                while todo:
                    x, y = todo.pop()
                    hole.append((x, y))
                    outside = outside or x in (0, w - 1) or y in (0, h - 1)
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 <= nx < w and 0 <= ny < h and not seen[nx][ny] and not solid[nx][ny]:
                            seen[nx][ny] = True
                            todo.append((nx, ny))
                grey = sum(1 for x, y in hole if max(rgb[x][y]) <= self.pocket_grey)
                if not outside and grey < 0.12 * len(hole):
                    for x, y in hole:
                        keep[x][y] = True
        return keep


def cells(y0: int, y1: int, edges: list[int], labels: tuple = (), extra: dict | None = None, pad: int = 0,
          seeds: int | None = None, points: dict | None = None, **kw) -> list[Cut]:
    """A row of cells, one per painted frame, between consecutive x `edges`, from y0 to y1. `labels` (the label
    pills) are wiped in every cell; `extra` adds `cleared` areas per frame (index in the row). With `pad` (on a
    sheet with `core`), each cell reaches that many pixels into its neighbours, for frames whose glow or tails
    cross the edge: the neighbour's own body there is a separate core shape and drops."""
    extra = extra or {}
    if seeds is not None:
        # Overlapping figures: each cell reaches the middle of the cells beside it and every figure in it grows
        # from its own middle (the cell's middle), so each keeps what is nearest to it.
        # `points` gives a figure more seed points (sheet x, y) by index: a lantern it spits that touches the next.
        mids = [(a + b) / 2 for a, b in zip(edges, edges[1:])]
        own = [(m, tuple((points or {}).get(i, ()))) for i, m in enumerate(mids)]
        # Each cell reaches the middle of the second figure on either side, and the figures in it all grow.
        return [Cut((round(mids[i - 2]) if i > 1 else edges[0], y0, round(mids[i + 2]) if i + 2 < len(mids) else edges[-1],
                     y1), cleared=tuple(labels) + tuple(extra.get(i, ())),
                    seeds=(own[i], tuple(own[j] for j in (i - 2, i - 1, i + 1, i + 2) if 0 <= j < len(mids)), seeds),
                    **kw)
                for i in range(len(mids))]
    return [Cut((a - (pad if i else 0), y0, b + (pad if i < len(edges) - 2 else 0), y1),
                cleared=tuple(labels) + tuple(extra.get(i, ())), **kw)
            for i, (a, b) in enumerate(zip(edges, edges[1:]))]


def _line_x(points, y: float) -> float:
    """The x of a polyline ((x, y), ... from top to bottom) at height `y`; straight up and down past its ends."""
    if y <= points[0][1]:
        return points[0][0]
    for (xa, ya), (xb, yb) in zip(points, points[1:]):
        if y <= yb:
            return xa + (xb - xa) * (y - ya) / (yb - ya)
    return points[-1][0]


def _shapes(keep, w: int, h: int) -> list[list[tuple[int, int]]]:
    seen = [[False] * h for _ in range(w)]
    shapes = []
    for sx in range(w):
        for sy in range(h):
            if seen[sx][sy] or not keep[sx][sy]:
                continue
            shape, stack = [], [(sx, sy)]
            seen[sx][sy] = True
            while stack:
                x, y = stack.pop()
                shape.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[nx][ny] and keep[nx][ny]:
                        seen[nx][ny] = True
                        stack.append((nx, ny))
            shapes.append(shape)
    return shapes


def shrink(image: Image.Image, k: float) -> Image.Image:
    """`image` scaled by `k` (LANCZOS, premultiplied) with hard 0/255 alpha and clear pixels colourless."""
    size = (max(1, round(image.width * k)), max(1, round(image.height * k)))
    small = image.resize(size, Image.LANCZOS)
    small.putalpha(small.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
    return clean(small)


def clean(image: Image.Image) -> Image.Image:
    """Fully clear pixels carry no colour, so the PNG bytes depend only on what shows."""
    px = image.load()
    for y in range(image.height):
        for x in range(image.width):
            if px[x, y][3] == 0:
                px[x, y] = (0, 0, 0, 0)
    return image


def place(piece: Piece, k: float, frame: tuple[int, int], anchor_x: float, cx: float, ground: int,
          lift: int = 0) -> Image.Image:
    """`piece` scaled by `k` on a `frame`-sized canvas (pixels): the sheet column `anchor_x` lands on pixel
    column `cx`, and the piece's lowest pixel on row `ground` (minus `lift`)."""
    small = shrink(piece.image, k)
    out = Image.new("RGBA", frame, (0, 0, 0, 0))
    x = round(cx - (anchor_x - piece.box[0]) * k)
    y = ground + 1 - small.height - lift
    out.paste(small, (x, y), small)
    return clean(out)


def fit(piece: Piece, frame: tuple[int, int], align: str = "left", width: int | None = None,
        k: float | None = None) -> Image.Image:
    """`piece` scaled to fit `frame` (pixels), or by `k` if given, leading edge on the left (or centred), on
    the bottom row; `width` caps the part kept, measured from the leading (left) edge, in sheet pixels."""
    image = piece.image if width is None else piece.image.crop((0, 0, min(width, piece.image.width), piece.image.height))
    image = image.crop(image.getbbox())
    if k is None:
        k = min(frame[0] / image.width, frame[1] / image.height)
    small = shrink(image, k)
    out = Image.new("RGBA", frame, (0, 0, 0, 0))
    x = 0 if align == "left" else (frame[0] - small.width) // 2
    out.paste(small, (x, frame[1] - small.height), small)
    return clean(out)


def fit_scale(pieces: list[Piece], frame: tuple[int, int]) -> float:
    """The one scale at which every piece fits `frame` (pixels): a group drawn at one size."""
    return min(min(frame[0] / p.image.width, frame[1] / p.image.height) for p in pieces)


def body_mask(image: Image.Image, height: int) -> Image.Image:
    """The bottom `height` rows of `image`'s alpha as a 1-bit mask, on a canvas `height` tall."""
    a = image.getchannel("A").point(lambda v: 255 if v else 0)
    out = Image.new("L", (a.width, height), 0)
    out.paste(a, (0, height - a.height))
    return out.convert("1")


def _count(mask: Image.Image) -> int:
    return mask.convert("L").histogram()[255]


def best_shift(a: Image.Image, b: Image.Image, reach: int) -> int:
    """How far right of `a` (both standing on the same ground row) `b` overlaps it best: the shift with the largest
    intersection over union of their lower bodies. Ties go to the smaller shift, so the result is deterministic."""
    width = a.width + b.width + 2 * reach
    base = Image.new("1", (width, a.height), 0)
    base.paste(a, (b.width + reach, 0))
    best = (-1.0, 0)
    for dx in range(-reach, reach + 1):
        moved = Image.new("1", (width, a.height), 0)
        moved.paste(b, (b.width + reach + dx, 0))
        union = _count(ImageChops.logical_or(base, moved))
        score = _count(ImageChops.logical_and(base, moved)) / union if union else 0
        if score > best[0] + 1e-9 or (abs(score - best[0]) <= 1e-9 and abs(dx) < abs(best[1])):
            best = (score, dx)
    return best[1]
