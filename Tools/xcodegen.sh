#!/bin/bash
# Generates PurrfectlyDangerous.xcodeproj from project.yml with the private settings from `.env`
# (kept out of git; copy `.env.example` to `.env` and fill it in). Variables already set in the
# environment win over the file, so CI can pass them directly.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env ]; then
  while IFS='=' read -r key value; do
    [[ -z "$key" || "$key" == \#* ]] && continue
    [ -z "${!key:-}" ] && export "$key=$value"
  done < .env
fi
: "${DEVELOPMENT_TEAM:?set DEVELOPMENT_TEAM in .env (see .env.example)}"

xcodegen generate "$@"
