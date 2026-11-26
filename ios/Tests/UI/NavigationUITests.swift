import XCTest

/// Opening a page from a book, the way a reader does.
///
/// This exists because of a bug that could not be reasoned about from the
/// source: tapping a day in Advent 2026 pushed the list of days again, with
/// the page it should have opened sitting underneath it, so going back
/// "opened" the right page. Whatever the cause, the test is the same — after
/// tapping a day the reader must be on that day — and a navigation bar title
/// is the one thing that says unambiguously which page is on top.
final class NavigationUITests: XCTestCase {

    private var app: XCUIApplication!

    override func setUp() {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launch()
    }

    /// One run should tell us the whole tree when a query misses.
    private func dumpTree(_ why: String) {
        let a = XCTAttachment(string: app.debugDescription)
        a.name = "tree-\(why)"
        a.lifetime = .keepAlways
        add(a)
    }

    /// A book reached from the Prayers tab is *pushed* into that tab's
    /// navigation stack, which is the case that broke. The Missal, which is
    /// the root of its own tab, is covered separately below.
    func testOpeningADayFromAdventOpensThatDay() throws {
        app.tabBars.buttons["Prayers"].tap()

        let book = app.staticTexts["Advent 2026"]
        guard book.waitForExistence(timeout: 15) else {
            dumpTree("no-advent-row")
            return XCTFail("Advent 2026 is not listed on the Prayers screen")
        }
        book.tap()

        guard app.navigationBars["Advent 2026"].waitForExistence(timeout: 10) else {
            dumpTree("book-did-not-open")
            return XCTFail("the Advent book did not open")
        }

        let day = app.staticTexts["November 27"]
        guard day.waitForExistence(timeout: 10) else {
            dumpTree("no-day-row")
            return XCTFail("the book did not list its days")
        }
        day.tap()

        // The day's own page must now be on top. If the list of days was
        // pushed again instead, this bar is still the book's.
        if !app.navigationBars["November 27"].waitForExistence(timeout: 10) {
            dumpTree("day-did-not-open")
            XCTFail("tapping November 27 did not open it — the top of the stack "
                    + "is \(app.navigationBars.firstMatch.identifier.isEmpty ? "unnamed" : app.navigationBars.firstMatch.identifier)")
        }
        XCTAssertFalse(app.staticTexts["Concluding Prayers"].exists,
                       "the list of days is still on screen, so the book was pushed again")
    }

    /// The same move in the book that is its own tab's root. It reached its
    /// sections through the same path, so it is worth holding to the same
    /// promise.
    func testOpeningASectionFromTheMissalOpensIt() throws {
        app.tabBars.buttons["Missal"].tap()

        guard app.navigationBars.firstMatch.waitForExistence(timeout: 15) else {
            dumpTree("missal-did-not-open")
            return XCTFail("the Missal tab did not open")
        }
        let section = app.staticTexts["Prayers Before Mass"]
        guard section.waitForExistence(timeout: 10) else {
            dumpTree("no-missal-section")
            return XCTFail("the Missal did not list its sections")
        }
        section.tap()

        if !app.navigationBars["Prayers Before Mass"].waitForExistence(timeout: 10) {
            dumpTree("missal-section-did-not-open")
            XCTFail("tapping a Missal section did not open it")
        }
    }
}
