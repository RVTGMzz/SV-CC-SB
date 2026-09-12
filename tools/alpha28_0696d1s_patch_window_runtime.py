#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "src/Cardcha/Services/AirshipAmbientAnimationService.cs"

OLD_HEADER = '''/// <summary>
/// 0696D1R isolated Window recovery plus existing Console ambient renderer.
/// Window returns to the approved 0690 ownership contract: static physical body in TMX,
/// four independent transparent moving-sky overlays at runtime. D2 will rebuild the
/// season/time/weather matrix only after Ron accepts this bounded source repair.
/// </summary>'''

NEW_HEADER = '''/// <summary>
/// 0696D1S isolated Window motion repair plus existing Console ambient renderer.
/// The physical Window body remains map-native. Runtime moves one extracted real airship
/// sprite only; legacy overlay_2..4 window/transition slices are never animated.
/// D2 will rebuild the season/time/weather matrix after Ron accepts this motion contract.
/// </summary>'''

OLD_BLOCK = '''    // 0696D1R: preserve the approved 0690 contract. The physical Window body is map-native;
    // runtime cycles four independent transparent 160x80 moving-sky overlays. D2 will later
    // rebuild season/time/weather behavior from this accepted clean source.
    private static readonly string[] D1RWindowOverlayPaths =
    {
        "assets/airship_props/set01_redux/observation_window_overlay_1.png",
        "assets/airship_props/set01_redux/observation_window_overlay_2.png",
        "assets/airship_props/set01_redux/observation_window_overlay_3.png",
        "assets/airship_props/set01_redux/observation_window_overlay_4.png",
    };
    private const long D1RWindowFrameDurationMs = 450L;
'''

NEW_BLOCK = '''    // 0696D1S: the four legacy Window overlays are NOT four airship frames.
    // Only this extracted airship sprite moves. The Window frame/body stays map-native.
    private const string D1SAirshipPath =
        "assets/airship_props/set01_redux/window_runtime/observation_window_airship.png";
    private static readonly Point[] D1SAirshipPositions =
    {
        new(62, 33),
        new(71, 33),
        new(80, 33),
        new(89, 33),
    };
    private const long D1SAirshipFrameDurationMs = 550L;
'''

NEW_METHOD = '''    private static bool DrawObservationWindow(SpriteBatch batch, long clockMs)
    {
        if (Resolver is null)
            return false;

        AirshipAmbientManifest? manifest = Resolver.Manifest;
        if (manifest is null)
            return false;

        AirshipObservationWindowConfig config = manifest.ObservationWindow;
        Vector2 propTopLeft = WorldToScreen(config.WorldAnchor.TileX * 64f, config.WorldAnchor.TileY * 64f);

        Texture2D? airship = GetTexture(D1SAirshipPath);
        if (airship is null)
            return false;

        int frameIndex = (int)((clockMs / D1SAirshipFrameDurationMs) % D1SAirshipPositions.Length);
        Point pos = D1SAirshipPositions[frameIndex];

        // Draw only the real airship sprite. Never draw legacy overlay_2..4 here: those files
        // are window/transition slices and made the pillar appear to fly across the sky.
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


def main() -> None:
    text = SERVICE.read_text(encoding="utf-8")

    if "D1SAirshipPath" in text and "observation_window_overlay_2.png" not in text:
        print("D1S runtime already patched")
        return

    if OLD_HEADER in text:
        text = text.replace(OLD_HEADER, NEW_HEADER)
    if OLD_BLOCK not in text:
        raise RuntimeError("Could not locate D1R Window overlay block")
    text = text.replace(OLD_BLOCK, NEW_BLOCK)

    start = text.index("    private static bool DrawObservationWindow")
    end = text.index("    private static bool DrawNavigationConsole", start)
    text = text[:start] + NEW_METHOD + text[end:]

    if "observation_window_overlay_2.png" in text:
        raise RuntimeError("Legacy overlay cycling still referenced after patch")
    if "D1SAirshipPath" not in text:
        raise RuntimeError("Real airship runtime path missing after patch")

    SERVICE.write_text(text, encoding="utf-8")
    print("0696D1S Window runtime patched: only real airship sprite moves")


if __name__ == "__main__":
    main()
