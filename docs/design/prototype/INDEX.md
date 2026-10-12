# Prototype reference captures

Captures of the approved clickable prototype — the owner-approved layout of every screen
([ADR-0017](../../decisions/0017-turnbase-visual-identity.md) §5). A screen of the platform is done
when its capture of the same state matches the one here, except for the deviations listed in §5.

**Naming:** `<screen>.<desktop|mobile>.<light|dark>.webp`. Desktop is 1440×900, mobile 400×860, both
with reduced motion, so the sliding indicators and panes are captured at rest. The prototype was
signed in as the sample player *Nova*; the "Prototype · sample data" dock at the bottom right is
prototype-only and is not part of the target.

| Screen | Files |
|---|---|
| Landing, five snap screens | `landing.*`, `landing-share.*`, `landing-library.*`, `landing-build.*`, `landing-join.*` |
| Log in / Register | `login.*`, `register.*` |
| Games catalog | `games.*` |
| Game detail | `game-detail.*` |
| Rooms list | `rooms.*` |
| Join with a code | `join-code.*` |
| Room: lobby, in game, result | `room-lobby.*`, `room-game.*`, `room-results.*` |
| Profile: Stats, History | `profile-stats.*`, `profile-history.*` |
| Friends: All, Requests | `friends.*`, `friends-requests.*` |
| Settings: Account, Appearance | `settings-account.*`, `settings-appearance.*` |
| Quick tour (first step) | `tour.*` |

Captures of the landing's lower screens show the page scrolled to that screen; the prototype's
bottom-right dock and the "The library"-style dot rail labels are as they appeared (the rail is part of the target).
