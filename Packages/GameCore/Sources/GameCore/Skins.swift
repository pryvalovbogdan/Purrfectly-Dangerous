import Foundation

/// A cat the player can play as. Purely cosmetic: a skin never changes the game. Display text lives
/// in Lore.json under `skin.<id>.name` and `skin.<id>.desc`; the hero sprite for it is the artist's.
public struct Skin: Sendable, Equatable, Identifiable {
    public let id: String
    /// Fish from the wallet it costs to unlock; 0 for the cat everyone starts with.
    public let price: Int

    public var nameKey: String { "skin.\(id).name" }
    public var descriptionKey: String { "skin.\(id).desc" }

    /// The cat everyone owns from the start.
    public static let free = "fluffy"

    /// Every cat, in shop order.
    public static let catalog: [Skin] = [
        Skin(id: "fluffy", price: 0), Skin(id: "shadow", price: 150), Skin(id: "misty", price: 200),
        Skin(id: "sakura", price: 250), Skin(id: "honey", price: 300), Skin(id: "pixie", price: 400),
        Skin(id: "clover", price: 500), Skin(id: "snowball", price: 600), Skin(id: "napster", price: 750),
        Skin(id: "toffee", price: 900), Skin(id: "cabage", price: 2000), Skin(id: "sharky", price: 2000),
    ]

    public static func named(_ id: String) -> Skin? {
        catalog.first { $0.id == id }
    }
}

/// What came of trying to unlock a cat.
public enum SkinUnlock: Sendable, Equatable {
    /// Bought: the price was taken from the wallet.
    case unlocked
    /// The wallet is short by `missing` fish; nothing changed.
    case notEnoughFish(missing: Int)
    case alreadyOwned
    case unknownSkin
}
