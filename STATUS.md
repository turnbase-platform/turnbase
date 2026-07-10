## Last Session Summary

**Date:** 2026-07-11 (session 3)

**Ran the Espresso feasibility spike (ADR-0005)** and, on its outcome, made the **game trust-model
decision (new ADR-0006): the MVP hosts official, first-party Java games only.**

**Spike results** (`docs/reviews/2026-07-02-mvp-readiness/espresso-spike-results.md`) — a throwaway
Maven project run on GraalVM CE 21.0.2 (and Oracle GraalVM 21.0.11 for comparison), loading a
trivial untrusted guest game into an Espresso context and probing each FR-CTX control:
- **Works on CE:** cross-version heap/static isolation (FR-CTX-001/003), `System.exit` containment
  (FR-CTX-006, `java.ExitHost=false`), forced termination (FR-CTX-008, `Context.interrupt` ≈5 ms),
  fast startup (cold ≈0.6 s).
- **Does NOT work on CE:** **filesystem (FR-CTX-004) and network (FR-CTX-005) leak** to the host OS —
  Espresso must boot with native access, and the guest JDK's `java.io`/`java.net` bypass
  `IOAccess.NONE`; **per-context heap cap (FR-CTX-007) is Oracle-only**.
- **Oracle GraalVM** adds only the enforced heap cap (`sandbox.MaxHeapMemory`); FS/network still leak
  (Espresso only runs under `TRUSTED`). **gVisor** helps only at the OS/container layer. So untrusted
  Java needs a hardened container regardless → **stay on CE** (honours CON-001).
- **Root cause / general rule:** Truffle sandboxes *native-free* guests (JS fully, Python largely) on
  CE; Java (Espresso) and native LLVM (C/C++/Rust) cannot be sandboxed in-JVM on CE.

- **ADR-0006 — Game trust model:** MVP = official-only Java backends. Untrusted backends of any
  language deferred post-MVP (hardened-container Java via gVisor; JS/Python via GraalJS/GraalPy).
  Trust is assigned **per runtime**; the Orchestration↔Game Host gRPC contract is the
  language-agnostic seam (`manifest.runtime`). For trusted official code the Game Host needs only
  resource limits (interrupt timeouts + container memory), not adversarial isolation — this resolves
  the ADR-0005 FR-CTX enforcement question and likely pulls the untrusted upload pipeline out of MVP
  scope.

**Files changed:**
- `docs/reviews/2026-07-02-mvp-readiness/espresso-spike-results.md` — new (spike report incl.
  gVisor + Oracle GraalVM comparison) + review INDEX entry
- `docs/decisions/0006-game-trust-model-java-official-only.md` — new + decisions INDEX entry
- `docs/decisions/0005-game-sandbox-espresso-spike.md` — spike-outcome section
- `docs/requirements/platform-architecture.md` — MVP trust-model scope note, CON-001 correction,
  ADR-0006 ref, OQ-002 result
- `docs/requirements/game-development-experience.md` — official-only-Java MVP note, ADR-0006 ref
- `docs/requirements/game-contracts.md` — MVP trust-scope note (contract unchanged)
- `docs/specs/manifest/manifest-schema.md` — `runtime` field per-runtime trust policy note
- `STATUS.md` — this update

**Spike project** lives in the transient scratchpad (not committed); re-creatable from the report.

---

## Next Priorities

Continue the review's action plan (`docs/reviews/2026-07-02-mvp-readiness/INDEX.md`):

1. **Owner decisions** — ✅ done (ADR-0001…0005, 2026-07-10).
2. **Espresso feasibility spike** (ADR-0005) — ✅ done (2026-07-11). Outcome: untrusted Java not
   isolable in-JVM on CE → **ADR-0006** scopes MVP to official-only Java. Game Host isolation for the
   MVP = interrupt timeouts + container memory limit (no adversarial in-JVM enforcement).
3. **Game Host internals spec** — now unblocked (ADR-0005/0006). Decide **Espresso-in-hardened-
   container vs plain-JVM-per-process**; spec the trusted-code enforcement (timeouts + container
   memory), instance-per-session model, GDK Host injection, serialization, guest classpath. Ship the
   Java 21 guest in the image (`java.JavaHome`; bundled Maven Espresso guest is JDK 17).
4. **Remaining blocker spec fixes** — WS abuse controls (API-1/2), game-effect delivery +
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
