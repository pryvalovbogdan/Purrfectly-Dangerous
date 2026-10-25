"""The Phantom Cat Queen and her projectiles, cut from the user's painted sheet (`sheet_boss.py`).

Source: `docs/concept/Phantom Cat Queen Boss Sheet.png`, copied to `Tools/sprites/boss_phantom_source.png`, painted to
`docs/boss-phantom-sheet-brief.md` with real transparency (her smoke and glow semi-transparent). Replaces the
code-drawn `boss_phantom` (`boss_phantom.py`) and `hazard_wave`, `hazard_wisp` (`boss_hazards.py`): those modules
skip a sprite whose name is in `NAMES`. Same sprite names and animation names; the frame is wider than the code-drawn
one (her smoke trails far behind her and the staff reaches far ahead), with the same ground row.
"""
from __future__ import annotations

from PIL import Image, ImageFilter, ImageOps

import palette as P
from sheet_boss import BossSheet, Cut, best_shift, body_mask, clean, fit, fit_scale, shrink
from sprite import Sprite

# Points: 84×126 when code-drawn. The same height and ground row, but wider: the painted Queen trails her smoke up to
# 92 points behind her head and thrusts her staff up to 63 ahead of it (the code-drawn one stayed within 84).
SIZE = (156, 126)
CX, GROUND = 92, 122
SCALE = 3

# The painting is semi-transparent all over (nothing reaches alpha 255): her fur, cloak and staff are painted at
# alpha 240-254, the smoke and glow round her fade out below that. A pixel is hers from alpha 200 (a solid figure
# with a clean edge; the faint haze between figures drops); figures are told apart from alpha 240.
SHEET = BossSheet(source="boss_phantom_source.png", alpha=200, core=240)

LABELS = ((10, 5, 125, 35), (845, 5, 1000, 35), (10, 160, 160, 190), (10, 320, 225, 350), (10, 472, 142, 502),
          (10, 645, 145, 677), (655, 650, 797, 682), (10, 805, 175, 838), (695, 805, 865, 838), (10, 905, 205, 942),
          (665, 905, 785, 942), (1122, 900, 1272, 935))        # the label pills, wiped wherever a cell overlaps one


def _figures(y0: int, y1: int, centres: list[int], half: int = 12, extra: dict | None = None,
             effects: tuple = (), points: dict | None = None, **kw) -> list[Cut]:
    """A row of overlapping figures (her smoke reaches under the next one's staff): one cell per figure, from the
    second figure on the left to the second on the right, each grown from the core pixels within `half` of its
    `centres` x (her head and body) along the painting's dark outlines (see `Cut.seeds`). `effects` are sheet points
    in cast effects (a crescent, a ball of ghost-fire) that grow as figures of their own, so they take what is theirs
    and no figure keeps them; `points` gives a figure more seed points by index (a staff thrust into such an effect)."""
    extra, points = extra or {}, points or {}
    own = [(c, tuple(points.get(i, ()))) for i, c in enumerate(centres)]
    loose = tuple((-10_000, (point,)) for point in effects)      # no band: they grow from their point only
    out = []
    for i, c in enumerate(centres):
        x0 = centres[i - 2] if i > 1 else c - 110
        x1 = centres[i + 2] if i + 2 < len(centres) else c + 110
        others = tuple(own[j] for j in (i - 2, i - 1, i + 1, i + 2) if 0 <= j < len(centres)) + loose
        out.append(Cut((max(0, x0), y0, min(1536, x1), y1), cleared=LABELS + tuple(extra.get(i, ())),
                       seeds=(own[i], others, half), **kw))
    return out


# One cell per painted frame, seeded on her head (sheet x).
ROWS = {
    "idle": _figures(37, 158, [94, 196, 293, 390, 487, 584, 680, 781]),
    "teleport": _figures(37, 158, [902, 1005, 1080, 1152, 1225, 1297, 1380, 1475], keep_all=True, min_bits=120),
    "summon": _figures(178, 314, [89, 205, 325, 440, 559, 682, 807, 935, 1064, 1197]),
    # Each cast throws its effect over the next frame's smoke: the crescents (2, 4) and the dark ghost-fire balls round
    # the staff's tip (5-9) are the spectral wave itself, a separate sprite, so they grow as `effects` and drop; the
    # staffs thrust into the balls and the smoke tails under the one before are seeded on the figure (`points`).
    "waves": _figures(352, 466, [105, 227, 354, 488, 620, 777, 946, 1101, 1250, 1396], core=225,
                      effects=((415, 400), (399, 439), (695, 401), (700, 420), (683, 432), (850, 440), (865, 420),
                               (1010, 440), (1022, 420), (1162, 440), (1172, 420), (1308, 440), (1318, 420),
                               (1458, 440), (1478, 425)),
                      points={5: ((795, 412), (812, 415), (725, 440), (715, 425)),     # staff and smoke tail
                              6: ((965, 414), (985, 418), (890, 440), (880, 425)),
                              7: ((1115, 413), (1135, 416), (1060, 440), (1045, 425)),
                              8: ((1265, 415), (1282, 417), (1195, 440), (1185, 425)),
                              9: ((1410, 417), (1428, 420), (1345, 440), (1335, 425))}),
    "split": _figures(505, 640, [97, 228, 375, 491, 647, 805, 974, 1134, 1308]),
    "hurt": _figures(680, 800, [91, 202, 314, 411, 526]),
    "death": _figures(680, 800, [763, 898, 1023, 1140, 1253, 1358, 1465], keep_all=True, min_bits=40),
}
EXTRA = {
    "wave": [Cut((x0, 943, x1, 1022), cleared=LABELS, alpha=120, core=1)
             for x0, x1 in ((20, 135), (135, 234), (234, 335), (335, 436), (436, 538), (538, 645))],
    "wisp": [Cut((x0, 943, x1, 1022), cleared=LABELS, alpha=120, core=1)
             for x0, x1 in ((655, 752), (752, 858), (858, 954), (954, 1037), (1037, 1115))],
}


# Points per sheet pixel: she keeps about the code-drawn Queen's height (about 110 points, crown to smoke; the sheet
# paints her about 118 px tall). At 3x detail every sheet pixel becomes 2.8 texture pixels (LANCZOS); the engine draws
# them with nearest filtering.
K = 0.93
# The painter drew SUMMON a little larger than IDLE (the same head and staff, larger) and TELEPORT 7 too: scaled by this
# much on top of `K` (measured by the figures' heights), so she keeps one size when GameScene switches animations.
ROW_SIZE = {"summon": 0.93}
FRAME_SIZE = {("teleport", 7): 0.97}
BODY = 60                         # points above the ground compared when lining up frames that have no head to seed on

# Animations: (painted row, frame), fps, loop. GameScene plays an attack once from the start of its wind-up and holds
# the last frame, so played frame N (0-based) shows at N / fps seconds (Bosses.json `boss_phantom`):
#   summon (`summon_ghosts`, ghost cats at 0.9 and 1.9 s): the painted row has one cast, the staff thrust at SUMMON 4;
#     it plays again after SUMMON 8, so the thrusts are frames 4 and 9: at 4 / 4.7 = 0.85 s and 9 / 4.7 = 1.91 s.
#     SUMMON 9 (a ghost cat painted beside her) is the summoned sprite itself: cut off, and not played.
#   teleport (`spectral_waves`, waves at 0.8, 1.4 and 2.0 s; also a phase-3 copy appearing): TELEPORT (she dissolves
#     and re-forms) then SPECTRAL WAVES at 10 fps: the thrusts WAVES 2 and 4 and the staff levelled, WAVES 5, are frames
#     8, 14 and 20. Between them she draws the staff back (WAVES 3, held) and raises the glowing orb again (WAVES 0, 1).
#   split: the real Queen in phase 3 loops IDLE with a pulsing glow round her outline (see `_glow`). The painted SPLIT
#     row (her conjuring look-alikes beside her) has no slot: the game draws the copies itself.
# IDLE 0 (a curl of smoke the other frames lack) is left out so the loop closes.
_W = lambda *frames: [("waves", i) for i in frames]
PLAN = {
    "idle": ([("idle", i) for i in range(1, 8)], 7, True),                         # 1.0 s a loop
    "summon": ([("summon", i) for i in (*range(9), 4, 5, 6)], 4.7, False),
    "teleport": ([("teleport", i) for i in range(8)] + _W(2, 3, 3, 0, 1, 1, 4, 3, 3, 0, 1, 1, 5, 6, 7, 8, 9), 10, False),
    "split": ([("idle", i) for i in range(1, 8)], 7, True),
    "hurt": ([("hurt", i) for i in range(5)], 12, True),                          # 0.42 s
    "death": ([("death", i) for i in range(7)], 7, False),                         # 1.0 s, ends in the violet flame
}
HEADLESS = {("death", i) for i in range(1, 7)}
GLOW = (5, 7, 9, 11, 11, 9, 7)    # SPLIT: the glow's width round her (texture pixels), frame by frame
LIFT = (0.12, 0.18, 0.24, 0.3, 0.3, 0.24, 0.18)    # and how far she is lit toward the glow's pale pink


def _glow(image: Image.Image, width: int, lift: float) -> Image.Image:
    """`image` lit `lift` of the way toward pale pink, with a hard-edged two-tone aura `width` px wide round its
    outline: pale pink inside, magenta outside."""
    a = image.getchannel("A")
    lit = Image.blend(image, Image.new("RGBA", image.size, (*P.QN_ORB_L[:3], 255)), lift)
    lit.putalpha(a)
    image = lit
    inner = a.filter(ImageFilter.MaxFilter(2 * max(1, width // 2) + 1))
    outer = a.filter(ImageFilter.MaxFilter(2 * width + 1))
    out = Image.new("RGBA", image.size, (0, 0, 0, 0))
    out.paste(Image.new("RGBA", image.size, (*P.QN_ORB[:3], 255)), (0, 0), outer)
    out.paste(Image.new("RGBA", image.size, (*P.QN_ORB_L[:3], 255)), (0, 0), inner)
    out.alpha_composite(image)
    return clean(out)


def boss() -> Sprite:
    fw, fh = SIZE[0] * SCALE, SIZE[1] * SCALE
    ground = GROUND * SCALE + SCALE - 1          # the lowest pixel row of point row GROUND
    centre = CX * SCALE + SCALE / 2
    k = K * SCALE
    used = sorted({key for frames, _, _ in PLAN.values() for key in frames})
    pieces = {key: SHEET.cut(ROWS[key[0]][key[1]]) for key in used}
    small = {key: shrink(p.image, k * FRAME_SIZE.get(key, ROW_SIZE.get(key[0], 1))) for key, p in pieces.items()}

    # Where each frame's left edge goes (frame pixels): her head (the `centres` seed) on the anchor. DEATH's frames after
    # the first (lying down, the head moving forward as she sinks) are lined up with the frame before them over their
    # lower body (`best_shift`).
    def left(key):
        piece, image = pieces[key], small[key]
        head = ROWS[key[0]][key[1]].seeds[0][0]
        return round(centre - (head - piece.box[0]) * image.width / piece.image.width)

    lefts = {}
    for key in used:
        if key not in HEADLESS:
            lefts[key] = left(key)
    deaths = [key for key in used if key[0] == "death"]
    for a, b in zip(deaths, deaths[1:]):
        ma, mb = body_mask(small[a], BODY * SCALE), body_mask(small[b], BODY * SCALE)
        lefts[b] = lefts[a] + best_shift(ma, mb, 30 * SCALE)

    sprite = Sprite("boss_phantom", SIZE, faces_left=True, cx=CX, ground=GROUND, scale=SCALE)
    for name, (frames, fps, loop) in PLAN.items():
        out_frames = []
        for i, key in enumerate(frames):
            image = small[key]
            if name == "split":
                pad = GLOW[i]
                image = _glow(ImageOps.expand(image, pad), pad, LIFT[i])
                x = lefts[key] - pad
            else:
                x = lefts[key]
            # Never touching the frame's sides: HURT 4 (the staff flung up and forward) moves back 13 points, which reads
            # as the recoil; DEATH 0-5 (the smoke trailing far behind) forward up to 4.
            x = min(max(x, 1), fw - 1 - image.width)
            out = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
            bottom = ground + 1 + (GLOW[i] if name == "split" else 0)
            out.paste(image, (x, bottom - image.height), image)
            if name == "split":                             # the glow stops at the ground, as her smoke does
                out.paste((0, 0, 0, 0), (0, ground + 1, fw, fh))
            out_frames.append(clean(out))
        sprite.add(name, out_frames, fps=fps, loop=loop)
    return sprite


def hazards() -> list[Sprite]:
    """Painted pointing right with the trail on the left: turned to fly left, as the game draws hazards (not mirrored
    on export). One size per row, leading edge on the left, bottom on the bottom row, as the code-drawn ones (16×14
    and 18×14 frames round 12×12 hitboxes). The last painted frames of each row (the effect shrinking away) are left
    out so the loops close: SPECTRAL WAVE 0-4, WISP 0-2."""
    s = SCALE

    def hazard(name: str, cells: list[Cut], size: tuple[int, int], fps: int) -> Sprite:
        pieces = [SHEET.cut(c) for c in cells]
        for p in pieces:
            p.image = ImageOps.mirror(p.image)
        box = (size[0] * s, size[1] * s)
        kk = fit_scale(pieces, box)
        sprite = Sprite(f"hazard_{name}", size, scale=s)
        sprite.add("fly", [fit(p, box, k=kk) for p in pieces], fps=fps)
        return sprite

    return [hazard("wave", EXTRA["wave"][:5], (16, 14), 12), hazard("wisp", EXTRA["wisp"][:3], (18, 14), 12)]


NAMES = {"boss_phantom", "hazard_wave", "hazard_wisp"}


def build() -> list[Sprite]:
    return [boss(), *hazards()]
