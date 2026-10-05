import Foundation

// Custom arrangements of an office.
//
// The printed text is never edited. An arrangement is a separate, ordered list
// of references into the content model, and the reader can throw it away at any
// time to get the published office back exactly as St. Tikhon's set it.

// MARK: - A prayer

/// One prayer: a heading block and everything beneath it until the next
/// heading. This is the unit the reader reorders, removes and inserts.
struct PrayerUnit: Identifiable, Hashable {
    let pageSlug: String
    let headingID: String
    let title: String
    /// The heading block followed by its body.
    let blocks: [Block]

    var id: String { "\(pageSlug)#\(headingID)" }
}

/// One slot in an arrangement.
///
/// It carries its own `id` rather than deriving one from the prayer, because a
/// reader may legitimately want the same prayer twice — the Jesus Prayer at the
/// start of an office and again at its close. Keying on the prayer would make
/// the second copy collide with the first and confuse `ForEach`.
struct ArrangedPrayer: Codable, Hashable, Identifiable {
    var id: UUID = UUID()
    let page: String
    let heading: String

    init(id: UUID = UUID(), page: String, heading: String) {
        self.id = id
        self.page = page
        self.heading = heading
    }

    init(_ unit: PrayerUnit) {
        self.init(page: unit.pageSlug, heading: unit.headingID)
    }
}

// MARK: - Splitting a page into prayers

extension Library {
    /// Whatever stands before the first heading — the lead line that introduces
    /// the office. It belongs to the page, not to any prayer, so it is never
    /// reordered and never removed.
    func preamble(of slug: String) -> [Block] {
        guard let page = page(slug) else { return [] }
        return Array(page.blocks.prefix { $0.type != .heading })
    }

    /// The page's prayers, in printed order.
    func units(of slug: String) -> [PrayerUnit] {
        guard let page = page(slug) else { return [] }
        var out: [PrayerUnit] = []
        var current: [Block] = []

        func flush() {
            guard let head = current.first, head.type == .heading else { return }
            out.append(PrayerUnit(pageSlug: slug,
                                  headingID: head.stableID,
                                  title: head.plain,
                                  blocks: current))
        }

        for block in page.blocks {
            if block.type == .heading {
                flush()
                current = [block]
            } else if !current.isEmpty {
                current.append(block)
            }
        }
        flush()
        return out
    }

    /// Resolve a stored reference back to its prayer. Returns nil when the
    /// content has been regenerated and the heading no longer exists, which is
    /// why every call site drops missing prayers rather than trapping.
    func unit(_ ref: ArrangedPrayer) -> PrayerUnit? {
        units(of: ref.page).first { $0.headingID == ref.heading }
    }

    /// The prayers offered when adding to an office: everything in A Little
    /// Prayer Book, grouped by the section it comes from.
    func palette() -> [(section: BookSection, units: [PrayerUnit])] {
        guard let book = books.first(where: { $0.slug == "prayerbook" }) else { return [] }
        return book.sections.compactMap { section in
            let units = units(of: section.slug)
            return units.isEmpty ? nil : (section, units)
        }
    }
}

// MARK: - The store

/// The reader's arrangements, one per office, saved as JSON beside the app's
/// other data. Absent key means "as printed" — there is no copy of the
/// published order kept anywhere, so it cannot drift from the content model.
@MainActor
final class Arrangements: ObservableObject {
    static let shared = Arrangements()

    @Published private var byPage: [String: [ArrangedPrayer]]

    private static let fileName = "arrangements.json"

    private static var fileURL: URL {
        let dir = FileManager.default.urls(for: .applicationSupportDirectory,
                                           in: .userDomainMask)[0]
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir.appendingPathComponent(fileName)
    }

    private init() {
        if let data = try? Data(contentsOf: Self.fileURL),
           let decoded = try? JSONDecoder().decode([String: [ArrangedPrayer]].self, from: data) {
            byPage = decoded
        } else {
            byPage = [:]
        }
    }

    /// The reader's order for this office, or nil when it stands as printed.
    func arrangement(for slug: String) -> [ArrangedPrayer]? { byPage[slug] }

    func isCustomised(_ slug: String) -> Bool { byPage[slug] != nil }

    func save(_ prayers: [ArrangedPrayer], for slug: String) {
        byPage[slug] = prayers
        persist()
    }

    /// Back to the printed office.
    func reset(_ slug: String) {
        byPage.removeValue(forKey: slug)
        persist()
    }

    private func persist() {
        guard let data = try? JSONEncoder().encode(byPage) else { return }
        try? data.write(to: Self.fileURL, options: .atomic)
    }
}
