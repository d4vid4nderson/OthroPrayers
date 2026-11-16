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
                // dark themes get a dark interface; the system does the rest
                .preferredColorScheme(settings.preferredScheme)
                // Applied at the root so the whole app scales together —
                // prayer text, tab bar, settings — rather than the prayers
                // growing out of step with the chrome around them.
                //
                // Always this one modifier, never a conditional one: see
                // Settings.textSizeRange. Attaching it only when unlinked
                // changed the view's type as the toggle flipped, which tore
                // down the navigation stack and bounced the reader out of
                // Settings every time they touched it.
                .dynamicTypeSize(settings.textSizeRange)
                // the single accent: the system tints every stock control with it
                .tint(settings.effectiveTheme.palette.accent)
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
    @EnvironmentObject private var settings: Settings
    @Environment(\.scenePhase) private var phase

    /// Named `Pane` rather than `Tab`: SwiftUI's own `Tab` builder is used
    /// below, and a nested type called `Tab` would shadow it.
    enum Pane: String, Hashable { case prayers, missal, worship, settings }

    /// Bound through Settings rather than held here. @State and @SceneStorage
    /// were both lost when a theme change rebuilt this view; the singleton is
    /// not rebuilt, so the tab survives.
    private var pane: Binding<Pane> {
        Binding(get: { Pane(rawValue: settings.pane) ?? .prayers },
                set: { settings.pane = $0.rawValue })
    }

    var body: some View {
        // The iOS 18+ `Tab` builder, which is what the newer bar behaviours —
        // minimising, the glass morph between bar and content — are written
        // against. The old `.tabItem` form still compiles but opts out of them.
        TabView(selection: pane) {
            Tab("Prayers", systemImage: "sun.horizon", value: Pane.prayers) {
                NavigationStack { TodayView() }
            }
            Tab("Missal", systemImage: "book.pages", value: Pane.missal) {
                NavigationStack { bookView(slug: "st-peter-missal", fallback: "Missal") }
            }
            // Only when there is something to hear. A build made from a clean
            // checkout has the manifest but none of the audio, and a tab full
            // of rows that do nothing when tapped is worse than no tab.
            if Chant.hasAudio {
                Tab("Worship", systemImage: "music.note.list", value: Pane.worship) {
                    NavigationStack { WorshipView() }
                }
            }
            Tab("Settings", systemImage: "gearshape", value: Pane.settings) {
                NavigationStack { SettingsView() }
            }
        }
        // The bar collapses to a pill as the reader scrolls down into a prayer
        // and returns on the way back up: more page, and no gesture to learn.
        .tabBarMinimizeBehavior(.onScrollDown)
        // Read from the window scene, not from the environment: the app
        // forces a colour scheme, and the environment would report that back
        // rather than the phone's own setting. Refreshed whenever the app
        // comes forward, which is when a change made in Settings.app lands.
        .onAppear { settings.systemIsDark = Appearance.systemIsDark }
        .onChange(of: phase) { _, new in
            if new == .active { settings.systemIsDark = Appearance.systemIsDark }
        }
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


