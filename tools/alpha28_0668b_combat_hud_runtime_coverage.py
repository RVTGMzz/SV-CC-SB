from pathlib import Path
import json, re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.36'

# version bump
manifest_path = ROOT/'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['Version'] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
for rel in ['Cardcha.csproj','Directory.Build.targets']:
    p = ROOT/rel
    s = p.read_text(encoding='utf-8')
    s = s.replace('0.3.0-alpha.28.0.4.14.4.5.12.35', VERSION)
    p.write_text(s, encoding='utf-8')

# 1) Core timed HUD snapshot
p = ROOT/'Services'/'CoreCardEffectsService.cs'
s = p.read_text(encoding='utf-8')
record_anchor = 'internal readonly record struct CardPassiveDebugSnapshot('
if 'TimedCardHudState' not in s:
    idx = s.index(record_anchor)
    rec = '''internal readonly record struct TimedCardHudState(\n    string CardId,\n    double RemainingSeconds,\n    double TotalSeconds,\n    string StackText,\n    int Priority\n);\n\n'''
    s = s[:idx] + rec + s[idx:]

prop_anchor = '    public int CurrentNoHitKillStreak => Math.Max(0, this.NoHitKillStreak);\n'
if 'GetTimedHudStates()' not in s:
    method = r'''    internal IReadOnlyList<TimedCardHudState> GetTimedHudStates()
    {
        if (!this.Loadout.CardEffectsActive)
            return Array.Empty<TimedCardHudState>();

        long now = Environment.TickCount64;
        this.ExpireTimedStacks(now);
        List<TimedCardHudState> states = new();

        void Add(string id, long until, int totalMs, int priority, string stack = "")
        {
            if (!this.Loadout.IsEquipped(id) || until <= now)
                return;
            double remaining = Math.Max(0d, (until - now) / 1000d);
            double total = Math.Max(0.1d, totalMs / 1000d);
            states.Add(new TimedCardHudState(id, remaining, total, stack, priority));
        }

        Add("guard_step", this.GuardStepUntil, this.LevelInt("guard_step", 600, 700, 800, 900), 62);
        Add("backstep", this.BackstepUntil, this.LevelInt("backstep", 1000, 1100, 1200, 1300), 61);
        Add("explorer", this.ExplorerUntil, 3000, 45);
        Add("momentum", this.MomentumUntil, 2000, 70);
        Add("adrenaline", this.AdrenalineUntil, 3000, 90);
        Add("fleet_hunter", this.FleetHunterUntil, 2500, 72);
        Add("battle_trance", this.BattleTranceUntil, 2000, 74);
        Add("overclock", this.OverclockUntil, 5000, 80);
        Add("void_walker", this.VoidPhaseUntil, this.LevelInt("void_walker", 1500, 1750, 2000), 95);
        Add("time_breaker", this.TimeBreakerUntil, 3000, 88);
        Add("apex_predator", this.ApexPredatorBuffUntil, 6000, 78);

        if (this.Loadout.IsEquipped("predator") && this.PredatorStacks > 0 && this.PredatorExpiresAt > now)
            Add("predator", this.PredatorExpiresAt, 6000, 68, $"{this.PredatorStacks}/3");

        if (this.Loadout.IsEquipped("war_drum") && this.WarDrumStacks > 0 && this.WarDrumExpiresAt > now)
        {
            long until = this.WarDrumStacks >= 4 && this.WarDrumBurstUntil > now ? this.WarDrumBurstUntil : this.WarDrumExpiresAt;
            int total = this.WarDrumStacks >= 4 && this.WarDrumBurstUntil > now ? 3000 : 6000;
            Add("war_drum", until, total, 76, $"{this.WarDrumStacks}/4");
        }

        return states;
    }

'''
    s = s.replace(prop_anchor, prop_anchor + method, 1)
p.write_text(s, encoding='utf-8')

# 2) expose timed states from CombatService
p = ROOT/'Services'/'CombatService.cs'
s = p.read_text(encoding='utf-8')
anchor = '    public int CurrentNoHitKillStreak => this.Completion.CurrentNoHitKillStreak;\n'
if 'CurrentTimedCardHudStates' not in s:
    s = s.replace(anchor, anchor + '    internal IReadOnlyList<TimedCardHudState> CurrentTimedCardHudStates => this.Completion.GetTimedHudStates();\n', 1)
p.write_text(s, encoding='utf-8')

# 3) Combat HUD: active timed card coverage; persistent READY indicators temporarily suppressed
p = ROOT/'UI'/'CombatHudRenderer.cs'
s = p.read_text(encoding='utf-8')
if 'ShowPersistentReadyIndicators' not in s:
    s = s.replace('    private const int CircleTextureSize = 64;\n', '    private const int CircleTextureSize = 64;\n    // 0668B: temporary cleanup requested after in-game overlap report.\n    private const bool ShowPersistentReadyIndicators = false;\n', 1)

# wrap Phoenix ready
s = s.replace('        if (this.Loadout.IsEquipped("phoenix_heart") && this.Combat.IsPhoenixReady)\n', '        if (ShowPersistentReadyIndicators && this.Loadout.IsEquipped("phoenix_heart") && this.Combat.IsPhoenixReady)\n', 1)
# suppress soul eater progress-only READY but keep active buff
s = s.replace('            else\n            {\n                entries.Add(new HudEntry(\n                    Key: "soul_eater_progress",', '            else if (ShowPersistentReadyIndicators)\n            {\n                entries.Add(new HudEntry(\n                    Key: "soul_eater_progress",', 1)

# timed states before chain hunter
insert_anchor = '        if (this.Loadout.IsEquipped("chain_hunter"))\n'
if 'CurrentTimedCardHudStates' not in s:
    timed_block = r'''        // 0668B: every player-facing timed proc should visibly confirm that the card fired.
        // Passive always-on cards stay quiet; duration/stack effects get a compact Cardcha slot.
        foreach (TimedCardHudState timed in this.Combat.CurrentTimedCardHudStates)
        {
            CardDefinition? timedCard = this.Cards.Get(timed.CardId);
            string label = timedCard?.Name ?? timed.CardId;
            entries.Add(new HudEntry(
                Key: "timed_" + timed.CardId,
                CardId: timed.CardId,
                Label: label,
                Value: $"{timed.RemainingSeconds:0.0}s",
                RemainingSeconds: timed.RemainingSeconds,
                TotalSeconds: timed.TotalSeconds,
                Timing: HudTiming.Duration,
                StackText: timed.StackText,
                Kind: HudKind.Buff,
                Priority: timed.Priority
            ));
        }

'''
    s = s.replace(insert_anchor, timed_block + insert_anchor, 1)
p.write_text(s, encoding='utf-8')

# 4) hide the large Verdant Core corner panel; runtime/world feedback stays alive
p = ROOT/'Services'/'BossCardService.cs'
s = p.read_text(encoding='utf-8')
start = s.index('    public void OnRenderedHud(object? sender, RenderedHudEventArgs e)\n    {')
end = s.index('\n    public string DebugUnlock()', start)
replacement = '''    public void OnRenderedHud(object? sender, RenderedHudEventArgs e)\n    {\n        // 0668B: temporarily hidden after real-game overlap feedback.\n        // Verdant Core runtime, activation message, world icon and diagnostics remain active.\n        // Reintroduce it later only through the unified Cardcha combat HUD.\n    }\n'''
s = s[:start] + replacement + s[end:]
p.write_text(s, encoding='utf-8')

# 5) startup version text and diagnostics command
p = ROOT/'ModEntry.cs'
s = p.read_text(encoding='utf-8')
s = s.replace('0.3.0-alpha.28.0.4.14.4.5.12.35 VERDANT TOTEM + AIRSHIP HUB CLEANUP TEST', '0.3.0-alpha.28.0.4.14.4.5.12.36 COMBAT HUD RUNTIME COVERAGE HOTFIX TEST')
cmd_anchor = '        helper.ConsoleCommands.Add("cardcha_combat_status", "Show active Cardcha combat state.", this.CommandCombatStatus);\n'
if 'cardcha_hud_runtime_status' not in s:
    s = s.replace(cmd_anchor, cmd_anchor + '        helper.ConsoleCommands.Add("cardcha_hud_runtime_status", "Show timed Cardcha HUD proc state.", (_, _) => this.Monitor.Log(string.Join(" | ", this.Combat.CurrentTimedCardHudStates.Select(p => $"{p.CardId}:{p.RemainingSeconds:0.0}s")), LogLevel.Alert));\n', 1)
p.write_text(s, encoding='utf-8')

# handoff
Path('handoff/ALPHA28_0668B_COMBAT_HUD_RUNTIME_COVERAGE.md').write_text(f'''# Alpha28 0668B - Combat HUD Runtime Coverage Hotfix\n\nBuild: `{VERSION}`\nBranch: `cardcha-alpha28-0668b-combat-hud-runtime-coverage`\nStatus: in-game acceptance pending.\n\n## Fixes\n- Adrenaline now appears in the unified Cardcha combat HUD for its real 3-second runtime.\n- Timed-proc HUD coverage added for Guard Step, Backstep, Explorer, Momentum, Adrenaline, Fleet Hunter, Battle Trance, Overclock, Void Walker, Time Breaker, Apex Predator, Predator stacks, and War Drum stacks.\n- Passive always-on cards remain quiet instead of cluttering the screen.\n- Persistent READY indicators are temporarily hidden.\n- The separate Verdant Core left-corner panel is temporarily hidden. Verdant Core gameplay remains active, including trigger, damage reduction, healing, world icon and messages.\n- No combat balance, Boss I, Totem, Hunt Run, Airship or save-schema values changed.\n''', encoding='utf-8')
Path('handoff/LATEST_CARDCHA_HANDOFF.md').write_text(f'''# Latest Cardcha handoff\n\nCurrent branch: `cardcha-alpha28-0668b-combat-hud-runtime-coverage`\nCurrent build: `{VERSION}`\nContinue from `handoff/ALPHA28_0668B_COMBAT_HUD_RUNTIME_COVERAGE.md`.\nDo not resume from stale main.\n''', encoding='utf-8')

print(json.dumps({'version': VERSION, 'adrenalineHud': True, 'timedProcHud': True, 'persistentReadyHidden': True, 'verdantCornerPanelHidden': True}, indent=2))
