using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// Alpha28 .5.11 home/schedule layer for MiMi, including her unlocked 17:30 secret-TV routine.
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
    private static readonly Point SecretTvWatchTile = new(6, 10);
    private static readonly Point SecretLateHomeTile = new(13, 7);
    private const float StairUseDistance = 112f;

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly WorldActorService WorldActors;
    private readonly Func<bool> StoryOwnsMimiActor;
    private readonly Func<bool> MysteryOwnsMimiActor;

    private Point? CachedWizardStairTile;
    private Point? CachedAtticStairTile;
    private bool LoggedAtticCreation;
    private bool AtticCreationFailed;
    private bool LoggedAtticFailure;
    private long AtticAutoExitBlockedUntilMs;

    public MimiHomeService(
        IModHelper helper,
        IMonitor monitor,
        SaveService save,
        WorldActorService worldActors,
        Func<bool> storyOwnsMimiActor,
        Func<bool> mysteryOwnsMimiActor)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.WorldActors = worldActors;
        this.StoryOwnsMimiActor = storyOwnsMimiActor;
        this.MysteryOwnsMimiActor = mysteryOwnsMimiActor;
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

        if (!this.Save.Data.MimiMeetupCompleted)
            return;

        // Run after MimiMysteryTownService every tick. This makes the post-meetup home layer the
        // final authority outside the legacy 11:00-17:00 merchant routine, without visible flicker.
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
            // At 6+ hearts MiMi really spends 17:30-22:00 in the TV nook. Talking to her there
            // gets routine-specific dialogue instead of falling through to the old mystery lines.
            if (this.IsSecretTvRoutineNow())
            {
                NPC? mimi = this.WorldActors.FindMimiActor();
                if (mimi is not null
                    && mimi.currentLocation == location
                    && PlayerIsNearNpc(mimi, 118f))
                {
                    this.Helper.Input.Suppress(e.Button);
                    Game1.drawObjectDialogue(this.T(this.ResolveSecretTvTalkKey()));
                    return;
                }
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
            Game1.warpFarmer("WizardHouse", landing.X, landing.Y, 2);
            return "Attic TEST bypass: returned to WizardHouse. Normal progression was not changed.";
        }

        GameLocation? attic = this.EnsureAtticLocation();
        if (attic is null)
            return "Attic TEST bypass couldn't create Cardcha_MiMiAttic.";

        Point arrival = this.ResolveAtticStairTile(attic);
        this.AtticAutoExitBlockedUntilMs = Environment.TickCount64 + 850;
        Game1.warpFarmer(AtticLocationName, arrival.X, Math.Max(1, arrival.Y - 1), 0);
        return "Attic TEST bypass: warped to Cardcha_MiMiAttic. Run cardcha_test_attic again to leave. Normal progression was not changed.";
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
        return $"MiMiHome=Attic({attic is not null}) | AtticAccess={this.GetMimiHearts()}/{AtticAccessHearts} hearts | WizardStair={wizardStair.X},{wizardStair.Y} | WorkRoute={route} | WorkHours=11:00-17:00 | SecretTV={secretTv} 17:30-22:00";
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
        if (!Context.IsWorldReady
            || !this.Save.Data.MimiMeetupCompleted
            || this.StoryOwnsMimiActor()
            || this.MysteryOwnsMimiActor()
            || Game1.eventUp)
        {
            return;
        }

        NPC? mimi = this.WorldActors.FindMimiActor() ?? this.WorldActors.EnsureMimiActor();
        if (mimi is null)
            return;

        bool weekday = IsWeekday();
        bool workHours = weekday && Game1.timeOfDay >= WorkStart && Game1.timeOfDay < WorkEnd;

        // Before/after work and weekends, MiMi actually lives upstairs now instead of vanishing
        // into the old hidden holding tile.
        if (!workHours)
        {
            GameLocation? attic = this.EnsureAtticLocation();
            if (attic is null)
                return;

            // The secret TV routine is friendship-gated and only owns the evening window.
            // We resolve against the real furniture collision so a future decor nudge can't strand MiMi.
            if (this.IsSecretTvRoutineNow())
            {
                Point tv = FindClearTileNear(attic, SecretTvWatchTile);
                PlaceMimi(mimi, attic, tv, 0); // face north toward the TV
                return;
            }

            // After the show window, high-friendship MiMi winds down by her personal corner.
            // Lower friendship preserves the pre-0646 generic home placement exactly.
            if (this.IsSecretTvRoutineUnlocked() && Game1.timeOfDay >= SecretTvEnd)
            {
                Point lateHome = FindClearTileNear(attic, SecretLateHomeTile);
                PlaceMimi(mimi, attic, lateHome, 1);
                return;
            }

            Point home = FindClearTileNear(attic, preferUpperHalf: true);
            PlaceMimi(mimi, attic, home, 2);
            return;
        }

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
        int width = wizard.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 12;
        int height = wizard.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 10;
        Point preferred = new(
            Math.Clamp(width - 2, 2, Math.Max(2, width - 2)),
            Math.Clamp((int)Math.Round(height * 0.20f), 2, Math.Max(2, height - 3))
        );
        // Keep the entrance visually fixed and one tile farther right / higher than 0.7.7.5,
        // separating the ladder from the fireplace while preserving the safe landing resolver.
        // Never re-run a nearest-clear search here, or the ladder can visually move as tiles change.
        return preferred;
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
