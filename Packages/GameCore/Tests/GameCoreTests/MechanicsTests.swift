import Foundation
import Testing
@testable import GameCore

/// The kitten's abilities, the four worlds' enemy behaviours, slick ground and platforms.
@Suite struct MechanicsTests {
    func hero(_ level: Int) -> HeroStats { HeroStats(xp: Progression.xp(forLevel: level)) }

    func hit(_ events: [GameEvent]) -> Bool {
        events.contains { if case .heroHit = $0 { true } else if case .heroDied = $0 { true } else { false } }
    }

    /// Steps with no input until `condition` holds (or `limit` seconds pass); returns all events.
    @discardableResult
    func advance(_ world: inout RunnerWorld, limit: Double = 10, _ input: Input = Input(),
                 until condition: (RunnerWorld) -> Bool) -> [GameEvent] {
        var events: [GameEvent] = []
        let end = world.time + limit
        while !condition(world), world.time < end, !world.isOver { events += world.step(input, dt: dt) }
        return events
    }

    func gap(_ world: RunnerWorld, _ kind: ItemKind) -> Double {
        (world.entities.first { $0.kind == kind }?.x ?? 10_000) - world.distance
    }

    // MARK: - Ghost Dash

    @Test func ghostDashNeedsLevelFourAndSlipsThroughAnEnemy() {
        let level = flatLevel(items: [.init(at: 400, kind: .penguin)])
        var plain = RunnerWorld(level: level, boss: nil, stats: hero(3))
        advance(&plain) { gap($0, .penguin) < 24 }
        var events = plain.step(Input(pawPressed: true), dt: dt) + plain.run(1.5)
        #expect(!events.contains(.dashed))
        #expect(hit(events))

        var dasher = RunnerWorld(level: level, boss: nil, stats: hero(4))
        advance(&dasher) { gap($0, .penguin) < 24 }
        events = dasher.step(Input(pawPressed: true), dt: dt)
        #expect(events.contains(.dashed))
        #expect(dasher.isDashing)
        events += dasher.run(1.5)
        #expect(!hit(events))
        #expect(dasher.stats.hearts == 3)
        #expect(!dasher.isDashing)
    }

    @Test func ghostDashHasACooldown() {
        var world = RunnerWorld(level: flatLevel(), boss: nil, stats: hero(4))
        var dashes = world.step(Input(pawPressed: true, pawHeld: true), dt: dt).filter { $0 == .dashed }.count
        world.run(0.2)
        dashes += world.step(Input(pawPressed: true, pawHeld: true), dt: dt).filter { $0 == .dashed }.count
        #expect(dashes == 1)
        #expect(!world.canDash)
        world.run(world.tuning.dashCooldown)
        #expect(world.canDash)
        #expect(world.step(Input(pawPressed: true, pawHeld: true), dt: dt).contains(.dashed))
    }

    @Test func ghostDashDoesNotPassTerrainOrRavines() {
        var world = RunnerWorld(level: flatLevel(items: [.init(at: 300, kind: .stump)]), boss: nil, stats: hero(4))
        advance(&world) { gap($0, .stump) < 18 }
        #expect(hit(world.step(Input(pawPressed: true), dt: dt) + world.run(0.4)))

        var faller = RunnerWorld(level: flatLevel(ravines: [Ravine(at: 300, width: 40)]), boss: nil, stats: hero(4))
        advance(&faller) { $0.distance > 290 }
        let events = faller.step(Input(pawPressed: true), dt: dt) + faller.run(1)
        #expect(events.contains(.dashed))
        #expect(events.contains(.heroFell))
    }

    @Test func ghostDashSlipsThroughBossHazards() {
        let wave = HazardSpec(kind: "wave", delay: 0, y: 0, width: 16, height: 10, closingSpeed: 150)
        let attack = BossAttack(name: "wave", telegraph: 0.3, duration: 0.3, recover: 5, hazards: [wave])
        let boss = BossDefinition(id: "b", hp: 5, width: 30, height: 40, baseY: 0, vulnerable: .always,
                                  attacks: [attack], phases: [.init(startsBelow: 1, attacks: ["wave"])])
        var world = RunnerWorld(level: flatLevel(length: 100), boss: boss, stats: hero(4))
        advance(&world) { ($0.hazards.first.map { $0.x - $0.width / 2 } ?? 1000) - $0.distance < 20 }
        let events = world.step(Input(pawPressed: true), dt: dt) + world.run(0.6)
        #expect(events.contains(.dashed))
        #expect(!hit(events))
    }

    // MARK: - Super Pounce

    @Test func holdingThePawThenLettingGoPounces() {
        var world = RunnerWorld(level: flatLevel(), boss: nil, stats: hero(5))
        var events = world.step(Input(pawPressed: true, pawHeld: true), dt: dt)
        events += world.run(world.tuning.chargeTime, Input(pawHeld: true))
        #expect(world.isPounceReady)
        #expect(!events.contains(.dashed))
        events = world.step(Input(), dt: dt)
        #expect(events.contains(.pounced))
        #expect(world.pouncing)
        #expect(!world.onGround)
        world.run(1.5)
        #expect(world.onGround)
        #expect(!world.pouncing)

        // A short press is still a dash.
        var tapper = RunnerWorld(level: flatLevel(), boss: nil, stats: hero(5))
        events = tapper.step(Input(pawPressed: true, pawHeld: true), dt: dt) + tapper.run(0.1, Input(pawHeld: true))
        events += tapper.step(Input(), dt: dt)
        #expect(events.contains(.dashed))
        #expect(!events.contains(.pounced))
    }

    @Test func superPounceLeapsFartherThanAJump() {
        func airborneDistance(pounce: Bool) -> Double {
            var world = RunnerWorld(level: flatLevel(), boss: nil, stats: hero(5))
            if pounce {
                _ = world.step(Input(pawPressed: true, pawHeld: true), dt: dt)
                world.run(0.6, Input(pawHeld: true))
                _ = world.step(Input(), dt: dt)
            } else {
                _ = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
            }
            let start = world.distance
            while !world.onGround { _ = world.step(Input(jumpHeld: true), dt: dt) }
            return world.distance - start
        }
        #expect(airborneDistance(pounce: true) > airborneDistance(pounce: false) * 1.5)
    }

    func pounce(into kind: ItemKind, releaseAt release: Double) -> [GameEvent] {
        var world = RunnerWorld(level: flatLevel(items: [.init(at: 400, kind: kind)]), boss: nil, stats: hero(5))
        var events: [GameEvent] = []
        while gap(world, kind) > release { events += world.step(Input(pawPressed: world.time == 0, pawHeld: true), dt: dt) }
        events += world.step(Input(), dt: dt)
        return events + world.run(1.5)
    }

    @Test func superPounceBreaksACrateWall() {
        let events = pounce(into: .crateWall, releaseAt: 50)
        #expect(events.contains(.pounced))
        #expect(events.contains { if case .wallBroken = $0 { true } else { false } })
        #expect(!hit(events))
    }

    @Test(arguments: [ItemKind.squirrel, .snowball, .mechMouse])
    func superPounceDefeatsWalkersItTouches(kind: ItemKind) {
        // Close enough that the leap meets it before rising over it.
        let events = pounce(into: kind, releaseAt: 24)
        #expect(events.contains { if case .enemyDefeated(_, kind: kind) = $0 { true } else { false } })
        #expect(!hit(events))
    }

    @Test func aCrateWallCannotBeJumpedOrShot() {
        var world = RunnerWorld(level: flatLevel(items: [.init(at: 400, kind: .crateWall)]), boss: nil, stats: hero(4))
        advance(&world) { gap($0, .crateWall) < 120 }
        var events = world.run(0.05, Input(fireHeld: true))
        events += advance(&world) { gap($0, .crateWall) < 30 }
        events += world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        events += world.run(0.25, Input(jumpPressed: true, jumpHeld: true))
        events += world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt) + world.run(1, Input(jumpHeld: true))
        #expect(events.contains { if case .yarnBounced = $0 { true } else { false } })
        #expect(hit(events))
    }

    // MARK: - Slick ground

    @Test func slickGroundIsFasterAndGivesNoShortHop() {
        var level = flatLevel()
        level.slick = [SlickZone(at: 200, width: 400, kind: "milk")]
        var world = RunnerWorld(level: level, boss: nil)
        world.run(1.5)
        #expect(world.runSpeed == 100)
        advance(&world) { $0.distance > 300 }
        #expect(world.onSlick)
        #expect(abs(world.runSpeed - 130) < 1e-9)

        func tapApex(_ world: RunnerWorld) -> Double {
            var world = world
            var top = 0.0
            _ = world.step(Input(jumpPressed: true), dt: dt)
            while !world.onGround {
                _ = world.step(Input(), dt: dt)
                top = max(top, world.heroY)
            }
            return top
        }
        let slickHop = tapApex(world)
        let dryHop = tapApex(RunnerWorld(level: flatLevel(), boss: nil))
        #expect(dryHop < 15)
        #expect(slickHop > 45)
    }

    // MARK: - Platforms

    @Test func ledgesAreOneWayAndCanBeStoodOn() {
        var level = flatLevel()
        level.platforms = [Platform(at: 200, width: 150, y: 20)]
        var world = RunnerWorld(level: level, boss: nil)
        // Running under it: the kitten is shorter than its height.
        advance(&world) { $0.distance > 230 }
        #expect(world.onGround && world.heroY == 0 && world.standingOn == nil)
        // Jumping up through it lands on top.
        _ = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        advance(&world, limit: 1, Input(jumpHeld: true)) { $0.onGround }
        #expect(world.standingOn == 0)
        #expect(world.heroY == 20)
        // Running off its end drops back to the ground.
        advance(&world) { $0.distance > 360 }
        advance(&world, limit: 1) { $0.onGround }
        #expect(world.heroY == 0)
        #expect(world.standingOn == nil)
        #expect(world.stats.hearts == 3)
    }

    @Test func aLedgeCarriesTheBotOverARavineTooWideToJump() {
        var level = flatLevel(ravines: [Ravine(at: 300, width: 130)], length: 800)
        #expect(LevelValidator.botRun(level, boss: nil).finished == false)
        level.platforms = [Platform(at: 345, width: 40, y: 12, kind: "bridge")]
        #expect(LevelValidator.botRun(level, boss: nil).finished)
    }

    @Test func aCrumblingLedgeGivesWayAfterItIsLandedOn() {
        var level = flatLevel()
        level.platforms = [Platform(at: 220, width: 300, y: 12, mode: .crumbles)]
        var world = RunnerWorld(level: level, boss: nil)
        advance(&world) { $0.distance > 215 }
        #expect(world.platformState(0) == .solid)
        var events = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        events += advance(&world, limit: 1, Input(jumpHeld: true)) { $0.onGround }
        #expect(events.contains(.platformCrumbling(index: 0)))
        #expect(world.standingOn == 0)
        #expect(world.platformState(0) == .crumbling)
        world.run(Platform.defaultCrumbleAfter + 0.05)
        #expect(world.platformState(0) == .gone)
        advance(&world, limit: 1) { $0.onGround }
        #expect(world.heroY == 0)
    }

    @Test func aBlinkingLedgeFollowsTheClock() {
        var level = flatLevel()
        level.platforms = [Platform(at: 400, width: 60, y: 12, mode: .blinks, period: 2, solidFor: 1.2)]
        var world = RunnerWorld(level: level, boss: nil)
        var seen: [PlatformState] = []
        while world.time < 2 {
            _ = world.step(Input(), dt: dt)
            if seen.last != world.platformState(0) { seen.append(world.platformState(0)) }
        }
        #expect(seen == [.solid, .crumbling, .gone, .solid])
    }

    // MARK: - Throwers

    @Test func branchSquirrelLobsAcornsThatLandAndRoll() throws {
        var world = RunnerWorld(level: flatLevel(items: [.init(at: 500, kind: .branchSquirrel)]), boss: nil)
        let events = advance(&world) { $0.hazards.contains { $0.kind == "acorn" } }
        #expect(events.contains { if case .threw = $0 { true } else { false } })
        let thrown = try #require(world.hazards.first)
        #expect(thrown.y > 30)
        world.run(1)
        let rolling = try #require(world.hazards.first { $0.id == thrown.id })
        #expect(rolling.y == 0)
        #expect(rolling.vx < 0)
    }

    @Test func skeletonMouseThrowsBonesLowAndTheBellRingsWavesAlongTheGround() throws {
        var mouse = RunnerWorld(level: flatLevel(items: [.init(at: 500, kind: .skeletonMouse)]), boss: nil)
        advance(&mouse) { !$0.hazards.isEmpty }
        #expect(mouse.hazards.first?.kind == "bone")
        #expect(mouse.hazards.first?.y == 2)

        var bell = RunnerWorld(level: flatLevel(items: [.init(at: 500, kind: .bell)]), boss: nil)
        let events = advance(&bell) { !$0.hazards.isEmpty }
        #expect(events.contains { if case .bellRang = $0 { true } else { false } })
        #expect(bell.hazards.first?.kind == "soundwave")
        #expect(bell.hazards.first?.y == 0)
        // Ringing never stops while the kitten is in range, so standing still is hit.
        #expect(hit(bell.run(4)))
    }

    @Test func cannonballsAndSkullsFlyOverAStandingKitten() {
        let level = flatLevel(items: [.init(at: 500, kind: .cannon), .init(at: 900, kind: .skull)])
        var world = RunnerWorld(level: level, boss: nil)
        let events = world.run(9)
        #expect(events.contains { if case .threw = $0 { true } else { false } })
        #expect(!hit(events))
    }

    // MARK: - Behaviours

    @Test func hedgehogCurlsUpWhenCloseAndThenShrugsOffYarnAndStomps() throws {
        // Shot early, it is defeated.
        var early = RunnerWorld(level: flatLevel(items: [.init(at: 500, kind: .hedgehog)]), boss: nil, stats: hero(2))
        advance(&early) { gap($0, .hedgehog) < 220 }
        let shot = early.run(0.05, Input(fireHeld: true)) + early.run(1)
        #expect(shot.contains { if case .enemyDefeated(_, kind: .hedgehog) = $0 { true } else { false } })

        var world = RunnerWorld(level: flatLevel(items: [.init(at: 500, kind: .hedgehog)]), boss: nil, stats: hero(2))
        let events = advance(&world) { gap($0, .hedgehog) < 85 }
        #expect(events.contains { if case .curled = $0 { true } else { false } })
        #expect(world.entities.first?.state == .curled)
        let late = world.run(0.05, Input(fireHeld: true)) + world.run(0.3)
        #expect(late.contains { if case .yarnBounced = $0 { true } else { false } })
        #expect(!late.contains { if case .enemyHit = $0 { true } else { false } })

        // Curled, no landing on it is safe.
        for takeOff in stride(from: 20.0, to: 80, by: 4) {
            var stomper = RunnerWorld(level: flatLevel(items: [.init(at: 400, kind: .hedgehog)]), boss: nil)
            var jumped = false
            var events: [GameEvent] = []
            while stomper.time < 5, !stomper.isOver {
                let jump = !jumped && gap(stomper, .hedgehog) < takeOff
                jumped = jumped || jump
                events += stomper.step(Input(jumpPressed: jump, jumpHeld: true), dt: dt)
            }
            #expect(!events.contains { if case .stomped = $0 { true } else { false } })
        }
    }

    @Test func ghostCatOnlyExistsWhileVisibleAndYarnPassesThrough() throws {
        let cycle = try #require(ItemKind.ghostCat.spec.cycle)
        #expect(cycle.state(at: 0.5) == .active)
        #expect(cycle.state(at: 1.4) == .idle)
        #expect(cycle.state(at: 1.9) == .warning)

        var world = RunnerWorld(level: flatLevel(items: [.init(at: 300, kind: .ghostCat)]), boss: nil, stats: hero(2))
        advance(&world) { $0.time.truncatingRemainder(dividingBy: cycle.period) > 1.3 && !$0.entities.isEmpty }
        #expect(world.entities.first?.state == .hidden)
        #expect(world.entities.first?.isTangible == false)
        var events: [GameEvent] = []
        for _ in 0..<6 { events += world.run(0.05, Input(fireHeld: true)) + world.run(0.35) }
        #expect(!events.contains { if case .enemyDefeated = $0 { true } else { false } })
        #expect(!events.contains { if case .enemyHit = $0 { true } else { false } })
    }

    @Test func icicleBlinksThenDropsAndLeavesShards() throws {
        var world = RunnerWorld(level: flatLevel(items: [.init(at: 400, kind: .icicle)]), boss: nil)
        var events = advance(&world) { $0.entities.first?.state == .warning }
        #expect(events.contains { if case .fallWarning = $0 { true } else { false } })
        events = advance(&world, limit: 2) { $0.entities.first?.state == .landed }
        #expect(events.contains { if case .shattered = $0 { true } else { false } })
        let shards = try #require(world.entities.first)
        #expect(shards.y == 0)
        #expect(shards.x - world.distance > 15)
        #expect(shards.box.maxY == ItemKind.icicle.spec.fall?.shardHeight)
        // Shards on the ground hurt a kitten that runs on, and the bot hops them.
        var standing = world
        #expect(hit(standing.run(1)))
        var bot = Bot()
        var botEvents: [GameEvent] = []
        while world.time < 6 { botEvents += world.step(bot.input(for: world, dt: dt), dt: dt) }
        #expect(!hit(botEvents))
    }

    @Test func ventsFireOnTheWorldClock() {
        func run(offset: Double) -> [GameEvent] {
            var world = RunnerWorld(level: flatLevel(items: [.init(at: 300, kind: .vent, cycleOffset: offset)]), boss: nil)
            return world.run(4)
        }
        // The kitten passes the vent around t = 3: at offset 0 that is in a firing window, at 1 it is not.
        let firing = run(offset: 0)
        #expect(firing.contains { if case .trapFired = $0 { true } else { false } })
        #expect(hit(firing))
        #expect(!hit(run(offset: 1)))
    }

    // MARK: - Forest creatures (atlas set)

    static let forestCreatures: [ItemKind] = [.slime, .mushroomCat, .forestBat, .plantCat, .beeCat, .stumpCat,
                                              .snailCat, .spiderCat]

    func defeated(_ events: [GameEvent], _ kind: ItemKind) -> Bool {
        events.contains { if case .enemyDefeated(_, kind: kind) = $0 { true } else { false } }
    }

    /// Jumps once when the gap to `kind` falls below each take-off distance in turn; returns the
    /// events of every attempt that stomped it.
    func stompAttempts(_ kind: ItemKind, at: Double = 400) -> [[GameEvent]] {
        stride(from: 20.0, to: 90, by: 2).compactMap { takeOff in
            var world = RunnerWorld(level: flatLevel(items: [.init(at: at, kind: kind)]), boss: nil)
            var jumped = false
            var events: [GameEvent] = []
            while world.time < 6, !world.isOver {
                let jump = !jumped && gap(world, kind) < takeOff
                jumped = jumped || jump
                events += world.step(Input(jumpPressed: jump, jumpHeld: true), dt: dt)
            }
            return events.contains { if case .stomped = $0 { true } else { false } } ? events : nil
        }
    }

    @Test func forestCreaturesHaveTheirIdsAndHitboxes() {
        let expected: [(ItemKind, String, Double, Double, Int)] = [
            (.squirrel, "squirrel", 18, 24, 10), (.branchSquirrel, "branch_squirrel", 18, 20, 20),
            (.hedgehog, "hedgehog", 20, 15, 15), (.acorn, "acorn", 12, 11, 10),
            (.slime, "slime", 20, 14, 10), (.mushroomCat, "mushroom_cat", 18, 22, 15),
            (.forestBat, "forest_bat", 18, 14, 15), (.plantCat, "plant_cat", 18, 30, 20),
            (.beeCat, "bee_cat", 18, 16, 20), (.stumpCat, "stump_cat", 20, 28, 25),
            (.snailCat, "snail_cat", 24, 16, 15), (.spiderCat, "spider_cat", 18, 16, 20),
        ]
        for (kind, id, width, height, xp) in expected {
            #expect(kind.rawValue == id)
            #expect(kind.spec.width == width && kind.spec.height == height, "\(id) hitbox")
            #expect(kind.spec.xp == xp, "\(id) xp")
            #expect(kind.spec.yarnable, "\(id) is yarnable")
        }
    }

    @Test func slimeCreepsInSlowlyAndAStompKillsIt() throws {
        var world = RunnerWorld(level: flatLevel(items: [.init(at: 500, kind: .slime)]), boss: nil)
        advance(&world) { !$0.entities.isEmpty }
        let start = try #require(world.entities.first?.x)
        world.run(1)
        let moved = start - (world.entities.first?.x ?? start)
        #expect(moved > 10 && moved < 20)
        #expect(stompAttempts(.slime).contains { defeated($0, .slime) && !hit($0) })
    }

    @Test func mushroomCatPuffsSporesThatLandAheadAndRollOn() throws {
        var world = RunnerWorld(level: flatLevel(items: [.init(at: 500, kind: .mushroomCat)]), boss: nil)
        let events = advance(&world) { $0.hazards.contains { $0.kind == "spore" } }
        #expect(events.contains { if case .threw = $0 { true } else { false } })
        let spore = try #require(world.hazards.first)
        #expect(spore.y > ItemKind.mushroomCat.spec.height / 2)
        #expect(world.entities.first?.x == 500)
        advance(&world, limit: 2) { $0.hazards.first?.y == 0 }
        let landed = try #require(world.hazards.first { $0.id == spore.id })
        #expect(landed.y == 0)
        #expect(landed.x - world.distance > 40)
        world.run(0.2)
        #expect((world.hazards.first { $0.id == spore.id }?.x ?? .infinity) < landed.x)
        #expect(stompAttempts(.mushroomCat).contains { defeated($0, .mushroomCat) })
    }

    @Test func forestBatSwoopsButNeverLowEnoughToHitAStandingKitten() {
        var world = RunnerWorld(level: flatLevel(items: [.init(at: 500, kind: .forestBat)]), boss: nil)
        var lowest = Double.infinity
        var events: [GameEvent] = []
        while world.time < 6 {
            events += world.step(Input(), dt: dt)
            if let bat = world.entities.first(where: { $0.kind == .forestBat }) { lowest = min(lowest, bat.y) }
        }
        #expect(lowest >= 28)
        #expect(lowest > world.tuning.heroHeight)
        #expect(lowest < ItemKind.forestBat.spec.baseY)
        #expect(!hit(events))
    }

    @Test func plantCatOnlyBitesWhileActiveAndYarnHurtsItAnyTime() throws {
        let cycle = try #require(ItemKind.plantCat.spec.cycle)
        #expect(ItemKind.plantCat.spec.cycleRole == .trap)
        #expect(!ItemKind.plantCat.spec.stompable)
        #expect(ItemKind.plantCat.spec.hp == 2)
        // Running straight through: harmless while shut, a bite while active.
        func runThrough(offset: Double) -> [GameEvent] {
            var world = RunnerWorld(level: flatLevel(items: [.init(at: 300, kind: .plantCat, cycleOffset: offset)]),
                                    boss: nil)
            return world.run(4)
        }
        let results = stride(from: 0.0, to: cycle.period, by: 0.1).map { hit(runThrough(offset: $0)) }
        #expect(results.contains(true))
        #expect(results.contains(false))

        // Yarn lands while it is shut, not just while it bites: two balls defeat it.
        var world = RunnerWorld(level: flatLevel(items: [.init(at: 500, kind: .plantCat)]), boss: nil, stats: hero(2))
        advance(&world) { gap($0, .plantCat) < 200 }
        var events = world.run(0.05, Input(fireHeld: true))
        var stateWhenHit: EntityState?
        while stateWhenHit == nil, world.time < 6 {
            let state = world.entities.first?.state
            let step = world.step(Input(), dt: dt)
            events += step
            if step.contains(where: { if case .enemyHit = $0 { true } else { false } }) { stateWhenHit = state }
        }
        #expect(stateWhenHit != nil && stateWhenHit != .active)
        #expect(world.entities.first?.isTangible == false)
        events += world.run(0.05, Input(fireHeld: true)) + world.run(0.6)
        #expect(defeated(events, .plantCat))
    }

    @Test func beeCatHoversOverheadDriftsInAndFiresStingsLow() throws {
        var world = RunnerWorld(level: flatLevel(items: [.init(at: 600, kind: .beeCat)]), boss: nil)
        advance(&world) { !$0.entities.isEmpty }
        let bee = try #require(world.entities.first)
        #expect(bee.y >= 36 && bee.y <= 44)
        #expect(bee.box.minY > world.tuning.heroHeight)
        advance(&world) { $0.hazards.contains { $0.kind == "sting" } }
        let sting = try #require(world.hazards.first)
        #expect(sting.y == 4)
        #expect(sting.gravity == 0)
        let drifted = try #require(world.entities.first)
        #expect(drifted.x < bee.x)
        #expect(drifted.x > bee.x - 40)
        // A sting is low: a kitten that never jumps is stung.
        #expect(hit(world.run(4)))
    }

    @Test func stumpCatIsSolidShootsLeavesAlongTheGroundAndTakesTwoYarn() throws {
        let spec = ItemKind.stumpCat.spec
        #expect(spec.solid && spec.hp == 2 && spec.velocity == 0)
        var world = RunnerWorld(level: flatLevel(items: [.init(at: 600, kind: .stumpCat)]), boss: nil)
        advance(&world) { $0.hazards.contains { $0.kind == "leaf" } }
        #expect(world.hazards.first?.y == 2)
        #expect(world.hazards.first?.gravity == 0)

        var shooter = RunnerWorld(level: flatLevel(items: [.init(at: 600, kind: .stumpCat)]), boss: nil, stats: hero(2))
        advance(&shooter) { gap($0, .stumpCat) < 250 }
        let events = shooter.run(0.05, Input(fireHeld: true)) + shooter.run(0.4)
            + shooter.run(0.05, Input(fireHeld: true)) + shooter.run(1)
        #expect(events.contains { if case .enemyHit = $0 { true } else { false } })
        #expect(defeated(events, .stumpCat))

        // Terrain: a Ghost Dash does not slip through it.
        var dasher = RunnerWorld(level: flatLevel(items: [.init(at: 300, kind: .stumpCat)]), boss: nil, stats: hero(4))
        advance(&dasher) { gap($0, .stumpCat) < 18 }
        #expect(hit(dasher.step(Input(pawPressed: true), dt: dt) + dasher.run(0.4)))
    }

    @Test func snailCatHidesInItsShellWhenCloseAndThenShrugsOffYarnAndStomps() {
        var early = RunnerWorld(level: flatLevel(items: [.init(at: 500, kind: .snailCat)]), boss: nil, stats: hero(2))
        advance(&early) { gap($0, .snailCat) < 220 }
        #expect(defeated(early.run(0.05, Input(fireHeld: true)) + early.run(1), .snailCat))

        var world = RunnerWorld(level: flatLevel(items: [.init(at: 500, kind: .snailCat)]), boss: nil, stats: hero(2))
        let events = advance(&world) { gap($0, .snailCat) < 76 }
        #expect(events.contains { if case .curled = $0 { true } else { false } })
        #expect(world.entities.first?.state == .curled)
        let late = world.run(0.05, Input(fireHeld: true)) + world.run(0.3)
        #expect(late.contains { if case .yarnBounced = $0 { true } else { false } })
        #expect(!defeated(late, .snailCat))
        #expect(stompAttempts(.snailCat).isEmpty)
    }

    @Test func spiderCatHangsHarmlesslyThenDropsAndWalksIn() throws {
        var world = RunnerWorld(level: flatLevel(items: [.init(at: 500, kind: .spiderCat)]), boss: nil)
        advance(&world) { !$0.entities.isEmpty }
        let hanging = try #require(world.entities.first)
        #expect(hanging.y == 60)
        #expect(hanging.state == .idle)
        // Out of reach on its thread: it neither hurts nor takes yarn.
        #expect(!hanging.isTangible)
        // It does not walk while it hangs.
        world.run(0.5)
        #expect(world.entities.first?.x == hanging.x)

        var events = advance(&world) { $0.entities.first?.state == .warning }
        #expect(events.contains { if case .fallWarning = $0 { true } else { false } })
        #expect(world.entities.first?.isTangible == false)
        events = advance(&world, limit: 2) { $0.entities.first?.state == .landed }
        #expect(events.contains { if case .droppedDown = $0 { true } else { false } })
        #expect(!events.contains { if case .shattered = $0 { true } else { false } })
        let landed = try #require(world.entities.first)
        #expect(landed.y == 0)
        #expect(landed.isTangible)
        #expect(landed.x - world.distance > 30)
        #expect(landed.box.maxY - landed.box.minY == ItemKind.spiderCat.spec.height)
        world.run(0.1)
        #expect((world.entities.first?.x ?? .infinity) < landed.x)
        // On the ground it is an ordinary walker: standing still is bitten.
        var standing = world
        #expect(hit(standing.run(2)))
    }

    @Test func spiderCatOnTheGroundIsStompedShotAndWalks() {
        #expect(stompAttempts(.spiderCat).contains { defeated($0, .spiderCat) && !hit($0) })
        var shooter = RunnerWorld(level: flatLevel(items: [.init(at: 500, kind: .spiderCat)]), boss: nil, stats: hero(2))
        advance(&shooter) { $0.entities.first?.state == .landed }
        #expect(defeated(shooter.run(0.05, Input(fireHeld: true)) + shooter.run(0.6), .spiderCat))
        // A walker once down (it turns at a rim and a Super Pounce defeats it), not while it hangs.
        var walker = RunnerWorld(level: flatLevel(items: [.init(at: 500, kind: .spiderCat)]), boss: nil)
        advance(&walker) { !$0.entities.isEmpty }
        #expect(walker.entities.first?.walks == false)
        advance(&walker) { $0.entities.first?.state == .landed }
        #expect(walker.entities.first?.walks == true)
    }

    @Test(arguments: MechanicsTests.forestCreatures, [1, 2])
    func botClearsEachForestCreatureWithoutAHit(kind: ItemKind, entry: Int) {
        let level = flatLevel(items: [.init(at: 400, kind: kind), .init(at: 800, kind: kind)], length: 1200,
                              entry: entry, reward: max(entry, 2))
        #expect(LevelValidator.botRun(level, boss: nil).finished)
    }

    @Test func botClearsAForestRunOfEveryCreature() {
        let items = Self.forestCreatures.enumerated().map { PlacedItem(at: 400 + Double($0.offset) * 260, kind: $0.element) }
        #expect(LevelValidator.botRun(flatLevel(items: items, length: 2700), boss: nil).finished)
    }

    // MARK: - Bot

    @Test func botPouncesThroughCrateWalls() {
        let level = flatLevel(items: [.init(at: 500, kind: .crateWall), .init(at: 900, kind: .crateWall)],
                              length: 1200, entry: 5, reward: 5)
        #expect(LevelValidator.botRun(level, boss: nil).finished)
        var lower = level
        lower.entryHeroLevel = 4
        #expect(!LevelValidator.botRun(lower, boss: nil).finished)
    }

    /// A vent that is firing just as the kitten passes is too tall for one jump. With a feeble second
    /// jump (test tuning) only a Ghost Dash gets through, and the bot must find it.
    @Test func botDashesThroughWhatNoJumpClears() {
        var tuning = Tuning()
        tuning.doubleJumpScale = 0.3
        var level = flatLevel(items: [.init(at: 300, kind: .vent)], length: 800, entry: 3, reward: 3)
        #expect(!LevelValidator.botRun(level, boss: nil, tuning: tuning).finished)
        level.entryHeroLevel = 4
        #expect(LevelValidator.botRun(level, boss: nil, tuning: tuning).finished)
    }

    // MARK: - Validation

    @Test func validatorChecksSurfaces() {
        var level = flatLevel()
        level.slick = [SlickZone(at: 100, width: 50)]
        level.platforms = [Platform(at: 400, width: 10, y: 12), Platform(at: 600, width: 40, y: 80),
                           Platform(at: 800, width: 40, y: 12, mode: .blinks, period: 1, solidFor: 2)]
        let problems = LevelValidator.surfaceProblems(in: level, tuning: Tuning())
        #expect(problems.contains { $0.contains("slick zone at 100 is inside the 150-unit start runway") })
        #expect(problems.contains { $0.contains("platform at 400 is narrower than the hero") })
        #expect(problems.contains { $0.contains("platform at 600 is 80 high") })
        #expect(problems.contains { $0.contains("platform at 800 blinks") })
    }

    @Test func wideRavinesAreAllowedOnceDoublePounceIsGuaranteed() {
        let wide = Ravine(at: 400, width: 70)
        let early = flatLevel(ravines: [wide], entry: 1)
        let late = flatLevel(ravines: [wide], entry: 3)
        #expect(LevelValidator.ravineProblems(in: early, items: [], tuning: Tuning()).contains { $0.contains("70 wide") })
        #expect(LevelValidator.ravineProblems(in: late, items: [], tuning: Tuning()).isEmpty)
        #expect(LevelValidator.botRun(late, boss: nil).finished)
    }
}
