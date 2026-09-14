#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import json
import re

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = ROOT / "src/Cardcha/Services/AirshipFoundationService.cs"
RENDERER = ROOT / "src/Cardcha/Services/AirshipInteriorStardewRenderer.cs"
DECK = ROOT / "src/Cardcha/assets/airship_deck.tmx"
REPORT = ROOT / "handoff/AIRSHIP_0696D3A_GAMEPLAY_ROOM_INTEGRATION_VALIDATION.json"

TRAVEL_GATE = (4, 5)
UPGRADE_FOOTPRINTS = {
    "engine": [(4, 8), (5, 8)],
    "navigation": [(18, 8), (19, 8)],
    "hull": [(7, 11), (8, 11)],
    "reactor": [(15, 11), (16, 11)],
}
COLLISION_GID = 5400


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one baseline match, found {count}")
    return text.replace(old, new, 1)


def patch_foundation() -> None:
    text = FOUNDATION.read_text(encoding="utf-8")
    old = """        Point action = GetActionTile();\n        Point helm = ResolveDeckHelmTile(location);\n        Point exit = ResolveDeckExitTile(location);\n\n        if (action == helm)\n        {\n            this.Helper.Input.Suppress(e.Button);\n            this.HandleRegion1DepartureRequest();\n            return;\n        }\n"""
    new = """        Point action = GetActionTile();\n        Point travelGate = ResolveDeckTravelGateTile(location);\n        Point exit = ResolveDeckExitTile(location);\n\n        // 0696D3-A: map travel has a dedicated visible gate instead of being hidden on the helm/radar.\n        if (ActionTouchesStation(action, travelGate))\n        {\n            this.Helper.Input.Suppress(e.Button);\n            this.HandleRegion1DepartureRequest();\n            return;\n        }\n"""
    text = replace_once(text, old, new, "dedicated travel gate interaction")

    old_method = """    private static Point ResolveDeckHelmTile(GameLocation deck)\n    {\n        int width = deck.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 24;\n        int height = deck.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 14;\n        return new Point(Math.Clamp(width / 2, 2, width - 3), Math.Clamp(6, 2, height - 3));\n    }\n"""
    new_method = old_method + """\n    private static Point ResolveDeckTravelGateTile(GameLocation deck)\n    {\n        int width = deck.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 24;\n        int height = deck.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 14;\n        return new Point(Math.Clamp(4, 2, width - 3), Math.Clamp(5, 2, height - 3));\n    }\n"""
    text = replace_once(text, old_method, new_method, "travel gate resolver")
    FOUNDATION.write_text(text, encoding="utf-8")


def patch_renderer() -> None:
    text = RENDERER.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '    private const string PropRoot0690 = "assets/airship_props/set01_redux";\n',
        '    private const string PropRoot0690 = "assets/airship_props/set01_redux";\n    private const string TravelGateVisualPath0696D3A = PropRoot0690 + "/boarding_gate_arch.png";\n',
        "travel gate asset path",
    )
    text = replace_once(
        text,
        "    private static bool HubDecorLoadFailed;\n",
        "    private static bool HubDecorLoadFailed;\n    private static Texture2D? TravelGateVisual0696D3A;\n    private static bool TravelGateVisualLoadFailed0696D3A;\n",
        "travel gate texture cache",
    )
    text = replace_once(
        text,
        "        DrawAmbientLamps(batch, phase);\n        // 0696C: restore the four level-aware Engine/Navigation/Hull/Reactor stations.\n",
        "        DrawAmbientLamps(batch, phase);\n        DrawTravelGate0696D3A(batch, phase);\n        // 0696D3-A: all four upgrade stations stay present and share a grounded physical footprint.\n",
        "travel gate draw call",
    )

    marker = "    private static void DrawHelmMagic(SpriteBatch batch, float phase)\n"
    gate_method = r'''    private static Texture2D? GetTravelGateVisual0696D3A()
    {
        if (TravelGateVisual0696D3A is not null && !TravelGateVisual0696D3A.IsDisposed)
            return TravelGateVisual0696D3A;
        TravelGateVisual0696D3A = null;
        if (TravelGateVisualLoadFailed0696D3A || ModEntry.StaticHelper is null)
            return null;
        try
        {
            TravelGateVisual0696D3A = ModEntry.StaticHelper.ModContent.Load<Texture2D>(TravelGateVisualPath0696D3A);
            return TravelGateVisual0696D3A;
        }
        catch
        {
            TravelGateVisualLoadFailed0696D3A = true;
            return null;
        }
    }

    private static void DrawTravelGate0696D3A(SpriteBatch batch, float phase)
    {
        Texture2D? gate = GetTravelGateVisual0696D3A();
        if (gate is null || gate.Width <= 0 || gate.Height <= 0)
            return;

        Point tile = new(4, 5);
        Vector2 floor = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 58f);
        const int width = 244;
        int height = Math.Max(128, (int)MathF.Round(gate.Height * (width / (float)gate.Width)));
        Rectangle dst = new((int)floor.X - width / 2, (int)floor.Y - height + 32, width, height);
        batch.Draw(gate, dst, null, Color.White, 0f, Vector2.Zero, SpriteEffects.None, 0.883f);

        float pulse = 0.56f + 0.12f * MathF.Sin(phase * 2.1f);
        Color gold = new Color(228, 176, 84) * (0.52f + pulse * 0.20f);
        Color cyan = new Color(96, 211, 224) * (0.34f + pulse * 0.18f);
        DrawRect(batch, new Rectangle((int)floor.X - 48, (int)floor.Y - 4, 96, 5), gold);
        DrawDiamond(batch, new Vector2(floor.X, floor.Y - 18), 7, cyan);
    }

'''
    if "DrawTravelGate0696D3A" not in text.split(marker, 1)[0]:
        if text.count(marker) != 1:
            raise RuntimeError("travel gate renderer insertion point missing")
        text = text.replace(marker, gate_method + marker, 1)

    old_station = """            DrawRect(batch, new Rectangle((int)center.X - 54, (int)center.Y - 55, 108, 72), accent * (0.075f + pulse * 0.045f));\n            DrawRect(batch, new Rectangle((int)center.X - 38, (int)center.Y - 42, 76, 52), accent * (0.085f + pulse * 0.055f));\n            Rectangle dst = new((int)center.X - 56, (int)center.Y - 76, 112, 112);\n"""
    new_station = """            // 0696D3-A: a dark/brass plinth anchors the machine to the room instead of floating over the floor.\n            DrawRect(batch, new Rectangle((int)center.X - 54, (int)center.Y + 9, 108, 18), new Color(49, 34, 31) * 0.92f);\n            DrawRect(batch, new Rectangle((int)center.X - 46, (int)center.Y + 7, 92, 7), new Color(177, 118, 57) * 0.78f);\n            DrawRect(batch, new Rectangle((int)center.X - 54, (int)center.Y - 55, 108, 72), accent * (0.055f + pulse * 0.035f));\n            DrawRect(batch, new Rectangle((int)center.X - 38, (int)center.Y - 42, 76, 52), accent * (0.065f + pulse * 0.045f));\n            Rectangle dst = new((int)center.X - 52, (int)center.Y - 70, 104, 104);\n"""
    text = replace_once(text, old_station, new_station, "grounded upgrade station presentation")
    RENDERER.write_text(text, encoding="utf-8")


def patch_deck_collision() -> None:
    text = DECK.read_text(encoding="utf-8")
    pattern = re.compile(r'(<layer id="3" name="Buildings" width="24" height="14">.*?<data encoding="csv">)(.*?)(</data>.*?</layer>)', re.S)
    match = pattern.search(text)
    if not match:
        raise RuntimeError("Buildings layer not found in airship_deck.tmx")
    values = [int(x.strip()) for x in match.group(2).replace("\n", "").split(",") if x.strip()]
    if len(values) != 24 * 14:
        raise RuntimeError(f"unexpected Buildings tile count {len(values)}")

    targets = [p for points in UPGRADE_FOOTPRINTS.values() for p in points]
    for x, y in targets:
        values[y * 24 + x] = COLLISION_GID

    rows = []
    for y in range(14):
        rows.append(",".join(str(v) for v in values[y * 24:(y + 1) * 24]))
    data = "\n" + ",\n".join(rows) + "\n"
    text = text[:match.start()] + match.group(1) + data + match.group(3) + text[match.end():]

    if 'CardchaD3AIntegration' not in text:
        text = text.replace(
            '  <property name="CardchaSourceBlueprint" value="handoff/AIRSHIP_ROOM_BLUEPRINT_0696.json" />\n',
            '  <property name="CardchaSourceBlueprint" value="handoff/AIRSHIP_ROOM_BLUEPRINT_0696.json" />\n  <property name="CardchaD3AIntegration" value="upgrade-footprints|dedicated-travel-gate|gameplay-first" />\n',
            1,
        )
    DECK.write_text(text, encoding="utf-8")


def validate() -> dict:
    foundation = FOUNDATION.read_text(encoding="utf-8")
    renderer = RENDERER.read_text(encoding="utf-8")
    deck = DECK.read_text(encoding="utf-8")

    checks = {
        "dedicatedTravelGateResolver": "ResolveDeckTravelGateTile" in foundation,
        "departureUsesTravelGate": "ActionTouchesStation(action, travelGate)" in foundation,
        "helmNoLongerOwnsDeparture": "if (action == helm)" not in foundation,
        "gateUsesExistingBoardingArt": 'TravelGateVisualPath0696D3A = PropRoot0690 + "/boarding_gate_arch.png"' in renderer,
        "gateRenderedOnDeck": "DrawTravelGate0696D3A(batch, phase);" in renderer,
        "allFourUpgradeSystemsStillPresent": all(token in renderer for token in ["AirshipEngineLevel", "AirshipNavigationLevel", "AirshipHullLevel", "AirshipReactorLevel"]),
        "groundedUpgradePlinth": "0696D3-A: a dark/brass plinth anchors the machine" in renderer,
        "deckD3AProperty": "CardchaD3AIntegration" in deck,
    }

    pattern = re.compile(r'<layer id="3" name="Buildings" width="24" height="14">.*?<data encoding="csv">(.*?)</data>', re.S)
    match = pattern.search(deck)
    collision = {}
    if match:
        values = [int(x.strip()) for x in match.group(1).replace("\n", "").split(",") if x.strip()]
        for name, points in UPGRADE_FOOTPRINTS.items():
            collision[name] = all(len(values) == 24 * 14 and values[y * 24 + x] == COLLISION_GID for x, y in points)
    else:
        collision = {name: False for name in UPGRADE_FOOTPRINTS}
    checks["upgradeCollisionFootprints"] = all(collision.values())

    report = {
        "phase": "0696D3-A",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "travelGateTile": list(TRAVEL_GATE),
        "upgradeCollisionFootprints": {k: [list(p) for p in v] for k, v in UPGRADE_FOOTPRINTS.items()},
        "collisionResults": collision,
        "checks": checks,
        "scopeDeferred": ["radar-reference-rework", "prop-scale-placement", "room1-border", "entrance-arch-x2", "window-size-adjustment"],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if report["status"] != "PASS":
        raise SystemExit(json.dumps(report, indent=2))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    if not args.apply and not args.validate:
        parser.error("choose --apply and/or --validate")
    if args.apply:
        patch_foundation()
        patch_renderer()
        patch_deck_collision()
    if args.validate:
        print(json.dumps(validate(), indent=2))


if __name__ == "__main__":
    main()
