import GameCore
import StoreKit
import SwiftUI

/// The golden fish icon: the generated `golden_fish` sprite once the artist has drawn it, until then
/// the fish sprite turned gold (greyed, brightened, then tinted; the outline stays dark).
struct GoldenFishIcon: View {
    @Environment(AppModel.self) private var model
    var height: CGFloat = 18

    var body: some View {
        if model.sprites.sheet("golden_fish") != nil {
            PixelIcon(sprite: "golden_fish", height: height)
        } else {
            PixelIcon(sprite: "fish", height: height)
                .saturation(0)
                .brightness(0.2)
                .colorMultiply(Color.menuGold)
        }
    }
}

extension Color {
    /// Golden fish: their icon tint and the fill of golden buttons.
    static let menuGold = Color(red: 1.0, green: 0.78, blue: 0.2)
}

/// The golden fish balance on a dark pill with a gold edge and a plus: tapping it opens the packs.
struct GoldenWallet: View {
    @Environment(AppModel.self) private var model
    let amount: Int
    var compact = false
    let open: () -> Void

    var body: some View {
        Button(action: open) {
            HStack(spacing: compact ? 4 : 6) {
                GoldenFishIcon(height: compact ? 14 : 18)
                Text("\(amount)").font(.pixel(compact ? 13 : 16)).foregroundStyle(Color.menuGold).monospacedDigit()
                Image(systemName: "plus.circle.fill")
                    .font(.system(size: compact ? 13 : 16, weight: .black))
                    .foregroundStyle(Color.menuGold)
            }
            .padding(.horizontal, compact ? 8 : 12)
            .padding(.vertical, compact ? 5 : 6)
            .background(Color.menuInk.opacity(0.85), in: Capsule())
            .overlay(Capsule().stroke(Color.menuGold.opacity(0.8), lineWidth: 2.5))
            .contentShape(Capsule())
        }
        .buttonStyle(.plain)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(amount) \(model.ui("golden_fish_count"))")
        .accessibilityHint(model.ui("get_golden"))
        .accessibilityAddTraits(.isButton)
    }
}

/// "Get golden fish": the four packs with their App Store prices, over a dimmed screen. Prices are
/// StoreKit's `displayPrice`, in the player's currency; nothing about money is written in the app.
struct GoldenShopOverlay: View {
    @Environment(AppModel.self) private var model
    let close: () -> Void

    var body: some View {
        ZStack {
            Color.black.opacity(0.55)
                .ignoresSafeArea()
                .onTapGesture(perform: dismiss)
                .accessibilityAddTraits(.isButton)
                .accessibilityAction(.escape, dismiss)
            GoldenShopPanel(close: dismiss)
                .padding(.horizontal, 20)
                .padding(.vertical, 10)
        }
        .task { await model.golden.loadProducts() }
    }

    private func dismiss() {
        guard model.golden.buying == nil else { return }
        model.golden.notice = nil
        close()
    }
}

private struct GoldenShopPanel: View {
    @Environment(AppModel.self) private var model
    let close: () -> Void

    var body: some View {
        let golden = model.golden
        VStack(spacing: 8) {
            PixelTitle(text: model.ui("get_golden"), size: 20, alignment: .center, splitFrom: 9)
            HStack(spacing: 6) {
                GoldenFishIcon(height: 16)
                Text("\(model.goldenFish)").font(.pixel(14)).monospacedDigit()
            }
            .foregroundStyle(Color.parchmentInk)
            .accessibilityElement(children: .ignore)
            .accessibilityLabel("\(model.goldenFish) \(model.ui("golden_fish_count"))")
            switch golden.status {
            case .loaded:
                // Two by two, so the panel stays short enough for a phone on its side.
                ScrollView {
                    LazyVGrid(columns: [GridItem(.flexible(), spacing: 8), GridItem(.flexible(), spacing: 8)],
                              spacing: 10) {
                        ForEach(GoldenFish.packs) { pack in
                            PackButton(pack: pack, product: golden.product(for: pack))
                        }
                    }
                    .padding(.vertical, 4)
                }
                .scrollBounceBehavior(.basedOnSize)
                .frame(maxHeight: 136)
            case .idle, .loading:
                ProgressView()
                    .tint(Color.parchmentInk)
                    .frame(height: 60)
                    .accessibilityLabel(model.ui("store_loading"))
            case .unavailable:
                Text(model.ui("store_unavailable"))
                    .font(.pixel(12))
                    .foregroundStyle(Color.parchmentInk)
                    .multilineTextAlignment(.center)
                    .fixedSize(horizontal: false, vertical: true)
                    .frame(minHeight: 40)
            }
            // The notice takes the hint's place, so the panel keeps its height on a phone on its side.
            if let notice = golden.notice {
                noticeLine(notice)
            } else {
                Text(model.ui("golden_hint"))
                .font(.pixel(10))
                .foregroundStyle(Color.parchmentInk.opacity(0.75))
                .multilineTextAlignment(.center)
                .lineLimit(2)
                .minimumScaleFactor(0.8)
                .fixedSize(horizontal: false, vertical: true)
            }
            HStack(spacing: 10) {
                if golden.status == .unavailable && golden.enabled {
                    SecondaryButton(title: model.ui("try_again"), height: 40, fontSize: 13) {
                        Task { await golden.loadProducts() }
                    }
                }
                SecondaryButton(title: model.ui("back"), height: 40, fontSize: 13, action: close)
                    .disabled(golden.buying != nil)
            }
        }
        .frame(maxWidth: 380)
        .parchmentCard()
    }

    private func noticeLine(_ notice: GoldenStore.Notice) -> some View {
        let text = switch notice {
        case .thanks: model.ui("golden_thanks")
        case .pending: model.ui("golden_pending")
        case .failed: model.ui("golden_failed")
        }
        return Text(text)
                .font(.pixel(11))
                .foregroundStyle(notice == .failed ? Color.badgeRed : Color.parchmentInk)
                .multilineTextAlignment(.center)
                .lineLimit(2)
                .minimumScaleFactor(0.8)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityAddTraits(.updatesFrequently)
    }
}

/// One pack: the golden fish it gives over its App Store price; a spinner while it is being bought.
private struct PackButton: View {
    @Environment(AppModel.self) private var model
    let pack: GoldenFish.Pack
    let product: Product?

    var body: some View {
        let golden = model.golden
        let busy = golden.buying == pack.productID
        Button {
            Task { await golden.buy(pack) }
        } label: {
            VStack(spacing: 3) {
                HStack(spacing: 5) {
                    GoldenFishIcon(height: 18)
                    OutlinedText(text: "\(pack.amount)", size: 18)
                }
                if busy {
                    ProgressView().tint(Color.menuInk).frame(height: 14)
                } else {
                    Text(product?.displayPrice ?? "–")
                        .font(.pixel(13))
                        .lineLimit(1)
                        .minimumScaleFactor(0.6)
                }
            }
        }
        .buttonStyle(ChunkyButtonStyle(kind: .golden, padding: 6))
        .frame(height: 58)
        .disabled(product == nil || golden.buying != nil)
        .opacity(product == nil || (golden.buying != nil && !busy) ? 0.6 : 1)
        .accessibilityLabel("\(pack.amount) \(model.ui("golden_fish_count")), \(product?.displayPrice ?? "")")
    }
}
