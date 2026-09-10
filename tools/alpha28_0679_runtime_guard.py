#!/usr/bin/env python3
from pathlib import Path

p=Path('src/Cardcha/Services/RegionExpeditionService.cs')
t=p.read_text(encoding='utf-8')
old='''    private bool DebugForceNormalRegion2;\n    private bool DebugForceBossApproachRegion2;'''
new='''    private bool DebugForceNormalRegion2;\n    private bool DebugForceBossApproachRegion2;\n    private bool DebugBossGateBypassRegion2;'''
if old not in t: raise SystemExit('0679 guard: runtime field anchor missing')
t=t.replace(old,new,1)
t=t.replace('if (owned < 40 && !this.DebugForceBossApproachRegion2)', 'if (owned < 40 && !this.DebugBossGateBypassRegion2)', 1)
t=t.replace('''        this.DebugForceNormalRegion2 = false;\n        this.DebugForceBossApproachRegion2 = false;\n    }\n\n    private void ReturnToDeckImmediate''', '''        this.DebugForceNormalRegion2 = false;\n        this.DebugForceBossApproachRegion2 = false;\n        this.DebugBossGateBypassRegion2 = false;\n    }\n\n    private void ReturnToDeckImmediate''', 1)
t=t.replace('''        this.DebugBypassRegion = 2;\n        this.DebugForceBossApproachRegion2 = true;''', '''        this.DebugBypassRegion = 2;\n        this.DebugForceBossApproachRegion2 = true;\n        this.DebugBossGateBypassRegion2 = true;''', 1)
p.write_text(t,encoding='utf-8')

p=Path('src/Cardcha/Services/MilestoneBossService.cs')
t=p.read_text(encoding='utf-8')
old='''        if (!Game1.currentLocation?.NameOrUniqueName.Equals(RegionExpeditionService.Region2LocationName, StringComparison.OrdinalIgnoreCase) == true)'''
new='''        if (Game1.currentLocation?.NameOrUniqueName.Equals(RegionExpeditionService.Region2LocationName, StringComparison.OrdinalIgnoreCase) != true)'''
if old not in t: raise SystemExit('0679 guard: Boss II location expression anchor missing')
t=t.replace(old,new,1)
p.write_text(t,encoding='utf-8')
print('0679 runtime guard applied')
