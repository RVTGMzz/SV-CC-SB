#!/usr/bin/env python3
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha"
EXPECTED_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.55"
EXPECTED_BRANCH = "cardcha-alpha28-0687-tmx-csv-runtime-load-fix"
UINT32_MAX = 4294967295
TARGETS = {
    "boss2_hollow_curator_arena.tmx",
    "boss3_tricolor_resonance_arena.tmx",
    "boss4_mimi_resonance_arena.tmx",
    "region2_forgotten_archive.tmx",
    "region2_inkbound_stacks.tmx",
    "region2_mirror_gallery.tmx",
    "region2_warden_vault.tmx",
}


def need(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("0687 VALIDATION FAIL: " + msg)

manifest = json.loads((SRC / "manifest.json").read_text(encoding="utf-8"))
need(manifest.get("Version") == EXPECTED_VERSION, "manifest version mismatch")
for rel in ["Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
    need(EXPECTED_VERSION in (SRC / rel).read_text(encoding="utf-8"), f"{rel} build mismatch")

seen_targets = set()
checked_layers = 0
checked_files = 0
for path in sorted((SRC / "assets").rglob("*.tmx")):
    raw = path.read_text(encoding="utf-8")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise SystemExit(f"0687 VALIDATION FAIL: invalid XML {path.relative_to(ROOT)}: {exc}")
    if path.name in TARGETS:
        seen_targets.add(path.name)
    map_w = int(root.attrib.get("width", "0") or 0)
    map_h = int(root.attrib.get("height", "0") or 0)
    had_csv = False
    for layer in root.findall("layer"):
        data = layer.find("data")
        if data is None or data.attrib.get("encoding") != "csv":
            continue
        had_csv = True
        checked_layers += 1
        body = data.text or ""
        # Match TMXTile's runtime behavior: every comma-separated token must parse.
        tokens = [part.strip() for part in body.split(',')]
        need(tokens and all(token != "" for token in tokens),
             f"empty CSV token in {path.name}/{layer.attrib.get('name','?')}")
        vals = []
        for token in tokens:
            need(re.fullmatch(r"\d+", token) is not None,
                 f"non-uint CSV token {token!r} in {path.name}/{layer.attrib.get('name','?')}")
            value = int(token)
            need(0 <= value <= UINT32_MAX,
                 f"GID outside UInt32 in {path.name}/{layer.attrib.get('name','?')}")
            vals.append(value)
        width = int(layer.attrib.get("width", map_w) or map_w)
        height = int(layer.attrib.get("height", map_h) or map_h)
        need(width > 0 and height > 0, f"invalid layer dimensions in {path.name}")
        need(len(vals) == width * height,
             f"tile count mismatch {path.name}/{layer.attrib.get('name','?')}: {len(vals)} != {width*height}")
    if had_csv:
        checked_files += 1

need(seen_targets == TARGETS, "missing reported runtime-failure TMX target(s): " + ", ".join(sorted(TARGETS - seen_targets)))
need(checked_files > 0 and checked_layers > 0, "no CSV TMX layers checked")

# 0687 is serialization-only. Keep a small identity lock for the 0686 boss handoff;
# the workflow separately proves all TMX non-empty GID sequences are byte-order equivalent to 0686.
r2 = (SRC / "Services" / "Region2RoguelikeRunService.cs").read_text(encoding="utf-8")
boss = (SRC / "Services" / "MilestoneBossService.cs").read_text(encoding="utf-8")
need("BindCuratorArchiveRuleSink" in r2 and "CuratorArchiveRuleSink?.Invoke" in r2, "0686 Archive Rule transfer missing")
for key in ["loose_folios", "iron_bindings", "mirror_draft", "redacted_ledger"]:
    need(key in boss or key in r2, f"Archive Rule {key} missing")
need("new[] { 0, 0, 1 }" in boss, "Hollow Curator phase 1 changed")

latest = (ROOT / "handoff" / "LATEST_CARDCHA_HANDOFF.md").read_text(encoding="utf-8")
need(EXPECTED_BRANCH in latest and EXPECTED_VERSION in latest and "0687" in latest, "latest handoff mismatch")
need((ROOT / "handoff" / "ALPHA28_0687_TMX_CSV_RUNTIME_LOAD_FIX.md").exists(), "0687 handoff missing")

audit = (ROOT / "render_depth_audit.json").read_text(encoding="utf-8")
need(EXPECTED_BRANCH in audit, "render audit branch marker mismatch")
need('"physicalAllowed": false' in audit, "render-depth physicalAllowed locks missing")

print(f"0687 VALIDATION PASS: {checked_files} TMX file(s), {checked_layers} CSV layer(s), no empty tokens, all UInt32 and exact tile counts.")
