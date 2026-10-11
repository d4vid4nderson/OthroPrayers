import SwiftUI
import UIKit

// The design layer, driven by the chosen Theme.
//
// Stock SwiftUI components do the heavy lifting — TabView, NavigationStack,
// .toolbar, Form — so the system supplies Liquid Glass and gets the specular
// highlights, blur and motion right in ways a hand-rolled material cannot.
// What this file supplies is the palette, the type and the restraint.

/// The palette in force. A free function rather than an environment value so
/// that leaf views need not all be rewritten to carry it; Settings is a
/// MainActor singleton and publishes on change, so any view observing it
/// re-renders with the new colours.
@MainActor
var palette: Palette { Settings.shared.theme.palette }

@MainActor
enum Typeface {
    private static var theme: Theme { Settings.shared.theme }
    private static var dyslexic: Bool { Settings.shared.dyslexicFont }

    /// Anything read at length.
    static func prayer(_ style: Font.TextStyle = .body) -> Font {
        theme.bodyFont(style, dyslexic: dyslexic)
    }

    /// Titles.
    static func display(_ style: Font.TextStyle = .largeTitle) -> Font {
        theme.displayFont(style, dyslexic: dyslexic)
    }

    /// Interface labels — "On rising", "The Lord's Prayer".
    static func label(_ style: Font.TextStyle = .caption) -> Font {
        theme.uiFont(style, dyslexic: dyslexic)
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

/// A label in the app's quiet voice: wide tracking, small, secondary.
struct MicroLabel: View {
    let text: String
    var body: some View {
        Text(text.uppercased())
            .font(Typeface.label(.caption2))
            .tracking(1.6)
            .foregroundStyle(palette.inkFaint)
    }
}

/// The short accent rule under a page title, doing the work the printed
/// ornament used to.
struct AccentRule: View {
    var width: CGFloat = 28
    var body: some View {
        Capsule()
            .fill(palette.accent)
            .frame(width: width, height: 1.5)
            .accessibilityHidden(true)
    }
}
