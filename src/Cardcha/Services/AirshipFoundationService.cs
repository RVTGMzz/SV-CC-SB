using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Monsters;

namespace Cardcha.Services;

/// <summary>
/// Alpha.28 Airship foundation with the conflict-safe Sky Dock entrance.
///
/// Compatibility contract:
/// - The Dock is anchored dynamically from Forest's existing Farm warp instead of hard-coded
///   vanilla coordinates, so custom farm layouts don't move the access point into nonsense.
/// - It does NOT replace Forest map tiles, add objects, change collision, or reserve NPC paths.
/// - The visible dock is a lightweight Cardcha overlay only; base-game NPC movement/gameplay
///   remains authoritative. At worst a map overhaul may make the cosmetic marker less ideal,
///   but it should not break the Forest or block an NPC.
/// </summary>
internal sealed class AirshipFoundationService
{
    public const string DeckLocationName = "Cardcha_AirshipDeck";
    public const string DeckMapAssetName = "Maps/Cardcha_AirshipDeck";
    public const string SkyDockLocationName = "Forest";
    public const string SkyDockInteriorLocationName = "Cardcha_SkyDockInterior";
    public const string SkyDockInteriorMapAssetName = "Maps/Cardcha_SkyDockInterior";
    public const string Region1LocationName = "Cardcha_Region1";
    public const string Region1MapAssetName = "Maps/Cardcha_Region1";

    private const string DeckMapPath = "assets/airship_deck.tmx";
    private const string SkyDockInteriorMapPath = "assets/sky_dock_interior.tmx";
    private const string Region1MapPath = "assets/region1_hunting.tmx";
    private const string AirshipVisualPath = "assets/airship_visual.png";
    private const string Region1MonsterMarkerKey = "Ronvotri.Cardcha/Region1Spawn";
    private const int Region1GateCardRequirement = 20;
    private const int Region1Fare = 100;
    private const int Region2Fare = 250;
    private const int Region3Fare = 500;
    private const int Region4Fare = 1000;
    private const long DepartureConfirmWindowMs = 5000L;
    private const long FlightCutsceneDurationMs = 3200L;
    private const long FlightWarpAtMs = 1650L;
    private const long FlybyDurationMs = 4600L;
    private const long FlybyArmDelayMs = 2200L;
    private const float BoardingUseDistance = 128f;
    private const float FlybyTiltRadians = 0.028f;
    private const float CutsceneTiltRadians = 0.045f;
    private const float CutsceneScalePulse = 0.018f;

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;

    private bool FlybyActive;
    private long FlybyStartedAtMs;
    private long FlybyArmAfterMs;
    private bool DeckCreationFailed;
    private bool LoggedDeckFailure;
    private bool LoggedDeckCreation;
    private bool SkyDockInteriorCreationFailed;
    private bool LoggedSkyDockInteriorFailure;
    private bool LoggedSkyDockInteriorCreation;
    private bool Region1CreationFailed;
    private bool LoggedRegion1Failure;
    private bool LoggedRegion1Creation;
    private long PendingDepartureUntilMs;
    private bool FlightCutsceneActive;
    private bool FlightCutsceneReturning;
    private bool FlightCutsceneWarped;
    private long FlightCutsceneStartedAtMs;
    private Point? CachedSkyDockTile;
    private Point? CachedForestFarmWarpTile;
    private long WarpGraceUntilMs;
    private Texture2D? AirshipVisual;
    private bool AirshipVisualLoadFailed;
    private bool LoggedAirshipVisualFailure;

    public AirshipFoundationService(IModHelper helper, IMonitor monitor, SaveService save)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
    }

    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)
    {
        if (e.NameWithoutLocale.IsEquivalentTo(DeckMapAssetName))
        {
            e.LoadFromModFile<xTile.Map>(DeckMapPath, AssetLoadPriority.Exclusive);
            return;
        }

        if (e.NameWithoutLocale.IsEquivalentTo(SkyDockInteriorMapAssetName))
        {
            e.LoadFromModFile<xTile.Map>(SkyDockInteriorMapPath, AssetLoadPriority.Exclusive);
            return;
        }

        if (e.NameWithoutLocale.IsEquivalentTo(Region1MapAssetName))
            e.LoadFromModFile<xTile.Map>(Region1MapPath, AssetLoadPriority.Exclusive);
    }

    public void OnSaveLoaded()
    {
        this.ResetRuntime();
        this.EnsureDeckLocation();
        this.EnsureSkyDockInteriorLocation();
        this.EnsureRegion1Location();
        this.MigrateUnlockFromExistingStory();
        this.FlybyArmAfterMs = Environment.TickCount64 + FlybyArmDelayMs;
    }

    public void OnDayStarted()
    {
        this.FlybyActive = false;
        this.FlybyStartedAtMs = 0;
        this.CachedSkyDockTile = null;
        this.CachedForestFarmWarpTile = null;
        this.DeckCreationFailed = false;
        this.LoggedDeckFailure = false;
        this.SkyDockInteriorCreationFailed = false;
        this.LoggedSkyDockInteriorFailure = false;
        this.Region1CreationFailed = false;
        this.LoggedRegion1Failure = false;
        this.EnsureDeckLocation();
        this.EnsureSkyDockInteriorLocation();
        this.EnsureRegion1Location();
        this.MigrateUnlockFromExistingStory();
        this.FlybyArmAfterMs = Environment.TickCount64 + 1500L;
    }

    public void OnReturnedToTitle()
    {
        this.ResetRuntime();
        this.LoggedDeckCreation = false;
        this.LoggedSkyDockInteriorCreation = false;
        this.LoggedRegion1Creation = false;
    }

    public void OnUpdateTicked(UpdateTickedEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        long now = Environment.TickCount64;

        if (this.FlightCutsceneActive)
        {
            Game1.player.Halt();
            this.UpdateFlightCutscene(now);
            return;
        }

        if (this.PendingDepartureUntilMs > 0 && now > this.PendingDepartureUntilMs)
            this.PendingDepartureUntilMs = 0;

        if (this.FlybyActive)
        {
            if (now - this.FlybyStartedAtMs >= FlybyDurationMs)
            {
                this.FlybyActive = false;
                this.FlybyStartedAtMs = 0;
            }
            return;
        }

        if (!this.Save.Data.AirshipFlybySeen
            && !this.Save.Data.FirstScrapTriggered
            && now >= this.FlybyArmAfterMs
            && Game1.currentLocation == Game1.getFarm()
            && Game1.timeOfDay >= 700
            && Game1.timeOfDay < 1900
            && Game1.activeClickableMenu is null
            && !Game1.dialogueUp
            && !Game1.eventUp)
        {
            this.StartFlyby(persistSeen: true);
        }
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        if (this.FlybyActive && Game1.currentLocation == Game1.getFarm())
            this.DrawFlyby(e.SpriteBatch);

        GameLocation? location = Game1.currentLocation;
        if (this.Save.Data.AirshipUnlocked && IsSkyDockLocation(location))
            this.DrawSkyDock(e.SpriteBatch, this.ResolveSkyDockTile());

        if (location?.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase) == true)
            this.DrawSkyDockInteriorDetails(e.SpriteBatch, location);

        if (location?.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase) == true)
            this.DrawDeckMarkers(e.SpriteBatch, location);

        if (location?.NameOrUniqueName.Equals(Region1LocationName, StringComparison.OrdinalIgnoreCase) == true)
            this.DrawRegion1Details(e.SpriteBatch, location);

        if (this.FlightCutsceneActive)
            this.DrawFlightCutscene(e.SpriteBatch);
    }

    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady
            || !e.Button.IsActionButton()
            || Game1.activeClickableMenu is not null
            || Game1.dialogueUp
            || Game1.eventUp
            || this.FlightCutsceneActive
            || Environment.TickCount64 < this.WarpGraceUntilMs)
        {
            return;
        }

        GameLocation? location = Game1.currentLocation;
        if (location is null)
            return;

        // Sky Dock is the normal gameplay entrance. It never edits Forest collision/pathing.
        if (IsSkyDockLocation(location) && this.Save.Data.AirshipUnlocked)
        {
            Point dock = this.ResolveSkyDockTile();
            if (!PlayerIsNear(dock))
                return;

            GameLocation? interior = this.EnsureSkyDockInteriorLocation();
            if (interior is null)
            {
                this.Helper.Input.Suppress(e.Button);
                Game1.drawObjectDialogue(ModEntry.T("airship.skydock.interior.unavailable"));
                return;
            }

            this.Helper.Input.Suppress(e.Button);
            Point arrival = ResolveSkyDockInteriorArrivalTile(interior);
            this.WarpGraceUntilMs = Environment.TickCount64 + 850L;
            Game1.warpFarmer(SkyDockInteriorLocationName, arrival.X, arrival.Y, 0);
            return;
        }

        if (location.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase))
        {
            Point interiorAction = GetActionTile();
            Point route = ResolveSkyDockInteriorRouteTile(location);
            Point bay = ResolveSkyDockInteriorBayTile(location);
            Point interiorExit = ResolveSkyDockInteriorExitTile(location);

            if (Touches(interiorAction, route)
                || PlayerIsNear(route)
                || Touches(interiorAction, bay)
                || PlayerIsNear(bay))
            {
                this.Helper.Input.Suppress(e.Button);
                this.HandleRegion1DepartureRequest();
                return;
            }

            if (Touches(interiorAction, interiorExit) || PlayerIsNear(interiorExit))
            {
                this.Helper.Input.Suppress(e.Button);
                this.ReturnToSkyDockExterior();
            }
            return;
        }

        if (location.NameOrUniqueName.Equals(Region1LocationName, StringComparison.OrdinalIgnoreCase))
        {
            this.HandleRegion1Interaction(e, location);
            return;
        }

        if (!location.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))
            return;

        Point action = GetActionTile();
        Point helm = ResolveDeckHelmTile(location);
        Point exit = ResolveDeckExitTile(location);

        if (Touches(action, helm))
        {
            this.Helper.Input.Suppress(e.Button);
            int owned = this.Save.Data.OwnedCards?.Count ?? 0;
            Game1.drawObjectDialogue(
                this.Save.Data.AirshipHighestRegionUnlocked >= 1
                    ? ModEntry.T("airship.route.region1.foundation", new { cards = owned })
                    : ModEntry.T("airship.route.locked")
            );
            return;
        }

        if (!Touches(action, exit) && !PlayerIsNear(exit))
            return;

        this.Helper.Input.Suppress(e.Button);
        this.StartFlightCutscene(returning: true);
    }

    public void OnWarped(object? sender, WarpedEventArgs e)
    {
        if (!Context.IsWorldReady
            || !Context.IsMainPlayer
            || !e.NewLocation.NameOrUniqueName.Equals(Region1LocationName, StringComparison.OrdinalIgnoreCase)
            || e.OldLocation?.NameOrUniqueName.Equals(Region1LocationName, StringComparison.OrdinalIgnoreCase) == true)
        {
            return;
        }

        this.PopulateRegion1(e.NewLocation);
    }

    /// <summary>TEST-only direct deck access; does not unlock the Airship or alter story flags.</summary>
    public string DebugToggleDeck()
    {
        if (!Context.IsWorldReady)
            return "Airship TEST unavailable: load a save first.";

        if (Game1.currentLocation?.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase) == true)
        {
            this.WarpToSkyDockInterior();
            return "Airship TEST: returned to Sky Dock interior. Story/unlock/fare state was not changed.";
        }

        GameLocation? deck = this.EnsureDeckLocation();
        if (deck is null)
            return "Airship TEST couldn't create Cardcha_AirshipDeck.";

        Point arrival = ResolveDeckArrivalTile(deck);
        this.WarpGraceUntilMs = Environment.TickCount64 + 850L;
        Game1.warpFarmer(DeckLocationName, arrival.X, arrival.Y, 0);
        return "Airship TEST: warped to Cardcha_AirshipDeck. Run cardcha_test_airship again to return to Sky Dock interior. Story/unlock/fare state was not changed.";
    }

    /// <summary>TEST-only replay of the distant Farm flyby without changing the persisted seen flag.</summary>
    public string DebugReplayFlyby()
    {
        if (!Context.IsWorldReady)
            return "Airship flyby TEST unavailable: load a save first.";

        if (Game1.currentLocation != Game1.getFarm())
            return "Airship flyby TEST: go to the Farm first.";

        this.StartFlyby(persistSeen: false);
        return "Airship flyby TEST started. The persisted flyby/story state was not changed.";
    }

    public string Describe()
    {
        if (!Context.IsWorldReady)
            return "Airship=<no save>";

        Point dock = this.ResolveSkyDockTile();
        Point farmWarp = this.ResolveForestFarmWarpTile();
        bool deckExists = Game1.getLocationFromName(DeckLocationName) is not null;
        bool interiorExists = Game1.getLocationFromName(SkyDockInteriorLocationName) is not null;
        bool region1Exists = Game1.getLocationFromName(Region1LocationName) is not null;
        return $"AirshipFlybySeen={this.Save.Data.AirshipFlybySeen} | " +
               $"FlybyActive={this.FlybyActive} | " +
               $"Unlocked={this.Save.Data.AirshipUnlocked} | " +
               $"HighestRegion={this.Save.Data.AirshipHighestRegionUnlocked} | " +
               $"UnlockDay={this.Save.Data.AirshipUnlockedDay} | " +
               $"DeckExists={deckExists} | InteriorExists={interiorExists} | Region1Exists={region1Exists} | Flights={this.Save.Data.AirshipFlightsTaken} | FarePaid={this.Save.Data.AirshipTotalFarePaid}g | SkyDock={SkyDockLocationName}({dock.X},{dock.Y}) | " +
               $"ForestFarmWarp={farmWarp.X},{farmWarp.Y} | CollisionEdits=NONE";
    }

    private void MigrateUnlockFromExistingStory()
    {
        if (!Context.IsWorldReady || !this.Save.Data.MimiMeetupCompleted)
            return;

        bool changed = false;
        if (!this.Save.Data.AirshipUnlocked)
        {
            this.Save.Data.AirshipUnlocked = true;
            changed = true;
        }

        if (this.Save.Data.AirshipHighestRegionUnlocked < 1)
        {
            this.Save.Data.AirshipHighestRegionUnlocked = 1;
            changed = true;
        }

        if (this.Save.Data.AirshipUnlockedDay < 0)
        {
            this.Save.Data.AirshipUnlockedDay = Game1.Date.TotalDays;
            changed = true;
        }

        if (!changed)
            return;

        this.Save.Save();
        this.Monitor.Log(
            "Alpha.28 Airship migration: existing completed MiMi/Wizard handoff now owns Region I access through Sky Dock.",
            LogLevel.Info
        );
    }

    private void StartFlyby(bool persistSeen)
    {
        this.FlybyActive = true;
        this.FlybyStartedAtMs = Environment.TickCount64;

        if (persistSeen && !this.Save.Data.AirshipFlybySeen)
        {
            this.Save.Data.AirshipFlybySeen = true;
            this.Save.Save();
        }

        Game1.playSound("wand");
        this.Monitor.Log(
            persistSeen
                ? "Alpha.28 pre-MiMi Airship flyby played and was persisted as seen."
                : "Alpha.28 TEST replay of the pre-MiMi Airship flyby started.",
            LogLevel.Trace
        );
    }

    private GameLocation? EnsureDeckLocation()
    {
        if (!Context.IsWorldReady || this.DeckCreationFailed)
            return null;

        GameLocation? existing = Game1.getLocationFromName(DeckLocationName);
        if (existing is not null)
            return existing;

        try
        {
            GameLocation deck = new(DeckMapAssetName, DeckLocationName);
            Game1.locations.Add(deck);
            if (!this.LoggedDeckCreation)
            {
                this.LoggedDeckCreation = true;
                this.Monitor.Log(
                    "Created Cardcha_AirshipDeck from Cardcha-owned alpha.28 foundation map.",
                    LogLevel.Info
                );
            }
            return deck;
        }
        catch (Exception ex)
        {
            this.DeckCreationFailed = true;
            if (!this.LoggedDeckFailure)
            {
                this.LoggedDeckFailure = true;
                this.Monitor.Log(
                    $"Couldn't create Cardcha Airship deck; retries suppressed until next save/day. {ex.GetType().Name}: {ex.Message}",
                    LogLevel.Error
                );
            }
            return null;
        }
    }

    private GameLocation? EnsureSkyDockInteriorLocation()
    {
        if (!Context.IsWorldReady || this.SkyDockInteriorCreationFailed)
            return null;

        GameLocation? existing = Game1.getLocationFromName(SkyDockInteriorLocationName);
        if (existing is not null)
            return existing;

        try
        {
            GameLocation interior = new(SkyDockInteriorMapAssetName, SkyDockInteriorLocationName);
            Game1.locations.Add(interior);
            if (!this.LoggedSkyDockInteriorCreation)
            {
                this.LoggedSkyDockInteriorCreation = true;
                this.Monitor.Log("Created Cardcha_SkyDockInterior from Cardcha-owned vanilla-tile layout.", LogLevel.Info);
            }
            return interior;
        }
        catch (Exception ex)
        {
            this.SkyDockInteriorCreationFailed = true;
            if (!this.LoggedSkyDockInteriorFailure)
            {
                this.LoggedSkyDockInteriorFailure = true;
                this.Monitor.Log($"Couldn't create Sky Dock interior; retries suppressed until next save/day. {ex.GetType().Name}: {ex.Message}", LogLevel.Error);
            }
            return null;
        }
    }

    private GameLocation? EnsureRegion1Location()
    {
        if (!Context.IsWorldReady || this.Region1CreationFailed)
            return null;

        GameLocation? existing = Game1.getLocationFromName(Region1LocationName);
        if (existing is not null)
            return existing;

        try
        {
            GameLocation region = new(Region1MapAssetName, Region1LocationName);
            Game1.locations.Add(region);
            if (!this.LoggedRegion1Creation)
            {
                this.LoggedRegion1Creation = true;
                this.Monitor.Log(
                    "Created Cardcha_Region1 hunting grounds with controlled Cardcha monster spawning.",
                    LogLevel.Info
                );
            }
            return region;
        }
        catch (Exception ex)
        {
            this.Region1CreationFailed = true;
            if (!this.LoggedRegion1Failure)
            {
                this.LoggedRegion1Failure = true;
                this.Monitor.Log(
                    $"Couldn't create Region I hunting grounds; retries suppressed until next save/day. {ex.GetType().Name}: {ex.Message}",
                    LogLevel.Error
                );
            }
            return null;
        }
    }

    private void HandleRegion1DepartureRequest()
    {
        if (this.Save.Data.AirshipHighestRegionUnlocked < 1)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.route.locked"));
            return;
        }

        // Validate the target before money is ever consumed.
        if (this.EnsureRegion1Location() is null)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region1.unavailable"));
            return;
        }

        int fare = this.GetRegionFare(1);
        long now = Environment.TickCount64;
        if (this.PendingDepartureUntilMs <= now)
        {
            this.PendingDepartureUntilMs = now + DepartureConfirmWindowMs;
            Game1.drawObjectDialogue(
                fare <= 0
                    ? ModEntry.T("airship.route.region1.first_free")
                    : ModEntry.T("airship.route.region1.confirm", new { fare })
            );
            return;
        }

        this.PendingDepartureUntilMs = 0;
        if (Game1.player.Money < fare)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.route.not_enough", new { fare, money = Game1.player.Money }));
            return;
        }

        if (fare > 0)
            Game1.player.Money -= fare;

        this.Save.Data.AirshipFlightsTaken++;
        this.Save.Data.AirshipTotalFarePaid += fare;
        this.Save.Save();
        this.StartFlightCutscene(returning: false);
    }

    private int GetRegionFare(int region)
    {
        if (this.Save.Data.AirshipFlightsTaken <= 0)
            return 0; // MiMi's first flight is free; persisted so it can't be consumed twice accidentally.

        return region switch
        {
            1 => Region1Fare,
            2 => Region2Fare,
            3 => Region3Fare,
            4 => Region4Fare,
            _ => Region1Fare
        };
    }

    private void StartFlightCutscene(bool returning)
    {
        this.FlightCutsceneActive = true;
        this.FlightCutsceneReturning = returning;
        this.FlightCutsceneWarped = false;
        this.FlightCutsceneStartedAtMs = Environment.TickCount64;
        this.PendingDepartureUntilMs = 0;
        Game1.player.Halt();
        Game1.playSound("wand");
    }

    private void UpdateFlightCutscene(long now)
    {
        long elapsed = now - this.FlightCutsceneStartedAtMs;
        if (!this.FlightCutsceneWarped && elapsed >= FlightWarpAtMs)
        {
            this.FlightCutsceneWarped = true;
            if (this.FlightCutsceneReturning)
            {
                if (!this.WarpToSkyDockInterior())
                    this.ReturnToSkyDockExterior();
            }
            else
            {
                GameLocation? region = this.EnsureRegion1Location();
                if (region is null)
                {
                    // Target was validated before charging; this is a last-resort failure path.
                    this.FlightCutsceneActive = false;
                    this.ReturnToSkyDockExterior();
                    Game1.drawObjectDialogue(ModEntry.T("airship.region1.unavailable"));
                    return;
                }

                Point arrival = ResolveRegion1ArrivalTile(region);
                this.WarpGraceUntilMs = Environment.TickCount64 + 850L;
                Game1.warpFarmer(Region1LocationName, arrival.X, arrival.Y, 0);
            }
        }

        if (elapsed >= FlightCutsceneDurationMs)
        {
            this.FlightCutsceneActive = false;
            this.FlightCutsceneReturning = false;
            this.FlightCutsceneWarped = false;
            this.FlightCutsceneStartedAtMs = 0;
            this.WarpGraceUntilMs = Environment.TickCount64 + 500L;
        }
    }

    private bool WarpToSkyDockInterior()
    {
        GameLocation? interior = this.EnsureSkyDockInteriorLocation();
        if (interior is null)
            return false;

        Point arrival = ResolveSkyDockInteriorArrivalTile(interior);
        this.WarpGraceUntilMs = Environment.TickCount64 + 850L;
        Game1.warpFarmer(SkyDockInteriorLocationName, arrival.X, arrival.Y, 0);
        return true;
    }

    private void ReturnToSkyDockExterior()
    {
        GameLocation? forest = Game1.getLocationFromName(SkyDockLocationName);
        if (forest is null)
        {
            GameLocation? farm = Game1.getFarm();
            if (farm is null)
                return;

            Point fallback = FindClearTileNear(farm, new Point(8, 8));
            this.WarpGraceUntilMs = Environment.TickCount64 + 850L;
            Game1.warpFarmer(farm.NameOrUniqueName, fallback.X, fallback.Y, 2);
            return;
        }

        Point dock = this.ResolveSkyDockTile();
        Point landing = FindClearTileNear(forest, new Point(dock.X + 1, dock.Y + 1));
        this.WarpGraceUntilMs = Environment.TickCount64 + 850L;
        Game1.warpFarmer(forest.NameOrUniqueName, landing.X, landing.Y, 2);
    }

    private void HandleRegion1Interaction(ButtonPressedEventArgs e, GameLocation location)
    {
        Point action = GetActionTile();
        Point gate = ResolveRegion1GateTile(location);
        Point returnPad = ResolveRegion1ReturnTile(location);
        Point bossSigil = ResolveRegion1BossSigilTile(location);
        int playerTileY = (int)(Game1.player.Position.Y / 64f);

        if (Touches(action, returnPad) || PlayerIsNear(returnPad))
        {
            this.Helper.Input.Suppress(e.Button);
            this.StartFlightCutscene(returning: true);
            return;
        }

        if (Touches(action, gate) || PlayerIsNear(gate))
        {
            this.Helper.Input.Suppress(e.Button);

            if (playerTileY < gate.Y)
            {
                Point mainSide = ResolveRegion1MainGateArrivalTile(location);
                this.WarpGraceUntilMs = Environment.TickCount64 + 450L;
                Game1.warpFarmer(Region1LocationName, mainSide.X, mainSide.Y, 2);
                return;
            }

            int owned = this.Save.Data.OwnedCards?.Count ?? 0;
            if (owned < Region1GateCardRequirement)
            {
                Game1.drawObjectDialogue(
                    ModEntry.T(
                        "airship.region1.gate.locked",
                        new { cards = owned, required = Region1GateCardRequirement }
                    )
                );
                return;
            }

            Point staging = ResolveRegion1StagingArrivalTile(location);
            this.WarpGraceUntilMs = Environment.TickCount64 + 450L;
            Game1.playSound("discoverMineral");
            Game1.warpFarmer(Region1LocationName, staging.X, staging.Y, 2);
            Game1.showGlobalMessage(ModEntry.T("airship.region1.gate.open"));
            return;
        }

        if (Touches(action, bossSigil) || PlayerIsNear(bossSigil))
        {
            this.Helper.Input.Suppress(e.Button);
            Game1.drawObjectDialogue(ModEntry.T("airship.region1.boss.staging"));
        }
    }

    private void PopulateRegion1(GameLocation location)
    {
        foreach (NPC actor in location.characters
                     .Where(actor => actor is Monster && actor.modData.ContainsKey(Region1MonsterMarkerKey))
                     .ToList())
        {
            location.characters.Remove(actor);
        }

        Point[] candidates =
        {
            new(5, 10), new(10, 9), new(15, 11), new(25, 10), new(30, 9), new(35, 11),
            new(7, 15), new(12, 18), new(17, 16), new(23, 17), new(28, 15), new(34, 18),
            new(5, 22), new(10, 23), new(15, 21), new(25, 22), new(30, 23), new(35, 21)
        };

        int seed = unchecked(
            (int)Game1.uniqueIDForThisGame
            + Game1.Date.TotalDays * 397
            + this.Save.Data.AirshipFlightsTaken * 7919
        );
        Random random = new(seed);
        Point[] shuffled = candidates.OrderBy(_ => random.Next()).ToArray();
        int count = Math.Min(random.Next(8, 12), shuffled.Length);
        int spawned = 0;

        foreach (Point tile in shuffled)
        {
            if (spawned >= count)
                break;

            Vector2 tileVector = new(tile.X, tile.Y);
            Vector2 position = tileVector * 64f;
            try
            {
                if (location.IsTileBlockedBy(tileVector) || location.Objects.ContainsKey(tileVector))
                    continue;
            }
            catch
            {
                continue;
            }

            int roll = random.Next(100);
            Monster monster = roll switch
            {
                < 58 => new GreenSlime(position, 0),
                < 83 => new Bat(position),
                _ => new Bug(position, 0)
            };
            monster.modData[Region1MonsterMarkerKey] = "1";
            location.characters.Add(monster);
            spawned++;
        }

        this.Monitor.Log(
            $"Region I visit populated with {spawned} controlled monster(s). Drops remain routed through Cardcha's existing Scrap pipeline.",
            LogLevel.Trace
        );
    }

    private Point ResolveSkyDockTile()
    {
        if (this.CachedSkyDockTile is Point cached)
            return cached;

        GameLocation? forest = Game1.getLocationFromName(SkyDockLocationName);
        if (forest is null)
        {
            this.CachedSkyDockTile = new Point(6, 6);
            return this.CachedSkyDockTile.Value;
        }

        Point farmWarp = this.ResolveForestFarmWarpTile();
        int width = forest.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 120;
        int height = forest.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 120;

        // Player exits the Farm into Forest; the dock should be visible immediately to the left.
        // Search a compact left-side band instead of claiming a fixed vanilla tile.
        Point preferred = new(
            Math.Clamp(farmWarp.X - 7, 2, Math.Max(2, width - 3)),
            Math.Clamp(farmWarp.Y + 2, 2, Math.Max(2, height - 3))
        );

        Point? safe = FindSafeDockTile(forest, preferred, farmWarp);
        this.CachedSkyDockTile = safe ?? preferred;
        return this.CachedSkyDockTile.Value;
    }

    private Point ResolveForestFarmWarpTile()
    {
        if (this.CachedForestFarmWarpTile is Point cached)
            return cached;

        GameLocation? forest = Game1.getLocationFromName(SkyDockLocationName);
        if (forest is null)
        {
            this.CachedForestFarmWarpTile = new Point(20, 2);
            return this.CachedForestFarmWarpTile.Value;
        }

        try
        {
            foreach (Warp warp in forest.warps)
            {
                if (!string.IsNullOrWhiteSpace(warp.TargetName)
                    && warp.TargetName.Contains("Farm", StringComparison.OrdinalIgnoreCase))
                {
                    this.CachedForestFarmWarpTile = new Point(warp.X, warp.Y);
                    return this.CachedForestFarmWarpTile.Value;
                }
            }
        }
        catch
        {
            // A heavily rewritten Forest may expose warps differently. Fall back to upper-middle.
        }

        int width = forest.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 120;
        this.CachedForestFarmWarpTile = new Point(Math.Clamp(width / 2, 3, Math.Max(3, width - 4)), 2);
        return this.CachedForestFarmWarpTile.Value;
    }

    private static Point? FindSafeDockTile(GameLocation forest, Point preferred, Point farmWarp)
    {
        int width = forest.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 120;
        int height = forest.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 120;

        for (int radius = 0; radius <= 7; radius++)
        {
            for (int y = Math.Max(2, preferred.Y - radius); y <= Math.Min(height - 3, preferred.Y + radius); y++)
            {
                // Keep every candidate visibly left of the Farm entrance and out of its warp lane.
                for (int x = Math.Max(2, preferred.X - radius); x <= Math.Min(farmWarp.X - 4, preferred.X + radius); x++)
                {
                    Point candidate = new(x, y);
                    if (IsDockFootprintSafe(forest, candidate, farmWarp))
                        return candidate;
                }
            }
        }

        return null;
    }

    private static bool IsDockFootprintSafe(GameLocation location, Point anchor, Point farmWarp)
    {
        Point[] footprint =
        {
            anchor,
            new(anchor.X - 1, anchor.Y),
            new(anchor.X + 1, anchor.Y),
            new(anchor.X - 1, anchor.Y + 1),
            new(anchor.X, anchor.Y + 1),
            new(anchor.X + 1, anchor.Y + 1)
        };

        foreach (Point p in footprint)
        {
            if (Math.Abs(p.X - farmWarp.X) <= 3 && Math.Abs(p.Y - farmWarp.Y) <= 3)
                return false;

            try
            {
                Vector2 tile = new(p.X, p.Y);
                if (location.IsTileBlockedBy(tile) || location.Objects.ContainsKey(tile))
                    return false;
            }
            catch
            {
                return false;
            }

            try
            {
                foreach (Warp warp in location.warps)
                {
                    if (Math.Abs(warp.X - p.X) <= 2 && Math.Abs(warp.Y - p.Y) <= 2)
                        return false;
                }
            }
            catch
            {
                // Don't reject the candidate solely because a map overhaul hides warp metadata.
            }
        }

        return true;
    }

    private static Point ResolveSkyDockInteriorArrivalTile(GameLocation interior)
    {
        int width = interior.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30;
        int height = interior.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;
        return FindClearTileNear(interior, new Point(width / 2, Math.Max(2, height - 4)));
    }

    private static Point ResolveSkyDockInteriorExitTile(GameLocation interior)
    {
        int width = interior.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30;
        int height = interior.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;
        return new Point(width / 2, Math.Max(1, height - 2));
    }

    private static Point ResolveSkyDockInteriorRouteTile(GameLocation interior)
    {
        int width = interior.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30;
        int height = interior.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;
        return new Point(Math.Clamp(width / 3, 3, width - 4), Math.Clamp(7, 3, height - 5));
    }

    private static Point ResolveSkyDockInteriorBayTile(GameLocation interior)
    {
        int width = interior.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30;
        int height = interior.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;
        return new Point(Math.Clamp(width - 6, 4, width - 3), Math.Clamp(7, 3, height - 5));
    }

    private static Point ResolveRegion1ArrivalTile(GameLocation region)
    {
        int width = region.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 40;
        int height = region.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 28;
        return FindClearTileNear(region, new Point(width / 2, Math.Max(8, height - 4)));
    }

    private static Point ResolveRegion1ReturnTile(GameLocation region)
    {
        int width = region.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 40;
        int height = region.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 28;
        return new Point(width / 2, Math.Max(8, height - 3));
    }

    private static Point ResolveRegion1GateTile(GameLocation region)
    {
        int width = region.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 40;
        return new Point(width / 2, 6);
    }

    private static Point ResolveRegion1MainGateArrivalTile(GameLocation region)
    {
        Point gate = ResolveRegion1GateTile(region);
        return FindClearTileNear(region, new Point(gate.X, gate.Y + 2));
    }

    private static Point ResolveRegion1StagingArrivalTile(GameLocation region)
    {
        Point gate = ResolveRegion1GateTile(region);
        return FindClearTileNear(region, new Point(gate.X, gate.Y - 2));
    }

    private static Point ResolveRegion1BossSigilTile(GameLocation region)
    {
        int width = region.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 40;
        return new Point(width / 2, 2);
    }

    private static Point ResolveDeckArrivalTile(GameLocation deck)
    {
        int width = deck.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 24;
        int height = deck.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 14;
        Point preferred = new(width / 2, Math.Max(2, height - 4));
        return FindClearTileNear(deck, preferred);
    }

    private static Point ResolveDeckExitTile(GameLocation deck)
    {
        int width = deck.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 24;
        int height = deck.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 14;
        return new Point(Math.Clamp(width / 2, 1, width - 2), Math.Clamp(height - 2, 1, height - 2));
    }

    private static Point ResolveDeckHelmTile(GameLocation deck)
    {
        int width = deck.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 24;
        int height = deck.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 14;
        return new Point(Math.Clamp(width / 2, 2, width - 3), Math.Clamp(4, 2, height - 3));
    }

    private void DrawFlyby(SpriteBatch batch)
    {
        float progress = Math.Clamp(
            (Environment.TickCount64 - this.FlybyStartedAtMs) / (float)FlybyDurationMs,
            0f,
            1f
        );

        float screenX = MathHelper.Lerp(-240f, Game1.viewport.Width + 240f, progress);
        float crest = (float)Math.Sin(progress * Math.PI);
        float bob = (float)Math.Sin(progress * MathHelper.TwoPi * 1.35f) * (2.5f + crest * 4.5f);
        float screenY = 92f - crest * 18f + bob;
        float rotation = (float)Math.Sin(progress * MathHelper.TwoPi * 1.15f) * FlybyTiltRadians;
        float verticalScale = 1f + (float)Math.Sin(progress * MathHelper.TwoPi * 1.35f) * 0.012f;
        Vector2 world = new(Game1.viewport.X + screenX, Game1.viewport.Y + screenY);
        Vector2 p = Game1.GlobalToLocal(Game1.viewport, world);

        if (this.TryDrawAirshipSprite(
                batch,
                p,
                230f,
                new Color(105, 94, 128) * 0.78f,
                SpriteEffects.None,
                rotation,
                verticalScale))
        {
            return;
        }

        Color silhouette = new Color(48, 38, 68) * 0.82f;
        Color gondola = new Color(66, 47, 49) * 0.88f;
        Color glint = new Color(190, 225, 255) * 0.55f;

        DrawRect(batch, new Rectangle((int)p.X - 74, (int)p.Y - 20, 148, 10), silhouette);
        DrawRect(batch, new Rectangle((int)p.X - 88, (int)p.Y - 10, 176, 12), silhouette);
        DrawRect(batch, new Rectangle((int)p.X - 94, (int)p.Y + 2, 188, 14), silhouette);
        DrawRect(batch, new Rectangle((int)p.X - 82, (int)p.Y + 16, 164, 10), silhouette);
        DrawRect(batch, new Rectangle((int)p.X - 50, (int)p.Y + 26, 100, 6), silhouette);

        DrawRect(batch, new Rectangle((int)p.X - 46, (int)p.Y + 42, 92, 16), gondola);
        DrawRect(batch, new Rectangle((int)p.X - 30, (int)p.Y + 34, 4, 10), silhouette);
        DrawRect(batch, new Rectangle((int)p.X + 26, (int)p.Y + 34, 4, 10), silhouette);
        DrawRect(batch, new Rectangle((int)p.X + 45, (int)p.Y + 46, 24, 5), gondola);
        DrawRect(batch, new Rectangle((int)p.X - 67, (int)p.Y + 47, 22, 4), gondola);
        DrawRect(batch, new Rectangle((int)p.X + 12, (int)p.Y + 47, 5, 4), glint);
    }

    private void DrawSkyDock(SpriteBatch batch, Point tile)
    {
        Vector2 screen = Game1.GlobalToLocal(
            Game1.viewport,
            new Vector2((tile.X - 1) * 64f, tile.Y * 64f)
        );

        // Small, non-blocking Stardew-scale foundation: weathered planks + two rope posts +
        // MiMi's restrained cyan route glow. This is intentionally lightweight until final art.
        Color plankDark = new Color(96, 63, 38) * 0.86f;
        Color plank = new Color(145, 98, 57) * 0.90f;
        Color edge = new Color(69, 47, 31) * 0.92f;
        Color rope = new Color(205, 174, 112) * 0.82f;
        float pulse = 0.42f + 0.18f * (float)Math.Sin(Environment.TickCount64 / 260.0);
        Color glow = new Color(105, 214, 236) * pulse;
        float shipBob = (float)Math.Sin(Environment.TickCount64 / 360.0) * 4f;
        this.TryDrawAirshipSprite(
            batch,
            new Vector2(screen.X + 96f, screen.Y - 58f + shipBob),
            170f,
            Color.White * 0.88f,
            SpriteEffects.None
        );

        for (int row = 0; row < 2; row++)
        {
            int y = (int)screen.Y + 18 + row * 25;
            DrawRect(batch, new Rectangle((int)screen.X + 5, y, 182, 22), plank);
            DrawRect(batch, new Rectangle((int)screen.X + 5, y + 19, 182, 3), plankDark);
            for (int seam = 1; seam <= 5; seam++)
                DrawRect(batch, new Rectangle((int)screen.X + seam * 30, y, 2, 22), edge * 0.62f);
        }

        DrawRect(batch, new Rectangle((int)screen.X + 9, (int)screen.Y - 16, 9, 78), edge);
        DrawRect(batch, new Rectangle((int)screen.X + 174, (int)screen.Y - 16, 9, 78), edge);
        DrawRect(batch, new Rectangle((int)screen.X + 18, (int)screen.Y - 5, 156, 3), rope);
        DrawRect(batch, new Rectangle((int)screen.X + 78, (int)screen.Y + 31, 38, 5), glow);
        DrawRect(batch, new Rectangle((int)screen.X + 94, (int)screen.Y + 15, 6, 37), glow);
    }

    private void DrawSkyDockInteriorDetails(SpriteBatch batch, GameLocation interior)
    {
        Point route = ResolveSkyDockInteriorRouteTile(interior);
        Point exit = ResolveSkyDockInteriorExitTile(interior);
        Point bay = ResolveSkyDockInteriorBayTile(interior);

        // Route board: warm wood with a restrained MiMi cyan indicator.
        Vector2 board = Game1.GlobalToLocal(Game1.viewport, new Vector2((route.X - 1) * 64f, (route.Y - 2) * 64f));
        DrawRect(batch, new Rectangle((int)board.X, (int)board.Y, 150, 82), new Color(91, 58, 36) * 0.94f);
        DrawRect(batch, new Rectangle((int)board.X + 7, (int)board.Y + 7, 136, 68), new Color(147, 100, 57) * 0.96f);
        float pulse = 0.45f + 0.18f * (float)Math.Sin(Environment.TickCount64 / 270.0);
        DrawRect(batch, new Rectangle((int)board.X + 22, (int)board.Y + 52, 92, 6), new Color(104, 220, 238) * pulse);

        // Open-sky docking bay on the right wall. This is an overlay inside Cardcha's own location,
        // so it cannot affect vanilla collision/pathing.
        Vector2 sky = Game1.GlobalToLocal(Game1.viewport, new Vector2((bay.X - 2) * 64f, (bay.Y - 4) * 64f));
        DrawRect(batch, new Rectangle((int)sky.X, (int)sky.Y, 250, 170), new Color(74, 128, 167) * 0.92f);
        DrawRect(batch, new Rectangle((int)sky.X + 18, (int)sky.Y + 30, 72, 13), new Color(222, 237, 240) * 0.76f);
        DrawRect(batch, new Rectangle((int)sky.X + 105, (int)sky.Y + 72, 95, 12), new Color(222, 237, 240) * 0.62f);
        float bayBob = (float)Math.Sin(Environment.TickCount64 / 330.0) * 3f;
        this.TryDrawAirshipSprite(
            batch,
            new Vector2(sky.X + 125f, sky.Y + 86f + bayBob),
            215f,
            Color.White * 0.96f,
            SpriteEffects.None
        );
        DrawRect(batch, new Rectangle((int)sky.X - 8, (int)sky.Y - 8, 266, 8), new Color(67, 45, 31) * 0.96f);
        DrawRect(batch, new Rectangle((int)sky.X - 8, (int)sky.Y + 170, 266, 9), new Color(67, 45, 31) * 0.96f);
        DrawRect(batch, new Rectangle((int)sky.X - 8, (int)sky.Y - 8, 8, 187), new Color(67, 45, 31) * 0.96f);
        DrawRect(batch, new Rectangle((int)sky.X + 250, (int)sky.Y - 8, 8, 187), new Color(67, 45, 31) * 0.96f);

        DrawWorldMarker(batch, route, new Color(255, 220, 120) * 0.58f);
        DrawWorldMarker(batch, bay, new Color(105, 214, 236) * 0.62f);
        DrawWorldMarker(batch, exit, new Color(120, 220, 255) * 0.52f);
    }

    private void DrawRegion1Details(SpriteBatch batch, GameLocation region)
    {
        int width = region.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 40;
        int height = region.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 28;
        Point gate = ResolveRegion1GateTile(region);
        Point returnPad = ResolveRegion1ReturnTile(region);
        Point bossSigil = ResolveRegion1BossSigilTile(region);

        Vector2 path = Game1.GlobalToLocal(
            Game1.viewport,
            new Vector2((width / 2 - 1) * 64f, (gate.Y + 1) * 64f)
        );
        DrawRect(
            batch,
            new Rectangle((int)path.X, (int)path.Y, 192, Math.Max(64, (height - gate.Y - 4) * 64)),
            new Color(154, 116, 70) * 0.28f
        );

        Vector2 wall = Game1.GlobalToLocal(Game1.viewport, new Vector2(0f, gate.Y * 64f));
        DrawRect(batch, new Rectangle((int)wall.X, (int)wall.Y + 8, width * 64, 48), new Color(43, 63, 55) * 0.92f);
        DrawRect(batch, new Rectangle((int)wall.X, (int)wall.Y + 8, width * 64, 7), new Color(104, 142, 102) * 0.78f);

        Vector2 gateScreen = Game1.GlobalToLocal(
            Game1.viewport,
            new Vector2((gate.X - 1) * 64f, (gate.Y - 1) * 64f)
        );
        DrawRect(batch, new Rectangle((int)gateScreen.X, (int)gateScreen.Y, 192, 128), new Color(47, 39, 48) * 0.96f);
        DrawRect(batch, new Rectangle((int)gateScreen.X + 12, (int)gateScreen.Y + 14, 168, 102), new Color(117, 86, 48) * 0.92f);
        for (int x = 34; x <= 150; x += 29)
            DrawRect(batch, new Rectangle((int)gateScreen.X + x, (int)gateScreen.Y + 20, 9, 90), new Color(37, 31, 40) * 0.96f);

        Vector2 pad = Game1.GlobalToLocal(
            Game1.viewport,
            new Vector2((returnPad.X - 2) * 64f, (returnPad.Y - 1) * 64f)
        );
        DrawRect(batch, new Rectangle((int)pad.X, (int)pad.Y, 320, 128), new Color(84, 61, 42) * 0.76f);
        DrawRect(batch, new Rectangle((int)pad.X + 16, (int)pad.Y + 18, 288, 8), new Color(105, 214, 236) * 0.55f);
        float padBob = (float)Math.Sin(Environment.TickCount64 / 340.0) * 4f;
        this.TryDrawAirshipSprite(
            batch,
            new Vector2(pad.X + 160f, pad.Y - 55f + padBob),
            260f,
            Color.White * 0.94f,
            SpriteEffects.None
        );

        Vector2 sigil = Game1.GlobalToLocal(
            Game1.viewport,
            new Vector2((bossSigil.X - 1) * 64f, (bossSigil.Y - 1) * 64f)
        );
        float pulse = 0.48f + 0.17f * (float)Math.Sin(Environment.TickCount64 / 280.0);
        DrawRect(batch, new Rectangle((int)sigil.X, (int)sigil.Y + 48, 192, 14), new Color(190, 118, 67) * pulse);
        DrawRect(batch, new Rectangle((int)sigil.X + 88, (int)sigil.Y, 16, 112), new Color(190, 118, 67) * pulse);

        DrawWorldMarker(batch, gate, new Color(255, 196, 96) * 0.62f);
        DrawWorldMarker(batch, returnPad, new Color(105, 214, 236) * 0.66f);
        DrawWorldMarker(batch, bossSigil, new Color(223, 112, 86) * 0.62f);
    }

    private void DrawFlightCutscene(SpriteBatch batch)
    {
        float p = Math.Clamp(
            (Environment.TickCount64 - this.FlightCutsceneStartedAtMs) / (float)FlightCutsceneDurationMs,
            0f,
            1f
        );
        float eased = MathHelper.SmoothStep(0f, 1f, p);
        int w = Game1.viewport.Width;
        int h = Game1.viewport.Height;

        DrawRect(batch, new Rectangle(0, 0, w, h), new Color(21, 31, 51) * 0.94f);

        // Dock frame.
        Color woodDark = new Color(69, 46, 31) * 0.95f;
        Color wood = new Color(132, 87, 50) * 0.96f;
        DrawRect(batch, new Rectangle(0, h - 145, w, 145), woodDark);
        for (int x = 0; x < w; x += 72)
            DrawRect(batch, new Rectangle(x, h - 137, 66, 72), wood);
        DrawRect(batch, new Rectangle(70, 0, 16, h - 80), woodDark);
        DrawRect(batch, new Rectangle(w - 86, 0, 16, h - 80), woodDark);

        // Clouds make the scene read as an elevated dock even before bespoke Cardcha art exists.
        Color cloud = new Color(222, 236, 241) * 0.66f;
        DrawRect(batch, new Rectangle(w / 8, h / 4, w / 5, 18), cloud);
        DrawRect(batch, new Rectangle(w * 5 / 8, h / 3, w / 4, 20), cloud * 0.82f);

        float crest = (float)Math.Sin(p * Math.PI);
        float travel = this.FlightCutsceneReturning ? 1f - eased : eased;
        float shipX = MathHelper.Lerp(w * 0.28f, w * 0.78f, travel);
        float bob = (float)Math.Sin(p * MathHelper.TwoPi * 1.25f) * (3f + crest * 8f);
        float lift = crest * 24f;
        float shipY = h * 0.40f - lift + bob;
        float direction = this.FlightCutsceneReturning ? -1f : 1f;
        float rotation = -direction * CutsceneTiltRadians * (0.30f + crest * 0.70f);
        float verticalScale = 1f + (float)Math.Sin(p * MathHelper.TwoPi * 1.75f) * CutsceneScalePulse;
        SpriteEffects directionEffect = this.FlightCutsceneReturning
            ? SpriteEffects.FlipHorizontally
            : SpriteEffects.None;
        float targetWidth = Math.Min(720f, w * 0.62f);

        // The eased travel, bob, tilt and tiny breathing scale make departure and return feel
        // like a suspended vessel instead of a static overlay. The same motion runs on both
        // directions; only the travel direction and sprite flip are reversed.
        if (!this.TryDrawAirshipSprite(
                batch,
                new Vector2(shipX, shipY),
                targetWidth,
                Color.White * 0.98f,
                directionEffect,
                rotation,
                verticalScale))
        {
            this.DrawCinematicAirship(batch, new Vector2(shipX, shipY), 1.15f);
        }

        string title = ModEntry.T(this.FlightCutsceneReturning ? "airship.cutscene.return" : "airship.cutscene.departure");
        Vector2 size = Game1.smallFont.MeasureString(title);
        batch.DrawString(Game1.smallFont, title, new Vector2((w - size.X) / 2f, 26f), Color.White * 0.92f);
    }

    private bool TryDrawAirshipSprite(
        SpriteBatch batch,
        Vector2 center,
        float targetWidth,
        Color tint,
        SpriteEffects effects)
    {
        return this.TryDrawAirshipSprite(
            batch,
            center,
            targetWidth,
            tint,
            effects,
            rotation: 0f,
            verticalScale: 1f
        );
    }

    private bool TryDrawAirshipSprite(
        SpriteBatch batch,
        Vector2 center,
        float targetWidth,
        Color tint,
        SpriteEffects effects,
        float rotation,
        float verticalScale)
    {
        Texture2D? sprite = this.GetAirshipVisual();
        if (sprite is null || targetWidth <= 0f)
            return false;

        float scale = targetWidth / sprite.Width;
        Vector2 origin = new(sprite.Width / 2f, sprite.Height / 2f);
        Vector2 drawScale = new(scale, scale * Math.Max(0.01f, verticalScale));
        batch.Draw(
            sprite,
            center,
            sourceRectangle: null,
            color: tint,
            rotation: rotation,
            origin: origin,
            scale: drawScale,
            effects: effects,
            layerDepth: 1f
        );
        return true;
    }

    private Texture2D? GetAirshipVisual()
    {
        if (this.AirshipVisual is not null)
            return this.AirshipVisual;

        if (this.AirshipVisualLoadFailed)
            return null;

        try
        {
            this.AirshipVisual = this.Helper.ModContent.Load<Texture2D>(AirshipVisualPath);
            return this.AirshipVisual;
        }
        catch (Exception ex)
        {
            this.AirshipVisualLoadFailed = true;
            if (!this.LoggedAirshipVisualFailure)
            {
                this.LoggedAirshipVisualFailure = true;
                this.Monitor.Log(
                    $"Couldn't load Cardcha Airship visual; procedural fallback remains active. {ex.GetType().Name}: {ex.Message}",
                    LogLevel.Warn
                );
            }
            return null;
        }
    }

    private void DrawCinematicAirship(SpriteBatch batch, Vector2 p, float scale)
    {
        int X(float n) => (int)(p.X + n * scale);
        int Y(float n) => (int)(p.Y + n * scale);
        int S(float n) => Math.Max(1, (int)(n * scale));

        Color balloon = new Color(55, 44, 75) * 0.96f;
        Color hull = new Color(101, 66, 43) * 0.98f;
        Color trim = new Color(178, 125, 67) * 0.92f;
        Color glow = new Color(116, 222, 241) * 0.72f;

        DrawRect(batch, new Rectangle(X(-76), Y(-45), S(152), S(13)), balloon);
        DrawRect(batch, new Rectangle(X(-92), Y(-31), S(184), S(21)), balloon);
        DrawRect(batch, new Rectangle(X(-82), Y(-9), S(164), S(15)), balloon);
        DrawRect(batch, new Rectangle(X(-45), Y(28), S(90), S(22)), hull);
        DrawRect(batch, new Rectangle(X(-56), Y(50), S(112), S(8)), trim);
        DrawRect(batch, new Rectangle(X(-31), Y(6), S(4), S(23)), trim);
        DrawRect(batch, new Rectangle(X(27), Y(6), S(4), S(23)), trim);
        DrawRect(batch, new Rectangle(X(7), Y(37), S(7), S(7)), glow);
    }

    private void DrawDeckMarkers(SpriteBatch batch, GameLocation deck)
    {
        Point helm = ResolveDeckHelmTile(deck);
        Point exit = ResolveDeckExitTile(deck);
        DrawWorldMarker(batch, helm, new Color(255, 220, 120) * 0.58f);
        DrawWorldMarker(batch, exit, new Color(120, 220, 255) * 0.52f);
    }

    private static void DrawWorldMarker(SpriteBatch batch, Point tile, Color color)
    {
        Vector2 screen = Game1.GlobalToLocal(Game1.viewport, new Vector2(tile.X * 64f, tile.Y * 64f));
        DrawRect(batch, new Rectangle((int)screen.X + 14, (int)screen.Y + 48, 36, 5), color);
        DrawRect(batch, new Rectangle((int)screen.X + 29, (int)screen.Y + 34, 6, 24), color);
    }

    private static void DrawRect(SpriteBatch batch, Rectangle rectangle, Color color)
    {
        if (rectangle.Width <= 0 || rectangle.Height <= 0)
            return;
        batch.Draw(Game1.staminaRect, rectangle, color);
    }

    private static Point GetActionTile()
    {
        Point p = new((int)(Game1.player.Position.X / 64f), (int)(Game1.player.Position.Y / 64f));
        return Game1.player.FacingDirection switch
        {
            0 => new Point(p.X, p.Y - 1),
            1 => new Point(p.X + 1, p.Y),
            2 => new Point(p.X, p.Y + 1),
            3 => new Point(p.X - 1, p.Y),
            _ => p
        };
    }

    private static bool IsSkyDockLocation(GameLocation? location)
        => location?.NameOrUniqueName.Equals(SkyDockLocationName, StringComparison.OrdinalIgnoreCase) == true;

    private static bool PlayerIsNear(Point tile)
    {
        Vector2 center = new(tile.X * 64f + 32f, tile.Y * 64f + 32f);
        Vector2 player = Game1.player.Position + new Vector2(32f, 32f);
        return Vector2.DistanceSquared(center, player) <= BoardingUseDistance * BoardingUseDistance;
    }

    private static bool Touches(Point actionTile, Point tile)
        => Math.Abs(actionTile.X - tile.X) <= 1 && Math.Abs(actionTile.Y - tile.Y) <= 1;

    private static Point FindClearTileNear(GameLocation location, Point preferred)
    {
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 24;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 14;
        int centerX = Math.Clamp(preferred.X, 1, Math.Max(1, width - 2));
        int centerY = Math.Clamp(preferred.Y, 1, Math.Max(1, height - 2));

        for (int radius = 0; radius < Math.Max(width, height); radius++)
        {
            for (int y = Math.Max(1, centerY - radius); y <= Math.Min(height - 2, centerY + radius); y++)
            {
                for (int x = Math.Max(1, centerX - radius); x <= Math.Min(width - 2, centerX + radius); x++)
                {
                    if (Math.Abs(x - centerX) != radius && Math.Abs(y - centerY) != radius)
                        continue;

                    Point candidate = new(x, y);
                    try
                    {
                        Vector2 tile = new(candidate.X, candidate.Y);
                        if (!location.IsTileBlockedBy(tile) && !location.Objects.ContainsKey(tile))
                            return candidate;
                    }
                    catch
                    {
                        return candidate;
                    }
                }
            }
        }

        return new Point(centerX, centerY);
    }

    private void ResetRuntime()
    {
        this.FlybyActive = false;
        this.FlybyStartedAtMs = 0;
        this.FlybyArmAfterMs = 0;
        this.DeckCreationFailed = false;
        this.LoggedDeckFailure = false;
        this.SkyDockInteriorCreationFailed = false;
        this.LoggedSkyDockInteriorFailure = false;
        this.Region1CreationFailed = false;
        this.LoggedRegion1Failure = false;
        this.PendingDepartureUntilMs = 0;
        this.FlightCutsceneActive = false;
        this.FlightCutsceneReturning = false;
        this.FlightCutsceneWarped = false;
        this.FlightCutsceneStartedAtMs = 0;
        this.CachedSkyDockTile = null;
        this.CachedForestFarmWarpTile = null;
        this.WarpGraceUntilMs = 0;
        this.AirshipVisual = null;
        this.AirshipVisualLoadFailed = false;
        this.LoggedAirshipVisualFailure = false;
    }
}
