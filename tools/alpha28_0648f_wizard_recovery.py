from pathlib import Path
import binascii
import json
import re
import struct
import subprocess
import zlib

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.12'
BASE_VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.10'
GOOD_PORTRAIT_REF = 'origin/cardcha-alpha28-0647b-mimi-portrait-runtime-hotfix'
GOOD_PORTRAIT_PATH = 'src/Cardcha/assets/mimi_portraits.png'
WIZARD_STAIR_TILE = (11, 15)


def png_chunk(kind: bytes, data: bytes) -> bytes:
    body = kind + data
    return struct.pack('>I', len(data)) + body + struct.pack('>I', binascii.crc32(body) & 0xffffffff)


def decode_rgba_png(raw: bytes):
    if raw[:8] != b'\x89PNG\r\n\x1a\n':
        raise RuntimeError('portrait source is not PNG')
    pos = 8
    width = height = None
    compressed = bytearray()
    while pos < len(raw):
        length = struct.unpack('>I', raw[pos:pos+4])[0]
        kind = raw[pos+4:pos+8]
        data = raw[pos+8:pos+8+length]
        pos += 12 + length
        if kind == b'IHDR':
            width, height, depth, color_type, compression, filter_method, interlace = struct.unpack('>IIBBBBB', data)
            if (depth, color_type, compression, filter_method, interlace) != (8, 6, 0, 0, 0):
                raise RuntimeError(f'unsupported portrait PNG format: {(depth, color_type, interlace)}')
        elif kind == b'IDAT':
            compressed.extend(data)
        elif kind == b'IEND':
            break
    if width is None or height is None:
        raise RuntimeError('portrait PNG missing IHDR')
    stream = zlib.decompress(bytes(compressed))
    stride = width * 4
    rows = []
    prev = bytearray(stride)
    offset = 0
    for _ in range(height):
        filter_type = stream[offset]
        offset += 1
        scan = bytearray(stream[offset:offset+stride])
        offset += stride
        recon = bytearray(stride)
        for i, val in enumerate(scan):
            a = recon[i-4] if i >= 4 else 0
            b = prev[i]
            c = prev[i-4] if i >= 4 else 0
            if filter_type == 0:
                x = val
            elif filter_type == 1:
                x = (val + a) & 255
            elif filter_type == 2:
                x = (val + b) & 255
            elif filter_type == 3:
                x = (val + ((a + b) // 2)) & 255
            elif filter_type == 4:
                p = a + b - c
                pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                x = (val + pr) & 255
            else:
                raise RuntimeError(f'unsupported PNG filter {filter_type}')
            recon[i] = x
        rows.append(bytes(recon))
        prev = recon
    return width, height, rows


def encode_rgba_png(width: int, height: int, rows) -> bytes:
    payload = b''.join(b'\x00' + row for row in rows)
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + png_chunk(b'IHDR', ihdr) + png_chunk(b'IDAT', zlib.compress(payload, 9)) + png_chunk(b'IEND', b'')


def build_native_64_portrait_sheet(source: bytes) -> bytes:
    width, height, rows = decode_rgba_png(source)
    if (width, height) != (768, 128):
        raise RuntimeError(f'expected last-known-good MiMi master 768x128, got {width}x{height}')
    frame_count = 6
    source_frame = 128
    target_frame = 64
    out_rows = []
    for ty in range(target_frame):
        sy = ty * 2
        src = rows[sy]
        out = bytearray(frame_count * target_frame * 4)
        for frame in range(frame_count):
            for tx in range(target_frame):
                sx = frame * source_frame + tx * 2
                src_i = sx * 4
                dst_i = (frame * target_frame + tx) * 4
                out[dst_i:dst_i+4] = src[src_i:src_i+4]
        out_rows.append(bytes(out))
    return encode_rgba_png(frame_count * target_frame, target_frame, out_rows)


def remove_method(source: str, signature: str) -> str:
    start = source.find(signature)
    if start < 0:
        return source
    line_start = source.rfind('\n', 0, start) + 1
    brace = source.find('{', start)
    if brace < 0:
        raise RuntimeError(f'opening brace not found for {signature}')
    depth = 0
    for i in range(brace, len(source)):
        if source[i] == '{':
            depth += 1
        elif source[i] == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                while end < len(source) and source[end] in ' \t\r\n':
                    end += 1
                return source[:line_start] + source[end:]
    raise RuntimeError(f'closing brace not found for {signature}')


# Version metadata only.
manifest = ROOT / 'manifest.json'
data = json.loads(manifest.read_text(encoding='utf-8-sig'))
data['Version'] = VERSION
manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for rel in ['Cardcha.csproj', 'Directory.Build.targets']:
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    if BASE_VERSION not in text:
        raise RuntimeError(f'base version missing from {rel}')
    path.write_text(text.replace(BASE_VERSION, VERSION), encoding='utf-8')

# 1) MiMi portrait recovery.
# Use the last-known-good sharp 128px/frame artwork from 0647B and materialize it ONCE
# at build time as a native 64px/frame Stardew portrait sheet. Runtime never resizes it.
source_portrait = subprocess.check_output(['git', 'show', f'{GOOD_PORTRAIT_REF}:{GOOD_PORTRAIT_PATH}'])
portrait_bytes = build_native_64_portrait_sheet(source_portrait)
portrait_path = ROOT / 'assets/mimi_portraits.png'
portrait_path.write_bytes(portrait_bytes)
for obsolete in [ROOT / 'assets/mimi_portraits_runtime64.png', ROOT / 'assets/mimi_npc_portraits.png']:
    if obsolete.exists():
        obsolete.unlink()

mystery_path = ROOT / 'Services/MimiMysteryTownService.cs'
mystery = mystery_path.read_text(encoding='utf-8')
mystery = mystery.replace(
    '// Engine-compatible 64x64 portrait fallback only. Runtime dialogue portraits are generated in memory from MimiPortraitsPath.',
    '// One canonical sharp Stardew portrait sheet: six native 64x64 frames shared by dialogue and social UI consumers.'
)
mystery = mystery.replace(
    'e.LoadFrom(() => this.GetNativePortraitCompatibilitySheet(), AssetLoadPriority.Medium);',
    'e.LoadFromModFile<Texture2D>(MimiPortraitsPath, AssetLoadPriority.Exclusive);'
)
mystery = mystery.replace(
    'SetRectangleProperty(mimi, "MugShotSourceRect", 0, 192, 16, 24);',
    '// Gift Log / Social mugshot comes from the character sheet, not Portraits/. Crop the crisp front-facing head.\n                SetRectangleProperty(mimi, "MugShotSourceRect", 8, 0, 16, 24);'
)
mystery = remove_method(mystery, 'private Texture2D GetNativePortraitCompatibilitySheet()')
mystery = remove_method(mystery, 'private static Texture2D CreateRuntimePortraitSheet(Texture2D master)')
mystery_path.write_text(mystery, encoding='utf-8')

# 2) Wizard stair recovery.
# The user's WizardHouse is SVE's 15x35 map. The previous accepted landmark-relative rule
# resolved to EXACT tile 11,15. Freeze that numeric result so it cannot drift or search elsewhere.
home_path = ROOT / 'Services/MimiHomeService.cs'
home = home_path.read_text(encoding='utf-8')
start = home.index('    internal static Point ResolvePreferredWizardStairTile(GameLocation wizard)')
end = home.index('    private static Point ResolveWizardLandingTile', start)
home = home[:start] + '''    internal static Point ResolvePreferredWizardStairTile(GameLocation wizard)\n    {\n        // SVE WizardHouse exact acceptance tile: upper recessed niche between the two plants.\n        // Fixed absolute tile only. No percentages, map-size math, search, or dynamic relocation.\n        return new Point(11, 15);\n    }\n\n''' + home[end:]
home_path.write_text(home, encoding='utf-8')

# 3) Stair layering recovery.
# Keep the stair in-world and split it so no full-height always-front sprite can cover the farmer.
visual_path = ROOT / 'Services/MimiAtticVisualService.cs'
visual = visual_path.read_text(encoding='utf-8')
method_start = visual.index('    private void DrawStairMarker(SpriteBatch batch, Point tile)')
method_end = visual.index('    private static AtticLayout GetLayout', method_start)
visual = visual[:method_start] + '''    private void DrawStairMarker(SpriteBatch batch, Point tile)\n    {\n        try\n        {\n            Texture2D staircase = this.Helper.ModContent.Load<Texture2D>(StairSpritePath);\n\n            Rectangle upperSource = new(0, 0, staircase.Width, 48);\n            Rectangle lowerSource = new(0, 48, staircase.Width, 16);\n            Vector2 upperWorld = new(tile.X * 64f, (tile.Y - 4) * 64f);\n            Vector2 lowerWorld = new(tile.X * 64f, (tile.Y - 1) * 64f);\n            Vector2 upperScreen = Game1.GlobalToLocal(Game1.viewport, upperWorld);\n            Vector2 lowerScreen = Game1.GlobalToLocal(Game1.viewport, lowerWorld);\n\n            // Normal world-Y depths. A farmer standing in front has a larger depth and therefore\n            // renders over the stair instead of having their face/body covered by it.\n            float upperDepth = Math.Clamp(((tile.Y - 1) * 64f - 8f) / 10000f, 0.001f, 0.90f);\n            float lowerDepth = Math.Clamp((tile.Y * 64f - 8f) / 10000f, 0.001f, 0.90f);\n\n            batch.Draw(staircase, upperScreen, upperSource, Color.White, 0f, Vector2.Zero, 4f, SpriteEffects.None, upperDepth);\n            batch.Draw(staircase, lowerScreen, lowerSource, Color.White, 0f, Vector2.Zero, 4f, SpriteEffects.None, lowerDepth);\n        }\n        catch\n        {\n            // The warp remains functional if the cosmetic marker cannot be loaded.\n        }\n    }\n\n''' + visual[method_end:]
visual_path.write_text(visual, encoding='utf-8')

print(json.dumps({
    'version': VERSION,
    'portrait': 'last-known-good 0647B art -> static 384x64 native sheet',
    'mugshotSourceRect': [8, 0, 16, 24],
    'wizardHouseDimensionsVerified': [15, 35],
    'wizardStairTile': list(WIZARD_STAIR_TILE),
    'runtimePortraitResize': False,
    'dynamicStairPlacement': False
}, indent=2))
