from pathlib import Path
import json

ROOT = Path('src/Cardcha')
BASE_VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.24'
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.25'

manifest = ROOT / 'manifest.json'
data = json.loads(manifest.read_text(encoding='utf-8-sig'))
if data['Version'] != BASE_VERSION:
    raise RuntimeError(f'Expected base {BASE_VERSION}, got {data["Version"]}')
data['Version'] = VERSION
manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

for rel in ['Cardcha.csproj', 'Directory.Build.targets']:
    p = ROOT / rel
    text = p.read_text(encoding='utf-8')
    if BASE_VERSION not in text:
        raise RuntimeError(f'{BASE_VERSION} missing from {rel}')
    p.write_text(text.replace(BASE_VERSION, VERSION), encoding='utf-8')

home_path = ROOT / 'Services/MimiHomeService.cs'
home = home_path.read_text(encoding='utf-8')
old = '''    internal static Point ResolvePreferredWizardStairTile(GameLocation wizard)\n    {\n        // 0657: preserve the last in-game-visible WizardHouse stair column. The regression was\n        // introduced by changing the stair artwork/caching, not by this gameplay anchor. Keep\n        // visual, collision, interaction, ascent and return landing tied to the same x15 route.\n        return new Point(15, 15);\n    }\n'''
new = '''    internal static Point ResolvePreferredWizardStairTile(GameLocation wizard)\n    {\n        // 0658: WizardHouse replacements can expose a Buildings layer only 15 tiles wide,\n        // where valid X coordinates are 0..14. Preserve x15 on wider maps, but clamp the\n        // preferred right-wall route to the active map bounds so every stair subsystem shares\n        // one valid coordinate.\n        int width = wizard.Map?.GetLayer("Buildings")?.LayerWidth\n            ?? wizard.Map?.Layers.FirstOrDefault()?.LayerWidth\n            ?? 16;\n        int height = wizard.Map?.GetLayer("Buildings")?.LayerHeight\n            ?? wizard.Map?.Layers.FirstOrDefault()?.LayerHeight\n            ?? 35;\n\n        int x = Math.Clamp(15, 0, Math.Max(0, width - 1));\n        int y = Math.Clamp(15, 4, Math.Max(4, height - 1));\n        return new Point(x, y);\n    }\n'''
if old not in home:
    raise RuntimeError('0657 stair resolver block not found')
home = home.replace(old, new, 1)
home_path.write_text(home, encoding='utf-8')

handoff = Path('handoff/ALPHA28_0658_WIZARD_STAIR_BOUNDS_SAFE.md')
handoff.write_text('''# Alpha28 0658 - Wizard stair bounds-safe placement\n\nBuild: `0.3.0-alpha.28.0.4.14.4.5.12.25`\nBranch: `cardcha-alpha28-0658-wizard-stair-bounds-safe`\nStatus: implementation candidate, in-game acceptance pending.\n\n## Root cause confirmed from in-game log\nThe active WizardHouse replacement exposes a `Buildings` layer of `15x35`, so valid X coordinates are `0..14`. 0657 requested stair target `(15,15)`, which is outside that layer. The visual service therefore refused installation and retried every render, producing repeated warnings.\n\n## Fix\n`MimiHomeService.ResolvePreferredWizardStairTile` now resolves the preferred right-wall stair position against the active WizardHouse Buildings-layer dimensions. Preferred X remains 15 on maps wide enough for it, but clamps to `width - 1` when required. On the reported `15x35` map the resolved target is `(14,15)`.\n\nThe same resolved coordinate remains authoritative for visual placement, collision, player interaction, ascent and return landing.\n\nNo save schema, card canon, progression, MiMi profile, attic layout, Airship, Hunt Run, Boss Gate, Boss Form, or controller behavior is changed.\n''', encoding='utf-8')

latest = Path('handoff/LATEST_CARDCHA_HANDOFF.md')
latest.write_text('''# Latest Cardcha handoff\n\nCurrent branch: `cardcha-alpha28-0658-wizard-stair-bounds-safe`\nCurrent build: `0.3.0-alpha.28.0.4.14.4.5.12.25`\n\nContinue from:\n`handoff/ALPHA28_0658_WIZARD_STAIR_BOUNDS_SAFE.md`\n\nImportant: in-game acceptance is pending. Do not resume from stale `main`.\n''', encoding='utf-8')

print(json.dumps({
    'version': VERSION,
    'boundsBehavior': 'x=min(15, BuildingsWidth-1)',
    'reported15WideMapTarget': [14, 15],
}, indent=2))
