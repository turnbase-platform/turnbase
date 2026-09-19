# Game Bundle Format & Upload Pipeline

Implementation-level design of the **game bundle** — the ZIP archive a developer uploads — and of the
**pipeline** that turns it into a servable, loadable, catalogued game version: the archive's layout
and the security rules a reader must enforce, the ordered validation stages and their error
identifiers, how a validated bundle is unpacked and published atomically, how GDK API compatibility
is bounded, and what happens to storage and to the version slot when any of it fails.

This is the sibling of [`manifest-schema.md`](manifest-schema.md) and owns everything that document
lists as out of scope: the archive itself, path existence, `TurnBaseGame` resolution, GDK-class
absence, version ordering against server state, `gdkApiVersion` range, and size limits. It closes
review items **GAME-I7** (`gdkApiVersion` check) and the upload half of **GRMP-F4** (serialization
round-trip), and it is the document
[`game-asset-serving.md`](../game-frontend/game-asset-serving.md) §4.1 defers to when it says the
unpacking of the ZIP belongs elsewhere.

**Realizes:** `game-development-experience.md` FR-BUNDLE-001…007, FR-UPLOAD-002…008,
NFR-UPLOAD-001/002, FR-GDK-016, `game-contracts.md` NFR-SIZE-001; `game-catalog.md` FR-GAME-009/010/011/014.

**Depends on / must not contradict:**

| Document | What it fixes for this spec |
|---|---|
| [`manifest-schema.md`](manifest-schema.md) | the manifest contract; this spec never restates a field rule |
| [`../api-design/file-uploads.md`](../api-design/file-uploads.md) | the pre-signed URL flow and the `PENDING → PROCESSING → ACTIVE \| FAILED` statuses |
| [`../platform/data-model-catalog.md`](../platform/data-model-catalog.md) §1–2 | every row and column this pipeline writes, and the full status set |
| [`../game-frontend/game-asset-serving.md`](../game-frontend/game-asset-serving.md) §4–5 | the `/g/{gameId}/{version}/` tree, its caching and its CSP — the shape this pipeline must produce |
| [`../game-host/game-host-internals.md`](../game-host/game-host-internals.md) §3, §5, §7 | the guest bridge, the shared serialization engine, and how the backend JAR is fetched |
| [`../api-design/error-handling.md`](../api-design/error-handling.md) | the `422` bundle-validation error shape |
| [ADR-0006](../../decisions/0006-game-trust-model-java-official-only.md) | `runtime: "jvm"` is official-only for the MVP |

---

## 1. Scope, and what ADR-0006 does to it

**In scope:** the archive format and its reader; the ordered validation pipeline and its error
identifiers; the static serializability analysis; unpacking, publication and activation; the GDK API
compatibility range; slot expiry, retry and storage cleanup.

**Out of scope:** the manifest document's own rules (`manifest-schema.md`); the HTTP shape of the
upload endpoints (`file-uploads.md`); how the published tree is served, cached and framed
(`game-asset-serving.md`); how the Game Host loads the fetched JAR (`game-host-internals.md` §7); the
test harness's UX (planned harness spec).

### 1.1 The MVP exercises the official path only

ADR-0006 makes `runtime: "jvm"` — the only runtime that exists — **official-only**, and the ADR's own
consequences list says this "likely removes the untrusted bundle/upload-pipeline spec from MVP
scope." It does not, and the distinction matters: what ADR-0006 removes is the *untrusted actor*, not
the *pipeline*. Official games are still archives, still carry manifests, still declare entry points,
still need unpacking into `/g/{gameId}/{version}/`, and still need a version to become `ACTIVE`
exactly once. Every stage below runs for an official upload. What does not run in the MVP is any
stage whose *only* purpose is to defend against a hostile uploader — and there is exactly one such
stage, §3.2's `bundle.runtime.trust`, which for the MVP is the gate that rejects everything else.

So the pipeline is specified in full and **exercised in full**, with one honest caveat: the checks
that matter against an adversary (the archive rules of §2, the GDK-class check, the class-file
version check) are, for the MVP, protecting the platform from *its own build output*. They will catch
a packaging mistake; nobody has yet tried to defeat them. That is a reason to write them now and
review them again before community uploads open, not a reason to defer them — a validator retrofitted
onto a live pipeline is a validator that starts by grandfathering everything already stored.

**The enforcement point ADR-0006 asks for is §3.2 stage E4.** A bundle whose manifest declares
`runtime: "jvm"` is accepted only when the upload arrived on the admin path (`admin-tooling.md`
FR-ADM-001's localhost-bound Basic-auth port) and the target game is `badge = 'OFFICIAL'` with
`owner_user_id IS NULL`. This has to be a pipeline stage rather than an endpoint-level rule because
`runtime` is not known until the manifest has been parsed, which is after the bytes are already in
object storage: the public endpoint of `file-uploads.md` step 1 has only a version string and a size
to judge.

---

## 2. The archive

### 2.1 Format and layout

A bundle is a single ZIP archive (FR-BUNDLE-001). No tar, no 7z, no nested archive: one format means
one reader, and the reader is the largest untrusted-input surface in the platform.

```
bundle.zip
├── manifest.json              ← required, exactly at the archive root (FR-BUNDLE-002)
├── backend/
│   └── chess.jar              ← path declared by manifest.backend.path (FR-BUNDLE-003)
├── frontend/
│   ├── main.js                ← path declared by manifest.frontend.entryPoint
│   ├── assets/atlas.png
│   └── style.css
└── INFO.md                    ← optional, path declared by manifest.infoDoc (FR-BUNDLE-005)
```

Only `manifest.json` has a fixed location. Everything else is manifest-declared, which is what makes
the structure language-agnostic (FR-BUNDLE-007): a future `runtime: "py"` bundle has the same shape
with a different `backend.path` target. The directory names above are the convention the GDK
archetype emits; nothing validates them.

**There is no HTML file, and a bundle containing one at the frontend root gets a warning.** The
platform serves the document itself (`game-asset-serving.md` §5; `game-development-experience.md`
CON-006), so an `index.html` in the
bundle is dead weight that will never be loaded and almost always means the developer built for a
static host and expects their own shell.

### 2.2 Path rules

Entry names are the archive's attack surface, and every rule below has been the subject of a
published ZIP extraction CVE somewhere. A reader **must** reject an archive containing any entry
that:

| Rule | Rejected because |
|---|---|
| is not encoded UTF-8 (general-purpose bit 11 unset **and** the name is not pure ASCII) | the fallback is CP437, and guessing means the validator and the unpacker can disagree about which file is `manifest.json` |
| contains a NUL or any C0 control character | truncation differences between a Java `String` and a C filesystem call |
| is absolute (`/foo`), or carries a Windows drive or UNC prefix (`C:\`, `\\host\`) | writes outside the destination |
| contains a `..` path segment, before or after normalization | zip-slip: the canonical traversal escape |
| contains a backslash | on some readers a separator, on others a legal filename character — the two readings pick different files |
| has an empty segment, or a segment that is `.`, or a segment with leading/trailing whitespace or a trailing dot | normalizes differently on different filesystems; a name that means two things is a validation bypass |
| exceeds 1024 bytes total or 255 bytes in any one segment | POSIX `NAME_MAX`, and the object-key length budget of §5.1 |
| duplicates another entry's name, **case-insensitively** | see below |
| is not a regular file or a directory — the external-attributes mode says symlink, device, FIFO or socket | a symlink extracted before the entry that targets it turns a subsequent write into a write anywhere on the host |
| is encrypted (general-purpose bit 0 set) | unreadable, and an encrypted archive that "validates" is a validator that skipped it |
| uses a compression method other than *stored* (0) or *deflate* (8) | bzip2/LZMA/zstd decoders in a ZIP container are additional untrusted-input parsers for no developer benefit |

**Duplicate entries are fatal, and this is the rule that is easiest to get wrong.** ZIP permits two
entries with the same name; readers disagree about which wins — `java.util.zip.ZipFile#getEntry`
returns the *last* central-directory match, while a sequential `ZipInputStream` scan yields the
*first*. A validator that reads the manifest through one API and an unpacker that writes through the
other can be handed a bundle with two `manifest.json` entries: the validator approves entry 1 and the
unpacker publishes entry 2. Rejecting duplicates outright removes the class; matching the two APIs
would not, because it is a property nobody can see in a code review a year later. The comparison is
case-insensitive because the local-filesystem `ArtifactStore` backend runs on developer machines,
where `Main.js` and `main.js` are the same file, and GRMP's lesson §4 already records that
filesystem-artifact plumbing is where the local backend bites.

**The archive is read through its central directory, and the local headers are cross-checked.** An
entry whose local header disagrees with its central-directory record about name, compression method
or size is rejected. Nothing in the archive's own size fields is trusted for enforcement — §2.3's
ceilings are measured against bytes actually produced by the inflater, because the declared
uncompressed size is attacker-controlled and is exactly what a bomb lies about.

### 2.3 Resource ceilings

`FR-BUNDLE-006` caps the bundle at 256 MB and `game-development-experience.md` NFR-SIZE-001
(distinct from `game-contracts.md` NFR-SIZE-001, which is the 10 MB state cap) restates it as the configured maximum. That cap is
on the **compressed** archive and is therefore not a limit on anything the pipeline actually does: a
deflate stream of 256 MB of zeros expands past 250 GB, and the pipeline's job is to inflate it. The
ceilings that bound the work are these, all configurable (§8):

| Ceiling | Default | Enforced |
|---|---|---|
| Compressed archive size | 256 MB (`turnbase.uploads.max-bundle-size`) | declared at slot creation, re-checked against the stored object |
| **Total uncompressed size** | **1 GB** | incrementally, across all entries |
| Per-entry uncompressed size | 256 MB | incrementally |
| Per-entry compression ratio | 100:1 | incrementally, after the first 1 MB of output for that entry |
| Entry count | 20 000 | from the central directory, before any inflation |
| Directory nesting depth | 32 | from entry names |
| `manifest.json` size | 256 KiB | before parsing |
| Info document size | 1 MiB | before reading (it lands in a Postgres `text` column, §5.4) |

"Incrementally" is the operative word: a ceiling checked after inflation completes is not a ceiling.
The reader counts bytes as they leave the inflater and aborts the entry — and the whole validation —
the moment a counter crosses. The 1 GB total is four times the compressed cap, which is generous for
honest content (a 256 MB bundle is already almost entirely pre-compressed PNG, WOFF2 and JAR, none of
which deflate well) and small enough to fit the working space of a single validation without a disk
budget conversation.

The ratio ceiling is deliberately not applied to the first 1 MB of an entry's output, because small
highly-compressible files are ordinary — a 40 KB JSON level file, an SVG, a source map — and a naive
ratio check flags them all.

### 2.4 The reader is one component

The archive reader is a single class used by the validator, the unpacker and the test harness. This
is the manifest lesson (`manifest-schema.md`: one JSON Schema, two consumers) and the GRMP-F4 lesson
(one serialization engine, three consumers) applied a third time. Two readers with the same rule
written twice is the duplicate-entry bug above, generalized.

---

## 3. The validation pipeline

### 3.1 What runs where

`file-uploads.md` splits the flow across a synchronous slot request and an asynchronous job, and that
split determines what each check can possibly know.

| Phase | When | Knows | Reports as |
|---|---|---|---|
| **A — Slot** | `POST /api/games/{gameId}/versions` | a version string and a declared size | `422` (or `409`), synchronously |
| **B1 — Stored object** | within `POST .../confirm`, before it returns | whether the object exists and its size | `422` (or `503`/`410` outside this taxonomy — `file-uploads.md`'s error table), synchronously, on the confirm request itself |
| **C–F — Validation** | after `POST .../confirm` returns `202`, background job | the archive and the manifest | `validation_errors` on the version row; retrieved by `GET .../versions/{uploadId}` and pushed as `BUNDLE_VALIDATION_COMPLETE` |
| **G — Publication** | same job, after C–F pass | everything, plus the row lock on the game | as above |

**B1 is synchronous, not part of the background job** — a correction to this table and to §3.4 below.
`file-uploads.md`'s flow narrative (step 3) and its own § Size Validation both describe the
stored-size check as failing the `confirm` request itself, before `202` is ever returned; an earlier
revision of this table and of `error-handling.md`'s Bundle Validation Errors section grouped B with
the asynchronous C-F job and said `POST /api/games/{gameId}/versions` was the only synchronous `422`
source, which cannot both be true alongside `file-uploads.md`'s explicit, repeated statement to the
contrary. Resolved in `file-uploads.md`'s favor: it is the more specific, operational document for
the confirm endpoint's own behavior, and it independently states the same thing in two places. See
`IMP-GATE-61`.

**Phase A's version-ordering check is advisory and Phase G's is authoritative.** `file-uploads.md`
step 1 checks the declared version against the current active one, which is the right thing to do —
it is what stops a 256 MB upload that was doomed before it started. It is not sufficient, because
minutes elapse between the slot and the activation, and two slots can be open at once. Request a slot
for `1.3.0` (higher than the active `1.2.0` — accepted), then a slot for `1.2.5` (also higher —
accepted), let `1.3.0` validate and activate, then let `1.2.5` activate: the active version has gone
backwards, and `game-catalog.md` FR-GAME-009 says the platform rejects exactly that. The check is
therefore repeated inside the activation transaction of §5.4, under the same lock that makes
`game_version_active_key` decide the race.

### 3.2 Stages

Each stage names the `check` identifier that appears in the `errors` array of
[`error-handling.md`](../api-design/error-handling.md)'s bundle-validation shape. Identifiers are
dotted paths, matching the existing `manifest.version` / `backend.gdkClasses` examples.

**Phase A — slot** (synchronous):

| # | `check` | Decides | Requirement | On failure |
|---|---|---|---|---|
| A1 | `version.format` | `^\d+\.\d+\.\d+$` | game-catalog.md FR-GAME-009 | fatal, `422` |
| A2 | `version.ordering` | strictly higher than the current `ACTIVE` version, compared as three integers | FR-UPLOAD-006 | fatal, `422` (advisory — see §3.1) |
| A3 | `version.slot` | no unexpired `PENDING`, `PROCESSING`, `ACTIVE` or `SUPERSEDED` row already holds this `(game_id, version)` | §7.4 | fatal, `409` |
| A4 | `bundle.declaredSize` | `bundleSize` ≤ `turnbase.uploads.max-bundle-size` | FR-UPLOAD-007, FR-BUNDLE-006 | fatal, `422` |

**Phase B — the stored object** (synchronous, within `POST .../confirm` — see §3.1):

| # | `check` | Decides | Requirement | On failure |
|---|---|---|---|---|
| B1 | `bundle.storedSize` | the object exists, and its size is ≤ the declared size and ≤ the configured cap | FR-UPLOAD-007 | fatal, `422` |

**Phase C — archive integrity** *(barrier: nothing downstream can run without a readable archive)*:

| # | `check` | Decides | Requirement | On failure |
|---|---|---|---|---|
| C1 | `bundle.archive.format` | parses as ZIP; central directory intact; local headers agree; ≤ 20 000 entries; no encryption; permitted compression methods only | FR-BUNDLE-001 | fatal |
| C2 | `bundle.archive.entryName` | every entry name satisfies §2.2 | FR-BUNDLE-002 | fatal, one entry per offending name |
| C3 | `bundle.archive.duplicate` | no case-insensitive duplicate names | §2.2 | fatal |
| C4 | `bundle.archive.entryType` | every entry is a regular file or a directory | §2.2 | fatal |
| C5 | `bundle.archive.expansion` | the §2.3 ceilings hold | FR-BUNDLE-006 | fatal, aborts immediately |

**Phase D — manifest** *(barrier: without a manifest there are no declared paths to check)*:

| # | `check` | Decides | Requirement | On failure |
|---|---|---|---|---|
| D1 | `manifest.present` | `manifest.json` exists at the archive root, is ≤ 256 KiB, is valid UTF-8 and parses as JSON | FR-BUNDLE-002 | fatal |
| D2 | `manifest.<path>` | **delegated in full to [`manifest-schema.md`](manifest-schema.md)** — both layers, all identifiers, plus its non-fatal unknown-key warnings | FR-UPLOAD-002 | fatal / warning per that spec |
| D3 | `manifest.version` | equals the version declared at slot creation | §9, A1 | fatal |

**Phase E — archive against manifest** *(no barriers between these; all run)*:

| # | `check` | Decides | Requirement | On failure |
|---|---|---|---|---|
| E1 | `bundle.paths.backend` | `backend.path` names an existing file entry | FR-UPLOAD-003 | fatal |
| E2 | `bundle.paths.frontend` | `frontend.entryPoint` names an existing file entry | FR-UPLOAD-003 | fatal |
| E3 | `bundle.paths.infoDoc` | when `infoDoc` is declared, it names an existing file entry ≤ 1 MiB | FR-MANIFEST-007, §9 | fatal |
| E4 | `bundle.runtime.trust` | `runtime: "jvm"` arrived on the official path (§1.1) | ADR-0006 | fatal |
| E5 | `manifest.gdkApiVersion` | within the platform's supported range | GAME-I7, NFR-COMPAT-001 | fatal — §6 |
| E6 | `frontend.entryType` | `frontend.entryPoint` ends in `.js` or `.mjs`, and the frontend tree contains no `.html` | CON-006 | **warning** |

**Phase F — the backend artifact**, `runtime: "jvm"` only. F1–F2 are a barrier for F3–F7:

| # | `check` | Decides | Requirement | On failure |
|---|---|---|---|---|
| F1 | `backend.jar` | the entry at `backend.path` is itself a readable ZIP/JAR, subject to §2.2–2.3 recursively (one level; a JAR inside the JAR is not opened) | FR-BUNDLE-003 | fatal |
| F2 | `backend.classVersion` | every `.class` entry has major version ≤ 65 (Java 21); `META-INF/versions/N/` entries have N ≤ 21 | CON-007 | fatal |
| F3 | `backend.gdkClasses` | no entry under `io/turnbase/gdk/` | FR-UPLOAD-005, FR-GDK-014 | fatal |
| F4 | `backend.shadedRuntime` | no entry under a package the guest bridge also provides (`com/fasterxml/jackson/`) | §9 | **warning** |
| F5 | `backend.entryPoint` | `backend.entryPoint` resolves to a `public`, non-`abstract` class in this JAR, with a public no-argument constructor, that implements `io.turnbase.gdk.TurnBaseGame` | FR-UPLOAD-004 | fatal |
| F6 | `state.type` | the type argument `S` of `TurnBaseGame<S>` is statically resolvable and implements `GameState` | FR-GDK-012 | fatal (unresolvable ⇒ **warning**, F7 skipped) |
| F7 | `state.serializable` | `S`'s type graph is serializable by the shared engine | GRMP-F4, FR-GDK-013 | fatal / warning — §4 |

**Phase G — publication and activation:** §5. Its only reportable failures are `version.ordering`
(re-checked authoritatively) and `pipeline.interrupted` (§7.2).

### 3.3 "All failures in one response" has barriers, and saying so is not a weakening

FR-UPLOAD-008 requires every validation failure in a single report, and a naive reading of it is
unimplementable: the entry-class check cannot run when the JAR is not in the archive, and the
declared-path checks cannot run when the manifest did not parse. The pipeline therefore collects
**every failure within a phase** and stops only at a **barrier** — a phase whose output is the next
phase's input:

```
A ─┬─ B ─── C ══ D ══ E ─┬─ F1,F2 ══ F3…F7 ─── G
   │                     │
   └─ ══ is a barrier ───┘        E1 failing also skips F entirely
```

Everything else accumulates. A bundle with a 142-character `shortDescription`, a missing
`frontend/main.js`, an out-of-range `gdkApiVersion` and GDK classes in the JAR produces **four**
entries in one `errors` array, because those four sit in D, E, E and F with no barrier between them.
A bundle whose ZIP is truncated produces one. This is the honest contract, and it is worth stating
because the alternative — pretending the pipeline can report a check it was unable to run — produces
either invented errors or a validator that reports "manifest missing" four times.

### 3.4 The result is a resource, not an error response

`file-uploads.md` step 3 returns `202 Accepted` and validates asynchronously.
`error-handling.md`'s bundle-validation example shows a `422` whose `instance` is
`/api/games/abc/versions/upload-id/confirm`. Both cannot be true, and the example's own `errors`
array proves it: it mixes `manifest.version` (a Phase A check, decided minutes before the confirm)
with `backend.gdkClasses` (a Phase F check, decided minutes after it). No single HTTP response can
carry both. See §9 D2.

This spec resolves it as follows, and the resolution is visible in the shapes:

- **Phase A failures are a `422`** on `POST /api/games/{gameId}/versions`, with `instance` naming that
  path. This is a synchronous rejection of a request; the `422` bundle-validation shape fits exactly.
- **Phase B1 failures are a `422`** on `POST .../confirm` itself, with `instance` naming that path —
  the stored-size check runs before that request returns anything, so it is exactly as synchronous
  as Phase A's checks, just against a different request. `IMP-GATE-61` corrected this section (and
  §3.1's table) to say so; an earlier revision grouped B with the asynchronous phases below and
  `error-handling.md` claimed `POST /api/games/{gameId}/versions` was the only synchronous source,
  which `file-uploads.md`'s own flow narrative and § Size Validation directly contradict.
- **Phase C–G failures are not an HTTP error at all.** They are the *state of a resource* that was
  successfully created (`confirm` already returned `202` by the time any of them can run). `GET
  /api/games/{gameId}/versions/{uploadId}` returns `200` with the version record, whose `status` is
  `FAILED` and which carries `errors` and `warnings` arrays of the same `{ check, message }` entries,
  read from `validation_errors` / `validation_warnings`:

```json
{
  "uploadId": "550e8400-e29b-41d4-a716-446655440000",
  "version": "1.2.0",
  "status": "FAILED",
  "createdAt": "2026-06-11T13:00:00Z",
  "errors": [
    { "check": "bundle.paths.frontend", "message": "frontend.entryPoint 'frontend/main.js' is not in the archive." },
    { "check": "backend.gdkClasses",    "message": "JAR contains 12 entries under io/turnbase/gdk/. Declare the GDK API as 'provided' scope." }
  ],
  "warnings": [
    { "check": "manifest.capabilites", "message": "Unrecognized key 'capabilites' — did you mean 'capabilities'?" }
  ]
}
```

Returning a `422` Problem Detail from a `GET` that successfully found the thing it was asked for is a
category error: the request was fine, and a client that treats 4xx as "retry the request differently"
will loop. The `errors` array is the same array either way — one report format, two carriers, which
is what FR-UPLOAD-008 actually requires.

`warnings` is present on `ACTIVE` versions too; `manifest-schema.md` requires the upload UI to render
unknown-key warnings on a *successful* validation, and `game_version.validation_warnings` is where
they live.

---

## 4. The serialization round-trip check

### 4.1 The failure GRMP-F4 describes

`grmp-lessons.md` F4: Seven Wonders Duel's state serialized correctly inside the prototype platform
and failed to round-trip in the standalone validator, because the validator used a bare
`ObjectMapper` and the extracted game's POM had lost `<parameters>true</parameters>`. Two implicit
configurations drifted the moment the game left the monorepo. The lesson's framing is that such a
game is discovered at runtime, mid-session, when a crash-recovery attempt fails — and by then the
session is gone.

### 4.2 …is a failure mode TurnBase has already designed away, and that changes the answer

TurnBase does not serialize state only for recovery. **Canonical state is serialized JSON on every
single invocation** (`game-host-internals.md` §8: the host holds bytes, rich objects exist only
transiently inside the guest during a call). A state type that cannot round-trip therefore fails on
the *first action of the first game*, deterministically, as `MALFORMED_OUTPUT` or
`STATE_TOO_LARGE` — not months later during a recovery nobody was watching. Three consecutive
failures fail the session back to Lobby (§9.4 there) with no room closure and no history entry.

That is a materially smaller blast radius than GRMP's, and it reframes what the upload check is for.
It is **not** the last line of defence against silent data loss. It is a developer-experience
guarantee: catch the packaging mistake before the game reaches the catalog, so the first person to
discover it is the developer rather than four players who joined a room.

### 4.3 The constraint: NFR-UPLOAD-002 forbids execution

NFR-UPLOAD-002 is a **Must**: "The upload pipeline must not execute any code from the bundle during
validation. Static analysis and metadata inspection only." An executing round-trip — instantiate the
entry class, call `onInit`, serialize, deserialize, re-serialize, compare — violates it directly.

### 4.4 Resolution: a real static check at upload, the executing test in the harness

**The pipeline performs static serializability analysis of the state type, and NFR-UPLOAD-002 stands
unamended. The executing round trip lives in the test harness (FR-HARNESS-*), which runs the
developer's own code on the developer's own machine and has no trust problem to solve.**

Static analysis is not a consolation prize here. The specific defect GRMP hit — a lost
`-parameters` flag — is **exactly** the kind of thing a class file answers, because the flag's whole
effect is whether a `MethodParameters` attribute was emitted. The pipeline resolves `S` from the
`Signature` attribute of the entry class's `TurnBaseGame<S>` supertype and walks `S`'s field/component
graph, checking each node against the capability set of the **shared serialization component**
(`game-host-internals.md` §5) — read from that artifact, never re-derived, because a second copy of
"what Jackson can do here" is the drift F4 is about.

| Condition on a state type or any type reachable from it | Verdict | Why |
|---|---|---|
| Not a `record`, has no public no-arg constructor, and its creator constructor's parameters carry neither a `MethodParameters` attribute nor `@JsonProperty` | **fatal** | The GRMP defect. Jackson cannot name the parameters, so deserialization fails on every action. |
| A `Map<K, …>` whose `K` is not `String`, an `enum`, `UUID` or a boxed integral type | **fatal** | Jackson writes such a key with `toString()` and cannot read it back, and the developer has no hook to register a `KeyDeserializer` — the ObjectMapper is platform-owned and guest-side. A `Map<Position, Piece>` board is the most likely state shape on a board-game platform and it round-trips to garbage. |
| A field or component whose declared type is an interface or abstract class, other than `List`/`Set`/`Map`/`Collection` (which bind to concrete defaults) | **fatal** | Polymorphic deserialization needs type information the developer cannot supply: the GDK API is interfaces-only (FR-GDK-015) and carries no Jackson dependency, so `@JsonTypeInfo` is not reachable without bundling Jackson — which F4 (§3.2) warns about. |
| A declared type of `Object` | **fatal** | Same, with less information. (This rule is state-only. Effect payloads are `Object` by design — `backend-gdk-api.md` §6 — and are serialized but never deserialized.) |
| A type no registered module can handle (e.g. `java.time.*` without `JavaTimeModule`, `Optional` without `Jdk8Module`) | **fatal** | Decidable against the shared engine's registered module set. |
| A reference cycle in the type graph | **warning** | A self-referential nullable field is legal if never populated; a cycle that *is* populated overflows the stack at runtime. Undecidable statically. |
| `S` not resolvable — the entry class implements `TurnBaseGame` raw or with a type variable | **warning**, F7 skipped | Nothing to analyze. Reported so the silence is visible. |
| The graph exceeds the analysis bound (2 000 types or depth 64) | **warning**, analysis truncated | A bound that fails open would be a bound an adversary sets. |

All of these report under `state.serializable`, one entry per offending type, naming the field path
(`GuessState.board.pieces[key]`).

### 4.5 Why not execute in a throwaway Espresso context

ADR-0006 makes the MVP's Java trusted, so the *safety* objection to executing `onInit` at upload is
weak today. Three other objections are not.

**The safety is temporary and the code is permanent.** A validator that executes game code, gated on
"ADR-0006 says this is trusted", is a code-execution primitive sitting one configuration flag away
from the untrusted upload path that ADR-0006 explicitly plans to open. That is GRMP-F5 with a
different variable name: a `?? 'TRUSTED'` fallback that silently loaded untrusted code. The way to
fail closed, as `game-asset-serving.md` §9.3 puts it, is to have no branch that can fail open. Adding
the executor post-MVP is a change; removing one is a migration.

**The cost is a second Game Host inside the monolith.** Executing `onInit` needs an Espresso context,
which needs the guest JDK 21 image, the guest bridge JAR and the context-builder configuration —
i.e. `game-host-internals.md` §4.2 and §7 re-embedded in a different deployable. Against
NFR-UPLOAD-001's 30 s budget the seconds are affordable; duplicating another service's guest stack to
spend them is not.

**It buys less than it looks.** `onInit` needs an `InitContext` — a roster and materialized
parameters (FR-GDK-004). The pipeline would have to synthesize a roster, choosing arbitrarily among
the manifest's team templates, and would exercise the one initial state that choice produces. A game
whose state acquires its interesting shape on move 40 — the `Map<Position, Piece>` only becomes
non-empty after the first placement — is not covered at all. And the check would then have to be
*fatal* on a synthesized input the developer never wrote, or *non-fatal*, in which case it has
purchased an Espresso embedding to print a warning.

**The post-MVP answer is the same, and more so.** Untrusted uploads make execution strictly worse.
What changes post-MVP is only that the platform can no longer assume the developer ran the harness —
so the response is to tighten §4.4's fatal set, not to add an executor.

### 4.6 Where the executing test does live, and the residual risk

The harness runs `onInit`, serializes, deserializes, re-serializes and compares — the exact sequence
GRMP-F4 asks for — **through the shared serialization component**, which is the part of the lesson
that actually mattered: GRMP's game passed in-platform and failed standalone purely because the two
used different ObjectMappers. It runs automatically before launching the local environment, alongside
the bundle validation FR-HARNESS-002 already mandates, and it reaches states the upload pipeline
never could, because a developer playing their own game drives them.

FR-HARNESS-002 enumerates FR-UPLOAD-002 through 005 and 007 and does not mention the round trip. **It
must be amended to name it** — see §9 R1.

**Residual risk, stated plainly.** A state type that passes §4.4 can still fail to round-trip at
runtime: a field declared `List<Piece>` holding a subclass instance, a `Map<String, Object>` whose
values are decided at runtime, a getter that throws, a lossy `float`, or a `Set` whose iteration order
the game depends on and JSON does not preserve. None of these are statically decidable. Their
consequence is bounded as in §4.2 — first action, deterministic, session fails back to Lobby, room
survives — and their detection is the harness's job. A developer who never runs the harness ships a
game that fails on move one; that is a bad outcome and it is not a *silent* one, which is the property
GRMP-F4 was written about.

---

## 5. Unpacking and publication

### 5.1 Two trees, and the archive is kept

Publication writes two things into the artifact store, both derived from the validated archive and
both keyed so they are addressable without reading the manifest:

| Object key | Contents | Read by |
|---|---|---|
| `bundles/{gameId}/{version}/bundle.zip` | the uploaded archive, verbatim | nothing, in normal operation — see below |
| `unpacked/{gameId}/{version}/<archive-relative path>` | every published archive entry, byte-identical | the monolith's asset route, serving `/g/{gameId}/{version}/**` |
| `artifacts/{gameId}/{version}/backend.jar` | a copy of the entry at `manifest.backend.path` | the Game Host (`game-host-internals.md` §7.1) |

**The backend JAR is copied to a normalized key rather than served from its archive-relative path.**
The Game Host's `ContextKey` is `(game_id, game_version)` and nothing else; if the JAR's key depended
on `manifest.backend.path`, the Host would need the manifest — a database read or an extra gRPC field
— before it could fetch a JAR. A key derivable from the ContextKey removes that dependency entirely,
which is the whole reason `game-host-internals.md` §7.1 can describe the fetch in one sentence.

**The archive is retained, not deleted after unpacking.** It is what makes the unpacked tree
*rebuildable*: a validator change can be re-run against a historical bundle (the same argument
`data-model-catalog.md` §2 makes for storing the manifest whole), and a lost or corrupted object in
the unpacked tree is repairable without asking the developer to re-upload. This is also what
`bundle_object_key` and `bundle_purged_at` are for on a version whose assets are already unpacked:
the ZIP outlives its own upload and dies with the version (§7.3).

### 5.2 What is published, and the hole this closes

`game-asset-serving.md` §5 serves the bootstrap document with `<base href="/g/{gameId}/{version}/">`
and `<script src="{manifest.frontend.entryPoint}">`. `frontend.entryPoint` is an **archive-relative**
path (`frontend/main.js`), so the served tree must preserve archive-relative paths or every relative
reference in the game's build output breaks. The naive implementation of that requirement is "unpack
the whole archive", and the naive implementation is a data leak.

`game-asset-serving.md` §4.2 establishes that bundle assets are **unauthenticated** — the games origin
receives no cookies by construction, so the asset handler cannot know who is asking — and argues
correctly that this is fine because a bundle is "JavaScript, CSS and sprites". Unpack the whole
archive and it is no longer only that: `GET /g/{gameId}/{version}/backend/chess.jar` returns the
game's **backend** to anyone. Not even a guessing attack — `gameId` is in the hostname and the current
version is a column of the public catalog (FR-CAT-002), so the URL is derivable from a catalog page.
For the MVP that exposes the platform's own official game code; post-MVP it hands every third-party
developer's proprietary JAR to anyone who loads their game once.

Publication therefore applies a **deny list**, and the tree is otherwise an exact subset of the
archive:

| Excluded | Why |
|---|---|
| `manifest.json` | the platform's copy is authoritative (`game_version.manifest`); the archive copy is a duplicate with an independent path to being stale |
| the entry at `manifest.backend.path` | above |
| the entry at `manifest.infoDoc` | its rendered content is served through the game detail page (FR-GDET-003/004), where FR-GDET-004's sanitization applies; serving the raw Markdown from the games origin routes around that |
| any entry matching `*.jar`, `*.war`, `*.class` | a second backend artifact the manifest did not declare is still a backend artifact; no such file can ever be a browser asset |

Everything else publishes. **No entry is ever rewritten** — the published bytes equal the archive
bytes — so `<base href>` resolution, source maps and subresource paths behave exactly as they did in
the developer's build output.

A deny list is the wrong long-term shape and it is chosen deliberately: the right shape is an
allow list rooted at a manifest-declared `frontend.root`, which is a manifest change, and
`game-asset-serving.md` OQ-003 already contemplates the manifest growing a `frontend` field for a
related reason. Until then, a developer who puts a secret in their frontend build output publishes
it, exactly as they would to any static host. See OQ-002.

**Content types are set at publication, from a fixed extension map**, and this is load-bearing rather
than cosmetic: `game-asset-serving.md` §4.1 sends `X-Content-Type-Options: nosniff` on every game
response, so an ES module served as `application/octet-stream` is **refused by the browser**, not
sniffed. The map covers `.js`/`.mjs` → `text/javascript`, `.css`, `.json`, `.wasm` →
`application/wasm` (required for streaming instantiation, which the CSP's `'wasm-unsafe-eval'` exists
to permit), the image, font and audio types, and defaults to `application/octet-stream`. An unmapped
extension on `frontend.entryPoint` is E6's warning.

### 5.3 Unpack happens at validation, and publication is atomic without a rename

**At validation.** The alternative — unpack lazily on first serve — fails three ways. The games origin
is unauthenticated (§4.2 there), so an anonymous `GET` would trigger an inflation of up to 1 GB: a
denial-of-service with no authentication to rate-limit against. It re-opens every question of §2 at
serve time, in a latency-sensitive path, with a second reader. And it makes the atomicity below
impossible: there is no moment at which the tree is known complete.

**Atomic without a rename.** Object stores have no atomic directory rename, and GRMP's lesson §4
records `Files.move(ATOMIC_MOVE)` failing across mount boundaries on the local-filesystem backend, so
a rename-based publish is not available anyway. Atomicity comes instead from the **pointer**: the
asset route serves `/g/{gameId}/{version}/**` only for a version row whose `status` is `ACTIVE` or
`SUPERSEDED` and whose `bundle_purged_at` is null. Ordering:

```
1. write every published object under unpacked/{gameId}/{version}/    (status = PROCESSING)
2. write artifacts/{gameId}/{version}/backend.jar
3. read back: object count and per-object size match what was written
4. ── the activation transaction (§5.4) ──                            (status → ACTIVE)
```

A version is reachable only after step 4, and step 4 is a single database transaction. A crash at any
point in 1–3 leaves objects nobody can address, because no row points at them; §7.3's sweep collects
them. **A half-unpacked tree cannot start serving**, which is the property that matters: a game whose
frontend loads three of its four chunks is a game that renders a broken board and blames the
platform.

`SUPERSEDED` is in the predicate because FR-GAME-011 keeps the previous version alive while rooms are
using it, and FR-ASSET-007 pins a session to the version resolved when it started. Dropping
`SUPERSEDED` would blank the iframe of every in-progress game the instant a patch shipped.

The predicate is one row lookup per `(gameId, version)`, cacheable in-process because the mapping is
immutable except for purge — status only ever moves toward terminal, and `bundle_purged_at` is set
once. It is not a per-asset database read.

Rejected alternative: a `_published` marker object written last, checked by the serving path. It is a
second place to record a fact the version row already holds, and therefore a second place for it to
disagree — precisely the reasoning `data-model-catalog.md` §4 uses to refuse a `review_state` column.

### 5.4 The activation transaction

One transaction, taking the row lock on `game`, doing all of:

| Write | Source | Rule |
|---|---|---|
| re-check `version.ordering` against the current `ACTIVE` row | `version_major/minor/patch` | §3.1; abort → `FAILED` |
| incumbent `ACTIVE` → `SUPERSEDED`, `superseded_at = now()` | — | FR-GAME-010 |
| this row → `ACTIVE`, `activated_at = now()` | — | FR-GAME-010, guarded by `game_version_active_key` |
| `manifest`, `gdk_api_version` | the validated document | `data-model-catalog.md` §2 |
| `min_players` = Σ(`size.min` × `count.min`), `max_players` = Σ(`size.max` × `count.max`) | `teamTemplates` | FR-CAT-002 |
| `supports_ai`, `supports_spectators`, `supports_mid_game_join` | `capabilities` | FR-MANIFEST-003 |
| `game.active_version_id` | — | `data-model-catalog.md` §2 |
| `game_tag` rebuilt for this game | `tags` | `data-model-catalog.md` §3 |
| **first activation only:** `game.title`, `game.short_description`, `game.info_doc_markdown` | manifest, and the *resolved content* of `infoDoc` | `data-model-catalog.md` §1 — seeded once, never rewritten (FR-GAME-008) |
| badge: `VERIFIED` → `UNVERIFIED`; **`OFFICIAL` and `UNVERIFIED` unchanged** | — | FR-GAME-014, and see §9 D1 |

The badge rule is narrower than FR-GAME-014's text and it has to be. FR-GAME-014 says a new version
"clears Verified"; `data-model-catalog.md`'s traceability compresses that to "badge reset at
activation". Applied literally to an Official game — which under ADR-0006 is *every* game in the MVP
— setting `badge = 'UNVERIFIED'` violates `game_official_ownerless_ck`, whose equivalence requires
`badge = 'OFFICIAL'` exactly when `owner_user_id IS NULL`. The transaction aborts and no official game
can ever be updated. Verified is a thing only a community game has; clearing it is a no-op everywhere
else.

`info_doc_markdown` stores the **resolved content** of the `infoDoc` entry, not its path
(`data-model-catalog.md` §1), which is why E3 makes a declared-but-missing `infoDoc` fatal: at first
activation the pipeline must produce that content or permanently seed a null.

Everything after the transaction — the SSE `BUNDLE_VALIDATION_COMPLETE` notification of
`file-uploads.md` step 4 — is outside it and best-effort.

---

## 6. `gdkApiVersion` compatibility

### 6.1 The range is a property of the deployed guest bridge, not an independent setting

`game-host-internals.md` §3.2 puts the compiled GDK API classes in the **guest bridge JAR**, which
ships in the Game Host image. Exactly one GDK version is on the guest classpath at a time. The
"platform's supported range" is therefore not a free configuration value — it is a fact about a
deployed artifact, and a configuration key that could disagree with it would eventually disagree with
it. The bridge JAR declares its GDK version in its manifest; the monolith reads it at startup, and the
configured `turnbase.gdk.supported-range` is an **assertion** checked against it, failing startup on
mismatch. This mirrors `platform-operations.md` FR-CRED-002's rule that a missing or wrong
configuration must fail startup rather than silently pick a default.

The range is expressed as a closed interval of `x.y.z` versions and evaluated with the same
three-integer comparison as FR-GAME-009.

| Platform GDK | Supported range | Rationale |
|---|---|---|
| `0.y.z` (pre-release) | exactly `[0.y.0, 0.y.z]` | NFR-COMPAT-001 grants backward compatibility only *from v1.0.0*; during 0.x the API "may introduce breaking changes between versions without a major bump". A range spanning two 0.x minors would be a compatibility promise the requirement explicitly withholds. |
| `1.y.z` and later | `[1.0.0, 1.y.z]` | NFR-COMPAT-001: a game built against 1.x runs on 1.y for y ≥ x. The upper bound is real — a game declaring a GDK newer than the platform's is asking for classes that are not there. |
| across majors | unsupported | GDE OQ-003 defers the cross-major strategy; until it exists, a major mismatch is a rejection, not a gamble. |

The MVP ships `0.3.0` (the version in `manifest-schema.md`'s example), so the MVP range is
`[0.3.0, 0.3.0]`.

### 6.2 At upload

Stage E5: `manifest.gdkApiVersion` outside the range is fatal, with a message naming both the
declared version and the range. Below the range, the message says to rebuild against the current GDK;
above it, that the platform has not been upgraded yet. These are different developer actions and a
single "incompatible version" message sends half of them the wrong way.

The **test harness cannot perform this check offline** — the supported range is a property of a
deployment the harness has never contacted. FR-HARNESS-002's enumeration correctly omits it. See
OQ-004.

### 6.3 When the platform's range moves past a live game

Nothing in the corpus specifies this, and it is the case that actually hurts: an upgrade that orphans
a game which is `ACTIVE`, listed, and being played. Under the 0.x rule above it is not an edge case —
**every** platform GDK bump orphans **every** game, because the supported range is a single minor
line. That is what NFR-COMPAT-001's pre-1.0 carve-out means in practice, and it is better said out
loud than discovered on a Friday.

`data-model-catalog.md` §2 built `game_version_gdk_idx` — a btree on `gdk_api_version`, partial over
`status IN ('ACTIVE','SUPERSEDED')` — for exactly the reverse query this needs: *which stored versions
fall outside the currently supported range?*

```sql
SELECT game_id, version_id, version, gdk_api_version
  FROM game_version
 WHERE status IN ('ACTIVE','SUPERSEDED')
   AND gdk_api_version NOT BETWEEN :range_low AND :range_high;   -- three-integer comparison
```

**The sweep reports; it never mutates catalog state.** It runs at startup and whenever the range
changes, emitting one WARN per orphaned version and a gauge dimensioned by game, and it is a deploy
gate: a non-zero count is a failed upgrade, not a warning to triage later. It does not deactivate,
supersede or discard anything, for three reasons. There is no status that means "incompatible" —
`SUPERSEDED` asserts a newer version took over, which is false, and `DISCARDED` purges the bundle,
which turns a recoverable upgrade into permanent artifact loss. Clearing `game.active_version_id`
removes the game from the public catalog via `game_public_idx`'s `active_version_id IS NOT NULL`
term, so a bad upgrade would silently empty the catalog. And most decisively: **the correct remedy is
a platform rollback or a rebuilt bundle, and a mutation makes the rollback stop working** — rolling
back the image would restore compatibility, but not the catalog rows the upgrade rewrote.

**Enforcement is at room creation**, joining the existing set of catalog preconditions on
`INSERT INTO room` (`data-model-catalog.md` §1, *Where the write-side rules are enforced*): the active
version's `gdk_api_version` must lie in the range, or room creation fails with a `422` naming the
game. This is the right place because it is the last point at which a human can be told something
useful. The alternative — letting the room open and failing at `CreateSession` — surfaces as
`CODE_LOAD_ERROR` after players have gathered and configured teams.

**In-progress sessions are not touched.** Their Espresso context is already built against the GDK the
Game Host was running when it started, and `TerminateSession`-ing live games because of a
configuration change is a worse outcome than letting them finish. A rolling upgrade replaces the Game
Host pod, which fails those sessions anyway through the ordinary crash path
(`game-host-internals.md` §9.3), and that path is already specified.

For the MVP this makes the upgrade procedure concrete and cheap: official games are first-party and
versioned in-repo, so "rebuild the official games against the new GDK and publish them with the
platform" is a CI step in the same pipeline, not an operational hazard. It stops being cheap the day
community uploads open, which is the day NFR-COMPAT-001's v1.0.0 stability promise has to be real.

---

## 7. Failure, retry and cleanup

### 7.1 The status machine, as this pipeline drives it

`data-model-catalog.md` §2 owns the status set. This pipeline is the writer for five of the seven.

| From | To | Trigger |
|---|---|---|
| — | `PENDING` | slot created (`file-uploads.md` step 1) |
| `PENDING` | `PROCESSING` | confirm received, job claimed the row |
| `PENDING` | `EXPIRED` | `upload_expires_at` passed with no confirm — §7.2 |
| `PROCESSING` | `ACTIVE` | Phases B–G passed (§5.4) |
| `PROCESSING` | `FAILED` | any fatal check, or the job was interrupted — §7.2 |
| `ACTIVE` | `SUPERSEDED` | a newer version activated (§5.4) |
| `SUPERSEDED` / `ACTIVE` | `DISCARDED` | retirement — owned by `data-model-catalog.md` §2/§5, not by this spec |

`FAILED` and `EXPIRED` are terminal. Neither ever becomes `DISCARDED`: `DISCARDED` means *retired and
purged*, and `data-model-catalog.md`'s retirement predicate is defined only over `SUPERSEDED` and
`ACTIVE`. Their bundles are still purged (§7.3) and `bundle_purged_at` still records it; the status
stays put because it is already terminal and already correct. See §9 D5.

### 7.2 The two sweeps this pipeline needs

**Slot expiry.** A developer who requests a slot and never uploads leaves a `PENDING` row and possibly
a partially-uploaded object. `file-uploads.md`'s error table says the "pending slot [is] cleaned up by
scheduled job", `data-model-catalog.md` §2 defines `EXPIRED` as its outcome and builds
`game_version_upload_expiry_idx` to find it, and `local-environment.md` §7.2 configures
`turnbase.jobs.upload-slot-cleanup.interval` at 15 minutes. **No requirement defines the job and no
spec defines its duties** (§9 D3). Its duties are:

1. `PENDING` rows with `upload_expires_at < now()` → `EXPIRED`.
2. `PROCESSING` rows whose worker lease has lapsed → `FAILED`, with a single
   `{ "check": "pipeline.interrupted", "message": … }`. A validation job that dies with its pod
   otherwise leaves the row in `PROCESSING` forever, and because `game_version_key` is unique on
   `(game_id, version)`, that row **permanently burns the version number** — the developer can never
   retry `1.2.0`, only skip to `1.2.1`. The lease is a `claimed_by`/`claimed_until` pair the job
   refreshes; it does not exist as columns today (§9 D4).
3. Purge storage for every `EXPIRED` and `FAILED` row not yet purged (§7.3).
4. Delete objects under `unpacked/{gameId}/{version}/` and `artifacts/{gameId}/{version}/` for any
   version not in (`ACTIVE`, `SUPERSEDED`) — the collector for a crash during §5.3 steps 1–3.

It runs under FR-JOB-005's distributed lock and obeys FR-JOB-010's idempotency rule: every action is a
conditional transition whose guard is the precondition that justified it, so a re-run against a clean
system does nothing.

**GDK-range orphan detection** — §6.3. Not periodic; startup and range change only.

### 7.3 Storage lifecycle

| Row state | `bundles/…/bundle.zip` | `unpacked/…`, `artifacts/…` |
|---|---|---|
| `PENDING` | may or may not exist | never written |
| `PROCESSING` | exists | being written |
| `ACTIVE`, `SUPERSEDED` | retained (§5.1: the tree is rebuildable from it) | retained |
| `FAILED` | **purged**, `bundle_purged_at` set | purged |
| `EXPIRED` | **purged**, `bundle_purged_at` set | never existed |
| `DISCARDED` | purged by the retirement path (`data-model-catalog.md` §5) | purged with it |

A failed bundle is purged immediately, not after a grace period, and that needs justifying because it
is the one place this pipeline deletes something a user might want. It is safe because the *error
report* is durable and independent — `validation_errors` is a Postgres column, not something read out
of the object — and the developer already has the ZIP; they built it. Against that, a 256 MB object
per failed attempt is by far the largest garbage source in the platform, and FR-RET-005 offers no
automatic purge at all ("artifacts are retained indefinitely while the game is listed... no automated
purge is required"), so without this rule failed uploads accumulate without bound. Deletion is
best-effort and `bundle_purged_at` is set only on success, so a failed delete is retried by the next
sweep rather than being forgotten.

**The pre-signed URL's expiry is `upload_expires_at`** — the same instant, computed once. A URL that
outlives its slot lets bytes land under a key whose row is already `EXPIRED`, and nothing would ever
read or delete them. The sweep's prefix delete (7.2 duty 3) covers the narrow race where the PUT
completes just before expiry and the confirm arrives just after.

### 7.4 Does a failed version block re-uploading the same number?

Structurally, yes: `game_version_key` is unique on `(game_id, version)`, so a second slot for `1.2.0`
cannot be inserted while any row holds it. Left there, a manifest typo burns a release number
permanently — the developer's git tag says `1.2.0`, the platform will only ever accept `1.2.1`, and
FR-GAME-009 gives them no way back.

**The slot is reclaimable.** `POST /api/games/{gameId}/versions` for a version whose only existing row
is `FAILED` or `EXPIRED` **reuses that row**: status → `PENDING`, a fresh `upload_expires_at` and
pre-signed URL, `validation_errors`/`validation_warnings` cleared, `declared_size_bytes` updated, and
the prior object purged if the sweep has not got to it. No new row, so no unique-index conflict and no
schema change.

Reclamation is refused, with `409 conflict` from stage A3, when the existing row is:

| Status | Because |
|---|---|
| `PENDING`, unexpired | a slot is already open; two writers for one object key |
| `PROCESSING` | validation is running against those bytes |
| `ACTIVE` | it is the live version; replacing it is what a *new* version number is for |
| `SUPERSEDED` | rooms may still be running on it (FR-GAME-011) and `/g/{gameId}/{version}/` still serves it |
| `DISCARDED` | it existed and was retired; re-minting the number would make `room.game_version` and `game_history_entry.game_version`, which are text and may still name it, point at different code |

The last row is the one that decides the policy: version numbers of versions that were ever *live* are
immutable because history refers to them by string. Version numbers of versions that never activated
refer to nothing and are free.

No requirement states this. See §9 R2.

---

## 8. Configuration

Extends `local-environment.md` §7.2 and §7.5; the binding rule there applies.

| Property | Default | Source |
|---|---|---|
| `turnbase.uploads.max-bundle-size` | `256MB` | FR-BUNDLE-006 (existing) |
| `turnbase.uploads.slot-ttl` | `1h` | file-uploads.md step 1 (existing) |
| `turnbase.uploads.max-uncompressed-size` | `1GB` | §2.3 |
| `turnbase.uploads.max-entry-uncompressed-size` | `256MB` | §2.3 |
| `turnbase.uploads.max-compression-ratio` | `100` | §2.3 |
| `turnbase.uploads.max-entry-count` | `20000` | §2.3 |
| `turnbase.uploads.max-info-doc-size` | `1MB` | §2.3 |
| `turnbase.uploads.validation-lease` | `10m` | §7.2 duty 2 |
| `turnbase.jobs.upload-slot-cleanup.interval` | `15m` | §7.2 (existing) |
| `turnbase.gdk.supported-range` | `0.3.0-0.3.0` | §6.1 — asserted against the guest bridge at startup |

Every ceiling is configurable because GRMP-F6's lesson is that a hard-coded limit is a limit that
blocks a test run at midnight. None of them may be raised without re-reading §2.3: they are
correctness bounds on an untrusted parser, not performance knobs.

---

## 9. Assumptions this spec makes visible

Walking the pipeline end to end surfaced contradictions and gaps in adjacent documents. This spec
proceeds under a stated resolution for each rather than papering over it. **None of these are fixed
here** — every one needs an edit to a document this spec does not own.

**D1 — FR-GAME-014 applied literally breaks every official upload.** `game-catalog.md` FR-GAME-014
clears Verified on new-version upload; `data-model-catalog.md`'s traceability renders it "badge reset
at activation"; `file-uploads.md` step 3.6 says activation "clears `Verified` status" unconditionally.
For an Official game, `owner_user_id IS NULL`, and `game_official_ownerless_ck` is an *equivalence*, so
writing `badge = 'UNVERIFIED'` aborts the transaction. Under ADR-0006 every MVP game is Official, so
the first update of any official game fails. **Assumed resolution:** the badge transition is
`VERIFIED → UNVERIFIED` only (§5.4).

**D2 — the bundle-validation `422` cannot exist as documented.** `error-handling.md`'s example is a
`422` on `.../confirm` mixing a Phase A check with a Phase F check, while `file-uploads.md` step 3
returns `202`. **Assumed resolution:** §3.4 — `422` for synchronous Phase A only, and a `200` resource
carrying `errors`/`warnings` for everything asynchronous.

**D3 — the slot-expiry job has an index, a status, an interval and no definition.** `EXPIRED`,
`game_version_upload_expiry_idx` and `turnbase.jobs.upload-slot-cleanup.interval` all exist; no FR-JOB
in `platform-operations.md` defines the job, so it is also outside FR-JOB-005's single-instance rule
and FR-JOB-004's observability rule. **Assumed resolution:** §7.2, with the duties named there.

**D4 — `PROCESSING` has no exit on crash and no lease columns.** §7.2 duty 2 requires a
`claimed_by`/`claimed_until` pair on `game_version` that the schema does not have. **Assumed
resolution:** the columns are added; until they are, a crashed validation permanently burns a version
number.

**D5 — `FAILED` and `EXPIRED` bundles are purged but cannot be recorded as `DISCARDED`.** The
retirement predicate is defined only over `SUPERSEDED` and `ACTIVE`. **Assumed resolution:** §7.1 —
`bundle_purged_at` is set without a status change, which the column permits and no rule forbids.

**D6 — nothing binds the slot's version to the manifest's version.** `game_version.version` comes from
the step-1 request body; `manifest.version` comes from the archive; no document requires them to
agree. A slot for `1.2.0` can be filled with a bundle whose manifest says `0.0.1`, after which the
catalog, `/g/{gameId}/{version}/` and the Game Host `ContextKey` all say `1.2.0` while the artifact
the developer built says otherwise. **Assumed resolution:** stage D3, fatal.

**D7 — the whole-archive unpack publishes the backend JAR.** §5.2. The composition of
`game-asset-serving.md` §4.2 (assets are unauthenticated) with the archive-relative serving of §5
leaks `backend/*.jar` at a URL derivable from the public catalog. **Assumed resolution:** §5.2's deny
list.

**D8 — a game may shade classes the guest bridge also provides.** FR-BUNDLE-003 requires a fat JAR
with "all non-GDK dependencies", and `game-host-internals.md` §4.2 puts the bridge JAR *and* the game
JAR on one guest classpath. A game bundling its own Jackson gets whichever the classpath order picks,
silently, and fails with `NoSuchMethodError` at first invocation. FR-UPLOAD-005 checks only GDK
classes. **Assumed resolution:** stage F4, warning — a warning rather than a fatal because the correct
long-term fix is classloader isolation in the Game Host, not a validator rule.

**D9 — `manifest-schema.md` cites FR-UPLOAD-003 for `infoDoc` existence, which it does not cover.**
FR-UPLOAD-003 speaks only of "the backend and frontend entry points". This spec checks `infoDoc`
anyway and makes it fatal (stage E3), because `data-model-catalog.md` §1 needs its *content* at first
activation and a null there is permanent. The citation should be corrected or FR-UPLOAD-003 widened.

**D10 — the local seed path bypasses this pipeline.** `local-environment.md` §6 says official bundle
artifacts "are uploaded to MinIO by the same runner, from the official games' build output", with a
seeded `ACTIVE` version row. If that means writing a ZIP and inserting a row, the `unpacked/` tree of
§5.1 never exists: `make seed` succeeds, the catalog lists the game, and the iframe 404s on
`frontend/main.js` — the exact "lists and cannot start" failure that section says it wants to avoid.
**Assumed resolution:** the seeder drives this pipeline rather than writing storage directly.

**Requirement additions and amendments needed (none made here):**

- **R1 — FR-HARNESS-002 must name the serialization round trip.** It currently enumerates FR-UPLOAD-002
  through 005 and 007. §4.4 places the executing round trip in the harness and nowhere else, so
  without this amendment the check GRMP-F4 asks for is required by no requirement.
- **R2 — slot reclamation (§7.4) is a policy no requirement states.** FR-GAME-009 constrains ordering;
  nothing says whether a version number that never activated may be retried.
- **R3 — the state-type constraints of §4.4 belong in `backend-gdk-api.md` §5.** FR-GDK-013 promises
  "no manual serialization code is required from the developer", which is true only under constraints
  (records or `-parameters`; scalar map keys; no polymorphic fields) that are documented nowhere.
  GRMP-F4's own suggested change asked for this and it is still open — so the pipeline currently
  rejects games for violating rules the GDK never stated.
- **R4 — `game-host-internals.md` §5 cited NFR-SIZE-001 unqualified** (now fixed) for the 10 MB state cap. That
  ID exists in both `game-contracts.md` (10 MB state) and `game-development-experience.md` (256 MB
  bundle); the intended one is the former.

---

## 10. What is deliberately absent

- **No malware or virus scanning.** It would be security theatre against a JAR that is *designed* to
  run arbitrary code, and ADR-0006 already answers the trust question by not accepting untrusted
  backends at all. When community uploads open, dependency scanning of the fat JAR (Trivy is already
  in the CI checklist) is the useful control, not signature matching.
- **No bundle signing or provenance.** There are no developer signing keys, and inventing a PKI to
  authenticate an upload that already arrived over an authenticated session buys nothing.
- **No resumable or multipart upload.** A single PUT of ≤ 256 MB is within S3's 5 GB single-part
  limit. A developer on a bad connection re-uploads; §7.4 makes that free.
- **No delta or incremental uploads.** Every version is a complete bundle. Content-addressed sharing
  of unchanged assets across versions would save storage and break FR-ASSET-007's version pinning
  guarantee that a session's bytes never change.
- **No CDN.** ADR-0001: the monolith serves the games host directly, no new deployable.
- **No per-object digest.** The schema has no column for one, and the archive is retained (§5.1), so
  the unpacked tree is rebuildable rather than merely verifiable. See OQ-003.
- **No lint or quality gate on frontend build output.** Bundle size, source maps, minification and
  dead code are the developer's business.
- **No `manifest.json` rewriting.** The stored `jsonb` is the parsed document, byte-faithful to what
  was uploaded; nothing normalizes or injects defaults into it. `data-model-catalog.md`'s rebuildable-
  projection rule depends on that.

---

## 11. Open questions

- **OQ-001 — an orphaned-by-GDK-range version has no representation.** §6.3 enforces at room creation
  and refuses to mutate catalog state, so the game remains listed and advertised while being
  unhostable. Correct for a rollback-recoverable upgrade, poor for a user who clicks *Create Room* and
  gets a `422`. A non-mutating `compatible` flag computed at read time would fix the display; a status
  would not, for the reasons in §6.3.
- **OQ-002 — deny list vs. `frontend.root`.** §5.2 publishes everything except a deny list. An
  allow list rooted at a manifest-declared `frontend.root` is the correct shape and is a manifest
  change; `game-asset-serving.md` OQ-003 already contemplates the manifest growing frontend fields.
  Resolve both together or neither.
- **OQ-003 — no integrity digest on published objects.** A corrupted object in the unpacked tree is
  undetectable until it fails to parse in a browser. The archive makes it *repairable* but nothing
  makes it *detectable*. A digest column on `game_version`, or a manifest of digests written alongside
  the tree, is the fix; both are schema or storage-layout changes.
- **OQ-004 — the harness cannot check `gdkApiVersion` offline.** §6.2. A published, cacheable
  `/api/gdk/compatibility` document the harness fetches when online is the obvious answer, and it is a
  new public endpoint.
- **OQ-005 — NFR-UPLOAD-001's 30 s budget is unmeasured.** Fetch 256 MB, inflate up to 1 GB, analyze
  every class in a fat JAR, write the unpacked tree back to object storage. Plausible, unvalidated,
  and the class-graph walk of §4.4 is the term most likely to surprise. Benchmark against a real
  engine-based game before treating the Should as met.

---

## 12. Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-BUNDLE-001 (ZIP) | §2.1, stage C1 |
| FR-BUNDLE-002 (root manifest, declared paths) | §2.1, stages D1, E1–E3 |
| FR-BUNDLE-003 (fat JAR) | §2.1, stages F1–F2 |
| FR-BUNDLE-004 (frontend build output) | §5.2 |
| FR-BUNDLE-005 (info document) | stage E3, §5.4 |
| FR-BUNDLE-006 / `game-contracts.md` NFR-SIZE-001 (GDE) | §2.3, stages A4, B1 |
| FR-BUNDLE-007 (language-agnostic) | §2.1; Phase F is the only runtime-specific phase |
| FR-UPLOAD-002 (manifest validation) | stage D2 — delegated to `manifest-schema.md` |
| FR-UPLOAD-003 (structure validation) | stages E1, E2 (E3 by extension — §9 D9) |
| FR-UPLOAD-004 (entry class) | stage F5 |
| FR-UPLOAD-005 (GDK class conflict) | stage F3 |
| FR-UPLOAD-006 / game-catalog.md FR-GAME-009 | stages A1, A2; authoritative re-check in §5.4 |
| FR-UPLOAD-007 (size) | stages A4, B1, §2.3 |
| FR-UPLOAD-008 (all failures, one report) | §3.3, §3.4 |
| NFR-UPLOAD-001 (< 30 s) | §2.3 ceilings bound the work; OQ-005 |
| NFR-UPLOAD-002 (no code execution) | §4.4 — upheld, not amended |
| NFR-COMPAT-001 / FR-GDK-016 / GAME-I7 | §6 |
| FR-GDK-012/013/014 | stages F3, F6, F7 |
| game-catalog.md FR-GAME-010 (single active) | §5.4 + `game_version_active_key` |
| game-catalog.md FR-GAME-011 (old version lifecycle) | §5.3's `SUPERSEDED` serving predicate; retirement itself is `data-model-catalog.md` §2 |
| game-catalog.md FR-GAME-014 (Verified reset) | §5.4, narrowed — §9 D1 |
| game-catalog.md FR-CAT-002 (derived player counts) | §5.4 |
| FR-ASSET-007 (version pinning) | §5.3 |
| CON-006 (no HTML in bundle) | §2.1, stage E6 |
| CON-007 (Java 21 target) | stage F2 |
| ADR-0006 (official-only `jvm`) | §1.1, stage E4 |
| GRMP-F4 (round-trip validation) | §4 |
| GRMP-F6 (per-environment configuration) | §8 |
