"""Data model shared by character modules and the exporter."""
from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image


@dataclass
class Anim:
    frames: list[Image.Image]
    fps: int = 10
    loop: bool = True


@dataclass
class Sprite:
    name: str
    size: tuple[int, int]
    anims: dict[str, Anim] = field(default_factory=dict)
    # Characters are drawn facing right; enemies are mirrored on export so they face the hero.
    faces_left: bool = False
    # Where the figure stands inside the frame: x of its centre and y of its lowest pixel row.
    # None means horizontally centred / sitting on the bottom edge.
    cx: float | None = None
    ground: int | None = None
    # Pixels per point in the exported PNGs. 1 for drawn pixel art; painted sprites cut from a user's sheet
    # (`sheet_hero.py`) keep 3× detail: their frames are `size` × `scale` pixels, still `size` points in game.
    scale: int = 1

    def add(self, name: str, frames: list, fps: int = 10, loop: bool = True) -> None:
        images = [f.img if hasattr(f, "img") else f for f in frames]
        expected = (self.size[0] * self.scale, self.size[1] * self.scale)
        for image in images:
            if image.size != expected:
                raise ValueError(f"{self.name}/{name}: frame is {image.size}, expected {expected}")
        self.anims[name] = Anim(images, fps, loop)


def single(name: str, canvas, anim: str = "still", fps: int = 1, **kwargs) -> Sprite:
    """A sprite with one one-frame animation (props, tiles, icons)."""
    image = canvas.img if hasattr(canvas, "img") else canvas
    sprite = Sprite(name, image.size, **kwargs)
    sprite.add(anim, [image], fps=fps)
    return sprite
