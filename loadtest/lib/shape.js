// Shared scenario plumbing: environment parsing, stage lists and the options every scenario repeats.
import { cfg, hostsOption, dnsOption } from './config.js';
import { loginAll } from './player.js';
import { getPair, pairSession } from './pair.js';

const raw = (k, d) => (__ENV[k] !== undefined && __ENV[k] !== '' ? __ENV[k] : d);
export const envNum = (k, d) => Number(raw(k, d));
export const envList = (k, d) => String(raw(k, d)).split(',').map((x) => Number(x.trim())).filter((x) => !Number.isNaN(x));
export function required(k) {
  if (!raw(k, '')) throw new Error(k + ' is required (pairs): `soak` and `up-down` take it from the ramp-to-break ceiling');
  return envNum(k, 0);
}

// Phase B scenarios are ceiling-relative (load-testing-phase-b.md §6): CEILING is the ramp-to-break ceiling in pairs
// measured in the same run series, and `fraction` of it is the load. At least one pair.
export function ceilingPairs(fraction) {
  return Math.max(1, Math.round(required('CEILING') * fraction));
}

// Stages from [[minutes, target pairs], ...]: a ramp to each target over the given minutes.
export const rampStages = (list) => list.map(([minutes, target]) => ({ target, duration: Math.round(minutes * 60) + 's' }));

// The ramp that opens a step: a quarter of it, at most 10 s.
export const rampSeconds = () => Math.min(10, Math.floor(cfg.stepSeconds / 4));

// [{target, duration}] ramp to each level, then hold it for the rest of the step.
export function levelStages(levels) {
  const ramp = rampSeconds();
  return levels.flatMap((p) => [{ target: p, duration: ramp + 's' }, { target: p, duration: (cfg.stepSeconds - ramp) + 's' }]);
}
export const levelSegments = (levels) => levels.map((p) => ({ tag: String(p), seconds: cfg.stepSeconds }));

export function baseOptions(scenarios, thresholds) {
  return { hosts: hostsOption(), dns: dnsOption, setupTimeout: '10m', scenarios, thresholds,
    summaryTrendStats: ['avg', 'p(50)', 'p(95)', 'p(99)', 'max', 'count'] };
}

export const vuScenario = (executor, extra) => Object.assign({ executor, gracefulRampDown: '30s', gracefulStop: '60s' }, extra);

export async function playPair(data) {
  await pairSession(getPair(data), { games: cfg.freshRoomEvery });
}

export { loginAll };
