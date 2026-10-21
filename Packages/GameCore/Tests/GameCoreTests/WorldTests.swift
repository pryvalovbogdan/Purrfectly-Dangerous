import Testing
@testable import GameCore

@Suite struct WorldTests {
    /// Apex of one jump from flat ground: the button held for `hold` seconds after the press (0: a
    /// tap, released by the first step).
    func apex(hold: Double, stats: HeroStats = HeroStats()) -> Double {
        var world = RunnerWorld(level: flatLevel(), boss: nil, stats: stats)
        _ = world.run(0.3)
        var top = 0.0
        var elapsed = 0.0
        _ = world.step(Input(jumpPressed: true, jumpHeld: hold > 0), dt: dt)
        while !world.onGround, !world.isOver {
            elapsed += dt
            _ = world.step(Input(jumpHeld: elapsed < hold), dt: dt)
            top = max(top, world.heroY)
        }
        return top
    }

    @Test func holdingJumpGoesClearlyHigherThanTapping() {
        let tuning = Tuning()
        let tap = apex(hold: 0)
        let hold = apex(hold: 1)
        let short = apex(hold: 0.1)
        // A tap still clears a bush with room to spare, and peaks low.
        #expect(tap <= 30)
        #expect(tap > ItemKind.bush.spec.height + 8)
        // A full hold is a big jump, well over a tall stump.
        #expect(hold >= 60)
        #expect(hold > tap + 30)
        // In between, the longer the hold the higher.
        #expect(short > tap + 5 && short < hold - 5)
        // The validator's numbers come from the same physics.
        #expect(abs(tap - tuning.tapApex) < 3)
        #expect(abs(hold - tuning.jumpApex) < 3)
    }

    /// Letting go ends the boost; the speed already gained is kept (no cut), so a release mid-rise
    /// never stalls the kitten in the air.
    @Test func releasingEndsTheBoostWithoutCuttingTheSpeed() {
        let tuning = Tuning()
        var world = RunnerWorld(level: flatLevel(), boss: nil)
        _ = world.run(0.3)
        _ = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        _ = world.run(0.08, Input(jumpHeld: true))
        let held = world.heroVY
        _ = world.step(Input(), dt: dt)
        #expect(abs(world.heroVY - (held - tuning.gravity * dt)) < 1e-9)
        // Pressing again does not bring the boost back.
        let released = world.heroVY
        _ = world.step(Input(jumpHeld: true), dt: dt)
        #expect(abs(world.heroVY - (released - tuning.gravity * dt)) < 1e-9)
    }

    /// A Double Pounce is always a full one, whether or not the button is held.
    @Test func aDoublePounceIsAlwaysFullHeight() {
        let tuning = Tuning()
        func gain(held: Bool) -> Double {
            var world = RunnerWorld(level: flatLevel(), boss: nil, stats: HeroStats(xp: Progression.xp(forLevel: 3)))
            _ = world.run(0.3)
            _ = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
            while world.heroVY > 0 { _ = world.step(Input(jumpHeld: true), dt: dt) }
            let start = world.heroY
            _ = world.step(Input(jumpPressed: true, jumpHeld: held), dt: dt)
            var top = start
            while !world.onGround { _ = world.step(Input(jumpHeld: held), dt: dt); top = max(top, world.heroY) }
            return top - start
        }
        let expected = tuning.heldRise(from: tuning.jumpVelocity * tuning.doubleJumpScale).height
        #expect(abs(gain(held: false) - expected) < 3)
        #expect(abs(gain(held: true) - expected) < 3)
    }

    /// Tapping jump twice in a row: a second tap in the falling half of a hop is kept until the feet
    /// touch down, so the next hop starts on landing instead of being dropped.
    @Test func aSecondTapWhileFallingJumpsAgainOnLanding() {
        func steps(_ world: RunnerWorld, _ condition: (RunnerWorld) -> Bool) -> Int {
            var world = world, n = 0
            while !condition(world) { _ = world.step(Input(), dt: dt); n += 1 }
            return n
        }
        var world = RunnerWorld(level: flatLevel(), boss: nil)
        _ = world.run(0.5)
        _ = world.step(Input(jumpPressed: true), dt: dt)
        let untilLanding = steps(world) { $0.onGround }
        let untilApex = steps(world) { $0.heroVY <= 0 }
        // Tap again just after the top of the hop.
        for _ in 0..<(untilApex + 1) { _ = world.step(Input(), dt: dt) }
        var events = world.step(Input(jumpPressed: true), dt: dt)
        for _ in 0..<(untilLanding - untilApex + 2) { events += world.step(Input(), dt: dt) }
        #expect(events.contains(.jumped(double: false)))
        #expect(!world.onGround)
    }

    @Test func doubleJumpNeedsTheAbility() {
        func jumps(level: Int) -> Int {
            var world = RunnerWorld(level: flatLevel(), boss: nil, stats: HeroStats(xp: Progression.xp(forLevel: level)))
            var events = world.run(0.3, Input(jumpPressed: true, jumpHeld: true))
            events += world.run(0.2, Input(jumpPressed: true, jumpHeld: true))
            return events.filter { if case .jumped = $0 { true } else { false } }.count
        }
        #expect(jumps(level: 2) == 1)
        #expect(jumps(level: 3) == 2)
    }

    /// What the jump button shows in the air: whether a Double Pounce is still there to use.
    @Test func canDoubleJumpTracksTheSecondJump() {
        let pouncer = HeroStats(xp: Progression.xp(forLevel: 3))
        var world = RunnerWorld(level: flatLevel(), boss: nil, stats: pouncer)
        _ = world.run(0.3)
        #expect(!world.canDoubleJump)                       // on the ground
        _ = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        #expect(world.canDoubleJump)                        // first jump used, second left
        _ = world.run(0.1, Input(jumpHeld: true))
        _ = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        #expect(!world.canDoubleJump)                       // both used

        var novice = RunnerWorld(level: flatLevel(), boss: nil)
        _ = novice.run(0.3)
        _ = novice.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        #expect(!novice.canDoubleJump)                      // ability not won

        // Running off a ravine's rim leaves nothing to push off from.
        var faller = RunnerWorld(level: flatLevel(ravines: [Ravine(at: 200, width: 120)]), boss: nil, stats: pouncer)
        while faller.onGround, !faller.isOver { _ = faller.step(Input(), dt: dt) }
        #expect(!faller.canDoubleJump)
    }

    /// Players tap: each press is held about a tenth of a second. Two quick taps must still carry
    /// the kitten over the widest ravine the validator allows once Double Pounce is guaranteed.
    @Test func twoQuickTapsClearAWideRavine() {
        let tap = 0.1
        let tuning = Tuning()
        let width = (tuning.doubleJumpReach(speed: 140) * LevelValidator.ravineJumpShare).rounded(.down)
        var timings = 0
        for takeOff in stride(from: 0.0, to: 40, by: 4) {
            for second in stride(from: 0.1, to: 0.45, by: 0.05) {
                var level = flatLevel(ravines: [Ravine(at: 300, width: width)])
                level.speed = 140
                var world = RunnerWorld(level: level, boss: nil, stats: HeroStats(xp: Progression.xp(forLevel: 3)))
                var jumpedAt: Double?
                while world.time < 4, !world.isOver {
                    if jumpedAt == nil, 300 - world.distance < takeOff { jumpedAt = world.time }
                    let since = jumpedAt.map { world.time - $0 } ?? -1
                    let pressed = since == 0 || (since >= second && since < second + dt)
                    let held = (since >= 0 && since < tap) || (since >= second && since < second + tap)
                    _ = world.step(Input(jumpPressed: pressed, jumpHeld: held), dt: dt)
                }
                if !world.isOver { timings += 1 }
            }
        }
        #expect(timings >= 8)
    }

    @Test func runningIntoAStumpCostsAHeartThenGrantsImmunity() {
        var world = RunnerWorld(level: flatLevel(items: [.init(at: 200, kind: .stump), .init(at: 230, kind: .stump)]), boss: nil)
        let events = world.run(2.6)
        #expect(events.filter { $0 == .heroHit(heartsLeft: 2) }.count == 1)
        #expect(world.stats.hearts == 2)
    }

    @Test func threeHitsKill() {
        let stumps = [200.0, 400, 600].map { PlacedItem(at: $0, kind: .stump) }
        var world = RunnerWorld(level: flatLevel(items: stumps), boss: nil)
        let events = world.run(10)
        #expect(events.contains(.heroDied))
        #expect(world.phase == .dead)
        #expect(world.isOver)
    }

    /// Jumps at whichever take-off gap brings the hero down on top of the enemy.
    private func stomp(_ kind: ItemKind) -> (world: RunnerWorld, events: [GameEvent])? {
        for takeOff in stride(from: 20.0, to: 140, by: 4) {
            var world = RunnerWorld(level: flatLevel(items: [.init(at: 300, kind: kind)]), boss: nil)
            var events: [GameEvent] = []
            var jumped = false
            while world.time < 3.5 {
                let gap = (world.entities.first?.x ?? 1000) - world.distance
                let jump = !jumped && gap < takeOff
                jumped = jumped || jump
                events += world.step(Input(jumpPressed: jump, jumpHeld: true), dt: dt)
            }
            if events.contains(where: { if case .stomped = $0 { true } else { false } }) { return (world, events) }
        }
        return nil
    }

    /// Skeleton mice and hedgehogs kill on a stomp too, but throw bones / curl up first; see MechanicsTests.
    @Test(arguments: [ItemKind.squirrel])
    func landingOnItKillsItForItsXP(kind: ItemKind) throws {
        let (world, events) = try #require(stomp(kind))
        #expect(events.contains(.enemyDefeated(id: 1, kind: kind)))
        // One landing is enough, however much health it had.
        #expect(!events.contains { if case .enemyHit = $0 { true } else { false } })
        #expect(world.stats.xp == kind.spec.xp)
        #expect(world.score == kind.spec.xp)
        #expect(world.stats.hearts == 3)
    }

    @Test func theHeroBouncesOffAStompedEnemy() {
        var world = RunnerWorld(level: flatLevel(items: [.init(at: 200, kind: .squirrel)]), boss: nil)
        var bouncedUp = false
        // Jump late enough to come down on its head: a squirrel closes at 120 u/s, and a held jump is
        // back down at its head height about 0.75 s later.
        while world.time < 3 {
            let gap = (world.entities.first?.x ?? 1000) - world.distance
            let jump = world.onGround && gap < 100 && gap > 84
            let step = world.step(Input(jumpPressed: jump, jumpHeld: true), dt: dt)
            if step.contains(where: { if case .stomped = $0 { true } else { false } }) { bouncedUp = world.heroVY > 0 }
        }
        #expect(bouncedUp)
    }

    @Test(arguments: [ItemKind.penguin, .mechMouse])
    func landingOnItOnlyBounces(kind: ItemKind) throws {
        let (world, events) = try #require(stomp(kind))
        #expect(!events.contains { if case .enemyDefeated = $0 { true } else { false } })
        #expect(world.stats.xp == 0)
    }

    @Test func yarnNeedsLevelTwoAndDefeatsEnemies() {
        let level = flatLevel(items: [.init(at: 260, kind: .squirrel)])
        var novice = RunnerWorld(level: level, boss: nil)
        #expect(novice.run(0.5, Input(fireHeld: true)).isEmpty)

        var thrower = RunnerWorld(level: level, boss: nil, stats: HeroStats(xp: 100))
        let events = thrower.run(0.1, Input(fireHeld: true)) + thrower.run(1.5)
        #expect(events.contains { if case .yarnThrown = $0 { true } else { false } })
        #expect(events.contains { if case .enemyDefeated(_, kind: .squirrel) = $0 { true } else { false } })
    }

    @Test func snowballTakesTwoYarns() {
        var world = RunnerWorld(level: flatLevel(items: [.init(at: 420, kind: .snowball)]), boss: nil,
                                stats: HeroStats(xp: 100))
        var events: [GameEvent] = []
        for _ in 0..<2 {
            events += world.run(0.05, Input(fireHeld: true))
            events += world.run(0.4)
        }
        events += world.run(1.2)
        #expect(events.filter { if case .enemyHit = $0 { true } else { false } }.count == 1)
        #expect(events.contains { if case .enemyDefeated(_, kind: .snowball) = $0 { true } else { false } })
        #expect(world.stats.hearts == 3)
    }

    @Test(arguments: [ItemKind.stump, .bush])
    func yarnPassesThroughTerrainWithoutDestroyingIt(kind: ItemKind) {
        // A squirrel stands behind it: the shot must leave the terrain alone and still reach it.
        let level = flatLevel(items: [.init(at: 300, kind: kind), .init(at: 345, kind: .squirrel)])
        var thrower = RunnerWorld(level: level, boss: nil, stats: HeroStats(xp: 100))
        let events = thrower.run(0.05, Input(fireHeld: true)) + thrower.run(0.9)
        #expect(events.contains { if case .enemyDefeated(_, kind: .squirrel) = $0 { true } else { false } })
        #expect(!events.contains { if case .enemyDefeated(_, kind: kind) = $0 { true } else { false } })
        #expect(thrower.entities.contains { $0.kind == kind })
        // And it still hurts to run into.
        #expect((thrower.run(4)).contains(.heroHit(heartsLeft: 2)))
    }

    @Test func skeletonMouseHurtsFromTheSideAndTakesTwoYarns() {
        var walker = RunnerWorld(level: flatLevel(items: [.init(at: 200, kind: .skeletonMouse)]), boss: nil)
        var events = walker.run(3)
        #expect(events.contains(.heroHit(heartsLeft: 2)))
        #expect(walker.stats.xp == 0)

        var thrower = RunnerWorld(level: flatLevel(items: [.init(at: 380, kind: .skeletonMouse)]), boss: nil,
                                  stats: HeroStats(xp: 100))
        events = []
        for _ in 0..<2 {
            events += thrower.run(0.05, Input(fireHeld: true))
            events += thrower.run(0.4)
        }
        events += thrower.run(0.6)
        #expect(events.filter { if case .enemyHit = $0 { true } else { false } }.count == 1)
        #expect(events.contains { if case .enemyDefeated(_, kind: .skeletonMouse) = $0 { true } else { false } })
    }

    @Test func penguinIsFasterThanASquirrelAndTheBotGetsPastIt() {
        #expect(ItemKind.penguin.spec.velocity < ItemKind.squirrel.spec.velocity)
        var world = RunnerWorld(level: flatLevel(items: [.init(at: 200, kind: .penguin)]), boss: nil)
        var bot = Bot()
        while world.time < 3 { _ = world.step(bot.input(for: world, dt: dt), dt: dt) }
        #expect(world.stats.hearts == 3)
    }

    @Test func fishAndTheYarnBasketLevelTheHeroUp() {
        let items = [PlacedItem(at: 200, kind: .fish, y: 0), PlacedItem(at: 216, kind: .fish, y: 0),
                     PlacedItem(at: 300, kind: .yarnBasket)]
        var world = RunnerWorld(level: flatLevel(items: items, shrine: 2), boss: nil)
        let events = world.run(3.5)
        #expect(events.contains { if case .fish = $0 { true } else { false } })
        #expect(world.fishCollected == 2)
        #expect(world.score == 2 * ItemKind.fish.spec.xp)
        #expect(events.contains(.yarnBasket))
        #expect(events.contains(.leveledUp(level: 2, ability: .yarnShot)))
        #expect(world.stats.has(.yarnShot))
        #expect(world.stats.hearts == 3)
    }

    @Test func levelWithoutBossEndsAtItsLength() {
        var world = RunnerWorld(level: flatLevel(length: 400, reward: 3), boss: nil)
        let events = world.run(10)
        #expect(events.contains(.levelComplete))
        #expect(world.phase == .won)
        #expect(world.stats.level == 3)
    }

    // MARK: - Ravines

    @Test func runningIntoARavineEndsTheRunWhateverHeartsAreLeft() {
        var world = RunnerWorld(level: flatLevel(ravines: [Ravine(at: 200, width: 40)]), boss: nil)
        let events = world.run(3)
        #expect(events.contains(.heroFell))
        #expect(events.contains(.heroDied))
        #expect(world.phase == .dead)
        #expect(world.stats.hearts == 0)
        #expect(world.distance > 200 && world.distance < 240)
        #expect(world.heroY < 0)
    }

    @Test func aJumpClearsARavine() {
        var world = RunnerWorld(level: flatLevel(ravines: [Ravine(at: 200, width: 40)]), boss: nil)
        world.run(1.9)
        let events = world.run(1.5, Input(jumpPressed: true, jumpHeld: true))
        #expect(!events.contains(.heroFell))
        #expect(events.contains(.landed))
        #expect(world.onGround)
        #expect(world.distance > 240)
        #expect(world.stats.hearts == 3)
    }

    @Test func aJumpThatComesDownOverARavineFalls() {
        var world = RunnerWorld(level: flatLevel(ravines: [Ravine(at: 200, width: 40)]), boss: nil)
        // A full jump covers about 67 units at speed 100; from 150 it comes down at 217.
        world.run(1.5)
        let events = world.run(1.5, Input(jumpPressed: true, jumpHeld: true))
        #expect(events.contains(.heroFell))
        #expect(!events.contains(.landed))
    }

    @Test func theHeroStandsUntilTheirCentreIsPastTheRim() {
        var world = RunnerWorld(level: flatLevel(ravines: [Ravine(at: 200, width: 40)]), boss: nil)
        while world.distance < 199 { _ = world.step(Input(), dt: dt) }
        // The front half of the hitbox already hangs over the gap.
        #expect(world.heroBox.maxX > 200)
        #expect(world.onGround)
        #expect(!world.isOver)
    }

    @Test func noJumpingBackOutOfARavine() {
        var world = RunnerWorld(level: flatLevel(ravines: [Ravine(at: 200, width: 40)], entry: 3), boss: nil,
                                stats: HeroStats(xp: Progression.xp(forLevel: 3)))
        while !world.isOver, world.time < 5 {
            _ = world.step(Input(jumpPressed: world.distance > 201, jumpHeld: true), dt: dt)
        }
        #expect(world.phase == .dead)
    }

    @Test func aWalkerTurnsAroundAtARavine() throws {
        let level = flatLevel(items: [.init(at: 260, kind: .squirrel)], ravines: [Ravine(at: 200, width: 40)])
        var world = RunnerWorld(level: level, boss: nil)
        var leftmost = 1000.0
        var turnedAt: Double?
        while world.time < 1.8 {
            _ = world.step(Input(), dt: dt)
            guard let squirrel = world.entities.first else { continue }
            leftmost = min(leftmost, squirrel.box.minX)
            if squirrel.reversed, turnedAt == nil { turnedAt = squirrel.x }
        }
        // It never steps over the rim at 240, and after turning it walks away from it.
        #expect(leftmost >= 240)
        #expect(leftmost < 241)
        let squirrel = try #require(world.entities.first)
        #expect(squirrel.reversed)
        #expect(squirrel.x > (turnedAt ?? 1000))
    }

    @Test func aWalkerBetweenTwoRavinesPatrols() {
        let level = flatLevel(items: [.init(at: 560, kind: .penguin)],
                              ravines: [Ravine(at: 500, width: 40), Ravine(at: 600, width: 40)])
        var world = RunnerWorld(level: level, boss: nil)
        var turns = 0
        var reversed = false
        while world.time < 3.5 {
            _ = world.step(Input(), dt: dt)
            guard let penguin = world.entities.first else { continue }
            #expect(penguin.box.minX >= 540 && penguin.box.maxX <= 600)
            if penguin.reversed != reversed {
                reversed = penguin.reversed
                turns += 1
            }
        }
        #expect(turns >= 3)
    }

    @Test func flyersAndStaticThingsIgnoreRavines() {
        let level = flatLevel(items: [.init(at: 300, kind: .bat), .init(at: 310, kind: .ghostCat)],
                              ravines: [Ravine(at: 200, width: 40)])
        var world = RunnerWorld(level: level, boss: nil)
        world.run(1.2)
        #expect(world.entities.count == 2)
        #expect(world.entities.allSatisfy { !$0.reversed })
        #expect(world.entities.contains { $0.kind == .bat && $0.x < 260 })
    }

    @Test func ravinesInTheBossArenaAreIgnored() {
        let level = flatLevel(ravines: [Ravine(at: 380, width: 40)], length: 400, reward: 3)
        var world = RunnerWorld(level: level, boss: nil)
        #expect(world.ravines.isEmpty)
        world.run(10)
        #expect(world.phase == .won)
    }

    @Test func simulationIsDeterministic() throws {
        let level = try Content.level("level_01")
        let boss = try Content.bosses()[level.boss]
        func play() -> (Double, Int, Int) {
            var world = RunnerWorld(level: level, boss: boss)
            var bot = Bot()
            while !world.isOver, world.time < 120 { _ = world.step(bot.input(for: world, dt: dt), dt: dt) }
            return (world.distance, world.stats.xp, world.stats.hearts)
        }
        #expect(play() == play())
    }
}
