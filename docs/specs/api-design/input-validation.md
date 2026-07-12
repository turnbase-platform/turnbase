# Input Validation and Output Encoding

Cross-cutting conventions for every string, number and object the platform accepts from a client, and
for how user-generated content is rendered back.

**Realizes:** `user-accounts.md` NFR-SEC-005 (server-side validation), FR-AUTH-002/003/005/013;
`in-room-chat.md` FR-MSG-002; `game-rooms.md` FR-HOST-007 / CON-005. **Closes review blocker API-6**
(and core-requirements CORE-6/21 — username constraints).

## Principles

1. **The client's validation is UX; the server's is the contract.** Every rule here is enforced
   server-side. Frontend validation exists to give fast feedback and is never relied upon.
2. **Canonicalize before you compare or store.** A uniqueness check on a non-canonical string is not a
   uniqueness check.
3. **Encode on render, not on store.** User content is stored as the user typed it (post-canonicalization)
   and escaped at the point of rendering. Storing pre-escaped HTML is how you get double-escaping bugs
   and a false sense of safety.
4. **Bound everything that a client controls the size of** — string lengths, body size, frame size,
   object depth. An unbounded field is an availability bug waiting for someone to notice it.

## The pipeline

Every inbound request or frame runs the same ordered gauntlet. Order matters: each step is cheaper
than the one after it, and none of them should ever run on input the previous step would have rejected.

```
1. Size          Reject oversized bodies/frames before allocating a parse buffer
2. Authorize     Channel-level fast-fail (WS) / authentication (HTTP)
3. Parse         Well-formed JSON, within StreamReadConstraints
4. Canonicalize  UTF-8 → NFC → forbidden-code-point rejection → trim
5. Validate      Type, length, charset, range, whitelist
6. Authorize     Handler-level authoritative re-check (WS) / ownership (HTTP)
7. Act
```

---

## Canonicalization

Applied to **every** user-supplied string, before any length check, comparison, or persistence.

1. Reject input that is not well-formed UTF-8.
2. Normalize to **NFC** (`java.text.Normalizer.Form.NFC`).
3. Reject forbidden code points (below).
4. Trim leading and trailing whitespace.
5. **Length is measured after NFC, in Unicode code points** — never in UTF-16 `char` units, or `é`
   costs one character and `👋` costs two.

### Forbidden code points — everywhere, in every field

| Range / category | Why |
|---|---|
| C0 controls `U+0000`–`U+001F` | Log injection, protocol confusion, null-byte truncation |
| `U+007F` and C1 controls `U+0080`–`U+009F` | Same |
| Bidi controls `U+202A`–`U+202E`, `U+2066`–`U+2069` | **Rendering spoofing.** An RLO in a username or chat line reverses the visual order of everything after it — this is the Trojan Source class of attack, and it works on any UI that renders the string faithfully |
| Surrogates (`Cs`), private-use (`Co`), unassigned (`Cn`) | Not meaningful text; a source of encoder/decoder mismatches |

Fields that explicitly permit newlines (long-form game descriptions) allow `U+000A` only, and no other
C0 character. No field permits `\r` or `\t`.

---

## Field catalogue

| Field | Length (code points) | Charset / rule | Uniqueness |
|---|---|---|---|
| `username` | 3–32 | Letters (`L*`), combining marks (`M*`), decimal digits (`Nd`), and ASCII `_` `-`. Must begin with a letter or digit. **No** format characters (`Cf`, incl. ZWJ/ZWNJ), **no** spaces, **no** symbols or emoji, **no** punctuation beyond `_` `-`. Plus the script restriction below. | On the **skeleton** — see below |
| `password` | 8–128 | Any code point except the forbidden set. No composition rules (FR-AUTH-005). | — |
| `email` | ≤ 254 (local part ≤ 64) | **ASCII only.** FR-AUTH-002's rule: exactly one `@`, non-empty local part, domain containing at least one `.` | On the lowercased form |
| chat `text` | 1–500 | No control characters at all — the chat input is single-line (FR-MSG-002) | — |
| `correlationId` | — | Canonical UUID string. Rejected otherwise: it is echoed into error payloads, so it is not a free-text field | — |
| game action `payload` | ≤ 256 KB | **Opaque.** Well-formed JSON within `StreamReadConstraints`; never inspected (game state is opaque to the platform) | — |
| `parameters` | ≤ 4 KB serialized | Whitelisted against the game manifest — see below | — |
| game metadata (name, description, …) | per manifest | Bounded and validated by [manifest-schema.md](../manifest/manifest-schema.md); not re-specified here | — |

### Usernames: the confusable problem

Usernames are Unicode, so `аlice` (Cyrillic а) and `alice` (Latin a) are different strings that render
identically. Impersonation on a social platform is the whole game, so a plain `UNIQUE` index on the raw
string is not sufficient. Three mechanisms, all provided by **ICU4J `com.ibm.icu.text.SpoofChecker`**:

1. **Mixed-script restriction.** Usernames must pass `SpoofChecker` at restriction level
   **`MODERATELY_RESTRICTIVE`**: a single script plus `Common`/`Inherited`, with the standard
   multi-script allowances (Latin + Han + Hiragana/Katakana; Latin + Han + Hangul; Latin + Han +
   Bopomofo). This rejects the Latin+Cyrillic and Latin+Greek mixes where essentially all homoglyph
   attacks live, while leaving genuine non-Latin names entirely usable.

2. **Skeleton uniqueness.** The canonical uniqueness key is
   `SpoofChecker.getSkeleton(caseFold(NFC(username)))`, persisted in an indexed `username_skeleton`
   column with a `UNIQUE` constraint (covering active **and** soft-deleted accounts, per FR-AUTH-003).
   The display form is stored separately and preserved exactly as typed.

3. **Reserved-prefix check on the skeleton.** FR-AUTH-013 reserves the `guest-` prefix. That check runs
   against the **skeleton**, not the raw input — otherwise `guеst-1` (Cyrillic е) or a Unicode-hyphen
   variant sails past a naive `startsWith` and impersonates a system account.

**Accepted consequence:** skeletons collide aggressively. `Alice`, `ALICE`, `A1ice` and `Аlice` all map
to one key, so the second registration of any of them is refused. That is the mechanism working as
designed, and it is why the charset also excludes emoji and symbols (which carry their own confusable
and ZWJ-sequence problems for no real benefit in an identifier).

Both a plain duplicate and a confusable collision return the **same** 409 `conflict` — "Username
already taken". Distinguishing them would leak that a *visually similar* account exists, which is a
strictly worse enumeration oracle than the one already accepted (api-design review gap 13).

### Passwords: the silent-truncation trap

The 128-character cap bounds hashing cost, but the cap that actually matters is a different one:
**BCrypt silently truncates its input at 72 bytes.** A 128-code-point Unicode password can easily
exceed 72 *bytes*, at which point two different passwords hash to the same value and the extra entropy
the user thought they were adding is discarded without a word.

The platform therefore uses **Argon2id** (`Argon2PasswordEncoder`), which has no such limit. If BCrypt
is ever used instead, the password must be SHA-256 pre-hashed before it reaches the encoder.

---

## Size limits

| Surface | Limit | On breach |
|---|---|---|
| HTTP JSON request body | **64 KB** | `413 Payload Too Large` |
| JSON parse depth / string / number | `StreamReadConstraints`: max nesting **100**, max string length **256 KB**, max number length **1 000** | `400 validation-failed` |
| STOMP frame — `/app/game.*.action` | 256 KB (`setMessageSizeLimit`) | `ERROR` `ACTION_TOO_LARGE` |
| STOMP frame — `/app/room.*.member`, `/app/room.*.host` | 8 KB | `ERROR` `MESSAGE_TOO_LARGE` |
| STOMP frame — `/app/room.*.chat` | 4 KB | `ERROR` `MESSAGE_TOO_LARGE` |
| STOMP frame — `/app/game.*.sync` | 1 KB | `ERROR` `MESSAGE_TOO_LARGE` |

A 64 KB body cap is safe for *every* REST endpoint because **no endpoint ever receives a file**: game
bundles are uploaded via pre-signed URLs directly to object storage
([file-uploads.md](file-uploads.md)), so the largest legitimate body the API sees is a JSON DTO.

The per-destination STOMP caps are enforced in the same `ChannelInterceptor` as the Tier 6 rate limits
([rate-limiting.md](rate-limiting.md)) — the frame's byte length is known from the headers, before the
payload is deserialized. `setMessageSizeLimit` is a single channel-wide ceiling, so the tighter
per-destination caps have to live here; without them the 256 KB the action destination legitimately
needs would also be available to a chat flood.

`StreamReadConstraints` (Jackson 2.15+) is what stops a 60 KB body of nothing but `[[[[[[…]]]]]]` from
exhausting the parser's stack — a size cap alone does not.

---

## `CHANGE_PARAMETERS` is a whitelist, not a size cap

The review flagged `parameters: object` as "unbounded, broadcast verbatim to every subscriber — an
amplification and memory vector". It is, as written. But the fix is not a size cap, because **the game
manifest already declares the parameter schema** ([manifest-schema.md](../manifest/manifest-schema.md)
§ `parameters`): every parameter has a `key`, a `type` (`integer` / `decimal` / `boolean` / `string` /
`enum`), a `default`, and its type's bounds (`min`/`max`, `maxLength`, `options`).

So `CHANGE_PARAMETERS` is validated against the manifest of the game version pinned to the room:

| Rule | Error code |
|---|---|
| Every key must be declared in the manifest's `parameters` array | `UNKNOWN_PARAMETER` |
| Value must match the declared `type` | `PARAMETER_TYPE_MISMATCH` |
| `integer` / `decimal` within `[min, max]` | `PARAMETER_OUT_OF_RANGE` |
| `string` within `maxLength`, and canonicalized like any other string | `PARAMETER_OUT_OF_RANGE` |
| `enum` value ∈ `options` | `PARAMETER_OUT_OF_RANGE` |

Errors go to `/user/queue/errors` in the standard envelope, with `details` naming the offending keys.
Keys absent from the command retain their current value; the full set is still broadcast in
`PARAMETERS_CHANGED` (`room-websocket.md`), unchanged.

The 4 KB serialized cap remains as a pre-parse backstop, but it is no longer what makes this safe. The
broadcast object is now bounded by the manifest's own declared bounds — and those were themselves
validated at upload time (manifest-schema.md § Validation). **The amplification vector is gone by
construction rather than merely capped**, and a host can no longer push arbitrary attacker-chosen data
through the platform into every room member's client.

---

## Output encoding

**All user-generated strings are plain text.** Usernames, chat messages, game names — none of them are
markup, none are ever rendered as markup. React escapes by default; `dangerouslySetInnerHTML` is
**banned platform-wide**, enforced as `react/no-danger: error` in ESLint so CI fails on it rather than
a reviewer having to catch it (FR-CICD-001).

### The one exception: game log entries

`GAME_LOG` entries support basic Markdown (`game-contracts.md` FR-LOG-002) and are rendered by the
platform UI outside the iframe (FR-LOG-005). This is **the only surface where the platform renders
anything other than plain text** — and its content is composed by *game code*, which makes it the one
place "React escapes by default" does not save us.

The Markdown renderer must therefore run **locked down**:

- **Raw HTML passthrough disabled** (`html: false`) — no HTML blocks, no inline HTML.
- **Inline constructs allowlisted**: emphasis, strong, code span, and the GDK's colour annotation.
  Nothing else.
- **No links, no images, no autolinking** (`linkify: false`). A game must not be able to render a
  clickable URL into the platform's own UI.

**Accepted residual:** game code typically interpolates usernames into log entries (`**Alice** played
the Queen of Spades`). A username containing Markdown metacharacters can therefore corrupt the
*formatting* of a log line. With raw HTML disabled this is cosmetic — it cannot become markup or
script injection — and it is accepted. (Under ADR-0006 the MVP runs official games only, so the
composing code is first-party; the renderer restriction is what keeps this bounded when third-party
games arrive.)

### Response hygiene

- `X-Content-Type-Options: nosniff` on every response. JSON is never served as `text/html`.
- Game frontends receive platform data only via `postMessage`, from a separate registrable domain
  ([game-frontend/game-asset-serving.md](../game-frontend/game-asset-serving.md)). The platform never
  injects HTML into a game iframe, so there is no cross-boundary encoding surface at all.

---

## Rejection model

| Surface | Response |
|---|---|
| REST | `400` RFC 9457 `validation-failed` with the `errors` array ([error-handling.md](error-handling.md)) |
| REST — body too large | `413` |
| WebSocket | `ERROR` on `/user/queue/errors`, code `VALIDATION_FAILED`, echoing `correlationId`, with `details` naming the failed fields |

Validation errors name the **field and the rule**, never the rejected value. Reflecting attacker input
back through an error path is how a validation message becomes a log-injection or content-reflection
vector, and the client already knows what it sent.

---

## Requirements traceability

| Requirement / gap | Realized by |
|---|---|
| NFR-SEC-005 (server-side validation) | [The pipeline](#the-pipeline) — every rule is server-enforced |
| FR-AUTH-002 (email format) | [Field catalogue](#field-catalogue) |
| FR-AUTH-003 (username uniqueness) | Skeleton uniqueness index |
| FR-AUTH-005 (password minimum) | Field catalogue + Argon2id |
| FR-AUTH-013 (reserved `guest-` prefix) | Prefix check on the **skeleton** |
| FR-MSG-002 (chat 500 chars) | Field catalogue, measured in code points after NFC |
| FR-HOST-007 / CON-005 (configurable parameters) | [`CHANGE_PARAMETERS` whitelist](#change_parameters-is-a-whitelist-not-a-size-cap) |
| FR-LOG-002 / FR-LOG-005 (game log Markdown) | [Output encoding](#the-one-exception-game-log-entries) |
| **API-6** — no input-validation/output-encoding conventions | This document |
| CORE-6 / CORE-21 — username constraints unspecified | Field catalogue + confusable rules |

---

## Open questions

- **OQ-001 — No emoji or symbols in usernames.** Excluded because they bring their own confusable and
  ZWJ-sequence problems into an identifier that must be unambiguous. If users push back, the clean fix
  is a separate free-form **display name** alongside a strict `username`, which is a post-MVP model
  change rather than a loosening of these rules.
- **OQ-002 — ASCII-only email.** Rejects IDN/EAI addresses. Revisit if a real user is ever blocked;
  the cost of accepting them is a normalization contract with whatever mail system exists, and there
  is none in the MVP (no verification email is sent — FR-AUTH-002).
