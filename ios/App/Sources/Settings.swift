import SwiftUI

/// The app's preferences. Deliberately few: Sanctuary is one designed system,
/// not a themeable one, so there is no accent picker and no background
/// temperature — those controls existed on the web and could only be used to
/// break it.
@MainActor
final class Settings: ObservableObject {
    static let shared = Settings()

    @AppStorage("dyslexicFont") var dyslexicFont = false { willSet { objectWillChange.send() } }
    @AppStorage("hourReminders") var hourReminders = false { willSet { objectWillChange.send() } }
    @AppStorage("lastRead") var lastRead = ""

    private init() {}
}
