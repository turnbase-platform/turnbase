## Last Session Summary

**Date:** 2026-06-30

**Wrote the game manifest schema spec** (FR-MANIFEST-001–009) — the single source of
truth for game metadata, now unblocking the bundle/upload-pipeline spec.

- New `docs/specs/manifest/` directory with three files:
  - **`manifest.schema.json`** — normative JSON Schema (Draft 2020-12), the contract
    shared by the platform upload validator and the local test harness (FR-HARNESS-002)
    so the two cannot drift. Verified valid Draft 2020-12; the annotated example
    validates clean and negative cases (bad version, missing per-type parameter fields,
    bad `key` pattern, >10 tags, wrong `manifestVersion`) are correctly rejected, while
    an unknown key is correctly **accepted** (lenient).
  - **`manifest-schema.md`** — field semantics, two-layer validation, lenient
    unknown-key warnings, error model, and FR-MANIFEST traceability.
  - **`INDEX.md`** — subdir entry point + key decisions.
- **Decisions made this session** (via brainstorming): formal JSON Schema artifact (not
  prose); `manifestVersion` field (`"1"`, rejects unknown) independent of
  `gdkApiVersion`; **lenient unknown keys** surfaced as non-fatal warnings (not
  rejected); runtime-agnostic `backend` (`path` + `entryPoint`, FQCN under `jvm`);
  validation boundary = **manifest-in-isolation** (path existence, entry-class,
  GDK-class conflict, version ordering, size limits all deferred to the upload-pipeline
  spec); errors reuse the `error-handling.md` `{check, message}` 422 shape, with a new
  separate `warnings` array for non-fatal items.
- **Decided rather than asked** (flagged to user): `title` cap = 60 chars; the new
  `warnings` array on the validation response.

**Files changed:**
- `docs/specs/manifest/manifest.schema.json` — new (normative JSON Schema)
- `docs/specs/manifest/manifest-schema.md` — new (prose spec)
- `docs/specs/manifest/INDEX.md` — new (subdir index)
- `docs/specs/INDEX.md` — registered the new `manifest/` subdirectory
- `docs/requirements/game-development-experience.md` — linked the manifest spec under Related API Specifications

---

## Next Priorities

- **Game bundle format + upload pipeline** (FR-BUNDLE-*, FR-UPLOAD-*) — **recommended
  next**; now unblocked by the manifest schema. Owns the validation the manifest spec
  explicitly deferred: archive structure, path existence (FR-UPLOAD-003), entry-class
  implements `TurnBaseGame` (FR-UPLOAD-004), GDK-class conflict (FR-UPLOAD-005), version
  ordering (FR-UPLOAD-006), bundle size (FR-UPLOAD-007).
- **Test harness** (FR-HARNESS-*) — depends on manifest schema (reuses
  `manifest.schema.json`); has open distribution questions (OQ-001/002) to resolve first.
- **Platform-frontend shell spec** (not yet written) — must inject and honor the FE
  bootstrap contract `window.__TURNBASE__ = { parentOrigin, sessionId }` (CON-006),
  authoritatively defined in `frontend-gdk-api.md §9`.
- **GDK spec open questions** to revisit when real games exercise them: generic action payloads & enum-typed parameters (backend); reconnection re-init and multi-listener events (frontend).

---

## Coverage Summary

| Document | Coverage |
|----------|----------|
| `user-accounts.md` | Registration, auth, sessions, account management, profiles, guests, per-section privacy settings, block-requests toggle |
| `game-rooms.md` | Room list, creation, joining, host management, teams, readiness, lifecycle, mid-game join assignment |
| `game-catalog.md` | Catalog listing, game detail, game management, profile games tab |
| `notifications-invitations.md` | Alerts, notification center, invitations, friend request notifications |
| `reconnection-flow.md` | Disconnect detection, grace period, re-entry, kick mechanics |
| `in-room-chat.md` | Room/team channels, messaging, delivery model, late-join team chat access |
| `per-game-statistics.md` | Session counting, game detail stats, profile stats |
| `platform-views.md` | All views, navigation, redirects, auth tier gating |
| `game-development-experience.md` | GDK, game packaging, upload pipeline, local dev workflow |
| `game-contracts.md` | Platform ↔ game BE/FE protocol, effect types, structured outcome, postMessage API |
| `platform-architecture.md` | Game execution infrastructure, Game Host, Orchestration Service, sandboxing, scaling |
| `game-history.md` | Per-session history recording, win condition labels, profile history tab, privacy |
| `social-friends.md` | Friendship model, request lifecycle, friend cap, discovery, visibility, guest exclusion, block-requests toggle |
| `platform-operations.md` | Service topology (monolith), availability, observability stack, CI/CD pipeline, data retention |
| `onboarding-wizard.md` | First-time wizard overlay, pane structure, localStorage suppression, landing page re-entry |
| `admin-tooling.md` | Internal admin API, game badge model (Official/Verified/Unverified), review queue, private game behaviour |

---

## Open Questions Remaining in Existing Docs

| Document | Open Question |
|----------|---------------|
| `reconnection-flow.md` | Game engine response set after "player lost" event — deferred to Game SDK contracts |
| `game-history.md` | OQ-002: Pagination reuse — shared UI component vs. API pattern deferred to implementation |
| `game-contracts.md` | OQ-001: Log color annotation syntax — deferred to GDK spec |
| `game-contracts.md` | OQ-002: AI/bot player interface — deferred to future spec |
| `game-contracts.md` | OQ-003: Platform-managed timer system — deferred to future spec |
| `admin-tooling.md` | OQ-001: Can a developer resubmit a rejected game, or is rejection terminal? |
| `admin-tooling.md` | OQ-002: Can an operator delist a Verified or Official game post-approval? |
