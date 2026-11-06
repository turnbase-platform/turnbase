#!/usr/bin/env node
// Recovery from a full stop — IMP-M20-16, ADR-0021 (single-instance profile), local-environment.md §8.
//
// Brings the compose stack up with short deadlines, puts rooms in the states that matter, stops the WHOLE
// stack (Postgres, Redis, MinIO, Game Host, Platform, Frontend), lets longer than the grace period, the
// dispatch deadline and the lease TTL pass, starts it again, and asserts what room-lifecycle.md, ADR-0008/9/10
// and game-host-internals.md §9 require:
//   G  in progress, both players come back -> session record intact, nobody released, game resumes and ends
//   A  in progress, nobody comes back      -> grace is counted from adoption, then the room closes
//                                             GRACE_EXPIRED_NO_HUMAN and the session is torn down
//   L  lobby                               -> survives (FR-DC-007), is not closed as GRACE_EXPIRED_NO_HUMAN
//   leases/epochs                          -> old lease gone, one new one, adopted rooms on a new owner, epoch up
// Usage (repo root):  node scripts/recovery-test.mjs [--kill] [--keep]
//   --kill  stop with SIGKILL (crash path) instead of SIGTERM (graceful drain)
//   --keep  leave the stack running afterwards (default: down -v)
// Needs Docker, Node 22, turnbase-game-tictactoe/node_modules/ws, the three :dev images, and
// target/seed-bundles (scripts/seed-bundles.sh). Port 8080 and 8081/8082 must be free.
import { createRequire } from "node:module";
import { randomUUID } from "node:crypto";
import { execFileSync } from "node:child_process";
import { request as httpRequest } from "node:http";
import { existsSync, writeFileSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(resolve(ROOT, "turnbase-game-tictactoe/package.json"));
const WebSocket = require("ws");

const KILL = process.argv.includes("--kill");
const KEEP = process.argv.includes("--keep");
const GAME = "2cc66e36-52e6-4144-9a10-09d09c982ce4"; // Tic-Tac-Toe
const HOST = "turnbase.localhost:8080";
const BASE = "http://127.0.0.1:8080";

// Timings (seconds). Down time must exceed the grace period, the 35 s dispatch deadline and the 10 s lease TTL.
// Grace (30 s) is shorter than the outage (40 s), which is longer than the 35 s dispatch deadline and the 10 s lease
// TTL. With the Platform stopped first, nothing opens a reservation before the stop, so no deadline can elapse
// during it: the new owner opens them at adoption (room-lifecycle.md §1.4 step 4) and a player who returns within
// grace of the restart keeps the slot.
const GRACE = 30;
const DOWN = 40;
process.env.RECOVERY_GRACE = String(GRACE);
const RECONCILE = 10;

const COMPOSE_DIR = resolve(ROOT, "turnbase-platform/deploy/compose");
const OVERRIDE = resolve(ROOT, "scripts/recovery-compose.override.yml");
const ENV_FILE = resolve(COMPOSE_DIR, ".env");
const COMPOSE = ["compose", "-f", resolve(COMPOSE_DIR, "docker-compose.yml"), "-f", OVERRIDE];

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (m) => console.log(`[${new Date().toISOString().slice(11, 19)}] ${m}`);
const failures = [];
const check = (ok, what, detail = "") => {
  log(`${ok ? "PASS" : "FAIL"}  ${what}${detail ? "  (" + detail + ")" : ""}`);
  if (!ok) failures.push(what);
};
const dc = (...args) => execFileSync("docker", [...COMPOSE, ...args], { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
const redis = (...a) =>
  dc("exec", "-T", "redis", "sh", "-c", `REDISCLI_AUTH="$TURNBASE_REDIS_PASSWORD" redis-cli ${a.map((x) => `'${x}'`).join(" ")}`).trim();
const sql = (q) => dc("exec", "-T", "postgres", "sh", "-c", `PGPASSWORD="$POSTGRES_PASSWORD" psql -At -U turnbase_owner -d turnbase -c "${q}"`).trim();

function api(actor, method, path, body) {
  // node:http, not fetch: fetch will not send a Host header of our choosing, and the platform origin is routed by it.
  return new Promise((resolveA, rejectA) => {
    const data = body ? JSON.stringify(body) : undefined;
    const req = httpRequest(BASE + path, {
      method,
      headers: { Host: HOST, ...(actor.cookie ? { Cookie: actor.cookie } : {}), ...(data ? { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(data) } : {}) },
    }, (res) => {
      let t = "";
      res.on("data", (d) => (t += d));
      res.on("end", () => {
        let json = null;
        try { json = t ? JSON.parse(t) : null; } catch { /* not JSON */ }
        resolveA({ status: res.statusCode, json, res });
      });
    });
    req.on("error", rejectA);
    req.end(data);
  });
}
const cookieOf = (res) => (res.headers["set-cookie"] ?? []).map((c) => c.split(";")[0]).join("; ");
async function login(name) {
  // The local seeder runs after readiness; a login before it has created the user is refused. Retry briefly.
  for (let i = 0; ; i++) {
    const a = { name };
    const r = await api(a, "POST", "/api/auth/login", { usernameOrEmail: name, password: "password" });
    if (r.status < 300) { a.cookie = cookieOf(r.res); return a; }
    if (i >= 30) throw new Error(`login ${name}: ${r.status}`);
    await sleep(1000);
  }
}

function connect(actor) {
  return new Promise((resolveC, reject) => {
    const ws = new WebSocket(`ws://${BASE.replace(/^https?:\/\//, "")}/ws`, { headers: { Cookie: actor.cookie, Origin: `http://${HOST}`, Host: HOST } });
    const c = { ws, frames: [], waiters: [], closed: null };
    ws.on("open", () => { ws.send("CONNECT\naccept-version:1.2\nheart-beat:10000,10000\n\n\0"); c.hb = setInterval(() => ws.readyState === 1 && ws.send("\n"), 4000); });
    ws.on("error", reject);
    ws.on("close", (code) => { clearInterval(c.hb); c.closed = code; });
    ws.on("message", (d) => {
      for (const raw of String(d).split("\0")) {
        const text = raw.replace(/^\n+/, ""); if (!text) continue;
        const [head, ...rest] = text.split("\n\n");
        const [command] = head.split("\n");
        let msg = null; try { msg = JSON.parse(rest.join("\n\n")); } catch { /* no body */ }
        const f = { command, msg };
        if (command === "CONNECTED") resolveC(c);
        c.frames.push(f); c.waiters = c.waiters.filter((w) => !w(f));
      }
    });
    c.sub = (d) => ws.send(`SUBSCRIBE\nid:${randomUUID()}\ndestination:${d}\n\n\0`);
    c.cmd = (d, type, payload = {}) => ws.send(`SEND\ndestination:${d}\ncontent-type:application/json\n\n${JSON.stringify({ type, correlationId: randomUUID(), payload })}\0`);
    c.wait = (pred, ms = 20000) => {
      const hit = c.frames.find((f) => f.msg && pred(f.msg));
      if (hit) return Promise.resolve(hit);
      return new Promise((res, rej) => {
        const to = setTimeout(() => rej(new Error("timeout waiting for frame")), ms);
        c.waiters.push((f) => { if (f.msg && pred(f.msg)) { clearTimeout(to); res(f); return true; } return false; });
      });
    };
  });
}

// A room with two players and a started game; returns the connected actors and the session id.
async function startedGame(host, guest) {
  const room = (await api(host, "POST", "/api/rooms", { gameId: GAME, visibility: "PUBLIC", spectatingEnabled: false })).json;
  const roomId = room.roomId ?? room.room?.roomId;
  const j = await api(guest, "POST", `/api/rooms/${roomId}/participants`, { role: "PLAYER" });
  if (j.status !== 201) throw new Error(`${guest.name} join: ${j.status}`);
  const [h, g] = await Promise.all([connect(host), connect(guest)]);
  for (const x of [h, g]) { x.sub(`/topic/room.${roomId}`); x.sub("/user/queue/errors"); x.sub("/user/queue/game"); }
  await sleep(500);
  g.cmd(`/app/room.${roomId}.member`, "TOGGLE_READY", { ready: true });
  await h.wait((m) => m.type === "READINESS_CHANGED");
  h.cmd(`/app/room.${roomId}.host`, "START_GAME");
  const sid = (await h.wait((m) => m.type === "GAME_STARTED", 60000)).msg.payload.sessionId;
  for (const x of [h, g]) x.sub(`/topic/game.${sid}`);
  await sleep(500);
  return { roomId, sid, h, g };
}
async function sync(x, sid) {
  x.frames = x.frames.filter((f) => f.msg?.type !== "GAME_SYNC");
  x.cmd(`/app/game.${sid}.sync`, "REQUEST_GAME_SYNC");
  return (await x.wait((m) => m.type === "GAME_SYNC")).msg.payload.view;
}
async function move(x, other, sid, cell) {
  x.cmd(`/app/game.${sid}.action`, "SUBMIT_ACTION", { cell });
  await other.wait((m) => m.type === "GAME_EVENT" && m.payload?.type === "move" && m.payload.cell === cell && m.sessionId === sid);
}

async function until(what, fn, ms, every = 1000) {
  const end = Date.now() + ms;
  let last;
  while (Date.now() < end) { last = await fn(); if (last) return last; await sleep(every); }
  return null;
}
const roomRow = (id) => sql(`SELECT state||'|'||coalesce(closed_reason,'')||'|'||owner_epoch||'|'||coalesce(owner_instance_id,'') FROM room WHERE room_id='${id}'`).split("|");

async function main() {
  const createdEnv = !existsSync(ENV_FILE);
  if (createdEnv) {
    writeFileSync(ENV_FILE, [
      "TURNBASE_DB_OWNER_PASSWORD=rec-owner-pw", "TURNBASE_DB_APP_PASSWORD=rec-app-pw", "TURNBASE_REDIS_PASSWORD=rec-redis-pw",
      "MINIO_ROOT_USER=rec-minio", "MINIO_ROOT_PASSWORD=rec-minio-pw1", "TURNBASE_ARTIFACT_STORE_ACCESS_KEY=rec-app",
      "TURNBASE_ARTIFACT_STORE_SECRET_KEY=rec-app-secret", "TURNBASE_ADMIN_USERNAME=rec-admin", "TURNBASE_ADMIN_PASSWORD=rec-admin-pw", "",
    ].join("\n"));
  }
  try {
    log("down -v (clean start), then up");
    dc("down", "-v");
    dc("up", "-d", "--wait", "--wait-timeout", "300");
    await until("host registered", () => Number(redis("scard", "hosts")) >= 1, 90000);

    const extra = [];
    // ---- before the stop ----
    const [alice, bob, carol, dave] = [await login("alice"), await login("bob"), await login("carol"), await login("dave")];
    const guestRes = await api({}, "POST", "/api/auth/guest");
    if (guestRes.status >= 300) throw new Error(`guest: ${guestRes.status} (limit is 5 per IP per hour; wait or restart the stack's Redis)`);
    const guest = { name: "guest", cookie: cookieOf(guestRes.res) };

    const G = await startedGame(alice, bob);
    const A = await startedGame(carol, dave);
    const lobbyRoom = (await api(guest, "POST", "/api/rooms", { gameId: GAME, visibility: "PUBLIC", spectatingEnabled: false })).json;
    const lobbyId = lobbyRoom.roomId ?? lobbyRoom.room?.roomId;
    const lobbySock = await connect(guest);
    lobbySock.sub(`/topic/room.${lobbyId}`);

    // two moves in G, so the stored state is not the opening state
    const view0 = await sync(G.h, G.sid);
    const [X, O] = view0.yourMark === "X" ? [G.h, G.g] : [G.g, G.h];
    await move(X, O, G.sid, 0);
    await move(O, X, G.sid, 3);
    const boardBefore = JSON.stringify((await sync(G.h, G.sid)).board);
    const podBefore = redis("keys", "pod:*:alive");
    const epochBefore = { G: Number(redis("get", `room:${G.roomId}:epoch`)), A: Number(redis("get", `room:${A.roomId}:epoch`)) };
    log(`before: board=${boardBefore} lease=${podBefore} epochs=${JSON.stringify(epochBefore)} lobby=${roomRow(lobbyId)[0]}`);
    check(epochBefore.G >= 1 && epochBefore.A >= 1, "rooms were owned before the stop (epoch >= 1)");

    // ---- the full stop ----
    log(`stopping the whole stack (${KILL ? "SIGKILL" : "SIGTERM"})`);
    // Platform first, as a host shutdown or a deploy would: its drain tags the sockets it closes (room-lifecycle.md
    // §1.6). Stopping the Frontend first drops them as network failures instead, which is a different event.
    if (KILL) { dc("kill", "platform"); dc("kill"); } else { dc("stop", "platform"); dc("stop"); }
    log(`stack down for ${DOWN}s (grace ${GRACE}s, dispatch deadline 35s, lease TTL 10s)`);
    await sleep(DOWN * 1000);
    const t0 = Date.now();
    dc("up", "-d", "--wait", "--wait-timeout", "300");
    log(`stack up after ${Math.round((Date.now() - t0) / 1000)}s`);
    check(true, "stack restarted, every service healthy");

    // ---- after the start ----
    const hostUp = await until("host registered", () => Number(redis("scard", "hosts")) >= 1, 90000);
    check(!!hostUp, "Game Host registered again");

    const leases = redis("keys", "pod:*:alive").split("\n").filter(Boolean);
    check(leases.length === 1 && leases[0] !== podBefore, "exactly one liveness lease, and it is a new incarnation", leases.join(","));

    // Adoption (ADR-0008): the new instance claims the released rooms within one reconciliation interval.
    const adopted = await until("G and A adopted", () => {
      const g = roomRow(G.roomId), a = roomRow(A.roomId);
      return Number(g[2]) > epochBefore.G && Number(a[2]) > epochBefore.A ? { g, a } : null;
    }, (RECONCILE + 30) * 1000);
    check(!!adopted, "G and A adopted by the new instance, epoch advanced (ADR-0008)", adopted ? `G ${adopted.g[2]}, A ${adopted.a[2]}` : "not adopted");
    {
      // Both players of G return. Their reservations were opened at adoption, not at the stop.
      const owner = redis("get", `room:${G.roomId}:pod`);
      check(leases[0] === `pod:${owner}:alive`, "room:G:pod names the new instance", owner);
      const a2 = await login("alice"), b2 = await login("bob");
      const gRes = await api(a2, "GET", `/api/rooms/${G.roomId}`);
      const gState = gRes.json?.room ?? gRes.json;
      check(gState?.state === "IN_PROGRESS", "G still IN_PROGRESS after the restart", `${gRes.status} ${JSON.stringify(gRes.json).slice(0, 200)}`);
      const [ca, cb] = await Promise.all([connect(a2), connect(b2)]);
      for (const x of [ca, cb]) { x.sub(`/topic/room.${G.roomId}`); x.sub(`/topic/game.${G.sid}`); x.sub("/user/queue/game"); x.sub("/user/queue/errors"); }
      await sleep(500);
      const resumed = await sync(ca, G.sid);
      check(JSON.stringify(resumed.board) === boardBefore, "G session record intact: same board, onInit not re-run (game-host §9.1, §9.3)", JSON.stringify(resumed.board));
      const released = sql(`SELECT count(*) FROM room_participant WHERE room_id='${G.roomId}' AND left_at IS NOT NULL`);
      check(released === "0", "no G participant was released by the outage", `released=${released}`);
      const [X2, O2] = resumed.yourMark === "X" ? [ca, cb] : [cb, ca];
      await move(X2, O2, G.sid, 1); // X: 0,1  O: 3
      await move(O2, X2, G.sid, 4);
      await move(X2, O2, G.sid, 2); // top row
      const over = await ca.wait((m) => m.type === "GAME_OVER", 20000).catch(() => null);
      check(!!over, "G resumed and finished: moves applied once, in order (sequence continues)");
      extra.push(ca, cb);
    }

    // A: nobody returns. Grace restarted at adoption; closes after it plus a sweep.
    const closed = await until("A closed", () => roomRow(A.roomId)[0] === "CLOSED" && roomRow(A.roomId), (GRACE + RECONCILE + 40) * 1000);
    check(!!closed, "A (nobody returned) closed once grace, counted from adoption, elapsed", closed ? closed.join("|") : roomRow(A.roomId).join("|"));
    check(closed?.[1] === "GRACE_EXPIRED_NO_HUMAN", "A closed_reason = GRACE_EXPIRED_NO_HUMAN", closed?.[1]);
    const keysGone = await until("A session keys gone", () => redis("exists", `session:${A.sid}`) === "0" && redis("exists", `queue:${A.sid}`) === "0", 60000);
    check(!!keysGone, "A session record and queue torn down (ADR-0010)");
    check(redis("exists", `room:${A.roomId}:pod`) === "0", "A ownership keys deleted at closure");

    // L: a lobby room is not closed by the restart, nor by the grace expiring on its absent host.
    const lobbyNow = roomRow(lobbyId);
    check(lobbyNow[0] === "LOBBY", "L still LOBBY right after the restart (FR-DC-007)", lobbyNow.join("|"));
    await sleep(8000);
    const lobbyLate = roomRow(lobbyId);
    check(lobbyLate[1] !== "GRACE_EXPIRED_NO_HUMAN", "L not closed as GRACE_EXPIRED_NO_HUMAN once grace elapsed", lobbyLate.join("|"));

    for (const x of [G.h, G.g, A.h, A.g, lobbySock, ...extra]) try { x.ws.close(); } catch { /* already closed */ }
  } finally {
    if (!KEEP) { try { dc("down", "-v"); } catch { /* nothing to stop */ } }
    if (createdEnv) rmSync(ENV_FILE, { force: true });
  }
  if (failures.length) { console.error(`\nFAILED (${failures.length}): ${failures.join("; ")}`); process.exit(1); }
  console.log(`\nRECOVERY TEST PASSED (${KILL ? "kill" : "graceful"} stop)`);
}
main().catch((e) => { console.error("ERROR: " + (e?.stack ?? e)); process.exit(2); });
