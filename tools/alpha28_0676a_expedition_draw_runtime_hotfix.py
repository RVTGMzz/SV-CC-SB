from pathlib import Path

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.45.1'
PREVIOUS = '0.3.0-alpha.28.0.4.14.4.5.12.45'


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding='utf-8')
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f'{label}: expected anchor not found')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')


# Keep the human-visible startup line aligned with the hotfix package version.
replace_once(
    ROOT / 'ModEntry.cs',
    f'Cardcha! {PREVIOUS} REGION III / IV TERRAIN DEPTH PASS TEST',
    f'Cardcha! {VERSION} REGION III / IV TERRAIN DEPTH + EXPEDITION DRAW HOTFIX TEST',
    'ModEntry startup version',
)

print('0676A expedition draw runtime hotfix generator PASS')
