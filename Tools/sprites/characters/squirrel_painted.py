"""The Squirrel Soldier (level 1), cut from the user's painted sheet instead of drawn in code.

Source: `docs/concept/Squirrel Soldier Enemy Sheet.png`, copied to `Tools/sprites/squirrel_source.png`, painted
(roughly) to `docs/enemy-sheet-brief-fluffy.md` on real transparency: a faint haze (alpha under 10) round each
figure, the fur, helmet, spear and black outline nearly opaque (alpha about 252). The squirrels are found and cut by
`sheet_hero.HeroSheet` (alpha 200, found at 220); they are placed here, not by `HeroSheet.frames`: every frame at one
scale, lined up by its body (the centroid of its orange fur, not the spear), its lowest pixel on the ground line.
Replaces the code-drawn `squirrel` (`forest.py` skips the sprites in `NAMES`). Same sprite name, animation names,
loop flags, frame size (36×36 points), anchor (`cx` 18, `ground` 34) and `faces_left` (painted facing right,
mirrored on export); frames at 3x detail.
"""
from __future__ import annotations

from PIL import Image

from sheet_boss import shrink
from sheet_hero import Cat, HeroSheet, Row
from sprite import Sprite

SIZE = (36, 36)                   # points, as the code-drawn squirrel
CX, GROUND = 18, 34               # its lowest pixel on row 35 (the frame's last), as the code-drawn one
SCALE = 3


def _cut(x0: float, y0: float, x1: float, y1: float) -> tuple:
    """Two-pixel-wide rectangles along the line (x0, y0)-(x1, y1), one per sheet row: a cut through the black
    outline that two walking squirrels share where one's spear tip touches the next one's tail."""
    rects = []
    for y in range(int(y0), int(y1) + 1):
        x = round(x0 + (x1 - x0) * (y - y0) / (y1 - y0))
        rects.append((x, y, x + 2, y + 1))
    return tuple(rects)


# Rows as painted (each labelled with the count painted). Boxes hold the figures, clear of the label pills. IDLE,
# RUN, ATTACK, HIT, THROW and SPEAR PROJECTILE are not used by the game and not cut.
SHEET = HeroSheet(
    source="squirrel_source.png",
    rows={
        # Each spear tip touches the next squirrel's tail: cut apart along the outline they share.
        "walk": Row((800, 55, 1774, 232), 4,
                    cleared=_cut(1017, 123, 1007, 142) + _cut(1199, 120, 1189, 147) + _cut(1375, 134, 1375, 150)),
        # Struck (eyes squeezed shut), pitching forward with "x x" eyes, lying flat with the spear beside it (2-3).
        "death": Row((480, 505, 1774, 670), 4),
    },
    frame=(SIZE[0], SIZE[1] - 1), cx=CX, scale=SCALE, alpha=200, core=220, min_area=1500,
)

K = 0.5
BODY_X = 13.5                     # where the fur's centroid goes (points from the frame's left, facing right)
MARGIN = 1                        # clear texture pixels kept at the frame's sides and top
# DEATH 1-3 paint the dropped spear lying out in front, past the frame's edge at this scale (the lying squirrel is
# 33 points long on its own): it is cut off at these sheet columns, just in front of the face, so only the shaft
# under the chin shows (DEATH 0 is painted without it, so the spear is gone from the first death frame on).
SPEAR = {1: 878, 2: 1114, 3: 1383}

# Animation -> (painted row, its frames in order), fps, loop (the code-drawn squirrel's loop flags; durations as
# the brief's).
PLAN = {
    "walk": (("walk", (0, 1, 2, 3)), 8, True),         # 4 frames: 0.5 s a stride
    "death": (("death", (0, 1, 2, 3)), 8, False),      # 4: 0.5 s, ends lying flat
}

NAMES = {"squirrel"}


def _fur(rgb: tuple) -> bool:
    r, g, b = rgb
    return r > 150 and r - b > 80


def _centroid(cat: Cat) -> float:
    """The centroid across of the orange fur (pixels from the cut-out's left): the body, not the spear."""
    px = cat.image.load()
    w, h = cat.image.size
    xs = [x for y in range(h) for x in range(w) if px[x, y][3] and _fur(px[x, y][:3])]
    return sum(xs) / len(xs)


def squirrel() -> Sprite:
    fw, fh = SIZE[0] * SCALE, SIZE[1] * SCALE
    tx = BODY_X * SCALE
    ground = (GROUND + 1) * SCALE + SCALE - 1     # the lowest texture row: the bottom of point row 35
    sprite = Sprite("squirrel", SIZE, faces_left=True, cx=CX, ground=GROUND, scale=SCALE)
    for anim, ((row, which), fps, loop) in PLAN.items():
        frames = []
        for i in which:
            cat = SHEET.cats[row][i]
            if row == "death" and i in SPEAR:
                image = cat.image.crop((0, 0, SPEAR[i] - cat.box[0], cat.image.height))
                cat = Cat(image.crop(image.getbbox()), cat.box, 0, 0)    # the spear lay lowest: its paws now
            small = shrink(cat.image, K)
            x = round(tx - _centroid(cat) * K)
            x = min(max(x, MARGIN), fw - MARGIN - small.width)
            y = max(ground + 1 - small.height, MARGIN)
            frame = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
            frame.paste(small, (x, y), small)
            frames.append(frame)
        sprite.add(anim, frames, fps=fps, loop=loop)
    return sprite


def build() -> list[Sprite]:
    return [squirrel()]
