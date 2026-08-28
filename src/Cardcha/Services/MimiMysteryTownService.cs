using System.Collections;
using System.Reflection;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Newtonsoft.Json.Linq;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.GameData.Characters;
using StardewValley.Menus;

namespace Cardcha.Services;

/// <summary>
/// v0.1.17-alpha.11.38: MiMi mystery + merchant NPC runtime.
/// Before the first Scrap she keeps the temporary 10:00-15:00 Town mystery routine for testing.
/// After the Wizard handoff, trading is available immediately on the same weekday from 11:00-17:00:
/// Town on normal days, or inside the WizardHouse during rain/harsh weather.
/// </summary>
internal sealed class MimiMysteryTownService
{
    private enum FlightState
    {
        None,
        Arriving,
        Departing
    }

    public const string NpcId = "Ronvotri.Cardcha_MiMi";

    private const string CharacterAsset = "Characters/Ronvotri.Cardcha_MiMi";
    private const string PortraitAsset = "Portraits/Ronvotri.Cardcha_MiMi";
    private const string ScheduleAsset = "Characters/schedules/Ronvotri.Cardcha_MiMi";
    private const string DialogueAsset = "Characters/Dialogue/Ronvotri.Cardcha_MiMi";

    // Engine-compatible 64x64 portrait fallback only. Runtime dialogue portraits are generated in memory from MimiPortraitsPath.
    private const string MimiNativePortraitsPath = "assets/mimi_npc_portraits.png";
    private const string MimiPortraitsPath = "assets/mimi_portraits.png";
    private const string MimiWalkSheetPath = "assets/mimi_walk.png";
    private const string MimiSchedulePath = "assets/mimi_schedule.json";
    private const string MimiDialoguePath = "assets/mimi_dialogue.json";

    private static readonly Vector2 TownAnchor = new(45f * 64f, 62f * 64f);
    private static readonly Vector2 HiddenWizardPosition = new(-100f * 64f, -100f * 64f);
    private const float TalkDistance = 190f;
    private const int ArrivalStartTime = 1000;
    private const int DepartureTime = 1500;
    private const int LateDepartureGraceEndTime = 1600;
    private const int MerchantStartTime = 1100;
    private const int MerchantEndTime = 1700;
    private const int FlightDurationMs = 2600;
    private const float WanderSpeedPixelsPerSecond = 44f;
    private const int WanderPauseMinMs = 3200;
    private const int WanderPauseMaxMs = 6500;

    private static readonly Vector2[] WanderOffsets =
    {
        Vector2.Zero,
        new(48f, 0f),
        new(96f, 0f),
        new(96f, -32f),
        new(48f, -32f),
        new(0f, -32f)
    };

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly Action OpenMimiShop;
    private readonly WorldActorService WorldActors;
    private readonly Func<bool> StoryOwnsMimiActor;

    private Texture2D? MasterPortraitSheet;
    private Texture2D? RuntimePortraitSheet;
    private int TalkIndex;
    private bool LoggedNativeFound;
    private bool ArrivedToday;
    private bool DepartedToday;
    private FlightState Flight;
    private long FlightStartedMs;
    private Vector2 FlightStartWorld = TownAnchor;
    private Vector2 FlightTargetWorld = TownAnchor;
    private Vector2 WanderTarget = TownAnchor;
    private long NextWanderDecisionAtMs;
    private long LastWanderUpdateAtMs;
    private int WanderTargetIndex;
    private int WanderFacing = 2;
    private bool MerchantPepTalkPendingOpen;
    private bool OfficialMerchantArrival;
    private bool OfficialMerchantDeparture;
    private bool KnownNameAssetRefreshed;

    public MimiMysteryTownService(
        IModHelper helper,
        IMonitor monitor,
        SaveService save,
        Action openMimiShop,
        WorldActorService worldActors,
        Func<bool> storyOwnsMimiActor)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.OpenMimiShop = openMimiShop;
        this.WorldActors = worldActors;
        this.StoryOwnsMimiActor = storyOwnsMimiActor;
    }

    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)
    {
        if (e.Name.IsEquivalentTo(CharacterAsset))
        {
            e.LoadFromModFile<Texture2D>(MimiWalkSheetPath, AssetLoadPriority.Medium);
            return;
        }

        if (e.Name.IsEquivalentTo(PortraitAsset))
        {
            e.LoadFromModFile<Texture2D>(MimiNativePortraitsPath, AssetLoadPriority.Medium);
            return;
        }

        if (e.Name.IsEquivalentTo(ScheduleAsset))
        {
            // Intentionally blank: runtime controls exact 10:00 arrival / 15:00 departure itself (temporary test window).
            e.LoadFromModFile<Dictionary<string, string>>(MimiSchedulePath, AssetLoadPriority.Medium);
            return;
        }

        if (e.Name.IsEquivalentTo(DialogueAsset))
        {
            e.LoadFromModFile<Dictionary<string, string>>(MimiDialoguePath, AssetLoadPriority.Medium);
            return;
        }

        // Optional integration for Bouhm NPC Map Locations. Its official author API is a
        // content asset of Dictionary<string, JObject>; registering MiMi here ensures the dynamic
        // Cardcha NPC gets a marker config entry even though she starts the day hidden off-map.
        if (e.NameWithoutLocale.IsEquivalentTo("Mods/Bouhm.NPCMapLocations/NPCs"))
        {
            e.Edit(asset =>
            {
                IDictionary<string, JObject> data = asset.AsDictionary<string, JObject>().Data;
                data[NpcId] = new JObject
                {
                    ["MarkerCropOffset"] = 0
                };
            });
            return;
        }

        if (e.NameWithoutLocale.IsEquivalentTo("Data/Characters"))
        {
            e.Edit(asset =>
            {
                IDictionary<string, CharacterData> data = asset.AsDictionary<string, CharacterData>().Data;
                CharacterData mimi = new();

                SetProperty(mimi, "DisplayName", this.IsMimiIdentityKnown() ? "MiMi" : "???");
                SetProperty(mimi, "TextureName", NpcId);
                SetProperty(mimi, "Gender", "Female");
                SetProperty(mimi, "Age", "Teen");
                SetProperty(mimi, "Manner", "Neutral");
                SetProperty(mimi, "SocialAnxiety", "Outgoing");
                SetProperty(mimi, "Optimism", "Positive");
                SetProperty(mimi, "HomeRegion", "Other");
                SetProperty(mimi, "CanBeRomanced", false);
                SetProperty(mimi, "CanSocialize", "FALSE");
                SetProperty(mimi, "CanReceiveGifts", false);
                SetProperty(mimi, "CanGreetNearbyCharacters", false);
                SetProperty(mimi, "IntroductionsQuest", false);
                SetProperty(mimi, "PerfectionScore", false);
                SetProperty(mimi, "Calendar", "HiddenAlways");
                SetProperty(mimi, "SocialTab", "HiddenAlways");
                SetProperty(mimi, "EndSlideShow", "Hidden");
                SetProperty(mimi, "SpawnIfMissing", false);
                SetProperty(mimi, "Breather", false);
                SetProperty(mimi, "ForceOneTileWide", true);

                // Native world renderer uses the official 32x48 MiMi walk master directly.
                // The NPC actor scale preserves the approved in-game size.
                SetPointProperty(mimi, "Size", 32, 48);
                SetRectangleProperty(mimi, "MugShotSourceRect", 0, 0, 16, 15);
                SetPointProperty(mimi, "EmoteOffset", 0, -24);
                SetProperty(mimi, "Shadow", new CharacterShadowData
                {
                    Visible = true,
                    // Keep the shadow compact, but large enough to remain visible under the
                    // scaled 32x48 mystery sprite on bright Town tiles.
                    Offset = Point.Zero,
                    Scale = 1.28f
                });
                SetHome(mimi, "WizardHouse", 4, 6, "down");

                data[NpcId] = mimi;

                // ChaCha is also a real NPC actor now, so give Stardew explicit hidden character data
                // and a deliberately smaller native shadow instead of the oversized default.
                CharacterData chacha = new();
                SetProperty(chacha, "DisplayName", "ChaCha");
                SetProperty(chacha, "TextureName", WorldActorService.ChaChaNpcId);
                SetProperty(chacha, "CanSocialize", "FALSE");
                SetProperty(chacha, "CanReceiveGifts", false);
                SetProperty(chacha, "CanGreetNearbyCharacters", false);
                SetProperty(chacha, "IntroductionsQuest", false);
                SetProperty(chacha, "PerfectionScore", false);
                SetProperty(chacha, "Calendar", "HiddenAlways");
                SetProperty(chacha, "SocialTab", "HiddenAlways");
                SetProperty(chacha, "EndSlideShow", "Hidden");
                SetProperty(chacha, "SpawnIfMissing", false);
                SetProperty(chacha, "Breather", false);
                SetProperty(chacha, "ForceOneTileWide", true);
                SetPointProperty(chacha, "Size", 32, 32);
                SetProperty(chacha, "Shadow", new CharacterShadowData
                {
                    Visible = true,
                    Offset = Point.Zero,
                    Scale = 0.82f
                });
                data[WorldActorService.ChaChaNpcId] = chacha;
            });
        }
    }

    public bool IsVisibleNow()
        => Context.IsWorldReady
           && !this.Save.Data.FirstScrapTriggered
           && this.Flight == FlightState.None
           && Game1.timeOfDay >= ArrivalStartTime
           && Game1.timeOfDay < DepartureTime
           && FindNativeNpc()?.currentLocation?.NameOrUniqueName.Equals("Town", StringComparison.OrdinalIgnoreCase) == true
           && !Game1.eventUp;

    public void OnSaveLoaded()
    {
        this.ResetRuntimeForDay();
        this.KnownNameAssetRefreshed = false;
        this.EnsureTextures();
        this.WorldActors.EnsureMimiActor();
        this.EnsureKnownIdentityState();
        this.EnforcePhaseState();
    }

    public void OnDayStarted()
    {
        this.ResetRuntimeForDay();
        this.WorldActors.EnsureMimiActor();
        this.EnforcePhaseState();
    }

    public void OnReturnedToTitle()
    {
        this.TalkIndex = 0;
        this.LoggedNativeFound = false;
        this.ArrivedToday = false;
        this.DepartedToday = false;
        this.Flight = FlightState.None;
        this.FlightStartedMs = 0;
        this.FlightStartWorld = TownAnchor;
        this.FlightTargetWorld = TownAnchor;
        this.WanderTarget = TownAnchor;
        this.NextWanderDecisionAtMs = 0;
        this.LastWanderUpdateAtMs = 0;
        this.WanderTargetIndex = 0;
        this.WanderFacing = 2;
        this.MerchantPepTalkPendingOpen = false;
        this.OfficialMerchantArrival = false;
        this.OfficialMerchantDeparture = false;
        this.KnownNameAssetRefreshed = false;
        this.Helper.Events.Display.MenuChanged -= this.OnMerchantPepTalkMenuChanged;
    }

    public void OnTimeChanged(object? sender, TimeChangedEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        if (this.IsMerchantRoutineActive())
        {
            if (e.NewTime == MerchantStartTime
                && !IsHarshMerchantWeather()
                && Game1.currentLocation?.NameOrUniqueName.Equals("Town", StringComparison.OrdinalIgnoreCase) == true)
            {
                this.StartArrivalFlight(officialMerchant: true);
            }
            else if (e.NewTime == MerchantEndTime
                && !IsHarshMerchantWeather()
                && Game1.currentLocation?.NameOrUniqueName.Equals("Town", StringComparison.OrdinalIgnoreCase) == true)
            {
                this.StartDepartureFlight(officialMerchant: true);
            }
            else if (e.NewTime == MerchantStartTime || e.NewTime == MerchantEndTime)
                this.EnforceMerchantState();
            return;
        }

        if (this.Save.Data.FirstScrapTriggered)
            return;

        if (e.NewTime == ArrivalStartTime)
        {
            StartArrivalFlight();
            return;
        }

        if (e.NewTime >= DepartureTime && !this.DepartedToday && this.Flight == FlightState.None)
        {
            bool playerInTown = Game1.currentLocation?.NameOrUniqueName.Equals(
                "Town",
                StringComparison.OrdinalIgnoreCase) == true;

            // Don't run the broom animation off-screen. Keep MiMi waiting in Town for a short
            // grace window so arriving at 15:10/15:20 still lets the player actually see her leave.
            if (playerInTown && e.NewTime < LateDepartureGraceEndTime)
            {
                StartDepartureFlight();
            }
            else if (e.NewTime >= LateDepartureGraceEndTime)
            {
                HideNativeOffMap();
                this.DepartedToday = true;
            }
        }
    }

    public void OnUpdateTicked()
    {
        if (!Context.IsWorldReady)
            return;

        this.EnsureKnownIdentityState();

        if (this.IsMerchantRoutineActive())
        {
            if (this.Flight != FlightState.None)
            {
                this.UpdateFlight();
                NPC? departing = FindNativeNpc();
                if (departing is not null)
                    SetNpcDisplayName(departing, "MiMi");
                return;
            }

            this.EnforceMerchantState();
            NPC? merchant = FindNativeNpc();
            if (merchant is not null)
            {
                SetNpcDisplayName(merchant, "MiMi");
                merchant.hideShadow.Value = false;
            }
            if (!IsHarshMerchantWeather())
                this.UpdateNativeWander(officialMerchant: true);
            if (!this.Save.Data.ChaChaLoaned)
            {
                this.SyncChaChaWithMimi();
                this.WorldActors.UpdateChaChaEmotes(dialogueActive: Game1.activeClickableMenu is DialogueBox);
            }
            return;
        }

        if (this.Save.Data.FirstScrapTriggered)
        {
            this.Flight = FlightState.None;
            this.EnforceStoryVisibility();
            // Story/follower service owns ChaCha from this point onward.
            return;
        }

        this.UpdateFlight();

        // This also corrects stale/native schedule state from older installs/saves.
        if (this.Flight == FlightState.None)
        {
            this.EnforceCurrentTimeState(allowAnimation: Game1.currentLocation?.NameOrUniqueName.Equals("Town", StringComparison.OrdinalIgnoreCase) == true);
            this.UpdateNativeWander();
            this.SyncChaChaWithMimi();
            this.WorldActors.UpdateChaChaEmotes(dialogueActive: Game1.activeClickableMenu is DialogueBox);
        }
        // During broom flight, UpdateFlight owns BOTH MiMi and ChaCha so the normal follower
        // sync cannot overwrite altitude/drawOffset and create a flicker or size-jump illusion.

        NPC? native = FindNativeNpc();
        if (native is not null)
        {
            SetNpcDisplayName(native, this.IsMimiIdentityKnown() ? "MiMi" : "???");
            if (!this.IsMimiIdentityKnown())
                SuppressVanillaGreetingLeak();
        }

        if (native is not null && !this.LoggedNativeFound)
        {
            this.LoggedNativeFound = true;
            this.Monitor.Log(
                $"MiMi native NPC runtime found: {native.Name} at {native.currentLocation?.NameOrUniqueName ?? "<none>"}.",
                LogLevel.Trace
            );
        }

        // Mystery-phase townsfolk reactions are disabled for now; MiMi should remain more mysterious.
        // this.TryVillagerMysteryReaction();
    }

    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        if (this.IsMerchantRoutineActive())
        {
            if (this.Save.Data.MimiMeetupCompleted)
                return;
            this.TryOpenMerchant(e);
            return;
        }

        if (this.Save.Data.FirstScrapTriggered || this.Flight != FlightState.None)
            return;

        if (!e.Button.IsActionButton())
            return;

        if (Game1.activeClickableMenu is not null || Game1.dialogueUp || Game1.eventUp)
            return;

        if (Game1.timeOfDay < ArrivalStartTime || Game1.timeOfDay >= DepartureTime)
            return;

        NPC? native = FindNativeNpc() ?? this.WorldActors.EnsureMimiActor();
        if (native is null
            || native.isInvisible.Value
            || native.currentLocation != Game1.currentLocation
            || native.currentLocation?.NameOrUniqueName.Equals("Town", StringComparison.OrdinalIgnoreCase) != true)
        {
            return;
        }

        Vector2 actor = native.Position;

        Vector2 playerCenter = Game1.player.Position + new Vector2(32f, 32f);
        Vector2 actorCenter = actor + new Vector2(32f, 48f);

        if (Vector2.DistanceSquared(playerCenter, actorCenter) > TalkDistance * TalkDistance)
            return;

        this.Helper.Input.Suppress(e.Button);
        Game1.player.Halt();

        if (native is not null)
        {
            // Native collision/depth is authoritative now. Never teleport MiMi just because the
            // player pressed talk; pin her current position and simply turn her toward the player.
            this.WanderTarget = native.Position;
            this.NextWanderDecisionAtMs = CurrentGameMs() + 1800;
            this.LastWanderUpdateAtMs = CurrentGameMs();
            native.faceTowardFarmerForPeriod(1600, 3, false, Game1.player);
        }

        int mysteryLine = this.TalkIndex % 5;
        string key = $"story.mystery.{mysteryLine}";
        this.TalkIndex++;
        ShowMysteryDialogue(ModEntry.T(key), MysteryPortraitCommand(mysteryLine));
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        // Intentionally empty in alpha.11.37. MiMi and ChaCha are real world actors
        // in GameLocation.characters; Stardew now owns their depth sorting.
    }

    public bool OwnsMimiWorldActor => this.Flight != FlightState.None;

    public string Describe()
    {
        NPC? native = FindNativeNpc();
        string location = native?.currentLocation?.NameOrUniqueName ?? "<missing>";
        return $"MysteryNativeNpc={(native is not null)} | MysteryVisible={this.IsVisibleNow()} | " +
               $"Flight={this.Flight} | ArrivedToday={this.ArrivedToday} | DepartedToday={this.DepartedToday} | " +
               $"MysteryTalkIndex={this.TalkIndex} | NativeLocation={location} | " +
               $"RuntimeWindow=Town@10:00-15:00 + visible-departure grace to 16:00 | Merchant=Mon-Fri 11:00-17:00 Town/harsh-weather->WizardHouse, same-day after handoff | " +
               $"MerchantActive={this.IsMerchantRoutineActive()} | PlazaAnchor=45,62 | Wander=True | HumanReactionsOnly=True | FirstScrap={this.Save.Data.FirstScrapTriggered}";
    }

    private void ResetRuntimeForDay()
    {
        this.TalkIndex = 0;
        this.LoggedNativeFound = false;
        this.ArrivedToday = Game1.timeOfDay >= ArrivalStartTime;
        this.DepartedToday = false;
        this.Flight = FlightState.None;
        this.FlightStartedMs = 0;
        this.WanderTarget = TownAnchor;
        this.NextWanderDecisionAtMs = CurrentGameMs() + 2800;
        this.LastWanderUpdateAtMs = CurrentGameMs();
        this.WanderTargetIndex = 0;
        this.WanderFacing = 2;
        this.MerchantPepTalkPendingOpen = false;
        this.OfficialMerchantArrival = false;
        this.OfficialMerchantDeparture = false;
        this.Helper.Events.Display.MenuChanged -= this.OnMerchantPepTalkMenuChanged;
    }

    private bool IsMerchantRoutineActive()
    {
        if (!Context.IsWorldReady || !this.Save.Data.MimiMeetupCompleted)
            return false;

        if (IsRestoredCommunityCenterRoute())
            return false;

        int unlockedDay = this.Save.Data.MimiMerchantUnlockedDay;
        bool unlockedNow = unlockedDay < 0 || Game1.Date.TotalDays >= unlockedDay;
        return unlockedNow && IsMerchantWeekday();
    }

    private void EnforcePhaseState()
    {
        if (this.IsMerchantRoutineActive())
        {
            this.EnforceMerchantState();
            return;
        }

        if (this.Save.Data.FirstScrapTriggered)
        {
            this.EnforceStoryVisibility();
            return;
        }

        this.EnforceCurrentTimeState(allowAnimation: false);
    }

    private void EnforceMerchantState()
    {
        if (!this.IsMerchantRoutineActive())
            return;

        // Let the story service finish its short Wizard-house/farm departure animation first.
        // As soon as it releases MiMi, the same-day merchant routine can place her normally.
        if (this.StoryOwnsMimiActor())
            return;

        if (Game1.timeOfDay < MerchantStartTime || Game1.timeOfDay >= MerchantEndTime)
        {
            // alpha.27: HomeService keeps MiMi in her attic outside work hours.
            return;
        }

        // At the exact scheduled arrival tick, keep the ground actor hidden until StartArrivalFlight
        // moves the broom actor to its off-screen start point. This prevents a one-frame MiMi flash
        // at the plaza before the flight begins.
        bool playerInTown = Game1.currentLocation?.NameOrUniqueName.Equals("Town", StringComparison.OrdinalIgnoreCase) == true;
        if (!IsHarshMerchantWeather()
            && Game1.timeOfDay == MerchantStartTime
            && playerInTown
            && !this.ArrivedToday
            && this.Flight == FlightState.None)
        {
            this.HideNativeOffMap();
            return;
        }

        // Trading can start on the handoff day once the story presentation releases MiMi.
        if (IsHarshMerchantWeather())
            this.PlaceNativeInWizardHouseMerchant();
        else
            this.PlaceNativeInTownMerchant();
    }

    private void PlaceNativeInTownMerchant()
    {
        NPC? native = FindNativeNpc() ?? this.WorldActors.EnsureMimiActor();
        GameLocation? town = Game1.getLocationFromName("Town");
        if (native is null || town is null)
            return;

        // Reuse MiMi's familiar plaza spot, but don't teleport her back every tick; doing so
        // previously prevented the official post-handoff NPC from ever walking.
        if (native.currentLocation != town || native.isInvisible.Value)
        {
            MoveNative(native, town, TownAnchor, 2);
            this.WanderTarget = TownAnchor;
            this.NextWanderDecisionAtMs = CurrentGameMs() + 2200;
            this.LastWanderUpdateAtMs = CurrentGameMs();
        }
        else
        {
            this.WorldActors.ConfigureMimiActor(native, broom: false, visible: true);
        }
        SetNpcDisplayName(native, "MiMi");
        native.hideShadow.Value = false;
    }

    private void PlaceNativeInWizardHouseMerchant()
    {
        NPC? native = FindNativeNpc() ?? this.WorldActors.EnsureMimiActor();
        GameLocation? wizardHouse = Game1.getLocationFromName("WizardHouse");
        if (native is null || wizardHouse is null)
            return;

        Vector2 anchor = FindWarpSourceWorld(wizardHouse, "Forest")
            ?? new Vector2(4f * 64f, 8f * 64f);

        // A few tiles inside so she doesn't block the door.
        anchor += new Vector2(96f, -128f);
        MoveNative(native, wizardHouse, anchor, 2);
        SetNpcDisplayName(native, "MiMi");
        native.hideShadow.Value = false;
    }

    private void TryOpenMerchant(ButtonPressedEventArgs e)
    {
        if (!e.Button.IsActionButton()
            || Game1.activeClickableMenu is not null
            || Game1.dialogueUp
            || Game1.eventUp
            || Game1.timeOfDay < MerchantStartTime
            || Game1.timeOfDay >= MerchantEndTime)
        {
            return;
        }

        NPC? native = FindNativeNpc();
        if (native is null || native.currentLocation != Game1.currentLocation)
            return;

        Vector2 playerCenter = Game1.player.Position + new Vector2(32f, 32f);
        Vector2 mimiCenter = native.Position + new Vector2(32f, 64f);
        if (Vector2.DistanceSquared(playerCenter, mimiCenter) > TalkDistance * TalkDistance)
            return;

        this.Helper.Input.Suppress(e.Button);
        Game1.player.Halt();
        native.faceTowardFarmerForPeriod(1200, 3, false, Game1.player);

        if (!this.Save.Data.MimiFirstMerchantPepTalkShown)
        {
            this.Save.Data.MimiFirstMerchantPepTalkShown = true;
            this.Save.Save();
            this.MerchantPepTalkPendingOpen = true;
            this.Helper.Events.Display.MenuChanged -= this.OnMerchantPepTalkMenuChanged;
            this.Helper.Events.Display.MenuChanged += this.OnMerchantPepTalkMenuChanged;
            SetNpcDisplayName(native, "MiMi");
            if (this.TryShowDialogueWithPortrait(native, ModEntry.T("mimi.shop.first-post-handoff") + "$1"))
                return;

            this.Helper.Events.Display.MenuChanged -= this.OnMerchantPepTalkMenuChanged;
            this.MerchantPepTalkPendingOpen = false;
        }

        this.OpenMimiShop();
    }

    private void OnMerchantPepTalkMenuChanged(object? sender, MenuChangedEventArgs e)
    {
        if (!this.MerchantPepTalkPendingOpen)
            return;

        if (e.OldMenu is not DialogueBox || e.NewMenu is not null)
            return;

        this.Helper.Events.Display.MenuChanged -= this.OnMerchantPepTalkMenuChanged;
        this.MerchantPepTalkPendingOpen = false;

        if (Context.IsWorldReady && this.IsMerchantRoutineActive())
            this.OpenMimiShop();
    }

    private static bool IsRestoredCommunityCenterRoute()
    {
        if (!Context.IsWorldReady || Game1.MasterPlayer.mailReceived.Contains("JojaMember"))
            return false;
        try
        {
            return Game1.MasterPlayer.hasCompletedCommunityCenter()
                || Game1.MasterPlayer.mailReceived.Contains("ccIsComplete");
        }
        catch
        {
            return Game1.MasterPlayer.mailReceived.Contains("ccIsComplete");
        }
    }

    private static bool IsMerchantWeekday()
    {
        // Stardew seasons always start on Monday: day 1..5 = Mon..Fri, 6..7 = weekend.
        int dayIndex = (Math.Max(1, Game1.dayOfMonth) - 1) % 7;
        return dayIndex <= 4;
    }

    private static bool IsHarshMerchantWeather()
    {
        if (Game1.isRaining)
            return true;

        // Keep this compatible across 1.6 point releases/modded weather implementations.
        // Rain is the common case; the reflected flags additionally catch thunder, snow,
        // debris-heavy weather, and green rain when those members exist.
        return ReadGame1WeatherFlag("isLightning")
            || ReadGame1WeatherFlag("isSnowing")
            || ReadGame1WeatherFlag("isDebrisWeather")
            || ReadGame1WeatherFlag("isGreenRain");
    }

    private static bool ReadGame1WeatherFlag(string memberName)
    {
        const BindingFlags flags = BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.IgnoreCase;
        try
        {
            object? value = typeof(Game1).GetProperty(memberName, flags)?.GetValue(null)
                ?? typeof(Game1).GetField(memberName, flags)?.GetValue(null);
            return value is bool flag && flag;
        }
        catch
        {
            return false;
        }
    }

    private static Vector2? FindWarpSourceWorld(GameLocation location, string targetToken)
    {
        try
        {
            const BindingFlags flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.IgnoreCase;
            object? warps = location.GetType().GetProperty("warps", flags)?.GetValue(location)
                ?? location.GetType().GetField("warps", flags)?.GetValue(location);

            if (warps is not IEnumerable enumerable)
                return null;

            foreach (object? warp in enumerable)
            {
                if (warp is null)
                    continue;

                string? target = ReadStringMember(warp, "TargetName")
                    ?? ReadStringMember(warp, "TargetLocationName")
                    ?? ReadStringMember(warp, "Target");

                if (target is null || !target.Contains(targetToken, StringComparison.OrdinalIgnoreCase))
                    continue;

                int? x = ReadIntMember(warp, "X");
                int? y = ReadIntMember(warp, "Y");
                if (x.HasValue && y.HasValue)
                    return new Vector2(x.Value * 64f, y.Value * 64f);
            }
        }
        catch
        {
            // Farm/map mods may expose warps differently; use the safe fallback anchor.
        }

        return null;
    }

    private static string? ReadStringMember(object target, string memberName)
    {
        const BindingFlags flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.IgnoreCase;
        object? value = target.GetType().GetProperty(memberName, flags)?.GetValue(target)
            ?? target.GetType().GetField(memberName, flags)?.GetValue(target);
        return value?.ToString();
    }

    private static int? ReadIntMember(object target, string memberName)
    {
        const BindingFlags flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.IgnoreCase;
        object? value = target.GetType().GetProperty(memberName, flags)?.GetValue(target)
            ?? target.GetType().GetField(memberName, flags)?.GetValue(target);

        if (value is null)
            return null;

        try { return Convert.ToInt32(value); }
        catch { return null; }
    }

    private void EnforceCurrentTimeState(bool allowAnimation)
    {
        if (!Context.IsWorldReady || this.Save.Data.FirstScrapTriggered)
            return;

        if (Game1.timeOfDay < ArrivalStartTime)
        {
            HideNativeOffMap();
            return;
        }

        if (Game1.timeOfDay >= DepartureTime)
        {
            bool playerInTown = Game1.currentLocation?.NameOrUniqueName.Equals(
                "Town",
                StringComparison.OrdinalIgnoreCase) == true;

            if (!this.DepartedToday
                && Game1.timeOfDay < LateDepartureGraceEndTime)
            {
                if (allowAnimation && playerInTown && this.Flight == FlightState.None)
                {
                    StartDepartureFlight();
                    return;
                }

                // Keep her native actor in Town during the grace window instead of silently
                // completing the departure while the player is somewhere else.
                PlaceNativeInTown();
                return;
            }

            HideNativeOffMap();
            this.DepartedToday = true;
            return;
        }

        bool playerInTownNow = Game1.currentLocation?.NameOrUniqueName.Equals("Town", StringComparison.OrdinalIgnoreCase) == true;
        if (!this.ArrivedToday && playerInTownNow)
        {
            if (allowAnimation)
                StartArrivalFlight();
            else
                HideNativeOffMap();
            return;
        }

        PlaceNativeInTown();
    }

    private void StartArrivalFlight(bool officialMerchant = false)
    {
        if (this.Flight != FlightState.None
            || this.ArrivedToday
            || (this.Save.Data.FirstScrapTriggered && !officialMerchant))
            return;

        NPC? native = FindNativeNpc() ?? this.WorldActors.EnsureMimiActor();
        GameLocation? town = Game1.getLocationFromName("Town");
        if (native is null || town is null)
            return;

        this.Flight = FlightState.Arriving;
        this.OfficialMerchantArrival = officialMerchant;
        this.FlightStartedMs = CurrentGameMs();
        this.FlightStartWorld = GetOffscreenFlightPoint(town, TownAnchor, enterFromLeft: true);
        this.FlightTargetWorld = TownAnchor;
        this.WorldActors.MoveMimiActor(native, town, this.FlightStartWorld, 1, broom: true, visible: true);
        this.WorldActors.SetMimiFrame(native, 1, 0);
        native.drawOffset = new Vector2(0f, -230f);
        native.drawOnTop = true;
        native.hideShadow.Value = true;
        Game1.playSound("wand");
        this.Monitor.Log(
            officialMerchant
                ? "MiMi official merchant arrival: native broom actor started at 11:00."
                : "MiMi mystery arrival: native broom actor started at 10:00.",
            LogLevel.Info
        );
    }

    private void StartDepartureFlight(bool officialMerchant = false)
    {
        if (this.Flight != FlightState.None || (this.Save.Data.FirstScrapTriggered && !officialMerchant))
            return;

        NPC? native = FindNativeNpc() ?? this.WorldActors.EnsureMimiActor();
        GameLocation? town = Game1.getLocationFromName("Town");
        if (native is null || town is null)
            return;

        this.DepartedToday = false;
        Vector2 start = native.currentLocation == town ? native.Position : TownAnchor;
        this.Flight = FlightState.Departing;
        this.OfficialMerchantDeparture = officialMerchant;
        this.FlightStartedMs = CurrentGameMs();
        this.FlightStartWorld = start;
        this.FlightTargetWorld = GetOffscreenFlightPoint(town, start, enterFromLeft: false);
        this.WorldActors.MoveMimiActor(native, town, start, 0, broom: true, visible: true);
        this.WorldActors.SetMimiFrame(native, 0, 0);
        Game1.playSound("wand");
        this.Monitor.Log("MiMi mystery departure: native broom actor started at 15:00.", LogLevel.Info);
    }

    private void UpdateFlight()
    {
        if (this.Flight == FlightState.None)
            return;

        NPC? native = FindNativeNpc() ?? this.WorldActors.EnsureMimiActor();
        GameLocation? town = Game1.getLocationFromName("Town");
        if (native is null || town is null)
            return;

        long elapsed = CurrentGameMs() - this.FlightStartedMs;
        float raw = Math.Clamp(elapsed / (float)FlightDurationMs, 0f, 1f);
        float t = SmoothStep(raw);
        int frame = (int)(CurrentGameMs() / 110L) % 4;

        if (this.Flight == FlightState.Arriving)
        {
            Vector2 world = Vector2.Lerp(this.FlightStartWorld, this.FlightTargetWorld, t);
            float altitude = MathHelper.Lerp(230f, 0f, t);
            int facing = this.FlightTargetWorld.X >= this.FlightStartWorld.X ? 1 : 3;
            this.WorldActors.MoveMimiActor(native, town, world, facing, broom: true, visible: true);
            this.WorldActors.SetMimiFrame(native, facing, frame);
            native.drawOffset = new Vector2(0f, -altitude);
            native.drawOnTop = true;
            native.hideShadow.Value = true;
            native.rotation = (1f - t) * -0.045f + (float)Math.Sin(CurrentGameMs() / 330.0) * 0.006f;
            if (!this.OfficialMerchantArrival)
            {
                NPC? chacha = this.WorldActors.EnsureChaChaActor(
                    town,
                    world + new Vector2(-64f, 16f),
                    facing == 1 ? 3 : 2,
                    frame,
                    machine: false
                );
                if (chacha is not null)
                {
                    chacha.drawOffset = new Vector2(0f, -altitude + 10f);
                    chacha.drawOnTop = true;
                    chacha.hideShadow.Value = true;
                    chacha.rotation = 0f;
                }
            }
        }
        else
        {
            // 11.43: world-Y is NOT altitude. Moving MiMi north through Town made her visibly
            // phase into houses. Keep the ground anchor in open street space, raise the rendered
            // sprite with drawOffset, then cruise horizontally while drawOnTop makes her clearly
            // pass above roofs/buildings.
            const float liftFraction = 0.48f;
            Vector2 groundWorld;
            float visualAltitude;
            int facing;

            if (raw < liftFraction)
            {
                float liftRaw = raw / liftFraction;
                float lift = SmoothStep(liftRaw);
                groundWorld = this.FlightStartWorld + new Vector2(MathHelper.Lerp(0f, 24f, lift), 0f);
                visualAltitude = MathHelper.Lerp(0f, 220f, lift);
                facing = 0;
            }
            else
            {
                float cruiseRaw = (raw - liftFraction) / (1f - liftFraction);
                float cruise = SmoothStep(cruiseRaw);
                groundWorld = Vector2.Lerp(this.FlightStartWorld + new Vector2(24f, 0f), this.FlightTargetWorld, cruise);
                visualAltitude = MathHelper.Lerp(220f, 248f, cruise);
                facing = 1;
            }

            this.WorldActors.MoveMimiActor(native, town, groundWorld, facing, broom: true, visible: true);
            this.WorldActors.SetMimiFrame(native, facing, frame);
            native.drawOffset = new Vector2(0f, -visualAltitude);
            native.drawOnTop = true;
            native.hideShadow.Value = true;
            native.rotation = raw < liftFraction
                ? -0.012f
                : -0.035f + (float)Math.Sin(CurrentGameMs() / 350.0) * 0.008f;

            NPC? chacha = this.OfficialMerchantDeparture
                ? null
                : this.WorldActors.EnsureChaChaActor(
                    town,
                    groundWorld + new Vector2(-64f, 16f),
                    facing == 1 ? 3 : 2,
                    frame,
                    machine: false
                );
            if (chacha is not null)
            {
                chacha.drawOffset = new Vector2(0f, -visualAltitude + 10f);
                chacha.drawOnTop = true;
                chacha.hideShadow.Value = true;
                chacha.rotation = 0f;
            }
        }

        if (elapsed < FlightDurationMs)
            return;

        FlightState finished = this.Flight;
        bool officialArrival = this.OfficialMerchantArrival;
        bool officialDeparture = this.OfficialMerchantDeparture;
        this.Flight = FlightState.None;
        this.OfficialMerchantArrival = false;
        this.OfficialMerchantDeparture = false;
        this.FlightStartWorld = TownAnchor;
        this.FlightTargetWorld = TownAnchor;
        native.rotation = 0f;

        if (finished == FlightState.Arriving)
        {
            this.ArrivedToday = true;
            this.WorldActors.MoveMimiActor(native, town, TownAnchor, 2, broom: false, visible: true);
            native.drawOffset = Vector2.Zero;
            native.drawOnTop = false;
            native.hideShadow.Value = false;
            this.WorldActors.SetMimiFrame(native, 2, 0);
            this.WanderTarget = TownAnchor;
            this.NextWanderDecisionAtMs = CurrentGameMs() + 2600;
            this.LastWanderUpdateAtMs = CurrentGameMs();
            if (officialArrival)
                SetNpcDisplayName(native, "MiMi");
            Game1.playSound("smallSelect");
        }
        else
        {
            this.DepartedToday = true;
            HideNativeOffMap();
            if (!officialDeparture)
                this.WorldActors.HideChaChaActor();
        }
    }

    private Vector2 GetOffscreenFlightPoint(GameLocation location, Vector2 reference, bool enterFromLeft)
    {
        const float margin = 260f;
        if (Game1.currentLocation == location)
        {
            float left = Game1.viewport.X - margin;
            float right = Game1.viewport.X + Game1.viewport.Width + margin;
            float minY = Game1.viewport.Y + 120f;
            float maxY = Game1.viewport.Y + Game1.viewport.Height - 120f;
            float y = Math.Clamp(reference.Y, minY, Math.Max(minY, maxY));
            return new Vector2(enterFromLeft ? left : right, y);
        }

        // If Town isn't currently being rendered, still place the actor far enough away that
        // the next visible flight starts/finishes beyond any normal camera width.
        return reference + new Vector2(enterFromLeft ? -1200f : 1200f, 0f);
    }

    private bool IsMimiIdentityKnown()
        => this.Save.Data.MimiMeetupCompleted || this.Save.Data.MachineDelivered;

    private void EnsureKnownIdentityState()
    {
        if (!this.IsMimiIdentityKnown())
            return;

        NPC? native = FindNativeNpc();
        if (native is not null)
            SetNpcDisplayName(native, "MiMi");

        if (this.KnownNameAssetRefreshed)
            return;

        this.KnownNameAssetRefreshed = true;
        try
        {
            // Data/Characters is the fallback source used by DialogueBox for the speaker label.
            // Refresh it once the handoff reveals her identity so later portrait dialogue can't
            // regress to the pre-story "???" label.
            this.Helper.GameContent.InvalidateCache("Data/Characters");
        }
        catch (Exception ex)
        {
            this.Monitor.Log($"Couldn't refresh MiMi's revealed display name cache: {ex.Message}", LogLevel.Trace);
        }
    }

    private void PlaceNativeInTown()
    {
        NPC? native = FindNativeNpc() ?? this.WorldActors.EnsureMimiActor();
        GameLocation? town = Game1.getLocationFromName("Town");
        if (native is null || town is null)
            return;

        bool alreadyInTown = native.currentLocation == town;
        if (!alreadyInTown)
        {
            MoveNative(native, town, TownAnchor, 2);
            this.WanderTarget = TownAnchor;
            this.NextWanderDecisionAtMs = CurrentGameMs() + 2600;
            this.LastWanderUpdateAtMs = CurrentGameMs();
        }
        else
        {
            // Repair stale flight/hidden state after a reload or an interrupted transition.
            // Don't move her back to the anchor here; only normalize normal ground rendering.
            this.WorldActors.ConfigureMimiActor(native, broom: false, visible: true);
            native.hideShadow.Value = false;
            native.drawOnTop = false;
            native.drawOffset = Vector2.Zero;
            native.rotation = 0f;
        }

        this.ArrivedToday = true;
    }

    private void HideNativeOffMap()
        => this.WorldActors.HideMimiActor();

    private void MoveNative(NPC native, GameLocation target, Vector2 position, int facing)
        => this.WorldActors.MoveMimiActor(native, target, position, facing, broom: false, visible: true);

    private void EnforceStoryVisibility()
    {
        if (!Context.IsWorldReady || !this.Save.Data.FirstScrapTriggered)
            return;

        // StoryService explicitly owns MiMi while an intro/meetup/departure presentation is live.
        // This avoids a race where MysteryService would otherwise move the same native NPC off-map.
        if (this.StoryOwnsMimiActor())
            return;

        // After the Wizard meetup, MiMi is a persistent social NPC. The alpha.27 home layer
        // owns her during weekends, off-hours, and the restored Community Center route.
        if (this.Save.Data.MimiMeetupCompleted)
            return;

        this.HideNativeOffMap();
    }

    /// <summary>Return Cardcha's one canonical MiMi world actor.</summary>
    /// <remarks>alpha.11.37 moved actor ownership into WorldActorService, so old call sites
    /// still use this tiny compatibility helper instead of scanning Game1.locations themselves.</remarks>
    private NPC? FindNativeNpc()
        => this.WorldActors.FindMimiActor();

    private void ShowMysteryDialogue(string rawLine, string portraitCommand)
    {
        string text = ExtractDialogueText(rawLine) + portraitCommand;
        NPC? speaker = FindNativeNpc() ?? this.WorldActors.EnsureMimiActor();
        if (speaker is not null)
        {
            SetNpcDisplayName(speaker, "???");
            if (TryShowDialogueWithPortrait(speaker, text))
                return;
        }

        // Safe fallback if the native actor couldn't be created for any reason.
        Game1.drawObjectDialogue(rawLine);
    }

    private static string MysteryPortraitCommand(int lineIndex)
        => lineIndex switch
        {
            0 => "$0",
            1 => "$3",
            2 => "$2",
            3 => "$3",
            4 => "$5",
            _ => "$0"
        };

    private static string ExtractDialogueText(string rawLine)
    {
        int colon = rawLine.IndexOf(':');
        return colon >= 0 && colon + 1 < rawLine.Length
            ? rawLine[(colon + 1)..].Trim()
            : rawLine.Trim();
    }

    private bool TryShowDialogueWithPortrait(NPC speaker, string text)
    {
        try
        {
            this.EnsureTextures();
            AssignPortraitTexture(speaker, this.RuntimePortraitSheet);
            Dialogue dialogue = new Dialogue(speaker, "Mods/Ronvotri.Cardcha:RuntimeDialogue", text)
            {
                overridePortrait = this.RuntimePortraitSheet,
                showPortrait = true
            };
            Game1.activeClickableMenu = new DialogueBox(dialogue);
            return true;
        }
        catch (Exception ex)
        {
            this.Monitor.Log($"MiMi portrait dialogue failed: {ex}", LogLevel.Error);
            return false;
        }
    }

    private static Texture2D CreateRuntimePortraitSheet(Texture2D master)
    {
        const int frameCount = 6;
        const int targetSize = 64;
        if (master.Width % frameCount != 0)
            throw new InvalidOperationException($"MiMi master portrait width {master.Width} is not divisible by {frameCount}.");

        int sourceFrameWidth = master.Width / frameCount;
        int sourceFrameHeight = master.Height;
        Color[] source = new Color[master.Width * master.Height];
        master.GetData(source);
        Color[] output = new Color[frameCount * targetSize * targetSize];

        // Downsample the official mimi_portraits.png in memory only. This preserves the
        // user's master asset while giving vanilla DialogueBox the 64x64 frames it requires.
        for (int frame = 0; frame < frameCount; frame++)
        {
            int frameX = frame * sourceFrameWidth;
            for (int ty = 0; ty < targetSize; ty++)
            {
                int sy0 = ty * sourceFrameHeight / targetSize;
                int sy1 = Math.Max(sy0 + 1, (ty + 1) * sourceFrameHeight / targetSize);
                sy1 = Math.Min(sourceFrameHeight, sy1);
                for (int tx = 0; tx < targetSize; tx++)
                {
                    int sx0 = tx * sourceFrameWidth / targetSize;
                    int sx1 = Math.Max(sx0 + 1, (tx + 1) * sourceFrameWidth / targetSize);
                    sx1 = Math.Min(sourceFrameWidth, sx1);

                    double sumA = 0, sumRA = 0, sumGA = 0, sumBA = 0;
                    int samples = 0;
                    for (int sy = sy0; sy < sy1; sy++)
                    {
                        for (int sx = sx0; sx < sx1; sx++)
                        {
                            Color c = source[sy * master.Width + frameX + sx];
                            double a = c.A / 255.0;
                            sumA += c.A;
                            sumRA += c.R * a;
                            sumGA += c.G * a;
                            sumBA += c.B * a;
                            samples++;
                        }
                    }

                    byte outA = (byte)Math.Clamp((int)Math.Round(sumA / Math.Max(1, samples)), 0, 255);
                    double alphaWeight = sumA / 255.0;
                    byte outR = alphaWeight > 0 ? (byte)Math.Clamp((int)Math.Round(sumRA / alphaWeight), 0, 255) : (byte)0;
                    byte outG = alphaWeight > 0 ? (byte)Math.Clamp((int)Math.Round(sumGA / alphaWeight), 0, 255) : (byte)0;
                    byte outB = alphaWeight > 0 ? (byte)Math.Clamp((int)Math.Round(sumBA / alphaWeight), 0, 255) : (byte)0;
                    output[ty * (frameCount * targetSize) + frame * targetSize + tx] = new Color(outR, outG, outB, outA);
                }
            }
        }

        Texture2D runtime = new Texture2D(Game1.graphics.GraphicsDevice, frameCount * targetSize, targetSize);
        runtime.SetData(output);
        return runtime;
    }

    private static void AssignPortraitTexture(NPC npc, Texture2D? portraitTexture)
    {
        if (portraitTexture is null)
            return;

        try
        {
            PropertyInfo? prop = typeof(NPC).GetProperty("Portrait", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
            if (prop is not null && prop.CanWrite && prop.PropertyType == typeof(Texture2D))
            {
                prop.SetValue(npc, portraitTexture);
                return;
            }
        }
        catch
        {
        }

        foreach (string fieldName in new[] { "Portrait", "portrait", "portraitTexture", "PortraitTexture" })
        {
            try
            {
                FieldInfo? field = typeof(NPC).GetField(fieldName, BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
                if (field is not null && field.FieldType == typeof(Texture2D))
                {
                    field.SetValue(npc, portraitTexture);
                    return;
                }
            }
            catch
            {
            }
        }
    }

    private static void SetNpcDisplayName(NPC npc, string displayName)
    {
        // NPC.displayName is the value DialogueBox actually renders. Set it directly first;
        // the reflection fallback below only covers point-release/modded wrappers.
        npc.displayName = displayName;

        const BindingFlags flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.IgnoreCase;

        foreach (string memberName in new[] { "displayName", "DisplayName" })
        {
            try
            {
                PropertyInfo? property = typeof(NPC).GetProperty(memberName, flags);
                if (property is not null && property.CanWrite && property.PropertyType == typeof(string))
                    property.SetValue(npc, displayName);
            }
            catch
            {
            }

            try
            {
                FieldInfo? field = typeof(NPC).GetField(memberName, flags);
                if (field is null)
                    continue;

                if (field.FieldType == typeof(string))
                {
                    field.SetValue(npc, displayName);
                    continue;
                }

                object? netValue = field.GetValue(npc);
                PropertyInfo? valueProperty = netValue?.GetType().GetProperty("Value", flags);
                if (valueProperty is not null && valueProperty.CanWrite && valueProperty.PropertyType == typeof(string))
                    valueProperty.SetValue(netValue, displayName);
            }
            catch
            {
            }
        }
    }

    private void EnsureTextures()
    {
        this.MasterPortraitSheet ??= this.Helper.ModContent.Load<Texture2D>(MimiPortraitsPath);
        this.RuntimePortraitSheet ??= CreateRuntimePortraitSheet(this.MasterPortraitSheet);
    }

    private void SyncChaChaWithMimi()
    {
        if (this.Save.Data.ChaChaLoaned || this.Save.Data.FirstScrapTriggered)
            return;

        NPC? mimi = FindNativeNpc() ?? this.WorldActors.EnsureMimiActor();
        GameLocation? location = Game1.currentLocation;
        if (mimi is null
            || location is null
            || mimi.currentLocation != location
            || mimi.isInvisible.Value)
        {
            this.WorldActors.HideChaChaActor();
            return;
        }

        double seconds = CurrentGameMs() / 1000.0;
        Vector2 fairyDrift = new(
            (float)Math.Sin(seconds * 1.35 + 0.4) * 4.5f,
            (float)Math.Sin(seconds * 2.1) * 3.2f - 4f
        );
        int frame = (int)(CurrentGameMs() / 165L) % 4;

        NPC? existing = this.WorldActors.FindChaChaActor();
        if ((Game1.dialogueUp || Game1.activeClickableMenu is DialogueBox)
            && existing is not null
            && existing.currentLocation == location)
        {
            // Keep ChaCha exactly where she was when the conversation opened. Only the fairy
            // hover/wing frame continues; no safety-slot reselection means no talk-time hop.
            if (existing.Sprite is not null)
                existing.Sprite.CurrentFrame = frame;
            existing.drawOffset = fairyDrift;
            existing.shouldShadowBeOffset = false;
            existing.rotation = (float)Math.Sin(seconds * 1.7) * 0.018f;
            return;
        }

        // Keep one stable side relative to MiMi. Re-running the old safety-slot search every
        // tick could alternate between left/right candidates as MiMi walked, which looked like
        // ChaCha was blinking across her. Smooth the actor toward one fixed follow point instead.
        Vector2 desiredWorld = mimi.Position + new Vector2(64f, -6f);
        Vector2 baseWorld = desiredWorld;
        if (existing is not null && existing.currentLocation == location)
        {
            float distance = Vector2.Distance(existing.Position, desiredWorld);
            baseWorld = distance > 256f
                ? desiredWorld
                : Vector2.Lerp(existing.Position, desiredWorld, 0.12f);
        }
        NPC? chacha = this.WorldActors.EnsureChaChaActor(location, baseWorld, 0, frame, machine: false);
        if (chacha is not null)
        {
            chacha.drawOffset = fairyDrift;
            chacha.shouldShadowBeOffset = false;
            chacha.rotation = (float)Math.Sin(seconds * 1.7) * 0.018f;
        }
    }

    private Vector2 ResolveSafeChaChaPosition(Vector2 mimiWorld)
    {
        GameLocation? location = Game1.currentLocation;
        Vector2[] offsets =
        {
            new(64f, -6f),
            new(-64f, -6f),
            new(58f, 42f),
            new(-58f, 42f),
            new(52f, -46f),
            new(-52f, -46f)
        };

        foreach (Vector2 offset in offsets)
        {
            Vector2 candidate = mimiWorld + offset;
            if (location is null || IsChaChaWorldSafe(location, candidate))
                return candidate;
        }

        if (location is not null)
        {
            foreach (float radius in new[] { 82f, 104f, 126f })
            {
                for (int i = 0; i < 8; i++)
                {
                    float angle = MathHelper.TwoPi * i / 8f;
                    Vector2 candidate = mimiWorld + new Vector2((float)Math.Cos(angle), (float)Math.Sin(angle)) * radius;
                    if (IsChaChaWorldSafe(location, candidate))
                        return candidate;
                }
            }
        }

        // Extremely crowded fallback: keep ChaCha next to MiMi rather than teleporting away.
        return mimiWorld + new Vector2(64f, -6f);
    }

    private static bool IsChaChaWorldSafe(GameLocation location, Vector2 world)
    {
        if (!IsChaChaFootprintClear(location, world))
            return false;

        Vector2 center = world + new Vector2(16f, 20f);
        if (Game1.player.currentLocation == location)
        {
            Vector2 playerCenter = Game1.player.Position + new Vector2(32f, 42f);
            if (Vector2.DistanceSquared(center, playerCenter) < 48f * 48f)
                return false;
        }

        foreach (NPC npc in location.characters)
        {
            if (string.Equals(npc.Name, NpcId, StringComparison.OrdinalIgnoreCase)
                || string.Equals(npc.Name, WorldActorService.ChaChaNpcId, StringComparison.OrdinalIgnoreCase))
                continue;

            Vector2 npcCenter = npc.Position + new Vector2(32f, 36f);
            if (Vector2.DistanceSquared(center, npcCenter) < 58f * 58f)
                return false;
        }

        return true;
    }

    private static bool IsChaChaFootprintClear(GameLocation location, Vector2 world)
    {
        Vector2 feet = world + new Vector2(16f, 26f);
        Vector2[] samples =
        {
            feet,
            feet + new Vector2(-34f, 0f),
            feet + new Vector2(34f, 0f),
            feet + new Vector2(0f, -24f),
            feet + new Vector2(0f, 24f),
            feet + new Vector2(-28f, -18f),
            feet + new Vector2(28f, -18f),
            feet + new Vector2(-28f, 18f),
            feet + new Vector2(28f, 18f)
        };

        foreach (Vector2 sample in samples)
        {
            Vector2 tile = new((float)Math.Floor(sample.X / 64f), (float)Math.Floor(sample.Y / 64f));
            try
            {
                if (location.IsTileBlockedBy(tile))
                    return false;
            }
            catch
            {
            }
        }

        return true;
    }

    private Vector2 ChooseSafeWanderTarget(GameLocation town, NPC native, long now)
    {
        // The old full-footprint validator rejected every nearby plaza point on modded Town
        // maps, leaving mystery MiMi permanently idle. Use a small deterministic loop wholly
        // within the open plaza instead. Native actor collision still handles the farmer/NPCs.
        this.WanderTargetIndex = (this.WanderTargetIndex + 1) % WanderOffsets.Length;
        return TownAnchor + WanderOffsets[this.WanderTargetIndex];
    }

    private static bool IsTooCloseToOtherNpc(GameLocation location, NPC self, float distance)
    {
        float limit = distance * distance;
        foreach (NPC npc in location.characters)
        {
            if (ReferenceEquals(npc, self)
                || string.Equals(npc.Name, WorldActorService.ChaChaNpcId, StringComparison.OrdinalIgnoreCase))
                continue;
            if (Vector2.DistanceSquared(npc.Position, self.Position) < limit)
                return true;
        }
        return false;
    }

    private static bool IsMimiClearOfOtherNpcs(GameLocation location, NPC self, Vector2 candidate, float distance)
    {
        float limit = distance * distance;
        Vector2 candidateFeet = candidate + new Vector2(32f, 64f);
        foreach (NPC npc in location.characters)
        {
            if (ReferenceEquals(npc, self)
                || string.Equals(npc.Name, WorldActorService.ChaChaNpcId, StringComparison.OrdinalIgnoreCase))
                continue;

            Vector2 npcFeet = npc.Position + new Vector2(32f, 64f);
            if (Vector2.DistanceSquared(npcFeet, candidateFeet) < limit)
                return false;
        }
        return true;
    }

    private static bool IsWorldPositionSafeForMiMi(GameLocation location, Vector2 worldPosition, NPC self)
    {
        if (!IsMimiFootprintClear(location, worldPosition))
            return false;

        Vector2 mimiFeet = worldPosition + new Vector2(32f, 64f);
        // Do not reject a walk step merely because the player is nearby. That check made
        // mystery MiMi freeze whenever the player approached to watch or talk to her.
        // Native character collision still prevents her from walking through the farmer.
        const float minNpcDistance = 128f;
        foreach (NPC npc in location.characters)
        {
            if (ReferenceEquals(npc, self)
                || string.Equals(npc.Name, WorldActorService.ChaChaNpcId, StringComparison.OrdinalIgnoreCase))
                continue;

            Vector2 npcFeet = npc.Position + new Vector2(32f, 64f);
            if (Vector2.DistanceSquared(npcFeet, mimiFeet) < minNpcDistance * minNpcDistance)
                return false;
        }

        return true;
    }

    private static bool IsMimiFootprintClear(GameLocation location, Vector2 worldPosition)
    {
        Vector2 feet = worldPosition + new Vector2(32f, 64f);
        // MiMi is visually taller/wider than the hidden native NPC. Sample both her feet
        // and the body space one tile above so she doesn't visually stand inside bushes/trees.
        Vector2[] samples =
        {
            feet,
            feet + new Vector2(-34f, 0f),
            feet + new Vector2(34f, 0f),
            feet + new Vector2(0f, -32f),
            feet + new Vector2(-30f, -32f),
            feet + new Vector2(30f, -32f),
            feet + new Vector2(0f, -62f),
            feet + new Vector2(-26f, -56f),
            feet + new Vector2(26f, -56f)
        };

        foreach (Vector2 sample in samples)
        {
            Vector2 tile = new((float)Math.Floor(sample.X / 64f), (float)Math.Floor(sample.Y / 64f));
            try
            {
                if (location.IsTileBlockedBy(tile))
                    return false;
            }
            catch
            {
            }
        }

        return true;
    }

    private static bool IsTileClear(GameLocation location, Vector2 worldPoint)
    {
        Vector2 tile = new((float)Math.Floor(worldPoint.X / 64f), (float)Math.Floor(worldPoint.Y / 64f));
        try
        {
            return !location.IsTileBlockedBy(tile);
        }
        catch
        {
            return true;
        }
    }

    private void UpdateNativeWander(bool officialMerchant = false)
    {
        bool visible = officialMerchant
            ? this.IsMerchantRoutineActive()
              && Game1.timeOfDay >= MerchantStartTime
              && Game1.timeOfDay < MerchantEndTime
              && FindNativeNpc()?.currentLocation?.NameOrUniqueName.Equals("Town", StringComparison.OrdinalIgnoreCase) == true
            : this.IsVisibleNow();
        if (!visible || this.Flight != FlightState.None)
            return;

        NPC? native = FindNativeNpc() ?? this.WorldActors.EnsureMimiActor();
        GameLocation? town = Game1.getLocationFromName("Town");
        if (native is null || town is null || native.currentLocation != town)
            return;

        long now = CurrentGameMs();

        // Talking/menu interaction must never shove MiMi out of the way. Native collision now
        // handles physical spacing, so freeze her exact world position until the UI closes.
        if (Game1.dialogueUp || Game1.activeClickableMenu is not null)
        {
            this.WanderTarget = native.Position;
            this.NextWanderDecisionAtMs = Math.Max(this.NextWanderDecisionAtMs, now + 900);
            this.LastWanderUpdateAtMs = now;
            SetNativeWalkFrame(native, native.FacingDirection, 0);
            return;
        }
        if (IsTooCloseToOtherNpc(town, native, 220f))
            this.NextWanderDecisionAtMs = 0;

        if (this.LastWanderUpdateAtMs <= 0)
            this.LastWanderUpdateAtMs = now;

        float dt = Math.Clamp((now - this.LastWanderUpdateAtMs) / 1000f, 0f, 0.10f);
        this.LastWanderUpdateAtMs = now;

        // No synthetic personal-space escape here: it caused visible "jumping" when the
        // player pressed talk. Native world collision is the source of truth in alpha.11.37.

        Vector2 delta = this.WanderTarget - native.Position;
        float distance = delta.Length();

        if (distance <= 3f)
        {
            native.Position = this.WanderTarget;
            SetNativeWalkFrame(native, this.WanderFacing, 0);

            if (now >= this.NextWanderDecisionAtMs)
            {
                this.WanderTarget = ChooseSafeWanderTarget(town, native, now);
                int spread = Math.Max(1, WanderPauseMaxMs - WanderPauseMinMs);
                int jitter = (int)((now / 137L + this.WanderTargetIndex * 947L) % spread);
                this.NextWanderDecisionAtMs = now + WanderPauseMinMs + jitter;
            }

            return;
        }

        Vector2 direction = delta / Math.Max(0.001f, distance);
        float step = Math.Min(distance, WanderSpeedPixelsPerSecond * dt);
        Vector2 nextPosition = native.Position + direction * step;
        native.Position = nextPosition;

        int facing = Math.Abs(direction.X) >= Math.Abs(direction.Y)
            ? (direction.X >= 0f ? 1 : 3)
            : (direction.Y >= 0f ? 2 : 0);
        native.faceDirection(facing);
        this.WanderFacing = facing;

        int walkFrame = 1 + (int)(now / 170L) % 3;
        SetNativeWalkFrame(native, facing, walkFrame);
    }

    private void SetNativeWalkFrame(NPC native, int facing, int stepFrame)
        => this.WorldActors.SetMimiFrame(native, facing, stepFrame);

    private static void SuppressVanillaGreetingLeak()
    {
        if (Game1.currentLocation is null)
            return;

        foreach (NPC npc in Game1.currentLocation.characters)
        {
            try
            {
                FieldInfo? textField = typeof(NPC).GetField("textAboveHead", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
                FieldInfo? timerField = typeof(NPC).GetField("textAboveHeadTimer", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
                string? bubble = textField?.GetValue(npc) as string;
                if (!string.IsNullOrEmpty(bubble) && bubble.Contains(NpcId, StringComparison.OrdinalIgnoreCase))
                {
                    textField?.SetValue(npc, null);
                    timerField?.SetValue(npc, 0);
                }
            }
            catch
            {
            }
        }
    }

    private void TryVillagerMysteryReaction()
    {
        // Intentionally disabled for now. Mystery MiMi should not exchange visible chatter with townsfolk yet.
    }

    private static void FaceToward(NPC npc, Vector2 target)
    {
        Vector2 delta = target - npc.Position;
        int direction = Math.Abs(delta.X) >= Math.Abs(delta.Y)
            ? (delta.X >= 0f ? 1 : 3)
            : (delta.Y >= 0f ? 2 : 0);
        npc.faceDirection(direction);
    }

    private static long CurrentGameMs()
        => (long)Game1.currentGameTime.TotalGameTime.TotalMilliseconds;

    private static float SmoothStep(float t)
    {
        t = Math.Clamp(t, 0f, 1f);
        return t * t * (3f - 2f * t);
    }

    private static void SetHome(CharacterData target, string location, int x, int y, string direction)
    {
        Type targetType = target.GetType();
        PropertyInfo? property = targetType.GetProperty("Home", BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
        FieldInfo? field = targetType.GetField("Home", BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
        Type? listType = property?.PropertyType ?? field?.FieldType;
        if (listType is null)
            return;

        Type? itemType = listType.IsGenericType ? listType.GetGenericArguments().FirstOrDefault() : null;
        if (itemType is null)
            return;

        object? listObject = null;
        try { listObject = Activator.CreateInstance(listType); } catch { }
        listObject ??= Activator.CreateInstance(typeof(List<>).MakeGenericType(itemType));
        if (listObject is not IList list)
            return;

        object? home = Activator.CreateInstance(itemType);
        if (home is null)
            return;

        SetProperty(home, "Id", "Default");
        SetProperty(home, "ID", "Default");
        SetProperty(home, "Location", location);
        SetProperty(home, "Direction", direction);
        SetPointProperty(home, "Tile", x, y);
        list.Add(home);

        try
        {
            if (property is not null && property.CanWrite && property.PropertyType.IsInstanceOfType(listObject))
                property.SetValue(target, listObject);
            else if (field is not null && field.FieldType.IsInstanceOfType(listObject))
                field.SetValue(target, listObject);
        }
        catch { }
    }

    private static void SetRectangleProperty(object target, string propertyName, int x, int y, int width, int height)
    {
        Type targetType = target.GetType();
        PropertyInfo? property = targetType.GetProperty(propertyName, BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
        FieldInfo? field = targetType.GetField(propertyName, BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
        Type? memberType = property?.PropertyType ?? field?.FieldType;
        if (memberType is null)
            return;

        Type type = Nullable.GetUnderlyingType(memberType) ?? memberType;
        if (type != typeof(Rectangle))
            return;

        Rectangle value = new(x, y, width, height);
        try
        {
            if (property is not null && property.CanWrite)
                property.SetValue(target, value);
            else
                field?.SetValue(target, value);
        }
        catch { }
    }

    private static void SetPointProperty(object target, string propertyName, int x, int y)
    {
        Type targetType = target.GetType();
        PropertyInfo? property = targetType.GetProperty(propertyName, BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
        FieldInfo? field = targetType.GetField(propertyName, BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
        Type? memberType = property?.PropertyType ?? field?.FieldType;
        if (memberType is null)
            return;

        Type type = Nullable.GetUnderlyingType(memberType) ?? memberType;
        object? point = null;

        if (type == typeof(Point))
            point = new Point(x, y);
        else if (type == typeof(Vector2))
            point = new Vector2(x, y);
        else
        {
            try
            {
                point = Activator.CreateInstance(type);
                if (point is not null)
                {
                    SetProperty(point, "X", x);
                    SetProperty(point, "Y", y);
                }
            }
            catch { }
        }

        if (point is null || !type.IsInstanceOfType(point))
            return;

        try
        {
            if (property is not null && property.CanWrite)
                property.SetValue(target, point);
            else
                field?.SetValue(target, point);
        }
        catch { }
    }

    private static void SetProperty(object target, string propertyName, object? value)
    {
        Type targetObjectType = target.GetType();
        PropertyInfo? property = targetObjectType.GetProperty(propertyName, BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
        FieldInfo? field = targetObjectType.GetField(propertyName, BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
        Type? memberType = property?.PropertyType ?? field?.FieldType;
        if (memberType is null)
            return;

        try
        {
            object? converted = null;
            if (value is not null)
            {
                Type targetType = Nullable.GetUnderlyingType(memberType) ?? memberType;
                if (targetType.IsInstanceOfType(value))
                    converted = value;
                else if (targetType.IsEnum && value is string enumText)
                    converted = Enum.Parse(targetType, enumText, ignoreCase: true);
                else if (targetType == typeof(string))
                    converted = value.ToString() ?? string.Empty;
                else
                    converted = Convert.ChangeType(value, targetType);
            }

            if (property is not null && property.CanWrite)
                property.SetValue(target, converted);
            else
                field?.SetValue(target, converted);
        }
        catch
        {
            // Optional cross-version member; ignore if the installed game model differs.
        }
    }

}
