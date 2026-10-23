"""The Sakura Bat enemy, cut from the user's painted sheet instead of drawn in code.

Source: `docs/concept/Sakura Bat Enemy Sheet.png`, copied to `Tools/sprites/sakura_bat_source.png`, painted (roughly)
to `docs/enemy-sheet-brief-sakura.md` on real transparency (a semi-transparent pink haze). The bats are found and cut
by `sheet_hero.HeroSheet` (alpha 200, found at 220, loose sparkles and petals dropped); they are placed here, not by
`HeroSheet.frames`: a flyer has no ground line, so every frame is lined up by its body, the centroid of its cream fur
(head and body; the wings are pink), which holds the bat steady on its hitbox while the wings beat. Replaces the
code-drawn `sakura_bat` (`sakura_dusk_critters.py` skips the sprites in `NAMES`). Same sprite name, animation names,
loop flags, frame size (46×32 points), anchor (`cx` 23, `ground` 25) and `faces_left` (painted facing right, mirrored
on export); frames at 3x detail.
"""
from __future__ import annotations

from PIL import Image

from sheet_boss import shrink
from sheet_hero import Cat, HeroSheet, Row
from sprite import Sprite

SIZE = (46, 32)                   # points, as the code-drawn bat
CX, GROUND = 23, 25
SCALE = 3

# Rows as painted (counts are the bats painted; two rows differ from their labels, marked). Boxes hold the figures;
# the label pills a box reaches are wiped with `cleared`. IDLE (hovering; GameScene plays `fly` as the bat's resting
# loop, so it would never show) and PROJECTILE (the bat swoops, it does not shoot) are not cut.
SHEET = HeroSheet(
    source="sakura_bat_source.png",
    rows={
        "fly": Row((20, 205, 1530, 335), 8, cleared=((0, 170, 170, 213),)),
        # Cell 5 is a blossom projectile with no bat: wiped.
        "attack": Row((20, 370, 1520, 500), 6, cleared=((0, 330, 205, 377), (900, 370, 1080, 500))),   # 7 cells, labelled 6
        "hurt": Row((20, 540, 850, 665), 4, cleared=((0, 500, 190, 545),)),
        # Tumbling (1-4), bursting (5), a burst of blossoms (6), the petals settling (7-8).
        "death": Row((15, 712, 1520, 856), 8, cleared=((0, 850, 260, 860),)),                          # labelled 6
    },
    frame=SIZE, cx=CX, scale=SCALE, alpha=200, core=220, min_area=1500,
)

# Texture pixels per sheet pixel (0.21 points): the bat is painted side-on, its wing reaching up to about 120 sheet px
# behind its body, so this is the largest size at which the beating wing stays in the frame with the body over the
# hitbox (the code-drawn bat, painted face-on with its wings spread both ways, covered about 500 square points; this
# one about 440).
K = 0.63
# Where the fur's centroid goes (points from the frame's top-left, facing right): 3 points in front of the anchor and
# a little above the middle of the 18×14 hitbox (rows 12-25), so the body covers it.
BODY = (CX + 3.5, 18.0)
MARGIN = 1                        # clear texture pixels kept at the frame's edges

# Animation -> painted row, fps, loop (the code-drawn bat's loop flags). Every painted frame plays once, in order.
PLAN = {
    "fly": ("fly", 14, True),             # 8 frames: 0.57 s a wingbeat
    "attack": ("attack", 12, False),      # 6: 0.5 s (GameScene does not play it today)
    "hurt": ("hurt", 12, False),          # 4: 0.33 s (one hit defeats the bat, so it does not play today)
    "death": ("death", 12, False),        # 8: 0.67 s, ends on the settling petals
}
# Frames without a bat to line up (the burst, the petals): centred across on the body, at the height the painting has
# them under the last bat frame, so the burst stays where the bat burst.
NO_BODY = {"death": 5}

NAMES = {"sakura_bat"}


def _fur(rgb: tuple) -> bool:
    r, g, b = rgb
    return r > 215 and g > 195 and b > 190 and r - b < 40


def _centroid(cat: Cat) -> tuple[float, float]:
    """The centroid of the cream fur, in the cut-out's pixels."""
    px = cat.image.load()
    pts = [(x, y) for y in range(cat.image.height) for x in range(cat.image.width)
           if px[x, y][3] and _fur(px[x, y][:3])]
    return sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts)


def bat() -> Sprite:
    fw, fh = SIZE[0] * SCALE, SIZE[1] * SCALE
    tx, ty = BODY[0] * SCALE, BODY[1] * SCALE
    sprite = Sprite("sakura_bat", SIZE, faces_left=True, cx=CX, ground=GROUND, scale=SCALE)
    for anim, (row, fps, loop) in PLAN.items():
        cats = SHEET.cats[row]
        frames = []
        for i, cat in enumerate(cats):
            ref = cats[min(i, NO_BODY.get(row, len(cats)) - 1)]
            mx, my = _centroid(ref)
            # The sheet point that lands on the body target: this frame's own centroid; for a frame with no bat, the
            # middle of the cut-out across, at the last bat's centroid height (the row shares one painted ground).
            sx, sy = ref.box[0] + mx, ref.box[1] + my
            if ref is not cat:
                sx = (cat.box[0] + cat.box[2]) / 2
            small = shrink(cat.image, K)
            x = round(tx - (sx - cat.box[0]) * K)
            y = round(ty - (sy - cat.box[1]) * K)
            x = min(max(x, MARGIN), fw - MARGIN - small.width)
            y = min(max(y, MARGIN), fh - MARGIN - small.height)
            frame = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
            frame.paste(small, (x, y), small)
            frames.append(frame)
        sprite.add(anim, frames, fps=fps, loop=loop)
    return sprite


def build() -> list[Sprite]:
    return [bat()]
