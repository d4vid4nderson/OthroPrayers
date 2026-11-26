import SwiftUI
import UIKit

/// The phone's own light/dark, read without being told it by ourselves.
///
/// `preferredColorScheme` is a preference that travels up to the window, so
/// once the app sets it, `@Environment(\.colorScheme)` reports that value back
/// — asking it which appearance the phone is in only ever returns our own
/// answer. The window *scene*'s trait collection is not overridden by a view's
/// preference, so it still says what the phone is set to.
enum Appearance {
    static var systemIsDark: Bool {
        let scene = UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .first { $0.activationState == .foregroundActive }
            ?? UIApplication.shared.connectedScenes
                .compactMap { $0 as? UIWindowScene }.first
        return scene?.traitCollection.userInterfaceStyle == .dark
    }
}
