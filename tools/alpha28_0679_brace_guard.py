#!/usr/bin/env python3
from pathlib import Path
import re

p = Path('src/Cardcha/Services/RegionExpeditionService.cs')
t = p.read_text(encoding='utf-8')

# The 0679 tail replacement emits its own class close and preserves the original
# column-zero class close. Remove exactly one duplicated column-zero close at EOF.
# The method close is indented four spaces, so it is never matched by this rule.
fixed, count = re.subn(r'\n}\s*\n}\s*$', '\n}\n', t, count=1)
if count != 1:
    raise SystemExit('0679 brace guard: duplicated column-zero class closing brace was not found')

p.write_text(fixed, encoding='utf-8')
print('0679 brace guard applied: duplicate class close removed')
