import SwiftUI

/// The office due now, and the rest of the day behind it.
///
/// The one lit object on the screen is the hour you are meant to pray. The hour
/// is recomputed when the app returns to the foreground, so leaving it open
/// overnight does not leave Compline showing at breakfast.
struct TodayView: View {
    /// Colours and type, from the environment so this view is
    /// invalidated when they change. See Design.
    @Environment(\.design) var design
    private var palette: Palette { design.palette }
    @EnvironmentObject private var library: Library
    // observed so a theme change re-renders this screen
    @EnvironmentObject private var settings: Settings
    @Environment(\.scenePhase) private var phase
    @State private var now = Date.now

    private var current: Hour { library.currentHour(at: now) }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                MicroLabel(text: now.formatted(.dateTime.weekday(.wide).day().month(.wide)))
                    .padding(.bottom, 6)

                NavigationLink(value: current.slug) {
                    HeroCard(hour: current)
                }
                .buttonStyle(.plain)
                .padding(.bottom, 26)

                MicroLabel(text: "The rest of the day")
                    .padding(.bottom, 10)
                HourList(hours: library.remainingHours(at: now))

                MicroLabel(text: "Books")
                    .padding(.top, 28)
                    .padding(.bottom, 10)
                BookList()
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 24)
        }
        .scrollEdgeEffectStyle(.soft, for: .top)
        .background(palette.ground)
        .navigationTitle("Western Rite")
        .navigationDestination(for: String.self) { ReadingView(slug: $0) }
        .onChange(of: phase) { _, new in if new == .active { now = .now } }
    }
}

/// The lit card. Its glow is the only thing on the screen competing for
/// attention, which is the whole point.
private struct HeroCard: View {
    /// Colours and type, from the environment so this view is
    /// invalidated when they change. See Design.
    @Environment(\.design) var design
    private var palette: Palette { design.palette }
    let hour: Hour

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Now · \(hour.when)")
                .font(Typeface.label(.caption2))
                .tracking(1.6)
                .foregroundStyle(palette.accent)
                .textCase(.uppercase)
            Text(hour.title)
                .font(Typeface.display(.title))
                .foregroundStyle(palette.ink)
            Text(hour.blurb)
                .font(Typeface.prayer(.callout).italic())
                .foregroundStyle(palette.inkSoft)
                .fixedSize(horizontal: false, vertical: true)
            Label("Begin", systemImage: "chevron.right")
                .labelStyle(.titleAndIcon)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(palette.onAccent)
                .padding(.horizontal, 17)
                .padding(.vertical, 10)
                .background(palette.accent, in: Capsule())
                .padding(.top, 8)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(22)
        // Liquid Glass, tinted with the one warm light in the palette. The
        // system draws the specular edge, the blur and the motion. The
        // hand-drawn gold hairline that used to sit here is gone on purpose:
        // it fought the material's own edge rather than reinforcing it.
        .glassEffect(.regular.tint(palette.accent.opacity(0.18)),
                     in: Container.shape())
        .shadow(color: palette.accent.opacity(0.10), radius: 22)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(hour.title), due now, \(hour.when)")
        .accessibilityHint("Opens the office")
    }
}

private struct HourList: View {
    /// Colours and type, from the environment so this view is
    /// invalidated when they change. See Design.
    @Environment(\.design) var design
    private var palette: Palette { design.palette }
    let hours: [Hour]

    var body: some View {
        VStack(spacing: 0) {
            ForEach(hours) { hour in
                NavigationLink(value: hour.slug) {
                    HStack(spacing: 14) {
                        Circle().fill(palette.inkFaint).frame(width: 7, height: 7)
                        Text(hour.title).font(Typeface.display(.title3))
                        Spacer(minLength: 12)
                        MicroLabel(text: hour.when)
                    }
                    .padding(.vertical, 15)
                    .padding(.horizontal, 18)
                    .contentShape(.rect)
                }
                .buttonStyle(.plain)
                if hour.id != hours.last?.id { ThemedRule().padding(.leading, 18) }
            }
        }
        .background(palette.surface, in: Container.shape())
        .overlay(Container.shape().stroke(palette.hairline, lineWidth: 1))
    }
}

private struct BookList: View {
    /// Colours and type, from the environment so this view is
    /// invalidated when they change. See Design.
    @Environment(\.design) var design
    private var palette: Palette { design.palette }
    @EnvironmentObject private var library: Library

    var body: some View {
        VStack(spacing: 0) {
            ForEach(library.books) { book in
                NavigationLink { BookView(book: book) } label: {
                    row(title: book.title,
                        detail: "\(book.sections.count) sections",
                        symbol: book.slug == "prayerbook" ? "book.closed" : "book.pages")
                }
                .buttonStyle(.plain)
                ThemedRule().padding(.leading, 70)
            }
            ForEach(Array(library.extras.enumerated()), id: \.element.id) { i, extra in
                NavigationLink(value: extra.slug) {
                    row(title: extra.title, detail: extra.blurb, symbol: "cross")
                }
                .buttonStyle(.plain)
                if i < library.extras.count - 1 { ThemedRule().padding(.leading, 70) }
            }
        }
        .background(palette.surface, in: Container.shape())
        .overlay(Container.shape().stroke(palette.hairline, lineWidth: 1))
    }

    private func row(title: String, detail: String, symbol: String) -> some View {
        HStack(spacing: 15) {
            Image(systemName: symbol)
                .font(.system(size: 18))
                .foregroundStyle(palette.accent)
                .frame(width: 38, height: 38)
                .background(palette.accent.opacity(0.10), in: Container.inner())
                .overlay(Container.inner()
                    .stroke(palette.accent.opacity(0.18), lineWidth: 1))
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(Typeface.display(.title3))
                Text(detail).font(.caption).foregroundStyle(palette.inkSoft)
                    .lineLimit(1)
            }
            Spacer(minLength: 8)
            Image(systemName: "chevron.right").font(.footnote.weight(.semibold))
                .foregroundStyle(palette.inkFaint)
        }
        .padding(.vertical, 14)
        .padding(.horizontal, 18)
        .contentShape(.rect)
    }
}
