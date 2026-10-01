#!/usr/bin/env node
// Multi-actor black-box driver for the local TurnBase stack (compose, :8080).
// Four independent cookie jars = four "browsers": players alice and bob, spectator carol, outsider dave
// (the seeded `local` users, password `password`). Guests are not used: guest creation is limited to 5 per IP per hour.
// Usage (from the repo root):  node .claude/skills/run-turnbase/driver.mjs [scenario]
//   scenario: game (default) | drop | leave   (each starts a fresh room; drop/leave stop mid-game)
// Prints one JSON line of measurements; exits non-zero on the first thing that does not happen.
import { createRequire } from "node:module";
import { randomUUID } from "node:crypto";
const require = createRequire(new URL("../../../turnbase-game-tictactoe/package.json", import.meta.url));
const WebSocket = require("ws");

const GAME = "2cc66e36-52e6-4144-9a10-09d09c982ce4";
const HOST = process.env.PLATFORM_HOST ?? "turnbase.localhost:8080";
const BASE = process.env.PLATFORM_URL ?? "http://127.0.0.1:8080";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const fail = (m) => { console.error("FAIL: " + m); process.exit(1); };

async function api(actor, method, path, body) {
  const res = await fetch(BASE + path, {
    method,
    headers: { Host: HOST, ...(actor.cookie ? { Cookie: actor.cookie } : {}), ...(body ? { "Content-Type": "application/json" } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  const t = await res.text();
  return { status: res.status, json: t ? JSON.parse(t) : null, res };
}

async function login(name) {
  const a = { name };
  const r = await api(a, "POST", "/api/auth/login", { usernameOrEmail: name, password: "password" });
  if (r.status >= 300) fail(`login ${name}: ${r.status}`);
  a.cookie = r.res.headers.getSetCookie().map((c) => c.split(";")[0]).join("; ");
  return a;
}

// Minimal STOMP client. Sends a heartbeat every 4 s: a client that does not is closed by the server.
function connect(actor) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(`ws://${BASE.replace(/^https?:\/\//, "")}/ws`, { headers: { Cookie: actor.cookie, Origin: `http://${HOST}`, Host: HOST } });
    const c = { ws, frames: [], waiters: [], closed: null };
    ws.on("open", () => { ws.send("CONNECT\naccept-version:1.2\nheart-beat:10000,10000\n\n\0"); c.hb = setInterval(() => ws.readyState === 1 && ws.send("\n"), 4000); });
    ws.on("error", reject);
    ws.on("close", (code) => { clearInterval(c.hb); c.closed = code; });
    ws.on("message", (d) => {
      const t = Date.now();
      for (const raw of String(d).split("\0")) {
        const text = raw.replace(/^\n+/, ""); if (!text) continue;
        const [head, ...rest] = text.split("\n\n");
        const [command, ...hl] = head.split("\n");
        let msg = null; try { msg = JSON.parse(rest.join("\n\n")); } catch {}
        const f = { command, msg, t, dest: (hl.find((l) => l.startsWith("destination:")) ?? "").slice(12) };
        if (command === "CONNECTED") resolve(c);
        c.frames.push(f); c.waiters = c.waiters.filter((w) => !w(f));
      }
    });
    c.sub = (d) => ws.send(`SUBSCRIBE\nid:${randomUUID()}\ndestination:${d}\n\n\0`);
    c.cmd = (d, type, payload = {}) => { const t = Date.now(); ws.send(`SEND\ndestination:${d}\ncontent-type:application/json\n\n${JSON.stringify({ type, correlationId: randomUUID(), payload })}\0`); return t; };
    c.wait = (pred, ms = 15000) => {
      const hit = c.frames.find((f) => f.msg && pred(f.msg));
      if (hit) return Promise.resolve(hit);
      return new Promise((res, rej) => {
        const to = setTimeout(() => rej(new Error("timeout waiting for frame")), ms);
        c.waiters.push((f) => { if (f.msg && pred(f.msg)) { clearTimeout(to); res(f); return true; } return false; });
      });
    };
  });
}

async function setup() {
  const [A, B, C, D] = await Promise.all(["alice", "bob", "carol", "dave"].map(login));
  const room = (await api(A, "POST", "/api/rooms", { gameId: GAME, visibility: "PUBLIC", spectatingEnabled: true })).json;
  const roomId = room.roomId ?? room.room?.roomId;
  if ((await api(B, "POST", `/api/rooms/${roomId}/participants`, { role: "PLAYER" })).status !== 201) fail("B join");
  if ((await api(C, "POST", `/api/rooms/${roomId}/participants`, { role: "SPECTATOR" })).status !== 201) fail("C spectate");
  const [a, b, c, d] = await Promise.all([A, B, C, D].map(connect));
  for (const x of [a, b, c]) { x.sub(`/topic/room.${roomId}`); x.sub("/user/queue/errors"); x.sub("/user/queue/game"); }
  d.sub(`/topic/room.${roomId}`);
  await sleep(500);
  b.cmd(`/app/room.${roomId}.member`, "TOGGLE_READY", { ready: true });
  await a.wait((m) => m.type === "READINESS_CHANGED");
  const t0 = a.cmd(`/app/room.${roomId}.host`, "START_GAME");
  const started = await a.wait((m) => m.type === "GAME_STARTED", 30000);
  const sid = started.msg.payload.sessionId;
  for (const x of [a, b, c, d]) x.sub(`/topic/game.${sid}`);
  await sleep(500);
  return { A, B, C, D, a, b, c, d, roomId, sid, startMs: started.t - t0 };
}

async function game(w, out) {
  const { a, b, c, d, roomId, sid } = w;
  const marks = {};
  for (const [n, x] of [["a", a], ["b", b], ["c", c]]) { x.cmd(`/app/game.${sid}.sync`, "REQUEST_GAME_SYNC"); marks[n] = (await x.wait((m) => m.type === "GAME_SYNC")).msg.payload.view.yourMark; }
  out.marks = marks;
  const [X, O] = marks.a === "X" ? [a, b] : [b, a];
  // spectator and outsider must not be able to act or listen
  const n0 = c.frames.length; c.cmd(`/app/game.${sid}.action`, "SUBMIT_ACTION", { cell: 4 }); await sleep(600);
  out.spectatorAction = c.frames.slice(n0).find((f) => f.msg?.type === "ERROR")?.msg.payload.code;
  if (out.spectatorAction !== "ROLE_NOT_ELIGIBLE") fail("spectator action not refused");
  d.cmd(`/app/game.${sid}.action`, "SUBMIT_ACTION", { cell: 4 });
  out.moveLatencyMs = [];
  for (const [p, cell] of [[X, 0], [O, 3], [X, 1], [O, 4], [X, 2]]) {
    const t = p.cmd(`/app/game.${sid}.action`, "SUBMIT_ACTION", { cell });
    const f = await c.wait((m) => m.type === "GAME_EVENT" && m.sessionId === sid && m.payload?.type === "move" && m.payload.cell === cell);
    out.moveLatencyMs.push(f.t - t);
  }
  await a.wait((m) => m.type === "GAME_OVER");
  await a.wait((m) => m.type === "GAME_ENDED");
  out.outsiderFrames = d.frames.filter((f) => f.command === "MESSAGE").length;
  if (out.outsiderFrames) fail("outsider received frames");
}

async function drop(w, out) {
  const { a, b, B, roomId, sid } = w;
  b.ws.close(); await sleep(2500);
  out.disconnect = (await a.wait((m) => m.type === "PLAYER_DISCONNECTED")).msg.payload.gracePeriodSeconds;
  const b2 = await connect(B);
  b2.sub(`/topic/room.${roomId}`); b2.sub(`/topic/game.${sid}`); b2.sub("/user/queue/game"); b2.sub("/user/queue/errors"); await sleep(300);
  b2.cmd(`/app/game.${sid}.sync`, "REQUEST_GAME_SYNC");
  out.resyncBoard = (await b2.wait((m) => m.type === "GAME_SYNC")).msg.payload.view.board.join("");
  await a.wait((m) => m.type === "PLAYER_RECONNECTED");
  w.b = b2;
}

async function leave(w, out) {
  const { A, B, a, roomId } = w;
  out.leaveStatus = (await api(B, "DELETE", `/api/rooms/${roomId}/participants/me`)).status;
  await sleep(1500);
  out.afterLeave = a.frames.slice(-3).map((f) => f.msg?.type);
  out.roomState = (await api(A, "GET", `/api/rooms/${roomId}`)).json.state;
}

const which = process.argv[2] ?? "game";
const w = await setup();
const out = { scenario: which, warmOrColdStartMs: w.startMs };
if (which === "game") await game(w, out);
if (which === "drop") await drop(w, out);
if (which === "leave") await leave(w, out);
console.log(JSON.stringify(out));
for (const x of [w.a, w.b, w.c, w.d]) x.ws.close();
process.exit(0);
