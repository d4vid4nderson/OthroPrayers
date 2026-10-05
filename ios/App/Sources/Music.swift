import AVFoundation
import MediaPlayer
import SwiftUI

// The worship recordings: the All-Merciful Saviour Monastery chant, bundled
// with the app and played from disk. Like the prayers, nothing here touches
// the network — the whole collection is on the device.

struct Track: Codable, Hashable, Identifiable {
    let file: String
    let title: String
    let seconds: Int

    var id: String { file }

    /// m:ss, as a track length is always written.
    var length: String {
        String(format: "%d:%02d", seconds / 60, seconds % 60)
    }

    var url: URL? {
        Bundle.main.url(forResource: file, withExtension: nil, subdirectory: "Music")
    }
}

private struct MusicFile: Codable {
    let collection: String
    let tracks: [Track]
}

enum Chant {
    private static let file: MusicFile = Bundle.main.decode("music.json")
    static var collection: String { file.collection }
    static var tracks: [Track] { file.tracks }
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
        MPNowPlayingInfoCenter.default().nowPlayingInfo = [
            MPMediaItemPropertyTitle: current.title,
            MPMediaItemPropertyArtist: Chant.collection,
            MPMediaItemPropertyPlaybackDuration: audio.duration,
            MPNowPlayingInfoPropertyElapsedPlaybackTime: audio.currentTime,
            MPNowPlayingInfoPropertyPlaybackRate: audio.isPlaying ? 1.0 : 0.0,
        ]
    }
}

extension Player: AVAudioPlayerDelegate {
    nonisolated func audioPlayerDidFinishPlaying(_ player: AVAudioPlayer, successfully flag: Bool) {
        Task { @MainActor in self.finished() }
    }
}
