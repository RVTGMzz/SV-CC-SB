# Alpha28 0660 - Verdant Guardian Visual Complete + Colossus Pass

Build: `0.3.0-alpha.28.0.4.14.4.5.12.27`
Branch: `cardcha-alpha28-0660-verdant-visual-complete-colossus`
Status: implementation candidate, in-game acceptance pending.

## Scope
- Green Slime gameplay proxy is suppressed at draw time but remains HP/hitbox authority.
- Verdant Guardian display scale is 8x, exactly 2x the prior 4x prototype scale.
- Existing authored idle/intro/swipe/root sheets receive a darker, broader Colossus art-direction pass.
- Added summon, charge prep/loop/end, vine, slam, phase shift, hurt and defeat sheets.
- Added root warning/erupt, vine trap, slam warning/shockwave, leaf burst, phase pulse and core-release FX.
- Phase 2/3 receive progressively stronger glow/aura presentation.
- Death now has a 2.2s visual sequence before first-clear/rematch rewards fire.
- Boss knockback trajectory is zeroed and HeavyAnchor rejects external shove/pin movement; Cardcha-owned Charge movement remains authoritative.

## Locked systems preserved
Save schema 19, 20/40/60/80 milestones, 76/76 card audit, Boss Form 10 sec, Boss Energy 1/3, Forest gate, Airship routes/upgrades, MiMi profile/stair 0659 behavior, controller mapping, Hunt Run 4-of-6, and Region I Boss Gate threshold are unchanged.

## Acceptance pending
Verify in game: x2 size feels correct, proxy never flashes, boss cannot be team-pushed into walls, all attack states have distinct animation, phase escalation reads clearly, and rewards wait until the defeat/core-release sequence completes.
