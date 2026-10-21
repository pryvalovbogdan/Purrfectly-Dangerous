import SpriteKit

/// The picture behind the start and end screens: the Purrwood morning with the hero standing on the
/// start screen, sitting happily (under falling confetti) after a level and knocked out after a lost
/// run. Given a level theme it shows that level instead, with the hero running, for the screen that
/// announces the next level of an endless run. Decoration only; no game rules run here.
///
/// Every piece of art is its own sprite from the manifest. A sprite that is not drawn yet is left out.
final class MenuScene: SKScene {
    enum Pose {
        /// Running through the scenery, which scrolls (the next-level screen).
        case running
        /// Standing at rest, playing `idle` (the start screen).
        case standing
        /// Sitting pleased with itself, `sit_happy` (level complete).
        case happy
        /// Out cold, `ko`, with dizzy stars and its ghost bobbing above (game over).
        case knockedOut
    }

    /// Default share of the screen height below the ground line when upright.
    static let narrowGroundShare: CGFloat = 0.36
    /// World units across an upright screen: few enough that the hero fills a good part of it.
    private static let narrowUnits: CGFloat = 190
    private static let pace: CGFloat = 70
    /// How fast the clouds drift (in run units, before each layer's parallax factor) while at rest.
    private static let drift: CGFloat = 60
    private static let heroScale: CGFloat = 2

    private let library: SpriteLibrary
    private let upright: Bool
    /// Device pixels per scene unit (a whole number).
    private let pixelsPerUnit: CGFloat
    private let pose: Pose
    /// A level's background theme to show instead of the menu's own morning.
    private let theme: String?
    private let celebrate: Bool
    private let groundShare: CGFloat
    private let wideHeroPlace: CGFloat?
    private var parallax: [ParallaxNode] = []
    /// Cloud layers, which keep drifting when the rest of the scene stands still.
    private var clouds: [ParallaxNode] = []
    private var lastTime: TimeInterval?
    private var scroll: CGFloat = 0
    /// The composed menu picture is up (it has the cat sign painted in).
    private var hasPicture = false

    /// - Parameters:
    ///   - celebrate: confetti and big sparkles (level complete).
    ///   - groundShare: share of an upright screen below the ground line; the buttons sit on that earth.
    ///   - wideHeroPlace: where the hero stands across a wide screen (0…1); nil for the default.
    init(viewSize: CGSize, displayScale: CGFloat, library: SpriteLibrary, pose: Pose = .running, theme: String? = nil,
         celebrate: Bool = false, groundShare: CGFloat = MenuScene.narrowGroundShare, wideHeroPlace: CGFloat? = nil) {
        self.library = library
        self.pose = pose
        self.theme = theme
        self.celebrate = celebrate
        self.groundShare = groundShare
        self.wideHeroPlace = wideHeroPlace
        upright = viewSize.height > viewSize.width
        let sceneSize = Self.sceneSize(viewSize: viewSize, displayScale: max(displayScale, 1))
        pixelsPerUnit = sceneSize.width > 0 ? viewSize.width * max(displayScale, 1) / sceneSize.width : 1
        super.init(size: sceneSize)
        scaleMode = .fill
        anchorPoint = .zero
    }

    /// On its side the menu is framed like the game. Upright the game needs width to show what is
    /// coming; the menu does not, so it zooms in and the hero fills more of the screen.
    private static func sceneSize(viewSize: CGSize, displayScale: CGFloat) -> CGSize {
        guard viewSize.height > viewSize.width else {
            return GameScene.sceneSize(viewSize: viewSize, displayScale: displayScale)
        }
        let pixelsPerUnit = max(1, floor(viewSize.width * displayScale / narrowUnits))
        return CGSize(width: viewSize.width * displayScale / pixelsPerUnit,
                      height: viewSize.height * displayScale / pixelsPerUnit)
    }

    /// Points per world unit for a menu scene filling `viewSize`, so SwiftUI layouts can keep clear
    /// of the hero standing in it.
    static func pointsPerUnit(viewSize: CGSize, displayScale: CGFloat) -> CGFloat {
        let scene = sceneSize(viewSize: viewSize, displayScale: max(displayScale, 1))
        return scene.width > 0 ? viewSize.width / scene.width : 1
    }

    /// First row of each composed picture (from its top) where scenery starts below the open sky,
    /// measured from the art: the tops of the trees.
    static let sceneryTopRows: [String: CGFloat] = ["menu_scene_portrait": 38, "menu_scene_landscape": 2]

    /// Where the top of the scenery (tree tops) of the start screen's picture is, in points from the
    /// top of a menu scene filling `viewSize`; nil without the picture. Matches `addMenuBackdrop`.
    static func sceneryTop(viewSize: CGSize, displayScale: CGFloat, library: SpriteLibrary,
                           groundShare: CGFloat = narrowGroundShare) -> CGFloat? {
        let upright = viewSize.height > viewSize.width
        let name = upright ? "menu_scene_portrait" : "menu_scene_landscape"
        guard let sheet = library.sheet(name) else { return nil }
        let scene = sceneSize(viewSize: viewSize, displayScale: max(displayScale, 1))
        let unit = scene.width > 0 ? viewSize.width / scene.width : 1
        let groundY = upright ? (scene.height * groundShare).rounded() : 40
        let scale = max(1, (scene.width / sheet.width).rounded(.down))
        let pictureTop = scene.height - (groundY + sheet.height * scale)
        return (pictureTop + (sceneryTopRows[name] ?? 0) * scale) * unit
    }

    /// Height of the standing hero above the ground line, in world units.
    static func heroHeight(_ library: SpriteLibrary) -> CGFloat {
        (library.sheet("hero")?.height ?? 36) * heroScale
    }

    @available(*, unavailable)
    required init?(coder aDecoder: NSCoder) {
        fatalError("init(coder:) is not used")
    }

    override func didMove(to view: SKView) {
        view.ignoresSiblingOrder = true
        let groundY = upright ? (size.height * groundShare).rounded() : 40
        if let theme {
            parallax = LevelBackdrop.build(theme: theme, size: size, groundY: groundY, library: library, into: self)
        } else {
            addMenuBackdrop(groundY: groundY)
        }

        let hero = ActorNode(sprite: "hero", library: library)
        hero.setScale(Self.heroScale)
        // At rest on a wide screen the hero steps aside to leave the middle to the score card.
        let place: CGFloat = upright ? 0.5 : (wideHeroPlace ?? (pose == .running ? 0.22 : 0.13))
        hero.position = CGPoint(x: (size.width * place).rounded(), y: groundY)
        addChild(hero)
        if theme == nil, !hasPicture {
            addSign(groundY: groundY, heroPlace: place)
        }

        switch pose {
        case .running: hero.play("run")
        case .standing: hero.play(hero.has("menu") ? "menu" : "idle")
        case .happy: hero.play(hero.has("sit_happy") ? "sit_happy" : "idle")
        case .knockedOut: knockOut(hero)
        }
        if celebrate {
            addSparkles()
            startConfetti()
        }
    }

    // MARK: - Backdrop

    /// Where `menu_waterfall` goes on each composed scene, as the artist gives it (WATERFALL in
    /// Tools/sprites/characters/menu_scene.py): the overlay's top-left corner, in picture pixels from
    /// the picture's top-left. A picture without a spot gets no overlay (the still has its own).
    static let waterfallSpots: [String: CGPoint] = [
        "menu_scene_portrait": CGPoint(x: 126, y: 162),
        "menu_scene_landscape": CGPoint(x: 286, y: 78),
    ]

    /// The start screen's own morning: a smooth sky with clouds drifting across it, the composed
    /// Purrwood picture for this orientation standing on the ground line, then the forest ground.
    /// Nothing scrolls but the clouds. Without the picture (not drawn yet) the older menu strips stand
    /// in for it, still.
    private func addMenuBackdrop(groundY: CGFloat) {
        addSky()
        let pictureName = upright ? "menu_scene_portrait" : "menu_scene_landscape"
        var pictureTop = groundY + (upright ? 120 : 70)
        if let picture = library.textures(pictureName, "still").first ?? firstFrame(pictureName),
           let sheet = library.sheet(pictureName) {
            // Whole-number scale, the largest that is no wider than the screen (at least 1).
            let scale = max(1, (size.width / sheet.width).rounded(.down))
            let node = SKSpriteNode(texture: picture, size: CGSize(width: sheet.width * scale, height: sheet.height * scale))
            node.anchorPoint = .zero
            node.position = CGPoint(x: ((size.width - node.size.width) / 2).rounded(), y: groundY)
            node.zPosition = -8
            addChild(node)
            pictureTop = groundY + node.size.height
            hasPicture = true
            addWaterfall(on: pictureName, origin: node.position, scale: scale)
            addClouds(above: pictureTop)
        } else {
            addClouds(above: pictureTop)
            if let bank = addStrip("bg_menu_clouds", bottom: groundY, factor: 0.08, z: -9) {
                clouds.append(bank)
            }
            addStrip("bg_menu_horizon", bottom: groundY, factor: 0.2, z: -8)
            addStrip("bg_menu_bushes", bottom: groundY, factor: 0.55, z: -7)
        }
        if let fill = library.textures("ground_forest_fill", "still").first {
            let node = SKSpriteNode(texture: fill, size: CGSize(width: size.width, height: groundY))
            node.anchorPoint = .zero
            node.zPosition = -6
            addChild(node)
        }
        if let sheet = library.sheet("ground_forest"), let earth = library.textures("ground_forest_earth", "still").first,
           let earthSheet = library.sheet("ground_forest_earth") {
            let top = groundY - sheet.height
            addStrip("ground_forest", bottom: top, factor: 1, z: -5)
            for row in ParallaxNode.earth(below: top, tile: earth,
                                          tileSize: CGSize(width: earthSheet.width, height: earthSheet.height),
                                          viewWidth: size.width) {
                row.zPosition = -5
                addChild(row)
                parallax.append(row)
            }
        }
    }

    /// A smooth gradient sky over the whole scene. It is drawn with smooth filtering: stretched with
    /// nearest-neighbour, a gradient tile shows hard bands.
    private func addSky() {
        let name = library.sheet("menu_sky") != nil ? "menu_sky" : "bg_menu_sky"
        guard let animation = library.animationName(name, preferring: "still"),
              library.animation(name, animation)?.frames ?? 0 > 0 else { return }
        let texture = SKTexture(imageNamed: "\(name)_\(animation)_0")
        texture.filteringMode = .linear
        let node = SKSpriteNode(texture: texture, size: size)
        node.anchorPoint = .zero
        node.zPosition = -10
        addChild(node)
    }

    /// Clouds drifting slowly across the sky, behind the picture so they never cross the scenery.
    private func addClouds(above pictureTop: CGFloat) {
        let name = library.sheet("menu_clouds") != nil ? "menu_clouds" : "bg_menu_puffs"
        guard let sheet = library.sheet(name), let animation = library.animationName(name, preferring: "still"),
              let texture = library.textures(name, animation).first else { return }
        // Tucked half behind the top of the picture, but always on screen.
        let bottom = min(pictureTop - (sheet.height * 0.5).rounded(), size.height - sheet.height)
        let node = ParallaxNode(texture: texture, size: CGSize(width: sheet.width, height: sheet.height),
                                viewWidth: size.width, factor: 0.05)
        node.position.y = max(0, bottom)
        node.zPosition = -9
        addChild(node)
        clouds.append(node)
    }

    /// The animated waterfall over the still picture, at the spot the artist gives for it.
    private func addWaterfall(on picture: String, origin: CGPoint, scale: CGFloat) {
        guard let spot = Self.waterfallSpots[picture], let pictureSheet = library.sheet(picture),
              let sheet = library.sheet("menu_waterfall"), let waterfall = actor("menu_waterfall") else { return }
        waterfall.setScale(scale)
        // From a top-left corner (top-down) to the node's anchor point (bottom-up), in picture pixels.
        let anchorX = spot.x + sheet.width * sheet.anchorX
        let anchorY = pictureSheet.height - spot.y - sheet.height * (1 - sheet.anchorY)
        waterfall.position = CGPoint(x: origin.x + anchorX * scale, y: origin.y + anchorY * scale)
        waterfall.zPosition = -7.5
        addChild(waterfall)
    }

    private func firstFrame(_ sprite: String) -> SKTexture? {
        library.animationName(sprite, preferring: "still").flatMap { library.textures(sprite, $0).first }
    }

    @discardableResult
    private func addStrip(_ name: String, bottom: CGFloat, factor: CGFloat, z: CGFloat) -> ParallaxNode? {
        guard let texture = library.textures(name, "still").first, let sheet = library.sheet(name) else { return nil }
        let node = ParallaxNode(texture: texture, size: CGSize(width: sheet.width, height: sheet.height),
                                viewWidth: size.width, factor: factor)
        node.position.y = bottom
        node.zPosition = z
        addChild(node)
        parallax.append(node)
        return node
    }

    /// The wooden cat sign by the path, on the side of the hero the screen leaves open.
    private func addSign(groundY: CGFloat, heroPlace: CGFloat) {
        guard let sign = actor("sign_cat") else { return }
        let place: CGFloat = upright ? 0.13 : (heroPlace > 0.5 ? 0.93 : heroPlace + 0.15)
        sign.position = CGPoint(x: (size.width * place).rounded(), y: groundY)
        sign.zPosition = -1
        addChild(sign)
    }

    // MARK: - Poses

    /// Share of the screen width the knocked-out hero spans (as in the game-over reference).
    static let knockedOutWidthShare: CGFloat = 0.36
    /// The ghost and the dizzy stars are drawn at this share of the knocked-out hero's scale.
    static let ghostShare: CGFloat = 0.6

    /// Out cold on the grass, in front of everything in the scene (the picture's foreground bushes
    /// included), with stars over its head and a smaller ghost of it bobbing above. Scaled so the
    /// drawn cat spans about a third of the screen, at a whole number of device pixels per sprite pixel.
    private func knockOut(_ hero: ActorNode) {
        let animation = hero.has("ko") ? "ko" : "death"
        if hero.has("ko") {
            hero.play("ko")
        } else {
            // A frame from before the death animation fades the hero away.
            let frames = library.textures("hero", "death")
            if !frames.isEmpty { hero.texture = frames[min(3, frames.count - 1)] }
        }
        let sheet = library.sheet("hero")
        let sheetHeight = sheet?.height ?? 36
        let sheetWidth = sheet?.width ?? 44
        let drawn = MainActor.assumeIsolated { library.opaqueBounds("hero", animation) }
            ?? CGRect(x: 5, y: 15, width: 34, height: 21)
        let devicePixels = max(1, (size.width * pixelsPerUnit * Self.knockedOutWidthShare / drawn.width).rounded())
        let scale = devicePixels / pixelsPerUnit
        hero.setScale(scale)
        hero.zPosition = 5
        // Top of the drawn cat, above the hero's position, in scene units.
        let drawnTop = (sheetHeight - drawn.minY) * scale
        let smallScale = max(1, (devicePixels * Self.ghostShare).rounded()) / pixelsPerUnit

        if let stars = actor("stars_dizzy") {
            // Over the head, at the front (right) of a cat lying on its side.
            stars.setScale(smallScale)
            let headX = (drawn.maxX - drawn.width * 0.25 - sheetWidth * (sheet?.anchorX ?? 0.5)) * scale
            stars.position = CGPoint(x: snap(hero.position.x + headX), y: snap(hero.position.y + drawnTop + 1))
            stars.zPosition = 6
            addChild(stars)
        }
        if hero.has("ghost") {
            let ghost = ActorNode(sprite: "hero", library: library)
            ghost.setScale(smallScale)
            ghost.play("ghost")
            ghost.alpha = 0.85
            let ghostDrawn = MainActor.assumeIsolated { library.opaqueBounds("hero", "ghost") }
                ?? CGRect(x: 6, y: 2, width: 31, height: 30)
            // Its lowest drawn row a little above the cat (and above the stars).
            let lift = drawnTop + 8 * smallScale + 4 - (sheetHeight - ghostDrawn.maxY) * smallScale
            ghost.position = CGPoint(x: hero.position.x, y: snap(hero.position.y + lift))
            ghost.zPosition = 7
            let bob = SKAction.moveBy(x: 0, y: 6, duration: 1.1)
            bob.timingMode = .easeInEaseOut
            ghost.run(.repeatForever(.sequence([bob, bob.reversed()])))
            addChild(ghost)
        }
    }

    /// A scene position on a whole device pixel, so scaled pixel art stays crisp.
    private func snap(_ value: CGFloat) -> CGFloat {
        (value * pixelsPerUnit).rounded() / pixelsPerUnit
    }

    // MARK: - Celebration

    private static let confettiSprites = ["confetti_red", "confetti_yellow", "confetti_blue", "confetti_green"]

    /// Big sparkles twinkling in the sky and around the hero.
    private func addSparkles() {
        guard let name = library.animationName("sparkle_big", preferring: "still") else { return }
        let frames = library.textures("sparkle_big", name)
        guard !frames.isEmpty else { return }
        let spots: [CGPoint] = upright
            ? [CGPoint(x: 0.12, y: 0.86), CGPoint(x: 0.9, y: 0.8), CGPoint(x: 0.08, y: 0.55),
               CGPoint(x: 0.92, y: 0.5), CGPoint(x: 0.3, y: 0.4), CGPoint(x: 0.72, y: 0.36)]
            : [CGPoint(x: 0.06, y: 0.85), CGPoint(x: 0.24, y: 0.62), CGPoint(x: 0.3, y: 0.92),
               CGPoint(x: 0.95, y: 0.88), CGPoint(x: 0.04, y: 0.5)]
        for (index, spot) in spots.enumerated() {
            let node = SKSpriteNode(texture: frames[0])
            node.position = CGPoint(x: (size.width * spot.x).rounded(), y: (size.height * spot.y).rounded())
            node.zPosition = -3
            node.alpha = 0
            if frames.count > 1 {
                node.run(.repeatForever(.animate(with: frames, timePerFrame: 0.12)))
            }
            let twinkle = SKAction.sequence([.fadeIn(withDuration: 0.25), .wait(forDuration: 0.5),
                                             .fadeOut(withDuration: 0.35), .wait(forDuration: 0.6 + Double(index % 3) * 0.4)])
            node.run(.sequence([.wait(forDuration: Double(index) * 0.3), .repeatForever(twinkle)]))
            addChild(node)
        }
    }

    /// Confetti falling and fluttering over the whole sky: a first burst, then a steady trickle.
    private func startConfetti() {
        let kinds = Self.confettiSprites.compactMap { sprite -> [SKTexture]? in
            guard let name = library.animationName(sprite, preferring: "still") else { return nil }
            let frames = library.textures(sprite, name)
            return frames.isEmpty ? nil : frames
        }
        guard !kinds.isEmpty else { return }
        for _ in 0..<28 {
            dropConfetti(kinds, from: CGFloat.random(in: size.height * 0.45...size.height + 8))
        }
        run(.repeatForever(.sequence([.run { [weak self] in
            guard let self else { return }
            dropConfetti(kinds, from: size.height + 8)
        }, .wait(forDuration: 0.16, withRange: 0.12)])), withKey: "confetti")
    }

    private func dropConfetti(_ kinds: [[SKTexture]], from top: CGFloat) {
        guard let frames = kinds.randomElement(), let first = frames.first else { return }
        let piece = SKSpriteNode(texture: first)
        piece.position = CGPoint(x: CGFloat.random(in: 0...size.width).rounded(), y: top.rounded())
        piece.zPosition = -4
        let fallSpeed = CGFloat.random(in: 24...42)
        let fall = SKAction.moveBy(x: 0, y: -(top + 10), duration: Double((top + 10) / fallSpeed))
        let sway = SKAction.moveBy(x: CGFloat.random(in: 4...9), y: 0, duration: Double.random(in: 0.7...1.2))
        sway.timingMode = .easeInEaseOut
        // Turning over in the air: the piece narrows to its edge and flips.
        let flip = Double.random(in: 0.18...0.32)
        piece.run(.repeatForever(.sequence([.scaleX(to: -1, duration: flip), .scaleX(to: 1, duration: flip)])))
        piece.run(.repeatForever(.sequence([sway, sway.reversed()])))
        if frames.count > 1 {
            piece.run(.repeatForever(.animate(with: frames, timePerFrame: 0.1)))
        }
        piece.run(.sequence([fall, .removeFromParent()]))
        addChild(piece)
    }

    // MARK: - Helpers

    /// A sprite from the manifest playing its `still` animation (or its first), or nil if not drawn yet.
    private func actor(_ sprite: String) -> ActorNode? {
        guard let name = library.animationName(sprite, preferring: "still") else { return nil }
        let node = ActorNode(sprite: sprite, library: library)
        node.play(name)
        return node
    }

    override func update(_ currentTime: TimeInterval) {
        defer { lastTime = currentTime }
        guard let lastTime else { return }
        let dt = CGFloat(min(currentTime - lastTime, 0.1))
        if pose == .running {
            scroll += dt * Self.pace
            for layer in parallax { layer.scroll(to: scroll) }
        } else {
            scroll += dt * Self.drift
            for layer in clouds { layer.scroll(to: scroll) }
        }
    }
}
