// Each pair plays three games: two in one room (the second is the rematch), then one in a fresh room.
// Usage: k6 run loadtest/scenarios/smoke.js          (env: see lib/config.js; PAIRS, default 1, starts that many pairs at once)
import { cfg, hostsOption } from '../lib/config.js';
import { loginAll } from '../lib/player.js';
import { getPair, pairSession } from '../lib/pair.js';

export const options = {
  hosts: hostsOption(),
  setupTimeout: '10m',
  scenarios: {
    smoke: { executor: 'per-vu-iterations', vus: cfg.pairs, iterations: 1, maxDuration: '3m' },
  },
  thresholds: {
    tb_errors: ['count==0'],
    tb_games_completed: [`count>=${3 * cfg.pairs}`],
    'tb_game_start{cold:true}': ['max>0'], // the pair's first start (listed only if it was sampled)
    'tb_game_start{cold:false}': ['max>0'], // the rematch and the fresh room
  },
  summaryTrendStats: ['avg', 'p(50)', 'p(95)', 'p(99)', 'max', 'count'],
};

export function setup() { return loginAll(2 * cfg.pairs); }

export default async function (data) {
  const pair = getPair(data);
  await pairSession(pair, { games: 2 });
  await pairSession(pair, { games: 1 });
}
