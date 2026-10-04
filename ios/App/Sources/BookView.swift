import SwiftUI

/// A book's contents: numerals and hairlines, no boxes.
struct BookView: View {
    let book: Book
    @EnvironmentObject private var library: Library

    private static let numerals = ["I", "II", "III", "IV", "V", "VI", "VII",
                                   "VIII", "IX", "X", "XI", "XII"]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                if let summary = library.page(book.slug)?.summary, !summary.isEmpty {
                    Text(summary)
                        .font(Typeface.prayer(.callout).italic())
                        .foregroundStyle(.secondary)
                        .padding(.top, 6)
                        .padding(.bottom, 22)
                }
                ForEach(Array(book.sections.enumerated()), id: \.element.id) { i, section in
                    NavigationLink(value: section.slug) {
                        HStack(alignment: .firstTextBaseline, spacing: 15) {
                            Text(Self.numerals[safe: i] ?? "\(i + 1)")
                                .font(Typeface.display(.callout))
                                .foregroundStyle(.tertiary)
                                .frame(width: 26, alignment: .leading)
                            VStack(alignment: .leading, spacing: 3) {
                                Text(section.title).font(Typeface.display(.title3))
                                if !section.blurb.isEmpty {
                                    Text(section.blurb)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                        .fixedSize(horizontal: false, vertical: true)
                                }
                            }
                            Spacer(minLength: 0)
                        }
                        .padding(.vertical, 16)
                        .contentShape(.rect)
                    }
                    .buttonStyle(.plain)
                    Divider()
                }
            }
            .padding(.horizontal, 22)
            .padding(.bottom, 24)
        }
        .background(Color.sanctuaryGround)
        .navigationTitle(book.title)
        .navigationDestination(for: String.self) { ReadingView(slug: $0) }
    }
}

extension Array {
    subscript(safe index: Int) -> Element? {
        indices.contains(index) ? self[index] : nil
    }
}
