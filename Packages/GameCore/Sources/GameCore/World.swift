import Foundation

public struct Tuning: Sendable, Equatable {
    public var gravity = 900.0
    /// Take-off speed of a jump. On its own (a tap) it peaks at `tapApex`; holding the button adds
    /// lift (see `holdBoost`).
    public var jumpVelocity = 216.0
    /// Variable jump: while the button stays held, for up to `holdBoost` seconds after take-off (and
    /// only while still rising), gravity is multiplied by `holdGravity`. Letting go ends the boost at
    /// once; there is no cut to the speed already gained. A full hold peaks at `jumpApex`.
    public var holdBoost = 0.28
    public var holdGravity = 0.25
    /// A Double Pounce takes off at this share of `jumpVelocity` and always gets its whole boost.
    public var doubleJumpScale = 0.68
    /// A jump pressed this long before landing still triggers.
    public var jumpBuffer = 0.1
    /// The same, for a press on the way down from a jump (a quick second tap).
    public var fallJumpBuffer = 0.3
    /// The kitten's hitbox: body and head of the 32×32 caped cat (ears and cape do not count).
    public var heroWidth = 16.0
    public var heroHeight = 24.0
    /// Yarn speed relative to the hero.
    public var yarnSpeed = 260.0
    public var yarnCooldown = 0.35
    /// Paw hold that turns a Ghost Dash into a Super Pounce on release.
    public var chargeTime = 0.45
    /// Seconds a Ghost Dash leaves the kitten intangible, and the wait from one dash to the next.
    public var dashDuration = 0.35
    public var dashCooldown = 1.5
    /// Super Pounce: a low, long leap with extra forward speed until it lands.
    public var pounceVelocity = 240.0
    public var pounceBoost = 170.0
    /// Run speed factor on slick ground.
    public var slickSpeed = 1.3
    /// Gravity on lobbed projectiles (acorns from a branch).
    public var lobGravity = 500.0
    public var invulnerability = 1.2
    public var stompBounce = 220.0
    public var spawnAhead = 420.0
    public var despawnBehind = 140.0
    public var projectileRange = 330.0
    /// Boss position ahead of the hero. The app uses `wideBossOffset` on a wide (landscape) screen
    /// and `narrowBossOffset` on a narrow (portrait) one, where less of the level fits on screen.
    public var bossOffset = Tuning.wideBossOffset
    public static let wideBossOffset = 210.0
    public static let narrowBossOffset = 140.0
    public var bossIntro = 1.5
    public var victoryDelay = 2.0
    /// A lip of ground up to this high is stepped onto without a jump.
    public var stepUp = 4.0
    /// Running into a step face too high to get onto knocks the hero back for this long, at this
    /// speed, with a small hop if it was on the ground; it then holds its place until it lands (or
    /// jumps) and runs on. The run-up it gets back (31 units) is what a held jump needs to climb a
    /// 44-high step at the fastest level speed (140), with the jump pressed on landing.
    public var bumpBack = 0.26
    public var bumpBackSpeed = 120.0
    public var bumpHop = 140.0

    public init() {}

    /// Height gained, and seconds taken, rising from take-off speed `speed` with the button held for
    /// the whole boost.
    public func heldRise(from speed: Double) -> (height: Double, time: Double) {
        let boosted = gravity * holdGravity
        let after = speed - boosted * holdBoost
        guard after > 0 else { return (speed * speed / (2 * boosted), speed / boosted) }
        return (speed * holdBoost - boosted * holdBoost * holdBoost / 2 + after * after / (2 * gravity),
                holdBoost + after / gravity)
    }

    /// Height of a tapped jump (no boost).
    public var tapApex: Double { jumpVelocity * jumpVelocity / (2 * gravity) }

    /// Height of a full (held) jump from the ground.
    public var jumpApex: Double { heldRise(from: jumpVelocity).height }

    /// Height of a full jump followed by a Double Pounce at its top.
    public var doubleJumpApex: Double { jumpApex + heldRise(from: jumpVelocity * doubleJumpScale).height }

    /// Horizontal reach of a full jump from the ground at `speed`.
    public func jumpReach(speed: Double) -> Double {
        (heldRise(from: jumpVelocity).time + (2 * jumpApex / gravity).squareRoot()) * speed
    }

    /// Horizontal reach of a full jump followed by a Double Pounce at its top.
    public func doubleJumpReach(speed: Double) -> Double {
        let rise = heldRise(from: jumpVelocity).time + heldRise(from: jumpVelocity * doubleJumpScale).time
        return (rise + (2 * doubleJumpApex / gravity).squareRoot()) * speed
    }
}

/// What a level thing is doing now. Most things stay `idle`; the rest use the cases that apply to them.
public enum EntityState: Sendable, Equatable {
    case idle
    /// About to act: a trap or a hanging icicle blinking, a ghost about to appear. Harmless.
    case warning
    /// A trap firing, a phasing ghost visible, a faller dropping.
    case active
    /// A hedgehog rolled into a ball.
    case curled
    /// A phasing ghost that is not there.
    case hidden
    /// A faller that hit the ground and lies there as shards.
    case landed
    /// In the air on a leap (see `LeapSpec`).
    case leaping
}

public struct Entity: Sendable, Equatable, Identifiable {
    public let id: Int
    public let kind: ItemKind
    public var x: Double
    public var y: Double
    public var hp: Int
    /// Walking away from the hero, after turning back at a ravine.
    public var reversed = false
    public internal(set) var state = EntityState.idle
    /// Seconds added to the world clock for this thing's cycle.
    public let cycleOffset: Double
    /// Where it was placed: a patrol turns back a set distance either side of it.
    public let home: Double
    var timer: Double
    var vy = 0.0
    /// Seconds it has kept its distance ahead (see `KeepAheadSpec`), and the gap a lit fuse holds.
    var heldFor = 0.0
    var holdGap = 0.0
    /// Throws made so far (an alternating thrower summons on the even ones), and teleports still to come.
    var throwCount = 0
    var teleportsLeft = 0

    init(id: Int, kind: ItemKind, x: Double, y: Double, hp: Int, cycleOffset: Double = 0) {
        self.id = id
        self.kind = kind
        self.x = x
        self.y = y
        self.hp = hp
        self.cycleOffset = cycleOffset
        home = x
        timer = kind.spec.throwing?.windup ?? 0.6
        // A teleporter is not there at all until it wakes.
        if kind.spec.teleport != nil || kind.spec.chase != nil { state = .hidden }
        teleportsLeft = kind.spec.teleport?.repeats ?? 0
    }

    public var box: AABB {
        let spec = kind.spec
        if state == .landed, let fall = spec.fall {
            return AABB(centerX: x, bottom: y, width: fall.shardWidth, height: fall.shardHeight)
        }
        return AABB(centerX: x, bottom: y, width: spec.width, height: spec.height)
    }

    /// Whether it can touch anything now: traps only while firing, phasing ghosts only while visible,
    /// a creature on a thread only once it lets go.
    public var isTangible: Bool {
        let spec = kind.spec
        if spec.fall?.walksOnLanding == true { return state == .active || state == .landed }
        if spec.wake != nil { return state == .active || state == .leaping }
        if spec.chase != nil { return state == .active }
        guard spec.cycle != nil else { return true }
        return state == .active
    }

    /// Whether yarn can strike it now. A trap's body is always there, firing or not; a phasing ghost
    /// or a creature out of reach on its thread is not.
    public var catchesYarn: Bool {
        // Dormant stone stops yarn (it bounces off, see `isDormant`); an unseen teleporter does not.
        if kind.spec.wake != nil { return kind.spec.teleport == nil || isTangible }
        if kind.spec.chase != nil { return isTangible }
        return isTangible || (kind.spec.cycle != nil && kind.spec.cycleRole == .trap)
    }

    /// The blade zone in front of the body, on the side it walks toward (see `ReachSpec`).
    public var reachBox: AABB? {
        guard let reach = kind.spec.reach else { return nil }
        let half = kind.spec.width / 2
        let center = reversed ? x + half + reach.width / 2 : x - half - reach.width / 2
        return AABB(centerX: center, bottom: y, width: reach.width, height: reach.height)
    }

    /// Not yet woken (still stone, perched or unseen), or blinking its warning before it wakes.
    public var isDormant: Bool {
        kind.spec.wake != nil && (state == .idle || state == .warning || state == .hidden)
    }

    /// What the hero touching it does (before a Ghost Dash or a Super Pounce is taken into account).
    public enum Touch: Sendable, Equatable {
        /// Nothing: it is not there, or it is harmless.
        case none
        /// A safe bounce off its top.
        case bounce
        /// A bounce that also defeats it.
        case stompKill
        case hurt
    }

    /// Landing on a stompable top is a bounce (a kill if it `stompKills`, except a hard shell); a
    /// dormant statue or perched gargoyle is a bounce on top and harmless at the side; anything else
    /// that is there hurts if it `hurtsOnTouch`. A curled-up spiky ball is never safe.
    public func touch(fromAbove: Bool) -> Touch {
        let spec = kind.spec
        if isDormant { return fromAbove && spec.teleport == nil ? .bounce : .none }
        guard isTangible else { return .none }
        let shell = state == .curled && spec.shellBounce
        if spec.stompable, state != .curled || shell, fromAbove {
            return spec.stompKills && !shell ? .stompKill : .bounce
        }
        return spec.hurtsOnTouch ? .hurt : .none
    }

    /// Moving along the ground now (turns at a rim, a Super Pounce defeats it). A creature that drops
    /// from a thread only walks once it has landed.
    public var walks: Bool {
        if kind.spec.fall?.walksOnLanding == true { return state == .landed && kind.spec.velocity != 0 }
        if kind.spec.wake != nil { return state == .active && kind.spec.velocity != 0 }
        return kind.walks
    }

    /// Still up on its thread or about to let go: it does not move along x yet.
    var isHanging: Bool {
        kind.spec.fall?.walksOnLanding == true && (state == .idle || state == .warning)
    }
}

/// A ball of yarn thrown by the hero.
public struct Projectile: Sendable, Equatable, Identifiable {
    public let id: Int
    public var x: Double
    public var y: Double
    public var vx: Double
    /// Already sent through a portal (it goes through only once).
    public var ported = false

    public var size: Double { 8 }
    public var damage: Int { 1 }
    public var box: AABB { AABB(centerX: x, bottom: y, width: size, height: size) }
}

public struct Hazard: Sendable, Equatable, Identifiable {
    public let id: Int
    public internal(set) var kind: String
    public var x: Double
    public var y: Double
    public internal(set) var width: Double
    public internal(set) var height: Double
    public var vx: Double
    /// Seconds left as a harmless warning.
    public var arm: Double
    public var vy = 0.0
    /// Pulls a lobbed hazard down; it is zero once it rolls along the ground.
    public var gravity = 0.0
    /// Landed and rolling along the ground: it drops again off a step down.
    public var rolling = false
    /// Fizzles out where it lands instead of rolling on.
    public var fades = false
    /// Seconds left before it burns out; nil lasts until it leaves the screen.
    public var life: Double?
    /// What it becomes where it lands, if it lingers (a lava glob's puddle).
    public var linger: LingerSpec?
    /// Homing: how fast it may change height toward the hero's middle (units per second).
    public var homing: Double?
    /// A falling star: gravity only takes it once it has armed.
    public var waitsToFall = false

    public var isArmed: Bool { arm <= 0 }
    public var box: AABB { AABB(centerX: x, bottom: y, width: width, height: height) }
}

/// One open (or just closed) portal pair from a boss attack; see `PortalSpec`. Placed relative to the
/// hero, so `x` and `exitX` follow `distance`.
public struct Portal: Sendable, Equatable, Identifiable {
    public let id: Int
    public let spec: PortalSpec
    public internal(set) var x: Double
    public internal(set) var exitX: Double
    /// Seconds it stays open; negative once closed (it lingers a moment before it goes).
    public internal(set) var openLeft: Double

    public var isOpen: Bool { openLeft > 0 }
    public var width: Double { spec.width ?? PortalSpec.defaultWidth }
    public var height: Double { spec.height ?? PortalSpec.defaultHeight }
    public var box: AABB { AABB(centerX: x, bottom: spec.y, width: width, height: height) }
    public var exitBox: AABB { AABB(centerX: exitX, bottom: spec.exitY, width: width, height: height) }
}

public struct Input: Sendable, Equatable {
    /// True only on the frame the jump touch began.
    public var jumpPressed = false
    public var jumpHeld = false
    public var fireHeld = false
    /// True only on the frame the paw touch began.
    public var pawPressed = false
    public var pawHeld = false

    public init(jumpPressed: Bool = false, jumpHeld: Bool = false, fireHeld: Bool = false,
                pawPressed: Bool = false, pawHeld: Bool = false) {
        self.jumpPressed = jumpPressed
        self.jumpHeld = jumpHeld
        self.fireHeld = fireHeld
        self.pawPressed = pawPressed
        self.pawHeld = pawHeld
    }
}

public enum Phase: Sendable, Equatable {
    case running, boss, victory, won, dead
}

/// How a platform looks to the player right now.
public enum PlatformState: Sendable, Equatable {
    case solid
    /// Landed on and about to give way, or a blinking platform about to vanish.
    case crumbling
    case gone
}

public enum GameEvent: Sendable, Equatable {
    case jumped(double: Bool)
    case landed
    case heroHit(heartsLeft: Int)
    case heroDied
    /// The hero dropped into a ravine; `heroDied` follows.
    case heroFell
    case stomped(id: Int)
    case enemyHit(id: Int)
    case enemyDefeated(id: Int, kind: ItemKind)
    case fish(id: Int)
    case yarnBasket
    case leveledUp(level: Int, ability: Ability?)
    case yarnThrown(id: Int)
    case yarnGone(id: Int, hit: Bool)
    /// Yarn struck something it cannot hurt (a curled hedgehog, a crate wall) and dropped.
    case yarnBounced(id: Int)
    case dashed
    case pounced
    /// A Super Pounce broke a crate wall.
    case wallBroken(id: Int)
    case curled(id: Int)
    /// An enemy threw or fired something (acorn, bone, cannonball).
    case threw(id: Int)
    case bellRang(id: Int)
    /// A vent or piston started firing.
    case trapFired(id: Int)
    /// An icicle or debris started blinking, about to drop.
    case fallWarning(id: Int)
    /// It hit the ground and broke into shards.
    case shattered(id: Int)
    /// A creature dropped from its thread, reached the ground and starts walking.
    case droppedDown(id: Int)
    /// Something dormant (a statue, a perched gargoyle) began its warning before it wakes.
    case waking(id: Int)
    /// An unseen creature appeared ahead of the hero; it flashes, then attacks.
    case teleported(id: Int)
    /// A creature took off on a leap, and came down from it.
    case leapt(id: Int)
    case leapLanded(id: Int)
    /// A chaser is about to come in from behind the hero (the app shows where from).
    case chaseWarning(id: Int)
    /// A fuse was lit (it flashes), and it burst into a ring of fire.
    case fuseLit(id: Int)
    case exploded(id: Int)
    /// A thrower summoned a creature instead of throwing (the void mage).
    case summoned(id: Int)
    /// A boss opened a portal pair; yarn went through one.
    case portalOpened(id: Int)
    case yarnPorted(id: Int)
    /// In a phase that needs abilities, the hero used one through an attack: the boss can be hit for
    /// a moment.
    case bossExposed
    /// The hero ran into the face of a step too high to walk onto and is knocked back; once per hit.
    case bumped
    /// A thrown thing ran into the face of a step and broke.
    case hazardBroke(id: Int)
    /// The hero landed on a crumbling platform; it gives way shortly.
    case platformCrumbling(index: Int)
    case bossAppeared(id: String)
    case bossTelegraph(attack: String)
    case bossAttack(attack: String)
    case bossHit(hp: Int)
    case bossBlocked
    case bossDefeated
    case levelComplete
}

/// The whole game simulation for one level. A value type with no randomness, so a copy can be
/// stepped forward to look into the future — the validator bot relies on that.
public struct RunnerWorld: Sendable {
    public let level: LevelDefinition
    public let boss: BossDefinition?
    /// The level's ravines, slick zones and platforms in order. Like items, any that reach the boss
    /// arena are left out.
    public let ravines: [Ravine]
    public let slick: [SlickZone]
    public let platforms: [Platform]
    /// Raised blocks and dips. Like ravines, none reach the boss arena.
    public let ground: GroundProfile
    public private(set) var tuning: Tuning

    public private(set) var time = 0.0
    /// Hero's world x; the level scrolls by increasing this.
    public private(set) var distance = 0.0
    /// How fast `distance` grew on the last step (slick ground and a pounce make it faster; it is
    /// negative while the hero is knocked back off a step, and 0 while it then waits to land).
    public private(set) var runSpeed: Double
    public private(set) var heroY = 0.0
    public private(set) var heroVY = 0.0
    public private(set) var onGround = true
    /// Index into `platforms` of the ledge the hero stands on; nil on the ground or in the air.
    public private(set) var standingOn: Int?
    public private(set) var stats: HeroStats
    public private(set) var phase = Phase.running
    public private(set) var entities: [Entity] = []
    public private(set) var projectiles: [Projectile] = []
    public private(set) var hazards: [Hazard] = []
    public private(set) var portals: [Portal] = []
    /// Seconds left of an opening in a boss phase that `requires` abilities.
    public private(set) var bossOpening = 0.0
    public private(set) var bossState: BossState?
    /// Seconds of hit immunity left.
    public private(set) var invulnerable = 0.0
    /// Seconds the paw button has been held (charging a Super Pounce).
    public private(set) var pawCharge = 0.0
    /// Seconds of Ghost Dash left, and until the next one is allowed.
    public private(set) var dashTime = 0.0
    public private(set) var dashCooldownLeft = 0.0
    /// In a Super Pounce, until it lands.
    public private(set) var pouncing = false
    public private(set) var fishCollected = 0
    public private(set) var score = 0
    /// True only on the step the hero runs into the face of a step too high to walk onto.
    public private(set) var isAgainstWall = false
    /// Seconds of knockback left after such a hit: the hero moves backwards and `distance` shrinks.
    public private(set) var bumpBackLeft = 0.0
    /// The x of the face last run into.
    public private(set) var lastBumpFace: Double?
    /// Knocked back and not yet landed or jumped again: no forward motion, so the run-up is kept.
    private var bumpHold = false

    private var nextItem = 0
    private var nextID = 1
    private var jumpsUsed = 0
    /// Seconds of reduced gravity left on this jump while the button stays held (see `Tuning.holdBoost`).
    private var holdBoostLeft = 0.0
    /// The boost runs whether or not the button is held (a Double Pounce, a jump from slick ground).
    private var boostForced = false
    /// In the air because the ground ran out (off a ledge, step or rim), not because of a jump.
    private var offEdge = false
    private var jumpBuffer = 0.0
    private var yarnCooldown = 0.0
    private var wasFireHeld = false
    private var wasPawHeld = false
    private var slickFactor = 1.0
    /// When the hero first landed on each crumbling platform.
    private var platformLanded: [Double?]
    private var phaseTimer = 0.0
    private let attacks: [String: BossAttack]

    public init(level: LevelDefinition, boss: BossDefinition?, stats: HeroStats = HeroStats(),
                tuning: Tuning = Tuning()) {
        var sorted = level
        sorted.items.sort { $0.at < $1.at }
        self.level = sorted
        ravines = (level.ravines ?? []).filter { $0.end < level.length }.sorted { $0.at < $1.at }
        slick = (level.slick ?? []).filter { $0.at < level.length }.sorted { $0.at < $1.at }
        platforms = (level.platforms ?? []).filter { $0.at < level.length }.sorted { $0.at < $1.at }
        platformLanded = Array(repeating: nil, count: platforms.count)
        ground = GroundProfile((level.terrain ?? []).filter { $0.at < level.length })
        self.boss = boss
        self.stats = stats
        self.tuning = tuning
        runSpeed = level.speed
        var table: [String: BossAttack] = [:]
        for var attack in boss?.attacks ?? [] {
            attack.hazards.sort { $0.delay < $1.delay }
            attack.summons?.sort { $0.delay < $1.delay }
            table[attack.name] = attack
        }
        attacks = table
    }

    public var heroBox: AABB {
        AABB(centerX: distance, bottom: heroY, width: tuning.heroWidth, height: tuning.heroHeight)
    }

    /// Moves the boss nearer or farther to suit the screen. Safe at any time: the boss is re-placed
    /// from this value on every step.
    public mutating func setBossOffset(_ offset: Double) {
        tuning.bossOffset = offset
    }

    public var isPounceReady: Bool { stats.has(.superPounce) && pawCharge >= tuning.chargeTime }
    public var isDashing: Bool { dashTime > 0 }
    public var canDash: Bool { stats.has(.ghostDash) && dashCooldownLeft <= 0 }
    /// Yarn Shot is won and its cooldown has run out (what the yarn button shows; a throw also needs
    /// a fresh press during a run or boss fight).
    public var canThrow: Bool { stats.has(.yarnShot) && yarnCooldown <= 0 }
    public var isOver: Bool { phase == .won || phase == .dead }
    /// In the air with a Double Pounce still to use (what the jump button shows).
    public var canDoubleJump: Bool { !onGround && stats.has(.doublePounce) && jumpsUsed < 2 }
    /// On the base ground (not a ledge or a step) over a slick zone.
    public var onSlick: Bool {
        onGround && standingOn == nil && heroY == 0 && slick.contains { $0.contains(distance) }
    }

    /// Height of the ground at `x`: 0 on the base ground, more on a raised block, less in a dip.
    /// Ravines are holes in the base ground and are not part of it.
    public func groundHeight(at x: Double) -> Double {
        ground.height(at: x)
    }

    public func platformState(_ index: Int) -> PlatformState {
        let platform = platforms[index]
        switch platform.mode {
        case .solid:
            return .solid
        case .crumbles:
            guard let landed = platformLanded[index] else { return .solid }
            return time - landed < (platform.crumbleAfter ?? Platform.defaultCrumbleAfter) ? .crumbling : .gone
        case .blinks:
            let cycle = platform.cycle
            let phase = (time + (platform.offset ?? 0)).truncatingRemainder(dividingBy: cycle.period)
            guard phase < cycle.activeFor else { return .gone }
            return phase >= cycle.activeFor - Platform.blinkWarning ? .crumbling : .solid
        }
    }

    // MARK: - Step

    public mutating func step(_ input: Input, dt: Double) -> [GameEvent] {
        var events: [GameEvent] = []
        guard !isOver else { return events }

        time += dt
        // Speed is kept through a jump: what counts is the ground the hero left from.
        if onGround { slickFactor = onSlick ? tuning.slickSpeed : 1 }
        runSpeed = level.speed * slickFactor + (pouncing ? tuning.pounceBoost : 0)
        invulnerable = max(0, invulnerable - dt)
        yarnCooldown = max(0, yarnCooldown - dt)
        dashTime = max(0, dashTime - dt)
        dashCooldownLeft = max(0, dashCooldownLeft - dt)
        bossOpening = max(0, bossOpening - dt)

        let previousBottom = heroY
        paw(input, dt: dt, events: &events)
        moveHero(input, dt: dt, events: &events)
        throwYarn(input, events: &events)
        spawnItems()
        moveEntities(dt: dt, events: &events)
        updateBoss(dt: dt, events: &events)
        movePortals(dt: dt)
        moveHazards(dt: dt, events: &events)
        moveProjectiles(dt: dt, events: &events)
        if phase == .running || phase == .boss {
            collideHero(previousBottom: previousBottom, events: &events)
        }
        cleanUp()

        if phase == .victory {
            phaseTimer -= dt
            if phaseTimer <= 0 {
                phase = .won
                events.append(.levelComplete)
            }
        }
        return events
    }

    // MARK: - Hero

    /// Whether ledge `index` holds the hero up now.
    private func platformHolds(_ index: Int) -> Bool {
        platformState(index) != .gone
    }

    private func groundIsOpen(at x: Double) -> Bool {
        ravines.contains { $0.isOpen(at: x) }
    }

    /// What the hero's feet rest on at the current position: the highest ground under its box, or
    /// nil over a ravine (decided by the middle of the box, as before terrain existed).
    private var floor: Double? {
        let half = tuning.heroWidth / 2
        let top = ground.highest(from: distance - half, to: distance + half)
        if top <= 0, groundIsOpen(at: distance) { return nil }
        return top
    }

    public var isBumpedBack: Bool { bumpBackLeft > 0 }

    /// Runs forward. Running into the face of a step higher than the feet (by more than `stepUp`)
    /// stops the hero at it and knocks it back for `bumpBack` seconds, with a small hop from the
    /// ground; no harm done. The knockback never carries the hero's middle over a ravine, nor its
    /// back into the face of a higher step behind.
    private mutating func advance(dt: Double, events: inout [GameEvent]) {
        let start = distance
        let half = tuning.heroWidth / 2
        isAgainstWall = false
        if bumpBackLeft > 0 {
            bumpBackLeft = max(0, bumpBackLeft - dt)
            var target = distance - tuning.bumpBackSpeed * dt
            for ravine in ravines where ravine.end <= distance + GroundProfile.epsilon {
                target = max(target, ravine.end)
            }
            if let face = ground.wall(behind: distance - half, to: target - half, feet: heroY, step: tuning.stepUp) {
                target = max(target, face + half)
            }
            distance = min(distance, target)
            runSpeed = (distance - start) / dt
        } else if bumpHold, !onGround {
            runSpeed = 0
        } else {
            let front = distance + half
            if let wall = ground.wall(from: front, to: front + runSpeed * dt, feet: heroY, step: tuning.stepUp) {
                distance = max(distance, wall - half)
                runSpeed = (distance - start) / dt
                isAgainstWall = true
                lastBumpFace = wall
                bumpBackLeft = tuning.bumpBack
                bumpHold = true
                events.append(.bumped)
                if onGround {
                    // A small hop back; a Double Pounce is still there, as off a ledge.
                    heroVY = tuning.bumpHop
                    onGround = false
                    standingOn = nil
                    jumpsUsed = 1
                    holdBoostLeft = 0
                }
            } else {
                distance += runSpeed * dt
            }
        }
        // A low lip is walked (or risen) onto.
        if standingOn == nil, let floor, heroY < floor { heroY = floor }
    }

    private mutating func moveHero(_ input: Input, dt: Double, events: inout [GameEvent]) {
        // A press on the way down from a jump is kept a little longer, so tapping twice in a row hops
        // again on landing. Dropping off a ledge keeps the usual buffer: a press there is meant for
        // what comes next, and firing it on touchdown would jump far too early.
        if heroVY > 0 { offEdge = false }
        let fallingFromJump = !onGround && heroVY <= 0 && !offEdge
        if input.jumpPressed {
            jumpBuffer = fallingFromJump ? tuning.fallJumpBuffer : tuning.jumpBuffer
        } else {
            jumpBuffer = max(0, jumpBuffer - dt)
        }
        advance(dt: dt, events: &events)

        if onGround {
            if let index = standingOn {
                if !platforms[index].spans(distance) || !platformHolds(index) {
                    // Off the end of the ledge, or it gave way: falling, with only a Double Pounce left.
                    onGround = false
                    offEdge = true
                    standingOn = nil
                    jumpsUsed = 1
                }
            } else if let floor {
                if floor < heroY - tuning.stepUp {
                    // Off the edge of a step: falling, with only a Double Pounce left, as off a ledge.
                    onGround = false
                    offEdge = true
                    jumpsUsed = 1
                } else {
                    heroY = floor
                }
            } else {
                // Ran off the rim: nothing to push off from, so no jump can save this.
                onGround = false
                offEdge = true
                jumpsUsed = 2
            }
        }

        if jumpBuffer > 0 {
            if onGround {
                // How high is up to the player: the boost lasts while the button is held. Slick
                // ground gives no grip for a short hop: every jump from it is a full one.
                holdBoostLeft = tuning.holdBoost
                boostForced = onSlick
                heroVY = tuning.jumpVelocity
                onGround = false
                standingOn = nil
                jumpsUsed = 1
                jumpBuffer = 0
                bumpHold = false
                events.append(.jumped(double: false))
            } else if input.jumpPressed, jumpsUsed < 2, stats.has(.doublePounce) {
                heroVY = tuning.jumpVelocity * tuning.doubleJumpScale
                jumpsUsed = 2
                // Always full height, as if held through its whole boost: players tap.
                holdBoostLeft = tuning.holdBoost
                boostForced = true
                jumpBuffer = 0
                bumpHold = false
                bumpBackLeft = 0
                events.append(.jumped(double: true))
            }
        }

        guard !onGround else { return }
        var gravity = tuning.gravity
        if holdBoostLeft > 0, heroVY > 0, input.jumpHeld || boostForced {
            gravity *= tuning.holdGravity
            holdBoostLeft = max(0, holdBoostLeft - dt)
        } else {
            // Let go (or past the top): the boost is over for this jump.
            holdBoostLeft = 0
        }
        let previous = heroY
        heroVY -= gravity * dt
        heroY += heroVY * dt
        guard heroVY <= 0 else { return }

        // One-way ledges catch the hero on the way down if they were above or at the feet before.
        var best: (index: Int?, top: Double)?
        for index in platforms.indices {
            let platform = platforms[index]
            guard platform.spans(distance), platform.y <= previous + 0.001, platform.y >= heroY,
                  platformHolds(index), platform.y > (best?.top ?? -.infinity) else { continue }
            best = (index, platform.y)
        }
        let groundFloor = self.floor
        if best == nil, let groundFloor, heroY <= groundFloor { best = (nil, groundFloor) }
        if let best {
            heroY = best.top
            heroVY = 0
            onGround = true
            standingOn = best.index
            jumpsUsed = 0
            pouncing = false
            bumpHold = false
            events.append(.landed)
            if let index = best.index, platforms[index].mode == .crumbles, platformLanded[index] == nil {
                platformLanded[index] = time
                events.append(.platformCrumbling(index: index))
            }
        } else if heroY < 0, groundFloor == nil, phase != .dead {
            // Below the rim there is no way back, whatever hearts are left.
            stats.hearts = 0
            phase = .dead
            pouncing = false
            events += [.heroFell, .heroDied]
        }
    }

    /// Paw button: a tap is a Ghost Dash. With Super Pounce, the dash waits for the release, and a
    /// release after holding `chargeTime` pounces instead.
    private mutating func paw(_ input: Input, dt: Double, events: inout [GameEvent]) {
        defer { wasPawHeld = input.pawHeld }
        guard stats.has(.ghostDash), phase == .running || phase == .boss else {
            pawCharge = 0
            return
        }
        let pressed = input.pawPressed || (input.pawHeld && !wasPawHeld)
        guard stats.has(.superPounce) else {
            if pressed { dash(events: &events) }
            pawCharge = input.pawHeld ? pawCharge + dt : 0
            return
        }
        if pressed { pawCharge = 0 }
        if input.pawHeld { pawCharge += dt }
        // A touch that began and ended within one frame is a tap.
        let released = (wasPawHeld && !input.pawHeld) || (input.pawPressed && !input.pawHeld)
        guard released else { return }
        if pawCharge >= tuning.chargeTime {
            pounce(events: &events)
        } else {
            dash(events: &events)
        }
        pawCharge = 0
    }

    private mutating func dash(events: inout [GameEvent]) {
        guard dashCooldownLeft <= 0 else { return }
        dashTime = tuning.dashDuration
        dashCooldownLeft = tuning.dashCooldown
        events.append(.dashed)
    }

    private mutating func pounce(events: inout [GameEvent]) {
        guard onGround else { return }
        heroVY = tuning.pounceVelocity
        onGround = false
        standingOn = nil
        jumpsUsed = 1
        holdBoostLeft = 0
        jumpBuffer = 0
        pouncing = true
        events.append(.pounced)
    }

    private mutating func throwYarn(_ input: Input, events: inout [GameEvent]) {
        defer { wasFireHeld = input.fireHeld }
        guard stats.has(.yarnShot), phase == .running || phase == .boss,
              input.fireHeld, !wasFireHeld, yarnCooldown <= 0 else { return }
        yarnCooldown = tuning.yarnCooldown
        let shot = Projectile(id: takeID(), x: distance + 12, y: heroY + 4, vx: runSpeed + tuning.yarnSpeed)
        projectiles.append(shot)
        events.append(.yarnThrown(id: shot.id))
    }

    // MARK: - World

    private mutating func takeID() -> Int {
        defer { nextID += 1 }
        return nextID
    }

    private mutating func spawnItems() {
        guard phase == .running else { return }
        while nextItem < level.items.count {
            let item = level.items[nextItem]
            guard item.at < level.length else {
                nextItem = level.items.count
                break
            }
            guard item.at <= distance + tuning.spawnAhead else { break }
            let spec = item.kind.spec
            // Everything stands (or hangs, or floats) above the ground where it is placed.
            entities.append(Entity(id: takeID(), kind: item.kind, x: item.at,
                                   y: groundHeight(at: item.at) + (item.y ?? spec.baseY), hp: spec.hp,
                                   cycleOffset: item.cycleOffset ?? 0))
            nextItem += 1
        }
    }

    private mutating func moveEntities(dt: Double, events: inout [GameEvent]) {
        for index in entities.indices {
            var entity = entities[index]
            let spec = entity.kind.spec
            // A curled roller rolls at its own speed; anything hanging on a thread stays put.
            let speed = entity.state == .curled ? (spec.rollSpeed ?? spec.velocity) : spec.velocity
            let pausing = spec.burst.map { !$0.isMoving(at: time + entity.cycleOffset) } ?? false
            let still = entity.isHanging || entity.isDormant || entity.state == .leaping || pausing
            let velocity = still ? 0 : (entity.reversed ? -speed : speed)
            entity.x += velocity * dt
            if entity.walks, velocity != 0 {
                // Stop at a rim or a step (up or down) and head back the other way.
                let half = spec.width / 2
                let front = entity.x + (velocity < 0 ? -half : half)
                if let ravine = ravines.first(where: { $0.isOpen(at: front) }) {
                    entity.x = velocity < 0 ? ravine.end + half : ravine.at - half
                    entity.reversed.toggle()
                } else if let edge = ground.step(from: entity.x, to: front, level: entity.y) {
                    entity.x = velocity < 0 ? edge + half : edge - half
                    entity.reversed.toggle()
                } else if let patrol = spec.patrol, abs(entity.x - entity.home) > patrol {
                    // End of its beat: turn back toward its post.
                    entity.x = velocity < 0 ? entity.home - patrol : entity.home + patrol
                    entity.reversed.toggle()
                }
            }
            let gap = entity.x - distance
            if let flight = spec.flight {
                entity.y = groundHeight(at: entity.x) + flight.height(gap: gap)
            } else if velocity != 0, !entity.walks, spec.fall == nil {
                // Flyers without a dive (skulls, bee cats) keep their height above the ground below.
                entity.y = groundHeight(at: entity.x) + spec.baseY
            }
            if let curlsAt = spec.curlsAt, entity.state != .curled, gap < curlsAt {
                entity.state = .curled
                events.append(.curled(id: entity.id))
            }
            if let cycle = spec.cycle {
                var state = cycle.state(at: time + entity.cycleOffset)
                if spec.cycleRole == .phase, state == .idle { state = .hidden }
                if spec.cycleRole == .trap, state == .active, entity.state != .active {
                    events.append(.trapFired(id: entity.id))
                    if let throwing = spec.throwing, throwing.onCycleOpen, gap > 30, gap < throwing.range {
                        launch(throwing, from: entity, events: &events)
                    }
                }
                entity.state = state
            }
            if let fall = spec.fall {
                updateFaller(&entity, fall: fall, gap: gap, dt: dt, events: &events)
            }
            if let wake = spec.wake {
                updateWaker(&entity, wake: wake, gap: gap, dt: dt, events: &events)
            }
            if let keep = spec.keepAhead, entity.heldFor < keep.duration, entity.x - distance <= keep.distance {
                // Keeping its distance, moving with the hero, until its time is up.
                entity.x = distance + keep.distance
                entity.y = groundHeight(at: entity.x) + spec.baseY
                entity.heldFor += dt
            }
            if let chase = spec.chase {
                updateChaser(&entity, chase: chase, gap: gap, dt: dt, events: &events)
            }
            if let fuse = spec.fuse {
                updateFuse(&entity, fuse: fuse, gap: gap, dt: dt, events: &events)
            }
            if let throwing = spec.throwing, !throwing.onCycleOpen {
                // A phasing ghost only throws while it is there.
                let present = spec.cycle == nil || spec.cycleRole != .phase || entity.state == .active
                let inRange = present && gap > 30 && gap < throwing.range
                if inRange {
                    entity.timer -= dt
                    if entity.timer <= 0 {
                        entity.timer = throwing.interval
                        if let summon = throwing.alternateSummon, entity.throwCount % 2 == 0 {
                            summonAhead(summon, ahead: throwing.summonAhead)
                            events.append(.summoned(id: entity.id))
                        } else {
                            launch(throwing, from: entity, events: &events)
                        }
                        entity.throwCount += 1
                    }
                }
                // Winding up for the next throw: a warning the player can read.
                if throwing.warning > 0 {
                    entity.state = inRange && entity.timer <= throwing.warning ? .warning : .idle
                }
            }
            entities[index] = entity
        }
    }

    private mutating func launch(_ throwing: ThrowSpec, from entity: Entity, events: inout [GameEvent]) {
        hazards.append(Hazard(id: takeID(), kind: throwing.projectile, x: entity.x - 10,
                              y: throwing.y.map { groundHeight(at: entity.x) + $0 } ?? entity.y,
                              width: throwing.width, height: throwing.height,
                              vx: -throwing.speed, arm: 0,
                              gravity: throwing.arc ? tuning.lobGravity : 0, fades: throwing.fades,
                              linger: throwing.linger, homing: throwing.homing))
        events.append(entity.kind == .bell ? .bellRang(id: entity.id) : .threw(id: entity.id))
    }

    /// A creature appears `ahead` of the hero, standing (or floating) on the ground there.
    private mutating func summonAhead(_ kind: ItemKind, ahead: Double) {
        let x = distance + ahead
        entities.append(Entity(id: takeID(), kind: kind, x: x, y: groundHeight(at: x) + kind.spec.baseY,
                               hp: kind.spec.hp))
    }

    /// Unseen → warning (the hero reached its spot) → running in from behind, past the hero.
    private func updateChaser(_ entity: inout Entity, chase: ChaseSpec, gap: Double, dt: Double,
                              events: inout [GameEvent]) {
        switch entity.state {
        case .hidden:
            guard gap <= chase.trigger else { break }
            entity.state = .warning
            entity.timer = chase.warning
            events.append(.chaseWarning(id: entity.id))
        case .warning:
            entity.timer -= dt
            guard entity.timer <= 0 else { break }
            entity.state = .active
            entity.x = distance - chase.behind
            entity.y = groundHeight(at: entity.x)
        case .active:
            // Runs along the ground (it bounds over ravines and up and down steps).
            entity.x += (level.speed + chase.overtake) * dt
            entity.y = groundHeight(at: entity.x)
        default:
            break
        }
    }

    /// Drifting → lit (flashing, holding its gap) → a ring of fire on the ground where it was.
    private mutating func updateFuse(_ entity: inout Entity, fuse: FuseSpec, gap: Double, dt: Double,
                                     events: inout [GameEvent]) {
        switch entity.state {
        case .idle:
            guard gap < fuse.trigger else { break }
            entity.state = .warning
            entity.timer = fuse.warning
            entity.holdGap = gap
            events.append(.fuseLit(id: entity.id))
        case .warning:
            entity.x = distance + entity.holdGap
            entity.y = groundHeight(at: entity.x) + entity.kind.spec.baseY
            entity.timer -= dt
            guard entity.timer <= 0 else { break }
            entity.hp = 0
            hazards.append(Hazard(id: takeID(), kind: fuse.ring, x: entity.x, y: groundHeight(at: entity.x),
                                  width: fuse.ringWidth, height: fuse.ringHeight, vx: 0, arm: 0,
                                  life: fuse.ringLife))
            events.append(.exploded(id: entity.id))
        default:
            break
        }
    }

    /// Dormant → warning → awake, by way of a leap or a teleport if it has one. Awake it walks.
    private func updateWaker(_ entity: inout Entity, wake: WakeSpec, gap: Double, dt: Double,
                             events: inout [GameEvent]) {
        let spec = entity.kind.spec
        switch entity.state {
        case .idle, .hidden:
            guard gap < wake.trigger else { break }
            entity.state = .warning
            entity.timer = wake.warning
            if let teleport = spec.teleport {
                entity.x = distance + teleport.ahead
                entity.y = groundHeight(at: entity.x)
                events.append(.teleported(id: entity.id))
            } else {
                events.append(.waking(id: entity.id))
            }
        case .warning:
            if let teleport = spec.teleport {
                // Keeps its place ahead of the runner while it flashes.
                entity.x = distance + teleport.ahead
                entity.y = groundHeight(at: entity.x)
            }
            entity.timer -= dt
            guard entity.timer <= 0 else { break }
            if let leap = spec.leap {
                entity.state = .leaping
                entity.vy = leap.launchSpeed(gravity: tuning.gravity)
                // Toward the hero, whichever side it is on.
                entity.reversed = entity.x < distance
                events.append(.leapt(id: entity.id))
            } else {
                entity.state = .active
            }
        case .leaping:
            guard let leap = spec.leap else { break }
            let forward = leap.forwardSpeed(gravity: tuning.gravity)
            entity.x += (entity.reversed ? forward : -forward) * dt
            entity.vy -= tuning.gravity * dt
            entity.y += entity.vy * dt
            let floor = groundHeight(at: entity.x)
            guard entity.vy < 0, entity.y <= floor else { break }
            if floor <= 0, groundIsOpen(at: entity.x) {
                // Came down over a ravine: it drops out of sight.
                if entity.y < -60 { entity.hp = 0 }
            } else {
                entity.y = floor
                entity.vy = 0
                entity.state = .active
                events.append(.leapLanded(id: entity.id))
            }
        case .active:
            // A teleporter whose dash has carried it past the hero appears ahead again, if it may.
            guard let teleport = spec.teleport, entity.teleportsLeft > 0,
                  entity.x < distance - tuning.heroWidth * 2 else { break }
            entity.teleportsLeft -= 1
            entity.state = .warning
            entity.timer = wake.warning
            entity.reversed = false
            entity.x = distance + teleport.ahead
            entity.y = groundHeight(at: entity.x)
            events.append(.teleported(id: entity.id))
        default:
            break
        }
    }

    /// Hanging → blinking → dropping → shards on the ground (or, for a creature, walking on).
    /// Over a ravine it drops out of sight.
    private func updateFaller(_ entity: inout Entity, fall: FallSpec, gap: Double, dt: Double,
                              events: inout [GameEvent]) {
        switch entity.state {
        case .idle:
            if gap < fall.trigger {
                entity.state = .warning
                entity.timer = fall.warning
                events.append(.fallWarning(id: entity.id))
            }
        case .warning:
            entity.timer -= dt
            if entity.timer <= 0 { entity.state = .active }
        case .active:
            entity.vy -= tuning.gravity * dt
            entity.y += entity.vy * dt
            let floor = groundHeight(at: entity.x)
            if entity.y <= floor {
                if floor <= 0, groundIsOpen(at: entity.x) {
                    if entity.y < -60 { entity.hp = 0 }
                } else {
                    entity.y = floor
                    entity.vy = 0
                    entity.state = .landed
                    events.append(fall.walksOnLanding ? .droppedDown(id: entity.id) : .shattered(id: entity.id))
                }
            }
        default:
            break
        }
    }

    private mutating func moveHazards(dt: Double, events: inout [GameEvent]) {
        var kept: [Hazard] = []
        for var hazard in hazards {
            if let life = hazard.life {
                // A puddle or a ring of fire burns out.
                hazard.life = life - dt
                if life - dt <= 0 { continue }
            }
            hazard.x += hazard.vx * dt
            hazard.arm = max(0, hazard.arm - dt)
            if let rate = hazard.homing, hazard.box.minX > heroBox.maxX {
                // Steers toward the hero's middle, no faster than its turn rate; past the hero it flies on.
                let target = heroY + tuning.heroHeight / 2 - hazard.height / 2
                hazard.y += min(max(target - hazard.y, -rate * dt), rate * dt)
            }
            // Anything low enough to run into the face of a step breaks on it.
            if !ground.isFlat, hazard.vx != 0 {
                let front = hazard.x + (hazard.vx < 0 ? -hazard.width : hazard.width) / 2
                let face = hazard.vx < 0 ? ground.height(leftOf: front) : ground.height(at: front)
                if face > hazard.y + 0.001, !groundIsOpen(at: front) {
                    events.append(.hazardBroke(id: hazard.id))
                    continue
                }
            }
            let floor = groundHeight(at: hazard.x)
            if hazard.rolling, hazard.y > floor + 0.001 {
                // Rolled off a step down: it drops and rolls on below.
                hazard.rolling = false
                hazard.gravity = tuning.lobGravity
            }
            if hazard.gravity > 0, !(hazard.waitsToFall && !hazard.isArmed) {
                hazard.vy -= hazard.gravity * dt
                hazard.y += hazard.vy * dt
                if hazard.y <= floor, !(floor <= 0 && groundIsOpen(at: hazard.x)) {
                    if hazard.fades {
                        // A magic bolt fizzles out where it lands.
                        events.append(.hazardBroke(id: hazard.id))
                        continue
                    }
                    if let linger = hazard.linger {
                        // A lava glob lands as a burning puddle that stays put for a while.
                        hazard.kind = linger.kind
                        hazard.width = linger.width
                        hazard.height = linger.height
                        hazard.y = floor
                        hazard.vx = 0
                        hazard.vy = 0
                        hazard.gravity = 0
                        hazard.life = linger.seconds
                        hazard.linger = nil
                        kept.append(hazard)
                        continue
                    }
                    // A lobbed acorn lands and rolls on.
                    hazard.y = floor
                    hazard.vy = 0
                    hazard.gravity = 0
                    hazard.rolling = true
                }
            }
            kept.append(hazard)
        }
        hazards = kept
    }

    private mutating func moveProjectiles(dt: Double, events: inout [GameEvent]) {
        var kept: [Projectile] = []
        for var shot in projectiles {
            shot.x += shot.vx * dt
            if !shot.ported, let portal = portals.first(where: { $0.isOpen && $0.box.intersects(shot.box) }) {
                // Through the portal and out of its pair, at the same height within it.
                let reverses = portal.spec.reverses == true
                shot.y = portal.spec.exitY + (shot.y - portal.spec.y)
                shot.x = portal.exitX + (reverses ? -1 : 1) * (portal.width + shot.size) / 2
                if reverses { shot.vx = runSpeed - tuning.yarnSpeed }
                shot.ported = true
                events.append(.yarnPorted(id: shot.id))
            }
            if hit(with: shot, events: &events) {
                events.append(.yarnGone(id: shot.id, hit: true))
            } else if ground.height(at: shot.x + shot.size / 2) > shot.y + 0.001 {
                // Yarn stops against the face of a step.
                events.append(.yarnGone(id: shot.id, hit: false))
            } else if shot.x > distance + tuning.projectileRange || shot.x < distance - tuning.despawnBehind {
                events.append(.yarnGone(id: shot.id, hit: false))
            } else {
                kept.append(shot)
            }
        }
        projectiles = kept
    }

    /// Returns true when the shot is used up.
    private mutating func hit(with shot: Projectile, events: inout [GameEvent]) -> Bool {
        let box = shot.box
        if let index = entities.firstIndex(where: { entity in
            let spec = entity.kind.spec
            return entity.hp > 0 && entity.catchesYarn && (spec.yarnable || spec.deflectsYarn)
                && entity.box.intersects(box)
        }) {
            let entity = entities[index]
            if entity.kind.spec.deflectsYarn || entity.state == .curled || entity.isDormant {
                events.append(.yarnBounced(id: entity.id))
            } else {
                damage(entityAt: index, by: shot.damage, events: &events)
            }
            return true
        }
        guard phase == .boss, var state = bossState, let boss, state.action != .intro, state.action != .dead,
              state.box.intersects(box) else { return false }
        if boss.isOpen(hpFraction: state.hpFraction, action: state.action), !needsOpening(state, boss) || bossOpening > 0 {
            state.hp = max(0, state.hp - shot.damage)
            bossState = state
            events.append(.bossHit(hp: state.hp))
            if state.hp == 0 { defeatBoss(events: &events) }
        } else {
            events.append(.bossBlocked)
        }
        return true
    }

    private mutating func damage(entityAt index: Int, by amount: Int, events: inout [GameEvent]) {
        entities[index].hp -= amount
        let entity = entities[index]
        if entity.hp > 0 {
            events.append(.enemyHit(id: entity.id))
        } else {
            events.append(.enemyDefeated(id: entity.id, kind: entity.kind))
            award(xp: entity.kind.spec.xp, events: &events)
        }
    }

    private mutating func award(xp: Int, events: inout [GameEvent]) {
        score += xp
        announce(stats.gain(xp: xp), events: &events)
    }

    private func announce(_ levels: [Int], events: inout [GameEvent]) {
        for level in levels {
            events.append(.leveledUp(level: level, ability: Progression.ability(unlockedAt: level)))
        }
    }

    private mutating func collideHero(previousBottom: Double, events: inout [GameEvent]) {
        let hero = heroBox
        let ghost = dashTime > 0
        for index in entities.indices where entities[index].hp > 0
            && (entities[index].box.intersects(hero) || entities[index].reachBox?.intersects(hero) == true) {
            let entity = entities[index]
            let spec = entity.kind.spec
            switch entity.kind {
            case .fish:
                entities[index].hp = 0
                fishCollected += 1
                events.append(.fish(id: entity.id))
                award(xp: spec.xp, events: &events)
            case .yarnBasket:
                entities[index].hp = 0
                events.append(.yarnBasket)
                if let target = level.shrineLevel { announce(stats.raise(toLevel: target), events: &events) }
            default:
                let fromAbove = heroVY < 0 && previousBottom >= entity.box.maxY - 4
                guard entity.isTangible else {
                    // A dormant statue or perched gargoyle: its top holds the hero up for a bounce.
                    if entity.touch(fromAbove: fromAbove) == .bounce { bounce(off: index, events: &events) }
                    continue
                }
                if pouncing, spec.breakable {
                    entities[index].hp = 0
                    events.append(.wallBroken(id: entity.id))
                    continue
                }
                if pouncing, entity.walks || spec.chase != nil {
                    damage(entityAt: index, by: entity.hp, events: &events)
                    continue
                }
                // A Ghost Dash slips through creatures and traps, not through terrain.
                if ghost, !spec.solid { continue }
                switch entity.touch(fromAbove: fromAbove) {
                case .bounce:
                    bounce(off: index, events: &events)
                case .stompKill:
                    // The ones a stomp kills pay out like yarn.
                    damage(entityAt: index, by: entity.hp, events: &events)
                    bounce(off: index, events: &events)
                case .hurt:
                    hurt(events: &events)
                case .none:
                    break
                }
            }
        }
        exposeBossIfAbilityUsedThroughAnAttack(events: &events)
        guard !ghost else { return }
        for hazard in hazards where hazard.isArmed && hazard.box.intersects(hero) {
            hurt(events: &events)
        }
    }

    // MARK: - Final phase

    /// The phase `state` is in requires abilities, so yarn needs an opening.
    private func needsOpening(_ state: BossState, _ boss: BossDefinition) -> Bool {
        guard boss.phases.indices.contains(state.phaseIndex) else { return false }
        return !(boss.phases[state.phaseIndex].requires ?? []).isEmpty
    }

    /// True in a boss phase that requires abilities while no opening is running.
    public var bossNeedsOpening: Bool {
        guard phase == .boss, let state = bossState, let boss, state.action != .intro, state.action != .dead else {
            return false
        }
        return needsOpening(state, boss) && bossOpening <= 0
    }

    /// A Ghost Dash or Super Pounce (whichever the phase requires) while an armed hazard is level with
    /// the hero opens the boss for `openingTime`.
    private mutating func exposeBossIfAbilityUsedThroughAnAttack(events: inout [GameEvent]) {
        guard phase == .boss, let state = bossState, let boss, needsOpening(state, boss) else { return }
        let requires = boss.phases[state.phaseIndex].requires ?? []
        let usingOne = (isDashing && requires.contains(.ghostDash)) || (pouncing && requires.contains(.superPounce))
        let hero = heroBox
        guard usingOne, hazards.contains(where: { $0.isArmed && $0.box.minX < hero.maxX && $0.box.maxX > hero.minX })
        else { return }
        if bossOpening <= 0 { events.append(.bossExposed) }
        bossOpening = boss.openingTime ?? BossDefinition.defaultOpeningTime
    }

    /// Portals keep their place ahead of the hero; closed ones go after a moment.
    private mutating func movePortals(dt: Double) {
        for index in portals.indices {
            portals[index].openLeft -= dt
            portals[index].x = distance + portals[index].spec.ahead
            portals[index].exitX = distance + portals[index].spec.exitAhead
        }
        portals.removeAll { $0.openLeft < -0.4 }
    }

    /// Bounces the hero up off the top of entity `index`.
    private mutating func bounce(off index: Int, events: inout [GameEvent]) {
        let entity = entities[index]
        events.append(.stomped(id: entity.id))
        // From its top, so a landing on a corner never leaves the hero inside it.
        heroY = max(heroY, entity.box.maxY)
        heroVY = tuning.stompBounce
        jumpsUsed = 1
        holdBoostLeft = 0
    }

    private mutating func hurt(events: inout [GameEvent]) {
        guard invulnerable <= 0, phase == .running || phase == .boss else { return }
        stats.hearts -= 1
        invulnerable = tuning.invulnerability
        if stats.hearts <= 0 {
            stats.hearts = 0
            phase = .dead
            events.append(.heroDied)
        } else {
            events.append(.heroHit(heartsLeft: stats.hearts))
        }
    }

    private mutating func cleanUp() {
        let left = distance - tuning.despawnBehind
        // A chaser that ran on ahead out of sight is gone for good.
        let farAhead = distance + tuning.spawnAhead
        entities.removeAll { $0.hp <= 0 || $0.x < left || ($0.kind.spec.chase != nil && $0.x > farAhead) }
        hazards.removeAll { $0.x < left || $0.y < -60 }
    }

    // MARK: - Boss

    private mutating func updateBoss(dt: Double, events: inout [GameEvent]) {
        if phase == .running, distance >= level.length {
            guard let boss else {
                win(events: &events)
                return
            }
            phase = .boss
            bossState = BossState(id: boss.id, hp: boss.hp, maxHP: boss.hp, x: distance + tuning.bossOffset,
                                  y: boss.baseY, width: boss.width, height: boss.height)
            events.append(.bossAppeared(id: boss.id))
        }
        guard var state = bossState, let boss else { return }
        state.x = distance + tuning.bossOffset
        defer { if bossState != nil, bossState?.action != .dead { bossState = state } }
        guard phase == .boss else {
            bossState = state
            return
        }
        state.actionTime += dt

        switch state.action {
        case .intro:
            if state.actionTime >= tuning.bossIntro { startAttack(&state, boss: boss, events: &events) }
        case .telegraph:
            if state.actionTime >= (attacks[state.attackName]?.telegraph ?? 0) {
                state.action = .attack
                state.actionTime = 0
                events.append(.bossAttack(attack: state.attackName))
            }
        case .attack:
            guard let attack = attacks[state.attackName] else {
                state.action = .recover
                state.actionTime = 0
                break
            }
            while state.spawnedHazards < attack.hazards.count,
                  attack.hazards[state.spawnedHazards].delay <= state.actionTime {
                let spec = attack.hazards[state.spawnedHazards]
                let x = spec.ahead.map { distance + $0 } ?? state.x - state.width / 2
                let falls = spec.falls == true
                hazards.append(Hazard(id: takeID(), kind: spec.kind, x: x, y: spec.y, width: spec.width,
                                      height: spec.height, vx: level.speed - spec.closingSpeed, arm: spec.arm ?? 0,
                                      gravity: falls ? tuning.gravity : 0, fades: falls, waitsToFall: falls))
                state.spawnedHazards += 1
            }
            let portalSpecs = attack.portals ?? []
            while state.spawnedPortals < portalSpecs.count, portalSpecs[state.spawnedPortals].delay <= state.actionTime {
                let spec = portalSpecs[state.spawnedPortals]
                let portal = Portal(id: takeID(), spec: spec, x: distance + spec.ahead, exitX: distance + spec.exitAhead,
                                    openLeft: spec.open)
                portals.append(portal)
                events.append(.portalOpened(id: portal.id))
                state.spawnedPortals += 1
            }
            let summons = attack.summons ?? []
            while state.spawnedSummons < summons.count, summons[state.spawnedSummons].delay <= state.actionTime {
                let kind = summons[state.spawnedSummons].kind
                entities.append(Entity(id: takeID(), kind: kind, x: state.x - state.width / 2 - 10,
                                       y: kind.spec.baseY, hp: kind.spec.hp))
                state.spawnedSummons += 1
            }
            if state.actionTime >= attack.duration {
                state.action = .recover
                state.actionTime = 0
            }
        case .recover:
            if state.actionTime >= (attacks[state.attackName]?.recover ?? 0.5) {
                startAttack(&state, boss: boss, events: &events)
            }
        case .dead:
            break
        }
    }

    private func startAttack(_ state: inout BossState, boss: BossDefinition, events: inout [GameEvent]) {
        let fraction = state.hpFraction
        let phaseIndex = boss.phases.lastIndex { fraction <= $0.startsBelow } ?? 0
        if phaseIndex != state.phaseIndex {
            state.phaseIndex = phaseIndex
            state.attackCursor = 0
        }
        let phase = boss.phases.indices.contains(phaseIndex) ? boss.phases[phaseIndex] : nil
        let names = phase?.attacks ?? []
        state.attackName = names.isEmpty ? "" : names[state.attackCursor % names.count]
        // The real copy moves with every attack, in a fixed order the player can learn.
        state.copies = 1 + max(0, phase?.decoys ?? 0)
        state.trueCopy = (state.attackCursor * 2 + 1) % state.copies
        state.attackCursor += 1
        state.action = .telegraph
        state.actionTime = 0
        state.spawnedHazards = 0
        state.spawnedSummons = 0
        state.spawnedPortals = 0
        events.append(.bossTelegraph(attack: state.attackName))
    }

    private mutating func defeatBoss(events: inout [GameEvent]) {
        bossState?.action = .dead
        bossState?.actionTime = 0
        hazards.removeAll()
        portals.removeAll()
        events.append(.bossDefeated)
        win(events: &events)
    }

    private mutating func win(events: inout [GameEvent]) {
        phase = .victory
        phaseTimer = tuning.victoryDelay
        score += stats.hearts * 50
        announce(stats.raise(toLevel: level.bossRewardLevel), events: &events)
    }
}
