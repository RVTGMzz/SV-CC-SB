from pathlib import Path
import base64
import json
import re

ROOT = Path("src/Cardcha")
VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.38"
PREV = "0.3.0-alpha.28.0.4.14.4.5.12.37"

def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"0669 anchor missing: {label}")
    return text.replace(old, new, 1)

def regex_once(text: str, pattern: str, replacement: str, label: str) -> str:
    if replacement in text:
        return text
    out, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"0669 regex anchor missing: {label}")
    return out

# -----------------------------------------------------------------------------
# Version
# -----------------------------------------------------------------------------
manifest_path = ROOT / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["Version"] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

for rel in ["Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
    p = ROOT / rel
    s = p.read_text(encoding="utf-8").replace(PREV, VERSION)
    if rel == "ModEntry.cs":
        s = s.replace("COMBAT HUD RUNTIME COVERAGE HOTFIX TEST", "VISUAL AUTH PASS TEST")
    p.write_text(s, encoding="utf-8")

# -----------------------------------------------------------------------------
# Authored binary art generated specifically for 0669.
# -----------------------------------------------------------------------------
assets = {
    ROOT / "assets/bosses/verdant_guardian/arena/verdant_seed_totem.png": "iVBORw0KGgoAAAANSUhEUgAAAIAAAAAwCAYAAADZ9HK+AAAED0lEQVR4nO2az0sWQRjHvyv1CiKohD+g6FBSlvCi8r4qRYUHKUHrYN08eBQ6iP+Bp67iQfDoQehQQqZg4OHFJMiUFCGUqCgqSz34SiH5Gm2HeKZ59913353d2V115gPDvju7zHd+PPPMs/MOoNFoNBqNRqPRaDQajUYjiWVzzFw2x8yo66Gxp8jpoejg9T+7G+lAq67vBUcDsKNruM2xkdZOaDR6jUaj1xDVkaUvm6j1ZeNoANbBc2o83/CgOkF1/SBw7QH4xheaBUBuh/BJvJpHX9+LZhicsGZYGzfVnzLcNFgWUetb6xKlfhgIxwAE3yl2Fj5867EBAPG+RODu+Cjo+/VAQVHQAOJ9CXOqPyUtiBMlbP2u4TaTUhT6YZOzBIjQNdxmnrt4KiefrJ9IPfnIfq+OLkn9IlBZXwY5HmCqP2V8WvsBSny+XQEvBldy8jqvXzApiVZIdf2wcRUD5GvMt4efAdh3gkxU1w8SR3dk12ij+zSA/43vnOnGdMcEAODqYAPeP1jNKWf6+VtPbs+NfnKoBYsDC8dSPww8fQXwg89fw5oJfOfzV1X0ZeLaMmk2fM/8+Xc/04075ZfY88n0GvMENbEi6VZv1U8OtSC2u8+eZ8qK2Uw8jvr5SLTWmksv33nWEvIA/ODbQfn0nmz4zreD8qPQn+uZx952BnvbmUD07fYzEq21Jl0vnz/Lkki5rg2g0OAT9JwqJ4tCg0/Q86j0CRn68b6ESYnureXXVVX40hBaAqxGYF0CALBlwOqW6G9lr/8M8vrJoRbM9cyzZ+0jzciUFQMAc8N+3OJh0rfO/NhKGgCwt51heU311Vjf2mH3Itq2HiDfOYCamDuH4fY9UfKVO3v/lRL6NPjWWf/6zSbqqipYvoj38VRTmuVu8wG55wIWBxZwY/wa2keac/LDIEx9fucw01AOAFjf2kFTfTWa6quz3iUv4NsDOA0WWfd0xwQm02ss8V8AQULlLw4sMLdL9yro80bA42XwAY8eIF8jg278YdD/8PUXi/bD0ue9wO/ZLan6nmtcEytis366YyK0wef1yRWXVMZC1wcQqn58w0B8I3ty01JQUhnzXK7wmsxvj/Lfu2xpCHgDRFX9ntvJrMAund7N0ucDw/Gni/5iALdQo6OYfVpfjr7vmkfVeK0vRz/a2msiRxuA4rgOFvruNZgA8GVzz/G9M9UlAIDRRytSgyHV9e2CQJ7y8jL2u7T4wLW+rzOBmvAoLT4AUNgARdEGcEwgj0AeyC06BlCcgusEbXyIWha5Kr8bI6rr09pPS4Bbfu6fBFB4U0h7AMVxNICbV+p9n2rxU4bWD17fdRAoO/oURXV9cumy0UuA4tgGCLIPVBJuDyto/fD0tQdQHG0AGo3K/AX+Ue+xDcB53AAAAABJRU5ErkJggg==",
    ROOT / "assets/region1_environment_decor.png": "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",
    ROOT / "assets/airship_gate_auth.png": "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",
}
for path, payload in assets.items():
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(payload))

# -----------------------------------------------------------------------------
# Combat actor auth: keep gameplay proxies visible to the engine, hide ONLY draw.
# This aligns hitbox/AI/death with the custom art players actually see.
# -----------------------------------------------------------------------------
p = ROOT / "Patches" / "VerdantGuardianProxyDrawPatch.cs"
s = p.read_text(encoding="utf-8")
s = replace_once(
    s,
    "        => !__instance.modData.ContainsKey(VerdantGuardianBossService.BossMarkerKey)\n"
    "           && !__instance.modData.ContainsKey(VerdantGuardianBossService.TotemMarkerKey);",
    "        => !__instance.modData.ContainsKey(VerdantGuardianBossService.BossMarkerKey)\n"
    "           && !__instance.modData.ContainsKey(VerdantGuardianBossService.TotemMarkerKey)\n"
    "           && !__instance.modData.ContainsKey(VerdantGuardianBossService.BossAddMarkerKey);",
    "GreenSlime draw suppression includes boss adds"
)
p.write_text(s, encoding="utf-8")

p = ROOT / "Services" / "VerdantGuardianBossService.cs"
s = p.read_text(encoding="utf-8")

s = replace_once(
    s,
    "        this.UpdateTotemAnchors();\n        this.ObserveTotemBreaks(now);\n",
    "        this.UpdateTotemAnchors();\n        this.ObserveTotemBreaks(now);\n        this.ReassertBossActorAuth();\n",
    "boss actor auth tick"
)

old_leaf = """            if (string.Equals(kind, LeafWispId, StringComparison.OrdinalIgnoreCase))
            {
                add = new Bug(pos, 0);
                add.MaxHealth = this.Phase switch { 1 => 34, 2 => 46, _ => 58 };
                add.Speed = this.Phase switch { 1 => 4, 2 => 5, _ => 5 };
            }
            else
            {
                add = new GreenSlime(pos, 0);
                add.MaxHealth = this.Phase switch { 1 => 50, 2 => 68, _ => 84 };
                add.Speed = this.Phase switch { 1 => 2, 2 => 3, _ => 3 };
                kind = BriarlingId;
            }
"""
new_leaf = """            if (string.Equals(kind, LeafWispId, StringComparison.OrdinalIgnoreCase))
            {
                // 0669 auth: use the same stable, targetable GreenSlime actor family for both
                // custom summon silhouettes. Custom art hides the proxy draw, never the actor.
                add = new GreenSlime(pos, 0);
                add.MaxHealth = this.Phase switch { 1 => 34, 2 => 46, _ => 58 };
                add.Speed = this.Phase switch { 1 => 4, 2 => 5, _ => 5 };
            }
            else
            {
                add = new GreenSlime(pos, 0);
                add.MaxHealth = this.Phase switch { 1 => 50, 2 => 68, _ => 84 };
                add.Speed = this.Phase switch { 1 => 3, 2 => 4, _ => 4 };
                kind = BriarlingId;
            }
"""
s = replace_once(s, old_leaf, new_leaf, "summon stable actor family")

s = replace_once(
    s,
    "            // Hide only the vanilla proxy art. AI, collision, damage and death routing remain native/stable.\n"
    "            add.isInvisible.Value = true;\n",
    "            // 0669: invisibility must NEVER disable targetability/AI. Harmony suppresses only draw.\n"
    "            add.isInvisible.Value = false;\n",
    "summon engine visibility"
)

s = replace_once(
    s,
    "            proxy.isInvisible.Value = true;\n            arena.characters.Add(proxy);\n",
    "            // 0669: the proxy stays active/targetable; only its vanilla draw is suppressed.\n"
    "            proxy.isInvisible.Value = false;\n            arena.characters.Add(proxy);\n",
    "totem engine visibility"
)

auth_method = """    private void ReassertBossActorAuth()
    {
        GameLocation? arena = Game1.getLocationFromName(LocationName);
        if (arena is null) return;

        foreach (Monster actor in arena.characters.OfType<Monster>())
        {
            if (actor.modData.ContainsKey(TotemMarkerKey))
            {
                // Stationary objective: targetable/damageable, never an invisible engine actor.
                actor.isInvisible.Value = false;
                actor.Speed = 0;
                continue;
            }

            if (!actor.modData.ContainsKey(BossAddMarkerKey) || actor.Health <= 0)
                continue;

            actor.isInvisible.Value = false;
            if (actor.modData.TryGetValue(BossAddTypeKey, out string? kind)
                && string.Equals(kind, LeafWispId, StringComparison.OrdinalIgnoreCase))
            {
                actor.Speed = Math.Max(actor.Speed, this.Phase switch { 1 => 4, 2 => 5, _ => 5 });
            }
            else
            {
                actor.Speed = Math.Max(actor.Speed, this.Phase switch { 1 => 3, 2 => 4, _ => 4 });
            }
        }
    }

"""
s = replace_once(
    s,
    "    private void BeginDefeat(long now)\n",
    auth_method + "    private void BeginDefeat(long now)\n",
    "boss actor auth method"
)
p.write_text(s, encoding="utf-8")

# -----------------------------------------------------------------------------
# Totem visual = hitbox. Remove monster-like HP bars; durability is shown by art.
# -----------------------------------------------------------------------------
p = ROOT / "Services" / "VerdantGuardianArenaPolishService.cs"
s = p.read_text(encoding="utf-8")

new_draw_totems = """    private void DrawObelisks(SpriteBatch batch)
    {
        Texture2D? texture = this.Load("verdant_seed_totem.png");
        if (texture is null || texture.Width < 128 || texture.Height < 48) return;

        Monster[] living = this.Boss.VisualTotems;
        HashSet<int> livingIndices = new();
        foreach (Monster totem in living)
        {
            if (!totem.modData.TryGetValue(VerdantGuardianBossService.TotemIndexKey, out string? raw)
                || !int.TryParse(raw, out int index))
                index = 0;

            index = Math.Clamp(index, 0, ObeliskTiles.Length - 1);
            livingIndices.Add(index);

            float hp = totem.MaxHealth <= 0 ? 0f : Math.Clamp(totem.Health / (float)totem.MaxHealth, 0f, 1f);
            int frame = hp > 0.66f ? 0 : hp > 0.33f ? 1 : 2;
            Rectangle src = new(frame * 32, 0, 32, 48);

            // Critical 0669 auth rule: art follows the ACTUAL gameplay proxy position.
            Vector2 world = totem.Position + new Vector2(32f, 64f);
            Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
            float pulse = 0.97f + 0.025f * (float)Math.Sin(Environment.TickCount64 / 240d + index);
            float flash = index == this.Boss.VisualLastTotemHitIndex
                && Environment.TickCount64 - this.Boss.VisualLastTotemHitAtMs < 520 ? 0.90f : 0f;
            Color tint = Color.Lerp(Color.White, new Color(255, 237, 156), flash);
            float layer = Math.Clamp((world.Y + 56f) / 10000f, 0f, 0.94f);

            batch.Draw(texture, local, src, tint, 0f, new Vector2(16f, 47f),
                2.0f * pulse * (1f + flash * 0.08f), SpriteEffects.None, layer);

            // Objective halo, not a monster HP bar. Cracks/glow in the sprite carry durability.
            int halo = 23 + (int)(2f * Math.Sin(Environment.TickCount64 / 210d + index));
            Color objective = new Color(137, 225, 103) * (0.30f + flash * 0.26f);
            batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - halo, (int)local.Y + 4, halo * 2, 2), objective);
            batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 2, (int)local.Y + 1, 4, 8), objective * 0.72f);

            if (index == this.Boss.VisualLastTotemHitIndex
                && Environment.TickCount64 - this.Boss.VisualLastTotemHitAtMs < 700
                && this.Boss.VisualLastTotemHitDamage > 0)
            {
                string hitText = $"-{this.Boss.VisualLastTotemHitDamage}";
                Vector2 hitSize = Game1.smallFont.MeasureString(hitText);
                batch.DrawString(Game1.smallFont, hitText,
                    new Vector2(local.X - hitSize.X / 2f, local.Y - 78f),
                    new Color(255, 237, 156));
            }
        }

        Rectangle brokenSrc = new(96, 0, 32, 48);
        for (int i = 0; i < ObeliskTiles.Length; i++)
        {
            if (livingIndices.Contains(i)) continue;
            Point tile = ObeliskTiles[i];
            Vector2 world = new(tile.X * 64f + 32f, tile.Y * 64f + 64f);
            Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
            batch.Draw(texture, local, brokenSrc, Color.White * 0.78f, 0f,
                new Vector2(16f, 47f), 2.0f, SpriteEffects.None,
                Math.Clamp((world.Y + 56f) / 10000f, 0f, 0.94f));
        }
    }

"""
s = regex_once(
    s,
    r"    private void DrawObelisks\(SpriteBatch batch\)\n    \{.*?\n    \}\n\n    private void DrawTotemStaggerBurst",
    new_draw_totems + "    private void DrawTotemStaggerBurst",
    "totem visual-auth renderer"
)
p.write_text(s, encoding="utf-8")

# -----------------------------------------------------------------------------
# Summon presentation: smaller/native-feeling art, readable health/death target.
# -----------------------------------------------------------------------------
p = ROOT / "Services" / "VerdantGuardianSummonVisualService.cs"
s = p.read_text(encoding="utf-8")
s = s.replace(
    "        float scale = wisp ? 3.25f : 3.55f;\n",
    "        float scale = wisp ? 2.05f : 2.20f;\n"
)
s = replace_once(
    s,
    "        batch.Draw(texture, local, src, Color.White, 0f, new Vector2(16f, 27f), scale, SpriteEffects.None, layer);\n\n"
    "        if (wisp)\n",
    "        batch.Draw(texture, local, src, Color.White, 0f, new Vector2(16f, 27f), scale, SpriteEffects.None, layer);\n\n"
    "        // Summons are real killable enemies. A compact bar confirms hits without prop-like clutter.\n"
    "        float hp = add.MaxHealth <= 0 ? 0f : Math.Clamp(add.Health / (float)add.MaxHealth, 0f, 1f);\n"
    "        int hpW = wisp ? 38 : 44;\n"
    "        int hpX = (int)local.X - hpW / 2;\n"
    "        int hpY = (int)local.Y + 5;\n"
    "        batch.Draw(Game1.staminaRect, new Rectangle(hpX, hpY, hpW, 4), Color.Black * 0.62f);\n"
    "        batch.Draw(Game1.staminaRect, new Rectangle(hpX + 1, hpY + 1, Math.Max(1, (int)((hpW - 2) * hp)), 2), new Color(178, 224, 122) * 0.90f);\n\n"
    "        if (wisp)\n",
    "summon compact HP confirmation"
)
s = s.replace(
    "            batch.Draw(texture, local, src, Color.White, 0f, new Vector2(16f, 27f), scale, SpriteEffects.None, Math.Min(0.995f, layer + 0.0003f));\n",
    "            batch.Draw(texture, local, src, Color.White * 0.86f, 0f, new Vector2(16f, 27f), scale, SpriteEffects.None, Math.Min(0.995f, layer + 0.0003f));\n"
)
s = s.replace(
    'return $"CustomSummons=ON | Living=[{living}] | Pending={this.Boss.VisualSummonTargets.Length} | ProxyArtHidden=ON | FailedAssets={this.Failed.Count}";',
    'return $"CustomSummons=ON | Living=[{living}] | Pending={this.Boss.VisualSummonTargets.Length} | EngineActorsVisible=YES | ProxyDrawHidden=YES | Killable=YES | FailedAssets={this.Failed.Count}";'
)
p.write_text(s, encoding="utf-8")

# -----------------------------------------------------------------------------
# Airship gate: replace procedural portal tower with one authored compact dock sprite.
# -----------------------------------------------------------------------------
p = ROOT / "Services" / "AirshipFoundationService.cs"
s = p.read_text(encoding="utf-8")
s = replace_once(
    s,
    '    private const string AirshipVisualPath = "assets/airship_visual.png";\n',
    '    private const string AirshipVisualPath = "assets/airship_visual.png";\n'
    '    private const string AirshipGateVisualPath = "assets/airship_gate_auth.png";\n',
    "airship gate asset path"
)
s = replace_once(
    s,
    "    private Texture2D? AirshipVisual;\n",
    "    private Texture2D? AirshipVisual;\n"
    "    private Texture2D? AirshipGateVisual;\n"
    "    private bool AirshipGateVisualLoadFailed;\n",
    "airship gate texture fields"
)

new_gate_method = """    private void DrawSkyDock(SpriteBatch batch, Point tile)
    {
        Texture2D? gate = this.GetAirshipGateVisual();
        if (gate is null)
            return;

        // 0669: one compact authored boarding object. No procedural tower, no giant portal glass.
        Vector2 world = new(tile.X * 64f + 32f, tile.Y * 64f + 70f);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
        float pulse = 0.97f + 0.025f * (float)Math.Sin(Environment.TickCount64 / 420d);
        float layer = Math.Clamp((world.Y + 18f) / 10000f, 0f, 0.94f);
        batch.Draw(gate, local, null, Color.White, 0f,
            new Vector2(gate.Width / 2f, gate.Height - 10f), 1.48f * pulse,
            SpriteEffects.None, layer);

        // Small ground confirmation only. The art itself communicates "boarding gate".
        Color warm = new Color(231, 190, 111) * 0.42f;
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 42, (int)local.Y - 7, 84, 3), warm);
    }

    private Texture2D? GetAirshipGateVisual()
    {
        if (this.AirshipGateVisual is not null && !this.AirshipGateVisual.IsDisposed)
            return this.AirshipGateVisual;
        if (this.AirshipGateVisualLoadFailed)
            return null;

        try
        {
            this.AirshipGateVisual = this.Helper.ModContent.Load<Texture2D>(AirshipGateVisualPath);
            return this.AirshipGateVisual;
        }
        catch (Exception ex)
        {
            this.AirshipGateVisualLoadFailed = true;
            this.Monitor.Log($"0669 Airship gate visual unavailable: {ex.GetType().Name}: {ex.Message}", LogLevel.Warn);
            return null;
        }
    }

"""
s = regex_once(
    s,
    r"    private void DrawSkyDock\(SpriteBatch batch, Point tile\)\n    \{.*?\n    \}\n\n    private void DrawSkyDockInteriorDetails",
    new_gate_method + "    private void DrawSkyDockInteriorDetails",
    "authored Forest gate renderer"
)
p.write_text(s, encoding="utf-8")

# -----------------------------------------------------------------------------
# Sky Dock/Airship rooms: fewer, purposeful prop clusters. Region I: organic atlas/layout.
# -----------------------------------------------------------------------------
p = ROOT / "Services" / "AirshipInteriorStardewRenderer.cs"
s = p.read_text(encoding="utf-8")
s = regex_once(
    s,
    r"    private static void DrawDeckStardewDecor\(SpriteBatch batch\)\n    \{.*?\n    \}\n\n    private static void DrawDockStardewDecor",
    """    private static void DrawDeckStardewDecor(SpriteBatch batch)
    {
        Texture2D? atlas = GetHubDecorAtlas();
        if (atlas is null) return;

        // 0669 foundation: grouped by purpose instead of scattered test props.
        // Navigation/work cluster.
        DrawDecor(batch, atlas, 2, 0, new Point(4, 6), 1.75f);
        DrawDecor(batch, atlas, 0, 1, new Point(7, 6), 1.75f);
        DrawDecor(batch, atlas, 1, 2, new Point(5, 9), 1.65f);

        // Central communal/helm cluster.
        DrawDecor(batch, atlas, 1, 1, new Point(12, 8), 2.35f, 92, 56);
        DrawDecor(batch, atlas, 3, 0, new Point(10, 10), 1.70f);

        // Maintenance/storage cluster.
        DrawDecor(batch, atlas, 3, 2, new Point(18, 8), 1.75f);
        DrawDecor(batch, atlas, 0, 0, new Point(20, 10), 1.65f);
        DrawDecor(batch, atlas, 2, 2, new Point(19, 5), 1.65f);
    }

    private static void DrawDockStardewDecor""",
    "deck purposeful clusters"
)
s = regex_once(
    s,
    r"    private static void DrawDockStardewDecor\(SpriteBatch batch\)\n    \{.*?\n    \}\n\n    private static void DrawDecor",
    """    private static void DrawDockStardewDecor(SpriteBatch batch)
    {
        Texture2D? atlas = GetHubDecorAtlas();
        if (atlas is null) return;

        // Waiting/storage side.
        DrawDecor(batch, atlas, 0, 0, new Point(4, 10), 1.70f);
        DrawDecor(batch, atlas, 2, 1, new Point(6, 10), 1.65f);
        DrawDecor(batch, atlas, 0, 2, new Point(6, 12), 1.60f);

        // Route desk in one readable cluster.
        DrawDecor(batch, atlas, 3, 1, new Point(8, 6), 1.70f);
        DrawDecor(batch, atlas, 1, 2, new Point(9, 8), 1.60f);

        // Boarding side, kept visually open.
        DrawDecor(batch, atlas, 2, 2, new Point(22, 10), 1.65f);
        DrawDecor(batch, atlas, 1, 0, new Point(24, 11), 1.65f);
    }

    private static void DrawDecor""",
    "dock purposeful clusters"
)
# Tone down the videogame-ring boarding marker.
s = s.replace(
    "        DrawRect(batch, new Rectangle((int)bay.X - 38, (int)bay.Y - 18, 76, 36), teal * 0.08f);\n"
    "        DrawPixelRing(batch, bay, 20, teal * 0.56f);\n"
    "        DrawDiamond(batch, bay, 8, teal * 0.70f);\n",
    "        DrawRect(batch, new Rectangle((int)bay.X - 30, (int)bay.Y - 7, 60, 3), teal * 0.28f);\n"
    "        DrawDiamond(batch, bay + new Vector2(0f, -5f), 5, teal * 0.58f);\n"
)
p.write_text(s, encoding="utf-8")

p = ROOT / "Services" / "Region1StardewDecorRenderer.cs"
p.write_text("""using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// 0669 foundation pass: room-specific organic edge clusters using an authored 8-cell forest atlas.
/// It intentionally avoids repeating the same staircase/grid silhouette in every Hunt Run room.
/// </summary>
internal static class Region1StardewDecorRenderer
{
    private const string AtlasPath = "assets/region1_environment_decor.png";
    private const int CellSize = 32;
    private const int CellCount = 8;
    private static Texture2D? Atlas;
    private static bool LoadFailed;

    public static void Draw(SpriteBatch batch, GameLocation room, int roomIndex)
    {
        Texture2D? atlas = GetAtlas();
        if (atlas is null) return;

        int width = room.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 28;
        int height = room.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 20;

        Point[] points = roomIndex switch
        {
            0 => new[] { new Point(3,4), new Point(7,3), new Point(width-5,5), new Point(5,height-4), new Point(width-8,height-3), new Point(width-3,height-6) },
            1 => new[] { new Point(2,5), new Point(6,3), new Point(width-4,4), new Point(width-7,7), new Point(4,height-5), new Point(width-5,height-4) },
            2 => new[] { new Point(4,3), new Point(9,4), new Point(width-6,3), new Point(width-3,8), new Point(3,height-4), new Point(width-9,height-3) },
            3 => new[] { new Point(3,6), new Point(6,3), new Point(10,5), new Point(width-4,5), new Point(width-7,height-4), new Point(5,height-3) },
            4 => new[] { new Point(2,4), new Point(8,3), new Point(width-5,3), new Point(width-3,7), new Point(6,height-4), new Point(width-8,height-3) },
            _ => new[] { new Point(4,4), new Point(8,3), new Point(width-6,4), new Point(3,height-5), new Point(width-4,height-5), new Point(width-9,height-3) },
        };

        for (int i = 0; i < points.Length; i++)
        {
            Point tile = points[i];
            int sprite = Math.Abs(roomIndex * 5 + i * 3) % CellCount;
            Rectangle src = new(sprite * CellSize, 0, CellSize, CellSize);
            Vector2 world = new(tile.X * 64f + 32f, tile.Y * 64f + 58f);
            Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
            float scale = 1.72f + (sprite % 3) * 0.14f;
            float layer = Math.Clamp((world.Y + 18f) / 10000f, 0.01f, 0.88f);
            batch.Draw(atlas, local, src, Color.White, 0f, new Vector2(16f,31f), scale, SpriteEffects.None, layer);
        }
    }

    private static Texture2D? GetAtlas()
    {
        if (Atlas is not null && !Atlas.IsDisposed) return Atlas;
        Atlas = null;
        if (LoadFailed || ModEntry.StaticHelper is null) return null;
        try
        {
            Atlas = ModEntry.StaticHelper.ModContent.Load<Texture2D>(AtlasPath);
            return Atlas;
        }
        catch
        {
            LoadFailed = true;
            return null;
        }
    }
}
""", encoding="utf-8")

# -----------------------------------------------------------------------------
# Handoff
# -----------------------------------------------------------------------------
handoff = Path("handoff/ALPHA28_0669_VISUAL_AUTH_PASS.md")
handoff.write_text("""# Alpha28 0669 - Visual / Auth Pass

Build: `0.3.0-alpha.28.0.4.14.4.5.12.38`
Branch: `cardcha-alpha28-0669-visual-auth-pass`
Status: CI/package pending; in-game visual acceptance required.

## Scope
### 1. Combat actor auth
- Totem and summon gameplay proxies are no longer `isInvisible`.
- Harmony suppresses GreenSlime proxy DRAW only for Boss, Totem and Boss Add markers.
- Both Briarling and Leaf Wisp use stable targetable GreenSlime actor proxies; custom art remains authoritative.
- Summon custom art is reduced toward native Stardew scale and gets a compact HP confirmation bar.
- Totem art follows the actual proxy position.
- Totem monster-style HP bars are removed; damage states are authored into the 4-frame seed-effigy sprite.
- Totem balance remains frozen: 4 x 90 HP, barrier 15/10/6/3/0%, final stagger 1.2s.

### 2. Airship gate visual fix
- Procedural oversized portal tower is replaced by a compact authored boarding-gate sprite.
- Forest gate anchor, interaction radius and collision contract remain unchanged.
- Gate still uses the existing farmer-depth patch.

### 3. Sky Dock + map polish foundation
- Airship Deck and Sky Dock props are grouped into purposeful clusters rather than scattered test props.
- Boarding marker is reduced to a small ground confirmation.
- Region I Hunt Run uses an 8-cell authored environment atlas and room-specific asymmetric edge clusters.
- This is a foundation pass, not the final Region I map redraw.

## Preserved
- 0668C physical Hunt Run Lost Cache.
- 0668B timed combat HUD / Adrenaline runtime coverage.
- Boss I 1600 HP and 0665 damage/cooldown profile.
- Save schema 19, 76 active cards / 80 source entries, controller semantics, MiMi/ChaCha locked contracts.

## Acceptance
1. `cardcha_test_boss1`, then `cardcha_boss1_summons`: Briarling/Leaf Wisp must move under native actor AI, take damage and die.
2. Totem sprite, hit feedback and damage target must occupy the same place. No monster-style HP bar under decorative pillars.
3. Break all four Totems and confirm Barrier reduction + final 1.2s stagger still works.
4. `cardcha_test_gate`: Forest boarding gate must render as one compact authored object with correct player depth.
5. `cardcha_test_airship`: inspect Sky Dock and Deck for reduced scatter/placeholder feel.
6. Run several Hunt Run rooms and judge only the visible 0669 foundation: less repetition, more organic edge dressing.
7. Lost Cache remains a physical interactable chest.
8. Adrenaline timed HUD still appears for ~3 seconds after kill.

## Next
Do not claim the full boss/ChaCha concept art overhaul is finished in 0669. If this auth/foundation pass is accepted, the next visual build can focus on native-size Verdant Guardian + Guardian Rabbit authored animation sets.
""", encoding="utf-8")

Path("handoff/LATEST_CARDCHA_HANDOFF.md").write_text(
    "# Latest Cardcha Handoff\n\n"
    "Current branch: `cardcha-alpha28-0669-visual-auth-pass`\n"
    "Current build: `0.3.0-alpha.28.0.4.14.4.5.12.38`\n"
    "Continue from: `handoff/ALPHA28_0669_VISUAL_AUTH_PASS.md`\n\n"
    "Do not resume from stale `main`, 0668B, or 0668C.\n",
    encoding="utf-8"
)

print("0669 visual/auth generator complete")
