from pathlib import Path

p = Path('src/Cardcha/ModEntry.cs')
text = p.read_text(encoding='utf-8')
lines = text.splitlines()
marker = 'VERDANT GUARDIAN VISUAL COMPLETE + COLOSSUS TEST'
hits = [i for i, line in enumerate(lines) if marker in line]
if len(hits) != 1:
    raise RuntimeError(f'Expected exactly one 0660 startup marker line, got {len(hits)}')
idx = hits[0]
# The first 0660 generator used an over-escaped regex character class, which could stop
# at an ordinary letter n and leave a tail containing interpolation braces. Replace the
# whole generated log argument line with a plain non-interpolated string.
lines[idx] = '            "Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.27 VERDANT GUARDIAN VISUAL COMPLETE + COLOSSUS TEST",'
p.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('0660 compile hotfix: startup log line normalized')
