from pathlib import Path
p = Path('src/Cardcha/Patches/AirshipGateRelocationPatch.cs')
s = p.read_text(encoding='utf-8')
if s.endswith('\n}}\n'):
    s = s[:-4] + '}\n'
if not s.rstrip().endswith('}'):
    raise RuntimeError('AirshipGateRelocationPatch.cs has an invalid ending')
p.write_text(s, encoding='utf-8')
print('0646B finalizer PASS')
