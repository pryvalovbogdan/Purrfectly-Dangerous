"""The Bird Crow enemy, cut from the user's painted sheet instead of drawn in code.

Source: `docs/concept/Bird Crow Enemy Sheet.png`, copied to `Tools/sprites/bird_crow_source.png`, painted (roughly)
to `docs/enemy-sheet-brief-sakura.md` on real transparency: a heavy semi-transparent pink glow, the crow's feathers,
mask, scarf and dark outline nearly opaque. The crows are found and cut by `sheet_hero.HeroSheet` (alpha 200, found at
220, loose petals dropped); they are placed here, not by `HeroSheet.frames`: a flyer has no ground line (and this one
no painted shadow), so, as for the Sakura Bat, every frame is lined up by its head, the centroid of its cream tengu
mask, which holds the crow steady on its hitbox while the wings beat. Replaces the code-drawn `bird_crow`
(`sakura_critters.py` skips the sprites in `NAMES`). Same sprite name, animation names, loop flags, frame size (48×34
points), anchor (`cx` 22, `ground` 27) and `faces_left` (painted facing right, mirrored on export); frames at 3x
detail.
"""
from __future__ import annotations

from PIL import Image

from sheet_boss import shrink
from sheet_hero import Cat, HeroSheet, Row
from sprite import Sprite

SIZE = (48, 34)                   # points, as the code-drawn crow
CX, GROUND = 22, 27
SCALE = 3

# Rows as painted (counts are the shapes cut; four rows differ from their labels, marked). Boxes hold the figures;
# the label pills a box reaches are wiped with `cleared`. PROJECTILE (painted 7, labelled 6; the crow dives, it does
# not throw feathers) is not cut.
SHEET = HeroSheet(
    source="bird_crow_source.png",
    rows={
        "idle": Row((20, 25, 1340, 152), 7, cleared=((0, 0, 180, 52),)),                         # labelled 6
        "fly": Row((20, 175, 1774, 326), 9, cleared=((0, 160, 180, 209),)),                      # labelled 8
        # Six crows and, beside crows 4-6, three loose pink feathers (projectiles): cut as shapes, then left out
        # (`FEATHERS`).
        "attack": Row((20, 330, 1680, 490), 9, cleared=((0, 325, 215, 378),)),                  # 6 crows, labelled 6
        "hurt": Row((20, 500, 870, 632), 4, cleared=((0, 485, 190, 534),)),
        # Falling (1-2), lying, bursting into petals (3-5), piles of blossoms (6-8).
        "death": Row((20, 640, 1774, 762), 8, cleared=((0, 630, 205, 680),)),                   # labelled 6
    },
    frame=SIZE, cx=CX, scale=SCALE, alpha=200, core=220, min_area=1500,
)
FEATHERS = {"attack": (4, 6, 8)}       # shapes in a row that are not the crow (left to right)

# Texture pixels per sheet pixel (0.18 points): the largest at which the beating wings (up to about 90 sheet px above
# the mask and 90 below it) stay in the 34-point frame; the painted crow (about 170×100 px, 9 600 px²) then covers about
# 320 square points, the code-drawn one about 390.
K = 0.55
# Where the mask's centroid goes (points from the frame's top-left, facing right): the head 7 points in front of the
# anchor, so the body behind and under it covers the 18×14 hitbox (rows 13-27, x 13-31), with room above for the
# raised wings, below for the lowered ones, and behind for the tail.
HEAD = (29.5, 16.7)
MARGIN = 1                        # clear texture pixels kept at the frame's edges
# The petal piles at the end of DEATH (no crow): smaller than the crow, a modest pile, centred across on where the
# last crow lay and standing on the row's painted ground under it.
PILE = 0.7

# Animation -> painted row, fps, loop (the code-drawn crow's loop flags). Every painted frame plays once, in order.
PLAN = {
    "idle": ("idle", 8, True),            # 7 frames: 0.88 s (GameScene plays `fly` first, so unused today)
    "fly": ("fly", 14, True),             # 9: 0.64 s a wingbeat
    "attack": ("attack", 12, False),      # 6: 0.5 s, the dive
    "hurt": ("hurt", 12, False),          # 4: 0.33 s (one hit defeats the crow, so it does not play today)
    "death": ("death", 12, False),        # 8: 0.67 s, ends on a pile of petals
}

NAMES = {"bird_crow"}


def _mask(rgb: tuple) -> bool:
    r, g, b = rgb
    return r > 225 and g > 195 and b > 150


def _head(cat: Cat) -> tuple[float, float] | None:
    """The centroid of the cream mask, in the cut-out's pixels, or None for a frame with no crow (the petals)."""
    px = cat.image.load()
    pts = [(x, y) for y in range(cat.image.height) for x in range(cat.image.width)
           if px[x, y][3] and _mask(px[x, y][:3])]
    if len(pts) < 100:
        return None
    return sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts)


def crow() -> Sprite:
    fw, fh = SIZE[0] * SCALE, SIZE[1] * SCALE
    tx, ty = HEAD[0] * SCALE, HEAD[1] * SCALE
    sprite = Sprite("bird_crow", SIZE, faces_left=True, cx=CX, ground=GROUND, scale=SCALE)
    for anim, (row, fps, loop) in PLAN.items():
        cats = [c for i, c in enumerate(SHEET.cats[row]) if i not in FEATHERS.get(row, ())]
        frames = []
        first = _head(cats[0])
        last_x = tx
        for cat in cats:
            head = _head(cat)
            if head is None:                # petals: centred on the last crow, on the row's painted ground
                small = shrink(cat.image, K * PILE)
                x = round(last_x - small.width / 2)
                bottom = ty + (cat.box[3] - (cats[0].box[1] + first[1])) * K
                y = round(bottom - small.height)
            else:
                small = shrink(cat.image, K)
                x = round(tx - head[0] * K)
                if row == "death":
                    # The death keeps its painted height (the row shares one ground), so the crow drops as it falls.
                    y = round(ty - (cats[0].box[1] + first[1] - cat.box[1]) * K)
                else:
                    y = round(ty - head[1] * K)
                last_x = x + small.width / 2
            x = min(max(x, MARGIN), fw - MARGIN - small.width)
            y = min(max(y, MARGIN), fh - MARGIN - small.height)
            frame = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
            frame.paste(small, (x, y), small)
            frames.append(frame)
        sprite.add(anim, frames, fps=fps, loop=loop)
    return sprite


def build() -> list[Sprite]:
    return [crow()]
