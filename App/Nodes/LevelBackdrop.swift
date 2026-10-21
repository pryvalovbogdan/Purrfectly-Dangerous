import SpriteKit

/// The layered scenery of a level theme: sky, clouds, hills and the ground strip. Shared by the game
/// and the screen that announces the next level, so both show the same place.
enum LevelBackdrop {
    /// Adds the layers for `theme` to `parent` and returns the strips that scroll, back to front.
    /// With `groundLayers` the base ground goes into them instead: the fill into `fill`, the strip
    /// and its earth into `strip`, at z 0 inside each; the caller places them at z -5 and -4 (the
    /// game masks sunken dips out of both, and draws raised blocks between them).
    static func build(theme: String, size: CGSize, groundY: CGFloat, library: SpriteLibrary,
                      into parent: SKNode, groundLayers: (fill: SKNode, strip: SKNode)? = nil) -> [ParallaxNode] {
        var parallax: [ParallaxNode] = []
        if let sky = library.textures("bg_\(theme)_sky", "still").first {
            // The banded sky keeps its drawn height and sits on the ground line, so the horizon looks the
            // same in both orientations; anything above it is filled with the sky's top colour.
            let bandHeight: CGFloat = 200
            let node = SKSpriteNode(texture: sky, size: CGSize(width: size.width, height: bandHeight))
            node.anchorPoint = .zero
            node.position.y = groundY
            node.zPosition = -10
            parent.addChild(node)
            // Below the ground line only the ground itself used to be drawn, so where the game hides it
            // above the floor of a dip the scene's dark background showed through. The band mirrored
            // about the ground line carries the horizon colours on down; the ground covers it elsewhere.
            let mirrored = SKSpriteNode(texture: sky, size: CGSize(width: size.width, height: bandHeight))
            mirrored.anchorPoint = .zero
            mirrored.yScale = -1
            mirrored.position.y = groundY
            mirrored.zPosition = -10
            parent.addChild(mirrored)
            let above = size.height - groundY - bandHeight
            if above > 0, let topColour = library.textures("bg_\(theme)_sky_top", "still").first {
                let fill = SKSpriteNode(texture: topColour, size: CGSize(width: size.width, height: above + 1))
                fill.anchorPoint = .zero
                fill.position.y = groundY + bandHeight - 1
                fill.zPosition = -10
                parent.addChild(fill)
            }
        }
        if let fill = library.textures("ground_\(theme)_fill", "still").first {
            let node = SKSpriteNode(texture: fill, size: CGSize(width: size.width, height: groundY))
            node.anchorPoint = .zero
            node.zPosition = groundLayers == nil ? -5 : 0
            (groundLayers?.fill ?? parent).addChild(node)
        }
        parallax += standingLayers(theme: theme, size: size, standingOn: groundY, library: library, into: parent)
        let name = "ground_\(theme)"
        if let texture = library.textures(name, "still").first, let sheet = library.sheet(name) {
            let node = ParallaxNode(texture: texture, size: CGSize(width: sheet.width, height: sheet.height),
                                    viewWidth: size.width, factor: 1)
            node.position.y = groundY - sheet.height
            node.zPosition = groundLayers == nil ? -4 : 0
            (groundLayers?.strip ?? parent).addChild(node)
            parallax.append(node)
            // Upright the earth runs deeper than the tile; keep it textured and scrolling as one piece.
            if let earth = library.textures("\(name)_earth", "still").first, let earthSheet = library.sheet("\(name)_earth") {
                for row in ParallaxNode.earth(below: node.position.y, tile: earth,
                                              tileSize: CGSize(width: earthSheet.width, height: earthSheet.height),
                                              viewWidth: size.width) {
                    row.zPosition = groundLayers == nil ? -4 : 0
                    (groundLayers?.strip ?? parent).addChild(row)
                    parallax.append(row)
                }
            }
        }
        return parallax
    }

    /// The scrolling scenery layers, back to front: name, parallax factor, z, and height above the
    /// line they stand on. The loose clouds float above the tree line, so they mostly show upright,
    /// where there is open sky; everything else stands on the line.
    static let layers: [(name: String, factor: CGFloat, z: CGFloat, lift: CGFloat)] = [
        ("puffs", 0.03, -9.5, 150), ("clouds", 0.06, -9.0, 0), ("far", 0.15, -8.0, 0),
        ("near", 0.4, -6.0, 0), ("bushes", 0.7, -5.5, 0),
    ]

    /// Adds the parallax layers for `theme` standing on `line` to `parent` and returns them. With
    /// `withSky` the sky band goes behind them, standing on the same line (the game uses this for the
    /// scenery seen down in a dip, seated on the dip's floor).
    @discardableResult
    static func standingLayers(theme: String, size: CGSize, standingOn line: CGFloat, library: SpriteLibrary,
                               into parent: SKNode, withSky: Bool = false) -> [ParallaxNode] {
        if withSky, let sky = library.textures("bg_\(theme)_sky", "still").first {
            let node = SKSpriteNode(texture: sky, size: CGSize(width: size.width, height: 200))
            node.anchorPoint = .zero
            node.position.y = line
            node.zPosition = -10
            parent.addChild(node)
        }
        var parallax: [ParallaxNode] = []
        for layer in layers {
            let name = "bg_\(theme)_\(layer.name)"
            guard let texture = library.textures(name, "still").first, let sheet = library.sheet(name) else { continue }
            let node = ParallaxNode(texture: texture, size: CGSize(width: sheet.width, height: sheet.height),
                                    viewWidth: size.width, factor: layer.factor)
            node.position.y = line + layer.lift
            node.zPosition = layer.z
            parent.addChild(node)
            parallax.append(node)
        }
        return parallax
    }
}
