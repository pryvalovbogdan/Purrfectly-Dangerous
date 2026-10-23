# Hero sprite sheet brief (for any cat)

A brief for the artist painting a playable cat for **Purrfectly Dangerous**, a 2D pixel-art
auto-runner for iPhone. Each cat is one painted sprite sheet. The game's build cuts the sheet into
animation frames automatically (`Tools/sprites/sheet_hero.py`), so the sheet must follow the rules below
exactly. Frame counts, speeds and loops are what the game plays. A missing or miscounted row means the
game has to fake that animation from other frames.

## What to deliver

- **Two sheets per cat**, because there are about 100 frames:
  - `<Cat name> Hero Sheet A.png`: movement and actions: IDLE, RUN, STOP, JUMP, FALL, DOUBLE JUMP, THROW,
    DASH, POUNCE.
  - `<Cat name> Hero Sheet B.png`: reactions and menus: HURT, DEATH, KO, GHOST, MENU, SIT HAPPY, CHEER,
    PEEK, and the effects row.
- **PNG, about 2560×1600 each (larger is fine)**, with a **real transparent background** (see Sheet
  rules).
- **Cat size:** about **90–110 px tall standing**, the same on every sheet. All cats appear at the same
  size in the game, so a cat painted smaller ends up smaller on screen.

## Smooth motion

Each animation lasts the same time in the game as before, but it now has more frames, so the motion
is smooth instead of jumping between a few poses. That means:

- **Paint in-betweens.** Each frame is a small step from the one before it: a paw moves a little, the
  tail swings a little further. No two neighbouring frames should look like different poses.
- **Looping rows must close the loop.** The last frame leads straight back into the first (RUN, IDLE,
  MENU, SIT HAPPY, GHOST, KO, DASH, JUMP, FALL, DOUBLE JUMP).
- **Follow-through:** the ears, scarf and tail lag a frame or two behind the body and keep swinging when
  it stops. This sells the motion more than anything else.
- **Steady spacing:** in a cycle (run, flip), move by about the same amount every frame. Bunch frames
  close together only where the motion eases in or out (the start of a wind-up, a landing).
- **Keep the volume:** the cat must not grow or shrink between frames. Squash on a landing and stretch
  on a leap are welcome, but they come back to the same size.

## Sheet rules

- **Export as a PNG with a real transparent background.** A checkerboard painted into the picture is
  not transparency: the cutter then has to guess which light pixels are background and which are white
  fur, and eats fur or leaves specks. To check, open the PNG over a dark background: the squares must
  disappear. If the tool can't export transparency, use one flat colour that never appears on the cat
  (pure green `#00FF00` or dark navy), never a checkerboard or gradient.
- **The cat is fully opaque with a dark outline all round**, including the ghost. Glow may be soft, but
  it must not touch or join two frames.
- **One row per animation**, frames left to right in playing order, the label above or beside the row
  (never touching a cat). Several short rows may share a line if there is a clear gap between them.
  A long row (RUN, DEATH) may wrap onto a second line directly below it; label the second line
  "RUN (cont.)" and keep the same order.
- **The number of cats in a row must equal the frame count in the table.** No extra or missing frames.
- **The cat faces right** in every frame.
- **At least ~20 px of empty space** between frames.
- **Same scale in every frame of every row.** The widest frame sets the size of all of them, so keep
  run, dash and pounce no wider than about 1.6× the standing width.
- **Grounded rows:** all paws on one baseline. **Airborne rows:** paint a soft ground shadow under the
  cat so the ground line is known; the cutter removes it.
- **Both eyes open** in every frame unless the table says otherwise. The only blinks are in IDLE and
  MENU (the eyes closing over two frames and opening over two).
- **Effects** (petals, sparkles, swirls, speed lines, trails) go in their own row at the bottom, never
  touching the cat. Small loose specks near the cat are dropped by the cutter.
- **Don't paint the yarn ball** — the game draws the shot itself.

## The cat

Every cat is a small chibi kitten hero: a big head, a short body, a tail, and a scarf or short cape
round its neck that flutters when it moves. Keep the proportions and the outline weight the same for
every cat, so the whole cast reads as one family. Use the cat's portrait on the CATS screen
(`App/Resources/Assets.xcassets/cat_<id>.imageset`) as the look to match.

| Cat (id) | In the game's words | Colours |
|---|---|---|
| Fluffy (`fluffy`) | A ginger furball with more courage than sense. | Orange tabby, white muzzle, chest and paws |
| Shadow (`shadow`) | Black as midnight and twice as quiet. | Black fur, green eyes |
| Misty (`misty`) | A soft grey cat who seems to drift rather than run. | Grey fur, blue scarf |
| Sakura (`sakura`) | Pink as spring blossom, quick as a falling petal. | White and pink fur, blossom by the ear, pink scarf, gold bell |
| Honey (`honey`) | Golden coat, sweet face, sharp claws. | Cream fur, gold scarf |
| Pixie (`pixie`) | Tiny, sparkly and impossible to catch. | Pale fur, purple scarf, violet eyes |
| Clover (`clover`) | Lucky green ribbon, luckier landings. | Orange tabby, green ribbon/scarf |
| Snowball (`snowball`) | Pure white fluff that never minds the cold. | White fur, blue scarf, blue eyes |
| Napster (`napster`) | Mostly asleep, but terrifying when awake. | Warm grey fur, brown scarf |
| Toffee (`toffee`) | A caramel cat with a sticky habit of winning. | Calico with a dark patch over one ear, brown scarf |
| Cabage (`cabage`) | Leafy hood, green thumbs and a crunchy attitude. | Calico kitten in a whole cabbage onesie with a leafy hood |
| Sharky (`sharky`) | Wears a shark suit. Nobody has asked why. | Calico kitten in a whole shark onesie, face in the shark's mouth |

## Animations

| # | Row | Frames | Speed | Loops | Lasts | When the game plays it | What the frames show |
|---|---|---|---|---|---|---|---|
| 1 | IDLE | 8 | 8 fps | yes | 1 s | Standing still after a win; fallback in menus | Standing on all fours, breathing: chest and back rise over frames 1–3 and settle over 4–5, the tail sways through all 8. **Blink:** eyes half-closed in 6, closed in 7, half-open in 8 |
| 2 | RUN | 12 | 20 fps | yes | 0.6 s per cycle | Running on the ground — most of the game | One full gallop: front paws land (1), body compresses (2–3), back paws pass under (4–5), push off (6), all paws off the ground (7); then the same with the other paw leading (8–12). Frame 12 leads back into 1. Ears, scarf and tail bounce a beat behind the body. Eyes open |
| 3 | STOP | 6 | 15 fps | no | 0.4 s | Level won: skids to a halt, then idle | Front paws braking, leaning back (1–2), sliding (3–4), settling (5), standing (6, the same as IDLE 1) |
| 4 | JUMP | 4 | 12 fps | yes | 0.33 s per loop | Rising after a jump | Leaping up: front paws tucked, back legs stretched behind, scarf trailing down; the 4 frames flutter the scarf, ears and tail |
| 5 | FALL | 4 | 12 fps | yes | 0.33 s per loop | Coming down | Front paws reaching down for the landing, back legs forward, scarf and ears blown up; the 4 frames flutter them |
| 6 | DOUBLE JUMP | 8 | 24 fps | yes | 0.33 s per flip | Rising after the second jump (Double Pounce) | **A full forward flip**, curled up, turning 45° per frame: 0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°. Frame 8 leads back into 1 |
| 7 | THROW (yarn shot) | 6 | 24 fps | no | 0.25 s | Every yarn shot, on the ground or in the air | Front paw pulled back (1–2), swinging forward (3), paw fully forward, mouth open — the release (4), follow-through (5), back to running (6). No yarn ball. Keep the back legs in a running pose |
| 8 | DASH (Ghost Dash) | 6 | 18 fps | yes | 0.33 s | Ghost Dash | Low, stretched, very fast pose, ears flat, scarf streaming straight back; the legs make one quick stride over the 6 frames. Paint it solid; a speed trail can go in the effects row |
| 9 | POUNCE (Super Pounce) | 6 | 16 fps | yes | 0.38 s per loop | Super Pounce: a long forward leap that defeats walkers | Crouched take-off (1), body stretching out (2–3), fully stretched with front paws reaching ahead, claws out, back legs straight behind (4–5), starting to land (6) |
| 10 | HURT | 4 | 12 fps | yes | 0.33 s | Just after taking a hit | Recoil backwards with eyes squeezed shut "> <" and ears back (1–2), recoil peak (3), easing back (4) |
| 11 | DEATH | 10 | 12 fps | no | 0.83 s | Losing the last heart (the last frame stays) | Hit flinch (1–2), thrown up (3–4), tumbling (5–6), landing on its side (7), bounce (8), lying flat (9), lying flat with eyes "x x" (10) |
| 12 | KO | 4 | 4 fps | yes | 1 s | Game-over screen | Lying flat on its side, dizzy swirl eyes, breathing slowly over the 4 frames (the swirls may turn). The game adds the stars itself |
| 13 | GHOST | 8 | 8 fps | yes | 1 s | Game-over screen, floating above the KO cat | A pale, softly glowing spirit version of the cat, **still with a clear outline**, bobbing smoothly up and down once over the 8 frames, tail waving. The game makes it see-through |
| 14 | MENU | 8 | 8 fps | yes | 1 s | Start screen and the CATS screen | Standing proud, three-quarter view, breathing and tail sway like IDLE, with the same blink in frames 6–8 |
| 15 | SIT HAPPY | 8 | 10 fps | yes | 0.8 s | Start screen while happy | Sitting, happy "^ ^" closed-eye smile (allowed here), tail wagging one full swing and back, a small head bob |

Also wanted: **CHEER** 6 frames (10 fps, loops: paws up, hopping; Fluffy's is used on the title screen)
and **PEEK** 6 frames (6 fps, loops: lying on a ledge, looking down, tail swaying). Optional for the
other cats.

**Total: 102 frames per cat** (114 with CHEER and PEEK), plus the effects row.

## Before sending, check

- [ ] The background is transparent: the squares disappear on a dark background.
- [ ] Every row has exactly the frame count in the table, and looping rows close the loop.
- [ ] Neighbouring frames are small steps (in-betweens), not different poses.
- [ ] The cat faces right everywhere, at the same size in every frame.
- [ ] Paws on one line in grounded rows; a shadow under airborne frames.
- [ ] Both eyes open, except the IDLE/MENU blink, HURT, DEATH, KO and SIT HAPPY.
- [ ] Two sheets: A (movement and actions) and B (reactions, menus, effects).
- [ ] DOUBLE JUMP is a flip, THROW is a paw throw, POUNCE is a stretched leap (not a ball).
- [ ] No yarn ball, no effects touching the cat, at least ~20 px between frames.
- [ ] Standing height about 90–110 px.

Mistakes seen on earlier sheets: a checkerboard painted in instead of transparency, a row with one
frame more than its label, a cat that winks in idle and run, a ball roll instead of the pounce leap, and
a ghost without an outline.

## For the developer cutting the sheet

These counts are higher than the code-drawn heroes' (e.g. RUN 8 at 14 fps). The game reads frame counts
and fps from `Sprites.json`, so it plays them as they are, as long as each animation keeps its duration:
THROW must fit the 0.25 s throw window, and HURT the 0.3 s hurt window. Use every painted frame and set
fps = frames / duration; `test_hero_skins_match_the_hero` in `Tools/sprites/tests/test_sprites.py` allows a
painted skin its own counts and fps if each animation lasts within about 25% of the code-drawn hero's. One
thing must still change for two-sheet cats: `sheet_hero.py` reads one sheet per cat, not two.
