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
    @ViewBuilder let header: (_ width: CGFloat, _ maxHeight: CGFloat) -> Header
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
            header(width, headerHeight).padding(.top, top)
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
        return HStack(alignment: .center, spacing: 20) {
            header(headerWidth, headerHeight)
                .frame(width: headerWidth)
            VStack(spacing: 12) {
                card(true)
                buttons(true)
            }
            .frame(width: columnWidth)
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
        ZStack {
            MenuBackground(pose: .happy, celebrate: true, groundShare: MenuView.groundShare, wideHeroPlace: 0.12)
            ResultLayout(figureHeight: 0.85, cardHeight: (230, 200)) { width, maxHeight in
                WreathTitle(text: model.ui("level_complete"), wreath: "title_wreath_small", width: width,
                            maxHeight: maxHeight, topper: ["cheer", "idle"], topperSink: 0.3,
                            sunburst: true, fish: true)
            } card: { compact in
                card(summary, compact: compact)
            } buttons: { compact in
                ResultButtons(summary: summary, compact: compact)
            }
        }
    }

    private func card(_ summary: ResultSummary, compact: Bool) -> some View {
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
        .parchmentCard()
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
            ResultLayout(figureHeight: 1.3, cardHeight: (200, 180)) { width, maxHeight in
                VStack(spacing: 6) {
                    livesRow
                    WreathTitle(text: model.ui("game_over"), wreath: "title_wreath_stone", width: width,
                                maxHeight: max(80, maxHeight - 44), fish: true, leaves: true, allGradient: true)
                }
            } card: { compact in
                card(summary, compact: compact)
            } buttons: { compact in
                ResultButtons(summary: summary, gameOver: true, compact: compact)
            }
        }
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
