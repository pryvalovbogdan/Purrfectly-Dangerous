import Foundation

/// Everything a level file can place. Raw values are the ids used in level JSON and asset names.
public enum ItemKind: String, Codable, Sendable, CaseIterable {
    // World 1 — forest
    case bush, stump, squirrel, acorn, branchSquirrel = "branch_squirrel", hedgehog
    case slime, mushroomCat = "mushroom_cat", forestBat = "forest_bat", plantCat = "plant_cat", beeCat = "bee_cat"
    case stumpCat = "stump_cat", snailCat = "snail_cat", spiderCat = "spider_cat"
    // World 2 — frost
    case icicle, snowball, penguin, snowdrift
    // World 3 — haunted
    case ghostCat = "ghost_cat", bat, skeletonMouse = "skeleton_mouse", skull, bell, tombstone
    // World 4 — citadel
    case vent, piston, cannon, debris, mechMouse = "mech_mouse", gear, crateWall = "crate_wall"
    // Pickups
    case fish, yarnBasket = "yarn_basket"
}

/// Something an enemy throws or sends along the ground on a timer while the hero is in range.
public struct ThrowSpec: Sendable, Equatable {
    /// Hazard kind of the projectile (sprite `hazard_<projectile>`).
    public var projectile: String
    public var interval: Double
    /// Throws only while the hero is between 30 and this far away.
    public var range: Double
    /// World speed toward the hero.
    public var speed: Double
    /// Bottom of the projectile; nil launches it from the thrower's own height.
    public var y: Double?
    public var width: Double
    public var height: Double
    /// Lobbed: it falls under `Tuning.lobGravity`, then rolls on along the ground.
    public var arc = false
}

/// A fixed on/off rhythm read from the world clock, so every copy of the world agrees on it.
/// Each period starts with the active part; the last `warning` seconds before it are a warning.
public struct CycleSpec: Sendable, Equatable {
    public var period: Double
    public var activeFor: Double
    public var warning: Double

    public func state(at time: Double) -> EntityState {
        let phase = time.truncatingRemainder(dividingBy: period)
        if phase < activeFor { return .active }
        return phase >= period - warning ? .warning : .idle
    }
}

/// What a cycle switches: a trap that only hurts while active, or a body that only exists while active.
public enum CycleRole: Sendable, Equatable {
    case trap, phase
}

/// Hangs overhead; when the hero comes within `trigger` it blinks for `warning` seconds, then drops
/// and stays on the ground as a spike — or, for a creature that `walksOnLanding`, lands and walks on.
public struct FallSpec: Sendable, Equatable {
    public var trigger: Double
    public var warning: Double
    /// Hitbox of what is left on the ground: shards (a low thing to hop), or the creature itself.
    public var shardWidth = 14.0
    public var shardHeight = 6.0
    /// A creature on a thread rather than a falling object: out of reach (harmless, and yarn passes)
    /// while it hangs and blinks, and once down it walks at the item's `velocity` like any walker.
    public var walksOnLanding = false
}

/// How a flyer's height follows the gap to the hero: `high` while far away, down to `low` once close.
public struct FlightSpec: Sendable, Equatable {
    public var high: Double
    public var low: Double
    /// Gap to the hero at which the dive starts and ends.
    public var diveStart: Double
    public var diveEnd: Double

    public func height(gap: Double) -> Double {
        let progress = min(1, max(0, (diveStart - gap) / (diveStart - diveEnd)))
        return high + (low - high) * progress
    }
}

public struct ItemSpec: Sendable {
    /// Hitbox in world units (1 unit = 1 sprite pixel).
    public var width: Double
    public var height: Double
    /// Bottom of the hitbox above the ground.
    public var baseY: Double = 0
    public var hp: Int = 1
    public var xp: Int = 0
    /// World velocity along x; negative walks toward the hero.
    public var velocity: Double = 0
    public var hurtsOnTouch = true
    /// Landing on it from above is safe: the hero bounces off unhurt.
    public var stompable = false
    /// That landing also defeats it outright, whatever health it has left, and earns its XP.
    public var stompKills = false
    /// Yarn damages it (otherwise yarn passes through).
    public var yarnable = false
    /// Yarn stops against it and does nothing.
    public var deflectsYarn = false
    /// Terrain rather than a creature or hazard: Ghost Dash does not pass through it.
    public var solid = false
    /// Only a Super Pounce breaks it.
    public var breakable = false
    /// Hero level a player needs to get past it without being hit.
    public var minHeroLevel = 1
    public var throwing: ThrowSpec?
    /// Curls up into an unstompable, yarn-proof ball once the hero is this close.
    public var curlsAt: Double?
    public var cycle: CycleSpec?
    public var cycleRole: CycleRole = .trap
    public var fall: FallSpec?
    public var flight: FlightSpec?
}

extension ItemKind {
    /// Moves along the ground, so it cannot cross a ravine. A Super Pounce defeats it. A creature
    /// that drops from a thread only walks once it has landed (see `Entity.walks`).
    public var walks: Bool { spec.velocity != 0 && spec.baseY == 0 && spec.flight == nil }

    public var isPickup: Bool { self == .fish || self == .yarnBasket }

    public var spec: ItemSpec {
        switch self {
        // MARK: forest
        case .bush: ItemSpec(width: 22, height: 14, solid: true)
        case .stump: ItemSpec(width: 12, height: 24, solid: true)
        case .squirrel: ItemSpec(width: 18, height: 24, xp: 10, velocity: -20, stompable: true, stompKills: true,
                                 yarnable: true)
        case .acorn: ItemSpec(width: 12, height: 11, xp: 10, velocity: -60, yarnable: true)
        case .branchSquirrel:
            ItemSpec(width: 18, height: 20, baseY: 44, xp: 20, stompable: true, yarnable: true,
                     throwing: ThrowSpec(projectile: "acorn", interval: 2.0, range: 300, speed: 70, y: nil,
                                         width: 8, height: 8, arc: true))
        case .hedgehog: ItemSpec(width: 20, height: 15, xp: 15, velocity: -18, stompable: true, stompKills: true,
                                 yarnable: true, curlsAt: 90)
        case .slime: ItemSpec(width: 20, height: 14, xp: 10, velocity: -16, stompable: true, stompKills: true,
                              yarnable: true)
        // Puffs a spore from the top of its cap; it drops ahead of the kitten and rolls on along the ground.
        case .mushroomCat:
            ItemSpec(width: 18, height: 22, xp: 15, stompable: true, stompKills: true, yarnable: true,
                     throwing: ThrowSpec(projectile: "spore", interval: 2.0, range: 300, speed: 60, y: 24,
                                         width: 6, height: 6, arc: true))
        // Like the haunted bat: swoops down to just over a standing kitten's head (24), never lower.
        case .forestBat:
            ItemSpec(width: 18, height: 14, baseY: 42, xp: 15, velocity: -40, yarnable: true,
                     flight: FlightSpec(high: 42, low: 28, diveStart: 150, diveEnd: 70))
        // Shut (idle) it is harmless, open (warning) it is about to bite, biting (active) it hurts.
        // Its body is always there for yarn, whatever the cycle (see `RunnerWorld.hit(with:)`).
        case .plantCat:
            ItemSpec(width: 18, height: 30, hp: 2, xp: 20, yarnable: true,
                     cycle: CycleSpec(period: 2.0, activeFor: 0.6, warning: 0.5))
        // Hovers above a standing kitten and drifts in slowly, firing stings low along the ground.
        case .beeCat:
            ItemSpec(width: 18, height: 16, baseY: 40, xp: 20, velocity: -10, yarnable: true,
                     throwing: ThrowSpec(projectile: "sting", interval: 1.8, range: 300, speed: 90, y: 4,
                                         width: 8, height: 4))
        // A stump that is a turret: terrain (no Ghost Dash through it) that sends leaves along the ground.
        case .stumpCat:
            ItemSpec(width: 20, height: 28, hp: 2, xp: 25, yarnable: true, solid: true,
                     throwing: ThrowSpec(projectile: "leaf", interval: 2.0, range: 300, speed: 80, y: 2,
                                         width: 8, height: 5))
        // Hides in its shell once close (the curler behaviour): no stomp, yarn bounces off; jump it.
        case .snailCat: ItemSpec(width: 24, height: 16, xp: 15, velocity: -8, stompable: true, stompKills: true,
                                 yarnable: true, curlsAt: 80)
        case .spiderCat:
            ItemSpec(width: 18, height: 16, baseY: 60, xp: 20, velocity: -20, stompable: true, stompKills: true,
                     yarnable: true,
                     fall: FallSpec(trigger: 130, warning: 0.4, shardWidth: 18, shardHeight: 16, walksOnLanding: true))
        // MARK: frost
        case .icicle: ItemSpec(width: 8, height: 18, baseY: 70, fall: FallSpec(trigger: 130, warning: 0.35))
        case .snowball: ItemSpec(width: 14, height: 14, hp: 2, xp: 20, velocity: -60, yarnable: true)
        case .penguin: ItemSpec(width: 18, height: 12, xp: 20, velocity: -90, stompable: true, yarnable: true)
        case .snowdrift: ItemSpec(width: 20, height: 8, solid: true)
        // MARK: haunted
        // Drifts in overhead and down to the ground; it only exists while visible, and yarn passes through.
        case .ghostCat:
            ItemSpec(width: 14, height: 14, baseY: 44, velocity: -20,
                     cycle: CycleSpec(period: 2.0, activeFor: 1.2, warning: 0.3), cycleRole: .phase,
                     flight: FlightSpec(high: 44, low: 2, diveStart: 150, diveEnd: 80))
        case .bat:
            ItemSpec(width: 14, height: 10, baseY: 40, xp: 15, velocity: -40, yarnable: true,
                     flight: FlightSpec(high: 40, low: 26, diveStart: 150, diveEnd: 70))
        case .skeletonMouse:
            ItemSpec(width: 14, height: 14, hp: 2, xp: 25, stompable: true, stompKills: true, yarnable: true,
                     throwing: ThrowSpec(projectile: "bone", interval: 1.8, range: 300, speed: 90, y: 2,
                                         width: 8, height: 5))
        // A projectile on its own: flies straight in at head height, just over a kitten on the ground.
        case .skull: ItemSpec(width: 10, height: 10, baseY: 26, velocity: -80)
        case .bell:
            ItemSpec(width: 12, height: 14, baseY: 56, hurtsOnTouch: false,
                     throwing: ThrowSpec(projectile: "soundwave", interval: 2.0, range: 300, speed: 80, y: 0,
                                         width: 8, height: 8))
        case .tombstone: ItemSpec(width: 14, height: 24, solid: true)
        // MARK: citadel
        // Traps: the hitbox is the flame column / the slammed piston, and is harmless while inactive.
        case .vent: ItemSpec(width: 12, height: 60, cycle: CycleSpec(period: 2.4, activeFor: 0.8, warning: 0.5))
        case .piston: ItemSpec(width: 20, height: 70, cycle: CycleSpec(period: 2.0, activeFor: 0.6, warning: 0.4))
        case .cannon:
            ItemSpec(width: 14, height: 12, baseY: 30, hp: 2, xp: 25, yarnable: true,
                     throwing: ThrowSpec(projectile: "cannonball", interval: 2.2, range: 320, speed: 110, y: 26,
                                         width: 8, height: 8))
        case .debris: ItemSpec(width: 12, height: 12, baseY: 70, fall: FallSpec(trigger: 130, warning: 0.35))
        case .mechMouse: ItemSpec(width: 18, height: 12, hp: 2, xp: 30, velocity: -80, stompable: true,
                                  yarnable: true)
        case .gear: ItemSpec(width: 20, height: 26, solid: true)
        case .crateWall: ItemSpec(width: 16, height: 120, deflectsYarn: true, solid: true, breakable: true,
                                  minHeroLevel: 5)
        // MARK: pickups
        case .fish: ItemSpec(width: 10, height: 10, baseY: 14, xp: 5, hurtsOnTouch: false)
        case .yarnBasket: ItemSpec(width: 16, height: 400, hurtsOnTouch: false)
        }
    }
}

public struct AABB: Sendable, Equatable {
    public var minX, minY, maxX, maxY: Double

    public init(centerX: Double, bottom: Double, width: Double, height: Double) {
        minX = centerX - width / 2
        maxX = centerX + width / 2
        minY = bottom
        maxY = bottom + height
    }

    public func intersects(_ other: AABB) -> Bool {
        minX < other.maxX && maxX > other.minX && minY < other.maxY && maxY > other.minY
    }
}
