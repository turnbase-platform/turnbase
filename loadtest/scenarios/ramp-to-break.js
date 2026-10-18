// Stepped pairs, +STEP_PAIRS per step, until a step's thresholds cross (abortOnFail): finds the ceiling.
// Usage: k6 run loadtest/scenarios/ramp-to-break.js
// Env: START_PAIRS (10), STEP_PAIRS (10), MAX_PAIRS (1000), STEP_SECONDS (120), SETTLE_SECONDS (20),
//      THRESHOLD_SCALE (1). A crossed threshold ends the run with exit code 99.
import { stepper, thresholds } from '../lib/metrics.js';
import { cfg } from '../lib/config.js';
import { envNum, levelStages, levelSegments, baseOptions, vuScenario, playPair, loginAll } from '../lib/shape.js';

const start = envNum('START_PAIRS', 10);
const inc = envNum('STEP_PAIRS', 10);
const max = envNum('MAX_PAIRS', 1000);
const levels = [];
for (let p = start; p <= max; p += inc) levels.push(p);
stepper.configure(levelSegments(levels), cfg.settleSeconds);

export const options = baseOptions(
  { 'ramp-to-break': vuScenario('ramping-vus', { startVUs: 0, stages: levelStages(levels) }) },
  thresholds({ steps: levels.map(String), abort: true }));

export function setup() { return loginAll(2 * levels[levels.length - 1]); }
export default playPair;
