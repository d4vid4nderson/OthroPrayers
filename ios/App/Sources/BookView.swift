import SwiftUI

/// A book's contents: numerals and hairlines, no boxes.
struct BookView: View {
    /// Colours and type, from the environment so this view is
    /// invalidated when they change. See Design.
    @Environment(\.design) var design
    private var palette: Palette { design.palette }
    let book: Book
    @EnvironmentObject private var library: Library
    // observed so a theme change re-renders this screen
    @EnvironmentObject private var settings: Settings

    private static let numerals = ["I", "II", "III", "IV", "V", "VI", "VII",
                                   "VIII", "IX", "X", "XI", "XII"]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                if let summary = library.page(book.slug)?.summary, !summary.isEmpty {
                    Text(summary)
                        .font(Typeface.prayer(.callout).italic())
                        .foregroundStyle(palette.inkSoft)
                        .padding(.top, 6)
                        .padding(.bottom, 22)
                }
                ForEach(Array(book.sections.enumerated()), id: \.element.id) { i, section in
                    NavigationLink(value: Route.page(section.slug)) {
                        HStack(alignment: .firstTextBaseline, spacing: 15) {
                            Text(Self.numerals[safe: i] ?? "\(i + 1)")
                                .font(Typeface.display(.callout))
                                .foregroundStyle(palette.inkFaint)
                                .frame(width: 26, alignment: .leading)
                            VStack(alignment: .leading, spacing: 3) {
                                Text(section.title).font(Typeface.display(.title3))
                                if !section.blurb.isEmpty {
                                    Text(section.blurb)
                                        .font(.caption)
                                        .foregroundStyle(palette.inkSoft)
                                        .fixedSize(horizontal: false, vertical: true)
                                }
                            }
                            Spacer(minLength: 0)
                        }
                        .padding(.vertical, 16)
                        .contentShape(.rect)
                    }
                    .buttonStyle(.plain)
                    ThemedRule()
                }
            }
            .padding(.horizontal, 22)
            .padding(.bottom, 24)
        }
        .scrollEdgeEffectStyle(.soft, for: .top)
        .background(palette.ground)
        .navigationTitle(book.title)
    }
}

extension Array {
    subscript(safe index: Int) -> Element? {
        indices.contains(index) ? self[index] : nil
    }
}
