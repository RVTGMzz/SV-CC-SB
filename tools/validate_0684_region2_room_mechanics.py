#!/usr/bin/env python3
from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src' / 'Cardcha'
V = '0.3.0-alpha.28.0.4.14.4.5.12.52'


def need(cond, msg):
    if not cond:
        raise SystemExit('0684 VALIDATION FAIL: ' + msg)

manifest = json.loads((SRC/'manifest.json').read_text(encoding='utf-8'))
need(manifest.get('Version') == V, 'manifest version mismatch')
for rel in ['Cardcha.csproj', 'Directory.Build.targets', 'ModEntry.cs']:
    need(V in (SRC/rel).read_text(encoding='utf-8'), rel + ' version mismatch')

r2 = (SRC/'Services'/'Region2RoguelikeRunService.cs').read_text(encoding='utf-8')
for token in [
    'RoomMechanicMarkerKey = "Ronvotri.Cardcha/0684RoomMechanic"',
    'MirrorTelegraphMs = 1050L',
    'InkTelegraphMs = 900L',
    'VaultTelegraphMs = 950L',
    'private string ActiveRoomMechanic = "none";',
    'private void ArmRoomMechanicForCombat(GameLocation location)',
    'private void UpdateRoomMechanic(GameLocation location)',
    'private bool TryArmRoomMechanicTelegraph(GameLocation location, long now)',
    'private void ResolveRoomMechanicHit()',
    'private static void DrawHazardOutline(SpriteBatch batch, Point tile, Color color)',
    '"mirror_trace"', '"ink_sweep"', '"warden_seal"',
    'Region2RoomKind.MirrorGallery => "mirror_trace"',
    'Region2RoomKind.InkboundStacks => "ink_sweep"',
    'Region2RoomKind.WardenVault when this.CurrentKind == Region2NodeKind.Elite => "warden_seal"',
    'Game1.player.takeDamage(damage, false, null);',
    'this.TargetNodes = 6 + random.Next(4)',
    'this.CurrentNode == 3 || this.CurrentNode == 6',
    'InteractionMarkerKey = "Ronvotri.Cardcha/0683Region2Interaction"',
    'this.ArmRoomMechanicForCombat(location);',
]:
    need(token in r2, 'room mechanic/runtime contract missing: ' + token)

need('return $"0684 Region II Rogue:' in r2, '0684 status banner missing')
need('public string DescribeRoomMechanic()' in r2, 'mechanic diagnostics missing')
need('this.CurrentRoom == Region2RoomKind.WardenVault && (gateClose || gateFacing)' in r2, 'Warden Vault boss gate scope regressed')

# Vestibule is deliberately the no-extra-hazard room.
arm_start = r2.index('private void ArmRoomMechanicForCombat')
arm_end = r2.index('private void UpdateRoomMechanic', arm_start)
arm = r2[arm_start:arm_end]
need('Region2RoomKind.Vestibule' not in arm, 'Vestibule should remain lower-pressure without a repeating mechanic')
need('_ => "none"' in arm, 'no-mechanic fallback missing')

# Transient world renderer may only draw thin telegraph outlines, never physical Cardcha objects.
rw_start = r2.index('public void OnRenderedWorld')
rw_end = r2.index('public void OnButtonPressed', rw_start)
rw = r2[rw_start:rw_end]
for banned in ['Chest', 'Furniture', 'Texture2D', 'DrawString', 'room.setObject', 'StaticTile', 'Game1.objectSpriteSheet']:
    need(banned not in rw, 'physical/world-label content leaked into RoomMechanic RenderedWorld: ' + banned)
need('DrawHazardOutline' in rw and 'RoomMechanicTiles' in rw, 'hazard telegraph draw missing')

# Cursed Archive must still sleep until the physical tome is activated, then arm Inkbound mechanics.
resolve_start = r2.index('private void ResolveRoomInteraction')
resolve_end = r2.index('private string DebugResolveRoomInteraction', resolve_start)
resolve = r2[resolve_start:resolve_end]
need('if (kind == Region2NodeKind.CursedArchive)' in resolve, 'Cursed Archive activation branch missing')
need('this.SpawnNodeEnemies(location, kind);' in resolve, 'Cursed Archive no longer wakes combat')
need('this.ArmRoomMechanicForCombat(location);' in resolve, 'Cursed Archive does not arm room mechanic after activation')

# 0683 route-end bug fix: Final Cache must never auto-award from CompleteCurrentNode.
complete_start = r2.index('private void CompleteCurrentNode')
complete_end = r2.index('private void PrepareRouteChoice', complete_start)
complete = r2[complete_start:complete_end]
need('this.BeginNode(location, Region2NodeKind.FinalCache);' in complete, 'route-end Final Cache is not routed to physical interaction')
need('this.AwardNode(Region2NodeKind.FinalCache);' not in complete, 'route-end Final Cache still auto-awards reward')

# ModEntry must wire only the VFX renderer and expose diagnostics.
mod = (SRC/'ModEntry.cs').read_text(encoding='utf-8')
need('helper.Events.Display.RenderedWorld += this.Region2Rogue.OnRenderedWorld;' in mod, 'Region2Rogue VFX RenderedWorld hook missing')
need('cardcha_region2_mechanic_status' in mod, 'mechanic status command missing')
need('0684 REGION II ROOM-SPECIFIC MECHANICS TEST' in mod, 'build label missing')

# Rendering audit must explicitly classify the new hook as VFX-only.
audit = json.loads((ROOT/'render_depth_audit.json').read_text(encoding='utf-8'))
need(audit.get('branch') == 'cardcha-alpha28-0684-region2-room-specific-mechanics', 'render-depth audit branch stale')
meta = audit.get('renderedWorldSubscribers', {}).get('Region2Rogue')
need(isinstance(meta, dict), 'Region2Rogue missing from render-depth audit')
need(meta.get('physicalAllowed') is False, 'Region2Rogue physicalAllowed must be false')
need('vfx-only' in str(meta.get('classification', '')), 'Region2Rogue audit classification is not VFX-only')

# EN/VI mechanic text must exist, with no world-space label requirement.
keys = [
    'airship.region2.mechanic.active',
    'airship.region2.mechanic.mirror_trace.name',
    'airship.region2.mechanic.ink_sweep.name',
    'airship.region2.mechanic.warden_seal.name',
]
for lang in ['default.json', 'vi.json']:
    data = json.loads((SRC/'i18n'/lang).read_text(encoding='utf-8'))
    for key in keys:
        need(key in data, lang + ' missing ' + key)

# The four physical rooms and 0683 station atlas stay structurally intact.
maps = [
    'region2_forgotten_archive.tmx',
    'region2_inkbound_stacks.tmx',
    'region2_mirror_gallery.tmx',
    'region2_warden_vault.tmx',
]
for name in maps:
    root = ET.parse(SRC/'assets'/name).getroot()
    need((int(root.attrib['width']), int(root.attrib['height'])) == (40, 28), name + ' dimensions changed')
    for layer in root.findall('layer'):
        vals = [x.strip() for x in (layer.find('data').text or '').split(',') if x.strip()]
        need(len(vals) == 1120, f'{name}:{layer.attrib.get("name")} CSV count {len(vals)} != 1120')
    ts = next((x for x in root.findall('tileset') if x.attrib.get('name') == 'cardcha_region2_interactions'), None)
    need(ts is not None, name + ' lost 0683 interaction tileset')

# Frozen progression/economy/boss/save/card contracts.
airship = (SRC/'Services'/'AirshipFoundationService.cs').read_text(encoding='utf-8')
need('private const int Region2Fare = 250;' in airship, 'Region II fare changed')
boss = (SRC/'Services'/'MilestoneBossService.cs').read_text(encoding='utf-8')
need('HollowCuratorMaxHealth = 2200' in boss, 'Boss II HP changed')
need('return (MilestoneBossKind.HollowCurator, 40, "The Hollow Curator")' in boss, '40-card milestone changed')
need('SetNextHollowCuratorRecord(CuratorRunRecord record)' in boss, 'Curator Records You regressed')
save = (SRC/'Services'/'SaveService.cs').read_text(encoding='utf-8')
need('19' in save, 'save schema 19 token missing')
cards = json.loads((SRC/'assets'/'cards.json').read_text(encoding='utf-8'))
legacy = {'endless_hunt', 'fate_weaver', 'immortal_echo', 'worldbreaker'}
ids = {str(c.get('Id', '')) for c in cards}
need(len(cards) == 80 and len(ids) == 80 and legacy.issubset(ids) and len(ids - legacy) == 76, '80/76 card audit changed')

# Documentation trail must be current.
latest = (ROOT/'handoff'/'LATEST_CARDCHA_HANDOFF.md').read_text(encoding='utf-8')
need('0684' in latest and V in latest, 'LATEST handoff not advanced to 0684')
need((ROOT/'handoff'/'ALPHA28_0684_REGION2_ROOM_SPECIFIC_MECHANICS.md').exists(), '0684 handoff missing')
design = (ROOT/'handoff'/'REGION2_ROGUELIKE_DESIGN_DIRECTION.md').read_text(encoding='utf-8')
need('### 0684 implementation note' in design, '0684 design note missing')
need('6–9 short nodes' in design, '6-9 route design lost')

print('0684 validation PASS: room-specific tactics, VFX-only telegraphs, physical Final Cache, 6-9 route, Curator, depth, progression and 80/76 contracts intact.')
