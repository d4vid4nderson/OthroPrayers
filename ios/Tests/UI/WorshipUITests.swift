import XCTest

/// The worship tab, driven the way a listener would.
///
/// Audio is the kind of thing that compiles perfectly and plays nothing, so
/// this taps real recordings and reads the transport back out of the UI.
final class WorshipUITests: XCTestCase {

    private var app: XCUIApplication!

    override func setUp() {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launch()
    }

    /// The recordings are not in the repository — they are other people's
    /// published work and it is public — so a build made from a clean checkout
    /// has no Worship tab at all, by design. These tests need audio to mean
    /// anything, so they skip rather than fail when it is absent. That is the
    /// state CI always runs in; they still run in full on a machine that has
    /// the recordings staged.
    private func requireWorship() throws {
        guard app.tabBars.buttons["Worship"].waitForExistence(timeout: 5) else {
            throw XCTSkip("no recordings in this build, so there is no Worship tab")
        }
    }

    /// A collection is a door, not a list: the tracks live on its own page.
    func testCollectionOpensItsOwnPage() throws {
        try requireWorship()
        app.tabBars.buttons["Worship"].tap()

        let collection = element(beginning: "All-Merciful Saviour Monastery")
        XCTAssertTrue(collection.waitForExistence(timeout: 10),
                      "the collection row did not appear on the worship screen")
        attach(name: "w1-worship-root")

        // The tracks belong to the collection's page, not the screen above it.
        let track = element(beginning: "Dogmatic Theotokion Tone I")
        XCTAssertFalse(track.exists, "a collection's tracks should not be on the main screen")

        collection.tap()
        XCTAssertTrue(track.waitForExistence(timeout: 10), "the collection page did not open")
        attach(name: "w2-collection-page")

        track.tap()

        // The bar only offers Pause when the player reports it is sounding, so
        // this is a real assertion about playback, not just about layout.
        let pause = app.buttons["Pause"]
        XCTAssertTrue(pause.waitForExistence(timeout: 10),
                      "no now-playing bar — the track did not start")
        attach(name: "w3-playing")

        pause.tap()
        XCTAssertTrue(app.buttons["Play"].waitForExistence(timeout: 5),
                      "pausing did not stop playback")

        // And the bar survives leaving the tab: the player is app-wide.
        app.tabBars.buttons["Prayers"].tap()
        app.tabBars.buttons["Worship"].tap()
        XCTAssertTrue(app.buttons["Play"].waitForExistence(timeout: 5),
                      "the player lost its track when the tab changed")
    }

    /// A single is not behind a door: it plays from the worship screen itself.
    func testSinglePlaysFromTheMainScreen() throws {
        try requireWorship()
        app.tabBars.buttons["Worship"].tap()

        let single = element(beginning: "Mary, We Hail Thee")
        XCTAssertTrue(single.waitForExistence(timeout: 10),
                      "the single was not on the worship screen")

        single.tap()
        XCTAssertTrue(app.buttons["Pause"].waitForExistence(timeout: 10),
                      "the single did not start")
        attach(name: "w4-single-playing")
    }

    /// The bar renamed from Today, and the prayer book tab is gone.
    func testTabBar() throws {
        for name in ["Prayers", "Missal", "Settings"] {
            XCTAssertTrue(app.tabBars.buttons[name].exists, "missing tab: \(name)")
        }
        // Worship is conditional — it appears only when the build carries
        // recordings — so its presence is not asserted either way here. What
        // is asserted is that its absence costs nothing else: the other three
        // tabs are all still there.
        XCTAssertFalse(app.tabBars.buttons["Today"].exists, "Today should have been renamed")
        attach(name: "w0-tab-bar")
    }

    /// Rows combine their children for VoiceOver, so each one surfaces as a
    /// single button whose label starts with the title.
    private func element(beginning: String) -> XCUIElement {
        app.buttons.matching(NSPredicate(format: "label BEGINSWITH %@", beginning)).firstMatch
    }

    private func attach(name: String) {
        let shot = XCTAttachment(screenshot: app.screenshot())
        shot.name = name
        shot.lifetime = .keepAlways
        add(shot)
    }
}
