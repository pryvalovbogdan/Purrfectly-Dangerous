#!/bin/bash
# Raises the build number (CURRENT_PROJECT_VERSION in project.yml) by one and prints the new number.
# App Store Connect refuses a build number it already has, so every upload needs a new one.
set -euo pipefail
cd "$(dirname "$0")/.."
current=$(sed -n 's/^ *CURRENT_PROJECT_VERSION: "\([0-9]*\)"$/\1/p' project.yml)
[ -n "$current" ] || { echo "no CURRENT_PROJECT_VERSION in project.yml" >&2; exit 1; }
next=$((current + 1))
sed -i '' "s/CURRENT_PROJECT_VERSION: \"$current\"/CURRENT_PROJECT_VERSION: \"$next\"/" project.yml
echo "$next"
