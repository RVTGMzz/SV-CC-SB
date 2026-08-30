using System.Collections;
using System.Reflection;
using HarmonyLib;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
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
    private static bool allowVanillaNpcActionOnce;

    private static readonly BindingFlags PublicInstance = BindingFlags.Instance | BindingFlags.Public;
    private static readonly BindingFlags AnyInstance = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
    private static readonly BindingFlags AnyStatic = BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic;

    private enum PendingAction
    {
        None,
        Recruit,
        MemberMenu,
        Manage,
        Talk
    }

    private NPC? dialogueNpc;
    private Rectangle actionButtonBounds = Rectangle.Empty;

    private NPC? queuedNpc;
    private PendingAction pendingAction;
    private bool commandMode;

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
            this.Monitor.Log("Dialogue recruit touch hook installed.", LogLevel.Trace);
        }
        else
        {
            this.Monitor.Log("DialogueBox.receiveLeftClick(int,int,bool) was not found. Controller shoulder input will still work, but touching the recruit hint may not.", LogLevel.Warn);
        }

        MethodInfo? npcCheckAction = AccessTools.Method(
            typeof(NPC),
            nameof(NPC.checkAction),
            new[] { typeof(Farmer), typeof(GameLocation) }
        );

        if (npcCheckAction is not null)
        {
            harmony.Patch(
                npcCheckAction,
                prefix: new HarmonyMethod(typeof(ModEntry), nameof(NpcCheckActionPrefix))
            );
            this.Monitor.Log("Recruited-NPC direct interaction hook installed.", LogLevel.Trace);
        }
        else
        {
            this.Monitor.Log("NPC.checkAction(Farmer, GameLocation) was not found. Direct member interaction will use the SMAPI action-button fallback.", LogLevel.Warn);
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
            this.Monitor.Log("Connected to The Stardew Squad. Controller/mobile dialogue bridge is ready.", LogLevel.Info);
    }

    private void OnRenderedActiveMenu(object? sender, RenderedActiveMenuEventArgs e)
    {
        if (!this.TryGetDialogueContext(out DialogueBox? dialogue, out NPC? npc))
        {
            this.dialogueNpc = null;
            this.actionButtonBounds = Rectangle.Empty;
            return;
        }

        // Once an NPC is already in the player's squad, there is deliberately NO second R prompt.
        // Interacting with that NPC opens the member action menu directly instead.
        if (this.IsRecruited(npc))
        {
            this.dialogueNpc = null;
            this.actionButtonBounds = Rectangle.Empty;
            return;
        }

        if (!this.IsRecruitEligible(npc))
        {
            this.dialogueNpc = null;
            this.actionButtonBounds = Rectangle.Empty;
            return;
        }

        this.dialogueNpc = npc;
        this.actionButtonBounds = this.GetActionButtonBounds(dialogue);
        this.DrawRecruitHint(e.SpriteBatch, this.actionButtonBounds);
    }

    private void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        if (this.commandMode)
        {
            string pressed = e.Button.ToString();
            if (e.Button == SButton.Escape || pressed.Contains("ControllerB", StringComparison.OrdinalIgnoreCase))
            {
                this.Helper.Input.Suppress(e.Button);
                this.commandMode = false;
                Game1.addHUDMessage(new HUDMessage(this.Helper.Translation.Get("command.cancelled").ToString(), HUDMessage.error_type));
                return;
            }

            if (e.Button.IsActionButton() || e.Button == SButton.MouseLeft)
            {
                this.Helper.Input.Suppress(e.Button);

                Point tile = e.Button == SButton.MouseLeft || e.Button == SButton.MouseRight
                    ? e.Cursor.Tile.ToPoint()
                    : Game1.player.GetGrabTile().ToPoint();

                this.commandMode = false;
                this.InvokeManualCommand(tile);
                return;
            }
        }

        // Before recruitment only: while normal NPC dialogue is open, R/L shoulder activates
        // the visible "R - Invite" prompt. Outside that dialogue the shoulders are untouched,
        // so Stardew's normal toolbar switching remains intact.
        if (this.dialogueNpc is not null && this.actionButtonBounds != Rectangle.Empty)
        {
            string buttonName = e.Button.ToString();
            bool shoulder = buttonName.Contains("RightShoulder", StringComparison.OrdinalIgnoreCase)
                         || buttonName.Contains("LeftShoulder", StringComparison.OrdinalIgnoreCase);

            if (shoulder)
            {
                this.Helper.Input.Suppress(e.Button);
                this.QueueAction(this.dialogueNpc, PendingAction.Recruit, closeDialogue: true);
                return;
            }
        }

        // Fallback for platforms where NPC.checkAction can't be patched or is bypassed.
        // Old Stardew Squad keybinds are not suppressed here and keep working as before.
        if (Game1.activeClickableMenu is null
            && !Game1.eventUp
            && !Game1.isFestival()
            && e.Button.IsActionButton())
        {
            NPC? npc = this.FindInteractedNpc(e);
            if (npc is not null && this.IsRecruited(npc))
            {
                this.Helper.Input.Suppress(e.Button);
                this.QueueAction(npc, PendingAction.MemberMenu);
            }
        }
    }

    private void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
    {
        if (this.pendingAction == PendingAction.None || this.queuedNpc is null)
            return;

        NPC npc = this.queuedNpc;
        PendingAction action = this.pendingAction;
        this.queuedNpc = null;
        this.pendingAction = PendingAction.None;

        switch (action)
        {
            case PendingAction.Recruit:
                this.InvokeRecruitment(npc);
                break;
            case PendingAction.MemberMenu:
                this.ShowMemberActionMenu(npc);
                break;
            case PendingAction.Manage:
                this.InvokeMemberManagement(npc);
                break;
            case PendingAction.Talk:
                this.InvokeVanillaTalk(npc);
                break;
        }
    }

    private void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e)
    {
        this.dialogueNpc = null;
        this.queuedNpc = null;
        this.pendingAction = PendingAction.None;
        this.commandMode = false;
        this.actionButtonBounds = Rectangle.Empty;
        this.squadModEntry = null;
        this.bridgeWarned = false;
        allowVanillaNpcActionOnce = false;
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
        const int height = 58;
        int width = Math.Clamp(dialogue.width / 3, 280, 400);
        int x = dialogue.xPositionOnScreen + dialogue.width - width - 20;
        int y = dialogue.yPositionOnScreen - height - 8;

        if (y < 12)
            y = dialogue.yPositionOnScreen + 12;

        return new Rectangle(x, y, width, height);
    }

    private void DrawRecruitHint(SpriteBatch spriteBatch, Rectangle bounds)
    {
        string label = this.Helper.Translation.Get("button.recruit").ToString();

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

    private void ShowMemberActionMenu(NPC npc)
    {
        if (Game1.eventUp || Game1.isFestival() || !this.IsRecruited(npc))
            return;

        object? mate = this.GetLocalMate(npc);
        if (mate is null)
            return;

        bool tasksEnabled = this.GetTasksEnabled();
        string question = this.Helper.Translation.Get("member.question", new { name = npc.displayName }).ToString();

        var responses = new List<Response>
        {
            new("command", this.Helper.Translation.Get("member.command")),
            new("manage", this.Helper.Translation.Get("member.manage")),
            new("tasks", this.Helper.Translation.Get(tasksEnabled ? "member.tasks.on" : "member.tasks.off")),
            new("talk", this.Helper.Translation.Get("member.talk"))
        };

        var cancel = new Response("cancel", this.Helper.Translation.Get("member.cancel"));
        cancel.hotkey = Keys.Escape;
        responses.Add(cancel);

        Game1.currentLocation.createQuestionDialogue(
            question,
            responses.ToArray(),
            (who, key) =>
            {
                switch (key)
                {
                    case "command":
                        this.BeginCommandMode();
                        break;
                    case "manage":
                        this.QueueAction(npc, PendingAction.Manage);
                        break;
                    case "tasks":
                        this.ToggleTasksEnabled();
                        break;
                    case "talk":
                        this.QueueAction(npc, PendingAction.Talk);
                        break;
                }
            },
            npc
        );
    }

    private void BeginCommandMode()
    {
        this.commandMode = true;
        Game1.addHUDMessage(new HUDMessage(this.Helper.Translation.Get("command.pick").ToString(), HUDMessage.newQuest_type));
    }

    private void InvokeManualCommand(Point tile)
    {
        if (!this.EnsureSquadBridge() || this.squadModEntry is null)
            return;

        try
        {
            object? interactionManager = GetProperty(this.squadModEntry, "InteractionManager");
            if (interactionManager is null)
                throw new InvalidOperationException("Stardew Squad InteractionManager is unavailable.");

            // Prefer the original private routing method because it preserves farmhand -> host
            // multiplayer behavior. Fall back to the public authoritative method if needed.
            MethodInfo? routed = interactionManager.GetType().GetMethod("HandleManualCommand", AnyInstance, null, new[] { typeof(Point) }, null);
            if (routed is not null)
            {
                routed.Invoke(interactionManager, new object?[] { tile });
                return;
            }

            MethodInfo? authoritative = interactionManager.GetType().GetMethods(PublicInstance)
                .FirstOrDefault(p => p.Name == "AssignManualTaskFor" && p.GetParameters().Length == 2);

            if (authoritative is null)
                throw new MissingMethodException(interactionManager.GetType().FullName, "HandleManualCommand/AssignManualTaskFor");

            authoritative.Invoke(interactionManager, new object?[] { Game1.player, tile });
        }
        catch (TargetInvocationException ex)
        {
            this.Monitor.Log($"Squad command failed: {ex.InnerException ?? ex}", LogLevel.Error);
            Game1.addHUDMessage(new HUDMessage(this.Helper.Translation.Get("command.failed").ToString(), HUDMessage.error_type));
        }
        catch (Exception ex)
        {
            this.Monitor.Log($"Squad command failed: {ex}", LogLevel.Error);
            Game1.addHUDMessage(new HUDMessage(this.Helper.Translation.Get("command.failed").ToString(), HUDMessage.error_type));
        }
    }

    private void InvokeMemberManagement(NPC npc)
    {
        object? mate = this.GetLocalMate(npc);
        if (mate is null)
            return;

        try
        {
            this.WithVanillaDialogueUi(() => InvokeNoArgRequired(mate, "HandleManagement"));
        }
        catch (TargetInvocationException ex)
        {
            this.ReportActionError(npc, ex.InnerException ?? ex);
        }
        catch (Exception ex)
        {
            this.ReportActionError(npc, ex);
        }
    }

    private void InvokeRecruitment(NPC npc)
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
            if (this.IsRecruited(npc))
            {
                this.ShowMemberActionMenu(npc);
                return;
            }

            object? squadMateFactory = GetProperty(this.squadModEntry, "SquadMateFactory");
            if (squadMateFactory is null)
                throw new InvalidOperationException("Stardew Squad SquadMateFactory is unavailable.");

            MethodInfo? create = squadMateFactory.GetType().GetMethods(PublicInstance)
                .FirstOrDefault(p => p.Name == "Create" && p.GetParameters().Length == 1);

            object? potentialMate = create?.Invoke(squadMateFactory, new object?[] { npc });
            if (potentialMate is null)
                throw new InvalidOperationException("SquadMateFactory.Create returned null.");

            MethodInfo? recruit = potentialMate.GetType().GetMethods(PublicInstance)
                .FirstOrDefault(p => p.Name == "HandleRecruitment" && p.GetParameters().Length == 1);

            if (recruit is null)
                throw new MissingMethodException(potentialMate.GetType().FullName, "HandleRecruitment");

            // Force only this prompt through Stardew's native question-dialogue UI so controller
            // and mobile players can navigate it. The user's original Stardew Squad config is
            // restored immediately after the menu is created.
            this.WithVanillaDialogueUi(() => recruit.Invoke(potentialMate, new object?[] { Game1.player }));
        }
        catch (TargetInvocationException ex)
        {
            this.ReportActionError(npc, ex.InnerException ?? ex);
        }
        catch (Exception ex)
        {
            this.ReportActionError(npc, ex);
        }
    }

    private void InvokeVanillaTalk(NPC npc)
    {
        if (npc.currentLocation != Game1.currentLocation || Game1.eventUp)
            return;

        try
        {
            allowVanillaNpcActionOnce = true;
            npc.checkAction(Game1.player, Game1.currentLocation);
        }
        finally
        {
            allowVanillaNpcActionOnce = false;
        }
    }

    private void QueueAction(NPC npc, PendingAction action, bool closeDialogue = false)
    {
        if (this.pendingAction != PendingAction.None)
            return;

        this.queuedNpc = npc;
        this.pendingAction = action;

        if (action == PendingAction.Recruit)
        {
            this.dialogueNpc = null;
            this.actionButtonBounds = Rectangle.Empty;
            Game1.playSound("smallSelect");
        }

        if (closeDialogue && Game1.activeClickableMenu is DialogueBox)
            Game1.exitActiveMenu();
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
        if (!this.EnsureSquadBridge() || this.squadModEntry is null || !Context.IsWorldReady)
            return false;

        object? squadManager = GetProperty(this.squadModEntry, "SquadManager");
        if (squadManager is null)
            return false;

        try
        {
            long playerId = Game1.player.UniqueMultiplayerID;

            MethodInfo? localMethod = squadManager.GetType().GetMethods(PublicInstance)
                .FirstOrDefault(p =>
                {
                    if (p.Name != "IsRecruited")
                        return false;
                    ParameterInfo[] args = p.GetParameters();
                    return args.Length == 2
                        && args[0].ParameterType.IsAssignableFrom(npc.GetType())
                        && args[1].ParameterType == typeof(long);
                });

            if (localMethod is not null)
                return localMethod.Invoke(squadManager, new object?[] { npc, playerId }) as bool? ?? false;

            MethodInfo? fallback = squadManager.GetType().GetMethods(PublicInstance)
                .FirstOrDefault(p => p.Name == "IsRecruited" && p.GetParameters().Length == 1);

            return fallback?.Invoke(squadManager, new object?[] { npc }) as bool? ?? false;
        }
        catch (Exception ex)
        {
            this.Monitor.Log($"Could not query squad state for {npc.Name}: {ex}", LogLevel.Warn);
            return false;
        }
    }

    private object? GetLocalMate(NPC npc)
    {
        if (!this.EnsureSquadBridge() || this.squadModEntry is null)
            return null;

        object? squadManager = GetProperty(this.squadModEntry, "SquadManager");
        if (squadManager is null)
            return null;

        long playerId = Game1.player.UniqueMultiplayerID;

        MethodInfo? localMethod = squadManager.GetType().GetMethods(PublicInstance)
            .FirstOrDefault(p =>
            {
                if (p.Name != "GetMember")
                    return false;
                ParameterInfo[] args = p.GetParameters();
                return args.Length == 2
                    && args[0].ParameterType.IsAssignableFrom(npc.GetType())
                    && args[1].ParameterType == typeof(long);
            });

        if (localMethod is not null)
            return localMethod.Invoke(squadManager, new object?[] { npc, playerId });

        MethodInfo? fallback = squadManager.GetType().GetMethods(PublicInstance)
            .FirstOrDefault(p => p.Name == "GetMember" && p.GetParameters().Length == 1);

        return fallback?.Invoke(squadManager, new object?[] { npc });
    }

    private bool GetTasksEnabled()
    {
        object? config = GetProperty(this.squadModEntry, "Config");
        return GetBoolProperty(config, "TasksEnabled");
    }

    private void ToggleTasksEnabled()
    {
        if (!this.EnsureSquadBridge() || this.squadModEntry is null)
            return;

        object? config = GetProperty(this.squadModEntry, "Config");
        if (config is null)
            return;

        PropertyInfo? property = FindProperty(config.GetType(), "TasksEnabled");
        if (property is null || property.PropertyType != typeof(bool) || !property.CanWrite)
            return;

        bool enabled = !(property.GetValue(config) as bool? ?? false);
        property.SetValue(config, enabled);
        this.TryPersistSquadConfig(config);

        string key = enabled ? "tasks.enabled" : "tasks.disabled";
        Game1.addHUDMessage(new HUDMessage(this.Helper.Translation.Get(key).ToString(), HUDMessage.newQuest_type));
    }

    private void TryPersistSquadConfig(object config)
    {
        try
        {
            object? helper = GetProperty(this.squadModEntry, "Helper");
            if (helper is null)
                return;

            MethodInfo? writeConfig = typeof(IModHelper).GetMethods()
                .FirstOrDefault(p => p.Name == "WriteConfig" && p.IsGenericMethodDefinition && p.GetParameters().Length == 1);

            writeConfig?.MakeGenericMethod(config.GetType()).Invoke(helper, new[] { config });
        }
        catch (Exception ex)
        {
            // The in-memory toggle already succeeded. Persistence failure shouldn't block play.
            this.Monitor.Log($"TasksEnabled changed for this session, but saving Stardew Squad's config failed: {ex.Message}", LogLevel.Warn);
        }
    }

    private void WithVanillaDialogueUi(Action action)
    {
        object? config = GetProperty(this.squadModEntry, "Config");
        PropertyInfo? property = config is null ? null : FindProperty(config.GetType(), "UseVanillaDialogueUI");

        if (config is null || property is null || property.PropertyType != typeof(bool) || !property.CanWrite)
        {
            action();
            return;
        }

        bool original = property.GetValue(config) as bool? ?? false;
        property.SetValue(config, true);
        try
        {
            action();
        }
        finally
        {
            property.SetValue(config, original);
        }
    }

    private NPC? FindInteractedNpc(ButtonPressedEventArgs e)
    {
        Point grabTile = Game1.player.GetGrabTile().ToPoint();
        NPC? npc = FindNpcAtTile(grabTile);
        if (npc is not null)
            return npc;

        return FindNpcAtTile(e.Cursor.Tile.ToPoint());
    }

    private static NPC? FindNpcAtTile(Point tile)
    {
        if (Game1.currentLocation is null)
            return null;

        Rectangle tileBounds = new(tile.X * 64, tile.Y * 64, 64, 64);
        return Game1.currentLocation.characters
            .OfType<NPC>()
            .FirstOrDefault(p => p.GetBoundingBox().Intersects(tileBounds));
    }

    private void ReportActionError(NPC npc, Exception ex)
    {
        this.Monitor.Log($"Dialogue squad action failed for {npc.Name}: {ex}", LogLevel.Error);
        Game1.addHUDMessage(new HUDMessage(
            this.Helper.Translation.Get("error.action", new { name = npc.displayName }).ToString(),
            HUDMessage.error_type
        ));
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
            this.Monitor.Log("The Stardew Squad bridge is not ready yet; UI actions will retry automatically.", LogLevel.Warn);
        }

        return false;
    }

    private static PropertyInfo? FindProperty(Type type, string name)
    {
        Type? cursor = type;
        while (cursor is not null)
        {
            PropertyInfo? property = cursor.GetProperty(name, AnyInstance | BindingFlags.DeclaredOnly);
            if (property is not null)
                return property;
            cursor = cursor.BaseType;
        }
        return null;
    }

    private static object? GetProperty(object? owner, string name)
    {
        if (owner is null)
            return null;

        return FindProperty(owner.GetType(), name)?.GetValue(owner);
    }

    private static bool GetBoolProperty(object? owner, string name)
    {
        return GetProperty(owner, name) is bool value && value;
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

        mod.QueueAction(mod.dialogueNpc, PendingAction.Recruit, closeDialogue: true);
        return false;
    }

    private static bool NpcCheckActionPrefix(NPC __instance, Farmer who, GameLocation l, ref bool __result)
    {
        if (allowVanillaNpcActionOnce)
        {
            allowVanillaNpcActionOnce = false;
            return true;
        }

        ModEntry? mod = Instance;
        if (mod is null || !Context.IsWorldReady || Game1.eventUp || Game1.isFestival())
            return true;

        if (!ReferenceEquals(who, Game1.player))
            return true;

        if (!mod.IsRecruited(__instance))
            return true;

        mod.QueueAction(__instance, PendingAction.MemberMenu);
        __result = true;
        return false;
    }
}
