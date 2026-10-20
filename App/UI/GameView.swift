import GameCore
import SpriteKit
import SwiftUI

struct GameView: View {
    @Environment(AppModel.self) private var model
    let levelIndex: Int
    @State private var hud = GameHUD()
    @State private var scene: GameScene?

    @Environment(\.displayScale) private var displayScale
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        ZStack {
            // The game fills the whole screen; the HUD below stays inside the safe area so it clears
            // the notch, Dynamic Island and home indicator in either orientation.
            GeometryReader { proxy in
                ZStack {
                    Color.black
                    if let scene {
                        SpriteView(scene: scene, preferredFramesPerSecond: 60)
                    }
                }
                .onAppear { if scene == nil { scene = makeScene(viewSize: proxy.size) } }
                .onChange(of: proxy.size) { _, newSize in scene?.layout(viewSize: newSize) }
            }
            .ignoresSafeArea()
            HUDView(hud: hud,
                    jump: { scene?.setJump(held: $0) },
                    fire: { scene?.setFire(held: $0) },
                    paw: { scene?.setPaw(held: $0) },
                    quit: { model.quit() })
        }
        // Leaving the app mid-level pauses it, so the player comes back to the resume screen, not a
        // run that carried on (or a hit taken) while they were away.
        .onChange(of: scenePhase) { _, phase in
            if phase != .active { hud.isPaused = true }
        }
        .onAppear {
            // A level can open while the app is away: the next-level screen starts it after a countdown.
            // A bot run opens its level at launch, before the app is active, and must not wait on a tap.
            if scenePhase != .active, !model.autoplay { hud.isPaused = true }
        }
    }

    private func makeScene(viewSize: CGSize) -> GameScene {
        let level = model.levels[levelIndex]
        return GameScene(
            viewSize: viewSize,
            displayScale: displayScale,
            level: level,
            boss: model.bosses[level.boss],
            stats: model.startingStats(for: levelIndex),
            library: model.sprites,
            hud: hud,
            // Bot and other debug runs stay silent.
            soundOn: model.soundOn,
            autoplay: model.autoplay,
            timeScale: model.endless?.speed ?? 1,
            openingBanner: openingBanner(for: level),
            text: { model.text($0) },
            onFinish: { model.finish(level: levelIndex, result: $0) }
        )
    }
}

extension GameView {
    /// In an endless run each level announces itself, and a new loop its number and speed.
    private func openingBanner(for level: LevelDefinition) -> String? {
        guard let run = model.endless else { return nil }
        guard run.startsNewLoop else { return model.text(level.nameKey).uppercased() }
        return NextLevelView.loopTitle(run)
    }
}

private struct HUDView: View {
    @Environment(AppModel.self) private var model
    let hud: GameHUD
    let jump: (Bool) -> Void
    let fire: (Bool) -> Void
    let paw: (Bool) -> Void
    let quit: () -> Void
    @Environment(\.verticalSizeClass) private var verticalSizeClass

    /// Upright, the buttons sit a little in from the corners and up off the bottom edge, nearer the thumbs.
    private var upright: Bool { verticalSizeClass != .compact }

    var body: some View {
        ZStack {
            VStack(spacing: 6) {
                HStack(alignment: .top, spacing: 12) {
                    VStack(alignment: .leading, spacing: 4) {
                        HStack(spacing: 3) {
                            ForEach(0..<hud.maxHearts, id: \.self) { index in
                                SpriteImage(sprite: index < hud.hearts ? "heart_full" : "heart_empty", animation: "still")
                                    .frame(width: 22, height: 20)
                            }
                        }
                        .accessibilityElement(children: .ignore)
                        .accessibilityLabel("\(hud.hearts) of \(hud.maxHearts) hearts")
                        FishCount(count: hud.fish)
                    }
                    // A dark backing keeps the counters readable over clouds and snow.
                    .padding(6)
                    .background(.black.opacity(0.3), in: RoundedRectangle(cornerRadius: 6))
                    VStack(alignment: .leading, spacing: 2) {
                        Text("LV \(hud.heroLevel)").font(.pixel(13)).outlined()
                        Bar(fraction: hud.xpFraction, color: .yellow).frame(width: 90, height: 6)
                    }
                    .padding(.top, 2)
                    .padding(6)
                    .background(.black.opacity(0.3), in: RoundedRectangle(cornerRadius: 6))
                    Spacer()
                    Button {
                        hud.isPaused.toggle()
                    } label: {
                        Image(systemName: hud.isPaused ? "play.fill" : "pause.fill")
                            .font(.title3)
                            .padding(10)
                            .background(.black.opacity(0.35), in: Circle())
                    }
                    .accessibilityLabel(hud.isPaused ? "Resume" : "Pause")
                }
                if let boss = hud.bossName {
                    VStack(spacing: 2) {
                        Text(boss.uppercased()).font(.pixel(11)).outlined()
                        Bar(fraction: hud.bossFraction, color: .red).frame(maxWidth: 240).frame(height: 8)
                    }
                    .padding(6)
                    .background(.black.opacity(0.3), in: RoundedRectangle(cornerRadius: 6))
                }
                if let banner = hud.banner {
                    Text(banner)
                        .font(.pixel(18))
                        .padding(.horizontal, 14)
                        .padding(.vertical, 6)
                        .background(.black.opacity(0.55), in: Capsule())
                        .padding(.top, 8)
                }
                if let ability = hud.award {
                    AwardCard(ability: ability)
                        .padding(.top, 8)
                        .transition(.scale(scale: 0.3).combined(with: .opacity))
                }
                Spacer()
            }
            .animation(.spring(response: 0.35, dampingFraction: 0.55), value: hud.award)
            .padding(.horizontal, 16)
            .padding(.top, 8)

            // Only these buttons take game input: yarn (with the paw above it) on the left, jump on the right.
            VStack {
                Spacer()
                HStack(alignment: .bottom) {
                    VStack(spacing: upright ? 0 : -14) {
                        if hud.canDash {
                            HoldButton(onChange: paw) {
                                ZStack {
                                    Circle().fill(.black.opacity(0.15))
                                    if hud.canPounce {
                                        Circle().stroke(Color.white.opacity(0.25), lineWidth: 5)
                                        Circle().trim(from: 0, to: hud.pounceCharge)
                                            .stroke(hud.pounceCharge >= 1 ? Color.yellow : Color.pink, lineWidth: 5)
                                            .rotationEffect(.degrees(-90))
                                    }
                                    SpriteImage(sprite: hud.pounceCharge >= 1 ? "ability_superPounce" : "ability_ghostDash",
                                                animation: "still")
                                        .frame(width: 48, height: 48)
                                        .opacity(hud.dashReady || hud.pounceCharge > 0 ? 1 : 0.4)
                                }
                            }
                            .accessibilityLabel(model.text("ability.ghostDash"))
                            .accessibilityHint(hud.canPounce ? model.text("ability.superPounce") : "")
                        }
                        if hud.canFire {
                            HoldButton(onChange: fire) {
                                ZStack {
                                    Circle().fill(.black.opacity(0.15))
                                    SpriteImage(sprite: "ability_yarnShot", animation: "still")
                                        .frame(width: 48, height: 48)
                                }
                            }
                            .accessibilityLabel(model.text("ability.yarnShot"))
                        }
                    }
                    Spacer()
                    HoldButton(onChange: jump) {
                        ZStack {
                            Circle().fill(.black.opacity(0.15))
                            if hud.canDoubleJump { PounceRing() }
                            // A plain arrow reads as "jump" at a glance; a second one once it can pounce again in the air.
                            Image(systemName: hud.canDoubleJump ? "chevron.up.2" : "chevron.up")
                                .font(.system(size: 38, weight: .black))
                                .foregroundStyle(.white)
                                .shadow(color: .black.opacity(0.6), radius: 0, x: 0, y: 2)
                        }
                    }
                    .accessibilityLabel("Jump")
                }
                // On its side the safe area already keeps the buttons clear of the notch, so they can
                // reach a little past it towards the edges.
                .padding(.horizontal, upright ? 26 : -14)
                .padding(.bottom, upright ? 20 : 0)
            }
            .disabled(hud.isPaused)

            if hud.isPaused {
                Color.black.opacity(0.6).ignoresSafeArea()
                VStack(spacing: 18) {
                    Text(model.ui("paused")).font(.pixel(28))
                    Button(model.ui("resume")) { hud.isPaused = false }.buttonStyle(PixelButton())
                    Button(model.ui("quit"), action: quit).buttonStyle(PixelButton(tint: .gray))
                }
            }
        }
        .foregroundStyle(.white)
    }
}

/// The fish counter: a fish and "×N".
private struct FishCount: View {
    let count: Int

    var body: some View {
        HStack(spacing: 4) {
            SpriteImage(sprite: "fish", animation: "spin").frame(width: 24, height: 18)
            Text("×\(count)").font(.pixel(14)).outlined()
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("\(count) fish")
    }
}

/// A round on-screen button that reports when a finger goes down on it and when it lifts. The
/// touch area reaches a little past the drawn circle so a thumb that lands just off it still counts.
private struct HoldButton<Label: View>: View {
    let onChange: (Bool) -> Void
    @ViewBuilder let label: () -> Label
    @GestureState private var isPressed = false

    var body: some View {
        label()
            .frame(width: 88, height: 88)
            .scaleEffect(isPressed ? 0.92 : 1)
            .opacity(isPressed ? 0.9 : 0.55)
            .padding(14)
            .contentShape(Circle())
            .gesture(DragGesture(minimumDistance: 0).updating($isPressed) { _, pressed, _ in pressed = true })
            // GestureState resets on release and on cancel, so a lost touch can never stick held.
            .onChange(of: isPressed) { _, pressed in onChange(pressed) }
            .onDisappear { if isPressed { onChange(false) } }
            .accessibilityAddTraits(.isButton)
    }
}

/// A soft ring of yarn colours that turns around the jump button once Double Pounce is won.
private struct PounceRing: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    private let colors: [Color] = [.pink, .purple, .cyan, .pink, .yellow, .pink]

    var body: some View {
        TimelineView(.animation(paused: reduceMotion)) { context in
            let t = reduceMotion ? 0 : context.date.timeIntervalSinceReferenceDate
            let pulse = 0.5 + 0.5 * sin(t * 3)
            ZStack {
                Circle()
                    .stroke(AngularGradient(colors: colors, center: .center), lineWidth: 5)
                    .rotationEffect(.radians(t * 1.5))
                    .blur(radius: 3 + 2 * pulse)
                Circle()
                    .stroke(AngularGradient(colors: colors, center: .center), lineWidth: 3)
                    .rotationEffect(.radians(-t * 1.1))
            }
            .opacity(0.7 + 0.3 * pulse)
        }
        .allowsHitTesting(false)
    }
}

/// The award for a new ability: its icon and name on a gold card.
private struct AwardCard: View {
    @Environment(AppModel.self) private var model
    let ability: Ability

    var body: some View {
        HStack(spacing: 12) {
            SpriteImage(sprite: "ability_\(ability.rawValue)", animation: "still").frame(width: 48, height: 48)
            VStack(alignment: .leading, spacing: 2) {
                Text(model.ui("new_ability")).font(.pixel(10)).foregroundStyle(Color.menuInk.opacity(0.75))
                PixelTitle(text: model.text("ability.\(ability.rawValue)"), size: 20).fixedSize()
            }
        }
        .padding(.vertical, 10)
        .padding(.horizontal, 4)
        .modifier(MenuPanel(fill: Color(red: 0.95, green: 0.78, blue: 0.27)))
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("New ability: \(model.text("ability.\(ability.rawValue)"))")
    }
}

struct Bar: View {
    let fraction: Double
    let color: Color

    var body: some View {
        GeometryReader { proxy in
            ZStack(alignment: .leading) {
                Rectangle().fill(.black.opacity(0.5))
                Rectangle().fill(color).frame(width: proxy.size.width * min(max(fraction, 0), 1))
            }
            .overlay(Rectangle().stroke(.white.opacity(0.8), lineWidth: 1))
        }
    }
}

struct PixelButton: ButtonStyle {
    var tint = Color.orange

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.pixel(16))
            .foregroundStyle(.black)
            .padding(.horizontal, 22)
            .padding(.vertical, 10)
            .background(tint.opacity(configuration.isPressed ? 0.6 : 1), in: Rectangle())
            .overlay(Rectangle().stroke(.black, lineWidth: 2))
    }
}

extension View {
    /// A one-pixel dark edge so HUD text stays readable over bright snow or sky.
    func outlined() -> some View {
        shadow(color: .black.opacity(0.8), radius: 0, x: 1, y: 1).shadow(color: .black.opacity(0.5), radius: 0, x: -1, y: 0)
    }
}

extension Font {
    static func pixel(_ size: CGFloat) -> Font {
        .system(size: size, weight: .heavy, design: .monospaced)
    }
}
