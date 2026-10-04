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
        // A stock TabView: on iOS 26 and later the system gives the tab bar
        // Liquid Glass, with the scroll-edge behaviour and morphing that a
        // hand-built bar cannot reproduce.
        TabView(selection: $tab) {
            Tab("Today", systemImage: "sun.horizon", value: Tab.today) {
                NavigationStack { TodayView() }
            }
            if let book = library.books.first(where: { $0.slug == "prayerbook" }) {
                Tab("Prayers", systemImage: "book.closed", value: Tab.prayers) {
                    NavigationStack { BookView(book: book) }
                }
            }
            if let missal = library.books.first(where: { $0.slug == "st-peter-missal" }) {
                Tab("Missal", systemImage: "book.pages", value: Tab.missal) {
                    NavigationStack { BookView(book: missal) }
                }
            }
            Tab("Settings", systemImage: "gearshape", value: Tab.settings) {
                NavigationStack { SettingsView() }
            }
        }
        .sheet(item: Binding(get: { deepLink.map(LinkedPage.init) },
                             set: { deepLink = $0?.slug })) { linked in
            NavigationStack {
                ReadingView(slug: linked.slug)
            }
        }
    }
}

private struct LinkedPage: Identifiable {
    let slug: String
    var id: String { slug }
}
