# ADR-0014: The Platform Monolith is modular by feature, and Spring Modulith enforces it

- **Status:** Accepted
- **Date:** 2026-08-20
- **Deciders:** Project owner
- **Relates to:** [ADR-0012](0012-repo-strategy-polyrepo-submodules.md) — where a *repository*
  boundary is drawn. This ADR is about the boundaries *inside* the single largest repository.

## Context

`CLAUDE.md` calls the platform a monolith and the architecture "microservices — independently
deployable services, each in its own submodule". Both are true and they describe different axes:
ADR-0012 splits the system into five repositories, and `turnbase-platform` is one of them. That one
repository holds roughly **forty of the 59 work items** — accounts, sessions, social, rooms, chat,
game orchestration, catalog, upload, history, notifications, admin.

Until now the corpus said nothing about how that repository is organised internally. The only
evidence of the monolith's package root anywhere in ~22 700 lines was a logger name in a JSON sample
in `observability.md` — `io.turnbase.room.RoomService`, written incidentally to illustrate log
structure rather than to decide anything.

That is a gap with a specific cost profile. Phase 1 is executed by implementation agents across many
sessions, each reading only the documents its work item names. Forty items with no stated layout do
not produce one layout; they produce a layered `service/` package with forty classes in it, or four
competing conventions, decided by whichever item happened to be built first. And the decision is
close to irreversible in practice: by the time it is visible, moving it is a rename touching every
file.

The deeper risk is not the *shape* of the packages but the **edges between them**. A monolith becomes
a big ball of mud one reasonable shortcut at a time — `RoomService` calling `CatalogRepository`
directly because it needs one column, `HistoryRecorder` reaching into a room's internals because the
data is right there. Each shortcut is locally correct and collectively fatal, and none of them is
visible in the diff that introduces it.

## Decision

### 1. Package by feature, under `io.turnbase.platform`

The Platform Monolith's root package is **`io.turnbase.platform`**. Beneath it, one package per
feature, each owning its own controllers, services, repositories and domain types:

```
io.turnbase.platform
├── common/          # error model, pagination, validation, rate limiter (IMP-M1-01, M1-02)
├── account/         # registration, login, guests, profiles, erasure
├── session/         # JWT key set, session lifecycle, displacement
├── social/          # friendships and requests
├── room/            # room CRUD, lifecycle, ownership, teams, readiness
├── chat/            # in-room chat
├── game/            # orchestration client, session registry, outbox, fan-out
├── catalog/         # catalog listing, game detail
├── upload/          # bundle pipeline, manifest validation, asset serving
├── history/         # history recording, statistics
├── notification/    # notifications, SSE stream
└── admin/           # admin API, review queue, badges
```

**This list is the milestone decomposition, not a new taxonomy.** It was derived from the registry's
own items rather than invented, which is why it costs nothing to adopt: each work item already knows
which package it belongs to without anyone deciding.

The sibling repositories take matching roots — `io.turnbase.gamehost`, `io.turnbase.grpc`, and the
already-fixed `io.turnbase.gdk` of `backend-gdk-api.md` §2.

### 2. Layer *inside* a feature, never across features

Within `room/` the familiar layering still applies — controller, service, repository. What changes is
that the layer is subordinate to the feature, not the other way round. There is no top-level
`controller` package containing every controller in the system.

The reason is navigational as much as architectural: an agent given "IMP-M2-05 — Join, teams,
readiness" and a read-list can open one directory and see the whole feature. Under layered packaging
the same work is spread across four directories that each also contain forty unrelated files.

### 3. Cross-feature access goes through a feature's public API, and Spring Modulith verifies it

Each feature package's top level is its API. Everything under an `internal` subpackage is private to
that feature. **`spring-modulith` enforces this with a single test**:

```java
@Test
void verifiesModularStructure() {
  ApplicationModules.of(TurnBaseApplication.class).verify();
}
```

That test fails the build when one feature reaches into another's internals, or when two features
form a dependency cycle. It is the whole enforcement mechanism — no custom ArchUnit rules, no
review checklist, no convention anyone has to remember.

**Why enforce rather than document:** an unenforced layout convention erodes silently, and this
project's code is written largely by agents that read one work item at a time and cannot see the
boundary they are about to cross. A boundary that is a build error is a boundary; a boundary that is
a sentence in a conventions document is a preference.

### 4. Events for decoupling are permitted but not required at M0

Spring Modulith's application events are the idiomatic way to break a cycle the verifier rejects —
history recording reacting to a game ending rather than being called by it. The MVP does not adopt
event-driven decomposition as a general style; events are the escape hatch for a specific cycle,
used when one appears, and the durable-work tables of `data-model.md` §4 remain the mechanism for
anything that must survive a restart. Modulith's event publication registry is **not** adopted —
`session_teardown` and `game_input_outbox` already do that job, and ADR-0010 decided how.

### 5. Adopted at skeleton time, not retrofitted

`spring-modulith-starter-core` and the verification test land in **IMP-M0-03**, before any feature
exists. Retrofitting it after thirty items would mean fixing every accumulated violation at once, in
one large change, at the point where the boundaries have already stopped being real.

## Consequences

### What gets easier

- **Every work item knows its package without asking.** The registry's milestone map is the package
  list, so the most frequently made small decision in Phase 1 stops being a decision.
- **The modular-monolith claim becomes demonstrable.** `CLAUDE.md` states game-agnostic core and
  clean boundaries as architecture principles. A passing `ApplicationModules.verify()` is evidence;
  a package diagram is an assertion.
- **Extraction stays cheap.** ADR-0012 draws repository boundaries where a component can be
  independently deployed. If a feature ever needs to become a service, a verified module boundary is
  most of the work already done.
- **Modulith generates module documentation** (C4 component diagrams, a module canvas) from the code
  rather than from a document that drifts.

### What gets harder, or riskier

- **A legitimate cross-feature call now needs a deliberate API.** `room/` needing catalog data
  exposes a method on `catalog`'s public surface instead of injecting its repository. This is the
  point of the ADR, and it will feel like friction the first three times.
- **One more dependency**, and one more failure mode an agent must be able to read: a Modulith
  verification failure names the violating type but reads unlike a test assertion. `conventions.md`
  carries the interpretation.
- **Cycles surface late.** History↔game and notification↔room are the plausible ones. The fix is §4's
  events, and finding them at M5 with the verifier is much cheaper than finding them never.

### Cascade

| Document | Change |
|---|---|
| `docs/implementation/conventions.md` | New. Carries §1's package list, the `internal` rule, and the tooling that enforces it |
| `registry.md` | `IMP-M0-03` gains the dependency and the verification test in its *Done when*; `conventions.md` joins the read-list of every Java item |
| `observability.md` | The log sample's `logger` corrected to `io.turnbase.platform.room.RoomService` |
| `CLAUDE.md` | Architecture principles gain the module-boundary rule |

### Why this is an ADR

It constrains every future change to the largest repository in the project, and it is independently
revisitable — dropping Modulith while keeping package-by-feature is a coherent future decision, and
so is the reverse. It also resolves a question the corpus had never asked out loud, which is exactly
the kind of thing that gets re-litigated by someone who finds forty features in one flat package and
assumes nobody thought about it.
