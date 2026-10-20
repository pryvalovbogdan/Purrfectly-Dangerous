import Foundation

/// The height of the ground along a level: base ground at 0, raised blocks and dips from the level's
/// `terrain`. Ravines are not part of it (they are holes in the base ground; see `RunnerWorld`).
public struct GroundProfile: Sendable, Equatable {
    /// The level's terrain pieces, sorted by `at`.
    public let pieces: [Terrain]
    /// Every x where the height may change (both ends of every piece), sorted and without repeats.
    public let edges: [Double]

    /// Slack for floating-point positions resting exactly on an edge.
    static let epsilon = 1e-6

    public init(_ terrain: [Terrain]) {
        pieces = terrain.filter { $0.width > 0 }.sorted { $0.at < $1.at }
        var edges: [Double] = []
        for piece in pieces {
            for x in [piece.at, piece.end] where edges.last != x { edges.append(x) }
        }
        self.edges = edges.sorted()
    }

    public var isFlat: Bool { pieces.isEmpty }

    /// Height of the ground at `x`. On a seam between two pieces the right-hand one counts.
    public func height(at x: Double) -> Double {
        pieces.first { $0.contains(x) }?.height ?? 0
    }

    /// Height of the ground just left of `x` (what a seam looks like from the left).
    public func height(leftOf x: Double) -> Double {
        pieces.first { $0.at < x && $0.end >= x }?.height ?? 0
    }

    /// The highest ground under the span `lo...hi` (open at both ends, so a box resting against a
    /// face does not stand on it).
    public func highest(from lo: Double, to hi: Double) -> Double {
        var top = -Double.infinity
        var covered = lo + Self.epsilon
        for piece in pieces where piece.at < hi - Self.epsilon && piece.end > lo + Self.epsilon {
            top = max(top, piece.height)
            // Any stretch of base ground between pieces counts as 0.
            if piece.at > covered { top = max(top, 0) }
            covered = max(covered, piece.end)
        }
        if covered < hi - Self.epsilon { top = max(top, 0) }
        return top
    }

    /// Lowest ground under the span `lo...hi` (open at both ends).
    public func lowest(from lo: Double, to hi: Double) -> Double {
        var bottom = Double.infinity
        var covered = lo + Self.epsilon
        for piece in pieces where piece.at < hi - Self.epsilon && piece.end > lo + Self.epsilon {
            bottom = min(bottom, piece.height)
            if piece.at > covered { bottom = min(bottom, 0) }
            covered = max(covered, piece.end)
        }
        if covered < hi - Self.epsilon { bottom = min(bottom, 0) }
        return bottom
    }

    /// True when the height changes somewhere strictly inside `lo...hi`.
    public func changes(from lo: Double, to hi: Double) -> Bool {
        highest(from: lo, to: hi) != lowest(from: lo, to: hi)
    }

    /// Moving right with the leading edge going from `front` to `target`: the first face that is
    /// more than `step` above `feet`, as the x of the face. Nil when the way is clear.
    public func wall(from front: Double, to target: Double, feet: Double, step: Double) -> Double? {
        for edge in edges where edge >= front - Self.epsilon && edge <= target {
            if height(at: edge) > feet + step, height(at: edge) > height(leftOf: edge) { return edge }
        }
        return nil
    }

    /// The first seam between `x` and `front` (in either direction, `front` included) where the
    /// ground on the far side is not at `level`. Walkers turn back there.
    public func step(from x: Double, to front: Double, level: Double) -> Double? {
        if front < x {
            for edge in edges.reversed() where edge <= x + Self.epsilon && edge >= front {
                if abs(height(leftOf: edge) - level) > Self.epsilon { return edge }
            }
        } else {
            for edge in edges where edge >= x - Self.epsilon && edge <= front {
                if abs(height(at: edge) - level) > Self.epsilon { return edge }
            }
        }
        return nil
    }

    /// Every rise the hero meets running right: where the ground steps up by more than `step`.
    /// `rise` is how far the ground climbs there.
    public func rises(step: Double) -> [(at: Double, rise: Double)] {
        edges.compactMap { edge in
            let rise = height(at: edge) - height(leftOf: edge)
            return rise > step ? (edge, rise) : nil
        }
    }
}
