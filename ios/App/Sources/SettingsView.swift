import SwiftUI
import UIKit
import UserNotifications

/// Few controls, on purpose — but the style is one of them: the app carries
/// all four, and which one a reader wants is theirs to say.
///
/// Text size is gone: the app follows the phone's own Dynamic Type setting, so
/// there is no bespoke three-step control that nothing else on the device knows
/// about. Theme is gone: Sanctuary is dark by construction. The accent palettes
/// and background temperature the web version carried are gone too — one
/// designed system cannot honour them.
struct SettingsView: View {
    @EnvironmentObject private var settings: Settings
    @EnvironmentObject private var library: Library

    var body: some View {
        Form {
            Section {
                Toggle("Match phone appearance", isOn: $settings.followSystemAppearance)
                if settings.followSystemAppearance {
                    Picker("In light mode", selection: $settings.lightTheme) {
                        ForEach(Theme.allCases) { Text($0.name).tag($0) }
                    }
                    Picker("In dark mode", selection: $settings.darkTheme) {
                        ForEach(Theme.allCases) { Text($0.name).tag($0) }
                    }
                } else {
                    Picker("Style", selection: $settings.theme) {
                        ForEach(Theme.allCases) { Text($0.name).tag($0) }
                    }
                    .pickerStyle(.inline)
                    .labelsHidden()
                }
                // Only when Terminal is what will actually be drawn — under
                // "match phone appearance" that depends on which side the
                // phone is on, so it asks effectiveTheme rather than theme.
                if settings.effectiveTheme == .terminal
                    || settings.lightTheme == .terminal
                    || settings.darkTheme == .terminal {
                    Picker("Phosphor", selection: $settings.terminalPhosphor) {
                        ForEach(Theme.Phosphor.allCases) { p in
                            Text(p.name).tag(p)
                        }
                    }
                }
            } header: {
                Text("Style")
            } footer: {
                Text(settings.followSystemAppearance
                     ? "The app turns light and dark with the phone, using the "
                       + "theme you pick for each. "
                       + settings.effectiveTheme.detail
                     : "Fixed to this theme whatever the phone is set to. "
                       + settings.theme.detail
                     + " Dyslexia-friendly text overrides whichever you pick.")
            }

            Section {
                Toggle("Dyslexia-friendly text", isOn: $settings.dyslexicFont)
                Toggle("Match phone text size", isOn: $settings.followSystemTextSize)
                if !settings.followSystemTextSize {
                    Picker("Text size", selection: $settings.textSize) {
                        ForEach(Settings.offeredSizes, id: \.self) { size in
                            Text(Self.name(for: size)).tag(size)
                        }
                    }
                }
                specimen
            } header: {
                Text("Reading")
            } footer: {
                Text(settings.followSystemTextSize
                     ? "Text size follows iOS. Change it in Settings › Display & "
                       + "Brightness, or Accessibility, and every app follows together."
                     : "This app only. Bold text and contrast still follow iOS. "
                       + "The very largest accessibility sizes are set in iOS itself.")
            }

            Section {
                // Two rows of real icons rather than two lists of words. Each
                // row previews the axis it changes against the current value
                // of the other, so the tiles show what tapping them will
                // actually do.
                iconRow(title: "Style", items: Settings.IconStyle.allCases,
                        label: \.shortName, selected: settings.iconStyle) { st in
                    Settings.previewName(colour: settings.iconColour, style: st)
                } pick: { settings.iconStyle = $0 }

                iconRow(title: "Colour", items: Settings.IconColour.allCases,
                        label: \.shortName, selected: settings.iconColour) { c in
                    Settings.previewName(colour: c, style: settings.iconStyle)
                } pick: { settings.iconColour = $0 }
            } header: {
                Text("App icon")
            } footer: {
                Text(settings.iconColour == .automatic && settings.iconStyle == .mark
                     ? "The default icon follows the phone between light, dark and "
                       + "tinted. Choosing anything else fixes it."
                     : "A chosen icon is one image, so it no longer changes with "
                       + "light and dark mode. Set it back to Follow appearance "
                       + "and IC XC NIKA to have it do so again.")
            }

            Section {
                Toggle("Remind me at each hour", isOn: $settings.hourReminders)
                if settings.hourReminders {
                    // One row per office: its name, its time, its switch.
                    // A toggle row plus a separate indented "at" row turned
                    // four offices into eight rows and read as a mess.
                    ForEach(library.hours) { hour in
                        HStack(spacing: 12) {
                            Text(hour.title)
                                .lineLimit(1)
                                .layoutPriority(1)
                            Spacer(minLength: 4)
                            DatePicker("", selection: time(for: hour),
                                       displayedComponents: .hourAndMinute)
                                .labelsHidden()
                                .disabled(!settings.reminds(hour))
                                .opacity(settings.reminds(hour) ? 1 : 0.4)
                            Toggle("", isOn: Binding(
                                get: { settings.reminds(hour) },
                                set: { settings.setReminds($0, for: hour) }))
                                .labelsHidden()
                        }
                        .accessibilityElement(children: .contain)
                        .accessibilityLabel(hour.title)
                    }
                }
            } header: {
                Text("The hours")
            } footer: {
                Text("A quiet notification when each office falls due. "
                     + "Nothing leaves the phone: the reminders are scheduled locally.")
            }

            Section {
                LabeledContent("Version", value: Self.version)
            } footer: {
                Text("The Western Rite offices, A Little Prayer Book and the "
                     + "St. Peter Pew Missal. Everything is held on the device; "
                     + "the app makes no network requests.")
            }
        }
        // A Form paints the system's grouped background and row fills, which
        // follow light/dark but not the theme — so Settings stayed system grey
        // while every other screen turned. Hidden, and repainted from the
        // palette.
        .scrollContentBackground(.hidden)
        .background(palette.ground)
        .listRowBackground(palette.surface)
        .navigationTitle("Settings")
        .onChange(of: settings.hourReminders) { _, on in
            reschedule(enabled: on)
        }
        // Moving a time has to re-arm the notifications, or the picker would
        // change and nothing behind it would.
        .onChange(of: settings.reminderTimes) { _, _ in
            reschedule(enabled: settings.hourReminders)
        }
        .onChange(of: settings.reminderOff) { _, _ in
            reschedule(enabled: settings.hourReminders)
        }
        .onChange(of: settings.iconColour) { _, _ in applyIcon() }
        .onChange(of: settings.iconStyle) { _, _ in applyIcon() }
    }

    /// iOS shows its own "you have changed the icon" alert, which cannot be
    /// suppressed through the public API, so the change is not announced again
    /// here. Setting the same name twice is a no-op worth avoiding: it would
    /// put that alert on screen for nothing.
    private func applyIcon() {
        let wanted = settings.alternateIconName
        guard UIApplication.shared.supportsAlternateIcons,
              UIApplication.shared.alternateIconName != wanted else { return }
        UIApplication.shared.setAlternateIconName(wanted) { error in
            if let error {
                // Nothing a reader can do about it, and nothing worth
                // interrupting them for; the picker simply will not have taken.
                print("app icon: \(error.localizedDescription)")
            }
        }
    }

    /// The times are read here, on the main actor, and handed over as plain
    /// data. Passing `settings` into the task instead would drag an actor
    /// across the boundary for the sake of four integers.
    private func reschedule(enabled: Bool) {
        let hours = library.hours
        // only the offices that ring, and only their times
        let wanted = hours.filter { settings.reminds($0) }
        let times = Dictionary(uniqueKeysWithValues:
            wanted.map { ($0.slug, settings.reminderMinutes(for: $0)) })
        Task { await Reminders.apply(enabled: enabled, hours: wanted, times: times) }
    }

    /// One row of the icon picker: a horizontal strip of tiles.
    @ViewBuilder
    private func iconRow<T: Hashable & Identifiable>(
        title: String,
        items: [T],
        label: KeyPath<T, String>,
        selected: T,
        preview: @escaping (T) -> String,
        pick: @escaping (T) -> Void
    ) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            MicroLabel(text: title)
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 14) {
                    ForEach(items) { item in
                        IconTile(preview: preview(item),
                                 label: item[keyPath: label],
                                 selected: item == selected) { pick(item) }
                    }
                }
                .padding(.horizontal, 2)
                .padding(.bottom, 2)
            }
        }
        .padding(.vertical, 6)
        .listRowInsets(EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 0))
    }

    /// A DatePicker wants a Date; a reminder is a time of day. The date part
    /// is thrown away on the way back in, so only hour and minute survive —
    /// the trigger repeats daily and has no use for a day.
    private func time(for hour: Hour) -> Binding<Date> {
        Binding(
            get: {
                let m = settings.reminderMinutes(for: hour)
                return Calendar.current.date(
                    bySettingHour: m / 60, minute: m % 60, second: 0,
                    of: Date.now) ?? Date.now
            },
            set: { new in
                let c = Calendar.current.dateComponents([.hour, .minute], from: new)
                settings.setReminderMinutes((c.hour ?? 0) * 60 + (c.minute ?? 0),
                                            for: hour)
            })
    }

    /// A few lines of a real page, set exactly as a page sets them.
    ///
    /// Shown whether or not the size is unlinked, so flipping the toggle shows
    /// the difference rather than making it something to remember. In the
    /// reading colours and the reading typeface, not a dimmed sample: legibility
    /// is the thing being judged, and grey text at the right size would answer
    /// the wrong question. It carries a rubric and a cross-mark as well as
    /// prayer text, because a page is all three and they do not scale alike.
    private var specimen: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Preview")
                .font(.caption2.weight(.semibold))
                .tracking(1.4)
                .textCase(.uppercase)
                .foregroundStyle(palette.inkFaint)

            Text("Stand, and make the sign of the cross.")
                .font(Typeface.prayer(.callout).italic())
                .foregroundStyle(palette.inkSoft)

            (Text("✠ ")
                .font(Typeface.prayer(.title))
                .foregroundColor(palette.accent)
             + Text("In the Name of the Father, and of the Son, and of the Holy Spirit. Amen.")
                .font(Typeface.prayer()))
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.vertical, 6)
        // No size modifier here on purpose: the override is applied at the
        // root of the app, so this screen is already being drawn at the chosen
        // size and the specimen inherits it. What it adds is the reading
        // typeface, the rubric and the cross-mark, which the settings chrome
        // around it does not show.
    }

    /// DynamicTypeSize has no display name of its own, and ".xxxLarge" is not
    /// something to show a reader.
    private static func name(for size: DynamicTypeSize) -> String {
        switch size {
        case .xSmall:  return "Extra small"
        case .small:   return "Small"
        case .medium:  return "Medium"
        case .large:   return "Default"
        case .xLarge:  return "Large"
        case .xxLarge: return "Extra large"
        default:       return "Largest"
        }
    }

    private static var version: String {
        let v = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "—"
        let b = Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "—"
        return "\(v) (\(b))"
    }
}

/// Local notifications for the hours — the thing a web app could not do without
/// a server. These are scheduled on the device and send nothing anywhere.
enum Reminders {
    /// `times` gives each office's reminder as minutes after midnight, keyed
    /// by slug. It used to be `hour.from`, which is when the office's *window*
    /// opens — so Morning Prayer's reminder fired at four in the morning.
    static func apply(enabled: Bool, hours: [Hour], times: [String: Int]) async {
        let centre = UNUserNotificationCenter.current()
        centre.removeAllPendingNotificationRequests()
        guard enabled else { return }
        guard let granted = try? await centre.requestAuthorization(options: [.alert, .sound]),
              granted else { return }
        for hour in hours {
            let m = times[hour.slug] ?? Settings.defaultMinutes(for: hour)
            var when = DateComponents()
            when.hour = m / 60
            when.minute = m % 60
            let content = UNMutableNotificationContent()
            content.title = hour.title
            content.body = hour.blurb
            content.sound = .default
            let request = UNNotificationRequest(
                identifier: "hour-\(hour.slug)",
                content: content,
                trigger: UNCalendarNotificationTrigger(dateMatching: when, repeats: true))
            try? await centre.add(request)
        }
    }
}

/// One icon in the picker: the artwork itself, masked to the shape iOS will
/// mask it to, with the chosen one ringed.
private struct IconTile: View {
    let preview: String
    let label: String
    let selected: Bool
    let tap: () -> Void

    private let side: CGFloat = 60
    // iOS draws app icons as a squircle; a plain rounded rect at this radius
    // is close enough at this size and does not need a custom shape.
    private var shape: some InsettableShape {
        RoundedRectangle(cornerRadius: side * 0.225, style: .continuous)
    }

    var body: some View {
        Button(action: tap) {
            VStack(spacing: 6) {
                // A missing asset must show, not vanish: the first version of
                // this picker drew nothing at all because the imagesets were
                // written with an unfilled 2x/3x, and blank tiles look like a
                // layout bug rather than a missing file.
                Image(preview)
                    .resizable()
                    .frame(width: side, height: side)
                    .background(
                        ZStack {
                            Color.secondary.opacity(0.18)
                            Image(systemName: "questionmark")
                                .font(.caption).foregroundStyle(palette.inkSoft)
                        })
                    .clipShape(shape)
                    .overlay(shape.stroke(selected ? palette.accent : .clear,
                                          lineWidth: 2.5))
                    .overlay(shape.stroke(palette.hairline, lineWidth: 0.5))
                Text(label)
                    .font(.caption2)
                    .lineLimit(1)
                    .foregroundStyle(selected ? palette.accent : .secondary)
            }
            .frame(width: 74)
        }
        .buttonStyle(.plain)
        .accessibilityLabel(label)
        .accessibilityAddTraits(selected ? [.isButton, .isSelected] : .isButton)
    }
}
