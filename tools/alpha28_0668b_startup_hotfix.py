from pathlib import Path

p = Path('src/Cardcha/ModEntry.cs')
s = p.read_text(encoding='utf-8')
old = 'Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.35 HUNT RUN 2.0 ADVANCED LAYER TEST'
new = 'Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.36 COMBAT HUD RUNTIME COVERAGE HOTFIX TEST'
if old not in s and new not in s:
    raise SystemExit('startup banner anchor missing')
s = s.replace(old, new)
p.write_text(s, encoding='utf-8')
print(new)
