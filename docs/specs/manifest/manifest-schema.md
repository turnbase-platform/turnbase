# Game Manifest Schema

Design of the `manifest.json` document that sits at the root of every TurnBase
game bundle. The manifest is the **single source of truth** for a game's
metadata, capabilities, entry points, team structure, and host-configurable
parameters (CON-005). This spec defines its structure, field semantics, and the
validation performed on the manifest **document in isolation**.

Realizes `docs/requirements/game-development-experience.md` FR-MANIFEST-001
through FR-MANIFEST-009.

## Artifacts

| File | Role |
|------|------|
| [`manifest.schema.json`](manifest.schema.json) | Normative, machine-readable JSON Schema (Draft 2020-12). The contract consumed by both the platform upload validator and the local test harness (FR-HARNESS-002), so the two cannot drift. |
| `manifest-schema.md` (this file) | Intent, field semantics, supplementary validation rules the schema cannot express, the error model, and requirements traceability. |

## Scope

**In scope:** the manifest's shape and the validation of a manifest document on
its own — types, formats, ranges, enumerations, required fields, and cross-field
consistency.

**Out of scope** (owned by the bundle / upload-pipeline spec, which validates the
manifest *against the archive and platform state*):

- Existence of declared `backend.path`, `frontend.entryPoint`, `infoDoc` paths
  within the archive (FR-UPLOAD-003).
- Whether `backend.entryPoint` resolves to a class implementing `TurnBaseGame`
  (FR-UPLOAD-004).
- Absence of GDK API classes in the JAR (FR-UPLOAD-005).
- `version` being strictly higher than the current active version, which needs
  server state (FR-UPLOAD-006, game-catalog.md FR-GAME-009).
- `gdkApiVersion` falling within a platform-supported range (NFR-COMPAT-001).
- Bundle size limits (FR-UPLOAD-007).

---

## Structure

A complete, annotated example:

```json
{
  "manifestVersion": "1",
  "title": "Chess",
  "shortDescription": "Classic two-player strategy on an 8×8 board.",
  "version": "1.0.0",
  "gdkApiVersion": "0.3.0",
  "runtime": "jvm",
  "backend":  { "path": "backend/chess.jar", "entryPoint": "com.example.ChessGame" },
  "frontend": { "entryPoint": "frontend/main.js" },
  "infoDoc": "INFO.md",
  "tags": ["strategy", "board", "classic"],
  "capabilities": { "ai": false, "spectators": true, "midGameJoin": false },
  "teamTemplates": [
    { "name": "White", "size": { "min": 1, "max": 1 }, "count": { "min": 1, "max": 1 } },
    { "name": "Black", "size": { "min": 1, "max": 1 }, "count": { "min": 1, "max": 1 } }
  ],
  "parameters": [
    { "key": "moveTimer", "displayName": "Move timer (s)", "type": "integer",
      "min": 0, "max": 600, "default": 60 }
  ]
}
```

---

## Top-level fields

| Field | Type | Required | Constraints | Notes |
|-------|------|----------|-------------|-------|
| `manifestVersion` | string | Yes | Must equal `"1"` | Schema revision of the manifest document itself, independent of `gdkApiVersion`. Unknown values are rejected (forward-evolution hook). |
| `title` | string | Yes | 1–60 chars | Game display name. (Requirements cap `shortDescription` but not the title; 60 chosen for catalog/detail layout.) |
| `shortDescription` | string | Yes | 1–100 chars | Catalog summary and info-section fallback (FR-MANIFEST-001, game-catalog.md FR-GDET-003). |
| `version` | string | Yes | `^[0-9]+\.[0-9]+\.[0-9]+$` | Game version (FR-GAME-009). Ordering vs. active version is checked by the upload pipeline. |
| `gdkApiVersion` | string | Yes | `^[0-9]+\.[0-9]+\.[0-9]+$` | GDK API the game was built against (FR-GDK-016). Compatibility range check is the platform's job. |
| `runtime` | string (enum) | Yes | `"jvm"` | Determines interpretation of `backend` (FR-BUNDLE-007). Future runtimes extend this enum. Runtime selection is the language-agnostic seam of the platform contract; a **per-runtime trust policy** governs whether a runtime may host untrusted code (ADR-0006). For the MVP, `jvm` is **official-only** — untrusted Java cannot be isolated on GraalVM CE (ADR-0005) — so `runtime: "jvm"` bundles are accepted only via the first-party/official deployment path, not an untrusted upload. Post-MVP untrusted runtimes (`js`, `py`) extend this enum. |
| `backend` | object | Yes | see below | Backend component descriptor. |
| `frontend` | object | Yes | see below | Frontend component descriptor. |
| `infoDoc` | string | No | non-empty | Relative path to a Markdown info/rules doc (FR-MANIFEST-007, FR-BUNDLE-005). |
| `tags` | array<string> | Yes | 1–10 items, each 1–24 chars | Free-form tags (FR-MANIFEST-006, FR-GAME-003). |
| `capabilities` | object | Yes | see below | Capability flags (FR-MANIFEST-003). |
| `teamTemplates` | array<object> | Yes | ≥ 1 item | Team structure (FR-MANIFEST-002). |
| `parameters` | array<object> | No | — | Host-configurable parameters (FR-MANIFEST-004). |

### `backend`

Runtime-agnostic shape so the archive structure stays language-independent
(FR-BUNDLE-007).

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `path` | string | Yes | Relative path to the backend artifact in the archive. For `jvm`, the fat JAR (FR-BUNDLE-003). |
| `entryPoint` | string | Yes | Runtime-interpreted entry identifier. For `jvm`, the fully qualified class name implementing `TurnBaseGame`, e.g. `com.example.ChessGame` (FR-MANIFEST-008). |

### `frontend`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `entryPoint` | string | Yes | Relative path to the JS entry file, e.g. `frontend/main.js` (FR-MANIFEST-009). The bundle ships build output only — no HTML; the platform shell injects the FE GDK (CON-006). |

### `capabilities`

All three flags are required and boolean (FR-MANIFEST-003); they are independent
of one another.

| Field | Meaning |
|-------|---------|
| `ai` | Game supports AI (bot) players. **Must be `false` in v1** — see below. |
| `spectators` | Game supports the spectator role. |
| `midGameJoin` | Players may join a session already in progress (game-rooms.md FR-JOIN-006 / FR-TEAM-011). |

**`capabilities.ai: true` is rejected while `game-contracts.md` OQ-002 is open.** A supplementary
check fails the bundle with `check: "manifest.capabilities.ai"` and a message naming the deferral. The
flag stays in the schema — its shape is settled and the platform surface that reads it already exists
(`../api-design/room-websocket.md`'s `aiPlayers`, always empty in v1) — but there is no AI execution
environment (`platform-architecture.md` *Out of Scope*), so a game that declared support would be
accepted, listed, and then unable to seat the AI the host asked for. Rejecting at validation is the
only point where the developer learns this before their players do.

### `teamTemplates`

Each entry mirrors `game-rooms.md` FR-TEAM (its prose table is the authority for
runtime team behaviour).

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | Conditional | 1–40 chars. **Required when `teamTemplates` has more than one entry** (supplementary check); defaults to `"Team"` for a single template. |
| `size.min` | integer | Yes | ≥ 1 |
| `size.max` | integer | Yes | ≥ 1; **≥ `size.min`** (supplementary check) |
| `count.min` | integer | Yes | ≥ 1 |
| `count.max` | integer | Yes | ≥ 1; **≥ `count.min`** (supplementary check) |

### `parameters`

Each entry declares a host-configurable parameter. The `type` selects which
additional fields apply (FR-MANIFEST-005). The accessor set in
`gdk-api/backend-gdk-api.md §5` (`GameParameters`) is the runtime counterpart of
these types.

| `type` | Required type-specific fields | `default` type | Notes |
|--------|-------------------------------|----------------|-------|
| `integer` | `min`, `max` (integers) | integer | `min ≤ default ≤ max` (supplementary check). |
| `decimal` | `min`, `max` (numbers) | number | `min ≤ default ≤ max` (supplementary check). |
| `boolean` | — | boolean | — |
| `string` | `maxLength` (optional, ≥ 1) | string | If `maxLength` present, `default` length ≤ `maxLength` (supplementary check). |
| `enum` | `options` (non-empty array of strings) | string | `default` must be one of `options`; `options` must be unique (supplementary checks). |

Common fields on every parameter:

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `key` | string | Yes | `^[a-zA-Z][a-zA-Z0-9_]*$`, ≤ 40 chars; **unique across the array** (supplementary check). Used by `GameParameters` accessors. |
| `displayName` | string | Yes | 1–60 chars. |
| `type` | string (enum) | Yes | One of the five types above. |
| `default` | per type | Yes | Every parameter declares a default, so `GameParameters` getters never return absent (see backend GDK spec §5). |

---

## Validation

Validation has two layers. Both run during upload (FR-UPLOAD-002) and in the
test harness (FR-HARNESS-002); together they either accept the manifest or
produce a complete list of failures.

### Layer 1 — JSON Schema

`manifest.schema.json` (Draft 2020-12) covers everything expressible
declaratively: required fields, primitive types, string patterns
(`version`, `gdkApiVersion`, parameter `key`), length and item bounds, numeric
minimums, enumerations (`runtime`, parameter `type`), and the per-`type`
parameter field requirements via `if`/`then`.

### Layer 2 — Supplementary programmatic checks

Rules JSON Schema (Draft 2020-12) cannot cleanly express. The validator runs all
of them and collects every failure:

| Check | Rule |
|-------|------|
| `teamTemplates[i].size` | `size.max ≥ size.min` |
| `teamTemplates[i].count` | `count.max ≥ count.min` |
| `teamTemplates[i].name` | `name` present on every template when `teamTemplates.length > 1` |
| `parameters[i].default` (integer/decimal) | `min ≤ default ≤ max` |
| `parameters[i].default` (string) | `default` length ≤ `maxLength`, when `maxLength` declared |
| `parameters[i].default` (enum) | `default ∈ options` |
| `parameters[i].options` (enum) | options are unique |
| `parameters` | `key` values are unique across the array |

### Unknown keys (lenient)

Keys not defined by this schema are **not** rejected. The validator emits a
**non-fatal warning** for each unrecognized key (identifying its location) so
typos such as `tag` instead of `tags`, or `capabilites`, surface to the
developer without failing the upload. Warnings are returned alongside a
successful validation result and rendered by the upload UI and the test harness.

### Error model

Fatal validation failures use the `{ "check": <id>, "message": <human-readable> }` entry shape defined
in [`api-design/error-handling.md`](../api-design/error-handling.md). **How they are delivered depends
on when they are detected, and manifest validation is almost always the late case.**

- **Phase A — the slot request.** `POST /api/games/{gameId}/versions` validates what it can from the
  declared metadata alone. Those failures are a synchronous `422 business-rule-violation` whose
  `instance` names that path.
- **Phases B–G — everything that needs the bundle bytes, which is all manifest validation.** The
  manifest lives *inside* the uploaded archive, so it cannot be read until after `confirm`, which has
  already returned `202 Accepted`. These failures are **not an HTTP error at all**: they are the state
  of a resource that was successfully created. `GET /api/games/{gameId}/versions/{uploadId}` returns
  `200` with `status: "FAILED"` and the `errors` and `warnings` arrays below.

The full phase model and the reasoning are in
[`bundle-format.md`](bundle-format.md) §3.4, which is authoritative; this section states the
consequence for manifest checks specifically. All Layer 1 and Layer 2 failures are still reported
together in one array (FR-UPLOAD-008) — one report format, two carriers.

**Do not return a `422` from the `GET`.** The request was fine and the resource was found; a client
that treats 4xx as "retry the request differently" will loop.

`check` identifiers use dotted/indexed paths into the manifest, consistent with
the existing examples (`manifest.version`, `backend.gdkClasses`).

A Phase A failure — synchronous, on the slot request:

```json
{
  "type": "https://turnbase.io/errors/business-rule-violation",
  "title": "Bundle Validation Failed",
  "status": 422,
  "detail": "The uploaded bundle failed validation.",
  "errors": [
    { "check": "manifest.shortDescription", "message": "shortDescription exceeds 100 characters (was 142)." },
    { "check": "manifest.teamTemplates[1].name", "message": "name is required when more than one team template is declared." },
    { "check": "manifest.parameters[0].default", "message": "default 700 is greater than max 600." }
  ]
}
```

A manifest failure — the version resource, fetched after the `202`:

```json
{
  "uploadId": "550e8400-e29b-41d4-a716-446655440000",
  "version": "1.2.0",
  "status": "FAILED",
  "createdAt": "2026-06-11T13:00:00Z",
  "errors": [
    { "check": "manifest.shortDescription", "message": "shortDescription exceeds 100 characters (was 142)." },
    { "check": "manifest.teamTemplates[1].name", "message": "name is required when more than one team template is declared." }
  ],
  "warnings": [
    { "check": "manifest.capabilites", "message": "Unrecognized key 'capabilites' — did you mean 'capabilities'?" }
  ]
}
```

Non-fatal warnings reuse the same `{ check, message }` entry shape but are
carried in a separate `warnings` array and never, on their own, cause rejection.

---

## Requirements traceability

| Requirement | Realized by |
|-------------|-------------|
| FR-MANIFEST-001 (required metadata) | `title`, `shortDescription`, `version`, `gdkApiVersion`, `runtime`, `backend.entryPoint`, `frontend.entryPoint` |
| FR-MANIFEST-002 (team templates) | `teamTemplates` + `$defs.teamTemplate` / `$defs.range` |
| FR-MANIFEST-003 (capability flags) | `capabilities.ai`, `.spectators`, `.midGameJoin` |
| FR-MANIFEST-004 (configurable parameters) | `parameters` + `$defs.parameter` |
| FR-MANIFEST-005 (parameter types) | `$defs.parameter` `allOf` per-`type` branches; parameter validation table |
| FR-MANIFEST-006 (tags) | `tags` (1–10 items, 1–24 chars) |
| FR-MANIFEST-007 (info document path) | `infoDoc` |
| FR-MANIFEST-008 (backend entry point — JVM) | `backend.entryPoint` (FQCN under `runtime: "jvm"`) |
| FR-MANIFEST-009 (frontend entry point) | `frontend.entryPoint` |
| FR-GDK-016 (GDK version in manifest) | `gdkApiVersion` |
| FR-UPLOAD-002 / FR-UPLOAD-008 (manifest validation, detailed errors) | Validation section (two layers, single aggregated error response) |

Adjacent requirements validated by the bundle / upload-pipeline spec rather than
here: FR-UPLOAD-003, FR-UPLOAD-004, FR-UPLOAD-005, FR-UPLOAD-006, FR-UPLOAD-007.
