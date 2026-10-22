"""Sakura's world, the Blossom Path, after docs/concept/Sakura Pixel Art Game Tileset.png (reference only): a bright
blue-violet sky with pink-tinged clouds and a snow-capped pink-violet mountain, pagodas on misty cliffs with
waterfalls, cherry trees in full bloom, a red torii gate and stone lanterns, mossy grass and pink petals over
grey-purple cobbles, a blue waterfall pit, a red arched bridge, a moving wooden platform and bamboo spikes.

Theme id `sakura`; same names, sizes and contracts as the forest (docs/sprite-spec.md). The ground, terrain, island
and pit stonework are the forest's own generated tiles recoloured by a fixed palette map (so every tiling and seam
contract carries over exactly), with blossoms and petals added at wrapped positions; the pit's water is the forest's."""
from __future__ import annotations

import math

from PIL import Image

import palette as P
from characters import scenery as S
from characters import waterfall as WF
from characters.forest import platform
from characters.islands import finish, slab_top, wedge
from draw import Canvas, noise, see_through
from sprite import Sprite, single
import woodland as W

LAYER_W = S.LAYER_W
BRIDGE_SEED = 967
BLOSSOMS = (P.SK_BLOSSOM_DD, P.SK_BLOSSOM_D, P.SK_BLOSSOM, P.SK_BLOSSOM_L, P.SK_BLOSSOM_W)

# Forest colour -> sakura colour: brown and grey cobbles become grey-purple stone, flowers turn to blossom.
STONE_MAP = {
    P.EARTH_L: P.SK_ROCK_L, P.EARTH: P.SK_ROCK, P.EARTH_D: P.SK_ROCK_D, P.EARTH_DD: P.SK_ROCK_DD,
    P.STONE_L: P.SK_ROCK_L, P.STONE: P.SK_ROCK, P.STONE_D: P.SK_ROCK_D, P.STONE_DD: P.SK_ROCK_DD,
    P.ROCK: P.SK_ROCK, P.ROCK_D: P.SK_ROCK_D, P.ROCK_DD: P.SK_ROCK_DD, P.ROCK_L: P.SK_ROCK_L,
    P.KIT_GREEN_L: P.SK_MOSS_L, P.KIT_GREEN: P.SK_MOSS, P.KIT_GREEN_D: P.SK_MOSS_D, P.KIT_GREEN_DD: P.SK_MOSS_DD,
    P.LEAF_Y: P.SK_MOSS_L,
    P.PINK: P.SK_BLOSSOM, P.GOLD_D: P.SK_BLOSSOM_D, P.GOLD: P.SK_BLOSSOM_L,
    P.CLIFF_BACK_L: P.SK_ROCK_D, P.CLIFF_BACK: P.SK_ROCK_D, P.CLIFF_BACK_D: P.SK_ROCK_DD,
    P.CLIFF_BACK_DD: P.SK_ROCK_DD, P.WOOD_OUT: P.SK_ROCK_DD, P.OUTLINE: P.SK_ROCK_DD,
}
CLOUD_MAP = {P.WHITE: P.SK_CLOUD_W, P.CLOUD_S: P.SK_CLOUD_S, P.CLOUD_D: P.SK_CLOUD_D}


def recolour(image: Image.Image, mapping: dict) -> Image.Image:
    """Swaps exact palette colours, keeping each pixel's alpha."""
    table = {k[:3]: v[:3] for k, v in mapping.items()}
    out = image.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a and (r, g, b) in table:
                px[x, y] = (*table[(r, g, b)], a)
    return out


def is_green(pixel) -> bool:
    return pixel[3] and pixel[:3] in {c[:3] for c in (P.KIT_GREEN_L, P.KIT_GREEN, P.KIT_GREEN_D, P.LEAF_Y,
                                                     P.SK_MOSS_L, P.SK_MOSS, P.SK_MOSS_D)}


def petals(image: Image.Image, seed: int, count: int, rows: tuple, wrap: bool = True) -> Image.Image:
    """Scatters little five-dot blossoms and loose petals over the grass (only on green pixels), wrapping at the
    tile's width so a tiled strip stays seamless."""
    out = image.copy()
    px = out.load()
    w, h = out.size
    rnd = noise(seed)
    for k in range(count):
        x, y = int(rnd() * w), rows[0] + int(rnd() * (rows[1] - rows[0] + 1))
        if not (0 <= y < h) or not is_green(px[x % w, y]):
            continue
        if k % 3 == 0:                                             # a loose petal
            px[x % w, y] = P.SK_BLOSSOM_L
            continue
        for dx, dy, col in ((0, 0, P.SK_BLOSSOM_W), (-1, 0, P.SK_BLOSSOM), (1, 0, P.SK_BLOSSOM), (0, -1, P.SK_BLOSSOM_L),
                            (0, 1, P.SK_BLOSSOM_D)):
            xx, yy = (x + dx) % w if wrap else x + dx, y + dy
            if 0 <= xx < w and 0 <= yy < h and px[xx, yy][3]:
                px[xx, yy] = col
    return out


def sakura_single(name: str, sprite: Sprite, mapping: dict = STONE_MAP, petal=None) -> Sprite:
    """A copy of a forest sprite under a sakura name: every frame recoloured, petals added if asked."""
    out = Sprite(name, sprite.size, faces_left=sprite.faces_left, cx=sprite.cx, ground=sprite.ground)
    for anim, data in sprite.anims.items():
        frames = [recolour(f, mapping) for f in data.frames]
        if petal:
            frames = [petals(f, *petal) for f in frames]
        out.add(anim, frames, fps=data.fps, loop=data.loop)
    return out


# --- parallax ------------------------------------------------------------------------------------------

def falling_petals(c: Canvas, seed: int, count: int, y0: float, y1: float) -> None:
    rnd = noise(seed)
    for _ in range(count):
        x, y = rnd() * c.size[0], y0 + rnd() * (y1 - y0)
        c.px(x, y, P.SK_BLOSSOM)
        c.px(x + 1, y + (1 if rnd() > 0.5 else 0), P.SK_BLOSSOM_L)


def sakura_clouds(name: str, height: int, clouds: list, seed: int) -> Sprite:
    """The forest's puffy cumulus in pink-tinged whites, with petals drifting through the sky."""
    base = S.forest_clouds(name, height, clouds)
    c = Canvas(LAYER_W, height)
    c.paste(recolour(base.anims["still"].frames[0], CLOUD_MAP))
    falling_petals(c, seed, 26, 0, height - 10)
    return single(name, c)


def misty_cliff(c: Canvas, x0: float, x1: float, top: float, base: float) -> None:
    c.rect(x0, top + 2, x1, base, P.SK_STONE_D)
    for x in range(int(x0) + 3, int(x1), 6):                       # rock striations
        c.line((x, top + 4), (x - 1, base), P.SK_STONE_DM)
        c.line((x + 2, top + 5), (x + 2, top + 16), P.SK_STONE)
    c.rect(x0 - 1, top, x1 + 1, top + 2, P.KIT_GREEN_D)
    c.rect(x0, top, x1, top, P.KIT_GREEN)
    for x in range(int(x0), int(x1), 7):                           # blossoming shrubs on the rim
        W.clump(c, x + 3, top - 1, 3, BLOSSOMS)


def snow_mountain(c: Canvas, x: float, base: float, w: float, h: float) -> None:
    """The big snow-capped mountain, pink-violet with a lit left face."""
    c.poly([(x - w, base), (x - 8, base - h), (x + 8, base - h), (x + w, base)], P.SK_MTN)
    c.poly([(x - w, base), (x - 8, base - h), (x - 2, base - h), (x - w * 0.35, base)], P.SK_MTN_L)
    c.poly([(x + 8, base - h), (x + w, base), (x + w * 0.4, base)], P.SK_MTN_D)
    cap = [(x - 8, base - h), (x + 8, base - h), (x + 20, base - h + 16), (x + 12, base - h + 13), (x + 6, base - h + 19),
           (x - 2, base - h + 12), (x - 9, base - h + 20), (x - 16, base - h + 14), (x - 22, base - h + 17)]
    c.poly(cap, P.SK_SNOW)
    c.poly([(x + 2, base - h), (x + 8, base - h), (x + 20, base - h + 16), (x + 12, base - h + 13)], P.SK_SNOW_S)


# --- temple architecture (pass 2, after docs/concept/Sakura Pagoda Pixel Art Atlas.png) ------------------

def crest(c: Canvas, x: float, y: float, big: bool = True) -> None:
    """The pink sakura crest: five petals round a pale centre."""
    if big:
        for dx, dy in ((0, -2), (-2, -1), (2, -1), (-1, 1), (1, 1)):
            c.rect(x + dx - 0.5, y + dy - 0.5, x + dx + 0.5, y + dy + 0.5, P.SK_BLOSSOM_D)
        c.px(x, y, P.SK_BLOSSOM_L)
    else:
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
            c.px(x + dx, y + dy, P.SK_BLOSSOM_D)


def hanging_lantern(c: Canvas, x: float, top: float, s: float) -> None:
    """A red paper lantern on a short cord, glowing."""
    h = max(3, round(4 * s))
    c.px(x, top, P.SK_ROOF_D)
    c.px(x, top + 1, P.SK_ROOF_D)
    c.rect(x - 1, top + 2, x + 1, top + 1 + h, P.SK_RED)
    c.rect(x, top + 2, x, top + 1 + h, P.LANTERN)
    c.rect(x - 1, top + 2, x + 1, top + 2, P.GOLD_D)
    c.rect(x - 1, top + 1 + h, x + 1, top + 1 + h, P.GOLD_D)


def roof(c: Canvas, x: float, yb: float, span: float, rh: float, s: float, ridge: float = 0.2,
         lanterns: bool = False) -> None:
    """A dark tiled roof with upturned eaves and gold knobs on the tips; its eave line is row `yb`."""
    half = span / 2
    layer = Canvas(*c.size)
    lift = max(2, round(5 * s))
    top = [(x - half, yb - lift), (x - half * 0.78, yb - rh * 0.3), (x - half * 0.5, yb - rh * 0.68),
           (x - half * ridge, yb - rh)]
    pts = top + [(2 * x - px, py) for px, py in reversed(top)] + [(x + half - 3 * s, yb), (x - half + 3 * s, yb)]
    layer.poly(pts, P.SK_ROOF)
    px = layer.img.load()
    w, h = layer.size
    step = max(2, round(3 * s))
    for xx in range(max(0, int(x - half)), min(w, int(x + half) + 1)):
        col = [y for y in range(max(0, int(yb - rh - 2)), min(h, int(yb) + 1)) if px[xx, y][3]]
        if not col:
            continue
        px[xx, col[0]] = P.SK_ROOF_L                          # lit ridge of each tile row
        if (xx - int(x)) % step == 0:
            for y in col[1:]:
                px[xx, y] = P.SK_ROOF_D                       # tile seams running down the roof
        if col[-1] >= yb - 1:
            px[xx, col[-1]] = P.SK_ROOF_D
    c.paste(layer)
    c.rect(x - half + 3 * s, yb + 1, x + half - 3 * s, yb + max(1, round(1.5 * s)), P.SK_RED_D)   # rafters
    for side in (-1, 1):                                      # gold knobs on the upturned tips
        tx = x + side * half
        c.px(tx, yb - lift - 1, P.GOLD)
        c.px(tx, yb - lift, P.GOLD_D)
        if s >= 0.6:
            c.px(tx - side, yb - lift - 1, P.GOLD_D)
        if lanterns:
            hanging_lantern(c, x + side * (half - 6 * s), yb + 2, s)


def storey(c: Canvas, x: float, yb: float, w: float, h: float, s: float, door: bool) -> None:
    """Red lacquered walls between pillars, white panels with the crest, a gold beam on top."""
    c.rect(x - w / 2, yb - h, x + w / 2, yb, P.SK_RED)
    n = max(2, round(w / (12 * s)))
    bay = w / n
    for k in range(n + 1):                                    # pillars
        px = x - w / 2 + k * bay
        c.rect(px - 0.5 * s, yb - h, px + 0.5 * s, yb, P.SK_RED_D)
    if s >= 0.5:
        for k in range(n):
            bx0, bx1 = x - w / 2 + k * bay + 1.5 * s, x - w / 2 + (k + 1) * bay - 1.5 * s
            mid = (bx0 + bx1) / 2
            if door and abs(mid - x) < bay / 2:
                c.rect(bx0, yb - h * 0.62, bx1, yb, P.SK_ROOF_D)          # the doorway, gold-framed
                c.rect(bx0, yb - h * 0.62, bx1, yb - h * 0.62, P.GOLD_D)
                c.line((mid, yb - h * 0.58), (mid, yb), P.SK_RED_D)
                continue
            if bx1 - bx0 >= 3:
                c.rect(bx0, yb - h * 0.78, bx1, yb - h * 0.15, P.SK_PANEL)
                c.rect(bx0, yb - h * 0.15, bx1, yb - h * 0.15, P.SK_PANEL_D)
                crest(c, mid, yb - h * 0.47, big=bx1 - bx0 >= 6)
    else:
        for k in range(n):
            c.px(x - w / 2 + (k + 0.5) * bay, yb - h / 2, P.SK_PANEL)
    c.rect(x - w / 2, yb - h, x + w / 2, yb - h, P.GOLD_D)
    c.rect(x - w / 2, yb, x + w / 2, yb, P.SK_RED_D)


def temple(c: Canvas, x: float, base: float, s: float) -> None:
    """A three-tier temple: a stone platform with steps, red storeys with crest panels, dark roofs with upturned
    eaves and gold knobs, hanging lanterns, and a gold finial. About 112s wide and 114s tall."""
    pw, ph = 100 * s, max(3, round(6 * s))
    c.rect(x - pw / 2, base - ph, x + pw / 2, base, P.SK_ROCK)                       # stone platform
    c.rect(x - pw / 2, base - ph, x + pw / 2, base - ph, P.SK_ROCK_L)
    for jx in range(int(x - pw / 2) + 3, int(x + pw / 2), max(3, round(8 * s))):
        c.line((jx, base - ph + 1), (jx, base), P.SK_ROCK_D)
    sw = 24 * s                                                                      # steps
    for k in range(ph):
        y = base - k
        c.rect(x - sw / 2 - (ph - k) * 0.5, y, x + sw / 2 + (ph - k) * 0.5, y, P.SK_ROCK_L if k % 2 else P.SK_ROCK)
    c.rect(x - pw / 2 + 2 * s, base - ph - 2 * s, x + pw / 2 - 2 * s, base - ph - 1, P.SK_RED_D)   # red railing
    for jx in range(int(x - pw / 2 + 2 * s), int(x + pw / 2 - 2 * s) + 1, max(3, round(6 * s))):
        if abs(jx - x) > sw / 2:
            c.px(jx, base - ph - 3 * s, P.GOLD)
    y = base - ph
    tiers = [((84, 30), (118, 17)), ((60, 20), (88, 15)), ((40, 16), (66, 21))]
    for i, ((w, h), (span, rh)) in enumerate(tiers):
        storey(c, x, y, w * s, h * s, s, door=i == 0)
        yb = y - h * s + 2 * s
        roof(c, x, yb, span * s, rh * s, s, ridge=0.04 if i == 2 else 0.22, lanterns=s >= 0.6 and i < 2)
        y = yb - rh * s * 0.5
    rt = yb - 21 * s                                                                 # finial on the top ridge
    c.rect(x - 2 * s, rt - 3 * s, x + 2 * s, rt, P.GOLD_D)
    c.rect(x - 2 * s, rt - 3 * s, x - 1 * s, rt, P.GOLD)
    c.ellipse(x, rt - 6 * s, max(1, 2.5 * s), max(1, 2.5 * s), P.GOLD)
    c.px(x - s, rt - 7 * s, P.YELLOW)
    c.line((x, rt - 13 * s), (x, rt - 8 * s), P.GOLD_D)


def gnarled_cherry(c: Canvas, x: float, base: float, h: float, w: float, seed: int) -> None:
    """A big cherry tree like the atlas's: a thick twisting trunk with a root flare and branches, and a full,
    layered pink crown with white highlights."""
    rnd = noise(seed)
    tw = max(5, w * 0.17)
    fork = base - h * 0.46
    lean = (rnd() - 0.5) * w * 0.16
    bend = (rnd() - 0.5) * tw
    trunk = [(x - tw * 1.6, base), (x - tw * 0.7, base - 3), (x - tw * 0.55 + bend, base - h * 0.22),
             (x - tw * 0.5 + lean, fork), (x + tw * 0.5 + lean, fork), (x + tw * 0.55 + bend, base - h * 0.24),
             (x + tw * 0.75, base - 3), (x + tw * 1.7, base)]
    c.poly(trunk, P.BARK_D)
    c.poly([(x - tw * 1.3, base), (x - tw * 0.6, base - 3), (x - tw * 0.45 + bend, base - h * 0.22),
            (x - tw * 0.4 + lean, fork), (x + lean, fork), (x + bend * 0.5, base - h * 0.22), (x + tw * 0.1, base)],
           P.BARK)
    for k in range(4):                                         # bark twists and knots
        c.line((x - tw * 0.4 + k * tw * 0.3, base - 2), (x - tw * 0.3 + lean + k * tw * 0.25 + bend * 0.5, fork + 2),
               P.BARK_DD)
    c.ellipse(x + bend * 0.6, base - h * 0.3, 1.2, 1.6, P.BARK_DD)
    branches = [(-0.36, 0.62), (0.34, 0.66), (-0.12, 0.8), (0.16, 0.84)]
    for bx, by in branches:
        c.line((x + lean, fork), (x + bx * w, base - h * by), P.BARK_D, max(2, round(tw * 0.4)))
    crowns = [(0.0, 0.78, 0.66, 0.4), (-0.3, 0.64, 0.5, 0.34), (0.3, 0.66, 0.5, 0.34), (-0.1, 0.6, 0.42, 0.26),
              (0.14, 0.58, 0.42, 0.26)]
    for k, (cx, cy, cw, ch) in enumerate(crowns):
        W.canopy(c, x + cx * w, base - h * cy, w * cw, h * ch, seed + k, BLOSSOMS, (3, 6))
    for bx, by in branches[:2]:                                # branch tips showing through the lower crown
        c.line((x + bx * w * 0.6, base - h * by * 0.95), (x + bx * w * 0.85, base - h * by * 0.98), P.BARK_DD)
    for _ in range(int(w * 0.9)):                              # bright flower specks
        c.px(x + (rnd() - 0.5) * w * 0.85, base - h * (0.5 + rnd() * 0.45), P.SK_BLOSSOM_W)
    for _ in range(int(w * 0.4)):                              # fallen petals round the roots
        c.px(x + (rnd() - 0.5) * w * 0.9, base - rnd() * 2, P.SK_BLOSSOM_L)


def torii(c: Canvas, x: float, base: float, s: float = 1.0) -> None:
    """A red torii: two pillars on stone feet, the black curved top beam (kasagi) over a red one, the tie beam,
    and a white banner with the crest hanging in the middle."""
    half, hgt = 15 * s, 44 * s
    for side in (-1, 1):
        px = x + side * half
        c.rect(px - 1.5 * s, base - hgt, px + 1.5 * s, base, P.SK_RED)
        c.rect(px + 0.5 * s, base - hgt, px + 1.5 * s, base, P.SK_RED_D)
        c.rect(px - 2.5 * s, base - 4 * s, px + 2.5 * s, base, P.SK_ROCK)
        c.rect(px - 2.5 * s, base - 4 * s, px + 2.5 * s, base - 4 * s, P.SK_ROCK_L)
    c.rect(x - half - 3 * s, base - hgt + 8 * s, x + half + 3 * s, base - hgt + 10 * s, P.SK_RED)   # nuki
    c.rect(x - half - 3 * s, base - hgt + 10 * s, x + half + 3 * s, base - hgt + 10 * s, P.SK_RED_D)
    c.rect(x - half - 4 * s, base - hgt - 1 * s, x + half + 4 * s, base - hgt + 1 * s, P.SK_RED)     # shimaki
    c.poly([(x - half - 8 * s, base - hgt - 5 * s), (x - half - 5 * s, base - hgt - 3 * s),
            (x + half + 5 * s, base - hgt - 3 * s), (x + half + 8 * s, base - hgt - 5 * s),
            (x + half + 6 * s, base - hgt - 1 * s), (x - half - 6 * s, base - hgt - 1 * s)], P.SK_ROOF_D)  # kasagi
    c.line((x - half - 5 * s, base - hgt - 3 * s), (x + half + 5 * s, base - hgt - 3 * s), P.SK_ROOF_L)
    c.rect(x - 1.5 * s, base - hgt + 1 * s, x + 1.5 * s, base - hgt + 8 * s, P.SK_ROOF_D)   # gakuzuka plaque
    by0, by1 = base - hgt + 11 * s, base - hgt + 26 * s                                    # hanging banner
    c.rect(x - 5 * s, by0, x + 5 * s, by1, P.SK_PANEL)
    c.poly([(x - 5 * s, by1), (x, by1 - 3 * s), (x + 5 * s, by1), (x + 5 * s, by1 + 3 * s), (x, by1),
            (x - 5 * s, by1 + 3 * s)], P.SK_PANEL)
    c.rect(x - 5 * s, by0, x - 5 * s, by1, P.SK_PANEL_D)
    crest(c, x, (by0 + by1) / 2, big=s >= 0.8)


def stone_lantern(c: Canvas, x: float, base: float) -> None:
    """A tōrō: a stepped stone base, a post, a lit firebox under a curved cap with a knob."""
    c.rect(x - 4, base - 2, x + 4, base, P.SK_ROCK)
    c.rect(x - 4, base - 2, x + 4, base - 2, P.SK_ROCK_L)
    c.rect(x - 1.5, base - 9, x + 1.5, base - 3, P.SK_ROCK_D)
    c.rect(x - 3, base - 10, x + 3, base - 9, P.SK_ROCK)
    c.rect(x - 3, base - 15, x + 3, base - 11, P.SK_ROCK)
    c.rect(x - 1.5, base - 14, x + 1.5, base - 12, P.LANTERN)
    c.poly([(x - 6, base - 15), (x - 3, base - 18), (x + 3, base - 18), (x + 6, base - 15)], P.SK_ROCK_L)
    c.px(x - 6, base - 16, P.SK_ROCK_L)
    c.px(x + 6, base - 16, P.SK_ROCK_L)
    c.rect(x - 1, base - 20, x + 1, base - 19, P.SK_ROCK_L)


def komainu(c: Canvas, x: float, base: float, side: int) -> None:
    """A stone guardian lion-dog sitting on a pedestal, facing `side` (1 = right)."""
    c.rect(x - 5, base - 6, x + 5, base, P.SK_ROCK)                  # pedestal
    c.rect(x - 5, base - 6, x + 5, base - 6, P.SK_ROCK_L)
    c.rect(x - 4, base - 3, x + 4, base - 3, P.SK_ROCK_D)
    b = base - 7
    c.ellipse(x - side, b - 4, 4, 4, P.SK_STONE)                     # haunch
    c.rect(x + side * 2 - 1, b - 6, x + side * 2 + 1, b, P.SK_STONE)  # front legs
    c.ellipse(x + side * 1.5, b - 9, 3.5, 3.2, P.SK_STONE_L)          # head and mane
    for dx, dy in ((-3, -1), (-2, -3), (0, -4), (2, -3)):
        c.px(x + side * (1.5 + dx * 0.6) + dx * 0.2, b - 9 + dy, P.SK_STONE)
    c.px(x + side * 3.5, b - 9, P.SK_STONE_DD)                       # eye
    c.px(x + side * 4.5, b - 8, P.SK_STONE)                          # snout
    c.line((x - side * 4, b - 5), (x - side * 6, b - 9), P.SK_STONE)  # curled tail
    c.px(x - side * 6, b - 10, P.SK_STONE_L)


def railing(c: Canvas, x0: float, x1: float, base: float) -> None:
    """A red fence: posts with gold caps every 6 px and two rails."""
    c.rect(x0, base - 7, x1, base - 6, P.SK_RED)
    c.rect(x0, base - 3, x1, base - 3, P.SK_RED_D)
    for px in range(int(x0), int(x1) + 1, 6):
        c.rect(px, base - 9, px + 1, base, P.SK_RED)
        c.px(px + 1, base - 8, P.SK_RED_D)
        c.rect(px, base - 10, px + 1, base - 10, P.GOLD)


def banner(c: Canvas, x: float, base: float, white: bool) -> None:
    """A tall banner on a pole: red with a white crest, or white with a red border and the crest."""
    c.line((x, base), (x, base - 30), P.BARK_D)
    c.rect(x - 1, base - 31, x + 7, base - 30, P.BARK_D)
    c.px(x - 1, base - 32, P.GOLD)
    body, trim = (P.SK_PANEL, P.SK_RED) if white else (P.SK_RED, P.SK_RED_D)
    c.rect(x + 1, base - 29, x + 7, base - 12, body)
    c.poly([(x + 1, base - 12), (x + 4, base - 15), (x + 7, base - 12), (x + 7, base - 9), (x + 4, base - 12),
            (x + 1, base - 9)], body)
    c.rect(x + 1, base - 29, x + 1, base - 10, trim)
    c.rect(x + 7, base - 29, x + 7, base - 10, trim)
    c.ellipse(x + 4, base - 22, 2.5, 2.5, P.SK_PANEL if not white else P.SK_PANEL)
    crest(c, x + 4, base - 22)


def sakura_far() -> Canvas:
    """The snow-capped mountain and lower ranges, misty hills with small pagodas, a cliff with a pagoda on top and
    a waterfall down its face, mist at the foot."""
    h = 110
    c = Canvas(LAYER_W, h)
    W.mountains(c, h, 905, 6, (40, 64), (P.SK_MTN_L, P.SK_MTN, P.SK_MTN_D), tips=P.SK_SNOW_S)
    W.wrapped(lambda px: snow_mountain(c, px, h, 92, 96), 96)
    hills = Canvas(LAYER_W, h)                                       # misty hills with blossom
    for x, top, w in ((30, 74, 70), (150, 70, 80), (210, 80, 60)):
        def hill(px, top=top, w=w):
            hills.ellipse(px, h + 6, w / 2, h - top + 6, P.SK_MTN_D)
            W.canopy(hills, px, top + 10, w * 0.8, 16, int(px) % 97 + 990, BLOSSOMS, (3, 5))
        W.wrapped(hill, x)
    c.paste(W.haze(hills, P.SK_SKY_HAZE, 0.18))
    W.piece(c, lambda layer, px: temple(layer, px, 72, 0.3), 150, P.SK_ROOF_D)
    W.piece(c, lambda layer, px: temple(layer, px, 78, 0.24), 34, P.SK_ROOF_D)
    W.wrapped(lambda px: misty_cliff(c, px, px + 58, 50, h), 252)    # the cliff with its pagoda
    W.piece(c, lambda layer, px: temple(layer, px, 50, 0.36), 281, P.SK_ROOF_D)
    W.cascade(c, 262, 52, h - 3, 6, 3)
    mist = Canvas(LAYER_W, h)
    for x in range(0, LAYER_W, 18):
        mist.ellipse(x + 9, h - 8, 16, 6, P.SK_MIST)
    c.paste(see_through(mist.img, 140))
    return W.haze(c, P.SK_SKY_HAZE, 0.14)


def sakura_near() -> Canvas:
    """A distant blossom band; big gnarled cherry trees; the main temple hall on its platform, flanked by komainu,
    stone lanterns and red railings; the torii with its banner, and crest banners on poles."""
    h = 150
    c = Canvas(LAYER_W, h)
    band = Canvas(LAYER_W, h)
    rnd = noise(910)
    band.rect(0, h - 26, LAYER_W - 1, h - 1, P.SK_BLOSSOM_DD)
    for i in range(16):
        x = i * LAYER_W / 16 + rnd() * 10
        top = h - 34 - rnd() * 14
        W.wrapped(lambda px, top=top, i=i: W.round_tree(band, px, h, top, 20, 920 + i,
                                                        (P.SK_BLOSSOM_DD, P.SK_BLOSSOM_DD, P.SK_BLOSSOM_D,
                                                         P.SK_BLOSSOM, P.SK_BLOSSOM),
                                                        (P.SK_ROOF, P.SK_ROOF_D), (4, 7)), x)
    c.paste(W.haze(band, P.SK_SKY_HAZE, 0.25))
    for k, (x, th, w) in enumerate(((22, 104, 76), (292, 96, 70))):
        W.piece(c, lambda layer, px, th=th, w=w, k=k: gnarled_cherry(layer, px, h - 1, th, w, 930 + k), x,
                P.SK_BLOSSOM_DD)
    W.piece(c, lambda layer, px: temple(layer, px, h - 1, 0.9), 168, P.SK_ROOF_D)
    for x0, x1 in ((86, 112), (224, 250)):
        W.piece(c, lambda layer, px, w=x1 - x0: railing(layer, px, px + w, h - 1), x0, P.SK_RED_D)
    for x, side in ((116, 1), (220, -1)):
        W.piece(c, lambda layer, px, side=side: komainu(layer, px, h - 1, side), x, P.SK_ROCK_DD)
    for x in (100, 236):
        W.piece(c, lambda layer, px: stone_lantern(layer, px, h - 1), x, P.SK_ROCK_DD)
    W.piece(c, lambda layer, px: torii(layer, px, h - 1, 1.0), 60, P.SK_RED_D)
    for x, white in ((254, False), (266, True)):
        W.piece(c, lambda layer, px, white=white: banner(layer, px, h - 1, white), x, P.SK_RED_D)
    falling_petals(c, 935, 18, 10, h - 20)
    return W.haze(c, P.SK_SKY_L, 0.08)


def sakura_bushes() -> Canvas:
    """Low bushes covered in pink blossom, with small paper lanterns on posts here and there."""
    h = 24
    c = Canvas(LAYER_W, h)
    rnd = noise(940)
    for i in range(11):
        x = i * LAYER_W / 11 + rnd() * 12
        w = 14 + rnd() * 14
        tall = 8 + rnd() * 5

        def bush(layer, px, w=w, tall=tall, i=i):
            W.canopy(layer, px, h - tall / 2 + 1, w, tall + 2, 950 + i,
                     (P.KIT_GREEN_DD, P.KIT_GREEN_D, P.SK_BLOSSOM_D, P.SK_BLOSSOM, P.SK_BLOSSOM_L), size=(3, 5))
        W.piece(c, bush, x)
    for x in (58, 176, 274):
        def lantern(layer, px):
            layer.line((px, h - 1), (px, h - 9), P.BARK_D)
            layer.rect(px - 2, h - 15, px + 2, h - 10, P.SK_CLOUD_W)
            layer.rect(px - 1, h - 14, px + 1, h - 11, P.LANTERN)
            layer.rect(px - 2, h - 15, px + 2, h - 15, P.SK_RED_D)
            layer.rect(px - 2, h - 10, px + 2, h - 10, P.SK_RED_D)
        W.piece(c, lantern, x)
    return W.haze(c, P.SK_SKY_L, 0.04)


# --- ground, terrain, island, pit -----------------------------------------------------------------------

# --- ground, terrain, island (pass 2: the atlas's mossy dark stone blocks) --------------------------------

ROCK = (P.SK_ROCK_L, P.SK_ROCK, P.SK_ROCK_D)
ROCK_DARK = (P.SK_ROCK, P.SK_ROCK_D, P.SK_ROCK_DD)


def stone_texture(w: int, h: int, courses: list, seed: int) -> Canvas:
    """Big rounded stone blocks over dark mortar, periodic in both directions (each stone is drawn wrapped), with a
    little moss on some of their tops. `courses` = (y0, height, widths, offset); their heights must add up to h."""
    c = Canvas(w, h)
    c.rect(0, 0, w - 1, h - 1, P.SK_ROCK_DD)
    rnd = noise(seed)
    for y0, height, widths, offset in courses:
        x = offset
        for sw in widths:
            ramp = ROCK if rnd() > 0.3 else ROCK_DARK
            mossy = rnd() > 0.55
            spot = (rnd(), rnd())
            for dx in (-w, 0, w):
                W.cobble(c, x + dx, y0, x + dx + sw - 2, y0 + height - 2, ramp)
                if mossy:
                    c.rect(x + dx + 2, y0, x + dx + sw - 4, y0, P.SK_MOSS_D)
                    c.px(x + dx + 3, y0 + 1, P.SK_MOSS_DD)
                c.px(x + dx + 2 + spot[0] * (sw - 6), y0 + 2 + spot[1] * (height - 5), ramp[2])
            x += sw
    return c


def mossy_turf(c: Canvas, width: int, seed: int, x0: int = 0, depth: int = 4) -> None:
    """Olive moss on rows 0..depth with tufts hanging up to 4 rows below it and pink petals scattered over it.
    Every column's look is a function of x mod `width`, so a tile of that width repeats seamlessly."""
    for x in range(width):
        k = (x * 7 + seed) % 11
        c.rect(x0 + x, 0, x0 + x, depth, P.SK_MOSS)
        c.px(x0 + x, 0, P.SK_MOSS_L)
        if k % 3 == 0:
            c.px(x0 + x, 1, P.SK_MOSS_L)
        c.px(x0 + x, depth, P.SK_MOSS_D)
        drop = (0, 1, 2, 1, 3, 0, 2, 4, 1, 0, 2)[k]
        for d in range(drop):
            c.px(x0 + x, depth + 1 + d, P.SK_MOSS_D if d < drop - 1 else P.SK_MOSS_DD)
    for x in range(width):
        k = (x * 5 + seed * 3) % 13
        if k in (0, 6):                                        # a blossom: five dots
            for dx, dy, col in ((0, 0, P.SK_BLOSSOM_W), (-1, 0, P.SK_BLOSSOM), (1, 0, P.SK_BLOSSOM),
                                (0, -1, P.SK_BLOSSOM_L), (0, 1, P.SK_BLOSSOM_D)):
                c.px(x0 + (x + dx) % width, 2 + dy + (x % 2), col)
        elif k in (3, 9):
            c.px(x0 + x, 1 + (x % 3), P.SK_BLOSSOM_L)          # loose petals
        elif k == 11:
            c.px(x0 + x, depth + 2, P.SK_BLOSSOM)              # a petal caught in the hanging moss


EARTH_COURSES = [(0, 9, [11, 10, 11], 0), (9, 9, [9, 12, 11], 5), (18, 9, [12, 10, 10], 2), (27, 9, [10, 11, 11], 7)]


def sakura_earth(c: Canvas) -> None:
    """32x36: four courses of 9-row blocks, periodic, so it stacks under itself and under the ground tile."""
    c.paste(stone_texture(32, 36, EARTH_COURSES, 1001))


def sakura_ground(c: Canvas) -> None:
    """32x48: the same blocks (rows 12-47 are exactly the earth tile) under mossy turf with petals."""
    tex = stone_texture(32, 36, EARTH_COURSES, 1001)
    c.paste(tex, 0, 12)
    c.paste(tex, 0, -24)
    mossy_turf(c, 32, 5)


FILL_COURSES = [(0, 8, [9, 7], 2), (8, 8, [7, 9], 7)]


def stone_end(c: Canvas, y0: int, y1: int) -> None:
    c.rect(4, y0, 7, y1, P.SK_ROCK_DD)
    W.cobble(c, 2, y0, 7, y1, ROCK)


def outline_left(c: Canvas, rows) -> None:
    for y in rows:
        for x in range(c.size[0]):
            if c.img.getpixel((x, y))[3]:
                c.px(x - 1, y, P.SK_ROCK_DD)
                break


def terrain() -> list[Sprite]:
    top = Canvas(16, 16)                                       # turf over one 9-row course, rim at row 15
    top.paste(stone_texture(16, 16, [(7, 9, [7, 9], 0), (0, 7, [16], 0)], 1002))
    mossy_turf(top, 16, 2)
    edge = Canvas(8, 16)                                       # rounded mossy corner over a stone end
    stone_end(edge, 7, 15)
    outline_left(edge, range(7, 16))
    for y, x0 in enumerate((3, 1, 0, 0, 0)):
        edge.rect(x0, y, 7, y, P.SK_MOSS_L if y == 0 else P.SK_MOSS_D if y == 4 else P.SK_MOSS)
    edge.rect(0, 5, 1, 5, P.SK_MOSS_D)
    for x, drop in ((0, 3), (3, 2), (5, 4)):
        edge.rect(x, 5, x, 4 + drop, P.SK_MOSS_D)
        edge.px(x, 5 + drop, P.SK_MOSS_DD)
    for dx, dy, col in ((4, 2, P.SK_BLOSSOM_W), (3, 2, P.SK_BLOSSOM), (5, 2, P.SK_BLOSSOM), (4, 1, P.SK_BLOSSOM_L),
                        (4, 3, P.SK_BLOSSOM_D), (1, 2, P.SK_BLOSSOM_L), (5, 8, P.SK_BLOSSOM)):
        edge.px(dx, dy, col)
    wall = Canvas(8, 16)                                       # two stone ends, a moss streak, a petal
    stone_end(wall, 0, 7)
    stone_end(wall, 8, 15)
    outline_left(wall, range(16))
    for x, y in ((3, 0), (4, 0), (5, 0), (3, 8), (4, 8)):
        wall.px(x, y, P.SK_MOSS_D)
    wall.px(4, 1, P.SK_MOSS_DD)
    wall.px(5, 9, P.SK_BLOSSOM_L)
    fill = stone_texture(16, 16, FILL_COURSES, 1003)
    return [single("terrain_sakura_top", top), single("terrain_sakura_edge", edge),
            single("terrain_sakura_wall", wall), single("terrain_sakura_fill", fill)]


def island() -> Sprite:
    """48x24 like `island`: mossy turf with blossoms (top row = walk surface) over a rounded wedge of dark stone
    blocks, moss and blossom trailing from its sides."""
    body = wedge([(6, 8, [9, 10, 9, 10, 10], 1, ROCK, 1011), (12, 7, [8, 9, 7, 9, 8, 7], 5, ROCK_DARK, 1012),
                  (17, 6, [7, 8, 8, 7], 9, ROCK_DARK, 1013)], P.SK_ROCK_DD, P.SK_ROCK_DD)
    slab_top(body, [P.SK_MOSS_L, P.SK_MOSS, P.SK_MOSS, P.SK_MOSS, P.SK_MOSS_D, P.SK_MOSS_D, P.SK_MOSS_DD])
    c = finish(body, P.SK_ROCK_DD)
    turf = Canvas(44, 12)
    mossy_turf(turf, 44, 7)
    c.paste(turf, 2, 0)
    for y, inset in enumerate((2, 1, 0, 0, 0)):              # keep the rounded ends
        for k in range(inset + 2):
            c.px(k, y, P.CLEAR)
            c.px(47 - k, y, P.CLEAR)
    c.px(2, 0, P.CLEAR)
    c.px(45, 0, P.CLEAR)
    for x, top, length in ((3, 6, 9), (44, 6, 7)):            # moss trailing from the sides, with blossom
        for k in range(length):
            c.px(x, top + k, P.SK_MOSS_D if k % 2 else P.SK_MOSS)
        c.px(x, top + length, P.SK_BLOSSOM)
        c.px(x - 1, top + length - 3, P.SK_BLOSSOM_L)
    for x, y in ((16, 14), (30, 13), (23, 19)):
        c.px(x, y, P.SK_MOSS_D)
    return single("island_sakura", c)


# --- bridge and pool --------------------------------------------------------------------------------------

def bridge() -> Sprite:
    """48x12 like `bridge`, after the atlas's red arched bridge: red-lacquered deck planks (walk surface = top
    row) with a gold-studded red fascia, a red arch over a grey stone underside, and a red post with a gold cap at
    the left. Crumbles like the forest bridge."""
    w, h = 48, 12
    c = Canvas(w, h)
    for i, x in enumerate(range(4, w, 6)):                    # deck planks
        c.rect(x, 1, x + 4, 2, P.SK_RED_L if i % 2 else P.SK_RED)
        c.rect(x, 1, x + 4, 1, P.SK_RED_L)
        c.rect(x + 5, 1, x + 5, 2, P.SK_RED_D)
    c.rect(4, 3, w - 1, 4, P.SK_RED)                          # fascia with gold studs
    c.rect(4, 4, w - 1, 4, P.SK_RED_D)
    for x in range(7, w, 8):
        c.px(x, 3, P.GOLD)
    for k in range(w - 4):                                    # stone underside and the red arch
        x = 4 + k
        y = 5 + round((1 - math.sin(k / (w - 5) * math.pi)) * 5)
        c.rect(x, 5, x, y, P.SK_ROCK if (k // 4) % 2 else P.SK_ROCK_D)
        c.px(x, y, P.SK_RED)
        if y < 11:
            c.px(x, y + 1, P.SK_RED_D)
    c.rect(0, 1, 3, 11, P.SK_RED)                             # post with a gold cap
    c.rect(3, 1, 3, 11, P.SK_RED_D)
    c.rect(0, 1, 3, 2, P.GOLD)
    c.rect(0, 2, 3, 2, P.GOLD_D)
    c.rect(0, 9, 3, 11, P.SK_ROCK)
    for x, col in ((11, P.SK_BLOSSOM_L), (26, P.SK_BLOSSOM), (39, P.SK_BLOSSOM_L)):
        c.px(x, 2, col)
    return platform("bridge_sakura", c.outline(P.SK_RED_D), "crumble", BRIDGE_SEED)


def lilies(sprite: Sprite) -> Sprite:
    """Adds two lily pads (one with a pink flower) and a floating blossom to every frame of the pool surface, on rows
    5-7 below the foam band; the
    pads sit still, the blossom bobs a pixel, so the 4-frame loop stays seamless."""
    out = Sprite(sprite.name, sprite.size)
    for anim, data in sprite.anims.items():
        frames = []
        for k, frame in enumerate(data.frames):
            c = Canvas(*sprite.size)
            c.paste(frame)
            for px, py in ((3, 6), (12, 6)):
                c.ellipse(px, py, 2.4, 1, P.SK_LILY)
                c.rect(px - 2, py, px + 2, py, P.SK_LILY)
                c.px(px - 1, py - 1, P.SK_LILY_L)
                c.px(px + 2, py, P.SK_LILY_D)
                c.px(px + 1, py, P.WATER)                     # the pad's notch
            c.px(3, 5, P.SK_BLOSSOM_W)
            c.px(2, 5, P.SK_BLOSSOM)
            c.px(4, 5, P.SK_BLOSSOM)
            by = 6 + (k % 2)
            c.px(8, by, P.SK_BLOSSOM_L)
            c.px(9, by, P.SK_BLOSSOM)
            frames.append(c)
        out.add(anim, frames, fps=data.fps, loop=data.loop)
    return out


def pit() -> list[Sprite]:
    """The forest's waterfall pit with grey-purple stonework and blossoms on the rim; the water stays blue."""
    stone = {"ravine_sakura": WF.wall_a(), "ravine_sakura_b": WF.wall_b(), "ravine_sakura_back": WF.back(),
             "ravine_sakura_floor": WF.floor()}
    out = [sakura_single(n, s) for n, s in stone.items()]
    out.append(sakura_single("ravine_sakura_rim", WF.rim(), petal=(961, 14, (0, 14), False)))
    out.append(sakura_single("ravine_sakura_vines", WF.vines(), petal=(962, 10, (0, 23), False)))
    for name, sprite in (("falls", WF.falls()), ("falls_edge", WF.falls_edge()), ("lip", WF.lip()),
                         ("surface", WF.surface()), ("pool", WF.pool()), ("splash", WF.splash()), ("deep", WF.deep())):
        out.append(sakura_single(f"ravine_sakura_{name}", sprite, {}))
    out = [lilies(o) if o.name == "ravine_sakura_surface" else o for o in out]
    fill = Canvas(8, 48)                                             # the plain-pit fallback, as the forest's
    for y0, y1, col in ((0, 39, P.SK_ROCK_D), (40, 40, P.WHITE), (41, 41, P.WATER_L), (42, 44, P.WATER),
                        (45, 46, P.WATER_D), (47, 47, P.WATER_DD)):
        fill.rect(0, y0, 7, y1, col)
    out.append(single("ravine_sakura_fill", fill))
    return out


# --- platforms and props --------------------------------------------------------------------------------

def moving_platform() -> Sprite:
    """48x12 wooden plank platform (walk surface = top row) on two short posts, for the moving platforms."""
    w, h = 48, 12
    c = Canvas(w, h)
    c.rect(1, 1, w - 2, 5, P.PLANK)
    for x in range(1, w - 1, 8):                                    # planks
        c.rect(x, 1, x + 6, 1, P.PLANK_L)
        c.rect(x + 7, 1, x + 7, 5, P.PLANK_D)
        c.px(x + 2 + (x // 8) % 3, 3, P.PLANK_D)
    c.rect(1, 5, w - 2, 5, P.PLANK_D)
    for px in (5, w - 8):                                           # posts with bound tips
        c.rect(px, 6, px + 2, 10, P.BARK)
        c.rect(px + 2, 6, px + 2, 10, P.BARK_D)
        c.rect(px, 7, px + 2, 7, P.SAND)
        c.px(px + 1, 11, P.BARK_D)
    c.px(14, 2, P.SK_BLOSSOM_L)
    c.px(33, 3, P.SK_BLOSSOM)
    return single("platform_sakura_moving", c.outline(P.WOOD_OUT))


def bamboo_spikes() -> Sprite:
    """About 22x20: a bed of cut bamboo in a stone-edged pit (feet on row 19, centre x 11). `idle` shows only the cut
    stubs; `warn` they rattle up a little; `rise` the spears thrust up to full height."""
    size, cx, gy = (22, 20), 11, 19
    xs = (3, 8, 13, 18)

    def frame(heights: list, shake: int = 0) -> Image.Image:
        c = Canvas(*size)
        for k, (x, hgt) in enumerate(zip(xs, heights)):
            top = gy - 2 - hgt
            c.rect(x - 1, top, x + 1, gy - 2, P.SK_BAMBOO)
            c.rect(x - 1, top, x - 1, gy - 2, P.SK_BAMBOO_L)
            c.rect(x + 1, top, x + 1, gy - 2, P.SK_BAMBOO_D)
            for ny in range(int(gy - 6), int(top), -5):              # nodes
                c.rect(x - 1, ny, x + 1, ny, P.SK_BAMBOO_D)
            c.poly([(x - 1, top), (x + 1, top - 3), (x + 1, top)], P.SK_BAMBOO_L)   # the slanted cut, sharp
            c.px(x + 1, top - 3, P.SK_BLOSSOM_W)
        c.rect(0, gy - 2, 21, gy, P.SK_STONE)                        # stone kerb
        c.rect(0, gy - 2, 21, gy - 2, P.SK_STONE_L)
        for x in (5, 16):
            c.px(x, gy - 1, P.SK_STONE_D)
        c.outline(P.SK_BAMBOO_DD)
        if shake:
            for x in xs:
                c.px(x + 2, gy - 4, P.SK_STONE_L)                    # dust
        return c.img

    sprite = Sprite("bamboo_spikes", size, cx=cx, ground=gy)
    sprite.add("idle", [frame([1, 1, 1, 1])], fps=1)
    sprite.add("warn", [frame([2, 3, 2, 3], shake=1), frame([3, 2, 3, 2], shake=1)], fps=10)
    sprite.add("rise", [frame([7, 9, 8, 6]), frame([14, 16, 15, 13]), frame([13, 15, 14, 12])], fps=14, loop=False)
    return sprite


def build() -> list[Sprite]:
    return [
        *S.smooth_sky("sakura", [P.SK_SKY_TOP, P.SK_SKY, P.SK_SKY_L, P.SK_SKY_HAZE]),
        sakura_clouds("bg_sakura_puffs", 120, [(30, 50, 34, 16), (110, 90, 26, 12), (176, 40, 40, 18),
                                               (250, 80, 30, 14), (300, 30, 22, 10)], 971),
        sakura_clouds("bg_sakura_clouds", 150, [(20, 70, 62, 30), (92, 40, 40, 20), (150, 84, 74, 34),
                                                (222, 34, 46, 22), (282, 74, 56, 28), (120, 104, 36, 14)], 972),
        single("bg_sakura_far", sakura_far()),
        single("bg_sakura_near", sakura_near()),
        single("bg_sakura_bushes", sakura_bushes()),
        *S.ground("sakura", sakura_ground, sakura_earth),
        S.flat("ground_sakura_fill", P.SK_ROCK_DD),
        *pit(), *terrain(), island(), bridge(), moving_platform(), bamboo_spikes(),
    ]
