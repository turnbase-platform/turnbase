## Last Session Summary

**Date:** 2026-08-17 (session 12)

**Adopted [Astryx](https://github.com/facebook/astryx) as the platform's design system**
([ADR-0013](docs/decisions/0013-astryx-design-system.md)), and scanned the local toolchain before
Phase 1 coding. Documents only — still no code.

### Environment: ready, no installs needed

| | |
|---|---|
| Node / npm | **v22.20.0** / 11.9.0 ✓ — matches Astryx's own CI target. `.nvmrc` added |
| JDK | `.sdkmanrc` pins **`21.0.2-graalce`** — GraalVM CE for JDK 21, exactly what `CLAUDE.md` requires, and installed. It is not *active* only because `sdkman_auto_env=false`; `sdk env`, or flip the flag |
| Maven / Docker / kubectl / helm | 3.9.11 ✓ · 29.1.2 ✓ · v1.34.1 (`docker-desktop`) ✓ · **v4.2.4** ✓ |

Three "gaps" in my first scan were wrong and are corrected: docker and helm failed only inside the
tool sandbox (read-only `$HOME`, blocked namespaces), and Espresso is not a JDK-level install at all
— `gu` was removed in GraalVM for JDK 21+, so it arrives as Maven artifacts in the Game Host's pom.

**Helm is v4**, not 3 — `IMP-M0-08` should be written against v4 chart conventions.

### Astryx supersedes the in-house design system

`design-system.md` was written on 2026-08-16 to close IR-23: our own tokens, CSS Modules, seventeen
components. One day later the component half of it is replaced. That is a large reversal, so it is an
ADR rather than a spec edit.

**Why it is worth it:** seventeen components, their ARIA behaviour, their keyboard handling and their
documentation stop being our work. Astryx is Meta's, MIT, 150+ components, React 19+, and its CLI and
docs are built as one surface *for agents* — `astryx init` writes a component index into `CLAUDE.md`.
That matters disproportionately here, where Phase 1 is executed by agents at low reasoning effort.

**Why it costs less than it looks:** Astryx authors its styles with StyleX but ships **pre-built
CSS** — no Vite plugin, no PostCSS, no Babel config — and documents `className` override against CSS
Modules. The styling decision from yesterday survives intact for everything we write.

**What actually changed beyond the library:**

- **The aesthetic.** `platform-ui-library.md` described neon accents on near-black with frosted glass
  and gradients. `theme-neutral` is muted and minimal. FR-TOK-007 (gradients) is **withdrawn**;
  FR-TOK-001 loses the neon palette; FR-TOK-005 loses the frosted glass, and NFR-PERF-002's
  `backdrop-filter` clause goes with it. This was the substantive decision, not a side effect.
- **All five `OQ-*` in `platform-ui-library.md` are closed** — three *dropped* rather than answered,
  because each asked the platform to make a visual decision Astryx has already made. The WCAG AA hard
  floor survives, and is easier to hold on a muted palette than it would have been on neon.
- **CON-002 amended for the second time in two days**, CON-003 narrowed to our own code.
- **`IMP-M6-01` is now an integration item**, not a construction one — the largest scope reduction
  available in M6.

**Rules that keep it from drifting**, all in `design-system.md`:

1. **Exact version pins, no `^`.** Astryx is Beta at 0.4.3. Upgrades run `astryx upgrade --apply`.
2. **The ladder: compose → swizzle → write.** Stop at the first rung that works. A swizzle is a fork
   with a nice name — it stops receiving upstream accessibility fixes and cannot be codemodded.
3. **No wrapper layer.** Application code imports `@astryxdesign/core/Button` directly. `src/ui/`
   holds only what Astryx does not ship and is expected to stay near-empty.
4. **Nothing in this corpus lists Astryx's components.** Lookup is `npm run astryx -- component
   <Name>` or the MCP server. A copy would be stale within a release — the lesson from deleting 1,794
   lines of inventories the day before.

**The one trap worth repeating:** `<LinkProvider component={Link}>` must be mounted in the shell.
Without it every Astryx `Link` emits a plain `<a href>` and triggers a full page reload — dropping
the STOMP connection, the room subscription and all in-memory session state. It surfaces as a
navigation bug three milestones from where it was introduced.

`.mcp.json` (the `astryx` documentation server) is committed with this change.

---

## Previous Session Summary

**Date:** 2026-08-16 (session 11)

Five pieces of work: closed all 23 implementation-readiness blockers, completed the implementation
registry, wrote `docs/requirements/INDEX.md` and ran a corpus-wide sanity check, named the last
missing configuration key, then harvested the ten surviving non-blocking findings and pruned 7 500
lines of spent working files.

### Part 5 — harvest, then prune

**Ten non-blocking findings survived the blocker round inside per-slice review files**, where nobody
would have found them. All ten are now fixed in the corpus, and several were about to cost real time:
the `bigserial` / `GENERATED ALWAYS AS IDENTITY` split across three schema documents and the
mislabelled circular FK both land on `IMP-M0-06`, the very first substantial item.

Two are worth calling out because the fix went deeper than the finding:

- **The GDK forbade unseeded randomness and supplied no seed.** The finding was "the flagship example
  violates the determinism rule stated 60 lines above it". The cause is that the rule was
  unsatisfiable: *any* game with hidden information needs randomness, and nothing in `InitContext`
  offered a seed. Added **`InitContext.seed()`**, derived by the GDK Host from the session id
  (`game-host-internals.md` §3.5) — no proto field, no column, and replay-stability inherited from
  the session id already having it. Fixing only the example would have left every developer with the
  same impossible rule.
- **`test-harness.md` told developers the Game Host blocks filesystem and network calls** — the exact
  claim the Espresso spike disproved. It now states what the container enforces versus the context,
  and warns that Compose enforces neither, so "it ran locally" is not "it is allowed".

Also fixed: `platform-ui-library.md` listed all five of its OQs as open when `design-system.md` had
resolved four of them.

**Then the pruning.** `docs/` went from 30 229 lines to 22 715 — **25% smaller**:

| Removed | Lines | Why |
|---|---|---|
| 5 machine-extracted inventories | 1 794 | Snapshots taken *before* remediation, enumerating exactly what it changed. `config-ops.md` had no `spectator-capacity`, `minio-init`, Promtail, Alertmanager or the two Postgres roles; `api-surface.md` had no room REST API at all |
| `remediation-plan.md` | 2 280 | Executed. Every fix is in the review INDEX's `Closed:` lines and the registry's gates table |
| 8 slice reports, 2026-08-16 | 3 184 | Harvested first, then dropped |
| 5 domain reports, 2026-07-02 | 380 | Round closed and superseded by a full re-audit of the same corpus |
| `requirements-gaps.md` | 34 | Phase 0 TODO, all items checked. Its open-questions list was a stale duplicate of the specs' own |

A stale inventory is worse than no inventory: it is exactly the kind of file an agent greps into and
believes. That, rather than size, is why they went.

**Kept, deliberately:** `espresso-spike-results.md` (nine inbound citations; in the read-lists of
`IMP-M0-04` and `IMP-M3-02`) and both review INDEXes, which carry every blocker with its evidence and
resolution. `docs/superpowers/specs/2026-06-12-repo-strategy-design.md` was an unreferenced orphan but
a real decision, so it became **ADR-0012** rather than being deleted; `docs/superpowers/` is gone.

**Every relative link in the corpus now resolves with no exclusions** — the 19 long-standing false
positives went with the remediation plan.

### Part 4 — `turnbase.room.spectator-capacity` (IR-24)

The last open finding: NFR-SPEC-001 required spectator capacity to be "configurable at the platform
level" and no property name existed, so four documents referred to a `spectatorCapacity` that came
from nowhere. The key is **`turnbase.room.spectator-capacity`**, default `8`, env
`TURNBASE_ROOM_SPECTATOR_CAPACITY`.

It landed in `local-environment.md` **§7.1**, not §7.4 as the finding suggested — that guess came
from `social.friend-cap` living in §7.4, but a spectator limit is a property of a room and every other
`turnbase.room.*` key is in §7.1. The section is retitled *Room lifecycle, capacity and deadlines*.

Two things had to be decided, not just named, because the key is useless without them:

- **Platform-level, and not per-game.** A manifest declares *whether* a game supports spectating, not
  a headcount. What the limit bounds is the platform's fan-out cost, which is the same whatever the
  game is — and NFR-SPEC-001 already denies hosts any say, so a per-game number would be a third
  party's opinion about the platform's budget.
- **The wire field is the resolved value, not stored state.** Lowering the property evicts nobody; a
  room sits above capacity until spectators leave. The alternative is disconnecting people mid-game to
  satisfy a config change. `ROOM_STATE` therefore carries `spectatorCapacity` and emits **no delta**
  when it changes — it is not versioned state.

Named at all four call sites, and the two work items that said *escalate* (IMP-M0-09, IMP-M2-01) now
state the key. IMP-M0-09 keeps a sharpened version of the warning: **§7 is the whole tunable surface,
so a missing key is a specification defect rather than licence to invent one.**

### Part 3 — the requirements index, and what writing it found

[`docs/requirements/INDEX.md`](docs/requirements/INDEX.md) closes IR-25. Seventeen documents, each
with a one-line scope and **the requirement-ID prefixes it defines** — that second column is the part
worth having, because it turns "which document owns `FR-XFER`?" into a lookup.

Writing it corrected the corpus's own account of the collision problem. `specs/INDEX.md` says fifty
identifiers are defined in more than one document; that count matches IDs *anywhere* in a file, so it
counts citations as definitions. Counting definitions only, **twelve prefixes genuinely collide** —
all twelve are listed, with `FR-SESS` flagged as the one that actually bites.

Checking citations strictly against *definitions* then found **19 mis-qualified citations**: 18 in
`implementation/registry.md` — `FR-RET-003` qualified with `game-history.md`, for instance, which
discusses the requirement at length though `platform-operations.md` defines it — and one in
`manifest/bundle-format.md`. All corrected. The same pass caught `VW-RLOBBY-001…017`, a range that
silently swallows `VW-RLOBBY-008`, struck through as *(removed)* in `platform-views.md`.

This is exactly the hazard `specs/INDEX.md` names — *"a wrong qualifier is worse than a bare ID"* —
and it had gone undetected because every check written before now used the loose definition.

**Sanity check, whole corpus, all clean:** every relative link resolves; 0 mis-qualified or
nonexistent requirement citations; 0 dangling `§` references; every document registered in an
`INDEX.md`; all 59 live work items carry all five fields. Checks 2 and 3 are the ones worth
reconstructing after any documentation change — they are the two that found real defects.

### Part 2 — the registry is now complete and current

`docs/implementation/INDEX.md` promised that *every* work item carries a **Read first** list and a
**Done when** clause. It did not. An audit of the 60 item sections found **19 with no body at all**,
37 with no read-list, 53 with no *Satisfies* and 24 with no *Done when* — including `IMP-M2-01`,
`IMP-M3-01` and `IMP-M6-01`, each the first item of its milestone. The three specs written in Part 1
were cited by **no work item**, only by the gates block, so an agent picking up "Room CRUD and
listing" would have built the room REST API without reading `room-rest-api.md`.

**All 59 live items now carry Repo, Depends on, Read first, Satisfies and Done when.** Verified
mechanically: 73 document paths resolve, every `§N` reference resolves against a real heading, and
every one of the ~600 requirement-ID citations exists in the document it is qualified with. That
last check caught a real error — `FR-HOST-001…009` in IMP-M2-06, when `game-rooms.md` has no
FR-HOST-004 or 005.

Also fixed: `IMP-M6-07` retired as `CANCELLED` (IR-23 cut the wizard, but the item still read
`READY`); `IMP-M0-07`'s read-list said "nine containers" and its done-when omitted `minio-init` and
`01-roles.sql`, so **the item existing to implement IR-01 and IR-02 could have passed without
either**; `IMP-M0-10` still carried a `Gate:` line saying the metric requirements had no implementing
spec; two dead `Gate:` lines removed; `deployment/INDEX.md`'s "nine containers"; and INDEX.md's two
claims about where the register lives and which findings gate items.

`Gate:` is now present **only** when something is open, so its absence means what it says.

### Part 1 — three new specifications, one scope cut

| Document | Closes | Note |
|---|---|---|
| `docs/specs/api-design/room-rest-api.md` | IR-13 | Five endpoints. REST is membership only; every in-room mutation stays STOMP. Gated all of M2 |
| `docs/specs/deployment/observability.md` | IR-04 | All four signals wired end to end. Adds Promtail and Alertmanager as containers |
| `docs/specs/platform-frontend/design-system.md` | IR-23a | Tokens, CSS Modules, 17 components, accessibility baseline |
| `docs/requirements/onboarding-wizard.md` | IR-23b | **Cut from v1.** Banner + all 16 priorities read `Post-MVP` |

### The four scope decisions — taken by the user, before the plan was written

Recorded because a future reader will otherwise reopen them.

| Question | Decision |
|---|---|
| Onboarding wizard | **Cut from v1.** The only one of the four structural gaps droppable without weakening what the project demonstrates |
| Design system home | **Fold into `turnbase-frontend`** as an internal module with a lint-enforced import boundary. CON-002 amended; the five-repo table stays at five |
| AI players | **Keep the wire, defer the schema.** Declare the v1 behaviour of the existing surface |
| CI coverage gate | **Narrow FR-CICD-003 to unit + integration**, measured at PR time. Keeps a real gate |

### Two resolutions departed from the review's own suggestion

- **IR-11 needs no new table.** The review left "record the closure as owed" unresolved. The
  mechanism already existed — §5.1 duty 2's deferred tail — which broadcasts *and* evaluates closure
  under the claim. A `room_closure_owed` table would be a second durable to-do duplicating one that
  works; ADR-0010's lesson is about keying such tables correctly, not minting more.
- **IR-12 declares the v1 behaviour of the AI wire surface** rather than adding a schema
  representation or cutting FR-HOST-003: `aiPlayers` always empty, `ADD_AI_PLAYER` always
  `AI_NOT_SUPPORTED`, `capabilities.ai: true` rejected at bundle validation, the "not an AI" closure
  clause removed. The protocol shape survives for when OQ-002 resolves.

### One dependency that is invisible from the affected documents

**IR-09's fix has two halves and IR-11 depends on the first.** Making `lost_announced_at` honest —
stamped by every path that sets `left_at`, not only by grace expiry — is what lets IR-11's owed
closure ride the deferred tail. The second half, narrowing duty 2 on `leave_reason`, is a backstop
against a writer that forgets. Doing only the narrowing would have left the column meaning something
other than its name, which is how the defect arose.

### Two new findings, both closed in Part 3

- ~~**IR-24**~~ — NFR-SPEC-001's spectator capacity had no configuration key. **Closed:**
  `turnbase.room.spectator-capacity`, default `8`, `local-environment.md` §7.1.
- ~~**IR-25**~~ — `docs/requirements/` had no `INDEX.md`. **Closed.**

Both are in the review INDEX under *Found during remediation*, each with a `**Closed:**` line.

### Corpus state

**Every relative link in the corpus resolves — 0 broken.** The 19 long-standing false positives are
gone with `remediation-plan.md`, so the check is now clean with no exclusions for the first time.

`docs/` is 22 715 lines after Part 5's pruning, down from 30 229. Everything that remains is either
normative (requirements, specs, ADRs), the build plan (implementation), or a closed round's record of
why the corpus is shaped as it is (two review INDEXes plus the Espresso spike results).

## Earlier Sessions

**Date:** 2026-08-15 (session 9)

**Finished Phase 0.** The corpus is now implementation-ready: every table is defined, the services
are wired and startable, config and secrets have a home, the schema has an evolution story, and eight
end-to-end journeys trace the whole system across components. **21 new files, ~35 edited.**

### What was written

| Stage | Output |
|---|---|
| 1 — the rest of the data model | Five sibling schema docs under `docs/specs/platform/`: accounts, social, catalog, history & statistics, notifications. ~30 tables |
| 2 — schema migrations (**closes OPS-3**) | **ADR-0011** (Flyway, forward-only, backward-compatible) + `deployment/schema-migrations.md` + FR-DB-001…004, CON-012 |
| 3 — system wiring | `deployment/local-environment.md`: nine containers, ports, startup and readiness budget, K8s-vs-compose, seeds, testing, and **the consolidated configuration surface** — every tunable in the corpus in one table |
| 4 — secrets (**closes OPS-5**) | `deployment/secrets-and-configuration.md` + FR-CRED-001…005. JWT key set with graceful rotation |
| 5 — end-to-end flows | `docs/specs/flows/` — INDEX + eight journeys |
| 6 — remaining specs | `manifest/bundle-format.md` (subagent), `gdk-api/test-harness.md`, `platform-frontend/shell-architecture.md` |
| 7 — edit backlog | platform-operations, user-accounts, rest-conventions, sse-notifications, websocket, the gRPC sweep, platform-ui-library, and the ID-qualification rule |

**Stage 1 decided five files rather than one.** Each domain runs 250–400 lines in the established
voice, and the INDEX is the navigation layer the corpus already uses. `data-model.md` keeps the
shared conventions the five inherit.

### The defects — 27, found in three distinct ways

**A gate review of Stage 1 returned 4 blockers, 14 defects, 8 nits and 6 coverage gaps.** All were
accepted; the three claims I had made about defects in the *requirements* were independently
confirmed real rather than manufactured, but **two of my resolutions did not execute**:

1. **`DISCARDED` was unreachable for the version my own FR-ACCT-007 amendment had to discard.** The
   status required `SUPERSEDED`, which requires a newer version — which never arrives for a
   single-version game whose owner is gone. The amendment purged nothing in the common case.
   "Retired" is now two disjoint conditions.
2. **The erasure scatter stranded three live objects** — an open `game_review` sitting in the admin
   queue forever addressed to a developer who cannot be notified, `room_invitation` on both legs, and
   `room`/`room_participant` entirely, despite `data-model.md` already defining
   `closed_reason = 'ACCOUNT_DELETED'` with no writer. **Nothing happens by cascade on that path**,
   because a registered deletion is soft — which is exactly what made the omissions look handled.

Also from that review: a `room_invitation` with no expiry made its notification **permanently
unpurgeable** (three retention requirements silently narrowed); `ghe_placement_ck` would abort the
whole recording transaction on a malformed outcome with no possible retry; the two columns whose
entire purpose is `ON DELETE CASCADE` had no index; and my partial-index rationale contradicted what
the sibling document said correctly about NULL distinctness.

**The reviewer also caught that all five files ended in literal `</content></invoke>` tool
scaffolding.** It was eight files, not five.

**The bundle-format subagent found an MVP-blocking defect by composing two correct documents.**
`file-uploads.md` clears Verified status unconditionally at activation; `game_official_ownerless_ck`
ties `badge='OFFICIAL'` to `owner_user_id IS NULL` as an equivalence. Under ADR-0006 every MVP game is
Official — so **every official upload aborts its activation transaction, and no official game can
ever be updated.** The only path the MVP exercises. Narrowed to `VERIFIED → UNVERIFIED` only.

It also found that unpacking the whole archive under `/g/{gameId}/{version}/` **publishes the backend
JAR to anonymous callers** — `gameId` is in the hostname and the version is a public catalog column,
so the URL is derivable from a catalog page. `game-asset-serving.md` §4.2 argued the exposure was
acceptable because "a bundle is JavaScript, CSS and sprites", which stops being true the moment you
unpack all of it. Publication now filters.

Plus: `PROCESSING` had no exit at all, and because `(game_id, version)` is unique, a validation job
that died with its pod **permanently burned that version number**; the bundle-validation `422` in
`error-handling.md` mixed a synchronous check with an async one in a response no endpoint can
produce; `FR-UPLOAD-006` was checked only at slot creation, so two open slots could walk the active
version **backwards**; and the seed path bypassed the pipeline it depends on, producing exactly the
"lists and cannot start" outcome the same paragraph said it was avoiding.

**Writing the flows found the rest.** `FR-INV-008` requires invitations deleted at room *closure*,
and the only mechanism was a foreign-key cascade that fires seven days later at purge — a correct
rule, stated once, in a document none of its five producers is written from. Same shape as last
session's worst finding. And `FR-FAIL-001` terminated the session on the *first* game failure while
`FR-FAIL-003` allows three, with nothing anywhere saying what happens to the failed input or telling
the acting player: the game appears to hang, they retry, and three clicks kill the session for
everyone with no client ever told why.

### Decisions worth carrying

1. **Erasure uses a random token, not an HMAC.** ADR-0004 requires non-reversibility; `HMAC(user_id,
   pepper)` is reversible by enumeration over a small id space given the key. Only a construction
   that discards its input qualifies.
2. **Guest exclusion is a foreign key.** `friendship` references `app_user (user_id, kind)` with a
   local `CHECK kind = 'REGISTERED'`, so FR-SOC-020 cannot be violated from any code path.
3. **Guest purge is two-phase**, because a literal 24-hour delete fails permanently on
   `room_participant`'s FK and the cascade that would "fix" it would silently remove a seated player
   from a live game. FR-RET-002 amended to state the real bound (~8 days).
4. **Project only what needs an index shape the source cannot provide.** Tags get a table; the
   capability columns do not. The one exception — `title`/`short_description` — is named, because
   FR-GAME-008 makes them owner-editable and therefore not projections of anything.
5. **A notification's subject foreign key marks actionability**, and the retention purge is indexed
   *partially on having no subject* — so it can never remove an actionable message out from under a
   live object.
6. **The deploy is a rolling update even at one replica.** Under `Recreate`, ADR-0008's claim path
   never runs against a live incumbent, and `platform-operations.md`'s claim that it is "continuously
   tested rather than dormant" would be false.
7. **The monolith's readiness must not depend on the Game Host** — coupling them lets a Game Host
   restart drop every WebSocket on the platform, including rooms not running a game at all.
8. **Static serializability at upload, the executing round trip in the harness.** NFR-UPLOAD-002
   forbids running game code at upload; an executor gated on "ADR-0006 says trusted" is GRMP-F5's
   fail-open with a different variable name. New FR-HARNESS-010 makes the harness half a requirement
   rather than an assumption.

### Process

Both lessons from last session held. The Stage-1 reviewer returned a **bare idle notification**; a
re-task with an explicit file list, explicit scenarios and an explicit "an idle notification is not a
usable answer" recovered it and produced the session's best findings. Both subagents were given owned
file lists and both complied — verified with `git status`, not assumed.

**New lesson: a constraint that turns a silent corruption into a loud failure is doing its job, and
will look like the bug.** Tightening `game_official_ownerless_ck` from an implication to an
equivalence is what surfaced the MVP-blocking badge defect. The right response was to fix the
transition, not to loosen the check.

**Verification:** every relative link in `docs/` resolves (0 broken); no dangling FR/NFR citations
across all specs, decisions and requirements; no duplicate IDs within any document; every file
registered in its nearest INDEX. Four ID collisions I introduced during the session (`FR-SEC-001…005`,
`FR-ALERT-006`, `FR-HARNESS-006`, `FR-SESS-005`) were caught by the collision audit and renumbered.

---

---

## Next Priorities

**Phase 1 has started. Work from [`docs/implementation/INDEX.md`](docs/implementation/INDEX.md), not
from this file.** The registry holds **59 live work items** (IMP-M6-07 is cancelled), each with a
read-list, dependencies, the requirement IDs it satisfies and a done-when clause; this section only
says which of them to pick up.

**No work item is gated.** All 23 readiness blockers are closed, so an item's status is whatever its
own dependencies imply. The registry's gates block records how each one closed rather than what it
blocks, and a `Gate:` line now appears on an item only when one is actually open.

### The next session

**Start writing code, at `IMP-M0-01`.**

1. **IMP-M0-01 through IMP-M0-05** — the five repository skeletons. Mechanical, and they unblock
   everything. **`IMP-M0-05` now also installs and wires Astryx** (exact pins, three CSS imports in
   cascade-layer order, `<Theme>` + `<LinkProvider>`, `data-astryx-theme`, self-hosted Figtree) —
   a skeleton without them renders almost-right screens that get corrected one at a time later.
2. **IMP-M0-06 — the Flyway baseline.** The highest-value item in the registry. Transcribing
   `V1__baseline.sql` from the six schema documents is the first mechanical test of whether they are
   mutually consistent. The two hazards the audit named are now **fixed in the documents**:
   `data-model.md` states one auto-increment idiom (`bigint GENERATED ALWAYS AS IDENTITY`), and
   `schema-migrations.md` §5 names one circular foreign key rather than two. **Any further
   disagreement found while transcribing is a
   specification defect — fix the document, then the SQL.** Do not reconcile silently in the
   migration.

   Two schema changes from this session must land in the baseline:
   `room_participant_unannounced_idx` (IR-09) and nothing else — IR-11 deliberately added no table.

3. **IMP-M0-07 — the compose stack.** IR-01 and IR-02 are closed, so this is now buildable end to
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

### Spec hygiene

- **The ID-qualification retrofit** remains outstanding. `docs/specs/INDEX.md` states the rule and it
  holds for new text; the corpus predates it. The highest-traffic collision is `FR-SESS-001…004`,
  defined in both `user-accounts.md` (account sessions) and `platform-architecture.md` (Game Host
  in-memory state); all seven citations resolve correctly by context, so this is a hazard rather than
  a defect. A **wrong** qualifier is worse than a bare ID.
- **Done this session:** the `FR-JOB-007a…e` sub-duty convention is declared in `docs/specs/INDEX.md`,
  and `data-model-accounts.md:392`'s wrong FR-INV-002 citation is corrected.
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
IR-25) are closed too. **Nothing in the corpus is open.**

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
Flyway, forward-only, backward-compatible).

**Implementation:** `docs/implementation/` — the registry Phase 1 executes from. **59 live work items
across 7 milestones** (IMP-M6-07 cancelled), each carrying a read-list, dependencies, the requirement
IDs it satisfies and a done-when clause. Nothing is gated.

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
