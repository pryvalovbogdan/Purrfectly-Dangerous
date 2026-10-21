import Foundation
import GameCore
import Observation

/// What the SwiftUI overlay shows; the scene writes it once per frame.
@MainActor
@Observable
final class GameHUD {
    var hearts = 3
    var maxHearts = 3
    var heroLevel = 1
    /// Fish picked up this level.
    var fish = 0
    /// Progress toward the next hero level, 0...1 (1 at max level).
    var xpFraction = 0.0
    var canFire = false
    /// The next yarn throw is ready (Yarn Shot won and its cooldown over).
    var fireReady = false
    /// The paw button shows once Ghost Dash is unlocked.
    var canDash = false
    /// False while the dash is cooling down.
    var dashReady = true
    var canPounce = false
    var canDoubleJump = false
    /// What the jump button offers right now.
    enum JumpButton: Equatable {
        /// On the ground: a jump.
        case ready
        /// In the air with a Double Pounce still to use.
        case double
        /// In the air with no jump left.
        case spent
    }
    var jumpButton = JumpButton.ready
    /// How far the paw is charged toward a Super Pounce, 0...1.
    var pounceCharge = 0.0
    var bossName: String?
    /// The boss's neutral id (`boss_squirrel`, …), for its own banner art; nil outside the fight.
    var bossID: String?
    /// Counts the hits on the boss, so the bar can flash on each.
    var bossHits = 0
    var bossFraction = 1.0
    var banner: String?
    /// An ability just won, shown as an award card for a moment.
    var award: Ability?
    var isPaused = false
    /// Debug builds only (the jump trace): how many jumps have landed, and the last one's apex above
    /// where it started, in world units. Read by the jump-height UI test.
    var debugJumpCount = 0
    var debugJumpApex = 0.0
}
