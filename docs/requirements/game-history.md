# Game History Requirements

This document defines the requirements for recording and displaying a registered user's personal game history — the per-session record of every completed game a user participated in as a player.

## Related Documents

- `user-accounts.md` — profile structure, privacy model (amended alongside this spec)
- `per-game-statistics.md` — aggregate session counts (distinct from per-session history)
- `game-contracts.md` — defines the `game_over` structured outcome that drives history recording
- `game-catalog.md` — pagination model reused here (FR-CAT-004)
- `platform-views.md` — profile view and settings view (amended alongside this spec)
- `../decisions/0004-account-erasure-pseudonymization.md` — ADR-0004: account deletion pseudonymizes history

---

## Stakeholders

| Role | Description |
|------|-------------|
| Registered User | Accumulates game history; controls its visibility via privacy settings |
| Visitor (Unauth / Guest / Other Registered) | May view history on public profiles where not hidden |
| Guest User | Plays sessions but accrues no game history |
| Game Developer | Controls what per-session stats appear via the `game_over` stats maps |

---

## Definitions

| Term | Definition |
|------|------------|
| History Entry | A record linking one registered user to one completed game session, capturing outcome and stats |
| Structured Outcome | The `game_over` payload from the game BE consumed by the platform (see `game-contracts.md` FR-EFF-005) |
| Stats Map | The opaque key-value map in `playerResults` or `teamResults` within the structured outcome |
| Win Condition Label | The platform-derived human-readable outcome string shown on a history entry card |
| Game Name Snapshot | The game's title captured at session completion; retained even after soft-deletion |

---

## Functional Requirements

### Recording

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-HIST-001 | History trigger | A history entry is created for each registered player in a session only when the game BE emits a `game_over` effect. Sessions that end without a `game_over` — including platform-side failures, all-player disconnects, and room closure mid-game — do not produce history entries. | Must |
| FR-HIST-002 | One entry per player per session | Each registered player in the session receives an independent history entry derived from the structured outcome. Spectators do not receive history entries. | Must |
| FR-HIST-003 | Guest exclusion | Guest users do not accrue game history. No history entry is created for guest participants. | Must |
| FR-HIST-004 | Outcome source | The outcome recorded for each player is determined entirely by the structured outcome the game BE returns in the `game_over` effect. The platform does not override, infer, or supplement any outcome field. | Must |
| FR-HIST-005 | Stored fields | Each history entry must store: session ID, game ID, game name snapshot, session completed-at timestamp, the player's placement (1-based integer, derived from the player's team entry in `teamResults`), total team count in the session (equal to `teamResults` length), the draw flag, the player's stats map (from `playerResults`), and the player's team stats map (from `teamResults` for the player's team). | Must |
| FR-HIST-006 | Game name snapshot | The game's title is captured at the moment of session completion and stored as part of the history entry. This snapshot is used for display and search regardless of subsequent title changes or soft-deletion of the game. | Must |

### Win Condition Label

The platform derives a single human-readable label per entry from `placement`, `draw`, and `teamCount` (= `teamResults.length`). This label is the primary outcome indicator shown on history entry cards.

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-HIST-010 | Draw | When `draw=true`, the label is "Draw", regardless of placement. | Must |
| FR-HIST-011 | Victory | When `draw=false` and `placement=1`, the label is "Victory". | Must |
| FR-HIST-012 | Defeat | When `draw=false`, `placement > 1`, and `teamCount=2`, the label is "Defeat". | Must |
| FR-HIST-013 | Ordinal placement | When `draw=false`, `placement > 1`, and `teamCount > 2`, the label is the ordinal string for the placement (e.g. "2nd place", "3rd place", "4th place"). | Must |

### Profile History Tab

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-HIST-020 | Dedicated history tab | The registered user profile must include a dedicated "History" tab displaying the user's game history list. This tab is separate from the inline statistics section and the uploaded games tab. | Must |
| FR-HIST-021 | History entry card | Each entry in the history list is displayed as a card showing: the game name (linked to `/games/:id` if the game is not soft-deleted; plain text otherwise), the win condition label (FR-HIST-010 – FR-HIST-013), and the session completed-at date. | Must |
| FR-HIST-022 | Expanded entry detail | Selecting a history entry card expands it to reveal the game-defined stats. Stats from the player's `playerResults` stats map and the player's team's `teamResults` stats map are rendered as separate labeled key-value sections. If either map is empty or absent, that section is omitted. Selecting again collapses the card. | Must |
| FR-HIST-023 | Deleted game display | When a history entry references a soft-deleted game, the game name snapshot is displayed as plain text (no link). No other indication of deletion is required. | Must |
| FR-HIST-024 | Default sort | The history list is sorted by session completed-at timestamp, descending (most recent first), by default. | Must |
| FR-HIST-025 | Search | A search input filters the history list by matching the query against the stored game name snapshot. Matching is case-insensitive substring matching applied server-side. | Must |
| FR-HIST-026 | Pagination | The history list is paginated using the same model as the game catalog (FR-CAT-004 in `game-catalog.md`): configurable page size (default 25), with first / previous / next / last navigation controls and current page / total page count display. | Must |
| FR-HIST-027 | Empty state | When a user has no history entries (or no entries match the active search), the tab displays a placeholder message indicating no history is available. | Must |
| FR-HIST-028 | Owner always sees own history | A user always sees their own history tab when viewing their own profile, regardless of privacy settings. | Must |
| FR-HIST-029 | Visitor visibility | The history tab is visible to visitors only when the profile is public and the game history section is not hidden via per-section privacy settings (see FR-PROF-006 in `user-accounts.md`). | Must |

### Account Deletion & Data Lifecycle

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-HIST-030 | Account deletion — pseudonymization | On account deletion, the user's history entries are **retained, not deleted**: the entry's link to the person is replaced with a stable, non-reversible pseudonymous token and any PII (username, email, avatar / display name) is stripped, so the rows remain valid for session and per-game statistics integrity while no longer constituting personal data (GDPR pseudonymization — ADR-0004). This **supersedes the earlier hard-delete behavior**. Pseudonymized entries no longer surface on any profile, since the account itself is soft-deleted (`user-accounts.md` FR-ACCT-009). Detailed erasure mechanics (exact fields, timing, audit trail) are deferred to a future data-operations spec. | Must |

---

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-HIST-001 | Performance | History list query latency (paginated, with optional search filter) | p95 < 300ms | Must |
| NFR-HIST-002 | Scalability | History queries must be backed by database indexing on user ID, completed-at timestamp, and game name snapshot to remain performant as history volume grows. | — | Must |
| NFR-HIST-003 | Storage | History entries are retained for the lifetime of the user account and beyond: on account deletion they are **pseudonymized rather than removed** (retained with the person's identity replaced by a non-reversible token), consistent with FR-HIST-030 and FR-ACCT-005 in `user-accounts.md` (ADR-0004). | — | Must |

---

## Constraints

| ID | Description |
|----|-------------|
| CON-001 | History entries are only created from `game_over` structured outcomes; no other completion signal creates a history record. |
| CON-002 | History search and pagination are server-side; client-side filtering is not acceptable. |
| CON-003 | The platform does not interpret or validate the contents of stats maps beyond storing them as-is. |

---

## Out of Scope

- Aggregate win/loss/draw statistics derived from history (e.g. win rate per game) — future phase
- Cross-player history queries (e.g. "games played against this person")
- Sorting by any column other than completed-at timestamp
- Deleting or editing individual history entries by the user
- History for spectated sessions

---

## Open Questions

- **OQ-001 (resolved)** — The `game_over` structured outcome contract (`game-contracts.md` FR-OUTCOME-001 – FR-OUTCOME-004) is stable. The `teamResults` / `playerResults` / `draw` structure is consistent with the stored fields in FR-HIST-005; no revision is pending.
- **OQ-002** — Pagination component reuse: FR-HIST-026 reuses the catalog pagination model by specification. Whether this becomes a shared UI component or a shared API pagination pattern is an implementation decision.
