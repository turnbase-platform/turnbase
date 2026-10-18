// Every limiter enabled (the stock chart, no `loadtest` profile): confirms the limiters answer under load
// and that nothing else breaks. Deploy first: `bash loadtest/install.sh --default-limits`.
// Usage: k6 run loadtest/scenarios/default-limits.js
// Env: VUS (20 pairs), DURATION (3m), LOGIN_PARALLEL (2). Does not provision: the stock limits allow 3 registrations an hour,
// so run provision.js under the loadtest overlay first (README, *Run procedure*).
// Pass: no unexpected error, at least one RATE_LIMIT_EXCEEDED, no 5xx.
import { thresholds, expectCodes } from '../lib/metrics.js';
import { envNum, baseOptions, playPair, loginAll } from '../lib/shape.js';

const vus = envNum('VUS', 20);
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
