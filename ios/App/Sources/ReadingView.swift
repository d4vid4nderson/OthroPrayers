import SwiftUI

/// A page of prayer: type, white space and one hairline.
///
/// The contents fold away behind one line, closed by default, so the page opens
/// on the prayer rather than on a menu. The page turn sits at the foot.
struct ReadingView: View {
    let slug: String
    @EnvironmentObject private var library: Library
    @EnvironmentObject private var settings: Settings
    @State private var showContents = false

    private var page: Page? { library.page(slug) }

    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                if let page {
                    VStack(spacing: 0) {
                        masthead(page)
                        if page.sections.count > 1 { contents(page, proxy: proxy) }
                        ForEach(page.blocks, id: \.stableID) { block in
                            BlockView(block: block)
                                .id(block.id ?? "")
                        }
                        pageTurn
                    }
                    .padding(.horizontal, 22)
                    .padding(.bottom, 28)
                } else {
                    ContentUnavailableView("Not in this book", systemImage: "book.closed")
                        .padding(.top, 80)
                }
            }
        }
        .background(Color.sanctuaryGround)
        .navigationTitle(page?.title ?? "")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear { settings.lastRead = slug }
    }

    private func masthead(_ page: Page) -> some View {
        VStack(spacing: 10) {
            Text(page.title)
                .font(Typeface.display(.largeTitle))
                .multilineTextAlignment(.center)
            GoldRule().padding(.top, 8)
        }
        .frame(maxWidth: .infinity)
        .padding(.top, 18)
        .padding(.bottom, 20)
    }

    /// One quiet line, closed by default. DisclosureGroup rather than a custom
    /// control so VoiceOver announces the expanded state for free.
    private func contents(_ page: Page, proxy: ScrollViewProxy) -> some View {
        DisclosureGroup(isExpanded: $showContents) {
            VStack(spacing: 0) {
                ForEach(page.sections, id: \.stableID) { section in
                    Button {
                        withAnimation {
                            proxy.scrollTo(section.id ?? "", anchor: .top)
                            showContents = false
                        }
                    } label: {
                        Text(section.plain)
                            .font(Typeface.prayer(.callout))
                            .foregroundStyle(.secondary)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(.vertical, 11)
                            .contentShape(.rect)
                    }
                    .buttonStyle(.plain)
                    Divider()
                }
            }
        } label: {
            MicroLabel(text: "Contents")
        }
        .tint(.secondary)
        .padding(.bottom, 14)
    }

    @ViewBuilder
    private var pageTurn: some View {
        let (previous, next) = library.neighbours(of: slug)
        if previous != nil || next != nil {
            VStack(spacing: 0) {
                Divider().padding(.bottom, 20)
                HStack(spacing: 10) {
                    if let previous {
                        turn(previous, direction: .backward)
                    }
                    if let next {
                        turn(next, direction: .forward)
                    }
                }
            }
            .padding(.top, 34)
        }
    }

    private enum Direction { case backward, forward }

    private func turn(_ section: BookSection, direction: Direction) -> some View {
        NavigationLink(value: section.slug) {
            HStack(spacing: 9) {
                if direction == .backward {
                    Image(systemName: "chevron.left").font(.footnote.weight(.semibold))
                        .foregroundStyle(.tertiary)
                }
                VStack(alignment: direction == .backward ? .leading : .trailing, spacing: 1) {
                    MicroLabel(text: direction == .backward ? "Previous" : "Next")
                    Text(section.title)
                        .font(Typeface.display(.callout))
                        .lineLimit(1)
                }
                if direction == .forward {
                    Image(systemName: "chevron.right").font(.footnote.weight(.semibold))
                        .foregroundStyle(.tertiary)
                }
            }
            .frame(maxWidth: .infinity,
                   alignment: direction == .backward ? .leading : .trailing)
            .padding(.vertical, 12)
            .padding(.horizontal, 16)
            // pills, never squares
            .background(Color.sanctuarySurface, in: Capsule())
            .overlay(Capsule().stroke(.separator, lineWidth: 1))
            .contentShape(Capsule())
        }
        .buttonStyle(.plain)
    }
}
