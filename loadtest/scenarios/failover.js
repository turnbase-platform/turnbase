// Redundancy: a hold at LOAD_PAIRS (50% of the scaled ceiling) while failover-driver.sh, started by run.sh, kills one
// Platform pod (SIGKILL), recovers, kills one Game Host pod (SIGKILL), recovers, then deletes one of each gracefully
// (load-testing-phase-b.md §6). Usage: bash loadtest/run.sh start failover LOAD_PAIRS=<n> [WATCHED_PAIRS=8 ...]
// The players are scale-in.js's: LOAD_PAIRS plain pairs hold the load and WATCHED_PAIRS recovering pairs are the
// measurement (they reconnect, re-sync and carry on; a started game that never finishes is `tb_si_games_lost`, and
// the threshold is zero). run.sh defaults the length to DURATION_S=1500, LOAD_HOLD_S=1440.
import { required } from '../lib/shape.js';

required('LOAD_PAIRS');
export { options, setup, load, watched } from './scale-in.js';
