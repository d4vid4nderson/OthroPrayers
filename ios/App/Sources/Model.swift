import Foundation

// The content model mirrors ios/Content/content.json and structure.json, both
// generated from build.py. Nothing here is hand-maintained: regenerate with
//     python3 build.py && python3 export_content.py
// and the app picks the new text up on the next build.

// MARK: - Content

/// One run of text inside a block, carrying its inline mark and, for a
/// cross-reference, the slug of the page it points at.
struct Run: Codable, Hashable {
    enum Mark: String, Codable {
        case rubric, signum, dropcap, italic, strong, smallcaps, versal, sup, small
    }

    let t: String
    let mark: Mark?
    let href: String?

    /// Hymns keep their line breaks; everything else is a single line.
    var lines: [String] { t.components(separatedBy: "\n") }
}

struct Block: Codable, Hashable, Identifiable {
    enum Kind: String, Codable {
        case heading, subheading, rubric, verse, lead, paragraph, item, term, definition
    }

    let type: Kind
    let runs: [Run]
    let style: String?
    let id: String?

    var isHymn: Bool { style == "hymn" }
    var plain: String { runs.map(\.t).joined() }
}

extension Block {
    // Identifiable: the generator only gives ids to jump targets, so fall back
    // to the text, which is stable for a given build.
    var stableID: String { id ?? plain }
}

struct Page: Codable, Hashable, Identifiable {
    let slug: String
    let title: String
    let summary: String
    let blocks: [Block]

    var id: String { slug }

    /// The headings a reader can jump to, in order.
    var sections: [Block] { blocks.filter { $0.type == .heading } }
}

private struct ContentFile: Codable { let pages: [Page] }

// MARK: - Structure

struct Hour: Codable, Hashable, Identifiable {
    let slug: String
    let title: String
    let blurb: String
    let when: String
    let from: Int
    let until: Int

    var id: String { slug }

    /// True when `hour` falls in this office's window. Compline's window wraps
    /// past midnight (21 → 4), so the two cases are not the same test.
    func covers(hour: Int) -> Bool {
        from < until ? (hour >= from && hour < until) : (hour >= from || hour < until)
    }
}

struct BookSection: Codable, Hashable, Identifiable {
    let slug: String
    let title: String
    let blurb: String
    var id: String { slug }
}

struct Book: Codable, Hashable, Identifiable {
    let slug: String
    let title: String
    let sections: [BookSection]
    var id: String { slug }
}

struct Extra: Codable, Hashable, Identifiable {
    let slug: String
    let title: String
    let blurb: String
    var id: String { slug }
}

private struct StructureFile: Codable {
    let hours: [Hour]
    let books: [Book]
    let extras: [Extra]
}

// MARK: - Library

/// Everything the app knows, loaded once from the bundle.
@MainActor
final class Library: ObservableObject {
    static let shared = Library()

    let pages: [String: Page]
    let hours: [Hour]
    let books: [Book]
    let extras: [Extra]

    private init() {
        let content: ContentFile = Bundle.main.decode("content.json")
        let structure: StructureFile = Bundle.main.decode("structure.json")
        pages = Dictionary(uniqueKeysWithValues: content.pages.map { ($0.slug, $0) })
        hours = structure.hours
        books = structure.books
        extras = structure.extras
    }

    func page(_ slug: String) -> Page? { pages[slug] }

    /// The office due at `date`, or the first one if nothing covers the hour.
    func currentHour(at date: Date = .now) -> Hour {
        let h = Calendar.current.component(.hour, from: date)
        return hours.first { $0.covers(hour: h) } ?? hours[0]
    }

    /// The hours other than the one showing in the hero, in their daily order.
    func remainingHours(at date: Date = .now) -> [Hour] {
        let now = currentHour(at: date)
        return hours.filter { $0.slug != now.slug }
    }

    /// The book a page belongs to, for the back button and the page turn.
    func book(containing slug: String) -> Book? {
        books.first { $0.sections.contains { $0.slug == slug } }
    }

    /// Previous and next section within a page's own book.
    func neighbours(of slug: String) -> (BookSection?, BookSection?) {
        guard let book = book(containing: slug),
              let i = book.sections.firstIndex(where: { $0.slug == slug }) else { return (nil, nil) }
        return (i > 0 ? book.sections[i - 1] : nil,
                i < book.sections.count - 1 ? book.sections[i + 1] : nil)
    }
}

extension Bundle {
    func decode<T: Decodable>(_ file: String) -> T {
        guard let url = url(forResource: file, withExtension: nil),
              let data = try? Data(contentsOf: url) else {
            fatalError("\(file) is missing from the bundle — run `python3 build.py && python3 export_content.py`")
        }
        do {
            return try JSONDecoder().decode(T.self, from: data)
        } catch {
            fatalError("\(file) could not be decoded: \(error)")
        }
    }
}
