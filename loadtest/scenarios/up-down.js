// Ramp up, hold, ramp to zero, hold at zero: checks that resources are released afterwards.
// Usage: k6 run -e PAIRS=<n> loadtest/scenarios/up-down.js
// Env: PAIRS (required), RAMP_MINUTES (5), HOLD_MINUTES (5), IDLE_MINUTES (5, the zero-load hold).
// The phases are tagged step:up|hold|down|idle; there is no settle window and no threshold aborts.
import { sleep } from 'k6';
import { stepper, thresholds } from '../lib/metrics.js';
import { envNum, required, baseOptions, vuScenario, playPair, loginAll } from '../lib/shape.js';

const pairs = required('PAIRS');
const ramp = envNum('RAMP_MINUTES', 5) * 60;
const hold = envNum('HOLD_MINUTES', 5) * 60;
const idle = envNum('IDLE_MINUTES', envNum('HOLD_MINUTES', 5)) * 60;
stepper.configure([{ tag: 'up', seconds: ramp }, { tag: 'hold', seconds: hold }, { tag: 'down', seconds: ramp },
  { tag: 'idle', seconds: idle }], 0, undefined, undefined, 2 * ramp + hold);

// k6 drops a trailing zero-VU stage, so the hold at zero is a second scenario: one VU that sleeps and sends nothing.
const loaded = 2 * ramp + hold;
export const options = baseOptions({
  'up-down': vuScenario('ramping-vus', { startVUs: 0, stages: [
    { target: pairs, duration: ramp + 's' }, { target: pairs, duration: hold + 's' }, { target: 0, duration: ramp + 's' },
  ] }),
  idle: { executor: 'per-vu-iterations', vus: 1, iterations: 1, startTime: loaded + 's', maxDuration: (idle + 60) + 's', exec: 'idleHold' },
}, thresholds({ steps: [null], abort: false }));

export function setup() { return loginAll(2 * pairs); }
export function idleHold() { sleep(idle); }
export default playPair;
