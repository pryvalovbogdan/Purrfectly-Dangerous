"""The kitten hero and its ball of yarn.

The hero is a chibi orange cat standing up on its hind legs (44x36 frame, feet on row 34, body centred
on x 22): a big round head with tall ears, white muzzle, chest and paw tips, and a red cape. `chibi()`
draws it from a `HeroPose`.

`cat()` draws a side-on cat on all fours from a `CatPose`; the ghost cats reuse it.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

from PIL import Image

import palette as P
from draw import Canvas, end_of, r, see_through, tint
from sprite import Sprite

SIZE = (44, 36)
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
    lift: float = 0          # pixels above the ground
    head_dx: float = 0
    head_dy: float = 0
    cape: float = 35         # 0 = hangs straight down, 90 = streams straight back, more = lifts
    cape_len: float = 15
    flap: float = 0          # phase of the ripple running down the cape
    ripple: float = 14       # how much the cape ripples
    tail: float = -35        # tail root angle above straight back (90 = up, negative = drooping)
    curl: float = 18         # how much the tail bends forward per segment
    eye: str = "open"        # open | shut | wide | x | squint
    mouth: bool = False
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
STAMP_COLOURS = {"F": P.GINGER, "L": P.GINGER_L, "D": P.GINGER_D, "S": P.GINGER_DD, "W": P.FUR_WHITE,
                 "w": P.FUR_WHITE_D, "P": P.PINK, "p": P.PINK_D, "K": P.BLACK, "H": P.WHITE}
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
        }[pose.eye]
        for x, y in marks:
            rows[y][x] = "K"
        if pose.eye == "wide":
            rows[8][7] = rows[8][13] = rows[11][15] = "H"
    if pose.mouth:                                           # a small open "o" under the nose
        for x, y in ((10, 12), (11, 12), (10, 13), (11, 13)):
            rows[y][x] = "p"
        rows[12][9] = rows[12][12] = "W"
        rows[13][10] = "K"
    return rows


def _stamp(c: Canvas, rows, x0: int, y0: int) -> None:
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                c.px(x0 + x, y0 + y, STAMP_COLOURS[ch])


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
        knee = on.limb(start, spec[0], THIGH, colour, 3)
        foot = on.limb(knee, spec[1], SHIN, colour, 3)
        on.rect(foot[0] - 1, foot[1] - 0.5, foot[0] + 1, foot[1] + 0.5, paw)     # white paw tip
        return foot

    def arm(start, spec, colour, paw, on):
        elbow = on.limb(start, spec[0], UPPER_ARM + pose.reach, colour, 2)
        hand = on.limb(elbow, spec[1], FOREARM + pose.reach, colour, 2)
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
    hero = Sprite("hero", SIZE, cx=CX, ground=GROUND)

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
        hero_frame(HeroPose(cape=88 + k * 3, cape_len=12, flap=k * 1.6, ripple=16, tail=-70 + k * 3, curl=16, head_dy=dy, eye=e))
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

    return [hero, yarn()]


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
