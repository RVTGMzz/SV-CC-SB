# NEXT SESSION — Cardcha v0.3.0-alpha.17 Mythic + Minimap + Browse

## Current candidate
- Version: `0.3.0-alpha.17`
- Build label: `Cardcha! v0.3.0-alpha.17 MYTHIC + MINIMAP + BROWSE`
- Baseline: alpha.16 Binder Deselect + Browse.

## Exact alpha.17 fixes
1. Binder heading is now just `BỘ SƯU TẬP / COLLECTION`; owned/total is already shown by the footer discovery count.
2. User-facing locked Boss slot text is now `Ô kỹ năng Thần Thoại hiện vẫn đang bị khóa.` / `The Mythic Skill slot is still locked.`
3. NPC Map Locations Custom mode crops exactly 16x15 from the top-left of the NPC texture. MiMi uses 32x48 frames, which caused the visible quarter-head marker. Alpha.17 embeds a dedicated full-face marker into that exact crop region.
4. The reserved first front frame is never rendered in-world; normal MiMi/??? front animation uses the other front poses so the minimap marker pixels never flash on the character.
5. NPC Map Locations custom integration uses `MarkerCropOffset=0`; Vanilla mode uses `MugShotSourceRect=0,0,16,15`.
6. **Selection lock hardening:** controller A creates/replaces a persistent locked card action context. RIGHT or DOWN from a collection cell while locked jumps into the detail/action buttons. Normal navigation, rarity filters, and page changes do not clear the lock. Every Favorite/Equip/Upgrade action restores the locked card before executing, so UI preview/focus changes cannot retarget the action. Only the explicit `BỎ CHỌN / DESELECT` button releases the lock.

## Test first
- Binder heading: no literal `(owned/total)`.
- Focus/click the Mythic slot: status says `Kỹ năng Thần Thoại`, not Boss.
- NPC Map Locations Custom mode: MiMi/??? marker shows the whole face, purple hair and red bow, not one quarter of the head.
- Vanilla marker icon mode: same full marker.
- Watch MiMi front-facing idle/walk for any corrupted reserved-frame flash.
- Controller lock test: A-select #03, move focus around, change filter/page if desired, then trigger Favorite/Equip/Upgrade; every action must still target #03 until `BỎ CHỌN`. RIGHT/DOWN from a locked collection cell must enter the action area.
- Press `BỎ CHỌN`, then move across collection cells without A; right-page preview must follow the focused card again.

## Artifacts
- `Cardcha_v0.3.0-alpha.17_MythicMinimap_WindowsBuilder_FULL.zip`
- `Cardcha_v0.3.0-alpha.17_SOURCE_SNAPSHOT.zip`

Static validation passed in the container; real Windows compile with Stardew/SMAPI refs is still required.