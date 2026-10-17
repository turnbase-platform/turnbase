# Architecture Decision Records

Durable record of significant, cross-cutting decisions for the TurnBase platform. Each ADR captures the context, the decision taken, its consequences, and the documents it affects. ADRs are the authoritative source once accepted; requirements and specs should link back to the relevant ADR rather than restating the rationale.

Format: one file per decision, numbered sequentially (`NNNN-slug.md`). Status is one of `Proposed`, `Accepted`, `Superseded`, `Deprecated`.

## Records

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-local-first-mvp-platform.md) | Local-first MVP platform (Docker Desktop Kubernetes) | Accepted |
| [0002](0002-websocket-room-affinity.md) | WebSocket scaling via room affinity | Accepted |
| [0003](0003-mvp-availability-target.md) | MVP availability target of 99% | Accepted |
| [0004](0004-account-erasure-pseudonymization.md) | Account erasure via history pseudonymization | Accepted |
| [0005](0005-game-sandbox-espresso-spike.md) | Game sandbox — Espresso spike gates the Game Host spec | Accepted |
| [0006](0006-game-trust-model-java-official-only.md) | Game trust model — Java backends are official-only for the MVP | Accepted |
| [0007](0007-game-frontend-separate-domain.md) | Game frontends are served from a separate registrable domain | Accepted |
| [0008](0008-room-ownership-lifecycle.md) | Room ownership is a lease-gated claim, not a lifetime assignment | Accepted |
| [0009](0009-grace-deadline-durability.md) | Grace deadlines are persisted absolute timestamps, fired by a sweep | Accepted |
| [0010](0010-session-teardown-ordering.md) | Session teardown is a durable to-do, not an ordering | Accepted |
| [0011](0011-schema-migrations.md) | Schema migrations — Flyway, forward-only, backward-compatible | Accepted |
| [0012](0012-repo-strategy-polyrepo-submodules.md) | Repository strategy — polyrepo under an organisation, with submodules | Accepted |
| [0013](0013-astryx-design-system.md) | Astryx supersedes the in-house design system | Accepted |
| [0014](0014-modular-monolith-spring-modulith.md) | The Platform Monolith is modular by feature, and Spring Modulith enforces it | Accepted |
| [0015](0015-static-analysis-error-prone-nullaway.md) | Static analysis at skeleton time — Error Prone and NullAway | Accepted |
| [0016](0016-spring-boot-4-migration.md) | Both Spring Boot services move to Spring Boot 4.1 | Accepted |
| [0017](0017-turnbase-visual-identity.md) | The platform takes a TurnBase visual identity on top of Astryx (amends 0013 §4) | Accepted |
| [0018](0018-game-start-resilience.md) | Starting a game survives a cold, restarting or wedged Game Host, and says what it is doing | Accepted |

## Provenance

ADRs 0001–0005 ratify the six "Strategic decisions needing the project owner" from the
[MVP Readiness Review 2026-07-02](../reviews/2026-07-02-mvp-readiness/INDEX.md), taken in an
owner decision session on 2026-07-10.

ADR-0006 follows from the Espresso feasibility spike run on 2026-07-10/11 (ADR-0005), which showed
in-JVM Espresso on GraalVM CE cannot isolate untrusted Java; the owner chose to scope the MVP to
official-only Java backends and defer untrusted backends (hardened-container Java, plus JS/Python
runtimes) to post-MVP.

ADR-0007 resolves review blocker GAME-B3 (2026-07-12). It is recorded as an ADR rather than left in
the spec because it **overturns the review's own suggested resolution** on a security argument, and
because it carries a real-world cost (a second registered domain in production).

ADR-0008–0010 close the room-lifecycle durability cluster (GRMP lessons F1, F2 and F3) on 2026-08-09.
They are three ADRs rather than one because they are independently revisitable — a future live
migration would replace 0008 without touching 0009 or 0010 — but they were taken together, and each
depends on the other two: the sweep of 0009 needs 0008's claim before it may broadcast, and 0010's
re-drive is a duty of the same sweep. Two of the three also fix defects that were already latent in
the specs: a rolling deploy would have deleted every Lobby room, and an adopting instance would have
re-issued event versions that clients discard silently.

ADR-0013 reverses a decision recorded one day earlier. `design-system.md` was written on 2026-08-16
to close review blocker IR-23 — our own tokens, our own CSS Modules convention, our own seventeen
components — and on 2026-08-17 the component half of it was replaced by Astryx, Meta's open-source
design system. It is an ADR for two reasons: a future reader finding `design-system.md` would
otherwise take the superseded design as current, and it amends `platform-ui-library.md` CON-002 for
the second time in two days. It also changes the platform's visual direction, from neon-on-near-black
with frosted glass to Astryx's muted `theme-neutral`.

ADR-0012 is the oldest decision here and the last to be filed. It was taken at inception and lived
as a loose design note outside the ADR directory, unreferenced by anything, while `CLAUDE.md` carried
its conclusion — the five-repo table and the one-line submodule rule — without its argument. The
argument is the part worth keeping: why not a monorepo (the SDK needs a public artifact with no
internal dependencies leaking transitively), and why the proto lives in `turnbase-common` rather than
a `turnbase-contracts` repo of its own.

ADR-0014 and ADR-0015 were both taken on 2026-08-20, during and just after the pre-implementation
readiness review, alongside the build conventions that became
[`../implementation/conventions.md`](../implementation/conventions.md). Most of that round is *not*
recorded here — Spotless, JaCoCo, test suffixes and cross-repo pinning are replaceable build tooling
and live in `conventions.md`. These two are ADRs because each constrains all future code rather than
configuring the build: 0014 fixes the internal structure of the repository that holds forty of the 59
work items, and 0015's NullAway changes the contract of every method signature in the project.

They share an argument, and it is the reason both were taken before any code existed: **a build-time
check that is cheap to adopt at skeleton time is prohibitive to adopt at work item forty**, because
the retrofit arrives as one unreviewable change and gets downgraded to a warning instead. There is no
later point at which either decision is still available on the same terms. The review also found that
the corpus's sole evidence of the monolith's package root was an incidental logger name in a JSON log
sample.

ADR-0016 was taken on 2026-10-10 when two CRITICAL `spring-webmvc` CVEs with no fix on the Spring
6.2 line turned `turnbase-platform`'s Trivy gate red (`IMP-GATE-97`). Upgrading was preferred to a
waiver because the 3.5 line will not receive the fix at all. It is executed as milestone M11, and
it carries the one recorded exception to ADR-0012's same-session branch rule.

ADR-0017 was taken on 2026-10-11, after the clickable prototype of the intended look was approved. It
reverses ADR-0013 §4 (the muted `theme-neutral` aesthetic) while keeping the rest of 0013: Astryx still
owns components. The part worth reading is §2, *Delivery* — a built theme, own tokens in plain CSS,
self-hosted fonts and colours defined in one table — because the prototype itself broke the shell CSP and the
raw-value rules, and the look would not have shipped as prototyped.

ADR-0011 closes OPS-3, open since the review and never addressed: the corpus defined roughly thirty
tables while naming no migration tool at all. It is recorded as an ADR rather than as a spec section
because two of its rules constrain every future change — forward-only, and backward-compatible with
the previous application version — and because the second is what makes the image rollback the CI/CD
pipeline already promises (FR-CICD-008) true rather than nominal.

ADR-0018 was taken on 2026-10-17 after a freshly set-up stack refused every game start with a generic
error until the Game Host was restarted by hand. The part worth reading is §2: a sizeable share of cold
boots stall the whole JVM inside Truffle's native interface, so no code inside it can notice, and a
separate process has to kill it.
