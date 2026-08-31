from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "src" / "Cardcha" / "assets" / "airship_visual.png"


def main() -> None:
    image = Image.open(ASSET).convert("RGBA")
    if image.size != (384, 256):
        raise RuntimeError(f"Unexpected airship asset size: {image.size}")

    source = np.array(image, dtype=np.uint8)
    output = source.copy()

    # Remove the two baked/static propeller assemblies by restoring nearby hull pixels.
    # Runtime code draws the only visible propeller blades, so the base art must be blade-free.
    mask_image = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask_image)
    draw.ellipse((77, 165, 131, 229), fill=255)
    draw.ellipse((254, 165, 315, 232), fill=255)
    mask = np.array(mask_image) > 0

    for y, x in zip(*np.where(mask)):
        if y < 172:
            continue
        sample_x = x + 54 if x < 190 else x - 99
        sample_x = max(0, min(source.shape[1] - 1, sample_x))
        output[y, x] = source[y, sample_x]

    # Fully transparent pixels in the old PNG kept near-white RGB values, which can produce
    # a light fringe on dark backgrounds in some render paths. Normalize them to transparent black.
    output[output[:, :, 3] == 0, :3] = 0

    # Remove only neutral near-white edge pixels connected to transparency. The actual airship
    # outline is dark/gold, so this targets export fringe without bleaching the cream balloon.
    for _ in range(3):
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
        neutral_bright = (rgb.min(axis=2) > 225) & ((rgb.max(axis=2) - rgb.min(axis=2)) < 20)
        remove = (alpha > 0) & neighbor_transparent & neutral_bright
        output[remove] = (0, 0, 0, 0)

    output[output[:, :, 3] == 0, :3] = 0
    Image.fromarray(output, mode="RGBA").save(ASSET, optimize=True, compress_level=9)
    print("Airship asset cleaned: transparent edge normalized; baked propeller blades removed.")


if __name__ == "__main__":
    main()
