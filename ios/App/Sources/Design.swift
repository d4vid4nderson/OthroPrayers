import SwiftUI
import UIKit

// The design layer, driven by the chosen Theme.
//
// Stock SwiftUI components do the heavy lifting — TabView, NavigationStack,
// .toolbar, Form — so the system supplies Liquid Glass and gets the specular
// highlights, blur and motion right in ways a hand-rolled material cannot.
// What this file supplies is the palette, the type and the restraint.

/// How the app is drawn: the palette in force, and the inputs the typeface
/// depends on.
///
/// This used to be a free `palette` variable reading `Settings.shared`, on the
/// reasoning that Settings publishes on change so "any view observing it
/// re-renders with the new colours". The catch is in those three words.
/// Reading a global inside `body` creates no dependency: SwiftUI re-renders a
/// view when something the view *observes* changes, and a global is observed
/// by nobody. Views that happened to hold an `@EnvironmentObject settings`
/// repainted; views that only called `palette` were never invalidated and kept
/// whatever colours they were first drawn with. Changing the theme left a
/// black page carrying cream cards, with the headings in the new ink and
/// invisible against them.
///
/// Carrying it in the environment is what makes the dependency real, and it
/// does so without changing view identity — so the colours follow a theme
/// change while the navigation stack stays exactly where the reader left it.
///
/// `theme` and `dyslexic` are here even though `Typeface` reads them itself.
/// They are what makes this value differ when only the font changed, so the
/// views depending on it are invalidated and the static lookups below are
/// re-read. Without them, turning on the dyslexic face would repaint nothing.
struct Design: Equatable {
    var palette: Palette
    var theme: Theme
    var dyslexic: Bool

    @MainActor
    init(_ settings: Settings) {
        let theme = settings.effectiveTheme
        self.palette = theme.palette(phosphor: settings.terminalPhosphor)
        self.theme = theme
        self.dyslexic = settings.dyslexicFont
    }

    /// For the environment's default, which cannot reach a MainActor
    /// singleton from a static initialiser.
    fileprivate init(palette: Palette, theme: Theme, dyslexic: Bool) {
        self.palette = palette
        self.theme = theme
        self.dyslexic = dyslexic
    }
}

private struct DesignKey: EnvironmentKey {
    // Only ever seen by a view with no app above it, such as a preview.
    static let defaultValue = Design(palette: Theme.sanctuary.palette,
                                     theme: .sanctuary, dyslexic: false)
}

extension EnvironmentValues {
    var design: Design {
        get { self[DesignKey.self] }
        set { self[DesignKey.self] = newValue }
    }
}

/// Reads `Settings.shared` directly, which is correct *at the moment a view
/// renders*. What was missing was never the value — it was a reason for the
/// view to render again. `@Environment(\.design)` supplies that.
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
    /// Colours and type, from the environment so this view is
    /// invalidated when they change. See Design.
    @Environment(\.design) var design
    private var palette: Palette { design.palette }
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
    /// Colours and type, from the environment so this view is
    /// invalidated when they change. See Design.
    @Environment(\.design) var design
    private var palette: Palette { design.palette }
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
    /// Colours and type, from the environment so this view is
    /// invalidated when they change. See Design.
    @Environment(\.design) var design
    private var palette: Palette { design.palette }
    var body: some View {
        Rectangle()
            .fill(palette.hairline)
            .frame(height: 1)
    }
}
