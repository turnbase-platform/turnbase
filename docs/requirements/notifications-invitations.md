# Notifications & Invitations Requirements

## Related API Specifications

- [sse-notifications.md](../specs/api-design/sse-notifications.md) — SSE stream implementation for real-time notification delivery (implements FR-NOTIF-007, FR-NOTIF-008; resolves CON-001)

## Stakeholders

| Role | Description |
|------|-------------|
| Player | Authenticated user who sends and receives invitations and notifications |
| Host | Player who sends game room invitations to friends |
| Invitee | Friend who receives a game room invitation |
| Platform | Generates alerts and notifications in response to system events |

---

## Definitions

| Term | Meaning |
|------|---------|
| **Alert** | A transient, ephemeral message shown in-session; never persisted. Used for platform interactions, acknowledgements, and errors. |
| **Notification** | A persisted, actionable or informational message delivered to a specific user. Survives page navigation; visible in the notification center. |

---

## Functional Requirements

### Alerts

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-ALERT-001 | Display alert | The platform displays an alert as a transient overlay (e.g. toast/banner) for in-session feedback. Alerts are never stored or shown in the notification center. | Must |
| FR-ALERT-002 | Alert triggers | Alerts are generated for: operation successes (e.g. game uploaded, invite sent), operation failures (e.g. join rejected with cause), authentication events (login failed, throttled), and service errors. | Must |
| FR-ALERT-003 | Alert auto-dismiss | Alerts auto-dismiss after a short display period without user interaction. | Must |
| FR-ALERT-004 | Alert queueing | When multiple alerts fire in succession, they are queued and displayed sequentially, not stacked or replaced. | Should |
| FR-ALERT-005 | Reconnection alert | When a player is disconnected from a room they can re-enter, a transient alert is shown with a Rejoin button and a Dismiss option. After dismissal, a pinned card remains on the Active Rooms view. Full details in reconnection-flow.md FR-REJOIN-001 and FR-REJOIN-002. | Must |
| FR-ALERT-010 | Alerts are a distinct delivery class | Alerts and notifications may share a real-time transport, but they are distinct event classes on it and must be distinguishable by the client without inspecting the payload. An alert carries no identifier, has no read state, is never persisted, and is **dropped** if the recipient is not connected — replaying a stale acknowledgement on next login is the behaviour FR-ALERT-001 exists to exclude. A notification carries an identifier, has read state, and is replayed if it was not delivered (FR-NOTIF-008). Three messages currently modelled as notifications are alerts by this test and are reclassified: invitation accepted and invitation declined (FR-INV-006 already calls them alerts) and session displaced (FR-SESS-004 is an error response — and a persisted notification addressed to a session that has just been invalidated cannot be read by its recipient). | Must |

### Notification Center

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-NOTIF-001 | Notification center access | The notification center is accessible via an overlay (e.g. triggered from a nav icon) and as a dedicated view within the player's own profile. It is visible only to the authenticated user. | Must |
| FR-NOTIF-002 | Unread badge | A visible unread notification count is displayed on the notification center entry point (e.g. bell icon). The count reflects all unread notifications. | Must |
| FR-NOTIF-003 | Read/unread state | Each notification has a read or unread state. A notification transitions to read when the user clicks or taps it. Once read, it cannot become unread. | Must |
| FR-NOTIF-004 | Mark all as read | A single action marks all notifications as read. | Should |
| FR-NOTIF-005 | Delete notification | A player can permanently delete any individual notification. This action is irreversible. | Must |
| FR-NOTIF-006 | Notification retention | Notifications are retained for 30 days from creation, then automatically purged. The retention period is configurable at the platform level. | Must |
| FR-NOTIF-007 | Real-time delivery | Notifications are delivered in real-time while the player is online. The specific mechanism (e.g. WebSocket, SSE) is an implementation decision and must not be locked in at requirements stage. | Must |
| FR-NOTIF-008 | Offline delivery | Notifications generated while a player is offline are delivered upon their next session. | Must |
| FR-NOTIF-009 | Pagination | The notification center list is paginated. Total notification count and total page count are shown. | Must |

### Game Invitation Notifications

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-INV-001 | Send invitation | A host can invite friends to their game room one at a time via the platform. The invitation is delivered as a notification to the invitee. | Must |
| FR-INV-002 | Friends-only restriction | Platform invitations may only be sent to players who are friends with the host. | Must |
| FR-INV-003 | Invitation actions | An invitation notification presents two inline actions: Accept and Decline. A player may also ignore the invitation (take neither action). Invitations do not reserve or block room slots. | Must |
| FR-INV-004 | Accept invitation — join flow | On accepting an invitation, the player is taken to the room view. If the room supports both player and spectator roles and both are available, the player is presented with a choice before fully joining. Room joining follows the rules in game-rooms FR-JOIN-003 through FR-JOIN-008. | Must |
| FR-INV-005 | Accept invitation — join rejected | If the room can no longer accommodate the player (no available slots, no spectating, room closed), the join attempt fails and an alert is shown with the reason. | Must |
| FR-INV-006 | Sender alert on response | When an invitee accepts or declines, the host receives an alert. No alert is sent when an invitation is ignored. | Must |
| FR-INV-007 | Multiple pending invitations | A player may hold multiple pending invitations simultaneously. Accepting one does not automatically decline others — they remain pending. The single-room constraint (game-rooms FR-JOIN-007) is enforced at join time. | Must |
| FR-INV-008 | Stale invitation handling | If a room is closed or removed, any pending invitation notifications referencing that room are deleted. The deletion happens **when the room closes**, not when the room record is later purged (`platform-operations.md` FR-RET-006 retains closed rooms for 7 days). If a stale notification is acted on before deletion occurs, the join fails gracefully with an alert explaining the room is no longer available. | Must |
| FR-INV-009 | Invitation expiry | A room invitation expires after the same configurable window as notification retention (default 30 days) and is then deleted along with its notification. Without an expiry of its own, an ignored invitation to a room that never closes — an in-progress room with connected players never reaches the idle timeout — keeps its notification alive indefinitely, because FR-FREQ-006 correctly forbids the generic purge from removing a notification whose object is still live. Sharing the retention window with FR-NOTIF-006 rather than choosing a second one is deliberate: two clocks on one object is the defect FR-FREQ-006 exists to prevent. | Must |

### Friend Request Notifications

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-FREQ-001 | Friend request as notification | Incoming friend requests are delivered as notifications and appear in the notification center. | Must |
| FR-FREQ-002 | Friend request actions | A friend request notification presents two inline actions: Accept and Decline. A player may ignore the request (take neither action). | Must |
| FR-FREQ-003 | Accept friend request | On accept, the two players become friends. The sender receives a notification that their request was accepted. The accepting player receives a confirmation notification. | Must |
| FR-FREQ-004 | Decline friend request | On decline, the sender receives a notification that their request was declined. The declining user receives no separate confirmation. | Must |
| FR-FREQ-005 | Friend request retention | Friend requests follow the standard 30-day notification retention policy. An expired friend request is automatically purged with no further action. | Must |
| FR-FREQ-006 | The request is the durable object; its notification follows it | A notification that carries an inline action (an incoming friend request, a room invitation) refers to an underlying object with its own lifecycle. That object's lifecycle governs the notification's: resolving, cancelling or expiring the request or invitation must delete the notifications referring to it, in the same operation. Conversely, the generic retention purge (FR-NOTIF-006) must **not** remove a notification whose underlying object is still live. Without this rule the two are independently timed clocks on one thing, and the recipient of a long-lived request either loses the ability to act on it from the notification center while it is still listed in their Pending tab, or is left holding an action whose target no longer exists. | Must |

### Join Links

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-LINK-001 | Join link is external | Room join links are shared outside the platform (e.g. via Discord). They are not delivered through the notification system. | Must |
| FR-LINK-002 | Join link behavior | Clicking a join link takes the user directly to the room. All joining rules from game-rooms (FR-JOIN-003 through FR-JOIN-006) apply — including player/spectator choice and late-join handling. | Must |

---

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-PERF-001 | Performance | Notification delivered to an online user after the triggering event | < 500ms p95 | Should |
| NFR-SEC-001 | Security | Notification center content is visible only to the authenticated owner — no cross-user access | No client-side trust | Must |
| NFR-SCALE-001 | Scalability | Notification retention window is configurable at the platform level without code changes | Default: 30 days | Must |

---

## Constraints

| ID | Description |
|----|-------------|
| CON-001 | Real-time notification delivery mechanism (WebSocket, SSE, etc.) is an implementation decision — requirements must not prescribe it |
| CON-002 | Backend: Java 21, Spring Boot 4.1+ |
| CON-003 | Frontend: React 19, TypeScript |

---

## Out of Scope

- Email and push notifications (external delivery channels)
- Administrative announcements (platform-wide broadcasts)
- Player blocking
- Notification preferences / per-type mute controls
- Invitation status tracking in the room lobby UI
