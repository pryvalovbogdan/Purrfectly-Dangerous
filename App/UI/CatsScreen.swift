import GameCore
import SwiftUI

/// The CATS screen, after docs/concept/Pixel Cat Selection Adventure.png: the CATS plank over the
/// forest, the highlighted cat big in the scene with arrows either side, a parchment card with its
/// name and description, a 4×3 grid of cats, and SELECT (or two unlock buttons, for its price in
/// fish or in golden fish) at the bottom. The golden fish wallet at the top opens the packs. On its side the preview is on the left and the card, grid and button on the right.
/// Skins are looks only, so there are no stat bars. Display only: owning, paying and selecting are
/// the model's (see `CatsScreenModel`).
struct CatsScreen: View {
    @Environment(AppModel.self) private var model
    let onBack: () -> Void
    /// The cat shown big and framed in the grid; starts on the one in use.
    @State private var highlighted: String?
    @State private var sparkle: UUID?
    @State private var showGoldenShop = false
    /// The purchase whose banner is showing.
    @State private var banner: GoldenStore.Delivery?

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
            if showGoldenShop {
                GoldenShopOverlay(close: { showGoldenShop = false })
                    .transition(.opacity)
            }
            if let banner {
                VStack {
                    // Below the wallets, so the golden fish counting up stays in view.
                    GoldenPurchaseBanner(amount: banner.amount)
                        .padding(.horizontal, 20)
                        .padding(.top, 72)
                    Spacer()
                }
                .transition(.move(edge: .top).combined(with: .opacity))
                .task(id: banner.id) {
                    try? await Task.sleep(for: .seconds(2.8))
                    if self.banner?.id == banner.id { self.banner = nil }
                }
            }
        }
        .animation(.easeOut(duration: 0.15), value: showGoldenShop)
        .animation(.spring(duration: 0.45, bounce: 0.3), value: banner)
        // A purchase went through: close the panel, then the banner and the balance counting up.
        .onChange(of: model.golden.delivery) { _, delivery in
            guard let delivery else { return }
            showGoldenShop = false
            banner = delivery
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
                TitlePlank(text: model.ui("cats"))
                    .frame(width: min(width * 0.72, 350))
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
                TitlePlank(text: model.ui("cats"))
                    .frame(width: min(usable - right - 14, 280))
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

    /// Back at the left, the fish and golden fish wallets at the right: side by side, smaller if they
    /// do not fit (the left column of a small phone on its side), or one over the other.
    private func topBar(data: CatsScreenModel) -> some View {
        HStack(spacing: 8) {
            Button(action: onBack) {
                Image(systemName: "arrow.left").font(.system(size: 20, weight: .black))
            }
            .buttonStyle(ChunkyButtonStyle(kind: .secondary, padding: 0))
            .frame(width: 48, height: 46)
            .accessibilityLabel(model.ui("back"))
            Spacer(minLength: 0)
            ViewThatFits(in: .horizontal) {
                HStack(spacing: 8) { wallets(data: data, compact: false) }
                HStack(spacing: 6) { wallets(data: data, compact: true) }
                VStack(alignment: .trailing, spacing: 4) { wallets(data: data, compact: true) }
            }
        }
    }

    @ViewBuilder
    private func wallets(data: CatsScreenModel, compact: Bool) -> some View {
        FishWallet(amount: data.wallet, compact: compact)
        GoldenWallet(amount: data.golden, compact: compact) { showGoldenShop = true }
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
            // Two ways to pay, side by side; one that cannot be afforded is greyed with what is missing.
            HStack(spacing: 10) {
                unlockButton(data: data, current: current, currency: .fish)
                if current.goldenPrice != nil {
                    unlockButton(data: data, current: current, currency: .golden)
                }
            }
        }
    }

    private func unlockButton(data: CatsScreenModel, current: CatsScreenModel.Cat, currency: Currency) -> some View {
        let price = (currency == .fish ? current.price : current.goldenPrice) ?? 0
        let short = price - (currency == .fish ? data.wallet : data.golden)
        let currencyName = model.ui(currency == .fish ? "fish" : "golden_fish_count")
        return Button {
            if data.unlock(current.id, currency) {
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
            VStack(spacing: 1) {
                HStack(spacing: 6) {
                    if currency == .fish {
                        PixelIcon(sprite: "fish", height: 20)
                    } else {
                        GoldenFishIcon(height: 20)
                    }
                    OutlinedText(text: "\(price)", size: 20)
                }
                if short > 0 {
                    Text(model.ui("need_more").replacingOccurrences(of: "{n}", with: "\(short)"))
                        .font(.pixel(10))
                        .opacity(0.9)
                        .lineLimit(1)
                        .minimumScaleFactor(0.7)
                }
            }
        }
        .buttonStyle(ChunkyButtonStyle(kind: currency == .fish ? .primary : .golden, padding: 6))
        .frame(height: 52)
        .disabled(short > 0)
        .saturation(short > 0 ? 0 : 1)
        .opacity(short > 0 ? 0.7 : 1)
        .accessibilityLabel("\(model.ui("unlock")) \(current.name), \(price) \(currencyName)")
        .accessibilityValue(short > 0 ? model.ui("need_more").replacingOccurrences(of: "{n}", with: "\(short)") : "")
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
        /// Golden fish it costs instead; nil for the free cat.
        let goldenPrice: Int?
        let owned: Bool
        /// The cut-out portrait image asset (`cat_<id>`).
        let portrait: String
        /// The hero sprite it wears (`hero_<id>`, or `hero` for Fluffy), when drawn.
        let sprite: String?
    }

    let cats: [Cat]
    let wallet: Int
    /// Golden fish to spend.
    let golden: Int
    let selected: String
    /// Pays for and gives the cat with fish or golden fish; false if it can't be afforded.
    let unlock: (String, Currency) -> Bool
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
    var compact = false

    var body: some View {
        HStack(spacing: compact ? 4 : 6) {
            PixelIcon(sprite: "fish", height: compact ? 14 : 18)
            Text("\(amount)").font(.pixel(compact ? 13 : 16)).foregroundStyle(Color.menuPaper).monospacedDigit()
        }
        .padding(.horizontal, compact ? 8 : 12)
        .padding(.vertical, compact ? 5 : 6)
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

    /// The hero sprite a cat wears: its recoloured `hero_<id>` once drawn; the free cat (Fluffy) is `hero` itself.
    func heroSprite(for skin: String) -> String? {
        let skinned = "hero_\(skin)"
        if sprites.sheet(skinned) != nil { return skinned }
        return skin == SaveGame.defaultSkin && sprites.sheet("hero") != nil ? "hero" : nil
    }

    /// TEMPORARY (shown-cats): only the cats whose art is painted are listed on the CATS screen; the others
    /// stay in the catalog and in saves, just hidden. Remove to list every cat again; Tools/release-check.sh warns.
    static let shownCats: Set<String> = ["fluffy", "sakura", "cabage", "sharky"]

    /// The CATS screen's view of the shop (rules and saving are GameCore's `Skin` and `SaveGame`).
    var catsScreenModel: CatsScreenModel {
        let cats = Skin.catalog.filter { Self.shownCats.contains($0.id) }.map { skin in
            CatsScreenModel.Cat(id: skin.id, name: text(skin.nameKey), description: text(skin.descriptionKey),
                                price: skin.price, goldenPrice: skin.goldenPrice, owned: ownedSkins.contains(skin.id), portrait: "cat_\(skin.id)",
                                sprite: heroSprite(for: skin.id))
        }
        return CatsScreenModel(cats: cats, wallet: fishWallet, golden: goldenFish, selected: selectedSkin,
                               unlock: { [weak self] id, currency in self?.unlockSkin(id, with: currency) == .unlocked },
                               select: { [weak self] id in _ = self?.selectSkin(id) })
    }
}

/// The screen's leafy wooden title plank (`title_plank`, the painted CATS plank with its lettering taken
/// out) lettered from Lore.json, so the heading can be renamed there.
struct TitlePlank: View {
    let text: String

    var body: some View {
        Image("title_plank")
            .resizable().interpolation(.high).scaledToFit()
            .overlay {
                GeometryReader { box in
                    // Between the two painted paws, on the plank's middle line.
                    PixelTitle(text: text, size: box.size.height * 0.34, alignment: .center, tint: .menuPaper)
                        .frame(width: box.size.width * 0.56)
                        .position(x: box.size.width * 0.5, y: box.size.height * 0.56)
                }
            }
            .accessibilityElement(children: .ignore)
            .accessibilityLabel(text)
            .accessibilityAddTraits(.isHeader)
    }
}
