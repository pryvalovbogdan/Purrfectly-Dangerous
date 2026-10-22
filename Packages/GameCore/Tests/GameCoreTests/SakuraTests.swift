import Foundation
import Testing
@testable import GameCore

/// Cat routes (the Sakura route's Blossom Path in slot 1), moving platforms and the route's content.
@Suite struct SakuraTests {
    func level(_ id: String, background: String = "forest") -> LevelDefinition {
        LevelDefinition(id: id, nameKey: "level.\(id).name", background: background, speed: 110, length: 900,
                        entryHeroLevel: 1, shrineLevel: nil, boss: "none", bossRewardLevel: 2, items: [])
    }

    var base: [LevelDefinition] { (1...5).map { level(String(format: "level_%02d", $0)) } }
    var book: RouteBook { RouteBook(overrides: ["sakura": [0: level("sakura_01", background: "sakura")]]) }

    // MARK: Routes

    @Test func selectingSakuraSwapsInHerBlossomPathAsLevelOne() {
        let route = book.levels(for: "sakura", base: base)
        #expect(route.map(\.id) == ["sakura_01", "level_02", "level_03", "level_04", "level_05"])
        #expect(route[0].background == "sakura")
        #expect(book.hasRoute("sakura"))
    }

    @Test func everyOtherCatKeepsTheNormalWorlds() {
        for skin in Skin.catalog.map(\.id) where skin != "sakura" {
            #expect(book.levels(for: skin, base: base).map(\.id) == base.map(\.id), "\(skin)")
        }
    }

    @Test func anUnknownRouteOrSlotFallsBackToTheNormalLevels() {
        #expect(book.levels(for: "no_such_cat", base: base) == base)
        // An override for a slot the game doesn't have is ignored.
        let odd = RouteBook(overrides: ["pixie": [9: level("pixie_10")], "sakura": [-1: level("sakura_00")]])
        #expect(odd.levels(for: "pixie", base: base) == base)
        #expect(odd.levels(for: "sakura", base: base) == base)
        #expect(!odd.hasRoute("napster"))
    }

    @Test func routeFilesAreNamedByCatAndSlot() {
        #expect(RouteBook.slot(fromFileName: "route_sakura_01.json")?.skin == "sakura")
        #expect(RouteBook.slot(fromFileName: "route_sakura_01.json")?.slot == 0)
        #expect(RouteBook.slot(fromFileName: "route_sakura_03.json")?.slot == 2)
        #expect(RouteBook.slot(fromFileName: "level_01.json") == nil)
        #expect(RouteBook.slot(fromFileName: "route_sakura.json") == nil)
        #expect(RouteBook.slot(fromFileName: "route_sakura_00.json") == nil)
    }

    @Test func theEndlessRunFollowsTheSelectedCatsRoute() {
        let route = book.levels(for: "sakura", base: base)
        var run = EndlessRun(levelCount: route.count)
        var played: [String] = []
        for _ in 0..<6 {
            played.append(route[run.levelIndex].id)
            run.clear(stats: HeroStats(xp: Progression.xp(forLevel: 3)), score: 1)
        }
        #expect(played == ["sakura_01", "level_02", "level_03", "level_04", "level_05", "sakura_01"])
    }

    @Test func progressIsKeptPerLevelSoSakurasLevelOneHasItsOwnBest() {
        var game = SaveGame()
        game.complete(levelID: "level_01", score: 500, xp: 100)
        game.complete(levelID: "sakura_01", score: 120, xp: 100)
        #expect(game.bestScores["level_01"] == 500)
        #expect(game.bestScores["sakura_01"] == 120)
    }

    // MARK: Content

    @Test func theSakuraRouteShipsItsBlossomPath() throws {
        let book = try Content.routes()
        let path = try #require(book.overrides["sakura"]?[0])
        #expect(path.id == "sakura_01" && path.nameKey == "level.sakura_1.name")
        #expect(path.background == "sakura" && path.speed == 110)
        #expect(path.entryHeroLevel == 1 && path.shrineLevel == 2 && path.bossRewardLevel == 3)
        #expect(path.items.contains { $0.kind == .yarnBasket })
        #expect(path.boss == "boss_kitsune")
        #expect(try Content.bosses()["boss_kitsune"] != nil)
        let lore = try Content.lore()
        #expect(lore.strings["level.sakura_1.name"] == "Blossom Path")
        #expect(lore.strings["boss_kitsune.name"] == "Blossom Kitsune Guardian")
        // Only the Sakura route, slots 1 and 2 for now.
        #expect(book.overrides.keys.sorted() == ["sakura"])
        #expect(book.overrides["sakura"]?.keys.sorted() == [0, 1])
    }

    @Test func withSakuraSelectedSlotsOneAndTwoAreHersAndTheRestNormal() throws {
        let book = try Content.routes()
        let base = try Content.levelIDs.map(Content.level)
        let route = book.levels(for: "sakura", base: base)
        #expect(route.map(\.id) == ["sakura_01", "sakura_02"] + base.dropFirst(2).map(\.id))
        #expect(book.levels(for: "fluffy", base: base).map(\.id) == base.map(\.id))
    }

    @Test func theSakuraRouteShipsPetalBridgesAsSlotTwo() throws {
        let bridges = try #require(try Content.routes().overrides["sakura"]?[1])
        #expect(bridges.id == "sakura_02" && bridges.nameKey == "level.sakura_2.name")
        #expect(bridges.background == "sakura_dusk" && bridges.speed == 120)
        // Sakura arrives from her first level with Double Pounce, and leaves with Ghost Dash.
        #expect(bridges.entryHeroLevel == 3 && bridges.bossRewardLevel == 4)
        #expect(bridges.boss == "boss_toad")
        #expect(try Content.bosses()["boss_toad"] != nil)
        let lore = try Content.lore()
        #expect(lore.strings["level.sakura_2.name"] == "Petal Bridges")
        #expect(lore.strings["boss_toad.name"] == "Lantern Toad Guardian")
        let blossom = try #require(try Content.routes().overrides["sakura"]?[0])
        #expect(bridges.entryHeroLevel <= blossom.bossRewardLevel)
    }

    @Test(arguments: [Tuning.wideBossOffset, Tuning.narrowBossOffset])
    func petalBridgesIsBeatableWithoutAHit(bossOffset: Double) throws {
        let bridges = try #require(try Content.routes().overrides["sakura"]?[1])
        var tuning = Tuning()
        tuning.bossOffset = bossOffset
        let report = LevelValidator.validate(bridges, bosses: try Content.bosses(), tuning: tuning)
        #expect(report.problems == [])
        #expect(report.clearTime != nil)
    }

    @Test(arguments: [Tuning.wideBossOffset, Tuning.narrowBossOffset])
    func theBlossomPathIsBeatableWithoutAHit(bossOffset: Double) throws {
        let path = try #require(try Content.routes().overrides["sakura"]?[0])
        var tuning = Tuning()
        tuning.bossOffset = bossOffset
        let report = LevelValidator.validate(path, bosses: try Content.bosses(), tuning: tuning)
        #expect(report.problems == [])
        #expect(report.clearTime != nil)
    }

    // MARK: Moving platforms

    @Test func aMovingPlatformSwingsOnTheWorldClock() {
        let side = Platform(at: 300, width: 40, y: 14, mode: .moves, period: 2, offset: 0, axis: .x, travel: 30)
        let lift = Platform(at: 300, width: 40, y: 20, mode: .moves, period: 2, offset: 0.5, axis: .y, travel: 10)
        #expect(side.left(at: 0) == 300)
        #expect(abs(side.left(at: 0.5) - 330) < 1e-9)
        #expect(abs(side.left(at: 1.5) - 270) < 1e-9)
        #expect(side.top(at: 0.7) == 14)
        #expect(abs(lift.top(at: 0) - 30) < 1e-9)
        #expect(lift.left(at: 1.3) == 300)
        // Deterministic: the same time, the same place.
        #expect(side.left(at: 12.34) == side.left(at: 12.34))
    }

    func ride(_ platform: Platform) -> (world: RunnerWorld, rode: [Double]) {
        var level = flatLevel()
        level.platforms = [platform]
        var world = RunnerWorld(level: level, boss: nil)
        while world.distance < platform.at - 30 { _ = world.step(Input(), dt: dt) }
        _ = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        var rode: [Double] = []
        for _ in 0..<240 {
            _ = world.step(Input(jumpHeld: world.heroVY > 0), dt: dt)
            if world.standingOn == 0 { rode.append(world.heroY) }
        }
        return (world, rode)
    }

    @Test func theKittenRidesAVerticalPlatformUpAndDown() {
        let lift = Platform(at: 280, width: 200, y: 20, mode: .moves, period: 1.6, axis: .y, travel: 10)
        let (world, rode) = ride(lift)
        #expect(rode.count > 20)
        #expect((rode.max() ?? 0) - (rode.min() ?? 0) > 8)
        #expect(world.stats.hearts == 3)
    }

    @Test func aSidewaysPlatformCarriesTheKittenWithIt() {
        var level = flatLevel()
        let side = Platform(at: 280, width: 200, y: 14, mode: .moves, period: 2, axis: .x, travel: 20)
        level.platforms = [side]
        var world = RunnerWorld(level: level, boss: nil)
        while world.distance < 250 { _ = world.step(Input(), dt: dt) }
        _ = world.step(Input(jumpPressed: true, jumpHeld: true), dt: dt)
        while world.standingOn != 0, world.time < 5 { _ = world.step(Input(jumpHeld: true), dt: dt) }
        #expect(world.standingOn == 0)
        // Standing on it, each step moves the kitten by its run plus the platform's own move.
        let before = world.distance, leftBefore = world.platformLeft(0)
        _ = world.step(Input(), dt: dt)
        if world.standingOn == 0 {
            let carried = world.platformLeft(0) - leftBefore
            #expect(abs(world.distance - before - (world.level.speed * dt + carried)) < 1e-6)
        }
    }

    @Test func theValidatorChecksMovingPlatformsAndTheBotCrossesOnOne() {
        var bad = flatLevel()
        bad.platforms = [Platform(at: 400, width: 40, y: 40, mode: .moves, axis: .y, travel: 30),
                         Platform(at: 600, width: 40, y: 12, mode: .moves, axis: .x)]
        let problems = LevelValidator.surfaceProblems(in: bad, tuning: Tuning())
        #expect(problems.contains { $0.contains("platform at 400") && $0.contains("high") })
        #expect(problems.contains { $0.contains("platform at 600") && $0.contains("travel") })

        // A ravine too wide to jump, bridged by a platform that swings over it.
        var bridge = flatLevel(ravines: [Ravine(at: 400, width: 130)], length: 1000)
        bridge.platforms = [Platform(at: 430, width: 50, y: 12, mode: .moves, period: 3, axis: .x, travel: 15)]
        #expect(LevelValidator.surfaceProblems(in: bridge, tuning: Tuning()).isEmpty)
        #expect(LevelValidator.botRun(bridge, boss: nil).finished)
    }
}
