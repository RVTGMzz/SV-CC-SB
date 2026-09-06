from pathlib import Path
import json
import re
import subprocess

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.11'
BASE_VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.10'
PORTRAIT_SOURCE_REF = 'origin/cardcha-alpha28-0646-mimi-secret-tv-routine'
PORTRAIT_SOURCE_PATH = 'src/Cardcha/assets/mimi_portraits_runtime64.png'

# Version metadata only.
manifest = ROOT / 'manifest.json'
data = json.loads(manifest.read_text(encoding='utf-8-sig'))
data['Version'] = VERSION
manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

for rel in ['Cardcha.csproj', 'Directory.Build.targets']:
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    text = text.replace(BASE_VERSION, VERSION)
    path.write_text(text, encoding='utf-8')

# ---------------------------------------------------------------------------
# 1) MiMi portrait: restore the last known-good native 64x64/frame sheet.
#    It becomes the ONE shared mimi_portraits.png used by Social/Gift Log and dialogue.
#    No outer stroke, no padding, no runtime resize sheet.
# ---------------------------------------------------------------------------
portrait_bytes = subprocess.check_output([
    'git', 'show', f'{PORTRAIT_SOURCE_REF}:{PORTRAIT_SOURCE_PATH}'
])
portrait_path = ROOT / 'assets/mimi_portraits.png'
portrait_path.write_bytes(portrait_bytes)
for obsolete in [ROOT / 'assets/mimi_portraits_runtime64.png', ROOT / 'assets/mimi_npc_portraits.png']:
    if obsolete.exists():
        obsolete.unlink()

mystery_path = ROOT / 'Services/MimiMysteryTownService.cs'
mystery = mystery_path.read_text(encoding='utf-8')
mystery = mystery.replace(
    '// Engine-compatible 64x64 portrait fallback only. Runtime dialogue portraits are generated in memory from MimiPortraitsPath.',
    '// One canonical native Stardew portrait sheet: six 64x64 frames shared by Social/Gift Log and all MiMi dialogue.'
)
mystery = mystery.replace(
    'e.LoadFrom(() => this.GetNativePortraitCompatibilitySheet(), AssetLoadPriority.Medium);',
    'e.LoadFromModFile<Texture2D>(MimiPortraitsPath, AssetLoadPriority.Exclusive);'
)

# Remove obsolete runtime portrait generators safely by matching braces.
def remove_method(source: str, signature: str) -> str:
    start = source.find(signature)
    if start < 0:
        return source
    line_start = source.rfind('\n', 0, start) + 1
    brace = source.find('{', start)
    if brace < 0:
        raise RuntimeError(f'Opening brace not found for {signature}')
    depth = 0
    i = brace
    while i < len(source):
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                while end < len(source) and source[end] in ' \t':
                    end += 1
                if end < len(source) and source[end] == '\r':
                    end += 1
                if end < len(source) and source[end] == '\n':
                    end += 1
                return source[:line_start] + source[end:]
        i += 1
    raise RuntimeError(f'Closing brace not found for {signature}')

mystery = remove_method(mystery, 'private Texture2D GetNativePortraitCompatibilitySheet()')
mystery = remove_method(mystery, 'private static Texture2D CreateRuntimePortraitSheet(Texture2D master)')
mystery_path.write_text(mystery, encoding='utf-8')

# ---------------------------------------------------------------------------
# 2) Wizard stair position: EXACT fixed tile, no map percentages/searches.
#    Screenshot acceptance target: upper-right niche between the two plants.
# ---------------------------------------------------------------------------
home_path = ROOT / 'Services/MimiHomeService.cs'
home = home_path.read_text(encoding='utf-8')
start = home.index('    internal static Point ResolvePreferredWizardStairTile(GameLocation wizard)')
end = home.index('    private static Point ResolveWizardLandingTile', start)
replacement = '''    internal static Point ResolvePreferredWizardStairTile(GameLocation wizard)\n    {\n        // WIZ-02 candidate: exact screenshot-approved upper niche between the two plants.\n        // Absolute world tile by design. No map-size math, safety scan, NPC/object check, or relocation.\n        return new Point(19, 5);\n    }\n\n'''
home = home[:start] + replacement + home[end:]
home_path.write_text(home, encoding='utf-8')

# ---------------------------------------------------------------------------
# 3) Wizard stair layering: split 16x64 art into upper/lower slices and depth-sort
#    at the stair's world Y instead of the old always-front 0.995 overlay.
#    No WizardHouse tiles are removed.
# ---------------------------------------------------------------------------
visual_path = ROOT / 'Services/MimiAtticVisualService.cs'
visual = visual_path.read_text(encoding='utf-8')
method_start = visual.index('    private void DrawStairMarker(SpriteBatch batch, Point tile)')
method_end = visual.index('    private static AtticLayout GetLayout', method_start)
new_draw = '''    private void DrawStairMarker(SpriteBatch batch, Point tile)\n    {\n        try\n        {\n            Texture2D staircase = this.Helper.ModContent.Load<Texture2D>(StairSpritePath);\n\n            // The 16x64 staircase is four world tiles tall at 4x scale. Its foot ends at tile.Y.\n            // Split it so the lower segment participates in normal Y-depth instead of forcing the\n            // entire ladder over the farmer with the old fixed 0.995f layer depth.\n            Rectangle upperSource = new(0, 0, staircase.Width, 48);\n            Rectangle lowerSource = new(0, 48, staircase.Width, 16);\n            Vector2 upperWorld = new(tile.X * 64f, (tile.Y - 4) * 64f);\n            Vector2 lowerWorld = new(tile.X * 64f, (tile.Y - 1) * 64f);\n            Vector2 upperScreen = Game1.GlobalToLocal(Game1.viewport, upperWorld);\n            Vector2 lowerScreen = Game1.GlobalToLocal(Game1.viewport, lowerWorld);\n\n            float upperDepth = Math.Clamp(((tile.Y - 1) * 64f - 8f) / 10000f, 0.001f, 0.90f);\n            float lowerDepth = Math.Clamp((tile.Y * 64f - 8f) / 10000f, 0.001f, 0.90f);\n\n            batch.Draw(staircase, upperScreen, upperSource, Color.White, 0f, Vector2.Zero, 4f, SpriteEffects.None, upperDepth);\n            batch.Draw(staircase, lowerScreen, lowerSource, Color.White, 0f, Vector2.Zero, 4f, SpriteEffects.None, lowerDepth);\n        }\n        catch\n        {\n            // The actual warp still works if the visual asset can't be loaded.\n        }\n    }\n\n'''
visual = visual[:method_start] + new_draw + visual[method_end:]
visual_path.write_text(visual, encoding='utf-8')

print(json.dumps({
    'version': VERSION,
    'scope': [
        'MiMi one native 64x64/frame portrait sheet',
        'Wizard stair fixed absolute tile (19,5)',
        'Wizard stair split world-Y depth rendering'
    ],
    'portraitSource': f'{PORTRAIT_SOURCE_REF}:{PORTRAIT_SOURCE_PATH}',
    'portraitDestination': str(portrait_path),
    'wizardStairTile': [19, 5],
    'unrelatedSystemsTouched': False
}, indent=2))
