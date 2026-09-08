# Alpha28 0669 - Boss Visual Overhaul + Totem Feedback + ChaCha Form Pass

Status: QUEUED AFTER 0668C IN-GAME ACCEPTANCE.
Do not create the 0669 implementation branch from 0668B. Fork it from the accepted 0668C source.

## Target

Bring Boss I presentation substantially closer to the approved Cardcha Boss Concepts instead of continuing with enlarged/prototype-looking sprites.

The concept target for Boss I is:
- Verdant Guardian as a massive ancient forest titan;
- organic roots / bark / vines / antler-like crown silhouette;
- a readable luminous Verdant Core;
- a polished living-ruins / ancient-grove arena;
- ChaCha Guardian Rabbit as an unmistakable transformed boss form, not a normal follower with minor effects.

## 0669 scope

### 1. Verdant Guardian native-size visual overhaul
- stop relying on a small authored frame enlarged to create boss scale;
- author/render the boss at an appropriate native pixel footprint for its intended in-game size;
- preserve a strong readable silhouette at actual Stardew camera scale;
- make roots, shoulder mass, crown/antlers, vines and glowing core legible;
- keep boss collision/gameplay proxy separate from presentation;
- preserve current combat timings and balance unless a later explicit balance pass is requested.

Required visual states:
- idle / breathing-root sway;
- intro / awaken;
- attack windups that communicate the existing attack state machine;
- hurt reaction;
- totem-final stagger reaction;
- phase transition;
- defeat/core release.

### 2. Totem presentation polish
0668C owns functional clarity. 0669 may improve art without changing the accepted mechanics:
- stronger authored intact / damaged / critical / broken states;
- arena placement must visually read as four linked ward objects around the Guardian;
- barrier connection can be shown subtly through particles/runes/roots, not permanent noisy text.

### 3. ChaCha Guardian Rabbit form overhaul
- dedicated Guardian Rabbit sprite/animation set;
- clearly rabbit-like, never cat-like;
- visibly larger/more powerful than normal follower ChaCha without becoming visually absurd;
- forest/guardian identity matching Boss I concept;
- clear transformation entrance and expiration feedback;
- preserve Boss Form duration at 10 seconds and Boss Energy gain scale at 1/3.

### 4. Boss arena art pass
- replace the current flat/placeholder feeling with a Stardew-readable ancient grove / living ruins arena;
- improve ground shape, paths, foliage, ruined stone, shrine/core focal hierarchy and depth;
- avoid repetitive staircase/band geometry;
- the four Totems must feel intentionally integrated into the arena;
- maintain collision, combat space and retreat route.

### 5. Region I enemy/environment native-size follow-up
If in-game acceptance still confirms Briarling / Leaf Wisp look blown-up:
- replace render scaling with native-size authored sprites;
- strengthen Region I room dressing and organic map shapes;
- keep Hunt Run routing/progression unchanged.

## Frozen contracts

Do not change without explicit user instruction:
- save schema 19;
- 76 active normal cards / 80 source entries with four legacy mythic exclusions;
- Boss I 0665 balance including 1600 HP;
- Totem mechanics accepted from 0668C;
- Boss Form 10 seconds;
- Boss Energy gain scale 1/3;
- Airship route/unlock/fare contracts;
- controller semantic mapping;
- MiMi birthday Spring 17;
- MiMi final boss milestone at 80 cards;
- ChaCha rabbit identity;
- strict TMX CSV validation.

## Acceptance bar

0669 is not accepted because the assets exist or CI compiles. It passes only when actual in-game screenshots at normal Stardew camera scale show:
- Verdant Guardian immediately reads as the concept's ancient forest titan;
- ChaCha's Guardian Rabbit immediately reads as a transformed boss form;
- the arena looks authored rather than generated/placeholder;
- visual effects reinforce mechanics without obscuring combat;
- no regression to 0668C interaction clarity.
