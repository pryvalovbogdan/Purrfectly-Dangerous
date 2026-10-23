import SwiftUI

/// The in-game HUD panels, after docs/concept/Pixel Cat Platformer HUD Sprite Sheet.png: the lives
/// panel (hearts and fish, with the cat's head over its left edge) and the "LV" tab panel with the
/// XP bar. Sprites are drawn at one whole number of device pixels per sprite pixel with
/// nearest-neighbour filtering; the cat's head is a painting and is scaled smoothly. Panel sizes and
/// insets come from Tools/sprites/characters/hud.py. Display only: the scene fills in GameHUD.
enum HUDMetrics {
    /// Device pixels per HUD sprite pixel: a heart (16 px) about 21 pt tall on 3x, 24 pt on 2x.
    static func pixelScale(_ displayScale: CGFloat) -> Int {
        max(2, Int((max(displayScale, 1) * 4 / 3).rounded()))
    }

    /// `hud_panel`: 24×24, the border and inner line 6 px deep on every side.
    static let panelInset: CGFloat = 6
    /// `hud_level_tab`: 64×32. The tab rises 8 px above the body on the left; only the body between
    /// x 50 and x 57 stretches sideways.
    static let tabSize = CGSize(width: 64, height: 32)
    static let tabLeftCap: CGFloat = 50
    static let tabRightCap: CGFloat = 7
    /// `xp_bar_frame`: 24×10, insets 3; the track the fill goes in is x 2…21, y 2…7.
    static let barHeight: CGFloat = 10
    static let barInset: CGFloat = 3
    /// The heart effects are 24×22 with the heart drawn at (4, 4).
    static let heartEffectOffset: CGFloat = 4
}

/// A panel sprite drawn 9-slice: the whole sprite image, its corners kept and its middle stretched,
/// at a whole-pixel scale. `size` and `caps` are in sprite pixels.
struct NineSliceSprite: View {
    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale
    let sprite: String
    let caps: EdgeInsets
    let size: CGSize
    let pixelScale: Int

    var body: some View {
        if let image = model.sprites.images(sprite, "still").first {
            let unit = CGFloat(pixelScale) / max(displayScale, 1)
            Image(decorative: image, scale: max(displayScale, 1) / CGFloat(pixelScale))
                .resizable(capInsets: EdgeInsets(top: caps.top * unit, leading: caps.leading * unit,
                                                 bottom: caps.bottom * unit, trailing: caps.trailing * unit),
                           resizingMode: .stretch)
                .interpolation(.none)
                .frame(width: size.width * unit, height: size.height * unit)
        }
    }
}

/// Short HUD text in the bold pixel lettering, flat colour, straight (no arch).
struct HUDText: View {
    let text: String
    let color: Color
    /// Device pixels per sub-pixel of the lettering.
    let sub: Int

    var body: some View {
        LogoTitle(lines: [LogoTitle.Line(text: text, fill: .flat(color))], sub: max(1, sub), arch: false)
    }
}

// MARK: - Lives

/// Hearts in a row over the fish count, on a navy panel, with the cat's head overlapping the panel's
/// left edge and poking above its top.
struct LivesPanel: View {
    @Environment(\.displayScale) private var displayScale
    let hearts: Int
    let maxHearts: Int
    let fish: Int

    /// The head is about 1.4 times the panel's height, as on the sheet.
    private static let headShare: CGFloat = 1.4
    /// hud_cat.png is 214×203.
    private static let headAspect: CGFloat = 214 / 203

    var body: some View {
        let k = HUDMetrics.pixelScale(displayScale)
        let unit = CGFloat(k) / max(displayScale, 1)
        let inset = HUDMetrics.panelInset
        // Content in sprite pixels: hearts (14 tall, 1 apart), 2 px gap, the fish row (12 tall).
        let heartsWidth = CGFloat(maxHearts) * 17 - 1
        let contentHeight: CGFloat = 14 + 2 + 12
        let panelHeight = contentHeight + 2 * inset
        let headHeight = (panelHeight * unit * Self.headShare).rounded()
        let headWidth = (headHeight * Self.headAspect).rounded()
        // The head covers the panel's left part; the hearts start just past its cheek.
        let leftRoom = (headWidth * 0.78 / unit).rounded()
        let panelWidth = leftRoom + heartsWidth + inset

        ZStack(alignment: .bottomLeading) {
            NineSliceSprite(sprite: "hud_panel",
                            caps: EdgeInsets(top: inset, leading: inset, bottom: inset, trailing: inset),
                            size: CGSize(width: panelWidth, height: panelHeight), pixelScale: k)
                .overlay(alignment: .topLeading) {
                    VStack(alignment: .leading, spacing: 2 * unit) {
                        HeartsRow(hearts: hearts, maxHearts: maxHearts, pixelScale: k)
                        HStack(spacing: 2 * unit) {
                            PixelSprite(sprite: "fish", animations: ["spin"], pixelScale: k, animated: false)
                            HUDText(text: "×\(fish)", color: .white, sub: k - 1)
                                .frame(height: 12 * unit)
                        }
                    }
                    .padding(.top, inset * unit)
                    .padding(.leading, leftRoom * unit)
                }
                .padding(.leading, headWidth * 0.1)
            // The cat: bottom on the panel's bottom, its left edge just past the panel's.
            Image("hud_cat")
                .resizable()
                .interpolation(.high)
                .scaledToFit()
                .frame(width: headWidth, height: headHeight)
                .accessibilityHidden(true)
        }
        .frame(height: headHeight, alignment: .bottom)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(hearts) of \(maxHearts) hearts, \(fish) fish")
    }
}

/// The hearts, each playing `heart_lose` as it empties and `heart_gain` as it fills.
private struct HeartsRow: View {
    let hearts: Int
    let maxHearts: Int
    let pixelScale: Int
    @Environment(\.displayScale) private var displayScale
    @State private var effects: [Int: HeartEffect] = [:]

    private struct HeartEffect: Equatable {
        let sprite: String
        let animation: String
        let id = UUID()
    }

    var body: some View {
        let unit = CGFloat(pixelScale) / max(displayScale, 1)
        HStack(spacing: unit) {
            ForEach(0..<maxHearts, id: \.self) { index in
                PixelSprite(sprite: index < hearts ? "heart_full" : "heart_empty", pixelScale: pixelScale)
                    .overlay(alignment: .topLeading) {
                        if let effect = effects[index] {
                            PixelSprite(sprite: effect.sprite, animations: [effect.animation], pixelScale: pixelScale)
                                .id(effect.id)
                                .offset(x: -HUDMetrics.heartEffectOffset * unit, y: -HUDMetrics.heartEffectOffset * unit)
                                .allowsHitTesting(false)
                        }
                    }
            }
        }
        .onChange(of: hearts) { old, new in
            guard new != old else { return }
            let losing = new < old
            let effect = losing ? ("heart_lose", "burst", 0.45) : ("heart_gain", "glow", 0.9)
            for index in min(old, new)..<max(old, new) where index < maxHearts {
                let shown = HeartEffect(sprite: effect.0, animation: effect.1)
                effects[index] = shown
                Task { @MainActor in
                    try? await Task.sleep(for: .seconds(effect.2))
                    if effects[index] == shown { effects[index] = nil }
                }
            }
        }
    }
}

// MARK: - Level

/// "LV n" on the tab of the level panel, with the XP bar in its body coloured by kitten level. On a
/// level up the bar flashes and gold arrows rise from it.
struct LevelPanel: View {
    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale
    let level: Int
    let fraction: Double
    @State private var levelUp: UUID?
    @State private var flash = 0.0

    /// Panel width in sprite pixels (the sprite's own is 64; the body stretches).
    private static let width: CGFloat = 84

    /// XP fill per kitten level, from the palette (Tools/sprites/palette.py HUD_FILL_*): light, base, dark.
    static func fillColors(level: Int) -> (light: Color, base: Color, dark: Color) {
        switch level {
        case ...1: (Color(hex: 0x9cf07a), Color(hex: 0x44c040), Color(hex: 0x268a30))
        case 2: (Color(hex: 0x8ad8ff), Color(hex: 0x2a9ef0), Color(hex: 0x1a6ac0))
        case 3: (Color(hex: 0xfff08a), Color(hex: 0xffc81e), Color(hex: 0xd88a10))
        default: (Color(hex: 0xff8a8a), Color(hex: 0xee3040), Color(hex: 0xa81c34))
        }
    }

    var body: some View {
        let k = HUDMetrics.pixelScale(displayScale)
        let unit = CGFloat(k) / max(displayScale, 1)
        let size = CGSize(width: Self.width, height: HUDMetrics.tabSize.height)
        // The bar sits in the body: 6 px in from the sides, its top 15 px down.
        let barWidth = size.width - 12

        NineSliceSprite(sprite: "hud_level_tab",
                        caps: EdgeInsets(top: 0, leading: HUDMetrics.tabLeftCap, bottom: 0, trailing: HUDMetrics.tabRightCap),
                        size: size, pixelScale: k)
            .overlay(alignment: .topLeading) {
                HStack(spacing: 0) {
                    HUDText(text: model.ui("level_short"), color: .white, sub: k - 2)
                    HUDText(text: "\(level)", color: Color(hex: 0xffc81e), sub: k - 2)
                }
                .padding(.leading, 5 * unit)
                .padding(.top, 2 * unit)
            }
            .overlay(alignment: .topLeading) {
                XPBar(fraction: fraction, level: level, width: barWidth, pixelScale: k)
                    .overlay(Color.white.opacity(flash).allowsHitTesting(false))
                    .padding(.leading, 6 * unit)
                    .padding(.top, 15 * unit)
            }
            .overlay(alignment: .topTrailing) {
                if let levelUp {
                    PixelSprite(sprite: "level_up_arrows", animations: ["rise"], pixelScale: k)
                        .id(levelUp)
                        .offset(x: -4 * unit, y: -18 * unit)
                        .allowsHitTesting(false)
                }
            }
            .onChange(of: level) { old, new in
                guard new > old else { return }
                let shown = UUID()
                levelUp = shown
                flash = 0.85
                withAnimation(.easeOut(duration: 0.6)) { flash = 0 }
                Task { @MainActor in
                    // The arrows' six frames at 10 fps.
                    try? await Task.sleep(for: .seconds(0.6))
                    if levelUp == shown { levelUp = nil }
                }
            }
            .accessibilityElement(children: .ignore)
            .accessibilityLabel("\(model.ui("level")) \(level)")
            .accessibilityValue("\(Int((min(max(fraction, 0), 1) * 100).rounded()))%")
    }
}

/// `xp_bar_frame` 9-slice, filled in the level's colours to `fraction` in whole sprite pixels. The
/// fill is the rows of `xp_bar_fill` (light, light, base, base, base, dark) in the level's palette
/// colours: the sprite itself is only drawn in yellow.
private struct XPBar: View {
    @Environment(\.displayScale) private var displayScale
    let fraction: Double
    let level: Int
    /// Width in sprite pixels.
    let width: CGFloat
    let pixelScale: Int

    var body: some View {
        let unit = CGFloat(pixelScale) / max(displayScale, 1)
        let inset = HUDMetrics.barInset
        let track = width - 4
        let filled = (track * CGFloat(min(max(fraction, 0), 1))).rounded(.down)
        let colors = LevelPanel.fillColors(level: level)
        NineSliceSprite(sprite: "xp_bar_frame", caps: EdgeInsets(top: inset, leading: inset, bottom: inset, trailing: inset),
                        size: CGSize(width: width, height: HUDMetrics.barHeight), pixelScale: pixelScale)
            .overlay(alignment: .topLeading) {
                if filled > 0 {
                    VStack(spacing: 0) {
                        Rectangle().fill(colors.light).frame(height: 2 * unit)
                        Rectangle().fill(colors.base).frame(height: 3 * unit)
                        Rectangle().fill(colors.dark).frame(height: unit)
                    }
                    .frame(width: filled * unit)
                    .padding(.leading, 2 * unit)
                    .padding(.top, 2 * unit)
                }
            }
    }
}

extension Color {
    /// A colour from a 0xRRGGBB value, as the palette writes them.
    init(hex: UInt32) {
        self.init(red: Double((hex >> 16) & 0xff) / 255, green: Double((hex >> 8) & 0xff) / 255,
                  blue: Double(hex & 0xff) / 255)
    }
}

// MARK: - Boss

/// The boss's health during the fight. A boss with its own banner art (only the Great Squirrel King
/// so far: `boss_banner_squirrel`, with its name painted in) shows that banner, centred, with the
/// sprite bar tucked under it as on docs/concept/The Great Squirrel King UI Sprite Sheet.png. Every
/// other boss, or a missing bar sprite, gets the plain name and bar.
struct BossHealth: View {
    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale
    @Environment(\.verticalSizeClass) private var verticalSizeClass
    let id: String?
    let name: String
    let fraction: Double
    let hits: Int

    /// Banner art per boss id (image assets cut from each boss's sheet).
    static let banners: [String: String] = ["boss_squirrel": "boss_banner_squirrel"]
    static let barSprites = ["boss_bar_frame", "boss_bar_fill", "boss_bar_fill_low", "boss_bar_flash"]

    /// Bosses of Sakura's route: the painted blossom plaque and bar (`SakuraBossHealth`).
    static let sakuraBosses: Set<String> = ["boss_kitsune", "boss_toad", "boss_guardian_cat"]

    /// Bosses whose health plate opens the fight with its own entrance and shows the name, so the
    /// scene leaves out the plain name banner (it would only repeat the name under the plate).
    static func introducesItself(_ id: String) -> Bool {
        sakuraBosses.contains(id)
    }

    var body: some View {
        let banner = id.flatMap { Self.banners[$0] }
        let barsDrawn = Self.barSprites.allSatisfy { model.sprites.sheet($0) != nil }
        if let id, Self.sakuraBosses.contains(id) {
            // Upright about the HUD row's width; on its side half the width, its height capped
            // (SakuraBossHealth.maxPlateHeight) so it stays a slim strip over the play area.
            SakuraBossHealth(name: name, fraction: fraction, hits: hits)
                .containerRelativeFrame(.horizontal) { width, _ in
                    (width * (verticalSizeClass == .compact ? 0.5 : 0.9)).rounded()
                }
        } else if let banner, barsDrawn {
            // About 70% of an upright screen wide; on its side 30%, which keeps the banner and bar to
            // about a fifth of the screen's height.
            let share: CGFloat = verticalSizeClass == .compact ? 0.3 : 0.7
            VStack(spacing: 0) {
                Image(banner)
                    .resizable()
                    .interpolation(.high)
                    .scaledToFit()
                    .accessibilityHidden(true)
                // A little narrower than the banner, overlapping its bottom edge.
                GeometryReader { proxy in
                    BossBar(fraction: fraction, hits: hits, width: proxy.size.width)
                        .frame(maxWidth: .infinity)
                }
                .frame(height: BossBar.height(model.sprites, displayScale: displayScale))
                .padding(.horizontal, 10)
                .padding(.top, -6)
            }
            .containerRelativeFrame(.horizontal) { width, _ in (width * share).rounded() }
            .accessibilityElement(children: .ignore)
            .accessibilityLabel(name)
            .accessibilityValue("\(Int((min(max(fraction, 0), 1) * 100).rounded()))%")
        } else {
            VStack(spacing: 2) {
                Text(name.uppercased()).font(.pixel(11)).outlined()
                Bar(fraction: fraction, color: .red).frame(maxWidth: 240).frame(height: 8)
            }
            .padding(6)
            .background(.black.opacity(0.3), in: RoundedRectangle(cornerRadius: 6))
        }
    }
}

/// `boss_bar_frame` 9-slice at the HUD's whole-pixel scale, `boss_bar_fill` (or `boss_bar_fill_low`
/// under a third) stretched to the health left and easing down to it, and `boss_bar_flash` blinking
/// over it on each hit. Insets and track from Tools/sprites/characters/hud.py (boss bar section).
private struct BossBar: View {
    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale
    let fraction: Double
    let hits: Int
    /// Width in points.
    let width: CGFloat
    @State private var flash = 0.0

    /// `boss_bar_frame` (40×12) 9-slice insets, which are also where its track starts.
    static let insetX: CGFloat = 7
    static let insetY: CGFloat = 4

    /// Height in points of the bar at the HUD scale.
    static func height(_ library: SpriteLibrary, displayScale scale: CGFloat) -> CGFloat {
        let k = CGFloat(HUDMetrics.pixelScale(scale))
        return (library.sheet("boss_bar_frame")?.height ?? 12) * k / max(scale, 1)
    }

    var body: some View {
        let k = HUDMetrics.pixelScale(displayScale)
        let unit = CGFloat(k) / max(displayScale, 1)
        let frameHeight = model.sprites.sheet("boss_bar_frame")?.height ?? 12
        let fillHeight = model.sprites.sheet("boss_bar_fill")?.height ?? 4
        let widthPixels = (width / unit).rounded(.down)
        // The track runs from x 7 to the width less 8, rows 4 to 7.
        let track = max(0, widthPixels - 2 * Self.insetX)
        let shown = min(max(fraction, 0), 1)
        let low = shown < 1.0 / 3

        NineSliceSprite(sprite: "boss_bar_frame",
                        caps: EdgeInsets(top: Self.insetY, leading: Self.insetX, bottom: Self.insetY, trailing: Self.insetX),
                        size: CGSize(width: widthPixels, height: frameHeight), pixelScale: k)
            .overlay(alignment: .topLeading) {
                ZStack(alignment: .leading) {
                    NineSliceSprite(sprite: low ? "boss_bar_fill_low" : "boss_bar_fill", caps: EdgeInsets(),
                                    size: CGSize(width: max(0, (track * shown).rounded()), height: fillHeight),
                                    pixelScale: k)
                        .animation(.easeOut(duration: 0.25), value: shown)
                    NineSliceSprite(sprite: "boss_bar_flash", caps: EdgeInsets(),
                                    size: CGSize(width: track, height: fillHeight), pixelScale: k)
                        .opacity(flash)
                }
                .padding(.leading, Self.insetX * unit)
                .padding(.top, Self.insetY * unit)
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
}
