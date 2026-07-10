## Last Session Summary

**Date:** 2026-07-10 (session 2)

**Ratified the six strategic owner decisions** from the MVP readiness review
(`docs/reviews/2026-07-02-mvp-readiness/INDEX.md`), recorded them as ADRs, and applied the
decision-driven doc amendments. Key reframing this session: the owner scoped the MVP to
**local-first** development on **Docker Desktop Kubernetes (WSL2)** — no cloud.

- **New `docs/decisions/` ADR log** (INDEX + ADR-0001…0005), cross-referenced from the review INDEX.
- **ADR-0001 — Local-first MVP:** runs on local Docker Desktop Kubernetes + docker-compose
  quick-start. gVisor → **production-only** (`runsc` unavailable on WSL2). Cloud
  (AWS/EKS/Terraform/ALB) deferred. `FR-SCALE-*` deferred post-MVP.
- **ADR-0002 — WebSocket room affinity** chosen over Redis pub/sub (resolves API-3); rewrote the
  `platform-operations.md` WebSocket scaling section.
- **ADR-0003 — Availability:** 99% MVP *Must*, 99.9% aspiration.
- **ADR-0004 — Erasure:** account deletion **pseudonymizes** game history (keep rows, strip PII).
  This **reverses** the prior hard-delete in `FR-ACCT-005` / `NFR-HIST-003`; added new
  **FR-HIST-030**. (The review had mischaracterized history as "kept indefinitely"; it was
  actually hard-deleted. Owner confirmed retain-pseudonymized.)
- **ADR-0005 — Sandbox:** an Espresso feasibility spike on **GraalVM CE for JDK 21** gates the
  Game Host FR-CTX enforcement design; OQ-002 process-isolation fallback stays first-class; the
  3s/5s startup NFRs (FR-SCALE-007, NFR-PERF-001) are deferred to post-MVP.
- **GraalVM label fix:** corrected "GraalVM CE 23" → "GraalVM CE for JDK 21" in `CLAUDE.md` and
  `platform-architecture.md` — no CE build exists for JDK 23; CE for JDK 21 is what's installed.

**Files changed:**
- `docs/decisions/` — new `INDEX.md` + `0001`…`0005`
- `docs/reviews/2026-07-02-mvp-readiness/INDEX.md` — strategic-decisions resolution note
- `docs/requirements/platform-operations.md` — WS room affinity, availability 99%, `FR-SCALE-*`
  post-MVP, CON-002/CON-011, out-of-scope, ADR refs
- `docs/requirements/platform-architecture.md` — MVP-scope banner, gVisor + startup-NFR deferrals,
  OQ-002 spike note, CE-label fixes, ADR refs
- `docs/requirements/game-history.md` — new FR-HIST-030, amended NFR-HIST-003, ADR ref
- `docs/requirements/user-accounts.md` — amended FR-ACCT-005, ADR ref
- `CLAUDE.md` — GraalVM CE for JDK 21 label
- `STATUS.md` — this update

---

## Next Priorities

Continue the review's action plan (`docs/reviews/2026-07-02-mvp-readiness/INDEX.md`):

1. **Owner decisions** — ✅ done (ADR-0001…0005, 2026-07-10).
2. **Espresso feasibility spike** (ADR-0005) — the next hands-on task; a small GraalVM CE for
   JDK 21 proof-of-concept (context startup timing + which isolation controls work on CE). Gates
   the Game Host internals spec and FR-CTX enforcement design.
3. **Remaining blocker spec fixes** — WS abuse controls (API-1/2), game-effect delivery +
   crash-recovery idempotency + FE serving origin (GAME-B1/B2/B3).
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
ADR-0003 (availability), ADR-0004 (erasure pseudonymization), ADR-0005 (sandbox / Espresso spike).

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
