import Foundation
import GameCore
import Observation

struct GameResult: Equatable {
    var won: Bool
    var score: Int
    var xp: Int
    var heroLevel: Int
    var hearts: Int
    /// Fish picked up in this level.
    var fish: Int
    /// Abilities gained during this run, in unlock order.
    var unlocked: [Ability]
}

@MainActor
@Observable
final class AppModel {
    enum Screen: Equatable {
        case menu
        /// `attempt` changes on every start so a retry builds a fresh scene.
        case playing(level: Int, attempt: Int)
        case finished(level: Int, result: GameResult)
        /// Between two levels of an endless run: the score so far and the level coming up.
        case nextLevel(level: Int)
    }

    /// The normal five worlds (`level_NN.json`).
    let baseLevels: [LevelDefinition]
    /// The cats' own routes (`route_<skin>_NN.json`), swapped in for the selected cat.
    let routes: RouteBook
    /// The levels in play order for the selected cat: its route, or the normal worlds. The LEVELS
    /// panel and the endless run both follow it; progress and bests are kept per level id.
    var levels: [LevelDefinition] { routes.levels(for: save.selectedSkin, base: baseLevels) }
    let bosses: [String: BossDefinition]
    let sprites: SpriteLibrary
    private let lore: Lore
    private let store = DefaultsSaveStore()
    /// The iCloud copy of golden fish and owned cats.
    private let cloud = CloudSync()
    /// Golden fish packs from the App Store.
    let golden = GoldenStore()
    /// Off in debug bot, silent and UI-test runs: no App Store and no iCloud there.
    private(set) var purchasesEnabled = false

    var screen = Screen.menu {
        didSet { updateMusic() }
    }
    private(set) var save: SaveGame
    /// Debug builds only: `-autoplay <level number>` starts that level with the validator bot playing,
    /// and `-autoplay endless` an endless run, so the game can be watched and screenshotted in the
    /// simulator without touch input. Those runs are silent and are not saved.
    private(set) var autoplay = false
    /// Debug builds only: `-silent` keeps every sound off, for simulator runs (Tools/run-sim.sh).
    private var silent = false
    /// Debug builds only: `-uitest-jump` plays a flat, empty copy of level 1 with real touches and no
    /// bot, for the jump-height UI test (UITests/JumpHoldUITests.swift). Never set in Release.
    private(set) var jumpTest = false
    private let music = MusicPlayer()
    /// False while the app is in the background or behind the app switcher; the music never plays then.
    private var isActive = true
    /// The endless run in progress or just ended; nil while a level is played on its own.
    private(set) var endless: EndlessRun?
    private var attempts = 0

    init(bundle: Bundle = .main) {
        do {
            baseLevels = try ContentLoader.levels(in: bundle)
            routes = try ContentLoader.routes(in: bundle)
            bosses = try ContentLoader.bosses(in: bundle)
            guard let loreURL = bundle.url(forResource: "Lore", withExtension: "json") else {
                throw ContentError.missing("Lore.json")
            }
            lore = try Lore(data: Data(contentsOf: loreURL))
            sprites = try SpriteLibrary(bundle: bundle)
        } catch {
            // The content ships inside the app; if it cannot be read the build itself is broken.
            fatalError("Game content failed to load: \(error)")
        }
        save = store.load()
        #if DEBUG
        let arguments = ProcessInfo.processInfo.arguments
        silent = arguments.contains("-silent")
        if arguments.contains("-uitest-jump") {
            jumpTest = true
            silent = true
            screen = .playing(level: 0, attempt: 0)
        }
        if let flag = arguments.firstIndex(of: "-autoplay"), arguments.indices.contains(flag + 1) {
            if arguments[flag + 1] == "endless" {
                autoplay = true
                startEndless()
            } else if let number = Int(arguments[flag + 1]), levels.indices.contains(number - 1) {
                autoplay = true
                save.unlockedLevels = levels.count
                screen = .playing(level: number - 1, attempt: 0)
            }
        }
        #endif
        purchasesEnabled = !autoplay && !silent && !jumpTest
        if purchasesEnabled { startPurchasesAndCloud() }
        updateMusic()
    }

    /// The level to play at `index`. In the debug jump test, level 1 with nothing in it: no items,
    /// ravines, platforms, slick ground or terrain, and no boss within reach, so every jump starts and
    /// ends on the same flat ground.
    func playableLevel(_ index: Int) -> LevelDefinition {
        var level = levels[index]
        #if DEBUG
        if jumpTest, !ProcessInfo.processInfo.arguments.contains("-uitest-keep-level") {
            level.items = []
            level.ravines = nil
            level.slick = nil
            level.platforms = nil
            level.terrain = nil
            level.length = 1_000_000
        }
        #endif
        return level
    }

    /// Sound effects and music play only when the player has sound on and no debug run asked for quiet.
    var soundOn: Bool { save.soundOn && !autoplay && !silent }

    /// The theme plays on the start and end screens and is quiet during play.
    private func updateMusic() {
        guard isActive else {
            music.pauseNow()
            return
        }
        switch screen {
        case .menu, .finished:
            if soundOn { music.play() } else { music.stop() }
        case .playing, .nextLevel:
            music.stop()
        }
    }

    func text(_ key: String) -> String {
        lore.text(key)
    }

    /// Interface wording: the `ui.<key>` entry of Lore.json, so every label can be reworded there. A
    /// missing key shows as itself on screen; ContentTests checks every key used in App/ exists.
    func ui(_ key: String) -> String {
        lore.text("ui.\(key)")
    }

    func isUnlocked(_ index: Int) -> Bool {
        index < save.unlockedLevels
    }

    /// On its own a level starts with saved XP, but never below what earlier bosses guarantee. In an
    /// endless run the hero is whoever left the previous level.
    func startingStats(for index: Int) -> HeroStats {
        if let endless { return endless.startingStats(for: levels[index]) }
        return HeroStats(xp: max(save.xp, Progression.xp(forLevel: levels[index].entryHeroLevel)))
    }

    func start(level index: Int) {
        guard levels.indices.contains(index), isUnlocked(index) else { return }
        endless = nil
        attempts += 1
        screen = .playing(level: index, attempt: attempts)
    }

    /// Starts an endless run from the first level with a fresh hero.
    func startEndless() {
        let run = EndlessRun(levelCount: levels.count)
        endless = run
        attempts += 1
        screen = .playing(level: run.levelIndex, attempt: attempts)
    }

    func finish(level index: Int, result: GameResult) {
        // Every level that ends, won or lost, on its own or in an endless run, banks its fish.
        if !autoplay, result.fish > 0 {
            save.addFish(result.fish)
            store.save(save)
        }
        guard var run = endless else {
            if result.won, !autoplay {
                save.complete(levelID: levels[index].id, score: result.score, xp: result.xp)
                store.save(save)
            }
            screen = .finished(level: index, result: result)
            return
        }
        if result.won {
            var hero = HeroStats(xp: result.xp)
            hero.hearts = result.hearts
            run.clear(stats: hero, score: result.score)
        } else {
            run.end(score: result.score)
        }
        endless = run
        record(run)
        screen = run.isOver ? .finished(level: index, result: result) : .nextLevel(level: run.levelIndex)
    }

    /// Leaves the next-level screen of an endless run and starts that level.
    func continueEndless() {
        guard case .nextLevel(let index) = screen, endless != nil else { return }
        attempts += 1
        screen = .playing(level: index, attempt: attempts)
    }

    /// Back to the menu from anywhere; an endless run left part-way keeps what it had banked.
    func quit() {
        if let endless { record(endless) }
        endless = nil
        screen = .menu
    }

    private func record(_ run: EndlessRun) {
        guard !autoplay else { return }
        save.recordEndless(score: run.score, cleared: run.cleared, total: levels.count)
        store.save(save)
    }

    /// Called as the app comes to the front or leaves it.
    func setActive(_ active: Bool) {
        guard active != isActive else { return }
        isActive = active
        updateMusic()
    }

    // MARK: - Cats shop (rules and save in GameCore: `Skin`, `SaveGame.unlock` / `select`)

    /// Fish banked from every run, to spend on cats.
    var fishWallet: Int { save.fishWallet }
    /// Cats the player owns, by id (always includes the free one).
    var ownedSkins: Set<String> { save.ownedSkins }
    /// The cat in use, by id.
    var selectedSkin: String { save.selectedSkin }

    /// Golden fish to spend (bought with real money; see `GoldenStore`).
    var goldenFish: Int { save.goldenFish }

    /// Buys a cat with fish from the wallet or with golden fish; saved (and backed up) when it works.
    @discardableResult
    func unlockSkin(_ id: String, with currency: Currency = .fish) -> SkinUnlock {
        let result = save.unlock(skin: id, with: currency)
        if result == .unlocked { persistBackedUp() }
        return result
    }

    /// Picks the cat to play as; only an owned one. Returns whether it is now the one in use.
    @discardableResult
    func selectSkin(_ id: String) -> Bool {
        guard save.selectedSkin != id else { return save.owns(id) }
        guard save.select(skin: id) else { return false }
        store.save(save)
        return true
    }

    /// Every cat the shop offers, by neutral id, in shop order; the first is everyone's from the start.
    static let skins = Skin.catalog.map(\.id)

    // MARK: - Golden fish and iCloud (rules in GameCore: `GoldenFish`, `SaveGame.creditGolden` / `merge`)

    /// From launch: merge the iCloud copy in, follow later changes to it, and listen for App Store
    /// transactions (including ones that finished while the app was closed).
    private func startPurchasesAndCloud() {
        cloud.start { [weak self] remote in self?.mergeCloud(remote) }
        if let remote = cloud.read() {
            mergeCloud(remote)
        } else {
            cloud.write(save.cloudBackup)
        }
        golden.start { [weak self] transaction, product, quantity in
            self?.creditGolden(transaction: transaction, product: product, quantity: quantity) ?? false
        }
    }

    /// Credits a verified App Store transaction once, saves, and backs up. True when the golden fish
    /// are in the save (just now or from before), so the transaction can be finished.
    private func creditGolden(transaction: String, product: String, quantity: Int) -> Bool {
        guard let amount = GoldenFish.amount(forProduct: product) else { return false }
        if save.creditGolden(transaction: transaction, amount: amount * max(1, quantity)) {
            persistBackedUp()
        }
        return save.hasCredited(transaction: transaction)
    }

    /// Takes in a copy from iCloud (union, never removes) and writes the result back if it has more.
    private func mergeCloud(_ remote: CloudBackup) {
        if save.merge(remote) { store.save(save) }
        if save.cloudBackup != remote { cloud.write(save.cloudBackup) }
    }

    /// Saves on the phone, then copies the golden fish and cats to iCloud.
    private func persistBackedUp() {
        store.save(save)
        if purchasesEnabled { cloud.write(save.cloudBackup) }
    }

    func setSound(on: Bool) {
        save.soundOn = on
        store.save(save)
        updateMusic()
    }
}
