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

    @Test func aQuickTapStillHopsHighEnoughForALowStep() {
        var world = RunnerWorld(level: flatLevel(), boss: nil)
        _ = world.run(0.5)
        let top = tap(&world)
        #expect(top >= 28)
        #expect(top < Tuning().jumpApex - 4)   // still shorter than a held jump
    }

    @Test func aTapAgainstAWallIsAlwaysAFullJumpAndClimbsIt() {
        var world = RunnerWorld(level: level([Terrain(at: 300, width: 100, height: 40)]), boss: nil)
        advance(&world) { $0.isAgainstWall }
        #expect(tap(&world) >= 40)
        #expect(world.heroY == 40)
        #expect(!world.isAgainstWall)
    }

    @Test func aTapJustBeforeATallStepIsAFullJump() {
        var world = RunnerWorld(level: level([Terrain(at: 300, width: 100, height: 40)]), boss: nil)
        advance(&world) { $0.distance >= 300 - 8 - 30 }
        #expect(tap(&world) >= 40)
        #expect(world.heroY == 40)
    }

    @Test func theHeroStopsAgainstAWallAndTheLevelWaits() throws {
        let walker = PlacedItem(at: 700, kind: .slime)
        var world = RunnerWorld(level: level([Terrain(at: 300, width: 100, height: 30)], items: [walker]), boss: nil)
        let events = advance(&world) { $0.isAgainstWall }
        #expect(events.filter { $0 == .bumped }.count == 1)
        let stoppedAt = world.distance
        #expect(abs(stoppedAt - (300 - world.tuning.heroWidth / 2)) < 1e-6)
        let slime = try #require(world.entities.first)
        // Stuck for a second: no distance, no second bump, but the clock and the slime carry on.
        let time = world.time
        let more = world.run(1)
        #expect(world.distance == stoppedAt)
        #expect(world.runSpeed == 0)
        #expect(world.time > time + 0.9)
        #expect(!more.contains(.bumped))
        #expect(try #require(world.entities.first).x < slime.x - 10)
        // A jump gets on top.
        _ = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        advance(&world, limit: 2, Input(jumpHeld: true)) { $0.onGround }
        #expect(world.heroY == 30)
        #expect(world.distance > stoppedAt)
        #expect(!world.isAgainstWall)
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

    @Test func aDipIsFallenIntoAndItsFarWallStopsTheHero() {
        var world = RunnerWorld(level: level([Terrain(at: 300, width: 80, height: -24)]), boss: nil)
        advance(&world) { $0.isAgainstWall }
        #expect(world.heroY == -24)
        #expect(abs(world.distance - (380 - world.tuning.heroWidth / 2)) < 1e-6)
        _ = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        advance(&world, limit: 2, Input(jumpHeld: true)) { $0.onGround }
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
        #expect(dasher.isAgainstWall)
        #expect(dasher.distance <= 292 + 1e-6)

        var pouncer = RunnerWorld(level: level(wall, entry: 5), boss: nil, stats: hero(5))
        advance(&pouncer, Input(pawHeld: true)) { $0.distance > 240 }
        let leap = pouncer.step(Input(), dt: dt) + pouncer.run(1)
        #expect(leap.contains(.pounced))
        #expect(pouncer.distance <= 292 + 1e-6)
        #expect(pouncer.heroY == 0)
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
        #expect(run.stuckAt == nil)
    }

    @Test func aWallNeedingDoublePounceIsOnlyAllowedOnceItIsGuaranteed() {
        let wall = [Terrain(at: 500, width: 120, height: 58)]
        let early = level(wall, length: 1200, entry: 2)
        #expect(LevelValidator.terrainProblems(in: early, items: [], tuning: Tuning())
            .contains { $0.contains("step at 500 rises 58; one jump at hero level 2 climbs at most 44") })
        let run = LevelValidator.botRun(early, boss: nil)
        #expect(!run.finished)
        #expect(run.stuckAt != nil)

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
        // on its own gives up after `maxStuckTime` rather than standing there for ever.
        let level = level([Terrain(at: 500, width: 120, height: 100)], length: 1200, entry: 3, reward: 3)
        let run = LevelValidator.botRun(level, boss: nil)
        #expect(run.stuckAt != nil)
        #expect(run.time < 500 / 100 + LevelValidator.maxStuckTime + 1)
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
