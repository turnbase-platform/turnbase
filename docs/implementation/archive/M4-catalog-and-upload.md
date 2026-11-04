# Archive — M4 Catalog and upload

Closed milestone, moved out of [`../registry.md`](../registry.md) verbatim by `IMP-M20-01`. Not read by a session unless an item's read-list names it ([`../INDEX.md`](../INDEX.md) *Archive*). `IMP-M4-*` identifiers cited elsewhere resolve here.

## Register rows

| ID | Item | Repo | Depends on | Status |
|---|---|---|---|---|
| IMP-M4-01 | Catalog listing and game detail | platform | M1-01 | DONE |
| IMP-M4-02 | Manifest schema validation | platform | M0-06 | DONE |
| IMP-M4-03 | Upload pipeline and version state machine | platform | M4-02 | DONE |
| IMP-M4-04 | Bundle publication and asset serving | platform | M4-03 | DONE |
| IMP-M4-05 | Admin API — review queue and badges | platform | M4-03 | DONE |

---

## M4 — Catalog and upload

**Read first:** `docs/specs/manifest/bundle-format.md`, `manifest-schema.md`, `manifest.schema.json`,
`docs/specs/platform/data-model-catalog.md`, `docs/specs/api-design/file-uploads.md`,
`docs/specs/game-frontend/game-asset-serving.md`, flow `08`.

### IMP-M4-01 — Catalog listing and game detail

**Repo:** `turnbase-platform` · **Depends on:** IMP-M1-01

**Read first:**
- `docs/requirements/game-catalog.md` FR-CAT-001…010, FR-GDET-001…009
- `docs/specs/platform/data-model-catalog.md` §1 (`game`), §3 (`game_tag`), §4 (`game_review`)
- `docs/requirements/admin-tooling.md` FR-BADGE-001…004, FR-PRV-001 — visibility is an
  admin-tooling rule that this endpoint enforces
- `docs/specs/api-design/pagination-filtering-sorting.md`
- `docs/specs/api-design/input-validation.md` § *Output encoding*
- `docs/specs/api-design/rest-conventions.md`
- `docs/specs/api-design/error-handling.md`
- `docs/specs/platform/data-model.md` §1 (`room`), §2 (`room_participant`) — FR-GDET-005's active
  player count reads these tables directly, `room_open_game_idx`'s documented purpose
- `docs/specs/api-design/catalog-rest-api.md`

**Satisfies:** `game-catalog.md` FR-CAT-001…010, FR-GDET-001…009, NFR-PERF-001…002,
NFR-SCAL-001, NFR-SEC-001…002, NFR-USAB-001…002; `admin-tooling.md` FR-PRV-001; `platform-views.md`
VW-CAT-001…003, VW-GDET-001…003

**Done when:** an Unverified game is absent from the catalog and from search for every caller except
its owner (`admin-tooling.md` FR-PRV-001); each game carries exactly one badge, read from one column
(FR-BADGE-001); descriptions are delivered as **Markdown source** and rendered to React elements
client-side (IMP-M6-06) — the API never returns an HTML string, which is what makes
`input-validation.md`'s `dangerouslySetInnerHTML` ban enforceable rather than aspirational (IR-19).

**Closed:** `IMP-GATE-64` (opened and closed 2026-09-20, session 61) — three defects found claiming
this item. (1) No document defined the `GET /api/games` / `GET /api/games/{gameId}` routes this item's
own *Done when* requires; fixed by adding `docs/specs/api-design/catalog-rest-api.md`, registered in
that directory's `INDEX.md` and in `game-catalog.md`'s *Related API Specifications*. (2)
`pagination-filtering-sorting.md` § *Filtering* § *Implementation* and `api-design/INDEX.md`'s *Key
Decisions* both described a Spring Data JPA Specifications mechanism that exists nowhere in
`turnbase-platform` — every repository (`RoomRepository`, `AdminGameRepository`, etc.) hand-writes SQL
via `JdbcClient`; fixed both documents to describe that mechanism instead. (3) This item's own
*Satisfies* claimed the entirety of `FR-GAME-001…014` and `admin-tooling.md FR-PRV-001…004`, neither
of which its *Done when* clause tests or its two read-only endpoints build — narrowed to what is
actually built (dropped `FR-GAME-001…014` outright; narrowed `FR-PRV-001…004` to `FR-PRV-001`).
`FR-PRV-004` (the game owner's submit-for-review action) remains unclaimed by any item in the
registry — `admin-rest-api.md` §7 already disclaims building it; noted in `STATUS.md` for a future
item rather than solved here. (4) `data-model-catalog.md` §1 asserted a null-owner game "renders the
platform name" as its catalog author without ever naming the literal string — a decision visible in a
response body that no document made; fixed by naming it (`"TurnBase"`) in that section.

---

### IMP-M4-02 — Manifest schema validation

**Repo:** `turnbase-platform` · **Depends on:** IMP-M0-06

**Closed:** IMP-GATE-60 (opened and closed 2026-09-14, session 53) — this item's own read-list calls
`manifest.schema.json` "the executable artifact and the authority," meaning code in this repository
reads it directly, but `turnbase-platform` must build from a standalone clone (no path outside the
repository, same constraint `conventions.md` §5 states for `turnbase-common`) and no document said
how the file gets from the spec tree into this repository's build, where it lives, or whether a
drift guard exists — `manifest-schema.md`'s own "the contract ... so the two cannot drift" language
already names the exact risk `conventions.md` §5 built a full mechanism for on the proto, and never
extended it here. Same shape as `IMP-GATE-31`/`33`/`35`/`37`/`57`/`58`/`59`, at the scale of a build
mechanism rather than a REST surface. Fixed: `conventions.md` §5 gained a paragraph mirroring "The
proto is copied, not shared" — a committed copy at
`turnbase-platform/src/main/resources/manifest/manifest.schema.json`, refreshed and checked by new
`scripts/sync-manifest-schema.sh` (`--check` is a no-op until a copy exists, since none does yet —
wiring the parent's pre-push hook is this item's own job once it creates the first copy, not a
prerequisite to starting it).

**Read first:**
- `docs/specs/manifest/manifest.schema.json` — **the executable artifact and the authority**
- `docs/specs/manifest/manifest-schema.md` — the prose, including the `capabilities` rules
- `docs/specs/manifest/bundle-format.md` §3 (where in the pipeline this runs)
- `docs/requirements/game-development-experience.md` FR-MANIFEST-001…009

**Satisfies:** `game-development-experience.md` FR-MANIFEST-001…009

**Done when:** validation runs against `manifest.schema.json` — the executable artifact — and the
prose documents agree with it. Where they disagree, fix the document. `capabilities.ai: true` is
**rejected** at validation (IR-12): the field survives in the schema for a future release, and a
bundle declaring it today would list a game whose AI seats can never be filled. The schema file is
committed to this repository via `scripts/sync-manifest-schema.sh` (`IMP-GATE-60`,
`conventions.md` §5), and that script's `--check` mode is wired into the parent repo's
`.githooks/pre-push` in the same change that creates the copy.

**Done 2026-09-14 (session 54).** `upload.ManifestValidator` runs `manifest.schema.json` — the
committed copy this item creates at `turnbase-platform/src/main/resources/manifest/`, generated by
`scripts/sync-manifest-schema.sh` — as Layer 1, through `com.networknt:json-schema-validator`
(Draft 2020-12) rather than hand-written per-field checks. Layer 2 covers the cross-field rules the
schema cannot express (`manifest-schema.md` § Validation): team-template and parameter range
ordering, the conditional team-template name, parameter-default membership/bounds per type, and
duplicate parameter keys — plus the IR-12 rejection of `capabilities.ai: true`, reported the same way
(`check: "manifest.capabilities.ai"`). Unknown top-level and nested keys are collected into a
separate `warnings` list rather than failing validation, matching the schema's deliberately lenient
`additionalProperties` stance. `ManifestValidationResult` carries both lists; `errors`/`warnings`
entries are `common.CheckError` (`{check, message}`), the shape `error-handling.md`'s bundle-
validation format already uses. Bundle-, archive- and JAR-level checks (`bundle-format.md` Phases A,
B, C, E, F, G) are `IMP-M4-03`'s concern, not this item's — `ManifestValidator` only ever sees an
already-parsed manifest document.

**Also fixed, found while committing the schema copy:** neither this repository's nor
`turnbase-platform`'s `.gitattributes` pinned `manifest.schema.json` to LF, unlike `gamehost.proto`
— `sync-manifest-schema.sh`'s own header comment claimed the same "pinned to LF on each side"
guarantee `sync-proto.sh`'s does, copied verbatim from it, but the pin itself was never added when
the script was written (`IMP-GATE-60`, session 53). Under this environment's `core.autocrlf=true`,
a fresh clone would have checked the authoritative file out as CRLF while the committed copy in
`turnbase-platform` stayed whatever line ending existed at commit time, and `sync-manifest-schema.sh
--check`'s `--strip-trailing-cr` masks exactly this case locally without fixing it for a real content
diff. Fixed: both `.gitattributes` files gained a `text eol=lf` pin for their respective path,
mirroring `*.proto`'s. Not gated — a missing safeguard the script's own comment already claimed
existed, not a contradiction between two documents — but worth a line here so it is not
rediscovered as a mystery CI flake.

**Verified.** `ManifestValidatorTest` (unit): the spec's own worked example validates clean; each
Layer 2 rule and the `capabilities.ai` rejection independently produce the documented `check` id;
an unrecognized top-level key produces a warning without affecting `valid()`; an empty document
produces the full set of missing-required-field errors. `./mvnw verify` and
`./mvnw verify -Pintegration` green locally. Pushed directly to `turnbase-platform master`
(no PR, ADR-0012) after the `pre-push` hook passed; CI run `34893340481`'s `build` job green
(19m42s — Verify, coverage, both Trivy gates, image push). `e2e` failed on the same
`compose-platform-1`/smoke-test issue flagged as unrelated and non-gating since session 50/51
(`platform-operations.md` OQ-002); this run's failure is on "Run the e2e smoke test," not a new
shape. Submodule ref bumped in this repo.

---

### IMP-M4-03 — Upload pipeline and version state machine

**Repo:** `turnbase-platform` · **Depends on:** IMP-M4-02

**Follow-up (IMP-GATE-69, not a gate):** `StateSerializabilityAnalyzer` hardcodes the Jackson
capability table `bundle-format.md` §4.4 says to read from the shared serialization component, because
that artifact did not exist. Once `io.turnbase:turnbase-serialization` is published
(`game-host-internals.md` §3.6), replace the hardcoded table with its capability descriptor. Nothing
else waits on it.

**Closed:** IMP-GATE-61 (opened and closed 2026-09-19, session 55) — `error-handling.md`'s Bundle
Validation Errors § Synchronous claimed `POST /api/games/{gameId}/versions` is the only endpoint
producing a synchronous `422` in the `{check, message}` shape, and `bundle-format.md` §3.1's phase
table and §3.4's prose grouped Phase B with the asynchronous C-G background job, reporting only via
`validation_errors`/`GET`. Both directly contradict `file-uploads.md`, whose flow narrative (step 3)
and dedicated § Size Validation independently and repeatedly state that stage B1 (the stored-object
size check) fails the `confirm` request itself, synchronously, before `202` is ever returned. Fixed
in `file-uploads.md`'s favor — it is the more specific, operational document for the confirm
endpoint and states the same thing twice: `bundle-format.md` §3.1's table now carries B1 as its own
synchronous row distinct from the C-F background job, §3.2's Phase B heading and §3.4's prose say so
explicitly, and `error-handling.md`'s Synchronous section now names both request paths that can
produce this shape.

**Read first:**
- `docs/specs/manifest/bundle-format.md` **in full** — §3 the pipeline (Phases A–G), §4 the
  serialization round trip, §7 failure/retry/cleanup, §9 the assumptions it makes visible.
  **§3.4 is the authoritative statement of where a failure surfaces.**
- `docs/specs/api-design/file-uploads.md` — the three-step flow and its error cases
- `docs/specs/platform/data-model-catalog.md` §2 (`game_version`) and §7
- `docs/specs/api-design/rate-limiting.md` Tier 3; `error-handling.md` § *Bundle Validation Errors*
- `docs/specs/flows/08-upload-to-play.md`

**Satisfies:** `game-development-experience.md` FR-UPLOAD-001…009, FR-BUNDLE-001…007,
NFR-UPLOAD-001…002, NFR-SIZE-001

**Done when:** every non-terminal status has a documented exit, including `PROCESSING` when the
validating pod dies; a died-mid-validation version number is not permanently burned by the
`(game_id, version)` unique constraint; two open slots cannot walk the active version **backwards**;
activation clears Verified status **only on `VERIFIED → UNVERIFIED`** — an unconditional clear makes
every official upload abort against `game_official_ownerless_ck`, which is the only path the MVP
exercises.

**Failures surface in two different places and the split is not negotiable** (IR-18). Phase A
failures are a **synchronous `422`** on the request itself. Everything from `confirm` onward — Phases
B through G — surfaces as the version resource's `FAILED` state, read via
`GET /api/games/{gameId}/versions/{uploadId}`. A client that waits for a `422` from `confirm` waits
forever.

---

### IMP-M4-04 — Bundle publication and asset serving

**Repo:** `turnbase-platform` · **Depends on:** IMP-M4-03

**Closed:** IMP-GATE-62 (opened and closed 2026-09-19, session 56) — this item's own *Satisfies*
triple-claimed `game-contracts.md` FR-FE-001…006 with `IMP-M3-12` and `IMP-M6-05`, even though
`game-asset-serving.md`'s own Scope section names "the postMessage message catalogue itself" as
explicitly **out of scope** for that document — FR-FE-001…006 is the game-session event catalogue
(`init`, `game_event`, `player_joined`, `player_left`, `game_over`, spectator filtering), which
neither bundle publication nor asset serving ever touches. Separately, this item's own *Done when*
clause tested none of its real `FR-ASSET-001…009` scope: its one clause ("publication filters") was
already fully satisfied by `IMP-M4-03`'s `PublicationService`, which implements §5.2's deny list
verbatim, before this item's own code existed. Underneath that, half of this item's read-list —
`GET /play/{sessionId}` (§5's server-rendered bootstrap document; §4.1's version-pinning row and its
`Host`-vs-session `gameId` cross-check; FR-ASSET-003/007) — has no data to resolve against: no
`sessionId → (gameId, version)` mapping exists anywhere in the schema, because game sessions are
`IMP-M3-05`'s data to create, and `IMP-M3-05` was not this item's dependency
(`room.GameSessionStarter` is still `IMP-M2-06`'s no-op stub, confirmed by reading
`room/PendingGameSessionStarter.java`). Same shape as `IMP-GATE-08`/`18`/`28`/`46`/`53` — an item
whose read-list quietly assumes a caller or a data source that a sibling, unlisted item actually
builds. Fixed: `FR-FE-001…006` dropped from this item's *Satisfies* — unique to `IMP-M3-12`
(the client library) and `IMP-M6-05` (the shell's relay) already, per their own sections. This item
narrowed to exactly what `IMP-M4-03` alone makes buildable: the `Host`-header virtual-routing filter
and `GET /g/{gameId}/{version}/**` static asset serving. `GET /play/{sessionId}` (§4.1 row 1, §5, §7)
moves to `IMP-M3-05` below — the item that already composes and broadcasts `gameFrontendUrl` on
`GAME_STARTED` and is the only item with session data to resolve the route against; `IMP-M3-05` gains
`IMP-M4-04` in *Depends on* (it reuses this item's asset-serving code and deny-listed tree),
`FR-ASSET-003/007/008` in *Satisfies* (008 was already being built there, unclaimed), and a *Done
when* clause. Read-list and Done-when corrected below.

**Read first:**
- `docs/specs/manifest/bundle-format.md` §5 (unpacking and publication)
- `docs/specs/game-frontend/game-asset-serving.md` §3 (origin architecture), §4 (serving — routes,
  the `Host` filter, the unauthenticated-assets deny list), §6.4 (CSP on game responses), §9
  invariants 1, 2, 4 (the ones that do not depend on session data — §9 has only 5 invariants total;
  the prior citation of a 6th was an editing slip, corrected here, session 57)
- `docs/decisions/0007-game-frontend-separate-domain.md`
- `docs/specs/deployment/local-environment.md` §7.7

**Satisfies:** `game-development-experience.md` FR-ASSET-001, FR-ASSET-002, FR-ASSET-005,
FR-ASSET-006, FR-ASSET-009

**Done when:** a request's `Host` header alone decides whether it may reach the platform API, the
platform frontend, or `/g/{gameId}/{version}/**` — never routes from one set to the other regardless
of path (§4, §9 invariant 1). `GET /g/{gameId}/{version}/**` serves only what `IMP-M4-03`'s
publication deny list wrote — unpacking the whole archive would publish the backend JAR to anonymous
callers, since `gameId` is in the hostname and the version is a public catalog column, so the URL is
derivable from a catalog page — with the fixed extension-to-content-type map, `X-Content-Type-Options:
nosniff`, `Cache-Control: public, max-age=31536000, immutable`, and §6.4's CSP on every response; a
missing object 404s. No platform cookie is ever scoped to the games domain, and the games origin never
appears in any CORS/STOMP/server-side trust allowlist (§9 invariant 2).

**A pre-signed URL is a bearer credential.** Every log line that carries one is truncated at the
query string (FR-OBS-005).

---

### IMP-M4-05 — Admin API, review queue and badges

**Repo:** `turnbase-platform` · **Depends on:** IMP-M4-03

**Closed:** `IMP-GATE-63` (opened and closed 2026-09-19, session 58) — this item's own claimed
`admin-tooling.md` FR-OFF-001 ("admin can upload a game directly as an Official title") turned out to
be unbuildable: no document anywhere defines how a `game` row is created at all — `file-uploads.md`
step 1 assumes `gameId` already names one, and `game-catalog.md` FR-GAME-001 defers the mechanism to
a document that itself defers it onward again. This item's read-list also never named
`file-uploads.md`/`bundle-format.md`, whose Phase A–G pipeline the fix has to reuse, and its own
*Satisfies* duplicated `FR-PRV-001…004` with `IMP-M4-01`, which already claims and actually implements
them (catalog visibility, room-creation preconditions) — neither is admin-API work. Fixed: new
`docs/specs/api-design/admin-rest-api.md` — `POST /admin/games` (the missing game-row creation, scoped
to the one path the MVP needs: admin's own official upload) plus an admin-scoped mirror of
`file-uploads.md`'s three routes, the review-queue endpoints (list/detail/approve/reject), and the
`bundle-format.md` stage E4 resolution (the "arrived on the admin path" half `IMP-M4-03`'s session
note left open is decided by which listener served the request — there is no other signal available).
`rest-conventions.md` § *Base Path* now carves out the admin listener's `/admin/` namespace;
`admin-tooling.md` gained a *Related API Specifications* section. `FR-PRV-001…004` dropped from this
item's *Satisfies* (see below). `python3 scripts/check-corpus.py` clean.

**Read first:**
- `docs/requirements/admin-tooling.md` **in full**
- `docs/specs/api-design/admin-rest-api.md` **in full** — the endpoint shapes, request/response
  bodies and status codes this item builds to
- `docs/specs/api-design/file-uploads.md`, `docs/specs/manifest/bundle-format.md` §3.2 (Phases A-G,
  stage E4) — the pipeline `admin-rest-api.md` §4 reuses verbatim; read `upload.VersionUploadController`/
  `Service`/`PublicationService` directly, don't re-derive them
- `docs/specs/platform/data-model-catalog.md` §1, §2, §4
- `docs/specs/api-design/rest-conventions.md` § *Actuator and the Management Port*, § *Base Path*
- `docs/specs/deployment/local-environment.md` §1 host port map

**Satisfies:** `admin-tooling.md` FR-ADM-001…003, FR-REV-001…006, FR-BADGE-001…004, FR-OFF-001…002,
NFR-AUD-001, NFR-CRED-001, NFR-SEC-001

**`FR-PRV-001…004` removed from *Satisfies*** — `IMP-M4-01` already claims them and its own Done-when
is where they are actually checked (catalog-query invisibility, room-creation preconditions); nothing
in this item's own Done-when below ever exercised them, so the duplicate was a bookkeeping error, not
a second implementation.

**Done when:** the admin API is served on the **management port, the same listener as actuator**, and
is loopback-bound under compose and unrouted under Kubernetes (FR-ADM-001, `admin-tooling.md`
CON-001, `local-environment.md` §1); HTTP Basic with credentials from configuration (FR-ADM-002);
**no browser panel exists** (FR-ADM-003); `POST /admin/games` creates the game row and `POST
/admin/games/{gameId}/versions`/`.../confirm` complete an official upload to `ACTIVE` with no review
row ever created (FR-OFF-001…002, `admin-rest-api.md` §3-§4); approval sets Verified and publishes,
rejection stores a plain-text reason and does **not** delete the game or transfer ownership
(FR-REV-004…006, `admin-rest-api.md` §5); every mutating admin action writes an audit record
(NFR-AUD-001).

---
