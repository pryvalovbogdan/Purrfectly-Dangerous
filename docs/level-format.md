# Level and boss data

## `App/Resources/Levels/level_NN.json`

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
| `platforms[]` | Optional one-way ledges: `at` (left end), `width`, `y` (top above ground, 4–44), `mode`, `kind` (look only, also the sprite name: `bridge`, `ice_ledge`, `vanish`). The hero lands on them from above, jumps up through them, and can stand on them over a ravine |
| `platforms[].mode` | `solid`; `crumbles` (gone for good `crumbleAfter` s after the first landing, default 0.5); `blinks` (there for `solidFor` of every `period` s on the world clock, default 1.6 of 2.4, flickering for the last 0.4; `offset` shifts it) |

Walking off the end of a ledge, or standing on one as it goes, drops the hero; a Double Pounce is
still possible then. Running off the rim of a ravine on the ground allows no jump at all.

### Item kinds

| World | Kind | Behaviour |
| --- | --- | --- |
| forest | `bush`, `stump` | Static terrain (low-wide / tall) |
| forest | `squirrel` | Walker; a stomp kills |
| forest | `acorn` | Fast low roller |
| forest | `branch_squirrel` | Sits 44 up, lobs `acorn` hazards that land and roll on along the ground |
| forest | `hedgehog` | Walker; within 90 of the hero it curls up: then no stomp, and yarn bounces off |
| frost | `icicle` | Hangs 70 up; 130 from the hero it blinks 0.35 s, drops, and lies as low shards (14×6) |
| frost | `snowball` | Fast roller, 2 HP |
| frost | `penguin` | Very fast slider; stomp is a safe bounce |
| frost | `snowdrift` | Static, low |
| haunted | `ghost_cat` | Drifts in high and down to the ground; visible 1.2 s of every 2 s and harmless otherwise; yarn passes through |
| haunted | `bat` | Flies at 40, swoops to 18 (just over a standing kitten) as it nears |
| haunted | `skeleton_mouse` | Stands and throws low `bone` hazards; stomp kills; 2 HP |
| haunted | `skull` | Flies straight in at 18, just over a standing kitten |
| haunted | `bell` | Hangs 56 up, harmless; every 2 s in range it sends a low `soundwave` hazard along the ground |
| haunted | `tombstone` | Static, tall |
| citadel | `vent` | Flame column (60 high) for 0.8 s of every 2.4 s, blinking 0.5 s before; harmless otherwise |
| citadel | `piston` | Slams (70 high) for 0.6 s of every 2 s, blinking 0.4 s before; harmless otherwise |
| citadel | `cannon` | Mounted 24 up, fires `cannonball` hazards at 20 (just over a standing kitten); 2 HP |
| citadel | `debris` | As `icicle` |
| citadel | `mech_mouse` | Fast chaser, 2 HP; stomp is a safe bounce |
| citadel | `gear` | Static, tall |
| citadel | `crate_wall` | 120 high: only a Super Pounce breaks it (needs hero level 5); yarn bounces off |
| any | `fish` | +5 XP and +1 fish |
| any | `yarn_basket` | Raises the hero to `shrineLevel` |

Ghost Dash (level 4) passes through creatures, thrown things and traps for 0.35 s, but not through
terrain (`bush`, `stump`, `snowdrift`, `tombstone`, `gear`, `crate_wall`) or over ravines. A Super
Pounce (level 5) defeats any walker or roller it touches and breaks a `crate_wall`.
| `ravines[]` | Optional gaps in the ground: `at` is the left rim, `width` how far it spans. Needs sprites `ravine_<theme>`, `ravine_<theme>_fill` and `ravine_<theme>_deep` |

Useful numbers: the kitten's hitbox is 18 wide and 16 tall. A full jump is 50 high and lasts
0.67 s, so it covers `speed × 0.67` units (≈ 74 at speed 110). A tap hop is about 10 high. A full
jump plus a Double Pounce at its top lasts about 1.08 s. A Super Pounce is 32 high, lasts 0.53 s
and adds 140 to the speed while in the air. Leave roughly 110+ units between ground threats.

Ravines: a fall ends the run, so the validator caps `width` at 65% of a full jump's reach (47 at
speed 110, 60 at 140), or of a jump plus Double Pounce once `entryHeroLevel` is 3 or more (≈ 84 at
speed 120), plus the length of any platforms over it; it wants at least 16. Keep them out of the start runway and the last 60
units, leave 40 of ground between two of them, and put nothing that stands on the ground inside
one (coins above are fine). Walking enemies turn back at a rim, so one placed between two ravines
patrols the ledge. To have a walker turn where the player can watch, start it far enough from the
rim that it arrives about two seconds after it spawns (a goblin about 45 units, a hound about 90).

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
- An attack runs `telegraph` → `duration` (hazards and `summons` spawn at their `delay`) → `recover`.
- Hazard `y` is its bottom edge: `0` makes a low hazard to jump, `42` a high one to run under
  (the kitten's hitbox is 18 wide and 16 tall, so anything below 16 hits it standing).
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
the boss pattern is the problem.
