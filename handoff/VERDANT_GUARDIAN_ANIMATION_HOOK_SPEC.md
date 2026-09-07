# Verdant Guardian Animation Hook Spec

Status: **CODE-READY VISUAL PIPELINE SPEC**
Branch: `cardcha-alpha28-0651-verdant-animation-hook`
Parent gameplay build: `0.3.0-alpha.28.0.4.14.4.5.12.18`

This spec connects the approved Verdant Guardian 64x64 animation sheets to the existing Boss I state machine without changing combat balance.

## Core rule
The existing `VerdantGuardianBossService` state machine remains authoritative for gameplay timing, damage, cooldowns, phase thresholds and rewards.

Animation is presentation-only in the first integration pass. Replacing art or frame counts must not change when damage occurs.

Do not bind damage directly to PNG frame count until the visuals are accepted in-game.

## Renderer architecture

Add a dedicated runtime component:

`VerdantGuardianAnimationController`

Responsibilities:
- map `VerdantGuardianState` to a visual clip;
- lazy-load approved boss animation textures;
- advance frames from elapsed state time;
- draw the boss body using the proxy monster's world position;
- draw the core glow overlay and future phase overlays;
- expose diagnostics/fallback state;
- never mutate SaveData or combat logic.

The existing GreenSlime proxy remains the combat actor for:
- Monster damage pipeline;
- player weapon targeting;
- movement/collision;
- HP / death detection;
- Cardcha combat hooks.

The vanilla proxy body must be hidden only for monsters carrying:
`Ronvotri.Cardcha/VerdantGuardian`

Recommended implementation: a narrow Harmony prefix on `Monster.draw(SpriteBatch)` which returns false only for the marked Verdant Guardian and delegates custom draw to the animation controller. Never suppress drawing for unrelated monsters.

## Frame contract

All boss body source frames:
- frame width: `64`
- frame height: `64`
- source sheet orientation: horizontal strip
- transparent background
- source feet anchor: `(32,58)`
- initial world scale: `4f`

At scale 4, the visual occupies up to ~256x256 screen pixels while the proxy remains the gameplay collision/damage actor. Hitbox tuning is a separate acceptance step.

## Clip model

Recommended code model:

```csharp
internal sealed record VerdantGuardianClip(
    string Id,
    string AssetPath,
    int FrameCount,
    int FrameWidth,
    int FrameHeight,
    int FrameMs,
    bool Loop,
    Point FeetAnchor
);
```

Runtime animator fields:

```csharp
private string CurrentClipId = "idle";
private long ClipStartedAtMs;
private int CurrentFrame;
private bool ClipLoadFailed;
private readonly Dictionary<string, Texture2D> Textures = new();
```

Do not dispose textures loaded through `Helper.ModContent` manually.

## State to clip mapping

| Gameplay state | Visual clip |
|---|---|
| `Dormant` | `idle` frame 0 / statue pose |
| `Intro` | `intro_awaken` |
| `Decision` | `idle` |
| `SwipeTelegraph` | `swipe_attack` |
| `RootSpikesTelegraph` | `root_cast` |
| `SummonAdds` | `summon_cast` |
| `ChargeTelegraph` | `charge_prep` |
| `Charging` | `charge_loop` |
| `VineTrapTelegraph` | `vine_cast` |
| `VineTrapActive` | `idle` + vine-zone FX |
| `AreaSlamTelegraph` | `slam_attack` |
| `PhaseTransition` | `phase_shift` |
| `Defeated` | `defeat` |
| `Victory` | hold final defeat frame / optional `victory_idle` |

When leaving `Charging`, optionally play `charge_end` as a short presentation bridge before returning to idle. Gameplay must not wait on it in v1.

## Clip definitions

Initial target clips:

```text
idle              6f   150ms/frame loop
intro_awaken     10f   150ms/frame once
swipe_attack      9f    78ms/frame once
root_cast         8f   112ms/frame once
summon_cast      10f    60ms/frame once
charge_prep       7f   128ms/frame once
charge_loop       3f    80ms/frame loop
charge_end        4f   100ms/frame once
vine_cast         8f   112ms/frame once
slam_attack      11f   100ms/frame once
phase_shift      12f   133ms/frame once
hurt               3f    90ms/frame once
defeat            12f   150ms/frame once
```

These numbers intentionally approximate the current gameplay durations:
- swipe 700ms;
- root 900ms;
- summon 600ms;
- charge telegraph 900ms;
- vine telegraph 900ms;
- slam 1100ms;
- phase transition 1600ms.

The state machine still decides the actual transition time.

## State-normalized playback

For attack clips whose state has a fixed duration, prefer normalized playback:

```text
progress = clamp((now - stateStarted) / stateDuration, 0..0.999)
frame = floor(progress * frameCount)
```

Use this for:
- intro;
- swipe;
- root;
- summon;
- charge prep;
- vine cast;
- slam;
- phase shift.

Use free-running loop playback only for:
- idle;
- charge loop;
- optional persistent overlays.

This guarantees animation reaches the intended impact pose without changing combat timing.

## Presentation event markers

These markers are visual synchronization references only for v1.

| Clip | Visual event |
|---|---|
| `intro_awaken` | frame 4 core brightens, frame 8 fully awake |
| `swipe_attack` | frame 5-6 swing contact pose |
| `root_cast` | frame 4 warning intensifies, frame 7 eruption pose |
| `summon_cast` | frame 7 summon burst |
| `charge_prep` | frame 5 direction-lock pose |
| `vine_cast` | frame 4 telegraph intensifies, frame 7 trap-open pose |
| `slam_attack` | frame 4 warning peak, frame 7 impact, frame 8 shockwave |
| `phase_shift` | frame 8 pulse, frame 12 stabilized form |
| `defeat` | frame 10 core separation, frame 12 collapse hold |

The existing service already applies real damage at its own state thresholds. Do not duplicate damage calls from animation events.

## Draw transform

Boss proxy position is the logical center/feet reference. Draw using feet anchoring:

```text
feetWorld = proxy.Position + bossFeetOffset
screen = Game1.GlobalToLocal(viewport, feetWorld)
source = rectangle(frame * 64, 0, 64, 64)
origin = (32,58)
scale = 4f
layerDepth = derived from feet Y
```

Recommended first-pass logical feet offset from proxy position:
`(32f, 56f)`

Tune this only after screenshot comparison.

Do not center the 64x64 frame on the proxy. The boss must feel planted on the ground.

## Facing

Verdant Guardian v1 does not need four-direction art.

Use one front/three-quarter sprite and horizontal flip when appropriate:
- player left of boss -> normal;
- player right of boss -> `SpriteEffects.FlipHorizontally`.

Freeze facing during:
- charge telegraph;
- charging;
- swipe impact;
- phase transition.

This keeps asset scope reasonable while still reacting to player position.

## Phase visual rules

Base body remains the same across all phases.

Phase 1:
- base texture;
- subtle core glow.

Phase 2:
- stronger core glow;
- slightly brighter green pulse;
- optional leaf particles.

Phase 3:
- brightest core;
- persistent rhythmic pulse;
- more frequent leaf sparks / phase aura.

No separate full-body recolor sheet is required for v1.

## Core glow overlay

Asset:
`assets/bosses/verdant_guardian/boss1_verdant_guardian_core_glow.png`

Contract:
- 64x64 frames aligned exactly to idle/base body coordinates;
- same `(32,58)` anchor;
- additive-looking transparent pixels;
- 4-6 frame loop;
- phase controls opacity and pulse rate.

If missing, retain the current procedural green cross/pulse as fallback.

## FX ownership

Ground telegraphs remain owned by `VerdantGuardianBossService` because they represent gameplay danger zones.

Swap procedural rectangles/circles for sprite FX only after the custom FX sheets exist. Their gameplay geometry must remain unchanged initially.

Planned assets:
- `fx_boss1_root_warning.png`
- `fx_boss1_root_erupt.png`
- `fx_boss1_vine_trap.png`
- `fx_boss1_slam_warning.png`
- `fx_boss1_slam_shockwave.png`
- `fx_boss1_leaf_burst.png`
- `fx_boss1_phase_pulse.png`

## Fallback contract

The visual pipeline must never make Boss I unplayable because of a missing PNG.

Fallback hierarchy:
1. approved custom clip;
2. approved custom idle sheet;
3. current vanilla GreenSlime proxy + procedural core glow.

Log a missing asset once, not every frame.

A missing cosmetic file must not break arena creation, boss HP, attacks, rewards or save persistence.

## Patch contract

Recommended patch:
`Patches/VerdantGuardianDrawPatch.cs`

Pseudo-interface:

```csharp
internal static class VerdantGuardianDrawPatch
{
    private static VerdantGuardianAnimationController? Visuals;

    public static void Apply(Harmony harmony, VerdantGuardianAnimationController visuals) { ... }

    private static bool Prefix(Monster __instance, SpriteBatch b)
    {
        if (!__instance.modData.ContainsKey(VerdantGuardianBossService.BossMarkerKey))
            return true;

        return !Visuals.TryDraw(__instance, b);
    }
}
```

If `TryDraw` returns false because no custom texture loaded, return true and allow vanilla slime rendering.

## Service integration

`VerdantGuardianBossService` should expose read-only visual state:

```csharp
public VerdantGuardianState CurrentState => this.State;
public int CurrentPhase => this.Phase;
public long CurrentStateStartedAtMs => this.StateStartedAtMs;
public Vector2 CurrentChargeDirection => this.ChargeDirection;
```

The animation controller reads these values only. It must not set boss state.

`ModEntry` owns both services:

```text
VerdantGuardianBossService
VerdantGuardianAnimationController
```

Initialization order:
1. create Boss I service;
2. create animation controller with Boss I service;
3. apply narrow draw patch;
4. register no extra save hooks for animator.

## Diagnostics

Add console/status fields:

```text
VisualMode=Custom|IdleFallback|VanillaProxy
Clip=<id>
Frame=<n>/<count>
Phase=<1..3>
Scale=4.0
Anchor=32,58
MissingAssets=<count>
```

Suggested command:
`cardcha_boss1_visual_status`

Optional debug-only clip preview:
`cardcha_boss1_visual_clip <clip-id>`

Do not persist debug clip overrides.

## Asset directory contract

```text
assets/bosses/verdant_guardian/
  boss1_verdant_guardian_idle.png
  boss1_verdant_guardian_intro_awaken.png
  boss1_verdant_guardian_swipe_attack.png
  boss1_verdant_guardian_root_cast.png
  boss1_verdant_guardian_summon_cast.png
  boss1_verdant_guardian_charge_prep.png
  boss1_verdant_guardian_charge_loop.png
  boss1_verdant_guardian_charge_end.png
  boss1_verdant_guardian_vine_cast.png
  boss1_verdant_guardian_slam_attack.png
  boss1_verdant_guardian_phase_shift.png
  boss1_verdant_guardian_hurt.png
  boss1_verdant_guardian_defeat.png
  boss1_verdant_guardian_core_glow.png
  fx_boss1_root_warning.png
  fx_boss1_root_erupt.png
  fx_boss1_vine_trap.png
  fx_boss1_slam_warning.png
  fx_boss1_slam_shockwave.png
  fx_boss1_leaf_burst.png
  fx_boss1_phase_pulse.png
```

## First implementation slice

Implement in this order:
1. animation controller + clip registry;
2. narrow Boss I draw suppression patch;
3. `idle` custom sheet loading;
4. state-to-clip mapping;
5. normalized playback;
6. core glow overlay;
7. diagnostics;
8. then add attack PNGs one clip at a time.

Acceptance for the first visual build:
- Slime body disappears only when a custom Verdant clip is successfully loaded;
- Boss remains fully damageable through the existing proxy;
- feet do not visibly slide across the floor during idle/attack;
- both phase thresholds and all attack timings match build .12.18;
- missing assets safely fall back to vanilla proxy;
- no SaveData schema change.

## Protected systems
Do not change while implementing this visual layer:
- Save schema 19;
- Boss I HP/damage/cooldown values unless explicitly tuning later;
- Boss Gate requirement 20;
- Region I Hunt Run 4-of-6;
- Boss Form duration 10 seconds;
- Boss Energy gain scale 1/3;
- 76/76 active card audit;
- MiMi/Wizard stair pending work;
- Airship route/visual;
- Forest collision/gate contract.
