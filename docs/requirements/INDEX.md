# Requirements

**What the system must do.** Seventeen documents, one per feature area, each owning a set of
numbered requirement IDs. How the system is *designed* to do it lives in
[`../specs/`](../specs/INDEX.md); what gets *built next* lives in
[`../implementation/`](../implementation/INDEX.md).

Most documents open with a **Related API Specifications** section linking to the specs that realise
them. Those links are maintained in both directions — when a spec moves or is added, the requirement
document's link list is updated with it.

## Documents

| Document | Covers | Defines |
|---|---|---|
| [user-accounts.md](user-accounts.md) | Registration, credential and OAuth login, sessions and displacement, account management and deletion, profiles and per-section privacy, guest accounts | `FR-AUTH` `FR-ACCT` `FR-PROF` `FR-GUEST` `FR-SESS` |
| [social-friends.md](social-friends.md) | Friendship model, request lifecycle, friend cap, discovery, visibility, guest exclusion, block-requests toggle | `FR-SOC` |
| [game-rooms.md](game-rooms.md) | Room listing and creation, joining and visibility rules, host management, teams and slots, readiness, room lifecycle | `FR-LIST` `FR-CREATE` `FR-JOIN` `FR-HOST` `FR-TEAM` `FR-READY` `FR-LIFE` `FR-XFER` `NFR-SPEC` |
| [reconnection-flow.md](reconnection-flow.md) | Disconnect detection, grace deadlines and expiry, re-entry and resync, kick mechanics, host-disconnect handling | `FR-DC` `FR-GRACE` `FR-EXPIRY` `FR-REJOIN` `FR-KICK` `FR-HDISC` `NFR-CONF` |
| [in-room-chat.md](in-room-chat.md) | Room and team channels, message delivery model, spectator exclusion, late-join team chat access | `FR-MSG` `FR-CHAN` `FR-SWITCH` |
| [notifications-invitations.md](notifications-invitations.md) | Persisted notifications vs. transient alerts, the notification centre, room invitations and invite links, friend-request notifications | `FR-NOTIF` `FR-ALERT` `FR-INV` `FR-LINK` `FR-FREQ` |
| [game-catalog.md](game-catalog.md) | Catalog listing and search, game detail pages, game management, the profile games tab | `FR-CAT` `FR-GAME` `FR-GDET` `FR-UPROF` |
| [game-history.md](game-history.md) | Per-session history recording, win-condition labels, the profile history tab, privacy and erasure pseudonymization | `FR-HIST` `NFR-HIST` |
| [per-game-statistics.md](per-game-statistics.md) | Session counting, per-game aggregates on the detail page, profile statistics | `FR-STATS` `NFR-STATS` |
| [platform-views.md](platform-views.md) | Every view in the platform frontend, navigation, redirects, and auth-tier gating | `VW-*` |
| [platform-ui-library.md](platform-ui-library.md) | Design tokens, the component inventory, layout primitives, theming, and the library's packaging constraints | `FR-TOK` `FR-COMP` `FR-LYT` `FR-THM` `NFR-VER` |
| [game-contracts.md](game-contracts.md) | The platform ↔ game protocol: inputs, effects, state, responses, structured outcome, logging, the postMessage surface | `FR-IN` `FR-EFF` `FR-STATE` `FR-RESP` `FR-OUTCOME` `FR-PROC` `FR-LOG` `FR-FA` `FR-FE` |
| [game-development-experience.md](game-development-experience.md) | The GDK (backend and frontend), the manifest, bundle packaging, the upload pipeline, asset serving, the local test harness | `FR-GDK` `FR-FEGDK` `FR-MANIFEST` `FR-BUNDLE` `FR-UPLOAD` `FR-ASSET` `FR-HARNESS` `NFR-COMPAT` `NFR-UPLOAD` |
| [platform-architecture.md](platform-architecture.md) | Game execution infrastructure: the Game Host, Orchestration, guest isolation, code loading, effect delivery, failure handling, scaling | `FR-CTX` `FR-LOAD` `FR-ORCH` `FR-REG` `FR-ROUTE` `FR-DELIVER` `FR-FAIL` `FR-SCALE` `FR-SEC` |
| [platform-operations.md](platform-operations.md) | Service topology, availability, metrics/logs/traces/alerts, CI/CD, scheduled jobs, retention, credentials, deployment | `FR-MET` `FR-TRACE` `FR-CICD` `FR-JOB` `FR-RET` `FR-CRED` `FR-DB` `FR-DEPLOY` `NFR-JOB` `NFR-OBS` |
| [admin-tooling.md](admin-tooling.md) | The internal admin API, the Official/Verified/Unverified badge model, the review queue, private-game behaviour | `FR-ADM` `FR-REV` `FR-BADGE` `FR-OFF` `FR-PRV` `NFR-AUD` `NFR-CRED` |
| [onboarding-wizard.md](onboarding-wizard.md) | **Post-MVP — cut from v1** (IR-23). First-run wizard overlay, pane structure, suppression, landing-page re-entry. Retained as the record of a deferred feature; no work item implements it | `FR-ONB` `NFR-ONB` |

`FR-OBS` is defined in **both** `platform-architecture.md` and `platform-operations.md`, and several
`NFR-*` prefixes are shared — see *Citing a requirement* below.

## Where to start

Reading these front to back is the wrong order; they were written per feature, not per journey.

- **To understand the system:** read [`../specs/flows/INDEX.md`](../specs/flows/INDEX.md) first.
  Eight end-to-end journeys, each naming the requirements it exercises at every step.
- **To implement something:** go to [`../implementation/INDEX.md`](../implementation/INDEX.md) and
  find your work item. It names exactly which documents here you need, and no more.
- **To settle a "why is it like that":** check [`../decisions/INDEX.md`](../decisions/INDEX.md). Eleven
  ADRs, and the reasoning is there rather than in the requirement.

## Citing a requirement

**The full rule lives in [`../specs/INDEX.md`](../specs/INDEX.md) § *Citing a requirement* and applies
to this directory too: every cross-document citation carries a document qualifier.**

`FR-GAME-009` alone is ambiguous. `` `game-catalog.md` FR-GAME-009 `` is not.

Twelve prefixes are genuinely defined in more than one document — these are the ones where a bare ID
resolves to the wrong requirement rather than to none:

| Prefix | Defined in |
|---|---|
| `NFR-SEC` | `admin-tooling` · `game-catalog` · `game-contracts` · `game-rooms` · `in-room-chat` · `notifications-invitations` · `platform-architecture` · `platform-views` · `user-accounts` |
| `NFR-PERF` | `game-catalog` · `game-contracts` · `game-rooms` · `in-room-chat` · `notifications-invitations` · `platform-architecture` · `platform-operations` · `platform-ui-library` · `reconnection-flow` |
| `NFR-USAB` | `game-catalog` · `game-rooms` · `platform-views` |
| `NFR-SCALE` | `notifications-invitations` · `platform-architecture` · `platform-operations` |
| `FR-SESS` | `platform-architecture` (Game Host in-memory state) · `user-accounts` (account sessions) |
| `FR-OBS` | `platform-architecture` · `platform-operations` |
| `FR-ALERT` | `notifications-invitations` (user-facing) · `platform-operations` (operational) |
| `FR-TEAM` | `game-rooms` · `in-room-chat` |
| `NFR-AVAIL` | `platform-architecture` · `platform-operations` |
| `NFR-REL` | `game-contracts` · `platform-architecture` |
| `NFR-DX` | `game-development-experience` · `platform-ui-library` |
| `NFR-SIZE` | `game-contracts` · `game-development-experience` |

**`FR-SESS` is the one that actually bites.** `FR-SESS-001` and `FR-SESS-003` exist in both
`platform-architecture.md` and `user-accounts.md` with unrelated meanings, and both are cited by M1
work items. A wrong qualifier there is worse than a bare ID, because it reads as deliberate.

`CON-001` through `CON-012` are numbered per document and are defined in nearly all of them. A `CON`
citation without a document name means nothing at all.

Every other prefix in the table above is unique corpus-wide and may be cited bare.

## Related

- [`../specs/INDEX.md`](../specs/INDEX.md) — the design specifications that realise these requirements.
- [`../implementation/INDEX.md`](../implementation/INDEX.md) — the work-item registry. Each item names
  the requirement IDs it satisfies, document-qualified.
- [`../decisions/INDEX.md`](../decisions/INDEX.md) — the ADRs. Where a requirement was narrowed, cut or
  deferred, an ADR usually says why.
- [`../requirements-gaps.md`](../requirements-gaps.md) — the Phase 0 pre-implementation TODO. Historical:
  every critical and significant item is checked off. Kept as a record of what was found missing and
  when.
- [`../reviews/2026-08-16-implementation-readiness/INDEX.md`](../reviews/2026-08-16-implementation-readiness/INDEX.md)
  — the audit that qualified this corpus for implementation. All 23 blockers closed; IR-24 and IR-25
  remain open and non-blocking.
