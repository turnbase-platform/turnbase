## Last Session Summary

**Date:** 2026-11-06 (session 275) — **`IMP-M20-14` DONE. 224 of 232 items done.**

- `RoomRepository` (3,242 lines) is six package-private repositories plus `RoomRecords` (the shared value types): `RoomRepository` (create/join/leave, member commands, 663 lines), `RoomHostCommandRepository` (527), `RoomGameStartRepository` (239), `RoomReadRepository` (606), `RoomPresenceRepository` (598), `RoomOutboxRepository` (584). Largest class 663 lines. SQL and transaction boundaries moved verbatim; callers and tests take the repository they use.
- Local: unit 298 tests (unchanged); integration 53 classes, 380 tests, per-class counts equal the `@Test` counts in source (no test added or removed). Failing in the environment, identically on untouched master: `GameAssetControllerIT` (6) and `SeedDataIT` (1) — `*.games.localhost` requests get an I/O error. `RateLimitInterceptorIT` failed once under load and passed alone.
- `ARCHITECTURE.md` and one spec reference (`room-invitation-rest-api.md`) updated; corpus check clean.
- Next: pick the next READY item (`IMP-M20-15`…).

```
== turnbase-platform
phase        classes  tests   seconds
unit              65    298       6.0
integration       53    381     614.5
-- slowest classes [unit] (sum of test times)
     1.61s    8  io.turnbase.platform.game.GameSessionServiceTest
     1.13s    1  io.turnbase.platform.account.LoginServiceTimingTest
     0.78s    2  io.turnbase.platform.RedisConnectionConfigTest
     0.70s    2  io.turnbase.platform.ConnectionPoolSizeTest
     0.59s    6  io.turnbase.platform.room.ParticipantCacheTest
     0.56s    1  io.turnbase.platform.room.RoomOwnershipSchedulingConfigTest
     0.40s    2  io.turnbase.platform.game.GameHostChannelsTest
     0.39s    5  io.turnbase.platform.session.OAuthStateServiceTest
     0.35s    4  io.turnbase.platform.account.GoogleOAuthClientTest
     0.27s   12  io.turnbase.platform.websocket.WebSocketRateLimiterTest
-- slowest classes [integration] (sum of test times)
    97.96s   13  io.turnbase.platform.notification.NotificationControllerIT
    93.97s    6  io.turnbase.platform.upload.GameAssetControllerIT
    67.17s    6  io.turnbase.platform.notification.TwoInstanceIT
    55.18s    6  io.turnbase.platform.websocket.WebSocketIT
    28.78s   21  io.turnbase.platform.room.RoomOwnershipServiceIT
    22.94s    8  io.turnbase.platform.seed.SeedDataIT
    18.24s   25  io.turnbase.platform.room.RoomControllerIT
    18.14s   11  io.turnbase.platform.room.ReconciliationJobIT
    17.95s    1  io.turnbase.platform.game.HostFailureReassignmentIT
    15.31s   20  io.turnbase.platform.social.SocialControllerIT
== turnbase-game-host
phase        classes  tests   seconds
unit              22     89     117.2
integration        7     22     100.2
-- slowest classes [unit] (sum of test times)
    57.43s    5  io.turnbase.gamehost.shim.GameBridgeClientEspressoTest
    17.51s    3  io.turnbase.gamehost.warmup.GameHostWarmupTest
    12.52s    4  io.turnbase.gamehost.registration.HostWedgeTest
    12.11s    4  io.turnbase.gamehost.espresso.EspressoIsolationTest
     3.59s    3  io.turnbase.gamehost.espresso.SharedEngineIsolationTest
     2.53s    1  io.turnbase.gamehost.espresso.EspressoContextLifecycleTest
     2.41s    2  io.turnbase.gamehost.registration.HostLivenessLoopTest
     1.88s    7  io.turnbase.gamehost.espresso.GameContextManagerTest
     1.70s    7  io.turnbase.gamehost.espresso.BootWatchdogTest
     1.49s    1  io.turnbase.gamehost.registration.HostWedgeWiringTest
-- slowest classes [integration] (sum of test times)
    43.98s    1  io.turnbase.gamehost.espresso.ConcurrentBootsIT
    25.83s    1  io.turnbase.gamehost.espresso.bench.EngineSharingBenchmarkIT
    24.66s   11  io.turnbase.gamehost.dispatch.SessionDispatcherIT
     4.51s    2  io.turnbase.gamehost.grpc.GrpcServerIntegrationIT
     0.78s    2  io.turnbase.gamehost.artifact.S3ArtifactStoreIT
     0.46s    4  io.turnbase.gamehost.dispatch.SessionRecordStoreIT
     0.00s    1  io.turnbase.gamehost.bridge.GuestBridgeJarIT
== turnbase-frontend
phase        classes  tests   seconds
vitest           122    944      57.9
-- slowest classes [vitest] (sum of test times)
     8.15s   63  src/app/App.test.tsx
     5.03s   36  src/features/rooms/RoomPage.test.tsx
     3.66s   15  src/features/settings/SettingsPage.test.tsx
     3.03s   13  src/features/notifications/NotificationPanel.test.tsx
     2.29s    8  src/features/catalog/CatalogPage.test.tsx
     2.16s   10  src/features/rooms/RoomsPage.test.tsx
     1.45s   14  src/features/rooms/RoomGame.test.tsx
     1.45s    8  src/features/friends/FriendsPage.test.tsx
     1.35s   12  src/features/profile/ProfilePage.test.tsx
     1.20s    4  eslint-rules/theme-scope.test.js
```

## Current State

- **Phase 1, M20 (refinement) open**: 13 of 22 items remain (`10` partly done). M0–M19 are closed (archived under `docs/implementation/archive/`).
- **Red / not run:** CI is refused for billing, so every item is judged locally (`spotless:apply`, `verify`, `verify -Pintegration`). Nothing else is known red.
- **Owner-held:** CI billing (or the public flip); the 7WD bootstrap secret (re-check live before reporting it); the Repos Production reply, which decides whether 7WD ships under its name.

## Next Priorities

- `10` (PARTIAL, continue from its Remaining line), `11`, `13`, `15`, `17`, `18`, `19`, `20`, `21` have no open dependency. Keep the maps current: `check-corpus.py code-maps` fails on a renamed class they name.
- After M20: M21 public release (licence, README, gitleaks, published artifacts), M22 cloud deployment (ADR-0021 from `IMP-M20-15` first), then Phase C.

[`conventions.md`](docs/implementation/conventions.md) applies to every item and is not repeated in read-lists.
