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
        // The buttons sit near the screen's edges: iOS must not hold their touches back (or take
        // them) for its own edge swipes, nor show the home indicator over them, during play.
        .defersSystemGestures(on: .all)
        .persistentSystemOverlays(.hidden)
        // Leaving the app mid-level pauses it, so the player comes back to the resume screen, not a
        // run that carried on (or a hit taken) while they were away.
        .onChange(of: scenePhase) { _, phase in
            if phase != .active { hud.isPaused = true }
        }
        .onAppear {
            // A level can open while the app is away: the next-level screen starts it after a countdown.
            // A bot run opens its level at launch, before the app is active, and must not wait on a tap.
            if scenePhase != .active, !model.autoplay, !model.jumpTest { hud.isPaused = true }
        }
    }

    private func makeScene(viewSize: CGSize) -> GameScene {
        let level = model.playableLevel(levelIndex)
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
    /// The ability buttons' size on its side (whole-pixel 64 pt on 3x screens).
    private static let wideButton: CGFloat = 64
    @Environment(\.displayScale) private var displayScale

    /// The cat-paw jump button at `size` pt, in the state the world is in.
    @ViewBuilder
    private func jumpButton(size: CGFloat) -> some View {
    // The cat-paw jump button, in the state the world is in; the old arrow if the
    // paw sprites are not drawn yet.
    let face = ButtonFace.jump(hud.jumpButton, unlocked: hud.canDoubleJump)
    let drawn = face.all.allSatisfy { model.sprites.sheet($0) != nil }
    HoldButton(onChange: jump, pressEffect: drawn ? .sprite : .fade, size: size) { pressed in
        if drawn {
            ButtonFace(sprite: pressed ? face.pressed : face.idle, animation: face.animation, size: size)
        } else {
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
    }
    .accessibilityLabel("Jump")
    .accessibilityIdentifier("jumpButton")
    }

    /// The paw button (once Ghost Dash is won) and the yarn button (once Yarn Shot is), at `size` pt.
    @ViewBuilder
    private func abilityButtons(size: CGFloat) -> some View {
        if hud.canDash {
            // Ghost Dash (dash / pressed / cooling down); once Super Pounce is won, the
            // pounce faces while the paw is charging. The old ring if not drawn.
            let pawFace = ButtonFace.paw(dashReady: hud.dashReady, canPounce: hud.canPounce,
                                         charge: hud.pounceCharge)
            let pawDrawn = pawFace.all.allSatisfy { model.sprites.sheet($0) != nil }
            HoldButton(onChange: paw, pressEffect: pawDrawn ? .sprite : .fade, size: size) { pressed in
                if pawDrawn {
                    ButtonFace(sprite: pressed ? pawFace.pressed : pawFace.idle, animation: pawFace.animation, size: size)
                } else {
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
            }
            .accessibilityLabel(model.text("ability.ghostDash"))
            .accessibilityHint(hud.canPounce ? model.text("ability.superPounce") : "")
        }
        if hud.canFire {
            // Yarn: ready / pressed / cooling down. The old icon if not drawn.
            let yarnFace = ButtonFace.yarn(ready: hud.fireReady)
            let yarnDrawn = yarnFace.all.allSatisfy { model.sprites.sheet($0) != nil }
            HoldButton(onChange: fire, pressEffect: yarnDrawn ? .sprite : .fade, size: size) { pressed in
                if yarnDrawn {
                    ButtonFace(sprite: pressed ? yarnFace.pressed : yarnFace.idle, animation: yarnFace.animation, size: size)
                } else {
                    ZStack {
                        Circle().fill(.black.opacity(0.15))
                        SpriteImage(sprite: "ability_yarnShot", animation: "still")
                            .frame(width: 48, height: 48)
                    }
                }
            }
            .accessibilityLabel(model.text("ability.yarnShot"))
        }
    }

    var body: some View {
        ZStack {
            #if DEBUG
            if model.jumpTest {
                // For the jump-height UI test: "<jumps landed> <last apex>", barely visible.
                Text("\(hud.debugJumpCount) \(String(format: "%.1f", hud.debugJumpApex))")
                    .font(.system(size: 8))
                    .opacity(0.02)
                    .accessibilityIdentifier("jumpApex")
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .bottom)
                    .allowsHitTesting(false)
            }
            // Always on in debug builds, so a hold can be checked on a real device: the last jump's
            // apex (world units above where it left) and how long the button was held.
            Text(hud.debugJumpCount == 0 ? "jump – · held –"
                 : String(format: "jump %.0f · held %.2fs", hud.debugJumpApex, hud.debugJumpHeld))
                .font(.system(size: 11, weight: .semibold, design: .monospaced))
                .foregroundStyle(.white)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .background(.black.opacity(0.45), in: Capsule())
                .padding(.top, 52)
                .padding(.trailing, 8)
                .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topTrailing)
                .allowsHitTesting(false)
                .accessibilityHidden(true)
            #endif
            VStack(spacing: 6) {
                HStack(alignment: .bottom, spacing: 12) {
                    // The lives panel (cat head, hearts, fish) and the LV panel with the XP bar.
                    LivesPanel(hearts: hud.hearts, maxHearts: hud.maxHearts, fish: hud.fish)
                    LevelPanel(level: hud.heroLevel, fraction: hud.xpFraction)
                    Spacer(minLength: 0)
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
                    BossHealth(id: hud.bossID, name: boss, fraction: hud.bossFraction, hits: hud.bossHits)
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
                    // Upright the paw stacks over the yarn on the earth below the ground line, and jump is on
                    // the right; on its side all three are smaller, on the earth strip in the bottom corners
                    // (the overlays below), under the running kitten.
                    if upright {
                        VStack(spacing: 0) { abilityButtons(size: 88) }
                    }
                    Spacer()
                    if upright { jumpButton(size: 88) }
                }
                // On its side the safe area already keeps the buttons clear of the notch, so they can
                // reach a little past it towards the edges.
                .padding(.horizontal, upright ? 26 : -14)
                .padding(.bottom, upright ? 20 : 0)
            }
            .disabled(hud.isPaused)

            if !upright {
                // On its side the ground line is only 40 units up, too low for the buttons to fit under
                // it at full size: smaller, side by side, their tops just under the ground line in the
                // safe-area corner, so they cover the earth strip and never the kitten running above.
                ScreenFrame { size, insets in
                    let ground = GameScene.groundHeight(viewSize: size, displayScale: displayScale)
                    HStack(spacing: 8 - 2 * HoldButton<EmptyView>.padding(for: Self.wideButton)) {
                        abilityButtons(size: Self.wideButton)
                    }
                    .padding(.leading, insets.leading + 4 - HoldButton<EmptyView>.padding(for: Self.wideButton))
                    .padding(.top, size.height - ground + 2 - HoldButton<EmptyView>.padding(for: Self.wideButton))
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
                }
                .disabled(hud.isPaused)
                // The jump button mirrors them in the bottom-right corner, clear of what comes in from
                // the right.
                ScreenFrame { size, insets in
                    let ground = GameScene.groundHeight(viewSize: size, displayScale: displayScale)
                    let pad = HoldButton<EmptyView>.padding(for: Self.wideButton)
                    jumpButton(size: Self.wideButton)
                        .padding(.trailing, insets.trailing + 4 - pad)
                        .padding(.top, size.height - ground + 2 - pad)
                        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topTrailing)
                }
                .disabled(hud.isPaused)
            }

            if hud.isPaused {
                PauseMenu(resume: { hud.isPaused = false }, quit: quit)
            }
        }
        .foregroundStyle(.white)
    }
}

/// The fish counter: a fish and "×N".
/// A round on-screen button that reports when a finger goes down on it and when it lifts. The
/// touch area reaches a little past the drawn circle so a thumb that lands just off it still counts.
private struct HoldButton<Label: View>: View {
    enum PressEffect {
        /// Translucent, brighter and smaller while held (the drawn-in-code buttons).
        case fade
        /// The sprite has its own pressed frame; only a slight squash.
        case sprite
    }

    let onChange: (Bool) -> Void
    var pressEffect = PressEffect.fade
    /// Drawn size in points; the touch area reaches `padding(for:)` further all round.
    var size: CGFloat = 88
    /// The face, given whether the button is held.
    @ViewBuilder let label: (_ pressed: Bool) -> Label
    @State private var isPressed = false

    /// Extra touch area round a button of `size`: generous on the small ones too.
    static func padding(for size: CGFloat) -> CGFloat { size >= 88 ? 14 : 12 }

    var body: some View {
        label(isPressed)
            .frame(width: size, height: size)
            .scaleEffect(isPressed ? (pressEffect == .sprite ? 0.96 : 0.92) : 1)
            .opacity(pressEffect == .sprite ? 1 : (isPressed ? 0.9 : 0.55))
            .padding(Self.padding(for: size))
            // Touches come straight from UIKit (a SwiftUI gesture lost holds on a real device: every
            // jump came out a tap). The pad covers the whole circle, padding included.
            .overlay {
                TouchPad { pressed in
                    guard pressed != isPressed else { return }
                    isPressed = pressed
                    onChange(pressed)
                }
                .clipShape(Circle())
            }
            .onDisappear {
                if isPressed {
                    isPressed = false
                    onChange(false)
                }
            }
            .accessibilityElement(children: .combine)
            .accessibilityAddTraits(.isButton)
            // VoiceOver's double tap: a short press.
            .accessibilityAction {
                onChange(true)
                Task { @MainActor in
                    try? await Task.sleep(for: .seconds(0.15))
                    onChange(false)
                }
            }
    }
}

/// A transparent UIKit view that reports a press: held from the moment a finger lands on it until
/// that same finger lifts or the system cancels it, with nothing in between (moving the finger, other
/// fingers on other buttons) changing that. Hit-tests as a circle filling its bounds.
private struct TouchPad: UIViewRepresentable {
    let onChange: (Bool) -> Void

    func makeUIView(context: Context) -> TouchPadView {
        let view = TouchPadView()
        view.onChange = onChange
        return view
    }

    func updateUIView(_ view: TouchPadView, context: Context) {
        view.onChange = onChange
        // A disabled button (the game paused) takes no touches at all; one held as it is disabled
        // lets go.
        view.isUserInteractionEnabled = context.environment.isEnabled
        if !context.environment.isEnabled { view.release() }
    }

    static func dismantleUIView(_ view: TouchPadView, coordinator: ()) {
        view.release()
    }
}

final class TouchPadView: UIView {
    var onChange: ((Bool) -> Void)?
    /// The finger that pressed this button; others are ignored until it lifts.
    private var touch: UITouch?

    override init(frame: CGRect) {
        super.init(frame: frame)
        backgroundColor = .clear
        isMultipleTouchEnabled = true
        isExclusiveTouch = false
        isAccessibilityElement = false
    }

    @available(*, unavailable)
    required init?(coder: NSCoder) {
        fatalError("init(coder:) is not used")
    }

    override func didMoveToWindow() {
        super.didMoveToWindow()
        // Recognizers up the hierarchy (SwiftUI's, the window's) must neither hold a touch back until
        // they give up on it nor cancel it when they recognise something.
        var view: UIView? = superview
        while let current = view {
            for recognizer in current.gestureRecognizers ?? [] {
                recognizer.delaysTouchesBegan = false
                recognizer.delaysTouchesEnded = false
                recognizer.cancelsTouchesInView = false
            }
            view = current.superview
        }
    }

    override func point(inside point: CGPoint, with event: UIEvent?) -> Bool {
        let radius = min(bounds.width, bounds.height) / 2
        return hypot(point.x - bounds.midX, point.y - bounds.midY) <= radius
    }

    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent?) {
        guard touch == nil, let first = touches.first else { return }
        touch = first
        onChange?(true)
    }

    override func touchesMoved(_ touches: Set<UITouch>, with event: UIEvent?) {}

    override func touchesEnded(_ touches: Set<UITouch>, with event: UIEvent?) {
        lift(touches)
    }

    override func touchesCancelled(_ touches: Set<UITouch>, with event: UIEvent?) {
        lift(touches)
    }

    private func lift(_ touches: Set<UITouch>) {
        guard let touch, touches.contains(touch) else { return }
        release()
    }

    /// Lets go (the finger lifted, or the button is going away).
    func release() {
        guard touch != nil else { return }
        touch = nil
        onChange?(false)
    }
}

/// An action button drawn as its sprite (the cat-paw jump, yarn and paw buttons, all 48×48), at the
/// whole-pixel scale nearest 88 pt.
private struct ButtonFace: View {
    @Environment(AppModel.self) private var model
    @Environment(\.displayScale) private var displayScale
    let sprite: String
    let animation: String
    /// The size to come nearest, in points.
    var size: CGFloat = 88

    /// The sprites for one state of a button: at rest, while held, and its animation.
    struct Faces {
        let idle: String
        let pressed: String
        var animation = "still"
        var all: [String] { [idle, pressed] }
    }

    /// The jump button: a gold, sparkling paw only while a Double Pounce is there to use, so it is
    /// never gold before the ability is won.
    static func jump(_ state: GameHUD.JumpButton, unlocked: Bool) -> Faces {
        switch state {
        case .ready: Faces(idle: "button_jump", pressed: "button_jump_pressed")
        case .double: Faces(idle: "button_double", pressed: "button_double_pressed", animation: "sparkle")
        case .spent:
            unlocked ? Faces(idle: "button_double_disabled", pressed: "button_double_disabled")
                : Faces(idle: "button_jump_disabled", pressed: "button_jump_disabled")
        }
    }

    /// The yarn button, dimmed while the next throw is not ready.
    static func yarn(ready: Bool) -> Faces {
        ready ? Faces(idle: "button_yarn", pressed: "button_yarn_pressed")
            : Faces(idle: "button_yarn_cooldown", pressed: "button_yarn_cooldown")
    }

    /// The paw button: Ghost Dash, dimmed while it cools down; once Super Pounce is won, the pounce
    /// face while the paw charges and the sparkling one when the charge is full.
    static func paw(dashReady: Bool, canPounce: Bool, charge: Double) -> Faces {
        if canPounce, charge >= 1 {
            return Faces(idle: "button_pounce_charged", pressed: "button_pounce_charged", animation: "sparkle")
        }
        if canPounce, charge > 0 {
            return Faces(idle: "button_pounce", pressed: "button_pounce")
        }
        return dashReady ? Faces(idle: "button_dash", pressed: "button_dash_pressed")
            : Faces(idle: "button_dash_cooldown", pressed: "button_dash_cooldown")
    }

    var body: some View {
        let width = model.sprites.sheet(sprite)?.width ?? 48
        // Nearest `size` in whole device pixels per sprite pixel; a tie takes the smaller.
        let exact = size * max(displayScale, 1) / width
        let scale = max(1, Int(exact.rounded(.down)) + (exact - exact.rounded(.down) > 0.5 ? 1 : 0))
        PixelSprite(sprite: sprite, animations: [animation], pixelScale: scale)
    }
}

/// A soft ring of yarn colours that turns around the jump button once Double Pounce is won (shown
/// only with the old arrow button, when the paw sprites are missing).
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

// MARK: - Pause

/// The pause menu from the user's sheet (docs/concept/Retro Cat Pause Menu Sprite Sheet.png): one
/// painted panel (`pause_panel`) with PAUSED and its RESUME and QUIT TO MENU buttons baked in, over the
/// dimmed game. Each baked button has a hit area laid over it that shows the button's pressed art while
/// held and acts when the finger lifts inside it. The overlay takes every touch.
private struct PauseMenu: View {
    @Environment(AppModel.self) private var model
    let resume: () -> Void
    let quit: () -> Void

    /// pause_panel.png is 691×744.
    private static let aspect: CGFloat = 691.0 / 744.0
    /// The baked buttons, as fractions of the panel image.
    private static let resumeRect = CGRect(x: 0.10, y: 0.473, width: 0.805, height: 0.161)
    private static let quitRect = CGRect(x: 0.10, y: 0.661, width: 0.805, height: 0.162)

    var body: some View {
        ZStack {
            // Swallows every touch that misses the panel's buttons.
            Color.black.opacity(0.55)
                .ignoresSafeArea()
                .contentShape(Rectangle())
                .onTapGesture {}
            GeometryReader { proxy in
                // Upright about 86% of the width; on its side about 92% of the (safe) height.
                let upright = proxy.size.height > proxy.size.width
                let width = upright
                    ? min(proxy.size.width * 0.86, proxy.size.height * 0.92 * Self.aspect)
                    : proxy.size.height * 0.92 * Self.aspect
                let panel = CGSize(width: width.rounded(), height: (width / Self.aspect).rounded())
                Image("pause_panel")
                    .resizable()
                    .interpolation(.high)
                    .frame(width: panel.width, height: panel.height)
                    .accessibilityElement()
                    .accessibilityLabel(model.ui("paused"))
                    .accessibilityAddTraits(.isHeader)
                    .overlay(alignment: .topLeading) {
                        ZStack(alignment: .topLeading) {
                            PauseButtonArea(rect: Self.resumeRect, panel: panel, pressedImage: "pause_resume_pressed",
                                            label: model.ui("resume"), action: resume)
                            PauseButtonArea(rect: Self.quitRect, panel: panel, pressedImage: "pause_quit_pressed",
                                            label: model.ui("quit"), action: quit)
                        }
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
    }
}

/// A touch area over one of the pause panel's baked buttons, 6 pt larger all round. Held, it draws the
/// button's pressed art into the button's own rect; lifted inside, it acts; slid off, it cancels.
private struct PauseButtonArea: View {
    /// The button as fractions of the panel.
    let rect: CGRect
    /// The panel's size in points.
    let panel: CGSize
    let pressedImage: String
    let label: String
    let action: () -> Void
    @State private var pressed = false

    private static let pad: CGFloat = 6

    var body: some View {
        let button = CGRect(x: rect.minX * panel.width, y: rect.minY * panel.height,
                            width: rect.width * panel.width, height: rect.height * panel.height)
        let area = button.insetBy(dx: -Self.pad, dy: -Self.pad)
        ZStack {
            Color.clear
            Image(pressedImage)
                .resizable()
                .interpolation(.high)
                .frame(width: button.width, height: button.height)
                .opacity(pressed ? 1 : 0)
        }
        .frame(width: area.width, height: area.height)
        .contentShape(Rectangle())
        .gesture(
            DragGesture(minimumDistance: 0)
                .onChanged { value in
                    pressed = CGRect(origin: .zero, size: area.size).contains(value.location)
                }
                .onEnded { value in
                    let inside = CGRect(origin: .zero, size: area.size).contains(value.location)
                    pressed = false
                    if inside { action() }
                }
        )
        .offset(x: area.minX, y: area.minY)
        .accessibilityElement()
        .accessibilityLabel(label)
        .accessibilityAddTraits(.isButton)
        .accessibilityAction { action() }
    }
}

