import GameCore
import SwiftUI

/// The end of a run: the level-complete screen after a win, the game-over screen otherwise. Both
/// share the wreath title, the parchment score card and the chunky buttons.
struct ResultView: View {
    let levelIndex: Int
    let result: GameResult

    var body: some View {
        if result.won {
            LevelCompleteView(levelIndex: levelIndex, result: result)
        } else {
            GameOverView(levelIndex: levelIndex, result: result)
        }
    }
}

/// What both end screens report, worked out once from the result, the endless run and the save.
@MainActor
struct ResultSummary {
    let model: AppModel
    let levelIndex: Int
    let result: GameResult

    var level: LevelDefinition { model.levels[levelIndex] }
    /// The score this screen is about: the whole run in endless, the level otherwise.
    var score: Int { model.endless?.score ?? result.score }
    var savedBest: Int { model.endless != nil ? model.save.bestEndlessScore : model.save.bestScores[level.id] ?? 0 }
    /// Only a finished level counts toward its best; an endless run always counts.
    var counts: Bool { model.endless != nil || result.won }
    var best: Int { counts ? max(savedBest, score) : savedBest }
    /// The save already holds this run by the time the screen shows, so a score equal to the best is new.
    var isNewBest: Bool { counts && score > 0 && score >= savedBest }

    var medal: Medal? {
        if let run = model.endless { return Medal.forEndless(cleared: run.cleared, levelCount: model.levels.count) }
        return Medal.forLevel(won: result.won, hearts: result.hearts, maxHearts: HeroStats().maxHearts)
    }

    /// The number of the level the run got to. In an endless run this counts on across loops (the
    /// sixth level reached is 6, not level 2 of loop 2), from the levels the run has beaten.
    var levelReached: Int {
        if let run = model.endless { return run.cleared + 1 }
        return levelIndex + 1
    }

    /// Fish picked up in the level just played, and how many it holds.
    var fish: (collected: Int, total: Int) { (result.fish, level.fishTotal) }

    /// "LEVEL 1 — THE PURRWOOD FOREST".
    var levelLine: String {
        "\(model.ui("level")) \(levelIndex + 1) — \(model.text(level.nameKey).uppercased())"
    }

    var newAbilities: [String] {
        result.unlocked.map { "\(model.ui("new_ability")): \(model.text("ability.\($0.rawValue)").uppercased())" }
    }

    /// Plays the same thing again: the level, or a fresh endless run.
    func retry() {
        if model.endless != nil { model.startEndless() } else { model.start(level: levelIndex) }
    }

    var nextLevelOpen: Bool { model.endless == nil && result.won && model.isUnlocked(levelIndex + 1) }
}

// MARK: - Shared pieces

/// SCORE and (NEW) BEST with dotted leaders.
private struct ScoreRows: View {
    @Environment(AppModel.self) private var model
    let summary: ResultSummary
    var compact = false

    var body: some View {
        let size: CGFloat = compact ? 12 : 14
        VStack(spacing: compact ? 6 : 9) {
            LeaderRow(label: model.ui("score"), size: size) { number(summary.score, size: size) }
            LeaderRow(label: model.ui("best"), badge: summary.isNewBest ? model.ui("new") : nil, size: size) {
                number(summary.best, size: size)
            }
        }
    }

    private func number(_ value: Int, size: CGFloat) -> some View {
        Text("\(value)").font(.pixel(size * 1.45)).monospacedDigit()
    }
}

/// FISH COLLECTED ……… 🐟 3/4, with the fish sprite.
private struct FishRow: View {
    @Environment(AppModel.self) private var model
    let summary: ResultSummary
    var compact = false

    var body: some View {
        let size: CGFloat = compact ? 12 : 14
        LeaderRow(label: model.ui("fish_collected"), size: size) {
            HStack(spacing: 6) {
                PixelIcon(sprite: "fish", height: size * 1.4)
                Text("\(summary.fish.collected)/\(summary.fish.total)").font(.pixel(size * 1.3))
            }
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(model.ui("fish_collected")) \(summary.fish.collected)/\(summary.fish.total)")
    }
}

/// The two end screens' buttons: a wide orange one, and cream ones under it.
private struct ResultButtons: View {
    @Environment(AppModel.self) private var model
    let summary: ResultSummary
    /// Game over: RETRY and MENU are both wide. Level complete: NEXT LEVEL wide, RETRY and MENU in a row.
    var gameOver = false
    var compact = false

    var body: some View {
        let primaryHeight: CGFloat = compact ? 48 : 56
        let secondaryHeight: CGFloat = compact ? 44 : 52
        VStack(spacing: compact ? 8 : 10) {
            if gameOver || !summary.nextLevelOpen {
                PrimaryButton(title: model.ui("retry"), icon: "icon_retry", height: primaryHeight, fontSize: compact ? 22 : 26,
                              action: summary.retry)
                SecondaryButton(title: model.ui("menu"), icon: "icon_home", layout: .iconLeading,
                                height: secondaryHeight, fontSize: compact ? 18 : 22) { model.quit() }
            } else {
                PrimaryButton(title: model.ui("next_level"), icon: "icon_play", height: primaryHeight,
                              fontSize: compact ? 20 : 24) { model.start(level: summary.levelIndex + 1) }
                HStack(spacing: 12) {
                    SecondaryButton(title: model.ui("retry"), icon: "icon_retry", layout: .iconTrailing,
                                    height: secondaryHeight, fontSize: compact ? 15 : 17, action: summary.retry)
                    SecondaryButton(title: model.ui("menu"), icon: "icon_home", layout: .iconLeading,
                                    height: secondaryHeight, fontSize: compact ? 15 : 17) { model.quit() }
                }
            }
        }
    }
}

/// Shared frame of both end screens. Upright: header, card, then the hero in the scene and the
/// buttons on the earth. On its side the hero is on the left, the header in a middle column and
/// the card over the buttons on the right.
private struct ResultLayout<Header: View, Card: View, Buttons: View>: View {
    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale
    /// How far above the ground line the scene's figure reaches, in hero heights.
    let figureHeight: CGFloat
    /// Estimated card heights (upright, compact), so the header gets the rest.
    let cardHeight: (tall: CGFloat, wide: CGFloat)
    /// On its side too, the card goes straight under the header in one column (so it can cover the
    /// game-over title's cut edge), with the buttons in a column beside it.
    var titleOverCard = false
    /// The header gets its column width, the height it may use, and the screen width.
    @ViewBuilder let header: (_ width: CGFloat, _ maxHeight: CGFloat, _ screenWidth: CGFloat) -> Header
    @ViewBuilder let card: (_ compact: Bool) -> Card
    @ViewBuilder let buttons: (_ compact: Bool) -> Buttons

    static var groundShare: CGFloat { MenuView.groundShare }
    static var wideHeroPlace: CGFloat { 0.12 }

    var body: some View {
        ScreenFrame { size, insets in
            if size.width > size.height { wide(size: size, insets: insets) } else { tall(size: size, insets: insets) }
        }
    }

    private func tall(size: CGSize, insets: EdgeInsets) -> some View {
        let unit = MenuScene.pointsPerUnit(viewSize: size, displayScale: displayScale)
        let ground = (size.height * Self.groundShare).rounded()
        let figureTop = ground + MenuScene.heroHeight(model.sprites) * figureHeight * unit
        let side = max(16, insets.leading)
        let width = min(size.width - 2 * side, 380)
        let top = insets.top + 8
        let headerHeight = max(120, size.height - figureTop - top - cardHeight.tall - 16)
        return VStack(spacing: 0) {
            header(width, headerHeight, size.width).padding(.top, top)
            card(false).frame(width: width).padding(.top, 6)
            Spacer(minLength: 0)
            buttons(false)
                .frame(width: width)
                .padding(.top, 14)
                .frame(height: ground, alignment: .top)
        }
        .frame(maxWidth: .infinity)
    }

    private func wide(size: CGSize, insets: EdgeInsets) -> some View {
        let start = max(size.width * 0.25, insets.leading + 150)
        let end = max(insets.trailing, 16)
        let available = size.width - start - end
        let headerWidth = (available - 20) * 0.45
        let columnWidth = min(360, available - 20 - headerWidth)
        let top = insets.top + 10
        let bottom = max(insets.bottom, 10) + 6
        let headerHeight = size.height - top - bottom
        let stackWidth = min(360, (available - 20) * 0.6)
        return HStack(alignment: .center, spacing: 20) {
            if titleOverCard {
                // Header over the card, as upright; the header shrinks to leave the card its height.
                VStack(spacing: 6) {
                    header(stackWidth, headerHeight - cardHeight.wide - 6, size.width)
                    card(true)
                }
                .frame(width: stackWidth)
                buttons(true)
                    .frame(width: min(280, available - 20 - stackWidth))
            } else {
                header(headerWidth, headerHeight, size.width)
                    .frame(width: headerWidth)
                VStack(spacing: 12) {
                    card(true)
                    buttons(true)
                }
                .frame(width: columnWidth)
            }
        }
        .padding(.top, top)
        .padding(.bottom, bottom)
        .padding(.leading, start)
        .padding(.trailing, end)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .leading)
    }
}

// MARK: - Level complete

/// After a won level: sunburst, confetti and sparkles, the hero cheering over the wreath title, the
/// card with stars, score, best, level and fish, the hero sitting happily below, and the buttons.
struct LevelCompleteView: View {
    @Environment(AppModel.self) private var model
    let levelIndex: Int
    let result: GameResult

    var body: some View {
        let summary = ResultSummary(model: model, levelIndex: levelIndex, result: result)
        if let look = CompleteLook.forTheme(summary.level.background) {
            PaintedCompleteView(look: look, summary: summary) { compact in
                Self.cardContent(summary, compact: compact)
            }
        } else {
            standard(summary)
        }
    }

    /// The Purrwood look: the hero sitting in the menu's morning under the wreath title.
    private func standard(_ summary: ResultSummary) -> some View {
        ZStack {
            MenuBackground(pose: .happy, celebrate: true, groundShare: MenuView.groundShare, wideHeroPlace: 0.12)
            ResultLayout(figureHeight: 0.85, cardHeight: (230, 200)) { width, maxHeight, _ in
                WreathTitle(text: model.ui("level_complete"), wreath: "title_wreath_small", width: width,
                            maxHeight: maxHeight, topper: [TitleFigure.cheer.drawn(from: model.heroSprite), .cheer, .idle],
                            sunburst: true, fish: true)
            } card: { compact in
                card(summary, compact: compact)
            } buttons: { compact in
                ResultButtons(summary: summary, compact: compact)
            }
        }
    }

    private func card(_ summary: ResultSummary, compact: Bool) -> some View {
        Self.cardContent(summary, compact: compact).parchmentCard()
    }

    /// What the card says: stars, score, best, the level and its fish, and any ability just learnt.
    fileprivate static func cardContent(_ summary: ResultSummary, compact: Bool) -> some View {
        VStack(spacing: compact ? 7 : 10) {
            MedalStars(medal: summary.medal, size: compact ? 22 : 30)
                .padding(.bottom, compact ? 0 : 4)
            ScoreRows(summary: summary, compact: compact)
            CardDivider()
            Text(summary.levelLine)
                .font(.pixel(compact ? 11 : 12))
                .foregroundStyle(Color.parchmentInk)
                .lineLimit(1)
                .minimumScaleFactor(0.6)
            FishRow(summary: summary, compact: compact)
            ForEach(summary.newAbilities, id: \.self) { line in
                Text(line)
                    .font(.pixel(compact ? 10 : 11))
                    .foregroundStyle(Color.menuOrangeDeep)
                    .lineLimit(1)
                    .minimumScaleFactor(0.6)
            }
        }
    }
}

// MARK: - A world's own level-complete screen

/// A world's own level-complete look, from the user's painting of it (one sheet per level theme, cut by
/// `complete_looks()` in Tools/sprites/export.py into `<piece>_complete_<theme>`): the title, the world's boss, the
/// card's frame, the three buttons and a few loose decorations. Keyed by the level's background theme, so every
/// level of that world gets it; other worlds keep the Purrwood look. Sizes, and where the card's text and the
/// buttons' labels go (the painted sample text was taken out there), are in the cut pieces' pixels.
struct CompleteLook {
    let theme: String
    let titleSize: CGSize
    let bossSize: CGSize
    /// The boss's bottom is a straight cut (it stands on a wall that goes on): it fades out.
    var bossFades = false
    let cardSize: CGSize
    /// The card's empty parchment, where its text goes.
    let parchment: CGRect
    let next: PaintedButtonArt
    let retry: PaintedButtonArt
    let menu: PaintedButtonArt
    /// Small loose pieces floating over the title's top corners.
    var decorations: [(piece: String, size: CGSize)] = []

    func image(_ piece: String) -> String { "\(piece)_complete_\(theme)" }

    static func forTheme(_ theme: String) -> CompleteLook? { all[theme] }

    static let all: [String: CompleteLook] = [
        "frost": CompleteLook(
            theme: "frost", titleSize: CGSize(width: 533, height: 455), bossSize: CGSize(width: 546, height: 548),
            cardSize: CGSize(width: 732, height: 673), parchment: CGRect(x: 115, y: 161, width: 498, height: 366),
            next: PaintedButtonArt(piece: "next", size: CGSize(width: 629, height: 176),
                                   label: CGRect(x: 120, y: 44, width: 445, height: 78)),
            retry: PaintedButtonArt(piece: "retry", size: CGSize(width: 422, height: 142),
                                    label: CGRect(x: 108, y: 27, width: 236, height: 73)),
            menu: PaintedButtonArt(piece: "menu", size: CGSize(width: 366, height: 134),
                                   label: CGRect(x: 83, y: 26, width: 204, height: 73)),
            decorations: [("flake", CGSize(width: 100, height: 112)), ("crystal", CGSize(width: 51, height: 103))]),
        "haunted": CompleteLook(
            theme: "haunted", titleSize: CGSize(width: 613, height: 405), bossSize: CGSize(width: 411, height: 594),
            cardSize: CGSize(width: 622, height: 635), parchment: CGRect(x: 99, y: 172, width: 404, height: 354),
            next: PaintedButtonArt(piece: "next", size: CGSize(width: 695, height: 166),
                                   label: CGRect(x: 190, y: 60, width: 379, height: 60)),
            retry: PaintedButtonArt(piece: "retry", size: CGSize(width: 351, height: 113),
                                    label: CGRect(x: 98, y: 30, width: 192, height: 61)),
            menu: PaintedButtonArt(piece: "menu", size: CGSize(width: 316, height: 113),
                                   label: CGRect(x: 54, y: 30, width: 184, height: 61)),
            decorations: [("ghost", CGSize(width: 124, height: 130)), ("flame", CGSize(width: 59, height: 109))]),
        "citadel": CompleteLook(
            theme: "citadel", titleSize: CGSize(width: 568, height: 375), bossSize: CGSize(width: 454, height: 642),
            bossFades: true,
            cardSize: CGSize(width: 589, height: 574), parchment: CGRect(x: 86, y: 142, width: 408, height: 340),
            next: PaintedButtonArt(piece: "next", size: CGSize(width: 638, height: 175),
                                   label: CGRect(x: 100, y: 51, width: 438, height: 87)),
            retry: PaintedButtonArt(piece: "retry", size: CGSize(width: 348, height: 121),
                                    label: CGRect(x: 87, y: 22, width: 188, height: 67)),
            menu: PaintedButtonArt(piece: "menu", size: CGSize(width: 331, height: 121),
                                   label: CGRect(x: 60, y: 22, width: 198, height: 67))),
    ]
}

/// One painted button and where its label goes, in its pixels.
struct PaintedButtonArt {
    let piece: String
    let size: CGSize
    let label: CGRect

    var aspect: CGFloat { size.height / size.width }
}

/// The level-complete screen in a world's own look (`CompleteLook`), over that world's scenery. Upright: the title
/// with the boss beside it, the card, NEXT LEVEL, then RETRY and MENU, all shrunk together when the screen is short.
/// On its side: the title and boss over the buttons on the left, the card on the right.
private struct PaintedCompleteView<Card: View>: View {
    @Environment(AppModel.self) private var model
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    let look: CompleteLook
    let summary: ResultSummary
    @ViewBuilder let card: (_ compact: Bool) -> Card
    @State private var floating = false

    private static var spacing: CGFloat { 8 }
    /// The boss stands this much taller than the title, and this share of its width tucks behind the title.
    private static var bossGrowth: CGFloat { 1.15 }
    private static var bossTuck: CGFloat { 0.18 }

    var body: some View {
        ZStack {
            MenuBackground(pose: .empty, theme: look.theme, celebrate: true)
            Color.black.opacity(0.2).ignoresSafeArea()
            ScreenFrame { size, insets in
                if size.width > size.height { wide(size: size, insets: insets) } else { tall(size: size, insets: insets) }
            }
        }
        .onAppear {
            guard !reduceMotion else { return }
            withAnimation(.easeInOut(duration: 1.8).repeatForever(autoreverses: true)) { floating = true }
        }
    }

    // MARK: Layout

    private func tall(size: CGSize, insets: EdgeInsets) -> some View {
        let side = max(12, insets.leading)
        let top = insets.top + 4
        let available = size.height - top - max(insets.bottom, 10)
        var width = min(size.width - 2 * side, 420)
        let natural = headerHeight(width: width) + width * look.cardSize.height / look.cardSize.width
            + buttonsHeight(width: width)
        if natural + 3 * Self.spacing > available {
            width *= (available - 3 * Self.spacing) / natural
        }
        return VStack(spacing: Self.spacing) {
            header(width: width, maxHeight: .infinity)
            cardView(width: width)
            buttons(width: width)
        }
        .frame(width: width)
        .padding(.top, top)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .top)
    }

    private func wide(size: CGSize, insets: EdgeInsets) -> some View {
        let leading = max(insets.leading, 16), trailing = max(insets.trailing, 16)
        let top = max(insets.top, 8), bottom = max(insets.bottom, 8)
        let availableWidth = size.width - leading - trailing
        let availableHeight = size.height - top - bottom
        let cardAspect = look.cardSize.height / look.cardSize.width
        let cardWidth = min(availableHeight / cardAspect, availableWidth * 0.52)
        let column = availableWidth - cardWidth - 16
        let buttonsWidth = min(column, 360)
        let headerRoom = availableHeight - buttonsHeight(width: buttonsWidth) - Self.spacing
        return HStack(spacing: 16) {
            VStack(spacing: Self.spacing) {
                header(width: column, maxHeight: headerRoom)
                    .frame(maxHeight: .infinity)
                buttons(width: buttonsWidth)
            }
            .frame(width: column)
            cardView(width: cardWidth)
                .frame(maxHeight: .infinity)
        }
        .padding(.top, top)
        .padding(.bottom, bottom)
        .padding(.leading, leading)
        .padding(.trailing, trailing)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    /// The title's height in a header `width` wide (the boss beside it, part of it tucked behind).
    private func titleHeight(width: CGFloat) -> CGFloat {
        let title = look.titleSize.width / look.titleSize.height
        let boss = look.bossSize.width / look.bossSize.height
        return width / (title + Self.bossGrowth * boss * (1 - Self.bossTuck))
    }

    private func headerHeight(width: CGFloat) -> CGFloat { titleHeight(width: width) * Self.bossGrowth }

    private func buttonsHeight(width: CGFloat) -> CGFloat {
        let half = (width - 10) / 2
        return width * 0.92 * look.next.aspect + half * max(look.retry.aspect, look.menu.aspect) + Self.spacing
    }

    // MARK: Pieces

    /// The title with the boss beside it, both standing on the header's bottom, and the loose decorations
    /// floating over the title's top corners.
    private func header(width: CGFloat, maxHeight: CGFloat) -> some View {
        let height = min(titleHeight(width: width), maxHeight / Self.bossGrowth)
        let titleWidth = height * look.titleSize.width / look.titleSize.height
        let bossHeight = height * Self.bossGrowth
        let bossWidth = bossHeight * look.bossSize.width / look.bossSize.height
        return HStack(alignment: .bottom, spacing: -bossWidth * Self.bossTuck) {
            Image(look.image("title"))
                .resizable()
                .interpolation(.high)
                .frame(width: titleWidth, height: height)
                .accessibilityLabel(model.ui("level_complete"))
                .accessibilityAddTraits(.isHeader)
                .overlay(alignment: .topLeading) { decorations(titleWidth: titleWidth, height: height) }
                .zIndex(1)
            Image(look.image("boss"))
                .resizable()
                .interpolation(.high)
                .frame(width: bossWidth, height: bossHeight)
                .mask {
                    LinearGradient(stops: [.init(color: .black, location: look.bossFades ? 0.8 : 1),
                                           .init(color: .clear, location: 1)],
                                   startPoint: .top, endPoint: .bottom)
                }
                .accessibilityHidden(true)
        }
        .frame(width: width)
    }

    @ViewBuilder
    private func decorations(titleWidth: CGFloat, height: CGFloat) -> some View {
        let spots: [CGPoint] = [CGPoint(x: -0.02, y: 0.02), CGPoint(x: 0.9, y: -0.04)]
        ForEach(Array(zip(look.decorations.indices, spots)), id: \.0) { index, spot in
            let piece = look.decorations[index]
            let pieceHeight = height * (index == 0 ? 0.24 : 0.2)
            Image(look.image(piece.piece))
                .resizable()
                .interpolation(.high)
                .frame(width: pieceHeight * piece.size.width / piece.size.height, height: pieceHeight)
                .offset(x: titleWidth * spot.x, y: height * spot.y + (floating == (index == 0) ? -4 : 4))
                .accessibilityHidden(true)
        }
    }

    private func cardView(width: CGFloat) -> some View {
        let scale = width / look.cardSize.width
        let parchment = look.parchment
        let inner = CGSize(width: parchment.width * scale, height: parchment.height * scale)
        return Image(look.image("card"))
            .resizable()
            .interpolation(.high)
            .frame(width: width, height: look.cardSize.height * scale)
            .overlay(alignment: .topLeading) {
                FitInside(size: inner) { card(inner.height < 230) }
                    .offset(x: parchment.minX * scale, y: parchment.minY * scale)
            }
    }

    private func buttons(width: CGFloat) -> some View {
        let half = (width - 10) / 2
        return VStack(spacing: Self.spacing) {
            if summary.nextLevelOpen {
                PaintedButton(art: look.next, theme: look.theme, title: model.ui("next_level"), icon: "icon_play",
                              primary: true, width: width * 0.92) { model.start(level: summary.levelIndex + 1) }
                HStack(spacing: 10) {
                    PaintedButton(art: look.retry, theme: look.theme, title: model.ui("retry"), icon: "icon_retry",
                                  width: half, action: summary.retry)
                    PaintedButton(art: look.menu, theme: look.theme, title: model.ui("menu"), icon: "icon_home",
                                  iconLeading: true, width: half) { model.quit() }
                }
            } else {
                PaintedButton(art: look.next, theme: look.theme, title: model.ui("retry"), icon: "icon_retry",
                              primary: true, width: width * 0.92, action: summary.retry)
                PaintedButton(art: look.menu, theme: look.theme, title: model.ui("menu"), icon: "icon_home",
                              iconLeading: true, width: half) { model.quit() }
            }
        }
    }
}

/// Lays its content out in `size`'s width and shrinks it (never grows it) until it is no taller than `size`.
private struct FitInside<Content: View>: View {
    let size: CGSize
    @ViewBuilder let content: Content
    @State private var natural: CGFloat = 0

    var body: some View {
        let scale = natural > size.height ? size.height / natural : 1
        content
            .frame(width: size.width / scale)
            .fixedSize(horizontal: false, vertical: true)
            .onGeometryChange(for: CGFloat.self) { $0.size.height } action: { natural = $0 }
            .scaleEffect(scale)
            .frame(width: size.width, height: size.height)
    }
}

/// A painted button with its label set where the painted one was: outlined cream lettering on the orange one,
/// dark on the cream ones, with the icon beside it. It sinks a little and darkens while held.
private struct PaintedButton: View {
    let art: PaintedButtonArt
    let theme: String
    let title: String
    let icon: String
    var iconLeading = false
    var primary = false
    let width: CGFloat
    let action: () -> Void

    var body: some View {
        Button(action: action) { EmptyView() }
            .buttonStyle(Style(button: self))
            .frame(width: width, height: width * art.aspect)
            .accessibilityLabel(title)
    }

    private struct Style: ButtonStyle {
        let button: PaintedButton

        func makeBody(configuration: Configuration) -> some View {
            let art = button.art
            let scale = button.width / art.size.width
            let box = CGSize(width: art.label.width * scale, height: art.label.height * scale)
            let pressed = configuration.isPressed
            Image("\(art.piece)_complete_\(button.theme)")
                .resizable()
                .interpolation(.high)
                .overlay(alignment: .topLeading) {
                    label(box: box)
                        .frame(width: box.width, height: box.height)
                        .offset(x: art.label.minX * scale, y: art.label.minY * scale)
                }
                .brightness(pressed ? -0.12 : 0)
                .offset(y: pressed ? 2 : 0)
                .contentShape(Rectangle())
        }

        @ViewBuilder
        private func label(box: CGSize) -> some View {
            let iconSlot: CGFloat = 1.6
            // The pixel font is monospaced, its letters about 0.62 of its size wide.
            let fitted = box.width / (CGFloat(button.title.count) * 0.62 + iconSlot)
            let size = min(box.height * (button.primary ? 0.5 : 0.46), fitted)
            HStack(spacing: size * 0.4) {
                if button.iconLeading { PixelIcon(sprite: button.icon, height: size * 1.2) }
                if button.primary {
                    OutlinedText(text: button.title, size: size)
                } else {
                    Text(button.title).font(.pixel(size)).foregroundStyle(Color.menuInk).lineLimit(1)
                }
                if !button.iconLeading { PixelIcon(sprite: button.icon, height: size * 1.1) }
            }
        }
    }
}

// MARK: - Game over

/// After a lost run: a dead-cat head per heart lost, GAME OVER on its stone wreath with leaves
/// drifting round it, the card, the hero out cold below with its ghost bobbing over it, then RETRY
/// and MENU.
struct GameOverView: View {
    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale
    let levelIndex: Int
    let result: GameResult

    /// Heads shown: one per heart lost, and at least one (a fall into a ravine can end a run with
    /// hearts left).
    private var livesLost: Int {
        max(1, HeroStats().maxHearts - max(0, result.hearts))
    }

    var body: some View {
        let summary = ResultSummary(model: model, levelIndex: levelIndex, result: result)
        ZStack {
            MenuBackground(pose: .knockedOut, groundShare: MenuView.groundShare, wideHeroPlace: 0.12)
            ResultLayout(figureHeight: 1.3, cardHeight: (200, 180), titleOverCard: true) { width, maxHeight, screenWidth in
                title(width: width, maxHeight: maxHeight, screenWidth: screenWidth)
            } card: { compact in
                card(summary, compact: compact)
            } buttons: { compact in
                ResultButtons(summary: summary, gameOver: true, compact: compact)
            }
        }
    }

    /// Upright the title is about four fifths of the screen wide, as in the reference; on its side it
    /// fills the column it shares with the card, shrunk to the height left above the card.
    private static let titleShare: CGFloat = 0.82
    /// How far the card covers the title image's straight bottom edge (the card follows it 6 pt down).
    private static let cardOverlap: CGFloat = 6
    /// How far the heads sit down over the top of the title's leaves.
    private static let headsOverlap: CGFloat = 10

    /// The heads lost over the reference title art: the stone slab with GAME OVER, its leaves and the
    /// fish, as one image (`title_game_over`, cut from the reference, not pixel-grid art, so it is
    /// scaled smoothly). The words still come from Lore.json for VoiceOver.
    private func title(width: CGFloat, maxHeight: CGFloat, screenWidth: CGFloat) -> some View {
        let titleWidth = min(width, (screenWidth * Self.titleShare).rounded())
        return VStack(spacing: -Self.headsOverlap) {
            livesRow.zIndex(1)
            Image("title_game_over")
                .resizable()
                .interpolation(.high)
                .scaledToFit()
                .frame(maxWidth: titleWidth, maxHeight: max(80, maxHeight - 32 + Self.headsOverlap))
                .accessibilityLabel(model.ui("game_over"))
                .accessibilityAddTraits(.isHeader)
        }
        // The card follows straight under the title (both orientations): tuck the cut edge behind it.
        .padding(.bottom, -(6 + Self.cardOverlap))
    }

    private var livesRow: some View {
        HStack(spacing: 10) {
            ForEach(0..<livesLost, id: \.self) { _ in
                PixelIcon(sprite: "life_lost", height: 32)
            }
        }
        .accessibilityHidden(true)
    }

    private func card(_ summary: ResultSummary, compact: Bool) -> some View {
        let size: CGFloat = compact ? 12 : 14
        return VStack(spacing: compact ? 7 : 10) {
            ScoreRows(summary: summary, compact: compact)
            CardDivider()
            LeaderRow(label: model.ui("level_reached"), size: size) {
                Text("\(summary.levelReached)").font(.pixel(size * 1.45))
            }
            CardDivider()
            FishRow(summary: summary, compact: compact)
        }
        .parchmentCard()
    }
}

#Preview("Level complete") {
    ResultView(levelIndex: 0, result: GameResult(won: true, score: 1280, xp: 320, heroLevel: 3, hearts: 3, fish: 4,
                                                 unlocked: [.doublePounce]))
        .environment(AppModel())
}

#Preview("Game over") {
    ResultView(levelIndex: 2, result: GameResult(won: false, score: 320, xp: 120, heroLevel: 2, hearts: 0, fish: 2,
                                                 unlocked: []))
        .environment(AppModel())
}
