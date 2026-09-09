from pathlib import Path
import json

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.43'
PREV = '0.3.0-alpha.28.0.4.14.4.5.12.42'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'{label}: anchor not found')
    return text.replace(old, new, 1)


def update_text(path: Path, fn):
    text = path.read_text(encoding='utf-8')
    new = fn(text)
    if new != text:
        path.write_text(new, encoding='utf-8')


# Version bump, including the Directory.Build.targets manifest-rewrite target.
for rel in ['manifest.json', 'Cardcha.csproj', 'Directory.Build.targets']:
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    if VERSION not in text:
        if PREV not in text:
            raise RuntimeError(f'version {rel}: {PREV} not found')
        text = text.replace(PREV, VERSION)
        path.write_text(text, encoding='utf-8')


def make_region_map(region: int) -> str:
    width, height = 40, 28
    back = [381] * (width * height)
    buildings = [0] * (width * height)
    front = [0] * (width * height)

    # Cardcha-owned vanilla-tile maps. The routes are intentionally different silhouettes,
    # but all combat lanes remain open so foundation gameplay is never blocked by decorative art.
    for y in range(height):
        for x in range(width):
            i = y * width + x
            if x in (0, width - 1) or y in (0, height - 1):
                buildings[i] = 381
            if ((x * 17 + y * 31 + region * 13) % 23) == 0:
                back[i] = 382

    if region == 3:
        # Mirrorwild: two mirrored north/south trails with a central reflection bridge.
        for y in range(2, height - 2):
            for x in (9, 10, 29, 30):
                back[y * width + x] = 457
        for x in range(9, 31):
            for y in (7, 20):
                back[y * width + x] = 457
        for d in range(0, 8):
            for x, y in ((19 - d, 13 - d // 2), (20 + d, 13 - d // 2),
                         (19 - d, 14 + d // 2), (20 + d, 14 + d // 2)):
                if 1 < x < width - 2 and 1 < y < height - 2:
                    back[y * width + x] = 457
        role = 'region3-mirrorwild|three-wave-expedition|unbanked-extraction'
        layout = 'mirrored-trails|reflection-crossings|south-airship-pad'
    else:
        # Resonance Verge: a strong central lane with three branching resonance spokes.
        for y in range(2, height - 2):
            for x in range(18, 22):
                back[y * width + x] = 457
        for x in range(5, 35):
            y = 8 + abs(20 - x) // 5
            for dy in (0, 1):
                if 1 < y + dy < height - 2:
                    back[(y + dy) * width + x] = 457
        for x in range(7, 33):
            y = 19 - abs(20 - x) // 6
            if 1 < y < height - 2:
                back[y * width + x] = 457
        role = 'region4-resonance-verge|three-wave-expedition|unbanked-extraction'
        layout = 'central-resonance-lane|tricolor-spokes|south-airship-pad'

    def csv(vals):
        return ',\n'.join(','.join(str(vals[y * width + x]) for x in range(width)) for y in range(height))

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" renderorder="right-down" width="{width}" height="{height}" tilewidth="16" tileheight="16" infinite="0" nextlayerid="4" nextobjectid="1">
 <properties>
  <property name="Outdoors" value="T" />
  <property name="CardchaRegionVersion" value="0674" />
  <property name="CardchaRegionRole" value="{role}" />
  <property name="CardchaAssetPolicy" value="cardcha-owned-map|vanilla-tiles-only|native-size-enemies" />
  <property name="CardchaLayout" value="{layout}" />
 </properties>
 <tileset firstgid="1" name="spring_outdoorsTileSheet" tilewidth="16" tileheight="16" tilecount="1975" columns="25">
  <image source=".spring_outdoorsTileSheet.png" width="400" height="1264" />
 </tileset>
 <layer id="1" name="Back" width="{width}" height="{height}">
  <data encoding="csv">{csv(back)}</data>
 </layer>
 <layer id="2" name="Buildings" width="{width}" height="{height}">
  <data encoding="csv">{csv(buildings)}</data>
 </layer>
 <layer id="3" name="Front" width="{width}" height="{height}">
  <data encoding="csv">{csv(front)}</data>
 </layer>
</map>
'''


(ROOT / 'assets/region3_mirrorwild.tmx').write_text(make_region_map(3), encoding='utf-8')
(ROOT / 'assets/region4_resonance_verge.tmx').write_text(make_region_map(4), encoding='utf-8')


service = r'''using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Monsters;

namespace Cardcha.Services;

internal enum ExpeditionRegion
{
    Mirrorwild = 3,
    ResonanceVerge = 4,
}

/// <summary>
/// 0674 gameplay foundation for the post-Boss-II and post-Boss-III regions.
/// These are short three-wave expeditions, intentionally separate from Region I Hunt Run 2.0.
/// Enemy proxies stay at native Stardew sprite scale; authored replacement art can land later
/// without changing the combat/progression contract.
/// </summary>
internal sealed class RegionExpeditionService
{
    public const string Region3LocationName = "Cardcha_Region3_Mirrorwild";
    public const string Region3MapAssetName = "Maps/Cardcha_Region3_Mirrorwild";
    public const string Region4LocationName = "Cardcha_Region4_ResonanceVerge";
    public const string Region4MapAssetName = "Maps/Cardcha_Region4_ResonanceVerge";

    private const string Region3MapPath = "assets/region3_mirrorwild.tmx";
    private const string Region4MapPath = "assets/region4_resonance_verge.tmx";
    private const string EnemyMarkerKey = "Ronvotri.Cardcha/0674ExpeditionEnemy";
    private const string EnemyRoleKey = "Ronvotri.Cardcha/0674ExpeditionRole";
    private const int WaveCount = 3;
    private const long RouteConfirmWindowMs = 5000L;
    private const long ExtractConfirmWindowMs = 5000L;
    private const long BetweenWaveDelayMs = 1100L;

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly AirshipFoundationService Airship;

    private ExpeditionRegion? CurrentRegion;
    private ExpeditionRegion? PendingRouteRegion;
    private long PendingRouteUntilMs;
    private bool Active;
    private bool Completed;
    private bool WaveSpawned;
    private int CurrentWave;
    private long NextWaveAtMs;
    private int UnbankedScrap;
    private int UnbankedShiny;
    private long ExtractConfirmUntilMs;
    private int DebugBypassRegion;

    public RegionExpeditionService(IModHelper helper, IMonitor monitor, SaveService save, AirshipFoundationService airship)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.Airship = airship;
    }

    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)
    {
        if (e.NameWithoutLocale.IsEquivalentTo(Region3MapAssetName))
        {
            e.LoadFromModFile<xTile.Map>(Region3MapPath, AssetLoadPriority.Exclusive);
            return;
        }
        if (e.NameWithoutLocale.IsEquivalentTo(Region4MapAssetName))
            e.LoadFromModFile<xTile.Map>(Region4MapPath, AssetLoadPriority.Exclusive);
    }

    public void OnSaveLoaded(object? sender, SaveLoadedEventArgs e)
    {
        this.ResetRuntime(clearEnemies: true);
        this.EnsureLocation(ExpeditionRegion.Mirrorwild);
        this.EnsureLocation(ExpeditionRegion.ResonanceVerge);
    }

    public void OnDayStarted(object? sender, DayStartedEventArgs e)
    {
        this.ResetRuntime(clearEnemies: true);
        this.EnsureLocation(ExpeditionRegion.Mirrorwild);
        this.EnsureLocation(ExpeditionRegion.ResonanceVerge);
    }

    public void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e)
    {
        this.ResetRuntime(clearEnemies: true);
        this.DebugBypassRegion = 0;
    }

    /// <summary>
    /// Called by the 0673 milestone route only while the NEXT boss is still below its card gate.
    /// At the exact boss threshold, the milestone boss keeps priority.
    /// </summary>
    public string UseRouteConsole(int ownedCards, int nextBossRequired, string nextBossName)
    {
        if (!Context.IsWorldReady)
            return ModEntry.T("airship.expedition.unavailable");

        List<ExpeditionRegion> available = this.GetAvailableRegions();
        if (available.Count == 0)
            return nextBossRequired > 0
                ? ModEntry.T("airship.milestone.progress", new { name = nextBossName, cards = ownedCards, required = nextBossRequired })
                : ModEntry.T("airship.milestone.all_clear");

        long now = Environment.TickCount64;
        if (this.PendingRouteRegion is ExpeditionRegion pending && this.PendingRouteUntilMs > now)
            return this.LaunchPendingRoute(pending);

        this.PendingRouteRegion = null;
        this.PendingRouteUntilMs = 0;

        if (available.Count == 1)
            return this.PrepareRoute(available[0]);

        string prompt = nextBossRequired > 0
            ? ModEntry.T("airship.expedition.choose", new { boss = nextBossName, cards = ownedCards, required = nextBossRequired })
            : ModEntry.T("airship.expedition.choose_clear");
        Response[] choices = available
            .Select(r => new Response($"cardcha_expedition_{(int)r}", this.RegionDisplayName(r)))
            .Append(new Response("cardcha_expedition_cancel", ModEntry.T("airship.expedition.cancel")))
            .ToArray();

        Game1.currentLocation.createQuestionDialogue(prompt, choices, (Farmer who, string answer) =>
        {
            if (!answer.StartsWith("cardcha_expedition_", StringComparison.OrdinalIgnoreCase)
                || answer.Equals("cardcha_expedition_cancel", StringComparison.OrdinalIgnoreCase))
                return;
            if (!int.TryParse(answer["cardcha_expedition_".Length..], out int raw)
                || raw is not (3 or 4))
                return;
            ExpeditionRegion selected = (ExpeditionRegion)raw;
            if (!this.CanEnter(selected))
            {
                Game1.drawObjectDialogue(ModEntry.T("airship.expedition.locked", new { region = raw }));
                return;
            }
            Game1.drawObjectDialogue(this.PrepareRoute(selected));
        });
        return string.Empty;
    }

    private string PrepareRoute(ExpeditionRegion region)
    {
        GameLocation? target = this.EnsureLocation(region);
        if (target is null)
            return ModEntry.T("airship.expedition.unavailable");

        this.PendingRouteRegion = region;
        this.PendingRouteUntilMs = Environment.TickCount64 + RouteConfirmWindowMs;
        int fare = this.Airship.GetRegionFareForExternalRoute((int)region);
        Game1.playSound("smallSelect");
        return fare <= 0
            ? ModEntry.T("airship.expedition.confirm_free", new { region = this.RegionDisplayName(region) })
            : ModEntry.T("airship.expedition.confirm", new { region = this.RegionDisplayName(region), fare });
    }

    private string LaunchPendingRoute(ExpeditionRegion region)
    {
        this.PendingRouteRegion = null;
        this.PendingRouteUntilMs = 0;
        if (!this.CanEnter(region))
            return ModEntry.T("airship.expedition.locked", new { region = (int)region });

        GameLocation? target = this.EnsureLocation(region);
        if (target is null)
            return ModEntry.T("airship.expedition.unavailable");

        Point arrival = ResolveArrivalTile(target);
        return this.Airship.BeginExternalRegionFlight((int)region, target.NameOrUniqueName, arrival);
    }

    public void OnWarped(object? sender, WarpedEventArgs e)
    {
        ExpeditionRegion? incoming = ResolveRegion(e.NewLocation);
        ExpeditionRegion? outgoing = ResolveRegion(e.OldLocation);

        if (incoming is ExpeditionRegion region)
        {
            bool bypass = this.DebugBypassRegion == (int)region;
            if (!this.CanEnter(region) && !bypass)
            {
                this.Monitor.Log($"0674 blocked unauthorized Region {(int)region} entry.", LogLevel.Warn);
                this.ReturnToDeckImmediate();
                return;
            }
            this.StartExpedition(e.NewLocation, region);
            return;
        }

        if (outgoing is not null && this.Active)
        {
            int lostScrap = this.UnbankedScrap;
            int lostShiny = this.UnbankedShiny;
            this.ResetRuntime(clearEnemies: true);
            if (lostScrap > 0 || lostShiny > 0)
                Game1.showGlobalMessage(ModEntry.T("airship.expedition.lost", new { scrap = lostScrap, shiny = lostShiny }));
        }
    }

    public void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
    {
        if (!Context.IsWorldReady || !this.Active || this.CurrentRegion is null || Game1.currentLocation is null)
            return;
        if (ResolveRegion(Game1.currentLocation) != this.CurrentRegion)
            return;

        long now = Environment.TickCount64;
        if (!this.WaveSpawned)
        {
            if (!this.Completed && now >= this.NextWaveAtMs)
                this.SpawnWave(Game1.currentLocation, this.CurrentRegion.Value, this.CurrentWave);
            return;
        }

        if (CountMarkedEnemies(Game1.currentLocation) > 0)
            return;

        this.WaveSpawned = false;
        this.AwardWave(this.CurrentRegion.Value, this.CurrentWave);
        if (this.CurrentWave >= WaveCount)
        {
            this.Completed = true;
            this.NextWaveAtMs = 0;
            Game1.playSound("discoverMineral");
            Game1.showGlobalMessage(ModEntry.T("airship.expedition.ready"));
            return;
        }

        int cleared = this.CurrentWave;
        this.CurrentWave++;
        this.NextWaveAtMs = now + BetweenWaveDelayMs;
        Game1.showGlobalMessage(ModEntry.T("airship.expedition.wave_clear", new
        {
            wave = cleared,
            scrap = this.UnbankedScrap,
            shiny = this.UnbankedShiny
        }));
    }

    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady || !e.Button.IsActionButton() || !this.Active || this.CurrentRegion is null
            || Game1.activeClickableMenu is not null || Game1.dialogueUp || Game1.eventUp || Game1.currentLocation is null)
            return;
        if (ResolveRegion(Game1.currentLocation) != this.CurrentRegion)
            return;

        Point extract = ResolveExtractionTile(Game1.currentLocation);
        Point player = PlayerTile();
        Point action = Game1.player.GetGrabTile().ToPoint();
        if (Math.Abs(player.X - extract.X) > 2 || Math.Abs(player.Y - extract.Y) > 2)
        {
            if (Math.Abs(action.X - extract.X) > 1 || Math.Abs(action.Y - extract.Y) > 1)
                return;
        }

        this.Helper.Input.Suppress(e.Button);
        long now = Environment.TickCount64;
        if (this.ExtractConfirmUntilMs <= now)
        {
            this.ExtractConfirmUntilMs = now + ExtractConfirmWindowMs;
            Game1.drawObjectDialogue(ModEntry.T("airship.expedition.extract_confirm", new
            {
                scrap = this.UnbankedScrap,
                shiny = this.UnbankedShiny,
                wave = this.Completed ? WaveCount : Math.Max(0, this.CurrentWave - (this.WaveSpawned ? 0 : 1))
            }));
            return;
        }

        this.ExtractConfirmUntilMs = 0;
        this.BankRewards();
        this.Active = false;
        this.Completed = false;
        this.ClearMarkedEnemies(Game1.currentLocation);
        this.Airship.StartExternalRegionReturnFlight();
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        if (!Context.IsWorldReady || Game1.currentLocation is null)
            return;
        ExpeditionRegion? region = ResolveRegion(Game1.currentLocation);
        if (region is null)
            return;

        DrawRegionIdentity(e.SpriteBatch, Game1.currentLocation, region.Value);
        foreach (Monster monster in Game1.currentLocation.characters.OfType<Monster>()
                     .Where(m => m.Health > 0 && m.modData.ContainsKey(EnemyMarkerKey)))
        {
            DrawEnemyIdentity(e.SpriteBatch, monster, region.Value);
        }
    }

    private void StartExpedition(GameLocation location, ExpeditionRegion region)
    {
        this.ClearMarkedEnemies(location);
        this.CurrentRegion = region;
        this.Active = true;
        this.Completed = false;
        this.WaveSpawned = false;
        this.CurrentWave = 1;
        this.NextWaveAtMs = Environment.TickCount64 + 700L;
        this.UnbankedScrap = 0;
        this.UnbankedShiny = 0;
        this.ExtractConfirmUntilMs = 0;
        Game1.showGlobalMessage(ModEntry.T("airship.expedition.arrive", new { region = this.RegionDisplayName(region) }));
        this.Monitor.Log($"0674 expedition started: {region}, native-size enemy proxies, 3-wave contract.", LogLevel.Info);
    }

    private void SpawnWave(GameLocation location, ExpeditionRegion region, int wave)
    {
        this.ClearMarkedEnemies(location);
        Point[] candidates =
        {
            new(6,5), new(11,5), new(18,5), new(22,5), new(29,5), new(34,5),
            new(7,10), new(13,10), new(20,9), new(27,10), new(33,10),
            new(6,16), new(12,17), new(18,15), new(22,15), new(28,17), new(34,16),
            new(9,22), new(15,21), new(25,21), new(31,22)
        };
        int seed = unchecked((int)Game1.uniqueIDForThisGame + Game1.Date.TotalDays * 1009 + (int)region * 65537 + wave * 7919 + this.Save.Data.AirshipFlightsTaken * 31);
        Random random = new(seed);
        Point[] shuffled = candidates.OrderBy(_ => random.Next()).ToArray();
        int targetCount = region == ExpeditionRegion.Mirrorwild ? 3 + wave * 2 : 4 + wave * 2;
        int spawned = 0;

        foreach (Point tile in shuffled)
        {
            if (spawned >= targetCount)
                break;
            Vector2 tv = new(tile.X, tile.Y);
            try
            {
                if (location.IsTileBlockedBy(tv) || location.Objects.ContainsKey(tv))
                    continue;
            }
            catch { continue; }

            Monster enemy = this.CreateEnemy(region, wave, spawned, tv * 64f);
            enemy.modData[EnemyMarkerKey] = $"0674:{(int)region}:{wave}";
            location.characters.Add(enemy);
            spawned++;
        }

        this.WaveSpawned = true;
        Game1.playSound(region == ExpeditionRegion.Mirrorwild ? "ghost" : "wand");
        Game1.showGlobalMessage(ModEntry.T("airship.expedition.wave", new
        {
            region = this.RegionDisplayName(region),
            wave,
            total = WaveCount
        }));
        this.Monitor.Log($"0674 {region} wave {wave}/{WaveCount}: spawned={spawned}.", LogLevel.Trace);
    }

    private Monster CreateEnemy(ExpeditionRegion region, int wave, int index, Vector2 position)
    {
        int archetype = (index + wave) % 3;
        Monster monster;
        string role;
        int hp;
        int speed;

        if (region == ExpeditionRegion.Mirrorwild)
        {
            if (wave == 3 && index == 0)
            {
                monster = new GreenSlime(position, 0);
                role = "mirror_sentinel";
                hp = 480;
                speed = 3;
            }
            else if (archetype == 0)
            {
                monster = new Bat(position);
                role = "mirror_wisp";
                hp = 105 + wave * 18;
                speed = 4;
            }
            else if (archetype == 1)
            {
                monster = new Bug(position, 0);
                role = "glass_scarab";
                hp = 145 + wave * 24;
                speed = 3;
            }
            else
            {
                monster = new GreenSlime(position, 0);
                role = "echo_slime";
                hp = 190 + wave * 32;
                speed = 2;
            }
        }
        else
        {
            if (wave == 3 && index == 0)
            {
                monster = new GreenSlime(position, 0);
                role = "resonant_prime";
                hp = 650;
                speed = 3;
            }
            else if (archetype == 0)
            {
                monster = new Bat(position);
                role = "ignis_echo";
                hp = 145 + wave * 24;
                speed = 5;
            }
            else if (archetype == 1)
            {
                monster = new GreenSlime(position, 0);
                role = "vita_husk";
                hp = 235 + wave * 42;
                speed = 2;
            }
            else
            {
                monster = new Bug(position, 0);
                role = "aether_mite";
                hp = 175 + wave * 30;
                speed = 4;
            }
        }

        monster.MaxHealth = hp;
        monster.Health = hp;
        monster.Speed = speed;
        monster.modData[EnemyRoleKey] = role;
        return monster;
    }

    private void AwardWave(ExpeditionRegion region, int wave)
    {
        int scrap = region == ExpeditionRegion.Mirrorwild
            ? wave switch { 1 => 10, 2 => 15, _ => 22 }
            : wave switch { 1 => 15, 2 => 22, _ => 32 };
        int shiny = region == ExpeditionRegion.Mirrorwild
            ? (wave == 3 ? 2 : wave == 2 ? 1 : 0)
            : (wave == 1 ? 1 : wave == 2 ? 2 : 3);
        this.UnbankedScrap += scrap;
        this.UnbankedShiny += shiny;
    }

    private void BankRewards()
    {
        int scrap = Math.Max(0, this.UnbankedScrap);
        int shiny = Math.Max(0, this.UnbankedShiny);
        if (scrap > 0 || shiny > 0)
        {
            this.Save.Data.CardboardScraps += scrap;
            this.Save.Data.ShinyScraps += shiny;
            this.Save.Save();
        }
        this.UnbankedScrap = 0;
        this.UnbankedShiny = 0;
        Game1.showGlobalMessage(ModEntry.T("airship.expedition.bank", new { scrap, shiny }));
    }

    private List<ExpeditionRegion> GetAvailableRegions()
    {
        List<ExpeditionRegion> result = new();
        HashSet<string> bossCards = this.Save.Data.BossCardsUnlocked ?? new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        if (this.Save.Data.AirshipHighestRegionUnlocked >= 3 && bossCards.Contains(MilestoneBossService.MirrorArchiveBossCardId))
            result.Add(ExpeditionRegion.Mirrorwild);
        if (this.Save.Data.AirshipHighestRegionUnlocked >= 4 && bossCards.Contains(MilestoneBossService.TricolorBossCardId))
            result.Add(ExpeditionRegion.ResonanceVerge);
        return result;
    }

    private bool CanEnter(ExpeditionRegion region)
        => this.GetAvailableRegions().Contains(region);

    private GameLocation? EnsureLocation(ExpeditionRegion region)
    {
        if (!Context.IsWorldReady)
            return null;
        string name = region == ExpeditionRegion.Mirrorwild ? Region3LocationName : Region4LocationName;
        string asset = region == ExpeditionRegion.Mirrorwild ? Region3MapAssetName : Region4MapAssetName;
        GameLocation? existing = Game1.getLocationFromName(name);
        if (existing is not null)
            return existing;
        try
        {
            GameLocation location = new(asset, name);
            Game1.locations.Add(location);
            return location;
        }
        catch (Exception ex)
        {
            this.Monitor.Log($"0674 couldn't create {name}: {ex.GetType().Name}: {ex.Message}", LogLevel.Error);
            return null;
        }
    }

    private static ExpeditionRegion? ResolveRegion(GameLocation? location)
    {
        string? name = location?.NameOrUniqueName;
        if (name?.Equals(Region3LocationName, StringComparison.OrdinalIgnoreCase) == true)
            return ExpeditionRegion.Mirrorwild;
        if (name?.Equals(Region4LocationName, StringComparison.OrdinalIgnoreCase) == true)
            return ExpeditionRegion.ResonanceVerge;
        return null;
    }

    private string RegionDisplayName(ExpeditionRegion region)
        => ModEntry.T(region == ExpeditionRegion.Mirrorwild ? "airship.expedition.region3" : "airship.expedition.region4");

    private static Point ResolveArrivalTile(GameLocation location)
    {
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 40;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 28;
        return new Point(width / 2, Math.Max(4, height - 5));
    }

    private static Point ResolveExtractionTile(GameLocation location)
    {
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 40;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 28;
        return new Point(width / 2, Math.Max(3, height - 3));
    }

    private static Point PlayerTile()
        => new((int)(Game1.player.Position.X / 64f), (int)(Game1.player.Position.Y / 64f));

    private static int CountMarkedEnemies(GameLocation location)
        => location.characters.OfType<Monster>().Count(m => m.Health > 0 && m.modData.ContainsKey(EnemyMarkerKey));

    private void ClearMarkedEnemies(GameLocation? location)
    {
        if (location is null)
            return;
        foreach (NPC actor in location.characters.Where(a => a is Monster && a.modData.ContainsKey(EnemyMarkerKey)).ToList())
            location.characters.Remove(actor);
    }

    private void ResetRuntime(bool clearEnemies)
    {
        if (clearEnemies)
        {
            this.ClearMarkedEnemies(Game1.getLocationFromName(Region3LocationName));
            this.ClearMarkedEnemies(Game1.getLocationFromName(Region4LocationName));
        }
        this.CurrentRegion = null;
        this.PendingRouteRegion = null;
        this.PendingRouteUntilMs = 0;
        this.Active = false;
        this.Completed = false;
        this.WaveSpawned = false;
        this.CurrentWave = 0;
        this.NextWaveAtMs = 0;
        this.UnbankedScrap = 0;
        this.UnbankedShiny = 0;
        this.ExtractConfirmUntilMs = 0;
    }

    private void ReturnToDeckImmediate()
    {
        GameLocation? deck = Game1.getLocationFromName(AirshipFoundationService.DeckLocationName);
        if (deck is not null)
        {
            int width = deck.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 24;
            int height = deck.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 14;
            Game1.warpFarmer(deck.NameOrUniqueName, width / 2, Math.Max(4, height - 4), 0);
            return;
        }
        GameLocation? forest = Game1.getLocationFromName(AirshipFoundationService.SkyDockLocationName);
        if (forest is not null)
            Game1.warpFarmer(forest.NameOrUniqueName, 20, 4, 2);
    }

    private static void DrawRegionIdentity(SpriteBatch batch, GameLocation location, ExpeditionRegion region)
    {
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 40;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 28;
        Point extract = ResolveExtractionTile(location);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, new Vector2(extract.X * 64f + 32f, extract.Y * 64f + 32f));
        Color c = region == ExpeditionRegion.Mirrorwild ? new Color(143, 187, 226) : new Color(197, 135, 218);
        float pulse = 0.55f + 0.16f * (float)Math.Sin(Environment.TickCount64 / 260d);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 34, (int)local.Y - 3, 68, 6), c * pulse);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 3, (int)local.Y - 34, 6, 68), c * pulse);

        // Small deterministic motes only; no full-screen tint and no oversized sci-fi overlays.
        for (int i = 0; i < 12; i++)
        {
            int x = 3 + (i * 11 + (int)region * 7) % Math.Max(4, width - 6);
            int y = 3 + (i * 7 + (int)region * 5) % Math.Max(4, height - 7);
            Vector2 p = Game1.GlobalToLocal(Game1.viewport, new Vector2(x * 64f + 32f, y * 64f + 32f));
            int s = 2 + (i % 2);
            batch.Draw(Game1.staminaRect, new Rectangle((int)p.X, (int)p.Y, s, s), c * 0.30f);
        }
    }

    private static void DrawEnemyIdentity(SpriteBatch batch, Monster monster, ExpeditionRegion region)
    {
        Vector2 world = monster.Position + new Vector2(32f, 56f);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
        Color c = region == ExpeditionRegion.Mirrorwild ? new Color(123, 192, 226) : new Color(209, 132, 191);
        if (monster.modData.TryGetValue(EnemyRoleKey, out string? role))
        {
            if (role.Contains("vita", StringComparison.OrdinalIgnoreCase)) c = new Color(116, 205, 133);
            else if (role.Contains("ignis", StringComparison.OrdinalIgnoreCase)) c = new Color(224, 134, 105);
            else if (role.Contains("aether", StringComparison.OrdinalIgnoreCase)) c = new Color(126, 166, 229);
            else if (role.Contains("sentinel", StringComparison.OrdinalIgnoreCase) || role.Contains("prime", StringComparison.OrdinalIgnoreCase)) c = new Color(232, 205, 111);
        }
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 8, (int)local.Y, 16, 2), c * 0.72f);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 1, (int)local.Y - 7, 2, 14), c * 0.72f);
    }

    public string Describe()
    {
        if (!Context.IsWorldReady)
            return "0674 Expedition=<no save>";
        string pending = this.PendingRouteRegion?.ToString() ?? "none";
        double confirm = this.PendingRouteUntilMs > Environment.TickCount64 ? (this.PendingRouteUntilMs - Environment.TickCount64) / 1000d : 0d;
        return $"0674 Expedition | Available=[{string.Join(',', this.GetAvailableRegions())}] | Current={this.CurrentRegion?.ToString() ?? "none"} | " +
               $"Active={this.Active} Complete={this.Completed} Wave={this.CurrentWave}/{WaveCount} Spawned={this.WaveSpawned} | " +
               $"Unbanked={this.UnbankedScrap} Scrap + {this.UnbankedShiny} Shiny | Pending={pending}:{confirm:0.0}s | Schema=19";
    }

    public string DebugEnter(int region)
    {
        if (!Context.IsWorldReady || region is not (3 or 4))
            return "0674 TEST: load a save and use region 3 or 4.";
        ExpeditionRegion target = (ExpeditionRegion)region;
        GameLocation? location = this.EnsureLocation(target);
        if (location is null)
            return $"0674 TEST: Region {region} map unavailable.";
        this.DebugBypassRegion = region;
        Point arrival = ResolveArrivalTile(location);
        Game1.warpFarmer(location.NameOrUniqueName, arrival.X, arrival.Y, 0);
        return $"0674 TEST: entered Region {region} with runtime-only gate bypass. Save unlock state unchanged.";
    }

    public string DebugClearWave()
    {
        if (!Context.IsWorldReady || !this.Active || Game1.currentLocation is null || ResolveRegion(Game1.currentLocation) is null)
            return "0674 TEST: enter an active Region III/IV expedition first.";
        this.ClearMarkedEnemies(Game1.currentLocation);
        return $"0674 TEST: cleared current wave actors. {this.Describe()}";
    }
}
'''
(ROOT / 'Services/RegionExpeditionService.cs').write_text(service, encoding='utf-8')


# Airship: expose a generic external-region flight while preserving the Region I helm flow.
airship_path = ROOT / 'Services/AirshipFoundationService.cs'
def patch_airship(text: str) -> str:
    text = replace_once(
        text,
        '    private Func<string>? MilestoneRouteAction;\n',
        '    private Func<string>? MilestoneRouteAction;\n    private string PendingExternalFlightLocationName = string.Empty;\n    private Point PendingExternalFlightArrivalTile;\n',
        'airship external flight fields'
    )
    text = replace_once(
        text,
        '    public void BindMilestoneRouteHandler(Func<string> handler)\n        => this.MilestoneRouteAction = handler;\n\n',
        '''    public void BindMilestoneRouteHandler(Func<string> handler)\n        => this.MilestoneRouteAction = handler;\n\n    public int GetRegionFareForExternalRoute(int region)\n        => this.GetRegionFare(region);\n\n    public string BeginExternalRegionFlight(int region, string targetLocationName, Point arrivalTile)\n    {\n        if (!Context.IsWorldReady || region is not (3 or 4))\n            return ModEntry.T("airship.expedition.unavailable");\n        GameLocation? target = Game1.getLocationFromName(targetLocationName);\n        if (target is null)\n            return ModEntry.T("airship.expedition.unavailable");\n\n        int fare = this.GetRegionFare(region);\n        if (Game1.player.Money < fare)\n            return ModEntry.T("airship.route.not_enough", new { fare, money = Game1.player.Money });\n        if (fare > 0)\n            Game1.player.Money -= fare;\n\n        this.Save.Data.AirshipFlightsTaken++;\n        this.Save.Data.AirshipTotalFarePaid += fare;\n        this.Save.Save();\n        this.PendingExternalFlightLocationName = targetLocationName;\n        this.PendingExternalFlightArrivalTile = arrivalTile;\n        this.StartFlightCutscene(returning: false);\n        return string.Empty;\n    }\n\n    public void StartExternalRegionReturnFlight()\n    {\n        this.PendingExternalFlightLocationName = string.Empty;\n        this.PendingExternalFlightArrivalTile = Point.Zero;\n        this.StartFlightCutscene(returning: true);\n    }\n\n''',
        'airship external flight API'
    )
    old = '''            else\n            {\n                GameLocation? firstRoom = this.BeginRegion1HuntRun();\n                if (firstRoom is null\n                {'''
    # Use a narrower anchor that matches current source exactly.
    anchor = '''            else\n            {\n                GameLocation? firstRoom = this.BeginRegion1HuntRun();\n                if (firstRoom is null)\n                {'''
    replacement = '''            else\n            {\n                if (!string.IsNullOrWhiteSpace(this.PendingExternalFlightLocationName))\n                {\n                    GameLocation? external = Game1.getLocationFromName(this.PendingExternalFlightLocationName);\n                    if (external is null)\n                    {\n                        this.FlightCutsceneActive = false;\n                        this.PendingExternalFlightLocationName = string.Empty;\n                        this.ReturnToSkyDockExterior();\n                        Game1.drawObjectDialogue(ModEntry.T("airship.expedition.unavailable"));\n                        return;\n                    }\n                    Point arrival = this.PendingExternalFlightArrivalTile;\n                    this.WarpGraceUntilMs = Environment.TickCount64 + 850L;\n                    Game1.warpFarmer(external.NameOrUniqueName, arrival.X, arrival.Y, 0);\n                }\n                else\n                {\n                    GameLocation? firstRoom = this.BeginRegion1HuntRun();\n                    if (firstRoom is null)\n                    {'''
    if replacement not in text:
        if anchor not in text:
            raise RuntimeError('airship flight external anchor missing')
        text = text.replace(anchor, replacement, 1)
        closing_anchor = '''                Point arrival = ResolveRegion1RunArrivalTile(firstRoom);\n                this.WarpGraceUntilMs = Environment.TickCount64 + 850L;\n                Game1.warpFarmer(firstRoom.NameOrUniqueName, arrival.X, arrival.Y, 0);\n            }\n        }\n\n        if (elapsed >= FlightCutsceneDurationMs)'''
        closing_replacement = '''                    Point arrival = ResolveRegion1RunArrivalTile(firstRoom);\n                    this.WarpGraceUntilMs = Environment.TickCount64 + 850L;\n                    Game1.warpFarmer(firstRoom.NameOrUniqueName, arrival.X, arrival.Y, 0);\n                }\n            }\n        }\n\n        if (elapsed >= FlightCutsceneDurationMs)'''
        if closing_anchor not in text:
            raise RuntimeError('airship flight closing anchor missing')
        text = text.replace(closing_anchor, closing_replacement, 1)
    text = replace_once(
        text,
        '            this.FlightCutsceneStartedAtMs = 0;\n            this.WarpGraceUntilMs = Environment.TickCount64 + 500L;\n',
        '            this.FlightCutsceneStartedAtMs = 0;\n            this.PendingExternalFlightLocationName = string.Empty;\n            this.PendingExternalFlightArrivalTile = Point.Zero;\n            this.WarpGraceUntilMs = Environment.TickCount64 + 500L;\n',
        'airship clear external target'
    )
    return text
update_text(airship_path, patch_airship)


# Milestone route delegates to expeditions only between boss thresholds; bosses retain exact-threshold priority.
boss_path = ROOT / 'Services/MilestoneBossService.cs'
def patch_boss(text: str) -> str:
    text = replace_once(
        text,
        '    private readonly Random Rng = new(0x670B055);\n\n',
        '    private readonly Random Rng = new(0x670B055);\n    private Func<int, int, string, string>? ExpeditionRouteAction;\n\n',
        'milestone expedition delegate field'
    )
    text = replace_once(
        text,
        '    public bool IsInArena => this.ResolveCurrentKind(Game1.currentLocation) is not null;\n',
        '''    public void BindExpeditionRouteHandler(Func<int, int, string, string> handler)\n        => this.ExpeditionRouteAction = handler;\n\n    public bool IsInArena => this.ResolveCurrentKind(Game1.currentLocation) is not null;\n''',
        'milestone expedition bind'
    )
    text = replace_once(
        text,
        '''        if (kind is null)\n        {\n            this.RouteConfirmUntilMs = 0;\n            this.RouteConfirmKind = null;\n            return ModEntry.T("airship.milestone.all_clear");\n        }\n''',
        '''        if (kind is null)\n        {\n            this.RouteConfirmUntilMs = 0;\n            this.RouteConfirmKind = null;\n            if (this.ExpeditionRouteAction is not null && this.Save.Data.AirshipHighestRegionUnlocked >= 3)\n                return this.ExpeditionRouteAction(owned, 0, string.Empty);\n            return ModEntry.T("airship.milestone.all_clear");\n        }\n''',
        'milestone all clear expedition route'
    )
    text = replace_once(
        text,
        '''        if (owned < required)\n        {\n            this.RouteConfirmUntilMs = 0;\n            this.RouteConfirmKind = null;\n            return ModEntry.T("airship.milestone.progress", new { name, cards = owned, required });\n        }\n''',
        '''        if (owned < required)\n        {\n            this.RouteConfirmUntilMs = 0;\n            this.RouteConfirmKind = null;\n            if (kind != MilestoneBossKind.HollowCurator && this.ExpeditionRouteAction is not null)\n                return this.ExpeditionRouteAction(owned, required, name);\n            return ModEntry.T("airship.milestone.progress", new { name, cards = owned, required });\n        }\n''',
        'milestone between-boss expedition route'
    )
    text = text.replace('0673 MilestoneRoute', '0674 MilestoneRoute')
    text = text.replace('0673 MilestoneBoss', '0674 MilestoneBoss')
    return text
update_text(boss_path, patch_boss)


# ModEntry wiring.
entry_path = ROOT / 'ModEntry.cs'
def patch_entry(text: str) -> str:
    text = replace_once(text, '    private AirshipFoundationService Airship = null!;\n', '    private AirshipFoundationService Airship = null!;\n    private RegionExpeditionService RegionExpeditions = null!;\n', 'entry field')
    text = replace_once(
        text,
        '        this.Airship = new AirshipFoundationService(helper, this.Monitor, this.Save, this.Controller);\n        this.VerdantGuardian = new VerdantGuardianBossService',
        '        this.Airship = new AirshipFoundationService(helper, this.Monitor, this.Save, this.Controller);\n        this.RegionExpeditions = new RegionExpeditionService(helper, this.Monitor, this.Save, this.Airship);\n        this.VerdantGuardian = new VerdantGuardianBossService',
        'entry instantiate'
    )
    text = replace_once(
        text,
        '        this.MilestoneBosses = new MilestoneBossService(helper, this.Monitor, this.Save);\n        this.Airship.BindMilestoneRouteHandler(this.MilestoneBosses.UseAirshipMilestoneRoute);\n',
        '        this.MilestoneBosses = new MilestoneBossService(helper, this.Monitor, this.Save);\n        this.MilestoneBosses.BindExpeditionRouteHandler(this.RegionExpeditions.UseRouteConsole);\n        this.Airship.BindMilestoneRouteHandler(this.MilestoneBosses.UseAirshipMilestoneRoute);\n',
        'entry route bind'
    )
    text = replace_once(text, '        helper.Events.Content.AssetRequested += this.Airship.OnAssetRequested;\n', '        helper.Events.Content.AssetRequested += this.Airship.OnAssetRequested;\n        helper.Events.Content.AssetRequested += this.RegionExpeditions.OnAssetRequested;\n', 'entry asset event')
    text = replace_once(text, '        helper.Events.GameLoop.SaveLoaded += this.MilestoneBosses.OnSaveLoaded;\n', '        helper.Events.GameLoop.SaveLoaded += this.MilestoneBosses.OnSaveLoaded;\n        helper.Events.GameLoop.SaveLoaded += this.RegionExpeditions.OnSaveLoaded;\n', 'entry save event')
    text = replace_once(text, '        helper.Events.GameLoop.DayStarted += this.MilestoneBosses.OnDayStarted;\n', '        helper.Events.GameLoop.DayStarted += this.MilestoneBosses.OnDayStarted;\n        helper.Events.GameLoop.DayStarted += this.RegionExpeditions.OnDayStarted;\n', 'entry day event')
    text = replace_once(text, '        helper.Events.GameLoop.UpdateTicked += this.MilestoneBosses.OnUpdateTicked;\n', '        helper.Events.GameLoop.UpdateTicked += this.MilestoneBosses.OnUpdateTicked;\n        helper.Events.GameLoop.UpdateTicked += this.RegionExpeditions.OnUpdateTicked;\n', 'entry update event')
    text = replace_once(text, '        helper.Events.GameLoop.ReturnedToTitle += this.MilestoneBosses.OnReturnedToTitle;\n', '        helper.Events.GameLoop.ReturnedToTitle += this.MilestoneBosses.OnReturnedToTitle;\n        helper.Events.GameLoop.ReturnedToTitle += this.RegionExpeditions.OnReturnedToTitle;\n', 'entry title event')
    text = replace_once(text, '        helper.Events.Display.RenderedWorld += this.MilestoneBosses.OnRenderedWorld;\n', '        helper.Events.Display.RenderedWorld += this.MilestoneBosses.OnRenderedWorld;\n        helper.Events.Display.RenderedWorld += this.RegionExpeditions.OnRenderedWorld;\n', 'entry render event')
    text = replace_once(text, '        helper.Events.Input.ButtonPressed += this.MilestoneBosses.OnButtonPressed;\n', '        helper.Events.Input.ButtonPressed += this.MilestoneBosses.OnButtonPressed;\n        helper.Events.Input.ButtonPressed += this.RegionExpeditions.OnButtonPressed;\n', 'entry button event')
    text = replace_once(text, '        helper.Events.Player.Warped += this.MilestoneBosses.OnWarped;\n', '        helper.Events.Player.Warped += this.MilestoneBosses.OnWarped;\n        helper.Events.Player.Warped += this.RegionExpeditions.OnWarped;\n', 'entry warp event')
    text = replace_once(
        text,
        '        helper.ConsoleCommands.Add("cardcha_milestone_route_status", "Show the real 40/60/80-card milestone route state.", (_, _) => this.Monitor.Log(this.MilestoneBosses.DescribeMilestoneRoute(), LogLevel.Alert));\n',
        '''        helper.ConsoleCommands.Add("cardcha_milestone_route_status", "Show the real 40/60/80-card milestone route state.", (_, _) => this.Monitor.Log(this.MilestoneBosses.DescribeMilestoneRoute(), LogLevel.Alert));\n        helper.ConsoleCommands.Add("cardcha_expedition_status", "Show Region III/IV expedition runtime and route state.", (_, _) => this.Monitor.Log(this.RegionExpeditions.Describe(), LogLevel.Alert));\n        helper.ConsoleCommands.Add("cardcha_test_region3", "TEST ONLY: enter Region III Mirrorwild without changing progression.", (_, _) => this.Monitor.Log(this.RegionExpeditions.DebugEnter(3), LogLevel.Alert));\n        helper.ConsoleCommands.Add("cardcha_test_region4", "TEST ONLY: enter Region IV Resonance Verge without changing progression.", (_, _) => this.Monitor.Log(this.RegionExpeditions.DebugEnter(4), LogLevel.Alert));\n        helper.ConsoleCommands.Add("cardcha_expedition_clear", "TEST ONLY: clear current Region III/IV expedition wave.", (_, _) => this.Monitor.Log(this.RegionExpeditions.DebugClearWave(), LogLevel.Alert));\n''',
        'entry expedition commands'
    )
    text = text.replace(f'Cardcha! {PREV} MILESTONE PROGRESSION BOSS ROUTE TEST', f'Cardcha! {VERSION} REGION III / IV EXPEDITION FOUNDATION TEST')
    return text
update_text(entry_path, patch_entry)


# i18n.
keys_en = {
    'airship.expedition.region3': 'Region III • Mirrorwild',
    'airship.expedition.region4': 'Region IV • Resonance Verge',
    'airship.expedition.choose': '{{boss}} is still sealed ({{cards}}/{{required}} cards). Choose an unlocked expedition route:',
    'airship.expedition.choose_clear': 'Milestone route clear. Choose an expedition route:',
    'airship.expedition.cancel': 'Stay at the Sky Dock',
    'airship.expedition.confirm': '{{region}} is charted. Fare: {{fare}}g. Use the route console again within 5 seconds to depart.',
    'airship.expedition.confirm_free': '{{region}} is charted. This flight is free. Use the route console again within 5 seconds to depart.',
    'airship.expedition.unavailable': 'That expedition route is unstable right now. No fare was consumed.',
    'airship.expedition.locked': 'Region {{region}} is still sealed by Cardcha progression.',
    'airship.expedition.arrive': '{{region}} • Expedition started. Clear three resonance waves, then extract from the southern Airship pad.',
    'airship.expedition.wave': '{{region}} • Wave {{wave}}/{{total}} incoming.',
    'airship.expedition.wave_clear': 'Wave {{wave}}/3 cleared • Unbanked cargo: {{scrap}} Scrap + {{shiny}} Shiny Scrap.',
    'airship.expedition.ready': 'Expedition complete. Use the southern Airship pad to extract your cargo.',
    'airship.expedition.extract_confirm': 'Extract now after wave {{wave}} with {{scrap}} Scrap + {{shiny}} Shiny Scrap? Interact again within 5 seconds.',
    'airship.expedition.bank': 'Expedition cargo secured: +{{scrap}} Scrap, +{{shiny}} Shiny Scrap.',
    'airship.expedition.lost': 'Emergency exit: {{scrap}} Scrap + {{shiny}} Shiny Scrap of unbanked expedition cargo was lost.'
}
keys_vi = {
    'airship.expedition.region3': 'Khu III • Rừng Gương',
    'airship.expedition.region4': 'Khu IV • Rìa Cộng Hưởng',
    'airship.expedition.choose': '{{boss}} vẫn bị phong ấn ({{cards}}/{{required}} thẻ). Chọn khu thám hiểm đã mở:',
    'airship.expedition.choose_clear': 'Các mốc Boss đã hoàn tất. Chọn khu thám hiểm:',
    'airship.expedition.cancel': 'Ở lại Bến Trời',
    'airship.expedition.confirm': 'Đã định tuyến {{region}}. Phí bay: {{fare}}g. Dùng bảng tuyến lần nữa trong 5 giây để khởi hành.',
    'airship.expedition.confirm_free': 'Đã định tuyến {{region}}. Chuyến này miễn phí. Dùng bảng tuyến lần nữa trong 5 giây để khởi hành.',
    'airship.expedition.unavailable': 'Tuyến thám hiểm này hiện chưa ổn định. Bạn không bị trừ phí.',
    'airship.expedition.locked': 'Khu {{region}} vẫn đang bị khóa bởi tiến trình Cardcha.',
    'airship.expedition.arrive': '{{region}} • Bắt đầu thám hiểm. Vượt qua 3 đợt cộng hưởng rồi rút về tại bãi Airship phía nam.',
    'airship.expedition.wave': '{{region}} • Đợt {{wave}}/{{total}} đang tới.',
    'airship.expedition.wave_clear': 'Đã dọn đợt {{wave}}/3 • Hàng chưa ký gửi: {{scrap}} Scrap + {{shiny}} Shiny Scrap.',
    'airship.expedition.ready': 'Hoàn tất thám hiểm. Hãy dùng bãi Airship phía nam để mang chiến lợi phẩm về.',
    'airship.expedition.extract_confirm': 'Rút về sau đợt {{wave}} với {{scrap}} Scrap + {{shiny}} Shiny Scrap? Tương tác lần nữa trong 5 giây để xác nhận.',
    'airship.expedition.bank': 'Đã ký gửi chiến lợi phẩm: +{{scrap}} Scrap, +{{shiny}} Shiny Scrap.',
    'airship.expedition.lost': 'Rời khu khẩn cấp: đã mất {{scrap}} Scrap + {{shiny}} Shiny Scrap chưa kịp ký gửi.'
}
for lang, additions in [('default.json', keys_en), ('vi.json', keys_vi)]:
    path = ROOT / 'i18n' / lang
    data = json.loads(path.read_text(encoding='utf-8'))
    data.update(additions)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


handoff = f'''# Cardcha alpha28 0674 — Region III / IV Gameplay Foundation

## Current branch / build
- Branch: `cardcha-alpha28-0674-region3-region4-gameplay-foundation`
- Build: `{VERSION}`
- Base: 0673 Milestone Progression Boss Route

## 0674 gameplay contract
- Region III `Mirrorwild` unlock requires Boss II reward `mirror_archive` + `AirshipHighestRegionUnlocked >= 3`.
- Region IV `Resonance Verge` unlock requires Boss III reward `tricolor_resonance` + `AirshipHighestRegionUnlocked >= 4`.
- Sky Dock route console keeps milestone-boss priority at exact 60/80 thresholds.
- Between boss thresholds it opens expeditions: Region III while farming toward 60 cards; Region IV while farming toward 80 cards.
- If both expedition regions are open, the route console presents a destination choice.
- Region III fare = 500g; Region IV fare = 1000g, reusing Airship fare/flight telemetry.
- External region flights reuse the existing Airship flight cutscene.
- Each expedition is 3 waves with unbanked Scrap/Shiny Scrap; extraction banks rewards.
- Unexpected exit loses only unbanked expedition cargo.
- Enemy foundation uses native-size Stardew monster proxies with Cardcha role metadata. No render scaling/enlargement.
- New maps are Cardcha-owned vanilla-tile TMX maps with distinct route silhouettes; visual/authored-enemy polish remains pending.

## Region identity
### Region III — Mirrorwild
- Mirrored trail layout.
- Mirror Wisp / Glass Scarab / Echo Slime proxy archetypes.
- Wave 3 Mirror Sentinel elite.
- Rewards: 47 Scrap + 3 Shiny Scrap for full clear.

### Region IV — Resonance Verge
- Central resonance lane + three-spoke layout.
- Ignis Echo / Vita Husk / Aether Mite proxy archetypes.
- Wave 3 Resonant Prime elite.
- Rewards: 69 Scrap + 6 Shiny Scrap for full clear.

## Debug
- `cardcha_expedition_status`
- `cardcha_test_region3`
- `cardcha_test_region4`
- `cardcha_expedition_clear`

## Frozen / regression guards
- Save schema stays 19.
- Region I Hunt Run 2.0 helm flow remains intact.
- 0673 real Boss 40/60/80 route remains intact and has priority at boss thresholds.
- Boss I / Totems / 0669 Region I visuals unchanged.
- 0671 milestone boss arena/art assets unchanged.
- 0672 Boss II/III/IV encounter depth unchanged.
- Boss Form duration 10s; Boss Energy gain 1/3 unchanged.
- MiMi remains final boss at 80 cards.
- `mimi_walk.png` remains locked.
- 76 active normal-card audit / 80 source entries unchanged.
- Strict TMX CSV validation required.

## In-game acceptance order
1. Real progression: clear Boss II → route console before 60 cards → Region III expedition available.
2. Confirm 500g fare, Airship cutscene, Mirrorwild arrival.
3. Clear all 3 waves; verify native-size enemies, reward totals and southern extraction.
4. Early extraction after wave 1/2 banks only current unbanked cargo.
5. Unexpected warp/death loses unbanked cargo only.
6. At 60 cards, route console must prioritize Boss III rather than Region III.
7. Clear Boss III → Region IV route becomes available while under 80 cards.
8. Region IV full 3-wave clear + 1000g fare + extraction.
9. At 80 cards, route console must prioritize MiMi.
10. Verify Region I helm still starts Hunt Run 2.0 unchanged.

## Next likely pass
- 0675 should be authored Region III/IV enemy + environment art only after 0674 gameplay acceptance/screenshots.
'''
Path('handoff/ALPHA28_0674_REGION3_REGION4_GAMEPLAY_FOUNDATION.md').write_text(handoff, encoding='utf-8')
Path('handoff/LATEST_CARDCHA_HANDOFF.md').write_text(f'''# Latest Cardcha Handoff\n\nCurrent branch: `cardcha-alpha28-0674-region3-region4-gameplay-foundation`\nCurrent build: `{VERSION}`\nContinue from: `handoff/ALPHA28_0674_REGION3_REGION4_GAMEPLAY_FOUNDATION.md`\n\n0674 in-game acceptance is pending. Do not resume from stale `main` or pre-0674 branches.\n''', encoding='utf-8')

print('0674 generator complete')
