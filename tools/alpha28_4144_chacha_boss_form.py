from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4'


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def write(rel, text):
    (ROOT / rel).write_text(text, encoding='utf-8')


def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'{label}: anchor not found')
    return text.replace(old, new, 1)


# Version metadata.
manifest = ROOT / 'manifest.json'
data = json.loads(manifest.read_text(encoding='utf-8'))
data['Version'] = VERSION
manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

csproj = ROOT / 'Cardcha.csproj'
s = csproj.read_text(encoding='utf-8')
s = re.sub(r'<Version>[^<]+</Version>', f'<Version>{VERSION}</Version>', s, count=1)
csproj.write_text(s, encoding='utf-8')

(ROOT / 'Directory.Build.targets').write_text(f'''<Project>\n  <PropertyGroup>\n    <Version>{VERSION}</Version>\n  </PropertyGroup>\n\n  <!-- .4.14.4 ChaCha Boss Form foundation. -->\n  <Target Name="CardchaAlpha2804144Manifest" BeforeTargets="BeforeBuild">\n    <Exec Command="python3 -c &quot;from pathlib import Path; import re; p=Path(r'$(MSBuildProjectDirectory)/manifest.json'); s=p.read_text(encoding='utf-8'); s=re.sub(r'\\&quot;Version\\&quot;\\s*:\\s*\\&quot;[^\\&quot;]+\\&quot;', '\\&quot;Version\\&quot;: \\&quot;{VERSION}\\&quot;', s, count=1); p.write_text(s, encoding='utf-8')&quot;" />\n  </Target>\n</Project>\n''', encoding='utf-8')

# Boss Energy: suppress gain during Boss Form.
s = read('Services/BossEnergyService.cs')
if 'private bool GainSuppressed;' not in s:
    s = replace_once(
        s,
        '    private double Current;\n',
        '    private double Current;\n    private bool GainSuppressed;\n',
        'Boss Energy suppression field'
    )
    s = replace_once(
        s,
        '    public double CurrentEnergy => Math.Clamp(this.Current, 0d, MaxEnergy);\n',
        '    public double CurrentEnergy => Math.Clamp(this.Current, 0d, MaxEnergy);\n    public bool IsGainSuppressed => this.GainSuppressed;\n',
        'Boss Energy suppression property'
    )
    s = replace_once(
        s,
        '    public bool TrySpend(double amount)\n',
        '    public void SetGainSuppressed(bool suppressed)\n        => this.GainSuppressed = suppressed;\n\n    public bool TrySpend(double amount)\n',
        'Boss Energy suppression setter'
    )
    s = replace_once(
        s,
        '        this.GainEvents = 0;\n',
        '        this.GainEvents = 0;\n        this.GainSuppressed = false;\n',
        'Boss Energy reset suppression'
    )
    s = replace_once(
        s,
        '        if (amount <= 0d)\n            return;\n\n        double before = this.CurrentEnergy;\n',
        '        if (amount <= 0d || this.GainSuppressed)\n            return;\n\n        double before = this.CurrentEnergy;\n',
        'Boss Energy suppressed Add'
    )
    s = s.replace(
        '$"(base={this.LastBaseGain:0.##}, VictoryChargeBonus={this.LastVictoryChargeBonus:0.##}) | Events={this.GainEvents}";',
        '$"(base={this.LastBaseGain:0.##}, VictoryChargeBonus={this.LastVictoryChargeBonus:0.##}) | Events={this.GainEvents} | Suppressed={this.GainSuppressed}";'
    )
write('Services/BossEnergyService.cs', s)

# World actor: Boss Form has an unmistakable larger visual while preserving the approved sprite sheet.
s = read('Services/WorldActorService.cs')
if 'ChaChaBossNativeScale' not in s:
    s = replace_once(
        s,
        '    private const float ChaChaNativeScale = 0.5625f;\n',
        '    private const float ChaChaNativeScale = 0.5625f;\n    private const float ChaChaBossNativeScale = 0.74f;\n',
        'ChaCha Boss scale constant'
    )
    s = replace_once(
        s,
        '    private int LastChaChaEmote = -1;\n',
        '    private int LastChaChaEmote = -1;\n    private bool ChaChaBossVisualActive;\n',
        'ChaCha Boss visual state'
    )
    s = replace_once(
        s,
        '        actor.Scale = ChaChaNativeScale;\n',
        '        actor.Scale = this.ChaChaBossVisualActive ? ChaChaBossNativeScale : ChaChaNativeScale;\n',
        'ChaCha scale selection'
    )
    s = replace_once(
        s,
        '    public NPC? FindChaChaActor()\n',
        '''    public bool IsChaChaBossVisualActive => this.ChaChaBossVisualActive;\n\n    public void SetChaChaBossVisual(bool active)\n    {\n        this.ChaChaBossVisualActive = active;\n        NPC? actor = this.FindChaChaActor();\n        if (actor is not null)\n            actor.Scale = active ? ChaChaBossNativeScale : ChaChaNativeScale;\n    }\n\n    public NPC? FindChaChaActor()\n''',
        'ChaCha Boss visual API'
    )
    s = replace_once(
        s,
        '            this.LastChaChaEmote = -1;\n            return;\n',
        '            this.LastChaChaEmote = -1;\n            this.ChaChaBossVisualActive = false;\n            return;\n',
        'ChaCha hidden visual reset'
    )
    s = replace_once(
        s,
        '        this.LastChaChaEmote = -1;\n    }\n\n    /// <summary>\n    /// Give ChaCha occasional',
        '        this.LastChaChaEmote = -1;\n        this.ChaChaBossVisualActive = false;\n    }\n\n    /// <summary>\n    /// Give ChaCha occasional',
        'ChaCha hide reset'
    )
    s = replace_once(
        s,
        '        this.LastChaChaEmote = -1;\n    }\n}\n',
        '        this.LastChaChaEmote = -1;\n        this.ChaChaBossVisualActive = false;\n    }\n}\n',
        'ChaCha title reset'
    )
write('Services/WorldActorService.cs', s)

# i18n for activation card and lifecycle.
for lang, values in {
    'default.json': {
        'chacha.boss.ready': 'CHACHA BOSS FORM • READY',
        'chacha.boss.hint': 'CLICK • or press SELECT / VIEW ×3',
        'chacha.boss.triple': 'SELECT / VIEW  {{count}}/{{max}}',
        'chacha.boss.active': 'CHACHA BOSS FORM • ACTIVE',
        'chacha.boss.timer': '{{seconds}}s remaining',
        'chacha.boss.activated': 'ChaCha absorbed the full resonance and entered Boss Form!',
    },
    'vi.json': {
        'chacha.boss.ready': 'CHACHA BOSS FORM • SẴN SÀNG',
        'chacha.boss.hint': 'BẤM NÚT • hoặc SELECT / VIEW ×3',
        'chacha.boss.triple': 'SELECT / VIEW  {{count}}/{{max}}',
        'chacha.boss.active': 'CHACHA BOSS FORM • ĐANG KÍCH HOẠT',
        'chacha.boss.timer': 'Còn {{seconds}} giây',
        'chacha.boss.activated': 'ChaCha đã hấp thụ đủ cộng hưởng và chuyển sang Boss Form!',
    },
}.items():
    path = ROOT / 'i18n' / lang
    obj = json.loads(path.read_text(encoding='utf-8'))
    obj.update(values)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# ModEntry wiring + test commands.
s = read('ModEntry.cs')
if 'private ChaChaBossFormService ChaChaBossForm = null!;' not in s:
    s = replace_once(
        s,
        '    private BossEnergyService BossEnergy = null!;\n    private CombatService Combat = null!;\n',
        '    private BossEnergyService BossEnergy = null!;\n    private ChaChaBossFormService ChaChaBossForm = null!;\n    private CombatService Combat = null!;\n',
        'ModEntry ChaCha Boss field'
    )
    s = replace_once(
        s,
        '''        this.WorldActors = new WorldActorService(this.Monitor);\n        this.PortableMachine = new PortableMachineService(\n''',
        '''        this.WorldActors = new WorldActorService(this.Monitor);\n        this.ChaChaBossForm = new ChaChaBossFormService(\n            helper, this.Monitor, this.Save, this.BossEnergy, this.WorldActors\n        );\n        this.PortableMachine = new PortableMachineService(\n''',
        'ModEntry ChaCha Boss construction'
    )
    s = replace_once(
        s,
        '        helper.Events.GameLoop.DayStarted += this.BossEnergy.OnDayStarted;\n',
        '        helper.Events.GameLoop.DayStarted += this.BossEnergy.OnDayStarted;\n        helper.Events.GameLoop.DayStarted += this.ChaChaBossForm.OnDayStarted;\n',
        'ChaCha Boss day event'
    )
    s = replace_once(
        s,
        '        helper.Events.GameLoop.UpdateTicked += this.CardArena.OnUpdateTicked;\n',
        '        helper.Events.GameLoop.UpdateTicked += this.CardArena.OnUpdateTicked;\n        helper.Events.GameLoop.UpdateTicked += this.ChaChaBossForm.OnUpdateTicked;\n',
        'ChaCha Boss update event'
    )
    s = replace_once(
        s,
        '        helper.Events.GameLoop.ReturnedToTitle += this.BossEnergy.OnReturnedToTitle;\n',
        '        helper.Events.GameLoop.ReturnedToTitle += this.BossEnergy.OnReturnedToTitle;\n        helper.Events.GameLoop.ReturnedToTitle += this.ChaChaBossForm.OnReturnedToTitle;\n',
        'ChaCha Boss title event'
    )
    s = replace_once(
        s,
        '        helper.Events.Display.RenderedHud += this.CardLabOverlay.OnRenderedHud;\n',
        '        helper.Events.Display.RenderedHud += this.CardLabOverlay.OnRenderedHud;\n        helper.Events.Display.RenderedHud += this.ChaChaBossForm.OnRenderedHud;\n',
        'ChaCha Boss HUD event'
    )
    s = replace_once(
        s,
        '        helper.Events.Input.ButtonPressed += this.CardLabOverlay.OnButtonPressed;\n',
        '        helper.Events.Input.ButtonPressed += this.CardLabOverlay.OnButtonPressed;\n        helper.Events.Input.ButtonPressed += this.ChaChaBossForm.OnButtonPressed;\n',
        'ChaCha Boss input event'
    )
    s = replace_once(
        s,
        '        helper.ConsoleCommands.Add("cardcha_card_auto_run", "TEST ONLY: run deterministic runtime scenarios for all 76 active cards.", this.CommandCardAutoRun);\n',
        '        helper.ConsoleCommands.Add("cardcha_card_auto_run", "TEST ONLY: run deterministic runtime scenarios for all 76 active cards.", this.CommandCardAutoRun);\n        helper.ConsoleCommands.Add("cardcha_chacha_boss_ready", "TEST ONLY: fill Boss Energy to 100 so the ChaCha activation UI can be tested.", this.CommandChaChaBossReady);\n        helper.ConsoleCommands.Add("cardcha_chacha_boss_status", "Show ChaCha Boss Form runtime state.", this.CommandChaChaBossStatus);\n',
        'ChaCha Boss commands registration'
    )

# End transient form before Stardew serializes locations.
s = replace_once(
    s,
    '        this.Combat.PrepareForGameSave();\n        // ChaCha is a runtime-only world actor;',
    '        this.Combat.PrepareForGameSave();\n        this.ChaChaBossForm.OnSaving();\n        // ChaCha is a runtime-only world actor;',
    'ChaCha Boss save cleanup'
)

# Add explicit commands before CommandVersion.
if 'private void CommandChaChaBossReady' not in s:
    s = replace_once(
        s,
        '    private void CommandVersion(string command, string[] args)\n',
        '''    private void CommandChaChaBossReady(string command, string[] args)\n    {\n        if (!Context.IsWorldReady)\n        {\n            this.Monitor.Log("Load a save before priming ChaCha Boss Form.", LogLevel.Warn);\n            return;\n        }\n\n        this.ChaChaBossForm.DebugPrimeReady();\n        this.Monitor.Log("ChaCha Boss Form TEST primed to 100 Boss Energy. Use the flashing button or Select/View x3.", LogLevel.Alert);\n    }\n\n    private void CommandChaChaBossStatus(string command, string[] args)\n    {\n        this.Monitor.Log("===== CHACHA BOSS FORM =====\\n" + this.ChaChaBossForm.Describe(), LogLevel.Alert);\n    }\n\n    private void CommandVersion(string command, string[] args)\n''',
        'ChaCha Boss command methods'
    )

s = s.replace(
    'Cardcha! v0.3.0-alpha.28.0.4.14.3.8 BOSS ENERGY + VICTORY CHARGE TEST',
    f'Cardcha! v{VERSION} CHACHA BOSS FORM FOUNDATION TEST'
)
write('ModEntry.cs', s)

print(f'Applied ChaCha Boss Form foundation {VERSION}')
