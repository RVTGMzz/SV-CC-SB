# Cardcha .5.6.1 Readability + Progression + MiMi Style

Target version: `0.3.0-alpha.28.0.4.14.4.5.6.1`

User-requested acceptance scope:

1. Forest Arcane Gate moves to a canonical Wizard-side meadow anchor instead of roaming unrelated Forest sectors. It resolves relative to the live WizardHouse warp for map-overhaul compatibility, searches only a tiny local pocket, keeps 160px interaction, and never edits Forest collision.
2. Gate visual is raised above the approach tile and return landing is placed in front, so the post-world portal art should no longer sit across the farmer's body during normal use.
3. Persistent ChaCha Boss Energy rectangular HUD is removed. Boss Energy charging, READY announcement, aura, controller chord, Left Shift+A, 10s Boss Form, and 1/3 gain pacing remain.
4. Cardcha Wizard-door bypass is valid only on MiMi's explicitly offered appointment day. Picking up Scrap/cardboard alone cannot create a Cardcha WizardHouse bypass or start the meetup. Missed appointment still uses the existing forced doorstep fallback.
5. Remove post-world bridge bars/cables and central mana lanes that visually cut through the farmer. Fill the outer boarding room using side-wall props only.
6. The Sky Dock panel is explicitly labeled and described as an informational Route Status Board; departure remains on the Airship Bridge helm.
7. MiMi portrait family receives a conservative Stardewization pass: stronger dark silhouette stroke, restricted palette, pixel clusters, same dimensions/expressions. `mimi_walk.png` is locked and must remain byte-identical.
8. Airship upgrade atlas receives a stronger dark outline so hardware reads closer to Stardew's object language.

Out of scope:
- permanent gameplay bonuses for Engine/Navigation/Hull/Reactor;
- MiMi attic rebuild;
- changing `mimi_walk.png`;
- Forest collision/path edits;
- main branch promotion.
