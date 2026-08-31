from __future__ import annotations

from pathlib import Path
from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "src" / "Cardcha" / "assets" / "airship_visual.png"


def main() -> None:
    image = Image.open(ASSET).convert("RGBA")
    if image.size != (384, 256):
        raise RuntimeError(f"Unexpected airship asset size: {image.size}")

    output = np.array(image, dtype=np.uint8)

    # alpha28.0.4.11 ships with the static propeller blades already removed from the source PNG.
    # This tool is intentionally idempotent: it only sanitizes alpha-edge RGB and must NOT try
    # to repaint/clone hull pixels on every CI run. Runtime code draws the only visible blades.
    output[output[:, :, 3] == 0, :3] = 0

    # Remove only neutral near-white export fringe that touches transparency. The cream balloon
    # is warm/beige rather than neutral white, so the narrow neutral threshold avoids eating art.
    for _ in range(2):
        alpha = output[:, :, 3]
        transparent = alpha == 0
        neighbor_transparent = np.zeros_like(transparent)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                shifted = np.roll(np.roll(transparent, dy, axis=0), dx, axis=1)
                if dy == -1:
                    shifted[-1, :] = False
                elif dy == 1:
                    shifted[0, :] = False
                if dx == -1:
                    shifted[:, -1] = False
                elif dx == 1:
                    shifted[:, 0] = False
                neighbor_transparent |= shifted

        rgb = output[:, :, :3].astype(np.int16)
        neutral_bright = (rgb.min(axis=2) > 235) & ((rgb.max(axis=2) - rgb.min(axis=2)) < 14)
        remove = (alpha > 0) & neighbor_transparent & neutral_bright
        output[remove] = (0, 0, 0, 0)

    output[output[:, :, 3] == 0, :3] = 0
    Image.fromarray(output, mode="RGBA").save(ASSET, optimize=True, compress_level=9)
    print("Airship asset alpha sanitized; no static-blade repainting performed.")


if __name__ == "__main__":
    main()
