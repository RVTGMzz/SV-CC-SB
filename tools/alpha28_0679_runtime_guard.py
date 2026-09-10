#!/usr/bin/env python3
from pathlib import Path


def ensure_replace(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f'0679 guard: {label} anchor missing')
    return text.replace(old, new, 1)

# Region II runtime hardening.
p=Path('src/Cardcha/Services/RegionExpeditionService.cs')
t=p.read_text(encoding='utf-8')
t=ensure_replace(t,
'''    private bool DebugForceNormalRegion2;\n    private bool DebugForceBossApproachRegion2;''',
'''    private bool DebugForceNormalRegion2;\n    private bool DebugForceBossApproachRegion2;\n    private bool DebugBossGateBypassRegion2;''',
'runtime debug field')

# A separate debug callback lets the test gate enter Boss II without mutating 40-card/Boss I save state.
t=ensure_replace(t,
'''    private readonly AirshipFoundationService Airship;\n    private Func<string>? Region2BossGateAction;''',
'''    private readonly AirshipFoundationService Airship;\n    private Func<string>? Region2BossGateAction;\n    private Func<string>? Region2BossGateDebugAction;''',
'Region2 callback field')
t=ensure_replace(t,
'''    public void BindRegion2BossGateHandler(Func<string> handler)\n        => this.Region2BossGateAction = handler;''',
'''    public void BindRegion2BossGateHandler(Func<string> handler)\n        => this.Region2BossGateAction = handler;\n\n    public void BindRegion2BossGateDebugHandler(Func<string> handler)\n        => this.Region2BossGateDebugAction = handler;''',
'Region2 callback bind')

if 'if (cleared && !this.DebugBossGateBypassRegion2)' not in t:
    if 'if (cleared)\n        {' not in t: raise SystemExit('0679 guard: cleared-gate anchor missing')
    t=t.replace('if (cleared)\n        {', 'if (cleared && !this.DebugBossGateBypassRegion2)\n        {', 1)
if 'if (owned < 40 && !this.DebugBossGateBypassRegion2)' not in t:
    if 'if (owned < 40 && !this.DebugForceBossApproachRegion2)' not in t: raise SystemExit('0679 guard: card-gate anchor missing')
    t=t.replace('if (owned < 40 && !this.DebugForceBossApproachRegion2)', 'if (owned < 40 && !this.DebugBossGateBypassRegion2)', 1)

old_action='''        if (this.Region2BossGateAction is null)\n        {\n            Game1.drawObjectDialogue(ModEntry.T("airship.expedition.unavailable"));\n            return true;\n        }\n\n        string result = this.Region2BossGateAction();\n        if (!string.IsNullOrWhiteSpace(result))\n            Game1.drawObjectDialogue(result);\n        return true;'''
new_action='''        Func<string>? bossAction = this.DebugBossGateBypassRegion2\n            ? this.Region2BossGateDebugAction\n            : this.Region2BossGateAction;\n        bool debugGate = this.DebugBossGateBypassRegion2;\n        this.DebugBossGateBypassRegion2 = false;\n        if (bossAction is null)\n        {\n            Game1.drawObjectDialogue(ModEntry.T("airship.expedition.unavailable"));\n            return true;\n        }\n\n        string result = bossAction();\n        if (!string.IsNullOrWhiteSpace(result))\n            Game1.drawObjectDialogue(result);\n        this.Monitor.Log($"0679 Region II Archive Seal used. debug={debugGate}.", LogLevel.Info);\n        return true;'''
t=ensure_replace(t, old_action, new_action, 'Region2 boss action')

reset_old='''        this.DebugForceNormalRegion2 = false;\n        this.DebugForceBossApproachRegion2 = false;\n    }\n\n    private void ReturnToDeckImmediate'''
reset_new='''        this.DebugForceNormalRegion2 = false;\n        this.DebugForceBossApproachRegion2 = false;\n        this.DebugBossGateBypassRegion2 = false;\n    }\n\n    private void ReturnToDeckImmediate'''
t=ensure_replace(t, reset_old, reset_new, 'Region2 reset flag')

debug_old='''        this.DebugBypassRegion = 2;\n        this.DebugForceBossApproachRegion2 = true;'''
debug_new='''        this.DebugBypassRegion = 2;\n        this.DebugForceBossApproachRegion2 = true;\n        this.DebugBossGateBypassRegion2 = true;'''
t=ensure_replace(t, debug_old, debug_new, 'Region2 debug entry flag')
p.write_text(t,encoding='utf-8')

# Compile-safe nullable location test in the real Boss II gate handler.
p=Path('src/Cardcha/Services/MilestoneBossService.cs')
t=p.read_text(encoding='utf-8')
old='''        if (!Game1.currentLocation?.NameOrUniqueName.Equals(RegionExpeditionService.Region2LocationName, StringComparison.OrdinalIgnoreCase) == true)'''
new='''        if (Game1.currentLocation?.NameOrUniqueName.Equals(RegionExpeditionService.Region2LocationName, StringComparison.OrdinalIgnoreCase) != true)'''
t=ensure_replace(t, old, new, 'Boss II location expression')
p.write_text(t,encoding='utf-8')

# Wire the runtime-only test gate to the existing direct Boss II debug entry.
p=Path('src/Cardcha/ModEntry.cs')
t=p.read_text(encoding='utf-8')
old='''        this.RegionExpeditions.BindRegion2BossGateHandler(this.MilestoneBosses.EnterBoss2FromRegion2);'''
new='''        this.RegionExpeditions.BindRegion2BossGateHandler(this.MilestoneBosses.EnterBoss2FromRegion2);\n        this.RegionExpeditions.BindRegion2BossGateDebugHandler(() => this.MilestoneBosses.DebugEnterBoss(2));'''
t=ensure_replace(t, old, new, 'ModEntry Region2 debug gate binding')
p.write_text(t,encoding='utf-8')

print('0679 runtime guard PASS: real gate strict, debug gate runtime-only')
