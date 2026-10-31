// Two compressed "days": a smooth rise from LOW (5%) to HIGH (60%) of the scaled ceiling, a plateau and a fall back
// (load-testing-phase-b.md §6). Answers: no flapping, no scale-in mid-game failures.
// Usage: k6 run -e CEILING=<pairs> loadtest/scenarios/diurnal.js
// Env: CEILING (required), DAYS (2), DAY_MINUTES (20), HIGH_FRACTION (0.6), LOW_FRACTION (0.05),
//      RISE_SHARE (0.3: the share of a day for the rise, and the same again for the fall; the rest is the plateau).
// Tagged step:rise|plateau|fall (every day alike); no threshold aborts.
import { stepper, thresholds } from '../lib/metrics.js';
import { envNum, ceilingPairs, rampStages, baseOptions, vuScenario, playPair, loginAll } from '../lib/shape.js';

const high = ceilingPairs(envNum('HIGH_FRACTION', 0.6));
const low = ceilingPairs(envNum('LOW_FRACTION', 0.05));
const days = envNum('DAYS', 2);
const day = envNum('DAY_MINUTES', 20);
const rise = day * envNum('RISE_SHARE', 0.3);
const plateau = day - 2 * rise;
const segments = [];
const stages = [];
for (let d = 0; d < days; d++) {
  segments.push({ tag: 'rise', seconds: rise * 60 }, { tag: 'plateau', seconds: plateau * 60 }, { tag: 'fall', seconds: rise * 60 });
  stages.push(...rampStages([[rise, high], [plateau, high], [rise, low]]));
}
stepper.configure(segments, 0);

export const options = baseOptions({
  diurnal: vuScenario('ramping-vus', { startVUs: low, stages }),
}, thresholds({ steps: ['plateau'], abort: false }));

export function setup() { return loginAll(2 * high); }
export default playPair;
