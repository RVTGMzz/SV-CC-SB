from pathlib import Path
import json

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.37'
PREV = '0.3.0-alpha.28.0.4.14.4.5.12.36'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'0668C anchor missing: {label}')
    return text.replace(old, new, 1)


# -----------------------------------------------------------------------------
# Version bump
# -----------------------------------------------------------------------------
manifest_path = ROOT / 'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['Version'] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for rel in ['Cardcha.csproj', 'Directory.Build.targets']:
    p = ROOT / rel
    s = p.read_text(encoding='utf-8').replace(PREV, VERSION)
    p.write_text(s, encoding='utf-8')

p = ROOT / 'ModEntry.cs'
s = p.read_text(encoding='utf-8').replace(PREV, VERSION)
p.write_text(s, encoding='utf-8')

# -----------------------------------------------------------------------------
# Boss I: Totem objective clarity, without changing balance.
# -----------------------------------------------------------------------------
p = ROOT / 'Services' / 'VerdantGuardianBossService.cs'
s = p.read_text(encoding='utf-8')

s = replace_once(
    s,
    '    private int LastTotemHitIndex = -1;\n',
    '    private int LastTotemHitIndex = -1;\n    private int LastTotemHitDamage;\n',
    'totem last-hit damage field'
)
s = replace_once(
    s,
    '    internal int VisualLastTotemHitIndex => this.LastTotemHitIndex;\n',
    '    internal int VisualLastTotemHitIndex => this.LastTotemHitIndex;\n    internal int VisualLastTotemHitDamage => this.LastTotemHitDamage;\n',
    'totem last-hit damage visual snapshot'
)
# The vanilla slime exists only as a collision/damage proxy. It must never be visible.
s = s.replace('            proxy.isInvisible.Value = false;\n', '            proxy.isInvisible.Value = true;\n')
if 'proxy.isInvisible.Value = true;' not in s:
    raise RuntimeError('0668C failed to hide Verdant Totem vanilla proxy')

# Reset last-hit damage anywhere the existing index is reset.
s = s.replace(
    '        this.LastTotemHitIndex = -1;\n',
    '        this.LastTotemHitIndex = -1;\n        this.LastTotemHitDamage = 0;\n'
)

s = replace_once(
    s,
    '            Game1.showGlobalMessage(ModEntry.T("boss.verdant.totem.broken", new { remaining = living }));\n',
    '            Game1.showGlobalMessage(ModEntry.T("boss.verdant.totem.broken", new { remaining = living, barrier = this.GetTotemDamageReductionPercent() }));\n',
    'totem break barrier feedback'
)

old_notify = '''    internal void NotifyTotemHit(Monster monster, int previousHealth)\n    {\n        if (!monster.modData.ContainsKey(TotemMarkerKey) || previousHealth <= monster.Health) return;\n        this.LastTotemHitAtMs = Environment.TickCount64;\n        if (monster.modData.TryGetValue(TotemIndexKey, out string? raw) && int.TryParse(raw, out int index)) this.LastTotemHitIndex = Math.Clamp(index, 0, TotemTiles.Length - 1);\n    }\n'''
new_notify = '''    internal void NotifyTotemHit(Monster monster, int previousHealth)\n    {\n        if (!monster.modData.ContainsKey(TotemMarkerKey) || previousHealth <= monster.Health) return;\n        this.LastTotemHitAtMs = Environment.TickCount64;\n        this.LastTotemHitDamage = Math.Max(1, previousHealth - Math.Max(0, monster.Health));\n        if (monster.modData.TryGetValue(TotemIndexKey, out string? raw) && int.TryParse(raw, out int index)) this.LastTotemHitIndex = Math.Clamp(index, 0, TotemTiles.Length - 1);\n    }\n'''
s = replace_once(s, old_notify, new_notify, 'totem hit damage capture')

s = replace_once(
    s,
    '        this.LastLivingTotemCount = living;\n    }\n\n    internal int ModifyBossIncomingDamage',
    '        this.LastLivingTotemCount = living;\n        this.PruneDestroyedTotems();\n    }\n\n    private void PruneDestroyedTotems()\n    {\n        GameLocation? arena = Game1.getLocationFromName(LocationName);\n        if (arena is null) return;\n        foreach (Monster dead in arena.characters.OfType<Monster>()\n                     .Where(m => m.Health <= 0 && m.modData.ContainsKey(TotemMarkerKey))\n                     .ToList())\n        {\n            arena.characters.Remove(dead);\n        }\n    }\n\n    internal int ModifyBossIncomingDamage',
    'dead totem pruning'
)

# Extend Boss I HUD with the mechanic the player is meant to read.
s = replace_once(
    s,
    '        Rectangle outer = new(x, y, width, 34);\n',
    '        Rectangle outer = new(x, y, width, 58);\n',
    'boss HUD height'
)
hud_anchor = '        e.SpriteBatch.DrawString(Game1.smallFont, title, new Vector2(Game1.uiViewport.Width / 2f - size.X / 2f, y + 7), Color.White);\n'
hud_add = hud_anchor + '''        int livingTotems = this.GetLivingTotemCount();\n        int barrier = this.GetTotemDamageReductionPercent();\n        string totemSummary = ModEntry.T("boss.verdant.totem.hud", new { living = livingTotems, barrier });\n        Vector2 totemSize = Game1.smallFont.MeasureString(totemSummary);\n        Color totemColor = livingTotems > 0 ? new Color(221, 244, 184) : new Color(255, 220, 151);\n        e.SpriteBatch.DrawString(Game1.smallFont, totemSummary, new Vector2(Game1.uiViewport.Width / 2f - totemSize.X / 2f, y + 35), totemColor);\n'''
s = replace_once(s, hud_anchor, hud_add, 'boss HUD totem summary')

p.write_text(s, encoding='utf-8')

# -----------------------------------------------------------------------------
# Boss I arena presentation: stronger target hit + final stagger readability.
# -----------------------------------------------------------------------------
p = ROOT / 'Services' / 'VerdantGuardianArenaPolishService.cs'
s = p.read_text(encoding='utf-8')

s = s.replace(
    'Environment.TickCount64 - this.Boss.VisualLastTotemHitAtMs < 130 ? 0.45f : 0f',
    'Environment.TickCount64 - this.Boss.VisualLastTotemHitAtMs < 520 ? 0.90f : 0f'
)
if '< 520 ? 0.90f : 0f' not in s:
    raise RuntimeError('0668C totem hit-flash anchor missing')
s = s.replace(
    '2.15f * pulse, SpriteEffects.None, layer);',
    '2.15f * pulse * (1f + flash * 0.10f), SpriteEffects.None, layer);',
    1
)

hp_line = '            int barW = 54, barX = (int)local.X - 27, barY = (int)local.Y + 7; batch.Draw(Game1.staminaRect, new Rectangle(barX, barY, barW, 5), Color.Black * 0.65f); batch.Draw(Game1.staminaRect, new Rectangle(barX + 1, barY + 1, Math.Max(1, (int)((barW - 2) * hp)), 3), new Color(119, 211, 92) * 0.92f);\n'
hp_plus = hp_line + '''            if (index == this.Boss.VisualLastTotemHitIndex && Environment.TickCount64 - this.Boss.VisualLastTotemHitAtMs < 700 && this.Boss.VisualLastTotemHitDamage > 0)\n            {\n                string hitText = $"-{this.Boss.VisualLastTotemHitDamage}";\n                Vector2 hitSize = Game1.smallFont.MeasureString(hitText);\n                batch.DrawString(Game1.smallFont, hitText, new Vector2(local.X - hitSize.X / 2f, local.Y - 92f), new Color(255, 237, 156));\n            }\n'''
s = replace_once(s, hp_line, hp_plus, 'totem floating hit number')

world_anchor = '        this.DrawAmbientMotes(e.SpriteBatch);\n'
s = replace_once(
    s,
    world_anchor,
    world_anchor + '        this.DrawTotemStaggerBurst(e.SpriteBatch);\n',
    'totem stagger world burst call'
)

state_anchor = '        if (current == VerdantGuardianState.PhaseTransition)\n'
state_add = '''        if (current == VerdantGuardianState.TotemStagger)\n        {\n            this.PlayCue("thudStep");\n            this.TriggerShake(10, 520, "totem-final-stagger");\n        }\n\n''' + state_anchor
s = replace_once(s, state_anchor, state_add, 'totem stagger camera/sound cue')

method_anchor = '    private void DrawRetreatGlyph(SpriteBatch batch)\n'
stagger_method = '''    private void DrawTotemStaggerBurst(SpriteBatch batch)\n    {\n        if (this.Boss.VisualState != VerdantGuardianState.TotemStagger) return;\n        long elapsed = Math.Max(0L, Environment.TickCount64 - this.Boss.VisualStateStartedAtMs);\n        float progress = Math.Clamp(elapsed / 1200f, 0f, 1f);\n        Vector2 local = Game1.GlobalToLocal(Game1.viewport, this.Boss.VisualBossCenter);\n        int radius = 42 + (int)(progress * 150f);\n        float alpha = Math.Max(0f, 0.92f - progress * 0.72f);\n        Color c = new Color(205, 255, 137) * alpha;\n        for (int i = 0; i < 20; i++)\n        {\n            float a = i * MathHelper.TwoPi / 20f;\n            int x = (int)(local.X + MathF.Cos(a) * radius);\n            int y = (int)(local.Y + MathF.Sin(a) * radius * 0.58f);\n            batch.Draw(Game1.staminaRect, new Rectangle(x - 4, y - 4, 8, 8), c);\n        }\n        if (elapsed < 360)\n        {\n            int flash = Math.Max(70, 240 - (int)(elapsed * 0.42f));\n            batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - flash / 2, (int)local.Y - flash / 4, flash, flash / 2), Color.White * (0.16f * (1f - elapsed / 360f)));\n        }\n    }\n\n'''
s = replace_once(s, method_anchor, stagger_method + method_anchor, 'totem stagger burst method')

p.write_text(s, encoding='utf-8')

# -----------------------------------------------------------------------------
# Hunt Run Lost Cache: physical chest + interaction-gated reward.
# The screenshot-confirmed issue was the Hunt Run rare room, not Sky Dock.
# -----------------------------------------------------------------------------
p = ROOT / 'Services' / 'AirshipFoundationService.cs'
s = p.read_text(encoding='utf-8')

s = replace_once(
    s,
    '    private const string Region1RootNestMarkerKey = "Ronvotri.Cardcha/Region1RootNest";\n',
    '    private const string Region1RootNestMarkerKey = "Ronvotri.Cardcha/Region1RootNest";\n    private const string Region1LostCacheMarkerKey = "Ronvotri.Cardcha/Region1LostCache";\n',
    'Lost Cache marker key'
)

s = replace_once(
    s,
    '            && TryGetRegion1RunRoomIndex(activeRunRoom, out _)\n            && CountRegion1MarkedMonsters(activeRunRoom) == 0)\n',
    '            && TryGetRegion1RunRoomIndex(activeRunRoom, out _)\n            && CountRegion1MarkedMonsters(activeRunRoom) == 0\n            && !this.CurrentRegion1NodeNeedsManualInteraction())\n',
    'Lost Cache auto-clear gate'
)

s = replace_once(
    s,
    '        int remaining = CountRegion1MarkedMonsters(location);\n',
    '        if (this.TryHandleRegion1LostCacheInteraction(e, location))\n            return;\n\n        int remaining = CountRegion1MarkedMonsters(location);\n',
    'Lost Cache interaction before route handling'
)

s = replace_once(
    s,
    '        this.ClearRegion1MarkedMonsters(location);\n        this.Region1EliteAuraNextAtMs = 0;\n',
    '        this.ClearRegion1MarkedMonsters(location);\n        this.ClearRegion1LostCacheObject(location);\n        this.Region1EliteAuraNextAtMs = 0;\n',
    'Lost Cache cleanup on room population'
)

old_no_combat = '''        if (encounter is Region1RunEncounterType.Shrine or Region1RunEncounterType.LostCache or Region1RunEncounterType.Moonwell)\n        {\n            this.Monitor.Log($"Region I Hunt Run node {this.Region1RunStep + 1}: {encounter}, no combat spawn.", LogLevel.Trace);\n            return;\n        }\n'''
new_no_combat = '''        if (encounter is Region1RunEncounterType.Shrine or Region1RunEncounterType.LostCache or Region1RunEncounterType.Moonwell)\n        {\n            if (encounter == Region1RunEncounterType.LostCache)\n                this.EnsureRegion1LostCacheChest(location);\n            this.Monitor.Log($"Region I Hunt Run node {this.Region1RunStep + 1}: {encounter}, no combat spawn.", LogLevel.Trace);\n            return;\n        }\n'''
s = replace_once(s, old_no_combat, new_no_combat, 'Lost Cache chest population')

old_rare_draw = '''        Region1RunEncounterType currentEncounter = this.Region1RunEncounters[this.Region1RunStep];\n        if (currentEncounter is Region1RunEncounterType.LostCache or Region1RunEncounterType.Moonwell or Region1RunEncounterType.AncientEcho)\n        {\n            int width = room.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 28;\n            int height = room.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 20;\n            Point rareTile = new(width / 2, Math.Max(5, height / 2));\n            DrawRunChoiceMarker(batch, rareTile, RareEncounterColor(currentEncounter), ModEntry.T($"airship.region1.run.rare.{currentEncounter.ToString().ToLowerInvariant()}.name"));\n        }\n'''
new_rare_draw = '''        Region1RunEncounterType currentEncounter = this.Region1RunEncounters[this.Region1RunStep];\n        if (currentEncounter == Region1RunEncounterType.LostCache)\n        {\n            // 0668C: the cache is a physical chest. No floating name or action hint before interaction.\n            if (!this.Region1RunRewardedSteps.Contains(this.Region1RunStep))\n                return;\n        }\n        else if (currentEncounter is Region1RunEncounterType.Moonwell or Region1RunEncounterType.AncientEcho)\n        {\n            Point rareTile = ResolveRegion1RunRareTile(room);\n            DrawRunChoiceMarker(batch, rareTile, RareEncounterColor(currentEncounter), ModEntry.T($"airship.region1.run.rare.{currentEncounter.ToString().ToLowerInvariant()}.name"));\n        }\n'''
s = replace_once(s, old_rare_draw, new_rare_draw, 'Lost Cache no-floating-label presentation')

# Debug clear should not leave a stale chest behind.
s = replace_once(
    s,
    '        this.HandleRegion1RunNodeCleared(Game1.currentLocation);\n        return $"TEST: cleared node {this.Region1RunStep + 1}/{this.Region1RunTargetNodes}. {this.DescribeHuntRun2()}";\n',
    '        this.HandleRegion1RunNodeCleared(Game1.currentLocation);\n        this.ClearRegion1LostCacheObject(Game1.currentLocation);\n        return $"TEST: cleared node {this.Region1RunStep + 1}/{this.Region1RunTargetNodes}. {this.DescribeHuntRun2()}";\n',
    'debug Lost Cache cleanup'
)

helper_anchor = '    private static Color RouteColor(Region1RunRouteKind route) => route switch\n'
helper_methods = '''    private bool CurrentRegion1NodeNeedsManualInteraction()\n    {\n        if (!this.Region1RunActive || this.Region1RunStep < 0 || this.Region1RunStep >= this.Region1RunEncounters.Length)\n            return false;\n        return this.Region1RunEncounters[this.Region1RunStep] == Region1RunEncounterType.LostCache\n            && !this.Region1RunRewardedSteps.Contains(this.Region1RunStep);\n    }\n\n    private bool TryHandleRegion1LostCacheInteraction(ButtonPressedEventArgs e, GameLocation location)\n    {\n        if (!this.CurrentRegion1NodeNeedsManualInteraction())\n            return false;\n\n        Point cacheTile = ResolveRegion1RunRareTile(location);\n        Point actionTile = GetActionTile();\n        Point cursorTile = new((int)e.Cursor.GrabTile.X, (int)e.Cursor.GrabTile.Y);\n        bool mouseDirect = e.Button == SButton.MouseRight && Touches(cursorTile, cacheTile);\n        if (!Touches(actionTile, cacheTile) && !mouseDirect)\n            return false;\n\n        this.Helper.Input.Suppress(e.Button);\n        Game1.playSound("openBox");\n        this.HandleRegion1RunNodeCleared(location);\n        this.ClearRegion1LostCacheObject(location);\n        Game1.drawObjectDialogue(ModEntry.T("airship.region1.run.rare.lostcache.opened"));\n        return true;\n    }\n\n    private static Point ResolveRegion1RunRareTile(GameLocation room)\n    {\n        int width = room.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 28;\n        int height = room.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 20;\n        return new Point(width / 2, Math.Max(5, height / 2));\n    }\n\n    private void EnsureRegion1LostCacheChest(GameLocation room)\n    {\n        Point tile = ResolveRegion1RunRareTile(room);\n        Vector2 key = new(tile.X, tile.Y);\n        if (room.Objects.TryGetValue(key, out StardewValley.Object? existing))\n        {\n            if (existing is Chest && existing.modData.ContainsKey(Region1LostCacheMarkerKey))\n                return;\n            return;\n        }\n\n        Chest cache = new(true);\n        cache.modData[Region1LostCacheMarkerKey] = "0668C";\n        room.setObject(key, cache);\n    }\n\n    private void ClearRegion1LostCacheObject(GameLocation room)\n    {\n        Point tile = ResolveRegion1RunRareTile(room);\n        Vector2 key = new(tile.X, tile.Y);\n        if (room.Objects.TryGetValue(key, out StardewValley.Object? existing)\n            && existing.modData.ContainsKey(Region1LostCacheMarkerKey))\n        {\n            room.Objects.Remove(key);\n        }\n    }\n\n'''
s = replace_once(s, helper_anchor, helper_methods + helper_anchor, 'Lost Cache interaction helpers')

p.write_text(s, encoding='utf-8')

# -----------------------------------------------------------------------------
# i18n
# -----------------------------------------------------------------------------
def patch_i18n(path: Path, values: dict[str, str]):
    data = json.loads(path.read_text(encoding='utf-8'))
    data.update(values)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

patch_i18n(ROOT / 'i18n' / 'default.json', {
    'boss.verdant.totem.hud': 'TOTEMS {{living}}/4  •  BARRIER {{barrier}}%',
    'boss.verdant.totem.broken': 'A Verdant Seed Totem shattered. {{remaining}} remain. Guardian Barrier: {{barrier}}%.',
    'boss.verdant.totem.all-broken': 'VERDANT BARRIER BROKEN! The Guardian staggers for 1.2 seconds as the final seed totem collapses.',
    'airship.region1.run.rare.lostcache.opened': 'LOST CACHE\nYou open the abandoned supply chest. +4 Scrap and +1 Shiny Scrap are added to this run\'s unbanked rewards.'
})
patch_i18n(ROOT / 'i18n' / 'vi.json', {
    'boss.verdant.totem.hud': 'TRỤ VERDANT {{living}}/4  •  KHIÊN {{barrier}}%',
    'boss.verdant.totem.broken': 'Một Trụ Hạt Verdant đã vỡ. Còn {{remaining}} trụ. Khiên Guardian còn {{barrier}}%.',
    'boss.verdant.totem.all-broken': 'KHIÊN VERDANT ĐÃ VỠ! Guardian choáng rõ rệt trong 1,2 giây khi trụ cuối cùng sụp xuống.',
    'airship.region1.run.rare.lostcache.opened': 'KHO ĐỒ THẤT LẠC\nBạn mở chiếc rương tiếp tế bị bỏ quên. +4 Scrap và +1 Shiny Scrap được cộng vào phần thưởng chưa bank của chuyến săn này.'
})

# -----------------------------------------------------------------------------
# Durable handoff: screenshot-corrected scope is explicit.
# -----------------------------------------------------------------------------
handoff = f'''# Alpha28 0668C - Mechanic Clarity Hotfix\n\nBuild: `{VERSION}`\nBranch: `cardcha-alpha28-0668c-mechanic-clarity-hotfix`\nStatus: CI/package pending until workflow completes; in-game acceptance pending.\n\n## Screenshot-corrected issue identity\nThe screenshot labeled `KHO ĐỒ THẤT LẠC` was a Hunt Run `LostCache` rare encounter, not the Sky Dock Lost & Found point. 0668C fixes the actual Hunt Run room behavior.\n\n## Implemented\n### Verdant Seed Totems\n- Balance frozen: 4 x 90 HP, barrier 15/10/6/3/0%, >=2 totems keeps the existing Root/Vine ~8% cooldown acceleration, final stagger remains exactly 1.2s.\n- Vanilla GreenSlime totem proxy is hidden.\n- Boss HUD now shows living Totems and current Barrier percentage.\n- Stronger per-totem hit flash and floating damage feedback.\n- Dead totem proxies are pruned from the arena actor list so they cannot remain live targets.\n- Each break reports the new barrier percentage.\n- Final break adds a strong camera/sound/world burst while preserving the existing 1.2s state-machine stagger.\n\n### Hunt Run Lost Cache\n- LostCache no longer auto-clears merely because the room has zero monsters.\n- A physical Stardew Chest is spawned at the rare-room interaction point.\n- No floating `KHO ĐỒ THẤT LẠC` name or button hint is shown before interaction.\n- Adjacent action/controller input and direct mouse right-click can claim the cache.\n- Only after interaction are +4 Scrap and +1 Shiny Scrap granted to the run's unbanked reward pool and the node becomes cleared.\n- Route/boon progression stays hidden until the cache is actually opened.\n\n## Preserved from 0668B\n- Adrenaline and the other timed Cardcha HUD runtime states remain unchanged.\n- Persistent READY clutter remains hidden.\n- Verdant Core separate READY panel remains hidden; gameplay remains active.\n\n## Explicitly out of scope\n- Verdant Guardian native-size art overhaul.\n- Guardian Rabbit / ChaCha boss-form art overhaul.\n- Airship/Sky Dock redesign.\n- Full Region I environment redesign.\n- Briarling/Leaf Wisp native-size redraw.\nThese remain 0669 work after 0668C in-game mechanic acceptance.\n\n## TEST handoff\n### Prerequisites\n- Load a save with Cardcha available.\n- Normal Boss I access still follows established Region I/Boss I progression.\n- LostCache is a Hunt Run rare encounter and normally appears from later run nodes according to the existing rare-room roll.\n\n### Debug bypass\n- Boss I direct test: `cardcha_test_boss1`.\n- Totem diagnostic: `cardcha_boss1_totem_status`.\n- Timed HUD diagnostic: `cardcha_hud_runtime_status`.\n- Hunt Run diagnostic: `cardcha_huntrun_status`.\n- `cardcha_huntrun_clear` remains a test-only combat/node bypass and intentionally bypasses the physical-cache acceptance path.\n\n### Verify\n1. Boss I has four custom Verdant totems with no visible vanilla slime proxy.\n2. Damage one totem repeatedly: HP bar, hit flash and damage number follow the correct totem.\n3. Break one: broken state remains visible, live target disappears, HUD Barrier percentage drops.\n4. Break all four: the final break produces an unmistakable 1.2s Guardian stagger.\n5. In a Hunt Run LostCache room, the center is a physical chest, with no idle floating `KHO ĐỒ THẤT LẠC` label.\n6. Before opening the chest, route choices must not become available.\n7. Interact by controller/action or right-click: chest resolves, reward message appears, then route/boon progression becomes available.\n8. Equip Adrenaline, kill a monster and confirm its approximately 3.0s timed HUD icon still appears.\n'''
Path('handoff/ALPHA28_0668C_MECHANIC_CLARITY_HOTFIX.md').write_text(handoff, encoding='utf-8')
Path('handoff/LATEST_CARDCHA_HANDOFF.md').write_text(
    f'''# Latest Cardcha Handoff\n\nCurrent branch: `cardcha-alpha28-0668c-mechanic-clarity-hotfix`\nCurrent build: `{VERSION}`\nContinue from: `handoff/ALPHA28_0668C_MECHANIC_CLARITY_HOTFIX.md`\n\nDo not resume from stale `main` or 0668B. 0669 must fork from accepted 0668C after in-game mechanic acceptance.\n''',
    encoding='utf-8'
)

print(f'0668C generator complete: {VERSION}')
