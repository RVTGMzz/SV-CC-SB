#!/usr/bin/env python3
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageOps

OLD='0.3.0-alpha.28.0.4.14.4.5.12.48'
NEW='0.3.0-alpha.28.0.4.14.4.5.12.49'
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'src'/'Cardcha'


def repl(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f'0681 anchor missing: {label}')
    return text.replace(old,new,1)

# -----------------------------------------------------------------------------
# Runtime record DTO. Runtime-only by design, so save schema remains 19.
# -----------------------------------------------------------------------------
record_path=SRC/'Services'/'CuratorRunRecord.cs'
record_path.write_text(r'''namespace Cardcha.Services;

/// <summary>
/// Runtime-only summary of a Region II Forgotten Archive run.
/// It is handed to Hollow Curator at the Archive Seal and deliberately is not persisted,
/// so the boss reflects the run the player just completed without changing save schema.
/// </summary>
internal sealed class CuratorRunRecord
{
    public string Tag { get; }
    public int Risk { get; }
    public int Precision { get; }
    public int Pressure { get; }
    public int Recovery { get; }
    public int Mirror { get; }
    public int NodesReached { get; }
    public bool DebugMode { get; }

    public CuratorRunRecord(string tag, int risk, int precision, int pressure, int recovery, int mirror, int nodesReached, bool debugMode = false)
    {
        this.Tag = NormalizeTag(tag);
        this.Risk = Math.Max(0, risk);
        this.Precision = Math.Max(0, precision);
        this.Pressure = Math.Max(0, pressure);
        this.Recovery = Math.Max(0, recovery);
        this.Mirror = Math.Max(0, mirror);
        this.NodesReached = Math.Max(0, nodesReached);
        this.DebugMode = debugMode;
    }

    public static CuratorRunRecord Neutral => new("neutral", 0, 0, 0, 0, 0, 0);

    public static CuratorRunRecord Debug(string? tag)
    {
        string normalized = NormalizeTag(tag);
        return normalized switch
        {
            "risk" => new(normalized, 4, 1, 1, 0, 0, 6, true),
            "precision" => new(normalized, 0, 4, 0, 0, 0, 6, true),
            "pressure" => new(normalized, 1, 0, 4, 0, 0, 6, true),
            "recovery" => new(normalized, 0, 0, 1, 4, 0, 6, true),
            "mirror" => new(normalized, 0, 1, 0, 0, 4, 6, true),
            _ => new("neutral", 0, 0, 0, 0, 0, 6, true),
        };
    }

    public string Describe()
        => $"tag={this.Tag}, nodes={this.NodesReached}, risk={this.Risk}, precision={this.Precision}, pressure={this.Pressure}, recovery={this.Recovery}, mirror={this.Mirror}, debug={this.DebugMode}";

    private static string NormalizeTag(string? tag)
    {
        string value = (tag ?? "neutral").Trim().ToLowerInvariant();
        return value is "risk" or "precision" or "pressure" or "recovery" or "mirror" ? value : "neutral";
    }
}
''',encoding='utf-8')

# -----------------------------------------------------------------------------
# Region II: transfer the accumulated record into the boss before warping.
# -----------------------------------------------------------------------------
p=SRC/'Services'/'Region2RoguelikeRunService.cs'
t=p.read_text(encoding='utf-8')
t=repl(t,
'''    private Func<string>? BossGateAction;\n    private Func<string>? BossGateDebugAction;''',
'''    private Func<string>? BossGateAction;\n    private Func<string>? BossGateDebugAction;\n    private Action<CuratorRunRecord>? CuratorRecordSink;''',
'record sink field')
t=repl(t,
'''    public void BindBossGateHandlers(Func<string> realHandler, Func<string> debugHandler)\n    {\n        this.BossGateAction = realHandler;\n        this.BossGateDebugAction = debugHandler;\n    }\n\n    public void OnSaveLoaded''',
'''    public void BindBossGateHandlers(Func<string> realHandler, Func<string> debugHandler)\n    {\n        this.BossGateAction = realHandler;\n        this.BossGateDebugAction = debugHandler;\n    }\n\n    public void BindCuratorRecordSink(Action<CuratorRunRecord> sink)\n        => this.CuratorRecordSink = sink;\n\n    public void OnSaveLoaded''',
'record sink bind')
t=repl(t,
'''        this.LastCuratorRecord = debug ? "debug" : this.CurrentRecordTag();\n        this.BankAllRemaining();\n        this.LeavingForBoss = true;\n        string result = handler();''',
'''        CuratorRunRecord record = this.BuildCuratorRunRecord(debug);\n        this.CuratorRecordSink?.Invoke(record);\n        this.BankAllRemaining();\n        this.LeavingForBoss = true;\n        string result = handler();''',
'gate transfers record')
t=repl(t,
'''        this.Active = false;\n        this.Monitor.Log($"0680 Region II -> Hollow Curator. Curator record={this.LastCuratorRecord}.", LogLevel.Info);''',
'''        this.LastCuratorRecord = record.Tag;\n        this.Active = false;\n        this.Monitor.Log($"0681 Region II -> Hollow Curator. Transferred {record.Describe()}.", LogLevel.Info);''',
'gate transfer log')
t=repl(t,
'''    private string CurrentRecordTag()\n    {''',
'''    private CuratorRunRecord BuildCuratorRunRecord(bool debug)\n    {\n        if (debug)\n            return CuratorRunRecord.Debug("neutral");\n        return new CuratorRunRecord(\n            this.CurrentRecordTag(),\n            this.RiskRecord,\n            this.PrecisionRecord,\n            this.PressureRecord,\n            this.RecoveryRecord,\n            this.MirrorRecord,\n            this.CurrentNode\n        );\n    }\n\n    private string CurrentRecordTag()\n    {''',
'build record method')
t=t.replace('0680 Region II Rogue:', '0681 Region II Rogue:')
p.write_text(t,encoding='utf-8')

# -----------------------------------------------------------------------------
# Hollow Curator: consume record and reflect it through phase 2/3 attacks + visuals.
# -----------------------------------------------------------------------------
p=SRC/'Services'/'MilestoneBossService.cs'
t=p.read_text(encoding='utf-8')
t=repl(t,
'''    private int CuratorAdaptationStacks;\n    private int DecisionSerial;''',
'''    private int CuratorAdaptationStacks;\n    private CuratorRunRecord PendingCuratorRecord = CuratorRunRecord.Neutral;\n    private CuratorRunRecord ActiveCuratorRecord = CuratorRunRecord.Neutral;\n    private bool HasPendingCuratorRecord;\n    private bool CuratorRecordRevealed;\n    private int DecisionSerial;''',
'curator record fields')
t=repl(t,
'''    public void BindExpeditionRouteHandler(Func<int, int, string, string> handler)\n        => this.ExpeditionRouteAction = handler;\n\n    public bool IsInArena''',
'''    public void BindExpeditionRouteHandler(Func<int, int, string, string> handler)\n        => this.ExpeditionRouteAction = handler;\n\n    public void SetNextHollowCuratorRecord(CuratorRunRecord record)\n    {\n        this.PendingCuratorRecord = record ?? CuratorRunRecord.Neutral;\n        this.HasPendingCuratorRecord = true;\n        this.Monitor.Log($"0681 Hollow Curator pending run record: {this.PendingCuratorRecord.Describe()}.", LogLevel.Trace);\n    }\n\n    public string DebugEnterBoss2WithRecord(string? tag)\n    {\n        CuratorRunRecord record = CuratorRunRecord.Debug(tag);\n        this.SetNextHollowCuratorRecord(record);\n        return this.DebugEnterBoss(2) + $" Curator record={record.Tag}.";\n    }\n\n    public bool IsInArena''',
'curator public record api')
t=repl(t,
'''        return $"0679 MilestoneBoss | Current={current} | State={this.State} | Phase={this.Phase} | HP={hp}/{max} | " +\n               $"CuratorAdapt={this.CuratorAdaptationStacks}/3 | BossCards=[{string.Join(',', this.Save.Data.BossCardsUnlocked ?? new HashSet<string>())}] | " +''',
'''        return $"0681 MilestoneBoss | Current={current} | State={this.State} | Phase={this.Phase} | HP={hp}/{max} | " +\n               $"CuratorAdapt={this.CuratorAdaptationStacks}/3 | CuratorRecord={this.ActiveCuratorRecord.Describe()} | BossCards=[{string.Join(',', this.Save.Data.BossCardsUnlocked ?? new HashSet<string>())}] | " +''',
'describe record')
t=repl(t,
'''        this.CuratorAdaptationStacks = 0;\n        this.DecisionSerial = 0;''',
'''        this.CuratorAdaptationStacks = 0;\n        if (kind == MilestoneBossKind.HollowCurator)\n        {\n            this.ActiveCuratorRecord = this.HasPendingCuratorRecord ? this.PendingCuratorRecord : CuratorRunRecord.Neutral;\n            this.PendingCuratorRecord = CuratorRunRecord.Neutral;\n            this.HasPendingCuratorRecord = false;\n        }\n        else\n        {\n            this.ActiveCuratorRecord = CuratorRunRecord.Neutral;\n        }\n        this.CuratorRecordRevealed = false;\n        this.DecisionSerial = 0;''',
'start encounter consumes record')
t=repl(t,
'''            case MilestoneBossKind.HollowCurator:\n            {\n                int[] pool = this.Phase switch\n                {\n                    1 => new[] { 0, 0, 1 },\n                    2 => new[] { 0, 1, 2, 4, 4 },\n                    _ => new[] { 0, 2, 3, 4, 4 },\n                };\n                this.CurrentAttack = pool[this.Rng.Next(pool.Length)];\n                this.MaybeTeleportPrimary("curator");\n                break;\n            }''',
'''            case MilestoneBossKind.HollowCurator:\n            {\n                int recordAttack = this.CuratorRecordAttackId();\n                int[] pool = this.Phase switch\n                {\n                    1 => new[] { 0, 0, 1 },\n                    2 => new[] { 0, 1, 2, 4, recordAttack, recordAttack },\n                    _ => new[] { 0, 2, 3, 4, recordAttack, recordAttack, recordAttack },\n                };\n                this.CurrentAttack = pool[this.Rng.Next(pool.Length)];\n                if (this.CurrentAttack == 5)\n                {\n                    this.AttackTargetTile2 = ClampArenaTile(new Point(\n                        this.AttackTargetTile.X + (this.DecisionSerial % 2 == 0 ? 3 : -3),\n                        this.AttackTargetTile.Y\n                    ));\n                }\n                else if (this.CurrentAttack == 9)\n                {\n                    this.AttackTargetTile2 = ClampArenaTile(new Point(\n                        this.AttackTargetTile.X + (this.DecisionSerial % 2 == 0 ? 2 : -2),\n                        this.AttackTargetTile.Y + (this.DecisionSerial % 3 == 0 ? 2 : -1)\n                    ));\n                }\n                this.MaybeTeleportPrimary("curator");\n                break;\n            }''',
'curator record attack pool')
t=repl(t,
'''            case 4:\n                if (PlayerWithin(this.EchoTargetTile, 1.8f) || PlayerWithin(this.EchoTargetTile2, 1.25f))\n                    DamagePlayer(17 + this.Phase * 2 + extra);\n                Game1.playSound("wand");\n                break;\n\n            case 10:''',
'''            case 4:\n                if (PlayerWithin(this.EchoTargetTile, 1.8f) || PlayerWithin(this.EchoTargetTile2, 1.25f))\n                    DamagePlayer(17 + this.Phase * 2 + extra);\n                Game1.playSound("wand");\n                break;\n            case 5: // RISK: two collapsing archive zones, strong but clearly telegraphed.\n                if (PlayerWithin(this.AttackTargetTile, 2.15f) || PlayerWithin(this.AttackTargetTile2, 1.25f))\n                    DamagePlayer(20 + this.Phase + extra);\n                Game1.playSound("thudStep");\n                break;\n            case 6: // PRECISION: narrow current + remembered strike.\n                if (PlayerWithin(this.AttackTargetTile, 0.95f) || PlayerWithin(this.EchoTargetTile, 0.95f))\n                    DamagePlayer(22 + extra);\n                Game1.playSound("Cowboy_gunload");\n                break;\n            case 7: // PRESSURE: wider, lower-damage compression pulse.\n                if (PlayerWithin(this.AttackTargetTile, 2.65f))\n                    DamagePlayer(18 + this.Phase + extra);\n                Game1.playSound("thudStep");\n                break;\n            case 8: // RECOVERY: Curator reflects restoration without disabling player healing.\n            {\n                Monster? curator = this.FindRole("curator", false);\n                if (curator is not null)\n                    curator.Health = Math.Min(curator.MaxHealth, curator.Health + 55 + this.CuratorAdaptationStacks * 10);\n                if (PlayerWithin(this.AttackTargetTile, 1.35f))\n                    DamagePlayer(10 + extra);\n                Game1.playSound("healSound");\n                break;\n            }\n            case 9: // MIRROR: current + secondary + previous position echo.\n                if (PlayerWithin(this.AttackTargetTile, 1.55f)\n                    || PlayerWithin(this.AttackTargetTile2, 1.25f)\n                    || PlayerWithin(this.EchoTargetTile, 1.25f))\n                    DamagePlayer(18 + this.Phase + extra);\n                Game1.playSound("wand");\n                break;\n\n            case 10:''',
'curator record attacks')
t=repl(t,
'''        this.PendingPhase = nextPhase;\n        this.State = MilestoneBossState.PhaseTransition;''',
'''        this.PendingPhase = nextPhase;\n        if (this.CurrentKind == MilestoneBossKind.HollowCurator && nextPhase == 2 && !this.CuratorRecordRevealed)\n        {\n            this.CuratorRecordRevealed = true;\n            Game1.showGlobalMessage(ModEntry.T("boss.curator.record.reveal", new { record = this.CuratorRecordShort() }));\n        }\n        this.State = MilestoneBossState.PhaseTransition;''',
'reveal record phase2')
t=repl(t,
'''        1 => 900,\n        3 => 1050,\n        4 => 880,\n        10 => 720,''',
'''        1 => 900,\n        3 => 1050,\n        4 => 880,\n        5 => 980,\n        6 => 1150,\n        7 => 1050,\n        8 => 1050,\n        9 => 1000,\n        10 => 720,''',
'curator record telegraph timings')
# Replace curator actor frame selection with 18-frame, 9-family state mapping.
t=repl(t,
'''        if (role == "curator")\n        {\n            texture = this.Helper.ModContent.Load<Texture2D>(HollowCuratorTexturePath);\n            int frame = this.State == MilestoneBossState.PhaseTransition ? 2\n                : this.Phase >= 3 ? 3\n                : this.State == MilestoneBossState.Telegraph ? 1\n                : 0;\n            source = new Rectangle(frame * 48, 0, 48, 64);\n            scale = 1.95f;\n            offset = new Vector2(0f, 6f);\n        }''',
'''        if (role == "curator")\n        {\n            texture = this.Helper.ModContent.Load<Texture2D>(HollowCuratorTexturePath);\n            int family = this.CuratorAnimationFamily();\n            int anim = (int)((Environment.TickCount64 / 190L + this.DecisionSerial) & 1L);\n            int frame = family * 2 + anim;\n            source = new Rectangle(frame * 48, 0, 48, 64);\n            scale = 1.95f;\n            float hover = this.State is MilestoneBossState.Intro or MilestoneBossState.Decision\n                ? (float)Math.Sin(Environment.TickCount64 / 240d) * 2f\n                : 0f;\n            offset = new Vector2(0f, 6f + hover);\n        }''',
'curator 18 frame draw')
# Telegraph special handling.
t=repl(t,
'''        int radius = this.CurrentAttack switch\n        {\n            3 or 25 or 28 => 2,\n            13 or 24 or 27 => 2,\n            _ => 1,\n        };''',
'''        int radius = this.CurrentAttack switch\n        {\n            3 or 5 or 7 or 25 or 28 => 2,\n            13 or 24 or 27 => 2,\n            _ => 1,\n        };''',
'record attack telegraph radius')
t=repl(t,
'''        if (this.CurrentAttack is 4 or 26)\n        {''',
'''        if (this.CurrentAttack == 6)\n        {\n            Color precision = new Color(185, 224, 255) * (pulse + 0.08f);\n            DrawTileZone(batch, this.AttackTargetTile, 0, precision);\n            DrawTileZone(batch, this.EchoTargetTile, 0, precision * 0.78f);\n            return;\n        }\n\n        if (this.CurrentAttack is 4 or 26)\n        {''',
'precision telegraph')
t=repl(t,
'''        if (this.CurrentAttack == 27)\n            c = this.TricolorCycle(this.MimiCadenceIndex);\n\n        DrawTileZone(batch, this.AttackTargetTile, radius, c * pulse);''',
'''        if (this.CurrentAttack == 27)\n            c = this.TricolorCycle(this.MimiCadenceIndex);\n        else if (this.CurrentKind == MilestoneBossKind.HollowCurator && this.CurrentAttack is >= 5 and <= 9)\n            c = this.CuratorRecordColor();\n\n        DrawTileZone(batch, this.AttackTargetTile, radius, c * pulse);''',
'record telegraph color')
t=repl(t,
'''        if (this.CurrentAttack is 2 or 12 or 13 or 15 or 22 or 24 or 27 or 28)\n            DrawTileZone(batch, this.AttackTargetTile2, 1, new Color(238, 218, 255) * pulse);\n\n        if (this.CurrentAttack is 14 or 28)''',
'''        if (this.CurrentAttack is 2 or 5 or 9 or 12 or 13 or 15 or 22 or 24 or 27 or 28)\n            DrawTileZone(batch, this.AttackTargetTile2, 1, new Color(238, 218, 255) * pulse);\n\n        if (this.CurrentAttack is 9 or 14 or 28)\n            DrawTileZone(batch, this.EchoTargetTile, 1, new Color(190, 166, 255) * pulse);\n        else if (this.CurrentAttack is 14 or 28)''',
'record extra zones')
# Above replacement introduces unreachable else-if for 14/28 but harmless; normalize it cleanly.
t=t.replace('''        if (this.CurrentAttack is 9 or 14 or 28)\n            DrawTileZone(batch, this.EchoTargetTile, 1, new Color(190, 166, 255) * pulse);\n        else if (this.CurrentAttack is 14 or 28)\n            DrawTileZone(batch, this.EchoTargetTile, 1, new Color(190, 166, 255) * pulse);''',
'''        if (this.CurrentAttack is 9 or 14 or 28)\n            DrawTileZone(batch, this.EchoTargetTile, 1, new Color(190, 166, 255) * pulse);''')
# Curator aura follows the recorded family.
t=repl(t,
'''                "mimi" => new Color(199, 139, 218),\n                _ => new Color(166, 190, 232),''',
'''                "mimi" => new Color(199, 139, 218),\n                "curator" => this.CuratorRecordColor(),\n                _ => new Color(166, 190, 232),''',
'curator record aura color')
# HUD phase text includes a short, localized record tag.
t=repl(t,
'''                1 => $"Observation • Adapt {this.CuratorAdaptationStacks}/3",\n                2 => $"Reflection • Adapt {this.CuratorAdaptationStacks}/3",\n                _ => $"Curator's Truth • Adapt {this.CuratorAdaptationStacks}/3",''',
'''                1 => $"Observation • {this.CuratorRecordShort()} • Adapt {this.CuratorAdaptationStacks}/3",\n                2 => $"Reflection • {this.CuratorRecordShort()} • Adapt {this.CuratorAdaptationStacks}/3",\n                _ => $"Curator's Truth • {this.CuratorRecordShort()} • Adapt {this.CuratorAdaptationStacks}/3",''',
'curator HUD record')
# Insert helper methods before DrawBossAuraVfx.
t=repl(t,
'''    private void DrawBossAuraVfx(SpriteBatch batch, MilestoneBossKind kind)\n    {''',
'''    private int CuratorRecordAttackId()\n        => this.ActiveCuratorRecord.Tag switch\n        {\n            "risk" => 5,\n            "precision" => 6,\n            "pressure" => 7,\n            "recovery" => 8,\n            "mirror" => 9,\n            _ => 4,\n        };\n\n    private string CuratorRecordShort()\n        => ModEntry.T($"boss.curator.record.short.{this.ActiveCuratorRecord.Tag}");\n\n    private Color CuratorRecordColor()\n        => this.ActiveCuratorRecord.Tag switch\n        {\n            "risk" => new Color(232, 146, 93),\n            "precision" => new Color(166, 218, 246),\n            "pressure" => new Color(210, 112, 154),\n            "recovery" => new Color(112, 207, 151),\n            "mirror" => new Color(171, 150, 242),\n            _ => new Color(166, 190, 232),\n        };\n\n    private int CuratorAnimationFamily()\n    {\n        if (this.State == MilestoneBossState.Defeated)\n            return 8;\n        if (this.State == MilestoneBossState.PhaseTransition || this.Phase >= 3 && this.State != MilestoneBossState.Telegraph)\n            return 7;\n        if (this.State != MilestoneBossState.Telegraph)\n            return 0;\n        return this.CurrentAttack switch\n        {\n            1 => 1,\n            5 => 2,\n            6 => 3,\n            7 => 4,\n            8 => 5,\n            4 or 9 => 6,\n            3 => 7,\n            _ => 1,\n        };\n    }\n\n    private void DrawBossAuraVfx(SpriteBatch batch, MilestoneBossKind kind)\n    {''',
'curator record helpers')
# Reset only active runtime record; keep pending if a gate just set it before warp. Full title/day reset clears pending too.
t=repl(t,
'''        this.CuratorAdaptationStacks = 0;\n        this.DecisionSerial = 0;\n        this.RouteConfirmUntilMs = 0;''',
'''        this.CuratorAdaptationStacks = 0;\n        this.ActiveCuratorRecord = CuratorRunRecord.Neutral;\n        this.CuratorRecordRevealed = false;\n        this.DecisionSerial = 0;\n        this.RouteConfirmUntilMs = 0;''',
'reset active curator record')
p.write_text(t,encoding='utf-8')

# -----------------------------------------------------------------------------
# ModEntry wiring and debug command.
# -----------------------------------------------------------------------------
p=SRC/'ModEntry.cs'
t=p.read_text(encoding='utf-8')
t=repl(t,
'''        this.Region2Rogue.BindBossGateHandlers(this.MilestoneBosses.EnterBoss2FromRegion2, () => this.MilestoneBosses.DebugEnterBoss(2));\n        this.Airship.BindMilestoneRouteHandler''',
'''        this.Region2Rogue.BindBossGateHandlers(this.MilestoneBosses.EnterBoss2FromRegion2, () => this.MilestoneBosses.DebugEnterBoss(2));\n        this.Region2Rogue.BindCuratorRecordSink(this.MilestoneBosses.SetNextHollowCuratorRecord);\n        this.Airship.BindMilestoneRouteHandler''',
'bind curator record sink')
t=repl(t,
'''        helper.ConsoleCommands.Add("cardcha_test_boss2", "TEST ONLY: enter Boss II - The Hollow Curator (40-card milestone bypass).", (_, _) => this.Monitor.Log(this.MilestoneBosses.DebugEnterBoss(2), LogLevel.Alert));\n        helper.ConsoleCommands.Add("cardcha_test_boss3",''',
'''        helper.ConsoleCommands.Add("cardcha_test_boss2", "TEST ONLY: enter Boss II - The Hollow Curator (40-card milestone bypass).", (_, _) => this.Monitor.Log(this.MilestoneBosses.DebugEnterBoss(2), LogLevel.Alert));\n        helper.ConsoleCommands.Add("cardcha_test_boss2_record", "TEST ONLY: enter Boss II with a Curator record: risk|precision|pressure|recovery|mirror|neutral.", (_, args) => this.Monitor.Log(this.MilestoneBosses.DebugEnterBoss2WithRecord(args.FirstOrDefault()), LogLevel.Alert));\n        helper.ConsoleCommands.Add("cardcha_test_boss3",''',
'Boss2 record debug command')
t=t.replace(OLD,NEW)
t=t.replace('0680 REGION II 6-9 NODE ROGUELIKE ROUTE TEST','0681 HOLLOW CURATOR RECORDS YOU TEST')
p.write_text(t,encoding='utf-8')

# -----------------------------------------------------------------------------
# Version files.
# -----------------------------------------------------------------------------
for rel in ['manifest.json','Cardcha.csproj','Directory.Build.targets']:
    p=SRC/rel
    s=p.read_text(encoding='utf-8')
    if NEW not in s:
        if OLD not in s:
            raise SystemExit(f'0681 version anchor missing: {rel}')
        s=s.replace(OLD,NEW)
    p.write_text(s,encoding='utf-8')

# -----------------------------------------------------------------------------
# i18n. Short tags are deliberately compact so the boss HUD never sprawls.
# -----------------------------------------------------------------------------
en={
    'boss.curator.record.reveal':'The Hollow Curator opens your record: {{record}}.',
    'boss.curator.record.short.neutral':'Neutral',
    'boss.curator.record.short.risk':'Risk',
    'boss.curator.record.short.precision':'Precision',
    'boss.curator.record.short.pressure':'Pressure',
    'boss.curator.record.short.recovery':'Recovery',
    'boss.curator.record.short.mirror':'Mirror',
}
vi={
    'boss.curator.record.reveal':'Giám Thủ Rỗng mở hồ sơ của bạn: {{record}}.',
    'boss.curator.record.short.neutral':'Trung tính',
    'boss.curator.record.short.risk':'Mạo hiểm',
    'boss.curator.record.short.precision':'Chuẩn xác',
    'boss.curator.record.short.pressure':'Áp lực',
    'boss.curator.record.short.recovery':'Hồi phục',
    'boss.curator.record.short.mirror':'Phản chiếu',
}
for name,extra in [('default.json',en),('vi.json',vi)]:
    p=SRC/'i18n'/name
    data=json.loads(p.read_text(encoding='utf-8'))
    data.update(extra)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding='utf-8')

# -----------------------------------------------------------------------------
# 18-frame / 9-family Hollow Curator atlas.
# It preserves the approved 0678 silhouette and creates native-pixel state variants without
# enlarging the sprite or touching MiMi/Tricolor art.
# -----------------------------------------------------------------------------
p=SRC/'assets'/'bosses'/'milestone'/'hollow_curator.png'
img=Image.open(p).convert('RGBA')
if img.size == (864,64):
    pass
else:
    if img.size != (192,64):
        raise SystemExit(f'0681 expected prior Hollow Curator atlas 192x64, got {img.size}')
    base=[img.crop((i*48,0,(i+1)*48,64)) for i in range(4)]

    def tint(frame, rgb, strength):
        solid=Image.new('RGBA',frame.size,(rgb[0],rgb[1],rgb[2],255))
        out=Image.blend(frame,solid,strength)
        out.putalpha(frame.getchannel('A'))
        return out

    def shifted(frame, dx=0, dy=0):
        out=Image.new('RGBA',frame.size,(0,0,0,0))
        out.alpha_composite(frame,(dx,dy))
        return out

    def glyph(frame, color, mode):
        out=frame.copy(); d=ImageDraw.Draw(out)
        c=(*color,210)
        if mode=='observe':
            for x,y in [(5,18),(41,18),(8,31),(38,31)]:
                d.rectangle((x,y,x+1,y+1),fill=c)
        elif mode=='risk':
            d.line((4,48,10,42),fill=c,width=1); d.line((38,42,44,48),fill=c,width=1)
            d.rectangle((6,50,8,52),fill=c); d.rectangle((40,50,42,52),fill=c)
        elif mode=='precision':
            d.line((7,16,7,42),fill=c,width=1); d.line((40,16,40,42),fill=c,width=1)
            d.rectangle((5,27,9,29),fill=c); d.rectangle((38,27,42,29),fill=c)
        elif mode=='pressure':
            d.rectangle((4,45,9,46),fill=c); d.rectangle((38,45,43,46),fill=c)
            d.rectangle((2,51,6,52),fill=c); d.rectangle((41,51,45,52),fill=c)
        elif mode=='recovery':
            d.rectangle((5,22,6,30),fill=c); d.rectangle((2,25,9,27),fill=c)
            d.rectangle((41,22,42,30),fill=c); d.rectangle((38,25,45,27),fill=c)
        elif mode=='mirror':
            for x,y in [(4,20),(42,20),(7,37),(39,37)]:
                d.polygon([(x,y-2),(x+2,y),(x,y+2),(x-2,y)],fill=c)
        elif mode=='truth':
            d.line((3,56,12,47),fill=c,width=1); d.line((36,47,45,56),fill=c,width=1)
            d.polygon([(24,5),(27,9),(24,13),(21,9)],outline=c)
        return out

    frames=[]
    # family 0 idle / hover
    frames += [base[0], shifted(base[0],0,-1)]
    # family 1 observe / generic adaptation
    frames += [glyph(base[1],(143,190,255),'observe'), glyph(shifted(base[1],0,-1),(183,218,255),'observe')]
    # family 2 risk
    frames += [glyph(tint(base[3],(236,137,82),0.18),(247,166,94),'risk'), glyph(tint(base[2],(226,112,91),0.20),(255,183,105),'risk')]
    # family 3 precision
    frames += [glyph(tint(base[1],(169,220,248),0.16),(203,238,255),'precision'), glyph(tint(base[0],(192,229,250),0.18),(220,245,255),'precision')]
    # family 4 pressure
    frames += [glyph(tint(base[2],(207,103,151),0.18),(235,137,177),'pressure'), glyph(tint(base[3],(188,91,143),0.20),(245,148,188),'pressure')]
    # family 5 recovery
    frames += [glyph(tint(base[2],(100,205,145),0.18),(144,236,175),'recovery'), glyph(tint(base[1],(104,190,153),0.19),(166,245,193),'recovery')]
    # family 6 mirror
    mirror_a=glyph(tint(base[2],(165,145,240),0.15),(204,188,255),'mirror')
    mirror_b=glyph(ImageOps.mirror(tint(base[2],(138,170,245),0.17)),(205,196,255),'mirror')
    frames += [mirror_a,mirror_b]
    # family 7 Curator's Truth / phase transition
    frames += [glyph(tint(base[3],(181,130,238),0.16),(225,189,255),'truth'), glyph(tint(shifted(base[3],0,-1),(206,153,245),0.18),(239,209,255),'truth')]
    # family 8 defeat collapse
    d0=shifted(base[3],0,2); d0.putalpha(d0.getchannel('A').point(lambda a:int(a*0.72)))
    d1=shifted(base[3],0,4); d1.putalpha(d1.getchannel('A').point(lambda a:int(a*0.46)))
    frames += [d0,d1]

    atlas=Image.new('RGBA',(48*18,64),(0,0,0,0))
    for i,frame in enumerate(frames):
        atlas.alpha_composite(frame,(i*48,0))
    atlas.save(p,optimize=True)

# -----------------------------------------------------------------------------
# Handoff/document trail.
# -----------------------------------------------------------------------------
latest=ROOT/'handoff'/'LATEST_CARDCHA_HANDOFF.md'
latest.write_text(f'''# Latest Cardcha Handoff\n\nCurrent branch: `cardcha-alpha28-0681-hollow-curator-records-you`\nCurrent build: `{NEW}`\nContinue from: `handoff/ALPHA28_0681_HOLLOW_CURATOR_RECORDS_YOU.md`\nDesign direction: `handoff/REGION2_ROGUELIKE_DESIGN_DIRECTION.md`\n\n0681 connects the 0680 Region II run record to Hollow Curator. Phase 2/3 now reflects the dominant run tendency through a fair signature attack, and Hollow Curator uses 9 animation families / 18 native-pixel frames. In-game acceptance is pending.\n''',encoding='utf-8')

handoff=ROOT/'handoff'/'ALPHA28_0681_HOLLOW_CURATOR_RECORDS_YOU.md'
handoff.write_text(f'''# Cardcha Alpha 28 - 0681 Hollow Curator Records You\n\nBranch: `cardcha-alpha28-0681-hollow-curator-records-you`  \nBuild: `{NEW}`\n\n## Purpose\n\n0680 established a 6-9 node branching Forgotten Archive run and recorded five readable tendencies. 0681 makes that observation matter in the Region II boss fight without hard-countering the player's build.\n\n## Curator Records You\n\nAt the real Region II Archive Seal, the current runtime record is transferred to Hollow Curator before the boss warp. The record contains risk, precision, pressure, recovery, mirror, nodes reached and the dominant tag. It is runtime-only; save schema remains 19.\n\nHollow Curator phase 1 remains Observation. At the transition to phase 2 the boss reveals the dominant record. Phases 2/3 bias one extra signature attack into the existing attack pool:\n\n- Risk -> Archive Collapse: two clear danger zones, stronger damage.\n- Precision -> Perfect Margin: narrow current + remembered strike with a longer tell.\n- Pressure -> Compression Pulse: broad but lower-damage pressure field.\n- Recovery -> Restoration Echo: modest Curator heal plus a small danger zone; it does not disable player healing.\n- Mirror -> Mirror Catalogue: current, secondary and previous-position echo.\n- Neutral -> existing Mirror Echo behavior.\n\nThe old adaptation stack remains capped at 3. Record attacks complement rather than replace the normal boss kit.\n\n## Hollow Curator visual auth pass\n\nThe old four-frame atlas is replaced by a native 48x64-frame atlas with 18 frames across 9 animation families:\n\n1. idle / hover\n2. observe / adaptation\n3. risk\n4. precision\n5. pressure\n6. recovery\n7. mirror\n8. Curator's Truth / phase transition\n9. defeat collapse\n\nThe approved Curator silhouette is preserved. No sprite enlargement beyond the existing 1.95 world scale was introduced. Boss art still renders at Monster.draw actor depth; physical art never returns to RenderedWorld.\n\n## Debug\n\n- `cardcha_test_region2` - normal 6-9 node run.\n- `cardcha_region2_rogue_status` - run node/record status.\n- `cardcha_expedition_clear` - clear a combat node quickly.\n- `cardcha_test_boss2_record risk`\n- `cardcha_test_boss2_record precision`\n- `cardcha_test_boss2_record pressure`\n- `cardcha_test_boss2_record recovery`\n- `cardcha_test_boss2_record mirror`\n- `cardcha_test_boss2_record neutral`\n- `cardcha_boss_milestone_status` - includes the active Curator record.\n\n## Frozen contracts\n\n- Region II run length remains 6-9 nodes.\n- Region II fare remains 250g.\n- Boss II remains 2200 HP and rewards Mirror Archive.\n- Boss II remains the 40-card Region II milestone.\n- Region III/IV gameplay and rewards unchanged.\n- Boss III/IV art unchanged.\n- MiMi `mimi_walk.png` untouched.\n- Save schema 19; 80 source / 76 normal cards.\n- Repository rendering-depth contract remains mandatory.\n\n## Acceptance\n\nCI proves static/compile/package only. In-game acceptance should verify: record transfer from a real Region II run, correct phase-2 reveal, signature telegraph fairness, animation readability, actor-depth occlusion and no duplicate proxy art.\n''',encoding='utf-8')

# Update design doc implementation note without changing the locked 6-9 direction.
doc=ROOT/'handoff'/'REGION2_ROGUELIKE_DESIGN_DIRECTION.md'
s=doc.read_text(encoding='utf-8')
marker='## Acceptance question\n'
note='''## 0681 implementation note\n\n0681 implements the first real `Curator Records You` bridge: the dominant 0680 run tendency is handed to Boss II and biases a readable signature attack in phases 2/3. This is intentionally adaptive rather than a hard counter. The design remains open to playtest-driven tuning.\n\n'''
if note not in s:
    if marker not in s: raise SystemExit('0681 design doc acceptance marker missing')
    s=s.replace(marker,note+marker,1)
doc.write_text(s,encoding='utf-8')

print('0681 integration complete: Curator run-record bridge, adaptive attacks, 18-frame boss atlas, i18n, version and handoff.')
