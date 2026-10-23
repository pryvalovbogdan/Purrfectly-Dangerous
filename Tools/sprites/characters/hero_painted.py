"""Heroes cut from the user's painted sprite sheets (`sheet_hero.py`) instead of drawn in code.

Each entry of `PAINTED` replaces the code-drawn skin of the same id in `hero.py`. Same sprite name,
animation names, loop flags, frame size (in points) and anchor as `hero`. Frame counts are the
painted ones (more in-betweens than the code-drawn hero), with the fps set so each animation lasts
about as long as the hero's (`docs/hero-sheet-brief.md`, "Lasts"). Frames are exported at 3x detail
(132×108 PNGs, 44×36 points).

Sakura's sheet is painted to `docs/hero-sheet-brief.md`: every animation has its own row, cheer and
peek included.
"""
from __future__ import annotations

import draw
from sheet_hero import HeroSheet, Row
from sprite import Sprite

from characters.hero import CX, GROUND, SIZE

# Sakura: `docs/concept/Sakura Cat Pixel Sprite Sheet v3.png`, copied to `hero_sakura_source.png`.
# Painted to `docs/hero-sheet-brief.md` on real transparency: the pink haze and the ground shadows are
# semi-transparent (alpha under about 180), her fur and dark outline nearly opaque (the outline's
# lowest pixels about 215), so a threshold of 200 keeps the soft white fur edge and drops the rest.
# Neighbouring cats touch at that threshold in RUN, so the cats are found at 220 (`core`) and grown out.
# Boxes hold the cats only (the label pills sit above them). Airborne rows put their ground on the
# painted shadows. Counts are the cats painted, which differ from the labels in five rows (marked).
SAKURA = HeroSheet(
    source="hero_sakura_source.png",
    rows={
        "idle": Row((10, 42, 634, 120), 8, align="body"),
        "run": Row((645, 42, 1536, 112), 16, even=True,   # drifts from 58 to 52 px tall
                   splits=((1484, 77, 1490, 84),)),      # the last two cats touch
        "stop": Row((10, 170, 598, 256), 8),
        "jump": Row((610, 165, 1052, 256), 5, airborne=True, ground=252),       # labelled 6
        "fall": Row((1062, 165, 1534, 256), 6, airborne=True, ground=252),
        "double": Row((10, 300, 690, 392), 8, airborne=True, ground=381, thin=2),   # the flip; rings cut
        "throw": Row((695, 300, 1520, 392), 9),                                 # labelled 8
        "dash": Row((12, 428, 700, 512), 7, thin=2),                            # labelled 8
        # A leap whose landing frames stand far behind the stretched ones: centred frame by frame.
        "pounce": Row((722, 426, 1532, 514), 8, airborne=True, ground=502, align=False),
        "hurt": Row((15, 555, 392, 645), 4),
        # Tumbles from standing to lying flat: the head moves about, so each frame is centred on its own.
        "death": Row((392, 555, 1160, 645), 9, align=False),                    # labelled 12
        "ko": Row((1160, 555, 1532, 645), 4),
        "ghost": Row((10, 688, 722, 780), 8, align="body"),
        "menu": Row((735, 688, 1532, 780), 9, align="body"),                     # labelled 8
        "sit": Row((10, 822, 505, 912), 8, align="body"),
        "cheer": Row((515, 815, 985, 912), 7, airborne=True, ground=905),       # labelled 8; hops
        # Behind a wooden box she rests her paws on: the box is part of the pose, so it stays.
        "peek": Row((992, 822, 1534, 905), 7, align="body", splits=(1080, 1154, 1228, 1302, 1377, 1453)),  # labelled 8
    },
    # Standing poses (idle, menu, sit, ghost, peek) are lined up by the lower body, not the head: the head
    # turns and the tail and scarf swing in them, which made her slide sideways on the start screen.
    frame=SIZE, cx=CX, alpha=200, core=220, min_area=1500,
    # She is painted small (about 68 sheet px standing): enlarged 1.24x (about 28 pt standing), a little soft
    # but close to the other heroes' 33-34 pt; 1:1 left her at 23 pt.
    max_scale=1.24,
    # Her rows are painted at different sizes (RUN about a fifth smaller than IDLE, MENU and HURT bigger):
    # every row is brought to IDLE's size, except the poses lying down.
    size_to="idle", size_skip=("death", "ko"),
    max_lift=3, max_lift_rows={"cheer": 3},
)


def sakura() -> Sprite:
    sheet = SAKURA
    # Animation -> its row (every painted cat, in order), fps and loop. The fps keep each animation's
    # length near the hero's (the brief's "Lasts"): throw within the 0.25 s throw window, hurt one
    # cycle in the 0.3 s hurt window.
    plan = {
        "run": ("run", 27, True),           # 16 frames, 0.59 s per cycle
        "stop": ("stop", 20, False),        # 8, 0.4 s
        "idle": ("idle", 8, True),          # 8, 1 s; the 8th blinks
        "jump": ("jump", 16, True),         # 5, 0.31 s
        "fall": ("fall", 20, True),         # 6, 0.3 s
        "double": ("double", 26, True),     # 8, 0.31 s: the forward flip
        "throw": ("throw", 36, False),      # 9, 0.25 s
        "dash": ("dash", 23, True),         # 7, 0.3 s
        "pounce": ("pounce", 21, True),     # 8, 0.38 s
        "hurt": ("hurt", 13, True),         # 4, 0.31 s
        "death": ("death", 11, False),      # 9, 0.82 s
        "peek": ("peek", 7, True),          # 7, 1 s
        "cheer": ("cheer", 12, True),       # 7, 0.58 s
        "sit_happy": ("sit", 10, True),     # 8, 0.8 s
        "menu": ("menu", 9, True),          # 9, 1 s
        "ko": ("ko", 5, True),              # 4, 0.8 s
        "ghost": ("ghost", 8, True),        # 8, 1 s
    }
    used = [(row, i) for row, _, _ in plan.values() for i in range(sheet.rows[row].count)]
    cut = sheet.frames(sorted(used))
    hero = Sprite("hero_sakura", SIZE, cx=CX, ground=GROUND, scale=sheet.scale)
    for anim, (row, fps, loop) in plan.items():
        frames = [cut[(row, i)] for i in range(sheet.rows[row].count)]
        if anim == "ghost":
            frames = [draw.see_through(f, 180) for f in frames]     # the painted spirit, see-through
        hero.add(anim, frames, fps=fps, loop=loop)
    return hero


PAINTED = {"sakura": sakura}


def build() -> list[Sprite]:
    return [make() for make in PAINTED.values()]
