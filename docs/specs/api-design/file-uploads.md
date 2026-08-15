# File Uploads

Game bundles (ZIP archives up to 256 MB — `game-development-experience.md FR-BUNDLE-006`) are uploaded via a pre-signed URL flow. Binary data never passes through the Spring Boot monolith — the client uploads directly to object storage.

## Storage Abstraction

The `ArtifactStore` interface supports three backends, selected by Spring profile:

| Environment | Backend |
|-------------|---------|
| Local dev / tests | MinIO (S3-compatible, run via Testcontainers `@ServiceConnection`) |
| Local Kubernetes | MinIO (deployed in-cluster) |
| Production | AWS S3 |

The same pre-signed URL code path runs against MinIO in tests as in production against S3. No test-specific branching exists in the upload flow.

## Upload Flow

### Step 1 — Request an upload slot

```
POST /api/games/{gameId}/versions
Content-Type: application/json

{
  "version": "1.2.0",
  "bundleSize": 42000000
}
```

The monolith:
1. Validates the declared version is strictly higher than the current active version (`game-catalog.md FR-GAME-009`)
2. Validates `bundleSize` is within the platform limit (default 256 MB)
3. Generates a pre-signed PUT URL via `ArtifactStore`
4. Creates a version record in `PENDING` state

**Response — 201 Created:**

```json
{
  "uploadId": "550e8400-e29b-41d4-a716-446655440000",
  "uploadUrl": "https://storage.example.com/games/abc/1.2.0/bundle.zip?X-Amz-Signature=...",
  "expiresAt": "2026-06-11T14:00:00Z"
}
```

### Step 2 — Client uploads directly to storage

The client PUTs the bundle ZIP to `uploadUrl`. The monolith is not involved in the transfer.

```
PUT {uploadUrl}
Content-Type: application/zip
Body: <bundle bytes>
```

### Step 3 — Client confirms the upload

```
POST /api/games/{gameId}/versions/{uploadId}/confirm
```

**Response — 202 Accepted**

The monolith returns immediately. Bundle validation runs asynchronously in a background job:

1. Fetches the ZIP from storage
2. Validates manifest schema (`game-development-experience.md FR-UPLOAD-002`)
3. Verifies backend and frontend entry points exist in the archive (`FR-UPLOAD-003`)
4. For JVM bundles: verifies entry class implements `TurnBaseGame` (`FR-UPLOAD-004`)
5. Checks that GDK API classes are not bundled in the JAR (`FR-UPLOAD-005`)
6. On success: transitions version to `ACTIVE`, and — **only if the game's badge is `VERIFIED`** — clears it to `UNVERIFIED` (`game-catalog.md FR-GAME-014`)
7. On failure: transitions version to `FAILED`, stores structured error details, and deletes the stored bundle object

The full stage list, the archive-safety rules and the `check` identifiers are in
[`../manifest/bundle-format.md`](../manifest/bundle-format.md); this document owns only the transport.

**Step 6's badge clause is conditional, and applying it unconditionally breaks every official
upload.** An Official game has `owner_user_id IS NULL`, and `game_official_ownerless_ck` ties the two
together as an equivalence — so writing `badge = 'UNVERIFIED'` on it aborts the activation
transaction. Under ADR-0006 every MVP game is Official, so an unconditional clear means no game can
ever be updated. FR-GAME-014 speaks only of *Verified* status; see
[`../platform/data-model-catalog.md`](../platform/data-model-catalog.md) §2.

**Step 1's version-ordering check is advisory; the authoritative one is at activation.** Two slots can
be open at once. Request `1.3.0` against an active `1.2.0` (accepted), request `1.2.5` (also accepted,
also higher than `1.2.0`), let `1.3.0` activate, then activate `1.2.5` — and the active version has
gone **backwards**, which is exactly what `FR-GAME-009` says the platform rejects. Step 1 exists to
save the developer a doomed 256 MB upload, not to enforce the rule; the activation transaction
re-checks against the version that is active *then*.

Validation is static analysis only — no game code is executed (`game-development-experience.md NFR-UPLOAD-002`).

### Step 4 — Client polls for result

```
GET /api/games/{gameId}/versions/{uploadId}
```

Returns the version record with its current status:

```json
{
  "uploadId": "550e8400-e29b-41d4-a716-446655440000",
  "version": "1.2.0",
  "status": "ACTIVE",
  "createdAt": "2026-06-11T13:00:00Z",
  "warnings": [ ]
}
```

This is a **`200`** whether validation passed or failed — the failure is the state of the resource,
not a failure of the request. The `errors` and `warnings` arrays are documented in
[error-handling.md](error-handling.md).

| Status | Meaning |
|--------|---------|
| `PENDING` | Upload slot created, awaiting upload and confirm |
| `PROCESSING` | Confirm received, validation in progress. Held under a lease — see below |
| `ACTIVE` | Validation passed, version is live |
| `FAILED` | Validation failed; `errors` populated, bundle object deleted |
| `EXPIRED` | Confirm never arrived before `expiresAt` |
| `SUPERSEDED` | A newer version activated; rooms may still be running on this one |
| `DISCARDED` | Retired and unreferenced; bundle purged |

The last three are defined in [`../platform/data-model-catalog.md`](../platform/data-model-catalog.md)
§2, which owns the state machine. They are listed here because a client polling this endpoint will
see them.

**`PROCESSING` is leased.** A validation job whose instance dies would otherwise leave the row in
`PROCESSING` forever — and since `(gameId, version)` is unique, that **permanently burns the version
number**: the developer could never retry `1.2.0`. The validator holds a lease on the row and
`platform-operations.md` FR-JOB-012 moves an expired one to `FAILED`.

**A version number is reclaimable only from `FAILED` or `EXPIRED`.** Re-requesting a slot for a
version whose row is in either state reuses the row. `ACTIVE`, `SUPERSEDED` and `DISCARDED` are
refused: those numbers were live, and `room.game_version` and `game_history_entry.game_version` are
text columns that may still name them.

When the client has an active SSE connection (`sse-notifications.md`), the platform also pushes a `BUNDLE_VALIDATION_COMPLETE` notification to the user so polling is not required.

## Error Cases

| Scenario | Step | Outcome |
|----------|------|---------|
| Version not strictly higher than current | 1 | 422 `business-rule-violation` |
| `bundleSize` exceeds platform limit | 1 | 422 `business-rule-violation` |
| Confirm arrives after `expiresAt` | 3 | 410 Gone; pending slot cleaned up by scheduled job |
| Manifest invalid, entry class missing, GDK classes present | async | Version → `FAILED`; structured errors in GET response |
| Storage unreachable during confirm | 3 | 503; client may retry Step 3 |

Validation errors follow the bundle validation error format in [error-handling.md](error-handling.md).

## Size Validation

The declared `bundleSize` in Step 1 is validated against the platform limit before issuing a pre-signed URL. The actual uploaded object size is also checked at confirm time — if the stored object is larger than declared, the confirm fails with 422.
