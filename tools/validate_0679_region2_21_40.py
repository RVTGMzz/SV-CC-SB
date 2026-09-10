#!/usr/bin/env python3
from pathlib import Path
import json, xml.etree.ElementTree as ET
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'src'/'Cardcha'
V='0.3.0-alpha.28.0.4.14.4.5.12.47'

def need(cond,msg):
    if not cond: raise SystemExit('0679 VALIDATION FAIL: '+msg)

manifest=json.loads((SRC/'manifest.json').read_text(encoding='utf-8'))
need(manifest.get('Version')==V,'manifest version mismatch')
for rel in ['Cardcha.csproj','Directory.Build.targets','ModEntry.cs']:
    need(V in (SRC/rel).read_text(encoding='utf-8'),rel+' version mismatch')

# Airship must reuse existing Region II fare and generic external flight plumbing.
a=(SRC/'Services'/'AirshipFoundationService.cs').read_text(encoding='utf-8')
need('private const int Region2Fare = 250;' in a,'Region II fare 250 missing')
need('region is not (2 or 3 or 4)' in a,'external flight does not accept Region II')
need('BeginExternalRegionFlight' in a and 'StartExternalRegionReturnFlight' in a,'external flight plumbing missing')

# Region II progression service.
s=(SRC/'Services'/'RegionExpeditionService.cs').read_text(encoding='utf-8')
for token in [
    'ForgottenArchive = 2',
    'Region2LocationName = "Cardcha_Region2_ForgottenArchive"',
    'Region2MapAssetName = "Maps/Cardcha_Region2_ForgottenArchive"',
    'Region2BossGateTile = new(20, 4)',
    'BindRegion2BossGateHandler',
    'TryUseRegion2BossGate',
    'BossApproachMode',
    'DebugEnterRegion2BossApproach',
    'DebugBossGateBypassRegion2',
    'this.Save.Data.Region1BossDefeated && this.Save.Data.AirshipHighestRegionUnlocked >= 2',
    'role = "ink_moth"', 'role = "paper_scarab"', 'role = "dust_slime"', 'role = "archive_warden"',
    'hp = 390',
]:
    need(token in s,'Region II service contract missing: '+token)
need('ExpeditionRegion.ForgottenArchive => 3 + wave' in s,'Region II wave count contract missing')
need('ExpeditionRegion.ForgottenArchive => wave switch { 1 => 7, 2 => 11, _ => 16 }' in s,'Region II Scrap rewards changed')
need('ExpeditionRegion.ForgottenArchive => wave == 3 ? 1 : 0' in s,'Region II Shiny reward changed')
# Later regions must stay frozen.
need('ExpeditionRegion.Mirrorwild => wave switch { 1 => 10, 2 => 15, _ => 22 }' in s,'Region III rewards changed')
need('_ => wave switch { 1 => 15, 2 => 22, _ => 32 }' in s,'Region IV rewards changed')
need('private const int WaveCount = 3;' in s,'3-wave contract changed')

# Boss II now belongs to Region II: threshold route lands in Region II, north seal enters arena.
mb=(SRC/'Services'/'MilestoneBossService.cs').read_text(encoding='utf-8')
for token in [
    'public string EnterBoss2FromRegion2()',
    'RegionExpeditionService.Region2LocationName',
    'owned < 40',
    'MilestoneBossKind.HollowCurator && this.ExpeditionRouteAction is not null',
    'return this.ExpeditionRouteAction(owned, required, name);',
    'HollowCuratorMaxHealth = 2200',
    'MirrorArchiveBossCardId = "mirror_archive"',
]:
    need(token in mb,'Boss II Region II route contract missing: '+token)
need('return (MilestoneBossKind.HollowCurator, 40, "The Hollow Curator")' in mb,'Boss II 40-card threshold changed')

mod=(SRC/'ModEntry.cs').read_text(encoding='utf-8')
for token in [
    'BindRegion2BossGateHandler(this.MilestoneBosses.EnterBoss2FromRegion2)',
    '"cardcha_test_region2"',
    '"cardcha_test_region2_bossgate"',
    '"cardcha_test_boss2"',
    '0679 REGION II 21-40 + BOSS II APPROACH TEST',
]:
    need(token in mod,'ModEntry Region II wiring/test contract missing: '+token)

patch=(SRC/'Patches'/'RegionExpeditionProxyDrawPatch.cs').read_text(encoding='utf-8')
for token in [
    'Region2EnemyAtlasPath = "assets/region2_forgotten_archive_enemies.png"',
    'RegionExpeditionService.Region2LocationName',
    'ExpeditionRegion.ForgottenArchive',
    '"ink_moth" => 0', '"paper_scarab" => 1', '"dust_slime" => 2', '"archive_warden" => 3',
    'AccessTools.DeclaredMethod(typeof(Monster), "draw", new[] { typeof(SpriteBatch) })',
]:
    need(token in patch,'Region II actor-depth patch missing: '+token)
for bad in ['typeof(GreenSlime)', 'typeof(Bat)', 'typeof(Bug)']:
    need(bad not in patch,'expedition patch regressed to subclass Harmony target: '+bad)

# Region II authored assets.
with Image.open(SRC/'assets'/'region2_forgotten_archive_enemies.png') as im:
    need(im.size==(256,32),f'Region II enemy atlas size {im.size} != (256,32)')
with Image.open(SRC/'assets'/'region2_forgotten_archive_tiles.png') as im:
    need(im.size==(256,64),f'Region II tile atlas size {im.size} != (256,64)')

map_path=SRC/'assets'/'region2_forgotten_archive.tmx'
root=ET.parse(map_path).getroot()
need(int(root.attrib['width'])==40 and int(root.attrib['height'])==28,'Region II TMX must be 40x28')
props={p.attrib.get('name'):p.attrib.get('value','') for p in root.find('properties').findall('property')}
need('21-40-cards' in props.get('CardchaRegionRole',''),'Region II role property missing 21-40 band')
need('map-layer-physical-depth' in props.get('CardchaAssetPolicy',''),'Region II depth policy missing')
images=[ts.find('image').attrib.get('source') for ts in root.findall('tileset') if ts.find('image') is not None]
need('region2_forgotten_archive_tiles.png' in images,'Region II authored tileset missing')
layers={l.attrib.get('name'):l for l in root.findall('layer')}
for name in ['Back','CardchaGround','Buildings','Front']:
    need(name in layers,'Region II layer missing: '+name)
    d=layers[name].find('data')
    vals=[x.strip() for x in (d.text or '').replace('\n','').split(',') if x.strip()]
    need(len(vals)==40*28,f'Region II {name} CSV {len(vals)} != 1120')
ground_vals=[int(x.strip()) for x in (layers['CardchaGround'].find('data').text or '').replace('\n','').split(',') if x.strip()]
build_vals=[int(x.strip()) for x in (layers['Buildings'].find('data').text or '').replace('\n','').split(',') if x.strip()]
front_vals=[int(x.strip()) for x in (layers['Front'].find('data').text or '').replace('\n','').split(',') if x.strip()]
need(sum(v>=2001 for v in ground_vals)>=12,'Region II authored ground identity too sparse')
need(sum(v>=2001 for v in build_vals)>=15,'Region II physical archive decor/gate too sparse')
need(sum(v>=2001 for v in front_vals)>=6,'Region II Front-layer depth decor too sparse')

# Translation coverage.
for lang in ['default.json','vi.json']:
    data=json.loads((SRC/'i18n'/lang).read_text(encoding='utf-8'))
    for key in [
        'airship.expedition.region2','airship.region2.boss_approach','airship.region2.boss_gate.cards',
        'airship.region2.boss_gate.echoes','airship.region2.boss_gate.boss1','airship.region2.boss_gate.cleared',
        'airship.region2.boss_gate.location']:
        need(key in data,lang+' missing '+key)

# Frozen persistence/card contracts.
save=(SRC/'Services'/'SaveService.cs').read_text(encoding='utf-8')
need('19' in save,'save schema 19 token missing')
cards=json.loads((SRC/'assets'/'cards.json').read_text(encoding='utf-8'))
need(len(cards)==80,f'expected 80 source cards, got {len(cards)}')
ids={str(c.get('Id','')) for c in cards}
legacy={'endless_hunt','fate_weaver','immortal_echo','worldbreaker'}
need(len(ids)==80,'card IDs not unique')
need(legacy.issubset(ids),'legacy mythic IDs missing')
need(len(ids-legacy)==76,'normal-card contract not 76')

print('0679 validation PASS: Region II 21-40 progression, Boss II gate route, actor-depth art, TMX, rewards and frozen contracts intact.')
