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

/// The final boss's tools: portals that bend yarn, stars that blink then fall, and a last phase that
/// opens only to an ability used through an attack.
@Suite struct VoidBossTests {
    func hero(_ level: Int) -> HeroStats { HeroStats(xp: Progression.xp(forLevel: level)) }

    func boss(attacks: [BossAttack], phases: [BossPhase], hp: Int = 5) -> BossDefinition {
        BossDefinition(id: "test_void", hp: hp, width: 40, height: 80, baseY: 0, vulnerable: .always,
                       attacks: attacks, phases: phases)
    }

    func arena(_ boss: BossDefinition, heroLevel: Int = 5) -> RunnerWorld {
        var world = RunnerWorld(level: flatLevel(length: 100), boss: boss, stats: hero(heroLevel))
        world.run(1.1)
        return world
    }

    /// Steps until `condition`, with `input`, returning the events.
    func advance(_ world: inout RunnerWorld, limit: Double = 6, _ input: Input = Input(),
                 until condition: (RunnerWorld) -> Bool) -> [GameEvent] {
        var events: [GameEvent] = []
        let end = world.time + limit
        while !condition(world), world.time < end, !world.isOver { events += world.step(input, dt: dt) }
        return events
    }

    // MARK: Portals

    func portalBoss(reverses: Bool = false, open: Double = 4) -> BossDefinition {
        let pair = PortalSpec(delay: 0, open: open, ahead: 60, y: 0, exitAhead: 120, exitY: 40, reverses: reverses)
        let warp = BossAttack(name: "warp", telegraph: 0.2, duration: open, recover: 5, hazards: [], portals: [pair])
        return boss(attacks: [warp], phases: [.init(startsBelow: 1, attacks: ["warp"])])
    }

    @Test func yarnThroughAnOpenPortalComesOutOfItsPair() throws {
        var world = arena(portalBoss())
        _ = advance(&world) { !$0.portals.isEmpty }
        let portal = try #require(world.portals.first)
        #expect(portal.isOpen)
        let events = world.step(Input(fireHeld: true), dt: dt) + advance(&world, limit: 1) { world in
            world.projectiles.first.map { $0.ported } ?? false
        }
        #expect(events.contains { if case .yarnPorted = $0 { true } else { false } })
        let shot = try #require(world.projectiles.first)
        // Out of the exit: higher, further on, still flying forward.
        #expect(shot.y >= 40)
        #expect(shot.x >= world.distance + 120 - 8)
        #expect(shot.vx > 0)
        // It goes through only once, even if it meets a portal again.
        let later = world.run(0.3)
        #expect(!later.contains { if case .yarnPorted = $0 { true } else { false } })
    }

    @Test func aReversingPortalSendsYarnBackTheOtherWay() throws {
        var world = arena(portalBoss(reverses: true))
        _ = advance(&world) { !$0.portals.isEmpty }
        _ = world.step(Input(fireHeld: true), dt: dt)
        _ = advance(&world, limit: 1) { $0.projectiles.first?.ported ?? false }
        let shot = try #require(world.projectiles.first)
        #expect(shot.vx < 0)
    }

    @Test func aClosedPortalLetsYarnStraightThroughAndPortalsAreDeterministic() throws {
        var world = arena(portalBoss(open: 0.3))
        _ = advance(&world) { !$0.portals.isEmpty }
        _ = advance(&world, limit: 1) { !($0.portals.first?.isOpen ?? true) }
        let events = world.step(Input(fireHeld: true), dt: dt) + world.run(0.6)
        #expect(!events.contains { if case .yarnPorted = $0 { true } else { false } })

        var a = arena(portalBoss()), b = arena(portalBoss())
        let ea = a.run(2, Input(fireHeld: true)), eb = b.run(2, Input(fireHeld: true))
        #expect(ea == eb)
        #expect(a.projectiles == b.projectiles)
    }

    // MARK: Falling stars

    @Test func aStarBlinksInPlaceThenFallsAndShattersOnTheGround() throws {
        let star = HazardSpec(kind: "star", delay: 0, y: 150, width: 12, height: 12, closingSpeed: 100, ahead: 160,
                              arm: 0.6, falls: true)
        let rain = BossAttack(name: "rain", telegraph: 0.2, duration: 0.2, recover: 5, hazards: [star])
        var world = arena(boss(attacks: [rain], phases: [.init(startsBelow: 1, attacks: ["rain"])]))
        _ = advance(&world) { !$0.hazards.isEmpty }
        let blinking = try #require(world.hazards.first)
        #expect(!blinking.isArmed)
        world.run(0.3)
        let still = try #require(world.hazards.first)
        // Telegraphed: it hangs at its x (fixed in the world) while it blinks.
        #expect(still.y == 150 && still.x == blinking.x)
        _ = advance(&world, limit: 1) { $0.hazards.first?.isArmed ?? false }
        world.run(0.2)
        #expect((world.hazards.first?.y ?? 150) < 150)
        let events = advance(&world, limit: 2) { $0.hazards.isEmpty }
        #expect(events.contains { if case .hazardBroke = $0 { true } else { false } })
    }

    // MARK: Final phase

    func finalBoss() -> BossDefinition {
        let paw = HazardSpec(kind: "shadow_paw", delay: 0.3, y: 0, width: 16, height: 14, closingSpeed: 220)
        let swipe = BossAttack(name: "swipe", telegraph: 0.4, duration: 0.6, recover: 0.8, hazards: [paw])
        return BossDefinition(id: "test_void", hp: 4, width: 40, height: 80, baseY: 0, vulnerable: .always,
                              attacks: [swipe],
                              phases: [.init(startsBelow: 1, attacks: ["swipe"], requires: [.ghostDash, .superPounce])],
                              openingTime: 2.0)
    }

    @Test func theFinalPhaseShrugsOffYarnUntilAnAbilityIsUsedThroughAnAttack() throws {
        var world = arena(finalBoss())
        // Yarn alone is blocked (fired again and again once the intro is over).
        var events: [GameEvent] = []
        for index in 0..<240 { events += world.step(Input(fireHeld: index % 20 < 2), dt: dt) }
        #expect(events.contains(.bossBlocked))
        #expect(!events.contains { if case .bossHit = $0 { true } else { false } })
        #expect(world.bossOpening == 0)

        // A Ghost Dash through a paw opens it.
        var dasher = arena(finalBoss(), heroLevel: 4)
        _ = advance(&dasher) { world in
            world.hazards.contains { $0.isArmed && $0.box.minX - world.heroBox.maxX < 4 }
        }
        events = dasher.step(Input(pawPressed: true), dt: dt) + dasher.run(0.4)
        #expect(events.contains(.bossExposed))
        #expect(!events.contains { if case .heroHit = $0 { true } else { false } })
        #expect(dasher.bossOpening > 0)
        // Then yarn lands, until the opening closes.
        events = dasher.run(0.05, Input(fireHeld: true)) + dasher.run(1.0)
        #expect(events.contains { if case .bossHit = $0 { true } else { false } })
        dasher.run(2.0)
        #expect(dasher.bossOpening == 0)
    }

    @Test func aSuperPounceOverAnAttackOpensItToo() {
        var world = arena(finalBoss())
        var events: [GameEvent] = []
        // Hold the paw to charge, and let go as a paw comes near.
        events += world.step(Input(pawPressed: true, pawHeld: true), dt: dt)
        events += advance(&world, Input(pawHeld: true)) { world in
            world.isPounceReady && world.hazards.contains { $0.isArmed && $0.box.minX - world.heroBox.maxX < 30 }
        }
        events += world.step(Input(), dt: dt) + world.run(0.8)
        #expect(events.contains(.pounced))
        #expect(events.contains(.bossExposed))
    }

    @Test func theBotUsesItsAbilitiesToBeatAFinalPhase() {
        var world = arena(finalBoss())
        var bot = Bot()
        var events: [GameEvent] = []
        while !world.isOver, world.time < 60 { events += world.step(bot.input(for: world, dt: dt), dt: dt) }
        #expect(events.contains(.bossDefeated))
        #expect(!events.contains { if case .heroHit = $0 { true } else { false } })
    }
}
