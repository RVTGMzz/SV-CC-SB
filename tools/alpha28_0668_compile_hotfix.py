from pathlib import Path

p = Path('src/Cardcha/Services/VerdantGuardianArenaPolishService.cs')
s = p.read_text(encoding='utf-8')
if 'using StardewValley.Monsters;' not in s:
    s = s.replace('using StardewValley;\n', 'using StardewValley;\nusing StardewValley.Monsters;\n', 1)
p.write_text(s, encoding='utf-8')
print('0668 compile normalization applied')
