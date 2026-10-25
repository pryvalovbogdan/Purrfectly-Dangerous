"""The Sakura start screen's backdrop, composed from pieces of the user's painted asset sheet instead of drawn in code.

Source: `docs/concept/Sakura Start Screen Asset Sheet.png`, copied to `Tools/sprites/sakura_menu_source.png` (real
transparency: a coloured haze under alpha 200 behind opaque pieces). The layout follows the mock-up
`docs/concept/Sakura Start Screen.png`: Mt Fuji and blue ranges at the back, cherry trees at both sides, the pagoda on
its rock with the red bridge (left), the waterfall cliff with its shrine (centre right), the torii with the paw banner
and lanterns (right), bushes and a flowery hedge along the bottom. The middle of the bottom is left fairly open for the
hero, who stands on the ground line in front of it.

`menu_scene_sakura_portrait` (210x230 points) and `menu_scene_sakura_landscape` (440x150) are 3x PNGs (630x690 and
1320x450 pixels). Their bottom row is the ground line (the app draws the ground strip under it). Unlike
`menu_scene_portrait` / `_landscape` they are TRANSPARENT above the scenery: the app draws `menu_sky` and drifting
clouds behind them. The logo from the same sheet is `title_start_sakura` (cut by `export.titles()`).

Each piece is the sheet's alpha >= 200 pixels in a box (optionally inside a polygon, where pieces of the sheet touch:
the pagoda, its bridge and the waterfall cliff are one painted blob), the largest connected shape only. Pieces are
scaled with `sheet_boss.shrink` (LANCZOS, premultiplied, alpha back to hard 0/255). Plain arithmetic, so every run is
identical.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw

from sheet_boss import clean, shrink
from sprite import Sprite

SOURCE = Path(__file__).resolve().parents[1] / "sakura_menu_source.png"
SCALE = 3
ALPHA = 200

# The split between the pagoda (with the bridge in front of its rock) and the waterfall cliff, which touch in the
# sheet: a line from top to bottom between the pagoda's right cherry tree and the cliff's trees, then along the top
# of the bridge's right end under the cliff's pool.
_SPLIT = [(575, 263), (578, 350), (590, 362), (598, 372), (604, 380), (618, 395), (624, 425), (610, 447),
          (590, 470), (576, 495), (575, 540), (595, 580), (600, 640), (605, 678)]

# name -> (box in the sheet, polygon in sheet pixels or None). The largest opaque shape inside is the piece.
PIECES = {
    "fuji": ((738, 28, 1061, 143), None),
    "range": ((509, 204, 918, 294), None),                 # three snowy peaks (a pink cloud touches on the right)
    "range_low": ((847, 374, 1116, 429), None),            # two low hazy peaks
    "tree_big": ((1071, 9, 1418, 292), [(1071, 9), (1418, 9), (1418, 272), (1297, 272), (1297, 292),
                                        (1213, 292), (1213, 272), (1071, 272)]),
    "tree_round": ((1095, 268, 1340, 440), None),        # the big tree's trunk behind it: see BROWN_ABOVE
    "tree_small": ((1271, 370, 1459, 505), None),
    "tree_lean": ((1377, 111, 1515, 262), None),
    # The pagoda with the bridge in front of its rock; a wooden sign under the bridge's left end is left out.
    "pagoda": ((12, 263, 712, 813), [(0, 263)] + _SPLIT + [(712, 678), (712, 813), (450, 813), (450, 777),
                                                         (0, 777)]),
    "cliff": ((565, 280, 965, 678), [(965, 280), (965, 678)] + _SPLIT[::-1][:-1] + [(575, 280)]),
    "torii": ((991, 452, 1244, 688), None),
    "banner": ((975, 530, 1029, 688), None),
    "lantern_post": ((1247, 493, 1298, 687), None),       # tall red lantern on a post
    "lantern_post2": ((1321, 523, 1385, 687), None),      # shorter, dark roof
    "lantern_stone": ((1383, 582, 1456, 689), None),     # (a cat sign hangs under it in the sheet)
    "bushes": ((14, 707, 288, 794), None),                 # a rocky bank of bushes with blossoms
    "hedge": ((14, 816, 313, 863), None),                  # a low flowery hedge
    "bush": ((528, 798, 642, 871), None),
    "fence": ((410, 818, 511, 863), None),
}

# Pieces whose dark or brown (not pink) pixels above a sheet row are dropped: the big tree's trunk comes down behind the
# round tree's crown in the sheet.
BROWN_ABOVE = {"tree_round": 296}


@lru_cache(maxsize=None)
def _sheet() -> Image.Image:
    return Image.open(SOURCE).convert("RGBA")


@lru_cache(maxsize=None)
def piece(name: str) -> Image.Image:
    """The piece cut out of the sheet with hard alpha, trimmed to its opaque bounds."""
    box, poly = PIECES[name]
    im = _sheet().crop(box)
    w, h = im.size
    alpha = im.getchannel("A").point(lambda a: 255 if a >= ALPHA else 0)
    if poly:
        mask = Image.new("L", im.size, 0)
        ImageDraw.Draw(mask).polygon([(x - box[0], y - box[1]) for x, y in poly], fill=255)
        alpha = Image.composite(alpha, mask, mask)
    a = alpha.load()
    if name in BROWN_ABOVE:
        px = im.load()
        for y in range(min(h, BROWN_ABOVE[name] - box[1])):
            for x in range(w):
                if px[x, y][0] < 170 or px[x, y][2] < px[x, y][1]:
                    a[x, y] = 0
    seen = bytearray(w * h)
    best: list = []
    for y0 in range(h):
        for x0 in range(w):
            if seen[y0 * w + x0] or not a[x0, y0]:
                continue
            seen[y0 * w + x0] = 1
            shape, stack = [], [(x0, y0)]
            while stack:
                x, y = stack.pop()
                shape.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and a[nx, ny]:
                        seen[ny * w + nx] = 1
                        stack.append((nx, ny))
            if len(shape) > len(best):
                best = shape
    keep = Image.new("L", im.size, 0)
    k = keep.load()
    for p in best:
        k[p] = 255
    im.putalpha(keep)
    return clean(im).crop(keep.getbbox())


def put(canvas: Image.Image, name: str, k: float, cx: float, base: float, flip: bool = False) -> None:
    """Piece `name` scaled by `k` (canvas pixels per sheet pixel), its middle at `cx` points from the left and its
    lowest row on row `base` points from the top (`base` = the canvas height puts it on the ground line)."""
    small = shrink(piece(name), k)
    if flip:
        small = small.transpose(Image.FLIP_LEFT_RIGHT)
    x = round(cx * SCALE - small.width / 2)
    y = round(base * SCALE) - small.height
    canvas.paste(small, (x, y), small)


# (piece, k, cx, base, flip), back to front; cx and base in points.
PORTRAIT = [
    ("range", 0.9, 40, 172, False),
    ("range", 0.9, 175, 175, True),
    ("fuji", 1.5, 110, 165, False),
    ("range_low", 0.9, 105, 178, False),
    ("tree_big", 0.8, 10, 140, True),
    ("tree_big", 0.75, 200, 185, False),
    ("tree_small", 0.7, 135, 170, True),
    ("tree_round", 0.7, 80, 200, False),
    ("cliff", 0.75, 150, 230, False),
    ("bushes", 0.6, 95, 214, False),
    ("bush", 0.7, 100, 207, False),
    ("pagoda", 0.7, 22, 230, False),
    ("torii", 0.8, 185, 229, False),
    ("banner", 0.8, 160, 230, False),
    ("lantern_stone", 0.7, 206, 230, False),
    ("bushes", 0.7, 22, 230, False),
    ("hedge", 0.5, 25, 230, False),
    ("hedge", 0.5, 75, 230, True),
    ("hedge", 0.5, 125, 230, False),
    ("hedge", 0.5, 175, 230, True),
]

LANDSCAPE = [
    ("fuji", 1.3, 283, 122, False),
    ("range", 0.8, 55, 138, False),
    ("range", 0.8, 165, 136, True),
    ("range", 0.8, 405, 136, True),
    ("range_low", 0.8, 115, 140, False),
    ("range_low", 0.8, 235, 140, True),
    ("range_low", 0.8, 365, 140, False),
    ("tree_big", 0.6, 18, 136, True),
    ("tree_big", 0.6, 432, 144, False),
    ("tree_round", 0.6, 95, 138, False),
    ("tree_small", 0.6, 140, 136, True),
    ("tree_round", 0.6, 262, 142, True),
    ("tree_small", 0.6, 372, 140, False),
    ("cliff", 0.6, 335, 150, False),
    ("pagoda", 0.55, 200, 150, False),
    ("torii", 0.6, 402, 149, False),
    ("banner", 0.6, 380, 150, False),
    ("lantern_post", 0.55, 288, 150, False),
    ("lantern_stone", 0.55, 433, 150, False),
    ("bushes", 0.5, 22, 150, False),
    ("bushes", 0.5, 68, 150, True),
    ("bushes", 0.5, 114, 150, False),
    ("bush", 0.5, 262, 150, False),
    ("bushes", 0.7, 167, 150, True),
] + [("hedge", 0.5, 25 + 50 * i, 150, i % 2 == 1) for i in range(9)]


def scene(w: int, h: int, layout: list) -> Image.Image:
    canvas = Image.new("RGBA", (w * SCALE, h * SCALE), (0, 0, 0, 0))
    for name, k, cx, base, flip in layout:
        put(canvas, name, k, cx, base, flip)
    return clean(canvas)


def picture(name: str, size: tuple[int, int], layout: list) -> Sprite:
    """One still picture of `size` points at 3x detail (what `single` builds for a 1x picture)."""
    sprite = Sprite(name, size, scale=SCALE)
    sprite.add("still", [scene(*size, layout)], fps=1)
    return sprite


def build() -> list[Sprite]:
    return [
        picture("menu_scene_sakura_portrait", (210, 230), PORTRAIT),
        picture("menu_scene_sakura_landscape", (440, 150), LANDSCAPE),
    ]
