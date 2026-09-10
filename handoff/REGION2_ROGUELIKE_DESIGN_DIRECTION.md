# Region II Roguelike Design Direction

Status: **Design direction locked for the next Region II iteration.**  
This document captures intent and design reasoning, not a literal feature checklist.

## Context

0679 established the structural correction that Boss II belongs to Region II, the 21–40 card progression band. It currently provides a single Region II expedition-style map with three waves and a north Archive Seal leading to Hollow Curator.

That implementation is a foundation, not the final target.

The user’s suggestion of “2–3 maps, each with 2–3 waves” was an example to communicate the desired sense of travelling through multiple spaces before reaching Boss II. **Do not treat those numbers as hard requirements.** Future development should challenge and improve the example when a stronger roguelike structure is available.

## Core goal

Region II should feel like a replayable roguelike biome, not a linear mini-campaign and not a longer sequence of fixed combat waves.

The target feeling is:

> “One more run. I want to see which rooms, risks and routes appear this time.”

A successful Region II run should create meaningful choices, changing encounter rhythm, visible anticipation of Hollow Curator, and reasons to take different routes on repeat visits.

## Proposed run structure

Use a **branching route of roughly 4–7 short nodes as a tuning starting point**, not a permanent fixed count.

A node does not need to be a unique map. A run can mix rooms, sub-areas, transitions and encounter states. The important part is that the player experiences progression through the Forgotten Archive rather than standing in one arena for repeated waves.

Candidate node types:

- standard combat;
- elite encounter;
- archive event;
- reward / cache room;
- Mirror Choice;
- cursed archive room;
- healing or restoration shrine;
- shortcut;
- risky optional branch;
- Boss Gate / Archive Seal.

Do not require every run to contain every node type.

## Branching and risk/reward

Region II should regularly ask the player to choose between routes instead of moving through one mandatory chain.

Examples:

- safer route with lower rewards;
- elite route with increased Scrap/Shiny potential;
- Mirror Route with a strong benefit paired with an enemy modifier;
- optional extra room before Boss II for more reward at increased risk;
- shortcut that reaches the boss earlier but sacrifices potential run power.

The exact rewards and probabilities should be tuned after playtesting. The principle is more important than any initial number.

## Region II identity: the Archive watches the player

Forgotten Archive must not be Region I with new tiles.

Its signature system should be **observation / recording / reflection**.

Hollow Curator is conceptually present throughout the run. The Archive observes how the player fights, records notable behavior, and later reflects parts of that behavior back at the player.

Potential observations include:

- repeated melee pressure;
- ranged-heavy play;
- critical-hit-focused play;
- frequent healing/support;
- repeated use of a dominant Cardcha effect;
- aggressive or defensive route choices.

The implementation should begin simple and deterministic enough to debug. It does not need a complicated machine-learning-style model. A small set of clearly readable combat tendencies is preferable to an opaque system.

## Hollow Curator foreshadowing

Boss II should be felt before the final arena.

Possible techniques:

- brief Hollow Curator silhouette behind a mirror or ruined shelf;
- archive pages reacting to recent combat behavior;
- room modifiers introduced as if the Curator is editing the Archive;
- mirrored copies or echoes of an earlier encounter;
- short text/VFX cues indicating that an action was “recorded”;
- environmental changes near the end of the run.

Avoid excessive floating text. Environmental and animation communication is preferred.

## Signature boss concept: Curator Records You

Working design concept:

**Curator Records You**

During the Region II run, the system records a small number of strong or repeated player tendencies. In Hollow Curator phases 2/3, the boss converts those records into attack patterns, summons, resistances, arena changes or mirror echoes.

Examples, subject to iteration:

- melee-heavy run → close-range punish / reflected melee zones;
- ranged-heavy run → mirror projectiles or line denial;
- crit-heavy run → short Curator critical echo window;
- support/healing-heavy run → Vita-like archive recovery or healing denial;
- repeated dominant effect → a mirrored version appears during the boss fight.

This should be readable and fair. The player should understand what was copied and have a chance to respond.

Do not make the system invalidate a build simply because it is effective. The goal is adaptation and surprise, not hard countering the player.

## Boss Gate philosophy

Do not make the Archive Seal merely the end of a fixed hallway.

After a suitable minimum run depth, a Boss Gate may become available while optional nodes remain.

This enables a roguelike decision:

- fight Hollow Curator now;
- continue deeper for more run power / rewards;
- accept additional risk or a curse to weaken one boss mechanic;
- take an elite branch before committing to the boss.

Exact unlock timing remains a tuning decision.

## Hollow Curator visual/animation direction

The current four-state visual is insufficient as a final milestone-boss presentation.

However, the solution is **not simply “add more frames.”** Animation should exist because boss behavior needs it.

Target animation/state families should support gameplay such as:

- idle / hover / page movement;
- movement or drift;
- cast wind-up;
- card/page volley;
- summon / mirror creation;
- record / observe state;
- reflection / adaptation state;
- hit / stagger;
- phase transition;
- defeat / archive collapse.

The final frame count is not specified here. Build the animation set around the actual encounter state machine and telegraphs.

## Encounter presentation principles

Hollow Curator should have memorable stage presence without oversized blurry sprites.

Keep these rules:

- native-size authored pixel art;
- actor-owned draw depth for the boss and combat actors;
- physical environment belongs in TMX/native map layers;
- `RenderedWorld` is for non-physical VFX only;
- avoid giant floating labels;
- telegraphs should be readable before damage lands;
- boss phases should look different, not only change numbers in code;
- visible sprite, hitbox and gameplay actor must remain aligned.

## What not to do

Do **not** interpret this document as requiring:

- exactly 2–3 maps;
- exactly 2–3 waves per map;
- exactly 4–7 nodes forever;
- every room being combat;
- three fixed maps named A/B/C;
- a completely linear Region II route;
- more boss animation frames with no gameplay purpose.

Do not blindly implement a user example when a better solution serves the stated goal. Treat examples as design prompts and apply critical design judgment.

## Relationship to 0679

0679 remains the current technical source-of-truth build and provides:

- Region II ownership of the 21–40 card band;
- 250g Airship route foundation;
- Region II authored enemy identities;
- physical Archive Seal → Boss II route;
- Hollow Curator as the Region II milestone boss;
- rendering-depth contracts.

The next Region II development pass should evolve the current single-map/three-wave expedition into the roguelike structure described here while preserving stable progression, save schema and accepted systems unless concrete testing requires a change.

## Suggested next-pass scope

Working label only, not locked version number:

**Region II Roguelike Route + Hollow Curator Encounter Auth Pass**

Recommended development order:

1. Build reusable branching-node/run-state architecture for Region II.
2. Add room/event variety and route choices.
3. Add observation/recording data for the run.
4. Connect optional Boss Gate timing and risk/reward choices.
5. Rebuild Hollow Curator behavior and animation around the recorded-run mechanic.
6. Playtest pacing, clarity, reward balance and replay value before expanding Region III/IV with the same philosophy.

## Acceptance question

The primary acceptance test is not “did all planned rooms spawn?”

It is:

> **Does a second Region II run create a genuinely different tactical/story rhythm and make the player curious about a third run?**

If the answer is no, the roguelike layer is not finished yet.
