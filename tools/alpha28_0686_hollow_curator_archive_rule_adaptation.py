#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha"
OLD = "0.3.0-alpha.28.0.4.14.4.5.12.53"
NEW = "0.3.0-alpha.28.0.4.14.4.5.12.54"
BRANCH = "cardcha-alpha28-0686-hollow-curator-archive-rule-adaptation"
R2 = SRC / "Services" / "Region2RoguelikeRunService.cs"
BOSS = SRC / "Services" / "MilestoneBossService.cs"


def need(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("0686 BUILD FAIL: " + msg)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    need(old in text, "missing anchor: " + label)
    return text.replace(old, new, 1)


manifest = json.loads((SRC / "manifest.json").read_text(encoding="utf-8"))
r2_text = R2.read_text(encoding="utf-8")
boss_text = BOSS.read_text(encoding="utf-8")
if manifest.get("Version") == NEW and "BindCuratorArchiveRuleSink" in r2_text and "SetNextHollowCuratorArchiveRule" in boss_text:
    print("0686 already materialized; generator is idempotent.")
    raise SystemExit(0)

need(manifest.get("Version") == OLD, f"expected {OLD}, found {manifest.get('Version')}")
need("Region2RunModifier" in r2_text and "RedactedLedger" in r2_text, "0685 run modifier runtime missing")
need("CuratorRecordAttackId()" in boss_text and "CuratorAdaptationStacks" in boss_text, "Curator Records You runtime missing")

# Exact build bump. Save schema, progression, cards and accepted assets stay frozen.
for rel in ["manifest.json", "Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
    p = SRC / rel
    text = p.read_text(encoding="utf-8")
    need(OLD in text, f"{rel} missing old build version")
    p.write_text(text.replace(OLD, NEW), encoding="utf-8")

# Region II transfers its active Archive Rule beside the existing Curator run record.
t = R2.read_text(encoding="utf-8")
t = replace_once(
    t,
    "    private Action<CuratorRunRecord>? CuratorRecordSink;\n",
    "    private Action<CuratorRunRecord>? CuratorRecordSink;\n    private Action<string>? CuratorArchiveRuleSink;\n",
    "Archive Rule sink field",
)
t = replace_once(
    t,
    "    public void BindCuratorRecordSink(Action<CuratorRunRecord> sink)\n        => this.CuratorRecordSink = sink;\n",
    "    public void BindCuratorRecordSink(Action<CuratorRunRecord> sink)\n        => this.CuratorRecordSink = sink;\n\n    public void BindCuratorArchiveRuleSink(Action<string> sink)\n        => this.CuratorArchiveRuleSink = sink;\n",
    "Archive Rule sink binding",
)
t = replace_once(
    t,
    "        CuratorRunRecord record = this.BuildCuratorRunRecord(debug);\n        this.CuratorRecordSink?.Invoke(record);\n",
    "        CuratorRunRecord record = this.BuildCuratorRunRecord(debug);\n        this.CuratorArchiveRuleSink?.Invoke(RunModifierKey(this.ActiveRunModifier));\n        this.CuratorRecordSink?.Invoke(record);\n",
    "Archive Rule boss transfer",
)
old_log = 'this.Monitor.Log($"0683 Region II -> Hollow Curator. Transferred {record.Describe()}.", LogLevel.Info);'
if old_log in t:
    t = t.replace(old_log, 'this.Monitor.Log($"0686 Region II -> Hollow Curator. Transferred {record.Describe()} + ArchiveRule={RunModifierKey(this.ActiveRunModifier)}.", LogLevel.Info);', 1)
R2.write_text(t, encoding="utf-8")

# Hollow Curator receives the rule as transient runtime state. CuratorRunRecord/save schema are unchanged.
b = BOSS.read_text(encoding="utf-8")
b = replace_once(
    b,
    "    private bool CuratorRecordRevealed;\n    private int DecisionSerial;\n",
    "    private bool CuratorRecordRevealed;\n    private string PendingCuratorArchiveRule = \"none\";\n    private string ActiveCuratorArchiveRule = \"none\";\n    private bool HasPendingCuratorArchiveRule;\n    private int DecisionSerial;\n",
    "Curator Archive Rule runtime fields",
)
b = replace_once(
    b,
    "    public void SetNextHollowCuratorRecord(CuratorRunRecord record)\n    {\n        this.PendingCuratorRecord = record ?? CuratorRunRecord.Neutral;\n        this.HasPendingCuratorRecord = true;\n        this.Monitor.Log($\"0681 Hollow Curator pending run record: {this.PendingCuratorRecord.Describe()}.\", LogLevel.Trace);\n    }\n",
    "    public void SetNextHollowCuratorRecord(CuratorRunRecord record)\n    {\n        this.PendingCuratorRecord = record ?? CuratorRunRecord.Neutral;\n        this.HasPendingCuratorRecord = true;\n        this.Monitor.Log($\"0681 Hollow Curator pending run record: {this.PendingCuratorRecord.Describe()}.\", LogLevel.Trace);\n    }\n\n    public void SetNextHollowCuratorArchiveRule(string? archiveRule)\n    {\n        this.PendingCuratorArchiveRule = NormalizeCuratorArchiveRule(archiveRule);\n        this.HasPendingCuratorArchiveRule = this.PendingCuratorArchiveRule != \"none\";\n        this.Monitor.Log($\"0686 Hollow Curator pending Archive Rule: {this.PendingCuratorArchiveRule}.\", LogLevel.Trace);\n    }\n",
    "Curator Archive Rule setter",
)
b = replace_once(
    b,
    "        CuratorRunRecord record = CuratorRunRecord.Debug(tag);\n        this.SetNextHollowCuratorRecord(record);\n        return this.DebugEnterBoss(2) + $\" Curator record={record.Tag}.\";\n",
    "        CuratorRunRecord record = CuratorRunRecord.Debug(tag);\n        this.SetNextHollowCuratorArchiveRule(\"none\");\n        this.SetNextHollowCuratorRecord(record);\n        return this.DebugEnterBoss(2) + $\" Curator record={record.Tag}; ArchiveRule=none.\";\n",
    "direct Curator debug neutral rule",
)

# Consume both transient inputs on boss start.
b = replace_once(
    b,
    "            this.ActiveCuratorRecord = this.HasPendingCuratorRecord ? this.PendingCuratorRecord : CuratorRunRecord.Neutral;\n            this.PendingCuratorRecord = CuratorRunRecord.Neutral;\n            this.HasPendingCuratorRecord = false;\n",
    "            this.ActiveCuratorRecord = this.HasPendingCuratorRecord ? this.PendingCuratorRecord : CuratorRunRecord.Neutral;\n            this.ActiveCuratorArchiveRule = this.HasPendingCuratorArchiveRule ? this.PendingCuratorArchiveRule : \"none\";\n            this.PendingCuratorRecord = CuratorRunRecord.Neutral;\n            this.HasPendingCuratorRecord = false;\n            this.PendingCuratorArchiveRule = \"none\";\n            this.HasPendingCuratorArchiveRule = false;\n",
    "Curator rule activation",
)
b = replace_once(
    b,
    "        else\n        {\n            this.ActiveCuratorRecord = CuratorRunRecord.Neutral;\n        }\n        this.CuratorRecordRevealed = false;\n",
    "        else\n        {\n            this.ActiveCuratorRecord = CuratorRunRecord.Neutral;\n            this.ActiveCuratorArchiveRule = \"none\";\n        }\n        this.CuratorRecordRevealed = false;\n",
    "non-Curator rule reset",
)

# Phase 1 remains unchanged. Phases 2/3 receive a secondary attack-composition bias from the Archive Rule.
old_pool = '''                int recordAttack = this.CuratorRecordAttackId();
                int[] pool = this.Phase switch
                {
                    1 => new[] { 0, 0, 1 },
                    2 => new[] { 0, 1, 2, 4, recordAttack, recordAttack },
                    _ => new[] { 0, 2, 3, 4, recordAttack, recordAttack, recordAttack },
                };
                this.CurrentAttack = pool[this.Rng.Next(pool.Length)];
'''
new_pool = '''                int recordAttack = this.CuratorRecordAttackId();
                int[] pool = this.Phase switch
                {
                    1 => new[] { 0, 0, 1 },
                    2 => this.ApplyCuratorArchiveRuleAttackBias(new[] { 0, 1, 2, 4, recordAttack, recordAttack }),
                    _ => this.ApplyCuratorArchiveRuleAttackBias(new[] { 0, 2, 3, 4, recordAttack, recordAttack, recordAttack }),
                };
                this.CurrentAttack = pool[this.Rng.Next(pool.Length)];
'''
b = replace_once(b, old_pool, new_pool, "Archive Rule attack composition")

# Mirror Draft occasionally reflects the second zone only on attacks which already own a second zone.
mirror_anchor = '''                else if (this.CurrentAttack == 9)
                {
                    this.AttackTargetTile2 = ClampArenaTile(new Point(
                        this.AttackTargetTile.X + (this.DecisionSerial % 2 == 0 ? 2 : -2),
                        this.AttackTargetTile.Y + (this.DecisionSerial % 3 == 0 ? 2 : -1)
                    ));
                }
                this.MaybeTeleportPrimary("curator");
'''
mirror_new = '''                else if (this.CurrentAttack == 9)
                {
                    this.AttackTargetTile2 = ClampArenaTile(new Point(
                        this.AttackTargetTile.X + (this.DecisionSerial % 2 == 0 ? 2 : -2),
                        this.AttackTargetTile.Y + (this.DecisionSerial % 3 == 0 ? 2 : -1)
                    ));
                }
                if (this.Phase >= 2 && this.ActiveCuratorArchiveRule == "mirror_draft"
                    && this.DecisionSerial % 2 == 0 && this.CurrentAttack is 2 or 5 or 9)
                {
                    this.AttackTargetTile2 = MirrorCuratorTile(this.AttackTargetTile);
                }
                this.MaybeTeleportPrimary("curator");
'''
b = replace_once(b, mirror_anchor, mirror_new, "Mirror Draft target reflection")

# Reveal the recorded tendency and inherited rule together at phase 2.
b = replace_once(
    b,
    '            Game1.showGlobalMessage(ModEntry.T("boss.curator.record.reveal", new { record = this.CuratorRecordShort() }));\n',
    '            Game1.showGlobalMessage(ModEntry.T("boss.curator.record_rule.reveal", new { record = this.CuratorRecordShort(), rule = this.CuratorArchiveRuleShort() }));\n',
    "combined record/rule reveal",
)

# Loose Folios accelerates the between-attack rhythm; Iron Bindings slows it. Telegraph duration itself is untouched.
old_gap = '''    private int CurrentDecisionGapMs() => this.CurrentKind switch
    {
        MilestoneBossKind.HollowCurator => this.Phase switch { 1 => 780, 2 => 650, _ => 520 },
        MilestoneBossKind.TricolorResonance => this.Phase >= 4 ? 520 : 720,
        MilestoneBossKind.Mimi => this.Phase switch { 1 => 720, 2 => 620, 3 => 520, _ => 430 },
        _ => 650,
    };
'''
new_gap = '''    private int CurrentDecisionGapMs()
    {
        int gap = this.CurrentKind switch
        {
            MilestoneBossKind.HollowCurator => this.Phase switch { 1 => 780, 2 => 650, _ => 520 },
            MilestoneBossKind.TricolorResonance => this.Phase >= 4 ? 520 : 720,
            MilestoneBossKind.Mimi => this.Phase switch { 1 => 720, 2 => 620, 3 => 520, _ => 430 },
            _ => 650,
        };
        if (this.CurrentKind != MilestoneBossKind.HollowCurator || this.Phase < 2)
            return gap;
        return this.ActiveCuratorArchiveRule switch
        {
            "loose_folios" => Math.Max(360, gap - 100),
            "iron_bindings" => gap + 120,
            _ => gap,
        };
    }
'''
b = replace_once(b, old_gap, new_gap, "Archive Rule cadence")

# Helpers reuse the already-authored and already-telegraphed Curator attacks.
helper_anchor = "    private int CuratorRecordAttackId()\n"
need(helper_anchor in b, "Curator record helper anchor")
helper_block = r'''    private int[] ApplyCuratorArchiveRuleAttackBias(int[] basePool)
    {
        if (this.Phase < 2 || this.ActiveCuratorArchiveRule == "none")
            return basePool;
        IEnumerable<int> extra = this.ActiveCuratorArchiveRule switch
        {
            "loose_folios" => new[] { 0, 2 },
            "iron_bindings" => new[] { 3 },
            "mirror_draft" => new[] { 9 },
            "redacted_ledger" => new[] { 4, 4 },
            _ => Array.Empty<int>(),
        };
        return basePool.Concat(extra).ToArray();
    }

    private static string NormalizeCuratorArchiveRule(string? archiveRule)
    {
        string key = (archiveRule ?? string.Empty).Trim().ToLowerInvariant();
        return key is "loose_folios" or "iron_bindings" or "mirror_draft" or "redacted_ledger" ? key : "none";
    }

    private string CuratorArchiveRuleShort()
        => ModEntry.T($"boss.curator.rule.short.{this.ActiveCuratorArchiveRule}");

    private static Point MirrorCuratorTile(Point tile)
        => ClampArenaTile(new Point(27 - tile.X, tile.Y));

'''
b = b.replace(helper_anchor, helper_block + helper_anchor, 1)

# Diagnostics and HUD expose the secondary rule without changing phase-1 mechanics.
old_diag = 'CuratorRecord={this.ActiveCuratorRecord.Describe()} | BossCards='
need(old_diag in b, "boss diagnostics anchor")
b = b.replace(old_diag, 'CuratorRecord={this.ActiveCuratorRecord.Describe()} | ArchiveRule={this.ActiveCuratorArchiveRule} | BossCards=', 1)
b = replace_once(
    b,
    '                2 => $"Reflection • {this.CuratorRecordShort()} • Adapt {this.CuratorAdaptationStacks}/3",\n',
    '                2 => $"Reflection • {this.CuratorRecordShort()} • {this.CuratorArchiveRuleShort()} • Adapt {this.CuratorAdaptationStacks}/3",\n',
    "phase 2 rule HUD",
)
b = replace_once(
    b,
    '                _ => $"Curator\'s Truth • {this.CuratorRecordShort()} • Adapt {this.CuratorAdaptationStacks}/3",\n',
    '                _ => $"Curator\'s Truth • {this.CuratorRecordShort()} • {this.CuratorArchiveRuleShort()} • Adapt {this.CuratorAdaptationStacks}/3",\n',
    "phase 3 rule HUD",
)

# Tint an Archive-Rule-injected Mirror Draft attack as mirror-purple even when the primary tendency is different.
b = replace_once(
    b,
    '        else if (this.CurrentKind == MilestoneBossKind.HollowCurator && this.CurrentAttack is >= 5 and <= 9)\n            c = this.CuratorRecordColor();\n',
    '        else if (this.CurrentKind == MilestoneBossKind.HollowCurator && this.CurrentAttack is >= 5 and <= 9)\n            c = this.CurrentAttack == 9 && this.ActiveCuratorArchiveRule == "mirror_draft"\n                ? new Color(186, 164, 246)\n                : this.CuratorRecordColor();\n',
    "Mirror Draft telegraph tint",
)

# Reset active and pending transient rule state so a run cannot leak into a later boss encounter.
b = replace_once(
    b,
    "        this.ActiveCuratorRecord = CuratorRunRecord.Neutral;\n        this.CuratorRecordRevealed = false;\n",
    "        this.ActiveCuratorRecord = CuratorRunRecord.Neutral;\n        this.PendingCuratorRecord = CuratorRunRecord.Neutral;\n        this.HasPendingCuratorRecord = false;\n        this.PendingCuratorArchiveRule = \"none\";\n        this.ActiveCuratorArchiveRule = \"none\";\n        this.HasPendingCuratorArchiveRule = false;\n        this.CuratorRecordRevealed = false;\n",
    "Curator Archive Rule runtime cleanup",
)
BOSS.write_text(b, encoding="utf-8")

# Wire the transient rule handoff. No new RenderedWorld subscriber is introduced.
mod_path = SRC / "ModEntry.cs"
mod = mod_path.read_text(encoding="utf-8")
mod = replace_once(
    mod,
    "        this.Region2Rogue.BindCuratorRecordSink(this.MilestoneBosses.SetNextHollowCuratorRecord);\n",
    "        this.Region2Rogue.BindCuratorRecordSink(this.MilestoneBosses.SetNextHollowCuratorRecord);\n        this.Region2Rogue.BindCuratorArchiveRuleSink(this.MilestoneBosses.SetNextHollowCuratorArchiveRule);\n",
    "Archive Rule boss binding",
)
mod = mod.replace("0685 REGION II ENCOUNTER COMPOSITION + RUN MODIFIERS TEST", "0686 HOLLOW CURATOR ARCHIVE RULE ADAPTATION TEST")
mod_path.write_text(mod, encoding="utf-8")

# Localized boss-readable rule labels. Existing 0685 run modifier text remains intact.
for lang, values in {
    "default.json": {
        "boss.curator.record_rule.reveal": "Hollow Curator opens your record: {{record}}. The Archive Rule persists: {{rule}}.",
        "boss.curator.rule.short.none": "No Archive Rule",
        "boss.curator.rule.short.loose_folios": "Loose Folios",
        "boss.curator.rule.short.iron_bindings": "Iron Bindings",
        "boss.curator.rule.short.mirror_draft": "Mirror Draft",
        "boss.curator.rule.short.redacted_ledger": "Redacted Ledger",
    },
    "vi.json": {
        "boss.curator.record_rule.reveal": "Hollow Curator mở bản ghi của bạn: {{record}}. Luật Kho Lưu Trữ vẫn còn hiệu lực: {{rule}}.",
        "boss.curator.rule.short.none": "Không Có Luật",
        "boss.curator.rule.short.loose_folios": "Trang Rời",
        "boss.curator.rule.short.iron_bindings": "Gáy Sắt",
        "boss.curator.rule.short.mirror_draft": "Bản Nháp Gương",
        "boss.curator.rule.short.redacted_ledger": "Sổ Bôi Đen",
    },
}.items():
    ip = SRC / "i18n" / lang
    data = json.loads(ip.read_text(encoding="utf-8"))
    data.update(values)
    ip.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# No renderer ownership changes. Advance only the branch marker.
audit_path = ROOT / "render_depth_audit.json"
audit = json.loads(audit_path.read_text(encoding="utf-8"))
audit["branch"] = BRANCH
audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")

# Keep design and handoff trail current.
design_path = ROOT / "handoff" / "REGION2_ROGUELIKE_DESIGN_DIRECTION.md"
design = design_path.read_text(encoding="utf-8")
note = '''\n\n### 0686 implementation note\n\nHollow Curator now inherits the run's 0685 Archive Rule as a secondary, transient adaptation layer beside `Curator Records You`. The dominant player tendency remains the primary adaptive identity. Archive Rules only affect phases 2/3 by biasing already-authored Curator attacks, modestly changing cadence for Loose Folios/Iron Bindings, and allowing Mirror Draft to reflect eligible secondary target geometry. This is adaptation and continuity, not a hard counter; phase 1 remains mechanically unchanged Observation. No save schema or physical rendering ownership changes.\n'''
if "### 0686 implementation note" not in design:
    design += note
design_path.write_text(design, encoding="utf-8")

handoff = f'''# Alpha.28 0686 Hollow Curator Archive Rule Adaptation\n\nBranch: `{BRANCH}`\nBuild: `{NEW}`\nBase: 0685 Region II Encounter Composition + Run Modifiers\n\n## Purpose\n\n0686 closes the run-to-boss loop: Hollow Curator now receives the current Region II Archive Rule in addition to the existing `Curator Records You` tendency record. The run modifier no longer disappears at the Archive Seal.\n\n## Boss adaptation\n\n- Phase 1 remains normal Observation with no Archive Rule gameplay effect.\n- **Loose Folios:** phases 2/3 bias toward quick direct/paired attacks and shorten the decision gap by 100ms.\n- **Iron Bindings:** phases 2/3 add weight to the heavy compression attack and lengthen the decision gap by 120ms.\n- **Mirror Draft:** phases 2/3 add a mirrored Curator attack to the pool; every second eligible two-zone attack mirrors its secondary target across the arena.\n- **Redacted Ledger:** phases 2/3 add extra weight to remembered-position echo attacks.\n- The dominant run tendency remains the primary recorded adaptation; Archive Rule is a secondary layer and never disables the player's build.\n\n## Transfer/lifecycle\n\nRegion II sends the Archive Rule through a transient parallel sink immediately before Boss II entry. It is consumed when Hollow Curator starts and cleared on runtime reset. `CuratorRunRecord` and save schema remain unchanged. Direct Boss II record-debug entry defaults to no Archive Rule; Region II boss-gate debug carries the run's selected rule.\n\n## Presentation\n\nAt phase 2, one localized message reveals both the recorded tendency and inherited Archive Rule. Boss HUD shows the rule in phases 2/3. No new `RenderedWorld` subscriber or physical object is added; existing actor-depth boss rendering and telegraph VFX remain authoritative.\n\n## Frozen contracts\n\n- Region II run target 6–9 nodes; checkpoints 3 and 6.\n- Region II fare 250g.\n- 0683 physical interactions/Final Cache remain intact.\n- 0684 room-specific mechanics remain intact.\n- 0685 four Archive Rules and encounter composition remain intact.\n- Hollow Curator remains 2200 HP at the 40-card milestone.\n- Save schema remains 19.\n- Card audit remains 80 source / 76 active normal.\n- Region III/IV, Boss III/IV, accepted maps/art/Airship and `mimi_walk.png` are untouched.\n\n## Debug\n\n- `cardcha_test_region2`\n- `cardcha_region2_rogue_status`\n- `cardcha_test_region2_bossgate`\n- `cardcha_test_boss2_record <risk|precision|pressure|recovery|mirror|neutral>`\n- `cardcha_boss_milestone_status`\n\n## Acceptance\n\nCI proves static/compile/package contracts only. In-game acceptance remains pending. Compare several Region II runs through Boss II and confirm the Archive Rule remains noticeable but secondary to the tendency record, telegraphs stay readable, and phase 1 pacing remains unchanged.\n'''
(ROOT / "handoff" / "ALPHA28_0686_HOLLOW_CURATOR_ARCHIVE_RULE_ADAPTATION.md").write_text(handoff, encoding="utf-8")
latest = f'''# Latest Cardcha Handoff\n\nCurrent branch: `{BRANCH}`\nCurrent build: `{NEW}`\nContinue from: `handoff/ALPHA28_0686_HOLLOW_CURATOR_ARCHIVE_RULE_ADAPTATION.md`\nDesign direction: `handoff/REGION2_ROGUELIKE_DESIGN_DIRECTION.md`\n\n0686 preserves the 0685 Region II run composition/modifier layer and carries its Archive Rule through the Archive Seal into Hollow Curator phases 2/3 as a readable secondary adaptation beside `Curator Records You`. In-game acceptance is pending.\n'''
(ROOT / "handoff" / "LATEST_CARDCHA_HANDOFF.md").write_text(latest, encoding="utf-8")

print("0686 generator complete: Region II Archive Rule -> Hollow Curator phase 2/3 adaptation + localized reveal/HUD + transient lifecycle.")
