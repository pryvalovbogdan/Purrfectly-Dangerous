import Foundation
import Testing
@testable import GameCore

/// The Sakura route's third level (theme `sakura_night`, Sakura World level 3 sheet): its five creatures.
extension MechanicsTests {
    static let nightCreatures: [ItemKind] = [.shadowSlime, .samuraiRonin, .oniCat, .tenguCrow, .spiritWisp]

    /// A flat test level at world 3's speed, with Ghost Dash (Sakura arrives from Petal Bridges with it).
    func nightLevel(_ items: [PlacedItem], length: Double = 2000, entry: Int = 4) -> LevelDefinition {
        var level = flatLevel(items: items, length: length, entry: entry, reward: max(entry, 2))
        level.background = "sakura_night"
        level.speed = 130
        return level
    }

    @Test func sakuraNightCreaturesHaveTheirIdsAndHitboxes() {
        let expected: [(ItemKind, String, Double, Double, Int, Int)] = [
            (.shadowSlime, "shadow_slime", 20, 16, 1, 15), (.samuraiRonin, "samurai_ronin", 18, 22, 2, 30),
            (.oniCat, "oni_cat", 24, 28, 4, 60), (.tenguCrow, "tengu_crow", 18, 14, 1, 20),
            (.spiritWisp, "spirit_wisp", 16, 20, 2, 30),
        ]
        for (kind, id, width, height, hp, xp) in expected {
            #expect(kind.rawValue == id)
            #expect(ItemKind(rawValue: id) == kind)
            #expect(kind.spec.width == width && kind.spec.height == height, "\(id) hitbox")
            #expect(kind.spec.hp == hp, "\(id) hp")
            #expect(kind.spec.xp == xp, "\(id) xp")
            #expect(kind.spec.yarnable, "\(id) is yarnable")
        }
        // The oni is the toughest of them, like the frost world's mini yeti.
        #expect(Self.nightCreatures.allSatisfy { $0 == .oniCat || $0.spec.hp < ItemKind.oniCat.spec.hp })
        #expect(ItemKind.oniCat.spec.hp == ItemKind.miniYeti.spec.hp)
        #expect(ItemKind.oniCat.spec.minHeroLevel == 3)
    }

    @Test func shadowSlimeLurchesInBurstsAndAStompKillsIt() throws {
        let burst = try #require(ItemKind.shadowSlime.spec.burst)
        var world = RunnerWorld(level: nightLevel([.init(at: 700, kind: .shadowSlime)]), boss: nil)
        advance(&world) { !$0.entities.isEmpty }
        var moved = false, stood = false
        for _ in 0..<120 {
            let before = world.entities.first?.x ?? 0
            _ = world.step(Input(), dt: dt)
            let step = before - (world.entities.first?.x ?? before)
            if burst.isMoving(at: world.time) { moved = moved || step > 0 } else { stood = stood || step == 0 }
        }
        #expect(moved && stood)
        // Its leap is drawn only: the hitbox stays on the ground.
        #expect(world.entities.first?.y == 0)
        #expect(stompAttempts(.shadowSlime).contains { defeated($0, .shadowSlime) && !hit($0) })
    }

    @Test func samuraiRoninTakesItsStanceThenLungesWithACrescentSlash() throws {
        let feint = try #require(ItemKind.samuraiRonin.spec.feint)
        #expect(!feint.backsOff)
        var world = RunnerWorld(level: nightLevel([.init(at: 800, kind: .samuraiRonin)]), boss: nil)
        advance(&world) { !$0.entities.isEmpty }
        // Walking in, the blade is sheathed.
        #expect(world.entities.first?.reachBox == nil)
        advance(&world) { $0.entities.first?.state == .warning }
        #expect(gap(world, .samuraiRonin) <= feint.trigger && gap(world, .samuraiRonin) > feint.trigger - 10)
        // The stance: it stands still.
        let stance = try #require(world.entities.first?.x)
        world.run(0.05)
        #expect(world.entities.first?.x == stance)
        #expect(world.entities.first?.reachBox == nil)
        let events = advance(&world, limit: 1) { $0.entities.first?.state == .active }
        #expect(events.contains { if case .lunged = $0 { true } else { false } })
        let slashing = try #require(world.entities.first)
        let slash = try #require(slashing.reachBox)
        #expect(slash.maxX <= slashing.box.minX)
        world.run(0.1)
        #expect(slashing.x - (world.entities.first?.x ?? slashing.x) > 0.1 * abs(feint.lungeSpeed) - 1)
        #expect(stompAttempts(.samuraiRonin).contains { defeated($0, .samuraiRonin) })
        #expect(takesYarn(.samuraiRonin, 2))
    }

    @Test func oniCatSwingsItsClubAheadLobsRocksAndTakesFourYarn() throws {
        let club = try #require(ItemKind.oniCat.spec.reach)
        #expect(!club.whileLunging)
        // The club faces the way it walks.
        var entity = Entity(id: 1, kind: .oniCat, x: 100, y: 0, hp: 4)
        #expect((entity.reachBox?.maxX ?? .infinity) <= entity.box.minX)
        entity.reversed = true
        #expect((entity.reachBox?.minX ?? -.infinity) >= entity.box.maxX)

        // It lobs rocks that land ahead of the kitten and roll on.
        var world = RunnerWorld(level: nightLevel([.init(at: 700, kind: .oniCat)]), boss: nil)
        advance(&world) { $0.hazards.contains { $0.kind == "oni_rock" } }
        let rock = try #require(world.hazards.first { $0.kind == "oni_rock" })
        #expect(rock.y > 20 && rock.gravity > 0)
        advance(&world, limit: 2) { world in world.hazards.first { $0.id == rock.id }?.y == 0 }
        let landed = try #require(world.hazards.first { $0.id == rock.id })
        #expect(landed.x - world.distance > 40)
        #expect(landed.vx < 0)

        // No stomp: landing on it is never a stomp.
        #expect(!ItemKind.oniCat.spec.stompable)
        #expect(stompAttempts(.oniCat).isEmpty)
        #expect(takesYarn(.oniCat, 4))
    }

    @Test func tenguCrowDivesAllTheWayToTheGround() {
        var world = RunnerWorld(level: nightLevel([.init(at: 700, kind: .tenguCrow)]), boss: nil)
        var lowest = Double.infinity, highest = 0.0
        var events: [GameEvent] = []
        while world.time < 7, !world.isOver {
            events += world.step(Input(), dt: dt)
            if let crow = world.entities.first(where: { $0.kind == .tenguCrow }) {
                lowest = min(lowest, crow.y)
                highest = max(highest, crow.y)
            }
        }
        #expect(lowest == 0)
        #expect(highest > 40)
        // It ends low: a kitten that never jumps is hit.
        #expect(hit(events))
    }

    @Test func spiritWispFloatsAndShootsHomingWispFireballs() throws {
        var world = RunnerWorld(level: nightLevel([.init(at: 700, kind: .spiritWisp)]), boss: nil)
        advance(&world) { !$0.entities.isEmpty }
        #expect(world.entities.first?.y == 36)
        let start = try #require(world.entities.first?.x)
        advance(&world) { $0.hazards.contains { $0.kind == "wisp_shot" } }
        #expect((world.entities.first?.x ?? start) < start)
        let shot = try #require(world.hazards.first { $0.kind == "wisp_shot" })
        #expect(shot.homing != nil && shot.homing == ItemKind.shadowSpirit.spec.throwing?.homing)
        #expect(shot.gravity == 0 && shot.vx < 0)
        // Up at 36 it takes yarn from a hop: two balls.
        #expect(!defeated(jumpVolley(at: .spiritWisp, count: 1), .spiritWisp))
        #expect(defeated(jumpVolley(at: .spiritWisp, count: 2), .spiritWisp))
    }

    @Test func aNightWorldIsDeterministicWhenCopied() {
        let items = Self.nightCreatures.enumerated().map { PlacedItem(at: 400 + Double($0.offset) * 160, kind: $0.element) }
        var world = RunnerWorld(level: nightLevel(items, length: 1600), boss: nil)
        world.run(1.5)
        var a = world, b = world
        let ea = a.run(4), eb = b.run(4)
        #expect(ea == eb)
        #expect(a.entities == b.entities && a.hazards == b.hazards && a.stats == b.stats)
    }

    static let nightBotCases: [(ItemKind, Int)] = nightCreatures.flatMap { kind in
        [3, 4].filter { $0 >= kind.spec.minHeroLevel }.map { (kind, $0) }
    }

    @Test(arguments: MechanicsTests.nightBotCases)
    func botClearsEachSakuraNightCreatureWithoutAHit(kind: ItemKind, entry: Int) {
        let level = nightLevel([.init(at: 400, kind: kind), .init(at: 900, kind: kind)], length: 1400, entry: entry)
        #expect(LevelValidator.botRun(level, boss: nil).finished)
    }

    @Test func botClearsASakuraNightRunOfEveryCreature() {
        let items = Self.nightCreatures.enumerated().map { PlacedItem(at: 400 + Double($0.offset) * 300, kind: $0.element) }
        #expect(LevelValidator.botRun(nightLevel(items, length: 2400), boss: nil).finished)
    }
}
