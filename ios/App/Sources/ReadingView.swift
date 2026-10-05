import SwiftUI

/// A page of prayer: type, white space and one hairline.
///
/// The contents fold away behind one line, closed by default, so the page opens
/// on the prayer rather than on a menu. The page turn sits at the foot.
///
/// The office is drawn prayer by prayer rather than block by block, because the
/// prayer is the unit the reader arranges. When an arrangement exists it drives
/// the order; otherwise the printed order does.
struct ReadingView: View {
    let slug: String
    @EnvironmentObject private var library: Library
    @EnvironmentObject private var settings: Settings
    @EnvironmentObject private var arrangements: Arrangements
    @State private var showContents = false
    @State private var showArrange = false

    private var page: Page? { library.page(slug) }

    /// A prayer as drawn on the page. The identity is the arrangement slot, not
    /// the prayer, so the same prayer can appear twice without the two copies
    /// colliding as view identities.
    private struct Drawn: Identifiable {
        let id: String
        let unit: PrayerUnit
    }

    private var drawn: [Drawn] {
        if let arrangement = arrangements.arrangement(for: slug) {
            return arrangement.compactMap { slot in
                library.unit(slot).map { Drawn(id: slot.id.uuidString, unit: $0) }
            }
        }
        return library.units(of: slug).map { Drawn(id: $0.id, unit: $0) }
    }

    private var isCustomised: Bool { arrangements.isCustomised(slug) }

    var body: some View {
        ScrollViewReader { proxy in
            ScrollView {
                if let page {
                    VStack(spacing: 0) {
                        masthead(page)
                        if drawn.count > 1 { contents(proxy: proxy) }

                        ForEach(library.preamble(of: slug), id: \.stableID) { block in
                            BlockView(block: block)
                        }

                        ForEach(drawn) { item in
                            VStack(spacing: 0) {
                                ForEach(Array(item.unit.blocks.enumerated()), id: \.offset) { _, block in
                                    BlockView(block: block)
                                }
                            }
                            .id(item.id)
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
        .scrollEdgeEffectStyle(.soft, for: .top)
        .background(Color.sanctuaryGround)
        .navigationTitle(page?.title ?? "")
        .navigationBarTitleDisplayMode(.inline)
        // iOS 27. A prayer book should not shove the previous page sideways
        // out of the way; it should dissolve into the next one.
        .navigationTransition(.crossFade)
        .toolbar {
            if drawn.count > 1 {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        showArrange = true
                    } label: {
                        Label("Arrange", systemImage: isCustomised
                              ? "list.bullet.indent"
                              : "arrow.up.arrow.down")
                    }
                    .accessibilityLabel("Arrange this office")
                }
            }
        }
        .sheet(isPresented: $showArrange) {
            NavigationStack {
                ArrangeView(slug: slug, title: page?.title ?? "")
            }
        }
        .onAppear { settings.lastRead = slug }
    }

    private func masthead(_ page: Page) -> some View {
        VStack(spacing: 10) {
            Text(page.title)
                .font(Typeface.display(.largeTitle))
                .multilineTextAlignment(.center)
            GoldRule().padding(.top, 8)
            if isCustomised {
                MicroLabel(text: "Your arrangement")
                    .padding(.top, 6)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.top, 18)
        .padding(.bottom, 20)
    }

    /// One quiet line, closed by default. DisclosureGroup rather than a custom
    /// control so VoiceOver announces the expanded state for free.
    private func contents(proxy: ScrollViewProxy) -> some View {
        DisclosureGroup(isExpanded: $showContents) {
            VStack(spacing: 0) {
                ForEach(drawn) { item in
                    Button {
                        withAnimation {
                            proxy.scrollTo(item.id, anchor: .top)
                            showContents = false
                        }
                    } label: {
                        Text(item.unit.title)
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
