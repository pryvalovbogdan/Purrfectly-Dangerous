import Foundation
import Testing
@testable import GameCore

/// The CATS shop: a fish wallet filled by every run, and cat skins bought from it. Purely cosmetic.
@Suite struct SkinShopTests {
    @Test func theCatalogHasEveryCatAtItsPrice() {
        let prices = Dictionary(uniqueKeysWithValues: Skin.catalog.map { ($0.id, $0.price) })
        #expect(prices == ["fluffy": 0, "shadow": 150, "misty": 200, "sakura": 250, "honey": 300, "pixie": 400,
                           "clover": 500, "snowball": 600, "napster": 750, "toffee": 900, "cabage": 2000,
                           "sharky": 2000])
        #expect(Skin.catalog.map(\.id).first == Skin.free)
        #expect(Skin.catalog.count == Set(Skin.catalog.map(\.id)).count)
        #expect(Skin.named("honey")?.nameKey == "skin.honey.name")
        #expect(Skin.named("honey")?.descriptionKey == "skin.honey.desc")
        #expect(Skin.named("orange") == nil)
    }

    @Test func aNewSaveOwnsOnlyFluffyWithAnEmptyWallet() {
        let game = SaveGame()
        #expect(game.fishWallet == 0)
        #expect(game.ownedSkins == ["fluffy"])
        #expect(game.selectedSkin == "fluffy")
        for skin in Skin.catalog where skin.id != Skin.free { #expect(!game.owns(skin.id)) }
    }

    @Test func everyRunsFishAddUpInTheWallet() {
        var game = SaveGame()
        game.addFish(12)     // a level won
        game.addFish(5)      // a level lost
        game.addFish(0)
        game.addFish(-3)     // nonsense is ignored
        #expect(game.fishWallet == 17)
    }

    @Test func unlockingChecksThePriceAndSpendsTheFish() {
        var game = SaveGame()
        game.addFish(180)
        do { let result = game.unlock(skin: "misty"); #expect(result == .notEnoughFish(missing: 20)) }
        #expect(game.fishWallet == 180)
        #expect(!game.owns("misty"))

        do { let result = game.unlock(skin: "shadow"); #expect(result == .unlocked) }
        #expect(game.fishWallet == 30)
        #expect(game.owns("shadow"))
        do { let result = game.unlock(skin: "shadow"); #expect(result == .alreadyOwned) }
        #expect(game.fishWallet == 30)
        do { let result = game.unlock(skin: "fluffy"); #expect(result == .alreadyOwned) }
        do { let result = game.unlock(skin: "no_such_cat"); #expect(result == .unknownSkin) }

        // Exactly enough is enough.
        game.addFish(170)
        do { let result = game.unlock(skin: "misty"); #expect(result == .unlocked) }
        #expect(game.fishWallet == 0)
    }

    @Test func onlyAnOwnedSkinCanBeSelected() {
        var game = SaveGame()
        do { let result = game.select(skin: "sharky"); #expect(!result) }
        #expect(game.selectedSkin == "fluffy")
        do { let result = game.select(skin: "no_such_cat"); #expect(!result) }
        game.addFish(2000)
        do { let result = game.unlock(skin: "sharky"); #expect(result == .unlocked) }
        do { let result = game.select(skin: "sharky"); #expect(result) }
        #expect(game.selectedSkin == "sharky")
        do { let result = game.select(skin: "fluffy"); #expect(result) }
        #expect(game.selectedSkin == "fluffy")
    }

    @Test func theWalletAndCatsSurviveASaveAndLoad() throws {
        let suite = "gamecore.tests.\(UInt64.random(in: 0...UInt64.max))"
        let defaults = try #require(UserDefaults(suiteName: suite))
        defer { defaults.removePersistentDomain(forName: suite) }
        let store = DefaultsSaveStore(defaults: defaults)

        var game = SaveGame()
        game.complete(levelID: "level_01", score: 120, xp: 300)
        game.addFish(700)
        _ = game.unlock(skin: "honey")
        _ = game.select(skin: "honey")
        store.save(game)

        let loaded = store.load()
        #expect(loaded == game)
        #expect(loaded.fishWallet == 400)
        #expect(loaded.ownedSkins == ["fluffy", "honey"])
        #expect(loaded.selectedSkin == "honey")
        #expect(loaded.bestScores["level_01"] == 120)
    }

    @Test func anOlderSaveLoadsWithAnEmptyWalletAndFluffy() throws {
        // Before the shop: the one cat was "orange", and there was no wallet or owned list.
        let old = #"{"xp":300,"unlockedLevels":2,"bestScores":{"level_01":120},"soundOn":true,"selectedSkin":"orange"}"#
        let game = try JSONDecoder().decode(SaveGame.self, from: Data(old.utf8))
        #expect(game.fishWallet == 0)
        #expect(game.ownedSkins == ["fluffy"])
        #expect(game.selectedSkin == "fluffy")
        #expect(game.bestScores["level_01"] == 120 && game.xp == 300 && game.unlockedLevels == 2)
    }

    @Test func aDamagedSaveCannotHoldALockedOrUnknownCat() throws {
        // Owned list without fluffy, a selection that is not owned: fluffy is put back and selected.
        let odd = #"{"fishWallet":50,"ownedSkins":["shadow","made_up"],"selectedSkin":"sharky"}"#
        let game = try JSONDecoder().decode(SaveGame.self, from: Data(odd.utf8))
        #expect(game.fishWallet == 50)
        #expect(game.ownedSkins == ["fluffy", "shadow"])
        #expect(game.selectedSkin == "fluffy")
    }

    @Test func everyCatHasANameAndADescriptionInTheLoreFile() throws {
        let lore = try Content.lore()
        for skin in Skin.catalog {
            #expect(lore.strings[skin.nameKey]?.isEmpty == false, "no name for \(skin.id)")
            #expect(lore.strings[skin.descriptionKey]?.isEmpty == false, "no description for \(skin.id)")
        }
    }
}
