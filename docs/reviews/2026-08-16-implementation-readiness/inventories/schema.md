# TurnBase Relational Schema Inventory

## Section 1 — Table Register

| Table | Owning Document | Purpose | PK | Source `file:line` |
|---|---|---|---|---|
| `room` | data-model.md | Owns rooms, host, state, lifecycle | `room_id` | 38–72 |
| `room_participant` | data-model.md | Participant slots, grace, leave state | `(room_id, user_id)` | 158–183 |
| `room_team` | data-model.md | Team declarations per game template | `team_id` | 230–238 |
| `session_teardown` | data-model.md | Durable owed teardown, retry loop | `session_id` | 286–297 |
| `game_input_outbox` | data-model.md | Durable outbox, player_left effects | `id` | 313–326 |
| `app_user` | data-model-accounts.md | User accounts, registered/guest, identity | `user_id` | 31–67 |
| `user_auth_method` | data-model-accounts.md | Password/OAuth credentials per user | `auth_method_id` | 223–241 |
| `user_session` | data-model-accounts.md | Login sessions, revocation state | `session_id` | 277–290 |
| `user_privacy_settings` | data-model-accounts.md | Profile/history/friend visibility toggles | `user_id` | 336–351 |
| `friendship` | data-model-social.md | Bidirectional friendships, one row per pair | `(user_id_low, user_id_high)` | 20–39 |
| `friend_request` | data-model-social.md | Pending friend requests with 30d window | `request_id` | 96–117 |
| `game` | data-model-catalog.md | Game metadata, badge, listing, ownership | `game_id` | 34–60 |
| `game_version` | data-model-catalog.md | Game versions, validation, bundle tracking | `version_id` | 197–245 |
| `game_tag` | data-model-catalog.md | Projection of active version tags (searchable) | `(game_id, tag)` | 425–432 |
| `game_review` | data-model-catalog.md | Admin review queue, decision audit trail | `review_id` | 467–488 |
| `game_session_completion` | data-model-history.md | Session completion record, idempotency key | `session_id` | 27–39 |
| `game_history_entry` | data-model-history.md | Per-player history, placement, stats | `entry_id` | 80–110 |
| `notification` | data-model-notifications.md | Persisted notifications, delivery, read state | `notification_id` | 24–58 |
| `room_invitation` | data-model-notifications.md | Pending friend invites to rooms, 30d deadline | `invitation_id` | 159–177 |

---

## Section 2 — Per-table Detail

### `room`

**Columns:**
- `room_id`: uuid PRIMARY KEY
- `game_id`: uuid NOT NULL
- `game_version`: text NOT NULL
- `host_user_id`: uuid NULL
- `visibility`: text NOT NULL
- `state`: text NOT NULL
- `spectating_enabled`: boolean NOT NULL DEFAULT false
- `invite_code`: text NULL UNIQUE
- `parameters`: jsonb NOT NULL DEFAULT '{}'::jsonb
- `version`: bigint NOT NULL DEFAULT 0
- `active_session_id`: uuid NULL
- `owner_instance_id`: text NULL
- `owner_epoch`: bigint NOT NULL DEFAULT 0
- `ownerless_since`: timestamptz NULL
- `migration_window_expires_at`: timestamptz NULL
- `last_activity_at`: timestamptz NOT NULL DEFAULT now()
- `closed_at`: timestamptz NULL
- `closed_reason`: text NULL
- `reconcile_flagged_at`: timestamptz NULL
- `created_at`: timestamptz NOT NULL DEFAULT now()

**Foreign Keys:**
- `game_id` → `game(game_id)` (no ON DELETE stated)
- `host_user_id` → `app_user(user_id)` (no ON DELETE stated, nullable)

**Indexes:**
- `room_open_state_idx` on `(state)` WHERE `state <> 'CLOSED'`
- `room_idle_lobby_idx` on `(last_activity_at)` WHERE `state = 'LOBBY'`
- `room_closed_purge_idx` on `(closed_at)` WHERE `state = 'CLOSED'`
- `room_active_session_idx` on `(active_session_id)` WHERE `active_session_id IS NOT NULL`
- `room_open_game_idx` on `(game_id, game_version)` WHERE `state <> 'CLOSED'`

**Constraints:**
- None named

Source: data-model.md:38–72

---

### `room_participant`

**Columns:**
- `room_id`: uuid NOT NULL
- `user_id`: uuid NOT NULL
- `role`: text NOT NULL
- `team_id`: uuid NULL
- `joined_at`: timestamptz NOT NULL DEFAULT now()
- `join_order`: integer NOT NULL
- `connection_count`: integer NOT NULL DEFAULT 0
- `ready`: boolean NOT NULL DEFAULT false
- `grace_reservation_id`: uuid NULL
- `grace_expires_at`: timestamptz NULL
- `left_at`: timestamptz NULL
- `leave_reason`: text NULL
- `lost_announced_at`: timestamptz NULL

**Primary Key:** `(room_id, user_id)`

**Foreign Keys:**
- `room_id` → `room(room_id)` ON DELETE CASCADE
- `user_id` → `app_user(user_id)` (no ON DELETE stated)
- `team_id` → `room_team(team_id)` (nullable, no ON DELETE stated)

**Indexes:**
- `room_participant_grace_due_idx` on `(grace_expires_at)` WHERE `grace_expires_at IS NOT NULL AND left_at IS NULL`

**Constraints:**
- None named

Source: data-model.md:158–183

---

### `room_team`

**Columns:**
- `team_id`: uuid PRIMARY KEY
- `room_id`: uuid NOT NULL
- `template_index`: integer NOT NULL
- `team_index`: integer NOT NULL
- `configured_size`: integer NOT NULL

**Foreign Keys:**
- `room_id` → `room(room_id)` ON DELETE CASCADE

**Indexes:**
- (implicit from UNIQUE constraint)

**Constraints:**
- `UNIQUE (room_id, template_index, team_index)`

Source: data-model.md:230–238

---

### `session_teardown`

**Columns:**
- `session_id`: uuid PRIMARY KEY
- `room_id`: uuid NOT NULL
- `reason`: text NOT NULL
- `requested_at`: timestamptz NOT NULL DEFAULT now()
- `attempts`: integer NOT NULL DEFAULT 0
- `next_attempt_at`: timestamptz NOT NULL DEFAULT now()
- `last_error`: text NULL

**Foreign Keys:**
- None (deliberately)

**Indexes:**
- `session_teardown_due_idx` on `(next_attempt_at)`

**Constraints:**
- None named

Source: data-model.md:286–297

---

### `game_input_outbox`

**Columns:**
- `id`: bigserial PRIMARY KEY
- `session_id`: uuid NOT NULL
- `sequence`: bigint NULL
- `payload`: jsonb NOT NULL
- `created_at`: timestamptz NOT NULL DEFAULT now()
- `attempts`: integer NOT NULL DEFAULT 0
- `dispatched_at`: timestamptz NULL
- `last_error`: text NULL

**Foreign Keys:**
- None

**Indexes:**
- `game_input_outbox_pending_idx` on `(session_id, id)` WHERE `dispatched_at IS NULL`

**Constraints:**
- None named

Source: data-model.md:313–326

---

### `app_user`

**Columns:**
- `user_id`: uuid PRIMARY KEY
- `kind`: text NOT NULL
- `username`: text NOT NULL
- `username_skeleton`: text NOT NULL
- `email`: text NULL
- `email_source`: text NULL
- `guest_serial`: bigint NULL
- `username_changed_at`: timestamptz NULL
- `email_changed_at`: timestamptz NULL
- `created_at`: timestamptz NOT NULL DEFAULT now()
- `deleted_at`: timestamptz NULL
- `deletion_reason`: text NULL
- `purgeable_after`: timestamptz NULL

**Foreign Keys:**
- None

**Indexes:**
- `app_user_skeleton_key` UNIQUE on `(username_skeleton)`
- `app_user_id_kind_key` UNIQUE on `(user_id, kind)`
- `app_user_guest_serial_key` UNIQUE on `(guest_serial)` WHERE `guest_serial IS NOT NULL`
- `app_user_email_key` UNIQUE on `(lower(email))` WHERE `email IS NOT NULL`
- `app_user_username_trgm_idx` GIN on `(lower(username))` WHERE `kind = 'REGISTERED' AND deleted_at IS NULL`
- `app_user_guest_expiry_idx` on `(created_at)` WHERE `kind = 'GUEST' AND deleted_at IS NULL`
- `app_user_guest_purge_idx` on `(purgeable_after)` WHERE `kind = 'GUEST' AND purgeable_after IS NOT NULL`

**Constraints:**
- `app_user_kind_ck` CHECK `kind IN ('REGISTERED','GUEST')`
- `app_user_username_len_ck` CHECK `char_length(username) BETWEEN 3 AND 32`
- `app_user_guest_serial_ck` CHECK `(kind = 'GUEST') = (guest_serial IS NOT NULL)`
- `app_user_email_ck` CHECK `(kind = 'GUEST' OR deleted_at IS NOT NULL OR (email IS NOT NULL AND email_source IS NOT NULL))`

Source: data-model-accounts.md:31–67

---

### `user_auth_method`

**Columns:**
- `auth_method_id`: uuid PRIMARY KEY
- `user_id`: uuid NOT NULL
- `method`: text NOT NULL
- `password_hash`: text NULL
- `provider_subject`: text NULL
- `created_at`: timestamptz NOT NULL DEFAULT now()
- `updated_at`: timestamptz NOT NULL DEFAULT now()

**Foreign Keys:**
- `user_id` → `app_user(user_id)` ON DELETE CASCADE

**Indexes:**
- `user_auth_method_per_user_key` UNIQUE on `(user_id, method)`
- `user_auth_method_subject_key` UNIQUE on `(method, provider_subject)` WHERE `provider_subject IS NOT NULL`

**Constraints:**
- `user_auth_method_shape_ck` CHECK `((method = 'PASSWORD' AND password_hash IS NOT NULL AND provider_subject IS NULL) OR (method = 'GOOGLE' AND password_hash IS NULL AND provider_subject IS NOT NULL))`

Source: data-model-accounts.md:223–241

---

### `user_session`

**Columns:**
- `session_id`: uuid PRIMARY KEY
- `user_id`: uuid NOT NULL
- `issued_at`: timestamptz NOT NULL DEFAULT now()
- `expires_at`: timestamptz NOT NULL
- `revoked_at`: timestamptz NULL
- `revoked_reason`: text NULL
- `key_id`: text NOT NULL
- `user_agent_hash`: text NULL

**Foreign Keys:**
- `user_id` → `app_user(user_id)` ON DELETE CASCADE

**Indexes:**
- `user_session_active_key` UNIQUE on `(user_id)` WHERE `revoked_at IS NULL`
- `user_session_expiry_idx` on `(expires_at)` WHERE `revoked_at IS NULL`

**Constraints:**
- None named

Source: data-model-accounts.md:277–290

---

### `user_privacy_settings`

**Columns:**
- `user_id`: uuid PRIMARY KEY
- `profile_private`: boolean NOT NULL DEFAULT false
- `history_visibility`: text NOT NULL DEFAULT 'PUBLIC'
- `stats_visibility`: text NOT NULL DEFAULT 'PUBLIC'
- `games_visibility`: text NOT NULL DEFAULT 'PUBLIC'
- `friends_visibility`: text NOT NULL DEFAULT 'PUBLIC'
- `block_friend_requests`: boolean NOT NULL DEFAULT false
- `updated_at`: timestamptz NOT NULL DEFAULT now()

**Foreign Keys:**
- `user_id` → `app_user(user_id)` ON DELETE CASCADE

**Indexes:**
- None explicit

**Constraints:**
- `ups_history_ck` CHECK `history_visibility IN ('PUBLIC','HIDDEN')`
- `ups_stats_ck` CHECK `stats_visibility IN ('PUBLIC','HIDDEN')`
- `ups_games_ck` CHECK `games_visibility IN ('PUBLIC','HIDDEN')`
- `ups_friends_ck` CHECK `friends_visibility IN ('PUBLIC','FRIENDS_ONLY','HIDDEN')`

Source: data-model-accounts.md:336–351

---

### `friendship`

**Columns:**
- `user_id_low`: uuid NOT NULL
- `user_id_high`: uuid NOT NULL
- `kind_low`: text NOT NULL DEFAULT 'REGISTERED'
- `kind_high`: text NOT NULL DEFAULT 'REGISTERED'
- `created_at`: timestamptz NOT NULL DEFAULT now()

**Primary Key:** `(user_id_low, user_id_high)`

**Foreign Keys:**
- `friendship_low_fk`: `(user_id_low, kind_low)` → `app_user(user_id, kind)` ON DELETE CASCADE ON UPDATE CASCADE
- `friendship_high_fk`: `(user_id_high, kind_high)` → `app_user(user_id, kind)` ON DELETE CASCADE ON UPDATE CASCADE

**Indexes:**
- `friendship_high_idx` on `(user_id_high)`

**Constraints:**
- `friendship_order_ck` CHECK `user_id_low < user_id_high`
- `friendship_low_registered_ck` CHECK `kind_low = 'REGISTERED'`
- `friendship_high_registered_ck` CHECK `kind_high = 'REGISTERED'`

Source: data-model-social.md:20–39

---

### `friend_request`

**Columns:**
- `request_id`: uuid PRIMARY KEY
- `sender_id`: uuid NOT NULL
- `recipient_id`: uuid NOT NULL
- `sender_kind`: text NOT NULL DEFAULT 'REGISTERED'
- `recipient_kind`: text NOT NULL DEFAULT 'REGISTERED'
- `created_at`: timestamptz NOT NULL DEFAULT now()
- `expires_at`: timestamptz NOT NULL

**Foreign Keys:**
- `friend_request_sender_fk`: `(sender_id, sender_kind)` → `app_user(user_id, kind)` ON DELETE CASCADE ON UPDATE CASCADE
- `friend_request_recipient_fk`: `(recipient_id, recipient_kind)` → `app_user(user_id, kind)` ON DELETE CASCADE ON UPDATE CASCADE

**Indexes:**
- `friend_request_pair_key` UNIQUE on `(sender_id, recipient_id)`
- `friend_request_recipient_idx` on `(recipient_id, created_at DESC)`
- `friend_request_expiry_idx` on `(expires_at)`

**Constraints:**
- `friend_request_self_ck` CHECK `sender_id <> recipient_id`
- `friend_request_sender_registered_ck` CHECK `sender_kind = 'REGISTERED'`
- `friend_request_recipient_registered_ck` CHECK `recipient_kind = 'REGISTERED'`

Source: data-model-social.md:96–117

---

### `game`

**Columns:**
- `game_id`: uuid PRIMARY KEY
- `owner_user_id`: uuid NULL
- `title`: text NOT NULL
- `short_description`: text NOT NULL
- `info_doc_markdown`: text NULL
- `badge`: text NOT NULL DEFAULT 'UNVERIFIED'
- `listed`: boolean NOT NULL DEFAULT false
- `active_version_id`: uuid NULL
- `completed_session_count`: bigint NOT NULL DEFAULT 0
- `created_at`: timestamptz NOT NULL DEFAULT now()
- `updated_at`: timestamptz NOT NULL DEFAULT now()
- `archived_at`: timestamptz NULL
- `deleted_at`: timestamptz NULL

**Foreign Keys:**
- `owner_user_id` → `app_user(user_id)` (no ON DELETE stated, nullable)

**Indexes:**
- `game_public_idx` on `(created_at DESC)` WHERE `deleted_at IS NULL AND archived_at IS NULL AND listed AND badge <> 'UNVERIFIED'`
- `game_owner_idx` on `(owner_user_id)` WHERE `deleted_at IS NULL`
- `game_title_trgm_idx` GIN on `(lower(title))`

**Constraints:**
- `game_badge_ck` CHECK `badge IN ('OFFICIAL','VERIFIED','UNVERIFIED')`
- `game_official_ownerless_ck` CHECK `(badge = 'OFFICIAL') = (owner_user_id IS NULL)`

Source: data-model-catalog.md:34–60

---

### `game_version`

**Columns:**
- `version_id`: uuid PRIMARY KEY
- `game_id`: uuid NOT NULL
- `version`: text NOT NULL
- `version_major`: integer NOT NULL GENERATED ALWAYS AS (split_part) STORED
- `version_minor`: integer NOT NULL GENERATED ALWAYS AS (split_part) STORED
- `version_patch`: integer NOT NULL GENERATED ALWAYS AS (split_part) STORED
- `status`: text NOT NULL
- `manifest`: jsonb NULL
- `gdk_api_version`: text NULL
- `bundle_object_key`: text NULL
- `declared_size_bytes`: bigint NOT NULL
- `stored_size_bytes`: bigint NULL
- `upload_expires_at`: timestamptz NOT NULL
- `validation_errors`: jsonb NULL
- `validation_warnings`: jsonb NULL
- `min_players`: integer NULL
- `max_players`: integer NULL
- `supports_ai`: boolean NULL
- `supports_spectators`: boolean NULL
- `supports_mid_game_join`: boolean NULL
- `claimed_by`: text NULL
- `claimed_until`: timestamptz NULL
- `created_at`: timestamptz NOT NULL DEFAULT now()
- `activated_at`: timestamptz NULL
- `superseded_at`: timestamptz NULL
- `bundle_purged_at`: timestamptz NULL

**Foreign Keys:**
- `game_id` → `game(game_id)` ON DELETE CASCADE
- `game.active_version_id` → `game_version(version_id)` (added at line 243–244)

**Indexes:**
- `game_version_key` UNIQUE on `(game_id, version)`
- `game_version_active_key` UNIQUE on `(game_id)` WHERE `status = 'ACTIVE'`
- `game_version_order_idx` on `(game_id, version_major, version_minor, version_patch)`
- `game_version_upload_expiry_idx` on `(upload_expires_at)` WHERE `status = 'PENDING'`
- `game_version_stuck_idx` on `(claimed_until)` WHERE `status = 'PROCESSING'`
- `game_version_players_idx` on `(min_players, max_players)` WHERE `status = 'ACTIVE'`
- `game_version_gdk_idx` on `(gdk_api_version)` WHERE `status IN ('ACTIVE','SUPERSEDED')`

**Constraints:**
- `game_version_format_ck` CHECK `version ~ '^[0-9]+\.[0-9]+\.[0-9]+$'`
- `game_version_status_ck` CHECK `status IN ('PENDING','PROCESSING','ACTIVE','FAILED','EXPIRED','SUPERSEDED','DISCARDED')`

Source: data-model-catalog.md:197–245

---

### `game_tag`

**Columns:**
- `game_id`: uuid NOT NULL
- `tag`: text NOT NULL

**Primary Key:** `(game_id, tag)`

**Foreign Keys:**
- `game_id` → `game(game_id)` ON DELETE CASCADE

**Indexes:**
- `game_tag_trgm_idx` GIN on `(lower(tag))`

**Constraints:**
- None named

Source: data-model-catalog.md:425–432

---

### `game_review`

**Columns:**
- `review_id`: uuid PRIMARY KEY
- `game_id`: uuid NOT NULL
- `version_id`: uuid NOT NULL
- `submitted_at`: timestamptz NOT NULL DEFAULT now()
- `decided_at`: timestamptz NULL
- `decision`: text NULL
- `rejection_reason`: text NULL
- `decided_by`: text NULL

**Foreign Keys:**
- `game_id` → `game(game_id)` ON DELETE CASCADE
- `version_id` → `game_version(version_id)` (no ON DELETE stated)

**Indexes:**
- `game_review_open_key` UNIQUE on `(game_id)` WHERE `decided_at IS NULL`
- `game_review_queue_idx` on `(submitted_at)` WHERE `decided_at IS NULL`
- `game_review_approved_idx` on `(game_id, decided_at DESC)` WHERE `decision = 'APPROVED'`

**Constraints:**
- `game_review_decision_ck` CHECK `((decided_at IS NULL AND decision IS NULL AND rejection_reason IS NULL AND decided_by IS NULL) OR (decided_at IS NOT NULL AND decision IN ('APPROVED','REJECTED','WITHDRAWN') AND decided_by IS NOT NULL))`
- `game_review_reason_ck` CHECK `decision <> 'REJECTED' OR rejection_reason IS NOT NULL`

Source: data-model-catalog.md:467–488

---

### `game_session_completion`

**Columns:**
- `session_id`: uuid PRIMARY KEY
- `game_id`: uuid NOT NULL
- `game_version`: text NOT NULL
- `completed_at`: timestamptz NOT NULL
- `player_count`: integer NOT NULL
- `team_count`: integer NOT NULL
- `draw`: boolean NOT NULL
- `recorded_at`: timestamptz NOT NULL DEFAULT now()

**Foreign Keys:**
- None (deliberately)

**Indexes:**
- `game_session_completion_game_idx` on `(game_id, completed_at DESC)`

**Constraints:**
- None named

Source: data-model-history.md:27–39

---

### `game_history_entry`

**Columns:**
- `entry_id`: bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY
- `session_id`: uuid NOT NULL
- `user_id`: uuid NULL
- `subject_token`: text NULL
- `game_id`: uuid NOT NULL
- `game_name_snapshot`: text NOT NULL
- `completed_at`: timestamptz NOT NULL
- `placement`: integer NOT NULL
- `team_count`: integer NOT NULL
- `draw`: boolean NOT NULL
- `player_stats`: jsonb NOT NULL DEFAULT '{}'::jsonb
- `team_stats`: jsonb NOT NULL DEFAULT '{}'::jsonb
- `pseudonymized_at`: timestamptz NULL

**Foreign Keys:**
- `session_id` → `game_session_completion(session_id)` (no ON DELETE stated)
- `user_id` → `app_user(user_id)` (no ON DELETE stated, nullable)

**Indexes:**
- `ghe_session_user_key` UNIQUE on `(session_id, user_id)`
- `ghe_user_recent_idx` on `(user_id, completed_at DESC)` WHERE `user_id IS NOT NULL`
- `ghe_user_game_idx` on `(user_id, game_id)` WHERE `user_id IS NOT NULL`
- `ghe_user_name_trgm_idx` GIN on `(user_id, lower(game_name_snapshot))` WHERE `user_id IS NOT NULL`

**Constraints:**
- `ghe_placement_ck` CHECK `placement >= 1 AND placement <= team_count`
- `ghe_subject_ck` CHECK `(user_id IS NULL) = (subject_token IS NOT NULL)`

Source: data-model-history.md:80–110

---

### `notification`

**Columns:**
- `notification_id`: uuid PRIMARY KEY
- `event_seq`: bigint GENERATED ALWAYS AS IDENTITY
- `user_id`: uuid NOT NULL
- `type`: text NOT NULL
- `payload`: jsonb NOT NULL DEFAULT '{}'::jsonb
- `friend_request_id`: uuid NULL
- `invitation_id`: uuid NULL
- `created_at`: timestamptz NOT NULL DEFAULT now()
- `delivered_at`: timestamptz NULL
- `read_at`: timestamptz NULL

**Foreign Keys:**
- `user_id` → `app_user(user_id)` ON DELETE CASCADE
- `friend_request_id` → `friend_request(request_id)` ON DELETE CASCADE
- `notification_invitation_fk`: `invitation_id` → `room_invitation(invitation_id)` ON DELETE CASCADE (added at line 175–176)

**Indexes:**
- `notification_seq_key` UNIQUE on `(event_seq)`
- `notification_user_recent_idx` on `(user_id, created_at DESC)`
- `notification_unread_idx` on `(user_id)` WHERE `read_at IS NULL`
- `notification_undelivered_idx` on `(user_id, event_seq)` WHERE `delivered_at IS NULL`
- `notification_purge_idx` on `(created_at)` WHERE `friend_request_id IS NULL AND invitation_id IS NULL`
- `notification_friend_request_idx` on `(friend_request_id)` WHERE `friend_request_id IS NOT NULL`
- `notification_invitation_idx` on `(invitation_id)` WHERE `invitation_id IS NOT NULL`

**Constraints:**
- `notification_single_subject_ck` CHECK `(friend_request_id IS NULL) OR (invitation_id IS NULL)`

Source: data-model-notifications.md:24–58, 175–176

---

### `room_invitation`

**Columns:**
- `invitation_id`: uuid PRIMARY KEY
- `room_id`: uuid NOT NULL
- `inviter_user_id`: uuid NOT NULL
- `invitee_user_id`: uuid NOT NULL
- `created_at`: timestamptz NOT NULL DEFAULT now()
- `expires_at`: timestamptz NOT NULL

**Foreign Keys:**
- `room_id` → `room(room_id)` ON DELETE CASCADE
- `inviter_user_id` → `app_user(user_id)` ON DELETE CASCADE
- `invitee_user_id` → `app_user(user_id)` ON DELETE CASCADE

**Indexes:**
- `room_invitation_pair_key` UNIQUE on `(room_id, invitee_user_id)`
- `room_invitation_invitee_idx` on `(invitee_user_id)`
- `room_invitation_inviter_idx` on `(inviter_user_id)`
- `room_invitation_expiry_idx` on `(expires_at)`

**Constraints:**
- `room_invitation_self_ck` CHECK `inviter_user_id <> invitee_user_id`

Source: data-model-notifications.md:159–177

---

## Section 3 — Enumerated Types / Status Values

| Table.column | Permitted values | Source `file:line` |
|---|---|---|
| `room.visibility` | `PUBLIC`, `FRIENDS_ONLY`, `INVITE_ONLY` | data-model.md:44 |
| `room.state` | `LOBBY`, `IN_PROGRESS`, `CLOSED` | data-model.md:45 |
| `room.closed_reason` | `NO_PLAYERS_REMAINING`, `GRACE_EXPIRED_NO_HUMAN`, `ACCOUNT_DELETED`, `IDLE_TIMEOUT`, `SESSION_UNRECOVERABLE` | data-model.md:126–130 |
| `room_participant.role` | `PLAYER`, `SPECTATOR` | data-model.md:161 |
| `room_participant.leave_reason` | `LEFT`, `KICKED`, `GRACE_EXPIRED`, `EARLY_RELEASE`, `ROOM_CLOSED`, `GAME_ENDED` | data-model.md:173–174 |
| `app_user.kind` | `REGISTERED`, `GUEST` | data-model-accounts.md:33 |
| `app_user.deletion_reason` | `SELF_SERVICE`, `GUEST_EXPIRED` | data-model-accounts.md:45 |
| `user_auth_method.method` | `PASSWORD`, `GOOGLE` | data-model-accounts.md:226 |
| `user_session.revoked_reason` | `DISPLACED`, `LOGOUT`, `ACCOUNT_DELETED`, `GUEST_EXPIRED`, `KEY_ROTATED` | data-model-accounts.md:283 |
| `user_privacy_settings.history_visibility` | `PUBLIC`, `HIDDEN` | data-model-accounts.md:346 |
| `user_privacy_settings.stats_visibility` | `PUBLIC`, `HIDDEN` | data-model-accounts.md:347 |
| `user_privacy_settings.games_visibility` | `PUBLIC`, `HIDDEN` | data-model-accounts.md:348 |
| `user_privacy_settings.friends_visibility` | `PUBLIC`, `FRIENDS_ONLY`, `HIDDEN` | data-model-accounts.md:349 |
| `game.badge` | `OFFICIAL`, `VERIFIED`, `UNVERIFIED` | data-model-catalog.md:41 |
| `game_version.status` | `PENDING`, `PROCESSING`, `ACTIVE`, `FAILED`, `EXPIRED`, `SUPERSEDED`, `DISCARDED` | data-model-catalog.md:231–232 |
| `game_review.decision` | `APPROVED`, `REJECTED`, `WITHDRAWN` | data-model-catalog.md:473 |
| `notification.type` | `FRIEND_REQUEST`, `FRIEND_REQUEST_ACCEPTED`, `FRIEND_REQUEST_DECLINED`, `FRIEND_ADDED`, `ROOM_INVITATION`, `GAME_APPROVED`, `GAME_REJECTED`, `BUNDLE_VALIDATION_COMPLETE` | data-model-notifications.md:264–272 |

---

## Section 4 — Redis Keys

| Key pattern | Value type | TTL | Written by | Source `file:line` |
|---|---|---|---|---|
| `pod:{podId}:alive` | string (renewed) | 10s, renewed every 3s | each instance for itself | room-lifecycle.md:38 |
| `room:{roomId}:pod` | string (podId) | NONE STATED | claim/release scripts | room-lifecycle.md:39 |
| `room:{roomId}:epoch` | integer (incremented) | NONE STATED | claim script INCR | room-lifecycle.md:40 |
| `queue:{sessionId}` | list (dispatched events) | NONE STATED | orchestration, session queue | room-lifecycle.md:146 |
| `session:/routing:/queue:/seq:/delivered:/failcount:{sessionId}` | various (routing/queue/counters) | NONE STATED | session management | room-lifecycle.md:499 |
| `platform:sentinel` | marker | NONE STATED | sentinel writer | room-lifecycle.md:641 |

---

## Section 5 — Observations

**(a) Foreign key columns with NO explicit index:**

- `room.game_id` → `game(game_id)` (data-model.md:41)
- `room.host_user_id` → `app_user(user_id)` (data-model.md:43)
- `room_participant.team_id` → `room_team(team_id)` (data-model.md:162)
- `game_review.version_id` → `game_version(version_id)` (data-model-catalog.md:470)

**(b) Enumerated status values in CHECK constraints vs. writers:**

All enumerated values found in CHECK constraints are documented as being written by at least one documented transition:
- `room.closed_reason`: all five values named in closure-reason table (data-model.md:126–130) appear in requirements cited at those lines.
- `room_participant.leave_reason`: all six values are produced by identified lifecycle transitions (data-model.md:173–174, FR-XFER-002, FR-KICK-003, FR-HDISC-003, FR-EXPIRY-004, closure, game end).
- `user_session.revoked_reason`: all five values are written (login, logout, deletion, guest expiry, key rotation).
- `game_version.status`: all seven values are reachable per the status machine (data-model-catalog.md:§2).
- `game_review.decision`: all three values are written (approval, rejection, account-deletion withdrawal).

No enumerated value in a CHECK was found that is never written by any documented path.

**(c) Tables referenced by name in documents but not defined in this corpus:**

All tables referenced by foreign keys, in-document prose, or cross-file sections are defined:
- Every `REFERENCES` target exists in one of the 7 documents.
- All erasure cascade targets in data-model-accounts.md:§5 table (line 387–399) are defined.

No table is orphaned.

**(d) Redis keys with TTL not stated:**

- `room:{roomId}:pod` — line 39: "TTL none"
- `room:{roomId}:epoch` — line 40: "TTL none"
- `queue:{sessionId}` — line 146: no TTL information given
- `session:/routing:/queue:/seq:/delivered:/failcount:{sessionId}` — line 499: no TTL information given
- `platform:sentinel` — line 641: no TTL information given (mentioned only as a reset marker, not a keyed data structure with stated TTL)
