import Foundation
import Testing
@testable import GameCore

/// Golden fish: the premium currency bought in packs, spent on cats as an alternative to fish, and
/// backed up to iCloud as a conflict-free union of purchases and cats.
@Suite struct GoldenFishTests {
    @Test func everyCatButTheFreeOneHasAGoldenPriceFromItsFishPrice() {
        let golden = Dictionary(uniqueKeysWithValues: Skin.catalog.compactMap { skin in
            skin.goldenPrice.map { (skin.id, $0) }
        })
        #expect(golden == ["shadow": 10, "misty": 10, "sakura": 50, "honey": 15, "pixie": 20, "clover": 25,
                           "snowball": 30, "napster": 40, "toffee": 45, "cabage": 100, "sharky": 100])
        #expect(Skin.named(Skin.free)?.goldenPrice == nil)
        // The rule they were first set by: fish price / 20, rounded up to a multiple of 5, at least 10.
        // Sakura's prices were later raised by hand.
        for skin in Skin.catalog where skin.id != Skin.free && skin.id != "sakura" {
            let derived = max(10, Int((Double(skin.price) / 20 / 5).rounded(.up)) * 5)
            #expect(skin.goldenPrice == derived, "\(skin.id)")
        }
    }

    @Test func thePacksAreTheFourProductsWithTheirAmounts() {
        #expect(GoldenFish.packs.map(\.amount) == [50, 150, 350, 800])
        #expect(GoldenFish.amount(forProduct: "com.pryvalov.purrfectlydangerous.golden50") == 50)
        #expect(GoldenFish.amount(forProduct: "com.pryvalov.purrfectlydangerous.golden150") == 150)
        #expect(GoldenFish.amount(forProduct: "com.pryvalov.purrfectlydangerous.golden350") == 350)
        #expect(GoldenFish.amount(forProduct: "com.pryvalov.purrfectlydangerous.golden800") == 800)
        #expect(GoldenFish.amount(forProduct: "com.pryvalov.purrfectlydangerous.unlock_all") == nil)
        #expect(Set(GoldenFish.productIDs).count == 4)
    }

    @Test func aNewSaveHasNoGoldenFish() {
        let game = SaveGame()
        #expect(game.goldenFish == 0)
        #expect(game.goldenPurchases.isEmpty && game.goldenSkins.isEmpty)
    }

    @Test func crediting() {
        var game = SaveGame()
        do { let changed = game.creditGolden(transaction: "1001", amount: 50); #expect(changed) }
        do { let changed = game.creditGolden(transaction: "1002", amount: 150); #expect(changed) }
        #expect(game.goldenFish == 200)
        #expect(game.hasCredited(transaction: "1001"))
        #expect(!game.hasCredited(transaction: "9999"))
        // Nonsense changes nothing.
        do { let changed = game.creditGolden(transaction: "1003", amount: 0); #expect(!changed) }
        do { let changed = game.creditGolden(transaction: "1004", amount: -5); #expect(!changed) }
        do { let changed = game.creditGolden(transaction: "", amount: 50); #expect(!changed) }
        #expect(game.goldenFish == 200)
        // Golden fish never touch the fish wallet.
        #expect(game.fishWallet == 0)
    }

    @Test func creditingTheSameTransactionTwiceIsANoOp() {
        var game = SaveGame()
        do { let changed = game.creditGolden(transaction: "42", amount: 350); #expect(changed) }
        do { let changed = game.creditGolden(transaction: "42", amount: 350); #expect(!changed) }
        do { let changed = game.creditGolden(transaction: "42", amount: 800); #expect(!changed) }
        #expect(game.goldenFish == 350)
        #expect(game.goldenPurchases == ["42": 350])
    }

    @Test func buyingACatWithEachCurrency() {
        var game = SaveGame()
        game.addFish(200)
        game.creditGolden(transaction: "t1", amount: 50)

        do { let result = game.unlock(skin: "shadow", with: .fish); #expect(result == .unlocked) }
        #expect(game.fishWallet == 50 && game.goldenFish == 50)

        do { let result = game.unlock(skin: "honey", with: .golden); #expect(result == .unlocked) }
        #expect(game.fishWallet == 50)
        #expect(game.goldenFish == 35)
        #expect(game.goldenSkins == ["honey": 15])
        #expect(game.owns("honey") && game.owns("shadow"))
        do { let changed = game.select(skin: "honey"); #expect(changed) }

        // Owned is owned, whatever it was bought with.
        do { let result = game.unlock(skin: "honey", with: .fish); #expect(result == .alreadyOwned) }
        do { let result = game.unlock(skin: "shadow", with: .golden); #expect(result == .alreadyOwned) }
        do { let result = game.unlock(skin: "fluffy", with: .golden); #expect(result == .alreadyOwned) }
        do { let result = game.unlock(skin: "no_such_cat", with: .golden); #expect(result == .unknownSkin) }
        #expect(game.goldenFish == 35 && game.fishWallet == 50)

        // Exactly enough is enough.
        game.creditGolden(transaction: "t2", amount: 150)
        do { let result = game.unlock(skin: "toffee", with: .golden); #expect(result == .unlocked) }
        do { let result = game.unlock(skin: "pixie", with: .golden); #expect(result == .unlocked) }
        do { let result = game.unlock(skin: "pixie", with: .golden); #expect(result == .alreadyOwned) }
        #expect(game.goldenFish == 120)
    }

    @Test func notEnoughGoldenFishChangesNothing() {
        var game = SaveGame()
        game.addFish(5000)
        game.creditGolden(transaction: "t1", amount: 30)
        let before = game
        do { let result = game.unlock(skin: "toffee", with: .golden); #expect(result == .notEnoughGoldenFish(missing: 15)) }
        #expect(game == before)
        #expect(!game.owns("toffee"))
        // The fish price is still there to pay instead.
        do { let result = game.unlock(skin: "toffee", with: .fish); #expect(result == .unlocked) }
        #expect(game.goldenFish == 30 && game.fishWallet == 4100)
    }

    @Test func mergingTwoDivergedSavesGivesTheUnionAndTheRightBalance() {
        // One phone backed up, then two phones went their own ways.
        var shared = SaveGame()
        shared.creditGolden(transaction: "a", amount: 50)
        _ = shared.unlock(skin: "shadow", with: .golden)          // 40 left

        var phone = shared
        phone.creditGolden(transaction: "b", amount: 150)         // 190
        _ = phone.unlock(skin: "toffee", with: .golden)           // 145
        phone.addFish(200)
        do { let result = phone.unlock(skin: "misty", with: .fish); #expect(result == .unlocked) }

        var tablet = shared
        tablet.creditGolden(transaction: "c", amount: 350)        // 390
        _ = tablet.unlock(skin: "snowball", with: .golden)        // 360

        var left = phone
        do { let changed = left.merge(tablet.cloudBackup); #expect(changed) }
        var right = tablet
        do { let changed = right.merge(phone.cloudBackup); #expect(changed) }

        for merged in [left, right] {
            #expect(merged.goldenPurchases == ["a": 50, "b": 150, "c": 350])
            #expect(merged.goldenSkins == ["shadow": 10, "toffee": 45, "snowball": 30])
            #expect(merged.ownedSkins == ["fluffy", "shadow", "toffee", "misty", "snowball"])
            #expect(merged.goldenFish == 550 - 85)
        }
        #expect(left.cloudBackup == right.cloudBackup)
        // Merging again, or merging an older copy, changes nothing and never takes anything away.
        do { let changed = left.merge(tablet.cloudBackup); #expect(!changed) }
        do { let changed = left.merge(shared); #expect(!changed) }
        do { let changed = left.merge(CloudBackup()); #expect(!changed) }
        #expect(left.goldenFish == 465)
        // Only what syncs is merged: each phone keeps its own fish wallet and selected cat.
        #expect(left.fishWallet == phone.fishWallet && right.fishWallet == tablet.fishWallet)
    }

    @Test func aNewPhoneGetsEverythingBackFromTheBackup() throws {
        var old = SaveGame()
        old.creditGolden(transaction: "a", amount: 800)
        _ = old.unlock(skin: "toffee", with: .golden)
        old.addFish(150)
        _ = old.unlock(skin: "shadow")
        let data = try JSONEncoder().encode(old.cloudBackup)

        var fresh = SaveGame()
        do { let changed = fresh.merge(try JSONDecoder().decode(CloudBackup.self, from: data)); #expect(changed) }
        #expect(fresh.goldenFish == 755)
        #expect(fresh.ownedSkins == ["fluffy", "toffee", "shadow"])
        // A transaction replayed by the App Store after the restore is not credited again.
        do { let changed = fresh.creditGolden(transaction: "a", amount: 800); #expect(!changed) }
        #expect(fresh.goldenFish == 755)
    }

    @Test func spendingTheSameGoldenFishOnTwoPhonesNeverGoesBelowZero() {
        var shared = SaveGame()
        shared.creditGolden(transaction: "a", amount: 50)
        var phone = shared
        _ = phone.unlock(skin: "toffee", with: .golden)           // 45 of 50
        var tablet = shared
        _ = tablet.unlock(skin: "clover", with: .golden)          // 25 of 50
        phone.merge(tablet)
        #expect(phone.owns("toffee") && phone.owns("clover"))
        #expect(phone.goldenFish == 0)
        // The 20 owed come out of the next purchase.
        phone.creditGolden(transaction: "b", amount: 50)
        #expect(phone.goldenFish == 30)
    }

    @Test func unknownCatsAndBadAmountsInABackupAreNotOwned() {
        var game = SaveGame()
        let odd = CloudBackup(goldenPurchases: ["a": 50, "b": -10, "c": 0],
                              goldenSkins: ["future_cat": 20],
                              ownedSkins: ["made_up", "honey"])
        do { let changed = game.merge(odd); #expect(changed) }
        #expect(game.goldenPurchases == ["a": 50])
        #expect(game.ownedSkins == ["fluffy", "honey"])
        #expect(!game.owns("future_cat"))
        // A cat from a newer version stays paid for, so it is not counted again.
        #expect(game.goldenFish == 30)
    }

    @Test func goldenFishSurviveASaveAndLoad() throws {
        let suite = "gamecore.tests.\(UInt64.random(in: 0...UInt64.max))"
        let defaults = try #require(UserDefaults(suiteName: suite))
        defer { defaults.removePersistentDomain(forName: suite) }
        let store = DefaultsSaveStore(defaults: defaults)

        var game = SaveGame()
        game.creditGolden(transaction: "2000000123", amount: 150)
        _ = game.unlock(skin: "napster", with: .golden)
        store.save(game)

        let loaded = store.load()
        #expect(loaded == game)
        #expect(loaded.goldenFish == 110)
        #expect(loaded.owns("napster"))
    }

    @Test func aSaveFromBeforeGoldenFishStillLoads() throws {
        // The format shipped with the fish wallet and the shop, before golden fish.
        let old = #"{"xp":900,"unlockedLevels":3,"bestScores":{"level_02":340},"soundOn":false,"bestEndlessScore":1200,"bestEndlessCleared":2,"selectedSkin":"honey","fishWallet":75,"ownedSkins":["fluffy","honey"]}"#
        let game = try JSONDecoder().decode(SaveGame.self, from: Data(old.utf8))
        #expect(game.goldenFish == 0)
        #expect(game.goldenPurchases.isEmpty && game.goldenSkins.isEmpty)
        #expect(game.fishWallet == 75)
        #expect(game.ownedSkins == ["fluffy", "honey"])
        #expect(game.selectedSkin == "honey")
        #expect(game.xp == 900 && game.unlockedLevels == 3 && !game.soundOn && game.bestEndlessScore == 1200)
        #expect(try JSONDecoder().decode(CloudBackup.self, from: Data("{}".utf8)) == CloudBackup(giftsTakenBack: false))
    }

    @Test func theFreeSakuraFromTestFlightIsTakenBackOnce() throws {
        // A save from a build that gave Sakura away: she is taken back, and the cat in use falls back.
        let gifted = #"{"fishWallet":40,"ownedSkins":["fluffy","sakura","honey"],"selectedSkin":"sakura"}"#
        var game = try JSONDecoder().decode(SaveGame.self, from: Data(gifted.utf8))
        #expect(game.ownedSkins == ["fluffy", "honey"])
        #expect(game.selectedSkin == "fluffy")
        #expect(game.fishWallet == 40)
        // Paid for in golden fish: kept.
        let paid = #"{"goldenPurchases":{"a":50},"goldenSkins":{"sakura":15},"ownedSkins":["fluffy","sakura"],"selectedSkin":"sakura"}"#
        let payer = try JSONDecoder().decode(SaveGame.self, from: Data(paid.utf8))
        #expect(payer.owns("sakura") && payer.selectedSkin == "sakura")
        // An old iCloud backup does not hand her out again; a backup written since does.
        do { let changed = game.merge(CloudBackup(ownedSkins: ["fluffy", "sakura"], giftsTakenBack: false)); #expect(!changed) }
        #expect(!game.owns("sakura"))
        // Bought with fish after the step: the save keeps her through a save and load.
        game.addFish(3500)
        do { let result = game.unlock(skin: "sakura"); #expect(result == .unlocked) }
        let reloaded = try JSONDecoder().decode(SaveGame.self, from: JSONEncoder().encode(game))
        #expect(reloaded.owns("sakura"))
        var other = SaveGame()
        do { let changed = other.merge(game.cloudBackup); #expect(changed) }
        #expect(other.owns("sakura"))
    }

    @Test func aCatPaidForInGoldenFishIsOwnedEvenIfTheOwnedListLostIt() throws {
        let odd = #"{"goldenPurchases":{"a":50},"goldenSkins":{"honey":15},"ownedSkins":["fluffy"],"selectedSkin":"honey"}"#
        let game = try JSONDecoder().decode(SaveGame.self, from: Data(odd.utf8))
        #expect(game.owns("honey"))
        #expect(game.selectedSkin == "honey")
        #expect(game.goldenFish == 35)
    }
}
