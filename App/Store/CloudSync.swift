import Foundation
import GameCore

/// Keeps the save's `CloudBackup` (golden fish bought, cats bought with them, cats owned) in the iCloud
/// key-value store, so it survives a reinstall or a new phone. The backup only ever grows and is
/// merged by union in GameCore (`SaveGame.merge`), so the copy here and the one on the phone can both
/// change and still come together without losing anything.
///
/// When iCloud is off, signed out or not entitled, `NSUbiquitousKeyValueStore` keeps values on the
/// device only and never syncs; nothing here fails then, the backup just stays local.
@MainActor
final class CloudSync {
    private static let key = "cloudBackup.v1"
    private let store = NSUbiquitousKeyValueStore.default
    private var observer: NSObjectProtocol?

    /// Starts listening for copies written on other devices; `onChange` gets each one as it arrives.
    func start(onChange: @escaping @MainActor (CloudBackup) -> Void) {
        guard observer == nil else { return }
        observer = NotificationCenter.default.addObserver(
            forName: NSUbiquitousKeyValueStore.didChangeExternallyNotification, object: store, queue: .main
        ) { [weak self] _ in
            MainActor.assumeIsolated {
                guard let self, let backup = self.read() else { return }
                onChange(backup)
            }
        }
        // Asks for anything newer from iCloud; the answer comes through the notification.
        store.synchronize()
    }

    /// The copy in iCloud (or the last one seen), if there is one that can be read.
    func read() -> CloudBackup? {
        guard let data = store.data(forKey: Self.key) else { return nil }
        return try? JSONDecoder().decode(CloudBackup.self, from: data)
    }

    /// Writes `backup` when it differs from what is there.
    func write(_ backup: CloudBackup) {
        guard backup != read() else { return }
        let encoder = JSONEncoder()
        encoder.outputFormatting = .sortedKeys
        guard let data = try? encoder.encode(backup) else { return }
        store.set(data, forKey: Self.key)
    }
}
