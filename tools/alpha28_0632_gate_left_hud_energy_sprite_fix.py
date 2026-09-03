from pathlib import Path
import hashlib
import json
import re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.2'


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def write(rel, text):
    (ROOT / rel).write_text(text, encoding='utf-8')


def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'{label}: anchor not found')
    return text.replace(old, new, 1)


# -----------------------------------------------------------------------------
# Version. Save schema stays 19.
# -----------------------------------------------------------------------------
manifest_path = ROOT / 'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['Version'] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

csproj = ROOT / 'Cardcha.csproj'
s = csproj.read_text(encoding='utf-8')
s = re.sub(r'<Version>[^<]+</Version>', f'<Version>{VERSION}</Version>', s, count=1)
csproj.write_text(s, encoding='utf-8')

(ROOT / 'Directory.Build.targets').write_text(f'''<Project>\n  <PropertyGroup>\n    <Version>{VERSION}</Version>\n  </PropertyGroup>\n\n  <!-- .4.14.4.5.2 Forest gate-left + compact ChaCha HUD + slower energy + sprite repair. -->\n  <Target Name="CardchaAlpha280414452Manifest" BeforeTargets="BeforeBuild">\n    <Exec Command="python3 -c &quot;from pathlib import Path; import re; p=Path(r'$(MSBuildProjectDirectory)/manifest.json'); s=p.read_text(encoding='utf-8'); s=re.sub(r'\\&quot;Version\\&quot;\\s*:\\s*\\&quot;[^\\&quot;]+\\&quot;', '\\&quot;Version\\&quot;: \\&quot;{VERSION}\\&quot;', s, count=1); p.write_text(s, encoding='utf-8')&quot;" />\n  </Target>\n</Project>\n''', encoding='utf-8')

# Keep the console banner truthful if this source carries one.
entry = read('ModEntry.cs')
entry = re.sub(
    r'Cardcha! v0\.3\.0-alpha\.28\.0\.4\.14\.4\.5(?:\.1)?[^"\\n]*TEST',
    f'Cardcha! v{VERSION} GATE HUD ENERGY SPRITE FIX TEST',
    entry,
)
write('ModEntry.cs', entry)


# -----------------------------------------------------------------------------
# Forest Arcane Gate: move farther LEFT and make it proximity-enterable.
# No Forest tiles/collision are edited.
# -----------------------------------------------------------------------------
s = read('Services/AirshipFoundationService.cs')
s = replace_once(
    s,
    '    private const float ForestGateUseDistance = 320f;\n',
    '    private const float ForestGateUseDistance = 320f;\n    private const float ForestGateAutoEnterDistance = 112f;\n',
    'Forest gate auto-enter distance'
)

old_auto = '''        GameLocation? location = Game1.currentLocation;\n        if (location is null)\n            return false;\n\n        Point playerTile = new(\n'''
new_auto = '''        GameLocation? location = Game1.currentLocation;\n        if (location is null)\n            return false;\n\n        // Forest gate remains presentation-only: no collision or map tile mutation.\n        // Walking close to the aperture now behaves like a real portal, which also avoids\n        // action-button reach problems caused by custom Forest fences/trees.\n        if (IsSkyDockLocation(location) && this.Save.Data.AirshipUnlocked)\n        {\n            Point dock = this.ResolveSkyDockTile();\n            if (PlayerIsNear(dock, ForestGateAutoEnterDistance))\n            {\n                GameLocation? interior = this.EnsureSkyDockInteriorLocation();\n                if (interior is null)\n                    return false;\n\n                Point arrival = ResolveSkyDockInteriorArrivalTile(interior);\n                this.WarpGraceUntilMs = Environment.TickCount64 + 850L;\n                Game1.playSound("wand");\n                Game1.warpFarmer(SkyDockInteriorLocationName, arrival.X, arrival.Y, 0);\n                return true;\n            }\n        }\n\n        Point playerTile = new(\n'''
s = replace_once(s, old_auto, new_auto, 'Forest gate proximity transition')

old_resolve = '''        // Player exits the Farm into Forest; the dock should be visible immediately to the left.\n        // Search a compact left-side band instead of claiming a fixed vanilla tile.\n        Point preferred = new(\n            Math.Clamp(farmWarp.X - 7, 2, Math.Max(2, width - 3)),\n            Math.Clamp(farmWarp.Y + 2, 2, Math.Max(2, height - 3))\n        );\n\n        Point? safe = FindSafeDockTile(forest, preferred, farmWarp);\n        this.CachedSkyDockTile = safe ?? preferred;\n        return this.CachedSkyDockTile.Value;\n'''
new_resolve = '''        // User-approved placement: move the Arcane Gate decisively LEFT of the Farm entrance.\n        // Search broadly on the left side and never fall back to a known-blocked preferred tile.\n        Point preferred = new(\n            Math.Clamp(farmWarp.X - 14, 3, Math.Max(3, width - 4)),\n            Math.Clamp(farmWarp.Y + 3, 3, Math.Max(3, height - 4))\n        );\n\n        Point? safe = FindSafeDockTile(forest, preferred, farmWarp);\n        this.CachedSkyDockTile = safe ?? FindLeftDockFallback(forest, preferred, farmWarp);\n        return this.CachedSkyDockTile.Value;\n'''
s = replace_once(s, old_resolve, new_resolve, 'Move Forest gate left')

s = replace_once(
    s,
    '        for (int radius = 0; radius <= 7; radius++)\n',
    '        for (int radius = 0; radius <= 18; radius++)\n',
    'Expand Forest gate search radius'
)
s = replace_once(
    s,
    '                for (int x = Math.Max(2, preferred.X - radius); x <= Math.Min(farmWarp.X - 4, preferred.X + radius); x++)\n',
    '                for (int x = Math.Max(2, preferred.X - radius); x <= Math.Min(farmWarp.X - 9, preferred.X + radius); x++)\n',
    'Keep Forest gate farther left'
)

fallback_anchor = '''        return null;\n    }\n\n    private static bool IsDockFootprintSafe(GameLocation location, Point anchor, Point farmWarp)\n'''
fallback_method = '''        return null;\n    }\n\n    private static Point FindLeftDockFallback(GameLocation forest, Point preferred, Point farmWarp)\n    {\n        int width = forest.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 120;\n        int height = forest.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 120;\n        int maxX = Math.Clamp(farmWarp.X - 9, 3, Math.Max(3, width - 4));\n\n        // A modded Forest can be visually dense enough that no full 3x3 footprint is pristine.\n        // In that case choose the nearest genuinely walkable center on the LEFT, instead of\n        // putting the portal back inside a trunk/fence. Interaction remains collision-free.\n        for (int radius = 0; radius <= 24; radius++)\n        {\n            for (int y = Math.Max(3, preferred.Y - radius); y <= Math.Min(height - 4, preferred.Y + radius); y++)\n            {\n                for (int x = Math.Max(3, preferred.X - radius); x <= Math.Min(maxX, preferred.X + radius); x++)\n                {\n                    if (Math.Abs(x - preferred.X) != radius && Math.Abs(y - preferred.Y) != radius)\n                        continue;\n\n                    Point p = new(x, y);\n                    try\n                    {\n                        Vector2 tile = new(p.X, p.Y);\n                        var buildings = forest.Map?.GetLayer("Buildings");\n                        if (buildings?.Tiles[p.X, p.Y] is not null\n                            || forest.IsTileBlockedBy(tile)\n                            || forest.Objects.ContainsKey(tile)\n                            || forest.terrainFeatures.ContainsKey(tile))\n                        {\n                            continue;\n                        }\n                        return p;\n                    }\n                    catch\n                    {\n                        continue;\n                    }\n                }\n            }\n        }\n\n        // Last resort is still kept left of the Farm warp. This does not alter collision.\n        return new Point(maxX, Math.Clamp(preferred.Y, 3, Math.Max(3, height - 4)));\n    }\n\n    private static bool IsDockFootprintSafe(GameLocation location, Point anchor, Point farmWarp)\n'''
s = replace_once(s, fallback_anchor, fallback_method, 'Forest left fallback')

s = replace_once(
    s,
    '        Point landing = FindClearTileNear(forest, new Point(dock.X + 1, dock.Y + 1));\n',
    '        Point landing = FindClearTileNear(forest, new Point(dock.X, dock.Y + 3));\n',
    'Forest gate return landing'
)
write('Services/AirshipFoundationService.cs', s)


# -----------------------------------------------------------------------------
# ChaCha Boss Energy: user feedback says 100 fills too quickly. Halve gain pace.
# -----------------------------------------------------------------------------
s = read('Services/BossEnergyService.cs')
for old, new, label in [
    ('    private const double RegularKillEnergy = 10d;\n', '    private const double RegularKillEnergy = 5d;\n', 'regular kill energy'),
    ('    private const double BossLikeKillEnergy = 20d;\n', '    private const double BossLikeKillEnergy = 10d;\n', 'boss kill energy'),
    ('    private const double CritLikeEnergy = 1d;\n', '    private const double CritLikeEnergy = 0.5d;\n', 'crit energy'),
    ('    private const double DamagePerEnergy = 100d;\n', '    private const double DamagePerEnergy = 200d;\n', 'damage per energy'),
    ('    private const double MaxDamageEnergyPerHit = 2d;\n', '    private const double MaxDamageEnergyPerHit = 1d;\n', 'damage cap energy'),
]:
    s = replace_once(s, old, new, label)
write('Services/BossEnergyService.cs', s)


# -----------------------------------------------------------------------------
# ChaCha Energy HUD: remove the loud instruction strip; keep title/value + bar.
# -----------------------------------------------------------------------------
s = read('Services/ChaChaBossFormService.cs')
old_border = '''        Color border = this.IsReady\n            ? Color.Lerp(new Color(220, 55, 48), Color.White, pulse * 0.55f)\n            : this.IsActive\n                ? new Color(235, 80, 66)\n                : stageColor * 0.92f;\n'''
new_border = '''        Color border = this.IsActive\n            ? new Color(235, 80, 66)\n            : stageColor * 0.92f;\n'''
s = replace_once(s, old_border, new_border, 'Steady ChaCha HUD border')
s = replace_once(
    s,
    '        Rectangle track = new(rect.X + 12, rect.Y + 29, rect.Width - 24, 12);\n',
    '        Rectangle track = new(rect.X + 12, rect.Y + 28, rect.Width - 24, 10);\n',
    'Compact ChaCha HUD track'
)

detail_start = s.find('        string detail;\n')
detail_end_marker = '    }\n\n    public void OnRenderedWorld'
if detail_start < 0:
    if 'chacha.boss.hint.combo' in s[s.find('public void OnRenderedHud'):s.find('public void OnRenderedWorld')]:
        raise RuntimeError('ChaCha HUD detail block anchor not found')
else:
    detail_end = s.find(detail_end_marker, detail_start)
    if detail_end < 0:
        raise RuntimeError('ChaCha HUD detail block end not found')
    s = s[:detail_start] + s[detail_end:]

s = replace_once(s, '        const int width = 318;\n        const int height = 58;\n', '        const int width = 300;\n        const int height = 46;\n', 'Compact ChaCha HUD rect')
write('Services/ChaChaBossFormService.cs', s)


# -----------------------------------------------------------------------------
# Sprite sheets were already committed as real binary blobs before this finalizer.
# Verify exact repaired pixels so CI cannot silently reintroduce the squashed sources.
# -----------------------------------------------------------------------------
expected = {
    'assets/items.png': 'b64d5e4e2200690eb286cef54f0e666d98bb4af3ef73a5caa41c3a0a27a3b0f8',
    'assets/chacha_skill_materials.png': '8fccb150a4ecfa37ba56db5e4f223e041ae56222407d769a0b66622ad3cc08b1',
    'assets/chacha_skill_icons.png': 'ce9764afc67c66599e83f032e4d560d7f996109fa0ad6c90bffff71ef656a520',
}
for rel, digest in expected.items():
    actual = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
    if actual != digest:
        raise RuntimeError(f'{rel}: repaired sprite SHA mismatch {actual}')

print(f'Applied {VERSION} Gate/HUD/Energy/Sprite fix')
