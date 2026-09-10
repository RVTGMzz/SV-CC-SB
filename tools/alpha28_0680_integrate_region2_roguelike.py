#!/usr/bin/env python3
from pathlib import Path
import json, re

VERSION_OLD='0.3.0-alpha.28.0.4.14.4.5.12.47'
VERSION_NEW='0.3.0-alpha.28.0.4.14.4.5.12.48'

def repl(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f'0680 integration anchor missing: {label}')
    return text.replace(old,new,1)

# ----- Region II service runtime polish: defer route choice until event dialogue closes -----
p=Path('src/Cardcha/Services/Region2RoguelikeRunService.cs')
t=p.read_text(encoding='utf-8')
t=repl(t,
'''    private bool ChoicePending;\n    private bool DebugBossGateEntry;''',
'''    private bool ChoicePending;\n    private bool ChoiceDeferred;\n    private bool DebugBossGateEntry;''',
'choice deferred field')
t=repl(t,
'''        if (this.RouteComplete || this.BossGateReady || this.ChoicePending)\n            return;\n        if (!IsCombatKind(this.CurrentKind) || !this.NodeSpawned)''',
'''        if (this.ChoiceDeferred && !Game1.dialogueUp && Game1.activeClickableMenu is null)\n        {\n            this.ChoiceDeferred = false;\n            this.PrepareRouteChoice(Game1.currentLocation);\n            return;\n        }\n        if (this.RouteComplete || this.BossGateReady || this.ChoicePending || this.ChoiceDeferred)\n            return;\n        if (!IsCombatKind(this.CurrentKind) || !this.NodeSpawned)''',
'deferred choice update')
t=repl(t,
'''        this.ResolveNonCombatNode(kind);\n        this.CompleteCurrentNode(location);''',
'''        this.ResolveNonCombatNode(kind);\n        this.CompleteCurrentNode(location);''',
'noncombat unchanged sentinel')
# At the end of CompleteCurrentNode, defer if an event dialogue is still active.
t=repl(t,
'''        this.PrepareRouteChoice(location);\n    }\n\n    private void PrepareRouteChoice''',
'''        if (Game1.dialogueUp || Game1.activeClickableMenu is not null)\n        {\n            this.ChoiceDeferred = true;\n            return;\n        }\n        this.PrepareRouteChoice(location);\n    }\n\n    private void PrepareRouteChoice''',
'defer route choice after dialogue')
t=repl(t,
'''        this.ChoicePending = false;\n        this.NodeSpawned = false;''',
'''        this.ChoicePending = false;\n        this.ChoiceDeferred = false;\n        this.NodeSpawned = false;''',
'start reset deferred')
t=repl(t,
'''        this.ChoicePending = false;\n        this.NodeSpawned = false;\n        this.CurrentNode = 0;''',
'''        this.ChoicePending = false;\n        this.ChoiceDeferred = false;\n        this.NodeSpawned = false;\n        this.CurrentNode = 0;''',
'full reset deferred')
p.write_text(t,encoding='utf-8')

# ----- Legacy RegionExpeditionService: provide a clean Region II runtime handoff -----
p=Path('src/Cardcha/Services/RegionExpeditionService.cs')
t=p.read_text(encoding='utf-8')
anchor='''    public void BindRegion2BossGateDebugHandler(Func<string> handler)\n        => this.Region2BossGateDebugAction = handler;\n\n    public void OnAssetRequested'''
insert='''    public void BindRegion2BossGateDebugHandler(Func<string> handler)\n        => this.Region2BossGateDebugAction = handler;\n\n    /// <summary>\n    /// 0680 runtime handoff: Region II roguelike owns the Forgotten Archive after the Airship/permission\n    /// layer has accepted the warp. Region III/IV remain on this legacy expedition runtime.\n    /// </summary>\n    public void SuspendLegacyRegion2RuntimeForRoguelike()\n    {\n        if (this.CurrentRegion != ExpeditionRegion.ForgottenArchive)\n            return;\n        if (Game1.currentLocation?.NameOrUniqueName.Equals(Region2LocationName, StringComparison.OrdinalIgnoreCase) == true)\n            this.ClearMarkedEnemies(Game1.currentLocation);\n        this.CurrentRegion = null;\n        this.Active = false;\n        this.Completed = false;\n        this.WaveSpawned = false;\n        this.CurrentWave = 0;\n        this.BossApproachMode = false;\n        this.NextWaveAtMs = 0;\n        this.UnbankedScrap = 0;\n        this.UnbankedShiny = 0;\n        this.ExtractConfirmUntilMs = 0;\n    }\n\n    public void OnAssetRequested'''
t=repl(t,anchor,insert,'legacy Region II suspension method')
p.write_text(t,encoding='utf-8')

# ----- ModEntry wiring -----
p=Path('src/Cardcha/ModEntry.cs')
t=p.read_text(encoding='utf-8')
t=repl(t,
'    private RegionExpeditionService RegionExpeditions = null!;\n',
'    private RegionExpeditionService RegionExpeditions = null!;\n    private Region2RoguelikeRunService Region2Rogue = null!;\n',
'Region2 field')
t=repl(t,
'''        this.RegionExpeditions = new RegionExpeditionService(helper, this.Monitor, this.Save, this.Airship);\n        this.VerdantGuardian =''',
'''        this.RegionExpeditions = new RegionExpeditionService(helper, this.Monitor, this.Save, this.Airship);\n        this.Region2Rogue = new Region2RoguelikeRunService(helper, this.Monitor, this.Save, this.Airship, this.RegionExpeditions);\n        this.VerdantGuardian =''',
'Region2 instantiate')
t=repl(t,
'''        this.RegionExpeditions.BindRegion2BossGateDebugHandler(() => this.MilestoneBosses.DebugEnterBoss(2));\n        this.Airship.BindMilestoneRouteHandler''',
'''        this.RegionExpeditions.BindRegion2BossGateDebugHandler(() => this.MilestoneBosses.DebugEnterBoss(2));\n        this.Region2Rogue.BindBossGateHandlers(this.MilestoneBosses.EnterBoss2FromRegion2, () => this.MilestoneBosses.DebugEnterBoss(2));\n        this.Airship.BindMilestoneRouteHandler''',
'Region2 boss bind')
# lifecycle/events, always after legacy RegionExpeditions so 0680 can take ownership.
for old,new,label in [
('        helper.Events.GameLoop.SaveLoaded += this.RegionExpeditions.OnSaveLoaded;\n','        helper.Events.GameLoop.SaveLoaded += this.RegionExpeditions.OnSaveLoaded;\n        helper.Events.GameLoop.SaveLoaded += this.Region2Rogue.OnSaveLoaded;\n','save event'),
('        helper.Events.GameLoop.DayStarted += this.RegionExpeditions.OnDayStarted;\n','        helper.Events.GameLoop.DayStarted += this.RegionExpeditions.OnDayStarted;\n        helper.Events.GameLoop.DayStarted += this.Region2Rogue.OnDayStarted;\n','day event'),
('        helper.Events.GameLoop.UpdateTicked += this.RegionExpeditions.OnUpdateTicked;\n','        helper.Events.GameLoop.UpdateTicked += this.RegionExpeditions.OnUpdateTicked;\n        helper.Events.GameLoop.UpdateTicked += this.Region2Rogue.OnUpdateTicked;\n','update event'),
('        helper.Events.GameLoop.ReturnedToTitle += this.RegionExpeditions.OnReturnedToTitle;\n','        helper.Events.GameLoop.ReturnedToTitle += this.RegionExpeditions.OnReturnedToTitle;\n        helper.Events.GameLoop.ReturnedToTitle += this.Region2Rogue.OnReturnedToTitle;\n','title event'),
('        helper.Events.Input.ButtonPressed += this.RegionExpeditions.OnButtonPressed;\n','        helper.Events.Input.ButtonPressed += this.RegionExpeditions.OnButtonPressed;\n        helper.Events.Input.ButtonPressed += this.Region2Rogue.OnButtonPressed;\n','button event'),
('        helper.Events.Player.Warped += this.RegionExpeditions.OnWarped;\n','        helper.Events.Player.Warped += this.RegionExpeditions.OnWarped;\n        helper.Events.Player.Warped += this.Region2Rogue.OnWarped;\n','warp event')]:
    t=repl(t,old,new,label)

old='''        helper.ConsoleCommands.Add("cardcha_expedition_status", "Show Region II/III/IV expedition runtime and route state.", (_, _) => this.Monitor.Log(this.RegionExpeditions.Describe(), LogLevel.Alert));\n        helper.ConsoleCommands.Add("cardcha_test_region2", "TEST ONLY: enter Region II Forgotten Archive as a normal 21-40 progression run.", (_, _) => this.Monitor.Log(this.RegionExpeditions.DebugEnter(2), LogLevel.Alert));\n        helper.ConsoleCommands.Add("cardcha_test_region2_bossgate", "TEST ONLY: enter Region II Boss Approach and test the north Archive Seal.", (_, _) => this.Monitor.Log(this.RegionExpeditions.DebugEnterRegion2BossApproach(), LogLevel.Alert));'''
new='''        helper.ConsoleCommands.Add("cardcha_expedition_status", "Show Region II roguelike + Region III/IV expedition runtime and route state.", (_, _) => this.Monitor.Log(this.Region2Rogue.Describe() + "\\n" + this.RegionExpeditions.Describe(), LogLevel.Alert));\n        helper.ConsoleCommands.Add("cardcha_region2_rogue_status", "Show Region II 6-9 node route, risk/reward and Curator observation state.", (_, _) => this.Monitor.Log(this.Region2Rogue.Describe(), LogLevel.Alert));\n        helper.ConsoleCommands.Add("cardcha_test_region2", "TEST ONLY: enter Region II Forgotten Archive as a normal 6-9 node roguelike run.", (_, _) =>\n        {\n            this.Region2Rogue.PrepareNormalDebugEntry();\n            this.Monitor.Log(this.RegionExpeditions.DebugEnter(2), LogLevel.Alert);\n        });\n        helper.ConsoleCommands.Add("cardcha_test_region2_bossgate", "TEST ONLY: enter Region II at a node-6-ready Archive Seal without changing save progression.", (_, _) =>\n        {\n            this.Region2Rogue.PrepareBossGateDebugEntry();\n            this.Monitor.Log(this.RegionExpeditions.DebugEnter(2), LogLevel.Alert);\n        });'''
t=repl(t,old,new,'region2 commands')
t=repl(t,
'''        helper.ConsoleCommands.Add("cardcha_expedition_clear", "TEST ONLY: clear current Region II/III/IV expedition wave.", (_, _) => this.Monitor.Log(this.RegionExpeditions.DebugClearWave(), LogLevel.Alert));''',
'''        helper.ConsoleCommands.Add("cardcha_expedition_clear", "TEST ONLY: clear current Region II node or Region III/IV expedition wave.", (_, _) => this.Monitor.Log(this.Region2Rogue.IsActive ? this.Region2Rogue.DebugClearCurrentNode() : this.RegionExpeditions.DebugClearWave(), LogLevel.Alert));''',
'expedition clear command')
# build log/version
t=t.replace(VERSION_OLD, VERSION_NEW)
t=t.replace('0679 REGION II 21-40 + BOSS II APPROACH TEST','0680 REGION II 6-9 NODE ROGUELIKE ROUTE TEST')
p.write_text(t,encoding='utf-8')

# ----- Versions -----
for rel in ['src/Cardcha/manifest.json','src/Cardcha/Cardcha.csproj','src/Cardcha/Directory.Build.targets']:
    p=Path(rel); s=p.read_text(encoding='utf-8');
    if VERSION_NEW not in s:
        if VERSION_OLD not in s: raise SystemExit(f'0680 version anchor missing: {rel}')
        s=s.replace(VERSION_OLD,VERSION_NEW)
    p.write_text(s,encoding='utf-8')

# ----- i18n -----
en={
'airship.region2.rogue.start':'FORGOTTEN ARCHIVE RUN • Route depth this run: {{total}} nodes. The Archive is watching.',
'airship.region2.rogue.node':'ARCHIVE {{node}}/{{total}} • {{kind}}',
'airship.region2.rogue.choose':'The Archive forks at node {{node}}/{{total}}. Choose a route.',
'airship.region2.rogue.route_label':'{{kind}} • {{risk}}',
'airship.region2.rogue.risk_high':'HIGH RISK / HIGH REWARD',
'airship.region2.rogue.risk_normal':'VARIABLE ROUTE',
'airship.region2.rogue.kind.combat':'Inkbound Hall',
'airship.region2.rogue.kind.ambush':'Page-Swarm Ambush',
'airship.region2.rogue.kind.elite':'Warden Archive',
'airship.region2.rogue.kind.mirror':'Mirror Choice',
'airship.region2.rogue.kind.event':'Living Index',
'airship.region2.rogue.kind.cache':'Sealed Cache',
'airship.region2.rogue.kind.restoration':'Restoration Desk',
'airship.region2.rogue.kind.cursed':'Cursed Archive',
'airship.region2.rogue.kind.bossgate':'Archive Seal • Hollow Curator',
'airship.region2.rogue.kind.finalcache':'Deep Archive Cache',
'airship.region2.rogue.event.mirror':'A cracked mirror records your reflection. +3 unbanked Scrap. The Curator noticed the choice.',
'airship.region2.rogue.event.archive':'The Living Index rearranges itself around your recent condition. A small recovery and +2 unbanked Scrap.',
'airship.region2.rogue.event.cache':'A sealed drawer clicks open. +4 unbanked Scrap; something shiny may be tucked inside.',
'airship.region2.rogue.event.restoration':'An old restoration desk still hums. Recover up to 18 HP and gain +1 unbanked Scrap.',
'airship.region2.rogue.checkpoint':'ARCHIVE CHECKPOINT • Node {{node}} banked +{{scrap}} Scrap / +{{shiny}} Shiny.',
'airship.region2.rogue.complete':'DEEP ARCHIVE CLEARED • Return south to extract. Unbanked: {{scrap}} Scrap / {{shiny}} Shiny.',
'airship.region2.rogue.lost':'The Archive closed behind you. Lost unbanked route reward: {{scrap}} Scrap / {{shiny}} Shiny.',
'airship.region2.rogue.bossgate_ready':'ARCHIVE SEAL READY • Hollow Curator recorded: {{record}}. Interact with the north seal.',
'airship.region2.rogue.bossgate_not_ready':'The north Archive Seal is observing you, but the route has not exposed the boss yet. Current node: {{node}}.',
'airship.region2.rogue.extract_complete':'Extract this completed run? Remaining {{scrap}} Scrap / {{shiny}} Shiny will be banked. Interact again to confirm.',
'airship.region2.rogue.extract_early':'Emergency extract at node {{node}}/{{total}}? Unbanked {{scrap}} Scrap / {{shiny}} Shiny will be LOST. Checkpoint rewards stay safe. Interact again to confirm.',
'airship.region2.rogue.debug_bossgate':'TEST • Region II Archive Seal is ready at node 6. Debug bypass changes no save progression.',
'airship.region2.rogue.record.neutral':'no dominant pattern',
'airship.region2.rogue.record.risk':'risk-seeking routes',
'airship.region2.rogue.record.precision':'clean clears',
'airship.region2.rogue.record.pressure':'damage taken under pressure',
'airship.region2.rogue.record.recovery':'recovery choices',
'airship.region2.rogue.record.mirror':'mirror interactions',
'airship.region2.rogue.record.debug':'debug record'
}
vi={
'airship.region2.rogue.start':'CHUYẾN ĐI KHO LƯU TRỮ • Độ sâu lần này: {{total}} nút. Kho Lưu Trữ đang quan sát bạn.',
'airship.region2.rogue.node':'KHO LƯU TRỮ {{node}}/{{total}} • {{kind}}',
'airship.region2.rogue.choose':'Lối đi tách nhánh tại nút {{node}}/{{total}}. Chọn tuyến đường.',
'airship.region2.rogue.route_label':'{{kind}} • {{risk}}',
'airship.region2.rogue.risk_high':'RỦI RO CAO / THƯỞNG CAO',
'airship.region2.rogue.risk_normal':'TUYẾN BIẾN ĐỔI',
'airship.region2.rogue.kind.combat':'Hành Lang Mực',
'airship.region2.rogue.kind.ambush':'Phục Kích Bầy Trang',
'airship.region2.rogue.kind.elite':'Kho Của Giám Thư',
'airship.region2.rogue.kind.mirror':'Lựa Chọn Gương',
'airship.region2.rogue.kind.event':'Mục Lục Sống',
'airship.region2.rogue.kind.cache':'Hòm Lưu Trữ Niêm Phong',
'airship.region2.rogue.kind.restoration':'Bàn Phục Chế',
'airship.region2.rogue.kind.cursed':'Kho Lưu Trữ Nguyền Rủa',
'airship.region2.rogue.kind.bossgate':'Phong Ấn Kho • Hollow Curator',
'airship.region2.rogue.kind.finalcache':'Kho Sâu',
'airship.region2.rogue.event.mirror':'Chiếc gương nứt ghi lại bóng của bạn. +3 Scrap chưa gửi kho. Curator đã chú ý lựa chọn này.',
'airship.region2.rogue.event.archive':'Mục Lục Sống tự sắp xếp theo tình trạng hiện tại của bạn. Hồi phục nhẹ và +2 Scrap chưa gửi kho.',
'airship.region2.rogue.event.cache':'Một ngăn tủ niêm phong bật mở. +4 Scrap chưa gửi kho; đôi khi còn có thứ lấp lánh bên trong.',
'airship.region2.rogue.event.restoration':'Một bàn phục chế cũ vẫn còn cộng hưởng. Hồi tối đa 18 HP và +1 Scrap chưa gửi kho.',
'airship.region2.rogue.checkpoint':'ĐIỂM LƯU KHO • Nút {{node}} đã gửi +{{scrap}} Scrap / +{{shiny}} Shiny vào kho an toàn.',
'airship.region2.rogue.complete':'ĐÃ KHÁM PHÁ KHO SÂU • Trở về phía nam để rút quân. Chưa gửi kho: {{scrap}} Scrap / {{shiny}} Shiny.',
'airship.region2.rogue.lost':'Kho Lưu Trữ khép lại phía sau. Mất phần thưởng chưa gửi kho: {{scrap}} Scrap / {{shiny}} Shiny.',
'airship.region2.rogue.bossgate_ready':'PHONG ẤN ĐÃ MỞ • Hollow Curator ghi nhận: {{record}}. Tương tác phong ấn phía bắc để vào Boss II.',
'airship.region2.rogue.bossgate_not_ready':'Phong ấn phía bắc đang quan sát bạn nhưng tuyến Boss chưa lộ ra. Hiện tại: nút {{node}}.',
'airship.region2.rogue.extract_complete':'Rút khỏi chuyến đi đã hoàn thành? {{scrap}} Scrap / {{shiny}} Shiny còn lại sẽ được gửi kho. Tương tác lần nữa để xác nhận.',
'airship.region2.rogue.extract_early':'Rút khẩn cấp ở nút {{node}}/{{total}}? {{scrap}} Scrap / {{shiny}} Shiny chưa gửi kho sẽ MẤT. Phần đã qua checkpoint vẫn an toàn. Tương tác lần nữa để xác nhận.',
'airship.region2.rogue.debug_bossgate':'TEST • Phong Ấn Region II đã sẵn sàng ở nút 6. Bypass test không sửa tiến trình save.',
'airship.region2.rogue.record.neutral':'chưa có xu hướng nổi bật',
'airship.region2.rogue.record.risk':'thích chọn đường mạo hiểm',
'airship.region2.rogue.record.precision':'dọn phòng sạch sẽ',
'airship.region2.rogue.record.pressure':'chịu nhiều áp lực sát thương',
'airship.region2.rogue.record.recovery':'ưu tiên hồi phục',
'airship.region2.rogue.record.mirror':'tương tác với gương',
'airship.region2.rogue.record.debug':'bản ghi test'
}
for rel, additions in [('src/Cardcha/i18n/default.json',en),('src/Cardcha/i18n/vi.json',vi)]:
    p=Path(rel); data=json.loads(p.read_text(encoding='utf-8')); data.update(additions); p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# ----- Design doc: explicit 6-9 target -----
p=Path('handoff/REGION2_ROGUELIKE_DESIGN_DIRECTION.md')
s=p.read_text(encoding='utf-8')
s=s.replace('roughly 4–7 short nodes as a tuning starting point','roughly 6–9 short nodes as the run-length target, aligned with Region I’s overall run length while keeping a different node identity and route logic')
s=s.replace('exactly 4–7 nodes forever','exactly 6–9 nodes forever')
if '6–9 short nodes' not in s: raise SystemExit('0680 design doc 6-9 update failed')
p.write_text(s,encoding='utf-8')

# ----- Handoff -----
handoff='''# Cardcha Alpha 28 - 0680 Region II Roguelike Route Foundation\n\nBranch: `cardcha-alpha28-0680-region2-roguelike-route-foundation`  \nBuild: `0.3.0-alpha.28.0.4.14.4.5.12.48`\n\n## Locked design correction\n\nRegion II run length is now **6-9 nodes**, intentionally similar to Region I's overall run length. This does NOT mean copying Region I room logic. Region II keeps the Forgotten Archive identity: branching choices, observation, recording, reflection and optional risk before Hollow Curator.\n\nThe earlier user example of 2-3 maps / 2-3 waves remains illustrative only, not a hard requirement.\n\n## 0680 runtime\n\nA dedicated `Region2RoguelikeRunService` now owns Region II runtime after the existing Airship/permission layer lands the player in the Forgotten Archive. Region III/IV remain on `RegionExpeditionService`.\n\n- Run target: deterministic 6-9 nodes.\n- Node types: Combat, Ambush, Elite, Mirror Choice, Archive Event, Cache, Restoration, Cursed Archive, Boss Gate, Final Cache.\n- Route choices are generated between nodes; the same fixed 3-wave sequence is gone for Region II.\n- Boss Gate may be offered from node 6 onward when Boss I is really clear and 40 cards are owned.\n- Choosing to go deeper keeps offering higher-risk alternatives until the target depth.\n- If under 40 cards, the run ends in a deep cache/extraction instead of Boss II.\n- Checkpoints at nodes 3 and 6 bank route rewards.\n- Early emergency extraction loses only currently unbanked rewards; checkpointed rewards remain safe.\n- Entering Hollow Curator banks remaining Region II route rewards before the arena warp.\n\n## Curator observation foundation\n\n0680 records a small transparent runtime profile for the current run:\n\n- risk route choices;\n- clean combat clears;\n- heavy damage / pressure clears;\n- restoration choices;\n- mirror interactions.\n\nThis is not yet wired into Hollow Curator attacks. It is the data foundation for the next encounter-auth pass. The current dominant record is exposed in `cardcha_region2_rogue_status` and at the Boss Gate.\n\n## Rendering contract\n\nNo new physical prop is drawn from `RenderedWorld`. Region II enemies continue using authored 32px sprites through the existing `Monster.draw` proxy suppression path. Static physical art remains TMX-owned.\n\n## Test\n\n1. `cardcha_test_region2` starts a normal 6-9 node test run without mutating progression.\n2. Use `cardcha_expedition_clear` on combat/ambush/elite/cursed nodes.\n3. Verify route choices vary and non-combat nodes do not require fake enemies.\n4. Verify node 3/6 checkpoint banking.\n5. Verify early extraction loses unbanked rewards only.\n6. `cardcha_test_region2_bossgate` starts directly at a test-ready node 6 Archive Seal; save progression remains unchanged.\n7. `cardcha_region2_rogue_status` shows run depth, route type, rewards and Curator record.\n8. Real 40-card progression must still require Boss I before Hollow Curator.\n\n## Frozen contracts\n\nSave schema 19; 80 source / 76 normal cards; Region II Airship fare 250g; Boss II 2200 HP; Region III/IV gameplay; MiMi locked art; 0678 Boss II-IV actor-depth art; Airship accepted assets; repository rendering-depth contract.\n\nIn-game acceptance remains pending. 0680 is the roguelike route foundation, not the final Hollow Curator behavior/animation pass.\n'''
Path('handoff/ALPHA28_0680_REGION2_ROGUELIKE_ROUTE_FOUNDATION.md').write_text(handoff,encoding='utf-8')
latest='''# Latest Cardcha Handoff\n\nCurrent branch: `cardcha-alpha28-0680-region2-roguelike-route-foundation`\nCurrent build: `0.3.0-alpha.28.0.4.14.4.5.12.48`\nContinue from: `handoff/ALPHA28_0680_REGION2_ROGUELIKE_ROUTE_FOUNDATION.md`\nDesign direction: `handoff/REGION2_ROGUELIKE_DESIGN_DIRECTION.md`\n\n0680 replaces Region II's fixed three-wave runtime with a 6-9 node branching roguelike route and lays the Curator observation foundation. In-game acceptance is pending.\n'''
Path('handoff/LATEST_CARDCHA_HANDOFF.md').write_text(latest,encoding='utf-8')
print('0680 integration complete')
