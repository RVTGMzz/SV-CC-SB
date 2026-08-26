from __future__ import annotations
from pathlib import Path
import hashlib, json, shutil, struct

ROOT = Path('src/Cardcha')
ASSETS = Path('tools/beta3_assets')
EXPECTED_ATLAS_SHA256 = '3769e1c61098f8dbca483819f4c79cc8db56d2c36edd84191b646d303b5507c5'
EXPECTED_ATLAS_SIZE = (320, 1024)

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'beta.3 patch expected exactly one {label}; found {count}')
    return text.replace(old, new, 1)

# --- WorldActorService: split one canonical actor into two phase-specific actor IDs. ---
world_path = ROOT / 'Services/WorldActorService.cs'
world = world_path.read_text(encoding='utf-8')
start = world.index('    public const string MimiNpcId')
end = world.index('    public NPC? EnsureChaChaActor')
world_block = r'''    public const string MimiNpcId = MimiMysteryTownService.NpcId;
    public const string MysteryMimiNpcId = MimiMysteryTownService.MysteryNpcId;
    public const string MimiCharacterAsset = "Characters/Ronvotri.Cardcha_MiMi";
    public const string MysteryMimiCharacterAsset = "Characters/Ronvotri.Cardcha_MiMi_Mystery";
    public const string MimiBroomCharacterAsset = "Characters/Ronvotri.Cardcha_MiMi_Broom";
    public const string ChaChaNpcId = "Ronvotri.Cardcha_ChaCha";
    public const string ChaChaCharacterAsset = "Characters/Ronvotri.Cardcha_ChaCha";
    public const string ChaChaMachineCharacterAsset = "Characters/Ronvotri.Cardcha_ChaCha_Machine";

    private const string MimiBroomSheetPath = "assets/mimi_broom.png";
    private const string ChaChaFollowSheetPath = "assets/chacha_follow.png";
    private const string ChaChaMachineSheetPath = "assets/chacha_machine.png";

    private const float MimiNativeScale = 0.575f;
    private const float ChaChaNativeScale = 0.45f;

    private readonly IMonitor Monitor;
    private NPC? ChaChaActor;

    public WorldActorService(IMonitor monitor)
    {
        this.Monitor = monitor;
    }

    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)
    {
        if (e.Name.IsEquivalentTo(MimiBroomCharacterAsset))
        {
            e.LoadFromModFile<Texture2D>(MimiBroomSheetPath, AssetLoadPriority.Medium);
            return;
        }
        if (e.Name.IsEquivalentTo(ChaChaCharacterAsset))
        {
            e.LoadFromModFile<Texture2D>(ChaChaFollowSheetPath, AssetLoadPriority.Medium);
            return;
        }
        if (e.Name.IsEquivalentTo(ChaChaMachineCharacterAsset))
            e.LoadFromModFile<Texture2D>(ChaChaMachineSheetPath, AssetLoadPriority.Medium);
    }

    public NPC? FindMimiActor() => this.FindUniqueMimiActor(MimiNpcId);
    public NPC? FindMysteryMimiActor() => this.FindUniqueMimiActor(MysteryMimiNpcId);

    private NPC? FindUniqueMimiActor(string actorId)
    {
        if (!Context.IsWorldReady)
            return null;
        NPC? found = null;
        foreach (GameLocation location in Game1.locations)
        {
            foreach (NPC npc in location.characters.Where(p => string.Equals(p.Name, actorId, StringComparison.OrdinalIgnoreCase)).ToList())
            {
                if (found is null)
                    found = npc;
                else
                    location.characters.Remove(npc);
            }
        }
        return found;
    }

    public NPC? EnsureMimiActor() => this.EnsureMimiActor(MimiNpcId, MimiCharacterAsset, "MiMi");
    public NPC? EnsureMysteryMimiActor() => this.EnsureMimiActor(MysteryMimiNpcId, MysteryMimiCharacterAsset, "???");

    private NPC? EnsureMimiActor(string actorId, string characterAsset, string displayName)
    {
        NPC? existing = this.FindUniqueMimiActor(actorId);
        if (existing is not null)
        {
            existing.displayName = displayName;
            return existing;
        }
        if (!Context.IsWorldReady)
            return null;
        GameLocation? wizardHouse = Game1.getLocationFromName("WizardHouse");
        if (wizardHouse is null)
            return null;
        try
        {
            NPC created = new(new AnimatedSprite(characterAsset, 0, 32, 48), new Vector2(-6400f, -6400f), 2, actorId);
            created.displayName = displayName;
            created.currentLocation = wizardHouse;
            wizardHouse.characters.Add(created);
            this.ConfigureMimiActor(created, broom: false, visible: false);
            return created;
        }
        catch (Exception ex)
        {
            this.Monitor.Log($"Couldn't create MiMi actor {actorId}: {ex}", LogLevel.Error);
            return null;
        }
    }

    public void ReconcileMimiActors(bool revealed)
    {
        if (!Context.IsWorldReady)
            return;
        if (revealed)
        {
            this.RemoveMysteryMimiActor();
            this.EnsureMimiActor();
        }
        else
        {
            this.RemoveMimiActor();
            this.EnsureMysteryMimiActor();
        }
    }

    public void HideMimiActor() => this.HideMimiActor(MimiNpcId);
    public void HideMysteryMimiActor() => this.HideMimiActor(MysteryMimiNpcId);

    private void HideMimiActor(string actorId)
    {
        if (!Context.IsWorldReady)
            return;
        NPC? actor = this.FindUniqueMimiActor(actorId);
        if (actor is null)
            return;
        GameLocation? wizardHouse = Game1.getLocationFromName("WizardHouse");
        if (wizardHouse is null)
        {
            actor.Halt();
            actor.isInvisible.Value = true;
            return;
        }
        this.MoveMimiActor(actor, wizardHouse, new Vector2(-6400f, -6400f), 2, broom: false, visible: false);
    }

    public void RemoveMimiActor() => this.RemoveMimiActor(MimiNpcId);
    public void RemoveMysteryMimiActor() => this.RemoveMimiActor(MysteryMimiNpcId);

    private void RemoveMimiActor(string actorId)
    {
        if (!Context.IsWorldReady)
            return;
        foreach (GameLocation location in Game1.locations)
        {
            foreach (NPC npc in location.characters.Where(p => string.Equals(p.Name, actorId, StringComparison.OrdinalIgnoreCase)).ToList())
            {
                npc.Halt();
                npc.isInvisible.Value = true;
                location.characters.Remove(npc);
            }
        }
    }

    public void MoveMimiActor(NPC actor, GameLocation target, Vector2 position, int facing, bool broom = false, bool visible = true)
    {
        if (actor.currentLocation != target)
        {
            actor.currentLocation?.characters.Remove(actor);
            if (!target.characters.Contains(actor))
                target.characters.Add(actor);
            actor.currentLocation = target;
        }
        actor.Halt();
        actor.Position = position;
        actor.FacingDirection = facing;
        this.ConfigureMimiActor(actor, broom, visible);
        this.SetMimiFrame(actor, facing, 0);
    }

    public void ConfigureMimiActor(NPC actor, bool broom, bool visible)
    {
        bool mystery = string.Equals(actor.Name, MysteryMimiNpcId, StringComparison.OrdinalIgnoreCase);
        string asset = broom ? MimiBroomCharacterAsset : mystery ? MysteryMimiCharacterAsset : MimiCharacterAsset;
        if (actor.Sprite is null || actor.Sprite.SpriteWidth != 32 || actor.Sprite.SpriteHeight != 48 || !string.Equals(actor.Sprite.loadedTexture, asset, StringComparison.OrdinalIgnoreCase))
            actor.Sprite = new AnimatedSprite(asset, 0, 32, 48);
        actor.displayName = mystery ? "???" : "MiMi";
        actor.Scale = MimiNativeScale;
        actor.forceOneTileWide.Value = true;
        actor.SimpleNonVillagerNPC = broom;
        actor.farmerPassesThrough = broom;
        actor.collidesWithOtherCharacters.Value = !broom;
        actor.willDestroyObjectsUnderfoot = false;
        actor.followSchedule = false;
        actor.ignoreScheduleToday = true;
        actor.drawOnTop = false;
        actor.drawOffset = Vector2.Zero;
        actor.shouldShadowBeOffset = false;
        actor.rotation = 0f;
        actor.breather.Value = false;
        actor.hideShadow.Value = false;
        actor.isInvisible.Value = !visible;
    }

    public void SetMimiFrame(NPC actor, int facing, int stepFrame)
    {
        if (actor.Sprite is null)
            return;
        int row = facing switch { 2 => 0, 1 => 1, 0 => 2, 3 => 3, _ => 0 };
        actor.FacingDirection = facing;
        actor.Sprite.CurrentFrame = row * 4 + Math.Clamp(stepFrame, 0, 3);
    }

'''
world = world[:start] + world_block + world[end:]
world_path.write_text(world, encoding='utf-8')

# --- MimiMysteryTownService: register both CharacterData entries and choose actor by phase. ---
mimi_path = ROOT / 'Services/MimiMysteryTownService.cs'
mimi = mimi_path.read_text(encoding='utf-8')
mimi = replace_once(mimi,
'    public const string NpcId = "Ronvotri.Cardcha_MiMi";\n\n    private const string CharacterAsset = "Characters/Ronvotri.Cardcha_MiMi";\n    private const string PortraitAsset = "Portraits/Ronvotri.Cardcha_MiMi";\n    private const string ScheduleAsset = "Characters/schedules/Ronvotri.Cardcha_MiMi";\n    private const string DialogueAsset = "Characters/Dialogue/Ronvotri.Cardcha_MiMi";\n',
'    public const string NpcId = "Ronvotri.Cardcha_MiMi";\n    public const string MysteryNpcId = "Ronvotri.Cardcha_MiMi_Mystery";\n\n    private const string CharacterAsset = "Characters/Ronvotri.Cardcha_MiMi";\n    private const string MysteryCharacterAsset = "Characters/Ronvotri.Cardcha_MiMi_Mystery";\n    private const string PortraitAsset = "Portraits/Ronvotri.Cardcha_MiMi";\n    private const string MysteryPortraitAsset = "Portraits/Ronvotri.Cardcha_MiMi_Mystery";\n    private const string ScheduleAsset = "Characters/schedules/Ronvotri.Cardcha_MiMi";\n    private const string MysteryScheduleAsset = "Characters/schedules/Ronvotri.Cardcha_MiMi_Mystery";\n    private const string DialogueAsset = "Characters/Dialogue/Ronvotri.Cardcha_MiMi";\n    private const string MysteryDialogueAsset = "Characters/Dialogue/Ronvotri.Cardcha_MiMi_Mystery";\n', 'MiMi asset constants')
mimi = mimi.replace('if (e.Name.IsEquivalentTo(CharacterAsset))', 'if (e.Name.IsEquivalentTo(CharacterAsset) || e.Name.IsEquivalentTo(MysteryCharacterAsset))', 1)
mimi = mimi.replace('if (e.Name.IsEquivalentTo(PortraitAsset))', 'if (e.Name.IsEquivalentTo(PortraitAsset) || e.Name.IsEquivalentTo(MysteryPortraitAsset))', 1)
mimi = mimi.replace('if (e.Name.IsEquivalentTo(ScheduleAsset))', 'if (e.Name.IsEquivalentTo(ScheduleAsset) || e.Name.IsEquivalentTo(MysteryScheduleAsset))', 1)
mimi = mimi.replace('if (e.Name.IsEquivalentTo(DialogueAsset))', 'if (e.Name.IsEquivalentTo(DialogueAsset) || e.Name.IsEquivalentTo(MysteryDialogueAsset))', 1)
char_start = mimi.index('                CharacterData mimi = new();')
char_end_marker = '                data[NpcId] = mimi;\n'
char_end = mimi.index(char_end_marker, char_start) + len(char_end_marker)
mimi = mimi[:char_start] + '''                // Mystery and revealed MiMi use separate runtime actor IDs so phase state cannot leak.\n                data[NpcId] = CreateMimiCharacterData("MiMi", NpcId);\n                data[MysteryNpcId] = CreateMimiCharacterData("???", MysteryNpcId);\n''' + mimi[char_end:]
mimi = mimi.replace('        this.WorldActors.EnsureMimiActor();\n        this.EnforcePhaseState();\n', '        this.WorldActors.ReconcileMimiActors(this.Save.Data.MimiMeetupCompleted);\n        this.EnforcePhaseState();\n', 2)
mimi = replace_once(mimi, '        if (this.IsMerchantRoutineActive())\n        {\n            bool harsh = IsHarshMerchantWeather();\n', '        if (this.IsMerchantRoutineActive())\n        {\n            if (this.StoryOwnsMimiActor())\n                return;\n\n            bool harsh = IsHarshMerchantWeather();\n', 'merchant time guard')
mimi = replace_once(mimi, '        if (this.IsMerchantRoutineActive())\n        {\n            if (this.Flight != FlightState.None && this.MerchantFlight)\n', '        if (this.IsMerchantRoutineActive())\n        {\n            if (this.StoryOwnsMimiActor())\n                return;\n\n            if (this.Flight != FlightState.None && this.MerchantFlight)\n', 'merchant update guard')
mimi = mimi.replace('this.WorldActors.EnsureMimiActor()', 'this.EnsureNativeNpc()')
mimi = replace_once(mimi, '    private void HideNativeOffMap()\n        => this.WorldActors.HideMimiActor();\n', '    private void HideNativeOffMap()\n    {\n        if (this.Save.Data.MimiMeetupCompleted)\n            this.WorldActors.HideMimiActor();\n        else\n            this.WorldActors.HideMysteryMimiActor();\n    }\n', 'phase hide helper')
mimi = replace_once(mimi,
'''    /// <summary>Return Cardcha's one canonical MiMi world actor.</summary>\n    /// <remarks>alpha.11.37 moved actor ownership into WorldActorService, so old call sites\n    /// still use this tiny compatibility helper instead of scanning Game1.locations themselves.</remarks>\n    private NPC? FindNativeNpc()\n        => this.WorldActors.FindMimiActor();\n''',
'''    /// <summary>Return the actor belonging to the current reveal phase.</summary>\n    private NPC? FindNativeNpc()\n        => this.Save.Data.MimiMeetupCompleted\n            ? this.WorldActors.FindMimiActor()\n            : this.WorldActors.FindMysteryMimiActor();\n\n    private NPC? EnsureNativeNpc()\n        => this.Save.Data.MimiMeetupCompleted\n            ? this.WorldActors.EnsureMimiActor()\n            : this.WorldActors.EnsureMysteryMimiActor();\n''', 'phase actor helpers')
mimi = mimi.replace('if (!string.IsNullOrEmpty(bubble) && bubble.Contains(NpcId, StringComparison.OrdinalIgnoreCase))', 'if (!string.IsNullOrEmpty(bubble)\n                    && (bubble.Contains(NpcId, StringComparison.OrdinalIgnoreCase)\n                        || bubble.Contains(MysteryNpcId, StringComparison.OrdinalIgnoreCase)))', 1)
create_data = '''    private static CharacterData CreateMimiCharacterData(string displayName, string textureName)\n    {\n        CharacterData mimi = new();\n        SetProperty(mimi, "DisplayName", displayName);\n        SetProperty(mimi, "TextureName", textureName);\n        SetProperty(mimi, "Gender", "Female");\n        SetProperty(mimi, "Age", "Teen");\n        SetProperty(mimi, "Manner", "Neutral");\n        SetProperty(mimi, "SocialAnxiety", "Outgoing");\n        SetProperty(mimi, "Optimism", "Positive");\n        SetProperty(mimi, "HomeRegion", "Other");\n        SetProperty(mimi, "CanBeRomanced", false);\n        SetProperty(mimi, "CanSocialize", "FALSE");\n        SetProperty(mimi, "CanReceiveGifts", false);\n        SetProperty(mimi, "CanGreetNearbyCharacters", false);\n        SetProperty(mimi, "IntroductionsQuest", false);\n        SetProperty(mimi, "PerfectionScore", false);\n        SetProperty(mimi, "Calendar", "HiddenAlways");\n        SetProperty(mimi, "SocialTab", "HiddenAlways");\n        SetProperty(mimi, "EndSlideShow", "Hidden");\n        SetProperty(mimi, "SpawnIfMissing", false);\n        SetProperty(mimi, "Breather", false);\n        SetProperty(mimi, "ForceOneTileWide", true);\n        SetPointProperty(mimi, "Size", 32, 48);\n        SetRectangleProperty(mimi, "MugShotSourceRect", 0, 0, 16, 24);\n        SetPointProperty(mimi, "EmoteOffset", 0, -24);\n        SetProperty(mimi, "Shadow", new CharacterShadowData { Visible = true, Offset = new Point(0, -2), Scale = 1.44f });\n        SetHome(mimi, "WizardHouse", 4, 6, "down");\n        return mimi;\n    }\n\n'''
mimi = replace_once(mimi, '    private static void SetHome(CharacterData target, string location, int x, int y, string direction)\n', create_data + '    private static void SetHome(CharacterData target, string location, int x, int y, string direction)\n', 'CreateMimiCharacterData insertion')
mimi_path.write_text(mimi, encoding='utf-8')

# --- CardchaStoryService: story always owns mystery actor; revealed actor never reuses it. ---
story_path = ROOT / 'Services/CardchaStoryService.cs'
story = story_path.read_text(encoding='utf-8')
story = story.replace('this.WorldActors.EnsureMimiActor()', 'this.WorldActors.EnsureMysteryMimiActor()')
story = story.replace('this.WorldActors.HideMimiActor()', 'this.WorldActors.HideMysteryMimiActor()')
story = story.replace('        => this.WorldActors.FindMimiActor();\n', '        => this.WorldActors.FindMysteryMimiActor();\n', 1)
story = story.replace('''        NPC? revealedMimi = this.FindMimiNpc();\n        if (revealedMimi is not null)\n            SetNpcDisplayName(revealedMimi, "MiMi");\n\n''', '', 1)
story = story.replace('''        this.Progression.CompleteWizardMeetup();\n        if (mimi is not null)\n            SetNpcDisplayName(mimi, "MiMi");\n\n''', '        this.Progression.CompleteWizardMeetup();\n\n', 1)
story = story.replace('            SetNpcDisplayName(mimi, this.Save.Data.MimiMeetupCompleted ? "MiMi" : "???");\n', '            SetNpcDisplayName(mimi, "???");\n', 1)
story = replace_once(story,
'''            bool isMimi = string.Equals(\n                speaker.Name,\n                MimiMysteryTownService.NpcId,\n                StringComparison.OrdinalIgnoreCase\n            );\n''',
'''            bool isMimi = string.Equals(speaker.Name, MimiMysteryTownService.NpcId, StringComparison.OrdinalIgnoreCase)\n                || string.Equals(speaker.Name, MimiMysteryTownService.MysteryNpcId, StringComparison.OrdinalIgnoreCase);\n''', 'story portrait actor check')
story = story.replace('''        this.WorldActors.HideMysteryMimiActor();\n        this.HideForcedWizardActor();\n        this.WorldActors.HideChaChaActor();\n''', '''        this.WorldActors.RemoveMysteryMimiActor();\n        this.HideForcedWizardActor();\n        this.WorldActors.HideChaChaActor();\n''', 1)
story = replace_once(story,
'''            this.MeetupExitPending = false;\n            this.Visual = VisualMode.None;\n            this.MeetupExitTarget = Vector2.Zero;\n            this.WorldActors.HideMysteryMimiActor();\n            return;\n''',
'''            this.MeetupExitPending = false;\n            this.Visual = VisualMode.None;\n            this.MeetupExitTarget = Vector2.Zero;\n            if (this.Save.Data.MimiMeetupCompleted)\n                this.WorldActors.RemoveMysteryMimiActor();\n            else\n                this.WorldActors.HideMysteryMimiActor();\n            return;\n''', 'meetup warp cleanup')
story = replace_once(story,
'''        this.MeetupExitPending = false;\n        this.Visual = VisualMode.None;\n        this.MeetupExitTarget = Vector2.Zero;\n        this.WorldActors.HideMysteryMimiActor();\n    }\n''',
'''        this.MeetupExitPending = false;\n        this.Visual = VisualMode.None;\n        this.MeetupExitTarget = Vector2.Zero;\n        this.WorldActors.RemoveMysteryMimiActor();\n    }\n''', 'meetup final cleanup')
story_path.write_text(story, encoding='utf-8')

# --- Carry forward beta.2 80-card visuals. ---
atlas_source = ASSETS / 'card_icons.png'
raw = atlas_source.read_bytes()
sha = hashlib.sha256(raw).hexdigest()
if sha != EXPECTED_ATLAS_SHA256:
    raise SystemExit(f'beta.3 atlas sha mismatch: {sha}')
if raw[:8] != b'\x89PNG\r\n\x1a\n' or raw[12:16] != b'IHDR':
    raise SystemExit('beta.3 atlas is not a valid PNG')
width, height = struct.unpack('>II', raw[16:24])
if (width, height) != EXPECTED_ATLAS_SIZE:
    raise SystemExit(f'beta.3 atlas size mismatch: {(width, height)}')
shutil.copy2(atlas_source, ROOT / 'assets/card_icons.png')

cards_path = ROOT / 'assets/cards.json'
cards = json.loads(cards_path.read_text(encoding='utf-8-sig'))
if len(cards) != 80:
    raise SystemExit(f'beta.3 expected 80 cards, got {len(cards)}')
for card in cards:
    base_id = int(card['BaseId'])
    card['IconIndex'] = base_id - 1
    card['UseInitialFallback'] = False
cards_path.write_text(json.dumps(cards, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# Build guards.
combined = world_path.read_text(encoding='utf-8') + mimi_path.read_text(encoding='utf-8') + story_path.read_text(encoding='utf-8')
for marker in ('Ronvotri.Cardcha_MiMi_Mystery', 'ReconcileMimiActors', 'EnsureMysteryMimiActor', 'RemoveMysteryMimiActor'):
    if marker not in combined:
        raise SystemExit(f'beta.3 missing actor marker {marker}')

for rel in ('Cardcha.csproj', 'manifest.json'):
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    if '0.2.0-beta.1' not in text:
        raise SystemExit(f'beta.3 expected beta.1 version marker in {rel}')
    path.write_text(text.replace('0.2.0-beta.1', '0.2.0-beta.3'), encoding='utf-8')

print('beta.3: mystery/real MiMi actor split + 80-card visuals applied')
print('atlas:', width, 'x', height, sha)
