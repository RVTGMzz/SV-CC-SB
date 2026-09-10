#!/usr/bin/env python3
from pathlib import Path

p = Path('tools/alpha28_0684_region2_room_specific_mechanics.py')
s = p.read_text(encoding='utf-8')
old_anchor = "        this.NodeSpawned = false;\\n        this.PendingInternalRoomWarp = false;\\n        this.AwaitingRoomInteraction = false;"
new_anchor = "        this.NodeSpawned = false;\\n        this.AwaitingRoomInteraction = false;\\n        this.ActiveInteractionTile = Point.Zero;\\n        this.PendingInternalRoomWarp = false;"
old_replacement = "        this.NodeSpawned = false;\\n        this.ResetRoomMechanicState();\\n        this.PendingInternalRoomWarp = false;\\n        this.AwaitingRoomInteraction = false;"
new_replacement = "        this.NodeSpawned = false;\\n        this.ResetRoomMechanicState();\\n        this.AwaitingRoomInteraction = false;\\n        this.ActiveInteractionTile = Point.Zero;\\n        this.PendingInternalRoomWarp = false;"
if old_anchor in s:
    s = s.replace(old_anchor, new_anchor, 1)
if old_replacement in s:
    s = s.replace(old_replacement, new_replacement, 1)
if new_anchor not in s or new_replacement not in s:
    raise SystemExit('0684 ALIGN FAIL: reset anchor/replacement not aligned')
p.write_text(s, encoding='utf-8')
print('0684 generator reset anchor aligned.')
