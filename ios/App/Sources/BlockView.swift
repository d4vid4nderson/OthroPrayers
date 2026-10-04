import SwiftUI

/// Renders one block of the content model.
///
/// The rule the design runs on: navigation may use the app idiom, but a page of
/// prayer gets type, white space and one hairline. So there are no cards here,
/// no icons, no tinted containers — only text, set well.
struct BlockView: View {
    let block: Block
    /// Tapping a cross-reference opens that page.
    var onLink: (String) -> Void = { _ in }

    var body: some View {
        switch block.type {
        case .heading:
            VStack(spacing: 10) {
                MicroLabel(text: block.plain)
                    .multilineTextAlignment(.center)
                Rectangle()
                    .fill(.quaternary)
                    .frame(width: 16, height: 1)
            }
            .frame(maxWidth: .infinity)
            .padding(.top, 26)
            .padding(.bottom, 12)

        case .subheading:
            Text(attributed)
                .font(Typeface.display(.title3))
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.top, 14)

        case .rubric:
            // the direction, not the prayer: italic, centred, stepped back
            Text(attributed)
                .font(Typeface.prayer(.callout).italic())
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 10)

        case .lead:
            Text(attributed)
                .font(Typeface.prayer(.callout).italic())
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .frame(maxWidth: .infinity)
                .padding(.bottom, 8)

        case .verse where block.isHymn:
            // a hymn's line breaks are its verse form — set each on its own
            // line, flush left, which is far easier to follow than justified
            VStack(alignment: .leading, spacing: 2) {
                ForEach(Array(hymnLines.enumerated()), id: \.offset) { _, line in
                    Text(line).font(Typeface.prayer())
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.vertical, 8)

        case .verse, .paragraph, .item:
            Text(attributed)
                .font(Typeface.prayer())
                .lineSpacing(5)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.vertical, 6)

        case .term:
            Text(attributed)
                .font(Typeface.prayer(.callout))
                .frame(maxWidth: .infinity, alignment: .leading)

        case .definition:
            Text(attributed)
                .font(Typeface.label(.caption))
                .foregroundStyle(Color.sanctuaryGold)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.bottom, 8)
        }
    }

    private var hymnLines: [String] {
        block.runs.flatMap(\.lines).filter { !$0.trimmingCharacters(in: .whitespaces).isEmpty }
    }

    /// Inline marks, assembled into one attributed string so the text still
    /// wraps, selects and reads aloud as a single passage.
    private var attributed: AttributedString {
        var out = AttributedString()
        for run in block.runs {
            var piece = AttributedString(run.t.replacingOccurrences(of: "\n", with: " "))
            switch run.mark {
            case .rubric:
                piece.foregroundColor = .secondary
            case .signum:
                piece.foregroundColor = .sanctuaryGold
            case .dropcap, .versal:
                piece.foregroundColor = .sanctuaryGold
                piece.font = Typeface.display(.title)
            case .italic:
                piece.font = Typeface.prayer().italic()
            case .strong:
                piece.font = Typeface.prayer().weight(.semibold)
            case .smallcaps:
                piece.font = Typeface.prayer(.callout)
            case .sup, .small:
                piece.font = Typeface.prayer(.caption)
            case .none:
                break
            }
            if let href = run.href {
                piece.foregroundColor = .sanctuaryGold
                piece.underlineStyle = .single
                piece.link = URL(string: "prayers://page/\(href)")
            }
            out.append(piece)
        }
        return out
    }
}
