import Foundation
import GameCore
import Observation
import StoreKit

/// The App Store side of golden fish (StoreKit 2 consumables). Loads the four packs, buys them, and
/// hands every verified transaction to the model to credit, finishing it only once the credit is
/// saved. What a pack gives and how the balance works are GameCore's (`GoldenFish`, `SaveGame`).
///
/// Purchases can arrive outside a tap on BUY (Ask to Buy approved later, a purchase interrupted by a
/// crash or a lost connection, a promoted purchase), so `start()` listens to `Transaction.updates`
/// for the life of the app and replays `Transaction.unfinished` at launch. A transaction already
/// credited (by id) is never credited again, so replays are harmless.
@MainActor
@Observable
final class GoldenStore {
    enum Status: Equatable {
        case idle, loading, loaded
        /// No products came back (offline, store down, or purchases off in this run).
        case unavailable
    }

    /// A short line shown in the golden fish panel after a purchase attempt.
    enum Notice: Equatable {
        case thanks, pending, failed
    }

    /// Products by id, once loaded.
    private(set) var products: [String: Product] = [:]
    private(set) var status = Status.idle
    /// A purchase made from the panel and credited: how many golden fish it gave. `id` goes up with each
    /// one, so the screen can close the panel, show the banner and count the balance up.
    struct Delivery: Equatable {
        let id: Int
        let amount: Int
    }

    /// The product being bought right now, if any.
    private(set) var buying: String?
    private(set) var delivery: Delivery?
    var notice: Notice?
    /// False in debug bot, silent and UI-test runs: nothing is loaded or bought there.
    private(set) var enabled = false

    /// Credits a transaction: (transaction id, product id, quantity). True once it is saved (now or
    /// before), so the transaction may be finished.
    @ObservationIgnored private var credit: ((String, String, Int) -> Bool)?
    @ObservationIgnored private var listeners: [Task<Void, Never>] = []

    /// Starts listening for transactions; call once at launch.
    func start(credit: @escaping (String, String, Int) -> Bool) {
        guard !enabled else { return }
        enabled = true
        self.credit = credit
        listeners.append(Task { [weak self] in
            for await result in Transaction.updates {
                await self?.process(result)
            }
        })
        listeners.append(Task { [weak self] in
            for await result in Transaction.unfinished {
                await self?.process(result)
            }
        })
    }

    /// The App Store's product for `pack`, once loaded; its `displayPrice` is the price to show.
    func product(for pack: GoldenFish.Pack) -> Product? {
        products[pack.productID]
    }

    /// Loads the packs from the App Store (again after a failure).
    func loadProducts() async {
        guard enabled else {
            status = .unavailable
            return
        }
        guard status != .loading, status != .loaded else { return }
        status = .loading
        do {
            let found = try await Product.products(for: GoldenFish.productIDs)
            products = Dictionary(found.map { ($0.id, $0) }, uniquingKeysWith: { first, _ in first })
            status = products.isEmpty ? .unavailable : .loaded
        } catch {
            status = .unavailable
        }
    }

    /// Buys one pack. Cancelling says nothing; waiting for approval, a failure or a purchase that
    /// cannot be verified leaves a short notice.
    func buy(_ pack: GoldenFish.Pack) async {
        guard enabled, buying == nil, let product = products[pack.productID] else { return }
        buying = pack.productID
        notice = nil
        defer { buying = nil }
        do {
            switch try await product.purchase() {
            case .success(.verified(let transaction)):
                if await deliver(transaction) {
                    let amount = (GoldenFish.amount(forProduct: transaction.productID) ?? 0)
                        * max(1, transaction.purchasedQuantity)
                    delivery = Delivery(id: (delivery?.id ?? 0) + 1, amount: amount)
                } else {
                    notice = .failed
                }
            case .success(.unverified):
                // Not signed by the App Store for this device: never credited, left unfinished.
                notice = .failed
            case .pending:
                // Ask to Buy or extra authentication: arrives later through `Transaction.updates`.
                notice = .pending
            case .userCancelled:
                break
            @unknown default:
                break
            }
        } catch {
            notice = .failed
        }
    }

    /// A transaction from the updates or unfinished streams; only verified ones are delivered.
    private func process(_ result: VerificationResult<Transaction>) async {
        guard case .verified(let transaction) = result else { return }
        await deliver(transaction)
    }

    /// Credits a verified golden fish transaction, then finishes it. Returns whether the golden fish
    /// are (now or already) in the save.
    @discardableResult
    private func deliver(_ transaction: Transaction) async -> Bool {
        guard GoldenFish.amount(forProduct: transaction.productID) != nil else { return false }
        if transaction.revocationDate != nil {
            // Refunded before it was used up: nothing to give, so just close it.
            await transaction.finish()
            return false
        }
        guard let credit, credit(String(transaction.id), transaction.productID, transaction.purchasedQuantity) else {
            return false
        }
        // Saved first, finished second: a crash in between replays it, and the id stops a double credit.
        await transaction.finish()
        return true
    }
}
