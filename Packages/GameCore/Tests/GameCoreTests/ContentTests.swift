import Foundation
import Testing
@testable import GameCore

@Suite struct ContentTests {
    /// Every level, at both boss distances the app uses (landscape and portrait).
    @Test(arguments: Content.levelIDs, [Tuning.wideBossOffset, Tuning.narrowBossOffset])
    func shippedLevelIsBeatableWithoutAHit(id: String, bossOffset: Double) throws {
        var tuning = Tuning()
        tuning.bossOffset = bossOffset
        let report = LevelValidator.validate(try Content.level(id), bosses: try Content.bosses(), tuning: tuning)
        #expect(report.problems == [])
        #expect(report.clearTime != nil)
    }

    @Test func levelFilesAreFound() {
        #expect(Content.levelIDs.count == 5)
        #expect(Content.levelIDs.first == "level_01")
    }

    /// The fifth and last world: the void, all abilities from the start, the final boss at the end
    /// with a last phase that needs the abilities.
    @Test func theFinalWorldIsTheVoid() throws {
        let level = try Content.level("level_05")
        #expect(level.background == "void")
        #expect(level.entryHeroLevel == 5 && level.bossRewardLevel == 5)
        #expect(level.boss == "boss_voidcat")
        let boss = try #require(try Content.bosses()["boss_voidcat"])
        #expect(boss.phases.last?.requires?.isEmpty == false)
        #expect(boss.attacks.contains { !($0.portals ?? []).isEmpty })
        #expect(boss.attacks.contains { $0.hazards.contains { $0.falls == true } })
        let lore = try Content.lore()
        #expect(lore.strings["level.5.name"]?.isEmpty == false)
        #expect(lore.strings["boss_voidcat.name"] == "The Void Cat")
        // Endless loops all five.
        var run = EndlessRun(levelCount: Content.levelIDs.count)
        for _ in 0..<5 { run.clear(stats: HeroStats(xp: Progression.xp(forLevel: 5)), score: 1) }
        #expect(run.levelIndex == 0 && run.loop == 2)
    }

    @Test func entryLevelsMatchEarlierBossRewards() throws {
        var guaranteed = 1
        for id in Content.levelIDs {
            let level = try Content.level(id)
            #expect(level.entryHeroLevel <= guaranteed, "\(id) assumes more than earlier levels grant")
            guaranteed = max(guaranteed, level.bossRewardLevel)
        }
    }

    @Test func everyBossDefinitionIsConsistent() throws {
        for boss in try Content.bosses().values {
            #expect(LevelValidator.problems(in: boss) == [])
        }
    }

    @Test func wallOfStumpsIsRejected() throws {
        let wall = stride(from: 400.0, to: 700, by: 14).map { PlacedItem(at: $0, kind: .stump) }
        var level = try Content.level("level_01")
        level.items = wall
        level.ravines = nil
        let report = LevelValidator.validate(level, bosses: try Content.bosses())
        #expect(!report.isValid)
        #expect(report.problems.contains { $0.contains("no-hit bot failed") })
    }

    @Test func crateWallBeforeSuperPounceIsRejected() throws {
        var level = try Content.level("level_03")
        level.items = [PlacedItem(at: 600, kind: .crateWall)]
        let report = LevelValidator.validate(level, bosses: try Content.bosses())
        #expect(report.problems.contains { $0.contains("crate_wall at 600 needs hero level 5") })
    }

    @Test func staticProblemsAreReported() throws {
        var level = try Content.level("level_01")
        level.boss = "boss_missing"
        level.items = [PlacedItem(at: 20, kind: .bush), PlacedItem(at: level.length - 10, kind: .bush)]
        let problems = LevelValidator.validate(level, bosses: try Content.bosses()).problems
        #expect(problems.contains { $0.contains("start runway") })
        #expect(problems.contains { $0.contains("too close to the boss") })
        #expect(problems.contains { $0.contains("not defined") })
    }

    @Test func badRavinesAreRejected() throws {
        var level = try Content.level("level_01")
        level.items = [PlacedItem(at: 820, kind: .stump), PlacedItem(at: 820, kind: .fish)]
        level.platforms = nil
        level.ravines = [Ravine(at: 100, width: 30), Ravine(at: 800, width: 40), Ravine(at: 850, width: 30),
                         Ravine(at: 1200, width: 90), Ravine(at: level.length - 70, width: 30)]
        let problems = LevelValidator.validate(level, bosses: try Content.bosses()).problems
        #expect(problems.contains { $0.contains("ravine at 100 is inside the 150-unit start runway") })
        #expect(problems.contains { $0.contains("stump at 820 stands in the ravine at 800") })
        #expect(!problems.contains { $0.contains("fish at 820") })
        #expect(problems.contains { $0.contains("ravine at 850 is too close to the one before it") })
        #expect(problems.contains { $0.contains("ravine at 1200 is 90 wide") })
        #expect(problems.contains { $0.contains("too close to the boss") && $0.contains("ravine") })
    }

    @Test func levelsWithoutRavinesStillLoad() throws {
        let json = #"{"id":"l","nameKey":"k","background":"forest","speed":110,"length":900,"entryHeroLevel":1,"boss":"b","bossRewardLevel":2,"items":[]}"#
        #expect(try ContentLoader.level(from: Data(json.utf8)).ravines == nil)
    }

    @Test func everyNameTheGameShowsIsInTheLoreFile() throws {
        let lore = try Content.lore()
        var keys = ["game.title", "game.tagline", "hero.name", "mode.endless.name"] + Ability.allCases.map { "ability.\($0.rawValue)" }
        for id in Content.levelIDs {
            let level = try Content.level(id)
            keys += [level.nameKey, "\(level.boss).name"]
        }
        for key in keys {
            #expect(lore.strings[key]?.isEmpty == false, "Lore.json has no text for \(key)")
        }
        #expect(lore.text("no.such.key") == "no.such.key")
    }

    /// Every interface label the app asks for (`ui("key")` / `ui("key", …)` in App/) is worded in Lore.json.
    @Test func everyInterfaceLabelIsInTheLoreFile() throws {
        let lore = try Content.lore()
        let app = Content.resources.deletingLastPathComponent()
        let files = FileManager.default.enumerator(atPath: app.path)?.compactMap { $0 as? String }
            .filter { $0.hasSuffix(".swift") } ?? []
        let pattern = try NSRegularExpression(pattern: #"\bui\("([a-z_]+)""#)
        var keys = Set<String>()
        for file in files {
            let source = try String(contentsOf: app.appendingPathComponent(file), encoding: .utf8)
            let range = NSRange(source.startIndex..., in: source)
            for match in pattern.matches(in: source, range: range) {
                keys.insert("ui." + (source as NSString).substring(with: match.range(at: 1)))
            }
        }
        #expect(keys.count > 10)
        for key in keys.sorted() {
            #expect(lore.strings[key]?.isEmpty == false, "Lore.json has no text for \(key)")
        }
    }

    @Test func fishTotalCountsTheFishInALevel() throws {
        let level = flatLevel(items: [PlacedItem(at: 300, kind: .fish), PlacedItem(at: 320, kind: .fish, y: 40),
                                      PlacedItem(at: 400, kind: .bush), PlacedItem(at: 500, kind: .yarnBasket)])
        #expect(level.fishTotal == 2)
        #expect(flatLevel().fishTotal == 0)
        for id in Content.levelIDs {
            #expect(try Content.level(id).fishTotal > 0, "\(id) has no fish to collect")
        }
    }

    /// A bot run can never report more fish than the level holds.
    @Test func aRunCollectsAtMostTheLevelsFish() throws {
        let level = flatLevel(items: stride(from: 300.0, to: 600, by: 30).map { PlacedItem(at: $0, kind: .fish) })
        var world = RunnerWorld(level: level, boss: nil)
        world.run(8)
        #expect(world.fishCollected == level.fishTotal)
    }
}
