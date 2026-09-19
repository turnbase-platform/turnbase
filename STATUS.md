## Last Session Summary

**Date:** 2026-09-19 (session 56)

**No item completed — `IMP-GATE-62` opened and closed on `IMP-M4-04` before any code.** Picked up
`IMP-M4-04` (bundle publication and asset serving, `READY` off `IMP-M4-03`, `DONE`) per session 55's
own recommendation. Reading its read-list (`bundle-format.md` §5, `game-asset-serving.md` in full,
ADR-0007, `local-environment.md` §7.7) surfaced two problems before any code was written.

First: this item's own *Satisfies* triple-claimed `game-contracts.md` FR-FE-001…006 with `IMP-M3-12`
and `IMP-M6-05` — but FR-FE-001…006 is the game-session postMessage event catalogue (`init`,
`game_event`, `player_joined`, `player_left`, `game_over`, spectator filtering), and
`game-asset-serving.md`'s own Scope section names that catalogue **out of scope** for this document.
Bundle publication and asset serving never touch it.

Second, and more load-bearing: this item's one *Done when* clause ("publication filters") turned out
to already be fully satisfied — `IMP-M4-03`'s `PublicationService` (verified by reading it) already
implements §5.2's deny list verbatim, so the clause was true before this item's own code existed.
Meanwhile the read-list's real remaining scope — `GET /play/{sessionId}` (§5's bootstrap document,
§4.1's version-pinning row) — has no data to resolve against: there is no `sessionId → (gameId,
version)` mapping anywhere in the schema. Game sessions are `IMP-M3-05`'s data to create
(`room.GameSessionStarter` is still `IMP-M2-06`'s no-op stub, confirmed by reading
`PendingGameSessionStarter.java`), and `IMP-M3-05` was not this item's dependency. Same shape as
`IMP-GATE-08`/`18`/`28`/`46`/`53`.

**Fixed** on `turnbase` `master` (branch `docs/imp-gate-62-m4-04-scope`, merged `--ff-only` and
deleted, same session): `IMP-M4-04`'s *Satisfies* dropped `FR-FE-001…006` (unique to `IMP-M3-12`/
`IMP-M6-05` already) and narrowed to `FR-ASSET-001/002/005/006/009` — exactly what `IMP-M4-03` alone
makes buildable: the `Host`-header virtual-routing filter and `GET /g/{gameId}/{version}/**` static
asset serving. Its read-list and *Done when* were rewritten to match. `GET /play/{sessionId}`
(FR-ASSET-003/007) moved to `IMP-M3-05`, which already composes and broadcasts `gameFrontendUrl` on
`GAME_STARTED` and is the only item with session data to resolve the route against — it gained
`IMP-M4-04` in *Depends on*, `FR-ASSET-003/007/008` in *Satisfies* (008 was already being built there,
just never claimed), a read-list addition (`game-asset-serving.md` §4.1/§5/§7), and a *Done when*
clause requiring `START_GAME` to pin `(gameId, version)` on the session record and the route to serve
against it. `python3 scripts/check-corpus.py` clean.

**`IMP-M4-04` is back to `READY` — code is next session's work, none was written this session.** Its
scope is now exactly the `Host`-routing filter plus the static asset route, buildable off `IMP-M4-03`
alone with no other repo or unbuilt item involved.

---

**Date:** 2026-09-19 (session 55)

**`IMP-M4-03` is now `DONE` — 37 of 61.** Upload pipeline and version state machine, picked up per
session 54's own recommendation. One gate opened and closed while implementing: `IMP-GATE-61`.

**`IMP-GATE-61`** — `error-handling.md`'s Bundle Validation Errors § Synchronous claimed
`POST /api/games/{gameId}/versions` was the only endpoint producing a synchronous `422` in the
`{check, message}` shape, and `bundle-format.md` §3.1's phase table grouped Phase B with the
asynchronous C-G background job — both directly contradicted `file-uploads.md`'s flow narrative and
its own § Size Validation, which twice state that `confirm`'s stored-size check (stage B1) fails the
`confirm` request itself, synchronously, before `202` is ever returned. Resolved in
`file-uploads.md`'s favor across both documents (it is the more specific, operational document and
says the same thing twice); `error-handling.md`'s Synchronous section now names both request paths,
and `bundle-format.md` §3.1/§3.2/§3.4 carry B1 as its own synchronous row/heading/bullet, distinct
from the C-G background job.

**Code, `turnbase-platform` `518116d`.** The full Phase A-G pipeline in a new `upload` package:
`VersionUploadController`/`Service` for the synchronous halves (Phase A slot creation — stages
A1-A4; Phase B1 confirm — stored-size check, 410/503 outside the `{check,message}` taxonomy);
`BundleValidationService` orchestrating the async Phases C-G on a dedicated `@Async` executor
(`UploadAsyncConfig` — no async executor existed anywhere in this repo before this item);
`ArchiveReader` — one hand-rolled ZIP central-directory reader (not `java.util.zip.ZipFile`, which
does not expose the general-purpose bit flags §2.2's UTF-8/encryption rules need), reused by
validation and by publication per §2.4's "one reader" rule and one level deep by `BackendJarAnalyzer`
for F1; `BackendJarAnalyzer` (F1-F5, ASM `ClassReader`/`ClassNode`) and `StateSerializabilityAnalyzer`
(F6-F7 — resolves `S` from `TurnBaseGame<S>`'s generic `Signature` attribute, walks its field/record
graph against §4.4's table, detecting the exact GRMP-F4 defect via the `MethodParameters`
attribute/`@JsonProperty` check); `PublicationService` (§5's deny-listed unpack, write-then-verify-
count, and the §5.4 activation transaction under the `game` row lock); `GameVersionRepository`
(direct SQL against `game`/`game_version`, `room.RoomInvitationRepository`'s established
cross-feature-schema precedent) including the authoritative ordering re-check and the narrowed
`VERIFIED → UNVERIFIED`-only badge transition; `UploadSlotCleanupJob` (§7.2's four sweep duties,
`room.RoomPurgeJob`'s `@SchedulerLock` shape) — duty 2 is the fix for a died-mid-validation version
number permanently burning `(game_id, version)`. New `ArtifactStore` abstraction (put/get/delete/
presign) over the existing raw `S3Client`, plus a new `S3Presigner` bean.

**Two real bugs found by the integration test suite, both fixed:** `ArtifactStoreConfig`'s new
`S3Presigner` bean was missing `pathStyleAccessEnabled`, so a presigned PUT URL against MinIO used
virtual-hosted-style addressing and every signature mismatched what the client actually sent (every
confirmed upload's bundle PUT failed with MinIO's `MissingFields`); `S3ArtifactStore
.downloadToTempFile` pre-created its destination with `Files.createTempFile`, but AWS SDK v2's
`S3Client#getObject(request, Path)` refuses to write to a path that already exists (opens
`CREATE_NEW`) — every confirmed bundle's download step threw a swallowed `FileAlreadyExistsException`,
surfacing only as a generic `pipeline.interrupted` `FAILED` status with no indication of the real
cause. Neither would have been caught without exercising the real pre-signed-URL round trip against
real MinIO, which is exactly what `VersionUploadControllerIT`'s happy-path test does.

**Scope notes, not gates — each a deliberate simplification within this item's own Done-when, not a
gap in it:**
- **E4's admin-path detection.** No admin upload endpoint or loopback-auth context exists yet
  (`IMP-M4-05`, not built). E4 checks only the game-row half of ADR-0006's predicate (`badge =
  'OFFICIAL' AND owner_user_id IS NULL`) — correctly, since that half is fully decidable now — and
  omits the "arrived on the admin path" half, since there is no mechanism anywhere in this repo yet
  to decide it. `IMP-M4-05` inherits closing this gap.
- **E5's `gdkApiVersion` range is a configured value, not an assertion against a real guest bridge
  artifact.** `bundle-format.md` §6.1 wants the configured range checked against the deployed guest
  bridge JAR's own declared version at startup; no guest bridge or Game Host gRPC client exists in
  this repo (`game-host-internals.md` is outside this item's read-list). `GdkCompatibilityProperties`
  binds `turnbase.gdk.supported-range` (default `0.3.0-0.3.0`, matching the spec's own MVP value) and
  E5 checks the manifest against it directly; there is nothing yet to assert it against.
- **F6/F7's module-registry knowledge is hardcoded, not read from a shared serialization
  component.** `game-host-internals.md` §5's shared serialization component (the authority §4.4 asks
  this stage to read Jackson's registered-module set from) does not exist as a consumable artifact.
  `StateSerializabilityAnalyzer` hardcodes the same two facts that component would otherwise supply
  (`java.time.*` and `Optional` are unhandled — no `JavaTimeModule`/`Jdk8Module` registered) rather
  than re-deriving a policy; noted at the point in the code where a future shared-component read
  would replace it.
- **No `BUNDLE_VALIDATION_COMPLETE` SSE push.** `notification.AlertPublisher`/`SseAlertPublisher`
  (`IMP-M5-03`) exist and a seam would be trivial to wire, but this item's own Done-when never
  mentions it and the client can already poll `GET .../versions/{uploadId}`. Left as a clean seam,
  not wired — same pattern `IMP-M5-03`'s own session note used for its own scope gaps.
- **Publication's write-then-verify (§5.3 step 3) checks object *count*, not a per-object byte
  checksum.** A cheap, real defence against a half-unpacked tree (a crash mid-write leaves a count
  mismatch, aborting activation) but not full corruption detection — `bundle-format.md` OQ-003
  already tracks the general absence of a per-object integrity digest as unresolved across the whole
  spec, not something this item was asked to close.
- **The `PROCESSING` lease is stamped once at claim, not renewed while the pipeline runs.** Default
  `validation-lease` is 10 minutes against an NFR-UPLOAD-001 target of under 30 seconds per run, so
  the risk of the sweep abandoning a still-running validation is low in practice, but a renewal call
  partway through Phases C-G would close it properly; not implemented this session.

**Verified — every Done-when clause tested explicitly, by name:**
1. *Every non-terminal status has a documented exit, including a died validator* —
   `UploadSlotCleanupJobIT` (duties 1/3/4 against real MinIO) and
   `VersionUploadControllerIT#theSweepFreesAnAbandonedLeaseAndTheVersionNumberCanBeRetried` (duty 2).
2. *A died-mid-validation version number is not permanently burned* — the same test: a `PROCESSING`
   row with an expired lease, swept to `FAILED`, then a fresh slot request for the identical
   `(gameId, version)` succeeds with `201`.
3. *Two open slots cannot walk the active version backwards* —
   `GameVersionRepositoryIT#twoSlotsCannotWalkTheActiveVersionBackwards`: 1.3.0 then 1.2.5 against an
   active 1.2.0, activated in that order; 1.2.5's activation is rejected by the authoritative recheck
   under the `game` row lock, not by request ordering. Proven directly against `activate()` rather
   than through HTTP, since a non-Official game can never reach activation at all (see E4 above) —
   the two-slot race has nothing to do with badge/ownership, so this is a faithful, more direct proof
   of the actual mechanism.
4. *Badge clears `VERIFIED → UNVERIFIED` only* — `GameVersionRepositoryIT`'s four badge tests:
   `VERIFIED → UNVERIFIED`, `UNVERIFIED` stays `UNVERIFIED`, `OFFICIAL` stays `OFFICIAL` on both a
   first and a second activation (the only path the MVP exercises, per ADR-0006) without violating
   `game_official_ownerless_ck`.
5. *Phase A is a synchronous `422`; Phases B-G never are* — four `VersionUploadControllerIT` tests
   for A1/A2/A4's `422`s and A3's `409`; `confirmingBeforeTheObjectIsUploadedIsSynchronous422` for
   B1; `asyncFailuresSurfaceOnlyAsTheVersionResourceNeverAsAnHttpError` asserts the `GET` on a
   `FAILED` version returns HTTP `200` (not `4xx`) with the error in the body.

Plus a real bundle validating end to end through every phase to `ACTIVE`
(`aFullyValidBundleActivates`) with a genuine compiled `TurnBaseGame` implementation and JAR (built
by a new `TestJavaCompiler` test helper — real `javac`, not hand-assembled bytecode, so
`-parameters`/`MethodParameters` — the exact GRMP-F4 defect — is the real compiler's output, not an
approximation); 15 `ArchiveReaderTest` cases (traversal, absolute paths, backslashes, empty
segments, trailing dots, oversized segments, case-insensitive duplicates, entry-count/total/
per-entry/ratio ceilings, corrupt archives); 8 `BackendJarAnalyzerTest` cases (F1-F5); 16
`StateSerializabilityAnalyzerTest` cases against every row of §4.4's table. `./mvnw verify` (207
tests) and `./mvnw verify -Pintegration` (195 tests) both green locally, zero regressions — one
`RoomPurgeJobIT` failure on the first full run was a MinIO Testcontainers startup timeout under this
session's heavy concurrent Docker load, confirmed a flake by an isolated rerun and by the full suite
passing clean on the following run.

**CI green on `turnbase-platform master`** — run `35446728285`, `build` job `22m14s`. `e2e` failed,
confirmed the same non-gating shape flagged since session 50/51
(`dependency failed to start: container compose-platform-1 exited (1)`) — but this run's captured
logs (added by session 50's own e2e fix) finally show the actual cause for the first time: the
platform container fails Spring context refresh on `RedisRateLimiterConfig` with `NOAUTH HELLO must
be called with the client already authenticated` — the e2e compose profile's Redis requires a
password the platform container isn't configured to send. Unrelated to this item (Redis
authentication, not uploads); recorded here since it is the first session to actually see the
cause rather than an opaque `exited (1)`. Submodule ref bumped to `518116d`.

**`IMP-M4-02` is now `DONE` — 36 of 61.** Manifest schema validation, picked up per session 53's own
recommendation now that `IMP-GATE-60` had specified the copy mechanism. No spec defect this time —
the read-list (`manifest.schema.json`, `manifest-schema.md`, `bundle-format.md` §3,
`game-development-experience.md` FR-MANIFEST-001…009) was sufficient.

**Code, `turnbase-platform` `0728237`.** `upload.ManifestValidator` runs the committed
`manifest.schema.json` copy (created this session at
`turnbase-platform/src/main/resources/manifest/`, via `scripts/sync-manifest-schema.sh`) as Layer 1
through `com.networknt:json-schema-validator` (Draft 2020-12) rather than hand-written per-field
checks. Layer 2 covers what the schema can't express: team-template/parameter range ordering, the
conditional team-template name, parameter-default membership/bounds per type, duplicate parameter
keys, and the IR-12 rejection of `capabilities.ai: true`. Unknown keys are collected as non-fatal
`warnings`, matching the schema's deliberately lenient `additionalProperties` stance.
`ManifestValidationResult` carries `errors`/`warnings` as `common.CheckError` (`{check, message}`),
the shape `error-handling.md`'s bundle-validation format already uses. Archive/JAR/activation checks
(`bundle-format.md` Phases A, B, C, E, F, G) stay `IMP-M4-03`'s job — this validator only ever sees an
already-parsed manifest document.

**Also fixed, found while committing the schema copy:** neither `.gitattributes` file pinned
`manifest.schema.json` to LF, unlike `gamehost.proto` — `sync-manifest-schema.sh`'s own header
comment (session 53) claimed the same "pinned to LF on each side" guarantee `sync-proto.sh`'s does,
copied verbatim, but the pin itself was never added. Under this environment's `core.autocrlf=true` a
fresh clone would checkout the two copies with different line endings, and `--check`'s
`--strip-trailing-cr` masks exactly that case locally without fixing it for a real diff. Fixed: both
`.gitattributes` files gained a `text eol=lf` pin, mirroring `*.proto`'s. Not gated — a missing
safeguard the script's own comment already claimed existed, not a documents-contradict-each-other
defect — recorded in the registry so it isn't rediscovered as a mystery CI flake.

**Verified.** `ManifestValidatorTest` (unit): the spec's own worked example validates clean; each
Layer 2 rule and the `capabilities.ai` rejection independently produce the documented `check` id; an
unrecognized key warns without affecting `valid()`; an empty document produces the full
missing-required-field error set. `./mvnw verify` and `./mvnw verify -Pintegration` green locally.
Pushed directly to `turnbase-platform master` (no PR, ADR-0012) after `pre-push` passed; CI run
`34893340481`'s `build` job green (19m42s). `e2e` failed on the same pre-existing, non-gating
smoke-test issue flagged since session 50/51 (`platform-operations.md` OQ-002) — unrelated to this
change. Submodule ref bumped in this repo.

**Not resolved, left for the user:** `turnbase-platform`'s remote branch
`feat/imp-m4-02-manifest-schema-validation` — already merged `--ff-only` into `master` and deleted
locally, but this session's sandbox denied remote-branch-delete permission, same as three prior
sessions' branches (`feat/imp-m2-10-reconciliation`, still outstanding from session 49/50/51/52/53
too — this makes at least two stale merged remote branches now waiting on a human with push rights).

---

**Date:** 2026-09-14 (session 52)

**`IMP-M5-03` is now `DONE` — 35 of 61.** Notifications and the SSE stream, picked up per session
51's own recommendation now that `IMP-GATE-59` had specified the REST surface. No spec defect this
time — the read-list (`notifications-invitations.md`, `data-model-notifications.md` §1/§3/§4,
`sse-notifications.md` in full, `notification-rest-api.md` in full, `rest-conventions.md` §
*Authorization and Ownership*, `pagination-filtering-sorting.md`, `platform-operations.md` FR-JOB-013/
FR-RET-001…006) was sufficient, and the retention-purge index and `room_invitation.expires_at` the
Done-when clause names were both already in the baseline migration from `IMP-M2-12`.

**Code, `turnbase-platform` `93a4f2f`.** `notification.NotificationController`/`Service`/`Repository`
build the five `notification-rest-api.md` endpoints against direct SQL on `notification` — this
package's own table, so no cross-schema read like `RoomInvitationRepository`'s. `NotificationStream
Controller` (`GET /api/notifications/stream`) and `NotificationEmitterRegistry` build the SSE half:
the registry mirrors `websocket.WebSocketConnectionRegistry`'s two-index shape (connections by
emitter id, a secondary index by user id), sends the `sse-notifications.md` § Keepalive comment on a
30s `@Scheduled` tick, and closes a stream on `session.SessionRevokedEvent` with a final `event: alert`
naming `revoked_reason` (`FR-SESS-010`, `IMP-GATE-28` — the SSE half `IMP-M2-02` already closed for
STOMP). Offline catch-up (`delivered_at IS NULL`, oldest `event_seq` first, stamped as sent) is
`NotificationRepository#markUndeliveredAsDelivered`. `AlertPublisher`'s real implementation,
`SseAlertPublisher`, replaces the no-op `PendingAlertPublisher` (deleted) — `IMP-M2-12`'s existing
`alertPublisher.publish(...)` call for `INVITATION_ACCEPTED`/`INVITATION_DECLINED` now reaches a
connected host with no change on that side.

**Scope note, not a gate: live push of a newly created notification to an already-open stream is not
built here.** `room.RoomInvitationRepository` and `social.SocialRepository` write `notification` rows
by direct SQL with no dispatch call of any kind — unlike alerts, no placeholder port existed for them
to call, and this item's own Done-when clause names only offline catch-up and the revocation-close
behaviour, not a live-push guarantee for an already-connected client. An already-open stream sees a
new row only at the next panel open or badge refresh, not pushed instantly. `sse-notifications.md`'s
own "at-least-once at best... the notification center is the backstop" reasoning covers this gap, and
closing it for two other already-`DONE` items' repositories is outside what this item's Done-when
asks for — recorded here rather than silently, since the next session touching live notification
delivery should not have to rediscover it.

**Verified.** `NotificationEmitterRegistryTest` (unit, mocked `SseEmitter`, the
`WebSocketConnectionRegistryTest` pattern) — alert routing by user id, silent drop when offline,
session-scoped close-with-final-alert, keepalive. `NotificationControllerIT` (integration, real
Postgres) — all five endpoints including ownership `404`s, the guarded one-way `read_at` transition
and its `422` on `{"read":false}`, mark-all-read and delete scoped to the principal, delete
idempotency, and a stream test using the JDK `HttpClient` that asserts the exact `event: notification`
frame shape `sse-notifications.md`'s wire example specifies and confirms `delivered_at` gets stamped.
`./mvnw verify -Pintegration` green locally, zero regressions (176 integration tests total including
every pre-existing suite). Pushed directly to `turnbase-platform master` (no PR, ADR-0012) after the
`pre-push` hook passed; CI run `34883859139`'s `build` job green (19m31s — tests, coverage, Trivy,
image push). `e2e` failed on the same `compose-platform-1` exit-`1` issue session 51 already flagged
as unexplained and unrelated to this change (it fails inside the full compose smoke test, not on
anything notification-specific); per `platform-operations.md` OQ-002 e2e gates nothing pre-merge, so
this does not block `DONE`. Submodule ref bumped in this repo.

---

**Date:** 2026-09-14 (session 51)

**No item completed — `IMP-GATE-59` opened and closed on `IMP-M5-03` before any code.** Picked up
`IMP-M5-03` (notifications and the SSE stream, `READY` off `IMP-M1-06, IMP-M1-07`, both `DONE`) per
`STATUS.md`'s own recommendation. Reading its read-list end to end (`notifications-invitations.md`,
`data-model-notifications.md` §1/§3/§4, `sse-notifications.md` in full, `platform-operations.md`
FR-JOB-013/FR-RET-001…006) found the item's *Satisfies* claims FR-NOTIF-001…009 in full — notification
center access, unread badge, read/unread state, mark-all-read, delete, pagination — but no document
anywhere defines the notification center's REST surface. `sse-notifications.md` specifies only the
stream endpoint; `rest-conventions.md`'s Authorization table already assumed `GET /api/notifications`
and `/api/notifications/{id}` exist (naming the ownership predicate and the principal-scoping rule)
without any document ever stating their methods, bodies, or status codes; `room-invitation-rest-api.md`
§6 independently pointed at the same missing endpoint as where a received `ROOM_INVITATION` is read.
Same shape as `IMP-GATE-31`/`33`/`35`/`37`/`57`/`58` — confirmed real, not a document this item merely
hadn't read, since two independent existing documents both assumed it. Also: this item's own read-list
never named `rest-conventions.md` or `pagination-filtering-sorting.md`, despite both supplying
conventions the missing surface has to follow.

**Fixed** on `turnbase` `master`, commit range on branch `docs/imp-gate-59-notification-rest-api`
(merged `--ff-only`, branch deleted, both locally and on the remote, same session): new
`docs/specs/api-design/notification-rest-api.md` — five endpoints (`GET /api/notifications` paginated
list, `GET .../unread-count` for the bell badge, `PATCH .../{id}` mark-read, `POST .../read-all`,
`DELETE .../{id}`), each endpoint's status codes, request/response bodies, and ownership handling spelled
out, plus a deliberate design note on why the unread count is its own endpoint rather than a field on
the list envelope (the bell must be populated before the panel is ever opened, and refreshed on every
SSE push, neither of which has a list request to piggyback on). Registered in
`docs/specs/api-design/INDEX.md`; `room-invitation-rest-api.md` §6 and its Related table now cite the
new document by name instead of a bare requirement ID. `IMP-M5-03`'s read-list gained
`notification-rest-api.md` in full, `rest-conventions.md` § *Authorization and Ownership*, and
`pagination-filtering-sorting.md`; its *Done when* clause gained an explicit line requiring the five
endpoints to exist and match that document exactly. `python3 scripts/check-corpus.py` clean.

**`IMP-M5-03` is back to `READY` — code is next session's work, none was written this session.** The
five-endpoint surface is now fully specified; the item's own `Done when` (retention-purge partial
index, SSE registry subscribing to `SessionRevokedEvent` on `IMP-M1-06`'s revocation) is unchanged
beyond the new endpoint clause. `IMP-M3-01`, `IMP-M3-02`, `IMP-M4-01`, `IMP-M4-02`, `IMP-M6-01` remain
independently `READY` for anyone who wants a different track.

---

**Date:** 2026-09-13 (session 50)

**`IMP-M2-12` is now `DONE` — 34 of 61.** Room invitations: send, decline, and acceptance via the
ordinary join endpoint. Two gates opened and closed while reading this item's own read-list, before
any code, the second superseding the first.

`IMP-GATE-57`: the item's Done-when clause claimed all of FR-JOIN-004's invalidity conditions resolve
to an empty list, but `room-rest-api.md` §3.1 already specifies the no-slot/no-spectate case returns a
full room resource with `canJoin: false, canSpectate: false`, not "not found."

`IMP-GATE-58` (supersedes `IMP-GATE-57` — that clause turned out not to belong to this item at all):
verifying prior art before writing code found the invite-*link* mechanism `IMP-GATE-57` was correcting
is entirely `IMP-M2-01`'s, already shipped (`RoomController`/`RoomService`/`RoomRepository`, read
directly, not assumed) — `FR-HOST-002`, `FR-JOIN-003…004`, `NFR-SEC-002` were double-claimed with
`IMP-M2-01`'s own *Satisfies*, and `FR-JOIN-006`/`008` with `IMP-M2-05`'s, both `DONE` items. Separate
double-claim: `FR-LINK-001…002` was claimed by both this item and `IMP-M5-03`, neither building
anything for it — reassigned to `IMP-M2-01`. Separately, no document anywhere defined this item's
actual REST surface (`room-rest-api.md` §8 explicitly defers FR-HOST-001's notification invites
elsewhere, but "elsewhere" was a requirements document with no endpoints) — same shape as
`IMP-GATE-35`/`37`. Fixed: new `docs/specs/api-design/room-invitation-rest-api.md` (send, decline;
acceptance is `IMP-M2-01`'s existing join endpoint, which gains one clause: a successful join resolves
the caller's pending invitation and alerts its inviter, a failed join leaves it pending so FR-INV-005
doesn't cost the player their invitation); `rest-conventions.md`'s Authorization table and
`room-rest-api.md` §5/§8/Related updated to match; `IMP-M2-12`'s *Satisfies* narrowed to
`FR-INV-001…009, FR-HOST-001`; `IMP-M2-01` gains `FR-LINK-001…002`; `IMP-M5-03` drops them. Also
caught and fixed in-flight: an unverified citation of `room-lifecycle.md`'s ownership-claim mechanism
in the new spec's step 1 (that mechanism fences `room.version`/WebSocket-affinity writes only,
`room_invitation` needs neither — fixed to a plain row-level `FOR UPDATE`), and a wrong assumption that
FR-INV-002's friends check would go through `social.RelationshipQueries` (it doesn't — `RoomRepository
#isVisible` already established direct-SQL-against-`friendship` as this package's actual precedent for
FR-LIST-006, so the implementation follows that, not the public API).

**Code, `turnbase-platform` `f2e3bfd`.** `RoomInvitationRepository`/`RoomInvitationService`/
`RoomInvitationController` (`POST /api/rooms/{roomId}/invitations`, `DELETE …/invitations/me`), direct
SQL against `app_user`/`friendship`/`notification` matching `SocialRepository`'s established
cross-feature-schema precedent. `RoomRepository#joinRoom` gained the accept-on-success clause
(`room-rest-api.md` §5 step 7); a failed join leaves the invitation untouched. New
`notification.AlertPublisher` port + `PendingAlertPublisher` no-op impl for FR-INV-006's alerts —
`IMP-M5-03` isn't built and isn't a dependency, same seam pattern as `SessionTerminator`/
`PendingSessionTerminator`. `RoomInvitationControllerIT` — 9 new tests (host-only, friends-only,
self-invite, idempotent resend, idempotent decline, accept-resolves, failed-join-leaves-pending), all
green; full `./mvnw verify -Pintegration` clean with zero regressions across every existing suite. CI
green on `turnbase-platform` `master` (run `34780943436`, commit `f2e3bfd`) — `build` job passed;
`e2e` failed, initially assumed to be the same pre-existing `lstat /target` defect session 44's
`IMP-GATE-52` note flagged as known-and-accepted. It was not, on closer look — see below.

**`e2e` follow-up, user-requested, out of `IMP-M2-12`'s own scope but done this session.** Diffing run
`34780943436` against the prior run `34768436866` (`IMP-M2-10`'s push) showed the identical `lstat
/target` failure shape in both, which at first read like confirmation of "still the known issue." It
was not: `.github/workflows/build.yml`'s `e2e` job builds `turnbase-game-host`'s jar from its sibling
checkout (`working-directory: turnbase-game-host`, a "Build turnbase-game-host" step) but has **no
equivalent step for `turnbase-platform` itself** — `needs: build` only orders the job after `build`,
it does not carry that job's `target/` over (separate runner, GitHub Actions jobs share nothing on
disk). `docker compose up --build` then fails the platform image's own `COPY target/turnbase-platform-
*.jar app.jar` because nothing in the `e2e` job's own checkout ever produced that jar — every `e2e` run
since session 44 has been failing on this, misdiagnosed as the earlier issue because the error message
is identical. **Fixed** (commit `9771934`): added the missing `./mvnw package -DskipTests` step,
mirroring the existing `turnbase-game-host` one. Confirmed by re-running CI (`34782193808`): the
platform image now builds and the container starts — but then exits `1` within ~20s inside the compose
stack, a real, different, still-unexplained runtime failure. `e2e-smoke.sh` never captured `docker
compose logs` before its `cleanup` trap tore the stack down, so the crash reason was invisible in CI.
**Also fixed** (commit `855438b`): `e2e-smoke.sh` now prints `docker compose logs` on an `up --wait`
failure before cleanup runs.

**Handoff for the next session — this is exactly where it stops:** commit `855438b` was pushed and a
third CI run (`34783240475`) was in progress, not yet observed to completion, when this session ended
at the user's request. **The actual reason `compose-platform-1` exits `1` is still unknown** — the next
session's first move should be `gh run view 34783240475 --repo turnbase-platform/turnbase-platform
--log --job <e2e job id>` (or the next push's run, if `34783240475` has rotated out) and read the
now-captured platform container log. Candidates worth checking first, none confirmed: a required
`.env`/compose-only config value `e2e-smoke.sh` doesn't set that `local-environment.md` §7 expects: a
Flyway migration issue specific to the fresh `test` database this compose profile creates (unlikely —
the same baseline runs clean under every Testcontainers IT); or a readiness dependency on MinIO's
bucket existing before `minio-init` has actually finished (the log ordering — `minio-init Exited` then
immediately `platform Starting` — looked plausible but unconfirmed). **This is still non-blocking**
(`FR-CICD-003`/`OQ-002`, `continue-on-error: true`) — nothing is gated on it, so there's no urgency,
only unfinished diagnosis. Submodule ref bumped to `855438b` and `IMP-M2-12` flipped to `DONE` in the
registry regardless, since `IMP-M2-12`'s own `build`-job gate (the one that matters for it) is green
and unrelated to any of this.

**Not resolved, left for the user:** `turnbase-platform`'s stale merged remote branch
`feat/imp-m2-10-reconciliation` (left over from session 49) — a third session's sandbox denied
remote-push permission for the delete.

---

**Date:** 2026-09-13 (session 49)

**`IMP-M2-10` is now `DONE` — 33 of 61.** Picking the item back up, the code turned out to already
exist: `turnbase-platform`'s `master` carried commit `852d415` ("feat(room): adoption and
reconciliation jobs (IMP-M2-10)"), already CI-green, with its own remote branch
(`feat/imp-m2-10-reconciliation`) already ff-merged but never deleted — the only things actually
outstanding were this repo's submodule ref (still pointing at `a2fc0a3`, `IMP-M2-09`'s commit) and the
registry/`STATUS.md` bookkeeping, which had not caught up to reflect it. Verified rather than assumed:
read `ReconciliationJob`, `RoomRepository`'s new reconciliation queries, `SessionTerminatorImpl`,
`ReconciliationMetrics`, `RoomOwnershipService`'s new `isInstanceAlive`/`sentinelPresent`/
`ensureSentinel`, `PodIdentity.bootAt()`, `RoomPurgeJob` and the `orphaned_session_flag` migration
against every read-list document and the *Done when* clause; all five duties, both guard exemptions,
the two-strike persistence split (`room.reconcile_flagged_at` vs `orphaned_session_flag`), and the
`SESSION_UNRECOVERABLE`-free Lobby fail-back match the corpus as fixed by `IMP-GATE-54/55/56`. Also
resolved is the session 48 open item that was never gated because it had an answer, just not yet a
written one: `SessionTerminatorImpl` now performs `terminateAndCleanup` step (c)'s bookkeeping itself
(`RoomRepository.recordSessionTeardownFailure`, 10s-doubling-to-5min backoff) rather than silently
no-opping, since there is still no Game Host gRPC client and every call honestly takes the failure
branch. Ran `./mvnw verify` and `./mvnw verify -Pintegration` locally (both green) and confirmed CI
green on `turnbase-platform` `master` at `852d415`. This session's own work: committed the leftover
submodule ref bump (`d18ce06`) and brought the registry and this file up to date.
**`turnbase-platform`'s remote branch `feat/imp-m2-10-reconciliation` is already ff-merged into
`master` but still exists on the remote** — a leftover the ADR-0012 "merge and delete in the same
session" rule should have caught; deleting it requires a remote-push permission this session's
sandbox denied, so it is still there for the next session (or the user) to remove. `python3
scripts/check-corpus.py` clean.

**Guard-exemption bookkeeping worked out this session, so the next one does not have to re-derive it
from the same two documents**: of the five FR-JOB-007 duties, only (e) (adopt) is exempt from *both*
FR-JOB-008 guards, per the explicit text in both `room-lifecycle.md` §5.4 and
`flows/05-owner-loss-and-adoption.md` §D. Duties (b), (c) and (d) are named explicitly, by letter, as
taking *both* guards in both documents. **Duty (a) (owed-teardown re-drive) is named in neither
enumeration** — `room-lifecycle.md` §5.4's guard-2 paragraph says "the other **three** repair duties"
take the two-strike rule after excluding only (e), which is arithmetically 4 remaining, not 3; guard
3's paragraph names "(b), (c) and (d)" by letter, once again omitting (a). Read as deliberate rather
than a miscount (a `session_teardown` row is a confirmed, already-durable debt, not an *inferred*
divergence — the entire premise guard 2 exists to guard against does not apply to it, unlike (b)/(c)/
(d) which are all "is this actually gone, or did I just observe it badly" inferences), so duty (a)
takes **guard 1 (reachability) only**. Not gated — a self-consistent reading, not a contradiction —
but worth recording so it is not re-litigated as if it were still open.

**Also unresolved, not gated because it has an answer, just not yet a written one**: `SessionTerminator`
is `void`, so neither `RoomSessionDetacherImpl`'s inline call nor duty (a)'s re-drive can see whether a
termination attempt succeeded, yet duty (a)'s own done-when clause requires "on failure `attempts++`,
backoff 10s doubling to a 5min cap" — and `room-lifecycle.md` §4's `terminateAndCleanup` pseudocode
places that exact bookkeeping (steps b/c: delete-on-`OK`, `attempts++`/backoff-on-error) **inside**
`terminateAndCleanup` itself, not in either caller. Reading `PendingSessionTerminator`'s own Javadoc
("matching `PendingGameInputDispatcher`'s 'never pretend delivery succeeded' precedent") together with
that pseudocode: the fix is to make `PendingSessionTerminator` actually perform step c's bookkeeping
(there is no gRPC client, so step a always fails, honestly) via a new `RoomRepository`
session-teardown-failure method mirroring `recordOutboxAttemptFailure`'s shape, computing
`next_attempt_at = now() + least(10 * 2^attempts, 300)` seconds. No design gap once this is written
down; it just wasn't reached this session.

**`IMP-M2-10` code is next session's actual work — none was written this session.** The prior-art map
from session 47 (`RoomOwnershipService.claim()`, `RoomSessionDetacherImpl`, `SessionTerminator`,
`GuestPurgeJob`'s `@SchedulerLock` precedent, `JobsProperties.Reconcile` already bound) still stands
unchanged; this session only closed two more read-list/guard gaps duty (a) and (b) exposed once their
implementation was actually drafted. A Flyway migration for `orphaned_session_flag` is now also part
of this item's scope, alongside the five duties, the daily purge job (FR-JOB-009), the reconciliation
metrics (FR-JOB-011: `turnbase.reconcile.candidates{duty}` gauge,
`turnbase.reconcile.repairs.total{duty,result}` counter, `turnbase.job.aborted.total{job,reason}`
counter) and a boot-instant field on `PodIdentity` for the startup-suppression guard.

---

**Date:** 2026-09-13 (session 47)

**`IMP-M2-10` is still `WIP` — `IMP-GATE-55` opened and closed; no code written this session either.**
Picking the item back up (session 46 left it read-list-corrected, code next), a research pass into
`turnbase-platform`'s existing room-package prior art (`RoomOwnershipService`, `RoomRepository`,
`GraceDeadlineSweepJob`, `SessionTerminator`) surfaced that duty (c) — "In Progress room with no
session fails back to Lobby" — collides with `game-rooms.md` FR-LIFE-007 and `room-websocket.md`'s
`ROOM_CLOSED` reason table, both of which said the platform **closes** that same room with
`SESSION_UNRECOVERABLE`. First reading: a flat contradiction between `platform-operations.md`
FR-JOB-007(c)/`room-lifecycle.md` §5.2 (Lobby) and those two documents (Closed). Second reading, after
finding `flows/07-room-closure.md` § Caller 5 (missing from this item's read-list, despite being the
one place all five `detachSession` callers are enumerated together): that document already reconciles
the two sides — "fail back to Lobby; `SESSION_UNRECOVERABLE` only if that also fails" — but the
reconciliation is itself hollow, because `detachSession`'s own shared skeleton has exactly two
non-success outcomes (a deferred claim, retried next tick; an idempotent no-op) and neither is a
"failure" duty (c) could close on. `SESSION_UNRECOVERABLE` has no producer anywhere in the corpus as
specified. Fixed: `room-lifecycle.md` §5.2 and `flows/07-room-closure.md` now state explicitly that
duty (c) has no closure branch; `game-rooms.md` FR-LIFE-007 narrowed to the idle-Lobby case alone;
`room-websocket.md`'s `ROOM_CLOSED` and `data-model.md`'s closure-reasons tables both drop
`SESSION_UNRECOVERABLE` (five closure paths become four). Separately, duty (c)'s "notify participants"
cited `platform-architecture.md` FR-FAIL-005, which names no wire event; fixed by naming the existing
`GAME_ENDED` event (`readinessReset: true`) as its client notification instead of inventing a new
type, since the described behaviour — back in Lobby, readiness reset — is that event's contract
verbatim. `IMP-M2-10`'s read-list gains `flows/07-room-closure.md` § Caller 5. Committed at `9022865`
on `turnbase` `master` (branch `docs/imp-gate-55-session-unrecoverable-lobby-vs-closed`, merged
`--ff-only` and deleted same session). `python3 scripts/check-corpus.py` clean.

**`IMP-M2-10` code is next, and the research already done should carry forward**: `RoomOwnershipService
.claim()` already implements the full adoption procedure (§1.4 steps 1–5, 7) — duty (e) just needs a
new `RoomRepository` query for unowned-room IDs and a call to `claim()` per candidate, no adoption
logic to write fresh. `RoomSessionDetacherImpl.detach()` is the exact claim-then-mutate pattern duties
(c) and (d) need (it already claims the room if this instance doesn't own it, then runs the state
transition under `RoomEventExecutor`). `SessionTerminator`/`PendingSessionTerminator` (a no-op stub)
is duty (a)'s reuse point for `terminateAndCleanup`; `session_teardown` has no reader anywhere yet —
duty (a)'s `next_attempt_at`/`attempts`-backoff query and update are new. All Flyway columns this job
needs already exist (`room.reconcile_flagged_at`, `.ownerless_since`, `room_idle_lobby_idx`,
`session_teardown.next_attempt_at`) — no new migration required. `turnbase.jobs.reconcile.*` config is
already bound (`JobsProperties.Reconcile`). `ShedLock` is already wired (`account.GuestPurgeJob` is the
`@SchedulerLock` precedent); FR-JOB-007 is explicitly single-instance per FR-JOB-005 (not
ownership-partitioned like FR-JOB-006), so one `@SchedulerLock`-guarded `run()` covering all five
duties is the right shape — duty (e) only skips the two `FR-JOB-008` *guards* internally, not the lock.

---

**Date:** 2026-09-13 (session 45)

**`IMP-M2-09` is now `DONE` — 32 of 61.** Room closure and the five detach paths, run in two passes.

**Pass 1 — `IMP-GATE-53` opened and closed.** Reading the item's own read-list surfaced that its
*Done when* required wiring all three of `detachSession`'s remaining callers (host-leave with no
humans, normal game end, retry-limit permanent failure), but two of those three have no trigger
anywhere in this item's dependency closure: normal game end (FR-LIFE-002) and retry-limit failure
(FR-FAIL-003/005) both originate in the Orchestration Service, which is `IMP-M3-05` and its
dependents — not built yet, and not a dependency of `IMP-M2-09`. Same shape as
`IMP-GATE-08`/`18`/`28`/`46`. Fixed in `docs/implementation/registry.md`: `IMP-M2-09` narrowed to the
mechanism plus the one reachable caller (host-leave with no humans, via `RoomService#leave`);
`IMP-M3-08` and `IMP-M3-09` each gained `IMP-M2-09` in *Depends on* and a Done-when clause naming
their own call site. Committed at `461ddbb` on `turnbase` `master`. `python3 scripts/check-corpus.py`
clean.

**Pass 2 — implementation, `turnbase-platform` `a2fc0a3`.** Replaced the no-op
`PendingRoomSessionDetacher` with the real `detachSession` (`room-lifecycle.md` §4): a fenced,
version-bumping room update via `RoomEventExecutor#execute` (not a bespoke transaction), FR-INV-008's
invitation deletion at closure, and durable `session_teardown`/outbox bookkeeping (ADR-0010), all
idempotent on `active_session_id`. A new `SessionTerminator` seam (`PendingSessionTerminator` for now)
stands in for the Game Host `TerminateSession` call, matching `GameSessionStarter`/
`GameInputDispatcher`'s precedent since no gRPC client to the Game Host exists in this repo yet. Wires
the one caller `IMP-GATE-53` left reachable: `RoomService#leave` now closes a room immediately with
`NO_PLAYERS_REMAINING` when the departing host leaves no other human player behind. Also fixed a
latent gap in `IMP-M2-07`'s own sweep duty 1 (`GraceDeadlineSweepJob`): it evaluated closure
unconditionally instead of only when a session is attached, which would have closed every Lobby room
a rolling deploy's mass grace-reservation open (§1.4 step 4) leaves behind — exactly what FR-DC-007
forbids, invisible until this item's detacher stopped being a no-op. `RoomSessionDetacherImplIT`,
updated `GraceDeadlineSweepJobIT`/`RoomControllerIT`; CI (`build`, run 34754357250) green. Submodule
ref bumped `417ecf9..a2fc0a3` and `docs/implementation/registry.md` flipped to `DONE` here.

**Process note:** this session ran via `scripts/autonomous-work-loop.sh` (a new unattended
`claude -p` loop, one fresh session per item). Pass 1 ran out of its per-session budget cap before
touching code (design reading only) — cap raised from $3 to unlimited for future runs. Pass 2
completed the implementation and pushed, but ended its turn expecting to "check back" on CI once it
went green, which doesn't exist non-interactively — left the top-level registry/submodule-ref bump
uncommitted until a human (via the outer session) watched CI to completion and finished the commit.
The script's prompt now tells sessions to block synchronously on CI (`gh run watch --exit-status`)
rather than ever ending a turn to check something "once it completes".

---

**Date:** 2026-09-13 (session 44)

**IMP-M2-08 — Reconnect and resync. DONE. 31 of 61 items complete.** `turnbase-platform master` now
has the snapshot-then-delta reconnect path at `7948aea`: a reconnecting client's `SUBSCRIBE` gets a
version-stamped snapshot and only deltas from that version forward (no merge path), a rejoin inside
the grace window restores the caller's existing seat/team via the reused-row upsert below rather than
re-seating them, and a rejoin after expiry falls through to the ordinary join path and its capacity
checks.

**IMP-GATE-50** (opened and closed same session) — `data-model.md` §2 says `room_participant` keeps
one row per `(room_id, user_id)` for a user's whole history in a room (never deleted, `left_at` marks
release), but `room-rest-api.md` §5 step 6 said "Insert" unconditionally — impossible to satisfy the
moment someone who previously left (voluntary, kicked, or grace-expired) rejoins, since the row
already exists. Fixed: both documents now specify `INSERT ... ON CONFLICT (room_id, user_id) DO
UPDATE`, reinitializing the departed row.

**IMP-GATE-51** (opened and closed same session) — `IMP-M2-08`'s *Satisfies* claimed
`reconnection-flow.md` FR-REJOIN-001…008 in full, but no *Done when* clause tested FR-REJOIN-007 (a
reconnect that loses the race to its own grace expiry must be told plainly, not dropped silently), and
no document named the call path or predicate for the already-registered `SLOT_RELEASED` error code.
Fixed, building on `IMP-GATE-50`'s row reuse: `room-websocket.md`'s Authorization Model now specifies
the predicate (`left_at IS NOT NULL AND leave_reason = 'GRACE_EXPIRED'` on the caller's own row) and
the call site (`SUBSCRIBE`, rejecting with `SLOT_RELEASED`); `IMP-M2-08`'s *Done when* gained the
clause.

**IMP-GATE-52** (opened and closed same session, found verifying this item's CI run) — MinIO stopped
publishing to Docker Hub some time after `IMP-M0-07`/`M0-08` pinned `minio/minio`/`minio/mc` there
with no registry host; every consumer (`docker-compose.yml`, the Helm chart's `values.yaml`, and both
Testcontainers pins in `PostgresIntegrationTest`/`ArtifactBucketReadinessCheckIT`) resolved to the now
-dead `docker.io/minio/…` and failed `pull access denied ... repository does not exist` — CI's `build`
job failed identically three times on this before the cause was found, across all ~22 IT classes
extending `PostgresIntegrationTest`, regardless of which item was being worked. Not a code defect in
`IMP-M2-08`, and not fixable by retrying. Fixed: every pin (`local-environment.md` §1,
`docker-compose.yml`, `values.yaml`, both Testcontainers `DockerImageName.parse(...)` calls, each also
gaining `.asCompatibleSubstituteFor("minio/minio")` — Testcontainers validates the bare repo name
regardless of host) now points at `quay.io/minio/minio`/`quay.io/minio/mc`, confirmed byte-identical
by digest to the dead Docker Hub references. Committed on top of `IMP-M2-08`'s own merge at
`417ecf9`. **CI green** on `turnbase-platform master`'s `build` job (run `34749048422`, 18m23s).

**`e2e` still fails, but on a new defect, not the old one** — worth knowing before anyone next looks
at it: MinIO itself now pulls and starts fine in the real compose stack (confirming `IMP-GATE-52`
fixes more than just Testcontainers), and the job gets past `turnbase-game-host` checkout and build
for the first time — then dies on `lstat /target: no such file or directory` inside the e2e smoke
test's own Docker build context. Every prior session's accepted `e2e` failure was the unprovisioned
`TURNBASE_GAME_HOST_PAT` failing at checkout, before the pipeline ever reached this point. Not
investigated or gated this session (out of `IMP-M2-08`'s scope) — expect this failure mode, not the
PAT one, next time `e2e` comes up.

**Also this session:** committed a leftover `turnbase-platform` submodule ref bump
(`d94db38`, `35b1aff` — a CI-only fix from session 43, verified green, never pushed to the parent
repo) that had been sitting uncommitted since the prior session ended.

**Two agents worked this item concurrently for part of the session** (the main session and a forked
subagent), both editing the same working trees before noticing — caught before anything was committed
and reconciled into the single account above, but worth a beat of caution for any future session that
delegates to a background fork while continuing to work the same checkout directly.

**The autonomous work-item loop that picked up `IMP-M2-08` was stopped by user request once this item
was finished** — `IMP-M2-09`, `IMP-M2-10` and `IMP-M2-12` remain `READY` and unpicked; the loop did not
continue into them.

---
## Next Priorities

**`IMP-GATE-62` is closed — `IMP-M4-04` is `READY` again, narrowed.** See *Last Session Summary*.
Its scope is now just the `Host`-routing filter and `GET /g/{gameId}/{version}/**`, buildable off
`IMP-M4-03` alone — the natural next pick, and small. `IMP-M3-05` (orchestration client and session
registry) gained the `/play/{sessionId}` bootstrap-document work this gate carved out of `IMP-M4-04`,
plus `IMP-M4-04` in its own *Depends on* — it is not startable until `IMP-M4-04` is `DONE`.
`IMP-M4-05` (admin API — review queue and badges) is still independently `READY` off `IMP-M4-03`.

**`IMP-M4-03` is now `DONE` — 37 of 61.** See prior session's summary. `IMP-M4-04` (bundle publication
and asset serving) and `IMP-M4-05` (admin API — review queue and badges), both `READY` off it, are
the natural next picks — `IMP-M4-05` in particular is where E4's deferred admin-path-detection half
(this session's scope note) has to land, since it's the item that actually builds the loopback-bound
admin auth context. `docs/specs/deployment/local-environment.md` §6's seeded-game item (`IMP-M0-01`
row, depends on `IMP-M4-03`) is also now unblocked. Independently `READY`: `IMP-M3-01`/`M3-02`
(GDK backend API / Game Host skeleton), `IMP-M5-01` (game history, off `IMP-M3-09` — confirm that
dependency is actually `DONE` first), `IMP-M6-01` (Astryx integration, off `IMP-M0-05`).

**Still outstanding, not gated to any item: the `e2e` CI job's `compose-platform-1` exit-`1`
failure — now with a real cause, not just a shape.** This session's captured logs show the platform
container failing Spring context refresh on `RedisRateLimiterConfig`: `NOAUTH HELLO must be called
with the client already authenticated` — the e2e compose profile's Redis instance requires a
password the platform container isn't configured to send. Worth a dedicated look (likely a missing
`SPRING_DATA_REDIS_PASSWORD` in the e2e compose profile's platform service env, or a Redis image
default-auth mismatch) — out of scope for `IMP-M4-03`, which only confirmed the shape matched prior
sessions' non-gating failure before moving on.

**`IMP-M4-02` is now `DONE` — 36 of 61.** See *Last Session Summary*. `IMP-M4-03` (upload pipeline
and version state machine), `READY` off it, is the natural next pick: it's the consumer
`ManifestValidator` was built for, and its own Done-when already names the Phase A–G checks that sit
around this item's Layer 1/2 validation (`bundle-format.md` §3.2).

**`IMP-M5-03` is `DONE` — 35 of 61.** See session 52's summary. Its one deliberate scope gap
(live push of a newly created notification to an already-open stream isn't wired for the two existing
producers, `room.RoomInvitationRepository` and `social.SocialRepository`) is recorded there, not
gated — pick it up only if a future item's own Done-when actually needs it.

**Independently `READY` next picks:** `IMP-M3-01`/`IMP-M3-02` (GDK backend API surface / Game Host
skeleton, `turnbase-sdk`/`turnbase-game-host`), `IMP-M4-01` (catalog listing), `IMP-M4-03` (upload
pipeline, above), `IMP-M5-01` (game history recording, off `IMP-M3-09` — check that dependency is
actually `DONE` before claiming), `IMP-M6-01` (Astryx integration, `turnbase-frontend`, off
`IMP-M0-05`). `IMP-M5-04` (retention purge jobs) is **not** yet startable: it depends on `IMP-M5-01`,
still `READY`, not `DONE`.

**Still outstanding, not gated to any item: the `e2e` CI job's `compose-platform-1` exit-`1` failure.**
Unrelated to notifications — this session's `build` run (`34883859139`) was green, `e2e` failed on the
same shape flagged since session 50/51. Read a recent run's `docker compose logs` output (captured
since session 50's fix) before diagnosing further.

**`IMP-M2-12` is now `DONE` — 34 of 61, and M2 is fully complete.** See *Last Session Summary*.
**`IMP-M5-03`** (notifications and the SSE stream), `READY` off `IMP-M1-06, IMP-M1-07` (both `DONE`),
is the natural next pick: it builds the real `NotificationEmitterRegistry`/SSE dispatch that
`notification.PendingAlertPublisher` (this session's no-op seam) is waiting to be replaced by, and
`IMP-M2-12`'s two alert types (`INVITATION_ACCEPTED`/`INVITATION_DECLINED`) plus the four
`FRIEND_REQUEST*`/`FRIEND_ADDED` notification types `IMP-M1-09` already writes are all ready
consumers with no wiring of their own left to do. Otherwise, fully independent tracks are open:
`IMP-M3-01` (GDK backend API surface, `turnbase-sdk`) and `IMP-M3-02` (Espresso context lifecycle,
`turnbase-game-host`) need no other repo's work first; `IMP-M4-01`/`M4-02` (catalog listing, manifest
validation, `platform`) are `READY` off `M1-01`/`M0-06`; `IMP-M6-01` (Astryx integration,
`turnbase-frontend`) is `READY` off `M0-05`.

**Still outstanding, not this session's to fix:** `turnbase-platform`'s stale merged remote branch
`feat/imp-m2-10-reconciliation` — three sessions' sandboxes in a row have denied remote-push
permission for the delete; needs a human or a session with that permission.

**`IMP-M2-08` is now `DONE` — 31 of 61.** `IMP-M2-09` (Room closure and the five detach paths —
including `detachSession`'s real implementation, replacing the `PendingRoomSessionDetacher` stub
`IMP-GATE-49` left) is `READY` off it and the natural next pick. `IMP-M2-10` (Adoption and
reconciliation jobs) is `READY` off `IMP-M2-03` independently; `IMP-M2-12` (room invitations) is
`READY` off `IMP-M2-01, IMP-M1-09` independently. The `minio` pull failure (`IMP-GATE-52`) is fixed —
no infra blocker remains for any of them.

**`IMP-M2-07` is now `DONE` — 30 of 61.** `IMP-M2-08` (Reconnect and resync) and `IMP-M2-09` (Room
closure and the five detach paths — including `detachSession`'s real implementation, replacing the
`PendingRoomSessionDetacher` stub `IMP-GATE-49` left) are both `READY` off it and are the natural
next picks. `IMP-M2-10` (Adoption and reconciliation jobs) is `READY` off `IMP-M2-03` independently.
`IMP-M2-12` (room invitations) remains `READY` off `IMP-M2-01, IMP-M1-09` independently.

Two things worth knowing before picking up `IMP-M2-09`: it inherits `IMP-M2-07`'s two call sites
(duty 1 step 4, duty 2's closure half) rather than writing its own, and `notifications-invitations.md`
FR-INV-008's invitation deletion belongs inside `detachSession` itself (`data-model.md` §1's Closure
reasons section — "every one of these five paths owes the same two side effects"), not bolted onto
each of its three additional callers separately.

A discovered-but-out-of-scope orphan, worth a look before `IMP-M2-08`/`M2-09` land: `game-rooms.md`
FR-XFER-001 (automatic host transfer on an ordinary voluntary leave, not a disconnect) does not
appear in any item's current *Satisfies* — `IMP-M2-06` dropped it, `IMP-M2-09` only claims
FR-XFER-002/005. `RoomService#leave` (the REST/voluntary path) still has no host-transfer logic at
all. Not gated this session since nothing in `IMP-M2-07`'s own Done-when touches it, but it will
surface the next time someone builds or tests a host voluntarily leaving a room with other players
still in it.

**`IMP-M2-11` is now `DONE` — 29 of 61.** `IMP-M3-05` (orchestration client and session registry — the
item that replaces `PendingGameSessionStarter` with a real implementation and gives `START_GAME` its
`GAME_STARTED` broadcast), `READY` off `IMP-M3-04, IMP-M2-04, IMP-M2-06`, is the natural next pick once
its own game-host dependency (`IMP-M3-04`) is ready; until then, `IMP-M2-07` (disconnect, grace
deadlines, sweeps) and `IMP-M2-10` (adoption and reconciliation jobs), both `READY` off `IMP-M2-03`
independently, and `IMP-M2-12` (room invitations), `READY` off `IMP-M2-01, IMP-M1-09` independently,
remain the pickable items that need no other repo's work first.

**IMP-GATE-45** (`IMP-M2-05`, opened and closed 2026-09-09, session 40) — `room-websocket.md`'s
Member Commands table states a role precondition for `TOGGLE_READY`/`SWITCH_TO_SPECTATOR` (non-host
human player) and `SWITCH_TO_PLAYER` (spectator), but the error-code registry — which claims to be
"the registry for every WebSocket error code in the corpus" — had no code for violating it. Fixed:
`room-websocket.md` gained `ROLE_NOT_ELIGIBLE` and a note that the *Authorized sender* column is
server-enforced. `IMP-M2-05` is now `DONE`.

**IMP-GATE-43** (`IMP-M2-04`, opened and closed 2026-09-09, session 40) — `IMP-M2-04`'s own read-list
(`room-websocket.md`'s versioning section) and `IMP-M2-01`'s own read-list (`room-rest-api.md` §5)
both require `PLAYER_JOINED`/`PLAYER_LEFT` to be broadcast, version-stamped, from the REST join/leave
transactions — but `IMP-M2-01` (`DONE`) shipped without it, because the lock-scoped
commit-then-publish executor those sentences presuppose is exactly what `IMP-M2-04` builds, and it
didn't exist yet. Fixed: `IMP-M2-04`'s *Depends on* gains `IMP-M2-01`, its read-list gains
`room-rest-api.md` §5–§6, and its *Done when* gains the two broadcast clauses; `IMP-M2-01`'s section
gained a note naming `IMP-M2-04` as the owner.

**IMP-GATE-44** (`IMP-M2-04`, opened and closed 2026-09-09, session 40) — `room-rest-api.md` §5
documented the Redis claim running *after* the join transaction commits, but `room-lifecycle.md` §2.1
and `room-websocket.md`'s versioning section require "lock outer → transaction inner → publish after
commit," and §2.1 says a stalled database blocks REST joins on the *same* lock a STOMP command uses —
only true if the lock is acquired before the mutation, not after. Fixed: `room-rest-api.md` §5's claim
moves to step 0, before the transaction; §6 (leave, which never claimed at all before) gained the
matching claim/lock/version/broadcast paragraph, with a failed claim skipping the broadcast rather
than failing the request (leave's existing text already accepted running unclaimed).

**`IMP-M2-04` is now `DONE` — 26 of 61.** `IMP-M2-05` (join, teams, readiness), `READY` off
`IMP-M2-04` alone, is now unblocked and the natural next pick — it builds its STOMP command handlers
against the `RoomEventExecutor` this item just shipped. `IMP-M2-07` (disconnect, grace deadlines,
sweeps) and `IMP-M2-10` (adoption and reconciliation jobs) are `READY` off `IMP-M2-03` independently;
`IMP-M2-12` (room invitations) is `READY` off `IMP-M2-01, IMP-M1-09` independently. `IMP-M2-06`
(host management and transfer) and `IMP-M2-11` (in-room chat) both wait on `IMP-M2-05`.

**`IMP-M2-02` is `DONE` — 25 of 61.** STOMP endpoint, auth, subscriptions, `turnbase-platform`,
pushed and green in CI (see Last Session Summary). Nothing else in the registry names `IMP-M2-02` as
a dependency, so its completion does not itself move any other item to `READY` — `IMP-M2-04` and
`IMP-M2-12` were already `READY` independently of it (below) and remain the natural next picks; the
room member/host command handlers `IMP-M2-05`/`M2-06`/`M2-11` need `IMP-M2-04`'s event
versioning/fan-out first, not this item.

**`IMP-M2-04`** (room event versioning and fan-out) is `READY` off `IMP-M2-03` alone — it is the
mechanism `IMP-M2-01`'s own leave/host-transfer gaps (deferred `lost_announced_at` tails, broadcast)
are waiting on, and the natural next pick: it is what turns `room-websocket.md`'s per-room `version`
counter and delta-publish-under-lock into a real component, which `IMP-M2-05` (join/teams/readiness)
then builds its command handlers against. **`IMP-M2-12`** (room invitations) is `READY` off
`IMP-M2-01, IMP-M1-09` independently.

**IMP-GATE-41** (`IMP-M2-01`, opened and closed 2026-09-08, session 38) — this item's read-list never
named `docs/specs/platform/data-model-catalog.md`, though `room-rest-api.md`'s create transaction and
its §3 listing predicate both depend on it: the three room-creation preconditions (FR-GAME-013,
FR-GAME-007, FR-PRV-002 — deleted/archived/listed/badge on `game`) were never stated, and the
`canJoin`/`canSpectate` predicate and row shape (FR-LIST-002, FR-LIST-003a) need
`game_version.min_players`/`.max_players`/`.supports_ai`/`.supports_spectators`/
`.supports_mid_game_join` — columns that document alone supplies. Also fixed a naming defect this
exposed: `room-rest-api.md` wrote `game.capabilities.midGameJoin`/`.spectating`, matching neither
`manifest-schema.md`'s real field (`capabilities.spectators`, not `.spectating`) nor the persisted
column (`game_version.supports_spectators`). Fixed: `room-rest-api.md` §2/§3/§5 now name
`gameVersion.supports_mid_game_join`/`.supports_spectators` and cite `data-model-catalog.md` §2; §2's
`gameId` row states the three preconditions explicitly; *Related* gained the citation; `IMP-M2-01`'s
read-list gained `data-model-catalog.md` §1–§2. **`IMP-M2-01` is `WIP` (session 38) and code is
next.**

**IMP-GATE-40** (`IMP-M2-01`, opened and closed 2026-09-08, session 37) — this item's Done-when clause
5 needs the room-ownership claim/redirect/`503` mechanism that `IMP-M2-03` builds, but `IMP-M2-03`
depended on `IMP-M2-02`, which depended on `IMP-M2-01` — a cycle in substance. `IMP-M2-04`, `IMP-M2-07`
and `IMP-M2-10` already depend on `IMP-M2-03` directly and needed no change. Fixed: `IMP-M2-03`'s
*Depends on* moves to `IMP-M1-06`; `IMP-M2-01`'s gains `IMP-M2-03`; `IMP-M2-02`'s gains `IMP-M2-03`
alongside `IMP-M2-01`. **`IMP-M2-03` is now the item to build first** — `IMP-M2-01` and `IMP-M2-02`
both wait on its claim component. `IMP-M2-01` is back to `READY` (not `WIP`) pending `IMP-M2-03`.

**IMP-GATE-39** (`IMP-M2-01`, opened and closed 2026-09-08, session 37) — this item's read-list never
named `docs/specs/platform/room-lifecycle.md`, though `room-rest-api.md` (its own read-list document)
cites it repeatedly for the ownership-claim mechanism behind Done-when clause 5 and the host-leave
delegation boundary in §6. Separately, `room-rest-api.md` builds FR-JOIN-007, FR-XFER-003 and
FR-HOST-002 entirely in this item's own REST endpoints, but this item's *Satisfies* claimed none of
them while `IMP-M2-05` and `IMP-M2-06` each claimed one anyway, over a STOMP-layer read-list that
never touches the REST handlers that actually build them. Fixed: `IMP-M2-01`'s read-list gained
`room-lifecycle.md` §1.2–§1.4, §1.7 and part of §4; its *Satisfies* gained FR-JOIN-007, FR-XFER-003,
FR-HOST-002; `IMP-M2-05`'s *Satisfies*/*Done when* dropped FR-JOIN-007; `IMP-M2-06`'s *Satisfies*
dropped FR-HOST-002 and FR-XFER-003. Superseded by `IMP-GATE-40` before any `IMP-M2-01` code was
written — see above.

**IMP-GATE-37** (`IMP-M1-10`, opened and closed 2026-09-08, session 36) — no document named the
JSON/redirect REST surface this item builds (the OAuth-initiate route, the pending-registration JSON
endpoints, the FR-AUTH-016 challenge-and-link endpoint), and the item's read-list never named
`rest-conventions.md` either. Same shape as IMP-GATE-31/33/35. Fixed: new
`docs/specs/api-design/oauth-rest-api.md` — five endpoints, the `turnbase_oauth_pending` cookie, two
new `local-environment.md` §7.4 TTL properties; `rate-limiting.md` Tier 1 gained the link-challenge
route and Tier 5's OAuth row now names its exact enforcement point; read-list corrected. `IMP-M1-10`
is back to `WIP` and code is next.

**IMP-GATE-38** (`IMP-M1-10`, opened and closed 2026-09-08, session 36) — `user-accounts.md`
NFR-SEC-006 never named this item's five endpoints as session-exempt (same shape as IMP-GATE-29).
Fixed: NFR-SEC-006 now names all five; read-list corrected.

**M1 is fully DONE, and `IMP-M2-03` now too — 23 of 61.** `IMP-M2-01` (room CRUD and listing) is
`READY` off `IMP-M1-06, IMP-M2-03` (`IMP-GATE-40` corrected the second dependency) — this is the next
pick. Its listing predicate needs a `friendship` join for `FRIENDS_ONLY` rooms, which `IMP-M1-09`
supplies; its Done-when clause 5's `503`/redirect/affinity-header behaviour now has
`room.RoomOwnershipService.claim()` to call. `IMP-M2-02` (STOMP endpoint) is `READY` off
`IMP-M2-01, IMP-M2-03` once `IMP-M2-01` lands. `IMP-M2-12` (room invitations) is `READY` off
`IMP-M2-01, IMP-M1-09`. `IMP-M5-03` (notifications and the SSE stream) is `READY` off
`IMP-M1-06, IMP-M1-07` — it now delivers the `notification` rows this item writes over SSE, rather
than writing any of its own for friend requests (`IMP-GATE-34`).

**IMP-GATE-35** (`IMP-M1-09`, opened and closed 2026-09-08, session 34) — no document in the corpus
ever defined this item's REST surface. `rest-conventions.md`'s Authorization table has named the
`/api/friend-requests/{id}` ownership predicate since it was written, but nothing supplied the
endpoints it governs, and this item's read-list never named `rest-conventions.md` either. Same shape
as `IMP-GATE-31`/`33`, at the scale of a whole feature rather than one route. Fixed: new
`docs/specs/api-design/social-rest-api.md` — seven endpoints (username search, send, list, accept,
cancel/decline, friend list, unfriend) plus a `relationshipState` extension to `GET
/api/users/{username}` for FR-SOC-016; registered in that directory's `INDEX.md`; read-list corrected.

**IMP-GATE-34** (`IMP-M1-09`, opened and closed 2026-09-08, session 34) — the item's *Satisfies*
claimed `notifications-invitations.md` FR-FREQ-001…006 in full, and `IMP-M5-03` independently claimed
the identical full range, but neither item's *Done when* clause tested the other's overlap — this
item's never mentioned notifications, and `IMP-M5-03`'s tested only the generic retention/alert
mechanics. `data-model-notifications.md` §3's type table settles it: the four
`FRIEND_REQUEST*`/`FRIEND_ADDED` rows are written at the moment a `friend_request` is created,
accepted, or declined — this item's own transactions. Same shape as `IMP-GATE-28`, in reverse: there
the generic item over-claimed; here it does too, but in the opposite direction (the specific producer
is `IMP-M1-09`, not the infrastructure item `IMP-M5-03`). Fixed: `IMP-M5-03`'s *Satisfies* narrowed to
drop FR-FREQ-001…006; `IMP-M1-09` keeps the claim, its *Done when* gained explicit notification-write
clauses for send/accept/decline/cancel, and its read-list gained `data-model-notifications.md` §1/§3.

**IMP-GATE-33** (`IMP-M1-08`, opened and closed 2026-09-08, session 33) — no document named a route
for FR-ACCT-004 itself (the deletion trigger); `rest-conventions.md`'s self-scoped account routes
named the identity, password and privacy mutations but nothing that deletes the account, and
`IMP-M1-08`'s read-list never named `rest-conventions.md`. Same shape as `IMP-GATE-31`. Fixed:
`rest-conventions.md` gained `DELETE /api/users/me` — `204`, clears the session cookie and closes live
connections per `FR-SESS-010`, no confirmation step at the API layer; read-list corrected.

**IMP-GATE-32** (`IMP-M1-08`, opened and closed 2026-09-08, session 33) — the item's *Satisfies*
claimed the full `FR-ACCT-004…010` range, but `FR-ACCT-009` (deleted-profile placeholder) and
`FR-ACCT-010` (password change) are already implemented and claimed by `IMP-M1-07`, and neither
appears in `IMP-M1-08`'s own *Done when* clause. Same shape as `IMP-GATE-08`/`18`/`28`/`30`. Fixed:
narrowed to `FR-ACCT-004…008`, the erasure duties this item actually builds.

**IMP-GATE-31** (`IMP-M1-07`, opened and closed 2026-09-08, session 32) — no document in the corpus
named a route for FR-ACCT-002 (username update) or FR-ACCT-003 (email update); `rest-conventions.md`'s
self-scoped account routes named the password and privacy endpoints but nothing for these two, and
`IMP-M1-07`'s own read-list never named `rest-conventions.md` at all despite it supplying the
routes/status codes for every endpoint the item builds. Fixed: `rest-conventions.md` gained
`PATCH /api/users/me` — one endpoint for both fields, each enforcing its own rolling 30-day window
independently, email rejected outright when OAuth-sourced (FR-AUTH-008/012); read-list corrected.

**IMP-GATE-30** (`IMP-M1-05`, opened and closed 2026-09-08, session 31) — `IMP-M1-05`'s *Satisfies*
claimed the full `FR-GUEST-001…010` range, but FR-GUEST-010 (guest profile display) needs a
`GET /api/users/{username}` endpoint that doesn't exist until `IMP-M1-07`, which was never a
dependency here — and `user-accounts.md` FR-PROF-002 states the identical duty under a different ID
in the same document, a duplicate `docs/requirements/INDEX.md` doesn't track since it only lists
cross-document prefix collisions. Same shape as `IMP-GATE-08`/`IMP-GATE-18`/`IMP-GATE-28`. Fixed:
`IMP-M1-05` narrowed to `FR-GUEST-001…009`; `IMP-M1-07`'s *Satisfies* gained `FR-GUEST-010` alongside
its existing `FR-PROF-002`.

**IMP-GATE-29** (`IMP-M1-05`, opened and closed 2026-09-08, session 31) — `user-accounts.md`
NFR-SEC-006's exempt list named the login and registration endpoints but not guest creation, even
though `rest-conventions.md`'s Authentication section derives its own "except" set from that exact
list and separately states `POST /api/auth/guest` is unauthenticated outright, matching
`rate-limiting.md`'s Tier 5 text — and a caller minting a guest account has no session yet by
definition. Fixed: NFR-SEC-006 now names the guest-creation endpoint, with the reason inline.
`IMP-M1-05`'s read-list also gained `rest-conventions.md` § Authentication, which named the endpoint
itself and was missing.

**Phase 1 is under way. Work from [`docs/implementation/INDEX.md`](docs/implementation/INDEX.md), not
from this file.** The registry holds **61 live work items** (IMP-M6-07 is cancelled), each with a
read-list, dependencies, the requirement IDs it satisfies and a done-when clause; this section only
says which of them to pick up.

**IMP-GATE-26** (`IMP-M1-04`, opened and closed 2026-09-06, session 29) — the item's *Satisfies*
claimed the full `FR-AUTH-001…016` range, including six OAuth-only requirements
(`FR-AUTH-007…012, 016`) and `VW-OAUTHCOMP-001…002`, but its *Done when* clause never mentioned OAuth
and its read-list didn't even carry the document naming the OAuth client secret's config key.
Fixed: `IMP-M1-04` retitled *Credential registration and login* and narrowed to `FR-AUTH-001…006, 011,
013…015`; the OAuth round trip (consent redirect, code exchange, signed `state`, the FR-AUTH-016
email-collision challenge-and-link path) is new item **`IMP-M1-10`**, `READY` off `IMP-M1-04`, which
is now `DONE` (see *Last Session Summary*).

**IMP-GATE-28** (`IMP-M1-06`, opened and closed 2026-09-08, session 30) — `IMP-M1-06`'s *Satisfies*
claimed `FR-SESS-010` in full, but its actual duty (closing a session's live WebSocket/SSE connections
on revocation) needs a connection registry that doesn't exist yet — `IMP-M2-02` and `IMP-M5-03` are
both still `READY`, and `IMP-M5-03` didn't claim `FR-SESS-010` at all despite SSE being one of the two
connection types the requirement names. Fixed: `IMP-M1-06` narrowed to `FR-SESS-001…004, FR-SESS-011`
plus publishing a `SessionRevokedEvent`; `IMP-M2-02` and `IMP-M5-03` each gained the corresponding
close-on-revocation `Done when` clause (`IMP-M5-03` also gained `FR-SESS-010` in *Satisfies* and
`IMP-M1-06` as a dependency, for the event type).

**IMP-GATE-27** (`IMP-M1-04`, opened and closed 2026-09-06, session 29) — no document in the corpus
named the session cookie itself, only its `httpOnly`/`Secure`/`SameSite=Strict` properties
(`user-accounts.md` CON-004); `rest-conventions.md`'s Authentication section, the natural home, was
also missing from `IMP-M1-04`'s read-list. Fixed: `rest-conventions.md` now names it —
`turnbase_session`, `Path=/` — as a fixed constant every server-side reader (the future STOMP
handshake, SSE endpoint, and any authenticated-route filter) must agree on; read-list corrected.

**IMP-GATE-30** (`IMP-M1-05`, opened and closed 2026-09-08, session 31) — `IMP-M1-05`'s *Satisfies*
claimed the full `FR-GUEST-001…010` range, but FR-GUEST-010 (guest profile display) needs a
`GET /api/users/{username}` endpoint that doesn't exist until `IMP-M1-07`, which was never a
dependency here — and `user-accounts.md` FR-PROF-002 states the identical duty under a different ID
in the same document, a duplicate `docs/requirements/INDEX.md` doesn't track since it only lists
cross-document prefix collisions. Same shape as `IMP-GATE-08`/`IMP-GATE-18`/`IMP-GATE-28`. Fixed:
`IMP-M1-05` narrowed to `FR-GUEST-001…009`; `IMP-M1-07`'s *Satisfies* gained `FR-GUEST-010` alongside
its existing `FR-PROF-002`.

**IMP-GATE-29** (`IMP-M1-05`, opened and closed 2026-09-08, session 31) — `user-accounts.md`
NFR-SEC-006 enumerated the endpoints exempt from session authentication ("the landing page, the login
endpoint, the registration endpoint, user profile pages, the game catalog, game detail pages") and
omitted guest creation, but `rest-conventions.md`'s Authentication section derives its own "except"
set from that exact list, and separately states `POST /api/auth/guest` is "an unauthenticated `POST`"
outright, matching `rate-limiting.md`'s Tier 5 text. A caller minting a guest account has by
definition no session yet. Fixed: NFR-SEC-006 now names the guest-creation endpoint, with the reason
inline. `IMP-M1-05`'s read-list also gained `rest-conventions.md` § Authentication, which named the
endpoint itself and was missing.

**Before starting any of them: no pull requests** (ADR-0012, amended 2026-09-05). Branch, build,
merge to `master`, delete the branch — all within one session. Dependabot is frozen, so nothing
arrives on its own any more; a dependency bump is now an ordinary change on an ordinary branch.

**Progress: 24 of 61 done** — `IMP-M0-01` (gRPC stubs, `turnbase-common`), `IMP-M0-02` (SDK
build-and-publish floor, `turnbase-sdk`), `IMP-M0-03` (Platform Monolith skeleton,
`turnbase-platform`), `IMP-M0-04` (Game Host skeleton, `turnbase-game-host`), `IMP-M0-05`
(Frontend skeleton, `turnbase-frontend`), `IMP-M0-06` (Flyway baseline, `turnbase-platform`),
`IMP-M0-07` (local stack compose profile, `turnbase-platform`), `IMP-M0-08` (Helm chart,
`turnbase-platform`), `IMP-M0-09` (configuration and secrets wiring, `turnbase-platform` +
`turnbase-game-host`), `IMP-M0-10` (observability baseline, `turnbase-platform` +
`turnbase-game-host`), `IMP-M0-11` (CI/CD workflows, all five repos), `IMP-M3-12` (FE GDK
client, `turnbase-sdk`), `IMP-M1-01` (error model, REST conventions, validation harness,
`turnbase-platform`), `IMP-M1-03` (JWT key set, issuance, rotation, `turnbase-platform`),
`IMP-M1-04` (credential registration and login, `turnbase-platform`), `IMP-M1-06` (session
lifecycle and displacement, `turnbase-platform`), `IMP-M1-05` (guest minting and purge,
`turnbase-platform`), `IMP-M1-07` (profiles and privacy settings, `turnbase-platform`),
`IMP-M1-08` (account deletion and erasure, `turnbase-platform`), `IMP-M1-09` (social graph —
friendships and requests, `turnbase-platform`), `IMP-M1-02` (rate limiter, Tiers 1-5,
`turnbase-platform`), `IMP-M1-10` (Google OAuth registration and login, `turnbase-platform`) and
`IMP-M2-03` (ownership claim, lease, epoch fence, `turnbase-platform`) and `IMP-M2-01` (room CRUD and
listing, `turnbase-platform`), all pushed and green in CI.
**M1 is complete; M2 is under way.**
**No work item is gated**, and all 23 readiness blockers remain closed, so an item's status is
whatever its own dependencies imply.

**M1 is fully DONE, and `IMP-M2-03`/`IMP-M2-01` too.** `IMP-M2-02` (STOMP endpoint) is `READY` off
`IMP-M2-01, IMP-M2-03` — both now satisfied — and is the next pick: it re-verifies ownership at
subscribe time using the same `room.RoomOwnershipService` this item's REST handlers already call.
`IMP-M2-12` (room invitations) is `READY` off both `IMP-M2-01` and `IMP-M1-09`. `IMP-M5-03`
(notifications and the SSE stream) is `READY` off `IMP-M1-06` and `IMP-M1-07`, and now delivers
`IMP-M1-09`'s `notification` rows over SSE rather than writing any of the friend-request types itself
(`IMP-GATE-34`).

**IMP-GATE-25** (`IMP-M0-11`, opened and closed 2026-09-05) — `game-development-experience.md`
CON-003 and ADR-0012's Release Strategy commit `turnbase-sdk` to Maven Central + npm, but no document
names a license for it, and Maven Central's publish validation rejects a POM with no `<licenses>`.
Raised to the project owner (a real decision, not a CI mechanic), who deferred it. Fixed: both
documents now say the Maven Central/npm publish is deferred until a license is chosen. Only the Maven
half gets an interim home (GitHub Packages, same as `turnbase-common`) — GitHub Packages' npm registry
requires a scope matching the `turnbase-platform` org, which `@turnbase/gdk` (FR-FEGDK-007) cannot
satisfy, so the npm package stays unpublished by any registry until the public one is available.

**IMP-GATE-24** (`IMP-M0-11`, opened and closed 2026-09-05) — FR-CICD-007/008 require a tag-triggered
production deployment and rollback, but ADR-0001 defers all cloud/production deployment to post-MVP
and names the local Docker Desktop cluster as the only CI-exercised deploy path — no production target
exists for a workflow to reach. Fixed: FR-CICD-007/008 marked deferred to post-MVP in
`platform-operations.md`; ADR-0001's *Affected documents* updated to record it. `IMP-M0-11`'s own
*Satisfies*/*Done when* narrowed to match — FR-CICD-006 (image push to a registry) stands.

**IMP-GATE-23** (`IMP-M0-11`, opened and closed 2026-09-05) — `platform-operations.md` FR-CICD-002/003
and OQ-002's resolution gated the pipeline on a **pull request** ("the PR cannot be merged...", "PR
feedback loops"), but ADR-0012 (amended 2026-09-05) suspends pull requests project-wide, so a
`pull_request` trigger would never fire. Fixed: FR-CICD-002 retitled *Pre-merge checks* and reworded
to gate on push to `master`; FR-CICD-003 and OQ-002 updated to match. No workflow code changed — the
five repos' `build.yml` files already run on push.

**`IMP-M0-11` is now DONE.** `IMP-M0-12` (seed data) stays not-`READY` — it depends on `IMP-M4-03`,
which has not been picked up. **M0 is otherwise finished, and `IMP-M1-01`/`IMP-M1-03` are now DONE
too.** Next up in M1 (accounts and sessions — see *Then, in dependency order* below): `IMP-M1-04`
(credential registration and login — narrowed from *Registration and login* by IMP-GATE-26; OAuth is
now the separate `IMP-M1-10`), `READY` off both `IMP-M1-01` and `IMP-M1-03`, is the natural next pick —
it is the first item to actually create an `app_user`/`user_session` row through an endpoint rather
than a test fixture. `IMP-M1-02` (rate limiter, Tiers 1–5), `READY` off `IMP-M1-01`, remains
independently pickable if `IMP-M1-04` is deferred. `IMP-M0-10` left five small
obligations on later items, each recorded as a sentence in that item's own section rather than a
gate: `IMP-M2-02` exposes `turnbase_websocket_connections_active`,
`IMP-M3-09`/`IMP-M2-10`/`IMP-M3-08` wire
`GameSessionFailureRate`/`ReconciliationRepairsPersist`/`TeardownOwed`, and any item adding a new
Redis usage site tags it per `conventions.md` §7. None of these block anything — they surface when
that item's own Done-when is checked.

**IMP-GATE-17** (`IMP-M0-09`, opened and closed 2026-09-05) — `turnbase.gamehost.grpc.port`, shipped
in `IMP-M0-04` and already read live by `GrpcServerLifecycle`, was never added to
`local-environment.md` §7.8, contradicting §7's own "whole tunable surface" claim — the same class
of gap IR-24 closed for `turnbase.room.spectator-capacity`. Fixed: added to §7.8 with its existing
default (`9090`).

**IMP-GATE-18** (`IMP-M0-10`, opened and closed 2026-09-05) — the Done-when clause required proving
trace propagation "across the REST → gRPC boundary," but no such boundary exists yet: `platform`
issues no outbound gRPC call and runs no gRPC server, and the Game Host's one outbound call
(`Register`) isn't triggered by an inbound REST request — that request chain doesn't exist before
`IMP-M3-05`. Fixed: narrowed to proving the interceptor mechanism against a controlled gRPC call, with
the live cross-repo check moved to `IMP-M3-05`. `IMP-M0-10`'s *Satisfies* was also narrowed to what it
actually builds — `FR-MET-002`, `FR-MET-005`, `FR-ALERT-003/006/007` and the Game Host's own
`platform-architecture.md` `FR-OBS-*` are deferred to `IMP-M2-02`, a new `conventions.md` §7 rule, and
`IMP-M3-09`/`IMP-M2-10`/`IMP-M3-08` respectively, each of which now carries the corresponding clause.

**IMP-GATE-19** (`IMP-M0-10`, opened and closed 2026-09-05) — `observability.md` §3's own worked
example showed `"sessionId": null` beside prose stating correlation IDs are "omitted when absent
rather than written as empty strings." Fixed: the example now omits the key.

**IMP-GATE-20** (`IMP-M0-10`, opened and closed 2026-09-05) — `observability.md` §2.1's SQL for
`turnbase_friend_requests_pending` filtered on a `status` column `friend_request` does not have
(`IMP-M0-06`'s baseline). Fixed: an unfiltered `count(*)` — a pending request's row existing is what
"pending" means in this schema; accepting or declining one deletes the row.

**IMP-GATE-21** (`IMP-M0-10`, opened and closed 2026-09-05) — found by actually running the stack:
`observability.md`'s JSON log example and Grafana derived-field regex used camelCase
`traceId`/`spanId`, but the OpenTelemetry Java agent's `logback-mdc` instrumentation — the mechanism
the doc itself credits — writes `trace_id`/`span_id` (OTel semantic conventions, not configurable).
Fixed: doc, `promtail-config.yaml` and `datasources.yaml` all changed to `trace_id`/`span_id`.

**IMP-GATE-22** (`IMP-M0-10`, opened and closed 2026-09-05) — also found by running the stack:
`tempo.yaml` (`IMP-M0-08`) left the OTLP receivers on Tempo's default loopback bind, so every span
export failed with `Connection refused` and zero traces ever reached Tempo — same bind-address trap
class as `IMP-GATE-14`. Fixed: explicit `endpoint: 0.0.0.0:4317`/`:4318`.

**IMP-GATE-16** (`IMP-M0-09`, opened and closed 2026-09-05) — `secrets-and-configuration.md`'s
`local`/`test,e2e`/`Kubernetes` split for the JWT key set cannot be implemented by Spring profile
alone: `local-environment.md` §4 runs the canonical Kubernetes chart under the identical
`spring.profiles.active=local` compose uses, but the two rows need opposite behaviour — generate and
persist to a file under compose (one instance), fail if absent under Kubernetes (the chart's own HPA
can run more than one replica). Fixed: a new non-secret switch, `turnbase.auth.jwt-key-set-required`
(`local-environment.md` §7.4, default `false`), set to `true` only by the Helm chart's ConfigMap;
`secrets-and-configuration.md` §3.1 now states this is the actual mechanism and profile is not.

**IMP-GATE-15** (`IMP-M0-09`, opened and closed 2026-09-05) — the *Done when* clause requires a
Kubernetes Secret path for every secret, including the JWT key set, but
`secrets-and-configuration.md` §3.1 named none: it said only "Supplied; startup fails if absent," and
§7 deliberately excludes secrets by design, so there was nowhere else it could be named either.
Fixed: §3.1 now names `TURNBASE_JWT_KEY_SET` (`turnbase.auth.jwt-key-set`), one JSON-valued
environment variable carrying the whole key set in §3.2's own shape.

**IMP-GATE-14** (`IMP-M0-07`, opened and closed 2026-09-05) — `local-environment.md` §1 said
compose achieves the loopback-only management port by setting `management.server.address =
127.0.0.1` *inside* the container, with the published port doing the rest — but a Docker published
port always forwards to the container's bridge interface, never its loopback, so a listener bound
that way is unreachable through its own published port regardless of the host-side bind. Proven
live: the container refused every host connection with the address set, and answered normally with
it unset. `IMP-M0-03`/`IMP-M0-04`'s "verified live" claims never exercised a real Docker
port-publish round trip. Fixed: §1 and §7.9 now say the app listens on all interfaces in both
profiles; compose's restriction is the published port's own host-side bind. No application code
changed (`MANAGEMENT_SERVER_ADDRESS` already defaults to unset); only stale comments and
`docker-compose.yml` were corrected.

**IMP-GATE-13** (`IMP-M0-07`, opened and closed 2026-09-05) — ADR-0011 §6 requires the Postgres
init script to create `pg_trgm` and `btree_gin` as superuser (the baseline migration's own
`CREATE EXTENSION IF NOT EXISTS` for both then succeeds as a no-op), but
`secrets-and-configuration.md` §4's actual `01-roles.sql` content created only `pgcrypto`. Running
the real compose stack — the first thing to migrate as the actual unprivileged `turnbase_app` role
rather than a Testcontainers superuser — failed outright with `permission denied to create
extension "pg_trgm"`. Fixed: §4's script (and `deploy/compose/initdb/01-roles.sql`) now creates all
three extensions; the baseline migration file needed no change, verified.

**IMP-GATE-12** (`IMP-M0-07`/`IMP-M0-08`, opened and closed 2026-09-05) — both items' `Repo` field
said "this repo" (the root `turnbase` landing repo), but `local-environment.md` §4 roots the whole
deploy tree — compose files, Helm chart — at `turnbase-platform/deploy/…`, and ADR-0012 describes
`turnbase` itself as holding only docs, specs and submodule refs, no deploy artifacts. Fixed: both
items' `Repo` corrected to `turnbase-platform`, matching the spec and the ADR.

**IMP-GATE-11** (`IMP-M0-06`, opened and closed 2026-09-05) — `schema-migrations.md` §5 names
`shedlock` as a baseline table but no document supplied its columns. Fixed: §5 now states the DDL,
which is ShedLock's own fixed schema, not a TurnBase design choice.

**IMP-GATE-10** (`IMP-M0-06`, opened and closed 2026-09-05) — the *Done when* clause named the
baseline file `V1__baseline.sql`, contradicting ADR-0011 §5 and `schema-migrations.md` §§1–2, which
mandate timestamp-based naming and both already name the real file `V202608091200__baseline.sql`.
Fixed: the registry entry (the one document that had it wrong) now names
`V202608091200__baseline.sql` throughout.

**IMP-GATE-09** (`IMP-M0-04`, opened and closed 2026-09-04) — no document names the address the Game
Host dials to reach the Platform Monolith's `GameHostRegistryService`, which `local-environment.md`
§2 places on the monolith's `8080` HTTP listener rather than a dedicated port. Fixed: §7.8 gained
`turnbase.gamehost.orchestration-address` (default `platform:8080`).

**IMP-GATE-08** (`IMP-M0-04`, opened and closed 2026-09-04) — the *Done when* clause required "the
process registers with the Platform Monolith per §3's 60-second budget," but the platform's server
side of `GameHostRegistryService` is not implemented until `IMP-M3-05` (depends on `IMP-M3-04`,
`IMP-M2-04`), far downstream of `IMP-M0-04` (depends only on `IMP-M0-01`). Same shape as
`IMP-GATE-03`. Fixed: `IMP-M0-04`'s clause narrowed to a `Register` client call proven against an
in-process stub registry service; the real cross-repo, 60-second-budget check is now `IMP-M3-05`'s own
*Done when* clause.

**IMP-GATE-07** (`IMP-M0-03`, opened and closed 2026-09-02, `DONE` 2026-09-04) — `IMP-M0-03`/`M0-04`'s
*Done when* required the `turnbase-grpc` client/server stubs to resolve "at the exact pinned
`<turnbase-common.version>`" against `conventions.md` §5's absolute "no `-SNAPSHOT` in a committed
pom" — but `turnbase-common` has never been tagged (a human action) and the publish workflow that
would produce a release is `IMP-M0-11`, which depends on `M0-03`/`M0-04`. Unsatisfiable as written.
Fixed: `conventions.md` §5 gained a bootstrap exception — pin the current development version,
resolved from the local install, until the first tag exists; `IMP-M0-11` owns both standing up the
publish workflow and the follow-up PRs that bump consumers to the real release once it's tagged. The
fix's first draft still missed how CI itself gets that install — see the session 16 summary above for
the private-repo credential problem that turned up executing it.

**IMP-GATE-06** (`IMP-M0-03`, opened and closed 2026-09-02) — `platform-operations.md` CON-010 still
said integration tests use Docker Compose, contradicting FR-CICD-004 in the same document (corrected
2026-08-20 to Testcontainers-only) and the same rule restated in `conventions.md` §3. Simply missed
when FR-CICD-004 was fixed. Fixed `platform-operations.md` CON-010 to state the Testcontainers/compose
split correctly.

Seven gates have now been opened *and closed* across the first three items — three on `IMP-M0-01`,
two on `IMP-M0-02`, two on `IMP-M0-03` — which is the number worth planning around: **a skeleton item
costs roughly one spec defect per document in its read-list.** Budget for that rather than treating a
gate as a delay.

**IMP-GATE-05** (`IMP-M0-02`, closed 2026-08-22) — `game-development-experience.md`
FR-FEGDK-001…009 (the `TurnBaseClient` class itself) was claimed only by `IMP-M6-05`, which
implements the platform shell's half of the postMessage boundary, not the client — no item in
`turnbase-sdk`, the repo that publishes `@turnbase/gdk`, owned it. Fixed by adding
**`IMP-M3-12` — FE GDK client**, depends on `IMP-M0-02`, and correcting `IMP-M6-05`'s *Satisfies*.

**IMP-GATE-04** (`IMP-M0-02`, closed 2026-08-22) — the read-list named `backend-gdk-api.md` §1–3
and claimed `FR-GDK-001`, but §3's `TurnBaseGame` cannot compile without all of §§3–8 — verbatim
`IMP-M3-01`'s own *Done when*. Fixed by narrowing `IMP-M0-02` to the build-and-publish floor; the
Java type surface stays `IMP-M3-01`'s.

**IMP-GATE-03** — the clause "resolves from both `turnbase-platform` and `turnbase-game-host`"
required the item's own dependents to exist first (`IMP-M0-04` depends on `IMP-M0-01`). The half that
is checkable at the source — install, then compile and run a consumer against the client stub *and*
the server base class — stayed; the cross-repo half moved onto `IMP-M0-03` and `IMP-M0-04`, which
have a consumer to check it with.

**IMP-GATE-02** — ADR-0012 said `turnbase-common` copies `gamehost.proto` into `src/main/proto/` *at
build time*, and also said each component repo is *independently usable without the root*. Two
sections apart, and they cannot both hold: a Maven step reading `../docs/` fails in a standalone
clone, which is exactly what that repo's CI checks out. ADR-0012 is amended — the copy is a
**committed file**, and the drift guard is `scripts/sync-proto.sh --check` in the parent's `pre-push`
hook, because drift here is silent (both repos compile; the two services disagree on the wire).

**IMP-GATE-01** — `gamehost.proto` declared `java_package = "com.turnbase.gamehost.grpc.v1"` against the
`io.turnbase.grpc` root that `conventions.md` §1 and ADR-0014 §1 both give `turnbase-common`. The
proto now declares `io.turnbase.grpc.gamehost.v1`, and `conventions.md` §5 states the rule — package
tail and canonical buf-module path — so the next generated artifact does not re-decide it.

**None of the three was findable by reading**, and none would have been caught by
`check-corpus.py`. They surfaced only because something finally had to compile against the documents.
That is the argument for doing the skeletons before anything subtle depends on them.

**[`docs/implementation/conventions.md`](docs/implementation/conventions.md) applies to every item and
is not repeated in read-lists** — package layout, static analysis, Spotless, test suffixes, JaCoCo,
branch and commit format, cross-repo version pinning. Assume it the way you assume `CLAUDE.md`.

**The harness is done.** Submodule `CLAUDE.md` files, the corpus checker, the status protocol, the
escalation format, the two skills and the permissions all landed in session 13, and sessions 14 and
15 proved them on real items: the `work-item` cadence held both times, `spec-defect` fired three
times on `IMP-M0-01` and twice on `IMP-M0-02`, and the `pre-push` hooks now run in two repositories.

### `turnbase-sdk` is a second worked example, narrower than `turnbase-common`

It adds two things `turnbase-common`'s pom didn't need: **Checkstyle** (bound at `validate`
alongside Spotless, public-type Javadoc only — the one repository that runs it) and an enforcer
**`bannedDependencies`** rule (`turnbase-grpc`/`turnbase-game-host` banned at every scope). Both are
mechanical answers to `turnbase-sdk/CLAUDE.md`'s two repo-specific rules, and both were verified to
actually fire against a deliberate violation before being trusted.

**`typescript` is pinned to `6.0.3`, not the latest `7.0.2`** — `typescript-eslint@8.67.0`'s peer
range is `<6.1.0`; `npm install` fails `ERESOLVE` otherwise. Not in `conventions.md` because it is a
toolchain fact rather than a project decision, but worth knowing before `IMP-M0-05`
(`turnbase-frontend`) or `IMP-M3-12` pin `typescript` again.

### The next session — `M0-04` is done; `M0-05`, `M0-06`, and `IMP-M3-12` are on the board

**`IMP-M0-04` is `DONE`.** `turnbase-common`, `turnbase-platform` and `turnbase-game-host` are now
three worked examples of the bootstrap-window mechanics (Spotless at `validate`, Error Prone +
NullAway, merged JaCoCo, the enforcer, the `.mvn/jvm.config` flags, and the `TURNBASE_COMMON_PAT`
bootstrap install — one secret per bootstrap-window consumer repo, never shared). `IMP-M0-05`
(frontend skeleton) has no such dependency and is a clean start by comparison.

Things `IMP-M0-01`/`M0-03` learned that `IMP-M0-04` met on its own first push too, all in
`conventions.md` §6:

| | |
|---|---|
| GraalVM CE | `graalvm/setup-graalvm`, **not** `actions/setup-java`, which has no `graalvm-community` distribution |
| `buf breaking` | pull requests only, against the base branch — a push has no reliable baseline |
| Dependabot | opens PRs within a minute of the first push; land `ignore` entries **with** a deliberate pin, and expect every PR to fail CI on the bootstrap secret regardless of content until `IMP-M0-11` |
| Line endings | `.gitattributes` pins `*.sh`, hooks and `mvnw` to LF, or a CRLF checkout makes git silently refuse to run a hook |
| Dependabot `ignore` dependency-name | **verify the entry actually matches** — a docker `dependency-name` never includes the registry host (`ghcr.io/…` doesn't match; the bare image name does), found the hard way by `IMP-M0-04`'s own first `dependabot.yml` |

**A dependency pinned as "the exact build a spike verified" (Espresso here; Astryx for `IMP-M0-05`)
needs an `ignore` entry with no version floor at all**, not a `>=<major>` range — a patch bump is still
a different build than the one that was verified, and only a version-range-shaped rule looks like it
covers that until the first Dependabot PR proves otherwise.

**`IMP-M3-12` (FE GDK client, `turnbase-sdk`) is now `READY`**, unblocked by `IMP-M0-02`. It's a
candidate for the same session as `M0-05`/`M0-06` if there's room: `frontend-gdk-api.md` is already
read in full for `IMP-M0-02`, and the declared types it needs (`Role`, `Player`, `Team`,
`InitContext`, the envelope) already exist in `src/main/ts/types.ts`.

**`IMP-M0-05` installs and wires Astryx** (exact pins, three CSS imports in cascade-layer order,
`<Theme>` + `<LinkProvider>`, `data-astryx-theme`, self-hosted Figtree) — a skeleton without them
renders almost-right screens that get corrected one at a time later. Its lint stack is pinned in
`conventions.md` §2, not left to `npm create vite`.

**Then, still in setup:** `IMP-M0-11` wires the CI workflows — every trigger on `master`,
Testcontainers with no compose in the PR job, and FR-CICD-010's Dependabot and Trivy as committed
configuration rather than a mention.

### Then the substantive M0 items

1. **IMP-M0-06 — the Flyway baseline.** The highest-value item in the registry. Transcribing
   `V1__baseline.sql` from the six schema documents is the first mechanical test of whether they are
   mutually consistent. The two hazards the audit named are now **fixed in the documents**:
   `data-model.md` states one auto-increment idiom (`bigint GENERATED ALWAYS AS IDENTITY`), and
   `schema-migrations.md` §5 names one circular foreign key rather than two. **Any further
   disagreement found while transcribing is a
   specification defect — fix the document, then the SQL.** Do not reconcile silently in the
   migration.

   Two schema changes from this session must land in the baseline:
   `room_participant_unannounced_idx` (IR-09) and nothing else — IR-11 deliberately added no table.

2. **IMP-M0-07 — the compose stack.** IR-01 and IR-02 are closed, so this is now buildable end to
   end: the `minio-init` container, `deploy/compose/initdb/01-roles.sql`, and `POSTGRES_USER` set to
   `turnbase_owner`. Getting the last one wrong is the silent FR-CRED-005 violation.

### Then, in dependency order

M1 accounts → M2 rooms (the longest milestone, and now fully specified) → M3 execution → M4 catalog →
M5 history → M6 frontend. The registry has the per-item ordering.

Three things worth knowing before the milestone that needs them:

- **M2's specifications are clean but subtle.** The ownership and versioning core was confirmed
  correct by the audit; the blockers clustered in the edges — expiry, closure, chat, sweeps — and all
  of those are now fixed. Read ADR-0008/0009/0010 before touching `room-lifecycle.md`'s mechanisms,
  and remember that **the epoch is the fence token, not the version**.
- **M3's trust boundary now requires an address check** (IR-17) that did not exist when the registry
  was written: every effect address is validated against the producing session's membership at
  fan-out.
- **M6's component library is Astryx, not ours** ([ADR-0013](docs/decisions/0013-astryx-design-system.md)).
  Read that ADR before anything else in M6. `IMP-M6-01` is an integration item — install is already
  done by `IMP-M0-05`, so what remains is the `ui/` boundary and the compose→swizzle→write ladder.
  **Component lookup is a tool call** (`npm run astryx -- component <Name>` or the `astryx` MCP
  server); nothing in this corpus lists them.

- **Every trigger, tag rule and branch protection names `master`**, in every repo. FR-CICD-002/006/007
  said `main` until session 13 and were corrected; a workflow written from the old text never fires.
- **Integration tests are Testcontainers, never compose** (`local-environment.md` §8). Compose belongs
  to the post-merge e2e job alone. The PR job needs a Docker daemon and nothing else.

### Spec hygiene

- **The ID-qualification retrofit** remains outstanding. `docs/specs/INDEX.md` states the rule and it
  holds for new text; the corpus predates it. The highest-traffic collision is `FR-SESS-001…004`,
  defined in both `user-accounts.md` (account sessions) and `platform-architecture.md` (Game Host
  in-memory state); all seven citations resolve correctly by context, so this is a hazard rather than
  a defect. A **wrong** qualifier is worse than a bare ID.
- The `FR-JOB-007a…e` sub-duty convention is declared in `docs/specs/INDEX.md`, and
  `data-model-accounts.md:392`'s wrong FR-INV-002 citation is corrected (session 11).
- **`docs/requirements/INDEX.md` now exists** (IR-25 closed) and carries the twelve genuinely
  colliding prefixes. Use it to resolve a qualifier before writing one — the qualifier names the
  document that **defines** the requirement, never one that merely cites it.
- **`turnbase.room.spectator-capacity`** (IR-24 closed) is in `local-environment.md` §7.1, whose
  title is now *Room lifecycle, capacity and deadlines*. §7 is again true when it claims to hold every
  tunable in the corpus — keep it that way: a property named at a call site and never registered there
  is invisible to the next configuration audit.
- The ten non-blocking findings worth acting on were harvested into the corpus in Part 5 and the
  slice files deleted; the review INDEX records each with where its fix landed. The remaining ~52 were
  NITs and low-value GAPs, and re-deriving one from a fresh audit is cheaper than carrying 3 184 lines
  of stale report against the chance that one mattered.

### Review action plan

`docs/reviews/2026-07-02-mvp-readiness/INDEX.md` — fully worked, **closed**.

`docs/reviews/2026-08-16-implementation-readiness/INDEX.md` — **closed.** 23 of 23 blockers resolved;
each entry carries a `**Closed:**` line. The two follow-on findings raised during remediation (IR-24,
IR-25) are closed too.

**2026-08-20 readiness review (session 13)** — no review directory: seven defects, all closed in the
same session, and the record is this file plus ADR-0014, ADR-0015 and `conventions.md`. A round that
opens and closes together does not need an INDEX to track it, and a working file describing it would
be spent on arrival.

**Nothing is open in the corpus, and nothing is open in the harness.** The next work is `IMP-M0-01`.

Two things are deferred rather than done, both deliberately:

- **The three proposed agents** (`impl-agent`, `done-when-verifier`, `spec-auditor`) wait until M0
  shows where the cadence actually hurts. Guessing their shape now costs more than waiting.
**`work-item` and `spec-defect` have now had their first real outing** and both held on `IMP-M0-01`.
`spec-defect` fired three times on one item; `work-item`'s "a green local build is not `DONE`" rule
is what kept the item at `WIP` until CI actually ran — and CI then failed in both jobs, which is the
best possible argument for the rule. Neither skill needed an edit. The one thing to watch on the next
item is whether three gates in one item makes the escalation feel routine enough to start skipping.

**Permissions are settled.** The Astryx and Playwright prefixes were corrected in session 13, and
session 14 added `git push` **without any force variant** — `--force`, `--force-with-lease`,
`--mirror`, `--delete`, `--prune`, `--tags` and `+refspec` stay denied, and a `v*.*.*` tag push stays
a human action because ADR-0012 makes it the release trigger.

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

**Specs:** `docs/specs/` — **flows** (new: eight end-to-end journeys — start here), **deployment**
(new: local environment and the configuration surface, schema migrations, secrets and key rotation),
**platform-frontend** (new: the React shell and the iframe trust boundary), platform (room lifecycle
plus the **complete relational data model** across six documents), api-design, internal-grpc,
game-host, game-frontend, gdk-api (now including the **test harness**), manifest (now including the
**bundle format and upload pipeline**).

**Decisions:** `docs/decisions/` — ADR-0001 (local-first platform), ADR-0002 (WS room affinity),
ADR-0003 (availability), ADR-0004 (erasure pseudonymization), ADR-0005 (sandbox / Espresso spike),
ADR-0006 (game trust model — official-only Java for MVP), ADR-0007 (game FEs on a separate
registrable domain), ADR-0008 (room ownership as a lease-gated claim), ADR-0009 (grace deadlines
persisted and swept), ADR-0010 (session teardown as a durable to-do), ADR-0011 (schema migrations —
Flyway, forward-only, backward-compatible), ADR-0012 (polyrepo under an organisation, with
submodules), ADR-0013 (Astryx supersedes the in-house design system), **ADR-0014 (modular monolith,
enforced by Spring Modulith)**, **ADR-0015 (static analysis — Error Prone and NullAway, at skeleton
time)**.

**Implementation:** `docs/implementation/` — the registry Phase 1 executes from. **61 live work items
across 7 milestones** (IMP-M6-07 cancelled; `IMP-M3-12` added session 15; `IMP-M1-10` added session 29),
each carrying a
read-list, dependencies, the requirement IDs it satisfies and a done-when clause. Nothing is gated.
Plus **`conventions.md`** (new, session 13): the code and build conventions every item assumes —
package layout, Spotless, tests and coverage, git, cross-repo dependencies, and the per-repo build
floor.

**Reviews:** `docs/reviews/` — two closed rounds, reduced to their INDEXes plus
`espresso-spike-results.md`. `2026-08-16-implementation-readiness/INDEX.md` carries all 23 blockers
with evidence and a `Closed:` line each, the ten harvested non-blocking findings, and IR-24/IR-25.
Working files (slice reports, inventories, the remediation plan) were deleted once spent — they had
become pre-remediation snapshots of a corpus that no longer matched them.

**Coverage caveat — now largely closed.** Of the four areas that had requirements but no implementing
specification, three were written this session: the design system
(`platform-frontend/design-system.md`), the room REST API (`api-design/room-rest-api.md`) and
observability (`deployment/observability.md`). The fourth, the onboarding wizard, was **cut from v1**
rather than specified. The table above lists requirement coverage, not design coverage.

---

## Open Questions Remaining in Existing Docs

| Document | Open Question |
|----------|---------------|
| `reconnection-flow.md` | Game engine response set after "player lost" event — deferred to Game SDK contracts |
| `game-history.md` | OQ-002: Pagination reuse — shared UI component vs. API pattern deferred to implementation |
| `game-contracts.md` | OQ-001: Log color annotation syntax — deferred to GDK spec |
| `game-contracts.md` | OQ-002: AI/bot player interface — deferred to future spec. **Mislabelled: this now blocks M2 (IR-12).** `ROOM_STATE` carries AI participants on the wire and the room-closure predicate turns on "not an AI", but `room_participant` has no discriminator — so the closure predicate cannot be written. Either add the column or remove AI from the protocol for the MVP |
| `game-contracts.md` | OQ-003: Platform-managed timer system — deferred to future spec |
| `websocket.md` | OQ-001: Resync cost under a *legitimate* mass reconnect (N resyncs serialize behind one session lock) — cache the per-viewer view against `lastAppliedSequence` if it becomes a hotspot. The adversarial case is now closed by the Tier 6 `snapshot` bucket |
| `websocket.md` | OQ-002: A game whose `onResync` returns an empty spectator view leaves spectators blank until the next `broadcast` — the test harness should warn |
| `admin-tooling.md` | OQ-001: Can a developer resubmit a rejected game, or is rejection terminal? |
| `admin-tooling.md` | OQ-002: Can an operator delist a Verified or Official game post-approval? |
| `game-asset-serving.md` | OQ-001: Fullscreen — `allow=""` grants no Permissions-Policy features; whether to add `allow="fullscreen"` is a shell-spec UX call |
| `game-asset-serving.md` | OQ-002: Private-bundle exposure — bundle assets are unauthenticated; a signed-token variant is additive if genuinely private third-party bundles become a requirement post-MVP |
| `game-asset-serving.md` | OQ-003: Manifest-declared stylesheets — CSS must currently be imported from JS; deferred to the bundle spec |
| `rate-limiting.md` | OQ-001: Shared-IP (CGNAT/campus NAT) guest throttling — accepted for a local-first MVP; escalation path is raise limit → add entropy to the key → proof-of-work |
| `rate-limiting.md` | OQ-002: Tier 6 budgets are per-pod, so a user connected to two pods gets 2× — accepted (these are abuse controls, not fairness quotas); revisit only if concurrent multi-room membership lands |
| `input-validation.md` | OQ-001: No emoji or symbols in usernames — the clean fix, if users push back, is a separate free-form display name alongside a strict username (post-MVP model change) |
| `input-validation.md` | OQ-002: ASCII-only email rejects IDN/EAI addresses — revisit if a real user is blocked; there is no mail system in the MVP to normalize against (no verification email is sent) |
| `room-lifecycle.md` | OQ-001: Lease/window numbers (10s TTL, 3s renew, 6s self-evict, 20s migration window, 5s/60s sweeps) are reasoned defaults with no measurement behind them; the relationships that must hold matter more than the values |
| `room-lifecycle.md` | OQ-002: Self-eviction uses a local monotonic clock while the lease expires in Redis — the 4s guard band covers single-node skew, but this is the one place a local clock still affects a correctness bound; re-examine before multi-node |
| `room-lifecycle.md` | OQ-003: Flapping clients — each disconnect starts a fresh window, so a connect/disconnect loop can hold a slot indefinitely; the Tier 6 reconnect lockout dampens it, but whether a hard cap per session is needed is deferred until observed |
| `data-model-catalog.md` | OQ-001: A rejected re-review leaves a community game with an `ACTIVE` version an operator refused, its previously approved version `SUPERSEDED` and unreactivatable, and no rollback in the status machine. §5.1 preserves the artifact; nothing says how to recover the state. Dormant under ADR-0006 |
| `data-model-catalog.md` | OQ-002: `game_review.decided_by` identifies a shared static credential, not a person (`admin-tooling.md` CON-002) — adequate for one operator, not as an audit trail beyond that |
| `data-model-catalog.md` | OQ-003: FR-REV-001's pending-review state has no owner-facing representation, so a second submission fails as a raw unique violation rather than a domain error |
| `local-environment.md` | OQ-001: The startup budget (≤30s to readiness, ≤60s to Game Host registration) is a target, not a measurement, and FR-JOB-008's 120-second suppression window depends on it |
| `local-environment.md` | OQ-002: **No backup, restore or disaster-recovery story for the local Postgres volume.** Undecided rather than decided; the first genuinely valuable data the platform holds is game history, retained indefinitely by FR-RET-003 and protected by nothing |
| `bundle-format.md` | OQ-1…5: publication deny list vs. a manifest `frontend.root` allow list (ties to `game-asset-serving.md` OQ-003); no integrity digest on published objects; the harness cannot check `gdkApiVersion` offline; NFR-UPLOAD-001's 30s validation budget is unmeasured; a version orphaned by a GDK-range move has no user-facing representation |
