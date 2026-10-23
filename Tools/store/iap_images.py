"""App Store Connect images for the golden fish packs: one 1024x1024 opaque PNG per pack, the painted pack
(`golden_pack_<amount>`, cut from the user's sheet by the sprite build) over a glowing night backdrop with
the amount below it. No prices: those come from the App Store in the buyer's currency.

    Tools/.venv/bin/python Tools/store/iap_images.py      # writes docs/store/iap/golden_<amount>.png
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "App/Resources/Assets.xcassets"
OUT = ROOT / "docs/store/iap"
FONT = "/System/Library/Fonts/SFNSRounded.ttf"
SIZE = 1024
AMOUNTS = (50, 150, 350, 800)

TOP, BOTTOM = (38, 22, 58), (92, 30, 78)          # plum night, warmer at the bottom
GLOW = (255, 196, 64)                              # the golden fish's gold
CREAM, INK = (255, 244, 214), (36, 20, 30)


def backdrop() -> Image.Image:
    """A vertical plum gradient with a soft gold glow behind the pack and a few fixed sparkles."""
    im = Image.new("RGB", (SIZE, SIZE))
    px = im.load()
    for y in range(SIZE):
        t = y / (SIZE - 1)
        row = tuple(round(a + (b - a) * t) for a, b in zip(TOP, BOTTOM))
        for x in range(SIZE):
            px[x, y] = row
    glow = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(glow).ellipse((150, 120, 874, 760), fill=150)
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    im = Image.composite(Image.new("RGB", (SIZE, SIZE), GLOW), im, glow)
    draw = ImageDraw.Draw(im)
    # Fixed four-point sparkles (no randomness: the files stay identical between runs).
    for x, y, r in ((120, 150, 18), (900, 210, 22), (850, 640, 14), (170, 600, 12), (520, 80, 10), (960, 470, 9)):
        for dx, dy in ((r, 0), (0, r)):
            draw.polygon([(x - dx, y - dy), (x + dy * 0.25, y - dx * 0.25), (x + dx, y + dy),
                          (x - dy * 0.25, y + dx * 0.25)], fill=(255, 236, 170))
    return im


def pack_art(amount: int, width: int) -> Image.Image:
    art = Image.open(ASSETS / f"golden_pack_{amount}.imageset/golden_pack_{amount}.png").convert("RGBA")
    # Specks of the painting's checkerboard and pale sparkle haze left at the art's edge: pale, washed-out
    # pixels reached from the empty background. Highlights inside the outline (eyes, scales) are walled off.
    px = art.load()
    w, h = art.size

    def pale(p: tuple) -> bool:
        r, g, b, a = p
        return a > 0 and min(r, g, b) > 140 and max(r, g, b) - min(r, g, b) < 60

    todo = [(x, y) for y in range(h) for x in range(w) if px[x, y][3] == 0]
    seen = set(todo)
    while todo:
        x, y = todo.pop()
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= n[0] < w and 0 <= n[1] < h and n not in seen and pale(px[n]):
                seen.add(n)
                px[n] = (0, 0, 0, 0)
                todo.append(n)
    k = width / art.width
    return art.resize((width, round(art.height * k)), Image.LANCZOS)


def outlined_text(draw: ImageDraw.ImageDraw, centre: tuple, text: str, size: int, fill, stroke: int) -> None:
    font = ImageFont.truetype(FONT, size)
    font.set_variation_by_name("Black")
    draw.text(centre, text, font=font, fill=fill, anchor="mm", stroke_width=stroke, stroke_fill=INK)


def image(amount: int) -> Image.Image:
    im = backdrop().convert("RGBA")
    art = pack_art(amount, 820)
    # Its shadow, then the art, centred above the amount.
    x, y = (SIZE - art.width) // 2, 640 - art.height
    shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse((x + 60, 600, x + art.width - 60, 680), fill=(0, 0, 0, 110))
    im.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)))
    im.alpha_composite(art, (x, y))
    draw = ImageDraw.Draw(im)
    outlined_text(draw, (SIZE // 2, 780), str(amount), 210, GLOW, 14)
    outlined_text(draw, (SIZE // 2, 920), "GOLDEN FISH", 92, CREAM, 10)
    return im.convert("RGB")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for amount in AMOUNTS:
        image(amount).save(OUT / f"golden_{amount}.png", optimize=True)
        print(OUT / f"golden_{amount}.png")


if __name__ == "__main__":
    main()
