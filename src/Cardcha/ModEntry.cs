using Cardcha.Integrations;
using Cardcha.Models;
using Cardcha.Patches;
using Cardcha.Services;
using Cardcha.UI;
using HarmonyLib;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Menus;

namespace Cardcha;

internal sealed class ModEntry : Mod
{
    internal static IMonitor? StaticMonitor;
    internal static IModHelper? StaticHelper;
    private static readonly HashSet<string> LoggedErrors = new(StringComparer.OrdinalIgnoreCase);

    private ModConfig Config = null!;
    private CardRegistry Cards = null!;
    private SaveService Save = null!;
    private GachaService Gacha = null!;
    private CardUpgradeService Upgrades = null!;
    private LoadoutService Loadout = null!;
    private ItemAssetService Items = null!;
    private ResourceService Resources = null!;
    private CombatService Combat = null!;
    private CardRenderer Renderer = null!;
    private ControllerProfileService Controller = null!;
    private ProgressionService Progression = null!;
    private DropService Drops = null!;
    private MonsterDeathService Deaths = null!;
    private UniversalEnemyObserverService EnemyObserver = null!;
    private CombatHudRenderer CombatHud = null!;
    private CardchaBookTabService BookTab = null!;
    private CardchaStoryService Story = null!;
    private MimiMysteryTownService Mystery = null!;
    private MimiSocialService Social = null!;
    private MimiHomeService Home = null!;
    private MimiAtticVisualService AtticVisual = null!;
    private WorldActorService WorldActors = null!;
    private PortableMachineService PortableMachine = null!;

    public override void Entry(IModHelper helper)
    {
        StaticMonitor = this.Monitor;
        StaticHelper = helper;
        this.Config = helper.ReadConfig<ModConfig>();
        this.Controller = new ControllerProfileService(this.Config, this.Monitor);
        this.Cards = new CardRegistry(helper);
        this.Save = new SaveService(helper);
        this.Upgrades = new CardUpgradeService(this.Save, this.Cards);
        this.Loadout = new LoadoutService(this.Save, this.Cards, this.Upgrades);
        this.Gacha = new GachaService(this.Cards, this.Save, this.Config);
        this.Items = new ItemAssetService(helper);
        this.Resources = new ResourceService(this.Save);
        this.Combat = new CombatService(this.Config, this.Loadout, this.Save, this.Cards, this.Upgrades);
        this.Renderer = new CardRenderer(helper);
        this.Progression = new ProgressionService(helper, this.Monitor, this.Save);
        this.Drops = new DropService(
            this.Config,
            this.Loadout,
            this.Upgrades,
            this.Cards,
            this.Resources,
            this.Progression.OnFirstCardboardScrapDropped,
            () => this.Progression.HasFirstScrapTriggered,
            () => this.Combat.CurrentNoHitKillStreak
        );
        this.Deaths = new MonsterDeathService(this.Drops, this.Combat);
        this.EnemyObserver = new UniversalEnemyObserverService(this.Deaths);
        this.CombatHud = new CombatHudRenderer(
            this.Config,
            this.Combat,
            this.Loadout,
            this.Save,
            this.Cards,
            this.Renderer
        );
        this.BookTab = new CardchaBookTabService(
            helper,
            this.Save,
            this.OpenBinderFromMenu
        );
        this.WorldActors = new WorldActorService(this.Monitor);
        this.PortableMachine = new PortableMachineService(
            helper,
            this.Monitor,
            this.Save,
            this.OpenPortableMachineMenu
        );
        this.Story = new CardchaStoryService(
            helper,
            this.Monitor,
            this.Save,
            this.Progression,
            this.Resources,
            this.Config,
            this.WorldActors
        );
        this.Mystery = new MimiMysteryTownService(
            helper,
            this.Monitor,
            this.Save,
            this.OpenMimiShop,
            this.WorldActors,
            () => this.Story.OwnsMimiWorldActor
        );
        this.Social = new MimiSocialService(
            helper,
            this.Monitor,
            this.Save,
            this.WorldActors,
            this.OpenMimiShop
        );
        this.Home = new MimiHomeService(
            helper,
            this.Monitor,
            this.Save,
            this.WorldActors,
            () => this.Story.OwnsMimiWorldActor,
            () => this.Mystery.OwnsMimiWorldActor
        );
        this.AtticVisual = new MimiAtticVisualService(helper, this.Save);

        helper.Events.Content.AssetRequested += this.Items.OnAssetRequested;
        helper.Events.Content.AssetRequested += this.WorldActors.OnAssetRequested;
        helper.Events.Content.AssetRequested += this.Mystery.OnAssetRequested;
        helper.Events.Content.AssetRequested += this.Social.OnAssetRequested;
        helper.Events.Content.AssetRequested += this.AtticVisual.OnAssetRequested;
        helper.Events.GameLoop.GameLaunched += this.OnGameLaunched;
        helper.Events.GameLoop.SaveLoaded += this.OnSaveLoaded;
        helper.Events.GameLoop.Saving += this.OnSaving;
        helper.Events.GameLoop.DayStarted += this.OnDayStarted;
        helper.Events.GameLoop.TimeChanged += this.Mystery.OnTimeChanged;
        helper.Events.GameLoop.UpdateTicked += this.OnUpdateTicked;
        helper.Events.GameLoop.ReturnedToTitle += this.OnReturnedToTitle;
        helper.Events.Display.RenderedHud += this.OnRenderedHud;
        helper.Events.Display.RenderedWorld += this.Story.OnRenderedWorld;
        helper.Events.Display.RenderedWorld += this.AtticVisual.OnRenderedWorld;
        helper.Events.Display.MenuChanged += this.BookTab.OnMenuChanged;
        helper.Events.Display.RenderedActiveMenu += this.BookTab.OnRenderedActiveMenu;
        helper.Events.Input.ButtonPressed += this.BookTab.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.Social.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.Mystery.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.Home.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.AtticVisual.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.PortableMachine.OnButtonPressed;
        helper.Events.Player.Warped += this.Story.OnWarped;
        helper.Events.World.ObjectListChanged += this.OnObjectListChanged;

        helper.ConsoleCommands.Add("cardcha_status", "Show Cardcha prototype state.", this.CommandStatus);
        helper.ConsoleCommands.Add("cardcha_pull", "Debug pull without resource cost: cardcha_pull [standard|premium] [count]", this.CommandPull);
        helper.ConsoleCommands.Add("cardcha_unlock", "Unlock cards for testing: cardcha_unlock <card-id|all>", this.CommandUnlock);
        helper.ConsoleCommands.Add("cardcha_equip", "Equip a prototype card by ID: cardcha_equip <card-id>", this.CommandEquip);
        helper.ConsoleCommands.Add("cardcha_unequip", "Unequip a prototype card by ID.", this.CommandUnequip);
        helper.ConsoleCommands.Add("cardcha_combat_status", "Show active Cardcha combat state.", this.CommandCombatStatus);
        helper.ConsoleCommands.Add("cardcha_give_scrap", "Give prototype Scrap: cardcha_give_scrap [normal|shiny] [amount]", this.CommandGiveScrap);
        helper.ConsoleCommands.Add("cardcha_give_machine", "Give the Cardcha! Machine prototype.", this.CommandGiveMachine);
        helper.ConsoleCommands.Add("cardcha_give_portable_machine", "Give the Portable Cardcha Machine for testing.", this.CommandGivePortableMachine);
        helper.ConsoleCommands.Add("cardcha_open_machine", "Open the Cardcha! Machine UI for testing.", this.CommandOpenMachine);
        helper.ConsoleCommands.Add("cardcha_open_portable_machine", "Open the Portable Cardcha Machine UI for testing.", this.CommandOpenPortableMachine);
        helper.ConsoleCommands.Add("cardcha_open_binder", "Open the Cardcha! Binder UI for testing.", this.CommandOpenBinder);
        helper.ConsoleCommands.Add("cardcha_test_report", "Show combat verification + save persistence report.", this.CommandTestReport);
        helper.ConsoleCommands.Add("cardcha_test_reset", "Reset transient Cardcha combat verification counters.", this.CommandTestReset);
        helper.ConsoleCommands.Add("cardcha_persistence_status", "Show the last save/reload persistence audit.", this.CommandPersistenceStatus);
        helper.ConsoleCommands.Add("cardcha_progression_status", "Show normal-gameplay onboarding state.", this.CommandProgressionStatus);
        helper.ConsoleCommands.Add("cardcha_drop_status", "Show monster-death and Scrap-drop diagnostics.", this.CommandDropStatus);
        helper.ConsoleCommands.Add("cardcha_version", "Show the exact Cardcha build currently loaded.", this.CommandVersion);
        helper.ConsoleCommands.Add("cardcha_enemy_status", "Show universal mod-enemy observer diagnostics.", this.CommandEnemyStatus);
        helper.ConsoleCommands.Add("cardcha_machine_status", "Show Cardcha machine objects in inventory/current location.", this.CommandMachineStatus);
        helper.ConsoleCommands.Add("cardcha_portable_status", "Show Portable Cardcha Machine entitlement/milestone state.", this.CommandPortableStatus);
        helper.ConsoleCommands.Add("cardcha_loot_rates", "Show the current Cardcha loot profile.", this.CommandLootRates);
        helper.ConsoleCommands.Add("cardcha_hud_toggle", "Toggle Cardcha combat HUD on/off.", this.CommandHudToggle);
        helper.ConsoleCommands.Add("cardcha_book_status", "Show Cardcha Book tab layout/controller diagnostics.", this.CommandBookStatus);
        helper.ConsoleCommands.Add("cardcha_story_status", "Show MiMi/Cardcha Chapter 1 story state.", this.CommandStoryStatus);
        helper.ConsoleCommands.Add("cardcha_controller_status", "Show resolved Cardcha controller profile and mapping.", this.CommandControllerStatus);
        helper.ConsoleCommands.Add("cardcha_test_attic", "TEST ONLY: toggle direct MiMi attic access without changing friendship/story progression.", this.CommandTestAttic);
    }

    private void OnGameLaunched(object? sender, GameLaunchedEventArgs e)
    {
        this.Cards.Load();
        this.RegisterConfigMenu();

        Harmony harmony = new(this.ModManifest.UniqueID);
        MonsterDropPatch.Apply(harmony, this.Deaths);
        MonsterDamagePatch.Apply(harmony, this.Combat, this.Deaths);
        CriticalChancePatch.Apply(harmony, this.Combat);
        FarmerDamagePatch.Apply(harmony, this.Combat);
        MachineInteractionPatch.Apply(harmony, this.OpenMachineMenu);
        BookNavigationPatch.Apply(harmony, this.BookTab);
        MimiProfileMenuPatch.Apply(harmony);

        this.Monitor.Log(
            $"Cardcha! v0.3.0-alpha.27.0.7.8.7 ATTIC ACCEPTANCE POLISH TEST with {this.Cards.All.Count} cards. The cardboard is now combat-capable. This seems unsafe.",
            LogLevel.Info
        );
    }

    private void RegisterConfigMenu()
    {
        IGenericModConfigMenuApi? gmcm = this.Helper.ModRegistry.GetApi<IGenericModConfigMenuApi>("spacechase0.GenericModConfigMenu");
        if (gmcm is null)
            return;

        gmcm.Register(
            this.ModManifest,
            reset: () =>
            {
                ModConfig defaults = new();
                this.Config.ControllerLayout = defaults.ControllerLayout;
                this.Config.ControllerMapping = defaults.ControllerMapping;
            },
            save: () => this.Helper.WriteConfig(this.Config)
        );

        gmcm.AddSectionTitle(
            this.ModManifest,
            () => ModEntry.T("config.controller.section"),
            () => ModEntry.T("config.controller.section.tooltip")
        );

        gmcm.AddTextOption(
            this.ModManifest,
            () => this.Config.ControllerLayout,
            value => this.Config.ControllerLayout = value,
            () => ModEntry.T("config.controller.layout"),
            () => ModEntry.T("config.controller.layout.tooltip"),
            new[] { "Auto", "Xbox", "Nintendo", "PlayStation", "Generic" },
            value => ModEntry.T($"config.controller.layout.{value.ToLowerInvariant()}")
        );

        gmcm.AddTextOption(
            this.ModManifest,
            () => this.Config.ControllerMapping,
            value => this.Config.ControllerMapping = value,
            () => ModEntry.T("config.controller.mapping"),
            () => ModEntry.T("config.controller.mapping.tooltip"),
            new[] { "Auto", "Standard", "NintendoNative" },
            value => ModEntry.T($"config.controller.mapping.{value.ToLowerInvariant()}")
        );
    }

    private void OnSaveLoaded(object? sender, SaveLoadedEventArgs e)
    {
        this.Cards.RefreshTranslations();
        this.Save.Load();

        // Let progression self-heal old saves first (it may discover an existing Machine and
        // unlock the Binder), then reconcile Scrap storage to the correct physical/wallet phase.
        this.Progression.OnSaveLoaded();
        this.PortableMachine.OnSaveLoaded();
        (int storageNormal, int storageShiny) = this.Resources.SyncStorageModeOnLoad();
        if (storageNormal > 0 || storageShiny > 0)
        {
            string direction = this.Resources.IsBinderWalletActive
                ? "backpack -> Binder wallet"
                : "prototype wallet -> backpack";
            this.Monitor.Log(
                $"Reconciled Scrap storage ({direction}): normal={storageNormal}, shiny={storageShiny}.",
                LogLevel.Info
            );
        }

        this.Combat.ResetRuntime();
        this.Combat.ResetVerificationTelemetry();
        this.EnemyObserver.Reset();
        this.Combat.SyncPassiveBuffs();
        this.Story.OnSaveLoaded();
        this.Mystery.OnSaveLoaded();
        this.Social.OnSaveLoaded();
        this.Home.OnSaveLoaded();
        this.NormalizeCardchaMachinePlacement();
        this.NormalizePortableMachinePlacement();

        this.Monitor.Log(
            $"Save persistence audit: {this.Save.LastPersistenceMessage}",
            this.Save.LastPersistenceCheckPassed ? LogLevel.Info : LogLevel.Warn
        );
    }

    private void OnSaving(object? sender, SavingEventArgs e)
    {
        // ChaCha is a runtime-only world actor; remove it before Stardew serializes locations.
        this.Story.OnSaving();
        this.Save.Save();
    }

    private void OnDayStarted(object? sender, DayStartedEventArgs e)
    {
        this.Save.ResetForNewDay();
        this.Combat.ResetRuntime();
        this.Combat.ResetVerificationTelemetry();
        this.EnemyObserver.Reset();
        this.Combat.SyncPassiveBuffs();
        this.Progression.OnDayStarted();
        this.Story.OnDayStarted();
        this.Mystery.OnDayStarted();
        this.Social.OnDayStarted();
        this.Home.OnDayStarted();
        this.Save.Save();
    }

    private void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        this.Story.OnUpdateTicked(sender, e);
        this.Mystery.OnUpdateTicked();
        this.Home.OnUpdateTicked(e);
        this.Social.OnUpdateTicked(e);

        // Universal compatibility observer intentionally runs every tick so a custom
        // enemy that is removed immediately on defeat can't disappear between samples.
        this.EnemyObserver.Update(e.Ticks);

        if (!e.IsMultipleOf(15))
            return;

        this.Combat.SyncPassiveBuffs();
        this.Progression.OnUpdate();
    }

    private void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e)
    {
        this.Combat.ResetRuntime();
        this.EnemyObserver.Reset();
        this.Progression.OnReturnedToTitle();
        this.Story.OnReturnedToTitle();
        this.Mystery.OnReturnedToTitle();
        this.Social.OnReturnedToTitle();
        this.Home.OnReturnedToTitle();
        this.Save.Clear();
    }

    private void OnObjectListChanged(object? sender, ObjectListChangedEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        foreach (var pair in e.Added.ToList())
        {
            if (ItemAssetService.IsPortableMachine(pair.Value))
            {
                e.Location.Objects.Remove(pair.Key);
                this.ReturnPortableMachineToPlayer();
                Game1.showGlobalMessage(ModEntry.T("portable.machine.recovered"));
                this.Monitor.Log($"Recovered Portable Cardcha Machine placement at {e.Location.NameOrUniqueName}.", LogLevel.Info);
                continue;
            }

            if (IsMainFarmHouse(e.Location) || !MachineInteractionPatch.IsCardchaMachine(pair.Value))
                continue;

            // The stationary Cardcha machine is intentionally a home appliance, not a field
            // machine. If a modded map/placement path bypasses BigCraftableData's outdoor flag,
            // take it straight back into the player's inventory instead of leaving a bad placement.
            e.Location.Objects.Remove(pair.Key);
            this.ReturnCardchaMachineToPlayer();
            Game1.showGlobalMessage(ModEntry.T("machine.place.home-only"));
            this.Monitor.Log(
                $"Blocked Cardcha Machine placement outside the main FarmHouse ({e.Location.NameOrUniqueName}).",
                LogLevel.Info
            );
        }
    }

    private void NormalizeCardchaMachinePlacement()
    {
        if (!Context.IsWorldReady)
            return;

        GameLocation? mainHouse = Game1.getLocationFromName("FarmHouse");
        if (mainHouse is null)
            return;

        int recovered = 0;
        foreach (GameLocation location in Game1.locations.ToList())
        {
            if (ReferenceEquals(location, mainHouse))
                continue;

            foreach (var pair in location.Objects.Pairs
                         .Where(pair => MachineInteractionPatch.IsCardchaMachine(pair.Value))
                         .ToList())
            {
                location.Objects.Remove(pair.Key);
                recovered++;
                this.ReturnCardchaMachineToPlayer();
            }
        }

        if (recovered > 0)
        {
            Game1.showGlobalMessage(ModEntry.T("machine.place.home-only"));
            this.Monitor.Log(
                $"Recovered {recovered} Cardcha Machine(s) from non-main-house locations after the placement rule update.",
                LogLevel.Info
            );
        }
    }

    private void NormalizePortableMachinePlacement()
    {
        if (!Context.IsWorldReady) return;
        int recovered = 0;
        foreach (GameLocation location in Game1.locations.ToList())
        {
            foreach (var pair in location.Objects.Pairs.Where(pair => ItemAssetService.IsPortableMachine(pair.Value)).ToList())
            {
                location.Objects.Remove(pair.Key);
                recovered++;
                this.ReturnPortableMachineToPlayer();
            }
        }
        if (recovered > 0)
        {
            Game1.showGlobalMessage(ModEntry.T("portable.machine.recovered"));
            this.Monitor.Log($"Recovered {recovered} misplaced Portable Cardcha Machine(s).", LogLevel.Info);
        }
    }

    private void ReturnPortableMachineToPlayer()
    {
        Item portable = ItemAssetService.CreatePortableMachineItem();
        Item? leftover = Game1.player.addItemToInventory(portable);
        if (leftover is not null && Game1.currentLocation is not null)
            Game1.createItemDebris(leftover, Game1.player.Position, -1, Game1.currentLocation);
    }

    private static bool IsMainFarmHouse(GameLocation location)
    {
        GameLocation? mainHouse = Game1.getLocationFromName("FarmHouse");
        return mainHouse is not null && ReferenceEquals(location, mainHouse);
    }

    private void ReturnCardchaMachineToPlayer()
    {
        Item machine = ItemRegistry.Create($"(BC){ItemAssetService.CardchaMachineId}");
        if (machine is StardewValley.Object machineObject)
            machineObject.modData[ItemAssetService.MachineMarkerKey] = "1";

        Item? leftover = Game1.player.addItemToInventory(machine);
        if (leftover is not null && Game1.currentLocation is not null)
            Game1.createItemDebris(leftover, Game1.player.Position, -1, Game1.currentLocation);
    }

    private void OnRenderedHud(object? sender, RenderedHudEventArgs e)
    {
        this.CombatHud.Draw(e.SpriteBatch);
        this.Progression.DrawCenteredNotice(e.SpriteBatch);
    }

    private void OpenMachineMenu()
    {
        if (!Context.IsWorldReady || Game1.activeClickableMenu is not null)
            return;

        Game1.activeClickableMenu = new CardchaMachineMenu(
            this.Gacha,
            this.Resources,
            this.Save,
            this.Cards,
            this.Loadout,
            this.Upgrades,
            this.Config,
            this.Renderer,
            this.Controller,
            this.Combat.SyncPassiveBuffs,
            this.Story.OnPullResolved,
            CardchaMachineMode.Stationary
        );
    }

    private void OpenMachineFromBinder()
    {
        if (!Context.IsWorldReady)
            return;

        // This callback is invoked while the Binder is still the active menu, so the
        // normal world-interaction guard in OpenMachineMenu() must not reject it.
        // Replacing the active menu keeps the transition atomic and avoids briefly
        // returning control to gameplay between the Binder and the machine.
        Game1.activeClickableMenu = new CardchaMachineMenu(
            this.Gacha,
            this.Resources,
            this.Save,
            this.Cards,
            this.Loadout,
            this.Upgrades,
            this.Config,
            this.Renderer,
            this.Controller,
            this.Combat.SyncPassiveBuffs,
            this.Story.OnPullResolved,
            CardchaMachineMode.Stationary
        );
    }

    private void OpenPortableMachineMenu()
    {
        if (!Context.IsWorldReady || Game1.activeClickableMenu is not null)
            return;

        Game1.activeClickableMenu = new CardchaMachineMenu(
            this.Gacha,
            this.Resources,
            this.Save,
            this.Cards,
            this.Loadout,
            this.Upgrades,
            this.Config,
            this.Renderer,
            this.Controller,
            this.Combat.SyncPassiveBuffs,
            this.Story.OnPullResolved,
            CardchaMachineMode.Portable
        );
    }

    private void OpenMimiShop()
    {
        if (!Context.IsWorldReady || Game1.activeClickableMenu is not null)
            return;

        Game1.activeClickableMenu = new MimiScrapShopMenu(
            this.Resources,
            this.Save,
            this.PortableMachine,
            this.Controller
        );
    }

    private void OpenBinderMenu()
    {
        if (!Context.IsWorldReady || Game1.activeClickableMenu is not null)
            return;

        Game1.activeClickableMenu = new CardchaBinderMenu(
            this.Cards,
            this.Save,
            this.Resources,
            this.Loadout,
            this.Upgrades,
            this.Renderer,
            this.Controller,
            () => Game1.exitActiveMenu(),
            this.OpenMachineFromBinder,
            this.Combat.SyncPassiveBuffs,
            ModEntry.T("binder.back.close")
        );
    }

    private void OpenBinderFromMenu(IClickableMenu previousMenu)
    {
        if (!Context.IsWorldReady)
            return;

        string backLabel = previousMenu is StardewValley.Menus.ItemGrabMenu
            ? ModEntry.T("binder.back.chest")
            : ModEntry.T("binder.back.menu");

        Game1.activeClickableMenu = new CardchaBinderMenu(
            this.Cards,
            this.Save,
            this.Resources,
            this.Loadout,
            this.Upgrades,
            this.Renderer,
            this.Controller,
            () =>
            {
                Game1.activeClickableMenu = previousMenu;

                if (Game1.options.SnappyMenus
                    && previousMenu.currentlySnappedComponent is null)
                {
                    previousMenu.snapToDefaultClickableComponent();
                }
            },
            this.OpenMachineFromBinder,
            this.Combat.SyncPassiveBuffs,
            backLabel,
            previousMenu
        );
    }

    private void CommandControllerStatus(string command, string[] args)
    {
        this.Monitor.Log($"Cardcha controller: {this.Controller.Describe()}", LogLevel.Info);
        this.Monitor.Log(
            $"Hints: Confirm={this.Controller.GetLabel(ControllerAction.Confirm)}, Favorite={this.Controller.GetLabel(ControllerAction.Favorite)}, Deselect={this.Controller.GetLabel(ControllerAction.Deselect)}, Exit={this.Controller.GetLabel(ControllerAction.Exit)}",
            LogLevel.Info
        );
    }

    private void CommandStatus(string command, string[] args)
    {
        if (!Context.IsWorldReady)
        {
            this.Monitor.Log("Load a save first.", LogLevel.Warn);
            return;
        }

        SaveData d = this.Save.Data;
        this.Monitor.Log(
            $"Owned: {d.OwnedCards.Count}/{this.Cards.All.Count} | Equipped: [{string.Join(", ", d.EquippedCards)}] | Slots: {d.ActiveCardSlotCount}/5 | Copies: {d.CardCopies.Values.Sum()} | SlotDust: {d.SuspiciousDust} | PullIndex: {d.PullIndex} | Standard Legendary Sympathy: {d.StandardSinceLegendary}/{this.Config.StandardLegendaryPity} | Premium: {d.PremiumSinceLegendary}/{this.Config.PremiumLegendaryPity}",
            LogLevel.Info
        );
    }

    private void CommandPull(string command, string[] args)
    {
        if (!Context.IsWorldReady)
            return;

        PullType type = args.FirstOrDefault()?.Equals("premium", StringComparison.OrdinalIgnoreCase) == true
            ? PullType.Premium
            : PullType.Standard;
        int count = args.Length >= 2 && int.TryParse(args[1], out int parsed) ? Math.Clamp(parsed, 1, 10) : 1;

        for (int i = 0; i < count; i++)
        {
            PullResult result = this.Gacha.Pull(type);
            string suffix = result.IsNew ? "NEW!" : $"duplicate -> +{result.DuplicateCopiesAwarded} same-card copy";
            this.Monitor.Log($"[{type}] {result.Card.Rarity}: {result.Card.Name} — {suffix}", LogLevel.Alert);
        }
    }

    private void CommandUnlock(string command, string[] args)
    {
        if (!Context.IsWorldReady)
            return;

        string id = args.FirstOrDefault() ?? "";
        if (id.Equals("all", StringComparison.OrdinalIgnoreCase))
        {
            foreach (CardDefinition card in this.Cards.All)
                this.Save.Data.OwnedCards.Add(card.Id);

            this.Save.Save();
            this.Monitor.Log($"Unlocked all {this.Cards.All.Count} prototype cards. Responsible testing has ended.", LogLevel.Alert);
            return;
        }

        CardDefinition? match = this.Cards.Get(id);
        if (match is null)
        {
            this.Monitor.Log($"Unknown card '{id}'.", LogLevel.Warn);
            return;
        }

        this.Save.Data.OwnedCards.Add(match.Id);
        this.Save.Save();
        this.Monitor.Log($"Unlocked {match.Name} ({match.Id}).", LogLevel.Info);
    }

    private void CommandEquip(string command, string[] args)
    {
        string id = args.FirstOrDefault() ?? "";
        bool ok = this.Loadout.Equip(id);
        if (ok)
            this.Combat.SyncPassiveBuffs();

        int slots = this.Upgrades.GetUnlockedSlotCount();
        this.Monitor.Log(
            ok
                ? $"Equipped {id}."
                : $"Couldn't equip '{id}' (not owned, unknown, or {slots} active slots full).",
            ok ? LogLevel.Info : LogLevel.Warn
        );
    }

    private void CommandUnequip(string command, string[] args)
    {
        string id = args.FirstOrDefault() ?? "";
        bool ok = this.Loadout.Unequip(id);
        if (ok)
            this.Combat.SyncPassiveBuffs();

        this.Monitor.Log(ok ? $"Unequipped {id}." : $"'{id}' wasn't equipped.", ok ? LogLevel.Info : LogLevel.Warn);
    }

    private void CommandCombatStatus(string command, string[] args)
    {
        if (!Context.IsWorldReady)
            return;

        this.Monitor.Log(
            $"Combat cards: {(this.Config.EnableCombatCards ? "ON" : "OFF")} | Chain Hunter: {this.Combat.CurrentChainHunterStacks}/{this.Config.ChainHunterMaxStacks} stacks ({this.Combat.CurrentChainSecondsRemaining:0.0}s) | Phoenix used today: {this.Save.Data.PhoenixHeartUsedToday} | HP: {Game1.player.health}/{Game1.player.maxHealth}",
            LogLevel.Info
        );
    }

    private void CommandTestReport(string command, string[] args)
    {
        if (!Context.IsWorldReady)
        {
            this.Monitor.Log("Load a save first.", LogLevel.Warn);
            return;
        }

        SaveData d = this.Save.Data;
        this.Monitor.Log(
            "===== CARDCHA TEST REPORT =====\n" +
            $"Owned: {d.OwnedCards.Count}/{this.Cards.All.Count}\n" +
            $"Equipped: [{string.Join(", ", d.EquippedCards)}]\n" +
            $"Dust: {d.SuspiciousDust} | PullIndex: {d.PullIndex}\n" +
            $"Persistence: {this.Save.DescribePersistence()}\n" +
            this.Combat.BuildVerificationReport(),
            LogLevel.Alert
        );
    }

    private void CommandTestReset(string command, string[] args)
    {
        this.Combat.ResetVerificationTelemetry();
        this.Monitor.Log("Cardcha combat verification counters reset. Go bonk something.", LogLevel.Info);
    }

    private void CommandPersistenceStatus(string command, string[] args)
    {
        if (!Context.IsWorldReady)
        {
            this.Monitor.Log("Load a save first.", LogLevel.Warn);
            return;
        }

        this.Monitor.Log(
            $"Persistence: {this.Save.DescribePersistence()}",
            this.Save.LastPersistenceCheckPassed ? LogLevel.Info : LogLevel.Warn
        );
    }

    private void CommandHudToggle(string command, string[] args)
    {
        this.Config.EnableCombatHud = !this.Config.EnableCombatHud;
        this.Helper.WriteConfig(this.Config);

        this.Monitor.Log(
            ModEntry.T(
                this.Config.EnableCombatHud ? "hud.toggle.on" : "hud.toggle.off"
            ),
            LogLevel.Info
        );
    }

    private void CommandStoryStatus(string command, string[] args)
    {
        this.Monitor.Log(
            "===== CARDCHA STORY STATUS =====\n" +
            this.Progression.DescribeState() + "\n" +
            this.Story.Describe() + "\n" +
            this.Mystery.Describe() + "\n" +
            this.Social.Describe() + "\n" +
            this.Home.Describe() + "\n" +
            this.PortableMachine.Describe(),
            LogLevel.Alert
        );
    }

    private void CommandBookStatus(string command, string[] args)
    {
        this.Monitor.Log(
            "===== CARDCHA BOOK STATUS =====\n" + this.BookTab.Describe(),
            LogLevel.Alert
        );
    }

    private void CommandLootRates(string command, string[] args)
    {
        this.Monitor.Log(
            "===== CARDCHA LOOT RATES v0.3.0-alpha.26.4 =====\n" +
            "Regular enemy: 12% normal Scrap, amount 1; dry-streak guarantee at 8 kills; Shiny 3%, amount 1.\n" +
            "Boss-like (boss/elite/apex/champion/raid hint): 65% normal Scrap, amount 2; Shiny 25%, amount 1.\n" +
            "Raw Max HP is NOT used to classify or scale rewards.",
            LogLevel.Alert
        );
    }

    private void CommandMachineStatus(string command, string[] args)
    {
        if (!Context.IsWorldReady)
        {
            this.Monitor.Log("Load a save first.", LogLevel.Warn);
            return;
        }

        List<string> lines = new();

        for (int i = 0; i < Game1.player.Items.Count; i++)
        {
            Item? item = Game1.player.Items[i];
            if (item is StardewValley.Object obj
                && (MachineInteractionPatch.IsCardchaMachine(obj)
                    || ItemAssetService.IsPortableMachine(obj)
                    || obj.Name.Contains("Cardcha", StringComparison.OrdinalIgnoreCase)))
            {
                lines.Add(
                    $"Inventory[{i}]: Qualified={obj.QualifiedItemId} | ItemId={obj.ItemId} | " +
                    $"Name={obj.Name} | StationaryMarker={obj.modData.ContainsKey(ItemAssetService.MachineMarkerKey)} | " +
                    $"Portable={ItemAssetService.IsPortableMachine(obj)}"
                );
            }
        }

        if (Game1.currentLocation is not null)
        {
            foreach ((Microsoft.Xna.Framework.Vector2 tile, StardewValley.Object obj) in Game1.currentLocation.Objects.Pairs)
            {
                if (MachineInteractionPatch.IsCardchaMachine(obj)
                    || obj.Name.Contains("Cardcha", StringComparison.OrdinalIgnoreCase))
                {
                    lines.Add(
                        $"Placed[{tile.X:0},{tile.Y:0}]: Qualified={obj.QualifiedItemId} | ItemId={obj.ItemId} | " +
                        $"Name={obj.Name} | Marker={obj.modData.ContainsKey(ItemAssetService.MachineMarkerKey)}"
                    );
                }
            }
        }

        this.Monitor.Log(
            "===== CARDCHA MACHINE STATUS =====\n" +
            (lines.Count == 0 ? "No Cardcha-looking machine found." : string.Join("\n", lines)),
            LogLevel.Alert
        );
    }

    private void CommandPortableStatus(string command, string[] args)
    {
        if (!Context.IsWorldReady)
        {
            this.Monitor.Log("Load a save first.", LogLevel.Warn);
            return;
        }

        this.Monitor.Log(
            "===== CARDCHA PORTABLE MACHINE STATUS =====\n" +
            this.PortableMachine.Describe(),
            LogLevel.Alert
        );
    }

    private void CommandEnemyStatus(string command, string[] args)
    {
        if (!Context.IsWorldReady)
        {
            this.Monitor.Log("Load a save first.", LogLevel.Warn);
            return;
        }

        this.Monitor.Log(
            "===== CARDCHA UNIVERSAL ENEMY STATUS =====\n" +
            this.EnemyObserver.Describe() + "\n" +
            this.Deaths.Describe() + "\n" +
            this.Drops.Describe(),
            LogLevel.Alert
        );
    }

    private void CommandTestAttic(string command, string[] args)
    {
        if (!Context.IsWorldReady)
        {
            this.Monitor.Log("Load a save before using cardcha_test_attic.", LogLevel.Warn);
            return;
        }

        bool leaving = Game1.currentLocation?.NameOrUniqueName.Equals(
            MimiHomeService.AtticLocationName,
            StringComparison.OrdinalIgnoreCase
        ) == true;

        this.AtticVisual.SetTestAccess(!leaving);
        string result = this.Home.DebugToggleAtticAccess();
        this.Monitor.Log(result, LogLevel.Alert);
    }

    private void CommandVersion(string command, string[] args)
    {
        this.Monitor.Log(
            "Cardcha! v0.3.0-alpha.27.0.7.8.7 ATTIC ACCEPTANCE POLISH TEST",
            LogLevel.Alert
        );
    }

    private void CommandDropStatus(string command, string[] args)
    {
        if (!Context.IsWorldReady)
        {
            this.Monitor.Log("Load a save first.", LogLevel.Warn);
            return;
        }

        this.Monitor.Log(
            "===== CARDCHA DROP STATUS =====\n" +
            this.Deaths.Describe() + "\n" +
            this.Drops.Describe() + "\n" +
            $"EnableMonsterDrops={this.Config.EnableMonsterDrops} | Multiplier={this.Config.PrototypeDropMultiplier:0.##}",
            LogLevel.Alert
        );
    }

    private void CommandProgressionStatus(string command, string[] args)
    {
        if (!Context.IsWorldReady)
        {
            this.Monitor.Log("Load a save first.", LogLevel.Warn);
            return;
        }

        this.Monitor.Log(
            $"Normal gameplay: {this.Progression.DescribeState()}",
            LogLevel.Info
        );
    }

    private void CommandGiveScrap(string command, string[] args)
    {
        if (!Context.IsWorldReady)
            return;

        bool shiny = args.FirstOrDefault()?.Equals("shiny", StringComparison.OrdinalIgnoreCase) == true;
        int amount = args.Length >= 2 && int.TryParse(args[1], out int parsed) ? Math.Clamp(parsed, 1, 999) : 10;
        string id = shiny ? DropService.ShinyScrapId : DropService.CardboardScrapId;
        this.Resources.Add(id, amount);
        string destination = this.Resources.IsBinderWalletActive ? "Binder wallet" : "backpack";
        this.Monitor.Log($"Added {amount} {(shiny ? "Shiny " : "")}Cardboard Scrap to the {destination}.", LogLevel.Info);
    }

    private void CommandGiveMachine(string command, string[] args)
    {
        if (!Context.IsWorldReady)
            return;

        Item item = ItemRegistry.Create($"(BC){ItemAssetService.CardchaMachineId}");
        Item? leftover = Game1.player.addItemToInventory(item);
        if (leftover is not null)
            Game1.createItemDebris(leftover, Game1.player.Position, -1, Game1.currentLocation);

        this.Monitor.Log("Gave Cardcha! Machine. Please do not shake it.", LogLevel.Info);
    }

    private void CommandGivePortableMachine(string command, string[] args)
    {
        if (!Context.IsWorldReady)
            return;

        this.PortableMachine.GiveForDebug();
        this.Monitor.Log(
            "Gave Portable Cardcha Machine and marked the entitlement as acquired for this test save.",
            LogLevel.Info
        );
    }

    private void CommandOpenMachine(string command, string[] args)
        => this.OpenMachineMenu();

    private void CommandOpenPortableMachine(string command, string[] args)
        => this.OpenPortableMachineMenu();

    private void CommandOpenBinder(string command, string[] args)
        => this.OpenBinderMenu();

    internal static string T(string key)
        => StaticHelper?.Translation.Get(key).ToString() ?? key;

    internal static string T(string key, object tokens)
        => StaticHelper?.Translation.Get(key, tokens).ToString() ?? key;

    internal static void LogOnce(string key, string message)
    {
        if (!LoggedErrors.Add(key))
            return;

        StaticMonitor?.Log(message, LogLevel.Error);
    }
}
