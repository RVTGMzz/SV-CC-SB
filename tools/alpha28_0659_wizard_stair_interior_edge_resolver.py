from pathlib import Path
import json

ROOT = Path('src/Cardcha')
BASE_VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.25'
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.26'

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
old = '''    internal static Point ResolvePreferredWizardStairTile(GameLocation wizard)\n    {\n        // 0658: WizardHouse replacements can expose a Buildings layer only 15 tiles wide,\n        // where valid X coordinates are 0..14. Preserve x15 on wider maps, but clamp the\n        // preferred right-wall route to the active map bounds so every stair subsystem shares\n        // one valid coordinate.\n        int width = wizard.Map?.GetLayer("Buildings")?.LayerWidth\n            ?? wizard.Map?.Layers.FirstOrDefault()?.LayerWidth\n            ?? 16;\n        int height = wizard.Map?.GetLayer("Buildings")?.LayerHeight\n            ?? wizard.Map?.Layers.FirstOrDefault()?.LayerHeight\n            ?? 35;\n\n        int x = Math.Clamp(15, 0, Math.Max(0, width - 1));\n        int y = Math.Clamp(15, 4, Math.Max(4, height - 1));\n        return new Point(x, y);\n    }\n'''
new = '''    internal static Point ResolvePreferredWizardStairTile(GameLocation wizard)\n    {\n        // 0659: layer bounds are not the same thing as the visible room boundary. The 15-wide\n        // SVE WizardHouse accepts x14 mathematically, but that column is black exterior void.\n        // Resolve the stair from actual map content instead: use the rightmost walkable Back\n        // tile at the landing row which is immediately beside a wall/void boundary. This keeps\n        // the ladder inside the room and directly against the right wall where the NPCs stand.\n        const int preferredY = 15;\n        var buildings = wizard.Map?.GetLayer("Buildings");\n        var back = wizard.Map?.GetLayer("Back");\n\n        int width = buildings?.LayerWidth\n            ?? back?.LayerWidth\n            ?? wizard.Map?.Layers.FirstOrDefault()?.LayerWidth\n            ?? 16;\n        int height = buildings?.LayerHeight\n            ?? back?.LayerHeight\n            ?? wizard.Map?.Layers.FirstOrDefault()?.LayerHeight\n            ?? 35;\n        int y = Math.Clamp(preferredY, 4, Math.Max(4, height - 1));\n\n        if (buildings is not null && back is not null)\n        {\n            int scanY = Math.Clamp(y, 0, Math.Min(buildings.LayerHeight, back.LayerHeight) - 1);\n            int maxX = Math.Min(buildings.LayerWidth, back.LayerWidth) - 1;\n\n            // First pass: choose a walkable interior floor tile directly beside the right boundary.\n            for (int x = maxX; x >= 0; x--)\n            {\n                if (back.Tiles[x, scanY] is null || buildings.Tiles[x, scanY] is not null)\n                    continue;\n\n                bool rightIsBoundary = x == maxX\n                    || back.Tiles[x + 1, scanY] is null\n                    || buildings.Tiles[x + 1, scanY] is not null;\n                if (rightIsBoundary)\n                    return new Point(x, scanY);\n            }\n\n            // Compatibility fallback: still prefer the rightmost actual floor tile, never raw map width.\n            for (int x = maxX; x >= 0; x--)\n            {\n                if (back.Tiles[x, scanY] is not null && buildings.Tiles[x, scanY] is null)\n                    return new Point(x, scanY);\n            }\n        }\n\n        // Last-resort fallback for unusual map replacements with no standard Back layer. Stay one\n        // tile inside the layer edge rather than returning the edge column itself.\n        int fallbackX = Math.Clamp(Math.Min(15, width - 2), 0, Math.Max(0, width - 1));\n        return new Point(fallbackX, y);\n    }\n'''
if old not in home:
    raise RuntimeError('0658 stair resolver block not found')
home = home.replace(old, new, 1)
home_path.write_text(home, encoding='utf-8')

handoff = Path('handoff/ALPHA28_0659_WIZARD_STAIR_INTERIOR_EDGE.md')
handoff.write_text('''# Alpha28 0659 - Wizard stair interior-edge resolver\n\nBuild: `0.3.0-alpha.28.0.4.14.4.5.12.26`\nBranch: `cardcha-alpha28-0659-wizard-stair-interior-edge-resolver`\nStatus: implementation candidate, in-game acceptance pending.\n\n## In-game evidence\n0658 successfully installed and rendered the stair, but the screenshot showed it entirely in the black exterior to the right of the WizardHouse room. This proves `Buildings width - 1` is a legal layer coordinate but not the visible interior boundary.\n\n## Fix\n`ResolvePreferredWizardStairTile` now scans the active `Back` + `Buildings` layers at the stair landing row. It chooses the rightmost tile that:\n- has a real `Back` floor tile,\n- has no blocking `Buildings` tile at the landing, and\n- is immediately beside either void or a wall/building tile on its right.\n\nA second pass chooses the rightmost real floor tile if the boundary condition is unavailable. Only if a replacement lacks standard layers does the fallback stay one tile inside the raw layer edge.\n\nThe resolved coordinate remains the single source of truth for stair visual placement, collision, interaction, ascent and return landing.\n\nNo save schema, progression, card canon, MiMi profile, Community Center stability/dialogue, attic layout, Airship, Hunt Run, Boss Gate, Boss Form, or controller behavior is changed.\n''', encoding='utf-8')

latest = Path('handoff/LATEST_CARDCHA_HANDOFF.md')
latest.write_text('''# Latest Cardcha handoff\n\nCurrent branch: `cardcha-alpha28-0659-wizard-stair-interior-edge-resolver`\nCurrent build: `0.3.0-alpha.28.0.4.14.4.5.12.26`\n\nContinue from:\n`handoff/ALPHA28_0659_WIZARD_STAIR_INTERIOR_EDGE.md`\n\nImportant: in-game acceptance is pending. Do not resume from stale `main`.\n''', encoding='utf-8')

print(json.dumps({
    'version': VERSION,
    'resolver': 'rightmost real Back floor tile adjacent to right wall/void',
    'fallback': 'one tile inside raw layer edge',
}, indent=2))
