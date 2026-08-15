# Manifest Schema Specifications

Implementation-level design of the **game manifest** — the `manifest.json` at the
root of every TurnBase game bundle. The manifest is the single source of truth
for a game's metadata, capabilities, entry points, team structure, and
host-configurable parameters (CON-005). Realizes
`docs/requirements/game-development-experience.md` FR-MANIFEST-001 through
FR-MANIFEST-009.

## Scope

The manifest document's shape and the validation performed on it **in
isolation** (types, formats, ranges, enums, required fields, cross-field
consistency) — plus the **bundle that carries it**: the archive format, the
upload validation pipeline, and publication of the unpacked tree. The split
between the two is deliberate: validation that requires only the manifest
document is [manifest-schema.md](manifest-schema.md); validation that requires
the archive contents or platform state (path existence, entry-class checks,
GDK-class conflicts, version ordering, GDK API range, size limits) is
[bundle-format.md](bundle-format.md).

## Files

| File | Topic |
|------|-------|
| [manifest.schema.json](manifest.schema.json) | Normative JSON Schema (Draft 2020-12) for `manifest.json`. Consumed by both the platform upload validator and the local test harness. |
| [manifest-schema.md](manifest-schema.md) | Field semantics, supplementary validation rules the schema cannot express, the lenient unknown-key policy, the error model, and requirements traceability. |
| [bundle-format.md](bundle-format.md) | The ZIP bundle and its upload pipeline: archive layout and the security rules a ZIP reader must enforce, the ordered validation stages and their `check` identifiers, the static serializability analysis (GRMP-F4), unpacking and atomic publication into the `/g/{gameId}/{version}/` tree, `gdkApiVersion` compatibility (GAME-I7), and slot expiry, retry and storage cleanup. |

## Key Decisions

- **Authoritative artifact is a JSON Schema file**, not prose — one contract
  shared by the platform validator and the test harness (FR-HARNESS-002),
  eliminating drift.
- **`manifestVersion`** is a distinct schema-revision field (currently `"1"`),
  independent of `gdkApiVersion`, so the manifest structure can evolve on its own
  cadence; unknown versions are rejected.
- **Two-layer validation:** declarative JSON Schema, plus supplementary
  programmatic checks for rules Draft 2020-12 can't express (range ordering,
  default-in-range / default-in-options, parameter-key uniqueness, conditional
  team `name`).
- **Lenient on unknown keys:** unrecognized keys are not rejected but surfaced as
  non-fatal warnings, so typos are visible without failing the upload.
- **`backend` is runtime-agnostic** (`path` + `entryPoint`) so the archive
  structure stays language-independent (FR-BUNDLE-007); `entryPoint` is the FQCN
  under `runtime: "jvm"`.
- **Errors reuse the bundle-validation shape** from `api-design/error-handling.md`
  (`422 business-rule-violation` with a `{ check, message }` array), reporting all
  failures in one response (FR-UPLOAD-008) — but only synchronous slot-request
  failures are a `422`; asynchronous validation results are the *state of a
  resource*, returned as `200` with `errors`/`warnings` (bundle-format.md §3.4).
- **One report, but with barriers.** FR-UPLOAD-008's "all failures at once" is
  collected per phase; a phase whose output the next phase consumes (archive →
  manifest → declared paths → JAR) stops the pipeline rather than inventing
  errors it could not compute (bundle-format.md §3.3).
- **NFR-UPLOAD-002 stands: no game code is executed at upload.** GRMP-F4's
  serialization round trip is split — static serializability analysis of the
  state type at upload (which catches the exact `-parameters` defect GRMP hit),
  the *executing* round trip in the test harness, both through the shared
  serialization engine (bundle-format.md §4).
- **Publication is atomic through the version row, not a rename.** Object stores
  have no atomic directory rename; the unpacked tree becomes reachable only when
  the version reaches `ACTIVE`, so a half-unpacked tree can never serve
  (bundle-format.md §5.3).
- **The published tree is a subset of the archive.** A whole-archive unpack would
  serve the backend JAR from the unauthenticated games origin at a URL derivable
  from the public catalog; a deny list excludes it, the manifest and the info doc
  (bundle-format.md §5.2).
- **A moving GDK compatibility range never mutates catalog state.** Orphaned
  versions are reported at startup and blocked at room creation; deactivating
  them would make a platform rollback stop working (bundle-format.md §6.3).
