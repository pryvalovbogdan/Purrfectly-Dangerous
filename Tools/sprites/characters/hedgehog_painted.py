"""The Spiky Hedgehog Cat (level 1), cut from the user's painted sheet instead of drawn in code.

Source: `docs/concept/Hedgehog Enemy Sheet.png`, copied to `Tools/sprites/hedgehog_source.png`, painted (roughly) to
`docs/enemy-sheet-brief-fluffy.md` on real transparency: a soft semi-transparent edge, the quills, fur and dark
outline nearly opaque. The hedgehogs are found and cut by `sheet_hero.HeroSheet` (alpha 200, found at 220); they are
placed here, not by `HeroSheet.frames`: every frame at one scale, centred across on the anchor by the centroid of its
quills and fur, its lowest pixel on the ground line. Replaces the code-drawn `hedgehog` (`forest.py` skips the sprites
in `NAMES`). Same sprite name, animation names, loop flags, frame size (36×28 points), anchor (`cx` 18, `ground` 26)
and `faces_left` (painted facing right, mirrored on export); frames at 3x detail.

The sheet has no CURL row: the curl-up is the first two ROLL frames (the head tucked into a half-curled ball, then the
ball), and ROLLED goes on round the same turn.
"""
from __future__ import annotations

from PIL import Image

from sheet_boss import shrink
from sheet_hero import Cat, HeroSheet, Row
from sprite import Sprite

SIZE = (36, 28)                   # points, as the code-drawn hedgehog
CX, GROUND = 18, 26               # its lowest pixel on row 27, as the code-drawn one
SCALE = 3

# Rows as painted (counts are the hedgehogs painted; DEATH is labelled 4). Boxes hold the figures, clear of the label
# pills. IDLE, RUN, HIT, SPIKE ATTACK and SPIKE PROJECTILE are not used by the game and not cut. The swoosh arcs
# painted behind the rolling ball are soft enough to fall away at alpha 200.
SHEET = HeroSheet(
    source="hedgehog_source.png",
    rows={
        "walk": Row((905, 60, 1774, 228), 4),
        "roll": Row((905, 288, 1774, 462), 4),
        # Struck (paw up, eye open), x-eyed (2-3), sinking flat with its eyes shut (4-5).
        "death": Row((500, 505, 1600, 668), 5),                                                  # labelled 4
    },
    frame=(SIZE[0], SIZE[1] - 1), cx=CX, scale=SCALE, alpha=200, core=220, min_area=1500,
)

# Texture pixels per sheet pixel (0.167 points): the painted hedgehog (about 176×146 px walking, 18 900 px²) covers
# about 525 square points, the code-drawn one about 517; the widest death frame (197 px) is 33 points.
K = 0.5
MARGIN = 1                        # clear texture pixels kept at the frame's sides and top

# Animation -> (painted row, its frames in order), fps, loop (the code-drawn hedgehog's loop flags and about its
# durations). ROLL 4 is left out: the ball turns its face back (looking left, against the way it rolls), and the face
# then jumps to the front again at the loop's seam.
PLAN = {
    "walk": (("walk", (0, 1, 2, 3)), 8, True),        # 4 frames: 0.5 s a stride
    "curl": (("roll", (0, 1)), 8, False),             # 2: 0.25 s, head tucked, then the ball (played once on curling)
    "rolled": (("roll", (2, 0, 1)), 6, True),         # 3: 0.5 s a turn, going on from where `curl` stops
    "death": (("death", (0, 1, 2, 3, 4)), 12, False),  # 5: 0.42 s, ends lying flat
}

NAMES = {"hedgehog"}


def _centroid(cat: Cat) -> float:
    """The centroid across of the opaque pixels (pixels from the cut-out's left)."""
    px = cat.image.load()
    w, h = cat.image.size
    xs = [x for y in range(h) for x in range(w) if px[x, y][3]]
    return sum(xs) / len(xs)


def hedgehog() -> Sprite:
    fw, fh = SIZE[0] * SCALE, SIZE[1] * SCALE
    tx = (CX + 0.5) * SCALE
    ground = (GROUND + 1) * SCALE + SCALE - 1     # the lowest texture row: the bottom of point row 27
    sprite = Sprite("hedgehog", SIZE, faces_left=True, cx=CX, ground=GROUND, scale=SCALE)
    for anim, ((row, which), fps, loop) in PLAN.items():
        frames = []
        for i in which:
            cat = SHEET.cats[row][i]
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
    return [hedgehog()]
