#!/usr/bin/env python3
from pathlib import Path

p = Path('src/Cardcha/Services/Region2RoguelikeRunService.cs')
s = p.read_text(encoding='utf-8')
old = '''            else
            {
                this.CurrentKind = Region2NodeKind.FinalCache;
                this.AwardNode(Region2NodeKind.FinalCache);
                this.RouteComplete = true;
                Game1.playSound("discoverMineral");
                Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.complete", new { scrap = this.UnbankedScrap, shiny = this.UnbankedShiny }));
            }
            return;'''
new = '''            else
            {
                // 0684 audit correction: route-end Final Cache must remain the physical 0683 Chest interaction.
                // Never auto-award it from the node-completion path.
                this.BeginNode(location, Region2NodeKind.FinalCache);
            }
            return;'''
if new in s:
    print('0684 route-end Final Cache fix already materialized.')
    raise SystemExit(0)
if old not in s:
    raise SystemExit('0684 FINAL CACHE FIX FAIL: legacy auto-award block not found')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('0684 route-end Final Cache now requires physical Chest interaction.')
