import SwiftUI
import UserNotifications

/// Few controls, on purpose.
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
            Section("Reading") {
                Toggle("Dyslexia-friendly text", isOn: $settings.dyslexicFont)
                LabeledContent("Text size") {
                    Text("Follows your phone")
                        .foregroundStyle(.secondary)
                }
            } footer: {
                Text("Text size, bold text and contrast all follow iOS. "
                     + "Change them in Settings › Display & Brightness, or Accessibility.")
            }

            Section("The hours") {
                Toggle("Remind me at each hour", isOn: $settings.hourReminders)
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
