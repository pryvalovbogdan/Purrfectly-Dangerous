# Releasing

Every merge to `main` runs `.github/workflows/release.yml` on the self-hosted Mac runner:

1. `Tools/check.sh`: game rules, every level beatable, art tests, simulator build. Any failure stops the run.
2. `Tools/bump-build.sh`: build number (`CURRENT_PROJECT_VERSION` in `project.yml`) + 1.
3. `Tools/release.sh`: `Tools/release-check.sh`, then a signed Release archive uploaded to App Store
   Connect. A few minutes later it is in TestFlight.
4. The new build number is committed to `main` as `Build N [skip ci]`.

Sending a build to App Store review is still done by hand in App Store Connect: pick the build on
the version page, then Submit for Review. The marketing version (`MARKETING_VERSION`, e.g. 1.0.0) is
also raised by hand in `project.yml` when a new App Store version starts.

The same release works without CI, from this Mac, with the key's settings in `.env` (see
`.env.example`: `ASC_KEY_ID`, `ASC_ISSUER_ID`, `ASC_KEY_PATH`):

```
Tools/check.sh && Tools/bump-build.sh && Tools/release.sh
```

Every secret lives in one of two places, never in the repo: `.env` on this Mac (git ignores it; the
scripts read it through `Tools/env.sh`), and GitHub secrets in CI, which the workflow passes to the
same scripts as environment variables.

## One-time setup

### App Store Connect API key

App Store Connect → Users and Access → Integrations → App Store Connect API → **Team Keys** (not
Individual Keys: those cannot manage certificates and profiles) → Generate API Key with the **Admin**
role, which automatic signing needs to create the cloud-managed distribution certificate. Note its **Key ID** and the **Issuer ID** at the top
of the page, and download the `.p8` file (it can be downloaded only once). Xcode uses the key to
sign automatically: it creates the distribution certificate and profile itself.

### GitHub secrets

Repository → Settings → Secrets and variables → Actions → New repository secret:

| Secret | Value |
| --- | --- |
| `DEVELOPMENT_TEAM` | the team id, as in `.env` |
| `ASC_KEY_ID` | the key's Key ID |
| `ASC_ISSUER_ID` | the Issuer ID |
| `ASC_KEY_P8` | the whole text of the `.p8` file, including the `BEGIN`/`END PRIVATE KEY` lines |

### Self-hosted runner on this Mac

Repository → Settings → Actions → Runners → New self-hosted runner → macOS, and follow the commands
it shows (download, `./config.sh …`). Then install it as a service so it runs without a terminal:

```
./svc.sh install && ./svc.sh start
```

The runner needs `xcodegen` and `python3` on its `PATH`. It records the `PATH` from when `config.sh`
ran (in the runner folder's `.path` file); if Homebrew's `/opt/homebrew/bin` is missing there, add
it and restart the service. The Mac must be awake and online for a merge to release.

### Pushing the build number to `main`

The workflow pushes with the built-in `GITHUB_TOKEN`. If `main` is protected so that only pull
requests may change it, allow GitHub Actions to bypass that rule (Settings → Rules), or the last
step fails after the upload. The build is then in TestFlight, but `project.yml` still has the old
number: raise it by hand before the next merge.
