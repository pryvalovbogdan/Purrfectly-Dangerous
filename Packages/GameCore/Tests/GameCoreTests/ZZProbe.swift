import Testing
@testable import GameCore
@Test func zzProbeTurret() {
    var level = flatLevel(items: [.init(at: 600, kind: .riftTurret)], length: 1400, entry: 5, reward: 5); level.speed = 150
    var w = RunnerWorld(level: level, boss: nil, stats: HeroStats(xp: Progression.xp(forLevel: 5), maxHearts: 1))
    var bot = Bot()
    while !w.isOver, w.time < 20 {
        let input = bot.input(for: w, dt: dt)
        let threatened = !Bot.survives(w, plan: nil, horizon: Bot.reactionTime, dt: dt)
        let ev = w.step(input, dt: dt)
        let g = (w.entities.first?.x ?? 9999) - w.distance
        if g < 330, g > -40 {
            print("PROBE g", Int(g), "y", Int(w.heroY), "ground", w.onGround, "thr", threatened, "jp", input.jumpPressed, input.jumpHeld, "paw", input.pawPressed, input.pawHeld, "st", w.entities.first?.state as Any, "haz", w.hazards.map { Int($0.x - w.distance) }, ev.filter { $0 != .landed })
        }
    }
}
