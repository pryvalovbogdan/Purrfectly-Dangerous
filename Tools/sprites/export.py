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


def write_atlas_image(image: Image.Image, name: str) -> None:
    folder = ATLAS / f"{name}.imageset"
    write_png(image, folder / f"{name}.png")
    contents = {"images": [{"filename": f"{name}.png", "idiom": "universal", "scale": "1x"}],
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
        for stale in ATLAS.glob(f"{sprite.name}_*.imageset"):
            # Guard against prefixes: "hero" must not delete "hero_x" sprites of another name.
            if stale.stem.rsplit("_", 2)[0] == sprite.name:
                shutil.rmtree(stale)
        w, h = sprite.size
        anchor_x = 0.5 if sprite.cx is None else (sprite.cx + 0.5) / w
        entry = {"width": w, "height": h,
                 # Anchor of the figure inside the frame, as SpriteKit wants it (origin bottom-left).
                 "anchorX": round(1 - anchor_x if sprite.faces_left else anchor_x, 4),
                 "anchorY": 0 if sprite.ground is None else round((h - 1 - sprite.ground) / h, 4),
                 "animations": {}}
        for anim_name, anim in sprite.anims.items():
            frames = frames_of(sprite, anim_name)
            for index, frame in enumerate(frames):
                write_atlas_image(frame, frame_name(sprite.name, anim_name, index))
            write_png(sheet(frames), OUT / "sheets" / f"{sprite.name}_{anim_name}.png")
            scale = max(1, min(8, 256 // max(sprite.size)))
            write_gif(frames, anim.fps, OUT / "preview" / f"{sprite.name}_{anim_name}.gif", scale)
            entry["animations"][anim_name] = {"frames": len(frames), "fps": anim.fps, "loop": anim.loop}
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


def titles() -> None:
    for title in TITLES:
        cut_title(*title)
    for cut in SHEET_CUTS:
        cut_from_sheet(*cut)


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


PAUSE_SOURCE = "pause_source.png"

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
]


def cut_from_sheet(source: str, box: tuple, name: str, background=None) -> None:
    """One piece from a user UI sheet, like the titles: the checkerboard (and any navy panel behind
    the piece) is flood-filled away from the edges, stopped by the art's outline, then only the
    largest connected shape is kept, which drops stray specks."""
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


def contact_sheet(sprites: list[Sprite], path: Path, scale: int = 4) -> None:
    """One PNG with every animation of the given sprites as labelled rows, for quick review."""
    rows = [(s, name) for s in sprites for name in s.anims]
    width = max(s.size[0] * len(s.anims[name].frames) for s, name in rows) * scale
    height = sum(s.size[1] for s, _ in rows) * scale
    out = Image.new("RGBA", (width, height), PREVIEW_BG)
    y = 0
    for sprite, name in rows:
        strip = sheet(frames_of(sprite, name))
        out.alpha_composite(strip.resize((strip.width * scale, strip.height * scale), Image.NEAREST), (0, y))
        y += sprite.size[1] * scale
    write_png(out, path)
