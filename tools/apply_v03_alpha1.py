from __future__ import annotations

from pathlib import Path
import base64
import hashlib
import json
import shutil
import tempfile
import zipfile

ROOT = Path('src/Cardcha')
PAYLOAD_B64 = Path('tools/v03_templates_payload.b64')
EXPECTED_PAYLOAD_SHA256 = 'a34b0e08f13ff6754d49a8c0353f122527ba83edc16d16066d32b5754e6548cd'

if not PAYLOAD_B64.exists():
    raise SystemExit(f'v0.3 payload missing: {PAYLOAD_B64}')
payload = base64.b64decode(PAYLOAD_B64.read_text(encoding='ascii').strip(), validate=True)
payload_sha = hashlib.sha256(payload).hexdigest()
if payload_sha != EXPECTED_PAYLOAD_SHA256:
    raise SystemExit(f'v0.3 payload checksum mismatch: {payload_sha}')

with tempfile.TemporaryDirectory(prefix='cardcha-v03-') as tmp_name:
    tmp = Path(tmp_name)
    zip_path = tmp / 'payload.zip'
    zip_path.write_bytes(payload)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(tmp)
    templates = tmp / 'v03_templates'

    required_templates = [
        'UI/CardchaBinderMenuV2.cs',
        'UI/CardRenderer.cs',
        'UI/CardchaUi.cs',
        'Models/SaveData.cs',
        'Services/SaveService.cs',
    ]
    for rel in required_templates:
        src = templates / rel
        if not src.exists():
            raise SystemExit(f'v0.3 template missing: {src}')
        dst = ROOT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

# v0.3 collection rendering uses the single canonical 80-card atlas in BaseId order.
cards_path = ROOT / 'assets/cards.json'
cards = json.loads(cards_path.read_text(encoding='utf-8-sig'))
if len(cards) != 80:
    raise SystemExit(f'v0.3 expected 80 cards, got {len(cards)}')
for card in cards:
    base_id = int(card['BaseId'])
    if not 1 <= base_id <= 80:
        raise SystemExit(f'v0.3 invalid BaseId: {base_id}')
    card['IconIndex'] = base_id - 1
    card['UseInitialFallback'] = False
cards_path.write_text(json.dumps(cards, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

translations = {
    'vi.json': {
        'binder.collection.in-use': 'ĐANG DÙNG',
        'binder.collection.progress': 'BỘ SƯU TẬP — {{owned}} / {{total}}',
        'binder.collection.filter-progress': '{{rarity}} — {{owned}} / {{total}}',
        'binder.favorite.tab': 'YÊU THÍCH',
        'binder.favorite.header': 'YÊU THÍCH — {{count}}',
        'binder.favorite.empty': 'Chưa có thẻ yêu thích. Chọn một lá đã sở hữu rồi nhấn YÊU THÍCH.',
        'binder.favorite.add': 'YÊU THÍCH',
        'binder.favorite.remove': 'BỎ YÊU THÍCH',
        'binder.favorite.added': 'Đã thêm {{name}} vào Yêu thích.',
        'binder.favorite.removed': 'Đã bỏ {{name}} khỏi Yêu thích.',
        'binder.favorite.filter-active': 'Đang xem các thẻ bạn đã đánh dấu Yêu thích.',
        'binder.note': 'GHI CHÚ',
        'binder.inspect-help': 'Chọn một biểu tượng thẻ đã sở hữu ở trang trái để xem đầy đủ thông tin tại đây.',
        'binder.hint': 'A/bấm: xem  •  Nhấp đúp/Y: trang bị hoặc tháo nhanh',
    },
    'default.json': {
        'binder.collection.in-use': 'IN USE',
        'binder.collection.progress': 'COLLECTION — {{owned}} / {{total}}',
        'binder.collection.filter-progress': '{{rarity}} — {{owned}} / {{total}}',
        'binder.favorite.tab': 'FAVORITES',
        'binder.favorite.header': 'FAVORITES — {{count}}',
        'binder.favorite.empty': 'No favorite cards yet. Select an owned card and mark it as a favorite.',
        'binder.favorite.add': 'FAVORITE',
        'binder.favorite.remove': 'REMOVE FAVORITE',
        'binder.favorite.added': 'Added {{name}} to Favorites.',
        'binder.favorite.removed': 'Removed {{name}} from Favorites.',
        'binder.favorite.filter-active': 'Showing cards marked as Favorites.',
        'binder.note': 'NOTES',
        'binder.inspect-help': 'Select an owned card icon on the left page to inspect its full details here.',
        'binder.hint': 'A/click: inspect  •  Double-click/Y: quick equip or remove',
    },
}
for filename, patch in translations.items():
    path = ROOT / 'i18n' / filename
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    data.update(patch)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

for rel in ('Cardcha.csproj', 'manifest.json'):
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    if '0.2.0-beta.3' not in text:
        raise SystemExit(f'v0.3 expected beta.3 version marker in {rel}')
    path.write_text(text.replace('0.2.0-beta.3', '0.3.0-alpha.1'), encoding='utf-8')

ids = [int(c['BaseId']) for c in cards]
icons = [int(c['IconIndex']) for c in cards]
if ids != list(range(1, 81)):
    raise SystemExit('v0.3 Base IDs must remain fixed at 01-80')
if icons != list(range(80)):
    raise SystemExit('v0.3 icon map must be BaseId-1 for all 80 cards')
for filename in translations:
    data = json.loads((ROOT / 'i18n' / filename).read_text(encoding='utf-8-sig'))
    missing = [key for key in translations[filename] if not str(data.get(key, '')).strip()]
    if missing:
        raise SystemExit(f'v0.3 missing translation keys in {filename}: {missing}')

print('v0.3 alpha.1: new Binder UI templates applied')
print('collection: fixed BaseId order, 20 cards/page, grayscale locked icons, rarity borders')
print('favorites: persistent save field + separate bottom bookmark + detail action')
print('loadout: five circular active slots; Boss Slot remains locked')
