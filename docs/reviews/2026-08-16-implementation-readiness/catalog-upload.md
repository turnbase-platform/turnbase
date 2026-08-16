# Catalog, upload pipeline, bundle format & asset serving — implementation-readiness audit

**Agent:** Sonnet 5 · **Files reviewed:** 16 in full (see Coverage) · **Date:** 2026-08-16

## Coverage

Read in full: `docs/specs/manifest/bundle-format.md` (963 lines), `docs/specs/manifest/manifest-schema.md`,
`docs/specs/manifest/manifest.schema.json`, `docs/specs/platform/data-model-catalog.md` (658 lines),
`docs/specs/api-design/file-uploads.md`, `docs/specs/api-design/error-handling.md`,
`docs/specs/api-design/rate-limiting.md`, `docs/specs/game-frontend/game-asset-serving.md`,
`docs/requirements/game-catalog.md`, `docs/requirements/game-development-experience.md` (relevant FR-UPLOAD/FR-HARNESS/NFR sections),
`docs/requirements/admin-tooling.md`, `docs/decisions/0006-game-trust-model-java-official-only.md`,
`docs/specs/flows/08-upload-to-play.md`, `docs/specs/manifest/INDEX.md`, `docs/specs/game-frontend/INDEX.md`,
`docs/specs/platform-frontend/INDEX.md`, `docs/specs/api-design/pagination-filtering-sorting.md`,
`docs/specs/api-design/input-validation.md` (output-encoding / Markdown section), `docs/specs/deployment/local-environment.md`
(§6 seed data, §7 config surface), `docs/specs/platform/data-model-catalog.md` §§1–8 in full.

Sampled / cross-checked by targeted grep rather than full read: `docs/requirements/platform-operations.md` (FR-JOB-004/005/010/011/012 rows),
`docs/specs/gdk-api/backend-gdk-api.md` §5.1 (state-serializability rules), `docs/specs/deployment/schema-migrations.md` (ShedLock reference only).

**Not checked, and why:** `docs/decisions/0007-game-frontend-separate-domain.md` was not opened — game-asset-serving.md
explicitly states it realizes that ADR and I found no discrepancy between the spec and what the ADR would be expected to say;
treat anything ADR-0007-specific as **UNVERIFIED**. `docs/requirements/platform-ui-library.md` and `docs/requirements/platform-views.md`
were not opened in full — only grepped for specific IDs — on the judgment that catalog/detail/profile page requirements
(FR-CAT-003/009, FR-GDET-*, FR-UPROF-*) are self-contained enough in `game-catalog.md`'s own text that a missing "how" spec for pure
page layout is not, by itself, a blocker (see assessment below). If the team lead wants pixel-level layout ambiguity checked, that's
a platform-frontend slice concern, not confirmed clean by me. `docs/specs/game-host/game-host-internals.md` was not opened — cited
by bundle-format.md for the JAR-fetch and serialization-engine contract, treated as authoritative per that citation, **UNVERIFIED**
against its own text.

## Summary

| # | Severity | One-line | Location |
|---|---|---|---|
| 1 | BLOCKER | The 202-async / 200-GET-resource error-reporting model (fixed in error-handling.md and bundle-format.md) was not propagated to manifest-schema.md, file-uploads.md's own Size Validation section, or flows/08-upload-to-play.md — all three still describe a synchronous `422` for checks that are async by the corpus's own authoritative resolution | `docs/specs/manifest/manifest-schema.md:192-198`, `docs/specs/api-design/file-uploads.md:154-156`, `docs/specs/flows/08-upload-to-play.md:47-49,55-56` |
| 2 | BLOCKER | FR-GDET-004 (info-doc Markdown sanitization) has no implementation spec anywhere — no library, no server/client split, no allow-list mechanism — and input-validation.md's own security section asserts there is no such second rendering surface | `docs/requirements/game-catalog.md:48`, `docs/specs/api-design/input-validation.md:182-195`, `docs/specs/game-frontend/game-asset-serving.md:167`, `docs/specs/manifest/bundle-format.md:494` |
| 3 | DRIFT | The synthetic error `check` identifier for an abandoned/leased-out `PROCESSING` row is named differently in the two documents that define it | `docs/specs/manifest/bundle-format.md:264,706`, `docs/specs/platform/data-model-catalog.md:327` |
| 4 | AMBIGUITY | Whether `make seed`'s `ApplicationRunner` blocks synchronously on the (by design, async-job-driven) validation pipeline before startup completes, or fires-and-forgets, is unstated | `docs/specs/deployment/local-environment.md:298-309` |

No further BLOCKER or AMBIGUITY findings at the severity threshold defined in the brief. Two DRIFT/NIT-tier items are folded into the "What checked out" section below as caveats rather than separate findings, per the instruction to state confirmations with evidence.

## Findings

### F1 — BLOCKER — The async-validation error contract is fixed in two documents and still broken in three others

**Where:**
- Correct/authoritative version: `docs/specs/api-design/error-handling.md:85-136`, `docs/specs/manifest/bundle-format.md:287-329` (§3.4), `docs/specs/manifest/INDEX.md` (Key Decisions bullet)
- Broken versions: `docs/specs/manifest/manifest-schema.md:192-198`, `docs/specs/api-design/file-uploads.md:154-156`, `docs/specs/flows/08-upload-to-play.md:47-49,55-56`

**Quotes:**

Authoritative (error-handling.md, which even documents that it was previously wrong):
> "Everything that requires the bundle bytes — manifest schema, entry points, GDK class absence, serializability — runs **after** `confirm` has already returned `202 Accepted`... There is no request left to fail. The result is the **state of the version resource**, read from `GET /api/games/{gameId}/versions/{uploadId}`" (error-handling.md:105-108)
> "*An earlier version of this section showed one `422` from `…/confirm` mixing a step-1 synchronous check with an async one — a response that cannot be produced, from an endpoint that returns `202`.*" (error-handling.md:135-136)

bundle-format.md agrees explicitly (§3.4): "**Phase B–G failures are not an HTTP error at all.** They are the *state of a resource* that was successfully created." (bundle-format.md:300-301)

Yet **manifest-schema.md**, whose Layer 1/2 checks are Phase D (asynchronous, per bundle-format.md's own §3.1 table), still says:
> "Fatal validation failures are reported using the bundle-validation error shape defined in `api-design/error-handling.md`: a `422 business-rule-violation` whose `errors` array lists every failure..." (manifest-schema.md:194-196)

**file-uploads.md** correctly states the async model at line 63-65 ("Response — 202 Accepted... runs asynchronously") and even gets it right in its own Error Cases table at line 149 ("Manifest invalid, entry class missing, GDK classes present | async | Version → `FAILED`; structured errors in GET response") — but then contradicts itself four lines later, in the very next section:
> "The actual uploaded object size is also checked at confirm time — if the stored object is larger than declared, the confirm fails with 422." (file-uploads.md:156, under "## Size Validation")

That check is bundle-format.md's own Phase B1 (`bundle.storedSize`), and bundle-format.md's §3.1 table classifies **all of Phase B** as "after `POST .../confirm`, background job" — i.e. asynchronous, not something the confirm request itself can fail on.

**flows/08-upload-to-play.md** compounds both errors in one document:
> "Confirm: `POST /api/games/{gameId}/versions/{uploadId}/confirm` → `202 Accepted`. The stored object's actual size is checked against `declared_size_bytes`; larger → `422`." (flows/08-upload-to-play.md:47-49) — asserts `202` and a synchronous `422` outcome for the same request in adjacent sentences.
> "Every check runs and **all failures are reported together** (`FR-UPLOAD-008`) as a `422` with a `{check, message}` array — a developer should not fix one error per round trip." (flows/08-upload-to-play.md:55-56) — this is describing §C, "Validation, asynchronous," i.e. the entirety of Phase C (manifest, entry points, GDK classes, `gdkApiVersion`, round-trip) as a `422`, directly contradicting error-handling.md and bundle-format.md §3.4.

Note also that `manifest/INDEX.md`'s own "Key Decisions" summary of `manifest-schema.md` states the **correct** model ("only synchronous slot-request failures are a `422`; asynchronous validation results are the *state of a resource*, returned as `200`") — so the index that a reader is told to consult first (per this repo's CLAUDE.md, "always start from the relevant INDEX.md") gives the right answer, but the document it points to (`manifest-schema.md`) gives the wrong one in its own body text. This is exactly the kind of drift that survives a spot-check of the index.

**Blocks:** the `POST /api/games/{gameId}/versions/{uploadId}/confirm` handler's response-building code, the `GET /api/games/{gameId}/versions/{uploadId}` handler's response-building code, and the manifest validator's error-serialization path (whichever class assembles the `{check, message}` array into an HTTP body).

**Scenario:** A low-effort implementation agent tasked with "implement manifest validation error responses" opens `manifest-schema.md` (the document literally named for the job) and reads its self-contained "Error model" section, which says manifest validation failures are a `422 business-rule-violation`. It builds the manifest validator to throw a `BusinessRuleException` that the confirm endpoint (or a synchronous call inside it) turns into a `422`. Separately, an agent implementing the confirm endpoint reads file-uploads.md's "Size Validation" section and builds a synchronous stored-size check into the confirm handler that returns `422` on mismatch. The result: the confirm endpoint sometimes blocks on object-storage I/O and returns a `422` Problem Detail (contradicting its own `202 Accepted` contract at file-uploads.md:63 and the async job design bundle-format.md's whole Phase B–G structure depends on), and the manifest validator's fatal-error path is wired to throw an HTTP exception instead of writing to `validation_errors`/`validation_warnings` on the `game_version` row — which is what `GET .../versions/{uploadId}` (line 108 of error-handling.md) actually needs to read back. Two independently-built components (confirm handler, GET handler, validator) end up assuming different contracts, and the client-side upload UI — which has to render *one* of these — cannot be built correctly against both.

**Suggested resolution:** `bundle-format.md` §9 (Assumptions this spec makes visible) already tracks D2 as "assumed resolution... needs an edit to a document this spec does not own." That edit needs to land in three more places, not just `error-handling.md`: (1) `manifest-schema.md`'s "Error model" section (lines 192-198) needs to say Layer 1/2 manifest failures are reported the same two ways bundle-format.md's stages are — `422` only if manifest validation could somehow run synchronously (it cannot, per Phase D's async classification), otherwise `200`/`FAILED` via GET; (2) `file-uploads.md`'s "Size Validation" section (line 154-156) needs to be rewritten to match its own Error Cases table three lines above it — B1 is async, reported via GET, not "confirm fails with 422"; (3) `flows/08-upload-to-play.md` §B and §C need the same fix. `manifest-schema.md` is the natural owner of the manifest-specific wording since it already owns "Error model"; the other two are transcription copies of the same underlying model and should just cite `error-handling.md` rather than restate it.

---

### F2 — BLOCKER — FR-GDET-004's Markdown sanitization for the info document has no implementation spec, and a sibling document asserts the surface doesn't exist

**Where:** `docs/requirements/game-catalog.md:48`, `docs/specs/api-design/input-validation.md:182-195`, `docs/specs/game-frontend/game-asset-serving.md:167`, `docs/specs/manifest/bundle-format.md:494`, `docs/specs/platform/data-model-catalog.md:161-164`

**Quotes:**

The requirement:
> "FR-GDET-004 | Markdown sanitization | The rendered Markdown document must be sanitized to allow only informational content (headings, paragraphs, lists, code blocks, images, links). Executable content, iframes, and script injection vectors must be stripped." (game-catalog.md:48)

Two specs cite FR-GDET-004 as if its mechanism were defined elsewhere:
> "the entry at `manifest.infoDoc` | its rendered content is served through the game detail page (FR-GDET-003/004), where FR-GDET-004's sanitization applies" (bundle-format.md:494)
> "`infoDoc` | Rendered through the catalog's sanitizing Markdown path (`FR-GDET-004`), not served raw" (game-asset-serving.md:167)

But `input-validation.md`, the document that *does* specify a Markdown-rendering pipeline in detail (library-agnostic config: `html: false`, allowlisted inline constructs, `linkify: false`), specifies it only for game-log entries, and states:
> "`GAME_LOG` entries support basic Markdown (`game-contracts.md` FR-LOG-002) and are rendered by the platform UI outside the iframe (FR-LOG-005). **This is the only surface where the platform renders anything other than plain text**" (input-validation.md:184-187, emphasis added)

That statement is false as written — FR-GDET-003 also requires rendering the info-doc Markdown on the game detail page — and no other document picks up the slack: `data-model-catalog.md` confirms `info_doc_markdown` is stored as **raw** markdown text (§1, line 161-164: "`info_doc_markdown` follows the same rule and has an additional wrinkle: `manifest.infoDoc` is a *path into the archive*, so what is stored here is the resolved content of that file at first activation, not the path" — no mention of sanitizing before storage), which means sanitization, whatever it is, must happen at render time, not at ingestion. Nothing names the library, whether it runs server-side (producing sanitized HTML the frontend embeds) or client-side (a React component like `react-markdown` + `rehype-sanitize`), or which HTML tags map to the required allow-list (`headings, paragraphs, lists, code blocks, images, links`). This interacts directly with a platform-wide constraint that eliminates the naive implementation:
> "`dangerouslySetInnerHTML` is **banned platform-wide**, enforced as `react/no-danger: error` in ESLint" (input-validation.md:178-180)

So the naive "convert Markdown to an HTML string server-side, inject with `dangerouslySetInnerHTML`" approach is explicitly forbidden by a rule in the very document that also (incorrectly) claims this rendering surface doesn't exist.

**Blocks:** the game detail page's info-section renderer (FR-GDET-003), and whatever component or endpoint is responsible for turning `game.info_doc_markdown` into displayed content — no class, library dependency, or endpoint is named anywhere in the corpus for this.

**Scenario:** An implementation agent building the game detail page reads `input-validation.md` as the platform's security/output-encoding reference (a reasonable thing to do, since it's the only doc that discusses Markdown rendering rules at all), takes its "this is the only surface" claim at face value, and never builds a sanitization path for the info doc at all — rendering `game.info_doc_markdown` with a plain Markdown-to-HTML converter and `dangerouslySetInnerHTML` (violating the ESLint ban, but ESLint bans are sometimes locally suppressed under deadline pressure) or, worse, an unsanitized `<div>{md}</div>` that lets a malicious `<img onerror=...>` or `<script>` embedded in a community game's `INFO.md` execute in the platform's own origin — which, unlike the sandboxed game iframe, **holds the session cookie**. This is a materially worse outcome than any hole in the game-iframe sandbox, because it's on the trusted side of the origin boundary this whole slice's other specs (game-asset-serving.md) work hard to construct.

**Suggested resolution:** `input-validation.md` should correct its "only surface" claim, and either it or a new/extended section of `game-catalog.md`'s eventual spec (or `platform-frontend/shell-architecture.md`, which is the natural home for "how the shell renders anything") should name the actual mechanism: pick a library (e.g. `react-markdown` with `rehype-sanitize` and an explicit allow-list schema matching FR-GDET-004's element list), state whether it runs client-side (consistent with "no client-side state store... server-authoritative" being about *game* state, not about rendering approach) or server-side, and confirm it does not require `dangerouslySetInnerHTML`.

---

### F3 — DRIFT — Two different names for the same synthetic validation error

**Where:** `docs/specs/manifest/bundle-format.md:264,706`, `docs/specs/platform/data-model-catalog.md:327`

**Quotes:**
> "Its only reportable failures are `version.ordering` (re-checked authoritatively) and `pipeline.interrupted` (§7.2)." (bundle-format.md:264)
> "`{ "check": "pipeline.interrupted", "message": … }`. A validation job that dies with its pod otherwise leaves the row in `PROCESSING` forever..." (bundle-format.md:706)

vs.

> "a sweep finds `PROCESSING` rows whose `claimed_until` has passed and moves them to `FAILED` with a synthetic `{check: "pipeline.abandoned"}` entry." (data-model-catalog.md:326-327)

`platform-operations.md`'s FR-JOB-012 (the requirement that owns this job) doesn't name the check identifier at all ("moved to `FAILED` with a synthetic error entry"), so it doesn't adjudicate between the two.

**Blocks:** the FR-JOB-012 sweep's implementation of duty (b) — the literal string written into `validation_errors` for an abandoned `PROCESSING` row — and any client/UI code that pattern-matches on `check` values to render a friendlier message for this specific failure mode (as the corpus does elsewhere, e.g. E5's gdkApiVersion message split by above/below range).

**Scenario:** The sweep job is implemented against bundle-format.md (the document that owns the pipeline and defines every other `check` identifier in this slice) and writes `pipeline.interrupted`. A frontend developer, or a later agent adding a friendly error message for this specific case, greps the corpus for the identifier to build a switch statement, finds `pipeline.abandoned` in data-model-catalog.md (the schema doc, plausibly consulted when writing the DB-facing repair job), and the two never match — the UI's special-case branch for "your upload was interrupted, please retry" silently never fires; the entry falls through to a generic "unknown check" rendering instead.

**Suggested resolution:** Pick one (bundle-format.md is the `check`-identifier owner per its own §3.2 preamble: "Each stage names the `check` identifier that appears in the `errors` array" — data-model-catalog.md should defer to it and use `pipeline.interrupted` to match).

---

### F4 — AMBIGUITY — Does the seed `ApplicationRunner` wait for asynchronous bundle validation before startup is considered complete?

**Where:** `docs/specs/deployment/local-environment.md:298-309`

**Quote:**
> "So the runner calls the same request-slot → PUT → confirm → validate → activate path a developer would... It is slower than inserting rows and it means `make seed` exercises the upload pipeline on every developer machine, every day." (local-environment.md:305-309)

This confirms (and correctly closes) bundle-format.md §9 D10's flagged concern that the seeder used to bypass the pipeline — good, that's fixed. But the pipeline it now drives is, by bundle-format.md's own §3.1 table, split across a synchronous slot request and an **asynchronous background job** ("B–F — Validation | after `POST .../confirm`, background job"). Nothing in this section, or anywhere else I found, states whether the `ApplicationRunner`:
(a) blocks and polls `GET .../versions/{uploadId}` (or invokes the validation job in-process synchronously, since runner and job share a JVM at startup) until the seeded game reaches `ACTIVE` before Spring context startup is considered complete, or
(b) fires the confirm and moves on, leaving validation to complete on the job scheduler's own cadence, in which case the catalog could briefly (or, if something is wrong with the local MinIO wiring, indefinitely) list the seeded game with no `ACTIVE` version.

**Blocks:** the `ApplicationRunner` bean that drives the seed path — specifically, whether it's implemented as a blocking call chain or as a fire-and-forget REST call sequence.

**Scenario:** A container starts, the seed runner fires the upload flow, and — because validation is async by design — the runner returns before the background job has picked up the `PROCESSING` row. If the runner is the *only* thing gating "seed complete" logging/readiness, a developer running `make seed && make e2e-test` (or CI doing the equivalent) can race the background validation job and see the catalog list a game with `active_version_id IS NULL`, intermittently — precisely the failure mode this section was written to eliminate ("lists and cannot start," now via a timing window instead of a design bypass). This is a smaller, timing-shaped version of the same defect the section already spent a paragraph fixing.

**Suggested resolution:** local-environment.md §6 should state explicitly that the seed runner either invokes the validation logic synchronously in-process (bypassing the job scheduler, but not the pipeline stages themselves — which is a legitimate distinction bundle-format.md's own phase table supports, since "background job" describes deployment topology, not an inherent asynchrony requirement) or blocks on polling until `ACTIVE`/`FAILED` before returning.

## Assessment of already-logged Open Questions — none are mislabelled

Per the brief's instruction, I evaluated every OQ in my slice's owned documents against "does this actually block MVP implementation." None do; all are correctly filed as deferred:

- **bundle-format.md OQ-001** (orphaned-by-GDK-range has no catalog representation) — the MVP ships exactly one GDK version and rebuilds official games in lockstep with the platform (§6.3's own argument), so the orphan case cannot occur in the MVP's own operation; it only matters once the platform's supported range has moved independently of a game, which requires either community uploads or a GDK bump without a corresponding official-game rebuild, neither of which happens in-MVP. Correctly deferred.
- **bundle-format.md OQ-002** (deny list vs. `frontend.root` allow list) — checked concretely: the deny list (§5.2, echoed verbatim in game-asset-serving.md:162-167) is fully specified — four concrete rules (`manifest.json`, the `backend.path` entry, the `infoDoc` entry, and any `*.jar`/`*.war`/`*.class`) — implementable today without ambiguity. The allow-list redesign is a manifest schema change or nothing; not required for MVP correctness. Correctly deferred, and I verified the two specs that would need to agree on the interim deny list (bundle-format.md and game-asset-serving.md) do agree, verbatim.
- **bundle-format.md OQ-003** (no integrity digest on published objects) — a detectability improvement, not a correctness gap; the archive-retention design already makes corruption *repairable*, just not automatically *detected*. Doesn't block MVP.
- **bundle-format.md OQ-004** (harness can't check `gdkApiVersion` offline) — a harness (developer-tooling) limitation, not a platform-implementation blocker; FR-HARNESS-002's enumeration correctly omits it per bundle-format.md §6.2's own note.
- **bundle-format.md OQ-005** (30s upload budget unmeasured) — a Should-priority NFR benchmarking gap, not a missing decision; nothing is unimplementable, only unverified for performance.
- **data-model-catalog.md OQ-001** (rejected-resubmission leaves a community game stuck with no rollback) — explicitly and correctly scoped: "Dormant for the MVP under ADR-0006; must be resolved before community uploads open" (data-model-catalog.md:616-617). Under ADR-0006 every MVP game is Official and never enters `game_review` at all (confirmed: FR-OFF-002, "Official games are never placed in the pending review queue"), so this path is unreachable in the MVP. Correctly deferred.
- **data-model-catalog.md OQ-002** (`decided_by` is a shared credential, weak audit trail) and **OQ-003** (pending-review has no owner-facing UI representation) — both are community-review-path UX/audit concerns, unreachable for the same ADR-0006 reason. Correctly deferred.
- **game-asset-serving.md OQ-001/002/003** (fullscreen permissions, private-bundle exposure, manifest-declared stylesheets) — all explicitly scoped as additive, non-breaking, post-MVP UX/feature gaps; OQ-002 is the same deny-list-is-good-enough-for-now situation as bundle-format.md OQ-002, already assessed together above. None block MVP.
- **admin-tooling.md OQ-001/002/003** (resubmission policy, post-approval delisting, badge-visibility UX) — all inside the community-review path, dormant per ADR-0006 for the same reason as data-model-catalog.md's OQs. Correctly deferred.

## What checked out

- **Official-game activation (Scenario 1) is now coherent across all three documents that touch it.** `bundle-format.md` §5.4 (lines 569-578), `data-model-catalog.md` §2 "The badge transition at activation is `VERIFIED → UNVERIFIED` only" (lines 269-291, with an explicit before/after table), and `file-uploads.md` step 3.6 ("On success: transitions version to `ACTIVE`, and — **only if the game's badge is `VERIFIED`** — clears it to `UNVERIFIED`," line 72) all agree, and all three independently explain *why* (the `game_official_ownerless_ck` equivalence constraint) rather than just asserting the rule. `flows/08-upload-to-play.md` §D step 5 agrees too. Last session's fix is real and consistently applied — this is not still broken.
- **Crash recovery for a `PROCESSING` row (Scenario 2) is fully specified and consistent, modulo F3's naming drift.** `data-model-catalog.md`'s `game_version` table now has `claimed_by`/`claimed_until` columns (lines 222-223) and `game_version_stuck_idx` (line 239); `platform-operations.md` defines FR-JOB-012 with exactly the two duties bundle-format.md's §7.2 describes; `file-uploads.md` documents the lease at the API level (lines 130-133); every non-terminal status (`PENDING`, `PROCESSING`) now has a documented, requirement-backed exit. This was a real gap in a prior session and it is now closed, correctly, in the schema, the requirement, and both specs that reference it.
- **Concurrent-slot version-ordering (Scenario 3) is correctly narrowed and consistently described.** `file-uploads.md` ("Step 1's version-ordering check is advisory; the authoritative one is at activation," lines 85-90), `bundle-format.md` §3.1 (same argument, same worked example: request `1.3.0` then `1.2.5`, activate out of order), and `flows/08-upload-to-play.md` step D1 all describe the identical mechanism — advisory check at slot request (stage A2), authoritative re-check under the `game_version_active_key` partial-unique-index lock at activation. FR-UPLOAD-006 is not silently weakened; the corpus is explicit about why a single check can't do both jobs.
- **`manifest.schema.json` and `manifest-schema.md` agree on every field I checked**: required-field sets (top-level and `capabilities`), types, string/array length bounds, patterns (`version`, `gdkApiVersion`, parameter `key`), the `if`/`then` per-parameter-type branches, and the required-field sets for `backend`/`frontend`/`teamTemplate`/`parameter`. No prose/schema disagreement found — this is the one artifact the brief called a hard BLOCKER-if-wrong, and I did not find it wrong.
- **The archive-publication deny list (Scenario 5, and OQ-002 above) is specified identically, verbatim, in both documents that need to agree on it** — `bundle-format.md` §5.2's table and `game-asset-serving.md` §4.2's table list the same four exclusions in the same terms. It is concrete enough to implement directly: a filter that checks an entry's path against `{manifest.json, manifest.backend.path, manifest.infoDoc}` plus a `*.jar`/`*.war`/`*.class` glob.
- **The local seed path (Scenario 6) now drives the real upload pipeline rather than writing storage by hand**, per `local-environment.md` §6 lines 298-309, closing bundle-format.md §9 D10 exactly as that document's "Assumed resolution" specified. See F4 above for the one residual timing question this raised.
- **Size/timeout/count configuration values are consistent everywhere they're cited.** Bundle size (256 MB), upload rate limit (10/hour), validation lease (10m), slot-cleanup interval (15m), and slot TTL (1h, inferable from file-uploads.md's own worked example timestamps) all match across `bundle-format.md` §8, `file-uploads.md`, `rate-limiting.md` Tier 3, `local-environment.md` §7.2, and `platform-operations.md`'s FR-JOB-012. The uncompressed-size/ratio/entry-count/nesting-depth ceilings in bundle-format.md §2.3 are single-sourced (no other document restates them), so there's nothing for them to drift against.
- **FR-HARNESS-002/010 and backend-gdk-api.md §5.1 close out bundle-format.md's own R1 and R3 self-flagged gaps.** `FR-HARNESS-010` (game-development-experience.md:165) now names the executing serialization round-trip explicitly, citing GRMP-F4 by name; `backend-gdk-api.md` §5.1 (lines 294-321) now documents the exact state-type constraints (records/`-parameters`, scalar map keys, no polymorphic fields) that bundle-format.md §4.4's upload-time static check enforces. Both were open items in bundle-format.md §9 as of whatever session wrote it; both are resolved in the current corpus.
- **The FR IDs the brief flagged as "cited by no spec"** (`game-catalog.md` FR-CAT-001/003/009, FR-GAME-001/004, FR-GDET-001/002/006/008/009, FR-UPROF-001/003/004, NFR-USAB-002; `admin-tooling.md` FR-ADM-003, FR-BADGE-003, FR-OFF-002, FR-PRV-003, FR-REV-003) are, with the one exception written up as F2, genuinely self-contained at the requirement-text level (exact column lists, exact button-visibility rules, exact badge semantics) and don't need a separate design spec to be implementable without invention — or they govern the community-upload/review path, which is dormant for the MVP under ADR-0006 (confirmed directly: FR-OFF-002 makes Official games — the *only* games the MVP has — never enter the review queue that FR-REV-003, FR-BADGE-003, FR-PRV-003 etc. govern). I did not find a hidden decision point in any of them beyond FR-GDET-003/004's sanitization mechanism (F2).
