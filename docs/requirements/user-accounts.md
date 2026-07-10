# User Accounts & Authentication Requirements

## Related API Specifications

- [rest-conventions.md](../specs/api-design/rest-conventions.md) — HTTP methods, status codes, authentication via httpOnly cookie
- [error-handling.md](../specs/api-design/error-handling.md) — RFC 9457 Problem Details, validation error format
- [rate-limiting.md](../specs/api-design/rate-limiting.md) — Tier 1 auth endpoint rate limiting (implements NFR-SEC-003)
- [decisions/0004-account-erasure-pseudonymization.md](../decisions/0004-account-erasure-pseudonymization.md) — ADR-0004: account deletion pseudonymizes game history (FR-ACCT-005)

## Stakeholders
| Role | Description |
|------|-------------|
| Guest User | Authenticated limited account created via "Play as Guest"; accesses the platform with a 24-hour non-renewable session token; can view profiles and participate in games; no social features, statistics, or persistent identity |
| Registered User | Authenticated platform member; full access to games, social features, account settings, and personal profile |
| Platform (System) | Enforces authentication, authorization, rate limiting, and data integrity |

---

## Functional Requirements

### Registration

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-AUTH-001 | Credential registration | The system must allow a user to register with a unique username, unique email address, password, and password confirmation. No other personal information is required. | Must |
| FR-AUTH-002 | Email format validation | The system must validate that the submitted email address contains exactly one `@` character, with a non-empty local part before it and a domain containing at least one `.` after it. Validation is applied server-side using standard framework facilities (e.g. Bean Validation `@Email` on the backend, React form validation on the frontend). No verification email is sent. | Must |
| FR-AUTH-003 | Username uniqueness | Usernames must be unique across all active and soft-deleted accounts at the time of registration or update. | Must |
| FR-AUTH-004 | Email uniqueness | Email addresses must be unique across all active accounts at the time of registration or update. | Must |
| FR-AUTH-005 | Password minimum length | Passwords must be at least 8 characters. No other character composition restrictions apply. | Must |
| FR-AUTH-013 | Reserved username prefix | Usernames submitted during registration or update must not begin with the prefix `guest-`. This prefix is reserved for system-generated guest accounts. | Must |

### Authentication

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-AUTH-006 | Credential login | The system must allow a registered user to log in using either their username or email address combined with their password. | Must |
| FR-AUTH-007 | OAuth registration | The system must allow a user to register and log in via Google OAuth 2.0. On first OAuth login, the user must provide a username. | Must |
| FR-AUTH-008 | OAuth email immutability | Email addresses associated with a Google OAuth account cannot be modified by the user. | Must |
| FR-AUTH-009 | Linked auth methods | A user may link multiple authentication methods (credential-based and/or OAuth providers) to a single account. Either method can be used to log in. | Should |
| FR-AUTH-010 | Auth method addition | A user must be able to add an additional authentication method to their existing account from their account settings. | Should |
| FR-AUTH-011 | Minimum auth method | A user must always have at least one active authentication method. The system must prevent removal of an auth method if it is the only one linked to the account. | Must |
| FR-AUTH-012 | OAuth credential email independence | Adding a credential-based auth method to a Google OAuth account does not grant the ability to modify the email address. The email remains bound to the OAuth provider and is not editable. | Must |

### Session Management

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-SESS-001 | Session token issuance | On successful login, the system issues a session token valid for a platform-configurable duration from the time of issuance; the default is 24 hours. Token lifetime does not extend based on activity. | Must |
| FR-SESS-002 | Single active session | Only one active session is permitted per account at any time. | Must |
| FR-SESS-003 | New login displaces old session | When a user authenticates from a new device while an existing session is active, the existing session is immediately invalidated. | Must |
| FR-SESS-004 | Displaced session feedback | A request made with an invalidated session token must receive a clear error response indicating the session was terminated due to a login from another device. | Must |

### Account Management

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-ACCT-001 | UUID identity | Every user account is assigned a UUID as its internal identifier. This UUID persists independently of username, email, or authentication method. | Must |
| FR-ACCT-002 | Username update | A user may update their username at most once per rolling 30-day window. The new username must be unique at time of update. | Must |
| FR-ACCT-003 | Email update | A user may update their email address at most once per rolling 30-day window. Not available for accounts whose email originates from an OAuth provider. The new email must be unique at time of update. | Must |
| FR-ACCT-004 | Account deletion | A user may permanently delete their account from their profile settings. Deletion is irreversible. | Must |
| FR-ACCT-005 | Deletion — data purge | On account deletion, the following are removed: the user's statistics, the user's uploaded games (see FR-ACCT-007), and the user's entries in all friends' friend lists. The user's **game history is pseudonymized, not removed** — retained with the person's identity replaced by a non-reversible token and PII stripped (see `game-history.md` FR-HIST-030, ADR-0004). The account's UUID is retired and not reused. The email address is released and becomes available for re-registration. | Must |
| FR-ACCT-006 | Deletion — username reservation | On account deletion, the username is soft-deleted: it is permanently reserved and cannot be registered or claimed by any new or existing user. | Must |
| FR-ACCT-007 | Deletion — uploaded games | Games uploaded by a deleted user are archived immediately and made invisible to the public. Archived games are permanently deleted once no active game sessions reference them. | Must |
| FR-ACCT-008 | Deletion — statistics impact | Removal of a deleted user's personal statistics does not affect per-game session counters. Session counters are denormalized and are never decremented. See per-game-statistics.md FR-STATS-004. | Must |
| FR-ACCT-009 | Deleted profile page | Accessing the profile of a deleted (soft-deleted) user displays the reserved username and a message stating the account no longer exists. No other information is shown. | Must |

### User Profile

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-PROF-001 | Registered user profile | Every registered user has a profile that contains: game history, statistics, friend list, uploaded games, and privacy settings. | Must |
| FR-PROF-002 | Guest profile display | Guest user profiles display only the username. All other profile fields (game history, statistics, friend list, uploaded games) are not applicable and are not shown. | Must |
| FR-PROF-003 | Profile visibility — public | A public profile is visible to all visitors, including unauthenticated users, and displays: username, and any sections not hidden via per-section visibility settings (FR-PROF-006). | Must |
| FR-PROF-004 | Profile privacy setting | A registered user may set their profile to private at any time. | Must |
| FR-PROF-005 | Private profile display | A private profile displays only the username and a message stating the profile is private. All other profile content is hidden from other users, regardless of per-section visibility settings. | Must |
| FR-PROF-006 | Per-section visibility | A registered user with a public profile may independently hide any of the following sections from visitors: game history, statistics, friends list, uploaded games. Hidden sections are not shown to any user other than the profile owner. All sections are visible by default when a profile is set to public. Per-section settings are ignored when the profile is private. | Must |
| FR-PROF-007 | Owner always sees own profile | A user always sees all sections of their own profile regardless of privacy setting or per-section visibility configuration. | Must |
| FR-PROF-008 | Block incoming friend requests | A registered user may enable a setting on their profile that prevents other users from sending them friend requests. When enabled, the Send Request action is hidden on their profile and in username search results, and API attempts are rejected. Existing friendships and already-pending requests are unaffected when the setting is enabled. See social-friends.md FR-SOC-021. | Must |

### Guest Accounts

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-GUEST-001 | Guest account creation | The system must provide a "Play as Guest" action. Clicking it creates a guest account with an auto-generated username of the form `guest-<N>`, where N is a DB serial value auto-incrementing from 0. | Must |
| FR-GUEST-002 | Guest serial uniqueness | Guest serial values are unique. Two guest accounts cannot share the same serial or the same generated username. | Must |
| FR-GUEST-003 | Guest token issuance | On guest account creation, the system issues a session token identical in form to a standard login token. The token lifetime is the same platform-configurable value as for registered users (FR-SESS-001). The token cannot be renewed; once it expires, the guest account is inaccessible and considered abandoned. | Must |
| FR-GUEST-004 | No guest auth methods | Guest accounts have no authentication methods. There is no login flow for a guest account; the only means of access is the token issued at creation. | Must |
| FR-GUEST-005 | Guest account cleanup | A scheduled job permanently deletes guest accounts whose token has expired (i.e. accounts older than the configured guest token lifetime from FR-GUEST-003). The cleanup job runs on a configurable interval; the default is every 1 hour. | Must |
| FR-GUEST-006 | Guest permissions — allowed | Guest users may view user profiles and join or create game sessions. | Must |
| FR-GUEST-007 | Guest permissions — social | Guest users cannot add or have friends. Friend-related features are not displayed or accessible to guest users. | Must |
| FR-GUEST-008 | Guest permissions — games | Guest users cannot upload or manage games. | Must |
| FR-GUEST-009 | Guest permissions — statistics | Guest users do not accumulate personal statistics. Their completed sessions count toward per-game session totals but are not attributed to any user profile. | Must |
| FR-GUEST-010 | Guest profile display | A guest user's profile page displays only the username. No other profile content is shown, regardless of who is viewing it. | Must |

---

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-SEC-001 | Security | Passwords must be hashed using Argon2 (or equivalent strong adaptive hashing algorithm) with a unique random salt per user. Plaintext passwords must never be stored or logged. | 100% of stored passwords | Must |
| NFR-SEC-002 | Security | All client-server communication must be encrypted in transit. | TLS 1.2+ on all endpoints | Must |
| NFR-SEC-003 | Security | All auth-related endpoints (login, registration, password change, auth method addition/removal) must enforce IP-based rate limiting. After 5 failed attempts from the same IP, the IP is locked out. The initial lockout duration is 30 seconds. Each subsequent failed attempt doubles the lockout duration. Only failed attempts increment the counter; successful operations do not affect it. | 5 failures → 30s lockout; each additional failure doubles duration | Must |
| NFR-SEC-005 | Security | Server-side validation must be applied to all inputs regardless of client-side validation. | 100% of inputs | Must |
| NFR-SEC-006 | Security | All platform endpoints must require a valid session token, except: the landing page, the login endpoint, the registration endpoint, user profile pages, the game catalog, game detail pages (including the per-game statistics tab). Unauthenticated requests to any other endpoint must receive a 401 response. | 100% of non-exempt endpoints | Must |

---

## Constraints

| ID | Description |
|----|-------------|
| CON-001 | Backend must be implemented in Java 21 with Spring Boot 3.5+. |
| CON-002 | Email sending infrastructure is not available in the current phase. No emails are sent for any reason (verification, password reset, notifications). |
| CON-003 | Password reset is not supported until email infrastructure is in place. |
| CON-004 | Session tokens are stored client-side as httpOnly, Secure, SameSite=Strict cookies. Tokens are never stored in localStorage or accessible to JavaScript. SameSite=Strict prevents the cookie from being sent on cross-site requests, providing CSRF protection without a separate CSRF token. |

---

## Out of Scope

- Email verification flow
- Password reset / account recovery
- Terms & Conditions acceptance tracking
- Account suspension or administrative banning
- User-provided personal information (real name, phone number, avatar, etc.)
- Multi-factor authentication (beyond linked OAuth)

---

