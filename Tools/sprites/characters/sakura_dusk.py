"""Sakura's route level 2, "Petal Bridges": a sunset cliffside town, after docs/concept/Sakura World Level 2 Tileset
Sheet.png (reference only). Theme id `sakura_dusk`; same names, sizes and contracts as the other themes.

The stonework, ground, terrain, island, pit and bridges reuse sakura_world.py's generated pieces, recoloured to warmer
dusk stone and moss by a fixed palette map (so every tiling contract carries over). The parallax reuses its temple,
cherry, torii and lantern helpers under a sunset grade. Lantern glows are drawn on their own unoutlined layer and
composited under the lanterns, so the outline pass never rings them."""
from __future__ import annotations

import math

from PIL import Image

import palette as P
from characters import sakura_world as SW
from characters import scenery as S
from characters.forest import platform
from draw import Canvas, noise, see_through
from sprite import Sprite, single
import woodland as W

LAYER_W = S.LAYER_W

DUSK_MAP = {
    P.SK_ROCK_L: P.SD_ROCK_L, P.SK_ROCK: P.SD_ROCK, P.SK_ROCK_D: P.SD_ROCK_D, P.SK_ROCK_DD: P.SD_ROCK_DD,
    P.SK_MOSS_L: P.SD_MOSS_L, P.SK_MOSS: P.SD_MOSS, P.SK_MOSS_D: P.SD_MOSS_D, P.SK_MOSS_DD: P.SD_MOSS_DD,
}
WATER_MAP = {P.WHITE: P.SD_FOAM}                      # the falls' foam catches the sunset
CLOUD_MAP = {P.WHITE: P.SD_CLOUD_L, P.CLOUD_S: P.SD_CLOUD, P.CLOUD_D: P.SD_CLOUD_D}


def rename(sprite: Sprite, name: str, mapping: dict) -> Sprite:
    return SW.sakura_single(name, sprite, mapping)


def glow_layer(size: tuple, spots: list) -> Canvas:
    """Soft warm light: stacked see-through ellipses on a layer of their own, (x, y, radius) each."""
    out = Canvas(*size)
    for x, y, r in spots:
        for rr, a in ((r, 46), (r * 0.65, 66), (r * 0.35, 92)):
            layer = Canvas(*size)
            layer.ellipse(x, y, rr, rr, (P.SD_WINDOW[0], P.SD_WINDOW[1], P.SD_WINDOW[2], a))
            out.paste(layer)
    return out


def paper_lantern(c: Canvas, x: float, top: float, w: int = 5, h: int = 6) -> None:
    """A glowing paper lantern: dark caps, warm ribbed paper, a bright core and a tiny crest."""
    c.rect(x - w / 2 + 1, top, x + w / 2 - 1, top, P.SK_ROOF_D)
    c.rect(x - w / 2, top + 1, x + w / 2, top + h, P.SD_PAPER)
    c.rect(x - w / 2 + 1, top + 1, x + w / 2 - 1, top + h, P.SD_PAPER_L)
    c.rect(x - 0.5, top + 2, x + 0.5, top + h - 1, P.SD_SUN)
    for y in range(int(top) + 2, int(top + h), 2):
        c.px(x - w / 2, y, P.SD_PAPER_D)
        c.px(x + w / 2, y, P.SD_PAPER_D)
    c.rect(x - w / 2 + 1, top + h + 1, x + w / 2 - 1, top + h + 1, P.SK_ROOF_D)


# --- parallax ------------------------------------------------------------------------------------------

def dusk_clouds(name: str, height: int, clouds: list, seed: int, sun: bool) -> Sprite:
    base = S.forest_clouds(name, height, clouds)
    c = Canvas(LAYER_W, height)
    if sun:                                                    # the big setting sun, low on the horizon
        sy = height - 104
        c.paste(glow_layer((LAYER_W, height), [(100, sy, 40)]))
        c.ellipse(100, sy, 19, 19, P.SD_SUN_D)
        c.ellipse(99, sy - 1, 17.5, 17.5, P.SD_SUN)
        for y in (sy + 6, sy + 10, sy + 14):                 # cloud bands across its lower half
            c.rect(78, y, 122, y, P.SD_CLOUD)
    c.paste(SW.recolour(base.anims["still"].frames[0], CLOUD_MAP))
    SW.falling_petals(c, seed, 22, 0, height - 10)
    return single(name, c)


def dusk_far() -> Canvas:
    """Misty violet mountains and distant pagodas against the glow."""
    h = 110
    c = Canvas(LAYER_W, h)
    W.mountains(c, h, 1105, 6, (48, 76), (P.SD_MTN_L, P.SD_MTN, P.SD_MTN_D))
    W.wrapped(lambda px: SW.snow_mountain(c, px, h, 80, 74), 120)
    towers = Canvas(LAYER_W, h)
    for x, base, s in ((40, 96, 0.34), (178, 92, 0.42), (292, 98, 0.3)):
        W.piece(towers, lambda layer, px, base=base, s=s: SW.temple(layer, px, base, s), x, P.SK_ROOF_D)
    c.paste(W.haze(towers, P.SD_MTN_D, 0.45))
    mist = Canvas(LAYER_W, h)
    for x in range(0, LAYER_W, 18):
        mist.ellipse(x + 9, h - 6, 17, 7, P.SD_CLOUD_D)
    c.paste(see_through(mist.img, 150))
    return W.haze(c, P.SD_SKY_PINK, 0.16)


def house(c: Canvas, x: float, base: float) -> None:
    """A cliffside house: wooden walls, glowing windows, a dark tiled roof with upturned eaves."""
    c.rect(x - 14, base - 16, x + 14, base, P.PLANK_D)
    for y in range(int(base) - 15, int(base), 3):
        c.rect(x - 14, y, x + 14, y, P.BARK)
    for wx in (x - 10, x + 3):
        c.rect(wx, base - 12, wx + 6, base - 5, P.BARK_DD)
        c.rect(wx + 1, base - 11, wx + 5, base - 6, P.SD_WINDOW)
        c.rect(wx + 1, base - 11, wx + 2, base - 10, P.SD_WINDOW_L)
        c.line((wx + 3, base - 11), (wx + 3, base - 6), P.BARK_D)
    SW.roof(c, x, base - 16, 40, 12, 0.6, ridge=0.25)


def cliff(c: Canvas, x0: float, x1: float, top: float, base: float) -> None:
    """A mossy cliff of big dark stones with blossom along its rim."""
    tex = SW.stone_texture(int(x1 - x0) + 1, 36, [(0, 9, [11, 10, 11, 12, 9], 0),
                                                                          (9, 9, [9, 12, 11, 10, 11], 5),
                                                                          (18, 9, [12, 10, 10, 11, 10], 2),
                                                                          (27, 9, [10, 11, 11, 12, 9], 7)], 1110)
    for y in range(int(top), int(base) + 1, 36):
        c.paste(tex, x0, y)
    c.rect(x0, base + 1, x1, base + 40, (0, 0, 0, 0))
    c.rect(x0 - 1, top - 1, x1 + 1, top + 2, P.SK_MOSS)
    c.rect(x0 - 1, top - 1, x1 + 1, top - 1, P.SK_MOSS_L)
    for x in range(int(x0), int(x1), 6):
        W.clump(c, x + 3, top - 1, 3, SW.BLOSSOMS)


def lantern_string(c: Canvas, glows: list, x0: float, x1: float, top: float, sag: float, n: int) -> None:
    """Two posts with a sagging rope between them and `n` glowing paper lanterns hanging from it."""
    for px in (x0, x1):
        c.rect(px - 1, top, px + 1, top + 30, P.BARK_D)
        c.rect(px - 1, top, px + 1, top, P.BARK)
    for k in range(int(x1 - x0) + 1):
        t = k / (x1 - x0)
        c.px(x0 + k, top + 2 + sag * 4 * t * (1 - t), P.SAND)
    for i in range(1, n + 1):
        t = i / (n + 1)
        lx, ly = x0 + t * (x1 - x0), top + 2 + sag * 4 * t * (1 - t)
        c.px(lx, ly + 1, P.SAND)
        paper_lantern(c, lx, ly + 2, 4, 5)
        glows.append((lx, ly + 5, 7))


def dusk_near() -> Canvas:
    """Cliffs with houses and a temple glowing warm, a waterfall between them, cherry trees, a torii and strings of
    paper lanterns."""
    h = 150
    c = Canvas(LAYER_W, h)
    band = Canvas(LAYER_W, h)                                   # a distant blossom band
    rnd = noise(1120)
    band.rect(0, h - 24, LAYER_W - 1, h - 1, P.SK_BLOSSOM_DD)
    for i in range(16):
        x = i * LAYER_W / 16 + rnd() * 10
        top = h - 32 - rnd() * 12
        W.wrapped(lambda px, top=top, i=i: W.round_tree(band, px, h, top, 20, 1130 + i, SW.BLOSSOMS,
                                                        (P.SK_ROOF, P.SK_ROOF_D), (4, 7)), x)
    c.paste(W.haze(band, P.SD_SKY_PINK, 0.3))
    for x, top in ((92, 90), (226, 82)):                        # waterfalls between the cliffs
        W.cascade(c, x, top, h - 3, 7, 5)
    glows = []
    cliffs = Canvas(LAYER_W, h)                                 # cliffs, misted so they sit behind the play
    W.piece(cliffs, lambda layer, px: cliff(layer, px, px + 64, 96, h), 14, P.SD_ROCK_DD)
    W.piece(cliffs, lambda layer, px: cliff(layer, px, px + 76, 104, h), 120, P.SD_ROCK_DD)
    W.piece(cliffs, lambda layer, px: cliff(layer, px, px + 56, 90, h), 250, P.SD_ROCK_DD)
    c.paste(W.haze(cliffs, P.SD_MTN_D, 0.35))
    W.piece(c, lambda layer, px: house(layer, px, 95), 40, P.SK_ROOF_D)
    glows += [(33, 87, 9), (46, 87, 9)]
    W.piece(c, lambda layer, px: SW.temple(layer, px, 103, 0.55), 158, P.SK_ROOF_D)
    glows += [(158, 94, 12)]
    W.piece(c, lambda layer, px: house(layer, px, 89), 280, P.SK_ROOF_D)
    glows += [(273, 81, 9), (286, 81, 9)]
    W.piece(c, lambda layer, px: SW.gnarled_cherry(layer, px, 96, 62, 54, 1140), 8, P.SK_BLOSSOM_DD)
    W.piece(c, lambda layer, px: SW.gnarled_cherry(layer, px, 104, 56, 46, 1141), 200, P.SK_BLOSSOM_DD)
    W.piece(c, lambda layer, px: SW.torii(layer, px, 90, 0.7), 300, P.SK_RED_D)
    strings = Canvas(LAYER_W, h)
    lantern_string(strings, glows, 78, 118, 66, 6, 3)
    lantern_string(strings, glows, 230, 262, 60, 5, 2)
    c.paste(glow_layer((LAYER_W, h), glows))                    # the glow, under the lanterns, unoutlined
    W.outline_wrapped(strings, P.SK_ROOF_D)
    c.paste(strings)
    SW.falling_petals(c, 1145, 16, 10, h - 20)
    return W.haze(c, P.SD_SKY_PEACH, 0.1)


def dusk_bushes() -> Canvas:
    return W.haze(SW.sakura_bushes(), P.SD_SKY_PEACH, 0.08)


# --- ground, terrain, island, pit, bridges ---------------------------------------------------------------

def dusk_ground(c: Canvas) -> None:
    SW.sakura_ground(c)
    c.img = SW.recolour(c.img, DUSK_MAP)
    c.d = c.d.__class__(c.img)


def dusk_earth(c: Canvas) -> None:
    SW.sakura_earth(c)
    c.img = SW.recolour(c.img, DUSK_MAP)
    c.d = c.d.__class__(c.img)


def pit() -> list[Sprite]:
    out = []
    for sprite in SW.pit():
        name = sprite.name.replace("ravine_sakura", "ravine_sakura_dusk")
        water = any(sprite.name.endswith(k) for k in ("_falls", "_falls_edge", "_lip", "_splash", "_surface"))
        out.append(rename(sprite, name, {**DUSK_MAP, **(WATER_MAP if water else {})}))
    return out


def hang(c: Canvas, glows: list, x: float, top: float) -> None:
    c.px(x, top, P.SAND)
    paper_lantern(c, x, top + 1, 4, 4)
    glows.append((x, top + 4, 5))


def bridge() -> Sprite:
    """48x12 like `bridge`: the red arched bridge with two paper lanterns hanging under the deck (walk surface = the
    top row). Crumbles like the forest bridge."""
    still = SW.bridge().anims["still"].frames[0]
    lamps, glows = Canvas(48, 12), []
    for x in (16, 34):
        hang(lamps, glows, x, 5)
    lamps.outline(P.SK_ROOF_D)
    c = Canvas(48, 12)
    c.paste(SW.recolour(still, DUSK_MAP))
    c.paste(glow_layer((48, 12), glows))
    c.paste(lamps)
    return platform("bridge_sakura_dusk", c, "crumble", 1151)


def moving_platform() -> Sprite:
    """48x12 like `platform_sakura_moving`: the wooden plank platform with two lanterns hanging between its posts."""
    base = SW.moving_platform().anims["still"].frames[0]
    lamps, glows = Canvas(48, 12), []
    for x in (19, 29):
        hang(lamps, glows, x, 6)
    lamps.outline(P.SK_ROOF_D)
    c = Canvas(48, 12)
    c.paste(base)
    c.paste(glow_layer((48, 12), glows))
    c.paste(lamps)
    return single("platform_sakura_dusk_moving", c)


# --- hazard props -----------------------------------------------------------------------------------------

def lantern_pendulum() -> Sprite:
    """20x40: a big paper lantern on a rope, hanging straight down from the top centre (x 10, row 0: the pivot the
    engine swings it about). `swing` 8 frames: the flame flickers, the glow breathes and the tassel sways."""
    w, h = 20, 40
    frames = []
    for k in range(8):
        lamp = Canvas(w, h)
        lamp.line((10, 0), (10, 12), P.SAND)                     # rope
        lamp.px(10, 4, P.BARK_D)
        lamp.rect(7, 12, 13, 13, P.SK_ROOF_D)                    # top cap
        lamp.rect(5, 14, 15, 30, P.SD_PAPER)                     # paper body
        lamp.rect(4, 16, 16, 28, P.SD_PAPER)
        lamp.rect(6, 15, 14, 29, P.SD_PAPER_L)
        for y in range(16, 30, 3):                               # ribs
            lamp.rect(4, y, 4, y, P.SD_PAPER_D)
            lamp.rect(16, y, 16, y, P.SD_PAPER_D)
            lamp.rect(5, y, 6, y, P.SD_PAPER)
            lamp.rect(14, y, 15, y, P.SD_PAPER)
        lamp.ellipse(10, 22, 2.5 + (k % 2) * 0.5, 4, P.SD_SUN)  # flame light inside, flickering
        SW.crest(lamp, 10, 22)
        lamp.rect(7, 31, 13, 32, P.SK_ROOF_D)                    # bottom cap
        sway = round(math.sin(k / 8 * 2 * math.pi) * 1.4)
        lamp.line((10, 33), (10 + sway, 36), P.SK_RED)           # tassel
        lamp.rect(9 + sway, 36, 11 + sway, 38, P.SK_RED)
        lamp.px(10 + sway, 38, P.SK_RED_D)
        lamp.outline(P.SK_ROOF_D)
        frame = glow_layer((w, h), [(10, 22, 9 + (k % 4 in (1, 2)))])
        frame.paste(lamp)
        frames.append(frame)
    sprite = Sprite("lantern_pendulum", (w, h))
    sprite.add("swing", frames, fps=8)
    return sprite


def falling_lantern() -> Sprite:
    """14x18: a paper lantern on a short cord (`hang` 2, flickering), dropping (`fall` 2, cord snapped, tipping), and
    `burn` 4: a small flame patch where it landed (bottom row = the ground)."""
    w, h = 14, 18

    def lamp_frame(tilt: int, cord: bool, flicker: int) -> Canvas:
        lamp = Canvas(w, h)
        if cord:
            lamp.line((7, 0), (7, 3), P.SAND)
        else:
            lamp.px(7 - tilt, 1, P.SAND)
            lamp.px(7 - tilt, 2, P.SAND)
        lamp.rect(4, 4, 10, 4, P.SK_ROOF_D)
        lamp.rect(3, 5, 11, 13, P.SD_PAPER)
        lamp.rect(4, 5, 10, 13, P.SD_PAPER_L)
        for y in (7, 10):
            lamp.px(3, y, P.SD_PAPER_D)
            lamp.px(11, y, P.SD_PAPER_D)
        lamp.ellipse(7, 9, 1.5 + flicker * 0.5, 2.5, P.SD_SUN)
        lamp.rect(4, 14, 10, 14, P.SK_ROOF_D)
        lamp.outline(P.SK_ROOF_D)
        frame = glow_layer((w, h), [(7, 9, 6 + flicker)])
        img = lamp.img.rotate(-tilt * 12, resample=Image.NEAREST, center=(7, 9))
        frame.paste(img)
        return frame

    def burn(k: int) -> Canvas:
        frame = glow_layer((w, h), [(7, 14, 6 + k % 2)])
        f = Canvas(w, h)
        f.rect(2, 16, 11, 17, P.SK_ROOF_D)                       # the crushed lantern's frame
        f.rect(3, 15, 10, 15, P.SD_PAPER_D)
        for i, x in enumerate((4, 7, 10)):                       # flames licking up
            hgt = (3, 5, 4, 6)[(k + i) % 4]
            f.poly([(x - 1.5, 15), (x + 1.5, 15), (x + (k % 2) - 0.5, 15 - hgt)], P.ORANGE)
            f.line((x, 15), (x, 16 - hgt + 1), P.YELLOW)
        f.px(5 + k % 3, 9 - k % 2, P.SD_PAPER)                   # sparks
        frame.paste(f)
        return frame

    sprite = Sprite("falling_lantern", (w, h))
    sprite.add("hang", [lamp_frame(0, True, 0), lamp_frame(0, True, 1)], fps=4)
    sprite.add("fall", [lamp_frame(1, False, 1), lamp_frame(2, False, 0)], fps=10)
    sprite.add("burn", [burn(k) for k in range(4)], fps=10)
    return sprite


def build() -> list[Sprite]:
    terrain = [rename(s, s.name.replace("terrain_sakura", "terrain_sakura_dusk"), DUSK_MAP) for s in SW.terrain()]
    return [
        *S.smooth_sky("sakura_dusk", [P.SD_SKY_TOP, P.SD_SKY, P.SD_SKY_PINK, P.SD_SKY_PEACH, P.SD_SKY_PEACH]),
        dusk_clouds("bg_sakura_dusk_puffs", 120, [(30, 50, 34, 16), (110, 90, 26, 12), (176, 40, 40, 18),
                                                  (250, 80, 30, 14), (300, 30, 22, 10)], 1161, False),
        dusk_clouds("bg_sakura_dusk_clouds", 150, [(20, 70, 62, 30), (92, 40, 40, 20), (150, 84, 74, 34),
                                                   (282, 74, 56, 28), (120, 104, 36, 14)], 1162, True),
        single("bg_sakura_dusk_far", dusk_far()),
        single("bg_sakura_dusk_near", dusk_near()),
        single("bg_sakura_dusk_bushes", dusk_bushes()),
        *S.ground("sakura_dusk", dusk_ground, dusk_earth),
        S.flat("ground_sakura_dusk_fill", P.SD_ROCK_DD),
        *pit(), *terrain,
        rename(SW.island(), "island_sakura_dusk", DUSK_MAP),
        bridge(), moving_platform(), lantern_pendulum(), falling_lantern(),
    ]
