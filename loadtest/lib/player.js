// One user: HTTP half (login, request with cookie jar). The STOMP socket half is added by IMP-M15-08.
import http from 'k6/http';
import { cfg, userName } from './config.js';
import { m, ok, fail } from './metrics.js';

// 429 -> RATE_LIMIT_EXCEEDED, 5xx -> http_5xx, body.code, else http_<status>; status 0 is a network error.
export function errorCode(res) {
  if (res.status === 0) return 'network';
  try {
    const body = res.json();
    if (body && typeof body.code === 'string') return body.code;
  } catch (_) { /* not JSON */ }
  if (res.status === 429) return 'RATE_LIMIT_EXCEEDED';
  if (res.status >= 500) return 'http_5xx';
  return 'http_' + res.status;
}

export class Player {
  constructor(name, cookies) {
    this.name = name;
    this.jar = new http.CookieJar();
    for (const c of cookies || []) this.jar.set(cfg.baseUrl, c.name, c.value);
  }

  // `name` is a URL template (POST /api/rooms/{id}/participants), never the URL: flat metric cardinality.
  async request(method, path, body, name) {
    const headers = { Host: cfg.host };
    if (body !== undefined && body !== null) headers['Content-Type'] = 'application/json';
    const res = await http.asyncRequest(method, cfg.baseUrl + path,
      body === undefined || body === null ? null : JSON.stringify(body),
      { jar: this.jar, headers, tags: { name: name || method + ' ' + path } });
    return { res, ms: res.timings.duration };
  }

  cookieHeader() {
    const cookies = this.jar.cookiesForURL(cfg.baseUrl + '/');
    return Object.keys(cookies).map((k) => k + '=' + cookies[k][0]).join('; ');
  }

  async login() {
    const { res, ms } = await this.request('POST', '/api/auth/login',
      { usernameOrEmail: this.name, password: cfg.password }, 'POST /api/auth/login');
    if (res.status !== 200) { fail(errorCode(res)); return false; }
    m.login.add(ms);
    ok();
    return true;
  }
}

// setup(): logs in lt-00000.. in batches and returns the session cookies, so Argon2 stays out of the
// measured window. Scenarios set setupTimeout: '10m'.
export function loginAll(userCount) {
  const batchSize = Number(__ENV.LOGIN_PARALLEL || 8);
  const cookies = {};
  for (let start = 0; start < userCount; start += batchSize) {
    const names = [];
    for (let i = start; i < Math.min(start + batchSize, userCount); i++) names.push(userName(i));
    const reqs = names.map((name) => ['POST', cfg.baseUrl + '/api/auth/login',
      JSON.stringify({ usernameOrEmail: name, password: cfg.password }),
      { headers: { Host: cfg.host, 'Content-Type': 'application/json' }, tags: { name: 'POST /api/auth/login' } }]);
    const responses = http.batch(reqs);
    responses.forEach((res, idx) => {
      if (res.status !== 200) { fail(errorCode(res)); return; }
      m.login.add(res.timings.duration);
      cookies[names[idx]] = Object.keys(res.cookies).map((k) => ({ name: k, value: res.cookies[k][0].value }));
    });
  }
  return { cookies };
}
