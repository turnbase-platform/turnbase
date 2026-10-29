// Pairs that survive the loss of their Platform instance: the client of FR-DC / FR-DEPLOY-001 that, when its socket
// is closed (RECONNECT_REQUIRED) or its owner dies, reconnects, rejoins the room's topics, re-syncs the game and
// carries on, retrying ROOM_UNAVAILABLE_RETRY inside a budget. Used by test/scale-in-midgame.sh (IMP-M18-10).
// Usage: k6 run loadtest/scenarios/scale-in.js
// Env: WATCHED_PAIRS (8), DURATION_S (240), LOAD_PAIRS (0), LOAD_HOLD_S (150: how long the plain load pairs hold),
//      RETRY_BUDGET_MS (30000), THINK_MIN_MS / THINK_MAX_MS (800 / 1500, so that a game lasts several seconds).
// Outcome per watched game: finished; aborted (the disturbance hit before the game started: the room is left and a
// new one made, nothing was lost); lost (started, never finished). Pass = no lost game, no budget exceeded.
import { Counter, Trend } from 'k6/metrics';
import { cfg } from '../lib/config.js';
import { ok, fail } from '../lib/metrics.js';
import { loginAll, errorCode } from '../lib/player.js';
import { baseOptions, playPair } from '../lib/shape.js';
import { getPair, isOver, pickEmpty } from '../lib/pair.js';

const num = (k, d) => Number(__ENV[k] || d);
const WATCHED = num('WATCHED_PAIRS', 8);
const DURATION_S = num('DURATION_S', 240);
const LOAD = num('LOAD_PAIRS', 0);
const LOAD_HOLD_S = num('LOAD_HOLD_S', 150);
const BUDGET_MS = num('RETRY_BUDGET_MS', 30000);
const THINK_MIN = num('THINK_MIN_MS', 800);
const THINK_MAX = num('THINK_MAX_MS', 1500);
const T = cfg.stepTimeoutMs;

const finished = new Counter('tb_si_games_finished');
const aborted = new Counter('tb_si_games_aborted');
const lost = new Counter('tb_si_games_lost');
const recoveries = new Counter('tb_si_recoveries');
const exceeded = new Counter('tb_si_budget_exceeded');
const restRetries = new Counter('tb_si_rest_retries');
const recoverMs = new Trend('tb_si_recover_ms', true);

const scenarios = {
  watched: { executor: 'constant-vus', vus: WATCHED, duration: DURATION_S + 's', exec: 'watched', gracefulStop: '90s' },
};
if (LOAD > 0) {
  scenarios.load = { executor: 'ramping-vus', startVUs: 0, gracefulRampDown: '30s', gracefulStop: '60s', exec: 'load',
    stages: [{ duration: '30s', target: LOAD }, { duration: LOAD_HOLD_S + 's', target: LOAD }, { duration: '10s', target: 0 }] };
}
export const options = baseOptions(scenarios, {
  tb_si_games_lost: ['count==0'],
  tb_si_budget_exceeded: ['count==0'],
  tb_si_games_finished: ['count>0'],
});

export function setup() { return loginAll(2 * (WATCHED + LOAD) + 2); }

export function load(data) { return playPair(data); }

const sleepMs = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function view(f) {
  const v = f.msg.payload.view;
  return { id: f.msg.payload.init.self.id, board: v.board.slice(), turn: v.turn };
}

// Reconnects both players, rejoins the room and game topics; retries inside the budget.
async function recover(pair, roomId, sid) {
  const players = [pair.host, pair.guest];
  const t0 = Date.now();
  recoveries.add(1);
  for (;;) {
    if (Date.now() - t0 > BUDGET_MS) {
      exceeded.add(1);
      throw Object.assign(new Error('retry budget exceeded'), { code: 'retry_budget' });
    }
    try {
      players.forEach((p) => { p.close(); p.ws = null; p.wsHint = null; });
      await Promise.all(players.map((p) => p.ensureConnected()));
      await Promise.all(players.map((p) => p.ws.subscribeConfirmed('/topic/room.' + roomId, 2500)));
      players.forEach((p) => p.ws.subscribe('/topic/game.' + sid));
      recoverMs.add(Date.now() - t0);
      return;
    } catch (_) {
      await sleepMs(2000); // ROOM_UNAVAILABLE_RETRY's Retry-After
    }
  }
}

async function syncBoth(pair, sid) {
  const players = [pair.host, pair.guest];
  players.forEach((p) => p.ws.send('/app/game.' + sid + '.sync', 'REQUEST_GAME_SYNC'));
  const frames = await Promise.all(players.map((p) => p.ws.waitFor((f) => f.msg && f.msg.type === 'GAME_SYNC', T, 'sync_timeout')));
  const views = frames.map(view);
  const byId = {};
  players.forEach((p, i) => { byId[views[i].id] = p; });
  return { board: views[0].board, turn: views[0].turn, byId };
}

// A REST call for a room another instance owns answers 503 ROOM_UNAVAILABLE_RETRY (round-robin lands on a non-owner);
// the client's answer is to retry, and so is this one, inside the same budget.
async function restWithRetry(player, method, path, body, name, okStatus) {
  const t0 = Date.now();
  for (;;) {
    const r = await player.request(method, path, body, name);
    if (r.res.status === okStatus) return r;
    if (r.res.status !== 503 || Date.now() - t0 > BUDGET_MS) throw Object.assign(new Error(name + ' ' + r.res.status), { code: errorCode(r.res) });
    restRetries.add(1);
    await sleepMs(1000);
  }
}

async function oneGame(pair) {
  const { host, guest } = pair;
  const players = [host, guest];
  let roomId = null;
  let sid = null;
  try {
    const created = await restWithRetry(host, 'POST', '/api/rooms',
      { gameId: cfg.gameId, visibility: 'PUBLIC', spectatingEnabled: false }, 'POST /api/rooms', 201);
    const body = created.res.json();
    roomId = body.roomId || (body.room && body.room.roomId);
    host.wsHint = created.res.headers['X-Turnbase-Room-Instance'] || null;
    const joined = await restWithRetry(guest, 'POST', '/api/rooms/' + roomId + '/participants', { role: 'PLAYER' },
      'POST /api/rooms/{id}/participants', 201);
    guest.wsHint = joined.res.headers['X-Turnbase-Room-Instance'] || null;
    await Promise.all(players.map((p) => p.ensureConnected()));
    await Promise.all(players.map((p) => p.ws.subscribeConfirmed('/topic/room.' + roomId, T)));
    guest.ws.send('/app/room.' + roomId + '.member', 'TOGGLE_READY', { ready: true });
    await host.ws.waitFor((f) => f.msg && f.msg.type === 'READINESS_CHANGED', T, 'ready_timeout');
    host.ws.send('/app/room.' + roomId + '.host', 'START_GAME');
    const isStarted = (f) => f.msg && f.msg.type === 'GAME_STARTED';
    const [started] = await Promise.all(players.map((p) => p.ws.waitFor(isStarted, cfg.startTimeoutMs, 'start_timeout')));
    sid = started.msg.payload.sessionId;
  } catch (e) {
    aborted.add(1);
    if (__ENV.DEBUG) console.error('aborted before start: ' + e.code + ' ' + e.message);
    await cleanup(pair, roomId);
    await sleepMs(cfg.errorBackoffMs);
    return;
  }
  try {
    players.forEach((p) => p.ws.subscribe('/topic/game.' + sid));
    let state = await syncBoth(pair, sid).catch(async () => { await recover(pair, roomId, sid); return syncBoth(pair, sid); });
    while (!isOver(state.board)) {
      try {
        const mover = state.byId[state.turn];
        const cell = pickEmpty(state.board);
        await sleepMs(THINK_MIN + Math.random() * (THINK_MAX - THINK_MIN));
        mover.ws.send('/app/game.' + sid + '.action', 'SUBMIT_ACTION', { cell });
        const f = await mover.ws.waitFor((x) => x.msg && x.msg.type === 'GAME_EVENT' && x.msg.sessionId === sid
          && x.msg.payload && ((x.msg.payload.type === 'move' && x.msg.payload.cell === cell) || x.msg.payload.type === 'rejected'),
        T, 'move_timeout');
        if (f.msg.payload.type === 'rejected') throw Object.assign(new Error('move rejected'), { code: 'move_rejected' });
        state.board[cell] = f.msg.payload.mark;
        state.turn = f.msg.payload.next;
        ok();
      } catch (_) {
        await recover(pair, roomId, sid);
        state = await syncBoth(pair, sid);
      }
    }
    finished.add(1);
  } catch (e) {
    lost.add(1);
    fail(e.code || 'exception');
    console.error('game lost in room ' + roomId + ': ' + e.code + ' ' + e.message);
  } finally {
    await cleanup(pair, roomId);
  }
}

async function cleanup(pair, roomId) {
  if (roomId) {
    for (const p of [pair.host, pair.guest]) {
      try { await p.request('DELETE', '/api/rooms/' + roomId + '/participants/me', null, 'DELETE /api/rooms/{id}/participants/me'); } catch (_) { /* best effort */ }
    }
  }
  pair.host.close();
  pair.guest.close();
}

export async function watched(data) {
  await oneGame(getPair(data));
}

