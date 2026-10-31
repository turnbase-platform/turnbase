// Ramp to a fraction (70%) of the scaled ceiling and hold it for an hour: drift and flapping under extended load
// (load-testing-phase-b.md §6).
// Usage: k6 run -e CEILING=<pairs> loadtest/scenarios/sustained-high.js
// Env: CEILING (required), FRACTION (0.7), RAMP_MINUTES (5), HOLD_MINUTES (60), DOWN_MINUTES (2). Tagged step:ramp|hold|down; no abort.
import { stepper, thresholds } from '../lib/metrics.js';
import { envNum, ceilingPairs, rampStages, baseOptions, vuScenario, playPair, loginAll } from '../lib/shape.js';

const pairs = ceilingPairs(envNum('FRACTION', 0.7));
const ramp = envNum('RAMP_MINUTES', 5);
const hold = envNum('HOLD_MINUTES', 60);
const down = envNum('DOWN_MINUTES', 2);
stepper.configure([{ tag: 'ramp', seconds: ramp * 60 }, { tag: 'hold', seconds: hold * 60 }, { tag: 'down', seconds: down * 60 }], 0);

export const options = baseOptions({
  'sustained-high': vuScenario('ramping-vus', { startVUs: 0, stages: [...rampStages([[ramp, pairs], [hold, pairs]]), ...rampStages([[down, 0]])] }),
}, thresholds({ steps: ['hold'], abort: false }));

export function setup() { return loginAll(2 * pairs); }
export default playPair;
