#!/usr/bin/env python3
from pathlib import Path
import re

p = Path('src/Cardcha/Services/RegionExpeditionService.cs')
t = p.read_text(encoding='utf-8')

# Fresh generator output can contain two column-zero class closes at EOF.
# Materialized source already has the correct single class close, so accept both states.
fixed, count = re.subn(r'\n}\s*\n}\s*$', '\n}\n', t, count=1)
if count == 1:
    p.write_text(fixed, encoding='utf-8')
    print('0679 brace guard applied: duplicate class close removed')
elif re.search(r'\n    }\s*\n}\s*$', t):
    print('0679 brace guard PASS: source tail already normalized')
else:
    raise SystemExit('0679 brace guard: unexpected RegionExpeditionService tail')
