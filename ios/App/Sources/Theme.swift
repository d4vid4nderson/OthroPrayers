import SwiftUI
import UIKit

/// The styles the prayer book comes in.
///
/// A theme is a palette plus the faces it defaults to. Nothing else varies —
/// the layout, the spacing and the restraint are the same in all of them,
/// which is why a prayer looks like the same prayer whichever you pick. The
/// faces are only a default now: see ReadingFace.
enum Theme: String, CaseIterable, Identifiable, Codable {
    case paper, manuscript, sanctuary, darkPaper, advent, terminal, adventTerminal

    var id: String { rawValue }

    var name: String {
        switch self {
        case .paper: "Paper"
        case .manuscript: "Manuscript"
        case .sanctuary: "Sanctuary"
        case .darkPaper: "Dark Paper"
        case .advent: "Advent"
        case .terminal: "Terminal"
        case .adventTerminal: "Advent Terminal"
        }
    }

    var detail: String {
        switch self {
        case .paper: "The printed booklet."
        case .manuscript: "Vellum, iron gall and an insular hand."
        case .sanctuary: "Dark, for early and late."
        case .darkPaper: "The printed booklet, after dark."
        case .advent: "Evergreen and red, for the weeks of waiting."
        case .terminal: "A green-phosphor console."
        case .adventTerminal: "The console, keeping Advent."
        }
    }

    /// Dark themes get a dark interface; the system handles the rest.
    var colorScheme: ColorScheme {
        switch self {
        case .paper, .manuscript: .light
        case .sanctuary, .darkPaper, .advent, .terminal, .adventTerminal: .dark
        }
    }

    /// Set like a console: one colour on black, in a monospaced face, with
    /// the directions marked rather than ornamented. Two themes do it, so it
    /// is asked as a question rather than compared against one of them.
    var isConsole: Bool { self == .terminal || self == .adventTerminal }

    /// Which phosphor the Terminal theme glows in.
    ///
    /// A real terminal is one colour on black, and which colour was a property
    /// of the tube — P1 green, P3 amber — or, later, of the scheme someone
    /// chose. So it is a choice here too rather than one hardcoded green.
    enum Phosphor: String, CaseIterable, Identifiable {
        case green, teal, cyan, amber
        var id: String { rawValue }

        var name: String {
            switch self {
            case .green: return "Green"
            case .teal:  return "Teal"
            case .cyan:  return "Cyan"
            case .amber: return "Amber"
            }
        }

        var ink: Color {
            switch self {
            case .green: .hex(0x9BE89B)
            case .teal:  .hex(0x5EE6D0)
            case .cyan:  .hex(0x6BD5F5)
            case .amber: .hex(0xFFC777)
            }
        }

        var inkSoft: Color {
            switch self {
            case .green: .hex(0x6FAE78)
            case .teal:  .hex(0x46A89A)
            case .cyan:  .hex(0x4C9DB8)
            case .amber: .hex(0xC2975A)
            }
        }

        var inkFaint: Color {
            switch self {
            case .green: .hex(0x4E8A5A)
            case .teal:  .hex(0x357F75)
            case .cyan:  .hex(0x3A788C)
            case .amber: .hex(0x8F6F43)
            }
        }

        /// The second phosphor, for whatever the printed book set in red.
        /// Amber against the cool ones, green against amber itself.
        var accent: Color {
            self == .amber ? .hex(0x9BE89B) : .hex(0xFFB454)
        }
    }

    /// The palette, with the Terminal theme's phosphor supplied.
    func palette(phosphor: Phosphor) -> Palette {
        guard case .terminal = self else { return palette }
        return Palette(ground: .hex(0x070A07), surface: .hex(0x0C120C),
                       ink: phosphor.ink, inkSoft: phosphor.inkSoft,
                       inkFaint: phosphor.inkFaint,
                       accent: phosphor.accent, onAccent: .hex(0x070A07),
                       hairline: phosphor.ink.opacity(0.16))
    }

    var palette: Palette {
        switch self {
        case .paper:
            Palette(ground: .hex(0xFAF6EE), surface: .hex(0xFFFDF8),
                    ink: .hex(0x231F20), inkSoft: .hex(0x6B6560), inkFaint: .hex(0x9A938C),
                    accent: .hex(0xB3322A), onAccent: .white, hairline: .hex(0x231F20, 0.12))
        case .manuscript:
            Palette(ground: .hex(0xF0E4C8), surface: .hex(0xF6ECD6),
                    ink: .hex(0x2F2418), inkSoft: .hex(0x6A5A44), inkFaint: .hex(0x9A866A),
                    accent: .hex(0xA32A1E), onAccent: .hex(0xF0E4C8), hairline: .hex(0x2F2418, 0.16))
        case .sanctuary:
            Palette(ground: .hex(0x0C0D10), surface: .hex(0x15171C),
                    ink: .hex(0xECEAE6), inkSoft: .hex(0x9AA0AB), inkFaint: .hex(0x646B77),
                    accent: .hex(0xD9B36C), onAccent: .hex(0x1A1508), hairline: .hex(0xECEAE6, 0.09))
        case .darkPaper:
            // Paper turned down, not Sanctuary in another colour: the same
            // warm off-white and the same cinnabar, on a brown-black rather
            // than Sanctuary's blue-black. The accent is lifted from Paper's
            // 0xB3322A, which is a red meant to sit on cream and goes muddy
            // against a dark ground.
            Palette(ground: .hex(0x14120E), surface: .hex(0x1E1B16),
                    ink: .hex(0xEDE7DB), inkSoft: .hex(0xA69E90), inkFaint: .hex(0x756D61),
                    accent: .hex(0xD4675C), onAccent: .hex(0x14120E),
                    hairline: .hex(0xEDE7DB, 0.12))
        case .advent:
            // Evergreen and red, with the green in the prose rather than only
            // under it: the ink was a green-tinted white, which read as white.
            // This is a sage that is plainly green and still holds 7:1 against
            // the ground, so a long reading is no harder for it.
            //
            // The red was lifted from 0xD2413A, which measured 4.2:1 — under
            // the 4.5 that small text wants, and the accent is what the
            // citations and the directions are set in.
            Palette(ground: .hex(0x0B130D), surface: .hex(0x121C14),
                    ink: .hex(0xAED3A6), inkSoft: .hex(0x7FA47B), inkFaint: .hex(0x6B8F66),
                    accent: .hex(0xDE5048), onAccent: .hex(0x0B130D),
                    hairline: .hex(0xAED3A6, 0.12))
        case .adventTerminal:
            // The same two colours as a console wears them: green phosphor
            // for the body, red for the second phosphor. Terminal's own amber
            // is the wrong red for Advent, which is why this is a theme and
            // not another phosphor.
            Palette(ground: .hex(0x050A06), surface: .hex(0x0A120B),
                    ink: .hex(0x8FE08F), inkSoft: .hex(0x63A869), inkFaint: .hex(0x447A4B),
                    accent: .hex(0xFF5F52), onAccent: .hex(0x050A06),
                    hairline: .hex(0x8FE08F, 0.16))
        case .terminal:
            // two phosphors: green for the body, amber for whatever the printed
            // book set in red
            Palette(ground: .hex(0x070A07), surface: .hex(0x0C120C),
                    ink: .hex(0x9BE89B), inkSoft: .hex(0x6FAE78), inkFaint: .hex(0x4E8A5A),
                    accent: .hex(0xFFB454), onAccent: .hex(0x070A07), hairline: .hex(0x9BE89B, 0.16))
        }
    }

    /// The face for prayer text. Terminal is the only one that is not a serif —
    /// a console has exactly one kind of letter.
    func bodyFont(_ style: Font.TextStyle, face: ReadingFace) -> Font {
        if let chosen = face.font(style) { return chosen }
        if isConsole, let name = BundledFont.jetBrainsMono {
            return .custom(name, size: style.pointSize * 0.94, relativeTo: style)
        }
        return .system(style, design: .serif)
    }

    /// The face for titles.
    func displayFont(_ style: Font.TextStyle, face: ReadingFace) -> Font {
        // A chosen face is chosen everywhere. Leaving titles in the theme's
        // own letter would mean a reader who picked a face because the serif
        // was hard going still met it at the top of every office.
        if let chosen = face.font(style) { return chosen.weight(.semibold) }
        switch self {
        case .terminal, .adventTerminal:
            if let name = BundledFont.jetBrainsMono {
                return .custom(name, size: style.pointSize * 0.9, relativeTo: style).weight(.bold)
            }
            return .system(style, design: .monospaced).weight(.bold)
        case .manuscript:
            if let name = BundledFont.uncialAntiqua {
                return .custom(name, size: style.pointSize * 0.92, relativeTo: style)
            }
            return .system(style, design: .serif).weight(.semibold)
        case .paper, .sanctuary, .darkPaper, .advent:
            return .system(style, design: .serif).weight(.semibold)
        }
    }

    /// The face for interface labels.
    func uiFont(_ style: Font.TextStyle, face: ReadingFace) -> Font {
        if let chosen = face.font(style) { return chosen.weight(.semibold) }
        if isConsole, let name = BundledFont.jetBrainsMono {
            return .custom(name, size: style.pointSize * 0.94, relativeTo: style)
        }
        return .system(style, design: .default).weight(.semibold)
    }

    /// The sigil a terminal puts before a title, a heading or a rubric. The
    /// other three say the same thing with ornament and colour.
    func sigil(for kind: Block.Kind) -> String {
        guard isConsole else { return "" }
        switch kind {
        case .heading, .subheading: return "## "
        case .rubric: return "# "
        default: return ""
        }
    }
}

/// Equatable so SwiftUI can tell when the environment's Design actually
/// changed, rather than invalidating every dependent view on each pass.
struct Palette: Equatable {
    let ground: Color
    let surface: Color
    let ink: Color
    let inkSoft: Color
    let inkFaint: Color
    let accent: Color
    let onAccent: Color
    let hairline: Color
}

extension Color {
    static func hex(_ value: UInt32, _ opacity: Double = 1) -> Color {
        Color(.sRGB,
              red: Double((value >> 16) & 0xFF) / 255,
              green: Double((value >> 8) & 0xFF) / 255,
              blue: Double(value & 0xFF) / 255,
              opacity: opacity)
    }
}

/// Faces bundled with the app, looked up by family name once. iOS cannot load
/// the woff2 files the website uses, so these are converted to TTF at build
/// time (see export in the repo's font pipeline).
/// The letter the book is set in, chosen apart from the theme.
///
/// It used to be a single "dyslexia-friendly text" switch, which answered one
/// reader's difficulty and nobody else's. A theme's palette and its face are
/// separate preferences — liking Sanctuary's dark gold is no reason to be
/// held to a serif at body size on a dark ground, which is a genuinely hard
/// read — so the face is now its own choice and `.theme` keeps whatever the
/// theme would have picked.
enum ReadingFace: String, CaseIterable, Identifiable, Codable {
    case theme, serif, sans, rounded, mono, dyslexic

    var id: String { rawValue }

    var name: String {
        switch self {
        case .theme:    "Match the style"
        case .serif:    "Serif"
        case .sans:     "Sans"
        case .rounded:  "Rounded"
        case .mono:     "Monospaced"
        case .dyslexic: "Dyslexia-friendly"
        }
    }

    var detail: String {
        switch self {
        case .theme:    "Each style's own letter."
        case .serif:    "The printed book's letter."
        case .sans:     "Plainest, and the easiest at small sizes."
        case .rounded:  "Softer, with open shapes."
        case .mono:     "Every letter the same width."
        case .dyslexic: "Weighted feet, to hold the line steady."
        }
    }

    /// The font this face asks for, or nil to leave it to the theme.
    func font(_ style: Font.TextStyle) -> Font? {
        switch self {
        case .theme:
            return nil
        case .serif:
            return .system(style, design: .serif)
        case .sans:
            return .system(style, design: .default)
        case .rounded:
            return .system(style, design: .rounded)
        case .mono:
            // the bundled face if it is there, the system's if it is not
            if let name = BundledFont.jetBrainsMono {
                return .custom(name, size: style.pointSize * 0.94, relativeTo: style)
            }
            return .system(style, design: .monospaced)
        case .dyslexic:
            if let name = BundledFont.openDyslexic {
                return .custom(name, size: style.pointSize, relativeTo: style)
            }
            // Nothing is gained by pretending: without the bundled face this
            // is just the plainest system one.
            return .system(style, design: .default)
        }
    }
}

extension ReadingFace {
    /// The same choice, as a UIKit font.
    ///
    /// TextKit needs one, and the illuminated capitals are laid out there —
    /// SwiftUI's Text cannot flow around a shape, and a text container can.
    /// `sized` is the point size already scaled for the reader's text size;
    /// scaling is done by the caller because the app clamps Dynamic Type
    /// itself and UIKit would otherwise read the system's instead.
    func uiKitFont(sized size: CGFloat) -> UIFont? {
        switch self {
        case .theme:
            return nil
        case .serif:
            return .systemFont(ofSize: size).withDesign(.serif)
        case .sans:
            return .systemFont(ofSize: size)
        case .rounded:
            return .systemFont(ofSize: size).withDesign(.rounded)
        case .mono:
            if let name = BundledFont.jetBrainsMono {
                return UIFont(name: name, size: size * 0.94)
            }
            return .monospacedSystemFont(ofSize: size, weight: .regular)
        case .dyslexic:
            if let name = BundledFont.openDyslexic {
                return UIFont(name: name, size: size)
            }
            return .systemFont(ofSize: size)
        }
    }
}

extension UIFont {
    /// The same face in another design, or this one where that is unavailable.
    func withDesign(_ design: UIFontDescriptor.SystemDesign) -> UIFont {
        guard let d = fontDescriptor.withDesign(design) else { return self }
        return UIFont(descriptor: d, size: pointSize)
    }
}

extension Theme {
    /// The prayer face as a UIKit font, for paragraphs TextKit lays out.
    /// Named apart from `uiFont` above, which is the interface face.
    func bodyUIKitFont(sized size: CGFloat, face: ReadingFace) -> UIFont {
        if let chosen = face.uiKitFont(sized: size) { return chosen }
        if isConsole, let name = BundledFont.jetBrainsMono,
           let f = UIFont(name: name, size: size * 0.94) {
            return f
        }
        return UIFont.systemFont(ofSize: size).withDesign(.serif)
    }
}

enum BundledFont {
    static let openDyslexic = family(containing: "dyslexic")
    static let jetBrainsMono = family(containing: "jetbrains")
    static let uncialAntiqua = family(containing: "uncial")

    private static func family(containing needle: String) -> String? {
        UIFont.familyNames.first { $0.localizedCaseInsensitiveContains(needle) }
    }
}

extension Font.TextStyle {
    /// The reader's own size for this style, so custom faces scale with
    /// Dynamic Type exactly as the system ones do.
    var pointSize: CGFloat { UIFont.preferredFont(forTextStyle: uiStyle).pointSize }
}
