# Painting a boss sheet: Lantern Toad Guardian (Sakura's route, level 2)

What a painted sheet for `boss_toad` must contain so the build can cut it into the game's animations
(`Tools/sprites/sheet_boss.py`, `characters/boss_toad_painted.py`), the same way as the hero
(`docs/hero-sheet-brief.md`). The frame counts and speeds below are for smooth motion: they are higher
than the first painted sheet's, so the cutter's table and the frame counts in `Tools/sprites/tests/test_sprites.py`
change with the next sheet.

The boss: a squat crimson toad in three-quarter view, darker red underneath, gold-orange speckles on its
haunch and legs, a cream belly and throat, heavy half-lidded golden eyes and a wide mouth. It wears a
wide conical dark-brown straw hat with a gold rim and finial, piled with pink cherry blossoms, a red
paper lantern hanging from each side of the brim, and a thick gold rope collar with a tassel. It sits on
a mossy rock.

## What to deliver

- **Two sheets**, because there are about 80–100 frames:
  - `<Boss name> Boss Sheet A.png`: the boss's own animations (IDLE, the attacks, HURT, DEATH).
  - `<Boss name> Boss Sheet B.png`: the projectile rows, and WALK if painted.
- **PNG, about 2560×1600 each (larger is fine)**, with a **real transparent background** (see Sheet
  rules). Long rows may wrap onto a second line directly below; label it "CLAW (cont.)" and keep the order.
- **Boss size:** about **200–260 px wide sitting**, the same in every frame.

## Smooth motion

Every animation plays at about **10 frames a second** (idle and hurt a little faster), so the boss
moves smoothly instead of jumping between a few poses.

- **Paint in-betweens.** Each frame is a small step from the one before: a paw rises a little more, the
  glow grows a little brighter. No two neighbouring frames should look like different poses.
- **The wind-up is long (about 1 s, 10 or more frames) and must keep moving.** It's the warning the
  player reads, so it builds steadily: crouching lower, the glow growing, tails or lanterns swinging,
  a tremble at the peak. Never paint the same frame twice to fill time.
- **The strike or release is one clear frame** at the number given in the table, so it lands when the
  projectile leaves. Put the biggest change of the whole row there.
- **Follow-through:** tails, scarf, hat and lanterns lag behind the body and keep swinging after the
  strike. Ease out into the settle.
- **Looping rows close the loop:** the last frame of IDLE (and WALK) leads straight back into the first.
- **Keep the volume:** the boss must not grow or shrink between frames. Squash on a landing and stretch
  on a leap are welcome, but they return to the same size.

## Sheet rules

- **Export as a PNG with a real transparent background.** A checkerboard painted into the picture is
  not transparency: the cutter then has to guess which light pixels are background and which are the
  cream belly or the blossoms, and eats them or leaves specks. To check, open the PNG over a dark
  background: the squares must disappear. If the tool can't export transparency, use one flat colour
  that never appears on the toad (pure green `#00FF00` or dark navy), never a checkerboard or gradient.
- The toad is fully opaque with a dark outline; glow may be soft but must not touch or join two frames.
- One row per animation, frames left to right in playing order, label outside the row.
- Paint the toad facing **right**; the build mirrors it so it faces the hero in the game.
- At least ~30 px of empty space between frames.
- **Same scale in every frame of every row**, the bottom of the mossy rock on one baseline (only the
  slam leaves the ground). The game frame is 160×136 with the ground 4 px above the bottom, and the body
  the hero must hit is about 60 wide × 60 tall from the ground: body and face under the hat brim. The
  hat, lanterns and rock can stick out of that, but keep the widest pose no wider than about 2.5× the
  body, and leave room above the hat for the slam leap.
- **Both eyes open** (half-lidded is its normal look) unless the action below says otherwise. One blink
  in idle only.
- **Don't paint the projectiles flying away** — the tongue, the paper lanterns, the rocks and the shock
  wave are separate sprites (rows at the end). Paint only what stays on the toad: the throat puffing, the
  energy gathering at the mouth, the burst where it lands.

## How the game plays an attack

Each attack has a **wind-up** (the warning the player reads), then the attack itself. The game plays the
attack row once, from its first frame at the start of the wind-up, at 10 frames a second, and holds
the last frame until the boss rests. So frame N shows at about (N − 1) ÷ 10 seconds. The table puts the
strike/release frame at the moment the projectile leaves; paint the wind-up before it and the
follow-through after it.

## Animations

| # | Row | Frames | Speed | Loops | When the game plays it | What the frames show |
|---|---|---|---|---|---|---|
| 1 | IDLE | 8 | 8 fps | yes (1 s) | Entering the arena, between attacks | Sitting on its rock: the throat puffing out over 1–4 and back over 5–8, lanterns swaying; **blink** over 6–8 |
| 2 | TONGUE | 14 | 10 fps | no | `tongue_strike` (a low tongue lash along the ground the hero jumps over) | 1–4 leaning forward, cheeks swelling; 5–8 pink energy gathering at the mouth; 9–11 mouth starting to open, a tremble (the warning peak); **12 strike** (1.1 s): mouth wide, the base of the tongue shooting out; 13 tongue snapping back; 14 mouth closing, settling |
| 3 | LANTERNS | 18 | 10 fps | no | `lantern_arc` (spits a low lantern, then a high one) | 1–4 rearing back, throat swelling; 5–8 throat glowing; 9–10 cheeks full (the warning peak); **11 first spit** (1.0 s): mouth open; 12–16 refilling, head tilting up; **17 second spit** (1.6 s): mouth open, head up; 18 settling back |
| 4 | SLAM | 20 | 10 fps | no | `area_slam` (a rock falls ahead of the hero, then a shock wave rolls along the ground) | 1–4 deep crouch; 5–8 arms rising; 9–12 **leap**: off the rock, up to about a hat-height; 13–14 top of the leap; 15–16 coming down; **17 landing** (1.6 s): flattened, a burst of pink spikes, rocks and petals round the rock; 18–19 bouncing back up; 20 settling |
| 5 | HURT | 4 | 12 fps | yes | Just after being hit | 1–2 flinch with squeezed eyes, hat knocked askew; 3 recoil peak; 4 easing back. Keep the outline (the game may flash it) |
| 6 | DEATH | 12 | 10 fps | no (last frame stays) | Defeated | 1–2 big flinch; 3–4 slumping; 5–6 the hat tipping over and sliding off; 7–8 collapsing flat; 9–10 fading in a pink burst; 11 mostly gone; 12 only the mossy rock left |

Optional (the game doesn't use them today): WALK 8 frames (10 fps, loops: a squat shuffle, the hat
rocking) and PREPARE 6 frames (10 fps: leaning in, energy gathering at the mouth).

**Total: 76 boss frames** (90 with the optional rows), plus 32 projectile frames.

## Projectile rows (separate sprites)

| Row | Frames | Size in game | Loops | What it is |
|---|---|---|---|---|
| TONGUE | 4 | 42×12 (hits 40×10, low) | yes | The long pink tongue with a pink lantern-ball tip, stretched out flat and **as long as it is wide in the game (about 3.5× longer than tall)**, rippling along its length |
| LANTERN SHOT | 8 | 12×12 (hits 10×10) | yes | A red paper lantern with a white blossom crest, turning through one full spin as it flies, low |
| LANTERN SHOT HIGH | 8 | 12×12 (hits 10×10) | yes | The same lantern, a little brighter or with sparks, so the high one reads differently |
| SLAM ROCK | 8 | 14×14 (hits 12×12) | yes | A mossy rock tumbling through one full turn as it falls from above, with nothing loose beside it |
| SLAM WAVE | 4 | 18×12 (hits 16×10, low) | yes | A pink energy wave with petals rolling along the ground |

Projectiles fly toward the left (toward the hero): paint them pointing **left**, with the tip or trail on
the right. The tongue's lantern-ball tip is on the left.

## Before sending, check

- [ ] The background is transparent: the squares disappear on a dark background.
- [ ] **Two sheets**, not everything squeezed onto one: on a single 1536×1024 sheet the boss ends up
      about 100 px wide and has to be enlarged 2–3× in the game, which makes it soft.
- [ ] The boss is **200–260 px wide**, the same size in every frame of every row.
- [ ] **Every row has exactly the frame count in its label** — count them. Earlier sheets had rows
      with 12 frames labelled 8, or 3 labelled 4.
- [ ] Frames don't touch: at least ~30 px between bosses, and an attack effect (a slash, a burst) stays
      inside its own frame, never overlapping the next boss.
- [ ] Each attack's wind-up keeps moving (no repeated frames), and the strike/release frame is at the
      number in the table.
- [ ] Looping rows (IDLE, WALK) close the loop; DEATH ends on its final frame.
- [ ] Projectiles point left, each in its own row, with the counts in the projectile table.
