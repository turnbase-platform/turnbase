# ADR-0005: Game sandbox — Espresso spike gates the Game Host spec

- **Status:** Accepted
- **Date:** 2026-07-10
- **Deciders:** Project owner
- **Source:** MVP Readiness Review 2026-07-02 — blocker GAME-I1, strategic decision #6, and #6 (startup NFR deferral)

## Context

The Game Host runs untrusted third-party game code (Java) inside GraalVM. The plan is to sandbox
each game in a Truffle/Espresso guest context that can be locked down (per-context heap cap, no
filesystem/network, forced termination). Two assumptions are unverified on the **free GraalVM
Community Edition for JDK 21** the project targets (GraalVM CE 21 — the version installed;
note there is no CE build for JDK 23 in SDKMAN, and the "CE 23" label in the tech stack is the
deprecated GraalVM product-version scheme and should be read as "GraalVM CE for JDK 21"):

1. Some strong isolation controls (per-context heap caps, the strongest sandbox tiers) may be
   **Oracle-GraalVM-only**, not available on CE.
2. **Espresso context startup** (a guest JVM inside the host JVM) may exceed the current 3s/5s
   startup *Musts*.

The Game Host internals spec cannot name a concrete isolation mechanism until these are tested.
`platform-architecture.md` OQ-002 already documents a **process-isolation** fallback (each game in
its own process/container).

## Decision

1. **Run a small Espresso feasibility spike on GraalVM CE for JDK 21 first**, before freezing FR-CTX
   enforcement design or writing the Game Host internals spec. The spike loads a trivial guest
   game in Espresso and measures/verifies:
   - context startup time,
   - which isolation controls actually work on CE for JDK 21 (heap cap, no FS/network, forced termination).
2. **Keep the OQ-002 process-isolation fallback first-class.** If the spike shows CE Espresso
   (CE for JDK 21) cannot meet the isolation or startup needs, the MVP Game Host uses process/container isolation
   per game instead of in-JVM guest contexts.
3. **Defer the 3s/5s startup NFR Musts to post-MVP** (strategic #6). They are not
   MVP-enforceable and their feasibility depends on the spike outcome.

## Consequences

- **Positive:** avoids speccing against unverified capabilities; de-risks the highest-uncertainty
  area of the platform before committing to a design.
- **Negative:** the Game Host internals spec is blocked on the spike — but this is a short,
  self-contained technical task, not a full spec session.

## Affected documents

- `docs/requirements/platform-architecture.md` — startup NFRs → post-MVP; OQ-002 fallback stays
  first-class; add a note that the Espresso spike gates FR-CTX enforcement design.
- Future **Game Host internals spec** — blocked until spike results are in; mechanism chosen from
  the spike.
- Review INDEX — resolves GAME-I1 direction, strategic #6.
