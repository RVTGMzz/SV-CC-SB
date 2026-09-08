# Alpha28 0662 - Guardian Rabbit Boss Form

Build: `0.3.0-alpha.28.0.4.14.4.5.12.29`
Branch: `cardcha-alpha28-0662-guardian-rabbit-boss-form`
Status: implementation candidate, in-game acceptance pending. 0660 and 0661 visual/gameplay acceptance are also still pending because the user continued before testing.

## Guardian Rabbit
- Boss I / Verdant resonance now unlocks ChaCha's first actual named Boss Form: `guardian_rabbit`.
- Unlock derives from existing schema-19 Boss I state (`Region1BossDefeated` or `verdant_core` in `BossCardsUnlocked`). No save-schema migration.
- The generic enlarged ChaCha placeholder is replaced by a dedicated 4-direction x 4-frame Guardian Rabbit sprite sheet.
- Design canon: short, round rabbit body, long rabbit ears, leaf mantle, bark shoulder plates, glowing Verdant core. It is not humanoid and not cat-like.
- Active draw scale is 0.82 native NPC scale.

## Runtime
- Boss Form duration stays locked at exactly 10 seconds.
- Activation still spends exactly 100 Boss Energy.
- Boss Energy gain scale stays locked at x1/3 and gain is suppressed while Boss Form is active, exactly as before.
- Guardian Rabbit emits Root Pulse every 2 seconds while active.
- Test pulse damage: 18 per target, radius 176 px. Balance is explicitly provisional for the later balance pass.
- Root Pulse uses normal Monster.takeDamage routing so Cardcha death/drop observation remains compatible.
- Active aura switches to Verdant green and each Root Pulse has a visible expanding leaf/root bloom.

## Input / debug
- Controller activation remains Confirm+Deselect.
- Keyboard activation remains Left Shift+A.
- `cardcha_chacha_boss_ready` now grants only a runtime debug unlock and primes 100 Energy.
- `cardcha_guardian_rabbit_test` runtime-unlocks and immediately activates Guardian Rabbit for 10 seconds without changing save progression.
- `cardcha_chacha_boss_status` reports unlock, active form, pulse count/hits and locked Energy telemetry.

## Locked systems preserved
Save schema 19, 20/40/60/80 milestones, 76 active normal-card audit / 80 stored base IDs, Boss Form 10 sec, Boss Energy x1/3, 0659 MiMi stair behavior, MiMi native profile + CC continuity, Region I Hunt Run 4-of-6, 0660 Verdant Colossus, 0661 Verdant Core Boss Card, Airship route/upgrades, controller mapping and Forest gate are unchanged.
