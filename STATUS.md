## Last Session Summary

**Date:** 2026-11-07 (session 284) — **M20 closed and archived; the missed spots of its review fixed.**

- **`*.localhost` in the platform's tests** (`turnbase-platform` 53758f6): `GameAssetControllerIT` and one `SeedDataIT` test failed locally because this machine's resolver (`files dns`, WSL 2) sends `*.localhost` to DNS (~15 s, then fail); CI's systemd-resolved answers it. A test-scoped `InetAddressResolverProvider` answers loopback (RFC 6761). `verify -Pintegration` green: 301 unit, 381 IT; integration **279.8 s**, 46% of the 614.5 s baseline, so `IMP-M20-10`'s "at most half" is now met.
- **Language servers:** `typescript-lsp` kept. `jdtls-lsp` tried and **disabled**: it worked, but it builds into Maven's own `target/classes` and broke a concurrent `verify` (34 failures). `CLAUDE.md` *Language servers* says how to re-enable it.
- **7WD CI green** for the first time, once the owner added `TURNBASE_SDK_PAT`.
- M20 moved to `docs/implementation/archive/M20-refinement.md`; `CLAUDE.md` no longer calls 7WD a skeleton.

## Current State

- **Phase 1; no milestone open.** M0–M20 are closed and archived under `docs/implementation/archive/`.
- **CI runs again.** Latest `master` runs are green in common, sdk, game-host, platform, frontend and 7WD.
- **Known noise, not failures:** jdtls diagnostics list Jackson 3 deprecations (`asText()`, `isTextual()`) in about ten platform classes; the build does not warn about them.
- **Owner-held:** the Repos Production reply, which decides whether 7WD ships under its name.

## Next Priorities

- **Plan M21, the public release** (spike `RS-01`, `03`, `04`, `06`, `12`): licence for every repository (the owner's choice, needed first), an umbrella `README.md`, repository descriptions and topics, a gitleaks scan before the flip, `turnbase-common`/`turnbase-sdk` published so consumers need no PAT, then the visibility flip.
- Then M22, cloud deployment (from ADR-0021), then Phase C (`docs/specs/backlog.md` *Load-test findings*).

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
