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
var palette: Palette {
    Settings.shared.effectiveTheme.palette(phosphor: Settings.shared.terminalPhosphor)
}

@MainActor
enum Typeface {
    private static var theme: Theme { Settings.shared.effectiveTheme }
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

/// The app's container corner: a squircle, not a rounded square.
///
/// `RoundedRectangle` defaults to `.circular`, which butts a straight edge
/// against a circular arc. The curvature jumps at that join — from nothing to
/// all of it at once — and that discontinuity is exactly what the eye reads as
/// a rounded square. `.continuous` ramps the curvature in over a longer
/// stretch of the edge, which is the curve iOS itself uses for app icons,
/// sheets, widgets and alerts.
///
/// Defined once, here, because the cards had it one way and the icon picker
/// the other, and the two sat on the same screen.
enum Container {
    /// A card: an office, a chant, a section of the Today page.
    static let radius: CGFloat = 20
    /// Something sitting inside a card, which wants a tighter corner.
    static let innerRadius: CGFloat = 12

    static func shape(_ radius: CGFloat = Self.radius) -> RoundedRectangle {
        RoundedRectangle(cornerRadius: radius, style: .continuous)
    }

    /// A well or badge inside a card.
    static func inner() -> RoundedRectangle { shape(innerRadius) }

    /// The same curve at an app icon's proportion.
    ///
    /// iOS masks a home-screen icon at about 22.4% of its side rather than a
    /// fixed radius, so the picker's tiles have to scale their corner with
    /// their size to look like what they are previewing.
    static func icon(side: CGFloat) -> RoundedRectangle {
        RoundedRectangle(cornerRadius: side * 0.2237, style: .continuous)
    }
}

/// A hairline in the theme's own colour.
///
/// SwiftUI's `Divider` draws the system separator, which knows about light and
/// dark but nothing about which theme is on — so on Terminal it was a grey
/// line through green text.
struct ThemedRule: View {
    var body: some View {
        Rectangle()
            .fill(palette.hairline)
            .frame(height: 1)
    }
}
