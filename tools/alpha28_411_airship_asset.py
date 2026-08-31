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

    # alpha28.0.4.11: static propeller blades are absent from the base sprite.
    # Runtime code is the only place that renders spinning blades.
    # This pass only cleans the matte/background and is deliberately idempotent.
    rgb = output[:, :, :3].astype(np.int16)
    alpha = output[:, :, 3]
    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)

    # The source export contains fully opaque neutral whites between ropes/struts.
    # They are background, not ship art. Remove all neutral-white islands, not only
    # pixels connected to the outside edge, so dark scenes don't show white panels.
    neutral_white = (alpha > 0) & (mn >= 228) & ((mx - mn) <= 26)
    output[neutral_white] = (0, 0, 0, 0)

    # Peel the remaining neutral anti-aliased matte one pixel layer at a time.
    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),            (0, 1),
        (1, -1),  (1, 0),   (1, 1),
    ]
    for threshold in (220, 212, 204, 196):
        alpha = output[:, :, 3]
        transparent = alpha == 0
        neighbor_transparent = np.zeros_like(transparent)

        for dy, dx in directions:
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
        mx = rgb.max(axis=2)
        mn = rgb.min(axis=2)
        fringe = (alpha > 0) & neighbor_transparent & (mn >= threshold) & ((mx - mn) <= 34)
        output[fringe] = (0, 0, 0, 0)

    # Transparent pixels must have black RGB so texture filtering cannot resurrect
    # a pale matte around the silhouette on dark backgrounds.
    output[output[:, :, 3] == 0, :3] = 0

    Image.fromarray(output, mode="RGBA").save(ASSET, optimize=True, compress_level=9)
    print(
        "Airship asset cleaned: opaque white matte removed, alpha fringe stripped, "
        "transparent RGB normalized; runtime-only propeller blades preserved."
    )


if __name__ == "__main__":
    main()
