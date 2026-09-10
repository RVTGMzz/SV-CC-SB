#!/usr/bin/env python3
from pathlib import Path
import json, xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'src'/'Cardcha'
V='0.3.0-alpha.28.0.4.14.4.5.12.50'

def need(cond,msg):
    if not cond:
        raise SystemExit('0682 VALIDATION FAIL: '+msg)

manifest=json.loads((SRC/'manifest.json').read_text(encoding='utf-8'))
need(manifest.get('Version')==V,'manifest version mismatch')
for rel in ['Cardcha.csproj','Directory.Build.targets','ModEntry.cs']:
    need(V in (SRC/rel).read_text(encoding='utf-8'),rel+' version mismatch')

r2=(SRC/'Services'/'Region2RoguelikeRunService.cs').read_text(encoding='utf-8')
for token in [
    'internal enum Region2RoomKind',
    'InkboundStacks','MirrorGallery','WardenVault',
    'Cardcha_Region2_InkboundStacks','Cardcha_Region2_MirrorGallery','Cardcha_Region2_WardenVault',
    'PendingInternalRoomWarp','BeginNodeHere','ResolveRoomForNode','SpawnCandidatesForRoom',
    'if (incoming && outgoing)',
    'this.TargetNodes = 6 + random.Next(4)',
    'this.CurrentNode == 3 || this.CurrentNode == 6',
    'BindCuratorRecordSink(Action<CuratorRunRecord> sink)',
    'this.CuratorRecordSink?.Invoke(record)',
]:
    need(token in r2,'Region II multi-room contract missing: '+token)
need('Game1.warpFarmer(target.NameOrUniqueName, arrival.X, arrival.Y, 0)' in r2,'internal room warp missing')
need('this.ClearRunEnemies(e.OldLocation)' in r2,'old-room enemy cleanup missing')
need('this.ResetRuntime(clearEnemies: false)' in r2,'outside-region reset behavior missing')
need('runLength=6-9 nodes' in r2,'6-9 node status contract missing')

mod=(SRC/'ModEntry.cs').read_text(encoding='utf-8')
need('helper.Events.Content.AssetRequested += this.Region2Rogue.OnAssetRequested;' in mod,'Region2Rogue asset event not wired')
need('0682 REGION II MULTI-ROOM ROGUELIKE TEST' in mod,'0682 build label missing')

boss=(SRC/'Services'/'MilestoneBossService.cs').read_text(encoding='utf-8')
need('Region2RoguelikeRunService.IsRegion2(Game1.currentLocation)' in boss,'Boss II entry does not accept all Region II rooms')
for token in ['HollowCuratorMaxHealth = 2200','MirrorArchiveBossCardId = "mirror_archive"','CuratorRunRecord']:
    need(token in boss,'Boss II/Curator contract changed: '+token)
need('return (MilestoneBossKind.HollowCurator, 40, "The Hollow Curator")' in boss,'Boss II 40-card milestone changed')

# New TMX room files: strict 40x28 and 4 complete CSV layers.
rooms={
    'region2_inkbound_stacks.tmx':'inkbound-stacks',
    'region2_mirror_gallery.tmx':'mirror-gallery',
    'region2_warden_vault.tmx':'warden-vault',
}
for rel,role in rooms.items():
    p=SRC/'assets'/rel
    need(p.exists(),rel+' missing')
    root=ET.parse(p).getroot()
    need((int(root.attrib['width']),int(root.attrib['height']))==(40,28),rel+' dimensions changed')
    props={x.attrib.get('name'):x.attrib.get('value','') for x in root.find('properties').findall('property')}
    need(props.get('CardchaRegionVersion')==V,rel+' version property mismatch')
    need(role in props.get('CardchaRegionRole',''),rel+' room role missing')
    need('map-layer-physical-depth' in props.get('CardchaAssetPolicy',''),rel+' depth policy missing')
    layers={x.attrib.get('name'):x for x in root.findall('layer')}
    for lname in ['Back','CardchaGround','Buildings','Front']:
        need(lname in layers,rel+' missing '+lname)
        data=layers[lname].find('data')
        vals=[x.strip() for x in (data.text or '').replace('\n','').split(',') if x.strip()]
        need(len(vals)==1120,f'{rel} {lname} has {len(vals)} cells, expected 1120')
    images=[x.attrib.get('source','') for ts in root.findall('tileset') for x in ts.findall('image')]
    need('region2_forgotten_archive_tiles.png' in images,rel+' does not reuse accepted Region II atlas')

# Warden Vault must contain the accepted 3x2 Archive Seal at north center.
root=ET.parse(SRC/'assets'/'region2_warden_vault.tmx').getroot()
build=next(x for x in root.findall('layer') if x.attrib.get('name')=='Buildings').find('data')
vals=[int(x.strip()) for x in (build.text or '').replace('\n','').split(',') if x.strip()]
def tile(x,y): return vals[y*40+x]
need([tile(x,3) for x in (19,20,21)]==[2020,2021,2022],'Warden Vault top seal row misassembled')
need([tile(x,4) for x in (19,20,21)]==[2023,2024,2025],'Warden Vault bottom seal row misassembled')

# Existing Region II base map + later region/boss assets should remain compatible.
need((SRC/'assets'/'region2_forgotten_archive.tmx').exists(),'base Archive Vestibule map missing')
need((SRC/'assets'/'region2_forgotten_archive_enemies.png').exists(),'Region II enemy atlas missing')
need((SRC/'assets'/'bosses'/'milestone'/'hollow_curator.png').exists(),'Hollow Curator atlas missing')

# Fare/save/card contracts.
a=(SRC/'Services'/'AirshipFoundationService.cs').read_text(encoding='utf-8')
need('private const int Region2Fare = 250;' in a,'Region II fare changed')
save=(SRC/'Services'/'SaveService.cs').read_text(encoding='utf-8')
need('19' in save,'save schema 19 token missing')
cards=json.loads((SRC/'assets'/'cards.json').read_text(encoding='utf-8'))
need(len(cards)==80,f'expected 80 source cards, got {len(cards)}')
ids={str(c.get('Id','')) for c in cards}
legacy={'endless_hunt','fate_weaver','immortal_echo','worldbreaker'}
need(len(ids)==80,'card IDs not unique')
need(legacy.issubset(ids),'legacy mythics missing')
need(len(ids-legacy)==76,'normal card count not 76')

# No new physical RenderedWorld owner in Region II service.
need('RenderedWorldEventArgs' not in r2,'Region II physical room rendering regressed into RenderedWorld')

# Handoff trail.
latest=(ROOT/'handoff'/'LATEST_CARDCHA_HANDOFF.md').read_text(encoding='utf-8')
need('cardcha-alpha28-0682-region2-multiroom-roguelike' in latest,'latest handoff branch mismatch')
need(V in latest,'latest handoff build mismatch')
need((ROOT/'handoff'/'ALPHA28_0682_REGION2_MULTIROOM_ROGUELIKE.md').exists(),'0682 handoff missing')

print('0682 validation PASS: 4-room Region II route, strict TMX, internal warp continuity, Curator integration and frozen contracts intact.')
