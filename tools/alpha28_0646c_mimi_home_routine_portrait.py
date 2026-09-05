from pathlib import Path
import json

ROOT = Path('src/Cardcha')

def replace_once(path: Path, old: str, new: str):
    text = path.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'missing expected block in {path}: {old[:120]!r}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')

# Version bump.
for rel in ['manifest.json', 'Cardcha.csproj', 'Directory.Build.targets']:
    p = ROOT / rel
    text = p.read_text(encoding='utf-8')
    text = text.replace('0.3.0-alpha.28.0.4.14.4.5.11.2', '0.3.0-alpha.28.0.4.14.4.5.11.3')
    p.write_text(text, encoding='utf-8')

home = ROOT / 'Services/MimiHomeService.cs'
text = home.read_text(encoding='utf-8')
text = text.replace('Alpha28 .5.11.2 home routine fix: fixed anchors, no home shop, direct routine TEST states.',
                    'Alpha28 .5.11.3 home routine fix: living idle movement + master-derived Cardcha home dialogue.')

text = text.replace(
'''    private static readonly Point DefaultHomeTile = new(10, 4);\n    private static readonly Point SecretTvWatchTile = new(5, 10);\n    private static readonly Point SecretLateHomeTile = new(13, 7);\n    private const float StairUseDistance = 112f;''',
'''    private static readonly Point DefaultHomeTile = new(10, 4);\n    private static readonly Point SecretTvWatchTile = new(5, 10);\n    private static readonly Point SecretLateHomeTile = new(13, 7);\n    private static readonly Point[] HomeIdleTiles = { new(10, 4), new(9, 5), new(11, 5), new(10, 6) };\n    private static readonly Point[] TvIdleTiles = { new(5, 10), new(4, 10), new(6, 10), new(5, 9) };\n    private static readonly Point[] LateIdleTiles = { new(13, 7), new(13, 6), new(14, 7), new(12, 7) };\n    private const float HomeWalkSpeedPixelsPerSecond = 34f;\n    private const int HomePauseMinMs = 2200;\n    private const int HomePauseMaxMs = 4800;\n    private const float StairUseDistance = 112f;''')

text = text.replace(
'''    private long AtticAutoExitBlockedUntilMs;\n    private string? DebugRoutineOverride;''',
'''    private long AtticAutoExitBlockedUntilMs;\n    private string? DebugRoutineOverride;\n    private string? ActiveHomeRoutineState;\n    private Vector2 HomeWanderTarget;\n    private int HomeWanderIndex;\n    private int HomeWanderFacing = 2;\n    private long NextHomeWanderDecisionAtMs;\n    private long LastHomeWanderUpdateAtMs;''')

# Allow runtime TEST override even when the save hasn't completed the meetup, and update movement every tick.
text = text.replace(
'''        if (!this.Save.Data.MimiMeetupCompleted)\n            return;\n\n        // Run after MimiMysteryTownService every tick. This makes the post-meetup home layer the\n        // final authority outside the legacy 11:00-17:00 merchant routine, without visible flicker.\n        this.EnsureAtticLocation();\n        this.EnforceSchedule();''',
'''        // Runtime TEST override deliberately bypasses story/friendship gates without changing save data.\n        // This also means cardcha_test_mimi_routine works on a clean test save instead of being\n        // overwritten one tick later by the pre-meetup early return.\n        if (this.DebugRoutineOverride is not null)\n        {\n            this.EnsureAtticLocation();\n            this.EnforceSchedule();\n            return;\n        }\n\n        if (!this.Save.Data.MimiMeetupCompleted)\n            return;\n\n        // Run after MimiMysteryTownService every tick. Home movement is continuous but state\n        // transitions are stable, so MiMi walks instead of being teleported back to an anchor.\n        this.EnsureAtticLocation();\n        this.EnforceSchedule();''')

# Reset wander runtime on title return.
text = text.replace(
'''        this.LoggedAtticFailure = false;\n        this.DebugRoutineOverride = null;\n    }''',
'''        this.LoggedAtticFailure = false;\n        this.DebugRoutineOverride = null;\n        this.ResetHomeWanderRuntime();\n    }''', 1)

# Make all empty-hand attic talk use the crisp Cardcha portrait path, not native social checkAction.
old_attic = '''        if (location.NameOrUniqueName.Equals(AtticLocationName, StringComparison.OrdinalIgnoreCase))\n        {\n            // At 6+ hearts MiMi really spends 17:30-22:00 in the TV nook. Talking to her there\n            // gets routine-specific dialogue instead of falling through to the old mystery lines.\n            if (this.IsSecretTvRoutineNow())\n            {\n                NPC? mimi = this.WorldActors.FindMimiActor();\n                if (mimi is not null\n                    && mimi.currentLocation == location\n                    && PlayerIsNearNpc(mimi, 118f))\n                {\n                    this.Helper.Input.Suppress(e.Button);\n                    string text = this.T(this.ResolveSecretTvTalkKey());\n                    if (!this.ShowMimiPortraitDialogue(mimi, text))\n                        Game1.drawObjectDialogue(text);\n                    return;\n                }\n            }\n\n            Point stair = this.ResolveAtticStairTile(location);'''
new_attic = '''        if (location.NameOrUniqueName.Equals(AtticLocationName, StringComparison.OrdinalIgnoreCase))\n        {\n            // The attic is MiMi's home. Every empty-hand talk here is owned by HomeService so\n            // vanilla Social.checkAction can never swap in the small native 64px portrait file.\n            NPC? mimi = this.WorldActors.FindMimiActor();\n            if (Game1.player.ActiveObject is null\n                && mimi is not null\n                && mimi.currentLocation == location\n                && PlayerIsNearNpc(mimi, 150f))\n            {\n                this.Helper.Input.Suppress(e.Button);\n                Game1.player.Halt();\n                mimi.faceTowardFarmerForPeriod(1200, 3, false, Game1.player);\n                this.RegisterHomeTalkFriendship(mimi);\n                string key = this.ResolveHomeTalkKey();\n                string line = this.T(key);\n                if (!this.ShowMimiPortraitDialogue(mimi, line))\n                    Game1.drawObjectDialogue(line);\n                return;\n            }\n\n            Point stair = this.ResolveAtticStairTile(location);'''
if old_attic not in text:
    raise SystemExit('attic interaction block not found')
text = text.replace(old_attic, new_attic, 1)

start = text.index('    private void EnforceSchedule()')
end = text.index('    private void PlaceMimi(', start)
replacement = r'''    private void EnforceSchedule()
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

        if (!this.Save.Data.MimiMeetupCompleted
            || this.StoryOwnsMimiActor()
            || this.MysteryOwnsMimiActor())
        {
            this.ResetHomeWanderRuntime();
            return;
        }

        bool weekday = IsWeekday();
        bool workHours = weekday && Game1.timeOfDay >= WorkStart && Game1.timeOfDay < WorkEnd;

        if (!workHours)
        {
            GameLocation? attic = this.EnsureAtticLocation();
            if (attic is null)
                return;

            string state = this.IsSecretTvRoutineNow()
                ? "tv"
                : this.IsSecretTvRoutineUnlocked() && Game1.timeOfDay >= SecretTvEnd
                    ? "late"
                    : "home";
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
        int anchorFacing = state == "tv" ? 0 : state == "late" ? 1 : 2;

        bool stateChanged = !string.Equals(this.ActiveHomeRoutineState, state, StringComparison.OrdinalIgnoreCase);
        bool actorNeedsRecovery = mimi.currentLocation != attic || mimi.isInvisible.Value;
        if (stateChanged || actorNeedsRecovery)
        {
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
        return pool[0];
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

'''
text = text[:start] + replacement + text[end:]

home.write_text(text, encoding='utf-8')

# Social: defer every empty-hand attic interaction to HomeService, not only TV time.
mod = ROOT / 'ModEntry.cs'
mod_text = mod.read_text(encoding='utf-8')
mod_text = mod_text.replace('() => this.Home.OwnsSecretTvDialogueNow()', '() => this.Home.OwnsAnyAtticDialogueNow()', 1)
mod.write_text(mod_text, encoding='utf-8')

# Home-specific spoken lines, localized in both languages.
for rel, values in {
    'i18n/default.json': {
        'mimi.attic.routine.home.talk': "Up here I'm off the clock. Give me five minutes and I'll probably remember where I left the sensible notes.$1",
        'mimi.attic.routine.late.talk': "I'm winding down. Tea, one last note, then I am absolutely going to sleep this time.$1"
    },
    'i18n/vi.json': {
        'mimi.attic.routine.home.talk': "Ở trên này là hết giờ làm rồi nhé. Cho tôi năm phút, chắc tôi sẽ nhớ ra mình để mấy ghi chú nghiêm túc ở đâu.$1",
        'mimi.attic.routine.late.talk': "Tôi đang nghỉ dần đây. Uống trà, ghi nốt một dòng, rồi lần này nhất định tôi sẽ đi ngủ thật.$1"
    }
}.items():
    p = ROOT / rel
    data = json.loads(p.read_text(encoding='utf-8'))
    data.update(values)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print('alpha28 0646c generated')
