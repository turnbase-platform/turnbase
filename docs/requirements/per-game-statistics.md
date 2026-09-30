# Per-Game Statistics Requirements

## Related API Specifications

- [statistics-rest-api.md](../specs/api-design/statistics-rest-api.md) — `completedSessionCount` on game detail and `GET /api/users/{username}/statistics` (implements FR-STATS-010…012, FR-STATS-020…027)

## Stakeholders

| Role | Description |
|------|-------------|
| Unauthenticated Visitor | Can view game-level stats on game detail pages |
| Guest User | Contributes to game-level session counts; has no personal stats |
| Registered User | Accumulates personal stats; stats visible on public profiles |
| Platform (System) | Records completed sessions and computes stats via live queries |

---

## Functional Requirements

### Stat Collection

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-STATS-001 | Countable session | A session is counted in statistics only when the game engine reports it as complete. Valid completion signals are: natural game completion and forfeit by a participant. Any session that ends without a game engine completion signal — including sessions terminated by all players disconnecting or by room closure mid-game — is not counted. | Must |
| FR-STATS-002 | Spectator exclusion | Spectator participation in a session does not count toward any statistic for that user. Only players contribute to personal stats. | Must |
| FR-STATS-003 | Guest contribution | Guest users are not tracked in personal statistics, but their completed sessions count toward per-game session totals. | Must |
| FR-STATS-004 | Deletion persistence | When a registered user's account is deleted, per-game session counts are not retroactively adjusted. The platform maintains a denormalized session counter per game, incremented at session completion and never decremented. Account deletion does not modify this counter. | Must |

### Game Detail Page — Stats Tab

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-STATS-010 | Games played count | The stats tab on the game detail page (`/games/:id`) must display the total number of completed sessions ever played for that game, across all players (registered and guest). | Must |
| FR-STATS-011 | Stat placement | The games played count must be displayed as a card within a dedicated "Statistics" section on the stats tab of the game detail page. | Must |
| FR-STATS-012 | Live query | The games played count is fetched live on each page load by reading the game's denormalized session counter (see FR-STATS-004). No real-time updates after initial load are required. | Must |

### User Profile — Inline Stats

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-STATS-020 | Total played games | The user profile must display the total number of completed sessions the user has participated in as a player, across all games. | Must |
| FR-STATS-021 | Most played game | The user profile must display the game in which the user has the most completed sessions as a player. If multiple games are tied, the one that comes first alphabetically by title is used. | Must |
| FR-STATS-022 | Most played game link | The most played game entry must link to that game's detail page at `/games/:id`. | Must |
| FR-STATS-023 | Zero state | If a user has never completed a game session as a player, total played games displays `0` and the most played game displays a placeholder (no game name, no link). | Must |
| FR-STATS-024 | Stats inline placement | User profile stats are displayed inline within the profile content, not in a separate tab. | Must |
| FR-STATS-025 | Stats live query | User profile stats are fetched live on each profile page load. | Must |
| FR-STATS-026 | Guest profile exclusion | Guest user profiles do not display any stats section. | Must |
| FR-STATS-027 | Profile stats visibility | User profile statistics are hidden from visitors when the profile is private, or when the statistics section is hidden via per-section visibility settings (see FR-PROF-006 in `user-accounts.md`). The profile owner always sees their own statistics regardless of privacy setting. | Must |

---

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-STATS-001 | Performance | Per-game session counter read latency | p95 < 300ms | Must |
| NFR-STATS-002 | Performance | User profile stats query latency (total sessions, most played game) | p95 < 300ms | Must |
| NFR-STATS-003 | Scalability | Session count queries must be backed by appropriate database indexing to remain performant as session history grows. | — | Must |

---

## Constraints

| ID | Description |
|----|-------------|
| CON-001 | Stats are computed via live API queries on each page load; no pre-aggregation or caching layer is specified. |
| CON-002 | Frontend must be implemented in React 19 with TypeScript. |
| CON-003 | Only registered users accumulate personal statistics; guest accounts are excluded from personal stat tracking. |

---

## Out of Scope

- Leaderboards and player rankings (explicitly deferred indefinitely)
- Developer-defined or game-specific custom statistics
- Time-scoped stat views (e.g., this week, this month)
- Per-game breakdown on the user profile (e.g., sessions per game listed individually)
- A dedicated stats tab on the user profile (deferred to a future phase)
- Win/loss/draw tracking or any outcome-based personal statistics
- Real-time stat updates after initial page load

---

## Open Questions

- None outstanding.
