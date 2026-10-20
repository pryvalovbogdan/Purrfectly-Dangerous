import Foundation

public struct PlacedItem: Codable, Sendable, Equatable {
    /// Distance from the level start, in world units.
    public var at: Double
    public var kind: ItemKind
    /// Overrides the kind's default height above ground (used for fish arcs).
    public var y: Double?
    /// Seconds added to the world clock for this item's on/off cycle (vents, pistons, ghost cats),
    /// so neighbours can run out of step.
    public var cycleOffset: Double?

    public init(at: Double, kind: ItemKind, y: Double? = nil, cycleOffset: Double? = nil) {
        self.at = at
        self.kind = kind
        self.y = y
        self.cycleOffset = cycleOffset
    }
}

/// A stretch of slick ground (spilled milk, ice): the hero runs faster on it and every jump from it
/// is a full jump.
public struct SlickZone: Codable, Sendable, Equatable {
    public var at: Double
    public var width: Double
    /// Look only, and the sprite name (`milk`, `ice`).
    public var kind: String?

    public var end: Double { at + width }

    public init(at: Double, width: Double, kind: String? = nil) {
        self.at = at
        self.width = width
        self.kind = kind
    }

    public func contains(_ x: Double) -> Bool { x >= at && x <= end }
}

public enum PlatformMode: String, Codable, Sendable {
    /// Always there.
    case solid
    /// Gives way `crumbleAfter` seconds after the hero first lands on it, for good.
    case crumbles
    /// There for `solidFor` seconds out of every `period`, on the world clock.
    case blinks
}

/// A one-way ledge: the hero lands on it from above and jumps up through it. It can bridge a ravine.
public struct Platform: Codable, Sendable, Equatable {
    /// Left end, as a distance from the level start.
    public var at: Double
    public var width: Double
    /// Height of its top above the ground.
    public var y: Double
    public var mode: PlatformMode
    /// Look only, and the sprite name (`bridge`, `ice_ledge`, `vanish`).
    public var kind: String?
    public var crumbleAfter: Double?
    public var period: Double?
    public var solidFor: Double?
    /// Seconds added to the world clock for a blinking platform.
    public var offset: Double?

    public static let defaultCrumbleAfter = 0.5
    public static let defaultPeriod = 2.4
    public static let defaultSolidFor = 1.6
    /// A blinking platform flickers this long before it vanishes.
    public static let blinkWarning = 0.4

    public var end: Double { at + width }

    public init(at: Double, width: Double, y: Double, mode: PlatformMode = .solid, kind: String? = nil,
                crumbleAfter: Double? = nil, period: Double? = nil, solidFor: Double? = nil, offset: Double? = nil) {
        self.at = at
        self.width = width
        self.y = y
        self.mode = mode
        self.kind = kind
        self.crumbleAfter = crumbleAfter
        self.period = period
        self.solidFor = solidFor
        self.offset = offset
    }

    public func spans(_ x: Double) -> Bool { x >= at && x <= end }

    /// The on/off rhythm of a blinking platform.
    public var cycle: CycleSpec {
        CycleSpec(period: period ?? Self.defaultPeriod, activeFor: solidFor ?? Self.defaultSolidFor, warning: 0)
    }
}

/// A gap in the ground. The hero falls in; walking enemies turn back at its rims.
public struct Ravine: Codable, Sendable, Equatable {
    /// Left rim, as a distance from the level start.
    public var at: Double
    public var width: Double

    public var end: Double { at + width }

    public init(at: Double, width: Double) {
        self.at = at
        self.width = width
    }

    /// True when there is no ground under `x`.
    public func isOpen(at x: Double) -> Bool {
        x > at && x < end
    }
}

public struct LevelDefinition: Codable, Sendable, Equatable {
    public var id: String
    /// Key into Lore.json for the display name.
    public var nameKey: String
    public var background: String
    /// Run speed in world units per second.
    public var speed: Double
    /// Distance at which the boss fight starts.
    public var length: Double
    /// Hero level a player is guaranteed to have on entry (set by earlier boss rewards).
    public var entryHeroLevel: Int
    /// Hero level granted by passing a yarn basket in this level.
    public var shrineLevel: Int?
    public var boss: String
    /// Hero level granted by defeating the boss.
    public var bossRewardLevel: Int
    public var items: [PlacedItem]
    public var ravines: [Ravine]?
    public var slick: [SlickZone]?
    public var platforms: [Platform]?

    public init(id: String, nameKey: String, background: String, speed: Double, length: Double,
                entryHeroLevel: Int, shrineLevel: Int? = nil, boss: String, bossRewardLevel: Int,
                items: [PlacedItem], ravines: [Ravine]? = nil, slick: [SlickZone]? = nil,
                platforms: [Platform]? = nil) {
        self.id = id
        self.nameKey = nameKey
        self.background = background
        self.speed = speed
        self.length = length
        self.entryHeroLevel = entryHeroLevel
        self.shrineLevel = shrineLevel
        self.boss = boss
        self.bossRewardLevel = bossRewardLevel
        self.items = items
        self.ravines = ravines
        self.slick = slick
        self.platforms = platforms
    }

    /// Fish placed in the level: everything a run through it can collect (fish come only from the
    /// level data, never from enemies or the boss).
    public var fishTotal: Int {
        items.lazy.filter { $0.kind == .fish }.count
    }
}

public enum ContentError: Error, Equatable {
    case missing(String)
    case invalid(String)
}

public enum ContentLoader {
    public static func level(from data: Data) throws -> LevelDefinition {
        var level = try JSONDecoder().decode(LevelDefinition.self, from: data)
        level.items.sort { $0.at < $1.at }
        return level
    }

    public static func bosses(from data: Data) throws -> [String: BossDefinition] {
        let list = try JSONDecoder().decode([BossDefinition].self, from: data)
        return Dictionary(list.map { ($0.id, $0) }, uniquingKeysWith: { first, _ in first })
    }

    public static func level(named id: String, in bundle: Bundle) throws -> LevelDefinition {
        try level(from: data(id, in: bundle))
    }

    /// All `level_*.json` files in the bundle, in play order (file names sort in play order).
    public static func levels(in bundle: Bundle) throws -> [LevelDefinition] {
        let urls = bundle.urls(forResourcesWithExtension: "json", subdirectory: nil) ?? []
        let levels = try urls
            .filter { $0.lastPathComponent.hasPrefix("level_") }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
            .map { try level(from: Data(contentsOf: $0)) }
        guard !levels.isEmpty else { throw ContentError.missing("level_*.json") }
        return levels
    }

    public static func bosses(in bundle: Bundle) throws -> [String: BossDefinition] {
        try bosses(from: data("Bosses", in: bundle))
    }

    private static func data(_ name: String, in bundle: Bundle) throws -> Data {
        guard let url = bundle.url(forResource: name, withExtension: "json") else {
            throw ContentError.missing("\(name).json")
        }
        return try Data(contentsOf: url)
    }
}
