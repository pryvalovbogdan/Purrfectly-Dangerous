"""The Rolling Onigiri enemy, cut from the user's painted sheet (`sheet_hero.py`) instead of drawn in code.

Source: `docs/concept/Rolling Onigiri Enemy Sheet.png`, copied to `Tools/sprites/rolling_onigiri_source.png`, painted
(roughly) to `docs/enemy-sheet-brief-sakura.md` on real transparency: a semi-transparent pink haze (its clear pixels
carry a bright red that the export drops with the alpha), the rice, nori and dark outline nearly opaque. Replaces the
code-drawn `rolling_onigiri` (`sakura_critters.py` skips the sprites in `NAMES`). Same sprite name, animation names,
loop flags, frame size (44×28 points), anchor (`cx` 22, `ground` 25) and `faces_left` (painted facing right,
mirrored on export); frames at 3x detail.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image

from sheet_hero import Cat, HeroSheet, Row
from sprite import Sprite

SIZE = (44, 28)                   # points, as the code-drawn onigiri
CX, GROUND = 22, 25               # its lowest pixel (the outline) on row 26, as the code-drawn one
SCALE = 3


def _effect(rgb: tuple) -> bool:
    """The swooshes, speed streaks and bursts: pink, magenta or a pinkish white (blue at least green). The rice is a
    warm cream (blue under green) and the nori and outline dark, so they wall the fill off from the body."""
    r, g, b = rgb
    return r > 150 and b >= g


@dataclass
class OnigiriSheet(HeroSheet):
    """`HeroSheet` that also clears what trails behind the onigiri in the rows in `swept` (the swoosh arcs of the
    roll): a fill from the cut-out's left edge through the effect's colours
    (`_effect`) and clear pixels, in its trailing part (left of `reach` of its width), stopped by the rice and the
    dark nori and outline, so the body stays. The figure is then cropped again."""
    swept: dict = field(default_factory=dict)     # row -> (how far across (0..1) the fill may go, frame indices)

    def _cut_row(self, name: str, row: Row) -> list[Cat]:
        cats = super()._cut_row(name, row)
        if name in self.swept:
            reach, which = self.swept[name]
            for i in which:
                _sweep(cats[i], reach)
        return cats


def _sweep(cat: Cat, reach: float) -> None:
    im = cat.image
    w, h = im.size
    px = im.load()
    limit = round(w * reach)
    todo = [(0, y) for y in range(h)] + [(x, y) for x in range(limit) for y in (0, h - 1)]
    seen = set()
    while todo:
        x, y = todo.pop()
        if (x, y) in seen or not (0 <= x < limit and 0 <= y < h):
            continue
        seen.add((x, y))
        if px[x, y][3] and not _effect(px[x, y][:3]):
            continue
        px[x, y] = (0, 0, 0, 0)
        todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    _keep_largest(im)
    left, top, right, bottom = im.getchannel("A").getbbox()
    cat.image = im.crop((left, top, right, bottom))
    x0, y0 = cat.box[:2]
    cat.box = (x0 + left, y0 + top, x0 + right, y0 + bottom)
    cat.front -= left


def _keep_largest(im: Image.Image) -> None:
    """Clear every piece but the largest (bits of a streak cut loose from the body)."""
    w, h = im.size
    px = im.load()
    seen, pieces = set(), []
    for sy in range(h):
        for sx in range(w):
            if (sx, sy) in seen or not px[sx, sy][3]:
                continue
            piece, todo = [], [(sx, sy)]
            seen.add((sx, sy))
            while todo:
                x, y = todo.pop()
                piece.append((x, y))
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen and px[nx, ny][3]:
                        seen.add((nx, ny))
                        todo.append((nx, ny))
            pieces.append(piece)
    pieces.sort(key=len, reverse=True)
    for piece in pieces[1:]:
        for x, y in piece:
            px[x, y] = (0, 0, 0, 0)


# Rows as painted (counts are the onigiri painted; ROLL is labelled 10). Boxes hold the figures, clear of the label
# pills. DUST TRAIL is not used by the game and not cut.
SHEET = OnigiriSheet(
    source="rolling_onigiri_source.png",
    rows={
        "idle": Row((15, 52, 960, 160), 6, align="body"),
        # One full turn: upright (1), tipping (2), the ball turning (3-9), upright again (10-11): it loops.
        "roll": Row((15, 222, 1774, 345), 11, align=False),                    # labelled 10
        # The charge: the speed streaks are painted over the back of the nori, so a fill would leave holes; they are
        # cut off at the nori's back instead (what lies over the body stays). Frame 4 keeps its blossom burst whole.
        "attack": Row((15, 408, 1280, 530), 6, trim_left={0: 64, 1: 257, 2: 476, 4: 900, 5: 1128}),
        "hurt": Row((15, 592, 650, 718), 4),
        # Squashed, burst, then a pile of rice and petals: each frame centred on its own.
        "death": Row((660, 592, 1774, 718), 6, align=False),
    },
    frame=(SIZE[0], SIZE[1] - 1), cx=CX, scale=SCALE, alpha=200, core=220, min_area=1500,
    # About 0.21 points per sheet pixel: the painted onigiri (about 112×91 px sitting) covers about as much as the
    # code-drawn one did (about 316 square points).
    max_scale=0.63,
    size_to="idle", size_skip=("death",),
    swept={"roll": (0.5, range(2, 9))},          # the swoosh arcs behind the turning ball (frames 3-9)
)

# Animation -> painted row (every frame, in order), fps, loop (the code-drawn onigiri's loop flags).
PLAN = {
    "idle": ("idle", 6, True),            # 6 frames: 1 s a loop
    "roll": ("roll", 18, True),           # 11: 0.61 s a turn; played from the start on `curled` (the curl-up), then held
    "attack": ("attack", 16, False),      # 6: 0.38 s (only a fallback for `roll` in GameScene)
    "hurt": ("hurt", 12, False),          # 4: 0.33 s
    "death": ("death", 10, False),        # 6: 0.6 s, ends on the pile of rice
}

NAMES = {"rolling_onigiri"}


def onigiri() -> Sprite:
    sheet = SHEET
    used = sorted((row, i) for row, _, _ in PLAN.values() for i in range(sheet.rows[row].count))
    cut = sheet.frames(used)
    sprite = Sprite("rolling_onigiri", SIZE, faces_left=True, cx=CX, ground=GROUND, scale=SCALE)
    for anim, (row, fps, loop) in PLAN.items():
        frames = []
        for i in range(sheet.rows[row].count):
            frame = Image.new("RGBA", (SIZE[0] * SCALE, SIZE[1] * SCALE), (0, 0, 0, 0))
            frame.paste(cut[(row, i)], (0, 0))
            frames.append(frame)
        sprite.add(anim, frames, fps=fps, loop=loop)
    return sprite


def build() -> list[Sprite]:
    return [onigiri()]
