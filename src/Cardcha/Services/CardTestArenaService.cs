using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Monsters;

namespace Cardcha.Services;

/// <summary>
/// TEST-only isolated combat room for repeatable card verification.
/// Time is frozen, one marked slime respawns forever, outgoing raw weapon hits are normalized,
/// incoming dummy contact damage is normalized, and lethal player damage is rescued in-place.
/// The arena never writes its temporary state to SaveData.
/// </summary>
internal sealed class CardTestArenaService
{
    public const string LocationName = "Cardcha_CardTestArena";
    public const string MapAssetName = "Maps/Cardcha_CardTestArena";
    public const string TestMonsterMarkerKey = "Ronvotri.Cardcha/CardTestArenaDummy";

    private const string MapPath = "assets/card_test_arena.tmx";
    private const int FixedOutgoingRawDamage = 100;
    private const int FixedIncomingRawDamage = 10;
    private const int DummyMaxHealth = 500;
    private const long RespawnDelayMs = 450L;
    private static readonly Point PlayerArrivalTile = new(4, 6);
    private static readonly Point DummySpawnTile = new(11, 6);

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly CardTestLabService Lab;

    private bool CreationFailed;
    private bool LoggedCreation;
    private long RespawnAtMs;
    private string ReturnLocationName = "";
    private Point ReturnTile;
    private int ReturnFacing = 2;
    private int FrozenTimeOfDay;
    private int FrozenGameTimeInterval;
    private bool ArenaEntered;

    public CardTestArenaService(IModHelper helper, IMonitor monitor, CardTestLabService lab)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Lab = lab;
    }

    public bool IsInArena
        => Context.IsWorldReady
           && Game1.currentLocation?.NameOrUniqueName.Equals(LocationName, StringComparison.OrdinalIgnoreCase) == true;

    public int FixedOutgoingDamage => FixedOutgoingRawDamage;
    public int FixedIncomingDamage => FixedIncomingRawDamage;

    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)
    {
        if (e.NameWithoutLocale.IsEquivalentTo(MapAssetName))
            e.LoadFromModFile<xTile.Map>(MapPath, AssetLoadPriority.Exclusive);
    }

    public void OnSaveLoaded(object? sender, SaveLoadedEventArgs e)
    {
        this.ResetRuntime();
        this.EnsureLocation();
    }

    public void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e)
    {
        this.ResetRuntime();
        this.LoggedCreation = false;
    }

    public void OnWarped(object? sender, WarpedEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        if (e.NewLocation.NameOrUniqueName.Equals(LocationName, StringComparison.OrdinalIgnoreCase))
        {
            this.ArenaEntered = true;
            this.EnsureDummy(forceRespawn: true);
            return;
        }

        if (e.OldLocation?.NameOrUniqueName.Equals(LocationName, StringComparison.OrdinalIgnoreCase) == true)
            this.RestoreClock();
    }

    public void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
    {
        if (!this.IsInArena)
            return;

        // Freeze the Stardew clock and keep the test player supplied. This is intentionally arena-only.
        Game1.timeOfDay = this.FrozenTimeOfDay;
        Game1.gameTimeInterval = 0;
        if (Game1.player is not null)
            Game1.player.Stamina = Game1.player.MaxStamina;

        this.EnsureDummy(forceRespawn: false);
    }

    public bool EnterArena()
    {
        if (!Context.IsWorldReady || Game1.player is null)
            return false;

        this.Lab.BeginSession();
        GameLocation? arena = this.EnsureLocation();
        if (arena is null)
            return false;

        if (!this.IsInArena)
        {
            this.ReturnLocationName = Game1.currentLocation?.NameOrUniqueName ?? "Farm";
            this.ReturnTile = new Point(
                (int)(Game1.player.Position.X / 64f),
                (int)(Game1.player.Position.Y / 64f)
            );
            this.ReturnFacing = Game1.player.FacingDirection;
            this.FrozenTimeOfDay = Game1.timeOfDay;
            this.FrozenGameTimeInterval = Game1.gameTimeInterval;
        }

        this.ArenaEntered = true;
        this.RespawnAtMs = 0;
        Game1.warpFarmer(LocationName, PlayerArrivalTile.X, PlayerArrivalTile.Y, 1);
        this.EnsureDummy(forceRespawn: true);
        Game1.showGlobalMessage("Card Test Arena: TIME FROZEN • raw hit 100 • dummy hit 10");
        return true;
    }

    public void ExitArena()
    {
        if (!Context.IsWorldReady)
            return;

        this.RemoveDummy();
        this.RestoreClock();

        if (this.IsInArena)
        {
            string targetName = string.IsNullOrWhiteSpace(this.ReturnLocationName) ? "Farm" : this.ReturnLocationName;
            GameLocation? target = Game1.getLocationFromName(targetName) ?? Game1.getFarm();
            if (target is not null)
            {
                Point targetTile = this.ReturnTile == Point.Zero ? new Point(8, 8) : this.ReturnTile;
                Game1.warpFarmer(target.NameOrUniqueName, targetTile.X, targetTile.Y, this.ReturnFacing);
            }
        }

        this.ArenaEntered = false;
        this.RespawnAtMs = 0;
    }

    public void PrepareForSave()
    {
        if (!this.ArenaEntered && !this.IsInArena)
            return;

        this.ExitArena();
    }

    public bool TryOverrideOutgoingDamage(Monster monster, ref int damage, bool isBomb, Farmer? who)
    {
        if (!this.IsInArena
            || isBomb
            || damage <= 0
            || who is null
            || !monster.modData.ContainsKey(TestMonsterMarkerKey))
        {
            return false;
        }

        // Steady Grip specifically tests vanilla hit variance, so preserve the raw Stardew hit for that card.
        if (this.Lab.ActiveCardId.Equals("steady_grip", StringComparison.OrdinalIgnoreCase))
            return false;

        damage = FixedOutgoingRawDamage;
        return true;
    }

    public bool TryOverrideIncomingDamage(ref int damage, Monster? damager)
    {
        if (!this.IsInArena
            || damage <= 0
            || damager is null
            || !damager.modData.ContainsKey(TestMonsterMarkerKey))
        {
            return false;
        }

        damage = FixedIncomingRawDamage;
        return true;
    }

    public void AfterFarmerDamage(Farmer farmer)
    {
        if (!this.IsInArena || farmer.health > 0)
            return;

        // Cardcha revive cards resolve first in CombatService. If none rescued the hit, the arena does.
        farmer.health = farmer.maxHealth;
        farmer.Stamina = farmer.MaxStamina;
        Game1.playSound("yoba");
        Game1.showGlobalMessage("TEST ARENA REVIVE • no money/items/time lost");
    }

    public void ResetDummy(double healthPercent = 1.0)
    {
        if (!this.IsInArena)
            return;

        Monster? dummy = this.GetDummy();
        if (dummy is null)
        {
            this.EnsureDummy(forceRespawn: true);
            dummy = this.GetDummy();
        }

        if (dummy is null)
            return;

        dummy.Position = new Vector2(DummySpawnTile.X * 64f, DummySpawnTile.Y * 64f);
        dummy.Health = Math.Clamp(
            (int)Math.Round(dummy.MaxHealth * Math.Clamp(healthPercent, 0.01, 1.0)),
            1,
            dummy.MaxHealth
        );
        this.RespawnAtMs = 0;
    }

    public string Describe()
    {
        Monster? dummy = this.GetDummy();
        string dummyStatus = dummy is null
            ? "respawning"
            : $"HP {Math.Max(0, dummy.Health)}/{Math.Max(1, dummy.MaxHealth)}";
        return $"Arena={(this.IsInArena ? "ACTIVE" : "off")} | Time={(this.IsInArena ? "FROZEN" : "normal")} | Dummy={dummyStatus} | RawOutgoing={FixedOutgoingRawDamage} | RawIncoming={FixedIncomingRawDamage}";
    }

    public void DrawHud(SpriteBatch b)
    {
        if (!this.IsInArena)
            return;

        Monster? dummy = this.GetDummy();
        string hp = dummy is null ? "RESPAWNING..." : $"{Math.Max(0, dummy.Health)}/{Math.Max(1, dummy.MaxHealth)} HP";
        string line = $"CARD TEST ARENA   TIME FROZEN   DUMMY {hp}   RAW HIT 100   RAW HIT TO YOU 10";
        Vector2 size = Game1.smallFont.MeasureString(line);
        float scale = Math.Min(0.9f, (Game1.uiViewport.Width - 40f) / Math.Max(1f, size.X));
        Rectangle bg = new(16, Game1.uiViewport.Height - 58, Math.Min(Game1.uiViewport.Width - 32, (int)(size.X * scale) + 28), 42);
        b.Draw(Game1.staminaRect, bg, Color.Black * 0.78f);
        b.DrawString(Game1.smallFont, line, new Vector2(bg.X + 14, bg.Y + 9), Color.White, 0f, Vector2.Zero, scale, SpriteEffects.None, 1f);
    }

    private GameLocation? EnsureLocation()
    {
        if (!Context.IsWorldReady || this.CreationFailed)
            return null;

        GameLocation? existing = Game1.getLocationFromName(LocationName);
        if (existing is not null)
            return existing;

        try
        {
            GameLocation arena = new(MapAssetName, LocationName);
            Game1.locations.Add(arena);
            if (!this.LoggedCreation)
            {
                this.LoggedCreation = true;
                this.Monitor.Log("Created Cardcha_CardTestArena test-only frozen combat room.", LogLevel.Info);
            }
            return arena;
        }
        catch (Exception ex)
        {
            this.CreationFailed = true;
            this.Monitor.Log($"Couldn't create Card Test Arena: {ex.GetType().Name}: {ex.Message}", LogLevel.Error);
            return null;
        }
    }

    private void EnsureDummy(bool forceRespawn)
    {
        if (!this.IsInArena)
            return;

        GameLocation? arena = Game1.currentLocation;
        if (arena is null)
            return;

        Monster? existing = this.GetDummy();
        if (existing is not null && existing.Health > 0 && !forceRespawn)
            return;

        if (existing is not null)
            arena.characters.Remove(existing);

        long now = Environment.TickCount64;
        if (!forceRespawn)
        {
            if (this.RespawnAtMs <= 0)
            {
                this.RespawnAtMs = now + RespawnDelayMs;
                return;
            }
            if (now < this.RespawnAtMs)
                return;
        }

        GreenSlime dummy = new(new Vector2(DummySpawnTile.X * 64f, DummySpawnTile.Y * 64f), 0)
        {
            MaxHealth = DummyMaxHealth,
            Health = DummyMaxHealth,
            Speed = 0
        };
        dummy.modData[TestMonsterMarkerKey] = "1";
        arena.characters.Add(dummy);
        this.RespawnAtMs = 0;
    }

    private Monster? GetDummy()
        => Game1.currentLocation?.characters
            .OfType<Monster>()
            .FirstOrDefault(monster => monster.modData.ContainsKey(TestMonsterMarkerKey));

    private void RemoveDummy()
    {
        GameLocation? arena = Game1.getLocationFromName(LocationName);
        if (arena is null)
            return;

        foreach (NPC actor in arena.characters.Where(actor => actor.modData.ContainsKey(TestMonsterMarkerKey)).ToList())
            arena.characters.Remove(actor);
    }

    private void RestoreClock()
    {
        if (!this.ArenaEntered)
            return;

        if (this.FrozenTimeOfDay > 0)
            Game1.timeOfDay = this.FrozenTimeOfDay;
        Game1.gameTimeInterval = Math.Max(0, this.FrozenGameTimeInterval);
    }

    private void ResetRuntime()
    {
        this.RemoveDummy();
        this.CreationFailed = false;
        this.RespawnAtMs = 0;
        this.ReturnLocationName = "";
        this.ReturnTile = Point.Zero;
        this.ReturnFacing = 2;
        this.FrozenTimeOfDay = 0;
        this.FrozenGameTimeInterval = 0;
        this.ArenaEntered = false;
    }
}
