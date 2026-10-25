"""Sakura's route level 3: a night among the shrines, after docs/concept/Sakura World Level 3 Asset Sheet.png
(reference only). Theme id `sakura_night`; same names, sizes and contracts as the other themes.

A deep blue-violet sky with stars and a big pink moon, far pagodas with lit windows on dark mountains, cliffs of dark
slate stone with teal moss and pink blossom, red torii, glowing lanterns, bamboo and blue waterfalls. The ground,
terrain, island, pit and bridges are sakura_world.py's generated pieces recoloured by a fixed palette map (so every
tiling contract carries over), like `sakura_dusk`. The scenery is drawn in daylight colours and then sunk into the
night (`night()`), and only the light sources - lantern paper, windows, the moon - are laid on after, so they glow.
Every glow is its own unoutlined layer composited under the lamp, so the outline pass never rings it."""
from __future__ import annotations

import math

from PIL import Image

import palette as P
from characters import sakura_dusk as SD
from characters import sakura_world as SW
from characters import scenery as S
from characters.forest import platform
from draw import Canvas, noise, see_through
from sprite import Sprite, single
import woodland as W

LAYER_W = S.LAYER_W

NIGHT_MAP = {
    P.SK_ROCK_L: P.SN_ROCK_L, P.SK_ROCK: P.SN_ROCK, P.SK_ROCK_D: P.SN_ROCK_D, P.SK_ROCK_DD: P.SN_ROCK_DD,
    P.SK_MOSS_L: P.SN_MOSS_L, P.SK_MOSS: P.SN_MOSS, P.SK_MOSS_D: P.SN_MOSS_D, P.SK_MOSS_DD: P.SN_MOSS_DD,
}
WATER_MAP = {P.WHITE: P.SN_FOAM}                       # the falls' foam is moonlit
CLOUD_MAP = {P.WHITE: P.SN_CLOUD_L, P.CLOUD_S: P.SN_CLOUD, P.CLOUD_D: P.SN_CLOUD_D}
# Buildings at night: the red walls darken, the white crest panels become lit paper windows.
LIT_MAP = {P.SK_PANEL: P.SD_PAPER_D, P.SK_PANEL_D: P.SK_RED_D, P.SK_RED: P.SK_RED_D, P.SK_RED_L: P.SK_RED,
           P.SK_BLOSSOM_D: P.SD_WINDOW, P.SK_BLOSSOM_L: P.SD_WINDOW_L, **NIGHT_MAP}
# Things that glow keep their colour when the scenery is sunk into the night.
LIGHTS = {c[:3] for c in (P.SD_WINDOW, P.SD_WINDOW_L, P.SD_PAPER, P.SD_PAPER_L, P.SD_PAPER_D, P.SD_SUN, P.LANTERN,
                          P.WATER_L, P.WATER, P.WHITE, P.SN_FOAM, P.GOLD)}
NIGHT_BLOSSOMS = (P.SK_BLOSSOM_DD, P.SK_BLOSSOM_D, P.SK_BLOSSOM, P.SK_BLOSSOM_L, P.SK_BLOSSOM_L)


def rename(sprite: Sprite, name: str, mapping: dict) -> Sprite:
    return SW.sakura_single(name, sprite, mapping)


def night(c: Canvas, colour, amount: float) -> Canvas:
    """Pushes every pixel toward the night `colour`, except the light sources in LIGHTS."""
    img = c.img
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a and (r, g, b) not in LIGHTS:
                px[x, y] = (round(r + (colour[0] - r) * amount), round(g + (colour[1] - g) * amount),
                            round(b + (colour[2] - b) * amount), a)
    c.d = c.d.__class__(img)
    return c


def glow(size: tuple, spots: list, colour=P.SD_WINDOW, strength: float = 1.0) -> Canvas:
    """Soft light on a layer of its own: stacked see-through ellipses, (x, y, radius) each."""
    out = Canvas(*size)
    for x, y, rad in spots:
        for rr, a in ((rad, 40), (rad * 0.65, 60), (rad * 0.35, 90)):
            layer = Canvas(*size)
            layer.ellipse(x, y, rr, rr, (colour[0], colour[1], colour[2], min(255, round(a * strength))))
            out.paste(layer)
    return out


def stars(c: Canvas, seed: int, count: int, y0: float, y1: float) -> None:
    """Pinprick stars, a few of them four-point twinkles."""
    rnd = noise(seed)
    for k in range(count):
        x, y = rnd() * c.size[0], y0 + rnd() * (y1 - y0)
        if k % 7 == 0:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c.px((x + dx) % c.size[0], y + dy, P.SN_STAR_D)
            c.px(x, y, P.SN_STAR)
        else:
            c.px(x, y, P.SN_STAR if k % 3 == 0 else P.SN_STAR_D)


# --- parallax ------------------------------------------------------------------------------------------

def moon(c: Canvas, x: float, y: float, rad: float) -> None:
    """The big pink moon: a pink halo on its own layer, a disc lit from the upper left, soft craters."""
    c.paste(glow(c.size, [(x, y, rad * 2.3)], P.SN_MOON, 0.7))
    c.ellipse(x, y, rad, rad, P.SN_MOON_D)                          # shaded lower right
    c.ellipse(x - 1.5, y - 1.5, rad - 1.5, rad - 1.5, P.SN_MOON)
    c.ellipse(x - rad * 0.4, y - rad * 0.4, rad * 0.32, rad * 0.32, P.SN_MOON_L)
    for dx, dy, r_ in ((0.35, -0.3, 0.2), (-0.3, 0.3, 0.16), (0.2, 0.45, 0.12), (-0.45, -0.2, 0.1), (0.55, 0.15, 0.1)):
        c.ellipse(x + dx * rad, y + dy * rad, r_ * rad, r_ * rad, P.SN_MOON_D)
        c.px(x + dx * rad - r_ * rad * 0.5, y + dy * rad - r_ * rad * 0.5, P.SN_MOON_DD)


def night_clouds(name: str, height: int, clouds: list, seed: int, with_moon: bool) -> Sprite:
    base = S.forest_clouds(name, height, clouds)
    c = Canvas(LAYER_W, height)
    stars(c, seed + 7, 70 if with_moon else 40, 0, height - 30)
    if with_moon:
        moon(c, 210, height - 108, 20)
    c.paste(SW.recolour(base.anims["still"].frames[0], CLOUD_MAP))
    SW.falling_petals(c, seed, 12, 0, height - 10)
    return single(name, c)


def pine(c: Canvas, x: float, base: float, h: float, colour, light=None) -> None:
    """A dark conifer silhouette in three stacked tiers."""
    for k in range(3):
        top = base - h + k * h * 0.26
        w = h * (0.16 + k * 0.08)
        c.poly([(x, top), (x + w, top + h * 0.34), (x - w, top + h * 0.34)], colour)
        if light:
            c.line((x, top), (x - w, top + h * 0.34), light)
    c.rect(x - 0.5, base - h * 0.1, x + 0.5, base, colour)


def lit_temple(c: Canvas, x: float, base: float, s: float, bright: bool = False) -> None:
    """The sakura temple with its walls dark and its crest panels turned into lit paper windows (`bright`: pale
    window dots for the far ones)."""
    layer = Canvas(*c.size)
    SW.temple(layer, x, base, s)
    c.paste(SW.recolour(layer.img, {**LIT_MAP, P.SK_PANEL: P.SD_WINDOW_L} if bright else LIT_MAP))


def night_far() -> Canvas:
    """Dark blue mountains, pine silhouettes, and distant pagodas with lit windows above a violet mist."""
    h = 110
    c = Canvas(LAYER_W, h)
    W.mountains(c, h, 1205, 6, (44, 72), (P.SN_MTN_L, P.SN_MTN, P.SN_MTN_D))
    towers = Canvas(LAYER_W, h)
    glows = []
    hills = Canvas(LAYER_W, h)
    for x, base, s in ((46, 92, 0.36), (176, 86, 0.46), (290, 96, 0.3)):
        W.wrapped(lambda px, base=base, s=s: hills.ellipse(px, base + 14, 70 * s, 16, P.SN_MTN_D), x)
        W.piece(towers, lambda layer, px, base=base, s=s: lit_temple(layer, px, base, s, True), x, P.SK_ROOF_D)
        glows.append((x, base - 30 * s, 26 * s))
    c.paste(hills)
    pines = Canvas(LAYER_W, h)
    rnd = noise(1206)
    for i in range(26):
        x, hh = i * LAYER_W / 26 + rnd() * 8, 14 + rnd() * 14
        W.wrapped(lambda px, hh=hh: pine(pines, px, h - 4, hh, P.SN_MTN_D, P.SN_MTN), x)
    c.paste(pines)
    night(towers, P.SN_MTN_D, 0.25)
    c.paste(glow((LAYER_W, h), glows, P.SD_WINDOW, 0.9))
    c.paste(towers)
    mist = Canvas(LAYER_W, h)
    for x in range(0, LAYER_W, 18):
        mist.ellipse(x + 9, h - 6, 17, 7, P.SN_MIST)
    c.paste(see_through(mist.img, 130))
    return night(c, P.SN_SKY_VIOLET, 0.12)


def bamboo(c: Canvas, x: float, base: float, h: float, seed: int) -> None:
    """A clump of three bamboo stalks with nodes and a few leaf sprays at the top."""
    rnd = noise(seed)
    for k, dx in enumerate((-3, 0, 3)):
        top = base - h * (0.8 + rnd() * 0.2)
        sx = x + dx
        c.rect(sx - 0.5, top, sx + 0.5, base, P.SK_BAMBOO_D)
        c.line((sx - 0.5, top), (sx - 0.5, base), P.SK_BAMBOO)
        for ny in range(int(base) - 6, int(top), -7):
            c.rect(sx - 1, ny, sx + 1, ny, P.SK_BAMBOO_DD)
        for j in range(3):
            ly = top + j * 6 + rnd() * 3
            side = 1 if (j + k) % 2 else -1
            c.line((sx, ly), (sx + side * 5, ly + 2), P.SK_BAMBOO_D)
            c.line((sx + side * 1, ly + 1), (sx + side * 4, ly + 3), P.SK_BAMBOO)


def hanging_lamp(c: Canvas, glows: list, x: float, top: float, w: int = 4, h: int = 5) -> None:
    c.px(x, top, P.SAND)
    SD.paper_lantern(c, x, top + 1, w, h)
    glows.append((x, top + 1 + h / 2 + 1, 6 + w))


def lamp_post(c: Canvas, glows: list, x: float, base: float, tall: float = 26) -> None:
    """A wooden post with a crossbar and a paper lantern hanging from it."""
    c.rect(x - 1, base - tall, x, base, P.SN_WOOD)
    c.rect(x - 1, base - tall, x - 1, base, P.SN_WOOD_L)
    c.rect(x - 2, base - tall, x + 6, base - tall + 1, P.SN_WOOD)
    hanging_lamp(c, glows, x + 4, base - tall + 2, 4, 5)


def night_near() -> Canvas:
    """A distant blossom band; cliffs of dark slate with waterfalls between; a temple, a shrine and a house glowing
    warm; cherry trees, bamboo, a torii and paper lanterns strung between posts."""
    h = 150
    c = Canvas(LAYER_W, h)
    band = Canvas(LAYER_W, h)                                    # distant blossom band
    rnd = noise(1220)
    band.rect(0, h - 22, LAYER_W - 1, h - 1, P.SK_BLOSSOM_DD)
    for i in range(16):
        x = i * LAYER_W / 16 + rnd() * 10
        top = h - 30 - rnd() * 12
        W.wrapped(lambda px, top=top, i=i: W.round_tree(band, px, h, top, 20, 1230 + i, SW.BLOSSOMS,
                                                        (P.SK_ROOF, P.SK_ROOF_D), (4, 7)), x)
    c.paste(night(band, P.SN_SKY_VIOLET, 0.5))
    for x, top in ((94, 92), (228, 84)):                         # waterfalls between the cliffs
        falls = Canvas(LAYER_W, h)
        W.cascade(falls, x, top, h - 3, 7, 5)
        c.paste(SW.recolour(falls.img, WATER_MAP))
    cliffs = Canvas(LAYER_W, h)                                   # slate cliffs with moss and blossom
    W.piece(cliffs, lambda layer, px: SD.cliff(layer, px, px + 66, 98, h), 14, P.SK_ROCK_DD)
    W.piece(cliffs, lambda layer, px: SD.cliff(layer, px, px + 74, 106, h), 120, P.SK_ROCK_DD)
    W.piece(cliffs, lambda layer, px: SD.cliff(layer, px, px + 56, 92, h), 252, P.SK_ROCK_DD)
    cliffs.img = SW.recolour(cliffs.img, NIGHT_MAP)
    c.paste(night(cliffs, P.SN_SKY_BLUE, 0.3))
    glows = []
    scene = Canvas(LAYER_W, h)                                    # buildings, trees and props on the cliff tops
    W.piece(scene, lambda layer, px: SW.gnarled_cherry(layer, px, 98, 62, 54, 1240), 10, P.SK_BLOSSOM_DD)
    W.piece(scene, lambda layer, px: SW.gnarled_cherry(layer, px, 106, 56, 46, 1241), 204, P.SK_BLOSSOM_DD)
    W.piece(scene, lambda layer, px: bamboo(layer, px, 98, 50, 1242), 70, P.SK_BAMBOO_DD)
    W.piece(scene, lambda layer, px: bamboo(layer, px, 92, 46, 1243), 300, P.SK_BAMBOO_DD)
    W.piece(scene, lambda layer, px: bamboo(layer, px, 106, 40, 1244), 184, P.SK_BAMBOO_DD)
    W.piece(scene, lambda layer, px: SD.house(layer, px, 97), 44, P.SK_ROOF_D)
    glows += [(37, 89, 9), (50, 89, 9)]
    W.piece(scene, lambda layer, px: lit_temple(layer, px, 105, 0.55), 158, P.SK_ROOF_D)
    glows += [(158, 96, 14), (158, 74, 9)]
    W.piece(scene, lambda layer, px: SW.torii(layer, px, 92, 0.72), 278, P.SK_RED_D)
    W.piece(scene, lambda layer, px: SW.stone_lantern(layer, px, 92), 258, P.SK_ROCK_DD)
    glows += [(258, 79, 7)]
    W.piece(scene, lambda layer, px: SW.stone_lantern(layer, px, 105), 186, P.SK_ROCK_DD)
    glows += [(186, 92, 7)]
    scene.img = SW.recolour(scene.img, {**NIGHT_MAP, P.SK_PANEL: P.SD_PAPER_L, P.SK_PANEL_D: P.SD_PAPER})
    night(scene, P.SN_SKY_BLUE, 0.22)
    lamps = Canvas(LAYER_W, h)                                    # lanterns, outlined on their own
    SD.lantern_string(lamps, glows, 78, 116, 68, 6, 3)
    SD.lantern_string(lamps, glows, 232, 266, 62, 5, 2)
    lamp_post(lamps, glows, 300, 92)
    lamp_post(lamps, glows, 126, 105, 22)
    W.outline_wrapped(lamps, P.SK_ROOF_D)
    c.paste(glow((LAYER_W, h), glows, P.SD_WINDOW, 1.1))
    c.paste(scene)
    c.paste(lamps)
    SW.falling_petals(c, 1245, 14, 10, h - 20)
    return c


def night_bushes() -> Canvas:
    bushes = SW.sakura_bushes()
    bushes.img = SW.recolour(bushes.img, {P.KIT_GREEN_DD: P.SN_MOSS_DD, P.KIT_GREEN_D: P.SN_MOSS_D,
                                          P.KIT_GREEN: P.SN_MOSS, P.SK_CLOUD_W: P.SD_PAPER_L})
    return night(bushes, P.SN_SKY_BLUE, 0.18)


# --- ground, terrain, island, pit, bridges ---------------------------------------------------------------

def night_ground(c: Canvas) -> None:
    SW.sakura_ground(c)
    c.img = SW.recolour(c.img, NIGHT_MAP)
    c.d = c.d.__class__(c.img)


def night_earth(c: Canvas) -> None:
    SW.sakura_earth(c)
    c.img = SW.recolour(c.img, NIGHT_MAP)
    c.d = c.d.__class__(c.img)


def pit() -> list[Sprite]:
    out = []
    for sprite in SW.pit():
        name = sprite.name.replace("ravine_sakura", "ravine_sakura_night")
        water = any(sprite.name.endswith(k) for k in ("_falls", "_falls_edge", "_lip", "_splash", "_surface"))
        out.append(rename(sprite, name, {**NIGHT_MAP, **(WATER_MAP if water else {})}))
    return out


def lamps_under(size: tuple, xs: tuple, top: float) -> tuple[Canvas, Canvas]:
    lamps, glows = Canvas(*size), []
    for x in xs:
        SD.hang(lamps, glows, x, top)
    lamps.outline(P.SK_ROOF_D)
    return lamps, glow(size, glows, P.SD_WINDOW, 1.2)


def bridge() -> Sprite:
    """48x12 like `bridge`: the red arched bridge with two paper lanterns glowing under the deck (walk surface = the
    top row). Crumbles like the forest bridge."""
    still = SW.bridge().anims["still"].frames[0]
    lamps, light = lamps_under((48, 12), (16, 34), 5)
    c = Canvas(48, 12)
    c.paste(SW.recolour(still, NIGHT_MAP))
    c.paste(light)
    c.paste(lamps)
    return platform("bridge_sakura_night", c, "crumble", 1251)


def moving_platform() -> Sprite:
    """48x12 like `platform_sakura_moving`: the wooden plank platform with two lanterns glowing between its posts."""
    base = SW.moving_platform().anims["still"].frames[0]
    lamps, light = lamps_under((48, 12), (19, 29), 6)
    c = Canvas(48, 12)
    c.paste(base)
    c.paste(light)
    c.paste(lamps)
    return single("platform_sakura_night_moving", c)


def build() -> list[Sprite]:
    terrain = [rename(s, s.name.replace("terrain_sakura", "terrain_sakura_night"), NIGHT_MAP) for s in SW.terrain()]
    return [
        *S.smooth_sky("sakura_night", [P.SN_SKY_TOP, P.SN_SKY, P.SN_SKY_BLUE, P.SN_SKY_VIOLET, P.SN_SKY_GLOW]),
        night_clouds("bg_sakura_night_puffs", 120, [(30, 50, 34, 16), (110, 90, 26, 12), (176, 40, 40, 18),
                                                    (250, 80, 30, 14), (300, 30, 22, 10)], 1261, False),
        night_clouds("bg_sakura_night_clouds", 150, [(20, 70, 62, 30), (100, 44, 40, 20), (176, 66, 64, 22),
                                                     (282, 76, 56, 28), (130, 104, 36, 14)], 1262, True),
        single("bg_sakura_night_far", night_far()),
        single("bg_sakura_night_near", night_near()),
        single("bg_sakura_night_bushes", night_bushes()),
        *S.ground("sakura_night", night_ground, night_earth),
        S.flat("ground_sakura_night_fill", P.SN_ROCK_DD),
        *pit(), *terrain,
        rename(SW.island(), "island_sakura_night", NIGHT_MAP),
        bridge(), moving_platform(),
    ]
