import SwiftUI

// Sanctuary, natively.
//
// The deliberate choice here is to use stock SwiftUI components — TabView,
// NavigationStack, .toolbar, Form — rather than hand-painting surfaces. On
// iOS 26 and later the system gives those components Liquid Glass for free,
// and gets the specular highlights, blur and motion right in ways a hand-rolled
// material cannot. What the app supplies is the palette, the type and the
// restraint; the material is Apple's.

extension Color {
    /// The single warm light source. Everything else on screen recedes behind it.
    static let sanctuaryGold = Color(red: 0xD9 / 255, green: 0xB3 / 255, blue: 0x6C / 255)
    /// Ink on a gold fill.
    static let onGold = Color(red: 0x1A / 255, green: 0x15 / 255, blue: 0x08 / 255)
    /// The ground. Darker than the system's dark background on purpose: this is
    /// an app for before light and after it.
    static let sanctuaryGround = Color(red: 0x0C / 255, green: 0x0D / 255, blue: 0x10 / 255)
    static let sanctuarySurface = Color(red: 0x15 / 255, green: 0x17 / 255, blue: 0x1C / 255)
}

/// How prayer text is set. Serif for anything you read at length — New York,
/// which carries Dynamic Type properly — and the system face for UI.
///
/// Every size below is a *semantic* text style, never a point size, so the
/// whole app follows the reader's Dynamic Type setting. That is the real
/// accessibility win over the web version, where the text size control was a
/// bespoke three-step thing that nothing else on the phone knew about.
enum Typeface {
    static func prayer(_ style: Font.TextStyle = .body) -> Font {
        if Settings.shared.dyslexicFont, let name = OpenDyslexic.familyName {
            return .custom(name, size: UIFont.preferredFont(forTextStyle: style.uiStyle).pointSize,
                           relativeTo: style)
        }
        return .system(style, design: .serif)
    }

    static func display(_ style: Font.TextStyle = .largeTitle) -> Font {
        if Settings.shared.dyslexicFont, let name = OpenDyslexic.familyName {
            return .custom(name, size: UIFont.preferredFont(forTextStyle: style.uiStyle).pointSize,
                           relativeTo: style)
        }
        return .system(style, design: .serif).weight(.semibold)
    }

    /// Small caps labels — "On rising", "The Lord's Prayer".
    static func label(_ style: Font.TextStyle = .caption) -> Font {
        .system(style, design: .default).weight(.semibold)
    }
}

extension Font.TextStyle {
    var uiStyle: UIFont.TextStyle {
        switch self {
        case .largeTitle: .largeTitle
        case .title: .title1
        case .title2: .title2
        case .title3: .title3
        case .headline: .headline
        case .subheadline: .subheadline
        case .callout: .callout
        case .footnote: .footnote
        case .caption: .caption1
        case .caption2: .caption2
        default: .body
        }
    }
}

/// OpenDyslexic is bundled rather than relied upon: iOS has no system
/// equivalent, and the reader this app was built for needs it.
enum OpenDyslexic {
    static let familyName: String? = {
        UIFont.familyNames.first { $0.localizedCaseInsensitiveContains("dyslexic") }
    }()
}

/// A label set in small caps with wide tracking — the app's quiet voice.
struct MicroLabel: View {
    let text: String
    var body: some View {
        Text(text.uppercased())
            .font(Typeface.label(.caption2))
            .tracking(1.6)
            .foregroundStyle(.secondary)
    }
}

/// The short gold rule that sits under a page title and does the work the
/// printed ornament used to.
struct GoldRule: View {
    var width: CGFloat = 28
    var body: some View {
        Capsule()
            .fill(Color.sanctuaryGold)
            .frame(width: width, height: 1.5)
            .accessibilityHidden(true)
    }
}
