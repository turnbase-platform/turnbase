## Last Session Summary

**Date:** 2026-10-14/15 (session 199) — `IMP-M13-03…07` DONE earlier in the session; **`IMP-M13-08` is still WIP**: the owner compared the running build with the prototype artefact and these fixes landed, but not every screen has been compared in both appearances at both widths. Landing: every card now gets the spotlight and lit edge, only the Friday-night card tilts (`ui/Glass`, `ui/Specimen` replace the `inert` pictures, which blocked hover), its border no longer clips the chat bubble, and the Friends card was redesigned (covers, one weight of action, a room-code stub). Sign-in pages (`/`, `/login`, `/register`) carry no Games link: **VW-NAV-002 amended** in `platform-views.md`. Login and register use the prototype's fields (`theme/fields.css`: 44px, borderless, accent-tint focus; no "Required" markers) and show Google when `/api/auth/providers` says so. **Found by the taller fields:** the bell and user menu opened *below* the phone's bottom bar, off-screen; `ui/Responsive/useDockedBar` now opens them above. E2E Google assertions follow the stack's own answer. 907 unit tests, lint, typecheck, prettier green; `make e2e` passes in full after a Game Host restart (it had gone stale after hours of aborted runs: every start said "The game could not be started"). **Local stack:** `deploy/compose/.env` (git-ignored) now holds dummy Google credentials so the button shows; clicking it fails at Google. CI on `turnbase-frontend` `master` was not watched.

---

## Next Priorities

**Session 200:** finish `IMP-M13-08`: compare the remaining screens with the artefact (https://claude.ai/artifact/6RC1DNauYNHMZPPqZLbYz2) in Light and Dark at 1280 and 400 px (catalog, game detail, rooms, room, profile, friends, settings were not re-checked this session), then close M13 in STATUS and both `CLAUDE.md` files. Open design gap: the artefact's top bar on `/login` shows "Log in" tinted and an outline "Create account"; ours has "Play as Guest" and a filled "Create account". The borderless fields now apply to every `TextInput`: look for fields that vanish on a same-coloured surface.

**Session 200:** finish `IMP-M13-08`: compare the remaining screens with the artefact (https://claude.ai/artifact/6RC1DNauYNHMZPPqZLbYz2) in Light and Dark at 1280 and 400 px (catalog, game detail, rooms, room, profile, friends, settings were not re-checked this session), then close M13 in STATUS and both `CLAUDE.md` files. Open design gap noted: the artefact's top bar on `/login` shows "Log in" tinted and an outline "Create account"; ours has "Play as Guest" and a filled "Create account". Browser-wide, the borderless fields now apply to every `TextInput`: look for fields that vanish on a same-coloured surface.

**Session 199:** every `IMP-*` item is `DONE`; none is `PARTIAL` or `BLOCKED`. Candidates: glance at `turnbase-frontend` CI; let `RoomSection` adopt `ui/SectionCard` (it duplicates it); the stale-cookie probe `401` (platform + spec), re-vendoring `vendor/turnbase-gdk-0.1.0.tgz` in `turnbase-game-tictactoe`, and the two absent metrics (histogram config for `HighLatencyP95`, repository metrics).

**Session 198:** every `IMP-*` item is `DONE`; none is `PARTIAL` or `BLOCKED`. Candidates: the stale-cookie probe `401` above (platform + spec), re-vendoring `vendor/turnbase-gdk-0.1.0.tgz` in `turnbase-game-tictactoe` (session 196), and the two absent metrics (histogram config for `HighLatencyP95`, repository metrics).

**Session 196:** `IMP-M10-23` (SDK game frame does not post to a detached parent), then `24`.

**Session 195:** `IMP-M10-22` (Espresso sandbox container dependency documented), then `23`, `24`.

**Session 194:** `IMP-M10-21` (scoped object-store credential), then `22`, `23`.

**Session 193:** `IMP-M10-20` (actuator `loggers` read-only), then `21`, `22`.

**Session 192:** `IMP-M10-19` (`__Host-` Secure session cookie), then `20`, `21`.

**Session 191:** `IMP-M10-18` (done).

**Session 190:** `IMP-M10-17` (unknown route returns 404), then `18`, `19`.

**Session 189:** `IMP-M10-16` (denial copy states the real reason), then `17`, `18`.

**Session 188:** `IMP-M10-15` (escape `LIKE` wildcards in search), then `16`, `17`.

**Session 187:** `IMP-M10-14` (bound the lock and limiter maps), then `15`, `16`.

**Session 186:** `IMP-M10-13` (blocked-send fails visibly), then `14`, `15`.

**Session 185:** `IMP-M10-12` (email change / account deletion re-auth), then `13`, `14`.

**Session 184:** `IMP-M10-11` (Friends view live via SSE `FRIEND_*` notifications; Rooms out of scope per `IMP-GATE-98`), then `12`, `13`.

**Session 183:** `IMP-M10-11` (live refresh), then `12`, `13`.

**Session 181:** `IMP-M10-09` (catalog search NUL/control bytes), then `10`, `11`.

**Session 180:** `IMP-M10-08` (Game Host first cold Espresso context), then `09`, `10`.

**Session 179:** `IMP-M10-07` (chunked body-size limit), then `08`, `09`.

**Session 178:** `IMP-M10-06` (gRPC registry unreachable from the public edge), then `07`, `08`.

**Session 177:** `IMP-M10-05` (rate-limit client IP from the trusted hop), then `06…08`.

**Session 176:** `IMP-M10-04` (atomic login-lockout counter), then High tier `05…08`.

**Session 175:** `IMP-M10-03` (deny a room join before it writes Redis), then High tier `04…08`. `IMP-M10-02` CI result not checked — glance at `turnbase-platform` `master` if convenient.

**Session 174:** M10 is the open milestone — 114 of 137 done, `IMP-M10-02…24` `READY`. Start with `IMP-M10-02` (wildcard-subscribe queue leak, Critical), then the High tier `03…08`. Consider a follow-up for the two absent metrics (histogram config for `HighLatencyP95`, repository metrics).

**Session 173:** `IMP-M11-08` (both pipelines green on Boot 4 — `CI wait: required`; then unpause M10: `IMP-M10-01` to `DONE`). Consider a follow-up for the two absent metrics (histogram config for `HighLatencyP95`, repository metrics).

**Session 172:** `IMP-M11-07` (local stack and acceptance suite on both Boot 4 branches); `08` last (waits for pipelines). M10 stays paused.

**Session 171:** `IMP-M11-06` (game-host tests green: protobuf pin, then ITs and the Espresso round-trip); `07` follows. M10 stays paused.

**Session 170:** `IMP-M11-05` (game-host compile on Boot 4); `06` follows. M10 stays paused.

**Session 169:** `IMP-M11-04` (platform tests green on Boot 4: start with `spring-boot-starter-flyway`, then the carried-in note in its section); `IMP-M11-05` (game-host) is independent. M10 stays paused.

**Session 168:** `IMP-M11-03` (platform host-side JSON → Jackson 3); `IMP-M11-05` (game-host) is independent. Also chase the `io.turnbase.grpc.gamehost.v1.*` `NoClassDefFound` unit errors noted above. M10 stays paused.

**Session 167:** **M11 first — M10 is paused.** Start `IMP-M11-02` (platform compiles on Boot 4.1.1); `IMP-M11-05` (game-host) is independent. M11 uses the ordinary workflow (short-lived branch, merge, bump) (CI not awaited only if the prompt carries a `CI policy for this run` paragraph, i.e. `--skip-ci-wait`): `DONE` for `02…07` means green locally; `02`, `03`, `05` may leave a named part of the build red (record it here); only `08` waits for the pipelines. `IMP-M10-01` is `PARTIAL` but waits on `IMP-M11-08` — do not pick it up.

**Session 166:** `IMP-M10-01` is `PARTIAL` — re-check CI/Trivy on `turnbase-platform` `master` (new Boot/Spring 6.2.x patch?); if green, bump the ref and mark `DONE`. Otherwise decide the gate (`spec-defect`). Meanwhile `IMP-M10-02…24` are independent and `READY`, but they will inherit the red gate in the same repo.

**Session 165:** `M10` is the open milestone — 105 of 129 done, `IMP-M10-01…24` all `READY`, none `PARTIAL` or `BLOCKED` (`IMP-GATE-96` was opened and closed in session 164). Start with the Critical items: `IMP-M10-01` (ownerless-upload authorization, the gate's code side) and `IMP-M10-02` (wildcard-subscribe queue leak), then the High tier `03…08`. See the review INDEX for the finding behind each item.

**Session 164:** none pending at start — all 105 M1–M9 items were `DONE`; ran the E2E & security audit and opened `M10`. No item is `PARTIAL` or `BLOCKED`.

**Session 163:** `IMP-M9-09` (the suite, last). 104 of 105 done. No item is `PARTIAL` or `BLOCKED`.

**Session 162:** `IMP-M9-08`; `09` last. 103 of 105 done. No item is `PARTIAL` or `BLOCKED`.

**Session 161:** `IMP-M9-08`, `IMP-M9-11` (independent); `09` last. 102 of 105 done. No item is `PARTIAL` or `BLOCKED`.

**Session 160:** `IMP-M9-08`, `07` (independent); `09` last. 101 of 104 done. No item is `PARTIAL` or `BLOCKED`.

**Session 159:** `IMP-M9-06`, `08`, `07` (independent); `09` last. 100 of 104 done. No item is `PARTIAL` or `BLOCKED`.

**Session 158:** `IMP-M9-05`, `06`, `08`, `07` (independent); `09` last. 99 of 104 done. No item is `PARTIAL` or `BLOCKED`.

**Session 157:** `IMP-M9-04`–`06`, `08`, `07` (independent); `09` last. 98 of 104 done. No item is `PARTIAL` or `BLOCKED`.

**Session 156:** `IMP-M9-03`–`06`, `08`, `07` (independent); `09` last. 97 of 104 done. No item is `PARTIAL` or `BLOCKED`.

**Session 155:** `IMP-M9-02`–`06`, `08`, `07` (independent); `09` last. 96 of 104 done. No item is `PARTIAL` or `BLOCKED`.

**Session 154:** `IMP-M9-01` is `PARTIAL` and now unblocked — run `make e2e` for the `INVITE_ONLY` case (`notifications.spec.ts`, `rooms.spec.ts`) to finish it. Then `02`–`06`, `08`, `07`; `09` last. 95 of 104 done.

**Session 151:** do `IMP-M9-10` (platform) next — it is `READY` — then finish `IMP-M9-01` (`make e2e`). 94 of 104 done.

**`IMP-M9-01` is `PARTIAL` (session 150); 94 of 104 done.** Next: `IMP-M9-10` (platform: `reachable()` for `INVITE_ONLY`), then re-run `make e2e` to finish `IMP-M9-01` (its `**Remaining:**` line); `02`–`05`, `06`, `08`, `07` are independent; `09` last. Ignore older notes below.

**M9 opened (session 149) from the completeness audit; 94 of 103 done.** Next: `IMP-M9-01` (lobby friend invitations, CA-01 High), then `02`, `03`, `04`, `05` (each independent), `06`, `08`, and `07` (a docs decision); `09` (the suite) last. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M8-16` is `DONE` (session 148).** All 94 items are `DONE`; Phase 1 build plan is complete. Ignore older notes below.

**`IMP-M8-18` is `DONE` (session 147).** Next: `IMP-M8-16` (acceptance suite; mind the guest allowance) — the last M8 item. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M8-15` is `DONE` (session 146).** Next: `IMP-M8-18` (platform live push), then `16` (suite; mind the guest allowance). No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M8-13` is `DONE` (session 145).** Next: `IMP-M8-15`, `IMP-M8-18` (platform live push), then `16` (suite). No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M8-12` is `DONE` (session 144).** Next: `IMP-M8-13`, `15`, `IMP-M8-18` (platform live push), then `16` (suite). No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M8-14` is `DONE` (session 143).** Next: `IMP-M8-12` (friends view, now unblocked), `13`, `15`, `IMP-M8-18` (platform live push), then `16` (suite). No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M8-11` is `DONE` (session 142).** Next: views `12…14`, `15`, then `16` (suite). No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M8-10` is `DONE` (session 141).** Next: views `11…14`, `15`, then `16` (suite). No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M8-17` is `DONE` (session 140).** Next: `IMP-M8-10` (game room, now unblocked); views `11…15` are independent. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-GATE-95` is closed (session 139).** Next: `IMP-M8-17` (backend `viewerRole`), then `IMP-M8-10` (game room). Views `11…14` are independent. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M8-09` is `DONE` (session 138).** Next: view items `10…14`. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M8-08` is `DONE` (session 137).** Next: view items `09…14`. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M8-07` is `DONE` (session 136).** Next: view items `08…14`. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M8-06` is `DONE` (session 135).** Next: `IMP-M8-07` (login/register), then view items `08…14`. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M8-05` is `DONE` (session 134).** Next: view items `06…14` in parallel. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M8-04` is `DONE` (session 133).** Next: `IMP-M8-05`; view items `06…14` in parallel. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M8-03` is `DONE` (session 132).** Next: `IMP-M8-04`, `05`; view items `06…14` in parallel. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M8-02` is `DONE` (session 131).** Next: `IMP-M8-03`, `04`, `05`; view items `06…14` in parallel. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M8-01` is `DONE` (session 130).** Next: `IMP-M8-02` (friends 500), `03`, `04`, `05`; view items `06…14` in parallel. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**Milestone M8 is open (session 129), all 16 items `READY`.** Start with `IMP-M8-01` and `IMP-M8-02` (the 500s), then `03`, `04`; the view items `06…14` can run in parallel with them. `IMP-M8-10` opens with a `spec-defect` on which route may enrol a visitor. Ignore older notes below.

**`IMP-M7-13` is `DONE` (session 128).** No item is `PARTIAL` or `BLOCKED`; see the item's follow-ups (friends endpoint 500 first). Ignore older notes below.

**`IMP-M7-13` is `PARTIAL` (session 127).** It is the last item: pick it up first — its `**Remaining:**` line starts with the intermittent blank game frame. Ignore older notes below.

**`IMP-M7-12` is `DONE` (session 126).** Next: `IMP-M7-13` (acceptance suite) — the last item. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M7-11` is `DONE` (session 125).** Next: `IMP-M7-12`, then `13` (acceptance suite) last. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M7-10` is `DONE` (session 124).** Next: `IMP-M7-11`, `12`, then `13` (acceptance suite) last. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M7-09` is `DONE` (session 123).** Next: `IMP-M7-10…12`, then `13` (acceptance suite) last. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M7-08` is `DONE` (session 122).** Next: `IMP-M7-09…12`, then `13` (acceptance suite) last. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M7-07` is `DONE` (session 121).** Next: `IMP-M7-08…12`, then `13` (acceptance suite) last. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M7-04` is `DONE` (session 120).** Next: `IMP-M7-07…12`, then `13` (acceptance suite) last. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M7-03` is `DONE` (session 119).** Next: `IMP-M7-04` (chat), `07…12`, then `13` (acceptance suite) last. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M7-02` is `DONE` (session 118).** Next: `IMP-M7-03` (in-game/results views, iframe mount), then `IMP-M7-04`, `07…12`, `13` last. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M7-01` is `DONE` (session 117).** Next: `IMP-M7-02 → 03` (lobby, in-game views), then `IMP-M7-04`, `07…12`, `13` last. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M7-06` is `DONE` (session 116).** Next: `IMP-M7-01 → 02 → 03` (room views), then `IMP-M7-04`, `07…12`, `13` last. No item is `PARTIAL` or `BLOCKED`. Ignore older notes below.

**`IMP-M7-05` is `DONE` (session 115).** Start with `IMP-M7-06` (backend defect the room views will surface), then
`IMP-M7-01 → 02 → 03` (the room views — the MVP is not playable without them), then `IMP-M7-04`,
`07…12`, and `IMP-M7-13` last as the acceptance suite. No item is `PARTIAL` or `BLOCKED`. Ignore
older notes below.

**`IMP-M3-10` is `DONE` (session 113).** No item is `PARTIAL`; check the registry for `READY` items. Ignore older notes below.

**`IMP-M3-10` is `PARTIAL` — continue it first**, from its `**Remaining:**` line: build `make reset-db`/`make seed` so a clean reset lists the game. `TURNBASE_SDK_PAT` on the game repo is a human action (game CI red until then). No other item is `READY`. Ignore older notes below.

**`IMP-M3-10` is `PARTIAL` — continue it first.** Build the Game Host heartbeat/`ReportContexts`/`Deregister` loop, then run `e2e-roundtrip.mjs` and the Tempo check; `TURNBASE_SDK_PAT` on the game repo is a human action. No other item is `READY`.

**`IMP-M6-05` is `DONE` (session 109).** Only `IMP-M3-10` (creates a sixth repo) is `READY`. Ignore older notes below.

**`IMP-M6-06` is `DONE` (session 108).** No item is `PARTIAL`; `IMP-M3-10` (creates a sixth repo) and `IMP-M6-05` are `READY`.

**`IMP-M6-06` is `PARTIAL` — continue it first** (notifications panel; see its `**Remaining:**` line). `IMP-M3-10`
(creates a sixth repo), `IMP-M6-05` are `READY`.

**`IMP-M3-11` is `DONE` (session 106).** `IMP-M3-10`, `IMP-M6-06`, `IMP-M6-05` are `READY`.

**`IMP-M3-11` is `PARTIAL` — continue it before anything else** (see its `**Remaining:**` line; start with the
WebSocket/STOMP server choice for clause 4).

**`IMP-M3-13` is `DONE` (session 103).** Do **`IMP-M3-11`** (GDK test harness) next — its dependency is
now met. `IMP-M3-10`, `IMP-M6-06`, `IMP-M6-05` are also `READY`.

**`IMP-GATE-91` closed (session 102).** Do **`IMP-M3-13` before `IMP-M3-11`.** `IMP-M3-10`, `IMP-M6-06`,
`IMP-M6-05` are also `READY`.

**`IMP-M5-04` is `DONE` (session 101).** `IMP-M6-06`, `IMP-M3-10`, `IMP-M3-11`, `IMP-M6-05` are `READY`.

**`IMP-M5-02` is `DONE` (session 100).** `IMP-M5-04`, `IMP-M6-06`, `IMP-M3-10`, `IMP-M3-11`, `IMP-M6-05` are `READY`.

**`IMP-GATE-90` closed (session 99).** `IMP-M5-02` is `READY` — build the two reads from `statistics-rest-api.md`; the writer exists.

**`IMP-M5-01` is `DONE` (session 98).** `IMP-M5-02`, `IMP-M5-04`, `IMP-M6-06`, `IMP-M3-10`, `IMP-M3-11`, `IMP-M6-05` are `READY`.

**`IMP-M3-09` is `DONE` (session 97).** `IMP-M3-10`, `IMP-M3-11`, `IMP-M5-01`, `IMP-M6-05` are `READY`.

**`IMP-M3-08` is `DONE` (session 96).** `IMP-M3-09` (failure handling: `ACTION_REJECTED`, retry-limit
caller), `IMP-M3-10`, `IMP-M3-11`, `IMP-M6-05` are `READY`.

**`IMP-M3-07` is `DONE` (session 95).** `IMP-M3-08`, `IMP-M3-09`, `IMP-M3-10`, `IMP-M3-11`,
`IMP-M6-05` are `READY`.

**`IMP-M3-06` is `DONE` (session 94).** `IMP-M3-07` (effect fan-out; also owns the `game.*`
subscription authorizer) is next; `IMP-M3-08`, `IMP-M3-10`, `IMP-M3-11` are also `READY`.

**`IMP-M3-05` is `DONE` (session 93).** `IMP-M3-06` (input outbox and the `GAME_ACTION` admission
handler) and `IMP-M3-08` are now `READY`; `IMP-M3-10` (first official game) also carries the Tempo
trace check. Ignore the older `IMP-M3-05` notes below.

**`IMP-M3-05` is `PARTIAL` — continue it before anything else.** Its `**Remaining:**` line in
`registry.md` lists what is owed. First, the two end-to-end checks (`Register` <= 60 s, and one
trace in Tempo), run against `IMP-M0-07`'s compose stack. Second, decide whether `ACTION_REJECTED`
and host reassignment on `UNAVAILABLE` belong to this item or to `IMP-M3-06`/`IMP-M3-08`.
The old e2e CI failure noted further down (`compose-platform-1` exit 1) may be the first thing in
the way.

**`IMP-GATE-87` opened and closed (session 90, `IMP-M3-05`) — `IMP-M3-05` is `READY`, build it
next.** Read the new `game-host-internals.md` §11/§13 material first. Risk not settled by the gate:
`local-environment.md` §7.8 says `GameHostRegistryService` shares the monolith's HTTP listener
(`platform:8080`), so it needs gRPC-over-servlet on Tomcat with h2c, including the bidi `Heartbeat`
stream — spike that before building the rest. The item is large (registry server, dispatch client,
real `GameSessionStarter`, `/play/{sessionId}`, two cross-repo e2e checks); consider building the
registry server and its Game Host round trip first.

**`IMP-M3-04` is `DONE` (session 89) — 49 of 62. `IMP-M3-05` (Orchestration client and session
registry, `turnbase-platform`) is `READY` for the first time** — all three of its dependencies
(`IMP-M3-04`, `IMP-M2-04`, `IMP-M2-06`) are now `DONE`. This is the natural next pick: it's the item
that replaces `PendingGameSessionStarter` with a real implementation, gives `START_GAME` its
`GAME_STARTED` broadcast, and is what nearly all of M2/M3's prior sessions have been converging
toward. Its own read-list will name the actual gRPC client surface against `GameHostService`, now
real rather than `UNIMPLEMENTED`.

**Two things `IMP-M3-04` deliberately left unbuilt, recorded in `registry.md`'s Scope note, not
gated — pick up only if a future item's own *Done when* actually needs them:** (1) no
watchdog/timeout mechanism for a hung game handler (§12) — only in-band exceptions map to
`GameFailureKind`; (2) `ArtifactCache.pin`/`unpin` (`IMP-M3-02`) still isn't wired to
`GameContextManager` (`IMP-M3-03`), so FR-LOAD-004 (never evict a JAR backing a live context) isn't
enforced.

**Worth a dedicated look, not gated to any item: `turnbase-game-host`'s `build.yml` was missing
`-Pintegration` on the Verify step** (fixed session 89) — the entire `*IT` suite never ran in CI
before this, for any item, back to whenever the first `*IT` class was added. Nothing else currently
suggests other repos have the same gap (`turnbase-platform`'s has always carried it;
`turnbase-common`/`turnbase-sdk`/`turnbase-frontend` not re-checked this session), but it's the kind
of thing worth one more look before assuming it's isolated.

**Deferred by `IMP-M6-04` (session 85): the room-view page components still need building.** STOMP
client and rooms API layer are done and tested (`useRoomConnection`, `openRoomConnection`, `roomsApi`),
but no page composes them yet — `VW-ROOMS` (rooms list, including the `IMP-GATE-84` reconnection card,
still unpopulated server-side), `VW-JOIN`, `VW-RLOBBY`, `VW-RGAME`, `VW-RRESULT`, and `in-room-chat.md`
FR-CHAN/FR-SWITCH (channel switching UI). Check whether a follow-up item already exists in the
registry for this slice before opening a new one — `IMP-M6-04`'s own *Satisfies* still lists these
VW-*/FR-CHAN/FR-SWITCH IDs even though its *Done when* doesn't require them, so registry hygiene may
need a pass here too.

**`reservedSlot` (from `IMP-GATE-84`) is defined in `room-rest-api.md` §3 but not yet populated by the
backend.** `IMP-M2-01`/`IMP-M2-07` (both `DONE`) don't write it — a future session should wire it
there before the rooms-list reconnection card (VW-ROOMS-005) can render anything real.

**`IMP-GATE-85` opened and closed (session 85, `IMP-M6-04`)** — no document named how a browser's
native `WebSocket` (which cannot set handshake headers) carries the `X-TurnBase-Room-Instance` hint
forward. Fixed: `room-websocket.md` names `/ws?instance={podId}`, a query parameter, as the mechanism.

**`IMP-GATE-84` opened and closed (session 85, `IMP-M6-04`)** — `shell-architecture.md` §8 required
the `/rooms` reconnection pinned card to be "driven by a field on the rooms list response" that
`room-rest-api.md` never defined. Fixed: `room-rest-api.md` §3 gained a `reservedSlot` envelope field.
The backend (`IMP-M2-01`/`IMP-M2-07`, both `DONE`) does not populate it yet — a future session should
wire it there; `IMP-M6-04`'s own pinned-card rendering (VW-ROOMS-005) is deferred until it does, since
that field isn't in this item's *Done when*.

**`IMP-M6-03` is `DONE` (session 84) — 44 of 61.** Account/profile/friends/settings views shipped; see
prior sessions' summaries for scope and the deliberately-deferred statistics/history tabs and
username-search UI. Nothing else changes status as a result: `IMP-M6-04` and `IMP-M6-06` were already
`READY` independently of `M6-03` (session 80's note); `IMP-M6-04` is now `DONE` (above); `IMP-M6-05`
still waits on `IMP-M6-04` — now unblocked. `IMP-M6-03`'s own profile statistics/history tabs stay
blocked on `IMP-M5-01`/`IMP-M5-02` exactly as before — re-open that slice, don't re-open the item, once
either ships.

**`IMP-GATE-82` is closed (session 82) — `IMP-M6-03` is `READY` again, with a written profile-response
contract to build against.** Its own statistics/game-history tabs still need `IMP-M5-01`/`IMP-M5-02`'s
REST surface (not `DONE`) per session 80/81's notes — build those tabs against whatever those items
publish, or leave them for the item that does. The friends-section, uploaded-games-section and core
profile-envelope rendering (owner/guest/private/soft-deleted cases) have no such gap and are fully
startable now.

**`IMP-GATE-81` is closed (session 81) — `IMP-M6-06`'s History tab now has a data source, but the item
is not startable yet.** `IMP-M6-06`'s *Depends on* gained `IMP-M5-01`, which is `READY`, not `DONE` —
per the `work-item` skill's step 1, `IMP-M6-06` cannot actually be picked up until `IMP-M5-01` (game
history recording **and** the new `history-rest-api.md` read endpoint, `turnbase-platform`) is `DONE`.
`IMP-M5-01`'s own dependency `IMP-M3-09` should be checked `DONE` before claiming it. The catalog half
of `IMP-M6-06` (VW-CAT/VW-GDET, `game-catalog.md` FR-CAT/FR-GDET) has no such gap and could be split
out if a future session wants to build only that slice — its own *Done when* clauses don't require the
History tab to exist. `IMP-M6-03` remains `READY` per session 80's note; its own profile
statistics/history tabs have the identical `IMP-M5-01`/`M5-02` dependency, now sharper since
`IMP-M5-01`'s scope is confirmed rather than assumed. `IMP-M6-04` remains `READY` and independent of
both.

**`IMP-GATE-79` is closed (session 79) — `IMP-M3-03` is `READY`, design gap resolved.** The
guest-boundary call interface now carries `entryPointFqcn` end-to-end (`gamehost.proto`
`CreateSessionRequest.entry_point_fqcn`, resolved by Orchestration from the manifest). Actual
implementation is still unstarted and remains large: `turnbase-sdk` half first (root reactor,
`turnbase-serialization` artifact), then `turnbase-game-host` (bridge package, shaded JAR, host shim,
Espresso test) — and the game-host half still needs the `TURNBASE_SDK_PAT` human action below before
it can merge.

**`IMP-M6-03`, `-04` and `-06` are `READY`** now that `IMP-M6-02` is done (`-05` waits on `-04`).
Independent picks unchanged: `IMP-M3-03` (sdk half first; game-host half still
needs the `TURNBASE_SDK_PAT` human action below).

**`IMP-M0-12` is `DONE` — 44 of 61; `IMP-GATE-73` (MinIO image source) is closed.** See *Last Session
Summary*. Two follow-ups, neither gated: (1) CI's `Verify` jobs have no `timeout-minutes`, so a
Testcontainers pull failure retries silently for hours instead of failing fast. Add one (about 40 min;
healthy runs take about 25) in `turnbase-platform` and `turnbase-game-host`. (2) The `pgsty` fork is a
community build: if it ever disappears too, `local-environment.md` §1 is where the next source is named.

**Human action needed before `IMP-M3-03`'s game-host half can merge:** create a fine-grained PAT
(read-only on Contents, scoped to `turnbase-sdk` only) and store it as `TURNBASE_SDK_PAT` on
`turnbase-platform/turnbase-game-host` (`IMP-GATE-70`). An agent cannot do this. It does not block
starting: build the `turnbase-sdk` half first (root reactor so one `./mvnw install` installs
`turnbase-sdk` + `turnbase-serialization`; publish workflow must cover both), merge and push it green,
then do the game-host half locally and merge it only once `gh secret list -R
turnbase-platform/turnbase-game-host` shows the secret and the workflow's new bootstrap step exists.
`IMP-M3-11` now also depends on `IMP-M3-03`, so it cannot start until that is `DONE`.


**`IMP-M3-03` is `READY` again after `IMP-GATE-69`** — start it in `turnbase-sdk` (the
`turnbase-serialization` artifact: publish/install and pin it), then `turnbase-game-host` (bridge
package, shaded bridge jar, host shim, Espresso test through §3.3's entrypoint). Open sub-questions
the spec leaves to the implementer because they are invisible outside the repos: the sdk repo's
directory/module layout, and the bridge manifest attribute carrying the GDK version
(`bundle-format.md` §6.1 requires one but does not name it — if the monolith's startup check
(`turnbase.gdk.supported-range`) is built before this settles, name it in that spec then). `IMP-M3-11`
now also depends on `IMP-M3-03`. Other independently `READY` picks: `IMP-M0-12` (see the seed-data
`SocialService`/`NotificationService` note below).

**`IMP-M3-02` is `DONE` — 43 of 61.** See *Last Session Summary*. Espresso context lifecycle and the
Artifact Store are complete and green in CI. `IMP-M3-03` (GDK host bridge and serialization boundary,
`turnbase-game-host`) is now the natural next pick — its only two dependencies, `IMP-M3-01` and
`IMP-M3-02`, are both `DONE`.

Other independently `READY` picks, unchanged from prior sessions' notes: `IMP-M0-12` (seed data,
`turnbase-platform`, off `M0-06`/`M4-03` — unresolved `SocialService`/`NotificationService`
package-private question, multiple prior sessions stuck here, resolve it explicitly before code),
`IMP-M3-11` (GDK test harness, `turnbase-sdk`, off `M3-01` — large, plan as a multi-part build: CLI
launcher, mock Orchestration/WebSocket bridge, two-origin browser serving, bundle-validator reuse,
multi-player simulation, log rendering).

---

**`IMP-M6-01` is `DONE` — 42 of 61.** See *Last Session Summary*. Astryx integration and the `ui/`
boundary are complete; `src/ui/` stays near-empty until a future item composes or swizzles a real
component into it.

Independently `READY` picks, unchanged from session 64/65's notes: `IMP-M0-12` (seed data,
`turnbase-platform`, off `M0-06`/`M4-03` — unresolved `SocialService`/`NotificationService`
package-private question, two prior sessions stuck here, resolve it explicitly before code),
`IMP-M3-02` (Espresso context lifecycle, `turnbase-game-host`, off `M0-04`), `IMP-M3-11` (GDK test
harness, `turnbase-sdk`, off `M3-01` — large, plan as a multi-part build: CLI launcher, mock
Orchestration/WebSocket bridge, two-origin browser serving, bundle-validator reuse, multi-player
simulation, log rendering).

---

**`IMP-M3-11` (GDK test harness) is `READY` again, scope now fully specified — 41 of 61 unchanged.**
See *Last Session Summary*: `IMP-GATE-67` closed this session, and `IMP-M3-11`'s *Done when* now
covers the whole FR-HARNESS-001…008/010 surface, not just the round trip. It's a genuinely large item
— a CLI launcher, a mock Orchestration/WebSocket bridge, two-origin browser serving, bundle-validator
reuse, multi-player simulation, log rendering — plan for it accordingly rather than as a small pickup.

**`IMP-M0-12` (seed data) remains the other un-gated `READY` item**, and its unresolved design
question is unchanged from session 64's note: `SocialService`/`NotificationService` are
package-private, so the seeder's path into them (real REST surface over `WebClient`, vs. a narrow new
public entry point per feature) needs a deliberate decision before its `ApplicationRunner` is written.
Two prior sessions (62, 63) already got stuck there without landing code — resolve that question
explicitly before writing code, not mid-implementation.

Other independently `READY` picks, unchanged from session 64's note: `IMP-M3-02` (Espresso context
lifecycle, `turnbase-game-host`, off `M0-04`), `IMP-M6-01` (Astryx integration, `turnbase-frontend`,
off `M0-05`).

**`IMP-M3-01` is `DONE` — 41 of 61.** See *Last Session Summary*. `IMP-M0-12` (seed data) is still the
most-recommended next pick — un-gated since `IMP-GATE-66` closed two sessions ago — and can now
optionally use the real `io.turnbase.gdk.TurnBaseGame` interface instead of `TestBundles.java`'s
hand-compiled stub, though no *Done when* clause requires that switch. Its unresolved design question
is unchanged: `SocialService`/`NotificationService` are package-private, so the seeder's path into
them (real REST surface over `WebClient`, vs. a narrow new public entry point per feature) still needs
a deliberate decision before its `ApplicationRunner` is written. `IMP-M3-11` (GDK test harness) is now
`READY` for the first time — its only dependency, `IMP-M3-01`, is `DONE`.

A stale remote branch `feat/imp-m3-01-gdk-backend-api-surface` on `turnbase-sdk`'s origin needs a
manual `git push origin --delete` — the session's permission gate blocked the automated delete (see
*Last Session Summary*). It is already fully merged into `master`; deleting it is cleanup, not a
blocker.

**`IMP-M0-12` (seed data) is `READY`, un-gated, and is the natural next pick.** See *Last Session
Summary* — `IMP-GATE-66` closed this session, `local-environment.md` §6 now excludes all three
notification types (`ROOM_INVITATION`, `GAME_APPROVED`, `GAME_REJECTED`) that the real system cannot
yet produce, and code is all that remains. The bundle-fixture approach `IMP-M4-03`'s own
`TestBundles.java` already uses (a hand-compiled stub `io.turnbase.gdk.TurnBaseGame` interface + a
trivial implementer, since Phase F's checks are structural bytecode analysis, not a real SDK
dependency) is directly reusable for the seed's official-game bundle — no need to wait on `IMP-M3-01`
or `IMP-M3-10`. **Before writing the `ApplicationRunner`, resolve how it reaches `social`/`notification`
at all** — `SocialService` and `NotificationService` are package-private, so either the seeder drives
the real REST surface over `WebClient` against the running app (consistent with §6's "drives the real
pipeline" framing, and with how the bundle upload already has to work: slot → PUT → confirm → poll),
or a narrow public seeding entry point gets added to each feature deliberately, as a real design
decision rather than a boundary worked around in passing.

**`FR-PRV-004` (the game owner's submit-for-review action) is still unclaimed by any item in the
registry** — flagged again this session while diagnosing `IMP-GATE-66`; `IMP-M0-12`'s two now-excluded
notification types (`GAME_APPROVED`/`GAME_REJECTED`) will need it before they can ever be seeded.
Worth assigning to an existing catalog/admin item or opening a small new one.

**`IMP-M4-01` is `DONE` — 40 of 61.** See prior session's summary. `IMP-M3-05` (orchestration
client and session registry) remains the one item this repo's M3/M4 work has been converging on but
still cannot start: its dependency `IMP-M3-04` (gRPC service implementation, `turnbase-game-host`) is
`READY` in the register table, not `DONE` — check the table directly before picking it up, prose in
this file has been wrong about this before (session 58).

Independently `READY` with all dependencies actually confirmed `DONE`: `IMP-M3-01`/`IMP-M3-02` (GDK
backend API surface / Espresso context lifecycle — no other item needed first), `IMP-M6-01` (Astryx
integration, off `IMP-M0-05`). `IMP-M5-01` (game history) needs `IMP-M3-09`, still `READY` — not a
valid pick yet either.

**`FR-PRV-004` (the game owner's submit-for-review action) is unclaimed by any item in the
registry** — surfaced while narrowing `IMP-M4-01`'s over-claimed *Satisfies* this session.
`admin-rest-api.md` §7 explicitly disclaims building it, and no other item's *Satisfies* names it
either. Worth either assigning to an existing catalog/admin item or opening a small new one before it
is forgotten entirely.

**`IMP-M4-01`'s commit landed directly on `turnbase-platform master` without a feature branch first**
— see *Last Session Summary* for the honest account. No cleanup needed (no orphan branch exists), but
worth remembering to create the branch before the first edit next time.

**Still outstanding, not gated to any item — the `e2e` CI job's `NOAUTH HELLO must be called with
the client already authenticated` Redis-auth failure.** Last confirmed identical on session 57's CI
run (`35462118529`) — three sessions in a row hit the exact same cause since it was first diagnosed
in session 56, and it was not re-checked this session (this session's own admin-API work never
touched `e2e`). The fix is likely a missing `SPRING_DATA_REDIS_PASSWORD` in the e2e compose profile's
platform service env, or a Redis image default-auth mismatch. Non-gating (`platform-operations.md`
OQ-002) but worth someone's dedicated turn rather than a further confirmation.

**`IMP-GATE-62` is closed — `IMP-M4-04` is `READY` again, narrowed.** See *Last Session Summary*.
Its scope is now just the `Host`-routing filter and `GET /g/{gameId}/{version}/**`, buildable off
`IMP-M4-03` alone — the natural next pick, and small. `IMP-M3-05` (orchestration client and session
registry) gained the `/play/{sessionId}` bootstrap-document work this gate carved out of `IMP-M4-04`,
plus `IMP-M4-04` in its own *Depends on* — it is not startable until `IMP-M4-04` is `DONE`.
`IMP-M4-05` (admin API — review queue and badges) is still independently `READY` off `IMP-M4-03`.

**`IMP-M4-03` is now `DONE` — 37 of 61.** See prior session's summary. `IMP-M4-04` (bundle publication
and asset serving) and `IMP-M4-05` (admin API — review queue and badges), both `READY` off it, are
the natural next picks — `IMP-M4-05` in particular is where E4's deferred admin-path-detection half
(this session's scope note) has to land, since it's the item that actually builds the loopback-bound
admin auth context. `docs/specs/deployment/local-environment.md` §6's seeded-game item (`IMP-M0-01`
row, depends on `IMP-M4-03`) is also now unblocked. Independently `READY`: `IMP-M3-01`/`M3-02`
(GDK backend API / Game Host skeleton), `IMP-M5-01` (game history, off `IMP-M3-09` — confirm that
dependency is actually `DONE` first), `IMP-M6-01` (Astryx integration, off `IMP-M0-05`).

**Still outstanding, not gated to any item: the `e2e` CI job's `compose-platform-1` exit-`1`
failure — now with a real cause, not just a shape.** This session's captured logs show the platform
container failing Spring context refresh on `RedisRateLimiterConfig`: `NOAUTH HELLO must be called
with the client already authenticated` — the e2e compose profile's Redis instance requires a
password the platform container isn't configured to send. Worth a dedicated look (likely a missing
`SPRING_DATA_REDIS_PASSWORD` in the e2e compose profile's platform service env, or a Redis image
default-auth mismatch) — out of scope for `IMP-M4-03`, which only confirmed the shape matched prior
sessions' non-gating failure before moving on.

**`IMP-M4-02` is now `DONE` — 36 of 61.** See *Last Session Summary*. `IMP-M4-03` (upload pipeline
and version state machine), `READY` off it, is the natural next pick: it's the consumer
`ManifestValidator` was built for, and its own Done-when already names the Phase A–G checks that sit
around this item's Layer 1/2 validation (`bundle-format.md` §3.2).

**`IMP-M5-03` is `DONE` — 35 of 61.** See session 52's summary. Its one deliberate scope gap
(live push of a newly created notification to an already-open stream isn't wired for the two existing
producers, `room.RoomInvitationRepository` and `social.SocialRepository`) is recorded there, not
gated — pick it up only if a future item's own Done-when actually needs it.

**Independently `READY` next picks:** `IMP-M3-01`/`IMP-M3-02` (GDK backend API surface / Game Host
skeleton, `turnbase-sdk`/`turnbase-game-host`), `IMP-M4-01` (catalog listing), `IMP-M4-03` (upload
pipeline, above), `IMP-M5-01` (game history recording, off `IMP-M3-09` — check that dependency is
actually `DONE` before claiming), `IMP-M6-01` (Astryx integration, `turnbase-frontend`, off
`IMP-M0-05`). `IMP-M5-04` (retention purge jobs) is **not** yet startable: it depends on `IMP-M5-01`,
still `READY`, not `DONE`.

**Still outstanding, not gated to any item: the `e2e` CI job's `compose-platform-1` exit-`1` failure.**
Unrelated to notifications — this session's `build` run (`34883859139`) was green, `e2e` failed on the
same shape flagged since session 50/51. Read a recent run's `docker compose logs` output (captured
since session 50's fix) before diagnosing further.

**`IMP-M2-12` is now `DONE` — 34 of 61, and M2 is fully complete.** See *Last Session Summary*.
**`IMP-M5-03`** (notifications and the SSE stream), `READY` off `IMP-M1-06, IMP-M1-07` (both `DONE`),
is the natural next pick: it builds the real `NotificationEmitterRegistry`/SSE dispatch that
`notification.PendingAlertPublisher` (this session's no-op seam) is waiting to be replaced by, and
`IMP-M2-12`'s two alert types (`INVITATION_ACCEPTED`/`INVITATION_DECLINED`) plus the four
`FRIEND_REQUEST*`/`FRIEND_ADDED` notification types `IMP-M1-09` already writes are all ready
consumers with no wiring of their own left to do. Otherwise, fully independent tracks are open:
`IMP-M3-01` (GDK backend API surface, `turnbase-sdk`) and `IMP-M3-02` (Espresso context lifecycle,
`turnbase-game-host`) need no other repo's work first; `IMP-M4-01`/`M4-02` (catalog listing, manifest
validation, `platform`) are `READY` off `M1-01`/`M0-06`; `IMP-M6-01` (Astryx integration,
`turnbase-frontend`) is `READY` off `M0-05`.

**Still outstanding, not this session's to fix:** `turnbase-platform`'s stale merged remote branch
`feat/imp-m2-10-reconciliation` — three sessions' sandboxes in a row have denied remote-push
permission for the delete; needs a human or a session with that permission.

**`IMP-M2-08` is now `DONE` — 31 of 61.** `IMP-M2-09` (Room closure and the five detach paths —
including `detachSession`'s real implementation, replacing the `PendingRoomSessionDetacher` stub
`IMP-GATE-49` left) is `READY` off it and the natural next pick. `IMP-M2-10` (Adoption and
reconciliation jobs) is `READY` off `IMP-M2-03` independently; `IMP-M2-12` (room invitations) is
`READY` off `IMP-M2-01, IMP-M1-09` independently. The `minio` pull failure (`IMP-GATE-52`) is fixed —
no infra blocker remains for any of them.

**`IMP-M2-07` is now `DONE` — 30 of 61.** `IMP-M2-08` (Reconnect and resync) and `IMP-M2-09` (Room
closure and the five detach paths — including `detachSession`'s real implementation, replacing the
`PendingRoomSessionDetacher` stub `IMP-GATE-49` left) are both `READY` off it and are the natural
next picks. `IMP-M2-10` (Adoption and reconciliation jobs) is `READY` off `IMP-M2-03` independently.
`IMP-M2-12` (room invitations) remains `READY` off `IMP-M2-01, IMP-M1-09` independently.

Two things worth knowing before picking up `IMP-M2-09`: it inherits `IMP-M2-07`'s two call sites
(duty 1 step 4, duty 2's closure half) rather than writing its own, and `notifications-invitations.md`
FR-INV-008's invitation deletion belongs inside `detachSession` itself (`data-model.md` §1's Closure
reasons section — "every one of these five paths owes the same two side effects"), not bolted onto
each of its three additional callers separately.

A discovered-but-out-of-scope orphan, worth a look before `IMP-M2-08`/`M2-09` land: `game-rooms.md`
FR-XFER-001 (automatic host transfer on an ordinary voluntary leave, not a disconnect) does not
appear in any item's current *Satisfies* — `IMP-M2-06` dropped it, `IMP-M2-09` only claims
FR-XFER-002/005. `RoomService#leave` (the REST/voluntary path) still has no host-transfer logic at
all. Not gated this session since nothing in `IMP-M2-07`'s own Done-when touches it, but it will
surface the next time someone builds or tests a host voluntarily leaving a room with other players
still in it.

**`IMP-M2-11` is now `DONE` — 29 of 61.** `IMP-M3-05` (orchestration client and session registry — the
item that replaces `PendingGameSessionStarter` with a real implementation and gives `START_GAME` its
`GAME_STARTED` broadcast), `READY` off `IMP-M3-04, IMP-M2-04, IMP-M2-06`, is the natural next pick once
its own game-host dependency (`IMP-M3-04`) is ready; until then, `IMP-M2-07` (disconnect, grace
deadlines, sweeps) and `IMP-M2-10` (adoption and reconciliation jobs), both `READY` off `IMP-M2-03`
independently, and `IMP-M2-12` (room invitations), `READY` off `IMP-M2-01, IMP-M1-09` independently,
remain the pickable items that need no other repo's work first.

**IMP-GATE-45** (`IMP-M2-05`, opened and closed 2026-09-09, session 40) — `room-websocket.md`'s
Member Commands table states a role precondition for `TOGGLE_READY`/`SWITCH_TO_SPECTATOR` (non-host
human player) and `SWITCH_TO_PLAYER` (spectator), but the error-code registry — which claims to be
"the registry for every WebSocket error code in the corpus" — had no code for violating it. Fixed:
`room-websocket.md` gained `ROLE_NOT_ELIGIBLE` and a note that the *Authorized sender* column is
server-enforced. `IMP-M2-05` is now `DONE`.

**IMP-GATE-43** (`IMP-M2-04`, opened and closed 2026-09-09, session 40) — `IMP-M2-04`'s own read-list
(`room-websocket.md`'s versioning section) and `IMP-M2-01`'s own read-list (`room-rest-api.md` §5)
both require `PLAYER_JOINED`/`PLAYER_LEFT` to be broadcast, version-stamped, from the REST join/leave
transactions — but `IMP-M2-01` (`DONE`) shipped without it, because the lock-scoped
commit-then-publish executor those sentences presuppose is exactly what `IMP-M2-04` builds, and it
didn't exist yet. Fixed: `IMP-M2-04`'s *Depends on* gains `IMP-M2-01`, its read-list gains
`room-rest-api.md` §5–§6, and its *Done when* gains the two broadcast clauses; `IMP-M2-01`'s section
gained a note naming `IMP-M2-04` as the owner.

**IMP-GATE-44** (`IMP-M2-04`, opened and closed 2026-09-09, session 40) — `room-rest-api.md` §5
documented the Redis claim running *after* the join transaction commits, but `room-lifecycle.md` §2.1
and `room-websocket.md`'s versioning section require "lock outer → transaction inner → publish after
commit," and §2.1 says a stalled database blocks REST joins on the *same* lock a STOMP command uses —
only true if the lock is acquired before the mutation, not after. Fixed: `room-rest-api.md` §5's claim
moves to step 0, before the transaction; §6 (leave, which never claimed at all before) gained the
matching claim/lock/version/broadcast paragraph, with a failed claim skipping the broadcast rather
than failing the request (leave's existing text already accepted running unclaimed).

**`IMP-M2-04` is now `DONE` — 26 of 61.** `IMP-M2-05` (join, teams, readiness), `READY` off
`IMP-M2-04` alone, is now unblocked and the natural next pick — it builds its STOMP command handlers
against the `RoomEventExecutor` this item just shipped. `IMP-M2-07` (disconnect, grace deadlines,
sweeps) and `IMP-M2-10` (adoption and reconciliation jobs) are `READY` off `IMP-M2-03` independently;
`IMP-M2-12` (room invitations) is `READY` off `IMP-M2-01, IMP-M1-09` independently. `IMP-M2-06`
(host management and transfer) and `IMP-M2-11` (in-room chat) both wait on `IMP-M2-05`.

**`IMP-M2-02` is `DONE` — 25 of 61.** STOMP endpoint, auth, subscriptions, `turnbase-platform`,
pushed and green in CI (see Last Session Summary). Nothing else in the registry names `IMP-M2-02` as
a dependency, so its completion does not itself move any other item to `READY` — `IMP-M2-04` and
`IMP-M2-12` were already `READY` independently of it (below) and remain the natural next picks; the
room member/host command handlers `IMP-M2-05`/`M2-06`/`M2-11` need `IMP-M2-04`'s event
versioning/fan-out first, not this item.

**`IMP-M2-04`** (room event versioning and fan-out) is `READY` off `IMP-M2-03` alone — it is the
mechanism `IMP-M2-01`'s own leave/host-transfer gaps (deferred `lost_announced_at` tails, broadcast)
are waiting on, and the natural next pick: it is what turns `room-websocket.md`'s per-room `version`
counter and delta-publish-under-lock into a real component, which `IMP-M2-05` (join/teams/readiness)
then builds its command handlers against. **`IMP-M2-12`** (room invitations) is `READY` off
`IMP-M2-01, IMP-M1-09` independently.

**IMP-GATE-41** (`IMP-M2-01`, opened and closed 2026-09-08, session 38) — this item's read-list never
named `docs/specs/platform/data-model-catalog.md`, though `room-rest-api.md`'s create transaction and
its §3 listing predicate both depend on it: the three room-creation preconditions (FR-GAME-013,
FR-GAME-007, FR-PRV-002 — deleted/archived/listed/badge on `game`) were never stated, and the
`canJoin`/`canSpectate` predicate and row shape (FR-LIST-002, FR-LIST-003a) need
`game_version.min_players`/`.max_players`/`.supports_ai`/`.supports_spectators`/
`.supports_mid_game_join` — columns that document alone supplies. Also fixed a naming defect this
exposed: `room-rest-api.md` wrote `game.capabilities.midGameJoin`/`.spectating`, matching neither
`manifest-schema.md`'s real field (`capabilities.spectators`, not `.spectating`) nor the persisted
column (`game_version.supports_spectators`). Fixed: `room-rest-api.md` §2/§3/§5 now name
`gameVersion.supports_mid_game_join`/`.supports_spectators` and cite `data-model-catalog.md` §2; §2's
`gameId` row states the three preconditions explicitly; *Related* gained the citation; `IMP-M2-01`'s
read-list gained `data-model-catalog.md` §1–§2. **`IMP-M2-01` is `WIP` (session 38) and code is
next.**

**IMP-GATE-40** (`IMP-M2-01`, opened and closed 2026-09-08, session 37) — this item's Done-when clause
5 needs the room-ownership claim/redirect/`503` mechanism that `IMP-M2-03` builds, but `IMP-M2-03`
depended on `IMP-M2-02`, which depended on `IMP-M2-01` — a cycle in substance. `IMP-M2-04`, `IMP-M2-07`
and `IMP-M2-10` already depend on `IMP-M2-03` directly and needed no change. Fixed: `IMP-M2-03`'s
*Depends on* moves to `IMP-M1-06`; `IMP-M2-01`'s gains `IMP-M2-03`; `IMP-M2-02`'s gains `IMP-M2-03`
alongside `IMP-M2-01`. **`IMP-M2-03` is now the item to build first** — `IMP-M2-01` and `IMP-M2-02`
both wait on its claim component. `IMP-M2-01` is back to `READY` (not `WIP`) pending `IMP-M2-03`.

**IMP-GATE-39** (`IMP-M2-01`, opened and closed 2026-09-08, session 37) — this item's read-list never
named `docs/specs/platform/room-lifecycle.md`, though `room-rest-api.md` (its own read-list document)
cites it repeatedly for the ownership-claim mechanism behind Done-when clause 5 and the host-leave
delegation boundary in §6. Separately, `room-rest-api.md` builds FR-JOIN-007, FR-XFER-003 and
FR-HOST-002 entirely in this item's own REST endpoints, but this item's *Satisfies* claimed none of
them while `IMP-M2-05` and `IMP-M2-06` each claimed one anyway, over a STOMP-layer read-list that
never touches the REST handlers that actually build them. Fixed: `IMP-M2-01`'s read-list gained
`room-lifecycle.md` §1.2–§1.4, §1.7 and part of §4; its *Satisfies* gained FR-JOIN-007, FR-XFER-003,
FR-HOST-002; `IMP-M2-05`'s *Satisfies*/*Done when* dropped FR-JOIN-007; `IMP-M2-06`'s *Satisfies*
dropped FR-HOST-002 and FR-XFER-003. Superseded by `IMP-GATE-40` before any `IMP-M2-01` code was
written — see above.

**IMP-GATE-37** (`IMP-M1-10`, opened and closed 2026-09-08, session 36) — no document named the
JSON/redirect REST surface this item builds (the OAuth-initiate route, the pending-registration JSON
endpoints, the FR-AUTH-016 challenge-and-link endpoint), and the item's read-list never named
`rest-conventions.md` either. Same shape as IMP-GATE-31/33/35. Fixed: new
`docs/specs/api-design/oauth-rest-api.md` — five endpoints, the `turnbase_oauth_pending` cookie, two
new `local-environment.md` §7.4 TTL properties; `rate-limiting.md` Tier 1 gained the link-challenge
route and Tier 5's OAuth row now names its exact enforcement point; read-list corrected. `IMP-M1-10`
is back to `WIP` and code is next.

**IMP-GATE-38** (`IMP-M1-10`, opened and closed 2026-09-08, session 36) — `user-accounts.md`
NFR-SEC-006 never named this item's five endpoints as session-exempt (same shape as IMP-GATE-29).
Fixed: NFR-SEC-006 now names all five; read-list corrected.

**M1 is fully DONE, and `IMP-M2-03` now too — 23 of 61.** `IMP-M2-01` (room CRUD and listing) is
`READY` off `IMP-M1-06, IMP-M2-03` (`IMP-GATE-40` corrected the second dependency) — this is the next
pick. Its listing predicate needs a `friendship` join for `FRIENDS_ONLY` rooms, which `IMP-M1-09`
supplies; its Done-when clause 5's `503`/redirect/affinity-header behaviour now has
`room.RoomOwnershipService.claim()` to call. `IMP-M2-02` (STOMP endpoint) is `READY` off
`IMP-M2-01, IMP-M2-03` once `IMP-M2-01` lands. `IMP-M2-12` (room invitations) is `READY` off
`IMP-M2-01, IMP-M1-09`. `IMP-M5-03` (notifications and the SSE stream) is `READY` off
`IMP-M1-06, IMP-M1-07` — it now delivers the `notification` rows this item writes over SSE, rather
than writing any of its own for friend requests (`IMP-GATE-34`).

**IMP-GATE-35** (`IMP-M1-09`, opened and closed 2026-09-08, session 34) — no document in the corpus
ever defined this item's REST surface. `rest-conventions.md`'s Authorization table has named the
`/api/friend-requests/{id}` ownership predicate since it was written, but nothing supplied the
endpoints it governs, and this item's read-list never named `rest-conventions.md` either. Same shape
as `IMP-GATE-31`/`33`, at the scale of a whole feature rather than one route. Fixed: new
`docs/specs/api-design/social-rest-api.md` — seven endpoints (username search, send, list, accept,
cancel/decline, friend list, unfriend) plus a `relationshipState` extension to `GET
/api/users/{username}` for FR-SOC-016; registered in that directory's `INDEX.md`; read-list corrected.

**IMP-GATE-34** (`IMP-M1-09`, opened and closed 2026-09-08, session 34) — the item's *Satisfies*
claimed `notifications-invitations.md` FR-FREQ-001…006 in full, and `IMP-M5-03` independently claimed
the identical full range, but neither item's *Done when* clause tested the other's overlap — this
item's never mentioned notifications, and `IMP-M5-03`'s tested only the generic retention/alert
mechanics. `data-model-notifications.md` §3's type table settles it: the four
`FRIEND_REQUEST*`/`FRIEND_ADDED` rows are written at the moment a `friend_request` is created,
accepted, or declined — this item's own transactions. Same shape as `IMP-GATE-28`, in reverse: there
the generic item over-claimed; here it does too, but in the opposite direction (the specific producer
is `IMP-M1-09`, not the infrastructure item `IMP-M5-03`). Fixed: `IMP-M5-03`'s *Satisfies* narrowed to
drop FR-FREQ-001…006; `IMP-M1-09` keeps the claim, its *Done when* gained explicit notification-write
clauses for send/accept/decline/cancel, and its read-list gained `data-model-notifications.md` §1/§3.

**IMP-GATE-33** (`IMP-M1-08`, opened and closed 2026-09-08, session 33) — no document named a route
for FR-ACCT-004 itself (the deletion trigger); `rest-conventions.md`'s self-scoped account routes
named the identity, password and privacy mutations but nothing that deletes the account, and
`IMP-M1-08`'s read-list never named `rest-conventions.md`. Same shape as `IMP-GATE-31`. Fixed:
`rest-conventions.md` gained `DELETE /api/users/me` — `204`, clears the session cookie and closes live
connections per `FR-SESS-010`, no confirmation step at the API layer; read-list corrected.

**IMP-GATE-32** (`IMP-M1-08`, opened and closed 2026-09-08, session 33) — the item's *Satisfies*
claimed the full `FR-ACCT-004…010` range, but `FR-ACCT-009` (deleted-profile placeholder) and
`FR-ACCT-010` (password change) are already implemented and claimed by `IMP-M1-07`, and neither
appears in `IMP-M1-08`'s own *Done when* clause. Same shape as `IMP-GATE-08`/`18`/`28`/`30`. Fixed:
narrowed to `FR-ACCT-004…008`, the erasure duties this item actually builds.

**IMP-GATE-31** (`IMP-M1-07`, opened and closed 2026-09-08, session 32) — no document in the corpus
named a route for FR-ACCT-002 (username update) or FR-ACCT-003 (email update); `rest-conventions.md`'s
self-scoped account routes named the password and privacy endpoints but nothing for these two, and
`IMP-M1-07`'s own read-list never named `rest-conventions.md` at all despite it supplying the
routes/status codes for every endpoint the item builds. Fixed: `rest-conventions.md` gained
`PATCH /api/users/me` — one endpoint for both fields, each enforcing its own rolling 30-day window
independently, email rejected outright when OAuth-sourced (FR-AUTH-008/012); read-list corrected.

**IMP-GATE-30** (`IMP-M1-05`, opened and closed 2026-09-08, session 31) — `IMP-M1-05`'s *Satisfies*
claimed the full `FR-GUEST-001…010` range, but FR-GUEST-010 (guest profile display) needs a
`GET /api/users/{username}` endpoint that doesn't exist until `IMP-M1-07`, which was never a
dependency here — and `user-accounts.md` FR-PROF-002 states the identical duty under a different ID
in the same document, a duplicate `docs/requirements/INDEX.md` doesn't track since it only lists
cross-document prefix collisions. Same shape as `IMP-GATE-08`/`IMP-GATE-18`/`IMP-GATE-28`. Fixed:
`IMP-M1-05` narrowed to `FR-GUEST-001…009`; `IMP-M1-07`'s *Satisfies* gained `FR-GUEST-010` alongside
its existing `FR-PROF-002`.

**IMP-GATE-29** (`IMP-M1-05`, opened and closed 2026-09-08, session 31) — `user-accounts.md`
NFR-SEC-006's exempt list named the login and registration endpoints but not guest creation, even
though `rest-conventions.md`'s Authentication section derives its own "except" set from that exact
list and separately states `POST /api/auth/guest` is unauthenticated outright, matching
`rate-limiting.md`'s Tier 5 text — and a caller minting a guest account has no session yet by
definition. Fixed: NFR-SEC-006 now names the guest-creation endpoint, with the reason inline.
`IMP-M1-05`'s read-list also gained `rest-conventions.md` § Authentication, which named the endpoint
itself and was missing.

**Phase 1 is under way. Work from [`docs/implementation/INDEX.md`](docs/implementation/INDEX.md), not
from this file.** The registry holds **61 live work items** (IMP-M6-07 is cancelled), each with a
read-list, dependencies, the requirement IDs it satisfies and a done-when clause; this section only
says which of them to pick up.

**IMP-GATE-26** (`IMP-M1-04`, opened and closed 2026-09-06, session 29) — the item's *Satisfies*
claimed the full `FR-AUTH-001…016` range, including six OAuth-only requirements
(`FR-AUTH-007…012, 016`) and `VW-OAUTHCOMP-001…002`, but its *Done when* clause never mentioned OAuth
and its read-list didn't even carry the document naming the OAuth client secret's config key.
Fixed: `IMP-M1-04` retitled *Credential registration and login* and narrowed to `FR-AUTH-001…006, 011,
013…015`; the OAuth round trip (consent redirect, code exchange, signed `state`, the FR-AUTH-016
email-collision challenge-and-link path) is new item **`IMP-M1-10`**, `READY` off `IMP-M1-04`, which
is now `DONE` (see *Last Session Summary*).

**IMP-GATE-28** (`IMP-M1-06`, opened and closed 2026-09-08, session 30) — `IMP-M1-06`'s *Satisfies*
claimed `FR-SESS-010` in full, but its actual duty (closing a session's live WebSocket/SSE connections
on revocation) needs a connection registry that doesn't exist yet — `IMP-M2-02` and `IMP-M5-03` are
both still `READY`, and `IMP-M5-03` didn't claim `FR-SESS-010` at all despite SSE being one of the two
connection types the requirement names. Fixed: `IMP-M1-06` narrowed to `FR-SESS-001…004, FR-SESS-011`
plus publishing a `SessionRevokedEvent`; `IMP-M2-02` and `IMP-M5-03` each gained the corresponding
close-on-revocation `Done when` clause (`IMP-M5-03` also gained `FR-SESS-010` in *Satisfies* and
`IMP-M1-06` as a dependency, for the event type).

**IMP-GATE-27** (`IMP-M1-04`, opened and closed 2026-09-06, session 29) — no document in the corpus
named the session cookie itself, only its `httpOnly`/`Secure`/`SameSite=Strict` properties
(`user-accounts.md` CON-004); `rest-conventions.md`'s Authentication section, the natural home, was
also missing from `IMP-M1-04`'s read-list. Fixed: `rest-conventions.md` now names it —
`turnbase_session`, `Path=/` — as a fixed constant every server-side reader (the future STOMP
handshake, SSE endpoint, and any authenticated-route filter) must agree on; read-list corrected.

**IMP-GATE-30** (`IMP-M1-05`, opened and closed 2026-09-08, session 31) — `IMP-M1-05`'s *Satisfies*
claimed the full `FR-GUEST-001…010` range, but FR-GUEST-010 (guest profile display) needs a
`GET /api/users/{username}` endpoint that doesn't exist until `IMP-M1-07`, which was never a
dependency here — and `user-accounts.md` FR-PROF-002 states the identical duty under a different ID
in the same document, a duplicate `docs/requirements/INDEX.md` doesn't track since it only lists
cross-document prefix collisions. Same shape as `IMP-GATE-08`/`IMP-GATE-18`/`IMP-GATE-28`. Fixed:
`IMP-M1-05` narrowed to `FR-GUEST-001…009`; `IMP-M1-07`'s *Satisfies* gained `FR-GUEST-010` alongside
its existing `FR-PROF-002`.

**IMP-GATE-29** (`IMP-M1-05`, opened and closed 2026-09-08, session 31) — `user-accounts.md`
NFR-SEC-006 enumerated the endpoints exempt from session authentication ("the landing page, the login
endpoint, the registration endpoint, user profile pages, the game catalog, game detail pages") and
omitted guest creation, but `rest-conventions.md`'s Authentication section derives its own "except"
set from that exact list, and separately states `POST /api/auth/guest` is "an unauthenticated `POST`"
outright, matching `rate-limiting.md`'s Tier 5 text. A caller minting a guest account has by
definition no session yet. Fixed: NFR-SEC-006 now names the guest-creation endpoint, with the reason
inline. `IMP-M1-05`'s read-list also gained `rest-conventions.md` § Authentication, which named the
endpoint itself and was missing.

**Before starting any of them: no pull requests** (ADR-0012, amended 2026-09-05). Branch, build,
merge to `master`, delete the branch — all within one session. Dependabot is frozen, so nothing
arrives on its own any more; a dependency bump is now an ordinary change on an ordinary branch.

**Progress: 24 of 61 done** — `IMP-M0-01` (gRPC stubs, `turnbase-common`), `IMP-M0-02` (SDK
build-and-publish floor, `turnbase-sdk`), `IMP-M0-03` (Platform Monolith skeleton,
`turnbase-platform`), `IMP-M0-04` (Game Host skeleton, `turnbase-game-host`), `IMP-M0-05`
(Frontend skeleton, `turnbase-frontend`), `IMP-M0-06` (Flyway baseline, `turnbase-platform`),
`IMP-M0-07` (local stack compose profile, `turnbase-platform`), `IMP-M0-08` (Helm chart,
`turnbase-platform`), `IMP-M0-09` (configuration and secrets wiring, `turnbase-platform` +
`turnbase-game-host`), `IMP-M0-10` (observability baseline, `turnbase-platform` +
`turnbase-game-host`), `IMP-M0-11` (CI/CD workflows, all five repos), `IMP-M3-12` (FE GDK
client, `turnbase-sdk`), `IMP-M1-01` (error model, REST conventions, validation harness,
`turnbase-platform`), `IMP-M1-03` (JWT key set, issuance, rotation, `turnbase-platform`),
`IMP-M1-04` (credential registration and login, `turnbase-platform`), `IMP-M1-06` (session
lifecycle and displacement, `turnbase-platform`), `IMP-M1-05` (guest minting and purge,
`turnbase-platform`), `IMP-M1-07` (profiles and privacy settings, `turnbase-platform`),
`IMP-M1-08` (account deletion and erasure, `turnbase-platform`), `IMP-M1-09` (social graph —
friendships and requests, `turnbase-platform`), `IMP-M1-02` (rate limiter, Tiers 1-5,
`turnbase-platform`), `IMP-M1-10` (Google OAuth registration and login, `turnbase-platform`) and
`IMP-M2-03` (ownership claim, lease, epoch fence, `turnbase-platform`) and `IMP-M2-01` (room CRUD and
listing, `turnbase-platform`), all pushed and green in CI.
**M1 is complete; M2 is under way.**
**No work item is gated**, and all 23 readiness blockers remain closed, so an item's status is
whatever its own dependencies imply.

**M1 is fully DONE, and `IMP-M2-03`/`IMP-M2-01` too.** `IMP-M2-02` (STOMP endpoint) is `READY` off
`IMP-M2-01, IMP-M2-03` — both now satisfied — and is the next pick: it re-verifies ownership at
subscribe time using the same `room.RoomOwnershipService` this item's REST handlers already call.
`IMP-M2-12` (room invitations) is `READY` off both `IMP-M2-01` and `IMP-M1-09`. `IMP-M5-03`
(notifications and the SSE stream) is `READY` off `IMP-M1-06` and `IMP-M1-07`, and now delivers
`IMP-M1-09`'s `notification` rows over SSE rather than writing any of the friend-request types itself
(`IMP-GATE-34`).

**IMP-GATE-25** (`IMP-M0-11`, opened and closed 2026-09-05) — `game-development-experience.md`
CON-003 and ADR-0012's Release Strategy commit `turnbase-sdk` to Maven Central + npm, but no document
names a license for it, and Maven Central's publish validation rejects a POM with no `<licenses>`.
Raised to the project owner (a real decision, not a CI mechanic), who deferred it. Fixed: both
documents now say the Maven Central/npm publish is deferred until a license is chosen. Only the Maven
half gets an interim home (GitHub Packages, same as `turnbase-common`) — GitHub Packages' npm registry
requires a scope matching the `turnbase-platform` org, which `@turnbase/gdk` (FR-FEGDK-007) cannot
satisfy, so the npm package stays unpublished by any registry until the public one is available.

**IMP-GATE-24** (`IMP-M0-11`, opened and closed 2026-09-05) — FR-CICD-007/008 require a tag-triggered
production deployment and rollback, but ADR-0001 defers all cloud/production deployment to post-MVP
and names the local Docker Desktop cluster as the only CI-exercised deploy path — no production target
exists for a workflow to reach. Fixed: FR-CICD-007/008 marked deferred to post-MVP in
`platform-operations.md`; ADR-0001's *Affected documents* updated to record it. `IMP-M0-11`'s own
*Satisfies*/*Done when* narrowed to match — FR-CICD-006 (image push to a registry) stands.

**IMP-GATE-23** (`IMP-M0-11`, opened and closed 2026-09-05) — `platform-operations.md` FR-CICD-002/003
and OQ-002's resolution gated the pipeline on a **pull request** ("the PR cannot be merged...", "PR
feedback loops"), but ADR-0012 (amended 2026-09-05) suspends pull requests project-wide, so a
`pull_request` trigger would never fire. Fixed: FR-CICD-002 retitled *Pre-merge checks* and reworded
to gate on push to `master`; FR-CICD-003 and OQ-002 updated to match. No workflow code changed — the
five repos' `build.yml` files already run on push.

**`IMP-M0-11` is now DONE.** `IMP-M0-12` (seed data) stays not-`READY` — it depends on `IMP-M4-03`,
which has not been picked up. **M0 is otherwise finished, and `IMP-M1-01`/`IMP-M1-03` are now DONE
too.** Next up in M1 (accounts and sessions — see *Then, in dependency order* below): `IMP-M1-04`
(credential registration and login — narrowed from *Registration and login* by IMP-GATE-26; OAuth is
now the separate `IMP-M1-10`), `READY` off both `IMP-M1-01` and `IMP-M1-03`, is the natural next pick —
it is the first item to actually create an `app_user`/`user_session` row through an endpoint rather
than a test fixture. `IMP-M1-02` (rate limiter, Tiers 1–5), `READY` off `IMP-M1-01`, remains
independently pickable if `IMP-M1-04` is deferred. `IMP-M0-10` left five small
obligations on later items, each recorded as a sentence in that item's own section rather than a
gate: `IMP-M2-02` exposes `turnbase_websocket_connections_active`,
`IMP-M3-09`/`IMP-M2-10`/`IMP-M3-08` wire
`GameSessionFailureRate`/`ReconciliationRepairsPersist`/`TeardownOwed`, and any item adding a new
Redis usage site tags it per `conventions.md` §7. None of these block anything — they surface when
that item's own Done-when is checked.

**IMP-GATE-17** (`IMP-M0-09`, opened and closed 2026-09-05) — `turnbase.gamehost.grpc.port`, shipped
in `IMP-M0-04` and already read live by `GrpcServerLifecycle`, was never added to
`local-environment.md` §7.8, contradicting §7's own "whole tunable surface" claim — the same class
of gap IR-24 closed for `turnbase.room.spectator-capacity`. Fixed: added to §7.8 with its existing
default (`9090`).

**IMP-GATE-18** (`IMP-M0-10`, opened and closed 2026-09-05) — the Done-when clause required proving
trace propagation "across the REST → gRPC boundary," but no such boundary exists yet: `platform`
issues no outbound gRPC call and runs no gRPC server, and the Game Host's one outbound call
(`Register`) isn't triggered by an inbound REST request — that request chain doesn't exist before
`IMP-M3-05`. Fixed: narrowed to proving the interceptor mechanism against a controlled gRPC call, with
the live cross-repo check moved to `IMP-M3-05`. `IMP-M0-10`'s *Satisfies* was also narrowed to what it
actually builds — `FR-MET-002`, `FR-MET-005`, `FR-ALERT-003/006/007` and the Game Host's own
`platform-architecture.md` `FR-OBS-*` are deferred to `IMP-M2-02`, a new `conventions.md` §7 rule, and
`IMP-M3-09`/`IMP-M2-10`/`IMP-M3-08` respectively, each of which now carries the corresponding clause.

**IMP-GATE-19** (`IMP-M0-10`, opened and closed 2026-09-05) — `observability.md` §3's own worked
example showed `"sessionId": null` beside prose stating correlation IDs are "omitted when absent
rather than written as empty strings." Fixed: the example now omits the key.

**IMP-GATE-20** (`IMP-M0-10`, opened and closed 2026-09-05) — `observability.md` §2.1's SQL for
`turnbase_friend_requests_pending` filtered on a `status` column `friend_request` does not have
(`IMP-M0-06`'s baseline). Fixed: an unfiltered `count(*)` — a pending request's row existing is what
"pending" means in this schema; accepting or declining one deletes the row.

**IMP-GATE-21** (`IMP-M0-10`, opened and closed 2026-09-05) — found by actually running the stack:
`observability.md`'s JSON log example and Grafana derived-field regex used camelCase
`traceId`/`spanId`, but the OpenTelemetry Java agent's `logback-mdc` instrumentation — the mechanism
the doc itself credits — writes `trace_id`/`span_id` (OTel semantic conventions, not configurable).
Fixed: doc, `promtail-config.yaml` and `datasources.yaml` all changed to `trace_id`/`span_id`.

**IMP-GATE-22** (`IMP-M0-10`, opened and closed 2026-09-05) — also found by running the stack:
`tempo.yaml` (`IMP-M0-08`) left the OTLP receivers on Tempo's default loopback bind, so every span
export failed with `Connection refused` and zero traces ever reached Tempo — same bind-address trap
class as `IMP-GATE-14`. Fixed: explicit `endpoint: 0.0.0.0:4317`/`:4318`.

**IMP-GATE-16** (`IMP-M0-09`, opened and closed 2026-09-05) — `secrets-and-configuration.md`'s
`local`/`test,e2e`/`Kubernetes` split for the JWT key set cannot be implemented by Spring profile
alone: `local-environment.md` §4 runs the canonical Kubernetes chart under the identical
`spring.profiles.active=local` compose uses, but the two rows need opposite behaviour — generate and
persist to a file under compose (one instance), fail if absent under Kubernetes (the chart's own HPA
can run more than one replica). Fixed: a new non-secret switch, `turnbase.auth.jwt-key-set-required`
(`local-environment.md` §7.4, default `false`), set to `true` only by the Helm chart's ConfigMap;
`secrets-and-configuration.md` §3.1 now states this is the actual mechanism and profile is not.

**IMP-GATE-15** (`IMP-M0-09`, opened and closed 2026-09-05) — the *Done when* clause requires a
Kubernetes Secret path for every secret, including the JWT key set, but
`secrets-and-configuration.md` §3.1 named none: it said only "Supplied; startup fails if absent," and
§7 deliberately excludes secrets by design, so there was nowhere else it could be named either.
Fixed: §3.1 now names `TURNBASE_JWT_KEY_SET` (`turnbase.auth.jwt-key-set`), one JSON-valued
environment variable carrying the whole key set in §3.2's own shape.

**IMP-GATE-14** (`IMP-M0-07`, opened and closed 2026-09-05) — `local-environment.md` §1 said
compose achieves the loopback-only management port by setting `management.server.address =
127.0.0.1` *inside* the container, with the published port doing the rest — but a Docker published
port always forwards to the container's bridge interface, never its loopback, so a listener bound
that way is unreachable through its own published port regardless of the host-side bind. Proven
live: the container refused every host connection with the address set, and answered normally with
it unset. `IMP-M0-03`/`IMP-M0-04`'s "verified live" claims never exercised a real Docker
port-publish round trip. Fixed: §1 and §7.9 now say the app listens on all interfaces in both
profiles; compose's restriction is the published port's own host-side bind. No application code
changed (`MANAGEMENT_SERVER_ADDRESS` already defaults to unset); only stale comments and
`docker-compose.yml` were corrected.

**IMP-GATE-13** (`IMP-M0-07`, opened and closed 2026-09-05) — ADR-0011 §6 requires the Postgres
init script to create `pg_trgm` and `btree_gin` as superuser (the baseline migration's own
`CREATE EXTENSION IF NOT EXISTS` for both then succeeds as a no-op), but
`secrets-and-configuration.md` §4's actual `01-roles.sql` content created only `pgcrypto`. Running
the real compose stack — the first thing to migrate as the actual unprivileged `turnbase_app` role
rather than a Testcontainers superuser — failed outright with `permission denied to create
extension "pg_trgm"`. Fixed: §4's script (and `deploy/compose/initdb/01-roles.sql`) now creates all
three extensions; the baseline migration file needed no change, verified.

**IMP-GATE-12** (`IMP-M0-07`/`IMP-M0-08`, opened and closed 2026-09-05) — both items' `Repo` field
said "this repo" (the root `turnbase` landing repo), but `local-environment.md` §4 roots the whole
deploy tree — compose files, Helm chart — at `turnbase-platform/deploy/…`, and ADR-0012 describes
`turnbase` itself as holding only docs, specs and submodule refs, no deploy artifacts. Fixed: both
items' `Repo` corrected to `turnbase-platform`, matching the spec and the ADR.

**IMP-GATE-11** (`IMP-M0-06`, opened and closed 2026-09-05) — `schema-migrations.md` §5 names
`shedlock` as a baseline table but no document supplied its columns. Fixed: §5 now states the DDL,
which is ShedLock's own fixed schema, not a TurnBase design choice.

**IMP-GATE-10** (`IMP-M0-06`, opened and closed 2026-09-05) — the *Done when* clause named the
baseline file `V1__baseline.sql`, contradicting ADR-0011 §5 and `schema-migrations.md` §§1–2, which
mandate timestamp-based naming and both already name the real file `V202608091200__baseline.sql`.
Fixed: the registry entry (the one document that had it wrong) now names
`V202608091200__baseline.sql` throughout.

**IMP-GATE-09** (`IMP-M0-04`, opened and closed 2026-09-04) — no document names the address the Game
Host dials to reach the Platform Monolith's `GameHostRegistryService`, which `local-environment.md`
§2 places on the monolith's `8080` HTTP listener rather than a dedicated port. Fixed: §7.8 gained
`turnbase.gamehost.orchestration-address` (default `platform:8080`).

**IMP-GATE-08** (`IMP-M0-04`, opened and closed 2026-09-04) — the *Done when* clause required "the
process registers with the Platform Monolith per §3's 60-second budget," but the platform's server
side of `GameHostRegistryService` is not implemented until `IMP-M3-05` (depends on `IMP-M3-04`,
`IMP-M2-04`), far downstream of `IMP-M0-04` (depends only on `IMP-M0-01`). Same shape as
`IMP-GATE-03`. Fixed: `IMP-M0-04`'s clause narrowed to a `Register` client call proven against an
in-process stub registry service; the real cross-repo, 60-second-budget check is now `IMP-M3-05`'s own
*Done when* clause.

**IMP-GATE-07** (`IMP-M0-03`, opened and closed 2026-09-02, `DONE` 2026-09-04) — `IMP-M0-03`/`M0-04`'s
*Done when* required the `turnbase-grpc` client/server stubs to resolve "at the exact pinned
`<turnbase-common.version>`" against `conventions.md` §5's absolute "no `-SNAPSHOT` in a committed
pom" — but `turnbase-common` has never been tagged (a human action) and the publish workflow that
would produce a release is `IMP-M0-11`, which depends on `M0-03`/`M0-04`. Unsatisfiable as written.
Fixed: `conventions.md` §5 gained a bootstrap exception — pin the current development version,
resolved from the local install, until the first tag exists; `IMP-M0-11` owns both standing up the
publish workflow and the follow-up PRs that bump consumers to the real release once it's tagged. The
fix's first draft still missed how CI itself gets that install — see the session 16 summary above for
the private-repo credential problem that turned up executing it.

**IMP-GATE-06** (`IMP-M0-03`, opened and closed 2026-09-02) — `platform-operations.md` CON-010 still
said integration tests use Docker Compose, contradicting FR-CICD-004 in the same document (corrected
2026-08-20 to Testcontainers-only) and the same rule restated in `conventions.md` §3. Simply missed
when FR-CICD-004 was fixed. Fixed `platform-operations.md` CON-010 to state the Testcontainers/compose
split correctly.

Seven gates have now been opened *and closed* across the first three items — three on `IMP-M0-01`,
two on `IMP-M0-02`, two on `IMP-M0-03` — which is the number worth planning around: **a skeleton item
costs roughly one spec defect per document in its read-list.** Budget for that rather than treating a
gate as a delay.

**IMP-GATE-05** (`IMP-M0-02`, closed 2026-08-22) — `game-development-experience.md`
FR-FEGDK-001…009 (the `TurnBaseClient` class itself) was claimed only by `IMP-M6-05`, which
implements the platform shell's half of the postMessage boundary, not the client — no item in
`turnbase-sdk`, the repo that publishes `@turnbase/gdk`, owned it. Fixed by adding
**`IMP-M3-12` — FE GDK client**, depends on `IMP-M0-02`, and correcting `IMP-M6-05`'s *Satisfies*.

**IMP-GATE-04** (`IMP-M0-02`, closed 2026-08-22) — the read-list named `backend-gdk-api.md` §1–3
and claimed `FR-GDK-001`, but §3's `TurnBaseGame` cannot compile without all of §§3–8 — verbatim
`IMP-M3-01`'s own *Done when*. Fixed by narrowing `IMP-M0-02` to the build-and-publish floor; the
Java type surface stays `IMP-M3-01`'s.

**IMP-GATE-03** — the clause "resolves from both `turnbase-platform` and `turnbase-game-host`"
required the item's own dependents to exist first (`IMP-M0-04` depends on `IMP-M0-01`). The half that
is checkable at the source — install, then compile and run a consumer against the client stub *and*
the server base class — stayed; the cross-repo half moved onto `IMP-M0-03` and `IMP-M0-04`, which
have a consumer to check it with.

**IMP-GATE-02** — ADR-0012 said `turnbase-common` copies `gamehost.proto` into `src/main/proto/` *at
build time*, and also said each component repo is *independently usable without the root*. Two
sections apart, and they cannot both hold: a Maven step reading `../docs/` fails in a standalone
clone, which is exactly what that repo's CI checks out. ADR-0012 is amended — the copy is a
**committed file**, and the drift guard is `scripts/sync-proto.sh --check` in the parent's `pre-push`
hook, because drift here is silent (both repos compile; the two services disagree on the wire).

**IMP-GATE-01** — `gamehost.proto` declared `java_package = "com.turnbase.gamehost.grpc.v1"` against the
`io.turnbase.grpc` root that `conventions.md` §1 and ADR-0014 §1 both give `turnbase-common`. The
proto now declares `io.turnbase.grpc.gamehost.v1`, and `conventions.md` §5 states the rule — package
tail and canonical buf-module path — so the next generated artifact does not re-decide it.

**None of the three was findable by reading**, and none would have been caught by
`check-corpus.py`. They surfaced only because something finally had to compile against the documents.
That is the argument for doing the skeletons before anything subtle depends on them.

**[`docs/implementation/conventions.md`](docs/implementation/conventions.md) applies to every item and
is not repeated in read-lists** — package layout, static analysis, Spotless, test suffixes, JaCoCo,
branch and commit format, cross-repo version pinning. Assume it the way you assume `CLAUDE.md`.

**The harness is done.** Submodule `CLAUDE.md` files, the corpus checker, the status protocol, the
escalation format, the two skills and the permissions all landed in session 13, and sessions 14 and
15 proved them on real items: the `work-item` cadence held both times, `spec-defect` fired three
times on `IMP-M0-01` and twice on `IMP-M0-02`, and the `pre-push` hooks now run in two repositories.

### `turnbase-sdk` is a second worked example, narrower than `turnbase-common`

It adds two things `turnbase-common`'s pom didn't need: **Checkstyle** (bound at `validate`
alongside Spotless, public-type Javadoc only — the one repository that runs it) and an enforcer
**`bannedDependencies`** rule (`turnbase-grpc`/`turnbase-game-host` banned at every scope). Both are
mechanical answers to `turnbase-sdk/CLAUDE.md`'s two repo-specific rules, and both were verified to
actually fire against a deliberate violation before being trusted.

**`typescript` is pinned to `6.0.3`, not the latest `7.0.2`** — `typescript-eslint@8.67.0`'s peer
range is `<6.1.0`; `npm install` fails `ERESOLVE` otherwise. Not in `conventions.md` because it is a
toolchain fact rather than a project decision, but worth knowing before `IMP-M0-05`
(`turnbase-frontend`) or `IMP-M3-12` pin `typescript` again.

### The next session — `M0-04` is done; `M0-05`, `M0-06`, and `IMP-M3-12` are on the board

**`IMP-M0-04` is `DONE`.** `turnbase-common`, `turnbase-platform` and `turnbase-game-host` are now
three worked examples of the bootstrap-window mechanics (Spotless at `validate`, Error Prone +
NullAway, merged JaCoCo, the enforcer, the `.mvn/jvm.config` flags, and the `TURNBASE_COMMON_PAT`
bootstrap install — one secret per bootstrap-window consumer repo, never shared). `IMP-M0-05`
(frontend skeleton) has no such dependency and is a clean start by comparison.

Things `IMP-M0-01`/`M0-03` learned that `IMP-M0-04` met on its own first push too, all in
`conventions.md` §6:

| | |
|---|---|
| GraalVM CE | `graalvm/setup-graalvm`, **not** `actions/setup-java`, which has no `graalvm-community` distribution |
| `buf breaking` | pull requests only, against the base branch — a push has no reliable baseline |
| Dependabot | opens PRs within a minute of the first push; land `ignore` entries **with** a deliberate pin, and expect every PR to fail CI on the bootstrap secret regardless of content until `IMP-M0-11` |
| Line endings | `.gitattributes` pins `*.sh`, hooks and `mvnw` to LF, or a CRLF checkout makes git silently refuse to run a hook |
| Dependabot `ignore` dependency-name | **verify the entry actually matches** — a docker `dependency-name` never includes the registry host (`ghcr.io/…` doesn't match; the bare image name does), found the hard way by `IMP-M0-04`'s own first `dependabot.yml` |

**A dependency pinned as "the exact build a spike verified" (Espresso here; Astryx for `IMP-M0-05`)
needs an `ignore` entry with no version floor at all**, not a `>=<major>` range — a patch bump is still
a different build than the one that was verified, and only a version-range-shaped rule looks like it
covers that until the first Dependabot PR proves otherwise.

**`IMP-M3-12` (FE GDK client, `turnbase-sdk`) is now `READY`**, unblocked by `IMP-M0-02`. It's a
candidate for the same session as `M0-05`/`M0-06` if there's room: `frontend-gdk-api.md` is already
read in full for `IMP-M0-02`, and the declared types it needs (`Role`, `Player`, `Team`,
`InitContext`, the envelope) already exist in `src/main/ts/types.ts`.

**`IMP-M0-05` installs and wires Astryx** (exact pins, three CSS imports in cascade-layer order,
`<Theme>` + `<LinkProvider>`, `data-astryx-theme`, self-hosted Figtree) — a skeleton without them
renders almost-right screens that get corrected one at a time later. Its lint stack is pinned in
`conventions.md` §2, not left to `npm create vite`.

**Then, still in setup:** `IMP-M0-11` wires the CI workflows — every trigger on `master`,
Testcontainers with no compose in the PR job, and FR-CICD-010's Dependabot and Trivy as committed
configuration rather than a mention.

### Then the substantive M0 items

1. **IMP-M0-06 — the Flyway baseline.** The highest-value item in the registry. Transcribing
   `V1__baseline.sql` from the six schema documents is the first mechanical test of whether they are
   mutually consistent. The two hazards the audit named are now **fixed in the documents**:
   `data-model.md` states one auto-increment idiom (`bigint GENERATED ALWAYS AS IDENTITY`), and
   `schema-migrations.md` §5 names one circular foreign key rather than two. **Any further
   disagreement found while transcribing is a
   specification defect — fix the document, then the SQL.** Do not reconcile silently in the
   migration.

   Two schema changes from this session must land in the baseline:
   `room_participant_unannounced_idx` (IR-09) and nothing else — IR-11 deliberately added no table.

2. **IMP-M0-07 — the compose stack.** IR-01 and IR-02 are closed, so this is now buildable end to
   end: the `minio-init` container, `deploy/compose/initdb/01-roles.sql`, and `POSTGRES_USER` set to
   `turnbase_owner`. Getting the last one wrong is the silent FR-CRED-005 violation.

### Then, in dependency order

M1 accounts → M2 rooms (the longest milestone, and now fully specified) → M3 execution → M4 catalog →
M5 history → M6 frontend. The registry has the per-item ordering.

Three things worth knowing before the milestone that needs them:

- **M2's specifications are clean but subtle.** The ownership and versioning core was confirmed
  correct by the audit; the blockers clustered in the edges — expiry, closure, chat, sweeps — and all
  of those are now fixed. Read ADR-0008/0009/0010 before touching `room-lifecycle.md`'s mechanisms,
  and remember that **the epoch is the fence token, not the version**.
- **M3's trust boundary now requires an address check** (IR-17) that did not exist when the registry
  was written: every effect address is validated against the producing session's membership at
  fan-out.
- **M6's component library is Astryx, not ours** ([ADR-0013](docs/decisions/0013-astryx-design-system.md)).
  Read that ADR before anything else in M6. `IMP-M6-01` is an integration item — install is already
  done by `IMP-M0-05`, so what remains is the `ui/` boundary and the compose→swizzle→write ladder.
  **Component lookup is a tool call** (`npm run astryx -- component <Name>` or the `astryx` MCP
  server); nothing in this corpus lists them.

- **Every trigger, tag rule and branch protection names `master`**, in every repo. FR-CICD-002/006/007
  said `main` until session 13 and were corrected; a workflow written from the old text never fires.
- **Integration tests are Testcontainers, never compose** (`local-environment.md` §8). Compose belongs
  to the post-merge e2e job alone. The PR job needs a Docker daemon and nothing else.

### Spec hygiene

- **The ID-qualification retrofit** remains outstanding. `docs/specs/INDEX.md` states the rule and it
  holds for new text; the corpus predates it. The highest-traffic collision is `FR-SESS-001…004`,
  defined in both `user-accounts.md` (account sessions) and `platform-architecture.md` (Game Host
  in-memory state); all seven citations resolve correctly by context, so this is a hazard rather than
  a defect. A **wrong** qualifier is worse than a bare ID.
- The `FR-JOB-007a…e` sub-duty convention is declared in `docs/specs/INDEX.md`, and
  `data-model-accounts.md:392`'s wrong FR-INV-002 citation is corrected (session 11).
- **`docs/requirements/INDEX.md` now exists** (IR-25 closed) and carries the twelve genuinely
  colliding prefixes. Use it to resolve a qualifier before writing one — the qualifier names the
  document that **defines** the requirement, never one that merely cites it.
- **`turnbase.room.spectator-capacity`** (IR-24 closed) is in `local-environment.md` §7.1, whose
  title is now *Room lifecycle, capacity and deadlines*. §7 is again true when it claims to hold every
  tunable in the corpus — keep it that way: a property named at a call site and never registered there
  is invisible to the next configuration audit.
- The ten non-blocking findings worth acting on were harvested into the corpus in Part 5 and the
  slice files deleted; the review INDEX records each with where its fix landed. The remaining ~52 were
  NITs and low-value GAPs, and re-deriving one from a fresh audit is cheaper than carrying 3 184 lines
  of stale report against the chance that one mattered.

### Review action plan

`docs/reviews/2026-07-02-mvp-readiness/INDEX.md` — fully worked, **closed**.

`docs/reviews/2026-08-16-implementation-readiness/INDEX.md` — **closed.** 23 of 23 blockers resolved;
each entry carries a `**Closed:**` line. The two follow-on findings raised during remediation (IR-24,
IR-25) are closed too.

**2026-08-20 readiness review (session 13)** — no review directory: seven defects, all closed in the
same session, and the record is this file plus ADR-0014, ADR-0015 and `conventions.md`. A round that
opens and closes together does not need an INDEX to track it, and a working file describing it would
be spent on arrival.

**Nothing is open in the corpus, and nothing is open in the harness.** The next work is `IMP-M0-01`.

Two things are deferred rather than done, both deliberately:

- **The three proposed agents** (`impl-agent`, `done-when-verifier`, `spec-auditor`) wait until M0
  shows where the cadence actually hurts. Guessing their shape now costs more than waiting.
**`work-item` and `spec-defect` have now had their first real outing** and both held on `IMP-M0-01`.
`spec-defect` fired three times on one item; `work-item`'s "a green local build is not `DONE`" rule
is what kept the item at `WIP` until CI actually ran — and CI then failed in both jobs, which is the
best possible argument for the rule. Neither skill needed an edit. The one thing to watch on the next
item is whether three gates in one item makes the escalation feel routine enough to start skipping.

**Permissions are settled.** The Astryx and Playwright prefixes were corrected in session 13, and
session 14 added `git push` **without any force variant** — `--force`, `--force-with-lease`,
`--mirror`, `--delete`, `--prune`, `--tags` and `+refspec` stay denied, and a `v*.*.*` tag push stays
a human action because ADR-0012 makes it the release trigger.

---

## Coverage Summary

| Document | Coverage |
|----------|----------|
| `user-accounts.md` | Registration, auth, sessions, account management, profiles, guests, per-section privacy settings, block-requests toggle |
| `game-rooms.md` | Room list, creation, joining, host management, teams, readiness, lifecycle, mid-game join assignment |
| `game-catalog.md` | Catalog listing, game detail, game management, profile games tab |
| `notifications-invitations.md` | Alerts, notification center, invitations, friend request notifications |
| `reconnection-flow.md` | Disconnect detection, grace period, re-entry, kick mechanics |
| `in-room-chat.md` | Room/team channels, messaging, delivery model, late-join team chat access |
| `per-game-statistics.md` | Session counting, game detail stats, profile stats |
| `platform-views.md` | All views, navigation, redirects, auth tier gating |
| `game-development-experience.md` | GDK, game packaging, upload pipeline, local dev workflow |
| `game-contracts.md` | Platform ↔ game BE/FE protocol, effect types, structured outcome, postMessage API |
| `platform-architecture.md` | Game execution infrastructure, Game Host, Orchestration Service, sandboxing, scaling |
| `game-history.md` | Per-session history recording, win condition labels, profile history tab, privacy, deletion pseudonymization |
| `social-friends.md` | Friendship model, request lifecycle, friend cap, discovery, visibility, guest exclusion, block-requests toggle |
| `platform-operations.md` | Service topology (monolith), availability, observability stack, CI/CD pipeline, data retention |
| `onboarding-wizard.md` | First-time wizard overlay, pane structure, localStorage suppression, landing page re-entry |
| `admin-tooling.md` | Internal admin API, game badge model (Official/Verified/Unverified), review queue, private game behaviour |

**Specs:** `docs/specs/` — **flows** (new: eight end-to-end journeys — start here), **deployment**
(new: local environment and the configuration surface, schema migrations, secrets and key rotation),
**platform-frontend** (new: the React shell and the iframe trust boundary), platform (room lifecycle
plus the **complete relational data model** across six documents), api-design, internal-grpc,
game-host, game-frontend, gdk-api (now including the **test harness**), manifest (now including the
**bundle format and upload pipeline**).

**Decisions:** `docs/decisions/` — ADR-0001 (local-first platform), ADR-0002 (WS room affinity),
ADR-0003 (availability), ADR-0004 (erasure pseudonymization), ADR-0005 (sandbox / Espresso spike),
ADR-0006 (game trust model — official-only Java for MVP), ADR-0007 (game FEs on a separate
registrable domain), ADR-0008 (room ownership as a lease-gated claim), ADR-0009 (grace deadlines
persisted and swept), ADR-0010 (session teardown as a durable to-do), ADR-0011 (schema migrations —
Flyway, forward-only, backward-compatible), ADR-0012 (polyrepo under an organisation, with
submodules), ADR-0013 (Astryx supersedes the in-house design system), **ADR-0014 (modular monolith,
enforced by Spring Modulith)**, **ADR-0015 (static analysis — Error Prone and NullAway, at skeleton
time)**.

**Implementation:** `docs/implementation/` — the registry Phase 1 executes from. **61 live work items
across 7 milestones** (IMP-M6-07 cancelled; `IMP-M3-12` added session 15; `IMP-M1-10` added session 29),
each carrying a
read-list, dependencies, the requirement IDs it satisfies and a done-when clause. Nothing is gated.
Plus **`conventions.md`** (new, session 13): the code and build conventions every item assumes —
package layout, Spotless, tests and coverage, git, cross-repo dependencies, and the per-repo build
floor.

**Reviews:** `docs/reviews/` — two closed rounds, reduced to their INDEXes plus
`espresso-spike-results.md`. `2026-08-16-implementation-readiness/INDEX.md` carries all 23 blockers
with evidence and a `Closed:` line each, the ten harvested non-blocking findings, and IR-24/IR-25.
Working files (slice reports, inventories, the remediation plan) were deleted once spent — they had
become pre-remediation snapshots of a corpus that no longer matched them.

**Coverage caveat — now largely closed.** Of the four areas that had requirements but no implementing
specification, three were written this session: the design system
(`platform-frontend/design-system.md`), the room REST API (`api-design/room-rest-api.md`) and
observability (`deployment/observability.md`). The fourth, the onboarding wizard, was **cut from v1**
rather than specified. The table above lists requirement coverage, not design coverage.

---

## Open Questions Remaining in Existing Docs

| Document | Open Question |
|----------|---------------|
| `reconnection-flow.md` | Game engine response set after "player lost" event — deferred to Game SDK contracts |
| `game-history.md` | OQ-002: Pagination reuse — shared UI component vs. API pattern deferred to implementation |
| `game-contracts.md` | OQ-001: Log color annotation syntax — deferred to GDK spec |
| `game-contracts.md` | OQ-002: AI/bot player interface — deferred to future spec. **Mislabelled: this now blocks M2 (IR-12).** `ROOM_STATE` carries AI participants on the wire and the room-closure predicate turns on "not an AI", but `room_participant` has no discriminator — so the closure predicate cannot be written. Either add the column or remove AI from the protocol for the MVP |
| `game-contracts.md` | OQ-003: Platform-managed timer system — deferred to future spec |
| `websocket.md` | OQ-001: Resync cost under a *legitimate* mass reconnect (N resyncs serialize behind one session lock) — cache the per-viewer view against `lastAppliedSequence` if it becomes a hotspot. The adversarial case is now closed by the Tier 6 `snapshot` bucket |
| `websocket.md` | OQ-002: A game whose `onResync` returns an empty spectator view leaves spectators blank until the next `broadcast` — the test harness should warn |
| `admin-tooling.md` | OQ-001: Can a developer resubmit a rejected game, or is rejection terminal? |
| `admin-tooling.md` | OQ-002: Can an operator delist a Verified or Official game post-approval? |
| `game-asset-serving.md` | OQ-001: Fullscreen — `allow=""` grants no Permissions-Policy features; whether to add `allow="fullscreen"` is a shell-spec UX call |
| `game-asset-serving.md` | OQ-002: Private-bundle exposure — bundle assets are unauthenticated; a signed-token variant is additive if genuinely private third-party bundles become a requirement post-MVP |
| `game-asset-serving.md` | OQ-003: Manifest-declared stylesheets — CSS must currently be imported from JS; deferred to the bundle spec |
| `rate-limiting.md` | OQ-001: Shared-IP (CGNAT/campus NAT) guest throttling — accepted for a local-first MVP; escalation path is raise limit → add entropy to the key → proof-of-work |
| `rate-limiting.md` | OQ-002: Tier 6 budgets are per-pod, so a user connected to two pods gets 2× — accepted (these are abuse controls, not fairness quotas); revisit only if concurrent multi-room membership lands |
| `input-validation.md` | OQ-001: No emoji or symbols in usernames — the clean fix, if users push back, is a separate free-form display name alongside a strict username (post-MVP model change) |
| `input-validation.md` | OQ-002: ASCII-only email rejects IDN/EAI addresses — revisit if a real user is blocked; there is no mail system in the MVP to normalize against (no verification email is sent) |
| `room-lifecycle.md` | OQ-001: Lease/window numbers (10s TTL, 3s renew, 6s self-evict, 20s migration window, 5s/60s sweeps) are reasoned defaults with no measurement behind them; the relationships that must hold matter more than the values |
| `room-lifecycle.md` | OQ-002: Self-eviction uses a local monotonic clock while the lease expires in Redis — the 4s guard band covers single-node skew, but this is the one place a local clock still affects a correctness bound; re-examine before multi-node |
| `room-lifecycle.md` | OQ-003: Flapping clients — each disconnect starts a fresh window, so a connect/disconnect loop can hold a slot indefinitely; the Tier 6 reconnect lockout dampens it, but whether a hard cap per session is needed is deferred until observed |
| `data-model-catalog.md` | OQ-001: A rejected re-review leaves a community game with an `ACTIVE` version an operator refused, its previously approved version `SUPERSEDED` and unreactivatable, and no rollback in the status machine. §5.1 preserves the artifact; nothing says how to recover the state. Dormant under ADR-0006 |
| `data-model-catalog.md` | OQ-002: `game_review.decided_by` identifies a shared static credential, not a person (`admin-tooling.md` CON-002) — adequate for one operator, not as an audit trail beyond that |
| `data-model-catalog.md` | OQ-003: FR-REV-001's pending-review state has no owner-facing representation, so a second submission fails as a raw unique violation rather than a domain error |
| `local-environment.md` | OQ-001: The startup budget (≤30s to readiness, ≤60s to Game Host registration) is a target, not a measurement, and FR-JOB-008's 120-second suppression window depends on it |
| `local-environment.md` | OQ-002: **No backup, restore or disaster-recovery story for the local Postgres volume.** Undecided rather than decided; the first genuinely valuable data the platform holds is game history, retained indefinitely by FR-RET-003 and protected by nothing |
| `bundle-format.md` | OQ-1…5: publication deny list vs. a manifest `frontend.root` allow list (ties to `game-asset-serving.md` OQ-003); no integrity digest on published objects; the harness cannot check `gdkApiVersion` offline; NFR-UPLOAD-001's 30s validation budget is unmeasured; a version orphaned by a GDK-range move has no user-facing representation |
