"""The Great Squirrel King and his projectiles, cut from the user's painted sheet (`sheet_boss.py`).

Source: `docs/concept/Squirrel King Boss Sheet.png`, copied to `Tools/sprites/boss_squirrel_source.png`, painted
after `docs/boss-squirrel-sheet-brief.md` as one sheet with real transparency (the glow and dust semi-transparent),
no labels. Replaces the code-drawn `boss_squirrel` (`boss_squirrel.py`) and `hazard_acorn`, `hazard_acorn_high`,
`hazard_giant_acorn` and `hazard_shockwave` (`boss_hazards.py`): those modules skip a sprite whose name is in
`NAMES`. Same sprite names, animation names, loop flags and ground row; the frame is wider (150×132 points instead
of 112×132) because the painted king, tail and sceptre included, is about 130 points wide at the size where his
body fills the 56×84 hitbox.

What is painted, row by row (counted on the sheet, numbered from 1 as in the brief):
1. 9 frames: standing with the sceptre, breathing (IDLE).
2. 12 frames: reaching (1-3), the sceptre thrust forward (4), drawing back (5), the paw flung forward (6), leaning
   back (7), a low lunge with the sceptre forward (8), crouched low and glaring (9-11), the sceptre swung down onto
   the ground in front (12); with 7 flying acorns painted above 8-12 (not cut: the projectile row has them).
3. 11 frames: an acorn at the belly (1), the sceptre held out (2), a giant crowned acorn heaved overhead (3, 4),
   rolled into a ball in his cape with dust behind (5-8), standing up again (9-11).
4. 12 frames: wincing (1, 2), dizzy with stars (3, 4), sinking (5-7), flat and dizzy (8, 9), face down with the crown
   off (10-12).
5. 10 small flying acorns with short trails; 7 big ones with long trails.
6. 8 giant crowned acorns (1-4 glowing, 5-8 landing with debris); 8 frames of a rolling dust wave.
7. Loose effects (sparkles, puffs, leaves, pebbles, a ring, a crown, stars): not cut.
"""
from __future__ import annotations

from PIL import Image, ImageOps

from sheet_boss import BossSheet, Cut, best_shift, body_mask, cells, clean, shrink
from sprite import Sprite

SIZE = (164, 132)                 # points (the code-drawn boss was 112×132)
CX, GROUND = 95, 128              # facing right, as painted; the ground row as the code-drawn boss
SCALE = 3

SHEET = BossSheet(source="boss_squirrel_source.png", alpha=200, core=240)

# The flying acorns painted above ROW 2's frames 8-12, wiped from those cells.
ACORNS_ABOVE = ((940, 140, 1774, 189),)


def _row(y0: int, y1: int, edges: list[int], extra: dict | None = None, **kw) -> list[Cut]:
    return cells(y0, y1, edges, (), extra, **kw)


# One cell per painted frame (sheet x edges about halfway between the figures). The figures touch or overlap their
# neighbours (a sceptre over the next tail): with `seeds`, every figure near a cell grows at once from its own middle
# over the painting (a watershed along the dark outlines), so each keeps what is nearest to it.
ROWS = {
    "idle": _row(4, 140, [5, 190, 377, 560, 743, 927, 1113, 1298, 1483, 1680], seeds=15),
    "row2": _row(142, 277, [5, 163, 303, 428, 559, 690, 818, 955, 1080, 1186, 1291, 1404, 1580], seeds=15,
                 extra={i: ACORNS_ABOVE for i in range(7, 12)}),
    "row3": _row(280, 424, [5, 145, 298, 431, 566, 692, 828, 967, 1113, 1290, 1488, 1680], seeds=15),
    "row4": _row(426, 556, [5, 146, 307, 451, 585, 715, 856, 987, 1121, 1278, 1443, 1592, 1765], seeds=15),
}
EXTRA = {
    "acorn": _row(568, 650, [20, 105, 195, 287, 383, 482, 578, 662, 740, 808, 870], alpha=150, core=1),
    "acorn_high": _row(568, 650, [880, 1050, 1180, 1310, 1440, 1560, 1680, 1774], alpha=150, core=1),
    "giant": _row(620, 760, [15, 120, 222, 323, 425, 520, 618, 725, 840], alpha=150, core=1),
    "wave": _row(680, 760, [850, 925, 1025, 1160, 1280, 1418, 1535, 1660, 1765], alpha=150, core=1),
}

# Points per sheet pixel: the king's body and head (crown, tail and sceptre aside) fill the 56×84 hitbox, as the
# code-drawn king's did; he stands about 100 points tall with the crown (122 sheet px).
K = 0.8
BODY = 60                         # points above the ground compared when lining frames up
REACH = 30                        # the most a frame is shifted to line up with the one before it (points)
# IDLE 1's chest (sheet x): put on the anchor, so the hitbox sits on the body and the tail sticks out behind.
CHEST = 129
# Crouched, he folds back toward his tail and the body leaves the front of the hitbox (where the yarn hits): these
# frames are moved this many points toward the kitten, so the front of the body stays near the hitbox's front edge.
NUDGE = {**{("row2", i): d for i, d in ((6, 6), (7, 10), (8, 14), (9, 14), (10, 14), (11, 10))},
         **{("row3", i): 12 for i in range(4, 8)}, ("row4", 8): 8, ("row4", 9): 12}
CLOSE = ("idle", "row3")   # rows whose drift is spread so they end where IDLE 1 stands

# The projectiles (points): the nut of the low acorn about 10 across (its hitbox 10×10), of the high one about 13
# (14×12), the giant acorn's shell about 17 wide and, with its cap, 23 tall (18×22); how much of each flying acorn
# is kept from its leading edge (sheet px: the nut and a stub of the trail).
ACORN_NUT, ACORN_HIGH_NUT, GIANT_SHELL = 10, 13, 17
ACORN_LEAD, ACORN_HIGH_LEAD = 36, 46

# Animations: (painted row, frame) in playing order, fps, loop; the lists count frames from 0, the notes from 1 as the
# docstring. GameScene plays an attack
# once from the start of its wind-up and holds the last frame until the boss rests, so entry N shows at N / fps
# seconds. The entries are placed so each release shows when Bosses.json's `boss_squirrel` lets its hazard go (times
# from the start of the wind-up), and every attack ends before the boss's next wind-up (ActorNode does not restart an
# animation that is still playing):
#   throw (acorn_arc, 3.2 s from wind-up to the next): ROW 2 1-8, then ROW 3 9 and 11 (standing up again), at 3.34
#         fps: the sceptre thrust (ROW 2 4) at 3 / 3.34 = 0.90 s (low acorn 0.9 s), the paw flung forward (6) at
#         1.50 s (high acorn 1.5 s), the low lunge with the sceptre (8) at 2.10 s (low acorn 2.1 s); ends at 3.0 s.
#   roll (acorn_roll, 3.3 s): leaning back and crouching (ROW 2 7, 9-11) over the 0.9 s wind-up, then the ball
#         (ROW 3 5-8, a spin, so its four poses repeat) from entry 9 (0.9 s, the first acorn) through entry 23
#         (2.3 s, the third; the second at 1.6 s), then standing up (ROW 3 9, 11); 10 fps, ends at 2.8 s.
#   climb (giant_acorn, 3.7 s): the sceptre held out (ROW 3 2), the giant acorn heaved overhead and trembling (ROW 3
#         3 and 4 in turn), gone from his paws at entry 10 (1.0 s, the giant acorn appears ahead of the kitten),
#         watching (ROW 3 9), crouching (ROW 2 7, 9-11), the sceptre slammed down in front (ROW 2 12) at entry 26
#         (2.6 s, the shockwave leaves), standing up (ROW 3 9, 11); 10 fps, ends at 3.2 s.
# No climbing, jump or landing is painted: CLIMB keeps its name (GameScene plays it for giant_acorn) but shows the
# heave and a sceptre slam. HURT is the one wince that keeps the sceptre (ROW 4 2), held for the 0.25 s GameScene
# shows it; DEATH is the rest of ROW 4 (3-12: dizzy, sinking, flat on his face, the crown off), ending on the last.
def _rep(row: str, frame: int, n: int) -> list:
    return [(row, frame)] * n


THROW = [*(("row2", i) for i in range(8)), ("row3", 8), ("row3", 10)]
ROLL = [*_rep("row2", 6, 2), *_rep("row2", 8, 2), *_rep("row2", 9, 2), *_rep("row2", 10, 3),
        *(("row3", 4 + i % 4) for i in range(15)), *_rep("row3", 8, 3), ("row3", 10)]
CLIMB = [*_rep("row3", 1, 4), *(("row3", 2 + i % 2) for i in range(6)), *_rep("row3", 8, 6),
         *_rep("row2", 6, 2), *_rep("row2", 8, 2), *_rep("row2", 9, 2), *_rep("row2", 10, 4),
         *_rep("row2", 11, 3), *_rep("row3", 8, 2), ("row3", 10)]
PLAN = {
    "idle": ([("idle", i) for i in range(9)], 9, True),             # 1.0 s a loop
    "throw": (THROW, 3.34, False),
    "roll": (ROLL, 10, False),
    "climb": (CLIMB, 10, False),
    "hurt": ([("row4", 1)], 12, True),
    "death": ([("row4", i) for i in range(2, 12)], 10, False),      # 1.0 s, ends lying flat
}
# The release entries (index into the list): checked in the tests against Bosses.json's hazard times.
RELEASES = {"throw": (3, 5, 7), "roll": (9, 16, 23), "climb": (10, 26)}


def boss() -> Sprite:
    fw, fh = SIZE[0] * SCALE, SIZE[1] * SCALE
    ground = GROUND * SCALE + SCALE - 1          # the lowest pixel row of point row GROUND
    centre = CX * SCALE + SCALE / 2
    body, reach = BODY * SCALE, REACH * SCALE
    k = K * SCALE
    pieces = {name: [SHEET.cut(c) for c in row] for name, row in ROWS.items()}
    small = {name: [shrink(p.image, k) for p in ps] for name, ps in pieces.items()}
    masks = {name: [body_mask(im, body) for im in ims] for name, ims in small.items()}

    # Where each painted frame's left edge goes, from the anchor (frame pixels), the same in every animation that
    # plays it: IDLE 1 with its chest on the anchor; every other frame lined up with the one painted before it (each
    # row's first with IDLE 1), so the body stays put and only real moves (a crouch, a lunge) show. IDLE (a loop) and
    # ROW 3 (ending as he stands) spread the drift they gather over their frames, so they close on IDLE 1.
    ref = masks["idle"][0]
    offset = {}
    for name in ROWS:
        ms = masks[name]
        if name == "idle":
            xs = [-(CHEST - pieces["idle"][0].box[0]) * k]
        else:
            xs = [offset[("idle", 0)] + best_shift(ref, ms[0], reach)]
        for a, b in zip(ms, ms[1:]):
            xs.append(xs[-1] + best_shift(a, b, reach))
        if name in CLOSE:
            if name == "idle":             # a loop: the frame after the last is IDLE 1 again
                end, n = xs[-1] + best_shift(ms[-1], ref, reach) - xs[0], len(xs)
            else:
                end, n = xs[-1] - (offset[("idle", 0)] + best_shift(ref, ms[-1], reach)), len(xs) - 1
            xs = [x - end * i / n for i, x in enumerate(xs)]
        offset.update({(name, i): x + NUDGE.get((name, i), 0) * SCALE for i, x in enumerate(xs)})

    sprite = Sprite("boss_squirrel", SIZE, faces_left=True, cx=CX, ground=GROUND, scale=SCALE)
    for name, (plan, fps, loop) in PLAN.items():
        frames = []
        for key in plan:
            im = small[key[0]][key[1]]
            x = round(centre + offset[key])
            if not 1 <= x <= fw - 1 - im.width:
                raise ValueError(f"boss_squirrel {name} {key}: {x}..{x + im.width} leaves the frame (0..{fw})")
            out = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
            out.paste(im, (x, ground + 1 - im.height), im)
            frames.append(clean(out))
        sprite.add(name, frames, fps=fps, loop=loop)
    return sprite


def hazards() -> list[Sprite]:
    """Painted flying right (the trail and the dust's back on the left), mirrored here to point left, the way they
    fly, as the game draws hazards (not mirrored on export). Each row at one scale, the solid part about the size of
    its Bosses.json hitbox, centred on the frame (the hitbox's middle) and standing on the bottom row; only trails and
    glow stick out of the hitbox."""
    s = SCALE

    def turned(row: str, picks) -> list[Image.Image]:
        return [ImageOps.mirror(SHEET.cut(EXTRA[row][i]).image) for i in picks]

    def framed(images: list[Image.Image], k: float, size: tuple[int, int], left: float | None = None) -> list:
        # Scaled by `k`, bottom on the bottom row; centred, or with the leading edge at point column `left`.
        out = []
        for im in images:
            small = shrink(im, k)
            frame = Image.new("RGBA", (size[0] * s, size[1] * s), (0, 0, 0, 0))
            x = round(left * s) if left is not None else (frame.width - small.width) // 2
            frame.paste(small, (x, frame.height - small.height), small)
            out.append(clean(frame))
        return out

    def hazard(name: str, size: tuple[int, int], frames: list, fps: int) -> Sprite:
        sprite = Sprite(f"hazard_{name}", size, scale=s)
        sprite.add("fly", frames, fps=fps)
        return sprite

    # The acorns: the round nut leads (about 30 sheet px across); a stub of its fiery trail is kept behind it.
    low = [im.crop((0, 0, ACORN_LEAD, im.height)) for im in turned("acorn", (1, 3, 5, 7))]
    low = [im.crop(im.getbbox()) for im in low]
    k_low = min(fit_scale_images(low, (12 * s, 12 * s)), ACORN_NUT * s / 30)
    high = [im.crop((0, 0, ACORN_HIGH_LEAD, im.height)) for im in turned("acorn_high", (1, 2, 3, 4))]
    high = [im.crop(im.getbbox()) for im in high]
    k_high = min(fit_scale_images(high, (18 * s - 2 * s, 14 * s)), ACORN_HIGH_NUT * s / 30)
    giant = turned("giant", range(4))
    k_giant = min(fit_scale_images(giant, (28 * s, 34 * s)), GIANT_SHELL * s / 56)
    wave = turned("wave", range(1, 5))
    k_wave = fit_scale_images(wave, (24 * s, 12 * s))
    return [hazard("acorn", (12, 12), framed(low, k_low, (12, 12)), 14),
            hazard("acorn_high", (18, 14), framed(high, k_high, (18, 14), left=2), 14),
            hazard("giant_acorn", (28, 34), framed(giant, k_giant, (28, 34)), 8),
            hazard("shockwave", (24, 12), framed(wave, k_wave, (24, 12)), 12)]


def fit_scale_images(images: list[Image.Image], box: tuple[int, int]) -> float:
    """The one scale at which every image fits `box` (pixels)."""
    return min(min(box[0] / im.width, box[1] / im.height) for im in images)


NAMES = {"boss_squirrel", "hazard_acorn", "hazard_acorn_high", "hazard_giant_acorn", "hazard_shockwave"}


def build() -> list[Sprite]:
    return [boss(), *hazards()]
