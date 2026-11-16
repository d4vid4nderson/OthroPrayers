import SwiftUI

/// Renders one block of the content model.
///
/// The rule the design runs on: navigation may use the app idiom, but a page of
/// prayer gets type, white space and one hairline. So there are no cards here,
/// no icons, no tinted containers — only text, set well.
struct BlockView: View {
    let block: Block
    @EnvironmentObject private var settings: Settings
    /// Tapping a cross-reference opens that page.
    var onLink: (String) -> Void = { _ in }

    var body: some View {
        switch block.type {
        case .heading:
            VStack(spacing: 10) {
                MicroLabel(text: settings.theme.sigil(for: block.type) + block.plain)
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
            // the direction, not the prayer. A console sets it as a comment,
            // flush left in the second phosphor; the other three italicise and
            // centre it, as the printed book does.
            Text(AttributedString(settings.theme.sigil(for: .rubric)) + attributed)
                .font(settings.theme == .terminal
                      ? Typeface.prayer(.callout)
                      : Typeface.prayer(.callout).italic())
                .foregroundStyle(settings.theme == .terminal ? palette.accent : palette.inkSoft)
                .multilineTextAlignment(settings.theme == .terminal ? .leading : .center)
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

        // The versicle: the celebrant's line, set like a direction rather than
        // like the prayer, so the reader can see at a glance which words are
        // theirs to say. The web build said it this way too — "the celebrant's
        // prompt, set like a rubric direction; the people's words in ink".
        case .cue:
            Text(attributed)
                .font(Typeface.prayer(.callout).italic())
                .foregroundStyle(palette.inkSoft)
                .lineSpacing(3)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.top, 8)

        // The response: the people's words, in full ink directly beneath.
        case .response:
            Text(attributed)
                .font(Typeface.prayer())
                .lineSpacing(5)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.bottom, 8)

        case .terms:
            Text(attributed)
                .font(Typeface.display(.callout))
                .foregroundStyle(palette.accent)
                .multilineTextAlignment(.center)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 6)

        case .opening:
            Text(attributed)
                .font(Typeface.prayer(.title3))
                .lineSpacing(5)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.vertical, 8)

        case .colophon:
            VStack(alignment: .leading, spacing: 0) {
                Divider().padding(.bottom, 14)
                Text(attributed)
                    .font(.footnote.italic())
                    .foregroundStyle(.secondary)
                    .lineSpacing(3)
            }
            .padding(.top, 20)

        case .term:
            Text(attributed)
                .font(Typeface.prayer(.callout))
                .frame(maxWidth: .infinity, alignment: .leading)

        case .definition:
            Text(attributed)
                .font(Typeface.label(.caption))
                .foregroundStyle(palette.accent)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.bottom, 8)
        }
    }

    private var hymnLines: [String] {
        block.runs.flatMap(\.lines).filter { !$0.trimmingCharacters(in: .whitespaces).isEmpty }
    }

    /// Inline marks, assembled into one attributed string so the text still
    /// wraps, selects and reads aloud as a single passage.
    /// The runs with the cross-mark's spacing made even.
    ///
    /// The printed book sets ✠ tight against the word that follows it — "✠and
    /// the love of God" — and relies on whatever space happens to precede it.
    /// Neither side can be trusted, so both are stripped here and the gap is
    /// put back by the renderer, the same on each side.
    private var spacedRuns: [Run] {
        var rs = block.runs
        for i in rs.indices where rs[i].mark == .signum {
            if i > 0 {
                rs[i - 1] = Run(t: trimmingTrailingSpaces(rs[i - 1].t),
                                mark: rs[i - 1].mark, href: rs[i - 1].href)
            }
            if i + 1 < rs.count {
                var next = rs[i + 1].t
                while next.first == " " { next.removeFirst() }
                rs[i + 1] = Run(t: next, mark: rs[i + 1].mark, href: rs[i + 1].href)
            }
        }
        return rs
    }

    private func trimmingTrailingSpaces(_ s: String) -> String {
        var t = s
        while t.last == " " { t.removeLast() }
        return t
    }

    private var attributed: AttributedString {
        var out = AttributedString()
        for (i, run) in spacedRuns.enumerated() {
            var piece = AttributedString(run.t.replacingOccurrences(of: "\n", with: " "))
            switch run.mark {
            case .rubric:
                piece.foregroundColor = palette.inkSoft
            case .signum:
                // Set larger than the text it sits in: it is an instruction to
                // make the sign of the cross, and at body size it disappeared
                // into the line. The spaces are added here rather than trusted
                // from the source, so the mark is evenly set on both sides —
                // except at the very start of a block, where a leading space
                // would indent the line. Each office opens on this mark.
                let glyph = run.t.trimmingCharacters(in: .whitespaces)
                piece = AttributedString((i == 0 ? "" : " ") + glyph + " ")
                piece.foregroundColor = palette.accent
                piece.font = Typeface.prayer(.title3)
            case .dropcap, .versal:
                piece.foregroundColor = palette.accent
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
                piece.foregroundColor = palette.accent
                piece.underlineStyle = .single
                piece.link = URL(string: "prayers://page/\(href)")
            }
            out.append(piece)
        }
        return out
    }
}
