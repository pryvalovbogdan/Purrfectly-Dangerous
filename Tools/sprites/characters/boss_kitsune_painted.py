"""The Blossom Kitsune Guardian and its projectiles, cut from the user's painted sheet (`sheet_boss.py`).

Source: `docs/concept/Kitsune Sakura Boss Sprite Sheet v2.png`, copied to `Tools/sprites/boss_kitsune_source.png`,
painted to `docs/boss-kitsune-sheet-brief.md` with real transparency (the pink haze is semi-transparent). Replaces
the code-drawn `boss_kitsune` (`boss_kitsune.py`), `hazard_claw_slash`, `hazard_bloom_shot`,
`hazard_bloom_shot_high` (`boss_hazards.py`) and `sakura_spirit` (`sakura_critters.py`): those modules skip a
sprite whose name is in `NAMES`. Same sprite names, animation names, frame sizes (in points) and anchors.
"""
from __future__ import annotations

from dataclasses import replace

from PIL import Image, ImageOps

from sheet_boss import BossSheet, Cut, best_shift, body_mask, cells, clean, fit, fit_scale, shrink
from sprite import Sprite

SIZE = (150, 120)                 # points, as the code-drawn boss
CX, GROUND = 72, 116
SCALE = 3

SHEET = BossSheet(source="boss_kitsune_source.png", alpha=200, core=240)

LABELS = ((11, 5, 138, 34), (11, 159, 156, 188), (11, 311, 166, 340), (11, 452, 182, 482), (11, 618, 153, 648),
          (400, 618, 556, 648), (11, 773, 208, 803), (554, 773, 756, 803), (1013, 773, 1251, 803),
          (11, 883, 301, 913), (685, 881, 977, 911))    # the label pills, wiped wherever a cell overlaps one


def _row(y0: int, y1: int, edges: list[int], extra: dict | None = None, **kw) -> list[Cut]:
    return cells(y0, y1, edges, LABELS, extra, **kw)


# CLAW: the strike (frame 11) trails its crescent behind it, close to frame 10's raised paw; in the follow-through
# each frame's fading crescent reaches under the muzzle of the frame before. Split along these lines (sheet x, y).
_CRESCENT = ((893, 204), (913, 250), (918, 267))
_MUZZLE_12 = ((1027, 236), (1025, 255), (1022, 280), (1013, 300))
_MUZZLE_13 = ((1100, 215), (1104, 245), (1107, 265), (1106, 280), (1100, 295))

# One cell per painted frame (sheet boxes between consecutive x edges).
ROWS = {
    "idle": _row(34, 156, [8, 120, 223, 324, 427, 533, 640, 748, 857, 970, 1081, 1191, 1302], pad=14),
    # The strike (11) trails its crescent behind it, over the gap to frame 10: frame 10 loses the crescent's tip.
    # In the follow-through each frame's fading crescent reaches under the muzzle of the frame before: the cells
    # overlap there and each wipes the other's part.
    "claw": [*_row(150, 308, [8, 106, 190, 273, 355, 436, 512, 588, 666, 747, 826, 916],
                   {1: (("r", ((191, 0), (191, 1024))),), 2: (("l", ((191, 0), (191, 1024))),), 10: (("r", _CRESCENT),)},
                   pad=14),
             Cut((886, 150, 1030, 308), cleared=(("l", _CRESCENT), ("r", _MUZZLE_12))),
             Cut((1010, 150, 1110, 308), cleared=(("l", _MUZZLE_12), ("r", _MUZZLE_13))),
             Cut((1095, 150, 1204, 308), cleared=(("l", _MUZZLE_13),)),
             *_row(150, 308, [1176, 1275, 1358, 1447, 1530], pad=14)],
    "bloom": _row(310, 450, [8, 118, 211, 303, 388, 466, 552, 637, 722, 810, 904, 998, 1101, 1202, 1297, 1395,
                             1515], pad=14),
    # The swirl (frames 7-11) is fainter than the fox: cut there at a lower alpha, so more of it shows.
    "summon": [replace(c, alpha=170) if 7 <= i <= 11 else c for i, c in enumerate(
        _row(450, 615, [8, 112, 212, 303, 400, 500, 588, 677, 767, 866, 968, 1060, 1151, 1243, 1328, 1424, 1530],
             pad=14))],
    "hurt": _row(610, 768, [8, 122, 240, 370]),
    "death": _row(610, 768, [380, 504, 610, 723, 837, 943, 1035, 1122, 1200, 1288, 1366, 1440, 1530], keep_all=True, pad=14),
}
EXTRA = {
    "slash": _row(800, 884, [12, 105, 195, 280, 365, 450, 545], alpha=150, core=1),
    "shot": _row(800, 884, [556, 617, 673, 725, 776, 826, 876, 928, 1000], alpha=150, core=1),
    "shot_high": _row(800, 884, [1005, 1077, 1143, 1204, 1260, 1320, 1384, 1446, 1515], alpha=150, core=1),
    "float": _row(912, 1020, [15, 104, 173, 255, 332, 413, 500, 578, 680], alpha=150, core=1),
    # The last petals are fainter: cut at a lower alpha so the burst fades instead of vanishing.
    "spirit_death": [replace(c, alpha=100) if i >= 3 else c for i, c in enumerate(
        _row(912, 1020, [680, 776, 866, 980, 1090, 1200, 1300], alpha=150, core=1, keep_all=True, min_bits=12))],
}

# Points per sheet pixel: the fox keeps the size of the first painted kitsune in the game (about 86 points wide
# sitting, haunch, chest and neck filling the 50×70 hitbox). The v2 fox is painted about 100 px wide, so at 3x
# detail every sheet pixel becomes 2.5 texture pixels (LANCZOS); the engine draws them with nearest filtering.
K = 0.83
# The painter drew some rows a little smaller than IDLE (the same head and scarf, smaller): those rows are scaled up
# by this much on top of `K`, so the fox keeps one size when GameScene switches animations. BLOOM's last frame
# (sitting up again) is painted at IDLE's size, the rest of the row smaller.
ROW_SIZE = {"claw": 1.1, "bloom": 1.12}
FRAME_SIZE = {("bloom", 15): 1.0}
BODY = 60                         # points above the ground compared when lining frames up (skips antlers and glow)
CHEST = 6                         # IDLE 0's middle sits this far toward the head from the middle of its lower body
REACH = 30                        # the most a frame is shifted to line up with the one before it (points)

# Animations: painted row, fps, loop. Every painted frame plays once, in order. GameScene plays an attack once from
# the start of its wind-up and holds the last frame, so painted frame N (0-based) shows at N / fps seconds; the fps
# puts the strike frame where the projectile leaves (Bosses.json `boss_kitsune`):
#   claw: strike 11 (the lunge through the crescent) at 11 / 9.17 = 1.20 s (claw_slash's slash leaves at 1.3 s,
#         double_claw's first at 1.2 s);
#   bloom: release 11 (the burst at the mouth) at 11 / 10 = 1.10 s (bloom_shots 1.2 s, bloom_volley 1.0 s);
#   summon: release 10 (the swirl at its fullest) at 10 / 8 = 1.25 s (the first spirit at 1.3 s).
PLAN = {
    "idle": (12, True),           # 12 frames: 1.0 s a loop
    "claw": (9.17, False),        # 18 frames
    "bloom": (10, False),         # 16 frames
    "summon": (8, False),         # 16 frames
    "hurt": (9, True),            # 3 frames: 0.33 s
    "death": (10, False),         # 12 frames: 1.2 s, ends on the petal pile
}


def boss() -> Sprite:
    fw, fh = SIZE[0] * SCALE, SIZE[1] * SCALE
    ground = GROUND * SCALE + SCALE - 1          # the lowest pixel row of point row GROUND
    centre = CX * SCALE + SCALE / 2
    body, reach = BODY * SCALE, REACH * SCALE
    pieces = {name: [SHEET.cut(c) for c in cells] for name, cells in ROWS.items()}
    small = {name: [shrink(p.image, K * SCALE * FRAME_SIZE.get((name, i), ROW_SIZE.get(name, 1)))
                    for i, p in enumerate(ps)] for name, ps in pieces.items()}
    masks = {name: [body_mask(im, body) for im in ims] for name, ims in small.items()}

    # Where each frame's left edge goes (frame pixels): IDLE 0 with its body (haunch, chest, neck) on the anchor; every
    # other frame lined up with the one before it (each row's first and last frame with IDLE 0), so the body stays
    # put between frames and animations and only real moves (a rear, a lunge, a recoil) show. The small drift a
    # row gathers along the way is spread over its frames, so its last frame lands where IDLE 0 stands.
    ref = masks["idle"][0]
    box = ref.getbbox()
    lefts = {"idle": [round(centre - (box[0] + box[2]) / 2 - CHEST * SCALE)]}
    for name in ROWS:
        ms = masks[name]
        xs = lefts.get(name) or [lefts["idle"][0] + best_shift(ref, ms[0], reach)]
        for a, b in zip(ms, ms[1:]):
            xs.append(xs[-1] + best_shift(a, b, reach))
        end = lefts["idle"][0] + best_shift(ref, ms[-1], reach) if name != "death" else xs[-1]
        if name == "idle":                   # a loop: the frame after the last is IDLE 0 again
            end = xs[-1] + best_shift(ms[-1], ref, reach) - lefts["idle"][0]
            xs = [round(x - end * i / len(xs)) for i, x in enumerate(xs)]
        else:
            n = len(xs) - 1
            xs = [round(x + (end - xs[-1]) * i / n) for i, x in enumerate(xs)]
        lefts[name] = xs

    sprite = Sprite("boss_kitsune", SIZE, faces_left=True, cx=CX, ground=GROUND, scale=SCALE)
    for name, (fps, loop) in PLAN.items():
        frames = []
        for im, x in zip(small[name], lefts[name]):
            x = min(max(x, 1), fw - 1 - im.width)            # the crescent's tip would touch the frame's edge
            out = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
            out.paste(im, (x, ground + 1 - im.height), im)
            frames.append(clean(out))
        sprite.add(name, frames, fps=fps, loop=loop)
    return sprite


def hazards() -> list[Sprite]:
    """Painted pointing left (the way they fly), as the game draws hazards: not mirrored. The crescent fills its frame
    at one size, leading edge on the left, bottom on the bottom row; the blossoms are centred on their middle at one
    size, the blossom filling the 12×12 frame (2 px larger than the Bosses.json hitbox), sparkles cut at its edge."""
    s = SCALE

    def hazard(name: str, frames: list, fps: int) -> Sprite:
        sprite = Sprite(f"hazard_{name}", (frames[0].width // s, frames[0].height // s), scale=s)
        sprite.add("fly", frames, fps=fps)
        return sprite

    def blossoms(cells) -> list:
        pieces = [SHEET.cut(c) for c in cells]
        sides = sorted(min(p.image.size) for p in pieces)
        kk = 12 * s / sides[len(sides) // 2]
        out = []
        for p in pieces:
            im = shrink(p.image, kk)
            a = im.getchannel("A")
            # The middle of the blossom: the centroid of its pixels (the sparkles are too small to pull it).
            n = sum(1 for v in a.tobytes() if v)
            px = a.load()
            mx = sum(x for y in range(im.height) for x in range(im.width) if px[x, y]) / n
            my = sum(y for y in range(im.height) for x in range(im.width) if px[x, y]) / n
            frame = Image.new("RGBA", (12 * s, 12 * s), (0, 0, 0, 0))
            frame.paste(im, (round(6 * s - mx - 0.5), round(6 * s - my - 0.5)), im)
            out.append(clean(frame))
        return out

    slashes = [SHEET.cut(c) for c in EXTRA["slash"]]
    k = fit_scale(slashes, (28 * s, 14 * s))
    slash = [fit(p, (28 * s, 14 * s), k=k) for p in slashes]
    return [hazard("claw_slash", slash, 12), hazard("bloom_shot", blossoms(EXTRA["shot"]), 12),
            hazard("bloom_shot_high", blossoms(EXTRA["shot_high"]), 12)]


def spirit() -> Sprite:
    """The float frames are painted facing right (three-quarters), like every enemy here, and mirrored on export to
    face the hero; the first two death frames (the flinch) are painted facing left, so the death row is turned here.
    One size for all float frames; the lowest pixel on row 20, as the code-drawn spirit."""
    s = SCALE
    floats = [SHEET.cut(c) for c in EXTRA["float"]]
    deaths = [SHEET.cut(c) for c in EXTRA["spirit_death"]]
    box = (24 * s, 20 * s)                       # rows 1-20: clear of the top edge, lowest pixel on row 20
    k = fit_scale(floats, box)

    def framed(piece, kk, turn=False) -> Image.Image:
        out = Image.new("RGBA", (24 * s, 24 * s), (0, 0, 0, 0))
        image = fit(piece, box, align="centre", k=kk)
        out.paste(ImageOps.mirror(image) if turn else image, (0, s))
        return out

    sprite = Sprite("sakura_spirit", (24, 24), faces_left=True, cx=12, ground=20, scale=s)
    sprite.add("float", [framed(p, k) for p in floats], fps=10)
    # The burst into petals spreads wider than the spirit: drawn smaller where it must, to stay in the frame.
    sprite.add("death", [framed(p, min(k, fit_scale([p], box)), turn=True) for p in deaths], fps=12, loop=False)
    return sprite


NAMES = {"boss_kitsune", "hazard_claw_slash", "hazard_bloom_shot", "hazard_bloom_shot_high", "sakura_spirit"}


def build() -> list[Sprite]:
    return [boss(), *hazards(), spirit()]
