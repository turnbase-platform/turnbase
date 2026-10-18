// The pair game loop: one VU drives two users through room -> ready -> start -> play -> rematch.
// Port of the protocol in .claude/skills/run-turnbase/driver.mjs; destinations in load-testing.md §3.6.
import exec from 'k6/execution';
import { cfg, pairUsers } from './config.js';
import { m, ok, fail, stepTags } from './metrics.js';
import { Player, errorCode } from './player.js';

const PAIRS_PROVISIONED = 1000;
const LINES = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]];
const sleepMs = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Harness helpers for choosing legal moves, not platform logic. `empty` is the board's empty value;
// when omitted, a falsy cell is empty.
const isEmptyCell = (c, empty) => (empty === undefined ? !c : c === empty);

export function winner(board, empty) {
  for (const [a, b, c] of LINES) {
    if (!isEmptyCell(board[a], empty) && board[a] === board[b] && board[a] === board[c]) return board[a];
  }
  return null;
}

export function isOver(board, empty) {
  return winner(board, empty) !== null || !board.some((c) => isEmptyCell(c, empty));
}

export function pickEmpty(board, empty) {
  const cells = [];
  board.forEach((c, i) => { if (isEmptyCell(c, empty)) cells.push(i); });
  return cells[Math.floor(Math.random() * cells.length)];
}

// The one place that knows the GAME_SYNC field names.
function readView(f) {
  const v = f.msg.payload.view;
  return { id: f.msg.payload.init.self.id, mark: v.yourMark, board: v.board.slice(), turn: v.turn };
}

const pairs = {};
export function getPair(data) {
  const idx = exec.vu.idInTest - 1;
  if (idx >= PAIRS_PROVISIONED) throw new Error('VU id beyond provisioned users');
  if (!pairs[idx]) {
    const [hostName, guestName] = pairUsers(idx);
    const cookies = (data && data.cookies) || {};
    pairs[idx] = { host: new Player(hostName, cookies[hostName]), guest: new Player(guestName, cookies[guestName]),
      gamesStarted: 0, counted: false };
  }
  return pairs[idx];
}

async function leave(p, roomId) {
  // Defensive cleanup: not counted as a failure whatever it returns.
  try { await p.request('DELETE', '/api/rooms/' + roomId + '/participants/me', null, 'DELETE /api/rooms/{id}/participants/me'); } catch (_) { /* ignore */ }
}

// A server-side error frame explains a timeout better than the timeout does.
function serverErrorCode(players) {
  for (const p of players) {
    if (!p.ws) continue;
    const f = p.ws.buffer.find((x) => x.headers.destination === '/user/queue/errors' && x.msg && x.msg.payload);
    if (f) return f.msg.payload.code || 'server_error';
  }
  return null;
}

async function think() {
  if (cfg.thinkMaxMs > 0) await sleepMs(cfg.thinkMinMs + Math.random() * (cfg.thinkMaxMs - cfg.thinkMinMs));
}

async function playGame(pair, roomId) {
  const { host, guest } = pair;
  const T = cfg.stepTimeoutMs;
  host.ws.clear();
  guest.ws.clear();

  const tReady = guest.ws.send('/app/room.' + roomId + '.member', 'TOGGLE_READY', { ready: true });
  const ready = await host.ws.waitFor((f) => f.msg && f.msg.type === 'READINESS_CHANGED', T, 'ready_timeout');
  m.lobbyEvent.add(ready.t - tReady, stepTags());
  ok();

  const cold = pair.gamesStarted === 0 && Date.now() - exec.scenario.startTime < cfg.coldWindowMs;
  const tStart = host.ws.send('/app/room.' + roomId + '.host', 'START_GAME');
  const isStarted = (f) => f.msg && f.msg.type === 'GAME_STARTED';
  const [startedHost] = await Promise.all([
    host.ws.waitFor(isStarted, cfg.startTimeoutMs, 'start_timeout'),
    guest.ws.waitFor(isStarted, cfg.startTimeoutMs, 'start_timeout'),
  ]);
  m.gameStart.add(startedHost.t - tStart, stepTags({ cold: String(cold) }));
  pair.gamesStarted++;
  ok();
  const sid = startedHost.msg.payload.sessionId;
  m.activeGames.add(1);

  const gameSubs = [host.ws.subscribe('/topic/game.' + sid), guest.ws.subscribe('/topic/game.' + sid)];
  try {
    const views = await Promise.all([host, guest].map(async (p) => {
      p.ws.send('/app/game.' + sid + '.sync', 'REQUEST_GAME_SYNC');
      return readView(await p.ws.waitFor((f) => f.msg && f.msg.type === 'GAME_SYNC', T, 'sync_timeout'));
    }));
    ok();
    const byId = {};
    [host, guest].forEach((p, i) => { byId[views[i].id] = p; });
    const empty = views[0].board[0];
    const board = views[0].board;
    let turn = views[0].turn;

    let tFirstMove = 0;
    while (!isOver(board, empty)) {
      const mover = byId[turn];
      if (!mover) throw Object.assign(new Error('no player holds the turn ' + turn), { code: 'unknown_turn' });
      const cell = pickEmpty(board, empty);
      await think();
      const t0 = mover.ws.send('/app/game.' + sid + '.action', 'SUBMIT_ACTION', { cell });
      if (!tFirstMove) tFirstMove = t0;
      const f = await mover.ws.waitFor((x) => x.msg && x.msg.type === 'GAME_EVENT' && x.msg.sessionId === sid
        && x.msg.payload && ((x.msg.payload.type === 'move' && x.msg.payload.cell === cell) || x.msg.payload.type === 'rejected'),
      T, 'move_timeout');
      if (f.msg.payload.type === 'rejected') throw Object.assign(new Error('move rejected'), { code: 'move_rejected' });
      m.moveRtt.add(f.t - t0, stepTags());
      board[cell] = f.msg.payload.mark;
      turn = f.msg.payload.next;
      ok();
    }

    await Promise.all([host, guest].map((p) => p.ws.waitFor((f) => f.msg && f.msg.type === 'GAME_OVER', T, 'game_over_timeout')));
    m.gameDuration.add(Date.now() - tFirstMove, stepTags());
    await Promise.all([host, guest].map((p) => p.ws.waitFor((f) => f.msg && f.msg.type === 'GAME_ENDED', T, 'game_ended_timeout')));
    m.gamesCompleted.add(1, stepTags());
    ok();
  } finally {
    m.activeGames.add(0);
    host.ws.unsubscribe(gameSubs[0]);
    guest.ws.unsubscribe(gameSubs[1]);
  }
}

// Plays `games` games in ONE room (the second and later are rematches), then leaves it and closes both sockets.
export async function pairSession(pair, { games }) {
  const { host, guest } = pair;
  if (!pair.counted) { // first iteration: make the zero-valued counters print in the summary
    pair.counted = true;
    m.errors.add(0);
    m.wsDisconnects.add(0);
  }
  let roomId = null;
  let failed = false;
  const roomSubs = [];
  try {
    await Promise.all([host.ensureConnected(), guest.ensureConnected()]);
    const created = await host.request('POST', '/api/rooms',
      { gameId: cfg.gameId, visibility: 'PUBLIC', spectatingEnabled: false }, 'POST /api/rooms');
    if (created.res.status !== 201) throw Object.assign(new Error('room create ' + created.res.status), { code: errorCode(created.res) });
    const body = created.res.json();
    roomId = body.roomId || (body.room && body.room.roomId);
    m.roomCreate.add(created.ms, stepTags());
    ok();

    const joined = await guest.request('POST', '/api/rooms/' + roomId + '/participants', { role: 'PLAYER' },
      'POST /api/rooms/{id}/participants');
    if (joined.res.status !== 201) throw Object.assign(new Error('room join ' + joined.res.status), { code: errorCode(joined.res) });
    m.roomJoin.add(joined.ms, stepTags());
    ok();

    roomSubs.push(host.ws.subscribe('/topic/room.' + roomId), guest.ws.subscribe('/topic/room.' + roomId));
    // The simple broker sends no RECEIPT, and the two sockets are processed independently: without a pause the
    // guest's first TOGGLE_READY can be broadcast before the host's subscription exists (seen as ready_timeout).
    await sleepMs(cfg.subscribeSettleMs);
    for (let g = 0; g < games; g++) await playGame(pair, roomId);
  } catch (e) {
    failed = true;
    if (__ENV.DEBUG) console.error('pairSession failed: ' + e.code + ' ' + e.message + ' ' + (e.stack || ''));
    const known = e.code === 'timeout' || /_timeout$/.test(e.code || '') ? serverErrorCode([host, guest]) : null;
    fail(known || e.code || 'exception');
  } finally {
    if (roomId) {
      await leave(host, roomId);
      await leave(guest, roomId);
      if (host.ws) host.ws.unsubscribe(roomSubs[0]);
      if (guest.ws) guest.ws.unsubscribe(roomSubs[1]);
    }
    // An open socket (and its heart-beat timer) keeps a k6 iteration from ever ending, so the sockets live
    // for one pairSession, not for the VU.
    host.close();
    guest.close();
    if (failed) await sleepMs(cfg.errorBackoffMs);
  }
}
