import Foundation

/// Golden fish: the premium currency, bought with real money as consumable In-App Purchases and spent
/// only on cats (each cat can also be bought with ordinary fish, so every cat stays free to earn).
/// The App Store side lives in the app; here are the packs and the save rules.
public enum GoldenFish {
    /// One pack sold in the store: its App Store product id and the golden fish it gives. Prices
    /// are set in App Store Connect and shown from StoreKit; they are never written in code.
    public struct Pack: Sendable, Equatable, Identifiable {
        public let productID: String
        public let amount: Int
        public var id: String { productID }
    }

    /// Every pack, cheapest first (the shop's order).
    public static let packs: [Pack] = [
        Pack(productID: "com.pryvalov.purrfectlydangerous.golden50", amount: 50),
        Pack(productID: "com.pryvalov.purrfectlydangerous.golden150", amount: 150),
        Pack(productID: "com.pryvalov.purrfectlydangerous.golden350", amount: 350),
        Pack(productID: "com.pryvalov.purrfectlydangerous.golden800", amount: 800),
    ]

    public static var productIDs: [String] { packs.map(\.productID) }

    /// Golden fish given by one purchase of `productID`; nil for a product the game does not sell.
    public static func amount(forProduct productID: String) -> Int? {
        packs.first { $0.productID == productID }?.amount
    }
}

/// The part of a save kept in iCloud so it survives a reinstall or a new phone: the golden fish
/// bought, the cats bought with them, and every cat owned. Each field only ever grows, so two copies
/// that changed apart (two phones, or one offline) merge without conflict by taking the union.
public struct CloudBackup: Codable, Sendable, Equatable {
    /// App Store transaction id → golden fish credited for it.
    public var goldenPurchases: [String: Int] = [:]
    /// Cat id → golden fish paid for it.
    public var goldenSkins: [String: Int] = [:]
    /// Every cat owned, however it was paid for.
    public var ownedSkins: Set<String> = []

    public init(goldenPurchases: [String: Int] = [:], goldenSkins: [String: Int] = [:], ownedSkins: Set<String> = []) {
        self.goldenPurchases = goldenPurchases
        self.goldenSkins = goldenSkins
        self.ownedSkins = ownedSkins
    }

    public init(from decoder: Decoder) throws {
        let values = try decoder.container(keyedBy: CodingKeys.self)
        goldenPurchases = try values.decodeIfPresent([String: Int].self, forKey: .goldenPurchases) ?? [:]
        goldenSkins = try values.decodeIfPresent([String: Int].self, forKey: .goldenSkins) ?? [:]
        ownedSkins = try values.decodeIfPresent(Set<String>.self, forKey: .ownedSkins) ?? []
    }
}
