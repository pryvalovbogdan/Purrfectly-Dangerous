import SwiftUI

/// Chunky logo lettering drawn as pixels. A 5×7 bitmap font is drawn with every font cell as 2×2
/// "sub-pixels" and thickened by one sub-pixel right and down, so strokes and bars are 3 sub-pixels
/// thick. The letters sit on a solid near-black backing (2 sub-pixels round them, filling the gaps
/// between letters so a word reads as one dark silhouette) with a drop shadow below. Each stroke has
/// a lighter top edge, and each line bends up in a gentle arch towards its middle letters. All of it
/// is in whole sub-pixels, and a sub-pixel is a whole number of device pixels, so the lettering is
/// as crisp as the sprites. The words come from Lore.json; this is only the typeface. Letters it has
/// no glyph for fall back to their unaccented form, then to a gap.
struct LogoTitle: View {
    enum Fill: Equatable {
        /// Cream with a white top edge: the logo's first line.
        case cream
        /// Yellow at the top running to orange at the bottom.
        case gold
        case flat(Color)
    }

    struct Line: Equatable {
        var text: String
        var fill: Fill
    }

    let lines: [Line]
    /// Device pixels per sub-pixel (a letter is 15 sub-pixels tall).
    let sub: Int
    /// The last "O" of the last line is the paw icon on a full-size letter.
    var paw = false
    /// The fish sprite just past the end of the last line, at the bottom.
    var fish = false
    /// Bend each line up towards its middle (logo headings; not numerals).
    var arch = true

    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale

    var body: some View {
        let layout = LogoLayout(lines: lines, paw: paw && model.sprites.sheet("icon_paw") != nil,
                                fish: fish ? model.sprites.sheet("fish").map { (Int($0.width), Int($0.height)) } : nil,
                                arch: arch)
        let unit = CGFloat(sub) / max(displayScale, 1)
        Canvas { context, _ in
            layout.draw(in: context, unit: unit)
        }
        .frame(width: CGFloat(layout.width) * unit, height: CGFloat(layout.height) * unit)
        .overlay(alignment: .topLeading) {
            if let center = layout.pawCenter, let sheet = model.sprites.sheet("icon_paw") {
                // The paw print stamped dark on its gold letter, at a whole-pixel scale.
                let pawScale = max(1, Int((CGFloat(sub) * LogoLayout.pawWidth / sheet.width).rounded()))
                let pawUnit = CGFloat(pawScale) / max(displayScale, 1)
                PixelSprite(sprite: "icon_paw", pixelScale: pawScale)
                    .colorMultiply(Color(red: 0.3, green: 0.16, blue: 0.08))
                    .offset(x: (center.x * unit - sheet.width * pawUnit / 2).rounded(),
                            y: (center.y * unit - sheet.height * pawUnit / 2).rounded())
            }
        }
        .overlay(alignment: .topLeading) {
            if let origin = layout.fishOrigin {
                PixelSprite(sprite: "fish", pixelScale: sub, animated: false)
                    .offset(x: CGFloat(origin.x) * unit, y: CGFloat(origin.y) * unit)
            }
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(lines.map(\.text).joined(separator: " "))
    }

    struct Metrics {
        var width: Int
        var height: Int
        /// Middle of the first line, in sub-pixels from the left.
        var firstLineCenter: CGFloat
        /// How far below the top the first line's highest letter face starts (the backing above it).
        var firstLineTop: Int
    }

    static func metrics(_ lines: [Line], paw: Bool, fish: (Int, Int)?, arch: Bool = true) -> Metrics {
        let layout = LogoLayout(lines: lines, paw: paw, fish: fish, arch: arch)
        return Metrics(width: layout.width, height: layout.height, firstLineCenter: layout.firstLineCenter,
                       firstLineTop: layout.firstLineTop)
    }

    /// The logo's lines: one, or two balanced by word count once there are `splitFrom` words.
    static func lines(_ text: String, splitFrom: Int, allGradient: Bool, tint: Color?) -> [Line] {
        let words = text.uppercased().split(separator: " ")
        let texts: [String]
        if words.count >= splitFrom, words.count > 1 {
            let first = words.count / 2
            texts = [words.prefix(first).joined(separator: " "), words.dropFirst(first).joined(separator: " ")]
        } else {
            texts = [text.uppercased()]
        }
        return texts.enumerated().map { index, line in
            if let tint { return Line(text: line, fill: .flat(tint)) }
            let cream = texts.count > 1 && index == 0 && !allGradient
            return Line(text: line, fill: cream ? .cream : .gold)
        }
    }
}

/// Where every sub-pixel of a logo goes. Coordinates are sub-pixels from the top left.
struct LogoLayout {
    static let glyphWidth = 11
    static let glyphHeight = 15
    static let gap = 2
    static let spaceAdvance = 7
    /// The paw's letter: a solid rounded block the paw print is stamped on.
    static let pawBlock = [".###.", "#####", "#####", "#####", "#####", "#####", ".###."]
    /// How wide the paw print is, in sub-pixels (a letter is 11).
    static let pawWidth: CGFloat = 9
    /// Sub-pixels of near-black backing round every letter.
    static let backing = 2
    static let shadow = 2
    /// Top of one line to the top of the next: the backings of the two lines overlap.
    static let linePitch = 18
    /// How far a line's middle letters rise above its ends: about a tenth of a letter's height.
    static let rise = 2

    private(set) var width = 0
    private(set) var height = 0
    /// Middle of the paw's letter, in sub-pixels.
    private(set) var pawCenter: CGPoint?
    private(set) var fishOrigin: (x: Int, y: Int)?
    private(set) var firstLineCenter: CGFloat = 0
    private(set) var firstLineTop = 0
    /// Fill of each lit sub-pixel: the line's fill and the row within the letter.
    private var lit: [Int: (fill: LogoTitle.Fill, row: Int)] = [:]
    private var backingCells = Set<Int>()

    fileprivate enum Slot {
        case glyph([String]), space, paw
    }

    init(lines: [LogoTitle.Line], paw: Bool, fish: (Int, Int)?, arch: Bool = true) {
        let pad = Self.backing
        let rise = arch ? Self.rise : 0
        var rows: [(slots: [Slot], width: Int)] = []
        for (index, line) in lines.enumerated() {
            var slots = line.text.map { Self.slot(for: $0) }
            if paw, index == lines.count - 1,
               let at = line.text.lastIndex(of: "O"), at != line.text.startIndex {
                slots[line.text.distance(from: line.text.startIndex, to: at)] = .paw
            }
            let advance = slots.map { $0.isSpace ? Self.spaceAdvance : Self.glyphWidth + Self.gap }.reduce(0, +)
            rows.append((slots, max(0, advance - Self.gap)))
        }
        let lettersWidth = rows.map(\.width).max() ?? 0
        width = lettersWidth + 2 * pad
        height = pad + rise + max(0, rows.count - 1) * Self.linePitch + Self.glyphHeight + pad + Self.shadow
        firstLineTop = pad + rise

        for (index, row) in rows.enumerated() {
            let fill = lines[index].fill
            // The ends of the line sit on `base`; letters nearer the middle rise along a parabola.
            let base = pad + rise + index * Self.linePitch
            let left = pad + (lettersWidth - row.width) / 2
            let middle = CGFloat(left) + CGFloat(row.width) / 2
            let half = max(1, CGFloat(row.width - Self.glyphWidth) / 2)
            if index == 0 { firstLineCenter = middle }
            var x = left
            for slot in row.slots {
                if slot.isSpace {
                    x += Self.spaceAdvance
                    continue
                }
                let t = (CGFloat(x) + CGFloat(Self.glyphWidth) / 2 - middle) / half
                let lift = Int((CGFloat(rise) * max(0, 1 - t * t)).rounded())
                let top = base - lift
                if index == 0 { firstLineTop = min(firstLineTop, top) }
                switch slot {
                case .paw:
                    pawCenter = CGPoint(x: CGFloat(x) + CGFloat(Self.glyphWidth) / 2, y: CGFloat(top) + CGFloat(Self.glyphHeight) / 2)
                    stamp(Self.pawBlock, x: x, top: top, fill: fill)
                case .glyph(let bitmap):
                    stamp(bitmap, x: x, top: top, fill: fill)
                case .space:
                    break
                }
                x += Self.glyphWidth + Self.gap
            }
            if index == rows.count - 1, let fish {
                // Just past the end of the line, its bottom on the end letters' bottom.
                let fishX = x - Self.gap + pad + 1
                let fishY = base + Self.glyphHeight + 1 - fish.1
                fishOrigin = (fishX, fishY)
                width = max(width, fishX + fish.0)
            }
        }

        // The backing: every sub-pixel within two of a letter, with the corners of that reach
        // rounded off so the silhouette is chunky rather than square.
        for k in lit.keys {
            let x = k % Self.stride, y = k / Self.stride
            for dy in -pad...pad {
                for dx in -pad...pad where abs(dx) + abs(dy) < 2 * pad {
                    backingCells.insert(key(x + dx, y + dy))
                }
            }
        }
    }

    /// Lights a 5×7 glyph: each font cell 2×2 sub-pixels, thickened one sub-pixel right and down.
    private mutating func stamp(_ bitmap: [String], x: Int, top: Int, fill: LogoTitle.Fill) {
        for (cy, bits) in bitmap.enumerated() {
            for (cx, bit) in bits.enumerated() where bit == "#" {
                for dy in 0...2 {
                    for dx in 0...2 {
                        lit[key(x + 2 * cx + dx, top + 2 * cy + dy)] = (fill, 2 * cy + dy)
                    }
                }
            }
        }
    }

    private static let stride = 4096
    private func key(_ x: Int, _ y: Int) -> Int { y * Self.stride + x }

    private static func slot(for character: Character) -> Slot {
        if character == " " { return .space }
        if let glyph = PixelFont.glyphs[character] { return .glyph(glyph) }
        let plain = String(character).folding(options: [.diacriticInsensitive, .caseInsensitive], locale: nil).uppercased()
        if let first = plain.first, let glyph = PixelFont.glyphs[first] { return .glyph(glyph) }
        return .space
    }

    // MARK: Drawing

    /// Near-black backing (#1a1110) and the drop shadow under it.
    static let ink = Color(red: 0.102, green: 0.067, blue: 0.063)
    static let shadowColor = Color(red: 0.24, green: 0.12, blue: 0.08)

    func draw(in context: GraphicsContext, unit: CGFloat) {
        let litKeys = Set(lit.keys)
        // Shadow, then backing, then the letters' fill, then the highlight along each stroke's top.
        fill(context, Set(backingCells.map { $0 + Self.shadow * Self.stride }), Self.shadowColor, unit)
        fill(context, backingCells, Self.ink, unit)
        var byShade: [String: (Color, Set<Int>)] = [:]
        for (k, value) in lit {
            let isTop = !litKeys.contains(k - Self.stride)
            let color = Self.color(value.fill, row: value.row, highlight: isTop)
            byShade[Self.shade(value.fill, row: value.row, highlight: isTop), default: (color, [])].1.insert(k)
        }
        for (_, entry) in byShade.sorted(by: { $0.key < $1.key }) {
            fill(context, entry.1, entry.0, unit)
        }
    }

    /// Fills the given sub-pixels, merged into horizontal runs.
    private func fill(_ context: GraphicsContext, _ cells: Set<Int>, _ color: Color, _ unit: CGFloat) {
        var path = Path()
        for k in cells.sorted() {
            // Start a run only at its left end.
            if cells.contains(k - 1), (k - 1) / Self.stride == k / Self.stride { continue }
            var end = k
            while cells.contains(end + 1), (end + 1) / Self.stride == k / Self.stride { end += 1 }
            let x = CGFloat(k % Self.stride), y = CGFloat(k / Self.stride)
            path.addRect(CGRect(x: x * unit, y: y * unit, width: CGFloat(end - k + 1) * unit, height: unit))
        }
        context.fill(path, with: .color(color))
    }

    /// Which colour a sub-pixel gets, as a key for grouping (a title has one flat tint).
    private static func shade(_ fill: LogoTitle.Fill, row: Int, highlight: Bool) -> String {
        let kind: String
        switch fill {
        case .cream: kind = "cream"
        case .gold: kind = "gold"
        case .flat: kind = "flat"
        }
        if highlight { return kind + "-top" }
        switch fill {
        case .cream: return kind + (row < 12 ? "-0" : "-1")
        case .gold: return kind + (row < 4 ? "-0" : row < 8 ? "-1" : row < 12 ? "-2" : "-3")
        case .flat: return kind
        }
    }

    private static func color(_ fill: LogoTitle.Fill, row: Int, highlight: Bool) -> Color {
        switch fill {
        case .cream:
            if highlight { return .white }
            return row < 12 ? Color(red: 1.0, green: 0.95, blue: 0.85) : Color(red: 0.91, green: 0.8, blue: 0.66)
        case .gold:
            if highlight { return Color(red: 1.0, green: 0.97, blue: 0.72) }
            switch row {
            case ..<4: return Color(red: 1.0, green: 0.86, blue: 0.27)
            case ..<8: return Color(red: 1.0, green: 0.72, blue: 0.15)
            case ..<12: return Color(red: 0.97, green: 0.56, blue: 0.09)
            default: return Color(red: 0.87, green: 0.4, blue: 0.05)
            }
        case .flat(let color):
            return highlight ? Color.white : color
        }
    }
}

private extension LogoLayout.Slot {
    var isSpace: Bool {
        if case .space = self { return true }
        return false
    }
}

/// A blocky 5×7 capital font: digits, A–Z and the punctuation titles use.
enum PixelFont {
    static let glyphs: [Character: [String]] = [
        "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
        "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
        "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
        "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
        "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
        "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
        "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"],
        "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
        "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
        "J": ["..###", "...#.", "...#.", "...#.", "#..#.", "#..#.", ".##.."],
        "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
        "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
        "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
        "N": ["#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"],
        "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
        "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
        "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
        "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
        "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
        "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
        "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
        "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
        "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
        "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
        "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
        "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
        "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
        "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
        "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
        "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
        "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
        "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
        "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
        "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
        "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
        "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
        "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
        "?": [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."],
        ".": [".....", ".....", ".....", ".....", ".....", ".....", "..#.."],
        ",": [".....", ".....", ".....", ".....", ".....", "..#..", ".#..."],
        "'": ["..#..", "..#..", ".....", ".....", ".....", ".....", "....."],
        "’": ["..#..", "..#..", ".....", ".....", ".....", ".....", "....."],
        ":": [".....", "..#..", ".....", ".....", ".....", "..#..", "....."],
        "-": [".....", ".....", ".....", ".###.", ".....", ".....", "....."],
        "—": [".....", ".....", ".....", "#####", ".....", ".....", "....."],
        "/": ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
        "×": [".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "....."],
        "&": [".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"],
    ]
}
