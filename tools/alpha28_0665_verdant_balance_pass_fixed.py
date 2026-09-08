from pathlib import Path
import json

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.32'
PREV = '0.3.0-alpha.28.0.4.14.4.5.12.31'

# Version.
manifest_path = ROOT / 'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['Version'] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for rel in ['Cardcha.csproj', 'Directory.Build.targets']:
    p = ROOT / rel
    p.write_text(p.read_text(encoding='utf-8').replace(PREV, VERSION), encoding='utf-8')

# Verdant Guardian fight balance.
boss_path = ROOT / 'Services' / 'VerdantGuardianBossService.cs'
boss = boss_path.read_text(encoding='utf-8')
old = '    private const int BossMaxHealth = 1300;\n'
new = '''    // 0665 Region I balance candidate. Phase 1 teaches the moves, Phase 2/3 add pressure.
    private const int BossMaxHealth = 1600;
    private const int SwipeDamageP1 = 10;
    private const int SwipeDamageP2 = 12;
    private const int SwipeDamageP3 = 14;
    private const int RootDamageP1 = 8;
    private const int RootDamageP2 = 10;
    private const int RootDamageP3 = 12;
    private const int ChargeDamageP1 = 14;
    private const int ChargeDamageP2 = 16;
    private const int ChargeDamageP3 = 19;
    private const int VineDamageP1 = 4;
    private const int VineDamageP2 = 5;
    private const int VineDamageP3 = 7;
    private const int SlamDamageP1 = 16;
    private const int SlamDamageP2 = 18;
    private const int SlamDamageP3 = 22;
    private const float HeavyRecoilCapPixels = 18f;
    private const float HeavyRecenterFactor = 0.22f;
'''
assert old in boss
boss = boss.replace(old, new, 1)

old = '''        // Colossus weight: normal attacks cannot shove the boss around. Only Cardcha-owned
        // movement (Charge or phase recenter) changes HeavyAnchor.
        if (this.State != VerdantGuardianState.Charging && this.State != VerdantGuardianState.PhaseTransition)
            boss.Position = this.HeavyAnchor;
'''
new = '''        // 0665 heavy-body tuning: allow a tiny hit reaction, but never cumulative wall-pinning.
        // HeavyAnchor only moves through Cardcha-owned motion (Charge/phase recenter).
        if (this.State != VerdantGuardianState.Charging && this.State != VerdantGuardianState.PhaseTransition)
            this.ApplyHeavyRecoil(boss);
'''
assert old in boss
boss = boss.replace(old, new, 1)

for old, new in {
    'DamagePlayer(10, boss)': 'DamagePlayer(PhaseDamage(SwipeDamageP1, SwipeDamageP2, SwipeDamageP3, this.Phase), boss)',
    'DamagePlayer(8, boss)': 'DamagePlayer(PhaseDamage(RootDamageP1, RootDamageP2, RootDamageP3, this.Phase), boss)',
    'DamagePlayer(14, boss)': 'DamagePlayer(PhaseDamage(ChargeDamageP1, ChargeDamageP2, ChargeDamageP3, this.Phase), boss)',
    'DamagePlayer(4, boss)': 'DamagePlayer(PhaseDamage(VineDamageP1, VineDamageP2, VineDamageP3, this.Phase), boss)',
    'DamagePlayer(16, boss)': 'DamagePlayer(PhaseDamage(SlamDamageP1, SlamDamageP2, SlamDamageP3, this.Phase), boss)',
}.items():
    assert old in boss, old
    boss = boss.replace(old, new, 1)

for old, new in [
    ('add.MaxHealth = this.Phase switch { 1 => 38, 2 => 52, _ => 68 };', 'add.MaxHealth = this.Phase switch { 1 => 34, 2 => 46, _ => 58 };'),
    ('add.Speed = this.Phase switch { 1 => 4, 2 => 5, _ => 6 };', 'add.Speed = this.Phase switch { 1 => 4, 2 => 5, _ => 5 };'),
    ('add.MaxHealth = this.Phase switch { 1 => 55, 2 => 75, _ => 95 };', 'add.MaxHealth = this.Phase switch { 1 => 50, 2 => 68, _ => 84 };'),
]:
    assert old in boss, old
    boss = boss.replace(old, new, 1)

old = '''    private static int CooldownMs(VerdantGuardianAttack attack, int phase) => attack switch
    {
        VerdantGuardianAttack.Swipe => phase switch { 1 => 2200, 2 => 1800, _ => 1500 },
        VerdantGuardianAttack.RootSpikes => phase switch { 1 => 5200, 2 => 4500, _ => 3600 },
        VerdantGuardianAttack.SummonAdds => phase switch { 1 => 16000, 2 => 14000, _ => 12500 },
        VerdantGuardianAttack.Charge => phase == 2 ? 7000 : 5600,
        VerdantGuardianAttack.VineTrap => phase == 2 ? 8500 : 6500,
        VerdantGuardianAttack.AreaSlam => 7200,
        _ => 2500
    };

    private static int DecisionGapMs(int phase) => phase switch { 1 => 700, 2 => 550, _ => 400 };
'''
new = '''    private static int CooldownMs(VerdantGuardianAttack attack, int phase) => attack switch
    {
        // Slightly more breathing room than the raw prototype. Pressure still rises each phase,
        // but the player should read the animation rather than get chain-locked by attack roulette.
        VerdantGuardianAttack.Swipe => phase switch { 1 => 2400, 2 => 2000, _ => 1700 },
        VerdantGuardianAttack.RootSpikes => phase switch { 1 => 5600, 2 => 4800, _ => 4000 },
        VerdantGuardianAttack.SummonAdds => phase switch { 1 => 17000, 2 => 14500, _ => 13000 },
        VerdantGuardianAttack.Charge => phase == 2 ? 7200 : 6000,
        VerdantGuardianAttack.VineTrap => phase == 2 ? 8800 : 7000,
        VerdantGuardianAttack.AreaSlam => 7600,
        _ => 2600
    };

    private static int DecisionGapMs(int phase) => phase switch { 1 => 750, 2 => 600, _ => 450 };
'''
assert old in boss
boss = boss.replace(old, new, 1)

anchor = '    private static Point[] BuildRootTargets(Point center, int phase)\n'
assert anchor in boss
helpers = '''    private void ApplyHeavyRecoil(Monster boss)
    {
        Vector2 displacement = boss.Position - this.HeavyAnchor;
        float length = displacement.Length();
        if (length <= 0.05f)
        {
            boss.Position = this.HeavyAnchor;
            return;
        }

        if (length > HeavyRecoilCapPixels)
            displacement = displacement / length * HeavyRecoilCapPixels;

        Vector2 clamped = this.HeavyAnchor + displacement;
        boss.Position = Vector2.Lerp(clamped, this.HeavyAnchor, HeavyRecenterFactor);
    }

    private static int PhaseDamage(int p1, int p2, int p3, int phase)
        => phase <= 1 ? p1 : phase == 2 ? p2 : p3;

    public string DescribeBalance()
        => $"0665 Region I Balance | HP={BossMaxHealth} | Damage P1/P2/P3: Swipe={SwipeDamageP1}/{SwipeDamageP2}/{SwipeDamageP3}, " +
           $"Root={RootDamageP1}/{RootDamageP2}/{RootDamageP3}, Charge={ChargeDamageP1}/{ChargeDamageP2}/{ChargeDamageP3}, " +
           $"Vine={VineDamageP1}/{VineDamageP2}/{VineDamageP3}, Slam={SlamDamageP1}/{SlamDamageP2}/{SlamDamageP3} | " +
           $"HeavyRecoilCap={HeavyRecoilCapPixels:0}px Recenter={HeavyRecenterFactor:0.00} | AddsMax={MaxActiveAdds}";

'''
boss = boss.replace(anchor, helpers + anchor, 1)
boss = boss.replace('return $"Arena={this.IsInArena} | State={this.State} | Phase={this.Phase} | HP={hp} | Adds=[{adds}] | Cleared=',
                    'return $"Arena={this.IsInArena} | State={this.State} | Phase={this.Phase} | HP={hp} | Balance=0665 | Adds=[{adds}] | Cleared=', 1)
boss_path.write_text(boss, encoding='utf-8')

# Knockback: strong resistance with tiny visible recoil, instead of absolute immunity.
patch_path = ROOT / 'Patches' / 'MonsterDamagePatch.cs'
patch = patch_path.read_text(encoding='utf-8')
anchor = '    private static CardTestArenaService? TestArena;\n'
assert anchor in patch
patch = patch.replace(anchor, anchor + '    private const double VerdantGuardianKnockbackScale = 0.08d;\n    private const int VerdantGuardianKnockbackCap = 12;\n', 1)
old = '''            // Boss I Colossus pass: weapon/team trajectories do not launch the Guardian.
            if (__instance.modData.ContainsKey(VerdantGuardianBossService.BossMarkerKey))
            {
                xTrajectory = 0;
                yTrajectory = 0;
            }

            if (Combat is not null)
            {
                damage = Combat.ModifyMonsterDamage(__instance, damage, isBomb, who);
                TestArena?.ClampMainDummyDamage(__instance, ref damage);
                Combat.ModifyMonsterTrajectory(ref xTrajectory, ref yTrajectory, isBomb, who);
            }
'''
new = '''            bool isVerdantGuardian = __instance.modData.ContainsKey(VerdantGuardianBossService.BossMarkerKey);

            if (Combat is not null)
            {
                damage = Combat.ModifyMonsterDamage(__instance, damage, isBomb, who);
                TestArena?.ClampMainDummyDamage(__instance, ref damage);
                Combat.ModifyMonsterTrajectory(ref xTrajectory, ref yTrajectory, isBomb, who);
            }

            // 0665: receive 8% of final trajectory, then hard-cap it. The boss service recenters
            // toward HeavyAnchor, so repeated party hits cannot walk the Guardian into a wall.
            if (isVerdantGuardian)
            {
                xTrajectory = Math.Clamp((int)Math.Round(xTrajectory * VerdantGuardianKnockbackScale), -VerdantGuardianKnockbackCap, VerdantGuardianKnockbackCap);
                yTrajectory = Math.Clamp((int)Math.Round(yTrajectory * VerdantGuardianKnockbackScale), -VerdantGuardianKnockbackCap, VerdantGuardianKnockbackCap);
            }
'''
assert old in patch
patch = patch.replace(old, new, 1)
patch_path.write_text(patch, encoding='utf-8')

# Guardian Rabbit.
form_path = ROOT / 'Services' / 'ChaChaBossFormService.cs'
form = form_path.read_text(encoding='utf-8')
assert '    public const int GuardianRootPulseDamage = 18;\n' in form
form = form.replace('    public const int GuardianRootPulseDamage = 18;\n', '    public const int GuardianRootPulseDamage = 14;\n', 1)
form_path.write_text(form, encoding='utf-8')

# Verdant Core.
card_path = ROOT / 'Services' / 'BossCardService.cs'
card = card_path.read_text(encoding='utf-8')
assert '    public const double VerdantDamageReduction = 0.35d;\n' in card
assert '    public const int VerdantCooldownMs = 24000;\n' in card
card = card.replace('    public const double VerdantDamageReduction = 0.35d;\n', '    public const double VerdantDamageReduction = 0.30d;\n', 1)
card = card.replace('    public const int VerdantCooldownMs = 24000;\n', '    public const int VerdantCooldownMs = 28000;\n', 1)
card_path.write_text(card, encoding='utf-8')

# Descriptions stay truthful.
def patch_json(path, changes):
    data = json.loads(path.read_text(encoding='utf-8'))
    data.update(changes)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

patch_json(ROOT/'i18n/default.json', {
    'boss.card.verdant_core.desc': 'When a hit would leave you at or below 50% HP, Verdant Guard awakens for 6s: take 30% less damage and recover 2 HP each second. 28s cooldown.',
    'chacha.boss.guardian.desc': 'ChaCha channels Verdant Guardian resonance for 10 seconds. Every 2 seconds, roots pulse around ChaCha for 14 damage to nearby monsters.'
})
patch_json(ROOT/'i18n/vi.json', {
    'boss.card.verdant_core.desc': 'Khi một đòn đánh sắp khiến HP còn 50% hoặc thấp hơn, Verdant Guard thức tỉnh trong 6 giây: giảm 30% sát thương nhận vào và hồi 2 HP mỗi giây. Hồi chiêu 28 giây.',
    'chacha.boss.guardian.desc': 'ChaCha cộng hưởng với Verdant Guardian trong 10 giây. Cứ mỗi 2 giây, rễ cây phát xung quanh ChaCha, gây 14 sát thương lên quái gần đó.'
})

# ModEntry debug/version.
mod_path = ROOT / 'ModEntry.cs'
mod = mod_path.read_text(encoding='utf-8')
command_anchor = '        helper.ConsoleCommands.Add("cardcha_boss1_polish_status", "Show Verdant arena cinematic/camera/sound polish state.", (_, _) => this.Monitor.Log(this.VerdantArenaPolish.Describe(), LogLevel.Alert));\n'
assert command_anchor in mod
mod = mod.replace(command_anchor, command_anchor + '        helper.ConsoleCommands.Add("cardcha_boss1_balance_status", "Show the 0665 Region I Boss balance profile.", (_, _) => this.Monitor.Log(this.VerdantGuardian.DescribeBalance() + "\\n" + this.BossCards.Describe() + "\\n" + this.ChaChaBossForm.Describe(), LogLevel.Alert));\n', 1)
old_version_line = '0.3.0-alpha.28.0.4.14.4.5.12.31 VERDANT ARENA CINEMATIC POLISH TEST'
assert old_version_line in mod
mod = mod.replace(old_version_line, '0.3.0-alpha.28.0.4.14.4.5.12.32 VERDANT REGION I BALANCE PASS TEST', 1)
mod_path.write_text(mod, encoding='utf-8')

# Handoff.
Path('handoff/ALPHA28_0665_VERDANT_REGION1_BALANCE_PASS.md').write_text(f'''# Alpha28 0665 - Verdant Region I Balance Pass\n\nBuild: `{VERSION}`\nBranch: `cardcha-alpha28-0665-verdant-balance-pass`\nStatus: balance candidate; in-game acceptance for 0660-0665 remains pending.\n\n## Verdant Guardian\n- HP: 1300 -> 1600 (+23%, deliberately not doubled).\n- Phase damage: Swipe 10/12/14; Root 8/10/12; Charge 14/16/19; Vine 4/5/7; Slam 16/18/22.\n- Cooldowns/decision gaps are slightly more readable; telegraph and animation timings are unchanged.\n\n## Heavy body\n- 8% final knockback, 12 trajectory cap.\n- 18 px recoil envelope, then recenter to HeavyAnchor.\n- Charge and phase recenter remain the only ways HeavyAnchor itself moves, preventing team wall-pinning.\n\n## Summons\n- Briarling HP 50/68/84, speed 2/3/3.\n- Leaf Wisp HP 34/46/58, speed 4/5/5.\n- Max active adds remains 4; 0663 species/composition is unchanged.\n\n## Guardian Rabbit\n- Duration 10s, pulse every 2s, radius 176 px unchanged.\n- Root Pulse damage 18 -> 14.\n- Boss Energy cost 100 and gain x1/3 unchanged.\n\n## Verdant Core\n- Trigger 50% projected HP, duration 6s, regen 2 HP/s unchanged.\n- Damage reduction 35% -> 30%.\n- Cooldown 24s -> 28s.\n\n## Debug\n- `cardcha_boss1_balance_status`\n\n## Locked systems preserved\nSave schema 19, 20/40/60/80 milestones, 76 active normal cards / 80 stored IDs, 0659 MiMi stair resolver, MiMi profile/CC continuity, Region I Hunt Run 4-of-6, 0660 visuals, 0663 custom summon art, 0664 arena/camera/sound polish, Airship route/upgrades, controller mapping and Forest gate are unchanged.\n''', encoding='utf-8')
Path('handoff/LATEST_CARDCHA_HANDOFF.md').write_text(f'''# Latest Cardcha handoff\n\nCurrent branch: `cardcha-alpha28-0665-verdant-balance-pass`\nCurrent build: `{VERSION}`\n\nContinue from:\n`handoff/ALPHA28_0665_VERDANT_REGION1_BALANCE_PASS.md`\n\n0660-0665 in-game acceptance is pending. Do not resume from stale `main`.\n''', encoding='utf-8')

print(json.dumps({
    'version': VERSION,
    'bossHP': 1600,
    'damage': {'swipe':[10,12,14], 'root':[8,10,12], 'charge':[14,16,19], 'vine':[4,5,7], 'slam':[16,18,22]},
    'knockback': {'scale':0.08, 'trajectoryCap':12, 'recoilCapPixels':18},
    'guardianRabbitDamage': 14,
    'verdantCore': {'reduction':0.30, 'durationSec':6, 'regenPerSec':2, 'cooldownSec':28},
    'schema': 19
}, indent=2))
