// Holds PAIRS concurrent pairs (about 70% of the ramp-to-break ceiling) to expose leaks and slow degradation.
// Usage: k6 run -e PAIRS=<n> loadtest/scenarios/soak.js
// Env: PAIRS (required), HOLD_MINUTES (30), RAMP_SECONDS (120; the ramp down takes half of it).
// Thresholds are global and none aborts: the question is the trend, not a step.
import { thresholds } from '../lib/metrics.js';
import { envNum, required, baseOptions, vuScenario, playPair, loginAll } from '../lib/shape.js';

const pairs = required('PAIRS');
const ramp = envNum('RAMP_SECONDS', 120);
const hold = envNum('HOLD_MINUTES', 30) * 60;

export const options = baseOptions({
  soak: vuScenario('ramping-vus', { startVUs: 0, stages: [
    { target: pairs, duration: ramp + 's' }, { target: pairs, duration: hold + 's' }, { target: 0, duration: Math.ceil(ramp / 2) + 's' },
  ] }),
}, thresholds({ steps: [null], abort: false }));

export function setup() { return loginAll(2 * pairs); }
export default playPair;
