from pathlib import Path

ROOT = Path("src/Cardcha")
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.11"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.11.1"


def replace_version(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if NEW_VERSION in text:
        return
    if OLD_VERSION not in text:
        raise RuntimeError(f"Expected {OLD_VERSION} in {path}")
    path.write_text(text.replace(OLD_VERSION, NEW_VERSION), encoding="utf-8")


def patch_mystery_service() -> None:
    path = ROOT / "Services" / "MimiMysteryTownService.cs"
    text = path.read_text(encoding="utf-8")

    anchor = "    private bool TryShowDialogueWithPortrait(NPC speaker, string text)\n"
    wrapper = '''    internal void PrepareCrispPortrait(NPC speaker)\n    {\n        this.EnsureTextures();\n        AssignPortraitTexture(speaker, this.RuntimePortraitSheet);\n    }\n\n    internal bool TryShowCrispPortraitDialogue(NPC speaker, string text)\n        => this.TryShowDialogueWithPortrait(speaker, text);\n\n'''
    if "PrepareCrispPortrait" not in text:
        if anchor not in text:
            raise RuntimeError("Could not find MiMi portrait dialogue anchor")
        text = text.replace(anchor, wrapper + anchor, 1)

    for token in ["PrepareCrispPortrait", "TryShowCrispPortraitDialogue", "AssignPortraitTexture(speaker, this.RuntimePortraitSheet)"]:
        if token not in text:
            raise RuntimeError(f"Missing Mystery portrait token: {token}")

    path.write_text(text, encoding="utf-8")


def patch_home_service() -> None:
    path = ROOT / "Services" / "MimiHomeService.cs"
    text = path.read_text(encoding="utf-8")

    text = text.replace(
        "/// Alpha28 .5.11 home/schedule layer for MiMi, including her unlocked 17:30 secret-TV routine.",
        "/// Alpha28 .5.11.1 home/schedule hotfix: stable attic anchors + crisp portrait dialogue.",
        1,
    )

    field_anchor = "    private readonly Func<bool> MysteryOwnsMimiActor;\n"
    if "ShowMimiPortraitDialogue" not in text:
        if field_anchor not in text:
            raise RuntimeError("Could not find HomeService delegate field anchor")
        text = text.replace(
            field_anchor,
            field_anchor + "    private readonly Func<NPC, string, bool> ShowMimiPortraitDialogue;\n",
            1,
        )

    state_anchor = "    private long AtticAutoExitBlockedUntilMs;\n"
    if "CachedAtticRoutineKey" not in text:
        if state_anchor not in text:
            raise RuntimeError("Could not find HomeService runtime state anchor")
        text = text.replace(
            state_anchor,
            state_anchor
            + "    private string? CachedAtticRoutineKey;\n"
            + "    private Point? CachedAtticRoutineTile;\n",
            1,
        )

    old_ctor = '''        WorldActorService worldActors,\n        Func<bool> storyOwnsMimiActor,\n        Func<bool> mysteryOwnsMimiActor)\n    {\n        this.Helper = helper;\n        this.Monitor = monitor;\n        this.Save = save;\n        this.WorldActors = worldActors;\n        this.StoryOwnsMimiActor = storyOwnsMimiActor;\n        this.MysteryOwnsMimiActor = mysteryOwnsMimiActor;\n    }\n'''
    new_ctor = '''        WorldActorService worldActors,\n        Func<bool> storyOwnsMimiActor,\n        Func<bool> mysteryOwnsMimiActor,\n        Func<NPC, string, bool> showMimiPortraitDialogue)\n    {\n        this.Helper = helper;\n        this.Monitor = monitor;\n        this.Save = save;\n        this.WorldActors = worldActors;\n        this.StoryOwnsMimiActor = storyOwnsMimiActor;\n        this.MysteryOwnsMimiActor = mysteryOwnsMimiActor;\n        this.ShowMimiPortraitDialogue = showMimiPortraitDialogue;\n    }\n'''
    if old_ctor in text:
        text = text.replace(old_ctor, new_ctor, 1)
    elif "showMimiPortraitDialogue" not in text:
        raise RuntimeError("Could not patch HomeService constructor")

    # Reset stable anchor cache whenever the home layer resets its location cache.
    reset_needle = "        this.CachedAtticStairTile = null;\n"
    reset_repl = (
        "        this.CachedAtticStairTile = null;\n"
        "        this.CachedAtticRoutineKey = null;\n"
        "        this.CachedAtticRoutineTile = null;\n"
    )
    # SaveLoaded, DayStarted, ReturnedToTitle each contain this exact statement.
    if text.count("this.CachedAtticRoutineKey = null;") < 3:
        text = text.replace(reset_needle, reset_repl, 3)

    old_talk = '''                    this.Helper.Input.Suppress(e.Button);\n                    Game1.drawObjectDialogue(this.T(this.ResolveSecretTvTalkKey()));\n                    return;\n'''
    new_talk = '''                    this.Helper.Input.Suppress(e.Button);\n                    string text = this.T(this.ResolveSecretTvTalkKey());\n                    if (!this.ShowMimiPortraitDialogue(mimi, text))\n                        Game1.drawObjectDialogue(text);\n                    return;\n'''
    if old_talk in text:
        text = text.replace(old_talk, new_talk, 1)
    elif "ShowMimiPortraitDialogue(mimi, text)" not in text:
        raise RuntimeError("Could not patch secret-TV portrait dialogue")

    text = text.replace(
        "Point tv = FindClearTileNear(attic, SecretTvWatchTile);",
        "Point tv = this.ResolveStableAtticRoutineTile(attic, \"tv\", SecretTvWatchTile);",
        1,
    )
    text = text.replace(
        "Point lateHome = FindClearTileNear(attic, SecretLateHomeTile);",
        "Point lateHome = this.ResolveStableAtticRoutineTile(attic, \"late\", SecretLateHomeTile);",
        1,
    )
    text = text.replace(
        "Point home = FindClearTileNear(attic, preferUpperHalf: true);",
        "Point home = this.ResolveStableAtticRoutineTile(attic, \"home\");",
        1,
    )

    method_anchor = "    private void PlaceMimi(NPC mimi, GameLocation target, Point tile, int facing)\n"
    stable_method = '''    private Point ResolveStableAtticRoutineTile(GameLocation attic, string routineKey, Point? preferred = null)\n    {\n        if (this.CachedAtticRoutineKey == routineKey && this.CachedAtticRoutineTile is Point cached)\n            return cached;\n\n        Point resolved = preferred is Point target\n            ? FindClearTileNear(attic, target)\n            : FindClearTileNear(attic, preferUpperHalf: true);\n\n        this.CachedAtticRoutineKey = routineKey;\n        this.CachedAtticRoutineTile = resolved;\n        return resolved;\n    }\n\n    internal bool OwnsSecretTvDialogueNow()\n        => this.IsSecretTvRoutineNow()\n           && Game1.currentLocation?.NameOrUniqueName.Equals(AtticLocationName, StringComparison.OrdinalIgnoreCase) == true;\n\n'''
    if "ResolveStableAtticRoutineTile" not in text:
        if method_anchor not in text:
            raise RuntimeError("Could not find PlaceMimi anchor")
        text = text.replace(method_anchor, stable_method + method_anchor, 1)

    required = [
        "CachedAtticRoutineKey",
        "ResolveStableAtticRoutineTile(attic, \"tv\", SecretTvWatchTile)",
        "ResolveStableAtticRoutineTile(attic, \"late\", SecretLateHomeTile)",
        "ResolveStableAtticRoutineTile(attic, \"home\")",
        "OwnsSecretTvDialogueNow()",
        "ShowMimiPortraitDialogue(mimi, text)",
    ]
    for token in required:
        if token not in text:
            raise RuntimeError(f"Missing HomeService hotfix token: {token}")

    path.write_text(text, encoding="utf-8")


def patch_social_service() -> None:
    path = ROOT / "Services" / "MimiSocialService.cs"
    text = path.read_text(encoding="utf-8")

    field_anchor = "    private readonly Action OpenMimiShop;\n"
    if "PrepareMimiPortrait" not in text:
        text = text.replace(
            field_anchor,
            field_anchor
            + "    private readonly Action<NPC> PrepareMimiPortrait;\n"
            + "    private readonly Func<bool> DeferToHomeDialogue;\n",
            1,
        )

    old_ctor = '''        SaveService save,\n        WorldActorService worldActors,\n        Action openMimiShop)\n    {\n        this.Helper = helper;\n        this.Monitor = monitor;\n        this.Save = save;\n        this.WorldActors = worldActors;\n        this.OpenMimiShop = openMimiShop;\n    }\n'''
    new_ctor = '''        SaveService save,\n        WorldActorService worldActors,\n        Action openMimiShop,\n        Action<NPC> prepareMimiPortrait,\n        Func<bool> deferToHomeDialogue)\n    {\n        this.Helper = helper;\n        this.Monitor = monitor;\n        this.Save = save;\n        this.WorldActors = worldActors;\n        this.OpenMimiShop = openMimiShop;\n        this.PrepareMimiPortrait = prepareMimiPortrait;\n        this.DeferToHomeDialogue = deferToHomeDialogue;\n    }\n'''
    if old_ctor in text:
        text = text.replace(old_ctor, new_ctor, 1)
    elif "prepareMimiPortrait" not in text:
        raise RuntimeError("Could not patch SocialService constructor")

    friendship_anchor = '''        if (!Game1.player.friendshipData.TryGetValue(NpcId, out Friendship? friendship) || friendship is null)\n            return;\n\n        this.Helper.Input.Suppress(e.Button);\n'''
    friendship_repl = '''        if (!Game1.player.friendshipData.TryGetValue(NpcId, out Friendship? friendship) || friendship is null)\n            return;\n\n        // Empty-hand TV-nook interaction belongs to MimiHomeService so its routine-specific\n        // dialogue can use the same crisp runtime portrait as MiMi's story scenes. Gifts still\n        // flow through Stardew's native NPC handling.\n        if (Game1.player.ActiveObject is null && this.DeferToHomeDialogue())\n            return;\n\n        this.Helper.Input.Suppress(e.Button);\n'''
    if friendship_anchor in text:
        text = text.replace(friendship_anchor, friendship_repl, 1)
    elif "this.DeferToHomeDialogue()" not in text:
        raise RuntimeError("Could not add Home dialogue defer gate")

    native_anchor = '''        if (Game1.player.ActiveObject is not null || !friendship.TalkedToToday)\n        {\n            try\n            {\n                mimi.checkAction(Game1.player, Game1.currentLocation);\n'''
    native_repl = '''        if (Game1.player.ActiveObject is not null || !friendship.TalkedToToday)\n        {\n            try\n            {\n                // Vanilla social dialogue previously fell back to the coarse runtime64 PNG.\n                // Point the NPC at the same in-memory portrait sheet used by Cardcha story dialogue.\n                this.PrepareMimiPortrait(mimi);\n                mimi.checkAction(Game1.player, Game1.currentLocation);\n'''
    if native_anchor in text:
        text = text.replace(native_anchor, native_repl, 1)
    elif "this.PrepareMimiPortrait(mimi);" not in text:
        raise RuntimeError("Could not patch crisp vanilla social portrait")

    for token in ["PrepareMimiPortrait", "DeferToHomeDialogue", "this.PrepareMimiPortrait(mimi);", "this.DeferToHomeDialogue()"]:
        if token not in text:
            raise RuntimeError(f"Missing SocialService hotfix token: {token}")

    path.write_text(text, encoding="utf-8")


def patch_airship_service() -> None:
    path = ROOT / "Services" / "AirshipFoundationService.cs"
    text = path.read_text(encoding="utf-8")

    field_anchor = "    private bool LoggedAirshipVisualFailure;\n"
    if "TestGateAccessActive" not in text:
        text = text.replace(field_anchor, field_anchor + "    private bool TestGateAccessActive;\n", 1)

    text = text.replace(
        "if (this.Save.Data.AirshipUnlocked && IsSkyDockLocation(location))",
        "if ((this.Save.Data.AirshipUnlocked || this.TestGateAccessActive) && IsSkyDockLocation(location))",
        1,
    )
    text = text.replace(
        "if (IsSkyDockLocation(location) && this.Save.Data.AirshipUnlocked)",
        "if (IsSkyDockLocation(location) && (this.Save.Data.AirshipUnlocked || this.TestGateAccessActive))",
        1,
    )

    debug_anchor = "    /// <summary>TEST-only direct deck access; does not unlock the Airship or alter story flags.</summary>\n"
    debug_gate = '''    /// <summary>TEST-only warp to the Forest Arcane Gate; runtime access only, no save/story mutation.</summary>\n    public string DebugWarpToGate()\n    {\n        if (!Context.IsWorldReady)\n            return "Arcane Gate TEST unavailable: load a save first.";\n\n        GameLocation? forest = Game1.getLocationFromName(SkyDockLocationName);\n        if (forest is null)\n            return "Arcane Gate TEST couldn't find Forest.";\n\n        this.TestGateAccessActive = true;\n        this.CachedSkyDockTile = null;\n        Point dock = this.ResolveSkyDockTile();\n        Point landing = FindClearTileNear(forest, new Point(dock.X, dock.Y + 2));\n        this.WarpGraceUntilMs = Environment.TickCount64 + 850L;\n        Game1.warpFarmer(forest.NameOrUniqueName, landing.X, landing.Y, 0);\n        return $"Arcane Gate TEST: warped near Forest gate at ({dock.X},{dock.Y}). Runtime-only gate access is enabled until title reload; save/story unlock state was not changed.";\n    }\n\n'''
    if "DebugWarpToGate()" not in text:
        if debug_anchor not in text:
            raise RuntimeError("Could not find Airship debug method anchor")
        text = text.replace(debug_anchor, debug_gate + debug_anchor, 1)

    describe_token = 'return $"AirshipFlybySeen={this.Save.Data.AirshipFlybySeen} | " +'
    if "GateTest=" not in text and describe_token in text:
        text = text.replace(
            describe_token,
            'return $"GateTest={this.TestGateAccessActive} | " +\n               $"AirshipFlybySeen={this.Save.Data.AirshipFlybySeen} | " +',
            1,
        )

    for token in ["TestGateAccessActive", "DebugWarpToGate()", "AirshipUnlocked || this.TestGateAccessActive", "GateTest="]:
        if token not in text:
            raise RuntimeError(f"Missing Airship gate-test token: {token}")

    path.write_text(text, encoding="utf-8")


def patch_mod_entry() -> None:
    path = ROOT / "ModEntry.cs"
    text = path.read_text(encoding="utf-8")

    old_services = '''        this.Social = new MimiSocialService(\n            helper,\n            this.Monitor,\n            this.Save,\n            this.WorldActors,\n            this.OpenMimiShop\n        );\n        this.Home = new MimiHomeService(\n            helper,\n            this.Monitor,\n            this.Save,\n            this.WorldActors,\n            () => this.Story.OwnsMimiWorldActor,\n            () => this.Mystery.OwnsMimiWorldActor\n        );\n'''
    new_services = '''        this.Home = new MimiHomeService(\n            helper,\n            this.Monitor,\n            this.Save,\n            this.WorldActors,\n            () => this.Story.OwnsMimiWorldActor,\n            () => this.Mystery.OwnsMimiWorldActor,\n            (npc, text) => this.Mystery.TryShowCrispPortraitDialogue(npc, text)\n        );\n        this.Social = new MimiSocialService(\n            helper,\n            this.Monitor,\n            this.Save,\n            this.WorldActors,\n            this.OpenMimiShop,\n            npc => this.Mystery.PrepareCrispPortrait(npc),\n            () => this.Home.OwnsSecretTvDialogueNow()\n        );\n'''
    if old_services in text:
        text = text.replace(old_services, new_services, 1)
    elif "TryShowCrispPortraitDialogue" not in text:
        raise RuntimeError("Could not rewire MiMi home/social services")

    cmd_anchor = '        helper.ConsoleCommands.Add("cardcha_test_airship", "TEST ONLY: toggle direct Airship deck access without changing story progression.", this.CommandTestAirship);\n'
    cmd_line = '        helper.ConsoleCommands.Add("cardcha_test_gate", "TEST ONLY: warp directly beside the Forest Arcane Gate with runtime-only access.", this.CommandTestGate);\n'
    if "cardcha_test_gate" not in text:
        if cmd_anchor not in text:
            raise RuntimeError("Could not find Airship command registration anchor")
        text = text.replace(cmd_anchor, cmd_line + cmd_anchor, 1)

    handler_anchor = '''    private void CommandTestAirship(string command, string[] args)\n    {\n        this.Monitor.Log(this.Airship.DebugToggleDeck(), LogLevel.Alert);\n    }\n\n'''
    handler = '''    private void CommandTestGate(string command, string[] args)\n    {\n        this.Monitor.Log(this.Airship.DebugWarpToGate(), LogLevel.Alert);\n    }\n\n'''
    if "private void CommandTestGate" not in text:
        if handler_anchor not in text:
            raise RuntimeError("Could not find CommandTestAirship handler anchor")
        text = text.replace(handler_anchor, handler + handler_anchor, 1)

    for token in ["TryShowCrispPortraitDialogue", "PrepareCrispPortrait", "OwnsSecretTvDialogueNow", "cardcha_test_gate", "CommandTestGate", "DebugWarpToGate"]:
        if token not in text:
            raise RuntimeError(f"Missing ModEntry hotfix token: {token}")

    path.write_text(text, encoding="utf-8")


def main() -> None:
    for path in [ROOT / "manifest.json", ROOT / "Cardcha.csproj", ROOT / "Directory.Build.targets"]:
        replace_version(path)
    patch_mystery_service()
    patch_home_service()
    patch_social_service()
    patch_airship_service()
    patch_mod_entry()
    print(f"Prepared Cardcha {NEW_VERSION}: MiMi home stability + crisp portrait + direct gate test")


if __name__ == "__main__":
    main()
