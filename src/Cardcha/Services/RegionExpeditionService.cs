using Microsoft.Xna.Framework;
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
