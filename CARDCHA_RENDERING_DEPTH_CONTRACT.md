# Cardcha Rendering Depth Contract

Status: **NON-NEGOTIABLE REPOSITORY CONTRACT**

This document exists because Cardcha repeatedly shipped visual regressions where terrain, furniture, gates, boss props, or authored actors were painted after Stardew had already drawn the Farmer/NPC layer.

The root problem is not an individual offset. It is rendering ownership.

## Core rule

**No physical Cardcha world object may be rendered as a `Display.RenderedWorld` overlay.**

`RenderedWorld` is reserved for transient VFX and non-physical cues only.

A `layerDepth` value passed to a draw call inside `RenderedWorld` does not put that draw back into Stardew's already-completed world sorting pass.

## Required ownership matrix

| Visual | Required owner | Forbidden owner |
|---|---|---|
| floor, path, grass, puddle, terrain | TMX `Back` / map terrain | `RenderedWorld` |
| tree, rock, bush, crystal, ruin | TMX / terrain feature / native object | `RenderedWorld` |
| furniture, chest, crate, table, machine | Stardew `Furniture` / `Object` / TMX | `RenderedWorld` |
| gate, arch, wall, railing, bridge | TMX `Buildings`/`Front` or native world entity | `RenderedWorld` |
| boss body | boss proxy's actor draw slot | `RenderedWorld` |
| summon / enemy body | `Monster.draw` / actor draw slot | `RenderedWorld` |
| destructible Totem / ward | same actor/hitbox draw slot | `RenderedWorld` |
| ground telegraph | map/pre-world or translucent VFX with actor-safe rules | opaque physical overlay |
| particles, sparks, aura | `RenderedWorld` allowed | n/a |
| HUD/status | HUD renderer | world object overlay |

## Actor occlusion acceptance

For every physical visual added or changed, test all of the following:

1. Farmer stands immediately **south/in front** of it.
2. Farmer stands immediately **north/behind** it.
3. Farmer stands on the **same interaction tile** where possible.
4. ChaCha or another NPC/companion passes beside it.
5. Visual footprint matches collision/interaction footprint.
6. No floor/decor pixel paints over actor feet/body.
7. No tall prop stays permanently above every actor.
8. No authored actor is double-rendered with its vanilla proxy.

A screenshot failure on any item means visual acceptance = **FAIL**, even when CI compiles.

## Anchor acceptance

Gameplay and art must derive from one source of truth.

- gate art => exact gate interaction tile;
- Totem art => exact damageable proxy position;
- boss art => exact boss proxy position;
- extraction cue => exact extraction tile;
- route marker => exact route action tile.

Do not create an independent magic coordinate for a visual copy of an existing gameplay object.

## Current audit matrix

Audit branch: `cardcha-alpha28-0676b-region-layering-extraction-hotfix`

### SAFE / correct ownership

- **MiMi Attic furniture**: real Stardew `Furniture`; native draw order/collision.
- **WizardHouse MiMi stairs**: installed into TMX `Buildings`; no post-world stair overlay.
- **ChaCha Boss Energy/Form aura**: transient VFX only; no physical prop.
- **Verdant Core world icon**: transient status indicator only; not a physical object.

### CONFIRMED UNSAFE DEBT - must be removed from post-world physical rendering

- `AirshipInteriorStardewRenderer.DrawDeckStardewDecor`
- `AirshipInteriorStardewRenderer.DrawDockStardewDecor`
- physical sprite body in `AirshipInteriorStardewRenderer.DrawUpgradeStations`
- `AirshipFoundationService.DrawSkyDock` gate sprite when invoked from `OnRenderedWorld`
- physical/floor portions of `AirshipFoundationService.DrawSkyDockInteriorDetails`
- physical/floor portions of `AirshipFoundationService.DrawDeckDetails`
- `AirshipFoundationService.DrawRegion1Details` physical structures
- `Region1StardewDecorRenderer.Draw`
- Verdant Guardian boss body in `VerdantGuardianVisualService.OnRenderedWorld`
- Briarling/Leaf Wisp bodies in `VerdantGuardianSummonVisualService.OnRenderedWorld`
- Verdant Totem/obelisk bodies in `VerdantGuardianArenaPolishService.DrawObelisks`
- Boss II/III/IV actor bodies drawn from `MilestoneBossService.OnRenderedWorld`
- Region III/IV authored enemy bodies and terrain overlays from the legacy `RegionExpeditionService.OnRenderedWorld` path (0676B migration in progress)

### ALLOWED WITH VFX-ONLY RESTRICTION

The following may remain in `RenderedWorld` only for translucent/temporary effects, not solid world props:

- combat telegraphs;
- particles/motes;
- short-lived impact flashes;
- ChaCha aura/pulse;
- Boss Card status icon;
- small extraction/route cue that hides when an actor overlaps it.

## 0676B migration policy

0676B is a depth-correctness hotfix, not merely a coordinate hotfix.

During migration:

- disabling an unsafe fake physical overlay is preferred over shipping another overlay that covers actors;
- static decor must later be rebuilt into TMX or native Furniture/Object entities;
- authored combat bodies must move to their actor draw slots;
- CI success is not visual acceptance.

## Future development rule

Any PR/build that introduces a new physical prop through `RenderedWorld` is invalid by repository policy, even if it looks correct in one screenshot.
