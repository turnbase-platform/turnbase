## Last Session Summary

**Date:** 2026-11-05 (session 264) — **`IMP-M20-05` done: code→spec references are checked. 215 of 232 items done.**

- New `code-refs` check in `scripts/check-corpus.py` (9th): every `*.md` file and `<file>.md §N` named in a submodule's tracked non-markdown source must resolve against the corpus or the repository's own documents; `target/…` output is not a reference. `scripts/test-code-refs.py` plants a bad file and two bad `§` references and asserts each fails.
- Fixed in `turnbase-platform` (comments/paths only): `FR-AUTH-005/input-validation.md` joined by a slash, a `room-lifecycle.md` split across a wrapped line, the M18 report path, and two `Path.of("target", "x.md")` outputs. The frontend's three were CSS class selectors, not references.
- `verify` green; the two touched ITs ran and wrote their reports. No CI (billing).

## Current State

- **Phase 1, M20 (refinement) open**: 17 of 22 items remain. M0–M19 are closed (archived under `docs/implementation/archive/`).
- **Red / not run:** CI is refused for billing, so every item is judged locally (`spotless:apply`, `verify`, `verify -Pintegration`). Nothing else is known red.
- **Owner-held:** CI billing (or the public flip); the 7WD bootstrap secret (re-check live before reporting it); the Repos Production reply, which decides whether 7WD ships under its name.

## Next Priorities

- `07`, `08`, `13`, `15`, `17`, `18`, `19`, `20`, `21` have no open dependency; `06` is unblocked. Keep the maps current: `check-corpus.py code-maps` fails on a renamed class they name.
- After M20: M21 public release (licence, README, gitleaks, published artifacts), M22 cloud deployment (ADR-0021 from `IMP-M20-15` first), then Phase C.

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
