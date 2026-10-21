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
