#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = ROOT / "src/Cardcha/Services/AirshipFoundationService.cs"
AMBIENT = ROOT / "src/Cardcha/Services/AirshipAmbientAnimationService.cs"
DOCK = ROOT / "src/Cardcha/assets/sky_dock_interior.tmx"
SHELL = ROOT / "src/Cardcha/assets/airship_props/room_shell/airship_deck_border_0696c.png"
REPORT = ROOT / "handoff/AIRSHIP_0696D3C_ROOM_SHELL_ENTRANCES_VALIDATION.json"

SHELL_GID = 7200
SHELL_GIDS = set(range(7200, 7210))
EXPECTED_SHELL_SHA = "d6216e23c77cc5531658786ec70ae6f0e6742019f82711c78990f77ea7852535"
EXPECTED_D2 = {
    "morning": "93f6d4fcd403838d5758be012448c44978e65a8a4cb8bb33d4b24e4fb00802c0",
    "noon": "38cf1e47d73b7374c21932ca6fbd957a3f55d833385698d0b415721ebaddb29f",
    "evening": "2b3fb1ec4e4dd8d0bb7b2a3cf511ce7f8757e8dbbbb9ba54493f791df6aa0b5f",
    "night": "5d9ec8cbb2f13221d0463e474209d5a7bb3fbc4d1eb05bee28a15483b4c1173b",
}
D2_ROOT = ROOT / "src/Cardcha/assets/airship_props/set01_redux/window_runtime"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one baseline match, found {count}")
    return text.replace(old, new, 1)


def parse_layer(text: str, name: str, width: int, height: int) -> tuple[re.Match[str], list[int]]:
    pattern = re.compile(
        rf'(<layer id="\d+" name="{re.escape(name)}" width="{width}" height="{height}">.*?<data encoding="csv">)(.*?)(</data>.*?</layer>)',
        re.S,
    )
    match = pattern.search(text)
    if not match:
        raise RuntimeError(f"layer {name} not found")
    values = [int(x.strip()) for x in match.group(2).replace("\n", "").split(",") if x.strip()]
    if len(values) != width * height:
        raise RuntimeError(f"layer {name} tile count {len(values)} != {width * height}")
    return match, values


def write_layer(text: str, match: re.Match[str], values: list[int], width: int, height: int) -> str:
    rows = [",".join(str(v) for v in values[y * width:(y + 1) * width]) for y in range(height)]
    data = "\n" + ",\n".join(rows) + "\n"
    return text[:match.start()] + match.group(1) + data + match.group(3) + text[match.end():]


def set_shell_tile(values: list[int], width: int, x: int, y: int, gid: int, label: str) -> None:
    idx = y * width + x
    existing = values[idx]
    if existing not in (0, gid) and existing not in SHELL_GIDS:
        raise RuntimeError(f"{label}: refusing to overwrite non-shell tile {existing} at {x},{y}")
    values[idx] = gid


def patch_room1_shell() -> None:
    if sha(SHELL) != EXPECTED_SHELL_SHA:
        raise RuntimeError(f"room-shell source SHA changed: {sha(SHELL)}")

    text = DOCK.read_text(encoding="utf-8")
    width, height = 30, 18

    if 'CardchaSkyDockRoomShell0696D3C' not in text:
        tileset = (
            ' <tileset firstgid="7200" name="CardchaSkyDockRoomShell0696D3C" tilewidth="16" tileheight="16" tilecount="10" columns="10">\n'
            '  <image source="airship_props/room_shell/airship_deck_border_0696c.png" width="160" height="16" />\n'
            ' </tileset>\n'
        )
        marker = ' <layer id="1" name="Back" width="30" height="18">'
        if text.count(marker) != 1:
            raise RuntimeError("room-shell tileset insertion point missing")
        text = text.replace(marker, tileset + marker, 1)

    if 'CardchaRoomShellContract' not in text:
        prop = '  <property name="CardchaRoomShellContract" value="0696D3C|shared-0696c-shell|doorway-x14-15|finished-room-1" />\n'
        marker = '  <property name="CardchaSourceBlueprint" value="handoff/AIRSHIP_ROOM_BLUEPRINT_0696.json" />\n'
        if text.count(marker) != 1:
            raise RuntimeError("room-shell property insertion point missing")
        text = text.replace(marker, marker + prop, 1)

    # Buildings2 owns the top and vertical shell, mirroring the accepted room-2 grammar.
    m, values = parse_layer(text, "Buildings2", width, height)
    set_shell_tile(values, width, 0, 0, 7206, "top-left")
    for x in range(1, width - 1):
        set_shell_tile(values, width, x, 0, 7203, "top")
    set_shell_tile(values, width, width - 1, 0, 7207, "top-right")
    for y in range(1, height - 1):
        set_shell_tile(values, width, 0, y, 7200, "left")
        set_shell_tile(values, width, width - 1, y, 7201, "right")
    text = write_layer(text, m, values, width, height)

    # Front2 owns the lower lip so the player naturally passes behind it at the doorway.
    m, values = parse_layer(text, "Front2", width, height)
    door_left, door_right = width // 2 - 1, width // 2
    bottom = height - 1
    set_shell_tile(values, width, 0, bottom, 7204, "bottom-left")
    set_shell_tile(values, width, width - 1, bottom, 7205, "bottom-right")
    for x in range(1, width - 1):
        if x in (door_left, door_right):
            idx = bottom * width + x
            if values[idx] in SHELL_GIDS:
                values[idx] = 0
            continue
        gid = 7208 if x == door_left - 1 else 7209 if x == door_right + 1 else 7202
        set_shell_tile(values, width, x, bottom, gid, "bottom")
    text = write_layer(text, m, values, width, height)

    DOCK.write_text(text, encoding="utf-8")


def patch_outdoor_gate() -> None:
    text = FOUNDATION.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "    private const float ForestGateUseDistance = 160f;\n",
        "    private const float ForestGateUseDistance = 256f;\n",
        "outdoor gate interaction radius",
    )
    text = replace_once(
        text,
        "        // 0669: one compact authored boarding object. No procedural tower, no giant portal glass.\n        Vector2 world = new(tile.X * 64f + 32f, tile.Y * 64f + 70f);\n",
        "        // 0696D3-C: the accepted gate art is intentionally prominent and floor-anchored.\n        // Keep the same world anchor, but anchor the sprite by its true bottom so x2 scale does not drift downward.\n        Vector2 world = new(tile.X * 64f + 32f, tile.Y * 64f + 70f);\n",
        "outdoor gate anchor comment",
    )
    text = replace_once(
        text,
        "            new Vector2(gate.Width / 2f, gate.Height - 10f), 1.48f * pulse,\n",
        "            new Vector2(gate.Width / 2f, gate.Height), 2.88f * pulse,\n",
        "outdoor gate x2 scale and bottom anchor",
    )
    text = replace_once(
        text,
        "        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 42, (int)local.Y - 7, 84, 3), warm);\n",
        "        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 74, (int)local.Y - 7, 148, 4), warm);\n",
        "outdoor gate ground confirmation",
    )
    FOUNDATION.write_text(text, encoding="utf-8")


def patch_window_presentation() -> None:
    text = AMBIENT.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "    private const long D1SAirshipFrameDurationMs = 550L;\n",
        "    private const long D1SAirshipFrameDurationMs = 550L;\n    // 0696D3-C: subtle 6.25% centered overscan. Source PNG bytes stay canonical and untouched.\n    private const float ObservationWindowPresentationScale = 4.25f;\n",
        "window presentation scale constant",
    )

    old_env = """                batch.Draw(\n                    environment,\n                    new Rectangle(\n                        (int)propTopLeft.X,\n                        (int)propTopLeft.Y,\n                        config.FootprintPx.Width * 4,\n                        config.FootprintPx.Height * 4\n                    ),\n                    null,\n                    Color.White,\n                    0f,\n                    Vector2.Zero,\n                    SpriteEffects.None,\n                    0.8840f\n                );\n"""
    new_env = """                Rectangle presentation = ResolveObservationWindowPresentation(config, propTopLeft);\n                batch.Draw(\n                    environment,\n                    presentation,\n                    null,\n                    Color.White,\n                    0f,\n                    Vector2.Zero,\n                    SpriteEffects.None,\n                    0.8840f\n                );\n"""
    text = replace_once(text, old_env, new_env, "window environment presentation")

    old_ship = """        int frameIndex = (int)((clockMs / D1SAirshipFrameDurationMs) % D1SAirshipPositions.Length);\n        Point pos = D1SAirshipPositions[frameIndex];\n        batch.Draw(\n            airship,\n            new Rectangle(\n                (int)propTopLeft.X + pos.X * 4,\n                (int)propTopLeft.Y + pos.Y * 4,\n                airship.Width * 4,\n                airship.Height * 4\n            ),\n"""
    new_ship = """        int frameIndex = (int)((clockMs / D1SAirshipFrameDurationMs) % D1SAirshipPositions.Length);\n        Point pos = D1SAirshipPositions[frameIndex];\n        Rectangle presentation = ResolveObservationWindowPresentation(config, propTopLeft);\n        float presentationScale = presentation.Width / (float)Math.Max(1, config.FootprintPx.Width);\n        batch.Draw(\n            airship,\n            new Rectangle(\n                presentation.X + (int)MathF.Round(pos.X * presentationScale),\n                presentation.Y + (int)MathF.Round(pos.Y * presentationScale),\n                (int)MathF.Round(airship.Width * presentationScale),\n                (int)MathF.Round(airship.Height * presentationScale)\n            ),\n"""
    text = replace_once(text, old_ship, new_ship, "window airship presentation")

    old_lightning = """        batch.Draw(\n            flash,\n            new Rectangle((int)propTopLeft.X, (int)propTopLeft.Y, config.FootprintPx.Width * 4, config.FootprintPx.Height * 4),\n"""
    new_lightning = """        batch.Draw(\n            flash,\n            ResolveObservationWindowPresentation(config, propTopLeft),\n"""
    text = replace_once(text, old_lightning, new_lightning, "window lightning presentation")

    marker = "    private static Rectangle ScaleViewport(AirshipViewportConfig source, Vector2 propTopLeft)\n"
    helper = """    private static Rectangle ResolveObservationWindowPresentation(\n        AirshipObservationWindowConfig config,\n        Vector2 propTopLeft\n    )\n    {\n        int baseWidth = config.FootprintPx.Width * 4;\n        int baseHeight = config.FootprintPx.Height * 4;\n        int width = (int)MathF.Round(config.FootprintPx.Width * ObservationWindowPresentationScale);\n        int height = (int)MathF.Round(config.FootprintPx.Height * ObservationWindowPresentationScale);\n        return new Rectangle(\n            (int)propTopLeft.X - (width - baseWidth) / 2,\n            (int)propTopLeft.Y - (height - baseHeight) / 2,\n            width,\n            height\n        );\n    }\n\n"""
    if "private static Rectangle ResolveObservationWindowPresentation" not in text:
        if text.count(marker) != 1:
            raise RuntimeError("window presentation helper insertion point missing")
        text = text.replace(marker, helper + marker, 1)
    AMBIENT.write_text(text, encoding="utf-8")


def validate() -> dict:
    dock = DOCK.read_text(encoding="utf-8")
    foundation = FOUNDATION.read_text(encoding="utf-8")
    ambient = AMBIENT.read_text(encoding="utf-8")

    d2_actual = {}
    for state, expected in EXPECTED_D2.items():
        p = D2_ROOT / f"window_scene_default_{state}_clear.png"
        d2_actual[state] = sha(p)

    width, height = 30, 18
    _, b2 = parse_layer(dock, "Buildings2", width, height)
    _, f2 = parse_layer(dock, "Front2", width, height)
    top_ok = b2[0] == 7206 and b2[width - 1] == 7207 and all(b2[x] == 7203 for x in range(1, width - 1))
    sides_ok = all(b2[y * width] == 7200 and b2[y * width + width - 1] == 7201 for y in range(1, height - 1))
    door_left, door_right = width // 2 - 1, width // 2
    bottom = height - 1
    bottom_ok = (
        f2[bottom * width] == 7204
        and f2[bottom * width + width - 1] == 7205
        and f2[bottom * width + door_left] == 0
        and f2[bottom * width + door_right] == 0
        and f2[bottom * width + door_left - 1] == 7208
        and f2[bottom * width + door_right + 1] == 7209
    )

    checks = {
        "sharedRoomShellAssetExact": sha(SHELL) == EXPECTED_SHELL_SHA,
        "room1ShellTilesetPresent": "CardchaSkyDockRoomShell0696D3C" in dock,
        "room1TopShell": top_ok,
        "room1SideShells": sides_ok,
        "room1BottomDoorwayShell": bottom_ok,
        "room1ShellContract": "0696D3C|shared-0696c-shell|doorway-x14-15|finished-room-1" in dock,
        "outdoorGateApproximatelyX2": "2.88f * pulse" in foundation,
        "outdoorGateBottomAnchored": "new Vector2(gate.Width / 2f, gate.Height), 2.88f * pulse" in foundation,
        "outdoorGateUseRadiusScaled": "private const float ForestGateUseDistance = 256f;" in foundation,
        "windowPresentationScale": "private const float ObservationWindowPresentationScale = 4.25f;" in ambient,
        "windowCenteredOverscanHelper": "ResolveObservationWindowPresentation" in ambient,
        "d2CanonicalBytesFrozen": all(d2_actual[s] == EXPECTED_D2[s] for s in EXPECTED_D2),
    }

    report = {
        "phase": "0696D3-C",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "room1Shell": {
            "asset": str(SHELL.relative_to(ROOT)),
            "sha256": sha(SHELL),
            "map": str(DOCK.relative_to(ROOT)),
            "doorwayTiles": [[door_left, bottom], [door_right, bottom]],
        },
        "outdoorEntranceGate": {
            "scaleBefore": 1.48,
            "scaleAfter": 2.88,
            "useDistanceBefore": 160,
            "useDistanceAfter": 256,
            "anchorPolicy": "same-world-floor-point|true-bottom-origin",
        },
        "observationWindowPresentation": {
            "nativeSourceBytesChanged": False,
            "baseScreenScale": 4.0,
            "presentationScale": 4.25,
            "increasePercent": 6.25,
            "mode": "centered-runtime-overscan",
            "d2Sha256": d2_actual,
        },
        "checks": checks,
        "next": "0696D3-D regression and TEST package",
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
        patch_room1_shell()
        patch_outdoor_gate()
        patch_window_presentation()
    if args.validate:
        print(json.dumps(validate(), indent=2))


if __name__ == "__main__":
    main()
