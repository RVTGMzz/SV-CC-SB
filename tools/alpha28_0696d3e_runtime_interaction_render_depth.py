#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "handoff/AIRSHIP_0696D3E_RUNTIME_INTERACTION_RENDER_DEPTH_VALIDATION.json"

GATE_PATCH = ROOT / "src/Cardcha/Patches/AirshipGateDepthPatch.cs"
SAFETY_PATCH = ROOT / "src/Cardcha/Patches/WorldPhysicalOverlaySafetyPatch.cs"
AMBIENT = ROOT / "src/Cardcha/Services/AirshipAmbientAnimationService.cs"
FOUNDATION = ROOT / "src/Cardcha/Services/AirshipFoundationService.cs"
MOD_ENTRY = ROOT / "src/Cardcha/ModEntry.cs"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def method_body(text: str, start: str, end: str) -> str:
    if start not in text:
        return ""
    tail = text.split(start, 1)[1]
    return tail.split(end, 1)[0] if end in tail else tail


def main() -> None:
    gate = read(GATE_PATCH)
    safety = read(SAFETY_PATCH)
    ambient = read(AMBIENT)
    foundation = read(FOUNDATION)
    mod_entry = read(MOD_ENTRY)

    console = method_body(
        ambient,
        "private static bool DrawNavigationConsole",
        "private static void DrawConsoleLayer",
    )

    required_upgrade_sockets = [
        "new Point(4, 8)",
        "new Point(19, 8)",
        "new Point(7, 11)",
        "new Point(16, 11)",
    ]
    required_floor1_resolvers = [
        "ResolveSkyDockInteriorRouteTile",
        "ResolveSkyDockInteriorBayTile",
        "ResolveSkyDockLostFoundTile",
        "ResolveSkyDockInteriorExitTile",
    ]
    required_safety_suppressions = [
        '"DrawRegion1Details"',
        '"DrawDeckStardewDecor"',
        '"DrawDockStardewDecor"',
    ]

    checks = {
        # Registration / ownership.
        "d3eDepthPatchRegistered": "AirshipGateDepthPatch.Apply(harmony, this.Airship, this.Monitor);" in mod_entry,
        "d3eSafetyPatchRegistered": "WorldPhysicalOverlaySafetyPatch.Apply(harmony, this.Monitor);" in mod_entry,

        # Gate + floor-2 render depth: whole runtime deck marker pass is blocked from the
        # normal RenderedWorld call and replayed immediately before the local Farmer draw.
        "deckMarkersResolved": '"DrawDeckMarkers"' in gate and "DeckMarkersMethod" in gate,
        "deckMarkersPostWorldSuppressed": (
            "prefix: new HarmonyMethod(typeof(AirshipGateDepthPatch), nameof(AllowOnlyFarmerDepthDeckMarkers))" in gate
            and "private static bool AllowOnlyFarmerDepthDeckMarkers()" in gate
            and "=> AllowDeckMarkerPass;" in gate
        ),
        "deckMarkersReplayBeforeFarmer": (
            "DrawDeckMarkersBeforePlayer(service, b);" in gate
            and "DeckMarkersMethod.Invoke(service, new object[] { batch, location });" in gate
            and "AllowDeckMarkerPass = true;" in gate
            and "AllowDeckMarkerPass = false;" in gate
        ),

        # Legacy physical overlay safety remains narrow. Upgrade stations must stay visible
        # because they now belong to the pre-Farmer deck pass rather than being blanket-disabled.
        "threeUnsafeLegacyPaintersSuppressed": all(token in safety for token in required_safety_suppressions),
        "upgradeStationsNotBlanketSuppressed": '"DrawUpgradeStations"' not in safety,
        "safetyPatchExpectedCountThree": "suppressed {patched}/3 unsafe post-world renderer(s)" in safety,

        # Interaction bridge: patch the canonical action tile and reuse existing gameplay handlers.
        "getActionTilePostfixInstalled": (
            '"GetActionTile"' in gate
            and "postfix: new HarmonyMethod(typeof(AirshipGateDepthPatch), nameof(NormalizeAirshipActionTile))" in gate
        ),
        "radarFootprintRoutesToTravelGate": (
            'ResolvePoint("ResolveDeckHelmTile", location, new Point(12, 6))' in gate
            and "if (NearEither(action, playerTile, helm, 2, 2))" in gate
            and "__result = travelGate;" in gate
        ),
        "existingTravelHandlerStillAuthoritative": (
            "ResolveDeckTravelGateTile" in foundation
            and "ActionTouchesStation(action, travelGate)" in foundation
        ),
        "travelGateFootprintExpanded": "NearEither(action, playerTile, travelGate, 2, 2)" in gate,
        "allFourUpgradeFootprintsExpanded": all(token in gate for token in required_upgrade_sockets),
        "floor1InteractionResolversCovered": all(token in gate for token in required_floor1_resolvers),

        # Radar visual authority from Ron's latest runtime feedback overrides D3-D's old
        # acceptance of the yellow backing asset. The asset may remain in the repository for
        # provenance, but DrawNavigationConsole must neither render it nor resurrect the legacy
        # full overlay when ambient slices are unavailable.
        "radarBackgroundNotRendered": "state.RadarBackground" not in console,
        "legacyConsoleFallbackDisabled": "DrawLegacyFullOverlay(" not in console,
        "missingAmbientKeepsMapNativeConsole": (
            "if (!state.AmbientAssetsReady)" in console
            and "return false;" in console
        ),
        "animatedRadarLayersRemain": all(
            token in console for token in ["state.RadarGlow", "state.RadarSweep", "state.RadarPings"]
        ),
    }

    report = {
        "phase": "0696D3-E",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "mode": "static-source-contract",
        "authority": "Ron latest in-game runtime feedback overrides stale D3-D visual assumptions",
        "runtimeFailuresAddressed": [
            "gate-over-player",
            "floor2-props-over-player",
            "radar-yellow-backing",
            "radar-not-actionable-for-travel",
            "floor1-floor2-interaction-misses",
        ],
        "checks": checks,
        "runtimeAcceptance": "PENDING-RON-IN-GAME",
        "runtimeNote": "Static CI can prove wiring/build/package contracts only. Runtime PASS requires Ron to test the new TEST package in game.",
    }

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
