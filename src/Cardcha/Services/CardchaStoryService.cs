using System.Collections;
using System.Reflection;
using Cardcha.Models;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Menus;

namespace Cardcha.Services;

internal sealed class CardchaStoryService
{
    private enum SceneKind
    {
        None,
        MimiIntro,
        WizardMeetup
    }

    private enum VisualMode
    {
        None,
        MimiOnBroom,
        MimiMeetup,
        MimiDeparting
    }

    private const string MimiPortraitsPath = "assets/mimi_portraits.png";

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly ProgressionService Progression;
    private readonly ResourceService Resources;
    private readonly ModConfig Config;
    private readonly WorldActorService WorldActors;

    private SceneKind Scene;
    private VisualMode Visual;
    private bool DialogueOpen;
    private string[] Lines = Array.Empty<string>();
    private int DialogueIndex;
    private long IntroNotBefore;
    private bool MeetupHintShownToday;
    private bool IntroArrivalPending;
    private Vector2 SceneAnchor;
    private long SceneVisualStartedAt;
    private Vector2 ChaChaFollowerWorld;
    private Vector2 ChaChaFollowerVelocity;
    private bool ChaChaFollowerInitialized;
    private int ChaChaFollowerDirection = 3;
    private bool MeetupExitPending;
    private Vector2 MeetupExitTarget;

    private Texture2D? MasterPortraitSheet;
    private Texture2D? RuntimePortraitSheet;

    public CardchaStoryService(
        IModHelper helper,
        IMonitor monitor,
        SaveService save,
        ProgressionService progression,
        ResourceService resources,
        ModConfig config,
        WorldActorService worldActors)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.Progression = progression;
        this.Resources = resources;
        this.Config = config;
        this.WorldActors = worldActors;
    }

    public bool OwnsMimiWorldActor
        => this.Scene != SceneKind.None
           || this.Visual != VisualMode.None
           || this.IntroArrivalPending
           || this.MeetupExitPending;

    public void OnSaveLoaded()
    {
        this.ResetRuntime();
        this.IntroNotBefore = Environment.TickCount64 + 900;
        this.EnsureTextures();
    }

    public void OnDayStarted()
    {
        this.ResetRuntime();
        this.MeetupHintShownToday = false;
        this.IntroNotBefore = Environment.TickCount64 + 900;
        this.EnsureTextures();
    }

    public void OnReturnedToTitle()
    {
        this.ResetRuntime();
        this.WorldActors.OnReturnedToTitle();
    }

    public void OnSaving()
        => this.WorldActors.HideChaChaActor();

    public void OnWarped(object? sender, WarpedEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        if (e.NewLocation.NameOrUniqueName.Equals("WizardHouse", StringComparison.OrdinalIgnoreCase))
            TryStartWizardMeetup();
        else if (e.NewLocation == Game1.getFarm())
            TryStartMimiIntro();
    }

    public void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        this.UpdateSceneWorldActors();
        this.UpdateMimiMeetupExit();

        if (this.ShouldDrawLoanedChaCha())
        {
            this.UpdateChaChaFollowerPosition();
            this.SyncChaChaFollowerActor();
        }
        else if (this.Scene == SceneKind.None && !this.MeetupExitPending)
        {
            this.ChaChaFollowerInitialized = false;
            this.WorldActors.HideChaChaActor();
        }

        if (this.IntroArrivalPending)
        {
            Game1.player.Halt();
            if (Environment.TickCount64 - this.SceneVisualStartedAt >= 1700)
                this.BeginMimiIntroDialogue();
            return;
        }

        if (this.DialogueOpen)
            return;

        if (!e.IsMultipleOf(15))
            return;

        if (Game1.currentLocation == Game1.getFarm())
            TryStartMimiIntro();

        if (Game1.currentLocation?.NameOrUniqueName.Equals(
                "WizardHouse",
                StringComparison.OrdinalIgnoreCase) == true)
        {
            TryStartWizardMeetup();
        }
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        // World bodies are no longer drawn here. Only ChaCha's cosmetic sparkle trail remains
        // a post-world effect; MiMi and ChaCha themselves are native GameLocation actors.
        if (!Context.IsWorldReady || !this.ShouldDrawLoanedChaCha() || !this.ChaChaFollowerInitialized)
            return;

        float speed = this.ChaChaFollowerVelocity.Length();
        if (speed > 12f)
            DrawChaChaSparkles(e.SpriteBatch, this.ChaChaFollowerWorld, speed);
    }

    public string Describe()
        => $"Scene={this.Scene} | Visual={this.Visual} | Dialogue={this.DialogueOpen} | " +
           $"FirstScrap={this.Save.Data.FirstScrapTriggered} | " +
           $"FirstScrapDay={this.Save.Data.FirstScrapDay} | Today={Game1.Date.TotalDays} | " +
           $"IntroArrivalPending={this.IntroArrivalPending} | " +
           $"MiMiIntro={this.Save.Data.MimiIntroSeen} | " +
           $"MeetupPending={this.Save.Data.MimiMeetupPending} | " +
           $"MeetupDone={this.Save.Data.MimiMeetupCompleted} | " +
           $"ChaChaLoaned={this.Save.Data.ChaChaLoaned} | " +
           $"FirstPullQuest={this.Save.Data.FirstPullQuestActive} | " +
           $"FirstPullDone={this.Save.Data.FirstPullCompleted} | " +
           $"Chapter1Done={this.Save.Data.Chapter1Completed} | " +
           $"Time={Game1.timeOfDay} | Location={Game1.currentLocation?.NameOrUniqueName ?? "<none>"}";

    private void TryStartMimiIntro()
    {
        if (this.Scene != SceneKind.None || this.DialogueOpen)
            return;

        if (!this.Progression.ShouldStartMimiIntro())
            return;

        if (Environment.TickCount64 < this.IntroNotBefore)
            return;

        if (Game1.currentLocation != Game1.getFarm())
            return;

        if (Game1.activeClickableMenu is not null
            || Game1.eventUp
            || Game1.dialogueUp)
        {
            return;
        }

        this.Scene = SceneKind.MimiIntro;
        this.Visual = VisualMode.MimiOnBroom;
        this.SceneAnchor = Game1.player.Position + new Vector2(-136f, -88f);
        this.SceneVisualStartedAt = Environment.TickCount64;
        this.Lines = Array.Empty<string>();
        this.DialogueIndex = 0;
        this.DialogueOpen = false;
        this.IntroArrivalPending = true;

        // The player sees MiMi physically fly in first. Dialogue begins only after
        // the broom landing animation completes.
        Game1.playSound("wand");
        Game1.player.Halt();

        this.Monitor.Log(
            "Cardcha Chapter 1: NEXT-DAY MiMi farm broom arrival started; dialogue waits for landing.",
            LogLevel.Info
        );
    }

    private void BeginMimiIntroDialogue()
    {
        if (!this.IntroArrivalPending || this.Scene != SceneKind.MimiIntro)
            return;

        this.IntroArrivalPending = false;
        this.Lines = new[]
        {
            ModEntry.T("story.mimi.intro.0"),
            ModEntry.T("story.mimi.intro.1"),
            ModEntry.T("story.mimi.intro.2"),
            ModEntry.T("story.mimi.intro.3"),
            ModEntry.T("story.mimi.intro.4")
        };
        this.DialogueIndex = 0;
        this.DialogueOpen = true;
        Game1.playSound("smallSelect");
        this.Helper.Events.Display.MenuChanged += this.OnMenuChanged;
        this.ShowCurrentLine();
    }

    private void TryStartWizardMeetup()
    {
        if (this.Scene != SceneKind.None || this.DialogueOpen)
            return;

        if (!this.Progression.ShouldStartMimiMeetup())
            return;

        if (Game1.currentLocation?.NameOrUniqueName.Equals(
                "WizardHouse",
                StringComparison.OrdinalIgnoreCase) != true)
        {
            return;
        }

        if (Game1.timeOfDay < 1300 || Game1.timeOfDay > 1700)
        {
            if (!this.MeetupHintShownToday
                && Game1.timeOfDay >= 1000
                && Game1.timeOfDay < 1300)
            {
                this.MeetupHintShownToday = true;
                Game1.addHUDMessage(
                    new HUDMessage(
                        ModEntry.T("story.mimi.meetup-too-early"),
                        HUDMessage.newQuest_type
                    )
                );
            }

            return;
        }

        if (Game1.activeClickableMenu is not null
            || Game1.eventUp
            || Game1.dialogueUp)
        {
            return;
        }

        this.Scene = SceneKind.WizardMeetup;
        this.Visual = VisualMode.MimiMeetup;
        this.SceneAnchor = Game1.player.Position + new Vector2(92f, -12f);
        this.SceneVisualStartedAt = Environment.TickCount64;
        this.Lines = new[]
        {
            ModEntry.T("story.meetup.1"),
            ModEntry.T("story.meetup.2"),
            ModEntry.T("story.meetup.3"),
            ModEntry.T("story.meetup.4"),
            ModEntry.T("story.meetup.5"),
            ModEntry.T("story.meetup.6"),
            ModEntry.T("story.meetup.7"),
            ModEntry.T("story.meetup.8")
        };
        this.DialogueIndex = 0;
        this.DialogueOpen = true;

        PlayMagicArrival(Game1.currentLocation, this.SceneAnchor + new Vector2(24f, 48f));
        Game1.player.Halt();

        this.Helper.Events.Display.MenuChanged += this.OnMenuChanged;
        this.ShowCurrentLine();

        this.Monitor.Log(
            "Cardcha Chapter 1: MiMi + Wizard forest meetup started with in-world visuals.",
            LogLevel.Info
        );
    }

    private void OnMenuChanged(object? sender, MenuChangedEventArgs e)
    {
        if (!this.DialogueOpen)
            return;

        if (e.OldMenu is null || e.NewMenu is not null)
            return;

        this.DialogueIndex++;

        if (this.DialogueIndex < this.Lines.Length)
        {
            this.ShowCurrentLine();
            return;
        }

        this.Helper.Events.Display.MenuChanged -= this.OnMenuChanged;
        this.DialogueOpen = false;
        this.Lines = Array.Empty<string>();
        this.DialogueIndex = 0;

        SceneKind finished = this.Scene;
        this.Scene = SceneKind.None;
        this.Visual = VisualMode.None;

        if (finished == SceneKind.MimiIntro)
            FinishMimiIntro();
        else if (finished == SceneKind.WizardMeetup)
            FinishWizardMeetup();
    }

    private void ShowCurrentLine()
    {
        if (!this.DialogueOpen
            || this.DialogueIndex < 0
            || this.DialogueIndex >= this.Lines.Length)
        {
            return;
        }

        this.ShowStoryDialogue(this.Lines[this.DialogueIndex]);
    }

    private void FinishMimiIntro()
    {
        this.Progression.CompleteMimiIntro();

        Game1.playSound("smallSelect");
        Game1.addHUDMessage(
            new HUDMessage(
                ModEntry.T("story.mimi.quest-added"),
                HUDMessage.newQuest_type
            )
        );
    }

    private void FinishWizardMeetup()
    {
        this.Progression.CompleteWizardMeetup();
        int starterScraps = this.GrantStarterScrapForFirstPull();
        this.Save.Save();

        Game1.playSound("questcomplete");
        PlayMagicArrival(
            Game1.currentLocation,
            Game1.player.Position + new Vector2(64f, 0f)
        );

        Game1.addHUDMessage(
            new HUDMessage(
                ModEntry.T("story.machine-unlocked"),
                HUDMessage.newQuest_type
            )
        );

        Game1.showGlobalMessage(
            ModEntry.T(
                "story.first-pull.objective",
                new { amount = starterScraps }
            )
        );

        this.StartMimiMeetupExit();
    }

    public void OnPullResolved(PullType type, int count)
    {
        if (!this.Progression.OnPullResolved(type, count))
            return;

        Game1.playSound("questcomplete");
        Game1.addHUDMessage(
            new HUDMessage(
                ModEntry.T("story.first-pull.complete"),
                HUDMessage.newQuest_type
            )
        );

        Game1.showGlobalMessage(ModEntry.T("story.chapter1.complete"));
    }

    private int GrantStarterScrapForFirstPull()
    {
        int target = Math.Max(1, this.Config.StandardPullCost);
        int current = this.Resources.Count(DropService.CardboardScrapId);
        int missing = Math.Max(0, target - current);

        if (missing <= 0)
            return 0;

        this.Resources.Add(DropService.CardboardScrapId, missing);

        this.Monitor.Log(
            $"Wizard supplied {missing} starter Cardboard Scrap so the first Standard Pull tutorial is immediately playable.",
            LogLevel.Info
        );

        return missing;
    }


    private void ShowStoryDialogue(string rawLine)
    {
        if (string.IsNullOrWhiteSpace(rawLine))
            return;

        string speakerKey = "MiMi";
        string text = rawLine.Trim();
        int colon = rawLine.IndexOf(':');
        if (colon >= 0)
        {
            speakerKey = rawLine[..colon].Trim();
            if (colon + 1 < rawLine.Length)
                text = rawLine[(colon + 1)..].Trim();
        }

        NPC? speaker = this.ResolveDialogueSpeaker(speakerKey);
        string portraitCommand = this.GetStoryPortraitCommand(speakerKey);
        if (speaker is not null && TryShowDialogueWithPortrait(speaker, text + portraitCommand))
            return;

        Game1.drawObjectDialogue(rawLine);
    }

    private string GetStoryPortraitCommand(string speakerKey)
    {
        if (speakerKey.Contains("Pháp", StringComparison.OrdinalIgnoreCase)
            || speakerKey.Contains("Wizard", StringComparison.OrdinalIgnoreCase))
        {
            return string.Empty;
        }

        return this.Scene switch
        {
            SceneKind.MimiIntro => this.DialogueIndex switch
            {
                0 => "$1",
                1 => "$3",
                2 => "$1",
                3 => "$2",
                4 => "$3",
                _ => "$0"
            },
            SceneKind.WizardMeetup => this.DialogueIndex switch
            {
                0 => "$1",
                2 => "$3",
                6 => "$5",
                7 => "$4",
                _ => "$0"
            },
            _ => "$0"
        };
    }

    private NPC? ResolveDialogueSpeaker(string speakerKey)
    {
        string normalized = speakerKey.Trim();
        if (normalized.Contains("Pháp", StringComparison.OrdinalIgnoreCase)
            || normalized.Contains("Wizard", StringComparison.OrdinalIgnoreCase))
        {
            return Game1.getCharacterFromName("Wizard");
        }

        NPC? mimi = FindMimiNpc();
        if (mimi is not null)
        {
            SetNpcDisplayName(mimi, normalized == "???" ? "???" : "MiMi");
            return mimi;
        }

        return Game1.getCharacterFromName("Wizard");
    }

    private bool TryShowDialogueWithPortrait(NPC speaker, string text)
    {
        try
        {
            this.EnsureTextures();
            bool isMimi = string.Equals(
                speaker.Name,
                MimiMysteryTownService.NpcId,
                StringComparison.OrdinalIgnoreCase
            );

            if (isMimi)
                AssignPortraitTexture(speaker, this.RuntimePortraitSheet);

            Dialogue dialogue = new Dialogue(speaker, "Mods/Ronvotri.Cardcha:RuntimeDialogue", text)
            {
                showPortrait = true
            };

            if (isMimi)
                dialogue.overridePortrait = this.RuntimePortraitSheet;

            Game1.activeClickableMenu = new DialogueBox(dialogue);
            return true;
        }
        catch (Exception ex)
        {
            this.Monitor.Log($"Cardcha story portrait dialogue failed for {speaker.Name}: {ex}", LogLevel.Error);
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

    private NPC? FindMimiNpc()
        => this.WorldActors.FindMimiActor();

    private void ResetRuntime()
    {
        if (this.DialogueOpen)
            this.Helper.Events.Display.MenuChanged -= this.OnMenuChanged;

        this.Scene = SceneKind.None;
        this.Visual = VisualMode.None;
        this.DialogueOpen = false;
        this.Lines = Array.Empty<string>();
        this.DialogueIndex = 0;
        this.IntroArrivalPending = false;
        this.IntroNotBefore = 0;
        this.SceneAnchor = Vector2.Zero;
        this.SceneVisualStartedAt = 0;
        this.ChaChaFollowerWorld = Vector2.Zero;
        this.ChaChaFollowerVelocity = Vector2.Zero;
        this.ChaChaFollowerInitialized = false;
        this.ChaChaFollowerDirection = 3;
        this.MeetupExitPending = false;
        this.MeetupExitTarget = Vector2.Zero;
        this.WorldActors.HideChaChaActor();
    }

    private void EnsureTextures()
    {
        this.MasterPortraitSheet ??= this.Helper.ModContent.Load<Texture2D>(MimiPortraitsPath);
        this.RuntimePortraitSheet ??= CreateRuntimePortraitSheet(this.MasterPortraitSheet);
    }

    private bool ShouldDrawLoanedChaCha()
        => this.Save.Data.ChaChaLoaned
           && this.Scene == SceneKind.None
           && !Game1.eventUp;

    private void UpdateChaChaFollowerPosition()
    {
        GameLocation? location = Game1.currentLocation;
        if (location is null)
            return;

        // Stardew-fairy style movement: ChaCha follows a slowly drifting target instead of
        // hovering at one fixed point like a helicopter. The drift is intentionally small so
        // the familiar still feels attached to the player while gently gliding around them.
        double seconds = Game1.currentGameTime.TotalGameTime.TotalSeconds;
        Vector2 offset = Game1.player.FacingDirection switch
        {
            0 => new Vector2(-42f, 34f),
            1 => new Vector2(-54f, -6f),
            2 => new Vector2(54f, -18f),
            3 => new Vector2(54f, -6f),
            _ => new Vector2(54f, -18f)
        };
        Vector2 fairyDrift = new(
            (float)Math.Sin(seconds * 1.15) * 7f,
            (float)Math.Sin(seconds * 1.73 + 0.8) * 5f
        );
        Vector2 desired = Game1.player.Position + offset + fairyDrift;
        Vector2 target = this.ResolveSafeChaChaFollowerTarget(desired);

        if (!this.ChaChaFollowerInitialized
            || Vector2.DistanceSquared(this.ChaChaFollowerWorld, target) > 300f * 300f
            || !this.IsChaChaWorldSafe(location, this.ChaChaFollowerWorld, allowNearPlayer: true))
        {
            this.ChaChaFollowerWorld = target;
            this.ChaChaFollowerVelocity = Vector2.Zero;
            this.ChaChaFollowerInitialized = true;
            return;
        }

        float dt = Math.Clamp((float)Game1.currentGameTime.ElapsedGameTime.TotalSeconds, 1f / 120f, 1f / 20f);
        Vector2 toTarget = target - this.ChaChaFollowerWorld;

        // Critically damped-ish flight spring in pixels/second. This gives ChaCha a soft
        // curved catch-up motion, with a little inertia but without rubber-band overshoot.
        this.ChaChaFollowerVelocity += toTarget * (7.5f * dt);
        this.ChaChaFollowerVelocity *= Math.Max(0f, 1f - 4.8f * dt);

        float maxSpeed = 210f;
        float speed = this.ChaChaFollowerVelocity.Length();
        if (speed > maxSpeed)
            this.ChaChaFollowerVelocity *= maxSpeed / speed;

        if (toTarget.LengthSquared() < 6f * 6f)
            this.ChaChaFollowerVelocity *= Math.Max(0f, 1f - 7.0f * dt);

        Vector2 step = this.ChaChaFollowerVelocity * dt;
        Vector2 candidate = this.ChaChaFollowerWorld + step;

        if (!this.IsChaChaWorldSafe(location, candidate, allowNearPlayer: true))
        {
            // Slide around obstacles instead of phasing through trees, bushes, NPCs, or the player.
            Vector2 slideX = this.ChaChaFollowerWorld + new Vector2(step.X, 0f);
            Vector2 slideY = this.ChaChaFollowerWorld + new Vector2(0f, step.Y);
            if (this.IsChaChaWorldSafe(location, slideX, allowNearPlayer: true))
            {
                candidate = slideX;
                this.ChaChaFollowerVelocity.Y *= 0.25f;
            }
            else if (this.IsChaChaWorldSafe(location, slideY, allowNearPlayer: true))
            {
                candidate = slideY;
                this.ChaChaFollowerVelocity.X *= 0.25f;
            }
            else
            {
                candidate = this.ChaChaFollowerWorld;
                this.ChaChaFollowerVelocity *= 0.25f;
            }
        }

        this.ChaChaFollowerWorld = candidate;

        Vector2 movement = this.ChaChaFollowerVelocity;
        if (movement.LengthSquared() >= 16f)
        {
            if (Math.Abs(movement.X) >= Math.Abs(movement.Y))
                this.ChaChaFollowerDirection = movement.X >= 0f ? 3 : 1;
            else
                this.ChaChaFollowerDirection = movement.Y >= 0f ? 0 : 2;
        }
    }

    private void UpdateSceneWorldActors()
    {
        if (!Context.IsWorldReady)
            return;

        bool broom = this.Visual == VisualMode.MimiOnBroom
            && Game1.currentLocation == Game1.getFarm();
        bool meetup = this.Visual == VisualMode.MimiMeetup
            && Game1.currentLocation?.NameOrUniqueName.Equals(
                "WizardHouse",
                StringComparison.OrdinalIgnoreCase
            ) == true;

        if (!broom && !meetup)
            return;

        GameLocation location = Game1.currentLocation;
        NPC? mimi = this.WorldActors.EnsureMimiActor();
        if (mimi is null)
            return;

        double time = Game1.currentGameTime.TotalGameTime.TotalMilliseconds / 1000.0;
        float sceneAge = this.SceneVisualStartedAt <= 0
            ? 1f
            : Math.Clamp((Environment.TickCount64 - this.SceneVisualStartedAt) / 1000f, 0f, 1f);

        Vector2 mimiWorld = this.SceneAnchor;
        int mimiFacing;
        int mimiFrame;

        if (broom)
        {
            float arrive = sceneAge * sceneAge * (3f - 2f * sceneAge);
            mimiWorld += new Vector2(MathHelper.Lerp(-230f, 0f, arrive), 0f);
            mimiFacing = 1;
            mimiFrame = (int)(Game1.currentGameTime.TotalGameTime.TotalMilliseconds / 135.0) % 4;
            this.WorldActors.MoveMimiActor(mimi, location, mimiWorld, mimiFacing, broom: true, visible: true);
            this.WorldActors.SetMimiFrame(mimi, mimiFacing, mimiFrame);
            mimi.rotation = (1f - arrive) * -0.075f + (float)Math.Sin(time * 2.8) * 0.010f;
        }
        else
        {
            Vector2 toPlayer = Game1.player.Position - this.SceneAnchor;
            mimiFacing = Math.Abs(toPlayer.X) >= Math.Abs(toPlayer.Y)
                ? (toPlayer.X >= 0f ? 1 : 3)
                : (toPlayer.Y >= 0f ? 2 : 0);

            float walkIn = Math.Clamp(sceneAge / 0.72f, 0f, 1f);
            float eased = walkIn * walkIn * (3f - 2f * walkIn);
            float entryX = mimiFacing == 3 ? -44f : 44f;
            mimiWorld += new Vector2(MathHelper.Lerp(entryX, 0f, eased), 0f);
            mimiFrame = walkIn < 1f
                ? (int)(Game1.currentGameTime.TotalGameTime.TotalMilliseconds / 125.0) % 4
                : 0;

            this.WorldActors.MoveMimiActor(mimi, location, mimiWorld, mimiFacing, broom: false, visible: true);
            this.WorldActors.SetMimiFrame(mimi, mimiFacing, mimiFrame);
            mimi.rotation = 0f;
        }

        Vector2 chachaWorld = broom
            ? mimiWorld + new Vector2(92f, 0f)
            : mimiWorld + new Vector2(-76f, 8f);
        int chachaRow = broom ? 0 : 1;
        int chachaFrame = (int)(Game1.currentGameTime.TotalGameTime.TotalMilliseconds / 160.0) % 4;
        NPC? chacha = this.WorldActors.EnsureChaChaActor(
            location,
            chachaWorld,
            chachaRow,
            chachaFrame,
            machine: true
        );
        if (chacha is not null)
        {
            chacha.drawOffset = new Vector2(0f, (float)Math.Sin(time * 3.0) * 1.5f - 3f);
            chacha.shouldShadowBeOffset = false;
            chacha.rotation = 0f;
        }
    }

    private void SyncChaChaFollowerActor()
    {
        if (!this.ChaChaFollowerInitialized || Game1.currentLocation is null)
            return;

        float speed = this.ChaChaFollowerVelocity.Length();
        int frameMs = speed > 120f ? 90 : speed > 35f ? 125 : 175;
        int frame = (int)(Game1.currentGameTime.TotalGameTime.TotalMilliseconds / frameMs) % 4;
        NPC? chacha = this.WorldActors.EnsureChaChaActor(
            Game1.currentLocation,
            this.ChaChaFollowerWorld,
            this.ChaChaFollowerDirection,
            frame,
            machine: false
        );

        if (chacha is not null)
        {
            double seconds = Game1.currentGameTime.TotalGameTime.TotalSeconds;
            chacha.drawOffset = new Vector2(
                (float)Math.Sin(seconds * 2.2 + 0.4) * 1.8f,
                (float)Math.Sin(seconds * 3.6) * 2.5f - 5f
            );
            chacha.shouldShadowBeOffset = false;
            chacha.rotation = Math.Clamp(this.ChaChaFollowerVelocity.X * 0.00045f, -0.055f, 0.055f);
        }
    }

    private Vector2 ResolveSafeChaChaFollowerTarget(Vector2 desired)
    {
        GameLocation? location = Game1.currentLocation;
        if (location is null)
            return desired;

        if (this.IsChaChaWorldSafe(location, desired, allowNearPlayer: true))
            return desired;

        Vector2 player = Game1.player.Position;
        Vector2[] alternatives =
        {
            player + new Vector2(54f, -10f),
            player + new Vector2(-54f, -10f),
            player + new Vector2(44f, 38f),
            player + new Vector2(-44f, 38f),
            player + new Vector2(46f, -42f),
            player + new Vector2(-46f, -42f),
            player + new Vector2(0f, 56f),
            player + new Vector2(0f, -58f)
        };

        foreach (Vector2 candidate in alternatives)
        {
            if (this.IsChaChaWorldSafe(location, candidate, allowNearPlayer: true))
                return candidate;
        }

        // Crowded maps/modded towns can invalidate the usual follower slots. Search a wider
        // ring before giving up so ChaCha doesn't initialize inside a tree or decorative prop.
        foreach (float radius in new[] { 76f, 96f, 118f })
        {
            for (int i = 0; i < 8; i++)
            {
                float angle = MathHelper.TwoPi * i / 8f;
                Vector2 candidate = player + new Vector2((float)Math.Cos(angle), (float)Math.Sin(angle)) * radius;
                if (this.IsChaChaWorldSafe(location, candidate, allowNearPlayer: true))
                    return candidate;
            }
        }

        if (this.ChaChaFollowerWorld != Vector2.Zero
            && this.IsChaChaWorldSafe(location, this.ChaChaFollowerWorld, allowNearPlayer: true))
        {
            return this.ChaChaFollowerWorld;
        }

        return desired;
    }

    private bool IsChaChaWorldSafe(GameLocation location, Vector2 world, bool allowNearPlayer)
    {
        if (!IsChaChaFootprintClear(location, world))
            return false;

        Vector2 center = world + new Vector2(16f, 20f);
        Vector2 playerCenter = Game1.player.Position + new Vector2(32f, 42f);
        float minPlayerDistance = allowNearPlayer ? 44f : 58f;
        if (Game1.player.currentLocation == location
            && Vector2.DistanceSquared(center, playerCenter) < minPlayerDistance * minPlayerDistance)
        {
            return false;
        }

        foreach (NPC npc in location.characters)
        {
            if (npc is null
                || npc.isInvisible.Value
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
                // If another map/mod exposes unusual bounds, don't hard-crash the follower.
            }
        }

        return true;
    }

    private static void DrawChaChaSparkles(SpriteBatch b, Vector2 world, float speed)
    {
        double ms = Game1.currentGameTime.TotalGameTime.TotalMilliseconds;
        float strength = Math.Clamp(speed / 120f, 0.25f, 1f);
        Color[] colors = { Color.White, new Color(255, 225, 120), new Color(220, 180, 255) };
        for (int i = 0; i < 5; i++)
        {
            float phase = (float)(ms * 0.0045 + i * 1.37);
            float radius = 22f + i * 3.5f;
            Vector2 sparkleWorld = world + new Vector2(16f, 14f) + new Vector2(
                (float)Math.Cos(phase) * radius,
                (float)Math.Sin(phase * 1.21f) * (10f + i * 2f)
            );
            Vector2 pos = Game1.GlobalToLocal(Game1.viewport, sparkleWorld);
            float pulse = 0.45f + 0.55f * (float)Math.Abs(Math.Sin(phase * 1.8f));
            Color c = colors[i % colors.Length] * (0.28f + 0.42f * pulse * strength);
            int s = pulse > 0.76f ? 3 : 2;
            b.Draw(Game1.staminaRect, new Rectangle((int)pos.X - s, (int)pos.Y, s * 2 + 1, 1), c);
            b.Draw(Game1.staminaRect, new Rectangle((int)pos.X, (int)pos.Y - s, 1, s * 2 + 1), c);
        }
    }

    private void StartMimiMeetupExit()
    {
        if (Game1.currentLocation?.NameOrUniqueName.Equals("WizardHouse", StringComparison.OrdinalIgnoreCase) != true)
            return;

        this.MeetupExitPending = true;
        this.Visual = VisualMode.MimiDeparting;
        this.SceneVisualStartedAt = Environment.TickCount64;
        this.MeetupExitTarget = FindNearestExitWorld(Game1.currentLocation, this.SceneAnchor);
    }

    private void UpdateMimiMeetupExit()
    {
        if (!this.MeetupExitPending)
            return;

        GameLocation? location = Game1.currentLocation;
        NPC? mimi = this.WorldActors.EnsureMimiActor();
        if (location is null
            || mimi is null
            || !location.NameOrUniqueName.Equals("WizardHouse", StringComparison.OrdinalIgnoreCase))
        {
            return;
        }

        float raw = Math.Clamp((Environment.TickCount64 - this.SceneVisualStartedAt) / 1900f, 0f, 1f);
        float eased = raw * raw * (3f - 2f * raw);
        Vector2 target = this.MeetupExitTarget == Vector2.Zero
            ? this.SceneAnchor + new Vector2(0f, 150f)
            : this.MeetupExitTarget;
        Vector2 world = Vector2.Lerp(this.SceneAnchor, target, eased);
        Vector2 delta = target - this.SceneAnchor;
        int facing = Math.Abs(delta.X) >= Math.Abs(delta.Y)
            ? (delta.X >= 0f ? 1 : 3)
            : (delta.Y >= 0f ? 2 : 0);
        int frame = (int)(Game1.currentGameTime.TotalGameTime.TotalMilliseconds / 125.0) % 4;

        this.WorldActors.MoveMimiActor(mimi, location, world, facing, broom: false, visible: true);
        this.WorldActors.SetMimiFrame(mimi, facing, frame);
        mimi.rotation = 0f;

        if (raw < 1f)
            return;

        this.MeetupExitPending = false;
        this.Visual = VisualMode.None;
        this.MeetupExitTarget = Vector2.Zero;
        mimi.isInvisible.Value = true;
    }

    private static Vector2 FindNearestExitWorld(GameLocation location, Vector2 fallbackFrom)
    {
        try
        {
            const BindingFlags flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.IgnoreCase;
            object? warps = location.GetType().GetProperty("warps", flags)?.GetValue(location)
                ?? location.GetType().GetField("warps", flags)?.GetValue(location);

            if (warps is IEnumerable enumerable)
            {
                Vector2? best = null;
                float bestDistance = float.MaxValue;

                foreach (object? warp in enumerable)
                {
                    if (warp is null)
                        continue;

                    int? x = ReadIntMember(warp, "X");
                    int? y = ReadIntMember(warp, "Y");
                    if (!x.HasValue || !y.HasValue)
                        continue;

                    Vector2 world = new(x.Value * 64f, y.Value * 64f);
                    float distance = Vector2.DistanceSquared(world, fallbackFrom);
                    if (distance < bestDistance)
                    {
                        bestDistance = distance;
                        best = world;
                    }
                }

                if (best.HasValue)
                    return best.Value;
            }
        }
        catch
        {
            // Cosmetic exit only; fall back to walking downward if another mod changes warp internals.
        }

        return fallbackFrom + new Vector2(0f, 150f);
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

    private static void PlayMagicArrival(GameLocation location, Vector2 position)
    {
        Game1.playSound("wand");

        Vector2[] offsets =
        {
            new(-22f, -34f),
            new(18f, -24f),
            new(-30f, 4f),
            new(24f, 8f),
            new(-12f, 30f),
            new(18f, 34f)
        };

        for (int i = 0; i < offsets.Length; i++)
        {
            TemporaryAnimatedSprite sparkle = new(
                10,
                position + offsets[i],
                i % 2 == 0
                    ? new Color(222, 133, 255)
                    : new Color(126, 105, 255),
                8,
                i % 2 == 1,
                55f
            )
            {
                scale = 0.70f + i * 0.05f,
                scaleChange = 0.022f,
                alphaFade = 0.016f,
                delayBeforeAnimationStart = i * 32,
                layerDepth = Math.Max(
                    0f,
                    (position.Y + 128f + i) / 10000f
                )
            };

            location.temporarySprites.Add(sparkle);
        }
    }
}
