#!/usr/bin/env python3
from pathlib import Path

# Region II runtime hardening.
p=Path('src/Cardcha/Services/RegionExpeditionService.cs')
t=p.read_text(encoding='utf-8')
old='''    private bool DebugForceNormalRegion2;\n    private bool DebugForceBossApproachRegion2;'''
new='''    private bool DebugForceNormalRegion2;\n    private bool DebugForceBossApproachRegion2;\n    private bool DebugBossGateBypassRegion2;'''
if old not in t: raise SystemExit('0679 guard: runtime field anchor missing')
t=t.replace(old,new,1)

# A separate debug callback lets the test gate enter Boss II without mutating 40-card/Boss I save state.
old='''    private readonly AirshipFoundationService Airship;\n    private Func<string>? Region2BossGateAction;'''
new='''    private readonly AirshipFoundationService Airship;\n    private Func<string>? Region2BossGateAction;\n    private Func<string>? Region2BossGateDebugAction;'''
if old not in t: raise SystemExit('0679 guard: Region2 callback field anchor missing')
t=t.replace(old,new,1)
old='''    public void BindRegion2BossGateHandler(Func<string> handler)\n        => this.Region2BossGateAction = handler;'''
new='''    public void BindRegion2BossGateHandler(Func<string> handler)\n        => this.Region2BossGateAction = handler;\n\n    public void BindRegion2BossGateDebugHandler(Func<string> handler)\n        => this.Region2BossGateDebugAction = handler;'''
if old not in t: raise SystemExit('0679 guard: Region2 callback bind anchor missing')
t=t.replace(old,new,1)

t=t.replace('if (cleared)\n        {', 'if (cleared && !this.DebugBossGateBypassRegion2)\n        {', 1)
t=t.replace('if (owned < 40 && !this.DebugForceBossApproachRegion2)', 'if (owned < 40 && !this.DebugBossGateBypassRegion2)', 1)

old='''        if (this.Region2BossGateAction is null)\n        {\n            Game1.drawObjectDialogue(ModEntry.T("airship.expedition.unavailable"));\n            return true;\n        }\n\n        string result = this.Region2BossGateAction();\n        if (!string.IsNullOrWhiteSpace(result))\n            Game1.drawObjectDialogue(result);\n        return true;'''
new='''        Func<string>? action = this.DebugBossGateBypassRegion2\n            ? this.Region2BossGateDebugAction\n            : this.Region2BossGateAction;\n        bool debugGate = this.DebugBossGateBypassRegion2;\n        this.DebugBossGateBypassRegion2 = false;\n        if (action is null)\n        {\n            Game1.drawObjectDialogue(ModEntry.T("airship.expedition.unavailable"));\n            return true;\n        }\n\n        string result = action();\n        if (!string.IsNullOrWhiteSpace(result))\n            Game1.drawObjectDialogue(result);\n        this.Monitor.Log($"0679 Region II Archive Seal used. debug={debugGate}.", LogLevel.Info);\n        return true;'''
if old not in t: raise SystemExit('0679 guard: Region2 boss action anchor missing')
t=t.replace(old,new,1)

t=t.replace('''        this.DebugForceNormalRegion2 = false;\n        this.DebugForceBossApproachRegion2 = false;\n    }\n\n    private void ReturnToDeckImmediate''', '''        this.DebugForceNormalRegion2 = false;\n        this.DebugForceBossApproachRegion2 = false;\n        this.DebugBossGateBypassRegion2 = false;\n    }\n\n    private void ReturnToDeckImmediate''', 1)
t=t.replace('''        this.DebugBypassRegion = 2;\n        this.DebugForceBossApproachRegion2 = true;''', '''        this.DebugBypassRegion = 2;\n        this.DebugForceBossApproachRegion2 = true;\n        this.DebugBossGateBypassRegion2 = true;''', 1)
p.write_text(t,encoding='utf-8')

# Compile-safe nullable location test in the real Boss II gate handler.
p=Path('src/Cardcha/Services/MilestoneBossService.cs')
t=p.read_text(encoding='utf-8')
old='''        if (!Game1.currentLocation?.NameOrUniqueName.Equals(RegionExpeditionService.Region2LocationName, StringComparison.OrdinalIgnoreCase) == true)'''
new='''        if (Game1.currentLocation?.NameOrUniqueName.Equals(RegionExpeditionService.Region2LocationName, StringComparison.OrdinalIgnoreCase) != true)'''
if old not in t: raise SystemExit('0679 guard: Boss II location expression anchor missing')
t=t.replace(old,new,1)
p.write_text(t,encoding='utf-8')

# Wire the runtime-only test gate to the existing direct Boss II debug entry.
p=Path('src/Cardcha/ModEntry.cs')
t=p.read_text(encoding='utf-8')
old='''        this.RegionExpeditions.BindRegion2BossGateHandler(this.MilestoneBosses.EnterBoss2FromRegion2);'''
new='''        this.RegionExpeditions.BindRegion2BossGateHandler(this.MilestoneBosses.EnterBoss2FromRegion2);\n        this.RegionExpeditions.BindRegion2BossGateDebugHandler(() => this.MilestoneBosses.DebugEnterBoss(2));'''
if old not in t: raise SystemExit('0679 guard: ModEntry Region2 gate binding anchor missing')
t=t.replace(old,new,1)
p.write_text(t,encoding='utf-8')

print('0679 runtime guard applied: real gate strict, debug gate runtime-only')
