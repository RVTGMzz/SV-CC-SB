#!/usr/bin/env python3
from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha"
V = "0.3.0-alpha.28.0.4.14.4.5.12.53"
BRANCH = "cardcha-alpha28-0685-region2-encounter-composition-run-modifiers"


def need(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("0685 VALIDATION FAIL: " + msg)


manifest = json.loads((SRC / "manifest.json").read_text(encoding="utf-8"))
need(manifest.get("Version") == V, "manifest version mismatch")
for rel in ["Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
    need(V in (SRC / rel).read_text(encoding="utf-8"), rel + " version mismatch")

r2 = (SRC / "Services" / "Region2RoguelikeRunService.cs").read_text(encoding="utf-8")

# 0685 run-level composition contract.
for token in [
    "internal enum Region2RunModifier",
    "LooseFolios",
    "IronBindings",
    "MirrorDraft",
    "RedactedLedger",
    "private Region2RunModifier ActiveRunModifier = Region2RunModifier.MirrorDraft;",
    'private string LastEncounterMix = "none";',
    "this.ActiveRunModifier = PickRunModifier(random);",
    "private Region2NodeKind PickWeightedRoute(Random random, IEnumerable<Region2NodeKind> candidates)",
    "private static int RunModifierRouteWeight(Region2RunModifier modifier, Region2NodeKind kind)",
    "private int ResolveEncounterArchetype(Region2NodeKind kind, int index, int depth)",
    "private void ApplyRunModifierEnemyStats(ref float hpScale, ref int speed)",
    "Region2RunModifier.LooseFolios => roll < 58 ? 0 : roll < 84 ? 1 : 2",
    "Region2RunModifier.IronBindings => roll < 15 ? 0 : roll < 45 ? 1 : 2",
    "Region2RunModifier.MirrorDraft => roll % 3",
    "Region2RunModifier.RedactedLedger => roll < 25 ? 0 : roll < 75 ? 1 : 2",
    "hpScale *= 0.88f;",
    "hpScale *= 1.18f;",
    "hpScale *= 1.05f;",
    "speed += 1;",
    "speed = Math.Max(1, speed - 1);",
    "this.LastEncounterMix = DescribeEncounterMix(location);",
    "private static string DescribeEncounterMix(GameLocation location)",
]:
    need(token in r2, "0685 composition contract missing: " + token)

need('return $"0685 Region II Rogue: modifier={this.ActiveRunModifier}, mix={this.LastEncounterMix}' in r2, "0685 diagnostics missing modifier/mix")
need('modifier = this.RunModifierDisplayName()' in r2 and 'effect = this.RunModifierEffectText()' in r2, "run intro does not expose modifier")
need('int archetype = this.ResolveEncounterArchetype(kind, index, depth);' in r2, "old enemy composition still authoritative")
need('kind == Region2NodeKind.Ambush ? 0 : (index + depth) % 3' not in r2, "all-moth Ambush/cyclic composition survived")

# Route identity must be weighted, while anti-repeat/exclude behavior stays intact.
need('return this.PickWeightedRoute(random, deep);' in r2, "deep route is still uniform")
need('return this.PickWeightedRoute(random, candidates);' in r2, "normal route is still uniform")
need('.Where(k => k != previous && (!exclude.HasValue || k != exclude.Value))' in r2, "route anti-repeat/exclude contract regressed")
for token in [
    "Region2NodeKind.Ambush => 28",
    "Region2NodeKind.Elite => 26",
    "Region2NodeKind.MirrorChoice => 28",
    "Region2NodeKind.CursedArchive => 28",
]:
    need(token in r2, "signature route weight missing: " + token)

# 0684 room mechanics must remain a separate, intact tactical layer.
for token in [
    'RoomMechanicMarkerKey = "Ronvotri.Cardcha/0684RoomMechanic"',
    "MirrorTelegraphMs = 1050L",
    "InkTelegraphMs = 900L",
    "VaultTelegraphMs = 950L",
    'Region2RoomKind.MirrorGallery => "mirror_trace"',
    'Region2RoomKind.InkboundStacks => "ink_sweep"',
    'Region2RoomKind.WardenVault when this.CurrentKind == Region2NodeKind.Elite => "warden_seal"',
    "Game1.player.takeDamage(damage, false, null);",
    "public string DescribeRoomMechanic()",
]:
    need(token in r2, "0684 room mechanic regressed: " + token)

rw_start = r2.index("public void OnRenderedWorld")
rw_end = r2.index("public void OnButtonPressed", rw_start)
rw = r2[rw_start:rw_end]
for banned in ["Chest", "Furniture", "Texture2D", "DrawString", "room.setObject", "StaticTile", "Game1.objectSpriteSheet"]:
    need(banned not in rw, "physical/world-label content leaked into Region2 RenderedWorld: " + banned)
need("DrawHazardOutline" in rw and "RoomMechanicTiles" in rw, "0684 telegraph draw missing")

# 0683 physical interactions and route-end Final Cache remain physical/native.
need('InteractionMarkerKey = "Ronvotri.Cardcha/0683Region2Interaction"' in r2, "0683 interaction marker missing")
need("private void EnsureInteractionChest(GameLocation room, Point tile)" in r2, "physical interaction Chest support missing")
complete_start = r2.index("private void CompleteCurrentNode")
complete_end = r2.index("private void PrepareRouteChoice", complete_start)
complete = r2[complete_start:complete_end]
need("this.BeginNode(location, Region2NodeKind.FinalCache);" in complete, "route-end Final Cache is not routed to interaction")
need("this.AwardNode(Region2NodeKind.FinalCache);" not in complete, "Final Cache still auto-awards")

# Frozen roguelike structure and Curator observation contracts.
need("this.TargetNodes = 6 + random.Next(4)" in r2, "6-9 run length changed")
need("this.CurrentNode == 3 || this.CurrentNode == 6" in r2, "checkpoint 3/6 contract changed")
need("this.CuratorRecordSink?.Invoke(record);" in r2, "Curator Records You transfer regressed")
need("this.CurrentNode = 6;" in r2, "boss-gate debug depth changed")
need("nextNode >= 6" in r2, "optional Boss Gate timing changed")

# Localized Archive Rule intro and all four rules.
keys = [
    "airship.region2.modifier.loose_folios.name",
    "airship.region2.modifier.loose_folios.effect",
    "airship.region2.modifier.iron_bindings.name",
    "airship.region2.modifier.iron_bindings.effect",
    "airship.region2.modifier.mirror_draft.name",
    "airship.region2.modifier.mirror_draft.effect",
    "airship.region2.modifier.redacted_ledger.name",
    "airship.region2.modifier.redacted_ledger.effect",
]
for lang in ["default.json", "vi.json"]:
    data = json.loads((SRC / "i18n" / lang).read_text(encoding="utf-8"))
    start = data.get("airship.region2.rogue.start", "")
    need("{{modifier}}" in start and "{{effect}}" in start and "{{total}}" in start, lang + " run intro missing modifier placeholders")
    for key in keys:
        need(key in data and str(data[key]).strip(), lang + " missing " + key)

# No new rendering ownership. Audit advances branch only and Region2Rogue remains VFX-only.
audit = json.loads((ROOT / "render_depth_audit.json").read_text(encoding="utf-8"))
need(audit.get("branch") == BRANCH, "render-depth audit branch stale")
meta = audit.get("renderedWorldSubscribers", {}).get("Region2Rogue")
need(isinstance(meta, dict), "Region2Rogue missing from render-depth audit")
need(meta.get("physicalAllowed") is False, "Region2Rogue physicalAllowed must remain false")

# Four Region II maps remain structurally intact.
for name in [
    "region2_forgotten_archive.tmx",
    "region2_inkbound_stacks.tmx",
    "region2_mirror_gallery.tmx",
    "region2_warden_vault.tmx",
]:
    root = ET.parse(SRC / "assets" / name).getroot()
    need((int(root.attrib["width"]), int(root.attrib["height"])) == (40, 28), name + " dimensions changed")
    for layer in root.findall("layer"):
        vals = [x.strip() for x in (layer.find("data").text or "").split(",") if x.strip()]
        need(len(vals) == 1120, f'{name}:{layer.attrib.get("name")} CSV count {len(vals)} != 1120')
    ts = next((x for x in root.findall("tileset") if x.attrib.get("name") == "cardcha_region2_interactions"), None)
    need(ts is not None, name + " lost 0683 interaction tileset")

# Frozen progression/economy/boss/save/card contracts.
airship = (SRC / "Services" / "AirshipFoundationService.cs").read_text(encoding="utf-8")
need("private const int Region2Fare = 250;" in airship, "Region II fare changed")
boss = (SRC / "Services" / "MilestoneBossService.cs").read_text(encoding="utf-8")
need("HollowCuratorMaxHealth = 2200" in boss, "Boss II HP changed")
need('return (MilestoneBossKind.HollowCurator, 40, "The Hollow Curator")' in boss, "40-card milestone changed")
need("SetNextHollowCuratorRecord(CuratorRunRecord record)" in boss, "Curator Records You API regressed")
save = (SRC / "Services" / "SaveService.cs").read_text(encoding="utf-8")
need("19" in save, "save schema 19 token missing")
cards = json.loads((SRC / "assets" / "cards.json").read_text(encoding="utf-8"))
legacy = {"endless_hunt", "fate_weaver", "immortal_echo", "worldbreaker"}
ids = {str(c.get("Id", "")) for c in cards}
need(len(cards) == 80 and len(ids) == 80 and legacy.issubset(ids) and len(ids - legacy) == 76, "80/76 card audit changed")

# ModEntry and handoff trail.
mod = (SRC / "ModEntry.cs").read_text(encoding="utf-8")
need("0685 REGION II ENCOUNTER COMPOSITION + RUN MODIFIERS TEST" in mod, "0685 build label missing")
need("helper.Events.Display.RenderedWorld += this.Region2Rogue.OnRenderedWorld;" in mod, "0684 VFX event wiring lost")
latest = (ROOT / "handoff" / "LATEST_CARDCHA_HANDOFF.md").read_text(encoding="utf-8")
need("0685" in latest and V in latest and BRANCH in latest, "LATEST handoff not advanced to 0685")
need((ROOT / "handoff" / "ALPHA28_0685_REGION2_ENCOUNTER_COMPOSITION_RUN_MODIFIERS.md").exists(), "0685 handoff missing")
design = (ROOT / "handoff" / "REGION2_ROGUELIKE_DESIGN_DIRECTION.md").read_text(encoding="utf-8")
need("### 0685 implementation note" in design, "0685 design note missing")
need("### 0684 implementation note" in design, "0684 design note lost")
need("6–9 short nodes" in design, "6-9 route design lost")

print("0685 validation PASS: Archive Rules shape route + enemy composition, 0684/0683 layers and frozen progression/card/rendering contracts intact.")
