# Level and boss data

## `App/Resources/Levels/level_NN.json`

The normal route is every `level_NN.json`, in file-name order. A cat's own level for slot NN (from 01)
is `route_<skin>_NN.json` (e.g. `route_sakura_01.json`, Sakura's Blossom Path in slot 1): same format,
with its own `id` (e.g. `sakura_01`, so its progress and bests are its own) and `nameKey`
(e.g. `level.sakura_1.name`). It should fit its slot as the level it replaces does (`entryHeroLevel`,
`shrineLevel`, `bossRewardLevel`). Every route level is validated like a normal one.

Files are loaded in file-name order; adding `level_05.json` adds a fifth level with no code change.

```json
{
  "id": "level_01",
  "nameKey": "level.1.name",
  "background": "forest",
  "speed": 110,
  "length": 3600,
  "entryHeroLevel": 1,
  "shrineLevel": 2,
  "boss": "boss_squirrel",
  "bossRewardLevel": 3,
  "ravines": [{ "at": 1420, "width": 30 }],
  "slick": [{ "at": 1110, "width": 120, "kind": "milk" }],
  "platforms": [{ "at": 3790, "width": 52, "y": 12, "mode": "crumbles", "kind": "bridge" }],
  "terrain": [{ "at": 900, "width": 96, "height": 24 }, { "at": 996, "width": 64, "height": 40 },
              { "at": 1600, "width": 80, "height": -20 }],
  "items": [{ "at": 420, "kind": "bush" }, { "at": 704, "kind": "fish", "y": 30 },
            { "at": 900, "kind": "vent", "cycleOffset": 1.2 }]
}
```

| Field | Meaning |
| --- | --- |
| `nameKey` | Key in `App/Resources/Lore.json` holding the display name |
| `background` | Theme: needs sprites `bg_<theme>_sky`, `_clouds`, `_puffs`, `_far`, `_near`, `_bushes`, `_sky_top` and `ground_<theme>` with `_fill` and `_earth` |
| `speed` | World units per second |
| `length` | Distance at which the boss appears |
| `entryHeroLevel` | Hero level the player is guaranteed on entry; must not exceed what earlier bosses grant |
| `shrineLevel` | Hero level granted by a `yarn_basket` item (required if one is placed) |
| `bossRewardLevel` | Hero level granted for beating the boss |
| `items[].at` | Distance from the start. Keep 150 clear at the start and 60 before `length` |
| `items[].kind` | An `ItemKind` (see the table below) |
| `items[].y` | Optional height above ground (fish arcs) |
| `items[].cycleOffset` | Optional seconds added to the world clock for this item's on/off cycle (vents, pistons, ghost cats), so neighbours can run out of step |
| `slick[]` | Optional slick ground: `at`, `width`, `kind` (look only, also the sprite name: `milk`, `ice`). On it the run speed is ×1.3 and every jump is a full one (no short hop). The speed is kept through a jump from it |
| `platforms[]` | Optional one-way ledges: `at` (left end), `width`, `y` (top above the base ground, 4–44; over terrain at least 4 above the highest block under it), `mode`, `kind` (look only, also the sprite name: `bridge`, `ice_ledge`, `vanish`, `island`; an `island` is a floating clump of earth and must be `solid`). The hero lands on them from above, jumps up through them, and can stand on them over a ravine |
| `platforms[].mode` | `solid`; `crumbles` (gone for good `crumbleAfter` s after the first landing, default 0.5); `blinks` (there for `solidFor` of every `period` s on the world clock, default 1.6 of 2.4, flickering for the last 0.4; `offset` shifts it); `moves` (swings `travel` either way of where it is placed along `axis`, `x` sideways or `y` up and down, smoothly, one full swing every `period` s on the world clock, default 2.4; `offset` shifts it; the hero rides it. The validator wants an axis and a travel above 0, a vertical one between 4 and the jump limit all the way, and a sideways one clear of the runway and boss arena; for a ravine's width it counts the ledge where it is placed) |

Walking off the end of a ledge, or standing on one as it goes, drops the hero; a Double Pounce is
still possible then. Running off the rim of a ravine on the ground allows no jump at all.

### Item kinds

| World | Kind | Behaviour |
| --- | --- | --- |
| forest | `bush`, `stump` | Static terrain (low-wide / tall). Landing on a stump's top is a safe bounce; the bush's thorns hurt from above too |
| forest | `squirrel` | Walker; a stomp kills |
| forest | `acorn` | Fast low roller |
| forest | `branch_squirrel` | Sits 44 up, lobs `acorn` hazards that land and roll on along the ground |
| forest | `hedgehog` | Walker; within 90 of the hero it curls up: then no stomp, and yarn bounces off |
| forest | `slime` | Slow walker (16/s); a stomp kills |
| forest | `mushroom_cat` | Stands still; puffs a `spore` from 24 up (top of its cap) every 2 s in range that drops ahead of the hero and rolls on along the ground; a stomp kills |
| forest | `forest_bat` | Like `bat`: flies at 42, swoops to 28 (just over a standing kitten) as it nears |
| forest | `plant_cat` | Trap on the world clock: bites (30 high) for 0.6 s of every 2 s, open as a warning 0.5 s before, shut and harmless otherwise (`cycleOffset` shifts it); no stomp; yarn hits it any time, 2 HP |
| forest | `bee_cat` | Hovers 40 up, drifting in at 10/s; every 1.8 s in range fires a `sting` along the ground at 4 |
| forest | `stump_cat` | Terrain, 28 tall; every 2 s in range sends a `leaf` along the ground at 2; its top is a safe bounce (no kill), its sides hurt; 2 HP |
| forest | `snail_cat` | Very slow walker (8/s); within 80 of the hero it hides in its shell: then yarn bounces off, and landing on it is a safe bounce with no kill (`shellBounce`) |
| forest | `spider_cat` | Hangs 60 up, harmless and out of yarn's reach; 130 from the hero it blinks 0.4 s, drops, and walks in (20/s) as a walker; a stomp kills |
| frost | `icicle` | Hangs 70 up; 130 from the hero it blinks 0.35 s, drops, and lies as low shards (14×6) |
| frost | `snowball` | Fast roller, 2 HP |
| frost | `penguin` | Very fast slider; stomp is a safe bounce |
| frost | `snowdrift` | Static, low; its top is a safe bounce |
| frost | `ice_slime` | Walker (22/s); a stomp kills |
| frost | `snow_cat` | Fast walker (55/s), 20 tall; a stomp kills; 2 HP |
| frost | `ice_bat` | Like `forest_bat`: flies at 42, swoops to 28 (just over a standing kitten) as it nears |
| frost | `ice_golem` | Slow walker (8/s), 26×30; stomp is a safe bounce; 3 HP; needs hero level 3 |
| frost | `penguin_soldier` | Walks back and forth up to 30 either side of where it is placed (and turns at rims and steps); within 70 of the hero it thrusts a `spear` (low, at 6, 14×4, fast); a stomp kills; 2 HP |
| frost | `snowy_owl` | Hovers 60 up, drifting in at 10/s; 170 from the hero it blinks 0.4 s, then drops an `icicle_shot` straight down (lands ~50 ahead of the hero and lies there, 10 tall); no stomp |
| frost | `ice_hedgehog` | Walker; within 100 of the hero it curls up and rolls in at 110/s (turning at rims and steps): then no stomp, and yarn bounces off |
| frost | `snowman` | Stands, 30 tall; lobs `snowball_shot` hazards from 28 up that land ahead of the hero and roll on; stomp is a safe bounce; 2 HP |
| frost | `icicle_plant` | Trap on the world clock: open (24 high, hurts) for 0.6 s of every 2.4 s, opening as a warning 0.5 s before, shut and harmless otherwise (`cycleOffset` shifts it); each time it opens in range it fires an `icicle_bolt` along the ground at 4; no stomp; yarn hits it any time, 2 HP |
| frost | `mini_yeti` | Very slow walker (6/s), 30×34; no stomp; 4 HP; needs hero level 3 |
| haunted | `ghost_cat` | Drifts in high and down to the ground; visible 1.2 s of every 2 s and harmless otherwise; yarn passes through. While visible and in range it throws a `spirit_ball` every 2.4 s, straight at 26 (just over a standing kitten) |
| haunted | `bat` | Flies at 40, swoops to 26 (just over a standing kitten) as it nears |
| haunted | `skeleton_mouse` | Stands and throws low `bone` hazards; stomp kills; 2 HP |
| haunted | `skull` | Flies straight in at 26, just over a standing kitten |
| haunted | `bell` | Hangs 56 up, harmless; every 2 s in range it sends a low `soundwave` hazard along the ground |
| haunted | `tombstone` | Static, tall; its top is a safe bounce |
| haunted | `haunted_portrait` | Hovers 32 up (just over a standing kitten), drifting in at 12/s; every 2.2 s in range fires a `magic_shot` along the ground at 4; no stomp; 2 HP |
| haunted | `cursed_armor` | 20×28 statue: harmless and still, yarn bounces off, landing on it is a safe bounce, until the hero is within 140; flashes 0.5 s, then walks in at 12/s; awake it hurts to touch (no stomp); 3 HP; needs hero level 3 |
| haunted | `candle_cat` | Slow walker (15/s); every 2.5 s in range sends a `fire_orb` along the ground at 2; no stomp (its flame burns) |
| haunted | `poltergeist_book` | Floats 48 up, drifting in at 8/s; every 2.4 s within 220 lobs a `magic_bolt` that lands ahead of the hero and fizzles out (no rolling) |
| haunted | `gargoyle_cat` | Perched (harmless, still, yarn bounces off, landing on it is a safe bounce) until the hero is within 240; flashes 0.5 s, leaps 70 toward the hero (28 high, ~0.5 s), lands ahead of it on the local ground and walks in at 25/s; stomp is a safe bounce; 2 HP. Leave flat ground in front of it: a leap that comes down over a ravine is lost |
| haunted | `shadow_cat` | Unseen and intangible (yarn passes) until the hero is within 180; then appears 80 ahead of the hero, flashes 0.4 s keeping that distance, and dashes in at 120/s as a walker; a stomp kills. Where it appears is wherever the hero is plus 80, so leave ground there (no ravine or step) |
| citadel | `vent` | Flame column (60 high) for 0.8 s of every 2.4 s, blinking 0.5 s before; harmless otherwise |
| citadel | `piston` | Slams (70 high) for 0.6 s of every 2 s, blinking 0.4 s before; harmless otherwise |
| citadel | `cannon` | Mounted 24 up, fires `cannonball` hazards at 20 (just over a standing kitten); 2 HP |
| citadel | `debris` | As `icicle` |
| citadel | `mech_mouse` | Fast chaser, 2 HP; stomp is a safe bounce |
| citadel | `gear` | Static, tall |
| citadel | `crate_wall` | 120 high: only a Super Pounce breaks it (needs hero level 5); yarn bounces off |
| citadel | `lava_slime` | Walker (14/s), no stomp; every 2.4 s in range lobs a `lava_glob` from 12 up that lands ahead and becomes a `lava_puddle` (18×4) for 1 s |
| citadel | `fire_imp` | Hovers 40 up; once 140 from the hero it keeps that distance for 3 s, then drifts in at 20/s; every 2.2 s in range fires a `fireball_shot` along the ground at 4 |
| citadel | `stone_guard` | 26×32 walker (8/s); stomp is a safe bounce; within 60 it throws a short `magma_blast` (12×8) at 8; 4 HP; needs hero level 3 |
| citadel | `hell_hound` | A chase: unseen until the hero reaches the spot it is placed at; 0.6 s warning, then it runs in from 120 behind the hero at the level speed + 130, past it and on out of sight (over ravines and steps); hurts on any touch; 2 HP. Place it where the hero has flat ground for a jump about 1–1.5 s after reaching that spot |
| citadel | `ember_bat` | Like `ice_bat`: flies at 42, swoops to 28 |
| citadel | `flame_archer` | 16×24, stands; every 2 s in range fires a `flame_arrow` (12×4) at 6; a stomp kills; 2 HP. Put it on a ledge (terrain) for its intended look |
| citadel | `chainsaw_cat` | 26×30 walker (10/s) with a 20×24 blade zone in front of its body that hurts too; no stomp; 5 HP; needs hero level 5 (a Super Pounce through it defeats it) |
| citadel | `fire_wisp` | Floats 20 up, drifting in at 40/s; within 50 it flashes 0.5 s keeping that gap, then bursts into a `fire_ring` (40×10) on the ground for 0.4 s; yarn (from a hop) defeats it first |
| void | `void_slime` | 20×14 walker at 30/s in bursts on the world clock (0.5 s moving, 0.5 s still; `cycleOffset` shifts it); every 2.2 s in range spits a `void_orb` (8×8) along the ground at 2; no stomp |
| void | `void_bat` | Like `ice_bat`: flies at 42, swoops to 28; every 2 s in range fires a `void_orb` at 30 (over a standing kitten) |
| void | `void_sentinel` | Floats 36 up, still; charges 0.8 s (warning), then fires a `void_laser` (30×4, 170/s) at 4 within 300; 3 HP |
| void | `rift_hound` | Like `hell_hound`, with a 0.45 s warning and running 170 faster than the level |
| void | `void_mage` | 16×24, stands; every 3 s in range, by turns, summons a `void_wisp` 80 ahead of the hero (first) or fires a `void_bolt` (10×6) at 6; a stomp kills; 3 HP |
| void | `rift_turret` | Hovers 20 up, still (in the hero's way: jump it); charges 1 s (warning), then a `crystal_shot` (10×4, 200/s) at 4; 2 HP |
| void | `void_wisp` | Floats 30 up, drifting in at 30/s; every 2.5 s in range a `homing_orb` (8×8, 100/s) that steers its height toward the hero's middle at up to 40/s while ahead of the hero |
| void | `mini_void_cat` | As `shadow_cat` (unseen until 180, appears 80 ahead, 0.4 s flash, dash at 120/s), then once more: when its dash has passed the hero it appears 80 ahead again; a stomp kills |
| sakura | `sakura_slime` | 20×14 walker at 24/s in bursts on the world clock (0.6 s moving, 0.4 s still); a stomp kills |
| sakura | `sakura_bunny` | 18×20 walker at 70/s; within 90 of the hero it hops back once (35/s away, 0.35 s), then lunges at 150/s with a 14×16 swipe zone in front of it that hurts like its body; a stomp kills |
| sakura | `lantern_spirit` | Hovers 36 up, still; every 2.4 s in range a slow `blossom_shot` (10×8, 70/s) along the ground at 4 |
| sakura | `bird_crow` | Flies at 50, diving as it nears (from 170 away to 60) all the way to the ground; jump it late or yarn it |
| sakura | `spike_plant` | Trap on the world clock like `plant_cat`/`icicle_plant`: open (20 high, hurts) for 0.6 s of every 2.4 s, opening 0.5 s before; each time it opens in range it spits a `blossom_shot` along the ground at 4; yarn any time, 2 HP |
| sakura | `rolling_onigiri` | Sits still; within 110 of the hero it curls up and rolls in at 120/s (turning at rims and steps): then no stomp, and yarn bounces off |
| sakura | `bamboo_spikes` | Trap on the world clock: up (20×18, hurts) for 0.7 s of every 2.2 s, blinking 0.5 s before; down and harmless otherwise (`cycleOffset` shifts it) |
| sakura | `sakura_spirit` | 12×12, skims in 4 up at 70/s (the Kitsune Guardian summons it); jump it or yarn it |
| sakura_dusk | `lantern_slime` | 20×16 walker at 24/s in bursts (0.5 s moving, 0.5 s still); every 2 s within 220 drops a `lantern_ember` that lands as a `lantern_flame` (12×4) burning for 0.6 s; a stomp kills |
| sakura_dusk | `ninja_tanuki` | 18×22 walker at 30/s; within 80 it stands 0.25 s winding up, then slashes forward at 120/s with a 14×18 crescent in front that hurts; a stomp kills; 2 HP |
| sakura_dusk | `sakura_bat` | Like `forest_bat`: flies at 42, swoops to 28 |
| sakura_dusk | `shadow_spirit` | Floats 36 up, drifting in at 10/s; every 2.6 s a homing `spirit_flame` (8×8, 100/s, turning toward the hero's middle at up to 40/s); 2 HP |
| sakura_dusk | `spike_kappa` | Trap on the world clock: open (22×18, hurts) for 0.6 s of every 3 s, opening 0.6 s before; each time it opens in range it throws a fan of three `spike_ball`s (8×8) from 16 up, at 50/80/110 forward and 140/170/200 up, that land ahead and roll on; yarn any time, 2 HP. Mind its rhythm: it only throws if the hero is 30–300 away when it opens |
| sakura_dusk | `lantern_pendulum` | A 14×14 lantern on a 90 rope from a pivot 110 above where it is placed, swinging 1 rad either way every 3.2 s (`cycleOffset` shifts it): bottom of the swing 13 up (in the way), the ends about 54 up. Leave room either side (it swings about 76 each way) |
| sakura_dusk | `falling_lantern` | Hangs 70 up; 130 from the hero it blinks 0.4 s, drops, and burns on the ground as a 16×8 hot patch for 1 s, then is gone |
| sakura_night | `shadow_slime` | 20×16 walker at 30/s in bursts (0.4 s moving, 0.4 s still); its leap is drawn only; a stomp kills |
| sakura_night | `samurai_ronin` | 18×22 walker at 32/s; within 90 it stands 0.3 s in its stance, then lunges at 130/s with a 16×18 crescent slash in front that hurts; a stomp kills; 2 HP |
| sakura_night | `oni_cat` | 24×28 slow walker at 8/s with a 10×20 club always out in front that hurts like its body; every 3 s in range lobs an `oni_rock` (8×8) from 24 up that lands ahead and rolls on at 60/s; no stomp; 4 HP; needs kitten level 3 (Double Pounce over it) |
| sakura_night | `tengu_crow` | 18×14, flies at 52, diving as it nears (from 170 away to 60) all the way to the ground, at 55/s; jump it late or yarn it |
| sakura_night | `spirit_wisp` | 16×20, floats 36 up, drifting in at 12/s; every 2.4 s a homing `wisp_shot` (8×8, 110/s, turning toward the hero's middle at up to 40/s); 2 HP |
| any | `fish` | +5 XP and +1 fish |
| any | `yarn_basket` | Raises the hero to `shrineLevel` |

Ghost Dash (level 4) passes through creatures, thrown things and traps for 0.35 s, but not through
terrain (`bush`, `stump`, `stump_cat`, `snowdrift`, `tombstone`, `gear`, `crate_wall`) or over ravines. A Super
Pounce (level 5) defeats any walker or roller it touches and breaks a `crate_wall`.
| `terrain[]` | Optional steps in the ground: `at` (left end), `width` (at least 16), `height` above the base ground (positive: a raised block, at most 60; negative: a dip, at most 32 deep). Pieces never overlap; touching ones make a staircase. See below |
| `ravines[]` | Optional gaps in the ground: `at` is the left rim, `width` how far it spans. Needs sprites `ravine_<theme>`, `ravine_<theme>_fill` and `ravine_<theme>_deep` |

Useful numbers: the kitten's hitbox is 16 wide and 24 tall. A full (held) jump is about 63 high and
lasts 0.83 s, so it covers `speed × 0.83` units (≈ 91 at speed 110). A tap is about 24 high and
lasts about 0.47 s; holds in between land in between. A full jump plus a Double Pounce at its top
reaches about 98 and lasts about 1.3 s. One held jump climbs a step of up to 58. A Super Pounce is
32 high, lasts 0.53 s and adds 170 to the speed while in the air. Leave roughly 110+ units between
ground threats.

Ravines: a fall ends the run, so the validator caps `width` at 65% of a full jump's reach (59 at
speed 110, 75 at 140), or of a jump plus Double Pounce once `entryHeroLevel` is 3 or more (≈ 101 at
speed 120), plus the length of any platforms over it; it wants at least 16. Keep them out of the start runway and the last 60
units, leave 40 of ground between two of them, and put nothing that stands on the ground inside
one (coins above are fine). Walking enemies turn back at a rim, so one placed between two ravines
patrols the ledge. To have a walker turn where the player can watch, start it far enough from the
rim that it arrives about two seconds after it spawns (a goblin about 45 units, a hound about 90).

Terrain: running into any face higher than 4 above its feet knocks the kitten back about 26 units
(never over a ravine rim behind, nor into a higher face behind); it needs a jump to get on. Every rise it meets (onto a block, from stair to stair, out
of a dip) must be climbable with the hero level guaranteed there: at most 44 with one jump, at most
84 once Double Pounce (level 3) is guaranteed by `entryHeroLevel` or by a `yarn_basket` before it.
Keep terrain out of the start runway and the last 60 units (the boss arena is flat), 16 away from
any ravine, and off slick zones. Nothing that stands on the ground may stand across a step (fish and
other pickups may). Items, fish `y` and enemy heights are measured from the ground where they are
placed. Walkers turn back at every step, so one placed on a block patrols it. Draws with
`terrain_<theme>_top`, `_edge`, `_wall` and `_fill`, falling back to the `ground_<theme>` pieces.

## `App/Resources/Bosses.json`

```json
{
  "id": "boss_squirrel", "hp": 20, "width": 56, "height": 84, "baseY": 0,
  "vulnerable": "always",
  "attacks": [{
    "name": "acorn_volley", "telegraph": 0.8, "duration": 0.6, "recover": 0.8,
    "hazards": [{ "kind": "acorn", "delay": 0, "y": 0, "width": 16, "height": 10, "closingSpeed": 150 }]
  }],
  "phases": [{ "startsBelow": 1, "attacks": ["acorn_volley"] }]
}
```

- `vulnerable`: `always`, or `recover` (damage only lands in the pause after an attack).
- `armoredAbove` (optional): while the HP fraction is above it, damage only lands while recovering,
  whatever `vulnerable` says; at or below it `vulnerable` applies (the Mecha-Mouser uses 0.4).
- `phases[].decoys` (optional): extra look-alike copies during that phase, lined up from the boss
  toward the hero (`BossState.copyXs`). Only `BossState.trueCopy` takes damage, and it changes with
  every attack in a fixed order; yarn passes through the others.
- `phases[].requires` (optional, e.g. `["ghostDash", "superPounce"]`): in that phase yarn only lands
  while the boss is exposed. Using a listed ability (a Ghost Dash, or a Super Pounce) while an armed
  hazard overlaps the hero along x exposes it for `openingTime` seconds (boss field, default 1.5).
  Make sure the attacks of such a phase send hazards the hero can dash or pounce through.
- An attack runs `telegraph` → `duration` (hazards, `summons` and `portals` spawn at their `delay`)
  → `recover`.
- `attacks[].portals[]` (optional): `delay`, `open` (seconds), `ahead` and `y` of the entry, `exitAhead`
  and `exitY` of the exit (both relative to the hero, so they stay on screen), optional `reverses`
  (yarn comes back out) and `width`/`height` (default 16×28). Yarn entering the open entry leaves the
  exit at the same height within it, once per ball. Needs sprite `portal` (`open`, `close`).
- Hazard `falls: true`: a falling star. It hangs where it spawned while it arms (`arm`, blinking),
  then drops under gravity and shatters on the ground. Use `ahead` with `closingSpeed` equal to the
  level speed to pin it to a spot the hero runs toward, and a high `y`.
- Hazard `y` is its bottom edge: `0` makes a low hazard to jump, `42` a high one to run under
  (the kitten's hitbox is 16 wide and 24 tall, so anything below 24 hits it standing).
- `closingSpeed` is how fast it approaches on screen. With `ahead` the hazard appears that far in
  front of the hero instead of at the boss; set `closingSpeed` to the level speed to pin it to the
  ground, and `arm` to the seconds it blinks as a warning first.
- `phases` are ordered by falling `startsBelow` (HP fraction); the first must be `1`.
- Each hazard `kind` needs a sprite `hazard_<kind>`; each boss a sprite named like its `id` with
  `idle` and `death`, plus attack animations mapped in `GameScene.attackAnimation`.

## Validation

`swift test --package-path Packages/GameCore` runs `LevelValidator` on every level file: static
checks (runway, abilities guaranteed where needed, ravines, boss and attack names resolve) and then a bot
that must finish the level and boss **on a single heart**. A failure reports the distance at which
the bot was hit, e.g. `no-hit bot failed at distance 4431 (dead)` — a distance past `length` means
the boss pattern is the problem. `no-hit bot bounced off the step at 1210 more than 3 times`
or `no-hit bot was held back by the step at 1210 for over 4 s` means the bot could not get onto a
step (a softlock); `no-hit bot made no progress at distance 1210 for over 4 s` that it got nowhere. Terrain messages name the piece or the rise,
e.g. `step at 996 rises 40; one jump at hero level 2 climbs at most 58`. A rise also needs clear
ground before it, so that a kitten knocked back off it gets the run-up to climb it at the level's
speed (from 41 for a 40 step to 57 for a 56 step at speed 150): a ravine rim or a higher face too
close behind fails with `step at 1200 rises 48: knocked back off it at speed 150 the kitten needs 49
of run-up to climb it, but the ravine ending at 1170 leaves 22`. Other examples:
`terrain at 1210 is too close to the ravine at 1260`, `bush at 1000 stands across a step`.
