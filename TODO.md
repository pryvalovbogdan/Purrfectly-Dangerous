# To fix later

Open issues found while working on the game (October 2026). Each has where to look and how to check
it. Items marked *unverified* were noticed once and not confirmed. Follow `CLAUDE.md` when fixing:
rules in GameCore, art is code, check both orientations, and run `Tools/check.sh` at the end.

## Performance

- [ ] **0.2–0.3 s freeze when the Level Complete screen appears**, in every level. The boss-fight
      freezes are fixed (painted boss bar lettering cached, boss textures preloaded in
      `GameScene.preloadTextures()`); this one is separate. Likely the painted result screen images
      (`App/UI/ResultView.swift`, `CompleteLook`, the `*_complete_*` assets) or the result
      background decoding when the screen first shows. Decode them ahead of time, as
      `BossHealth.prepare` does for the boss bar.
      *Check:* record a level with `xcrun simctl io <dev> recordVideo` and count frozen frames
      around the level's end.

## Cats

- [ ] **Sharky's abilities: half done, never seen in the game.** The water-wave shot (`shot_wave`) and
      the water slide under him during a Ghost Dash (`water_slide`) are drawn in
      `Tools/sprites/characters/skin_abilities.py`. They're wired through the `skinLooks` table and
      `renderSlide()` in `App/Scenes/GameScene.swift`. Not yet checked in the simulator. Sharky isn't
      for sale, so give him to a test save: add `"sharky"` to `ownedSkins`, set `selectedSkin`, and set
      `giftsTakenBack: true` in `savegame.v1`.
- [ ] **Cabage's abilities, not started.** Yarn Shot should be a thrown cabbage (it spins, then bursts
      into leaves). Ghost Dash should be Cabage riding a curled cabbage leaf. Add both to `skinLooks` the
      same way as Sharky. The artist brief describes both (`docs/hero-sheet-brief.md`, "Sharky's
      water" and "Cabage's cabbages"). Cabage's KITTIES description already promises them ("lobs
      cabbages and rides a leaf"), so make them or change the text back before he goes on sale.
- [ ] **Preload the skin's shot sprite.** `preloadTextures()` loads only `yarn`. Load `skinLook.shot`
      as well, so the first water wave doesn't stall.
- [ ] **Cabage and Sharky are "not for sale"** (`Skin.available == false` in
      `Packages/GameCore/Sources/GameCore/Skins.swift`; the KITTIES screen shows COMING SOON). Open
      them when their art and abilities are done.
- [ ] **The KITTIES screen lists only some cats** (`shownCats` in `App/UI/CatsScreen.swift`, marked
      TEMPORARY). `Tools/release-check.sh` warns about it.
- [ ] **Sakura's hero sheet is mixed.** Idle, run and menu come from sheet v4; the other rows come from
      v3, which has a different style and winks in jump, fall, stop, throw, dash and ghost. A full v4
      sheet painted to `docs/hero-sheet-brief.md` would fix it.

## Bosses

- [ ] **Void Cat art gaps.** There is no painted hurt or defeat row. Hurt is idle knocked back, and
      defeat is a generated star dissolve with no "x x" eyes. The painted tail smoke and ear flames
      flicker between frames. A few frames of the shadow-paw and portal-paw attacks have straight cut
      edges. The shadow-paw projectile is dark on the dark floor. Upright, the paw thrusts reach almost
      to the kitten (they don't hit). See `docs/boss-voidcat-sheet-brief.md` for what a better sheet
      needs.
- [ ] **Other painted bosses have thin rows.** Some attacks play like slide shows, and there are no
      hurt rows. Mecha's core barrage, the Void Cat's portal and the phase changes would need their own
      Swift mapping (`attackAnimation` in `GameScene.swift`) if separate rows are painted.
- [ ] **The design doc and the code disagree.** Glacipurr's dive icing over, and the Queen's ghosts
      soaking up yarn, are described in `docs/game-design.md` but don't match what the game does.
      Decide which is right, then fix the other.
- [ ] **The Lantern Toad's rock stays after it is defeated** (Sakura route). *Unverified.*
- [ ] **Glacipurr's crest pokes through the boss bar.** *Unverified.*
- [ ] **The hell and rift hounds may run backwards** (`faces_left` not flipped). *Unverified.*

## Screens and HUD

- [ ] **Sky objects appear twice** (two suns, moons or black holes) and pass behind the pause button
      and HUD: frost, haunted, citadel, void, sakura_dusk and sakura_night.
- [ ] **Level Complete screens.**
  - Level 1 (forest), level 5 (void) and the Sakura levels still use the plain forest look; only
    frost, haunted and citadel have painted looks (`CompleteLook` in `App/UI/ResultView.swift`).
  - The stars are the small `MedalStars`, much smaller than the painted ones.
  - NEXT LEVEL is a little small on the haunted button.
  - The citadel card has a seam on its left post and a faint steam outline on the rebuilt bottom bar.
  - The rebuilt parchment shows faint banding.
- [ ] **The void level's shadow cat is hard to see.** *Unverified.*

## App Store

- [ ] **Version mismatch.** The app is `1.0.0` (`MARKETING_VERSION` in `project.yml`) but the App Store
      Connect version is `1.0`. Make them the same, or uploaded builds won't attach to that version.
- [ ] **The portrait screenshots and video are weak.** The lower 40% is ground and buttons, and bosses
      are cut off at the right edge. Prefer the landscape set, or reframe portrait.
- [ ] **The preview video doesn't open on the start screen.** It's edited by a throwaway AVFoundation
      script. If it's remade often, move that script into `Tools/store/`.
- [ ] **`Tools/store/header.py` is out of date.** It uses sprites that no longer exist (`fireball`,
      `hazard_frost`, `boss_dragon`, the hero `cast` animation). Fix it or delete it.
- [ ] **Store file names use display names** (`docs/store/screenshots/*_purrwood_forest.png`, …).
      Rename them if those names change in `Lore.json`.

## Tooling

- [ ] **`Tools/sprites/build.py <name>` builds every sprite module**, even when you name one, so it
      takes minutes. Make it build only the named modules.
- [ ] **The signing team ID is still in git history** (it's now read from `.env`). It isn't really a
      secret, since it's printed in every signed app. Removing it would mean rewriting history and
      force-pushing.
