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
    internal static ChaChaSkillService? StaticChaChaSkills;
    internal static ChaChaSupportCastService? StaticChaChaSupport;
    private static readonly HashSet<string> LoggedErrors = new(StringComparer.OrdinalIgnoreCase);

    private ModConfig Config = null!;
    private CardRegistry Cards = null!;
    private SaveService Save = null!;
    private GachaService Gacha = null!;
    private CardUpgradeService Upgrades = null!;
    private LoadoutService Loadout = null!;
    private ItemAssetService Items = null!;
    private ResourceService Resources = null!;
    private BossEnergyService BossEnergy = null!;
    private BossCardService BossCards = null!;
    private ChaChaBossFormService ChaChaBossForm = null!;
    private ChaChaSkillService ChaChaSkills = null!;
    private ChaChaSupportCastService ChaChaSupport = null!;
    private ChaChaSkillMaterialService ChaChaMaterials = null!;
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
    private AirshipFoundationService Airship = null!;
    private RegionExpeditionService RegionExpeditions = null!;
    private VerdantGuardianBossService VerdantGuardian = null!;
    private VerdantGuardianVisualService VerdantGuardianVisual = null!;
    private VerdantGuardianSummonVisualService VerdantSummons = null!;
    private VerdantGuardianArenaPolishService VerdantArenaPolish = null!;
    private MilestoneBossService MilestoneBosses = null!;
    private CardTestLabService CardLab = null!;
    private CardTestArenaService CardArena = null!;
    private CardTestLabOverlayService CardLabOverlay = null!;
    private CardAutoScenarioRunnerService CardAutoRunner = null!;

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
        this.BossEnergy = new BossEnergyService(this.Loadout, this.Cards, this.Upgrades);
        this.BossCards = new BossCardService(helper, this.Monitor, this.Save, this.Config);
        this.Combat = new CombatService(this.Config, this.Loadout, this.Save, this.Cards, this.Upgrades, this.BossEnergy);
        this.Renderer = new CardRenderer(helper);
        this.WorldActors = new WorldActorService(this.Monitor);
        this.ChaChaSkills = new ChaChaSkillService(helper, this.Monitor, this.Save, this.WorldActors);
        StaticChaChaSkills = this.ChaChaSkills;
        this.ChaChaBossForm = new ChaChaBossFormService(
            helper, this.Monitor, this.Save, this.BossEnergy, this.WorldActors, this.Controller
        );
        this.ChaChaSupport = new ChaChaSupportCastService(this.Monitor, this.Save, this.ChaChaSkills, () => this.ChaChaBossForm.IsActive);
        StaticChaChaSupport = this.ChaChaSupport;
        this.ChaChaMaterials = new ChaChaSkillMaterialService(helper, this.Monitor, this.Save, this.ChaChaSkills, this.Controller);
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
        this.Deaths = new MonsterDeathService(this.Drops, this.Combat, this.ChaChaMaterials, this.ChaChaSupport);
        this.EnemyObserver = new UniversalEnemyObserverService(this.Deaths);
        this.CombatHud = new CombatHudRenderer(
            this.Config,
            this.Combat,
            this.BossEnergy,
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
        this.Home = new MimiHomeService(
            helper,
            this.Monitor,
            this.Save,
            this.WorldActors,
            () => this.Story.OwnsMimiWorldActor,
            () => this.Mystery.OwnsMimiWorldActor,
            (npc, text) => this.Mystery.TryShowCrispPortraitDialogue(npc, text)
        );
        this.Social = new MimiSocialService(
            helper,
            this.Monitor,
            this.Save,
            this.WorldActors,
            this.OpenMimiShop,
            npc => this.Mystery.PrepareCrispPortrait(npc),
            () => this.Home.OwnsAnyAtticDialogueNow()
        );
        this.AtticVisual = new MimiAtticVisualService(helper, this.Save);
        this.Airship = new AirshipFoundationService(helper, this.Monitor, this.Save, this.Controller);
        this.RegionExpeditions = new RegionExpeditionService(helper, this.Monitor, this.Save, this.Airship);
        this.VerdantGuardian = new VerdantGuardianBossService(helper, this.Monitor, this.Save, this.PortableMachine);
        this.VerdantGuardianVisual = new VerdantGuardianVisualService(helper, this.Monitor, this.VerdantGuardian);
        this.VerdantSummons = new VerdantGuardianSummonVisualService(helper, this.Monitor, this.VerdantGuardian);
        this.VerdantArenaPolish = new VerdantGuardianArenaPolishService(helper, this.Monitor, this.VerdantGuardian);
        this.MilestoneBosses = new MilestoneBossService(helper, this.Monitor, this.Save);
        this.MilestoneBosses.BindExpeditionRouteHandler(this.RegionExpeditions.UseRouteConsole);
        this.Airship.BindMilestoneRouteHandler(this.MilestoneBosses.UseAirshipMilestoneRoute);
        this.CardLab = new CardTestLabService(this.Cards, this.Save, this.Combat);
        this.CardArena = new CardTestArenaService(helper, this.Monitor, this.CardLab);
        this.CardLabOverlay = new CardTestLabOverlayService(helper, this.CardLab, this.CardArena, this.OpenCardTestLab, this.EndCardTestLabSession);
        this.CardAutoRunner = new CardAutoScenarioRunnerService(
            this.Monitor, this.Config, this.Cards, this.Save, this.Upgrades, this.Combat, this.Drops, this.Gacha, this.BossEnergy
        );

        helper.Events.Content.AssetRequested += this.Items.OnAssetRequested;
        helper.Events.Content.AssetRequested += this.WorldActors.OnAssetRequested;
        helper.Events.Content.AssetRequested += this.Mystery.OnAssetRequested;
        helper.Events.Content.AssetRequested += this.Social.OnAssetRequested;
        helper.Events.Content.AssetRequested += this.AtticVisual.OnAssetRequested;
        helper.Events.Content.AssetRequested += this.Airship.OnAssetRequested;
        helper.Events.Content.AssetRequested += this.RegionExpeditions.OnAssetRequested;
        helper.Events.Content.AssetRequested += this.VerdantGuardian.OnAssetRequested;
        helper.Events.Content.AssetRequested += this.MilestoneBosses.OnAssetRequested;
        helper.Events.Content.AssetRequested += this.CardArena.OnAssetRequested;
        helper.Events.GameLoop.GameLaunched += this.OnGameLaunched;
        helper.Events.GameLoop.SaveLoaded += this.OnSaveLoaded;
        helper.Events.GameLoop.SaveLoaded += this.CardArena.OnSaveLoaded;
        helper.Events.GameLoop.SaveLoaded += this.BossCards.OnSaveLoaded;
        helper.Events.GameLoop.SaveLoaded += this.MilestoneBosses.OnSaveLoaded;
        helper.Events.GameLoop.SaveLoaded += this.RegionExpeditions.OnSaveLoaded;
        helper.Events.GameLoop.Saving += this.OnSaving;
        helper.Events.GameLoop.Saved += this.OnSaved;
        helper.Events.GameLoop.DayStarted += this.OnDayStarted;
        helper.Events.GameLoop.DayStarted += this.BossEnergy.OnDayStarted;
        helper.Events.GameLoop.DayStarted += this.BossCards.OnDayStarted;
        helper.Events.GameLoop.DayStarted += this.ChaChaBossForm.OnDayStarted;
        helper.Events.GameLoop.DayStarted += this.ChaChaSupport.OnDayStarted;
        helper.Events.GameLoop.DayStarted += this.VerdantGuardian.OnDayStarted;
        helper.Events.GameLoop.DayStarted += this.MilestoneBosses.OnDayStarted;
        helper.Events.GameLoop.DayStarted += this.RegionExpeditions.OnDayStarted;
        helper.Events.GameLoop.TimeChanged += this.Mystery.OnTimeChanged;
        helper.Events.GameLoop.UpdateTicked += this.OnUpdateTicked;
        helper.Events.GameLoop.UpdateTicked += this.CardArena.OnUpdateTicked;
        helper.Events.GameLoop.UpdateTicked += this.BossCards.OnUpdateTicked;
        helper.Events.GameLoop.UpdateTicked += this.VerdantGuardian.OnUpdateTicked;
        helper.Events.GameLoop.UpdateTicked += this.MilestoneBosses.OnUpdateTicked;
        helper.Events.GameLoop.UpdateTicked += this.RegionExpeditions.OnUpdateTicked;
        helper.Events.GameLoop.UpdateTicked += this.VerdantArenaPolish.OnUpdateTicked;
        helper.Events.GameLoop.UpdateTicked += this.ChaChaBossForm.OnUpdateTicked;
        helper.Events.GameLoop.ReturnedToTitle += this.OnReturnedToTitle;
        helper.Events.GameLoop.ReturnedToTitle += this.ChaChaSkills.OnReturnedToTitle;
        helper.Events.GameLoop.ReturnedToTitle += this.ChaChaSupport.OnReturnedToTitle;
        helper.Events.GameLoop.ReturnedToTitle += this.BossEnergy.OnReturnedToTitle;
        helper.Events.GameLoop.ReturnedToTitle += this.BossCards.OnReturnedToTitle;
        helper.Events.GameLoop.ReturnedToTitle += this.ChaChaBossForm.OnReturnedToTitle;
        helper.Events.GameLoop.ReturnedToTitle += this.CardArena.OnReturnedToTitle;
        helper.Events.GameLoop.ReturnedToTitle += this.VerdantGuardian.OnReturnedToTitle;
        helper.Events.GameLoop.ReturnedToTitle += this.VerdantGuardianVisual.OnReturnedToTitle;
        helper.Events.GameLoop.ReturnedToTitle += this.VerdantSummons.OnReturnedToTitle;
        helper.Events.GameLoop.ReturnedToTitle += this.VerdantArenaPolish.OnReturnedToTitle;
        helper.Events.GameLoop.ReturnedToTitle += this.MilestoneBosses.OnReturnedToTitle;
        helper.Events.GameLoop.ReturnedToTitle += this.RegionExpeditions.OnReturnedToTitle;
        helper.Events.Display.RenderedHud += this.OnRenderedHud;
        helper.Events.Display.RenderedHud += this.CardLabOverlay.OnRenderedHud;
        helper.Events.Display.RenderedHud += this.BossCards.OnRenderedHud;
        helper.Events.Display.RenderedHud += this.ChaChaBossForm.OnRenderedHud;
        helper.Events.Display.RenderedHud += this.ChaChaSupport.OnRenderedHud;
        helper.Events.Display.RenderedHud += this.VerdantGuardian.OnRenderedHud;
        helper.Events.Display.RenderedHud += this.VerdantArenaPolish.OnRenderedHud;
        helper.Events.Display.RenderedHud += this.MilestoneBosses.OnRenderedHud;
        helper.Events.Display.RenderedWorld += this.Story.OnRenderedWorld;
        helper.Events.Display.RenderedWorld += this.BossCards.OnRenderedWorld;
        helper.Events.Display.RenderedWorld += this.ChaChaSkills.OnRenderedWorld;
        helper.Events.Display.RenderedWorld += this.ChaChaSupport.OnRenderedWorld;
        helper.Events.Display.RenderedWorld += this.ChaChaMaterials.OnRenderedWorld;
        helper.Events.Display.RenderedWorld += this.ChaChaBossForm.OnRenderedWorld;
        helper.Events.Display.RenderedWorld += this.AtticVisual.OnRenderedWorld;
        helper.Events.Display.RenderedWorld += this.Airship.OnRenderedWorld;
        helper.Events.Display.RenderedWorld += this.VerdantArenaPolish.OnRenderedWorld;
        helper.Events.Display.RenderedWorld += this.VerdantGuardian.OnRenderedWorld;
        helper.Events.Display.RenderedWorld += this.VerdantGuardianVisual.OnRenderedWorld;
        helper.Events.Display.RenderedWorld += this.VerdantSummons.OnRenderedWorld;
        helper.Events.Display.RenderedWorld += this.MilestoneBosses.OnRenderedWorld;
        helper.Events.Display.RenderedWorld += this.RegionExpeditions.OnRenderedWorld;
        helper.Events.Display.MenuChanged += this.BookTab.OnMenuChanged;
        helper.Events.Display.RenderedActiveMenu += this.BookTab.OnRenderedActiveMenu;
        helper.Events.Input.ButtonPressed += this.Story.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.ChaChaSkills.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.ChaChaMaterials.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.BookTab.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.Social.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.Mystery.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.Home.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.AtticVisual.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.PortableMachine.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.Airship.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.VerdantGuardian.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.MilestoneBosses.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.RegionExpeditions.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.CardLabOverlay.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.ChaChaBossForm.OnButtonPressed;
        helper.Events.Player.Warped += this.Story.OnWarped;
        helper.Events.Player.Warped += this.ChaChaSkills.OnWarped;
        helper.Events.Player.Warped += this.Airship.OnWarped;
        helper.Events.Player.Warped += this.VerdantGuardian.OnWarped;
        helper.Events.Player.Warped += this.VerdantArenaPolish.OnWarped;
        helper.Events.Player.Warped += this.MilestoneBosses.OnWarped;
        helper.Events.Player.Warped += this.RegionExpeditions.OnWarped;
        helper.Events.Player.Warped += this.CardArena.OnWarped;
        helper.Events.World.ObjectListChanged += this.OnObjectListChanged;

        helper.ConsoleCommands.Add("cardcha_status", "Show Cardcha prototype state.", this.CommandStatus);
        helper.ConsoleCommands.Add("cardcha_pull", "Debug pull without resource cost: cardcha_pull [standard|premium] [count]", this.CommandPull);
        helper.ConsoleCommands.Add("cardcha_unlock", "Unlock cards for testing: cardcha_unlock <card-id|all>", this.CommandUnlock);
        helper.ConsoleCommands.Add("cardcha_equip", "Equip a prototype card by ID: cardcha_equip <card-id>", this.CommandEquip);
        helper.ConsoleCommands.Add("cardcha_unequip", "Unequip a prototype card by ID.", this.CommandUnequip);
        helper.ConsoleCommands.Add("cardcha_combat_status", "Show active Cardcha combat state.", this.CommandCombatStatus);
        helper.ConsoleCommands.Add("cardcha_hud_runtime_status", "Show timed Cardcha HUD proc state.", (_, _) => this.Monitor.Log(string.Join(" | ", this.Combat.CurrentTimedCardHudStates.Select(p => $"{p.CardId}:{p.RemainingSeconds:0.0}s")), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_give_scrap", "Give prototype Scrap: cardcha_give_scrap [normal|shiny] [amount]", this.CommandGiveScrap);
        helper.ConsoleCommands.Add("cardcha_give_dust", "TEST ONLY: give Magic Dust for Airship upgrade testing: cardcha_give_dust [amount]", this.CommandGiveDust);
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
        helper.ConsoleCommands.Add("cardcha_mimi_profile_status", "Show MiMi Gift Log/Profile scaling hook diagnostics.", (_, _) => this.Monitor.Log(MimiProfileMenuPatch.Describe(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_controller_status", "Show resolved Cardcha controller profile and mapping.", this.CommandControllerStatus);
        helper.ConsoleCommands.Add("cardcha_test_attic", "TEST ONLY: toggle direct MiMi attic access without changing friendship/story progression.", this.CommandTestAttic);
        helper.ConsoleCommands.Add("cardcha_test_mimi_routine", "TEST ONLY: force MiMi attic state: home|tv|late|auto.", this.CommandTestMimiRoutine);
        helper.ConsoleCommands.Add("cardcha_airship_status", "Show alpha.28 Airship foundation state.", this.CommandAirshipStatus);
        helper.ConsoleCommands.Add("cardcha_huntrun_status", "Show Region I Hunt Run 2.0 route/boon/checkpoint state.", (_, _) => this.Monitor.Log(this.Airship.DescribeHuntRun2(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_huntrun_daily", "Show today's Region I mutation, Elite affix and rare-room state.", (_, _) => this.Monitor.Log(this.Airship.DescribeHuntAdvanced(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_huntrun_clear", "TEST ONLY: clear the current Hunt Run 2.0 encounter.", (_, _) => this.Monitor.Log(this.Airship.DebugClearHuntRunNode(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_test_gate", "TEST ONLY: warp directly beside the Forest Arcane Gate with runtime-only access.", this.CommandTestGate);
        helper.ConsoleCommands.Add("cardcha_test_airship", "TEST ONLY: toggle direct Airship deck access without changing story progression.", this.CommandTestAirship);
        helper.ConsoleCommands.Add("cardcha_test_airship_flyby", "TEST ONLY: replay the pre-MiMi Farm Airship flyby without changing save progression.", this.CommandTestAirshipFlyby);
        helper.ConsoleCommands.Add("cardcha_test_boss1", "TEST ONLY: enter the Verdant Guardian arena without changing the 20-card gate.", (_, _) => this.Monitor.Log(this.VerdantGuardian.DebugEnterArena(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss1_status", "Show Verdant Guardian runtime/save state.", (_, _) => this.Monitor.Log(this.VerdantGuardian.Describe(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss1_visual_status", "Show Verdant Guardian visual animation state.", (_, _) => this.Monitor.Log(this.VerdantGuardianVisual.Describe() + "\n" + this.VerdantSummons.Describe(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss1_polish_status", "Show Verdant arena cinematic/camera/sound polish state.", (_, _) => this.Monitor.Log(this.VerdantArenaPolish.Describe(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss1_balance_status", "Show the 0665 Region I Boss balance profile.", (_, _) => this.Monitor.Log(this.VerdantGuardian.DescribeBalance() + "\n" + this.BossCards.Describe() + "\n" + this.ChaChaBossForm.Describe(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss1_totem_status", "Show destructible Verdant Seed Totem state.", (_, _) => this.Monitor.Log(this.VerdantGuardian.DescribeBalance(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss1_summons", "TEST ONLY: replace current Boss I adds with one custom summon wave.", (_, _) => this.Monitor.Log(this.VerdantGuardian.DebugSummonWave(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_test_boss2", "TEST ONLY: enter Boss II - The Hollow Curator (40-card milestone bypass).", (_, _) => this.Monitor.Log(this.MilestoneBosses.DebugEnterBoss(2), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_test_boss3", "TEST ONLY: enter Boss III - The Tricolor Resonance (60-card milestone bypass).", (_, _) => this.Monitor.Log(this.MilestoneBosses.DebugEnterBoss(3), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_test_boss4", "TEST ONLY: enter Boss IV - MiMi (80-card milestone bypass).", (_, _) => this.Monitor.Log(this.MilestoneBosses.DebugEnterBoss(4), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss_milestone_status", "Show Boss II/III/IV runtime and milestone reward state.", (_, _) => this.Monitor.Log(this.MilestoneBosses.Describe(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_milestone_route_status", "Show the real 40/60/80-card milestone route state.", (_, _) => this.Monitor.Log(this.MilestoneBosses.DescribeMilestoneRoute(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_expedition_status", "Show Region III/IV expedition runtime and route state.", (_, _) => this.Monitor.Log(this.RegionExpeditions.Describe(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_test_region3", "TEST ONLY: enter Region III Mirrorwild without changing progression.", (_, _) => this.Monitor.Log(this.RegionExpeditions.DebugEnter(3), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_test_region4", "TEST ONLY: enter Region IV Resonance Verge without changing progression.", (_, _) => this.Monitor.Log(this.RegionExpeditions.DebugEnter(4), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_expedition_clear", "TEST ONLY: clear current Region III/IV expedition wave.", (_, _) => this.Monitor.Log(this.RegionExpeditions.DebugClearWave(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss_card_status", "Show dedicated Boss Card slot/runtime state.", (_, _) => this.Monitor.Log(this.BossCards.Describe(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss_card_unlock", "TEST ONLY: unlock Verdant Core without changing Boss I clear state.", (_, _) => this.Monitor.Log(this.BossCards.DebugUnlock(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss_card_equip", "Equip a Boss Card: cardcha_boss_card_equip verdant_core|none", (_, args) => this.Monitor.Log(this.BossCards.DebugEquip(args.FirstOrDefault()), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss_card_trigger", "TEST ONLY: force Verdant Guard active for visual/gameplay verification.", (_, _) => this.Monitor.Log(this.BossCards.DebugTrigger(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss_form_charge", "TEST ONLY: add Boss Energy: cardcha_boss_form_charge [amount]", (_, args) =>
        {
            int amount = args.Length > 0 && int.TryParse(args[0], out int parsed) ? parsed : 100;
            this.Monitor.Log(this.ChaChaBossForm.DebugCharge(amount), LogLevel.Alert);
        });
        helper.ConsoleCommands.Add("cardcha_boss_form_trigger", "TEST ONLY: trigger the highest unlocked ChaCha Boss Form.", (_, _) => this.Monitor.Log(this.ChaChaBossForm.DebugTrigger(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss_form_status", "Show ChaCha Boss Form runtime state.", (_, _) => this.Monitor.Log(this.ChaChaBossForm.Describe(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_chacha_skills", "Show ChaCha normal-form exploration skill state.", (_, _) => this.Monitor.Log(this.ChaChaSkills.Describe(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_chacha_skill_unlock", "TEST ONLY: unlock a ChaCha exploration skill without changing region progression: cardcha_chacha_skill_unlock <vital|guard|spirit|luck>", (_, args) => this.Monitor.Log(this.ChaChaSkills.DebugUnlock(args.FirstOrDefault()), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_chacha_skill_equip", "Equip an unlocked ChaCha exploration skill: cardcha_chacha_skill_equip <vital|guard|spirit|luck|none>", (_, args) => this.Monitor.Log(this.ChaChaSkills.DebugEquip(args.FirstOrDefault()), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_chacha_skill_materials", "TEST ONLY: give ChaCha region materials: cardcha_chacha_skill_materials [amount]", (_, args) =>
        {
            int amount = args.Length > 0 && int.TryParse(args[0], out int parsed) ? parsed : 20;
            this.ChaChaMaterials.GiveAllForDebug(amount);
            this.Monitor.Log(this.ChaChaMaterials.Describe(), LogLevel.Alert);
        });
        helper.ConsoleCommands.Add("cardcha_chacha_station_status", "Show ChaCha Resonance Pedestal material and upgrade state.", (_, _) => this.Monitor.Log(this.ChaChaMaterials.Describe(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_test_cards", "Open the dedicated Card Test Lab (local only).", this.CommandTestCards);
        helper.ConsoleCommands.Add("cardcha_test_run", "Run automated Cardcha card scenarios: cardcha_test_run [batchA|batchB|all|report]", this.CommandTestRun);
        helper.ConsoleCommands.Add("cardcha_test_arena", "Enter the isolated Card Test Arena without touching story or world state.", this.CommandTestArena);
        helper.ConsoleCommands.Add("cardcha_test_arena_clear", "Remove all Card Test Arena enemies.", this.CommandTestArenaClear);
        helper.ConsoleCommands.Add("cardcha_test_arena_spawn", "Spawn Card Test Arena enemies: cardcha_test_arena_spawn [normal|elite|boss] [count]", this.CommandTestArenaSpawn);
        helper.ConsoleCommands.Add("cardcha_test_arena_exit", "Leave the Card Test Arena and restore the original player location.", this.CommandTestArenaExit);
    }

    private void OnGameLaunched(object? sender, GameLaunchedEventArgs e)
    {
        this.Cards.Load();
        this.RegisterConfigMenu();

        Harmony harmony = new(this.ModManifest.UniqueID);
        MonsterDropPatch.Apply(harmony, this.Deaths);
        MonsterDamagePatch.Apply(harmony, this.Combat, this.Deaths, this.CardArena, this.VerdantGuardian);
        VerdantGuardianProxyDrawPatch.Apply(harmony);
        RegionExpeditionProxyDrawPatch.Apply(harmony);
        CriticalChancePatch.Apply(harmony, this.Combat);
        FarmerDamagePatch.Apply(harmony, this.Combat, this.ChaChaSupport, this.CardArena, this.BossCards);
        MachineInteractionPatch.Apply(harmony, this.OpenMachineMenu);
        BookNavigationPatch.Apply(harmony, this.BookTab);
        MimiProfileMenuPatch.Apply(harmony);
        AirshipGateDepthPatch.Apply(harmony, this.Airship, this.Monitor);

        this.Monitor.Log(
            "Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.45.2 REGION LAYERING + MAP CLEANUP + GATE ALIGNMENT HOTFIX TEST",
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
        this.Airship.OnSaveLoaded();
        this.VerdantGuardian.OnSaveLoaded();
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
        this.VerdantGuardian.PrepareForSave();
        this.CardArena.PrepareForSave();
        this.CardLab.EndSession();
        this.Combat.PrepareForGameSave();
        this.ChaChaBossForm.OnSaving();
        // ChaCha is a runtime-only world actor; remove it before Stardew serializes locations.
        this.Story.OnSaving();
        this.Save.Save();
    }

    private void OnSaved(object? sender, SavedEventArgs e)
    {
        this.Combat.SyncPassiveBuffs();
    }

    private void OnDayStarted(object? sender, DayStartedEventArgs e)
    {
        this.Save.ResetForNewDay();
        this.Combat.ResetRuntime();
        this.Combat.ResetVerificationTelemetry();
        this.EnemyObserver.Reset();
        this.Combat.SyncPassiveBuffs();
        this.Progression.OnDayStarted();
        this.Airship.OnDayStarted();
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
        this.Airship.OnUpdateTicked(e);

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
        this.Airship.OnReturnedToTitle();
        this.NormalizeCardchaMachinePlacement();
        this.NormalizePortableMachinePlacement();
    }

    private void OnRenderedHud(object? sender, RenderedHudEventArgs e)
    {
        this.CombatHud.Draw(e.SpriteBatch);
    }

    private void OnObjectListChanged(object? sender, ObjectListChangedEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        this.Progression.OnObjectListChanged(e);
        this.NormalizeCardchaMachinePlacement();
        this.NormalizePortableMachinePlacement();
    }

    private static void TryLogOnce(IMonitor monitor, string key, string message, LogLevel level = LogLevel.Warn)
    {
        if (LoggedErrors.Add(key))
            monitor.Log(message, level);
    }

    private void NormalizeCardchaMachinePlacement()
    {
        if (!Context.IsWorldReady)
            return;

        try
        {
            foreach (GameLocation location in Game1.locations)
            {
                foreach ((Vector2 tile, StardewValley.Object obj) in location.Objects.Pairs.ToList())
                {
                    if (!this.Items.IsCardchaMachine(obj))
                        continue;

                    if (this.PortableMachine.IsPortableMachine(obj))
                    {
                        // Portable machines are inventory-only. Remove legacy placed instances and return
                        // one copy to the player when the save still owns the portable entitlement.
                        location.Objects.Remove(tile);
                        if (this.Save.Data.PortableMachinePurchased || this.Save.Data.PortableMachineGifted)
                            this.EnsurePortableMachineInInventory();
                        continue;
                    }

                    // Stationary Machine remains placeable indoors only.
                    if (location.IsOutdoors)
                    {
                        location.Objects.Remove(tile);
                        this.Items.EnsureMachineInInventory();
                    }
                }
            }
        }
        catch (Exception ex)
        {
            TryLogOnce(this.Monitor, "normalize-machine", $"Cardcha machine placement normalization failed safely: {ex.Message}");
        }
    }

    private void NormalizePortableMachinePlacement()
    {
        if (!Context.IsWorldReady)
            return;

        try
        {
            foreach (GameLocation location in Game1.locations)
            {
                foreach ((Vector2 tile, StardewValley.Object obj) in location.Objects.Pairs.ToList())
                {
                    if (!this.PortableMachine.IsPortableMachine(obj))
                        continue;

                    location.Objects.Remove(tile);
                }
            }

            if (this.Save.Data.PortableMachinePurchased || this.Save.Data.PortableMachineGifted)
                this.EnsurePortableMachineInInventory();
        }
        catch (Exception ex)
        {
            TryLogOnce(this.Monitor, "normalize-portable", $"Portable machine placement normalization failed safely: {ex.Message}");
        }
    }

    private void EnsurePortableMachineInInventory()
    {
        if (!Context.IsWorldReady)
            return;

        bool has = Game1.player.Items.Any(item => item is StardewValley.Object obj && this.PortableMachine.IsPortableMachine(obj));
        if (!has)
            Game1.player.addItemToInventory(this.PortableMachine.CreatePortableMachine());
    }

    private void OpenMachineMenu()
    {
        if (!Context.IsWorldReady)
            return;

        Game1.activeClickableMenu = new CardchaMachineMenu(
            this.Config,
            this.Save,
            this.Gacha,
            this.Cards,
            this.Upgrades,
            this.Resources,
            this.Loadout,
            this.PortableMachine,
            this.Controller,
            this.OpenBinderFromMachine,
            this.OpenBinderFromPortableMachine
        );
    }

    private void OpenPortableMachineMenu()
    {
        if (!Context.IsWorldReady)
            return;

        Game1.activeClickableMenu = new CardchaMachineMenu(
            this.Config,
            this.Save,
            this.Gacha,
            this.Cards,
            this.Upgrades,
            this.Resources,
            this.Loadout,
            this.PortableMachine,
            this.Controller,
            this.OpenBinderFromPortableMachine,
            this.OpenBinderFromPortableMachine
        );
    }

    private void OpenBinderFromMenu()
    {
        if (!Context.IsWorldReady)
            return;
        Game1.activeClickableMenu = new CardchaBinderMenu(
            this.Config,
            this.Save,
            this.Cards,
            this.Upgrades,
            this.Loadout,
            this.Gacha,
            this.Resources,
            this.BossCards,
            this.ChaChaBossForm,
            this.ChaChaSkills,
            this.Controller,
            onClose: null,
            openMachine: this.OpenMachineMenu,
            openPortableMachine: this.OpenPortableMachineMenu,
            context: BinderReturnContext.PlayerMenu,
            returnMenu: Game1.activeClickableMenu
        );
    }

    private void OpenBinderFromMachine()
    {
        if (!Context.IsWorldReady)
            return;
        Game1.activeClickableMenu = new CardchaBinderMenu(
            this.Config,
            this.Save,
            this.Cards,
            this.Upgrades,
            this.Loadout,
            this.Gacha,
            this.Resources,
            this.BossCards,
            this.ChaChaBossForm,
            this.ChaChaSkills,
            this.Controller,
            onClose: this.OpenMachineMenu,
            openMachine: this.OpenMachineMenu,
            openPortableMachine: this.OpenPortableMachineMenu,
            context: BinderReturnContext.CardchaMachine,
            returnMenu: null
        );
    }

    private void OpenBinderFromPortableMachine()
    {
        if (!Context.IsWorldReady)
            return;
        Game1.activeClickableMenu = new CardchaBinderMenu(
            this.Config,
            this.Save,
            this.Cards,
            this.Upgrades,
            this.Loadout,
            this.Gacha,
            this.Resources,
            this.BossCards,
            this.ChaChaBossForm,
            this.ChaChaSkills,
            this.Controller,
            onClose: this.OpenPortableMachineMenu,
            openMachine: this.OpenMachineMenu,
            openPortableMachine: this.OpenPortableMachineMenu,
            context: BinderReturnContext.PortableMachine,
            returnMenu: null
        );
    }

    private void CommandStatus(string command, string[] args)
    {
        if (!Context.IsWorldReady)
        {
            this.Monitor.Log("Load a save first.", LogLevel.Warn);
            return;
        }

        this.Monitor.Log(
            $"Cardcha | Schema={this.Save.Data.SchemaVersion} | Cards={this.Save.Data.OwnedCards.Count}/{this.Cards.All.Count} | Equipped={string.Join(',', this.Save.Data.EquippedCards)} | " +
            $"Scrap={this.Save.Data.CardboardScraps} | Shiny={this.Save.Data.ShinyScraps} | Dust={this.Save.Data.SuspiciousDust} | " +
            $"BinderUnlocked={this.Save.Data.BinderUnlocked} | MachineDelivered={this.Save.Data.MachineDelivered}",
            LogLevel.Alert
        );
    }

    private void CommandPull(string command, string[] args)
    {
        PullType type = args.FirstOrDefault()?.Equals("premium", StringComparison.OrdinalIgnoreCase) == true
            ? PullType.Premium
            : PullType.Standard;
        int count = 1;
        if (args.Length > 1 && int.TryParse(args[1], out int parsed))
            count = Math.Clamp(parsed, 1, 100);

        for (int i = 0; i < count; i++)
        {
            PullResult pull = this.Gacha.Pull(type, free: true);
            this.Monitor.Log($"{pull.Card.Name} [{pull.Card.Rarity}] duplicate={pull.IsDuplicate} dust={pull.DustGranted}", LogLevel.Info);
        }
    }

    private void CommandUnlock(string command, string[] args)
    {
        if (!Context.IsWorldReady)
        {
            this.Monitor.Log("Load a save first.", LogLevel.Warn);
            return;
        }

        string target = args.FirstOrDefault() ?? "";
        if (target.Equals("all", StringComparison.OrdinalIgnoreCase))
        {
            this.Save.Data.OwnedCards = this.Cards.All.Select(card => card.Id).ToHashSet(StringComparer.OrdinalIgnoreCase);
            foreach (CardDefinition card in this.Cards.All)
                this.Save.Data.CardLevels[card.Id] = Math.Max(1, this.Save.Data.CardLevels.GetValueOrDefault(card.Id));
            this.Save.Save();
            this.Monitor.Log($"Unlocked all {this.Cards.All.Count} cards.", LogLevel.Alert);
            return;
        }

        CardDefinition? card = this.Cards.Get(target);
        if (card is null)
        {
            this.Monitor.Log($"Unknown card '{target}'.", LogLevel.Warn);
            return;
        }

        this.Save.Data.OwnedCards.Add(card.Id);
        this.Save.Data.CardLevels[card.Id] = Math.Max(1, this.Save.Data.CardLevels.GetValueOrDefault(card.Id));
        this.Save.Save();
        this.Monitor.Log($"Unlocked {card.Name} ({card.Id}).", LogLevel.Alert);
    }

    private void CommandEquip(string command, string[] args)
    {
        string target = args.FirstOrDefault() ?? "";
        if (!this.Loadout.TryEquip(target))
        {
            this.Monitor.Log($"Couldn't equip '{target}'.", LogLevel.Warn);
            return;
        }
        this.Save.Save();
        this.Combat.SyncPassiveBuffs();
        this.Monitor.Log($"Equipped {target}.", LogLevel.Alert);
    }

    private void CommandUnequip(string command, string[] args)
    {
        string target = args.FirstOrDefault() ?? "";
        if (!this.Loadout.TryUnequip(target))
        {
            this.Monitor.Log($"Couldn't unequip '{target}'.", LogLevel.Warn);
            return;
        }
        this.Save.Save();
        this.Combat.SyncPassiveBuffs();
        this.Monitor.Log($"Unequipped {target}.", LogLevel.Alert);
    }

    private void CommandCombatStatus(string command, string[] args)
    {
        this.Monitor.Log(this.Combat.DescribeState(), LogLevel.Alert);
    }

    private void CommandGiveScrap(string command, string[] args)
    {
        if (!Context.IsWorldReady)
            return;
        string kind = args.FirstOrDefault() ?? "normal";
        int amount = args.Length > 1 && int.TryParse(args[1], out int parsed) ? Math.Max(1, parsed) : 10;
        if (kind.Equals("shiny", StringComparison.OrdinalIgnoreCase))
            this.Resources.AddShiny(amount);
        else
            this.Resources.AddNormal(amount);
        this.Save.Save();
        this.Monitor.Log($"Scrap now: normal={this.Resources.GetNormalCount()} shiny={this.Resources.GetShinyCount()}", LogLevel.Alert);
    }

    private void CommandGiveDust(string command, string[] args)
    {
        if (!Context.IsWorldReady)
            return;
        int amount = args.Length > 0 && int.TryParse(args[0], out int parsed) ? Math.Max(1, parsed) : 25;
        this.Save.Data.SuspiciousDust += amount;
        this.Save.Save();
        this.Monitor.Log($"Magic Dust now {this.Save.Data.SuspiciousDust} (+{amount}).", LogLevel.Alert);
    }

    private void CommandGiveMachine(string command, string[] args)
    {
        this.Items.EnsureMachineInInventory();
        this.Monitor.Log("Cardcha Machine ensured in inventory.", LogLevel.Alert);
    }

    private void CommandGivePortableMachine(string command, string[] args)
    {
        if (!Context.IsWorldReady)
            return;
        this.Save.Data.PortableMachineGifted = true;
        this.EnsurePortableMachineInInventory();
        this.Save.Save();
        this.Monitor.Log("Portable Cardcha Machine entitlement enabled and item ensured in inventory.", LogLevel.Alert);
    }

    private void CommandOpenMachine(string command, string[] args)
    {
        this.OpenMachineMenu();
    }

    private void CommandOpenPortableMachine(string command, string[] args)
    {
        this.OpenPortableMachineMenu();
    }

    private void CommandOpenBinder(string command, string[] args)
    {
        this.OpenBinderFromMenu();
    }

    private void CommandTestReport(string command, string[] args)
    {
        this.Monitor.Log(this.Combat.GetVerificationReport(), LogLevel.Alert);
    }

    private void CommandTestReset(string command, string[] args)
    {
        this.Combat.ResetVerificationTelemetry();
        this.Monitor.Log("Cardcha combat verification telemetry reset.", LogLevel.Alert);
    }

    private void CommandPersistenceStatus(string command, string[] args)
    {
        this.Monitor.Log(this.Save.LastPersistenceMessage, this.Save.LastPersistenceCheckPassed ? LogLevel.Alert : LogLevel.Warn);
    }

    private void CommandProgressionStatus(string command, string[] args)
    {
        this.Monitor.Log(this.Progression.Describe(), LogLevel.Alert);
    }

    private void CommandDropStatus(string command, string[] args)
    {
        this.Monitor.Log(this.EnemyObserver.Describe(), LogLevel.Alert);
    }

    private void CommandVersion(string command, string[] args)
    {
        this.Monitor.Log($"Cardcha version: {this.ModManifest.Version}", LogLevel.Alert);
    }

    private void CommandEnemyStatus(string command, string[] args)
    {
        this.Monitor.Log(this.EnemyObserver.Describe(), LogLevel.Alert);
    }

    private void CommandMachineStatus(string command, string[] args)
    {
        int inventory = Game1.player.Items.Count(item => item is StardewValley.Object obj && this.Items.IsCardchaMachine(obj));
        int world = Game1.locations.Sum(location => location.Objects.Pairs.Count(pair => this.Items.IsCardchaMachine(pair.Value)));
        this.Monitor.Log($"Cardcha Machine inventory={inventory} world={world}.", LogLevel.Alert);
    }

    private void CommandPortableStatus(string command, string[] args)
    {
        this.Monitor.Log(this.PortableMachine.Describe(), LogLevel.Alert);
    }

    private void CommandLootRates(string command, string[] args)
    {
        this.Monitor.Log(this.Drops.DescribeRates(), LogLevel.Alert);
    }

    private void CommandHudToggle(string command, string[] args)
    {
        this.Config.EnableCombatHud = !this.Config.EnableCombatHud;
        this.Helper.WriteConfig(this.Config);
        this.Monitor.Log(this.Config.EnableCombatHud ? T("hud.toggle.on") : T("hud.toggle.off"), LogLevel.Alert);
    }

    private void CommandBookStatus(string command, string[] args)
    {
        this.Monitor.Log(this.BookTab.Describe(), LogLevel.Alert);
    }

    private void CommandStoryStatus(string command, string[] args)
    {
        this.Monitor.Log(this.Story.Describe(), LogLevel.Alert);
    }

    private void CommandControllerStatus(string command, string[] args)
    {
        this.Monitor.Log(this.Controller.Describe(), LogLevel.Alert);
    }

    private void CommandTestAttic(string command, string[] args)
    {
        this.Monitor.Log(this.Home.DebugToggleDirectAccess(), LogLevel.Alert);
    }

    private void CommandTestMimiRoutine(string command, string[] args)
    {
        this.Monitor.Log(this.Home.DebugForceRoutine(args.FirstOrDefault()), LogLevel.Alert);
    }

    private void CommandAirshipStatus(string command, string[] args)
    {
        this.Monitor.Log(this.Airship.Describe(), LogLevel.Alert);
    }

    private void CommandTestGate(string command, string[] args)
    {
        this.Monitor.Log(this.Airship.DebugToggleGateAccess(), LogLevel.Alert);
    }

    private void CommandTestAirship(string command, string[] args)
    {
        this.Monitor.Log(this.Airship.DebugToggleDirectAirship(), LogLevel.Alert);
    }

    private void CommandTestAirshipFlyby(string command, string[] args)
    {
        this.Monitor.Log(this.Airship.DebugReplayFlyby(), LogLevel.Alert);
    }

    private void CommandTestCards(string command, string[] args)
    {
        if (!Context.IsWorldReady)
        {
            this.Monitor.Log("Load a save first.", LogLevel.Warn);
            return;
        }

        Game1.activeClickableMenu = new CardTestLabMenu(
            this.Cards,
            this.Save,
            this.Upgrades,
            this.Loadout,
            this.Gacha,
            this.Resources,
            this.Combat,
            this.Drops,
            this.BossEnergy,
            this.CardLab,
            this.CardArena,
            this.Controller
        );
    }

    private void CommandTestRun(string command, string[] args)
    {
        string mode = args.FirstOrDefault()?.Trim().ToLowerInvariant() ?? "all";
        this.CardAutoRunner.Run(mode);
    }

    private void CommandTestArena(string command, string[] args)
    {
        if (!Context.IsWorldReady)
        {
            this.Monitor.Log("Load a save first.", LogLevel.Warn);
            return;
        }
        this.Monitor.Log(this.CardArena.Enter(), LogLevel.Alert);
    }

    private void CommandTestArenaClear(string command, string[] args)
    {
        this.Monitor.Log(this.CardArena.Clear(), LogLevel.Alert);
    }

    private void CommandTestArenaSpawn(string command, string[] args)
    {
        string kind = args.FirstOrDefault() ?? "normal";
        int count = args.Length > 1 && int.TryParse(args[1], out int parsed) ? parsed : 1;
        this.Monitor.Log(this.CardArena.Spawn(kind, count), LogLevel.Alert);
    }

    private void CommandTestArenaExit(string command, string[] args)
    {
        this.Monitor.Log(this.CardArena.Exit(), LogLevel.Alert);
    }

    private void OpenCardTestLab()
    {
        if (!Context.IsWorldReady)
            return;
        Game1.activeClickableMenu = new CardTestLabMenu(
            this.Cards,
            this.Save,
            this.Upgrades,
            this.Loadout,
            this.Gacha,
            this.Resources,
            this.Combat,
            this.Drops,
            this.BossEnergy,
            this.CardLab,
            this.CardArena,
            this.Controller
        );
    }

    private void EndCardTestLabSession()
    {
        this.CardLab.EndSession();
    }

    public static string T(string key, object? tokens = null)
    {
        if (StaticHelper is null)
            return key;
        return tokens is null
            ? StaticHelper.Translation.Get(key)
            : StaticHelper.Translation.Get(key, tokens);
    }
}
