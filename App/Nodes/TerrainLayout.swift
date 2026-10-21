import Foundation
import GameCore

/// Where every terrain sprite goes, worked out without SpriteKit so the same code can be checked
/// offline (a script compiles this file and composites the real PNGs from its output).
///
/// Touching pieces of the same kind (all raised, or all sunken) form one **run**, drawn as one solid
/// mass over a height profile:
/// - earth fill on one grid for the whole run, from G − 48 up to each column's surface, clipped to the
///   run's outline by a mask (no seams between pieces);
/// - top tiles along each flat stretch: inset under a cap on its own higher side, run on under the face
///   of a higher neighbour, so there are no gaps and no doubled outlines;
/// - a face only where one is exposed: an end cap with its top on the higher surface over walls tiled
///   up from the lower surface. At the outer ends of a raised run that is down to the base ground; at a
///   step inside a run only the part between the two surfaces. A dip's outer faces belong to the base
///   ground around it, a step between a raised run and a dip to the raised side.
///
/// Units: x in world units relative to `Run.origin`, y relative to the ground line G (up positive).
enum TerrainLayout {
    enum Role: String {
        case top, fill, edge, wall
    }

    struct Sprite: Equatable {
        var role: Role
        /// Left edge of the frame as drawn (a mirrored sprite still covers [x, x + width)).
        var x: Double
        /// Bottom of the frame.
        var y: Double
        var mirrored = false
        /// Order inside the run: fill 0, walls 2, caps 3, tops 4. Tops go in front so the lower stretch's
        /// grass runs over the foot of a step shorter than a cap (only tiles shorter than their stretch
        /// ever overlap a cap otherwise).
        var z: Double
    }

    struct Rect: Equatable {
        var x, y, width, height: Double
    }

    struct Run {
        /// World x the run's node stands at; every x inside is relative to it.
        var origin: Double
        /// Span from `origin` that holds everything drawn, for culling.
        var width: Double
        var isDip: Bool
        /// Fill tiles, drawn through `mask` (the run's outline under its top tiles).
        var fills: [Sprite]
        var mask: [Rect]
        /// Tops, walls and caps, drawn as they are.
        var sprites: [Sprite]
    }

    struct Sizes {
        var top: (width: Double, height: Double)
        var fill: (width: Double, height: Double)?
        var edge: (width: Double, height: Double)?
        var wall: (width: Double, height: Double)?
    }

    /// Where the fill starts: the bottom of the ground strip's tile, so the grids line up.
    static let fillBase = -48.0

    /// Left edges of whole tiles covering `span`: side by side, the last one pulled back so the row
    /// ends flush with the span (a span shorter than a tile gets one tile centred on it).
    static func tileOffsets(span: Double, tile: Double) -> [Double] {
        guard span > tile else { return [(span - tile) / 2] }
        let count = Int((span / tile).rounded(.up))
        return (0..<count).map { min(Double($0) * tile, span - tile).rounded() }
    }

    static func runs(_ ground: GroundProfile, sizes: Sizes) -> [Run] {
        // Group touching pieces of the same sign.
        var groups: [[Terrain]] = []
        for piece in ground.pieces where piece.height != 0 {
            if let last = groups.last?.last, last.end == piece.at, (last.height < 0) == (piece.height < 0) {
                groups[groups.count - 1].append(piece)
            } else {
                groups.append([piece])
            }
        }
        return groups.map { run(of: $0, ground: ground, sizes: sizes) }
    }

    private static func run(of pieces: [Terrain], ground: GroundProfile, sizes: Sizes) -> Run {
        let start = pieces[0].at, end = pieces[pieces.count - 1].end
        let isDip = pieces[0].height < 0
        // Flat stretches: neighbouring pieces of one height count as one.
        var stretches: [(from: Double, to: Double, height: Double)] = []
        for piece in pieces {
            if let last = stretches.last, last.height == piece.height, last.to == piece.at {
                stretches[stretches.count - 1].to = piece.end
            } else {
                stretches.append((piece.at, piece.end, piece.height))
            }
        }
        let outerLeft = ground.height(leftOf: start), outerRight = ground.height(at: end)
        let cap = sizes.edge?.width ?? 0
        let margin = max(cap, 8) + 8
        let origin = (start - margin).rounded(.down)
        func local(_ x: Double) -> Double { x - origin }

        var sprites: [Sprite] = []
        var mask: [Rect] = []
        var fillFrom = Double.infinity, fillTo = -Double.infinity, top = -Double.infinity
        for (index, stretch) in stretches.enumerated() {
            let leftHeight = index == 0 ? outerLeft : stretches[index - 1].height
            let rightHeight = index == stretches.count - 1 ? outerRight : stretches[index + 1].height
            let leftIsBase = index == 0 && !ground.pieces.contains { $0.end == start }
            let rightIsBase = index == stretches.count - 1 && !ground.pieces.contains { $0.at == end }
            /// How far the top and fill reach past this side: in under its own cap (negative), on under
            /// a higher neighbour's face (8; 1 into the base ground's face around a dip), else flush.
            func reach(neighbour: Double, isBase: Bool) -> Double {
                guard cap > 0, neighbour != stretch.height else { return 0 }
                if neighbour < stretch.height { return -cap }
                return isDip && isBase ? 1 : 8
            }
            let from = stretch.from - reach(neighbour: leftHeight, isBase: leftIsBase)
            let to = stretch.to + reach(neighbour: rightHeight, isBase: rightIsBase)
            for x in tileOffsets(span: to - from, tile: sizes.top.width) {
                sprites.append(Sprite(role: .top, x: local(from + x), y: stretch.height - sizes.top.height, z: 4))
            }
            if to > from {
                mask.append(Rect(x: local(from), y: fillBase, width: to - from, height: stretch.height - fillBase))
                fillFrom = min(fillFrom, from)
                fillTo = max(fillTo, to)
            }
            top = max(top, stretch.height)
        }

        // One fill for the whole run, on a grid fixed to the world so neighbouring runs match too.
        var fills: [Sprite] = []
        if let fill = sizes.fill, fillTo > fillFrom {
            var x = (fillFrom / fill.width).rounded(.down) * fill.width
            while x < fillTo {
                var y = fillBase
                while y < top {
                    fills.append(Sprite(role: .fill, x: local(x), y: y, z: 0))
                    y += fill.height
                }
                x += fill.width
            }
        }

        // Faces at every seam this run owns: the higher side's, or the base ground's around a dip.
        if let edge = sizes.edge {
            var seams: [(x: Double, left: Double, right: Double)] = [(start, outerLeft, stretches[0].height)]
            for index in stretches.indices.dropFirst() {
                seams.append((stretches[index].from, stretches[index - 1].height, stretches[index].height))
            }
            seams.append((end, stretches[stretches.count - 1].height, outerRight))
            for (index, seam) in seams.enumerated() {
                let outer = index == 0 || index == seams.count - 1
                let higherIsOutside = outer && (index == 0 ? seam.left > seam.right : seam.right > seam.left)
                // An outer face of a higher neighbour belongs to it, unless that neighbour is the base ground.
                if higherIsOutside, max(seam.left, seam.right) != 0 { continue }
                let facesLeft = seam.right > seam.left
                let high = max(seam.left, seam.right), low = min(seam.left, seam.right)
                let x = facesLeft ? seam.x : seam.x - edge.width
                sprites.append(Sprite(role: .edge, x: local(x), y: high - edge.height, mirrored: !facesLeft, z: 3))
                if let wall = sizes.wall {
                    var bottom = low
                    while bottom < high - edge.height {
                        sprites.append(Sprite(role: .wall, x: local(x), y: bottom, mirrored: !facesLeft, z: 2))
                        bottom += wall.height
                    }
                }
            }
        }
        return Run(origin: origin, width: end + margin - origin, isDip: isDip, fills: fills, mask: mask,
                   sprites: sprites)
    }
}
