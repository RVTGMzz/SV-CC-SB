#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/Cardcha"
ASSETS = SRC / "assets"

OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.58"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.59"
BRANCH = "cardcha-alpha28-0692-airship-rgba-gate-restore"
PARENT_BRANCH = "cardcha-alpha28-0691-airship-prop-set02-harbor-furnishings"
PARENT_HEAD = "91b9166e915f0b50a3dd23b0cb5e8fb888191974"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


# Version bump first. This pass is a runtime-visibility hotfix, not a visual redesign.
for rel in ["manifest.json", "Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
    p = SRC / rel
    if not p.exists():
        continue
    s = read(p).replace(OLD_VERSION, NEW_VERSION)
    if rel == "ModEntry.cs":
        s = s.replace(
            "0691 AIRSHIP PROP SET02 HARBOR FURNISHINGS TEST",
            "0692 AIRSHIP RGBA GATE RESTORE TEST",
        )
    write(p, s)


# -----------------------------------------------------------------------------
# 0692 texture contract
# -----------------------------------------------------------------------------
# xTile/TMX is much less forgiving than SMAPI's direct Texture2D loader. The
# 0690/0691 prop materializers left several production PNGs as indexed/palette
# images (PNG color type 3). They looked fine in file previews, but the in-game
# TMX renderer dropped the whole custom GID group on the affected setup.
#
# Every physical TMX texture is now exported as true RGBA (PNG color type 6),
# and a flat production copy sits next to the TMX. This removes BOTH variables:
# indexed PNG decoding and nested relative image paths.

SET01 = ASSETS / "airship_props/set01_redux"
SET02 = ASSETS / "airship_props/set02_harbor"


def rgba_copy(src: Path, dst: Path) -> None:
    if not src.exists():
        raise RuntimeError(f"missing source texture: {src}")
    image = Image.open(src).convert("RGBA")
    dst.parent.mkdir(parents=True, exist_ok=True)
    image.save(dst, format="PNG", optimize=True)


physical: dict[str, tuple[Path, str]] = {
    "route": (SET01 / "route_notice_board.png", "airship_0692_route_notice_board.png"),
    "gate": (SET01 / "boarding_gate_arch.png", "airship_0692_boarding_gate_arch.png"),
    "signal": (SET01 / "signal_lamp.png", "airship_0692_signal_lamp.png"),
    "cargo": (SET01 / "cargo_parcel_crate.png", "airship_0692_cargo_parcel_crate.png"),
    "window": (SET01 / "observation_window_base.png", "airship_0692_observation_window.png"),
    "console": (SET01 / "navigation_console_base.png", "airship_0692_navigation_console.png"),
    "collision": (SET01 / "collision_blocker.png", "airship_0692_collision_blocker.png"),
    "departures": (SET02 / "departures_schedule_board.png", "airship_0692_departures_schedule_board.png"),
    "bench": (SET02 / "waiting_bench.png", "airship_0692_waiting_bench.png"),
    "luggage": (SET02 / "luggage_cart.png", "airship_0692_luggage_cart.png"),
}

# Normalize the source library in place too, then make flat TMX production copies.
for source, flat_name in physical.values():
    rgba_copy(source, source)
    rgba_copy(source, ASSETS / flat_name)

# 0690 runtime-only overlays remain runtime-only, but normalize them as well so
# there is no mixed indexed/RGBA Airship asset contract left behind.
for stem in ("observation_window_overlay", "navigation_console_overlay"):
    for frame in range(1, 5):
        p = SET01 / f"{stem}_{frame}.png"
        rgba_copy(p, p)

# Exterior authored gate already was RGBA in 0691; rewrite it deterministically
# so the validator can enforce one texture contract for every Airship gate path.
rgba_copy(ASSETS / "airship_gate_auth.png", ASSETS / "airship_gate_auth.png")


def set_property(root: ET.Element, name: str, value: str) -> None:
    props = root.find("properties")
    if props is None:
        props = ET.Element("properties")
        root.insert(0, props)
    for prop in props.findall("property"):
        if prop.attrib.get("name") == name:
            prop.set("value", value)
            return
    ET.SubElement(props, "property", {"name": name, "value": value})


def repoint_tilesets(path: Path, sources: dict[str, str]) -> None:
    tree = ET.parse(path)
    root = tree.getroot()
    found: set[str] = set()
    for ts in root.findall("tileset"):
        name = ts.attrib.get("name", "")
        if name not in sources:
            continue
        image = ts.find("image")
        if image is None:
            raise RuntimeError(f"{path.name}/{name}: missing image node")
        image.set("source", sources[name])
        found.add(name)
    missing = set(sources) - found
    if missing:
        raise RuntimeError(f"{path.name}: missing tilesets {sorted(missing)}")
    set_property(root, "CardchaTextureContract", "0692|flat-rgba-tmx-textures|png-color-type-6")
    ET.indent(tree, space=" ")
    tree.write(path, encoding="UTF-8", xml_declaration=True)


repoint_tilesets(
    ASSETS / "sky_dock_interior.tmx",
    {
        "CardchaRouteNoticeBoard0690": physical["route"][1],
        "CardchaBoardingGate0690": physical["gate"][1],
        "CardchaSignalLamp0690": physical["signal"][1],
        "CardchaCargoCrate0690": physical["cargo"][1],
        "CardchaCollision0690": physical["collision"][1],
        "CardchaDeparturesBoard0691": physical["departures"][1],
        "CardchaWaitingBench0691": physical["bench"][1],
        "CardchaLuggageCart0691": physical["luggage"][1],
    },
)
repoint_tilesets(
    ASSETS / "airship_deck.tmx",
    {
        "CardchaObservationWindow0690": physical["window"][1],
        "CardchaNavigationConsole0690": physical["console"][1],
        "CardchaSignalLamp0690": physical["signal"][1],
        "CardchaCollision0690": physical["collision"][1],
    },
)


# -----------------------------------------------------------------------------
# Exterior gate depth hotfix
# -----------------------------------------------------------------------------
# 0676B correctly suppresses the old post-world DrawSkyDock path by Harmony
# prefixing DrawSkyDock() with `return false`. But DrawForestGateAtFarmerDepth()
# also called that SAME method, so the valid farmer-depth path got suppressed too.
# Keep DrawSkyDock as the intentionally blocked legacy wrapper and route the
# farmer-depth path straight to an unpatched core implementation.
service_path = SRC / "Services/AirshipFoundationService.cs"
service = read(service_path)
old_call = "this.DrawSkyDock(batch, this.ResolveSkyDockTile());"
new_call = "this.DrawSkyDockCore(batch, this.ResolveSkyDockTile());"
if service.count(old_call) != 1:
    raise RuntimeError(f"expected exactly one farmer-depth DrawSkyDock call, found {service.count(old_call)}")
service = service.replace(old_call, new_call, 1)

needle = """    private void DrawSkyDock(SpriteBatch batch, Point tile)\n    {\n        Texture2D? gate = this.GetAirshipGateVisual();"""
replacement = """    private void DrawSkyDock(SpriteBatch batch, Point tile)\n    {\n        // 0692: legacy wrapper only. AirshipGateDepthPatch intentionally suppresses this method\n        // so a post-world physical gate can never cover the farmer.\n        this.DrawSkyDockCore(batch, tile);\n    }\n\n    private void DrawSkyDockCore(SpriteBatch batch, Point tile)\n    {\n        Texture2D? gate = this.GetAirshipGateVisual();"""
if service.count(needle) != 1:
    raise RuntimeError("could not locate unique DrawSkyDock implementation anchor")
service = service.replace(needle, replacement, 1)
write(service_path, service)


# Render-depth audit: this fixes ownership/routing; it does NOT re-enable physical
# furniture in Display.RenderedWorld.
audit_path = ROOT / "render_depth_audit.json"
audit = json.loads(read(audit_path))
audit["branch"] = BRANCH
done = audit.setdefault("completedDepthMigrations", [])
for marker in [
    "0692 Airship TMX physical textures->flat true RGBA PNG color type 6",
    "0692 exterior gate farmer-depth path->unpatched DrawSkyDockCore; legacy DrawSkyDock remains suppressed",
]:
    if marker not in done:
        done.append(marker)
write(audit_path, json.dumps(audit, indent=2) + "\n")


handoff = ROOT / "handoff/ALPHA28_0692_AIRSHIP_RGBA_GATE_RESTORE.md"
handoff.write_text(
    f"""# Alpha 28 0692 — Airship RGBA + Gate Restore Hotfix

## Source of truth
- Branch: `{BRANCH}`
- Parent: `{PARENT_BRANCH}` @ `{PARENT_HEAD}`
- Build: `{NEW_VERSION}`

## Trigger
Ron tested 0691 in-game and reported a visual regression:
- the authored outdoor boarding gate was missing;
- the new Airship/Sky Dock physical prop group was largely absent even though the assets were present in the package;
- the room therefore fell back visually to sparse inherited/procedural elements.

## Root causes addressed
1. 0690/0691 TMX prop PNGs were left as indexed/palette PNGs on the production path. 0692 normalizes every physical Airship TMX prop to true RGBA and points TMX at flat, same-directory production copies.
2. `AirshipGateDepthPatch` suppresses legacy `DrawSkyDock()` by design, but the valid farmer-depth draw path also called `DrawSkyDock()`. 0692 introduces `DrawSkyDockCore()`; the Harmony-blocked wrapper stays legacy-only while farmer-depth rendering calls the unpatched core directly.

## Visual design
No visual redesign. The approved `boarding_gate_arch.png` remains the gate design. No old gate is restored.

## Rendering contract
- Interior physical props remain TMX-owned.
- Existing 0690 window/console motion remains VFX-only.
- No new physical `RenderedWorld` furniture is introduced.
- Exterior gate stays farmer-depth injected via the existing Harmony contract.

## Acceptance
CI/build/package status is determined by the 0692 workflow.
In-game visual acceptance remains PENDING until Ron tests the resulting TEST package.
""",
    encoding="utf-8",
)

(ROOT / "handoff/LATEST_CARDCHA_HANDOFF.md").write_text(
    f"""# Latest Cardcha Handoff

Current source-of-truth branch: `{BRANCH}`

Current build: `{NEW_VERSION}`

Current handoff: `handoff/ALPHA28_0692_AIRSHIP_RGBA_GATE_RESTORE.md`

Parent source-of-truth: `{PARENT_BRANCH}` @ `{PARENT_HEAD}`

Status: 0692 runtime-visibility hotfix materialized; CI/package status must be read from the completed 0692 workflow. In-game visual acceptance is PENDING.
""",
    encoding="utf-8",
)

print("0692 Airship RGBA + gate restore materialized")
