import GameCore
import SpriteKit
import UIKit

/// Draws a `RunnerWorld` and feeds it touches. All rules live in GameCore; nothing here decides
/// whether the kitten is hit or an enemy dies.
final class GameScene: SKScene {
    private static let step = 1.0 / 60
    /// How the playfield is framed for one orientation.
    private struct Framing {
        /// Fewest world units that must fit: height for the tallest boss and a double jump, width to
        /// see a boss standing `bossOffset` ahead of the hero.
        let minimumUnits: CGSize
        let heroScreenX: CGFloat
        let bossOffset: Double
        /// Share of the screen height below the ground line.
        let groundShare: CGFloat?

        static let wide = Framing(minimumUnits: CGSize(width: 330, height: 180), heroScreenX: 70,
                                  bossOffset: Tuning.wideBossOffset, groundShare: nil)
        /// Portrait trades view distance for size: sprites are drawn larger, so the hero stands
        /// nearer the edge and the boss nearer the hero to keep both on screen.
        static let narrow = Framing(minimumUnits: CGSize(width: 190, height: 180), heroScreenX: 30,
                                    bossOffset: Tuning.narrowBossOffset, groundShare: 0.38)

        static func `for`(_ viewSize: CGSize) -> Framing {
            viewSize.height > viewSize.width ? narrow : wide
        }
    }

    /// A one-way ledge drawn as a row of its sprite's tiles.
    private struct PlatformView {
        let index: Int
        let sprite: String
        let node: SKNode
        let tiles: [SKSpriteNode]
        let height: CGFloat
    }

    private var framing: Framing

    /// Height of the ground line above the bottom of the scene; set by `layout(viewSize:)`.
    private var groundY: CGFloat = 40
    private let displayScale: CGFloat

    private var world: RunnerWorld
    private let library: SpriteLibrary
    private let hud: GameHUD
    /// Nil when sound is off; built with the scene so no sound loads mid-level.
    private let sounds: SoundPlayer?
    /// How fast the game clock runs; above 1 in the later loops of an endless run.
    private let timeScale: Double
    private let openingBanner: String?
    private let text: (String) -> String
    private let onFinish: (GameResult) -> Void
    /// Set by the `-autoplay` debug launch argument: the validator bot plays instead of touches.
    private var bot: Bot?

    private var lastTime: TimeInterval?
    private var accumulator = 0.0
    /// Distance used for scrolling the scenery; stops when the level is won.
    private var scroll = 0.0
    private var jumpHeld = false
    private var fireHeld = false
    private var pawHeld = false
    private var jumpPending = false
    private var pawPending = false
    private var reported = false
    private var unlocked: [Ability] = []

    private var parallax: [ParallaxNode] = []
    private var groundNodes: [(at: Double, width: Double, node: SKNode)] = []
    /// The base ground fill and strip, each cropped so they leave gaps above the floor of a dip;
    /// empty in a level without dips. Each has its own mask (a node has one parent), kept in step.
    private var groundCrops: [SKCropNode] = []
    /// White rectangles of each crop's mask: one per stretch of ground on screen.
    private var groundMaskRects: [[SKSpriteNode]] = []
    /// The hero went down a ravine: the drop is animated here, so `renderHero` leaves them alone.
    private var fell = false
    private let scenery = SKNode()
    private let actors = SKNode()
    private var hero: ActorNode!
    /// One node per boss copy; index 0 stands at the boss position, the rest are the phantom's decoys.
    private var bossNodes: [ActorNode] = []
    private var entityNodes: [Int: ActorNode] = [:]
    private var hazardNodes: [Int: ActorNode] = [:]
    private var shotNodes: [Int: ActorNode] = [:]
    private var platformViews: [PlatformView] = []
    /// World time each crumbling ledge was landed on, to pace its crumble frames.
    private var crumbleStart: [Int: Double] = [:]
    /// Sprite for hazards an enemy threw, keyed by hazard id (an acorn from a branch is not a boss acorn).
    private var thrownSprite: [Int: String] = [:]
    private var hurtUntil = 0.0
    private var throwUntil = 0.0
    private var bossHurtUntil = 0.0
    private var doubleJumping = false
    private var wasPouncing = false
    private var bannerUntil = 0.0
    private var awardUntil = 0.0

    private let haptics = UIImpactFeedbackGenerator(style: .medium)

    init(viewSize: CGSize, displayScale: CGFloat, level: LevelDefinition, boss: BossDefinition?, stats: HeroStats, library: SpriteLibrary,
         hud: GameHUD, soundOn: Bool, autoplay: Bool = false, timeScale: Double = 1, openingBanner: String? = nil,
         text: @escaping (String) -> String, onFinish: @escaping (GameResult) -> Void) {
        world = RunnerWorld(level: level, boss: boss, stats: stats)
        self.library = library
        self.hud = hud
        sounds = soundOn ? SoundPlayer() : nil
        self.timeScale = timeScale
        self.openingBanner = openingBanner
        self.text = text
        self.onFinish = onFinish
        bot = autoplay ? Bot() : nil
        self.displayScale = max(displayScale, 1)
        framing = Framing.for(viewSize)
        world.setBossOffset(framing.bossOffset)
        super.init(size: Self.sceneSize(viewSize: viewSize, displayScale: self.displayScale))
        // The scene has the view's proportions, so `.fill` scales both axes alike.
        scaleMode = .fill
        anchorPoint = .zero
        groundY = Self.groundLine(for: size, framing: framing)
        // Animations keep pace with the faster clock.
        speed = CGFloat(timeScale)
    }

    /// World units shown for a view of `viewSize` points. One unit always covers a whole number of
    /// device pixels, the same on both axes, so every sprite pixel is drawn square and the same size.
    static func sceneSize(viewSize: CGSize, displayScale: CGFloat) -> CGSize {
        let minimum = Framing.for(viewSize).minimumUnits
        let pixelsPerUnit = max(1, floor(min(viewSize.height * displayScale / minimum.height,
                                             viewSize.width * displayScale / minimum.width)))
        return CGSize(width: viewSize.width * displayScale / pixelsPerUnit,
                      height: viewSize.height * displayScale / pixelsPerUnit)
    }

    /// In portrait the ground line sits part-way up the screen, leaving earth below for thumbs.
    private static func groundLine(for size: CGSize, framing: Framing) -> CGFloat {
        framing.groundShare.map { (size.height * $0).rounded() } ?? 40
    }

    /// Called when the view changes size (rotation). The simulation is untouched; only the camera
    /// framing and scenery are rebuilt.
    func layout(viewSize: CGSize) {
        let newSize = Self.sceneSize(viewSize: viewSize, displayScale: displayScale)
        guard newSize != size, viewSize.width > 0, viewSize.height > 0 else { return }
        size = newSize
        framing = Framing.for(viewSize)
        world.setBossOffset(framing.bossOffset)
        groundY = Self.groundLine(for: newSize, framing: framing)
        guard hero != nil else { return }
        buildScenery()
        render()
    }

    @available(*, unavailable)
    required init?(coder aDecoder: NSCoder) {
        fatalError("init(coder:) is not used")
    }

    // MARK: - Setup

    override func didMove(to view: SKView) {
        view.isMultipleTouchEnabled = true
        view.ignoresSiblingOrder = true
        addChild(scenery)
        buildScenery()
        actors.zPosition = 10
        addChild(actors)
        buildPlatforms()
        hero = ActorNode(sprite: "hero", library: library)
        hero.zPosition = 5
        hero.play("run")
        actors.addChild(hero)
        syncHUD()
        if let openingBanner { showBanner(openingBanner) }
        render()
    }

    private func buildScenery() {
        scenery.removeAllChildren()
        parallax.removeAll()
        groundNodes.removeAll()
        groundCrops.removeAll()
        groundMaskRects.removeAll()
        let theme = world.level.background
        if library.textures("bg_\(theme)_sky", "still").isEmpty { backgroundColor = .darkGray }
        var layers: (fill: SKNode, strip: SKNode)?
        if world.ground.pieces.contains(where: { $0.height < 0 }) {
            // Fill at -5 and strip at -4, as without dips; raised blocks go between them (-4.5).
            for z in [-5.0, -4.0] {
                let crop = SKCropNode()
                crop.maskNode = SKNode()
                crop.zPosition = CGFloat(z)
                scenery.addChild(crop)
                groundCrops.append(crop)
                groundMaskRects.append([])
            }
            layers = (groundCrops[0], groundCrops[1])
        }
        parallax = LevelBackdrop.build(theme: theme, size: size, groundY: groundY, library: library, into: scenery,
                                       groundLayers: layers)
        buildRavines(theme: theme)
        buildSlickZones()
        buildTerrain(theme: theme)
    }

    /// Sprites for raised blocks and dips (contract in docs/sprite-spec.md, "Forest terrain"),
    /// falling back to the plain ground pieces while a theme has no terrain art. Without an end cap
    /// or wall a block simply has square sides.
    private struct TerrainArt {
        let top: (texture: SKTexture, size: CGSize)
        let fill: (texture: SKTexture, size: CGSize)?
        let edge: (texture: SKTexture, size: CGSize)?
        let wall: (texture: SKTexture, size: CGSize)?
    }

    private func terrainArt(theme: String) -> TerrainArt? {
        func piece(_ names: String...) -> (texture: SKTexture, size: CGSize)? {
            for name in names {
                if let texture = library.textures(name, "still").first, let sheet = library.sheet(name) {
                    return (texture, CGSize(width: sheet.width, height: sheet.height))
                }
            }
            return nil
        }
        let prefix = "terrain_\(theme)"
        guard let top = piece("\(prefix)_top", "ground_\(theme)") else { return nil }
        return TerrainArt(top: top, fill: piece("\(prefix)_fill", "ground_\(theme)_earth", "ground_\(theme)_fill"),
                          edge: piece("\(prefix)_edge"), wall: piece("\(prefix)_wall"))
    }

    /// Screen height of a walk surface `height` above the base ground.
    private func surfaceY(_ height: Double) -> CGFloat { (groundY + CGFloat(height)).rounded() }

    /// z of terrain: a raised block sits just behind the ground strip (-4) so the base turf passes in
    /// front of its foot; a dip and the faces around it sit in front of the strip.
    private static let raisedZ: CGFloat = -4.5
    private static let dipZ: CGFloat = -3.9

    /// Raised blocks and dips. Each piece: top tiles with their frame top on the surface S, and fill
    /// behind them on the 16-unit grid from G - 48 up to the tile holding S - 16. Each seam where the
    /// height changes: an end cap on the higher side (top on its S), mirrored on a right-hand end,
    /// over walls tiled upward from the lower side's surface.
    private func buildTerrain(theme: String) {
        let ground = world.ground
        guard !ground.isFlat, let art = terrainArt(theme: theme) else { return }
        let capWidth = Double(art.edge?.size.width ?? 0)

        for piece in ground.pieces {
            let left = ground.height(leftOf: piece.at), right = ground.height(at: piece.end)
            let leftCapped = left < piece.height && art.edge != nil
            let rightCapped = right < piece.height && art.edge != nil
            // A block exactly two caps wide is only its caps and walls.
            if leftCapped, rightCapped, piece.width <= capWidth * 2 { continue }
            // Inset under a cap, 8 under a taller neighbour (1 for a dip below the base ground), flush otherwise.
            func reach(capped: Bool, neighbour: Double, seamIsBase: Bool) -> Double {
                if capped { return -capWidth }
                guard neighbour > piece.height else { return 0 }
                return piece.height < 0 && seamIsBase ? 1 : 8
            }
            let x0 = reach(capped: leftCapped, neighbour: left,
                           seamIsBase: !ground.pieces.contains { $0.end == piece.at })
            let x1 = reach(capped: rightCapped, neighbour: right,
                           seamIsBase: !ground.pieces.contains { $0.at == piece.end })
            let spanLeft = -x0, span = piece.width + x0 + x1
            guard span > 0 else { continue }

            let node = SKNode()
            node.zPosition = piece.height < 0 ? Self.dipZ : Self.raisedZ
            let surface = surfaceY(piece.height)
            let topSize = art.top.size
            if let fill = art.fill {
                // Tile bottoms on the grid G - 48 + 16k, from the lowest up to the one holding S - 16.
                let base = groundY - 48
                let rows = Int(((surface - topSize.height - base) / fill.size.height).rounded(.down))
                for row in 0...max(rows, 0) {
                    for column in Self.tileOffsets(span: span, tile: Double(fill.size.width)) {
                        let tile = SKSpriteNode(texture: fill.texture, size: fill.size)
                        tile.anchorPoint = .zero
                        tile.position = CGPoint(x: CGFloat(spanLeft + column).rounded(),
                                                y: base + CGFloat(row) * fill.size.height)
                        tile.zPosition = -0.02
                        node.addChild(tile)
                    }
                }
            }
            for column in Self.tileOffsets(span: span, tile: Double(topSize.width)) {
                let tile = SKSpriteNode(texture: art.top.texture, size: topSize)
                tile.anchorPoint = .zero
                tile.position = CGPoint(x: CGFloat(spanLeft + column).rounded(), y: surface - topSize.height)
                node.addChild(tile)
            }
            scenery.addChild(node)
            groundNodes.append((piece.at + spanLeft, span, node))
        }

        guard let edge = art.edge else { return }
        for seam in ground.edges {
            let left = ground.height(leftOf: seam), right = ground.height(at: seam)
            guard left != right else { continue }
            // The higher side gets the cap; a right-hand end is the left cap mirrored.
            let facesLeft = right > left
            let high = surfaceY(max(left, right)), low = surfaceY(min(left, right))
            let node = SKNode()
            node.zPosition = min(left, right) < 0 ? Self.dipZ : Self.raisedZ
            // The node starts at the left of the cap's column. A mirrored sprite (anchored at its
            // left edge) flips onto the span left of its position, so it is placed at the right.
            func place(_ sprite: SKSpriteNode, y: CGFloat) {
                sprite.anchorPoint = .zero
                sprite.position = CGPoint(x: facesLeft ? 0 : edge.size.width, y: y)
                if !facesLeft { sprite.xScale = -1 }
                node.addChild(sprite)
            }
            let cap = SKSpriteNode(texture: edge.texture, size: edge.size)
            cap.zPosition = 0.02
            place(cap, y: high - edge.size.height)
            if let wall = art.wall {
                // Upward from the lower side's surface until a tile reaches S - 16; behind the cap.
                var bottom = low
                while bottom < high - edge.size.height {
                    let sprite = SKSpriteNode(texture: wall.texture, size: wall.size)
                    sprite.zPosition = 0.01
                    place(sprite, y: bottom)
                    bottom += wall.size.height
                }
            }
            scenery.addChild(node)
            groundNodes.append((facesLeft ? seam : seam - Double(edge.size.width), Double(edge.size.width), node))
        }
    }

    /// Hides the base ground above the floor of each dip on screen, over [x0 - 8, x1 + 8), and shows
    /// it everywhere else. The mask is a row of rectangles: full height, or up to a dip's floor.
    private func updateGroundMask() {
        guard !groundCrops.isEmpty else { return }
        let margin: CGFloat = 8
        var holes: [(x0: CGFloat, x1: CGFloat, floor: CGFloat)] = []
        for dip in world.ground.pieces where dip.height < 0 {
            let x0 = screenX(dip.at).rounded() - margin, x1 = screenX(dip.at).rounded() + CGFloat(dip.width) + margin
            if x1 > 0, x0 < size.width { holes.append((x0, x1, surfaceY(dip.height))) }
        }
        // Cut the screen at every hole's ends; each stretch shows up to the lowest floor over it.
        var cuts: [CGFloat] = [-2, size.width + 2]
        for hole in holes { cuts += [hole.x0, hole.x1] }
        cuts = Array(Set(cuts.map { min(max($0, -2), size.width + 2) })).sorted()
        var rects: [CGRect] = []
        for (a, b) in zip(cuts, cuts.dropFirst()) where b > a {
            let middle = (a + b) / 2
            let height = holes.filter { $0.x0 <= middle && $0.x1 > middle }.map(\.floor).min() ?? size.height
            if let last = rects.last, last.maxX == a, last.height == height {
                rects[rects.count - 1].size.width += b - a
            } else {
                rects.append(CGRect(x: a, y: 0, width: b - a, height: height))
            }
        }
        for (index, crop) in groundCrops.enumerated() {
            guard let mask = crop.maskNode else { continue }
            while groundMaskRects[index].count < rects.count {
                let rect = SKSpriteNode(color: .white, size: CGSize(width: 1, height: 1))
                rect.anchorPoint = .zero
                mask.addChild(rect)
                groundMaskRects[index].append(rect)
            }
            for (slot, sprite) in groundMaskRects[index].enumerated() {
                guard slot < rects.count else {
                    sprite.isHidden = true
                    continue
                }
                sprite.isHidden = false
                sprite.position = rects[slot].origin
                sprite.size = rects[slot].size
            }
        }
    }

    /// Pits drawn over the ground strip, one per ravine; `render()` moves them with the level.
    private func buildRavines(theme: String) {
        let name = "ravine_\(theme)"
        guard let wall = library.textures(name, "still").first, let sheet = library.sheet(name),
              let dark = library.textures("\(name)_fill", "still").first else { return }
        let wallSize = CGSize(width: sheet.width, height: sheet.height)
        for ravine in world.ravines {
            let node = SKNode()
            node.zPosition = -3
            let width = CGFloat(ravine.width)
            let fill = SKSpriteNode(texture: dark, size: CGSize(width: width, height: wallSize.height))
            fill.anchorPoint = .zero
            fill.position.y = groundY - wallSize.height
            node.addChild(fill)
            // Where the earth is deeper than the drawn pit, carry its bottom colour on down.
            if groundY > wallSize.height, let bottomColour = library.textures("\(name)_deep", "still").first {
                let rest = SKSpriteNode(texture: bottomColour, size: CGSize(width: width, height: fill.position.y + 1))
                rest.anchorPoint = .zero
                node.addChild(rest)
            }
            for (x, facing) in [(0, 1.0), (width, -1.0)] {
                let side = SKSpriteNode(texture: wall, size: wallSize)
                side.anchorPoint = .zero
                side.position = CGPoint(x: x, y: fill.position.y)
                side.xScale = facing
                side.zPosition = 0.5
                node.addChild(side)
            }
            scenery.addChild(node)
            groundNodes.append((ravine.at, ravine.width, node))
        }
    }

    /// Spilled milk and ice: the zone's sprite repeated along the ground.
    private func buildSlickZones() {
        for zone in world.slick {
            let name = zone.kind ?? "milk"
            guard let texture = library.textures(name, "still").first, let sheet = library.sheet(name) else { continue }
            let node = SKNode()
            node.zPosition = -3.5
            for left in Self.tileOffsets(span: zone.width, tile: Double(sheet.width)) {
                let tile = SKSpriteNode(texture: texture, size: CGSize(width: sheet.width, height: sheet.height))
                tile.anchorPoint = CGPoint(x: 0, y: sheet.anchorY)
                tile.position = CGPoint(x: CGFloat(left), y: groundY)
                node.addChild(tile)
            }
            scenery.addChild(node)
            groundNodes.append((zone.at, zone.width, node))
        }
    }

    /// Left edges of whole tiles covering `span`: side by side, the last one pulled back so the row
    /// ends flush with the span instead of hanging past it.
    private static func tileOffsets(span: Double, tile: Double) -> [Double] {
        guard span > tile else { return [(span - tile) / 2] }
        let count = Int((span / tile).rounded(.up))
        return (0..<count).map { min(Double($0) * tile, span - tile).rounded() }
    }

    /// Ledges live with the actors (the kitten stands on them); they do not depend on screen size.
    private func buildPlatforms() {
        for (index, platform) in world.platforms.enumerated() {
            let name = platform.kind ?? "bridge"
            let sheet = library.sheet(name)
            let tileSize = CGSize(width: sheet?.width ?? 48, height: sheet?.height ?? 8)
            let node = SKNode()
            node.zPosition = 1
            var tiles: [SKSpriteNode] = []
            // A floating island is one drawn piece, centred on the ledge; the rest repeat their tile.
            let lefts = name == "island" ? [((platform.width - Double(tileSize.width)) / 2).rounded()]
                : Self.tileOffsets(span: platform.width, tile: Double(tileSize.width))
            for left in lefts {
                let tile = SKSpriteNode(texture: nil, color: sheet == nil ? .magenta : .clear, size: tileSize)
                tile.anchorPoint = .zero
                tile.position.x = CGFloat(left)
                node.addChild(tile)
                tiles.append(tile)
            }
            actors.addChild(node)
            platformViews.append(PlatformView(index: index, sprite: name, node: node, tiles: tiles,
                                              height: tileSize.height))
        }
    }

    // MARK: - Input

    // The on-screen buttons in the HUD call these; touches elsewhere on the screen do nothing.

    func setJump(held: Bool) {
        if held && !jumpHeld { jumpPending = true }
        jumpHeld = held
    }

    func setFire(held: Bool) {
        fireHeld = held
    }

    /// Paw button: a tap is a Ghost Dash, a hold then release a Super Pounce.
    func setPaw(held: Bool) {
        if held && !pawHeld { pawPending = true }
        pawHeld = held
    }

    // MARK: - Loop

    override func update(_ currentTime: TimeInterval) {
        guard !hud.isPaused, let last = lastTime else {
            // Dropping the timestamp while paused stops the pause from being replayed as one big step.
            lastTime = hud.isPaused ? nil : currentTime
            return
        }
        lastTime = currentTime
        accumulator += min(currentTime - last, 0.1) * timeScale
        while accumulator >= Self.step {
            accumulator -= Self.step
            guard !world.isOver else { break }
            let input = bot?.input(for: world, dt: Self.step)
                ?? Input(jumpPressed: jumpPending, jumpHeld: jumpHeld, fireHeld: fireHeld,
                         pawPressed: pawPending, pawHeld: pawHeld)
            jumpPending = false
            pawPending = false
            let moving = world.phase == .running || world.phase == .boss
            handle(world.step(input, dt: Self.step))
            if moving { scroll += world.runSpeed * Self.step }
        }
        render()
        syncHUD()
        if world.isOver, !reported { report() }
    }

    private func report() {
        reported = true
        let won = world.phase == .won
        play(won ? .win : .lose)
        let result = GameResult(won: won, score: world.score, xp: world.stats.xp, heroLevel: world.stats.level,
                                hearts: world.stats.hearts, fish: world.fishCollected,
                                unlocked: unlocked)
        run(.sequence([.wait(forDuration: won ? 0.6 : 1.4), .run { [onFinish] in onFinish(result) }]))
    }

    // MARK: - Events

    /// Sprite of what each thrower throws.
    private static let thrownBy: [ItemKind: String] = [
        .branchSquirrel: "acorn_thrown", .skeletonMouse: "bone", .cannon: "cannonball", .bell: "hazard_wave",
        .mushroomCat: "spore", .beeCat: "sting", .stumpCat: "leaf",
    ]
    /// Sprites for thrown hazard kinds whose `hazard_<kind>` sprite does not exist.
    private static let projectileSprite = ["bone": "bone", "cannonball": "cannonball", "soundwave": "hazard_wave",
                                           "spore": "spore", "sting": "sting", "leaf": "leaf"]
    /// Hiding animation and the pose held afterwards, for things that curl up or hide in a shell.
    private static let curlAnimation: [ItemKind: (start: String, hold: String)] = [
        .hedgehog: ("curl", "rolled"), .snailCat: ("hide", "shell"),
    ]

    private func handle(_ events: [GameEvent]) {
        for event in events {
            switch event {
            case .jumped(let double):
                play(double ? .doubleJump : .jump)
                if double {
                    doubleJumping = true
                    hero.play("double", restart: true)
                }
            case .landed:
                doubleJumping = false
                if wasPouncing {
                    wasPouncing = false
                    play(.thump)
                    burst("spark_star", count: 6, radius: 20, at: CGPoint(x: framing.heroScreenX, y: screenY(world.heroY) + 2))
                }
            case .heroHit:
                hurtUntil = world.time + 0.3
                play(.hurt)
                haptics.impactOccurred()
            case .heroDied:
                play(.hurt)
                haptics.impactOccurred()
            case .heroFell:
                dropHeroIntoRavine()
            case .stomped:
                play(.stomp)
            case .enemyHit(let id):
                entityNodes[id]?.flash()
            case .enemyDefeated(let id, _):
                retire(entityNodes.removeValue(forKey: id))
            case .fish(let id):
                play(.fish)
                if let node = entityNodes.removeValue(forKey: id) {
                    burst("spark_star", count: 5, radius: 14, at: CGPoint(x: node.position.x, y: node.position.y + 6))
                    node.run(.sequence([.group([.moveBy(x: 0, y: 14, duration: 0.2), .fadeOut(withDuration: 0.2)]),
                                        .removeFromParent()]))
                }
            case .yarnBasket:
                play(.fish)
                if let node = entityNodes.values.first(where: { $0.spriteName == ItemKind.yarnBasket.rawValue }) {
                    burst("spark_ember", count: 8, radius: 26, at: CGPoint(x: node.position.x, y: node.position.y + node.size.height / 2))
                }
            case .leveledUp(let level, let ability):
                play(.levelUp)
                if let ability {
                    unlocked.append(ability)
                    award(ability)
                } else {
                    showBanner("LV \(level)")
                }
            case .yarnThrown:
                throwUntil = world.time + 0.25
                hero.play("throw", restart: true)
                play(.yarn)
            case .dashed:
                play(.dash)
            case .pounced:
                wasPouncing = true
                play(.pounce)
            case .wallBroken(let id):
                play(.crash)
                haptics.impactOccurred()
                if let node = entityNodes.removeValue(forKey: id) {
                    node.play("break") { [weak node] in
                        node?.run(.sequence([.fadeOut(withDuration: 0.2), .removeFromParent()]))
                    }
                }
            case .yarnBounced:
                play(.block)
            case .curled(let id):
                play(.curl)
                let kind = world.entities.first { $0.id == id }?.kind
                let names = kind.flatMap { Self.curlAnimation[$0] } ?? ("curl", "rolled")
                entityNodes[id]?.play(names.start) { [weak node = entityNodes[id]] in node?.play(names.hold) }
            case .threw(let id):
                guard let entity = world.entities.first(where: { $0.id == id }) else { break }
                tagThrownHazard(from: entity)
                let node = entityNodes[id]
                let name = node?.has("throw") == true ? "throw" : "fire"
                node?.play(name, restart: true) { [weak node] in node?.play(Self.defaultAnimation[entity.kind] ?? "idle") }
                if entity.kind == .cannon { play(.cannon) }
            case .bellRang(let id):
                play(.bell)
                guard let entity = world.entities.first(where: { $0.id == id }) else { break }
                tagThrownHazard(from: entity)
                let node = entityNodes[id]
                node?.play("ring", restart: true) { [weak node] in node?.play("idle") }
            case .trapFired(let id):
                if let entity = world.entities.first(where: { $0.id == id }), isOnScreen(entity.x) {
                    switch entity.kind {
                    case .piston, .plantCat: play(.slam)
                    default: play(.flame)
                    }
                }
            case .fallWarning:
                break
            case .shattered(let id):
                if let entity = world.entities.first(where: { $0.id == id }), isOnScreen(entity.x) { play(.shatter) }
            case .bumped:
                // Stopped against a step: a squash and a puff of dust at the front paws.
                play(.thump)
                hero.run(.sequence([.scaleX(to: 1.15, y: 0.82, duration: 0.05), .scale(to: 1, duration: 0.15)]),
                         withKey: "bump")
                dust(at: CGPoint(x: framing.heroScreenX + CGFloat(world.tuning.heroWidth / 2), y: screenY(world.heroY) + 2))
            case .hazardBroke(let id):
                if let node = hazardNodes.removeValue(forKey: id) {
                    if node.position.x > -20, node.position.x < size.width + 20 { dust(at: node.position) }
                    node.removeFromParent()
                }
            case .droppedDown(let id):
                if let entity = world.entities.first(where: { $0.id == id }), isOnScreen(entity.x) { play(.thump) }
            case .platformCrumbling(let index):
                crumbleStart[index] = world.time
                play(.crumble)
            case .yarnGone(let id, let hit):
                guard let node = shotNodes.removeValue(forKey: id) else { break }
                if hit {
                    play(.impact)
                    node.play("impact") { [weak node] in node?.removeFromParent() }
                } else {
                    node.removeFromParent()
                }
            case .bossAppeared(let id):
                play(.bossRoar)
                showBanner(text("\(id).name").uppercased())
            case .bossTelegraph, .bossAttack:
                break
            case .bossHit:
                play(.bossHit)
                bossHurtUntil = world.time + 0.25
                trueBossNode?.flash()
            case .bossBlocked:
                play(.block)
                trueBossNode?.flash(.gray, duration: 0.06)
            case .bossDefeated:
                let real = trueBossNode
                real?.play("death")
                for node in bossNodes where node !== real {
                    node.run(.sequence([.fadeOut(withDuration: 0.3), .removeFromParent()]))
                }
            case .levelComplete:
                break
            }
        }
    }

    /// Remembers which sprite the hazard `entity` just threw should use. The new hazard is the one
    /// not yet drawn nearest to where throws start (just in front of the thrower).
    private func tagThrownHazard(from entity: Entity) {
        guard let sprite = Self.thrownBy[entity.kind] else { return }
        let fresh = world.hazards.filter { hazardNodes[$0.id] == nil && thrownSprite[$0.id] == nil }
        if let hazard = fresh.min(by: { abs($0.x - (entity.x - 10)) < abs($1.x - (entity.x - 10)) }) {
            thrownSprite[hazard.id] = sprite
        }
    }

    private func isOnScreen(_ worldX: Double) -> Bool {
        let x = screenX(worldX)
        return x > -20 && x < size.width + 20
    }

    /// Drops the hero out of sight. The crop keeps them behind the ground on either side of the pit.
    private func dropHeroIntoRavine() {
        fell = true
        hero.play("fall")
        guard let ravine = world.ravines.first(where: { $0.isOpen(at: world.distance) }) else { return }
        let sky = SKSpriteNode(color: .white, size: CGSize(width: size.width, height: size.height - groundY))
        sky.anchorPoint = .zero
        sky.position.y = groundY
        let pit = SKSpriteNode(color: .white, size: CGSize(width: CGFloat(ravine.width), height: groundY))
        pit.anchorPoint = .zero
        pit.position.x = screenX(ravine.at)
        let mask = SKNode()
        mask.addChild(sky)
        mask.addChild(pit)
        let crop = SKCropNode()
        crop.maskNode = mask
        crop.zPosition = hero.zPosition
        hero.removeFromParent()
        crop.addChild(hero)
        actors.addChild(crop)
        let drop = SKAction.moveBy(x: 0, y: -(groundY + hero.size.height), duration: 0.5)
        drop.timingMode = .easeIn
        hero.run(drop)
    }

    private func retire(_ node: ActorNode?) {
        guard let node else { return }
        if node.has("death") {
            node.play("death") { [weak node] in node?.removeFromParent() }
        } else {
            node.run(.sequence([.fadeOut(withDuration: 0.15), .removeFromParent()]))
        }
    }

    /// A ring of small sprites flying out from `origin` and fading.
    private func burst(_ sprite: String, count: Int, radius: CGFloat, at origin: CGPoint) {
        guard let texture = library.textures(sprite, "still").first else { return }
        for index in 0..<count {
            let angle = CGFloat(index) / CGFloat(count) * 2 * .pi + 0.3
            let node = SKSpriteNode(texture: texture)
            node.position = origin
            node.zPosition = 7
            actors.addChild(node)
            let fly = SKAction.moveBy(x: cos(angle) * radius, y: sin(angle) * radius, duration: 0.35)
            fly.timingMode = .easeOut
            node.run(.sequence([.group([fly, .sequence([.wait(forDuration: 0.2), .fadeOut(withDuration: 0.15)])]),
                                .removeFromParent()]))
        }
    }

    /// A few earth-coloured pixels kicked up and fading.
    private func dust(at origin: CGPoint) {
        for (index, (dx, dy)) in [(-6.0, 5.0), (-3.0, 8.0), (2.0, 7.0), (-8.0, 2.0), (4.0, 3.0)].enumerated() {
            let node = SKSpriteNode(color: SKColor(red: 0.72, green: 0.62, blue: 0.46, alpha: 1),
                                    size: CGSize(width: index % 2 == 0 ? 2 : 1, height: index % 2 == 0 ? 2 : 1))
            node.position = CGPoint(x: origin.x.rounded(), y: origin.y.rounded())
            node.zPosition = 7
            actors.addChild(node)
            let fly = SKAction.moveBy(x: dx, y: dy, duration: 0.3)
            fly.timingMode = .easeOut
            node.run(.sequence([.group([fly, .sequence([.wait(forDuration: 0.15), .fadeOut(withDuration: 0.15)])]),
                                .removeFromParent()]))
        }
    }

    /// A new ability is the big moment of a run: an award card on the HUD and a burst around the hero.
    private func award(_ ability: Ability) {
        hud.award = ability
        awardUntil = world.time + 2.6
        hero.flash(.yellow, duration: 0.25)
        // Centred on the kitten's body, whatever size its frame is.
        let origin = CGPoint(x: hero.position.x, y: hero.position.y + hero.size.height / 2)

        if let star = library.textures("spark_star", "still").first {
            let count = 10
            for index in 0..<count {
                let angle = CGFloat(index) / CGFloat(count) * 2 * .pi
                let node = SKSpriteNode(texture: star)
                node.position = origin
                node.zPosition = 7
                actors.addChild(node)
                let fly = SKAction.moveBy(x: cos(angle) * 48, y: sin(angle) * 48, duration: 0.6)
                fly.timingMode = .easeOut
                node.run(.sequence([.group([fly, .rotate(byAngle: .pi, duration: 0.6),
                                            .sequence([.wait(forDuration: 0.35), .fadeOut(withDuration: 0.25)])]),
                                    .removeFromParent()]))
            }
        }
        // Feathers for the pounce, curls of yarn for the rest.
        let rising = ability == .doublePounce ? "spark_feather" : "spark_ember"
        if let texture = library.textures(rising, "still").first {
            for (index, offset) in [-16, 9, -5, 15, -11, 3, 12, -8].enumerated() {
                let node = SKSpriteNode(texture: texture)
                node.position = CGPoint(x: origin.x + CGFloat(offset), y: hero.position.y + CGFloat(index % 3) * hero.size.height / 5)
                node.zPosition = 7
                node.alpha = 0
                actors.addChild(node)
                let rise = SKAction.moveBy(x: CGFloat(offset) * 0.3, y: 46, duration: 0.8)
                rise.timingMode = .easeOut
                node.run(.sequence([.wait(forDuration: Double(index) * 0.07), .fadeIn(withDuration: 0.05),
                                    .group([rise, .sequence([.wait(forDuration: 0.45), .fadeOut(withDuration: 0.35)])]),
                                    .removeFromParent()]))
            }
        }
    }

    private func showBanner(_ message: String) {
        hud.banner = message
        bannerUntil = world.time + 2.2
    }

    private func play(_ sound: Sound) {
        sounds?.play(sound)
    }

    // MARK: - Drawing

    private func screenX(_ worldX: Double) -> CGFloat {
        CGFloat(worldX - world.distance) + framing.heroScreenX
    }

    private func screenY(_ worldY: Double) -> CGFloat {
        CGFloat(worldY) + groundY
    }

    private func render() {
        for layer in parallax { layer.scroll(to: CGFloat(scroll)) }
        for (at, width, node) in groundNodes {
            node.position.x = screenX(at).rounded()
            node.isHidden = node.position.x > size.width || node.position.x + CGFloat(width) < 0
        }
        updateGroundMask()
        renderPlatforms()
        renderHero()
        renderEntities()
        renderHazards()
        renderShots()
        renderBoss()
    }

    private func renderHero() {
        guard !fell else { return }
        hero.position = CGPoint(x: framing.heroScreenX, y: screenY(world.heroY))
        // Blink while hit-immune so the player can see the grace period.
        let blinking = world.invulnerable > 0 && world.phase != .dead && world.phase != .victory
        hero.alpha = blinking && Int(world.time * 16) % 2 == 0 ? 0.35 : 1

        switch world.phase {
        case .dead:
            hero.play("death")
        case .victory, .won:
            if hero.current != "stop", hero.current != "idle" {
                hero.play("stop") { [weak hero] in hero?.play("idle") }
            }
        case .running, .boss:
            if world.time < hurtUntil {
                hero.play("hurt")
            } else if world.isDashing {
                hero.play("dash")
            } else if world.pouncing {
                hero.play("pounce")
            } else if world.time < throwUntil {
                // Started by the throw itself; it plays through once.
            } else if !world.onGround {
                if doubleJumping, world.heroVY > 0 {
                    hero.play("double")
                } else {
                    hero.play(world.heroVY > 0 ? "jump" : "fall")
                }
            } else {
                hero.play("run")
            }
        }
    }

    private static let defaultAnimation: [ItemKind: String] = [
        .squirrel: "walk", .hedgehog: "walk", .skeletonMouse: "idle", .branchSquirrel: "idle", .cannon: "idle",
        .acorn: "roll", .snowball: "roll", .penguin: "slide", .mechMouse: "run",
        .ghostCat: "float", .bat: "fly", .skull: "fly", .bell: "idle", .gear: "spin",
        .vent: "idle", .piston: "up", .icicle: "hang", .debris: "hang",
        .slime: "walk", .mushroomCat: "idle", .forestBat: "fly", .plantCat: "idle", .beeCat: "fly",
        .stumpCat: "idle", .snailCat: "walk", .spiderCat: "hang",
        .fish: "spin", .yarnBasket: "glow",
    ]

    private func renderEntities() {
        var seen = Set<Int>()
        for entity in world.entities {
            seen.insert(entity.id)
            let node = entityNodes[entity.id] ?? makeEntityNode(entity)
            node.position = CGPoint(x: screenX(entity.x), y: screenY(entity.y))
            node.xScale = entity.reversed ? -1 : 1
            node.alpha = 1
            node.colorBlendFactor = 0
            animate(node, for: entity)
        }
        for (id, node) in entityNodes where !seen.contains(id) {
            node.removeFromParent()
            entityNodes[id] = nil
        }
    }

    /// Animations that follow an entity's state rather than an event.
    private func animate(_ node: ActorNode, for entity: Entity) {
        let blink = Int(world.time * 12) % 2 == 0
        switch entity.kind {
        case .vent, .piston:
            let names = entity.kind == .vent ? ["idle", "warn", "fire"] : ["up", "warn", "slam"]
            switch entity.state {
            case .warning: node.play(names[1])
            case .active: node.play(names[2])
            default: node.play(names[0])
            }
        case .icicle, .debris:
            switch entity.state {
            case .warning:
                node.play("hang")
                // About to drop: flash white so it reads as a warning, not scenery.
                node.color = .white
                node.colorBlendFactor = blink ? 0.7 : 0
            case .active: node.play("fall")
            case .landed: node.play("shatter")
            default: node.play("hang")
            }
        case .ghostCat:
            switch entity.state {
            case .hidden:
                // Blinks out, then only a faint shimmer shows where it drifts.
                if node.current == "float" { node.play("fade") }
                if !node.isBusy { node.alpha = 0.12 }
            case .warning:
                if node.current == "fade", !node.isBusy { node.play("float") }
                node.alpha = blink ? 0.6 : 0.25
            default:
                node.play("float")
            }
        case .hedgehog, .snailCat:
            // Normally started by the `curled` event; this catches a node made after it fired.
            let names = Self.curlAnimation[entity.kind] ?? ("curl", "rolled")
            if entity.state == .curled, node.current == "walk" {
                node.play(names.start) { [weak node] in node?.play(names.hold) }
            }
        case .plantCat:
            switch entity.state {
            case .warning: node.play("warn")
            case .active: node.play("bite")
            default: node.play("idle")
            }
        case .spiderCat:
            switch entity.state {
            case .warning:
                node.play("hang")
                // About to let go: flash so the drop is announced.
                node.color = .white
                node.colorBlendFactor = blink ? 0.7 : 0
            case .active: node.play("drop")
            case .landed: node.play("walk")
            default: node.play("hang")
            }
        default:
            break
        }
    }

    private func makeEntityNode(_ entity: Entity) -> ActorNode {
        let node = ActorNode(sprite: entity.kind.rawValue, library: library)
        node.zPosition = entity.kind == .yarnBasket ? 1 : (entity.kind == .crateWall ? 4 : 3)
        node.play(Self.defaultAnimation[entity.kind] ?? "still")
        actors.addChild(node)
        entityNodes[entity.id] = node
        return node
    }

    /// Ledges follow `platformState`: whole while solid, crumble frames paced over the crumble time,
    /// and gone once they give way. A blinking ledge flickers through its fading frames before it vanishes.
    private func renderPlatforms() {
        for view in platformViews {
            let platform = world.platforms[view.index]
            view.node.position = CGPoint(x: screenX(platform.at).rounded(), y: screenY(platform.y) - view.height)
            let state = world.platformState(view.index)
            var texture: SKTexture?
            switch (platform.mode, state) {
            case (_, .solid):
                texture = (library.textures(view.sprite, "still").first ?? library.textures(view.sprite, "solid").first)
            case (.blinks, .crumbling):
                let frames = library.textures(view.sprite, "fading")
                texture = frames.isEmpty ? nil : frames[Int(world.time * 8) % frames.count]
            case (_, .crumbling):
                let frames = library.textures(view.sprite, "crumble")
                let elapsed = world.time - (crumbleStart[view.index] ?? world.time)
                let span = platform.crumbleAfter ?? Platform.defaultCrumbleAfter
                // All but the last frame while it still holds; the last one as it drops away.
                let index = Int(elapsed / span * Double(max(frames.count - 1, 1)))
                texture = frames.isEmpty ? nil : frames[min(index, max(frames.count - 2, 0))]
            case (.crumbles, .gone):
                let frames = library.textures(view.sprite, "crumble")
                let goneAt = (crumbleStart[view.index] ?? 0) + (platform.crumbleAfter ?? Platform.defaultCrumbleAfter)
                texture = world.time - goneAt < 0.15 ? frames.last : nil
            case (_, .gone):
                texture = nil
            }
            view.node.isHidden = texture == nil || view.node.position.x > size.width
                || view.node.position.x + CGFloat(platform.width) < 0
            for tile in view.tiles { tile.texture = texture }
        }
    }

    private func renderHazards() {
        var seen = Set<Int>()
        for hazard in world.hazards {
            seen.insert(hazard.id)
            let node: ActorNode
            if let existing = hazardNodes[hazard.id] {
                node = existing
            } else {
                let sprite = thrownSprite[hazard.id] ?? Self.projectileSprite[hazard.kind] ?? "hazard_\(hazard.kind)"
                node = ActorNode(sprite: sprite, library: library)
                node.zPosition = 4
                node.play("fly")
                actors.addChild(node)
                hazardNodes[hazard.id] = node
            }
            node.position = CGPoint(x: screenX(hazard.x), y: screenY(hazard.y))
            // A hazard that is still arming is only a warning: faint and blinking.
            node.alpha = hazard.isArmed ? 1 : (Int(world.time * 12) % 2 == 0 ? 0.25 : 0.55)
        }
        for (id, node) in hazardNodes where !seen.contains(id) {
            node.removeFromParent()
            hazardNodes[id] = nil
        }
        for id in thrownSprite.keys where !seen.contains(id) && hazardNodes[id] == nil {
            thrownSprite[id] = nil
        }
    }

    private func renderShots() {
        for shot in world.projectiles {
            let node: ActorNode
            if let existing = shotNodes[shot.id] {
                node = existing
            } else {
                node = ActorNode(sprite: "yarn", library: library)
                node.anchorPoint = CGPoint(x: 0.5, y: 0.5)
                node.zPosition = 6
                node.play("fly")
                actors.addChild(node)
                shotNodes[shot.id] = node
            }
            node.position = CGPoint(x: screenX(shot.x), y: screenY(shot.y + shot.size / 2))
        }
    }

    /// Animation a boss plays for an attack. Names not listed fall back to an animation whose name
    /// is part of the attack's name, then to the boss's "*".
    private static let attackAnimation: [String: [String: String]] = [
        "boss_squirrel": ["acorn_arc": "throw", "acorn_roll": "roll", "giant_acorn": "climb", "*": "throw"],
        "boss_icedragon": ["shard_fan": "shards", "freezing_breath": "breath", "dive": "dive", "*": "breath"],
        "boss_phantom": ["summon_ghosts": "summon", "spectral_waves": "teleport", "split": "split", "*": "summon"],
        "boss_mecha": ["rockets": "rockets", "tail_sweep": "tail", "core_barrage": "core", "*": "rockets"],
    ]

    private func attackAnimation(boss: String, attack: String) -> String {
        let table = Self.attackAnimation[boss] ?? [:]
        if let name = table[attack] { return name }
        let own = library.sheet(boss)?.animations.keys.sorted() ?? []
        if let name = own.first(where: { !["idle", "hurt", "death"].contains($0) && attack.contains($0) }) { return name }
        return table["*"] ?? "idle"
    }

    /// The copy that takes damage.
    private var trueBossNode: ActorNode? {
        guard let state = world.bossState, !bossNodes.isEmpty else { return bossNodes.first }
        return bossNodes[min(state.trueCopy, bossNodes.count - 1)]
    }

    private func renderBoss() {
        guard let state = world.bossState else { return }
        if state.action != .dead {
            while bossNodes.count < state.copies {
                let node = ActorNode(sprite: state.id, library: library)
                node.zPosition = 2
                node.play(bossNodes.isEmpty ? "idle" : (node.has("teleport") ? "teleport" : "idle"))
                actors.addChild(node)
                bossNodes.append(node)
            }
            while bossNodes.count > state.copies {
                bossNodes.removeLast().removeFromParent()
            }
        }
        // Slides in from off-screen during the intro.
        let entering = state.action == .intro ? max(0, 1 - state.actionTime / world.tuning.bossIntro) : 0
        let xs = state.copyXs
        let core = world.boss.map { boss in boss.armoredAbove.map { state.hpFraction <= $0 } ?? false } ?? false
        let rest = core && bossNodes.first?.has("core") == true ? "core" : "idle"

        for (index, node) in bossNodes.enumerated() {
            let x = xs.indices.contains(index) ? xs[index] : state.x
            node.position = CGPoint(x: screenX(x) + CGFloat(entering) * 180, y: groundY)
            guard state.action != .dead else { continue }
            if state.copies > 1, index == state.trueCopy, node.has("split") {
                // The real one glows; the look-alikes act out the attack.
                if !(node.current == "teleport" && node.isBusy) { node.play("split") }
                node.alpha = 1
                continue
            }
            node.alpha = state.copies > 1 ? 0.7 : 1
            switch state.action {
            case .dead:
                break
            case .intro:
                node.play(world.time < bossHurtUntil ? "hurt" : "idle")
            case .telegraph, .attack:
                // The wind-up is the first frames of the attack animation, so it reads as a warning.
                var name = attackAnimation(boss: state.id, attack: state.attackName)
                // Only the real copy glows; look-alikes stand idle through a split.
                if name == "split", state.copies > 1 { name = "idle" }
                if node.current != name, !(node.current == "teleport" && node.isBusy) { node.play(name) }
            case .recover:
                if world.time < bossHurtUntil, node.has("hurt") {
                    node.play("hurt")
                } else if !node.isBusy || node.current == "hurt" {
                    node.play(rest)
                }
            }
        }
    }

    private func syncHUD() {
        let stats = world.stats
        show(\.hearts, stats.hearts)
        show(\.maxHearts, stats.maxHearts)
        show(\.heroLevel, stats.level)
        show(\.fish, world.fishCollected)
        if let needed = Progression.xpToNext(fromXP: stats.xp) {
            let floor = Progression.xp(forLevel: stats.level)
            show(\.xpFraction, Double(stats.xp - floor) / Double(stats.xp - floor + needed))
        } else {
            show(\.xpFraction, 1)
        }
        show(\.canFire, stats.has(.yarnShot))
        show(\.canDash, stats.has(.ghostDash))
        show(\.canPounce, stats.has(.superPounce))
        show(\.dashReady, world.canDash)
        show(\.canDoubleJump, stats.has(.doublePounce))
        // Quantised so the ring does not redraw the SwiftUI overlay on every frame of a hold.
        let charge = stats.has(.superPounce) ? min(1, world.pawCharge / world.tuning.chargeTime) : 0
        show(\.pounceCharge, (charge * 20).rounded() / 20)
        if let boss = world.bossState, world.phase == .boss {
            show(\.bossName, text("\(boss.id).name"))
            show(\.bossFraction, boss.hpFraction)
        } else {
            show(\.bossName, nil)
        }
        if hud.banner != nil, world.time > bannerUntil { hud.banner = nil }
        if hud.award != nil, world.time > awardUntil { hud.award = nil }
    }

    /// Writes a HUD value only when it differs. Every write redraws the SwiftUI overlay, even one
    /// that changes nothing, and this runs each frame.
    private func show<Value: Equatable>(_ field: ReferenceWritableKeyPath<GameHUD, Value>, _ value: Value) {
        if hud[keyPath: field] != value { hud[keyPath: field] = value }
    }
}
