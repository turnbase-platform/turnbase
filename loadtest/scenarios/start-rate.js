// Open model: new games per second, stepped upward. Each iteration creates a room, joins, readies, starts,
// plays one game and leaves. Stresses game_start as a rate independent of concurrency.
// Usage: k6 run loadtest/scenarios/start-rate.js
// Env: RATES (1,2,4,8,16,32 games/s), STEP_SECONDS (120), SETTLE_SECONDS (20), MAX_PAIRS (400, the VU cap).
import { stepper, thresholds } from '../lib/metrics.js';
import { cfg } from '../lib/config.js';
import { envNum, envList, levelStages, levelSegments, baseOptions, loginAll } from '../lib/shape.js';
import { getPair, pairSession } from '../lib/pair.js';

const rates = envList('RATES', '1,2,4,8,16,32');
const maxPairs = envNum('MAX_PAIRS', 400);
stepper.configure(levelSegments(rates), cfg.settleSeconds);

export const options = baseOptions({
  'start-rate': {
    executor: 'ramping-arrival-rate', startRate: 1, timeUnit: '1s',
    preAllocatedVUs: Math.min(50, maxPairs), maxVUs: maxPairs,
    stages: levelStages(rates), gracefulStop: '60s',
  },
}, thresholds({ steps: rates.map(String), abort: false }));

export function setup() { return loginAll(2 * maxPairs); }

export default async function (data) {
  await pairSession(getPair(data), { games: 1 });
}
