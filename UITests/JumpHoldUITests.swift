import XCTest

/// Real touches on the jump button, in the debug build's flat test level (`-uitest-jump`): holding
/// the button must give a higher jump than a tap. The game's own tests prove this for RunnerWorld;
/// this covers the path from the touch to the world (HoldButton, GameScene's input).
///
/// Run: `xcodebuild test -project PurrfectlyDangerous.xcodeproj -scheme PurrfectlyDangerous
///   -destination 'platform=iOS Simulator,name=iPhone 17' -only-testing:PurrfectlyDangerousUITests`
final class JumpHoldUITests: XCTestCase {
    override func setUp() {
        continueAfterFailure = false
    }

    func testHoldingJumpGoesHigherThanATap() throws {
        try checkHoldBeatsTap(orientation: .portrait, touchAt: CGVector(dx: 0.5, dy: 0.5))
    }

    /// On its side the jump button reaches towards the bottom-right corner; a thumb lands on its lower
    /// half, near the screen edges, where iOS holds touches back for its own edge swipes unless the
    /// game defers them.
    func testHoldingJumpNearTheScreenEdgeGoesHigherThanATap() throws {
        try checkHoldBeatsTap(orientation: .landscapeLeft, touchAt: CGVector(dx: 0.7, dy: 0.92))
    }

    private func checkHoldBeatsTap(orientation: UIDeviceOrientation, touchAt offset: CGVector) throws {
        XCUIDevice.shared.orientation = orientation
        let app = XCUIApplication()
        app.launchArguments = ["-uitest-jump", "-silent"]
        app.launch()
        defer { XCUIDevice.shared.orientation = .portrait }

        let jump = app.buttons["jumpButton"]
        XCTAssertTrue(jump.waitForExistence(timeout: 20), "no jump button")
        let readout = app.staticTexts["jumpApex"]
        XCTAssertTrue(readout.waitForExistence(timeout: 5), "no apex readout (is this a debug build?)")
        // Let the run settle on the ground first.
        Thread.sleep(forTimeInterval: 1)

        let point = jump.coordinate(withNormalizedOffset: offset)
        let tapped = measure(readout) { point.tap() }
        Thread.sleep(forTimeInterval: 0.5)
        let held = measure(readout) { point.press(forDuration: 0.5) }

        let summary = "\(orientation == .portrait ? "portrait" : "landscape") touch at \(offset): tap apex \(tapped), hold apex \(held)"
        print("JUMP-UITEST \(summary)")
        add(XCTAttachment(string: summary))
        // A tap is cut early (about 32 units); held, the jump runs its full rise (about 48).
        XCTAssertGreaterThan(held, tapped + 12, summary)
    }

    /// Does `action`, waits for the jump to land, and returns its apex from the readout.
    private func measure(_ readout: XCUIElement, action: () -> Void) -> Double {
        let before = Self.parse(readout.label).count
        action()
        let deadline = Date().addingTimeInterval(5)
        while Date() < deadline {
            let now = Self.parse(readout.label)
            if now.count > before { return now.apex }
            Thread.sleep(forTimeInterval: 0.1)
        }
        XCTFail("the jump never landed (readout \(readout.label))")
        return 0
    }

    /// The readout is "<jumps landed> <last apex>".
    private static func parse(_ label: String) -> (count: Int, apex: Double) {
        let parts = label.split(separator: " ")
        guard parts.count == 2, let count = Int(parts[0]), let apex = Double(parts[1]) else { return (0, 0) }
        return (count, apex)
    }
}
