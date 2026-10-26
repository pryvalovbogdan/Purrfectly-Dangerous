import SwiftUI
import UIKit

/// A boss's health on a painted plate, cut from one of the user's bar sheets (`Style`): the boss's name in the
/// plate's dark field, and under it a bar frame with a painted fill (its two ends and a stretched middle slice).
/// Where the text and the fill go is measured in the painted pieces (`*_BAR_CUTS` in Tools/sprites/export.py).
/// Which boss gets which style is decided in `BossHealth.paintedStyle(for:)`.
///
/// The plate and the frame stretch only their plain middles, so the plate can be wider than the painting's
/// own shape: the name gets room for one line of the pixel lettering at a whole number of device pixels per
/// sub-pixel, the largest that fits inside the plate's dark field (two lines only when one cannot reach that
/// size). The plate opens with a pop and the fill charging up; on each hit the fill blinks, eases down, and
/// the lost piece breaks into the style's petals (or leaves, flowers and paws) and sparkles; under a third it
/// pulses gently. Display only.
struct PaintedBossHealth: View {
    let style: Style
    let name: String
    let fraction: Double
    let hits: Int
    /// A painted crest that sits on the plate's top rim (the Great Squirrel King's crown), or nil.
    var crest: String?

    @Environment(\.displayScale) private var displayScale
    @Environment(\.verticalSizeClass) private var verticalSizeClass
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    /// The fill as drawn: eases toward `fraction`.
    @State private var shown = 0.0
    @State private var flash = 0.0
    @State private var pulse = false
    @State private var appeared = false
    @State private var bursts: [PetalBurst] = []
    @State private var chargeStart: Date?

    /// One painted bar: its image assets and where things sit in them, in the paintings' pixels.
    struct Style {
        /// The plate the name goes on, and the part of it the name may use (its dark field less a margin).
        var plate: String
        var plateSize: CGSize
        var plateText: CGRect
        /// Only the plate's columns between these insets stretch.
        var plateCaps: (leading: CGFloat, trailing: CGFloat)
        /// The bar frame, its track (where the fill goes), and its ends (the track between them stretches).
        var frame: String
        var frameSize: CGSize
        var track: CGRect
        var frameCaps: CGFloat
        /// The frame drawn at this share of the plate's scale (as on the sheet).
        var frameScale: CGFloat
        /// The bar's top, as a share of the plate's height (it overlaps the plate's bottom).
        var barTop: CGFloat
        var barSpan: BarSpan
        /// The fill's left end, middle slice and right end, and the ends' width per height.
        var fill: (left: String, mid: String, right: String)
        var fillAspect: (left: CGFloat, right: CGFloat)
        /// On its side the plate is at most this tall (points), so the whole stays a slim strip.
        var maxPlateHeight: CGFloat
        /// What a hit sheds.
        var shower: Shower
        /// A run of sparkles riding the fill's tip as it charges in (the sheet's sparkle trail).
        var chargeTrail: Bool
        /// Where a crest's bottom sits on the plate (its top rim), in plate pixels from the top.
        var crestBase: CGFloat

        enum BarSpan {
            /// This share of the plate's width, centred.
            case share(CGFloat)
            /// The plate's width less these many plate pixels at each side (under its dark field).
            case inset(CGFloat)
        }

        enum Shower {
            /// Drawn petals (ellipses) in these colours, outlined.
            case petals([Color], edge: Color)
            /// Painted pieces (image assets), thrown in turn.
            case pieces([String])
        }

        var assets: [String] {
            var names = [plate, frame, fill.left, fill.mid, fill.right]
            if case .pieces(let pieces) = shower { names += pieces }
            return names
        }

        /// Every piece is in the bundle (otherwise the HUD falls back to the plain bar).
        var isDrawn: Bool { assets.allSatisfy { UIImage(named: $0) != nil } }

        /// Sakura's route, after docs/concept/Sakura Boss Health Bar Sprite Sheet.png: the blossom-and-gold
        /// plaque (`boss_plate_sakura`, its dark field x 322…1007, y 88…158; columns 660…700 stretch), the
        /// flowered frame (`boss_bar_frame_sakura`) and the glossy red fill (ends 36×64), shedding pink petals.
        static let sakura = Style(
            plate: "boss_plate_sakura", plateSize: CGSize(width: 1340, height: 207),
            plateText: CGRect(x: 330, y: 89, width: 670, height: 69), plateCaps: (660, 640),
            frame: "boss_bar_frame_sakura", frameSize: CGSize(width: 1420, height: 135),
            track: CGRect(x: 165, y: 40, width: 1075, height: 50), frameCaps: 250,
            frameScale: 0.906, barTop: 0.88, barSpan: .share(0.96),
            fill: ("boss_bar_fill_sakura_left", "boss_bar_fill_sakura_mid", "boss_bar_fill_sakura_right"),
            fillAspect: (36 / 64, 36 / 64), maxPlateHeight: 50,
            shower: .petals([Color(hex: 0xffc4d6), Color(hex: 0xff8fb0), Color(hex: 0xffe6ee)], edge: Color(hex: 0xc2185b)),
            chargeTrail: false, crestBase: 30)

        /// Fluffy's route (the five base worlds), after docs/concept/Floral Boss Health Bar Sheet.png: the
        /// flowered wooden frame (`boss_plate_floral`, 1416×226, its dark field x 240…1175, y 83…159; columns
        /// 660…700 stretch), under it the rounded bar (`boss_bar_frame_floral`, as wide as the field) and the
        /// orange fill with a paw print at its tip (ends 30×48 and 64×48), shedding leaves, blossoms and paws.
        static let floral = Style(
            plate: "boss_plate_floral", plateSize: CGSize(width: 1416, height: 226),
            plateText: CGRect(x: 262, y: 88, width: 891, height: 66), plateCaps: (660, 716),
            frame: "boss_bar_frame_floral", frameSize: CGSize(width: 1264, height: 81),
            track: CGRect(x: 20, y: 16, width: 1224, height: 48), frameCaps: 60,
            frameScale: 1, barTop: 0.77, barSpan: .inset(226),
            fill: ("boss_bar_fill_floral_left", "boss_bar_fill_floral_mid", "boss_bar_fill_floral_right"),
            fillAspect: (30 / 48, 64 / 48), maxPlateHeight: 48,
            shower: .pieces(["boss_bar_leaf_floral", "boss_bar_petal_floral", "boss_bar_flower_floral",
                             "boss_bar_paw_floral"]),
            chargeTrail: true, crestBase: 66)
    }

    /// Sizes of everything for one width, in points (the lettering in device pixels per sub-pixel).
    struct Plan {
        var style: Style
        var width: CGFloat
        /// Points per pixel of the plate painting.
        var plateScale: CGFloat
        var plateHeight: CGFloat
        var lines: [LogoTitle.Line]
        /// The lettering's size in sub-pixels (`LogoTitle.metrics(lines)`, kept so it is measured once).
        var metrics: LogoTitle.Metrics
        var sub: Int
        var barScale: CGFloat
        var barWidth: CGFloat
        var barHeight: CGFloat
        var barTop: CGFloat
        /// Room above the plate for a crest: everything else sits this much lower.
        var rise: CGFloat
        var crestHeight: CGFloat
        var height: CGFloat

        /// The fill's track inside the bar, in the bar's points.
        var track: CGRect {
            let track = style.track
            return CGRect(x: track.minX * barScale, y: track.minY * barScale,
                          width: barWidth - (style.frameSize.width - track.maxX + track.minX) * barScale,
                          height: track.height * barScale)
        }

        /// The name's box on the plate, in the plate's points.
        var textBox: CGRect {
            let text = style.plateText
            return CGRect(x: text.minX * plateScale, y: text.minY * plateScale,
                          width: width - (style.plateSize.width - text.width) * plateScale,
                          height: text.height * plateScale)
        }
    }

    /// A crest's height, as a share of the plate's.
    static let crestShare: CGFloat = 0.5

    /// The largest lettering that fits the plate's field, one line before two at the same size. For each
    /// size the plate takes the largest scale that leaves the line room (the middle stretching to make up
    /// the width), up to its natural shape and the height cap.
    @MainActor static func plan(style: Style, width: CGFloat, name: String, displayScale: CGFloat,
                                maxPlateHeight: CGFloat?, crest: String?) -> Plan {
        let scale = max(displayScale, 1)
        let widthPixels = width * scale
        var cap = widthPixels / style.plateSize.width
        if let maxPlateHeight { cap = min(cap, maxPlateHeight * scale / style.plateSize.height) }
        let around = style.plateSize.width - style.plateText.width
        let oneLine = LogoTitle.lines(name, splitFrom: .max, tint: nil)
        let twoLines = LogoTitle.lines(name, splitFrom: 2, tint: nil)
        let candidates = (twoLines.count > 1 ? [oneLine, twoLines] : [oneLine])
            .map { (lines: $0, metrics: LogoTitle.metrics($0, fish: nil, arch: false)) }
        var choice: (lines: [LogoTitle.Line], metrics: LogoTitle.Metrics, sub: Int, plateScale: CGFloat)?
        search: for sub in (1...3).reversed() {
            for (lines, metrics) in candidates {
                let s = min(cap, (widthPixels - CGFloat(metrics.width * sub)) / around)
                if s > 0, style.plateText.height * s >= CGFloat(metrics.height * sub) {
                    choice = (lines, metrics, sub, s)
                    break search
                }
            }
        }
        // Nothing fits (a very long name on a very small screen): the smallest two lines on the largest plate.
        let picked = choice ?? (candidates.last!.lines, candidates.last!.metrics, 1, cap)
        let plateScale = picked.plateScale / scale
        let plateHeight = (style.plateSize.height * plateScale).rounded()
        let barScale = plateScale * style.frameScale
        let barWidth: CGFloat = switch style.barSpan {
        case .share(let share): (width * share).rounded()
        case .inset(let inset): (width - 2 * inset * plateScale).rounded()
        }
        let barHeight = (style.frameSize.height * barScale).rounded()
        let crestHeight = crest == nil ? 0 : (plateHeight * crestShare).rounded()
        let rise = max(0, crestHeight - (style.crestBase * plateScale).rounded())
        let barTop = (plateHeight * style.barTop).rounded()
        return Plan(style: style, width: width, plateScale: plateScale, plateHeight: plateHeight,
                    lines: picked.lines, metrics: picked.metrics, sub: picked.sub, barScale: barScale,
                    barWidth: barWidth, barHeight: barHeight, barTop: barTop, rise: rise, crestHeight: crestHeight,
                    height: rise + max(barTop + barHeight, plateHeight))
    }

    /// Plans already worked out. Laying out the lettering is slow, and SwiftUI asks for the plan
    /// several times on every HUD update of a fight (each hit, each change of a button), which stalled
    /// whole frames; the inputs only change on rotation or with the boss.
    private struct PlanKey: Hashable {
        var plate: String
        var width: CGFloat
        var name: String
        var displayScale: CGFloat
        var maxPlateHeight: CGFloat?
        var crest: String?
    }

    @MainActor private static var plans: [PlanKey: Plan] = [:]

    @MainActor private func plan(width: CGFloat) -> Plan {
        let cap = verticalSizeClass == .compact ? style.maxPlateHeight : nil
        let key = PlanKey(plate: style.plate, width: width, name: name, displayScale: displayScale,
                          maxPlateHeight: cap, crest: crest)
        if let plan = Self.plans[key] { return plan }
        let plan = Self.plan(style: style, width: width, name: name, displayScale: displayScale, maxPlateHeight: cap,
                             crest: crest)
        // A handful of widths per fight (orientations); start over rather than grow without end.
        if Self.plans.count > 32 { Self.plans.removeAll() }
        Self.plans[key] = plan
        return plan
    }

    var body: some View {
        HeightForWidth(height: { plan(width: $0).height }) {
            GeometryReader { proxy in
                content(plan(width: proxy.size.width))
            }
        }
        .scaleEffect(appeared ? 1 : 0.8)
        .opacity(appeared ? 1 : 0)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(name)
        .accessibilityValue("\(Int((clamped(fraction) * 100).rounded()))%")
        .onAppear {
            withAnimation(.spring(response: 0.4, dampingFraction: 0.6)) { appeared = true }
            // The fill charges up from empty, as a fight opens.
            withAnimation(.easeOut(duration: reduceMotion ? 0 : ChargeTrailView.duration).delay(ChargeTrailView.delay)) {
                shown = clamped(fraction)
            }
            if style.chargeTrail, !reduceMotion {
                let start = Date.now
                chargeStart = start
                Task { @MainActor in
                    try? await Task.sleep(for: .seconds(ChargeTrailView.delay + ChargeTrailView.duration + ChargeTrailView.linger))
                    if chargeStart == start { chargeStart = nil }
                }
            }
            updatePulse()
        }
        .onChange(of: fraction) { old, new in
            withAnimation(.easeOut(duration: 0.35)) { shown = clamped(new) }
            if new < old { burst(from: clamped(old), to: clamped(new)) }
            updatePulse()
        }
        .onChange(of: hits) { _, _ in
            // Two quick blinks.
            Task { @MainActor in
                for _ in 0..<2 {
                    flash = 1
                    try? await Task.sleep(for: .seconds(0.06))
                    flash = 0
                    try? await Task.sleep(for: .seconds(0.06))
                }
            }
        }
    }

    private func content(_ plan: Plan) -> some View {
        // Cap insets are in the image's points: draw each painting at the scale it is shown at, so its
        // ends keep their shape and only the middle stretches.
        let plateCaps = EdgeInsets(top: 0, leading: style.plateCaps.leading * plan.plateScale, bottom: 0,
                                   trailing: style.plateCaps.trailing * plan.plateScale)
        let frameCaps = EdgeInsets(top: 0, leading: style.frameCaps * plan.barScale, bottom: 0,
                                   trailing: style.frameCaps * plan.barScale)
        let unit = CGFloat(plan.sub) / max(displayScale, 1)
        let metrics = plan.metrics
        let textBox = plan.textBox
        let track = plan.track
        let barLeft = ((plan.width - plan.barWidth) / 2).rounded()
        let barTop = plan.rise + plan.barTop
        return ZStack(alignment: .topLeading) {
            Self.painting(style.plate, pointsPerPixel: plan.plateScale)
                .resizable(capInsets: plateCaps, resizingMode: .stretch).interpolation(.high)
                .frame(width: plan.width, height: plan.plateHeight)
                .offset(y: plan.rise)
            LogoTitle(lines: plan.lines, sub: plan.sub, arch: false)
                // Centred in the field, on whole points of the lettering's grid.
                .offset(x: (textBox.midX - CGFloat(metrics.width) * unit / 2).rounded(),
                        y: plan.rise + (textBox.midY - CGFloat(metrics.height) * unit / 2).rounded())
            if let crest {
                // Centred on the plate's top rim.
                Self.picture(crest).resizable().interpolation(.high).scaledToFit()
                    .frame(width: plan.width, height: plan.crestHeight)
                    .offset(y: plan.rise + (style.crestBase * plan.plateScale).rounded() - plan.crestHeight)
            }
            Self.painting(style.frame, pointsPerPixel: plan.barScale)
                .resizable(capInsets: frameCaps, resizingMode: .stretch).interpolation(.high)
                .frame(width: plan.barWidth, height: plan.barHeight)
                .overlay(alignment: .topLeading) {
                    fill(width: track.width, height: track.height)
                        .offset(x: track.minX, y: track.minY)
                }
                .offset(x: barLeft, y: barTop)
        }
        .frame(width: plan.width, height: plan.height, alignment: .topLeading)
        .overlay {
            let barTrack = track.offsetBy(dx: barLeft, dy: barTop)
            ZStack {
                if !bursts.isEmpty {
                    PetalBurstView(bursts: bursts, shower: style.shower, track: barTrack, size: track.height)
                }
                if let chargeStart {
                    ChargeTrailView(start: chargeStart, to: clamped(fraction), track: barTrack, size: track.height)
                }
            }
        }
    }

    /// The fill, `shown` of the track long: two rounded ends and the middle stretched between them
    /// (the ends shrink together once the fill is shorter than both).
    private func fill(width track: CGFloat, height: CGFloat) -> some View {
        let length = track * shown
        let natural = (left: height * style.fillAspect.left, right: height * style.fillAspect.right)
        let squeeze = min(1, length / (natural.left + natural.right))
        let ends = (left: natural.left * squeeze, right: natural.right * squeeze)
        return HStack(spacing: 0) {
            Self.picture(style.fill.left).resizable().interpolation(.high).frame(width: ends.left, height: height)
            Self.picture(style.fill.mid).resizable().interpolation(.high)
                .frame(width: max(0, length - ends.left - ends.right), height: height)
            Self.picture(style.fill.right).resizable().interpolation(.high).frame(width: ends.right, height: height)
        }
        .brightness(flash * 0.35 + (pulse ? 0.14 : 0))
        .opacity(length > 0.5 ? 1 : 0)
    }

    /// An image asset drawn at `pointsPerPixel` points per pixel of the painting.
    private static func painting(_ name: String, pointsPerPixel: CGFloat) -> Image {
        guard let image = decoded(name), pointsPerPixel > 0 else { return Image(name) }
        return Image(decorative: image, scale: 1 / pointsPerPixel)
    }

    /// An image asset at one point per pixel (for pieces that are resized anyway).
    fileprivate static func picture(_ name: String) -> Image {
        decoded(name).map { Image(decorative: $0, scale: 1) } ?? Image(name)
    }

    /// The bar's paintings, decoded once and kept: drawn from memory rather than decoded again when
    /// the plate first shows or is first hit (`prepare(_:name:crest:)` does it before the fight).
    @MainActor private static var decodedImages: [String: CGImage] = [:]

    @MainActor private static func decoded(_ name: String) -> CGImage? {
        if let image = decodedImages[name] { return image }
        guard let image = UIImage(named: name) else { return nil }
        let decoded = (image.preparingForDisplay() ?? image).cgImage
        decodedImages[name] = decoded
        return decoded
    }

    /// Decodes a style's pieces (and a crest) ahead of the fight, and lays out the boss's name.
    @MainActor static func prepare(_ style: Style, name: String, crest: String?) {
        for name in style.assets + [crest].compactMap({ $0 }) { _ = decoded(name) }
        // Lay out the name's lettering (one line and two) ahead too; `plan` picks from these.
        for split in [Int.max, 2] {
            _ = LogoTitle.metrics(LogoTitle.lines(name, splitFrom: split, tint: nil), fish: nil, arch: false)
        }
    }

    private func clamped(_ value: Double) -> Double { min(max(value, 0), 1) }

    /// Under a third the fill breathes a little brighter and back, about once a second.
    private func updatePulse() {
        let low = fraction > 0 && fraction < 1.0 / 3
        guard low != pulse, !reduceMotion else { return }
        if low {
            withAnimation(.easeInOut(duration: 0.55).repeatForever(autoreverses: true)) { pulse = true }
        } else {
            withAnimation(.easeOut(duration: 0.2)) { pulse = false }
        }
    }

    /// Pieces off the stretch of fill just lost (at most three bursts at once).
    private func burst(from: Double, to: Double) {
        guard !reduceMotion else { return }
        let shot = PetalBurst(from: from, to: to, start: .now)
        bursts = Array((bursts + [shot]).suffix(3))
        Task { @MainActor in
            try? await Task.sleep(for: .seconds(PetalBurst.life))
            bursts.removeAll { $0.id == shot.id }
        }
    }
}

/// A fixed scatter (0…1) per piece, so every burst has the same lively but tidy shape.
private func scatter(_ i: Int, _ salt: Int) -> CGFloat {
    let x = sin(Double(i * 12 + salt * 7) * 12.9898 + 78.233) * 43758.5453
    return CGFloat(x - x.rounded(.down))
}

/// A four-point star, the sheet's sparkle.
private func sparkle(at center: CGPoint, radius r: CGFloat) -> Path {
    var star = Path()
    star.move(to: CGPoint(x: center.x, y: center.y - r))
    star.addQuadCurve(to: CGPoint(x: center.x + r, y: center.y), control: center)
    star.addQuadCurve(to: CGPoint(x: center.x, y: center.y + r), control: center)
    star.addQuadCurve(to: CGPoint(x: center.x - r, y: center.y), control: center)
    star.addQuadCurve(to: CGPoint(x: center.x, y: center.y - r), control: center)
    return star
}

/// One hit's shower: it leaves the lost piece of fill (`to`…`from` of the track) and falls away.
private struct PetalBurst: Identifiable {
    let id = UUID()
    let from: Double
    let to: Double
    let start: Date

    static let life = 0.7
    static let petals = 9
    static let sparkles = 4
}

/// Draws the bursts: petals (or painted leaves, blossoms and paws) tumbling out of the bar and a few
/// sparkles, in one Canvas that only runs while a burst is showing. It may draw outside the plate.
private struct PetalBurstView: View {
    let bursts: [PetalBurst]
    let shower: PaintedBossHealth.Style.Shower
    /// The fill's track, in the plate's points.
    let track: CGRect
    /// Height of the track: the scale of the pieces.
    let size: CGFloat

    private static let reach: CGFloat = 60

    var body: some View {
        TimelineView(.animation) { context in
            Canvas { canvas, _ in
                for burst in bursts {
                    draw(burst, at: context.date.timeIntervalSince(burst.start), in: &canvas)
                }
            }
        }
        .padding(-Self.reach)
        .allowsHitTesting(false)
        .accessibilityHidden(true)
    }

    private func draw(_ burst: PetalBurst, at t: TimeInterval, in canvas: inout GraphicsContext) {
        let life = PetalBurst.life
        guard t >= 0, t < life else { return }
        let progress = CGFloat(t / life)
        let fade = 1 - progress * progress
        let left = track.minX + track.width * CGFloat(burst.to)
        let span = max(track.width * CGFloat(burst.from - burst.to), size * 0.5)
        let origin = CGPoint(x: Self.reach, y: Self.reach + track.midY)
        let seconds = CGFloat(t)
        for i in 0..<PetalBurst.petals {
            let x0 = left + span * (CGFloat(i) + 0.5) / CGFloat(PetalBurst.petals)
            // Thrown up and to the right (the way the sheets' breaking piece scatters), then falling.
            let vx = size * (0.6 + 2.2 * scatter(i, 1))
            let vy = -size * (1.8 + 2.4 * scatter(i, 2))
            let gravity = size * 9
            let point = CGPoint(x: origin.x + x0 + vx * seconds,
                                y: origin.y + vy * seconds + gravity * seconds * seconds / 2)
            let spin = Angle.degrees(Double(scatter(i, 3) * 360 + 540 * progress * (i.isMultiple(of: 2) ? 1 : -1)))
            var piece = canvas
            piece.opacity = fade
            piece.translateBy(x: point.x, y: point.y)
            piece.rotate(by: spin)
            switch shower {
            case .petals(let colors, let edge):
                let petal = CGSize(width: size * (0.55 + 0.25 * scatter(i, 4)), height: size * 0.34)
                let shape = Path(ellipseIn: CGRect(x: -petal.width / 2, y: -petal.height / 2,
                                                   width: petal.width, height: petal.height))
                piece.fill(shape, with: .color(colors[i % colors.count]))
                piece.stroke(shape, with: .color(edge), lineWidth: max(0.5, size * 0.04))
            case .pieces(let names):
                guard !names.isEmpty else { break }
                // Each painted piece at its own shape, its longer side about two thirds of the track.
                let image = piece.resolve(PaintedBossHealth.picture(names[i % names.count]))
                let side = size * (0.6 + 0.3 * scatter(i, 4))
                let k = side / max(image.size.width, image.size.height, 1)
                let drawn = CGSize(width: image.size.width * k, height: image.size.height * k)
                piece.draw(image, in: CGRect(x: -drawn.width / 2, y: -drawn.height / 2,
                                             width: drawn.width, height: drawn.height))
            }
        }
        // Sparkles: four-point stars that flare and fade where the piece broke off.
        for i in 0..<PetalBurst.sparkles {
            let delay = 0.25 * scatter(i, 5)
            let local = (progress - delay) / (1 - delay)
            guard local > 0, local < 1 else { continue }
            let center = CGPoint(x: origin.x + left + span * scatter(i, 6) + size * scatter(i, 7),
                                 y: origin.y + size * (scatter(i, 8) - 0.9))
            canvas.fill(sparkle(at: center, radius: size * 0.35 * sin(.pi * local)), with: .color(.white))
        }
    }
}

/// As the fill charges in, a golden star rides its tip with a short wake of sparkles, then flares out
/// (after the sparkle trail on the floral sheet). The tip follows the fill's own ease-out.
private struct ChargeTrailView: View {
    let start: Date
    /// Where the fill stops, as a share of the track.
    let to: Double
    let track: CGRect
    let size: CGFloat

    static let delay = 0.2
    static let duration = 0.9
    static let linger = 0.3
    private static let reach: CGFloat = 40
    private static let gold = Color(hex: 0xfff3b0)

    var body: some View {
        TimelineView(.animation) { context in
            Canvas { canvas, _ in
                draw(at: context.date.timeIntervalSince(start) - Self.delay, in: &canvas)
            }
        }
        .padding(-Self.reach)
        .allowsHitTesting(false)
        .accessibilityHidden(true)
    }

    /// SwiftUI's ease-out (a cubic Bézier 0, 0, 0.58, 1) at `t`, solved for x by bisection.
    private func easeOut(_ t: Double) -> Double {
        let x = min(max(t, 0), 1)
        var lo = 0.0, hi = 1.0
        for _ in 0..<20 {
            let u = (lo + hi) / 2
            let bx = 3 * (1 - u) * u * u * 0.58 + u * u * u
            if bx < x { lo = u } else { hi = u }
        }
        let u = (lo + hi) / 2
        return 3 * (1 - u) * u * u + u * u * u
    }

    private func draw(at t: TimeInterval, in canvas: inout GraphicsContext) {
        guard t >= 0 else { return }
        let total = Self.duration + Self.linger
        guard t < total else { return }
        let origin = CGPoint(x: Self.reach, y: Self.reach)
        let tip = track.minX + track.width * CGFloat(to * easeOut(t / Self.duration))
        // After the fill lands the star flares once and fades.
        let after = max(0, t - Self.duration) / Self.linger
        let fade = 1 - after
        let y = origin.y + track.midY
        let flare = 1 + 0.6 * sin(.pi * min(after * 2, 1))
        var star = canvas
        star.opacity = fade
        star.addFilter(.shadow(color: Self.gold, radius: size * 0.4))
        star.fill(sparkle(at: CGPoint(x: origin.x + tip, y: y), radius: size * 0.7 * flare), with: .color(Self.gold))
        // The wake: small sparkles left behind along the track, each twinkling out.
        for i in 0..<6 {
            let back = size * (0.6 + 1.1 * CGFloat(i))
            let x = tip - back
            guard x > track.minX else { continue }
            let twinkle = abs(sin(t * 9 + Double(i) * 1.7))
            let r = size * (0.32 - 0.035 * CGFloat(i)) * CGFloat(twinkle) * fade
            let dy = size * (scatter(i, 9) - 0.5) * 0.9
            canvas.fill(sparkle(at: CGPoint(x: origin.x + x, y: y + dy), radius: max(0, r)), with: .color(.white))
        }
    }
}

/// Takes the width it is offered and the height `height` gives for it, and lays its content out in
/// exactly that: the boss plate never claims more height than it draws.
private struct HeightForWidth: Layout {
    let height: (CGFloat) -> CGFloat

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let width = proposal.width.flatMap { $0.isFinite ? $0 : nil } ?? 360
        return CGSize(width: width, height: height(width))
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        for subview in subviews {
            subview.place(at: bounds.origin, proposal: ProposedViewSize(bounds.size))
        }
    }
}
