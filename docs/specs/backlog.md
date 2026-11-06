# Open-question register and backlog

Every `OQ-*` in `docs/specs` has one disposition here (`IMP-M20-20`, 2026-11-06). The question stays in its
own document; this file says what became of it. Three dispositions:

- **closed** — the corpus or the code already answers it; the pointer says where.
- **decide** — the owner chooses; the options are listed in [Decisions for the owner](#decisions-for-the-owner).
  Nothing is built until the owner picks.
- **backlog** — it can wait; the *Trigger* column is the event that makes it worth picking up again.

Paths are relative to `docs/specs/`. A new open question gets a row here in the same change that adds it.

## Closed

| Question | Answer |
|---|---|
| `gdk-api/frontend-gdk-api.md` OQ-001 reconnection re-init | Resolved in the document: the iframe reloads, so the client receives a fresh `init` and then its per-viewer view. |
| `game-host/game-host-internals.md` §18 OQ-5 eager or lazy reassignment | Resolved 2026-10-29 (`IMP-M18-12`): lazy. |
| `game-host/game-host-internals.md` §18 OQ-6 twelve Espresso contexts per JVM | Resolved 2026-11-06 (`IMP-M20-18`): the host counts creations and retires at the limit. |
| `deployment/local-environment.md` §10 OQ-001 startup budget is a guess | Measured by `IMP-M20-17` (*Startup time* in the same document). The ≤ 30 s target holds; no CI assertion, because CI is not running. |

## Decisions for the owner

| Question | Options | Recommendation |
|---|---|---|
| `platform/data-model-catalog.md` §7 OQ-001 a rejected re-approval leaves a game stuck | (a) a *pending version* row distinct from the active one; (b) let a rejection reactivate the previous `SUPERSEDED` version; (c) refuse upload of a community game while a review is open | (a). It is the only one that keeps the catalog entry live while a patch is reviewed. Must be decided before community uploads open (ADR-0006). |
| `platform/data-model-catalog.md` §7 OQ-003 owner cannot see "pending review" | (a) add a requirement: the owner's game view shows the open review and the submit action answers a domain error; (b) leave the raw unique violation | (a). The read is one `EXISTS` over the partial index. |
| `game-frontend/game-asset-serving.md` §12 OQ-001 fullscreen | (a) `allow="fullscreen"` on the game iframe; (b) keep `allow=""` | (b) until a game asks; (a) is safe (user-gesture gated) and one attribute. |
| `deployment/local-environment.md` §10 OQ-002 no backup for the local Postgres volume | (a) state that losing the volume is acceptable locally; (b) a documented `pg_dump` target | (a) for local, and move the question to M22 (cloud) where history is real data. |

## Backlog

| Question | Why it can wait | Trigger |
|---|---|---|
| `platform/data-model-catalog.md` §7 OQ-002 `decided_by` is a shared credential | One operator today. | A second operator exists. |
| `gdk-api/frontend-gdk-api.md` §13 OQ-002 multiple `onGameEvent` listeners | The setter form is enough; an `addGameEventListener` variant is additive. | A game needs fan-out. |
| `gdk-api/frontend-gdk-api.md` §13 OQ-003 public debug hook for dropped messages | Belongs to the test-harness spec. | The harness is built. |
| `gdk-api/backend-gdk-api.md` §13 OQ-001 generic action payloads | A single named or `sealed` action type avoids it. | A game needs `List<Move>`. |
| `gdk-api/backend-gdk-api.md` §13 OQ-002 typed `getEnum` | Additive overload. | A game uses enum parameters. |
| `gdk-api/backend-gdk-api.md` §13 OQ-003 rich log formatting | Basic Markdown covers FR-LOG-002. | A game needs colour. |
| `game-frontend/game-asset-serving.md` §12 OQ-002 private bundles | Additive (signed tokens); no contract changes. | A private third-party bundle is required. |
| `game-frontend/game-asset-serving.md` §12 OQ-003 manifest stylesheets | CSS is imported from JS. | A game needs `<link>`ed styles; decide with `manifest/bundle-format.md` OQ-002. |
| `platform/room-lifecycle.md` OQ-001 lease numbers chosen, not derived | The load tests ran with them and the invariants held. | A cloud deployment shows different reconnect latencies (M22). |
| `platform/room-lifecycle.md` OQ-002 local monotonic clock vs Redis lease | Single-node guard band is ample. | A multi-node deployment (M22). |
| `platform/room-lifecycle.md` OQ-003 flapping clients | The reconnect lockout dampens it. | The behaviour is observed. |
| `api-design/websocket.md` OQ-001 resync cost under mass reconnect | Bounded by MVP session sizes. | A resync shows as a hotspot. |
| `api-design/websocket.md` OQ-002 spectator sync with no spectator view | A game-authoring concern. | The test harness is built (it should warn). |
| `api-design/rate-limiting.md` OQ-001 shared-IP guest throttling | Local-first MVP. | Real users behind one NAT are throttled. |
| `api-design/rate-limiting.md` OQ-002 tier 6 budgets are per pod | Documented limit. | Multi-room membership lands. |
| `api-design/input-validation.md` OQ-001 emoji in usernames | A display name is a post-MVP model change. | Users push back. |
| `api-design/input-validation.md` OQ-002 ASCII-only email | No mail system exists. | A real user is blocked or mail is added. |
| `manifest/bundle-format.md` §11 OQ-001 version orphaned by GDK range | A read-time `compatible` flag is additive. | A GDK range bump orphans a listed game. |
| `manifest/bundle-format.md` §11 OQ-002 deny list vs `frontend.root` | Manifest change; resolve with asset-serving OQ-003. | Manifest grows frontend fields. |
| `manifest/bundle-format.md` §11 OQ-003 no integrity digest | Schema or storage change; archive makes it repairable. | Community uploads open. |
| `manifest/bundle-format.md` §11 OQ-004 harness cannot check `gdkApiVersion` offline | New public endpoint. | The harness is built. |
| `manifest/bundle-format.md` §11 OQ-005 30 s upload budget unmeasured | Needs a real engine-based game. | Community uploads open. |
| `game-host/game-host-internals.md` §18 OQ-1 per-context memory and FR-CTX-007 | Pod-level cap is enough; `loadtest/reports/2026-10-18-contexts.md` has the first numbers. | Phase C packs several versions per pod. |
| `game-host/game-host-internals.md` §18 OQ-2 per-session interrupt isolation | Accepted for the MVP. | Cross-session density grows. |
| `game-host/game-host-internals.md` §18 OQ-3 instance sharing | Memory optimisation. | Real games validate the no-mutable-field rule. |
| `game-host/game-host-internals.md` §18 OQ-4 live-object state cache | Opt-in optimisation. | State (de)serialization nears the 30 s budget. |
