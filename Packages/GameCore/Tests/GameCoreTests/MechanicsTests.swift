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

    @Test func canThrowFollowsTheYarnCooldown() {
        #expect(!RunnerWorld(level: flatLevel(), boss: nil, stats: hero(1)).canThrow)
        var world = RunnerWorld(level: flatLevel(), boss: nil, stats: hero(2))
        #expect(world.canThrow)
        #expect(world.step(Input(fireHeld: true), dt: dt).contains { if case .yarnThrown = $0 { true } else { false } })
        #expect(!world.canThrow)
        world.run(world.tuning.yarnCooldown + dt)
        #expect(world.canThrow)
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
        #expect(dryHop < 38)
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

    /// Jumps once when the gap to `kind` falls below each take-off distance in turn, as a tap, a
    /// short hold and a full hold; returns the events of every attempt that stomped it.
    func stompAttempts(_ kind: ItemKind, at: Double = 400, terrain: [Terrain]? = nil) -> [[GameEvent]] {
        var level = flatLevel(items: [.init(at: at, kind: kind)])
        level.terrain = terrain
        return [0.0, 0.12, 1].flatMap { hold in
            stride(from: 20.0, to: 90, by: 2).compactMap { takeOff -> [GameEvent]? in
                var world = RunnerWorld(level: level, boss: nil)
                var jumpedAt: Double?
                var events: [GameEvent] = []
                while world.time < 6, !world.isOver {
                    let jump = jumpedAt == nil && gap(world, kind) < takeOff
                    if jump { jumpedAt = world.time }
                    let held = jumpedAt.map { world.time - $0 < hold } ?? false
                    events += world.step(Input(jumpPressed: jump, jumpHeld: held), dt: dt)
                }
                return events.contains { if case .stomped = $0 { true } else { false } } ? events : nil
            }
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

    @Test func snailCatHidesInItsShellWhenCloseAndThenShrugsOffYarnButBouncesTheKitten() {
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

        // Landing on the hidden shell is a safe bounce: no hit, and the snail stays. (A hop too low
        // to come down on top can clip the shell's face first; that is a hit, not a landing.)
        let landings = stompAttempts(.snailCat).filter { events in
            let stomp = events.firstIndex { if case .stomped = $0 { true } else { false } }!
            return !hit(Array(events[..<stomp]))
        }
        #expect(!landings.isEmpty)
        for events in landings {
            #expect(!hit(events))
            #expect(!defeated(events, .snailCat))
        }
        // The hedgehog's spikes still hurt once it has curled.
        #expect(stompAttempts(.hedgehog).isEmpty)
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

    // MARK: - Frost creatures (Frostpaw Mountains sheet)

    static let frostCreatures: [ItemKind] = [.iceSlime, .snowCat, .iceBat, .iceGolem, .penguinSoldier, .snowyOwl,
                                             .iceHedgehog, .snowman, .iciclePlant, .miniYeti]

    /// A flat test level at world 2's speed.
    func frostLevel(_ items: [PlacedItem], terrain: [Terrain]? = nil, length: Double = 2000, entry: Int = 1)
        -> LevelDefinition {
        var level = flatLevel(items: items, length: length, entry: entry, reward: max(entry, 2))
        level.speed = 120
        level.terrain = terrain
        return level
    }

    /// Fires one ball of yarn, then lets it fly.
    func shoot(_ world: inout RunnerWorld, flight: Double = 0.5) -> [GameEvent] {
        world.run(0.05, Input(fireHeld: true)) + world.run(max(flight, world.tuning.yarnCooldown))
    }

    /// A kitten with Yarn Shot fires `count` balls at `kind` from 280 away, then lets them land.
    func volley(at kind: ItemKind, count: Int) -> [GameEvent] {
        var world = RunnerWorld(level: frostLevel([.init(at: 700, kind: kind)]), boss: nil, stats: hero(2))
        advance(&world) { gap($0, kind) < 280 }
        var events: [GameEvent] = []
        for _ in 0..<count { events += world.run(0.05, Input(fireHeld: true)) + world.run(0.4) }
        return events + world.run(1)
    }

    /// Exactly `hp` balls of yarn defeat it: one fewer does not.
    func takesYarn(_ kind: ItemKind, _ hp: Int) -> Bool {
        !defeated(volley(at: kind, count: hp - 1), kind) && defeated(volley(at: kind, count: hp), kind)
    }

    @Test func frostCreaturesHaveTheirIdsAndHitboxes() {
        let expected: [(ItemKind, String, Double, Double, Int, Int)] = [
            (.iceSlime, "ice_slime", 20, 14, 1, 12), (.snowCat, "snow_cat", 20, 20, 2, 25),
            (.iceBat, "ice_bat", 18, 14, 1, 15), (.iceGolem, "ice_golem", 26, 30, 3, 40),
            (.penguinSoldier, "penguin_soldier", 18, 24, 2, 25), (.snowyOwl, "snowy_owl", 20, 16, 1, 25),
            (.iceHedgehog, "ice_hedgehog", 20, 16, 1, 20), (.snowman, "snowman", 20, 30, 2, 25),
            (.iciclePlant, "icicle_plant", 18, 24, 2, 25), (.miniYeti, "mini_yeti", 30, 34, 4, 60),
        ]
        for (kind, id, width, height, hp, xp) in expected {
            #expect(kind.rawValue == id)
            #expect(kind.spec.width == width && kind.spec.height == height, "\(id) hitbox")
            #expect(kind.spec.hp == hp, "\(id) hp")
            #expect(kind.spec.xp == xp, "\(id) xp")
            #expect(kind.spec.yarnable, "\(id) is yarnable")
        }
        #expect(ItemKind.iceGolem.spec.minHeroLevel == 3)
        #expect(ItemKind.miniYeti.spec.minHeroLevel == 3)
        // The original frost set is still there.
        for id in ["icicle", "snowball", "penguin", "snowdrift"] { #expect(ItemKind(rawValue: id) != nil) }
    }

    @Test func iceSlimeHopsInOnTheGroundAndAStompKillsIt() throws {
        var world = RunnerWorld(level: frostLevel([.init(at: 500, kind: .iceSlime)]), boss: nil)
        advance(&world) { !$0.entities.isEmpty }
        let start = try #require(world.entities.first?.x)
        var highest = 0.0
        for _ in 0..<60 {
            _ = world.step(Input(), dt: dt)
            highest = max(highest, world.entities.first?.y ?? 0)
        }
        // The hop is only drawn: the hitbox stays on the ground.
        #expect(highest == 0)
        let moved = start - (world.entities.first?.x ?? start)
        #expect(moved > 18 && moved < 26)
        #expect(stompAttempts(.iceSlime).contains { defeated($0, .iceSlime) && !hit($0) })
    }

    @Test func snowCatRunsInFastSlashesFromTheSideAndTakesAStompOrTwoYarn() throws {
        var world = RunnerWorld(level: frostLevel([.init(at: 700, kind: .snowCat)]), boss: nil)
        advance(&world) { !$0.entities.isEmpty }
        let start = try #require(world.entities.first?.x)
        var standing = world
        standing.run(1)
        #expect(start - (standing.entities.first?.x ?? start) > 50)
        #expect(hit(standing.run(4)))
        #expect(stompAttempts(.snowCat).contains { defeated($0, .snowCat) && !hit($0) })
        #expect(takesYarn(.snowCat, 2))
    }

    @Test func iceBatSwoopsButNeverLowEnoughToHitAStandingKitten() {
        var world = RunnerWorld(level: frostLevel([.init(at: 500, kind: .iceBat)]), boss: nil)
        var lowest = Double.infinity
        var events: [GameEvent] = []
        while world.time < 6 {
            events += world.step(Input(), dt: dt)
            if let bat = world.entities.first(where: { $0.kind == .iceBat }) { lowest = min(lowest, bat.y) }
        }
        #expect(lowest >= 28)
        #expect(lowest < ItemKind.iceBat.spec.baseY)
        #expect(!hit(events))
    }

    @Test func iceGolemIsASafeBounceTakesThreeYarnAndCrawls() throws {
        let landings = stompAttempts(.iceGolem)
        #expect(!landings.isEmpty)
        for events in landings {
            #expect(!defeated(events, .iceGolem))
        }
        #expect(landings.contains { !hit($0) })

        var world = RunnerWorld(level: frostLevel([.init(at: 700, kind: .iceGolem)]), boss: nil)
        advance(&world) { !$0.entities.isEmpty }
        let start = try #require(world.entities.first?.x)
        world.run(1)
        let moved = start - (world.entities.first?.x ?? start)
        #expect(moved > 6 && moved < 10)
        #expect(takesYarn(.iceGolem, 3))
    }

    @Test func penguinSoldierPatrolsAroundItsPostAndThrustsAShortSpear() throws {
        var world = RunnerWorld(level: frostLevel([.init(at: 700, kind: .penguinSoldier)]), boss: nil)
        advance(&world) { !$0.entities.isEmpty }
        var xs: [Double] = []
        var turns = 0
        var facing = world.entities.first?.reversed
        while gap(world, .penguinSoldier) > 120 {
            _ = world.step(Input(), dt: dt)
            guard let penguin = world.entities.first else { break }
            xs.append(penguin.x)
            if penguin.reversed != facing { turns += 1 }
            facing = penguin.reversed
        }
        #expect(turns >= 1)
        #expect((xs.min() ?? 0) >= 700 - 31 && (xs.max() ?? 0) <= 700 + 31)
        #expect((xs.max() ?? 0) - (xs.min() ?? 0) > 40)

        // The spear only comes out at close range, low, and fast.
        var thrusts: [Double] = []
        var events: [GameEvent] = []
        while world.time < 12, !world.isOver, world.entities.contains(where: { $0.kind == .penguinSoldier }) {
            let step = world.step(Input(), dt: dt)
            events += step
            if step.contains(where: { if case .threw = $0 { true } else { false } }) {
                thrusts.append(gap(world, .penguinSoldier))
            }
        }
        #expect(!thrusts.isEmpty)
        #expect(thrusts.allSatisfy { $0 <= 70 })
        #expect(hit(events))
        let level = frostLevel([.init(at: 700, kind: .penguinSoldier)])
        var spearWorld = RunnerWorld(level: level, boss: nil)
        advance(&spearWorld) { $0.hazards.contains { $0.kind == "spear" } }
        let spear = try #require(spearWorld.hazards.first)
        #expect(spear.y == 6 && spear.width == 14 && spear.height == 4)
        #expect(spear.vx == -140 && spear.gravity == 0)

        #expect(stompAttempts(.penguinSoldier).contains { defeated($0, .penguinSoldier) })
    }

    @Test func snowyOwlBlinksThenDropsAnIcicleStraightDownAheadOfTheKitten() throws {
        var world = RunnerWorld(level: frostLevel([.init(at: 700, kind: .snowyOwl)]), boss: nil)
        advance(&world) { !$0.entities.isEmpty }
        let owl = try #require(world.entities.first)
        #expect(owl.y == 60)
        #expect(!ItemKind.snowyOwl.spec.stompable)
        let warned = advance(&world) { $0.entities.first?.state == .warning }
        #expect(!warned.contains { if case .threw = $0 { true } else { false } })
        #expect(world.hazards.isEmpty)
        let events = advance(&world, limit: 2) { !$0.hazards.isEmpty }
        #expect(events.contains { if case .threw = $0 { true } else { false } })
        #expect(world.entities.first.map { $0.x < owl.x } == true)
        let shot = try #require(world.hazards.first)
        #expect(shot.kind == "icicle_shot")
        #expect(shot.vx == 0)
        #expect(shot.y > 40)
        advance(&world, limit: 2) { $0.hazards.first?.y == 0 }
        let landed = try #require(world.hazards.first)
        #expect(landed.x == shot.x)
        #expect(landed.x - world.distance > 30)
        // It lies there: a kitten that never jumps runs into it.
        #expect(hit(world.run(2)))
    }

    @Test func iceHedgehogCurlsThenRollsInFastAndTurnsAtAStep() throws {
        var world = RunnerWorld(level: frostLevel([.init(at: 700, kind: .iceHedgehog)]), boss: nil, stats: hero(2))
        let before = advance(&world) { $0.entities.first?.state == .curled }
        #expect(before.contains { if case .curled = $0 { true } else { false } })
        #expect(gap(world, .iceHedgehog) <= 100 && gap(world, .iceHedgehog) > 90)
        let curledAt = try #require(world.entities.first?.x)
        world.run(0.1)
        let rolled = curledAt - (world.entities.first?.x ?? curledAt)
        #expect(rolled > 10 && rolled < 14)
        let late = shoot(&world, flight: 0.4)
        #expect(late.contains { if case .yarnBounced = $0 { true } else { false } })
        #expect(!defeated(late, .iceHedgehog))
        #expect(stompAttempts(.iceHedgehog).isEmpty)

        // Shot before it curls, it is defeated.
        #expect(defeated(volley(at: .iceHedgehog, count: 1), .iceHedgehog))

        // Rolling, it still turns back at a step.
        // The kitten is held back at the block's near face; the hedgehog rolls in from the far side.
        let block = Terrain(at: 680, width: 20, height: 10)
        var stepper = RunnerWorld(level: frostLevel([.init(at: 800, kind: .iceHedgehog)], terrain: [block]),
                                  boss: nil)
        advance(&stepper) { $0.entities.first?.state == .curled }
        advance(&stepper, limit: 1) { $0.entities.first?.reversed == true }
        #expect(stepper.entities.first?.reversed == true)
        #expect((stepper.entities.first?.x ?? 0) >= block.end)
        #expect(stepper.entities.first?.state == .curled)
        #expect(stepper.stats.hearts == 3)
    }

    @Test func snowmanLobsSnowballsThatLandAheadAndIsOnlyABounce() throws {
        var world = RunnerWorld(level: frostLevel([.init(at: 700, kind: .snowman)]), boss: nil)
        advance(&world) { $0.hazards.contains { $0.kind == "snowball_shot" } }
        let ball = try #require(world.hazards.first)
        #expect(ball.y > 20)
        #expect(ball.gravity > 0)
        advance(&world, limit: 2) { $0.hazards.first?.y == 0 }
        let landed = try #require(world.hazards.first { $0.id == ball.id })
        #expect(landed.x - world.distance > 40)
        #expect(world.entities.first?.x == 700)

        let landings = stompAttempts(.snowman)
        #expect(!landings.isEmpty)
        #expect(landings.allSatisfy { !defeated($0, .snowman) })
        #expect(takesYarn(.snowman, 2))
    }

    @Test func iciclePlantFiresABoltEachTimeItOpensAndYarnHurtsItShut() throws {
        let cycle = try #require(ItemKind.iciclePlant.spec.cycle)
        var world = RunnerWorld(level: frostLevel([.init(at: 700, kind: .iciclePlant)]), boss: nil)
        var opened = 0
        var bolts = Set<Int>()
        while gap(world, .iciclePlant) > 40 {
            let step = world.step(Input(), dt: dt)
            let fired = step.contains { if case .trapFired = $0 { true } else { false } }
            let fresh = world.hazards.filter { !bolts.contains($0.id) }
            if fired, gap(world, .iciclePlant) < 300 { opened += 1 }
            // A new bolt only ever comes out on the frame it opens.
            #expect(fresh.isEmpty || fired)
            for bolt in fresh {
                #expect(bolt.kind == "icicle_bolt")
                #expect(bolt.y == 4)
                #expect(bolt.gravity == 0)
                bolts.insert(bolt.id)
            }
        }
        #expect(opened >= 1)
        #expect(bolts.count == opened)

        // A trap like plant_cat: shut it is harmless to touch, open it hurts. Yarn hits it any time.
        #expect(ItemKind.iciclePlant.spec.cycleRole == .trap)
        #expect(!ItemKind.iciclePlant.spec.stompable)
        var shut = Entity(id: 1, kind: .iciclePlant, x: 0, y: 0, hp: 2)
        #expect(!shut.isTangible && shut.catchesYarn)
        shut.state = cycle.state(at: 0)
        #expect(shut.isTangible)
        #expect(takesYarn(.iciclePlant, 2))
    }

    @Test func miniYetiCannotBeStompedAndTakesFourYarn() throws {
        #expect(!ItemKind.miniYeti.spec.stompable)
        #expect(stompAttempts(.miniYeti).isEmpty)
        #expect(takesYarn(.miniYeti, 4))
    }

    static let frostBotCases: [(ItemKind, Int)] = frostCreatures.flatMap { kind in
        [1, 3].filter { $0 >= kind.spec.minHeroLevel }.map { (kind, $0) }
    }

    @Test(arguments: MechanicsTests.frostBotCases)
    func botClearsEachFrostCreatureWithoutAHit(kind: ItemKind, entry: Int) {
        let level = frostLevel([.init(at: 400, kind: kind), .init(at: 800, kind: kind)], length: 1300, entry: entry)
        #expect(LevelValidator.botRun(level, boss: nil).finished)
    }

    @Test func botClearsAFrostRunOfEveryCreature() {
        let items = Self.frostCreatures.enumerated().map { PlacedItem(at: 400 + Double($0.offset) * 280, kind: $0.element) }
        #expect(LevelValidator.botRun(frostLevel(items, length: 3400, entry: 3), boss: nil).finished)
    }

    // MARK: - Haunted creatures (Haunted Meowseum sheet)

    static let hauntedCreatures: [ItemKind] = [.ghostCat, .bat, .hauntedPortrait, .cursedArmor, .candleCat,
                                               .poltergeistBook, .gargoyleCat, .shadowCat]

    /// A flat test level at world 3's speed.
    func hauntedLevel(_ items: [PlacedItem], length: Double = 2000, entry: Int = 1) -> LevelDefinition {
        var level = flatLevel(items: items, length: length, entry: entry, reward: max(entry, 2))
        level.speed = 130
        return level
    }

    func threw(_ events: [GameEvent]) -> Bool {
        events.contains { if case .threw = $0 { true } else { false } }
    }

    func bounced(_ events: [GameEvent]) -> Bool {
        events.contains { if case .yarnBounced = $0 { true } else { false } }
    }

    func yarnHit(_ events: [GameEvent]) -> Bool {
        events.contains { if case .enemyHit = $0 { true } else if case .enemyDefeated = $0 { true } else { false } }
    }

    /// Jumps and fires each ball at the top of a hop, to reach something hovering over a standing kitten.
    func jumpVolley(at kind: ItemKind, count: Int, from: Double = 260, fireAbove: Double = 30) -> [GameEvent] {
        var world = RunnerWorld(level: hauntedLevel([.init(at: 800, kind: kind)]), boss: nil, stats: hero(2))
        advance(&world) { gap($0, kind) < from }
        var events: [GameEvent] = []
        for _ in 0..<count {
            events += world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
            events += advance(&world, limit: 1, Input(jumpHeld: true)) { $0.heroY > fireAbove }
            events += world.step(Input(jumpHeld: true, fireHeld: true), dt: dt)
            events += advance(&world, limit: 2, Input(jumpHeld: true)) { $0.onGround }
        }
        return events + world.run(1)
    }

    @Test func hauntedCreaturesHaveTheirIdsAndHitboxes() throws {
        let expected: [(ItemKind, String, Double, Double, Int, Int)] = [
            (.hauntedPortrait, "haunted_portrait", 18, 20, 2, 25), (.cursedArmor, "cursed_armor", 20, 28, 3, 45),
            (.candleCat, "candle_cat", 14, 16, 1, 15), (.poltergeistBook, "poltergeist_book", 16, 14, 1, 20),
            (.gargoyleCat, "gargoyle_cat", 20, 24, 2, 35), (.shadowCat, "shadow_cat", 16, 20, 1, 30),
        ]
        for (kind, id, width, height, hp, xp) in expected {
            #expect(kind.rawValue == id)
            #expect(kind.spec.width == width && kind.spec.height == height, "\(id) hitbox")
            #expect(kind.spec.hp == hp, "\(id) hp")
            #expect(kind.spec.xp == xp, "\(id) xp")
            #expect(kind.spec.yarnable, "\(id) is yarnable")
        }
        #expect(ItemKind.cursedArmor.spec.minHeroLevel == 3)
        // The bat is only restyled.
        let bat = ItemKind.bat.spec
        #expect(bat.width == 14 && bat.height == 10 && bat.baseY == 40 && bat.flight?.low == 26)
        // The ghost cat keeps its phasing.
        #expect(ItemKind.ghostCat.spec.cycleRole == .phase)
        let spirit = try #require(ItemKind.ghostCat.spec.throwing)
        #expect(spirit.projectile == "spirit_ball" && spirit.width == 8 && spirit.height == 8)
        #expect(spirit.speed == 100 && spirit.interval == 2.4 && spirit.y == 26)
    }

    @Test func ghostCatOnlyThrowsSpiritBallsWhileVisibleAndOverAStandingKitten() throws {
        let level = hauntedLevel([.init(at: 700, kind: .ghostCat), .init(at: 1500, kind: .ghostCat, cycleOffset: 1)])
        var world = RunnerWorld(level: level, boss: nil)
        var throwCount = 0
        var seen = Set<Int>()
        while world.time < 12, !world.isOver {
            let step = world.step(Input(), dt: dt)
            for case .threw(let id) in step {
                throwCount += 1
                #expect(world.entities.first { $0.id == id }?.state == .active)
            }
            for ball in world.hazards where !seen.contains(ball.id) {
                seen.insert(ball.id)
                #expect(ball.kind == "spirit_ball")
                #expect(ball.y >= world.tuning.heroHeight)
                #expect(ball.vx == -100 && ball.gravity == 0)
            }
        }
        #expect(throwCount >= 1)
    }

    @Test func hauntedPortraitHoversOverheadAndFiresLowMagicShots() throws {
        var world = RunnerWorld(level: hauntedLevel([.init(at: 800, kind: .hauntedPortrait)]), boss: nil)
        advance(&world) { !$0.entities.isEmpty }
        let portrait = try #require(world.entities.first)
        #expect(portrait.y == 32)
        #expect(portrait.box.minY > world.tuning.heroHeight)
        #expect(!ItemKind.hauntedPortrait.spec.stompable)
        advance(&world) { !$0.hazards.isEmpty }
        let shot = try #require(world.hazards.first)
        #expect(shot.kind == "magic_shot" && shot.y == 4 && shot.width == 10 && shot.height == 6)
        #expect(shot.vx == -110 && shot.gravity == 0)
        #expect((world.entities.first?.x ?? .infinity) < portrait.x)
        #expect(hit(world.run(4)))
        // Out of reach of yarn from the ground; from a hop it takes two.
        #expect(!yarnHit(volley(at: .hauntedPortrait, count: 2)))
        #expect(!defeated(jumpVolley(at: .hauntedPortrait, count: 1), .hauntedPortrait))
        #expect(defeated(jumpVolley(at: .hauntedPortrait, count: 2), .hauntedPortrait))
    }

    @Test func cursedArmorSleepsAsAStatueThenWakesWalksAndSlashes() throws {
        var world = RunnerWorld(level: hauntedLevel([.init(at: 800, kind: .cursedArmor)]), boss: nil, stats: hero(2))
        advance(&world) { !$0.entities.isEmpty }
        let statue = try #require(world.entities.first)
        #expect(statue.state == .idle && !statue.isTangible)
        // Asleep it does not move, and yarn bounces off the stone.
        advance(&world) { gap($0, .cursedArmor) < 250 }
        var shooter = world
        let early = shoot(&shooter, flight: 0.9)
        #expect(bounced(early))
        #expect(!yarnHit(early))
        world.run(0.5)
        #expect(world.entities.first?.x == statue.x)

        let waking = advance(&world) { $0.entities.first?.state == .warning }
        #expect(waking.contains { if case .waking = $0 { true } else { false } })
        #expect(gap(world, .cursedArmor) < 140 && gap(world, .cursedArmor) > 120)
        #expect(world.entities.first?.isTangible == false)
        let warnedAt = world.time
        advance(&world, limit: 1) { $0.entities.first?.state == .active }
        #expect(abs(world.time - warnedAt - 0.5) < 0.05)
        let woke = try #require(world.entities.first)
        #expect(woke.isTangible)
        // Awake: yarn lands, it walks in, and touching it hurts (no stomp).
        var awake = world
        let awakeShot = awake.run(0.05, Input(fireHeld: true)) + awake.run(0.4)
        #expect(yarnHit(awakeShot) && !bounced(awakeShot))
        world.run(0.25)
        #expect((world.entities.first?.x ?? .infinity) < woke.x)
        #expect(hit(world.run(2)))
        #expect(!ItemKind.cursedArmor.spec.stompable)
    }

    @Test func candleCatWalksInSendingFireOrbsAlongTheGroundAndBurnsAStomper() throws {
        var world = RunnerWorld(level: hauntedLevel([.init(at: 800, kind: .candleCat)]), boss: nil)
        advance(&world) { !$0.entities.isEmpty }
        let start = try #require(world.entities.first?.x)
        advance(&world) { !$0.hazards.isEmpty }
        let orb = try #require(world.hazards.first)
        #expect(orb.kind == "fire_orb" && orb.y == 2 && orb.width == 8 && orb.height == 8 && orb.vx == -80)
        #expect((world.entities.first?.x ?? start) < start)
        #expect(stompAttempts(.candleCat).isEmpty)
        #expect(defeated(volley(at: .candleCat, count: 1), .candleCat))
    }

    @Test func poltergeistBookLobsBoltsThatFadeWhereTheyLand() throws {
        var world = RunnerWorld(level: hauntedLevel([.init(at: 800, kind: .poltergeistBook)]), boss: nil)
        advance(&world) { !$0.entities.isEmpty }
        #expect(world.entities.first?.y == 48)
        advance(&world) { !$0.hazards.isEmpty }
        let bolt = try #require(world.hazards.first)
        #expect(bolt.kind == "magic_bolt" && bolt.gravity > 0 && bolt.y > 30)
        var last = bolt
        var events: [GameEvent] = []
        while let current = world.hazards.first(where: { $0.id == bolt.id }), world.time < 10 {
            last = current
            #expect(!current.rolling)
            events += world.step(Input(), dt: dt)
        }
        #expect(events.contains(.hazardBroke(id: bolt.id)))
        #expect(last.y < 6)
        #expect(last.x - world.distance > 20)
        // Up at 48 it takes yarn thrown near the top of a full jump.
        #expect(!yarnHit(volley(at: .poltergeistBook, count: 1)))
        #expect(defeated(jumpVolley(at: .poltergeistBook, count: 1, fireAbove: 42), .poltergeistBook))
    }

    @Test func gargoyleCatPerchesThenLeapsAheadAndWalksIn() throws {
        var world = RunnerWorld(level: hauntedLevel([.init(at: 900, kind: .gargoyleCat)]), boss: nil, stats: hero(2))
        advance(&world) { !$0.entities.isEmpty }
        let perched = try #require(world.entities.first)
        #expect(!perched.isTangible)
        advance(&world) { gap($0, .gargoyleCat) < 320 }
        var shooter = world
        #expect(bounced(shoot(&shooter, flight: 1.3)))
        world.run(0.3)
        #expect(world.entities.first?.x == perched.x)

        let leap = try #require(ItemKind.gargoyleCat.spec.leap)
        var events = advance(&world) { $0.entities.first?.state == .warning }
        #expect(events.contains { if case .waking = $0 { true } else { false } })
        events = advance(&world, limit: 1) { $0.entities.first?.state == .leaping }
        #expect(events.contains { if case .leapt = $0 { true } else { false } })
        #expect(world.entities.first?.isTangible == true)
        var top = 0.0
        events = []
        while world.entities.first?.state == .leaping, world.time < 20 {
            events += world.step(Input(), dt: dt)
            top = max(top, world.entities.first?.y ?? 0)
        }
        #expect(events.contains { if case .leapLanded = $0 { true } else { false } })
        let landed = try #require(world.entities.first)
        #expect(landed.state == .active && landed.y == 0)
        #expect(abs(perched.x - leap.distance - landed.x) < 6)
        #expect(top > leap.height - 4)
        // It comes down in front of the kitten and walks in.
        #expect(landed.x - world.distance > 18)
        world.run(0.1)
        #expect((world.entities.first?.x ?? .infinity) < landed.x)
        #expect(hit(world.run(2)))
        // A landing on it is a safe bounce that does not break the stone.
        let landings = stompAttempts(.gargoyleCat, at: 500)
        #expect(landings.contains { !hit($0) })
        #expect(landings.allSatisfy { !defeated($0, .gargoyleCat) })
    }

    @Test func shadowCatIsUnseenThenAppearsAheadFlashesAndDashes() throws {
        var world = RunnerWorld(level: hauntedLevel([.init(at: 900, kind: .shadowCat)]), boss: nil, stats: hero(2))
        advance(&world) { !$0.entities.isEmpty }
        let hidden = try #require(world.entities.first)
        #expect(hidden.state == .hidden && !hidden.isTangible && !hidden.catchesYarn)
        let passed = shoot(&world, flight: 0.6)
        #expect(!bounced(passed) && !yarnHit(passed))

        let events = advance(&world) { $0.entities.first?.state == .warning }
        #expect(events.contains { if case .teleported = $0 { true } else { false } })
        let shown = try #require(world.entities.first)
        #expect(abs(shown.x - world.distance - 80) < 1)
        #expect(!shown.isTangible)
        // While it flashes it keeps its place ahead of the runner.
        world.run(0.2)
        #expect(abs((world.entities.first?.x ?? 0) - world.distance - 80) < 1)
        advance(&world, limit: 1) { $0.entities.first?.state == .active }
        let dashing = try #require(world.entities.first)
        #expect(dashing.isTangible && dashing.catchesYarn)
        var standing = world
        standing.run(0.05)
        #expect((standing.entities.first?.x ?? .infinity) < dashing.x - 4)
        #expect(hit(standing.run(1)))
        // A jump timed off its flash lands on it: a stomp kills.
        var flashed = RunnerWorld(level: hauntedLevel([.init(at: 900, kind: .shadowCat)]), boss: nil)
        advance(&flashed) { $0.entities.first?.state == .warning }
        let stomps = stride(from: 0.0, to: 0.8, by: 0.02).compactMap { delay -> [GameEvent]? in
            var world = flashed
            var events = world.run(delay)
            events += world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
            events += world.run(1.5, Input(jumpHeld: true))
            return events.contains { if case .stomped = $0 { true } else { false } } ? events : nil
        }
        #expect(stomps.contains { defeated($0, .shadowCat) && !hit($0) })
    }

    static let hauntedBotCases: [(ItemKind, Int)] = hauntedCreatures.flatMap { kind in
        [1, 4].filter { $0 >= kind.spec.minHeroLevel }.map { (kind, $0) }
    }

    @Test(arguments: MechanicsTests.hauntedBotCases)
    func botClearsEachHauntedCreatureWithoutAHit(kind: ItemKind, entry: Int) {
        let level = hauntedLevel([.init(at: 400, kind: kind), .init(at: 850, kind: kind)], length: 1400, entry: entry)
        #expect(LevelValidator.botRun(level, boss: nil).finished)
    }

    @Test func botClearsAHauntedRunOfEveryCreature() {
        let items = Self.hauntedCreatures.enumerated().map { PlacedItem(at: 400 + Double($0.offset) * 320, kind: $0.element) }
        #expect(LevelValidator.botRun(hauntedLevel(items, length: 3200, entry: 4), boss: nil).finished)
    }

    // MARK: - Solid tops

    /// Landings that came down on top: attempts where nothing hurt before the first stomp. (A hop too
    /// low to clear the top can clip a face first; that is running into it, not landing on it.)
    func cleanLandings(_ attempts: [[GameEvent]]) -> [[GameEvent]] {
        attempts.filter { events in
            guard let stomp = events.firstIndex(where: { if case .stomped = $0 { true } else { false } }) else { return false }
            return !hit(Array(events[..<stomp]))
        }
    }

    /// Stumps, gravestones, snow mounds and the stump cat read as something to stand on: landing on
    /// top bounces off safely (and does not break the stump cat), but running into a side hurts.
    @Test(arguments: [ItemKind.stump, .tombstone, .snowdrift, .stumpCat])
    func landingOnASolidTopIsASafeBounceButItsSideHurts(kind: ItemKind) {
        // The stump cat is met close to the start, so its first leaf comes while the kitten is
        // already in the air on its way onto the top (otherwise the leaf hits first).
        let landings = cleanLandings(stompAttempts(kind, at: kind == .stumpCat ? 180 : 400))
        #expect(!landings.isEmpty, "\(kind.rawValue): no landing on top")
        for events in landings {
            #expect(!hit(events), "\(kind.rawValue): hurt by a landing on top")
            #expect(!defeated(events, kind))
        }
        #expect(kind.spec.solid)                                  // still terrain for Ghost Dash
        var runner = RunnerWorld(level: flatLevel(items: [.init(at: 400, kind: kind)]), boss: nil)
        #expect(hit(runner.run(6)), "\(kind.rawValue): running into its side is a hit")
    }

    @Test func aBushsThornsStillHurtFromAbove() {
        #expect(stompAttempts(.bush).isEmpty)
        var world = RunnerWorld(level: flatLevel(items: [.init(at: 400, kind: .bush)]), boss: nil)
        #expect(hit(world.run(6)))
    }

    /// The device report: a stump cat standing on a 40-high ledge, landed on from a jump along the
    /// ledge (the kitten starts up on it). Every landing on its top is safe.
    @Test func aStumpCatOnALedgeIsSafeToLandOn() {
        let landings = cleanLandings(stompAttempts(.stumpCat, at: 180, terrain: [Terrain(at: 0, width: 600, height: 40)]))
        #expect(!landings.isEmpty)
        for events in landings {
            #expect(!hit(events))
            #expect(!defeated(events, .stumpCat))
        }
    }

    /// Who touches what, kind by kind and state by state.
    @Test func touchingSolidTopsDormantStatuesAndAwakeEnemies() {
        func touch(_ kind: ItemKind, _ state: EntityState? = nil, above: Bool) -> Entity.Touch {
            var entity = Entity(id: 1, kind: kind, x: 0, y: 0, hp: kind.spec.hp)
            if let state { entity.state = state }
            return entity.touch(fromAbove: above)
        }
        // Props: a bounce on top, a hit from the side. Thorns, gears and crate walls hurt either way.
        for kind in [ItemKind.stump, .tombstone, .snowdrift, .stumpCat] {
            #expect(touch(kind, above: true) == .bounce, "\(kind.rawValue)")
            #expect(touch(kind, above: false) == .hurt, "\(kind.rawValue)")
        }
        for kind in [ItemKind.bush, .gear, .crateWall] {
            #expect(touch(kind, above: true) == .hurt, "\(kind.rawValue)")
        }
        // Dormant statue and perched gargoyle (also while blinking awake): a safe bounce on top,
        // nothing from the side.
        for kind in [ItemKind.cursedArmor, .gargoyleCat] {
            for state in [EntityState.idle, .warning] {
                #expect(touch(kind, state, above: true) == .bounce, "\(kind.rawValue) \(state)")
                #expect(touch(kind, state, above: false) == .none, "\(kind.rawValue) \(state)")
            }
        }
        // Awake, they keep their rules: the armor's slash hurts even from above; the gargoyle is a
        // safe bounce on top, a hit from the side, in the air too.
        #expect(touch(.cursedArmor, .active, above: true) == .hurt)
        #expect(touch(.gargoyleCat, .active, above: true) == .bounce)
        #expect(touch(.gargoyleCat, .leaping, above: false) == .hurt)
        // An unseen shadow is not there at all; dashing, a stomp kills it.
        #expect(touch(.shadowCat, .hidden, above: true) == .none)
        #expect(touch(.shadowCat, .warning, above: true) == .none)
        #expect(touch(.shadowCat, .active, above: true) == .stompKill)
        // Unchanged elsewhere: a squirrel is stomped, a curled hedgehog's spikes hurt.
        #expect(touch(.squirrel, above: true) == .stompKill)
        #expect(touch(.hedgehog, .curled, above: true) == .hurt)
        #expect(touch(.snailCat, .curled, above: true) == .bounce)
    }

    // MARK: - Citadel creatures (Cataclysm Citadel sheet)

    static let citadelCreatures: [ItemKind] = [.lavaSlime, .fireImp, .stoneGuard, .hellHound, .emberBat,
                                               .flameArcher, .chainsawCat, .fireWisp]

    /// A flat test level at world 4's speed.
    func citadelLevel(_ items: [PlacedItem], length: Double = 2000, entry: Int = 5) -> LevelDefinition {
        var level = flatLevel(items: items, length: length, entry: entry, reward: max(entry, 2))
        level.speed = 140
        return level
    }

    @Test func citadelCreaturesHaveTheirIdsAndHitboxes() {
        let expected: [(ItemKind, String, Double, Double, Int, Int)] = [
            (.lavaSlime, "lava_slime", 20, 14, 1, 15), (.fireImp, "fire_imp", 18, 18, 1, 25),
            (.stoneGuard, "stone_guard", 26, 32, 4, 50), (.hellHound, "hell_hound", 26, 18, 2, 35),
            (.emberBat, "ember_bat", 18, 14, 1, 15), (.flameArcher, "flame_archer", 16, 24, 2, 30),
            (.chainsawCat, "chainsaw_cat", 26, 30, 5, 80), (.fireWisp, "fire_wisp", 14, 14, 1, 20),
        ]
        for (kind, id, width, height, hp, xp) in expected {
            #expect(kind.rawValue == id)
            #expect(kind.spec.width == width && kind.spec.height == height, "\(id) hitbox")
            #expect(kind.spec.hp == hp, "\(id) hp")
            #expect(kind.spec.xp == xp, "\(id) xp")
            #expect(kind.spec.yarnable, "\(id) is yarnable")
        }
        #expect(ItemKind.stoneGuard.spec.minHeroLevel == 3)
        #expect(ItemKind.chainsawCat.spec.minHeroLevel == 5)
        // The original citadel set is still there.
        for id in ["vent", "piston", "cannon", "debris", "mech_mouse", "gear", "crate_wall"] {
            #expect(ItemKind(rawValue: id) != nil)
        }
    }

    @Test func lavaSlimeSpitsGlobsThatLeaveABriefBurningPuddle() throws {
        var world = RunnerWorld(level: citadelLevel([.init(at: 700, kind: .lavaSlime)]), boss: nil)
        advance(&world) { $0.hazards.contains { $0.kind == "lava_glob" } }
        let glob = try #require(world.hazards.first)
        #expect(glob.gravity > 0 && glob.y > 6)
        advance(&world, limit: 2) { $0.hazards.first?.kind == "lava_puddle" }
        let puddle = try #require(world.hazards.first { $0.id == glob.id })
        #expect(puddle.kind == "lava_puddle" && puddle.y == 0 && puddle.vx == 0)
        #expect(puddle.width == 18 && puddle.height == 4)
        #expect(puddle.x - world.distance > 30)
        // It burns about a second, then is gone.
        let landedAt = world.time
        advance(&world, limit: 2) { !$0.hazards.contains { $0.id == glob.id } }
        #expect(abs(world.time - landedAt - 1.0) < 0.1)
        // Molten: no stomp. One yarn puts it out.
        #expect(!ItemKind.lavaSlime.spec.stompable)
        #expect(stompAttempts(.lavaSlime).isEmpty)
        #expect(takesYarn(.lavaSlime, 1))
    }

    @Test func fireImpKeepsItsDistanceThenDriftsInFiringLowFireballs() throws {
        let keep = try #require(ItemKind.fireImp.spec.keepAhead)
        var world = RunnerWorld(level: citadelLevel([.init(at: 800, kind: .fireImp)]), boss: nil)
        advance(&world) { gap($0, .fireImp) <= keep.distance + 0.5 }
        #expect(world.entities.first?.y == 40)
        let heldFrom = world.time
        var balls: [Hazard] = []
        while world.time - heldFrom < keep.duration - 0.05 {
            let known = Set(world.hazards.map(\.id))
            let step = world.step(Input(), dt: dt)
            if threw(step) { balls += world.hazards.filter { !known.contains($0.id) } }
            #expect(abs(gap(world, .fireImp) - keep.distance) < 0.5)
        }
        let ball = try #require(balls.first)
        #expect(ball.kind == "fireball_shot" && ball.y == 4 && ball.gravity == 0)
        world.run(0.5)
        #expect(gap(world, .fireImp) < keep.distance - 60)
        // Up at 40 it takes yarn from a hop; on the ground the fireballs must be jumped.
        #expect(defeated(jumpVolley(at: .fireImp, count: 1, from: 200, fireAbove: 34), .fireImp))
        var standing = RunnerWorld(level: citadelLevel([.init(at: 800, kind: .fireImp)]), boss: nil)
        #expect(hit(standing.run(6)))
    }

    @Test func stoneGuardIsASafeBounceAndThrowsAShortMagmaBlast() throws {
        let landings = cleanLandings(stompAttempts(.stoneGuard))
        #expect(!landings.isEmpty)
        for events in landings {
            #expect(!hit(events))
            #expect(!defeated(events, .stoneGuard))
        }
        var world = RunnerWorld(level: citadelLevel([.init(at: 700, kind: .stoneGuard)]), boss: nil)
        advance(&world) { !$0.entities.isEmpty }
        var blasts: [Double] = []
        while world.time < 8, !world.isOver, world.entities.contains(where: { $0.kind == .stoneGuard }) {
            let step = world.step(Input(), dt: dt)
            if threw(step) { blasts.append(gap(world, .stoneGuard)) }
        }
        #expect(!blasts.isEmpty)
        #expect(blasts.allSatisfy { $0 <= 60 })
        var blaster = RunnerWorld(level: citadelLevel([.init(at: 700, kind: .stoneGuard)]), boss: nil)
        advance(&blaster) { !$0.hazards.isEmpty }
        let blast = try #require(blaster.hazards.first)
        #expect(blast.kind == "magma_blast" && blast.y == 8 && blast.gravity == 0)
        #expect(takesYarn(.stoneGuard, 4))
    }

    @Test func hellHoundWarnsThenRunsInFromBehindAndOvertakes() throws {
        let chase = try #require(ItemKind.hellHound.spec.chase)
        var world = RunnerWorld(level: citadelLevel([.init(at: 600, kind: .hellHound)]), boss: nil)
        advance(&world) { !$0.entities.isEmpty }
        let lurking = try #require(world.entities.first)
        #expect(lurking.state == .hidden && !lurking.isTangible && !lurking.catchesYarn)
        // When the kitten reaches its spot, a warning (the app shows an arrow behind the kitten).
        let warned = advance(&world) { $0.entities.first?.state == .warning }
        #expect(warned.contains { if case .chaseWarning = $0 { true } else { false } })
        #expect(world.distance >= 600 - chase.trigger - 1)
        #expect(world.entities.first?.isTangible == false)
        advance(&world, limit: 2) { $0.entities.first?.state == .active }
        let hound = try #require(world.entities.first)
        #expect(hound.x < world.distance - chase.behind + 4)
        #expect(hound.isTangible)
        // Faster than the kitten: it catches up and passes.
        var standing = world
        let before = standing.distance - hound.x
        standing.run(0.2)
        let after = standing.distance - (standing.entities.first?.x ?? -.infinity)
        #expect(before - after > 0.2 * chase.overtake - 2)
        #expect(hit(standing.run(2)))
        // A jump timed off its appearance clears it (it is not stompable: only over it).
        let clean = stride(from: 0.0, to: 1.2, by: 0.04).contains { delay in
            var jumper = world
            var events = jumper.run(delay)
            events += jumper.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
            events += jumper.run(2, Input(jumpHeld: true))
            return !hit(events)
        }
        #expect(clean)
        #expect(!ItemKind.hellHound.spec.stompable)
    }

    @Test func emberBatSwoopsButNeverLowEnoughToHitAStandingKitten() {
        var world = RunnerWorld(level: citadelLevel([.init(at: 500, kind: .emberBat)]), boss: nil)
        var lowest = Double.infinity
        var events: [GameEvent] = []
        while world.time < 6 {
            events += world.step(Input(), dt: dt)
            if let bat = world.entities.first(where: { $0.kind == .emberBat }) { lowest = min(lowest, bat.y) }
        }
        #expect(lowest >= 28)
        #expect(!hit(events))
    }

    @Test func flameArcherStandsAndShootsLowArrowsAndAStompKillsIt() throws {
        var world = RunnerWorld(level: citadelLevel([.init(at: 700, kind: .flameArcher)]), boss: nil)
        advance(&world) { !$0.hazards.isEmpty }
        let arrow = try #require(world.hazards.first)
        #expect(arrow.kind == "flame_arrow" && arrow.y == 6 && arrow.gravity == 0)
        #expect(world.entities.first?.x == 700)
        #expect(stompAttempts(.flameArcher).contains { defeated($0, .flameArcher) })
        #expect(takesYarn(.flameArcher, 2))
    }

    @Test func chainsawCatsBladeReachesAheadOfItsBodyAndASuperPounceCutsThrough() throws {
        let reach = try #require(ItemKind.chainsawCat.spec.reach)
        var world = RunnerWorld(level: citadelLevel([.init(at: 700, kind: .chainsawCat)]), boss: nil)
        var firstHitGap: Double?
        while world.time < 8, firstHitGap == nil, !world.isOver {
            if hit(world.step(Input(), dt: dt)) { firstHitGap = gap(world, .chainsawCat) }
        }
        let bodyTouch = ItemKind.chainsawCat.spec.width / 2 + world.tuning.heroWidth / 2
        #expect((firstHitGap ?? 0) > bodyTouch + reach.width / 2)
        #expect(!ItemKind.chainsawCat.spec.stompable)
        #expect(takesYarn(.chainsawCat, 5))
        // The blade faces the way it walks.
        var entity = Entity(id: 1, kind: .chainsawCat, x: 100, y: 0, hp: 5)
        #expect((entity.reachBox?.maxX ?? .infinity) <= entity.box.minX)
        entity.reversed = true
        #expect((entity.reachBox?.minX ?? -.infinity) >= entity.box.maxX)
        // A Super Pounce through blade and body defeats it.
        let pounces = stride(from: 40.0, to: 90, by: 4).map { pounce(into: .chainsawCat, releaseAt: $0) }
        #expect(pounces.contains { defeated($0, .chainsawCat) && !hit($0) })
    }

    @Test func fireWispFlashesKeepsItsDistanceThenBurstsIntoARing() throws {
        let fuse = try #require(ItemKind.fireWisp.spec.fuse)
        var world = RunnerWorld(level: citadelLevel([.init(at: 700, kind: .fireWisp)]), boss: nil)
        advance(&world) { !$0.entities.isEmpty }
        #expect(world.entities.first?.y == 20)
        let lit = advance(&world) { $0.entities.first?.state == .warning }
        #expect(lit.contains { if case .fuseLit = $0 { true } else { false } })
        let litGap = gap(world, .fireWisp)
        #expect(litGap <= fuse.trigger && litGap > fuse.trigger - 5)
        world.run(fuse.warning / 2)
        #expect(abs(gap(world, .fireWisp) - litGap) < 0.5)
        let burst = advance(&world, limit: 1) { !$0.hazards.isEmpty }
        #expect(burst.contains { if case .exploded = $0 { true } else { false } })
        #expect(!defeated(burst, .fireWisp))
        #expect(!world.entities.contains { $0.kind == .fireWisp })
        let ring = try #require(world.hazards.first)
        #expect(ring.kind == "fire_ring" && ring.y == 0 && ring.width == fuse.ringWidth && ring.vx == 0)
        // Running on is burned; a hop over the ring, or a Ghost Dash through it, is not.
        var runner = world
        #expect(hit(runner.run(1)))
        var hopper = world
        #expect(!hit(hopper.step(Input(jumpPressed: true, jumpHeld: true), dt: dt) + hopper.run(1, Input(jumpHeld: true))))
        var dashed = RunnerWorld(level: citadelLevel([.init(at: 700, kind: .fireWisp)]), boss: nil, stats: hero(4))
        // Dashed as the kitten reaches the ring's near edge.
        advance(&dashed) { world in
            world.hazards.first.map { $0.box.minX - world.heroBox.maxX < 3 } ?? false
        }
        #expect(!hit(dashed.step(Input(pawPressed: true), dt: dt) + dashed.run(0.4)))
        // The ring burns out.
        world.run(fuse.ringLife + 0.1)
        #expect(!world.hazards.contains { $0.kind == "fire_ring" })
        // Shot down (from a hop) before it blows, it is defeated.
        #expect(defeated(jumpVolley(at: .fireWisp, count: 1, from: 200, fireAbove: 14), .fireWisp))
    }

    static let citadelBotCases: [(ItemKind, Int)] = citadelCreatures.flatMap { kind in
        [3, 5].filter { $0 >= kind.spec.minHeroLevel }.map { (kind, $0) }
    }

    @Test(arguments: MechanicsTests.citadelBotCases)
    func botClearsEachCitadelCreatureWithoutAHit(kind: ItemKind, entry: Int) {
        let level = citadelLevel([.init(at: 400, kind: kind), .init(at: 900, kind: kind)], length: 1500, entry: entry)
        #expect(LevelValidator.botRun(level, boss: nil).finished)
    }

    @Test func botClearsACitadelRunOfEveryCreature() {
        let items = Self.citadelCreatures.enumerated().map { PlacedItem(at: 400 + Double($0.offset) * 380, kind: $0.element) }
        #expect(LevelValidator.botRun(citadelLevel(items, length: 3800), boss: nil).finished)
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

    /// A vent that is firing just as the kitten passes. With feeble jumps (test tuning: no hold boost
    /// and a weak second jump) only a Ghost Dash gets through, and the bot must find it.
    @Test func botDashesThroughWhatNoJumpClears() {
        var tuning = Tuning()
        tuning.holdBoost = 0
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
