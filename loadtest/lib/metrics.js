// Metric declarations, the step tagger and the threshold set (load-testing.md §6).
import exec from 'k6/execution';
import { Trend, Counter, Gauge, Rate } from 'k6/metrics';
import { cfg } from './config.js';

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
  // The correctness check of IMP-M18-14 (correctness.sh): started = finished + abandoned, no gaps, no duplicates.
  gamesStarted: new Counter('tb_games_started'),
  gamesAbandoned: new Counter('tb_games_abandoned'), // the harness gave up on a started game (a failed iteration)
  restRetries: new Counter('tb_rest_retries'), // 503 ROOM_UNAVAILABLE_RETRY answered to a REST call on a non-owner
  seqChecked: new Counter('tb_seq_checked'), // broadcast GAME_EVENTs the gap/duplicate check looked at (proof it ran)
  seqGaps: new Counter('tb_seq_gaps'),
  seqDups: new Counter('tb_seq_dups'),
  wsDisconnects: new Counter('tb_ws_disconnects'), // unexpected socket closes only
  // Last value any VU wrote; reports take concurrent games from turnbase_game_sessions_active instead.
  activeGames: new Gauge('tb_active_games'),
  opFailed: new Rate('tb_op_failed'), // 1 per failed operation, 0 per successful one
};
export const provisionCreated = new Counter('tb_provision_created');
export const provisionExisting = new Counter('tb_provision_existing');

// Tags every sample with the step it belongs to, so a threshold judges one step and not the whole run
// (k6 thresholds are global; without a step tag a ramp would abort on the cumulative percentile).
// The first `settleSeconds` of each segment are tagged `warmup`, which no threshold selects.
let segments = [];
let settleMs = 0;
let clock = Date.now;
let startAt = null;
let planMs = 0;
export const stepper = {
  // segments: [{tag, seconds}] back to back from the scenario start; clock and start are injectable for tests.
  // `executorSeconds` is the length of the scenario's VU stages when it is not the sum of the segments (up-down).
  //
  // Steps are placed on the executor's own clock, `exec.scenario.progress` times the stage length, not on Date.now():
  // the VU stages run on the monotonic clock and the WSL 2 wall clock can be slewed (7% slow was measured, session 255),
  // which made a step's tag drift up to 95 s from the VUs that belong to it and cut the last step of the M17 runs
  // (`2026-10-24-m17-parallelism.md` finding 4). With an injected clock the old wall-clock path is used.
  configure(list, settleSeconds, now, startTime, executorSeconds) {
    segments = list;
    settleMs = settleSeconds * 1000;
    clock = now || Date.now;
    startAt = startTime === undefined ? null : startTime;
    planMs = 1000 * (executorSeconds || list.reduce((a, s) => a + s.seconds, 0));
  },
  tags() {
    if (segments.length === 0) return {};
    let elapsed;
    if (clock === Date.now && startAt === null) {
      try { elapsed = Math.min(1, exec.scenario.progress) * planMs; } catch (_) { return {}; } // setup() has no scenario
    } else {
      let start = startAt;
      if (start === null) {
        try { start = exec.scenario.startTime; } catch (_) { return {}; }
      }
      elapsed = clock() - start;
    }
    if (elapsed < 0) return { step: 'warmup' };
    let from = 0;
    let i = 0;
    while (i < segments.length - 1 && elapsed >= from + segments[i].seconds * 1000) from += segments[i++].seconds * 1000;
    return { step: elapsed - from < settleMs ? 'warmup' : segments[i].tag };
  },
};
const tagged = (t) => Object.assign({}, stepper.tags(), t || {});
export { tagged as stepTags };

let expected = new Set();
export function expectCodes(list) { expected = new Set(list); }
export function ok(tags) { m.opFailed.add(false, tagged(tags)); }
export function fail(code, tags) {
  const t = tagged(tags);
  m.errors.add(1, Object.assign({ code, expected: String(expected.has(code)) }, t));
  m.opFailed.add(true, t);
}

const LIMITS = [ // metric, extra tag, p95 ms, p99 ms
  ['tb_move_rtt', null, 200, 500],
  ['tb_room_create', null, 200, 500],
  ['tb_room_join', null, 200, 500],
  ['tb_lobby_event', null, 300, 600],
  ['tb_game_start', 'cold:false', 1000, 2000], // the cold start is recorded, not gated
];
const scaled = (v, scale) => parseFloat((v * scale).toPrecision(12));

// One threshold group per step. With abort, a failing threshold ends the run 30 s after the test start at
// the earliest (k6 counts delayAbortEval from the test start, not from the step).
export function thresholds({ steps = [null], abort = false, scale = cfg.thresholdScale, extra = {} } = {}) {
  const out = {};
  const entry = (t) => (abort ? { threshold: t, abortOnFail: true, delayAbortEval: '30s' } : t);
  for (const s of steps) {
    const key = (name, tag) => {
      const tags = [s == null ? null : 'step:' + s, tag].filter(Boolean).join(',');
      return tags ? name + '{' + tags + '}' : name;
    };
    for (const [name, tag, p95, p99] of LIMITS) {
      out[key(name, tag)] = [entry('p(95)<' + scaled(p95, scale)), entry('p(99)<' + scaled(p99, scale))];
    }
    out[key('tb_op_failed')] = [entry('rate<' + scaled(0.01, scale))];
    // Never fail; they only make k6 keep these per step, for steps-table.sh.
    out[key('tb_errors')] = ['count>=0'];
    out[key('tb_games_completed')] = ['count>=0'];
  }
  return Object.assign(out, extra);
}
