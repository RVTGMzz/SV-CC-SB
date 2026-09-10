#!/usr/bin/env python3
from pathlib import Path
import json
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'src'/'Cardcha'
V='0.3.0-alpha.28.0.4.14.4.5.12.49'

def need(cond,msg):
    if not cond:
        raise SystemExit('0681 VALIDATION FAIL: '+msg)

manifest=json.loads((SRC/'manifest.json').read_text(encoding='utf-8'))
need(manifest.get('Version')==V,'manifest version mismatch')
for rel in ['Cardcha.csproj','Directory.Build.targets','ModEntry.cs']:
    need(V in (SRC/rel).read_text(encoding='utf-8'),rel+' version mismatch')

# 0680 route length and identity must stay intact.
r2=(SRC/'Services'/'Region2RoguelikeRunService.cs').read_text(encoding='utf-8')
for token in [
    'this.TargetNodes = 6 + random.Next(4)',
    'Region2NodeKind.MirrorChoice','Region2NodeKind.CursedArchive','Region2NodeKind.BossGate',
    'this.CurrentNode == 3 || this.CurrentNode == 6',
    'BindCuratorRecordSink(Action<CuratorRunRecord> sink)',
    'CuratorRunRecord record = this.BuildCuratorRunRecord(debug)',
    'this.CuratorRecordSink?.Invoke(record)',
    'this.RiskRecord','this.PrecisionRecord','this.PressureRecord','this.RecoveryRecord','this.MirrorRecord',
]:
    need(token in r2,'Region II record/route contract missing: '+token)
need('6-9 nodes' in r2,'6-9 node target missing')

record=(SRC/'Services'/'CuratorRunRecord.cs').read_text(encoding='utf-8')
for token in [
    'internal sealed class CuratorRunRecord',
    'public string Tag { get; }',
    'public int Risk { get; }','public int Precision { get; }','public int Pressure { get; }',
    'public int Recovery { get; }','public int Mirror { get; }','public int NodesReached { get; }',
    'public static CuratorRunRecord Debug(string? tag)',
]:
    need(token in record,'CuratorRunRecord contract missing: '+token)

boss=(SRC/'Services'/'MilestoneBossService.cs').read_text(encoding='utf-8')
for token in [
    'SetNextHollowCuratorRecord(CuratorRunRecord record)',
    'DebugEnterBoss2WithRecord(string? tag)',
    'ActiveCuratorRecord = this.HasPendingCuratorRecord ? this.PendingCuratorRecord : CuratorRunRecord.Neutral',
    'int recordAttack = this.CuratorRecordAttackId()',
    '"risk" => 5','"precision" => 6','"pressure" => 7','"recovery" => 8','"mirror" => 9',
    'case 5:', 'case 6:', 'case 7:', 'case 8:', 'case 9:',
    'boss.curator.record.reveal',
    'private int CuratorAnimationFamily()',
    'int frame = family * 2 + anim',
    'source = new Rectangle(frame * 48, 0, 48, 64)',
    'HollowCuratorMaxHealth = 2200',
    'MirrorArchiveBossCardId = "mirror_archive"',
]:
    need(token in boss,'Hollow Curator 0681 contract missing: '+token)
# Adaptation is a bias, not a replacement: original attacks remain in phase pools.
need('2 => new[] { 0, 1, 2, 4, recordAttack, recordAttack }' in boss,'phase 2 mixed attack pool changed')
need('_ => new[] { 0, 2, 3, 4, recordAttack, recordAttack, recordAttack }' in boss,'phase 3 mixed attack pool changed')
need('Math.Min(3, this.CuratorAdaptationStacks + 1)' in boss,'Curator adaptation cap changed')
# Recovery reflection must not disable player healing.
for forbidden in ['Game1.player.canMove = false','Game1.player.health = Math.Min(Game1.player.health','healingDisabled','disableHealing']:
    need(forbidden not in boss,'hard-counter/healing-disable regression: '+forbidden)

mod=(SRC/'ModEntry.cs').read_text(encoding='utf-8')
for token in [
    'this.Region2Rogue.BindCuratorRecordSink(this.MilestoneBosses.SetNextHollowCuratorRecord)',
    '"cardcha_test_boss2_record"',
    'this.MilestoneBosses.DebugEnterBoss2WithRecord(args.FirstOrDefault())',
    '0681 HOLLOW CURATOR RECORDS YOU TEST',
]:
    need(token in mod,'ModEntry 0681 wiring missing: '+token)

# Hollow Curator now has 18 native 48x64 frames; no world sprite blow-up was introduced.
with Image.open(SRC/'assets'/'bosses'/'milestone'/'hollow_curator.png') as im:
    need(im.size==(864,64),f'Hollow Curator atlas {im.size} != (864,64)')
need('scale = 1.95f;' in boss,'Hollow Curator accepted world scale changed')
need('DrawActorAtMonsterDepth' in boss,'actor-depth boss renderer missing')
rendered=boss[boss.find('public void OnRenderedWorld'):boss.find('public void OnRenderedHud')]
need('DrawActorAtMonsterDepth' not in rendered,'physical boss body regressed into RenderedWorld')

# i18n coverage in EN + VI.
keys=[
'boss.curator.record.reveal',
'boss.curator.record.short.neutral','boss.curator.record.short.risk','boss.curator.record.short.precision',
'boss.curator.record.short.pressure','boss.curator.record.short.recovery','boss.curator.record.short.mirror'
]
for lang in ['default.json','vi.json']:
    data=json.loads((SRC/'i18n'/lang).read_text(encoding='utf-8'))
    for key in keys:
        need(key in data,lang+' missing '+key)

# Boss II remains the 40-card Region II milestone.
need('return (MilestoneBossKind.HollowCurator, 40, "The Hollow Curator")' in boss,'Boss II 40-card milestone changed')
a=(SRC/'Services'/'AirshipFoundationService.cs').read_text(encoding='utf-8')
need('private const int Region2Fare = 250;' in a,'Region II fare changed')

# Persistence/card contracts remain frozen.
save=(SRC/'Services'/'SaveService.cs').read_text(encoding='utf-8')
need('19' in save,'save schema 19 token missing')
cards=json.loads((SRC/'assets'/'cards.json').read_text(encoding='utf-8'))
need(len(cards)==80,f'expected 80 source cards, got {len(cards)}')
ids={str(c.get('Id','')) for c in cards}
legacy={'endless_hunt','fate_weaver','immortal_echo','worldbreaker'}
need(len(ids)==80,'card IDs not unique')
need(legacy.issubset(ids),'legacy mythics missing')
need(len(ids-legacy)==76,'normal card count not 76')

# Documentation must preserve critical-design judgment, not turn examples into literal checklists.
doc=(ROOT/'handoff'/'REGION2_ROGUELIKE_DESIGN_DIRECTION.md').read_text(encoding='utf-8')
need('6–9 short nodes' in doc,'design doc lost 6-9 direction')
need('Do not blindly implement a user example' in doc,'critical design judgment rule missing')
need('0681 implementation note' in doc,'0681 design trail missing')

print('0681 validation PASS: real run-record transfer, fair adaptive Hollow Curator attacks, 18-frame actor-depth visual auth, 6-9 route and frozen contracts intact.')
