// The spike: LOW (10%) of the scaled ceiling, a step to 100% within 30 s, a hold, a drop back to LOW and a tail at LOW
// (load-testing-phase-b.md §6): how fast scale-out reacts and how much of the spike the thresholds absorb.
// Usage: k6 run -e CEILING=<pairs> loadtest/scenarios/spike.js
// Env: CEILING (required: the ramp-to-break ceiling in pairs), LOW_FRACTION (0.1), LOW_MINUTES (5), HOLD_MINUTES (10),
//      TAIL_MINUTES (5), STEP_UP_SECONDS (30). Phases are tagged step:base|spike|tail; the 30 s step-up is step:rise.
//      No threshold aborts: the interesting part is what fails while the replicas are still starting.
import { stepper, thresholds } from '../lib/metrics.js';
import { envNum, ceilingPairs, rampStages, baseOptions, vuScenario, playPair, loginAll } from '../lib/shape.js';

const peak = ceilingPairs(1);
const low = ceilingPairs(envNum('LOW_FRACTION', 0.1));
const lowMin = envNum('LOW_MINUTES', 5);
const holdMin = envNum('HOLD_MINUTES', 10);
const tailMin = envNum('TAIL_MINUTES', 5);
const rise = envNum('STEP_UP_SECONDS', 30);
stepper.configure([{ tag: 'base', seconds: lowMin * 60 }, { tag: 'rise', seconds: rise }, { tag: 'spike', seconds: holdMin * 60 },
  { tag: 'drop', seconds: 10 }, { tag: 'tail', seconds: tailMin * 60 }], 0);

export const options = baseOptions({
  spike: vuScenario('ramping-vus', { startVUs: low, stages: [
    ...rampStages([[lowMin, low]]), { target: peak, duration: rise + 's' }, ...rampStages([[holdMin, peak]]),
    { target: low, duration: '10s' }, ...rampStages([[tailMin, low]]),
  ] }),
}, thresholds({ steps: ['base', 'spike', 'tail'], abort: false }));

export function setup() { return loginAll(2 * peak); }
export default playPair;
