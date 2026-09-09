from pathlib import Path
import json, struct, subprocess, xml.etree.ElementTree as ET

root = Path('src/Cardcha')
version = '0.3.0-alpha.28.0.4.14.4.5.12.40'
manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
assert manifest['Version'] == version
assert version in (root/'Cardcha.csproj').read_text(encoding='utf-8')
assert version in (root/'Directory.Build.targets').read_text(encoding='utf-8')
assert 'AUTHORED BOSS VISUALS ARENAS TEST' in (root/'ModEntry.cs').read_text(encoding='utf-8')

def png_size(path):
    data = Path(path).read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n', path
    return struct.unpack('>II', data[16:24])

dims = {
    'assets/bosses/milestone/hollow_curator.png': (96,64),
    'assets/bosses/milestone/hollow_curator_arena_tiles.png': (128,64),
    'assets/bosses/milestone/tricolor_guardians.png': (144,48),
    'assets/bosses/milestone/tricolor_unified.png': (128,64),
    'assets/bosses/milestone/tricolor_arena_tiles.png': (128,64),
    'assets/bosses/milestone/mimi_resonance_master.png': (192,64),
    'assets/bosses/milestone/mimi_arena_tiles.png': (128,64),
    'assets/chacha_mirror_rabbit.png': (128,128),
    'assets/chacha_trinity_rabbit.png': (128,128),
    'assets/chacha_resonance_rabbit.png': (128,128),
}
for rel, expected in dims.items():
    p = root/rel
    assert p.exists() and p.stat().st_size > 100, rel
    assert png_size(p) == expected, (rel, png_size(p), expected)

boss = (root/'Services/MilestoneBossService.cs').read_text(encoding='utf-8')
for token in [
    'HollowCuratorMapPath = "assets/boss2_hollow_curator_arena.tmx"',
    'TricolorMapPath = "assets/boss3_tricolor_resonance_arena.tmx"',
    'MimiMapPath = "assets/boss4_mimi_resonance_arena.tmx"',
    'HollowCuratorTexturePath','TricolorGuardiansTexturePath','TricolorUnifiedTexturePath','MimiTexturePath',
    'this.Helper.ModContent.Load<Texture2D>(HollowCuratorTexturePath)',
    'this.Helper.ModContent.Load<Texture2D>(TricolorGuardiansTexturePath)',
    'this.Helper.ModContent.Load<Texture2D>(MimiTexturePath)',
    'HollowCuratorMaxHealth = 2200','TricolorGuardianMaxHealth = 780','TricolorUnifiedMaxHealth = 1650','MimiMaxHealth = 3600',
    'MirrorArchiveBossCardId = "mirror_archive"','TricolorBossCardId = "tricolor_resonance"','MimiBossCardId = "mimis_resonance"',
]: assert token in boss, token
assert 'SharedArenaMapPath' not in boss

world = (root/'Services/WorldActorService.cs').read_text(encoding='utf-8')
for token in ['ChaChaMirrorCharacterAsset','ChaChaTrinityCharacterAsset','ChaChaResonanceCharacterAsset',
              'ChaChaMirrorSheetPath','ChaChaTrinitySheetPath','ChaChaResonanceSheetPath',
              'GetChaChaBossCharacterAsset()', 'SetChaChaBossVisual(bool active, string formId)']:
    assert token in world, token

forms = (root/'Services/ChaChaBossFormService.cs').read_text(encoding='utf-8')
for token in ['MirrorRabbitFormId = "mirror_rabbit"','TrinityRabbitFormId = "trinity_rabbit"','ResonanceRabbitFormId = "resonance_rabbit"',
              'ResolvePreferredFormId()','MilestoneBossService.MirrorArchiveBossCardId','MilestoneBossService.TricolorBossCardId',
              'MilestoneBossService.MimiBossCardId','BossFormDurationMs = 10000','GuardianRootPulseDamage = 14','GuardianRootPulseIntervalMs = 2000']:
    assert token in forms, token

expected_roles = {
    'boss2_hollow_curator_arena.tmx': 'boss2|hollow-curator|library-of-forgotten-cards',
    'boss3_tricolor_resonance_arena.tmx': 'boss3|tricolor-resonance|three-aspects-one-core',
    'boss4_mimi_resonance_arena.tmx': 'boss4|mimi|resonance-master|final-boss',
}
for filename, role in expected_roles.items():
    p = root/'assets'/filename
    mr = ET.parse(p).getroot()
    props = {x.attrib.get('name'): x.attrib.get('value') for x in mr.find('properties').findall('property')}
    assert props.get('CardchaRegionRole') == role, (filename, props.get('CardchaRegionRole'))
    assert props.get('CardchaRegionVersion') == version

save = (root/'Services/SaveService.cs').read_text(encoding='utf-8')
assert 'CurrentSchemaVersion = 19' in save and 'CurrentSchemaVersion = 20' not in save
cards = json.loads((root/'assets/cards.json').read_text(encoding='utf-8'))
legacy = {'endless_hunt','fate_weaver','immortal_echo','worldbreaker'}
assert len(cards) == 80
assert len([c for c in cards if c.get('Id') not in legacy]) == 76

diff = subprocess.run(['git','diff','--quiet','origin/cardcha-alpha28-0670-remaining-boss-foundation','--','src/Cardcha/assets/mimi_walk.png'])
assert diff.returncode == 0, 'mimi_walk.png changed from 0670 baseline'

checked = 0
for tmx in sorted((root/'assets').rglob('*.tmx')):
    mr = ET.parse(tmx).getroot()
    for layer in mr.findall('layer'):
        data = layer.find('data')
        if data is None or data.attrib.get('encoding') != 'csv': continue
        vals = []
        for i, token in enumerate((data.text or '').split(',')):
            st = token.strip()
            assert st != '', f'{tmx}: empty CSV token {i}'
            n = int(st); assert 0 <= n <= 0xFFFFFFFF; vals.append(n)
        assert len(vals) == int(layer.attrib['width']) * int(layer.attrib['height']), tmx
        checked += 1
assert checked >= 30, checked
print(f'0671 validator PASS authoredPNGs={len(dims)} arenas=3 forms=4 schema=19 cards=76/80 strictTMX={checked}')
