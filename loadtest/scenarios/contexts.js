// The same game under several game ids, so the Game Host holds several Espresso contexts (one per
// `{gameId}:{gameVersion}`). Pair i plays ids[i % ids.length]. Build the copies first: `loadtest/lib/bundles.sh`.
// Usage: k6 run -e CONTEXT_IDS=<id>,<id>,<id>,<id> loadtest/scenarios/contexts.js
// Env: CONTEXT_IDS (required, comma separated; each a playable game), PAIRS (50), DURATION (5m).
// The thresholds exist to create the sub-metrics; none of them aborts.
import exec from 'k6/execution';
import { thresholds } from '../lib/metrics.js';
import { cfg } from '../lib/config.js';
import { envNum, baseOptions, loginAll } from '../lib/shape.js';
import { getPair, pairSession } from '../lib/pair.js';

const ids = String(__ENV.CONTEXT_IDS || '').split(',').map((x) => x.trim()).filter(Boolean);
if (ids.length < 2) throw new Error('CONTEXT_IDS needs at least two game ids (comma separated); loadtest/lib/bundles.sh prints them');
const pairs = envNum('PAIRS', 50);

export const options = baseOptions(
  { contexts: { executor: 'constant-vus', vus: pairs, duration: __ENV.DURATION || '5m', gracefulStop: '60s' } },
  thresholds({ steps: [null] }));

export function setup() { return loginAll(2 * pairs); }

export default async function (data) {
  const pair = getPair(data);
  await pairSession(pair, { games: cfg.freshRoomEvery, gameId: ids[(exec.vu.idInTest - 1) % ids.length] });
}
