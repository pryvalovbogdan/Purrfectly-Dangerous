"""Hero animation frames cut from a user's painted sprite sheet instead of drawn in code.

The cats sit in rows on the sheet, with glow, loose petals and effect swirls around them. Some sheets
have real transparency; others have a light checkerboard baked in (`HeroSheet.background`). For each
row (`Row`, a hand-tuned box in the sheet) the cutter:

1. on a sheet with real transparency, thresholds the painted alpha (`HeroSheet._transparent`); on a
   checkerboard sheet, makes the alpha (`HeroSheet._unchecker`): a flood fill from the box's
   border through the checkerboard and ground shadows, stopped by the cat's dark outline (so her
   white fur stays); then on through whatever the outline does not wall in (glow, petals, swirls,
   speed lines); checkerboard pockets the fill cannot reach are cleared, and thin strands cut off;
2. thresholds the alpha (`HeroSheet.alpha`): the solid fur and outline stay, the haze goes;
3. finds the cats as the connected shapes of at least `min_area` pixels, left to right (or, with
   `Row.splits` giving one cell per cat, the largest shape in each cell), so effects that do not touch the cat drop;
4. scales every frame of the sprite by ONE factor, chosen so the widest and tallest frame used still
   fits the game frame (but never above `max_scale`, so a cat painted small is not blurred by
   upscaling), so the hero never changes size between animations (rows listed in
   `own_scale` are the exception: shrunk further on their own when they would not fit);
5. puts the feet on one ground line (each grounded cat's lowest pixel on the frame's bottom row;
   airborne rows keep their painted height above the row's ground, clamped) and lines the cats of a
   row up by the front of the head (the rightmost pixel of the top half), with the row as a whole
   centred on the anchor;
6. downscales with LANCZOS to `scale`× the game frame (e.g. 132×108 for a 44×36 frame at 3x) and puts
   the alpha back to hard 0/255, so no glow halo shows on dark backgrounds.

Everything is plain arithmetic on the PNG, so the output is identical on every run.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Callable

from PIL import Image, ImageChops, ImageFilter

HERE = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Row:
    """One row of cats in the sheet."""
    box: tuple[int, int, int, int]       # x0, y0, x1, y1 in sheet pixels: the cats only, not the row's label
    count: int                           # cats expected in the box (the build fails loudly otherwise)
    airborne: bool = False               # keep each cat's painted height above the row's ground line
    ground: int | None = None            # that ground line (sheet y); default: the lowest cat's bottom
    # Per cat (index in the row): drop everything left of this sheet x (a long trail behind it).
    trim_left: dict = field(default_factory=dict)
    # Sheets with a baked-in checkerboard (`HeroSheet.background`): this row's own background rule
    # (e.g. a stricter one for a cat with no dark outline), and how thin (in sheet pixels) a strand
    # touching the cat may be and still be cut off (swirl rings, speed lines): 0 keeps everything.
    background: Callable[[tuple], bool] | None = None
    thin: int | None = None              # the sheet's `thin` for this row
    reach: int | None = None             # the sheet's `reach` for this row (0: off, for a cat with no outline)
    # Rectangles (sheet x0, y0, x1, y1) cleared by hand: an effect that touches the cat and is too
    # thick for `thin`.
    cleared: tuple = ()
    min_area: int | None = None          # smallest shape counted as a cat, if not the sheet's
    # How the row's cats are lined up: True by the front of the head (a run, a leap), False each centred on
    # its own, "body" each on the one before by where its lower body overlaps it best (a standing pose whose
    # head turns and whose tail and scarf swing, so neither the head nor the outline holds still).
    align: bool | str = True
    # Sheet x positions where the row is cut (a one-pixel clear column), for cats joined by a trail, a
    # swirl or a touching tail. With one cell per cat (`count` - 1 splits) each cell keeps only its
    # largest shape; with fewer, the cut only separates the cats it runs between. A split may also be a
    # rectangle (x0, y0, x1, y1) cleared where two cats touch; on a `core` sheet the cats grow back
    # over it, each up to where they meet.
    splits: tuple = ()
    # Scale each cat to the row's median height: for a row whose painter let the cats drift in size
    # along it (the same pose a little smaller every frame), so a loop does not pop at its seam.
    even: bool = False


@dataclass
class Cat:
    """One cut-out cat at sheet resolution: opaque where kept, clear elsewhere."""
    image: Image.Image
    box: tuple[int, int, int, int]       # where it was in the sheet
    lift: int                            # sheet pixels above the row's ground line (0 for grounded rows)
    front: int                           # x of the head's front, relative to `box`


@dataclass
class HeroSheet:
    source: str                          # PNG next to this file
    rows: dict[str, Row]
    frame: tuple[int, int]               # the game frame in points (the hero's SIZE)
    cx: int                              # anchor column in points (the hero's CX)
    scale: int = 3                       # pixels per point in the exported PNGs
    alpha: int = 190                     # alpha at or above which a pixel belongs to the cat
    min_area: int = 2500                 # smallest shape counted as a cat (sheet pixels)
    margin: int = 2                      # clear pixels kept at the frame's sides and top
    max_lift: int = 9                    # the most an airborne cat is drawn above the ground (points)
    # For sheets painted on a checkerboard instead of real transparency: which RGB pixels are the
    # checkerboard (or a ground shadow). Each row is flood-filled through them from its box's border,
    # so the cat's dark outline stops the fill and her white fur inside it stays.
    background: Callable[[tuple], bool] | None = None
    # Then, from what that cleared, through every pixel not walled in by the outline (`dark`) within
    # `reach` sheet pixels left, right, above and below: glow, petals, swirls, trails, dust. 0: off.
    reach: int = 0
    dark: Callable[[tuple], bool] = lambda p: max(p) < 140
    thin: int = 0                        # see `_unchecker`; per row in `Row.thin`
    # Rows scaled on their own (to fit the frame) instead of setting the one scale for every frame:
    # a pose painted much wider than the rest that would otherwise shrink the hero everywhere.
    own_scale: tuple = ()
    pocket_grey: int = 222               # the checkerboard's grey squares are no lighter than this
    max_lift_rows: dict = field(default_factory=dict)   # per row: its own `max_lift` (a flip needs more)
    # The most exported pixels per sheet pixel (1.0: 1:1). A cat painted small would otherwise be
    # upscaled to fill the frame, which blurs it; None: no cap.
    max_scale: float | None = None
    # On sheets with real transparency: a stricter alpha at which neighbouring cats whose soft edges
    # touch are still apart. Cats are found at `core`, then grown out over the pixels at `alpha`.
    core: int | None = None
    # Rows the painter drew at different sizes (a smaller RUN, a bigger MENU): each row is scaled so its
    # cats cover as much as this row's (the square root of the median painted area), so the hero keeps
    # one size from pose to pose. Rows in `size_skip` (lying down, curled up) keep the one scale. None: off.
    size_to: str | None = None
    size_skip: tuple = ()

    @cached_property
    def sheet(self) -> Image.Image:
        return Image.open(HERE / self.source).convert("RGBA")

    @cached_property
    def cats(self) -> dict[str, list[Cat]]:
        cats = {name: self._cut_row(name, row) for name, row in self.rows.items()}
        for name, row in self.rows.items():
            if row.align == "body":
                _line_up_bodies(cats[name])
        return cats

    def cat(self, row: str, index: int) -> Cat:
        return self.cats[row][index]

    def _cut_row(self, name: str, row: Row) -> list[Cat]:
        x0, y0, x1, y1 = row.box
        crop = self.sheet.crop(row.box)
        w, h = crop.size
        painted_alpha = crop.getchannel("A")
        painted = painted_alpha.load()
        if self.background is not None:
            crop.putalpha(self._unchecker(crop, row))
        else:
            crop.putalpha(self._transparent(crop, row))
        alpha = crop.getchannel("A").load()
        solid = [[alpha[x, y] >= self.alpha for y in range(h)] for x in range(w)]
        # The cats are found in the core (or the whole solid shape if there is no `core`), then grown
        # back out over the solid pixels they touch, so cats joined only by their soft edges stay apart.
        grow = self.core is not None and self.background is None
        seed = [[solid[x][y] and painted[x, y] >= self.core for y in range(h)] for x in range(w)] if grow else solid
        for cut in row.splits:
            if isinstance(cut, int):
                seed[cut - x0] = [False] * h
            else:                        # a rectangle where two cats touch (grown back on `core` sheets)
                for x in range(max(0, cut[0] - x0), min(w, cut[2] - x0)):
                    for y in range(max(0, cut[1] - y0), min(h, cut[3] - y0)):
                        seed[x][y] = False
        seen = [[False] * h for _ in range(w)]
        shapes = []
        for sx in range(w):
            for sy in range(h):
                if seen[sx][sy] or not seed[sx][sy]:
                    continue
                shape, stack = [], [(sx, sy)]
                seen[sx][sy] = True
                while stack:
                    x, y = stack.pop()
                    shape.append((x, y))
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 <= nx < w and 0 <= ny < h and not seen[nx][ny] and seed[nx][ny]:
                            seen[nx][ny] = True
                            stack.append((nx, ny))
                if len(shape) >= (row.min_area or self.min_area):
                    shapes.append(shape)
        if grow:
            # Grow every cat at once, one ring of pixels per step, over the solid pixels nobody has yet.
            owner = [[-1] * h for _ in range(w)]
            for i, shape in enumerate(shapes):
                for x, y in shape:
                    owner[x][y] = i
            ring = [(x, y, i) for i, shape in enumerate(shapes) for x, y in shape]
            while ring:
                grown = []
                for x, y, i in ring:
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 <= nx < w and 0 <= ny < h and owner[nx][ny] < 0 and solid[nx][ny]:
                            owner[nx][ny] = i
                            shapes[i].append((nx, ny))
                            grown.append((nx, ny, i))
                ring = grown
        columns = [cut for cut in row.splits if isinstance(cut, int)]
        if columns and len(columns) + 1 == row.count:
            edges = [x0, *columns, x1]
            cells = {}
            for shape in shapes:
                cell = sum(min(x for x, _ in shape) + x0 >= e for e in edges[1:-1])
                if len(shape) > len(cells.get(cell, ())):
                    cells[cell] = shape
            shapes = list(cells.values())
        if len(shapes) != row.count:
            raise ValueError(f"{self.source} row {name}: found {len(shapes)} cats, expected {row.count}")
        shapes.sort(key=lambda s: min(x for x, _ in s))
        src = crop.load()
        cats = []
        for i, shape in enumerate(shapes):
            cut = row.trim_left.get(i)
            if cut is not None:
                shape = [(x, y) for x, y in shape if x + x0 >= cut]
            left, top = min(x for x, _ in shape), min(y for _, y in shape)
            right, bottom = max(x for x, _ in shape) + 1, max(y for _, y in shape) + 1
            image = Image.new("RGBA", (right - left, bottom - top), (0, 0, 0, 0))
            px = image.load()
            for x, y in shape:
                px[x - left, y - top] = (*src[x, y][:3], 255)
            half = (bottom - top) // 2
            front = max(x for x, y in shape if y - top < half) - left
            cats.append(Cat(image, (left + x0, top + y0, right + x0, bottom + y0), 0, front))
        if row.airborne:
            ground = row.ground if row.ground is not None else max(c.box[3] for c in cats)
            for c in cats:
                c.lift = max(0, ground - c.box[3])
        return cats

    def _transparent(self, crop: Image.Image, row: Row) -> Image.Image:
        """The alpha of a row on a sheet with real transparency: the painted alpha thresholded at `alpha`
        (the haze and the ground shadows are semi-transparent, the fur and outline nearly opaque), with
        the row's `cleared` rectangles removed and, with `thin`, strands up to about 2×`thin` pixels wide
        (swirl rings, speed lines) cut off where they leave the body, as in `_unchecker`."""
        w, h = crop.size
        mask = crop.getchannel("A").point(lambda a: 255 if a >= self.alpha else 0)
        x0, y0 = row.box[:2]
        for cx0, cy0, cx1, cy1 in row.cleared:
            mask.paste(0, (cx0 - x0, cy0 - y0, cx1 - x0, cy1 - y0))
        thin = row.thin if row.thin is not None else self.thin
        if thin:
            body = mask.filter(ImageFilter.MinFilter(2 * thin + 1)).filter(ImageFilter.MaxFilter(2 * thin + 3))
            mask = Image.frombytes("L", (w, h), bytes(min(a, b) for a, b in zip(mask.tobytes(), body.tobytes())))
        return mask

    def _unchecker(self, crop: Image.Image, row: Row) -> Image.Image:
        """The alpha of a row painted on a checkerboard. A flood fill from the crop's border through
        `background` pixels (the checkerboard and the ground shadows) clears what lies around the cat;
        the cat's dark outline stops it, so her white fur stays. Pockets the fill cannot reach (a gap
        between legs closed off by a tail) are cleared when they are mostly the checkerboard's grey
        squares. With the row's `thin`, strands up to about 2×`thin` pixels wide (swirl rings, speed
        lines, dust) are cut off where they leave the body: an opening (erode, grow back a little,
        keep only what the grown-back body covers)."""
        background = row.background or self.background
        w, h = crop.size
        px = crop.load()
        rgb = [[px[x, y][:3] for y in range(h)] for x in range(w)]
        bg = [[background(rgb[x][y]) for y in range(h)] for x in range(w)]
        clear = [[False] * h for _ in range(w)]
        for cx0, cy0, cx1, cy1 in row.cleared:
            for x in range(max(0, cx0 - row.box[0]), min(w, cx1 - row.box[0])):
                for y in range(max(0, cy0 - row.box[1]), min(h, cy1 - row.box[1])):
                    clear[x][y] = True
        todo = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
        while todo:
            x, y = todo.pop()
            if clear[x][y] or not bg[x][y]:
                continue
            clear[x][y] = True
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h and not clear[nx][ny]:
                    todo.append((nx, ny))
        reach = row.reach if row.reach is not None else self.reach
        if reach:
            # Then on through anything that is not walled in by the outline: a pixel with no outline
            # within `reach` pixels in some straight direction (left, right, up or down) lies outside
            # the cat (a petal, swirl, speed line, dust cloud). Only from what is already clear, so a
            # thin spot in the outline lets at most a short streak through, not the whole cat.
            dark = [[self.dark(rgb[x][y]) for y in range(h)] for x in range(w)]
            # The rays see the outline one pixel thicker, so they do not slip through a thin spot.
            wall = [[any(dark[i][j] for i in range(max(0, x - 1), min(w, x + 2))
                         for j in range(max(0, y - 1), min(h, y + 2))) for y in range(h)] for x in range(w)]

            def walled(x, y):
                sides = (any(wall[i][y] for i in range(max(0, x - reach), x)),
                         any(wall[i][y] for i in range(x + 1, min(w, x + reach + 1))),
                         any(wall[x][j] for j in range(max(0, y - reach), y)),
                         any(wall[x][j] for j in range(y + 1, min(h, y + reach + 1))))
                return sum(sides) >= 3
            todo = [(nx, ny) for x in range(w) for y in range(h) if clear[x][y]
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
                    if 0 <= nx < w and 0 <= ny < h and not clear[nx][ny]]
            outside = [col[:] for col in clear]
            while todo:
                x, y = todo.pop()
                if clear[x][y] or dark[x][y] or walled(x, y):
                    continue
                clear[x][y] = True
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not clear[nx][ny]:
                        todo.append((nx, ny))
            # Streaks that slipped through a gap in the outline into the fur are narrow: close them
            # (grow the kept shape by 3 pixels and shrink it back) and keep what that fills, if the
            # checkerboard fill had not cleared it.
            kept = Image.frombytes("L", (w, h), bytes(0 if clear[x][y] else 255 for y in range(h) for x in range(w)))
            closed = kept.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(7)).load()
            for x in range(w):
                for y in range(h):
                    if clear[x][y] and not outside[x][y] and closed[x, y]:
                        clear[x][y] = False
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
        mask = Image.frombytes("L", (w, h), bytes(0 if clear[x][y] else 255 for y in range(h) for x in range(w)))
        thin = row.thin if row.thin is not None else self.thin
        if thin:
            body = mask.filter(ImageFilter.MinFilter(2 * thin + 1)).filter(ImageFilter.MaxFilter(2 * thin + 3))
            mask = Image.frombytes("L", (w, h), bytes(min(a, b) for a, b in zip(mask.tobytes(), body.tobytes())))
        return mask

    def factor(self, used: list[tuple[str, int]]) -> float:
        """The one scale (sheet pixels to exported pixels) at which every used cat fits the frame. A row's
        cats are lined up by the front of the head, so the width that must fit is the row's sweep: the
        most any of them reaches behind that point plus the most any reaches in front of it."""
        width = self.frame[0] * self.scale - 2 * self.margin
        height = self.frame[1] * self.scale - self.margin
        k = min(height / (self.cat(r, i).box[3] - self.cat(r, i).box[1]) for r, i in used)
        for row in {r for r, _ in used}:
            cats = [self.cat(r, i) for r, i in used if r == row]
            groups = [cats] if self.rows[row].align else [[c] for c in cats]
            for group in groups:
                sweep = max(c.front for c in group) + max(c.box[2] - c.box[0] - c.front for c in group)
                k = min(k, width / sweep)
        return k if self.max_scale is None else min(k, self.max_scale)

    def _size(self, row: str, used: list[tuple[str, int]]) -> float:
        """The square root of the median painted area of a row's used cats, in sheet pixels."""
        areas = sorted(sum(1 for a in self.cat(r, i).image.getchannel("A").tobytes() if a >= 128)
                       for r, i in used if r == row)
        return areas[len(areas) // 2] ** 0.5

    def size_factors(self, used: list[tuple[str, int]]) -> dict[str, float]:
        """Per row, the factor on top of the one scale that brings it to `size_to`'s size (1 without it)."""
        rows = sorted({r for r, _ in used})
        if self.size_to is None:
            return {row: 1.0 for row in rows}
        ref = self._size(self.size_to, used)
        return {row: 1.0 if row in self.size_skip else ref / self._size(row, used) for row in rows}

    def frames(self, used: list[tuple[str, int]]) -> dict[tuple[str, int], Image.Image]:
        """Every used cat as a finished frame (`frame` × `scale` pixels), keyed by (row, index)."""
        sizes = self.size_factors(used)
        if self.size_to is None:
            k_all = self.factor([f for f in used if f[0] not in self.own_scale])
        else:
            # One scale at which every row, enlarged or shrunk to the common size, still fits.
            cap, self.max_scale = self.max_scale, None
            fits = [self.factor([f for f in used if f[0] == row]) / sizes[row]
                    for row in sizes if row not in self.own_scale]
            self.max_scale = cap
            k_all = min(fits) if cap is None else min(min(fits), cap)
        fw, fh = self.frame[0] * self.scale, self.frame[1] * self.scale
        centre = (self.cx + 0.5) * self.scale
        out = {}
        used = set(used)
        for row in sorted({r for r, _ in used}):
            cats = self.cats[row]
            k = k_all * sizes[row]
            if row in self.own_scale:
                k = min(k, self.factor([f for f in used if f[0] == row]))
            # Line the row's used cats up by the front of the head, then centre their sweep on the anchor
            # (or, for a row that is not lined up, centre each cat on its own).
            # A row painted with its cats drifting in size (`Row.even`): each scaled to the row's median
            # height, so a loop does not pop in size at its seam.
            heights = sorted(c.box[3] - c.box[1] for c in cats)
            ks = [k * (heights[len(heights) // 2] / (c.box[3] - c.box[1]) if self.rows[row].even else 1)
                  for c in cats]

            def front_of(group):
                spans = [(-cats[i].front * ks[i], (cats[i].box[2] - cats[i].box[0] - cats[i].front) * ks[i])
                         for i in group]
                lo, hi = min(s[0] for s in spans), max(s[1] for s in spans)
                return min(max(centre - (lo + hi) / 2, self.margin - lo), fw - self.margin - hi)
            lined = front_of([i for i in range(len(cats)) if (row, i) in used])
            for i, cat in enumerate(cats):
                if (row, i) not in used:
                    continue
                k = ks[i]
                front_x = lined if self.rows[row].align else front_of([i])
                size = (max(1, round(cat.image.width * k)), max(1, round(cat.image.height * k)))
                small = cat.image.resize(size, Image.LANCZOS)
                hard = small.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
                small.putalpha(hard)
                cap = self.max_lift_rows.get(row, self.max_lift)
                lift = min(round(cat.lift * k), cap * self.scale, fh - self.margin - size[1])
                x = round(front_x - cat.front * k)
                y = fh - size[1] - max(0, lift)
                frame = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
                frame.alpha_composite(small, (x, y))
                # Fully clear pixels carry no colour, so the PNG bytes depend only on what shows.
                px = frame.load()
                for yy in range(fh):
                    for xx in range(fw):
                        if px[xx, yy][3] == 0:
                            px[xx, yy] = (0, 0, 0, 0)
                out[(row, i)] = frame
        return out


def _lower_body(cat: Cat) -> Image.Image:
    """The bottom 45% of a cat's opaque pixels as a 1-bit mask (paws, legs and belly: what stands still)."""
    alpha = cat.image.getchannel("A").point(lambda v: 255 if v >= 128 else 0)
    top = alpha.height - max(1, round(alpha.height * 0.45))
    return alpha.crop((0, top, alpha.width, alpha.height)).convert("1")


def _best_shift(a: Image.Image, b: Image.Image, reach: int = 40) -> int:
    """How far right of `a` (bottom rows level) `b` overlaps it best, by intersection over union; ties go to
    the smaller shift, so the result is deterministic."""
    height = max(a.height, b.height)
    width = a.width + b.width + 2 * reach
    base = Image.new("1", (width, height), 0)
    base.paste(a, (b.width + reach, height - a.height))
    best = (-1.0, 0)
    for dx in range(-reach, reach + 1):
        moved = Image.new("1", (width, height), 0)
        moved.paste(b, (b.width + reach + dx, height - b.height))
        union = ImageChops.logical_or(base, moved).convert("L").histogram()[255]
        both = ImageChops.logical_and(base, moved).convert("L").histogram()[255]
        score = both / union if union else 0
        if score > best[0] + 1e-9 or (abs(score - best[0]) <= 1e-9 and abs(dx) < abs(best[1])):
            best = (score, dx)
    return best[1]


def _line_up_bodies(cats: list[Cat]) -> None:
    """For a row with `align="body"`: each cat's `front` rewritten so the usual head line-up puts it where its
    lower body best overlaps the cat before it (the first cat keeps its own)."""
    offset = 0
    for before, cat in zip(cats, cats[1:]):
        offset += _best_shift(_lower_body(before), _lower_body(cat))
        cat.front = cats[0].front - offset
