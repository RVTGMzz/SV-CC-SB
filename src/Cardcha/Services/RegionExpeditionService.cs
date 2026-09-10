using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Monsters;

namespace Cardcha.Services;

internal enum ExpeditionRegion
{
    ForgottenArchive = 2,
    Mirrorwild = 3,
    ResonanceVerge = 4,
}

/// <summary>
/// 0676 terrain-depth pass for Region III Mirrorwild and Region IV Resonance Verge.
/// Three-wave gameplay, rewards, route gates, authored enemy silhouettes and extraction remain frozen.
/// Low-profile 64px terrain clusters deepen the two biomes without screen tinting, fake colliders,
/// or any per-enemy sprite enlargement.
/// </summary>
internal sealed class RegionExpeditionService
{
    public const string Region2LocationName = "Cardcha_Region2_ForgottenArchive";
    public const string Region2MapAssetName = "Maps/Cardcha_Region2_ForgottenArchive";
    public const string Region3LocationName = "Cardcha_Region3_Mirrorwild";
    public const string Region3MapAssetName = "Maps/Cardcha_Region3_Mirrorwild";
    public const string Region4LocationName = "Cardcha_Region4_ResonanceVerge";
    public const string Region4MapAssetName = "Maps/Cardcha_Region4_ResonanceVerge";

    private const string Region2MapPath = "assets/region2_forgotten_archive.tmx";
    private const string Region2EnemyAtlasPath = "assets/region2_forgotten_archive_enemies.png";
    private const string Region3MapPath = "assets/region3_mirrorwild.tmx";
    private const string Region4MapPath = "assets/region4_resonance_verge.tmx";
    private const string Region3EnemyAtlasPath = "assets/region3_mirrorwild_enemies.png";
    private const string Region4EnemyAtlasPath = "assets/region4_resonance_enemies.png";
    private const string Region3DecorAtlasPath = "assets/region3_mirrorwild_decor.png";
    private const string Region4DecorAtlasPath = "assets/region4_resonance_decor.png";
    private const string Region3TerrainAtlasPath = "assets/region3_mirrorwild_terrain.png";
    private const string Region4TerrainAtlasPath = "assets/region4_resonance_terrain.png";
    public const string EnemyMarkerKey = "Ronvotri.Cardcha/0674ExpeditionEnemy";
    public const string EnemyRoleKey = "Ronvotri.Cardcha/0674ExpeditionRole";
    private const float AuthoredWorldScale = 4f;
    private const int WaveCount = 3;
    private const long RouteConfirmWindowMs = 5000L;
    private const long ExtractConfirmWindowMs = 5000L;
    private const long BetweenWaveDelayMs = 1100L;

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly AirshipFoundationService Airship;
    private Func<string>? Region2BossGateAction;
    private Func<string>? Region2BossGateDebugAction;

    private static readonly Point Region2BossGateTile = new(20, 4);
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
    private bool BossApproachMode;
    private bool DebugForceNormalRegion2;
    private bool DebugForceBossApproachRegion2;
    private bool DebugBossGateBypassRegion2;
    private Texture2D? Region2EnemyAtlas;
    private Texture2D? Region3EnemyAtlas;
    private Texture2D? Region4EnemyAtlas;
    private Texture2D? Region3DecorAtlas;
    private Texture2D? Region4DecorAtlas;
    private Texture2D? Region3TerrainAtlas;
    private Texture2D? Region4TerrainAtlas;
    private bool Region3ArtLoadFailed;
    private bool Region4ArtLoadFailed;
    private bool Region3TerrainLoadFailed;
    private bool Region4TerrainLoadFailed;

    public RegionExpeditionService(IModHelper helper, IMonitor monitor, SaveService save, AirshipFoundationService airship)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.Airship = airship;
    }

    public void BindRegion2BossGateHandler(Func<string> handler)
        => this.Region2BossGateAction = handler;

    public void BindRegion2BossGateDebugHandler(Func<string> handler)
        => this.Region2BossGateDebugAction = handler;

    /// <summary>
    /// 0680 runtime handoff: Region II roguelike owns the Forgotten Archive after the Airship/permission
    /// layer has accepted the warp. Region III/IV remain on this legacy expedition runtime.
    /// </summary>
    public void SuspendLegacyRegion2RuntimeForRoguelike()
    {
        if (this.CurrentRegion != ExpeditionRegion.ForgottenArchive)
            return;
        if (Game1.currentLocation?.NameOrUniqueName.Equals(Region2LocationName, StringComparison.OrdinalIgnoreCase) == true)
            this.ClearMarkedEnemies(Game1.currentLocation);
        this.CurrentRegion = null;
        this.Active = false;
        this.Completed = false;
        this.WaveSpawned = false;
        this.CurrentWave = 0;
        this.BossApproachMode = false;
        this.NextWaveAtMs = 0;
        this.UnbankedScrap = 0;
        this.UnbankedShiny = 0;
        this.ExtractConfirmUntilMs = 0;
    }

    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)
    {
        if (e.NameWithoutLocale.IsEquivalentTo(Region2MapAssetName))
        {
            e.LoadFromModFile<xTile.Map>(Region2MapPath, AssetLoadPriority.Exclusive);
            return;
        }
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
        this.EnsureLocation(ExpeditionRegion.ForgottenArchive);
        this.EnsureLocation(ExpeditionRegion.Mirrorwild);
        this.EnsureLocation(ExpeditionRegion.ResonanceVerge);
    }

    public void OnDayStarted(object? sender, DayStartedEventArgs e)
    {
        this.ResetRuntime(clearEnemies: true);
        this.EnsureLocation(ExpeditionRegion.ForgottenArchive);
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
                || raw is not (2 or 3 or 4))
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
                this.Monitor.Log($"0676 blocked unauthorized Region {(int)region} entry.", LogLevel.Warn);
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
        if (this.BossApproachMode)
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

        if (this.CurrentRegion == ExpeditionRegion.ForgottenArchive && this.TryUseRegion2BossGate(e.Button, Game1.currentLocation))
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

    private bool TryUseRegion2BossGate(SButton button, GameLocation location)
    {
        Point player = PlayerTile();
        Point action = Game1.player.GetGrabTile().ToPoint();
        bool close = Math.Abs(player.X - Region2BossGateTile.X) <= 2 && Math.Abs(player.Y - Region2BossGateTile.Y) <= 2;
        bool facing = Math.Abs(action.X - Region2BossGateTile.X) <= 1 && Math.Abs(action.Y - Region2BossGateTile.Y) <= 1;
        if (!close && !facing)
            return false;

        this.Helper.Input.Suppress(button);
        int owned = this.Save.Data.OwnedCards?.Count ?? 0;
        bool cleared = this.Save.Data.BossCardsUnlocked?.Contains(MilestoneBossService.MirrorArchiveBossCardId) == true;
        if (cleared && !this.DebugBossGateBypassRegion2)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region2.boss_gate.cleared"));
            return true;
        }
        if (!this.Save.Data.Region1BossDefeated && this.DebugBypassRegion != 2)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region2.boss_gate.boss1"));
            return true;
        }
        if (owned < 40 && !this.DebugBossGateBypassRegion2)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region2.boss_gate.cards", new { cards = owned }));
            return true;
        }
        if (CountMarkedEnemies(location) > 0)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region2.boss_gate.echoes"));
            return true;
        }
        Func<string>? bossAction = this.DebugBossGateBypassRegion2
            ? this.Region2BossGateDebugAction
            : this.Region2BossGateAction;
        bool debugGate = this.DebugBossGateBypassRegion2;
        this.DebugBossGateBypassRegion2 = false;
        if (bossAction is null)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.expedition.unavailable"));
            return true;
        }

        string result = bossAction();
        if (!string.IsNullOrWhiteSpace(result))
            Game1.drawObjectDialogue(result);
        this.Monitor.Log($"0679 Region II Archive Seal used. debug={debugGate}.", LogLevel.Info);
        return true;
    }

    private void StartExpedition(GameLocation location, ExpeditionRegion region)
    {
        this.ClearMarkedEnemies(location);
        this.CurrentRegion = region;
        this.Active = true;
        this.WaveSpawned = false;
        this.CurrentWave = 1;
        this.UnbankedScrap = 0;
        this.UnbankedShiny = 0;
        this.ExtractConfirmUntilMs = 0;

        bool progressionBossApproach = region == ExpeditionRegion.ForgottenArchive
            && this.Save.Data.Region1BossDefeated
            && (this.Save.Data.OwnedCards?.Count ?? 0) >= 40
            && this.Save.Data.BossCardsUnlocked?.Contains(MilestoneBossService.MirrorArchiveBossCardId) != true;
        this.BossApproachMode = region == ExpeditionRegion.ForgottenArchive
            && (this.DebugForceBossApproachRegion2 || (progressionBossApproach && !this.DebugForceNormalRegion2));
        this.DebugForceNormalRegion2 = false;
        this.DebugForceBossApproachRegion2 = false;

        if (this.BossApproachMode)
        {
            this.Completed = true;
            this.CurrentWave = 0;
            this.NextWaveAtMs = 0;
            Game1.playSound("discoverMineral");
            Game1.showGlobalMessage(ModEntry.T("airship.region2.boss_approach"));
            this.Monitor.Log("0679 Region II Boss Approach active: north Archive Seal leads to Hollow Curator.", LogLevel.Info);
            return;
        }

        this.Completed = false;
        this.NextWaveAtMs = Environment.TickCount64 + 700L;
        Game1.showGlobalMessage(ModEntry.T("airship.expedition.arrive", new { region = this.RegionDisplayName(region) }));
        this.Monitor.Log($"0679 expedition started: {region}, 3-wave gameplay with actor-depth enemy art.", LogLevel.Info);
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
        int targetCount = region switch
        {
            ExpeditionRegion.ForgottenArchive => 3 + wave,
            ExpeditionRegion.Mirrorwild => 3 + wave * 2,
            _ => 4 + wave * 2,
        };
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
            enemy.modData[EnemyMarkerKey] = $"0676:{(int)region}:{wave}";
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
        this.Monitor.Log($"0676 {region} wave {wave}/{WaveCount}: spawned={spawned}.", LogLevel.Trace);
    }

    private Monster CreateEnemy(ExpeditionRegion region, int wave, int index, Vector2 position)
    {
        int archetype = (index + wave) % 3;
        Monster monster;
        string role;
        int hp;
        int speed;

        if (region == ExpeditionRegion.ForgottenArchive)
        {
            if (wave == 3 && index == 0)
            {
                monster = new GreenSlime(position, 0);
                role = "archive_warden";
                hp = 390;
                speed = 3;
            }
            else if (archetype == 0)
            {
                monster = new Bat(position);
                role = "ink_moth";
                hp = 85 + wave * 15;
                speed = 4;
            }
            else if (archetype == 1)
            {
                monster = new Bug(position, 0);
                role = "paper_scarab";
                hp = 120 + wave * 20;
                speed = 3;
            }
            else
            {
                monster = new GreenSlime(position, 0);
                role = "dust_slime";
                hp = 160 + wave * 26;
                speed = 2;
            }
        }
        else if (region == ExpeditionRegion.Mirrorwild)
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
        int scrap = region switch
        {
            ExpeditionRegion.ForgottenArchive => wave switch { 1 => 7, 2 => 11, _ => 16 },
            ExpeditionRegion.Mirrorwild => wave switch { 1 => 10, 2 => 15, _ => 22 },
            _ => wave switch { 1 => 15, 2 => 22, _ => 32 },
        };
        int shiny = region switch
        {
            ExpeditionRegion.ForgottenArchive => wave == 3 ? 1 : 0,
            ExpeditionRegion.Mirrorwild => wave == 3 ? 2 : wave == 2 ? 1 : 0,
            _ => wave == 1 ? 1 : wave == 2 ? 2 : 3,
        };
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
        if (this.Save.Data.Region1BossDefeated && this.Save.Data.AirshipHighestRegionUnlocked >= 2)
            result.Add(ExpeditionRegion.ForgottenArchive);
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
        string name = region switch
        {
            ExpeditionRegion.ForgottenArchive => Region2LocationName,
            ExpeditionRegion.Mirrorwild => Region3LocationName,
            _ => Region4LocationName,
        };
        string asset = region switch
        {
            ExpeditionRegion.ForgottenArchive => Region2MapAssetName,
            ExpeditionRegion.Mirrorwild => Region3MapAssetName,
            _ => Region4MapAssetName,
        };
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
            this.Monitor.Log($"0679 couldn't create {name}: {ex.GetType().Name}: {ex.Message}", LogLevel.Error);
            return null;
        }
    }

    private static ExpeditionRegion? ResolveRegion(GameLocation? location)
    {
        string? name = location?.NameOrUniqueName;
        if (name?.Equals(Region2LocationName, StringComparison.OrdinalIgnoreCase) == true)
            return ExpeditionRegion.ForgottenArchive;
        if (name?.Equals(Region3LocationName, StringComparison.OrdinalIgnoreCase) == true)
            return ExpeditionRegion.Mirrorwild;
        if (name?.Equals(Region4LocationName, StringComparison.OrdinalIgnoreCase) == true)
            return ExpeditionRegion.ResonanceVerge;
        return null;
    }

    private string RegionDisplayName(ExpeditionRegion region)
        => ModEntry.T(region switch
        {
            ExpeditionRegion.ForgottenArchive => "airship.expedition.region2",
            ExpeditionRegion.Mirrorwild => "airship.expedition.region3",
            _ => "airship.expedition.region4",
        });

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
            this.ClearMarkedEnemies(Game1.getLocationFromName(Region2LocationName));
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
        this.BossApproachMode = false;
        this.DebugForceNormalRegion2 = false;
        this.DebugForceBossApproachRegion2 = false;
        this.DebugBossGateBypassRegion2 = false;
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

    private void DrawRegionIdentity(SpriteBatch batch, GameLocation location, ExpeditionRegion region)
    {
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 40;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 28;

        Texture2D? terrain = this.GetTerrainAtlas(region);
        if (terrain is not null)
            this.DrawTerrainClusters(batch, terrain, region);

        Texture2D? decor = this.GetDecorAtlas(region);
        if (decor is not null)
            this.DrawDecorClusters(batch, decor, region);

        Point extract = ResolveExtractionTile(location);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, new Vector2(extract.X * 64f + 32f, extract.Y * 64f + 32f));
        Color c = region == ExpeditionRegion.Mirrorwild ? new Color(143, 187, 226) : new Color(197, 135, 218);
        float pulse = 0.44f + 0.11f * (float)Math.Sin(Environment.TickCount64 / 260d);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 25, (int)local.Y - 2, 50, 4), c * pulse);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 2, (int)local.Y - 25, 4, 50), c * pulse);

        // Small ambient flecks only. Terrain identity comes from authored ground forms, not a screen tint.
        for (int i = 0; i < 12; i++)
        {
            int x = 3 + (i * 11 + (int)region * 7) % Math.Max(4, width - 6);
            int y = 3 + (i * 7 + (int)region * 5) % Math.Max(4, height - 7);
            Vector2 p = Game1.GlobalToLocal(Game1.viewport, new Vector2(x * 64f + 32f, y * 64f + 32f));
            int size = i % 4 == 0 ? 3 : 2;
            batch.Draw(Game1.staminaRect, new Rectangle((int)p.X, (int)p.Y, size, size), c * 0.24f);
        }
    }

    private void DrawTerrainClusters(SpriteBatch batch, Texture2D terrain, ExpeditionRegion region)
    {
        // Mirrorwild is deliberately bilateral; Resonance Verge reads as a three-pole elemental triad.
        (Point, int)[] clusters = region == ExpeditionRegion.Mirrorwild
            ? new (Point, int)[]
            {
                (new Point(20,14),0),
                (new Point(10,7),6),(new Point(30,7),6),
                (new Point(7,16),2),(new Point(33,16),2),
                (new Point(12,22),3),(new Point(28,22),3),
                (new Point(13,4),5),(new Point(27,4),5),
                (new Point(5,23),7),(new Point(35,23),7),
                (new Point(17,10),1),(new Point(23,10),1),
                (new Point(15,18),4),(new Point(25,18),4),
            }
            : new (Point, int)[]
            {
                (new Point(20,14),3),
                (new Point(20,6),0),
                (new Point(8,19),1),(new Point(32,19),2),
                (new Point(14,11),6),(new Point(26,11),6),
                (new Point(12,23),4),(new Point(28,23),4),
                (new Point(6,8),5),(new Point(34,8),5),
                (new Point(20,22),7),
                (new Point(8,14),1),(new Point(32,14),2),
            };

        for (int i = 0; i < clusters.Length; i++)
        {
            Point anchor = clusters[i].Item1;
            int cell = clusters[i].Item2;
            Rectangle src = new(cell * 64, 0, 64, 64);
            Vector2 world = new(anchor.X * 64f + 32f, anchor.Y * 64f + 32f);
            Vector2 p = Game1.GlobalToLocal(Game1.viewport, world);
            float alpha = i == 0 ? 0.92f : 0.72f;
            batch.Draw(terrain, p, src, Color.White * alpha, 0f, new Vector2(32f, 32f),
                AuthoredWorldScale, SpriteEffects.None, 0.001f);
        }
    }

    private void DrawDecorClusters(SpriteBatch batch, Texture2D decor, ExpeditionRegion region)
    {
        (Point, int)[] anchors = region == ExpeditionRegion.Mirrorwild
            ? new (Point, int)[]
            {
                (new Point(4,5),0),(new Point(36,5),0),
                (new Point(8,10),3),(new Point(32,10),3),
                (new Point(4,18),6),(new Point(36,18),6),
                (new Point(10,23),1),(new Point(30,23),1),
                (new Point(14,5),2),(new Point(26,5),2),
                (new Point(8,14),7),(new Point(32,14),7),
                (new Point(13,19),4),(new Point(27,19),4),
                (new Point(17,7),5),(new Point(23,7),5),
            }
            : new (Point, int)[]
            {
                (new Point(4,6),6),(new Point(36,6),6),
                (new Point(10,10),0),(new Point(30,10),0),
                (new Point(5,20),3),(new Point(35,20),3),
                (new Point(13,23),1),(new Point(27,23),1),
                (new Point(15,7),2),(new Point(25,7),2),
                (new Point(9,16),7),(new Point(31,16),7),
                (new Point(14,18),4),(new Point(26,18),4),
                (new Point(20,5),5),(new Point(20,20),5),
            };

        for (int i = 0; i < anchors.Length; i++)
        {
            Point a = anchors[i].Item1;
            int cell = anchors[i].Item2;
            Rectangle src = new(cell * 32, 0, 32, 32);
            Vector2 world = new(a.X * 64f + 32f, a.Y * 64f + 58f);
            Vector2 p = Game1.GlobalToLocal(Game1.viewport, world);
            float layer = Math.Clamp((world.Y + 22f) / 10000f, 0f, 0.92f);
            batch.Draw(decor, p, src, Color.White, 0f, new Vector2(16f, 28f),
                AuthoredWorldScale, SpriteEffects.None, layer);
        }
    }

    private void DrawEnemyIdentity(SpriteBatch batch, Monster monster, ExpeditionRegion region)
    {
        if (!monster.modData.TryGetValue(EnemyRoleKey, out string? role) || string.IsNullOrWhiteSpace(role))
            return;

        Texture2D? atlas = this.GetEnemyAtlas(region);
        int roleIndex = RoleIndex(region, role);
        Vector2 world = monster.Position + new Vector2(32f, 64f);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
        float layer = Math.Clamp((world.Y + 32f) / 10000f, 0f, 0.94f);
        bool floating = role is "mirror_wisp" or "ignis_echo" or "aether_mite";
        float bob = floating ? (float)Math.Sin(Environment.TickCount64 / 210d + monster.GetHashCode() * 0.01) * 4f : 0f;

        // A quiet authored shadow keeps the new silhouettes grounded even though their AI proxy is hidden.
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 31, (int)local.Y - 8, 62, 8), Color.Black * 0.20f);
        if (atlas is null || roleIndex < 0)
        {
            Color fallback = region == ExpeditionRegion.Mirrorwild ? new Color(139, 201, 226) : new Color(203, 137, 211);
            batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 18, (int)local.Y - 52, 36, 48), fallback * 0.82f);
            return;
        }

        int frame = (int)((Environment.TickCount64 / 280L + Math.Abs(monster.GetHashCode())) % 2L);
        Rectangle src = new((roleIndex * 2 + frame) * 32, 0, 32, 32);
        batch.Draw(atlas, local + new Vector2(0f, bob), src, Color.White, 0f,
            new Vector2(16f, 28f), AuthoredWorldScale, SpriteEffects.None, layer);
    }

    private Texture2D? GetTerrainAtlas(ExpeditionRegion region)
    {
        try
        {
            if (region == ExpeditionRegion.Mirrorwild)
                return this.Region3TerrainAtlas ??= this.Helper.ModContent.Load<Texture2D>(Region3TerrainAtlasPath);
            return this.Region4TerrainAtlas ??= this.Helper.ModContent.Load<Texture2D>(Region4TerrainAtlasPath);
        }
        catch (Exception ex)
        {
            if (region == ExpeditionRegion.Mirrorwild && !this.Region3TerrainLoadFailed)
            {
                this.Region3TerrainLoadFailed = true;
                this.Monitor.Log($"0676 Mirrorwild terrain atlas unavailable: {ex.GetType().Name}: {ex.Message}", LogLevel.Warn);
            }
            else if (region == ExpeditionRegion.ResonanceVerge && !this.Region4TerrainLoadFailed)
            {
                this.Region4TerrainLoadFailed = true;
                this.Monitor.Log($"0676 Resonance terrain atlas unavailable: {ex.GetType().Name}: {ex.Message}", LogLevel.Warn);
            }
            return null;
        }
    }

    private Texture2D? GetEnemyAtlas(ExpeditionRegion region)
    {
        try
        {
            if (region == ExpeditionRegion.Mirrorwild)
                return this.Region3EnemyAtlas ??= this.Helper.ModContent.Load<Texture2D>(Region3EnemyAtlasPath);
            return this.Region4EnemyAtlas ??= this.Helper.ModContent.Load<Texture2D>(Region4EnemyAtlasPath);
        }
        catch (Exception ex)
        {
            if (region == ExpeditionRegion.Mirrorwild && !this.Region3ArtLoadFailed)
            {
                this.Region3ArtLoadFailed = true;
                this.Monitor.Log($"0676 Mirrorwild enemy atlas unavailable: {ex.GetType().Name}: {ex.Message}", LogLevel.Warn);
            }
            else if (region == ExpeditionRegion.ResonanceVerge && !this.Region4ArtLoadFailed)
            {
                this.Region4ArtLoadFailed = true;
                this.Monitor.Log($"0676 Resonance enemy atlas unavailable: {ex.GetType().Name}: {ex.Message}", LogLevel.Warn);
            }
            return null;
        }
    }

    private Texture2D? GetDecorAtlas(ExpeditionRegion region)
    {
        try
        {
            if (region == ExpeditionRegion.Mirrorwild)
                return this.Region3DecorAtlas ??= this.Helper.ModContent.Load<Texture2D>(Region3DecorAtlasPath);
            return this.Region4DecorAtlas ??= this.Helper.ModContent.Load<Texture2D>(Region4DecorAtlasPath);
        }
        catch
        {
            return null;
        }
    }

    private static int RoleIndex(ExpeditionRegion region, string role)
        => region switch
        {
            ExpeditionRegion.Mirrorwild => role switch
            {
                "mirror_wisp" => 0,
                "glass_scarab" => 1,
                "echo_slime" => 2,
                "mirror_sentinel" => 3,
                _ => -1,
            },
            _ => role switch
            {
                "ignis_echo" => 0,
                "vita_husk" => 1,
                "aether_mite" => 2,
                "resonant_prime" => 3,
                _ => -1,
            }
        };

    public string Describe()
    {
        if (!Context.IsWorldReady)
            return "0679 Expedition=<no save>";
        string pending = this.PendingRouteRegion?.ToString() ?? "none";
        double confirm = this.PendingRouteUntilMs > Environment.TickCount64 ? (this.PendingRouteUntilMs - Environment.TickCount64) / 1000d : 0d;
        return $"0679 Expedition | Available=[{string.Join(',', this.GetAvailableRegions())}] | Current={this.CurrentRegion?.ToString() ?? "none"} | " +
               $"Active={this.Active} Complete={this.Completed} BossApproach={this.BossApproachMode} Wave={this.CurrentWave}/{WaveCount} Spawned={this.WaveSpawned} | " +
               $"Unbanked={this.UnbankedScrap} Scrap + {this.UnbankedShiny} Shiny | Pending={pending}:{confirm:0.0}s | Schema=19";
    }

    public string DebugEnter(int region)
    {
        if (!Context.IsWorldReady || region is not (2 or 3 or 4))
            return "0679 TEST: load a save and use region 2, 3 or 4.";
        ExpeditionRegion target = (ExpeditionRegion)region;
        GameLocation? location = this.EnsureLocation(target);
        if (location is null)
            return $"0679 TEST: Region {region} map unavailable.";
        this.DebugBypassRegion = region;
        if (region == 2)
            this.DebugForceNormalRegion2 = true;
        Point arrival = ResolveArrivalTile(location);
        Game1.warpFarmer(location.NameOrUniqueName, arrival.X, arrival.Y, 0);
        return $"0679 TEST: entered Region {region} with runtime-only gate bypass. Save unlock state unchanged.";
    }

    public string DebugEnterRegion2BossApproach()
    {
        if (!Context.IsWorldReady)
            return "0679 TEST: load a save first.";
        GameLocation? location = this.EnsureLocation(ExpeditionRegion.ForgottenArchive);
        if (location is null)
            return "0679 TEST: Region II map unavailable.";
        this.DebugBypassRegion = 2;
        this.DebugForceBossApproachRegion2 = true;
        this.DebugBossGateBypassRegion2 = true;
        Point arrival = ResolveArrivalTile(location);
        Game1.warpFarmer(location.NameOrUniqueName, arrival.X, arrival.Y, 0);
        return "0679 TEST: entered Region II Boss Approach. Walk north to the Archive Seal; save progression is unchanged.";
    }

    public string DebugClearWave()
    {
        if (!Context.IsWorldReady || !this.Active || Game1.currentLocation is null || ResolveRegion(Game1.currentLocation) is null)
            return "0679 TEST: enter an active Region II/III/IV expedition first.";
        this.ClearMarkedEnemies(Game1.currentLocation);
        return $"0679 TEST: cleared current wave actors. {this.Describe()}";
    }
}
