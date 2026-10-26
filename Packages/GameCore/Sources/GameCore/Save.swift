import Foundation

public struct SaveGame: Codable, Sendable, Equatable {
    public var xp = 0
    /// Number of levels the player may start on their own, counted from the first. Levels are
    /// opened by beating them in an endless run.
    public var unlockedLevels = 0
    public var bestScores: [String: Int] = [:]
    public var soundOn = true
    public var bestEndlessScore = 0
    /// Most levels beaten in one endless run.
    public var bestEndlessCleared = 0
    /// The cat skin picked on the CATS screen, by neutral id; always one the player owns.
    public private(set) var selectedSkin = SaveGame.defaultSkin
    /// Fish banked from every run (levels and endless, won or lost), spent on cats in the shop.
    public private(set) var fishWallet = 0
    /// Cats unlocked in the shop, by id; always holds the free one.
    public private(set) var ownedSkins: Set<String> = [Skin.free]
    /// Golden fish bought: App Store transaction id → golden fish credited for it. Keyed by
    /// transaction so the same purchase can never be credited twice, and so copies merge cleanly.
    public private(set) var goldenPurchases: [String: Int] = [:]
    /// Cats bought with golden fish: cat id → golden fish paid. The balance is what was bought less
    /// what was paid here (see `goldenFish`), so it is never stored and never conflicts.
    public private(set) var goldenSkins: [String: Int] = [:]
    /// Whether the cats once given away free (`freeGifts`) have been taken back from this save. True
    /// for every save from now on; false only in data written before the step existed.
    public private(set) var giftsTakenBack = true

    /// The skin every player has from the start.
    public static let defaultSkin = Skin.free
    /// What the one cat was called before the shop; such saves now pick the free cat.
    static let legacySkins: Set<String> = ["orange"]
    /// Cats that TestFlight builds gave every player for free at launch. They are taken back once,
    /// unless they were paid for in golden fish (a fish purchase was impossible while they were free).
    static let freeGifts: Set<String> = ["sakura"]

    /// `owned` without the free gifts that were not paid for in golden fish.
    static func withoutFreeGifts(_ owned: Set<String>, golden: [String: Int]) -> Set<String> {
        owned.subtracting(freeGifts.subtracting(golden.keys))
    }

    public init() {}

    /// Fields added after the first release are optional in the data, so older saves still load.
    public init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CodingKeys.self)
        xp = try values.decodeIfPresent(Int.self, forKey: .xp) ?? 0
        unlockedLevels = try values.decodeIfPresent(Int.self, forKey: .unlockedLevels) ?? 0
        bestScores = try values.decodeIfPresent([String: Int].self, forKey: .bestScores) ?? [:]
        soundOn = try values.decodeIfPresent(Bool.self, forKey: .soundOn) ?? true
        bestEndlessScore = try values.decodeIfPresent(Int.self, forKey: .bestEndlessScore) ?? 0
        bestEndlessCleared = try values.decodeIfPresent(Int.self, forKey: .bestEndlessCleared) ?? 0
        fishWallet = max(0, try values.decodeIfPresent(Int.self, forKey: .fishWallet) ?? 0)
        // Only cats the game has; the free one always.
        let owned = try values.decodeIfPresent(Set<String>.self, forKey: .ownedSkins) ?? []
        goldenPurchases = (try values.decodeIfPresent([String: Int].self, forKey: .goldenPurchases) ?? [:])
            .filter { $0.value > 0 }
        goldenSkins = (try values.decodeIfPresent([String: Int].self, forKey: .goldenSkins) ?? [:])
            .filter { $0.value > 0 }
        // The free gifts are taken back once (a save from before that step), then the flag is set.
        let kept = try values.decodeIfPresent(Bool.self, forKey: .giftsTakenBack) ?? false
            ? owned : Self.withoutFreeGifts(owned, golden: goldenSkins)
        // A cat paid for in golden fish is owned.
        ownedSkins = kept.union(goldenSkins.keys).filter { Skin.named($0) != nil }.union([Skin.free])
        let selected = try values.decodeIfPresent(String.self, forKey: .selectedSkin) ?? Self.defaultSkin
        selectedSkin = ownedSkins.contains(selected) ? selected : Self.defaultSkin
    }

    public func owns(_ skin: String) -> Bool {
        ownedSkins.contains(skin)
    }

    /// Banks the fish picked up in a run that just ended (a level won or lost, or an endless level).
    public mutating func addFish(_ count: Int) {
        fishWallet += max(0, count)
    }

    /// Buys `skin` with fish from the wallet, or with golden fish, if there are enough and it is not
    /// owned yet. Otherwise nothing changes.
    @discardableResult
    public mutating func unlock(skin id: String, with currency: Currency = .fish) -> SkinUnlock {
        guard let skin = Skin.named(id) else { return .unknownSkin }
        guard !owns(id) else { return .alreadyOwned }
        guard skin.available else { return .unavailable }
        switch currency {
        case .fish:
            guard fishWallet >= skin.price else { return .notEnoughFish(missing: skin.price - fishWallet) }
            fishWallet -= skin.price
        case .golden:
            guard let price = skin.goldenPrice, price > 0 else { return .notForGoldenFish }
            guard goldenFish >= price else { return .notEnoughGoldenFish(missing: price - goldenFish) }
            goldenSkins[id] = price
        }
        ownedSkins.insert(id)
        return .unlocked
    }

    // MARK: Golden fish

    /// Golden fish ever credited from purchases.
    public var goldenBought: Int { goldenPurchases.values.reduce(0, +) }
    /// Golden fish ever paid for cats.
    public var goldenSpent: Int { goldenSkins.values.reduce(0, +) }
    /// Golden fish to spend. Never below 0: if two phones spent the same golden fish while apart,
    /// the merged save owes the difference and later purchases pay it off first.
    public var goldenFish: Int { max(0, goldenBought - goldenSpent) }

    /// Credits `amount` golden fish for the App Store transaction `transactionID`. A transaction
    /// already credited (a replayed or merged one) changes nothing. Returns whether it was new.
    @discardableResult
    public mutating func creditGolden(transaction transactionID: String, amount: Int) -> Bool {
        guard amount > 0, !transactionID.isEmpty, goldenPurchases[transactionID] == nil else { return false }
        goldenPurchases[transactionID] = amount
        return true
    }

    /// Whether the transaction `transactionID` has been credited.
    public func hasCredited(transaction transactionID: String) -> Bool {
        goldenPurchases[transactionID] != nil
    }

    /// What goes to iCloud: purchases, golden-bought cats and owned cats.
    public var cloudBackup: CloudBackup {
        CloudBackup(goldenPurchases: goldenPurchases, goldenSkins: goldenSkins, ownedSkins: ownedSkins,
                    giftsTakenBack: giftsTakenBack)
    }

    /// Takes in a copy kept elsewhere (iCloud, another phone): the union of purchases, golden-bought
    /// cats and owned cats. Never removes anything, so merging in any order, any number of times,
    /// gives the same result. Cats this version does not know are not owned here. Returns whether anything changed.
    @discardableResult
    public mutating func merge(_ remote: CloudBackup) -> Bool {
        let before = (goldenPurchases, goldenSkins, ownedSkins)
        for (transaction, amount) in remote.goldenPurchases where amount > 0 {
            // The same transaction always carries the same amount; max keeps the merge order-free.
            goldenPurchases[transaction] = max(goldenPurchases[transaction] ?? 0, amount)
        }
        // Kept even for a cat this version does not know (bought in a newer one), so its price stays
        // spent and the entry is not dropped from iCloud when this copy is written back.
        for (id, price) in remote.goldenSkins where price > 0 {
            goldenSkins[id] = max(goldenSkins[id] ?? 0, price)
        }
        // A backup written before the free gifts were taken back would hand them out again.
        let remoteOwned = remote.giftsTakenBack ? remote.ownedSkins
            : Self.withoutFreeGifts(remote.ownedSkins, golden: remote.goldenSkins)
        ownedSkins.formUnion(remoteOwned.union(remote.goldenSkins.keys).filter { Skin.named($0) != nil })
        return before != (goldenPurchases, goldenSkins, ownedSkins)
    }

    /// `merge(_:)` with another whole save.
    @discardableResult
    public mutating func merge(_ remote: SaveGame) -> Bool {
        merge(remote.cloudBackup)
    }

    /// Picks the cat to play as; only an owned one. Returns whether it is now selected.
    @discardableResult
    public mutating func select(skin id: String) -> Bool {
        guard owns(id) else { return false }
        selectedSkin = id
        return true
    }

    /// Records a level finished on its own.
    public mutating func complete(levelID: String, score: Int, xp newXP: Int) {
        xp = max(xp, newXP)
        bestScores[levelID] = max(bestScores[levelID] ?? 0, score)
    }

    /// Records where an endless run stands: `cleared` levels beaten out of a game of `total`. Each
    /// level beaten there becomes playable on its own.
    public mutating func recordEndless(score: Int, cleared: Int, total: Int) {
        unlockedLevels = min(total, max(unlockedLevels, cleared))
        bestEndlessScore = max(bestEndlessScore, score)
        bestEndlessCleared = max(bestEndlessCleared, cleared)
    }
}

public protocol SaveStore {
    func load() -> SaveGame
    func save(_ game: SaveGame)
}

public struct DefaultsSaveStore: SaveStore {
    private let defaults: UserDefaults
    private let key: String

    public init(defaults: UserDefaults = .standard, key: String = "savegame.v1") {
        self.defaults = defaults
        self.key = key
    }

    public func load() -> SaveGame {
        guard let data = defaults.data(forKey: key),
              let game = try? JSONDecoder().decode(SaveGame.self, from: data) else { return SaveGame() }
        return game
    }

    public func save(_ game: SaveGame) {
        guard let data = try? JSONEncoder().encode(game) else { return }
        defaults.set(data, forKey: key)
    }
}
