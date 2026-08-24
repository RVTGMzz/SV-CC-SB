using System.Collections;
using System.Reflection;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.GameData.Characters;
using StardewValley.Menus;

namespace Cardcha.Services;

/// <summary>
/// v0.1.17-alpha.11.32: MiMi mystery + merchant NPC runtime.
/// Before the first Scrap she keeps the temporary 10:00-15:00 Town mystery routine for testing.
/// After the Wizard handoff she becomes a daily 11:00-17:00 merchant: near the Farmhouse
/// on normal days, or inside the WizardHouse on rainy days.
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
    private const int MerchantStartTime = 1100;
    private const int MerchantEndTime = 1700;
    private const int FlightDurationMs = 1800;
    private const float WanderSpeedPixelsPerSecond = 44f;
    private const int WanderPauseMinMs = 3200;
    private const int WanderPauseMaxMs = 6500;

    private static readonly Vector2[] WanderOffsets =
    {
        Vector2.Zero,
        new(64f, 0f),
        new(-64f, 0f),
        new(0f, -64f),
        new(64f, -64f),
        new(-64f, -64f)
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
    private Vector2 WanderTarget = TownAnchor;
    private long NextWanderDecisionAtMs;
    private long LastWanderUpdateAtMs;
    private int WanderTargetIndex;
    private int WanderFacing = 2;
    private bool MerchantHandoffCleared;

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

        if (e.NameWithoutLocale.IsEquivalentTo("Data/Characters"))
        {
            e.Edit(asset =>
            {
                IDictionary<string, CharacterData> data = asset.AsDictionary<string, CharacterData>().Data;
                CharacterData mimi = new();

                SetProperty(mimi, "DisplayName", "???");
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
                SetRectangleProperty(mimi, "MugShotSourceRect", 0, 0, 16, 24);
                SetPointProperty(mimi, "EmoteOffset", 0, -24);
                SetHome(mimi, "WizardHouse", 4, 6, "down");

                data[NpcId] = mimi;
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
        this.EnsureTextures();
        this.WorldActors.EnsureMimiActor();
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
        this.WanderTarget = TownAnchor;
        this.NextWanderDecisionAtMs = 0;
        this.LastWanderUpdateAtMs = 0;
        this.WanderTargetIndex = 0;
        this.WanderFacing = 2;
        this.MerchantHandoffCleared = false;
    }

    public void OnTimeChanged(object? sender, TimeChangedEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        if (this.IsMerchantRoutineActive())
        {
            if (e.NewTime == MerchantStartTime || e.NewTime == MerchantEndTime)
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

        if (e.NewTime == DepartureTime)
        {
            StartDepartureFlight();
        }
    }

    public void OnUpdateTicked()
    {
        if (!Context.IsWorldReady)
            return;

        if (this.IsMerchantRoutineActive())
        {
            this.Flight = FlightState.None;
            this.EnforceMerchantState();
            if (!this.Save.Data.ChaChaLoaned)
                this.SyncChaChaWithMimi();
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
            this.EnforceCurrentTimeState(allowAnimation: Game1.currentLocation?.NameOrUniqueName.Equals("Town", StringComparison.OrdinalIgnoreCase) == true);

        this.UpdateNativeWander();
        this.SyncChaChaWithMimi();

        NPC? native = FindNativeNpc();
        if (native is not null)
        {
            SetNpcDisplayName(native, "???");
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
            EnsureConversationSpacing(native);
            native.faceTowardFarmerForPeriod(1600, 3, false, Game1.player);
        }

        int mysteryLine = this.TalkIndex % 5;
        string key = $"story.mystery.{mysteryLine}";
        this.TalkIndex++;
        ShowMysteryDialogue(ModEntry.T(key), MysteryPortraitCommand(mysteryLine));
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        // Intentionally empty in alpha.11.32. MiMi and ChaCha are real world actors
        // in GameLocation.characters; Stardew now owns their depth sorting.
    }

    public string Describe()
    {
        NPC? native = FindNativeNpc();
        string location = native?.currentLocation?.NameOrUniqueName ?? "<missing>";
        return $"MysteryNativeNpc={(native is not null)} | MysteryVisible={this.IsVisibleNow()} | " +
               $"Flight={this.Flight} | ArrivedToday={this.ArrivedToday} | DepartedToday={this.DepartedToday} | " +
               $"MysteryTalkIndex={this.TalkIndex} | NativeLocation={location} | " +
               $"RuntimeWindow=Town@10:00-15:00 (temporary test) | Merchant=11:00-17:00 Farm/rain->WizardHouse | " +
               $"MerchantActive={this.IsMerchantRoutineActive()} | PlazaAnchor=45,62 | Wander=True | HumanReactionsOnly=True | FirstScrap={this.Save.Data.FirstScrapTriggered}";
    }

    private void ResetRuntimeForDay()
    {
        this.TalkIndex = 0;
        this.LoggedNativeFound = false;
        this.ArrivedToday = Game1.timeOfDay >= ArrivalStartTime;
        this.DepartedToday = Game1.timeOfDay >= DepartureTime;
        this.Flight = FlightState.None;
        this.FlightStartedMs = 0;
        this.WanderTarget = TownAnchor;
        this.NextWanderDecisionAtMs = CurrentGameMs() + 2800;
        this.LastWanderUpdateAtMs = CurrentGameMs();
        this.WanderTargetIndex = 0;
        this.WanderFacing = 2;
        this.MerchantHandoffCleared = this.Save.Data.MimiMerchantUnlockedDay < Game1.Date.TotalDays;
    }

    private bool IsMerchantRoutineActive()
    {
        if (!Context.IsWorldReady || !this.Save.Data.MimiMeetupCompleted)
            return false;

        int unlockedDay = this.Save.Data.MimiMerchantUnlockedDay;
        return unlockedDay < 0 || Game1.Date.TotalDays >= unlockedDay;
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

        if (Game1.timeOfDay < MerchantStartTime || Game1.timeOfDay >= MerchantEndTime)
        {
            this.HideNativeOffMap();
            return;
        }

        // On the handoff day, let MiMi visibly finish walking out of the Wizard's house first.
        // As soon as the player leaves WizardHouse, the normal 11:00-17:00 merchant routine is live.
        int unlockedDay = this.Save.Data.MimiMerchantUnlockedDay;
        bool handoffDay = unlockedDay >= 0 && Game1.Date.TotalDays == unlockedDay;
        bool playerInWizardHouse = Game1.currentLocation?.NameOrUniqueName.Equals(
            "WizardHouse",
            StringComparison.OrdinalIgnoreCase) == true;

        if (handoffDay && !this.MerchantHandoffCleared)
        {
            if (playerInWizardHouse)
            {
                this.HideNativeOffMap();
                return;
            }

            this.MerchantHandoffCleared = true;
        }

        if (Game1.isRaining)
            this.PlaceNativeInWizardHouseMerchant();
        else
            this.PlaceNativeAtFarmMerchant();
    }

    private void PlaceNativeAtFarmMerchant()
    {
        NPC? native = FindNativeNpc() ?? this.WorldActors.EnsureMimiActor();
        GameLocation? farm = Game1.getFarm();
        if (native is null || farm is null)
            return;

        Vector2 anchor = FindWarpSourceWorld(farm, "FarmHouse")
            ?? new Vector2(62f * 64f, 16f * 64f);

        // Stand beside the door rather than directly on the warp tile.
        anchor += new Vector2(-72f, 10f);
        MoveNative(native, farm, anchor, 2);
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
        this.OpenMimiShop();
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
            // TimeChanged and UpdateTicked can run in either order around 15:00.
            // If UpdateTicked sees 15:00 first, start the broom departure here instead
            // of marking MiMi departed and making her vanish before the animation can begin.
            bool playerInTown = Game1.currentLocation?.NameOrUniqueName.Equals(
                "Town",
                StringComparison.OrdinalIgnoreCase) == true;

            if (allowAnimation && playerInTown && !this.DepartedToday && this.Flight == FlightState.None)
            {
                StartDepartureFlight();
                return;
            }

            HideNativeOffMap();
            if (!playerInTown || !allowAnimation)
                this.DepartedToday = true;
            return;
        }

        if (allowAnimation
            && !this.ArrivedToday
            && Game1.currentLocation?.NameOrUniqueName.Equals("Town", StringComparison.OrdinalIgnoreCase) == true)
        {
            StartArrivalFlight();
            return;
        }

        PlaceNativeInTown();
    }

    private void StartArrivalFlight()
    {
        if (this.Flight != FlightState.None || this.ArrivedToday || this.Save.Data.FirstScrapTriggered)
            return;

        NPC? native = FindNativeNpc() ?? this.WorldActors.EnsureMimiActor();
        GameLocation? town = Game1.getLocationFromName("Town");
        if (native is null || town is null)
            return;

        this.Flight = FlightState.Arriving;
        this.FlightStartedMs = CurrentGameMs();
        Vector2 high = TownAnchor + new Vector2(0f, -7f * 64f);
        this.WorldActors.MoveMimiActor(native, town, high, 2, broom: true, visible: true);
        this.WorldActors.SetMimiFrame(native, 2, 0);
        Game1.playSound("wand");
        this.Monitor.Log("MiMi mystery arrival: native broom actor started at 10:00.", LogLevel.Info);
    }

    private void StartDepartureFlight()
    {
        if (this.Flight != FlightState.None || this.Save.Data.FirstScrapTriggered)
            return;

        if (this.DepartedToday && Game1.timeOfDay > DepartureTime)
            return;

        NPC? native = FindNativeNpc() ?? this.WorldActors.EnsureMimiActor();
        GameLocation? town = Game1.getLocationFromName("Town");
        if (native is null || town is null)
            return;

        this.DepartedToday = false;
        Vector2 start = native.currentLocation == town ? native.Position : TownAnchor;
        this.Flight = FlightState.Departing;
        this.FlightStartedMs = CurrentGameMs();
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
        Vector2 high = TownAnchor + new Vector2(0f, -7f * 64f);
        Vector2 world = this.Flight == FlightState.Arriving
            ? Vector2.Lerp(high, TownAnchor, t)
            : Vector2.Lerp(TownAnchor, high, t);

        int facing = this.Flight == FlightState.Arriving ? 2 : 0;
        int frame = (int)(CurrentGameMs() / 110L) % 4;
        this.WorldActors.MoveMimiActor(native, town, world, facing, broom: true, visible: true);
        this.WorldActors.SetMimiFrame(native, facing, frame);
        native.rotation = this.Flight == FlightState.Arriving
            ? (1f - t) * 0.035f
            : t * -0.035f;

        this.SyncChaChaWithMimi();

        if (elapsed < FlightDurationMs)
            return;

        FlightState finished = this.Flight;
        this.Flight = FlightState.None;
        native.rotation = 0f;

        if (finished == FlightState.Arriving)
        {
            this.ArrivedToday = true;
            this.WorldActors.MoveMimiActor(native, town, TownAnchor, 2, broom: false, visible: true);
            this.WorldActors.SetMimiFrame(native, 2, 0);
            this.WanderTarget = TownAnchor;
            this.NextWanderDecisionAtMs = CurrentGameMs() + 2600;
            this.LastWanderUpdateAtMs = CurrentGameMs();
            Game1.playSound("smallSelect");
        }
        else
        {
            this.DepartedToday = true;
            HideNativeOffMap();
            this.WorldActors.HideChaChaActor();
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

        this.ArrivedToday = true;
    }

    private void HideNativeOffMap()
    {
        NPC? native = FindNativeNpc() ?? this.WorldActors.EnsureMimiActor();
        GameLocation? wizardHouse = Game1.getLocationFromName("WizardHouse");
        if (native is null || wizardHouse is null)
            return;

        this.WorldActors.MoveMimiActor(
            native,
            wizardHouse,
            HiddenWizardPosition,
            2,
            broom: false,
            visible: false
        );
    }

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

        this.HideNativeOffMap();
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
        try
        {
            FieldInfo? field = typeof(NPC).GetField("displayName", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
            field?.SetValue(npc, displayName);
        }
        catch
        {
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

        Vector2 baseWorld = ResolveSafeChaChaPosition(mimi.Position);
        double seconds = CurrentGameMs() / 1000.0;
        Vector2 fairyDrift = new(
            (float)Math.Sin(seconds * 1.35 + 0.4) * 4.5f,
            (float)Math.Sin(seconds * 2.1) * 3.2f - 4f
        );

        int frame = (int)(CurrentGameMs() / 165L) % 4;
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
        for (int attempt = 0; attempt < WanderOffsets.Length; attempt++)
        {
            this.WanderTargetIndex = (this.WanderTargetIndex + 1) % WanderOffsets.Length;
            Vector2 candidate = TownAnchor + WanderOffsets[this.WanderTargetIndex];
            if (IsWorldPositionSafeForMiMi(town, candidate, native))
                return candidate;
        }

        return native.Position;
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
        const float minPlayerDistance = 96f;
        if (Game1.player.currentLocation == location)
        {
            Vector2 playerFeet = Game1.player.Position + new Vector2(32f, 64f);
            if (Vector2.DistanceSquared(playerFeet, mimiFeet) < minPlayerDistance * minPlayerDistance)
                return false;
        }

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

    private void UpdateNativeWander()
    {
        if (!this.IsVisibleNow() || this.Flight != FlightState.None)
            return;

        NPC? native = FindNativeNpc() ?? this.WorldActors.EnsureMimiActor();
        GameLocation? town = Game1.getLocationFromName("Town");
        if (native is null || town is null || native.currentLocation != town)
            return;

        long now = CurrentGameMs();
        if (IsTooCloseToOtherNpc(town, native, 220f))
            this.NextWanderDecisionAtMs = 0;

        if (this.LastWanderUpdateAtMs <= 0)
            this.LastWanderUpdateAtMs = now;

        float dt = Math.Clamp((now - this.LastWanderUpdateAtMs) / 1000f, 0f, 0.10f);
        this.LastWanderUpdateAtMs = now;

        // Keep a real personal-space bubble even though MiMi's pretty sprite is custom-drawn.
        // The hidden native NPC provides collision where possible; this gentle escape handles
        // modded maps/actors which ignore invisible-NPC collision and prevents visual stacking.
        if (Game1.player.currentLocation == town)
        {
            Vector2 mimiFeet = native.Position + new Vector2(32f, 64f);
            Vector2 playerFeet = Game1.player.Position + new Vector2(32f, 64f);
            Vector2 away = mimiFeet - playerFeet;
            const float personalSpace = 78f;
            if (away.LengthSquared() < personalSpace * personalSpace)
            {
                if (away.LengthSquared() < 0.01f)
                    away = native.FacingDirection == 1 ? Vector2.UnitX : -Vector2.UnitX;
                else
                    away.Normalize();

                float escapeStep = Math.Max(1.5f, WanderSpeedPixelsPerSecond * dt * 1.35f);
                Vector2 escapeCandidate = native.Position + away * escapeStep;
                if (IsMimiFootprintClear(town, escapeCandidate)
                    && IsMimiClearOfOtherNpcs(town, native, escapeCandidate, 92f))
                {
                    native.Position = escapeCandidate;
                    this.WanderTarget = escapeCandidate;
                    this.NextWanderDecisionAtMs = now + 750;

                    int escapeFacing = Math.Abs(away.X) >= Math.Abs(away.Y)
                        ? (away.X >= 0f ? 1 : 3)
                        : (away.Y >= 0f ? 2 : 0);
                    native.faceDirection(escapeFacing);
                    this.WanderFacing = escapeFacing;
                    SetNativeWalkFrame(native, escapeFacing, 1 + (int)(now / 170L) % 3);
                    return;
                }
            }
        }

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
        if (!IsWorldPositionSafeForMiMi(town, nextPosition, native))
        {
            this.WanderTarget = native.Position;
            this.NextWanderDecisionAtMs = now + 900;
            SetNativeWalkFrame(native, this.WanderFacing, 0);
            return;
        }
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

    private void EnsureConversationSpacing(NPC native)
    {
        if (native.currentLocation != Game1.currentLocation)
            return;

        Vector2 player = Game1.player.Position;
        Vector2 delta = native.Position - player;
        const float desired = 112f;
        if (delta.LengthSquared() >= desired * desired)
            return;

        Vector2[] candidates =
        {
            player + new Vector2(desired, 0f),
            player + new Vector2(-desired, 0f),
            player + new Vector2(0f, desired),
            player + new Vector2(0f, -desired)
        };

        GameLocation location = native.currentLocation;
        foreach (Vector2 candidate in candidates.OrderBy(v => Vector2.DistanceSquared(v, native.Position)))
        {
            if (IsWorldPositionSafeForMiMi(location, candidate, native))
            {
                native.Position = candidate;
                this.WanderTarget = candidate;
                return;
            }
        }
    }

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
