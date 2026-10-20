# Game design — Purrfectly Dangerous

A kitten runs automatically across four worlds to win back the Sacred Fish. Each world ends in a
three-phase boss fight and gives the kitten a new ability. The source concept and style sheet are in
`docs/concept/`; this file is the version the game actually builds, and it wins where they differ.

First-release scope (concept §8): four worlds, four bosses, four abilities, fish, medals, endless
mode. **Not yet**: mini-bosses, upgrade shop, Nine Lives, Catnip Frenzy, cutscenes, the extra
encounters (§3) and the special bosses (§4).

## Loop and controls

The kitten runs automatically; the level scrolls toward it at the level's speed.

| Input | Action |
| --- | --- |
| Jump button (bottom right) | Jump. Hold for higher, release early for a short hop. |
| Jump again in the air | **Double Pounce** (kitten level 3+): a second, full-height jump. |
| Throw button (bottom left) | **Yarn Shot** (kitten level 2+): a ball of yarn thrown forward. |
| Paw button (above throw), tap | **Ghost Dash** (kitten level 4+): ~0.35 s intangible to enemies, projectiles and hazards (not to ravines). Cooldown ~1.5 s. |
| Paw button, hold then release | **Super Pounce** (kitten level 5): a long forward leap. Every walking/rolling enemy it touches is defeated and a `crate_wall` it touches breaks. Uses the charge timing the old charged shot used. |

The paw button only appears once Ghost Dash is unlocked.

Three hearts. A hit costs one and gives 1.2 s of immunity (the kitten blinks). Zero hearts ends the
run. Falling into a ravine (pit, chasm, lava) ends the run whatever hearts are left. Landing on top
of a stompable enemy bounces the kitten; enemies marked *stomp kills* are defeated by it.

## Progression

Fish are the pickups: each is +5 XP and +1 to the fish counter (score; shown in the HUD as `🐟 ×N`).
Enemies defeated by yarn or stomp give 10–40 XP.

| Kitten level | XP | Unlocks | Guaranteed by |
| --- | --- | --- | --- |
| 1 | 0 | — | — |
| 2 | 100 | Yarn Shot | `yarn_basket` shrine in world 1, before the boss |
| 3 | 300 | Double Pounce | beating world 1's boss |
| 4 | 600 | Ghost Dash | beating world 2's boss |
| 5 | 1000 | Super Pounce | beating world 3's boss |

This shifts the concept's reward table by one world so that every boss can be fought with yarn from
the start; the reward a boss *names* on the award card is the one it grants.

## Worlds

Ravines are gaps in the ground, themed per world (broken bridge, ice chasm, crypt pit, lava).
Walkers and rollers turn back at a rim. No ravines in a boss fight.

### Terrain: high and low ground

Levels can raise blocks of ground (mossy earth in the forest) or sink dips into it (`terrain` in
the level file). Everything stands on the ground where it is: the kitten, enemies, traps and fish.

- **Bump and stop.** Running into the face of a step higher than its feet stops the kitten (a squash
  and a puff of dust). The level waits: `distance`, scrolling and spawning stand still, while the
  clock, enemies, cycles and thrown things carry on. A jump that lifts the feet above the top gets it
  on. A lip of 4 or less is walked onto. A dip's far wall works the same way.
- Off the edge of a step the kitten drops to the lower ground with a Double Pounce still left, as
  off a ledge. Ghost Dash does not pass walls and Super Pounce does not break them.
- Walkers and rollers turn back at any step up or down, as at a ravine rim. Flyers keep their
  height above the ground below them. Things that fall land on the local ground.
- Thrown things and yarn break on the face of a step; a rolling acorn or spore drops off a step
  down and rolls on.
- Climbable: one jump climbs a step of up to 44; with Double Pounce (kitten level 3) up to 84. The
  validator checks every rise against the level guaranteed there and fails a level where the bot
  stands stuck for more than 4 s.
- The boss arena stays flat. Slick ground is base ground only. Raised blocks are at most 60 high and
  dips at most 32 deep, so both stay on screen (the camera does not move up or down).

### 1 — forest (speed 110, Easy)
| Id | Role | Behaviour | Beat it by |
| --- | --- | --- | --- |
| `bush` | thorny rose bush | static, low and wide | full jump |
| `stump` | tree stump | static, tall | jump |
| `squirrel` | squirrel soldier | walks toward the kitten | stomp (kills) or yarn, or jump |
| `acorn` | rolling acorn | small fast roller | hop |
| `branch_squirrel` | squirrel on a branch | stands up high, throws acorns that arc to the ground ahead | jump the acorn, or yarn it from a jump |
| `hedgehog` | hedgehog | walks; curls into a spiky ball when close (~90 units): curled, it can't be stomped and yarn bounces off | jump clear of it, or yarn/stomp before it curls |
| `slime` | forest slime | creeps slowly toward the kitten | stomp (kills), yarn, or hop |
| `mushroom_cat` | mushroom cat | stands still; puffs a spore from its cap that drops ahead of the kitten and rolls on along the ground | hop the spore; stomp (kills) or yarn |
| `forest_bat` | forest bat | flies in at head height and swoops, but never lower than just over a standing kitten (28) | stay down or jump late; yarn |
| `plant_cat` | biting plant | trap on a fixed cycle (world clock): shut and harmless, opens (warning), then bites; can't be stomped. Yarn hits it in any state, 2 HP | pass while shut, jump it, or 2 yarn |
| `bee_cat` | bee cat | hovers above head height (~40), drifting slowly in, firing stings low along the ground | jump the stings; yarn it from a jump |
| `stump_cat` | stump cat | terrain like `stump` (no Ghost Dash through it), a turret sending leaves along the ground, 2 HP | jump the leaves and the stump; 2 yarn |
| `snail_cat` | snail cat | crawls very slowly; hides in its shell when close (~80 units): hidden, it can't be stomped and yarn bounces off | jump it, or yarn/stomp before it hides |
| `spider_cat` | spider cat | hangs on a thread (~60 up), out of reach: harmless and yarn passes. When the kitten is ~130 away it blinks, drops ahead and walks in | stomp (kills) or yarn once down, or jump |
| `milk` | spilled milk (zone) | slick ground: run speed ×1.3 and no short hop while on it | timing |
| `bridge` | broken bridge plank (platform) | one-way platform over a ravine; **crumbles** 0.5 s after it is landed on | keep moving |

Boss `boss_squirrel` — **The Great Squirrel King**, always vulnerable, 20 HP.
1. Throws three acorns in a predictable arc (high/low mix).
2. Rolls across the arena leaving acorns behind (low rollers).
3. Climbs a tree and drops a giant acorn that makes a shockwave (blinking warning, then low wave).

### 2 — frost (speed 120, Medium)
| Id | Role | Behaviour | Beat it by |
| --- | --- | --- | --- |
| `ice` | ice patch (zone) | slick, as `milk` | timing |
| `icicle` | falling icicle | hangs from above; when the kitten is ~120 units away it blinks, then drops and shatters | pass before it falls, or wait |
| `snowball` | rolling snowball | fast roller, 2 HP | jump, or 2 yarn |
| `penguin` | sliding penguin | very fast belly-slider | jump/stomp (safe bounce, no kill) or yarn |
| `ice_ledge` | crumbling ice platform (platform) | crumbles 0.4 s after landing | keep moving |
| `snowdrift` | snow mound | static, low | hop |

Wide ravines (needing Double Pounce) appear here. Boss `boss_icedragon` — **Glacipurr**,
vulnerable only while recovering, 24 HP.
1. Ice shards in a fan (some high, some low).
2. Freezing breath sweep along the ground (low; jump it).
3. Ices the floor (slick for the rest of the attack), then dives from above (high; stay down).

### 3 — haunted (speed 130, Hard)
| Id | Role | Behaviour | Beat it by |
| --- | --- | --- | --- |
| `ghost_cat` | ghost cat | drifts toward the kitten, blinking in and out on a fixed cycle; only hurts while visible; yarn passes through | time it, or Ghost Dash |
| `bat` | swooping bat | flies at head height, swoops as it nears | stay down or jump late; yarn |
| `skeleton_mouse` | skeleton mouse | stands and throws bones low | jump the bones; stomp (kills) or 2 yarn |
| `skull` | floating skull | projectile flying straight at head height | stay down, or Ghost Dash |
| `bell` | cursed bell | hangs; every ~2 s rings a low sound wave along the ground | jump the waves |
| `tombstone` | gravestone | static, tall | jump |
| `vanish` | vanishing platform (platform) | solid/absent on a fixed cycle (world clock), blinking before it vanishes | time it |

Boss `boss_phantom` — **The Phantom Cat Queen**, always vulnerable, 26 HP, summons soak yarn.
1. Summons ghost cats that chase the kitten.
2. Teleports and sends spectral waves along the ground (low).
3. Splits into three copies; only the glowing one takes damage (others let yarn pass through).

### 4 — citadel (speed 140, Expert)
| Id | Role | Behaviour | Beat it by |
| --- | --- | --- | --- |
| `vent` | flame vent | fires a column of flame on a fixed on/off cycle, blinking before it fires | pass while off |
| `piston` | crushing piston | slams down on a cycle, blinking before | pass while up |
| `cannon` | wall cannon | fires fireballs at head height | stay down, Ghost Dash, or yarn (2 HP) |
| `debris` | falling ceiling debris | as `icicle` | pass before or after |
| `mech_mouse` | mechanical mouse | fast chaser; stomp is a safe bounce only | jump, yarn (2 HP), Super Pounce |
| `gear` | moving gear | static tall obstacle that spins (looks only) | jump |
| `crate_wall` | breakable wall | blocks the whole path up to jump height; only Super Pounce breaks it | Super Pounce |

Lava ravines everywhere. Boss `boss_mecha` — **The Mecha-Mouser**, 30 HP. Armored: until its HP is
at or below 40% it is hit only while recovering; then the core is exposed and phase 3 is fast.
1. Rockets that leave burning patches on the ground for a short time (low).
2. Tail sweep (low) while flame vents fire ahead (blinking warning).
3. Core exposed: rapid alternating high/low attacks with short openings.

## Pickups

| Id | Effect |
| --- | --- |
| `fish` | +5 XP, +1 fish |
| `yarn_basket` | raises the kitten to the level's `shrineLevel`; cannot be missed |

## Medals and endless

Medals as before (bronze/silver/gold → shown as 1–3 stars) for distance, enemies defeated and fish.
The START button begins an endless run through the four worlds in order, each with its boss, every
loop 15% faster up to ×2 (only the game clock changes, so the no-hit proof holds on every loop).
Scoring and saving as in the engine's `EndlessRun`.

## Names

Every displayed name — the title, tagline "One cat. Nine lives. Zero fish.", worlds, bosses,
abilities — lives in `App/Resources/Lore.json`, keyed by the role ids above.
