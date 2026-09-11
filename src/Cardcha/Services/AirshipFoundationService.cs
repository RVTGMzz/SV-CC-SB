using Cardcha.UI;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Monsters;
using StardewValley.Objects;

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
    // 0666 Hunt Run 2.0: a daily farming run is intentionally longer than the old 4-room prototype.
    private const int Region1RunMinNodes = 7;
    private const int Region1RunMaxNodes = 10;
    private const int Region1CheckpointNodeA = 3;
    private const int Region1CheckpointNodeB = 6;
    private const int Region1BossBranchMinNode = 7;
    private const string Region1EliteMarkerKey = "Ronvotri.Cardcha/Region1Elite";
    private const string Region1EliteAffixMarkerKey = "Ronvotri.Cardcha/Region1EliteAffix";
    private const string Region1RootNestMarkerKey = "Ronvotri.Cardcha/Region1RootNest";
    private const string Region1LostCacheMarkerKey = "Ronvotri.Cardcha/Region1LostCache";

    private enum Region1RunEncounterType
    {
        Combat,
        Ambush,
        Elite,
        RootNest,
        Shrine,
        LostCache,
        Moonwell,
        AncientEcho
    }

    private enum Region1EliteAffix
    {
        ThornAura,
        Swift,
        Regrowth,
        Bulwark,
        Infested,
        Resonant
    }

    private enum Region1DailyMutation
    {
        CalmGrove,
        BriarBloom,
        MoonlitGrove,
        Overgrown,
        ChaoticResonance
    }

    private enum Region1RunRouteKind
    {
        Moss,
        Briar,
        Ancient
    }
    private static readonly string[] Region1RunRoomLocationNames =
    {
        "Cardcha_R1_VerdantClearing",
        "Cardcha_R1_MossCreek",
        "Cardcha_R1_OldRuins",
        "Cardcha_R1_BriarThicket",
        "Cardcha_R1_HollowGrove",
        "Cardcha_R1_CardShrine",
    };
    private static readonly string[] Region1RunRoomMapAssetNames =
    {
        "Maps/Cardcha_R1_VerdantClearing",
        "Maps/Cardcha_R1_MossCreek",
        "Maps/Cardcha_R1_OldRuins",
        "Maps/Cardcha_R1_BriarThicket",
        "Maps/Cardcha_R1_HollowGrove",
        "Maps/Cardcha_R1_CardShrine",
    };
    private static readonly string[] Region1RunRoomMapPaths =
    {
        "assets/region1_rooms/room_1_verdant_clearing.tmx",
        "assets/region1_rooms/room_2_moss_creek.tmx",
        "assets/region1_rooms/room_3_old_ruins.tmx",
        "assets/region1_rooms/room_4_briar_thicket.tmx",
        "assets/region1_rooms/room_5_hollow_grove.tmx",
        "assets/region1_rooms/room_6_card_shrine.tmx",
    };
    private static readonly string[] Region1RunRoomNameKeys =
    {
        "airship.region1.run.room.0",
        "airship.region1.run.room.1",
        "airship.region1.run.room.2",
        "airship.region1.run.room.3",
        "airship.region1.run.room.4",
        "airship.region1.run.room.5",
    };
    private const string AirshipVisualPath = "assets/airship_visual.png";
    private const string AirshipGateVisualPath = "assets/airship_gate_auth.png";
    private const string AirshipUpgradeVisualPath = "assets/airship_upgrade_visuals.png";
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
    private const float BoardingUseDistance = 160f;
    private const float ForestGateUseDistance = 160f;
    private const string InteriorDecorMarkerKey = "Ronvotri.Cardcha/AirshipInteriorDecor";
    private const string InteriorDecorVersion = "alpha.28.0.4.14.4.5.12.45.3";
    private const float FlybyTiltRadians = 0.028f;
    private const float CutsceneTiltRadians = 0.045f;
    private const float CutsceneScalePulse = 0.018f;
    private const float PropellerSpinRadiansPerSecond = 22f;

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly ControllerProfileService Controller;
    private Func<string>? MilestoneRouteAction;
    private string PendingExternalFlightLocationName = string.Empty;
    private Point PendingExternalFlightArrivalTile;

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
    private Texture2D? AirshipGateVisual;
    private bool AirshipGateVisualLoadFailed;
    private Texture2D? AirshipUpgradeVisuals;
    private bool AirshipUpgradeVisualsLoadFailed;
    private bool AirshipVisualLoadFailed;
    private bool LoggedAirshipVisualFailure;
    private bool TestGateAccessActive;
    private GameLocation? DeckDecorAppliedLocation;
    private GameLocation? SkyDockDecorAppliedLocation;
    private int[] Region1RunRoute = Array.Empty<int>();
    private Region1RunEncounterType[] Region1RunEncounters = Array.Empty<Region1RunEncounterType>();
    private Region1RunRouteKind[] Region1RunRouteKinds = Array.Empty<Region1RunRouteKind>();
    private int Region1RunStep = -1;
    private int Region1RunSeed;
    private int Region1RunTargetNodes;
    private bool Region1RunActive;
    private bool Region1RunCompleted;
    private bool Region1RunRouteChoicesPrepared;
    private int Region1RunLeftRoomIndex = -1;
    private int Region1RunRightRoomIndex = -1;
    private Region1RunRouteKind Region1RunLeftRouteKind = Region1RunRouteKind.Moss;
    private Region1RunRouteKind Region1RunRightRouteKind = Region1RunRouteKind.Briar;
    private bool Region1RunAwaitingBoon;
    private string[] Region1RunBoonChoices = Array.Empty<string>();
    private readonly HashSet<string> Region1RunBoons = new(StringComparer.OrdinalIgnoreCase);
    private readonly HashSet<int> Region1RunRewardedSteps = new();
    private int Region1RunUnbankedScrap;
    private int Region1RunUnbankedShiny;
    private long Region1EliteAuraNextAtMs;
    private int Region1RunRareRoomsSeen;

    public AirshipFoundationService(IModHelper helper, IMonitor monitor, SaveService save, ControllerProfileService controller)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.Controller = controller;
    }

    public void BindMilestoneRouteHandler(Func<string> handler)
        => this.MilestoneRouteAction = handler;

    public int GetRegionFareForExternalRoute(int region)
        => this.GetRegionFare(region);

    public string BeginExternalRegionFlight(int region, string targetLocationName, Point arrivalTile)
    {
        if (!Context.IsWorldReady || region is not (2 or 3 or 4))
            return ModEntry.T("airship.expedition.unavailable");
        GameLocation? target = Game1.getLocationFromName(targetLocationName);
        if (target is null)
            return ModEntry.T("airship.expedition.unavailable");

        int fare = this.GetRegionFare(region);
        if (Game1.player.Money < fare)
            return ModEntry.T("airship.route.not_enough", new { fare, money = Game1.player.Money });
        if (fare > 0)
            Game1.player.Money -= fare;

        this.Save.Data.AirshipFlightsTaken++;
        this.Save.Data.AirshipTotalFarePaid += fare;
        this.Save.Save();
        this.PendingExternalFlightLocationName = targetLocationName;
        this.PendingExternalFlightArrivalTile = arrivalTile;
        this.StartFlightCutscene(returning: false);
        return string.Empty;
    }

    public void StartExternalRegionReturnFlight()
    {
        this.PendingExternalFlightLocationName = string.Empty;
        this.PendingExternalFlightArrivalTile = Point.Zero;
        this.StartFlightCutscene(returning: true);
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

        for (int i = 0; i < Region1RunRoomMapAssetNames.Length; i++)
        {
            if (!e.NameWithoutLocale.IsEquivalentTo(Region1RunRoomMapAssetNames[i]))
                continue;

            e.LoadFromModFile<xTile.Map>(Region1RunRoomMapPaths[i], AssetLoadPriority.Exclusive);
            return;
        }

        if (e.NameWithoutLocale.IsEquivalentTo(Region1MapAssetName))
            e.LoadFromModFile<xTile.Map>(Region1MapPath, AssetLoadPriority.Exclusive);
    }

    public void OnSaveLoaded()
    {
        this.ResetRuntime();
        GameLocation? deck = this.EnsureDeckLocation();
        GameLocation? dock = this.EnsureSkyDockInteriorLocation();
        this.EnsureRegion1Location();
        if (deck is not null) this.EnsureDeckVanillaFurniture(deck);
        if (dock is not null) this.EnsureSkyDockVanillaFurniture(dock);
        this.EnsureRegion1RunRoomLocations();
        this.ResetRegion1RunState();
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
        GameLocation? deck = this.EnsureDeckLocation();
        GameLocation? dock = this.EnsureSkyDockInteriorLocation();
        this.EnsureRegion1Location();
        if (deck is not null) this.EnsureDeckVanillaFurniture(deck);
        if (dock is not null) this.EnsureSkyDockVanillaFurniture(dock);
        this.EnsureRegion1RunRoomLocations();
        this.ResetRegion1RunState();
        this.MigrateUnlockFromExistingStory();
        this.FlybyArmAfterMs = Environment.TickCount64 + 1500L;
    }

    public void OnReturnedToTitle()
    {
        this.ResetRuntime();
        this.LoggedDeckCreation = false;
        this.LoggedSkyDockInteriorCreation = false;
        this.LoggedRegion1Creation = false;
        this.DeckDecorAppliedLocation = null;
        this.SkyDockDecorAppliedLocation = null;
        this.ResetRegion1RunState();
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

        GameLocation? activeRunRoom = Game1.currentLocation;
        if (this.Region1RunActive
            && activeRunRoom is not null
            && TryGetRegion1RunRoomIndex(activeRunRoom, out _)
            && CountRegion1MarkedMonsters(activeRunRoom) == 0
            && !this.CurrentRegion1NodeNeedsManualInteraction())
        {
            this.HandleRegion1RunNodeCleared(activeRunRoom);
        }

        if (this.Region1RunActive
            && activeRunRoom is not null
            && TryGetRegion1RunRoomIndex(activeRunRoom, out _)
            && e.IsMultipleOf(60))
        {
            this.UpdateRegion1EliteAffixes(activeRunRoom, now);
        }

        // Cardcha-owned portal lanes behave like real exits: walk onto the endpoint and transition.
        // The Forest gate deliberately stays action-driven for maximum map-overhaul compatibility.
        if (now >= this.WarpGraceUntilMs && this.TryHandleAutoTransition())
            return;

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
        if (location?.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase) == true)
            this.DrawSkyDockInteriorDetails(e.SpriteBatch, location);

        if (location?.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase) == true)
            this.DrawDeckMarkers(e.SpriteBatch, location);

        if (location?.NameOrUniqueName.Equals(Region1LocationName, StringComparison.OrdinalIgnoreCase) == true)
            this.DrawRegion1Details(e.SpriteBatch, location);

        if (location is not null && TryGetRegion1RunRoomIndex(location, out int activeRoomIndex))
        {
            Region1StardewDecorRenderer.Draw(e.SpriteBatch, location, activeRoomIndex);
            this.DrawRegion1HuntRun2Overlay(e.SpriteBatch, location);
        }

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

        // The Arcane Gate is the normal gameplay entrance. It never edits Forest collision/pathing.
        if (IsSkyDockLocation(location) && (this.Save.Data.AirshipUnlocked || this.TestGateAccessActive))
        {
            Point dock = this.ResolveSkyDockTile();
            // The Forest gate never edits collision. A wider action-only radius lets the player
            // activate it from the reachable side of fences/foliage on modded Forest maps.
            if (!PlayerIsNear(dock, ForestGateUseDistance))
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
            Point lostFound = ResolveSkyDockLostFoundTile(location);
            Point interiorExit = ResolveSkyDockInteriorExitTile(location);
            if (Touches(interiorAction, lostFound))
            {
                this.Helper.Input.Suppress(e.Button); Game1.playSound("openBox"); Game1.drawObjectDialogue(ModEntry.T("airship.lostfound.empty")); return;
            }

            if (interiorAction == route)
            {
                this.Helper.Input.Suppress(e.Button);
                if (this.MilestoneRouteAction is not null)
                {
                    string message = this.MilestoneRouteAction();
                    if (!string.IsNullOrWhiteSpace(message))
                        Game1.drawObjectDialogue(message);
                }
                else
                {
                    int owned = this.Save.Data.OwnedCards?.Count ?? 0;
                    Game1.drawObjectDialogue(ModEntry.T("airship.arcane.route_console", new { cards = owned }));
                }
                return;
            }

            if (interiorAction == bay)
            {
                this.Helper.Input.Suppress(e.Button);
                if (this.WarpToAirshipBridge())
                    Game1.showGlobalMessage(ModEntry.T("airship.arcane.bridge.entered"));
                else
                    Game1.drawObjectDialogue(ModEntry.T("airship.arcane.bridge.unavailable"));
                return;
            }

            if (interiorAction == interiorExit)
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

        if (TryGetRegion1RunRoomIndex(location, out _))
        {
            this.HandleRegion1RunRoomInteraction(e, location);
            return;
        }

        if (!location.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))
            return;

        Point action = GetActionTile();
        Point helm = ResolveDeckHelmTile(location);
        Point exit = ResolveDeckExitTile(location);

        if (action == helm)
        {
            this.Helper.Input.Suppress(e.Button);
            this.HandleRegion1DepartureRequest();
            return;
        }

        foreach ((AirshipUpgradeSystem system, Point tile) in ResolveDeckUpgradeSockets())
        {
            if (!ActionTouchesStation(action, tile))
                continue;

            this.Helper.Input.Suppress(e.Button);
            Game1.playSound("smallSelect");
            Game1.activeClickableMenu = new AirshipUpgradeMenu(this.Save, this.Controller, system);
            return;
        }

        if (action != exit)
            return;

        this.Helper.Input.Suppress(e.Button);
        if (this.WarpToSkyDockInterior())
            Game1.showGlobalMessage(ModEntry.T("airship.arcane.dock.returned"));
    }

    public void OnWarped(object? sender, WarpedEventArgs e)
    {
        if (!Context.IsWorldReady || !Context.IsMainPlayer)
            return;

        if (e.NewLocation.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))
            this.EnsureDeckVanillaFurniture(e.NewLocation);
        else if (e.NewLocation.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase))
            this.EnsureSkyDockVanillaFurniture(e.NewLocation);

        if (TryGetRegion1RunRoomIndex(e.NewLocation, out int roomIndex))
        {
            if (!this.Region1RunActive || this.Region1RunStep < 0 || this.Region1RunStep >= this.Region1RunTargetNodes)
            {
                Game1.showGlobalMessage(ModEntry.T("airship.region1.run.unstable"));
                return;
            }

            this.PopulateRegion1RunRoom(e.NewLocation, roomIndex);
            if (this.Region1RunStep == 0)
            {
                Region1DailyMutation mutation = this.ResolveRegion1DailyMutation();
                Game1.showGlobalMessage(ModEntry.T("airship.region1.run.mutation.banner", new
                {
                    mutation = ModEntry.T($"airship.region1.run.mutation.{MutationKey(mutation)}.name")
                }));
            }
            string encounter = ModEntry.T($"airship.region1.run.encounter.{this.Region1RunEncounters[this.Region1RunStep].ToString().ToLowerInvariant()}");
            Game1.showGlobalMessage(
                ModEntry.T(
                    "airship.region1.run.enter2",
                    new
                    {
                        step = this.Region1RunStep + 1,
                        total = this.Region1RunTargetNodes,
                        room = ModEntry.T(Region1RunRoomNameKeys[roomIndex]),
                        encounter
                    }
                )
            );
            return;
        }

        // Unexpected exit (death/emergency warp) drops only the current unbanked route bonus.
        // Checkpointed wallet rewards are already persisted and stay safe.
        if (this.Region1RunActive
            && e.OldLocation is not null
            && TryGetRegion1RunRoomIndex(e.OldLocation, out _)
            && !e.NewLocation.NameOrUniqueName.Equals(Region1LocationName, StringComparison.OrdinalIgnoreCase))
        {
            int lost = this.Region1RunUnbankedScrap;
            int lostShiny = this.Region1RunUnbankedShiny;
            this.ResetRegion1RunState();
            if (lost > 0 || lostShiny > 0)
                Game1.showGlobalMessage(ModEntry.T("airship.region1.run.unbanked-lost", new { scrap = lost, shiny = lostShiny }));
        }

        if (!e.NewLocation.NameOrUniqueName.Equals(Region1LocationName, StringComparison.OrdinalIgnoreCase))
            return;

        if (e.OldLocation is not null && TryGetRegion1RunRoomIndex(e.OldLocation, out _))
        {
            this.ClearRegion1MarkedMonsters(e.NewLocation);
            this.Region1RunActive = false;
            this.Region1RunCompleted = true;
            this.Region1RunStep = this.Region1RunTargetNodes;
            Game1.showGlobalMessage(ModEntry.T("airship.region1.run.complete"));
            return;
        }

        if (e.OldLocation?.NameOrUniqueName.Equals(Region1LocationName, StringComparison.OrdinalIgnoreCase) == true)
            return;

        this.PopulateRegion1(e.NewLocation);
    }

    /// <summary>TEST-only warp to the Forest Arcane Gate; runtime access only, no save/story mutation.</summary>
    public string DebugWarpToGate()
    {
        if (!Context.IsWorldReady)
            return "Arcane Gate TEST unavailable: load a save first.";

        GameLocation? forest = Game1.getLocationFromName(SkyDockLocationName);
        if (forest is null)
            return "Arcane Gate TEST couldn't find Forest.";

        this.TestGateAccessActive = true;
        Point dock = this.ResolveSkyDockTile();
        Point landing = ResolveForestGateLandingTile(forest, dock);
        this.WarpGraceUntilMs = Environment.TickCount64 + 850L;
        Game1.warpFarmer(forest.NameOrUniqueName, landing.X, landing.Y, 0);
        return $"Arcane Gate TEST: warped near Forest gate at ({dock.X},{dock.Y}). Runtime-only gate access is enabled until title reload; save/story unlock state was not changed.";
    }

    /// <summary>TEST-only direct deck access; does not unlock the Airship or alter story flags.</summary>
    public string DebugToggleDeck()
    {
        if (!Context.IsWorldReady)
            return "Airship TEST unavailable: load a save first.";

        if (Game1.currentLocation?.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase) == true)
        {
            this.WarpToSkyDockInterior();
            return "Airship TEST: returned to the Arcane Dock. Story/unlock/fare state was not changed.";
        }

        GameLocation? deck = this.EnsureDeckLocation();
        if (deck is null)
            return "Airship TEST couldn't create Cardcha_AirshipDeck.";

        Point arrival = ResolveDeckArrivalTile(deck);
        this.WarpGraceUntilMs = Environment.TickCount64 + 850L;
        Game1.warpFarmer(DeckLocationName, arrival.X, arrival.Y, 0);
        return "Airship TEST: warped to Cardcha_AirshipDeck. Run cardcha_test_airship again to return to the Arcane Dock. Story/unlock/fare state was not changed.";
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
        GameLocation? deckRoom = Game1.getLocationFromName(DeckLocationName);
        GameLocation? dockRoom = Game1.getLocationFromName(SkyDockInteriorLocationName);
        int deckFurniture = deckRoom?.furniture.Count(f => f.modData.ContainsKey(InteriorDecorMarkerKey)) ?? 0;
        int dockFurniture = dockRoom?.furniture.Count(f => f.modData.ContainsKey(InteriorDecorMarkerKey)) ?? 0;
        bool lostFoundPresent = false;
        if (dockRoom is not null)
        {
            Point lfTile = ResolveSkyDockLostFoundTile(dockRoom);
            lostFoundPresent = dockRoom.Objects.TryGetValue(new Vector2(lfTile.X, lfTile.Y), out StardewValley.Object? lf) && lf is Chest;
        }
        return $"GateTest={this.TestGateAccessActive} | " +
               $"AirshipFlybySeen={this.Save.Data.AirshipFlybySeen} | " +
               $"FlybyActive={this.FlybyActive} | " +
               $"Unlocked={this.Save.Data.AirshipUnlocked} | " +
               $"HighestRegion={this.Save.Data.AirshipHighestRegionUnlocked} | " +
               $"UnlockDay={this.Save.Data.AirshipUnlockedDay} | " +
               $"DeckExists={deckExists} | InteriorExists={interiorExists} | Region1Exists={region1Exists} | NativeDecor=Bridge:{deckFurniture},Dock:{dockFurniture},LostFound:{lostFoundPresent} | Flights={this.Save.Data.AirshipFlightsTaken} | FarePaid={this.Save.Data.AirshipTotalFarePaid}g | SkyDock={SkyDockLocationName}({dock.X},{dock.Y}) | " +
               $"ForestFarmWarp={farmWarp.X},{farmWarp.Y} | Upgrades=Engine:{this.Save.Data.AirshipEngineLevel}/3,Navigation:{this.Save.Data.AirshipNavigationLevel}/3,Hull:{this.Save.Data.AirshipHullLevel}/3,Reactor:{this.Save.Data.AirshipReactorLevel}/3 | CollisionEdits=NONE";
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
                this.Monitor.Log("Created Cardcha_SkyDockInterior as Cardcha-owned Arcane Dock layout.", LogLevel.Info);
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

    private bool EnsureRegion1RunRoomLocations()
    {
        if (!Context.IsWorldReady)
            return false;

        for (int i = 0; i < Region1RunRoomLocationNames.Length; i++)
        {
            if (Game1.getLocationFromName(Region1RunRoomLocationNames[i]) is not null)
                continue;

            try
            {
                Game1.locations.Add(new GameLocation(Region1RunRoomMapAssetNames[i], Region1RunRoomLocationNames[i]));
            }
            catch (Exception ex)
            {
                this.Monitor.Log(
                    $"Couldn't create Region I Hunt Run room {i + 1}; run generation aborted safely. {ex.GetType().Name}: {ex.Message}",
                    LogLevel.Error
                );
                return false;
            }
        }

        return true;
    }

    private void ResetRegion1RunState()
    {
        this.Region1RunRoute = Array.Empty<int>();
        this.Region1RunEncounters = Array.Empty<Region1RunEncounterType>();
        this.Region1RunRouteKinds = Array.Empty<Region1RunRouteKind>();
        this.Region1RunStep = -1;
        this.Region1RunSeed = 0;
        this.Region1RunTargetNodes = 0;
        this.Region1RunActive = false;
        this.Region1RunCompleted = false;
        this.Region1RunRouteChoicesPrepared = false;
        this.Region1RunLeftRoomIndex = -1;
        this.Region1RunRightRoomIndex = -1;
        this.Region1RunAwaitingBoon = false;
        this.Region1RunBoonChoices = Array.Empty<string>();
        this.Region1RunBoons.Clear();
        this.Region1RunRewardedSteps.Clear();
        this.Region1RunUnbankedScrap = 0;
        this.Region1RunUnbankedShiny = 0;
        this.Region1EliteAuraNextAtMs = 0;
        this.Region1RunRareRoomsSeen = 0;
    }

    private GameLocation? BeginRegion1HuntRun()
    {
        if (!this.EnsureRegion1RunRoomLocations())
            return null;

        this.Region1RunSeed = unchecked(
            (int)Game1.uniqueIDForThisGame
            + Game1.Date.TotalDays * 397
            + this.Save.Data.AirshipFlightsTaken * 7919
        );
        Random random = new(this.Region1RunSeed);
        this.Region1RunTargetNodes = random.Next(Region1RunMinNodes, Region1RunMaxNodes + 1);
        this.Region1RunRoute = Enumerable.Repeat(-1, this.Region1RunTargetNodes).ToArray();
        this.Region1RunEncounters = Enumerable.Repeat(Region1RunEncounterType.Combat, this.Region1RunTargetNodes).ToArray();
        this.Region1RunRouteKinds = Enumerable.Repeat(Region1RunRouteKind.Moss, this.Region1RunTargetNodes).ToArray();
        this.Region1RunRoute[0] = random.Next(Region1RunRoomLocationNames.Length);
        this.Region1RunEncounters[0] = Region1RunEncounterType.Combat;
        this.Region1RunStep = 0;
        this.Region1RunActive = true;
        this.Region1RunCompleted = false;
        this.Region1RunRouteChoicesPrepared = false;
        this.Region1RunRewardedSteps.Clear();
        this.Region1RunBoons.Clear();
        this.Region1RunUnbankedScrap = 0;
        this.Region1RunUnbankedShiny = 0;

        this.Monitor.Log(
            $"Region I Hunt Run 2.0 seed={this.Region1RunSeed}; targetNodes={this.Region1RunTargetNodes}; firstRoom={ModEntry.T(Region1RunRoomNameKeys[this.Region1RunRoute[0]])}. Branches generate after each clear.",
            LogLevel.Info
        );

        return Game1.getLocationFromName(Region1RunRoomLocationNames[this.Region1RunRoute[0]]);
    }

    private static bool TryGetRegion1RunRoomIndex(GameLocation location, out int index)
    {
        string name = location.NameOrUniqueName;
        for (int i = 0; i < Region1RunRoomLocationNames.Length; i++)
        {
            if (!name.Equals(Region1RunRoomLocationNames[i], StringComparison.OrdinalIgnoreCase))
                continue;

            index = i;
            return true;
        }

        index = -1;
        return false;
    }

    private void HandleRegion1RunRoomInteraction(ButtonPressedEventArgs e, GameLocation location)
    {
        Point action = GetActionTile();
        Point retreat = ResolveRegion1RunReturnTile(location);

        if (Touches(action, retreat) || PlayerIsNear(retreat))
        {
            this.Helper.Input.Suppress(e.Button);
            this.BankRegion1RunRewards("extract");
            this.ResetRegion1RunState();
            this.StartFlightCutscene(returning: true);
            return;
        }

        if (this.TryHandleRegion1LostCacheInteraction(e, location))
            return;

        int remaining = CountRegion1MarkedMonsters(location);
        if (remaining > 0)
        {
            Point[] blockedTargets = ResolveRegion1RunChoiceTiles(location);
            if (blockedTargets.Any(tile => Touches(action, tile)) || Touches(action, ResolveRegion1RunBossTile(location)))
            {
                this.Helper.Input.Suppress(e.Button);
                Game1.drawObjectDialogue(ModEntry.T("airship.region1.run.blocked", new { count = remaining }));
            }
            return;
        }

        this.HandleRegion1RunNodeCleared(location);

        if (this.Region1RunAwaitingBoon)
        {
            Point[] boonTiles = ResolveRegion1RunBoonTiles(location);
            for (int i = 0; i < boonTiles.Length && i < this.Region1RunBoonChoices.Length; i++)
            {
                if (!Touches(action, boonTiles[i]))
                    continue;
                this.Helper.Input.Suppress(e.Button);
                this.ChooseRegion1RunBoon(this.Region1RunBoonChoices[i]);
                return;
            }

            if (ResolveRegion1RunChoiceTiles(location).Any(tile => Touches(action, tile)))
            {
                this.Helper.Input.Suppress(e.Button);
                Game1.drawObjectDialogue(ModEntry.T("airship.region1.run.boon.choose-first"));
            }
            return;
        }

        int nodeNumber = this.Region1RunStep + 1;
        Point bossTile = ResolveRegion1RunBossTile(location);
        int owned = this.Save.Data.OwnedCards?.Count ?? 0;
        bool bossBranchVisible = nodeNumber >= Region1BossBranchMinNode;
        if (bossBranchVisible && Touches(action, bossTile))
        {
            this.Helper.Input.Suppress(e.Button);
            if (owned < Region1GateCardRequirement)
            {
                Game1.drawObjectDialogue(ModEntry.T("airship.region1.run.boss-locked", new { cards = owned, required = Region1GateCardRequirement }));
                return;
            }

            this.BankRegion1RunRewards("boss-branch");
            this.WarpRegion1RunToHub();
            return;
        }

        if (this.Region1RunStep >= this.Region1RunTargetNodes - 1)
        {
            if (Touches(action, bossTile))
            {
                this.Helper.Input.Suppress(e.Button);
                this.BankRegion1RunRewards("run-complete");
                this.WarpRegion1RunToHub();
            }
            return;
        }

        if (!this.Region1RunRouteChoicesPrepared)
            this.PrepareRegion1RunRouteChoices();

        Point[] routeTiles = ResolveRegion1RunChoiceTiles(location);
        if (routeTiles.Length >= 2 && Touches(action, routeTiles[0]))
        {
            this.Helper.Input.Suppress(e.Button);
            this.AdvanceRegion1HuntRun(this.Region1RunLeftRouteKind, this.Region1RunLeftRoomIndex);
            return;
        }
        if (routeTiles.Length >= 2 && Touches(action, routeTiles[1]))
        {
            this.Helper.Input.Suppress(e.Button);
            this.AdvanceRegion1HuntRun(this.Region1RunRightRouteKind, this.Region1RunRightRoomIndex);
        }
    }

    private void HandleRegion1RunNodeCleared(GameLocation location)
    {
        if (!this.Region1RunActive || this.Region1RunStep < 0 || this.Region1RunStep >= this.Region1RunTargetNodes)
            return;
        if (!this.Region1RunRewardedSteps.Add(this.Region1RunStep))
            return;

        int nodeNumber = this.Region1RunStep + 1;
        Region1RunRouteKind routeKind = this.Region1RunRouteKinds[this.Region1RunStep];
        Region1RunEncounterType encounter = this.Region1RunEncounters[this.Region1RunStep];
        Region1DailyMutation mutation = this.ResolveRegion1DailyMutation();

        if (encounter is Region1RunEncounterType.LostCache or Region1RunEncounterType.Moonwell or Region1RunEncounterType.AncientEcho)
            this.Region1RunRareRoomsSeen++;

        switch (encounter)
        {
            case Region1RunEncounterType.LostCache:
                this.Region1RunUnbankedScrap += 4;
                this.Region1RunUnbankedShiny += 1;
                break;
            case Region1RunEncounterType.Moonwell:
                Game1.player.health = Math.Min(Game1.player.maxHealth, Game1.player.health + Math.Max(12, (int)Math.Round(Game1.player.maxHealth * 0.30d)));
                this.BankRegion1RunRewards("moonwell");
                break;
            case Region1RunEncounterType.AncientEcho:
                this.Region1RunUnbankedScrap += 3;
                this.Region1RunUnbankedShiny += 1;
                break;
        }

        switch (mutation)
        {
            case Region1DailyMutation.Overgrown:
                this.Region1RunUnbankedScrap++;
                break;
            case Region1DailyMutation.BriarBloom:
                if (encounter is Region1RunEncounterType.Elite or Region1RunEncounterType.RootNest or Region1RunEncounterType.AncientEcho)
                    this.Region1RunUnbankedScrap++;
                break;
            case Region1DailyMutation.MoonlitGrove:
                Random moonlit = new(unchecked(this.Region1RunSeed + nodeNumber * 2147483 + Game1.Date.TotalDays));
                if (moonlit.NextDouble() < 0.25d)
                    this.Region1RunUnbankedShiny++;
                break;
            case Region1DailyMutation.ChaoticResonance:
                if (encounter is Region1RunEncounterType.Elite or Region1RunEncounterType.AncientEcho)
                    this.Region1RunUnbankedScrap++;
                break;
        }

        if (routeKind is Region1RunRouteKind.Briar or Region1RunRouteKind.Ancient)
            this.Region1RunUnbankedScrap++;
        if (this.Region1RunBoons.Contains("scrap_compass"))
            this.Region1RunUnbankedScrap++;
        if (this.Region1RunBoons.Contains("hunters_edge") && encounter is Region1RunEncounterType.Elite or Region1RunEncounterType.RootNest)
            this.Region1RunUnbankedScrap++;
        if (this.Region1RunBoons.Contains("verdant_recovery"))
            Game1.player.health = Math.Min(Game1.player.maxHealth, Game1.player.health + 6);
        if (this.Region1RunBoons.Contains("moss_ward") && encounter is Region1RunEncounterType.Elite or Region1RunEncounterType.RootNest)
            Game1.player.health = Math.Min(Game1.player.maxHealth, Game1.player.health + 12);
        if (this.Region1RunBoons.Contains("fortune_bud"))
        {
            Random fortune = new(unchecked(this.Region1RunSeed + nodeNumber * 982451653));
            if (fortune.NextDouble() < 0.20d)
                this.Region1RunUnbankedShiny++;
        }

        if (nodeNumber == Region1CheckpointNodeA || nodeNumber == Region1CheckpointNodeB)
        {
            if (this.Region1RunBoons.Contains("deep_roots"))
                Game1.player.health = Math.Min(Game1.player.maxHealth, Game1.player.health + 20);
            this.BankRegion1RunRewards($"checkpoint-{nodeNumber}");
            Game1.playSound("questcomplete");
            Game1.showGlobalMessage(ModEntry.T("airship.region1.run.checkpoint", new { node = nodeNumber }));
        }

        bool boonMilestone = nodeNumber == 2 || nodeNumber == 5 || nodeNumber == 8
            || (mutation == Region1DailyMutation.ChaoticResonance && (nodeNumber == 4 || nodeNumber == 7));
        if (boonMilestone || encounter == Region1RunEncounterType.Shrine)
            this.PrepareRegion1RunBoonChoices();

        if (!this.Region1RunAwaitingBoon && this.Region1RunStep < this.Region1RunTargetNodes - 1)
            this.PrepareRegion1RunRouteChoices();

        Game1.playSound("discoverMineral");
    }

    private void PrepareRegion1RunBoonChoices()
    {
        string[] pool =
        {
            "verdant_recovery",
            "scrap_compass",
            "deep_roots",
            "fortune_bud",
            "hunters_edge",
            "moss_ward"
        };
        string[] available = pool.Where(id => !this.Region1RunBoons.Contains(id)).ToArray();
        if (available.Length < 3)
        {
            this.Region1RunUnbankedScrap += 2;
            this.Region1RunAwaitingBoon = false;
            this.Region1RunBoonChoices = Array.Empty<string>();
            return;
        }

        Random random = new(unchecked(this.Region1RunSeed + (this.Region1RunStep + 1) * 65537 + this.Region1RunBoons.Count * 31337));
        this.Region1RunBoonChoices = available.OrderBy(_ => random.Next()).Take(3).ToArray();
        this.Region1RunAwaitingBoon = true;
        this.Region1RunRouteChoicesPrepared = false;
        Game1.showGlobalMessage(ModEntry.T("airship.region1.run.boon.ready"));
    }

    private void ChooseRegion1RunBoon(string boonId)
    {
        if (!this.Region1RunAwaitingBoon || !this.Region1RunBoonChoices.Contains(boonId, StringComparer.OrdinalIgnoreCase))
            return;
        this.Region1RunBoons.Add(boonId);
        this.Region1RunAwaitingBoon = false;
        this.Region1RunBoonChoices = Array.Empty<string>();
        Game1.playSound("yoba");
        Game1.showGlobalMessage(ModEntry.T("airship.region1.run.boon.chosen", new { boon = ModEntry.T($"airship.region1.run.boon.{boonId}.name") }));
        if (this.Region1RunStep < this.Region1RunTargetNodes - 1)
            this.PrepareRegion1RunRouteChoices();
    }

    private void PrepareRegion1RunRouteChoices()
    {
        if (!this.Region1RunActive || this.Region1RunStep >= this.Region1RunTargetNodes - 1)
        {
            this.Region1RunRouteChoicesPrepared = false;
            return;
        }

        Random random = new(unchecked(this.Region1RunSeed + (this.Region1RunStep + 1) * 104729));
        Region1RunRouteKind[] kinds = Enum.GetValues<Region1RunRouteKind>().OrderBy(_ => random.Next()).Take(2).ToArray();
        this.Region1RunLeftRouteKind = kinds[0];
        this.Region1RunRightRouteKind = kinds[1];
        int currentRoom = this.Region1RunRoute[this.Region1RunStep];
        this.Region1RunLeftRoomIndex = PickNextRegion1Room(random, currentRoom, -1);
        this.Region1RunRightRoomIndex = PickNextRegion1Room(random, currentRoom, this.Region1RunLeftRoomIndex);
        this.Region1RunRouteChoicesPrepared = true;
    }

    private static int PickNextRegion1Room(Random random, int currentRoom, int excludedRoom)
    {
        int[] candidates = Enumerable.Range(0, Region1RunRoomLocationNames.Length)
            .Where(i => i != currentRoom && i != excludedRoom)
            .OrderBy(_ => random.Next())
            .ToArray();
        return candidates.Length == 0 ? Math.Max(0, (currentRoom + 1) % Region1RunRoomLocationNames.Length) : candidates[0];
    }

    private Region1RunEncounterType RollRegion1Encounter(Region1RunRouteKind route, int nodeIndex)
    {
        Region1DailyMutation mutation = this.ResolveRegion1DailyMutation();
        Random random = new(unchecked(this.Region1RunSeed + (nodeIndex + 1) * 32452843 + (int)route * 49999));

        if (nodeIndex >= 3)
        {
            int rareChance = mutation switch
            {
                Region1DailyMutation.ChaoticResonance => 18,
                Region1DailyMutation.MoonlitGrove => 16,
                _ => 11
            };
            if (random.Next(100) < rareChance)
            {
                int rare = random.Next(100);
                return route switch
                {
                    Region1RunRouteKind.Ancient => rare < 45 ? Region1RunEncounterType.LostCache
                        : rare < 76 ? Region1RunEncounterType.Moonwell
                        : Region1RunEncounterType.AncientEcho,
                    Region1RunRouteKind.Briar => rare < 32 ? Region1RunEncounterType.LostCache
                        : rare < 50 ? Region1RunEncounterType.Moonwell
                        : Region1RunEncounterType.AncientEcho,
                    _ => rare < 44 ? Region1RunEncounterType.Moonwell
                        : rare < 82 ? Region1RunEncounterType.LostCache
                        : Region1RunEncounterType.AncientEcho,
                };
            }
        }

        int roll = random.Next(100);
        return route switch
        {
            Region1RunRouteKind.Moss => roll < 55 ? Region1RunEncounterType.Combat
                : roll < 78 ? Region1RunEncounterType.Ambush
                : roll < 90 ? Region1RunEncounterType.RootNest
                : Region1RunEncounterType.Shrine,
            Region1RunRouteKind.Briar => roll < 38 ? Region1RunEncounterType.Elite
                : roll < 68 ? Region1RunEncounterType.RootNest
                : Region1RunEncounterType.Ambush,
            _ => roll < 34 ? Region1RunEncounterType.Shrine
                : roll < 58 ? Region1RunEncounterType.RootNest
                : roll < 78 ? Region1RunEncounterType.Elite
                : Region1RunEncounterType.Combat,
        };
    }

    private void AdvanceRegion1HuntRun(Region1RunRouteKind routeKind, int roomIndex)
    {
        if (!this.Region1RunActive || this.Region1RunStep < 0 || this.Region1RunStep >= this.Region1RunTargetNodes - 1)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region1.run.unstable"));
            return;
        }

        int nextStep = this.Region1RunStep + 1;
        this.Region1RunRoute[nextStep] = Math.Clamp(roomIndex, 0, Region1RunRoomLocationNames.Length - 1);
        this.Region1RunRouteKinds[nextStep] = routeKind;
        this.Region1RunEncounters[nextStep] = this.RollRegion1Encounter(routeKind, nextStep);
        this.Region1RunStep = nextStep;
        this.Region1RunRouteChoicesPrepared = false;
        this.Region1RunAwaitingBoon = false;
        this.Region1RunBoonChoices = Array.Empty<string>();

        GameLocation? next = Game1.getLocationFromName(Region1RunRoomLocationNames[this.Region1RunRoute[nextStep]]);
        if (next is null)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region1.run.unstable"));
            return;
        }

        Point nextArrival = ResolveRegion1RunArrivalTile(next);
        this.WarpGraceUntilMs = Environment.TickCount64 + 650L;
        Game1.playSound("wand");
        Game1.warpFarmer(next.NameOrUniqueName, nextArrival.X, nextArrival.Y, 0);
    }

    private void WarpRegion1RunToHub()
    {
        GameLocation? hub = this.EnsureRegion1Location();
        if (hub is null)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region1.unavailable"));
            return;
        }

        Point arrival = ResolveRegion1ArrivalTile(hub);
        this.WarpGraceUntilMs = Environment.TickCount64 + 650L;
        Game1.playSound("discoverMineral");
        Game1.warpFarmer(Region1LocationName, arrival.X, arrival.Y, 0);
    }

    private void PopulateRegion1RunRoom(GameLocation location, int roomIndex)
    {
        this.ClearRegion1MarkedMonsters(location);
        this.ClearRegion1LostCacheObject(location);
        this.Region1EliteAuraNextAtMs = 0;
        if (!this.Region1RunActive || this.Region1RunStep < 0 || this.Region1RunStep >= this.Region1RunEncounters.Length)
            return;

        Region1RunEncounterType encounter = this.Region1RunEncounters[this.Region1RunStep];
        if (encounter is Region1RunEncounterType.Shrine or Region1RunEncounterType.LostCache or Region1RunEncounterType.Moonwell)
        {
            if (encounter == Region1RunEncounterType.LostCache)
                this.EnsureRegion1LostCacheChest(location);
            this.Monitor.Log($"Region I Hunt Run node {this.Region1RunStep + 1}: {encounter}, no combat spawn.", LogLevel.Trace);
            return;
        }

        Point[][] roomCandidates =
        {
            new[] { new Point(5,5), new Point(9,5), new Point(18,5), new Point(22,5), new Point(6,9), new Point(11,9), new Point(17,9), new Point(22,9), new Point(5,13), new Point(10,13), new Point(18,13), new Point(23,13), new Point(8,16), new Point(19,16) },
            new[] { new Point(5,4), new Point(10,5), new Point(17,4), new Point(22,5), new Point(7,9), new Point(11,10), new Point(18,9), new Point(23,10), new Point(5,15), new Point(10,14), new Point(18,15), new Point(22,14) },
            new[] { new Point(4,4), new Point(9,5), new Point(18,5), new Point(23,4), new Point(6,10), new Point(11,10), new Point(17,10), new Point(22,10), new Point(4,15), new Point(9,14), new Point(18,14), new Point(23,15) },
            new[] { new Point(5,4), new Point(10,4), new Point(18,5), new Point(22,5), new Point(6,9), new Point(12,9), new Point(17,10), new Point(22,10), new Point(5,14), new Point(10,15), new Point(18,14), new Point(23,15) },
            new[] { new Point(5,5), new Point(9,6), new Point(18,6), new Point(22,5), new Point(5,10), new Point(11,9), new Point(17,11), new Point(22,10), new Point(6,15), new Point(10,14), new Point(18,14), new Point(22,15) },
            new[] { new Point(5,5), new Point(10,5), new Point(18,5), new Point(23,5), new Point(6,9), new Point(10,11), new Point(18,9), new Point(22,11), new Point(5,15), new Point(10,15), new Point(18,15), new Point(23,15) },
        };

        int encounterSeed = unchecked(this.Region1RunSeed + roomIndex * 104729 + Math.Max(0, this.Region1RunStep) * 8191);
        Random random = new(encounterSeed);
        Point[] shuffled = roomCandidates[roomIndex].OrderBy(_ => random.Next()).ToArray();
        bool eliteEncounter = encounter is Region1RunEncounterType.Elite or Region1RunEncounterType.AncientEcho;
        Region1EliteAffix eliteAffix = eliteEncounter ? this.RollRegion1EliteAffix(this.Region1RunStep) : Region1EliteAffix.ThornAura;
        int targetCount = encounter switch
        {
            Region1RunEncounterType.Combat => random.Next(5, 8),
            Region1RunEncounterType.Ambush => random.Next(8, 11),
            Region1RunEncounterType.Elite => 4,
            Region1RunEncounterType.RootNest => 6,
            Region1RunEncounterType.AncientEcho => 3,
            _ => 0
        };
        if (eliteEncounter && eliteAffix == Region1EliteAffix.Infested)
            targetCount += 2;
        if (this.ResolveRegion1DailyMutation() == Region1DailyMutation.CalmGrove && targetCount > 3)
            targetCount--;

        int spawned = 0;
        foreach (Point tile in shuffled)
        {
            if (spawned >= targetCount)
                break;

            Vector2 tileVector = new(tile.X, tile.Y);
            try
            {
                if (location.IsTileBlockedBy(tileVector) || location.Objects.ContainsKey(tileVector))
                    continue;
            }
            catch
            {
                continue;
            }

            Monster monster;
            if (eliteEncounter && spawned == 0)
            {
                int baseHp = 210 + this.Region1RunStep * 16;
                if (encounter == Region1RunEncounterType.AncientEcho)
                    baseHp = (int)Math.Round(baseHp * 1.20d);
                GreenSlime elite = new(tileVector * 64f, 0) { MaxHealth = baseHp, Speed = 3 };
                elite.Health = elite.MaxHealth;
                elite.modData[Region1EliteMarkerKey] = "1";
                elite.modData[Region1EliteAffixMarkerKey] = eliteAffix.ToString();
                this.ApplyRegion1EliteAffix(elite, eliteAffix);
                monster = elite;
            }
            else if (encounter == Region1RunEncounterType.RootNest && spawned < 3)
            {
                GreenSlime nest = new(tileVector * 64f, 0) { MaxHealth = 60 + this.Region1RunStep * 8, Speed = 0 };
                nest.Health = nest.MaxHealth;
                nest.modData[Region1RootNestMarkerKey] = "1";
                monster = nest;
            }
            else
            {
                monster = CreateRegion1RunMonster(roomIndex, random.Next(100), tileVector * 64f);
                if (eliteEncounter && eliteAffix == Region1EliteAffix.Resonant)
                {
                    monster.Speed += 1;
                    monster.MaxHealth = Math.Max(1, (int)Math.Round(monster.MaxHealth * 1.15d));
                    monster.Health = monster.MaxHealth;
                }
            }

            monster.modData[Region1MonsterMarkerKey] = "huntrun2";
            this.ApplyRegion1DailyMutationToMonster(monster);
            location.characters.Add(monster);
            spawned++;
        }

        this.Monitor.Log(
            $"Region I Hunt Run 2.0 node {this.Region1RunStep + 1}/{this.Region1RunTargetNodes}: room={roomIndex + 1}, encounter={encounter}, eliteAffix={(eliteEncounter ? eliteAffix : "none")}, mutation={this.ResolveRegion1DailyMutation()}, spawned={spawned}.",
            LogLevel.Trace
        );
    }

    private Region1EliteAffix RollRegion1EliteAffix(int nodeIndex)
    {
        Region1EliteAffix[] pool = Enum.GetValues<Region1EliteAffix>();
        int seed = unchecked(this.Region1RunSeed + (nodeIndex + 1) * 67867967 + Game1.Date.TotalDays * 97);
        return pool[new Random(seed).Next(pool.Length)];
    }

    private void ApplyRegion1EliteAffix(Monster elite, Region1EliteAffix affix)
    {
        switch (affix)
        {
            case Region1EliteAffix.ThornAura:
                elite.MaxHealth = Math.Max(1, (int)Math.Round(elite.MaxHealth * 1.10d));
                break;
            case Region1EliteAffix.Swift:
                elite.Speed += 2;
                break;
            case Region1EliteAffix.Regrowth:
                elite.MaxHealth = Math.Max(1, (int)Math.Round(elite.MaxHealth * 1.15d));
                break;
            case Region1EliteAffix.Bulwark:
                elite.MaxHealth = Math.Max(1, (int)Math.Round(elite.MaxHealth * 1.60d));
                elite.Speed = Math.Max(1, elite.Speed - 1);
                break;
            case Region1EliteAffix.Infested:
                elite.MaxHealth = Math.Max(1, (int)Math.Round(elite.MaxHealth * 1.15d));
                break;
            case Region1EliteAffix.Resonant:
                elite.MaxHealth = Math.Max(1, (int)Math.Round(elite.MaxHealth * 1.25d));
                break;
        }
        elite.Health = elite.MaxHealth;
    }

    private void ApplyRegion1DailyMutationToMonster(Monster monster)
    {
        Region1DailyMutation mutation = this.ResolveRegion1DailyMutation();
        bool rootNest = monster.modData.ContainsKey(Region1RootNestMarkerKey);
        bool elite = monster.modData.ContainsKey(Region1EliteMarkerKey);
        double hpScale = mutation switch
        {
            Region1DailyMutation.CalmGrove => 0.90d,
            Region1DailyMutation.BriarBloom when elite || rootNest => 1.20d,
            Region1DailyMutation.Overgrown => 1.15d,
            Region1DailyMutation.ChaoticResonance => 1.10d,
            _ => 1.00d
        };
        monster.MaxHealth = Math.Max(1, (int)Math.Round(monster.MaxHealth * hpScale));
        monster.Health = monster.MaxHealth;

        if (!rootNest && mutation == Region1DailyMutation.MoonlitGrove && monster is Bat)
            monster.Speed += 1;
        if (!rootNest && mutation == Region1DailyMutation.ChaoticResonance)
            monster.Speed += 1;
    }

    private void UpdateRegion1EliteAffixes(GameLocation room, long now)
    {
        foreach (Monster elite in room.characters.OfType<Monster>().Where(m => m.Health > 0 && m.modData.ContainsKey(Region1EliteMarkerKey)))
        {
            if (!elite.modData.TryGetValue(Region1EliteAffixMarkerKey, out string? raw)
                || !Enum.TryParse(raw, ignoreCase: true, out Region1EliteAffix affix))
            {
                continue;
            }

            if (affix == Region1EliteAffix.Regrowth && elite.Health < elite.MaxHealth)
            {
                int heal = Math.Max(2, elite.MaxHealth / 40);
                elite.Health = Math.Min(elite.MaxHealth, elite.Health + heal);
            }

            if (affix == Region1EliteAffix.ThornAura && now >= this.Region1EliteAuraNextAtMs)
            {
                Vector2 eliteCenter = elite.Position + new Vector2(32f, 32f);
                Vector2 playerCenter = Game1.player.Position + new Vector2(32f, 32f);
                if (Vector2.Distance(eliteCenter, playerCenter) <= 112f)
                {
                    this.Region1EliteAuraNextAtMs = now + 1200L;
                    Game1.player.takeDamage(3, false, elite);
                    Game1.playSound("leafrustle");
                }
            }
        }
    }

    private Region1DailyMutation ResolveRegion1DailyMutation()
    {
        Region1DailyMutation[] values = Enum.GetValues<Region1DailyMutation>();
        int seed = unchecked((int)Game1.uniqueIDForThisGame + Game1.Date.TotalDays * 1009 + 17041);
        int index = (int)((uint)seed % (uint)values.Length);
        return values[index];
    }

    private static string MutationKey(Region1DailyMutation mutation) => mutation switch
    {
        Region1DailyMutation.CalmGrove => "calm_grove",
        Region1DailyMutation.BriarBloom => "briar_bloom",
        Region1DailyMutation.MoonlitGrove => "moonlit_grove",
        Region1DailyMutation.Overgrown => "overgrown",
        _ => "chaotic_resonance"
    };

    private static string EliteAffixKey(Region1EliteAffix affix) => affix switch
    {
        Region1EliteAffix.ThornAura => "thorn_aura",
        Region1EliteAffix.Swift => "swift",
        Region1EliteAffix.Regrowth => "regrowth",
        Region1EliteAffix.Bulwark => "bulwark",
        Region1EliteAffix.Infested => "infested",
        _ => "resonant"
    };

    private static Monster CreateRegion1RunMonster(int roomIndex, int roll, Vector2 position)
        => roomIndex switch
        {
            0 => roll < 72 ? (Monster)new GreenSlime(position, 0) : new Bug(position, 0),
            1 => roll < 55 ? (Monster)new GreenSlime(position, 0) : new Bat(position),
            2 => roll < 52 ? (Monster)new Bug(position, 0) : new Bat(position),
            3 => roll < 45 ? (Monster)new GreenSlime(position, 0) : roll < 78 ? new Bug(position, 0) : new Bat(position),
            4 => roll < 68 ? (Monster)new Bat(position) : new GreenSlime(position, 0),
            _ => roll < 34 ? (Monster)new GreenSlime(position, 0) : roll < 67 ? new Bat(position) : new Bug(position, 0),
        };

    private void BankRegion1RunRewards(string reason)
    {
        int scrap = Math.Max(0, this.Region1RunUnbankedScrap);
        int shiny = Math.Max(0, this.Region1RunUnbankedShiny);
        if (scrap <= 0 && shiny <= 0)
            return;

        this.Save.Data.CardboardScraps += scrap;
        this.Save.Data.ShinyScraps += shiny;
        this.Region1RunUnbankedScrap = 0;
        this.Region1RunUnbankedShiny = 0;
        this.Save.Save();
        Game1.showGlobalMessage(ModEntry.T("airship.region1.run.bank", new { scrap, shiny, reason }));
    }

    public string DescribeHuntRun2()
    {
        if (!Context.IsWorldReady)
            return "HuntRun2=<no save>";
        string encounter = this.Region1RunStep >= 0 && this.Region1RunStep < this.Region1RunEncounters.Length
            ? this.Region1RunEncounters[this.Region1RunStep].ToString()
            : "none";
        string route = this.Region1RunStep >= 0 && this.Region1RunStep < this.Region1RunRouteKinds.Length
            ? this.Region1RunRouteKinds[this.Region1RunStep].ToString()
            : "none";
        string affix = "none";
        Monster? elite = Game1.currentLocation?.characters.OfType<Monster>().FirstOrDefault(m => m.Health > 0 && m.modData.ContainsKey(Region1EliteMarkerKey));
        if (elite is not null && elite.modData.TryGetValue(Region1EliteAffixMarkerKey, out string? currentAffix))
            affix = currentAffix;
        Region1DailyMutation mutation = this.ResolveRegion1DailyMutation();
        return $"HuntRun2 Active={this.Region1RunActive} | Node={Math.Max(0, this.Region1RunStep + 1)}/{this.Region1RunTargetNodes} | " +
               $"Encounter={encounter} | Route={route} | Mutation={mutation} | EliteAffix={affix} | RareSeen={this.Region1RunRareRoomsSeen} | " +
               $"Boons=[{string.Join(',', this.Region1RunBoons)}] | AwaitingBoon={this.Region1RunAwaitingBoon} | " +
               $"Unbanked={this.Region1RunUnbankedScrap} Scrap + {this.Region1RunUnbankedShiny} Shiny | " +
               $"BossBranch={(this.Region1RunStep + 1 >= Region1BossBranchMinNode)} | Seed={this.Region1RunSeed}";
    }

    public string DescribeHuntAdvanced()
    {
        if (!Context.IsWorldReady)
            return "HuntRunAdvanced=<no save>";
        Region1DailyMutation mutation = this.ResolveRegion1DailyMutation();
        return $"DailyMutation={mutation} | Name={ModEntry.T($"airship.region1.run.mutation.{MutationKey(mutation)}.name")} | " +
               $"RareRoomsSeen={this.Region1RunRareRoomsSeen} | Run={this.DescribeHuntRun2()}";
    }

    public string DebugClearHuntRunNode()
    {
        if (!Context.IsWorldReady || !this.Region1RunActive || Game1.currentLocation is null || !TryGetRegion1RunRoomIndex(Game1.currentLocation, out _))
            return "Hunt Run 2.0 TEST: enter a Region I run room first.";
        this.ClearRegion1MarkedMonsters(Game1.currentLocation);
        this.HandleRegion1RunNodeCleared(Game1.currentLocation);
        this.ClearRegion1LostCacheObject(Game1.currentLocation);
        return $"TEST: cleared node {this.Region1RunStep + 1}/{this.Region1RunTargetNodes}. {this.DescribeHuntRun2()}";
    }

    private void DrawRegion1HuntRun2Overlay(SpriteBatch batch, GameLocation room)
    {
        if (!this.Region1RunActive || this.Region1RunStep < 0 || this.Region1RunStep >= this.Region1RunTargetNodes)
            return;

        Region1DailyMutation mutation = this.ResolveRegion1DailyMutation();
        string mutationLabel = "MUTATION • " + ModEntry.T($"airship.region1.run.mutation.{MutationKey(mutation)}.name");
        batch.DrawString(Game1.smallFont, mutationLabel, new Vector2(24f, 78f), new Color(208, 235, 184));

        foreach (Monster elite in room.characters.OfType<Monster>().Where(m => m.Health > 0 && m.modData.ContainsKey(Region1EliteMarkerKey)))
        {
            if (!elite.modData.TryGetValue(Region1EliteAffixMarkerKey, out string? raw)
                || !Enum.TryParse(raw, ignoreCase: true, out Region1EliteAffix affix))
            {
                continue;
            }
            Point tile = new((int)(elite.Position.X / 64f), (int)(elite.Position.Y / 64f));
            DrawRunChoiceMarker(batch, tile, EliteAffixColor(affix), ModEntry.T($"airship.region1.run.affix.{EliteAffixKey(affix)}.name"));
        }

        Region1RunEncounterType currentEncounter = this.Region1RunEncounters[this.Region1RunStep];
        if (currentEncounter == Region1RunEncounterType.LostCache)
        {
            // 0668C: the cache is a physical chest. No floating name or action hint before interaction.
            if (!this.Region1RunRewardedSteps.Contains(this.Region1RunStep))
                return;
        }
        else if (currentEncounter is Region1RunEncounterType.Moonwell or Region1RunEncounterType.AncientEcho)
        {
            Point rareTile = ResolveRegion1RunRareTile(room);
            DrawRunChoiceMarker(batch, rareTile, RareEncounterColor(currentEncounter), ModEntry.T($"airship.region1.run.rare.{currentEncounter.ToString().ToLowerInvariant()}.name"));
        }

        foreach (Monster nest in room.characters.OfType<Monster>().Where(m => m.Health > 0 && m.modData.ContainsKey(Region1RootNestMarkerKey)))
        {
            Vector2 center = Game1.GlobalToLocal(Game1.viewport, nest.Position + new Vector2(32f, 32f));
            int pulse = 34 + (int)(5f * Math.Sin(Environment.TickCount64 / 170d));
            batch.Draw(Game1.staminaRect, new Rectangle((int)center.X - pulse, (int)center.Y - 3, pulse * 2, 6), new Color(111, 199, 83) * 0.55f);
            batch.Draw(Game1.staminaRect, new Rectangle((int)center.X - 3, (int)center.Y - pulse, 6, pulse * 2), new Color(111, 199, 83) * 0.55f);
        }

        if (CountRegion1MarkedMonsters(room) > 0)
            return;

        if (this.Region1RunAwaitingBoon)
        {
            Point[] boonTiles = ResolveRegion1RunBoonTiles(room);
            for (int i = 0; i < boonTiles.Length && i < this.Region1RunBoonChoices.Length; i++)
                DrawRunChoiceMarker(batch, boonTiles[i], new Color(154, 228, 124), ModEntry.T($"airship.region1.run.boon.{this.Region1RunBoonChoices[i]}.name"));
            return;
        }

        int nodeNumber = this.Region1RunStep + 1;
        if (this.Region1RunStep < this.Region1RunTargetNodes - 1)
        {
            if (!this.Region1RunRouteChoicesPrepared)
                this.PrepareRegion1RunRouteChoices();
            Point[] routes = ResolveRegion1RunChoiceTiles(room);
            DrawRunChoiceMarker(batch, routes[0], RouteColor(this.Region1RunLeftRouteKind), ModEntry.T($"airship.region1.run.route.{this.Region1RunLeftRouteKind.ToString().ToLowerInvariant()}"));
            DrawRunChoiceMarker(batch, routes[1], RouteColor(this.Region1RunRightRouteKind), ModEntry.T($"airship.region1.run.route.{this.Region1RunRightRouteKind.ToString().ToLowerInvariant()}"));
        }

        Point boss = ResolveRegion1RunBossTile(room);
        if (nodeNumber >= Region1BossBranchMinNode)
        {
            int owned = this.Save.Data.OwnedCards?.Count ?? 0;
            string label = owned >= Region1GateCardRequirement
                ? ModEntry.T("airship.region1.run.route.boss")
                : ModEntry.T("airship.region1.run.route.boss-locked-short", new { cards = owned, required = Region1GateCardRequirement });
            DrawRunChoiceMarker(batch, boss, new Color(214, 194, 92), label);
        }
        else if (this.Region1RunStep >= this.Region1RunTargetNodes - 1)
        {
            DrawRunChoiceMarker(batch, boss, new Color(158, 211, 178), ModEntry.T("airship.region1.run.route.finish"));
        }
    }

    private bool CurrentRegion1NodeNeedsManualInteraction()
    {
        if (!this.Region1RunActive || this.Region1RunStep < 0 || this.Region1RunStep >= this.Region1RunEncounters.Length)
            return false;
        return this.Region1RunEncounters[this.Region1RunStep] == Region1RunEncounterType.LostCache
            && !this.Region1RunRewardedSteps.Contains(this.Region1RunStep);
    }

    private bool TryHandleRegion1LostCacheInteraction(ButtonPressedEventArgs e, GameLocation location)
    {
        if (!this.CurrentRegion1NodeNeedsManualInteraction())
            return false;

        Point cacheTile = ResolveRegion1RunRareTile(location);
        Point actionTile = GetActionTile();
        Point cursorTile = new((int)e.Cursor.GrabTile.X, (int)e.Cursor.GrabTile.Y);
        bool mouseDirect = e.Button == SButton.MouseRight && Touches(cursorTile, cacheTile);
        if (!Touches(actionTile, cacheTile) && !mouseDirect)
            return false;

        this.Helper.Input.Suppress(e.Button);
        Game1.playSound("openBox");
        this.HandleRegion1RunNodeCleared(location);
        this.ClearRegion1LostCacheObject(location);
        Game1.drawObjectDialogue(ModEntry.T("airship.region1.run.rare.lostcache.opened"));
        return true;
    }

    private static Point ResolveRegion1RunRareTile(GameLocation room)
    {
        int width = room.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 28;
        int height = room.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 20;
        return new Point(width / 2, Math.Max(5, height / 2));
    }

    private void EnsureRegion1LostCacheChest(GameLocation room)
    {
        Point tile = ResolveRegion1RunRareTile(room);
        Vector2 key = new(tile.X, tile.Y);
        if (room.Objects.TryGetValue(key, out StardewValley.Object? existing))
        {
            if (existing is Chest && existing.modData.ContainsKey(Region1LostCacheMarkerKey))
                return;
            return;
        }

        Chest cache = new(true);
        cache.modData[Region1LostCacheMarkerKey] = "0668C";
        room.setObject(key, cache);
    }

    private void ClearRegion1LostCacheObject(GameLocation room)
    {
        Point tile = ResolveRegion1RunRareTile(room);
        Vector2 key = new(tile.X, tile.Y);
        if (room.Objects.TryGetValue(key, out StardewValley.Object? existing)
            && existing.modData.ContainsKey(Region1LostCacheMarkerKey))
        {
            room.Objects.Remove(key);
        }
    }

    private static Color RouteColor(Region1RunRouteKind route) => route switch
    {
        Region1RunRouteKind.Moss => new Color(113, 198, 118),
        Region1RunRouteKind.Briar => new Color(202, 117, 104),
        _ => new Color(139, 177, 224)
    };


    private static Color EliteAffixColor(Region1EliteAffix affix) => affix switch
    {
        Region1EliteAffix.ThornAura => new Color(211, 104, 112),
        Region1EliteAffix.Swift => new Color(235, 218, 108),
        Region1EliteAffix.Regrowth => new Color(107, 220, 129),
        Region1EliteAffix.Bulwark => new Color(145, 169, 184),
        Region1EliteAffix.Infested => new Color(191, 131, 215),
        _ => new Color(95, 210, 202)
    };

    private static Color RareEncounterColor(Region1RunEncounterType encounter) => encounter switch
    {
        Region1RunEncounterType.LostCache => new Color(232, 199, 94),
        Region1RunEncounterType.Moonwell => new Color(116, 181, 236),
        _ => new Color(184, 125, 229)
    };

    private static void DrawRunChoiceMarker(SpriteBatch batch, Point tile, Color color, string label)
    {
        Vector2 world = new(tile.X * 64f + 32f, tile.Y * 64f + 32f);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
        float pulse = 0.82f + 0.12f * (float)Math.Sin(Environment.TickCount64 / 180d + tile.X);
        int size = (int)(24f * pulse);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - size, (int)local.Y - 3, size * 2, 6), color * 0.72f);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 3, (int)local.Y - size, 6, size * 2), color * 0.72f);
        Vector2 textSize = Game1.smallFont.MeasureString(label);
        batch.DrawString(Game1.smallFont, label, new Vector2(local.X - textSize.X / 2f, local.Y + 30f), Color.White);
    }

    private static Point[] ResolveRegion1RunChoiceTiles(GameLocation room)
    {
        int width = room.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 28;
        int center = width / 2;
        return new[] { new Point(Math.Max(2, center - 5), 2), new Point(Math.Min(width - 3, center + 5), 2) };
    }

    private static Point[] ResolveRegion1RunBoonTiles(GameLocation room)
    {
        int width = room.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 28;
        int center = width / 2;
        return new[] { new Point(Math.Max(3, center - 7), 5), new Point(center, 5), new Point(Math.Min(width - 4, center + 7), 5) };
    }

    private static Point ResolveRegion1RunBossTile(GameLocation room)
    {
        int width = room.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 28;
        return new Point(width / 2, 2);
    }

    private void ClearRegion1MarkedMonsters(GameLocation location)
    {
        foreach (NPC actor in location.characters
                     .Where(actor => actor is Monster && actor.modData.ContainsKey(Region1MonsterMarkerKey))
                     .ToList())
        {
            location.characters.Remove(actor);
        }
    }

    private static int CountRegion1MarkedMonsters(GameLocation location)
        => location.characters
            .OfType<Monster>()
            .Count(monster => monster.Health > 0 && monster.modData.ContainsKey(Region1MonsterMarkerKey));

    private static Point ResolveRegion1RunArrivalTile(GameLocation room)
    {
        int width = room.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 28;
        int height = room.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 20;
        return FindClearTileNear(room, new Point(width / 2, Math.Max(3, height - 3)));
    }

    private static Point ResolveRegion1RunReturnTile(GameLocation room)
    {
        int width = room.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 28;
        int height = room.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 20;
        return new Point(width / 2, Math.Max(2, height - 2));
    }

    private void HandleRegion1DepartureRequest()
    {
        if (this.Save.Data.AirshipHighestRegionUnlocked < 1)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.route.locked"));
            return;
        }

        // Validate the target before money is ever consumed.
        if (this.EnsureRegion1Location() is null || !this.EnsureRegion1RunRoomLocations())
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
                if (!this.WarpToAirshipBridge() && !this.WarpToSkyDockInterior())
                    this.ReturnToSkyDockExterior();
            }
            else
            {
                if (!string.IsNullOrWhiteSpace(this.PendingExternalFlightLocationName))
                {
                    GameLocation? external = Game1.getLocationFromName(this.PendingExternalFlightLocationName);
                    if (external is null)
                    {
                        this.FlightCutsceneActive = false;
                        this.PendingExternalFlightLocationName = string.Empty;
                        this.ReturnToSkyDockExterior();
                        Game1.drawObjectDialogue(ModEntry.T("airship.expedition.unavailable"));
                        return;
                    }
                    Point arrival = this.PendingExternalFlightArrivalTile;
                    this.WarpGraceUntilMs = Environment.TickCount64 + 850L;
                    Game1.warpFarmer(external.NameOrUniqueName, arrival.X, arrival.Y, 0);
                }
                else
                {
                    GameLocation? firstRoom = this.BeginRegion1HuntRun();
                    if (firstRoom is null)
                    {
                    // Target was validated before charging; this is a last-resort failure path.
                    this.FlightCutsceneActive = false;
                    this.ReturnToSkyDockExterior();
                    Game1.drawObjectDialogue(ModEntry.T("airship.region1.unavailable"));
                    return;
                }

                    Point arrival = ResolveRegion1RunArrivalTile(firstRoom);
                    this.WarpGraceUntilMs = Environment.TickCount64 + 850L;
                    Game1.warpFarmer(firstRoom.NameOrUniqueName, arrival.X, arrival.Y, 0);
                }
            }
        }

        if (elapsed >= FlightCutsceneDurationMs)
        {
            this.FlightCutsceneActive = false;
            this.FlightCutsceneReturning = false;
            this.FlightCutsceneWarped = false;
            this.FlightCutsceneStartedAtMs = 0;
            this.PendingExternalFlightLocationName = string.Empty;
            this.PendingExternalFlightArrivalTile = Point.Zero;
            this.WarpGraceUntilMs = Environment.TickCount64 + 500L;
        }
    }

    private bool TryHandleAutoTransition()
    {
        if (Game1.activeClickableMenu is not null || Game1.dialogueUp || Game1.eventUp || this.FlightCutsceneActive)
            return false;

        GameLocation? location = Game1.currentLocation;
        if (location is null)
            return false;

        Point playerTile = new(
            (int)(Game1.player.Position.X / 64f),
            (int)(Game1.player.Position.Y / 64f)
        );

        if (location.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase))
        {
            Point bay = ResolveSkyDockInteriorBayTile(location);
            if (playerTile == bay)
                return this.WarpToAirshipBridge();

            if (IsBottomDoorwayZone(location, playerTile))
            {
                this.ReturnToSkyDockExterior();
                return true;
            }

            return false;
        }

        if (location.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))
        {
            if (IsBottomDoorwayZone(location, playerTile))
                return this.WarpToSkyDockInterior();
        }

        return false;
    }

    private bool WarpToAirshipBridge()
    {
        GameLocation? deck = this.EnsureDeckLocation();
        if (deck is null)
            return false;

        Point arrival = ResolveDeckArrivalTile(deck);
        this.WarpGraceUntilMs = Environment.TickCount64 + 850L;
        Game1.playSound("wand");
        Game1.warpFarmer(DeckLocationName, arrival.X, arrival.Y, 0);
        return true;
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
        Point landing = ResolveForestGateLandingTile(forest, dock);
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
            int owned = this.Save.Data.OwnedCards?.Count ?? 0;
            if (owned < Region1GateCardRequirement)
            {
                Game1.drawObjectDialogue(ModEntry.T("airship.region1.gate.locked", new { cards = owned, required = Region1GateCardRequirement }));
                return;
            }

            GameLocation? arena = Game1.getLocationFromName(VerdantGuardianBossService.LocationName);
            if (arena is null)
            {
                Game1.drawObjectDialogue(ModEntry.T("boss.verdant.arena.unavailable"));
                return;
            }

            Game1.playSound("wand");
            Game1.warpFarmer(
                VerdantGuardianBossService.LocationName,
                VerdantGuardianBossService.PlayerArrivalTile.X,
                VerdantGuardianBossService.PlayerArrivalTile.Y,
                0
            );
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
        // .5.12.4: one authoritative, deterministic Forest gate anchor.
        // No runtime safe-tile search, flood-fill, or farmer/NPC occupancy is allowed to move it.
        // The -23,+10 offset preserves the accepted farm-side meadow placement immediately
        // right of the pink blossom tree.
        if (this.CachedSkyDockTile is Point cached)
            return cached;

        GameLocation? forest = Game1.getLocationFromName(SkyDockLocationName);
        Point farmWarp = this.ResolveForestFarmWarpTile();
        int width = forest?.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 120;
        int height = forest?.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 120;

        this.CachedSkyDockTile = new Point(
            Math.Clamp(farmWarp.X - 23, 2, Math.Max(2, width - 3)),
            Math.Clamp(farmWarp.Y + 10, 2, Math.Max(2, height - 4))
        );
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
        // Reserve visual breathing room in front of the overlay too. We do not delete or
        // alter Forest foliage; instead the dynamic anchor simply rejects a bushy footprint.
        Point[] footprint =
        {
            new(anchor.X - 1, anchor.Y),
            anchor,
            new(anchor.X + 1, anchor.Y),
            new(anchor.X - 1, anchor.Y + 1),
            new(anchor.X, anchor.Y + 1),
            new(anchor.X + 1, anchor.Y + 1),
            new(anchor.X - 1, anchor.Y + 2),
            new(anchor.X, anchor.Y + 2),
            new(anchor.X + 1, anchor.Y + 2)
        };

        foreach (Point p in footprint)
        {
            if (Math.Abs(p.X - farmWarp.X) <= 3 && Math.Abs(p.Y - farmWarp.Y) <= 3)
                return false;

            try
            {
                Vector2 tile = new(p.X, p.Y);
                // Static map-overhaul fences, trunks, and canopy pieces can live on map layers
                // without being represented as terrain features. Reject those anchors too.
                var buildings = location.Map?.GetLayer("Buildings");
                var front = location.Map?.GetLayer("Front");
                if (buildings?.Tiles[p.X, p.Y] is not null || front?.Tiles[p.X, p.Y] is not null)
                    return false;

                if (location.IsTileBlockedBy(tile)
                    || location.Objects.ContainsKey(tile)
                    || location.terrainFeatures.ContainsKey(tile))
                {
                    return false;
                }

                Rectangle tileBounds = new(p.X * 64, p.Y * 64, 64, 64);
                foreach (var feature in location.largeTerrainFeatures)
                {
                    if (feature.getBoundingBox().Intersects(tileBounds))
                        return false;
                }
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
        return new Point(width / 2, Math.Max(5, height - 4));
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
        return new Point(Math.Clamp(width / 4, 3, width - 4), Math.Clamp(7, 3, height - 5));
    }

    private static Point ResolveSkyDockInteriorBayTile(GameLocation interior)
    {
        int width = interior.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30;
        int height = interior.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;
        return new Point(Math.Clamp(width - 7, 4, width - 3), Math.Clamp(8, 3, height - 5));
    }

    private static Point ResolveSkyDockLostFoundTile(GameLocation interior)
    {
        int width = interior.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30; int height = interior.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;
        return new Point(Math.Clamp(5, 2, width - 3), Math.Clamp(11, 4, height - 3));
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

    private static bool IsPortalZone(Point playerTile, Point center, int radiusX, int radiusY)
        => Math.Abs(playerTile.X - center.X) <= radiusX
           && Math.Abs(playerTile.Y - center.Y) <= radiusY;

    private static bool IsBottomDoorwayZone(GameLocation location, Point playerTile)
    {
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 24;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 14;
        int center = width / 2;
        return playerTile.Y >= height - 2
            && (playerTile.X == center - 1 || playerTile.X == center);
    }


private void EnsureDeckVanillaFurniture(GameLocation deck)
{
    if (ReferenceEquals(this.DeckDecorAppliedLocation, deck)
        && deck.modData.TryGetValue(InteriorDecorMarkerKey, out string? version)
        && string.Equals(version, InteriorDecorVersion + "-0690-bridge", StringComparison.Ordinal))
        return;

    this.DeckDecorAppliedLocation = deck;
    ClearInteriorDecor(deck);
    // 0690: physical bridge furnishings are authored into airship_deck.tmx.
    deck.modData[InteriorDecorMarkerKey] = InteriorDecorVersion + "-0690-bridge";
}

private void EnsureSkyDockVanillaFurniture(GameLocation dock)
{
    if (ReferenceEquals(this.SkyDockDecorAppliedLocation, dock)
        && dock.modData.TryGetValue(InteriorDecorMarkerKey, out string? version)
        && string.Equals(version, InteriorDecorVersion + "-0690-dock", StringComparison.Ordinal))
        return;

    this.SkyDockDecorAppliedLocation = dock;
    ClearInteriorDecor(dock);
    // 0690: physical dock furnishings are authored into sky_dock_interior.tmx.
    dock.modData[InteriorDecorMarkerKey] = InteriorDecorVersion + "-0690-dock";
}

private static void ClearInteriorDecor(GameLocation location)
{
    foreach (Furniture old in location.furniture
                 .Where(f => f.modData.ContainsKey(InteriorDecorMarkerKey))
                 .ToList())
    {
        location.furniture.Remove(old);
    }

    foreach (Vector2 key in location.Objects.Pairs
                 .Where(pair => pair.Value?.modData.ContainsKey(InteriorDecorMarkerKey) == true)
                 .Select(pair => pair.Key)
                 .ToList())
    {
        location.Objects.Remove(key);
    }
}

private static void TryAddInteriorFurniture(
    GameLocation location,
    string itemId,
    int x,
    int y,
    int rotation = 0,
    string? heldId = null)
{
    Furniture item;
    try
    {
        item = ItemRegistry.Create<Furniture>(itemId).SetPlacement(x, y, rotation);
    }
    catch (Exception ex)
    {
        ModEntry.StaticMonitor?.Log($"0677A skipped invalid Airship furniture {itemId} at {x},{y}: {ex.GetType().Name}: {ex.Message}", StardewModdingAPI.LogLevel.Warn);
        return;
    }

    item.modData[InteriorDecorMarkerKey] = InteriorDecorVersion;
    if (heldId is not null)
    {
        try
        {
            item.SetHeldObject(ItemRegistry.Create<Furniture>(heldId));
        }
        catch (Exception ex)
        {
            ModEntry.StaticMonitor?.Log($"0677A kept Airship furniture {itemId} but skipped held decor {heldId}: {ex.GetType().Name}", StardewModdingAPI.LogLevel.Trace);
        }
    }
    location.furniture.Add(item);
}

private static void TryAddInteriorChest(GameLocation location, Point tile)
{
    try
    {
        Vector2 key = new(tile.X, tile.Y);
        if (location.Objects.TryGetValue(key, out StardewValley.Object? existing)
            && existing is not null
            && !existing.modData.ContainsKey(InteriorDecorMarkerKey))
        {
            return;
        }

        location.Objects.Remove(key);
        Chest chest = new(true);
        chest.modData[InteriorDecorMarkerKey] = InteriorDecorVersion;
        location.setObject(key, chest);
    }
    catch
    {
        // The interaction handler still works even if a decorative chest cannot spawn.
    }
}

    private static (AirshipUpgradeSystem System, Point Tile)[] ResolveDeckUpgradeSockets()
        => new[]
        {
            (AirshipUpgradeSystem.Engine, new Point(4, 8)),
            (AirshipUpgradeSystem.Navigation, new Point(19, 8)),
            (AirshipUpgradeSystem.Hull, new Point(7, 11)),
            (AirshipUpgradeSystem.Reactor, new Point(16, 11)),
        };

    private static bool ActionTouchesStation(Point action, Point station)
        => action.Y == station.Y && Math.Abs(action.X - station.X) <= 1;

    private int GetAirshipUpgradeLevel(AirshipUpgradeSystem system)
        => system switch
        {
            AirshipUpgradeSystem.Engine => this.Save.Data.AirshipEngineLevel,
            AirshipUpgradeSystem.Navigation => this.Save.Data.AirshipNavigationLevel,
            AirshipUpgradeSystem.Hull => this.Save.Data.AirshipHullLevel,
            AirshipUpgradeSystem.Reactor => this.Save.Data.AirshipReactorLevel,
            _ => 0,
        };

    private static Point ResolveDeckArrivalTile(GameLocation deck)
    {
        int width = deck.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 24;
        int height = deck.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 14;
        return new Point(width / 2, Math.Max(5, height - 4));
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
        return new Point(Math.Clamp(width / 2, 2, width - 3), Math.Clamp(6, 2, height - 3));
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
            this.DrawAirshipPropellerMotion(
                batch,
                p,
                230f,
                SpriteEffects.None,
                rotation,
                verticalScale,
                spinDirection: 1f
            );
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

    private void DrawSkyDockInteriorDetails(SpriteBatch batch, GameLocation interior)
    {
        // .5.8 Stardew interior renderer owns Sky Dock visual staging.
        if (AirshipInteriorStardewRenderer.TryDrawSkyDock(batch, interior))
            return;

        Point route = ResolveSkyDockInteriorRouteTile(interior);
        Point exit = ResolveSkyDockInteriorExitTile(interior);
        Point bay = ResolveSkyDockInteriorBayTile(interior);
        Point arrival = ResolveSkyDockInteriorArrivalTile(interior);

        float phase = (float)(Environment.TickCount64 / 980.0);
        float pulse = 0.58f + 0.16f * (float)Math.Sin(Environment.TickCount64 / 275.0);
        Color violet = new Color(180, 108, 255) * pulse;
        Color cyan = new Color(86, 221, 244) * (pulse * 0.96f);
        Color gold = new Color(226, 171, 81) * 0.94f;
        Color woodDark = new Color(66, 43, 35) * 0.96f;
        Color wood = new Color(108, 67, 46) * 0.94f;
        Color brass = new Color(158, 100, 54) * 0.94f;
        Color frame = new Color(42, 35, 49) * 0.98f;

        Vector2 arrivalCenter = Game1.GlobalToLocal(Game1.viewport, new Vector2(arrival.X * 64f + 32f, arrival.Y * 64f + 40f));
        Vector2 routeCenter = Game1.GlobalToLocal(Game1.viewport, new Vector2(route.X * 64f + 32f, route.Y * 64f + 36f));
        Vector2 bayCenter = Game1.GlobalToLocal(Game1.viewport, new Vector2(bay.X * 64f + 32f, bay.Y * 64f + 36f));

        // Open-sky mooring aperture, with the real locked Airship outside the room.
        Vector2 skyOrigin = Game1.GlobalToLocal(Game1.viewport, new Vector2((bay.X - 5) * 64f, (bay.Y - 5) * 64f));
        Rectangle sky = new((int)skyOrigin.X, (int)skyOrigin.Y, 8 * 64, 6 * 64);
        DrawVerticalGradient(batch, sky,
            new Color(71, 133, 199) * 0.93f,
            new Color(113, 178, 220) * 0.92f,
            new Color(231, 188, 205) * 0.78f);
        DrawPortalClouds(batch, sky, phase * 0.72f, Color.White * 0.56f);

        Vector2 dockedShip = new(sky.X + sky.Width * 0.66f, sky.Y + sky.Height * 0.46f);
        float shipBob = (float)Math.Sin(Environment.TickCount64 / 520.0) * 3.5f;
        if (this.TryDrawAirshipSprite(batch, dockedShip + new Vector2(0f, shipBob), 520f, Color.White * 0.88f, SpriteEffects.None, 0.006f, 1f))
        {
            this.DrawAirshipPropellerMotion(batch, dockedShip + new Vector2(0f, shipBob), 520f, SpriteEffects.None, 0.006f, 1f, spinDirection: 0.32f);
        }

        DrawRect(batch, new Rectangle(sky.X - 13, sky.Y - 13, sky.Width + 26, 16), frame);
        DrawRect(batch, new Rectangle(sky.X - 13, sky.Bottom - 2, sky.Width + 26, 16), frame);
        DrawRect(batch, new Rectangle(sky.X - 13, sky.Y, 16, sky.Height), frame);
        DrawRect(batch, new Rectangle(sky.Right - 2, sky.Y, 16, sky.Height), frame);
        for (int i = 1; i < 4; i++)
        {
            int x = sky.X + i * sky.Width / 4;
            DrawRect(batch, new Rectangle(x - 4, sky.Y, 8, sky.Height), brass * 0.70f);
        }
        DrawEllipticArc(batch, new Vector2(sky.Center.X, sky.Y + 22f), sky.Width * 0.50f, 90f, MathHelper.Pi, MathHelper.TwoPi, 22, 9f, brass * 0.82f);

        // Boarding deck projects toward the moored ship. Low-alpha planks preserve farmer readability.
        Vector2 bridgeStart = Game1.GlobalToLocal(Game1.viewport, new Vector2((arrival.X + 1) * 64f, (bay.Y + 1) * 64f));
        Rectangle deckRect = new(
            (int)Math.Min(bridgeStart.X, bayCenter.X - 90f),
            (int)bayCenter.Y + 34,
            Math.Max(180, (int)Math.Abs(bayCenter.X - bridgeStart.X) + 170),
            118
        );
        DrawRect(batch, deckRect, woodDark * 0.42f);
        for (int y = deckRect.Y + 10; y < deckRect.Bottom; y += 24)
            DrawRect(batch, new Rectangle(deckRect.X + 8, y, deckRect.Width - 16, 4), wood * 0.36f);
        DrawRect(batch, new Rectangle(deckRect.X + 10, deckRect.Y + 8, deckRect.Width - 20, 4), gold * 0.44f);
        DrawRect(batch, new Rectangle(deckRect.X + 10, deckRect.Bottom - 14, deckRect.Width - 20, 4), gold * 0.26f);
        DrawRailing(batch, new Vector2(deckRect.X + 16f, deckRect.Y + 12f), new Vector2(deckRect.Right - 16f, deckRect.Y + 12f), brass, cyan * 0.42f);

        // .5.6.1 readability: no post-world energy lines or large sigils through the farmer.
        // Keep magical identification attached to the actual destinations instead.
        DrawArcaneSigil(batch, routeCenter, 31f, violet * 0.52f, phase * 0.55f);
        DrawDiamondRune(batch, routeCenter, 10f, cyan * 0.68f);
        DrawArcaneSigil(batch, bayCenter, 29f, cyan * 0.48f, -phase * 0.48f);

        // Brass navigator console.
        Vector2 board = Game1.GlobalToLocal(Game1.viewport, new Vector2((route.X - 1) * 64f, (route.Y - 2) * 64f));
        DrawRect(batch, new Rectangle((int)board.X - 12, (int)board.Y + 14, 180, 88), new Color(24, 21, 31) * 0.66f);
        DrawRect(batch, new Rectangle((int)board.X, (int)board.Y, 156, 84), woodDark);
        DrawRect(batch, new Rectangle((int)board.X + 9, (int)board.Y + 9, 138, 60), wood);
        DrawRect(batch, new Rectangle((int)board.X + 18, (int)board.Y + 16, 120, 5), gold * 0.72f);
        DrawArcaneSigil(batch, new Vector2(board.X + 78f, board.Y + 43f), 27f, violet * 0.72f, -phase * 1.1f);
        DrawDiamondRune(batch, new Vector2(board.X + 78f, board.Y + 43f), 11f, cyan * 0.82f);
        DrawRect(batch, new Rectangle((int)board.X + 22, (int)board.Y + 74, 10, 38), brass);
        DrawRect(batch, new Rectangle((int)board.X + 124, (int)board.Y + 74, 10, 38), brass);
        string routeBoardLabel = ModEntry.T("airship.arcane.route_board.label");
        Vector2 routeBoardSize = Game1.smallFont.MeasureString(routeBoardLabel);
        float routeBoardScale = Math.Min(0.56f, 116f / Math.Max(1f, routeBoardSize.X));
        batch.DrawString(Game1.smallFont, routeBoardLabel,
            new Vector2(board.X + 78f - routeBoardSize.X * routeBoardScale / 2f, board.Y + 53f),
            new Color(236, 211, 151) * 0.84f, 0f, Vector2.Zero, routeBoardScale, SpriteEffects.None, 1f);
        DrawBrassLamp(batch, new Vector2(board.X - 26f, board.Y + 78f), phase, gold, violet);

        // Physical boarding arch in front of the ship instead of a second portal chamber.
        Vector2 gate = Game1.GlobalToLocal(Game1.viewport, new Vector2((bay.X - 1) * 64f, (bay.Y - 2) * 64f));
        Vector2 gateCenter = new(gate.X + 64f, gate.Y + 86f);
        DrawRect(batch, new Rectangle((int)gate.X - 12, (int)gate.Y + 17, 22, 142), frame);
        DrawRect(batch, new Rectangle((int)gate.X + 118, (int)gate.Y + 17, 22, 142), frame);
        DrawEllipticArc(batch, new Vector2(gateCenter.X, gate.Y + 24f), 66f, 62f, MathHelper.Pi, MathHelper.TwoPi, 18, 15f, frame);
        DrawEllipticArc(batch, new Vector2(gateCenter.X, gate.Y + 24f), 57f, 54f, MathHelper.Pi, MathHelper.TwoPi, 18, 5f, gold * 0.78f);
        DrawRect(batch, new Rectangle((int)gate.X + 10, (int)gate.Y + 146, 108, 8), brass * 0.90f);
        DrawArcaneSigil(batch, new Vector2(gateCenter.X, gate.Y + 112f), 30f, cyan * 0.58f, phase * 0.70f);
        DrawCrystalPylon(batch, new Vector2(gate.X - 6f, gate.Y + 161f), 43f, cyan, gold);
        DrawCrystalPylon(batch, new Vector2(gate.X + 134f, gate.Y + 161f), 43f, violet, gold);

        Vector2 exitCenter = Game1.GlobalToLocal(Game1.viewport, new Vector2(exit.X * 64f + 32f, exit.Y * 64f + 38f));
        DrawArcaneSigil(batch, exitCenter, 27f, cyan * 0.48f, -phase * 0.4f);
        DrawWorldMarker(batch, route, gold * 0.68f);
        DrawWorldMarker(batch, bay, violet * 0.76f);
        DrawWorldMarker(batch, exit, cyan * 0.60f);
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

    private static (Color Top, Color Mid, Color Low) ResolveOutdoorSkyPalette()
    {
        int time = Game1.timeOfDay;
        bool night = time >= 2000 || time < 600;
        bool dusk = time >= 1700 && time < 2000;
        bool dawn = time >= 600 && time < 800;

        Color top;
        Color mid;
        Color low;
        if (night)
        {
            top = new Color(18, 30, 65);
            mid = new Color(37, 49, 92);
            low = new Color(67, 64, 108);
        }
        else if (dusk)
        {
            top = new Color(72, 101, 160);
            mid = new Color(190, 118, 132);
            low = new Color(244, 176, 119);
        }
        else if (dawn)
        {
            top = new Color(94, 132, 181);
            mid = new Color(209, 156, 160);
            low = new Color(247, 204, 149);
        }
        else
        {
            top = new Color(78, 145, 207);
            mid = new Color(126, 190, 224);
            low = new Color(214, 225, 226);
        }

        if (Game1.isLightning)
            return (new Color(41, 49, 69), new Color(62, 68, 85), new Color(94, 96, 108));
        if (Game1.isRaining)
            return (new Color(48, 66, 91), new Color(70, 85, 105), new Color(101, 111, 120));
        if (Game1.isSnowing)
            return (new Color(95, 112, 139), new Color(141, 154, 174), new Color(201, 207, 211));
        if (Game1.isDebrisWeather)
            return (new Color(97, 127, 144), new Color(141, 160, 154), new Color(192, 190, 164));
        return (top, mid, low);
    }

    private static void DrawFlightWeather(SpriteBatch batch, Rectangle sky, float phase)
    {
        if (Game1.isRaining || Game1.isLightning)
        {
            Color rain = new Color(183, 204, 221) * 0.50f;
            for (int i = 0; i < 34; i++)
            {
                int x = sky.X + (int)((i * 73 + phase * 210f) % Math.Max(1, sky.Width));
                int y = sky.Y + (int)((i * 41 + phase * 330f) % Math.Max(1, sky.Height));
                DrawRect(batch, new Rectangle(x, y, 2, 10), rain);
            }
            if (Game1.isLightning)
            {
                float flash = Math.Max(0f, (float)Math.Sin(phase * 7.5f) - 0.86f) * 2.4f;
                if (flash > 0f)
                    DrawRect(batch, sky, Color.White * Math.Min(0.22f, flash));
            }
            return;
        }
        if (Game1.isSnowing)
        {
            Color snow = new Color(244, 245, 238) * 0.72f;
            for (int i = 0; i < 30; i++)
            {
                int x = sky.X + (int)((i * 83 + phase * 34f) % Math.Max(1, sky.Width));
                int y = sky.Y + (int)((i * 47 + phase * 58f) % Math.Max(1, sky.Height));
                int s = 2 + (i % 3);
                DrawRect(batch, new Rectangle(x, y, s, s), snow);
            }
            return;
        }
        if (Game1.isDebrisWeather)
        {
            Color leaf = new Color(164, 133, 73) * 0.62f;
            for (int i = 0; i < 22; i++)
            {
                int x = sky.X + (int)((i * 91 + phase * 120f) % Math.Max(1, sky.Width));
                int y = sky.Y + (int)((i * 53 + phase * 46f) % Math.Max(1, sky.Height));
                DrawRect(batch, new Rectangle(x, y, 4, 2), leaf);
            }
        }
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
        Rectangle sky = new(0, 0, w, h);
        float phase = (float)(Environment.TickCount64 / 1000.0);
        (Color top, Color mid, Color low) = ResolveOutdoorSkyPalette();
        DrawVerticalGradient(batch, sky, top, mid, low);

        bool night = Game1.timeOfDay >= 2000 || Game1.timeOfDay < 600;
        if (!Game1.isRaining && !Game1.isLightning && !Game1.isSnowing && !Game1.isDebrisWeather)
        {
            if (night)
                DrawStarfield(batch, sky, 54, phase, new Color(247, 235, 204) * 0.78f);
            else
            {
                DrawCloudBand(batch, sky, h / 5, phase * 16f, Color.White * 0.48f);
                DrawCloudBand(batch, sky, h * 2 / 5, -phase * 10f, Color.White * 0.30f);
            }
        }
        DrawFlightWeather(batch, sky, phase);

        // Thin lower haze only. The old fake wooden stage / straight cloud bars are gone.
        DrawRect(batch, new Rectangle(0, h - 52, w, 52), low * 0.24f);

        float crest = (float)Math.Sin(p * Math.PI);
        float travel = this.FlightCutsceneReturning ? 1f - eased : eased;
        float shipX = MathHelper.Lerp(w * 0.24f, w * 0.76f, travel);
        float bob = (float)Math.Sin(p * MathHelper.TwoPi * 1.25f) * (3f + crest * 8f);
        float lift = crest * 24f;
        float shipY = h * 0.43f - lift + bob;
        float direction = this.FlightCutsceneReturning ? -1f : 1f;
        float rotation = -direction * CutsceneTiltRadians * (0.30f + crest * 0.70f);
        float verticalScale = 1f + (float)Math.Sin(p * MathHelper.TwoPi * 1.75f) * CutsceneScalePulse;
        SpriteEffects directionEffect = this.FlightCutsceneReturning ? SpriteEffects.FlipHorizontally : SpriteEffects.None;
        float targetWidth = Math.Min(720f, w * 0.62f);

        bool spriteDrawn = this.TryDrawAirshipSprite(
            batch, new Vector2(shipX, shipY), targetWidth, Color.White * 0.98f,
            directionEffect, rotation, verticalScale
        );
        if (spriteDrawn)
        {
            this.DrawAirshipPropellerMotion(
                batch, new Vector2(shipX, shipY), targetWidth,
                directionEffect, rotation, verticalScale, spinDirection: direction
            );
        }
        else
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
        if (AirshipLayeredRenderer.TryDraw(batch, center, targetWidth, tint, effects, rotation, verticalScale))
            return true;

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

    private void DrawAirshipPropellerMotion(
        SpriteBatch batch,
        Vector2 spriteCenter,
        float targetWidth,
        SpriteEffects effects,
        float rotation,
        float verticalScale,
        float spinDirection)
    {
        Texture2D? sprite = this.GetAirshipVisual();
        if (sprite is null || targetWidth <= 0f)
            return;

        float scale = targetWidth / sprite.Width;
        bool mirrored = (effects & SpriteEffects.FlipHorizontally) != SpriteEffects.None;
        float spin = (float)(Environment.TickCount64 / 1000.0)
            * PropellerSpinRadiansPerSecond
            * spinDirection;

        Vector2 left = TransformSpriteOffset(
            new Vector2(-89f * scale, 66f * scale),
            spriteCenter,
            rotation,
            verticalScale,
            mirrored
        );
        Vector2 right = TransformSpriteOffset(
            new Vector2(90f * scale, 66f * scale),
            spriteCenter,
            rotation,
            verticalScale,
            mirrored
        );

        DrawAnimatedPropeller(batch, left, scale, spin);
        DrawAnimatedPropeller(batch, right, scale, -spin);
    }

    private static Vector2 TransformSpriteOffset(
        Vector2 offset,
        Vector2 center,
        float rotation,
        float verticalScale,
        bool mirrored)
    {
        if (mirrored)
            offset.X = -offset.X;

        offset.Y *= verticalScale;
        float cos = MathF.Cos(rotation);
        float sin = MathF.Sin(rotation);
        return center + new Vector2(
            offset.X * cos - offset.Y * sin,
            offset.X * sin + offset.Y * cos
        );
    }

    private static void DrawAnimatedPropeller(
        SpriteBatch batch,
        Vector2 center,
        float scale,
        float spin)
    {
        Color outline = new Color(49, 33, 25) * 0.78f;
        Color blade = new Color(247, 231, 196) * 0.88f;
        float length = 18f * scale;
        float outlineWidth = Math.Max(2f, 6f * scale);
        float bladeWidth = Math.Max(1.5f, 4f * scale);

        for (int i = 0; i < 3; i++)
        {
            float angle = spin + i * MathHelper.TwoPi / 3f;
            DrawRotorStroke(batch, center, angle, length, outlineWidth, outline);
            DrawRotorStroke(batch, center, angle, length * 0.90f, bladeWidth, blade);
        }

        int hubRadius = Math.Max(2, (int)(4f * scale));
        DrawRect(
            batch,
            new Rectangle(
                (int)center.X - hubRadius,
                (int)center.Y - hubRadius,
                hubRadius * 2 + 1,
                hubRadius * 2 + 1
            ),
            new Color(191, 128, 42) * 0.94f
        );
    }

    private static void DrawRotorStroke(
        SpriteBatch batch,
        Vector2 center,
        float angle,
        float length,
        float width,
        Color color)
    {
        batch.Draw(
            Game1.staminaRect,
            center,
            sourceRectangle: null,
            color: color,
            rotation: angle,
            origin: new Vector2(0f, 0.5f),
            scale: new Vector2(length, width),
            effects: SpriteEffects.None,
            layerDepth: 1f
        );
    }

    private Texture2D? GetAirshipUpgradeVisuals()
    {
        if (this.AirshipUpgradeVisuals is not null)
            return this.AirshipUpgradeVisuals;
        if (this.AirshipUpgradeVisualsLoadFailed)
            return null;

        try
        {
            this.AirshipUpgradeVisuals = this.Helper.ModContent.Load<Texture2D>(AirshipUpgradeVisualPath);
            return this.AirshipUpgradeVisuals;
        }
        catch (Exception ex)
        {
            this.AirshipUpgradeVisualsLoadFailed = true;
            this.Monitor.Log(
                $"Couldn't load Airship interior upgrade visuals; procedural sockets remain active. {ex.GetType().Name}: {ex.Message}",
                LogLevel.Warn
            );
            return null;
        }
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
        // .5.8 Stardew interior renderer owns Bridge visual staging.
        if (AirshipInteriorStardewRenderer.TryDrawDeck(batch, deck, this.Save))
            return;

        Point helm = ResolveDeckHelmTile(deck);
        Point exit = ResolveDeckExitTile(deck);
        int width = deck.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 24;
        float phase = (float)(Environment.TickCount64 / 1020.0);
        float pulse = 0.58f + 0.15f * (float)Math.Sin(Environment.TickCount64 / 270.0);
        Color violet = new Color(181, 108, 255) * pulse;
        Color cyan = new Color(87, 220, 244) * (pulse * 0.96f);
        Color gold = new Color(226, 171, 81) * 0.94f;
        Color brass = new Color(151, 93, 50) * 0.96f;
        Color woodDark = new Color(61, 39, 34) * 0.96f;
        Color wood = new Color(101, 62, 45) * 0.94f;
        Color frame = new Color(40, 33, 45) * 0.99f;
        bool night = Game1.timeOfDay >= 1800 || Game1.timeOfDay < 600;

        // Grand panoramic forward canopy.
        Vector2 window = Game1.GlobalToLocal(Game1.viewport, new Vector2(2f * 64f, 0.65f * 64f));
        int windowTiles = Math.Max(12, width - 4);
        Rectangle windowRect = new((int)window.X, (int)window.Y, windowTiles * 64, 5 * 64);
        Color skyTop = night ? new Color(23, 34, 73) : new Color(74, 137, 201);
        Color skyMid = night ? new Color(45, 49, 95) : new Color(114, 178, 220);
        Color skyLow = night ? new Color(76, 59, 108) : new Color(236, 188, 201);
        DrawVerticalGradient(batch, windowRect, skyTop * 0.98f, skyMid * 0.97f, skyLow * 0.90f);

        if (night)
            DrawStarfield(batch, windowRect, 46, phase, new Color(244, 235, 202) * 0.78f);
        else
        {
            DrawCloudBand(batch, windowRect, 46, phase * 22f, Color.White * 0.64f);
            DrawCloudBand(batch, windowRect, 132, -phase * 15f, Color.White * 0.46f);
            DrawFloatingIslands(batch, windowRect, phase);
        }

        // Curved ship-frame architecture around the panoramic glass.
        DrawRect(batch, new Rectangle(windowRect.X - 18, windowRect.Y - 18, windowRect.Width + 36, 20), frame);
        DrawRect(batch, new Rectangle(windowRect.X - 18, windowRect.Bottom - 6, windowRect.Width + 36, 21), frame);
        DrawRect(batch, new Rectangle(windowRect.X - 18, windowRect.Y, 20, windowRect.Height), frame);
        DrawRect(batch, new Rectangle(windowRect.Right - 2, windowRect.Y, 20, windowRect.Height), frame);
        DrawEllipticArc(batch, new Vector2(windowRect.Center.X, windowRect.Y + 34f), windowRect.Width * 0.50f, 108f, MathHelper.Pi, MathHelper.TwoPi, 30, 13f, frame);
        DrawEllipticArc(batch, new Vector2(windowRect.Center.X, windowRect.Y + 34f), windowRect.Width * 0.48f, 100f, MathHelper.Pi, MathHelper.TwoPi, 30, 5f, brass * 0.84f);

        for (int i = 1; i <= 5; i++)
        {
            float t = i / 6f;
            int x = (int)MathHelper.Lerp(windowRect.X + 60f, windowRect.Right - 60f, t);
            DrawRect(batch, new Rectangle(x - 5, windowRect.Y + 10, 10, windowRect.Height - 20), frame * 0.90f);
            DrawRect(batch, new Rectangle(x - 2, windowRect.Y + 14, 4, windowRect.Height - 28), brass * 0.62f);
        }

        Vector2 helmCenter = Game1.GlobalToLocal(Game1.viewport, new Vector2(helm.X * 64f + 32f, helm.Y * 64f + 42f));
        Vector2 exitCenter = Game1.GlobalToLocal(Game1.viewport, new Vector2(exit.X * 64f + 32f, exit.Y * 64f + 36f));

        // Purple runner and brass rails join boarding door to helm.
        Vector2 laneTop = new(helmCenter.X, helmCenter.Y + 54f);
        Vector2 laneBottom = new(exitCenter.X, exitCenter.Y - 14f);
        float laneY = Math.Min(laneTop.Y, laneBottom.Y);
        float laneHeight = Math.Max(96f, Math.Abs(laneBottom.Y - laneTop.Y));
        Rectangle runner = new((int)helmCenter.X - 72, (int)laneY, 144, (int)laneHeight);
        DrawRect(batch, runner, new Color(78, 45, 83) * 0.18f);
        DrawRect(batch, new Rectangle(runner.X + 11, runner.Y, 4, runner.Height), gold * 0.26f);
        DrawRect(batch, new Rectangle(runner.Right - 15, runner.Y, 4, runner.Height), gold * 0.38f);
        for (int y = runner.Y + 28; y < runner.Bottom; y += 54)
            DrawDiamondRune(batch, new Vector2(runner.Center.X, y), 9f, gold * 0.19f);
        // .5.6.1: removed post-world mana line through the central player lane.

        // Multi-level navigation dais and suspended astrolabe core.
        DrawRect(batch, new Rectangle((int)helmCenter.X - 132, (int)helmCenter.Y + 41, 264, 26), new Color(25, 22, 31) * 0.66f);
        DrawRect(batch, new Rectangle((int)helmCenter.X - 116, (int)helmCenter.Y + 24, 232, 32), woodDark);
        DrawRect(batch, new Rectangle((int)helmCenter.X - 98, (int)helmCenter.Y + 12, 196, 31), wood);
        DrawRect(batch, new Rectangle((int)helmCenter.X - 84, (int)helmCenter.Y + 5, 168, 10), brass);
        DrawEllipticArc(batch, new Vector2(helmCenter.X, helmCenter.Y - 58f), 82f, 76f, 0f, MathHelper.TwoPi, 24, 7f, brass * 0.88f);
        DrawEllipticArc(batch, new Vector2(helmCenter.X, helmCenter.Y - 58f), 61f, 55f, 0f, MathHelper.TwoPi, 22, 4f, violet * 0.76f);
        DrawEllipticArc(batch, new Vector2(helmCenter.X, helmCenter.Y - 58f), 39f, 34f, 0f, MathHelper.TwoPi, 18, 3f, cyan * 0.82f);
        DrawRotorStroke(batch, new Vector2(helmCenter.X, helmCenter.Y - 58f), phase * 0.42f, 78f, 3f, gold * 0.62f);
        DrawRotorStroke(batch, new Vector2(helmCenter.X, helmCenter.Y - 58f), -phase * 0.55f + MathHelper.PiOver2, 62f, 3f, cyan * 0.52f);
        DrawDiamondRune(batch, new Vector2(helmCenter.X, helmCenter.Y - 58f), 24f, cyan);
        DrawRect(batch, new Rectangle((int)helmCenter.X - 5, (int)helmCenter.Y - 31, 10, 38), gold * 0.58f);
        DrawArcaneSigil(batch, new Vector2(helmCenter.X, helmCenter.Y + 18f), 46f, violet * 0.64f, phase);
        DrawArcaneSparkles(batch, new Vector2(helmCenter.X, helmCenter.Y - 48f), 88f, 12, phase, Color.White * 0.52f);

        Vector2 leftConsole = Game1.GlobalToLocal(Game1.viewport, new Vector2(5f * 64f, 7.25f * 64f));
        Vector2 rightConsole = Game1.GlobalToLocal(Game1.viewport, new Vector2((width - 7f) * 64f, 7.25f * 64f));
        DrawBridgeConsole(batch, leftConsole, violet, cyan, gold, phase);
        DrawBridgeConsole(batch, rightConsole, cyan, violet, gold, -phase);
        DrawInstrumentCluster(batch, leftConsole + new Vector2(-88f, -10f), phase, gold, cyan);
        DrawInstrumentCluster(batch, rightConsole + new Vector2(88f, -10f), -phase, gold, violet);

        Vector2 leftBanner = Game1.GlobalToLocal(Game1.viewport, new Vector2(2.6f * 64f, 5.4f * 64f));
        Vector2 rightBanner = Game1.GlobalToLocal(Game1.viewport, new Vector2((width - 4.3f) * 64f, 5.4f * 64f));
        DrawCardchaBanner(batch, leftBanner, gold, violet);
        DrawCardchaBanner(batch, rightBanner, gold, violet);

        DrawUpgradeConduitNetwork(batch, helmCenter, phase, gold);

        foreach ((AirshipUpgradeSystem system, Point socket) in ResolveDeckUpgradeSockets())
        {
            Vector2 s = Game1.GlobalToLocal(Game1.viewport, new Vector2(socket.X * 64f + 32f, socket.Y * 64f + 38f));
            this.DrawUpgradeSocket(batch, s, system, this.GetAirshipUpgradeLevel(system), phase, gold);
        }

        // Architectural alcove around the existing ChaCha station. The station runtime remains authoritative.
        Vector2 chachaAlcove = Game1.GlobalToLocal(Game1.viewport, new Vector2(19f * 64f + 32f, 5f * 64f + 32f));
        DrawEllipticArc(batch, chachaAlcove + new Vector2(0f, -22f), 54f, 46f, MathHelper.Pi, MathHelper.TwoPi, 16, 7f, brass * 0.68f);
        DrawCrystalPylon(batch, chachaAlcove + new Vector2(-58f, 28f), 28f, violet * 0.62f, gold * 0.58f);
        DrawCrystalPylon(batch, chachaAlcove + new Vector2(58f, 28f), 28f, cyan * 0.62f, gold * 0.58f);

        DrawArcaneSigil(batch, exitCenter, 29f, cyan * 0.48f, -phase * 0.42f);
        DrawWorldMarker(batch, helm, gold * 0.70f);
        DrawWorldMarker(batch, exit, cyan * 0.60f);
    }

    private static void DrawVerticalGradient(SpriteBatch batch, Rectangle rect, Color top, Color middle, Color bottom)
    {
        if (rect.Width <= 0 || rect.Height <= 0)
            return;
        int h1 = Math.Max(1, rect.Height / 3);
        int h2 = Math.Max(1, rect.Height / 3);
        int h3 = Math.Max(1, rect.Height - h1 - h2);
        DrawRect(batch, new Rectangle(rect.X, rect.Y, rect.Width, h1), top);
        DrawRect(batch, new Rectangle(rect.X, rect.Y + h1, rect.Width, h2), middle);
        DrawRect(batch, new Rectangle(rect.X, rect.Y + h1 + h2, rect.Width, h3), bottom);
    }

    private static void DrawPortalClouds(SpriteBatch batch, Rectangle bounds, float phase, Color color)
    {
        int period = Math.Max(180, bounds.Width / 2);
        int shift = ((int)(phase * 29f) % period + period) % period;
        for (int i = -2; i < 6; i++)
        {
            int x = bounds.X + i * period + shift - 70;
            int y = bounds.Y + bounds.Height / 3 + (i % 3) * 31;
            DrawClippedRect(batch, bounds, new Rectangle(x, y, 96, 11), color * 0.56f);
            DrawClippedRect(batch, bounds, new Rectangle(x + 22, y - 9, 62, 13), color * 0.72f);
            DrawClippedRect(batch, bounds, new Rectangle(x + 48, y + 7, 82, 9), color * 0.44f);
        }
    }

    private static void DrawEllipticArc(SpriteBatch batch, Vector2 center, float radiusX, float radiusY, float startAngle, float endAngle, int segments, float width, Color color)
    {
        segments = Math.Max(3, segments);
        Vector2 previous = new(center.X + MathF.Cos(startAngle) * radiusX, center.Y + MathF.Sin(startAngle) * radiusY);
        for (int i = 1; i <= segments; i++)
        {
            float t = i / (float)segments;
            float angle = MathHelper.Lerp(startAngle, endAngle, t);
            Vector2 current = new(center.X + MathF.Cos(angle) * radiusX, center.Y + MathF.Sin(angle) * radiusY);
            DrawLine(batch, previous, current, width, color);
            previous = current;
        }
    }

    private static void DrawLine(SpriteBatch batch, Vector2 start, Vector2 end, float width, Color color)
    {
        Vector2 delta = end - start;
        float length = delta.Length();
        if (length < 0.5f)
            return;
        DrawRotorStroke(batch, start, MathF.Atan2(delta.Y, delta.X), length, width, color);
    }

    private static void DrawBrassLamp(SpriteBatch batch, Vector2 baseCenter, float phase, Color brass, Color glow)
    {
        int x = (int)baseCenter.X;
        int y = (int)baseCenter.Y;
        DrawRect(batch, new Rectangle(x - 3, y - 37, 6, 37), brass * 0.86f);
        DrawRect(batch, new Rectangle(x - 12, y - 43, 24, 7), brass * 0.92f);
        DrawRect(batch, new Rectangle(x - 9, y - 63, 18, 20), new Color(39, 33, 43) * 0.92f);
        float flicker = 0.64f + 0.20f * MathF.Sin(phase * 2.4f + x * 0.01f);
        DrawRect(batch, new Rectangle(x - 6, y - 59, 12, 12), glow * flicker);
        DrawRect(batch, new Rectangle(x - 13, y - 66, 26, 4), brass * 0.82f);
    }

    private static void DrawRailing(SpriteBatch batch, Vector2 start, Vector2 end, Color brass, Color glow)
    {
        DrawLine(batch, start, end, 4f, brass * 0.86f);
        Vector2 delta = end - start;
        float length = delta.Length();
        if (length < 1f)
            return;
        Vector2 direction = delta / length;
        for (float d = 0f; d <= length; d += 72f)
        {
            Vector2 p = start + direction * d;
            DrawRect(batch, new Rectangle((int)p.X - 3, (int)p.Y - 28, 6, 31), brass * 0.84f);
            DrawDiamondRune(batch, new Vector2(p.X, p.Y - 30f), 6f, glow * 0.44f);
        }
    }

    private static void DrawFloatingIslands(SpriteBatch batch, Rectangle bounds, float phase)
    {
        Color far = new Color(74, 82, 91) * 0.24f;
        Color near = new Color(83, 91, 96) * 0.31f;
        int drift = (int)(phase * 7f);
        for (int i = 0; i < 4; i++)
        {
            int x = bounds.X + ((i * 283 + drift) % Math.Max(1, bounds.Width));
            int y = bounds.Y + 66 + (i % 3) * 46;
            int w = 54 + (i % 2) * 24;
            Color c = i % 2 == 0 ? far : near;
            DrawRect(batch, new Rectangle(x, y, w, 8), c);
            DrawRect(batch, new Rectangle(x + 9, y + 8, w - 18, 7), c * 0.82f);
            DrawRect(batch, new Rectangle(x + 19, y + 15, Math.Max(8, w - 38), 8), c * 0.64f);
            DrawRect(batch, new Rectangle(x + w / 2 - 2, y - 19, 4, 19), c * 0.80f);
        }
    }

    private static void DrawInstrumentCluster(SpriteBatch batch, Vector2 origin, float phase, Color gold, Color accent)
    {
        DrawRect(batch, new Rectangle((int)origin.X - 36, (int)origin.Y - 20, 72, 42), new Color(51, 40, 47) * 0.94f);
        DrawRect(batch, new Rectangle((int)origin.X - 30, (int)origin.Y - 14, 60, 29), new Color(92, 63, 50) * 0.88f);
        DrawEllipticArc(batch, origin + new Vector2(-14f, 0f), 10f, 10f, 0f, MathHelper.TwoPi, 12, 3f, gold * 0.72f);
        DrawEllipticArc(batch, origin + new Vector2(14f, 0f), 10f, 10f, 0f, MathHelper.TwoPi, 12, 3f, gold * 0.72f);
        DrawRotorStroke(batch, origin + new Vector2(-14f, 0f), phase * 0.33f, 8f, 2f, accent * 0.70f);
        DrawRotorStroke(batch, origin + new Vector2(14f, 0f), -phase * 0.41f, 8f, 2f, accent * 0.70f);
    }

    private static void DrawCardchaBanner(SpriteBatch batch, Vector2 origin, Color gold, Color violet)
    {
        Rectangle cloth = new((int)origin.X, (int)origin.Y, 94, 116);
        DrawRect(batch, cloth, new Color(72, 39, 91) * 0.82f);
        DrawRect(batch, new Rectangle(cloth.X + 7, cloth.Y + 7, cloth.Width - 14, 4), gold * 0.60f);
        DrawRect(batch, new Rectangle(cloth.X + 7, cloth.Bottom - 12, cloth.Width - 14, 4), gold * 0.48f);
        DrawDiamondRune(batch, new Vector2(cloth.Center.X, cloth.Y + 38f), 14f, violet * 0.72f);
        string text = "CARDCHA";
        Vector2 size = Game1.smallFont.MeasureString(text);
        batch.DrawString(Game1.smallFont, text, new Vector2(cloth.Center.X - size.X * 0.36f, cloth.Y + 61f), gold * 0.84f, 0f, Vector2.Zero, 0.72f, SpriteEffects.None, 1f);
    }

    private static void DrawUpgradeConduitNetwork(SpriteBatch batch, Vector2 helmCenter, float phase, Color gold)
    {
        // Four independent infrastructure feeds converge beneath the central navigation dais.
        // These are visual-only conduits: no gameplay bonus is enabled by this pass.
        (Vector2 Offset, Color Color)[] feeds =
        {
            (new Vector2(-448f, 300f), new Color(247, 179, 82)),
            (new Vector2(384f, 300f), new Color(92, 207, 232)),
            (new Vector2(-256f, 364f), new Color(127, 151, 220)),
            (new Vector2(192f, 364f), new Color(205, 113, 232)),
        };

        foreach ((Vector2 offset, Color color) in feeds)
        {
            Vector2 start = helmCenter + offset;
            Vector2 elbow = new(start.X, helmCenter.Y + 122f);
            Vector2 end = new(helmCenter.X, helmCenter.Y + 122f);
            DrawLine(batch, start, elbow, 7f, new Color(41, 31, 42) * 0.80f);
            DrawLine(batch, elbow, end, 7f, new Color(41, 31, 42) * 0.80f);
            DrawLine(batch, start, elbow, 3f, color * 0.50f);
            DrawLine(batch, elbow, end, 3f, color * 0.50f);

            for (int i = 0; i < 4; i++)
            {
                float t = (phase * 0.045f + i * 0.25f) % 1f;
                Vector2 p = Vector2.Lerp(elbow, end, t);
                DrawDiamondRune(batch, p, 5f, color * 0.46f);
            }
        }

        DrawArcaneSigil(batch, new Vector2(helmCenter.X, helmCenter.Y + 122f), 34f, gold * 0.34f, -phase * 0.16f);
    }

    private void DrawUpgradeSocket(
        SpriteBatch batch,
        Vector2 center,
        AirshipUpgradeSystem system,
        int level,
        float phase,
        Color gold)
    {
        level = Math.Clamp(level, 0, AirshipUpgradeMenu.MaxLevel);
        Color systemColor = system switch
        {
            AirshipUpgradeSystem.Engine => new Color(247, 179, 82),
            AirshipUpgradeSystem.Navigation => new Color(92, 207, 232),
            AirshipUpgradeSystem.Hull => new Color(127, 151, 220),
            AirshipUpgradeSystem.Reactor => new Color(205, 113, 232),
            _ => new Color(180, 160, 200),
        };
        Texture2D? visual = this.GetAirshipUpgradeVisuals();
        if (visual is not null)
        {
            const int cell = 96;
            Rectangle source = new((int)system * cell, level * cell, cell, cell);
            Vector2 origin = new(cell / 2f, 72f);
            float bob = level <= 0 ? 0f : MathF.Sin(phase * (0.9f + level * 0.08f) + (int)system) * 1.5f;
            batch.Draw(
                visual,
                center + new Vector2(0f, 10f + bob),
                source,
                Color.White * (level <= 0 ? 0.76f : 0.96f),
                0f,
                origin,
                1f,
                SpriteEffects.None,
                1f
            );
        }

        float active = level <= 0 ? 0.18f : 0.34f + level * 0.10f;
        DrawArcaneSigil(batch, center, 28f + level * 3f, systemColor * active, phase * (0.22f + level * 0.09f));
        DrawCrystalPylon(
            batch,
            new Vector2(center.X, center.Y + 18f),
            14f + level * 3f,
            systemColor * (0.34f + level * 0.10f),
            gold * (0.24f + level * 0.10f)
        );
        for (int pip = 0; pip < AirshipUpgradeMenu.MaxLevel; pip++)
        {
            int x = (int)center.X - 18 + pip * 18;
            Color pipColor = pip < level ? systemColor * 0.92f : new Color(93, 82, 112) * 0.52f;
            DrawRect(batch, new Rectangle(x, (int)center.Y + 26, 9, 5), pipColor);
        }
        if (level >= 2)
            DrawDiamondRune(batch, new Vector2(center.X, center.Y - 28f - level * 3f), 8f + level * 2f, systemColor * 0.68f);
        if (level >= 3)
            DrawArcaneSparkles(batch, center, 44f, 6, phase * 1.4f, Color.White * 0.48f);
    }

    private static void DrawArcaneSigil(SpriteBatch batch, Vector2 center, float radius, Color color, float phase)
    {
        const int segments = 16;
        for (int i = 0; i < segments; i++)
        {
            float angle = phase + i * MathHelper.TwoPi / segments;
            float x = center.X + MathF.Cos(angle) * radius;
            float y = center.Y + MathF.Sin(angle) * radius * 0.52f;
            int size = i % 2 == 0 ? 7 : 5;
            DrawRect(batch, new Rectangle((int)x - size / 2, (int)y - size / 2, size, size), color);
        }

        for (int i = 0; i < 4; i++)
        {
            float angle = phase * 0.35f + i * MathHelper.PiOver2;
            DrawRotorStroke(batch, center, angle, radius * 0.78f, 3f, color * 0.62f);
        }
    }

    private static void DrawCrystalPylon(SpriteBatch batch, Vector2 baseCenter, float height, Color crystal, Color trim)
    {
        int h = Math.Max(20, (int)height);
        int x = (int)baseCenter.X;
        int y = (int)baseCenter.Y;
        DrawRect(batch, new Rectangle(x - 10, y - h, 20, h), crystal * 0.76f);
        DrawRect(batch, new Rectangle(x - 6, y - h - 12, 12, 16), crystal);
        DrawRect(batch, new Rectangle(x - 13, y - 5, 26, 7), trim * 0.74f);
        DrawRect(batch, new Rectangle(x - 3, y - h + 5, 6, Math.Max(8, h - 12)), Color.White * 0.22f);
    }

    private static void DrawManaLane(SpriteBatch batch, Vector2 start, Vector2 end, Color color, float phase)
    {
        Vector2 delta = end - start;
        float length = delta.Length();
        if (length < 1f)
            return;

        float angle = MathF.Atan2(delta.Y, delta.X);
        DrawRotorStroke(batch, start, angle, length, 3f, color * 0.52f);
        for (int i = 0; i < 7; i++)
        {
            float t = (i / 7f + phase * 0.075f) % 1f;
            if (t < 0f)
                t += 1f;
            Vector2 p = Vector2.Lerp(start, end, t);
            int size = i % 2 == 0 ? 6 : 4;
            DrawRect(batch, new Rectangle((int)p.X - size / 2, (int)p.Y - size / 2, size, size), color);
        }
    }

    private static void DrawArcaneSparkles(SpriteBatch batch, Vector2 center, float radius, int count, float phase, Color color)
    {
        for (int i = 0; i < count; i++)
        {
            float angle = phase * (0.35f + (i % 3) * 0.11f) + i * MathHelper.TwoPi / Math.Max(1, count);
            float orbit = radius * (0.55f + (i % 5) * 0.09f);
            float x = center.X + MathF.Cos(angle) * orbit;
            float y = center.Y + MathF.Sin(angle) * orbit * 0.62f;
            float twinkle = 0.55f + 0.35f * MathF.Sin(phase * 2.2f + i * 1.7f);
            int size = i % 4 == 0 ? 5 : 3;
            DrawRect(batch, new Rectangle((int)x - size / 2, (int)y - size / 2, size, size), color * twinkle);
        }
    }

    private static void DrawDiamondRune(SpriteBatch batch, Vector2 center, float radius, Color color)
    {
        float r = Math.Max(5f, radius);
        float side = r * 0.72f;
        DrawRotorStroke(batch, new Vector2(center.X, center.Y - r), MathHelper.PiOver4, side * 1.45f, 3f, color);
        DrawRotorStroke(batch, new Vector2(center.X + r, center.Y), MathHelper.PiOver4 * 3f, side * 1.45f, 3f, color);
        DrawRotorStroke(batch, new Vector2(center.X, center.Y + r), -MathHelper.PiOver4 * 3f, side * 1.45f, 3f, color);
        DrawRotorStroke(batch, new Vector2(center.X - r, center.Y), -MathHelper.PiOver4, side * 1.45f, 3f, color);
        DrawRect(batch, new Rectangle((int)center.X - 3, (int)center.Y - 3, 7, 7), Color.White * 0.48f);
    }

    private static void DrawBridgeConsole(SpriteBatch batch, Vector2 origin, Color primary, Color secondary, Color gold, float phase)
    {
        DrawRect(batch, new Rectangle((int)origin.X - 58, (int)origin.Y - 34, 116, 70), new Color(45, 37, 58) * 0.96f);
        DrawRect(batch, new Rectangle((int)origin.X - 48, (int)origin.Y - 24, 96, 48), new Color(77, 62, 91) * 0.94f);
        DrawRect(batch, new Rectangle((int)origin.X - 38, (int)origin.Y - 14, 76, 5), gold * 0.56f);
        DrawRect(batch, new Rectangle((int)origin.X - 30, (int)origin.Y + 4, 60, 5), secondary * 0.58f);
        DrawArcaneSigil(batch, new Vector2(origin.X, origin.Y + 30f), 22f, primary * 0.54f, phase * 0.45f);
    }

    private static void DrawCloudBand(SpriteBatch batch, Rectangle bounds, int yOffset, float drift, Color color)
    {
        int period = 340;
        int shift = ((int)drift % period + period) % period;
        for (int i = -1; i < 5; i++)
        {
            int x = bounds.X + i * period + shift - 80;
            int y = bounds.Y + yOffset + (i % 2) * 16;
            DrawClippedRect(batch, bounds, new Rectangle(x, y, 118, 13), color * 0.72f);
            DrawClippedRect(batch, bounds, new Rectangle(x + 24, y - 11, 72, 15), color * 0.82f);
            DrawClippedRect(batch, bounds, new Rectangle(x + 57, y + 8, 96, 10), color * 0.58f);
        }
    }

    private static void DrawStarfield(SpriteBatch batch, Rectangle bounds, int count, float phase, Color color)
    {
        int drift = (int)(phase * 9f);
        for (int i = 0; i < count; i++)
        {
            int x = bounds.X + ((i * 79 + drift) % Math.Max(1, bounds.Width) + bounds.Width) % bounds.Width;
            int y = bounds.Y + ((i * 47 + i * i * 3) % Math.Max(1, bounds.Height));
            float twinkle = 0.48f + 0.42f * MathF.Sin(phase * 2.1f + i * 0.83f);
            int size = i % 7 == 0 ? 4 : 2;
            DrawRect(batch, new Rectangle(x, y, size, size), color * twinkle);
        }
    }

    private static void DrawWorldMarker(SpriteBatch batch, Point tile, Color color)
    {
        Vector2 screen = Game1.GlobalToLocal(Game1.viewport, new Vector2(tile.X * 64f + 32f, tile.Y * 64f + 44f));
        DrawRect(batch, new Rectangle((int)screen.X - 16, (int)screen.Y + 8, 32, 4), color * 0.58f);
        DrawDiamondRune(batch, new Vector2(screen.X, screen.Y), 8f, color * 0.82f);
    }

    private static void DrawRect(SpriteBatch batch, Rectangle rectangle, Color color)
    {
        if (rectangle.Width <= 0 || rectangle.Height <= 0)
            return;
        batch.Draw(Game1.staminaRect, rectangle, color);
    }

    private static void DrawClippedRect(SpriteBatch batch, Rectangle bounds, Rectangle rectangle, Color color)
    {
        Rectangle clipped = Rectangle.Intersect(bounds, rectangle);
        if (clipped.Width <= 0 || clipped.Height <= 0)
            return;
        DrawRect(batch, clipped, color);
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

    internal bool CanDrawForestGateForLocalPlayer()
    {
        if (!Context.IsWorldReady || Game1.currentLocation is null)
            return false;
        return (this.Save.Data.AirshipUnlocked || this.TestGateAccessActive)
            && IsSkyDockLocation(Game1.currentLocation);
    }

    internal bool ShouldDrawForestGateAfterPlayer(Farmer farmer)
    {
        if (!this.CanDrawForestGateForLocalPlayer() || farmer is null)
            return false;
        Point dock = this.ResolveSkyDockTile();
        int playerTileY = (int)(farmer.Position.Y / 64f);
        // Above/behind the threshold: arch is foreground. At or below the threshold: farmer is
        // physically in front, so the gate must be queued before the farmer draw call.
        return playerTileY <= dock.Y + 1;
    }

    internal void DrawForestGateAtFarmerDepth(SpriteBatch batch)
    {
        if (!this.CanDrawForestGateForLocalPlayer())
            return;
        this.DrawSkyDock(batch, this.ResolveSkyDockTile());
    }

    private static Point ResolveForestGateLandingTile(GameLocation forest, Point dock)
    {
        Point[] candidates =
        {
            new(dock.X, dock.Y + 4), new(dock.X - 1, dock.Y + 4), new(dock.X + 1, dock.Y + 4),
            new(dock.X, dock.Y + 3), new(dock.X - 1, dock.Y + 3), new(dock.X + 1, dock.Y + 3),
            new(dock.X - 2, dock.Y + 3), new(dock.X + 2, dock.Y + 3),
        };
        foreach (Point p in candidates)
        {
            try
            {
                Vector2 v = new(p.X, p.Y);
                if (!forest.IsTileBlockedBy(v)
                    && !forest.Objects.ContainsKey(v)
                    && !forest.terrainFeatures.ContainsKey(v))
                    return p;
            }
            catch { }
        }
        return FindClearTileNear(forest, new Point(dock.X, dock.Y + 4));
    }

    private static bool IsSkyDockLocation(GameLocation? location)
        => location?.NameOrUniqueName.Equals(SkyDockLocationName, StringComparison.OrdinalIgnoreCase) == true;

    private static bool PlayerIsNear(Point tile)
        => PlayerIsNear(tile, BoardingUseDistance);

    private static bool PlayerIsNear(Point tile, float useDistance)
    {
        Vector2 center = new(tile.X * 64f + 32f, tile.Y * 64f + 32f);
        Vector2 player = Game1.player.Position + new Vector2(32f, 32f);
        return Vector2.DistanceSquared(center, player) <= useDistance * useDistance;
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
