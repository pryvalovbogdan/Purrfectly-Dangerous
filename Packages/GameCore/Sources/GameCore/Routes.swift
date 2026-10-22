import Foundation

/// Each cat can have its own route of worlds: some level slots replaced by that cat's own levels.
/// The playing order is the normal levels with the selected cat's overrides swapped in. Progress,
/// medals and best scores are kept per level id, so an override is tracked on its own.
///
/// Files: the normal route is every `level_NN.json`; a cat's override for slot NN (1-based) is
/// `route_<skin>_NN.json`, e.g. `route_sakura_01.json` replaces level 1 when Sakura is selected.
public struct RouteBook: Sendable, Equatable {
    /// Skin id → slot (0-based) → the level played there instead.
    public var overrides: [String: [Int: LevelDefinition]]

    public init(overrides: [String: [Int: LevelDefinition]] = [:]) {
        self.overrides = overrides
    }

    /// Whether `skin` has any level of its own.
    public func hasRoute(_ skin: String) -> Bool {
        !(overrides[skin] ?? [:]).isEmpty
    }

    /// The levels to play with `skin` selected: `base` with its overrides swapped in. A cat without
    /// a route, or an override for a slot the game doesn't have, changes nothing.
    public func levels(for skin: String, base: [LevelDefinition]) -> [LevelDefinition] {
        var levels = base
        for (slot, level) in overrides[skin] ?? [:] where levels.indices.contains(slot) {
            levels[slot] = level
        }
        return levels
    }

    /// The cat and 0-based slot of a route file named `route_<skin>_<NN>.json` (NN from 01).
    public static func slot(fromFileName name: String) -> (skin: String, slot: Int)? {
        guard name.hasPrefix("route_"), name.hasSuffix(".json") else { return nil }
        let stem = name.dropFirst("route_".count).dropLast(".json".count)
        guard let split = stem.lastIndex(of: "_"), let number = Int(stem[stem.index(after: split)...]), number >= 1
        else { return nil }
        let skin = String(stem[..<split])
        guard !skin.isEmpty else { return nil }
        return (skin, number - 1)
    }
}

extension ContentLoader {
    /// Every `route_<skin>_<NN>.json` in the bundle.
    public static func routes(in bundle: Bundle) throws -> RouteBook {
        let urls = bundle.urls(forResourcesWithExtension: "json", subdirectory: nil) ?? []
        var overrides: [String: [Int: LevelDefinition]] = [:]
        for url in urls {
            guard let slot = RouteBook.slot(fromFileName: url.lastPathComponent) else { continue }
            overrides[slot.skin, default: [:]][slot.slot] = try level(from: Data(contentsOf: url))
        }
        return RouteBook(overrides: overrides)
    }
}
