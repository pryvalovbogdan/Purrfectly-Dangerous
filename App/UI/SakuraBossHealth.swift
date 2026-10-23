import SwiftUI
import UIKit

/// The Sakura route's boss health, after docs/concept/Sakura Boss Health Bar Sprite Sheet.png: the boss's
/// name on the blossom-and-gold plaque (`boss_plate_sakura`), and under it the flowered bar frame
/// (`boss_bar_frame_sakura`) with the glossy red fill (its rounded ends and a stretched middle slice).
/// Where the text and the fill go is measured in the painted pieces (`SAKURA_BAR_CUTS` in
/// Tools/sprites/export.py).
///
/// The plaque and the frame stretch only their plain middles, so the plate can be wider than the
/// painting's own shape: the name gets room for one line of the pixel lettering at a whole number of
/// device pixels per sub-pixel, the largest that fits inside the plaque's dark field (two lines only
/// when one cannot reach that size). The plate opens with a pop and the fill charging up; on each hit
/// the fill blinks, eases down, and the lost piece breaks into petals and sparkles; under a third it
/// pulses gently. Display only.
struct SakuraBossHealth: View {
    let name: String
    let fraction: Double
    let hits: Int

    @Environment(\.displayScale) private var displayScale
    @Environment(\.verticalSizeClass) private var verticalSizeClass
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    /// The fill as drawn: eases toward `fraction`.
    @State private var shown = 0.0
    @State private var flash = 0.0
    @State private var pulse = false
    @State private var appeared = false
    @State private var bursts: [PetalBurst] = []

    // Measured in the painted pieces, in their pixels.
    /// `boss_plate_sakura`, and the part of it the name may use: the dark field (x 322…1007,
    /// y 88…158, rounded at the ends) less a little margin.
    static let plate = CGSize(width: 1340, height: 207)
    static let plateText = CGRect(x: 330, y: 89, width: 670, height: 69)
    /// Columns 660…700 are a plain stretch of the field between its gold rims; only they stretch.
    static let plateCaps = (leading: CGFloat(660), trailing: CGFloat(640))
    /// `boss_bar_frame_sakura`, its track, and its ornate ends (the track between them stretches).
    static let frame = CGSize(width: 1420, height: 135)
    static let track = CGRect(x: 165, y: 40, width: 1075, height: 50)
    static let frameCaps: CGFloat = 250
    /// The frame drawn at this share of the plate's scale (as on the sheet), overlapping the plate's
    /// bottom by this share of its height.
    static let frameScale: CGFloat = 0.906
    static let overlap: CGFloat = 0.12
    /// The fill's end pieces are 36×64.
    static let endAspect: CGFloat = 36 / 64
    /// On its side the plate is at most this tall (points), so the whole stays a slim strip.
    static let maxPlateHeight: CGFloat = 50

    /// Sizes of everything for one width, in points (the lettering in device pixels per sub-pixel).
    struct Plan {
        var width: CGFloat
        /// Points per pixel of the plate painting.
        var plateScale: CGFloat
        var plateHeight: CGFloat
        var lines: [LogoTitle.Line]
        var sub: Int
        var barScale: CGFloat
        var barWidth: CGFloat
        var barHeight: CGFloat
        var barTop: CGFloat
        var height: CGFloat

        /// The fill's track inside the bar, in the bar's points.
        var track: CGRect {
            CGRect(x: SakuraBossHealth.track.minX * barScale, y: SakuraBossHealth.track.minY * barScale,
                   width: barWidth - (SakuraBossHealth.frame.width - SakuraBossHealth.track.maxX + SakuraBossHealth.track.minX) * barScale,
                   height: SakuraBossHealth.track.height * barScale)
        }

        /// The name's box on the plate, in the plate's points.
        var textBox: CGRect {
            let text = SakuraBossHealth.plateText
            return CGRect(x: text.minX * plateScale, y: text.minY * plateScale,
                          width: width - (SakuraBossHealth.plate.width - text.width) * plateScale,
                          height: text.height * plateScale)
        }
    }

    /// The largest lettering that fits the plaque's field, one line before two at the same size. For each
    /// size the plate takes the largest scale that leaves the line room (the middle stretching to make up
    /// the width), up to its natural shape and the height cap.
    static func plan(width: CGFloat, name: String, displayScale: CGFloat, maxPlateHeight: CGFloat?) -> Plan {
        let scale = max(displayScale, 1)
        let widthPixels = width * scale
        var cap = widthPixels / plate.width
        if let maxPlateHeight { cap = min(cap, maxPlateHeight * scale / plate.height) }
        let around = plate.width - plateText.width
        let oneLine = LogoTitle.lines(name, splitFrom: .max, tint: nil)
        let twoLines = LogoTitle.lines(name, splitFrom: 2, tint: nil)
        var choice: (lines: [LogoTitle.Line], sub: Int, plateScale: CGFloat)?
        search: for sub in (1...3).reversed() {
            for lines in twoLines.count > 1 ? [oneLine, twoLines] : [oneLine] {
                let metrics = LogoTitle.metrics(lines, fish: nil, arch: false)
                let s = min(cap, (widthPixels - CGFloat(metrics.width * sub)) / around)
                if s > 0, plateText.height * s >= CGFloat(metrics.height * sub) {
                    choice = (lines, sub, s)
                    break search
                }
            }
        }
        // Nothing fits (a very long name on a very small screen): the smallest two lines on the largest plate.
        let picked = choice ?? (twoLines, 1, cap)
        let plateScale = picked.plateScale / scale
        let plateHeight = (plate.height * plateScale).rounded()
        let barScale = plateScale * frameScale
        let barWidth = (width * 0.96).rounded()
        let barHeight = (frame.height * barScale).rounded()
        let barTop = (plateHeight * (1 - overlap)).rounded()
        return Plan(width: width, plateScale: plateScale, plateHeight: plateHeight, lines: picked.lines,
                    sub: picked.sub, barScale: barScale, barWidth: barWidth, barHeight: barHeight,
                    barTop: barTop, height: barTop + barHeight)
    }

    var body: some View {
        let cap = verticalSizeClass == .compact ? Self.maxPlateHeight : nil
        HeightForWidth(height: { Self.plan(width: $0, name: name, displayScale: displayScale, maxPlateHeight: cap).height }) {
            GeometryReader { proxy in
                content(Self.plan(width: proxy.size.width, name: name, displayScale: displayScale, maxPlateHeight: cap))
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
            withAnimation(.easeOut(duration: reduceMotion ? 0 : 0.9).delay(0.2)) { shown = clamped(fraction) }
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
        let plateCaps = EdgeInsets(top: 0, leading: Self.plateCaps.leading * plan.plateScale, bottom: 0,
                                   trailing: Self.plateCaps.trailing * plan.plateScale)
        let frameCaps = EdgeInsets(top: 0, leading: Self.frameCaps * plan.barScale, bottom: 0,
                                   trailing: Self.frameCaps * plan.barScale)
        let unit = CGFloat(plan.sub) / max(displayScale, 1)
        let metrics = LogoTitle.metrics(plan.lines, fish: nil, arch: false)
        let textBox = plan.textBox
        let track = plan.track
        let barLeft = ((plan.width - plan.barWidth) / 2).rounded()
        return ZStack(alignment: .topLeading) {
            Self.painting("boss_plate_sakura", pointsPerPixel: plan.plateScale)
                .resizable(capInsets: plateCaps, resizingMode: .stretch).interpolation(.high)
                .frame(width: plan.width, height: plan.plateHeight)
            LogoTitle(lines: plan.lines, sub: plan.sub, arch: false)
                // Centred in the field, on whole points of the lettering's grid.
                .offset(x: (textBox.midX - CGFloat(metrics.width) * unit / 2).rounded(),
                        y: (textBox.midY - CGFloat(metrics.height) * unit / 2).rounded())
            Self.painting("boss_bar_frame_sakura", pointsPerPixel: plan.barScale)
                .resizable(capInsets: frameCaps, resizingMode: .stretch).interpolation(.high)
                .frame(width: plan.barWidth, height: plan.barHeight)
                .overlay(alignment: .topLeading) {
                    fill(width: track.width, height: track.height)
                        .offset(x: track.minX, y: track.minY)
                }
                .offset(x: barLeft, y: plan.barTop)
        }
        .frame(width: plan.width, height: plan.height, alignment: .topLeading)
        .overlay {
            if !bursts.isEmpty {
                PetalBurstView(bursts: bursts,
                               track: track.offsetBy(dx: barLeft, dy: plan.barTop),
                               size: track.height)
            }
        }
    }

    /// The red fill, `shown` of the track long: two rounded ends and the middle stretched between them
    /// (the ends shrink together once the fill is shorter than both).
    private func fill(width track: CGFloat, height: CGFloat) -> some View {
        let length = track * shown
        let end = min(height * Self.endAspect, length / 2)
        return HStack(spacing: 0) {
            Image("boss_bar_fill_sakura_left").resizable().interpolation(.high).frame(width: end, height: height)
            Image("boss_bar_fill_sakura_mid").resizable().interpolation(.high)
                .frame(width: max(0, length - 2 * end), height: height)
            Image("boss_bar_fill_sakura_right").resizable().interpolation(.high).frame(width: end, height: height)
        }
        .brightness(flash * 0.35 + (pulse ? 0.14 : 0))
        .opacity(length > 0.5 ? 1 : 0)
    }

    /// An image asset drawn at `pointsPerPixel` points per pixel of the painting.
    private static func painting(_ name: String, pointsPerPixel: CGFloat) -> Image {
        guard let image = UIImage(named: name)?.cgImage, pointsPerPixel > 0 else { return Image(name) }
        return Image(decorative: image, scale: 1 / pointsPerPixel)
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

    /// Petals off the piece of fill just lost (at most three bursts at once).
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

/// One hit's petals: they leave the lost piece of fill (`to`…`from` of the track) and fall away.
private struct PetalBurst: Identifiable {
    let id = UUID()
    let from: Double
    let to: Double
    let start: Date

    static let life = 0.7
    static let petals = 9
    static let sparkles = 4
}

/// Draws the petal bursts: pink petals tumbling out of the bar and a few sparkles, in one Canvas that
/// only runs while a burst is showing. It may draw outside the plate.
private struct PetalBurstView: View {
    let bursts: [PetalBurst]
    /// The fill's track, in the plate's points.
    let track: CGRect
    /// Height of the track: the scale of the petals.
    let size: CGFloat

    private static let reach: CGFloat = 60
    private static let petalColors = [Color(hex: 0xffc4d6), Color(hex: 0xff8fb0), Color(hex: 0xffe6ee)]
    private static let edge = Color(hex: 0xc2185b)

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

    /// A fixed scatter (0…1) per petal, so every burst has the same lively but tidy shape.
    private func scatter(_ i: Int, _ salt: Int) -> CGFloat {
        let x = sin(Double(i * 12 + salt * 7) * 12.9898 + 78.233) * 43758.5453
        return CGFloat(x - x.rounded(.down))
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
            // Thrown up and to the right (the way the sheet's breaking piece scatters), then falling.
            let vx = size * (0.6 + 2.2 * scatter(i, 1))
            let vy = -size * (1.8 + 2.4 * scatter(i, 2))
            let gravity = size * 9
            let point = CGPoint(x: origin.x + x0 + vx * seconds,
                                y: origin.y + vy * seconds + gravity * seconds * seconds / 2)
            let spin = Angle.degrees(Double(scatter(i, 3) * 360 + 540 * progress * (i.isMultiple(of: 2) ? 1 : -1)))
            let petal = CGSize(width: size * (0.55 + 0.25 * scatter(i, 4)), height: size * 0.34)
            var piece = canvas
            piece.opacity = fade
            piece.translateBy(x: point.x, y: point.y)
            piece.rotate(by: spin)
            let shape = Path(ellipseIn: CGRect(x: -petal.width / 2, y: -petal.height / 2,
                                               width: petal.width, height: petal.height))
            piece.fill(shape, with: .color(Self.petalColors[i % Self.petalColors.count]))
            piece.stroke(shape, with: .color(Self.edge), lineWidth: max(0.5, size * 0.04))
        }
        // Sparkles: four-point stars that flare and fade where the piece broke off.
        for i in 0..<PetalBurst.sparkles {
            let delay = 0.25 * scatter(i, 5)
            let local = (progress - delay) / (1 - delay)
            guard local > 0, local < 1 else { continue }
            let center = CGPoint(x: origin.x + left + span * scatter(i, 6) + size * scatter(i, 7),
                                 y: origin.y + size * (scatter(i, 8) - 0.9))
            let r = size * 0.35 * sin(.pi * local)
            var star = Path()
            star.move(to: CGPoint(x: center.x, y: center.y - r))
            star.addQuadCurve(to: CGPoint(x: center.x + r, y: center.y), control: center)
            star.addQuadCurve(to: CGPoint(x: center.x, y: center.y + r), control: center)
            star.addQuadCurve(to: CGPoint(x: center.x - r, y: center.y), control: center)
            star.addQuadCurve(to: CGPoint(x: center.x, y: center.y - r), control: center)
            canvas.fill(star, with: .color(.white))
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
