// Metric declarations. Task 9 (IMP-M15-09) adds `stepper` and `thresholds`; the pair loop (IMP-M15-08)
// is the other writer.
import { Trend, Counter, Gauge, Rate } from 'k6/metrics';

export const m = {
  login: new Trend('tb_login', true),
  roomCreate: new Trend('tb_room_create', true),
  roomJoin: new Trend('tb_room_join', true),
  lobbyEvent: new Trend('tb_lobby_event', true),
  gameStart: new Trend('tb_game_start', true), // tagged cold=true|false
  moveRtt: new Trend('tb_move_rtt', true),
  gameDuration: new Trend('tb_game_duration', true),
  gamesCompleted: new Counter('tb_games_completed'),
  errors: new Counter('tb_errors'), // tags: code, expected
  wsDisconnects: new Counter('tb_ws_disconnects'), // unexpected socket closes only
  // Last value any VU wrote; reports take concurrent games from turnbase_game_sessions_active instead.
  activeGames: new Gauge('tb_active_games'),
  opFailed: new Rate('tb_op_failed'), // 1 per failed operation, 0 per successful one
};
export const provisionCreated = new Counter('tb_provision_created');
export const provisionExisting = new Counter('tb_provision_existing');

let expected = new Set();
export function expectCodes(list) { expected = new Set(list); }
export function ok(tags) { m.opFailed.add(false, tags || {}); }
export function fail(code, tags) {
  const t = Object.assign({}, tags || {});
  m.errors.add(1, Object.assign({ code, expected: String(expected.has(code)) }, t));
  m.opFailed.add(true, t);
}
