import SwiftUI

/// The app's preferences. Deliberately few: Sanctuary is one designed system,
/// not a themeable one, so there is no accent picker and no background
/// temperature — those existed on the web and could only be used to break it.
///
/// Backed by UserDefaults directly rather than @AppStorage: @AppStorage is
/// built for use inside a View, and does not drive objectWillChange when it
/// sits on an ObservableObject, so a toggle here would not have refreshed the
/// text elsewhere in the app.
@MainActor
final class Settings: ObservableObject {
    static let shared = Settings()

    @Published var dyslexicFont: Bool { didSet { store.set(dyslexicFont, forKey: Key.dyslexic) } }
    @Published var hourReminders: Bool { didSet { store.set(hourReminders, forKey: Key.reminders) } }
    @Published var lastRead: String { didSet { store.set(lastRead, forKey: Key.lastRead) } }

    private let store = UserDefaults.standard

    private enum Key {
        static let dyslexic = "dyslexicFont"
        static let reminders = "hourReminders"
        static let lastRead = "lastRead"
    }

    private init() {
        dyslexicFont = store.bool(forKey: Key.dyslexic)
        hourReminders = store.bool(forKey: Key.reminders)
        lastRead = store.string(forKey: Key.lastRead) ?? ""
    }
}
