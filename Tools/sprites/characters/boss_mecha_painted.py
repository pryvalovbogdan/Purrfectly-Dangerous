"""The Mecha-Mouser and its projectiles, cut from the user's painted sheet (`sheet_boss.py`).

Source: `docs/concept/Mecha Mouser Boss Sheet.png`, copied to `Tools/sprites/boss_mecha_source.png`, painted after
`docs/boss-mecha-sheet-brief.md` with real transparency (the machine is nearly opaque, alpha 247-254): one sheet, the
machine's rows on top (IDLE, ROCKETS, TAIL SWEEP, CORE BARRAGE and DEATH side by side), the projectile and effect
rows below. It differs from the brief: no HURT and no separate CORE row, fewer frames than the brief asks for and
than the labels say. Replaces the code-drawn `boss_mecha` (`boss_mecha.py`) and `hazard_rocket`,
`hazard_burning_patch` (`boss_hazards.py`): those modules skip a sprite whose name is in `NAMES`. Same sprite names,
animation names, frame sizes (in points) and anchor. `hazard_tail`, `hazard_claw` and the citadel's `vent` stay
code-drawn: the painted TAIL WAVE and CLAW PROJECTILE are tall arcs and arrowheads that cannot cover their low,
long hitboxes (30×12, 50×12) inside their frames, and FLAME VENT has no off state for the level trap.
"""
from __future__ import annotations

from PIL import Image, ImageOps

from sheet_boss import BossSheet, best_shift, body_mask, cells, clean, shrink
from sprite import Sprite

# Points. Larger than the code-drawn boss (168×124, x 84, ground 120) so nothing is cut at the frame's edge: the
# raised rocket pod and ears of ROCKETS 2-6 reach 137 points up, the fiery arcs of TAIL SWEEP 5-8 96 points ahead of
# the chest and the tail 94 behind. The anchor (the chest on the ground) is the same point, so the game is unchanged.
SIZE = (192, 140)
CX, GROUND = 96, 136
SCALE = 3

SHEET = BossSheet(source="boss_mecha_source.png", alpha=200, core=246)

# The label pills (the IDLE pill hides the top of IDLE 0's ear: that ear is cut flat where the pill was).
LABELS = ((13, 3, 134, 32), (14, 156, 160, 186), (14, 323, 190, 353), (14, 475, 192, 500), (728, 475, 864, 500),
          (14, 688, 156, 718), (14, 778, 214, 810))


def _row(y0: int, y1: int, edges: list[int], extra: dict | None = None, **kw):
    return cells(y0, y1, edges, LABELS, extra, **kw)


# One cell per painted machine, edges halfway between their chests. The tails reach under the neighbours, so every
# machine near a cell grows at once from its own middle (`seeds`, a watershed along the dark outlines).
# `cleared` (sheet coordinates) wipes what is not the machine: the steam puffs behind ROCKETS 4-5, the flying rocket
# and its smoke trail over ROCKETS 6 (the launch flash at the hip stays), the smoke puff and sparks in CORE BARRAGE 4,
# and the neighbour's rear that a fiery arc in TAIL SWEEP 7-8 reaches.
ROWS = {
    "idle": _row(8, 151, [5, 164, 306, 454, 606, 755, 902, 1056, 1214, 1367, 1530], seeds=15),
    "rockets": _row(153, 320, [5, 166, 285, 404, 524, 648, 798, 982, 1188, 1376, 1530], seeds=15, extra={
        4: (("o", 528, 268, 10, 13),),
        5: (("o", 655, 268, 11, 12),),
        6: ((755, 153, 818, 232), (818, 153, 865, 191), ("o", 828, 270, 15, 18)),
    }),
    "tail": _row(320, 471, [5, 173, 297, 423, 566, 726, 879, 1027, 1196, 1366, 1530], seeds=15, extra={
        7: (("r", ((1214, 320), (1214, 471))),),
        8: (("r", ((1374, 320), (1374, 471))),),
    }),
    "barrage": _row(473, 644, [5, 153, 269, 368, 472, 596, 727], seeds=15, extra={
        4: (("o", 481, 545, 19, 17),),
    }),
    "death": _row(473, 644, [727, 845, 974, 1112, 1248, 1386, 1534], seeds=15, keep_all=True, min_bits=60),
}

# Points per sheet pixel: the machine is painted about 131 px tall with its ears (the feet on sheet row 148); at 0.87
# it is about 114 points tall, a little under the code-drawn boss (119), so the tallest pose (ROCKETS 6, painted 156
# px) fits the frame; the body column from the feet to the top of the head (about 94 points) fills the 50×104 hitbox
# 4 above the ground, the ears reaching its top. At 3x detail every sheet pixel becomes 2.6 texture pixels (LANCZOS);
# the engine draws them nearest.
K = 0.87
BODY = 70                         # points above the ground compared when lining frames up (the legs and torso)
REACH = 30                        # the most a frame is shifted to line up with the one before it (points)
ANCHOR = 234                      # sheet x of IDLE 1's chest (its body without the tail), put on `CX`
HURT_JOLT = (-3, -5, -2)          # HURT: IDLE 1 knocked back this many points (and the game's white flash)

# Animations: (painted row, painted frames played in order, fps, loop). GameScene plays an attack once from the start
# of its wind-up and holds the last frame, so the frame at position N in the list shows at N / fps seconds; the fps
# puts the release where Bosses.json `boss_mecha` releases the hazard:
#   rockets: ROCKETS painted 10 frames with one launch (6, the flash at the hip, the body turned in recoil). Played
#            0-8, then the aim and launch again (4, 5, 6), then 7-9: launches at positions 6 and 11, at 6 / 7 = 0.86 s
#            and 11 / 7 = 1.57 s (the rockets leave at 0.9 and 1.6 s). Ends on 9 (the pod folded down; no venting).
#   tail: TAIL SWEEP painted 10: 0-3 the tail coiling behind, 4 the clawed limb thrust forward low with the first
#         flame (4 / 4.67 = 0.86 s, as the flame vent springs up at 0.9 s), 7 the biggest fiery arc at the ground
#         (7 / 4.67 = 1.50 s, the tail sweep leaves at 1.5 s), 9 the tail whipped round in front.
#   core: CORE BARRAGE painted 6; the chest is open only in 4 and 5 and the tail is hidden from 2 on, so the resting
#         loop from 12 HP (which `core_barrage` also plays: GameScene maps it to `core`) is 2, 3, 4, 5, 4, 3, the
#         core flaring and dimming, at 6 fps (1 s). Nothing in it lines up with the barrage's hits.
#   idle: IDLE painted 10; 0 is drawn differently (and its ear is under the label), so 1-9 and back (the tail swings
#         out and back), at 12 fps (1.33 s a loop).
PLAN = {
    "idle": ("idle", (*range(1, 10), *range(8, 1, -1)), 12, True),
    "rockets": ("rockets", (*range(9), 4, 5, 6, 7, 8, 9), 7, False),
    "tail": ("tail", tuple(range(10)), 4.67, False),
    "core": ("barrage", (2, 3, 4, 5, 4, 3), 6, True),
    "death": ("death", tuple(range(6)), 6, False),          # 1 s, ends on the burning scrap heap
}


def boss() -> Sprite:
    fw, fh = SIZE[0] * SCALE, SIZE[1] * SCALE
    ground = GROUND * SCALE + SCALE - 1          # the lowest pixel row of point row GROUND
    centre = CX * SCALE + SCALE / 2
    k = K * SCALE
    body, reach = BODY * SCALE, REACH * SCALE
    pieces = {name: [SHEET.cut(c) for c in row] for name, row in ROWS.items()}
    small = {name: [shrink(p.image, k) for p in ps] for name, ps in pieces.items()}
    masks = {name: [body_mask(im, body) for im in ims] for name, ims in small.items()}

    # Where each frame's left edge goes (frame pixels): IDLE 1 with its chest on the anchor; every other frame lined
    # up with the one before it by its legs and torso (`best_shift`), so the body stays put and only real moves show.
    # Each row's first and last frame are lined up with IDLE 1 and the drift between is spread over the row (DEATH,
    # which collapses into a heap, only follows the chain).
    ref = masks["idle"][1]
    lefts = {}
    for name in ROWS:
        ms = masks[name]
        if name == "idle":
            xs = [0, round(centre - (ANCHOR - pieces["idle"][1].box[0]) * k)]
            for a, b in zip(ms[1:], ms[2:]):
                xs.append(xs[-1] + best_shift(a, b, reach))
            xs[0] = xs[1] - best_shift(ms[0], ms[1], reach)
        else:
            xs = [lefts["idle"][1] + best_shift(ref, ms[0], reach)]
            for a, b in zip(ms, ms[1:]):
                xs.append(xs[-1] + best_shift(a, b, reach))
            if name != "death":
                end = lefts["idle"][1] + best_shift(ref, ms[-1], reach)
                n = len(xs) - 1
                xs = [round(x + (end - xs[-1]) * i / n) for i, x in enumerate(xs)]
        lefts[name] = xs

    def frame(im: Image.Image, x: int, dx: int = 0) -> Image.Image:
        out = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        out.paste(im, (x + dx, ground + 1 - im.height), im)
        return clean(out)

    sprite = Sprite("boss_mecha", SIZE, faces_left=True, cx=CX, ground=GROUND, scale=SCALE)
    for name, (row, plan, fps, loop) in PLAN.items():
        sprite.add(name, [frame(small[row][i], lefts[row][i]) for i in plan], fps=fps, loop=loop)
        if name == "idle":
            rest = small["idle"][1], lefts["idle"][1]
            sprite.add("hurt", [frame(*rest, dx=d * SCALE) for d in HURT_JOLT], fps=12, loop=True)
    sprite.anims = {name: sprite.anims[name] for name in ("idle", "rockets", "tail", "core", "hurt", "death")}
    return sprite


# Projectile rows. Painted pointing right (up-right for the rocket): turned here to point left, the way they fly.
EXTRA = {
    "rocket": _row(700, 780, [20, 120, 220, 332, 440, 560, 668, 780], alpha=150, core=1),
    "patch": _row(800, 882, [20, 80, 152, 230, 316, 420, 536, 656, 775], alpha=150, core=1),
}
ROCKET_TILT = 17                  # degrees the painted rockets climb; levelled out before they are framed
ROCKET_HEIGHT = 8                 # points: the rocket's body with its fins, as tall as its 20×8 hitbox
PATCH_FRAMES = (2, 3, 4, 3)       # BURNING PATCH 2-4 burn, flickering (0-1 are embers catching, 5-7 smoke dying out)
PATCH_HEIGHT = 18                 # points: the tallest flame, over the 10×16 hitbox


def _alpha_bbox_rows(image: Image.Image, top: float) -> tuple[int, int]:
    """The vertical extent of the opaque pixels in the leading `top` part (fraction of the width) of `image`."""
    w = max(1, round(image.width * top))
    box = image.crop((0, 0, w, image.height)).getbbox()
    return box[1], box[3]


def hazards() -> list[Sprite]:
    s = SCALE

    def sprite(name: str, frames: list, fps: int) -> Sprite:
        out = Sprite(f"hazard_{name}", (frames[0].width // s, frames[0].height // s), scale=s)
        out.add("fly", frames, fps=fps)
        return out

    # The rocket: mirrored to point left, levelled, nose on the frame's left edge, the body (the leading 35% of the
    # cut, before the flame) ROCKET_HEIGHT tall and centred; the flame behind is cut at the frame's right edge, the smoke with it.
    rockets = []
    turned = []
    for cut in EXTRA["rocket"]:
        im = ImageOps.mirror(SHEET.cut(cut).image).rotate(ROCKET_TILT, resample=Image.BICUBIC, expand=True)
        im.putalpha(im.getchannel("A").point(lambda a: 255 if a >= 128 else 0))
        turned.append(clean(im))
    nose = []
    for im in turned:
        box = im.getbbox()
        im = im.crop(box)
        a = im.getchannel("A").load()
        tip = min(x for x in range(im.width) for y in range(im.height) if a[x, y])
        nose.append((im, tip))
    fw, fh = 22 * s, 10 * s
    for im, tip in nose:
        # Each frame to the same body height: the first rockets are painted smaller, and would pulse in the loop.
        top, bottom = _alpha_bbox_rows(im, 0.35)
        kk = ROCKET_HEIGHT * s / (bottom - top)
        small = shrink(im, kk)
        y0, y1 = _alpha_bbox_rows(small, 0.35)
        out = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
        out.paste(small, (-round(tip * kk), round(fh / 2 - (y0 + y1) / 2)), small)
        rockets.append(clean(out))

    # The burning patch: one size for all, the tallest flame PATCH_HEIGHT points, centred, on the bottom row; the
    # wide ground glow is cut at the frame's sides.
    cut = {i: SHEET.cut(EXTRA["patch"][i]) for i in set(PATCH_FRAMES)}
    pieces = [cut[i] for i in PATCH_FRAMES]
    kp = PATCH_HEIGHT * s / max(p.image.height for p in pieces)
    pw, ph = 14 * s, 20 * s
    patch = []
    for p in pieces:
        small = shrink(p.image, kp)
        out = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        out.paste(small, (round((pw - small.width) / 2), ph - small.height), small)
        patch.append(clean(out))
    return [sprite("rocket", rockets, 14), sprite("burning_patch", patch, 12)]


NAMES = {"boss_mecha", "hazard_rocket", "hazard_burning_patch"}


def build() -> list[Sprite]:
    return [boss(), *hazards()]
