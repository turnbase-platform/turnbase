## Last Session Summary

**Date:** 2026-07-11 (session 4)

**Wrote the Game Host & Execution Internals spec** (review "New spec documents" #4; STATUS priority
#3), now unblocked by the Espresso spike (ADR-0005) and trust model (ADR-0006). Ran it through the
brainstorming + requirements-engineering cadence; four owner decisions were taken, then three
cross-doc contradictions the spec surfaced were reconciled.

**Owner decisions taken this session:**
1. **Runtime model = Espresso in a hardened container** — one GraalVM CE 21 host JVM per pod, one
   Espresso context per game-version, sessions multiplex. Keeps the Truffle showcase + FR-CTX-012
   polyglot roadmap. (Alternatives rejected: plain-JVM-per-process, context-per-session.)
2. **Canonical state = serialized JSON** held in host memory + Redis; guest (de)serializes per
   invocation. Serialization engine is a **shared component** with the test harness/upload validator
   → structural GRMP-F4 round-trip test.
3. **Concurrent sessions + accepted interrupt caveat** — per-session single-flight, cross-session
   concurrency; `Context.interrupt` is context-scoped, so a timeout may abort a concurrent sibling
   (re-dispatched, state uncommitted). Documented, not hidden.
4. **One `TurnBaseGame` instance per session**; spec covers **both sides end-to-end** (Game Host +
   Orchestration execution pipeline), stopping at the WS Gateway seam (STOMP left to GAME-B1).

**Blockers closed:** GAME-I1/I2 (internals), **GAME-B2** (atomic Redis session record
`{stateJson, lastAppliedSequence, lastEffects}` + idempotent `CreateSession` + `sequence`-replay →
exactly-once application), execution half of **GAME-B1** (effect fan-out FR-DELIVER). Captured spike
follow-ups (ship JDK 21 guest via `java.JavaHome`; drop `IOAccess.NONE`/`MaxHeapMemory` as
enforcement; container provides FS/net/memory). Four OQs carried.

**Three contradictions reconciled (owner-approved, all edited now):**
- **GAME-M4** — swept `stdin/stdout` → in-process polyglot invocation across 6 references.
- **GAME-I5** — game `parameters` reframed from "opaque, never-inspected" to a platform-materialized
  manifest-keyed JSON map (proto comment + protocol doc corrected).
- **I/O denial** — `CON-005` / backend-gdk §9 reframed: "no FS/network" is a trusted-author contract
  obligation enforced at the **container layer**, not an in-JVM sandbox exception (spike reality).

**Files changed:**
- `docs/specs/game-host/game-host-internals.md` — **new** (the spec)
- `docs/specs/game-host/INDEX.md` — **new**; registered in `docs/specs/INDEX.md`
- `docs/requirements/platform-architecture.md` — game-host spec back-link; NFR-SEC-002 sweep
- `docs/requirements/game-contracts.md` — Game Host term, CON-001, CON-005, out-of-scope sweeps
- `docs/requirements/game-development-experience.md` — GDK Host term, FR-GDK-015 sweeps
- `docs/specs/internal-grpc/{INDEX.md,gamehost.proto,orchestration-gamehost-protocol.md}` — back-link
  + `parameters` model correction
- `docs/specs/gdk-api/backend-gdk-api.md` — §1 in-process ref, §9 I/O-denial reframe
- `STATUS.md` — this update

---

## Next Priorities

Continue the review's action plan (`docs/reviews/2026-07-02-mvp-readiness/INDEX.md`):

1. **Owner decisions** — ✅ done (ADR-0001…0005, 2026-07-10).
2. **Espresso feasibility spike** (ADR-0005) — ✅ done (2026-07-11). Outcome: untrusted Java not
   isolable in-JVM on CE → **ADR-0006** scopes MVP to official-only Java. Game Host isolation for the
   MVP = interrupt timeouts + container memory limit (no adversarial in-JVM enforcement).
3. **Game Host internals spec** — ✅ done (2026-07-11, session 4). Espresso-in-hardened-container;
   `docs/specs/game-host/game-host-internals.md`. Closed GAME-I1/I2, GAME-B2, exec-half of GAME-B1;
   reconciled GAME-M4, GAME-I5, and the I/O-denial contradiction.
4. **Remaining blocker spec fixes** — WS abuse controls (API-1/2); **game-session WebSocket spec
   (GAME-B1 client half)** — per-team topics, `/user/queue/game`, STOMP event catalogue,
   `sequence`-based client dedup, deliver-on-subscribe replay, action-send authorization (the seam
   this session's spec stops at); FE serving origin/CSP (GAME-B3).
4. **New specs (mostly rescoped local-first):** local deployment & infrastructure spec (Docker
   Desktop K8s + compose per ADR-0001), data-operations spec (Postgres/Redis local, accepted
   game-state loss window — OPS-4), secrets & config spec, Game Host internals spec (after spike),
   game-session WebSocket spec (GAME-B1), `input-validation.md` (API-6).
5. **Existing-doc edit checklist cluster** (review §): game-rooms/reconnection grace timers as
   persisted deadlines (GRMP-F2/F3), platform-operations reconciliation sweep (GRMP-F1) +
   Dependabot/Trivy + frontend in FR-CICD-001, rest-conventions authz/IDOR, rate-limiting WS tier,
   gRPC proto edits (incl. `left` reason value), platform-ui-library additions.
6. **Then** the previously planned queue: game bundle format + upload pipeline, test harness,
   platform-frontend shell spec (must fail closed on trust level — GRMP-F5).

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
| `game-history.md` | Per-session history recording, win condition labels, profile history tab, privacy, deletion pseudonymization |
| `social-friends.md` | Friendship model, request lifecycle, friend cap, discovery, visibility, guest exclusion, block-requests toggle |
| `platform-operations.md` | Service topology (monolith), availability, observability stack, CI/CD pipeline, data retention |
| `onboarding-wizard.md` | First-time wizard overlay, pane structure, localStorage suppression, landing page re-entry |
| `admin-tooling.md` | Internal admin API, game badge model (Official/Verified/Unverified), review queue, private game behaviour |

**Decisions:** `docs/decisions/` — ADR-0001 (local-first platform), ADR-0002 (WS room affinity),
ADR-0003 (availability), ADR-0004 (erasure pseudonymization), ADR-0005 (sandbox / Espresso spike),
ADR-0006 (game trust model — official-only Java for MVP).

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
