from pathlib import Path
import json

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.42'
PREV = '0.3.0-alpha.28.0.4.14.4.5.12.41'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'{label}: anchor not found')
    return text.replace(old, new, 1)


def update_text(path: Path, fn):
    text = path.read_text(encoding='utf-8')
    new = fn(text)
    if new != text:
        path.write_text(new, encoding='utf-8')


# Version bump.
for rel in ['manifest.json', 'Cardcha.csproj', 'Directory.Build.targets']:
    path = ROOT / rel
    update_text(path, lambda s, p=rel: replace_once(s, PREV, VERSION, f'version {p}'))

# Airship: bind route console to the milestone boss service while preserving the existing Hunt Run helm.
airship_path = ROOT / 'Services/AirshipFoundationService.cs'
def patch_airship(text: str) -> str:
    text = replace_once(
        text,
        '    private readonly SaveService Save;\n    private readonly ControllerProfileService Controller;\n',
        '    private readonly SaveService Save;\n    private readonly ControllerProfileService Controller;\n    private Func<string>? MilestoneRouteAction;\n',
        'airship callback field'
    )
    text = replace_once(
        text,
        '    public AirshipFoundationService(IModHelper helper, IMonitor monitor, SaveService save, ControllerProfileService controller)\n    {\n        this.Helper = helper;\n        this.Monitor = monitor;\n        this.Save = save;\n        this.Controller = controller;\n    }\n',
        '    public AirshipFoundationService(IModHelper helper, IMonitor monitor, SaveService save, ControllerProfileService controller)\n    {\n        this.Helper = helper;\n        this.Monitor = monitor;\n        this.Save = save;\n        this.Controller = controller;\n    }\n\n    public void BindMilestoneRouteHandler(Func<string> handler)\n        => this.MilestoneRouteAction = handler;\n',
        'airship callback binder'
    )
    old_route = '''            if (interiorAction == route)\n            {\n                this.Helper.Input.Suppress(e.Button);\n                int owned = this.Save.Data.OwnedCards?.Count ?? 0;\n                Game1.drawObjectDialogue(ModEntry.T("airship.arcane.route_console", new { cards = owned }));\n                return;\n            }\n'''
    new_route = '''            if (interiorAction == route)\n            {\n                this.Helper.Input.Suppress(e.Button);\n                if (this.MilestoneRouteAction is not null)\n                {\n                    string message = this.MilestoneRouteAction();\n                    if (!string.IsNullOrWhiteSpace(message))\n                        Game1.drawObjectDialogue(message);\n                }\n                else\n                {\n                    int owned = this.Save.Data.OwnedCards?.Count ?? 0;\n                    Game1.drawObjectDialogue(ModEntry.T("airship.arcane.route_console", new { cards = owned }));\n                }\n                return;\n            }\n'''
    text = replace_once(text, old_route, new_route, 'route console callback')
    return text
update_text(airship_path, patch_airship)

# Milestone bosses: real progression route with a second-interact confirmation window.
boss_path = ROOT / 'Services/MilestoneBossService.cs'
def patch_boss(text: str) -> str:
    text = replace_once(
        text,
        '    private int CuratorAdaptationStacks;\n    private int DecisionSerial;\n',
        '    private int CuratorAdaptationStacks;\n    private int DecisionSerial;\n    private long RouteConfirmUntilMs;\n    private MilestoneBossKind? RouteConfirmKind;\n    private const long RouteConfirmWindowMs = 5000L;\n',
        'boss route fields'
    )
    text = replace_once(
        text,
        '        long now = Environment.TickCount64;\n        this.AnchorBossActors();\n',
        '        long now = Environment.TickCount64;\n        if (this.RouteConfirmUntilMs > 0 && now > this.RouteConfirmUntilMs)\n        {\n            this.RouteConfirmUntilMs = 0;\n            this.RouteConfirmKind = null;\n        }\n        this.AnchorBossActors();\n',
        'route confirmation expiry'
    )
    marker = '    public string Describe()\n    {\n'
    route_methods = r'''    public string UseAirshipMilestoneRoute()
    {
        if (!Context.IsWorldReady)
            return ModEntry.T("airship.milestone.unavailable");

        int owned = this.Save.Data.OwnedCards?.Count ?? 0;
        (MilestoneBossKind? kind, int required, string name) = this.ResolveNextMilestoneRoute();
        if (kind is null)
        {
            this.RouteConfirmUntilMs = 0;
            this.RouteConfirmKind = null;
            return ModEntry.T("airship.milestone.all_clear");
        }

        if (kind == MilestoneBossKind.HollowCurator && !this.Save.Data.Region1BossDefeated)
            return ModEntry.T("airship.milestone.boss1_required");

        int regionRequired = kind switch
        {
            MilestoneBossKind.TricolorResonance => 3,
            MilestoneBossKind.Mimi => 4,
            _ => 2,
        };
        if (this.Save.Data.AirshipHighestRegionUnlocked < regionRequired)
            return ModEntry.T("airship.milestone.route_sealed", new { region = regionRequired });

        if (owned < required)
        {
            this.RouteConfirmUntilMs = 0;
            this.RouteConfirmKind = null;
            return ModEntry.T("airship.milestone.progress", new { name, cards = owned, required });
        }

        long now = Environment.TickCount64;
        if (this.RouteConfirmKind != kind || this.RouteConfirmUntilMs <= now)
        {
            this.RouteConfirmKind = kind;
            this.RouteConfirmUntilMs = now + RouteConfirmWindowMs;
            Game1.playSound("smallSelect");
            return ModEntry.T("airship.milestone.confirm", new { name, required });
        }

        GameLocation? arena = this.EnsureLocation(kind.Value);
        if (arena is null)
        {
            this.RouteConfirmUntilMs = 0;
            this.RouteConfirmKind = null;
            return ModEntry.T("airship.milestone.unavailable");
        }

        this.RouteConfirmUntilMs = 0;
        this.RouteConfirmKind = null;
        Game1.playSound("wand");
        Game1.warpFarmer(arena.NameOrUniqueName, ArrivalTile.X, ArrivalTile.Y, 0);
        return string.Empty;
    }

    public string DescribeMilestoneRoute()
    {
        int owned = this.Save.Data.OwnedCards?.Count ?? 0;
        (MilestoneBossKind? kind, int required, string name) = this.ResolveNextMilestoneRoute();
        string next = kind is null ? "all-clear" : $"{kind}:{name}:{owned}/{required}";
        double confirm = this.RouteConfirmUntilMs > Environment.TickCount64
            ? (this.RouteConfirmUntilMs - Environment.TickCount64) / 1000d
            : 0d;
        return $"0673 MilestoneRoute | Next={next} | BossI={this.Save.Data.Region1BossDefeated} | HighestRegion={this.Save.Data.AirshipHighestRegionUnlocked} | Confirm={this.RouteConfirmKind?.ToString() ?? "none"}:{confirm:0.0}s";
    }

    private (MilestoneBossKind? Kind, int Required, string Name) ResolveNextMilestoneRoute()
    {
        HashSet<string>? unlocked = this.Save.Data.BossCardsUnlocked;
        if (unlocked?.Contains(MirrorArchiveBossCardId) != true)
            return (MilestoneBossKind.HollowCurator, 40, "The Hollow Curator");
        if (unlocked?.Contains(TricolorBossCardId) != true)
            return (MilestoneBossKind.TricolorResonance, 60, "The Tricolor Resonance");
        if (unlocked?.Contains(MimiBossCardId) != true)
            return (MilestoneBossKind.Mimi, 80, "MiMi • The Resonance Master");
        return (null, 0, string.Empty);
    }

'''
    text = replace_once(text, marker, route_methods + marker, 'milestone route methods')
    text = replace_once(
        text,
        '        this.CuratorAdaptationStacks = 0;\n        this.DecisionSerial = 0;\n        this.AttackTargetTile = PlayerTile();\n',
        '        this.CuratorAdaptationStacks = 0;\n        this.DecisionSerial = 0;\n        this.RouteConfirmUntilMs = 0;\n        this.RouteConfirmKind = null;\n        this.AttackTargetTile = PlayerTile();\n',
        'start encounter route reset'
    )
    # ResetRuntime has the same tail but no AttackTargetTile immediately after, so patch its exact ending.
    text = replace_once(
        text,
        '        this.CuratorAdaptationStacks = 0;\n        this.DecisionSerial = 0;\n    }\n\n    private void RemoveMarkedActors',
        '        this.CuratorAdaptationStacks = 0;\n        this.DecisionSerial = 0;\n        this.RouteConfirmUntilMs = 0;\n        this.RouteConfirmKind = null;\n    }\n\n    private void RemoveMarkedActors',
        'reset runtime route state'
    )
    text = text.replace('0672 MilestoneBoss', '0673 MilestoneBoss')
    return text
update_text(boss_path, patch_boss)

# ModEntry binding, diagnostics, and build banner.
entry_path = ROOT / 'ModEntry.cs'
def patch_entry(text: str) -> str:
    text = replace_once(
        text,
        '        this.MilestoneBosses = new MilestoneBossService(helper, this.Monitor, this.Save);\n        this.CardLab = new CardTestLabService',
        '        this.MilestoneBosses = new MilestoneBossService(helper, this.Monitor, this.Save);\n        this.Airship.BindMilestoneRouteHandler(this.MilestoneBosses.UseAirshipMilestoneRoute);\n        this.CardLab = new CardTestLabService',
        'bind milestone route'
    )
    text = replace_once(
        text,
        '        helper.ConsoleCommands.Add("cardcha_boss_milestone_status", "Show Boss II/III/IV runtime and milestone reward state.", (_, _) => this.Monitor.Log(this.MilestoneBosses.Describe(), LogLevel.Alert));\n',
        '        helper.ConsoleCommands.Add("cardcha_boss_milestone_status", "Show Boss II/III/IV runtime and milestone reward state.", (_, _) => this.Monitor.Log(this.MilestoneBosses.Describe(), LogLevel.Alert));\n        helper.ConsoleCommands.Add("cardcha_milestone_route_status", "Show the real 40/60/80-card milestone route state.", (_, _) => this.Monitor.Log(this.MilestoneBosses.DescribeMilestoneRoute(), LogLevel.Alert));\n',
        'milestone route command'
    )
    text = text.replace(PREV, VERSION)
    text = text.replace('BOSS ENCOUNTER DEPTH PASS TEST', 'MILESTONE PROGRESSION BOSS ROUTE TEST')
    return text
update_text(entry_path, patch_entry)

# i18n additions.
def patch_i18n(path: Path, values: dict[str, str]):
    data = json.loads(path.read_text(encoding='utf-8'))
    data.update(values)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

patch_i18n(ROOT / 'i18n/default.json', {
    'airship.milestone.boss1_required': 'The Milestone Route is still sealed. Defeat the Verdant Guardian first.',
    'airship.milestone.route_sealed': 'The resonance route beyond Region {{region}} is still sealed by the previous milestone.',
    'airship.milestone.progress': 'Milestone Route • {{name}} • {{cards}}/{{required}} cards. Keep collecting cards to stabilize this route.',
    'airship.milestone.confirm': 'Milestone Route ready: {{name}} ({{required}} cards). Interact with the route console again within 5 seconds to depart.',
    'airship.milestone.all_clear': 'All four milestone resonances are complete. The route console is quiet for now.',
    'airship.milestone.unavailable': 'The milestone arena cannot be stabilized right now.'
})
patch_i18n(ROOT / 'i18n/vi.json', {
    'airship.milestone.boss1_required': 'Tuyến Mốc vẫn đang bị phong ấn. Hãy đánh bại Verdant Guardian trước.',
    'airship.milestone.route_sealed': 'Tuyến cộng hưởng vượt qua Khu Vực {{region}} vẫn bị khóa bởi mốc trước đó.',
    'airship.milestone.progress': 'Tuyến Mốc • {{name}} • {{cards}}/{{required}} lá bài. Hãy tiếp tục sưu tập để ổn định tuyến đường này.',
    'airship.milestone.confirm': 'Tuyến Mốc đã sẵn sàng: {{name}} ({{required}} lá bài). Tương tác với bàn điều hướng lần nữa trong 5 giây để khởi hành.',
    'airship.milestone.all_clear': 'Cả bốn mốc cộng hưởng đã hoàn tất. Bàn điều hướng tạm thời đã yên lặng.',
    'airship.milestone.unavailable': 'Hiện tại chưa thể ổn định đấu trường mốc này.'
})

# Handoff.
handoff = Path('handoff/ALPHA28_0673_MILESTONE_PROGRESSION_BOSS_ROUTE.md')
handoff.write_text(f'''# Alpha28 0673 - Milestone Progression & Boss Route Integration\n\nBuild: `{VERSION}`\nBranch: `cardcha-alpha28-0673-milestone-progression-boss-route`\nStatus: CI/package pending. In-game acceptance for 0669-0672 remains pending.\n\n## Scope\n- Sky Dock route console becomes the real 40/60/80-card milestone route.\n- Deck helm remains Region I Hunt Run access and is not hijacked by milestone bosses.\n- Boss II requires real Boss I clear + 40 owned cards.\n- Boss III requires Mirror Archive clear/unlock + Region III state + 60 owned cards.\n- Boss IV MiMi requires Tricolor Resonance clear/unlock + Region IV state + 80 owned cards.\n- First route-console interaction shows readiness; second interaction within 5 seconds departs.\n- Existing Boss II/III/IV victory rewards continue to unlock Region III/IV and their Boss Cards.\n\n## Regression guards\n- Save schema remains 19.\n- Boss HP, phase mechanics, 0671 authored PNG/TMX assets, and 0672 encounter-depth logic remain unchanged.\n- Boss I / 0669 remains frozen pending player acceptance.\n- `mimi_walk.png` remains locked.\n- Card audit remains 76 active / 80 source.\n''', encoding='utf-8')
Path('handoff/LATEST_CARDCHA_HANDOFF.md').write_text(f'''# Latest Cardcha Handoff\n\nCurrent branch: `cardcha-alpha28-0673-milestone-progression-boss-route`\nCurrent build: `{VERSION}`\nContinue from: `handoff/ALPHA28_0673_MILESTONE_PROGRESSION_BOSS_ROUTE.md`\n\n0669-0672 in-game acceptance is still pending. Do not resume from stale `main` or pre-0673 branches.\n''', encoding='utf-8')

print('0673 generator complete')
