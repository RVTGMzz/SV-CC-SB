from pathlib import Path
import json, re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.10'
PREV = '0.3.0-alpha.28.0.4.14.4.5.12.9'

# Version metadata.
manifest = ROOT / 'manifest.json'
data = json.loads(manifest.read_text(encoding='utf-8-sig'))
data['Version'] = VERSION
manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

for rel in ['Cardcha.csproj', 'Directory.Build.targets']:
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    text = text.replace(PREV, VERSION)
    path.write_text(text, encoding='utf-8')

# WIZ-02 / WIZ-03 only.
# Fixed floor anchor: move the staircase upward into the narrow alcove between the two plants.
# No clear-tile scan, no runtime relocation, no tile deletion.
home = ROOT / 'Services/MimiHomeService.cs'
text = home.read_text(encoding='utf-8')
old = '''        // WIZ-01/WIZ-02 LOCKED: this is a landmark-relative FIXED tile, not a safety search.\n        // In the current WizardHouse layout this is the bare floor between the two plants\n        // selected in the acceptance screenshot. NPCs, temporary objects, time, and player\n        // movement are deliberately ignored so the staircase can never "run" to another tile.\n        int x = Math.Clamp(width - 4, 2, Math.Max(2, width - 2));\n        int y = Math.Clamp((int)Math.Round(height * 0.58f), 2, Math.Max(2, height - 3));\n        return new Point(x, y);'''
new = '''        // WIZ-01/WIZ-02/WIZ-03 candidate: one fixed landmark-relative anchor only.\n        // The accepted screenshot target is the recessed floor tile between the two plants,\n        // higher than the previous open-floor placement. This deliberately ignores NPCs,\n        // temporary objects, time, and player movement, so the staircase cannot "run".\n        int x = Math.Clamp(width - 4, 2, Math.Max(2, width - 2));\n        int y = Math.Clamp((int)Math.Round(height * 0.42f), 2, Math.Max(2, height - 3));\n        return new Point(x, y);'''
if old not in text:
    raise SystemExit('Expected 0648C fixed stair block not found')
text = text.replace(old, new, 1)
home.write_text(text, encoding='utf-8')

# Draw the 4-tile-tall stair one tile higher than its interaction/landing floor tile.
# This keeps the bottom of the visual out of the farmer/NPC standing tile instead of painting
# over characters from RenderedWorld.
visual = ROOT / 'Services/MimiAtticVisualService.cs'
text = visual.read_text(encoding='utf-8')
old_draw = '            Vector2 world = new(tile.X * 64f, (tile.Y - 3) * 64f);'
new_draw = '            Vector2 world = new(tile.X * 64f, (tile.Y - 4) * 64f);'
if old_draw not in text:
    raise SystemExit('Expected Wizard stair draw anchor not found')
text = text.replace(old_draw, new_draw, 1)
visual.write_text(text, encoding='utf-8')

print(json.dumps({
    'version': VERSION,
    'scope': ['WIZ-02 move fixed stair into upper between-plants alcove', 'WIZ-03 keep stair visual off the standing tile'],
    'wizardStair': 'x=width-4, y=round(height*0.42), fixed; visual lifted 1 tile',
    'tileDeletion': False,
    'runtimeRelocation': False,
    'unrelatedSystemsTouched': False,
}, indent=2))
