"""The Void Cat and its projectiles, cut from the user's painted sheet (`sheet_boss.py`).

Source: `Void Cat Cosmic Boss Sprite Atlas.png`, copied to `Tools/sprites/boss_voidcat_source.png` (1774×887, real
transparency: the body nearly opaque, a wide violet and blue glow fading out round it). It differs from
`docs/boss-voidcat-sheet-brief.md`: one sheet, not three; a crouching cat seen from the side, its paws reaching right
(not front-facing); the boss rows IDLE, SHADOW PAWS, STAR FALL, PORTAL PAWS, PORTAL SHARDS, PHASE RUSH and PHASE
STORM with 10-12 frames each (the labels' counts don't always match), no HURT and no DEATH row; and every row painted
at its own size (IDLE about a third larger than the others, PORTAL PAWS a little squashed). Replaces the code-drawn
`boss_voidcat` (`boss_voidcat.py`) and `hazard_shadow_paw`, `hazard_falling_star`, `hazard_void_wave`,
`hazard_star_shard` and `portal` (`boss_hazards.py`): those modules skip a sprite whose name is in `NAMES`.
`hazard_portal_ring` (no attack throws it) stays code-drawn. Same sprite name and anchor point; the frame is wider
(400×140 points, was 170×140) and the animations follow the painted rows: `swipe` (unused) is gone and two attacks get
rows of their own, `rift` (`portal_shards`) and `storm` (`phase_storm`), which GameScene.attackAnimation must map
(`ATTACKS`); until it does they play `portal` and `phase`.
"""
from __future__ import annotations

from PIL import Image, ImageOps

import draw
import palette as P
from sheet_boss import BossSheet, Cut, Piece, _line_x, clean, fit, fit_scale
from sprite import Sprite

SCALE = 3

# A pixel is the cat's from alpha 200 (its dark body and the magenta rim; the soft glow round it, which reaches into
# the neighbouring frames, drops). Figures are told apart from alpha 250.
SHEET = BossSheet(source="boss_voidcat_source.png", alpha=200, core=250)

# The label pills, wiped wherever a cell overlaps one.
LABELS = ((8, 6, 108, 34), (8, 144, 150, 165), (8, 257, 146, 279), (8, 370, 152, 392), (8, 468, 166, 491),
          (8, 571, 150, 592), (8, 659, 152, 680),
          (14, 760, 146, 782), (430, 760, 600, 782), (876, 760, 1002, 782), (1340, 760, 1464, 782),
          (14, 820, 162, 844), (462, 820, 600, 844), (883, 820, 1002, 844))


def _figures(y0: int, y1: int, heads: list[int], bounds: dict | None = None, extra: dict | None = None,
             cores: dict | None = None, **kw) -> list[Cut]:
    """A row of figures whose paws and tails reach under each other: one cell per figure, from just past the head of
    the one before to just short of the head of the one after (sheet x, between the eyes), so this figure is the
    largest shape of core pixels in it; the neighbours' cores grow back out at the same time, so each keeps the soft
    edge nearest to it. Where two
    figures' cores touch (a paw thrust into the next one's tail), `bounds[i]` is a polyline ((x, y), ... from top to
    bottom) between figure i and i + 1: everything right of it is wiped from i, everything left of it from i + 1.
    `extra` adds `cleared` areas by index, `cores` a figure's own core alpha."""
    bounds, extra, cores = bounds or {}, extra or {}, cores or {}
    out = []
    for i, c in enumerate(heads):
        x0 = heads[i - 1] + 30 if i else c - 130
        x1 = heads[i + 1] - 30 if i + 1 < len(heads) else c + 170
        cut = tuple(extra.get(i, ()))
        if i in bounds:
            cut += (("r", bounds[i]),)
        if i - 1 in bounds:
            cut += (("l", bounds[i - 1]),)
        out.append(Cut((max(0, x0), y0, min(1774, x1), y1), cleared=LABELS + cut, core=cores.get(i), **kw))
    return out


# The head of every painted cat (sheet x, between the eyes; the frame's anchor) and the band of its row. PHASE RUSH's
# cats streak low in 1-8, the head at the front of the streak.
HEADS = {
    "idle": (20, 140, [120, 276, 451, 628, 807, 979, 1159, 1335, 1519, 1695]),
    "paws": (144, 252, [108, 250, 393, 556, 686, 863, 1007, 1179, 1369, 1540, 1706]),
    "stars": (257, 366, [104, 240, 389, 541, 687, 831, 978, 1131, 1300, 1509, 1715]),
    "portal": (370, 468, [105, 246, 387, 536, 682, 830, 976, 1129, 1309, 1489, 1710]),
    "shards": (468, 570, [108, 257, 400, 554, 711, 866, 1025, 1181, 1331, 1465, 1589, 1708]),
    "rush": (571, 656, [115, 284, 452, 637, 832, 1000, 1152, 1322, 1526, 1700]),
    "storm": (659, 756, [106, 226, 369, 507, 607, 783, 964, 1155, 1334, 1524, 1700]),
}
# Where two figures touch, the line between them (see `_figures`): SHADOW PAWS 2-8 thrust a paw into the next one's
# tail; PORTAL PAWS 2-9 thrust it into a portal painted in front of the claws, the next one's tail right behind it.
# The portal goes with the line (the game draws its own portal pair, ahead of the kitten): the claws keep what is left
# of the line at the portal's near edge, the next figure what is right of its far edge.
BOUNDS = {
    "paws": {2: ((481, 144), (482, 214), (477, 228), (474, 252)),
             3: ((618, 144), (618, 199), (638, 201), (638, 228), (631, 240), (629, 252)),
             4: ((771, 144), (771, 252)),
             5: ((919, 144), (919, 201), (936, 206), (936, 252)),
             6: ((1094, 144), (1094, 204), (1114, 208), (1114, 252)),
             7: ((1258, 144), (1258, 192), (1296, 200), (1298, 252)),
             8: ((1457, 144), (1457, 252))},
}
_line = lambda x: ((x, 0), (x, 887))
# PORTAL PAWS: (the claws' edge, the next figure's edge) per thrust.
PORTALS = {2: (448, 484), 3: (601, 634), 4: (744, 777), 5: (895, 913), 6: (1036, 1077), 7: (1188, 1232),
           8: (1376, 1418), 9: (1561, 1612)}
EXTRA = {
    "portal": {i: ((("r", _line(PORTALS[i][0])),) if i in PORTALS else ())
                  + ((("l", _line(PORTALS[i - 1][1])),) if i - 1 in PORTALS else ()) for i in range(11)},
    # PORTAL SHARDS 5-8: the spark of a shard flying off behind the tail (the star shard is a sprite of its own).
    "shards": {5: (("o", 788, 508, 14, 12),), 6: (("o", 946, 507, 14, 12),), 7: (("o", 1106, 506, 14, 12),),
               8: (("o", 1258, 507, 14, 12),)},
    # PHASE STORM 4: the next frame's far-flung paw lies over its cell.
    "storm": {4: (("r", _line(665)),)},
}
# PORTAL PAWS 7: the shoulder is painted soft (alpha 200-250), so the thrust arm is found with the body from alpha 200.
CORES = {"portal": {7: 200}}
ROWS = {name: _figures(y0, y1, heads, BOUNDS.get(name), EXTRA.get(name), CORES.get(name))
        for name, (y0, y1, heads) in HEADS.items()}
# Where a neighbour's paw or portal lay over a figure's tail, the line cuts the tail off straight (and in PORTAL PAWS
# the claws thrust into the portal). The cut is frayed into smoke and flame instead: it eats up to `FRAY` sheet pixels
# further in, in a wave that changes every few rows.
FRAY = 12

# Points per sheet pixel. The painter drew every row at its own size: each row is scaled to IDLE's (measured by the
# distance between the eyes and from the eyes to the chest portal in every frame), PORTAL PAWS a little more upward
# than across (it is painted squashed). IDLE's cat is about 100 points tall to the ear tips crouching, as tall as the
# code-drawn boss's body, its head and chest over the 60×90 hitbox; the tail and paws stick out.
K = 1.0
ROW_SIZE = {"idle": (1.0, 1.0), "paws": (1.25, 1.25), "stars": (1.35, 1.35), "portal": (1.34, 1.42),
            "shards": (1.32, 1.32), "rush": (1.42, 1.42), "storm": (1.41, 1.41)}

# Points. The head sits on `CX`; the frame reaches far behind it for PHASE RUSH's streak and far ahead for the paws
# thrust out in SHADOW PAWS and PHASE STORM (off screen behind the boss in game; the game reads only the anchor).
SIZE = (400, 140)
CX, GROUND = 220, 136

# Animations: (painted row, painted frames played in order, fps, loop). GameScene plays an attack once from the start
# of its wind-up and holds the last frame, so the frame at position N shows at N / 10 seconds (all attacks play at 10
# fps); the frames are picked so the strike shows when Bosses.json `boss_voidcat` lets the hazard go. The painted rows
# have one or two strikes each, so frames are played again:
#   paws (`shadow_paws`, low shadow paws at 0.7, 1.3, 1.9 s): SHADOW PAWS 8 (the paw reared up, the tail raised) is the
#        wind-up before each slam (held a beat), the paw thrust far ahead the slam: SHADOW PAWS 6 at 7, 7 (the
#        longest) at 13, 6 at 19. SHADOW PAWS 0, painted smaller than the rest, is left out.
#   stars (`star_fall`, falling stars at 0.7 and 1.2 s, a low shadow paw at 1.6 s): STAR FALL 7 (the star held highest)
#        at 7 and 12, the stars gathering on the raised paw (3-6) before each; STAR FALL 8 (the paw slammed down in a
#        burst) at 16. The stars painted flying off (in 8 and 9) are the falling-star sprite: dropped.
#   portal (`portal_paws`, portals open at 0.6 s, a low void wave at 1.1, a high star shard at 1.8, a low wave at 2.5):
#        the first thrust (PORTAL PAWS 2) at 6, the long low thrust (8) at 11 and 25, the paw thrust highest (6) at 18.
#        The portals painted round the claws are the game's portal pair: dropped (see `PORTALS`).
#   rift (`portal_shards`, portals at 0.6 s, high star shards at 0.9 and 2.1, a low void wave at 1.5): PORTAL SHARDS 0
#        (the paw lifted) at 6, 1 (flung up high) at 9, 4 (raked low) at 15, 6 (flung up ahead) at 21.
#   phase (`phase_rush`: a low void wave at 0.5 s, high star shards at 1.0 and 2.0, a low shadow paw at 1.5): the cat
#        streaks low in a smear of void smoke; PHASE RUSH 5 and 8 (a flash along the smear) at 5, 10, 15 and 20, 3-7
#        streaming between. Starts and ends on PHASE RUSH 9 (PHASE RUSH 0 is painted smaller).
#   storm (`phase_storm`: falling stars at 0.5 and 1.2 s, a low void wave at 0.9, a low shadow paw at 1.7): PHASE STORM
#        4 (an orb flung up) at 5 and 12, 5 (both arms swept wide) at 9, 6 (a paw thrust ahead) at 17.
PLAN = {
    "idle": ("idle", tuple(range(10)), 8, True),                                                  # 1.25 s a loop
    "paws": ("paws", (10, 9, 1, 3, 4, 8, 8, 6, 5, 4, 3, 8, 8, 7, 5, 4, 1, 8, 8, 6, 5, 1, 9, 10), 10, False),
    "stars": ("stars", (0, 1, 2, 3, 4, 5, 6, 7, 9, 3, 5, 6, 7, 9, 2, 1, 8, 10, 0), 10, False),
    "portal": ("portal", (10, 0, 1, 0, 1, 3, 2, 3, 5, 7, 5, 8, 9, 7, 5, 3, 4, 5, 6, 4, 5, 3, 7, 5, 9, 8, 1, 0),
               10, False),
    "rift": ("shards", (11, 10, 9, 8, 2, 5, 0, 2, 0, 1, 2, 7, 8, 5, 3, 4, 3, 5, 2, 0, 2, 6, 7, 8, 9, 10), 10, False),
    "phase": ("rush", (9, 1, 2, 3, 4, 5, 6, 7, 3, 4, 8, 6, 7, 3, 4, 5, 6, 7, 3, 4, 8, 2, 1, 9), 10, False),
    "storm": ("storm", (10, 1, 2, 7, 3, 4, 2, 1, 8, 5, 9, 3, 4, 1, 2, 7, 8, 6, 9, 10), 10, False),
}
# Where each attack's strikes are in its played frames (positions above), for the tests: `ATTACKS` is what GameScene
# should play for each attack (GameScene.attackAnimation).
RELEASES = {"paws": (7, 13, 19), "stars": (7, 12, 16), "portal": (6, 11, 18, 25), "rift": (6, 9, 15, 21),
            "phase": (5, 10, 15, 20), "storm": (5, 9, 12, 17)}
ATTACKS = {"shadow_paws": "paws", "star_fall": "stars", "portal_paws": "portal", "portal_shards": "rift",
           "phase_rush": "phase", "phase_storm": "storm"}
HURT_JOLT = (3, 5, 2)             # HURT: IDLE 0 knocked back this many points (and the game's white flash)


def _scale(image: Image.Image, kx: float, ky: float) -> Image.Image:
    """`image` scaled by `kx` across and `ky` up (LANCZOS, premultiplied) with hard 0/255 alpha."""
    size = (max(1, round(image.width * kx)), max(1, round(image.height * ky)))
    small = image.resize(size, Image.LANCZOS)
    small.putalpha(small.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
    return clean(small)


def _fray(piece: Piece, cut: Cut, seed: int, front: bool) -> None:
    """Frays the straight cut a figure's left line (an "l" area in `cut.cleared`) leaves in its tail, and with `front`
    the one its right line leaves in its claws."""
    rnd = draw.noise(seed)
    h, w = piece.image.height, piece.image.width
    px = piece.image.load()
    x0, y0 = piece.box[:2]
    for side in ("l", "r") if front else ("l",):
        lines = [area[1] for area in cut.cleared if area[0] == side]
        if not lines:
            continue
        knots = [rnd() * FRAY for _ in range(h // 5 + 2)]
        for y in range(h):
            t = y / 5
            depth = knots[int(t)] + (knots[int(t) + 1] - knots[int(t)]) * (t - int(t))
            if side == "l":
                edge = round(max(_line_x(points, y + y0) for points in lines) - x0 + depth)
                xs = range(min(w, max(0, edge)))
            else:
                edge = round(min(_line_x(points, y + y0) for points in lines) - x0 - depth)
                xs = range(max(0, edge), w)
            for x in xs:
                px[x, y] = (0, 0, 0, 0)


def frames() -> dict[tuple[str, int], tuple[Image.Image, int]]:
    """Every painted frame the plan uses, scaled, with the x of its left edge in the frame (texture pixels)."""
    used = sorted({(row, i) for row, plan, _, _ in PLAN.values() for i in plan} | {("idle", 0)})
    centre = CX * SCALE + SCALE / 2
    out = {}
    for row, i in used:
        piece = SHEET.cut(ROWS[row][i])
        _fray(piece, ROWS[row][i], seed=len(out) + 1, front=row == "portal")
        kx, ky = (K * SCALE * f for f in ROW_SIZE[row])
        image = _scale(piece.image, kx, ky)
        head = HEADS[row][2][i]
        out[row, i] = image, round(centre - (head - piece.box[0]) * kx)
    return out


def boss() -> Sprite:
    fw, fh = SIZE[0] * SCALE, SIZE[1] * SCALE
    ground = GROUND * SCALE + SCALE - 1          # the lowest pixel row of point row GROUND
    cut = frames()
    made: dict[tuple, Image.Image] = {}          # the plans replay frames: place and clean each one once

    def frame(key, dx: int = 0) -> Image.Image:
        if (key, dx) not in made:
            out = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
            image, x = cut[key]
            out.paste(image, (x + dx, ground + 1 - image.height), image)
            made[key, dx] = clean(out)
        return made[key, dx].copy()

    sprite = Sprite("boss_voidcat", SIZE, faces_left=True, cx=CX, ground=GROUND, scale=SCALE)
    for name, (row, plan, fps, loop) in PLAN.items():
        sprite.add(name, [frame((row, i)) for i in plan], fps=fps, loop=loop)
    sprite.add("hurt", [frame(("idle", 0), dx=-d * SCALE) for d in HURT_JOLT], fps=12, loop=True)
    sprite.add("death", _death(frame(("idle", 0))), fps=10, loop=False)
    return sprite


# DEATH: no row is painted. IDLE 0 flashes, then comes apart into stars: its pixels go in a random order (rising
# from the feet), the ones just gone glinting as stars that drift up, the last few stars fading out.
DEATH_FRAMES = 10
DEATH_IN_AIR = (7, 8, 9)          # only stars left, risen off the ground
DEATH_STARS = (P.VC_STAR, P.VC_RIM_L, P.VC_EYE_GLOW, P.WHITE)


def _death(body: Image.Image) -> list[Image.Image]:
    a = body.getchannel("A").load()
    w, h = body.size
    pixels = [(x, y) for y in range(h) for x in range(w) if a[x, y]]
    top = min(y for _, y in pixels)
    bottom = max(y for _, y in pixels)
    rnd = draw.noise(77)
    # When each pixel goes (0...1): random, a little earlier at the top, so the cat dissolves from the head down.
    goes = {(x, y): 0.15 + 0.7 * rnd() + 0.15 * (bottom - y) / max(1, bottom - top) for x, y in pixels}
    src = body.load()
    out = []
    for k in range(DEATH_FRAMES):
        t = k / (DEATH_FRAMES - 2)                        # 0 at the flash, 1 at the second-last frame
        frame = Image.new("RGBA", body.size, (0, 0, 0, 0))
        dst = frame.load()
        if k == 0:
            white = Image.blend(body, Image.new("RGBA", body.size, (*P.WHITE[:3], 255)), 0.6)
            white.putalpha(body.getchannel("A"))
            out.append(white)
            continue
        stars = draw.noise(500)
        for x, y in pixels:
            g = goes[x, y]
            if g > t:
                dst[x, y] = src[x, y]
            elif t - g < 0.25 and stars() < 0.012:          # just gone: a star rising from where it was
                sy = y - round((t - g) * 4 * 40 * SCALE)
                colour = DEATH_STARS[int(stars() * len(DEATH_STARS)) % len(DEATH_STARS)]
                for dx, dy in ((dx, dy) for dx in range(SCALE) for dy in range(SCALE)):     # one point
                    if 0 <= x + dx < w and 0 <= sy + dy < h:
                        dst[x + dx, sy + dy] = (*colour[:3], 255)
        out.append(clean(frame))
    return out


# Projectile rows (SHADOW PAW, FALLING STAR, VOID WAVE, STAR SHARD, PORTAL ENTRY, PORTAL EXIT): one cell per painted
# frame, its soft glow kept from alpha 120 (the portals' from 200). Painted pointing right: mirrored to fly left, as
# the game draws hazards.


def _small(y0: int, y1: int, spans: tuple, alpha: int = 120) -> list[Cut]:
    return [Cut((x0, y0, x1, y1), cleared=LABELS, alpha=alpha, core=1) for x0, x1 in spans]



PROJECTILES = {
    "shadow_paw": _small(762, 821, ((24, 90), (96, 148), (153, 205), (208, 262), (265, 316), (318, 366), (369, 414))),
    "falling_star": _small(762, 821, ((448, 478), (503, 531), (554, 586), (607, 646))),
    "void_wave": _small(762, 821, ((890, 950), (952, 1006), (1007, 1066), (1068, 1128), (1129, 1190),
                                   (1191, 1258))),
    "star_shard": _small(762, 821, ((1344, 1416), (1422, 1485), (1488, 1556), (1558, 1618), (1620, 1684),
                                    (1686, 1762))),
    # The portal at its widest (PORTAL ENTRY 3 and 4, PORTAL EXIT 3), then PORTAL EXIT 4-7 shrinking to a spark.
    # The portals' glow is wide and round: they are cut from alpha 200, the ring with a thin rim of glow (the last
    # spark, all glow, from 120).
    "open": _small(822, 887, ((181, 232), (247, 293), (600, 668)), alpha=200),
    "close": _small(822, 887, ((671, 712), (722, 762), (776, 806)), alpha=200) + _small(822, 887, ((826, 842),)),
}
# (sprite, painted frames, frame size in points, fps). The brief's sizes: the void wave and star shard frames are as
# big as their 24×12 and 20×8 hitboxes (the code-drawn ones were smaller); the shadow paw keeps its 40×14 frame, the
# solid paw at the front (on the left) as tall as the 16×14 hitbox, its smoke trail behind.
#   shadow paw: SHADOW PAW 1-6 (the paw rolling, its smoke curling); 0, a thin streak, is left out.
#   falling star: FALLING STAR 0-3 and back (it twinkles, its trail streaming up above it); 4-7, the burst where it
#                 lands, are not played (the game removes the star when it lands).
#   void wave: VOID WAVE 3-5, the full dark crescent with its lit crest (0-2 are it forming).
#   star shard: STAR SHARD 0-5, the crystal glinting.
HAZARDS = {
    "shadow_paw": ((1, 2, 3, 4, 5, 6), (40, 14), 12),
    "falling_star": ((0, 1, 2, 3, 2, 1), (12, 16), 12),
    "void_wave": ((3, 4, 5), (26, 12), 12),
    "star_shard": ((0, 1, 2, 3, 4, 5), (22, 8), 12),
}
# `portal`: an upright swirling oval standing on its bottom row, 26×36 as the code-drawn one. `open` (looping while
# yarn is bent through it): the three widest rings painted (PORTAL ENTRY 3, 4, PORTAL EXIT 3, then ENTRY 4 again), the
# swirl turning; ENTRY 0-2 and 5-6 are smaller (opening, settling) and would make the loop pulse. `close` (once, as it
# shuts): PORTAL EXIT 4-7, shrinking to a spark. The open ring is `PORTAL_TALL` points tall with its glow (about 23
# wide; the code-drawn one was 20×32).
PORTAL_SIZE = (26, 36)
PORTAL_TALL = 30


def _mirrored(cut: Cut) -> Piece:
    piece = SHEET.cut(cut)
    piece.image = ImageOps.mirror(piece.image)
    return piece


def hazards() -> list[Sprite]:
    s = SCALE
    out = []
    for name, (picked, size, fps) in HAZARDS.items():
        pieces = [_mirrored(PROJECTILES[name][i]) for i in picked]
        box = (size[0] * s, size[1] * s)
        k = fit_scale(pieces, box)
        sprite = Sprite(f"hazard_{name}", size, scale=s)
        align = "centre" if name == "falling_star" else "left"
        sprite.add("fly", [fit(p, box, align=align, k=k) for p in pieces], fps=fps)
        out.append(sprite)
    pieces = {key: [SHEET.cut(c) for c in PROJECTILES[key]] for key in ("open", "close")}
    box = (PORTAL_SIZE[0] * s, PORTAL_SIZE[1] * s)
    # The three rings are painted a little different in size: each is brought to `PORTAL_TALL` (no pulsing loop).
    ks = [PORTAL_TALL * s / p.image.height for p in pieces["open"]]
    k = min(ks)
    gate = Sprite("portal", PORTAL_SIZE, scale=s)
    gate.add("open", [fit(pieces["open"][i], box, align="centre", k=ks[i]) for i in (0, 1, 2, 1)], fps=10)
    gate.add("close", [fit(p, box, align="centre", k=k) for p in pieces["close"]], fps=12, loop=False)
    out.append(gate)
    return out


NAMES = {"boss_voidcat", "hazard_shadow_paw", "hazard_falling_star", "hazard_void_wave", "hazard_star_shard", "portal"}


def build() -> list[Sprite]:
    return [boss(), *hazards()]
