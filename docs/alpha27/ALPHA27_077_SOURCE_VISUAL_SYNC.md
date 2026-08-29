# Alpha.27.0.7.7 source visual synchronization

The 0.7.7 acceptance package contains the user-approved visual versions of `chacha_follow.png`, `chacha_machine.png`, `card_icons.png`, and `chacha_portrait.png`. The active branch still contains older pixels for those four files, while `mimi_walk.png` and `mimi_social_mugshot.png` already match the approved acceptance package.

Locked rule: never modify `mimi_walk.png` unless explicitly requested by the user. The Social mugshot stays a dedicated separate asset.

Until the four stale source visuals are synchronized, the canonical guard is expected to fail closed. This is deliberate: CI must not silently replace or reinterpret approved art.
