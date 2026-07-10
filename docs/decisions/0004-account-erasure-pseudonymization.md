# ADR-0004: Account erasure via history pseudonymization

- **Status:** Accepted
- **Date:** 2026-07-10
- **Deciders:** Project owner
- **Source:** MVP Readiness Review 2026-07-02 — strategic decision #5

## Context

Game history is currently retained indefinitely with no deletion story. That is a gap before any
EU-reachable public launch: GDPR grants a right to erasure, but hard-deleting a user's history
rows would also destroy *opponents'* game records and corrupt aggregate/per-game statistics that
reference those sessions.

## Decision

On account deletion, **pseudonymize** the departing user's identity in retained,
integrity-bearing records (game history and equivalent):

- Replace direct PII — username, email, avatar, display name — with a **stable pseudonymous
  token** (e.g., "Deleted user").
- **Keep the rows** so opponents' histories and aggregate statistics remain intact and
  referentially valid.
- The pseudonym must not be reversible or re-linkable to the original identity.
- User-authored free text that may contain PII (e.g., chat messages) is **out of history scope**
  and handled under its own retention policy, not by this ADR.

This is the **requirements-level** answer. A detailed erasure / data-lifecycle spec (exact fields,
timing, verification, audit trail) is deferred to a data-operations spec.

## Consequences

- **Positive:** satisfies the erasure intent while preserving referential integrity and stats.
- **Negative / follow-ups:** requires a stable, non-reversible pseudonym scheme and an audit
  trail; every surface that renders a player's name from history must tolerate a pseudonymized /
  "deleted user" display.

## Affected documents

- `docs/requirements/game-history.md` — add an FR: account deletion pseudonymizes history rows.
- `docs/requirements/user-accounts.md` — account-deletion flow triggers history pseudonymization.
- Future **data-operations spec** — detailed erasure mechanics and audit.
- Review INDEX — resolves strategic #5.
