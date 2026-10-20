import SwiftUI

/// Chunky logo lettering drawn as pixels: a 5×7 bitmap font, each font cell drawn as 2×2 "sub-pixels"
/// and thickened by one sub-pixel to the right, then a one-sub-pixel dark outline, a lighter highlight
/// along the top of every stroke and a solid drop shadow below. Every sub-pixel is a whole number of
/// device pixels, so the letters are as crisp as the sprites. The words come from Lore.json; this is
/// only the typeface. Letters it has no glyph for fall back to their unaccented form, then to a gap.
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
    /// Device pixels per sub-pixel (a letter is 14 sub-pixels tall, 16 with its outline).
    let sub: Int
    /// The last "O" of the last line is the paw icon, a full letter in size.
    var paw = false
    /// The fish sprite just past the end of the last line, at the bottom.
    var fish = false

    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale

    var body: some View {
        let layout = LogoLayout(lines: lines, paw: paw && model.sprites.sheet("icon_paw") != nil,
                                fish: fish ? model.sprites.sheet("fish").map { (Int($0.width), Int($0.height)) } : nil)
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
                    .offset(x: center.x * unit - sheet.width * pawUnit / 2, y: center.y * unit - sheet.height * pawUnit / 2)
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

    /// Size in sub-pixels of `lines`, and where the first line's middle is (for centring something
    /// over it when the fish makes the block lopsided).
    static func metrics(_ lines: [Line], paw: Bool, fish: (Int, Int)?) -> (width: Int, height: Int, firstLineCenter: CGFloat) {
        let layout = LogoLayout(lines: lines, paw: paw, fish: fish)
        return (layout.width, layout.height, layout.firstLineCenter)
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
    static let glyphHeight = 14
    static let gap = 2
    static let spaceAdvance = 6
    /// The paw's letter: a solid rounded block the paw print is stamped on.
    static let pawBlock = [".###.", "#####", "#####", "#####", "#####", "#####", ".###."]
    /// How wide the paw print is, in sub-pixels (a letter is 11).
    static let pawWidth: CGFloat = 9
    static let linePitch = 17
    static let outline = 1
    static let shadow = 2

    private(set) var width = 0
    private(set) var height = 0
    /// Middle of the paw's letter, in sub-pixels.
    private(set) var pawCenter: CGPoint?
    private(set) var fishOrigin: (x: Int, y: Int)?
    private(set) var firstLineCenter: CGFloat = 0
    /// Fill of each lit sub-pixel: the line's fill and the row within the letter.
    private var lit: [Int: (fill: LogoTitle.Fill, row: Int)] = [:]

    private enum Slot {
        case glyph([String]), space, paw
    }

    init(lines: [LogoTitle.Line], paw: Bool, fish: (Int, Int)?) {
        let pad = Self.outline
        var rows: [(slots: [Slot], width: Int)] = []
        for (index, line) in lines.enumerated() {
            var slots = line.text.map { Self.slot(for: $0) }
            if paw, index == lines.count - 1,
               let at = line.text.lastIndex(of: "O"), at != line.text.startIndex {
                slots[line.text.distance(from: line.text.startIndex, to: at)] = .paw
            }
            let advance = slots.map { slot -> Int in
                switch slot {
                case .glyph: Self.glyphWidth + Self.gap
                case .space: Self.spaceAdvance
                case .paw: Self.glyphWidth + Self.gap
                }
            }.reduce(0, +)
            rows.append((slots, max(0, advance - Self.gap)))
        }
        let lettersWidth = rows.map(\.width).max() ?? 0
        width = lettersWidth + 2 * pad
        height = pad + max(0, rows.count - 1) * Self.linePitch + Self.glyphHeight + pad + Self.shadow

        for (index, row) in rows.enumerated() {
            let fill = lines[index].fill
            let top = pad + index * Self.linePitch
            var x = pad + (lettersWidth - row.width) / 2
            if index == 0 { firstLineCenter = CGFloat(x) + CGFloat(row.width) / 2 }
            for slot in row.slots {
                switch slot {
                case .space:
                    x += Self.spaceAdvance
                case .paw:
                    pawCenter = CGPoint(x: CGFloat(x) + CGFloat(Self.glyphWidth) / 2, y: CGFloat(top) + CGFloat(Self.glyphHeight) / 2)
                    stamp(Self.pawBlock, x: x, top: top, fill: fill)
                    x += Self.glyphWidth + Self.gap
                case .glyph(let bitmap):
                    stamp(bitmap, x: x, top: top, fill: fill)
                    x += Self.glyphWidth + Self.gap
                }
            }
            if index == rows.count - 1, let fish {
                // Just past the end of the line, its bottom on the letters' bottom outline.
                let fishX = x - Self.gap + pad + 1
                let fishY = top + Self.glyphHeight + pad - fish.1
                fishOrigin = (fishX, fishY)
                width = max(width, fishX + fish.0)
            }
        }
    }

    /// Lights a 5×7 glyph: each font cell 2×2 sub-pixels, thickened one sub-pixel to the right.
    private mutating func stamp(_ bitmap: [String], x: Int, top: Int, fill: LogoTitle.Fill) {
        for (cy, bits) in bitmap.enumerated() {
            for (cx, bit) in bits.enumerated() where bit == "#" {
                for dy in 0..<2 {
                    for dx in 0...2 {
                        lit[key(x + 2 * cx + dx, top + 2 * cy + dy)] = (fill, 2 * cy + dy)
                    }
                }
            }
        }
    }

    private func key(_ x: Int, _ y: Int) -> Int { y * 4096 + x }

    private static func slot(for character: Character) -> Slot {
        if character == " " { return .space }
        if let glyph = PixelFont.glyphs[character] { return .glyph(glyph) }
        let plain = String(character).folding(options: [.diacriticInsensitive, .caseInsensitive], locale: nil).uppercased()
        if let first = plain.first, let glyph = PixelFont.glyphs[first] { return .glyph(glyph) }
        return .space
    }

    // MARK: Drawing

    static let ink = Color(red: 0.11, green: 0.08, blue: 0.13)
    static let shadowColor = Color(red: 0.2, green: 0.1, blue: 0.08)

    func draw(in context: GraphicsContext, unit: CGFloat) {
        let litKeys = Set(lit.keys)
        var outline = Set<Int>()
        for k in litKeys {
            let x = k % 4096, y = k / 4096
            for dy in -1...1 {
                for dx in -1...1 { outline.insert(key(x + dx, y + dy)) }
            }
        }
        // Shadow, then outline, then the letters' fill, then the highlight along each stroke's top.
        fill(context, Set(outline.map { $0 + 2 * 4096 }), Self.shadowColor, unit)
        fill(context, outline, Self.ink, unit)
        var byColor: [String: (Color, Set<Int>)] = [:]
        for (k, value) in lit {
            let isTop = !litKeys.contains(k - 4096)
            let color = Self.color(value.fill, row: value.row, highlight: isTop)
            byColor[Self.shade(value.fill, row: value.row, highlight: isTop), default: (color, [])].1.insert(k)
        }
        for (_, entry) in byColor.sorted(by: { $0.key < $1.key }) {
            fill(context, entry.1, entry.0, unit)
        }
    }

    /// Fills the given sub-pixels, merged into horizontal runs.
    private func fill(_ context: GraphicsContext, _ cells: Set<Int>, _ color: Color, _ unit: CGFloat) {
        var path = Path()
        for k in cells.sorted() {
            // Start a run only at its left end.
            if cells.contains(k - 1), (k - 1) / 4096 == k / 4096 { continue }
            var end = k
            while cells.contains(end + 1), (end + 1) / 4096 == k / 4096 { end += 1 }
            let x = CGFloat(k % 4096), y = CGFloat(k / 4096)
            path.addRect(CGRect(x: x * unit, y: y * unit, width: CGFloat(end - k + 1) * unit, height: unit))
        }
        context.fill(path, with: .color(color))
    }

    /// Which of the colours below a sub-pixel gets, as a key for grouping (a title has one flat tint).
    private static func shade(_ fill: LogoTitle.Fill, row: Int, highlight: Bool) -> String {
        let kind: String
        switch fill {
        case .cream: kind = "cream"
        case .gold: kind = "gold"
        case .flat: kind = "flat"
        }
        if highlight { return kind + "-top" }
        switch fill {
        case .cream: return kind + (row < 11 ? "-0" : "-1")
        case .gold: return kind + (row < 4 ? "-0" : row < 8 ? "-1" : row < 11 ? "-2" : "-3")
        case .flat: return kind
        }
    }

    private static func color(_ fill: LogoTitle.Fill, row: Int, highlight: Bool) -> Color {
        switch fill {
        case .cream:
            if highlight { return .white }
            return row < 11 ? Color(red: 1.0, green: 0.95, blue: 0.85) : Color(red: 0.91, green: 0.8, blue: 0.66)
        case .gold:
            if highlight { return Color(red: 1.0, green: 0.97, blue: 0.72) }
            switch row {
            case ..<4: return Color(red: 1.0, green: 0.86, blue: 0.27)
            case ..<8: return Color(red: 1.0, green: 0.72, blue: 0.15)
            case ..<11: return Color(red: 0.97, green: 0.56, blue: 0.09)
            default: return Color(red: 0.87, green: 0.4, blue: 0.05)
            }
        case .flat(let color):
            return highlight ? Color.white : color
        }
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
