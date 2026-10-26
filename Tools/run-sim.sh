#!/bin/bash
# Builds the app, installs it on an iPhone simulator, launches it and saves screenshots.
# Usage: [ORIENT=landscape|portrait] [CATS=<cat id>] Tools/run-sim.sh [level number or "endless" for bot autoplay] [seconds ...]
#   Tools/run-sim.sh              -> menu screenshot
#   CATS=sharky Tools/run-sim.sh  -> the CATS screen on that cat
#   Tools/run-sim.sh 1 4 20 40    -> level 1 played by the bot, shots after 4 s, 20 s and 40 s
#   Tools/run-sim.sh endless 60   -> an endless run played by the bot, shot after 60 s
set -euo pipefail
cd "$(dirname "$0")/.."

DEVICE="${SIM_DEVICE:-$(xcrun simctl list devices available | grep -E '^\s+iPhone' | tail -1 | grep -oE '[0-9A-F-]{36}')}"
OUT=.build/screens
ORIENT="${ORIENT:-landscape}"
CATS_ARGS=()
[ -n "${CATS:-}" ] && CATS_ARGS=(-cats "$CATS")
TAG="${CATS:+cats_${CATS}_}"
mkdir -p "$OUT"

Tools/xcodegen.sh >/dev/null
xcodebuild -project PurrfectlyDangerous.xcodeproj -scheme PurrfectlyDangerous -configuration Debug \
  -destination "platform=iOS Simulator,id=$DEVICE" -derivedDataPath .build/xcode build \
  2>&1 | grep -E 'error:|BUILD (SUCCEEDED|FAILED)' || true
APP=.build/xcode/Build/Products/Debug-iphonesimulator/PurrfectlyDangerous.app
[ -d "$APP" ] || { echo "build failed: $APP missing"; exit 1; }

xcrun simctl bootstatus "$DEVICE" -b >/dev/null
xcrun simctl install "$DEVICE" "$APP"
xcrun simctl terminate "$DEVICE" com.pryvalov.purrfectlydangerous 2>/dev/null || true

LEVEL="${1:-}"
if [ -n "$LEVEL" ]; then
  shift
  xcrun simctl launch "$DEVICE" com.pryvalov.purrfectlydangerous -autoplay "$LEVEL" -orientation "$ORIENT" -silent ${CATS_ARGS[@]+"${CATS_ARGS[@]}"} >/dev/null
  PREVIOUS=0
  for AT in "${@:-4}"; do
    sleep $((AT - PREVIOUS)); PREVIOUS=$AT
    xcrun simctl io "$DEVICE" screenshot "$OUT/${TAG}level${LEVEL}_${ORIENT}_${AT}s.png" >/dev/null 2>&1
    echo "$OUT/${TAG}level${LEVEL}_${ORIENT}_${AT}s.png"
  done
else
  xcrun simctl launch "$DEVICE" com.pryvalov.purrfectlydangerous -orientation "$ORIENT" -silent ${CATS_ARGS[@]+"${CATS_ARGS[@]}"} >/dev/null
  sleep 3
  xcrun simctl io "$DEVICE" screenshot "$OUT/${TAG}menu_${ORIENT}.png" >/dev/null 2>&1
  echo "$OUT/${TAG}menu_${ORIENT}.png"
fi
