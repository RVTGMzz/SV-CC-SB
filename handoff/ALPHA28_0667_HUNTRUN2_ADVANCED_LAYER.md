# Alpha28 0667 - Hunt Run 2.0 Advanced Layer

Build: `0.3.0-alpha.28.0.4.14.4.5.12.34`
Branch: `cardcha-alpha28-0667-huntrun2-advanced-layer`
Status: implementation candidate; in-game acceptance pending for 0660-0667.

## Elite Affixes
- Thorn Aura: proximity pulse, 3 damage, 1.2s cooldown.
- Swift: +2 Speed.
- Regrowth: heals every second.
- Bulwark: +60% HP, slightly slower.
- Infested: +2 escorts.
- Resonant: tougher Elite; escorts gain +15% HP and +1 Speed.
- Affixes are deterministic per run seed/node and are shown above the Elite.

## Daily Mutation
One deterministic Region I mutation per save-day, shared by every run that day:
- Calm Grove: -10% enemy HP, slightly fewer enemies.
- Briar Bloom: Elite/Root Nest +20% HP, dangerous nodes +1 route Scrap.
- Moonlit Grove: faster Bats, 25% Shiny chance per clear, more rare rooms.
- Overgrown Day: +15% enemy HP, +1 route Scrap per clear.
- Chaotic Resonance: +10% HP/+1 Speed, more rare rooms, extra boon milestones at nodes 4 and 7.

## Advanced Rare Rooms
Starting from node 4, route rolls can create:
- Lost Cache: no combat; +4 Scrap +1 Shiny.
- Moonwell: no combat; heal 30% Max HP and bank current route rewards.
- Ancient Echo: affixed Elite; +3 Scrap +1 Shiny.
Base rare chance is 11%, Moonlit 16%, Chaotic 18%. Route type weights which rare room appears.

## Preserved
- Hunt Run remains 7-10 nodes with checkpoints 3/6, Boss branch from node 7, Extract, 1-of-3 boons.
- Monsters still feed Scrap pipeline; no finished-card drops.
- Save schema 19 unchanged.
- Boss I 0660-0665, Verdant Core, Guardian Rabbit, Airship, MiMi/stair/profile/CC, 76 active-card audit unchanged.
