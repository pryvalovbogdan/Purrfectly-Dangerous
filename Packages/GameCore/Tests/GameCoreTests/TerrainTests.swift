import Foundation
import Testing
@testable import GameCore

/// Raised blocks and dips: the hero stops against their faces, things stand on the local ground,
/// walkers turn at steps and thrown things break on them.
@Suite struct TerrainTests {
    func hero(_ level: Int) -> HeroStats { HeroStats(xp: Progression.xp(forLevel: level)) }

    func level(_ terrain: [Terrain], items: [PlacedItem] = [], length: Double = 2000, entry: Int = 1,
               reward: Int = 2) -> LevelDefinition {
        var level = flatLevel(items: items, length: length, entry: entry, reward: max(reward, entry))
        level.terrain = terrain
        return level
    }

    @discardableResult
    func advance(_ world: inout RunnerWorld, limit: Double = 10, _ input: Input = Input(),
                 until condition: (RunnerWorld) -> Bool) -> [GameEvent] {
        var events: [GameEvent] = []
        let end = world.time + limit
        while !condition(world), world.time < end, !world.isOver { events += world.step(input, dt: dt) }
        return events
    }

    func hit(_ events: [GameEvent]) -> Bool {
        events.contains { if case .heroHit = $0 { true } else if case .heroDied = $0 { true } else { false } }
    }

    // MARK: - Ground

    @Test func groundHeightFollowsBlocksAndDips() {
        let ground = GroundProfile([Terrain(at: 300, width: 40, height: 20), Terrain(at: 340, width: 40, height: 36),
                                    Terrain(at: 600, width: 50, height: -20)])
        #expect(ground.height(at: 299) == 0)
        #expect(ground.height(at: 300) == 20)
        #expect(ground.height(at: 340) == 36)
        #expect(ground.height(leftOf: 340) == 20)
        #expect(ground.height(at: 380) == 0)
        #expect(ground.height(at: 620) == -20)
        #expect(ground.highest(from: 290, to: 306) == 20)
        #expect(ground.highest(from: 590, to: 606) == 0)
        #expect(ground.lowest(from: 590, to: 606) == -20)
        #expect(ground.lowest(from: 610, to: 626) == -20)
        // Rises the hero meets: up onto each stair, and out of the dip.
        #expect(ground.rises(step: 4).map(\.at) == [300, 340, 650])
    }

    @Test func terrainIsReadFromLevelData() throws {
        let json = #"{"id":"l","nameKey":"k","background":"forest","speed":110,"length":900,"entryHeroLevel":1,"boss":"b","bossRewardLevel":2,"items":[],"terrain":[{"at":300,"width":64,"height":24},{"at":500,"width":40,"height":-16}]}"#
        let level = try ContentLoader.level(from: Data(json.utf8))
        #expect(level.terrain == [Terrain(at: 300, width: 64, height: 24), Terrain(at: 500, width: 40, height: -16)])
    }

    // MARK: - Hero

    /// A tap: pressed and already released by the first step, as a quick thumb on the button is.
    func tap(_ world: inout RunnerWorld) -> Double {
        var top = world.heroY
        _ = world.step(Input(jumpPressed: true, jumpHeld: false), dt: dt)
        while !world.onGround, !world.isOver {
            _ = world.step(Input(), dt: dt)
            top = max(top, world.heroY)
        }
        return top
    }

    /// The same, with the button held for `hold` seconds after the press.
    func jump(_ world: inout RunnerWorld, hold: Double) -> Double {
        var top = world.heroY
        var elapsed = 0.0
        _ = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        while !world.onGround, !world.isOver {
            elapsed += dt
            _ = world.step(Input(jumpHeld: elapsed < hold), dt: dt)
            top = max(top, world.heroY)
        }
        return top
    }

    @Test func aQuickTapHopsALowStep() {
        var flat = RunnerWorld(level: flatLevel(), boss: nil)
        _ = flat.run(0.5)
        let top = tap(&flat)
        #expect(top >= 22)
        #expect(top < Tuning().jumpApex - 25)   // far shorter than a held jump
        // Level 1's 16-high steps are hopped onto with a tap.
        var world = RunnerWorld(level: level([Terrain(at: 300, width: 100, height: 16)]), boss: nil)
        advance(&world) { $0.distance >= 300 - 8 - 24 }
        _ = tap(&world)
        #expect(world.heroY == 16)
    }

    /// No safety net in front of tall steps: the player decides. A tap bumps off a 40-high step; a
    /// held jump from the same spot climbs it.
    @Test func nearATallStepATapFallsShortAndAHoldClimbs() {
        var tapped = RunnerWorld(level: level([Terrain(at: 300, width: 100, height: 40)]), boss: nil)
        advance(&tapped) { $0.distance >= 300 - 8 - 30 }
        var held = tapped
        var events: [GameEvent] = []
        _ = tapped.step(Input(jumpPressed: true), dt: dt)
        events += advance(&tapped, limit: 2) { $0.onGround }
        #expect(events.contains(.bumped))
        #expect(tapped.heroY == 0)

        #expect(jump(&held, hold: 1) >= 40)
        #expect(held.heroY == 40)
    }

    @Test func aHeldJumpBeforeALowStepStillGoesHigh() {
        var tapped = RunnerWorld(level: level([Terrain(at: 300, width: 100, height: 16)]), boss: nil)
        advance(&tapped) { $0.distance >= 300 - 8 - 30 }
        var held = tapped
        let hop = tap(&tapped)
        #expect(tapped.heroY == 16)                          // a tap gets onto the step
        #expect(jump(&held, hold: 1) > hop + 25)              // a hold still leaps well over it
    }

    @Test func aPressWhileDroppingOffAStepDoesNotFireOnLanding() {
        var world = RunnerWorld(level: level([Terrain(at: 240, width: 80, height: 16)],
                                             items: [.init(at: 430, kind: .bush)]), boss: nil)
        advance(&world) { 240 - $0.distance < 30 }
        _ = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        advance(&world, Input(jumpHeld: true)) { $0.onGround && $0.heroY == 16 }
        advance(&world) { !$0.onGround }                      // ran off the end of the step
        let early = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        let landing = advance(&world) { $0.onGround }
        #expect(!(early + landing + world.step(Input(), dt: dt)).contains(.jumped(double: false)))
        // Pressed again in good time, the bush is cleared.
        advance(&world) { 430 - $0.distance < 35 }
        var events = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        events += advance(&world, Input(jumpHeld: true)) { $0.distance > 470 }
        #expect(!hit(events))
    }

    /// Runs into the face at 300 (40 high) and returns the events up to and including the hit.
    func runIntoWall(_ world: inout RunnerWorld) -> [GameEvent] {
        advance(&world) { $0.isAgainstWall }
    }

    @Test func runningIntoAWallKnocksTheHeroBackWithoutHarm() throws {
        var world = RunnerWorld(level: level([Terrain(at: 300, width: 100, height: 40)]), boss: nil)
        let events = runIntoWall(&world)
        #expect(events.filter { $0 == .bumped }.count == 1)
        #expect(world.lastBumpFace == 300)
        let contact = world.distance
        #expect(abs(contact - (300 - world.tuning.heroWidth / 2)) < 1e-6)
        // A small hop back, with the Double Pounce still there.
        #expect(!world.onGround)
        #expect(world.isBumpedBack)
        // Knocked back by about bumpBack × bumpBackSpeed, moving backwards on screen too.
        world.run(0.05)
        #expect(world.runSpeed < 0)
        #expect(!world.isAgainstWall)
        advance(&world, limit: 2) { $0.onGround }
        let knock = world.tuning.bumpBack * world.tuning.bumpBackSpeed
        #expect(abs((contact - world.distance) - knock) < world.tuning.bumpBackSpeed * dt * 2)
        // No harm: no heart lost and no immunity.
        #expect(world.stats.hearts == 3)
        #expect(world.invulnerable == 0)
        // Then it runs on, and (without a jump) is knocked back again.
        let landedAt = world.distance
        let again = advance(&world, limit: 2) { $0.isAgainstWall }
        #expect(world.distance > landedAt)
        #expect(again.filter { $0 == .bumped }.count == 1)
    }

    @Test func aJumpPressedDuringTheKnockbackFiresOnLandingAndClearsTheStep() {
        // A 44-high step at the fastest level speed: the run-up the knockback gives back is enough
        // for a held jump to climb it.
        var level = level([Terrain(at: 300, width: 100, height: 44)])
        level.speed = 140
        var world = RunnerWorld(level: level, boss: nil)
        _ = runIntoWall(&world)
        // Pressed on the way down from the hop: kept until the feet touch down.
        advance(&world, limit: 1) { $0.heroVY < 0 }
        var events = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        events += advance(&world, limit: 2, Input(jumpHeld: true)) { $0.onGround && $0.heroY == 44 }
        #expect(events.contains(.jumped(double: false)))
        #expect(!events.contains(.bumped))
        #expect(world.heroY == 44)
        #expect(world.distance > 300)
    }

    @Test func aDoublePounceOnceKnockedBackClimbs() {
        var world = RunnerWorld(level: level([Terrain(at: 300, width: 100, height: 40)], entry: 3, reward: 3),
                                boss: nil, stats: hero(3))
        _ = runIntoWall(&world)
        // Pressed at the end of the knockback, from the hop: it carries on forward and over.
        advance(&world, limit: 1) { !$0.isBumpedBack }
        let events = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
            + advance(&world, limit: 2, Input(jumpHeld: true)) { $0.onGround }
        #expect(events.contains(.jumped(double: true)))
        #expect(!events.contains(.bumped))
        #expect(world.heroY == 40)
    }

    @Test func theKnockbackStopsAtARavineRimBehind() {
        // The kitten jumps a ravine and lands just short of a face: knocked back, it stops with its
        // middle on the rim instead of going over.
        var level = level([Terrain(at: 306, width: 100, height: 40)])
        level.ravines = [Ravine(at: 260, width: 30)]
        var world = RunnerWorld(level: level, boss: nil)
        advance(&world) { $0.distance > 225 }
        _ = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        let events = advance(&world, limit: 2, Input(jumpHeld: true)) { $0.isAgainstWall }
        #expect(events.contains(.bumped))
        advance(&world, limit: 2) { $0.onGround }
        #expect(abs(world.distance - 290) < 1e-6)
        #expect(!world.isOver)
        #expect(world.stats.hearts == 3)
    }

    @Test func theKnockbackStopsAgainstAHigherStepBehind() {
        // Off a 20 block into a trench 40 wide before a 60 one: knocked back, its back stops
        // against the face of the block it came down from.
        var world = RunnerWorld(level: level([Terrain(at: 0, width: 300, height: 20),
                                              Terrain(at: 340, width: 100, height: 60)]), boss: nil)
        #expect(world.groundHeight(at: 0) == 20)
        let events = advance(&world) { $0.isAgainstWall }
        #expect(events.contains(.landed))
        #expect(world.lastBumpFace == 340)
        advance(&world, limit: 2) { $0.onGround }
        #expect(abs(world.distance - (300 + world.tuning.heroWidth / 2)) < 1e-6)
        #expect(world.heroY == 0)
    }

    @Test func aLowLipIsWalkedOnto() {
        var world = RunnerWorld(level: level([Terrain(at: 300, width: 100, height: 4)]), boss: nil)
        let events = advance(&world) { $0.distance > 320 }
        #expect(!events.contains(.bumped))
        #expect(world.heroY == 4)
        #expect(world.onGround)
    }

    @Test func walkingOffAStepDropsToTheLowerGroundWithADoublePounceLeft() {
        var world = RunnerWorld(level: level([Terrain(at: 200, width: 100, height: 20)]), boss: nil, stats: hero(3))
        advance(&world) { $0.distance > 170 }
        _ = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        advance(&world, limit: 2, Input(jumpHeld: true)) { $0.onGround && $0.heroY == 20 }
        #expect(world.heroY == 20)
        advance(&world) { !$0.onGround }
        #expect(world.distance > 300)
        // Off the edge it can still Double Pounce.
        let events = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        #expect(events.contains(.jumped(double: true)))
        advance(&world, limit: 2, Input(jumpHeld: true)) { $0.onGround }
        #expect(world.heroY == 0)
        #expect(world.stats.hearts == 3)
    }

    @Test func aDipIsFallenIntoAndItsFarWallBouncesTheHero() {
        var world = RunnerWorld(level: level([Terrain(at: 300, width: 80, height: -24)]), boss: nil)
        advance(&world) { $0.isAgainstWall }
        #expect(world.lastBumpFace == 380)
        advance(&world, limit: 1) { $0.heroVY < 0 }
        _ = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        advance(&world, limit: 2, Input(jumpHeld: true)) { $0.onGround && $0.heroY == 0 }
        #expect(world.heroY == 0)
        #expect(world.distance > 380)
        #expect(!world.isOver)
    }

    @Test func ghostDashAndSuperPounceDoNotPassWalls() {
        let wall = [Terrain(at: 300, width: 100, height: 40)]
        var dasher = RunnerWorld(level: level(wall, entry: 4), boss: nil, stats: hero(4))
        advance(&dasher) { $0.distance > 280 }
        let events = dasher.step(Input(pawPressed: true), dt: dt) + dasher.run(0.5)
        #expect(events.contains(.dashed))
        #expect(events.contains(.bumped))
        #expect(dasher.distance <= 292 + 1e-6)

        var pouncer = RunnerWorld(level: level(wall, entry: 5), boss: nil, stats: hero(5))
        advance(&pouncer, Input(pawHeld: true)) { $0.distance > 240 }
        let leap = pouncer.step(Input(), dt: dt) + pouncer.run(1)
        #expect(leap.contains(.pounced))
        #expect(leap.contains(.bumped))
        #expect(pouncer.distance <= 292 + 1e-6)
    }

    @Test func yarnStopsAgainstAWall() {
        var world = RunnerWorld(level: level([Terrain(at: 400, width: 100, height: 40)]), boss: nil, stats: hero(2))
        advance(&world) { $0.distance > 300 }
        let events = world.step(Input(fireHeld: true), dt: dt) + world.run(0.6)
        #expect(events.contains { if case .yarnGone(_, hit: false) = $0 { true } else { false } })
        #expect(world.projectiles.isEmpty)
    }

    // MARK: - Things on terrain

    @Test func thingsStandOnTheLocalGround() throws {
        let items = [PlacedItem(at: 330, kind: .stump), PlacedItem(at: 360, kind: .fish, y: 30),
                     PlacedItem(at: 520, kind: .bush), PlacedItem(at: 700, kind: .icicle)]
        let terrain = [Terrain(at: 300, width: 100, height: 30), Terrain(at: 500, width: 50, height: -20),
                       Terrain(at: 680, width: 40, height: 16)]
        var world = RunnerWorld(level: level(terrain, items: items), boss: nil)
        advance(&world) { $0.entities.count == 4 }
        #expect(world.entities.first { $0.kind == .stump }?.y == 30)
        #expect(world.entities.first { $0.kind == .fish }?.y == 60)
        #expect(world.entities.first { $0.kind == .bush }?.y == -20)
        #expect(world.entities.first { $0.kind == .icicle }?.y == 86)
        #expect(world.groundHeight(at: 520) == -20)
    }

    @Test func aFallerDropsToTheLocalGround() throws {
        let terrain = [Terrain(at: 380, width: 60, height: 24)]
        var world = RunnerWorld(level: level(terrain, items: [PlacedItem(at: 400, kind: .icicle)]), boss: nil)
        advance(&world) { $0.entities.first?.state == .landed }
        #expect(try #require(world.entities.first).y == 24)
    }

    @Test func walkersTurnBackAtStepsUpAndDown() throws {
        // On top of a block: walks to its edge and turns back.
        let block = Terrain(at: 500, width: 120, height: 20)
        var onTop = RunnerWorld(level: level([block], items: [PlacedItem(at: 560, kind: .squirrel)]), boss: nil)
        advance(&onTop, limit: 6) { $0.entities.first?.reversed == true }
        var squirrel = try #require(onTop.entities.first)
        #expect(squirrel.reversed)
        #expect(squirrel.y == 20)
        #expect(abs(squirrel.x - (500 + ItemKind.squirrel.spec.width / 2)) < 2)

        // Below a block: walks back to its face and turns there.
        let ahead = Terrain(at: 500, width: 120, height: 20)
        var below = RunnerWorld(level: level([ahead], items: [PlacedItem(at: 680, kind: .squirrel)]), boss: nil)
        advance(&below, limit: 6) { $0.entities.first?.reversed == true }
        squirrel = try #require(below.entities.first)
        #expect(squirrel.reversed)
        #expect(squirrel.y == 0)
        #expect(abs(squirrel.x - (620 + ItemKind.squirrel.spec.width / 2)) < 2)

        // A roller in a dip stays in it.
        var dip = RunnerWorld(level: level([Terrain(at: 500, width: 100, height: -20)],
                                           items: [PlacedItem(at: 560, kind: .acorn)]), boss: nil)
        advance(&dip, limit: 3) { $0.entities.first?.reversed == true }
        let acorn = try #require(dip.entities.first)
        #expect(acorn.reversed)
        #expect(acorn.y == -20)
    }

    @Test func projectilesBreakOnTheFaceOfAStep() throws {
        // A stump cat's leaves (2 up) run along the ground into a lip (4 high) the kitten just walks onto.
        let items = [PlacedItem(at: 700, kind: .stumpCat)]
        var world = RunnerWorld(level: level([Terrain(at: 500, width: 100, height: 4)], items: items), boss: nil)
        let events = advance(&world, limit: 6.2) { _ in false }
        #expect(events.contains { if case .threw = $0 { true } else { false } })
        #expect(events.contains { if case .hazardBroke = $0 { true } else { false } })
        #expect(world.hazards.allSatisfy { $0.x > 600 })
    }

    @Test func aRollingAcornDropsOffAStepAndRollsOn() throws {
        // The branch squirrel sits on a block; its acorns land on it, roll off its edge and on below.
        let items = [PlacedItem(at: 560, kind: .branchSquirrel)]
        var world = RunnerWorld(level: level([Terrain(at: 400, width: 200, height: 16)], items: items), boss: nil)
        advance(&world) { $0.hazards.contains { $0.rolling && $0.x < 380 } }
        let acorn = try #require(world.hazards.first { $0.rolling && $0.x < 380 })
        #expect(acorn.y == 0)
    }

    // MARK: - Bot and validation

    func validate(_ level: LevelDefinition) -> [String] {
        LevelValidator.validate(level, bosses: [:]).problems.filter { !$0.contains("boss 'none'") }
    }

    @Test func theBotClimbsAStaircaseAndCrossesADip() {
        let stairs = [Terrain(at: 400, width: 60, height: 16), Terrain(at: 460, width: 60, height: 32),
                      Terrain(at: 520, width: 80, height: 44), Terrain(at: 600, width: 60, height: 20),
                      Terrain(at: 900, width: 90, height: -24)]
        let level = level(stairs, items: [PlacedItem(at: 560, kind: .slime), PlacedItem(at: 1200, kind: .squirrel)],
                          length: 1500)
        #expect(LevelValidator.terrainProblems(in: level, items: level.items, tuning: Tuning()).isEmpty)
        let run = LevelValidator.botRun(level, boss: nil)
        #expect(run.finished)
        #expect(run.blocked == nil)
    }

    @Test func aWallNeedingDoublePounceIsOnlyAllowedOnceItIsGuaranteed() {
        // One held jump climbs up to 58; the tallest block allowed (60) needs Double Pounce.
        #expect(LevelValidator.climbHeight(heroLevel: 2, tuning: Tuning()) == 58)
        let wall = [Terrain(at: 500, width: 120, height: 60)]
        let early = level(wall, length: 1200, entry: 2)
        #expect(LevelValidator.terrainProblems(in: early, items: [], tuning: Tuning())
            .contains { $0.contains("step at 500 rises 60; one jump at hero level 2 climbs at most 58") })

        let late = level(wall, length: 1200, entry: 3, reward: 3)
        #expect(LevelValidator.terrainProblems(in: late, items: [], tuning: Tuning()).isEmpty)
        #expect(LevelValidator.botRun(late, boss: nil).finished)

        // Behind a yarn basket that grants Double Pounce it is fine too.
        var shrine = level(wall, items: [PlacedItem(at: 300, kind: .yarnBasket)], length: 1200, entry: 1, reward: 3)
        shrine.shrineLevel = 3
        #expect(LevelValidator.terrainProblems(in: shrine, items: shrine.items, tuning: Tuning()).isEmpty)
    }

    @Test func aSoftlockIsReported() {
        // Too high even for a Double Pounce: the validator says so before the bot runs, and the bot
        // on its own gives up once it has bounced off the same face more than `maxBumps` times.
        let level = level([Terrain(at: 500, width: 120, height: 100)], length: 1200, entry: 3, reward: 3)
        let run = LevelValidator.botRun(level, boss: nil)
        #expect(run.blocked?.contains("bounced off the step at 500 more than \(LevelValidator.maxBumps) times") == true)
        #expect(run.time < 500 / 100 + LevelValidator.maxHeldBack + 1)
        let report = LevelValidator.validate(level, bosses: [:])
        #expect(report.problems.contains { $0.contains("step at 500 rises 100") })
    }

    @Test func badTerrainIsRejected() {
        var level = level([Terrain(at: 100, width: 40, height: 20), Terrain(at: 400, width: 10, height: 20),
                           Terrain(at: 600, width: 60, height: 20), Terrain(at: 640, width: 60, height: 30),
                           Terrain(at: 800, width: 40, height: 70), Terrain(at: 1000, width: 40, height: -40),
                           Terrain(at: 1210, width: 40, height: 20), Terrain(at: 1400, width: 40, height: 20),
                           Terrain(at: 1960, width: 40, height: 20)],
                          items: [PlacedItem(at: 1000, kind: .bush), PlacedItem(at: 1020, kind: .fish)])
        level.ravines = [Ravine(at: 1260, width: 30)]
        level.slick = [SlickZone(at: 1380, width: 40)]
        level.platforms = [Platform(at: 600, width: 40, y: 22), Platform(at: 1700, width: 48, y: 12, mode: .crumbles, kind: "island")]
        let problems = validate(level)
        #expect(problems.contains { $0.contains("terrain at 100 is inside the 150-unit start runway") })
        #expect(problems.contains { $0.contains("terrain at 400 is narrower than the hero") })
        #expect(problems.contains { $0.contains("terrain at 640 overlaps the terrain at 600") })
        #expect(problems.contains { $0.contains("terrain at 800 is 70 high") })
        #expect(problems.contains { $0.contains("terrain at 1000 is 40 deep") })
        #expect(problems.contains { $0.contains("terrain at 1210 is too close to the ravine at 1260") })
        #expect(problems.contains { $0.contains("terrain at 1400 overlaps the slick zone at 1380") })
        #expect(problems.contains { $0.contains("terrain at 1960 is too close to the boss") })
        #expect(problems.contains { $0.contains("bush at 1000 stands across a step") })
        #expect(!problems.contains { $0.contains("fish at 1020") })
        #expect(problems.contains { $0.contains("platform at 600 is 2 above the terrain under it") })
        #expect(problems.contains { $0.contains("platform at 1700 is an island; islands are always solid") })
    }

    @Test func flatLevelsAreUntouched() {
        let level = flatLevel(items: [PlacedItem(at: 400, kind: .stumpCat)], length: 900)
        var world = RunnerWorld(level: level, boss: nil)
        let events = world.run(4)
        #expect(!events.contains(.bumped))
        #expect(!events.contains { if case .hazardBroke = $0 { true } else { false } })
        #expect(LevelValidator.terrainProblems(in: level, items: level.items, tuning: Tuning()).isEmpty)
    }
}
