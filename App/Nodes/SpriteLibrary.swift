import SpriteKit

/// Reads Sprites.json (written by Tools/sprites/build.py) and hands out the matching textures.
final class SpriteLibrary {
    struct Animation: Decodable {
        let frames: Int
        let fps: Double
        let loop: Bool
    }

    struct Sheet: Decodable {
        let width: CGFloat
        let height: CGFloat
        let anchorX: CGFloat
        let anchorY: CGFloat
        let animations: [String: Animation]
    }

    enum LibraryError: Error {
        case missingManifest
    }

    private let sheets: [String: Sheet]
    private var cache: [String: [SKTexture]] = [:]
    private var imageCache: [String: [CGImage]] = [:]

    init(bundle: Bundle) throws {
        guard let url = bundle.url(forResource: "Sprites", withExtension: "json") else {
            throw LibraryError.missingManifest
        }
        sheets = try JSONDecoder().decode([String: Sheet].self, from: Data(contentsOf: url))
    }

    func sheet(_ sprite: String) -> Sheet? {
        sheets[sprite]
    }

    func animation(_ sprite: String, _ name: String) -> Animation? {
        sheets[sprite]?.animations[name]
    }

    /// `preferred` if the sprite has that animation, else its first animation by name; nil if the
    /// sprite is not in the manifest. Lets screens use art that is still being drawn (or whose
    /// animation names differ) without crashing: a missing sprite is simply left out.
    func animationName(_ sprite: String, preferring preferred: String) -> String? {
        guard let animations = sheets[sprite]?.animations else { return nil }
        if animations[preferred] != nil { return preferred }
        return animations.keys.sorted().first
    }

    /// The frames of an animation as images for SwiftUI, cached. Each frame is a whole sprite image
    /// from the asset catalog; nothing is cut out of a texture.
    func images(_ sprite: String, _ name: String) -> [CGImage] {
        let key = "\(sprite)/\(name)"
        if let cached = imageCache[key] { return cached }
        let images = textures(sprite, name).map { $0.cgImage() }
        imageCache[key] = images
        return images
    }

    func textures(_ sprite: String, _ name: String) -> [SKTexture] {
        let key = "\(sprite)/\(name)"
        if let cached = cache[key] { return cached }
        guard let animation = animation(sprite, name) else { return [] }
        let textures = (0..<animation.frames).map { index -> SKTexture in
            let texture = SKTexture(imageNamed: "\(sprite)_\(name)_\(index)")
            texture.filteringMode = .nearest
            return texture
        }
        cache[key] = textures
        return textures
    }
}
