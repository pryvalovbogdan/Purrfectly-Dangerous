import GameCore
import SpriteKit
import SwiftUI

/// The look shared by the start, level-complete, game-over, next-level, levels and cats screens:
/// chunky pixel buttons, the parchment card, the outlined logo lettering and pixel sprites drawn at
/// whole-number scale with nearest-neighbour filtering. Decoration only; no game rules here.

extension Color {
    static let menuInk = Color(red: 0.11, green: 0.08, blue: 0.13)
    static let menuPaper = Color(red: 0.96, green: 0.96, blue: 0.94)
    /// The next-level card and its label ink.
    static let cardFill = Color(red: 0.85, green: 0.75, blue: 0.54)
    static let cardInk = Color(red: 0.62, green: 0.42, blue: 0.1)
    /// Cream of the secondary buttons and the logo's first line.
    static let menuCream = Color(red: 1.0, green: 0.95, blue: 0.84)
    static let menuOrange = Color(red: 0.97, green: 0.52, blue: 0.09)
    static let menuOrangeDeep = Color(red: 0.86, green: 0.38, blue: 0.05)
    static let menuYellow = Color(red: 1.0, green: 0.84, blue: 0.26)
    /// The parchment score card, its inner edge and its lettering.
    static let parchment = Color(red: 0.99, green: 0.93, blue: 0.8)
    static let parchmentEdge = Color(red: 0.84, green: 0.68, blue: 0.45)
    static let parchmentInk = Color(red: 0.24, green: 0.16, blue: 0.12)
    static let badgeRed = Color(red: 0.89, green: 0.16, blue: 0.2)
}

// MARK: - Backdrop

/// The scene behind the menu and the end screens, rebuilt whenever the screen changes shape.
struct MenuBackground: View {
    var pose = MenuScene.Pose.running
    /// A level's background theme; nil for the menu's own morning.
    var theme: String?
    var celebrate = false
    var groundShare = MenuScene.narrowGroundShare
    var wideHeroPlace: CGFloat?
    /// Show the chosen cat's own start screen (`StartLook`) when it has one (the start screen only).
    var followsCat = false

    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale
    @State private var scene: MenuScene?

    var body: some View {
        GeometryReader { proxy in
            ZStack {
                Color(red: 0.44, green: 0.71, blue: 0.88)
                if let scene {
                    // Only the running scene scrolls; at rest half the frame rate is plenty.
                    SpriteView(scene: scene, preferredFramesPerSecond: pose == .running || celebrate ? 60 : 30)
                        // SpriteView keeps presenting its first scene when handed a new one, so a rebuilt
                        // scene (another cat picked, a rotation) needs a new view.
                        .id(ObjectIdentifier(scene))
                }
            }
            .onAppear { scene = makeScene(proxy.size) }
            .onChange(of: proxy.size) { _, newSize in scene = makeScene(newSize) }
            // A cat picked on the CATS screen shows here as soon as the player comes back.
            .onChange(of: model.heroSprite) { _, _ in scene = makeScene(proxy.size) }
            .onChange(of: startLook) { _, _ in scene = makeScene(proxy.size) }
        }
        .ignoresSafeArea()
    }

    private func makeScene(_ size: CGSize) -> MenuScene {
        MenuScene(viewSize: size, displayScale: displayScale, library: model.sprites, pose: pose, theme: theme,
                  celebrate: celebrate, groundShare: groundShare, wideHeroPlace: wideHeroPlace,
                  heroSprite: model.heroSprite, startLook: startLook)
    }

    private var startLook: String? {
        followsCat ? StartLook.theme(forSkin: model.selectedSkin) : nil
    }
}

/// Screen-filling layout helper: hands its content the whole screen's size and the safe-area insets,
/// and lays the content out over the whole screen (origin at the screen's top left).
///
/// The reader itself stays inside the safe area: a GeometryReader that ignores the safe area reports
/// zero insets, which put the start screen's title under the Dynamic Island.
struct ScreenFrame<Content: View>: View {
    @ViewBuilder let content: (CGSize, EdgeInsets) -> Content

    var body: some View {
        GeometryReader { proxy in
            let insets = proxy.safeAreaInsets
            let full = CGSize(width: proxy.size.width + insets.leading + insets.trailing,
                              height: proxy.size.height + insets.top + insets.bottom)
            content(full, insets)
                .frame(width: full.width, height: full.height)
                .offset(x: -insets.leading, y: -insets.top)
        }
    }
}

// MARK: - Pixel sprites

extension SpriteLibrary {
    /// The largest whole number of device pixels per sprite pixel at which `sprite` fits in `box`
    /// (points); at least 1.
    func pixelScale(_ sprite: String, fitting box: CGSize, displayScale: CGFloat) -> Int {
        guard let sheet = sheet(sprite), sheet.width > 0, sheet.height > 0 else { return 1 }
        let scale = min(box.width * displayScale / sheet.width, box.height * displayScale / sheet.height)
        return max(1, Int(scale.rounded(.down)))
    }
}

/// A generated sprite in SwiftUI at a whole number of device pixels per sprite pixel, kept crisp,
/// animated from its manifest entry. Leaves nothing behind if the sprite is not in the manifest yet.
struct PixelSprite: View {
    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale
    let sprite: String
    /// Animations to try in order; the first the sprite has is played.
    var animations = ["still"]
    /// Device pixels per sprite pixel.
    var pixelScale = 1
    /// Fall back to the sprite's first animation when none of `animations` exists (props and icons).
    /// Characters pass false so a missing pose is left out rather than replaced by a random one.
    var anyAnimation = true
    var animated = true
    var flipped = false
    /// A sprite to play the animation from when `sprite` lacks all of `animations` (a recoloured
    /// hero falls back to `hero`).
    var fallback: String?
    @State private var start = Date()

    private var resolved: (sprite: String, name: String, info: SpriteLibrary.Animation, sheet: SpriteLibrary.Sheet)? {
        let library = model.sprites
        if let fallback, fallback != sprite, library.sheet(fallback) != nil,
           !animations.contains(where: { library.animation(sprite, $0) != nil }),
           let name = animations.first(where: { library.animation(fallback, $0) != nil }),
           let info = library.animation(fallback, name), let sheet = library.sheet(fallback) {
            return (fallback, name, info, sheet)
        }
        guard let sheet = library.sheet(sprite) else { return nil }
        let name = animations.first { library.animation(sprite, $0) != nil }
            ?? (anyAnimation ? library.animationName(sprite, preferring: animations.first ?? "still") : nil)
        guard let name, let info = library.animation(sprite, name) else { return nil }
        return (sprite, name, info, sheet)
    }

    var body: some View {
        if let resolved {
            let frames = model.sprites.images(resolved.sprite, resolved.name)
            let unit = CGFloat(pixelScale) / max(displayScale, 1)
            if !frames.isEmpty {
                Group {
                    if animated, frames.count > 1 {
                        TimelineView(.periodic(from: start, by: 1 / max(resolved.info.fps, 1))) { context in
                            let elapsed = context.date.timeIntervalSince(start)
                            let step = Int(elapsed * resolved.info.fps)
                            let index = resolved.info.loop ? step % frames.count : min(step, frames.count - 1)
                            frame(frames[max(0, index)])
                        }
                    } else {
                        frame(frames[0])
                    }
                }
                .frame(width: resolved.sheet.width * unit, height: resolved.sheet.height * unit)
                .scaleEffect(x: flipped ? -1 : 1)
                .accessibilityHidden(true)
            }
        }
    }

    private func frame(_ image: CGImage) -> some View {
        Image(decorative: image, scale: 1).interpolation(.none).resizable()
    }
}

/// One frame of a generated sprite as a SwiftUI image stretched to whatever frame it is given (the
/// in-game HUD sizes these itself).
struct SpriteImage: View {
    @Environment(AppModel.self) private var model
    let sprite: String
    let animation: String

    var body: some View {
        if let image = model.sprites.images(sprite, animation).first {
            Image(decorative: image, scale: 1).interpolation(.none).resizable()
        }
    }
}

/// A sprite icon about `height` points tall, at whole-pixel scale.
struct PixelIcon: View {
    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale
    let sprite: String
    var height: CGFloat = 22

    var body: some View {
        let sheetHeight = model.sprites.sheet(sprite)?.height ?? 16
        let scale = max(1, Int((height * displayScale / sheetHeight).rounded()))
        PixelSprite(sprite: sprite, pixelScale: scale)
    }
}

// MARK: - Shapes

/// A rectangle with stepped, pixel-art corners (two steps of `step` points).
struct PixelRect: InsettableShape {
    var step: CGFloat = 3
    var insetAmount: CGFloat = 0

    func path(in rect: CGRect) -> Path {
        let r = rect.insetBy(dx: insetAmount, dy: insetAmount)
        let s = min(step, r.width / 4, r.height / 4)
        let (x0, y0, x1, y1) = (r.minX, r.minY, r.maxX, r.maxY)
        var path = Path()
        path.addLines([
            CGPoint(x: x0 + 2 * s, y: y0), CGPoint(x: x1 - 2 * s, y: y0), CGPoint(x: x1 - 2 * s, y: y0 + s),
            CGPoint(x: x1 - s, y: y0 + s), CGPoint(x: x1 - s, y: y0 + 2 * s), CGPoint(x: x1, y: y0 + 2 * s),
            CGPoint(x: x1, y: y1 - 2 * s), CGPoint(x: x1 - s, y: y1 - 2 * s), CGPoint(x: x1 - s, y: y1 - s),
            CGPoint(x: x1 - 2 * s, y: y1 - s), CGPoint(x: x1 - 2 * s, y: y1), CGPoint(x: x0 + 2 * s, y: y1),
            CGPoint(x: x0 + 2 * s, y: y1 - s), CGPoint(x: x0 + s, y: y1 - s), CGPoint(x: x0 + s, y: y1 - 2 * s),
            CGPoint(x: x0, y: y1 - 2 * s), CGPoint(x: x0, y: y0 + 2 * s), CGPoint(x: x0 + s, y: y0 + 2 * s),
            CGPoint(x: x0 + s, y: y0 + s), CGPoint(x: x0 + 2 * s, y: y0 + s),
        ])
        path.closeSubpath()
        return path
    }

    func inset(by amount: CGFloat) -> PixelRect {
        var shape = self
        shape.insetAmount += amount
        return shape
    }
}

/// The dotted line between a label and its number on the score card.
struct DottedLeader: View {
    var color = Color.parchmentInk.opacity(0.35)

    var body: some View {
        Line()
            .stroke(color, style: StrokeStyle(lineWidth: 2, dash: [2, 4]))
            .frame(height: 2)
            .frame(minWidth: 12)
    }

    private struct Line: Shape {
        func path(in rect: CGRect) -> Path {
            Path { path in
                path.move(to: CGPoint(x: rect.minX, y: rect.midY))
                path.addLine(to: CGPoint(x: rect.maxX, y: rect.midY))
            }
        }
    }
}

// MARK: - Lettering

/// Text with a thick dark outline (and optionally a drop shadow), in any fill.
struct OutlinedText: View {
    let text: String
    let size: CGFloat
    var fill: AnyShapeStyle = AnyShapeStyle(Color.menuPaper)
    var shadow = false

    private static let outline: [CGSize] = [-1, 0, 1].flatMap { x in [-1, 0, 1].map { CGSize(width: x, height: $0) } }
        + [CGSize(width: 0, height: 2), CGSize(width: -1, height: 2), CGSize(width: 1, height: 2)]

    /// Outline thickness, in step with the lettering so small text is not swamped by it.
    private var weight: CGFloat { max(1.5, size * 0.075) }

    var body: some View {
        ZStack {
            if shadow {
                Text(text).foregroundStyle(Color.black.opacity(0.35))
                    .offset(x: weight, y: weight * 4)
            }
            ForEach(Self.outline.indices, id: \.self) { index in
                Text(text)
                    .foregroundStyle(Color.menuInk)
                    .offset(x: Self.outline[index].width * weight, y: Self.outline[index].height * weight)
            }
            Text(text).foregroundStyle(fill)
        }
        .font(.pixel(size))
        .lineLimit(1)
        .fixedSize()
    }
}

/// A heading in the chunky pixel lettering (see `LogoTitle`): the first of two lines cream, the rest
/// yellow-to-orange, or one flat `tint` for numerals. `size` is roughly the height of one line in
/// points; a heading too wide for its space steps down whole pixels until it fits.
struct PixelTitle: View {
    let text: String
    let size: CGFloat
    var alignment = HorizontalAlignment.leading
    var tint: Color?
    /// Text with at least this many words is set on two lines.
    var splitFrom = 3

    @Environment(\.displayScale) private var displayScale

    var body: some View {
        let lines = LogoTitle.lines(text, splitFrom: splitFrom, tint: tint)
        let preferred = max(1, Int((size * displayScale / 16).rounded()))
        ViewThatFits(in: .horizontal) {
            ForEach(Array((1...preferred).reversed()), id: \.self) { sub in
                // Numerals stay straight; headings bend like the logo.
                LogoTitle(lines: lines, sub: sub, arch: tint == nil)
            }
        }
        .accessibilityAddTraits(.isHeader)
    }
}

extension SpriteLibrary {
    /// The box (sprite pixels, top-left origin) holding every opaque pixel of an animation's frames,
    /// so a figure can be placed by what is drawn rather than by its padded frame.
    @MainActor
    func opaqueBounds(_ sprite: String, _ animation: String) -> CGRect? {
        let key = "\(sprite)/\(animation)"
        if let cached = OpaqueBoundsCache.values[key] { return cached }
        var union: CGRect?
        for image in images(sprite, animation) {
            guard var box = Self.opaqueBox(image) else { continue }
            // Painted heroes ship 3x images; measure in sprite pixels like the 1x ones.
            if let width = sheet(sprite)?.width, width > 0, CGFloat(image.width) != width {
                let scale = CGFloat(image.width) / width
                box = CGRect(x: box.minX / scale, y: box.minY / scale, width: box.width / scale, height: box.height / scale)
            }
            union = union.map { $0.union(box) } ?? box
        }
        OpaqueBoundsCache.values[key] = union
        return union
    }

    private static func opaqueBox(_ image: CGImage) -> CGRect? {
        let width = image.width, height = image.height
        var pixels = [UInt8](repeating: 0, count: width * height * 4)
        let drawn: Bool = pixels.withUnsafeMutableBytes { buffer in
            guard let context = CGContext(data: buffer.baseAddress, width: width, height: height, bitsPerComponent: 8,
                                          bytesPerRow: width * 4, space: CGColorSpaceCreateDeviceRGB(),
                                          bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) else { return false }
            context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
            return true
        }
        guard drawn else { return nil }
        var minX = width, minY = height, maxX = -1, maxY = -1
        // Bitmap rows run top to bottom in memory.
        for y in 0..<height {
            for x in 0..<width where pixels[(y * width + x) * 4 + 3] > 0 {
                minX = min(minX, x); maxX = max(maxX, x)
                minY = min(minY, y); maxY = max(maxY, y)
            }
        }
        guard maxX >= 0 else { return nil }
        return CGRect(x: minX, y: minY, width: maxX - minX + 1, height: maxY - minY + 1)
    }
}

@MainActor
private enum OpaqueBoundsCache {
    static var values: [String: CGRect?] = [:]
}

/// A figure that can sit on a title: a sprite animation, how much of its drawn height is head, and
/// how tall that head should be against the title.
struct TitleFigure {
    let sprite: String
    let animation: String
    /// Share of the drawn (opaque) height that is the head.
    var headShare: CGFloat = 0.9
    /// Head height as a share of the title's height.
    var headOfTitle: CGFloat = 0.5

    // The painted heroes stand on all fours with the tail up, so the head is about 60% of what is drawn.
    static let cheer = TitleFigure(sprite: "hero", animation: "cheer", headShare: 0.6, headOfTitle: 0.5)
    static let idle = TitleFigure(sprite: "hero", animation: "idle", headShare: 0.6, headOfTitle: 0.5)

    /// The same figure drawn from another sprite (the recoloured hero of the cat in use).
    func drawn(from sprite: String) -> TitleFigure {
        TitleFigure(sprite: sprite, animation: animation, headShare: headShare, headOfTitle: headOfTitle)
    }
}

/// A logo-style heading in the pixel lettering (the level-complete title): the hero standing behind
/// it, optionally a sunburst behind the hero and a fish just past the last line, and a wreath sprite
/// framing the letters from behind. The letters take the whole-pixel size nearest `width` that fits
/// `maxHeight` with the hero included; the hero is scaled (whole pixels) so its head is its chosen
/// share of the title. Missing sprites are left out.
struct WreathTitle: View {
    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale
    let text: String
    var wreath = "title_wreath_small"
    let width: CGFloat
    let maxHeight: CGFloat
    /// The figure over the title: the first of these that is drawn; empty for none.
    var topper: [TitleFigure] = []
    /// Share of the figure's drawn height that stands behind the letters. 0: it rests on top of them
    /// (paws on the outline) and never covers a letter.
    var topperSink: CGFloat = 0
    var sunburst = false
    var fish = false
    var splitFrom = 2

    private var library: SpriteLibrary { model.sprites }

    private struct Figure {
        let choice: TitleFigure
        let animation: String
        let bounds: CGRect
        let sheet: SpriteLibrary.Sheet
    }

    private var figure: Figure? {
        guard let choice = topper.first(where: { library.animation($0.sprite, $0.animation) != nil }),
              let sheet = library.sheet(choice.sprite),
              let bounds = library.opaqueBounds(choice.sprite, choice.animation) else { return nil }
        return Figure(choice: choice, animation: choice.animation, bounds: bounds, sheet: sheet)
    }

    /// Whole-pixel scale of the figure for a title `titleHeight` sub-pixels tall at `sub`: its head
    /// the figure's chosen share of the title's height.
    private func figureScale(_ figure: Figure?, sub: Int, titleHeight: Int) -> Int {
        guard let figure else { return 1 }
        let head = max(8, figure.bounds.height * figure.choice.headShare)
        return max(1, Int((CGFloat(titleHeight * sub) * figure.choice.headOfTitle / head).rounded()))
    }

    var body: some View {
        let scale = max(displayScale, 1)
        let lines = LogoTitle.lines(text, splitFrom: splitFrom, tint: nil)
        let fishSize = fish ? library.sheet("fish").map { (Int($0.width), Int($0.height)) } : nil
        let metrics = LogoTitle.metrics(lines, fish: fishSize)
        let figure = figure
        // Whole device pixels per sub-pixel make the sizes coarse steps, so take the one nearest the
        // width asked for (never more than 6% over it) whose height, figure included, fits.
        let fits: (Int) -> Bool = { sub in
            let raised = (figure?.bounds.height ?? 0) * CGFloat(figureScale(figure, sub: sub, titleHeight: metrics.height)) * (1 - topperSink)
            return CGFloat(metrics.height * sub) + raised <= maxHeight * scale
        }
        let target = width * scale
        let sub = (1...16)
            .filter { fits($0) && CGFloat(metrics.width * $0) <= target * 1.06 }
            .min { abs(CGFloat(metrics.width * $0) - target) < abs(CGFloat(metrics.width * $1) - target) } ?? 1
        let unit = CGFloat(sub) / scale
        // The letters' middle, which the fish can push off the middle of the whole block.
        let lettersShift = (metrics.firstLineCenter - CGFloat(metrics.width) / 2) * unit

        VStack(spacing: 0) {
            if let figure {
                figureView(figure, figureScale: figureScale(figure, sub: sub, titleHeight: metrics.height), shift: lettersShift)
                    .zIndex(topperSink > 0 ? 0 : 1)
                    // Resting: the paws cover only the dark backing above the highest letters, never a
                    // letter face. Standing behind: sunk that much further.
                    .padding(.bottom, -(CGFloat(metrics.firstLineTop) * unit
                        + figure.bounds.height * CGFloat(figureScale(figure, sub: sub, titleHeight: metrics.height)) / scale * topperSink))
            }
            LogoTitle(lines: lines, sub: sub, fish: fish)
                .background {
                    // Centred on the lettering (not the fish, not the shadow under it).
                    wreathView(letters: CGSize(width: metrics.lettersWidth * sub,
                                               height: (metrics.height - LogoLayout.shadow) * sub))
                        .offset(x: (metrics.lettersCenter - CGFloat(metrics.width) / 2) * unit,
                                y: -CGFloat(LogoLayout.shadow) * unit / 2)
                }
                .zIndex(topperSink > 0 ? 1 : 0)
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(text)
        .accessibilityAddTraits(.isHeader)
    }

    private func figureView(_ figure: Figure, figureScale: Int, shift: CGFloat) -> some View {
        let scale = max(displayScale, 1)
        let k = CGFloat(figureScale) / scale
        // Centre what is drawn (not the padded frame) over the first line, and stand its lowest drawn
        // row on the bottom of the box.
        let dx = (figure.sheet.width / 2 - figure.bounds.midX) * k + shift
        let dy = (figure.sheet.height - figure.bounds.maxY) * k
        return PixelSprite(sprite: figure.choice.sprite, animations: [figure.animation], pixelScale: figureScale,
                           anyAnimation: false, fallback: "hero")
            .background {
                if sunburst { Sunburst(maxWidth: width * 1.1, preferredScale: figureScale) }
            }
            .offset(x: dx, y: dy)
            .frame(height: figure.bounds.height * k, alignment: .bottom)
    }

    /// The plain box in the middle of each wreath sprite that the lettering goes in, in wreath pixels
    /// (from the artist); the big leaf fans (or the stone's rim) are round it.
    static let titleBoxes: [String: CGSize] = [
        "title_wreath_small": CGSize(width: 192, height: 54),
    ]

    /// The wreath behind the letters (sizes in device pixels) at the smallest whole-pixel scale whose
    /// title box holds them, so the leaf fans reach past the title.
    @ViewBuilder
    private func wreathView(letters: CGSize) -> some View {
        if let sheet = library.sheet(wreath) {
            PixelSprite(sprite: wreath, pixelScale: wreathScale(sheet: sheet, letters: letters))
                .allowsHitTesting(false)
        }
    }

    private func wreathScale(sheet: SpriteLibrary.Sheet, letters: CGSize) -> Int {
        let box = Self.titleBoxes[wreath] ?? CGSize(width: sheet.width * 0.86, height: sheet.height * 0.76)
        return max(Int((letters.width / box.width).rounded(.up)), Int((letters.height / box.height).rounded(.up)), 1)
    }
}

/// The sunburst behind a cheering hero, pulsing gently.
private struct Sunburst: View {
    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale
    let maxWidth: CGFloat
    let preferredScale: Int

    var body: some View {
        let fit = model.sprites.pixelScale("sunburst", fitting: CGSize(width: maxWidth, height: maxWidth), displayScale: displayScale)
        TimelineView(.animation(minimumInterval: 1 / 15)) { context in
            let phase = context.date.timeIntervalSinceReferenceDate
            PixelSprite(sprite: "sunburst", pixelScale: min(preferredScale, fit))
                .opacity(0.75 + 0.25 * sin(phase * 2))
        }
        .fixedSize()
        .allowsHitTesting(false)
    }
}

// MARK: - Buttons

/// A chunky pixel button: dark edge, a light (primary) or orange (secondary) line inside it, and a
/// shadow underneath that the button sinks into when pressed.
struct ChunkyButtonStyle: ButtonStyle {
    /// Primary orange, secondary cream, golden for what is paid in golden fish.
    enum Kind { case primary, secondary, golden }
    var kind = Kind.primary
    var padding: CGFloat = 14

    func makeBody(configuration: Configuration) -> some View {
        let pressed = configuration.isPressed
        let (fill, line): (Color, Color) = switch kind {
        case .primary: (.menuOrange, Color.menuYellow.opacity(0.85))
        case .secondary: (.menuCream, .menuOrange)
        case .golden: (.menuGold, Color.menuCream.opacity(0.9))
        }
        configuration.label
            .foregroundStyle(kind == .primary ? Color.menuPaper : Color.menuInk)
            .padding(.horizontal, padding)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(fill, in: PixelRect())
            .overlay(PixelRect().inset(by: 4).strokeBorder(line, lineWidth: 3))
            .overlay(PixelRect().strokeBorder(Color.menuInk, lineWidth: 3))
            .background(PixelRect().fill(Color.menuInk.opacity(0.6)).offset(y: pressed ? 0 : 4))
            .offset(y: pressed ? 3 : 0)
            .contentShape(Rectangle())
    }
}

/// The wide orange button (START, NEXT LEVEL, RETRY): outlined cream lettering and an icon on the right.
struct PrimaryButton: View {
    let title: String
    var icon: String?
    var height: CGFloat = 56
    var fontSize: CGFloat = 24
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            ZStack {
                OutlinedText(text: title, size: fontSize)
                    .minimumScaleFactor(0.6)
                if let icon {
                    PixelIcon(sprite: icon, height: fontSize * 0.95)
                        .frame(maxWidth: .infinity, alignment: .trailing)
                        .padding(.trailing, 6)
                }
            }
        }
        .buttonStyle(ChunkyButtonStyle(kind: .primary))
        .frame(height: height)
        .accessibilityLabel(title)
    }
}

/// The cream button: icon over the label (LEVELS, CATS) or beside it (RETRY, MENU).
struct SecondaryButton: View {
    enum Layout { case stacked, iconLeading, iconTrailing }
    let title: String
    var icon: String?
    var layout = Layout.iconLeading
    var height: CGFloat = 50
    var fontSize: CGFloat = 16
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            switch layout {
            case .stacked:
                VStack(spacing: 4) {
                    if let icon { PixelIcon(sprite: icon, height: fontSize * 1.7) }
                    label
                }
            case .iconLeading:
                HStack(spacing: 10) {
                    if let icon { PixelIcon(sprite: icon, height: fontSize * 1.3) }
                    label
                }
            case .iconTrailing:
                HStack(spacing: 10) {
                    label
                    if let icon { PixelIcon(sprite: icon, height: fontSize * 1.3) }
                }
            }
        }
        .buttonStyle(ChunkyButtonStyle(kind: .secondary))
        .frame(height: height)
        .accessibilityLabel(title)
    }

    private var label: some View {
        Text(title).font(.pixel(fontSize)).lineLimit(1).minimumScaleFactor(0.6)
    }
}

/// The start screen's KITTIES button, painted: a cream plank with Fluffy peeking over it, orange with sparkles
/// while held (`kitties_button`, `kitties_button_pressed`, cut by Tools/sprites/export.py). The painted
/// lettering is taken out, so the title comes from Lore.json and is set on the plank here.
struct KittiesButton: View {
    let title: String
    let action: () -> Void

    var body: some View {
        Button(action: action) { EmptyView() }
            .buttonStyle(KittiesButtonStyle(title: title))
            .accessibilityLabel(title)
    }
}

private struct KittiesButtonStyle: ButtonStyle {
    let title: String

    func makeBody(configuration: Configuration) -> some View {
        let pressed = configuration.isPressed
        Image(pressed ? "kitties_button_pressed" : "kitties_button")
            .resizable().interpolation(.high).scaledToFit()
            .overlay {
                GeometryReader { box in
                    // Where the painted lettering was: the plank's middle, below the cat's paws.
                    let size = box.size.height * 0.19
                    Group {
                        if pressed {
                            OutlinedText(text: title, size: size)
                        } else {
                            Text(title).font(.pixel(size)).foregroundStyle(Color.menuInk)
                        }
                    }
                    .lineLimit(1).minimumScaleFactor(0.5)
                    .frame(width: box.size.width * 0.66)
                    .position(x: box.size.width * 0.51, y: box.size.height * 0.73)
                }
            }
            .offset(y: pressed ? 2 : 0)
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .contentShape(Rectangle())
    }
}

/// Kept for the next-level screen: a wide orange button with just a title.
struct ResultButton: View {
    let title: String
    let action: () -> Void

    var body: some View {
        PrimaryButton(title: title, height: 52, fontSize: 20, action: action)
    }
}

/// Frame of the next-level card: the new panel look with an edge and a light line inside it.
struct MenuPanel: ViewModifier {
    let fill: Color

    func body(content: Content) -> some View {
        content
            .padding(.horizontal, 14)
            .background(fill, in: PixelRect())
            .overlay(PixelRect().inset(by: 4.5).strokeBorder(Color.menuPaper.opacity(0.8), lineWidth: 2))
            .overlay(PixelRect().strokeBorder(Color.menuInk, lineWidth: 3))
    }
}

// MARK: - Score card

/// The parchment card of the end screens and the levels/cats panels.
struct ParchmentCard: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(.horizontal, 18)
            .padding(.vertical, 14)
            .background(Color.parchment, in: PixelRect(step: 4))
            .overlay(PixelRect(step: 4).inset(by: 5).strokeBorder(Color.parchmentEdge, lineWidth: 2))
            .overlay(PixelRect(step: 4).strokeBorder(Color.menuInk, lineWidth: 3))
            .background(PixelRect(step: 4).fill(Color.menuInk.opacity(0.45)).offset(y: 5))
    }
}

extension View {
    func parchmentCard() -> some View { modifier(ParchmentCard()) }
}

/// One line of the score card: label, a dotted leader, then the value (with an optional badge first).
struct LeaderRow<Value: View>: View {
    let label: String
    var badge: String?
    var size: CGFloat = 13
    @ViewBuilder let value: () -> Value

    var body: some View {
        HStack(alignment: .center, spacing: 8) {
            if let badge { NewBadge(text: badge, size: size * 0.85) }
            Text(label).font(.pixel(size)).lineLimit(1).minimumScaleFactor(0.6).layoutPriority(1)
            DottedLeader()
            value().layoutPriority(2)
        }
        .foregroundStyle(Color.parchmentInk)
    }
}

/// The red NEW tag in front of a new best.
struct NewBadge: View {
    let text: String
    var size: CGFloat = 11

    var body: some View {
        Text(text)
            .font(.pixel(size))
            .foregroundStyle(Color.menuPaper)
            .padding(.horizontal, 5)
            .padding(.vertical, 2)
            .background(Color.badgeRed, in: Rectangle())
            .overlay(Rectangle().stroke(Color.menuInk.opacity(0.5), lineWidth: 1))
            .fixedSize()
    }
}

/// A rule across the card.
struct CardDivider: View {
    var body: some View {
        Rectangle().fill(Color.parchmentEdge).frame(height: 2)
    }
}

/// One to three stars (bronze, silver, gold); dark outlines for the ones not earned.
struct MedalStars: View {
    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale
    let medal: Medal?
    var size: CGFloat = 30

    private var stars: Int {
        switch medal {
        case .gold: 3
        case .silver: 2
        case .bronze: 1
        case nil: 0
        }
    }

    var body: some View {
        let scale = max(1, Int((size * displayScale / (model.sprites.sheet("spark_star")?.width ?? 9)).rounded()))
        HStack(spacing: size * 0.25) {
            ForEach(0..<3, id: \.self) { index in
                Group {
                    if index < stars {
                        PixelSprite(sprite: "spark_star", pixelScale: scale)
                    } else {
                        PixelSprite(sprite: "spark_star", pixelScale: scale)
                            .colorMultiply(.black).opacity(0.25)
                    }
                }
                // The middle star stands a little higher, like a podium.
                .offset(y: index == 1 ? -size * 0.2 : 0)
            }
        }
        .padding(.top, size * 0.2)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(stars)/3 \(model.ui("stars"))")
    }
}

/// The square cream sound toggle in a top corner.
struct SoundButton: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        let on = model.save.soundOn
        Button {
            model.setSound(on: !on)
        } label: {
            Image(systemName: on ? "speaker.wave.2.fill" : "speaker.slash.fill")
                .font(.system(size: 17, weight: .black))
        }
        .buttonStyle(ChunkyButtonStyle(kind: .secondary, padding: 0))
        .frame(width: 46, height: 46)
        .accessibilityLabel(on ? model.ui("sound_on") : model.ui("sound_off"))
    }
}
