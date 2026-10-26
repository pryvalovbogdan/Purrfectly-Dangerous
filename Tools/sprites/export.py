"""Writes sprites as sheets, GIF previews, an Xcode sprite atlas and a JSON manifest."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image, ImageOps

from sprite import Sprite

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Tools" / "sprites" / "out"
ATLAS = ROOT / "App" / "Resources" / "Assets.xcassets" / "Sprites.spriteatlas"
MANIFEST = ROOT / "App" / "Resources" / "Sprites.json"
PREVIEW_BG = (58, 64, 82, 255)


def frames_of(sprite: Sprite, anim: str) -> list[Image.Image]:
    frames = sprite.anims[anim].frames
    return [ImageOps.mirror(f) for f in frames] if sprite.faces_left else frames


def frame_name(sprite: str, anim: str, index: int) -> str:
    return f"{sprite}_{anim}_{index}"


def unique_frames(frames: list[Image.Image]) -> tuple[list[Image.Image], list[int]]:
    """The distinct frames of one animation, in order of first appearance, and for each played frame the
    index of its stored frame. A frame identical to an earlier one (a held pose, a replayed source frame)
    is written to the atlas once; `Sprites.json` lists the `sequence` when it is not simply 0..n-1."""
    stored: list[Image.Image] = []
    seen: dict[tuple, int] = {}
    sequence = []
    for frame in frames:
        key = (frame.mode, frame.size, frame.tobytes())
        if key not in seen:
            seen[key] = len(stored)
            stored.append(frame)
        sequence.append(seen[key])
    return stored, sequence


def stored_frame_index(manifest_animation: dict, index: int) -> int:
    """Which stored atlas frame (`<sprite>_<anim>_<i>`) played frame `index` shows."""
    return manifest_animation.get("sequence", range(manifest_animation["frames"]))[index]


def sheet(frames: list[Image.Image]) -> Image.Image:
    w, h = frames[0].size
    out = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        out.paste(frame, (i * w, 0))
    return out


def write_png(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # No timestamps or ancillary chunks, so the same pixels always produce the same bytes.
    image.save(path, format="PNG", optimize=False, compress_level=9)


def write_gif(frames: list[Image.Image], fps: int, path: Path, scale: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    big = []
    for frame in frames:
        bg = Image.new("RGBA", frame.size, PREVIEW_BG)
        bg.alpha_composite(frame)
        big.append(bg.resize((frame.width * scale, frame.height * scale), Image.NEAREST).convert("P", palette=Image.ADAPTIVE))
    big[0].save(path, save_all=True, append_images=big[1:], duration=max(20, round(1000 / fps)), loop=0, disposal=2)


def write_atlas_image(image: Image.Image, name: str, scale: int = 1) -> None:
    """One atlas frame. `scale` > 1 (painted sprites at 3x detail) tags the PNG so SpriteKit sizes the
    texture in points: a 132×108 PNG at 3x is a 44×36 texture."""
    folder = ATLAS / f"{name}.imageset"
    write_png(image, folder / f"{name}.png")
    contents = {"images": [{"filename": f"{name}.png", "idiom": "universal", "scale": f"{scale}x"}],
                "info": {"author": "xcode", "version": 1}}
    (folder / "Contents.json").write_text(json.dumps(contents, indent=2) + "\n")


def export(sprites: list[Sprite], only: set[str] | None = None) -> dict:
    """Exports `sprites`; with `only`, other sprites keep their files and manifest entries."""
    ATLAS.mkdir(parents=True, exist_ok=True)
    (ATLAS / "Contents.json").write_text(json.dumps({"info": {"author": "xcode", "version": 1}}, indent=2) + "\n")
    manifest = json.loads(MANIFEST.read_text()) if only and MANIFEST.exists() else {}

    if not only:
        for stale in ATLAS.glob("*.imageset"):
            shutil.rmtree(stale)
        for folder in ("sheets", "preview"):
            shutil.rmtree(OUT / folder, ignore_errors=True)

    for sprite in sprites:
        if only and sprite.name not in only:
            continue
        # The frames of every animation it has or had (the old manifest's), whatever their number: "hero" must not
        # delete "hero_x" sprites of another name, and "sit_happy" has an underscore of its own.
        for anim in set(sprite.anims) | set(manifest.get(sprite.name, {}).get("animations", {})):
            prefix = f"{sprite.name}_{anim}_"
            for stale in ATLAS.glob(f"{prefix}*.imageset"):
                if stale.stem[len(prefix):].isdigit():
                    shutil.rmtree(stale)
        w, h = sprite.size
        anchor_x = 0.5 if sprite.cx is None else (sprite.cx + 0.5) / w
        entry = {"width": w, "height": h,
                 # Anchor of the figure inside the frame, as SpriteKit wants it (origin bottom-left).
                 "anchorX": round(1 - anchor_x if sprite.faces_left else anchor_x, 4),
                 "anchorY": 0 if sprite.ground is None else round((h - 1 - sprite.ground) / h, 4),
                 "animations": {}}
        if sprite.scale != 1:
            entry["scale"] = sprite.scale
        for anim_name, anim in sprite.anims.items():
            frames = frames_of(sprite, anim_name)
            stored, sequence = unique_frames(frames)
            for index, frame in enumerate(stored):
                write_atlas_image(frame, frame_name(sprite.name, anim_name, index), sprite.scale)
            write_png(sheet(frames), OUT / "sheets" / f"{sprite.name}_{anim_name}.png")
            scale = max(1, min(8, 256 // max(sprite.size)) // sprite.scale)
            write_gif(frames, anim.fps, OUT / "preview" / f"{sprite.name}_{anim_name}.gif", scale)
            entry["animations"][anim_name] = {"frames": len(frames), "fps": anim.fps, "loop": anim.loop}
            if sequence != list(range(len(frames))):
                entry["animations"][anim_name]["sequence"] = sequence
        manifest[sprite.name] = entry

    MANIFEST.write_text(json.dumps(dict(sorted(manifest.items())), indent=1) + "\n")
    return manifest


ICON_SOURCE = Path(__file__).parent / "icon_source.png"
# The painting's rounded frame (x0, y0, x1, y1) and corner radius, in its own pixels.
ICON_FRAME, ICON_RADIUS = (39, 32, 1216, 1216), 266
ICON_INSET, ICON_GLOW = 16, 14


def icon_scene() -> Image.Image:
    """The one piece of art that is not drawn in code: the user's icon painting, cropped just inside
    its rounded frame to a full-bleed square. Its black corners are refilled by reflecting the
    picture inward through the corner circle; iOS masks that area anyway."""
    im = Image.open(ICON_SOURCE).convert("RGB")
    x0, y0, x1, y1 = ICON_FRAME
    size = min(x1 - x0, y1 - y0) - 2 * ICON_INSET
    left, top = round((x0 + x1 - size) / 2), round((y0 + y1 - size) / 2)
    art = im.crop((left, top, left + size, top + size))
    px, r = art.load(), ICON_RADIUS - ICON_INSET
    keep = (r - ICON_GLOW) ** 2
    far = size - 1 - r
    for ox, oy in ((r, r), (far, r), (r, far), (far, far)):
        xs = range(r) if ox == r else range(size - r, size)
        ys = range(r) if oy == r else range(size - r, size)
        for y in ys:
            for x in xs:
                dx, dy = x - ox, y - oy
                d2 = dx * dx + dy * dy
                if d2 > keep:
                    k = keep / d2 * 0.97
                    px[x, y] = px[int(ox + dx * k), int(oy + dy * k)]
    return art.resize((1024, 1024), Image.LANCZOS)


def app_icon(sprites: dict[str, Sprite]) -> None:
    """1024px App Store icon from `icon_source.png`. Opaque, as Apple requires."""
    scene = icon_scene()
    folder = ATLAS.parent / "AppIcon.appiconset"
    folder.mkdir(parents=True, exist_ok=True)
    write_png(scene, folder / "icon.png")
    write_png(scene.resize((256, 256), Image.LANCZOS), OUT / "contact" / "app_icon.png")
    contents = {"images": [{"filename": "icon.png", "idiom": "universal", "platform": "ios", "size": "1024x1024"}],
                "info": {"author": "xcode", "version": 1}}
    (folder / "Contents.json").write_text(json.dumps(contents, indent=2) + "\n")
    (ATLAS.parent / "Contents.json").write_text(json.dumps({"info": {"author": "xcode", "version": 1}}, indent=2) + "\n")


# Titles cut from the user's screen paintings rather than drawn in code: (source, box in the
# painting, rectangles inside the box to clear by hand because they are not sky, asset name).
TITLES = [
    ("game_over_source.png", (100, 196, 868, 592), [], "title_game_over"),
    # The start logo: the peeking cat, the leaf wreath, the lettering and the fish. The sound button
    # (top right) and a bush (bottom left) poke into the box and are cleared.
    ("start_source.png", (25, 120, 915, 597), [(770, 0, 890, 60), (0, 400, 70, 477)], "title_start"),
    # The CATS screen's leafy wooden title plank.
    ("cats_source.png", (225, 38, 710, 200), [], "title_cats"),
]


def _sky(p: tuple) -> bool:
    r, g, b = p[:3]
    blue = b > r + 35 and b > g + 5
    cloud = b >= r and b >= g - 6 and min(r, g, b) > 150 and max(r, g, b) - min(r, g, b) < 70
    # Sunlit cloud tops are a warmer white. Whites inside the art (faces, lettering) are walled in by
    # dark outlines, so the fill from the sky never reaches them.
    white = min(r, g, b) > 205 and max(r, g, b) - min(r, g, b) < 50
    return blue or cloud or white


def cut_title(source: str, box: tuple, cleared: list, name: str) -> None:
    """One title from a user painting, like the app icon: cropped to `box`, the sky behind it
    flood-filled away from the edges (outlines stop the fill, so a blue fish inside stays) and
    trimmed to what is left. A regular image, outside the sprite atlas, so it is never packed
    beside other art."""
    im = Image.open(Path(__file__).parent / source).convert("RGBA").crop(box)
    w, h = im.size
    px = im.load()
    for x0, y0, x1, y1 in cleared:
        for y in range(y0, min(y1, h)):
            for x in range(x0, min(x1, w)):
                px[x, y] = (0, 0, 0, 0)
    clear = [[False] * h for _ in range(w)]
    todo = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    todo += [(x, y) for x in range(w) for y in range(h) if px[x, y][3] == 0]
    while todo:
        x, y = todo.pop()
        if clear[x][y] or (px[x, y][3] and not _sky(px[x, y])):
            continue
        clear[x][y] = True
        px[x, y] = (0, 0, 0, 0)
        todo += [(nx, ny) for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
                 if 0 <= nx < w and 0 <= ny < h and not clear[nx][ny]]
    for _ in range(2):                                   # sky-tinted fringe pixels left at the edge
        fringe = [(x, y) for x in range(1, w - 1) for y in range(1, h - 1) if px[x, y][3] and _sky(px[x, y])
                  and any(px[x + dx, y + dy][3] == 0 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
        for x, y in fringe:
            px[x, y] = (0, 0, 0, 0)
    title = im.crop(im.getbbox())
    folder = ATLAS.parent / f"{name}.imageset"
    folder.mkdir(parents=True, exist_ok=True)
    write_png(title, folder / f"{name}.png")
    contents = {"images": [{"filename": f"{name}.png", "idiom": "universal"}],
                "info": {"author": "xcode", "version": 1}}
    (folder / "Contents.json").write_text(json.dumps(contents, indent=2) + "\n")


# The CATS plank with its lettering taken out, for the screen to letter itself from Lore.json (`ui.cats`):
# the painted left end (leaves, paw), the clean wood between the paw and the first letter stretched to
# `PLANK_MIDDLE` pixels (the grain runs along the plank, so it stretches cleanly), the painted right end.
PLANK_LEFT, PLANK_CLEAN, PLANK_RIGHT, PLANK_MIDDLE = 122, (124, 144), 338, 300


def blank_plank() -> None:
    im = Image.open(ATLAS.parent / "title_cats.imageset/title_cats.png").convert("RGBA")
    w, h = im.size
    left = im.crop((0, 0, PLANK_LEFT, h))
    wood = im.crop((PLANK_CLEAN[0], 0, PLANK_CLEAN[1], h)).resize((PLANK_MIDDLE, h), Image.NEAREST)
    right = im.crop((PLANK_RIGHT, 0, w, h))
    out = Image.new("RGBA", (left.width + PLANK_MIDDLE + right.width, h), (0, 0, 0, 0))
    out.paste(left, (0, 0))
    out.paste(wood, (left.width, 0))
    out.paste(right, (left.width + PLANK_MIDDLE, 0))
    name = "title_plank"
    folder = ATLAS.parent / f"{name}.imageset"
    folder.mkdir(parents=True, exist_ok=True)
    write_png(out, folder / f"{name}.png")
    contents = {"images": [{"filename": f"{name}.png", "idiom": "universal"}],
                "info": {"author": "xcode", "version": 1}}
    (folder / "Contents.json").write_text(json.dumps(contents, indent=2) + "\n")


# The Sakura route's boss health bar, from the user's painting (real transparency with a pink haze):
# (box in the sheet, asset name). The boxes are fixed (not trimmed), because the HUD places the name and
# the fill by where the plaque and the track sit in them (`PaintedBossHealth.Style.sakura` in App/UI/PaintedBossHealth.swift).
SAKURA_BAR_SOURCE = "sakura_boss_bar_source.png"
SAKURA_BAR_CUTS = [
    ((95, 25, 1435, 232), "boss_plate_sakura"),            # name plaque; text area x 305-1035, y 73-175
    ((60, 240, 1480, 375), "boss_bar_frame_sakura"),       # bar frame; track x 165-1240, y 40-90
    ((186, 397, 222, 461), "boss_bar_fill_sakura_left"),   # the red fill's rounded ends and a middle slice
    ((700, 397, 708, 461), "boss_bar_fill_sakura_mid"),
    ((1315, 397, 1351, 461), "boss_bar_fill_sakura_right"),
]


# The boss health bar of Fluffy's route (the five base worlds), from the user's floral sheet (real transparency;
# the colours under the clear pixels are a blurred backdrop, which the alpha threshold drops). Like the Sakura
# bar: the boxes are fixed, because `PaintedBossHealth.Style.floral` (App/UI/PaintedBossHealth.swift) places the
# name and the fill by where the field and the track sit in them.
FLORAL_BAR_SOURCE = "floral_boss_bar_source.png"
# (box in the sheet, asset name, smallest shape kept: the plate's box catches the tips of row 2's curls).
FLORAL_BAR_CUTS = [
    ((60, 26, 1476, 252), "boss_plate_floral", 1000),  # row 1, the flowered frame: its dark field (x 240-1175, y 83-159) takes the name
    ((136, 641, 1400, 722), "boss_bar_frame_floral", 40),  # row 6, the empty rounded bar: track x 20-1244, y 16-64
    # Loose pieces the hit effect throws out of the lost piece of fill.
    ((914, 766, 985, 831), "boss_bar_paw_floral", 40),
    ((998, 752, 1083, 850), "boss_bar_leaf_floral", 40),
    ((1187, 757, 1260, 831), "boss_bar_flower_floral", 40),
    ((1412, 794, 1453, 844), "boss_bar_petal_floral", 40),
]
# The orange fill, from the full bar of row 3: its rounded left end, a middle slice and the right end with the paw
# print. Its box (x 156-1380, y 406-454) lines up with the empty bar's track (row 6 sits 251 px lower). The frame
# ring around the fill is cleared by `cut_fill_piece`.
FLORAL_FILL_CUTS = [
    ((156, 406, 186, 454), "boss_bar_fill_floral_left"),
    ((700, 406, 708, 454), "boss_bar_fill_floral_mid"),
    ((1316, 406, 1380, 454), "boss_bar_fill_floral_right"),
]
FLORAL_FILL_ROW = (156, 406, 1380, 454)


# The level loading bar, from the user's loading sheet (real transparency): the empty bar of row 1 (`loading_bar`),
# its dark track alone in the same box (`loading_bar_track`: track x 92-310, y 47-80), for the screen to mask the
# fill with, and the striped fill of the full bar (`loading_bar_fill`, 257x31), which slides in along the track from
# under the paw (`LoadingScreen` in App/UI/LoadingScreen.swift).
LOADING_SOURCE = "loading_source.png"
LOADING_BAR_BOX = (14, 50, 375, 175)
LOADING_CUTS = [
    # (box in the sheet, a point inside the piece, the colours it is made of, asset name)
    (LOADING_BAR_BOX, (200, 112), lambda p: 30 < p[0] < 75 and p[1] < 45 and p[2] < 40, "loading_bar_track"),
    ((1822, 243, 2079, 274), (1950, 255), lambda p: p[0] > 200 and p[1] > 120, "loading_bar_fill"),
]


def cut_region(source: str, box: tuple, seed: tuple, colour, name: str) -> None:
    """One piece of a painting that is only the opaque pixels of `colour` joined to `seed` (sheet coordinates): a
    dark line walls a bar's track or fill in, so the flood stops there. The rest of `box` is cleared."""
    sheet = Image.open(Path(__file__).parent / source).convert("RGBA")
    px = sheet.load()
    region, todo = set(), [seed]
    while todo:
        x, y = todo.pop()
        if (x, y) in region or not (box[0] <= x < box[2] and box[1] <= y < box[3]):
            continue
        if px[x, y][3] < 200 or not colour(px[x, y]):
            continue
        region.add((x, y))
        todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    piece = Image.new("RGBA", (box[2] - box[0], box[3] - box[1]), (0, 0, 0, 0))
    out = piece.load()
    for x, y in region:
        out[x - box[0], y - box[1]] = px[x, y][:3] + (255,)
    folder = ATLAS.parent / f"{name}.imageset"
    folder.mkdir(parents=True, exist_ok=True)
    write_png(piece, folder / f"{name}.png")
    contents = {"images": [{"filename": f"{name}.png", "idiom": "universal"}],
                "info": {"author": "xcode", "version": 1}}
    (folder / "Contents.json").write_text(json.dumps(contents, indent=2) + "\n")


def cut_fill_piece(source: str, row: tuple, box: tuple, name: str) -> None:
    """One piece of a painted bar's fill, where the sheet only shows the fill inside its frame: the fill is what
    the middle of the bar reaches through bright pixels (red over 200), because a dark line walls it in from the
    frame's bright rim. Everything else in `box` (the dark line, the rim at the rounded ends) is cleared."""
    sheet = Image.open(Path(__file__).parent / source).convert("RGBA")
    im = sheet.crop(row)
    w, h = im.size
    px = im.load()

    def bright(p: tuple) -> bool:
        return p[3] >= 200 and p[0] > 200

    fill, todo = set(), [(w // 2, h // 2)]
    while todo:
        x, y = todo.pop()
        if (x, y) in fill or not (0 <= x < w and 0 <= y < h) or not bright(px[x, y]):
            continue
        fill.add((x, y))
        todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    piece = Image.new("RGBA", (box[2] - box[0], box[3] - box[1]), (0, 0, 0, 0))
    out = piece.load()
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            local = (x - row[0], y - row[1])
            if local in fill:
                r, g, b, _ = px[local]
                out[x - box[0], y - box[1]] = (r, g, b, 255)
    folder = ATLAS.parent / f"{name}.imageset"
    folder.mkdir(parents=True, exist_ok=True)
    write_png(piece, folder / f"{name}.png")
    contents = {"images": [{"filename": f"{name}.png", "idiom": "universal"}],
                "info": {"author": "xcode", "version": 1}}
    (folder / "Contents.json").write_text(json.dumps(contents, indent=2) + "\n")


# The Sakura start logo (Sakura peeking over the lettering, blossoms, the fish), from the start screen's asset sheet
# (real transparency; `characters/menu_sakura_painted.py` cuts the backdrop from the same sheet). The box is the
# logo's opaque bounds, so the image is trimmed like `title_start`.
SAKURA_MENU_SOURCE = "sakura_menu_source.png"
SAKURA_TITLE_BOX = (28, 13, 513, 262)


def cut_alpha_piece(source: str | Image.Image, box: tuple, name: str, alpha: int = 200, min_shape: int = 40) -> None:
    """One piece of a painting with real transparency (a file next to this one, or the painting already open):
    pixels under `alpha` (the soft haze) cleared, the rest made fully opaque, and loose specks smaller than
    `min_shape` pixels dropped (raise it to drop a neighbour's tips poking into the box). A regular image,
    outside the atlas."""
    sheet = source if isinstance(source, Image.Image) else Image.open(Path(__file__).parent / source)
    im = sheet.convert("RGBA").crop(box)
    w, h = im.size
    px = im.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255) if a >= alpha else (0, 0, 0, 0)
    seen = set()
    for start in ((x, y) for y in range(h) for x in range(w)):
        if start in seen or px[start][3] == 0:
            continue
        shape, stack = [start], [start]
        seen.add(start)
        while stack:
            x, y = stack.pop()
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= n[0] < w and 0 <= n[1] < h and n not in seen and px[n][3]:
                    seen.add(n)
                    stack.append(n)
                    shape.append(n)
        if len(shape) < min_shape:
            for p in shape:
                px[p] = (0, 0, 0, 0)
    folder = ATLAS.parent / f"{name}.imageset"
    folder.mkdir(parents=True, exist_ok=True)
    write_png(im, folder / f"{name}.png")
    contents = {"images": [{"filename": f"{name}.png", "idiom": "universal"}],
                "info": {"author": "xcode", "version": 1}}
    (folder / "Contents.json").write_text(json.dumps(contents, indent=2) + "\n")


# The start screen's KITTIES button, from the user's UI painting (real transparency): the cream plank with
# Fluffy peeking over it, and the orange one with sparkles for while it is held. Their painted lettering is
# taken out, for the menu to letter them from Lore.json (`ui.cats`, `KittiesButton` in App/UI/MenuStyle.swift):
# (plank box, lettering box, fill colour test, asset name).
KITTIES_SOURCE = "kitties_ui_source.png"
KITTIES_CUTS = [
    ((46, 14, 623, 329), (160, 204, 522, 284), lambda p: p[0] > 240 and p[1] > 200 and p[2] > 150, "kitties_button"),
    ((665, 16, 1256, 330), (788, 204, 1147, 293), lambda p: p[0] > 240 and 140 < p[1] < 190 and p[2] < 40,
     "kitties_button_pressed"),
]


def kitties_buttons() -> None:
    sheet = Image.open(Path(__file__).parent / KITTIES_SOURCE).convert("RGBA")
    px = sheet.load()
    for plank, (x0, y0, x1, y1), fill, name in KITTIES_CUTS:
        # Each row of the lettering's box gets the plank's fill at that height (it shades from top to bottom): the
        # mean of the fill-coloured pixels beside the lettering, over the row and three either side, so one row's
        # highlight does not show as a line.
        beside = {y: [px[x, y][:3] for x in range(plank[0], plank[2]) if not x0 <= x < x1 and fill(px[x, y])]
                  for y in range(y0 - 3, y1 + 3)}
        for y in range(y0, y1):
            near = [c for yy in range(y - 3, y + 4) for c in beside[yy]]
            colour = tuple(round(sum(c[i] for c in near) / len(near)) for i in range(3)) + (255,)
            for x in range(x0, x1):
                px[x, y] = colour
        cut_alpha_piece(sheet, plank, name)


def titles() -> None:
    for title in TITLES:
        cut_title(*title)
    blank_plank()
    kitties_buttons()
    for box, name in SAKURA_BAR_CUTS:
        cut_alpha_piece(SAKURA_BAR_SOURCE, box, name)
    for box, name, min_shape in FLORAL_BAR_CUTS:
        cut_alpha_piece(FLORAL_BAR_SOURCE, box, name, min_shape=min_shape)
    for box, name in FLORAL_FILL_CUTS:
        cut_fill_piece(FLORAL_BAR_SOURCE, FLORAL_FILL_ROW, box, name)
    cut_alpha_piece(LOADING_SOURCE, LOADING_BAR_BOX, "loading_bar", min_shape=200)
    for cut in LOADING_CUTS:
        cut_region(LOADING_SOURCE, *cut)
    cut_alpha_piece(SAKURA_MENU_SOURCE, SAKURA_TITLE_BOX, "title_start_sakura")
    for cut in SHEET_CUTS:
        cut_from_sheet(*cut)
    cat_portraits()
    cut_cat_card(*SAKURA_HUD_CUT)
    # Cats that later got their own sheets: their portrait is that sheet's IDLE FRONT pose instead
    # of the selection-sheet card (Cabage became a cabbage, not the frog hood the card shows).
    for cut in SKIN_SHEET_PORTRAITS:
        cut_from_sheet(*cut)
    complete_looks()


HUD_SOURCE = "hud_source.png"
HUD_CAT_BOX = (30, 90, 252, 310)


def _hud_background(p: tuple) -> bool:
    """The sheet's grey transparency checkerboard and the navy panel behind the head."""
    r, g, b = p[:3]
    checker = max(r, g, b) - min(r, g, b) < 22 and min(r, g, b) > 150
    blue = b > r + 18 and b >= g
    return checker or blue


def _checker_only(p: tuple) -> bool:
    """Only the neutral grey/white checkerboard, for sheets whose art has white and light-blue
    edges (clouds) that the HUD rule would eat."""
    r, g, b = p[:3]
    return max(r, g, b) - min(r, g, b) <= 4 and min(r, g, b) > 200


def _checker_and_glow(p: tuple) -> bool:
    """The checkerboard, also where the painting's pale yellow sparkle glow was laid over it."""
    r, g, b = p[:3]
    grey = max(r, g, b) - min(r, g, b) <= 16 and min(r, g, b) > 170
    glow = min(r, g) > 232 and b > 176
    return grey or glow


PAUSE_SOURCE = "pause_source.png"
CATS_SOURCE = "cats_source.png"
GOLDEN_PACKS_SOURCE = "golden_packs_source.png"
CAT_SKINS = ["fluffy", "shadow", "misty", "sakura", "honey", "pixie", "clover", "snowball",
             "napster", "toffee", "cabage", "sharky"]


def cut_cat_card(box: tuple, name: str, cleared: tuple = ()) -> None:
    """One cat portrait from the selection sheet's 4×3 card grid. The card behind it is a near-flat
    colour (grey, darker when locked; a blue sky on the selected one), so a pixel is background when
    it is close to the card colour sampled from the crop's border (or is sky blue) and connected to
    the border. Only the largest remaining shape is kept, which drops the lock, check mark and sleep
    z's; `cleared` rectangles remove badges that touch the cat. The game draws its own card."""
    im = Image.open(Path(__file__).parent / CATS_SOURCE).convert("RGBA").crop(box)
    w, h = im.size
    px = im.load()
    for x0, y0, x1, y1 in cleared:
        for y in range(y0, min(y1, h)):
            for x in range(x0, min(x1, w)):
                px[x, y] = (0, 0, 0, 0)
    border = sorted(px[x, y][:3] for x in range(w) for y in (0, 1, h - 2, h - 1) if px[x, y][3])
    card = border[len(border) // 2]

    def background(p: tuple) -> bool:
        if p[3] == 0:
            return True
        r, g, b = p[:3]
        sky = b > 150 and b > r + 40 and g > 100
        return sky or sum(abs(p[i] - card[i]) for i in range(3)) < 46

    clear = [[False] * h for _ in range(w)]
    todo = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while todo:
        x, y = todo.pop()
        if clear[x][y] or not background(px[x, y]):
            continue
        clear[x][y] = True
        px[x, y] = (0, 0, 0, 0)
        todo += [(nx, ny) for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
                 if 0 <= nx < w and 0 <= ny < h and not clear[nx][ny]]
    seen, best = set(), []
    for start in ((x, y) for x in range(w) for y in range(h)):
        if start in seen or px[start][3] == 0:
            continue
        shape, stack = [], [start]
        seen.add(start)
        while stack:
            x, y = stack.pop()
            shape.append((x, y))
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= n[0] < w and 0 <= n[1] < h and n not in seen and px[n][3]:
                    seen.add(n)
                    stack.append(n)
        best = max(best, shape, key=len)
    keep = set(best)
    for x in range(w):
        for y in range(h):
            if (x, y) not in keep:
                px[x, y] = (0, 0, 0, 0)
    piece = im.crop(im.getbbox())
    folder = ATLAS.parent / f"{name}.imageset"
    folder.mkdir(parents=True, exist_ok=True)
    write_png(piece, folder / f"{name}.png")
    contents = {"images": [{"filename": f"{name}.png", "idiom": "universal"}], "info": {"author": "xcode", "version": 1}}
    (folder / "Contents.json").write_text(json.dumps(contents, indent=2) + "\n")


SKIN_SHEET_PORTRAITS = [
    ("cabage_source.png", (470, 70, 640, 225), "cat_cabage", _checker_only),
    ("sharky_source.png", (470, 65, 630, 215), "cat_sharky", _checker_only),
]


def cat_portraits() -> None:
    cols = [(60, 236), (276, 452), (492, 668), (708, 884)]
    rows = [(800, 928), (1005, 1133), (1212, 1328)]
    for i, name in enumerate(CAT_SKINS):
        (x0, x1), (y0, y1) = cols[i % 4], rows[i // 4]
        cleared = ()
        if i == 0:                      # the selected card: inside its gold frame, minus the tick
            x0, y0, x1 = x0 + 8, y0 + 8, x1 - 8
            cleared = ((x1 - x0 - 34, 0, x1 - x0, 30),)
        if name in ("cabage", "sharky"):    # the padlock badge in the corner
            cleared = ((x1 - x0 - 36, 0, x1 - x0, 40),)
        cut_cat_card((x0, y0, x1, y1), f"cat_{name}", cleared)

# Sakura's head for the HUD lives panel (Fluffy's is `hud_cat`): her card on the selection sheet,
# down to the bell, minus the tip of her tail below the scarf.
SAKURA_HUD_CUT = ((710, 810, 858, 915), "hud_cat_sakura", ((0, 95, 40, 105),))

# Pieces cut from the user's UI sheets, which sit on a grey transparency checkerboard:
# (source, box in the sheet, asset name[, background rule]).
SHEET_CUTS = [
    (HUD_SOURCE, HUD_CAT_BOX, "hud_cat"),
    ("boss_squirrel_ui_source.png", (338, 6, 1648, 322), "boss_banner_squirrel"),
    ("boss_squirrel_ui_source.png", (48, 672, 350, 836), "boss_crown_squirrel"),
    # The pause panel (cat, clouds, leaves, PAUSED, both buttons, the grassy base). The buttons are
    # part of the picture; the game lays its touch areas over them.
    (PAUSE_SOURCE, (20, 120, 712, 880), "pause_panel", _checker_only),
    (PAUSE_SOURCE, (728, 258, 1116, 378), "pause_resume", _checker_only),
    (PAUSE_SOURCE, (1130, 258, 1516, 378), "pause_resume_pressed", _checker_only),
    (PAUSE_SOURCE, (728, 414, 1116, 534), "pause_quit", _checker_only),
    (PAUSE_SOURCE, (1130, 414, 1516, 534), "pause_quit_pressed", _checker_only),
    # The golden fish packs: only the picture above each painted price bar. The game draws the bar
    # itself, because the price must be the App Store's, in the player's currency.
    (GOLDEN_PACKS_SOURCE, (140, 60, 720, 314), "golden_pack_50", _checker_and_glow, 80),
    (GOLDEN_PACKS_SOURCE, (815, 25, 1400, 314), "golden_pack_150", _checker_and_glow, 80),
    (GOLDEN_PACKS_SOURCE, (140, 490, 720, 824), "golden_pack_350", _checker_and_glow, 80),
    (GOLDEN_PACKS_SOURCE, (815, 480, 1410, 824), "golden_pack_800", _checker_and_glow, 80),
]


def cut_from_sheet(source: str, box: tuple, name: str, background=None, keep_min: int = 0) -> None:
    """One piece from a user UI sheet, like the titles: the checkerboard (and any navy panel behind
    the piece) is flood-filled away from the edges, stopped by the art's outline, then only the
    largest connected shape is kept, which drops stray specks. With `keep_min`, every shape of at
    least that many pixels is kept instead (sparkles floating around the piece)."""
    im = Image.open(Path(__file__).parent / source).convert("RGBA").crop(box)
    w, h = im.size
    px = im.load()
    clear = [[False] * h for _ in range(w)]
    todo = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while todo:
        x, y = todo.pop()
        if clear[x][y] or not (background or _hud_background)(px[x, y]):
            continue
        clear[x][y] = True
        px[x, y] = (0, 0, 0, 0)
        todo += [(nx, ny) for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
                 if 0 <= nx < w and 0 <= ny < h and not clear[nx][ny]]
    seen, best, kept = set(), [], []
    for start in ((x, y) for x in range(w) for y in range(h)):
        if start in seen or px[start][3] == 0:
            continue
        shape, stack = [], [start]
        seen.add(start)
        while stack:
            x, y = stack.pop()
            shape.append((x, y))
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= n[0] < w and 0 <= n[1] < h and n not in seen and px[n][3]:
                    seen.add(n)
                    stack.append(n)
        best = max(best, shape, key=len)
        if keep_min and len(shape) >= keep_min:
            kept += shape
    keep = set(kept or best)
    for x in range(w):
        for y in range(h):
            if (x, y) not in keep:
                px[x, y] = (0, 0, 0, 0)
    piece = im.crop(im.getbbox())
    folder = ATLAS.parent / f"{name}.imageset"
    folder.mkdir(parents=True, exist_ok=True)
    write_png(piece, folder / f"{name}.png")
    contents = {"images": [{"filename": f"{name}.png", "idiom": "universal"}], "info": {"author": "xcode", "version": 1}}
    (folder / "Contents.json").write_text(json.dumps(contents, indent=2) + "\n")


# Each world's own level-complete screen (`CompleteLook` in App/UI/ResultView.swift), from the user's paintings: one
# sheet per level theme with the title, the world's boss, the score card's frame, the NEXT LEVEL / RETRY / MENU
# buttons and loose decorations. The sheets have real transparency (the blurred backdrop under the clear pixels is
# dropped by the alpha threshold). Painted sample text is taken out (`COMPLETE_BLANKS`): the card's stars, score,
# level name and fish and the buttons' labels and icons, which the game draws itself from Lore.json.
COMPLETE_SOURCES = {"frost": "frost_complete_source.png", "haunted": "haunted_complete_source.png",
                    "citadel": "citadel_complete_source.png"}


def _cream(p: tuple) -> bool:
    return p[0] > 225 and p[1] > 195 and p[2] > 140 and p[0] - p[2] > 25


def _pale(p: tuple) -> bool:
    return min(p[:3]) > 200


def _orange(p: tuple) -> bool:
    return p[0] > 200 and 90 < p[1] < 215 and p[2] < 110


# (theme, box to fill in the sheet, fill colour test). Each row of a box is refilled with the paint either side of
# it (`blank_box`), so the parchment's and the buttons' shading carries on under where the lettering was.
COMPLETE_BLANKS = [
    ("frost", (128, 615, 626, 958), _cream),        # card: stars, SCORE, BEST, level name, fish
    ("frost", (190, 955, 515, 991), _cream),        # card: NEW ABILITY (crystals reach in either side of it)
    ("frost", (505, 1090, 950, 1168), _orange),     # NEXT LEVEL ▷
    ("frost", (212, 1232, 448, 1305), _cream),      # RETRY ↻
    ("frost", (638, 1232, 842, 1305), _cream),      # ⌂ MENU
    ("haunted", (108, 558, 512, 862), _cream),
    ("haunted", (148, 862, 456, 912), _cream),
    ("haunted", (205, 1094, 584, 1154), _orange),
    ("haunted", (122, 1246, 314, 1307), _cream),
    ("haunted", (442, 1246, 626, 1307), _cream),
    ("citadel", (130, 618, 492, 744), _cream),      # the stars, between the card's two banners
    ("citadel", (104, 744, 512, 925), _cream),
    ("citadel", (160, 925, 456, 972), _cream),
    ("citadel", (240, 1105, 690, 1192), _orange),
    ("citadel", (120, 1266, 308, 1333), _pale),     # the steam buttons' fill is nearly white
    ("citadel", (450, 1266, 648, 1333), _pale),
]


def blank_box(px, box: tuple, fill) -> None:
    """Paints over `box` (sheet pixels) with the colour either side of it: each row runs from the mean of the
    `fill`-coloured pixels just left of the box to that of those just right of it (over the row and three either
    side, so one row's highlight does not show as a line). A side with no such pixels (a crystal reaching in) takes
    the other's colour; a row with none at all, the row above's."""
    x0, y0, x1, y1 = box

    def mean(xs, y):
        near = [px[x, yy][:3] for yy in range(y - 3, y + 4) for x in xs if fill(px[x, yy])]
        return tuple(sum(c[i] for c in near) / len(near) for i in range(3)) if near else None

    rows = []
    for y in range(y0, y1):
        left, right = mean(range(x0 - 10, x0), y), mean(range(x1, x1 + 10), y)
        rows.append((left or right, right or left))
    known = [row for row in rows if row[0]]
    last = known[0]
    for y in range(y0, y1):
        left, right = rows[y - y0] if rows[y - y0][0] else last
        last = (left, right)
        for x in range(x0, x1):
            t = (x - x0) / max(1, x1 - x0 - 1)
            px[x, y] = tuple(round(left[i] + (right[i] - left[i]) * t) for i in range(3)) + (255,)


def complete_sheet(theme: str) -> Image.Image:
    """The theme's painting with its sample text and labels painted out."""
    sheet = Image.open(Path(__file__).parent / COMPLETE_SOURCES[theme]).convert("RGBA")
    px = sheet.load()
    for blank_theme, box, fill in COMPLETE_BLANKS:
        if blank_theme == theme:
            blank_box(px, box, fill)
    if theme == "citadel":
        steamless_card_foot(px)
    return sheet


def _puff(p: tuple) -> bool:
    """The steam world's pink steam, lit orange by the lamps: warmer than the purple-grey iron and bluer than its
    rust (the parchment's cream, as warm, is left out by where it is: `CARD_PARCHMENT`)."""
    r, g, b = p[:3]
    return r > 150 and g > 95 and b > 70 and 25 <= r - g <= 150


# The steam card's bottom corners, which steam puffs cover (sheet pixels): the right corner, where the frame shows
# most, the parchment inside the frame (not steam however warm), and the line the card is symmetric about
# (x' = CARD_MIRROR - x).
CARD_FOOT, CARD_PARCHMENT, CARD_MIRROR = (423, 880, 613, 1060), (104, 618, 534, 992), 623
# How far left of hidden frame the frame it is rebuilt from lies: the bottom bar, with a bolt, runs on under the steam.
CARD_BAR_REPEAT, CARD_BAR_TOP = 60, 992


def steamless_card_foot(px) -> None:
    """Takes the steam off the steam card's bottom corners. In the right corner, steam between two bits of frame on
    a row of the bottom bar (from `CARD_BAR_TOP` down, with no gap between) is frame hidden behind steam, rebuilt
    from the frame `CARD_BAR_REPEAT` pixels left of it (the bar runs along the row); the rest of the steam is
    cleared. The left corner, more hidden, becomes the mirror image of the right one."""
    x0, y0, x1, y1 = CARD_FOOT
    px0, py0, px1, py1 = CARD_PARCHMENT
    for y in range(y0, y1):
        x = x0
        while x < x1:
            if px[x, y][3] < 200:
                x += 1
                continue
            end = x
            while end < x1 and px[end, y][3] >= 200:
                end += 1
            run = range(x, end)
            steam = {i for i in run if _puff(px[i, y]) and not (px0 <= i < px1 and py0 <= y < py1)}
            frame = [i for i in run if i not in steam]
            for i in run:
                if i in steam:
                    hidden = y >= CARD_BAR_TOP and frame and frame[0] < i < frame[-1]
                    px[i, y] = px[i - CARD_BAR_REPEAT, y] if hidden else (0, 0, 0, 0)
            x = end
        for x in range(CARD_MIRROR - x1 + 1, CARD_MIRROR - x0 + 1):
            px[x, y] = px[CARD_MIRROR - x, y]


def _smoke(p: tuple, q: tuple) -> bool:
    """A pixel of a soft steam puff, reached from its neighbour `q`: not an outline (dark) and close to `q` (the
    puffs are smooth; the art has hard edges)."""
    return sum(p[:3]) > 300 and sum(abs(p[i] - q[i]) for i in range(3)) < 40


def cut_painted(sheet: Image.Image, box: tuple, name: str, alpha: int = 200, haze=None, keep_min: int = 0,
                cleared: tuple = (), mirror_from: int | None = None) -> tuple:
    """One piece of a painting with real transparency: pixels under `alpha` cleared and the rest made opaque; with
    `haze`, soft painted smoke reached from the clear pixels through `haze(pixel, neighbour)` cleared too, stopped by
    the art's outlines; `cleared` rectangles (box pixels) cleared by hand. Only the largest shape is kept (the boxes
    catch a neighbour's tips), with `keep_min` every shape of at least that size. With `mirror_from` (a sheet x), the
    piece is made symmetric: what lies right of that line, and its mirror image on the left. Trimmed; returns the
    trimmed box in sheet pixels (before mirroring). A regular image, outside the atlas."""
    im = sheet.crop(box)
    w, h = im.size
    px = im.load()
    for x0, y0, x1, y1 in cleared:
        for y in range(max(0, y0), min(y1, h)):
            for x in range(max(0, x0), min(x1, w)):
                px[x, y] = (0, 0, 0, 0)
    original = im.copy().load()
    clear = bytearray(w * h)
    todo = []
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a >= alpha:
                px[x, y] = (r, g, b, 255)
            else:
                px[x, y] = (0, 0, 0, 0)
                clear[y * w + x] = 1
                todo.append((x, y))
    if haze:
        while todo:
            x, y = todo.pop()
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < w and 0 <= ny < h and not clear[ny * w + nx] and haze(original[nx, ny], original[x, y]):
                    clear[ny * w + nx] = 1
                    px[nx, ny] = (0, 0, 0, 0)
                    todo.append((nx, ny))
    seen, best, kept = bytearray(w * h), [], []
    for sy in range(h):
        for sx in range(w):
            if seen[sy * w + sx] or px[sx, sy][3] == 0:
                continue
            shape, stack = [], [(sx, sy)]
            seen[sy * w + sx] = 1
            while stack:
                x, y = stack.pop()
                shape.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and px[nx, ny][3]:
                        seen[ny * w + nx] = 1
                        stack.append((nx, ny))
            best = max(best, shape, key=len)
            if keep_min and len(shape) >= keep_min:
                kept += shape
    keep = set(kept or best)
    for y in range(h):
        for x in range(w):
            if px[x, y][3] and (x, y) not in keep:
                px[x, y] = (0, 0, 0, 0)
    bbox = im.getbbox()
    piece = im.crop(bbox)
    if mirror_from is not None:
        right = piece.crop((mirror_from - box[0] - bbox[0], 0, piece.width, piece.height))
        piece = Image.new("RGBA", (right.width * 2, right.height), (0, 0, 0, 0))
        piece.paste(ImageOps.mirror(right), (0, 0))
        piece.paste(right, (right.width, 0))
    _write_image(piece, name)
    return (box[0] + bbox[0], box[1] + bbox[1], box[0] + bbox[2], box[1] + bbox[3])


def _write_image(image: Image.Image, name: str) -> None:
    folder = ATLAS.parent / f"{name}.imageset"
    folder.mkdir(parents=True, exist_ok=True)
    write_png(image, folder / f"{name}.png")
    contents = {"images": [{"filename": f"{name}.png", "idiom": "universal"}], "info": {"author": "xcode", "version": 1}}
    (folder / "Contents.json").write_text(json.dumps(contents, indent=2) + "\n")


# (theme, box in the sheet, piece, cut options). Pieces are named `<piece>_complete_<theme>`; the Swift side
# (`CompleteLook`) knows where each card's parchment and each button's label sit in the trimmed pieces.
COMPLETE_CUTS = [
    ("frost", (22, 10, 555, 465), "title", {}),
    ("frost", (467, 20, 1013, 568), "boss", {}),
    ("frost", (13, 454, 745, 1127), "card", {}),
    ("frost", (385, 1046, 1014, 1222), "next", {}),
    ("frost", (104, 1205, 526, 1347), "retry", {}),
    ("frost", (555, 1206, 921, 1340), "menu", {}),
    ("frost", (774, 590, 874, 702), "flake", {}),
    ("frost", (920, 593, 971, 696), "crystal", {}),
    ("haunted", (12, 21, 625, 426), "title", {}),
    ("haunted", (596, 25, 1007, 619), "boss", {}),
    ("haunted", (9, 386, 631, 1021), "card", {}),
    ("haunted", (15, 1034, 710, 1200), "next", {}),
    ("haunted", (24, 1216, 375, 1329), "retry", {}),
    ("haunted", (388, 1216, 704, 1329), "menu", {}),
    ("haunted", (885, 1050, 1009, 1180), "ghost", {}),
    ("haunted", (843, 1207, 902, 1316), "flame", {}),
    # The steam world's pieces are wrapped in soft steam puffs, cleared with `_smoke`.
    ("citadel", (13, 20, 600, 470), "title", {"haze": _smoke}),
    # The Mecha-Mouser on the top of its castle wall: the towers left of it and the steam under the wall cut away.
    ("citadel", (520, 20, 1013, 662), "boss", {"haze": _smoke, "cleared": ((0, 380, 82, 642),)}),
    ("citadel", (13, 470, 612, 1060), "card", {"haze": _smoke, "cleared": ((552, 0, 599, 83), (592, 83, 599, 245))}),
    # A cheering cat (not the player's) sits on the NEXT LEVEL plank's left end: the right half is mirrored over it.
    ("citadel", (20, 1040, 770, 1235), "next", {"haze": _smoke, "mirror_from": 440}),
    ("citadel", (33, 1244, 381, 1365), "retry", {"haze": _smoke}),
    ("citadel", (390, 1244, 721, 1365), "menu", {"haze": _smoke}),
]


def complete_looks() -> None:
    sheets = {}
    for theme, box, piece, options in COMPLETE_CUTS:
        if theme not in sheets:
            sheets[theme] = complete_sheet(theme)
        cut_painted(sheets[theme], box, f"{piece}_complete_{theme}", **options)


def contact_sheet(sprites: list[Sprite], path: Path, scale: int = 4) -> None:
    """One PNG with every animation of the given sprites as labelled rows, for quick review. Sprites
    exported at more than 1x (`Sprite.scale`) are shown at their own pixels, enlarged by `scale // sprite.scale`."""
    rows = [(s, name) for s in sprites for name in s.anims]

    def k(s: Sprite) -> int:
        return s.scale * max(1, scale // s.scale)
    width = max(s.size[0] * len(s.anims[name].frames) * k(s) for s, name in rows)
    height = sum(s.size[1] * k(s) for s, _ in rows)
    out = Image.new("RGBA", (width, height), PREVIEW_BG)
    y = 0
    for sprite, name in rows:
        strip = sheet(frames_of(sprite, name))
        grow = k(sprite) // sprite.scale
        out.alpha_composite(strip.resize((strip.width * grow, strip.height * grow), Image.NEAREST), (0, y))
        y += sprite.size[1] * k(sprite)
    write_png(out, path)
