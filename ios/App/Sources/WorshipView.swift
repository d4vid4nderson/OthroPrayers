import SwiftUI

/// What there is to hear, as a plain list of it.
///
/// The same restraint as the prayer pages: no artwork, no shelves of album
/// covers. An album is one quiet row that opens onto its own page of tracks;
/// a single recording sits here in full. The only lit thing on either screen
/// is whatever is sounding.
struct WorshipView: View {
    @EnvironmentObject private var player: Player

    private let albums = Chant.albums
    private let singles = Chant.singles

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 26) {
                if !albums.isEmpty {
                    shelf("Collections") {
                        VStack(spacing: 0) {
                            ForEach(albums) { album in
                                NavigationLink(value: album) { row(album) }
                                    .buttonStyle(.plain)
                                if album.id != albums.last?.id {
                                    Divider().padding(.leading, 18)
                                }
                            }
                        }
                        .card()
                    }
                }

                if !singles.isEmpty {
                    shelf("Recordings") { TrackList(tracks: singles) }
                }
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 24)
        }
        .scrollEdgeEffectStyle(.soft, for: .top)
        .background(Color.sanctuaryGround)
        .navigationTitle("Worship")
        .navigationDestination(for: Album.self) { AlbumView(album: $0) }
        .nowPlayingBar()
    }

    private func shelf<Content: View>(_ label: String,
                                      @ViewBuilder content: () -> Content) -> some View {
        VStack(alignment: .leading, spacing: 0) {
            MicroLabel(text: label).padding(.bottom, 10)
            content()
        }
    }

    /// An album's row. It carries the waveform while one of its own tracks is
    /// sounding, so the reader can find their way back to it from here.
    private func row(_ album: Album) -> some View {
        let sounding = player.current.map { album.tracks.contains($0) } ?? false
        return HStack(spacing: 14) {
            ZStack {
                if sounding {
                    Image(systemName: player.isPlaying ? "waveform" : "pause.fill")
                        .font(.footnote.weight(.semibold))
                        .foregroundStyle(Color.sanctuaryGold)
                        .symbolEffect(.variableColor, isActive: player.isPlaying)
                } else {
                    Image(systemName: "music.note.list")
                        .font(.footnote)
                        .foregroundStyle(.tertiary)
                }
            }
            .frame(width: 18)

            VStack(alignment: .leading, spacing: 2) {
                Text(album.name)
                    .font(Typeface.display(.body))
                    .foregroundStyle(sounding ? Color.sanctuaryGold : .primary)
                    .multilineTextAlignment(.leading)
                    .fixedSize(horizontal: false, vertical: true)
                Text(album.summary)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer(minLength: 10)

            Image(systemName: "chevron.right")
                .font(.caption.weight(.semibold))
                .foregroundStyle(.tertiary)
        }
        .padding(.vertical, 14)
        .padding(.horizontal, 18)
        .contentShape(.rect)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(album.name), \(album.summary)")
        .accessibilityHint("Opens the collection")
    }
}

/// One album's page: the whole of it, in the order it is sung.
struct AlbumView: View {
    let album: Album

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                masthead
                TrackList(tracks: album.tracks)
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 24)
        }
        .scrollEdgeEffectStyle(.soft, for: .top)
        .background(Color.sanctuaryGround)
        // The name is set as a masthead rather than left to the navigation bar,
        // which truncates anything as long as a monastery's. The bar keeps it
        // too, inline, for where the reader is once the masthead scrolls away.
        .navigationTitle(album.name)
        .navigationBarTitleDisplayMode(.inline)
        .nowPlayingBar()
    }

    private var masthead: some View {
        VStack(spacing: 10) {
            Text(album.name)
                .font(Typeface.display(.largeTitle))
                .multilineTextAlignment(.center)
            GoldRule().padding(.top, 8)
            MicroLabel(text: album.summary).padding(.top, 6)
        }
        .frame(maxWidth: .infinity)
        .padding(.top, 18)
        .padding(.bottom, 20)
    }
}

/// A list of recordings. Tapping one plays it with the rest of the list behind
/// it, so a collection runs on to its end and the singles run on through each
/// other — never across the two.
struct TrackList: View {
    let tracks: [Track]
    @EnvironmentObject private var player: Player

    var body: some View {
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
        .card()
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

private extension View {
    /// The one card shape both lists sit on.
    func card() -> some View {
        self
            .background(Color.sanctuarySurface, in: RoundedRectangle(cornerRadius: 20))
            .overlay(RoundedRectangle(cornerRadius: 20).stroke(.separator, lineWidth: 1))
    }
}

extension View {
    /// The sounding bar, on every screen of the worship tab — it must not
    /// vanish just because the reader stepped into a collection.
    func nowPlayingBar() -> some View { modifier(NowPlayingBar()) }
}

private struct NowPlayingBar: ViewModifier {
    @EnvironmentObject private var player: Player

    func body(content: Content) -> some View {
        content.safeAreaInset(edge: .bottom) {
            if player.current != nil { NowPlaying() }
        }
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
                    if let source = player.current?.source {
                        MicroLabel(text: source)
                    }
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
