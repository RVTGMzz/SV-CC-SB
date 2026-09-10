#!/usr/bin/env python3
from pathlib import Path
p=Path('src/Cardcha/Services/MilestoneBossService.cs')
t=p.read_text(encoding='utf-8')
old='if (!actor.modData.ContainsKey(BossMarkerKey) || actor.Health <= 0)'
new='if (!actor.modData.ContainsKey(BossMarkerKey))'
if old not in t:
    raise SystemExit('0678 defeat visual guard: expected actor health guard not found')
p.write_text(t.replace(old,new,1),encoding='utf-8')
print('0678 defeat visual guard applied')
