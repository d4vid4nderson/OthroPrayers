import XCTest

/// The worship tab, driven the way a listener would.
///
/// Audio is the kind of thing that compiles perfectly and plays nothing, so
/// this taps a real track and reads the transport back out of the UI.
final class WorshipUITests: XCTestCase {

    private var app: XCUIApplication!

    override func setUp() {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launch()
    }

    func testPlayAndPause() throws {
        app.tabBars.buttons["Worship"].tap()

        // First track alphabetically, so it is on screen without scrolling.
        let first = app.staticTexts.matching(
            NSPredicate(format: "label BEGINSWITH %@", "Dogmatic Theotokion Tone I")).firstMatch
        XCTAssertTrue(first.waitForExistence(timeout: 10), "the track list did not appear")
        attach(name: "w1-track-list")

        first.tap()

        // The bar only offers Pause when the player reports it is sounding, so
        // this is a real assertion about playback, not just about layout.
        let pause = app.buttons["Pause"]
        XCTAssertTrue(pause.waitForExistence(timeout: 10),
                      "no now-playing bar — the track did not start")
        attach(name: "w2-playing")

        pause.tap()
        XCTAssertTrue(app.buttons["Play"].waitForExistence(timeout: 5),
                      "pausing did not stop playback")

        // And the bar survives leaving the tab: the player is app-wide.
        app.tabBars.buttons["Prayers"].tap()
        app.tabBars.buttons["Worship"].tap()
        XCTAssertTrue(app.buttons["Play"].waitForExistence(timeout: 5),
                      "the player lost its track when the tab changed")
    }

    /// The bar renamed from Today, and the prayer book tab is gone.
    func testTabBar() throws {
        for name in ["Prayers", "Missal", "Worship", "Settings"] {
            XCTAssertTrue(app.tabBars.buttons[name].exists, "missing tab: \(name)")
        }
        XCTAssertFalse(app.tabBars.buttons["Today"].exists, "Today should have been renamed")
        attach(name: "w0-tab-bar")
    }

    private func attach(name: String) {
        let shot = XCTAttachment(screenshot: app.screenshot())
        shot.name = name
        shot.lifetime = .keepAlways
        add(shot)
    }
}
