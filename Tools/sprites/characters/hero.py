"""The kitten hero and its ball of yarn.

The hero is a chibi orange cat standing up on its hind legs (44x36 frame, feet on row 34, body centred
on x 22): a big round head with tall ears, white muzzle, chest and paw tips, and a red cape. `chibi()`
draws it from a `HeroPose`.

`cat()` draws a side-on cat on all fours from a `CatPose`; the ghost cats reuse it.
"""
from __future__ import annotations

import math
from contextlib import contextmanager
from dataclasses import dataclass, replace

from PIL import Image

import palette as P
from draw import Canvas, end_of, r, see_through, tint
from sprite import Sprite

SIZE = (44, 36)


# ---------------------------------------------------------------------------------------------------
# Skins: every hero animation redrawn in another coat as `hero_<id>`. The drawing code reads the palette
# when it draws, so a skin swaps the fur, white, scarf/cape colours for the duration of the build
# (`wearing`), and `dress` adds eye colour, a flower or a hood to the head grids.

@dataclass(frozen=True)
class Skin:
    id: str
    fur: tuple | None = None          # light, base, shadow, stripe (None keeps the orange tabby)
    white: tuple | None = None        # muzzle, chest and paws: light, shade
    cape: tuple | None = None         # scarf and cape: light, base, dark
    iris: tuple | None = None         # coloured eyes
    flower: bool = False              # a pink flower by the ear
    patch: bool = False               # calico: a dark patch over the far ear and forehead
    hood: str | None = None           # "frog" | "shark"
    hood_colours: tuple | None = None


SKINS = (
    Skin("shadow", fur=P.SKIN_SHADOW_FUR_LIT, white=P.SKIN_SHADOW_WHITE, iris=P.SKIN_EYE_GREEN),
    Skin("misty", fur=P.SKIN_GREY_FUR, cape=(P.BLUE_L, P.BLUE, P.BLUE_D)),
    Skin("sakura", fur=P.SKIN_SNOW_FUR, cape=(P.YARN_L, P.YARN, P.YARN_D), flower=True),
    Skin("honey", fur=P.SKIN_CREAM_FUR, cape=(P.YELLOW, P.GOLD, P.GOLD_D)),
    Skin("pixie", fur=P.SKIN_PIXIE_FUR_LIT, white=P.SKIN_PIXIE_WHITE, cape=(P.PURPLE_L, P.PURPLE, P.PURPLE_D),
         iris=P.SKIN_EYE_VIOLET),
    Skin("clover", cape=(P.GREEN_L, P.GREEN, P.GREEN_D)),
    Skin("snowball", fur=P.SKIN_SNOW_FUR, cape=(P.BLUE_L, P.BLUE, P.BLUE_D), iris=P.SKIN_EYE_BLUE),
    Skin("napster", fur=P.SKIN_WARM_GREY_FUR, cape=(P.BROWN_L, P.BROWN, P.BROWN_D)),
    Skin("toffee", fur=P.SKIN_CALICO_FUR, cape=(P.BROWN_L, P.BROWN, P.BROWN_D), patch=True),
    Skin("cabage", cape=(P.LEAF_L, P.GREEN, P.FOREST), hood="frog", hood_colours=P.SKIN_FROG),
    Skin("sharky", cape=(P.BLUE, P.BLUE_D, P.NAVY), hood="shark", hood_colours=P.SKIN_SHARK),
)

_SKIN: Skin | None = None


@contextmanager
def wearing(skin: Skin):
    """Swaps the hero's palette entries for `skin` while drawing; always restores them."""
    global _SKIN
    names = ("GINGER_L", "GINGER", "GINGER_D", "GINGER_DD", "FUR_WHITE", "FUR_WHITE_D", "CAPE_L", "CAPE", "CAPE_D")
    saved = {n: getattr(P, n) for n in names}
    try:
        if skin.fur:
            P.GINGER_L, P.GINGER, P.GINGER_D, P.GINGER_DD = skin.fur
        if skin.white:
            P.FUR_WHITE, P.FUR_WHITE_D = skin.white
        if skin.cape:
            P.CAPE_L, P.CAPE, P.CAPE_D = skin.cape
        _SKIN = skin
        yield
    finally:
        for n, v in saved.items():
            setattr(P, n, v)
        _SKIN = None


# Per head grid (keyed by rows x width): rows of ears, first eye row, and the face opening a hood leaves
# (centre x, centre y, radius x, radius y), and where a flower sits by the near ear.
GRIDS = {
    (18, 18): dict(ears=5, eye=9, opening=(11.5, 12.5, 7.0, 5.5), flower=(16, 7)),
    (20, 22): dict(ears=6, eye=11, opening=(12.5, 15.0, 8.0, 6.0), flower=(19, 8)),
    (17, 18): dict(ears=5, eye=9, opening=(8.5, 12.0, 7.0, 5.0), flower=(15, 7)),
}


def dress(rows) -> list[list[str]]:
    """The head grid for the current skin: coloured irises, a flower, or a hood."""
    rows = [list(r) for r in rows]
    spec = GRIDS.get((len(rows), len(rows[0])))
    if spec is None:
        return rows
    h, w = len(rows), len(rows[0])
    if _SKIN.iris:
        for y in range(spec["eye"] - 1, spec["eye"] + 2):
            for x in range(w):
                if rows[y][x] == "K":
                    rows[y][x] = "I"
    if _SKIN.patch:                                          # calico: dark over the far ear and forehead
        for y in range(0, spec["ears"] + 4):
            for x in range(0, w // 2 - 1):
                if rows[y][x] in "FLD":
                    rows[y][x] = "S"
    if _SKIN.flower:
        fx, fy = spec["flower"]
        for x, y, ch in ((fx, fy, "Y"), (fx - 1, fy, "R"), (fx + 1, fy, "R"), (fx, fy - 1, "R"), (fx, fy + 1, "r")):
            if 0 <= x < w and 0 <= y < h:
                rows[y][x] = ch
    if _SKIN.hood:
        cx, cy, rx, ry = spec["opening"]
        tone = {"L": "h", "F": "g", "D": "j", "S": "j", "P": "j", "p": "j", "W": "g", "w": "g"}
        for y in range(spec["ears"], h):
            for x in range(w):
                inside = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1
                if rows[y][x] in tone and not inside:
                    rows[y][x] = tone[rows[y][x]]
        top = spec["ears"]
        cols = [x for x in range(w) if rows[top][x] != "."]
        left, right = min(cols), max(cols)
        for y in range(top):                                 # no cat ears under a hood
            rows[y] = ["."] * w
        for y, inset in ((top - 1, 2), (top - 2, 4)):        # a rounded dome over the crown
            for x in range(left + inset, right - inset + 1):
                rows[y][x] = "h" if x < (left + right) / 2 - 2 else "g"
        if _SKIN.hood == "frog":                             # two frog eyes on top
            for ex in (left + 3, right - 3):
                for dx, dy, ch in ((-1, -3, "g"), (0, -3, "g"), (1, -3, "g"), (-2, -2, "g"), (2, -2, "g"),
                                   (-1, -2, "T"), (0, -2, "T"), (1, -2, "T"), (-1, -1, "T"), (0, -1, "K"),
                                   (1, -1, "T"), (-2, -1, "g"), (2, -1, "g")):
                    x, y = ex + dx, top + dy
                    if 0 <= x < w and 0 <= y < h:
                        rows[y][x] = ch
        else:                                                # a shark fin, and teeth round the face opening
            mid = (left + right) // 2
            for k in range(4):
                for x in range(mid - k - 1, mid + 1):
                    if top - 2 - (3 - k) >= 0:
                        rows[top - 2 - (3 - k)][x] = "j" if x == mid else "g"
            ty = int(cy - ry)
            for x in range(int(cx - rx) + 1, int(cx + rx)):
                if 0 <= ty < h and rows[ty][x] != ".":
                    rows[ty][x] = "T"
                    if x % 2 == 0 and ty + 1 < h:
                        rows[ty + 1][x] = "T"
    return rows

CX, GROUND = 22, 34

@dataclass(frozen=True)
class Coat:
    fur: tuple = P.GINGER
    fur_l: tuple = P.GINGER_L
    fur_d: tuple = P.GINGER_D
    stripe: tuple = P.GINGER_DD
    belly: tuple = P.CREAM
    belly_d: tuple = P.CREAM_D
    nose: tuple = P.PINK
    eye: tuple = P.BLACK
    shine: tuple = P.WHITE
    inner_ear: tuple = P.PINK


TABBY = Coat()


@dataclass(frozen=True)
class CatPose:
    """Angles in degrees: 0 = straight down, positive = forward (toward the nose).
    Each leg is (upper angle, lower angle), both absolute."""
    front_near: tuple = (8, 0)
    front_far: tuple = (-6, -6)
    back_near: tuple = (-6, 0)
    back_far: tuple = (8, 0)
    stretch: float = 0      # body longer (+) or bunched up (-)
    tilt: float = 0         # chest this many pixels higher than the rump (+ = nose up)
    lift: float = 0         # pixels above the ground
    tail: float = 50        # tail root angle above straight back (90 = straight up)
    curl: float = 9         # how much the tail bends forward per segment
    head_dx: float = 0
    head_dy: float = 0
    eye: str = "open"       # open | shut | x | wide
    mouth: bool = False
    ears_back: bool = False
    bib: bool = True


UPPER, LOWER = 3.5, 3.2


def _leg_end(start, leg) -> tuple[float, float]:
    knee = end_of(start, leg[0], UPPER)
    return end_of(knee, leg[1], LOWER)


def cat(c: Canvas, pose: CatPose, cx: float = CX, ground: float = GROUND, coat: Coat = TABBY) -> dict:
    """Draws a right-facing cat whose lowest paw rests on `ground` (minus `pose.lift`)."""
    half = 4.5 + pose.stretch / 2

    def anchors(by: float):
        chest = (cx + half, by - pose.tilt / 2)
        rump = (cx - half, by + pose.tilt / 2)
        shoulder = (chest[0] + 0.5, chest[1] + 2)
        hip = (rump[0] - 0.5, rump[1] + 2)
        return chest, rump, shoulder, hip

    _, _, shoulder0, hip0 = anchors(0.0)
    lowest = max(_leg_end(shoulder0, pose.front_near)[1], _leg_end(shoulder0, pose.front_far)[1],
                 _leg_end(hip0, pose.back_near)[1], _leg_end(hip0, pose.back_far)[1])
    by = ground - 0.5 - pose.lift - lowest
    chest, rump, shoulder, hip = anchors(by)

    def leg(start, spec, color, paw):
        knee = c.limb(start, spec[0], UPPER, color, 2)
        foot = c.limb(knee, spec[1], LOWER, color, 2)
        c.rect(foot[0] - 0.5, foot[1] - 0.5, foot[0] + 1.5, foot[1] + 0.5, paw)
        return foot

    # Far legs, darker, behind everything.
    leg((shoulder[0] - 1, shoulder[1]), pose.front_far, coat.fur_d, coat.belly_d)
    leg((hip[0] + 1, hip[1]), pose.back_far, coat.fur_d, coat.fur_d)

    # Tail: a chain of short segments that curls toward the tip, with a ringed tabby pattern.
    base = (rump[0] - 3, rump[1] - 1.5)
    angle = pose.tail
    point = base
    for i in range(10):
        rad = math.radians(angle)
        nxt = (point[0] - math.cos(rad) * 1.15, point[1] - math.sin(rad) * 1.15)
        color = coat.stripe if i in (4, 8, 9) else coat.fur
        c.rect(nxt[0] - 0.5, nxt[1] - 0.5, nxt[0] + 0.5, nxt[1] + 0.5, color)
        point = nxt
        angle += pose.curl
    tail_tip = point

    # Body: a capsule from rump to chest; the haunch is a touch bigger than the chest.
    steps = 10
    for i in range(steps + 1):
        t = i / steps
        x = rump[0] + (chest[0] - rump[0]) * t
        y = rump[1] + (chest[1] - rump[1]) * t
        c.ellipse(x, y, 3.2, 3.9 - t * 0.6, coat.fur)
    # Belly shadow, back highlight and tabby stripes across the back.
    for i in range(steps + 1):
        t = i / steps
        x = rump[0] + (chest[0] - rump[0]) * t
        y = rump[1] + (chest[1] - rump[1]) * t
        c.px(x, y + 3.2 - t * 0.6, coat.fur_d)
        if 0.15 < t < 0.85:
            c.px(x, y - 3.2 + t * 0.6, coat.fur_l)
    for t in (0.22, 0.45, 0.68):
        x = rump[0] + (chest[0] - rump[0]) * t
        y = rump[1] + (chest[1] - rump[1]) * t - 3.6 + t * 0.6
        c.rect(x, y + 1, x, y + 2.5, coat.stripe)
    if pose.bib:
        c.ellipse(chest[0] + 1.5, chest[1] + 1.5, 1.6, 2.0, coat.belly)

    leg(hip, pose.back_near, coat.fur, coat.belly)
    # Haunch over the top of the near hind leg.
    c.ellipse(rump[0] - 0.5, rump[1] + 0.5, 2.2, 2.4, coat.fur)
    c.px(rump[0] - 1, rump[1] + 0.5, coat.stripe)
    c.px(rump[0], rump[1] - 0.5, coat.stripe)
    leg(shoulder, pose.front_near, coat.fur, coat.belly)

    # Head, in front of the chest.
    hx, hy = chest[0] + 4.5 + pose.head_dx, chest[1] - 3.5 + pose.head_dy
    for ex, tip in ((hx - 3.0, -2.5), (hx + 1.0, -1.0)):
        if pose.ears_back:
            c.poly([(ex - 2, hy - 2), (ex - 3.5 + tip / 3, hy - 4.5), (ex + 1.5, hy - 3.5)], coat.fur)
        else:
            c.poly([(ex - 1.8, hy - 2), (ex - 0.5 + tip / 4, hy - 7), (ex + 1.8, hy - 2)], coat.fur)
            c.px(ex - 0.3 + tip / 6, hy - 4, coat.inner_ear)
    c.ellipse(hx, hy, 4.3, 3.6, coat.fur)
    c.ellipse(hx + 0.5, hy + 1.2, 4.6, 2.6, coat.fur)
    c.rect(hx - 1, hy - 3.5, hx - 1, hy - 2.5, coat.stripe)       # forehead stripes
    c.rect(hx + 1, hy - 3.5, hx + 1, hy - 3, coat.stripe)
    c.px(hx - 3.5, hy + 0.5, coat.stripe)                          # cheek stripe
    c.ellipse(hx + 3, hy + 1.8, 2.0, 1.4, coat.belly)              # muzzle
    c.px(hx + 4.5, hy + 0.5, coat.nose)
    if pose.mouth:
        c.rect(hx + 3, hy + 2.5, hx + 4, hy + 3, P.PINK_D)
    ex, ey = hx + 1.5, hy - 0.5
    if pose.eye == "open":
        c.rect(ex, ey - 1, ex + 1, ey + 1, coat.eye)
        c.px(ex + 1, ey - 1, coat.shine)
    elif pose.eye == "wide":
        c.rect(ex - 0.5, ey - 1.5, ex + 1, ey + 1, coat.eye)
        c.px(ex + 1, ey - 1.5, coat.shine)
        c.px(ex - 0.5, ey + 1, coat.shine)
    elif pose.eye == "shut":
        c.rect(ex - 0.5, ey + 0.5, ex + 1, ey + 0.5, coat.eye)
    elif pose.eye == "x":
        c.line((ex - 1, ey - 1), (ex + 1, ey + 1), coat.eye)
        c.line((ex - 1, ey + 1), (ex + 1, ey - 1), coat.eye)
    return {"head": (hx, hy), "chest": chest, "rump": rump, "tail_tip": tail_tip,
            "paw": _leg_end(shoulder, pose.front_near)}



# ---------------------------------------------------------------------------------------------------
# The hero: an upright chibi cat.

@dataclass(frozen=True)
class HeroPose:
    """Angles in degrees: 0 = straight down, positive = forward (toward the nose), 180 = straight up.
    Legs and arms are (upper, lower) absolute angles."""
    near_leg: tuple = (4, 0)
    far_leg: tuple = (-6, -4)
    near_arm: tuple = (10, 25)
    far_arm: tuple = (-6, 15)
    lean: float = 0          # torso tilt forward; 90 = lying flat along the ground, nose first
    length: float = 0        # torso stretched (+) or squashed (-)
    reach: float = 0         # arms longer by this much per segment (throwing, reaching)
    arm_behind: bool = True   # near arm under the head, so it never crosses the face
    chunky: bool = False      # thick legs with flat white paws and toe marks (poses shown big on screens)
    lift: float = 0          # pixels above the ground
    head_dx: float = 0
    head_dy: float = 0
    cape: float = 35         # 0 = hangs straight down, 90 = streams straight back, more = lifts
    cape_len: float = 15
    flap: float = 0          # phase of the ripple running down the cape
    ripple: float = 14       # how much the cape ripples
    tail: float = -35        # tail root angle above straight back (90 = up, negative = drooping)
    curl: float = 18         # how much the tail bends forward per segment
    eye: str = "open"        # open | shut | wide | x | squint | happy (closed "^ ^")
    mouth: bool = False
    smile: bool = False      # a wide open happy mouth (overrides `mouth`)
    tongue: bool = False     # tongue poking out under the nose (knocked out)
    frown: bool = False      # a small sad mouth
    ears_back: bool = False


THIGH, SHIN, UPPER_ARM, FOREARM = 2.8, 2.6, 2.2, 2.2
TORSO = 6.5
PAD = 24  # scratch margin around the frame while posing


def _ribbon(c: Canvas, root, angle, length, flap, ripple, width0, width1, light, dark, edge=None):
    """A cloth strip from `root`: direction `angle` (0 = down, 90 = back), rippling, widening toward the end."""
    steps = 9
    seg = length / steps
    top, bottom = [], []
    point = root
    for i in range(steps + 1):
        t = i / steps
        a = math.radians(angle + math.sin(flap - i * 0.85) * ripple * t)
        direction = (-math.sin(a), math.cos(a))
        normal = (-direction[1], direction[0])            # the upper/outer side
        w = width0 + (width1 - width0) * t
        if i == steps:                                     # swallow-tail end
            w *= 0.55
        top.append((point[0] + normal[0] * w / 2, point[1] + normal[1] * w / 2))
        bottom.append((point[0] - normal[0] * w / 2, point[1] - normal[1] * w / 2))
        if i < steps:
            point = (point[0] + direction[0] * seg, point[1] + direction[1] * seg)
    mid = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in zip(top, bottom)]
    for i in range(steps):
        c.poly([top[i], top[i + 1], mid[i + 1], mid[i]], light)
        c.poly([mid[i], mid[i + 1], bottom[i + 1], bottom[i]], dark)
    tip = (point[0], point[1])
    c.poly([top[-1], tip, bottom[-1]], P.CLEAR)            # notch in the end
    if edge is not None:                                   # a clean light edge along the top
        for i in range(1, steps - 1):
            c.line(top[i], top[i + 1], edge)
    return tip


def chibi(c: Canvas, pose: HeroPose, cx: float, ground: float) -> dict:
    """Draws the hero facing right; the lowest pixel of its body (not the cape or tail) rests on `ground`
    (minus `pose.lift`)."""
    w, h = c.size
    body = Canvas(w + PAD * 2, h + PAD * 2)
    back = Canvas(w + PAD * 2, h + PAD * 2)
    joints = _chibi_at(body, back, pose, (cx + PAD - 0.5, PAD + h / 2))
    box = body.img.getbbox()
    dy = r(ground - pose.lift) - (box[3] - 1 - PAD) if box else 0
    back.paste(body)
    c.paste(back.img, -PAD, -PAD + dy)
    return {k: (v[0] - PAD, v[1] - PAD + dy) for k, v in joints.items()}


# The head is drawn pixel by pixel, so the ears, eyes and muzzle are crisp and identical in every frame; only
# the expression changes (see `_face`). Facing right, three-quarter view; the outline is added afterwards.
#   F fur  L light  D shadow  S stripe  W white  w white shadow  P pink  p dark pink  K eye  H shine
HEAD = (
    "...D...........F..",
    "...DF.........FF..",
    "..DPF........FPF..",
    "..DPPF......FPPF..",
    ".DDPPFF....FPPPFF.",
    "..DLLSLSFFWWFSFF..",
    ".DLLLSLSFFWWFSFFF.",
    "DFLLFFFFFFWWFFFFFF",
    "DFFFFFFFFFWWFFFFFF",
    "DFFFFFFHKFWWFHKKFF",
    "DFFFFFFKKWWWWKKKFF",
    "DSSFFFFKKWPPWKKKWF",
    ".DFFFFFWWpWWpWWWWF",
    "DDFFFFWWWWppWWWWWF",
    ".DDFFFwWWWWWWWWWF.",
    "..DDDDwwWWWWWWWF..",
    "...DDDDwwwWWWWD...",
    ".....DDDwwwwD.....",
)
EARS_BACK = (
    "..................",
    "..................",
    ".DD.............FF",
    "..DDPF.......FPFF.",
    "...DPPF.....FPPF..",
)
HEAD_CENTRE = (8.5, 11)          # the stamp pixel that sits on the head joint
FAR_EYE, NEAR_EYE = (7, 9), (13, 9)    # three-quarter view: the far eye is narrower
def stamp_colours() -> dict:
    """Colours of the head-grid characters, read from the palette when drawing (skins swap the palette)."""
    hood = _SKIN.hood_colours if _SKIN and _SKIN.hood_colours else (P.WHITE, P.WHITE, P.WHITE)
    return {"F": P.GINGER, "L": P.GINGER_L, "D": P.GINGER_D, "S": P.GINGER_DD, "W": P.FUR_WHITE,
            "w": P.FUR_WHITE_D, "P": P.PINK, "p": P.PINK_D, "K": P.BLACK, "H": P.WHITE,
            "I": _SKIN.iris if _SKIN and _SKIN.iris else P.BLACK,          # iris, coloured-eye skins
            "R": P.YARN, "Y": P.YELLOW, "r": P.YARN_D,                       # sakura's flower
            "h": hood[0], "g": hood[1], "j": hood[2], "T": P.WHITE, "O": P.OUTLINE}   # hoods
assert all(len(row) == 18 for row in HEAD + EARS_BACK)


def _face(pose: HeroPose) -> list[list[str]]:
    """The head stamp with this pose's ears, eyes and mouth."""
    rows = [list(row) for row in HEAD]
    if pose.ears_back:
        rows[:5] = [list(row) for row in EARS_BACK]
    if pose.eye != "open":
        for x0, y0 in (FAR_EYE, NEAR_EYE):                  # clear both eyes back to fur
            for y in range(y0, y0 + 3):
                for x in range(x0, x0 + 3):
                    if rows[y][x] in "KH":
                        rows[y][x] = "F"
        marks = {
            "shut": [(7, 10), (8, 10), (13, 10), (14, 10), (15, 10)],
            "wide": [(x, y) for x0, n in ((7, 2), (13, 3)) for x in range(x0, x0 + n) for y in range(8, 12)],
            "squint": [(7, 9), (8, 10), (7, 11), (15, 9), (14, 10), (15, 11)],
            "x": [(6, 9), (8, 9), (7, 10), (6, 11), (8, 11), (13, 9), (15, 9), (14, 10), (13, 11), (15, 11)],
            "sad": [(7, 10), (8, 10), (8, 11), (7, 11), (13, 10), (14, 10), (15, 10), (13, 11), (14, 11),
                    (15, 11), (8, 9), (13, 9)],
            "happy": [(6, 11), (7, 10), (8, 10), (9, 11), (13, 11), (14, 10), (15, 10), (16, 11)],
        }[pose.eye]
        for x, y in marks:
            rows[y][x] = "K"
        if pose.eye == "wide":
            rows[8][7] = rows[8][13] = rows[11][15] = "H"
    if pose.smile:                                           # a wide open "D" smile with a pink tongue
        for x, y, ch in ((9, 12, "K"), (10, 12, "K"), (11, 12, "K"), (12, 12, "K"), (9, 13, "K"), (10, 13, "p"),
                         (11, 13, "p"), (12, 13, "K"), (10, 14, "K"), (11, 14, "K"), (9, 14, "W"), (12, 14, "W")):
            rows[y][x] = ch
    elif pose.tongue:                                        # mouth open, tongue lolling out
        for x, y, ch in ((10, 12, "K"), (11, 12, "K"), (10, 13, "P"), (11, 13, "P"), (10, 14, "p"), (11, 14, "P"),
                         (12, 14, "p"), (11, 15, "p")):
            rows[y][x] = ch
    elif pose.frown:                                         # a little upside-down "u"
        for x, y in ((9, 14), (10, 13), (11, 13), (12, 14)):
            rows[y][x] = "K"
    elif pose.mouth:                                         # a small open "o" under the nose
        for x, y in ((10, 12), (11, 12), (10, 13), (11, 13)):
            rows[y][x] = "p"
        rows[12][9] = rows[12][12] = "W"
        rows[13][10] = "K"
    return rows


def _stamp(c: Canvas, rows, x0: int, y0: int) -> None:
    rows = dress(rows) if _SKIN else rows
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                c.px(x0 + x, y0 + y, stamp_colours()[ch])


def despeckle(c: Canvas) -> Canvas:
    """Replaces lone pixels (no neighbour of the same colour, three or four of another) with that colour, so
    posed shapes are made of clean flat areas."""
    src = c.img.load()
    w, h = c.img.size
    fixes = []
    for y in range(h):
        for x in range(w):
            colour = src[x, y]
            if colour[3] == 0:
                continue
            around = [src[nx, ny] if 0 <= nx < w and 0 <= ny < h else P.CLEAR
                      for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))]
            if colour in around:
                continue
            best = max(set(around), key=around.count)
            if around.count(best) >= 3:
                fixes.append((x, y, best))
    for x, y, colour in fixes:
        src[x, y] = colour
    return c


def _chibi_at(c: Canvas, back: Canvas, pose: HeroPose, hip) -> dict:
    lean = math.radians(pose.lean)
    up = (math.sin(lean), -math.cos(lean))                 # along the spine, hip -> neck
    front = (math.cos(lean), math.sin(lean))               # chest side
    length = TORSO + pose.length

    def along(d, f=0.0, base=hip):
        return (base[0] + up[0] * d + front[0] * f, base[1] + up[1] * d + front[1] * f)

    neck = along(length + 0.5)
    shoulder = along(length - 1.5, 0.8)
    head = (neck[0] + 1.5 + pose.head_dx, neck[1] - 5.6 + pose.head_dy)
    fur, fur_d, stripe = P.GINGER, P.GINGER_D, P.GINGER_DD
    white, white_d = P.FUR_WHITE, P.FUR_WHITE_D

    # Cape, behind everything: from the back of the neck, a light edge along its top.
    layer = Canvas(*c.size)
    _ribbon(layer, along(length - 1.5, -2.0), pose.cape - pose.lean * 0.3, pose.cape_len, pose.flap, pose.ripple,
            3, 4.6, P.CAPE, P.CAPE_D, P.CAPE_L)
    back.paste(despeckle(layer).outline())

    # Tail: a thick chain from the back of the rump, curling up at the tip, two dark bands; outlined on its
    # own so it stands clear of the body.
    layer = Canvas(*c.size)
    point = along(1.0, -3.2)
    angle = pose.tail
    for i in range(10):
        rad = math.radians(angle)
        point = (point[0] - math.cos(rad) * 1.25, point[1] - math.sin(rad) * 1.25)
        colour = stripe if i in (4, 7) else (fur_d if i < 2 else fur)
        layer.ellipse(point[0], point[1], 1.2 if i < 8 else 0.9, 1.2 if i < 8 else 0.9, colour)
        angle += pose.curl
    tail_tip = point
    back.paste(despeckle(layer).outline())

    def leg(start, spec, colour, paw, on):
        width = 4 if pose.chunky else 3
        knee = on.limb(start, spec[0], THIGH, colour, width)
        foot = on.limb(knee, spec[1], SHIN, colour, width)
        if pose.chunky:                                     # a flat white paw, toes marked, forward of the leg
            on.rect(foot[0] - 1.5, foot[1] - 1, foot[0] + 2.5, foot[1] + 0.5, paw)
            on.px(foot[0] + 0.5, foot[1], P.FUR_WHITE_D)
            on.px(foot[0] + 1.5, foot[1], P.FUR_WHITE_D)
        else:
            on.rect(foot[0] - 1, foot[1] - 0.5, foot[0] + 1, foot[1] + 0.5, paw)     # white paw tip
        return foot

    def arm(start, spec, colour, paw, on):
        width = 3 if pose.chunky else 2
        elbow = on.limb(start, spec[0], UPPER_ARM + pose.reach, colour, width)
        hand = on.limb(elbow, spec[1], FOREARM + pose.reach, colour, width)
        if pose.chunky:
            on.rect(hand[0] - 1, hand[1] - 1, hand[0] + 1, hand[1] + 0.5, paw)
            on.px(hand[0], hand[1], P.FUR_WHITE_D)
        else:
            on.rect(hand[0] - 0.5, hand[1] - 0.5, hand[0] + 0.5, hand[1] + 0.5, paw)
        return hand

    body = Canvas(*c.size)
    # Far limbs in shadow; each leg outlined on its own so strides read clearly against the body.
    layer = Canvas(*c.size)
    leg(along(0.5, -1.2), pose.far_leg, fur_d, white_d, layer)
    body.paste(despeckle(layer).outline())
    far_hand = arm((shoulder[0] - front[0] * 2, shoulder[1] - front[1] * 2), pose.far_arm, fur_d, white_d, body)

    # Torso: a small round body, shadowed along the back, with a white chest and belly in front.
    steps = 8
    for i in range(steps + 1):
        t = i / steps
        p = along(1.5 + t * (length - 2.5))
        body.ellipse(p[0], p[1], 3.7 - t * 0.7, 3.7 - t * 0.7, fur_d)
    for i in range(steps + 1):
        t = i / steps
        p = along(1.5 + t * (length - 2.5), 0.7)
        body.ellipse(p[0] + up[0] * 0.4, p[1] + up[1] * 0.4, 3.0 - t * 0.7, 3.0 - t * 0.7, fur)
    for i in range(steps + 1):
        t = i / steps
        p = along(1.0 + t * (length - 2.0), 2.1 - t * 0.3)
        body.ellipse(p[0], p[1], 1.9 - t * 0.4, 1.9 - t * 0.4, white)
    for d in (2.0, 4.0):                                    # two tabby bands over the back
        body.line(along(d, -3.0), along(d + 0.5, -1.6), stripe)
    c.paste(despeckle(body))
    layer = Canvas(*c.size)
    leg(along(0.8, 0.6), pose.near_leg, fur, white, layer)
    c.paste(despeckle(layer).outline())

    near_hand = None
    if pose.arm_behind:
        layer = Canvas(*c.size)
        near_hand = arm(shoulder, pose.near_arm, fur, white, layer)
        c.paste(layer.outline())

    # Head: the pixel stamp, on whole pixels so it never shimmers between frames.
    x0, y0 = r(head[0] - HEAD_CENTRE[0]), r(head[1] - HEAD_CENTRE[1])
    _stamp(c, _face(pose), x0, y0)

    # Scarf knotted under the chin (replacing the bottom row of the chin), its end hanging over the chest.
    c.rect(x0 + 3, y0 + 17, x0 + 12, y0 + 17, P.CAPE)
    c.rect(x0 + 5, y0 + 17, x0 + 9, y0 + 17, P.CAPE_L)
    c.rect(x0 + 4, y0 + 18, x0 + 11, y0 + 18, P.CAPE_D)
    c.rect(x0 + 10, y0 + 18, x0 + 11, y0 + 19, P.CAPE)
    c.px(x0 + 11, y0 + 20, P.CAPE_D)

    if not pose.arm_behind:                                 # near arm outlined, so it reads over the head
        layer = Canvas(*c.size)
        near_hand = arm(shoulder, pose.near_arm, fur, white, layer)
        c.paste(layer.outline())
    return {"head": (x0 + HEAD_CENTRE[0], y0 + HEAD_CENTRE[1]), "neck": neck, "hip": hip, "tail_tip": tail_tip,
            "near_hand": near_hand, "far_hand": far_hand}


def hero_frame(pose: HeroPose, extras=(), under=(), dx: float = 0) -> Image.Image:
    """One outlined frame; `under` is drawn before the cat (behind it), `extras` after the outline. `dx` moves
    the hips off `CX`, so a stretched-out body stays centred on the anchor."""
    c = Canvas(*SIZE)
    joints = chibi(c, pose, CX + dx, GROUND)
    c.outline()
    for extra in extras:
        extra(c, joints)
    if under:
        back = Canvas(*SIZE)
        for draw in under:
            draw(back, joints)
        back.paste(c.img)
        return back.img
    return c.img


# One leg through the 8-frame run, as (thigh, shin) angles. The other leg is the same four frames later.
# 0 contact (reaching out front), 1 down (weight on it), 2 passing (under the body), 3 push-off,
# 4 kick (paw flicked up behind), 5 swing (tucked), 6 reach, 7 flight (stretched forward).
RUN_LEG = ((52, 22), (28, 0), (2, -12), (-38, -48), (-58, -110), (-5, -95), (45, -10), (64, 36))
RUN_BOB = (0, 1, 0, 0, 0, 1, 0, 0)        # head drops on the down frames; the body rises in flight
RUN_LIFT = (0, 0, 0, 1, 0, 0, 0, 1)          # 3 and 7 are flight frames: both feet off the ground
RUN_DX = -4                                  # hips back, so the leaning body and head centre on the anchor


def running(frame: int, **overrides) -> HeroPose:
    """A driving run leaning forward: wide strides, a flight frame each step, arms swinging against the legs,
    the cape streaming flat and rippling, the tail trailing."""
    near, far = RUN_LEG[frame % 8], RUN_LEG[(frame + 4) % 8]

    phase = frame / 8 * math.tau

    def arm(p):                                    # front paws reach out under the chin, against the legs
        upper = 62 - 38 * math.cos(p)
        return (upper, upper - 25 + 30 * max(0.0, math.cos(p)))

    pose = HeroPose(near_leg=near, far_leg=far, near_arm=arm(phase + math.pi), far_arm=arm(phase), reach=1.0,
                    arm_behind=False, lean=45, length=3.5, head_dx=0,
                    head_dy=RUN_BOB[frame % 8], lift=RUN_LIFT[frame % 8], cape=118 - 3 * RUN_BOB[frame % 8],
                    cape_len=16, flap=phase * 2, ripple=20, tail=-14 + 8 * math.sin(phase * 2), curl=7)
    return replace(pose, **overrides)


def ghostly(image: Image.Image, alpha: int, cape: bool = True) -> Image.Image:
    """Ghost Dash: the fur recoloured to blue-white by brightness (so the white muzzle still shows), a blue
    outline, the cape left red; all at partial alpha."""
    out = image.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            cr, cg, cb, ca = px[x, y]
            if not ca:
                continue
            if (cr, cg, cb) == P.OUTLINE[:3]:
                colour = P.BLUE_D
            elif cape and (cr, cg, cb, 255) in (P.CAPE_L, P.CAPE, P.CAPE_D):  # cape and scarf
                colour = (cr, cg, cb, 255)
            else:
                lum = 0.3 * cr + 0.59 * cg + 0.11 * cb
                colour = (P.WHITE if lum > 215 else P.CYAN if lum > 125 else P.BLUE if lum > 80 else P.BLUE_D if lum > 35
                          else P.NAVY)
            px[x, y] = (*colour[:3], min(ca, alpha))
    return out


def star(c: Canvas, x: float, y: float, big: bool = True) -> None:
    c.px(x, y, P.WHITE)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        c.px(x + dx, y + dy, P.YELLOW)
    if big:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            c.px(x + dx, y + dy, P.GOLD)


def yarn_ball(c: Canvas, x: float, y: float) -> None:
    c.ellipse(x, y, 2, 2, P.YARN)
    c.px(x - 1, y - 1, P.YARN_L)
    c.line((x - 1, y + 1), (x + 1, y - 1), P.YARN_D)


def speed_lines(i: int, colours=(P.WHITE, P.CREAM), reach: float = 6):
    def draw(c, joints):
        x, y = joints["hip"]
        for k, dy in enumerate((-6, -2, 2)):
            n = 3 + (i + k * 2) % 4
            start = x - 9 - (k % 2) * 2
            c.line((start - n - reach / 2, y + dy), (start, y + dy), colours[k % len(colours)])
    return draw


def build() -> list[Sprite]:
    sprites = [hero_sprite("hero"), yarn()]
    for skin in SKINS:
        with wearing(skin):
            sprites.append(hero_sprite(f"hero_{skin.id}"))
    return sprites


def hero_sprite(name: str) -> Sprite:
    """Every hero animation, drawn in whatever coat is being worn (see `wearing`)."""
    hero = Sprite(name, SIZE, cx=CX, ground=GROUND)

    hero.add("run", [hero_frame(running(i), dx=RUN_DX) for i in range(8)], fps=14)

    def dust(n):
        def draw(c, joints):
            for i in range(n):
                x, y = CX + 7 + i * 3, GROUND - (i % 2)
                c.rect(x, y - 1, x + 1, y, P.GREY_L)
        return draw

    # Skids to a halt: carried forward by the run, then sits back on its heels with a front paw braced, the
    # cape flying on over its back and settling.
    stop = []
    for i, (lean, cape, head) in enumerate(((30, 110, 1), (8, 140, 0), (-10, 125, 0), (-4, 100, 0))):
        stop.append(hero_frame(HeroPose(near_leg=(48, 30), far_leg=(-20, -50), near_arm=(100, 85), far_arm=(88, 75),
                                        reach=1.2, arm_behind=False, lean=lean, length=1.5 if i == 0 else 0,
                                        head_dy=head, cape=cape, cape_len=14, flap=i * 1.3, ripple=20, tail=-15,
                                        curl=10, ears_back=i < 2, eye="squint" if i < 2 else "open"),
                               extras=[dust((1, 2, 2, 1)[i])], dx=-3 if i == 0 else 0))
    hero.add("stop", stop, fps=10, loop=False)

    # Stands at ease: breathing, the cape stirring, the tail swishing; blinks on the last frame.
    hero.add("idle", [
        hero_frame(HeroPose(near_arm=(20, 8), far_arm=(6, -4), chunky=True, cape=88 + k * 3, cape_len=12,
                            flap=k * 1.6, ripple=16, tail=-70 + k * 3, curl=16, head_dy=dy, eye=e))
        for k, (dy, e) in enumerate(((0, "open"), (0, "open"), (0.6, "open"), (0.6, "shut")))
    ], fps=4)

    # Springs up leaning into it: hind legs tucked, front paws reaching ahead, the cape streaming back and down.
    hero.add("jump", [
        hero_frame(HeroPose(near_leg=(70, -20), far_leg=(50, -40), near_arm=(105, 95), far_arm=(92, 85), reach=1.2,
                            arm_behind=False, lean=28, length=1.5, cape=78, cape_len=15, flap=0.0, ripple=18,
                            tail=-45, curl=12), dx=-2),
        hero_frame(HeroPose(near_leg=(80, -10), far_leg=(60, -30), near_arm=(112, 100), far_arm=(100, 90), reach=1.2,
                            arm_behind=False, lean=22, length=1.5, cape=88, cape_len=15, flap=1.5, ripple=18,
                            tail=-35, curl=13), dx=-2),
    ], fps=8)
    # Coming down: arms up, legs reaching for the ground, cape lifting above.
    hero.add("fall", [
        hero_frame(HeroPose(near_leg=(15, 5), far_leg=(-10, -10), near_arm=(115, 150), far_arm=(-115, -150), reach=0.8,
                            lean=-4, cape=135, flap=0.5, ripple=14, tail=15, curl=14, eye="wide", mouth=True)),
        hero_frame(HeroPose(near_leg=(12, 0), far_leg=(-8, -14), near_arm=(125, 160), far_arm=(-125, -160), reach=0.8,
                            lean=-4, cape=145, flap=2.0, ripple=14, tail=20, curl=15, eye="wide", mouth=True)),
    ], fps=8)

    # Double Pounce: tucks into a ball and flips forward once.
    tuck = HeroPose(near_leg=(95, -10), far_leg=(80, -20), near_arm=(110, 170), far_arm=(95, 160), lean=25,
                    cape=70, cape_len=8, ripple=6, tail=-30, curl=22, eye="open", head_dy=1.5)
    ball = Canvas(*SIZE)
    chibi(ball, tuck, CX, GROUND - 6)
    box = ball.img.getbbox()
    centre = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
    spin = []
    for k in range(4):
        c = Canvas(*SIZE)
        c.paste(ball.img.rotate(-90 * k, resample=Image.NEAREST, center=centre))
        c.outline()
        for j in range(5):                                   # a white motion arc trailing the spin
            a = math.radians(-90 * k + 110 + j * 14)
            c.px(centre[0] + math.cos(a) * 13, centre[1] - math.sin(a) * 13, P.WHITE if j > 1 else P.GREY_L)
        spin.append(c.img)
    hero.add("double", spin, fps=16)

    # Yarn Shot: winds up with the yarn behind its head and flings it forward.
    stance = dict(near_leg=(28, 10), far_leg=(-22, -30), cape=80, ripple=16, tail=-55, curl=15)

    def holding(c, joints):
        x, y = joints["near_hand"]
        ball = Canvas(*SIZE)
        yarn_ball(ball, x + 0.5, y - 1.5)
        c.paste(ball.outline())

    throw = [
        hero_frame(HeroPose(**stance, near_arm=(15, 75), far_arm=(40, 120), lean=2, flap=0.0), extras=[holding]),
        hero_frame(HeroPose(**stance, near_arm=(-95, -130), far_arm=(30, 60), lean=-12, flap=1.2, reach=0.8),
                   extras=[holding]),
        hero_frame(HeroPose(**{**stance, "cape": 95}, near_arm=(100, 92), far_arm=(-20, 10), lean=14, flap=2.4,
                            mouth=True, reach=1.4)),
        hero_frame(HeroPose(**{**stance, "cape": 85}, near_arm=(70, 55), far_arm=(-10, 20), lean=10, flap=3.6,
                            reach=0.8)),
    ]
    hero.add("throw", throw, fps=16, loop=False)

    # Ghost Dash: a see-through blue-white copy trailing after-images and speed lines.
    dash = []
    for i in range(4):
        pose = running(i * 2 + 1, lean=20, cape_len=10, lift=0)
        body = hero_frame(pose, dx=4)
        frame = Image.new("RGBA", SIZE, P.CLEAR)
        for offset, alpha in ((-6, 70),):
            ghost = Image.new("RGBA", SIZE, P.CLEAR)
            ghost.alpha_composite(ghostly(body, alpha, cape=False), (offset - (i % 2), 0))
            frame.alpha_composite(ghost)
        lines = Canvas(*SIZE)
        for k, y in enumerate((GROUND - 18, GROUND - 11, GROUND - 5)):
            n = 3 + (i + k * 3) % 4
            lines.line((2 + (k + i) % 3, y), (2 + (k + i) % 3 + n, y), P.WHITE if k % 2 else P.CYAN)
        frame.alpha_composite(see_through(lines.img, 200))
        frame.alpha_composite(ghostly(body, 235))
        dash.append(frame)
    hero.add("dash", dash, fps=16)

    # Super Pounce: stretched flat out, forepaws reaching, legs and cape streaming behind.
    pounce = []
    for i, (lean, stretch) in enumerate(((70, 1.5), (82, 3.0), (86, 3.0), (78, 2.0))):
        pose = HeroPose(near_leg=(-105 + i * 3, -100), far_leg=(-95 + i * 3, -90), near_arm=(58 - i * 2, 72 - i * 2),
                        far_arm=(50 - i * 2, 64 - i * 2), reach=2.2, arm_behind=True, lean=lean, length=stretch, lift=3, head_dx=1.5,
                        head_dy=0.5, cape=140, cape_len=12, flap=i * 1.6, ripple=14, tail=-4, curl=2,
                        ears_back=True, eye="wide", mouth=i in (1, 2))
        pounce.append(hero_frame(pose, under=[speed_lines(i, reach=0)], dx=-4))
    hero.add("pounce", pounce, fps=12)

    # Hurt: flinches back, eyes screwed shut, a star popping off its head.
    hurt_pose = HeroPose(near_leg=(25, 5), far_leg=(-5, -20), near_arm=(120, 160), far_arm=(-110, -150), reach=0.8, lean=-16,
                         lift=1, cape=60, flap=1.0, ripple=20, tail=40, curl=12, eye="squint", mouth=True,
                         ears_back=True)

    def hit_star(k):
        def draw(c, joints):
            x, y = joints["head"]
            star(c, x - 7 + k * 2, y - 9 + k, big=k == 0)
        return draw

    hurt = hero_frame(hurt_pose, extras=[hit_star(0)])
    hero.add("hurt", [tint(hurt, P.WHITE, 0.3), hero_frame(hurt_pose, extras=[hit_star(1)])], fps=10)
    hero.add("death", death_frames(hurt_pose), fps=8, loop=False)
    screen_poses(hero)
    return hero


def draped_cape(angle: float, length: float, flap: float, ripple: float = 8, dx: float = -3, dy: float = 0):
    """An extra that lays the cape over the cat's back (for lying poses, where the cape drawn behind the body
    would be hidden): from the back of the neck, outlined on its own."""
    def draw(c, joints):
        nx, ny = joints["neck"]
        layer = Canvas(*c.size)
        _ribbon(layer, (nx + dx, ny + dy), angle, length, flap, ripple, 3.5, 5.5, P.CAPE, P.CAPE_D, P.CAPE_L)
        c.paste(despeckle(layer).outline())
    return draw


def raised_paw(lift: float):
    """An extra: the near front leg thrust up beside the head (the cat's own arm is too short to clear its big
    head), fur with a light edge and a white paw on top."""
    def draw(c, joints):
        hx, hy = joints["head"]
        layer = Canvas(*c.size)
        base, tip = (hx + 6.5, hy + 6), (hx + 11, hy - 4 - lift)
        layer.line(base, tip, P.GINGER, 3)
        layer.line((base[0] - 1, base[1] - 1), (tip[0] - 1, tip[1]), P.GINGER_L)
        layer.ellipse(tip[0] + 0.5, tip[1] - 0.5, 1.6, 1.6, P.FUR_WHITE)
        layer.px(tip[0] + 1, tip[1] + 1, P.FUR_WHITE_D)
        c.paste(layer.outline())
    return draw


def ledge_paws(c, joints):
    """An extra: both front paws flopped over the ledge either side of the chin, toes on the ground row."""
    hx, _ = joints["head"]
    layer = Canvas(*c.size)
    for x in (hx - 5, hx + 4):
        layer.rect(x - 1, GROUND - 4, x + 1, GROUND - 1, P.GINGER)
        layer.px(x - 1, GROUND - 4, P.GINGER_L)
        layer.rect(x - 1, GROUND, x + 1, GROUND, P.FUR_WHITE)
        layer.px(x, GROUND - 1, P.FUR_WHITE)
        layer.px(x + 1, GROUND, P.FUR_WHITE_D)
    c.paste(layer.outline())


def screen_poses(hero: Sprite) -> None:
    """Poses for the start, level-complete and game-over screens (not used in play)."""
    # Peek: lying on its belly on top of the title, front paws flopped over the edge in front of its chin, the
    # cape draped over its back, the tail tip flicking; blinks on the third frame.
    peek = []
    for k in range(4):
        pose = HeroPose(near_leg=(-90, -95), far_leg=(-82, -88), near_arm=(78, 30), far_arm=(70, 20), reach=0.6,
                        arm_behind=False, lean=90, length=1, head_dx=1, head_dy=1.5, cape=60, cape_len=6, ripple=0,
                        tail=-6 + (0, 10, 18, 6)[k], curl=10, eye="shut" if k == 2 else "open")
        peek.append(hero_frame(pose, extras=[draped_cape(98 + (0, 4, 6, 2)[k], 13, k * 1.5, 10), ledge_paws], dx=-4))
    hero.add("peek", peek, fps=4)

    # Cheer: standing tall, one paw thrust up beside its head, "^ ^" eyes and a wide open smile, cape flapping.
    cheer = []
    for k in range(4):
        up = (0, 1, 0, 1)[k]
        pose = HeroPose(near_leg=(6, 0), far_leg=(-8, -4), near_arm=(20, 40), far_arm=(-25, 20), lean=-4, lift=up,
                        cape=100 + k * 12, cape_len=14, flap=k * 1.6, ripple=22, tail=-20 + up * 25, curl=16,
                        eye="happy", smile=True)
        cheer.append(hero_frame(pose, extras=[raised_paw(up)]))
    hero.add("cheer", cheer, fps=8)

    # Sitting on its haunches, paws together in front, "^ ^" eyes and a smile; the tail swishes along the
    # ground and the cape stirs behind.
    sit = []
    for k in range(4):
        pose = HeroPose(near_leg=(95, 5), far_leg=(85, 0), near_arm=(12, 5), far_arm=(4, 0), lean=-6, length=-0.5,
                        cape=72 + (0, 6, 10, 6)[k], cape_len=12, flap=k * 1.6, ripple=10,
                        tail=(-62, -48, -36, -48)[k], curl=(20, 16, 12, 16)[k], eye="happy", smile=True,
                        head_dy=(0, 0, 0.6, 0.6)[k])
        sit.append(hero_frame(pose))
    hero.add("sit_happy", sit, fps=6)

    # Start screen: crouched low and playful, both front legs planted, cape and scarf flowing back. Only the
    # cape (frame 2), the eyes (frame 3, a blink) and the tail (frame 4) move.
    hero.add("menu", [menu_frame(k) for k in range(4)], fps=4)

    # Knocked out: stretched out on its belly, head resting on the ground at the right with its ears up,
    # "x x" eyes and tongue out; tail lying out to the left, cape draped over its back. Frame 2: a 1 px twitch.
    ko = [ko_frame(k) for k in range(2)]
    hero.add("ko", ko, fps=3)

    hero.add("ghost", [ghost_frame(k) for k in range(4)], fps=5)


# A front-facing head for the ghost: round, two upright ears with pink insides (same shape as HEAD's ears),
# white muzzle; sad eyes and a frown are drawn on it in `ghost_frame`.
FRONT_HEAD = (
    "..F............F..",
    "..FF..........FF..",
    "..FPF........FPF..",
    ".FPPF........FPPF.",
    ".FPPPF......FPPPF.",
    ".FLLLFSFFFFSFFFFF.",
    "FLLLFFSFFFFSFFFFFF",
    "FLLFFFFFFFFFFFFFFF",
    "FFFFFFFFFFFFFFFFFF",
    "FFFFFFFFFFFFFFFFFF",
    "FFFFFFFFWWFFFFFFFF",
    "FFFFFFFWWWWFFFFFFF",
    "DFFFFFWWPPWWFFFFFD",
    "DFFFFWWWWWWWWFFFFD",
    ".DFFFWWWWWWWWFFFD.",
    "..DDDwwWWWWwwDDD..",
    "....DDDDDDDDDD....",
)
assert all(len(row) == 18 for row in FRONT_HEAD)


# A bigger head for the start-screen pose (22x20, same style and ear shape as HEAD): big eyes with shine,
# a pink nose and a tiny pink "w" mouth.
MENU_HEAD = (
    "...D..............F...",
    "...DF............FF...",
    "..DPF...........FPF...",
    "..DPPF.........FPPF...",
    ".DDPPF........FPPPF...",
    ".DPPPFF......FFPPPFF..",
    "..DLLLSLSFFFWWFSFFFF..",
    ".DLLLLSLSFFFWWFSFFFFF.",
    "DFLLLFFFFFFFWWFFFFFFFF",
    "DFLLFFFFFFFFWWFFFFFFFF",
    "DFFFFFFFFFFWWWWFFFFFFF",
    "DFFFFFFHKKFWWWWHKKFFFF",
    "DFFFFFFKKKWWWWWKKKFFFF",
    "DSSFFFFKKKWWPPWKKKWFFF",
    "DFFFFFWWWWpWpWpWWWWWFF",
    ".DFFFWWWWWWpWpWWWWWWF.",
    ".DDFFwWWWWWWWWWWWWWFF.",
    "..DDDwwWWWWWWWWWWWFD..",
    "...DDDwwwWWWWWWWWFD...",
    ".....DDDwwwwwwwDD.....",
)
assert all(len(row) == 22 for row in MENU_HEAD)


def menu_frame(k: int) -> Image.Image:
    """The start-screen pose: a compact cat crouched low, three-quarter view facing right, its big head over a
    short round body; two short white-pawed front legs side by side, the hind foot tucked at the back, the
    tail curling behind the cape, which billows up and back to the left. Built from separately outlined parts;
    only the cape (frame 2), the eyes (frame 3) and the tail (frame 4) move."""
    fur, fur_l, fur_d, stripe = P.GINGER, P.GINGER_L, P.GINGER_D, P.GINGER_DD
    white, white_d = P.FUR_WHITE, P.FUR_WHITE_D
    g = GROUND
    out = Canvas(*SIZE)
    hx, hy = 18, 3                                           # top left of the head grid

    def layer(draw, clean=True):
        part = Canvas(*SIZE)
        draw(part)
        out.paste((despeckle(part) if clean else part).outline())

    def tail(c):                                             # curling up at the back, behind the cape
        flick = 2 if k == 3 else 0
        pts = [(15, g - 3), (10, g - 3), (6, g - 5), (4, g - 9), (5 + flick, g - 13 - flick // 2)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            c.line((x0, y0), (x1, y1), fur, 3)
        c.rect(7, g - 5, 8, g - 3, stripe)
        c.rect(3, g - 8, 5, g - 8, stripe)

    def cape(c):                                             # billowing up and out to the left behind the cat
        lift = (0, 3, 0, 1)[k]
        top = [(23, g - 13), (17, g - 18), (12, g - 21 - lift), (7, g - 20 - lift), (3, g - 22 - lift),
               (1, g - 17 - lift)]
        bottom = [(4, g - 14), (2, g - 10), (8, g - 12), (12, g - 9), (17, g - 11), (23, g - 10)]
        c.poly(top + bottom, P.CAPE)
        c.poly(bottom + [(17, g - 13), (11, g - 13), (5, g - 15)], P.CAPE_D)
        for (x0, y0), (x1, y1) in zip(top, top[1:]):         # light top edge
            c.line((x0, y0 + 1), (x1, y1 + 1), P.CAPE_L)
        for x, y in ((9, g - 18 - lift), (14, g - 17)):        # folds
            c.line((x, y), (x + 1, y + 6), P.CAPE_D)

    def body(c):                                             # short and round, mostly behind the head
        c.ellipse(24, g - 6, 9, 6, fur_d)
        c.ellipse(24, g - 6.6, 8.2, 5.2, fur)
        c.line((19, g - 11), (20, g - 8), stripe)
        c.ellipse(16, g - 4, 4.5, 4, fur)                    # tucked haunch
        c.line((15, g - 7), (16, g - 5), stripe)

    def hind_foot(c):                                        # a white oval at the back
        c.ellipse(13.5, g - 1, 3.5, 1.6, white)
        c.px(12, g, white_d)
        c.px(14, g, white_d)

    def front_legs(c):                                       # two short legs side by side, white paws, toes marked
        for x0, colour in ((26, fur_d), (31, fur)):
            c.rect(x0, g - 9, x0 + 3, g - 3, colour)
            c.rect(x0, g - 6, x0 + 3, g - 6, stripe)
            c.rect(x0 - 1, g - 2, x0 + 4, g, white if colour == fur else white_d)
            for x in (x0, x0 + 2):
                c.px(x, g, white_d if colour == fur else P.GREY_L)

    def chest(c):                                            # white chest under the chin
        c.ellipse(31, g - 10, 4.5, 3, white)

    def head(c):
        rows = [list(row) for row in MENU_HEAD]
        if k == 2:                                           # blink: eyes shut into little curves
            for y in range(11, 14):
                for x in list(range(7, 10)) + list(range(15, 18)):
                    rows[y][x] = "F"
            for x, y in ((7, 12), (8, 13), (9, 12), (15, 12), (16, 13), (17, 12)):
                rows[y][x] = "K"
        _stamp(c, rows, hx, hy)

    def scarf(c):                                            # a short knot under the chin, a round gold bell
        c.rect(22, hy + 18, 33, hy + 19, P.CAPE)
        c.rect(24, hy + 18, 30, hy + 18, P.CAPE_L)
        c.rect(30, hy + 20, 32, hy + 20, P.CAPE)
        c.rect(30, hy + 21, 31, hy + 22, P.GOLD)
        c.px(30, hy + 21, P.YELLOW)
        c.px(31, hy + 22, P.GOLD_D)

    layer(tail)
    layer(cape)
    layer(body)
    layer(hind_foot, clean=False)
    layer(front_legs, clean=False)
    layer(chest)
    layer(head, clean=False)
    layer(scarf, clean=False)
    shifted = Image.new("RGBA", SIZE, P.CLEAR)               # 1 px right, so the cape tip clears the frame edge
    shifted.alpha_composite(out.img, (1, 0))
    return shifted


def ko_frame(k: int) -> Image.Image:
    """The knocked-out cat, about 40 px long, built from separately outlined parts so each one reads: tail,
    hind leg, body, cape, head (the HEAD grid with its ears up)."""
    fur, fur_l, fur_d, stripe = P.GINGER, P.GINGER_L, P.GINGER_D, P.GINGER_DD
    white, white_d = P.FUR_WHITE, P.FUR_WHITE_D
    g = GROUND
    out = Canvas(*SIZE)

    def layer(draw, clean=True):
        part = Canvas(*SIZE)
        draw(part)
        out.paste((despeckle(part) if clean else part).outline())

    def tail(c):                                             # lying out to the left, tip curling up (twitches)
        pts = [(9, g - 6), (6, g - 6), (4, g - 7), (3, g - 9 - k)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            c.line((x0, y0), (x1, y1), fur, 3)
        c.rect(5, g - 8, 5, g - 5, stripe)
        c.rect(3, g - 10 - k, 4, g - 9 - k, fur_d)

    def hind(c):                                             # hind leg stretched back, paw sole showing
        c.line((12, g - 2), (7, g - 1), fur, 3)
        c.rect(4, g - 2 + k, 7, g, white)
        c.px(5, g - 1 + k, P.PINK)

    def body(c):                                             # a long round body flat on the ground
        c.ellipse(17, g - 4.5, 11, 5, fur_d)
        c.ellipse(17, g - 5.2, 10.4, 4.3, fur)
        c.rect(10, g - 9, 24, g - 9, fur_l)                  # light along the top of the back
        for x in (12, 16, 20):                               # tabby bands across the back
            c.rect(x, g - 8, x, g - 5, stripe)
        c.ellipse(23, g - 2, 5, 2.2, white)                  # white chest against the ground
        c.rect(19, g - 1, 26, g, white)
        c.rect(19, g, 26, g, white_d)

    def cape(c):                                             # draped over the shoulders and back, not the belly
        c.poly([(26, g - 11), (19, g - 13), (12, g - 12), (8, g - 9), (10, g - 5), (13, g - 7), (19, g - 8),
                (25, g - 7)], P.CAPE)
        c.poly([(10, g - 5), (13, g - 7), (19, g - 8), (25, g - 7), (25, g - 8), (14, g - 9), (9, g - 8)], P.CAPE_D)
        c.line((13, g - 12), (24, g - 11), P.CAPE_L)
        c.line((16, g - 11), (15, g - 8), P.CAPE_D)          # a fold

    def front_paw(c):                                        # a white forepaw flopped out under the chin
        c.rect(21, g - 1, 25, g, white)
        c.px(22, g, white_d)

    def head(c):
        _stamp(c, _face(HeroPose(eye="x", tongue=True)), 24, g - 17)

    for draw in (tail, hind, body, cape, front_paw):
        layer(draw)
    layer(head, clean=False)                                 # the face is exact pixels: keep the "x" eyes
    return out.img


def ghost_frame(k: int) -> Image.Image:
    """The cat's ghost: the hero's head with a sad face over a small body that trails off into a wisp, all pale
    blue and see-through, a gold halo above and little white wings; bobs by up to 2 px."""
    bob = (0, 1, 2, 1)[k]
    c = Canvas(*SIZE)
    x0, y0 = CX - 9, 5 + bob
    hx, hy = x0 + HEAD_CENTRE[0], y0 + HEAD_CENTRE[1]
    c.ellipse(hx - 1, hy + 8, 5, 4, P.GINGER)                         # body
    c.ellipse(hx - 0.5, hy + 8.5, 2.5, 3, P.FUR_WHITE)                # chest
    point, angle = (hx - 3, hy + 11), 200 + (k % 2) * 10               # wisp curling off to the left
    for i in range(7):
        rad = math.radians(angle)
        point = (point[0] + math.cos(rad) * 1.2, point[1] - math.sin(rad) * 1.2)
        size = 2.2 - i * 0.28
        c.ellipse(point[0], point[1], size, size, P.GINGER)
        angle -= 22
    c.rect(hx + 1, hy + 10, hx + 3, hy + 11, P.FUR_WHITE)            # tiny paws held in front
    rows = [list(row) for row in FRONT_HEAD]
    for x, y in ((5, 9), (6, 9), (4, 10), (5, 10), (6, 10), (4, 11), (5, 11), (6, 11),      # big droopy eyes
                 (11, 9), (12, 9), (11, 10), (12, 10), (13, 10), (11, 11), (12, 11), (13, 11),
                 (8, 14), (9, 14), (7, 15), (10, 15)):                                      # a little frown
        rows[y][x] = "K"
    rows[9][5] = rows[9][12] = "H"
    _stamp(c, rows, x0, y0)
    c.outline()
    out = Canvas(*SIZE)
    wings = Canvas(*SIZE)
    flap = k % 2
    for side in (-1, 1):
        wx, wy = hx - 0.5 + side * 8, hy + 6
        wings.poly([(wx, wy + 1), (wx + side * 4, wy - 5 - flap), (wx + side * 7, wy - 4 - flap),
                    (wx + side * 6, wy), (wx + side * 2, wy + 2)], P.WHITE)
        wings.line((wx + side * 2, wy - 1), (wx + side * 4, wy - 3 - flap), P.BLUE_L)
    out.paste(ghostly(c.img, 215, cape=False))
    out.paste(wings.outline(P.BLUE_D))
    ty = int(y0 - 2)                                                   # a hollow gold ring
    left, right = int(hx - 5), int(hx + 4)
    out.rect(left + 1, ty - 1, right - 1, ty - 1, P.YELLOW)
    out.px(left, ty, P.GOLD)
    out.px(right, ty, P.GOLD)
    out.rect(left + 1, ty + 1, right - 1, ty + 1, P.GOLD_D)
    return out.img


def death_frames(hurt_pose: HeroPose) -> list[Image.Image]:
    """Knocked back, knees buckle, flops flat on its belly seeing stars, then fades away."""
    slump = HeroPose(near_leg=(80, -60), far_leg=(70, -70), near_arm=(20, 40), far_arm=(10, 30), lean=30,
                     cape=30, flap=0.5, ripple=10, tail=-50, curl=10, eye="x", ears_back=True, head_dy=1.5)
    flat = HeroPose(near_leg=(-90, -90), far_leg=(-80, -85), near_arm=(85, 90), far_arm=(80, 85), arm_behind=True, lean=90,
                    length=1, head_dx=1, head_dy=4, cape=95, cape_len=9, flap=0.0, ripple=4, tail=-5, curl=6,
                    eye="x", mouth=True, ears_back=True)

    def dizzy(t):
        def draw(c, joints):
            x, y = joints["head"]
            for k in range(3):
                a = t + k * math.tau / 3
                star(c, x + math.cos(a) * 5, y - 9 + math.sin(a) * 1.5, big=False)
        return draw

    lying = hero_frame(flat, dx=-4)
    return [hero_frame(hurt_pose), hero_frame(slump, dx=-1), lying, hero_frame(flat, extras=[dizzy(0.0)], dx=-4),
            see_through(hero_frame(flat, extras=[dizzy(1.4)], dx=-4), 140), see_through(lying, 55)]

def yarn() -> Sprite:
    """The thrown ball of yarn (12x12): rolls with a loose end trailing; bursts into loops on impact."""
    sprite = Sprite("yarn", (12, 12))
    mid = 5.5
    fly = []
    for i in range(4):
        c = Canvas(12, 12)
        for k in range(5):                               # trailing strand behind the ball
            c.px(mid - 4 - k * 0.9, mid + 2 + math.sin(k * 1.4 + i * 1.6) * 1.2, P.YARN_D if k < 3 else P.YARN)
        c.ellipse(mid, mid, 4, 4, P.YARN)
        a = -i * math.pi / 4
        for k in range(3):                               # wound strands, turning as it rolls
            ang = a + k * math.pi / 3
            dx, dy = math.cos(ang), math.sin(ang)
            nx, ny = -dy, dx
            off = (k - 1) * 1.6
            c.line((mid + nx * off - dx * 3.2, mid + ny * off - dy * 3.2),
                   (mid + nx * off + dx * 3.2, mid + ny * off + dy * 3.2), P.YARN_D)
        c.px(mid - 1.5, mid - 2, P.YARN_L)
        c.px(mid - 2, mid - 1, P.YARN_L)
        fly.append(c.outline(P.OUTLINE))
    sprite.add("fly", fly, fps=14)

    impact = []
    for i in range(5):
        c = Canvas(12, 12)
        reach = 1.5 + i * 1.1
        for k in range(6):
            ang = k / 6 * math.tau + i * 0.4
            x, y = mid + math.cos(ang) * reach, mid + math.sin(ang) * reach
            if i < 3:
                c.ellipse(x, y, 1, 1, P.YARN if (k + i) % 2 else P.YARN_L)
            else:
                c.px(x, y, P.YARN_L if k % 2 else P.YARN)
        if i < 2:
            c.ellipse(mid, mid, 3 - i * 1.2, 3 - i * 1.2, P.YARN)
            c.px(mid - 1, mid - 1, P.YARN_L)
        impact.append(c)
    sprite.add("impact", impact, fps=18, loop=False)
    return sprite
