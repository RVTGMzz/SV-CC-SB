#!/usr/bin/env python3
from pathlib import Path
import json
import re
import textwrap
import xml.etree.ElementTree as ET

OLD = "0.3.0-alpha.28.0.4.14.4.5.12.45.2"
NEW = "0.3.0-alpha.28.0.4.14.4.5.12.45.3"
ROOT = Path("src/Cardcha")


def bump_versions() -> None:
    for rel in ["manifest.json", "Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        if OLD not in text:
            # Idempotent materialization: a later CI retry can run after source was committed.
            if NEW in text:
                continue
            raise SystemExit(f"{rel}: expected baseline version {OLD} missing")
        text = text.replace(OLD, NEW)
        text = text.replace(
            "REGION LAYERING + MAP CLEANUP + GATE ALIGNMENT + WORLD DEPTH SAFETY HOTFIX TEST",
            "AIRSHIP TWO-ROOM NATIVE DECOR REBUILD TEST",
        )
        path.write_text(text, encoding="utf-8")


def rebuild_airship_service() -> None:
    path = ROOT / "Services/AirshipFoundationService.cs"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r'private const string InteriorDecorVersion = "[^"]+";',
        'private const string InteriorDecorVersion = "alpha.28.0.4.14.4.5.12.45.3";',
        text,
        count=1,
    )

    if "-0677-bridge" in text and "TryAddInteriorChest" in text:
        path.write_text(text, encoding="utf-8")
        return

    start = text.index("    private void EnsureDeckVanillaFurniture(GameLocation deck)")
    end = text.index(
        "    private static (AirshipUpgradeSystem System, Point Tile)[] ResolveDeckUpgradeSockets()",
        start,
    )

    replacement = textwrap.dedent(r'''
        private void EnsureDeckVanillaFurniture(GameLocation deck)
        {
            if (ReferenceEquals(this.DeckDecorAppliedLocation, deck)
                && deck.modData.TryGetValue(InteriorDecorMarkerKey, out string? version)
                && string.Equals(version, InteriorDecorVersion + "-0677-bridge", StringComparison.Ordinal))
            {
                return;
            }

            this.DeckDecorAppliedLocation = deck;
            ClearInteriorDecor(deck);

            // 0677: Bridge is a lived-in flying workshop, not a showroom and not a test grid.
            // Wall identity. Real Stardew furniture owns collision and draw depth.
            TryAddInteriorFurniture(deck, "(F)1614", 5, 1);
            TryAddInteriorFurniture(deck, "(F)1614", 17, 1);
            TryAddInteriorFurniture(deck, "(F)1541", 9, 1);
            TryAddInteriorFurniture(deck, "(F)1541", 14, 1);
            TryAddInteriorFurniture(deck, "(F)1289", 2, 4);
            TryAddInteriorFurniture(deck, "(F)1289", 20, 4);

            // LEFT: engine / hull workshop. Main x=10..14 spine stays clear.
            TryAddInteriorFurniture(deck, "(F)1443", 3, 5);
            TryAddInteriorFurniture(deck, "(F)1120", 3, 7, heldId: "(F)1369");
            TryAddInteriorFurniture(deck, "(F)1399", 2, 10, heldId: "(F)1369");
            TryAddInteriorFurniture(deck, "(F)1390", 5, 10);
            TryAddInteriorFurniture(deck, "(F)704", 6, 10);

            // RIGHT: navigation / resonance workshop.
            TryAddInteriorFurniture(deck, "(F)1443", 20, 5);
            TryAddInteriorFurniture(deck, "(F)1132", 18, 7, heldId: "(F)1368");
            TryAddInteriorFurniture(deck, "(F)1399", 20, 10, heldId: "(F)1369");
            TryAddInteriorFurniture(deck, "(F)1390", 18, 10);
            TryAddInteriorFurniture(deck, "(F)1132", 15, 10, heldId: "(F)1368");

            // Rugs group functions without blocking movement.
            TryAddInteriorFurniture(deck, "(F)1456", 9, 6);
            TryAddInteriorFurniture(deck, "(F)1623", 2, 9);
            TryAddInteriorFurniture(deck, "(F)1623", 18, 9);

            deck.modData[InteriorDecorMarkerKey] = InteriorDecorVersion + "-0677-bridge";
        }

        private void EnsureSkyDockVanillaFurniture(GameLocation dock)
        {
            if (ReferenceEquals(this.SkyDockDecorAppliedLocation, dock)
                && dock.modData.TryGetValue(InteriorDecorMarkerKey, out string? version)
                && string.Equals(version, InteriorDecorVersion + "-0677-dock", StringComparison.Ordinal))
            {
                return;
            }

            this.SkyDockDecorAppliedLocation = dock;
            ClearInteriorDecor(dock);

            // Wall rhythm creates three visual bays instead of one empty rectangle.
            TryAddInteriorFurniture(dock, "(F)1614", 4, 1);
            TryAddInteriorFurniture(dock, "(F)1614", 14, 1);
            TryAddInteriorFurniture(dock, "(F)1614", 24, 1);
            TryAddInteriorFurniture(dock, "(F)1541", 9, 1);
            TryAddInteriorFurniture(dock, "(F)1541", 20, 1);

            // LEFT: service / Lost & Found.
            TryAddInteriorFurniture(dock, "(F)1289", 2, 5);
            TryAddInteriorFurniture(dock, "(F)1443", 2, 8);
            TryAddInteriorFurniture(dock, "(F)1399", 3, 9, heldId: "(F)1369");
            TryAddInteriorFurniture(dock, "(F)1390", 7, 11);
            TryAddInteriorFurniture(dock, "(F)1623", 2, 10);
            TryAddInteriorChest(dock, ResolveSkyDockLostFoundTile(dock));

            // ROUTE DESK: frame the real route tile, never cover it.
            TryAddInteriorFurniture(dock, "(F)1120", 6, 5, heldId: "(F)1368");
            TryAddInteriorFurniture(dock, "(F)1443", 9, 5);
            TryAddInteriorFurniture(dock, "(F)704", 10, 5);

            // RIGHT: boarding / luggage side. Bay tile 23,8 remains open.
            TryAddInteriorFurniture(dock, "(F)1289", 27, 5);
            TryAddInteriorFurniture(dock, "(F)1443", 21, 6);
            TryAddInteriorFurniture(dock, "(F)1443", 26, 6);
            TryAddInteriorFurniture(dock, "(F)1399", 25, 11, heldId: "(F)1369");
            TryAddInteriorFurniture(dock, "(F)1390", 27, 11);
            TryAddInteriorFurniture(dock, "(F)1456", 22, 9);

            // Waiting nook, offset from the center arrival/exit corridor.
            TryAddInteriorFurniture(dock, "(F)432", 10, 11, rotation: 0);
            TryAddInteriorFurniture(dock, "(F)1399", 9, 12, heldId: "(F)1362");

            dock.modData[InteriorDecorMarkerKey] = InteriorDecorVersion + "-0677-dock";
        }

        private static void ClearInteriorDecor(GameLocation location)
        {
            foreach (Furniture old in location.furniture
                         .Where(f => f.modData.ContainsKey(InteriorDecorMarkerKey))
                         .ToList())
            {
                location.furniture.Remove(old);
            }

            foreach (Vector2 key in location.Objects.Pairs
                         .Where(pair => pair.Value?.modData.ContainsKey(InteriorDecorMarkerKey) == true)
                         .Select(pair => pair.Key)
                         .ToList())
            {
                location.Objects.Remove(key);
            }
        }

        private static void TryAddInteriorFurniture(
            GameLocation location,
            string itemId,
            int x,
            int y,
            int rotation = 0,
            string? heldId = null)
        {
            try
            {
                Furniture item = ItemRegistry.Create<Furniture>(itemId).SetPlacement(x, y, rotation);
                item.modData[InteriorDecorMarkerKey] = InteriorDecorVersion;
                if (heldId is not null)
                    item.SetHeldObject(ItemRegistry.Create<Furniture>(heldId));
                location.furniture.Add(item);
            }
            catch
            {
                // A changed vanilla furniture ID must never make either Airship room unloadable.
            }
        }

        private static void TryAddInteriorChest(GameLocation location, Point tile)
        {
            try
            {
                Vector2 key = new(tile.X, tile.Y);
                if (location.Objects.TryGetValue(key, out StardewValley.Object? existing)
                    && existing is not null
                    && !existing.modData.ContainsKey(InteriorDecorMarkerKey))
                {
                    return;
                }

                location.Objects.Remove(key);
                Chest chest = new(true);
                chest.modData[InteriorDecorMarkerKey] = InteriorDecorVersion;
                location.setObject(key, chest);
            }
            catch
            {
                // The interaction handler still works even if a decorative chest cannot spawn.
            }
        }

    ''')
    text = text[:start] + replacement + text[end:]
    path.write_text(text, encoding="utf-8")


def disable_legacy_postworld_room_props() -> None:
    path = ROOT / "Services/AirshipInteriorStardewRenderer.cs"
    text = path.read_text(encoding="utf-8")
    replacements = [
        "        DrawDeckStardewDecor(batch);\n",
        "        DrawUpgradeStations(batch, save, phase);\n",
        "        DrawDockStardewDecor(batch);\n",
    ]
    for call in replacements:
        text = text.replace(call, "", 1)
    path.write_text(text, encoding="utf-8")


def rewrite_room(path: Path, width: int, height: int, doorway_xs: set[int], role: str) -> None:
    tree = ET.parse(path)
    root = tree.getroot()
    props = root.find("properties")
    assert props is not None
    for prop in props.findall("property"):
        name = prop.attrib.get("name")
        if name == "CardchaAirshipVersion":
            prop.set("value", "alpha.28.0.4.14.4.5.12.45.3")
        elif name == "CardchaVisualProfile":
            prop.set("value", role + "|native-stardew-furniture|warm-wood-brass|clear-walking-spine")
        elif name == "CardchaArchitecture":
            prop.set("value", "vanilla-shell|native-furniture-and-object|no-postworld-physical-decor|depth-contract-0677")

    layers = {layer.attrib["name"]: layer for layer in root.findall("layer")}
    zero = [0] * (width * height)
    layers["BackDecor"].find("data").text = "\n" + ",".join(map(str, zero)) + "\n"
    layers["Front"].find("data").text = "\n" + ",".join(map(str, zero)) + "\n"

    block_gid = 4431 if width == 24 else 4635
    buildings: list[int] = []
    for y in range(height):
        for x in range(width):
            blocked = False
            if y in (1, 2, 3, 4):
                blocked = True
            if 5 <= y <= height - 2 and x in (0, width - 1):
                blocked = True
            if y == height - 1 and x not in doorway_xs:
                blocked = True
            buildings.append(block_gid if blocked else 0)
    layers["Buildings"].find("data").text = "\n" + ",".join(map(str, buildings)) + "\n"

    ET.indent(tree, space=" ")
    tree.write(path, encoding="UTF-8", xml_declaration=True)


def write_handoff() -> None:
    handoff = Path("handoff/ALPHA28_0677_AIRSHIP_TWO_ROOM_DECOR_REBUILD.md")
    handoff.write_text(
        """# Cardcha alpha28 — 0677 Airship Two-Room Decor Rebuild

## Source of truth
- Branch: `cardcha-alpha28-0677-airship-two-room-decor-rebuild`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.45.3`
- Base: 0676B world-depth safety contract.

## User acceptance problem
The two Airship rooms looked too empty, generic and test-like to be worth testing. 0677 is a room-composition rebuild, not a small prop sprinkle.

## Bridge
- Native Stardew furniture only for physical decor.
- Clear central walking spine.
- Navigation/reference wall, engine/hull workshop, resonance/reactor side, rugs, lamps, plants, windows and storage.
- Four upgrade sockets remain gameplay-authoritative.

## Dock / waiting hall
- Service/Lost & Found zone, route desk, boarding/luggage side and waiting nook.
- Lost & Found is a real Cardcha-owned Chest at the existing interaction tile.
- Center arrival/exit corridor and boarding bay remain open.

## Depth contract
- Old full-room BackDecor image layer disabled.
- No solid room prop restored through RenderedWorld.
- Physical room detail is Furniture/Object/TMX owned.
- Magical cues remain VFX-only.

## Frozen
No card balance, boss balance, progression, fare, save schema, MiMi art, ChaCha mechanics, or Region gameplay changes.

## Acceptance
1. `cardcha_test_airship`: Bridge must read as a furnished flying workshop/bridge, not an empty rectangle.
2. Walk center spine and all four upgrade sockets; native occlusion must remain correct.
3. Return to Dock: service, route, waiting and boarding zones must be visually distinct.
4. Lost & Found chest must be visible at its actual interaction position.
""",
        encoding="utf-8",
    )
    Path("handoff/LATEST_CARDCHA_HANDOFF.md").write_text(
        """# Latest Cardcha Handoff

Current branch: `cardcha-alpha28-0677-airship-two-room-decor-rebuild`
Current build: `0.3.0-alpha.28.0.4.14.4.5.12.45.3`
Continue from: `handoff/ALPHA28_0677_AIRSHIP_TWO_ROOM_DECOR_REBUILD.md`

0677 directly answers user rejection of the two Airship rooms as too superficial/empty. It inherits the 0676B render-depth contract: physical world decor must be TMX/Furniture/Object/native actor owned, never a RenderedWorld fake prop.

Do not resume from stale main or earlier branches.
""",
        encoding="utf-8",
    )


def main() -> None:
    bump_versions()
    rebuild_airship_service()
    disable_legacy_postworld_room_props()
    rewrite_room(ROOT / "assets/airship_deck.tmx", 24, 14, {11, 12}, "airship-bridge")
    rewrite_room(ROOT / "assets/sky_dock_interior.tmx", 30, 18, {14, 15}, "airship-dock-waiting-hall")
    write_handoff()
    print("0677 Airship two-room materialization complete")


if __name__ == "__main__":
    main()
