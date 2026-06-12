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
6. On success: transitions version to `ACTIVE`, clears `Verified` status (`game-catalog.md FR-GAME-014`)
7. On failure: transitions version to `FAILED`, stores structured error details

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
  "createdAt": "2026-06-11T13:00:00Z"
}
```

| Status | Meaning |
|--------|---------|
| `PENDING` | Upload slot created, awaiting upload and confirm |
| `PROCESSING` | Confirm received, validation in progress |
| `ACTIVE` | Validation passed, version is live |
| `FAILED` | Validation failed; error details returned in response |

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
