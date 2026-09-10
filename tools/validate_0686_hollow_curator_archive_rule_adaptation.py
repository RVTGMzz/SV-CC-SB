#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha"
V = "0.3.0-alpha.28.0.4.14.4.5.12.54"
BRANCH = "cardcha-alpha28-0686-hollow-curator-archive-rule-adaptation"


def need(cond, msg):
    if not cond:
        raise SystemExit("0686 VALIDATION FAIL: " + msg)

manifest = json.loads((SRC / "manifest.json").read_text(encoding="utf-8"))
need(manifest.get("Version") == V, "manifest version mismatch")
for rel in ["Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
    need(V in (SRC / rel).read_text(encoding="utf-8"), rel + " version mismatch")

r2 = (SRC / "Services" / "Region2RoguelikeRunService.cs").read_text(encoding="utf-8")
for token in [
    "Region2RunModifier",
    "LooseFolios", "IronBindings", "MirrorDraft", "RedactedLedger",
    "private Action<string>? CuratorArchiveRuleSink;",
    "public void BindCuratorArchiveRuleSink(Action<string> sink)",
    "this.CuratorArchiveRuleSink?.Invoke(RunModifierKey(this.ActiveRunModifier));",
    "this.CuratorRecordSink?.Invoke(record);",
    "this.TargetNodes = 6 + random.Next(4)",
    "this.CurrentNode == 3 || this.CurrentNode == 6",
    "RoomMechanicMarkerKey = \"Ronvotri.Cardcha/0684RoomMechanic\"",
    "InteractionMarkerKey = \"Ronvotri.Cardcha/0683Region2Interaction\"",
]:
    need(token in r2, "Region II transfer/frozen contract missing: " + token)
need(r2.index("CuratorArchiveRuleSink?.Invoke") < r2.index("CuratorRecordSink?.Invoke(record)"), "Archive Rule must transfer before boss warp via existing record path")

boss = (SRC / "Services" / "MilestoneBossService.cs").read_text(encoding="utf-8")
for token in [
    'private string PendingCuratorArchiveRule = "none";',
    'private string ActiveCuratorArchiveRule = "none";',
    "private bool HasPendingCuratorArchiveRule;",
    "public void SetNextHollowCuratorArchiveRule(string? archiveRule)",
    "NormalizeCuratorArchiveRule(archiveRule)",
    "this.ActiveCuratorArchiveRule = this.HasPendingCuratorArchiveRule ? this.PendingCuratorArchiveRule : \"none\";",
    "private int[] ApplyCuratorArchiveRuleAttackBias(int[] basePool)",
    '"loose_folios" => new[] { 0, 2 }',
    '"iron_bindings" => new[] { 3 }',
    '"mirror_draft" => new[] { 9 }',
    '"redacted_ledger" => new[] { 4, 4 }',
    '"loose_folios" => Math.Max(360, gap - 100)',
    '"iron_bindings" => gap + 120',
    "MirrorCuratorTile(this.AttackTargetTile)",
    "boss.curator.record_rule.reveal",
    "CuratorArchiveRuleShort()",
    "ArchiveRule={this.ActiveCuratorArchiveRule}",
]:
    need(token in boss, "Curator Archive Rule contract missing: " + token)

# Phase 1 must remain the existing Observation pool, without applying the run rule.
select_start = boss.index("private void SelectAttack")
select_end = boss.index("private void ApplyCurrentAttack", select_start)
select = boss[select_start:select_end]
need('1 => new[] { 0, 0, 1 }' in select, "Curator phase-1 Observation pool changed")
need('2 => this.ApplyCuratorArchiveRuleAttackBias' in select, "phase 2 does not inherit Archive Rule")
need('_ => this.ApplyCuratorArchiveRuleAttackBias' in select, "phase 3 does not inherit Archive Rule")

# Existing tendency adaptation remains primary and all five recorded attacks stay intact.
for token in ['"risk" => 5', '"precision" => 6', '"pressure" => 7', '"recovery" => 8', '"mirror" => 9']:
    need(token in boss, "Curator Records You regressed: " + token)
for attack in range(5, 10):
    need(f"case {attack}:" in boss, f"recorded Curator attack {attack} missing")
need("CuratorAdaptationStacks" in boss, "Curator adaptation stacks regressed")

# Rule state must be transient and cleared by ResetRuntime.
reset_start = boss.index("private void ResetRuntime")
reset_end = boss.index("private void RemoveMarkedActors", reset_start)
reset = boss[reset_start:reset_end]
for token in [
    'this.PendingCuratorArchiveRule = "none";',
    'this.ActiveCuratorArchiveRule = "none";',
    "this.HasPendingCuratorArchiveRule = false;",
    "this.PendingCuratorRecord = CuratorRunRecord.Neutral;",
]:
    need(token in reset, "Curator transient cleanup missing: " + token)

# ModEntry only adds the handoff binding, not another rendering subscriber.
mod = (SRC / "ModEntry.cs").read_text(encoding="utf-8")
need("BindCuratorArchiveRuleSink(this.MilestoneBosses.SetNextHollowCuratorArchiveRule)" in mod, "Archive Rule binding missing")
need("0686 HOLLOW CURATOR ARCHIVE RULE ADAPTATION TEST" in mod, "0686 build label missing")
need(mod.count("helper.Events.Display.RenderedWorld += this.MilestoneBosses.OnRenderedWorld;") == 1, "MilestoneBoss RenderedWorld hook duplicated")
need(mod.count("helper.Events.Display.RenderedWorld += this.Region2Rogue.OnRenderedWorld;") == 1, "Region2Rogue RenderedWorld hook duplicated")

# Rendering ownership remains unchanged and VFX-only.
audit = json.loads((ROOT / "render_depth_audit.json").read_text(encoding="utf-8"))
need(audit.get("branch") == BRANCH, "render-depth audit branch stale")
for key in ["MilestoneBosses", "Region2Rogue"]:
    meta = audit.get("renderedWorldSubscribers", {}).get(key)
    need(isinstance(meta, dict), key + " missing from render-depth audit")
    need(meta.get("physicalAllowed") is False, key + " physicalAllowed must stay false")

# EN/VI reveal and short names must exist.
i18n_keys = [
    "boss.curator.record_rule.reveal",
    "boss.curator.rule.short.none",
    "boss.curator.rule.short.loose_folios",
    "boss.curator.rule.short.iron_bindings",
    "boss.curator.rule.short.mirror_draft",
    "boss.curator.rule.short.redacted_ledger",
]
for lang in ["default.json", "vi.json"]:
    data = json.loads((SRC / "i18n" / lang).read_text(encoding="utf-8"))
    for key in i18n_keys:
        need(key in data, lang + " missing " + key)
    need("{{record}}" in data["boss.curator.record_rule.reveal"], lang + " reveal missing record token")
    need("{{rule}}" in data["boss.curator.record_rule.reveal"], lang + " reveal missing rule token")

# Frozen progression/economy/boss/save/card contracts.
airship = (SRC / "Services" / "AirshipFoundationService.cs").read_text(encoding="utf-8")
need("private const int Region2Fare = 250;" in airship, "Region II fare changed")
need("HollowCuratorMaxHealth = 2200" in boss, "Boss II HP changed")
need('return (MilestoneBossKind.HollowCurator, 40, "The Hollow Curator")' in boss, "40-card milestone changed")
save = (SRC / "Services" / "SaveService.cs").read_text(encoding="utf-8")
need("19" in save, "save schema 19 token missing")
cards = json.loads((SRC / "assets" / "cards.json").read_text(encoding="utf-8"))
legacy = {"endless_hunt", "fate_weaver", "immortal_echo", "worldbreaker"}
ids = {str(c.get("Id", "")) for c in cards}
need(len(cards) == 80 and len(ids) == 80 and legacy.issubset(ids) and len(ids - legacy) == 76, "80/76 card audit changed")

# 0683 Final Cache and 0684 hazards remain structurally present.
need("this.BeginNode(location, Region2NodeKind.FinalCache);" in r2, "physical route-end Final Cache regressed")
need("this.AwardNode(Region2NodeKind.FinalCache);" not in r2[r2.index("private void CompleteCurrentNode"):r2.index("private void PrepareRouteChoice")], "Final Cache auto-award regressed")
for token in ['"mirror_trace"', '"ink_sweep"', '"warden_seal"']:
    need(token in r2, "0684 room mechanic missing: " + token)

# Documentation trail must advance to 0686.
latest = (ROOT / "handoff" / "LATEST_CARDCHA_HANDOFF.md").read_text(encoding="utf-8")
need("0686" in latest and V in latest and BRANCH in latest, "LATEST handoff not advanced to 0686")
need((ROOT / "handoff" / "ALPHA28_0686_HOLLOW_CURATOR_ARCHIVE_RULE_ADAPTATION.md").exists(), "0686 handoff missing")
design = (ROOT / "handoff" / "REGION2_ROGUELIKE_DESIGN_DIRECTION.md").read_text(encoding="utf-8")
need("### 0686 implementation note" in design, "0686 design note missing")
need("6–9 short nodes" in design, "Region II 6-9 design direction lost")

print("0686 validation PASS: Archive Rule transfers into Curator phases 2/3; phase 1, tendency adaptation, depth, progression, save and 80/76 contracts remain intact.")
