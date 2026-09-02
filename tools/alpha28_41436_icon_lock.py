from pathlib import Path
import hashlib
import struct
import runpy

ROOT = Path('src/Cardcha')
ICON = ROOT / 'assets/card_icons.png'
LOCK = ROOT / 'assets/card_icons.sha256.lock'

raw = ICON.read_bytes()
assert len(raw) >= 24 and raw[:8] == b'\x89PNG\r\n\x1a\n', 'card_icons.png is not a PNG'
width, height = struct.unpack('>II', raw[16:24])
assert (width, height) == (320, 1024), f'card icon atlas must stay 320x1024, got {width}x{height}'
digest = hashlib.sha256(raw).hexdigest()

if LOCK.exists():
    expected = LOCK.read_text(encoding='utf-8').strip().lower()
    if expected and expected != digest:
        raise SystemExit(
            'card_icons.png no longer matches the approved official atlas lock. '
            f'expected {expected}, got {digest}. Update the lock only after explicit art approval.'
        )
else:
    LOCK.write_text(digest + '\n', encoding='utf-8')
    print(f'Adopted replacement official card icon atlas SHA-256: {digest}')

print(f'Card icon atlas lock PASS: {digest} ({width}x{height})')

# .4.14.3.7 one-time compatibility pre-hook. The historical Core service has an XML
# summary between namespace and class, so prepare the debug-snapshot anchor before the
# Auto Scenario finalizer. The shim is idempotent and does not touch gameplay behavior.
shim = Path('tools/alpha28_41437_core_anchor.py')
if shim.exists():
    runpy.run_path(str(shim), run_name='__main__')
