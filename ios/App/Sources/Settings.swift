import SwiftUI

/// The app's preferences. Few, on purpose — but the style is one of them: the
/// app carries all four, and which one a reader wants is theirs to say.
///
/// Backed by UserDefaults directly rather than @AppStorage: @AppStorage is
/// built for use inside a View, and does not drive objectWillChange when it
/// sits on an ObservableObject, so a toggle here would not have refreshed the
/// text elsewhere in the app.
@MainActor
final class Settings: ObservableObject {
    static let shared = Settings()

    @Published var theme: Theme { didSet { store.set(theme.rawValue, forKey: Key.theme) } }
    @Published var dyslexicFont: Bool { didSet { store.set(dyslexicFont, forKey: Key.dyslexic) } }
    @Published var hourReminders: Bool { didSet { store.set(hourReminders, forKey: Key.reminders) } }
    @Published var lastRead: String { didSet { store.set(lastRead, forKey: Key.lastRead) } }

    private let store = UserDefaults.standard

    private enum Key {
        static let theme = "theme"
        static let dyslexic = "dyslexicFont"
        static let reminders = "hourReminders"
        static let lastRead = "lastRead"
    }

    private init() {
        theme = Theme(rawValue: store.string(forKey: Key.theme) ?? "") ?? .sanctuary
        dyslexicFont = store.bool(forKey: Key.dyslexic)
        hourReminders = store.bool(forKey: Key.reminders)
        lastRead = store.string(forKey: Key.lastRead) ?? ""
    }
}
