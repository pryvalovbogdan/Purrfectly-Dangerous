import Foundation

/// Everything a level file can place. Raw values are the ids used in level JSON and asset names.
public enum ItemKind: String, Codable, Sendable, CaseIterable {
    // World 1 — forest
    case bush, stump, squirrel, acorn, branchSquirrel = "branch_squirrel", hedgehog
    case slime, mushroomCat = "mushroom_cat", forestBat = "forest_bat", plantCat = "plant_cat", beeCat = "bee_cat"
    case stumpCat = "stump_cat", snailCat = "snail_cat", spiderCat = "spider_cat"
    // World 2 — frost
    case icicle, snowball, penguin, snowdrift
    case iceSlime = "ice_slime", snowCat = "snow_cat", iceBat = "ice_bat", iceGolem = "ice_golem"
    case penguinSoldier = "penguin_soldier", snowyOwl = "snowy_owl", iceHedgehog = "ice_hedgehog", snowman
    case iciclePlant = "icicle_plant", miniYeti = "mini_yeti"
    // World 3 — haunted
    case ghostCat = "ghost_cat", bat, skeletonMouse = "skeleton_mouse", skull, bell, tombstone
    case hauntedPortrait = "haunted_portrait", cursedArmor = "cursed_armor", candleCat = "candle_cat"
    case poltergeistBook = "poltergeist_book", gargoyleCat = "gargoyle_cat", shadowCat = "shadow_cat"
    // World 4 — citadel
    case vent, piston, cannon, debris, mechMouse = "mech_mouse", gear, crateWall = "crate_wall"
    case lavaSlime = "lava_slime", fireImp = "fire_imp", stoneGuard = "stone_guard", hellHound = "hell_hound"
    case emberBat = "ember_bat", flameArcher = "flame_archer", chainsawCat = "chainsaw_cat", fireWisp = "fire_wisp"
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
    /// Lobbed: it falls under `Tuning.lobGravity`, then rolls on along the ground. With no `speed`
    /// it drops straight down and lies where it lands.
    public var arc = false
    /// Seconds in range before the first throw (the clock only runs while the hero is in range).
    public var windup = 0.6
    /// The thrower shows `EntityState.warning` for this long before each throw (0: no warning).
    public var warning = 0.0
    /// Fires once each time its trap cycle opens (turns active), instead of on `interval`.
    public var onCycleOpen = false
    /// A lobbed shot that fizzles out where it lands instead of rolling on.
    public var fades = false
    /// A lobbed shot that lands as something else that lingers a while (a burning puddle).
    public var linger: LingerSpec?
}

/// What a landed lob becomes: a still hazard of `kind` and this size, gone after `seconds`.
public struct LingerSpec: Sendable, Equatable {
    public var kind: String
    public var seconds: Double
    public var width: Double
    public var height: Double
}

/// Keeps its distance: once it comes within `distance` of the hero it stays that far ahead, moving
/// with it, for `duration` seconds; then it drifts in at the item's `velocity`.
public struct KeepAheadSpec: Sendable, Equatable {
    public var distance: Double
    public var duration: Double
}

/// A chase from behind. Unseen until the hero is within `trigger` of where it is placed (0: the hero
/// reaches that spot); then a `warning` (the app shows it coming), and it appears `behind` the hero
/// on the ground, running `overtake` faster than the level, past the hero and away ahead.
public struct ChaseSpec: Sendable, Equatable {
    public var trigger: Double
    public var warning: Double
    public var behind: Double
    public var overtake: Double
}

/// A harmful zone `width` wide and `height` tall just in front of the body, on the side it walks
/// toward (a blade). It hurts like the body; yarn and stomps only see the body.
public struct ReachSpec: Sendable, Equatable {
    public var width: Double
    public var height: Double
}

/// Burns a fuse: once within `trigger` of the hero it flashes for `warning` seconds, keeping that
/// gap, then bursts into a `ring` hazard on the ground (`ringWidth` × `ringHeight`, `ringLife` s).
public struct FuseSpec: Sendable, Equatable {
    public var trigger: Double
    public var warning: Double
    public var ring = "fire_ring"
    public var ringWidth: Double
    public var ringHeight: Double
    public var ringLife: Double
}

/// Lies dormant (a statue, a perched gargoyle, an unseen shadow) until the hero comes within
/// `trigger`, warns for `warning` seconds, then wakes: walks at the item's `velocity`, after a leap
/// or a teleport if it has one. Dormant it is harmless and does not move; yarn bounces off its stone,
/// or passes straight through if it is unseen (a teleporter).
public struct WakeSpec: Sendable, Equatable {
    public var trigger: Double
    public var warning: Double
}

/// On waking, a jump in a parabola toward the hero, landing `distance` from where it stood, with its
/// feet `height` above the take-off at the top (under `Tuning.gravity`). It walks on from the landing.
public struct LeapSpec: Sendable, Equatable {
    public var distance: Double
    public var height: Double

    public func launchSpeed(gravity: Double) -> Double { (2 * gravity * height).squareRoot() }
    public func duration(gravity: Double) -> Double { 2 * launchSpeed(gravity: gravity) / gravity }
    public func forwardSpeed(gravity: Double) -> Double { distance / duration(gravity: gravity) }
}

/// Unseen while dormant; on waking it appears `ahead` of the hero and keeps that place while it
/// flashes its warning, then walks (dashes) in.
public struct TeleportSpec: Sendable, Equatable {
    public var ahead: Double
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
    /// Once curled it is a hard shell rather than spikes: landing on it is a safe bounce (no kill).
    public var shellBounce = false
    /// Once curled it rolls at this world velocity instead of walking at `velocity`.
    public var rollSpeed: Double?
    /// Walks back and forth no more than this far either side of where it was placed.
    public var patrol: Double?
    public var cycle: CycleSpec?
    public var cycleRole: CycleRole = .trap
    public var fall: FallSpec?
    public var flight: FlightSpec?
    public var wake: WakeSpec?
    public var leap: LeapSpec?
    public var teleport: TeleportSpec?
    public var keepAhead: KeepAheadSpec?
    public var chase: ChaseSpec?
    public var reach: ReachSpec?
    public var fuse: FuseSpec?
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
        // Props with a flat top: landing on it is a safe bounce; running into a side still hurts.
        case .stump: ItemSpec(width: 12, height: 24, stompable: true, solid: true)
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
        // Its flat top is a safe bounce (no kill); its sides and leaves hurt.
        case .stumpCat:
            ItemSpec(width: 20, height: 28, hp: 2, xp: 25, stompable: true, yarnable: true, solid: true,
                     throwing: ThrowSpec(projectile: "leaf", interval: 2.0, range: 300, speed: 80, y: 2,
                                         width: 8, height: 5))
        // Hides in its shell once close (the curler behaviour): yarn bounces off, and so does a kitten
        // landing on it, unhurt; jump or bounce over it.
        case .snailCat: ItemSpec(width: 24, height: 16, xp: 15, velocity: -8, stompable: true, stompKills: true,
                                 yarnable: true, curlsAt: 80, shellBounce: true)
        case .spiderCat:
            ItemSpec(width: 18, height: 16, baseY: 60, xp: 20, velocity: -20, stompable: true, stompKills: true,
                     yarnable: true,
                     fall: FallSpec(trigger: 130, warning: 0.4, shardWidth: 18, shardHeight: 16, walksOnLanding: true))
        // MARK: frost
        case .icicle: ItemSpec(width: 8, height: 18, baseY: 70, fall: FallSpec(trigger: 130, warning: 0.35))
        case .snowball: ItemSpec(width: 14, height: 14, hp: 2, xp: 20, velocity: -60, yarnable: true)
        case .penguin: ItemSpec(width: 18, height: 12, xp: 20, velocity: -90, stompable: true, yarnable: true)
        case .snowdrift: ItemSpec(width: 20, height: 8, stompable: true, solid: true)
        // Hops along (the hop is drawn only; the hitbox stays on the ground).
        case .iceSlime: ItemSpec(width: 20, height: 14, xp: 12, velocity: -22, stompable: true, stompKills: true,
                                 yarnable: true)
        // A fast runner whose paw slash is its body: touching it from the side hurts.
        case .snowCat: ItemSpec(width: 20, height: 20, hp: 2, xp: 25, velocity: -55, stompable: true,
                                stompKills: true, yarnable: true)
        // Like the forest bat: swoops to just over a standing kitten's head (24), never lower.
        case .iceBat:
            ItemSpec(width: 18, height: 14, baseY: 42, xp: 15, velocity: -45, yarnable: true,
                     flight: FlightSpec(high: 42, low: 28, diveStart: 150, diveEnd: 70))
        // Slow and tough; landing on it is a safe bounce that does not break it.
        case .iceGolem: ItemSpec(width: 26, height: 30, hp: 3, xp: 40, velocity: -8, stompable: true,
                                 yarnable: true, minHeroLevel: 3)
        // Marches back and forth around its post; close up it thrusts its spear (a short, fast, low throw).
        case .penguinSoldier:
            ItemSpec(width: 18, height: 24, hp: 2, xp: 25, velocity: -30, stompable: true, stompKills: true,
                     yarnable: true,
                     throwing: ThrowSpec(projectile: "spear", interval: 1.0, range: 70, speed: 140, y: 6,
                                         width: 14, height: 4, windup: 0.1, warning: 0.1),
                     patrol: 30)
        // Hovers high, drifting in; it blinks, then drops an icicle straight down ahead of the kitten,
        // where it lies as a spike to hop.
        case .snowyOwl:
            ItemSpec(width: 20, height: 16, baseY: 60, xp: 25, velocity: -10, yarnable: true,
                     throwing: ThrowSpec(projectile: "icicle_shot", interval: 3.0, range: 170, speed: 0, y: nil,
                                         width: 6, height: 10, arc: true, windup: 0.4, warning: 0.4))
        // Curls up close and then rolls in fast; curled, its spikes can't be stomped and yarn bounces off.
        case .iceHedgehog:
            ItemSpec(width: 20, height: 16, xp: 20, velocity: -20, stompable: true, stompKills: true,
                     yarnable: true, curlsAt: 100, rollSpeed: -110)
        // Lobs snowballs from its head that land ahead of the kitten and roll on; a stomp only bounces.
        case .snowman:
            ItemSpec(width: 20, height: 30, hp: 2, xp: 25, stompable: true, yarnable: true,
                     throwing: ThrowSpec(projectile: "snowball_shot", interval: 2.2, range: 300, speed: 60, y: 28,
                                         width: 8, height: 8, arc: true))
        // A trap like plant_cat (shut, opening, open); each time it opens it fires a bolt along the ground.
        case .iciclePlant:
            ItemSpec(width: 18, height: 24, hp: 2, xp: 25, yarnable: true,
                     throwing: ThrowSpec(projectile: "icicle_bolt", interval: 2.4, range: 300, speed: 100, y: 4,
                                         width: 10, height: 4, onCycleOpen: true),
                     cycle: CycleSpec(period: 2.4, activeFor: 0.6, warning: 0.5))
        // A slow bruiser with a wide swipe (its wide hitbox): no stomp, four yarn, or a Double Pounce over.
        case .miniYeti: ItemSpec(width: 30, height: 34, hp: 4, xp: 60, velocity: -6, yarnable: true,
                                 minHeroLevel: 3)
        // MARK: haunted
        // Drifts in overhead and down to the ground; it only exists while visible, and yarn passes through.
        // While visible it also throws a spirit ball at head height, just over a standing kitten.
        case .ghostCat:
            ItemSpec(width: 14, height: 14, baseY: 44, velocity: -20,
                     throwing: ThrowSpec(projectile: "spirit_ball", interval: 2.4, range: 300, speed: 100, y: 26,
                                         width: 8, height: 8),
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
        case .tombstone: ItemSpec(width: 14, height: 24, stompable: true, solid: true)
        // A flying frame: hovers over a standing kitten's head, drifting in, firing low magic shots.
        case .hauntedPortrait:
            ItemSpec(width: 18, height: 20, baseY: 32, hp: 2, xp: 25, velocity: -12, yarnable: true,
                     throwing: ThrowSpec(projectile: "magic_shot", interval: 2.2, range: 300, speed: 110, y: 4,
                                         width: 10, height: 6))
        // A knight statue: harmless stone until the kitten is close, then it wakes and walks in.
        case .cursedArmor:
            ItemSpec(width: 20, height: 28, hp: 3, xp: 45, velocity: -12, yarnable: true, minHeroLevel: 3,
                     wake: WakeSpec(trigger: 140, warning: 0.5))
        // The flame on its head burns a stomper; it sends fire orbs along the ground.
        case .candleCat:
            ItemSpec(width: 14, height: 16, xp: 15, velocity: -15, yarnable: true,
                     throwing: ThrowSpec(projectile: "fire_orb", interval: 2.5, range: 300, speed: 80, y: 2,
                                         width: 8, height: 8))
        // Floats high, lobbing magic bolts that land ahead of the kitten and fizzle out.
        case .poltergeistBook:
            ItemSpec(width: 16, height: 14, baseY: 48, xp: 20, velocity: -8, yarnable: true,
                     throwing: ThrowSpec(projectile: "magic_bolt", interval: 2.4, range: 220, speed: 70, y: nil,
                                         width: 8, height: 8, arc: true, fades: true))
        // Perched stone until the kitten nears, then it leaps down in front of it and walks in.
        // A landing on it is a safe bounce. The trigger is far enough out that, at world 3's speed,
        // the leap comes down ahead of the kitten rather than over its head.
        case .gargoyleCat:
            ItemSpec(width: 20, height: 24, hp: 2, xp: 35, velocity: -25, stompable: true, yarnable: true,
                     wake: WakeSpec(trigger: 240, warning: 0.5), leap: LeapSpec(distance: 70, height: 28))
        // Unseen until close, then it appears ahead of the kitten, flashes and dashes in.
        case .shadowCat:
            ItemSpec(width: 16, height: 20, xp: 30, velocity: -120, stompable: true, stompKills: true,
                     yarnable: true, wake: WakeSpec(trigger: 180, warning: 0.4), teleport: TeleportSpec(ahead: 80))
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
        // Molten: no stomp. Spits lava globs that land ahead and burn as a puddle for a second.
        case .lavaSlime:
            ItemSpec(width: 20, height: 14, xp: 15, velocity: -14, yarnable: true,
                     throwing: ThrowSpec(projectile: "lava_glob", interval: 2.4, range: 300, speed: 60, y: 12,
                                         width: 8, height: 8, arc: true,
                                         linger: LingerSpec(kind: "lava_puddle", seconds: 1.0, width: 18, height: 4)))
        // Hovers over a standing kitten, keeping 140 ahead for 3 s, then drifts in; low fireballs.
        case .fireImp:
            ItemSpec(width: 18, height: 18, baseY: 40, xp: 25, velocity: -20, yarnable: true,
                     throwing: ThrowSpec(projectile: "fireball_shot", interval: 2.2, range: 300, speed: 110, y: 4,
                                         width: 10, height: 6),
                     keepAhead: KeepAheadSpec(distance: 140, duration: 3.0))
        // Slow and armoured: a safe bounce on top; close up it punches out a short magma blast.
        case .stoneGuard:
            ItemSpec(width: 26, height: 32, hp: 4, xp: 50, velocity: -8, stompable: true, yarnable: true,
                     minHeroLevel: 3,
                     throwing: ThrowSpec(projectile: "magma_blast", interval: 1.0, range: 60, speed: 120, y: 8,
                                         width: 12, height: 8, windup: 0.1, warning: 0.1))
        // Comes from behind: a warning, then it runs in past the kitten (jump it). Burns on any touch.
        case .hellHound:
            ItemSpec(width: 26, height: 18, hp: 2, xp: 35, yarnable: true,
                     chase: ChaseSpec(trigger: 0, warning: 0.6, behind: 120, overtake: 130))
        // Like the ice bat: swoops to just over a standing kitten's head (24), never lower.
        case .emberBat:
            ItemSpec(width: 18, height: 14, baseY: 42, xp: 15, velocity: -50, yarnable: true,
                     flight: FlightSpec(high: 42, low: 28, diveStart: 150, diveEnd: 70))
        // Stands (on ledges) and shoots low flame arrows.
        case .flameArcher:
            ItemSpec(width: 16, height: 24, hp: 2, xp: 30, stompable: true, stompKills: true, yarnable: true,
                     throwing: ThrowSpec(projectile: "flame_arrow", interval: 2.0, range: 300, speed: 120, y: 6,
                                         width: 12, height: 4))
        // Slow elite with a chainsaw reaching 20 ahead of its body. No stomp; a Super Pounce cuts through.
        case .chainsawCat:
            ItemSpec(width: 26, height: 30, hp: 5, xp: 80, velocity: -10, yarnable: true, minHeroLevel: 5,
                     reach: ReachSpec(width: 20, height: 24))
        // Drifts in low; close up it flashes and bursts into a ring of fire on the ground.
        case .fireWisp:
            ItemSpec(width: 14, height: 14, baseY: 20, xp: 20, velocity: -40, yarnable: true,
                     fuse: FuseSpec(trigger: 50, warning: 0.5, ringWidth: 40, ringHeight: 10, ringLife: 0.4))
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
