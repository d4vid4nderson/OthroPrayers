import XCTest

/// Drives the arrangement flow the way a reader would.
///
/// The point of this test is the drag: `reorderable()` is new in iOS 27 and
/// reorders the bound collection without a move closure, so the only way to
/// know it is wired correctly is to actually drag a row and read the order back.
final class ArrangeUITests: XCTestCase {

    private var app: XCUIApplication!

    override func setUp() {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launch()
    }

    /// Only the prayer rows. Section headers and footers are cells too, so they
    /// are excluded by identifier rather than by position.
    /// SwiftUI merges each List row into one accessibility element, so the rows
    /// come through as static texts carrying the identifier — not as cells.
    private var prayerCells: XCUIElementQuery {
        app.staticTexts.matching(identifier: "prayer.row")
    }

    /// Titles of the prayer rows, top to bottom. In edit mode the row carries a
    /// delete affordance, so its label is prefixed "Remove, ".
    private func rowTitles() -> [String] {
        prayerCells.allElementsBoundByIndex.map {
            $0.label.replacingOccurrences(of: "Remove, ", with: "")
        }
    }

    /// One run should tell us the whole tree when a query misses.
    private func dumpTree(_ why: String) {
        let a = XCTAttachment(string: app.debugDescription)
        a.name = "tree-\(why)"
        a.lifetime = .keepAlways
        add(a)
    }

    private func openMorningPrayerArrange() {
        app.tabBars.buttons["Prayers"].tap()
        let morning = app.staticTexts["Morning Prayer"]
        XCTAssertTrue(morning.waitForExistence(timeout: 10), "Morning Prayer not listed")
        morning.tap()

        let arrange = app.buttons["Arrange this office"]
        XCTAssertTrue(arrange.waitForExistence(timeout: 10), "Arrange button missing from the top bar")
        arrange.tap()
        XCTAssertTrue(app.navigationBars.buttons["Done"].waitForExistence(timeout: 10),
                      "Arrange sheet did not open")
    }

    func testReorderAddAndSave() throws {
        openMorningPrayerArrange()

        let before = rowTitles()
        if before.count <= 3 { dumpTree("seed") }
        XCTAssertGreaterThan(before.count, 3, "expected the printed office to seed the editor")
        attach(name: "1-arrange-open")

        // --- the drag: first prayer down past the fourth ---
        // Grab near the right edge, where the reorder control sits in edit mode.
        let grab = CGVector(dx: 0.92, dy: 0.5)
        let from = prayerCells.element(boundBy: 0).coordinate(withNormalizedOffset: grab)
        let to = prayerCells.element(boundBy: 3).coordinate(withNormalizedOffset: grab)
        from.press(forDuration: 1.2, thenDragTo: to)

        let after = rowTitles()
        attach(name: "2-after-drag")
        XCTAssertEqual(Set(before), Set(after), "a reorder must not add or lose prayers")
        XCTAssertNotEqual(before, after, "reorderable() did not change the order")

        // --- add a prayer from General Prayers ---
        app.buttons["Add a prayer"].tap()
        // General Prayers is the fifth section, ~38 rows down, so the row is not
        // rendered yet. Search for it — which also exercises the palette filter.
        let field = app.searchFields.firstMatch
        XCTAssertTrue(field.waitForExistence(timeout: 10), "palette has no search field")
        field.tap()
        field.typeText("Jesus")
        let jesus = app.staticTexts["The Jesus Prayer"]
        XCTAssertTrue(jesus.waitForExistence(timeout: 10), "palette did not list General Prayers")
        jesus.tap()

        let withAdded = rowTitles()
        attach(name: "3-after-add")
        XCTAssertEqual(withAdded.count, after.count + 1,
                       "expected exactly one new row.\nbefore add: \(after)\nafter add:  \(withAdded)")
        // The row is one combined element, so its label carries the prayer and
        // the book it came from: "The Jesus Prayer, General Prayers".
        XCTAssertTrue(withAdded.contains { $0.contains("The Jesus Prayer") },
                      "the added prayer is not in the list: \(withAdded)")

        // --- save, and confirm the page says it is the reader's own ---
        app.navigationBars.buttons["Done"].tap()
        XCTAssertTrue(app.staticTexts["YOUR ARRANGEMENT"].waitForExistence(timeout: 10),
                      "the reading page did not mark itself as customised")
        attach(name: "4-reading-customised")
    }

    private func attach(name: String) {
        let shot = XCTAttachment(screenshot: app.screenshot())
        shot.name = name
        shot.lifetime = .keepAlways
        add(shot)
    }
}
