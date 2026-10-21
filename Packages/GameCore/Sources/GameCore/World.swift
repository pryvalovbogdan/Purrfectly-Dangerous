import Foundation

public struct Tuning: Sendable, Equatable {
    public var gravity = 900.0
    public var jumpVelocity = 300.0
    /// Upward speed is multiplied by this when the jump button is released early.
    public var jumpCut = 0.45
    /// A release only cuts a jump after it has risen this long, so a quick tap (or a jump buffered
    /// before landing, by when the thumb is usually up) still hops over a low step.
    public var minJumpHold = 0.12
    public var doubleJumpScale = 0.9
    /// A jump pressed this long before landing still triggers.
    public var jumpBuffer = 0.1
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
    public var pounceBoost = 140.0
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

    public init() {}

    /// Height of a full jump from the ground.
    public var jumpApex: Double { jumpVelocity * jumpVelocity / (2 * gravity) }

    /// Height of a full jump followed by a full Double Pounce at its top.
    public var doubleJumpApex: Double {
        let second = jumpVelocity * doubleJumpScale
        return jumpApex + second * second / (2 * gravity)
    }

    /// Horizontal reach of a full jump from the ground at `speed`.
    public func jumpReach(speed: Double) -> Double {
        2 * jumpVelocity / gravity * speed
    }

    /// Horizontal reach of a full jump followed by a full Double Pounce at its top.
    public func doubleJumpReach(speed: Double) -> Double {
        let first = jumpVelocity, second = jumpVelocity * doubleJumpScale
        let top = (first * first + second * second) / (2 * gravity)
        return (first / gravity + second / gravity + (2 * top / gravity).squareRoot()) * speed
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
    var timer = 0.6
    var vy = 0.0

    init(id: Int, kind: ItemKind, x: Double, y: Double, hp: Int, cycleOffset: Double = 0) {
        self.id = id
        self.kind = kind
        self.x = x
        self.y = y
        self.hp = hp
        self.cycleOffset = cycleOffset
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
        guard spec.cycle != nil else { return true }
        return state == .active
    }

    /// Whether yarn can strike it now. A trap's body is always there, firing or not; a phasing ghost
    /// or a creature out of reach on its thread is not.
    public var catchesYarn: Bool {
        isTangible || (kind.spec.cycle != nil && kind.spec.cycleRole == .trap)
    }

    /// Moving along the ground now (turns at a rim, a Super Pounce defeats it). A creature that drops
    /// from a thread only walks once it has landed.
    public var walks: Bool {
        if kind.spec.fall?.walksOnLanding == true { return state == .landed && kind.spec.velocity != 0 }
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

    public var size: Double { 8 }
    public var damage: Int { 1 }
    public var box: AABB { AABB(centerX: x, bottom: y, width: size, height: size) }
}

public struct Hazard: Sendable, Equatable, Identifiable {
    public let id: Int
    public let kind: String
    public var x: Double
    public var y: Double
    public let width: Double
    public let height: Double
    public var vx: Double
    /// Seconds left as a harmless warning.
    public var arm: Double
    public var vy = 0.0
    /// Pulls a lobbed hazard down; it is zero once it rolls along the ground.
    public var gravity = 0.0
    /// Landed and rolling along the ground: it drops again off a step down.
    public var rolling = false

    public var isArmed: Bool { arm <= 0 }
    public var box: AABB { AABB(centerX: x, bottom: y, width: width, height: height) }
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
    /// The hero ran into the face of a step too high to walk onto and stopped; sent once per contact.
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
    /// How fast `distance` grew on the last step (slick ground and a pounce make it faster; it is 0
    /// while the hero is stopped against a wall).
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
    /// Pressed against the face of a step too high to walk onto: `distance` does not grow, so the
    /// level waits, while the clock, enemies and thrown things carry on.
    public private(set) var isAgainstWall = false

    private var nextItem = 0
    private var nextID = 1
    private var jumpsUsed = 0
    private var jumpCutDone = false
    /// Seconds since the last jump left the ground.
    private var jumpRise = 0.0
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
    public var isOver: Bool { phase == .won || phase == .dead }
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

        let previousBottom = heroY
        paw(input, dt: dt, events: &events)
        moveHero(input, dt: dt, events: &events)
        throwYarn(input, events: &events)
        spawnItems()
        moveEntities(dt: dt, events: &events)
        updateBoss(dt: dt, events: &events)
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

    /// Pressed against a step's face, or with one in reach of the rising half of a jump that rises
    /// higher than a short hop clears.
    private var facesTallStep: Bool {
        if isAgainstWall { return true }
        let front = distance + tuning.heroWidth / 2
        let reach = tuning.jumpReach(speed: level.speed) / 2
        return ground.wall(from: front, to: front + reach, feet: heroY, step: tuning.stepUp) != nil
    }

    /// Runs forward, unless the face of a step higher than the feet is in the way: then the hero
    /// stops against it and `distance` stays put until a jump lifts the feet above its top.
    private mutating func advance(dt: Double, events: inout [GameEvent]) {
        let start = distance
        let half = tuning.heroWidth / 2
        let front = distance + half
        if let wall = ground.wall(from: front, to: front + runSpeed * dt, feet: heroY, step: tuning.stepUp) {
            distance = max(distance, wall - half)
            runSpeed = (distance - start) / dt
            if !isAgainstWall { events.append(.bumped) }
            isAgainstWall = true
        } else {
            distance += runSpeed * dt
            isAgainstWall = false
        }
        // A low lip is walked (or risen) onto.
        if standingOn == nil, let floor, heroY < floor { heroY = floor }
    }

    private mutating func moveHero(_ input: Input, dt: Double, events: inout [GameEvent]) {
        // A press on the way down is kept until the feet touch down, so a quick second tap is never
        // dropped; one on the way up only lasts the usual buffer.
        let falling = !onGround && heroVY <= 0
        jumpBuffer = input.jumpPressed ? tuning.jumpBuffer : falling ? jumpBuffer : max(0, jumpBuffer - dt)
        advance(dt: dt, events: &events)

        if onGround {
            if let index = standingOn {
                if !platforms[index].spans(distance) || !platformHolds(index) {
                    // Off the end of the ledge, or it gave way: falling, with only a Double Pounce left.
                    onGround = false
                    standingOn = nil
                    jumpsUsed = 1
                }
            } else if let floor {
                if floor < heroY - tuning.stepUp {
                    // Off the edge of a step: falling, with only a Double Pounce left, as off a ledge.
                    onGround = false
                    jumpsUsed = 1
                } else {
                    heroY = floor
                }
            } else {
                // Ran off the rim: nothing to push off from, so no jump can save this.
                onGround = false
                jumpsUsed = 2
            }
        }

        if jumpBuffer > 0 {
            if onGround {
                // Slick ground gives no grip for a short hop, and a step a hop can't clear is never
                // met with one: every jump from either is a full one.
                jumpCutDone = onSlick || facesTallStep
                jumpRise = 0
                heroVY = tuning.jumpVelocity
                onGround = false
                standingOn = nil
                jumpsUsed = 1
                jumpBuffer = 0
                events.append(.jumped(double: false))
            } else if input.jumpPressed, jumpsUsed < 2, stats.has(.doublePounce) {
                heroVY = tuning.jumpVelocity * tuning.doubleJumpScale
                jumpsUsed = 2
                // Always full height: players tap, and a cut second jump clears too little.
                jumpCutDone = true
                jumpBuffer = 0
                events.append(.jumped(double: true))
            }
        }

        guard !onGround else { return }
        jumpRise += dt
        if !input.jumpHeld, heroVY > 0, !jumpCutDone, jumpRise >= tuning.minJumpHold {
            heroVY *= tuning.jumpCut
            jumpCutDone = true
        }
        let previous = heroY
        heroVY -= tuning.gravity * dt
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
        jumpCutDone = true
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
            let velocity = entity.isHanging ? 0 : (entity.reversed ? -spec.velocity : spec.velocity)
            entity.x += velocity * dt
            if entity.walks {
                // Stop at a rim or a step (up or down) and head back the other way.
                let half = spec.width / 2
                let front = entity.x + (velocity < 0 ? -half : half)
                if let ravine = ravines.first(where: { $0.isOpen(at: front) }) {
                    entity.x = velocity < 0 ? ravine.end + half : ravine.at - half
                    entity.reversed.toggle()
                } else if let edge = ground.step(from: entity.x, to: front, level: entity.y) {
                    entity.x = velocity < 0 ? edge + half : edge - half
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
                }
                entity.state = state
            }
            if let fall = spec.fall {
                updateFaller(&entity, fall: fall, gap: gap, dt: dt, events: &events)
            }
            if let throwing = spec.throwing, gap > 30, gap < throwing.range {
                entity.timer -= dt
                if entity.timer <= 0 {
                    entity.timer = throwing.interval
                    hazards.append(Hazard(id: takeID(), kind: throwing.projectile, x: entity.x - 10,
                                          y: throwing.y.map { groundHeight(at: entity.x) + $0 } ?? entity.y,
                                          width: throwing.width, height: throwing.height,
                                          vx: -throwing.speed, arm: 0,
                                          gravity: throwing.arc ? tuning.lobGravity : 0))
                    events.append(entity.kind == .bell ? .bellRang(id: entity.id) : .threw(id: entity.id))
                }
            }
            entities[index] = entity
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
            hazard.x += hazard.vx * dt
            hazard.arm = max(0, hazard.arm - dt)
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
            if hazard.gravity > 0 {
                hazard.vy -= hazard.gravity * dt
                hazard.y += hazard.vy * dt
                if hazard.y <= floor, !(floor <= 0 && groundIsOpen(at: hazard.x)) {
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
            if hit(with: shot, events: &events) {
                events.append(.yarnGone(id: shot.id, hit: true))
            } else if ground.height(at: shot.x + shot.size / 2) > shot.y + 0.001 {
                // Yarn stops against the face of a step.
                events.append(.yarnGone(id: shot.id, hit: false))
            } else if shot.x > distance + tuning.projectileRange {
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
            if entity.kind.spec.deflectsYarn || entity.state == .curled {
                events.append(.yarnBounced(id: entity.id))
            } else {
                damage(entityAt: index, by: shot.damage, events: &events)
            }
            return true
        }
        guard phase == .boss, var state = bossState, let boss, state.action != .intro, state.action != .dead,
              state.box.intersects(box) else { return false }
        if boss.isOpen(hpFraction: state.hpFraction, action: state.action) {
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
        for index in entities.indices where entities[index].hp > 0 && entities[index].box.intersects(hero) {
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
                guard entity.isTangible else { continue }
                if pouncing, spec.breakable {
                    entities[index].hp = 0
                    events.append(.wallBroken(id: entity.id))
                    continue
                }
                if pouncing, entity.walks {
                    damage(entityAt: index, by: entity.hp, events: &events)
                    continue
                }
                // A Ghost Dash slips through creatures and traps, not through terrain.
                if ghost, !spec.solid { continue }
                let fromAbove = heroVY < 0 && previousBottom >= entity.box.maxY - 4
                if spec.stompable, entity.state != .curled, fromAbove {
                    events.append(.stomped(id: entity.id))
                    // For most it is only a bounce; the ones it kills pay out like yarn.
                    if spec.stompKills { damage(entityAt: index, by: entity.hp, events: &events) }
                    heroVY = tuning.stompBounce
                    jumpsUsed = 1
                    jumpCutDone = true
                } else if spec.hurtsOnTouch {
                    hurt(events: &events)
                }
            }
        }
        guard !ghost else { return }
        for hazard in hazards where hazard.isArmed && hazard.box.intersects(hero) {
            hurt(events: &events)
        }
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
        entities.removeAll { $0.hp <= 0 || $0.x < left }
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
                hazards.append(Hazard(id: takeID(), kind: spec.kind, x: x, y: spec.y, width: spec.width,
                                      height: spec.height, vx: level.speed - spec.closingSpeed, arm: spec.arm ?? 0))
                state.spawnedHazards += 1
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
        events.append(.bossTelegraph(attack: state.attackName))
    }

    private mutating func defeatBoss(events: inout [GameEvent]) {
        bossState?.action = .dead
        bossState?.actionTime = 0
        hazards.removeAll()
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
