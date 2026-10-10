# Social & Friends System Requirements

## Stakeholders

| Role | Description |
|------|-------------|
| Registered User | Can send/receive friend requests, manage their friend list, and discover other players |
| Guest User | Cannot participate in any social features; friend UI is not displayed |
| Platform | Enforces relationship integrity, caps, visibility rules, and notification delivery |

---

## Definitions

| Term | Meaning |
|------|---------|
| **Friend relationship** | A mutual, bidirectional bond between two registered users. Both users see each other in their friend list. |
| **Friend request** | A pending invitation from a sender to a recipient. Exists until accepted, declined, cancelled, or expired (30-day retention). |
| **Reverse request** | A friend request from B to A when A already has a pending request to B. |

---

## Functional Requirements

### Friend Requests

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-SOC-001 | Send friend request — from profile | A registered user can send a friend request by visiting another registered user's profile and clicking "Send friend request." The button is not shown on the viewer's own profile, on guest profiles, or when a relationship or pending request already exists between the two users. | Must |
| FR-SOC-002 | Send friend request — by username search | A registered user can search for other registered users by username (prefix match) and send a friend request from the search results. Guest accounts do not appear in search results. Users with private profiles appear in search results; their profile content is hidden but the Send Request action is available, subject to FR-SOC-021. | Must |
| FR-SOC-003 | Duplicate request prevention | A user cannot send a friend request to someone they are already friends with, have a pending outgoing request to, or have a pending incoming request from. The UI prevents this by hiding or disabling the send action in these states. | Must |
| FR-SOC-004 | Reverse request auto-accept | If user A sends a friend request to user B, and a pending request from B to A already exists, the platform automatically accepts both requests and creates the friendship immediately. No manual action is required from either user. | Must |
| FR-SOC-005 | Cancel outgoing request | A registered user can cancel an outgoing friend request they have sent that has not yet been accepted or declined. The recipient's pending notification is removed. | Must |
| FR-SOC-006 | Accept friend request | A registered user can accept an incoming friend request. On acceptance, a mutual friendship is created. The sender receives a notification that their request was accepted. See notifications-invitations.md FR-FREQ-003. | Must |
| FR-SOC-007 | Decline friend request | A registered user can decline an incoming friend request. The request is removed. The sender receives a notification that their request was declined. See notifications-invitations.md FR-FREQ-004 (amended). | Must |
| FR-SOC-008 | Ignore friend request | A user may take no action on a friend request. The request remains pending until cancelled by the sender, the user acts on it, or it expires per the 30-day retention policy (notifications-invitations.md FR-FREQ-005). | Should |

### Friend List & Relationships

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-SOC-009 | Friend list cap | A registered user may have at most 50 friends simultaneously. When the cap is reached, outgoing friend requests cannot be sent until a friendship is removed. Incoming friend requests are still created and recorded, but the recipient cannot accept them while at cap; the pending request remains visible to both parties and may be accepted once the recipient drops below cap. | Must |
| FR-SOC-010 | Friend list order | The friend list is sorted alphabetically by username, case-insensitively. | Must |
| FR-SOC-011 | Unfriend | Either user in a friendship can remove the other from their friend list at any time. The removal is immediate and mutual — both users are removed from each other's friend list simultaneously. | Must |
| FR-SOC-012 | Relationship cleanup on deletion | When a registered account is deleted, all of that user's active friendships and pending friend requests (both sent and received) are removed. No notifications are sent for these removals. See user-accounts.md FR-ACCT-005. | Must |

### Friend List UI

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-SOC-013 | Friends tab | A registered user's profile includes a Friends section with two tabs: **Friends** (confirmed relationships) and **Pending** (all unresolved requests). The Pending tab is visible only to the profile owner. | Must |
| FR-SOC-014 | Pending tab — incoming requests | The Pending tab shows all incoming friend requests, each with Accept and Decline actions. | Must |
| FR-SOC-015 | Pending tab — outgoing requests | The Pending tab also shows all outgoing friend requests the user has sent that have not yet been accepted or declined, each with a Cancel action. | Must |
| FR-SOC-016 | Profile button state | On a registered user's public profile, the "Send friend request" button is replaced with contextual state labels: **Friends** (with an Unfriend action), **Request sent** (with a Cancel action), or **Request received** (with Accept / Decline actions). | Must |

### Visibility

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-SOC-017 | Friend list visibility options | The Friends section supports three visibility levels independently of other profile sections: **Public** (all visitors), **Friends Only** (only confirmed friends of the profile owner), and **Hidden** (no one except the profile owner). The default is Public. | Must |
| FR-SOC-018 | Profile owner always sees own friends | The Friends section (both tabs) is always fully visible to the profile owner regardless of the configured visibility level. | Must |
| FR-SOC-019 | Visibility when profile is private | When a profile is set to private (user-accounts.md FR-PROF-005), the Friends section is hidden to all visitors regardless of the Friends section visibility setting. | Must |
| FR-SOC-020 | Guest user — no social UI | All friend-related UI elements (friend list, pending tab, send request button) are hidden from guest users. Guest accounts cannot send or receive friend requests. See user-accounts.md FR-GUEST-007. | Must |
| FR-SOC-021 | Block incoming friend requests | A registered user may enable a privacy setting (user-accounts.md FR-PROF-008) that prevents other users from sending them friend requests. When this setting is enabled: the "Send friend request" button is hidden on their profile and in username search results; attempts to send a request via the API are rejected. Existing friendships and pending requests already in the system are unaffected when the setting is enabled. | Must |

---

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-SOC-PERF-001 | Performance | Friend request send, accept, decline, and unfriend operations complete end-to-end | < 300ms p95 | Should |
| NFR-SOC-PERF-002 | Performance | Username search results are returned | < 500ms p95 | Should |
| NFR-SOC-SEC-001 | Security | Friendship and request data is only readable by the users involved or public visitors for the visible portion; no cross-user enumeration is possible via the API | No client-side trust | Must |
| NFR-SOC-SCALE-001 | Scalability | Friend cap (50) and notification retention (30 days) are configurable at the platform level without code changes | See FR-SOC-009, notifications-invitations.md FR-FREQ-005 | Should |

---

## Constraints

| ID | Description |
|----|-------------|
| CON-001 | Backend: Java 21, Spring Boot 4.1+ |
| CON-002 | Frontend: React 19, TypeScript |
| CON-003 | Real-time notification delivery mechanism is an implementation decision (notifications-invitations.md CON-001) |

---

## Out of Scope

- User blocking and unblocking
- Abuse reporting
- Suggested friends / mutual-friend discovery
- Friends-only game room visibility filters
- Online/offline presence indicators for friends
- Mutual friend count or display
- Admin tooling for social graph management

---

## Open Questions

*All open questions resolved.*

- **OQ-001 (resolved)** — Incoming requests when recipient is at cap are recorded and remain visible to both parties. The recipient cannot accept until they drop below 50 friends. No immediate notification is sent to the sender; they see the request as pending (FR-SOC-009).
- **OQ-002 (resolved)** — Private-profile users appear in username search results with the Send Request option available. Private profile only hides profile content, not discoverability. Users who want to block incoming requests use the dedicated privacy toggle (FR-SOC-021).
