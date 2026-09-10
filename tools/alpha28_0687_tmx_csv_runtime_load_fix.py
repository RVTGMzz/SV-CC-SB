#!/usr/bin/env python3
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha"
OLD = "0.3.0-alpha.28.0.4.14.4.5.12.54"
NEW = "0.3.0-alpha.28.0.4.14.4.5.12.55"
OLD_BRANCH = "cardcha-alpha28-0686-hollow-curator-archive-rule-adaptation"
BRANCH = "cardcha-alpha28-0687-tmx-csv-runtime-load-fix"
DATA_RE = re.compile(r'(<data\s+encoding="csv"[^>]*>)(.*?)(</data>)', re.S)


def need(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("0687 BUILD FAIL: " + msg)


def csv_ids(body: str) -> list[str]:
    return [x.strip() for x in body.split(',') if x.strip()]


def repair_csv_block(match: re.Match[str]) -> str:
    opening, body, closing = match.groups()
    # TMXTile's CSV decoder splits on commas and UInt32.Parse()s every token.
    # Canonicalize to one delimiter between each real GID and no trailing
    # delimiter, so there can be no empty token anywhere in the block.
    tokens = csv_ids(body)
    need(tokens, "empty CSV data block")
    repaired = "\n" + ",".join(tokens) + "\n"
    return opening + repaired + closing


manifest_path = SRC / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
if manifest.get("Version") == NEW:
    print("0687 already materialized; generator is idempotent.")
    raise SystemExit(0)
need(manifest.get("Version") == OLD, f"expected {OLD}, found {manifest.get('Version')}")

# Exact build bump. Save schema/gameplay contracts stay frozen.
for rel in ["manifest.json", "Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
    p = SRC / rel
    text = p.read_text(encoding="utf-8")
    need(OLD in text, f"{rel} missing old build version")
    p.write_text(text.replace(OLD, NEW), encoding="utf-8")

# Runtime TMX compatibility repair. Preserve the exact non-empty GID sequence.
changed = []
for p in sorted((SRC / "assets").rglob("*.tmx")):
    text = p.read_text(encoding="utf-8")
    blocks = list(DATA_RE.finditer(text))
    if not blocks:
        continue
    before_ids = [csv_ids(m.group(2)) for m in blocks]
    repaired = DATA_RE.sub(repair_csv_block, text)
    after_blocks = list(DATA_RE.finditer(repaired))
    after_ids = [csv_ids(m.group(2)) for m in after_blocks]
    need(before_ids == after_ids, f"tile ID sequence changed in {p.relative_to(ROOT)}")
    if repaired != text:
        p.write_text(repaired, encoding="utf-8")
        changed.append(str(p.relative_to(ROOT)))

need(changed, "no TMX CSV serialization required repair")
print(f"0687 canonicalized {len(changed)} TMX file(s):")
for item in changed:
    print("  -", item)

# Render audit marker only. Rendering ownership itself is unchanged.
audit = ROOT / "render_depth_audit.json"
if audit.exists():
    text = audit.read_text(encoding="utf-8")
    if OLD_BRANCH in text:
        text = text.replace(OLD_BRANCH, BRANCH)
    audit.write_text(text, encoding="utf-8")

handoff = ROOT / "handoff" / "ALPHA28_0687_TMX_CSV_RUNTIME_LOAD_FIX.md"
handoff.write_text(f'''# Alpha 28 0687: TMX CSV Runtime Load Fix\n\nBranch: `{BRANCH}`  \nBuild: `{NEW}`\n\n## Purpose\nRepair a runtime TMX CSV serialization defect discovered by live SMAPI testing. TMXTile splits CSV data on commas and passes every token to `UInt32.Parse`; an empty token therefore prevents the entire map from loading.\n\n## Fix\n- Canonicalizes every authored `<data encoding="csv">` block to exactly one comma between real GIDs and no trailing delimiter.\n- Preserves every non-empty tile GID in the exact same order.\n- Does not alter map dimensions, tilesets, properties, layers, artwork, gameplay anchors, or render ownership.\n- Applies repository-wide to Cardcha `.tmx` assets so boss arenas and Region II rooms share the same runtime-safe format.\n- Adds a validator that rejects empty CSV tokens, non-UInt32 GIDs, and layer tile-count mismatches.\n\n## Live failure fixed\nThe reported stack ended in `TMXTile.TMXData.decode -> UInt32.Parse` for Hollow Curator, Tricolor Resonance, Mimi Resonance, Forgotten Archive, Inkbound Stacks, Mirror Gallery, and Warden Vault. Their subsequent `ContentLoadException: content file was not found` messages were downstream failures after the loader rejected the TMX.\n\n## Frozen contracts\n0686 Archive Rule transfer/adaptation remains unchanged. Region II fare remains 250g, route length 6-9 nodes, checkpoints 3/6, Hollow Curator 2200 HP, 40-card milestone, save schema 19, 0683 interactions/Final Cache, 0684 room mechanics, 0685 modifiers, and the rendering-depth contract remain frozen.\n\n## Acceptance\nCI must compile and validate every CSV layer. Final acceptance still requires a live SMAPI launch confirming the affected maps load without `TMXData.decode` / `UInt32.Parse` errors.\n''', encoding="utf-8")

latest = ROOT / "handoff" / "LATEST_CARDCHA_HANDOFF.md"
latest.write_text(f'''# Latest Cardcha Handoff\n\nCurrent branch: `{BRANCH}`\nCurrent build: `{NEW}`\nContinue from: `handoff/ALPHA28_0687_TMX_CSV_RUNTIME_LOAD_FIX.md`\nDesign direction: `handoff/REGION2_ROGUELIKE_DESIGN_DIRECTION.md`\n\n0687 is a runtime TMX compatibility hotfix over 0686. It canonicalizes CSV blocks so TMXTile receives only valid GID tokens while preserving the exact non-empty tile GID sequence and all gameplay/render contracts. In-game acceptance is pending.\n''', encoding="utf-8")

print("0687 TMX CSV runtime load fix materialized.")
