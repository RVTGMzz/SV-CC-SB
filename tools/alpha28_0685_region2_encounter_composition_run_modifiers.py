#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha"
OLD = "0.3.0-alpha.28.0.4.14.4.5.12.52"
NEW = "0.3.0-alpha.28.0.4.14.4.5.12.53"
BRANCH = "cardcha-alpha28-0685-region2-encounter-composition-run-modifiers"
SERVICE = SRC / "Services" / "Region2RoguelikeRunService.cs"


def need(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("0685 BUILD FAIL: " + msg)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    need(old in text, "missing anchor: " + label)
    return text.replace(old, new, 1)


manifest = json.loads((SRC / "manifest.json").read_text(encoding="utf-8"))
service_text = SERVICE.read_text(encoding="utf-8")
if manifest.get("Version") == NEW and "Region2RunModifier" in service_text and "RedactedLedger" in service_text:
    print("0685 already materialized; generator is idempotent.")
    raise SystemExit(0)

need(manifest.get("Version") == OLD, f"expected {OLD}, found {manifest.get('Version')}")
need('return $"0684 Region II Rogue:' in service_text, "0684 Region II runtime is not materialized")
need('RoomMechanicMarkerKey = "Ronvotri.Cardcha/0684RoomMechanic"' in service_text, "0684 room mechanics missing")

# Exact build bump. No save/progression/card schema changes.
for rel in ["manifest.json", "Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
    p = SRC / rel
    text = p.read_text(encoding="utf-8")
    need(OLD in text, f"{rel} missing old build version")
    p.write_text(text.replace(OLD, NEW), encoding="utf-8")

p = SERVICE
t = p.read_text(encoding="utf-8")

# A run-level rule is selected once and shapes both route composition and combat composition.
enum_anchor = '''internal enum Region2NodeKind
{
    Combat,
    Ambush,
    Elite,
    MirrorChoice,
    ArchiveEvent,
    Cache,
    Restoration,
    CursedArchive,
    BossGate,
    FinalCache,
}
'''
modifier_enum = enum_anchor + '''
internal enum Region2RunModifier
{
    LooseFolios,
    IronBindings,
    MirrorDraft,
    RedactedLedger,
}
'''
t = replace_once(t, enum_anchor, modifier_enum, "run modifier enum")

field_anchor = '    private string LastCuratorRecord = "none";\n    private string ActiveRoomMechanic = "none";\n'
field_new = '    private string LastCuratorRecord = "none";\n    private Region2RunModifier ActiveRunModifier = Region2RunModifier.MirrorDraft;\n    private string LastEncounterMix = "none";\n    private string ActiveRoomMechanic = "none";\n'
t = replace_once(t, field_anchor, field_new, "run modifier state")

# Select the rule from the already deterministic run RNG, then make it readable in the run intro.
t = replace_once(
    t,
    '        this.LastCuratorRecord = "none";\n        this.ExtractConfirmUntilMs = 0;\n',
    '        this.LastCuratorRecord = "none";\n        this.LastEncounterMix = "none";\n        this.ExtractConfirmUntilMs = 0;\n',
    "start-run mix reset",
)
t = replace_once(
    t,
    '        Random random = new(this.RunSeed);\n        this.TargetNodes = 6 + random.Next(4); // 6-9, aligned with Region I run length without copying its route logic.\n',
    '        Random random = new(this.RunSeed);\n        this.TargetNodes = 6 + random.Next(4); // 6-9, aligned with Region I run length without copying its route logic.\n        this.ActiveRunModifier = PickRunModifier(random);\n',
    "run modifier selection",
)
t = replace_once(
    t,
    '        Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.start", new { total = this.TargetNodes }));\n',
    '        Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.start", new\n        {\n            total = this.TargetNodes,\n            modifier = this.RunModifierDisplayName(),\n            effect = this.RunModifierEffectText()\n        }));\n',
    "localized run modifier intro",
)

# Existing route selection becomes weighted by the active Archive Rule instead of uniform RNG.
old_route_methods = '''    private static Region2NodeKind PickDeepRoute(Random random)
    {
        Region2NodeKind[] deep =
        {
            Region2NodeKind.Elite,
            Region2NodeKind.CursedArchive,
            Region2NodeKind.MirrorChoice,
            Region2NodeKind.Cache,
            Region2NodeKind.Ambush,
        };
        return deep[random.Next(deep.Length)];
    }

    private static Region2NodeKind PickRoute(Random random, Region2NodeKind previous, Region2NodeKind? exclude)
    {
        Region2NodeKind[] pool =
        {
            Region2NodeKind.Combat,
            Region2NodeKind.Ambush,
            Region2NodeKind.Elite,
            Region2NodeKind.MirrorChoice,
            Region2NodeKind.ArchiveEvent,
            Region2NodeKind.Cache,
            Region2NodeKind.Restoration,
            Region2NodeKind.CursedArchive,
        };
        List<Region2NodeKind> candidates = pool
            .Where(k => k != previous && (!exclude.HasValue || k != exclude.Value))
            .ToList();
        return candidates[random.Next(candidates.Count)];
    }
'''
new_route_methods = '''    private Region2NodeKind PickDeepRoute(Random random)
    {
        Region2NodeKind[] deep =
        {
            Region2NodeKind.Elite,
            Region2NodeKind.CursedArchive,
            Region2NodeKind.MirrorChoice,
            Region2NodeKind.Cache,
            Region2NodeKind.Ambush,
        };
        return this.PickWeightedRoute(random, deep);
    }

    private Region2NodeKind PickRoute(Random random, Region2NodeKind previous, Region2NodeKind? exclude)
    {
        Region2NodeKind[] pool =
        {
            Region2NodeKind.Combat,
            Region2NodeKind.Ambush,
            Region2NodeKind.Elite,
            Region2NodeKind.MirrorChoice,
            Region2NodeKind.ArchiveEvent,
            Region2NodeKind.Cache,
            Region2NodeKind.Restoration,
            Region2NodeKind.CursedArchive,
        };
        List<Region2NodeKind> candidates = pool
            .Where(k => k != previous && (!exclude.HasValue || k != exclude.Value))
            .ToList();
        return this.PickWeightedRoute(random, candidates);
    }

    private Region2NodeKind PickWeightedRoute(Random random, IEnumerable<Region2NodeKind> candidates)
    {
        List<(Region2NodeKind Kind, int Weight)> weighted = candidates
            .Select(kind => (kind, Math.Max(1, RunModifierRouteWeight(this.ActiveRunModifier, kind))))
            .ToList();
        if (weighted.Count == 0)
            return Region2NodeKind.Combat;

        int total = weighted.Sum(p => p.Weight);
        int roll = random.Next(total);
        foreach ((Region2NodeKind kind, int weight) in weighted)
        {
            if (roll < weight)
                return kind;
            roll -= weight;
        }
        return weighted[^1].Kind;
    }

    private static int RunModifierRouteWeight(Region2RunModifier modifier, Region2NodeKind kind)
        => modifier switch
        {
            Region2RunModifier.LooseFolios => kind switch
            {
                Region2NodeKind.Combat => 22,
                Region2NodeKind.Ambush => 28,
                Region2NodeKind.Elite => 10,
                Region2NodeKind.MirrorChoice => 8,
                Region2NodeKind.ArchiveEvent => 8,
                Region2NodeKind.Cache => 7,
                Region2NodeKind.Restoration => 6,
                Region2NodeKind.CursedArchive => 11,
                _ => 10,
            },
            Region2RunModifier.IronBindings => kind switch
            {
                Region2NodeKind.Combat => 12,
                Region2NodeKind.Ambush => 6,
                Region2NodeKind.Elite => 26,
                Region2NodeKind.MirrorChoice => 7,
                Region2NodeKind.ArchiveEvent => 8,
                Region2NodeKind.Cache => 18,
                Region2NodeKind.Restoration => 12,
                Region2NodeKind.CursedArchive => 11,
                _ => 10,
            },
            Region2RunModifier.MirrorDraft => kind switch
            {
                Region2NodeKind.Combat => 12,
                Region2NodeKind.Ambush => 10,
                Region2NodeKind.Elite => 9,
                Region2NodeKind.MirrorChoice => 28,
                Region2NodeKind.ArchiveEvent => 20,
                Region2NodeKind.Cache => 8,
                Region2NodeKind.Restoration => 10,
                Region2NodeKind.CursedArchive => 8,
                _ => 10,
            },
            Region2RunModifier.RedactedLedger => kind switch
            {
                Region2NodeKind.Combat => 8,
                Region2NodeKind.Ambush => 10,
                Region2NodeKind.Elite => 12,
                Region2NodeKind.MirrorChoice => 8,
                Region2NodeKind.ArchiveEvent => 12,
                Region2NodeKind.Cache => 18,
                Region2NodeKind.Restoration => 18,
                Region2NodeKind.CursedArchive => 28,
                _ => 10,
            },
            _ => 10,
        };
'''
t = replace_once(t, old_route_methods, new_route_methods, "weighted route composition")

# Replace the fixed/cyclic archetype rule. Elite Wardens remain untouched as the lead actor.
t = replace_once(
    t,
    '            int archetype = kind == Region2NodeKind.Ambush ? 0 : (index + depth) % 3;\n',
    '            int archetype = this.ResolveEncounterArchetype(kind, index, depth);\n',
    "encounter archetype composition",
)
t = replace_once(
    t,
    '        if (kind == Region2NodeKind.CursedArchive)\n        {\n            hpScale += 0.18f;\n            speed += 1;\n        }\n\n        int hp = Math.Max(1, (int)Math.Round(baseHp * hpScale));',
    '        if (kind == Region2NodeKind.CursedArchive)\n        {\n            hpScale += 0.18f;\n            speed += 1;\n        }\n\n        this.ApplyRunModifierEnemyStats(ref hpScale, ref speed);\n\n        int hp = Math.Max(1, (int)Math.Round(baseHp * hpScale));',
    "run modifier enemy stats",
)

# Record the actual composition spawned for deterministic diagnostics.
t = replace_once(
    t,
    '        Game1.playSound(kind == Region2NodeKind.Ambush ? "batScreech" : "wand");\n        this.Monitor.Log($"0683 Region II node {this.CurrentNode}/{this.TargetNodes} {kind}: spawned={spawned}.", LogLevel.Trace);\n',
    '        this.LastEncounterMix = DescribeEncounterMix(location);\n        Game1.playSound(kind == Region2NodeKind.Ambush ? "batScreech" : "wand");\n        this.Monitor.Log($"0685 Region II node {this.CurrentNode}/{this.TargetNodes} {kind}: modifier={this.ActiveRunModifier}, spawned={spawned}, mix={this.LastEncounterMix}.", LogLevel.Trace);\n',
    "encounter composition diagnostics",
)

# Run modifier helpers live beside enemy creation; 0684 room hazards remain a separate layer.
modifier_methods_anchor = '    private void ArmRoomMechanicForCombat(GameLocation location)\n'
need(modifier_methods_anchor in t, "room mechanic method anchor")
modifier_methods = r'''    private static Region2RunModifier PickRunModifier(Random random)
        => (Region2RunModifier)random.Next(Enum.GetValues<Region2RunModifier>().Length);

    private int ResolveEncounterArchetype(Region2NodeKind kind, int index, int depth)
    {
        int salt = unchecked(this.RunSeed + depth * 4099 + index * 8191 + (int)kind * 131);
        int roll = (int)((uint)salt % 100u);
        return this.ActiveRunModifier switch
        {
            Region2RunModifier.LooseFolios => roll < 58 ? 0 : roll < 84 ? 1 : 2,
            Region2RunModifier.IronBindings => roll < 15 ? 0 : roll < 45 ? 1 : 2,
            Region2RunModifier.MirrorDraft => roll % 3,
            Region2RunModifier.RedactedLedger => roll < 25 ? 0 : roll < 75 ? 1 : 2,
            _ => roll % 3,
        };
    }

    private void ApplyRunModifierEnemyStats(ref float hpScale, ref int speed)
    {
        switch (this.ActiveRunModifier)
        {
            case Region2RunModifier.LooseFolios:
                hpScale *= 0.88f;
                speed += 1;
                break;
            case Region2RunModifier.IronBindings:
                hpScale *= 1.18f;
                speed = Math.Max(1, speed - 1);
                break;
            case Region2RunModifier.RedactedLedger:
                hpScale *= 1.05f;
                break;
        }
    }

    private string RunModifierDisplayName()
        => ModEntry.T($"airship.region2.modifier.{RunModifierKey(this.ActiveRunModifier)}.name");

    private string RunModifierEffectText()
        => ModEntry.T($"airship.region2.modifier.{RunModifierKey(this.ActiveRunModifier)}.effect");

    private static string RunModifierKey(Region2RunModifier modifier) => modifier switch
    {
        Region2RunModifier.LooseFolios => "loose_folios",
        Region2RunModifier.IronBindings => "iron_bindings",
        Region2RunModifier.MirrorDraft => "mirror_draft",
        Region2RunModifier.RedactedLedger => "redacted_ledger",
        _ => "mirror_draft",
    };

    private static string DescribeEncounterMix(GameLocation location)
    {
        string[] roles = { "ink_moth", "paper_scarab", "dust_slime", "archive_warden" };
        List<string> parts = new();
        foreach (string role in roles)
        {
            int count = location.characters.OfType<Monster>().Count(m =>
                m.Health > 0
                && m.modData.ContainsKey(NodeMarkerKey)
                && m.modData.TryGetValue(RegionExpeditionService.EnemyRoleKey, out string? value)
                && value.Equals(role, StringComparison.OrdinalIgnoreCase));
            if (count > 0)
                parts.Add($"{role}:{count}");
        }
        return parts.Count == 0 ? "none" : string.Join(",", parts);
    }

'''
t = t.replace(modifier_methods_anchor, modifier_methods + modifier_methods_anchor, 1)

# Existing diagnostics now expose the rule and the last concrete encounter mix.
t = replace_once(
    t,
    'return $"0684 Region II Rogue: active={this.Active}, room={this.CurrentRoom}, node={this.CurrentNode}/{this.TargetNodes}, kind={this.CurrentKind}, interaction={this.AwaitingRoomInteraction}, mechanic={this.ActiveRoomMechanic}[{this.RoomMechanicCycles} cycles/{this.RoomMechanicHits} hits], "',
    'return $"0685 Region II Rogue: modifier={this.ActiveRunModifier}, mix={this.LastEncounterMix}, active={this.Active}, room={this.CurrentRoom}, node={this.CurrentNode}/{this.TargetNodes}, kind={this.CurrentKind}, interaction={this.AwaitingRoomInteraction}, mechanic={this.ActiveRoomMechanic}[{this.RoomMechanicCycles} cycles/{this.RoomMechanicHits} hits], "',
    "0685 modifier diagnostics",
)

# Clear the per-run identity on full runtime reset, while StartRun always selects a fresh deterministic rule.
t = replace_once(
    t,
    '        this.TargetNodes = 0;\n        this.UnbankedScrap = 0;\n',
    '        this.TargetNodes = 0;\n        this.ActiveRunModifier = Region2RunModifier.MirrorDraft;\n        this.LastEncounterMix = "none";\n        this.UnbankedScrap = 0;\n',
    "run modifier reset",
)

p.write_text(t, encoding="utf-8")

# Build label only. No new event hooks or rendering ownership changes in 0685.
mod_path = SRC / "ModEntry.cs"
mod = mod_path.read_text(encoding="utf-8")
mod = replace_once(
    mod,
    "0684 REGION II ROOM-SPECIFIC MECHANICS TEST",
    "0685 REGION II ENCOUNTER COMPOSITION + RUN MODIFIERS TEST",
    "0685 build label",
)
mod_path.write_text(mod, encoding="utf-8")

# EN/VI: make the run rule explicit once at run start, not as floating world text.
for lang, values in {
    "default.json": {
        "airship.region2.rogue.start": "FORGOTTEN ARCHIVE RUN • {{total}} nodes • Archive Rule: {{modifier}} • {{effect}}",
        "airship.region2.modifier.loose_folios.name": "Loose Folios",
        "airship.region2.modifier.loose_folios.effect": "Combat and Ambush routes recur more often; enemies skew faster but more fragile.",
        "airship.region2.modifier.iron_bindings.name": "Iron Bindings",
        "airship.region2.modifier.iron_bindings.effect": "Elite and Cache routes recur more often; enemies skew tougher but slower.",
        "airship.region2.modifier.mirror_draft.name": "Mirror Draft",
        "airship.region2.modifier.mirror_draft.effect": "Mirror and Archive Event routes recur more often; enemy archetypes stay deliberately mixed.",
        "airship.region2.modifier.redacted_ledger.name": "Redacted Ledger",
        "airship.region2.modifier.redacted_ledger.effect": "Cursed, Cache and Restoration routes recur more often; Paper Scarabs dominate the index.",
    },
    "vi.json": {
        "airship.region2.rogue.start": "CHUYẾN ĐI KHO LƯU TRỮ • {{total}} nút • Luật Kho: {{modifier}} • {{effect}}",
        "airship.region2.modifier.loose_folios.name": "Trang Rời",
        "airship.region2.modifier.loose_folios.effect": "Combat và Ambush xuất hiện thường hơn; quái thiên về nhanh nhưng mỏng hơn.",
        "airship.region2.modifier.iron_bindings.name": "Gáy Sắt",
        "airship.region2.modifier.iron_bindings.effect": "Elite và Cache xuất hiện thường hơn; quái thiên về trâu hơn nhưng chậm hơn.",
        "airship.region2.modifier.mirror_draft.name": "Bản Nháp Gương",
        "airship.region2.modifier.mirror_draft.effect": "Mirror và Archive Event xuất hiện thường hơn; đội hình quái được trộn đều có chủ đích.",
        "airship.region2.modifier.redacted_ledger.name": "Sổ Bôi Đen",
        "airship.region2.modifier.redacted_ledger.effect": "Cursed, Cache và Restoration xuất hiện thường hơn; Paper Scarab chiếm ưu thế trong đội hình.",
    },
}.items():
    ip = SRC / "i18n" / lang
    data = json.loads(ip.read_text(encoding="utf-8"))
    data.update(values)
    ip.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Rendering ownership is unchanged; advance only the audit's source branch marker.
audit_path = ROOT / "render_depth_audit.json"
audit = json.loads(audit_path.read_text(encoding="utf-8"))
audit["branch"] = BRANCH
meta = audit.get("renderedWorldSubscribers", {}).get("Region2Rogue", {})
need(meta.get("physicalAllowed") is False, "Region2Rogue render-depth classification regressed")
audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")

# Design note explains that 0685 varies whole-run rhythm rather than stacking arbitrary difficulty.
design_path = ROOT / "handoff" / "REGION2_ROGUELIKE_DESIGN_DIRECTION.md"
design = design_path.read_text(encoding="utf-8")
note = '''\n\n### 0685 implementation note\n\nRegion II now composes each run under one deterministic **Archive Rule** selected from the run seed. Loose Folios biases faster, more fragile pressure and Ambush/Combat routes; Iron Bindings biases heavier, slower enemies and Elite/Cache routes; Mirror Draft favors mixed enemy archetypes with Mirror/Event rhythm; Redacted Ledger favors Paper Scarabs and a Cursed/Cache/Restoration risk-reward loop. The modifier is shown once at run start and affects both route weighting and authored enemy composition. This is intended to make successive runs tactically different without turning the system into opaque random stat punishment. 0684 room-specific mechanics remain independent and stack on top of the selected run rule.\n'''
if "### 0685 implementation note" not in design:
    design += note
design_path.write_text(design, encoding="utf-8")

handoff = f'''# Alpha.28 0685 Region II Encounter Composition + Run Modifiers\n\nBranch: `{BRANCH}`\nBuild: `{NEW}`\nBase: 0684 Region II Room-Specific Mechanics\n\n## Purpose\n\n0685 adds a run-level composition layer above the existing 6–9 node route and 0684 room hazards. Each Region II run receives one deterministic Archive Rule that changes route weighting, enemy archetype composition and selected enemy pacing. The goal is for repeat runs to differ in tactical rhythm, not merely in RNG order.\n\n## Archive Rules\n\n- **Loose Folios / Trang Rời:** weights Combat and Ambush more heavily. Encounter rolls favor Ink Moths; enemies receive lower HP scaling but +1 Speed.\n- **Iron Bindings / Gáy Sắt:** weights Elite and Cache more heavily. Encounter rolls favor Dust Slimes; enemies receive higher HP scaling but -1 Speed with a safe floor.\n- **Mirror Draft / Bản Nháp Gương:** weights Mirror Choice and Archive Event more heavily. Enemy archetypes use an even deterministic mix with no extra stat tax.\n- **Redacted Ledger / Sổ Bôi Đen:** weights Cursed Archive, Cache and Restoration more heavily. Encounter rolls favor Paper Scarabs with a small HP premium, pairing recovery/reward opportunities with curse pressure.\n\nThe selected rule is derived from the run RNG after route length is chosen, so the same run seed is reproducible. The run intro displays the localized rule name and effect once.\n\n## Encounter composition\n\nThe old `Ambush => all Ink Moths` and cyclic `(index + depth) % 3` composition are replaced by a deterministic weighted archetype roll driven by the active Archive Rule. The Archive Warden remains the forced first Elite actor. `cardcha_region2_rogue_status` now reports both the active modifier and the last spawned role mix.\n\n## Preserved layers\n\n- 0684 Reflected Trace, Ink Sweep and Warden Seal are unchanged.\n- 0683 physical room interactions and route-end Final Cache remain physical/native.\n- Curator Records You remains active and receives the same run record contract.\n- Region II run target remains 6–9 nodes with checkpoints at 3 and 6.\n- Region II fare remains 250g.\n- Hollow Curator remains 2200 HP at the 40-card milestone.\n- Save schema remains 19.\n- Card audit remains 80 source / 76 active normal.\n- Region III/IV, Boss III/IV and accepted map/art assets are untouched.\n\n## Debug\n\n- `cardcha_test_region2`\n- `cardcha_expedition_clear`\n- `cardcha_region2_rogue_status`\n- `cardcha_region2_mechanic_status`\n- `cardcha_test_region2_bossgate`\n\n## Acceptance\n\nCI proves deterministic composition, frozen contracts and compile/package health only. In-game acceptance is pending. Compare several fresh Region II runs and verify that the intro rule matches the observed route/enemy rhythm, that Loose Folios feels fast rather than unfair, Iron Bindings feels deliberate rather than spongey, Mirror Draft creates useful mixed encounters, and Redacted Ledger produces a legible risk/recovery cadence. Also re-check all 0684 hazard telegraphs because they now stack with different enemy pacing.\n'''
(ROOT / "handoff" / "ALPHA28_0685_REGION2_ENCOUNTER_COMPOSITION_RUN_MODIFIERS.md").write_text(handoff, encoding="utf-8")
latest = f'''# Latest Cardcha Handoff\n\nCurrent branch: `{BRANCH}`\nCurrent build: `{NEW}`\nContinue from: `handoff/ALPHA28_0685_REGION2_ENCOUNTER_COMPOSITION_RUN_MODIFIERS.md`\nDesign direction: `handoff/REGION2_ROGUELIKE_DESIGN_DIRECTION.md`\n\n0685 preserves the 6–9 node multi-room run, 0683 physical interactions, 0684 room-specific mechanics and Curator Records You, while each run now selects one readable Archive Rule that biases route composition and enemy archetype/pacing. In-game acceptance is pending.\n'''
(ROOT / "handoff" / "LATEST_CARDCHA_HANDOFF.md").write_text(latest, encoding="utf-8")

print("0685 generator complete: run-level Archive Rules + weighted routes + deterministic enemy composition + EN/VI intro + docs.")
