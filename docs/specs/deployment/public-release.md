# Public release runbook (the flip)

Executed once, in one owner session, for `IMP-M21-10` (decisions D4–D9, D12 in the registry). The agent runs
the API steps below only after the owner confirms each in-session; steps marked **Owner** have no API.
Tick a step by replacing `[ ]` with `[x]`, the date, and the `gh api` read that confirmed it.

**Freeze:** nothing lands in any repository from step 2 until step 4 is done.

## Steps

- [x] **1. Gate.** `scripts/preflip-check.sh` exits 0 and `scripts/repo-settings.sh --check` reports no drift. *2026-11-07: `preflip-check: PASS (8 repositories)`; `repo-settings.sh --check`: `OK no drift`; `gh repo view` reports PRIVATE for all 8.*
- [x] **2. Flip (Owner).** *2026-11-07, by `gh repo edit --visibility public` in the order below; `gh repo view` prints PUBLIC for all 8.* Settings → Danger zone → Change visibility → Public, in this order:
  `turnbase-sdk`, `turnbase-common`, `turnbase-game-tictactoe`, `turnbase-game-host`, `turnbase-platform`,
  `turnbase-frontend`, `.github`, then the umbrella `turnbase` last (its links never point at a private
  repository). `turnbase-game-7wonders-duel` stays private (D9, `IMP-M21-09`).
  Confirm: `gh repo view turnbase-platform/<repo> --json visibility -q .visibility` prints `PUBLIC` for each.
- [x] **3. Hardening.** *2026-11-07, `repo-settings.sh --apply --harden`; `--check --harden` left Pages (no `gh-pages` branch yet) and 7WD (private, D9); Pages enabled after step 5 and `--check --harden` then leaves 7WD only.* `scripts/repo-settings.sh --apply --harden` (needs public repositories). It sets, per
  repository: secret scanning and push protection; private vulnerability reporting; Dependabot alerts on,
  security updates off (`conventions.md` §6); CodeQL default setup (Java, JavaScript/TypeScript); ruleset
  `master-protect` (no force push, no deletion, no required PRs); read-only default `GITHUB_TOKEN`; fork-PR
  workflows needing approval; Pages on `gh-pages` for common and sdk.
  Confirm: `scripts/repo-settings.sh --check --harden` reports no drift.
- [x] **3b. GHCR (Owner).** *2026-11-07, `gh api orgs/turnbase-platform/packages/container/<name> -q .visibility` prints `public` for platform, game-host and frontend.* Package settings → visibility Public for the platform, game-host and frontend
  images (web UI only).
- [x] **4. Drop the PAT.** *2026-11-07, platform `9d17128`, game-host `b3b12f8`, tictactoe `cbf9a82`; `build` green on all three; the dry-run `publish` is green in common and sdk.* In `turnbase-platform`, `turnbase-game-host`, `turnbase-game-tictactoe` the bootstrap
  clone of `turnbase-sdk` (and `turnbase-common` where cloned) drops `x-access-token:${TURNBASE_SDK_PAT}@`;
  the `TURNBASE_SDK_PAT` env entries go too. Land on `master` per repository; every `master` run is green
  before anything else lands. (The secret itself is deleted by `IMP-M21-11`.)
- [x] **5. Release (Owner).** *2026-11-07, `v0.1.0` pushed with `git` in common and sdk; the first attempt failed in `publish` (gh-pages bootstrap had no git identity, nothing published), fixed in common `d9ffa9d` and sdk `e783875`, tags re-cut; both `publish` runs green; `curl -fsI` on both `0.1.0` poms returns HTTP/2 200 anonymously.* Tag `v0.1.0` in `turnbase-common` and `turnbase-sdk`; both `publish.yml` runs
  succeed. Confirm the artifacts resolve anonymously from Pages:
  `curl -fsI https://turnbase-platform.github.io/<repo>/…/0.1.0/<artifact>-0.1.0.pom`.

## Done when

Every step is ticked with its date and read; `gh repo view` reports PUBLIC for each flipped repository; CI is
green on every `master`.
