from pathlib import Path
import hashlib
import io
import subprocess

from PIL import Image

BASELINE = '517a462648e0df9144c0a1e54475d1836834dcaa'
ROOT = Path('src/Cardcha')


def git_bytes(path: str) -> bytes:
    return subprocess.check_output(['git', 'show', f'{BASELINE}:{path}'])


def largest_component(cell: Image.Image) -> Image.Image:
    alpha = cell.getchannel('A')
    width, height = cell.size
    px = alpha.load()
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []

    for y in range(height):
        for x in range(width):
            if px[x, y] == 0 or (x, y) in seen:
                continue
            stack = [(x, y)]
            seen.add((x, y))
            component: list[tuple[int, int]] = []
            while stack:
                cx, cy = stack.pop()
                component.append((cx, cy))
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in seen and px[nx, ny] > 0:
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            components.append(component)

    if not components:
        return Image.new('RGBA', (1, 1), (0, 0, 0, 0))

    component = max(components, key=len)
    xs = [x for x, _ in component]
    ys = [y for _, y in component]
    mask = Image.new('L', cell.size, 0)
    mask_px = mask.load()
    for x, y in component:
        mask_px[x, y] = 255

    isolated = Image.new('RGBA', cell.size, (0, 0, 0, 0))
    isolated.paste(cell, (0, 0), mask)
    return isolated.crop((min(xs), min(ys), max(xs) + 1, max(ys) + 1))


def normalize_32_sheet(source_bytes: bytes) -> tuple[Image.Image, list[Image.Image]]:
    source = Image.open(io.BytesIO(source_bytes)).convert('RGBA')
    if source.size != (128, 32):
        raise RuntimeError(f'Expected 128x32 source, got {source.size}')

    output = Image.new('RGBA', (128, 32), (0, 0, 0, 0))
    normalized_cells: list[Image.Image] = []
    for index in range(4):
        cell = source.crop((index * 32, 0, (index + 1) * 32, 32))
        art = largest_component(cell).resize((28, 28), Image.Resampling.NEAREST)
        output.paste(art, (index * 32 + 2, 2), art)
        normalized_cells.append(art)
    return output, normalized_cells


def save_png(image: Image.Image, path: Path) -> str:
    image.save(path, format='PNG', optimize=False)
    return hashlib.sha256(path.read_bytes()).hexdigest()


materials, material_cells = normalize_32_sheet(
    git_bytes('src/Cardcha/assets/chacha_skill_materials.png')
)
icons, _ = normalize_32_sheet(
    git_bytes('src/Cardcha/assets/chacha_skill_icons.png')
)

# Restore the three legacy 16x16 item cells from a known-good backup before
# the ChaCha material atlas was introduced, then append four corrected material cells.
legacy = Image.open(
    io.BytesIO(git_bytes('_BACKUP_OLD_CARDCHA/20260825_200237_Cardcha/assets/items.png'))
).convert('RGBA')
if legacy.size != (48, 16):
    raise RuntimeError(f'Expected 48x16 legacy item sheet, got {legacy.size}')

items = Image.new('RGBA', (112, 16), (0, 0, 0, 0))
items.paste(legacy, (0, 0), legacy)
for index, material in enumerate(material_cells):
    small = material.resize((14, 14), Image.Resampling.NEAREST)
    items.paste(small, ((index + 3) * 16 + 1, 1), small)

hashes = {
    'items.png': save_png(items, ROOT / 'assets/items.png'),
    'chacha_skill_materials.png': save_png(materials, ROOT / 'assets/chacha_skill_materials.png'),
    'chacha_skill_icons.png': save_png(icons, ROOT / 'assets/chacha_skill_icons.png'),
}

for name, digest in hashes.items():
    print(f'{name} {digest}')
