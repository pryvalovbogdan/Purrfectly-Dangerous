# Hero sprite sheet brief (for any cat)

A brief for the artist painting a playable cat for **Purrfectly Dangerous**, a 2D pixel-art
auto-runner for iPhone. Each cat is one painted sprite sheet. The game's build cuts the sheet into
animation frames automatically (`Tools/sprites/sheet_hero.py`), so the sheet must follow the rules below
exactly. Frame counts, speeds and loops are what the game plays. A missing or miscounted row means the
game has to fake that animation from other frames.

## What to deliver

- **One sheet per cat**: `<Cat name> Hero Sheet.png`, every animation in the table plus the effects row
  (about 60 frames).
- **PNG, about 2560×1600 (larger is fine)**, with a **real transparent background** (see Sheet rules).
- **Cat size:** about **90–110 px tall standing**, the same in every row. All cats appear at the same
  size in the game, so a cat painted smaller ends up smaller on screen.

## Few frames, all the same cat

The game plays only a few frames per animation (the counts below). Earlier sheets had 16–17 frames per
row and the cats drifted from frame to frame: the tail was whole in one frame and hidden in the next, and
an eye winked now and then. In the game that looks like flicker. Fewer, steadier frames look better. That
means:

- **The same cat in every frame.** The same size, the same face, the same markings, the same scarf. Only
  the pose changes.
- **The whole tail in every frame**, at the same size: never hidden behind another cat, never cut off.
- **No eye blinking.** Both eyes fully open in every frame of every row. No blinks, no winks, no
  half-closed or squinting eyes, not even one frame of a blink in IDLE or MENU: the game plays so few
  frames that any blink flashes as a flicker. The eyes look the same in every frame: same size, same
  shape, same shine. The only exceptions are the expressions the table names: "> <" in HURT, "x x" in
  DEATH, swirls in KO, "^ ^" in SIT HAPPY and CHEER.
- **Clear poses.** With 2–8 frames each frame must read on its own: a run frame shows a clearly
  different leg position from its neighbours.
- **Looping rows must close the loop.** The last frame leads straight back into the first (RUN, IDLE,
  MENU, SIT HAPPY, GHOST, KO, DASH, JUMP, FALL, DOUBLE JUMP).
- **Follow-through:** the ears, scarf and tail lag a little behind the body.

## Sheet rules

- **Export as a PNG with a real transparent background.** A checkerboard painted into the picture is
  not transparency: the cutter then has to guess which light pixels are background and which are white
  fur, and eats fur or leaves specks. To check, open the PNG over a dark background: the squares must
  disappear. If the tool can't export transparency, use one flat colour that never appears on the cat
  (pure green `#00FF00` or dark navy), never a checkerboard or gradient.
- **The cat is fully opaque with a dark outline all round**, including the ghost. Glow may be soft, but
  it must not touch or join two frames.
- **Cats never touch or overlap.** Leave **at least ~30 px of empty space** between frames, measured
  from the tip of the tail and the end of the scarf, so the cutter can't hand one cat's tail to its
  neighbour.
- **One row per animation**, frames left to right in playing order, the label above or beside the row
  (never touching a cat). Several short rows may share a line if there is a clear gap between them.
- **The number of cats in a row must equal the frame count in the table.** No extra or missing frames.
- **The cat faces right** in every frame.
- **Same scale in every frame of every row.** The widest frame sets the size of all of them, so keep
  run, dash and pounce no wider than about 1.6× the standing width.
- **Grounded rows:** all paws on one baseline. **Airborne rows:** paint a soft ground shadow under the
  cat so the ground line is known; the cutter removes it.
- **Effects** (petals, sparkles, swirls, speed lines, trails, dust) go in their own row at the bottom,
  never touching the cat. Small loose specks near the cat are dropped by the cutter.
- **Don't paint the yarn ball**: the game draws the shot itself.

### Sharky's water

Sharky's abilities look different from the other cats' (the rules are the same):

- **Yarn Shot is a water wave.** In THROW, Sharky flings a wave instead of tossing yarn: one paw sweeps
  forward and the onesie's fin swings with it. Leave the paw empty, because the game draws the flying
  wave. If you paint the wave, put it in the effects row: 4 frames of a small curling blue wave with
  foam, flying right, about 24×16 px, plus 3 frames of its splash when it hits.
- **Ghost Dash is a surf.** In DASH, Sharky crouches low as if riding a board, leaning forward, with
  all four paws together on one line, not running. Paint no water under the cat. If you paint the
  water, put it in the effects row: 4 frames of a strip of water about 1.5× the cat's length and a
  quarter of its height, with foam and spray at the front, plus 2 frames of a starting splash. The
  game draws it under Sharky's feet while the dash lasts.

### Cabage's cabbages

Cabage's abilities look different from the other cats' (the rules are the same):

- **Yarn Shot is a thrown cabbage.** In THROW, Cabage lobs a cabbage overhand: the paw goes back
  behind the leafy hood, then forward. Leave the paw empty, because the game draws the flying cabbage.
  If you paint the cabbage, put it in the effects row: 4 frames of a small round green cabbage
  spinning, about 14×14 px, plus 3 frames of it bursting into leaves when it hits.
- **Ghost Dash is a leaf ride.** In DASH, Cabage crouches low on one big cabbage leaf, leaning
  forward with all four paws together on one line, as if sledging. Don't paint the leaf on the cat
  rows. If you paint the leaf, put it in the effects row: 4 frames of a wide curled cabbage leaf about
  1.3× the cat's length, its front tip curled up, with a few loose leaf bits flying off behind, plus
  2 frames of leaves scattering when the ride starts. The game draws it under Cabage's feet while the
  dash lasts.

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
| Cabage (`cabage`) | Leafy hood on: lobs cabbages and rides a leaf every dash. | Calico kitten in a whole cabbage onesie with a leafy hood; see "Cabage's cabbages" below |
| Sharky (`sharky`) | Shark suit on: throws waves and surfs every dash. | Calico kitten in a whole shark onesie, face in the shark's mouth; see "Sharky's water" below |

## Animations

| # | Row | Frames | Speed | Loops | Lasts | When the game plays it | What the frames show |
|---|---|---|---|---|---|---|---|
| 1 | IDLE | 4 | 4 fps | yes | 1 s | Standing still after a win; fallback in menus | Standing on all fours, breathing: chest up (1–2), down (3–4); the tail sways a little. Eyes open |
| 2 | RUN | 8 | 14 fps | yes | 0.57 s per cycle | Running on the ground — most of the game | One full gallop: front paws land (1), body compresses (2), back paws pass under (3), push off (4), all paws off the ground (5), front paws reaching (6–7), about to land (8). Frame 8 leads back into 1. The body bobs up and down; ears, scarf and tail bounce a beat behind. Tail whole and eyes open in every frame |
| 3 | STOP | 4 | 10 fps | no | 0.4 s | Level won: skids to a halt, then idle | Front paws braking, leaning back (1), sliding (2), settling (3), standing (4, the same as IDLE 1). No dust (it goes in the effects row) |
| 4 | JUMP | 2 | 8 fps | yes | 0.25 s per loop | Rising after a jump | Leaping up: front paws tucked, back legs stretched behind, scarf trailing down; the 2 frames flutter the scarf and tail |
| 5 | FALL | 2 | 8 fps | yes | 0.25 s per loop | Coming down | Front paws reaching down for the landing, back legs forward, scarf and ears blown up; the 2 frames flutter them |
| 6 | DOUBLE JUMP | 4 | 16 fps | yes | 0.25 s per flip | Rising after the second jump (Double Pounce) | **A full forward flip**, curled up, turning 90° per frame: 0°, 90°, 180°, 270°. Frame 4 leads back into 1 |
| 7 | THROW (yarn shot) | 4 | 16 fps | no | 0.25 s | Every yarn shot, on the ground or in the air | Front paw pulled back (1), paw fully forward, mouth open — the release (2), follow-through (3), back to running (4). No yarn ball. Keep the back legs in a running pose |
| 8 | DASH (Ghost Dash) | 4 | 16 fps | yes | 0.25 s | Ghost Dash | Low, stretched, very fast pose, ears flat, scarf streaming straight back; the legs make one quick stride over the 4 frames. Paint it solid; a speed trail can go in the effects row |
| 9 | POUNCE (Super Pounce) | 4 | 12 fps | yes | 0.33 s per loop | Super Pounce: a long forward leap that defeats walkers | Crouched take-off (1), body stretching out (2), fully stretched with front paws reaching ahead, claws out, back legs straight behind (3), starting to land (4) |
| 10 | HURT | 2 | 10 fps | yes | 0.2 s | Just after taking a hit | Recoil backwards with eyes squeezed shut "> <" and ears back (1), easing back (2) |
| 11 | DEATH | 6 | 8 fps | no | 0.75 s | Losing the last heart (the last frame stays) | Hit flinch (1), thrown up (2), tumbling (3), landing on its side (4), lying flat (5), lying flat with eyes "x x" (6) |
| 12 | KO | 2 | 3 fps | yes | 0.67 s | Game-over screen | Lying flat on its side, dizzy swirl eyes, breathing in (1) and out (2). The game adds the stars itself |
| 13 | GHOST | 4 | 5 fps | yes | 0.8 s | Game-over screen, floating above the KO cat | A pale, softly glowing spirit version of the cat, **still with a clear outline**, bobbing up (1–2) and down (3–4), tail waving. The game makes it see-through |
| 14 | MENU | 4 | 4 fps | yes | 1 s | Start screen and the CATS screen | Standing proud, three-quarter view, breathing and tail sway like IDLE. Eyes open |
| 15 | SIT HAPPY | 4 | 6 fps | yes | 0.67 s | Start screen while happy | Sitting, happy "^ ^" closed-eye smile (allowed here), tail wagging one full swing and back, a small head bob |

Also wanted: **CHEER** 4 frames (8 fps, loops: paws up, hopping, "^ ^" eyes allowed; Fluffy's is used on
the title screen) and **PEEK** 4 frames (4 fps, loops: lying on a ledge, looking down, tail swaying).
Optional for the other cats.

**Total: 58 frames per cat** (66 with CHEER and PEEK), plus the effects row.

## Before sending, check

- [ ] The background is transparent: the squares disappear on a dark background.
- [ ] Every row has exactly the frame count in the table, and looping rows close the loop.
- [ ] No two cats touch; at least ~30 px between them, tails and scarves included.
- [ ] The whole tail shows in every frame, at the same size.
- [ ] No eye blinking: both eyes fully open and identical in every frame, except HURT, DEATH, KO,
      SIT HAPPY and CHEER. No blinks, winks or half-closed eyes, in IDLE and MENU too.
- [ ] The cat faces right everywhere, at the same size and with the same face in every frame.
- [ ] Paws on one line in grounded rows; a shadow under airborne frames.
- [ ] DOUBLE JUMP is a flip, THROW is a paw throw, POUNCE is a stretched leap (not a ball).
- [ ] No yarn ball, no effects touching the cat.
- [ ] Standing height about 90–110 px.

Mistakes seen on earlier sheets: a checkerboard painted in instead of transparency, a row with more frames
than its label, cats packed so tight that each one's tail hid behind the next (the tail then flickers on and
off in the game), a cat that winks in idle, menu, jump and throw, a ball roll instead of the pounce leap, and
a ghost without an outline.

## For the developer cutting the sheet

These counts and speeds are the code-drawn hero's (`hero.drawn_hero`), so a sheet painted to them plays
at the same fps. The game reads frame counts and fps from `Sprites.json`. A painted skin may still have
its own counts if each animation keeps its duration: THROW must fit the 0.25 s throw window, and HURT the
0.3 s hurt window; `test_hero_skins_match_the_hero` in `Tools/sprites/tests/test_sprites.py` allows each
animation within about 25% of the code-drawn hero's. For an older sheet with too many or uneven frames, a
row in `characters/hero_painted.py` can play only some of its painted cats (the fourth item in the plan:
their indices), as Fluffy's does.
