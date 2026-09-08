from pathlib import Path
from PIL import Image, ImageDraw
import json, re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.30'

# ---------------- version ----------------
manifest_path = ROOT / 'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['Version'] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

for rel in ['Cardcha.csproj', 'Directory.Build.targets']:
    p = ROOT / rel
    s = p.read_text(encoding='utf-8')
    s = re.sub(r'0\.3\.0-alpha\.28\.0\.4\.14\.4\.5\.12\.29', VERSION, s)
    p.write_text(s, encoding='utf-8')

# ---------------- dedicated summon art ----------------
asset_dir = ROOT / 'assets' / 'bosses' / 'verdant_guardian' / 'summons'
asset_dir.mkdir(parents=True, exist_ok=True)

OUTLINE = (29, 43, 32, 255)
BARK = (105, 72, 44, 255)
BARK_HI = (154, 109, 62, 255)
LEAF_DARK = (37, 89, 51, 255)
LEAF = (63, 142, 70, 255)
LEAF_HI = (119, 201, 98, 255)
CORE = (126, 244, 119, 255)
CORE_HI = (231, 255, 178, 255)
WISP = (197, 242, 173, 255)
WISP_HI = (244, 255, 221, 255)
EYE = (30, 48, 33, 255)


def draw_briarling():
    img = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Rows: down, right, up, left. 4 frames each.
    for row in range(4):
        for frame in range(4):
            ox, oy = frame * 32, row * 32
            bob = [0, -1, 0, 1][frame]
            step = [-1, 0, 1, 0][frame]
            d.ellipse((ox+7, oy+27, ox+25, oy+30), fill=(20, 30, 22, 90))
            # thorn crown
            d.polygon([(ox+9,oy+13+bob),(ox+7,oy+7+bob),(ox+12,oy+10+bob)], fill=LEAF_DARK)
            d.polygon([(ox+14,oy+10+bob),(ox+16,oy+4+bob),(ox+18,oy+10+bob)], fill=LEAF_HI)
            d.polygon([(ox+21,oy+12+bob),(ox+25,oy+7+bob),(ox+24,oy+14+bob)], fill=LEAF)
            # bark bud body
            d.ellipse((ox+7, oy+10+bob, ox+25, oy+27+bob), fill=OUTLINE)
            d.ellipse((ox+8, oy+11+bob, ox+24, oy+26+bob), fill=BARK)
            d.arc((ox+10,oy+13+bob,ox+22,oy+24+bob), 195, 345, fill=BARK_HI, width=2)
            # leaf shoulder collar
            d.polygon([(ox+7,oy+17+bob),(ox+11,oy+13+bob),(ox+16,oy+17+bob),(ox+21,oy+13+bob),(ox+25,oy+17+bob),(ox+21,oy+21+bob),(ox+16,oy+19+bob),(ox+11,oy+21+bob)], fill=LEAF_DARK)
            d.polygon([(ox+9,oy+17+bob),(ox+13,oy+14+bob),(ox+15,oy+19+bob),(ox+11,oy+20+bob)], fill=LEAF)
            d.polygon([(ox+23,oy+17+bob),(ox+19,oy+14+bob),(ox+17,oy+19+bob),(ox+21,oy+20+bob)], fill=LEAF_HI)
            # root feet
            d.line((ox+12,oy+25+bob,ox+10+step,oy+29), fill=OUTLINE, width=2)
            d.line((ox+20,oy+25+bob,ox+22-step,oy+29), fill=OUTLINE, width=2)
            if row == 0:
                d.rectangle((ox+11,oy+15+bob,ox+12,oy+16+bob), fill=EYE)
                d.rectangle((ox+20,oy+15+bob,ox+21,oy+16+bob), fill=EYE)
                d.polygon([(ox+16,oy+18+bob),(ox+19,oy+21+bob),(ox+16,oy+24+bob),(ox+13,oy+21+bob)], fill=CORE, outline=CORE_HI)
            elif row == 1:
                d.rectangle((ox+20,oy+15+bob,ox+21,oy+16+bob), fill=EYE)
                d.polygon([(ox+19,oy+19+bob),(ox+22,oy+21+bob),(ox+19,oy+24+bob),(ox+17,oy+21+bob)], fill=CORE, outline=CORE_HI)
            elif row == 3:
                d.rectangle((ox+11,oy+15+bob,ox+12,oy+16+bob), fill=EYE)
                d.polygon([(ox+13,oy+19+bob),(ox+15,oy+21+bob),(ox+13,oy+24+bob),(ox+10,oy+21+bob)], fill=CORE, outline=CORE_HI)
            else:
                d.line((ox+16,oy+13+bob,ox+16,oy+23+bob), fill=BARK_HI, width=2)
                d.polygon([(ox+16,oy+14+bob),(ox+20,oy+18+bob),(ox+16,oy+21+bob),(ox+12,oy+18+bob)], fill=LEAF)
    img.save(asset_dir / 'briarling.png')


def draw_leaf_wisp():
    img = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for row in range(4):
        for frame in range(4):
            ox, oy = frame * 32, row * 32
            bob = [-1, -2, 0, 1][frame]
            tilt = [-1, 0, 1, 0][frame]
            d.ellipse((ox+9, oy+27, ox+23, oy+29), fill=(21, 31, 23, 65))
            # orbiting leaves
            d.polygon([(ox+7+tilt,oy+14),(ox+3+tilt,oy+11),(ox+5+tilt,oy+17)], fill=LEAF)
            d.polygon([(ox+24-tilt,oy+11),(ox+29-tilt,oy+8),(ox+27-tilt,oy+15)], fill=LEAF_HI)
            d.polygon([(ox+23,oy+23+bob),(ox+27,oy+25+bob),(ox+24,oy+28+bob)], fill=LEAF_DARK)
            # luminous seed spirit body
            d.polygon([(ox+16,oy+5+bob),(ox+23,oy+13+bob),(ox+21,oy+22+bob),(ox+16,oy+27+bob),(ox+11,oy+22+bob),(ox+9,oy+13+bob)], fill=OUTLINE)
            d.polygon([(ox+16,oy+6+bob),(ox+22,oy+14+bob),(ox+20,oy+21+bob),(ox+16,oy+25+bob),(ox+12,oy+21+bob),(ox+10,oy+14+bob)], fill=WISP)
            d.polygon([(ox+16,oy+7+bob),(ox+18,oy+13+bob),(ox+16,oy+19+bob),(ox+14,oy+13+bob)], fill=WISP_HI)
            # leaf crest changes with facing but keeps same species silhouette
            if row == 0:
                d.polygon([(ox+15,oy+8+bob),(ox+10,oy+3+bob),(ox+16,oy+5+bob)], fill=LEAF)
                d.polygon([(ox+17,oy+7+bob),(ox+23,oy+3+bob),(ox+18,oy+10+bob)], fill=LEAF_HI)
                d.rectangle((ox+12,oy+15+bob,ox+13,oy+16+bob), fill=EYE)
                d.rectangle((ox+19,oy+15+bob,ox+20,oy+16+bob), fill=EYE)
            elif row == 2:
                d.polygon([(ox+16,oy+8+bob),(ox+11,oy+3+bob),(ox+16,oy+5+bob)], fill=LEAF_DARK)
                d.polygon([(ox+16,oy+8+bob),(ox+22,oy+3+bob),(ox+18,oy+10+bob)], fill=LEAF)
                d.line((ox+16,oy+12+bob,ox+16,oy+21+bob), fill=LEAF_DARK, width=1)
            elif row == 1:
                d.polygon([(ox+17,oy+8+bob),(ox+25,oy+5+bob),(ox+20,oy+11+bob)], fill=LEAF_HI)
                d.rectangle((ox+19,oy+15+bob,ox+20,oy+16+bob), fill=EYE)
            else:
                d.polygon([(ox+15,oy+8+bob),(ox+7,oy+5+bob),(ox+12,oy+11+bob)], fill=LEAF_HI)
                d.rectangle((ox+12,oy+15+bob,ox+13,oy+16+bob), fill=EYE)
            d.point((ox+16,oy+18+bob), fill=CORE_HI)
    img.save(asset_dir / 'leaf_wisp.png')


def draw_portal():
    img = Image.new('RGBA', (128, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for frame in range(4):
        ox = frame * 32
        r = [8, 11, 14, 12][frame]
        for rr, alpha in [(r+4, 45), (r+2, 90), (r, 180)]:
            d.ellipse((ox+16-rr,16-rr//2,ox+16+rr,16+rr//2), outline=(104,238,109,alpha), width=2)
        d.polygon([(ox+16,3),(ox+19,8),(ox+16,11),(ox+13,8)], fill=CORE_HI)
        d.polygon([(ox+6,16),(ox+3,13),(ox+4,19)], fill=LEAF)
        d.polygon([(ox+26,13),(ox+29,10),(ox+28,16)], fill=LEAF_HI)
    img.save(asset_dir / 'summon_portal.png')


draw_briarling()
draw_leaf_wisp()
draw_portal()

# ---------------- boss runtime: deterministic custom summon identities ----------------
boss_path = ROOT / 'Services' / 'VerdantGuardianBossService.cs'
boss = boss_path.read_text(encoding='utf-8')

boss = boss.replace(
    '    public const string BossAddMarkerKey = "Ronvotri.Cardcha/VerdantGuardianAdd";\n',
    '    public const string BossAddMarkerKey = "Ronvotri.Cardcha/VerdantGuardianAdd";\n    public const string BossAddTypeKey = "Ronvotri.Cardcha/VerdantGuardianAddType";\n    public const string BriarlingId = "briarling";\n    public const string LeafWispId = "leaf_wisp";\n',
    1
)

boss = boss.replace(
    '    private Point[] RootTargets = Array.Empty<Point>();\n    private Point VineTarget;\n',
    '    private Point[] RootTargets = Array.Empty<Point>();\n    private Point[] PendingSummonTiles = Array.Empty<Point>();\n    private string[] PendingSummonKinds = Array.Empty<string>();\n    private Point VineTarget;\n',
    1
)

boss = boss.replace(
    '    internal Point[] VisualRootTargets => this.RootTargets;\n    internal Point VisualVineTarget => this.VineTarget;\n',
    '    internal Point[] VisualRootTargets => this.RootTargets;\n    internal Point[] VisualSummonTargets => this.PendingSummonTiles;\n    internal string[] VisualSummonKinds => this.PendingSummonKinds;\n    internal Monster[] VisualAdds => Game1.getLocationFromName(LocationName)?.characters.OfType<Monster>()\n        .Where(m => m.Health > 0 && m.modData.ContainsKey(BossAddMarkerKey)).ToArray() ?? Array.Empty<Monster>();\n    internal Point VisualVineTarget => this.VineTarget;\n',
    1
)

boss = boss.replace(
    '            case VerdantGuardianAttack.SummonAdds:\n                this.State = VerdantGuardianState.SummonAdds; Game1.playSound("leafrustle"); break;\n',
    '            case VerdantGuardianAttack.SummonAdds:\n                this.PrepareSummonPlan();\n                this.State = VerdantGuardianState.SummonAdds; Game1.playSound("leafrustle"); break;\n',
    1
)

boss = boss.replace(
    '        this.RootTargets = Array.Empty<Point>();\n        Game1.playSound("discoverMineral");\n',
    '        this.RootTargets = Array.Empty<Point>();\n        this.PendingSummonTiles = Array.Empty<Point>();\n        this.PendingSummonKinds = Array.Empty<string>();\n        Game1.playSound("discoverMineral");\n',
    1
)

boss = boss.replace(
    '    private void CompleteAttack(long now)\n    {\n        this.RootTargets = Array.Empty<Point>();\n        this.AttackApplied = false;\n',
    '    private void CompleteAttack(long now)\n    {\n        this.RootTargets = Array.Empty<Point>();\n        this.PendingSummonTiles = Array.Empty<Point>();\n        this.PendingSummonKinds = Array.Empty<string>();\n        this.AttackApplied = false;\n',
    1
)

old_spawn = '''    private void SpawnAdds()\n    {\n        GameLocation? arena = Game1.currentLocation;\n        if (arena is null) return;\n        int living = arena.characters.OfType<Monster>().Count(m => m.Health > 0 && m.modData.ContainsKey(BossAddMarkerKey));\n        int desired = this.Phase == 1 ? 2 : 3;\n        int spawnCount = Math.Min(desired, Math.Max(0, MaxActiveAdds - living));\n        if (spawnCount <= 0) return;\n        Point[] points = AddSpawnTiles.OrderBy(_ => this.EncounterRandom.Next()).Take(spawnCount).ToArray();\n        for (int i = 0; i < points.Length; i++)\n        {\n            Vector2 pos = new(points[i].X * 64f, points[i].Y * 64f);\n            Monster add = (i + this.Phase) % 2 == 0 ? new GreenSlime(pos, 0) : new Bug(pos, 0);\n            add.MaxHealth = this.Phase switch { 1 => 45, 2 => 60, _ => 75 };\n            add.Health = add.MaxHealth;\n            add.modData[BossAddMarkerKey] = this.Phase.ToString();\n            arena.characters.Add(add);\n        }\n    }\n'''

new_spawn = '''    private void PrepareSummonPlan()\n    {\n        GameLocation? arena = Game1.currentLocation;\n        if (arena is null)\n        {\n            this.PendingSummonTiles = Array.Empty<Point>();\n            this.PendingSummonKinds = Array.Empty<string>();\n            return;\n        }\n\n        int living = arena.characters.OfType<Monster>()\n            .Count(m => m.Health > 0 && m.modData.ContainsKey(BossAddMarkerKey));\n        int desired = this.Phase == 1 ? 2 : 3;\n        int spawnCount = Math.Min(desired, Math.Max(0, MaxActiveAdds - living));\n        if (spawnCount <= 0)\n        {\n            this.PendingSummonTiles = Array.Empty<Point>();\n            this.PendingSummonKinds = Array.Empty<string>();\n            return;\n        }\n\n        this.PendingSummonTiles = AddSpawnTiles\n            .OrderBy(_ => this.EncounterRandom.Next())\n            .Take(spawnCount)\n            .ToArray();\n\n        string[] phasePool = this.Phase switch\n        {\n            1 => new[] { BriarlingId, BriarlingId },\n            2 => new[] { BriarlingId, LeafWispId, BriarlingId },\n            _ => new[] { LeafWispId, BriarlingId, LeafWispId },\n        };\n        this.PendingSummonKinds = Enumerable.Range(0, spawnCount)\n            .Select(i => phasePool[i % phasePool.Length])\n            .ToArray();\n    }\n\n    private void SpawnAdds()\n    {\n        GameLocation? arena = Game1.currentLocation;\n        if (arena is null) return;\n        if (this.PendingSummonTiles.Length == 0) this.PrepareSummonPlan();\n\n        int count = Math.Min(this.PendingSummonTiles.Length, this.PendingSummonKinds.Length);\n        for (int i = 0; i < count; i++)\n        {\n            Point point = this.PendingSummonTiles[i];\n            string kind = this.PendingSummonKinds[i];\n            Vector2 pos = new(point.X * 64f, point.Y * 64f);\n            Monster add;\n            if (string.Equals(kind, LeafWispId, StringComparison.OrdinalIgnoreCase))\n            {\n                add = new Bug(pos, 0);\n                add.MaxHealth = this.Phase switch { 1 => 38, 2 => 52, _ => 68 };\n                add.Speed = this.Phase switch { 1 => 4, 2 => 5, _ => 6 };\n            }\n            else\n            {\n                add = new GreenSlime(pos, 0);\n                add.MaxHealth = this.Phase switch { 1 => 55, 2 => 75, _ => 95 };\n                add.Speed = this.Phase switch { 1 => 2, 2 => 3, _ => 3 };\n                kind = BriarlingId;\n            }\n\n            add.Health = add.MaxHealth;\n            add.modData[BossAddMarkerKey] = this.Phase.ToString();\n            add.modData[BossAddTypeKey] = kind;\n            // Hide only the vanilla proxy art. AI, collision, damage and death routing remain native/stable.\n            add.isInvisible.Value = true;\n            arena.characters.Add(add);\n        }\n\n        if (count > 0) Game1.playSound("debuffSpell");\n        this.PendingSummonTiles = Array.Empty<Point>();\n        this.PendingSummonKinds = Array.Empty<string>();\n    }\n'''

if old_spawn not in boss:
    raise RuntimeError('0663 SpawnAdds anchor missing')
boss = boss.replace(old_spawn, new_spawn, 1)

boss = boss.replace(
    '    public string Describe()\n    {\n        Monster? boss = this.ResolveBoss();\n',
    '''    public string DebugSummonWave()\n    {\n        if (!this.IsInArena) return "Verdant summon TEST unavailable: enter Boss I arena first.";\n        this.RemoveAdds();\n        this.PrepareSummonPlan();\n        string planned = string.Join(",", this.PendingSummonKinds);\n        this.SpawnAdds();\n        return $"Verdant summon TEST spawned phase {this.Phase}: [{planned}]. Vanilla proxy art is hidden; Cardcha summon visuals are active.";\n    }\n\n    public string Describe()\n    {\n        Monster? boss = this.ResolveBoss();\n''',
    1
)

boss = boss.replace(
    '        return $"Arena={this.IsInArena} | State={this.State} | Phase={this.Phase} | HP={hp} | Cleared={this.Save.Data.Region1BossDefeated} | BossCards=[{unlocked}] | EquippedBoss={this.Save.Data.EquippedBossCardId}";\n',
    '        string adds = string.Join(",", this.VisualAdds.Select(m => m.modData.TryGetValue(BossAddTypeKey, out string? kind) ? kind : "unknown"));\n        return $"Arena={this.IsInArena} | State={this.State} | Phase={this.Phase} | HP={hp} | Adds=[{adds}] | Cleared={this.Save.Data.Region1BossDefeated} | BossCards=[{unlocked}] | EquippedBoss={this.Save.Data.EquippedBossCardId}";\n',
    1
)

boss = boss.replace(
    '        this.RootTargets = Array.Empty<Point>();\n        this.VineTarget = Point.Zero;\n',
    '        this.RootTargets = Array.Empty<Point>();\n        this.PendingSummonTiles = Array.Empty<Point>();\n        this.PendingSummonKinds = Array.Empty<string>();\n        this.VineTarget = Point.Zero;\n',
    1
)

boss_path.write_text(boss, encoding='utf-8')

# ---------------- summon renderer ----------------
summon_visual = r'''using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Monsters;

namespace Cardcha.Services;

/// <summary>
/// 0663 dedicated Cardcha visuals for Verdant Guardian summons. Runtime monsters remain
/// stable GreenSlime/Bug proxies, but their vanilla art is hidden and never presented to players.
/// </summary>
internal sealed class VerdantGuardianSummonVisualService
{
    private const int FrameSize = 32;
    private const string AssetRoot = "assets/bosses/verdant_guardian/summons";
    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly VerdantGuardianBossService Boss;
    private readonly Dictionary<string, Texture2D?> Textures = new(StringComparer.OrdinalIgnoreCase);
    private readonly HashSet<string> Failed = new(StringComparer.OrdinalIgnoreCase);

    public VerdantGuardianSummonVisualService(IModHelper helper, IMonitor monitor, VerdantGuardianBossService boss)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Boss = boss;
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        if (!this.Boss.IsInArena)
            return;

        long now = Environment.TickCount64;
        this.DrawSummonPortals(e.SpriteBatch, now);
        foreach (Monster add in this.Boss.VisualAdds)
            this.DrawSummon(e.SpriteBatch, add, now);
    }

    private void DrawSummonPortals(SpriteBatch batch, long now)
    {
        if (this.Boss.VisualState != VerdantGuardianState.SummonAdds)
            return;
        Texture2D? portal = this.Load("summon_portal.png");
        if (portal is null || portal.Width < 128 || portal.Height < 32)
            return;

        long elapsed = Math.Max(0L, now - this.Boss.VisualStateStartedAtMs);
        int frame = Math.Clamp((int)(elapsed * 4 / 600L), 0, 3);
        Rectangle src = new(frame * FrameSize, 0, FrameSize, FrameSize);
        Point[] tiles = this.Boss.VisualSummonTargets;
        string[] kinds = this.Boss.VisualSummonKinds;
        for (int i = 0; i < tiles.Length; i++)
        {
            Point tile = tiles[i];
            Vector2 world = new(tile.X * 64f + 32f, tile.Y * 64f + 45f);
            Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
            Color tint = i < kinds.Length && string.Equals(kinds[i], VerdantGuardianBossService.LeafWispId, StringComparison.OrdinalIgnoreCase)
                ? new Color(206, 255, 182)
                : new Color(145, 229, 105);
            batch.Draw(portal, local, src, tint, 0f, new Vector2(16f, 16f), 3.7f, SpriteEffects.None,
                Math.Clamp((world.Y + 16f) / 10000f, 0f, 0.985f));
        }
    }

    private void DrawSummon(SpriteBatch batch, Monster add, long now)
    {
        if (!add.modData.TryGetValue(VerdantGuardianBossService.BossAddTypeKey, out string? kind))
            return;

        bool wisp = string.Equals(kind, VerdantGuardianBossService.LeafWispId, StringComparison.OrdinalIgnoreCase);
        string file = wisp ? "leaf_wisp.png" : "briarling.png";
        Texture2D? texture = this.Load(file);
        if (texture is null || texture.Width < 128 || texture.Height < 128)
            return;

        int row = add.FacingDirection switch
        {
            2 => 0,
            1 => 1,
            0 => 2,
            3 => 3,
            _ => 0,
        };
        int phaseOffset = Math.Abs(add.GetHashCode()) % 4;
        int frame = (int)((now / (wisp ? 120L : 155L) + phaseOffset) % 4L);
        Rectangle src = new(frame * FrameSize, row * FrameSize, FrameSize, FrameSize);

        float floatBob = wisp ? (float)Math.Sin((now + phaseOffset * 83L) / 150d) * 5f : 0f;
        Vector2 feet = add.Position + new Vector2(32f, wisp ? 38f + floatBob : 53f);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, feet);
        float scale = wisp ? 3.25f : 3.55f;
        float layer = Math.Clamp((add.Position.Y + 96f) / 10000f, 0f, 0.99f);

        Rectangle shadow = new((int)local.X - (wisp ? 24 : 31), (int)local.Y - 5, wisp ? 48 : 62, wisp ? 9 : 12);
        batch.Draw(Game1.staminaRect, shadow, Color.Black * (wisp ? 0.18f : 0.27f));
        batch.Draw(texture, local, src, Color.White, 0f, new Vector2(16f, 27f), scale, SpriteEffects.None, layer);

        if (wisp)
        {
            float pulse = 0.35f + 0.18f * (float)Math.Abs(Math.Sin(now / 120d));
            int r = 9 + (int)(3 * Math.Abs(Math.Sin(now / 140d)));
            batch.Draw(Game1.staminaRect, new Rectangle((int)local.X-r, (int)local.Y-48-r, r*2, r*2), new Color(137, 247, 126) * pulse);
            batch.Draw(texture, local, src, Color.White, 0f, new Vector2(16f, 27f), scale, SpriteEffects.None, Math.Min(0.995f, layer + 0.0003f));
        }
    }

    public void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e)
    {
        foreach (Texture2D? texture in this.Textures.Values)
            texture?.Dispose();
        this.Textures.Clear();
        this.Failed.Clear();
    }

    public string Describe()
    {
        string living = string.Join(",", this.Boss.VisualAdds.Select(m =>
            m.modData.TryGetValue(VerdantGuardianBossService.BossAddTypeKey, out string? kind) ? kind : "unknown"));
        return $"CustomSummons=ON | Living=[{living}] | Pending={this.Boss.VisualSummonTargets.Length} | ProxyArtHidden=ON | FailedAssets={this.Failed.Count}";
    }

    private Texture2D? Load(string file)
    {
        if (this.Textures.TryGetValue(file, out Texture2D? cached)) return cached;
        if (this.Failed.Contains(file)) return null;
        try
        {
            Texture2D texture = this.Helper.ModContent.Load<Texture2D>($"{AssetRoot}/{file}");
            this.Textures[file] = texture;
            return texture;
        }
        catch (Exception ex)
        {
            if (this.Failed.Add(file))
                this.Monitor.Log($"Verdant summon visual asset '{file}' unavailable: {ex.GetType().Name}: {ex.Message}", LogLevel.Warn);
            this.Textures[file] = null;
            return null;
        }
    }
}
'''
(ROOT / 'Services' / 'VerdantGuardianSummonVisualService.cs').write_text(summon_visual, encoding='utf-8')

# ---------------- ModEntry wiring ----------------
mod_path = ROOT / 'ModEntry.cs'
mod = mod_path.read_text(encoding='utf-8')
mod = mod.replace(
    '    private VerdantGuardianVisualService VerdantGuardianVisual = null!;\n',
    '    private VerdantGuardianVisualService VerdantGuardianVisual = null!;\n    private VerdantGuardianSummonVisualService VerdantSummons = null!;\n',
    1
)
mod = mod.replace(
    '        this.VerdantGuardianVisual = new VerdantGuardianVisualService(helper, this.Monitor, this.VerdantGuardian);\n',
    '        this.VerdantGuardianVisual = new VerdantGuardianVisualService(helper, this.Monitor, this.VerdantGuardian);\n        this.VerdantSummons = new VerdantGuardianSummonVisualService(helper, this.Monitor, this.VerdantGuardian);\n',
    1
)
mod = mod.replace(
    '        helper.Events.GameLoop.ReturnedToTitle += this.VerdantGuardianVisual.OnReturnedToTitle;\n',
    '        helper.Events.GameLoop.ReturnedToTitle += this.VerdantGuardianVisual.OnReturnedToTitle;\n        helper.Events.GameLoop.ReturnedToTitle += this.VerdantSummons.OnReturnedToTitle;\n',
    1
)
mod = mod.replace(
    '        helper.Events.Display.RenderedWorld += this.VerdantGuardianVisual.OnRenderedWorld;\n',
    '        helper.Events.Display.RenderedWorld += this.VerdantGuardianVisual.OnRenderedWorld;\n        helper.Events.Display.RenderedWorld += this.VerdantSummons.OnRenderedWorld;\n',
    1
)
mod = mod.replace(
    '        helper.ConsoleCommands.Add("cardcha_boss1_visual_status", "Show Verdant Guardian visual animation state.", (_, _) => this.Monitor.Log(this.VerdantGuardianVisual.Describe(), LogLevel.Alert));\n',
    '        helper.ConsoleCommands.Add("cardcha_boss1_visual_status", "Show Verdant Guardian visual animation state.", (_, _) => this.Monitor.Log(this.VerdantGuardianVisual.Describe() + "\\n" + this.VerdantSummons.Describe(), LogLevel.Alert));\n        helper.ConsoleCommands.Add("cardcha_boss1_summons", "TEST ONLY: replace current Boss I adds with one custom summon wave.", (_, _) => this.Monitor.Log(this.VerdantGuardian.DebugSummonWave(), LogLevel.Alert));\n',
    1
)
mod = mod.replace(
    'Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.29 GUARDIAN RABBIT BOSS FORM TEST',
    f'Cardcha! {VERSION} VERDANT CUSTOM SUMMONS TEST',
    1
)
mod_path.write_text(mod, encoding='utf-8')

# ---------------- i18n labels ----------------
for lang, entries in {
    'default.json': {
        'boss.verdant.summon.briarling.name': 'Briarling',
        'boss.verdant.summon.briarling.desc': 'A thorn-bud spawned from the Guardian root network.',
        'boss.verdant.summon.leaf-wisp.name': 'Leaf Wisp',
        'boss.verdant.summon.leaf-wisp.desc': 'A fast seed-spirit carried by Verdant resonance.'
    },
    'vi.json': {
        'boss.verdant.summon.briarling.name': 'Briarling',
        'boss.verdant.summon.briarling.desc': 'Một mầm gai được sinh ra từ mạng rễ của Guardian.',
        'boss.verdant.summon.leaf-wisp.name': 'Leaf Wisp',
        'boss.verdant.summon.leaf-wisp.desc': 'Linh thể hạt giống nhanh nhẹn được cộng hưởng Verdant nâng đỡ.'
    },
}.items():
    p = ROOT / 'i18n' / lang
    data = json.loads(p.read_text(encoding='utf-8'))
    data.update(entries)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# ---------------- handoff ----------------
handoff = Path('handoff/ALPHA28_0663_VERDANT_CUSTOM_SUMMONS.md')
handoff.write_text(f'''# Alpha28 0663 - Verdant custom summon mobs\n\nBuild: `{VERSION}`\nBranch: `cardcha-alpha28-0663-verdant-custom-summons`\nStatus: implementation candidate, in-game acceptance pending. 0660-0662 acceptance also remains pending.\n\n## Custom summons\n- Verdant Guardian no longer presents vanilla Green Slime/Bug art for Summon Adds.\n- Two Cardcha-owned summon identities now exist: `briarling` and `leaf_wisp`.\n- Briarling: compact bark/thorn bud, slower and tougher melee proxy.\n- Leaf Wisp: floating seed spirit, faster and lighter Bug proxy.\n- Both use dedicated 4-direction x 4-frame Cardcha sprite sheets. Vanilla proxy art is hidden through `isInvisible`; AI/collision/damage/death routing stay native and stable.\n- Summon cast now pre-plans exact spawn tiles and renders custom Verdant portals at those tiles during the 600ms telegraph.\n\n## Phase composition\n- Phase 1: Briarling + Briarling.\n- Phase 2: Briarling + Leaf Wisp + Briarling.\n- Phase 3: Leaf Wisp + Briarling + Leaf Wisp.\n- Existing hard cap of 4 living Boss I adds remains unchanged.\n- Existing SummonAdds cooldowns remain unchanged.\n\n## Provisional add stats\n- Briarling HP 55/75/95 and Speed 2/3/3 by phase.\n- Leaf Wisp HP 38/52/68 and Speed 4/5/6 by phase.\n- These are test values for later balance acceptance, not a global balance pass.\n\n## Debug\n- `cardcha_boss1_summons` clears current Boss I adds and spawns one deterministic custom wave for the current phase.\n- `cardcha_boss1_visual_status` now includes custom summon renderer state.\n\n## Locked systems preserved\nSave schema 19, 20/40/60/80 milestones, 76 active normal-card audit / 80 stored base IDs, Boss Form 10 sec, Boss Energy x1/3, Guardian Rabbit 0662 runtime, Verdant Colossus 0660, Verdant Core Boss Card 0661, 0659 MiMi stair behavior, MiMi native profile + CC continuity, Region I Hunt Run 4-of-6, Airship route/upgrades, controller mapping and Forest gate are unchanged.\n''', encoding='utf-8')

Path('handoff/LATEST_CARDCHA_HANDOFF.md').write_text(f'''# Latest Cardcha handoff\n\nCurrent branch: `cardcha-alpha28-0663-verdant-custom-summons`\nCurrent build: `{VERSION}`\n\nContinue from:\n`handoff/ALPHA28_0663_VERDANT_CUSTOM_SUMMONS.md`\n\n0660/0661/0662/0663 in-game acceptance is pending. Do not resume from stale `main`.\n''', encoding='utf-8')

print(f'Applied 0663 Verdant custom summons {VERSION}')
