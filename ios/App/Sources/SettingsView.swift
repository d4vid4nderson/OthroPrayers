import SwiftUI
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

    var body: some View {
        Form {
            Section {
                Picker("Style", selection: $settings.theme) {
                    ForEach(Theme.allCases) { theme in
                        Text(theme.name).tag(theme)
                    }
                }
                .pickerStyle(.inline)
                .labelsHidden()
            } header: {
                Text("Style")
            } footer: {
                Text(settings.theme.detail
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
                    // A sample in the chosen size, so the setting can be judged
                    // by eye rather than by the name of a size.
                    Text("Our Father, who art in heaven")
                        .font(Typeface.prayer())
                        .dynamicTypeSize(settings.textSize)
                        .foregroundStyle(.secondary)
                }
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
                Toggle("Remind me at each hour", isOn: $settings.hourReminders)
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
        .navigationTitle("Settings")
        .onChange(of: settings.hourReminders) { _, on in
            Task { await Reminders.apply(enabled: on, hours: Library.shared.hours) }
        }
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
    static func apply(enabled: Bool, hours: [Hour]) async {
        let centre = UNUserNotificationCenter.current()
        centre.removeAllPendingNotificationRequests()
        guard enabled else { return }
        guard let granted = try? await centre.requestAuthorization(options: [.alert, .sound]),
              granted else { return }
        for hour in hours {
            var when = DateComponents()
            when.hour = hour.from
            when.minute = 0
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
