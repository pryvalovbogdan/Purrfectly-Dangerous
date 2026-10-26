#!/bin/bash
# Generates PurrfectlyDangerous.xcodeproj from project.yml with the private settings from `.env`
# (Tools/env.sh).
set -euo pipefail
cd "$(dirname "$0")/.."

source Tools/env.sh
: "${DEVELOPMENT_TEAM:?set DEVELOPMENT_TEAM in .env (see .env.example)}"

xcodegen generate "$@"
