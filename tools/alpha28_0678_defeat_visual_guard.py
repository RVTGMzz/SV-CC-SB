#!/usr/bin/env python3
from pathlib import Path
p=Path('src/Cardcha/Services/MilestoneBossService.cs')
t=p.read_text(encoding='utf-8')
old='if (!actor.modData.ContainsKey(BossMarkerKey) || actor.Health <= 0)'
new='if (!actor.modData.ContainsKey(BossMarkerKey))'
if old not in t:
    raise SystemExit('0678 defeat visual guard: expected actor health guard not found')
t=t.replace(old,new,1)
old_depth='actor.getStandingY() / 10000f'
new_depth='(actor.Position.Y + 64f) / 10000f'
if old_depth not in t:
    raise SystemExit('0678 depth API guard: expected getStandingY expression not found')
t=t.replace(old_depth,new_depth,1)
p.write_text(t,encoding='utf-8')
print('0678 defeat visual + compile-safe feet depth guard applied')
