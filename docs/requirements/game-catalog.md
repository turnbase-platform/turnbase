# Game Catalog & Discovery Requirements

## Related API Specifications

- [rest-conventions.md](../specs/api-design/rest-conventions.md) — HTTP methods, status codes, public endpoint authentication rules
- [pagination-filtering-sorting.md](../specs/api-design/pagination-filtering-sorting.md) — Pagination, filtering, and sorting conventions (implements FR-CAT-004–008, NFR-SCAL-001)
- [file-uploads.md](../specs/api-design/file-uploads.md) — Pre-signed URL upload flow for game bundles (implements FR-GAME-001)
- [input-validation.md](../specs/api-design/input-validation.md) — the info document's Markdown renderer and allow-list (implements FR-GDET-004)

## Stakeholders

| Role | Description |
|------|-------------|
| Unauthenticated Visitor | Can browse the catalog and view game detail pages; cannot create rooms |
| Guest User | Full catalog access; can create rooms from catalog and detail pages |
| Registered User | Full catalog access; can upload, manage, and publish their own games |
| Game Developer | A registered user who has uploaded one or more games to the platform |
| Administrator | Internal operator; can set Official and Verified status on any game — no platform UI |
| Platform (System) | Indexes published games, enforces visibility rules, manages versioning lifecycle |

---

## Functional Requirements

### Catalog Listing

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-CAT-001 | Game catalog page | The platform must provide a publicly accessible game catalog at `/games` listing all published (public) games. | Must |
| FR-CAT-002 | Catalog columns | Each row in the catalog must display: game name, author username, min players, max players (both derived from the game's team templates and stored server-side), AI support (flag), spectator support (flag), current version, creation date, last updated date, and Official/Verified badge where applicable. | Must |
| FR-CAT-003 | Row expansion | Clicking a catalog row expands it inline to reveal the game's short description. Clicking again collapses it. Only one row may be expanded at a time. | Should |
| FR-CAT-004 | Pagination | The catalog is paginated with a configurable page size; the default is 25 games per page. Navigation controls provide: first page, previous page, next page, and last page. The current page number and total page count are displayed. | Must |
| FR-CAT-005 | Text search | A single search input filters the catalog by matching the query against game name, author username, and tags. Matching is case-insensitive substring matching. The filter is applied server-side. | Must |
| FR-CAT-006 | Player count filter | The catalog provides numeric min/max player count filter inputs. When set, only games whose player range overlaps the specified range are shown. | Should |
| FR-CAT-007 | Column sorting | The catalog can be sorted by any of the following columns, ascending or descending: name, author, min players, max players, version, creation date, last updated date. Default sort is by creation date descending. | Must |
| FR-CAT-008 | Create Room action | Each catalog row provides a "Create Room" button. This button is hidden for Unauthenticated Visitors and visible for Guest and Registered users, consistent with VW-CAT-003. | Must |
| FR-CAT-009 | Game detail link | Each catalog row links to the game's detail page at `/games/:id`. | Must |
| FR-CAT-010 | Official/Verified badge | Games with Official or Verified status display a visible badge in the catalog row. The two statuses are visually distinct. | Must |

---

### Game Detail Page

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-GDET-001 | Game detail page | The platform must provide a publicly accessible game detail page at `/games/:id` for any published (public) game. | Must |
| FR-GDET-002 | Game metadata display | The detail page must display: title, author username, current version, min players, max players (both derived from the game's team templates and stored server-side), AI support flag, spectator support flag, tags, creation date, last updated date, and Official/Verified badge. | Must |
| FR-GDET-003 | Info section | The detail page must include an info section. If the game provides a Markdown document, it is rendered there. If no Markdown document is provided, the short description is displayed instead. | Must |
| FR-GDET-004 | Markdown sanitization | The rendered Markdown document must be sanitized to allow only informational content (headings, paragraphs, lists, code blocks, images, links). Executable content, iframes, and script injection vectors must be stripped. | Must |
| FR-GDET-005 | Active player count | The detail page must display the total number of players currently in active rooms for this game. This count is loaded once per page load and does not update in real-time. | Should |
| FR-GDET-006 | Create Room action | The detail page provides a "Create Room" button, hidden for Unauthenticated Visitors and enabled for Guest and Registered users, consistent with VW-GDET-003. | Must |
| FR-GDET-007 | Deleted game page | When a soft-deleted game's detail page is accessed by anyone, the platform must display a "this game no longer exists" message (not a generic 404). | Must |
| FR-GDET-008 | Private game page | When an Unauthenticated Visitor or non-owner user attempts to access the detail page of a private (unlisted) game, the platform returns a 404 response. | Must |
| FR-GDET-009 | Owner private game access | The owner of a private game can access its detail page and create rooms from it. | Must |

---

### Game Management

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-GAME-001 | Upload new game | A Registered User can upload a new game from their profile page. The upload form and technical upload mechanism are deferred to the Game SDK specification. | Must |
| FR-GAME-002 | Required metadata | Every game must have the following metadata at creation and update: title, short description (max 100 characters), team templates (see game-rooms.md FR-TEAM-001 — min/max player counts are derived from these), AI (bot) support (boolean), spectator role support (boolean), and at least one tag. | Must |
| FR-GAME-003 | Tags | A game may have up to 10 tags. Each tag is free-form text, max 24 characters. Tags are set by the game developer. | Must |
| FR-GAME-004 | Optional Markdown info doc | A game may optionally provide a Markdown document as its info/rules page. This field is not required. | Should |
| FR-GAME-005 | Default visibility | Newly uploaded games are private (unlisted) by default. | Must |
| FR-GAME-006 | Publish / delist | The owner can toggle a game between public (visible in catalog) and private (unlisted). Delisting does not affect active or future rooms created by the owner. | Must |
| FR-GAME-007 | Private room creation | When a game is private, only the owner can create rooms for it. Players who are invited to or join such a room may play the game regardless of its private status. | Must |
| FR-GAME-008 | Update game metadata | The owner can update title, short description, and the Markdown info doc at any time without uploading a new version. All other metadata (team templates, AI support, spectator support, tags) is part of the game implementation and can only change via a new version upload. | Must |
| FR-GAME-009 | Version format | Game versions follow the `x.y.z` format (numeric segments only). The current version is set by the developer on each upload. Each new version must be strictly higher than the current one, with segments compared as integers left to right (major, then minor, then patch) — e.g. `1.10.0 > 1.9.0`. The platform rejects uploads where the submitted version is equal to or lower than the current active version. | Must |
| FR-GAME-010 | Single active version | Only one version of a game is active at a time. When a new version is uploaded, it becomes the active version immediately. All new rooms use the active version. | Must |
| FR-GAME-011 | Old version lifecycle | The previous version is retained as long as any rooms are actively using it. Once all rooms on the previous version have ended, that version is discarded. | Must |
| FR-GAME-012 | Delete game | The owner can delete a game. Deletion is a soft-delete: the game record is retained to preserve game history entries but is no longer accessible via the catalog or detail page. | Must |
| FR-GAME-013 | Delete with active rooms | Deletion follows the same lifecycle as a version change: the game continues to run in any active rooms until those rooms end. No new rooms can be created after deletion. | Must |
| FR-GAME-014 | Verified status reset | When a game owner uploads a new version, the game's Verified status is automatically cleared. Re-verification requires a new administrative action. | Must |

---

### Profile — Uploaded Games

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-UPROF-001 | Uploaded games tab | The user profile page must include a section or tab listing the user's uploaded games. | Must |
| FR-UPROF-002 | Own profile view | When viewing their own profile, a Registered User sees all their uploaded games (both public and private), an upload button, and management actions (edit, delist/publish, delete) per game. | Must |
| FR-UPROF-003 | Other user profile view | When viewing another user's profile, only that user's public games are shown. If they have no public games, the section is visible but shows an empty state message. | Must |
| FR-UPROF-004 | Profile game link | Each game in the uploaded games section links to that game's detail page. | Must |

---

## Non-Functional Requirements

| ID | Category | Description | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-PERF-001 | Performance | Catalog search and filter queries must be processed server-side and return results within an acceptable response time. | p95 < 300ms | Must |
| NFR-PERF-002 | Performance | The active player count on the game detail page is fetched once per page load; no real-time update mechanism is required. | p95 < 300ms | Must |
| NFR-SEC-001 | Security | Markdown documents submitted by game developers must be sanitized before rendering to prevent XSS and injection attacks. Only informational HTML elements are permitted. | 100% of rendered Markdown | Must |
| NFR-SEC-002 | Security | Private game detail pages must return a 404 to non-owners, indistinguishable from a nonexistent game, to prevent enumeration of private games. | 100% of unauthorized requests | Must |
| NFR-USAB-001 | Usability | When a soft-deleted game is accessed, the platform displays a clear "this game no longer exists" message rather than a generic error page. | — | Must |
| NFR-USAB-002 | Usability | The Official and Verified badges must be visually distinct from each other and clearly identifiable in both the catalog listing and the game detail page. | — | Should |
| NFR-SCAL-001 | Scalability | The catalog must remain performant as the number of published games grows. Search and filter queries must be backed by appropriate database indexing on name, author, tags, and player counts. | — | Must |

---

## Constraints

| ID | Description |
|----|-------------|
| CON-001 | Frontend must be implemented in React 19 with TypeScript. |
| CON-002 | All catalog filtering, searching, and sorting is server-side; client-side filtering is not acceptable. |
| CON-003 | Official and Verified status can only be set by an administrator via internal tooling — no platform UI is provided for this. |
| CON-004 | The game upload form and technical upload mechanism (JAR / JS bundle structure) are not defined here; they are deferred to the Game SDK specification. |
| CON-005 | Version format is strictly `x.y.z` with numeric segments only. |

---

## Out of Scope

- Game upload form and technical upload/delivery mechanism (Game SDK spec)
- Per-game statistics content beyond the active player count (specified in per-game-statistics.md)
- Administrator interface for managing Official/Verified status (internal tooling)
- Rating and review system
- Real-time catalog updates (e.g. live player counts in the list)
- Tag taxonomy management (tags are free-form, no admin-managed list)

---

## Open Questions

- None outstanding — all major areas resolved during clarification.
