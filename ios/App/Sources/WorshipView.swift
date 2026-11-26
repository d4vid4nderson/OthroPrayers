import SwiftUI

/// What there is to hear, as a plain list of it.
///
/// The same restraint as the prayer pages: no artwork, no shelves of album
/// covers. An album is one quiet row that opens onto its own page of tracks;
/// a single recording sits here in full. The only lit thing on either screen
/// is whatever is sounding.
struct WorshipView: View {
    /// Colours and type, from the environment so this view is
    /// invalidated when they change. See Design.
    @Environment(\.design) var design
    private var palette: Palette { design.palette }
    @EnvironmentObject private var player: Player
    // observed so a theme change re-renders this screen: `palette` reads
    // Settings.shared directly, which SwiftUI cannot see on its own
    @EnvironmentObject private var settings: Settings

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
                                    ThemedRule().padding(.leading, 18)
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
        .background(palette.ground)
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
                        .foregroundStyle(palette.accent)
                        .symbolEffect(.variableColor, isActive: player.isPlaying)
                } else {
                    Image(systemName: "music.note.list")
                        .font(.footnote)
                        .foregroundStyle(palette.inkFaint)
                }
            }
            .frame(width: 18)

            VStack(alignment: .leading, spacing: 2) {
                Text(album.name)
                    .font(Typeface.display(.body))
                    .foregroundStyle(sounding ? palette.accent : .primary)
                    .multilineTextAlignment(.leading)
                    .fixedSize(horizontal: false, vertical: true)
                Text(album.summary)
                    .font(.caption)
                    .foregroundStyle(palette.inkSoft)
            }

            Spacer(minLength: 10)

            Image(systemName: "chevron.right")
                .font(.caption.weight(.semibold))
                .foregroundStyle(palette.inkFaint)
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
    /// Colours and type, from the environment so this view is
    /// invalidated when they change. See Design.
    @Environment(\.design) var design
    private var palette: Palette { design.palette }
    let album: Album
    // see WorshipView: the palette is not observable by itself
    @EnvironmentObject private var settings: Settings

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
        .background(palette.ground)
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
            AccentRule().padding(.top, 8)
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
    /// Colours and type, from the environment so this view is
    /// invalidated when they change. See Design.
    @Environment(\.design) var design
    private var palette: Palette { design.palette }
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
                // A recording whose file is not in this build cannot play, so
                // the row says so rather than ignoring the tap in silence.
                .disabled(track.url == nil)
                .opacity(track.url == nil ? 0.4 : 1)
                if track.id != tracks.last?.id {
                    ThemedRule().padding(.leading, 18)
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
                        .foregroundStyle(palette.accent)
                        .symbolEffect(.variableColor, isActive: player.isPlaying)
                } else {
                    Circle().fill(palette.inkFaint).frame(width: 7, height: 7)
                }
            }
            .frame(width: 18)

            Text(track.title)
                .font(Typeface.display(.body))
                .foregroundStyle(sounding ? palette.accent : .primary)
                .multilineTextAlignment(.leading)
                .fixedSize(horizontal: false, vertical: true)

            Spacer(minLength: 10)

            Text(track.length)
                .font(.caption.monospacedDigit())
                .foregroundStyle(palette.inkSoft)
        }
        .padding(.vertical, 14)
        .padding(.horizontal, 18)
        .contentShape(.rect)
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(track.title), \(track.length)")
        .accessibilityHint(sounding && player.isPlaying ? "Pauses" : "Plays")
    }
}

/// The one card shape both lists sit on.
///
/// A ViewModifier rather than a method on View, because a method has nowhere
/// to put an `@Environment` and so had no way to be told the palette changed.
/// It read a global and kept the colours it was first drawn with.
private struct Card: ViewModifier {
    @Environment(\.design) var design

    func body(content: Content) -> some View {
        content
            .background(design.palette.surface, in: Container.shape())
            .overlay(Container.shape().stroke(design.palette.hairline, lineWidth: 1))
    }
}

private extension View {
    func card() -> some View { modifier(Card()) }
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
    /// Colours and type, from the environment so this view is
    /// invalidated when they change. See Design.
    @Environment(\.design) var design
    private var palette: Palette { design.palette }
    @EnvironmentObject private var player: Player

    var body: some View {
        VStack(spacing: 0) {
            ProgressView(value: player.progress)
                .progressViewStyle(.linear)
                .tint(palette.accent)
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
            .tint(palette.accent)
            .padding(.horizontal, 18)
            .padding(.vertical, 12)
        }
        .glassEffect(.regular.tint(palette.accent.opacity(0.12)),
                     in: Container.shape())
        .padding(.horizontal, 12)
        .padding(.bottom, 6)
    }
}
