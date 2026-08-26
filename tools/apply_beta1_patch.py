from __future__ import annotations

from collections import Counter
from pathlib import Path
import base64
import hashlib
import json
import shutil
import tempfile
import zipfile

ROOT = Path('src/Cardcha')
PARTS_DIR = Path('tools/beta1_payload_parts')
PAYLOAD = Path('tools/beta1_payload.zip')
EXPECTED_BASE64_LENGTH = 181388
EXPECTED_PAYLOAD_SHA256 = '46a3bd71ba3255f9bc465a359907a3cbb5343971e6d2f113c3fd66cbe0f8fbfb'
EXPECTED_WALK_SHA256 = '87d07c9e5e8bb9fe18bdcb110ed2ce49f081e84c80e8e23fe647b01f8adc01a5'
EXPECTED_RARITIES = {
    'Common': 27,
    'Rare': 23,
    'Epic': 16,
    'Legendary': 10,
    'Mythic': 4,
}

parts = sorted(PARTS_DIR.glob('part*.txt'))
if not parts:
    raise SystemExit(f'beta.1 payload parts missing: {PARTS_DIR}')
encoded = ''.join(part.read_text(encoding='utf-8').strip() for part in parts)
if len(encoded) != EXPECTED_BASE64_LENGTH:
    raise SystemExit(f'beta.1 payload base64 length mismatch: {len(encoded)}')
try:
    payload_bytes = base64.b64decode(encoded, validate=True)
except Exception as exc:
    raise SystemExit(f'beta.1 payload base64 decode failed: {exc}') from exc
payload_sha = hashlib.sha256(payload_bytes).hexdigest()
if payload_sha != EXPECTED_PAYLOAD_SHA256:
    raise SystemExit(f'beta.1 payload sha256 mismatch: {payload_sha}')
PAYLOAD.write_bytes(payload_bytes)

with tempfile.TemporaryDirectory(prefix='cardcha-beta1-') as tmp_name:
    tmp = Path(tmp_name)
    with zipfile.ZipFile(PAYLOAD) as archive:
        archive.extractall(tmp)

    note = tmp / 'BETA1_BASESET80_NOTES.md'
    if note.exists():
        shutil.copy2(note, Path('BETA1_BASESET80_NOTES.md'))

    for source in sorted(tmp.rglob('*')):
        if not source.is_file() or source.name == 'BETA1_BASESET80_NOTES.md':
            continue
        rel = source.relative_to(tmp)
        target = ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

# The latest player-approved MiMi sheet is part of the beta payload.
walk_sha = hashlib.sha256((ROOT / 'assets/mimi_walk.png').read_bytes()).hexdigest()
if walk_sha != EXPECTED_WALK_SHA256:
    raise SystemExit(f'beta.1 MiMi walk sheet mismatch: {walk_sha}')

# Validate the authored Base Set before compiling.
cards = json.loads((ROOT / 'assets/cards.json').read_text(encoding='utf-8-sig'))
if not isinstance(cards, list) or len(cards) != 80:
    raise SystemExit(f'beta.1 Base Set must contain 80 cards; got {len(cards) if isinstance(cards, list) else type(cards).__name__}')

base_ids = sorted(int(card['BaseId']) for card in cards)
if base_ids != list(range(1, 81)):
    raise SystemExit('beta.1 Base Set IDs must be exactly 01-80')

string_ids = [str(card['Id']).strip().lower() for card in cards]
if len(set(string_ids)) != 80:
    raise SystemExit('beta.1 Base Set has duplicate string IDs')

rarities = Counter(str(card['Rarity']) for card in cards)
if dict(rarities) != EXPECTED_RARITIES:
    raise SystemExit(f'beta.1 rarity split mismatch: {dict(rarities)}')

essence = next((card for card in cards if str(card['Id']).lower() == 'essence_finder'), None)
if essence is None or essence.get('Rarity') != 'Rare':
    raise SystemExit('beta.1 Essence Finder must exist and be Rare')

for card in cards:
    max_level = int(card.get('MaxLevel', 0))
    rules = card.get('StarRules') or []
    if max_level < 1 or max_level > 5 or len(rules) < max_level:
        raise SystemExit(f"beta.1 invalid star table for {card.get('Id')}: max={max_level}, rules={len(rules)}")
    if int(card.get('IconIndex', -1)) < 0 and not bool(card.get('UseInitialFallback')):
        raise SystemExit(f"beta.1 missing icon/fallback for {card.get('Id')}")

# Every card must have localized name/description/star rules in both shipped languages.
for language in ('default.json', 'vi.json'):
    data = json.loads((ROOT / 'i18n' / language).read_text(encoding='utf-8-sig'))
    missing: list[str] = []
    for card in cards:
        card_id = card['Id']
        for key in (f'card.{card_id}.name', f'card.{card_id}.desc'):
            if not str(data.get(key, '')).strip():
                missing.append(key)
        for level in range(1, int(card['MaxLevel']) + 1):
            key = f'card.{card_id}.star.{level}'
            if not str(data.get(key, '')).strip():
                missing.append(key)
    if missing:
        raise SystemExit(f'beta.1 {language} missing {len(missing)} card localization keys; first: {missing[:8]}')

# The previous workflow step materializes alpha.10, then beta.1 takes ownership of the test version.
for rel in ('Cardcha.csproj', 'manifest.json'):
    path = ROOT / rel
    text = path.read_text(encoding='utf-8')
    if '0.2.0-alpha.10' not in text:
        raise SystemExit(f'beta.1 expected alpha.10 version marker in {rel}')
    path.write_text(text.replace('0.2.0-alpha.10', '0.2.0-beta.1'), encoding='utf-8')

print('beta.1: Base Set 80 payload reconstructed, applied and validated')
print('payload sha256:', payload_sha)
print('rarities:', dict(rarities))
print('MiMi walk sha256:', walk_sha)
