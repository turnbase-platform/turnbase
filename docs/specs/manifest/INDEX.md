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
consistency). Validation that requires the archive contents or platform state
(path existence, entry-class checks, GDK-class conflicts, version ordering,
size limits) belongs to the bundle / upload-pipeline spec.

## Files

| File | Topic |
|------|-------|
| [manifest.schema.json](manifest.schema.json) | Normative JSON Schema (Draft 2020-12) for `manifest.json`. Consumed by both the platform upload validator and the local test harness. |
| [manifest-schema.md](manifest-schema.md) | Field semantics, supplementary validation rules the schema cannot express, the lenient unknown-key policy, the error model, and requirements traceability. |

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
  failures in one response (FR-UPLOAD-008).
