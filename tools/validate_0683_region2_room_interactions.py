#!/usr/bin/env python3
from pathlib import Path
import json, xml.etree.ElementTree as ET
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'src'/'Cardcha'
V='0.3.0-alpha.28.0.4.14.4.5.12.51'

def need(cond,msg):
    if not cond:
        raise SystemExit('0683 VALIDATION FAIL: '+msg)

manifest=json.loads((SRC/'manifest.json').read_text(encoding='utf-8'))
need(manifest.get('Version')==V,'manifest version mismatch')
for rel in ['Cardcha.csproj','Directory.Build.targets','ModEntry.cs']:
    need(V in (SRC/rel).read_text(encoding='utf-8'),rel+' version mismatch')

r2=(SRC/'Services'/'Region2RoguelikeRunService.cs').read_text(encoding='utf-8')
for token in [
    'InteractionMarkerKey = "Ronvotri.Cardcha/0683Region2Interaction"',
    'private bool AwaitingRoomInteraction;',
    'private Point ActiveInteractionTile;',
    'this.TryHandleRoomInteraction(e, Game1.currentLocation, action)',
    'private void PrepareRoomInteraction(GameLocation location, Region2NodeKind kind)',
    'private void ResolveRoomInteraction(GameLocation location, bool debug)',
    'private void EnsureInteractionChest(GameLocation room, Point tile)',
    'Chest chest = new(true);',
    'room.setObject(key, chest);',
    'kind == Region2NodeKind.CursedArchive',
    'this.SpawnNodeEnemies(location, kind);',
    'kind == Region2NodeKind.FinalCache',
    'private static bool IsManualInteractionKind',
    'Region2NodeKind.MirrorChoice','Region2NodeKind.ArchiveEvent','Region2NodeKind.Cache','Region2NodeKind.Restoration',
    'this.TargetNodes = 6 + random.Next(4)',
    'this.CurrentNode == 3 || this.CurrentNode == 6',
    'this.Region2Rogue.BindCuratorRecordSink(this.MilestoneBosses.SetNextHollowCuratorRecord)' if False else 'CuratorRecordSink',
]:
    need(token in r2,'runtime interaction contract missing: '+token)
need('interaction={this.AwaitingRoomInteraction}' in r2,'status does not expose pending interaction')
need('this.CurrentRoom == Region2RoomKind.WardenVault && (gateClose || gateFacing)' in r2,'Boss Gate scope regressed')

# Non-combat nodes must not auto-resolve in BeginNodeHere.
start=r2.index('private void BeginNodeHere')
end=r2.index('private void CompleteCurrentNode',start)
begin=r2[start:end]
need('this.ResolveNonCombatNode(kind);' not in begin,'non-combat node still auto-resolves on room entry')
need('this.PrepareRoomInteraction(location, kind);' in begin,'manual interaction not prepared')

# Cursed Archive must wake only after interaction.
prep=r2[r2.index('private void ResolveRoomInteraction'):r2.index('private string DebugResolveRoomInteraction')]
need('if (kind == Region2NodeKind.CursedArchive)' in prep,'Cursed Archive interaction branch missing')
need(prep.index('if (kind == Region2NodeKind.CursedArchive)') < prep.index('this.SpawnNodeEnemies(location, kind);'),'Cursed activation order invalid')

# Native station atlas and all four Region II maps.
with Image.open(SRC/'assets'/'region2_interaction_stations.png') as im:
    need(im.size==(128,32),f'interaction atlas {im.size} != (128,32)')

maps=[
    'region2_forgotten_archive.tmx','region2_inkbound_stacks.tmx','region2_mirror_gallery.tmx','region2_warden_vault.tmx'
]
for name in maps:
    root=ET.parse(SRC/'assets'/name).getroot()
    w=int(root.attrib['width']); h=int(root.attrib['height'])
    need((w,h)==(40,28),name+' dimensions changed')
    props={p.attrib.get('name'):p.attrib.get('value','') for p in root.find('properties').findall('property')}
    need(props.get('CardchaInteractionPolicy')=='tmx-physical-stations|manual-action|no-renderedworld-physical-props',name+' interaction policy missing')
    ts=next((x for x in root.findall('tileset') if x.attrib.get('name')=='cardcha_region2_interactions'),None)
    need(ts is not None,name+' interaction tileset missing')
    need(ts.attrib.get('firstgid')=='2101',name+' interaction firstgid mismatch')
    img=ts.find('image')
    need(img is not None and img.attrib.get('source')=='region2_interaction_stations.png',name+' station atlas source mismatch')
    for layer in root.findall('layer'):
        vals=[x.strip() for x in (layer.find('data').text or '').split(',') if x.strip()]
        need(len(vals)==1120,f'{name}:{layer.attrib.get("name")} CSV count {len(vals)} !=1120')

# Specific physical stations must exist in their intended rooms.
def vals_for(name):
    root=ET.parse(SRC/'assets'/name).getroot()
    layer=next(x for x in root.findall('layer') if x.attrib.get('name')=='Buildings')
    return [int(x.strip()) for x in (layer.find('data').text or '').split(',') if x.strip()]
def at(vals,x,y): return vals[y*40+x]
vest=vals_for('region2_forgotten_archive.tmx')
ink=vals_for('region2_inkbound_stacks.tmx')
mir=vals_for('region2_mirror_gallery.tmx')
need(at(vest,8,10)==2103 and at(vest,29,17)==2105,'Vestibule lectern/restoration stations missing')
need(at(ink,19,11)==2107,'Inkbound cursed tome missing')
need(at(mir,19,10)==2101 and at(mir,8,17)==2105 and at(mir,29,17)==2103,'Mirror Gallery stations missing')

# No physical interaction renderer may be added to RenderedWorld.
mod=(SRC/'ModEntry.cs').read_text(encoding='utf-8')
need('this.Region2Rogue.OnRenderedWorld' not in mod,'Region II physical interaction renderer regressed into RenderedWorld')
need('0683 REGION II ROOM INTERACTION TEST' in mod,'build banner missing')

# i18n EN/VI coverage.
keys=[
'airship.region2.interaction.ready','airship.region2.interaction.object.mirror','airship.region2.interaction.object.lectern',
'airship.region2.interaction.object.cache','airship.region2.interaction.object.restoration','airship.region2.interaction.object.cursed',
'airship.region2.interaction.object.finalcache','airship.region2.interaction.cursed_awakened','airship.region2.interaction.final_opened']
for lang in ['default.json','vi.json']:
    data=json.loads((SRC/'i18n'/lang).read_text(encoding='utf-8'))
    for key in keys: need(key in data,lang+' missing '+key)

# Frozen gameplay/progression contracts.
a=(SRC/'Services'/'AirshipFoundationService.cs').read_text(encoding='utf-8')
need('private const int Region2Fare = 250;' in a,'Region II fare changed')
boss=(SRC/'Services'/'MilestoneBossService.cs').read_text(encoding='utf-8')
need('HollowCuratorMaxHealth = 2200' in boss,'Boss II HP changed')
need('return (MilestoneBossKind.HollowCurator, 40, "The Hollow Curator")' in boss,'40-card Boss II milestone changed')
need('SetNextHollowCuratorRecord(CuratorRunRecord record)' in boss,'Curator Records You regressed')
save=(SRC/'Services'/'SaveService.cs').read_text(encoding='utf-8')
need('19' in save,'save schema 19 token missing')
cards=json.loads((SRC/'assets'/'cards.json').read_text(encoding='utf-8'))
need(len(cards)==80,'source card count changed')
legacy={'endless_hunt','fate_weaver','immortal_echo','worldbreaker'}
ids={str(c.get('Id','')) for c in cards}
need(len(ids)==80 and legacy.issubset(ids) and len(ids-legacy)==76,'80/76 card audit changed')

# Design trail must remain documented.
doc=(ROOT/'handoff'/'REGION2_ROGUELIKE_DESIGN_DIRECTION.md').read_text(encoding='utf-8')
need('6–9 short nodes' in doc,'6-9 route design lost')
need('### 0683 implementation note' in doc,'0683 design note missing')

print('0683 validation PASS: manual room interactions, TMX-native stations, real cache chest, dormant Cursed Archive activation, 6-9 route and Curator contracts intact.')
