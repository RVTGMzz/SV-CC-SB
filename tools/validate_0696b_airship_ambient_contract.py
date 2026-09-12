#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json
import xml.etree.ElementTree as ET
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src/Cardcha"
MANIFEST_PATH = SRC / "assets/airship_props/set01_redux/airship_ambient_manifest.json"
REPORT_PATH = ROOT / "handoff/AIRSHIP_AMBIENT_CONTRACT_VALIDATION_0696B.json"
EXPECTED_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.63"


def image_size(path: Path) -> tuple[int, int] | None:
    if not path.exists():
        return None
    with Image.open(path) as im:
        return im.size


def validate_map(path: Path) -> list[str]:
    root = ET.parse(path).getroot()
    names = [x.attrib.get("name", "") for x in root.findall("layer")]
    assert "BackDecor" not in names, f"{path.name}: BackDecor returned"
    for required in ["Back", "Back2", "Buildings", "Buildings2", "Front", "Front2"]:
        assert required in names, f"{path.name}: missing {required}"
    return names


def main() -> None:
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert data["schemaVersion"] == 1
    assert data["version"] == EXPECTED_VERSION
    assert data["visualAcceptance"] == "PENDING-RON-IN-GAME"
    assert data["global"]["tileSize"] == 16
    assert data["validation"]["collisionOwnedBy"] == "Buildings"
    assert "BackDecor" in data["validation"]["forbiddenLayers"]

    window = data["observationWindow"]
    console = data["navigationConsole"]
    assert window["footprintPx"] == {"width": 160, "height": 80}
    assert window["footprintTiles"] == {"width": 10, "height": 5}
    assert window["worldAnchor"]["tileX"] == 7 and window["worldAnchor"]["tileY"] == 1
    assert window["viewportPx"] == {"x": 16, "y": 14, "width": 128, "height": 42}
    assert console["footprintPx"] == {"width": 112, "height": 80}
    assert console["footprintTiles"] == {"width": 7, "height": 5}
    assert console["worldAnchor"]["tileX"] == 9 and console["worldAnchor"]["tileY"] == 5
    assert console["viewportPx"] == {"x": 18, "y": 8, "width": 48, "height": 32}

    # Approved fallback must remain exact and available until new production art exists.
    fallback_paths = window["legacyFallback"]["paths"] + console["legacyFallback"]["paths"]
    missing_fallback = [p for p in fallback_paths if not (SRC / p).exists()]
    assert not missing_fallback, f"missing approved legacy fallback: {missing_fallback}"

    planned: list[dict] = []
    def check_planned(path_str: str, expected: tuple[int, int] | None = None, required_now: bool = False) -> None:
        path = SRC / path_str
        size = image_size(path)
        status = "present" if size else "pending"
        if required_now:
            assert size is not None, f"required production asset missing: {path_str}"
        if size is not None and expected is not None:
            assert size == expected, f"{path_str}: {size} != {expected}"
        planned.append({"path": path_str, "status": status, "size": list(size) if size else None})

    check_planned(window["frame"]["path"], (160, 80))
    check_planned(window["mask"]["path"], (160, 80))
    for season, states in window["backdrops"]["states"].items():
        for bucket, path in states.items():
            check_planned(path)
    for weather, fx in window["weatherFx"].items():
        check_planned(fx["path"])
    for path in window["lightning"]["paths"]:
        check_planned(path)

    check_planned(console["frame"]["path"], (112, 80))
    for name, layer in console["layers"].items():
        check_planned(layer["path"])

    # Code contract checks.
    model = (SRC / "Models/AirshipAmbientManifest.cs").read_text(encoding="utf-8")
    resolver = (SRC / "Services/AirshipAmbientResolver.cs").read_text(encoding="utf-8")
    runtime = (SRC / "Services/AirshipAmbientAnimationService.cs").read_text(encoding="utf-8")
    renderer = (SRC / "Services/AirshipInteriorStardewRenderer.cs").read_text(encoding="utf-8")
    assert "class AirshipAmbientManifest" in model
    assert "ResolveTimeBucket" in resolver and "ResolveWeather" in resolver
    assert "DrawDeckAmbient" in runtime
    assert "AirshipAmbientAnimationService.DrawDeckAmbient(batch);" in renderer

    deck_layers = validate_map(SRC / "assets/airship_deck.tmx")
    dock_layers = validate_map(SRC / "assets/sky_dock_interior.tmx")

    version = json.loads((SRC / "manifest.json").read_text(encoding="utf-8"))["Version"]
    assert version == EXPECTED_VERSION, version

    present = [x for x in planned if x["status"] == "present"]
    pending = [x for x in planned if x["status"] == "pending"]
    report = {
        "phase": "0696B-airship-ambient-runtime-foundation",
        "build": EXPECTED_VERSION,
        "technicalValidation": "PASS",
        "visualAcceptance": "PENDING-RON-IN-GAME",
        "newAmbientArtState": "PENDING_PRODUCTION" if pending else "READY_FOR_IN_GAME_ACCEPTANCE",
        "legacyFallbackCount": len(fallback_paths),
        "legacyFallbackMissing": missing_fallback,
        "plannedAssetCount": len(planned),
        "plannedPresentCount": len(present),
        "plannedPendingCount": len(pending),
        "plannedAssets": planned,
        "deckLayers": deck_layers,
        "dockLayers": dock_layers,
        "notes": [
            "Technical PASS only validates contract/runtime wiring.",
            "New ambient art is allowed to be pending; approved 0690 fallback remains active.",
            "Visual acceptance remains Ron-only and requires in-game testing after production assets exist."
        ]
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
