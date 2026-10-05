import SwiftUI

@main
struct PrayersApp: App {
    @StateObject private var library = Library.shared
    @StateObject private var settings = Settings.shared
    @StateObject private var arrangements = Arrangements.shared
    @StateObject private var player = Player.shared
    /// Where a cross-reference inside a prayer sends the reader.
    @State private var deepLink: String?

    var body: some Scene {
        WindowGroup {
            RootView(deepLink: $deepLink)
                .environmentObject(library)
                .environmentObject(settings)
                .environmentObject(arrangements)
                .environmentObject(player)
                // Sanctuary is dark by construction, not by preference.
                .preferredColorScheme(.dark)
                // the single accent: the system tints every stock control with it
                .tint(.sanctuaryGold)
                .onOpenURL { url in
                    guard url.scheme == "prayers", url.host == "page" else { return }
                    deepLink = url.lastPathComponent
                }
        }
    }
}

struct RootView: View {
    @Binding var deepLink: String?
    @EnvironmentObject private var library: Library
    @State private var pane = Pane.prayers

    /// Named `Pane` rather than `Tab`: SwiftUI's own `Tab` builder is used
    /// below, and a nested type called `Tab` would shadow it.
    enum Pane: Hashable { case prayers, missal, worship, settings }

    var body: some View {
        // The iOS 18+ `Tab` builder, which is what the newer bar behaviours —
        // minimising, the glass morph between bar and content — are written
        // against. The old `.tabItem` form still compiles but opts out of them.
        TabView(selection: $pane) {
            Tab("Prayers", systemImage: "sun.horizon", value: Pane.prayers) {
                NavigationStack { TodayView() }
            }
            Tab("Missal", systemImage: "book.pages", value: Pane.missal) {
                NavigationStack { bookView(slug: "st-peter-missal", fallback: "Missal") }
            }
            Tab("Worship", systemImage: "music.note.list", value: Pane.worship) {
                NavigationStack { WorshipView() }
            }
            Tab("Settings", systemImage: "gearshape", value: Pane.settings) {
                NavigationStack { SettingsView() }
            }
        }
        // The bar collapses to a pill as the reader scrolls down into a prayer
        // and returns on the way back up: more page, and no gesture to learn.
        .tabBarMinimizeBehavior(.onScrollDown)
        .sheet(item: linkedPage) { linked in
            NavigationStack { ReadingView(slug: linked.slug) }
        }
    }

    @ViewBuilder
    private func bookView(slug: String, fallback: String) -> some View {
        if let book = library.books.first(where: { $0.slug == slug }) {
            BookView(book: book)
        } else {
            ContentUnavailableView("Not in this build", systemImage: "book.closed")
                .navigationTitle(fallback)
        }
    }

    private var linkedPage: Binding<LinkedPage?> {
        Binding(get: { deepLink.map(LinkedPage.init) },
                set: { deepLink = $0?.slug })
    }
}

struct LinkedPage: Identifiable {
    let slug: String
    var id: String { slug }
}
