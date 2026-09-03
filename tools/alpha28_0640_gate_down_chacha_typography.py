from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
VERSION_OLD = '0.3.0-alpha.28.0.4.14.4.5.6.1.1'
VERSION = '0.3.0-alpha.28.0.4.14.4.5.6.1.2'

# Version stamp.
for rel in ['manifest.json', 'Cardcha.csproj', 'Directory.Build.targets', 'ModEntry.cs']:
    p = ROOT / rel
    s = p.read_text(encoding='utf-8')
    s = s.replace(VERSION_OLD, VERSION)
    p.write_text(s, encoding='utf-8')

# Move the canonical Forest gate from the upper-right Wizard pocket down/left into
# the open meadow requested in the in-game screenshot. Keep the tiny local safety
# search and never touch Forest collision/pathing.
gate_path = ROOT / 'Patches/AirshipGateRelocationPatch.cs'
gate = gate_path.read_text(encoding='utf-8')
old_offset = 'private static readonly Point WizardGateOffset = new(8, -4);'
if old_offset not in gate and 'WizardGateOffset = new(-4, 0)' not in gate:
    raise SystemExit('Expected .5.6.1 WizardGateOffset contract not found')
gate = gate.replace(old_offset, 'private static readonly Point WizardGateOffset = new(-4, 0);')
gate = gate.replace(
    '    private static readonly Point[] WizardGateAlternates =\n    {\n        new(10, -3),\n        new(7, -2),\n    };',
    '    private static readonly Point[] WizardGateAlternates =\n    {\n        new(-5, 1),\n        new(-4, 2),\n        new(-6, 0),\n    };'
)
gate = gate.replace(
    '/// .5.6.1 canonical Forest Arcane Gate placement.',
    '/// .5.6.1.2 canonical Forest Arcane Gate placement: lower Wizard-side meadow.'
)
gate = gate.replace(
    '/// The gate now belongs to the Wizard-side meadow instead of roaming the Forest. We anchor from',
    '/// The gate now belongs to the lower Wizard-side meadow instead of the blocked upper pocket. We anchor from'
)
gate_path.write_text(gate, encoding='utf-8')

# Increase all explicit text caps in the ChaCha Resonance screen by exactly 1.5x.
# DrawScaledText still auto-fits to its rectangle, so long translations remain inside
# their panels while short/medium labels become substantially easier to read.
menu_path = ROOT / 'UI/ChaChaResonanceMenu.cs'
menu = menu_path.read_text(encoding='utf-8')
marker = '// .5.6.1.2 typography pass: all ChaCha Resonance text caps are 1.50x the previous values.'
if marker not in menu:
    max_hits = len(re.findall(r'maxScale:\s*[0-9]+(?:\.[0-9]+)?f', menu))
    button_hits = len(re.findall(r'textScale:\s*[0-9]+(?:\.[0-9]+)?f', menu))
    if max_hits < 10 or button_hits < 2:
        raise SystemExit(f'Unexpected ChaCha typography contract: maxScale={max_hits}, textScale={button_hits}')

    def bump(match):
        prefix = match.group(1)
        value = float(match.group(2)) * 1.5
        text = f'{value:.3f}'.rstrip('0').rstrip('.')
        return f'{prefix}{text}f'

    menu = re.sub(r'(maxScale:\s*)([0-9]+(?:\.[0-9]+)?)f', bump, menu)
    menu = re.sub(r'(textScale:\s*)([0-9]+(?:\.[0-9]+)?)f', bump, menu)
    menu = menu.replace(
        '    private const int EntryBaseId = 400;\n',
        '    private const int EntryBaseId = 400;\n    ' + marker + '\n'
    )

    # Give the most visibly cramped left-side information rows a little more vertical
    # room so the requested 1.5x cap can actually render instead of immediately fitting down.
    menu = menu.replace(
        'Rectangle title = new(this.LeftPanel.X + 16, this.LeftPanel.Y + 14, this.LeftPanel.Width - 32, 36);',
        'Rectangle title = new(this.LeftPanel.X + 16, this.LeftPanel.Y + 12, this.LeftPanel.Width - 32, 44);'
    )
    menu = menu.replace(
        'Rectangle formLabel = new(this.LeftPanel.X + 18, portrait.Bottom + 7, this.LeftPanel.Width - 36, 24);',
        'Rectangle formLabel = new(this.LeftPanel.X + 18, portrait.Bottom + 6, this.LeftPanel.Width - 36, 30);'
    )
    menu = menu.replace(
        'Rectangle formValue = new(this.LeftPanel.X + 18, formLabel.Bottom + 1, this.LeftPanel.Width - 36, 30);',
        'Rectangle formValue = new(this.LeftPanel.X + 18, formLabel.Bottom, this.LeftPanel.Width - 36, 36);'
    )
    menu = menu.replace(
        'Rectangle dustInfo = new(this.LeftPanel.X + 18, formValue.Bottom + 2, this.LeftPanel.Width - 36, 25);',
        'Rectangle dustInfo = new(this.LeftPanel.X + 18, formValue.Bottom + 1, this.LeftPanel.Width - 36, 30);'
    )

menu_path.write_text(menu, encoding='utf-8')

# Keep the build target comment honest.
targets_path = ROOT / 'Directory.Build.targets'
targets = targets_path.read_text(encoding='utf-8')
targets = targets.replace(
    '.5.6.1.1 TEST-only one-command max cards + ChaCha skill patch.',
    '.5.6.1.2 lower gate placement + ChaCha Resonance 1.5x typography; max-all debug retained.'
)
targets_path.write_text(targets, encoding='utf-8')

# Basic source-level assertions before CI compiles.
assert 'WizardGateOffset = new(-4, 0)' in gate
assert 'new(-5, 1)' in gate and 'new(-4, 2)' in gate and 'new(-6, 0)' in gate
assert 'CanonicalGateUseDistance = 160f' in gate
assert 'CollisionEdits=NONE' in gate
assert marker in menu
assert 'cardcha_max_all' in (ROOT / 'Patches/DebugMaxAllCommandPatch.cs').read_text(encoding='utf-8')
assert json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))['Version'] == VERSION
print('alpha28 .5.6.1.2 source generation PASS')
