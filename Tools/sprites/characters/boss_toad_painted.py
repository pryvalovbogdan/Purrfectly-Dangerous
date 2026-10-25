"""The Lantern Toad Guardian and its projectiles, cut from the user's painted sheet (`sheet_boss.py`).

Source: `docs/concept/Sakura Lantern Toad Boss Sprite Sheet v2.png`, copied to `Tools/sprites/boss_toad_source.png`,
painted to `docs/boss-toad-sheet-brief.md` with real transparency (the pink haze is semi-transparent): the user's
two sheets side by side, the toad's own rows on the left (A), the projectiles, WALK and PREPARE on the right (B).
Replaces the code-drawn `boss_toad` (`boss_toad.py`) and `hazard_toad_tongue`, `hazard_lantern_shot`,
`hazard_lantern_shot_high`, `hazard_slam_rock` and `hazard_slam_wave` (`boss_hazards.py`): those modules skip a
sprite whose name is in `NAMES`. Same sprite names, animation names, frame sizes (in points) and anchors.
"""
from __future__ import annotations

from PIL import Image

from sheet_boss import BossSheet, Cut, cells, clean, fit, fit_scale, shrink
from sprite import Sprite

SIZE = (160, 136)                 # points, as the code-drawn boss
CX, GROUND = 76, 132
SCALE = 3

SHEET = BossSheet(source="boss_toad_source.png", alpha=200, core=240)

LABELS = ((11, 6, 142, 37), (11, 169, 173, 199), (11, 324, 189, 354), (11, 489, 151, 519), (11, 797, 142, 828),
          (302, 796, 454, 827), (955, 6, 1201, 36), (955, 141, 1157, 172), (955, 273, 1206, 303),
          (955, 408, 1137, 439), (955, 537, 1142, 567), (955, 665, 1165, 696), (955, 811, 1194, 842),
          (936, 0, 952, 1024))            # the label pills and the line between the two sheets


def _row(y0: int, y1: int, edges: list[int], extra: dict | None = None, **kw) -> list[Cut]:
    return cells(y0, y1, edges, LABELS, extra, **kw)


# One cell per painted toad (sheet x edges halfway between the rocks). The toads overlap their neighbours (the
# lanterns and hat brims cross into the next frame): with `seeds`, every toad near a cell grows at once from its own
# middle over the painting (a watershed along the dark outlines), so each keeps what is nearest to it.
ROWS = {
    "idle": _row(38, 152, [5, 117, 219, 318, 417, 515, 613, 712, 810, 915], seeds=15),
    # The strike (8) shoots its tongue across the next toad: the cell stops at x 705, keeping the tongue's base
    # (the flying tongue is `hazard_toad_tongue`); toad 9 loses the tongue's tip.
    "tongue": _row(196, 305, [5, 105, 187, 268, 334, 401, 467, 530, 600, 705, 820, 925], seeds=15,
                   extra={8: (("r", ((712, 0), (712, 1024))),), 9: (("l", ((738, 0), (738, 1024))), ("o", 752, 258, 27, 18))}),
    # The spits (9-11): each lantern leaves the mouth over the next toad's side; it goes to the toad spitting it.
    "lanterns": _row(352, 470, [5, 95, 161, 221, 283, 343, 401, 460, 523, 591, 655, 710, 761, 817, 925], seeds=15,
                     points={9: ((667, 415),), 10: ((719, 417),), 11: ((768, 417),), 12: ((815, 427),), 13: ((837, 422),)}),
    # Wrapped onto two lines. Frames 4-7 leap off the rock (painted without it); 17 and 18 are painted without
    # the toad (only the rock and the burst) and are not played.
    "slam": [*_row(486, 642, [5, 102, 194, 290, 391, 483, 583, 677, 762, 847, 940], seeds=15),
             *_row(643, 766, [5, 102, 191, 290, 386, 486, 594, 694, 755, 818, 925], seeds=15, keep_all=True,
                   min_bits=60)],
    "hurt": _row(835, 948, [5, 78, 145, 209, 295], seeds=15),
    "death": _row(835, 948, [298, 388, 472, 556, 631, 697, 765, 852, 935], seeds=15, keep_all=True, min_bits=60),
    "walk": _row(700, 795, [955, 1032, 1101, 1166, 1230, 1295, 1367, 1444, 1530], seeds=15),
    "prepare": _row(845, 950, [955, 1052, 1147, 1241, 1331, 1427, 1530], seeds=15),
}
EXTRA = {
    "tongue_shot": _row(55, 125, [955, 1088, 1230, 1376, 1520], alpha=150, core=1),
    "lantern": _row(175, 262, [960, 1035, 1102, 1168, 1235, 1305, 1375, 1448, 1525], alpha=150, core=1),
    "lantern_high": _row(308, 395, [960, 1036, 1104, 1172, 1244, 1312, 1384, 1456, 1530], alpha=150, core=1),
    "rock": _row(445, 525, [955, 1032, 1101, 1173, 1245, 1314, 1380, 1456, 1530], alpha=150, core=1),
    "wave": _row(570, 648, [955, 1100, 1238, 1375, 1520], alpha=150, core=1),
}

# Points per sheet pixel: the toad keeps about the size of the first painted toad in the game (the v2 toad is painted
# about 97 px wide with its lanterns, about 100 tall with its hat; body and face under the brim fill the 60×60
# hitbox). At 3x detail every sheet pixel becomes 2.55 texture pixels (LANCZOS); the engine draws them nearest.
K = 0.85
# The painter drew the rows at slightly different sizes: each is scaled by this much on top of `K` to IDLE's size
# (measured by overlaying each row's toads on IDLE's).
ROW_SIZE = {"tongue": 1.08, "lanterns": 1.08, "slam": 1.08, "hurt": 1.1, "walk": 1.27, "prepare": 1.08}
LEAP = (4, 5, 6, 7)               # SLAM frames painted in the air, without the rock: drawn over SLAM 3's rock
SLAM_GROUND = (639, 759)          # the sheet ground row of SLAM's two lines (the bottom of the rock)

# Animations: painted row, the painted frames played (all but two), fps and loop. GameScene plays an attack once from
# the start of its wind-up and holds the last frame, so painted frame N (0-based) shows at N / fps seconds; the fps
# puts the strike where the projectile leaves (Bosses.json `boss_toad`):
#   tongue: strike 8 (the tongue shooting out) at 8 / 7.5 = 1.07 s (the tongue leaves at 1.1 s);
#   lanterns: first spit 9 at 9 / 9 = 1.0 s (the low lantern leaves at 1.0 s); the second spit, 11, lands at
#             1.22 s, earlier than the high lantern (1.6 s): the painted row has only two frames between the spits;
#   slam: the landing, 16 (flattened under the hat, the burst round the rock), at 16 / 10 = 1.6 s (the wave leaves at
#         1.6 s). SLAM 17 and 18 are painted without the toad (only the rock and the debris) and are left out.
PLAN = {
    "idle": ("idle", range(9), 9, True),                 # 1.0 s a loop
    "walk": ("walk", range(8), 10, True),
    "prepare": ("prepare", range(6), 10, False),
    "tongue": ("tongue", range(11), 7.5, False),
    "lanterns": ("lanterns", range(14), 9, False),
    "slam": ("slam", (*range(17), 19), 10, False),
    "hurt": ("hurt", range(4), 12, True),                # 0.33 s
    "death": ("death", range(8), 7, False),              # 1.14 s, ends with only the mossy rock
}


def _rock_middle(image: Image.Image) -> float:
    """x (in `image`) of the middle of the mossy rock the toad sits on: its lowest rows."""
    a = image.getchannel("A").load()
    w, h = image.size
    xs = [x for y in range(max(0, h - 6), h) for x in range(w) if a[x, y]]
    return (min(xs) + max(xs)) / 2


def boss() -> Sprite:
    fw, fh = SIZE[0] * SCALE, SIZE[1] * SCALE
    ground = GROUND * SCALE + SCALE - 1          # the lowest pixel row of point row GROUND
    centre = CX * SCALE + SCALE / 2
    pieces = {name: [SHEET.cut(c) for c in cells] for name, cells in ROWS.items()}

    # The rock under the leap: SLAM 3's lowest rows (below the toad's feet), at the slam's size.
    k_slam = K * SCALE * ROW_SIZE["slam"]
    base = pieces["slam"][3]
    rock_rows = 20                                # sheet rows of the rock
    rock_piece = base.image.crop((0, base.image.height - rock_rows, base.image.width, base.image.height))
    rock = shrink(rock_piece.crop(rock_piece.getbbox()), k_slam)

    sprite = Sprite("boss_toad", SIZE, faces_left=True, cx=CX, ground=GROUND, scale=SCALE)
    for name, (row, plan, fps, loop) in PLAN.items():
        k = K * SCALE * ROW_SIZE.get(row, 1)
        frames = []
        for i in plan:
            piece = pieces[row][i]
            image = shrink(piece.image, k)
            out = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
            if row == "slam" and i in LEAP:
                # In the air: the toad keeps its painted height above the ground and its painted place over the
                # rock (SLAM 3's rock, where it took off), which stays on the ground.
                cell = ROWS["slam"][i].seeds[0][0]
                base_cell = ROWS["slam"][3].seeds[0][0]
                rock_x = round(centre - rock.width / 2)
                out.paste(rock, (rock_x, ground + 1 - rock.height), rock)
                rock_mid_sheet = base.box[0] + _rock_middle(base.image) + (cell - base_cell)
                x = round(centre - (rock_mid_sheet - piece.box[0]) * k)
                lift = round((SLAM_GROUND[0] - piece.box[3]) * k)
                out.paste(image, (x, ground + 1 - image.height - lift), image)
            else:
                x = round(centre - _rock_middle(image))
                out.paste(image, (x, ground + 1 - image.height), image)
            frames.append(clean(out))
        sprite.add(name, frames, fps=fps, loop=loop)
    return sprite


def hazards() -> list[Sprite]:
    """Painted pointing left (the way they fly), as the game draws hazards: not mirrored. The tongue, rock and wave
    fill their frames at one size per row (2 px larger than the Bosses.json hitbox), leading edge on the left, bottom
    on the bottom row; the lanterns are centred on their middle at one size, the lantern filling the 12×12 frame,
    sparks cut at its edge."""
    s = SCALE

    def hazard(name: str, row: list[Cut], size: tuple[int, int], fps: int, align: str = "left") -> Sprite:
        pieces = [SHEET.cut(c) for c in row]
        box = (size[0] * s, size[1] * s)
        k = fit_scale(pieces, box)
        sprite = Sprite(f"hazard_{name}", size, scale=s)
        sprite.add("fly", [fit(p, box, align=align, k=k) for p in pieces], fps=fps)
        return sprite

    def lanterns(name: str, row: list[Cut]) -> Sprite:
        pieces = [SHEET.cut(c) for c in row]
        sides = sorted(min(p.image.size) for p in pieces)
        kk = 12 * s / sides[len(sides) // 2]
        frames = []
        for p in pieces:
            im = shrink(p.image, kk)
            a = im.getchannel("A")
            n = sum(1 for v in a.tobytes() if v)
            px = a.load()
            mx = sum(x for y in range(im.height) for x in range(im.width) if px[x, y]) / n
            my = sum(y for y in range(im.height) for x in range(im.width) if px[x, y]) / n
            frame = Image.new("RGBA", (12 * s, 12 * s), (0, 0, 0, 0))
            frame.paste(im, (round(6 * s - mx - 0.5), round(6 * s - my - 0.5)), im)
            frames.append(clean(frame))
        sprite = Sprite(f"hazard_{name}", (12, 12), scale=s)
        sprite.add("fly", frames, fps=12)
        return sprite

    return [hazard("toad_tongue", EXTRA["tongue_shot"], (42, 12), 10),
            lanterns("lantern_shot", EXTRA["lantern"]), lanterns("lantern_shot_high", EXTRA["lantern_high"]),
            hazard("slam_rock", EXTRA["rock"], (14, 14), 12, "centre"),
            hazard("slam_wave", EXTRA["wave"], (18, 12), 10)]


NAMES = {"boss_toad", "hazard_toad_tongue", "hazard_lantern_shot", "hazard_lantern_shot_high", "hazard_slam_rock",
         "hazard_slam_wave"}


def build() -> list[Sprite]:
    return [boss(), *hazards()]
