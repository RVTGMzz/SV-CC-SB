from pathlib import Path

p = Path('src/Cardcha/Services/CoreCardEffectsService.cs')
s = p.read_text(encoding='utf-8')
marker = 'internal readonly record struct CardPassiveDebugSnapshot('
if marker not in s:
    anchor = '/// <summary>\n/// Alpha.26.5 completion pass for Base Set cards whose text existed before their runtime hooks.\n'
    if anchor not in s:
        raise SystemExit('CoreCardEffectsService summary anchor not found')
    block = '''internal readonly record struct CardPassiveDebugSnapshot(\n    int Defense,\n    double WeaponSpeed,\n    double MovePercent,\n    double Knockback,\n    double CriticalPower,\n    int MagneticRadius,\n    double AttackMultiplier,\n    int VanguardShield,\n    int GuardianShield\n);\n\n'''
    s = s.replace(anchor, block + anchor, 1)
    p.write_text(s, encoding='utf-8')
print('Core passive debug snapshot anchor prepared')
