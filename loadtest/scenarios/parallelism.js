// Closed-loop pairs at think time 0, stepped 1, 2, 4, ... pairs: does the shared Espresso context parallelise?
// Usage: k6 run loadtest/scenarios/parallelism.js
// Env: LEVELS (1,2,4,8,16,32,64,128,256), STEP_SECONDS (120), SETTLE_SECONDS (20); see lib/config.js.
// The thresholds exist to create the per-step sub-metrics; none of them aborts.
import { stepper, thresholds } from '../lib/metrics.js';
import { cfg } from '../lib/config.js';
import { envList, levelStages, levelSegments, baseOptions, vuScenario, playPair, loginAll } from '../lib/shape.js';

const levels = envList('LEVELS', '1,2,4,8,16,32,64,128,256');
const maxPairs = Math.max(...levels);
stepper.configure(levelSegments(levels), cfg.settleSeconds);

export const options = baseOptions(
  { parallelism: vuScenario('ramping-vus', { startVUs: 0, stages: levelStages(levels) }) },
  thresholds({ steps: levels.map(String), abort: false }));

export function setup() { return loginAll(2 * maxPairs); }
export default playPair;
