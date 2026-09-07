using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// Alpha28 .5.11.3 home routine fix: living idle movement + master-derived Cardcha home dialogue.
/// The location ID is intentionally stable from the first TEST so a custom attic map can replace
/// the temporary vanilla interior later without changing friendship/save references.
/// </summary>
internal sealed class MimiHomeService
{
    public const string AtticLocationName = "Cardcha_MiMiAttic";
    private const string AtticMapPath = "Maps/Cardcha_MiMiAttic";
    private const int AtticAccessHearts = 2;
    private const int WorkStart = 1100;
    private const int WorkEnd = 1700;
    private const int SecretTvHeartRequirement = 6;
    private const int SecretTvStart = 1730;
    private const int SecretTvEnd = 2200;
    private static readonly Point DefaultHomeTile = new(9, 8);
    private static readonly Point SecretTvWatchTile = new(5, 9);
    private static readonly Point SecretLateHomeTile = new(13, 7);
    private static readonly Point[] HomeIdleTiles = { new(9, 8), new(8, 8), new(10, 8), new(9, 9), new(10, 9) };
    private static readonly Point[] TvIdleTiles = { new(5, 9), new(6, 9), new(6, 10), new(7, 9) };
    private static readonly Point[] LateIdleTiles = { new(13, 7), new(14, 7), new(13, 8), new(14, 8) };
    private const float HomeWalkSpeedPixelsPerSecond = 34f;
    private const int HomePauseMinMs = 2200;
    private const int HomePauseMaxMs = 4800;
    private const float StairUseDistance = 112f;

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly WorldActorService WorldActors;
    private readonly Func<bool> StoryOwnsMimiActor;
    private readonly Func<bool> MysteryOwnsMimiActor;
    private readonly Func<NPC, string, bool> ShowMimiPortraitDialogue;

    private Point? CachedWizardStairTile;
    private Point? CachedAtticStairTile;
    private bool LoggedAtticCreation;
    private bool AtticCreationFailed;
    private bool LoggedAtticFailure;
    private long AtticAutoExitBlockedUntilMs;
    private string? DebugRoutineOverride;
    private bool TestAtticRoutinePreview;
    private int LastObservedRoutineTime = -1;
    private string? ActiveHomeRoutineState;
    private Vector2 HomeWanderTarget;
    private int HomeWanderIndex;
    private int HomeWanderFacing = 2;
    private long NextHomeWanderDecisionAtMs;
    private long LastHomeWanderUpdateAtMs;

    public MimiHomeService(
        IModHelper helper,
        IMonitor monitor,
        SaveService save,
        WorldActorService worldActors,
        Func<bool> storyOwnsMimiActor,
        Func<bool> mysteryOwnsMimiActor,
        Func<NPC, string, bool> showMimiPortraitDialogue)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.WorldActors = worldActors;
        this.StoryOwnsMimiActor = storyOwnsMimiActor;
        this.MysteryOwnsMimiActor = mysteryOwnsMimiActor;
        this.ShowMimiPortraitDialogue = showMimiPortraitDialogue;
    }

    public void OnSaveLoaded()
    {
        this.CachedWizardStairTile = null;
        this.CachedAtticStairTile = null;
        this.AtticCreationFailed = false;
        this.LoggedAtticFailure = false;
        this.EnsureAtticLocation();
        this.EnforceSchedule();
    }

    public void OnDayStarted()
    {
        this.CachedWizardStairTile = null;
        this.CachedAtticStairTile = null;
        this.AtticCreationFailed = false;
        this.LoggedAtticFailure = false;
        this.EnsureAtticLocation();
        this.EnforceSchedule();
    }

    public void OnUpdateTicked(UpdateTickedEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        // The bottom-center landing is a real exit now. This runs even for the runtime-only
        // test bypass, but a short arrival grace period prevents immediately bouncing back out.
        this.TryAutoExitAttic();

        // Runtime TEST override deliberately bypasses story/friendship gates without changing save data.
        // This also means cardcha_test_mimi_routine works on a clean test save instead of being
        // overwritten one tick later by the pre-meetup early return.
        if (this.DebugRoutineOverride is not null)
        {
            this.EnsureAtticLocation();
            this.EnforceSchedule();
            return;
        }

        if (!this.Save.Data.MimiMeetupCompleted && !this.TestAtticRoutinePreview)
            return;

        // Run after MimiMysteryTownService every tick. Home movement is continuous but state
        // transitions are stable, so MiMi walks instead of being teleported back to an anchor.
        this.EnsureAtticLocation();
        this.EnforceSchedule();
    }

    public void OnReturnedToTitle()
    {
        this.CachedWizardStairTile = null;
        this.CachedAtticStairTile = null;
        this.LoggedAtticCreation = false;
        this.AtticCreationFailed = false;
        this.LoggedAtticFailure = false;
        this.DebugRoutineOverride = null;
        this.TestAtticRoutinePreview = false;
        this.LastObservedRoutineTime = -1;
        this.ResetHomeWanderRuntime();
    }

    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady
            || !this.Save.Data.MimiMeetupCompleted
            || !e.Button.IsActionButton()
            || Game1.activeClickableMenu is not null
            || Game1.dialogueUp
            || Game1.eventUp)
        {
            return;
        }

        GameLocation? location = Game1.currentLocation;
        if (location is null)
            return;

        if (location.NameOrUniqueName.Equals("WizardHouse", StringComparison.OrdinalIgnoreCase))
        {
            Point stair = this.ResolveWizardStairTile(location);
            if (!PlayerIsNear(stair))
                return;

            this.Helper.Input.Suppress(e.Button);
            int hearts = this.GetMimiHearts();
            if (hearts < AtticAccessHearts)
            {
                Game1.drawObjectDialogue(this.T("mimi.attic.locked", new { hearts = AtticAccessHearts }));
                return;
            }

            GameLocation? attic = this.EnsureAtticLocation();
            if (attic is null)
            {
                Game1.drawObjectDialogue(this.T("mimi.attic.unavailable"));
                return;
            }

            Point arrival = this.ResolveAtticStairTile(attic);
            this.AtticAutoExitBlockedUntilMs = Environment.TickCount64 + 850;
            Game1.warpFarmer(AtticLocationName, arrival.X, Math.Max(1, arrival.Y - 1), 0);
            return;
        }

        if (location.NameOrUniqueName.Equals(AtticLocationName, StringComparison.OrdinalIgnoreCase))
        {
            // The attic is MiMi's home. Every empty-hand talk here is owned by HomeService so
            // vanilla Social.checkAction can never swap in the small native 64px portrait file.
            NPC? mimi = this.WorldActors.FindMimiActor();
            if (Game1.player.ActiveObject is null
                && mimi is not null
                && mimi.currentLocation == location
                && PlayerIsNearNpc(mimi, 150f))
            {
                this.Helper.Input.Suppress(e.Button);
                Game1.player.Halt();
                mimi.faceTowardFarmerForPeriod(1200, 3, false, Game1.player);
                this.RegisterHomeTalkFriendship(mimi);
                string key = this.ResolveHomeTalkKey();
                string line = this.T(key);
                if (!this.ShowMimiPortraitDialogue(mimi, line))
                    Game1.drawObjectDialogue(line);
                return;
            }

            Point stair = this.ResolveAtticStairTile(location);
            if (!PlayerIsNear(stair))
                return;

            this.Helper.Input.Suppress(e.Button);
            GameLocation? wizard = Game1.getLocationFromName("WizardHouse");
            Point target = wizard is null ? new Point(4, 6) : this.ResolveWizardStairTile(wizard);
            Point landing = wizard is null ? new Point(target.X, target.Y + 1) : ResolveWizardLandingTile(wizard, target);
            Game1.warpFarmer("WizardHouse", landing.X, landing.Y, 2);
        }
    }

    /// <summary>
    /// TEST-only attic access. This never changes friendship, meetup flags, or save progression.
    /// Run the command again from inside the attic to return to WizardHouse.
    /// </summary>
    public string DebugToggleAtticAccess()
    {
        if (!Context.IsWorldReady)
            return "Attic TEST bypass unavailable: load a save first.";

        GameLocation? current = Game1.currentLocation;
        if (current is not null
            && current.NameOrUniqueName.Equals(AtticLocationName, StringComparison.OrdinalIgnoreCase))
        {
            GameLocation? wizard = Game1.getLocationFromName("WizardHouse");
            if (wizard is null)
                return "Attic TEST bypass couldn't find WizardHouse.";

            Point target = this.ResolveWizardStairTile(wizard);
            Point landing = ResolveWizardLandingTile(wizard, target);
            this.TestAtticRoutinePreview = false;
            this.LastObservedRoutineTime = -1;
            this.ResetHomeWanderRuntime();
            Game1.warpFarmer("WizardHouse", landing.X, landing.Y, 2);
            this.EnforceSchedule();
            return "Attic TEST bypass: returned to WizardHouse. Runtime clock preview disabled; normal progression was not changed.";
        }

        GameLocation? attic = this.EnsureAtticLocation();
        if (attic is null)
            return "Attic TEST bypass couldn't create Cardcha_MiMiAttic.";

        Point arrival = this.ResolveAtticStairTile(attic);
        this.TestAtticRoutinePreview = true;
        this.LastObservedRoutineTime = -1;
        this.ResetHomeWanderRuntime();
        this.AtticAutoExitBlockedUntilMs = Environment.TickCount64 + 850;
        this.EnforceSchedule();
        Game1.warpFarmer(AtticLocationName, arrival.X, Math.Max(1, arrival.Y - 1), 0);
        return "Attic TEST bypass: warped to Cardcha_MiMiAttic. Runtime clock preview ON, so world_settime 1720/1730/2000/2200 tests HOME/TV/TV/LATE without changing hearts/story. Run cardcha_test_attic again to leave.";
    }

    private void TryAutoExitAttic()
    {
        GameLocation? location = Game1.currentLocation;
        if (location is null
            || !location.NameOrUniqueName.Equals(AtticLocationName, StringComparison.OrdinalIgnoreCase)
            || Environment.TickCount64 < this.AtticAutoExitBlockedUntilMs)
        {
            return;
        }

        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 22;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 14;
        int tileX = (int)(Game1.player.Position.X / 64f);
        int tileY = (int)(Game1.player.Position.Y / 64f);
        int center = width / 2;

        // Only the two-tile bottom-center landing is an exit. Trigger on the final map row
        // before the farmer can visually wander into the black exterior void.
        if (tileY < height - 1 || tileX < center - 1 || tileX > center)
            return;

        GameLocation? wizard = Game1.getLocationFromName("WizardHouse");
        if (wizard is null)
            return;

        Point target = this.ResolveWizardStairTile(wizard);
        Point landing = ResolveWizardLandingTile(wizard, target);
        this.AtticAutoExitBlockedUntilMs = Environment.TickCount64 + 850;
        Game1.warpFarmer("WizardHouse", landing.X, landing.Y, 2);
    }

    public string Describe()
    {
        if (!Context.IsWorldReady)
            return "MiMiHome=<no save>";

        GameLocation? attic = Game1.getLocationFromName(AtticLocationName);
        Point wizardStair = this.ResolveWizardStairTile(Game1.getLocationFromName("WizardHouse"));
        string route = this.IsRestoredCommunityCenterRoute() ? "CommunityCenter" : this.IsJojaRoute() ? "Joja/Town" : "Town";
        string secretTv = this.IsSecretTvRoutineNow() ? "ACTIVE" : this.IsSecretTvRoutineUnlocked() ? "unlocked" : "locked";
        NPC? actor = this.WorldActors.FindMimiActor();
        string actorTile = actor is null ? "<missing>" : $"{(int)(actor.Position.X / 64f)},{(int)(actor.Position.Y / 64f)}@{actor.currentLocation?.NameOrUniqueName}";
        Point wanderTile = new((int)(this.HomeWanderTarget.X / 64f), (int)(this.HomeWanderTarget.Y / 64f));
        return $"MiMiHome=Attic({attic is not null}) | AtticAccess={this.GetMimiHearts()}/{AtticAccessHearts} hearts | WizardStair={wizardStair.X},{wizardStair.Y} | WorkRoute={route} | WorkHours=11:00-17:00 | SecretTV={secretTv} 17:30-22:00 | TestClockPreview={this.TestAtticRoutinePreview} | Clock={Game1.timeOfDay} | DebugRoutine={this.DebugRoutineOverride ?? "auto"} | RoutineState={this.ActiveHomeRoutineState ?? "<none>"} | WanderTarget={wanderTile.X},{wanderTile.Y} | Actor={actorTile}";
    }

    private GameLocation? EnsureAtticLocation()
    {
        if (!Context.IsWorldReady)
            return null;

        if (this.AtticCreationFailed)
            return null;

        GameLocation? existing = Game1.getLocationFromName(AtticLocationName);
        if (existing is not null)
            return existing;

        try
        {
            GameLocation attic = new(AtticMapPath, AtticLocationName);
            Game1.locations.Add(attic);
            this.CachedAtticStairTile = null;
            if (!this.LoggedAtticCreation)
            {
                this.LoggedAtticCreation = true;
                this.Monitor.Log($"Created MiMi attic location '{AtticLocationName}' using the alpha.27.0.7.7.5 fixed-ladder framed attic build.", LogLevel.Info);
            }
            return attic;
        }
        catch (Exception ex)
        {
            this.AtticCreationFailed = true;
            if (!this.LoggedAtticFailure)
            {
                this.LoggedAtticFailure = true;
                this.Monitor.Log(
                    $"Couldn't create MiMi attic location. Further retries are suppressed until the next save/day reload to prevent an exception loop. {ex.GetType().Name}: {ex.Message}",
                    LogLevel.Error
                );
            }
            return null;
        }
    }

    private void EnforceSchedule()
    {
        if (!Context.IsWorldReady || Game1.eventUp)
            return;

        NPC? mimi = this.WorldActors.FindMimiActor() ?? this.WorldActors.EnsureMimiActor();
        if (mimi is null)
            return;

        // Debug state is intentionally first and runtime-only.
        if (this.DebugRoutineOverride is not null)
        {
            GameLocation? debugAttic = this.EnsureAtticLocation();
            if (debugAttic is null)
                return;
            this.EnsureLivingAtticState(mimi, debugAttic, this.DebugRoutineOverride);
            return;
        }

        if ((!this.Save.Data.MimiMeetupCompleted && !this.TestAtticRoutinePreview)
            || this.StoryOwnsMimiActor()
            || this.MysteryOwnsMimiActor())
        {
            this.ResetHomeWanderRuntime();
            return;
        }

        bool weekday = IsWeekday();
        bool workHours = !this.TestAtticRoutinePreview && weekday && Game1.timeOfDay >= WorkStart && Game1.timeOfDay < WorkEnd;

        if (!workHours)
        {
            GameLocation? attic = this.EnsureAtticLocation();
            if (attic is null)
                return;

            bool routineUnlocked = this.IsSecretTvRoutineUnlocked() || this.TestAtticRoutinePreview;
            string state = routineUnlocked && Game1.timeOfDay >= SecretTvStart && Game1.timeOfDay < SecretTvEnd
                ? "tv"
                : routineUnlocked && Game1.timeOfDay >= SecretTvEnd
                    ? "late"
                    : "home";
            if (this.LastObservedRoutineTime != Game1.timeOfDay)
            {
                this.LastObservedRoutineTime = Game1.timeOfDay;
                this.NextHomeWanderDecisionAtMs = 0;
            }
            this.EnsureLivingAtticState(mimi, attic, state);
            return;
        }

        this.ResetHomeWanderRuntime();

        // Rain/harsh weather keeps the established Wizard-house merchant behavior. Once the
        // Community Center is restored through the non-Joja route, clear weekdays move her work
        // routine into the Community Center; otherwise the legacy Town merchant owns work hours.
        if (IsHarshWeather())
        {
            if (this.IsRestoredCommunityCenterRoute())
            {
                GameLocation? wizard = Game1.getLocationFromName("WizardHouse");
                if (wizard is not null)
                {
                    Point tile = FindClearTileNear(wizard, preferUpperHalf: false);
                    PlaceMimi(mimi, wizard, tile, 2);
                }
            }
            return;
        }

        if (!this.IsRestoredCommunityCenterRoute())
            return;

        GameLocation? center = Game1.getLocationFromName("CommunityCenter");
        if (center is null)
            return;

        Point work = FindClearTileNear(center, preferUpperHalf: false);
        PlaceMimi(mimi, center, work, 2);
    }

    private void EnsureLivingAtticState(NPC mimi, GameLocation attic, string state)
    {
        Point anchor = state switch
        {
            "tv" => SecretTvWatchTile,
            "late" => SecretLateHomeTile,
            _ => DefaultHomeTile
        };
        if (!IsTileClear(attic, anchor))
            anchor = FindClearTileNear(attic, anchor);
        int anchorFacing = state == "tv" ? 0 : state == "late" ? 1 : 2;

        bool stateChanged = !string.Equals(this.ActiveHomeRoutineState, state, StringComparison.OrdinalIgnoreCase);
        bool actorNeedsRecovery = mimi.currentLocation != attic || mimi.isInvisible.Value;
        if (stateChanged || actorNeedsRecovery)
        {
            if (stateChanged)
                this.Monitor.Log($"MiMi attic routine -> {state.ToUpperInvariant()} at {Game1.timeOfDay} (preview={this.TestAtticRoutinePreview}, hearts={this.GetMimiHearts()}).", LogLevel.Trace);
            PlaceMimi(mimi, attic, anchor, anchorFacing);
            this.ActiveHomeRoutineState = state;
            this.HomeWanderIndex = 0;
            this.HomeWanderFacing = anchorFacing;
            this.HomeWanderTarget = new Vector2(anchor.X * 64f, anchor.Y * 64f);
            long now = CurrentGameMs();
            this.LastHomeWanderUpdateAtMs = now;
            this.NextHomeWanderDecisionAtMs = now + 900L;
        }
        else
        {
            this.WorldActors.ConfigureMimiActor(mimi, broom: false, visible: true);
            mimi.displayName = "MiMi";
            mimi.hideShadow.Value = false;
        }

        this.UpdateHomeWander(mimi, attic, state);
    }

    private void UpdateHomeWander(NPC mimi, GameLocation attic, string state)
    {
        long now = CurrentGameMs();
        if (Game1.dialogueUp || Game1.activeClickableMenu is not null)
        {
            this.HomeWanderTarget = mimi.Position;
            this.NextHomeWanderDecisionAtMs = Math.Max(this.NextHomeWanderDecisionAtMs, now + 900L);
            this.LastHomeWanderUpdateAtMs = now;
            this.WorldActors.SetMimiFrame(mimi, mimi.FacingDirection, 0);
            return;
        }

        Point[] pool = state switch
        {
            "tv" => TvIdleTiles,
            "late" => LateIdleTiles,
            _ => HomeIdleTiles
        };

        if (this.LastHomeWanderUpdateAtMs <= 0)
            this.LastHomeWanderUpdateAtMs = now;
        float dt = Math.Clamp((now - this.LastHomeWanderUpdateAtMs) / 1000f, 0f, 0.10f);
        this.LastHomeWanderUpdateAtMs = now;

        Vector2 delta = this.HomeWanderTarget - mimi.Position;
        float distance = delta.Length();
        if (distance <= 3f)
        {
            mimi.Position = this.HomeWanderTarget;
            this.WorldActors.SetMimiFrame(mimi, this.HomeWanderFacing, 0);
            if (now >= this.NextHomeWanderDecisionAtMs)
            {
                Point next = this.ChooseNextHomeTile(attic, pool);
                this.HomeWanderTarget = new Vector2(next.X * 64f, next.Y * 64f);
                int spread = Math.Max(1, HomePauseMaxMs - HomePauseMinMs);
                int jitter = (int)((now / 149L + this.HomeWanderIndex * 613L) % spread);
                this.NextHomeWanderDecisionAtMs = now + HomePauseMinMs + jitter;
            }
            return;
        }

        Vector2 direction = delta / Math.Max(0.001f, distance);
        float step = Math.Min(distance, HomeWalkSpeedPixelsPerSecond * dt);
        Vector2 nextPosition = mimi.Position + direction * step;
        mimi.Position = nextPosition;

        int facing = Math.Abs(direction.X) >= Math.Abs(direction.Y)
            ? direction.X >= 0f ? 1 : 3
            : direction.Y >= 0f ? 2 : 0;
        this.HomeWanderFacing = facing;
        mimi.faceDirection(facing);
        int walkFrame = 1 + (int)(now / 180L) % 3;
        this.WorldActors.SetMimiFrame(mimi, facing, walkFrame);
    }

    private Point ChooseNextHomeTile(GameLocation attic, Point[] pool)
    {
        for (int attempt = 0; attempt < pool.Length; attempt++)
        {
            this.HomeWanderIndex = (this.HomeWanderIndex + 1) % pool.Length;
            Point candidate = pool[this.HomeWanderIndex];
            if (IsTileClear(attic, candidate))
                return candidate;
        }
        return FindClearTileNear(attic, pool[0]);
    }

    private void ResetHomeWanderRuntime()
    {
        this.ActiveHomeRoutineState = null;
        this.HomeWanderTarget = Vector2.Zero;
        this.HomeWanderIndex = 0;
        this.HomeWanderFacing = 2;
        this.NextHomeWanderDecisionAtMs = 0;
        this.LastHomeWanderUpdateAtMs = 0;
    }

    public string DebugForceRoutine(string mode)
    {
        if (!Context.IsWorldReady)
            return "MiMi routine TEST unavailable: load a save first.";

        mode = (mode ?? "auto").Trim().ToLowerInvariant();
        if (mode == "auto")
        {
            this.DebugRoutineOverride = null;
            this.ResetHomeWanderRuntime();
            this.EnforceSchedule();
            return "MiMi routine TEST: AUTO restored. Friendship/time rules own MiMi again.";
        }
        if (mode is not ("home" or "tv" or "late"))
            return "Usage: cardcha_test_mimi_routine <home|tv|late|auto>";

        GameLocation? attic = this.EnsureAtticLocation();
        NPC? mimi = this.WorldActors.FindMimiActor() ?? this.WorldActors.EnsureMimiActor();
        if (attic is null || mimi is null)
            return "MiMi routine TEST couldn't resolve the attic/NPC.";

        this.DebugRoutineOverride = mode;
        this.ResetHomeWanderRuntime();
        this.EnsureLivingAtticState(mimi, attic, mode);
        Point tile = new((int)(mimi.Position.X / 64f), (int)(mimi.Position.Y / 64f));
        return $"MiMi routine TEST: forced {mode.ToUpperInvariant()} at ({tile.X},{tile.Y}); living wander active. Runtime-only; use auto to release.";
    }

    internal bool OwnsSecretTvDialogueNow()
        => (this.DebugRoutineOverride == "tv" || this.IsSecretTvRoutineNow())
           && Game1.currentLocation?.NameOrUniqueName.Equals(AtticLocationName, StringComparison.OrdinalIgnoreCase) == true;

    internal bool OwnsAnyAtticDialogueNow()
        => Game1.currentLocation?.NameOrUniqueName.Equals(AtticLocationName, StringComparison.OrdinalIgnoreCase) == true;

    private string ResolveHomeTalkKey()
    {
        if (this.DebugRoutineOverride == "tv" || this.IsSecretTvRoutineNow())
            return this.ResolveSecretTvTalkKey();
        if (this.DebugRoutineOverride == "late" || (this.IsSecretTvRoutineUnlocked() && Game1.timeOfDay >= SecretTvEnd))
            return "mimi.attic.routine.late.talk";
        return "mimi.attic.routine.home.talk";
    }

    private void RegisterHomeTalkFriendship(NPC mimi)
    {
        try
        {
            if (!Game1.player.friendshipData.TryGetValue(MimiMysteryTownService.NpcId, out Friendship? friendship)
                || friendship is null
                || friendship.TalkedToToday)
                return;
            friendship.TalkedToToday = true;
            friendship.Points += 20;
        }
        catch (Exception ex)
        {
            this.Monitor.Log($"MiMi home friendship talk bookkeeping skipped: {ex.Message}", LogLevel.Trace);
        }
    }

    private static long CurrentGameMs()
        => (long)Game1.currentGameTime.TotalGameTime.TotalMilliseconds;

    private void PlaceMimi(NPC mimi, GameLocation target, Point tile, int facing)
    {
        Vector2 world = new(tile.X * 64f, tile.Y * 64f);
        if (mimi.currentLocation == target && !mimi.isInvisible.Value)
        {
            int currentX = (int)(mimi.Position.X / 64f);
            int currentY = (int)(mimi.Position.Y / 64f);
            if (currentX == tile.X && currentY == tile.Y)
            {
                this.WorldActors.ConfigureMimiActor(mimi, broom: false, visible: true);
                mimi.faceDirection(facing);
                mimi.displayName = "MiMi";
                mimi.hideShadow.Value = false;
                return;
            }
        }

        // A same-location move is intentional here. Before .5.11 PlaceMimi returned early whenever
        // MiMi was already in the attic, which meant a timed home routine could never reposition her.
        this.WorldActors.MoveMimiActor(mimi, target, world, facing, broom: false, visible: true);
        mimi.displayName = "MiMi";
        mimi.hideShadow.Value = false;
    }

    private Point ResolveWizardStairTile(GameLocation? wizard)
    {
        if (wizard is null)
            return new Point(4, 6);
        if (this.CachedWizardStairTile is Point cached)
            return cached;

        this.CachedWizardStairTile = ResolvePreferredWizardStairTile(wizard);
        return this.CachedWizardStairTile.Value;
    }

    internal static Point ResolvePreferredWizardStairTile(GameLocation wizard)
    {
        // 0655: x16 proved to be the right-wall/foreign-content column in-game. Keep the known-good
        // solid/interaction anchor at x15, then nudge the ladder artwork itself four screen pixels
        // to the right (one source pixel) so it sits closer to the wall without entering it.
        return new Point(15, 15);
    }

    private static Point ResolveWizardLandingTile(GameLocation wizard, Point stair)
    {
        Point[] candidates =
        {
            new(stair.X, stair.Y + 1),
            new(stair.X, stair.Y + 2),
            new(stair.X - 1, stair.Y + 1),
            new(stair.X + 1, stair.Y + 1),
            new(stair.X - 1, stair.Y + 2),
            new(stair.X + 1, stair.Y + 2),
            new(stair.X, stair.Y + 3)
        };

        foreach (Point candidate in candidates)
        {
            if (IsTileClear(wizard, candidate))
                return candidate;
        }

        return FindClearTileNear(wizard, new Point(stair.X, stair.Y + 2));
    }

    private Point ResolveAtticStairTile(GameLocation attic)
    {
        if (this.CachedAtticStairTile is Point cached)
            return cached;

        int width = attic.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 12;
        int height = attic.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 10;
        int x = Math.Clamp(width / 2, 1, Math.Max(1, width - 2));
        int startY = Math.Max(1, height - 3);
        for (int y = startY; y >= 1; y--)
        {
            Point candidate = new(x, y);
            if (IsTileClear(attic, candidate))
            {
                this.CachedAtticStairTile = candidate;
                return candidate;
            }
        }

        this.CachedAtticStairTile = new Point(x, startY);
        return this.CachedAtticStairTile.Value;
    }

    private static Point FindClearTileNear(GameLocation location, bool preferUpperHalf)
    {
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 12;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 10;
        Point preferred = new(
            Math.Clamp(width / 2, 2, Math.Max(2, width - 3)),
            preferUpperHalf
                ? Math.Clamp(height / 3, 2, Math.Max(2, height - 3))
                : Math.Clamp(height / 2, 2, Math.Max(2, height - 3))
        );
        return FindClearTileNear(location, preferred);
    }

    private static Point FindClearTileNear(GameLocation location, Point preferred)
    {
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 12;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 10;
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
                    Point p = new(x, y);
                    if (IsTileClear(location, p))
                        return p;
                }
            }
        }

        return new Point(centerX, centerY);
    }

    private static bool IsTileClear(GameLocation location, Point tile)
    {
        try
        {
            Vector2 v = new(tile.X, tile.Y);
            if (location.IsTileBlockedBy(v))
                return false;
            if (location.Objects.ContainsKey(v))
                return false;
            return true;
        }
        catch
        {
            return true;
        }
    }

    private static bool PlayerIsNear(Point tile)
    {
        Vector2 marker = new(tile.X * 64f + 32f, tile.Y * 64f + 32f);
        Vector2 player = Game1.player.Position + new Vector2(32f, 32f);
        return Vector2.DistanceSquared(marker, player) <= StairUseDistance * StairUseDistance;
    }

    private bool IsSecretTvRoutineUnlocked()
        => this.GetMimiHearts() >= SecretTvHeartRequirement;

    private bool IsSecretTvRoutineNow()
        => Context.IsWorldReady
           && this.IsSecretTvRoutineUnlocked()
           && Game1.timeOfDay >= SecretTvStart
           && Game1.timeOfDay < SecretTvEnd;

    private string ResolveSecretTvTalkKey()
    {
        if (this.Save.Data.ChaChaLoaned)
            return "mimi.attic.routine.tv.talk.chacha-away";
        if (Game1.timeOfDay >= 2000)
            return "mimi.attic.routine.tv.talk.late";
        return "mimi.attic.routine.tv.talk.early";
    }

    private static bool PlayerIsNearNpc(NPC npc, float distance)
    {
        Vector2 npcCenter = npc.Position + new Vector2(32f, 32f);
        Vector2 playerCenter = Game1.player.Position + new Vector2(32f, 32f);
        return Vector2.DistanceSquared(npcCenter, playerCenter) <= distance * distance;
    }

    private int GetMimiHearts()
    {
        if (!Context.IsWorldReady
            || !Game1.player.friendshipData.TryGetValue(MimiMysteryTownService.NpcId, out Friendship? friendship)
            || friendship is null)
        {
            return 0;
        }
        return Math.Max(0, friendship.Points / 250);
    }

    private bool IsRestoredCommunityCenterRoute()
    {
        if (!Context.IsWorldReady || this.IsJojaRoute())
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

    private bool IsJojaRoute()
        => Context.IsWorldReady && Game1.MasterPlayer.mailReceived.Contains("JojaMember");

    private static bool IsWeekday()
    {
        int dayIndex = (Math.Max(1, Game1.dayOfMonth) - 1) % 7;
        return dayIndex <= 4;
    }

    private static bool IsHarshWeather()
        => Game1.isRaining || Game1.isSnowing || Game1.isLightning;

    private string T(string key, object? tokens = null)
        => tokens is null
            ? this.Helper.Translation.Get(key).ToString()
            : this.Helper.Translation.Get(key, tokens).ToString();
}
