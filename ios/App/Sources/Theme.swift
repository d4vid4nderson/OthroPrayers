import SwiftUI

/// The four styles the prayer book comes in, matching the website exactly.
///
/// A theme is a palette plus a pair of faces: one for anything read at length,
/// one for the interface. Nothing else varies — the layout, the spacing and the
/// restraint are the same in all four, which is why a prayer looks like the
/// same prayer whichever you pick.
enum Theme: String, CaseIterable, Identifiable, Codable {
    case paper, manuscript, sanctuary, terminal

    var id: String { rawValue }

    var name: String {
        switch self {
        case .paper: "Paper"
        case .manuscript: "Manuscript"
        case .sanctuary: "Sanctuary"
        case .terminal: "Terminal"
        }
    }

    var detail: String {
        switch self {
        case .paper: "The printed booklet."
        case .manuscript: "Vellum, iron gall and an insular hand."
        case .sanctuary: "Dark, for early and late."
        case .terminal: "A green-phosphor console."
        }
    }

    /// Dark themes get a dark interface; the system handles the rest.
    var colorScheme: ColorScheme {
        switch self {
        case .paper, .manuscript: .light
        case .sanctuary, .terminal: .dark
        }
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
    func bodyFont(_ style: Font.TextStyle, dyslexic: Bool) -> Font {
        if dyslexic, let name = BundledFont.openDyslexic {
            return .custom(name, size: style.pointSize, relativeTo: style)
        }
        if self == .terminal, let name = BundledFont.jetBrainsMono {
            return .custom(name, size: style.pointSize * 0.94, relativeTo: style)
        }
        return .system(style, design: .serif)
    }

    /// The face for titles.
    func displayFont(_ style: Font.TextStyle, dyslexic: Bool) -> Font {
        if dyslexic, let name = BundledFont.openDyslexic {
            return .custom(name, size: style.pointSize, relativeTo: style)
        }
        switch self {
        case .terminal:
            if let name = BundledFont.jetBrainsMono {
                return .custom(name, size: style.pointSize * 0.9, relativeTo: style).weight(.bold)
            }
            return .system(style, design: .monospaced).weight(.bold)
        case .manuscript:
            if let name = BundledFont.uncialAntiqua {
                return .custom(name, size: style.pointSize * 0.92, relativeTo: style)
            }
            return .system(style, design: .serif).weight(.semibold)
        case .paper, .sanctuary:
            return .system(style, design: .serif).weight(.semibold)
        }
    }

    /// The face for interface labels.
    func uiFont(_ style: Font.TextStyle, dyslexic: Bool) -> Font {
        if dyslexic, let name = BundledFont.openDyslexic {
            return .custom(name, size: style.pointSize, relativeTo: style)
        }
        if self == .terminal, let name = BundledFont.jetBrainsMono {
            return .custom(name, size: style.pointSize * 0.94, relativeTo: style)
        }
        return .system(style, design: .default).weight(.semibold)
    }

    /// The sigil a terminal puts before a title, a heading or a rubric. The
    /// other three say the same thing with ornament and colour.
    func sigil(for kind: Block.Kind) -> String {
        guard self == .terminal else { return "" }
        switch kind {
        case .heading, .subheading: return "## "
        case .rubric: return "# "
        default: return ""
        }
    }
}

struct Palette {
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
