#!/usr/bin/env python3
from pathlib import Path
import json, re, xml.etree.ElementTree as ET

OLD='0.3.0-alpha.28.0.4.14.4.5.12.49'
NEW='0.3.0-alpha.28.0.4.14.4.5.12.50'
ROOT=Path('src/Cardcha')


def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f'0682 anchor missing: {label}')
    return text.replace(old, new, 1)

# ---------- build three additional Region II room maps from the accepted Region II atlas ----------
base_path=ROOT/'assets/region2_forgotten_archive.tmx'
base=ET.parse(base_path)
base_root=base.getroot()
W=int(base_root.attrib['width']); H=int(base_root.attrib['height'])
assert (W,H)==(40,28)

def blank(fill=0): return [fill]*(W*H)
def idx(x,y): return y*W+x
def setv(a,x,y,v):
    if 0 <= x < W and 0 <= y < H: a[idx(x,y)] = v

def rect(a,x0,y0,x1,y1,v):
    for y in range(y0,y1+1):
        for x in range(x0,x1+1): setv(a,x,y,v)

def border(build):
    for x in range(W): setv(build,x,0,381); setv(build,x,H-1,381)
    for y in range(H): setv(build,0,y,381); setv(build,W-1,y,381)

GRASS=381; PATH=457; DIRT=382
MOTIFS=[2001,2002,2003,2004,2005,2006,2007,2008]

def layer_data(root,name):
    layer=next(x for x in root.findall('layer') if x.attrib.get('name')==name)
    return layer.find('data')

def apply_layers(root, back, ground, buildings, front):
    for name,data in [('Back',back),('CardchaGround',ground),('Buildings',buildings),('Front',front)]:
        node=layer_data(root,name)
        rows=[]
        for y in range(H): rows.append(','.join(str(v) for v in data[y*W:(y+1)*W]) + ',')
        node.text='\n'+'\n'.join(rows)+'\n'

def make_common_back():
    a=blank(GRASS)
    centers=[20,20,19,19,20,21,21,20,19,18,18,19,20,21,22,22,21,20,19,19,20,21,21,20,20,20,20,20]
    for y,c in enumerate(centers):
        for x in range(max(1,c-2),min(W-1,c+3)): setv(a,x,y,PATH)
    return a

def room_xml(role, back, ground, buildings, front, outfile):
    root=ET.fromstring(ET.tostring(base_root, encoding='unicode'))
    props=root.find('properties')
    for p in props.findall('property'):
        if p.attrib.get('name')=='CardchaRegionVersion': p.set('value',NEW)
        if p.attrib.get('name')=='CardchaRegionRole': p.set('value',f'region2|forgotten-archive|{role}|21-40-cards|roguelike-room')
    apply_layers(root,back,ground,buildings,front)
    ET.ElementTree(root).write(outfile,encoding='utf-8',xml_declaration=True)

# Inkbound Stacks: shelf islands and narrow pockets while keeping a clean central route.
back=make_common_back(); ground=blank(); buildings=blank(); front=blank(); border(buildings)
for x,y,p in [(6,6,2026),(9,6,2027),(30,6,2026),(33,6,2027),(5,12,2030),(10,12,2031),(29,12,2030),(34,12,2031),
              (6,18,2033),(11,18,2034),(28,18,2033),(33,18,2034),(8,22,2035),(31,22,2035)]: setv(buildings,x,y,p)
for x,y in [(7,9),(12,15),(30,9),(27,15),(18,20),(22,20),(15,7),(25,7)]: setv(ground,x,y,MOTIFS[(x+y)%8])
room_xml('inkbound-stacks',back,ground,buildings,front,ROOT/'assets/region2_inkbound_stacks.tmx')

# Mirror Gallery: open, symmetric reflection floor.
back=blank(GRASS)
for y in range(H):
    width=4 if 5 <= y <= 22 else 2
    for x in range(20-width,21+width): setv(back,x,y,PATH)
for y in range(6,22):
    for x in (8,9,10,29,30,31):
        if (y%4)!=0: setv(back,x,y,DIRT)
ground=blank(); buildings=blank(); front=blank(); border(buildings)
for x,y in [(12,6),(28,6),(10,10),(30,10),(12,15),(28,15),(9,20),(31,20),(17,12),(23,12),(18,18),(22,18)]: setv(ground,x,y,MOTIFS[(x+y)%8])
for x,y,p in [(6,7,2028),(34,7,2028),(7,14,2029),(33,14,2029),(8,21,2032),(32,21,2032),(13,8,2036),(27,8,2037)]: setv(buildings,x,y,p)
room_xml('mirror-gallery',back,ground,buildings,front,ROOT/'assets/region2_mirror_gallery.tmx')

# Warden Vault: late-run chamber; north seal is the accepted 3x2 assembly.
back=blank(GRASS)
rect(back,7,5,32,23,DIRT); rect(back,10,7,29,21,PATH); rect(back,14,9,25,19,DIRT)
for y in range(3,27):
    for x in range(18,23): setv(back,x,y,PATH)
ground=blank(); buildings=blank(); front=blank(); border(buildings)
for x,gid in zip((19,20,21),(2020,2021,2022)): setv(buildings,x,3,gid)
for x,gid in zip((19,20,21),(2023,2024,2025)): setv(buildings,x,4,gid)
for x,y,p in [(8,8,2026),(32,8,2027),(8,19,2033),(32,19,2034),(13,12,2030),(27,12,2031),(13,18,2035),(27,18,2035)]: setv(buildings,x,y,p)
for x,y in [(10,10),(30,10),(11,17),(29,17),(16,8),(24,8),(16,21),(24,21)]: setv(ground,x,y,MOTIFS[(x+y)%8])
room_xml('warden-vault',back,ground,buildings,front,ROOT/'assets/region2_warden_vault.tmx')

# ---------- Region2RoguelikeRunService ----------
p=ROOT/'Services/Region2RoguelikeRunService.cs'
t=p.read_text(encoding='utf-8')

t=replace_once(t,'internal enum Region2NodeKind\n{','internal enum Region2RoomKind\n{\n    Vestibule,\n    InkboundStacks,\n    MirrorGallery,\n    WardenVault,\n}\n\ninternal enum Region2NodeKind\n{','room enum')
t=replace_once(t,
'    private const string NodeMarkerKey = "Ronvotri.Cardcha/0680Region2Node";\n    private const long ExtractConfirmWindowMs = 5000L;\n    private static readonly Point BossGateTile = new(20, 4);',
'    private const string NodeMarkerKey = "Ronvotri.Cardcha/0680Region2Node";\n    private const long ExtractConfirmWindowMs = 5000L;\n    private static readonly Point BossGateTile = new(20, 5);\n    public const string InkboundStacksLocationName = "Cardcha_Region2_InkboundStacks";\n    public const string InkboundStacksMapAssetName = "Maps/Cardcha_Region2_InkboundStacks";\n    public const string MirrorGalleryLocationName = "Cardcha_Region2_MirrorGallery";\n    public const string MirrorGalleryMapAssetName = "Maps/Cardcha_Region2_MirrorGallery";\n    public const string WardenVaultLocationName = "Cardcha_Region2_WardenVault";\n    public const string WardenVaultMapAssetName = "Maps/Cardcha_Region2_WardenVault";\n    private const string InkboundStacksMapPath = "assets/region2_inkbound_stacks.tmx";\n    private const string MirrorGalleryMapPath = "assets/region2_mirror_gallery.tmx";\n    private const string WardenVaultMapPath = "assets/region2_warden_vault.tmx";','room constants')
t=replace_once(t,'    private bool NodeSpawned;\n    private int CurrentNode;','    private bool NodeSpawned;\n    private bool PendingInternalRoomWarp;\n    private Region2NodeKind PendingNodeKind;\n    private Region2RoomKind CurrentRoom = Region2RoomKind.Vestibule;\n    private int CurrentNode;','room state')
t=replace_once(t,
'    public void OnSaveLoaded(object? sender, SaveLoadedEventArgs e) => this.ResetRuntime(clearEnemies: true);\n    public void OnDayStarted(object? sender, DayStartedEventArgs e) => this.ResetRuntime(clearEnemies: true);',
'    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)\n    {\n        if (e.NameWithoutLocale.IsEquivalentTo(InkboundStacksMapAssetName))\n            e.LoadFromModFile<xTile.Map>(InkboundStacksMapPath, AssetLoadPriority.Exclusive);\n        else if (e.NameWithoutLocale.IsEquivalentTo(MirrorGalleryMapAssetName))\n            e.LoadFromModFile<xTile.Map>(MirrorGalleryMapPath, AssetLoadPriority.Exclusive);\n        else if (e.NameWithoutLocale.IsEquivalentTo(WardenVaultMapAssetName))\n            e.LoadFromModFile<xTile.Map>(WardenVaultMapPath, AssetLoadPriority.Exclusive);\n    }\n\n    public void OnSaveLoaded(object? sender, SaveLoadedEventArgs e)\n    {\n        this.ResetRuntime(clearEnemies: true);\n        this.EnsureRoomLocations();\n    }\n    public void OnDayStarted(object? sender, DayStartedEventArgs e)\n    {\n        this.ResetRuntime(clearEnemies: true);\n        this.EnsureRoomLocations();\n    }','asset lifecycle')

start=t.index('    public void OnWarped(object? sender, WarpedEventArgs e)')
end=t.index('    public void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)', start)
new_warp='''    public void OnWarped(object? sender, WarpedEventArgs e)\n    {\n        bool incoming = IsRegion2(e.NewLocation);\n        bool outgoing = IsRegion2(e.OldLocation);\n\n        if (incoming && outgoing)\n        {\n            this.CurrentRoom = ResolveRoom(e.NewLocation);\n            this.ClearRunEnemies(e.OldLocation);\n            if (this.PendingInternalRoomWarp)\n            {\n                this.PendingInternalRoomWarp = false;\n                Region2NodeKind kind = this.PendingNodeKind;\n                this.BeginNodeHere(e.NewLocation, kind);\n            }\n            return;\n        }\n\n        if (incoming)\n        {\n            this.LegacyExpeditions.SuspendLegacyRegion2RuntimeForRoguelike();\n            this.CurrentRoom = ResolveRoom(e.NewLocation);\n            this.StartRun(e.NewLocation, this.DebugBossGateEntry);\n            this.DebugBossGateEntry = false;\n            return;\n        }\n\n        if (outgoing && this.Active)\n        {\n            if (!this.LeavingForBoss)\n            {\n                int lostScrap = this.UnbankedScrap;\n                int lostShiny = this.UnbankedShiny;\n                if (lostScrap > 0 || lostShiny > 0)\n                    Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.lost", new { scrap = lostScrap, shiny = lostShiny }));\n            }\n            this.ResetRuntime(clearEnemies: false);\n        }\n    }\n\n'''
t=t[:start]+new_warp+t[end:]
t=t.replace('return $"0681 Region II Rogue: active={this.Active}, node={this.CurrentNode}/{this.TargetNodes}, kind={this.CurrentKind}, "','return $"0682 Region II Rogue: active={this.Active}, room={this.CurrentRoom}, node={this.CurrentNode}/{this.TargetNodes}, kind={this.CurrentKind}, "')
t=replace_once(t,
'        if (debugBossGate)\n        {\n            this.CurrentNode = 6;\n            this.TargetNodes = Math.Max(6, this.TargetNodes);\n            this.CurrentKind = Region2NodeKind.BossGate;\n            this.BossGateReady = true;\n            this.LastCuratorRecord = "debug";\n            Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.debug_bossgate"));\n            return;\n        }',
'        if (debugBossGate)\n        {\n            this.CurrentNode = 6;\n            this.TargetNodes = Math.Max(6, this.TargetNodes);\n            this.LastCuratorRecord = "debug";\n            Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.debug_bossgate"));\n            this.BeginNode(location, Region2NodeKind.BossGate);\n            return;\n        }','debug start')
t=replace_once(t,
'    private void BeginNode(GameLocation location, Region2NodeKind kind)\n    {\n        this.CurrentKind = kind;',
'    private void BeginNode(GameLocation location, Region2NodeKind kind)\n    {\n        Region2RoomKind targetRoom = this.ResolveRoomForNode(kind);\n        string targetName = RoomLocationName(targetRoom);\n        if (!location.NameOrUniqueName.Equals(targetName, StringComparison.OrdinalIgnoreCase))\n        {\n            GameLocation? target = this.EnsureRoomLocation(targetRoom);\n            if (target is not null)\n            {\n                this.PendingInternalRoomWarp = true;\n                this.PendingNodeKind = kind;\n                this.ClearRunEnemies(location);\n                Point arrival = RoomArrivalTile(targetRoom);\n                Game1.warpFarmer(target.NameOrUniqueName, arrival.X, arrival.Y, 0);\n                return;\n            }\n        }\n        this.CurrentRoom = targetRoom;\n        this.BeginNodeHere(location, kind);\n    }\n\n    private void BeginNodeHere(GameLocation location, Region2NodeKind kind)\n    {\n        this.CurrentKind = kind;','begin node room transition')
old_candidates='''        Point[] candidates =\n        {\n            new(6,5), new(11,5), new(18,5), new(22,5), new(29,5), new(34,5),\n            new(7,10), new(13,10), new(20,9), new(27,10), new(33,10),\n            new(6,16), new(12,17), new(18,15), new(22,15), new(28,17), new(34,16),\n            new(9,22), new(15,21), new(25,21), new(31,22)\n        };'''
t=replace_once(t,old_candidates,'        Point[] candidates = SpawnCandidatesForRoom(this.CurrentRoom);','room spawn candidates')
t=replace_once(t,
'    private static bool IsRegion2(GameLocation? location)\n        => location?.NameOrUniqueName.Equals(RegionExpeditionService.Region2LocationName, StringComparison.OrdinalIgnoreCase) == true;',
'    internal static bool IsRegion2(GameLocation? location)\n        => location is not null && IsRegion2Name(location.NameOrUniqueName);\n\n    internal static bool IsRegion2Name(string? name)\n        => !string.IsNullOrWhiteSpace(name) && (\n            name.Equals(RegionExpeditionService.Region2LocationName, StringComparison.OrdinalIgnoreCase)\n            || name.Equals(InkboundStacksLocationName, StringComparison.OrdinalIgnoreCase)\n            || name.Equals(MirrorGalleryLocationName, StringComparison.OrdinalIgnoreCase)\n            || name.Equals(WardenVaultLocationName, StringComparison.OrdinalIgnoreCase));','room recognition')
t=replace_once(t,
'        if (clearEnemies && Context.IsWorldReady && IsRegion2(Game1.currentLocation) && Game1.currentLocation is not null)\n            this.ClearRunEnemies(Game1.currentLocation);',
'        if (clearEnemies && Context.IsWorldReady)\n        {\n            foreach (string name in Region2RoomNames())\n            {\n                GameLocation? room = Game1.getLocationFromName(name);\n                if (room is not null) this.ClearRunEnemies(room);\n            }\n        }','reset all rooms')
t=replace_once(t,'        this.NodeSpawned = false;\n        this.CurrentNode = 0;','        this.NodeSpawned = false;\n        this.PendingInternalRoomWarp = false;\n        this.CurrentRoom = Region2RoomKind.Vestibule;\n        this.CurrentNode = 0;','reset room state')

anchor='''    private static Point PlayerTile()\n        => new((int)(Game1.player.Position.X / 64f), (int)(Game1.player.Position.Y / 64f));'''
helpers='''    private Region2RoomKind ResolveRoomForNode(Region2NodeKind kind)\n    {\n        if (kind is Region2NodeKind.BossGate or Region2NodeKind.Elite or Region2NodeKind.FinalCache)\n            return Region2RoomKind.WardenVault;\n        if (kind == Region2NodeKind.MirrorChoice)\n            return Region2RoomKind.MirrorGallery;\n        if (kind is Region2NodeKind.Ambush or Region2NodeKind.CursedArchive)\n            return Region2RoomKind.InkboundStacks;\n        if (kind == Region2NodeKind.Restoration)\n            return this.CurrentNode >= 5 ? Region2RoomKind.MirrorGallery : Region2RoomKind.Vestibule;\n        if (kind == Region2NodeKind.Cache)\n            return ((this.RunSeed + this.CurrentNode) & 1) == 0 ? Region2RoomKind.MirrorGallery : Region2RoomKind.InkboundStacks;\n        if (kind == Region2NodeKind.ArchiveEvent)\n            return this.CurrentNode <= 3 ? Region2RoomKind.Vestibule : Region2RoomKind.MirrorGallery;\n        return (this.CurrentNode % 3) switch\n        {\n            0 => Region2RoomKind.MirrorGallery,\n            1 => Region2RoomKind.Vestibule,\n            _ => Region2RoomKind.InkboundStacks,\n        };\n    }\n\n    private static string RoomLocationName(Region2RoomKind room) => room switch\n    {\n        Region2RoomKind.InkboundStacks => InkboundStacksLocationName,\n        Region2RoomKind.MirrorGallery => MirrorGalleryLocationName,\n        Region2RoomKind.WardenVault => WardenVaultLocationName,\n        _ => RegionExpeditionService.Region2LocationName,\n    };\n\n    private static string RoomMapAssetName(Region2RoomKind room) => room switch\n    {\n        Region2RoomKind.InkboundStacks => InkboundStacksMapAssetName,\n        Region2RoomKind.MirrorGallery => MirrorGalleryMapAssetName,\n        Region2RoomKind.WardenVault => WardenVaultMapAssetName,\n        _ => RegionExpeditionService.Region2MapAssetName,\n    };\n\n    private static Point RoomArrivalTile(Region2RoomKind room)\n        => room == Region2RoomKind.WardenVault ? new Point(20, 23) : new Point(20, 24);\n\n    private static string[] Region2RoomNames()\n        => new[] { RegionExpeditionService.Region2LocationName, InkboundStacksLocationName, MirrorGalleryLocationName, WardenVaultLocationName };\n\n    private void EnsureRoomLocations()\n    {\n        foreach (Region2RoomKind room in Enum.GetValues<Region2RoomKind>())\n            this.EnsureRoomLocation(room);\n    }\n\n    private GameLocation? EnsureRoomLocation(Region2RoomKind room)\n    {\n        string name = RoomLocationName(room);\n        GameLocation? existing = Game1.getLocationFromName(name);\n        if (existing is not null) return existing;\n        try\n        {\n            GameLocation created = new(RoomMapAssetName(room), name);\n            Game1.locations.Add(created);\n            return created;\n        }\n        catch (Exception ex)\n        {\n            this.Monitor.Log($"0682 couldn't create Region II room {room}: {ex.GetType().Name}: {ex.Message}", LogLevel.Error);\n            return null;\n        }\n    }\n\n    private static Region2RoomKind ResolveRoom(GameLocation? location)\n    {\n        string? name = location?.NameOrUniqueName;\n        if (name?.Equals(InkboundStacksLocationName, StringComparison.OrdinalIgnoreCase) == true) return Region2RoomKind.InkboundStacks;\n        if (name?.Equals(MirrorGalleryLocationName, StringComparison.OrdinalIgnoreCase) == true) return Region2RoomKind.MirrorGallery;\n        if (name?.Equals(WardenVaultLocationName, StringComparison.OrdinalIgnoreCase) == true) return Region2RoomKind.WardenVault;\n        return Region2RoomKind.Vestibule;\n    }\n\n    private static Point[] SpawnCandidatesForRoom(Region2RoomKind room) => room switch\n    {\n        Region2RoomKind.InkboundStacks => new[]\n        {\n            new Point(5,5), new Point(13,5), new Point(27,5), new Point(35,5), new Point(7,10), new Point(16,10),\n            new Point(24,10), new Point(33,10), new Point(6,15), new Point(14,15), new Point(26,15), new Point(34,15),\n            new Point(9,20), new Point(17,20), new Point(23,20), new Point(31,20)\n        },\n        Region2RoomKind.MirrorGallery => new[]\n        {\n            new Point(8,6), new Point(14,6), new Point(20,7), new Point(26,6), new Point(32,6), new Point(10,11),\n            new Point(16,12), new Point(24,12), new Point(30,11), new Point(8,17), new Point(14,18), new Point(20,17),\n            new Point(26,18), new Point(32,17), new Point(12,22), new Point(28,22)\n        },\n        Region2RoomKind.WardenVault => new[]\n        {\n            new Point(10,8), new Point(15,8), new Point(25,8), new Point(30,8), new Point(9,13), new Point(15,13),\n            new Point(25,13), new Point(31,13), new Point(10,18), new Point(16,18), new Point(24,18), new Point(30,18)\n        },\n        _ => new[]\n        {\n            new Point(6,5), new Point(11,5), new Point(18,5), new Point(22,5), new Point(29,5), new Point(34,5),\n            new Point(7,10), new Point(13,10), new Point(20,9), new Point(27,10), new Point(33,10),\n            new Point(6,16), new Point(12,17), new Point(18,15), new Point(22,15), new Point(28,17), new Point(34,16),\n            new Point(9,22), new Point(15,21), new Point(25,21), new Point(31,22)\n        }\n    };\n\n    private static Point PlayerTile()\n        => new((int)(Game1.player.Position.X / 64f), (int)(Game1.player.Position.Y / 64f));'''
t=replace_once(t,anchor,helpers,'room helpers')
t=t.replace('0681 Region II -> Hollow Curator.', '0682 Region II -> Hollow Curator.')
t=t.replace('0680 Region II node ', '0682 Region II node ')
p.write_text(t,encoding='utf-8')

# ModEntry content event
p=ROOT/'ModEntry.cs'; t=p.read_text(encoding='utf-8')
t=replace_once(t,'        helper.Events.Content.AssetRequested += this.RegionExpeditions.OnAssetRequested;\n','        helper.Events.Content.AssetRequested += this.RegionExpeditions.OnAssetRequested;\n        helper.Events.Content.AssetRequested += this.Region2Rogue.OnAssetRequested;\n','asset event')
t=t.replace(OLD,NEW)
t=t.replace('0681 HOLLOW CURATOR RECORDS YOU TEST','0682 REGION II MULTI-ROOM ROGUELIKE TEST')
p.write_text(t,encoding='utf-8')

# Boss II entry accepts every Region II room
p=ROOT/'Services/MilestoneBossService.cs'; t=p.read_text(encoding='utf-8')
t=replace_once(t,
'        if (Game1.currentLocation?.NameOrUniqueName.Equals(RegionExpeditionService.Region2LocationName, StringComparison.OrdinalIgnoreCase) != true)\n            return ModEntry.T("airship.region2.boss_gate.location");',
'        if (!Region2RoguelikeRunService.IsRegion2(Game1.currentLocation))\n            return ModEntry.T("airship.region2.boss_gate.location");','boss room recognition')
p.write_text(t,encoding='utf-8')

for rel in ['manifest.json','Cardcha.csproj','Directory.Build.targets']:
    p=ROOT/rel; s=p.read_text(encoding='utf-8')
    if NEW not in s:
        if OLD not in s: raise SystemExit(f'0682 version anchor missing: {rel}')
        s=s.replace(OLD,NEW)
    p.write_text(s,encoding='utf-8')

# small room-name localization for logs/future HUD
for lang, vals in {
'default.json': {'airship.region2.room.vestibule':'Archive Vestibule','airship.region2.room.inkbound':'Inkbound Stacks','airship.region2.room.mirror':'Mirror Gallery','airship.region2.room.vault':'Warden Vault'},
'vi.json': {'airship.region2.room.vestibule':'Tiền Sảnh Kho Lưu Trữ','airship.region2.room.inkbound':'Dãy Kệ Nhuốm Mực','airship.region2.room.mirror':'Hành Lang Gương','airship.region2.room.vault':'Kho Niêm Phong Hộ Vệ'}
}.items():
    p=ROOT/'i18n'/lang; data=json.loads(p.read_text(encoding='utf-8')); data.update(vals); p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

(Path('handoff')/'ALPHA28_0682_REGION2_MULTIROOM_ROGUELIKE.md').write_text(f'''# Cardcha Alpha 28 - 0682 Region II Multi-Room Roguelike\n\nBranch: `cardcha-alpha28-0682-region2-multiroom-roguelike`  \nBuild: `{NEW}`\n\n## Purpose\n0680 made Region II a 6-9 node branching run. 0681 connected the run record to Hollow Curator. 0682 removes the remaining one-floor repetition: nodes now move through four physical Forgotten Archive room identities instead of replaying every encounter on one map.\n\n## Room set\n1. **Archive Vestibule** - broad early-run floor and ordinary combat/event space. Uses the accepted 0679 base map.\n2. **Inkbound Stacks** - broken shelf islands and narrower combat pockets. Favours Ambush/Cursed Archive and some caches.\n3. **Mirror Gallery** - wider symmetric reflection floor. Favours Mirror Choice, later events and some recovery/cache nodes.\n4. **Warden Vault** - compact late-run chamber containing the assembled Archive Seal. Elite, Final Cache and Boss Gate resolve here.\n\nA 6-9 node run may revisit a room identity, but standard combat rotates by depth and encounter kinds strongly bias different rooms. Node count remains the roguelike progression unit; a room is presentation/space, not a fixed checklist node.\n\n## Runtime transitions\nInternal Region II warps are explicitly distinguished from entering/leaving the region. Moving between Archive rooms never resets the run, never loses unbanked cargo and never restarts node 1. The selected node begins only after the destination room's Warped event resolves. Each room has its own spawn candidate set.\n\n## Depth contract\nAll physical shelves, seal pieces and room motifs live in TMX Back/CardchaGround/Buildings/Front. No room furniture or scenery is drawn from RenderedWorld.\n\n## Frozen contracts\n- Region II remains 6-9 nodes.\n- Fare remains 250g.\n- Checkpoints remain nodes 3 and 6.\n- Curator Records You remains active.\n- Boss II remains 2200 HP / 40-card milestone / Mirror Archive reward.\n- Region III/IV, Boss III/IV, Airship and MiMi art are unchanged.\n- Save schema remains 19; 80 source / 76 normal cards.\n\n## Acceptance\nCI proves static/compile/package only. In-game verify at least one run crosses multiple room identities, internal warps preserve cargo/records/node count, enemy spawns are reachable, the Warden Vault seal is aligned, and no TMX physical prop covers Farmer incorrectly.\n''',encoding='utf-8')
(Path('handoff')/'LATEST_CARDCHA_HANDOFF.md').write_text(f'''# Latest Cardcha Handoff\n\nCurrent branch: `cardcha-alpha28-0682-region2-multiroom-roguelike`\nCurrent build: `{NEW}`\nContinue from: `handoff/ALPHA28_0682_REGION2_MULTIROOM_ROGUELIKE.md`\nDesign direction: `handoff/REGION2_ROGUELIKE_DESIGN_DIRECTION.md`\n\n0682 preserves the 6-9 node branching run and Curator Records You, but nodes now transition among four physical Forgotten Archive room identities. In-game acceptance is pending.\n''',encoding='utf-8')
print('0682 multi-room integration generated successfully')
