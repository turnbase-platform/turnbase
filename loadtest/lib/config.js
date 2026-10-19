// Run parameters, all from the environment so a run's params.txt can reproduce it.
const e = (k, d) => (__ENV[k] !== undefined && __ENV[k] !== '' ? __ENV[k] : d);
const n = (k, d) => Number(e(k, d));
const baseUrl = e('BASE_URL', 'http://turnbase.localhost').replace(/\/$/, '');
const host = baseUrl.replace(/^https?:\/\//, ''); // host[:port]
export const cfg = {
  baseUrl, host, origin: baseUrl,
  wsUrl: baseUrl.replace(/^http/, 'ws') + '/ws',
  hostIp: e('HOST_IP', ''), // maps host -> ip when ::1 does not work
  gameId: e('GAME_ID', '2cc66e36-52e6-4144-9a10-09d09c982ce4'),
  userPrefix: e('USER_PREFIX', 'lt-'),
  password: e('PASSWORD', 'Loadtest-Passw0rd-2026'),
  thinkMinMs: n('THINK_MIN_MS', 0), thinkMaxMs: n('THINK_MAX_MS', 0),
  freshRoomEvery: n('FRESH_ROOM_EVERY', 5),
  stepSeconds: n('STEP_SECONDS', 120), settleSeconds: n('SETTLE_SECONDS', 20),
  thresholdScale: n('THRESHOLD_SCALE', 1),
  coldWindowMs: n('COLD_WINDOW_MS', 30000),
  startTimeoutMs: n('START_TIMEOUT_MS', 120000), stepTimeoutMs: n('STEP_TIMEOUT_MS', 10000),
  errorBackoffMs: n('ERROR_BACKOFF_MS', 1000),
  pairs: n('PAIRS', 1), // smoke.js: concurrent pairs, each its own two users
  subscribeSettleMs: n('SUBSCRIBE_SETTLE_MS', 50), // pause after the room subscriptions, before the first ready
};
export const userName = (i) => cfg.userPrefix + String(i).padStart(5, '0');
export const pairUsers = (p) => [userName(2 * p), userName(2 * p + 1)]; // VU id v -> pair v-1
export const hostsOption = () => (cfg.hostIp ? { [cfg.host.split(':')[0]]: cfg.hostIp } : {});
