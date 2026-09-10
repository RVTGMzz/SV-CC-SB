#!/usr/bin/env python3
from pathlib import Path
import json, xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'src'/'Cardcha'
V='0.3.0-alpha.28.0.4.14.4.5.12.48'

def need(cond,msg):
    if not cond:
        raise SystemExit('0680 VALIDATION FAIL: '+msg)

manifest=json.loads((SRC/'manifest.json').read_text(encoding='utf-8'))
need(manifest.get('Version')==V,'manifest version mismatch')
for rel in ['Cardcha.csproj','Directory.Build.targets','ModEntry.cs']:
    need(V in (SRC/rel).read_text(encoding='utf-8'),rel+' version mismatch')

# Dedicated Region II ownership. Region III/IV must remain on legacy expedition runtime.
r2=(SRC/'Services'/'Region2RoguelikeRunService.cs').read_text(encoding='utf-8')
for token in [
    'internal sealed class Region2RoguelikeRunService',
    'this.TargetNodes = 6 + random.Next(4)',
    'Region2NodeKind.Combat', 'Region2NodeKind.Ambush', 'Region2NodeKind.Elite',
    'Region2NodeKind.MirrorChoice', 'Region2NodeKind.ArchiveEvent', 'Region2NodeKind.Cache',
    'Region2NodeKind.Restoration', 'Region2NodeKind.CursedArchive',
    'Region2NodeKind.BossGate', 'Region2NodeKind.FinalCache',
    'nextNode >= 6',
    'this.CurrentNode == 3 || this.CurrentNode == 6',
    'this.RiskRecord', 'this.PrecisionRecord', 'this.PressureRecord',
    'this.RecoveryRecord', 'this.MirrorRecord',
    'SuspendLegacyRegion2RuntimeForRoguelike',
    'RegionExpeditionService.EnemyMarkerKey',
    'RegionExpeditionService.EnemyRoleKey',
    'this.Airship.StartExternalRegionReturnFlight()',
    'this.UnbankedScrap = 0;',
    'this.UnbankedShiny = 0;',
]:
    need(token in r2,'Region II roguelike token missing: '+token)
need('public void OnRenderedWorld' not in r2,'Region II roguelike must not own a RenderedWorld physical renderer')
need('6-9 nodes' in r2,'6-9 run-length contract missing')
need('2-3 maps' not in r2,'illustrative map count leaked into runtime contract')
need('airship.region2.rogue.extract_early' in r2,'early-extraction loss path missing')
need('airship.region2.rogue.extract_complete' in r2,'completed-run extraction path missing')

legacy=(SRC/'Services'/'RegionExpeditionService.cs').read_text(encoding='utf-8')
need('public void SuspendLegacyRegion2RuntimeForRoguelike()' in legacy,'legacy Region II suspension hook missing')
# Existing Region III/IV rewards remain frozen.
need('ExpeditionRegion.Mirrorwild => wave switch { 1 => 10, 2 => 15, _ => 22 }' in legacy,'Region III rewards changed')
need('_ => wave switch { 1 => 15, 2 => 22, _ => 32 }' in legacy,'Region IV rewards changed')

# Real progression and Boss II identity remain frozen.
a=(SRC/'Services'/'AirshipFoundationService.cs').read_text(encoding='utf-8')
need('private const int Region2Fare = 250;' in a,'Region II fare 250 changed')
need('region is not (2 or 3 or 4)' in a,'generic Airship external route no longer accepts Region II')
mb=(SRC/'Services'/'MilestoneBossService.cs').read_text(encoding='utf-8')
for token in [
    'public string EnterBoss2FromRegion2()',
    'HollowCuratorMaxHealth = 2200',
    'MirrorArchiveBossCardId = "mirror_archive"',
    'return (MilestoneBossKind.HollowCurator, 40, "The Hollow Curator")',
]:
    need(token in mb,'Boss II frozen contract missing: '+token)

mod=(SRC/'ModEntry.cs').read_text(encoding='utf-8')
for token in [
    'private Region2RoguelikeRunService Region2Rogue = null!;',
    'new Region2RoguelikeRunService(helper, this.Monitor, this.Save, this.Airship, this.RegionExpeditions)',
    'this.Region2Rogue.BindBossGateHandlers(this.MilestoneBosses.EnterBoss2FromRegion2',
    'GameLoop.UpdateTicked += this.Region2Rogue.OnUpdateTicked',
    'Player.Warped += this.Region2Rogue.OnWarped',
    'Input.ButtonPressed += this.Region2Rogue.OnButtonPressed',
    '"cardcha_region2_rogue_status"',
    'this.Region2Rogue.PrepareNormalDebugEntry()',
    'this.Region2Rogue.PrepareBossGateDebugEntry()',
    'this.Region2Rogue.IsActive ? this.Region2Rogue.DebugClearCurrentNode()',
    '0680 REGION II 6-9 NODE ROGUELIKE ROUTE TEST',
]:
    need(token in mod,'ModEntry 0680 wiring missing: '+token)

# Actor-depth art remains the only enemy visual path.
patch=(SRC/'Patches'/'RegionExpeditionProxyDrawPatch.cs').read_text(encoding='utf-8')
need('AccessTools.DeclaredMethod(typeof(Monster), "draw", new[] { typeof(SpriteBatch) })' in patch,'Monster.draw actor-depth patch missing')
need('Region2EnemyAtlasPath = "assets/region2_forgotten_archive_enemies.png"' in patch,'Region II authored atlas path missing')
for bad in ['typeof(GreenSlime)', 'typeof(Bat)', 'typeof(Bug)']:
    need(bad not in patch,'subclass Harmony draw regression: '+bad)

# Region II physical map remains strict TMX and the real north seal stays at the established map.
map_path=SRC/'assets'/'region2_forgotten_archive.tmx'
root=ET.parse(map_path).getroot()
need(int(root.attrib['width'])==40 and int(root.attrib['height'])==28,'Region II TMX changed from 40x28')
layers={l.attrib.get('name'):l for l in root.findall('layer')}
for name in ['Back','CardchaGround','Buildings','Front']:
    need(name in layers,'Region II layer missing: '+name)
    data=layers[name].find('data')
    vals=[x.strip() for x in (data.text or '').replace('\n','').split(',') if x.strip()]
    need(len(vals)==1120,f'Region II {name} CSV {len(vals)} != 1120')

# i18n coverage in both languages.
required_keys=[
'airship.region2.rogue.start','airship.region2.rogue.node','airship.region2.rogue.choose',
'airship.region2.rogue.kind.combat','airship.region2.rogue.kind.elite','airship.region2.rogue.kind.mirror',
'airship.region2.rogue.kind.cursed','airship.region2.rogue.kind.bossgate',
'airship.region2.rogue.checkpoint','airship.region2.rogue.extract_early',
'airship.region2.rogue.bossgate_ready','airship.region2.rogue.record.risk',
'airship.region2.rogue.record.precision','airship.region2.rogue.record.mirror'
]
for lang in ['default.json','vi.json']:
    data=json.loads((SRC/'i18n'/lang).read_text(encoding='utf-8'))
    for key in required_keys:
        need(key in data,lang+' missing '+key)

# Design intent is documented, and the old 4-7 tuning target is gone.
doc=(ROOT/'handoff'/'REGION2_ROGUELIKE_DESIGN_DIRECTION.md').read_text(encoding='utf-8')
need('6–9 short nodes' in doc,'design doc not updated to 6-9')
need('4–7 short nodes' not in doc,'old 4-7 tuning target still present')
need('not a literal feature checklist' in doc,'critical-design-judgment instruction missing')
need('Do not blindly implement a user example' in doc,'design reflection rule missing')

# Persistence and card registry stay frozen.
save=(SRC/'Services'/'SaveService.cs').read_text(encoding='utf-8')
need('19' in save,'save schema 19 token missing')
cards=json.loads((SRC/'assets'/'cards.json').read_text(encoding='utf-8'))
need(len(cards)==80,f'expected 80 source cards, got {len(cards)}')
ids={str(c.get('Id','')) for c in cards}
legacy_mythics={'endless_hunt','fate_weaver','immortal_echo','worldbreaker'}
need(len(ids)==80,'card IDs not unique')
need(legacy_mythics.issubset(ids),'legacy mythic IDs missing')
need(len(ids-legacy_mythics)==76,'normal card contract not 76')

print('0680 validation PASS: Region II is a 6-9 node branching roguelike runtime; Boss II/progression/depth/frozen contracts intact.')
