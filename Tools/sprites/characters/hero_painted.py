"""Heroes cut from the user's painted sprite sheets (`sheet_hero.py`) instead of drawn in code.

Each entry of `PAINTED` is a cat id: `fluffy` is the base sprite `hero` itself; any other id replaces the
code-drawn skin `hero_<id>` in `hero.py`. Same animation names, loop flags, frame size (in points) and
anchor as the code-drawn hero (`hero.drawn_hero`, still the reference the code-drawn skins are checked
against). Frame counts are the painted ones (more in-betweens than the code-drawn hero), with the fps
set so each animation lasts about as long as the code-drawn hero's (`docs/hero-sheet-brief.md`,
"Lasts"). Frames are exported at 3x detail (132×108 PNGs, 44×36 points).

Sakura's sheet is painted to `docs/hero-sheet-brief.md`: every animation has its own row, cheer and peek
included. Her idle, run and menu come from a second, later painting (`SAKURA_V4`) cut to the
same standing height. Fluffy's lacks a few rows, played from his other painted frames.
"""
from __future__ import annotations

from dataclasses import replace

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


# Sakura's idle and run (and her menu): `docs/concept/Sakura Cat Pixel Sprite Sheet v4.png`, copied to
# `hero_sakura_v4_source.png`: rows IDLE (6), WALK (6) and RUN (labelled 8, 9 painted) on real transparency.
# A soft red-pink glow rings every cat, all of it semi-transparent (alpha under 200) outside her dark outline,
# as are the loose specks between the rows: at 200 only the cats and the label pills are left, the cats well
# apart. Boxes hold the cats only, below the pills. Painted bigger than v3 (about 160 px standing): cut at
# the scale that makes her as tall as the v3 idle (`sakura`), so she keeps her size from run to jump.
SAKURA_V4 = HeroSheet(
    source="hero_sakura_v4_source.png",
    rows={
        "idle": Row((10, 129, 1275, 300), 6, align="body"),
        # WALK (6, box (10, 388, 1500, 560)) is not cut: the game has no walk, and a walk cycle is no skid (stop)
        # nor a standing pose (menu).
        # Labelled 8, painted 9: two strides (1-5, 6-9); the 9th is no repeat of the 1st (the least alike of
        # all) and leads back into it as smoothly as any other step, so all nine play.
        "run": Row((10, 640, 1765, 820), 9),
    },
    frame=SIZE, cx=CX, alpha=200, min_area=1500,
)


def _standing_height(frames: list) -> int:
    """The median opaque height (exported pixels) of a standing animation's frames."""
    heights = sorted(f.getchannel("A").getbbox()[3] - f.getchannel("A").getbbox()[1] for f in frames)
    return heights[len(heights) // 2]


def sakura() -> Sprite:
    # Animation -> its row (every painted cat, in order), fps and loop. The fps keep each animation's
    # length near the hero's (the brief's "Lasts"): throw within the 0.25 s throw window, hurt one
    # cycle in the 0.3 s hurt window. The whole v3 plan is cut as before (its one scale depends on every
    # row), then idle, run and menu are replaced by the v4 painting at the v3 idle's standing height.
    v3 = _sakura_v3()
    sheet = replace(SAKURA_V4)
    painted_h = sorted(c.box[3] - c.box[1] for c in sheet.cats["idle"])
    sheet.fixed_scale = _standing_height(v3.anims["idle"].frames) / painted_h[len(painted_h) // 2]
    v4 = painted("hero_sakura", sheet, {
        "run": ("run", 16, True),                 # 9, 0.56 s per cycle (two strides)
        "idle": ("idle", 6, True),                # 6, 1 s; eyes open in every frame
        "menu": ("idle", 6, True),                # 6, 1 s: standing and breathing (v3's MENU winks)
    })
    v3.anims.update(v4.anims)
    return v3


def _sakura_v3() -> Sprite:
    return painted("hero_sakura", SAKURA, {
        "run": ("run", 27, True),           # 16 frames, 0.59 s per cycle (replaced by v4's)
        "stop": ("stop", 20, False),        # 8, 0.4 s
        "idle": ("idle", 8, True),          # 8, 1 s; the 8th blinks (replaced by v4's; sets her size)
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
        "menu": ("menu", 9, True),          # 9, 1 s; winks (replaced by v4's idle)
        "ko": ("ko", 5, True),              # 4, 0.8 s
        "ghost": ("ghost", 8, True),        # 8, 1 s
    })


def _shadow(p: tuple) -> bool:
    return max(p) - min(p) <= 20 and 60 <= max(p) <= 140


# Fluffy, the hero: `docs/concept/Fluffy Hero Sprite Sheet v4.png`, copied to `hero_fluffy_source.png`. A fluffy
# orange tabby with a red scarf and gold bell, painted on real transparency: the haze behind the rows is fully clear,
# the fur and dark outline opaque, the ground shadows semi-transparent. Every row of the brief is painted but STOP,
# two rows side by side on each line; the cats stand apart, and the sparkles, hearts and swirls are loose specks too
# small to count. Counts are the cats painted, which differ from the labels in four rows (marked).
FLUFFY = HeroSheet(
    source="hero_fluffy_source.png",
    rows={
        "idle": Row((15, 46, 680, 138), 7, align="body"),                                     # labelled 6; 6 winks
        "run": Row((683, 46, 1530, 138), 9),                                                   # labelled 8
        "dash": Row((15, 180, 760, 285), 6),
        # Take-off (0), rising leaps (1-3), tail flung up (4), a roll (5), landing (6).
        "jump": Row((765, 168, 1530, 285), 7, airborne=True, cleared=((765, 140, 925, 178),)),   # labelled 6
        "fall": Row((15, 326, 760, 440), 6, airborne=True),
        "double": Row((765, 326, 1530, 440), 6, airborne=True),
        # The yarn ball flying off the last cat is left outside the box.
        "throw": Row((15, 476, 700, 580), 6, cleared=((14, 440, 170, 481),)),
        # The last two land in dust clouds.
        "pounce": Row((765, 470, 1530, 580), 6, airborne=True, cleared=((765, 440, 940, 481),)),
        "hurt": Row((15, 620, 440, 712), 4),
        "death": Row((450, 620, 1000, 712), 4, align=False),
        "ko": Row((1030, 625, 1530, 712), 4),
        # No dark outline: a blue glow (alpha 200+ at its rim) round the pale body; see-through in `painted`.
        "ghost": Row((15, 756, 640, 860), 5, align="body", airborne=True),                     # labelled 6
        "sit": Row((650, 757, 1040, 860), 4, align="body"),
        "cheer": Row((1060, 755, 1520, 860), 4, align="body"),
        "menu": Row((15, 902, 410, 1000), 4, align="body"),
        # Behind a wooden box he rests his paws on: the box is part of the pose, so it stays. The first two boxes
        # touch: cut apart.
        "peek": Row((415, 905, 875, 1000), 4, align="body", splits=(532,)),
    },
    frame=SIZE, cx=CX, alpha=200, min_area=1500,
    drop=_shadow,
    max_scale=1.36, own_scale=("dash",),
    size_to="idle", size_skip=("death", "ko"),
    max_lift=3,
)


def fluffy() -> Sprite:
    # As Sakura's: the fps keep each animation's length near the code-drawn hero's. Some animations play only part of
    # their row (the fourth item: indices in the row), and STOP, not painted, borrows IDLE's frames.
    return painted("hero", FLUFFY, {
        "run": ("run", 14, True, range(8)),             # 8, 0.57 s per cycle: the 9th repeats the first
        "stop": ("idle", 10, False, (0, 1, 2, 3)),      # 4, 0.4 s: no skid painted, so he settles into idle
        "idle": ("idle", 6, True, range(6)),            # 6, 1 s: the 7th winks
        "jump": ("jump", 12, True, (1, 2, 3)),          # 3, 0.25 s: rising (the roll and landing left out)
        "fall": ("fall", 24, True),                     # 6, 0.25 s
        "double": ("double", 24, True),                 # 6, 0.25 s: the forward flip
        "throw": ("throw", 24, False),                  # 6, 0.25 s
        "dash": ("dash", 24, True),                     # 6, 0.25 s
        "pounce": ("pounce", 12, True, (0, 1, 2, 3)),   # 4, 0.33 s: the leap, without the dusty landings
        "hurt": ("hurt", 13, True),                     # 4, 0.31 s
        "death": ("death", 5, False),                   # 4, 0.8 s
        "peek": ("peek", 4, True),                      # 4, 1 s
        "cheer": ("cheer", 8, True),                    # 4, 0.5 s
        "sit_happy": ("sit", 6, True),                  # 4, 0.67 s
        "menu": ("menu", 4, True),                      # 4, 1 s
        "ko": ("ko", 6, True),                          # 4, 0.67 s
        "ghost": ("ghost", 6, True),                    # 5, 0.83 s
    })


# Sharky: `docs/concept/Sharky Cat Pixel Sprite Sheet v2.png`, copied to `hero_sharky_source.png`. A calico kitten in
# a whole shark onesie, painted on real transparency: a blue haze behind the rows (alpha under 200), the cats and their
# dark outline opaque, no ground shadows. The rows sit two or three to a line, the cats well apart; hearts, stars and
# the throw's water flicks are loose specks too small to count. No STOP, POUNCE, MENU or PEEK row is painted, and the
# EFFECTS row (waves, splashes, bubbles) is not cut: `skin_abilities.py` draws Sharky's water. The pills of the jump,
# fall, sit and cheer rows reach down into their boxes and are cleared.
SHARKY = HeroSheet(
    source="hero_sharky_source.png",
    rows={
        "idle": Row((8, 42, 622, 162), 6, align="body"),
        "run": Row((632, 42, 1535, 162), 8),
        # Crouched take-off (0), then three rising leaps.
        "jump": Row((8, 196, 456, 345), 4, airborne=True, cleared=((10, 175, 128, 208),)),
        "fall": Row((466, 200, 922, 356), 4, airborne=True, cleared=((448, 175, 558, 208),)),
        # The forward roll; the blue swirl arcs round it are thin specks left behind.
        "double": Row((930, 212, 1530, 354), 6, airborne=True),
        # Belly down on a surf of spray. The spray behind the tail is trimmed (the game draws its own water slide
        # under the dash, `skin_abilities.py`), what is left is still wide, so the row is scaled on its own.
        "dash": Row((20, 403, 1410, 502), 6,
                    trim_left={0: 52, 1: 270, 2: 490, 3: 726, 4: 983, 5: 1240}),
        "throw": Row((10, 550, 530, 676), 4),
        "hurt": Row((575, 555, 965, 680), 3),
        "death": Row((995, 570, 1532, 672), 4, align=False),
        "sit": Row((8, 708, 475, 853), 4, align="body", cleared=((8, 686, 182, 720),)),
        "cheer": Row((495, 706, 958, 853), 4, align="body", cleared=((490, 686, 620, 720),)),
        "ko": Row((975, 740, 1532, 853), 4),
        # No dark outline: a pale blue spirit glowing at its rim; see-through in `painted`.
        "ghost": Row((12, 902, 692, 1006), 6, align="body", airborne=True),
    },
    frame=SIZE, cx=CX, alpha=200, min_area=1500,
    max_scale=1.36, own_scale=("dash",),
    size_to="idle", size_skip=("death", "ko"),
    max_lift=3,
)


# The plan of the costume sheets (Sharky, Cabbage), painted to the same rows and counts. As Fluffy's: the fps keep each
# animation's length near the code-drawn hero's. STOP and MENU borrow IDLE's frames, POUNCE the leap of JUMP, and PEEK
# (no box painted) the standing IDLE.
COSTUME_PLAN = {
    "run": ("run", 14, True),                       # 8, 0.57 s per cycle
    "stop": ("idle", 10, False, (0, 1, 2, 3)),      # 4, 0.4 s: no skid painted, so it settles into idle
    "idle": ("idle", 6, True),                      # 6, 1 s
    "jump": ("jump", 12, True, (1, 2, 3)),          # 3, 0.25 s: rising (the crouched take-off left out)
    "fall": ("fall", 16, True),                     # 4, 0.25 s
    "double": ("double", 24, True),                 # 6, 0.25 s: the forward roll
    "throw": ("throw", 16, False),                  # 4, 0.25 s
    "dash": ("dash", 24, True),                     # 6, 0.25 s
    "pounce": ("jump", 12, True),                   # 4, 0.33 s: the whole leap, take-off included
    "hurt": ("hurt", 10, True),                     # 3, 0.3 s
    "death": ("death", 5, False),                   # 4, 0.8 s
    "peek": ("idle", 6, True),                      # 6, 1 s
    "cheer": ("cheer", 8, True),                    # 4, 0.5 s
    "sit_happy": ("sit", 6, True),                  # 4, 0.67 s
    "menu": ("idle", 6, True),                      # 6, 1 s
    "ko": ("ko", 6, True),                          # 4, 0.67 s
    "ghost": ("ghost", 7, True),                    # 6, 0.86 s
}


def sharky() -> Sprite:
    return painted("hero_sharky", SHARKY, COSTUME_PLAN)


# Cabbage: `docs/concept/Cabbage Cat Pixel Sprite Sheet v2.png`, copied to `hero_cabage_source.png`. A calico kitten in
# a leafy cabbage onesie, painted to the same plan as Sharky's sheet: a green haze behind the rows and soft ground
# shadows (alpha under 200), the cats opaque and well apart; the stars, swirls and loose leaves are specks too small to
# count. No STOP, POUNCE, MENU or PEEK row, and the EFFECTS row is not cut. The pills of the jump and cheer rows reach
# down into their boxes and are cleared.
CABAGE = HeroSheet(
    source="hero_cabage_source.png",
    rows={
        "idle": Row((10, 42, 650, 163), 6, align="body"),
        "run": Row((662, 42, 1530, 163), 8),
        # Crouched take-off (0), then three rising leaps.
        "jump": Row((10, 198, 450, 340), 4, airborne=True, cleared=((10, 175, 136, 212),)),
        "fall": Row((460, 212, 915, 350), 4, airborne=True),
        "double": Row((918, 212, 1525, 350), 6, airborne=True),
        # Belly down with a green streak behind: the row is scaled on its own.
        "dash": Row((40, 405, 1405, 502), 6),
        "throw": Row((10, 548, 520, 672), 4),
        "hurt": Row((552, 552, 965, 672), 3),
        "death": Row((992, 560, 1525, 672), 4, align=False),
        "sit": Row((10, 724, 470, 853), 4, align="body"),
        "cheer": Row((498, 716, 960, 853), 4, align="body", cleared=((494, 686, 622, 721),)),
        "ko": Row((975, 755, 1525, 856), 4),
        # No dark outline: a pale green spirit glowing at its rim; see-through in `painted`.
        "ghost": Row((12, 903, 692, 1008), 6, align="body", airborne=True),
    },
    frame=SIZE, cx=CX, alpha=200, min_area=1500,
    max_scale=1.36, own_scale=("dash",),
    size_to="idle", size_skip=("death", "ko"),
    max_lift=3,
)


def cabage() -> Sprite:
    # Sharky's plan: both sheets are painted to the same rows and counts.
    return painted("hero_cabage", CABAGE, COSTUME_PLAN)


def painted(name: str, sheet: HeroSheet, plan: dict) -> Sprite:
    """The sprite `name` from `sheet`: per animation (row, fps, loop[, picks]), the painted cats of the row in
    order: every one, or only those whose indices are in `picks`."""
    picks = {anim: tuple(entry[3]) if len(entry) > 3 else tuple(range(sheet.rows[entry[0]].count))
             for anim, entry in plan.items()}
    used = sorted({(entry[0], i) for anim, entry in plan.items() for i in picks[anim]})
    cut = sheet.frames(used)
    hero = Sprite(name, SIZE, cx=CX, ground=GROUND, scale=sheet.scale)
    for anim, (row, fps, loop, *_) in plan.items():
        frames = [cut[(row, i)] for i in picks[anim]]
        if anim == "ghost":
            frames = [draw.see_through(f, 180) for f in frames]     # the painted spirit, see-through
        hero.add(anim, frames, fps=fps, loop=loop)
    return hero


PAINTED = {"fluffy": fluffy, "sakura": sakura, "sharky": sharky, "cabage": cabage}


def sprite_name(cat: str) -> str:
    """The sprite a painted cat is exported as: Fluffy is the hero itself, the others its skins."""
    return "hero" if cat == "fluffy" else f"hero_{cat}"


def build() -> list[Sprite]:
    return [make() for make in PAINTED.values()]
