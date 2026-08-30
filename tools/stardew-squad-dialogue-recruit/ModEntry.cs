using System.Reflection;
using HarmonyLib;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Characters;
using StardewValley.Menus;

namespace Ronvotri.StardewSquadDialogueRecruit;

public sealed class ModEntry : Mod
{
    private const string SquadModId = "ThaliaFawnheart.TheStardewSquad";
    private const string SquadAssemblyName = "TheStardewSquad";

    private static ModEntry? Instance;

    private static readonly BindingFlags PublicInstance = BindingFlags.Instance | BindingFlags.Public;
    private static readonly BindingFlags AnyStatic = BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic;

    private NPC? dialogueNpc;
    private Rectangle actionButtonBounds = Rectangle.Empty;
    private NPC? queuedNpc;
    private bool actionQueued;

    private object? squadModEntry;
    private bool bridgeWarned;

    public override void Entry(IModHelper helper)
    {
        Instance = this;

        helper.Events.GameLoop.GameLaunched += this.OnGameLaunched;
        helper.Events.Display.RenderedActiveMenu += this.OnRenderedActiveMenu;
        helper.Events.Input.ButtonPressed += this.OnButtonPressed;
        helper.Events.GameLoop.UpdateTicked += this.OnUpdateTicked;
        helper.Events.GameLoop.ReturnedToTitle += this.OnReturnedToTitle;

        var harmony = new Harmony(this.ModManifest.UniqueID);
        MethodInfo? receiveLeftClick = AccessTools.Method(
            typeof(DialogueBox),
            nameof(DialogueBox.receiveLeftClick),
            new[] { typeof(int), typeof(int), typeof(bool) }
        );

        if (receiveLeftClick is not null)
        {
            harmony.Patch(
                receiveLeftClick,
                prefix: new HarmonyMethod(typeof(ModEntry), nameof(DialogueBoxReceiveLeftClickPrefix))
            );
            this.Monitor.Log("Dialogue touch hook installed.", LogLevel.Trace);
        }
        else
        {
            this.Monitor.Log("DialogueBox.receiveLeftClick(int,int,bool) was not found. Controller shoulder input will still work, but touch input may not.", LogLevel.Warn);
        }
    }

    private void OnGameLaunched(object? sender, GameLaunchedEventArgs e)
    {
        if (!this.Helper.ModRegistry.IsLoaded(SquadModId))
        {
            this.Monitor.Log("The Stardew Squad 0.12.1+ is required.", LogLevel.Error);
            return;
        }

        if (this.EnsureSquadBridge())
            this.Monitor.Log("Connected to The Stardew Squad. Dialogue recruit button is ready.", LogLevel.Info);
    }

    private void OnRenderedActiveMenu(object? sender, RenderedActiveMenuEventArgs e)
    {
        if (!this.TryGetDialogueContext(out DialogueBox? dialogue, out NPC? npc))
        {
            this.dialogueNpc = null;
            this.actionButtonBounds = Rectangle.Empty;
            return;
        }

        this.dialogueNpc = npc;
        bool recruited = this.IsRecruited(npc);
        if (!recruited && !this.IsRecruitEligible(npc))
        {
            this.actionButtonBounds = Rectangle.Empty;
            return;
        }

        this.actionButtonBounds = this.GetActionButtonBounds(dialogue);
        this.DrawActionButton(e.SpriteBatch, this.actionButtonBounds, recruited);
    }

    private void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (this.dialogueNpc is null || this.actionButtonBounds == Rectangle.Empty)
            return;

        // The visible button is always touchable. On a physical controller, either shoulder
        // is accepted so the interaction stays comfortable regardless of the user's layout.
        string buttonName = e.Button.ToString();
        bool shoulder = buttonName.Contains("RightShoulder", StringComparison.OrdinalIgnoreCase)
                     || buttonName.Contains("LeftShoulder", StringComparison.OrdinalIgnoreCase);

        if (!shoulder)
            return;

        this.Helper.Input.Suppress(e.Button);
        this.QueueSquadAction(this.dialogueNpc);
    }

    private void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
    {
        if (!this.actionQueued || this.queuedNpc is null)
            return;

        NPC npc = this.queuedNpc;
        this.actionQueued = false;
        this.queuedNpc = null;

        this.InvokeSquadAction(npc);
    }

    private void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e)
    {
        this.dialogueNpc = null;
        this.queuedNpc = null;
        this.actionQueued = false;
        this.actionButtonBounds = Rectangle.Empty;
        this.squadModEntry = null;
        this.bridgeWarned = false;
    }

    private bool TryGetDialogueContext(out DialogueBox? dialogue, out NPC? npc)
    {
        dialogue = Game1.activeClickableMenu as DialogueBox;
        npc = null;

        if (dialogue is null || !Context.IsWorldReady)
            return false;

        if (Game1.eventUp || Game1.isFestival())
            return false;

        npc = GetCurrentSpeaker();
        if (npc is null || npc.currentLocation != Game1.currentLocation)
            return false;

        return this.EnsureSquadBridge();
    }

    private static NPC? GetCurrentSpeaker()
    {
        FieldInfo? field = typeof(Game1).GetField("currentSpeaker", AnyStatic);
        if (field?.GetValue(null) is NPC fieldNpc)
            return fieldNpc;

        PropertyInfo? property = typeof(Game1).GetProperty("currentSpeaker", AnyStatic);
        return property?.GetValue(null) as NPC;
    }

    private Rectangle GetActionButtonBounds(DialogueBox dialogue)
    {
        const int height = 64;
        int width = Math.Clamp(dialogue.width / 3, 260, 380);
        int x = dialogue.xPositionOnScreen + dialogue.width - width - 20;

        // Rune Factory-style context prompt: float it immediately above the dialogue box
        // instead of covering portrait/text/continue-arrow space inside the box.
        int y = dialogue.yPositionOnScreen - height - 8;
        if (y < 12)
            y = dialogue.yPositionOnScreen + 12;

        return new Rectangle(x, y, width, height);
    }

    private void DrawActionButton(SpriteBatch spriteBatch, Rectangle bounds, bool recruited)
    {
        string label = this.Helper.Translation.Get(recruited ? "button.manage" : "button.recruit").ToString();

        IClickableMenu.drawTextureBox(
            spriteBatch,
            bounds.X,
            bounds.Y,
            bounds.Width,
            bounds.Height,
            Color.White
        );

        Vector2 textSize = Game1.smallFont.MeasureString(label);
        Vector2 textPosition = new(
            bounds.X + Math.Max(16f, (bounds.Width - textSize.X) / 2f),
            bounds.Y + (bounds.Height - textSize.Y) / 2f - 1f
        );

        Utility.drawTextWithShadow(
            spriteBatch,
            label,
            Game1.smallFont,
            textPosition,
            Game1.textColor
        );
    }

    private bool IsRecruitEligible(NPC npc)
    {
        if (!this.EnsureSquadBridge() || this.squadModEntry is null)
            return false;

        object? config = GetProperty(this.squadModEntry, "Config");
        bool recruitAll = GetBoolProperty(config, "RecruitAllNpcs");

        return recruitAll
            || npc is Pet
            || Game1.player.friendshipData.ContainsKey(npc.Name);
    }

    private bool IsRecruited(NPC npc)
    {
        if (!this.EnsureSquadBridge() || this.squadModEntry is null)
            return false;

        object? squadManager = GetProperty(this.squadModEntry, "SquadManager");
        if (squadManager is null)
            return false;

        try
        {
            MethodInfo? method = squadManager.GetType()
                .GetMethods(PublicInstance)
                .FirstOrDefault(p => p.Name == "IsRecruited" && p.GetParameters().Length == 1);

            return method?.Invoke(squadManager, new object?[] { npc }) as bool? ?? false;
        }
        catch (Exception ex)
        {
            this.Monitor.Log($"Could not query squad state for {npc.Name}: {ex}", LogLevel.Warn);
            return false;
        }
    }

    private void QueueSquadAction(NPC npc)
    {
        if (this.actionQueued)
            return;

        this.queuedNpc = npc;
        this.actionQueued = true;
        this.dialogueNpc = null;
        this.actionButtonBounds = Rectangle.Empty;

        Game1.playSound("smallSelect");

        // Close the ordinary NPC dialogue first. Stardew Squad is then allowed to open its
        // own recruitment/management prompt on the following update tick without two menus
        // fighting for Game1.activeClickableMenu.
        if (Game1.activeClickableMenu is DialogueBox)
            Game1.exitActiveMenu();
    }

    private void InvokeSquadAction(NPC npc)
    {
        if (Game1.isFestival())
            return;

        if (!this.EnsureSquadBridge() || this.squadModEntry is null)
        {
            Game1.addHUDMessage(new HUDMessage(this.Helper.Translation.Get("error.bridge").ToString(), HUDMessage.error_type));
            return;
        }

        try
        {
            object? squadManager = GetProperty(this.squadModEntry, "SquadManager");
            object? squadMateFactory = GetProperty(this.squadModEntry, "SquadMateFactory");
            if (squadManager is null || squadMateFactory is null)
                throw new InvalidOperationException("Stardew Squad managers are unavailable.");

            bool recruited = this.IsRecruited(npc);
            if (recruited)
            {
                MethodInfo? getMember = squadManager.GetType()
                    .GetMethods(PublicInstance)
                    .FirstOrDefault(p => p.Name == "GetMember" && p.GetParameters().Length == 1);

                object? mate = getMember?.Invoke(squadManager, new object?[] { npc });
                if (mate is null)
                    throw new InvalidOperationException("Squad member lookup returned null.");

                InvokeNoArgIfPresent(mate, "Halt");
                InvokeNoArgRequired(mate, "HandleManagement");
                return;
            }

            MethodInfo? create = squadMateFactory.GetType()
                .GetMethods(PublicInstance)
                .FirstOrDefault(p => p.Name == "Create" && p.GetParameters().Length == 1);

            object? potentialMate = create?.Invoke(squadMateFactory, new object?[] { npc });
            if (potentialMate is null)
                throw new InvalidOperationException("SquadMateFactory.Create returned null.");

            MethodInfo? recruit = potentialMate.GetType()
                .GetMethods(PublicInstance)
                .FirstOrDefault(p => p.Name == "HandleRecruitment" && p.GetParameters().Length == 1);

            if (recruit is null)
                throw new MissingMethodException(potentialMate.GetType().FullName, "HandleRecruitment");

            // This intentionally enters Stardew Squad's own recruitment flow so friendship,
            // refusal rules, cap checks, multiplayer routing, custom dialogue, and save state
            // stay 100% owned by the original mod.
            recruit.Invoke(potentialMate, new object?[] { Game1.player });
        }
        catch (TargetInvocationException ex)
        {
            Exception inner = ex.InnerException ?? ex;
            this.Monitor.Log($"Dialogue squad action failed for {npc.Name}: {inner}", LogLevel.Error);
            Game1.addHUDMessage(new HUDMessage(
                this.Helper.Translation.Get("error.action", new { name = npc.displayName }).ToString(),
                HUDMessage.error_type
            ));
        }
        catch (Exception ex)
        {
            this.Monitor.Log($"Dialogue squad action failed for {npc.Name}: {ex}", LogLevel.Error);
            Game1.addHUDMessage(new HUDMessage(
                this.Helper.Translation.Get("error.action", new { name = npc.displayName }).ToString(),
                HUDMessage.error_type
            ));
        }
    }

    private bool EnsureSquadBridge()
    {
        if (this.squadModEntry is not null)
            return true;

        try
        {
            Assembly? assembly = AppDomain.CurrentDomain.GetAssemblies()
                .FirstOrDefault(p => string.Equals(p.GetName().Name, SquadAssemblyName, StringComparison.OrdinalIgnoreCase));

            Type? patchType = assembly?.GetType("TheStardewSquad.Patches.HarmonyPatches", throwOnError: false);
            FieldInfo? modEntryField = patchType?.GetField("_modEntry", AnyStatic);
            this.squadModEntry = modEntryField?.GetValue(null);

            if (this.squadModEntry is not null)
                return true;
        }
        catch (Exception ex)
        {
            if (!this.bridgeWarned)
                this.Monitor.Log($"Failed connecting to The Stardew Squad: {ex}", LogLevel.Warn);
        }

        if (!this.bridgeWarned)
        {
            this.bridgeWarned = true;
            this.Monitor.Log("The Stardew Squad bridge is not ready yet; dialogue button will retry automatically.", LogLevel.Warn);
        }

        return false;
    }

    private static object? GetProperty(object? owner, string name)
    {
        if (owner is null)
            return null;

        return owner.GetType().GetProperty(name, PublicInstance)?.GetValue(owner);
    }

    private static bool GetBoolProperty(object? owner, string name)
    {
        return GetProperty(owner, name) is bool value && value;
    }

    private static void InvokeNoArgIfPresent(object owner, string name)
    {
        owner.GetType().GetMethod(name, PublicInstance, null, Type.EmptyTypes, null)?.Invoke(owner, null);
    }

    private static void InvokeNoArgRequired(object owner, string name)
    {
        MethodInfo? method = owner.GetType().GetMethod(name, PublicInstance, null, Type.EmptyTypes, null);
        if (method is null)
            throw new MissingMethodException(owner.GetType().FullName, name);

        method.Invoke(owner, null);
    }

    private static bool DialogueBoxReceiveLeftClickPrefix(DialogueBox __instance, int x, int y)
    {
        ModEntry? mod = Instance;
        if (mod is null || mod.dialogueNpc is null || mod.actionButtonBounds == Rectangle.Empty)
            return true;

        if (!ReferenceEquals(Game1.activeClickableMenu, __instance))
            return true;

        if (!mod.actionButtonBounds.Contains(x, y))
            return true;

        mod.QueueSquadAction(mod.dialogueNpc);
        return false;
    }
}
