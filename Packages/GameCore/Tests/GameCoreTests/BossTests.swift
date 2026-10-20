import Testing
@testable import GameCore

@Suite struct BossTests {
    func boss(vulnerable: BossVulnerability = .always, armoredAbove: Double? = nil, decoys: Int? = nil,
              hp: Int = 3) -> BossDefinition {
        let hazard = HazardSpec(kind: "wave", delay: 0, y: 0, width: 16, height: 10, closingSpeed: 150)
        let slam = BossAttack(name: "slam", telegraph: 0.5, duration: 0.5, recover: 1.0, hazards: [hazard])
        let high = HazardSpec(kind: "blade", delay: 0, y: 42, width: 20, height: 10, closingSpeed: 150)
        let slash = BossAttack(name: "slash", telegraph: 0.5, duration: 0.5, recover: 1.0, hazards: [high])
        return BossDefinition(id: "test_boss", hp: hp, width: 40, height: 60, baseY: 0, vulnerable: vulnerable,
                              armoredAbove: armoredAbove, attacks: [slam, slash],
                              phases: [.init(startsBelow: 1, attacks: ["slam"], decoys: decoys),
                                       .init(startsBelow: 0.5, attacks: ["slash"], decoys: decoys)])
    }

    func arena(_ boss: BossDefinition, heroLevel: Int) -> RunnerWorld {
        var world = RunnerWorld(level: flatLevel(length: 100), boss: boss,
                                stats: HeroStats(xp: Progression.xp(forLevel: heroLevel)))
        world.run(1.1)
        return world
    }

    @Test func bossAppearsAtLevelLengthAndCyclesItsAttack() {
        var world = RunnerWorld(level: flatLevel(length: 100), boss: boss(), stats: HeroStats())
        var events = world.run(1.1)
        #expect(events.contains(.bossAppeared(id: "test_boss")))
        #expect(world.phase == .boss)
        events = world.run(2.2, Input())
        #expect(events.contains(.bossTelegraph(attack: "slam")))
        #expect(events.contains(.bossAttack(attack: "slam")))
        #expect(world.hazards.count == 1)
    }

    @Test func lowHazardHurtsUnlessJumped() {
        var standing = arena(boss(), heroLevel: 1)
        #expect(standing.run(5).contains(.heroHit(heartsLeft: 2)))

        var world = arena(boss(), heroLevel: 1)
        var bot = Bot()
        var hit = false
        while world.time < 12 {
            for event in world.step(bot.input(for: world, dt: dt), dt: dt) {
                if case .heroHit = event { hit = true }
            }
        }
        #expect(!hit)
    }

    @Test func yarnDefeatsBossAndGrantsReward() {
        var world = arena(boss(hp: 3), heroLevel: 2)
        var bot = Bot()
        var events: [GameEvent] = []
        while !world.isOver, world.time < 30 { events += world.step(bot.input(for: world, dt: dt), dt: dt) }
        #expect(events.contains(.bossDefeated))
        #expect(events.contains(.levelComplete))
        #expect(world.phase == .won)
    }

    @Test func secondPhaseSwitchesAttack() {
        var world = arena(boss(hp: 6), heroLevel: 2)
        var bot = Bot()
        var telegraphs: [String] = []
        while !world.isOver, world.time < 40 {
            for case let .bossTelegraph(attack) in world.step(bot.input(for: world, dt: dt), dt: dt) { telegraphs.append(attack) }
        }
        #expect(telegraphs.first == "slam")
        #expect(telegraphs.contains("slash"))
    }

    @Test func recoverOnlyBossBlocksShotsOutsideTheWindow() {
        var world = arena(boss(vulnerable: .recover, hp: 50), heroLevel: 2)
        var bot = Bot()
        var blocked = 0, hits = 0
        var hitActions: Set<BossAction> = []
        while world.time < 15 {
            for event in world.step(bot.input(for: world, dt: dt), dt: dt) {
                if event == .bossBlocked { blocked += 1 }
                if case .bossHit = event {
                    hits += 1
                    if let action = world.bossState?.action { hitActions.insert(action) }
                }
            }
        }
        #expect(blocked > 0)
        #expect(hits > 0)
        #expect(hitActions == [.recover])
    }

    /// Hits taken, and the boss action at each, while the bot plays the arena for `seconds`.
    func hits(_ boss: BossDefinition, seconds: Double) -> (hits: [(action: BossAction, fraction: Double)], blocked: Int) {
        var world = arena(boss, heroLevel: 2)
        var bot = Bot()
        var hits: [(BossAction, Double)] = []
        var blocked = 0
        while !world.isOver, world.time < seconds {
            for event in world.step(bot.input(for: world, dt: dt), dt: dt) {
                if event == .bossBlocked { blocked += 1 }
                if case .bossHit = event, let state = world.bossState { hits.append((state.action, state.hpFraction)) }
            }
        }
        return (hits, blocked)
    }

    @Test func armouredBossIsOnlyHitWhileRecoveringUntilItsHPDrops() {
        let (hits, blocked) = hits(boss(armoredAbove: 0.4, hp: 10), seconds: 60)
        #expect(blocked > 0)
        // Above 40% every hit landed in a recovery window; below it, hits land during attacks too.
        let armoured = hits.filter { $0.fraction >= 0.4 }
        let exposed = hits.filter { $0.fraction < 0.4 }
        #expect(!armoured.isEmpty && armoured.allSatisfy { $0.action == .recover })
        #expect(exposed.contains { $0.action != .recover })
    }

    @Test func armourRuleIsReadFromHPFraction() {
        let armoured = boss(armoredAbove: 0.4)
        #expect(!armoured.isOpen(hpFraction: 0.8, action: .attack))
        #expect(armoured.isOpen(hpFraction: 0.8, action: .recover))
        #expect(armoured.isOpen(hpFraction: 0.4, action: .attack))
        #expect(!boss(vulnerable: .recover).isOpen(hpFraction: 0.2, action: .telegraph))
    }

    @Test func onlyTheTrueCopyTakesDamageAndItMovesEachAttack() throws {
        var world = arena(boss(decoys: 2, hp: 50), heroLevel: 2)
        var trueCopies: [Int] = []
        var bot = Bot()
        while world.time < 12, !world.isOver {
            for case .bossTelegraph in world.step(bot.input(for: world, dt: dt), dt: dt) {
                trueCopies.append(world.bossState?.trueCopy ?? -1)
            }
        }
        let state = try #require(world.bossState)
        #expect(state.copies == 3)
        #expect(state.copyXs.count == 3)
        #expect(Set(trueCopies).count > 1)
        // The hitbox is the true copy's.
        #expect(state.box.minX == state.copyXs[state.trueCopy] - state.width / 2)
        // Yarn flies through the decoys in front and still lands on the real one.
        #expect(!hits(boss(decoys: 2, hp: 50), seconds: 15).hits.isEmpty)
    }
}
