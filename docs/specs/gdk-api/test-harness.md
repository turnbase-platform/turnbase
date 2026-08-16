# Local Test Harness

How a game developer runs their game without the platform. Realizes
`../../requirements/game-development-experience.md` FR-HARNESS-001…006 and NFR-DX-*.

The harness is a **developer tool shipped with the GDK**, not a service. It is a runnable JAR plus a
small static frontend, invoked from a game project's directory:

```
mvn io.turnbase:turnbase-harness:run
```

---

## 1. What it has to be, and what it must not become

The harness exists because the alternative — upload to a platform to see whether your game works — is
a minutes-long loop for a one-line change. Its whole value is being *faster and more honest* than the
platform, and those two pull in opposite directions:

| Must | Must not |
|---|---|
| Speak the exact protocol of `../../requirements/game-contracts.md` | Reimplement the protocol. It shares the contract artifacts, or it drifts |
| Validate with the same rules as upload (FR-HARNESS-002) | Fork the validator |
| Run the game in an isolated context | Reproduce the Game Host's Espresso topology |
| Be startable with no configuration | Require Docker, Redis, or a database |

**The harness reuses three artifacts and reimplements nothing:** `manifest.schema.json`
([`../manifest/manifest-schema.md`](../manifest/manifest-schema.md)), the bundle validator from
[`../manifest/bundle-format.md`](../manifest/bundle-format.md), and the `turnbase-sdk` types
themselves. A rule the harness enforces differently from the platform is worse than a rule it does
not enforce, because it teaches the developer something false.

---

## 2. Topology

```
  browser tab(s)                harness process (one JVM)
 ┌──────────────┐   WebSocket  ┌────────────────────────────────────┐
 │ game FE      │◀────────────▶│ mock Orchestration                 │
 │ (iframe)     │              │  · session, roster, teams          │
 │              │              │  · sequence allocation             │
 │ harness shell│              │  · effect fan-out + spectator rule  │
 └──────────────┘              │  · game log rendering              │
                               │                                    │
                               │ in-process game BE (plain JVM)     │
                               │  · TurnBaseGame instance           │
                               │  · state held in a field           │
                               └────────────────────────────────────┘
```

**One process, no Espresso, no gRPC, no Redis.** The game runs as an ordinary object in the harness's
own JVM.

That is a deliberate divergence from production and it is the harness's largest limitation, so it is
stated plainly rather than buried: **the harness does not sandbox.**

**Nor does the Game Host's context configuration, for most of what you might expect.** The ADR-0005
spike ([results](../../reviews/2026-07-02-mvp-readiness/espresso-spike-results.md)) proved that
`IOAccess.NONE` and `sandbox.MaxHeapMemory` do **not** interpose Espresso's native `java.io` and
`java.net` — a guest read `/etc/passwd` and got it. Filesystem (FR-CTX-004), network (FR-CTX-005) and
heap cap (FR-CTX-007) are enforced by the **container**, not the context
(`../game-host/game-host-internals.md` **§4** — the isolation mapping; §7 is the guest classpath).
What the context does block is `System.exit` (FR-CTX-006) and forced termination (FR-CTX-008).

The practical consequence for a game developer: **a game that reads a file may work locally, work in
Docker Compose, and still be wrong.** Compose has no gVisor (ADR-0001) and the network denial is a
Kubernetes `NetworkPolicy` that does not exist there. Do not treat "it ran" as "it is allowed" — the
contract is `game-contracts.md` CON-005, not whatever your local stack happens to permit.

This section says so at length because §1 makes truthfulness the harness's stated design constraint:
a rule the harness enforces differently from the platform is worse than a rule it does not enforce,
and the same applies to a rule it *describes* differently. The alternative —
embedding a guest JDK and a Truffle context in a developer tool — would make the harness a
multi-hundred-megabyte download that starts in seconds instead of milliseconds, to catch a class of
mistake that the platform catches anyway, at upload or at first invocation.

What the harness does instead is **warn**: it runs with a `SecurityManager`-equivalent audit hook
where the JDK still permits one, and flags the calls it observes. Advisory, not enforcement.

---

## 3. Serving the frontend

The harness serves the bundle's `frontend.entryPoint` inside a bootstrap document that mirrors the
platform's (`../game-frontend/game-asset-serving.md` §5): `window.__TURNBASE__` is populated
**before** the game's JS runs, and the FE GDK is injected by the harness rather than bundled by the
game.

**It uses two origins.** `http://localhost:{port}` for the harness shell and
`http://game.localhost:{port}` for the game iframe. Serving both from one origin would be simpler and
would hide every mistake the origin separation exists to catch: a game FE that reads
`window.parent.document`, or a shell handler that accepts `event.origin === '*'`, works perfectly on
one origin and breaks the moment it is deployed. Two origins locally means the postMessage contract
of [`frontend-gdk-api.md`](frontend-gdk-api.md) §8 is exercised for real.

The harness does **not** apply the platform's CSP. It reports what the platform's CSP would have
blocked (an inline `<script>`, a remote font, an `eval`) as a warning at load. Enforcing it would be
better; reporting it is what can be done without a header the harness would then have to keep in sync
by hand.

---

## 4. Simulated players

`FR-HARNESS-003` wants multiple simultaneous players; `FR-HARNESS-005` wants them without a browser
window each.

| Mechanism | Use |
|---|---|
| Additional browser tabs at `?player=bob` | Playing the game as a human |
| A debug panel in the harness shell | Switching the active viewer, inspecting state, forcing a resync |
| `harness.json` scenario file | Scripted action sequences, run headless |
| CLI: `--player bob --action '{"card":"7H"}'` | One-off actions and shell scripts |

The roster and team structure are synthesized from the manifest's `teamTemplates` at the
`count.min` × `size.max` shape the platform uses at room creation (`game-rooms.md` FR-TEAM-012), so
the roster the game sees locally has the same shape it will see in production.

**A spectator is included by default when the manifest declares `capabilities.spectators`.** The
harness fans out effects under the same rule the platform does — spectators receive `broadcast`
only — because `websocket.md` OQ-002 records the exact failure this catches: a game whose `onResync`
returns an empty spectator view leaves spectators looking at a blank screen until the next broadcast,
and no player ever notices. The harness warns when a resync returns an empty view for any viewer.

---

## 5. Lifecycle coverage

The harness can trigger every input the platform can, which is the point — most of them are otherwise
unreachable in local development.

| Input | Trigger |
|---|---|
| `init` | Automatic at start |
| `action` | Tab, debug panel, CLI or scenario |
| `player_joined` | Debug panel, if `capabilities.midGameJoin` |
| `player_left` | Debug panel, with `reason` selectable — `left`, `kicked`, `grace_expired` |
| `resync` | Debug panel, or a tab reload |

**`player_left` deserves its own note.** It is the input a game is most likely to handle wrongly,
because it is the only one that arrives without the player having done anything, and in production it
arrives up to 60 seconds after the disconnect. A developer who never triggers it locally ships a game
that stalls on a turn belonging to somebody who left.

---

## 6. Validation and the round trip

Two things run before the harness will launch (FR-HARNESS-002):

1. **The shared bundle validator**, from the same artifact the upload pipeline uses. Fatal findings
   stop the launch; warnings are printed and it continues.
2. **The serialization round trip** (FR-HARNESS-010) — and this one exists *only* here.

The upload pipeline analyses serializability **statically**, because NFR-UPLOAD-002 forbids executing
game code during upload validation. Static analysis catches the structural violations of
[`backend-gdk-api.md`](backend-gdk-api.md) §5.1 — a missing `-parameters`, a non-scalar map key, an
interface-typed field — and cannot catch the rest: a runtime subtype in a `List<Piece>`, a
`Map<String, Object>`, a throwing getter, a lossy `double`.

The harness runs the real thing:

```
after every invocation:
  json  = mapper.writeValueAsString(state)
  back  = mapper.readValue(json, stateType)
  if !state.equals(back):  report a diff and fail the run
```

After `onInit` and after **every** action, which is what makes it catch the state shape a game only
reaches on move 40. It uses the same `ObjectMapper` configuration the GDK Host uses, from the shared
serialization component — a harness with its own mapper would pass states the platform rejects, which
is precisely the drift GRMP lesson F4 is about.

**This is the only place in the corpus where the round trip is executed.** Without FR-HARNESS-010 the
check that lesson asks for is required by no requirement anywhere.

---

## 7. What it cannot tell you

Stated as a list because a developer who believes the harness is the platform will ship the
difference:

| Not covered | Where it bites |
|---|---|
| **Sandbox restrictions** | File, network, thread and `System.exit` calls succeed locally, fail in the Game Host (§2) |
| **The handler timeout** | No 30-second watchdog. A slow handler runs to completion locally |
| **State size** | No 10 MB ceiling (`game-contracts.md` NFR-SIZE-001) |
| **Concurrency** | One session, one player at a time through one thread. The platform's per-session single-flight lock is not exercised |
| **Crash recovery** | State lives in a field, not Redis. A restart is a new game |
| **Rate limits** | None. A game FE that submits an action per frame works here and is throttled in production |
| **Real latency** | In-process calls, sub-millisecond |
| **GDK version compatibility** | The harness runs whatever GDK the project depends on; the platform enforces a supported range (GAME-I7), which needs server state the harness has none of |

The last one is worth a specific warning at startup: a game that builds and runs here can still be
rejected at upload for a `gdkApiVersion` outside the platform's range, and that is the only
validation failure the harness structurally cannot pre-empt.

---

## 8. Configuration

`harness.json` beside the manifest, all fields optional:

| Field | Default | Purpose |
|---|---|---|
| `port` | `7777` | Harness shell; the game origin uses the same port |
| `players` | derived from `teamTemplates` | Names, teams, roles |
| `parameters` | manifest defaults | Override host-configurable parameters |
| `scenario` | — | Ordered actions to replay at start |
| `strictSerialization` | `true` | Fail the run on a round-trip mismatch rather than warn |
| `failOnWarnings` | `false` | Treat validator warnings as fatal, for CI |

`failOnWarnings` is what makes the harness usable as a game developer's own CI step, which is the
posture the platform would like third-party games to arrive in.

---

## 9. Requirements traceability

| Requirement | Realized by |
|---|---|
| FR-HARNESS-001 | §2, §3 — the mock Orchestration and the two-origin bootstrap |
| FR-HARNESS-002 | §6, from the shared validator artifact |
| FR-HARNESS-003 | §4 — multiple tabs |
| FR-HARNESS-004 | §2 — the harness renders the game log through the platform's Markdown configuration |
| FR-HARNESS-005 | §4 — debug panel, scenario file, CLI |
| FR-HARNESS-010 | §6 — the executing round trip |
| `websocket.md` OQ-002 | §4 — empty-spectator-view warning |
| GRMP lesson F4 | §6, together with the static half in `../manifest/bundle-format.md` §4 |
