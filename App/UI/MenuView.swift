import GameCore
import SwiftUI

/// The start screen: the title in its wreath with the hero peeking over it, the tagline, the hero
/// standing in the Purrwood below, and START, LEVELS and CATS on the earth. Upright everything is
/// stacked; on its side the title and buttons keep to the left and the hero stands on the right.
struct MenuView: View {
    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale
    @State private var overlay: Overlay?

    enum Overlay { case levels, cats }

    /// Share of an upright screen below the ground line; the buttons stand on that earth.
    static let groundShare: CGFloat = 0.25
    /// Where the hero stands across a wide screen, clear of the title and buttons on the left.
    static let wideHeroPlace: CGFloat = 0.76

    var body: some View {
        ZStack {
            MenuBackground(pose: .standing, groundShare: Self.groundShare, wideHeroPlace: Self.wideHeroPlace)
            ScreenFrame { size, insets in
                if size.width > size.height {
                    wide(size: size, insets: insets)
                } else {
                    tall(size: size, insets: insets)
                }
            }
            ScreenFrame { _, insets in
                // Beside the Dynamic Island or notch (the status bar is hidden), else under the safe area.
                SoundButton()
                    .padding(.top, max(14, insets.top - 44))
                    .padding(.trailing, max(insets.trailing, 14))
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topTrailing)
            }
            if let overlay {
                MenuOverlay(close: { self.overlay = nil }) {
                    switch overlay {
                    case .levels: LevelsPanel(close: { self.overlay = nil })
                    case .cats: CatsView(onBack: { self.overlay = nil })
                    }
                }
                .transition(.opacity)
            }
        }
        .animation(.easeOut(duration: 0.15), value: overlay)
    }

    /// Upright: title at the top, the hero in the middle of the scene, buttons on the earth.
    private func tall(size: CGSize, insets: EdgeInsets) -> some View {
        let ground = (size.height * Self.groundShare).rounded()
        let side = max(16, insets.leading)
        let width = min(size.width - 2 * side, 380)
        // The title block (peeking cat, title, tagline) hangs at least `titleClearance` below the safe
        // area, so the Dynamic Island never hides the cat's ears, and when there is room it comes down
        // to end just above the tree tops of the scene, leaving no empty band of sky between them.
        let topLimit = insets.top + Self.titleClearance
        let unit = MenuScene.pointsPerUnit(viewSize: size, displayScale: displayScale)
        let heroTop = size.height - ground - MenuScene.heroHeight(model.sprites) * unit
        let scenery = MenuScene.sceneryTop(viewSize: size, displayScale: displayScale, library: model.sprites,
                                           groundShare: Self.groundShare) ?? heroTop
        let bottomLimit = max(topLimit + 1, scenery - Self.sceneryGap)
        return ZStack(alignment: .top) {
            VStack(spacing: 0) {
                Spacer(minLength: topLimit)
                // About four fifths of an upright screen wide.
                titleBlock(width: (size.width * Self.tallTitleShare).rounded(), maxHeight: heroTop - topLimit - 40)
                    .fixedSize(horizontal: false, vertical: true)
            }
            // Bottom-aligned within the band while it fits; a taller block keeps its top and runs on.
            .frame(height: bottomLimit, alignment: .top)
            .frame(maxWidth: .infinity)
            actions(width: width)
                .padding(.top, 14)
                .frame(height: ground, alignment: .top)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottom)
        }
    }

    /// On its side: title over the buttons in a left column; the hero stands on the right.
    private func wide(size: CGSize, insets: EdgeInsets) -> some View {
        let leading = max(insets.leading, 20)
        let titleWidth = (size.width * Self.wideTitleShare).rounded()
        let width = min(400, titleWidth, size.width * Self.wideHeroPlace - leading - size.width * 0.16)
        let top = insets.top + Self.titleClearance
        let bottom = max(insets.bottom, 10) + 8
        let titleHeight = max(90, size.height - top - bottom - Self.actionsHeight - 44)
        return VStack(spacing: 8) {
            titleBlock(width: titleWidth, maxHeight: titleHeight)
            Spacer(minLength: 0)
            actions(width: width)
        }
        .frame(width: titleWidth)
        .padding(.top, top)
        .padding(.bottom, bottom)
        .padding(.leading, leading)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
    }

    private static let actionsHeight: CGFloat = 58 + 10 + 66
    /// Share of the screen width the title spans: upright, and in the left column on its side.
    private static let rowGap: CGFloat = 12
    private static let tallTitleShare: CGFloat = 0.8
    private static let wideTitleShare: CGFloat = 0.4
    /// Space kept between the safe area's top and the cat's ear tips.
    private static let titleClearance: CGFloat = 24
    /// Space between the tagline and the scene's tree tops.
    private static let sceneryGap: CGFloat = 8

    /// The title in its wreath with the hero peeking over it, and the tagline under it.
    private func titleBlock(width: CGFloat, maxHeight: CGFloat) -> some View {
        VStack(spacing: 4) {
            WreathTitle(text: model.text("game.title"), wreath: "title_wreath", width: width, maxHeight: maxHeight,
                        topper: ["peek", "idle"], fish: true, paw: true)
            Text(model.text("game.tagline"))
                .font(.pixel(13))
                .foregroundStyle(Color.menuPaper)
                .multilineTextAlignment(.center)
                .lineLimit(2)
                .minimumScaleFactor(0.7)
                .padding(.horizontal, 14)
                .padding(.vertical, 5)
                .background(Color(red: 0.12, green: 0.22, blue: 0.27).opacity(0.85), in: Capsule())
                .overlay(Capsule().stroke(Color.menuInk.opacity(0.5), lineWidth: 1.5))
        }
    }

    private func actions(width: CGFloat) -> some View {
        VStack(spacing: 10) {
            // START begins an endless run: every level in order, round and round.
            PrimaryButton(title: model.ui("start"), icon: "icon_play", height: 58, fontSize: 28) {
                model.startEndless()
            }
            .accessibilityHint(model.text("mode.endless.name"))
            // Sized as in the three-button design (a third of START less the gaps), two of them centred.
            let small = ((width - 2 * Self.rowGap) / 3).rounded(.down)
            HStack(spacing: Self.rowGap) {
                SecondaryButton(title: model.ui("levels"), icon: "icon_trophy", layout: .stacked, height: 66, fontSize: 14) {
                    overlay = .levels
                }
                .frame(width: small)
                SecondaryButton(title: model.ui("cats"), icon: "icon_cat", layout: .stacked, height: 66, fontSize: 14) {
                    overlay = .cats
                }
                .frame(width: small)
            }
            .frame(maxWidth: .infinity)
        }
        .frame(width: width)
    }
}

/// A panel over the dimmed menu; tapping outside it closes it.
private struct MenuOverlay<Content: View>: View {
    let close: () -> Void
    @ViewBuilder let content: () -> Content

    var body: some View {
        ZStack {
            Color.black.opacity(0.5)
                .ignoresSafeArea()
                .onTapGesture(perform: close)
                .accessibilityAddTraits(.isButton)
                .accessibilityAction(.escape, close)
            content()
                .padding(.horizontal, 20)
                .padding(.vertical, 14)
        }
    }
}

// MARK: - Levels

/// Every level, in order. A level opens here once it has been beaten in an endless run; the rest
/// show as locked.
struct LevelsPanel: View {
    @Environment(AppModel.self) private var model
    let close: () -> Void

    var body: some View {
        VStack(spacing: 12) {
            PixelTitle(text: model.ui("levels"), size: 26, alignment: .center, splitFrom: 9)
            if model.save.bestEndlessScore > 0 {
                LeaderRow(label: model.text("mode.endless.name").uppercased(), size: 11) {
                    Text("\(model.ui("best")) \(model.save.bestEndlessScore)").font(.pixel(11))
                }
            }
            ScrollView {
                VStack(spacing: 8) {
                    ForEach(model.levels.indices, id: \.self) { index in
                        LevelRow(index: index, close: close)
                    }
                }
                .padding(.vertical, 4)
            }
            .scrollBounceBehavior(.basedOnSize)
            .frame(maxHeight: 260)
            if !model.levels.indices.contains(where: model.isUnlocked) {
                Text(model.ui("levels_hint"))
                    .font(.pixel(11))
                    .foregroundStyle(Color.parchmentInk.opacity(0.8))
                    .multilineTextAlignment(.center)
                    .fixedSize(horizontal: false, vertical: true)
            }
            SecondaryButton(title: model.ui("back"), height: 44, fontSize: 15, action: close)
        }
        .frame(maxWidth: 380)
        .parchmentCard()
    }
}

private struct LevelRow: View {
    @Environment(AppModel.self) private var model
    let index: Int
    let close: () -> Void

    var body: some View {
        let level = model.levels[index]
        let open = model.isUnlocked(index)
        Button {
            close()
            model.start(level: index)
        } label: {
            HStack(spacing: 10) {
                Text("\(index + 1)").font(.pixel(18)).frame(width: 22)
                VStack(alignment: .leading, spacing: 2) {
                    Text(model.text(level.nameKey).uppercased()).font(.pixel(12)).lineLimit(1).minimumScaleFactor(0.6)
                    if !open {
                        Text(model.ui("locked")).font(.pixel(9)).opacity(0.7)
                    } else if let best = model.save.bestScores[level.id] {
                        Text("\(model.ui("best")) \(best)").font(.pixel(9)).opacity(0.75)
                    }
                }
                Spacer(minLength: 4)
                PixelIcon(sprite: open ? "icon_play" : "icon_lock", height: 18)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .buttonStyle(ChunkyButtonStyle(kind: .secondary, padding: 10))
        .frame(height: 48)
        .disabled(!open)
        .opacity(open ? 1 : 0.6)
        .accessibilityLabel("\(model.ui("level")) \(index + 1), \(model.text(level.nameKey))\(open ? "" : ", \(model.ui("locked"))")")
    }
}

// MARK: - Cats

/// The skins screen: the orange cat (selected) and locked slots still to come.
struct CatsView: View {
    @Environment(AppModel.self) private var model
    @Environment(\.verticalSizeClass) private var verticalSizeClass
    let onBack: () -> Void

    /// Slots shown locked until more skins exist.
    private static let lockedSlots = 3

    var body: some View {
        let columns = verticalSizeClass == .compact ? 4 : 2
        VStack(spacing: 14) {
            PixelTitle(text: model.ui("cats"), size: 26, alignment: .center, splitFrom: 9)
            LazyVGrid(columns: Array(repeating: GridItem(.fixed(118), spacing: 12), count: columns), spacing: 12) {
                ForEach(AppModel.skins, id: \.self) { skin in
                    SkinSlot(skin: skin, selected: model.save.selectedSkin == skin) { model.selectSkin(skin) }
                }
                ForEach(0..<Self.lockedSlots, id: \.self) { _ in
                    LockedSlot()
                }
            }
            SecondaryButton(title: model.ui("back"), height: 44, fontSize: 15, action: onBack)
                .frame(maxWidth: 260)
        }
        .parchmentCard()
    }
}

private struct SkinSlot: View {
    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale
    let skin: String
    let selected: Bool
    let select: () -> Void

    var body: some View {
        let scale = model.sprites.pixelScale("hero", fitting: CGSize(width: 96, height: 76), displayScale: displayScale)
        Button(action: select) {
            VStack(spacing: 4) {
                // Only the orange cat exists so far, and it is the hero as drawn.
                PixelSprite(sprite: "hero", animations: ["idle"], pixelScale: scale, anyAnimation: false)
                    .frame(height: 80, alignment: .bottom)
                Text(model.text("hero.name").uppercased()).font(.pixel(12)).lineLimit(1).minimumScaleFactor(0.6)
            }
            .padding(.vertical, 8)
        }
        .buttonStyle(ChunkyButtonStyle(kind: .secondary, padding: 6))
        .frame(height: 120)
        .overlay {
            if selected {
                PixelRect().inset(by: -4).strokeBorder(Color.menuOrange, lineWidth: 4)
            }
        }
        .overlay(alignment: .topTrailing) {
            if selected {
                NewBadge(text: model.ui("selected"), size: 8).offset(x: 6, y: -8)
            }
        }
        .accessibilityLabel(model.text("hero.name"))
        .accessibilityAddTraits(selected ? .isSelected : [])
    }
}

private struct LockedSlot: View {
    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale

    var body: some View {
        let scale = model.sprites.pixelScale("cat_silhouette", fitting: CGSize(width: 96, height: 76), displayScale: displayScale)
        VStack(spacing: 4) {
            ZStack(alignment: .bottomTrailing) {
                PixelSprite(sprite: "cat_silhouette", pixelScale: scale)
                PixelIcon(sprite: "icon_lock", height: 24).offset(x: 6, y: 2)
            }
            .frame(height: 80, alignment: .bottom)
            Text(model.ui("locked")).font(.pixel(12)).foregroundStyle(Color.parchmentInk.opacity(0.6))
        }
        .padding(.vertical, 8)
        .frame(maxWidth: .infinity)
        .frame(height: 120)
        .background(Color.parchmentEdge.opacity(0.35), in: PixelRect())
        .overlay(PixelRect().strokeBorder(Color.menuInk.opacity(0.5), lineWidth: 3))
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(model.ui("locked"))
    }
}

#Preview("Menu") {
    MenuView().environment(AppModel())
}

#Preview("Cats") {
    ZStack {
        Color(red: 0.44, green: 0.71, blue: 0.88).ignoresSafeArea()
        CatsView(onBack: {})
    }
    .environment(AppModel())
}

#Preview("Levels") {
    ZStack {
        Color(red: 0.44, green: 0.71, blue: 0.88).ignoresSafeArea()
        LevelsPanel(close: {})
    }
    .environment(AppModel())
}
