from pathlib import Path
import hashlib
import json

ROOT = Path('src/Cardcha')
BASE_VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.12'
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.13'
WALK_SHA256 = '04ff1cbf031c2be0a21f114b8f8eb6f8850bb800eeabd4c27df036d7b23d4fb7'

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

walk = ROOT / 'assets/mimi_walk.png'
walk_hash = hashlib.sha256(walk.read_bytes()).hexdigest()
if walk_hash != WALK_SHA256:
    raise RuntimeError(f'mimi_walk.png drifted: {walk_hash}')

world_path = ROOT / 'Services/WorldActorService.cs'
world = world_path.read_text(encoding='utf-8')
old = 'private const string MimiProfileSheetPath = "assets/mimi_profile.png";'
new = 'private const string MimiProfileSheetPath = "assets/mimi_walk.png";'
if old not in world:
    raise RuntimeError('MimiProfileSheetPath base line not found')
world = world.replace(old, new)
world_path.write_text(world, encoding='utf-8')

profile = ROOT / 'assets/mimi_profile.png'
if profile.exists():
    profile.unlink()

mystery_path = ROOT / 'Services/MimiMysteryTownService.cs'
mystery = mystery_path.read_text(encoding='utf-8')
old_rect = 'SetRectangleProperty(mimi, "MugShotSourceRect", 8, 0, 16, 24);'
new_rect = 'SetRectangleProperty(mimi, "MugShotSourceRect", 0, 192, 16, 24);'
if old_rect not in mystery:
    raise RuntimeError('0648F MugShotSourceRect not found')
mystery = mystery.replace(old_rect, new_rect)
mystery_path.write_text(mystery, encoding='utf-8')

home_path = ROOT / 'Services/MimiHomeService.cs'
home = home_path.read_text(encoding='utf-8')
old_stair = 'return new Point(11, 15);'
new_stair = 'return new Point(8, 15);'
if old_stair not in home:
    raise RuntimeError('0648F fixed stair tile not found')
home = home.replace(old_stair, new_stair, 1)
home_path.write_text(home, encoding='utf-8')

visual_path = ROOT / 'Services/MimiAtticVisualService.cs'
visual = visual_path.read_text(encoding='utf-8')
visual = visual.replace('this.DrawStairMarker(e.SpriteBatch, stair);', 'this.DrawStairMarker(e.SpriteBatch, location, stair);')
start = visual.index('    private void DrawStairMarker(SpriteBatch batch, Point tile)')
end = visual.index('    private static AtticLayout GetLayout', start)
replacement = '''    private void DrawStairMarker(SpriteBatch batch, GameLocation location, Point tile)\n    {\n        try\n        {\n            Texture2D staircase = this.Helper.ModContent.Load<Texture2D>(StairSpritePath);\n\n            // RenderedWorld is after Stardew draws characters. Draw the ladder as four tile-sized\n            // segments and omit only a segment intersecting a visible character body, so it never\n            // paints over the farmer/NPC while preserving the rest of the staircase.\n            for (int segment = 0; segment < 4; segment++)\n            {\n                Rectangle source = new(0, segment * 16, 16, 16);\n                Vector2 world = new(tile.X * 64f, (tile.Y - 4 + segment) * 64f);\n                Rectangle worldRect = new((int)world.X, (int)world.Y, 64, 64);\n                if (IntersectsVisibleCharacter(location, worldRect))\n                    continue;\n\n                Vector2 screen = Game1.GlobalToLocal(Game1.viewport, world);\n                batch.Draw(staircase, screen, source, Color.White, 0f, Vector2.Zero, 4f, SpriteEffects.None, 0.01f);\n            }\n        }\n        catch\n        {\n            // The warp remains functional if the cosmetic marker cannot be loaded.\n        }\n    }\n\n    private static bool IntersectsVisibleCharacter(GameLocation location, Rectangle stairSegment)\n    {\n        if (Game1.player.currentLocation == location\n            && stairSegment.Intersects(GetCharacterVisualBounds(Game1.player)))\n        {\n            return true;\n        }\n\n        foreach (NPC npc in location.characters)\n        {\n            if (npc.isInvisible.Value)\n                continue;\n            if (stairSegment.Intersects(GetCharacterVisualBounds(npc)))\n                return true;\n        }\n\n        return false;\n    }\n\n    private static Rectangle GetCharacterVisualBounds(Character character)\n    {\n        int x = (int)character.Position.X - 8;\n        int y = (int)character.Position.Y - 96;\n        return new Rectangle(x, y, 80, 160);\n    }\n\n'''
visual = visual[:start] + replacement + visual[end:]
visual_path.write_text(visual, encoding='utf-8')

print(json.dumps({
    'version': VERSION,
    'wizardStairTile': [8, 15],
    'stairShiftTilesLeft': 3,
    'profileSource': 'assets/mimi_walk.png',
    'deleted': ['assets/mimi_profile.png'],
    'smallAvatarMugShotSourceRect': [0, 192, 16, 24],
    'mimiWalkSha256': WALK_SHA256
}, indent=2))
