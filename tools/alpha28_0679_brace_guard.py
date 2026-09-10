#!/usr/bin/env python3
from pathlib import Path

p = Path('src/Cardcha/Services/RegionExpeditionService.cs')
t = p.read_text(encoding='utf-8')

# The 0679 Describe/debug tail replacement already emits the class closing brace,
# while the original replacement boundary preserves the old class close too.
# A correct C# tail here is method-close + class-close, not three consecutive closes.
needle = "\n    }\n}\n}\n"
if t.endswith(needle):
    t = t[:-2]  # remove only the final extra `}\n`
elif t.rstrip().endswith("\n    }\n}\n}"):
    trimmed = t.rstrip()
    t = trimmed[:-2].rstrip() + "\n"
else:
    raise SystemExit('0679 brace guard: expected generated triple closing-brace tail was not found')

p.write_text(t, encoding='utf-8')
print('0679 brace guard applied: RegionExpeditionService tail normalized')
