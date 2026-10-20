import Foundation

/// One damaging shape spawned by a boss attack.
public struct HazardSpec: Codable, Sendable, Equatable {
    /// Visual id, also the sprite name (`hazard_<kind>`).
    public var kind: String
    /// Seconds after the attack starts.
    public var delay: Double
    /// Bottom of the hazard above the ground. Low hazards are jumped, high ones are run under.
    public var y: Double
    public var width: Double
    public var height: Double
    /// Speed at which it approaches the hero on screen.
    public var closingSpeed: Double
    /// If set, spawns this far ahead of the hero instead of at the boss.
    public var ahead: Double?
    /// Seconds it is visible as a warning before it can hurt.
    public var arm: Double?
}

public struct SummonSpec: Codable, Sendable, Equatable {
    public var kind: ItemKind
    public var delay: Double
}

public struct BossAttack: Codable, Sendable, Equatable {
    public var name: String
    /// Wind-up before anything spawns.
    public var telegraph: Double
    /// Length of the attack itself; hazards and summons are timed inside it.
    public var duration: Double
    /// Pause afterwards, when `recover`-vulnerable bosses can be damaged.
    public var recover: Double
    public var hazards: [HazardSpec]
    public var summons: [SummonSpec]?
}

public struct BossPhase: Codable, Sendable, Equatable {
    /// Phase is active once HP fraction is at or below this (first phase uses 1).
    public var startsBelow: Double
    /// Attack names, cycled in order.
    public var attacks: [String]
    /// Extra look-alike copies of the boss during this phase. Only one copy (which one changes with
    /// every attack, deterministically) takes damage; yarn passes through the others.
    public var decoys: Int?

    public init(startsBelow: Double, attacks: [String], decoys: Int? = nil) {
        self.startsBelow = startsBelow
        self.attacks = attacks
        self.decoys = decoys
    }
}

public enum BossVulnerability: String, Codable, Sendable {
    case always, recover
}

public struct BossDefinition: Codable, Sendable, Equatable {
    public var id: String
    public var hp: Int
    public var width: Double
    public var height: Double
    /// Bottom of the hitbox above the ground.
    public var baseY: Double
    public var vulnerable: BossVulnerability
    /// Armour: while its HP fraction is above this, it can only be damaged while recovering, whatever
    /// `vulnerable` says; at or below it, `vulnerable` applies.
    public var armoredAbove: Double?
    public var attacks: [BossAttack]
    public var phases: [BossPhase]

    public init(id: String, hp: Int, width: Double, height: Double, baseY: Double, vulnerable: BossVulnerability,
                armoredAbove: Double? = nil, attacks: [BossAttack], phases: [BossPhase]) {
        self.id = id
        self.hp = hp
        self.width = width
        self.height = height
        self.baseY = baseY
        self.vulnerable = vulnerable
        self.armoredAbove = armoredAbove
        self.attacks = attacks
        self.phases = phases
    }

    /// Whether a hit lands now.
    public func isOpen(hpFraction: Double, action: BossAction) -> Bool {
        if action == .recover { return true }
        if let armoredAbove, hpFraction > armoredAbove { return false }
        return vulnerable == .always
    }
}

public enum BossAction: String, Sendable, Equatable {
    case intro, telegraph, attack, recover, dead
}

public struct BossState: Sendable, Equatable {
    public var id: String
    public var hp: Int
    public var maxHP: Int
    public var x: Double
    public var y: Double
    public var width: Double
    public var height: Double
    public var action: BossAction = .intro
    public var attackName: String = ""
    public var phaseIndex = 0
    /// Seconds spent in the current action.
    public var actionTime: Double = 0
    /// Copies on screen (1 + the phase's decoys) and which one is real, counted from the front.
    public var copies = 1
    public var trueCopy = 0
    var attackCursor = 0
    var spawnedHazards = 0
    var spawnedSummons = 0

    public var hpFraction: Double { maxHP > 0 ? Double(hp) / Double(maxHP) : 0 }
    /// Centre x of each copy. The first stands at the boss position; the others line up toward the hero.
    public var copyXs: [Double] { (0..<max(copies, 1)).map { x - Double($0) * (width + 8) } }
    /// Hitbox of the copy that takes damage.
    public var box: AABB {
        let xs = copyXs
        return AABB(centerX: xs[min(trueCopy, xs.count - 1)], bottom: y, width: width, height: height)
    }
}
