# The native app

A SwiftUI app — no WebView. This is the app; there is no longer a website
beside it.

> **Most of this has compiled on a Mac, but not all of it.** The Swift is
> written on Linux, where there is no Swift toolchain and no iOS SDK, so
> nothing can be type-checked here. The core built and ran; anything added
> since may still need fixes on the first build. Everything *generated* — the
> content model, the structure, the fonts, the icons — is verified on every
> change.

## How the content gets here

`build.py` stays the single source of truth for every word of prayer. Two
generators turn it into data the app reads at launch:

```sh
python3 build.py            # writes build/*.html, and ios/Content/structure.json
python3 export_content.py   # writes ios/Content/content.json
```

The pages in `build/` are an intermediate step and are gitignored — nothing is
served anywhere. See the root [README](../README.md) for the whole chain.

- **`structure.json`** — the four hours with their time windows, each book's
  section order, and the extras.
- **`content.json`** — 16 pages as semantic blocks: headings, rubrics, verses,
  their inline marks, and cross-references between pages.

The Xcode project references `ios/Content/` where the generators write it, so
the app cannot drift from the site. Re-run both and rebuild; that is the whole
content workflow.

`export_content.py` refuses to drop anything it does not recognise — if you add
a new kind of markup to `build.py`, it will fail loudly rather than silently
lose a line of a prayer.

## Building it

```sh
brew install xcodegen
cd ios && xcodegen generate && open Prayers.xcodeproj
```

Then set your team under **Signing & Capabilities** (or put the Team ID in
`project.yml` under `DEVELOPMENT_TEAM`).

Deployment target is **iOS 27.0**, for second-iteration Liquid Glass and
`.crossFade`. Drop it to 18.0 in `project.yml` if you need older devices; the
app uses stock components, so it degrades to the pre-Liquid-Glass look rather
than breaking.

## How it adopts iOS 27

Deliberately, by using stock components rather than hand-painting surfaces:
`TabView`, `NavigationStack`, `.toolbar`, `Form`. The system gives those Liquid
Glass, with the specular highlights, scroll-edge behaviour and morphing that a
hand-rolled material cannot reproduce. What the app supplies is the palette, the
type and the restraint.

One place is marked for you to upgrade on the Mac: the hero card on Today uses
`.background(.regularMaterial, …)` because that is an API I could be certain of
without a compiler. There is a comment in `TodayView.swift` showing the
`.glassEffect(…)` form to try once it builds.

## What going native bought

- **Real Dynamic Type.** Every size is a semantic text style, so the app follows
  the phone's own text-size, bold-text and contrast settings. The bespoke
  three-step control the web version carried is gone — nothing else on the
  device knew about it.
- **Local notifications** for each hour. No server, nothing leaves the phone.
- **VoiceOver** that reads a prayer as one passage, with the contents disclosure
  announcing its own state.
- **The app icon follows the phone's appearance** — light, dark, tinted.

## TestFlight

Already handled in the project:

- `ITSAppUsesNonExemptEncryption: false`, so App Store Connect stops asking
  about export compliance on every upload.
- `PrivacyInfo.xcprivacy` declaring no tracking, no collection, and the one
  required-reason API the app touches (UserDefaults, `CA92.1`).
- A launch screen on the Sanctuary ground, so the first frame is never white.
- `MARKETING_VERSION` / `CURRENT_PROJECT_VERSION` in `project.yml` — bump
  `CURRENT_PROJECT_VERSION` for every upload; App Store Connect rejects a repeat.

What you still have to do:

1. Create the app record in App Store Connect with bundle ID
   `com.orthoprayers.western` (change it in `project.yml` if you want another).
2. **Product › Archive**, then **Distribute App › TestFlight**.
3. Internal testers (your own team, up to 100) need no review. **External
   testers require Beta App Review**, which is lighter than full App Store
   review but is still a review — and a prayer book that is entirely offline
   content is a much easier case to make than a thin web wrapper.

### The worship recordings

`project.yml` lists `Music` as a source, but **`ios/Music/` is not in this
repository** and neither is `hymns/`: the recordings are other people's
published work and this repo is public. A fresh clone therefore has the
Worship screen's manifest but none of its audio.

To restore them on a machine that has the files, put them in `hymns/` — a
folder of recordings becomes a collection with its own page, a loose file
beside the folders becomes a single — and run:

```sh
python3 export_music.py
```

That normalises the names, reads each duration, stages the audio into
`ios/Music/` where `project.yml` picks it up as a folder reference, and
rewrites `ios/Content/music.json`.

### The app icon

Vector. `assets/icons/app-icon.svg` is the master, with the lettering converted
to outlines so it carries no font dependency and renders identically anywhere.
Nothing is upscaled at any size, which matters on TestFlight: the icon is the
first thing a tester sees and App Store Connect renders it large.

```sh
python3 generate_icons.py --ios
```

That writes the Xcode catalog with all three iOS appearances and copies it into
the project. It still emits a few web favicons alongside them, left over from
the website; they are harmless and uncommitted.

## Still to do

- **Widgets** — today's office on the Lock Screen or Home Screen. Real Swift
  work, not a plugin.

The Capacitor fallback (`ios/www`, `capacitor.config.json`, `package.json`) is
gone, along with the website it wrapped. This app is the only one now.
