# Platform frontend — implementation-readiness audit

**Agent:** Sonnet 5 · **Files reviewed:** 7 in full (+ CLAUDE.md, docs/specs/INDEX.md, docs/specs/platform-frontend/INDEX.md, docs/specs/game-frontend/INDEX.md, and targeted grep/spot-checks of docs/specs/api-design/websocket.md, rate-limiting.md, docs/requirements/reconnection-flow.md, docs/specs/platform/room-lifecycle.md, docs/specs/platform/data-model.md, docs/requirements/game-catalog.md) · **Date:** 2026-08-16

## Coverage

Read in full: `docs/specs/platform-frontend/shell-architecture.md`, `docs/requirements/platform-views.md`, `docs/requirements/platform-ui-library.md`, `docs/requirements/onboarding-wizard.md`, `docs/specs/game-frontend/game-asset-serving.md`, `docs/specs/gdk-api/frontend-gdk-api.md`, `docs/decisions/0007-game-frontend-separate-domain.md`.

Also read the `platform-frontend/INDEX.md` and `game-frontend/INDEX.md` (confirmed each subdirectory has exactly one spec file — `shell-architecture.md` and `game-asset-serving.md` respectively; there is no other implementing spec for the platform FE anywhere in the corpus).

Ran a corpus-wide `grep` for every requirement ID named in my brief's "cited by nothing" list, to independently verify the mechanical result before trusting it (brief's evidence standard requires opening files, not trusting a script). Confirmed accurate — see F2/F3 below.

Spot-checked cross-boundary claims against files I do not own, where my slice makes a factual assertion that depends on them: `websocket.md` (STOMP heartbeat/reconnect/`GAME_SYNC` wire contract), `rate-limiting.md` (`REQUEST_GAME_SYNC` bucket), `reconnection-flow.md` and `room-lifecycle.md`/`data-model.md` (the reservation model behind the pinned reconnection card). I did **not** do a full audit of those files — that is another slice's job — only enough to confirm or refute the specific claims `shell-architecture.md` makes about them.

**Not checked:** `platform-operations.md` FR-CICD-005 (e2e-on-HTTP-not-browser claim, §8 of shell-architecture.md) — took on faith, low risk. Component-level visual/UX correctness of `platform-ui-library.md`'s descriptions (not applicable — see F2, there is nothing to check it against).

## Summary

| # | Severity | One-line | Location |
|---|---|---|---|
| 1 | BLOCKER | `sandbox` attribute on the game iframe is contradicted between the two documents that both claim to define it, with opposite security reasoning | `shell-architecture.md:142`, `game-asset-serving.md:232` |
| 2 | BLOCKER | `platform-ui-library.md` (~30 FRs) has no implementing spec anywhere in the corpus, and its own CON-002-mandated standalone repo doesn't exist in CLAUDE.md's component list | `platform-ui-library.md:78`, `CLAUDE.md:42-49` |
| 3 | BLOCKER | `onboarding-wizard.md` (16 requirements, the entire document) is never referenced by any other document in the corpus — no mount point, no trigger wiring, not even a CTA row in `platform-views.md`'s Landing page table | `onboarding-wizard.md` (whole file), `platform-views.md:54-67` |
| 4 | BLOCKER | The platform shell's own CSP is never specified, despite `game-asset-serving.md` explicitly delegating it to the frontend shell spec and requiring `frame-src` be pinned | `game-asset-serving.md:265-274`, `shell-architecture.md` (no CSP section anywhere) |
| 5 | GAP | The reconnection pinned card's data source — "a field on the rooms list response" — has no corresponding field in any REST API spec found | `shell-architecture.md:244`, absence in `docs/specs/api-design/*.md` |
| 6 | AMBIGUITY | `onboarding-wizard.md` uses "guest" to mean unauthenticated visitor, colliding with `platform-views.md`'s Auth Tier vocabulary where "Guest" is a distinct tier with its own session token | `onboarding-wizard.md:7,20`, `platform-views.md:14-20` |
| 7 | NIT | `NFR-USAB-002` (platform-views.md) isn't cited by `shell-architecture.md` even though the behaviour it describes is realized there | `platform-views.md:390`, `shell-architecture.md:69-75` |

## Findings

### F1 — BLOCKER — Game iframe `sandbox` attribute contradicted between the two documents that own it

**Where:** `docs/specs/platform-frontend/shell-architecture.md:139-153`, `docs/specs/game-frontend/game-asset-serving.md:230-243`

**Quotes:**
> ```tsx
> <iframe
>   src={gameFrontendUrl}
>   sandbox="allow-scripts"
>   allow=""
>   referrerPolicy="no-referrer"
> />
> ```
> ...
> | `sandbox="allow-scripts"` **without** `allow-same-origin` | Together they would return the frame to its own origin and undo the sandbox entirely |
(`shell-architecture.md:139-146,152`)

> ```html
> <iframe src="{gameFrontendUrl}"
>         sandbox="allow-scripts allow-same-origin"
>         allow=""
>         referrerpolicy="no-referrer"></iframe>
> ```
> **`allow-scripts allow-same-origin` is safe here — and only here.** The well-known footgun is
> granting both to a *same-origin* frame, which lets the frame reach into its embedder and remove its
> own sandbox. This frame is cross-origin to the parent by construction (§3)...
(`game-asset-serving.md:230-240`)

Both documents claim ownership of this exact snippet. `shell-architecture.md:287` cites `game-asset-serving.md §6 embedding | §5 iframe attributes` in its own traceability table — i.e. it asserts it *realizes* §6, while textually contradicting §6.1's code. `shell-architecture.md`'s own INDEX.md restates the wrong (missing `allow-same-origin`) version as a "Key Decision," so the drift isn't a one-off typo — it's asserted twice, independently, in the platform-frontend subtree, against the value asset-serving.md gives with a detailed, specific security argument for why it must be the other value.

This is exactly the security disagreement the brief calls out explicitly: "A disagreement here is a security BLOCKER."

**Blocks:** The `<iframe>` JSX/HTML in the shell's `GameFrame` (or equivalently-named) component — the single most security-critical element in the platform frontend.

**Scenario:** An implementation agent reading only `shell-architecture.md` (the document whose job is specifically to describe "the game iframe — the trust boundary," §5) ships `sandbox="allow-scripts"` without `allow-same-origin`. Per `game-asset-serving.md:241-243`, this denies the game frame a real origin: `localStorage`/`IndexedDB` calls throw `SecurityError` (an opaque-origin sandboxed frame has no origin to key storage against), which breaks any game engine that touches persistent client storage (explicitly anticipated — Pixi/Phaser/Unity WASM builds are named in §6.4 as expected consumers). It also means `event.origin` on postMessage from the game frame is the string `"null"` (opaque origin), which breaks the shell's own origin-equality check at `shell-architecture.md:159` (`e.origin !== trustedGameOrigin`) — `trustedGameOrigin` is a real origin computed from `gameFrontendUrl`, never the string `"null"`, so **every message from the game would be silently dropped**, and the relay in §5 never works at all. Conversely, an agent reading only `game-asset-serving.md` ships the correct value but has no idea the sibling document disagrees and asserts the opposite reasoning as though it were the settled design.

**Suggested resolution:** `game-asset-serving.md` is the ADR-0007-realizing document and carries the actual security argument (cross-origin-by-construction makes `allow-same-origin` safe); it should be treated as authoritative. `shell-architecture.md:139-153` (code block, table row, and the identical restatement in `platform-frontend/INDEX.md`'s "Key Decisions" bullet) needs `allow-scripts allow-same-origin`, and the "why" column should be corrected to explain *why* the pairing is safe here (cross-origin by construction) rather than asserting it is unsafe.

---

### F2 — BLOCKER — `platform-ui-library.md` has no implementing spec anywhere in the corpus, and its own required repository doesn't exist

**Where:** `docs/requirements/platform-ui-library.md` (whole document — FR-COMP-002/003/004/005/007/008/009/011/012/013/014, FR-LYT-001/002/003, FR-THM-002, FR-TOK-001…007, NFR-DX-003, NFR-VER-001 — 24 of ~30 requirements), `docs/requirements/platform-ui-library.md:78`, `CLAUDE.md:42-49`

**Quotes:**
> "CON-002 | The library lives in a standalone repository, registered as a submodule of the TurnBase orchestrator repo, and is published as a scoped npm package." (`platform-ui-library.md:78`)

> `| `turnbase-frontend` (…) | Platform frontend (React 19, TypeScript) | Docker image / static assets |` — the last row of the component table; there is no `turnbase-ui`/`turnbase-design-system` row. (`CLAUDE.md:49`, full table `CLAUDE.md:42-49`)

> "Out of scope: visual design and component implementation, which belong to `platform-ui-library.md` and the separately published component library." (`platform-frontend/INDEX.md`)

I independently verified the mechanical result by grepping every requirement ID in this document across `docs/specs/` and `docs/decisions/`: the **only** hit anywhere in the implementing-spec corpus is a bare mention of `FR-COMP-010` (the `className` escape hatch) at `shell-architecture.md:41`. No document defines: the CSS delivery mechanism (CON-003 rules out Babel-transform CSS-in-JS, which still leaves CSS Modules, vanilla-extract, Tailwind, or plain CSS custom properties open — an actual architectural choice), the actual token names/CSS custom property naming scheme, the component API/prop shapes beyond one-line descriptions, the ESLint plugin's rule implementation (NFR-DX-004), or how Figtree is loaded (CON-004 says "must be loaded by the library or its setup instructions" — which one is undecided). This is distinct from the five already-logged and correctly-deferred `OQ-*` values (border radius, accent hex, contrast targets, blur fallback, Storybook) — those are visual-value decisions; what's missing here is the entire *architecture* of the package.

Compounding this: CON-002 requires the library to live in its own submodule-registered repo, but CLAUDE.md's repository table — the canonical list of what gets built — has no such repo. Nothing in the five listed repos (`turnbase-common`, `turnbase-sdk`, `turnbase-platform`, `turnbase-game-host`, `turnbase-frontend`) is a plausible home for a "separately published npm package" component library per CON-002's own wording.

**Blocks:** Every component-library task: the `Button`/`Card`/`Modal`/`Table`/etc. implementations, the token CSS file, the ESLint plugin, the package.json/build config for the "standalone repository." Transitively blocks essentially all of `shell-architecture.md`'s views (§7's room view, §6's notification rendering, all of `platform-views.md`'s tables) since `ui/` per `shell-architecture.md:32-42` "contains no components... re-exports `@turnbase/ui` only," and `@turnbase/ui` has nowhere to be built from.

**Scenario:** An implementation agent tasked with "build the design system" has a requirements document with one-line component descriptions and zero implementation guidance, no repository to check the code into, and no sibling spec document to consult (unlike, e.g., the game FE, which has both `game-development-experience.md`/`game-contracts.md` requirements *and* `game-asset-serving.md`/`frontend-gdk-api.md` implementing specs). At low reasoning effort it will invent a CSS strategy, a token-naming convention, and component internals from scratch, and nothing in the corpus can catch it being wrong because nothing else specifies what "right" looks like.

**Suggested resolution:** Either (a) add a `docs/specs/design-system/` (or similar) directory with an implementation-level spec analogous to `shell-architecture.md`, covering CSS delivery, token naming, and component composition, and register a `turnbase-ui` submodule in CLAUDE.md's repository table and `turnbase/` structure section; or (b) if the design is to fold the library into `turnbase-frontend` itself (contradicting CON-002 as currently written), amend CON-002 and add the missing architecture section to `shell-architecture.md`. Either way this needs a decision before implementation starts, not during it.

---

### F3 — BLOCKER — `onboarding-wizard.md` (entire document, 16 requirements) has no implementing spec and no integration point anywhere else in the corpus

**Where:** `docs/requirements/onboarding-wizard.md` (whole file), `docs/requirements/platform-views.md:54-67` (Landing Page section)

**Quote:**
> "FR-ONB-004 | Landing page trigger | The platform landing page provides a clearly labelled CTA (e.g. 'See what TurnBase offers') that opens the same onboarding wizard on demand..." (`onboarding-wizard.md:23`)

> Landing Page (`/`) element table: VW-LAND-001 (description), VW-LAND-002 (Login), VW-LAND-003 (Register), VW-LAND-004 (Play as Guest) — no row for an onboarding CTA. (`platform-views.md:61-66`)

I grepped `FR-ONB-` and `NFR-ONB-` across the entire `docs/specs/` and `docs/decisions/` trees: **zero hits**. `shell-architecture.md`'s directory structure (§2: `app/`, `features/{auth,rooms,catalog,profile,friends,notifications,game}`, `shared/`, `ui/`) has no `onboarding` feature and doesn't mention the wizard in its "Two views worth specifying" (§7) or anywhere in its requirements-traceability table (§10). `platform-views.md` — the document that owns every UI element on every view, including the Landing Page's button list — has no row for the FR-ONB-004-mandated CTA, despite listing Login/Register/Play-as-Guest as siblings on the same page. This is worse than a missing implementing spec (F2's situation): the *requirements* document for the shell doesn't even acknowledge the feature exists.

**Blocks:** The entire onboarding wizard component tree, the localStorage key scheme (two flags per FR-ONB-001/002/003, unnamed), where in the component tree it mounts (root layout? a specific route? — matters for whether it renders during the `/auth/callback` redirect chain), and the Landing Page CTA element itself (absent from `platform-views.md`'s own element table, so an agent implementing the Landing Page from `platform-views.md` alone won't build the CTA `onboarding-wizard.md` requires).

**Scenario:** Two independent implementation agents — one building the Landing Page from `platform-views.md`, one building the onboarding wizard from `onboarding-wizard.md` — produce inconsistent code with no document forcing them to agree: the Landing Page agent has no reason to add a CTA button (it's not in its source document's element table), and the wizard agent has no shell integration point to hook the auto-show trigger into (no localStorage-check-on-mount location is named, no component tree to mount into). At best this is discovered late; at worst the CTA is simply never built because the document an agent would actually build the Landing Page from doesn't mention it.

**Suggested resolution:** Add a `VW-LAND-005 | Onboarding CTA | ...` row to `platform-views.md`'s Landing Page table, and either fold a short "Onboarding wizard" section into `shell-architecture.md` (mount point, localStorage keys, trigger wiring against the auth-tier gate) or add it to the traceability/requirements-realized table so the gap is at least visible.

---

### F4 — BLOCKER — The platform shell's own CSP is never specified, though `game-asset-serving.md` requires it and delegates ownership to this document

**Where:** `docs/specs/game-frontend/game-asset-serving.md:265-274`, `docs/specs/platform-frontend/shell-architecture.md` (entire file — zero occurrences of "CSP," "Content-Security-Policy," or "frame-src")

**Quotes:**
> "### 6.3 The platform shell's own CSP
>
> The shell document that embeds the frame MUST pin `frame-src` to the games origin:
> ```
> frame-src http://*.games.localhost:8080;
> ```
> This blocks the frame from navigating itself anywhere else at all, closing the exfiltration channel a
> second time, in a second layer. (The rest of the shell's CSP belongs to the frontend shell spec.)"
(`game-asset-serving.md:265-274`)

I confirmed via `grep -n "CSP\|Content-Security-Policy\|frame-src" shell-architecture.md` that the string does not occur anywhere in the file. `shell-architecture.md` is unambiguously "the frontend shell spec" referred to in the quote above (it is the only spec file in `platform-frontend/`), so the explicit delegation lands on a document that never picks it up.

**Blocks:** The CSP header (or `<meta http-equiv>`) the platform's own document must send. This isn't only the `frame-src` directive named above — since no CSP section exists at all, `script-src`/`connect-src`/`style-src` for the React app itself (covering the Vite-built bundle, the REST API origin, the `/ws` STOMP endpoint, and the `/api/notifications/stream` SSE endpoint from §6) are equally undecided.

**Scenario:** §6.3's stated purpose is defense-in-depth: even if a malicious game self-navigates to exfiltrate data (the attack §6.2 already blocks via `targetOrigin` exactness), a pinned `frame-src` is a second independent layer. Without it specified anywhere an implementer will build, that second layer either doesn't exist or is invented ad hoc by whichever agent happens to notice the requirement is unmet — with no canonical value to invent it *from* (is it `frame-src {gamesOriginPattern}` derived from the same deploy-time template as `game-asset-serving.md §3.1`, or a static config value? Not stated).

**Suggested resolution:** Add a CSP subsection to `shell-architecture.md` §5 (or a new section) specifying the full directive set for platform-served documents, explicitly satisfying `game-asset-serving.md §6.3`'s `frame-src` requirement and deriving it from the same `turnbase.game-frontend.origin-template` configuration value asset-serving.md uses, so the two values can't drift independently.

---

### F5 — GAP — The reconnection pinned card's data source has no corresponding field in any REST API spec

**Where:** `docs/specs/platform-frontend/shell-architecture.md:242-245`, absence confirmed by grep across `docs/specs/api-design/*.md`

**Quote:**
> "The reconnection card is global, not room-scoped.** `VW-ROOMS-005` and `FR-REJOIN-002` pin a card
> to `/rooms` for as long as the player holds a reserved slot... It is driven by a field on the rooms
> list response, not by a WebSocket subscription to a room the client is no longer attached to."
(`shell-architecture.md:242-245`)

I searched `docs/specs/api-design/*.md` for any rooms-list response schema containing a reservation/grace-slot field (`reservedSlot`, `reservationExpiresAt`, `hasReservedSlot`, etc.) and found none — only `docs/specs/api-design/pagination-filtering-sorting.md:44` shows the query shape (`GET /api/rooms?status=...`), not the response body. The server-side reservation model is real and richly specified (`room-lifecycle.md`, `data-model.md`: `grace_reservation_id`, `grace_expires_at` on `room_participant`), so the *data* exists to serve this field — but no document I can find defines the endpoint contract that surfaces it to `/rooms`.

**Blocks:** The `GET /api/rooms` (or equivalent) response DTO on the server side, and the TanStack Query hook / `VW-ROOMS-005` pinned-card component on the client side that reads it.

**Scenario:** This is a cross-slice gap — `shell-architecture.md` names a mechanism it doesn't own the definition of. An implementer building the frontend room-list hook has nothing to type the field as; an implementer building the REST DTO independently has no requirement telling them to add it (unless the API-design slice's own audit catches this from its side). I flag it here because it's my document making the claim, but the fix belongs to whichever spec owns `GET /api/rooms`'s response shape (not found in my reviewed set — likely `docs/specs/api-design/rest-conventions.md` or a rooms-specific doc I did not review in full, out of my slice).

**Suggested resolution:** Whichever document defines the `GET /api/rooms` response schema should add the reservation field `shell-architecture.md:244` presumes exists, named and typed explicitly, and `shell-architecture.md` should cite it by name rather than "a field."

---

### F6 — AMBIGUITY — `onboarding-wizard.md`'s "guest" terminology collides with `platform-views.md`'s Auth Tier vocabulary

**Where:** `docs/requirements/onboarding-wizard.md:7,20`, `docs/requirements/platform-views.md:14-20`

**Quotes:**
> "Anonymous visitor (guest) | Arrives on the platform without an account; sees onboarding once per browser" (`onboarding-wizard.md:7`)
> "FR-ONB-001 | Auto-show for guests | The wizard is shown automatically to anonymous (guest) visitors on their first visit." (`onboarding-wizard.md:20`)

> Auth Tier Reference: "**Unauth** | No valid session token present" / "**Guest** | Valid session token for a guest account" (`platform-views.md:18-19`)

`platform-views.md` — the document `shell-architecture.md`'s route guard is built from — treats "Unauth" (no session) and "Guest" (has a *guest* session, created via `VW-LAND-004`/`VW-NAV-009` "Play as Guest") as two distinct, sequential tiers. `onboarding-wizard.md` uses "guest" as a synonym for "anonymous/unauthenticated," a different population, and never cites `platform-views.md`'s tier definitions at all (zero cross-references either direction, consistent with F3's isolation finding).

**Blocks:** The condition guarding `FR-ONB-001`'s auto-show logic — specifically, whether it should key off `Unauth` or off `Guest` in `platform-views.md`'s sense.

**Scenario:** A visitor arrives at `/` (Unauth), the wizard auto-shows and is dismissed (FR-ONB-001, localStorage flag set). They click "Play as Guest," get a real Guest-tier session (`platform-views.md` tier), and land on `/rooms`. Nothing in either document says whether creating a Guest account should be treated like `FR-ONB-002`'s "first sign-in" trigger (which the text restricts to "a registered user") or should do nothing (since the anonymous-visit flag is already set). The likely intended reading — informed by FR-ONB-003's "a user (guest or registered)" phrasing two lines below FR-ONB-001, which implies "guest" there means *has a guest account* — is that guest-account creation does **not** independently re-trigger the wizard, but this must be inferred by noticing the internal inconsistency between FR-ONB-001 and FR-ONB-003's own word choice; nothing states it directly.

**Suggested resolution:** `onboarding-wizard.md` should adopt `platform-views.md`'s tier vocabulary explicitly (cite it), and state directly whether the "first visit" flag in FR-ONB-001 is set on true Unauth arrival or on some other event, and confirm that Guest-account creation is a no-op for onboarding purposes.

---

### F7 — NIT — `NFR-USAB-002` not cited by `shell-architecture.md` despite being realized there

**Where:** `docs/requirements/platform-views.md:390`, `docs/specs/platform-frontend/shell-architecture.md:69-75`

**Quote:**
> "NFR-USAB-002 | Usability | When a Guest user attempts to access a Registered-only feature, the platform displays a clear message explaining that a registered account is required." (`platform-views.md:390`)

`shell-architecture.md`'s redirect table (§3) covers this behavior ("Guest hits a registered-only route → 403 page, 'requires a registered account'") but its traceability table (§10) cites only `VW-REDIR-005/006`, `NFR-SEC-001`, `NFR-USAB-001` for §3 — not `NFR-USAB-002`. The behavior itself checks out (matches `VW-REDIR-003`'s wording too), so this is a citation-completeness nit, not a behavioral gap.

**Suggested resolution:** Add `NFR-USAB-002` to the §10 traceability row for §3.

---

## What checked out

- **Auth-tier redirect table agreement.** `shell-architecture.md:69-75`'s four-row redirect table matches `platform-views.md`'s `VW-REDIR-001/002/003/007` verbatim in behavior (unauth→login-with-redirect, guest-on-registered-only→403, authenticated-hits-login→/rooms, any-401→clear-principal-and-redirect). Verified by direct comparison of `shell-architecture.md:69-75` against `platform-views.md:374-380`.
- **Open-redirect defense.** `shell-architecture.md:76-80`'s validation rule (must start with single `/`, not `//`, must not parse as absolute URL) is a correct, specific closure of `NFR-SEC-001`/`VW-REDIR-005/006` and correctly calls out the `//evil.com` protocol-relative bypass a naive check would miss.
- **Inbound postMessage validation (shell side) matches `frontend-gdk-api.md`'s mirrored spec.** `shell-architecture.md:157-165`'s three checks (origin equality, `event.source` identity, `GameMessage.safeParse` shape validation) are the exact mirror of `game-asset-serving.md §6.2`'s "parent's half" spec (`event.origin === gameOrigin && event.source === frameElement.contentWindow`) and of `frontend-gdk-api.md §8`'s game-side checks. All three documents agree message-for-message on this trust boundary (aside from the `sandbox` attribute itself — F1).
- **Malformed-postMessage handling agrees across documents.** `shell-architecture.md`'s `GameMessage.safeParse` (parse, not cast) matches `frontend-gdk-api.md:217-218`'s "Malformed or unrecognized message shapes from a valid origin are ignored." Both sides fail closed.
- **postMessage catalogue is consistent across `shell-architecture.md §5` and `frontend-gdk-api.md §10`.** Game→shell: `ready`, `action` (matches). Shell→game: the shell's table collapses `GAME_EVENT`/`GAME_SYNC` (server STOMP frames) into a single `game_event` postMessage, which is exactly what `frontend-gdk-api.md §4` describes ("first `game_event` after `init` is always the full current view... from the backend's `onResync` hook") — and cross-checked against `websocket.md:458` (`GAME_SYNC` → `init` then `game_event`), which independently confirms the same mapping from the server side.
- **The mandatory attach order (subscribe-before-sync) is corroborated server-side.** `shell-architecture.md §4`'s "attach order is mandatory" (subscribe, buffer, then `REQUEST_GAME_SYNC`) matches `websocket.md:441` ("Message received before `GAME_SYNC` has arrived → Buffer it") and `websocket.md:474` ("must not post `init` until it has both received `GAME_SYNC` and received the iframe's `ready` handshake") — the latter is a real ordering constraint `shell-architecture.md` doesn't spell out explicitly but doesn't contradict either.
- **`REQUEST_GAME_SYNC` rate-limit awareness is correct.** `shell-architecture.md:114-117`'s claim that snapshot-on-every-gap would be "a self-inflicted denial of service" is corroborated by `rate-limiting.md:161`: the `snapshot` bucket is 1 per 3s / burst 2, and the frame is independently flagged there as "the most expensive frame a client can send" for the same reason (re-enters the guest VM under the session's single-flight lock).
- **Room `version`/game `sequence` reconciliation split is real and correctly described.** The dense-vs-sparse distinction in `shell-architecture.md §4` matches the server-side semantics described in `websocket.md` (`GAME_SYNC` carries `asOfSequence`, holes from `send_to_player`/`send_to_team` are normal).
- **Post-Game Results as a client-side overlay, not a server state, is correctly cross-referenced.** `shell-architecture.md §7` and `platform-views.md`'s Post-Game Results section (`:248-250`) agree explicitly that the room is still `Lobby` server-side and the results view is a dismissible overlay over a still-mounted iframe.
- **CSRF/sandbox origin architecture (ADR-0007) is consistently described** between `game-asset-serving.md` and `ADR-0007` itself — the origin-template mechanism, deploy-time (never build-time) resolution, and the three-layer CSRF defense are stated identically in both documents.
