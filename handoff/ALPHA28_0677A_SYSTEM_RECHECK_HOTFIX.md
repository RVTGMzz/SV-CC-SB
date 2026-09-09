# Cardcha alpha28 — 0677A System Recheck + Airship Lifecycle Hotfix

Build: `0.3.0-alpha.28.0.4.14.4.5.12.45.3.1`
Branch: `cardcha-alpha28-0677a-system-recheck-hotfix`

## Recheck scope
- startup/Harmony targets
- Airship Bridge/Dock native decor lifecycle and interaction lanes
- 40/60/80 milestone route
- Region III/IV wave/extraction loop
- render-depth contract
- map CSV and package/version consistency

## Concrete fixes found during recheck
1. Native Airship furniture was being created from `RenderedWorld`; it now initializes on save/day/warp lifecycle instead.
2. Four large furniture origins sat too close to Engine/Navigation/Hull/Reactor interaction sockets; they were moved outside a conservative safety moat.
3. Optional held-table decoration failure could discard an otherwise valid base furniture item; held-decor failure is now non-fatal and logged.
4. `cardcha_airship_status` now reports Cardcha-owned native furniture counts and Lost & Found chest presence.

## Known remaining visual debt
Boss I body/summons/Totems and Boss II-IV authored bodies still use legacy post-world actor drawing. This is tracked by the repository render-depth audit and is NOT accepted yet.

No balance, card progression, fare, save schema, MiMi art, ChaCha mechanics, boss thresholds, or expedition rewards changed.
