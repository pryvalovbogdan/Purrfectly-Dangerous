# Game design — Purrfectly Dangerous

A kitten runs automatically across five worlds to win back the Sacred Fish. Each world ends in a
three-phase boss fight; the first four give the kitten a new ability, and the fifth, the void, is the
final world that tests them all. The source concept and style sheet are in
`docs/concept/`; this file is the version the game actually builds, and it wins where they differ.

First-release scope (concept §8, extended): four worlds and their bosses, plus the final void world
with the Void Cat (from the special bosses of §4), four abilities, fish, medals, endless mode.
**Not yet**: mini-bosses, upgrade shop, Nine Lives, Catnip Frenzy, cutscenes (the opening, and the
ending after the Void Cat: the golden crown, the mountain of fish and the mouse that steals the
throne), the extra encounters (§3) and the other special bosses (§4).

## Loop and controls

The kitten runs automatically; the level scrolls toward it at the level's speed.

| Input | Action |
| --- | --- |
| Jump button (bottom right) | Jump; **how long it is held decides how high** (a Mario-style variable jump). A press takes off at a modest speed: a tap peaks at about 24, enough for a bush or a low step. While the button stays held, gravity is reduced to a quarter for up to 0.28 s after take-off, so a full hold peaks at about 63 (a 0.1 s hold about 42, 0.2 s about 55). Letting go ends that boost at once, with no cut to the speed already gained; pressing again does not bring it back. There is no automatic full jump in front of steps: a tap bumps off a 40-high step, a hold climbs it. A jump from slick ground always gets the whole boost. A press on the way down from a jump (or a knock-back hop) is kept for 0.3 s, so tapping twice in a row hops again on landing. Dropping off a ledge or step keeps only the usual 0.1 s, so a press there is saved for the next obstacle instead of firing on touchdown. |
| Jump again in the air | **Double Pounce** (kitten level 3+): a second jump that always gets its whole boost, held or not (about 36 more; a full hold plus a Double Pounce at its top reaches about 98). |
| Throw button (bottom left) | **Yarn Shot** (kitten level 2+): a ball of yarn thrown forward. |
| Paw button (above throw), tap | **Ghost Dash** (kitten level 4+): ~0.35 s intangible to enemies, projectiles and hazards (not to ravines). Cooldown ~1.5 s. |
| Paw button, hold then release | **Super Pounce** (kitten level 5): a long forward leap. Every walking/rolling enemy it touches is defeated and a `crate_wall` it touches breaks. Uses the charge timing the old charged shot used. |

The paw button only appears once Ghost Dash is unlocked.

Three hearts. A hit costs one and gives 1.2 s of immunity (the kitten blinks). Zero hearts ends the
run. Falling into a ravine (pit, chasm, lava) ends the run whatever hearts are left. Landing on top
of a stompable enemy bounces the kitten; enemies marked *stomp kills* are defeated by it. Props with a
flat top (`stump`, `stump_cat`, `tombstone`, `snowdrift`) and dormant statues (`cursed_armor` asleep,
`gargoyle_cat` perched) are the same: landing on top is a safe bounce, and running into a prop's side
still hurts. Thorns (`bush`), gears and crate walls hurt from any side.

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

- **Bump back.** Running into the face of a step more than 4 above its feet, on the ground or in
  the air, knocks the kitten back: a squash, dust kicked off the face, and 0.26 s moving backwards at
  120 units/s (with a small hop if it was on the ground; a Double Pounce is still there). `distance`
  shrinks meanwhile and the scenery scrolls back. It then holds its place until it lands (or jumps
  again) and runs on, with a fresh run-up of about 31: enough for a held jump pressed on the way down
  to climb a 44 step at speed 140. No heart is lost and the immunity timer is untouched. The knockback
  never carries the kitten's middle over a ravine (it stops at the rim) nor its back into the face of
  a higher step behind. A lip of 4 or less is walked onto. A dip's far wall works the same way.
- Off the edge of a step the kitten drops to the lower ground with a Double Pounce still left, as
  off a ledge. Ghost Dash does not pass walls and Super Pounce does not break them.
- Walkers and rollers turn back at any step up or down, as at a ravine rim. Flyers keep their
  height above the ground below them. Things that fall land on the local ground.
- Thrown things and yarn break on the face of a step; a rolling acorn or spore drops off a step
  down and rolls on.
- Climbable: one held jump climbs a step of up to 58; with Double Pounce (kitten level 3) any step
  allowed (blocks are at most 60). The
  validator checks every rise against the level guaranteed there, and fails a level where the bot
  bounces off the same face more than 3 times, is held back by one for more than 4 s (from the first
  bounce until it is past the face), or makes no progress at all for 4 s.
- The boss arena stays flat. Slick ground is base ground only. Raised blocks are at most 60 high and
  dips at most 32 deep, so both stay on screen (the camera does not move up or down).

### 1 — forest (speed 110, Easy)
| Id | Role | Behaviour | Beat it by |
| --- | --- | --- | --- |
| `bush` | thorny rose bush | static, low and wide | full jump |
| `stump` | tree stump | static, tall; its top is a safe bounce | jump (or bounce off its top) |
| `squirrel` | squirrel soldier | walks toward the kitten | stomp (kills) or yarn, or jump |
| `acorn` | rolling acorn | small fast roller | hop |
| `branch_squirrel` | squirrel on a branch | stands up high, throws acorns that arc to the ground ahead | jump the acorn, or yarn it from a jump |
| `hedgehog` | hedgehog | walks; curls into a spiky ball when close (~90 units): curled, it can't be stomped and yarn bounces off | jump clear of it, or yarn/stomp before it curls |
| `slime` | forest slime | creeps slowly toward the kitten | stomp (kills), yarn, or hop |
| `mushroom_cat` | mushroom cat | stands still; puffs a spore from its cap that drops ahead of the kitten and rolls on along the ground | hop the spore; stomp (kills) or yarn |
| `forest_bat` | forest bat | flies in at head height and swoops, but never lower than just over a standing kitten (28) | stay down or jump late; yarn |
| `plant_cat` | biting plant | trap on a fixed cycle (world clock): shut and harmless, opens (warning), then bites; can't be stomped. Yarn hits it in any state, 2 HP | pass while shut, jump it, or 2 yarn |
| `bee_cat` | bee cat | hovers above head height (~40), drifting slowly in, firing stings low along the ground | jump the stings; yarn it from a jump |
| `stump_cat` | stump cat | terrain like `stump` (no Ghost Dash through it), a turret sending leaves along the ground, 2 HP. Its top is a safe bounce (no kill); its sides and leaves hurt | jump the leaves and the stump (or bounce off its top); 2 yarn |
| `snail_cat` | snail cat | crawls very slowly; hides in its shell when close (~80 units): hidden, yarn bounces off and so does the kitten: landing on the shell is a safe bounce that doesn't defeat it | jump or bounce over it, or yarn/stomp before it hides |
| `spider_cat` | spider cat | hangs on a thread (~60 up), out of reach: harmless and yarn passes. When the kitten is ~130 away it blinks, drops ahead and walks in | stomp (kills) or yarn once down, or jump |
| `milk` | spilled milk (zone) | slick ground: run speed ×1.3 and no short hop while on it | timing |
| `bridge` | broken bridge plank (platform) | one-way platform over a ravine; **crumbles** 0.5 s after it is landed on | keep moving |

Boss `boss_squirrel` — **The Great Squirrel King**, always vulnerable, 20 HP.
1. Throws three acorns in a predictable arc (high/low mix).
2. Rolls across the arena leaving acorns behind (low rollers).
3. Climbs a tree and drops a giant acorn that makes a shockwave (blinking warning, then low wave).

### 2 — frost (speed 120, Medium)
The creature roster follows the expanded concept, `docs/concept/Purrfectly_Dangerous_Game_Concept_Expanded.txt`
§9 (World 2 — Frostpaw Mountains), and its sprite sheet `docs/concept/Frostpaw Mountains Enemy Sprite Sheet.png`.

| Id | Role | Behaviour | Beat it by |
| --- | --- | --- | --- |
| `ice` | ice patch (zone) | slick, as `milk` | timing |
| `icicle` | falling icicle | hangs from above; when the kitten is ~130 units away it blinks, then drops and shatters | pass before it falls, or wait |
| `snowball` | rolling snowball | fast roller, 2 HP | jump, or 2 yarn |
| `penguin` | sliding penguin | very fast belly-slider | jump/stomp (safe bounce, no kill) or yarn |
| `snowdrift` | snow mound | static, low; its top is a safe bounce | hop |
| `ice_slime` | ice slime | hops along toward the kitten (the hop is only drawn; it stays on the ground) | stomp (kills), yarn, or hop |
| `snow_cat` | snow cat | fast runner; its paw slash is its body, so touching it from the side hurts. 2 HP | stomp (kills), 2 yarn, or jump |
| `ice_bat` | ice bat | swoops as it nears, never lower than just over a standing kitten (28) | stay down; yarn |
| `ice_golem` | small ice golem | slow, tough walker, 3 HP; landing on it is a safe bounce that doesn't break it. Needs kitten level 3 | jump/Double Pounce or bounce over it, or 3 yarn |
| `penguin_soldier` | penguin soldier | marches back and forth about 30 either side of its post; within ~70 it thrusts its spear (a short, fast, low stab), 2 HP | jump it early, stomp (kills), or 2 yarn |
| `snowy_owl` | snowy owl | hovers ~60 up, drifting in; it blinks, then drops an icicle straight down ahead of the kitten, which lies there as a spike. Can't be stomped | hop the icicle; yarn it from a jump |
| `ice_hedgehog` | ice hedgehog | walks; curls up when close (~100 units) and then rolls in fast (110), turning back at steps and rims. Curled, it can't be stomped and yarn bounces off | jump it, or yarn/stomp before it curls |
| `snowman` | snowman | stands and lobs snowballs that land ahead and roll on; a stomp is only a bounce. 2 HP | hop the snowballs, jump it, or 2 yarn |
| `icicle_plant` | icicle plant | trap like `plant_cat`: shut and harmless, opening (warning), then open: it hurts and fires an icicle bolt low along the ground each time it opens. Yarn hits it in any state, 2 HP | jump the bolt; pass while shut or jump it; 2 yarn |
| `mini_yeti` | mini yeti | slow bruiser with a wide swipe (a wide hitbox), 4 HP; can't be stomped. Needs kitten level 3 | Double Pounce over it, or 4 yarn |
| `ice_ledge` | crumbling ice platform (platform) | crumbles 0.4 s after landing | keep moving |

The rosters of worlds 3 and 4 likewise follow §9 of the expanded concept.

Wide ravines (needing Double Pounce) appear here. Boss `boss_icedragon` — **Glacipurr**,
vulnerable only while recovering, 24 HP.
1. Ice shards in a fan (some high, some low).
2. Freezing breath sweep along the ground (low; jump it).
3. Ices the floor (slick for the rest of the attack), then dives from above (high; stay down).

### 3 — haunted (speed 130, Hard)
The creature roster follows the expanded concept §9 (World 3 — The Haunted Meowseum) and its sheet
`docs/concept/Haunted Meowseum Enemy Sprite Showcase.png`. The concept's mini-boss, the Bone Mouse
Captain, is future work (no mini-bosses yet).

| Id | Role | Behaviour | Beat it by |
| --- | --- | --- | --- |
| `ghost_cat` | ghost cat | drifts toward the kitten, blinking in and out on a fixed cycle; only hurts while visible; yarn passes through. While visible it throws a spirit ball every ~2.4 s, straight at head height (26), just over a standing kitten | time it, or Ghost Dash; stay down for the spirit balls |
| `bat` | bat cat | flies at head height, swoops as it nears (unchanged; restyled) | stay down or jump late; yarn |
| `haunted_portrait` | haunted portrait | a flying frame hovering just over a standing kitten (32), drifting in, firing low magic shots; 2 HP | jump the shots; 2 yarn from a hop |
| `cursed_armor` | cursed armor cat | a harmless knight statue (yarn bounces off) until the kitten is within ~140; it flashes 0.5 s, wakes and walks in; asleep, landing on it is a safe bounce; awake, touching it hurts (no stomp), 3 HP. Needs kitten level 3 | Double Pounce over it, or 3 yarn once awake |
| `candle_cat` | candle cat | slow walker sending fire orbs along the ground; the flame on its head burns a stomper | jump the orbs and it; yarn |
| `poltergeist_book` | poltergeist book | floats high (48), drifting in, lobbing magic bolts that land ahead of the kitten and fizzle out | don't jump into a falling bolt; yarn from a full jump |
| `gargoyle_cat` | gargoyle cat | perched stone, harmless (yarn bounces off, landing on it is a safe bounce) until the kitten is ~240 away; it flashes 0.5 s, leaps ~70 toward the kitten, lands ahead of it and walks in. In the air and after, touching it hurts; landing on it is a safe bounce, 2 HP | jump or bounce over it; 2 yarn once down |
| `shadow_cat` | shadow cat | unseen and intangible until the kitten is within ~180; then it appears 80 ahead of the kitten, flashes 0.4 s (keeping that distance) and dashes in fast | jump it as it dashes (a stomp kills), or yarn it once it is visible |
| `skeleton_mouse` | skeleton mouse | stands and throws bones low | jump the bones; stomp (kills) or 2 yarn |
| `skull` | floating skull | projectile flying straight at head height | stay down, or Ghost Dash |
| `bell` | cursed bell | hangs; every ~2 s rings a low sound wave along the ground | jump the waves |
| `tombstone` | gravestone | static, tall; its top is a safe bounce | jump (or bounce off its top) |
| `vanish` | vanishing platform (platform) | solid/absent on a fixed cycle (world clock), blinking before it vanishes | time it |

Boss `boss_phantom` — **The Phantom Cat Queen**, always vulnerable, 26 HP, summons soak yarn.
1. Summons ghost cats that chase the kitten.
2. Teleports and sends spectral waves along the ground (low).
3. Splits into three copies; only the glowing one takes damage (others let yarn pass through).

### 4 — citadel (speed 140, Expert)
The creature roster follows the expanded concept §9 (World 4 — The Cataclysm Citadel) and its sheet
`docs/concept/Cataclysm Citadel Enemy Sprite Sheet.png`. The kitten enters at level 5, with every
ability. The concept's mini-boss, the Iron Bulldog, is future work (no mini-bosses yet).

| Id | Role | Behaviour | Beat it by |
| --- | --- | --- | --- |
| `vent` | flame vent | fires a column of flame on a fixed on/off cycle, blinking before it fires | pass while off |
| `piston` | crushing piston | slams down on a cycle, blinking before | pass while up |
| `cannon` | wall cannon | fires fireballs at head height | stay down, Ghost Dash, or yarn (2 HP) |
| `debris` | falling ceiling debris | as `icicle` | pass before or after |
| `mech_mouse` | mechanical mouse | fast chaser; stomp is a safe bounce only | jump, yarn (2 HP), Super Pounce |
| `gear` | moving gear | static tall obstacle that spins (looks only) | jump |
| `crate_wall` | breakable wall | blocks the whole path up to jump height; only Super Pounce breaks it | Super Pounce |
| `lava_slime` | lava slime | slow walker; spits lava globs that land ahead and burn as a puddle for about a second. Molten: no stomp | hop the puddle and it; yarn |
| `fire_imp` | fire imp | hovers above a standing kitten (40) and keeps 140 ahead of it for 3 s, firing low fireballs, then drifts in | jump the fireballs; yarn from a hop |
| `stone_guard` | stone guard cat | slow armoured walker, 4 HP; landing on it is a safe bounce. Close up (within 60) it punches out a short, low magma blast. Needs kitten level 3 | jump or bounce over it early; 4 yarn |
| `hell_hound` | hell hound cat | a chase: when the kitten reaches its spot it is heard coming (it flashes at the left edge), then it runs in from behind, 130 faster than the kitten, past it and away. Burns on any touch, 2 HP | jump it as it passes; Super Pounce |
| `ember_bat` | ember bat | swoops like the ice bat, never lower than just over a standing kitten (28), trailing sparks | stay down; yarn |
| `flame_archer` | flame archer cat | stands (on ledges) and shoots low flame arrows; 2 HP, a stomp kills | jump the arrows; stomp or 2 yarn |
| `chainsaw_cat` | chainsaw cat | slow elite walker, 5 HP; its chainsaw reaches 20 in front of its body and hurts like it. No stomp. Needs kitten level 5 | Super Pounce through it, or 5 yarn |
| `fire_wisp` | fire wisp | floats in low (20); within 50 it flashes for 0.5 s, keeping that distance, then bursts into a ring of fire on the ground (40 wide) for 0.4 s | hop the ring, Ghost Dash through it, or yarn it from a hop first |

Lava ravines everywhere. Boss `boss_mecha` — **The Mecha-Mouser**, 30 HP. Armored: until its HP is
at or below 40% it is hit only while recovering; then the core is exposed and phase 3 is fast.
1. Rockets that leave burning patches on the ground for a short time (low).
2. Tail sweep (low) while flame vents fire ahead (blinking warning).
3. Core exposed: rapid alternating high/low attacks with short openings.

### 5 — void (speed 150, Final)
The final world. The creature roster follows the expanded concept's "Final Level — The Void Cat"
roster and its sheet `docs/concept/The Void Cat_ Final Boss Sprite Sheet.png`; the boss follows §4
(the Void Cat: shadow paws, falling stars and portals that confuse projectile direction, and a final
phase that tests the abilities). The kitten enters at level 5 (every ability) and the boss grants
nothing new (`bossRewardLevel` 5). In an endless run it comes after level 4, and the run loops all
five worlds; like every level, it opens for play on its own once beaten there. `level_05.json` is a placeholder for the level designer.

| Id | Role | Behaviour | Beat it by |
| --- | --- | --- | --- |
| `void_slime` | void slime | lurches in on the world clock (0.5 s moving, 0.5 s still), spitting low void orbs; burns a stomper | jump the orbs and it; yarn |
| `void_bat` | void bat | swoops to just over a standing kitten (28) and fires void orbs at head height (30) | stay down; yarn from a hop |
| `void_sentinel` | void sentinel | floats at 36; charges for 0.8 s (it flashes), then a long low void laser (30 wide); 3 HP | jump the laser; 3 yarn from hops |
| `rift_hound` | rift hound | a faster hell hound: 0.45 s warning, then in from behind at 170 over the run speed | jump it as it passes |
| `void_mage` | void mage | stands; every 3 s, by turns, summons a void wisp 80 ahead of the kitten or fires a low void bolt; 3 HP, a stomp kills | jump the bolts; stomp, or 3 yarn |
| `rift_turret` | rift crystal | hovers at 20 (in the kitten's way); charges for 1 s (it flashes), then a fast low crystal shot; 2 HP | jump the shot, then it |
| `void_wisp` | void wisp | floats at 30, drifting in; every 2.5 s a homing orb that steers toward the kitten's middle at up to 40 units/s while it is still ahead | jump late (it can't climb that fast), or Ghost Dash |
| `mini_void_cat` | mini void cat | a shadow cat that, once its dash has passed the kitten, appears 80 ahead once more and dashes again; a stomp kills | jump or stomp each dash, or Ghost Dash |

Boss `boss_voidcat` — **The Void Cat**, 30 HP (placeholder tuning for the level designer).
1. Shadow paws sweeping along the ground (low), and falling stars: each blinks where it will fall
   (fixed on the ground ahead), then drops and shatters.
2. Portals: a pair opens for a while, the entry just ahead of the kitten and the exit further on and
   higher. Yarn that flies into the entry comes out of the exit (once per ball), at the same height
   within it, so it reaches the boss from an unexpected height; a portal may also send yarn back.
   The kitten itself passes through portals.
3. **The final phase needs the abilities.** Yarn is shrugged off unless the boss is *exposed*. The
   kitten exposes it by using a Ghost Dash or a Super Pounce through an attack: while dashing or
   pouncing, an armed hazard is level with the kitten (overlapping it along the run, at any height).
   The boss then stays exposed for `openingTime` (2 s) and yarn lands. (`phases[].requires` lists
   the abilities that count.)

## Pickups

| Id | Effect |
| --- | --- |
| `fish` | +5 XP, +1 fish |
| `yarn_basket` | raises the kitten to the level's `shrineLevel`; cannot be missed |

## Medals and endless

Medals as before (bronze/silver/gold → shown as 1–3 stars) for distance, enemies defeated and fish.
The START button begins an endless run through the five worlds in order, each with its boss, every
loop 15% faster up to ×2 (only the game clock changes, so the no-hit proof holds on every loop).
Scoring and saving as in the engine's `EndlessRun`.

## Cats and the fish wallet

Every fish picked up goes into a **fish wallet** kept in the save. A level banks its fish when it
ends, won or lost, played on its own or as part of an endless run. (A level left part-way with QUIT
banks nothing; bot runs never bank.) The per-level best scores and medals are kept as before; the
wallet is separate and only ever spent in the CATS shop. Saves from before the wallet start at 0.

The CATS screen sells cats, paid for from the wallet. A cat is **purely cosmetic**: it changes how
the kitten looks and nothing else (the simulation never sees it).

| Id | Price (fish) |
| --- | --- |
| `fluffy` | 0 (everyone's from the start) |
| `shadow` | 150 |
| `misty` | 200 |
| `sakura` | 250 |
| `honey` | 300 |
| `pixie` | 400 |
| `clover` | 500 |
| `snowball` | 600 |
| `napster` | 750 |
| `toffee` | 900 |
| `cabage` | 2000 |
| `sharky` | 2000 |

- Unlocking needs the full price in the wallet; it takes the fish and owns the cat for good. With too
  few fish, nothing changes and the shop says how many are missing. A cat already owned can't be
  bought again.
- Only an owned cat can be selected. The cat in use is saved; saves from before the shop (whose one
  cat was "orange") load with Fluffy owned and selected.
- The catalog and rules are `Skin` and `SaveGame.unlock(skin:)` / `select(skin:)` in GameCore. Names
  and one-line descriptions are in Lore.json as `skin.<id>.name` and `skin.<id>.desc`.

## Names

Every displayed name — the title, tagline "One cat. Nine lives. Zero fish.", worlds, bosses,
abilities — lives in `App/Resources/Lore.json`, keyed by the role ids above.
