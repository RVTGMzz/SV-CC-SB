#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "src/Cardcha/Services/AirshipAmbientAnimationService.cs"
text = PATH.read_text(encoding="utf-8")

field_marker = "    private static int LightningVariant;\n"
fields = '''    private static int LightningVariant;\n\n    // 0696D1R: preserve the approved 0690 contract. The physical Window body is map-native;\n    // runtime cycles four independent transparent 160x80 moving-sky overlays. D2 will later\n    // rebuild season/time/weather behavior from this accepted clean source.\n    private static readonly string[] D1RWindowOverlayPaths =\n    {\n        "assets/airship_props/set01_redux/observation_window_overlay_1.png",\n        "assets/airship_props/set01_redux/observation_window_overlay_2.png",\n        "assets/airship_props/set01_redux/observation_window_overlay_3.png",\n        "assets/airship_props/set01_redux/observation_window_overlay_4.png",\n    };\n    private const long D1RWindowFrameDurationMs = 450L;\n'''
if "D1RWindowOverlayPaths" not in text:
    if field_marker not in text:
        raise SystemExit("Could not find Airship ambient field insertion marker")
    text = text.replace(field_marker, fields, 1)

new_method = '''    private static bool DrawObservationWindow(SpriteBatch batch, long clockMs)\n    {\n        if (Resolver is null)\n            return false;\n\n        AirshipAmbientManifest? manifest = Resolver.Manifest;\n        if (manifest is null)\n            return false;\n\n        AirshipObservationWindowConfig config = manifest.ObservationWindow;\n        Vector2 propTopLeft = WorldToScreen(config.WorldAnchor.TileX * 64f, config.WorldAnchor.TileY * 64f);\n\n        int frameIndex = (int)((clockMs / D1RWindowFrameDurationMs) % D1RWindowOverlayPaths.Length);\n        string overlayPath = D1RWindowOverlayPaths[frameIndex];\n\n        // The TMX already owns the full physical body. Draw only one repaired transparent\n        // moving-sky overlay. Never crop, repack, shift or hollow the Window body here.\n        return DrawLegacyFullOverlay(batch, overlayPath, propTopLeft, depth: 0.8845f);\n    }\n\n'''
pattern = re.compile(
    r"    private static bool DrawObservationWindow\(SpriteBatch batch, long clockMs\)\n    \{.*?\n    \}\n\n(?=    private static bool DrawNavigationConsole)",
    re.S,
)
text, count = pattern.subn(new_method, text, count=1)
if count != 1:
    raise SystemExit(f"Expected to replace one DrawObservationWindow method, replaced {count}")

text = text.replace(
    "/// 0696C renderer for the two Airship hero ambient props.\n/// The window is resolved from an explicit season x time x weather scene matrix.\n/// IMPORTANT: 0690 window overlays 2..4 contain opaque black wipe pixels and are never\n/// used as production fallback. If new window art is unavailable, the clean TMX base remains.\n/// Navigation Console legacy overlays are safe and remain available as fallback.",
    "/// 0696D1R isolated Window recovery plus existing Console ambient renderer.\n/// Window returns to the approved 0690 ownership contract: static physical body in TMX,\n/// four independent transparent moving-sky overlays at runtime. D2 will rebuild the\n/// season/time/weather matrix only after Ron accepts this bounded source repair."
)

PATH.write_text(text, encoding="utf-8")
print("0696D1R runtime patched: four independent Window overlays active; matrix deferred to D2.")
