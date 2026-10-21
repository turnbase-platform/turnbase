// Creates the lt-* users (idempotent: log in, register if absent). Runs outside every measurement window.
// Usage: k6 run loadtest/scenarios/provision.js        (env: USERS, default 2000; see lib/config.js)
// Needs the `loadtest` profile (registration limiting off), otherwise it fails with RATE_LIMIT_EXCEEDED
// after 3 users: that is the profile not being active, not a script bug.
import exec from 'k6/execution';
import { cfg, userName, hostsOption, dnsOption } from '../lib/config.js';
import { provisionCreated, provisionExisting, fail } from '../lib/metrics.js';
import { Player, errorCode } from '../lib/player.js';

export const options = {
  hosts: hostsOption(),
  dns: dnsOption,
  scenarios: {
    provision: {
      executor: 'shared-iterations',
      vus: 8,
      iterations: Number(__ENV.USERS || 2000),
      maxDuration: '10m',
    },
  },
};

export default async function () {
  const name = userName(exec.scenario.iterationInTest);
  provisionCreated.add(0);
  provisionExisting.add(0);
  const p = new Player(name, []);
  const first = await p.request('POST', '/api/auth/login',
    { usernameOrEmail: name, password: cfg.password }, 'POST /api/auth/login');
  if (first.res.status === 200) { provisionExisting.add(1); return; }
  if (first.res.status !== 401 && first.res.status !== 404) { fail(errorCode(first.res)); return; }
  const reg = await p.request('POST', '/api/auth/register',
    { username: name, email: name + '@example.com', password: cfg.password, confirmPassword: cfg.password },
    'POST /api/auth/register');
  if (reg.res.status !== 201) { fail(errorCode(reg.res)); return; }
  provisionCreated.add(1);
  if (!(await p.login())) return;
}
