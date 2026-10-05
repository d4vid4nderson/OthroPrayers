import SwiftUI

/// The monastery's chant, as a plain list of what there is to hear.
///
/// The same restraint as the prayer pages: no artwork, no shelves of album
/// covers. The recordings are one collection, so the screen is one list, and
/// the only lit thing on it is whatever is sounding.
struct WorshipView: View {
    @EnvironmentObject private var player: Player

    private let tracks = Chant.tracks

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                MicroLabel(text: Chant.collection)
                    .padding(.bottom, 10)

                VStack(spacing: 0) {
                    ForEach(tracks) { track in
                        Button {
                            player.tap(track, queue: tracks)
                        } label: {
                            row(track)
                        }
                        .buttonStyle(.plain)
                        if track.id != tracks.last?.id {
                            Divider().padding(.leading, 18)
                        }
                    }
                }
                .background(Color.sanctuarySurface, in: RoundedRectangle(cornerRadius: 20))
                .overlay(RoundedRectangle(cornerRadius: 20).stroke(.separator, lineWidth: 1))
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 24)
        }
        .scrollEdgeEffectStyle(.soft, for: .top)
        .background(Color.sanctuaryGround)
        .navigationTitle("Worship")
        .safeAreaInset(edge: .bottom) {
            if player.current != nil { NowPlaying() }
        }
    }

    private func row(_ track: Track) -> some View {
        let sounding = player.current == track
        return HStack(spacing: 14) {
            ZStack {
                if sounding {
                    Image(systemName: player.isPlaying ? "waveform" : "pause.fill")
                        .font(.footnote.weight(.semibold))
                        .foregroundStyle(Color.sanctuaryGold)
                        .symbolEffect(.variableColor, isActive: player.isPlaying)
                } else {
                    Circle().fill(.tertiary).frame(width: 7, height: 7)
                }
            }
            .frame(width: 18)

            Text(track.title)
                .font(Typeface.display(.body))
                .foregroundStyle(sounding ? Color.sanctuaryGold : .primary)
                .multilineTextAlignment(.leading)
                .fixedSize(horizontal: false, vertical: true)

            Spacer(minLength: 10)

            Text(track.length)
                .font(.caption.monospacedDigit())
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 14)
        .padding(.horizontal, 18)
        .contentShape(.rect)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(track.title), \(track.length)")
        .accessibilityHint(sounding && player.isPlaying ? "Pauses" : "Plays")
    }
}

/// The bar that sits above the tab bar while something is sounding.
private struct NowPlaying: View {
    @EnvironmentObject private var player: Player

    var body: some View {
        VStack(spacing: 0) {
            ProgressView(value: player.progress)
                .progressViewStyle(.linear)
                .tint(Color.sanctuaryGold)
                .scaleEffect(x: 1, y: 0.6, anchor: .center)

            HStack(spacing: 16) {
                VStack(alignment: .leading, spacing: 1) {
                    Text(player.current?.title ?? "")
                        .font(Typeface.display(.subheadline))
                        .lineLimit(1)
                    MicroLabel(text: Chant.collection)
                }

                Spacer(minLength: 8)

                Button { player.toggle() } label: {
                    Image(systemName: player.isPlaying ? "pause.fill" : "play.fill")
                        .font(.title3)
                }
                .accessibilityLabel(player.isPlaying ? "Pause" : "Play")

                Button { player.next() } label: {
                    Image(systemName: "forward.fill").font(.body)
                }
                .accessibilityLabel("Next")
            }
            .tint(Color.sanctuaryGold)
            .padding(.horizontal, 18)
            .padding(.vertical, 12)
        }
        .glassEffect(.regular.tint(Color.sanctuaryGold.opacity(0.12)),
                     in: .rect(cornerRadius: 20))
        .padding(.horizontal, 12)
        .padding(.bottom, 6)
    }
}
