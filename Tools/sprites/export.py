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
        if sprite.scale != 1:
            entry["scale"] = sprite.scale
        for anim_name, anim in sprite.anims.items():
            frames = frames_of(sprite, anim_name)
            for index, frame in enumerate(frames):
                write_atlas_image(frame, frame_name(sprite.name, anim_name, index), sprite.scale)
            write_png(sheet(frames), OUT / "sheets" / f"{sprite.name}_{anim_name}.png")
            scale = max(1, min(8, 256 // max(sprite.size)) // sprite.scale)
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
# the fill by where the plaque and the track sit in them (`SakuraBossHealth` in App/UI/HUDPanels.swift).
SAKURA_BAR_SOURCE = "sakura_boss_bar_source.png"
SAKURA_BAR_CUTS = [
    ((95, 25, 1435, 232), "boss_plate_sakura"),            # name plaque; text area x 305-1035, y 73-175
    ((60, 240, 1480, 375), "boss_bar_frame_sakura"),       # bar frame; track x 165-1240, y 40-90
    ((186, 397, 222, 461), "boss_bar_fill_sakura_left"),   # the red fill's rounded ends and a middle slice
    ((700, 397, 708, 461), "boss_bar_fill_sakura_mid"),
    ((1315, 397, 1351, 461), "boss_bar_fill_sakura_right"),
]


def cut_alpha_piece(source: str, box: tuple, name: str, alpha: int = 200) -> None:
    """One piece of a painting with real transparency: pixels under `alpha` (the soft haze) cleared, the rest
    made fully opaque, and loose specks smaller than 40 pixels dropped. A regular image, outside the atlas."""
    im = Image.open(Path(__file__).parent / source).convert("RGBA").crop(box)
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
        if len(shape) < 40:
            for p in shape:
                px[p] = (0, 0, 0, 0)
    folder = ATLAS.parent / f"{name}.imageset"
    folder.mkdir(parents=True, exist_ok=True)
    write_png(im, folder / f"{name}.png")
    contents = {"images": [{"filename": f"{name}.png", "idiom": "universal"}],
                "info": {"author": "xcode", "version": 1}}
    (folder / "Contents.json").write_text(json.dumps(contents, indent=2) + "\n")


def titles() -> None:
    for title in TITLES:
        cut_title(*title)
    blank_plank()
    for box, name in SAKURA_BAR_CUTS:
        cut_alpha_piece(SAKURA_BAR_SOURCE, box, name)
    for cut in SHEET_CUTS:
        cut_from_sheet(*cut)
    cat_portraits()
    # Cats that later got their own sheets: their portrait is that sheet's IDLE FRONT pose instead
    # of the selection-sheet card (Cabage became a cabbage, not the frog hood the card shows).
    for cut in SKIN_SHEET_PORTRAITS:
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
