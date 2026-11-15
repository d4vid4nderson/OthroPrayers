import AVFoundation
import MediaPlayer
import SwiftUI

// The worship recordings, bundled with the app and played from disk. Like the
// prayers, nothing here touches the network — everything is on the device.
//
// What is on the shelf is whatever export_music.py found in hymns/: folders of
// recordings become albums with a page each, loose files become singles.

struct Track: Codable, Hashable, Identifiable {
    let file: String
    let title: String
    let seconds: Int
    /// Who recorded it, for the now-playing bar. An album's tracks are
    /// attributed to the album; a single carries whatever its own tags said,
    /// and may say nothing.
    let source: String?

    var id: String { file }

    /// m:ss, as a track length is always written.
    var length: String {
        String(format: "%d:%02d", seconds / 60, seconds % 60)
    }

    var url: URL? {
        Bundle.main.url(forResource: file, withExtension: nil, subdirectory: "Music")
    }
}

/// A folder of recordings — named `Album` rather than `Collection` so it does
/// not shadow the standard library's protocol of that name.
struct Album: Codable, Hashable, Identifiable {
    let name: String
    let tracks: [Track]

    var id: String { name }

    /// What the row under the title says: how much there is to hear.
    var summary: String {
        let minutes = tracks.reduce(0) { $0 + $1.seconds } / 60
        return "\(tracks.count) recordings · \(minutes) min"
    }
}

private struct MusicFile: Codable {
    let singles: [Track]
    let collections: [Album]
}

enum Chant {
    private static let file: MusicFile = Bundle.main.decode("music.json")
    /// Loose recordings, which sit on the worship screen itself.
    static var singles: [Track] { file.singles }
    /// Folders of recordings, each of which opens its own page.
    static var albums: [Album] { file.collections }
}

/// One player for the whole app, so the now-playing bar and the track list
/// cannot disagree about what is sounding.
@MainActor
final class Player: NSObject, ObservableObject {
    static let shared = Player()

    @Published private(set) var current: Track?
    @Published private(set) var isPlaying = false
    /// 0...1 through the current track.
    @Published var progress: Double = 0

    private var audio: AVAudioPlayer?
    private var ticker: Timer?
    private var queue: [Track] = []

    private override init() {
        super.init()
        configureSession()
        configureRemoteCommands()
    }

    // MARK: - Transport

    func play(_ track: Track, queue: [Track]) {
        self.queue = queue
        start(track)
    }

    /// Tapping the track that is already sounding pauses it, rather than
    /// starting it again from the beginning.
    func tap(_ track: Track, queue: [Track]) {
        if current == track {
            toggle()
        } else {
            play(track, queue: queue)
        }
    }

    func toggle() {
        guard let audio else { return }
        if audio.isPlaying {
            audio.pause()
            isPlaying = false
        } else {
            audio.play()
            isPlaying = true
        }
        updateNowPlaying()
    }

    func next() { step(by: 1) }
    func previous() {
        // Standard behaviour: part-way through a track, go back to its start.
        if let audio, audio.currentTime > 3 {
            audio.currentTime = 0
            updateNowPlaying()
        } else {
            step(by: -1)
        }
    }

    func seek(toFraction f: Double) {
        guard let audio else { return }
        audio.currentTime = max(0, min(1, f)) * audio.duration
        progress = f
        updateNowPlaying()
    }

    func stop() {
        audio?.stop()
        audio = nil
        current = nil
        isPlaying = false
        progress = 0
        ticker?.invalidate()
        MPNowPlayingInfoCenter.default().nowPlayingInfo = nil
    }

    // MARK: - Machinery

    private func start(_ track: Track) {
        guard let url = track.url, let player = try? AVAudioPlayer(contentsOf: url) else {
            // A missing file should not take the app down; the row simply does
            // nothing and the reader can pick another.
            return
        }
        audio?.stop()
        player.delegate = self
        player.prepareToPlay()
        player.play()

        audio = player
        current = track
        isPlaying = true
        progress = 0
        startTicking()
        updateNowPlaying()
    }

    private func step(by n: Int) {
        guard let current, let i = queue.firstIndex(of: current), !queue.isEmpty else { return }
        let next = (i + n + queue.count) % queue.count
        start(queue[next])
    }

    fileprivate func finished() {
        guard let current, let i = queue.firstIndex(of: current) else { return stop() }
        if i + 1 < queue.count {
            start(queue[i + 1])
        } else {
            stop()
        }
    }

    private func startTicking() {
        ticker?.invalidate()
        ticker = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.tick() }
        }
    }

    private func tick() {
        guard let audio, audio.duration > 0 else { return }
        progress = audio.currentTime / audio.duration
    }

    private func configureSession() {
        let session = AVAudioSession.sharedInstance()
        try? session.setCategory(.playback, mode: .default)
        try? session.setActive(true)
    }

    private func configureRemoteCommands() {
        let centre = MPRemoteCommandCenter.shared()
        centre.playCommand.addTarget { [weak self] _ in
            Task { @MainActor in self?.toggle() }
            return .success
        }
        centre.pauseCommand.addTarget { [weak self] _ in
            Task { @MainActor in self?.toggle() }
            return .success
        }
        centre.nextTrackCommand.addTarget { [weak self] _ in
            Task { @MainActor in self?.next() }
            return .success
        }
        centre.previousTrackCommand.addTarget { [weak self] _ in
            Task { @MainActor in self?.previous() }
            return .success
        }
    }

    private func updateNowPlaying() {
        guard let current, let audio else { return }
        var info: [String: Any] = [
            MPMediaItemPropertyTitle: current.title,
            MPMediaItemPropertyPlaybackDuration: audio.duration,
            MPNowPlayingInfoPropertyElapsedPlaybackTime: audio.currentTime,
            MPNowPlayingInfoPropertyPlaybackRate: audio.isPlaying ? 1.0 : 0.0,
        ]
        // Left out rather than blank when the recording does not say: the lock
        // screen lays itself out around the fields that are actually there.
        if let source = current.source {
            info[MPMediaItemPropertyArtist] = source
        }
        MPNowPlayingInfoCenter.default().nowPlayingInfo = info
    }
}

extension Player: AVAudioPlayerDelegate {
    nonisolated func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        Task { @MainActor in self.finished() }
    }
}
