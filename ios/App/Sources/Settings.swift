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

    /// Whether the app takes its light or dark from the phone.
    ///
    /// Without this the app simply forced whatever the chosen theme was, so a
    /// phone in light mode still got a dark app — the theme decided, and the
    /// phone was never consulted. On by default, which is what most people
    /// expect of an app they did not configure.
    @Published var followSystemAppearance: Bool {
        didSet { store.set(followSystemAppearance, forKey: Key.followAppearance) }
    }

    /// Which phosphor the Terminal theme glows in.
    @Published var terminalPhosphor: Theme.Phosphor {
        didSet { store.set(terminalPhosphor.rawValue, forKey: Key.phosphor) }
    }

    /// Which theme to use in each appearance while following the phone.
    @Published var lightTheme: Theme {
        didSet { store.set(lightTheme.rawValue, forKey: Key.lightTheme) }
    }
    @Published var darkTheme: Theme {
        didSet { store.set(darkTheme.rawValue, forKey: Key.darkTheme) }
    }

    /// The phone's current appearance, pushed in from the view tree, which is
    /// the only place it can be read. Not persisted: it is a fact about now.
    @Published var systemIsDark = false

    /// Which tab is open.
    ///
    /// It lived in @State, and then in @SceneStorage, and was lost both times
    /// when a theme change rebuilt the view — the reader was dropped back on
    /// Prayers mid-setting, which reads as the settings screen closing itself.
    /// This object is a singleton that nothing can rebuild, so a selection
    /// kept here outlives anything SwiftUI does to the views.
    @Published var pane = "prayers" { didSet { store.set(pane, forKey: Key.pane) } }

    /// The theme actually drawn.
    var effectiveTheme: Theme {
        followSystemAppearance ? (systemIsDark ? darkTheme : lightTheme) : theme
    }

    /// What to force on the interface, or nil to leave the phone in charge.
    /// nil is what makes `systemIsDark` meaningful: forcing a scheme would
    /// make the environment report back the value we just set.
    /// Always the drawn theme's own lightness, never nil.
    ///
    /// It used to be nil while following the phone, so that reading
    /// \.colorScheme back would report the phone rather than our own override.
    /// That traded away the thing that matters: with no override, iOS supplies
    /// light-mode system colours — .primary is black, the default background
    /// is white — while the theme paints dark surfaces underneath. Black text
    /// on a near-black card, and a cream page behind dark cards.
    ///
    /// The phone's appearance is read from the window scene instead (see
    /// Appearance), which an override on our own views does not touch.
    var preferredScheme: ColorScheme? {
        effectiveTheme.colorScheme
    }
    @Published var dyslexicFont: Bool { didSet { store.set(dyslexicFont, forKey: Key.dyslexic) } }
    @Published var hourReminders: Bool { didSet { store.set(hourReminders, forKey: Key.reminders) } }
    @Published var lastRead: String { didSet { store.set(lastRead, forKey: Key.lastRead) } }

    /// The home-screen icon, in three parts that do not constrain each other:
    /// what it shows, what it stands on, and what colour it is drawn in.
    ///
    /// They used to be two, with the ground and the figure locked together —
    /// "Crimson on black" was one choice, and a black figure on a gradient
    /// could not be asked for at all. Every combination now exists, including
    /// the ones that are a poor idea; the picker draws each tile from the
    /// icon it would actually set, so a bad pairing is visible before it is
    /// chosen rather than after.
    @Published var iconGround: IconGround {
        didSet { store.set(iconGround.rawValue, forKey: Key.iconGround) }
    }

    /// What the icon shows.
    @Published var iconStyle: IconStyle {
        didSet { store.set(iconStyle.rawValue, forKey: Key.iconStyle) }
    }

    /// The colour the figure itself is drawn in.
    @Published var iconMark: IconMark {
        didSet { store.set(iconMark.rawValue, forKey: Key.iconMark) }
    }

    enum IconStyle: String, CaseIterable, Identifiable {
        case mark, cross, orthodox, icon, medallion
        var id: String { rawValue }

        var name: String {
            switch self {
            case .mark:      return "IC XC NIKA"
            case .cross:     return "Cross"
            case .orthodox:  return "Orthodox cross"
            case .icon:      return "Icon"
            case .medallion: return "Medallion"
            }
        }

        /// What fits under a 60pt tile.
        var shortName: String {
            switch self {
            case .mark:      return "IC XC"
            case .cross:     return "Cross"
            case .orthodox:  return "Orthodox"
            case .icon:      return "Icon"
            case .medallion: return "Medallion"
            }
        }

        var detail: String {
            switch self {
            case .mark:      return "The mark the app opens on."
            case .cross:     return "The pattée cross alone."
            case .orthodox:  return "The three-bar cross."
            case .icon:      return "The Mother of God “of the Sign”. Richly drawn, so it reads best on a large icon."
            case .medallion: return "The Christ medallion from the centre of that icon. The clearest of these when the icon is small."
            }
        }
    }

    enum IconGround: String, CaseIterable, Identifiable {
        case automatic, black, slate, paper, vellum,
             // gradients, run corner to corner
             aurora, nebula, vespers, sunrise
        var id: String { rawValue }

        var name: String {
            switch self {
            case .automatic: return "Follow appearance"
            case .black:     return "Black"
            case .slate:     return "Slate"
            case .paper:     return "Paper"
            case .vellum:    return "Vellum"
            case .aurora:    return "Aurora — emerald to sapphire"
            case .nebula:    return "Nebula — sapphire to violet"
            case .vespers:   return "Vespers — violet to crimson"
            case .sunrise:   return "Sunrise — amber to crimson"
            }
        }

        /// What fits under a 60pt tile.
        var shortName: String {
            self == .automatic ? "Auto" : name.components(separatedBy: " —")[0]
        }

        /// The ground an icon is really drawn on.
        ///
        /// "Follow appearance" names no ground of its own: it means the
        /// default icon, which carries three. Paired with anything the
        /// default is not, it has to fall back to something, and black is
        /// what the default itself is drawn on.
        var drawn: String { self == .automatic ? "black" : rawValue }
    }

    enum IconMark: String, CaseIterable, Identifiable {
        case gold, ivory, black, phosphor
        var id: String { rawValue }

        var name: String {
            switch self {
            case .gold:     return "Gold"
            case .ivory:    return "Ivory"
            case .black:    return "Black"
            case .phosphor: return "Phosphor"
            }
        }

        var shortName: String { name }
    }

    /// The icon iOS should be asked for, or nil for the default.
    ///
    /// The default is gold lettering on black that follows the phone between
    /// light, dark and tinted. Ask for those three together and you are
    /// describing the default, so it is returned — keeping the appearance
    /// switching, which no alternate has, since an alternate is one image.
    var alternateIconName: String? {
        iconGround == .automatic && iconStyle == .mark && iconMark == .gold
            ? nil
            : Self.iconName(ground: iconGround, style: iconStyle, mark: iconMark)
    }

    /// The image name for any trio — always a real one.
    ///
    /// Serves both ends: it is what `setAlternateIconName` is given, and what
    /// the picker draws its tiles from. The icons ship as loose files rather
    /// than asset-catalog entries, so `UIImage(named:)` finds the very image
    /// iOS will put on the home screen. There is no second set of previews to
    /// fall out of step with them.
    static func iconName(ground: IconGround, style: IconStyle, mark: IconMark) -> String {
        "alt-\(ground.drawn)-\(style.rawValue)-\(mark.rawValue)"
    }

    /// When each office's reminder fires, as minutes after midnight, keyed by
    /// the office's slug. Only offices the reader has moved appear here;
    /// anything absent uses `defaultMinutes(for:)`.
    @Published var reminderTimes: [String: Int] {
        didSet { store.set(reminderTimes, forKey: Key.reminderTimes) }
    }

    /// Which offices ring. One switch for all four was too blunt: a reader
    /// may want Compline and nothing else. Absent means on, so an office this
    /// build does not know about still reminds.
    @Published var reminderOff: Set<String> {
        didSet { store.set(Array(reminderOff), forKey: Key.reminderOff) }
    }

    func reminds(_ hour: Hour) -> Bool { !reminderOff.contains(hour.slug) }

    func setReminds(_ on: Bool, for hour: Hour) {
        if on { reminderOff.remove(hour.slug) } else { reminderOff.insert(hour.slug) }
    }

    func reminderMinutes(for hour: Hour) -> Int {
        reminderTimes[hour.slug] ?? Self.defaultMinutes(for: hour)
    }

    func setReminderMinutes(_ minutes: Int, for hour: Hour) {
        reminderTimes[hour.slug] = max(0, min(minutes, 24 * 60 - 1))
    }

    /// When to remind, for an office the reader has not set a time for.
    ///
    /// Deliberately not `hour.from`, which is when the office's *window*
    /// opens, not when anyone wants to be told about it: Morning Prayer's
    /// window opens at four in the morning, and Compline's at nine at night.
    /// Reminders fired at the window's edge, so Morning Prayer was waking
    /// people at 4am. These are civil hours inside each window instead.
    /// nonisolated: this is arithmetic on an Hour and touches no state, and
    /// the scheduler needs it from outside the main actor. Settings being
    /// @MainActor would otherwise make even a pure function unreachable there.
    nonisolated static func defaultMinutes(for hour: Hour) -> Int {
        switch hour.slug {
        case "pb-morning":       return 7 * 60            // 07:00
        case "pb-noon":          return 12 * 60           // 12:00
        case "pb-evening":       return 18 * 60           // 18:00
        case "western-compline": return 21 * 60 + 30      // 21:30
        default:
            // An office this build does not know about: the window's start,
            // but never before seven.
            return max(hour.from, 7) * 60
        }
    }

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

    /// What the app applies, as a range, always.
    ///
    /// Expressed as a range so the *same* modifier can be attached whatever
    /// the setting is. The obvious shape — attach `.dynamicTypeSize(size)`
    /// when unlinked and nothing when following — changes the view's type
    /// when the toggle flips, and SwiftUI then rebuilds everything beneath it:
    /// the navigation stack is torn down and the reader is thrown out of
    /// Settings back to the root. Clamping to a single value pins the size;
    /// clamping to the whole range is a no-op that leaves iOS in charge.
    var textSizeRange: ClosedRange<DynamicTypeSize> {
        followSystemTextSize ? .xSmall ... .accessibility5 : textSize ... textSize
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
        static let followAppearance = "followSystemAppearance"
        static let lightTheme = "lightTheme"
        static let darkTheme = "darkTheme"
        static let phosphor = "terminalPhosphor"
        static let dyslexic = "dyslexicFont"
        static let reminders = "hourReminders"
        static let lastRead = "lastRead"
        static let followTextSize = "followSystemTextSize"
        static let textSize = "textSize"
        static let reminderTimes = "reminderTimes"
        static let reminderOff = "reminderOff"
        static let pane = "pane"
        static let iconGround = "iconGround"
        static let iconStyle = "iconStyle"
        static let iconMark = "iconMark"
        /// The pre-three-axis key, read once on upgrade. See `init`.
        static let iconColour = "iconColour"
    }

    /// The stored ground and mark, carrying forward a choice made before the
    /// two were separable.
    ///
    /// The old setting named a pairing — "Crimson on black", "Manuscript" —
    /// so splitting it cannot be exact: five of the old inks (crimson, amber,
    /// silver, sapphire, violet) are not among the four marks, and the nearest
    /// of those four is what they get. The alternative was to drop the
    /// preference on upgrade and move someone's home-screen icon without
    /// asking, which is worse than moving it a shade.
    private static func storedIcon(_ store: UserDefaults) -> (IconGround, IconMark) {
        if let raw = store.string(forKey: Key.iconGround),
           let ground = IconGround(rawValue: raw) {
            let mark = IconMark(rawValue: store.string(forKey: Key.iconMark) ?? "") ?? .gold
            return (ground, mark)
        }
        switch store.string(forKey: Key.iconColour) {
        case "sanctuary":   return (.black, .gold)
        case "paper":       return (.paper, .black)
        case "manuscript":  return (.vellum, .gold)
        case "terminal":    return (.black, .phosphor)
        case "ivory":       return (.black, .ivory)
        // the inks that no longer exist: all of them were on black
        case "crimson", "amber", "silver", "sapphire", "violet":
            return (.black, .gold)
        case "aurora":      return (.aurora, .ivory)
        case "nebula":      return (.nebula, .ivory)
        case "vespers":     return (.vespers, .ivory)
        case "sunrise":     return (.sunrise, .black)
        default:            return (.automatic, .gold)
        }
    }

    private init() {
        theme = Theme(rawValue: store.string(forKey: Key.theme) ?? "") ?? .sanctuary
        // default on, and absence of the key is not false here
        followSystemAppearance = store.object(forKey: Key.followAppearance) == nil
            ? true
            : store.bool(forKey: Key.followAppearance)
        lightTheme = Theme(rawValue: store.string(forKey: Key.lightTheme) ?? "") ?? .paper
        darkTheme = Theme(rawValue: store.string(forKey: Key.darkTheme) ?? "") ?? .sanctuary
        terminalPhosphor = Theme.Phosphor(rawValue: store.string(forKey: Key.phosphor) ?? "") ?? .green
        dyslexicFont = store.bool(forKey: Key.dyslexic)
        hourReminders = store.bool(forKey: Key.reminders)
        lastRead = store.string(forKey: Key.lastRead) ?? ""
        reminderTimes = store.dictionary(forKey: Key.reminderTimes) as? [String: Int] ?? [:]
        reminderOff = Set(store.stringArray(forKey: Key.reminderOff) ?? [])
        pane = store.string(forKey: Key.pane) ?? "prayers"
        iconStyle = IconStyle(rawValue: store.string(forKey: Key.iconStyle) ?? "") ?? .mark
        let (g, m) = Self.storedIcon(store)
        iconGround = g
        iconMark = m
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
