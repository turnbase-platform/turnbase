# Archive — M3 Game execution

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M3-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M3-01 | GDK backend API surface | sdk | M0-02 | DONE |
| IMP-M3-02 | Espresso context lifecycle | game-host | M0-04 | DONE |
| IMP-M3-03 | GDK host bridge and serialization boundary | sdk, game-host | M3-01, M3-02 | DONE |
| IMP-M3-04 | gRPC service implementation | game-host | M3-03 | DONE |
| IMP-M3-05 | Orchestration client and session registry | platform | M3-04, M2-04, M2-06 | DONE |
| IMP-M3-06 | Game input outbox and delivery | platform | M3-05 | DONE |
| IMP-M3-07 | Effect fan-out and spectator filtering | platform | M3-06 | DONE |
| IMP-M3-08 | Session teardown as a durable to-do | platform | M3-05, M2-09 | DONE |
| IMP-M3-09 | Game failure handling | platform, game-host | M3-07, M2-09 | DONE |
| IMP-M3-10 | The first official game | sdk consumer | M3-03, M3-05 | DONE |
| IMP-M3-11 | GDK test harness | sdk | M3-01, M3-03, M3-13 | DONE |
| IMP-M3-12 | FE GDK client (`@turnbase/gdk`) | sdk | M0-02 | DONE |
| IMP-M3-13 | Shared bundle validator module | sdk, platform | M4-03, M3-03 | DONE |

---

## M3 — Game execution

**Read first for the whole milestone:** `docs/specs/game-host/game-host-internals.md`,
`docs/specs/internal-grpc/orchestration-gamehost-protocol.md`, `gamehost.proto`,
`docs/specs/gdk-api/backend-gdk-api.md`, `docs/requirements/game-contracts.md`,
`docs/decisions/0005`, `docs/decisions/0006`, and flows `03` and `06`.

### IMP-M3-01 — GDK backend API surface

**Repo:** `turnbase-sdk` · **Depends on:** IMP-M0-02

**Read first:**
- `docs/specs/gdk-api/backend-gdk-api.md` **in full** — §3 lifecycle, §4 contexts, §5 data model,
  §6 effects, §7 results, §8 outcome, §9 determinism, §11 the worked example
- `docs/requirements/game-development-experience.md` FR-GDK-001…016, NFR-COMPAT-001, NFR-DX-001…002
- `docs/requirements/game-contracts.md` — the behavioural contract the types encode
- `docs/decisions/0006-game-trust-model-java-official-only.md`

**Satisfies:** `game-development-experience.md` FR-GDK-001…016, NFR-COMPAT-001, NFR-DX-001…002;
`game-contracts.md` FR-STATE-001…005, FR-IN-001…006, FR-EFF-001…007, FR-RESP-001…005,
FR-OUTCOME-001…004, FR-PROC-001…003, FR-LOG-001…005

**Done when:** every type in §§3–8 exists with the stated signature and carries Javadoc; the artifact
compiles to Java 21 bytecode and references no Java 22+ API — **it runs inside Espresso, where a
Java 22 API is a runtime failure in a sandbox, not a compile error**; §9's determinism contract is
stated in Javadoc on the interface itself, not only in the spec, because that is the only place a
game developer reads it.

---

### IMP-M3-02 — Espresso context lifecycle

**Repo:** `turnbase-game-host` · **Depends on:** IMP-M0-04

**Read first:**
- `docs/specs/game-host/game-host-internals.md` §§1–2, §4 (isolation: requirement → mechanism),
  §6 (context, session and instance model), §7 (game code loading and guest classpath), §11
- `docs/decisions/0005-game-sandbox-espresso-spike.md`
- `docs/reviews/2026-07-02-mvp-readiness/espresso-spike-results.md`
- `docs/requirements/platform-architecture.md` FR-CTX-001…012, FR-LOAD-001…005
- `docs/specs/deployment/local-environment.md` §7.8 (Game Host config), §7.9 (artifact-store
  endpoint/bucket keys, shared with the monolith) — added: the artifact-fetch half of §7 needs the
  same `turnbase.artifact-store.*` keys the monolith already binds, and §7.8 alone does not carry them.

**Satisfies:** `platform-architecture.md` FR-CTX-001…012, FR-LOAD-001…005

**Done when:** every isolation requirement in §4's table maps to a concrete Truffle/Espresso mechanism
that a test exercises — the table is a checklist, and an unexercised row is an assumption; a context
is created and disposed per §6's model with no leak across sessions; the guest classpath built per §7
contains the game JAR and the SDK and nothing else.

**Scope note (session 68/69):** FR-CTX-004/005/007 (no filesystem, no network, per-context memory cap)
are container-owned per §4.1's own framing — no deployment-manifest work item yet exists to provision
a container, so they are not exercised here; that is a gap in a later item, not in this one.
FR-CTX-009/010 (idle and memory-pressure eviction) are host-owned and implemented in
`GameContextManager`. FR-CTX-012 (polyglot extensibility) is "design" status per §4's table and needed
no code. "The SDK" on the guest classpath is the configured `sdkJarPath` placeholder — the real guest
bridge jar carrying the GDK API classes is IMP-M3-03's deliverable (§3.2).

---

### IMP-M3-03 — GDK host bridge and serialization boundary

**Repo:** `turnbase-sdk` (the serialization component), then `turnbase-game-host` (the guest bridge
and host shim) — two branches, in that order, per `conventions.md` §5 · **Depends on:** IMP-M3-01,
IMP-M3-02

**Closed:** IMP-GATE-69 (opened and closed 2026-09-26) — `game-host-internals.md` §3.2/§5 call the
serialization engine "one module reused by" the guest bridge, the harness and the upload validator,
and no document said which repository builds it or where the guest bridge jar itself is built; the
item's *Repo* named only `turnbase-game-host`, which the harness (`turnbase-sdk`) cannot depend on.
`IMP-M4-03` had already hardcoded the capability table for want of an artifact to read it from. Fixed:
new `game-host-internals.md` §3.6 — `io.turnbase:turnbase-serialization` is built by `turnbase-sdk`;
the guest bridge JAR is a second, shaded and unrelocated artifact of `turnbase-game-host`;
`conventions.md` §5 names the new artifact.

**Closed:** IMP-GATE-70 (opened and closed 2026-09-26) — the item's *Done when* needs `turnbase-game-host`
to depend on `turnbase-sdk` and `turnbase-serialization` and its pipeline to go green, but `conventions.md`
§5's bootstrap window covered `turnbase-common` alone: `turnbase-sdk` is private and untagged, so its
artifacts are nowhere for the Game Host's CI to fetch, and `TURNBASE_COMMON_PAT` cannot read it. Fixed:
`conventions.md` §5 extends the window to `turnbase-sdk` — one root `./mvnw install` installs both
artifacts, a second bootstrap step, a new human-provisioned `TURNBASE_SDK_PAT` secret on
`turnbase-game-host`. **The secret is a human action and does not yet exist**: do the `turnbase-sdk` half
first and merge it, verify the game-host half locally, and merge that half only once the secret is
present (`gh secret list -R turnbase-platform/turnbase-game-host` shows it).

**Closed:** IMP-GATE-79 (opened and closed 2026-09-27) — §3.3's guest-boundary call interface listed
`createSession(sessionId, teamsJson, parametersJson)` with no way to tell the guest bridge which
`TurnBaseGame` implementation to classload, and §6.1/§7.2 assigned entry-class loading to the bridge
without saying how the FQCN crosses the boundary; `CreateSessionRequest` carried no such field either.
Unsatisfiable as written — a `createSession` call with no entry point cannot instantiate a game. Fixed:
`gamehost.proto`'s `CreateSessionRequest` gains `entry_point_fqcn` (field 5), resolved by Orchestration
from the manifest's `backend.entryPoint` the same way it already resolves `parameters`
(`orchestration-gamehost-protocol.md` new "Entry-point resolution" §); `game-host-internals.md` §3.3's
table, §6.1 and §7.2 updated to match. `turnbase-common`'s committed proto copy synced and pushed
(`c04f932`), CI green.

**Session 86 progress:** the `turnbase-sdk` half is done and merged (`6d05ac4`) — `turnbase-sdk` is
now a two-module reactor (`gdk-api/`, unchanged; new `serialization/`), publishing
`io.turnbase:turnbase-serialization` (`GdkSerialization`'s write/read round trip with
NFR-SIZE-001/002 limits, `GdkObjectMapper`, and the `BindingCapabilities` Jackson-free descriptor
`bundle-format.md` §4.4 will eventually read, per `IMP-M4-03`'s recorded follow-up). CI green on
`master`.

**Session 87 progress:** the `turnbase-game-host` half is built, tested and committed on local branch
`feat/imp-m3-03-guest-bridge-and-host-shim` (`6b0adca`) — `io.turnbase.gamehost.bridge` (six §3.3
entrypoint methods, `GameEntrypoint`, `PlatformJson`, `GameParametersImpl`, the `*ContextImpl`
classes, `CodeLoadException`) plus `io.turnbase.gamehost.shim.GameBridgeClient`, driven end to end
through a real Espresso context by `GameBridgeClientEspressoTest` (5/5 green) — the authoritative
proof that the host shim sees only strings, primitives and byte arrays. `pom.xml`'s `maven-shade-plugin`
execution is bound to the `package` phase and declared before `spring-boot-maven-plugin` so
`default-jar` and then shading both complete before Spring Boot's `repackage` runs, producing the
`guest-bridge`-classifier artifact (`io.turnbase.gdk.*` + `turnbase-serialization` + Jackson,
unrelocated) alongside the app jar. The Dockerfile now stages both jars and sorts the `guest-bridge`
one to `/opt/turnbase/guest-bridge.jar` — `turnbase.gamehost.sdk-jar-path`'s default — which the
original glob fix would have silently discarded; verified by `docker build` + `docker run` showing
both artifacts at their correct paths with correct ownership. Because Espresso's guest-side class
loading is invisible to JaCoCo's host-JVM agent, `GameEntrypointTest`, `PlatformJsonTest` and
`GameParametersImplTest` exercise the same bridge classes directly on the host JVM so the merged
coverage floor is measurable; `./mvnw verify` (52 tests) and `./mvnw verify -Pintegration` (54 tests)
are both green locally. `build.yml` gained the `turnbase-sdk` bootstrap step `IMP-GATE-70` specifies.
`TURNBASE_SDK_PAT` was provisioned on `turnbase-platform/turnbase-game-host` this same session
(confirmed via `gh secret list`), clearing `IMP-GATE-70`'s human-action blocker. Merged
`feat/imp-m3-03-guest-bridge-and-host-shim` `--ff-only` into `master` and pushed (`6b0adca`); branch
deleted both locally and on the remote. The triggered CI run failed once on `Trivy scan — image
(report)` with "no space left on device" during the image export — a runner disk-space exhaustion
from the two bootstrap Maven installs plus this module's own image, not a code or vulnerability
defect. Fixed in two follow-up commits, both merged `--ff-only` directly to `master` to keep it green:
`7a3f1fb` deletes each bootstrap clone (`turnbase-common`, `turnbase-sdk`) right after installing it
to `~/.m2`; `24e3398` additionally frees disk by removing `ubuntu-latest`'s unused preinstalled
toolchains (`.NET`, Android SDK, GHC, CodeQL) before the image build. CI green on `master` at
`24e3398` (run `36342814547`, confirmed via `gh run watch --exit-status`), including the GHCR image
push. Submodule ref bumped in this repo to match. **`IMP-M3-03` is `DONE`.**

**Read first:**
- `docs/specs/game-host/game-host-internals.md` §3 (the guest bridge and host shim — **including §3.6,
  where each half is built**), §5 (the serialization engine), §8 (state representation)
- `docs/specs/gdk-api/backend-gdk-api.md` §10 (relationship to the gRPC contract)
- `docs/requirements/game-contracts.md` NFR-SEC-001…004, NFR-SIZE-001…002
- `docs/specs/manifest/bundle-format.md` §4.4 (the capability-descriptor consumer, for the exact
  shape `BindingCapabilities` needs to expose — missing from the original read-list; added this
  session because §3.6's "capability descriptor" line is undecidable without it)

**Satisfies:** `platform-architecture.md` FR-CTX-001…012; `game-contracts.md` NFR-SEC-001…004,
NFR-SIZE-001…002

**Done when:** every object crossing the Espresso boundary is copied, not shared. A shared mutable
object across that boundary is a sandbox escape regardless of ADR-0006's trust model. Also (§3.6):
`io.turnbase:turnbase-serialization` is built and pinned by exact version in `turnbase-game-host`; the
guest bridge JAR is a shaded, unrelocated second artifact of `turnbase-game-host` containing
`io.turnbase.gdk.*`, the serialization component and Jackson, and it — not the Spring Boot fat jar — is
what `turnbase.gamehost.sdk-jar-path` points at in the image; a test drives §3.3's entrypoint through a
real Espresso context and the host shim sees only strings, primitives and byte arrays.

---

### IMP-M3-04 — gRPC service implementation

**Repo:** `turnbase-game-host` · **Depends on:** IMP-M3-03

**Read first:**
- `docs/specs/internal-grpc/gamehost.proto` — including the field comments, which state all three
  sequence cases
- `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` **in full** — processing semantics,
  the error model, message size
- `docs/specs/game-host/game-host-internals.md` §9 (invocation, sequencing, idempotency, recovery),
  §12 (timeouts and `GameFailureKind` mapping)

**Satisfies:** `platform-architecture.md` FR-ORCH-001…007, FR-FAIL-001…007

**Done when:** `TerminateSession` is idempotent **as specified in the contract**, not merely in the
implementation; `NOT_FOUND` is scoped so a retried teardown does not read as a hard failure.

**A forward gap in the sequence is normal and must be accepted** (IR-16). The three cases — replay of
a seen sequence, the ordinary next sequence, and a forward gap — are stated at the field in the
`.proto` precisely because a reader working from generated code never sees the prose table.

**Closed IMP-GATE-86:** 2026-09-27 — `game-host-internals.md` §9.3 required a Game Host recovering a
session after a crash to reconstruct the guest-side `TurnBaseGame` instance from Redis alone, but the
§8.1 session record had no `entryPointFqcn` field, no RPC after `CreateSession` carried that value
again, and the guest bridge (`GameEntrypoint`) had no way to populate its session map other than
`createSession`, which unconditionally re-runs `onInit` — an idempotency violation for a session
already mid-game. Blocked FR-FAIL-002, which this item's own *Satisfies* claims. Fixed the same
session: `game-host-internals.md` §8.1 now has a persisted `entryPointFqcn` field (written once at
`CreateSession`, outside the per-invocation atomic unit); §3.3 adds a
`restoreSession(sessionId, entryPointFqcn)` guest-bridge method that populates the session map without
invoking `onInit`; §9.3 now calls it out explicitly in the recovery flow.

**Scope note (session 89):** this item's *Done when* clause is narrowly `TerminateSession`
idempotency plus `NOT_FOUND` scoping, and that is what the implementation (`SessionDispatcher`,
`GameHostServiceImpl`, the `session:{sessionId}` Redis record) and its tests cover. Two things named
in the *Read first* §12 material are deliberately not built here, so a later item doesn't discover
their absence by surprise: (1) no watchdog/timeout-interrupt infrastructure exists — a handler that
hangs rather than throwing is not detected or escalated to `GameFailureKind.TIMEOUT`; only an
in-band exception during a handler call is reported as a failure. (2) `ArtifactCache.pin`/`unpin`
(`IMP-M3-02`) is still not wired to context lifecycle (`IMP-M3-03`'s `GameContextManager`) — neither
references the other — so FR-LOAD-004 ("never evict a JAR backing a live context") is not yet
enforced. Neither gap blocks this item's own clause or FR-FAIL-001's in-band-exception path; both
are pre-existing or orthogonal, not introduced by this session, but are undone.

---

### IMP-M3-05 — Orchestration client and session registry

**Repo:** `turnbase-platform` · **Depends on:** IMP-M3-04, IMP-M2-04, IMP-M2-06, IMP-M4-04

**`IMP-M2-06` added to *Depends on*** (`IMP-GATE-46`, session 41) — this item's own clause below
replaces `IMP-M2-06`'s in-process-stub `GameSessionStarter` with a real implementation, so the port
and the `START_GAME` handler calling it must exist first.

**`IMP-M4-04` added to *Depends on*** (`IMP-GATE-62`, session 56) — `GET /play/{sessionId}`
(`game-asset-serving.md` §4.1 row 1, §5) reuses `IMP-M4-04`'s `Host`-routing filter and asset-serving
code, and needs the deny-listed unpacked tree that item's dependency (`IMP-M4-03`) publishes; this
item is the one that creates the session data the route resolves against, so it is where the route
lands. See `IMP-M4-04`'s *Closed* note for the full gate.

**Read first:**
- `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` — *Addressing the Game Host pods*,
  *Processing semantics*, *Error model*
- `docs/specs/game-host/game-host-internals.md` §6, §9, §13 (the Redis data model)
- `docs/specs/flows/02-room-to-game-start.md` — **step 6 names exactly which keys Orchestration writes**
- `docs/specs/platform/data-model.md` §1 (`active_session_id`), §4
- `docs/specs/api-design/room-websocket.md` — `GAME_STARTED`'s exact payload shape
- `docs/specs/game-frontend/game-asset-serving.md` §4.1 (the `/play/{sessionId}` route and version
  pinning), §5 (the bootstrap document), §7 (session integration)

**Satisfies:** `platform-architecture.md` FR-ORCH-001…007, FR-REG-001…004, FR-SESS-001…006;
`game-rooms.md` FR-HOST-009 (success path only — the precondition/rejection half is `IMP-M2-06`'s);
`game-development-experience.md` FR-ASSET-003, FR-ASSET-007, FR-ASSET-008

**Done when:** `session:{id}` has **exactly one writer, the Game Host** (IR-14). Orchestration writes
only the keys flow 02 step 6 names and reads the rest. The platform's own record of a live session is
`room.active_session_id` — a durable Postgres fact — not a Redis key, so a Redis flush loses cached
state and not the knowledge that a session exists.

**The real `GameSessionStarter` implementation replaces `IMP-M2-06`'s stub**: on a successful
`START_GAME`, it creates the session via the orchestration client, persists `room.active_session_id`
(the session's `(gameId, version)` is `room.game_version`, pinned at room creation per flow 02 §A
step 3 and never rewritten — FR-ASSET-007 holds because that column is immutable, not because the
version is re-resolved at start; `IMP-GATE-87`), and
broadcasts `GAME_STARTED` with the live `sessionId` and the server-composed `gameFrontendUrl`
(`room-websocket.md`) — not before, since a failed session creation must never advance the room to
In Progress.

**`GET /play/{sessionId}` serves `game-asset-serving.md` §5's bootstrap document** for the pinned
`(gameId, version)`, 404ing when the session is unknown or ended and when the `Host` header's
`gameId` does not match the session's own (§4.1's *Validation*) — never serving game A's code from
game B's origin. A reconnecting player and every other participant receive the identical bundle
regardless of any republish in between (FR-ASSET-007).

**Closed IMP-GATE-87:** 2026-09-29 — three things this item needs that no document supplied, found
while reading its read-list, none of which the code could settle without a silent choice. (1) The
Redis shape of the Game Host registry: `game-host-internals.md` §13 named `hostlease:` and `contexts:`
but no key for the advertised address, runtime types, load signals or the enumeration of instances,
though the protocol doc says the address "is stored in the Redis registry" and host selection needs to
enumerate them; §13 and §11 now define `hosts`, `host:{instanceId}` and the selection rule, and
correct `hostlease:`'s writer (the Game Host never touches Redis directly). (2) The heartbeat
interval, lease TTL and dispatch deadline had no values or config keys — `local-environment.md` §7.8
now carries `turnbase.orchestration.*`. (3) `game-asset-serving.md` §4.1 and this item's own *Done
when* said the session's version is resolved at session start and stored on "the session record",
contradicting flow 02 §A step 3 and `game-catalog.md` FR-GAME-010/011 (the version is pinned at room
creation) and naming a record the platform does not own; §4.1 and this clause now say
`room.game_version`, reached through `room.active_session_id`.

**Closed IMP-GATE-88:** 2026-09-29 — `START_GAME` had no defined outcome when the preconditions hold
but session creation fails (no eligible Game Host, or `CreateSession` errors); the WebSocket error
registry had no code for it and this item's clause says only that the room must not advance.
`room-websocket.md` now defines `GAME_START_FAILED` (`details.reason` `NO_HOST_AVAILABLE` |
`SESSION_CREATION_FAILED`), unicast to the host, room left in Lobby.

**Scope note (session 92) — partly landed, not `DONE`.** Session 91's list (registry server,
`GameSessionService.create`, real `START_GAME`, `/play`) plus, in `turnbase-platform`:
`GameInputService` (per-session `seq:` `INCR`, `ProcessInput` against the host `routing:` names,
the `delivered:` watermark so effects reach `EffectDelivery` once per sequence, `failcount:` counting
consecutive failures with the `turnbase.gamehost.retry-limit` limit, transport statuses mapped per the
protocol's *Error model*); the real `GameInputDispatcher` (outbox `player_left` → `ProcessInput`,
`NOT_FOUND` conditional on `room.active_session_id`, sequence from `seq:` rather than the row id);
`CreateSession`'s initial effects handed to `EffectDelivery`. `EffectDelivery` is the seam to
`IMP-M3-07`; until then a logging stub delivers to no client. **Still owed:** (1) the two cross-repo
end-to-end checks below; (2) `ACTION_REJECTED` unicast to the acting player and the player-facing failure notice
at the retry limit — the acting-player action path (`GAME_ACTION` → `ProcessInput`) has no caller
yet, so `GameInputService.process` is exercised only by the outbox; (3) reassigning a session to
another host on `UNAVAILABLE` (FR-ORCH-005) — the call is left for retry with the failure counted, but
`routing:` is not rewritten, because the game key needed to re-select a host is not in Redis;
(4) `TerminateSession` at the retry limit belongs to `IMP-M3-08`. Transport facts from session 91
stand (trailers-only status lost under grpc-servlet; `maxSavePostSize` raised to 1 MiB for h2c).

**Closed IMP-GATE-89:** 2026-09-30 — what session 92 left owed was not all this item's. (1) The
trace check needs a session that a Game Host can actually run, and the only loadable game is
`IMP-M3-10`'s (it already owns "can actually be started"); `TestBundles`' Chess is an empty-interface
stub. It moves there. (2) `ACTION_REJECTED` and the retry-limit notice are `IMP-M3-09`'s own clause
("the acting player is told why"), and the `/app/game.*.action` admission handler that would feed
`GameInputService.process` is `IMP-M3-06`'s (FR-IN-003). (3) Host reassignment on `UNAVAILABLE` is
FR-ORCH-005, which `IMP-M3-08` satisfies; it also needs the game key that `routing:` lacks, which is a
design question for that item. The `Register` half of IMP-GATE-08 was checkable now and is:
`deploy/compose/e2e-smoke.sh` fails unless a Game Host is in the `hosts` set within 60 s of
`compose up` (measured 27 s).

**Closes IMP-GATE-08's cross-repo half:** this item gives `GameHostRegistryService` its real server
implementation, so it also carries the end-to-end check `IMP-M0-04` could not — a `turnbase-game-host`
instance pointed at a running Platform Monolith completes `Register` within `local-environment.md`
§3's 60-second budget.

**IMP-GATE-18's cross-repo half moved to `IMP-M3-10`** (`IMP-GATE-89`): this item builds the chain
client → WebSocket → Orchestration → gRPC → Game Host, but nothing that a Game Host can run exists
until the first official game does, so the one-trace-in-Tempo check is that item's clause.

---

### IMP-M3-06 — Game input outbox and delivery

**Repo:** `turnbase-platform` · **Depends on:** IMP-M3-05

**Read first:**
- `docs/specs/platform/data-model.md` §4 — `game_input_outbox`, and why `session_id` is `NOT NULL`
- `docs/specs/platform/room-lifecycle.md` §3.3 — the conditional insert
- `docs/decisions/0010-session-teardown-ordering.md`
- `docs/specs/flows/03-game-turn.md`

**Satisfies:** `platform-architecture.md` FR-DELIVER-001…006; `game-contracts.md` FR-IN-001…006

**Also owns the acting-player path** (`IMP-GATE-89`): the `/app/game.*.action` handler that admits a
`GAME_ACTION` frame and calls `game.GameInputService#process`. `IMP-M3-05` built the service and only
the outbox calls it; this item is its second caller.

**Done when:** the outbox drain is **not** ownership-partitioned — it is a gRPC call needing no
ownership, and partitioning it leaves an unowned room's `player_left` undelivered, with the game
sitting on a turn that never comes.

**Built (session 94):** the drain (`GraceDeadlineSweepJob` duty 4, `GameInputDispatcherImpl`) already
existed from `IMP-M2-09`/`IMP-M3-05` and is not ownership-partitioned; this item added
`GameActionController` (`/app/game.{sessionId}.action`: handler-level admission read from durable room
state, the `PlayerRef` built server-side, `NOT_MEMBER` / `ROLE_NOT_ELIGIBLE` per `room-websocket.md`)
and `GameInputService.submitAction`, which serialises allocate-plus-dispatch per session — without it
two concurrent actions could reach the Game Host as 44, 43 and the first would be dropped as a replay.
A non-`DELIVERED` outcome is only logged; telling the player is `IMP-M3-09`. The channel-level
fast-fail (`game.*` `SubscriptionAuthorizer`) is `IMP-M3-07`'s, with the subscriptions it guards.

---

### IMP-M3-07 — Effect fan-out and spectator filtering

**Repo:** `turnbase-platform` · **Depends on:** IMP-M3-06

**Read first:**
- `docs/specs/game-host/game-host-internals.md` §10 (effect delivery and fan-out)
- `docs/specs/api-design/websocket.md` § `GAME_EVENT`, § *Authorization model (game)*
- `docs/specs/api-design/room-websocket.md` § *Spectator Event Visibility*
- `docs/requirements/game-contracts.md` FR-EFF-001…007, NFR-SEC-001…004

**Satisfies:** `game-contracts.md` FR-EFF-001…007, NFR-SEC-001…004; `platform-architecture.md`
FR-DELIVER-001…006

**Done when:** **every effect address is validated against the producing session's membership at
fan-out** (IR-17). The per-user queue secures the *subscription*, not the *address* — a subscriber can
only read their own queue, but nothing stops game code addressing an effect to a user who is not in
this session, and without the check the platform delivers it. Spectator visibility is applied
server-side; a client-side filter hands spectators the hidden state and asks them not to look.

**Built (session 95):** `game.EffectFanOut` replaces the logging stub. It validates each
`send_to_player`/`send_to_team` address against the session's *durable* roster (`SessionRosterSource`,
implemented by `room` from `room_participant`; a spectator is not a valid player target) and drops a
failing effect with a WARN and `turnbase.effect.address_rejected.total{kind}`; only the first
`game_over` per result is delivered and its structured outcome is never sent. Spectator filtering is
structural (topic subscriptions plus the player-only address check). `room.GameSubscriptionAuthorizer`
is the channel-level fast-fail for `game.*` topics. `CreateSession`'s initial effects are checked
against the roster from the create command, because `active_session_id` is not yet committed.
Not built here: `GAME_SYNC`/`GAME_PLAYER_*`/`SESSION_FAILED` messages, the game-log retention, and
what follows `game_over` (history, teardown) — `IMP-M3-08`/`09`.

---

### IMP-M3-08 — Session teardown as a durable to-do

**Repo:** `turnbase-platform` · **Depends on:** IMP-M3-05, IMP-M2-09

**`IMP-M2-09` added to *Depends on*** (`IMP-GATE-53`, session 45) — this item wires the normal
game-end caller into `room.RoomSessionDetacher#detach`, whose real implementation (`detachSession`,
`room-lifecycle.md` §4) is `IMP-M2-09`'s.

**Read first:**
- `docs/decisions/0010-session-teardown-ordering.md`
- `docs/specs/platform/data-model.md` §4 — `session_teardown`, keyed by `session_id`
- `docs/specs/platform/room-lifecycle.md` §4
- `docs/specs/flows/06-game-end-and-rematch.md`

**Satisfies:** `game-rooms.md` FR-XFER-005; `platform-architecture.md` FR-ORCH-005…007

**Also owns host reassignment on `UNAVAILABLE`** (FR-ORCH-005, `IMP-GATE-89`): `IMP-M3-05` counts the
failure and leaves the call for retry, but does not rewrite `routing:`, because the game key needed to
re-select a host is not in Redis. Deciding where that key lives is this item's, in
`game-host-internals.md` §13, before code.

**Done when:** the to-do is keyed by `sessionId`, **not** by a flag on the room — a rematch would
overwrite the previous session's owed teardown. Any rule testing whether a teardown was recorded must
test `room.active_session_id = :sessionId`, a durable fact, rather than the presence of the
`session_teardown` row, which `terminateAndCleanup` deletes on success. The age of the oldest owed row
is exposed so the `TeardownOwed` alert can fire past 15 minutes (`observability.md` §6 sketches the
rule; `platform-operations.md` FR-ALERT-007 defines it, deferred here by `IMP-M0-10`).

**`IMP-GATE-53`: this item wires `detachSession`'s normal-game-end caller** (flow 06, `nextState =
'LOBBY'`, no `closed_reason`) — the game backend's `game_over` notification, once this item's own
session-completion handling recognizes it, calls `RoomSessionDetacher#detach` exactly as
`GraceDeadlineSweepJob` already does for the closure paths.

**Built (session 96):** `game.SessionTerminationClient` (`TerminateSession`, 2 s deadline, reason mapped
onto the proto enum, whole key family deleted on confirmation) behind `room.SessionTerminatorImpl`, which
deletes the `session_teardown` row on success and backs off on failure; `game.GameEndListener`
implemented by `room.RoomGameEndListener` (first delivered `game_over` → `detachSession(..., 'GAME_OVER',
'LOBBY')`); `turnbase.teardown.owed.age` gauge. **Game key decision:** `gamekey:{sessionId}` =
`{gameId}:{gameVersion}`, written with `routing:` (`game-host-internals.md` §13); `GameInputService`
uses it to reassign `routing:` on `UNAVAILABLE` or a vanished host. History recording on `game_over`
is `IMP-M5-01`'s; the retry-limit caller is `IMP-M3-09`'s.

---

### IMP-M3-09 — Game failure handling

**Repo:** `turnbase-platform`, `turnbase-game-host` · **Depends on:** IMP-M3-07, IMP-M2-09

**`IMP-M2-09` added to *Depends on*** (`IMP-GATE-53`, session 45) — this item wires the
retry-limit-failure caller into `room.RoomSessionDetacher#detach`, whose real implementation
(`detachSession`, `room-lifecycle.md` §4) is `IMP-M2-09`'s.

**Read first:**
- `docs/specs/game-host/game-host-internals.md` §8.1 (the session record's failure slot), §9.1, §12
- `docs/specs/internal-grpc/orchestration-gamehost-protocol.md` § *Error model*
- `docs/requirements/platform-architecture.md` FR-FAIL-001…007
- `docs/requirements/game-contracts.md` FR-FA-001…003, NFR-REL-001…002
- `docs/specs/platform/room-lifecycle.md` §4 — the detach mechanism this item's caller invokes
- `docs/specs/flows/07-room-closure.md` § Caller 4 — retry-limit failure fails back to Lobby, not
  closed

**Satisfies:** `platform-architecture.md` FR-FAIL-001…007; `game-contracts.md` FR-FA-001…003,
NFR-REL-001…002

**Also owns the two notices `IMP-M3-05` left** (`IMP-GATE-89`): the unicast `ACTION_REJECTED` on
`/user/queue/errors` (kind, never message) and the player-facing notice at the retry limit.
`GameInputService` already counts `failcount:` and exposes the failure; this item delivers it.

**Done when:** the acting player is told why. `platform-architecture.md` FR-FAIL-001 and FR-FAIL-003
must be coherent about first-failure versus three-failure termination, and the failed input has a
stated disposition on every path.

**`IMP-GATE-53`: this item wires `detachSession`'s retry-limit-failure caller** (flow 07 caller 4,
`nextState = 'LOBBY'`, no `closed_reason`, `SESSION_FAILED` broadcast to clients instead of
`ROOM_CLOSED`, no history entry per `game-history.md` CON-001) — FR-FAIL-005's "notifies the Room
Service" is this call to `RoomSessionDetacher#detach`.

**The session record carries `lastOutcome` and `lastFailure` for a reason** (IR-15). A replayed
sequence that previously failed must return *its own* failure. Without those two slots the replay
returns `lastEffects` from the last *successful* input, so a retry of a rejected move looks to the
client like the move succeeded.

Retry-limit terminations feed the `GameSessionFailureRate` alert (`observability.md` §6 sketches the
rule; `platform-operations.md` FR-ALERT-003 defines it, deferred here by `IMP-M0-10`) — sessions
terminated by retry limit over active sessions, > 1% in 10 minutes.

---

### IMP-M3-10 — The first official game

**Repo:** a sixth repository, `turnbase-game-<name>`, **created when this item starts** ·
**Depends on:** IMP-M3-03

**The repository does not exist yet, and that is deliberate** (decided 2026-08-20). Nothing before
M3 needs a real game, and creating an empty sixth repo at M0 would put a submodule in this tree that
stays empty through four milestones. When this item starts: create it under the
`turnbase-platform` organisation, register it as a submodule, and add it to ADR-0012's repository
table and `CLAUDE.md`'s. It is a **consumer** of the platform, not part of it — which is the whole
point of the item, so it does not become a sixth first-class component.

**Read first:**
- `docs/specs/gdk-api/backend-gdk-api.md` §11 (the worked example) and §§3–8
- `docs/specs/gdk-api/frontend-gdk-api.md` §§3–7, §11
- `docs/specs/manifest/bundle-format.md` §2 (the archive), `manifest-schema.md`
- `docs/decisions/0006-game-trust-model-java-official-only.md`
- `docs/specs/api-design/websocket.md`, `room-websocket.md`, `room-rest-api.md` (the round-trip driver
  speaks them: login → `POST /api/rooms` → `POST …/participants {role}` → `TOGGLE_READY` /
  `START_GAME` → `REQUEST_GAME_SYNC` / `SUBMIT_ACTION`)

**Satisfies:** — *(no requirement. This item exists to prove the GDK contract is implementable by
someone outside the platform team, which ADR-0006 makes the MVP's only game-supply mechanism.)*

**Done when:** the game compiles against the **published SDK artifact only** — a dependency on
`turnbase-game-host` or `turnbase-common` means the contract is not self-sufficient and the item has
failed even if the game runs; it ships a frontend bundle built against the published npm package; it
is packaged per `bundle-format.md` §2 and published through IMP-M4-03's real pipeline; a full
create → join → start → several turns → outcome → history round trip passes against the local stack,
**and one game action shows as a single trace in Tempo spanning client → WebSocket → Orchestration →
gRPC → Game Host** (`observability.md` FR-TRACE-002; the cross-repo half of `IMP-GATE-18`, moved here
from `IMP-M3-05` by `IMP-GATE-89` because it needs a game a Game Host can run). `IMP-M3-05` is a
dependency for that reason.
Also (`IMP-GATE-71`): the bundle is placed in the directory `turnbase.seed.bundles-dir` names, as
`<gameId>.zip` with a fixed UUID (`local-environment.md` §6) — the compose bind mount and the chart
volume are this item's to add — and a clean `make reset-db` lists the game and it can be started.

**Closed:** IMP-GATE-93 (opened and closed 2026-09-30, session 111) — no work item owned the
platform's `REQUEST_GAME_SYNC` handler (`/app/game.{sessionId}.sync` → `GAME_SYNC` on
`/user/queue/game`, `websocket.md` § Game Session Protocol): `IMP-M3-07` listed `GAME_SYNC` as "not
built here — `IMP-M3-08`/`09`", and neither of those (teardown, failure handling) claims it, so the
round trip cannot pass. Fixed by giving the handler to this item, the first whose clause needs it
(remaining item 2 below).

**Done 2026-09-30 (session 113):** `make reset-db` / `make seed` in `turnbase-platform/Makefile` (stop clients, recreate schema + grants + extensions, flush Redis, restart → Flyway + seeder); after a clean reset the game is `ACTIVE` and `e2e-roundtrip.mjs` passes. `TURNBASE_SDK_PAT` now exists and game CI is green. Not built, not required by the clause: the real frontend sends no `traceparent` on STOMP frames, so a browser action's trace starts at the platform's `STOMP SEND` span.

**History:** **session 112:** `GAME_SYNC` handler (`game.{sessionId}.sync`, `GameSyncService`, retained `gamelog:` entries), full round trip login → create → join → ready → start → sync → 5 turns → `GAME_OVER` → history passes on compose, Tempo export fixed (OTLP HTTP 4318 in platform, Game Host, Helm), `STOMP SEND` span parented on `traceparent` and joined by the Game Host `ProcessInput` spans in one trace, Game Host artifact cache survives a restart; repo + submodule, backend (11 tests), frontend (vitest ≥95%), bundle
packaging, compose and Helm seed mounts; **session 111:** Game Host `HostLivenessLoop`
(Register/Heartbeat/ReportContexts/Deregister, re-registers on `NOT_FOUND`), `guest-bridge` jar now
actually contains `io.turnbase.gamehost.bridge.*` (it shipped only the SDK; `GuestBridgeJarIT`
guards it), the image's artifact-cache dir is writable, the platform logs why a session creation
failed. `START_GAME` works on the compose stack.

---

### IMP-M3-11 — GDK test harness

**Repo:** `turnbase-sdk` · **Depends on:** IMP-M3-01, IMP-M3-03 (added by IMP-GATE-69: Done-when
clause 8's "same `ObjectMapper` configuration as the GDK Host" is `io.turnbase:turnbase-serialization`,
which `IMP-M3-03`'s `turnbase-sdk` half builds — `game-host-internals.md` §3.6), IMP-M3-13 (added by
IMP-GATE-91: clause 2's "shared bundle validator" is `io.turnbase:turnbase-bundle-validator`)

**Closed:** IMP-GATE-91 (opened and closed 2026-09-30, session 102) — clause 2 required a validator
artifact shared with the upload pipeline, but the pipeline's validator existed only inside
`turnbase-platform` (Spring-coupled, unpublishable) and no item extracted it. Fixed by `IMP-M3-13`.

**Read first:**
- `docs/specs/gdk-api/test-harness.md` **in full** — §1 is a scope boundary, not a preamble
- `docs/specs/manifest/bundle-format.md` §2.4, §3 and `docs/requirements/game-contracts.md` — the
  validator's entry point and the WebSocket protocol clause 4 speaks (added by IMP-GATE-91; the
  list previously named neither)
- `docs/requirements/game-development-experience.md` FR-HARNESS-001…008, FR-HARNESS-010,
  NFR-UPLOAD-002
- `docs/specs/api-design/websocket.md` § Game Session Protocol, `docs/specs/gdk-api/frontend-gdk-api.md`
  §8–§10 and `docs/specs/game-frontend/game-asset-serving.md` §5 — the wire clause 4 must speak and the
  bootstrap clause 3 must populate (added by session 104: `game-contracts.md` says only that the
  client-facing wire is defined elsewhere, and names neither)

**Satisfies:** `game-development-experience.md` FR-HARNESS-001…008, FR-HARNESS-010

**Closed:** IMP-GATE-67 (opened and closed 2026-09-22) — this item's own *Done when* clause checked
only the executing round trip (FR-HARNESS-010), while its own *Satisfies* claimed the full harness
(FR-HARNESS-001…008) — the CLI launcher, the two-origin browser bootstrap, the mock
Orchestration/WebSocket bridge, bundle-validator reuse before launch, multi-player simulation, log
rendering and team/parameter configuration `test-harness.md` describes at length — none of which
exists anywhere in `turnbase-sdk` yet and which no other registry item claims. Fixed by rewriting
*Done when* below to cover every Must-priority FR-HARNESS clause *Satisfies* already claimed, not just
FR-HARNESS-010. FR-HARNESS-008 (hot reload, "Could") is left out of *Done when* deliberately — it
stays in *Satisfies* as aspirational per its own priority, matching how other items treat "Could"
rows.

**Done when:**
1. `mvn io.turnbase:turnbase-harness:run`, invoked from a game project directory containing a manifest
   and bundle, launches a local environment with no Docker, Redis or database (FR-HARNESS-001,
   FR-HARNESS-006).
2. Before launch, the shared bundle validator (the same artifact `bundle-format.md` gives the upload
   pipeline) runs against the project's manifest and bundle; a fatal finding stops the launch, a
   warning prints and the launch continues (FR-HARNESS-002).
3. The harness serves the game FE (`frontend.entryPoint`) at `http://game.localhost:{port}` and its own
   shell at `http://localhost:{port}`, populating `window.__TURNBASE__` before the game's JS runs
   (`test-harness.md` §3).
4. Two or more browser tabs connect as distinct simulated players through an in-process mock
   Orchestration that speaks `game-contracts.md`'s real WebSocket protocol — session, roster, teams,
   sequence allocation, effect fan-out with the spectator-broadcast-only rule (FR-HARNESS-001,
   FR-HARNESS-003).
5. Team assignment and game parameters are configurable before a session starts — the roster synthesized
   from the manifest's `teamTemplates` at the `count.min` × `size.max` shape, parameters overridable via
   `harness.json` (FR-HARNESS-007).
6. A CLI flag or debug-panel action delivers a mock `action`, `player_joined`, or `player_left` (with a
   selectable `reason`) to a chosen player without opening a browser tab for them, and can force a
   `resync` (FR-HARNESS-005).
7. The game log renders with the platform's Markdown configuration (FR-HARNESS-004).
8. After `onInit` and after every action, the harness runs the executing serialization round trip
   (serialize, deserialize, compare) using the same `ObjectMapper` configuration as the GDK Host;
   `strictSerialization: true` (the default) fails the run on a mismatch, `false` warns and continues
   (FR-HARNESS-010).

**Built (session 104):** module `harness` (`io.turnbase:turnbase-harness`, `io.turnbase.harness`),
plain jar for now. Clause 2 (`PreLaunchCheck`, over the shared `BundleValidator`; a project directory is
an unpacked bundle, zipped in memory — `test-harness.md` §8 now says so), clause 5's roster half
(`RosterSynthesizer`, `HarnessConfig` for `harness.json`) and clause 8 (`LocalGame`: in-process game,
`equals` round trip after `onInit` and every handler, strict/non-strict) hold, with tests. The E5
`gdkApiVersion` check accepts any version and a warning says so (`test-harness.md` §7).

**Built (session 105):** the module is now `maven-plugin` packaging: `RunMojo` (`io.turnbase:turnbase-harness:run`,
`-Dturnbase.harness.dir`/`.port`, no project model needed — verified from a bare directory through Maven,
offline of Docker/Redis/DB) → `HarnessLauncher` (pre-launch check → `GameLoader` → `onInit` → server), also
`HarnessMain`. `HarnessServer` (clause 3): JDK `HttpServer`, both origins on one port told apart by `Host`
(`localhost` shell, `game.localhost` game, anything else 421); the game origin serves the §5 bootstrap with
`window.__TURNBASE__` ahead of the entry-point script, `parentOrigin` fixed from the shell origin, and
serves project files except `manifest.json`, `harness.json`, the backend JAR and anything outside the root.
Clauses 1, 2, 3 (server side) and 8 hold, with tests (`LaunchTest`).

**Built (session 106):** clauses 3–7 complete. `MockOrchestration` speaks the real STOMP-over-WebSocket game session protocol (`websocket.md`): sync flow with `asOfSequence`, `GAME_EVENT`/`GAME_LOG`/`GAME_OVER`/`GAME_PLAYER_JOINED|LEFT` with `sequence`/`index` (lifecycle at `index: -1`), effect-address validation, spectator = broadcast only, identity from the connection. Transport is a hand-rolled RFC 6455 endpoint (`WebSocketServer`, own loopback port, `Origin` must be the shell). The shell (`shell.js`) relays STOMP↔`postMessage` with both halves of the origin check, renders the log through a locked-down Markdown subset, and has the roster/parameters/debug panel; `DebugCommand` is one shape for panel POST, `harness.json` scenario and CLI flags (`--player --action|--join|--leave|--resync`, or `-Dturnbase.harness.*`). `@turnbase/gdk` is injected by import map from the built `dist/index.js` bundled into the harness jar (`publish.yml` now runs the npm build first). Verified in a real browser. **Not built, outside *Done when*:** log colour annotations (syntax is `game-contracts.md` OQ-001), the CSP would-have-blocked report and audit-hook warnings of `test-harness.md` §2–§3, `game-development-experience.md` FR-HARNESS-008.

---

### IMP-M3-12 — FE GDK client (`@turnbase/gdk`)

**Repo:** `turnbase-sdk` · **Depends on:** IMP-M0-02

Opened by IMP-GATE-05 (`IMP-M0-02`, closed 2026-08-22): `FR-FEGDK-001…009` had no owning item in
`turnbase-sdk`, the repository that publishes the package. `IMP-M6-05` implements the platform
shell's half of the postMessage boundary, not the client library itself.

**Read first:**
- `docs/specs/gdk-api/frontend-gdk-api.md` **in full** — §4 handshake, §7 actions, §8 origin
  validation, §9 bootstrap contract, §10 the inbound/outbound envelope
- `docs/requirements/game-development-experience.md` FR-FEGDK-001…009
- `docs/requirements/game-contracts.md` FR-FE-001…006, FR-FA-001…003, NFR-SEC-004

**Satisfies:** `game-development-experience.md` FR-FEGDK-001…009; `game-contracts.md`
FR-FE-001…006, FR-FA-001…003, NFR-SEC-004

**Done when:** `TurnBaseClient<TAction, TEvent>` exists with the five replaceable callbacks
(`onInit`, `onGameEvent`, `onPlayerJoined`, `onPlayerLeft`, `onGameOver`), `start()`, `sendAction()`
and `dispose()`; the inbound message listener accepts a message only when **both**
`event.origin === parentOrigin` **and** `event.source === window.parent` hold (§8); no outbound post
ever uses `targetOrigin: '*'`; `start()` throws synchronously when `window.__TURNBASE__` is missing
and no `parentOrigin` override was supplied; calling `sendAction` before `init` throws.

**The trusted origin is never derived from a received message** — only from the shell bootstrap
(§9) or the explicit test-harness override — because inferring it from message traffic is circular
and is exactly the mistake the origin check exists to prevent.

---

### IMP-M3-13 — Shared bundle validator module

**Repo:** `turnbase-sdk`, then `turnbase-platform` · **Depends on:** IMP-M4-03, IMP-M3-03

Opened by IMP-GATE-91 (`IMP-M3-11`, 2026-09-30): `bundle-format.md` §2.4 and `game-development-experience.md` FR-HARNESS-002 say the
archive reader and validator are one component consumed by the upload pipeline, the unpacker and the
test harness. It was built inside `turnbase-platform` (`upload.ArchiveReader`, `ManifestValidator`,
`BackendJarAnalyzer`, `StateSerializabilityAnalyzer`, `ClassFileUtil`, and the pipeline body of
`BundleValidationService`), where the Spring stereotypes and `platform.common.CheckError` make it
unusable by the harness. Same lesson as the serialization engine (`game-host-internals.md` §3.6):
extract it, or the harness reimplements it and drifts.

**Read first:**
- `docs/specs/manifest/bundle-format.md` §2.4, §3, §4 and `manifest-schema.md`
- `docs/implementation/conventions.md` §5 (cross-repo artifacts) and the *manifest schema is copied*
  paragraph — the schema copy moves to this module
- `turnbase-platform/src/main/java/io/turnbase/platform/upload/` — the code being extracted

**Satisfies:** `game-development-experience.md` FR-HARNESS-002 (the artifact half)

**Done when:**
1. `turnbase-sdk` builds a third module, `io.turnbase:turnbase-bundle-validator`, from the same root
   `./mvnw install`, at the shared version. It has no Spring, no `turnbase-common`, no
   `turnbase-game-host` dependency (the enforcer's banned list applies) and carries its own committed
   copy of `manifest.schema.json` (`scripts/sync-manifest-schema.sh` learns the new path).
2. It exposes the reader, manifest validation, backend JAR analysis and static serializability
   analysis behind one entry point returning framework-free findings (severity, code, message), reusing
   `turnbase-serialization` where the analysis needs it.
3. `turnbase-platform` depends on it (pinned per `conventions.md` §5), its `upload` package keeps only
   the Spring wiring, persistence and async orchestration, and its existing upload unit and integration
   tests pass unchanged.
4. The moved classes' tests move with them and the module meets the JaCoCo gate.

**Built (session 103):** `io.turnbase:turnbase-bundle-validator` in `turnbase-sdk` (package
`io.turnbase.bundle`), entry point `BundleValidator.validate(zip, Options)` → `Result` of
`Finding(severity, code, message)` plus the `Bundle` Phase G needs. The platform's `upload` package
keeps `BundleValidationService` (fetch, trust rule, persistence, Phase G) and maps `Finding` to its own
`CheckError`. Decisions worth knowing: `VersionOrdering` moved with the module (the gdk range check
uses it; the platform imports it); the platform's own copy of `manifest.schema.json` is gone and
`sync-manifest-schema.sh` now targets the module's copy; the static analysis consults
`BindingCapabilities` for JDK map keys and module-dependent types (additive — the hardcoded lists
still apply); `TestBundles`/`TestJavaCompiler` are duplicated in the module's tests because the
platform's ITs still use theirs.

---
