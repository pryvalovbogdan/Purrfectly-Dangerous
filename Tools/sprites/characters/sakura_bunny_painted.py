"""The Sakura Bunny enemy, cut from the user's painted sheet (`sheet_hero.py`) instead of drawn in code.

Source: `docs/concept/Sakura Bunny Enemy Sheet.png`, copied to `Tools/sprites/sakura_bunny_source.png`, painted
(roughly) to `docs/enemy-sheet-brief-sakura.md` on real transparency: a semi-transparent pink haze and ground
shadows, the bunny's fur and dark outline nearly opaque. Replaces the code-drawn `sakura_bunny`
(`sakura_critters.py` skips the sprites in `NAMES`). Same sprite name, animation names, frame size (44×36 points),
anchor (`cx` 18, `ground` 33) and `faces_left` (painted facing right, mirrored on export); frames at 3x detail.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image

import palette as P

from sheet_hero import Cat, HeroSheet, Row
from sprite import Sprite

SIZE = (44, 36)                   # points, as the code-drawn bunny
CX, GROUND = 18, 33               # its feet: the lowest pixel (the outline) on row 34, as the code-drawn one
SCALE = 3
OUTLINE = P.SK_BUNNY_EDGE         # the painting's dark plum outline, put back where the ground was cut away


def _ground(rgb: tuple) -> bool:
    """The grey-purple contact shadow and the grey-green rocks under a bunny (and, there, its own dark outline):
    unsaturated and not light, or the moss on the rocks: green. The fur is light or pink, the ribbons and bag
    saturated red to purple; nothing on the bunny is green."""
    r, g, b = rgb
    return max(rgb) - min(rgb) < 40 and max(rgb) < 215 or g > r + 6 and g > b


@dataclass
class BunnySheet(HeroSheet):
    """`HeroSheet` that also cuts the painted ground away from under each bunny: in the bottom `band` sheet pixels
    of each (per row in `bands`), unsaturated dark pixels (`_ground`) are cleared, and the bunny's outline is put
    back as `ring` pixels of `OUTLINE` around what is left, over what was cleared. The figure is then cropped again,
    so its feet stand on the ground line."""
    band: int = 12
    bands: dict = field(default_factory=dict)
    ring: int = 2
    speck: int = 60

    def _cut_row(self, name: str, row: Row) -> list[Cat]:
        cats = super()._cut_row(name, row)
        band = self.bands.get(name, self.band)
        for cat in cats:
            self._drop_ground(cat, band)
        if row.airborne:
            ground = row.ground if row.ground is not None else max(c.box[3] for c in cats)
            for c in cats:
                c.lift = max(0, ground - c.box[3])
        return cats

    def _drop_ground(self, cat: Cat, band: int) -> None:
        im = cat.image
        w, h = im.size
        px = im.load()
        top = max(0, h - band)
        cut = {(x, y) for y in range(top, h) for x in range(w) if px[x, y][3] and _ground(px[x, y][:3])}
        for x, y in cut:
            px[x, y] = (0, 0, 0, 0)
        for _ in range(self.ring):
            edge = [(x, y) for x, y in cut
                    if any(0 <= nx < w and 0 <= ny < h and px[nx, ny][3] and (nx, ny) not in cut
                           for nx, ny in ((x + 1, y), (x - 1, y), (x, y - 1), (x, y + 1)))]
            for x, y in edge:
                px[x, y] = OUTLINE
            cut -= set(edge)
        # Bits of the rocks' outline left loose by the cut: pieces under `speck` pixels, apart from the bunny.
        seen = set()
        for sy in range(h):
            for sx in range(w):
                if (sx, sy) in seen or not px[sx, sy][3]:
                    continue
                piece, todo = [], [(sx, sy)]
                seen.add((sx, sy))
                while todo:
                    x, y = todo.pop()
                    piece.append((x, y))
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen and px[nx, ny][3]:
                            seen.add((nx, ny))
                            todo.append((nx, ny))
                if len(piece) < self.speck:
                    for x, y in piece:
                        px[x, y] = (0, 0, 0, 0)
        left, top_, right, bottom = im.getchannel("A").getbbox()
        cat.image = im.crop((left, top_, right, bottom))
        x0, y0 = cat.box[:2]
        cat.box = (x0 + left, y0 + top_, x0 + right, y0 + bottom)
        cat.front -= left

# Rows as painted (counts are the bunnies painted; the labels differ in two rows, marked). Boxes hold the bunnies;
# the label pills that a box reaches are wiped with `cleared`. No RUN row: the run is JUMP then FALL (a crouch, a
# leap, landing, a second smaller hop, landing), the airborne height kept from the painted shadows.
SHEET = BunnySheet(
    source="sakura_bunny_source.png",
    rows={
        "idle": Row((20, 20, 840, 140), 6, align="body", cleared=((0, 0, 160, 43),)),
        "walk": Row((20, 165, 1500, 284), 8, cleared=((0, 140, 160, 180),)),
        "jump": Row((20, 296, 1080, 432), 6, airborne=True, cleared=((0, 280, 160, 322),)),
        "fall": Row((20, 436, 1180, 581), 6, airborne=True, cleared=((0, 436, 160, 476),)),
        # Frame 5 is a blossom projectile with no bunny (the bunny's attack in the game is a melee lunge): wiped.
        "attack": Row((20, 596, 1090, 718), 5, cleared=((0, 590, 190, 615), (725, 596, 870, 718))),   # labelled 6
        "hurt": Row((20, 745, 520, 870), 3, cleared=((0, 710, 160, 754),)),                           # labelled 4
        # Collapses, then a pile of petals: each frame centred on its own.
        "death": Row((550, 745, 1520, 870), 6, align=False, cleared=((545, 710, 715, 754),)),
    },
    # One point row short: `frames()` stands the lowest pixel on the frame's bottom row, and the bunny's ground is
    # one row above the 36-point frame's bottom (padded back on below).
    frame=(SIZE[0], SIZE[1] - 1), cx=CX, scale=SCALE, alpha=200, core=220, min_area=1500,
    # About 0.25 points per sheet pixel: the painted bunny (about 112×89 px sitting) covers about as much as the
    # code-drawn one did (about 435 square points).
    max_scale=0.75,
    size_to="idle", size_skip=("death",),
    bands={"death": 26},             # the rocks under the lying bunny reach higher than a contact shadow
    max_lift=4,
)

# Animation -> painted rows (every bunny, in order), fps, loop.
PLAN = {
    "idle": (("idle",), 8, True),             # 6 frames: 0.75 s a loop
    "walk": (("walk",), 13, True),            # 8: 0.62 s, the hop back before the lunge
    "run": (("jump", "fall"), 18, True),      # 12: 0.67 s, two bounds
    "attack": (("attack",), 11, False),       # 5: 0.45 s, the burst at the muzzle in 3, held on the last
    "hurt": (("hurt",), 10, False),           # 3: 0.3 s
    "death": (("death",), 8, False),          # 6: 0.75 s, ends on the petal pile
}

NAMES = {"sakura_bunny"}


def bunny() -> Sprite:
    sheet = SHEET
    used = sorted((row, i) for rows, _, _ in PLAN.values() for row in rows for i in range(sheet.rows[row].count))
    cut = sheet.frames(used)
    sprite = Sprite("sakura_bunny", SIZE, faces_left=True, cx=CX, ground=GROUND, scale=SCALE)
    for anim, (rows, fps, loop) in PLAN.items():
        frames = []
        for row in rows:
            for i in range(sheet.rows[row].count):
                frame = Image.new("RGBA", (SIZE[0] * SCALE, SIZE[1] * SCALE), (0, 0, 0, 0))
                frame.paste(cut[(row, i)], (0, 0))
                frames.append(frame)
        sprite.add(anim, frames, fps=fps, loop=loop)
    return sprite


def build() -> list[Sprite]:
    return [bunny()]
