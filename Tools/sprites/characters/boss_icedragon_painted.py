"""Glacipurr, the World 2 ice dragon, and its projectiles, cut from the user's painted sheet (`sheet_boss.py`).

Source: `docs/concept/Glacipurr Ice Dragon Boss Sheet.png`, copied to `Tools/sprites/boss_icedragon_source.png`, painted
roughly to `docs/boss-icedragon-sheet-brief.md` with real transparency: one sheet (not the brief's two), far fewer
frames than the brief asks for, the dragon about 170 px wide sitting (not 400). Replaces the code-drawn
`boss_icedragon` (`boss_icedragon.py`) and `hazard_shard` and `hazard_ice_spike` (`boss_hazards.py`): those modules
skip a sprite whose name is in `NAMES`. `hazard_breath` stays code-drawn: the painted BREATH CLOUD is a round puff
about as tall as it is long, which would have to be drawn about three times taller than its low 40×12 hitbox.
Same sprite names, animation names, frame size (in points), anchor and ground row as the code-drawn dragon.
"""
from __future__ import annotations

from PIL import Image, ImageOps

from sheet_boss import BossSheet, Cut, best_shift, clean, fit_scale, shrink
from sprite import Sprite

SIZE = (190, 134)                 # points, as the code-drawn boss
CX, GROUND = 90, 130
SCALE = 3

SHEET = BossSheet(source="boss_icedragon_source.png", alpha=200, core=240)

LABELS = ((14, 7, 136, 38), (14, 148, 183, 179), (14, 307, 248, 339), (14, 470, 149, 502), (819, 503, 957, 535),
          (14, 645, 149, 676), (14, 695, 184, 727), (867, 696, 1070, 728), (15, 774, 184, 805), (867, 779, 1031, 811))


def _cut(box: tuple[int, int, int, int], pad: int = 4, **kw) -> Cut:
    x0, y0, x1, y1 = box
    return Cut((x0 - pad, y0 - pad, x1 + pad, y1 + pad), cleared=LABELS + tuple(kw.pop("cleared", ())), **kw)


# One cell per painted figure: its box at alpha 200, padded. The figures do not touch (a neighbour's wing tip or a
# loose ice chip inside a cell is a separate shape and drops), but BREATH 4's frost cone runs into BREATH 5 (the
# swoop in a cloud, not played): cut along the gap.
ROWS = {
    "idle": [_cut(b) for b in ((70, 19, 261, 145), (276, 19, 451, 143), (463, 19, 632, 143), (646, 21, 817, 144),
                               (831, 19, 993, 144), (1009, 21, 1176, 144), (1191, 22, 1348, 145),
                               (1363, 22, 1527, 145), (1542, 21, 1709, 145))],
    # The shards painted flying from the jaws of SHARD FAN 5 and 6 are separate shapes and drop.
    "shards": [_cut(b) for b in ((15, 188, 179, 300), (183, 184, 321, 299), (324, 183, 451, 299),
                                 (454, 188, 602, 299), (599, 177, 748, 300), (745, 178, 909, 300),
                                 (940, 171, 1106, 300), (1128, 179, 1274, 290), (1272, 198, 1391, 298),
                                 (1402, 195, 1540, 299), (1533, 202, 1646, 298), (1647, 205, 1757, 298))],
    "breath": [_cut((22, 349, 172, 458)), _cut((184, 338, 363, 447)), _cut((371, 337, 600, 458)),
               _cut((571, 337, 741, 448)), _cut((741, 332, 884, 470), pad=0),
               _cut((1419, 349, 1549, 464)), _cut((1567, 351, 1719, 461))],
    "dive": [_cut(b) for b in ((13, 511, 177, 636), (208, 473, 385, 591), (401, 488, 581, 630), (578, 494, 753, 655))],
    "hurt": [_cut(b) for b in ((171, 588, 288, 676), (328, 594, 450, 679))],
    "death": [_cut(b) for b in ((788, 548, 961, 663), (965, 526, 1165, 661), (1170, 547, 1334, 661),
                                (1338, 557, 1487, 660), (1483, 554, 1641, 660))]
             + [_cut((1644, 559, 1759, 663), alpha=120, core=200)],
}
EXTRA = {
    "shard": [_cut((x0, 726, x1, 790), pad=2, alpha=150, core=1) for x0, x1 in (
        (30, 120), (148, 248), (257, 366), (375, 477), (489, 599), (609, 730), (747, 853))],
    "spike": [_cut((x0, 788, x1, 879), pad=0, alpha=150, core=1) for x0, x1 in (
        (290, 360), (388, 457), (490, 560), (594, 664), (701, 772))],
}

# Points per sheet pixel: IDLE's dragon is painted about 125 px tall and 170-190 px long with its tail; at 0.8 it is
# about 100 points tall, as tall as the code-drawn dragon, its haunch, chest and mane over the 90×60 hitbox. At 3x
# detail every sheet pixel becomes 2.4 texture pixels (LANCZOS); the engine draws them with nearest filtering.
K = 0.84
# The painter drew the rows, and some frames within a row, at different sizes: each is scaled by this much on top of
# `K` to IDLE's size (measured from the height of the sitting frames and the size of the head and ears).
ROW_SIZE = {"shards": 1.03, "breath": 1.03, "dive": 0.9, "hurt": 1.2, "death": 0.92}
FRAME_SIZE = {("shards", 0): 1.08, ("shards", 8): 1.22, ("shards", 9): 1.1, ("shards", 10): 1.25, ("shards", 11): 1.27,
              ("breath", 0): 1.1, ("breath", 4): 1.15, ("breath", 5): 1.1, ("breath", 6): 1.1}
BAND = (10, 45)                   # points above the ground compared when lining frames up (chest and haunch)
REACH = 30                        # the most a frame is shifted to line up with the one before it (points)
AIR = {1: 30, 2: 14, 3: 0}        # DIVE frames in the air: points between the ground and the lowest pixel

# Animations: painted row, the painted frames played in order (a frame may be played again), fps, loop. GameScene
# plays an attack once from the start of its wind-up and holds the last frame, so played frame N (0-based) shows at
# N / fps seconds; the fps puts the release frames where the hazards leave (Bosses.json `boss_icedragon`):
#   shards: high shard at 0.8 s, low at 1.3 s, high at 1.8 s. SHARD FAN 5 (the first roar, the shards painted at
#           its jaws) shows at 3 / 4 = 0.75 s, 7 (lunging low, head down) at 1.25 s, 9 (roaring up) at 1.75 s.
#           SHARD FAN 1 and 3, near repeats of 2, are left out to fit the wind-up in 0.75 s.
#   breath: clouds at 0.9 and 1.9 s. BREATH 2 (the first full frost cone) at 2 / 2.2 = 0.91 s, BREATH 4 (the last
#           cone) at 1.82 s; then the two sitting frames in the pause. BREATH 5 (the swoop in a cloud) and the two
#           cloud-only frames are left out.
#   dive:   spikes at 1.0, 1.4 and 1.8 s. DIVE 3 (the wing sweep, ice streaks off the wing) at 5 / 5 = 1.0 s, 7 / 5
#           = 1.4 s and 9 / 5 = 1.8 s, DIVE 2 (wings raised) between; it lands on SHARD FAN 7's crouch at 2.2 s and
#           sits up (IDLE 0) for the pause.
PLAN = {
    "idle": ([("idle", i) for i in range(9)], 9, True),                              # 1 s a loop
    "shards": ([("shards", i) for i in (0, 2, 4, 5, 6, 7, 8, 9, 10, 11)], 4, False),  # 2.5 s
    "breath": ([("breath", i) for i in (0, 1, 2, 3, 4, 5, 6)], 2.2, False),            # 3.2 s
    "dive": ((("dive", 0), ("dive", 0), ("shards", 7), ("dive", 1), ("dive", 2), ("dive", 3), ("dive", 2),
              ("dive", 3), ("dive", 2), ("dive", 3), ("dive", 2), ("shards", 7), ("idle", 0)), 5, False),  # 2.6 s
    "hurt": ([("hurt", i) for i in range(2)], 8, True),                               # 0.25 s
    "death": ([("death", i) for i in range(6)], 6, False),                            # 1 s, ends frozen in ice
}

# Played DIVE frames drawn in the air (their lowest pixel above the ground row).
IN_AIR = {n for n, (row, i) in enumerate(PLAN["dive"][0]) if row == "dive" and AIR.get(i, 0)}


def _band(image: Image.Image, scale: int) -> Image.Image:
    """The rows `BAND` points above the image's bottom as a 1-bit mask (the chest and haunch, not the tail tip)."""
    lo, hi = BAND[0] * scale, BAND[1] * scale
    a = image.getchannel("A").point(lambda v: 255 if v else 0)
    out = Image.new("L", (a.width, hi - lo), 0)
    out.paste(a, (0, (hi - lo) - (a.height - lo)))
    return out.convert("1")


def _middle(image: Image.Image) -> float:
    """x of the centroid of `image`'s opaque pixels."""
    a = image.getchannel("A")
    hist = [0] * image.width
    px = a.load()
    for y in range(image.height):
        for x in range(image.width):
            if px[x, y]:
                hist[x] += 1
    return sum(x * n for x, n in enumerate(hist)) / sum(hist)


def boss() -> Sprite:
    fw, fh = SIZE[0] * SCALE, SIZE[1] * SCALE
    ground = GROUND * SCALE + SCALE - 1          # the lowest pixel row of point row GROUND
    centre = CX * SCALE + SCALE / 2
    reach = REACH * SCALE
    pieces = {name: [SHEET.cut(c) for c in cells] for name, cells in ROWS.items()}
    small = {name: [shrink(p.image, K * SCALE * FRAME_SIZE.get((name, i), ROW_SIZE.get(name, 1)))
                    for i, p in enumerate(ps)] for name, ps in pieces.items()}
    bands = {name: [_band(im, SCALE) for im in ims] for name, ims in small.items()}

    # Where each grounded frame's left edge goes (frame pixels): IDLE 0 with the middle of its chest-and-haunch band
    # on the anchor; every other frame lined up with IDLE 0 by that band (`best_shift`), so the body stays over the
    # hitbox in every frame and only real moves show. In-air DIVE frames keep their centroid on IDLE 0's.
    ref = bands["idle"][0]
    box = ref.getbbox()
    left0 = round(centre - (box[0] + box[2]) / 2)
    mid0 = left0 + _middle(small["idle"][0])
    lefts = {(name, i): left0 + best_shift(ref, m, reach) for name, ms in bands.items() for i, m in enumerate(ms)}
    for i in AIR:
        lefts[("dive", i)] = round(mid0 - _middle(small["dive"][i]))

    sprite = Sprite("boss_icedragon", SIZE, faces_left=True, cx=CX, ground=GROUND, scale=SCALE)
    for name, (plan, fps, loop) in PLAN.items():
        frames = []
        for row, i in plan:
            im = small[row][i]
            lift = AIR.get(i, 0) * SCALE if row == "dive" else 0
            x = min(max(lefts[(row, i)], 1), fw - 1 - im.width)     # BREATH 3, the longest, would touch the edge
            y = max(1, ground + 1 - im.height - lift)
            out = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
            out.paste(im, (x, y), im)
            frames.append(clean(out))
        sprite.add(name, frames, fps=fps, loop=loop)
    return sprite


def hazards() -> list[Sprite]:
    """The game's hazards fly left, leading with their left edge, their frame bottom on the hitbox bottom; each row at
    one size. ICE SHARD is painted pointing right (mirrored here) and about 3.5 times as long as it is tall with its
    trail: drawn as long as the frame (42 points for a 40×10 hitbox), its middle on the frame's middle row, the
    sparkles above and below cut at the frame's edge; the first, smaller painted shard is left out. ICE SPIKE is
    painted pointing up out of a burst of frost, as the code-drawn spike: the whole spike fits the 12×18 frame, its
    foot on the bottom row; the first painted spikes (still growing) and the last (melting) are left out."""
    s = SCALE

    shards = [SHEET.cut(c) for c in EXTRA["shard"][1:]]
    w, h = 42 * s, 12 * s
    k = 0.84 * w / max(p.image.width for p in shards)   # the crystal's top and bottom points stay in the frame
    flying = []
    for p in shards:
        im = ImageOps.mirror(shrink(p.image, k))
        frame = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        frame.paste(im, (0, round(h / 2 - im.height / 2)), im)
        flying.append(clean(frame))
    shard = Sprite("hazard_shard", (42, 12), scale=s)
    shard.add("fly", flying, fps=10)

    spikes = [SHEET.cut(c) for c in EXTRA["spike"]]
    w, h = 12 * s, 18 * s
    k = fit_scale(spikes, (w, h))
    rising = []
    for p in spikes:
        im = shrink(p.image, k)
        frame = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        frame.paste(im, ((w - im.width) // 2, h - im.height), im)
        rising.append(clean(frame))
    spike = Sprite("hazard_ice_spike", (12, 18), scale=s)
    spike.add("fly", rising, fps=8)
    return [shard, spike]


NAMES = {"boss_icedragon", "hazard_shard", "hazard_ice_spike"}


def build() -> list[Sprite]:
    return [boss(), *hazards()]
