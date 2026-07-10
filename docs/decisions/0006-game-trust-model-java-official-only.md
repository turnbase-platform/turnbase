# ADR-0006: Game trust model — Java backends are official-only for the MVP

- **Status:** Accepted
- **Date:** 2026-07-11
- **Deciders:** Project owner
- **Source:** Espresso feasibility spike ([results](../reviews/2026-07-02-mvp-readiness/espresso-spike-results.md)), ADR-0005, MVP Readiness Review 2026-07-02 — blocker GAME-I1

## Context

The Espresso spike (ADR-0005) established that **in-JVM Espresso on GraalVM CE cannot isolate
untrusted Java**: filesystem and network access leak straight to the host OS, and the only
per-context heap cap is Oracle-GraalVM-only. Adversarial-grade isolation of Java requires the
**OS/container layer** (hardened container + gVisor), which ADR-0001 defers past the MVP.

Truffle *does* securely sandbox native-free guest languages — **JavaScript (GraalJS)** fully on CE,
and **Python (GraalPy)** largely so — because those runtimes have no native syscall path. But this
is a *runtime capability*, not a *platform capability*: TurnBase has **no JS/Python backend GDK, no
Game Host embedding for them, and no contract** for non-Java game logic. Those are future work.

The platform and Game Host are written in Java on GraalVM. The intent is to host JS and Python games
**later**, via GraalVM guest runtimes (GraalJS/GraalPy) sitting behind the **same platform contract**
(the Orchestration↔Game Host gRPC protocol), through a runtime abstraction — not a single Java-only
host.

Consequently, **untrusted game backends of any language are not shippable for the MVP**: untrusted
Java is unsafe on CE without the deferred container hardening, and untrusted JS/Python has no runtime
or GDK yet.

## Decision

1. **The MVP hosts official, first-party Java games only.** Community-uploaded and privately-hosted
   game **backends** are disabled for the MVP — in any language. (This concerns *executing untrusted
   backend code*, not publishing or catalog UX.)
2. **Trust is assigned per runtime/language, matching isolation capability:**
   - **Java (Espresso):** trusted-only. Runs first-party code the platform team authors and reviews.
     Never exposed to an untrusted upload path for the MVP.
   - **JS (GraalJS) / Python (GraalPy):** *future* untrusted-capable runtimes (Truffle sandboxes them
     on CE), gated on building their GDK + Game Host runtime. **Not in the MVP.**
3. **Because official Java code is trusted, the MVP Game Host does not need adversarial isolation** —
   it needs *resource limits* for robustness against buggy (not hostile) games:
   - wall-clock handler timeouts via `Context.interrupt` / `close(true)` (verified on CE), and
   - a container/cgroup memory limit.

   Filesystem/network denial is applied as ordinary **defense-in-depth hygiene**, not as a
   hostile-code boundary. This resolves the ADR-0005 FR-CTX enforcement question **for the MVP**.
4. **Untrusted backend hosting returns post-MVP via two independent paths, each its own effort:**
   - **Untrusted Java:** the hardened-container + gVisor path (ADR-0001 production hardening).
     A "reviewed community Java" tier may be introduced as an intermediate step, but human review is
     **not** a substitute for the container.
   - **Untrusted JS/Python:** new backend GDKs + GraalJS/GraalPy runtimes behind the same platform
     contract, leveraging Truffle's CE sandbox.
5. **Forward architecture — the Game Host is language-agnostic at the contract seam.** The
   Orchestration↔Game Host gRPC contract and the Game Host structure must not assume a single guest
   language. A runtime abstraction selects the guest runtime (Espresso / GraalJS / GraalPy) per game,
   driven by a manifest `runtime` field, with a **per-runtime trust policy** governing whether that
   runtime may host untrusted code. The MVP implements **only the Espresso/Java runtime**, but the
   contract must be shaped now so adding a runtime later is not a breaking change.

## Consequences

- **Positive:**
  - Removes the highest-uncertainty work — the adversarial untrusted-Java sandbox, gVisor, and the
    untrusted-backend upload pipeline — from the MVP critical path. Consistent with ADR-0001.
  - Simplifies the (still-unwritten) Game Host internals spec to **timeouts + container memory
    limits**, not per-context adversarial enforcement.
  - Likely removes the untrusted **bundle/upload-pipeline spec** from MVP scope: with no untrusted
    backend, there is no untrusted backend upload path to build (a frontend/official deployment path
    still exists).
  - Preserves the full architecture showcase — Espresso, the GDK, the gRPC contract, and the manifest
    are all built and exercised by the official games.
  - Keeps the multi-language roadmap coherent and the contract language-agnostic from day one.
- **Negative / deferred:**
  - The MVP does **not** demonstrate untrusted-code sandboxing — a stated platform pillar
    (user-uploaded games) — deferring that capability and its security showcase to post-MVP.
  - A per-runtime trust policy and a manifest `runtime` field must be designed **now**, while only
    one runtime exists, to avoid a later contract break.
  - "Official-only" needs a concrete **enforcement point**: Java game backends must enter only
    through the trusted first-party deployment path, never an upload path.

## Affected documents

- `docs/requirements/platform-architecture.md` — FR-CTX enforcement reframed to the trusted-code
  model for the MVP; NFR-SEC-* scoping note; add runtime-abstraction + per-runtime trust concept;
  OQ-002's process/container fallback is now a **post-MVP untrusted-Java** concern, not an MVP one.
- `docs/requirements/game-contracts.md` — CON-001 correction (CE sandbox limitations per the spike);
  add the trust-model constraint; language-agnostic host framing.
- `docs/requirements/game-development-experience.md` — official-only Java for the MVP; JS/Python GDKs
  are post-MVP.
- `docs/specs/manifest/manifest-schema.md` — `runtime` field + per-runtime trust policy; reject
  non-official Java backends on the upload path.
- Future **upload-pipeline spec** / `docs/specs/api-design/file-uploads.md` — untrusted backend
  upload disabled for the MVP; scope to frontend/official assets.
- `ADR-0005` — this ADR consumes the spike outcome and resolves the FR-CTX enforcement direction for
  the MVP.
- Review INDEX — resolves GAME-I1's direction for MVP scope.
