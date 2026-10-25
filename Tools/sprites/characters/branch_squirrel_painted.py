"""The Squirrel on a Branch (level 1) and its thrown acorn, cut from the user's painted sheet instead of drawn in code.

Source: `docs/concept/Branch Squirrel Enemy Sheet.png`, copied to `Tools/sprites/branch_squirrel_source.png`, painted
(roughly) to `docs/enemy-sheet-brief-fluffy.md` on real transparency: a soft semi-transparent edge, the fur, leaves,
bark and dark outline nearly opaque. The squirrels are found and cut by `sheet_hero.HeroSheet` (alpha 200, found at
220); they are placed here, not by `HeroSheet.frames`: every frame at one scale, lined up by its branch (the centroid
of the bark), so the branch it stands on stays put while the squirrel breathes, throws and falls over on it.
The branch with its leaves is painted under the squirrel in every frame and is part of the sprite, as it was in the
code-drawn one. Replaces the code-drawn `branch_squirrel` and `acorn_thrown` (`forest.py` skips the sprites in
`NAMES`). Same sprite names, animation names, loop flags, frame sizes (40×40 and 14×14 points), `cx` and
`faces_left` (painted facing right, mirrored on export); frames at 3x detail.

The ground line (the anchor row: the branch top the squirrel sits on, at the item's `baseY`) moves up from row 32 to
row 29: the painted leaves hang about 10 points below the branch, more than the 7 rows the code-drawn branch had
under it. `Sprites.json` carries the anchor, so the game needs no change.
"""
from __future__ import annotations

from PIL import Image

from sheet_boss import clean, shrink
from sheet_hero import Cat, HeroSheet, Row
from sprite import Sprite

SIZE = (40, 40)                   # points, as the code-drawn branch squirrel
CX = 20
GROUND = 29                       # the branch top under the squirrel (row 32 in the code-drawn one; see the docstring)
SCALE = 3

# Rows as painted (each labelled with the count painted). Boxes hold the figures, clear of the label pills. ALERT,
# HIT (with stars), ACORN PROJECTILE (a fiery trail and leaves behind it), LEAF EFFECTS are not used by the game and
# not cut; the thrown acorn is the first DROP ACORN (its motion lines cut off).
SHEET = HeroSheet(
    source="branch_squirrel_source.png",
    rows={
        # IDLE 2's tail touches a leaf of IDLE 1: cut apart where they meet.
        "idle": Row((15, 58, 895, 262), 4, splits=((466, 120, 484, 152),)),
        "throw": Row((915, 62, 1774, 262), 4),
        # DEATH 4 drops an acorn (with motion lines) below the branch: cleared.
        "death": Row((950, 345, 1774, 522), 4, cleared=((1625, 503, 1705, 522),)),
        "drop": Row((1165, 640, 1610, 830), 4),
    },
    frame=(SIZE[0], SIZE[1] - 1), cx=CX, scale=SCALE, alpha=200, core=220, min_area=1500,
)

# Texture pixels per sheet pixel (0.157 points): the painted squirrel (about 133 px from the ear tips to the branch)
# stands about 21 points tall, its hit area 20; the branch and leaves, lined up, span 244 px (38 points).
K = 0.47
# Where the bark's centroid goes (texture pixels from the frame's left and top, facing right): the squirrel's body
# over `CX`, the lowest leaf on the frame's last row.
BARK = (61, 78)
MARGIN = 1                        # clear texture pixels kept at the frame's sides and top

# Animation -> (painted row, its frames in order), fps, loop (the code-drawn branch squirrel's loop flags and about
# its durations). `throw` starts as the acorn leaves (the game spawns the acorn and plays it on the same step):
# holding it (1), arm out (2-3), a new acorn in its paws (4).
PLAN = {
    "idle": (("idle", (0, 1, 2, 3)), 6, True),       # 4 frames: 0.67 s a breath, as the code-drawn 2 at 3 fps
    "throw": (("throw", (0, 1, 2, 3)), 10, False),   # 4: 0.4 s
    "death": (("death", (0, 1, 2, 3)), 8, False),    # 4: 0.5 s, ends lying limp over the branch with "x x" eyes
}

ACORN = (14, 14)                  # points, as the code-drawn thrown acorn
ACORN_K = 0.53                    # the painted acorn (57×74 px with its stem) at 10×13 points, as the code-drawn 12×14

NAMES = {"branch_squirrel", "acorn_thrown"}


def _fur(rgb: tuple) -> bool:
    r, g, b = rgb
    return r > 150 and r - b > 80


def _bark(rgb: tuple) -> bool:
    r, g, b = rgb
    return 60 < r < 170 and g < r * 0.75 and b < g and not _fur(rgb)


def _bark_centroid(cat: Cat) -> tuple[float, float]:
    """The centroid of the brown bark (pixels from the cut-out's top left): the branch, not the squirrel."""
    px = cat.image.load()
    w, h = cat.image.size
    pts = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] and _bark(px[x, y][:3])]
    return sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts)


def branch_squirrel() -> Sprite:
    fw, fh = SIZE[0] * SCALE, SIZE[1] * SCALE
    sprite = Sprite("branch_squirrel", SIZE, faces_left=True, cx=CX, ground=GROUND, scale=SCALE)
    for anim, ((row, which), fps, loop) in PLAN.items():
        frames = []
        for i in which:
            cat = SHEET.cats[row][i]
            small = shrink(cat.image, K)
            bx, by = _bark_centroid(cat)
            x = round(BARK[0] - bx * K)
            x = min(max(x, MARGIN), fw - MARGIN - small.width)
            y = round(BARK[1] - by * K)
            y = min(max(y, MARGIN), fh - small.height)
            frame = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
            frame.paste(small, (x, y), small)
            frames.append(frame)
        sprite.add(anim, frames, fps=fps, loop=loop)
    return sprite


def _acorn() -> Image.Image:
    """The first DROP ACORN without the motion lines above it: everything above the stem's dark outline."""
    image = SHEET.cats["drop"][0].image
    px = image.load()
    top = next(y for y in range(image.height) for x in range(image.width)
               if px[x, y][3] and max(px[x, y][:3]) < 70)
    image = image.crop((0, top, image.width, image.height))
    return image.crop(image.getbbox())


def acorn_thrown() -> Sprite:
    """The acorn turning a quarter turn a frame, clockwise (it rolls right; mirrored, it rolls left), as the
    code-drawn one did: it spins in the air and rolls on along the ground with the same frames."""
    fw, fh = ACORN[0] * SCALE, ACORN[1] * SCALE
    small = shrink(_acorn(), ACORN_K)
    sprite = Sprite("acorn_thrown", ACORN, faces_left=True, scale=SCALE)
    frames = []
    for turn in (None, Image.Transpose.ROTATE_270, Image.Transpose.ROTATE_180, Image.Transpose.ROTATE_90):
        piece = small if turn is None else small.transpose(turn)
        frame = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        frame.paste(piece, ((fw - piece.width) // 2, (fh - piece.height) // 2), piece)
        frames.append(clean(frame))
    sprite.add("fly", frames, fps=16)
    return sprite


def build() -> list[Sprite]:
    return [branch_squirrel(), acorn_thrown()]
