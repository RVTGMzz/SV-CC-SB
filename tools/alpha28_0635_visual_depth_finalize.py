from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha"
VERSION = "0.3.0-alpha.28.0.4.14.4.5.4"

# Keep the small Harmony depth patch compile-safe and self-registering.
patch_path = SRC / "Patches" / "AirshipVisualDepthPatch.cs"
patch = patch_path.read_text(encoding="utf-8")
patch = patch.replace(
    "(effects & SpriteEffects.FlipHorizontally) != 0",
    "(effects & SpriteEffects.FlipHorizontally) != SpriteEffects.None",
)
patch_path.write_text(patch, encoding="utf-8")

# Startup log had been stale since the first Airship polish build. Keep runtime diagnostics aligned
# with the exact test package so screenshots/logs can identify the build unambiguously.
entry_path = SRC / "ModEntry.cs"
entry = entry_path.read_text(encoding="utf-8")
entry = re.sub(
    r'\$"Cardcha! v[^\"]+ AIRSHIP VISUAL POLISH TEST with \{this\.Cards\.All\.Count\} cards\.',
    f'$"Cardcha! v{VERSION} AIRSHIP VISUAL DEPTH PASS 1 TEST with {{this.Cards.All.Count}} cards.',
    entry,
    count=1,
)
entry_path.write_text(entry, encoding="utf-8")

print(f"Finalized Cardcha {VERSION} Airship Visual Depth Pass 1")
