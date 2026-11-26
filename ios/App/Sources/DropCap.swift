import SwiftUI
import UIKit

/// A paragraph that opens with an illuminated capital, set as the booklet
/// sets it: the ornament stands where the first letter would, and the opening
/// lines are laid around it.
///
/// SwiftUI's `Text` cannot flow around a shape — there is no exclusion in its
/// layout — so this drops to TextKit, where a text container takes exclusion
/// paths and does exactly this. That is the whole reason for the detour into
/// UIKit; everything else here exists to keep the detour from showing.
///
/// The ornament is an alpha mask filled with the theme's accent, the same as
/// everywhere else, and the first letter has already left the text upstream:
/// the image carries it, and its alt text carries it for anyone who cannot
/// see the image.
struct DropCapParagraph: View {
    let text: String
    let art: String
    let label: String

    @Environment(\.design) var design
    @Environment(\.dynamicTypeSize) private var typeSize

    /// How many lines of text the capital stands beside. Three is the
    /// printer's usual, and it is what the booklet uses.
    private let lines: CGFloat = 3

    var body: some View {
        let size = Typeface.prayerPointSize(typeSize)
        let font = design.theme.bodyUIKitFont(sized: size, face: design.face)
        // The ornament is square, and its side is the height of the lines it
        // stands beside — the leading, not the point size, or it sits short.
        let side = (font.lineHeight * lines).rounded()
        DropCapText(text: text,
                    font: font,
                    colour: UIColor(design.palette.ink),
                    capSide: side,
                    capGap: size * 0.45)
            .overlay(alignment: .topLeading) {
                if let image = UIImage(named: art) {
                    Image(uiImage: image)
                        .renderingMode(.template)
                        .resizable()
                        .frame(width: side, height: side)
                        .foregroundStyle(design.palette.accent)
                        .accessibilityHidden(true)
                }
            }
            .accessibilityElement()
            .accessibilityLabel("\(label). \(text)")
            .padding(.vertical, 6)
    }
}

/// The text alone, with a hole cut for the capital.
private struct DropCapText: UIViewRepresentable {
    let text: String
    let font: UIFont
    let colour: UIColor
    let capSide: CGFloat
    let capGap: CGFloat

    func makeUIView(context: Context) -> UITextView {
        let v = UITextView()
        // A text view that does not scroll, select or inset is a paragraph.
        v.isScrollEnabled = false
        v.isEditable = false
        v.isSelectable = false
        v.backgroundColor = .clear
        v.textContainerInset = .zero
        v.textContainer.lineFragmentPadding = 0
        v.setContentCompressionResistancePriority(.required, for: .vertical)
        return v
    }

    func updateUIView(_ v: UITextView, context: Context) {
        let style = NSMutableParagraphStyle()
        // Matched to the ordinary paragraphs in BlockView rather than to the
        // printed page: the booklet justifies, the app sets ragged right, and
        // one justified paragraph among its neighbours reads as a mistake.
        style.alignment = .natural
        style.lineSpacing = 5
        v.attributedText = NSAttributedString(string: text, attributes: [
            .font: font, .foregroundColor: colour, .paragraphStyle: style,
        ])
        // The capital's square, plus the gap the text keeps from it.
        v.textContainer.exclusionPaths = [
            UIBezierPath(rect: CGRect(x: 0, y: 0,
                                      width: capSide + capGap, height: capSide)),
        ]
    }

    func sizeThatFits(_ proposal: ProposedViewSize,
                      uiView: UITextView,
                      context: Context) -> CGSize? {
        guard let width = proposal.width, width > 0 else { return nil }
        let fitted = uiView.sizeThatFits(
            CGSize(width: width, height: .greatestFiniteMagnitude))
        // Never shorter than the capital, or a short paragraph would clip it.
        return CGSize(width: width, height: max(fitted.height, capSide))
    }
}

extension Typeface {
    /// The prayer's point size at the reader's text size.
    ///
    /// Read from SwiftUI's environment rather than from UIKit, because the
    /// app clamps Dynamic Type itself (see Settings.textSizeRange) and UIKit
    /// would otherwise lay this one paragraph out at the system's size while
    /// every other paragraph used the app's.
    @MainActor
    static func prayerPointSize(_ size: DynamicTypeSize) -> CGFloat {
        let base = UIFont.preferredFont(
            forTextStyle: .body,
            compatibleWith: UITraitCollection(
                preferredContentSizeCategory: size.contentSizeCategory))
        return base.pointSize
    }
}

extension DynamicTypeSize {
    var contentSizeCategory: UIContentSizeCategory {
        switch self {
        case .xSmall: .extraSmall
        case .small: .small
        case .medium: .medium
        case .large: .large
        case .xLarge: .extraLarge
        case .xxLarge: .extraExtraLarge
        case .xxxLarge: .extraExtraExtraLarge
        case .accessibility1: .accessibilityMedium
        case .accessibility2: .accessibilityLarge
        case .accessibility3: .accessibilityExtraLarge
        case .accessibility4: .accessibilityExtraExtraLarge
        case .accessibility5: .accessibilityExtraExtraExtraLarge
        @unknown default: .large
        }
    }
}
