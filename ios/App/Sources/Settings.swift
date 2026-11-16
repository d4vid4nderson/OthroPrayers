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

    /// Whether the app follows the phone's own text size.
    ///
    /// On by default, and the right answer for most people: the setting is
    /// system-wide for a reason. But a prayer book is read in a dim church, at
    /// arm's length, in a way a phone is mostly not, so it can be unlinked and
    /// set larger here without making every other app shout.
    @Published var followSystemTextSize: Bool {
        didSet { store.set(followSystemTextSize, forKey: Key.followTextSize) }
    }

    /// The size used when it is unlinked. Ignored while following the phone.
    @Published var textSize: DynamicTypeSize {
        didSet { store.set(Self.index(of: textSize), forKey: Key.textSize) }
    }

    /// What the app should actually apply: nothing while following the phone,
    /// which leaves the system setting in charge.
    var textSizeOverride: DynamicTypeSize? {
        followSystemTextSize ? nil : textSize
    }

    /// The sizes offered. The accessibility sizes above xxxLarge are reachable
    /// through iOS itself and are deliberately not duplicated here: they
    /// reflow the whole interface, and a reader who needs them has set them
    /// system-wide already.
    static let offeredSizes: [DynamicTypeSize] = [
        .xSmall, .small, .medium, .large, .xLarge, .xxLarge, .xxxLarge,
    ]

    private static func index(of size: DynamicTypeSize) -> Int {
        offeredSizes.firstIndex(of: size) ?? offeredSizes.firstIndex(of: .large) ?? 3
    }

    private let store = UserDefaults.standard

    private enum Key {
        static let theme = "theme"
        static let dyslexic = "dyslexicFont"
        static let reminders = "hourReminders"
        static let lastRead = "lastRead"
        static let followTextSize = "followSystemTextSize"
        static let textSize = "textSize"
    }

    private init() {
        theme = Theme(rawValue: store.string(forKey: Key.theme) ?? "") ?? .sanctuary
        dyslexicFont = store.bool(forKey: Key.dyslexic)
        hourReminders = store.bool(forKey: Key.reminders)
        lastRead = store.string(forKey: Key.lastRead) ?? ""
        // bool(forKey:) is false for a key that was never written, and the
        // default here is *on*, so the absence of the key has to be asked
        // about rather than read.
        followSystemTextSize = store.object(forKey: Key.followTextSize) == nil
            ? true
            : store.bool(forKey: Key.followTextSize)
        let i = store.object(forKey: Key.textSize) == nil
            ? Self.offeredSizes.firstIndex(of: .large) ?? 3
            : store.integer(forKey: Key.textSize)
        textSize = Self.offeredSizes[min(max(i, 0), Self.offeredSizes.count - 1)]
    }
}
