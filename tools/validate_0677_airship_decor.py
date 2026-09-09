#!/usr/bin/env python3
from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT = Path("src/Cardcha")
VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.45.3"

assert json.loads((ROOT / "manifest.json").read_text())["Version"] == VERSION
assert VERSION in (ROOT / "Cardcha.csproj").read_text()
assert VERSION in (ROOT / "Directory.Build.targets").read_text()
entry = (ROOT / "ModEntry.cs").read_text()
assert VERSION in entry and "AIRSHIP TWO-ROOM NATIVE DECOR REBUILD TEST" in entry

air = (ROOT / "Services/AirshipFoundationService.cs").read_text()
assert "0677-bridge" in air and "0677-dock" in air
assert air.count("TryAddInteriorFurniture(deck,") >= 18
assert air.count("TryAddInteriorFurniture(dock,") >= 19
assert "TryAddInteriorChest(dock, ResolveSkyDockLostFoundTile(dock));" in air
assert "Chest chest = new(true);" in air
assert "location.setObject(key, chest);" in air

renderer = (ROOT / "Services/AirshipInteriorStardewRenderer.cs").read_text()
assert "DrawDeckStardewDecor(batch);" not in renderer
assert "DrawDockStardewDecor(batch);" not in renderer
assert "DrawUpgradeStations(batch, save, phase);" not in renderer

for name, w, h, door in [
    ("airship_deck.tmx", 24, 14, {11, 12}),
    ("sky_dock_interior.tmx", 30, 18, {14, 15}),
]:
    root = ET.parse(ROOT / "assets" / name).getroot()
    layers = {x.attrib["name"]: x for x in root.findall("layer")}
    assert set(layers) >= {"Back", "BackDecor", "Buildings", "Front"}

    for lname in ("BackDecor", "Front"):
        vals = [int(x.strip()) for x in (layers[lname].find("data").text or "").split(",") if x.strip()]
        assert len(vals) == w * h and all(v == 0 for v in vals), f"{name}:{lname}"

    buildings = [int(x.strip()) for x in (layers["Buildings"].find("data").text or "").split(",") if x.strip()]
    assert len(buildings) == w * h
    for y in range(5, h - 1):
        for x in range(1, w - 1):
            assert buildings[y * w + x] == 0, f"{name}: unexpected interior blocker {x},{y}"
    for x in range(w):
        value = buildings[(h - 1) * w + x]
        if x in door:
            assert value == 0, f"{name}: doorway blocked at {x}"
        else:
            assert value != 0, f"{name}: perimeter open at {x}"

save = (ROOT / "Services/SaveService.cs").read_text()
assert "CurrentSchemaVersion = 19" in save
cards = json.loads((ROOT / "assets/cards.json").read_text())
assert len(cards) == 80
print("0677 native two-room decor validator PASS")
