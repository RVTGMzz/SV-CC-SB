#!/usr/bin/env python3
from pathlib import Path
p=Path('src/Cardcha/Services/Region2RoguelikeRunService.cs')
t=p.read_text(encoding='utf-8')
old='''        if (gateClose || gateFacing)\n        {\n            this.Helper.Input.Suppress(e.Button);\n            this.TryUseBossGate();\n            return;\n        }'''
new='''        if (this.CurrentRoom == Region2RoomKind.WardenVault && (gateClose || gateFacing))\n        {\n            this.Helper.Input.Suppress(e.Button);\n            this.TryUseBossGate();\n            return;\n        }'''
if new not in t:
    if old not in t:
        raise SystemExit('0682 gate-scope anchor missing')
    t=t.replace(old,new,1)
p.write_text(t,encoding='utf-8')
print('0682 gate interaction scoped to WardenVault')
