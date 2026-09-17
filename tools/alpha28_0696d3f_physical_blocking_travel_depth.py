#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "handoff/AIRSHIP_0696D3F_PHYSICAL_BLOCKING_TRAVEL_DEPTH_VALIDATION.json"

PATCH = ROOT / "src/Cardcha/Patches/AirshipGateDepthPatch.cs"
AMBIENT = ROOT / "src/Cardcha/Services/AirshipAmbientAnimationService.cs"
FOUNDATION = ROOT / "src/Cardcha/Services/AirshipFoundationService.cs"
SAFETY = ROOT / "src/Cardcha/Patches/WorldPhysicalOverlaySafetyPatch.cs"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def method_body(text: str, start: str, end: str) -> str:
    if start not in text:
        return ""
    tail = text.split(start, 1)[1]
    return tail.split(end, 1)[0] if end in tail else tail


def main() -> None:
    patch = read(PATCH)
    ambient = read(AMBIENT)
    foundation = read(FOUNDATION)
    safety = read(SAFETY)

    console = method_body(
        ambient,
        "private static bool DrawNavigationConsole",
        "private static void DrawConsoleLayer",
    )
    deck_pass = method_body(
        patch,
        "private static void DrawD3FDeckPass",
        "private static void DrawD3FTravelGate",
    )
    prepare_map = method_body(
        patch,
        "private static void PrepareD3FDeckMap",
        "private static void DrawD3FDeckPass",
    )
    blocked = method_body(
        patch,
        "private static List<Rectangle> BuildD3FBlockedRects",
        "private static Rectangle TileRect",
    )

    station_tokens = [
        "new Point(4, 8)",
        "new Point(19, 8)",
        "new Point(7, 11)",
        "new Point(16, 11)",
    ]

    checks = {
        "legacyDeckMarkerPassHardSuppressed": (
            "private static bool SuppressLegacyDeckMarkers()" in patch
            and "=> false;" in patch
            and "DeckMarkersMethod.Invoke" not in patch
        ),
        "narrowD3FDeckPassOwnsPresentation": all(
            token in deck_pass
            for token in [
                "AirshipAmbientAnimationService.DrawDeckAmbient(batch);",
                "DrawD3FTravelGate(batch);",
                "DrawD3FUpgradeStations(batch);",
            ]
        ),
        "yellowConsoleBaseRemovedFromLiveMap": (
            'deck.Map?.GetLayer("Buildings2")' in prepare_map
            and "for (int y = 5; y <= 9; y++)" in prepare_map
            and "for (int x = 9; x <= 15; x++)" in prepare_map
            and "layer.Tiles[x, y] = null;" in prepare_map
        ),
        "ambientNeverDrawsStaticRadarBackground": (
            "state.RadarBackground" not in console
            and "DrawLegacyFullOverlay(" not in console
            and all(token in console for token in ["state.RadarGlow", "state.RadarSweep", "state.RadarPings"])
        ),
        "fourUpgradeStationsExplicit": all(token in patch for token in station_tokens),
        "upgradeAtlasFallbackExists": (
            "visible fallback stations will be used" in patch
            and "DrawD3FUpgradeStations" in patch
            and 'const string label = "UPGRADE";' in patch
        ),
        "travelGateVisible": (
            "DrawD3FTravelGate(batch);" in patch
            and 'DrawD3FBoardingPad(batch, tile, "TRAVEL");' in patch
        ),
        "skyDockBoardingPadVisible": 'DrawD3FBoardingPad(b, new Point(23, 8), "BOARD AIRSHIP");' in patch,
        "deckConsoleNoEnterFootprint": "result.Add(TileRect(9, 8, 7, 3));" in blocked,
        "deckUpgradeNoEnterFootprints": all(
            token in blocked
            for token in [
                "result.Add(TileRect(3, 8, 3, 2));",
                "result.Add(TileRect(18, 8, 3, 2));",
                "result.Add(TileRect(6, 11, 3, 1));",
                "result.Add(TileRect(15, 11, 3, 1));",
            ]
        ),
        "deckTravelGatePostsBlockedCenterOpen": (
            "result.Add(TileRect(2, 4, 2, 3));" in blocked
            and "result.Add(TileRect(5, 4, 2, 3));" in blocked
        ),
        "floor1LargePropsBlocked": all(
            token in blocked
            for token in [
                "result.Add(TileRect(2, 4, 12, 2));",
                "result.Add(TileRect(2, 9, 6, 2));",
                "result.Add(TileRect(21, 4, 2, 4));",
                "result.Add(TileRect(26, 4, 2, 4));",
                "result.Add(TileRect(22, 10, 4, 3));",
            ]
        ),
        "forestGateDoesNotMutateForestMap": (
            "Do not alter Forest tiles" in blocked
            and "TryResolveServicePointNoArgs" in blocked
            and "p.X - 2" in blocked
            and "p.X + 2" in blocked
        ),
        "lastSafePositionGuardInstalled": (
            "EnforceD3FPhysicalFootprints(__instance, location, service);" in patch
            and "LastSafePlayerPosition" in patch
            and "player.Position = LastSafePlayerPosition;" in patch
        ),
        "radarStillAlternateTravelControl": (
            'ResolvePoint("ResolveDeckHelmTile", location, new Point(12, 6))' in patch
            and "__result = travelGate;" in patch
        ),
        "dedicatedTravelHandlerStillAuthoritative": (
            "ResolveDeckTravelGateTile" in foundation
            and "ActionTouchesStation(action, travelGate)" in foundation
            and "HandleRegion1DepartureRequest();" in foundation
        ),
        "legacyUnsafePaintersStillSuppressed": all(
            token in safety for token in ['"DrawRegion1Details"', '"DrawDeckStardewDecor"', '"DrawDockStardewDecor"']
        ),
    }

    report = {
        "phase": "0696D3-F",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "mode": "static-source-contract",
        "authority": "Ron 2026-09-17 runtime screenshots supersede D3-E acceptance",
        "runtimeFailuresAddressed": [
            "forest-gate-player-can-enter-art",
            "floor1-large-prop-player-can-enter-art",
            "floor2-console-and-props-float-over-player",
            "four-upgrade-stations-not-visible",
            "yellow-navigation-console-base-still-visible",
            "boarding-travel-affordance-not-obvious",
        ],
        "checks": checks,
        "runtimeAcceptance": "PENDING-RON-IN-GAME",
        "runtimeNote": "D3-F CI proves source/build/package contracts only. Runtime PASS requires Ron to test the new package in game.",
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
