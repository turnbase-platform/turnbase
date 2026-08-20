# ADR-0015: Static analysis at skeleton time — Error Prone and NullAway

- **Status:** Accepted
- **Date:** 2026-08-20
- **Deciders:** Project owner
- **Relates to:** [ADR-0014](0014-modular-monolith-spring-modulith.md) — same reasoning about *when* a
  build-time check must be adopted, applied to a different kind of check

## Context

After the 2026-08-20 conventions round, the Java build enforces formatting (Spotless), module
boundaries (Spring Modulith), coverage (JaCoCo) and public-type Javadoc (Checkstyle, in the SDK).

**Nothing looks for defects.** Every one of those tools checks a property of the *shape* of the code.
None of them would notice `==` on two boxed `Long`s, a format string that disagrees with its
arguments, an ignored return value from a method whose entire purpose is its return value, or a
`.get()` on an `Optional` that can be empty. Those survive review reliably, because review is looking
at whether the logic is right, not at whether the language is behaving the way it reads.

Two things make this worth deciding now rather than noting as a gap.

**The retrofit problem, which is ADR-0014's argument again.** A linter added to an empty skeleton
costs one build-configuration block. The same linter added at work item forty produces two hundred
findings in a single change that nobody wants to review, so it gets configured to warn instead of
fail, and a warning nobody must act on is not a check. There is no third option where it is adopted
later and still works.

**Nullness is load-bearing in this data model specifically.** This is not a general preference for
null-safety. `room_participant` carries `left_at` and `lost_announced_at`, and the deferred-tail scan
of `room-lifecycle.md` §5.1 duty 2 is driven by the partial index
`WHERE left_at IS NOT NULL AND lost_announced_at IS NULL`. Whether a value is null *is* the state
machine. `closed_reason`, `owner_user_id` (whose nullness is tied to `badge='OFFICIAL'` by a check
constraint) and the notification subject foreign key that marks actionability are the same shape. A
codebase where nullness carries this much meaning and is invisible to the compiler is one where the
meaning is maintained by attention.

## Decision

### 1. Error Prone, at `ERROR`, in every Java repository

[Error Prone](https://errorprone.info/) runs as a compiler plugin. Its default `ERROR`-severity bug
patterns stay at `ERROR`; the build fails on them.

Chosen over the alternatives because it analyses the AST during compilation rather than the bytecode
afterwards — it is fast enough to run on every build, and its false-positive rate is low enough that
the findings are worth reading. That second property is the one that matters: **a linter people mute
is worse than no linter**, because muting it is a decision made once and inherited silently forever.

### 2. NullAway, with JSpecify `@NullMarked` at the package level

Every package is `@NullMarked`: references are non-null unless annotated `@Nullable`. NullAway then
fails the build on a dereference it cannot prove safe, and on passing a nullable value where a
non-null one is required.

`@NullMarked` at the package level rather than annotation-by-annotation is the whole point. The
default has to be non-null, because the alternative is that unannotated means unknown, and unknown
means unchecked — which is where the codebase already is.

**This changes how every method signature is written**, which is why it is an ADR and not a line in
`conventions.md`. A nullable return becomes a visible part of the contract rather than something the
caller discovers.

The SDK is annotated too. It is a published artifact that third parties compile against, and
nullability in the published API is documentation their IDE can read.

### 3. Rejected: SpotBugs, PMD, ArchUnit

- **SpotBugs** analyses bytecode, is slower, and has a materially higher false-positive rate. The
  marginal findings over Error Prone do not pay for the noise.
- **PMD** overlaps Checkstyle and is noisy at its useful rulesets.
- **ArchUnit** would enforce the module boundaries that `ApplicationModules.verify()` already
  enforces. Two mechanisms for one invariant means two places to update and one of them will rot.

### 4. Dependency and image scanning are configured at repository initialisation

`platform-operations.md` FR-CICD-010 already requires Dependabot and Trivy. No configuration file
exists. `dependabot.yml` and the Trivy workflow step land with each repository's skeleton, not later:
**critical fails the build, lower severities report and do not block** — the distinction the
requirement already argues for, because a pipeline that blocks on every advisory stops being run.

### 5. A check that fires is fixed or disabled with a stated reason — never muted globally

When a new check finds something in existing code, the two acceptable responses are to fix it, or to
suppress it **at the site** with `@SuppressWarnings("CheckName")` and a comment saying why. Lowering
a check's severity build-wide is not one of them: it is a decision made once, invisible afterwards,
that quietly turns off a class of finding for the whole project.

## Consequences

### What gets easier

- **A class of defect stops reaching review.** Reviewer attention moves to whether the logic is
  right, which is the only part a tool cannot check.
- **Nullness becomes part of the type**, so the several places where null encodes state are readable
  from the signature instead of from the schema document.
- **The SDK's published contract improves for free** — third-party developers get nullability in
  their IDE without us writing more Javadoc.

### What gets harder, or riskier

- **Build configuration friction, and it is the confusing kind.** Error Prone needs
  `-XDcompilePolicy=simple` and `--should-stop=ifError=FLOW`, plus `--add-exports` flags for
  `jdk.compiler` on modern JDKs — the same family of setup as google-java-format's, and the first
  failure reads like a broken toolchain rather than a missing flag. `conventions.md` §2 carries the
  interpretation; `IMP-M0-03` is where it is paid.
- **NullAway is the one that will feel like friction**, because it surfaces genuinely ambiguous cases
  the code previously left implicit. That is the finding, not the false positive — but it will not
  feel that way at the time.
- **Third-party and generated code.** Generated gRPC stubs, and Spring's own injection points, need
  exclusion from NullAway's scope. Getting that wrong produces noise on code nobody wrote, which is
  the fastest route to muting the tool.

### Cascade

| Document | Change |
|---|---|
| `docs/implementation/conventions.md` | §2 gains the Java analysis stack and the ESLint ruleset; §6's build floor |
| `registry.md` | `IMP-M0-02/03/04/05` gain the tooling in their *Done when*; `IMP-M0-11` gains Dependabot and Trivy |

### Why this is an ADR

NullAway changes the contract of every method signature in the project — that is a constraint on all
future code, not a build setting. It is also, like ADR-0014, a decision whose cost is near zero today
and prohibitive in three months, which is exactly the kind that gets deferred by default unless
somebody writes down that it was considered.
