// Every limiter enabled (the stock chart, no `loadtest` profile): confirms the limiters answer under load
// and that nothing else breaks. Deploy first: `bash loadtest/install.sh --default-limits`.
// Usage: k6 run loadtest/scenarios/default-limits.js
// Env: VUS (20 pairs), DURATION (3m), LOGIN_PARALLEL (2). Does not provision: the stock limits allow 3 registrations an hour,
// so run provision.js under the loadtest overlay first (README, *Run procedure*).
// Think time: THINK_MIN_MS and THINK_MAX_MS default to 250 here (0 elsewhere). The WebSocket action bucket
// (burst 10, 5 per second) stays the product limit, and a client with no think time exhausts it in the third
// game of every iteration; that was a harness artefact (load-testing.md §13 finding 12), not a platform defect.
// Pass: no unexpected error, at least one RATE_LIMIT_EXCEEDED, no 5xx.
import { cfg } from '../lib/config.js';
import { thresholds, expectCodes } from '../lib/metrics.js';
import { envNum, baseOptions, playPair, loginAll } from '../lib/shape.js';

const vus = envNum('VUS', 20);
if (__ENV.THINK_MIN_MS === undefined || __ENV.THINK_MIN_MS === '') cfg.thinkMinMs = 250;
if (__ENV.THINK_MAX_MS === undefined || __ENV.THINK_MAX_MS === '') cfg.thinkMaxMs = 250;
expectCodes(['RATE_LIMIT_EXCEEDED']);

export const options = baseOptions(
  { 'default-limits': { executor: 'constant-vus', vus, duration: __ENV.DURATION || '3m', gracefulStop: '60s' } },
  thresholds({ steps: [], extra: {
    'tb_errors{expected:false}': ['count==0'],
    'tb_errors{code:RATE_LIMIT_EXCEEDED}': ['count>0'],
    'tb_errors{code:http_5xx}': ['count==0'],
  } }));

// A small login batch: the public tier is live.
export function setup() { return loginAll(2 * vus, 2); }
export default playPair;
