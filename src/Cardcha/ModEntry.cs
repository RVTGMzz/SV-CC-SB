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
    private Region2RoguelikeRunService Region2Rogue = null!;
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
        this.Region2Rogue = new Region2RoguelikeRunService(helper, this.Monitor, this.Save, this.Airship, this.RegionExpeditions);
        this.VerdantGuardian = new VerdantGuardianBossService(helper, this.Monitor, this.Save, this.PortableMachine);
        this.VerdantGuardianVisual = new VerdantGuardianVisualService(helper, this.Monitor, this.VerdantGuardian);
        this.VerdantSummons = new VerdantGuardianSummonVisualService(helper, this.Monitor, this.VerdantGuardian);
        this.VerdantArenaPolish = new VerdantGuardianArenaPolishService(helper, this.Monitor, this.VerdantGuardian);
        this.MilestoneBosses = new MilestoneBossService(helper, this.Monitor, this.Save);
        this.MilestoneBosses.BindExpeditionRouteHandler(this.RegionExpeditions.UseRouteConsole);
        this.RegionExpeditions.BindRegion2BossGateHandler(this.MilestoneBosses.EnterBoss2FromRegion2);
        this.RegionExpeditions.BindRegion2BossGateDebugHandler(() => this.MilestoneBosses.DebugEnterBoss(2));
        this.Region2Rogue.BindBossGateHandlers(this.MilestoneBosses.EnterBoss2FromRegion2, () => this.MilestoneBosses.DebugEnterBoss(2));
        this.Region2Rogue.BindCuratorRecordSink(this.MilestoneBosses.SetNextHollowCuratorRecord);
        this.Region2Rogue.BindCuratorArchiveRuleSink(this.MilestoneBosses.SetNextHollowCuratorArchiveRule);
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
        helper.Events.Content.AssetRequested += this.Region2Rogue.OnAssetRequested;
        helper.Events.Content.AssetRequested += this.VerdantGuardian.OnAssetRequested;
        helper.Events.Content.AssetRequested += this.MilestoneBosses.OnAssetRequested;
        helper.Events.Content.AssetRequested += this.CardArena.OnAssetRequested;
        helper.Events.GameLoop.GameLaunched += this.OnGameLaunched;
        helper.Events.GameLoop.SaveLoaded += this.OnSaveLoaded;
        helper.Events.GameLoop.SaveLoaded += this.CardArena.OnSaveLoaded;
        helper.Events.GameLoop.SaveLoaded += this.BossCards.OnSaveLoaded;
        helper.Events.GameLoop.SaveLoaded += this.MilestoneBosses.OnSaveLoaded;
        helper.Events.GameLoop.SaveLoaded += this.RegionExpeditions.OnSaveLoaded;
        helper.Events.GameLoop.SaveLoaded += this.Region2Rogue.OnSaveLoaded;
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
        helper.Events.GameLoop.DayStarted += this.Region2Rogue.OnDayStarted;
        helper.Events.GameLoop.TimeChanged += this.Mystery.OnTimeChanged;
        helper.Events.GameLoop.UpdateTicked += this.OnUpdateTicked;
        helper.Events.GameLoop.UpdateTicked += this.CardArena.OnUpdateTicked;
        helper.Events.GameLoop.UpdateTicked += this.BossCards.OnUpdateTicked;
        helper.Events.GameLoop.UpdateTicked += this.VerdantGuardian.OnUpdateTicked;
        helper.Events.GameLoop.UpdateTicked += this.MilestoneBosses.OnUpdateTicked;
        helper.Events.GameLoop.UpdateTicked += this.RegionExpeditions.OnUpdateTicked;
        helper.Events.GameLoop.UpdateTicked += this.Region2Rogue.OnUpdateTicked;
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
        helper.Events.GameLoop.ReturnedToTitle += this.Region2Rogue.OnReturnedToTitle;
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
        helper.Events.Display.RenderedWorld += this.Region2Rogue.OnRenderedWorld;
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
        helper.Events.Input.ButtonPressed += this.Region2Rogue.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.CardLabOverlay.OnButtonPressed;
        helper.Events.Input.ButtonPressed += this.ChaChaBossForm.OnButtonPressed;
        helper.Events.Player.Warped += this.Story.OnWarped;
        helper.Events.Player.Warped += this.ChaChaSkills.OnWarped;
        helper.Events.Player.Warped += this.Airship.OnWarped;
        helper.Events.Player.Warped += this.VerdantGuardian.OnWarped;
        helper.Events.Player.Warped += this.VerdantArenaPolish.OnWarped;
        helper.Events.Player.Warped += this.MilestoneBosses.OnWarped;
        helper.Events.Player.Warped += this.RegionExpeditions.OnWarped;
        helper.Events.Player.Warped += this.Region2Rogue.OnWarped;
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
        helper.ConsoleCommands.Add("cardcha_test_boss2_record", "TEST ONLY: enter Boss II with a Curator record: risk|precision|pressure|recovery|mirror|neutral.", (_, args) => this.Monitor.Log(this.MilestoneBosses.DebugEnterBoss2WithRecord(args.FirstOrDefault()), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_test_boss3", "TEST ONLY: enter Boss III - The Tricolor Resonance (60-card milestone bypass).", (_, _) => this.Monitor.Log(this.MilestoneBosses.DebugEnterBoss(3), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_test_boss4", "TEST ONLY: enter Boss IV - MiMi (80-card milestone bypass).", (_, _) => this.Monitor.Log(this.MilestoneBosses.DebugEnterBoss(4), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss_milestone_status", "Show Boss II/III/IV runtime and milestone reward state.", (_, _) => this.Monitor.Log(this.MilestoneBosses.Describe(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_milestone_route_status", "Show the real 40/60/80-card milestone route state.", (_, _) => this.Monitor.Log(this.MilestoneBosses.DescribeMilestoneRoute(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_expedition_status", "Show Region II roguelike + Region III/IV expedition runtime and route state.", (_, _) => this.Monitor.Log(this.Region2Rogue.Describe() + "\n" + this.RegionExpeditions.Describe(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_region2_rogue_status", "Show Region II 6-9 node route, risk/reward and Curator observation state.", (_, _) => this.Monitor.Log(this.Region2Rogue.Describe(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_region2_mechanic_status", "Show active Region II room-specific combat mechanic and telegraph state.", (_, _) => this.Monitor.Log(this.Region2Rogue.DescribeRoomMechanic(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_test_region2", "TEST ONLY: enter Region II Forgotten Archive as a normal 6-9 node roguelike run.", (_, _) =>
        {
            this.Region2Rogue.PrepareNormalDebugEntry();
            this.Monitor.Log(this.RegionExpeditions.DebugEnter(2), LogLevel.Alert);
        });
        helper.ConsoleCommands.Add("cardcha_test_region2_bossgate", "TEST ONLY: enter Region II at a node-6-ready Archive Seal without changing save progression.", (_, _) =>
        {
            this.Region2Rogue.PrepareBossGateDebugEntry();
            this.Monitor.Log(this.RegionExpeditions.DebugEnter(2), LogLevel.Alert);
        });
        helper.ConsoleCommands.Add("cardcha_test_region3", "TEST ONLY: enter Region III Mirrorwild without changing progression.", (_, _) => this.Monitor.Log(this.RegionExpeditions.DebugEnter(3), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_test_region4", "TEST ONLY: enter Region IV Resonance Verge without changing progression.", (_, _) => this.Monitor.Log(this.RegionExpeditions.DebugEnter(4), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_expedition_clear", "TEST ONLY: clear/resolve current Region II node or Region III/IV expedition wave.", (_, _) => this.Monitor.Log(this.Region2Rogue.IsActive ? this.Region2Rogue.DebugClearCurrentNode() : this.RegionExpeditions.DebugClearWave(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss_card_status", "Show dedicated Boss Card slot/runtime state.", (_, _) => this.Monitor.Log(this.BossCards.Describe(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss_card_unlock", "TEST ONLY: unlock Verdant Core without changing Boss I clear state.", (_, _) => this.Monitor.Log(this.BossCards.DebugUnlock(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss_card_equip", "Equip a Boss Card: cardcha_boss_card_equip verdant_core|none", (_, args) => this.Monitor.Log(this.BossCards.DebugEquip(args.FirstOrDefault()), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_boss_card_trigger", "TEST ONLY: force Verdant Guard active for visual/gameplay verification.", (_, _) => this.Monitor.Log(this.BossCards.DebugTrigger(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_card_test", "TEST ONLY: open the visual 76-card Card Test Lab.", this.CommandCardTest);
        helper.ConsoleCommands.Add("cardcha_card_test_stop", "TEST ONLY: stop Card Test Lab, exit arena, and restore the real loadout.", this.CommandCardTestStop);
        helper.ConsoleCommands.Add("cardcha_card_auto_run", "TEST ONLY: run deterministic runtime scenarios for all 76 active cards.", this.CommandCardAutoRun);
        helper.ConsoleCommands.Add("cardcha_chacha_boss_ready", "TEST ONLY: fill Boss Energy to 100 so the ChaCha activation UI can be tested.", this.CommandChaChaBossReady);
        helper.ConsoleCommands.Add("cardcha_chacha_boss_status", "Show ChaCha Boss Form runtime state.", this.CommandChaChaBossStatus);
        helper.ConsoleCommands.Add("cardcha_guardian_rabbit_test", "TEST ONLY: runtime-unlock and immediately activate Guardian Rabbit for 10 seconds.", (_, _) => this.Monitor.Log(this.ChaChaBossForm.DebugForceGuardianRabbit() ? "TEST: Guardian Rabbit activated for 10 seconds." : "TEST: Guardian Rabbit could not activate in the current game state.", LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_chacha_skill_unlock", "TEST ONLY: discover the Region I ChaCha skill.", this.CommandChaChaSkillUnlock);
        helper.ConsoleCommands.Add("cardcha_chacha_skill_level", "TEST ONLY: set the Region I ChaCha skill level 1-5 without spending Magic Dust.", this.CommandChaChaSkillLevel);
        helper.ConsoleCommands.Add("cardcha_chacha_skill_cast", "TEST ONLY: replay the normal-form ChaCha skill cast visual.", this.CommandChaChaSkillCast);
        helper.ConsoleCommands.Add("cardcha_chacha_skill_status", "Show persistent ChaCha normal-form skill state.", this.CommandChaChaSkillStatus);
        helper.ConsoleCommands.Add("cardcha_chacha_materials", "TEST ONLY: give all four ChaCha region upgrade materials: cardcha_chacha_materials [amount]", this.CommandChaChaMaterials);
        helper.ConsoleCommands.Add("cardcha_chacha_station", "TEST ONLY: open the Airship ChaCha Resonance Pedestal UI directly.", this.CommandChaChaStation);
        helper.ConsoleCommands.Add("cardcha_chacha_material_status", "Show ChaCha region-material and Airship station state.", this.CommandChaChaMaterialStatus);
        helper.ConsoleCommands.Add("cardcha_chacha_support_status", "Show ChaCha one-cast support runtime state.", (_, _) => this.Monitor.Log("===== CHACHA SUPPORT CAST =====\n" + this.ChaChaSupport.Describe(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_chacha_support_force", "TEST ONLY: force one ChaCha Support Cast, bypassing cooldown.", (_, args) =>
        {
            if (!Context.IsWorldReady) return;
            bool ok = this.ChaChaSupport.DebugForceCast(args.FirstOrDefault() ?? "debug");
            this.Monitor.Log(ok ? "TEST: ChaCha Support Cast forced." : "TEST: Support Cast unavailable (unlock Vital/ChaCha or leave Boss Form).", ok ? LogLevel.Alert : LogLevel.Warn);
        });
    }

    private void OnGameLaunched(object? sender, GameLaunchedEventArgs e)
    {
        this.Cards.Load();
        this.RegisterConfigMenu();

        Harmony harmony = new(this.ModManifest.UniqueID);
        MonsterDropPatch.Apply(harmony, this.Deaths);
        MonsterDamagePatch.Apply(harmony, this.Combat, this.Deaths, this.CardArena, this.VerdantGuardian);
        VerdantGuardianProxyDrawPatch.Apply(harmony);
        MilestoneBossActorDrawPatch.Apply(harmony, this.MilestoneBosses, this.Monitor);
        RegionExpeditionProxyDrawPatch.Apply(harmony);
        CriticalChancePatch.Apply(harmony, this.Combat);
        FarmerDamagePatch.Apply(harmony, this.Combat, this.ChaChaSupport, this.CardArena, this.BossCards);
        MachineInteractionPatch.Apply(harmony, this.OpenMachineMenu);
        BookNavigationPatch.Apply(harmony, this.BookTab);
        MimiProfileMenuPatch.Apply(harmony);
        AirshipGateDepthPatch.Apply(harmony, this.Airship, this.Monitor);
        WorldPhysicalOverlaySafetyPatch.Apply(harmony, this.Monitor);

        this.Monitor.Log(
            "Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.55 0686 HOLLOW CURATOR ARCHIVE RULE ADAPTATION TEST",
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
        this.CardLab.EndSession();
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
            this.PortableMachine.Describe() + "\n" +
            this.Airship.Describe(),
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

    private void CommandTestMimiRoutine(string command, string[] args)
    {
        string mode = args.FirstOrDefault() ?? "auto";
        this.Monitor.Log(this.Home.DebugForceRoutine(mode), LogLevel.Alert);
    }

    private void CommandAirshipStatus(string command, string[] args)
    {
        this.Monitor.Log("===== CARDCHA AIRSHIP STATUS =====\n" + this.Airship.Describe(), LogLevel.Alert);
    }

    private void CommandTestGate(string command, string[] args)
    {
        this.Monitor.Log(this.Airship.DebugWarpToGate(), LogLevel.Alert);
    }

    private void CommandTestAirship(string command, string[] args)
    {
        this.Monitor.Log(this.Airship.DebugToggleDeck(), LogLevel.Alert);
    }

    private void CommandTestAirshipFlyby(string command, string[] args)
    {
        this.Monitor.Log(this.Airship.DebugReplayFlyby(), LogLevel.Alert);
    }

    private void CommandCardTest(string command, string[] args)
    {
        if (!Context.IsWorldReady)
        {
            this.Monitor.Log("Load a save before opening Card Test Lab.", LogLevel.Warn);
            return;
        }

        if (Game1.activeClickableMenu is not null)
        {
            this.Monitor.Log("Close the current menu first, then run cardcha_card_test again.", LogLevel.Warn);
            return;
        }

        this.OpenCardTestLab();
        this.Monitor.Log("Card Test Lab opened. Minimize once, then reopen from CARD LAB tab / F8 / controller right-stick. Arena stays active until END LAB or cardcha_card_test_stop.", LogLevel.Alert);
    }

    private void OpenCardTestLab()
    {
        if (!Context.IsWorldReady || Game1.activeClickableMenu is not null)
            return;
        Game1.activeClickableMenu = new CardTestLabMenu(this.CardLab, this.Renderer, this.CardArena, this.CardAutoRunner);
    }

    private void EndCardTestLabSession()
    {
        this.CardArena.ExitArena();
        this.CardLab.EndSession();
        if (Game1.activeClickableMenu is CardTestLabMenu)
            Game1.exitActiveMenu();
    }

    private void CommandCardTestStop(string command, string[] args)
    {
        if (!Context.IsWorldReady)
            return;
        this.EndCardTestLabSession();
        this.Monitor.Log("Card Test Lab stopped. Arena exited and the real loadout was restored.", LogLevel.Alert);
    }

    private void CommandCardAutoRun(string command, string[] args)
    {
        if (!Context.IsWorldReady)
        {
            this.Monitor.Log("Load a save before running Card Auto Scenario Runner.", LogLevel.Warn);
            return;
        }

        CardScenarioCounts counts = this.CardAutoRunner.RunAll();
        this.Monitor.Log(
            $"===== CARD AUTO SCENARIO RUNNER =====\nPASS {counts.Pass} | FAIL {counts.Fail} | BLOCKED {counts.Blocked} | ERROR {counts.Error} | NOT RUN {counts.NotRun}",
            counts.Fail > 0 || counts.Error > 0 ? LogLevel.Warn : LogLevel.Alert
        );
    }

    private void CommandChaChaBossReady(string command, string[] args)
    {
        if (!Context.IsWorldReady)
        {
            this.Monitor.Log("Load a save before priming ChaCha Boss Form.", LogLevel.Warn);
            return;
        }

        this.ChaChaBossForm.DebugPrimeReady();
        this.Monitor.Log("Guardian Rabbit TEST primed to 100 ChaCha Energy with a runtime-only unlock. Use controller Confirm+Deselect (Switch B+Y) or Left Shift+A.", LogLevel.Alert);
    }

    private void CommandChaChaBossStatus(string command, string[] args)
    {
        this.Monitor.Log("===== CHACHA BOSS FORM =====\n" + this.ChaChaBossForm.Describe(), LogLevel.Alert);
    }

    private void CommandChaChaSkillUnlock(string command, string[] args)
    {
        if (!Context.IsWorldReady)
        {
            this.Monitor.Log("Load a save before testing ChaCha skills.", LogLevel.Warn);
            return;
        }
        if (!this.Save.Data.ChaChaLoaned)
        {
            this.Monitor.Log("ChaCha has not joined the player yet; normal-form skills stay story-gated.", LogLevel.Warn);
            return;
        }

        string arg = args.FirstOrDefault()?.Trim().ToLowerInvariant() ?? "vital";
        IEnumerable<string> ids = arg == "all"
            ? ChaChaSkillService.SkillIds
            : new[]
            {
                arg switch
                {
                    "guard" or "aegis" or "bunny_aegis" => ChaChaSkillService.GuardSkillId,
                    "spirit" or "spirit_aid" => ChaChaSkillService.SpiritSkillId,
                    "luck" or "lucky" or "lucky_echo" => ChaChaSkillService.LuckSkillId,
                    _ => ChaChaSkillService.VitalSkillId
                }
            };

        int fresh = 0;
        foreach (string id in ids)
            if (this.ChaChaSkills.DebugDiscoverSkill(id, showPresentation: false))
                fresh++;
        this.ChaChaSkills.TriggerCastPresentation();
        this.Monitor.Log($"TEST: discovered {fresh} new ChaCha skill(s). Found=[{string.Join(",", this.Save.Data.ChaChaSkillsFound)}]", LogLevel.Alert);
    }

    private void CommandChaChaSkillLevel(string command, string[] args)
    {
        if (!Context.IsWorldReady)
            return;

        int level = args.Length > 0 && int.TryParse(args[0], out int parsed)
            ? Math.Clamp(parsed, 1, ChaChaSkillService.MaxSkillLevel)
            : 1;
        string selector = args.Length > 1 ? args[1].Trim().ToLowerInvariant() : "vital";
        string skillId = selector switch
        {
            "guard" or "aegis" => ChaChaSkillService.GuardSkillId,
            "spirit" => ChaChaSkillService.SpiritSkillId,
            "luck" or "lucky" => ChaChaSkillService.LuckSkillId,
            _ => ChaChaSkillService.VitalSkillId
        };

        if (!this.ChaChaSkills.DebugSetLevel(skillId, level))
        {
            this.Monitor.Log("Discover that ChaCha skill first. Use cardcha_chacha_skill_unlock <vital|guard|spirit|luck|all> for TEST.", LogLevel.Warn);
            return;
        }
        this.Monitor.Log($"TEST: {skillId} set to Lv {level}/{ChaChaSkillService.MaxSkillLevel}. No materials or Magic Dust were spent.", LogLevel.Alert);
    }

    private void CommandChaChaSkillCast(string command, string[] args)
    {
        if (!Context.IsWorldReady || !this.Save.Data.ChaChaLoaned)
            return;
        this.ChaChaSkills.TriggerCastPresentation();
        this.Monitor.Log("TEST: replayed ChaCha normal-form skill cast visual. No healing value is applied in this foundation.", LogLevel.Alert);
    }

    private void CommandChaChaSkillStatus(string command, string[] args)
    {
        this.Monitor.Log("===== CHACHA NORMAL-FORM SKILLS =====\n" + this.ChaChaSkills.Describe(), LogLevel.Alert);
    }

    private void CommandChaChaMaterials(string command, string[] args)
    {
        if (!Context.IsWorldReady)
            return;
        int amount = args.Length > 0 && int.TryParse(args[0], out int parsed) ? Math.Clamp(parsed, 1, 999) : 20;
        this.ChaChaMaterials.GiveAllForDebug(amount);
        this.Monitor.Log($"TEST: gave {amount} of each ChaCha skill material to the backpack.", LogLevel.Alert);
    }

    private void CommandChaChaStation(string command, string[] args)
    {
        if (!Context.IsWorldReady || Game1.activeClickableMenu is not null)
            return;
        Game1.activeClickableMenu = new ChaChaSkillUpgradeMenu(this.Save, this.ChaChaSkills, this.ChaChaMaterials, this.Controller);
    }

    private void CommandChaChaMaterialStatus(string command, string[] args)
    {
        this.Monitor.Log("===== CHACHA SKILL MATERIALS =====\n" + this.ChaChaMaterials.Describe(), LogLevel.Alert);
    }

    private void CommandVersion(string command, string[] args)
    {
        this.Monitor.Log($"Cardcha! v{this.ModManifest.Version}", LogLevel.Alert);
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

    private void CommandGiveDust(string command, string[] args)
    {
        if (!Context.IsWorldReady)
            return;

        int amount = args.Length >= 1 && int.TryParse(args[0], out int parsed)
            ? Math.Clamp(parsed, 1, 9999)
            : 50;
        this.Save.Data.SuspiciousDust += amount;
        this.Save.Save();
        this.Monitor.Log($"Added {amount} Magic Dust for Airship upgrade TEST. Total={this.Save.Data.SuspiciousDust}.", LogLevel.Info);
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
