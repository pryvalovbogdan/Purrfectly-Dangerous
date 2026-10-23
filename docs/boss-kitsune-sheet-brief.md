# Painting a boss sheet: Blossom Kitsune Guardian (Sakura's route, level 1)

What a painted sheet for `boss_kitsune` must contain so the build can cut it into the game's animations
(`Tools/sprites/sheet_boss.py`, `characters/boss_kitsune_painted.py`), the same way as the hero
(`docs/hero-sheet-brief.md`). The frame counts and speeds below are for smooth motion: they are higher
than the first painted sheet's, so the cutter's table and the frame counts in `Tools/sprites/tests/test_sprites.py`
change with the next sheet.

The boss: a white fox in cream fur shaded pink, three big fluffy tails tipped pink and magenta, branching
antlers flowering with blossoms, a magenta forehead mark, a dark purple scarf with a gold rope, a gold
bell and red tassels.

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
  not transparency: the cutter then has to guess which light pixels are background and which are cream
  fur, and eats fur or leaves specks. To check, open the PNG over a dark background: the squares must
  disappear. If the tool can't export transparency, use one flat colour that never appears on the fox
  (pure green `#00FF00` or dark navy), never a checkerboard or gradient.
- The fox is fully opaque with a dark outline; glow may be soft but must not touch or join two frames.
- One row per animation, frames left to right in playing order, label outside the row.
- Paint the fox facing **right**; the build mirrors it so it faces the hero in the game.
- At least ~30 px of empty space between frames.
- **Same scale in every frame of every row**, all paws on one baseline (it fights on the ground).
  The game frame is 150×120 with the ground 4 px above the bottom, and the body the hero must hit is
  about 50 wide × 70 tall from the ground: haunch, chest and neck. Tails, antlers and muzzle can stick
  out of that, but keep the widest pose no wider than about 2.5× the body.
- **Both eyes open** unless the action below says otherwise. One blink in idle only.
- **Don't paint the projectiles flying away** — the slash, the blossom shots and the spirits are separate
  sprites (rows at the end). Paint only what stays on the fox: the paw swipe, the glow gathering at the
  mouth, the swirl around it.

## How the game plays an attack

Each attack has a **wind-up** (the warning the player reads), then the attack itself. The game plays the
attack row once, from its first frame at the start of the wind-up, at 10 frames a second, and holds
the last frame until the boss rests. So frame N shows at about (N − 1) ÷ 10 seconds. The table puts the
strike/release frame at the moment the projectile leaves; paint the wind-up before it and the
follow-through after it.

## Animations

| # | Row | Frames | Speed | Loops | When the game plays it | What the frames show |
|---|---|---|---|---|---|---|
| 1 | IDLE | 8 | 8 fps | yes (1 s) | Entering the arena, between attacks | Sitting proud: breathing over 1–4, tails swaying through all 8, petals drifting; **blink** over 6–8 (half-closed, closed, half-open) |
| 2 | CLAW | 16 | 10 fps | no | `claw_slash` and `double_claw` (a low slash the hero jumps over) | 1–4 crouching lower, eyes narrowing; 5–9 the near forepaw rising high, claws starting to glow; 10–12 coiled, glow at its brightest, a tremble (the warning peak); **13 strike** (1.2 s): forepaw thrust forward through a big magenta crescent; 14–15 crescent breaking into petals; 16 settling back |
| 3 | BLOOM | 14 | 10 fps | no | `bloom_shots` and `bloom_volley` (blossom shots, low ones to jump, high ones to stay under) | 1–3 crouch, head lowering; 4–10 a glowing blossom gathering at the mouth, growing every frame; 11 at its biggest (the warning peak); **12 release** (1.1 s): mouth open, burst of light and petals; 13 a smaller after-burst; 14 settling back |
| 4 | SUMMON | 16 | 10 fps | no | `spirit_summon` (two blossom spirits fly at the hero) | 1–4 rearing up, head back; 5–9 a pink swirl starting round it and growing; 10–12 swirl bright, antlers glowing; **13 release** (1.2 s): swirl at full size, small fox-spirit flames appear; 14–15 flames leaving; 16 settling back |
| 5 | HURT | 4 | 12 fps | yes | Just after being hit | 1–2 flinch backwards, eyes squeezed "> <", ears back; 3 recoil peak; 4 easing back. Keep the outline (the game may flash it) |
| 6 | DEATH | 12 | 10 fps | no (last frame stays) | Defeated | 1–2 big flinch; 3–4 sinking; 5–6 front legs giving way; 7–8 lying down, then flat, eyes closed; 9–10 the body turning into petals; 11 mostly petals; 12 only a few petals left |

Optional: WALK 8 frames (10 fps, loops: trotting on all fours, tails streaming) — the game doesn't use
it today.

**Total: 70 boss frames** (78 with WALK), plus 36 projectile frames.

## Projectile and spirit rows (separate sprites)

| Row | Frames | Size in game | Loops | What it is |
|---|---|---|---|---|
| CLAW SLASH | 6 | 28×14 (hits 26×12, low) | yes | A magenta crescent flying left along the ground, its edge shimmering and shedding petals |
| BLOOM SHOT | 8 | 12×12 (hits 10×10) | yes | A glowing pink blossom turning through one full spin as it flies; used low |
| BLOOM SHOT HIGH | 8 | 12×12 (hits 10×10) | yes | The same blossom, a little brighter or with sparkles, so the high one reads differently |
| SAKURA SPIRIT — FLOAT | 8 | 24×24 (hits 12×12) | yes | A small pink fox-spirit flame with a face, bobbing smoothly up and down once as it floats toward the hero |
| SAKURA SPIRIT — DEATH | 6 | 24×24 | no | Popping into petals when hit, the petals scattering and fading |

Projectiles fly toward the left (toward the hero): paint them pointing **left**, with the trail on the
right.

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
