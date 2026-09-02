from pathlib import Path

# Execute the .3.7 finalizer with one compatibility improvement: the historical
# CoreCardEffectsService has an XML summary between namespace and class, so consider
# the debug snapshot type materialized when its own marker is present instead of
# requiring the entire namespace+class replacement block to be byte-identical.
p = Path('tools/alpha28_41437_auto_scenario.py')
s = p.read_text(encoding='utf-8')
needle = "    if new in text:\n        return text\n"
replacement = "    if label == 'Core passive snapshot type' and 'internal readonly record struct CardPassiveDebugSnapshot(' in text:\n        return text\n    if new in text:\n        return text\n"
if needle not in s:
    raise SystemExit('replace_once compatibility anchor not found')
s = s.replace(needle, replacement, 1)
exec(compile(s, str(p), 'exec'), {'__name__': '__main__', '__file__': str(p)})
