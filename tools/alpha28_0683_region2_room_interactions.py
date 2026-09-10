#!/usr/bin/env python3
from pathlib import Path
import json, re, xml.etree.ElementTree as ET
from PIL import Image, ImageDraw

ROOT=Path('src/Cardcha')
OLD='0.3.0-alpha.28.0.4.14.4.5.12.50'
NEW='0.3.0-alpha.28.0.4.14.4.5.12.51'


def need(cond,msg):
    if not cond:
        raise SystemExit('0683 BUILD FAIL: '+msg)

def replace_once(text, old, new, label):
    if new in text:
        return text
    need(old in text, 'missing anchor: '+label)
    return text.replace(old,new,1)

# ---------- authored native-pixel interaction station atlas ----------
atlas=Image.new('RGBA',(128,32),(0,0,0,0))
d=ImageDraw.Draw(atlas)

def px_rect(box, fill, outline=None):
    d.rectangle(box, fill=fill, outline=outline)

# mirror shrine, x 0..31
px_rect((4,4,27,27),(92,78,120,255),(42,36,60,255))
px_rect((7,6,24,23),(158,184,216,255),(229,232,248,255))
px_rect((10,9,21,20),(113,143,190,255))
px_rect((12,10,14,18),(206,222,240,180))
px_rect((8,24,23,27),(90,70,110,255))
# archive lectern, x 32..63
px_rect((39,15,56,27),(112,74,45,255),(55,38,28,255))
px_rect((42,10,53,18),(145,92,52,255),(62,41,28,255))
px_rect((36,7,47,13),(238,221,161,255),(111,78,45,255))
px_rect((48,7,59,13),(229,211,151,255),(111,78,45,255))
px_rect((47,8,48,13),(117,81,45,255))
# restoration font, x 64..95
px_rect((68,17,91,27),(81,106,103,255),(38,60,58,255))
px_rect((72,13,87,20),(99,166,160,255),(210,238,223,255))
px_rect((76,8,83,16),(129,211,192,255))
px_rect((78,5,81,10),(206,246,229,255))
px_rect((71,25,88,28),(66,91,84,255))
# cursed tome, x 96..127
px_rect((103,16,120,27),(64,47,70,255),(31,24,38,255))
px_rect((100,8,111,16),(112,61,117,255),(46,29,53,255))
px_rect((112,8,123,16),(96,49,108,255),(46,29,53,255))
px_rect((111,9,112,16),(205,95,190,255))
px_rect((106,5,109,8),(188,80,181,255))
px_rect((115,4,118,7),(133,91,194,255))

atlas_path=ROOT/'assets/region2_interaction_stations.png'
atlas.save(atlas_path)

# ---------- stamp physical interaction stations into TMX Buildings layers ----------
FIRSTGID=2101
station_tiles={
    'mirror':   (2101,2102,2109,2110),
    'lectern':  (2103,2104,2111,2112),
    'restoration':(2105,2106,2113,2114),
    'cursed':   (2107,2108,2115,2116),
}
room_stations={
    'region2_forgotten_archive.tmx': [('lectern',8,10),('restoration',29,17)],
    'region2_inkbound_stacks.tmx': [('cursed',19,11)],
    'region2_mirror_gallery.tmx': [('mirror',19,10),('restoration',8,17),('lectern',29,17)],
    'region2_warden_vault.tmx': [],
}

def csv_values(layer):
    data=layer.find('data')
    vals=[int(x.strip()) for x in (data.text or '').split(',') if x.strip()]
    return data,vals

def write_csv(data,vals,w,h):
    rows=[]
    for y in range(h):
        rows.append(','.join(str(v) for v in vals[y*w:(y+1)*w])+',')
    data.text='\n'+'\n'.join(rows)+'\n'

for filename, stations in room_stations.items():
    p=ROOT/'assets'/filename
    tree=ET.parse(p); root=tree.getroot()
    w=int(root.attrib['width']); h=int(root.attrib['height'])
    need((w,h)==(40,28), filename+' must stay 40x28')
    props=root.find('properties')
    if props is None:
        props=ET.Element('properties'); root.insert(0,props)
    def set_prop(name,value):
        existing=next((x for x in props.findall('property') if x.attrib.get('name')==name),None)
        if existing is None:
            existing=ET.SubElement(props,'property',{'name':name})
        existing.set('value',value)
    set_prop('CardchaRegionVersion',NEW)
    set_prop('CardchaInteractionPolicy','tmx-physical-stations|manual-action|no-renderedworld-physical-props')
    ts=next((x for x in root.findall('tileset') if x.attrib.get('name')=='cardcha_region2_interactions'),None)
    if ts is None:
        ts=ET.Element('tileset',{
            'firstgid':str(FIRSTGID),'name':'cardcha_region2_interactions','tilewidth':'16','tileheight':'16',
            'tilecount':'16','columns':'8'
        })
        ET.SubElement(ts,'image',{'source':'region2_interaction_stations.png','width':'128','height':'32'})
        children=list(root)
        last_ts=max(i for i,x in enumerate(children) if x.tag=='tileset')
        root.insert(last_ts+1,ts)
    buildings=next(x for x in root.findall('layer') if x.attrib.get('name')=='Buildings')
    data,vals=csv_values(buildings)
    need(len(vals)==w*h, filename+' Buildings CSV length')
    for kind,x,y in stations:
        a,b,c,e=station_tiles[kind]
        vals[y*w+x]=a; vals[y*w+x+1]=b
        vals[(y+1)*w+x]=c; vals[(y+1)*w+x+1]=e
    write_csv(data,vals,w,h)
    tree.write(p,encoding='utf-8',xml_declaration=True)

# ---------- Region II runtime: manual interaction nodes ----------
p=ROOT/'Services/Region2RoguelikeRunService.cs'
t=p.read_text(encoding='utf-8')
t=replace_once(t,'using StardewValley.Monsters;','using StardewValley.Monsters;\nusing StardewValley.Objects;','Chest namespace')
t=replace_once(t,
'    private const string NodeMarkerKey = "Ronvotri.Cardcha/0680Region2Node";\n    private const long ExtractConfirmWindowMs = 5000L;',
'    private const string NodeMarkerKey = "Ronvotri.Cardcha/0680Region2Node";\n    private const string InteractionMarkerKey = "Ronvotri.Cardcha/0683Region2Interaction";\n    private const long ExtractConfirmWindowMs = 5000L;',
'interaction marker')
t=replace_once(t,
'    private bool NodeSpawned;\n    private bool PendingInternalRoomWarp;',
'    private bool NodeSpawned;\n    private bool AwaitingRoomInteraction;\n    private Point ActiveInteractionTile;\n    private bool PendingInternalRoomWarp;',
'interaction state')
t=replace_once(t,
'        if (incoming && outgoing)\n        {\n            this.CurrentRoom = ResolveRoom(e.NewLocation);\n            this.ClearRunEnemies(e.OldLocation);',
'        if (incoming && outgoing)\n        {\n            this.ClearInteractionObject(e.OldLocation);\n            this.CurrentRoom = ResolveRoom(e.NewLocation);\n            this.ClearRunEnemies(e.OldLocation);',
'internal warp cleanup')
t=replace_once(t,
'        Point player = PlayerTile();\n        Point action = Game1.player.GetGrabTile().ToPoint();\n\n        bool gateClose',
'        Point player = PlayerTile();\n        Point action = Game1.player.GetGrabTile().ToPoint();\n\n        if (this.AwaitingRoomInteraction && this.TryHandleRoomInteraction(e, Game1.currentLocation, action))\n        {\n            this.Helper.Input.Suppress(e.Button);\n            return;\n        }\n\n        bool gateClose',
'interaction button priority')
t=replace_once(t,
'        if (!IsCombatKind(this.CurrentKind))\n            return $"Region II node {this.CurrentNode}/{this.TargetNodes} is {this.CurrentKind}; there are no combat enemies to clear.";',
'        if (this.AwaitingRoomInteraction)\n            return this.DebugResolveRoomInteraction();\n        if (!IsCombatKind(this.CurrentKind))\n            return $"Region II node {this.CurrentNode}/{this.TargetNodes} is {this.CurrentKind}; there are no combat enemies to clear.";',
'debug manual interaction')
t=t.replace('return $"0682 Region II Rogue: active={this.Active}, room={this.CurrentRoom}, node={this.CurrentNode}/{this.TargetNodes}, kind={this.CurrentKind}, "',
            'return $"0683 Region II Rogue: active={this.Active}, room={this.CurrentRoom}, node={this.CurrentNode}/{this.TargetNodes}, kind={this.CurrentKind}, interaction={this.AwaitingRoomInteraction}, "')
t=replace_once(t,
'        this.NodeSpawned = false;\n        this.CurrentNode = 1;',
'        this.NodeSpawned = false;\n        this.AwaitingRoomInteraction = false;\n        this.ActiveInteractionTile = Point.Zero;\n        this.CurrentNode = 1;',
'start run reset')

old_block='''        this.CurrentKind = kind;\n        this.ChoicePending = false;\n        this.BossGateReady = false;\n        this.NodeSpawned = false;\n        this.ExtractConfirmUntilMs = 0;\n        this.NodeStartHealth = Math.Max(1, Game1.player.health);\n\n        if (kind == Region2NodeKind.BossGate)\n        {\n            this.BossGateReady = true;\n            this.LastCuratorRecord = this.CurrentRecordTag();\n            Game1.playSound("discoverMineral");\n            Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.bossgate_ready", new { record = this.RecordDisplayName(this.LastCuratorRecord) }));\n            return;\n        }\n\n        if (kind == Region2NodeKind.FinalCache)\n        {\n            this.AwardNode(kind);\n            this.RouteComplete = true;\n            Game1.playSound("discoverMineral");\n            Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.complete", new { scrap = this.UnbankedScrap, shiny = this.UnbankedShiny }));\n            return;\n        }\n\n        if (IsCombatKind(kind))\n        {\n            this.SpawnNodeEnemies(location, kind);\n            this.NodeSpawned = true;\n            Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.node", new\n            {\n                node = this.CurrentNode,\n                total = this.TargetNodes,\n                kind = this.NodeDisplayName(kind)\n            }));\n            return;\n        }\n\n        this.ResolveNonCombatNode(kind);\n        this.CompleteCurrentNode(location);'''
new_block='''        this.CurrentKind = kind;\n        this.ChoicePending = false;\n        this.BossGateReady = false;\n        this.NodeSpawned = false;\n        this.AwaitingRoomInteraction = false;\n        this.ActiveInteractionTile = Point.Zero;\n        this.ClearInteractionObject(location);\n        this.ExtractConfirmUntilMs = 0;\n        this.NodeStartHealth = Math.Max(1, Game1.player.health);\n\n        if (kind == Region2NodeKind.BossGate)\n        {\n            this.BossGateReady = true;\n            this.LastCuratorRecord = this.CurrentRecordTag();\n            Game1.playSound("discoverMineral");\n            Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.bossgate_ready", new { record = this.RecordDisplayName(this.LastCuratorRecord) }));\n            return;\n        }\n\n        if (kind == Region2NodeKind.FinalCache || IsManualInteractionKind(kind))\n        {\n            this.PrepareRoomInteraction(location, kind);\n            return;\n        }\n\n        if (kind == Region2NodeKind.CursedArchive)\n        {\n            this.PrepareRoomInteraction(location, kind);\n            return;\n        }\n\n        if (IsCombatKind(kind))\n        {\n            this.SpawnNodeEnemies(location, kind);\n            this.NodeSpawned = true;\n            Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.node", new\n            {\n                node = this.CurrentNode,\n                total = this.TargetNodes,\n                kind = this.NodeDisplayName(kind)\n            }));\n            return;\n        }'''
t=replace_once(t,old_block,new_block,'BeginNodeHere manual conversion')

insert_anchor='    private void SpawnNodeEnemies(GameLocation location, Region2NodeKind kind)\n'
need(insert_anchor in t,'SpawnNodeEnemies anchor')
manual_methods=r'''    private void PrepareRoomInteraction(GameLocation location, Region2NodeKind kind)
    {
        this.AwaitingRoomInteraction = true;
        this.ActiveInteractionTile = ResolveInteractionTile(kind, this.CurrentRoom);
        if (kind is Region2NodeKind.Cache or Region2NodeKind.FinalCache)
            this.EnsureInteractionChest(location, this.ActiveInteractionTile);

        Game1.showGlobalMessage(ModEntry.T("airship.region2.interaction.ready", new
        {
            node = this.CurrentNode,
            total = this.TargetNodes,
            target = this.InteractionDisplayName(kind)
        }));
    }

    private bool TryHandleRoomInteraction(ButtonPressedEventArgs e, GameLocation location, Point actionTile)
    {
        if (!this.AwaitingRoomInteraction)
            return false;

        Point cursorTile = new((int)e.Cursor.GrabTile.X, (int)e.Cursor.GrabTile.Y);
        bool mouseDirect = e.Button == SButton.MouseRight && Touches(cursorTile, this.ActiveInteractionTile);
        if (!Touches(actionTile, this.ActiveInteractionTile) && !mouseDirect)
            return false;

        this.ResolveRoomInteraction(location, debug: false);
        return true;
    }

    private void ResolveRoomInteraction(GameLocation location, bool debug)
    {
        if (!this.AwaitingRoomInteraction)
            return;

        Region2NodeKind kind = this.CurrentKind;
        this.AwaitingRoomInteraction = false;

        if (kind is Region2NodeKind.Cache or Region2NodeKind.FinalCache)
        {
            this.ClearInteractionObject(location);
            Game1.playSound("openBox");
        }

        if (kind == Region2NodeKind.CursedArchive)
        {
            Game1.playSound("wand");
            this.SpawnNodeEnemies(location, kind);
            this.NodeSpawned = true;
            Game1.drawObjectDialogue(ModEntry.T("airship.region2.interaction.cursed_awakened"));
            return;
        }

        if (kind == Region2NodeKind.FinalCache)
        {
            this.AwardNode(kind);
            this.RouteComplete = true;
            Game1.playSound("discoverMineral");
            Game1.drawObjectDialogue(ModEntry.T("airship.region2.interaction.final_opened", new
            {
                scrap = this.UnbankedScrap,
                shiny = this.UnbankedShiny
            }));
            return;
        }

        this.ResolveNonCombatNode(kind);
        this.CompleteCurrentNode(location);
    }

    private string DebugResolveRoomInteraction()
    {
        if (!Context.IsWorldReady || !this.AwaitingRoomInteraction || Game1.currentLocation is null)
            return "No pending Region II room interaction.";

        Region2NodeKind kind = this.CurrentKind;
        this.ResolveRoomInteraction(Game1.currentLocation, debug: true);
        if (kind == Region2NodeKind.CursedArchive && this.NodeSpawned)
        {
            int removed = 0;
            for (int i = Game1.currentLocation.characters.Count - 1; i >= 0; i--)
            {
                if (Game1.currentLocation.characters[i] is Monster monster && monster.modData.ContainsKey(NodeMarkerKey))
                {
                    monster.Health = 0;
                    Game1.currentLocation.characters.RemoveAt(i);
                    removed++;
                }
            }
            return $"TEST: activated Cursed Archive and cleared {removed} awakened enemy/enemies; completion resolves next tick.";
        }
        return $"TEST: resolved Region II interaction node {this.CurrentNode}/{this.TargetNodes} ({kind}).";
    }

    private void EnsureInteractionChest(GameLocation room, Point tile)
    {
        Vector2 key = new(tile.X, tile.Y);
        if (room.Objects.TryGetValue(key, out StardewValley.Object? existing))
        {
            if (existing is Chest && existing.modData.ContainsKey(InteractionMarkerKey))
                return;
            this.Monitor.Log($"0683 Region II interaction chest tile {tile} is occupied; node remains interactable by tile.", LogLevel.Warn);
            return;
        }

        Chest chest = new(true);
        chest.modData[InteractionMarkerKey] = $"0683:{this.CurrentNode}:{this.CurrentKind}";
        room.setObject(key, chest);
    }

    private void ClearInteractionObject(GameLocation? room)
    {
        if (room is null)
            return;
        Point tile = ResolveCacheTile(ResolveRoom(room));
        Vector2 key = new(tile.X, tile.Y);
        if (room.Objects.TryGetValue(key, out StardewValley.Object? existing)
            && existing.modData.ContainsKey(InteractionMarkerKey))
            room.Objects.Remove(key);
    }

    private static bool IsManualInteractionKind(Region2NodeKind kind)
        => kind is Region2NodeKind.MirrorChoice or Region2NodeKind.ArchiveEvent or Region2NodeKind.Cache or Region2NodeKind.Restoration;

    private static Point ResolveInteractionTile(Region2NodeKind kind, Region2RoomKind room)
    {
        if (kind is Region2NodeKind.Cache or Region2NodeKind.FinalCache)
            return ResolveCacheTile(room);
        if (kind == Region2NodeKind.CursedArchive)
            return new Point(20, 12);
        if (kind == Region2NodeKind.MirrorChoice)
            return new Point(20, 11);
        if (kind == Region2NodeKind.Restoration)
            return room == Region2RoomKind.MirrorGallery ? new Point(9, 18) : new Point(30, 18);
        if (kind == Region2NodeKind.ArchiveEvent)
            return room == Region2RoomKind.MirrorGallery ? new Point(30, 18) : new Point(9, 11);
        return new Point(20, 14);
    }

    private static Point ResolveCacheTile(Region2RoomKind room) => room switch
    {
        Region2RoomKind.WardenVault => new Point(20, 16),
        Region2RoomKind.MirrorGallery => new Point(20, 17),
        Region2RoomKind.InkboundStacks => new Point(20, 17),
        _ => new Point(20, 16),
    };

    private string InteractionDisplayName(Region2NodeKind kind)
        => ModEntry.T($"airship.region2.interaction.object.{InteractionKey(kind)}");

    private static string InteractionKey(Region2NodeKind kind) => kind switch
    {
        Region2NodeKind.MirrorChoice => "mirror",
        Region2NodeKind.ArchiveEvent => "lectern",
        Region2NodeKind.Cache => "cache",
        Region2NodeKind.Restoration => "restoration",
        Region2NodeKind.CursedArchive => "cursed",
        Region2NodeKind.FinalCache => "finalcache",
        _ => "archive",
    };

    private static bool Touches(Point a, Point b)
        => Math.Abs(a.X - b.X) <= 1 && Math.Abs(a.Y - b.Y) <= 1;

'''
t=t.replace(insert_anchor,manual_methods+insert_anchor,1)

t=replace_once(t,
'        this.NodeSpawned = false;\n        this.CurrentNode = 0;',
'        this.NodeSpawned = false;\n        this.AwaitingRoomInteraction = false;\n        this.ActiveInteractionTile = Point.Zero;\n        this.CurrentNode = 0;',
'reset interaction state')
t=t.replace('0682 couldn\'t create Region II room','0683 couldn\'t create Region II room')
t=t.replace('0682 Region II node','0683 Region II node')
t=t.replace('0682 Region II -> Hollow Curator','0683 Region II -> Hollow Curator')
p.write_text(t,encoding='utf-8')

# ---------- version / build label ----------
for rel in ['manifest.json','Cardcha.csproj','Directory.Build.targets','ModEntry.cs']:
    q=ROOT/rel
    s=q.read_text(encoding='utf-8')
    s=s.replace(OLD,NEW)
    if rel=='ModEntry.cs':
        s=s.replace('0682 REGION II MULTI-ROOM ROGUELIKE TEST','0683 REGION II ROOM INTERACTION TEST')
        s=s.replace('clear current Region II node or Region III/IV expedition wave.','clear/resolve current Region II node or Region III/IV expedition wave.')
    q.write_text(s,encoding='utf-8')

# ---------- i18n ----------
strings_en={
    'airship.region2.interaction.ready':'Node {{node}}/{{total}}: {{target}} is waiting here. Interact with it to resolve this node.',
    'airship.region2.interaction.object.mirror':'the Archive Mirror',
    'airship.region2.interaction.object.lectern':'the Archive Lectern',
    'airship.region2.interaction.object.cache':'the sealed cache',
    'airship.region2.interaction.object.restoration':'the Restoration Font',
    'airship.region2.interaction.object.cursed':'the Cursed Tome',
    'airship.region2.interaction.object.finalcache':'the deep archive cache',
    'airship.region2.interaction.object.archive':'the archive focus',
    'airship.region2.interaction.cursed_awakened':'The Cursed Tome opens by itself. Ink-black pages scatter, and the archive wakes around you.',
    'airship.region2.interaction.final_opened':'The deep archive cache opens. Unbanked cargo: {{scrap}} Scrap + {{shiny}} Shiny.'
}
strings_vi={
    'airship.region2.interaction.ready':'Node {{node}}/{{total}}: {{target}} đang chờ trong phòng. Hãy tới gần và tương tác để hoàn tất node này.',
    'airship.region2.interaction.object.mirror':'Gương Lưu Trữ',
    'airship.region2.interaction.object.lectern':'Bục Sách Lưu Trữ',
    'airship.region2.interaction.object.cache':'rương lưu trữ niêm phong',
    'airship.region2.interaction.object.restoration':'Suối Phục Hồi',
    'airship.region2.interaction.object.cursed':'Quyển Sách Nguyền',
    'airship.region2.interaction.object.finalcache':'rương sâu trong kho lưu trữ',
    'airship.region2.interaction.object.archive':'điểm cộng hưởng lưu trữ',
    'airship.region2.interaction.cursed_awakened':'Quyển Sách Nguyền tự bật mở. Những trang giấy đen như mực tung ra, cả kho lưu trữ thức giấc quanh bạn.',
    'airship.region2.interaction.final_opened':'Rương sâu trong kho lưu trữ đã mở. Hàng chưa gửi kho: {{scrap}} Scrap + {{shiny}} Shiny.'
}
for name,add in [('default.json',strings_en),('vi.json',strings_vi)]:
    q=ROOT/'i18n'/name
    data=json.loads(q.read_text(encoding='utf-8'))
    data.update(add)
    q.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# ---------- handoff / design trail ----------
handoff=Path('handoff/ALPHA28_0683_REGION2_ROOM_INTERACTIONS.md')
handoff.write_text('''# Cardcha Alpha 28 - 0683 Region II Room Interactions\n\nBranch: `cardcha-alpha28-0683-region2-room-interactions`  \nBuild: `0.3.0-alpha.28.0.4.14.4.5.12.51`\n\n## Purpose\n\n0682 made Region II physically multi-room, but non-combat nodes still resolved immediately on entry. 0683 converts the archive into a tactile roguelike space: the player must walk to and interact with a physical room focus before Mirror Choice, Archive Event, Cache, Restoration, Cursed Archive, or Final Cache resolves.\n\n## Physical interaction contract\n\n- Mirror Shrine, Archive Lectern, Restoration Font and Cursed Tome are authored 32x32 native-pixel station art stamped into TMX `Buildings` layers through `region2_interaction_stations.png`.\n- Cache and Final Cache use a real Stardew `Chest` object with Cardcha modData.\n- No physical station is drawn from `RenderedWorld`.\n- No floating action label is used. The entry message names the target; the room itself communicates the object.\n- Controller and keyboard action-tile interaction are supported; direct right-click also works.\n\n## Node behavior\n\n- Mirror Choice: interact with the Archive Mirror, then the existing Mirror reward/record logic resolves.\n- Archive Event: interact with the Archive Lectern before its existing reward/heal behavior resolves.\n- Restoration: interact with the Restoration Font before the existing heal/reward resolves.\n- Cache: a real chest must be opened; it disappears after Cardcha resolves the reward.\n- Cursed Archive: enemies do not spawn until the player activates the Cursed Tome.\n- Final Cache: the run does not become complete until the deep cache is opened.\n- Boss Gate remains physical in Warden Vault and unchanged.\n\n## Frozen contracts\n\n- Region II remains 6-9 nodes, four room identities and 250g fare.\n- Checkpoints remain node 3 and 6.\n- Curator Records You remains intact.\n- Hollow Curator remains 2200 HP, 40-card milestone, Mirror Archive reward.\n- Region III/IV, Boss III/IV, Airship and MiMi assets are unchanged.\n- Save schema remains 19; 80 source / 76 normal cards.\n- Repository rendering-depth contract remains mandatory.\n\n## Acceptance\n\nIn game, verify each manual node can be found and activated without props covering Farmer/NPCs. Cache chest must be physical and removable. Cursed Archive must stay dormant until the tome is activated. Internal room warps must retain node/record/cargo state.\n''',encoding='utf-8')

latest=Path('handoff/LATEST_CARDCHA_HANDOFF.md')
latest.write_text('''# Latest Cardcha Handoff\n\nCurrent branch: `cardcha-alpha28-0683-region2-room-interactions`\nCurrent build: `0.3.0-alpha.28.0.4.14.4.5.12.51`\nContinue from: `handoff/ALPHA28_0683_REGION2_ROOM_INTERACTIONS.md`\nDesign direction: `handoff/REGION2_ROGUELIKE_DESIGN_DIRECTION.md`\n\n0683 preserves the 6-9 node multi-room run and Curator Records You, but non-combat Region II nodes now require physical room interaction. Cache/Final Cache use real Chest objects; other stations live in TMX Buildings layers. In-game acceptance is pending.\n''',encoding='utf-8')

doc=Path('handoff/REGION2_ROGUELIKE_DESIGN_DIRECTION.md')
ds=doc.read_text(encoding='utf-8')
if '### 0683 implementation note' not in ds:
    ds += '''\n\n### 0683 implementation note\n\nRoom variety must be functional, not decorative only. Non-combat nodes should ask the player to physically read the room: walk to a mirror, lectern, restorative focus, cursed object, or cache and interact. Physical objects belong in TMX/native Stardew object systems, never post-world overlays. This is presentation architecture, not a mandate that every future node use the same station or reward.\n'''
    doc.write_text(ds,encoding='utf-8')

print('0683 generated: manual Region II interactions, native TMX stations, real cache chests, Cursed Archive activation, version',NEW)
