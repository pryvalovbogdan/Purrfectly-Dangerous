import GameCore
import SwiftUI

/// The end of a run: a title, a card with the medal, the score and the best score, then the buttons,
/// over the same backdrop as the start screen.
struct ResultView: View {
    @Environment(AppModel.self) private var model
    @Environment(\.verticalSizeClass) private var verticalSizeClass
    let levelIndex: Int
    let result: GameResult

    private var level: LevelDefinition { model.levels[levelIndex] }
    /// The score this screen is about: the whole run in endless, the level otherwise.
    private var score: Int { model.endless?.score ?? result.score }
    private var savedBest: Int { model.endless != nil ? model.save.bestEndlessScore : model.save.bestScores[level.id] ?? 0 }
    /// Only a finished level counts toward its best; an endless run always counts.
    private var counts: Bool { model.endless != nil || result.won }
    private var best: Int { counts ? max(savedBest, score) : savedBest }

    private var medal: Medal? {
        if let run = model.endless { return Medal.forEndless(cleared: run.cleared, levelCount: model.levels.count) }
        return Medal.forLevel(won: result.won, hearts: result.hearts, maxHearts: HeroStats().maxHearts)
    }

    var body: some View {
        let sideBySide = verticalSizeClass == .compact
        ZStack {
            MenuBackground(pose: result.won ? .standing : .fallen)
            GeometryReader { proxy in
                if sideBySide {
                    // The hero stands at the left edge here, so everything keeps to a centre column.
                    VStack(spacing: 12) {
                        title(size: 32)
                        card(notesBeside: true)
                        HStack(spacing: 10) { buttons }
                    }
                    .frame(width: min(420, proxy.size.width * 0.52))
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                } else {
                    VStack(spacing: 0) {
                        title(size: 40).padding(.top, 20)
                        card(notesBeside: false).padding(.top, 18)
                        Spacer(minLength: 0)
                        VStack(spacing: 8) { buttons }
                            .frame(height: proxy.size.height * (MenuScene.narrowGroundShare - 0.05), alignment: .top)
                    }
                    .frame(maxWidth: .infinity)
                }
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 14)
        }
    }

    private func title(size: CGFloat) -> some View {
        PixelTitle(text: result.won ? model.ui("level_cleared", "Level complete") : model.ui("game_over", "Game over"),
                   size: size, alignment: .center)
    }

    /// On a wide, short screen the small print goes between the medal and the numbers to save height.
    private func card(notesBeside: Bool) -> some View {
        VStack(spacing: 10) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 8) {
                    label(model.ui("medal", "MEDAL"))
                    MedalStars(medal: medal)
                }
                if notesBeside {
                    noteLines.padding(.top, 24).padding(.leading, 10)
                }
                Spacer(minLength: 8)
                VStack(alignment: .trailing, spacing: 2) {
                    label(model.ui("score", "SCORE"))
                    PixelTitle(text: "\(score)", size: 28, tint: .menuPaper).fixedSize()
                    HStack(spacing: 6) {
                        if counts, score > 0, score >= savedBest {
                            Text(model.ui("new_best", "NEW")).font(.pixel(9)).foregroundStyle(Color.menuPaper)
                                .padding(.horizontal, 4).padding(.vertical, 2)
                                .background(Color.red, in: Rectangle())
                        }
                        label(model.ui("best", "BEST"))
                    }
                    .padding(.top, 4)
                    PixelTitle(text: "\(best)", size: 28, tint: .menuPaper).fixedSize()
                }
            }
            if !notesBeside {
                noteLines.frame(maxWidth: .infinity, alignment: .leading)
            }
        }
        .padding(.vertical, 14)
        .padding(.horizontal, 6)
        .modifier(MenuPanel(fill: .cardFill))
    }

    private var noteLines: some View {
        VStack(alignment: .leading, spacing: 6) {
            ForEach(notes, id: \.self) { note in
                Text(note).font(.pixel(11)).foregroundStyle(Color.menuInk.opacity(0.8))
                    .lineLimit(1).minimumScaleFactor(0.7)
            }
        }
    }

    private func label(_ text: String) -> some View {
        Text(text).font(.pixel(12)).foregroundStyle(Color.cardInk)
    }

    /// The small print under the numbers: how far the run got, and anything it unlocked.
    private var notes: [String] {
        let fish = "\(model.ui("fish", "FISH")) ×\(result.fish)"
        if let run = model.endless { return ["\(model.ui("levels", "LEVELS")) \(run.cleared)", fish] }
        let abilities = result.won
            ? result.unlocked.map { "\(model.ui("new_ability", "NEW ABILITY")): \(model.text("ability.\($0.rawValue)").uppercased())" }
            : []
        return [model.text(level.nameKey).uppercased(), fish] + abilities
    }

    @ViewBuilder private var buttons: some View {
        if model.endless != nil {
            ResultButton(title: model.ui("retry", "RETRY")) { model.startEndless() }
        } else {
            if result.won, model.isUnlocked(levelIndex + 1) {
                ResultButton(title: model.ui("next_level", "NEXT LEVEL")) { model.start(level: levelIndex + 1) }
            }
            ResultButton(title: model.ui("retry", "RETRY")) { model.start(level: levelIndex) }
        }
        ResultButton(title: model.ui("menu", "MENU")) { model.quit() }
    }
}

/// The medal earned as one to three stars (bronze, silver, gold); empty outlines when there is none.
struct MedalStars: View {
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
        HStack(spacing: size * 0.12) {
            ForEach(0..<3, id: \.self) { index in
                Group {
                    if index < stars {
                        SpriteImage(sprite: "spark_star", animation: "still")
                    } else {
                        SpriteImage(sprite: "spark_star", animation: "still")
                            .colorMultiply(.black).opacity(0.3)
                    }
                }
                .frame(width: size, height: size)
                // The middle star stands a little higher, like a podium.
                .offset(y: index == 1 ? -size * 0.2 : 0)
            }
        }
        .padding(.top, size * 0.2)
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(stars) of 3 stars")
    }
}

struct ResultButton: View {
    let title: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.pixel(18))
                .foregroundStyle(Color.menuPaper)
                .shadow(color: .menuInk.opacity(0.6), radius: 0, x: 0, y: 2)
                .lineLimit(1)
                .minimumScaleFactor(0.7)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 14)
                .modifier(MenuPanel(fill: .orange))
        }
    }
}
