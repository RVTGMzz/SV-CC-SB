#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src/Cardcha"
PROP = CARDCHA / "assets/airship_props/set01_redux"
WINDOW = PROP / "window_runtime"
SERVICE = CARDCHA / "Services/AirshipAmbientAnimationService.cs"
RESOLVER = CARDCHA / "Services/AirshipAmbientResolver.cs"
AMBIENT = PROP / "airship_ambient_manifest.json"
REPORT = ROOT / "handoff/AIRSHIP_0696D2_WINDOW_ENVIRONMENT_MATRIX_VALIDATION.json"

OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.68"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.69"
D1S_AIRSHIP_SHA256 = "58caeabc94744ad04ae1f006c91e09bf9a55d5a211d53b426b12ca9d0dc1c9ce"

APPROVED = {
    "morning": (
        "assets/airship_props/set01_redux/window_runtime/window_scene_default_morning_clear.png",
        "9a8996ef0068057e774419d9d4597f44753951b3ec1ec519cd6771efaad7b5d0",
    ),
    "noon": (
        "assets/airship_props/set01_redux/window_runtime/window_scene_default_noon_clear.png",
        "fa0f00051febb62d107e4a1dc14a079dbfc8183659a73b9ed2ecfe5c4efb3aff",
    ),
    "evening": (
        "assets/airship_props/set01_redux/window_runtime/window_scene_default_evening_clear.png",
        "b94d30d18bacecc2c3f09971aec2d5951956490be8c7cad2243b4689c865a638",
    ),
    "night": (
        "assets/airship_props/set01_redux/window_runtime/window_scene_default_night_clear.png",
        "f9d15f66485f514f4be8589ee29d45beabda87e357b1c1d3ffa7965855ed1990",
    ),
}

TIME_BUCKETS = {
    "morning": {"start": 600, "end": 1159},
    "noon": {"start": 1200, "end": 1659},
    "evening": {"start": 1700, "end": 1959},
    "night": {"start": 2000, "end": 2759},
}

DRAW_METHOD = '''    private static bool DrawObservationWindow(SpriteBatch batch, long clockMs)
    {
        if (Resolver is null)
            return false;

        AirshipAmbientManifest? manifest = Resolver.Manifest;
        if (manifest is null)
            return false;

        AirshipObservationWindowConfig config = manifest.ObservationWindow;
        Vector2 propTopLeft = WorldToScreen(config.WorldAnchor.TileX * 64f, config.WorldAnchor.TileY * 64f);

        // 0696D2: resolve one approved clear 160x80 environment from Game1.timeOfDay.
        // The accepted .68 airship stays independent and is drawn above the environment.
        AirshipResolvedWindowState state = Resolver.ResolveWindow(clockMs);
        if (state.AmbientAssetsReady && !string.IsNullOrWhiteSpace(state.BackdropPath))
        {
            Texture2D? environment = GetTexture(state.BackdropPath);
            if (environment is not null && environment.Width == 160 && environment.Height == 80)
            {
                batch.Draw(
                    environment,
                    new Rectangle(
                        (int)propTopLeft.X,
                        (int)propTopLeft.Y,
                        config.FootprintPx.Width * 4,
                        config.FootprintPx.Height * 4
                    ),
                    null,
                    Color.White,
                    0f,
                    Vector2.Zero,
                    SpriteEffects.None,
                    0.8840f
                );
            }
        }

        Texture2D? airship = GetTexture(D1SAirshipPath);
        if (airship is null)
            return state.AmbientAssetsReady;

        int frameIndex = (int)((clockMs / D1SAirshipFrameDurationMs) % D1SAirshipPositions.Length);
        Point pos = D1SAirshipPositions[frameIndex];
        batch.Draw(
            airship,
            new Rectangle(
                (int)propTopLeft.X + pos.X * 4,
                (int)propTopLeft.Y + pos.Y * 4,
                airship.Width * 4,
                airship.Height * 4
            ),
            null,
            Color.White,
            0f,
            Vector2.Zero,
            SpriteEffects.None,
            0.8845f
        );
        return true;
    }

'''


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def approved_path(relative: str) -> Path:
    return CARDCHA / relative


def check_sources() -> dict:
    result = {}
    errors = []
    for state, (relative, expected_hash) in APPROVED.items():
        path = approved_path(relative)
        item = {"path": relative, "expectedSha256": expected_hash}
        if not path.is_file():
            item["exists"] = False
            errors.append(f"{state}: missing {relative}")
            result[state] = item
            continue
        item["exists"] = True
        item["sha256"] = sha256(path)
        if item["sha256"] != expected_hash:
            errors.append(f"{state}: SHA256 mismatch")
        try:
            with Image.open(path) as image:
                image.load()
                item["format"] = image.format
                item["size"] = list(image.size)
                item["mode"] = image.mode
                if image.format != "PNG":
                    errors.append(f"{state}: expected PNG, got {image.format}")
                if image.size != (160, 80):
                    errors.append(f"{state}: expected 160x80, got {image.size}")
                if image.mode != "RGBA":
                    errors.append(f"{state}: expected RGBA, got {image.mode}")
        except Exception as exc:
            errors.append(f"{state}: decode failed: {exc}")
        result[state] = item

    if errors:
        raise RuntimeError("0696D2 approved source gate failed:\n- " + "\n- ".join(errors))
    return result


def patch_runtime() -> None:
    text = SERVICE.read_text(encoding="utf-8")
    start = text.index("    private static bool DrawObservationWindow")
    end = text.index("    private static bool DrawNavigationConsole", start)
    text = text[:start] + DRAW_METHOD + text[end:]
    text = text.replace(
        "0696D1S isolated Window motion repair plus existing Console ambient renderer.",
        "0696D2 clear-time Window environment matrix plus existing Console ambient renderer.",
    )
    text = text.replace(
        "D2 will rebuild the season/time/weather matrix after Ron accepts this motion contract.",
        "D2 draws one approved clear environment by time bucket behind the independent .68 airship sprite.",
    )
    SERVICE.write_text(text, encoding="utf-8")

    resolver = RESOLVER.read_text(encoding="utf-8")
    resolver = resolver.replace(
        "0696C source-of-truth resolver for Airship ambient visuals.",
        "0696D2 source-of-truth resolver for the clear-time Airship Window environments.",
    )
    resolver = resolver.replace(
        "Observation Window production state is explicit season x time x weather.",
        "Observation Window D2 state resolves four approved clear environments by time bucket.",
    )
    RESOLVER.write_text(resolver, encoding="utf-8")


def update_versions() -> None:
    for relative in ("manifest.json", "Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"):
        path = CARDCHA / relative
        if path.exists():
            text = path.read_text(encoding="utf-8").replace(OLD_VERSION, NEW_VERSION)
            text = text.replace(
                "0696D1S AIRSHIP MOTION REPAIR TEST",
                "0696D2 CLEAR WINDOW ENVIRONMENT MATRIX TEST",
            )
            path.write_text(text, encoding="utf-8")


def update_manifest() -> None:
    data = json.loads(AMBIENT.read_text(encoding="utf-8"))
    data["version"] = NEW_VERSION
    data["workstream"] = "0696D2-window-environment-matrix"
    data["visualAcceptance"] = "PENDING-RON-VISUAL"
    data["global"]["timeBuckets"] = TIME_BUCKETS

    ow = data["observationWindow"]
    ow["productionStatus"] = "D2_CLEAR_TIME_MATRIX_MATERIALIZED_PENDING_RON_VISUAL"
    paths = {state: relative for state, (relative, _) in APPROVED.items()}
    ow["backdrops"] = {
        "fallbackSeason": "default",
        "fallbackTime": "noon",
        "states": {"default": paths},
    }
    ow["sceneMatrix"] = {
        "fallbackSeason": "default",
        "fallbackTime": "noon",
        "fallbackWeather": "clear",
        "states": {
            "default": {
                state: {"clear": relative}
                for state, (relative, _) in APPROVED.items()
            }
        },
    }
    ow["d2ClearMatrix"] = {
        "scope": "time-of-day-clear-only",
        "states": {
            state: {
                "path": relative,
                "sha256": expected_hash,
                "nativeSize": [160, 80],
                "mode": "RGBA",
            }
            for state, (relative, expected_hash) in APPROVED.items()
        },
        "seasonVariantsDeferred": True,
        "weatherVariantsDeferred": True,
        "legacyEnvironmentOverlayReuse": False,
        "airshipLayer": "independent-.68-runtime-sprite",
        "acceptance": "PENDING-RON-VISUAL",
    }
    AMBIENT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_report(source_report: dict) -> None:
    airship = WINDOW / "observation_window_airship.png"
    payload = {
        "phase": "0696D2-window-environment-matrix",
        "version": NEW_VERSION,
        "visualAcceptance": "PENDING-RON-VISUAL",
        "timeBuckets": {
            "morning": "06:00-11:50",
            "noon": "12:00-16:50",
            "evening": "17:00-19:50",
            "night": "otherwise",
        },
        "sources": source_report,
        "contracts": {
            "clearTimeMatrixOnly": True,
            "seasonVariantsDeferred": True,
            "weatherVariantsDeferred": True,
            "navigationConsoleTouched": False,
            "legacyEnvironmentOverlayReuse": False,
            "independentAirshipPreserved": True,
            "airshipSha256": sha256(airship),
            "expectedAirshipSha256": D1S_AIRSHIP_SHA256,
        },
    }
    REPORT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def apply() -> None:
    sources = check_sources()
    airship = WINDOW / "observation_window_airship.png"
    if sha256(airship) != D1S_AIRSHIP_SHA256:
        raise RuntimeError("D1S independent airship drifted; refusing D2 apply")
    patch_runtime()
    update_versions()
    update_manifest()
    write_report(sources)


def validate() -> None:
    sources = check_sources()
    service = SERVICE.read_text(encoding="utf-8")
    resolver = RESOLVER.read_text(encoding="utf-8")
    ambient = json.loads(AMBIENT.read_text(encoding="utf-8"))
    errors = []

    if "Resolver.ResolveWindow(clockMs)" not in service:
        errors.append("runtime is not wired to ResolveWindow")
    if "state.BackdropPath" not in service:
        errors.append("runtime does not draw the resolved background")
    if "environment.Width == 160 && environment.Height == 80" not in service:
        errors.append("runtime 160x80 guard missing")
    for legacy in ("observation_window_overlay_2.png", "observation_window_overlay_3.png", "observation_window_overlay_4.png"):
        if legacy in service:
            errors.append(f"legacy overlay reused by runtime: {legacy}")
    if "ResolveTimeBucket(manifest.Global, Game1.timeOfDay)" not in resolver:
        errors.append("resolver is not driven by Game1.timeOfDay")
    if ambient.get("version") != NEW_VERSION:
        errors.append("ambient version mismatch")
    if ambient.get("workstream") != "0696D2-window-environment-matrix":
        errors.append("ambient workstream mismatch")
    if ambient["global"].get("timeBuckets") != TIME_BUCKETS:
        errors.append("time bucket contract drifted")

    ow = ambient["observationWindow"]
    matrix = ow.get("sceneMatrix", {}).get("states", {})
    if set(matrix) != {"default"}:
        errors.append("season variants activated in D2")
    else:
        default = matrix["default"]
        if set(default) != set(APPROVED):
            errors.append("time-state coverage is not exactly morning/noon/evening/night")
        else:
            for state, (relative, _) in APPROVED.items():
                if default[state] != {"clear": relative}:
                    errors.append(f"{state}: clear-only path contract drifted")

    d2 = ow.get("d2ClearMatrix", {})
    if d2.get("legacyEnvironmentOverlayReuse") is not False:
        errors.append("legacy overlay reuse guard missing")
    if d2.get("airshipLayer") != "independent-.68-runtime-sprite":
        errors.append("independent .68 airship ownership lost")

    airship = WINDOW / "observation_window_airship.png"
    if sha256(airship) != D1S_AIRSHIP_SHA256:
        errors.append("D1S airship hash drifted")
    with Image.open(airship) as image:
        image.load()
        if image.size != (15, 9):
            errors.append(f"D1S airship size drifted: {image.size}")

    for relative in ("manifest.json", "Cardcha.csproj", "Directory.Build.targets"):
        if NEW_VERSION not in (CARDCHA / relative).read_text(encoding="utf-8"):
            errors.append(f"{relative}: .69 version missing")

    if errors:
        raise RuntimeError("0696D2 runtime validation failed:\n- " + "\n- ".join(errors))

    write_report(sources)
    print(json.dumps({
        "phase": "0696D2-window-environment-matrix",
        "version": NEW_VERSION,
        "approvedSources": "PASS",
        "resolver": "PASS",
        "timeCoverage": "PASS",
        "independentAirship": "PASS",
        "visualAcceptance": "PENDING-RON-VISUAL",
    }, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-source", action="store_true")
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    if args.check_source:
        print(json.dumps(check_sources(), indent=2))
    elif args.apply:
        apply()
    else:
        validate()


if __name__ == "__main__":
    main()
