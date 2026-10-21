import Foundation

/// What the bot does with the paw button in a plan.
enum PawMove: Sendable, Equatable {
    /// A tap: Ghost Dash.
    case dash
    /// Let go of a fully charged paw: Super Pounce.
    case pounce
}

/// A move the bot commits to: an optional jump (hold time and when to double jump) and an optional
/// paw move at `pawAt` seconds.
struct BotPlan: Sendable, Equatable {
    var hold: Double?
    var secondAt: Double?
    var paw: PawMove?
    var pawAt = 0.0

    init(hold: Double? = nil, secondAt: Double? = nil, paw: PawMove? = nil, pawAt: Double = 0) {
        self.hold = hold
        self.secondAt = secondAt
        self.paw = paw
        self.pawAt = pawAt
    }

    /// From this point a plan that is back on the ground is finished.
    func settled(tuning: Tuning, dt: Double) -> Double {
        switch paw {
        case .dash: max(dt * 2, pawAt + tuning.dashDuration)
        case .pounce: pawAt + dt * 2
        case nil: dt * 2
        }
    }

    func input(elapsed: Double, dt: Double, base: Input) -> Input {
        var input = base
        if let hold {
            input.jumpPressed = elapsed < dt / 2
            input.jumpHeld = elapsed < hold
            if let secondAt, elapsed >= secondAt {
                input.jumpPressed = elapsed < secondAt + dt
                input.jumpHeld = elapsed < secondAt + hold
            }
        }
        let now = elapsed >= pawAt - dt / 2 && elapsed < pawAt + dt / 2
        switch paw {
        case .dash:
            // A one-frame tap.
            if now {
                input.pawPressed = true
                input.pawHeld = false
            }
        case .pounce:
            // The paw is already held and charged (see `Bot.baseInput`): let go for one frame.
            if now { input.pawHeld = false }
        case nil:
            break
        }
        return input
    }
}

/// Plays a level by simulating copies of the world a second ahead. Used to prove that a level and
/// its boss can be finished without taking a hit; it is not shipped as gameplay.
public struct Bot: Sendable {
    private var plan: BotPlan?
    private var elapsed = 0.0

    public init() {}

    /// Fire-button pattern as a pure function of world time, so look-ahead copies reproduce it.
    static func fireHeld(_ world: RunnerWorld) -> Bool {
        guard world.stats.has(.yarnShot) else { return false }
        return world.time.truncatingRemainder(dividingBy: 0.4) < 0.1
    }

    /// What the bot presses when it is not in the middle of a move. With Super Pounce it keeps the
    /// paw held, so a charged pounce is always one release away.
    static func baseInput(_ world: RunnerWorld) -> Input {
        Input(fireHeld: fireHeld(world), pawHeld: world.stats.has(.superPounce))
    }

    static func survives(_ start: RunnerWorld, plan: BotPlan?, horizon: Double, dt: Double) -> Bool {
        outcome(start, plan: plan, horizon: horizon, dt: dt).safe
    }

    /// Plays `plan` on a copy of the world. Being knocked back off a step is harmless, so it does not
    /// make a plan unsafe; `bumpedAt` is the face of the first step run into, if any.
    static func outcome(_ start: RunnerWorld, plan: BotPlan?, horizon: Double,
                        dt: Double) -> (safe: Bool, distance: Double, bumpedAt: Double?) {
        var bumpedAt: Double?
        var world = start
        var elapsed = 0.0
        var horizon = horizon
        var landed = false
        let settled = plan?.settled(tuning: start.tuning, dt: dt) ?? 0
        while elapsed < horizon {
            let base = baseInput(world)
            let input = plan?.input(elapsed: elapsed, dt: dt, base: base) ?? base
            for event in world.step(input, dt: dt) {
                switch event {
                case .heroHit, .heroDied: return (false, world.distance, bumpedAt)
                case .bumped: bumpedAt = bumpedAt ?? world.lastBumpFace
                default: break
                }
            }
            if world.phase == .victory || world.isOver { return (true, world.distance, bumpedAt) }
            elapsed += dt
            // A move only has to get the hero back on the ground safely; what comes after that is
            // a fresh decision, so stop looking shortly after touchdown.
            if plan != nil, !landed, world.onGround, elapsed > settled {
                landed = true
                horizon = min(horizon, elapsed + 0.12)
            }
        }
        return (true, world.distance, bumpedAt)
    }

    /// How far ahead, in seconds of running, the bot looks for a step it would bounce off.
    static let stepLookAhead = 0.7

    func candidates(for world: RunnerWorld) -> [BotPlan] {
        var candidates = [BotPlan(hold: 0.4), BotPlan(hold: 0.03)]
        if world.stats.has(.doublePounce) {
            candidates += [BotPlan(hold: 0.4, secondAt: 0.3), BotPlan(hold: 0.4, secondAt: 0.45)]
        }
        // With Super Pounce the paw is held for the pounce, so a dash is only a tap before it charges.
        if world.canDash, !world.isPounceReady {
            candidates += [BotPlan(paw: .dash), BotPlan(hold: 0.4, paw: .dash, pawAt: 0.15),
                           BotPlan(hold: 0.03, paw: .dash)]
        }
        if world.isPounceReady {
            candidates.append(BotPlan(paw: .pounce))
        }
        return candidates
    }

    public mutating func input(for world: RunnerWorld, dt: Double) -> Input {
        let base = Self.baseInput(world)
        if let plan {
            if world.onGround, elapsed > plan.settled(tuning: world.tuning, dt: dt) {
                self.plan = nil
            } else {
                defer { elapsed += dt }
                return plan.input(elapsed: elapsed, dt: dt, base: base)
            }
        }
        guard world.onGround else { return base }
        let threatened = !Self.survives(world, plan: nil, horizon: 0.45, dt: dt)
        // A step ahead that running on would bounce off: jump onto it from far enough out. Looking
        // further ahead than for threats leaves room for the take-off a tall step or a Double Pounce
        // needs; a move only counts if it ends with the hero past the face without a bounce.
        let face = Self.outcome(world, plan: nil, horizon: Self.stepLookAhead, dt: dt).bumpedAt
        guard threatened || face != nil else { return base }
        let options = candidates(for: world)
        var chosen: BotPlan?
        if let face {
            chosen = options.first {
                let result = Self.outcome(world, plan: $0, horizon: 1.3, dt: dt)
                return result.safe && result.bumpedAt == nil && result.distance > face
            }
        }
        if chosen == nil, threatened {
            chosen = options.first { Self.survives(world, plan: $0, horizon: 1.3, dt: dt) }
        }
        guard let chosen else { return base }
        plan = chosen
        elapsed = dt
        return chosen.input(elapsed: 0, dt: dt, base: base)
    }
}

public struct ValidationReport: Sendable, Equatable {
    public var problems: [String] = []
    /// Seconds of game time the bot needed; nil if it never finished.
    public var clearTime: Double?
    public var isValid: Bool { problems.isEmpty }
}

public enum LevelValidator {
    /// Static checks plus a no-hit bot run (the bot plays with a single heart).
    public static func validate(_ level: LevelDefinition, bosses: [String: BossDefinition],
                                tuning: Tuning = Tuning()) -> ValidationReport {
        var report = ValidationReport()
        let sorted = level.items.sorted { $0.at < $1.at }

        if level.speed <= 0 { report.problems.append("speed must be positive") }
        if level.length < 400 { report.problems.append("length must be at least 400") }
        if !(1...Progression.maxLevel).contains(level.entryHeroLevel) {
            report.problems.append("entryHeroLevel \(level.entryHeroLevel) is out of range")
        }
        let shrineAt = sorted.first { $0.kind == .yarnBasket }?.at
        if shrineAt != nil, level.shrineLevel == nil {
            report.problems.append("a yarn_basket is placed but shrineLevel is not set")
        }
        for item in sorted {
            if item.at < 150 { report.problems.append("\(item.kind.rawValue) at \(Int(item.at)) is inside the 150-unit start runway") }
            if item.at > level.length - 60 { report.problems.append("\(item.kind.rawValue) at \(Int(item.at)) is too close to the boss (length \(Int(level.length)))") }
            var guaranteed = level.entryHeroLevel
            if let shrineAt, let shrineLevel = level.shrineLevel, item.at > shrineAt { guaranteed = max(guaranteed, shrineLevel) }
            if item.kind.spec.minHeroLevel > guaranteed {
                report.problems.append("\(item.kind.rawValue) at \(Int(item.at)) needs hero level \(item.kind.spec.minHeroLevel), only \(guaranteed) is guaranteed there")
            }
        }

        report.problems += ravineProblems(in: level, items: sorted, tuning: tuning)
        report.problems += surfaceProblems(in: level, tuning: tuning)
        report.problems += terrainProblems(in: level, items: sorted, tuning: tuning)

        let boss = bosses[level.boss]
        if let boss {
            report.problems += problems(in: boss)
        } else {
            report.problems.append("boss '\(level.boss)' is not defined")
        }
        guard report.problems.isEmpty else { return report }

        let run = botRun(level, boss: boss, tuning: tuning)
        if run.finished {
            report.clearTime = run.time
        } else if let blocked = run.blocked {
            report.problems.append("no-hit bot \(blocked)")
        } else {
            report.problems.append("no-hit bot failed at distance \(Int(run.distance)) (\(run.phase))")
        }
        return report
    }

    /// Ground left between two ravines: room for the widest walker to turn around on.
    static let minimumLedge = 40.0
    /// Share of a full jump's reach a ravine may span, so clearing it does not need a perfect take-off.
    static let ravineJumpShare = 0.65

    static func ravineProblems(in level: LevelDefinition, items: [PlacedItem], tuning: Tuning) -> [String] {
        var problems: [String] = []
        let ravines = (level.ravines ?? []).sorted { $0.at < $1.at }
        // Once Double Pounce is guaranteed for the whole level, a ravine may need it.
        let reach = level.entryHeroLevel >= 3 ? tuning.doubleJumpReach(speed: level.speed)
                                              : tuning.jumpReach(speed: level.speed)
        for (index, ravine) in ravines.enumerated() {
            let name = "ravine at \(Int(ravine.at))"
            // Ledges over the gap break it up; the bot proves the hops between them.
            let bridged = (level.platforms ?? []).filter { $0.at < ravine.end && $0.end > ravine.at }
                .reduce(0.0) { $0 + min($1.end, ravine.end) - max($1.at, ravine.at) }
            let widest = (reach * ravineJumpShare + bridged).rounded(.down)
            if ravine.at < 150 { problems.append("\(name) is inside the 150-unit start runway") }
            if ravine.end > level.length - 60 { problems.append("\(name) is too close to the boss (length \(Int(level.length)))") }
            if ravine.width < 16 || ravine.width > widest {
                problems.append("\(name) is \(Int(ravine.width)) wide; it must be between 16 and \(Int(widest)) at speed \(Int(level.speed))")
            }
            if index > 0, ravine.at - ravines[index - 1].end < minimumLedge {
                problems.append("\(name) is too close to the one before it (leave \(Int(minimumLedge)) of ground)")
            }
            for item in items where item.y == nil && item.kind.spec.baseY == 0 {
                let half = item.kind.spec.width / 2
                if item.at + half > ravine.at, item.at - half < ravine.end {
                    problems.append("\(item.kind.rawValue) at \(Int(item.at)) stands in the \(name)")
                }
            }
        }
        return problems
    }

    /// Slick zones and platforms: inside the level, out of the start runway, and ledges low enough
    /// to land on from a full jump.
    static func surfaceProblems(in level: LevelDefinition, tuning: Tuning) -> [String] {
        var problems: [String] = []
        let apex = tuning.jumpVelocity * tuning.jumpVelocity / (2 * tuning.gravity)
        for zone in level.slick ?? [] {
            let name = "slick zone at \(Int(zone.at))"
            if zone.width <= 0 { problems.append("\(name) has no width") }
            if zone.at < 150 { problems.append("\(name) is inside the 150-unit start runway") }
            if zone.end > level.length - 60 { problems.append("\(name) is too close to the boss (length \(Int(level.length)))") }
        }
        for platform in level.platforms ?? [] {
            let name = "platform at \(Int(platform.at))"
            if platform.width < tuning.heroWidth { problems.append("\(name) is narrower than the hero") }
            if platform.y < 4 || platform.y > apex - 6 {
                problems.append("\(name) is \(Int(platform.y)) high; it must be between 4 and \(Int(apex - 6))")
            }
            if platform.at < 150 { problems.append("\(name) is inside the 150-unit start runway") }
            if platform.end > level.length - 60 { problems.append("\(name) is too close to the boss (length \(Int(level.length)))") }
            if platform.kind == "island", platform.mode != .solid {
                problems.append("\(name) is an island; islands are always solid")
            }
            if platform.mode == .blinks, platform.cycle.activeFor <= 0 || platform.cycle.activeFor >= platform.cycle.period {
                problems.append("\(name) blinks but solidFor must be between 0 and period")
            }
        }
        return problems
    }

    /// The camera does not follow the hero up or down: steps stay within this of the base ground so
    /// a double jump from the top and the floor of a dip both stay on screen (the landscape ground
    /// line is only 40 units above the bottom edge).
    static let maxTerrainHeight = 60.0
    static let maxDipDepth = 32.0
    /// A step the bot bounces off more often than this, or that keeps it back (from the first bounce
    /// until it is past the face) for longer than `maxHeldBack` seconds, counts as a softlock. So does
    /// no forward progress at all for `maxHeldBack` seconds.
    public static let maxBumps = 3
    public static let maxHeldBack = 4.0
    /// Headroom a climb leaves over the top of a jump, as for ledges.
    static let climbClearance = 6.0

    /// Highest step the hero is sure to climb with the abilities it is guaranteed.
    static func climbHeight(heroLevel: Int, tuning: Tuning) -> Double {
        let apex = Progression.abilities(forLevel: heroLevel).contains(.doublePounce) ? tuning.doubleJumpApex : tuning.jumpApex
        return (apex - climbClearance).rounded(.down)
    }

    /// Raised blocks and dips: inside the level, apart from ravines and the boss arena, walls low
    /// enough to climb with the hero level guaranteed there, and nothing standing across a step.
    static func terrainProblems(in level: LevelDefinition, items: [PlacedItem], tuning: Tuning) -> [String] {
        var problems: [String] = []
        let pieces = (level.terrain ?? []).sorted { $0.at < $1.at }
        guard !pieces.isEmpty else { return problems }
        let ground = GroundProfile(pieces)
        for (index, piece) in pieces.enumerated() {
            let name = "terrain at \(Int(piece.at))"
            if piece.width < tuning.heroWidth { problems.append("\(name) is narrower than the hero (\(Int(tuning.heroWidth)))") }
            if piece.height == 0 { problems.append("\(name) has no height") }
            if piece.height > maxTerrainHeight { problems.append("\(name) is \(Int(piece.height)) high; at most \(Int(maxTerrainHeight)) fits on screen") }
            if piece.height < -maxDipDepth { problems.append("\(name) is \(Int(-piece.height)) deep; at most \(Int(maxDipDepth)) fits on screen") }
            if piece.at < 150 { problems.append("\(name) is inside the 150-unit start runway") }
            if piece.end > level.length - 60 { problems.append("\(name) is too close to the boss (length \(Int(level.length))); the arena stays flat") }
            if index > 0, piece.at < pieces[index - 1].end {
                problems.append("\(name) overlaps the terrain at \(Int(pieces[index - 1].at))")
            }
            for ravine in level.ravines ?? [] where piece.at < ravine.end + tuning.heroWidth && piece.end > ravine.at - tuning.heroWidth {
                problems.append("\(name) is too close to the ravine at \(Int(ravine.at)) (leave \(Int(tuning.heroWidth)) of ground)")
            }
            for zone in level.slick ?? [] where piece.at < zone.end && piece.end > zone.at {
                problems.append("\(name) overlaps the slick zone at \(Int(zone.at)) (slick ground is base ground only)")
            }
        }
        let shrineAt = items.first { $0.kind == .yarnBasket }?.at
        for (at, rise) in ground.rises(step: tuning.stepUp) {
            var guaranteed = level.entryHeroLevel
            if let shrineAt, let shrineLevel = level.shrineLevel, at > shrineAt { guaranteed = max(guaranteed, shrineLevel) }
            let reach = climbHeight(heroLevel: guaranteed, tuning: tuning)
            if rise > reach {
                let how = Progression.abilities(forLevel: guaranteed).contains(.doublePounce) ? "a Double Pounce" : "one jump"
                problems.append("step at \(Int(at)) rises \(Int(rise)); \(how) at hero level \(guaranteed) climbs at most \(Int(reach))")
            }
        }
        for item in items where item.y == nil && item.kind.spec.baseY == 0 && !item.kind.isPickup {
            let half = item.kind.spec.width / 2
            if ground.changes(from: item.at - half, to: item.at + half) {
                problems.append("\(item.kind.rawValue) at \(Int(item.at)) stands across a step")
            }
        }
        for platform in level.platforms ?? [] where ground.highest(from: platform.at, to: platform.end) != 0
            || ground.lowest(from: platform.at, to: platform.end) != 0 {
            let under = ground.highest(from: platform.at, to: platform.end)
            if platform.y - under < 4 {
                problems.append("platform at \(Int(platform.at)) is \(Int(platform.y - under)) above the terrain under it; it must be at least 4")
            }
        }
        return problems
    }

    public static func problems(in boss: BossDefinition) -> [String] {
        var problems: [String] = []
        let names = Set(boss.attacks.map(\.name))
        if boss.hp <= 0 { problems.append("boss \(boss.id): hp must be positive") }
        if boss.phases.isEmpty { problems.append("boss \(boss.id): no phases") }
        if boss.phases.first?.startsBelow != 1 { problems.append("boss \(boss.id): first phase must have startsBelow 1") }
        if let armoredAbove = boss.armoredAbove, !(0..<1).contains(armoredAbove) {
            problems.append("boss \(boss.id): armoredAbove must be between 0 and 1")
        }
        for (index, phase) in boss.phases.enumerated() {
            if let decoys = phase.decoys, decoys < 0 { problems.append("boss \(boss.id): phase \(index) has negative decoys") }
            if phase.attacks.isEmpty { problems.append("boss \(boss.id): phase \(index) has no attacks") }
            for name in phase.attacks where !names.contains(name) {
                problems.append("boss \(boss.id): phase \(index) uses unknown attack '\(name)'")
            }
        }
        return problems
    }

    /// The bot plays the level on one heart. `blocked` says why the run was stopped early when a
    /// step keeps bouncing it back (see `maxBumps` and `maxHeldBack`): a softlock.
    static func botRun(_ level: LevelDefinition, boss: BossDefinition?, tuning: Tuning = Tuning(),
                       dt: Double = 1.0 / 60)
        -> (finished: Bool, time: Double, distance: Double, phase: Phase, blocked: String?) {
        let stats = HeroStats(xp: Progression.xp(forLevel: level.entryHeroLevel), maxHearts: 1)
        var world = RunnerWorld(level: level, boss: boss, stats: stats, tuning: tuning)
        var bot = Bot()
        let limit = level.length / max(level.speed, 1) + 240
        var furthest = world.distance, progressAt = 0.0
        var bumps: [Double: Int] = [:]
        var heldBy: (face: Double, since: Double)?
        func stop(_ why: String) -> (Bool, Double, Double, Phase, String?) {
            (false, world.time, world.distance, world.phase, why)
        }
        while !world.isOver, world.time < limit {
            let events = world.step(bot.input(for: world, dt: dt), dt: dt)
            if events.contains(.bumped), let face = world.lastBumpFace {
                bumps[face, default: 0] += 1
                if bumps[face, default: 0] > maxBumps {
                    return stop("bounced off the step at \(Int(face)) more than \(maxBumps) times")
                }
                if heldBy?.face != face { heldBy = (face, world.time) }
            }
            if let held = heldBy {
                if world.distance > held.face {
                    heldBy = nil
                } else if world.time - held.since > maxHeldBack {
                    return stop("was held back by the step at \(Int(held.face)) for over \(Int(maxHeldBack)) s")
                }
            }
            if world.distance > furthest + 1e-6 {
                furthest = world.distance
                progressAt = world.time
            } else if world.time - progressAt > maxHeldBack {
                return stop("made no progress at distance \(Int(world.distance)) for over \(Int(maxHeldBack)) s")
            }
        }
        return (world.phase == .won, world.time, world.distance, world.phase, nil)
    }
}
