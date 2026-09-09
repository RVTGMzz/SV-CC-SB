#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha"
AUDIT_PATH = ROOT / "render_depth_audit.json"
POLICY_PATH = ROOT / "CARDCHA_RENDERING_DEPTH_CONTRACT.md"
AGENTS_PATH = ROOT / "AGENTS.md"


def fail(message: str) -> None:
    raise SystemExit(f"RENDER DEPTH CONTRACT FAIL: {message}")


def normalized_markdown(text: str) -> str:
    """Normalize Markdown decoration/case so policy wording can evolve without weakening the contract."""
    text = text.lower()
    text = re.sub(r"[`*_#>|]", "", text)
    text = re.sub(r"[^a-z0-9./+ -]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


for required in (AUDIT_PATH, POLICY_PATH, AGENTS_PATH):
    if not required.exists():
        fail(f"missing required repository policy file: {required.relative_to(ROOT)}")

policy = POLICY_PATH.read_text(encoding="utf-8")
agents = AGENTS_PATH.read_text(encoding="utf-8")
policy_norm = normalized_markdown(policy)
agents_norm = normalized_markdown(agents)

# Validate the *meaningful contract phrases*, not Markdown punctuation/capitalization.
for token in (
    "no physical cardcha world object may be rendered as a display.renderedworld overlay",
    "ci success is not visual acceptance",
    "screenshot failure",
):
    if token not in policy_norm:
        fail(f"policy lost required contract phrase: {token}")
for token in (
    "physical world art must never be painted from display.renderedworld",
    "visual and gameplay anchors must be the same source of truth",
    "renderedworld is allowed only for transient non physical effects",
):
    if token not in agents_norm:
        fail(f"AGENTS.md lost required contract phrase: {token}")

audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
audited = audit.get("renderedWorldSubscribers", {})
if not audited:
    fail("render_depth_audit.json has no RenderedWorld subscriber audit")

mod_entry = (SRC / "ModEntry.cs").read_text(encoding="utf-8")
subscribers = re.findall(
    r"helper\.Events\.Display\.RenderedWorld\s*\+=\s*this\.([A-Za-z0-9_]+)\.OnRenderedWorld\s*;",
    mod_entry,
)
missing = sorted(set(subscribers) - set(audited))
stale = sorted(set(audited) - set(subscribers))
if missing:
    fail("new RenderedWorld subscriber(s) are not audited: " + ", ".join(missing))
if stale:
    fail("audit lists subscriber(s) no longer wired in ModEntry: " + ", ".join(stale))

for name, meta in audited.items():
    if meta.get("physicalAllowed") is not False:
        fail(f"{name}: physicalAllowed must remain false for every RenderedWorld subscriber")
    classification = str(meta.get("classification", ""))
    if not classification:
        fail(f"{name}: missing audit classification")

# Concrete regressions which caused real screenshots/runtime failures.
# These guards deliberately target architectural mistakes, not pixel offsets.
region_patch = (SRC / "Patches" / "RegionExpeditionProxyDrawPatch.cs").read_text(encoding="utf-8")
for token in (
    'AccessTools.DeclaredMethod(typeof(Monster), "draw", new[] { typeof(SpriteBatch) })',
    'SkipLegacyPostWorldEnemyDraw',
    '"DrawRegionIdentity"',
):
    if token not in region_patch:
        fail(f"Region III/IV actor-depth migration lost guard: {token}")
for token in ('typeof(GreenSlime)', 'typeof(Bat)', 'typeof(Bug)'):
    if token in region_patch:
        fail(f"Region III/IV draw patch regressed to subclass Harmony target: {token}")

attic = (SRC / "Services" / "MimiAtticVisualService.cs").read_text(encoding="utf-8")
for token in ("Furniture item =", 'map.GetLayer("Buildings")', "new StaticTile(buildings"):
    if token not in attic:
        fail(f"MiMi attic lost native-world depth ownership: {token}")

# A future change may remove these debt entries only by updating both source and audit.
# Until then CI requires every known unsafe location to remain explicitly recorded.
debt = set(audit.get("confirmedUnsafePhysicalPostWorld", []))
required_debt = {
    "AirshipInteriorStardewRenderer.DrawDeckStardewDecor",
    "AirshipInteriorStardewRenderer.DrawDockStardewDecor",
    "AirshipFoundationService.DrawRegion1Details",
    "Region1StardewDecorRenderer.Draw",
    "VerdantGuardianVisualService.boss-body",
    "VerdantGuardianSummonVisualService.summon-body",
    "VerdantGuardianArenaPolishService.DrawObelisks",
    "MilestoneBossService.DrawActor",
}
missing_debt = sorted(required_debt - debt)
if missing_debt:
    fail("known physical depth debt was removed from audit without a source migration: " + ", ".join(missing_debt))

# Do not allow the exact Region-I screenshot regression back in after 0676B fixes it.
airship = (SRC / "Services" / "AirshipFoundationService.cs").read_text(encoding="utf-8")
if "DrawRegion1Details(e.SpriteBatch, location);" in airship:
    print("RENDER DEPTH AUDIT WARNING: Region I physical overlay debt remains in legacy source but must be runtime-suppressed/migrated before visual acceptance.")
if "Region1StardewDecorRenderer.Draw(e.SpriteBatch, location, activeRoomIndex);" in airship:
    print("RENDER DEPTH AUDIT WARNING: Region I post-world decor debt remains in legacy source but must be runtime-suppressed/migrated before visual acceptance.")

print("Render depth contract PASS: every RenderedWorld subscriber is audited; no unaudited physical ownership may be introduced.")
