import Foundation
import Testing
@testable import GameCore

/// A human-fairness lint on top of the no-hit bot: the bot reacts in one frame and shoots turrets,
/// a player needs a run-up. After every landing spot (the top of a rise, the foot of a step down,
/// the near end of a platform, the far rim of a ravine) the next standing obstacle or step a tap does
/// not clear must leave room to land and jump again.
@Suite struct FairnessLintTests {
    /// What a tap clears: anything at least this tall needs a held jump.
    static let tapClears = 24.0
    /// Room a player needs between touching down and the near side of such an obstacle.
    static let runway = 90.0

    struct Crowded: CustomStringConvertible {
        let kind: String, at: Double, landing: Double, why: String
        var description: String { "\(kind) at \(Int(at)) is \(Int(at - landing)) after the \(why) at \(Int(landing))" }
    }

    static func crowded(_ level: LevelDefinition) -> [Crowded] {
        var landings: [(x: Double, why: String)] = []
        let ground = GroundProfile(level.terrain ?? [])
        for (edge, _) in ground.rises(step: 4) { landings.append((edge, "top of the rise")) }
        for edge in ground.edges where ground.height(at: edge) < ground.height(leftOf: edge) - 4 {
            landings.append((edge, "foot of the step down"))
        }
        // A platform is landed on near its left end. A step right after it is the next hop of a
        // stepping stone, which is fine; a tall obstacle is not.
        for platform in level.platforms ?? [] { landings.append((platform.at, "start of the platform")) }
        for ravine in level.ravines ?? [] { landings.append((ravine.end, "far rim of the ravine")) }
        var found: [Crowded] = []
        for item in level.items where !item.kind.isPickup && item.y == nil {
            let spec = item.kind.spec
            // Things that stand still (or pace around a post) where they are placed; walkers and
            // flyers meet the hero somewhere else, and the bot run covers them.
            guard spec.baseY == 0, spec.height >= tapClears, spec.velocity == 0 || spec.patrol != nil,
                  spec.flight == nil, spec.fall == nil else { continue }
            let near = item.at - spec.width / 2 - (spec.patrol ?? 0)
            for landing in landings where near > landing.x && near - landing.x < runway {
                found.append(Crowded(kind: item.kind.rawValue, at: item.at, landing: landing.x, why: landing.why))
            }
        }
        // A step up too high for a tap is an obstacle too (a lip of 4 is walked onto).
        for (edge, rise) in ground.rises(step: 4) where rise - 4 >= tapClears {
            for landing in landings where !landing.why.hasSuffix("platform") && edge > landing.x && edge - landing.x < runway {
                found.append(Crowded(kind: "step up \(Int(rise))", at: edge, landing: landing.x, why: landing.why))
            }
        }
        return found
    }

    @Test(arguments: Content.levelIDs)
    func tallObstaclesLeaveARunUpAfterEveryLanding(id: String) throws {
        let problems = Self.crowded(try Content.level(id))
        #expect(problems.isEmpty, "\(id): \(problems.map(\.description).joined(separator: "; "))")
    }
}
