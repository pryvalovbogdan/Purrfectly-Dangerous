"""The Samurai Ronin enemy, cut from the user's painted sheet instead of drawn in code.

Source: `docs/concept/Samurai Ronin Enemy Sheet.png`, copied to `Tools/sprites/samurai_ronin_source.png`, painted
(roughly) to `docs/enemy-sheet-brief-sakura.md` on real transparency: a heavy semi-transparent pink haze and dark
ground shadows, the ronin's fur, hat, scarf, blade and dark outline nearly opaque. The figures are found and cut by
`sheet_hero.HeroSheet` (alpha 200, found at 220, loose petals dropped); they are placed here, not by
`HeroSheet.frames`, so the slash crescents can run off the frame's edge instead of shrinking the ronin to fit them:
every frame at one scale, lined up by its body (the centroid of its near-black fur, gi and hat outline), its feet (the
lowest pixel under the body) on the ground line. Replaces the code-drawn `samurai_ronin` (`sakura_night_critters.py`
skips the sprites in `NAMES`). Same sprite name, animation names, loop flags, frame size (52×40 points), anchor
(`cx` 20, `ground` 37) and `faces_left` (painted facing right, mirrored on export); frames at 3x detail.
"""
from __future__ import annotations

from PIL import Image

from sheet_boss import shrink
from sheet_hero import Cat, HeroSheet, Row
from sprite import Sprite

SIZE = (52, 40)                   # points, as the code-drawn ronin
CX, GROUND = 20, 37               # its feet: the lowest pixel on row 38, as the code-drawn one
SCALE = 3

# Rows as painted (counts are the ronins painted; two rows differ from their labels, marked). Boxes hold the figures;
# the label pills a box reaches are wiped with `cleared`. PROJECTILE (the ronin's slash is melee) is not cut.
SHEET = HeroSheet(
    source="samurai_ronin_source.png",
    rows={
        "idle": Row((20, 44, 1100, 160), 6, cleared=((0, 0, 175, 47),)),
        "walk": Row((20, 188, 1750, 312), 9, cleared=((0, 160, 175, 200),)),                     # labelled 8
        # The strikes (3 and 5) keep their crescents; they are cut off at the frame's edge.
        "attack": Row((20, 333, 1600, 486), 6, cleared=((0, 310, 210, 354),)),
        "hurt": Row((20, 505, 870, 630), 4, cleared=((0, 480, 190, 523),)),
        # Kneeling, falling over, the hat rolling off (1-5), a burst of blossoms (6-7), a low pile of petals (8).
        # The PROJECTILE label's pill touches the first ronin's feet (sheet rows 757-759): wiped, the feet a row short.
        "death": Row((20, 650, 1740, 760), 8, cleared=((0, 620, 190, 663), (0, 757, 250, 760))),  # labelled 6
    },
    frame=(SIZE[0], SIZE[1] - 1), cx=CX, scale=SCALE, alpha=200, core=220, min_area=1500,
)

# Texture pixels per sheet pixel (0.25 points): the painted ronin (about 160×112 px standing, 10 900 px²) covers about
# as much as the code-drawn one did (about 684 square points).
K = 0.75
# Where the body's centroid goes (points from the frame's left, facing right): as near the anchor as the scarf trailing
# behind allows, so that it stays in the frame.
BODY_X = 27.0
FEET = 35                         # sheet px either side of the body's centroid searched for the feet
# Rows whose frames may run off the frame's edges: the slash crescents and the sword raised behind.
CROPPED = ("attack",)
# The petal burst and pile at the end of DEATH: drawn smaller than the ronin (it is a modest pile), centred on where
# the last ronin's body lay.
PILE = 0.7

# Animation -> painted row, fps, loop (the code-drawn ronin's loop flags). Every painted frame plays once, in order.
PLAN = {
    "idle": ("idle", 8, True),            # 6 frames: 0.75 s, the stance
    "walk": ("walk", 12, True),           # 9: 0.75 s a stride
    "attack": ("attack", 12, False),      # 6: 0.5 s, the slash crescent in 3
    "hurt": ("hurt", 12, False),          # 4: 0.33 s
    "death": ("death", 12, False),        # 8: 0.67 s, ends on the pile of petals
}

NAMES = {"samurai_ronin"}


def _dark(rgb: tuple) -> bool:
    return max(rgb) < 70


def _centroid(cat: Cat) -> float | None:
    """The body's centroid across (pixels from the cut-out's left), or None for a frame with no ronin (the petals)."""
    px = cat.image.load()
    w, h = cat.image.size
    xs = [x for y in range(h) for x in range(w) if px[x, y][3] and _dark(px[x, y][:3])]
    return sum(xs) / len(xs) if len(xs) >= 500 else None


def _feet(image: Image.Image, mx: float, reach: float) -> int:
    """The lowest opaque row of `image` within `reach` pixels either side of column `mx` (the feet, not the blade's
    tip or a crescent painted lower)."""
    px = image.load()
    lo, hi = max(0, int(mx - reach)), min(image.width, int(mx + reach) + 1)
    return max(y for y in range(image.height) for x in range(lo, hi) if px[x, y][3])


def ronin() -> Sprite:
    fw, fh = SIZE[0] * SCALE, SIZE[1] * SCALE
    tx = BODY_X * SCALE
    ground = (GROUND + 1) * SCALE + SCALE - 1     # the feet's lowest texture row: the bottom of point row 38
    sprite = Sprite("samurai_ronin", SIZE, faces_left=True, cx=CX, ground=GROUND, scale=SCALE)
    for anim, (row, fps, loop) in PLAN.items():
        frames = []
        last = tx
        for cat in SHEET.cats[row]:
            mx = _centroid(cat)
            if mx is None:                  # petals: smaller, centred on where the last body was, on the ground
                small = shrink(cat.image, K * PILE)
                x = round(last - small.width / 2)
                feet = small.height - 1
            else:
                small = shrink(cat.image, K)
                x = round(tx - mx * K)
                if row not in CROPPED:
                    # Kept whole in the frame where it fits (a ronin falling over slides back a little); where it
                    # does not, its front kept whole and the scarf trailing behind cut at the frame's edge.
                    x = max(x, 1) if small.width <= fw - 2 else 1 - (small.width - (fw - 2))
                    x = min(x, fw - 1 - small.width)
                last = x + mx * K
                feet = _feet(small, mx * K, FEET * K)
            frame = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
            frame.paste(small, (x, ground - feet), small)
            frames.append(frame)
        sprite.add(anim, frames, fps=fps, loop=loop)
    return sprite


def build() -> list[Sprite]:
    return [ronin()]
