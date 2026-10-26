#!/bin/bash
# Archives the Release build and uploads it to App Store Connect, where it shows up in TestFlight.
# Run Tools/check.sh and Tools/bump-build.sh first. Signing is automatic, with an App Store Connect API
# team key with the Admin role (see docs/release.md):
#   ASC_KEY_ID, ASC_ISSUER_ID     the key's id and the issuer id (App Store Connect → Users and Access → Integrations)
#   ASC_KEY_PATH                  the key's .p8 file
#   DEVELOPMENT_TEAM              the signing team
# all from the environment or `.env` (Tools/env.sh; see .env.example).
# The GitHub workflow (.github/workflows/release.yml) runs this on every merge to main; see docs/release.md.
set -euo pipefail
cd "$(dirname "$0")/.."
source Tools/env.sh
: "${ASC_KEY_ID:?set ASC_KEY_ID in .env}" "${ASC_ISSUER_ID:?set ASC_ISSUER_ID in .env}" "${ASC_KEY_PATH:?set ASC_KEY_PATH in .env}"
ASC_KEY_PATH="${ASC_KEY_PATH/#\~/$HOME}"

Tools/release-check.sh

OUT=.build/release
rm -rf "$OUT"
AUTH=(-allowProvisioningUpdates -authenticationKeyPath "$ASC_KEY_PATH"
      -authenticationKeyID "$ASC_KEY_ID" -authenticationKeyIssuerID "$ASC_ISSUER_ID")

echo "── archive"
xcodebuild archive -project PurrfectlyDangerous.xcodeproj -scheme PurrfectlyDangerous -configuration Release \
  -destination "generic/platform=iOS" -archivePath "$OUT/PurrfectlyDangerous.xcarchive" "${AUTH[@]}" -quiet

echo "── upload to App Store Connect"
xcodebuild -exportArchive -archivePath "$OUT/PurrfectlyDangerous.xcarchive" \
  -exportOptionsPlist Tools/ExportOptions.plist -exportPath "$OUT/export" "${AUTH[@]}" -quiet

echo "Uploaded. The build appears in TestFlight once App Store Connect has processed it."
