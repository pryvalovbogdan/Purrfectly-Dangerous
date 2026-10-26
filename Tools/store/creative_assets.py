#!/usr/bin/env python3
"""App Store "creative assets" (product page header and search result art) from the game's own art.

    Tools/.venv/bin/python Tools/store/creative_assets.py     # writes docs/store/creative/*.png

A moment from level 1, the Purrwood forest, drawn the way the game draws it (LevelBackdrop): the
forest sky band, clouds, the far cliff and castle, the near trees, the bushes, then the forest
ground strip and its earth. Fluffy leaps over a hedgehog through a trail of fish while a squirrel
soldier marches in, and the painted title logo sits above. Everything that matters stays in the
middle ~70% of the width and above the bottom fifth (the ground), where the App Store lays its own
name and Get button over the art.

Everything is laid out in "paint pixels", 3 per world unit: the painted sprites (hero, enemies) are
drawn at that resolution and the world-unit pixel art (scenery, ground, fish) is enlarged x3 with
nearest neighbour, exactly the proportions the game shows them in. That canvas is then enlarged by a
whole number with nearest neighbour and centre-cropped to the exact size, so every pixel stays
square and sharp. Only the title logo, a painting with no pixel grid, is resized smoothly, straight
to its final size. No randomness: the files are identical between runs.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "App/Resources/Assets.xcassets"
ATLAS = ASSETS / "Sprites.spriteatlas"
MANIFEST = json.loads((ROOT / "App/Resources/Sprites.json").read_text())
OUT = ROOT / "docs/store/creative"
PAINT = 3  # paint pixels per world unit
THEME = "forest"


@dataclass(frozen=True)
class Layout:
    """One output. `k` is the whole-number enlargement of the paint canvas (device pixels per
    world unit = 3k). Positions are world units: x from the centre, heights above the ground line.
    `ground` is the share of the height where the ground line sits; `title_h` is the logo's height
    and `title_top` its top, as shares of the image height."""
    name: str
    size: tuple[int, int]
    k: int
    ground: float
    title_h: float
    title_top: float
    hero_x: int
    hero_lift: int
    hedgehog_x: int
    squirrel_x: int
    fish: tuple[tuple[int, int], ...]


def arc(x0: int, x1: int, base: int, rise: int, count: int) -> tuple[tuple[int, int], ...]:
    """Points along a hump from x0 to x1, `base` above the ground at the ends, `rise` more mid-way."""
    return tuple((round(x0 + (x1 - x0) * i / (count - 1)),
                  round(base + rise * math.sin(math.pi * i / (count - 1)))) for i in range(count))


LAYOUTS = (
    # Fluffy has just cleared the hedgehog and sails on toward the fish and the squirrel soldier.
    Layout("header_16x9", (5244, 2950), 8, ground=0.80, title_h=0.32, title_top=0.03,
           hero_x=-4, hero_lift=18, hedgehog_x=-46, squirrel_x=60, fish=((26, 30), (42, 36))),
    Layout("header_21x9", (3840, 1646), 5, ground=0.80, title_h=0.36, title_top=0.03,
           hero_x=-4, hero_lift=14, hedgehog_x=-56, squirrel_x=66, fish=((26, 26), (44, 32))),
    Layout("search_3x2", (3840, 2560), 8, ground=0.80, title_h=0.29, title_top=0.03,
           hero_x=-6, hero_lift=18, hedgehog_x=-36, squirrel_x=39, fish=((19, 34), (32, 42))),
)


def frame(sprite: str, anim: str, index: int = 0) -> Image.Image:
    """A sprite frame at paint resolution: painted sprites as they are, pixel art enlarged x3."""
    spec = MANIFEST[sprite]
    sequence = spec["animations"][anim].get("sequence")
    name = f"{sprite}_{anim}_{sequence[index] if sequence else index}"
    img = Image.open(ATLAS / f"{name}.imageset" / f"{name}.png").convert("RGBA")
    k = PAINT // spec.get("scale", 1)
    return img.resize((img.width * k, img.height * k), Image.NEAREST) if k > 1 else img


def place(c: Image.Image, sprite: str, anim: str, index: int, x: int, feet: int) -> None:
    """Stands a sprite with its anchor (feet) at paint x / paint row `feet`, as the game does."""
    spec = MANIFEST[sprite]
    img = frame(sprite, anim, index)
    left = round(x - spec["anchorX"] * img.width)
    top = round(feet + spec["anchorY"] * img.height) - img.height
    c.alpha_composite(img, (left, top))


def tile_row(c: Image.Image, tile: Image.Image, top: int, start: int) -> None:
    """Repeats `tile` across the canvas, with the tile's column `start` at the canvas's left edge."""
    x = -(start % tile.width)
    while x < c.width:
        c.alpha_composite(tile, (x, top))
        x += tile.width


# Which column of each 320-unit scenery strip sits at the centre of the picture: the near trees
# frame the cabin, the castle on its cliff stands off to the right, clear of the title.
CENTRE_COLUMN = {"clouds": 150, "far": 160, "near": 143, "bushes": 120}


def scene(lay: Layout) -> Image.Image:
    w, h = math.ceil(lay.size[0] / lay.k), math.ceil(lay.size[1] / lay.k)
    c = Image.new("RGBA", (w, h))
    ground = round(h * lay.ground)
    mid = w // 2
    u = PAINT

    # Sky: the banded forest sky standing on the ground line, its top colour above it.
    band = frame(f"bg_{THEME}_sky", "still")
    c.alpha_composite(frame(f"bg_{THEME}_sky_top", "still").resize((w, h), Image.NEAREST))
    c.alpha_composite(band.resize((w, band.height), Image.NEAREST), (0, ground - band.height))

    # The scenery strips, back to front, each standing on the ground line.
    for name in ("clouds", "far", "near", "bushes"):
        strip = frame(f"bg_{THEME}_{name}", "still")
        tile_row(c, strip, ground - strip.height, CENTRE_COLUMN[name] * u - mid)

    # The ground: its strip (grass edge and earth) from the ground line down, then rows of earth.
    fill = frame(f"ground_{THEME}_fill", "still")
    c.alpha_composite(fill.resize((w, h - ground), Image.NEAREST), (0, ground))
    strip = frame(f"ground_{THEME}", "still")
    tile_row(c, strip, ground, 16 * u - mid)
    earth = frame(f"ground_{THEME}_earth", "still")
    top = ground + strip.height
    while top < h:
        tile_row(c, earth, top, 16 * u - mid)
        top += earth.height

    # A squirrel soldier marches in from the right; a hedgehog trundles along under the leap.
    place(c, "squirrel", "walk", 1, mid + lay.squirrel_x * u, ground)
    place(c, "hedgehog", "walk", 0, mid + lay.hedgehog_x * u, ground)

    # Fish ahead of the cat, the way a level strings them along a jump.
    for i, (dx, dy) in enumerate(lay.fish):
        f = frame("fish", "spin", 0)
        c.alpha_composite(f, (mid + dx * u - f.width // 2, ground - dy * u - f.height // 2))

    # Fluffy, mid-leap.
    place(c, "hero", "jump", 0, mid + lay.hero_x * u, ground - lay.hero_lift * u)
    return c


def title(height: int) -> Image.Image:
    """The painted logo, without the stray specks of paint floating loose around it."""
    art = Image.open(ASSETS / "title_start.imageset/title_start.png").convert("RGBA")
    px = art.load()
    seen: set[tuple[int, int]] = set()
    for y0 in range(art.height):
        for x0 in range(art.width):
            if (x0, y0) in seen or px[x0, y0][3] == 0:
                continue
            blob, todo = [], [(x0, y0)]
            seen.add((x0, y0))
            while todo:
                x, y = todo.pop()
                blob.append((x, y))
                for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if (0 <= n[0] < art.width and 0 <= n[1] < art.height and n not in seen
                            and px[n][3] > 0):
                        seen.add(n)
                        todo.append(n)
            if len(blob) < 200:
                for p in blob:
                    px[p] = (0, 0, 0, 0)
    return art.resize((round(art.width * height / art.height), height), Image.LANCZOS)


def image(lay: Layout) -> Image.Image:
    small = scene(lay)
    big = small.resize((small.width * lay.k, small.height * lay.k), Image.NEAREST)
    w, h = lay.size
    left, top = (big.width - w) // 2, (big.height - h) // 2
    out = big.crop((left, top, left + w, top + h))
    logo = title(round(h * lay.title_h))
    out.alpha_composite(logo, ((w - logo.width) // 2, round(h * lay.title_top)))
    return out.convert("RGB")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for lay in LAYOUTS:
        path = OUT / f"{lay.name}.png"
        image(lay).save(path, optimize=True)
        print(path)


if __name__ == "__main__":
    main()
