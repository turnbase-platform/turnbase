# Admin Tooling Requirements

## Stakeholders

| Role | Description |
|------|-------------|
| Platform operator | TurnBase staff with SSH access to the host machine; the sole user of admin tooling |
| Game developer | Community member who uploads games; affected by review decisions and notifications |
| Player | Affected indirectly by which games appear in the public catalog |

## Functional Requirements

### Admin API Access

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-ADM-001 | Internal-only port | The admin API is served on a separate HTTP port bound exclusively to `localhost`. It is never exposed on the internet-facing network interface. | Must |
| FR-ADM-002 | Basic auth protection | All admin endpoints require HTTP Basic Authentication. Credentials are static and configured via environment variables at deploy time. | Must |
| FR-ADM-003 | No admin UI | There is no browser-based admin panel. Operators interact with the admin API directly (e.g. via SSH tunnel + `curl` or similar). | Must |

### Game Badge Model

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-BADGE-001 | Three-state badge | Every game in the system carries exactly one badge: **Official**, **Verified**, or **Unverified**. A game cannot hold more than one badge simultaneously. | Must |
| FR-BADGE-002 | Official badge | Assigned to games uploaded directly by a platform operator. Indicates the game is first-party TurnBase content. Cannot be assigned to community-uploaded games. | Must |
| FR-BADGE-003 | Verified badge | Assigned to a community-uploaded game that has passed admin review and is approved for the public catalog. | Must |
| FR-BADGE-004 | Unverified badge | Default badge for community-uploaded games that have not been approved. Unverified games are private: they do not appear in the public catalog. | Must |

### Game Review Queue

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-REV-001 | Pending state on submission | When a game developer submits their game for public review, the game enters a **pending review** state and is added to the admin review queue. The game remains private (Unverified) during review. | Must |
| FR-REV-002 | List pending games | Admin can retrieve a list of all games currently in the pending review queue, ordered by submission date ascending (oldest first). | Must |
| FR-REV-003 | View game details | Admin can retrieve full details of any game: name, description, developer, upload date, bundle metadata, and current badge/state. | Must |
| FR-REV-004 | Approve game | Admin can approve a pending game. Approval transitions the game to the **Verified** badge and makes it publicly visible in the catalog. The developer receives a platform notification informing them of approval. | Must |
| FR-REV-005 | Reject game | Admin can reject a pending game, supplying a plain-text rejection reason. The game remains private (Unverified) and does not enter the public catalog. The developer receives a platform notification containing the rejection reason. | Must |
| FR-REV-006 | Rejection is non-destructive | Rejecting a game does not delete it. The developer retains ownership and the game remains in their library in its current private state. | Must |

### Official Game Management

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-OFF-001 | Upload official game | Admin can upload a game directly as an Official title. Official games bypass the review queue and are immediately publicly visible in the catalog upon upload. | Must |
| FR-OFF-002 | No review for official titles | Official games are never placed in the pending review queue, regardless of who triggers the upload mechanism. | Must |

### Private Game Behaviour

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-PRV-001 | Private game invisibility | An Unverified (private) game is not shown in the public game catalog or any search results to users other than the owner. | Must |
| FR-PRV-002 | Owner-only hosting | Only the game's owner may host a room for an Unverified game. No other player may start a session of a private game. | Must |
| FR-PRV-003 | Restricted joining | Rooms hosted for Unverified games are always private. Joining is restricted to players who are friends with the host or who have received an explicit invite link. | Must |
| FR-PRV-004 | Public submission | The owner of an Unverified game may submit it for public review at any time, transitioning it to the pending review state. | Must |

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-SEC-001 | Security | The admin port must not be reachable from outside the host machine. Verified by network configuration (firewall / binding to `127.0.0.1`). | Zero external reachability | Must |
| NFR-AUD-001 | Auditability | Every admin action (approve, reject, official upload) is written to the structured application log with the action type, target game ID, and timestamp. | 100% of mutating admin actions logged | Must |
| NFR-CRED-001 | Credential hygiene | Admin credentials must never appear in logs, stack traces, or error responses. | Zero credential leaks in output | Must |

## Constraints

| ID | Description |
|----|-------------|
| CON-001 | The admin API is implemented within the Platform Monolith and exposed on a separate management port (e.g. Spring Boot management port pattern). It is not a separate service. |
| CON-002 | Credentials are static strings supplied via environment variable at deploy time. No credential rotation mechanism is required at this stage. |
| CON-003 | The admin API is HTTP/JSON (same conventions as the public REST API). No dedicated admin UI is built. |

## Out of Scope

- Account moderation (ban, suspend, warn, delete player accounts)
- Chat or message moderation
- Fine-grained admin role tiers (all operators have full access)
- Game content scanning or automated policy enforcement
- Game resubmission workflow after rejection (behaviour after rejection is left undefined for now)
- Admin dashboard or browser-based UI

## Open Questions

- OQ-001: Can a developer resubmit a rejected game for another review attempt, or is rejection terminal? (deferred)
- OQ-002: Can an operator delist a Verified or Official game after it has gone public (e.g. for a policy violation discovered post-approval)? (deferred)
- OQ-003: Should the Unverified badge label be shown to the owner when they view their own game, to distinguish it from a Verified game? (UX detail, deferred to design phase)
