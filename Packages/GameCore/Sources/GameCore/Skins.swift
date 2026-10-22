import Foundation

/// A cat the player can play as. Purely cosmetic: a skin never changes the game. Display text lives
/// in Lore.json under `skin.<id>.name` and `skin.<id>.desc`; the hero sprite for it is the artist's.
public struct Skin: Sendable, Equatable, Identifiable {
    public let id: String
    /// Fish from the wallet it costs to unlock; 0 for the cat everyone starts with.
    public let price: Int
    /// Golden fish it costs instead (the premium currency, see `GoldenFish`); nil for the free cat.
    /// Set by hand so it can be tuned; first set as `price` / 20 rounded up to a multiple of 5, at
    /// least 10. Every cat can still be bought with fish alone.
    public let goldenPrice: Int?

    public init(id: String, price: Int, goldenPrice: Int? = nil) {
        self.id = id
        self.price = price
        self.goldenPrice = goldenPrice
    }

    public var nameKey: String { "skin.\(id).name" }
    public var descriptionKey: String { "skin.\(id).desc" }

    /// The cat everyone owns from the start.
    public static let free = "fluffy"

    /// Every cat, in shop order.
    public static let catalog: [Skin] = [
        Skin(id: "fluffy", price: 0),
        Skin(id: "shadow", price: 150, goldenPrice: 10),
        Skin(id: "misty", price: 200, goldenPrice: 10),
        Skin(id: "sakura", price: 250, goldenPrice: 15),
        Skin(id: "honey", price: 300, goldenPrice: 15),
        Skin(id: "pixie", price: 400, goldenPrice: 20),
        Skin(id: "clover", price: 500, goldenPrice: 25),
        Skin(id: "snowball", price: 600, goldenPrice: 30),
        Skin(id: "napster", price: 750, goldenPrice: 40),
        Skin(id: "toffee", price: 900, goldenPrice: 45),
        Skin(id: "cabage", price: 2000, goldenPrice: 100),
        Skin(id: "sharky", price: 2000, goldenPrice: 100),
    ]

    public static func named(_ id: String) -> Skin? {
        catalog.first { $0.id == id }
    }
}

/// What a cat is paid with in the shop.
public enum Currency: String, Sendable, Codable, CaseIterable {
    /// The fish wallet, filled by playing.
    case fish
    /// Golden fish, bought with real money (see `GoldenFish`).
    case golden
}

/// What came of trying to unlock a cat.
public enum SkinUnlock: Sendable, Equatable {
    /// Bought: the price was taken from the wallet (or the golden fish).
    case unlocked
    /// The wallet is short by `missing` fish; nothing changed.
    case notEnoughFish(missing: Int)
    /// The golden fish balance is short by `missing`; nothing changed.
    case notEnoughGoldenFish(missing: Int)
    /// This cat has no golden price (the free one); nothing changed.
    case notForGoldenFish
    case alreadyOwned
    case unknownSkin
}
