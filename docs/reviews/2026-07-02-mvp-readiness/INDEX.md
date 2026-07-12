# MVP Readiness Review — 2026-07-02

Phase-0 exit review: are the current requirements + specs sufficient to implement and ship the first TurnBase MVP online (AWS primary / GCP fallback)? Produced by five parallel domain reviews, each captured in full in this directory.

| File | Domain |
|------|--------|
| [core-requirements.md](core-requirements.md) | Platform-core requirements (accounts, rooms, chat, notifications, social, history, views, UI library) |
| [api-design.md](api-design.md) | API design specs — security, sanitation, consistency, implementability |
| [game-execution-stack.md](game-execution-stack.md) | Game execution chain: GDK, gRPC protocol, manifest, sandbox, effect delivery |
| [devops-deployment.md](devops-deployment.md) | Deployment, IaC, data-layer ops, CI/CD, secrets, observability, dev cadence |
| [grmp-lessons.md](grmp-lessons.md) | Lessons mined from the GRMP prototype (`../grmp`) |
| [espresso-spike-results.md](espresso-spike-results.md) | Results of the ADR-0005 Espresso feasibility spike on GraalVM CE for JDK 21 (gates the Game Host internals spec) |

Already-tracked gaps (bundle/upload-pipeline spec, test harness spec, frontend shell spec, open questions in `docs/requirements-gaps.md`) were excluded from all reviews.

## Verdict

**Not yet — but close.** The specs are unusually deep for Phase 0 (privacy matrices, WS protocol, error taxonomy, GDK surface, CI gates are implementation-ready), but the review found **15 blocking gaps** and roughly 30 important ones. They cluster in three places: (1) contradictions on the room-lifecycle happy path, (2) unspecified connective tissue at both ends of the game-execution chain plus a crash-recovery correctness hole, and (3) an almost entirely undecided path from "Docker image exists" to "users reach it over TLS on AWS". Estimated closure effort: **3–4 focused spec sessions plus one technical spike** (Espresso sandbox/startup feasibility on GraalVM CE).

## Consolidated blockers

Cross-references (e.g. CORE-1) point into the per-domain reports, which carry full evidence and suggested resolutions.

### Room lifecycle (core-requirements.md)
1. **CORE-1** — Initial team instantiation at room creation undefined; the room happy path forks here.
2. **CORE-2** — Voluntary "Leave Room" during a game contradicts the no-distinction disconnect model (`reconnection-flow.md` vs `game-rooms.md`/`room-websocket.md`).
3. **CORE-3** — Host disconnect with no other human (incl. 1-player-vs-AI rooms): immediate closure vs grace period, docs point both ways.

### API abuse & scaling architecture (api-design.md)
4. ~~**API-1**~~ — **Closed 2026-07-12** ([`rate-limiting.md`](../../specs/api-design/rate-limiting.md) Tier 6). Per-principal STOMP frame budgets in the inbound `ChannelInterceptor`, **pod-local** rather than Redis-backed: room affinity (ADR-0002) pins a user's whole frame stream to one pod, so an in-JVM bucket is *exact*, and a Redis round trip per chat message and game action would buy nothing. Six buckets, sized by cost — the strictest is `snapshot` (1 per 3s), because `REQUEST_GAME_SYNC` re-enters the guest VM under the session's single-flight lock and is the most expensive frame a client can send. Penalty ladder: drop + `RATE_LIMIT_EXCEEDED` → connection close on sustained violation → Redis-backed reconnect lockout (30s, doubling). Closing a connection mid-game starts the flooder's own grace period — escalation removes persistent abusers from live games with no separate mechanism.
5. ~~**API-2**~~ — **Closed 2026-07-12** ([`rate-limiting.md`](../../specs/api-design/rate-limiting.md) Tier 5, `user-accounts.md` NFR-SEC-007). A **success-counting** IP bucket: 5 guests + 3 registrations per IP per hour. The reason this leaked is that Tier 1 counts only *failures* while these operations always succeed — so the two counters now coexist on the same endpoints and do not interact.
6. **API-3** — `room-websocket.md` room-affinity model vs `platform-operations.md` Redis-pub/sub scaling model: two incompatible architectures; one must be chosen (recommendation: room affinity). *(Resolved as a decision by ADR-0002 — room affinity — but `platform-operations.md` still carries the contradicting text; the edit is in the checklist below.)*

### Game execution chain (game-execution-stack.md)
7. ~~**GAME-B1**~~ — **Closed 2026-07-11.** Execution half in [`game-host-internals.md`](../../specs/game-host/game-host-internals.md) §10; client half in [`websocket.md` § Game Session Protocol](../../specs/api-design/websocket.md#game-session-protocol) — per-team topic, `/user/queue/game`, the STOMP game event catalogue, and `(sequence, index)` client dedup. **I4** (action-send authorization) and **I6** (initial-effect race) closed with it: I6 is resolved by a read-only `resync` input (game-contracts.md FR-IN-006) rather than an effect journal — the game backend composes each attaching viewer's current view, since the platform may not read game state.
8. ~~**GAME-B2**~~ — **Closed 2026-07-11** ([`game-host-internals.md`](../../specs/game-host/game-host-internals.md) §8.1/§9): atomic Redis session record `{stateJson, lastAppliedSequence, lastEffects}` + idempotent `CreateSession` + sequence replay.
9. ~~**GAME-B3**~~ — **Closed 2026-07-12** ([`game-asset-serving.md`](../../specs/game-frontend/game-asset-serving.md)). Games are served from a **separate registrable domain**, one origin per game (`{gameId}.games.<domain>`), from a deploy-time template; `sandbox="allow-scripts allow-same-origin"` (safe only because the frame is cross-origin); `default-src 'none'` / `connect-src 'self'` CSP; a server-rendered document carries the `__TURNBASE__` bootstrap. **API-5 closed with it** — and note the review's own suggested resolution (`games.turnbase.io`) was **unsound**: `SameSite` is a *site* check, so a subdomain would have left every game able to make credentialed API calls. CSRF now has three independent layers (`connect-src`, a server-side `Origin` check, `SameSite`). **GRMP-F5** is closed by construction: the origin is server-supplied (never build-baked) and isolation is trust-independent, so there is no fail-open branch.

### Deployment (devops-deployment.md)
10. **OPS-1** — Cloud provider/K8s flavor is "TBD"; gVisor (a Must) is a checkbox on GKE but custom-AMI work on EKS → needs an ADR (see decisions below).
11. **OPS-2** — No infrastructure-as-code at all. Default: Terraform in a new `turnbase-infra` repo.
12. **OPS-3** — No DB operational decision and **no schema-migration tool anywhere in the docs**. Default: RDS PostgreSQL + Flyway with backward-compatible-migration rule.
13. **OPS-4** — Redis durability contradiction: Redis is the sole crash-recovery layer for live game state, but no persistence/HA requirement exists for Redis itself (single instance per OQ-001 resolution). Compounds GAME-B2.
14. **OPS-5** — No runtime secrets/per-env config strategy (JWT keys included). Default: AWS Secrets Manager + External Secrets Operator.
15. **OPS-6** — Ingress/TLS/DNS undefined for a WebSocket-centric product; ALB idle-timeout and connection-draining behavior on deploys unspecified.

## Strategic decisions needing the project owner

> **Resolved 2026-07-10.** All six ratified in an owner decision session and recorded as ADRs in
> [`docs/decisions/`](../../decisions/INDEX.md): the MVP is **local-first** (Docker Desktop
> Kubernetes + compose quick-start; cloud/gVisor deferred — ADR-0001), WebSocket scaling uses
> **room affinity** (ADR-0002), availability target is **99% MVP** / 99.9% aspiration (ADR-0003),
> account erasure **pseudonymizes** history (ADR-0004), `FR-SCALE-*` and the 3s/5s startup NFRs are
> **deferred to post-MVP**, and the **Espresso feasibility spike runs first** to gate the Game Host
> spec (ADR-0005). The original options are preserved below for provenance.

1. **AWS/EKS vs GKE, and gVisor timing.** gVisor-as-Must collides with EKS (custom node AMI) and with local WSL2 dev (runsc unavailable — GRMP lesson). Recommended: stay AWS/EKS per your preference, demote gVisor to **production-only, post-first-deploy hardening** (Truffle + pod isolation meanwhile), record as an ADR. Picking GKE purely for managed gVisor is the alternative.
2. **Compose-first MVP profile.** GRMP never escaped docker-compose in 15 months. Recommended: keep K8s as the production target (it's a stated project goal) but spec docker-compose as the fully supported dev/demo profile and defer FR-SCALE-* (HPA, draining, cold-start budgets) to post-MVP.
3. **WebSocket scaling model** (API-3): room affinity vs Redis pub/sub. Recommended: room affinity; amend `platform-operations.md`.
4. **Availability target**: 99.9% (Must) is not achievable solo without on-call/staging. Recommended: 99% MVP target, 99.9% aspiration.
5. **GDPR/account-erasure**: game history is kept indefinitely with no deletion story; needs at least a requirements-level answer (pseudonymize on account deletion) before a public EU-reachable launch.
6. **Espresso feasibility spike** (GAME-I1 + GRMP lesson): per-context heap caps and strong sandbox tiers may be Oracle-GraalVM-only; Espresso context startup may bust the 3s/5s Musts. Run the spike **before** freezing FR-CTX enforcement design and the startup NFRs; `platform-architecture.md` OQ-002's process-isolation fallback stays first-class.

## New spec documents to write (beyond the already-planned bundle/upload, harness, shell specs)

1. **Deployment & infrastructure spec** — EKS decision + gVisor ADR, Terraform layout, ECR, ALB/ACM/Route53, environments, Helm deploy flow from GitHub Actions (OIDC), WebSocket draining, rollback. (OPS-1/2/6, devops report §Verdict)
2. **Data-operations spec** — RDS + backups/RPO-RTO, Flyway workflow, ElastiCache persistence/HA + accepted game-state loss window, S3 buckets. (OPS-3/4)
3. **Secrets & production-observability spec** — Secrets Manager + External Secrets, JWT key handling, per-env config, prod monitoring stack sizing/retention, alert routing, external uptime check. (OPS-5, devops §6/§9)
4. **Game Host internals spec** — maps each FR-CTX isolation requirement to a concrete CE-23-validated mechanism; GDK Host injection, serialization engine (shared component — GRMP-F4), guest classpath, instance-per-session model. (GAME-I1/I2)
5. ~~**Game session WebSocket spec**~~ — **Done 2026-07-11**, written into [`websocket.md` § Game Session Protocol](../../specs/api-design/websocket.md#game-session-protocol). Note the deviation from this recommendation: **no effect retention / deliver-on-subscribe replay**. A platform-held effect journal would mean archiving every ≤10 MB payload of every live session in a single non-HA Redis (OPS-4). Instead, an attaching client asks the *game backend* for its current view (read-only `resync`, FR-IN-006) — bounded, and it makes catch-up race-free by construction. Cost: a contract addition (proto `Resync` RPC, a 4th required GDK hook), cheap now that ADR-0006 scopes the MVP to first-party games. (GAME-B1, I4, I6)
6. ~~**`input-validation.md`**~~ — **Done 2026-07-12** ([`input-validation.md`](../../specs/api-design/input-validation.md)). Two deviations from the recommendation, both because the recommendation was weaker than what the existing specs already made possible: (a) the `parameters` **cap** became a **whitelist** — the manifest already declares a typed parameter schema (`key`/`type`/`min`/`max`/`options`), so unknown keys are rejected outright and the amplification vector is gone by construction rather than merely bounded; (b) usernames are Unicode with an ICU4J **confusable-skeleton** uniqueness index and a mixed-script restriction, not just NFC — NFC alone does not stop `Аlice` (Cyrillic А) from impersonating `Alice`. Also pins the one place "React escapes by default" does *not* hold: `GAME_LOG` Markdown, whose content is composed by game code. (API-6, CORE-6/21)

## Existing-doc edit checklist (IMPORTANT tier, groupable into 1–2 sessions)

- `game-rooms.md` + `reconnection-flow.md`: CORE-1/2/3 resolutions; grace timers as persisted absolute deadlines + sweep (GRMP-F3); room-closure → `TerminateSession` ordering (GRMP-F2).
- `platform-operations.md`: reconciliation sweep job (GRMP-F1); scaling-model fix (API-3); cost/SLO reality check; Dependabot + Trivy in CI; frontend added to FR-CICD-001.
- `user-accounts.md`: password change FR, logout FR (+ guest warning), username constraints, OAuth email-collision rule, lockout decay, session-invalidation closes live WS/SSE.
- `rest-conventions.md`: authorization/ownership section (IDOR), actuator isolation, logout endpoint, idempotency note. *(CORS/Origin policy + CSRF — done 2026-07-12, § Origin Policy and CSRF.)*
- ~~`rate-limiting.md`~~: **Done 2026-07-12** — WS message tier (API-1), guest-creation bucket (API-2), X-Forwarded-For trust policy *(plus IPv6 /64-prefix keying, without which every IP tier is bypassable by anyone holding a routed /64)*, per-env configurability (GRMP-F6, with `enabled=false` permitted only under the `test`/`e2e` profile — the app fails to start otherwise, so the escape hatch that makes e2e runs bearable cannot ship to production).
- `notifications-invitations.md` + `sse-notifications.md`: alert-vs-notification event classes; friend-request/notification lifecycle coupling.
- `websocket.md`: STOMP heartbeats 10s/10s; `GAME_STARTED` topic separator fix.
- gRPC protocol + proto: parameters encoding (UTF-8 JSON, defaults materialized by Orchestration — GAME-I5); failed-action drop semantics (GAME-I3); sequence allocation in Redis; `GameOutcome` validation; stdin/stdout reference sweep (GAME-M4).
- `platform-ui-library.md`: add Tabs, Select, Switch/Checkbox, Badge; fix Avatar contradiction.
- Upload-pipeline spec (when written): `gdkApiVersion` check (GAME-I7), serialization round-trip smoke test (GRMP-F4). *(Game-asset origin decision — GAME-B3 — is done; the upload spec must unpack bundles into the `/g/{gameId}/{version}/` layout that [`game-asset-serving.md`](../../specs/game-frontend/game-asset-serving.md) §4.1 serves.)*

## What's already in good shape

Uniform RFC 9457 error model across REST/WS/SSE; the three room WebSocket docs interlock without contradictions; WS two-layer authorization; privacy matrices and guest semantics; GDK/manifest/proto developer surface is implementation-ready with consistent traceability; CI/test-tier requirements and the repo/branching/versioning strategy; several GRMP lessons already absorbed by design (spectator capability metadata, private-by-default uploads, host-driven start, lobby-disconnect-is-leave, hidden-information safety via effects-push, single WebSocket gateway).
