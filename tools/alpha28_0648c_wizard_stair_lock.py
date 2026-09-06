from pathlib import Path
import json, re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.9'

# Version metadata only.
manifest = ROOT / 'manifest.json'
data = json.loads(manifest.read_text(encoding='utf-8-sig'))
data['Version'] = VERSION
manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

for rel in ['Cardcha.csproj', 'Directory.Build.targets']:
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'0\.3\.0-alpha\.28\.0\.4\.14\.4\.5\.12\.8', VERSION, text)
    path.write_text(text, encoding='utf-8')

# WIZ-01 / WIZ-02 only. Do not touch any Airship, Gate, portrait, or MiMi routine code.
path = ROOT / 'Services/MimiHomeService.cs'
text = path.read_text(encoding='utf-8')
start = text.index('    internal static Point ResolvePreferredWizardStairTile(GameLocation wizard)')
end = text.index('    private static Point ResolveWizardLandingTile', start)
replacement = '''    internal static Point ResolvePreferredWizardStairTile(GameLocation wizard)\n    {\n        int width = wizard.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 12;\n        int height = wizard.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 10;\n\n        // WIZ-01/WIZ-02 LOCKED: this is a landmark-relative FIXED tile, not a safety search.\n        // In the current WizardHouse layout this is the bare floor between the two plants\n        // selected in the acceptance screenshot. NPCs, temporary objects, time, and player\n        // movement are deliberately ignored so the staircase can never "run" to another tile.\n        int x = Math.Clamp(width - 4, 2, Math.Max(2, width - 2));\n        int y = Math.Clamp((int)Math.Round(height * 0.58f), 2, Math.Max(2, height - 3));\n        return new Point(x, y);\n    }\n\n'''
text = text[:start] + replacement + text[end:]
path.write_text(text, encoding='utf-8')

print(json.dumps({
    'version': VERSION,
    'scope': ['WIZ-01 fixed stair position', 'WIZ-02 between-plants landmark placement'],
    'wizardStair': 'x=width-4, y=round(height*0.58), no clear-tile search',
    'tileDeletion': False,
    'unrelatedGameplayTouched': False,
}, indent=2))
