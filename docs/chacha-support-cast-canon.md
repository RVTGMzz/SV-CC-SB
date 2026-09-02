# ChaCha Support Cast Canon

Target phase: `0.3.0-alpha.28.0.4.14.4.4`

This document locks the agreed runtime behavior for ChaCha's normal-form support system before implementation.

## Core architecture

ChaCha has **one normal-form Support Cast**, not four independent active skills.

The four Region skills are modular upgrades to the same Support Cast. Learning later Region skills adds effects to the same cast instead of adding separate buttons, separate cooldowns, or separate active slots.

Boss Form / Mythic Echo remains a separate system and is not changed by this design.

## Support Cast triggers

### 1. Kill Cast

- Roll after the player kills a monster.
- Requires the Support Cast cooldown to be ready.
- Maximum roll chance at skill Lv5 is **18%**.
- Lv1-Lv4 kill-cast rates are **TBD** and must not be invented in runtime until approved.

### 2. Lucky Cast on damage

Each time the player receives damage, roll the following chance:

| Skill level | Lucky Cast chance |
| --- | ---: |
| Lv1 | 4% |
| Lv2 | 5% |
| Lv3 | 6% |
| Lv4 | 7% |
| Lv5 | 8% |

- A successful Lucky Cast always triggers immediately.
- Lucky Cast **ignores the current cooldown**.
- Lucky Cast does not depend on current HP.

### 3. Emergency Cast

- Track HP immediately before and after a damage event.
- If HP was **above 30% before the hit** and becomes **30% or lower after the hit**, ChaCha performs one guaranteed Support Cast.
- Emergency Cast **ignores the current cooldown**.
- If the player was already at or below 30% before the hit, that hit does not qualify for another Emergency Cast.
- To qualify again, HP must first return above 30% and then cross down through the threshold on a later hit.

### Trigger deduplication

One combat event may satisfy more than one trigger, but it must produce **at most one Support Cast**.

Suggested runtime evaluation for a damage event:
1. evaluate Lucky Cast roll;
2. evaluate Emergency threshold crossing;
3. if either succeeds, perform one forced Support Cast;
4. never double-cast for the same hit.

Kill Cast is evaluated on monster death and is cooldown-gated.

## Cooldown

- There is one shared Support Cast cooldown.
- **Lv5 cooldown = 20 seconds**.
- Lv1-Lv4 cooldown values are **TBD** and must remain centralized/configurable until approved.
- Lucky Cast and Emergency Cast bypass cooldown readiness.
- After any successful Support Cast, the shared cooldown restarts from the current level's full duration.

## Region skill modules

### Region I: Phúc Lành Sinh Khí / Vital Blessing

This is the core Support Cast module and the first discovered skill.

- The cast includes healing.
- Exact healing values by level are **TBD**.
- Do not implement guessed heal percentages.

Upgrade material: **Giọt Sương Sinh Khí / Vital Dewdrop**.

### Region II: Hộ Mệnh Thỏ Tiên / Bunny Aegis

Once learned, every Support Cast also applies the shield/protection module.

- Shield buff duration: **20 seconds**.
- Exact shield strength is **TBD**.

Upgrade material: **Mảnh Khiên Ánh Trăng / Moonshield Shard**.

### Region III: Tinh Linh Tiếp Sức / Spirit Aid

Once learned, each Support Cast has a **30% chance** to add the stamina-support effect.

- Exact stamina amount / stamina-buff magnitude is **TBD**.
- This is a module on the same Support Cast, not a separate skill cast.

Upgrade material: **Lông Vũ Gió Nhẹ / Breeze Feather**.

### Region IV: Phúc Vận Thỏ Tiên / Lucky Echo

Once learned, each Support Cast has a **50% chance** to add a Luck buff.

- Luck buff duration: **10 seconds**.
- Exact Luck magnitude is **TBD**.
- This is a module on the same Support Cast, not a separate skill cast.

Upgrade material: **Đồng Xu Phúc Tinh / Fortune Coin**.

## Visual behavior

A Support Cast should visually read as one ChaCha action whose effects grow as Region modules are learned.

- Base/Vital: ChaCha cast presentation + healing pulse.
- Shield learned: add shield visual to the same cast.
- Spirit Aid learned and 30% roll succeeds: add wind/feather/stamina visual.
- Lucky Echo learned and 50% roll succeeds: add star/fortune visual for 10s Luck buff.

The player should not need to press another combat button for normal-form ChaCha support.

## Explicit non-goals for `.4.14.4.4` preparation

Do not silently lock any of the following until approved:
- Vital Blessing heal values.
- Bunny Aegis shield strength.
- Spirit Aid stamina magnitude.
- Lucky Echo Luck magnitude.
- Kill Cast Lv1-Lv4 percentages.
- Cooldown Lv1-Lv4 values.

The existing `.4.14.4.3` Airship Resonance Pedestal, four materials, item art, skill art, Region I material drop route, Boss Form 10-second duration, Boss Energy UX, and 76-card contract must be preserved.
