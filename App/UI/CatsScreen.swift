import GameCore
import SwiftUI

/// The CATS screen, after docs/concept/Pixel Cat Selection Adventure.png: the CATS plank over the
/// forest, the highlighted cat big in the scene with arrows either side, a parchment card with its
/// name and description, a 4×3 grid of cats, and SELECT (or UNLOCK for a price in fish) at the
/// bottom. On its side the preview is on the left and the card, grid and button on the right.
/// Skins are looks only, so there are no stat bars. Display only: owning, paying and selecting are
/// the model's (see `CatsScreenModel`).
struct CatsScreen: View {
    @Environment(AppModel.self) private var model
    let onBack: () -> Void
    /// The cat shown big and framed in the grid; starts on the one in use.
    @State private var highlighted: String?
    @State private var sparkle: UUID?

    private var data: CatsScreenModel { model.catsScreenModel }

    var body: some View {
        let data = data
        let current = data.cats.first { $0.id == (highlighted ?? data.selected) } ?? data.cats.first
        ZStack {
            MenuBackground(pose: .empty, groundShare: Self.groundShare)
            ScreenFrame { size, insets in
                if let current {
                    if size.width > size.height {
                        wide(size: size, insets: insets, data: data, current: current)
                    } else {
                        tall(size: size, insets: insets, data: data, current: current)
                    }
                }
            }
        }
        .onAppear { if highlighted == nil { highlighted = data.selected } }
    }

    /// Share of an upright screen below the ground line: the card, grid and button sit on the earth.
    static let groundShare: CGFloat = 0.6

    // MARK: Layouts

    private func tall(size: CGSize, insets: EdgeInsets, data: CatsScreenModel, current: CatsScreenModel.Cat) -> some View {
        let side = max(14, insets.leading)
        let width = min(size.width - 2 * side, 420)
        let ground = (size.height * Self.groundShare).rounded()
        let sceneHeight = size.height - ground - insets.top
        return VStack(spacing: 0) {
            topBar(data: data)
                .padding(.top, insets.top + MenuView.topBarInset)
            VStack(spacing: 4) {
                Image("title_cats")
                    .resizable().interpolation(.high).scaledToFit()
                    .frame(width: min(width * 0.62, 300))
                    .accessibilityLabel(model.ui("cats"))
                    .accessibilityAddTraits(.isHeader)
                preview(current: current, data: data, height: max(90, sceneHeight - 160))
            }
            .frame(height: sceneHeight - 52, alignment: .bottom)
            VStack(spacing: 10) {
                infoCard(current)
                grid(data: data, current: current, columns: 4)
                actionButton(data: data, current: current)
            }
            .padding(.top, 10)
            .padding(.bottom, max(insets.bottom, 12))
            .frame(maxHeight: .infinity, alignment: .top)
        }
        .frame(width: width)
        .frame(maxWidth: .infinity)
    }

    private func wide(size: CGSize, insets: EdgeInsets, data: CatsScreenModel, current: CatsScreenModel.Cat) -> some View {
        let leading = max(insets.leading, 16)
        let trailing = max(insets.trailing, 16)
        let usable = size.width - leading - trailing
        let right = min(430, usable * 0.56)
        return HStack(alignment: .top, spacing: 14) {
            VStack(spacing: 6) {
                topBar(data: data)
                Image("title_cats")
                    .resizable().interpolation(.high).scaledToFit()
                    .frame(width: min(usable - right - 14, 240))
                    .accessibilityLabel(model.ui("cats"))
                    .accessibilityAddTraits(.isHeader)
                Spacer(minLength: 0)
                preview(current: current, data: data, height: max(80, size.height * 0.42))
                    .padding(.bottom, 40 * 2)
            }
            .frame(maxWidth: .infinity)
            VStack(spacing: 8) {
                infoCard(current)
                grid(data: data, current: current, columns: 4)
                actionButton(data: data, current: current)
            }
            .padding(10)
            .background(Color.menuInk.opacity(0.55), in: PixelRect(step: 4))
            .frame(width: right)
        }
        .padding(.top, insets.top + MenuView.topBarInset)
        .padding(.bottom, max(insets.bottom, 8))
        .padding(.leading, leading)
        .padding(.trailing, trailing)
    }

    // MARK: Pieces

    /// Back at the left, the fish wallet at the right.
    private func topBar(data: CatsScreenModel) -> some View {
        HStack {
            Button(action: onBack) {
                Image(systemName: "arrow.left").font(.system(size: 20, weight: .black))
            }
            .buttonStyle(ChunkyButtonStyle(kind: .secondary, padding: 0))
            .frame(width: 48, height: 46)
            .accessibilityLabel(model.ui("back"))
            Spacer()
            FishWallet(amount: data.wallet)
        }
    }

    /// The highlighted cat, big, standing on the grass, with arrows to step through the cats.
    private func preview(current: CatsScreenModel.Cat, data: CatsScreenModel, height: CGFloat) -> some View {
        HStack(spacing: 8) {
            arrow(left: true, data: data, current: current)
            CatFigure(cat: current, height: height)
                .frame(maxWidth: .infinity)
                .overlay {
                    if let sparkle {
                        PixelSprite(sprite: "sparkle_big", animations: ["loop"], pixelScale: 4)
                            .id(sparkle)
                            .allowsHitTesting(false)
                    }
                }
            arrow(left: false, data: data, current: current)
        }
    }

    private func arrow(left: Bool, data: CatsScreenModel, current: CatsScreenModel.Cat) -> some View {
        Button {
            guard let index = data.cats.firstIndex(where: { $0.id == current.id }), !data.cats.isEmpty else { return }
            let next = (index + (left ? -1 : 1) + data.cats.count) % data.cats.count
            highlighted = data.cats[next].id
        } label: {
            Image(systemName: left ? "arrowtriangle.left.fill" : "arrowtriangle.right.fill")
                .font(.system(size: 34, weight: .black))
                .foregroundStyle(Color.menuOrange)
                .shadow(color: .menuInk, radius: 0, x: 2, y: 2)
                .shadow(color: .menuInk, radius: 0, x: -1, y: -1)
                .frame(width: 44, height: 60)
                .contentShape(Rectangle())
        }
        .accessibilityLabel(model.ui(left ? "previous_cat" : "next_cat"))
    }

    private func infoCard(_ cat: CatsScreenModel.Cat) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            PixelTitle(text: cat.name, size: 22, alignment: .leading, splitFrom: 9)
            Text(cat.description)
                .font(.pixel(12))
                .foregroundStyle(Color.parchmentInk)
                .lineLimit(3)
                .minimumScaleFactor(0.8)
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .parchmentCard()
        .accessibilityElement(children: .combine)
    }

    private func grid(data: CatsScreenModel, current: CatsScreenModel.Cat, columns: Int) -> some View {
        LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 8), count: columns), spacing: 8) {
            ForEach(data.cats) { cat in
                CatCard(cat: cat, highlighted: cat.id == current.id, selected: cat.id == data.selected)
                    .onTapGesture { highlighted = cat.id }
            }
        }
    }

    @ViewBuilder
    private func actionButton(data: CatsScreenModel, current: CatsScreenModel.Cat) -> some View {
        if current.owned {
            PrimaryButton(title: model.ui("select"), height: 52, fontSize: 24) {
                data.select(current.id)
                // Back to the start page, where the chosen cat now stands.
                onBack()
            }
            .disabled(current.id == data.selected)
            .opacity(current.id == data.selected ? 0.7 : 1)
        } else {
            let short = current.price - data.wallet
            if short > 0 {
                // Greyed: what is still missing.
                HStack(spacing: 8) {
                    Text(model.ui("unlock")).font(.pixel(20))
                    PixelIcon(sprite: "fish", height: 18)
                    Text("\(current.price)").font(.pixel(18))
                    Text(model.ui("need_more").replacingOccurrences(of: "{n}", with: "\(short)"))
                        .font(.pixel(11)).opacity(0.85)
                }
                .foregroundStyle(Color.menuPaper.opacity(0.8))
                .frame(maxWidth: .infinity, minHeight: 52)
                .background(Color.gray.opacity(0.7), in: PixelRect())
                .overlay(PixelRect().strokeBorder(Color.menuInk, lineWidth: 3))
                .accessibilityElement(children: .combine)
                .accessibilityAddTraits(.isButton)
                .accessibilityAddTraits(.isStaticText)
            } else {
                Button {
                    if data.unlock(current.id) {
                        data.select(current.id)
                        sparkle = UUID()
                        let shown = sparkle
                        Task { @MainActor in
                            try? await Task.sleep(for: .seconds(0.9))
                            if sparkle == shown { sparkle = nil }
                            // After the unlock sparkle, back to the start page with the new cat.
                            onBack()
                        }
                    }
                } label: {
                    HStack(spacing: 8) {
                        OutlinedText(text: model.ui("unlock"), size: 22)
                        PixelIcon(sprite: "fish", height: 20)
                        OutlinedText(text: "\(current.price)", size: 20)
                    }
                }
                .buttonStyle(ChunkyButtonStyle(kind: .primary))
                .frame(height: 52)
                .accessibilityLabel("\(model.ui("unlock")) \(current.name), \(current.price)")
            }
        }
    }
}

/// What the CATS screen shows and can do: the cats in order (owned or not, with prices), the fish
/// wallet, the cat in use, and unlocking and selecting. Built by `AppModel.catsScreenModel`.
struct CatsScreenModel {
    struct Cat: Identifiable, Equatable {
        let id: String
        let name: String
        let description: String
        let price: Int
        let owned: Bool
        /// The cut-out portrait image asset (`cat_<id>`).
        let portrait: String
        /// The recoloured hero sprite (`hero_<id>`), when drawn.
        let sprite: String?
    }

    let cats: [Cat]
    let wallet: Int
    let selected: String
    /// Pays for and gives the cat; false if it can't be afforded.
    let unlock: (String) -> Bool
    let select: (String) -> Void
}

/// The cat big in the scene: its recoloured hero playing `menu` (or `idle`) at a whole-pixel scale,
/// or its painted portrait while the sprite is not drawn.
private struct CatFigure: View {
    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale
    let cat: CatsScreenModel.Cat
    let height: CGFloat

    var body: some View {
        if let sprite = cat.sprite, let sheet = model.sprites.sheet(sprite) {
            let scale = max(1, Int((height * displayScale / sheet.height).rounded(.down)))
            PixelSprite(sprite: sprite, animations: ["menu", "idle"], pixelScale: scale, anyAnimation: false,
                        fallback: "hero")
                .frame(height: height, alignment: .bottom)
                .accessibilityLabel(cat.name)
        } else {
            Image(cat.portrait)
                .resizable().interpolation(.high).scaledToFit()
                .frame(height: height)
                .accessibilityLabel(cat.name)
        }
    }
}

/// One cat in the grid: its portrait over its name. Gold frame when highlighted, a tick when in use;
/// dark with a lock and a gold price tag while not owned.
private struct CatCard: View {
    @Environment(AppModel.self) private var model
    let cat: CatsScreenModel.Cat
    let highlighted: Bool
    let selected: Bool

    var body: some View {
        VStack(spacing: 2) {
            Image(cat.portrait)
                .resizable().interpolation(.high).scaledToFit()
                .frame(maxWidth: .infinity)
                .frame(height: 54)
                .brightness(cat.owned ? 0 : -0.35)
                .saturation(cat.owned ? 1 : 0.4)
            Text(cat.name.uppercased())
                .font(.pixel(10))
                .foregroundStyle(cat.owned ? Color.menuInk : Color.menuPaper.opacity(0.85))
                .lineLimit(1)
                .minimumScaleFactor(0.6)
        }
        .padding(.top, 6)
        .padding(.bottom, cat.owned ? 6 : 14)
        .padding(.horizontal, 4)
        .background(cat.owned ? Color.parchment : Color.menuInk.opacity(0.85), in: PixelRect(step: 3))
        .overlay(PixelRect(step: 3).strokeBorder(highlighted ? Color.menuYellow : Color.menuInk,
                                                 lineWidth: highlighted ? 4 : 2.5))
        .overlay(alignment: .topTrailing) {
            if selected {
                Image(systemName: "checkmark")
                    .font(.system(size: 11, weight: .black))
                    .foregroundStyle(Color.menuInk)
                    .frame(width: 20, height: 20)
                    .background(Color.menuPaper, in: Circle())
                    .overlay(Circle().stroke(Color.menuInk, lineWidth: 2))
                    .offset(x: 5, y: -5)
            } else if !cat.owned {
                PixelIcon(sprite: "icon_lock", height: 16).offset(x: -3, y: 3)
            }
        }
        .overlay(alignment: .bottom) {
            if !cat.owned {
                HStack(spacing: 3) {
                    PixelIcon(sprite: "fish", height: 11)
                    Text("\(cat.price)").font(.pixel(10)).foregroundStyle(Color.menuInk)
                }
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(Color.menuYellow, in: Capsule())
                .overlay(Capsule().stroke(Color.menuInk, lineWidth: 1.5))
                .offset(y: 8)
            }
        }
        .contentShape(Rectangle())
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(cat.owned ? cat.name : "\(cat.name), \(model.ui("locked")), \(cat.price)")
        .accessibilityAddTraits(.isButton)
        .accessibilityAddTraits(selected ? .isSelected : [])
    }
}

/// The fish wallet: fish icon and the total, on a dark pill.
struct FishWallet: View {
    @Environment(AppModel.self) private var model
    let amount: Int

    var body: some View {
        HStack(spacing: 6) {
            PixelIcon(sprite: "fish", height: 18)
            Text("\(amount)").font(.pixel(16)).foregroundStyle(Color.menuPaper).monospacedDigit()
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Color.menuInk.opacity(0.85), in: Capsule())
        .overlay(Capsule().stroke(Color(red: 0.35, green: 0.37, blue: 0.45), lineWidth: 2.5))
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(amount) \(model.ui("fish"))")
    }
}

#Preview("Cats") {
    CatsScreen(onBack: {}).environment(AppModel())
}

// MARK: - Model

extension AppModel {
    /// The hero sprite for the cat in use: its recoloured `hero_<id>` once drawn, else `hero`.
    var heroSprite: String {
        let skinned = "hero_\(selectedSkin)"
        return sprites.sheet(skinned) != nil ? skinned : "hero"
    }

    /// The CATS screen's view of the shop (rules and saving are GameCore's `Skin` and `SaveGame`).
    var catsScreenModel: CatsScreenModel {
        let cats = Skin.catalog.map { skin in
            CatsScreenModel.Cat(id: skin.id, name: text(skin.nameKey), description: text(skin.descriptionKey),
                                price: skin.price, owned: ownedSkins.contains(skin.id), portrait: "cat_\(skin.id)",
                                sprite: sprites.sheet("hero_\(skin.id)") != nil ? "hero_\(skin.id)" : nil)
        }
        return CatsScreenModel(cats: cats, wallet: fishWallet, selected: selectedSkin,
                               unlock: { [weak self] id in self?.unlockSkin(id) == .unlocked },
                               select: { [weak self] id in _ = self?.selectSkin(id) })
    }
}
