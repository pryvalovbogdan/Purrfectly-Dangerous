import GameCore
import SpriteKit
import UIKit
#if DEBUG
import os
#endif

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
    /// The backdrop seen down in a dip: per floor height, a copy of the sky band and parallax layers
    /// seated on that floor, cropped to the holes above floors of that height (see `updateGroundMask`).
    private var holeScenery: [(height: Double, crop: SKCropNode, rects: [SKSpriteNode])] = []
    /// Looping scenery tiles (waterfall curtains, pool surface, splashes). Their frame is picked from
    /// the world clock in `render()`, so every tile of a kind shows the same frame and none drift.
    private var clockAnimated: [(node: SKSpriteNode, owner: SKNode, frames: [SKTexture], fps: Double)] = []
    /// Pool surface of the waterfall pits (nil for a plain pit): a kitten falling in sinks out of
    /// sight there instead of dropping past the floor over the earth.
    private var pitWaterY: CGFloat?
    /// Frames per second of that shared clock: the waterfall curtain's rate.
    private var clockRate = 10.0
    /// The hero went down a ravine: the drop is animated here, so `renderHero` leaves them alone.
    private var fell = false
    private let scenery = SKNode()
    private let actors = SKNode()
    private var hero: ActorNode!
    /// One node per boss copy; index 0 stands at the boss position, the rest are the phantom's decoys.
    private var bossNodes: [ActorNode] = []
    private var entityNodes: [Int: ActorNode] = [:]
    private var hazardNodes: [Int: ActorNode] = [:]
    /// Each open portal pair: the entry and the exit node.
    private var portalNodes: [Int: (entry: ActorNode, exit: ActorNode)] = [:]
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
    /// The hero's sprite: the recoloured `hero_<skin>` of the cat in use, or `hero`. Looks only.
    var heroSprite = "hero"

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

    /// How far the ground line is above the bottom of a game view of `viewSize`, in points (for the
    /// HUD to keep its buttons on the earth below it).
    static func groundHeight(viewSize: CGSize, displayScale: CGFloat) -> CGFloat {
        let scene = sceneSize(viewSize: viewSize, displayScale: max(displayScale, 1))
        guard scene.height > 0 else { return 0 }
        return groundLine(for: scene, framing: Framing.for(viewSize)) * viewSize.height / scene.height
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
        hero = ActorNode(sprite: library.sheet(heroSprite) != nil ? heroSprite : "hero", library: library, fallback: "hero")
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
        holeScenery.removeAll()
        clockAnimated.removeAll()
        pitWaterY = nil
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
        // Above a dip's floor the ground is gone, and the backdrop (standing on the ground line) has
        // nothing below it. Seat a copy of it on each floor height, so the hole shows the foot of the
        // same scenery, scrolling with it. Behind the ground and the dip pieces, in front of the sky.
        for height in Set(world.ground.pieces.filter { $0.height < 0 }.map(\.height)).sorted() {
            let crop = SKCropNode()
            crop.maskNode = SKNode()
            crop.zPosition = -5.2
            parallax += LevelBackdrop.standingLayers(theme: theme, size: size, standingOn: surfaceY(height),
                                                     library: library, into: crop, withSky: true)
            // Keep their order inside the crop, but within its own z.
            for child in crop.children { child.zPosition = (child.zPosition + 10) * 0.01 }
            scenery.addChild(crop)
            holeScenery.append((height, crop, []))
        }
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

    /// z of terrain: a raised run sits just behind the ground strip (-4) so the base turf passes in
    /// front of its foot; a dip and the faces around it sit in front of the strip.
    private static let raisedZ: CGFloat = -4.5
    private static let dipZ: CGFloat = -3.9

    /// Raised blocks and dips, one node per run of touching pieces, laid out by `TerrainLayout`: the
    /// run's fill through a crop shaped like its outline, then its walls, caps and top tiles.
    private func buildTerrain(theme: String) {
        let ground = world.ground
        guard !ground.isFlat, let art = terrainArt(theme: theme) else { return }
        func size(_ piece: (texture: SKTexture, size: CGSize)?) -> (width: Double, height: Double)? {
            piece.map { (Double($0.size.width), Double($0.size.height)) }
        }
        let sizes = TerrainLayout.Sizes(top: size(art.top)!, fill: size(art.fill), edge: size(art.edge),
                                        wall: size(art.wall))
        func piece(_ role: TerrainLayout.Role) -> (texture: SKTexture, size: CGSize)? {
            switch role {
            case .top: art.top
            case .fill: art.fill
            case .edge: art.edge
            case .wall: art.wall
            }
        }
        func sprite(_ placed: TerrainLayout.Sprite) -> SKSpriteNode? {
            guard let piece = piece(placed.role) else { return nil }
            let node = SKSpriteNode(texture: piece.texture, size: piece.size)
            node.anchorPoint = .zero
            // A mirrored sprite (anchored at its left edge) flips onto the span left of its position.
            node.position = CGPoint(x: CGFloat(placed.mirrored ? placed.x + Double(piece.size.width) : placed.x).rounded(),
                                    y: (groundY + CGFloat(placed.y)).rounded())
            node.xScale = placed.mirrored ? -1 : 1
            node.zPosition = CGFloat(placed.z) * 0.01
            return node
        }

        for run in TerrainLayout.runs(ground, sizes: sizes) {
            let node = SKNode()
            node.zPosition = run.isDip ? Self.dipZ : Self.raisedZ
            if !run.fills.isEmpty {
                let crop = SKCropNode()
                let mask = SKNode()
                for rect in run.mask {
                    let shape = SKSpriteNode(color: .white, size: CGSize(width: rect.width, height: rect.height))
                    shape.anchorPoint = .zero
                    shape.position = CGPoint(x: CGFloat(rect.x).rounded(), y: (groundY + CGFloat(rect.y)).rounded())
                    mask.addChild(shape)
                }
                crop.maskNode = mask
                for placed in run.fills { if let tile = sprite(placed) { crop.addChild(tile) } }
                node.addChild(crop)
            }
            for placed in run.sprites { if let tile = sprite(placed) { node.addChild(tile) } }
            scenery.addChild(node)
            groundNodes.append((run.origin, run.width, node))
        }
    }

    /// Hides the base ground above the floor of each dip on screen, over [x0 - 8, x1 + 8), and shows
    /// it everywhere else. The mask is a row of rectangles: full height, or up to a dip's floor.
    private func updateGroundMask() {
        guard !groundCrops.isEmpty else { return }
        let margin: CGFloat = 8
        var holes: [(x0: CGFloat, x1: CGFloat, floor: CGFloat)] = []
        for dip in world.ground.pieces where dip.height < 0 {
            let x0 = groundScreenX(dip.at) - margin, x1 = groundScreenX(dip.at) + CGFloat(dip.width) + margin
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
        // The hole above each dip's floor (the same span), for the backdrop seated on that floor.
        for index in holeScenery.indices {
            let height = holeScenery[index].height
            var holeRects: [CGRect] = []
            for dip in world.ground.pieces where dip.height == height {
                let x0 = groundScreenX(dip.at) - margin, x1 = x0 + CGFloat(dip.width) + 2 * margin
                let floor = surfaceY(dip.height)
                if x1 > 0, x0 < size.width { holeRects.append(CGRect(x: x0, y: floor, width: x1 - x0, height: groundY - floor)) }
            }
            holeScenery[index].crop.isHidden = holeRects.isEmpty
            guard let mask = holeScenery[index].crop.maskNode else { continue }
            while holeScenery[index].rects.count < holeRects.count {
                let rect = SKSpriteNode(color: .white, size: CGSize(width: 1, height: 1))
                rect.anchorPoint = .zero
                mask.addChild(rect)
                holeScenery[index].rects.append(rect)
            }
            for (slot, sprite) in holeScenery[index].rects.enumerated() {
                sprite.isHidden = slot >= holeRects.count
                guard slot < holeRects.count else { continue }
                sprite.position = holeRects[slot].origin
                sprite.size = holeRects[slot].size
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

    /// Pits drawn over the ground strip, one per ravine; `render()` moves them with the level. A theme
    /// with waterfall art gets waterfall pits; the rest (and the forest until its art exists) the plain pit.
    private func buildRavines(theme: String) {
        if buildWaterfallPits(theme: theme) { return }
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

    /// A sprite's frames: the named animation, or its only one.
    private func frames(_ sprite: String, _ preferred: String) -> (frames: [SKTexture], size: CGSize, fps: Double)? {
        guard let sheet = library.sheet(sprite), let name = library.animationName(sprite, preferring: preferred) else {
            return nil
        }
        let textures = library.textures(sprite, name)
        guard !textures.isEmpty else { return nil }
        return (textures, CGSize(width: sheet.width, height: sheet.height), library.animation(sprite, name)?.fps ?? 8)
    }

    /// The forest's waterfall pit (contract in docs/sprite-spec.md, "waterfall pit"). Pit [x0, x1),
    /// `a` = x0 + 8 and `b` = x1 - 8 between the wall faces, `G` the ground line, `P` the pool surface.
    /// Back to front: back wall, the curtain across [a, b) with its two edges, the lip, the water,
    /// the splash band, the walls, the vines and the rims. Whole sprites at whole pixels; tiles are
    /// pulled back inside their span rather than cut. Returns false (drawing nothing) if a required
    /// piece is missing, and the plain pit is drawn instead.
    private func buildWaterfallPits(theme: String) -> Bool {
        let name = "ravine_\(theme)"
        guard let wall = frames(name, "still"), let rim = frames("\(name)_rim", "still"),
              let back = frames("\(name)_back", "still"), let falls = frames("\(name)_falls", "flow"),
              let fallsEdge = frames("\(name)_falls_edge", "flow"), let lip = frames("\(name)_lip", "flow"),
              let surface = frames("\(name)_surface", "wave"), let pool = frames("\(name)_pool", "churn"),
              let splash = frames("\(name)_splash", "splash"), let floorTile = frames("\(name)_floor", "still")
        else { return false }
        let wallB = frames("\(name)_b", "still") ?? wall
        let vines = frames("\(name)_vines", "still")
        let G = groundY
        // The pool sits 40 below the ground line, less where the line is low (landscape) so 18 of water
        // stays on screen. `layout(viewSize:)` rebuilds the scenery on rotation.
        let P = G - min(40, G - 18)
        clockRate = falls.fps

        for ravine in world.ravines {
            let node = SKNode()
            node.zPosition = -3
            let x1 = CGFloat(ravine.width)
            let a: CGFloat = 8, b = x1 - 8
            var z: CGFloat = 0
            func add(_ piece: (frames: [SKTexture], size: CGSize, fps: Double), x: CGFloat, top: CGFloat,
                     mirrored: Bool = false) {
                let sprite = SKSpriteNode(texture: piece.frames[0], size: piece.size)
                sprite.anchorPoint = .zero
                // A mirrored sprite (anchored at its left edge) flips onto the span left of its position.
                sprite.position = CGPoint(x: (mirrored ? x + piece.size.width : x).rounded(),
                                          y: (top - piece.size.height).rounded())
                sprite.xScale = mirrored ? -1 : 1
                sprite.zPosition = z
                node.addChild(sprite)
                if piece.frames.count > 1 { clockAnimated.append((sprite, node, piece.frames, piece.fps)) }
            }
            /// Left edges of whole tiles across [from, to).
            func across(_ from: CGFloat, _ to: CGFloat, _ tile: CGSize) -> [CGFloat] {
                Self.tileOffsets(span: Double(to - from), tile: Double(tile.width)).map { from + CGFloat($0) }
            }

            // 1. Back wall across the pit, tops on G, G - 16, … down to P - 8.
            var top = G
            while top > P - 8 {
                for x in across(0, x1, back.size) { add(back, x: x, top: top) }
                top -= back.size.height
            }
            // 2–3. The curtain across [a, b) while its top is above P, with an edge at a and a mirrored one at b - 4.
            z = 1
            top = G
            while top > P {
                for x in across(a, b, falls.size) { add(falls, x: x, top: top) }
                top -= falls.size.height
            }
            z = 2
            top = G
            while top > P {
                add(fallsEdge, x: a, top: top)
                add(fallsEdge, x: b - fallsEdge.size.width, top: top, mirrored: true)
                top -= fallsEdge.size.height
            }
            // 4. The lip where the water pours over, top on G.
            z = 3
            for x in across(a, b, lip.size) { add(lip, x: x, top: G) }
            // 5. Water: surface on P, churning pool on P - 8, deep from P - 32 down, fading out at the bottom.
            z = 4
            for x in across(a, b, surface.size) { add(surface, x: x, top: P) }
            for x in across(a, b, pool.size) { add(pool, x: x, top: P - 8) }
            // 6. The foam band across [a, b), top on P + 8.
            z = 5
            for x in across(a, b, splash.size) { add(splash, x: x, top: P + 8) }
            // 7. The pit's floor, top on P - 32 (down to P - 48). Below it nothing is drawn, so the ground
            // strip's earth shows there as everywhere else.
            z = 5.5
            for x in across(a, b, floorTile.size) { add(floorTile, x: x, top: P - 32) }
            // 8. Walls at x0 and mirrored at [x1 - 8, x1), tops on G - 24, G - 40, … alternating, until a
            // tile's bottom reaches P - 48 (the last may overshoot below the floor).
            z = 6
            top = G - 24
            var alternate = false
            while top > P - 48 {
                let piece = alternate ? wallB : wall
                add(piece, x: 0, top: top)
                add(piece, x: x1 - piece.size.width, top: top, mirrored: true)
                alternate.toggle()
                top -= wall.size.height
            }
            // 9. Vines hanging from under the rims.
            z = 7
            if let vines {
                add(vines, x: 5, top: G - 14)
                add(vines, x: x1 - 5 - vines.size.width, top: G - 14, mirrored: true)
            }
            // 10. Rims on top, at x0 and mirrored at [x1 - 12, x1).
            z = 8
            add(rim, x: 0, top: G)
            add(rim, x: x1 - rim.size.width, top: G, mirrored: true)

            scenery.addChild(node)
            groundNodes.append((ravine.at, ravine.width, node))
        }
        pitWaterY = P
        return true
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
            let kind = platform.kind ?? "bridge"
            // The level's own look of the piece (`island_citadel`, `bridge_frost`, …) when drawn.
            let themed = "\(kind)_\(world.level.background)"
            let name = library.sheet(themed) != nil ? themed : kind
            let sheet = library.sheet(name)
            let tileSize = CGSize(width: sheet?.width ?? 48, height: sheet?.height ?? 8)
            let node = SKNode()
            node.zPosition = 1
            var tiles: [SKSpriteNode] = []
            // A floating island is one drawn piece, centred on the ledge; the rest repeat their tile.
            let lefts = kind == "island" ? [((platform.width - Double(tileSize.width)) / 2).rounded()]
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
        #if DEBUG
        trace.notice("setJump held=\(held, privacy: .public) t=\(CACurrentMediaTime(), format: .fixed(precision: 3), privacy: .public) worldTime=\(self.world.time, format: .fixed(precision: 3), privacy: .public)")
        #endif
        if held && !jumpHeld { jumpPending = true }
        jumpHeld = held
    }

    #if DEBUG
    // Jump trace (debug builds only): every press and release from the button, the held state each
    // step sends to the world when it changes, and each jump's apex. Read it with
    // `xcrun simctl spawn booted log show --predicate 'category == "jump"'`.
    private let trace = Logger(subsystem: "com.pryvalov.purrfectlydangerous", category: "jump")
    private var tracedHeld: Bool?
    private var jumpBaseY = 0.0
    private var jumpApex = 0.0
    private var tracingJump = false
    /// The hero's height before the current step, so a jump is measured from where it left.
    private var preStepY = 0.0
    /// How long the button stayed held from the jump's press, and whether it still is.
    private var jumpHeldFor = 0.0
    private var holdingJump = false
    #endif

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
            #if DEBUG
            if input.jumpHeld != tracedHeld || input.jumpPressed {
                tracedHeld = input.jumpHeld
                trace.notice("step held=\(input.jumpHeld, privacy: .public) pressed=\(input.jumpPressed, privacy: .public) worldTime=\(self.world.time, format: .fixed(precision: 3), privacy: .public) y=\(self.world.heroY, format: .fixed(precision: 1), privacy: .public) vy=\(self.world.heroVY, format: .fixed(precision: 1), privacy: .public)")
            }
            #endif
            let moving = world.phase == .running || world.phase == .boss
            #if DEBUG
            preStepY = world.heroY
            #endif
            handle(world.step(input, dt: Self.step))
            #if DEBUG
            if tracingJump { jumpApex = max(jumpApex, world.heroY) }
            if holdingJump {
                if input.jumpHeld { jumpHeldFor += Self.step } else { holdingJump = false }
            }
            #endif
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
        .penguinSoldier: "spear", .snowyOwl: "icicle_shot", .snowman: "snowball_shot", .iciclePlant: "icicle_bolt",
        .ghostCat: "spirit_ball", .hauntedPortrait: "magic_shot", .candleCat: "fire_orb", .poltergeistBook: "magic_bolt",
        .lavaSlime: "lava_glob", .fireImp: "fireball_shot", .stoneGuard: "magma_blast", .flameArcher: "flame_arrow",
        .voidSlime: "void_orb", .voidBat: "void_orb", .voidSentinel: "void_laser", .voidMage: "void_bolt",
        .riftTurret: "crystal_shot", .voidWisp: "homing_orb",
        .lanternSpirit: "blossom_shot", .spikePlant: "blossom_shot",
        .lanternSlime: "lantern_flame", .shadowSpirit: "spirit_flame", .spikeKappa: "spike_ball",
        .oniCat: "oni_rock", .spiritWisp: "wisp_shot",
    ]
    /// Sprites for thrown hazard kinds whose `hazard_<kind>` sprite does not exist.
    private static let projectileSprite = ["bone": "bone", "cannonball": "cannonball", "soundwave": "hazard_wave",
                                           "spore": "spore", "sting": "sting", "leaf": "leaf",
                                           "spear": "spear", "icicle_shot": "icicle_shot",
                                           "snowball_shot": "snowball_shot", "icicle_bolt": "icicle_bolt",
                                           "spirit_ball": "spirit_ball", "magic_shot": "magic_shot",
                                           "fire_orb": "fire_orb", "magic_bolt": "magic_bolt",
                                           "lava_glob": "lava_glob", "fireball_shot": "fireball_shot",
                                           "magma_blast": "magma_blast", "flame_arrow": "flame_arrow",
                                           "lava_puddle": "lava_puddle", "fire_ring": "fire_ring",
                                           "void_orb": "void_orb", "void_laser": "void_laser", "void_bolt": "void_bolt",
                                           "crystal_shot": "crystal_shot", "homing_orb": "homing_orb",
                                           "blossom_shot": "blossom_shot", "lantern_ember": "lantern_flame",
                                           "lantern_flame": "lantern_flame", "spirit_flame": "spirit_flame",
                                           "spike_ball": "spike_ball", "oni_rock": "oni_rock",
                                           "wisp_shot": "wisp_shot"]
    /// Hiding animation and the poses held afterwards (first one the sprite has), for things that
    /// curl up or hide in a shell.
    private static let curlAnimation: [ItemKind: (start: String, hold: [String])] = [
        .hedgehog: ("curl", ["rolled"]), .snailCat: ("hide", ["shell"]), .iceHedgehog: ("curl", ["roll", "attack"]),
        .rollingOnigiri: ("roll", ["roll", "attack"]),
    ]
    /// Animation for throwing or firing, first one the sprite has.
    private static let throwAnimation = ["throw", "cast", "attack", "fire"]

    /// Plays the first of `names` that the node's sprite has, so a sheet that is still being drawn
    /// (or names a pose differently) degrades to the next best pose instead of a blank sprite.
    private static func playAny(_ node: ActorNode?, _ names: [String], restart: Bool = false,
                                then completion: (() -> Void)? = nil) {
        guard let node else { return }
        let name = names.first { node.has($0) } ?? names.first ?? "idle"
        node.play(name, restart: restart, completion: completion)
    }

    private func handle(_ events: [GameEvent]) {
        for event in events {
            switch event {
            case .jumped(let double):
                #if DEBUG
                if !double {
                    tracingJump = true
                    jumpBaseY = preStepY
                    jumpApex = world.heroY
                    // The update loop adds this step and each further one the button stays held.
                    jumpHeldFor = 0
                    holdingJump = jumpHeld
                }
                trace.notice("jumped double=\(double, privacy: .public) worldTime=\(self.world.time, format: .fixed(precision: 3), privacy: .public) vy=\(self.world.heroVY, format: .fixed(precision: 1), privacy: .public) held=\(self.jumpHeld, privacy: .public)")
                #endif
                play(double ? .doubleJump : .jump)
                if double {
                    doubleJumping = true
                    hero.play("double", restart: true)
                    pawTrail()
                }
            case .landed:
                #if DEBUG
                if tracingJump {
                    tracingJump = false
                    let apex = jumpApex - jumpBaseY
                    hud.debugJumpCount += 1
                    hud.debugJumpApex = apex
                    hud.debugJumpHeld = jumpHeldFor
                    holdingJump = false
                    trace.notice("landed apex=\(apex, format: .fixed(precision: 1), privacy: .public) worldTime=\(self.world.time, format: .fixed(precision: 3), privacy: .public)")
                }
                #endif
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
                let node = entityNodes[id]
                node?.flash()
                // A brief flinch where the sprite has one, then back to what it was doing.
                // (Called `hit` on most sheets, `hurt` on the Sakura route's.)
                if let node, let flinch = ["hit", "hurt"].first(where: node.has),
                   let kind = world.entities.first(where: { $0.id == id })?.kind {
                    node.play(flinch, restart: true) { [weak node] in Self.playAny(node, Self.restAnimation(kind)) }
                }
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
                let names = kind.flatMap { Self.curlAnimation[$0] } ?? ("curl", ["rolled"])
                entityNodes[id]?.play(names.start) { [weak node = entityNodes[id]] in Self.playAny(node, names.hold) }
            case .threw(let id):
                guard let entity = world.entities.first(where: { $0.id == id }) else { break }
                tagThrownHazard(from: entity)
                let node = entityNodes[id]
                Self.playAny(node, Self.throwAnimation, restart: true) { [weak node] in
                    Self.playAny(node, Self.restAnimation(entity.kind))
                }
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
                    case .iciclePlant: play(.shatter)
                    default: play(.flame)
                    }
                }
            case .fallWarning:
                break
            case .shattered(let id):
                if let entity = world.entities.first(where: { $0.id == id }), isOnScreen(entity.x) { play(.shatter) }
            case .bumped:
                // Knocked back off a step: a squash, and dust kicked off the face back toward the kitten.
                play(.thump)
                hero.run(.sequence([.scaleX(to: 1.15, y: 0.82, duration: 0.05), .scale(to: 1, duration: 0.15)]),
                         withKey: "bump")
                let face = world.lastBumpFace.map(groundScreenX)
                    ?? framing.heroScreenX + CGFloat(world.tuning.heroWidth / 2)
                dust(at: CGPoint(x: face, y: screenY(world.heroY) + 2), awayFromWall: true)
            case .hazardBroke(let id):
                if let node = hazardNodes.removeValue(forKey: id) {
                    if node.position.x > -20, node.position.x < size.width + 20 { dust(at: node.position) }
                    node.removeFromParent()
                }
            case .droppedDown(let id):
                if let entity = world.entities.first(where: { $0.id == id }), isOnScreen(entity.x) { play(.thump) }
            case .waking(let id):
                // A statue stirring or a gargoyle shifting on its pedestal.
                if let entity = world.entities.first(where: { $0.id == id }), isOnScreen(entity.x) { play(.crumble) }
            case .teleported:
                play(.dash)
            case .leapt(let id):
                if let entity = world.entities.first(where: { $0.id == id }), isOnScreen(entity.x) { play(.pounce) }
            case .leapLanded(let id):
                if let entity = world.entities.first(where: { $0.id == id }), isOnScreen(entity.x) {
                    play(.thump)
                    dust(at: CGPoint(x: screenX(entity.x), y: screenY(entity.y) + 2))
                }
            case .chaseWarning:
                // Something is coming from behind: the hound flashes at the left edge (see `animate`).
                play(.dash)
            case .fuseLit:
                break
            case .lunged(let id):
                // The sakura bunny, ninja tanuki or samurai ronin lunges with its crescent slash.
                play(.dash)
                Self.playAny(entityNodes[id], ["attack", "run"], restart: true)
            case .summoned(let id):
                // The void mage raises a wisp ahead of the kitten.
                let node = entityNodes[id]
                let kind = world.entities.first { $0.id == id }?.kind
                Self.playAny(node, ["summon", "attack"], restart: true) { [weak node] in
                    Self.playAny(node, kind.map(Self.restAnimation) ?? ["idle"])
                }
            case .portalOpened:
                play(.dash)
            case .yarnPorted:
                play(.block)
            case .bossExposed:
                // The final phase opened to an ability: the boss can be hit for a moment.
                play(.impact)
                trueBossNode?.flash(.white, duration: 0.25)
            case .exploded(let id):
                play(.flame)
                if let node = entityNodes.removeValue(forKey: id) {
                    burst("spark_ember", count: 8, radius: 22, at: CGPoint(x: node.position.x, y: node.position.y + 6))
                    if node.has("attack") {
                        node.play("attack", restart: true) { [weak node] in node?.removeFromParent() }
                    } else {
                        node.run(.sequence([.fadeOut(withDuration: 0.15), .removeFromParent()]))
                    }
                }
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
                if !BossHealth.introducesItself(id) { showBanner(text("\(id).name").uppercased()) }
            case .bossTelegraph, .bossAttack:
                break
            case .bossHit:
                hud.bossHits += 1
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
        // The pit's opening: from the ground line down to the water of a waterfall pit, or to the
        // bottom of the screen for a plain one.
        let bottom = pitWaterY ?? 0
        let pit = SKSpriteNode(color: .white, size: CGSize(width: CGFloat(ravine.width), height: groundY - bottom))
        pit.anchorPoint = .zero
        pit.position = CGPoint(x: groundScreenX(ravine.at), y: bottom)
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

    /// Paw prints flashing at the hero's feet as it pushes off the air for a Double Pounce, left
    /// behind as the world scrolls on.
    private func pawTrail() {
        guard let animation = library.animation("paw_trail", "burst") else { return }
        let node = ActorNode(sprite: "paw_trail", library: library)
        node.position = CGPoint(x: framing.heroScreenX.rounded(), y: screenY(world.heroY).rounded())
        node.zPosition = 6
        actors.addChild(node)
        let duration = Double(animation.frames) / max(animation.fps, 1)
        node.run(.moveBy(x: -CGFloat(world.runSpeed * duration), y: 0, duration: duration))
        node.play("burst") { [weak node] in node?.removeFromParent() }
    }

    /// A few earth-coloured pixels kicked up and fading.
    /// With `awayFromWall` every grain flies left, off a face the kitten ran into on its right.
    private func dust(at origin: CGPoint, awayFromWall: Bool = false) {
        for (index, (spread, dy)) in [(-6.0, 5.0), (-3.0, 8.0), (2.0, 7.0), (-8.0, 2.0), (4.0, 3.0)].enumerated() {
            let dx = awayFromWall ? -abs(spread) - 2 : spread
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

    /// Whole-pixel x for scenery fixed to the ground (pits, terrain, slick zones, the dip mask). It
    /// moves by `floor(scroll)` exactly as the ground strip does, so a pit edge never shifts a pixel
    /// against the ground's texture from one frame to the next.
    private func groundScreenX(_ worldX: Double) -> CGFloat {
        CGFloat(worldX - scroll.rounded(.down)).rounded() + framing.heroScreenX.rounded()
    }

    private func screenY(_ worldY: Double) -> CGFloat {
        CGFloat(worldY) + groundY
    }

    private func render() {
        for layer in parallax { layer.scroll(to: CGFloat(scroll)) }
        for (at, width, node) in groundNodes {
            node.position.x = groundScreenX(at)
            node.isHidden = node.position.x > size.width || node.position.x + CGFloat(width) < 0
        }
        updateGroundMask()
        // One frame index for every animated scenery piece, at one rate, so they never drift apart.
        let tick = Int(world.time * clockRate)
        for tile in clockAnimated where !tile.owner.isHidden {
            let index = tick % tile.frames.count
            if tile.node.texture !== tile.frames[index] { tile.node.texture = tile.frames[index] }
        }
        renderPlatforms()
        renderHero()
        renderEntities()
        renderHazards()
        renderPortals()
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

    /// Creatures drawn from the world sheets (worlds 2 and 3): what they show while going about
    /// their business, first one the sprite has. Dormant and teleporting ones are posed in `animate`.
    private static let sheetRest: [ItemKind: [String]] = [
        .iceSlime: ["move", "walk", "idle"], .snowCat: ["run", "walk", "idle"], .iceBat: ["fly", "idle"],
        .iceGolem: ["walk", "idle"], .penguinSoldier: ["walk", "idle"], .snowyOwl: ["fly", "idle"],
        .iceHedgehog: ["walk", "move", "idle"], .snowman: ["idle", "walk"], .iciclePlant: ["closed", "idle"],
        .miniYeti: ["walk", "idle"],
        .ghostCat: ["float", "move", "idle"], .hauntedPortrait: ["move", "fly", "idle"],
        .cursedArmor: ["walk", "move", "idle"], .candleCat: ["move", "walk", "idle"],
        .poltergeistBook: ["move", "fly", "idle"], .gargoyleCat: ["walk", "move", "idle"],
        .shadowCat: ["attack", "move", "walk", "idle"],
        .lavaSlime: ["move", "walk", "idle"], .fireImp: ["fly", "idle"], .stoneGuard: ["walk", "idle"],
        .hellHound: ["run", "walk", "idle"], .emberBat: ["fly", "idle"], .flameArcher: ["idle", "walk"],
        .chainsawCat: ["walk", "idle"], .fireWisp: ["move", "idle"],
        .voidSlime: ["move", "idle"], .voidBat: ["fly", "idle"], .voidSentinel: ["idle", "move"],
        .riftHound: ["run", "idle"], .voidMage: ["idle", "walk"], .riftTurret: ["idle"],
        .voidWisp: ["move", "idle"], .miniVoidCat: ["attack", "move", "idle"],
        .sakuraSlime: ["walk", "idle"], .sakuraBunny: ["run", "walk", "idle"], .lanternSpirit: ["float", "idle"],
        .birdCrow: ["fly", "idle"], .spikePlant: ["idle"], .rollingOnigiri: ["idle"],
        .bambooSpikes: ["idle", "still"], .sakuraSpirit: ["float", "fly", "idle"],
        .lanternSlime: ["walk", "idle"], .ninjaTanuki: ["walk", "idle"], .sakuraBat: ["fly", "idle"],
        .shadowSpirit: ["float", "idle"], .spikeKappa: ["closed", "idle"], .lanternPendulum: ["swing", "idle", "still"],
        .fallingLantern: ["hang", "idle", "still"],
        .shadowSlime: ["walk", "idle"], .samuraiRonin: ["walk", "idle"], .oniCat: ["walk", "idle"],
        .tenguCrow: ["fly", "idle"], .spiritWisp: ["float", "idle"],
    ]

    /// The resting animation of a kind, best first.
    private static func restAnimation(_ kind: ItemKind) -> [String] {
        sheetRest[kind] ?? [defaultAnimation[kind] ?? "idle", "idle", "still"]
    }

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
        case .fallingLantern:
            switch entity.state {
            case .warning:
                // A warning shake: it flashes before it drops.
                Self.playAny(node, ["hang", "idle", "still"])
                node.color = .white
                node.colorBlendFactor = blink ? 0.7 : 0
            case .active: Self.playAny(node, ["fall", "hang", "idle", "still"])
            case .landed: Self.playAny(node, ["burn", "shatter", "idle", "still"])
            default: Self.playAny(node, ["hang", "idle", "still"])
            }
        case .spikeKappa:
            // Closed shell, opening lotus, then throwing.
            switch entity.state {
            case .warning: Self.playAny(node, ["open", "idle"])
            case .active: if !node.isBusy { Self.playAny(node, ["attack", "open"]) }
            default: Self.playAny(node, ["closed", "idle"])
            }
        case .ninjaTanuki, .samuraiRonin:
            // Winding up (the ronin's stance), then the slash.
            if entity.state == .warning, !node.isBusy {
                Self.playAny(node, ["idle", "walk"])
            } else if entity.state == .active, !node.isBusy {
                Self.playAny(node, ["attack", "walk"])
            }
        case .lanternPendulum:
            // The rope, from the pivot above where it hangs down to the lantern.
            if let swing = entity.kind.spec.pendulum {
                let pivot = CGPoint(x: screenX(entity.home), y: screenY(world.groundHeight(at: entity.home) + swing.pivot))
                let rope = (node.childNode(withName: "rope") as? SKShapeNode) ?? {
                    let rope = SKShapeNode()
                    rope.name = "rope"
                    rope.strokeColor = SKColor(red: 0.35, green: 0.2, blue: 0.15, alpha: 1)
                    rope.lineWidth = 1
                    rope.zPosition = -1
                    node.addChild(rope)
                    return rope
                }()
                let path = CGMutablePath()
                path.move(to: CGPoint(x: 0, y: node.size.height))
                path.addLine(to: CGPoint(x: pivot.x - node.position.x, y: pivot.y - node.position.y))
                rope.path = path
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
                if node.current != "fade", node.has("fade") { node.play("fade") }
                if !node.isBusy { node.alpha = 0.12 }
            case .warning:
                if node.current == "fade", !node.isBusy { node.play("float") }
                node.alpha = blink ? 0.6 : 0.25
            default:
                // Visible: floats, unless it is mid-throw (spirit ball).
                if !node.isBusy || node.current == "fade" { Self.playAny(node, Self.restAnimation(.ghostCat)) }
            }
        case .cursedArmor, .gargoyleCat:
            let statue = entity.kind == .cursedArmor ? ["statue", "idle"] : ["idle"]
            switch entity.state {
            case .idle:
                Self.playAny(node, statue)
            case .warning:
                // Stirring: the gargoyle crouches to spring; both flash so the player sees it coming.
                Self.playAny(node, entity.kind == .gargoyleCat ? ["prepare", "idle"] : statue)
                node.color = .white
                node.colorBlendFactor = blink ? 0.6 : 0
            case .leaping:
                Self.playAny(node, ["leap", "attack", "idle"])
            default:
                if !node.isBusy { Self.playAny(node, Self.restAnimation(entity.kind)) }
            }
        case .shadowCat, .miniVoidCat:
            switch entity.state {
            case .hidden:
                node.alpha = 0
            case .warning:
                Self.playAny(node, ["teleport", "idle"])
                node.alpha = blink ? 1 : 0.4
            default:
                if !node.isBusy { Self.playAny(node, Self.restAnimation(entity.kind)) }
            }
        case .voidSlime:
            // Lurches in bursts: moving, then still.
            let moving = entity.kind.spec.burst?.isMoving(at: world.time + entity.cycleOffset) ?? true
            if !node.isBusy { Self.playAny(node, moving ? ["move", "idle"] : ["idle"]) }
        case .voidSentinel, .riftTurret:
            if entity.state == .warning {
                // Charging: the visible wind-up before the shot.
                Self.playAny(node, ["charge", "attack", "idle"])
                node.color = .white
                node.colorBlendFactor = blink ? 0.5 : 0
            } else if !node.isBusy {
                Self.playAny(node, Self.restAnimation(entity.kind))
            }
        case .hedgehog, .snailCat, .iceHedgehog, .rollingOnigiri:
            // Normally started by the `curled` event; this catches a node made after it fired.
            let names = Self.curlAnimation[entity.kind] ?? ("curl", ["rolled"])
            if entity.state == .curled, node.current != names.start, !names.hold.contains(node.current) {
                node.play(names.start) { [weak node] in Self.playAny(node, names.hold) }
            }
        case .spikePlant:
            switch entity.state {
            case .warning: Self.playAny(node, ["open", "idle"])
            case .active: Self.playAny(node, ["attack", "open"])
            default: Self.playAny(node, ["idle", "closed"])
            }
        case .bambooSpikes:
            // Low spikes on a rhythm: down, blinking just before, then up.
            switch entity.state {
            case .warning:
                Self.playAny(node, ["warn", "idle", "still"])
                node.color = .white
                node.colorBlendFactor = blink ? 0.5 : 0
            case .active: Self.playAny(node, ["rise", "attack", "idle", "still"])
            default: Self.playAny(node, ["idle", "still"])
            }
        case .sakuraBunny:
            if entity.state == .warning, !node.isBusy {
                Self.playAny(node, ["walk", "idle"])
            } else if entity.state == .active, !node.isBusy {
                Self.playAny(node, ["attack", "run"])
            }
        case .sakuraSlime, .shadowSlime:
            // Shuffles in bursts; a little bounce lunge (the shadow slime's leap) once close (drawn only).
            let moving = entity.kind.spec.burst?.isMoving(at: world.time + entity.cycleOffset) ?? true
            if abs(entity.x - world.distance) < 40, node.has("attack") {
                node.play("attack")
            } else if !node.isBusy {
                Self.playAny(node, moving ? ["walk", "idle"] : ["idle"])
            }
        case .birdCrow, .tenguCrow:
            // Its dive, once it drops toward the ground.
            if entity.y - world.groundHeight(at: entity.x) < 36, !node.isBusy {
                Self.playAny(node, ["attack", "fly"])
            } else if !node.isBusy {
                Self.playAny(node, Self.restAnimation(entity.kind))
            }
        case .iciclePlant:
            switch entity.state {
            case .warning: Self.playAny(node, ["open", "idle"])
            case .active: Self.playAny(node, ["attack", "open"])
            default: Self.playAny(node, ["closed", "idle"])
            }
        case .penguinSoldier, .snowyOwl:
            // Winding up a thrust or a drop: the sheet's prepare pose, and the owl blinks.
            if entity.state == .warning, !node.isBusy {
                Self.playAny(node, ["prepare", "attack"] + Self.restAnimation(entity.kind))
                if entity.kind == .snowyOwl {
                    node.color = .white
                    node.colorBlendFactor = blink ? 0.7 : 0
                }
            } else if !node.isBusy {
                Self.playAny(node, Self.restAnimation(entity.kind))
            }
        case .hellHound where entity.state != .active, .riftHound where entity.state != .active:
            if entity.state == .warning {
                // Coming from behind: flash it at the left edge of the screen, at the kitten's height.
                node.position = CGPoint(x: node.size.width / 2 + 4, y: screenY(world.groundHeight(at: world.distance)))
                node.alpha = blink ? 0.9 : 0.2
                Self.playAny(node, Self.restAnimation(entity.kind))
            } else {
                node.alpha = 0
            }
        case .fireWisp where entity.state == .warning:
            // The fuse is lit: it flashes.
            node.color = .white
            node.colorBlendFactor = blink ? 0.7 : 0
        case .emberBat:
            // A cosmetic fiery trail.
            if Int(world.time * 60) % 8 == 0 {
                burst("spark_ember", count: 1, radius: 6, at: CGPoint(x: node.position.x + 6, y: node.position.y + 6))
            }
        case .snowCat, .iceGolem, .miniYeti, .chainsawCat, .hellHound, .riftHound, .oniCat:
            // Melee: swing once in reach (looks only; the hitbox decides the hit).
            let reach = entity.kind.spec.width / 2 + world.tuning.heroWidth / 2 + 14
            if abs(entity.x - world.distance) < reach, node.has("attack") {
                node.play("attack")
            } else if !node.isBusy {
                Self.playAny(node, Self.restAnimation(entity.kind))
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
        Self.playAny(node, Self.sheetRest[entity.kind] ?? [Self.defaultAnimation[entity.kind] ?? "still"])
        actors.addChild(node)
        entityNodes[entity.id] = node
        return node
    }

    /// Ledges follow `platformState`: whole while solid, crumble frames paced over the crumble time,
    /// and gone once they give way. A blinking ledge flickers through its fading frames before it vanishes.
    private func renderPlatforms() {
        for view in platformViews {
            let platform = world.platforms[view.index]
            // Where it is now: a moving ledge swings on the world clock.
            view.node.position = CGPoint(x: screenX(world.platformLeft(view.index)).rounded(),
                                         y: screenY(world.platformTop(view.index)) - view.height)
            let state = world.platformState(view.index)
            var texture: SKTexture?
            switch (platform.mode, state) {
            case (_, .solid):
                texture = (platformFrames(view, "still").first ?? platformFrames(view, "solid").first)
            case (.blinks, .crumbling):
                let frames = platformFrames(view, "fading")
                texture = frames.isEmpty ? nil : frames[Int(world.time * 8) % frames.count]
            case (_, .crumbling):
                let frames = platformFrames(view, "crumble")
                let elapsed = world.time - (crumbleStart[view.index] ?? world.time)
                let span = platform.crumbleAfter ?? Platform.defaultCrumbleAfter
                // All but the last frame while it still holds; the last one as it drops away.
                let index = Int(elapsed / span * Double(max(frames.count - 1, 1)))
                texture = frames.isEmpty ? nil : frames[min(index, max(frames.count - 2, 0))]
            case (.crumbles, .gone):
                let frames = platformFrames(view, "crumble")
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

    /// A ledge's frames for `animation`, from its themed sprite, or from the plain one if the themed
    /// sprite does not have that animation (its crumble frames, say) yet.
    private func platformFrames(_ view: PlatformView, _ animation: String) -> [SKTexture] {
        let frames = library.textures(view.sprite, animation)
        guard frames.isEmpty else { return frames }
        return library.textures(world.platforms[view.index].kind ?? "bridge", animation)
    }

    /// A node for `hazard`: the sprite of what threw it, or of its own kind; lingering ones (a lava
    /// puddle, a ring of fire) burn, the rest fly.
    private func makeHazardNode(_ hazard: Hazard) -> ActorNode {
        let lingering = hazard.life != nil ? Self.projectileSprite[hazard.kind] : nil
        let sprite = lingering ?? thrownSprite[hazard.id] ?? Self.projectileSprite[hazard.kind] ?? "hazard_\(hazard.kind)"
        let node = ActorNode(sprite: sprite, library: library)
        node.zPosition = 4
        Self.playAny(node, lingering != nil ? ["burn", "fly", "idle", "still"] : ["fly", "idle", "still"])
        actors.addChild(node)
        hazardNodes[hazard.id] = node
        return node
    }

    /// Portal pairs (sprite `portal`): `open` while yarn is bent through them, `close` as they shut.
    private func renderPortals() {
        var seen = Set<Int>()
        for portal in world.portals {
            seen.insert(portal.id)
            let pair = portalNodes[portal.id] ?? {
                let make = { () -> ActorNode in
                    let node = ActorNode(sprite: "portal", library: self.library)
                    node.zPosition = 5
                    self.actors.addChild(node)
                    return node
                }
                let pair = (entry: make(), exit: make())
                portalNodes[portal.id] = pair
                return pair
            }()
            pair.entry.position = CGPoint(x: screenX(portal.x), y: screenY(portal.spec.y))
            pair.exit.position = CGPoint(x: screenX(portal.exitX), y: screenY(portal.spec.exitY))
            for node in [pair.entry, pair.exit] {
                Self.playAny(node, portal.isOpen ? ["open", "idle", "still"] : ["close", "idle", "still"])
                node.alpha = portal.isOpen ? 1 : 0.4
            }
        }
        for (id, pair) in portalNodes where !seen.contains(id) {
            pair.entry.removeFromParent()
            pair.exit.removeFromParent()
            portalNodes[id] = nil
        }
    }

    private func renderHazards() {
        var seen = Set<Int>()
        for hazard in world.hazards {
            seen.insert(hazard.id)
            var node: ActorNode
            if let existing = hazardNodes[hazard.id] {
                node = existing
            } else {
                node = makeHazardNode(hazard)
            }
            if hazard.life != nil, let sprite = Self.projectileSprite[hazard.kind], node.spriteName != sprite {
                // A lava glob that landed became a puddle: draw the puddle instead.
                node.removeFromParent()
                node = makeHazardNode(hazard)
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
        "boss_kitsune": ["claw_slash": "claw", "double_claw": "claw", "bloom_shots": "bloom", "bloom_volley": "bloom", "spirit_summon": "summon", "*": "attack"],
        "boss_toad": ["tongue_strike": "tongue", "lantern_arc": "lanterns", "area_slam": "slam", "*": "attack"],
        "boss_guardian_cat": ["petal_volley": "volley", "petal_storm": "spin", "paw_slam": "slam", "torii_beam": "beam",
                              "spirit_summon": "summon", "*": "volley"],
        "boss_voidcat": ["shadow_paws": "paws", "star_fall": "stars", "portal_paws": "portal",
                         "portal_shards": "portal", "phase_rush": "phase", "phase_storm": "phase", "*": "attack"],
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
        show(\.fireReady, world.canThrow)
        show(\.canDash, stats.has(.ghostDash))
        show(\.canPounce, stats.has(.superPounce))
        show(\.dashReady, world.canDash)
        show(\.canDoubleJump, stats.has(.doublePounce))
        let jump: GameHUD.JumpButton
        if world.onGround {
            jump = .ready
        } else if world.canDoubleJump {
            jump = .double
        } else {
            jump = .spent
        }
        show(\.jumpButton, jump)
        // Quantised so the ring does not redraw the SwiftUI overlay on every frame of a hold.
        let charge = stats.has(.superPounce) ? min(1, world.pawCharge / world.tuning.chargeTime) : 0
        show(\.pounceCharge, (charge * 20).rounded() / 20)
        if let boss = world.bossState, world.phase == .boss {
            show(\.bossName, text("\(boss.id).name"))
            show(\.bossID, boss.id)
            show(\.bossFraction, boss.hpFraction)
        } else {
            show(\.bossName, nil)
            show(\.bossID, nil)
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
