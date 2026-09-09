from pathlib import Path
import json

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.39'
PREV = '0.3.0-alpha.28.0.4.14.4.5.12.38'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'0670 anchor missing: {label}')
    return text.replace(old, new, 1)


# Version bump.
manifest_path = ROOT / 'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['Version'] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for rel in ['Cardcha.csproj', 'Directory.Build.targets']:
    p = ROOT / rel
    p.write_text(p.read_text(encoding='utf-8').replace(PREV, VERSION), encoding='utf-8')

# Wire the new milestone boss owner into ModEntry.
p = ROOT / 'ModEntry.cs'
s = p.read_text(encoding='utf-8')
s = s.replace(PREV, VERSION)
s = s.replace('VISUAL AUTH PASS TEST', 'REMAINING BOSS FOUNDATION TEST')
s = replace_once(
    s,
    '    private VerdantGuardianArenaPolishService VerdantArenaPolish = null!;\n',
    '    private VerdantGuardianArenaPolishService VerdantArenaPolish = null!;\n    private MilestoneBossService MilestoneBosses = null!;\n',
    'MilestoneBoss field'
)
s = replace_once(
    s,
    '        this.VerdantArenaPolish = new VerdantGuardianArenaPolishService(helper, this.Monitor, this.VerdantGuardian);\n',
    '        this.VerdantArenaPolish = new VerdantGuardianArenaPolishService(helper, this.Monitor, this.VerdantGuardian);\n        this.MilestoneBosses = new MilestoneBossService(helper, this.Monitor, this.Save);\n',
    'MilestoneBoss construction'
)
s = replace_once(
    s,
    '        helper.Events.Content.AssetRequested += this.VerdantGuardian.OnAssetRequested;\n',
    '        helper.Events.Content.AssetRequested += this.VerdantGuardian.OnAssetRequested;\n        helper.Events.Content.AssetRequested += this.MilestoneBosses.OnAssetRequested;\n',
    'MilestoneBoss asset event'
)
s = replace_once(
    s,
    '        helper.Events.GameLoop.SaveLoaded += this.BossCards.OnSaveLoaded;\n',
    '        helper.Events.GameLoop.SaveLoaded += this.BossCards.OnSaveLoaded;\n        helper.Events.GameLoop.SaveLoaded += this.MilestoneBosses.OnSaveLoaded;\n',
    'MilestoneBoss save loaded event'
)
s = replace_once(
    s,
    '        helper.Events.GameLoop.DayStarted += this.VerdantGuardian.OnDayStarted;\n',
    '        helper.Events.GameLoop.DayStarted += this.VerdantGuardian.OnDayStarted;\n        helper.Events.GameLoop.DayStarted += this.MilestoneBosses.OnDayStarted;\n',
    'MilestoneBoss day event'
)
s = replace_once(
    s,
    '        helper.Events.GameLoop.UpdateTicked += this.VerdantGuardian.OnUpdateTicked;\n',
    '        helper.Events.GameLoop.UpdateTicked += this.VerdantGuardian.OnUpdateTicked;\n        helper.Events.GameLoop.UpdateTicked += this.MilestoneBosses.OnUpdateTicked;\n',
    'MilestoneBoss update event'
)
s = replace_once(
    s,
    '        helper.Events.GameLoop.ReturnedToTitle += this.VerdantArenaPolish.OnReturnedToTitle;\n',
    '        helper.Events.GameLoop.ReturnedToTitle += this.VerdantArenaPolish.OnReturnedToTitle;\n        helper.Events.GameLoop.ReturnedToTitle += this.MilestoneBosses.OnReturnedToTitle;\n',
    'MilestoneBoss title event'
)
s = replace_once(
    s,
    '        helper.Events.Display.RenderedHud += this.VerdantArenaPolish.OnRenderedHud;\n',
    '        helper.Events.Display.RenderedHud += this.VerdantArenaPolish.OnRenderedHud;\n        helper.Events.Display.RenderedHud += this.MilestoneBosses.OnRenderedHud;\n',
    'MilestoneBoss HUD event'
)
s = replace_once(
    s,
    '        helper.Events.Display.RenderedWorld += this.VerdantSummons.OnRenderedWorld;\n',
    '        helper.Events.Display.RenderedWorld += this.VerdantSummons.OnRenderedWorld;\n        helper.Events.Display.RenderedWorld += this.MilestoneBosses.OnRenderedWorld;\n',
    'MilestoneBoss world event'
)
s = replace_once(
    s,
    '        helper.Events.Input.ButtonPressed += this.VerdantGuardian.OnButtonPressed;\n',
    '        helper.Events.Input.ButtonPressed += this.VerdantGuardian.OnButtonPressed;\n        helper.Events.Input.ButtonPressed += this.MilestoneBosses.OnButtonPressed;\n',
    'MilestoneBoss input event'
)
s = replace_once(
    s,
    '        helper.Events.Player.Warped += this.VerdantArenaPolish.OnWarped;\n',
    '        helper.Events.Player.Warped += this.VerdantArenaPolish.OnWarped;\n        helper.Events.Player.Warped += this.MilestoneBosses.OnWarped;\n',
    'MilestoneBoss warped event'
)
cmd_anchor = '        helper.ConsoleCommands.Add("cardcha_boss1_summons", "TEST ONLY: replace current Boss I adds with one custom summon wave.", (_, _) => this.Monitor.Log(this.VerdantGuardian.DebugSummonWave(), LogLevel.Alert));\n'
cmd_add = cmd_anchor + '''        helper.ConsoleCommands.Add("cardcha_test_boss2", "TEST ONLY: enter Boss II - The Hollow Curator (40-card milestone bypass).", (_, _) => this.Monitor.Log(this.MilestoneBosses.DebugEnterBoss(2), LogLevel.Alert));\n        helper.ConsoleCommands.Add("cardcha_test_boss3", "TEST ONLY: enter Boss III - The Tricolor Resonance (60-card milestone bypass).", (_, _) => this.Monitor.Log(this.MilestoneBosses.DebugEnterBoss(3), LogLevel.Alert));\n        helper.ConsoleCommands.Add("cardcha_test_boss4", "TEST ONLY: enter Boss IV - MiMi (80-card milestone bypass).", (_, _) => this.Monitor.Log(this.MilestoneBosses.DebugEnterBoss(4), LogLevel.Alert));\n        helper.ConsoleCommands.Add("cardcha_boss_milestone_status", "Show Boss II/III/IV runtime and milestone reward state.", (_, _) => this.Monitor.Log(this.MilestoneBosses.Describe(), LogLevel.Alert));\n'''
s = replace_once(s, cmd_anchor, cmd_add, 'MilestoneBoss debug commands')
p.write_text(s, encoding='utf-8')

# Hide only custom boss proxy art. Actors stay visible to the engine for collision/damage.
p = ROOT / 'Patches' / 'VerdantGuardianProxyDrawPatch.cs'
s = p.read_text(encoding='utf-8')
s = replace_once(
    s,
    '           && !__instance.modData.ContainsKey(VerdantGuardianBossService.BossAddMarkerKey);\n',
    '           && !__instance.modData.ContainsKey(VerdantGuardianBossService.BossAddMarkerKey)\n           && !__instance.modData.ContainsKey(MilestoneBossService.BossMarkerKey);\n',
    'MilestoneBoss proxy draw suppression'
)
p.write_text(s, encoding='utf-8')

# Boss proxies must not knock around or trigger normal monster loot/death routing.
p = ROOT / 'Patches' / 'MonsterDamagePatch.cs'
s = p.read_text(encoding='utf-8')
s = replace_once(
    s,
    '            bool isVerdantTotem = __instance.modData.ContainsKey(VerdantGuardianBossService.TotemMarkerKey);\n',
    '            bool isVerdantTotem = __instance.modData.ContainsKey(VerdantGuardianBossService.TotemMarkerKey);\n            bool isMilestoneBoss = __instance.modData.ContainsKey(MilestoneBossService.BossMarkerKey);\n',
    'MilestoneBoss damage classification'
)
s = replace_once(
    s,
    '            if (isVerdantTotem) { xTrajectory = 0; yTrajectory = 0; }\n',
    '            if (isVerdantTotem || isMilestoneBoss) { xTrajectory = 0; yTrajectory = 0; }\n',
    'MilestoneBoss no knockback'
)
s = replace_once(
    s,
    '            if (__state > 0 && __instance.Health <= 0 && !__instance.modData.ContainsKey(VerdantGuardianBossService.TotemMarkerKey))\n',
    '            if (__state > 0 && __instance.Health <= 0\n                && !__instance.modData.ContainsKey(VerdantGuardianBossService.TotemMarkerKey)\n                && !__instance.modData.ContainsKey(MilestoneBossService.BossMarkerKey))\n',
    'MilestoneBoss loot suppression'
)
p.write_text(s, encoding='utf-8')

# Compile fix: switch expressions need the modulo result parenthesized.
p = ROOT / 'Services' / 'MilestoneBossService.cs'
s = p.read_text(encoding='utf-8')
s = s.replace(
    '    private Color TricolorCycle(int i) => i % 3 switch\n',
    '    private Color TricolorCycle(int i) => (i % 3) switch\n'
)
if 'private Color TricolorCycle(int i) => (i % 3) switch' not in s:
    raise RuntimeError('0670 tricolor color-switch compile fix missing')
p.write_text(s, encoding='utf-8')

# Handoff source of truth.
handoff = Path('handoff')
handoff.mkdir(exist_ok=True)
(handoff / 'ALPHA28_0670_REMAINING_BOSS_FOUNDATION.md').write_text('''# Alpha28 0670 - Remaining Boss Foundation\n\nBuild: `0.3.0-alpha.28.0.4.14.4.5.12.39`\nBranch: `cardcha-alpha28-0670-remaining-boss-foundation`\nStatus: CI/package and in-game acceptance pending.\n\n## User override / sequencing\n0669 has not yet received in-game acceptance because the user cannot test it right now. The user explicitly asked development to continue on the remaining bosses. 0670 therefore forks from materialized 0669 but does not modify Boss I/0669 visual-auth work. Any later 0669 regression must be fixed separately and then forward-ported carefully.\n\n## Boss II - 40 cards: The Hollow Curator\n- 2200 HP.\n- Phase 1 Observation: Card Volley + Scan/Adapt.\n- Phase 2 Reflection: adds Mirror Burst and faster pressure.\n- Phase 3 Curator's Truth: Archive Collapse + empowered reflection.\n- Adaptation stacks rise to 3 and strengthen Curator attack damage.\n- Runtime teleport/reposition every few decisions.\n- First clear unlocks Boss Card id `mirror_archive` and raises highest region to at least 3.\n\n## Boss III - 60 cards: The Tricolor Resonance\n- Three independently damageable guardians: Ignis, Vita, Aether, 780 HP each.\n- Ignis = heavy area pressure.\n- Vita = heals surviving guardians + vine pressure.\n- Aether = ranged zone pressure.\n- Only after all three fall does Phase 4 `Unified Resonance` spawn at 1650 HP.\n- First clear unlocks Boss Card id `tricolor_resonance` and raises highest region to at least 4.\n\n## Boss IV - 80 cards: MiMi, The Resonance Master\n- MiMi remains the final 80-card boss.\n- 3600 HP, four runtime phases at 75/50/25 percent thresholds.\n- Phase 1 Familiar Power.\n- Phase 2 Refined Control.\n- Phase 3 True Resonance.\n- Final phase combines arena/mirror/tricolor pressure.\n- First clear unlocks Boss Card id `mimis_resonance`.\n- `mimi_walk.png` is NOT modified. Boss runtime presentation is separate.\n\n## Architecture / regression guards\n- Save schema remains 19. No new save fields.\n- Boss completion persistence uses the existing `BossCardsUnlocked` set.\n- Region progression uses existing `AirshipHighestRegionUnlocked`.\n- Milestone boss GreenSlime proxies remain engine-visible (`isInvisible=false`) but their vanilla draw is Harmony-suppressed.\n- Milestone boss proxies do not receive knockback and do not trigger normal Scrap/loot death routing.\n- Boss I, Hunt Run, MiMi social/home assets, 76-card audit, controller contract and Airship gate identity remain untouched.\n\n## TEST commands\n- `cardcha_test_boss2`\n- `cardcha_test_boss3`\n- `cardcha_test_boss4`\n- `cardcha_boss_milestone_status`\n\nThese TEST commands bypass 40/60/80 ownership gates only for direct arena testing. Normal Region II/III/IV route integration remains later work.\n\n## Visual status\n0670 is a functional boss foundation. Boss II/III/IV use custom runtime silhouettes, telegraphs and HUD rather than final authored concept-quality sprite sheets. Dedicated native-size art, unique arenas, ChaCha Mirror/Trinity/Resonance forms and full Boss Card runtime effects remain later passes.\n''', encoding='utf-8')
(handoff / 'LATEST_CARDCHA_HANDOFF.md').write_text('''# Latest Cardcha Handoff\n\nCurrent branch: `cardcha-alpha28-0670-remaining-boss-foundation`\nCurrent build: `0.3.0-alpha.28.0.4.14.4.5.12.39`\nContinue from: `handoff/ALPHA28_0670_REMAINING_BOSS_FOUNDATION.md`\n\n0669 in-game acceptance is still pending. Do not resume from stale `main`, 0668B or 0668C.\n''', encoding='utf-8')

print('0670 remaining boss foundation generated')
