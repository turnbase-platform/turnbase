# API conventions — implementation-readiness audit

**Agent:** Sonnet 5 · **Files reviewed:** 6 owned + INDEX, 6 cross-checked in full, ~15 sampled/grepped · **Date:** 2026-08-16

## Coverage

Read in full: `docs/specs/api-design/rest-conventions.md`, `error-handling.md`, `input-validation.md`,
`pagination-filtering-sorting.md`, `rate-limiting.md` (351 lines), `openapi-documentation.md`,
`INDEX.md` (all owned files).

Also read in full, because they are the two shortest "endpoint definition" documents in the same
directory and directly exercise the error model: `file-uploads.md`, `sse-notifications.md`.

Read relevant sections in full (not skimmed) to check cross-document consistency:
`docs/specs/manifest/manifest-schema.md` (Validation/Error model §§154-215),
`docs/specs/manifest/bundle-format.md` (phase model + its own §3.4 "assumed resolution", lines
180-330 and 810-820), `docs/specs/platform/data-model-accounts.md` (`app_user`, `user_auth_method`
tables + narrative, lines 30-250 and 455-490), `docs/specs/platform/data-model-catalog.md` (`game`
table, lines 30-90), `docs/specs/api-design/websocket.md` (game-session error/auth sections, lines
330-410), `docs/specs/api-design/room-websocket.md` (Error Handling section, lines 625-714),
`docs/specs/flows/01-arrival-and-account.md` (registration + OAuth walkthroughs), `docs/specs/flows/08-upload-to-play.md`.

Sampled via grep across the full `docs/` tree for: every literal RFC 9457 `"type": "https://turnbase.io/errors...` occurrence (4 total, all inspected), every `POST|GET|PUT|PATCH|DELETE /api` occurrence, every DB `CHECK` constraint in `docs/specs/platform/data-model-*.md`, every mention of `cursor`, `privacy`/`visibility`, `/auth/callback`, `X-RateLimit`/`Retry-After`.

**Not checked / out of scope for this slice:** `room-chat-websocket.md` and the bulk of `room-websocket.md` / `websocket.md` beyond their error/auth sections — these belong to other slices' protocol design, and I only cross-checked the parts that touch error shape, rate-limit tiers, and validation, per the brief. I did not re-verify every requirement's FR/NFR numbering. `docs/decisions/ADR-*` were not opened directly — only referenced where another document cited one.

## Summary

| # | Severity | One-line | Location |
|---|---|---|---|
| 1 | BLOCKER | manifest-schema.md contradicts error-handling.md/file-uploads.md/bundle-format.md on sync-vs-async status for manifest validation failures | `docs/specs/manifest/manifest-schema.md:192-215` |
| 2 | GAP | Profile privacy / per-section visibility toggle has no REST endpoint defined anywhere (path, method, or body) despite being required (FR-PROF-004/006) and having dedicated UI (VW-SET-006/006a) and DB columns | `docs/specs/api-design/rest-conventions.md:24` |
| 3 | DRIFT | rest-conventions.md's absolute "/api/" URL-prefix rule has an unstated exception for the OAuth redirect endpoint `/auth/callback`, which is server-handled but lives outside `/api/` and outside every REST endpoint table | `docs/specs/api-design/rest-conventions.md:5` |
| 4 | GAP | No consolidated WebSocket error-code registry: room-websocket.md tabulates room + shared codes, but game-session codes (`ACTION_TOO_LARGE`, `ACTION_REJECTED`) exist only as prose in websocket.md, and error-handling.md (the doc titled "error handling") never mentions WS errors at all | `docs/specs/api-design/websocket.md:379,385` |
| 5 | NIT | `game.title` has no DB length CHECK even though manifest-schema.md bounds it to 1-60 chars and the accounts table explicitly documents its equivalent omission (username charset) — catalog table doesn't | `docs/specs/platform/data-model-catalog.md:34-54` |

## Findings

### F1 — BLOCKER — manifest-schema.md re-introduces the sync/async 422 bug error-handling.md's own changelog says was fixed

**Where:** `docs/specs/manifest/manifest-schema.md:154-215`, `docs/specs/api-design/error-handling.md:78-136`, `docs/specs/api-design/file-uploads.md:142-152`, `docs/specs/manifest/bundle-format.md:187-300,815-818`

**Quotes:**
> "Validation has two layers. Both run during upload (FR-UPLOAD-002)... Layer 1 — JSON Schema... Layer 2 — Supplementary programmatic checks... ### Error model / Fatal validation failures are reported using the bundle-validation error shape defined in api-design/error-handling.md: a 422 business-rule-violation whose errors array lists every failure" (manifest-schema.md:156-198, abridged)
>
> "Everything that requires the bundle bytes — manifest schema, entry points, GDK class absence, serializability — runs after confirm has already returned 202 Accepted... There is no request left to fail. The result is the state of the version resource" (error-handling.md:105-108)
>
> "*An earlier version of this section showed one 422 from …/confirm mixing a step-1 synchronous check with an async one — a response that cannot be produced, from an endpoint that returns 202.*" (error-handling.md:135-136)
>
> "Manifest invalid, entry class missing, GDK classes present | async | Version → FAILED; structured errors in GET response" (file-uploads.md:149)
>
> "**Phase D — manifest**... Phase B–G failures are not an HTTP error at all. They are the state of a resource" (bundle-format.md:232, 300)
>
> "D2 — the bundle-validation 422 cannot exist as documented... error-handling.md's example is a 422 on .../confirm mixing a Phase A check with a Phase F check... Assumed resolution: §3.4 — 422 for synchronous Phase A only, and a 200 resource carrying errors/warnings for everything asynchronous." (bundle-format.md:815-818)

**Blocks:** The bundle-validation job/service (the async worker that runs Layer 1/Layer 2 manifest checks after `confirm`, and the controller for `POST /api/games/{gameId}/versions` and `GET /api/games/{gameId}/versions/{uploadId}`). A low-effort agent implementing manifest validation reads `manifest-schema.md` — the document that literally owns manifest validation — and it says in its own dedicated "Error model" section to return a `422 business-rule-violation` Problem Detail with the manifest's `errors` array. That is wrong for every check in its own Layer 1/Layer 2 tables (`teamTemplates[i].size`, `parameters[i].default`, etc.) because none of them can run before the bundle bytes exist — the manifest.json is inside the ZIP, which is not available until after Step 3's `confirm` already returned `202`.

**Scenario:** Implementer builds `POST /api/games/{gameId}/versions/{uploadId}/confirm` to run the async validation job. Following manifest-schema.md literally, on a manifest schema failure (e.g. `teamTemplates[1].name` missing) the job either (a) tries to throw an HTTP 422 from a background job with no HTTP request context to attach it to, or (b) is built to have `confirm` block synchronously until manifest validation completes so it *can* return a 422 — which breaks the documented `202 Accepted` contract in file-uploads.md and the whole async/lease/`PROCESSING`-state model that `platform-operations.md FR-JOB-012` depends on. Either way, the client polling `GET .../versions/{uploadId}` per file-uploads.md Step 4 never sees the `FAILED` state with populated `errors` the way error-handling.md and file-uploads.md both specify.

**Suggested resolution:** `manifest-schema.md`'s "Error model" section (lines 192-215) should be rewritten to match `bundle-format.md`'s already-correct resolution: Layer 1/Layer 2 manifest checks are Phase D, reported only as the `FAILED` state of the version resource (`GET`, `200`, `errors` array) — never as a `422` from any request. `bundle-format.md` already fixed this same bug for `error-handling.md`'s example (see its own §D2); the fix was never propagated to `manifest-schema.md`, which still shows the old, wrong behaviour as its canonical example. `manifest-schema.md` should own this fix or explicitly defer to `bundle-format.md` §3.4 instead of repeating a (now stale) copy of the error shape.

---

### F2 — GAP — Profile privacy / per-section visibility has requirements, UI, and a schema, but no REST endpoint anywhere

**Where:** `docs/specs/api-design/rest-conventions.md:24`, `docs/requirements/user-accounts.md:81-83`, `docs/requirements/platform-views.md:345-346`, `docs/specs/platform/data-model-accounts.md:346-349`

**Quotes:**
> "Use PATCH when the client submits only the changed subset — a single field, a flag toggle, or a group of fields that are always changed together (e.g., **toggling profile section visibility**)." (rest-conventions.md:24)
>
> "FR-PROF-004 | Profile privacy setting | A registered user may set their profile to private at any time." / "FR-PROF-006 | Per-section visibility | A registered user with a public profile may independently hide any of [history, stats, friends, uploaded games]..." (user-accounts.md:81,83)
>
> "VW-SET-006 | Profile privacy toggle (public / private)... VW-SET-006a | Per-section visibility toggles (history, stats, friends, uploaded games)" (platform-views.md:345-346)
>
> `CONSTRAINT ups_history_ck CHECK (history_visibility IN ('PUBLIC','HIDDEN'))` ... (`user_privacy_settings`, data-model-accounts.md:346-349)

**Blocks:** The settings-page controller/handler backing `VW-SET-006`/`VW-SET-006a` — there is no path, method, or request/response DTO specified anywhere in the corpus, unlike every other stateful UI action (which gets at minimum an example endpoint in a flow or a table entry in `rest-conventions.md`'s Authorization table).

**Scenario:** Implementer building the account-settings screen must invent the endpoint whole-cloth: is it `PATCH /api/users/me/privacy`, `PATCH /api/users/me` with a nested `privacySettings` object, `PATCH /api/users/me/settings`, or five separate endpoints (one per toggle)? Because `rest-conventions.md` cites this exact feature as its *own worked example* of when to use PATCH, without ever naming the path, a second implementer building the same feature independently (or the OpenAPI-doc reviewer checking annotation coverage) has no way to know whether the first implementer's choice was the "intended" one — there is nothing in the corpus to compare against.

**Suggested resolution:** Either `rest-conventions.md` or a new/updated `user-accounts.md`-adjacent endpoint section should name the actual path and body shape (e.g. `PATCH /api/users/me/privacy-settings { "profileVisibility": "PRIVATE", "historyVisibility": "HIDDEN", ... }`), even briefly — this is squarely the kind of one-paragraph decision the brief flags as cheap to fix before implementation and expensive to leave implicit.

---

### F3 — DRIFT — `/api/` is stated as an absolute rule but the OAuth callback route is a real, externally-fixed exception never carved out

**Where:** `docs/specs/api-design/rest-conventions.md:5`, `docs/specs/deployment/secrets-and-configuration.md:223`, `docs/specs/flows/01-arrival-and-account.md:123-128`, `docs/requirements/platform-views.md:105-123`

**Quotes:**
> "All REST endpoints are served under `/api/`. There is no URL version prefix." (rest-conventions.md:5)
>
> "The redirect URI is registered per environment and must match exactly — `http://turnbase.localhost:8080/auth/callback`" (secrets-and-configuration.md:223)
>
> "2 | Google | Redirects to `/auth/callback?code=…&state=…` | 3 | Monolith | Verifies `state`... exchanges the code server-side..." (flows/01-arrival-and-account.md:124-125)

**Blocks:** The Spring Security / controller wiring for the OAuth2 login callback. `/auth/callback` (and `/auth/complete-registration`) are handled server-side (the monolith verifies `state` and exchanges the code — this is not a pure SPA route) and are registered with Google at a fixed, non-`/api/` path, yet `rest-conventions.md`'s URL Structure section states the `/api/` rule with no stated exceptions, and neither `/auth/callback` nor `/auth/complete-registration` appears in `rest-conventions.md`'s own endpoint tables (only the four `/api/auth/*` session-lifecycle endpoints are listed there).

**Scenario:** An implementer reading only `rest-conventions.md` (the document that owns URL structure) has no signal that a server-handled OAuth callback exists at all, let alone that it must sit outside `/api/` for reasons unrelated to REST conventions (Google's registered redirect URI is fixed infrastructure, not a design choice). If they mechanically apply the "everything is `/api/`" rule when wiring Spring Security's `redirect-uri` property, the login flow breaks in the specific environment where the callback is registered (any non-local env) since the registered URI won't match.

**Suggested resolution:** Add one sentence to `rest-conventions.md`'s URL Structure section noting that browser-navigated, provider-fixed redirect targets (`/auth/callback`, `/auth/complete-registration`) are an intentional, narrow exception to the `/api/` rule, with a pointer to `secrets-and-configuration.md` §OAuth and `flows/01-arrival-and-account.md` §E. This is cheap and the correct reading is inferable from context (hence DRIFT, not BLOCKER), but a document that states an "always" rule should name its one exception.

---

### F4 — GAP — No single WebSocket error-code registry; game-session codes exist only as prose, and error-handling.md never mentions WS at all

**Where:** `docs/specs/api-design/error-handling.md` (whole file, no WS mention), `docs/specs/api-design/websocket.md:379,385`, `docs/specs/api-design/room-websocket.md:652-679`

**Quotes:**
> "Oversized frames are rejected with `ACTION_TOO_LARGE`." (websocket.md:385, prose only, no table entry)
>
> "...produces `ACTION_REJECTED` on `/user/queue/errors`, carrying the `correlationId` and the failure *kind*..." (websocket.md:379, prose only, no table entry)
>
> "### Error codes" — a 21-row table covering `NOT_HOST` … `RATE_LIMIT_EXCEEDED`, explicitly including codes owned by other documents (`rate-limiting.md`, `input-validation.md`) but not `ACTION_TOO_LARGE` or `ACTION_REJECTED` (room-websocket.md:652-679)

**Blocks:** Whatever shared constant/enum an implementer writes for WS error codes (e.g. a `WsErrorCode` enum consumed by both the game-session and room `@MessageExceptionHandler`s). `error-handling.md` is the document titled and indexed ("RFC 9457 Problem Details, `@ControllerAdvice`, error taxonomy") as owning "error handling" for the platform, per `INDEX.md:15`, and it is exclusively about REST — it never states that WebSocket errors use a wholly different envelope and code set, nor points to where that set lives. `room-websocket.md` does the work of aggregating cross-document WS codes into one table, but its scope is room-only, so it correctly omits the two game-session-only codes — leaving them the only WS codes in the whole corpus with no table entry anywhere.

**Scenario:** An implementer builds the shared WS error-code enum by copying `room-websocket.md`'s "Error codes" table (the only such table in the corpus) verbatim, since nothing points them at `websocket.md`'s prose for the two codes it never tabulates. `ACTION_TOO_LARGE` and `ACTION_REJECTED` are missed; when the game-session handler later needs to emit them, the implementer either invents new spelling/casing inconsistent with the rest of the registry, or discovers the gap only by reading `websocket.md` end-to-end a second time.

**Suggested resolution:** Add a two-row "Game-session error codes" table to `websocket.md` (mirroring `room-websocket.md`'s format) for `ACTION_TOO_LARGE` and `ACTION_REJECTED`, and add one sentence to `error-handling.md` noting that this document covers REST error responses only and pointing to `websocket.md`/`room-websocket.md` for the WebSocket error envelope and code registry.

---

### F5 — NIT — `game.title` has no DB-level length CHECK, unlike the accounts table's documented pattern

**Where:** `docs/specs/platform/data-model-catalog.md:34-54`, `docs/specs/manifest/manifest-schema.md:75`, `docs/specs/platform/data-model-accounts.md:475-480`

**Quotes:**
> `title text NOT NULL` — no length CHECK (data-model-catalog.md:37, 52-53 show only `game_badge_ck` and `game_official_ownerless_ck`)
>
> "`title` | string | Yes | 1–60 chars | Game display name." (manifest-schema.md:75)
>
> "**No `CHECK` for the username charset.** ... The line between what is enforced here and what is enforced there is whether PostgreSQL can decide it without a library." (data-model-accounts.md:475-480 — an explicit, reasoned note for *why* a validation rule is absent from a CHECK)

**Blocks:** The `game` table DDL / migration. Not a correctness bug — `game.title` is only ever written from a manifest that was already validated against the 1-60 bound at upload time (`manifest-schema.md` Layer 1) — but it is the one field-length rule in the whole corpus with a stated app-layer bound and no matching DB CHECK, and no explanatory note the way `data-model-accounts.md` gives for its own analogous omission (username charset). This is asymmetric documentation quality, not a defect: worth a one-line fix, not worth dwelling on.

**Suggested resolution:** Either add `CONSTRAINT game_title_len_ck CHECK (char_length(title) BETWEEN 1 AND 60)` to `data-model-catalog.md`, or add a short note (matching the accounts-table style) explaining why it's intentionally omitted (e.g. "title is written exclusively from an already-validated manifest, unlike user-supplied fields").

---

## What checked out

- **REST error shape is singular and followed.** The RFC 9457 Problem Detail shape in `error-handling.md:17-29` is the only error response shape used anywhere in the corpus. A full-text grep for the literal `"type": "https://turnbase.io/errors` pattern across all of `docs/` returns exactly 4 hits: the two examples in `error-handling.md` itself, one in `rate-limiting.md` (429 shape, matches the taxonomy exactly), and one in `manifest-schema.md` (which matches the *shape* correctly — see F1 for the *status code* problem with that one).
- **The error-type taxonomy (`error-handling.md:42-54`) is a genuine single registry for REST**, and every status code in `rest-conventions.md`'s own Status Codes table (26-44) maps 1:1 to a taxonomy row — no orphan status codes, no orphan taxonomy rows.
- **Pagination is a single, consistently-referenced scheme.** `pagination-filtering-sorting.md`'s offset/1-indexed model (page=1, size=25 default, size≤100) is cited by name (`FR-CAT-004`) from four independent resource-owning documents — `game-catalog.md:31`, `game-history.md:73` ("using the same model as the game catalog"), `game-rooms.md:43,162`, `notifications-invitations.md:52` — and all four agree on default page size (25) and the metadata fields shown (total items/pages, current page, page size). No cursor-based scheme appears anywhere in the corpus (verified by grep).
- **Rate-limit tiers have an exhaustive default.** Tier 2 ("all authenticated endpoints not covered by another tier") is an explicit catch-all, so there is no implicit "guess the tier" case for a new authenticated endpoint — confirmed by checking that every endpoint sampled elsewhere in the corpus (room creation, notification reads, friend requests) falls cleanly into either an explicitly named tier or the Tier 2 default. Every one of the ~25 tunable numbers in Tiers 1-6 is backed by a `turnbase.rate-limit.*` property (rate-limiting.md:273-312), with a stated fail-closed default and a startup assertion preventing the `dev`/prod escape hatch.
- **Idempotency rules are internally consistent and match their two cited call sites.** `POST /api/games/{gameId}/versions`' `(game_id, version)`-unique retry behaviour (rest-conventions.md:125-128) matches file-uploads.md's own description of the same endpoint; the guest-minting non-idempotency (rest-conventions.md:129-131) matches Tier 5's explicit "this is accepted rather than solved" framing in rate-limiting.md:117-142.
- **OpenAPI's source of truth is stated once and consistently:** SpringDoc-generated from `@Tag`/`@Operation`/`@ApiResponse`/`@Schema` annotations (openapi-documentation.md:28-38), with a single shared `ProblemDetail` component referenced by every error response — nothing in the corpus hand-writes a competing OpenAPI YAML file.
- **WS principal resolution is stated once, consistently, in the same words, in both files that need it.** `websocket.md:405` and `room-websocket.md:593` both specify `SimpMessageHeaderAccessor.getUser()` (not `SecurityContextHolder`) for the identical reason (not populated on STOMP channel threads) — this is the kind of repetition that is *correct* (same fact restated where used) rather than drift, since both statements agree.
- **Username validation: DB and app layer divide responsibility cleanly and say so.** `app_user_username_len_ck` (data-model-accounts.md:49) matches `input-validation.md`'s 3-32 code-point bound exactly; the charset/confusable rules are explicitly and correctly deferred to the app layer with a stated reason (ICU dependency), not silently missing.
- **Chat message has no DB persistence and no DB constraint — correctly, not by omission.** `in-room-chat.md FR-MSG-005` says chat isn't persisted; grep confirms no `chat_message` table exists anywhere in `docs/specs/platform/`, so there is no DB-vs-app-layer contradiction to check for the 500-char chat bound (input-validation.md:71) — it lives only in the app layer, consistently.

## Overall readiness judgement

The cross-cutting conventions themselves — REST shape, error taxonomy, pagination, rate limiting, idempotency, OpenAPI — are well-specified, internally consistent, and (with the one real exception below) actually followed everywhere I could sample an endpoint definition against them. The rate-limiting document in particular is unusually rigorous: every number is a property, every tier has a stated key/window/breach response, and the Tier 2 default closes off the "what about endpoint X" question the brief specifically asks about. Pagination is a solid single-scheme story with four independent, agreeing citations.

The one finding that actually blocks correct implementation (F1) is not a weakness in this slice's own documents — `rest-conventions.md` and `error-handling.md` get the sync/async split right, and even document their own past mistake in a footnote. The bug is that a *third* document (`manifest-schema.md`, owned by the manifest slice but directly implementing this slice's error model) was never updated when `error-handling.md` and `bundle-format.md` fixed the same issue. This is exactly the "two documents agree, a third silently drifted" pattern the brief warns is easy to miss — worth flagging to whichever slice owns `docs/specs/manifest/` as well, since the fix belongs there.
