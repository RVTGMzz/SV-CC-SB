#!/usr/bin/env python3
from pathlib import Path
p=Path('tools/alpha28_0683_region2_room_interactions.py')
s=p.read_text(encoding='utf-8')
old="""t=replace_once(t,\n'        this.NodeSpawned = false;\\n        this.CurrentNode = 0;',\n'        this.NodeSpawned = false;\\n        this.AwaitingRoomInteraction = false;\\n        this.ActiveInteractionTile = Point.Zero;\\n        this.CurrentNode = 0;',\n'reset interaction state')"""
new="""t=replace_once(t,\n'        this.NodeSpawned = false;\\n        this.PendingInternalRoomWarp = false;\\n        this.CurrentRoom = Region2RoomKind.Vestibule;\\n        this.CurrentNode = 0;',\n'        this.NodeSpawned = false;\\n        this.AwaitingRoomInteraction = false;\\n        this.ActiveInteractionTile = Point.Zero;\\n        this.PendingInternalRoomWarp = false;\\n        this.CurrentRoom = Region2RoomKind.Vestibule;\\n        this.CurrentNode = 0;',\n'reset interaction state')"""
if old not in s and new not in s:
    raise SystemExit('0683 reset-generator fix anchor missing')
if old in s:
    s=s.replace(old,new,1)
# Also make ResetRuntime clear Cardcha interaction chests from all Region II rooms.
anchor="""                GameLocation? room = Game1.getLocationFromName(name);\\n                if (room is not null) this.ClearRunEnemies(room);"""
replacement="""                GameLocation? room = Game1.getLocationFromName(name);\\n                if (room is not null)\\n                {\\n                    this.ClearRunEnemies(room);\\n                    this.ClearInteractionObject(room);\\n                }"""
# This is source-code text embedded inside the generator output; inject a post-transform if absent.
post="""t=t.replace('                GameLocation? room = Game1.getLocationFromName(name);\\n                if (room is not null) this.ClearRunEnemies(room);',\n            '                GameLocation? room = Game1.getLocationFromName(name);\\n                if (room is not null)\\n                {\\n                    this.ClearRunEnemies(room);\\n                    this.ClearInteractionObject(room);\\n                }')\n"""
marker="t=t.replace('0682 couldn\\'t create Region II room','0683 couldn\\'t create Region II room')"
if post not in s:
    if marker not in s:
        raise SystemExit('0683 interaction cleanup insertion anchor missing')
    s=s.replace(marker,post+marker,1)
p.write_text(s,encoding='utf-8')
print('0683 generator reset/cleanup fix applied')
