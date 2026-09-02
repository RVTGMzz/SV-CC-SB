# ChaCha Support Cast Canon

Target phase: `0.3.0-alpha.28.0.4.14.4.4`

ChaCha has **one normal-form Support Cast**. The four Region skills are modular upgrades to this same cast, never four independent active skills or four cooldowns. Boss Form / Mythic Echo remains separate.

## Shared trigger level

The Support Cast trigger table uses **Vital Blessing level** (Lv1-Lv5).

| Level | Kill Cast after a monster kill | Lucky Cast when taking damage | Shared cooldown | Vital heal |
| --- | ---: | ---: | ---: | ---: |
| Lv1 | 6% | 4% | 40s | 10% Max HP |
| Lv2 | 9% | 5% | 35s | 13% Max HP |
| Lv3 | 12% | 6% | 30s | 16% Max HP |
| Lv4 | 15% | 7% | 25s | 20% Max HP |
| Lv5 | 18% | 8% | 20s | 25% Max HP |

### Kill Cast
- Roll after the local player kills a monster.
- Requires the shared cooldown to be ready.
- A failed roll does not start cooldown.

### Lucky Cast on damage
- Roll on every **actual health-damaging hit**.
- A successful roll casts immediately regardless of HP or cooldown.

### Emergency Cast
- If HP was **above 30% before the hit** and becomes **30% or lower after the hit**, cast once with 100% certainty.
- Emergency Cast ignores cooldown.
- If the player was already at or below 30%, later hits do not retrigger Emergency until HP first returns above 30%.

### Deduplication
A single damage event can satisfy Lucky + Emergency together, but creates **one cast only**. After any successful cast, the shared cooldown restarts from the current Vital level's full duration.

## Region modules

### Region I: Phúc Lành Sinh Khí / Vital Blessing
Every Support Cast heals the player by the Vital heal table above. Material: **Giọt Sương Sinh Khí / Vital Dewdrop**.

### Region II: Hộ Mệnh Thỏ Tiên / Bunny Aegis
Once learned, every Support Cast refreshes a **20 second shield**. Incoming damage reduction by Aegis level: **20 / 25 / 30 / 35 / 40%**. Material: **Mảnh Khiên Ánh Trăng / Moonshield Shard**.

### Region III: Tinh Linh Tiếp Sức / Spirit Aid
Once learned, every Support Cast rolls **30%** to restore stamina. Restore by Spirit Aid level: **10 / 15 / 20 / 25 / 30% Max Stamina**. Material: **Lông Vũ Gió Nhẹ / Breeze Feather**.

### Region IV: Phúc Vận Thỏ Tiên / Lucky Echo
Once learned, every Support Cast rolls **50%** to apply a **+1 Luck buff for 10 seconds**. Material: **Đồng Xu Phúc Tinh / Fortune Coin**. The 50% proc chance and 10s duration do not fragment into another cooldown.

## Visual / input contract
- One automatic Support Cast action from ChaCha.
- One HUD icon and one cooldown.
- No new combat button.
- Base heal pulse always appears. Shield, stamina and luck visuals layer onto the same cast only when learned/procced.
- Normal-form Support Cast is disabled while Boss Form is active.

## Regression locks
- Save schema stays 19; cooldown/buffs are runtime-only.
- Airship Resonance Pedestal + four upgrade materials remain.
- `card_icons.png` SHA-256 stays `c5ff456e9a0a697a10537a391ec5abf2f90966de89299799fd2153356b1e6e41`.
- Airship visual SHA-256 stays `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- Boss Form duration stays 10 seconds and existing activation controls stay unchanged.
- Forest collision/map edits remain NONE.
- Card auto audit remains 76/76 PASS.
