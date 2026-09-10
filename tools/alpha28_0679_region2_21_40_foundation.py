#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json, re
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src' / 'Cardcha'
OLD = '0.3.0-alpha.28.0.4.14.4.5.12.46'
V = '0.3.0-alpha.28.0.4.14.4.5.12.47'


def rep(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'0679 generator anchor missing: {label}')
    return text.replace(old, new, 1)


def replace_block(text: str, start_token: str, end_token: str, new_block: str, label: str) -> str:
    try:
        start = text.index(start_token)
        end = text.index(end_token, start)
    except ValueError:
        raise SystemExit(f'0679 block anchor missing: {label}')
    return text[:start] + new_block + text[end:]

# ---------------------------------------------------------------------------
# Version bump.
manifest_path = SRC / 'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['Version'] = V
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for rel in ['Cardcha.csproj', 'Directory.Build.targets', 'ModEntry.cs']:
    p = SRC / rel
    t = p.read_text(encoding='utf-8')
    t = t.replace(OLD, V)
    p.write_text(t, encoding='utf-8')

# ---------------------------------------------------------------------------
# Airship generic route: Region II uses the already-existing 250g fare.
airship_path = SRC / 'Services' / 'AirshipFoundationService.cs'
a = airship_path.read_text(encoding='utf-8')
a = rep(a, 'if (!Context.IsWorldReady || region is not (3 or 4))',
           'if (!Context.IsWorldReady || region is not (2 or 3 or 4))',
           'Airship external route region gate')
airship_path.write_text(a, encoding='utf-8')

# ---------------------------------------------------------------------------
# Region expedition service: add Region II as the 21-40 card biome and Boss II approach.
svc_path = SRC / 'Services' / 'RegionExpeditionService.cs'
s = svc_path.read_text(encoding='utf-8')
s = rep(s,
'''internal enum ExpeditionRegion
{
    Mirrorwild = 3,
    ResonanceVerge = 4,
}''',
'''internal enum ExpeditionRegion
{
    ForgottenArchive = 2,
    Mirrorwild = 3,
    ResonanceVerge = 4,
}''', 'ExpeditionRegion enum')

s = rep(s,
'''internal sealed class RegionExpeditionService
{
    public const string Region3LocationName = "Cardcha_Region3_Mirrorwild";''',
'''internal sealed class RegionExpeditionService
{
    public const string Region2LocationName = "Cardcha_Region2_ForgottenArchive";
    public const string Region2MapAssetName = "Maps/Cardcha_Region2_ForgottenArchive";
    public const string Region3LocationName = "Cardcha_Region3_Mirrorwild";''', 'Region2 constants')

s = rep(s,
'''    private const string Region3MapPath = "assets/region3_mirrorwild.tmx";''',
'''    private const string Region2MapPath = "assets/region2_forgotten_archive.tmx";
    private const string Region2EnemyAtlasPath = "assets/region2_forgotten_archive_enemies.png";
    private const string Region3MapPath = "assets/region3_mirrorwild.tmx";''', 'Region2 paths')

s = rep(s,
'''    private readonly AirshipFoundationService Airship;

    private ExpeditionRegion? CurrentRegion;''',
'''    private readonly AirshipFoundationService Airship;
    private Func<string>? Region2BossGateAction;

    private static readonly Point Region2BossGateTile = new(20, 4);
    private ExpeditionRegion? CurrentRegion;''', 'Region2 boss callback')

s = rep(s,
'''    private int DebugBypassRegion;
    private Texture2D? Region3EnemyAtlas;''',
'''    private int DebugBypassRegion;
    private bool BossApproachMode;
    private bool DebugForceNormalRegion2;
    private bool DebugForceBossApproachRegion2;
    private Texture2D? Region2EnemyAtlas;
    private Texture2D? Region3EnemyAtlas;''', 'Region2 runtime fields')

s = rep(s,
'''    public RegionExpeditionService(IModHelper helper, IMonitor monitor, SaveService save, AirshipFoundationService airship)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.Airship = airship;
    }

    public void OnAssetRequested''',
'''    public RegionExpeditionService(IModHelper helper, IMonitor monitor, SaveService save, AirshipFoundationService airship)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.Airship = airship;
    }

    public void BindRegion2BossGateHandler(Func<string> handler)
        => this.Region2BossGateAction = handler;

    public void OnAssetRequested''', 'bind Boss II gate')

s = rep(s,
'''    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)
    {
        if (e.NameWithoutLocale.IsEquivalentTo(Region3MapAssetName))''',
'''    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)
    {
        if (e.NameWithoutLocale.IsEquivalentTo(Region2MapAssetName))
        {
            e.LoadFromModFile<xTile.Map>(Region2MapPath, AssetLoadPriority.Exclusive);
            return;
        }
        if (e.NameWithoutLocale.IsEquivalentTo(Region3MapAssetName))''', 'Region2 asset request')

s = s.replace('        this.EnsureLocation(ExpeditionRegion.Mirrorwild);\n        this.EnsureLocation(ExpeditionRegion.ResonanceVerge);',
'''        this.EnsureLocation(ExpeditionRegion.ForgottenArchive);
        this.EnsureLocation(ExpeditionRegion.Mirrorwild);
        this.EnsureLocation(ExpeditionRegion.ResonanceVerge);''')

s = rep(s, '|| raw is not (3 or 4))', '|| raw is not (2 or 3 or 4))', 'route dialogue Region2 parser')

# Boss gate interaction must be checked before the southern extraction pad.
onbutton_anchor = '''        if (ResolveRegion(Game1.currentLocation) != this.CurrentRegion)
            return;

        Point extract = ResolveExtractionTile(Game1.currentLocation);'''
s = rep(s, onbutton_anchor,
'''        if (ResolveRegion(Game1.currentLocation) != this.CurrentRegion)
            return;

        if (this.CurrentRegion == ExpeditionRegion.ForgottenArchive && this.TryUseRegion2BossGate(e.Button, Game1.currentLocation))
            return;

        Point extract = ResolveExtractionTile(Game1.currentLocation);''', 'Region2 boss gate input')

# Boss approach waits for gate interaction instead of spawning a combat wave.
update_anchor = '''        if (ResolveRegion(Game1.currentLocation) != this.CurrentRegion)
            return;

        long now = Environment.TickCount64;'''
s = rep(s, update_anchor,
'''        if (ResolveRegion(Game1.currentLocation) != this.CurrentRegion)
            return;
        if (this.BossApproachMode)
            return;

        long now = Environment.TickCount64;''', 'Region2 boss approach update gate')

start_block = r'''    private bool TryUseRegion2BossGate(SButton button, GameLocation location)
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
        if (cleared)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region2.boss_gate.cleared"));
            return true;
        }
        if (!this.Save.Data.Region1BossDefeated && this.DebugBypassRegion != 2)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region2.boss_gate.boss1"));
            return true;
        }
        if (owned < 40 && !this.DebugForceBossApproachRegion2)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region2.boss_gate.cards", new { cards = owned }));
            return true;
        }
        if (CountMarkedEnemies(location) > 0)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region2.boss_gate.echoes"));
            return true;
        }
        if (this.Region2BossGateAction is null)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.expedition.unavailable"));
            return true;
        }

        string result = this.Region2BossGateAction();
        if (!string.IsNullOrWhiteSpace(result))
            Game1.drawObjectDialogue(result);
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

'''
s = replace_block(s, '    private void StartExpedition(GameLocation location, ExpeditionRegion region)', '    private void SpawnWave', start_block, 'StartExpedition + boss gate')

# Region II has a slightly lighter enemy count than later regions.
s = rep(s,
'        int targetCount = region == ExpeditionRegion.Mirrorwild ? 3 + wave * 2 : 4 + wave * 2;',
'''        int targetCount = region switch
        {
            ExpeditionRegion.ForgottenArchive => 3 + wave,
            ExpeditionRegion.Mirrorwild => 3 + wave * 2,
            _ => 4 + wave * 2,
        };''', 'Region2 wave count')

create_enemy = r'''    private Monster CreateEnemy(ExpeditionRegion region, int wave, int index, Vector2 position)
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

'''
s = replace_block(s, '    private Monster CreateEnemy(', '    private void AwardWave', create_enemy, 'CreateEnemy')

award = r'''    private void AwardWave(ExpeditionRegion region, int wave)
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

'''
s = replace_block(s, '    private void AwardWave(', '    private void BankRewards', award, 'AwardWave')

available = r'''    private List<ExpeditionRegion> GetAvailableRegions()
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

'''
s = replace_block(s, '    private List<ExpeditionRegion> GetAvailableRegions()', '    private bool CanEnter', available, 'GetAvailableRegions')

ensure = r'''    private GameLocation? EnsureLocation(ExpeditionRegion region)
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

'''
s = replace_block(s, '    private GameLocation? EnsureLocation(ExpeditionRegion region)', '    private static ExpeditionRegion? ResolveRegion', ensure, 'EnsureLocation')

resolve = r'''    private static ExpeditionRegion? ResolveRegion(GameLocation? location)
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

'''
s = replace_block(s, '    private static ExpeditionRegion? ResolveRegion(GameLocation? location)', '    private static Point ResolveArrivalTile', resolve, 'ResolveRegion + display')

# Clear Region II runtime enemies too and reset boss-approach state.
s = rep(s,
'''            this.ClearMarkedEnemies(Game1.getLocationFromName(Region3LocationName));
            this.ClearMarkedEnemies(Game1.getLocationFromName(Region4LocationName));''',
'''            this.ClearMarkedEnemies(Game1.getLocationFromName(Region2LocationName));
            this.ClearMarkedEnemies(Game1.getLocationFromName(Region3LocationName));
            this.ClearMarkedEnemies(Game1.getLocationFromName(Region4LocationName));''', 'Region2 reset clear')
s = rep(s,
'''        this.ExtractConfirmUntilMs = 0;
    }

    private void ReturnToDeckImmediate''',
'''        this.ExtractConfirmUntilMs = 0;
        this.BossApproachMode = false;
        this.DebugForceNormalRegion2 = false;
        this.DebugForceBossApproachRegion2 = false;
    }

    private void ReturnToDeckImmediate''', 'Region2 reset flags')

# Tail debug/status methods.
describe_tail = r'''    public string Describe()
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
'''
s = replace_block(s, '    public string Describe()', '\n}', describe_tail, 'Describe/debug tail')
svc_path.write_text(s, encoding='utf-8')

# ---------------------------------------------------------------------------
# Milestone route: Boss II now belongs to Region II, and the north gate owns the final warp.
mb_path = SRC / 'Services' / 'MilestoneBossService.cs'
mb = mb_path.read_text(encoding='utf-8')
insert_before = '    public string UseAirshipMilestoneRoute()\n'
if insert_before not in mb:
    raise SystemExit('0679 Milestone UseAirship route anchor missing')
method = r'''    public string EnterBoss2FromRegion2()
    {
        if (!Context.IsWorldReady)
            return ModEntry.T("airship.milestone.unavailable");
        if (!Game1.currentLocation?.NameOrUniqueName.Equals(RegionExpeditionService.Region2LocationName, StringComparison.OrdinalIgnoreCase) == true)
            return ModEntry.T("airship.region2.boss_gate.location");
        if (!this.Save.Data.Region1BossDefeated)
            return ModEntry.T("airship.milestone.boss1_required");
        int owned = this.Save.Data.OwnedCards?.Count ?? 0;
        if (owned < 40)
            return ModEntry.T("airship.region2.boss_gate.cards", new { cards = owned });
        if (this.Save.Data.BossCardsUnlocked?.Contains(MirrorArchiveBossCardId) == true)
            return ModEntry.T("airship.region2.boss_gate.cleared");

        GameLocation? arena = this.EnsureLocation(MilestoneBossKind.HollowCurator);
        if (arena is null)
            return ModEntry.T("airship.milestone.unavailable");
        Game1.playSound("wand");
        Game1.warpFarmer(arena.NameOrUniqueName, ArrivalTile.X, ArrivalTile.Y, 0);
        return string.Empty;
    }

'''
mb = mb.replace(insert_before, method + insert_before, 1)

mb = rep(mb,
'''            if (kind != MilestoneBossKind.HollowCurator && this.ExpeditionRouteAction is not null)
                return this.ExpeditionRouteAction(owned, required, name);''',
'''            if (this.ExpeditionRouteAction is not null)
                return this.ExpeditionRouteAction(owned, required, name);''', 'Boss II below-40 Region II route')

boss2_route_anchor = '''        long now = Environment.TickCount64;
        if (this.RouteConfirmKind != kind || this.RouteConfirmUntilMs <= now)'''
mb = rep(mb, boss2_route_anchor,
'''        // 0679: the 40-card milestone no longer teleports straight into Boss II.
        // Hollow Curator belongs to Region II, so the Airship lands in the Forgotten Archive;
        // the physical north Archive Seal is the boss entrance.
        if (kind == MilestoneBossKind.HollowCurator && this.ExpeditionRouteAction is not null)
        {
            this.RouteConfirmUntilMs = 0;
            this.RouteConfirmKind = null;
            return this.ExpeditionRouteAction(owned, required, name);
        }

        long now = Environment.TickCount64;
        if (this.RouteConfirmKind != kind || this.RouteConfirmUntilMs <= now)''', 'Boss II threshold route through Region II')
mb = mb.replace('return $"0674 MilestoneRoute |', 'return $"0679 MilestoneRoute |')
mb = mb.replace('return $"0674 MilestoneBoss |', 'return $"0679 MilestoneBoss |')
mb_path.write_text(mb, encoding='utf-8')

# ---------------------------------------------------------------------------
# ModEntry wiring + test commands.
mod_path = SRC / 'ModEntry.cs'
mod = mod_path.read_text(encoding='utf-8')
mod = rep(mod,
'''        this.MilestoneBosses = new MilestoneBossService(helper, this.Monitor, this.Save);
        this.MilestoneBosses.BindExpeditionRouteHandler(this.RegionExpeditions.UseRouteConsole);''',
'''        this.MilestoneBosses = new MilestoneBossService(helper, this.Monitor, this.Save);
        this.MilestoneBosses.BindExpeditionRouteHandler(this.RegionExpeditions.UseRouteConsole);
        this.RegionExpeditions.BindRegion2BossGateHandler(this.MilestoneBosses.EnterBoss2FromRegion2);''', 'Region2 boss gate wiring')

mod = rep(mod,
'''        helper.ConsoleCommands.Add("cardcha_expedition_status", "Show Region III/IV expedition runtime and route state.", (_, _) => this.Monitor.Log(this.RegionExpeditions.Describe(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_test_region3",''',
'''        helper.ConsoleCommands.Add("cardcha_expedition_status", "Show Region II/III/IV expedition runtime and route state.", (_, _) => this.Monitor.Log(this.RegionExpeditions.Describe(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_test_region2", "TEST ONLY: enter Region II Forgotten Archive as a normal 21-40 progression run.", (_, _) => this.Monitor.Log(this.RegionExpeditions.DebugEnter(2), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_test_region2_bossgate", "TEST ONLY: enter Region II Boss Approach and test the north Archive Seal.", (_, _) => this.Monitor.Log(this.RegionExpeditions.DebugEnterRegion2BossApproach(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_test_region3",''', 'Region2 test commands')
mod = mod.replace('TEST ONLY: clear current Region III/IV expedition wave.', 'TEST ONLY: clear current Region II/III/IV expedition wave.')
mod = re.sub(r'"Cardcha! ' + re.escape(V) + r' [^"]+ TEST"',
             f'"Cardcha! {V} 0679 REGION II 21-40 + BOSS II APPROACH TEST"', mod, count=1)
mod_path.write_text(mod, encoding='utf-8')

# ---------------------------------------------------------------------------
# Region II actor-depth renderer in the existing expedition Monster.draw patch.
patch_path = SRC / 'Patches' / 'RegionExpeditionProxyDrawPatch.cs'
p = patch_path.read_text(encoding='utf-8')
p = rep(p,
'''    private const string Region3EnemyAtlasPath = "assets/region3_mirrorwild_enemies.png";''',
'''    private const string Region2EnemyAtlasPath = "assets/region2_forgotten_archive_enemies.png";
    private const string Region3EnemyAtlasPath = "assets/region3_mirrorwild_enemies.png";''', 'Region2 enemy atlas path patch')
p = rep(p,
'''    private static Texture2D? Region3EnemyAtlas;''',
'''    private static Texture2D? Region2EnemyAtlas;
    private static Texture2D? Region3EnemyAtlas;''', 'Region2 enemy atlas field')
p = rep(p,
'''    private static bool Region3AtlasFailed;''',
'''    private static bool Region2AtlasFailed;
    private static bool Region3AtlasFailed;''', 'Region2 enemy atlas fail flag')
p = p.replace('Region III/IV', 'Region II/III/IV')
p = p.replace('role is "mirror_wisp" or "ignis_echo" or "aether_mite"', 'role is "ink_moth" or "mirror_wisp" or "ignis_echo" or "aether_mite"')
p = rep(p,
'''            Color fallback = region == ExpeditionRegion.Mirrorwild
                ? new Color(139, 201, 226)
                : new Color(203, 137, 211);''',
'''            Color fallback = region switch
            {
                ExpeditionRegion.ForgottenArchive => new Color(187, 164, 122),
                ExpeditionRegion.Mirrorwild => new Color(139, 201, 226),
                _ => new Color(203, 137, 211),
            };''', 'Region2 fallback color')
p = rep(p,
'''        Color accent = region == ExpeditionRegion.Mirrorwild
            ? new Color(143, 187, 226)
            : new Color(197, 135, 218);''',
'''        Color accent = region switch
        {
            ExpeditionRegion.ForgottenArchive => new Color(208, 174, 112),
            ExpeditionRegion.Mirrorwild => new Color(143, 187, 226),
            _ => new Color(197, 135, 218),
        };''', 'Region2 extraction accent')
p = rep(p,
'''        if (name?.Equals(RegionExpeditionService.Region3LocationName, StringComparison.OrdinalIgnoreCase) == true)
            return ExpeditionRegion.Mirrorwild;''',
'''        if (name?.Equals(RegionExpeditionService.Region2LocationName, StringComparison.OrdinalIgnoreCase) == true)
            return ExpeditionRegion.ForgottenArchive;
        if (name?.Equals(RegionExpeditionService.Region3LocationName, StringComparison.OrdinalIgnoreCase) == true)
            return ExpeditionRegion.Mirrorwild;''', 'Region2 resolve patch')

get_atlas_old = '''        try
        {
            if (region == ExpeditionRegion.Mirrorwild)
            {
                if (Region3AtlasFailed)
                    return null;
                return Region3EnemyAtlas ??= ModEntry.StaticHelper?.ModContent.Load<Texture2D>(Region3EnemyAtlasPath);
            }

            if (Region4AtlasFailed)
                return null;
            return Region4EnemyAtlas ??= ModEntry.StaticHelper?.ModContent.Load<Texture2D>(Region4EnemyAtlasPath);
        }
        catch (Exception ex)
        {
            if (region == ExpeditionRegion.Mirrorwild)
                Region3AtlasFailed = true;
            else
                Region4AtlasFailed = true;'''
get_atlas_new = '''        try
        {
            if (region == ExpeditionRegion.ForgottenArchive)
            {
                if (Region2AtlasFailed)
                    return null;
                return Region2EnemyAtlas ??= ModEntry.StaticHelper?.ModContent.Load<Texture2D>(Region2EnemyAtlasPath);
            }
            if (region == ExpeditionRegion.Mirrorwild)
            {
                if (Region3AtlasFailed)
                    return null;
                return Region3EnemyAtlas ??= ModEntry.StaticHelper?.ModContent.Load<Texture2D>(Region3EnemyAtlasPath);
            }

            if (Region4AtlasFailed)
                return null;
            return Region4EnemyAtlas ??= ModEntry.StaticHelper?.ModContent.Load<Texture2D>(Region4EnemyAtlasPath);
        }
        catch (Exception ex)
        {
            if (region == ExpeditionRegion.ForgottenArchive)
                Region2AtlasFailed = true;
            else if (region == ExpeditionRegion.Mirrorwild)
                Region3AtlasFailed = true;
            else
                Region4AtlasFailed = true;'''
p = rep(p, get_atlas_old, get_atlas_new, 'Region2 GetEnemyAtlas patch')

role_old = '''        => region switch
        {
            ExpeditionRegion.Mirrorwild => role switch'''
role_new = '''        => region switch
        {
            ExpeditionRegion.ForgottenArchive => role switch
            {
                "ink_moth" => 0,
                "paper_scarab" => 1,
                "dust_slime" => 2,
                "archive_warden" => 3,
                _ => -1,
            },
            ExpeditionRegion.Mirrorwild => role switch'''
p = rep(p, role_old, role_new, 'Region2 role index patch')
patch_path.write_text(p, encoding='utf-8')

# ---------------------------------------------------------------------------
# i18n.
for lang in ['default.json', 'vi.json']:
    ip = SRC / 'i18n' / lang
    data = json.loads(ip.read_text(encoding='utf-8'))
    if lang == 'vi.json':
        data.update({
            'airship.expedition.region2': 'Khu II • Kho Lưu Trữ Lãng Quên',
            'airship.region2.boss_approach': 'Kho Lưu Trữ đã mở đường đến cánh cổng phía bắc. Hollow Curator đang chờ sau Ấn Lưu Trữ.',
            'airship.region2.boss_gate.cards': 'Ấn Lưu Trữ chưa phản hồi. Cần đủ 40 lá bài để mở đường đến Hollow Curator. Hiện có {{cards}}/40.',
            'airship.region2.boss_gate.echoes': 'Ấn Lưu Trữ bị nhiễu bởi những Echo còn sống. Hãy dọn sạch kẻ địch trước.',
            'airship.region2.boss_gate.boss1': 'Đường đến Hollow Curator chỉ xuất hiện sau khi Verdant Guardian đã thực sự bị đánh bại.',
            'airship.region2.boss_gate.cleared': 'Hollow Curator đã bị đánh bại. Ấn Lưu Trữ giờ chỉ còn là một cánh cổng im lặng.',
            'airship.region2.boss_gate.location': 'Cổng Hollow Curator chỉ có thể được mở từ Khu II • Kho Lưu Trữ Lãng Quên.',
        })
    else:
        data.update({
            'airship.expedition.region2': 'Region II • Forgotten Archive',
            'airship.region2.boss_approach': 'The Archive route has stabilized. Hollow Curator waits beyond the north Archive Seal.',
            'airship.region2.boss_gate.cards': 'The Archive Seal is dormant. Own 40 cards to reach Hollow Curator. Current: {{cards}}/40.',
            'airship.region2.boss_gate.echoes': 'Living echoes are disrupting the Archive Seal. Clear the enemies first.',
            'airship.region2.boss_gate.boss1': 'The route to Hollow Curator appears only after Verdant Guardian is truly defeated.',
            'airship.region2.boss_gate.cleared': 'Hollow Curator has already been defeated. The Archive Seal is quiet now.',
            'airship.region2.boss_gate.location': 'Hollow Curator can only be entered through Region II • Forgotten Archive.',
        })
    ip.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# ---------------------------------------------------------------------------
# Authored Region II enemy atlas, 4 roles x 2 frames, 32x32 each.
assets = SRC / 'assets'
atlas = Image.new('RGBA', (256, 32), (0, 0, 0, 0))

def frame_canvas(index: int):
    return ImageDraw.Draw(atlas), index * 32

# Ink Moth: parchment core + dark ink wings.
for f in range(2):
    d, ox = frame_canvas(f)
    wing = (66, 58, 92, 255); wing2 = (91, 72, 112, 255); paper = (224, 206, 166, 255); ink=(39,35,54,255)
    dy = 1 if f else 0
    d.polygon([(ox+15,14+dy),(ox+5,6+dy),(ox+3,14+dy),(ox+9,20+dy),(ox+15,18+dy)], fill=wing)
    d.polygon([(ox+17,14+dy),(ox+27,6+dy),(ox+29,14+dy),(ox+23,20+dy),(ox+17,18+dy)], fill=wing2)
    d.rectangle((ox+13,9+dy,ox+19,22+dy), fill=paper)
    d.rectangle((ox+15,12+dy,ox+17,20+dy), fill=ink)
    d.point((ox+10,11+dy), fill=(194,151,236,255)); d.point((ox+22,11+dy), fill=(194,151,236,255))
# Paper Scarab.
for f in range(2):
    ox=(2+f)*32; d=ImageDraw.Draw(atlas); dy=f
    shell=(217,194,151,255); edge=(111,96,121,255); blue=(116,167,190,255); dark=(54,47,62,255)
    d.ellipse((ox+8,8+dy,ox+24,24+dy), fill=edge)
    d.ellipse((ox+10,9+dy,ox+22,22+dy), fill=shell)
    d.line((ox+16,10+dy,ox+16,22+dy), fill=dark, width=2)
    for yy in (12,18):
        d.line((ox+9,yy+dy,ox+4,yy-2+dy), fill=dark, width=2); d.line((ox+23,yy+dy,ox+28,yy-2+dy), fill=dark, width=2)
    d.rectangle((ox+13,6+dy,ox+19,9+dy), fill=blue)
# Dust Slime.
for f in range(2):
    ox=(4+f)*32; d=ImageDraw.Draw(atlas); h=1 if f else 0
    dust=(156,145,132,255); light=(198,183,157,255); ink=(76,65,71,255); paper=(235,220,180,255)
    d.rounded_rectangle((ox+6,11-h,ox+26,25), radius=6, fill=dust)
    d.rectangle((ox+8,18-h,ox+24,25), fill=light)
    d.rectangle((ox+11,15-h,ox+13,17-h), fill=ink); d.rectangle((ox+20,15-h,ox+22,17-h), fill=ink)
    d.rectangle((ox+15,10-h,ox+18,13-h), fill=paper)
    d.point((ox+9,11-h), fill=paper); d.point((ox+24,13-h), fill=paper)
# Archive Warden: book/mirror construct.
for f in range(2):
    ox=(6+f)*32; d=ImageDraw.Draw(atlas); lift=1 if f else 0
    stone=(91,82,91,255); gold=(207,168,91,255); glass=(126,182,196,255); paper=(222,203,166,255); dark=(46,42,51,255)
    d.rectangle((ox+8,10-lift,ox+24,25), fill=stone)
    d.rectangle((ox+10,12-lift,ox+22,22), fill=dark)
    d.polygon([(ox+16,7-lift),(ox+21,13-lift),(ox+16,19-lift),(ox+11,13-lift)], fill=glass)
    d.rectangle((ox+7,8-lift,ox+9,24), fill=gold); d.rectangle((ox+23,8-lift,ox+25,24), fill=gold)
    d.rectangle((ox+11,23,ox+21,26), fill=paper)
    d.point((ox+16,12-lift), fill=(238,238,218,255))
atlas.save(assets / 'region2_forgotten_archive_enemies.png')

# ---------------------------------------------------------------------------
# Region II 16px map tiles: subtle ground marks, archive ruins, and a 3x3 north seal.
tiles = Image.new('RGBA', (256, 64), (0,0,0,0))
d = ImageDraw.Draw(tiles)

def box(idx):
    return ((idx % 16)*16, (idx // 16)*16)

# 0..7 subtle ground motifs.
for idx in range(8):
    ox,oy=box(idx)
    if idx==0:
        d.line((ox+2,oy+11,ox+7,oy+8,ox+10,oy+10,ox+14,oy+5), fill=(122,108,94,180), width=1)
    elif idx==1:
        d.rectangle((ox+4,oy+6,ox+10,oy+10), fill=(221,204,167,220)); d.line((ox+5,oy+8,ox+9,oy+8), fill=(111,95,83,220))
    elif idx==2:
        d.polygon([(ox+8,oy+2),(ox+12,oy+8),(ox+8,oy+14),(ox+4,oy+8)], fill=(120,174,188,180))
    elif idx==3:
        d.rectangle((ox+3,oy+3,ox+12,oy+12), outline=(188,151,89,180)); d.rectangle((ox+6,oy+6,ox+9,oy+9), fill=(115,90,125,180))
    elif idx==4:
        for px,py in [(3,4),(11,5),(6,11),(13,13),(9,8)]: d.point((ox+px,oy+py), fill=(94,78,76,180))
    elif idx==5:
        d.arc((ox+3,oy+3,ox+13,oy+13), 20, 250, fill=(153,124,167,180)); d.point((ox+8,oy+8), fill=(216,190,112,200))
    elif idx==6:
        d.rectangle((ox+2,oy+10,ox+14,oy+13), fill=(91,109,78,170)); d.point((ox+5,oy+8), fill=(117,139,93,190)); d.point((ox+11,oy+9), fill=(117,139,93,190))
    elif idx==7:
        d.ellipse((ox+4,oy+6,ox+12,oy+11), fill=(63,53,69,150)); d.point((ox+9,oy+8), fill=(121,89,139,180))

# 8..15 rug/stone accents.
for idx in range(8,16):
    ox,oy=box(idx); c=(143,119,94,150) if idx%2==0 else (103,117,121,140)
    d.rectangle((ox+1,oy+1,ox+14,oy+14), outline=c)
    if idx%3==0: d.line((ox+3,oy+8,ox+13,oy+8), fill=c)

# 16..24: 3x3 Archive Seal pieces.
seal_bg=(66,60,72,255); seal_edge=(174,143,83,255); seal_glass=(103,164,183,255); seal_glow=(206,190,130,255)
for i in range(9):
    ox,oy=box(16+i); r=i//3; c=i%3
    d.rectangle((ox,oy,ox+15,oy+15), fill=seal_bg)
    if c==0: d.rectangle((ox,oy,ox+3,oy+15), fill=seal_edge)
    if c==2: d.rectangle((ox+12,oy,ox+15,oy+15), fill=seal_edge)
    if r==0: d.rectangle((ox,oy,ox+15,oy+3), fill=seal_edge)
    if r==2: d.rectangle((ox,oy+12,ox+15,oy+15), fill=seal_edge)
    if i==4:
        d.polygon([(ox+8,oy+2),(ox+13,oy+8),(ox+8,oy+13),(ox+3,oy+8)], fill=seal_glass)
        d.rectangle((ox+7,oy+6,ox+9,oy+10), fill=seal_glow)
    elif i in (1,3,5,7):
        d.line((ox+3,oy+8,ox+13,oy+8), fill=seal_glass, width=1)

# 25..39: shelves, columns, book piles, mirror plinths.
for idx in range(25,40):
    ox,oy=box(idx)
    if idx in (25,26,27,28):
        d.rectangle((ox+3,oy+2,ox+13,oy+15), fill=(105,76,55,255)); d.rectangle((ox+5,oy+4,ox+11,oy+6), fill=(189,151,92,255)); d.rectangle((ox+5,oy+9,ox+11,oy+11), fill=(127,150,142,255))
    elif idx in (29,30,31):
        d.rectangle((ox+5,oy+1,ox+11,oy+15), fill=(112,103,100,255)); d.rectangle((ox+3,oy+12,ox+13,oy+15), fill=(78,72,73,255))
    elif idx in (32,33,34):
        d.rectangle((ox+3,oy+10,ox+13,oy+14), fill=(92,72,56,255)); d.rectangle((ox+5,oy+6,ox+12,oy+9), fill=(209,190,148,255)); d.rectangle((ox+7,oy+3,ox+13,oy+5), fill=(115,149,164,255))
    elif idx in (35,36):
        d.rectangle((ox+5,oy+9,ox+11,oy+15), fill=(96,87,82,255)); d.polygon([(ox+8,oy+1),(ox+13,oy+8),(ox+8,oy+12),(ox+3,oy+8)], fill=(107,165,181,255))
    else:
        d.rectangle((ox+3,oy+11,ox+13,oy+14), fill=(100,80,62,255)); d.rectangle((ox+5,oy+7,ox+11,oy+10), fill=(219,199,156,255))
tiles.save(assets / 'region2_forgotten_archive_tiles.png')

# ---------------------------------------------------------------------------
# TMX: 40x28, organic broken-archive path, physical decor in map layers only.
W,H=40,28
base=[381]*(W*H)
# Irregular pale-stone route from south dock to north archive seal.
for y in range(4,26):
    shift = -1 if 7 <= y <= 10 else (1 if 15 <= y <= 18 else 0)
    center=20+shift
    width = 2 if y%5 else 3
    for x in range(center-width, center+width+1):
        if 1 <= x < W-1:
            base[y*W+x]=457
# Side reading courts / ruined archive chambers.
for cx,cy,rx,ry in [(9,9,5,3),(31,9,5,3),(10,18,5,3),(30,18,5,3)]:
    for y in range(cy-ry,cy+ry+1):
        for x in range(cx-rx,cx+rx+1):
            if 1<x<W-2 and 1<y<H-2 and ((x-cx)**2/(rx*rx)+(y-cy)**2/(ry*ry) <= 1.15):
                base[y*W+x]=382 if (x+y)%3 else 457

build=[0]*(W*H); front=[0]*(W*H); ground=[0]*(W*H)
# Outer collision border, leave south boarding gap.
for x in range(W):
    if not (18 <= x <= 22): build[x]=381
    if not (18 <= x <= 22): build[(H-1)*W+x]=381
for y in range(H):
    build[y*W]=381; build[y*W+W-1]=381
CUSTOM=2001
# Subtle ground identity. Keep center combat lane readable.
marks=[(7,7,1),(11,10,3),(29,7,2),(33,11,5),(7,17,6),(12,20,0),(28,17,3),(33,20,2),(16,12,1),(24,13,7),(18,21,4),(23,22,5),(14,6,2),(26,6,1)]
for x,y,t in marks: ground[y*W+x]=CUSTOM+t
# Archive shelves/columns as physical Buildings layer, all away from main corridor.
props=[(5,6,25),(8,6,26),(32,6,25),(35,6,26),(5,15,27),(8,16,28),(32,15,27),(35,16,28),
       (13,8,29),(27,8,30),(14,19,31),(26,19,29),(6,11,32),(34,11,33),(7,21,34),(33,21,32),
       (12,14,35),(28,14,36)]
for x,y,t in props:
    build[y*W+x]=CUSTOM+t
# A few upper shelf caps in Front, aligned to blocked bases below.
for x,y,t in [(5,5,25),(8,5,26),(32,5,25),(35,5,26),(5,14,27),(8,15,28),(32,14,27),(35,15,28)]:
    front[y*W+x]=CUSTOM+t
# North 3x3 Archive Seal: lower row/side columns block, upper arch in Front.
for r in range(3):
    for c in range(3):
        gid=CUSTOM+16+r*3+c
        x=19+c; y=2+r
        if r==0:
            front[y*W+x]=gid
        elif r==1 and c==1:
            front[y*W+x]=gid
            build[y*W+x]=gid
        else:
            build[y*W+x]=gid
# More floor runes around the seal, not collision.
for x,y,t in [(17,5,5),(18,5,2),(22,5,2),(23,5,5),(16,6,3),(24,6,3)]: ground[y*W+x]=CUSTOM+t


def csv(vals):
    return ',\n'.join(','.join(str(vals[y*W+x]) for x in range(W)) for y in range(H))

tmx=f'''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" renderorder="right-down" width="{W}" height="{H}" tilewidth="16" tileheight="16" infinite="0" nextlayerid="5" nextobjectid="1">
 <properties>
  <property name="Outdoors" value="T"/>
  <property name="CardchaRegionVersion" value="{V}"/>
  <property name="CardchaRegionRole" value="region2|forgotten-archive|21-40-cards|boss2-hollow-curator"/>
  <property name="CardchaAssetPolicy" value="cardcha-owned-map|map-layer-physical-depth|native-size-enemies|no-post-world-physical-overlays"/>
 </properties>
 <tileset firstgid="1" name="spring_outdoorsTileSheet" tilewidth="16" tileheight="16" tilecount="1975" columns="25">
  <image source=".spring_outdoorsTileSheet.png" width="400" height="1264"/>
 </tileset>
 <tileset firstgid="{CUSTOM}" name="cardcha_region2_archive" tilewidth="16" tileheight="16" tilecount="64" columns="16">
  <image source="region2_forgotten_archive_tiles.png" width="256" height="64"/>
 </tileset>
 <layer id="1" name="Back" width="{W}" height="{H}"><data encoding="csv">{csv(base)}</data></layer>
 <layer id="2" name="CardchaGround" width="{W}" height="{H}"><data encoding="csv">{csv(ground)}</data></layer>
 <layer id="3" name="Buildings" width="{W}" height="{H}"><data encoding="csv">{csv(build)}</data></layer>
 <layer id="4" name="Front" width="{W}" height="{H}"><data encoding="csv">{csv(front)}</data></layer>
</map>'''
(assets / 'region2_forgotten_archive.tmx').write_text(tmx, encoding='utf-8')

# ---------------------------------------------------------------------------
# Handoff.
handoff = ROOT / 'handoff' / 'ALPHA28_0679_REGION2_21_40_FOUNDATION.md'
handoff.write_text(f'''# Cardcha Alpha 28 - 0679 Region II 21-40 Foundation

Branch: `cardcha-alpha28-0679-region2-21-40-foundation`  
Build: `{V}`

## Corrected progression architecture

Boss II/III/IV are the bosses of Region II/III/IV respectively. They are not one shared gameplay destination.
0679 implements the missing Region II progression band:

- Boss I real clear unlocks Region II.
- 21-39 cards: Airship route console offers Region II • Forgotten Archive as the active progression biome.
- Region II has 3 combat waves and extraction.
- Region II fare uses the existing 250g fare constant.
- At 40 cards, the Airship lands in Region II Boss Approach instead of teleporting directly to Hollow Curator.
- The physical north Archive Seal is the Boss II entrance.
- Boss II arena remains a separate arena location, but it is entered from Region II, so Hollow Curator is now the Region II boss.

## Region II identity

Forgotten Archive is an outdoor fantasy archive ruin: parchment, ink, mirror fragments, broken shelves, archive stone and a north seal.
All physical terrain/decor is authored into TMX layers. No Region II physical prop is painted from RenderedWorld.

Enemies use vanilla Monster proxies only for AI/hitbox/combat; authored 32px Cardcha sprites are injected at Monster.draw:
- Ink Moth
- Paper Scarab
- Dust Slime
- Archive Warden (wave 3 elite)

## Rewards

Region II full clear: 34 Scrap + 1 Shiny (7/11/16 Scrap; Shiny only on wave 3).
Region III and IV reward contracts remain unchanged.

## Test

1. `cardcha_test_region2` - normal Region II 3-wave run regardless of real unlocks.
2. `cardcha_expedition_clear` - clear current wave quickly.
3. Verify south extraction banks 34 Scrap + 1 Shiny on full clear.
4. `cardcha_test_region2_bossgate` - Region II Boss Approach test.
5. Walk north to the Archive Seal and interact. In real progression it requires Boss I clear + 40 cards. Debug approach bypasses only the Region II entry, not persistent save progression.
6. `cardcha_test_boss2` remains available for direct boss visual testing.

## Frozen contracts

Save schema 19; 80 source / 76 normal cards; Boss II 2200 HP; Region III/IV gameplay/rewards; Boss III/IV milestone logic; MiMi locked art; Airship visual/decor; rendering-depth repository contract.

In-game screenshot acceptance remains pending.
''', encoding='utf-8')
latest = ROOT / 'handoff' / 'LATEST_CARDCHA_HANDOFF.md'
latest.write_text(f'''# Latest Cardcha Handoff

Current branch: `cardcha-alpha28-0679-region2-21-40-foundation`
Current build: `{V}`
Continue from: `handoff/ALPHA28_0679_REGION2_21_40_FOUNDATION.md`

0679 establishes Region II as the 21-40 card progression biome and routes the 40-card Hollow Curator milestone through its physical north Archive Seal. In-game visual/gameplay acceptance is pending.
''', encoding='utf-8')

print('0679 generator complete')
