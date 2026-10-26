import SwiftUI
import UIKit

/// Up while a level is built and its textures decoded: the level's name over the painted loading bar
/// (`loading_bar`, its track and its striped fill, cut by `LOADING_CUTS` in Tools/sprites/export.py). The
/// fill slides in along the track from under the paw, reaching `progress` (0…1) in `seconds`.
struct LoadingScreen: View {
    let title: String
    let progress: Double
    let seconds: Double

    @Environment(\.verticalSizeClass) private var verticalSizeClass

    var body: some View {
        let width: CGFloat = verticalSizeClass == .compact ? 320 : 300
        ZStack {
            Color.menuInk.ignoresSafeArea()
            VStack(spacing: 16) {
                PixelTitle(text: title, size: 30, alignment: .center)
                LoadingBar(progress: progress, seconds: seconds)
                    .frame(width: width, height: width * LoadingBar.Bar.size.height / LoadingBar.Bar.size.width)
            }
            .padding(.horizontal, 16)
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(title)
        .accessibilityValue("\(Int((progress * 100).rounded())) %")
    }
}

/// The bar itself, in UIKit: the scene's build holds the main thread while the screen is up, which
/// freezes a SwiftUI animation, but a Core Animation one keeps moving on its own.
private struct LoadingBar: UIViewRepresentable {
    let progress: Double
    let seconds: Double

    func makeUIView(context: Context) -> Bar { Bar() }

    func updateUIView(_ bar: Bar, context: Context) {
        bar.fill(to: progress, seconds: seconds)
    }

    final class Bar: UIView {
        /// The painting is 361×125; its track runs x 92…311 and the fill (257×31) sits in it at y 48.
        static let size = CGSize(width: 361, height: 125)
        private static let track = 92.0...311.0
        private static let fillSize = CGSize(width: 257, height: 31)
        private static let fillTop = 48.0

        private let frameView = Bar.pixelImage("loading_bar")
        private let fillView = Bar.pixelImage("loading_bar_fill")
        /// Holds the fill, cut to the track's shape so it stays off the paw and the rim.
        private let trackView = UIView()
        private let trackMask = Bar.pixelImage("loading_bar_track")
        private var progress = 0.0
        /// A fill asked for before the bar had a size: run once it is laid out, from the empty bar.
        private var pendingSeconds: Double?

        override init(frame: CGRect) {
            super.init(frame: frame)
            isUserInteractionEnabled = false
            addSubview(frameView)
            addSubview(trackView)
            trackView.addSubview(fillView)
            trackView.mask = trackMask
        }

        @available(*, unavailable)
        required init?(coder: NSCoder) {
            fatalError("init(coder:) is not used")
        }

        private static func pixelImage(_ name: String) -> UIImageView {
            let view = UIImageView(image: UIImage(named: name))
            view.layer.magnificationFilter = .nearest
            return view
        }

        private var scale: CGFloat { bounds.width / Self.size.width }

        private func fillFrame(at progress: Double) -> CGRect {
            let right = Self.track.lowerBound + progress * (Self.track.upperBound - Self.track.lowerBound)
            return CGRect(x: (right - Self.fillSize.width) * scale, y: Self.fillTop * scale,
                          width: Self.fillSize.width * scale, height: Self.fillSize.height * scale)
        }

        override func layoutSubviews() {
            super.layoutSubviews()
            frameView.frame = bounds
            trackView.frame = bounds
            trackMask.frame = bounds
            if let seconds = pendingSeconds, bounds.width > 0 {
                pendingSeconds = nil
                fillView.frame = fillFrame(at: 0)
                animateFill(seconds: seconds)
            } else if fillView.layer.animationKeys() == nil {
                fillView.frame = fillFrame(at: progress)
            }
        }

        func fill(to target: Double, seconds: Double) {
            guard target != progress else { return }
            progress = target
            if bounds.width > 0 { animateFill(seconds: seconds) } else { pendingSeconds = seconds }
        }

        private func animateFill(seconds: Double) {
            UIView.animate(withDuration: seconds, delay: 0, options: [.curveEaseOut, .beginFromCurrentState]) {
                self.fillView.frame = self.fillFrame(at: self.progress)
            }
        }
    }
}
