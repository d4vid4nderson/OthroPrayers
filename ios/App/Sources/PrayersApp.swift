import SwiftUI

@main
struct PrayersApp: App {
    @StateObject private var library = Library.shared
    @StateObject private var settings = Settings.shared
    /// Where a cross-reference inside a prayer sends the reader.
    @State private var deepLink: String?

    var body: some Scene {
        WindowGroup {
            RootView(deepLink: $deepLink)
                .environmentObject(library)
                .environmentObject(settings)
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
    @State private var tab = Tab.today

    enum Tab: Hashable { case today, prayers, missal, settings }

    var body: some View {
        // The classic tabItem form rather than the iOS 18 `Tab` builder: it has
        // been stable for a decade, it takes conditionals without complaint, and
        // on iOS 26+ the system still gives the bar Liquid Glass. Once the
        // project builds, the newer builder is a drop-in upgrade.
        TabView(selection: $tab) {
            NavigationStack { TodayView() }
                .tabItem { Label("Today", systemImage: "sun.horizon") }
                .tag(Tab.today)

            NavigationStack { bookView(slug: "prayerbook", fallback: "Prayers") }
                .tabItem { Label("Prayers", systemImage: "book.closed") }
                .tag(Tab.prayers)

            NavigationStack { bookView(slug: "st-peter-missal", fallback: "Missal") }
                .tabItem { Label("Missal", systemImage: "book.pages") }
                .tag(Tab.missal)

            NavigationStack { SettingsView() }
                .tabItem { Label("Settings", systemImage: "gearshape") }
                .tag(Tab.settings)
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
