# Rate Limiting

Distributed rate limiting via **Bucket4j** backed by **Redis**. All limits are enforced server-side via a `HandlerInterceptor` applied per endpoint group. Redis ensures limits apply consistently across all monolith replicas.

## Tier 1 — Auth Endpoints (IP-based, strict)

Applies to: login, registration, password change, auth method addition/removal.

Implements `user-accounts.md NFR-SEC-003` exactly:

- After 5 failed attempts from the same IP → 30-second lockout
- Each subsequent failed attempt doubles the lockout duration
- Only failed attempts increment the counter; successful operations do not affect it

Redis key: `rate:auth:{ip}`

On lockout, response is 429 with:

```
Retry-After: 30
```

## Tier 2 — General API (per-user)

Applies to: all authenticated endpoints not covered by Tier 1.

- 100 requests per 10-second sliding window
- Redis key: `rate:api:{userId}`

Response headers on every request in this tier:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 73
X-RateLimit-Reset: 1749643200
```

On limit exceeded:

```
HTTP 429 Too Many Requests
Retry-After: 4
```

## Tier 3 — Upload Sub-bucket (per-user, per-hour)

Applies to: `POST /api/games/{gameId}/versions` (Step 1 of the pre-signed upload flow — see [file-uploads.md](file-uploads.md)).

- 10 version uploads per user per rolling hour
- Enforced independently from the general Tier 2 bucket — a burst of uploads does not exhaust the general API budget
- Redis key: `rate:upload:{userId}`

## Tier 4 — Unauthenticated Endpoints (IP-based, lenient)

Applies to: game catalog, game detail pages, public user profiles — endpoints that require no session token (`user-accounts.md NFR-SEC-006`).

- 200 requests per minute per IP
- Covers normal browsing patterns; blocks scrapers and abusive crawlers
- Redis key: `rate:public:{ip}`

## 429 Response Shape

All rate limit rejections return a Problem Detail response (see [error-handling.md](error-handling.md)):

```json
{
  "type": "https://turnbase.io/errors/rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Too many requests. Please wait before retrying.",
  "instance": "/api/auth/login"
}
```

The `Retry-After` header is always present on 429 responses and indicates the minimum seconds to wait before retrying.
