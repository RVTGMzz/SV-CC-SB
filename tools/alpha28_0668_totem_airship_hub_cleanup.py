from pathlib import Path
from PIL import Image, ImageDraw
import json, re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.35'
PREV = '0.3.0-alpha.28.0.4.14.4.5.12.34'

# ---------- version ----------
manifest_path = ROOT/'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['Version'] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
for rel in ['Cardcha.csproj','Directory.Build.targets']:
    p=ROOT/rel
    s=p.read_text(encoding='utf-8').replace(PREV, VERSION)
    p.write_text(s,encoding='utf-8')

# ---------- pixel-art assets ----------
# Totem sheet: 4 frames, 32x48. intact / cracked / critical / broken burst.
arena_dir = ROOT/'assets'/'bosses'/'verdant_guardian'/'arena'
arena_dir.mkdir(parents=True,exist_ok=True)
W,H=32,48
totem = Image.new('RGBA',(W*4,H),(0,0,0,0))
for frame in range(4):
    d=ImageDraw.Draw(totem)
    ox=frame*W
    if frame<3:
        # roots/stone base
        d.rectangle((ox+7,38,ox+24,43), fill=(55,46,33,255))
        d.rectangle((ox+4,43,ox+27,46), fill=(38,34,27,255))
        d.rectangle((ox+10,21,ox+21,39), fill=(80,63,40,255))
        d.rectangle((ox+8,24,ox+23,34), fill=(97,75,43,255))
        d.rectangle((ox+11,14,ox+20,24), fill=(61,82,45,255))
        # leaf shoulders so it reads as a rooted object, not a creature
        d.polygon([(ox+8,23),(ox+2,18),(ox+4,28),(ox+10,31)], fill=(63,113,58,255))
        d.polygon([(ox+23,23),(ox+29,18),(ox+27,28),(ox+21,31)], fill=(63,113,58,255))
        # glowing seed core
        core=(127,232,103,255) if frame==0 else (201,210,91,255) if frame==1 else (239,151,76,255)
        d.polygon([(ox+16,15),(ox+22,22),(ox+20,30),(ox+16,34),(ox+12,30),(ox+10,22)], fill=core)
        d.rectangle((ox+14,20,ox+17,26), fill=(224,255,174,255))
        # rune bands
        d.rectangle((ox+9,35,ox+22,36), fill=(139,143,82,255))
        if frame>=1:
            d.line((ox+14,18,ox+18,24,ox+13,30), fill=(72,46,33,255), width=1)
        if frame>=2:
            d.line((ox+21,22,ox+17,29,ox+22,34), fill=(72,46,33,255), width=2)
            d.rectangle((ox+4,39,ox+8,42), fill=(97,75,43,255))
    else:
        d.rectangle((ox+6,42,ox+25,46), fill=(38,34,27,255))
        d.rectangle((ox+10,37,ox+21,42), fill=(74,57,37,255))
        # shattered core/leaf pixels
        for x,y,c in [(16,22,(190,255,128,255)),(7,26,(99,178,77,255)),(25,28,(99,178,77,255)),(12,15,(144,223,101,255)),(22,17,(213,246,137,255)),(5,34,(86,111,56,255)),(27,35,(86,111,56,255))]:
            d.rectangle((ox+x-1,y-1,ox+x+1,y+1),fill=c)
totem.save(arena_dir/'verdant_seed_totem.png')

# Airship hub decor atlas, 4x3 cells at 32px, authored chunky Stardew-ish pixel art.
cell=32
hub=Image.new('RGBA',(cell*4,cell*3),(0,0,0,0))
def box(col,row,rect,color):
    d=ImageDraw.Draw(hub); x0=col*cell; y0=row*cell
    r=(x0+rect[0],y0+rect[1],x0+rect[2],y0+rect[3]); d.rectangle(r,fill=color)
def line(col,row,pts,color,w=1):
    d=ImageDraw.Draw(hub); x0=col*cell; y0=row*cell
    d.line([(x0+x,y0+y) for x,y in pts],fill=color,width=w)
# 0 crate
box(0,0,(5,8,26,27),(120,74,39,255)); box(0,0,(7,10,24,25),(164,102,51,255)); line(0,0,[(7,10),(24,25)],(91,55,32,255),2); line(0,0,[(24,10),(7,25)],(91,55,32,255),2)
# 1 barrel
box(1,0,(9,6,23,28),(104,64,38,255)); box(1,0,(7,10,25,24),(143,88,46,255)); box(1,0,(7,11,25,13),(70,57,48,255)); box(1,0,(7,22,25,24),(70,57,48,255))
# 2 bookcase
box(2,0,(5,3,27,29),(81,50,34,255)); box(2,0,(7,5,25,27),(118,70,40,255)); box(2,0,(8,10,24,11),(58,40,32,255)); box(2,0,(8,19,24,20),(58,40,32,255))
for i,c in enumerate([(124,54,48,255),(60,104,130,255),(159,126,55,255),(87,121,67,255)]): box(2,0,(9+i*4,6,11+i*4,10),c); box(2,0,(9+i*4,15,11+i*4,19),c)
# 3 work table
box(3,0,(4,10,28,16),(143,88,48,255)); box(3,0,(7,16,10,28),(83,52,36,255)); box(3,0,(22,16,25,28),(83,52,36,255)); box(3,0,(8,7,15,10),(206,186,128,255)); box(3,0,(18,8,24,10),(91,135,117,255))
# 4 map board
box(0,1,(5,4,27,27),(79,52,38,255)); box(0,1,(7,6,25,24),(202,181,119,255)); line(0,1,[(10,19),(14,14),(18,16),(22,10)],(84,129,116,255),2); box(0,1,(12,9,14,11),(156,80,58,255)); box(0,1,(20,18,22,20),(156,80,58,255))
# 5 rug
box(1,1,(3,8,29,25),(104,53,74,255)); box(1,1,(5,10,27,23),(160,83,91,255)); box(1,1,(8,13,24,20),(199,139,91,255)); box(1,1,(10,15,22,18),(92,104,87,255))
# 6 lost-found chest
box(2,1,(5,12,27,28),(76,48,35,255)); box(2,1,(6,9,26,15),(128,78,43,255)); box(2,1,(8,14,24,26),(158,99,49,255)); box(2,1,(15,16,18,21),(218,174,75,255)); box(2,1,(7,23,25,25),(98,59,38,255))
# 7 brass lamp
box(3,1,(15,5,17,25),(116,78,46,255)); box(3,1,(10,24,22,27),(77,52,38,255)); box(3,1,(11,7,21,15),(194,139,59,255)); box(3,1,(13,8,19,13),(244,216,128,255))
# 8 rope coil
for r in [11,8,5]:
    d=ImageDraw.Draw(hub); ox=0; oy=2*cell; d.ellipse((ox+16-r,oy+17-r,ox+16+r,oy+17+r),outline=(157,120,74,255),width=2)
# 9 fern pot
box(1,2,(11,21,21,28),(125,73,43,255)); line(1,2,[(16,21),(16,10)],(68,112,59,255),2); line(1,2,[(16,13),(10,8)],(68,135,69,255),3); line(1,2,[(16,15),(23,9)],(83,153,74,255),3); line(1,2,[(16,18),(9,15)],(80,145,68,255),3)
# 10 sacks
box(2,2,(5,16,16,28),(168,142,91,255)); box(2,2,(15,13,27,28),(182,153,98,255)); box(2,2,(8,14,13,17),(126,103,70,255)); box(2,2,(18,11,23,15),(126,103,70,255))
# 11 little card shelf
box(3,2,(5,7,27,28),(74,50,39,255)); box(3,2,(7,9,25,26),(110,71,43,255)); box(3,2,(8,15,24,16),(52,39,34,255));
for i,c in enumerate([(82,157,135,255),(151,95,166,255),(202,153,68,255)]): box(3,2,(10+i*5,10,12+i*5,14),c)
hub.save(ROOT/'assets'/'airship_hub_decor.png')

# Region I edge decor atlas 4 cells.
forest=Image.new('RGBA',(128,32),(0,0,0,0)); d=ImageDraw.Draw(forest)
# fern, flowers, stone, stump
# fern
for pts in [[(15,27),(15,11)],[(15,18),(7,11)],[(15,20),(24,12)],[(15,23),(6,19)],[(15,24),(25,20)]]: d.line(pts,fill=(52,116,57,255),width=2)
# flowers
ox=32; d.line((ox+15,27,ox+15,14),fill=(55,121,58,255),width=2)
for dx,dy,c in [(-5,13,(234,185,106,255)),(0,10,(220,132,170,255)),(5,14,(196,219,116,255))]: d.rectangle((ox+15+dx-2,dy-2,ox+15+dx+2,dy+2),fill=c)
# stone
ox=64; d.polygon([(ox+5,25),(ox+8,15),(ox+15,10),(ox+24,14),(ox+28,24),(ox+22,28),(ox+10,28)],fill=(101,107,91,255)); d.polygon([(ox+9,17),(ox+15,12),(ox+22,15),(ox+18,19)],fill=(140,145,119,255))
# stump
ox=96; d.rectangle((ox+9,15,ox+23,28),fill=(93,62,39,255)); d.ellipse((ox+8,11,ox+24,19),fill=(141,95,50,255)); d.ellipse((ox+11,13,ox+21,17),outline=(84,57,38,255),width=1); d.line((ox+12,22,ox+7,27),fill=(77,83,43,255),width=2); d.line((ox+22,22,ox+27,27),fill=(77,83,43,255),width=2)
forest.save(ROOT/'assets'/'region1_environment_decor.png')

# ---------- Boss service: destructible totems ----------
p=ROOT/'Services'/'VerdantGuardianBossService.cs'; s=p.read_text(encoding='utf-8')
s=s.replace('    Victory\n}', '    Victory,\n    TotemStagger\n}', 1)
s=s.replace('    public const string BossAddTypeKey = "Ronvotri.Cardcha/VerdantGuardianAddType";\n', '    public const string BossAddTypeKey = "Ronvotri.Cardcha/VerdantGuardianAddType";\n    public const string TotemMarkerKey = "Ronvotri.Cardcha/VerdantSeedTotem";\n    public const string TotemIndexKey = "Ronvotri.Cardcha/VerdantSeedTotemIndex";\n',1)
s=s.replace('    private const int MaxActiveAdds = 4;\n', '    private const int MaxActiveAdds = 4;\n    private const int TotemMaxHealth = 90;\n    private const int TotemStaggerDurationMs = 1200;\n',1)
s=s.replace('    private static readonly Point[] AddSpawnTiles = { new(5, 5), new(22, 5), new(5, 14), new(22, 14) };\n', '    private static readonly Point[] AddSpawnTiles = { new(5, 5), new(22, 5), new(5, 14), new(22, 14) };\n    private static readonly Point[] TotemTiles = { new(3, 3), new(24, 3), new(3, 16), new(24, 16) };\n',1)
s=s.replace('    private Random EncounterRandom = new(1);\n', '    private Random EncounterRandom = new(1);\n    private int LastLivingTotemCount;\n    private long LastTotemHitAtMs;\n    private int LastTotemHitIndex = -1;\n',1)
s=s.replace('    internal Monster[] VisualAdds => Game1.getLocationFromName(LocationName)?.characters.OfType<Monster>()\n        .Where(m => m.Health > 0 && m.modData.ContainsKey(BossAddMarkerKey)).ToArray() ?? Array.Empty<Monster>();\n', '    internal Monster[] VisualAdds => Game1.getLocationFromName(LocationName)?.characters.OfType<Monster>()\n        .Where(m => m.Health > 0 && m.modData.ContainsKey(BossAddMarkerKey)).ToArray() ?? Array.Empty<Monster>();\n    internal Monster[] VisualTotems => Game1.getLocationFromName(LocationName)?.characters.OfType<Monster>()\n        .Where(m => m.Health > 0 && m.modData.ContainsKey(TotemMarkerKey)).ToArray() ?? Array.Empty<Monster>();\n    internal long VisualLastTotemHitAtMs => this.LastTotemHitAtMs;\n    internal int VisualLastTotemHitIndex => this.LastTotemHitIndex;\n',1)
# Insert totem update after now.
anchor='''        long now = Environment.TickCount64;\n        if (this.State == VerdantGuardianState.Victory)'''
replacement='''        long now = Environment.TickCount64;\n        this.UpdateTotemAnchors();\n        this.ObserveTotemBreaks(now);\n        if (this.State == VerdantGuardianState.Victory)'''
if anchor not in s: raise RuntimeError('boss update anchor missing')
s=s.replace(anchor,replacement,1)
# Add TotemStagger switch case before phase transition.
anchor='''            case VerdantGuardianState.PhaseTransition:\n                boss.Position = BossSpawnPosition();'''
replacement='''            case VerdantGuardianState.TotemStagger:\n                boss.Position = this.HeavyAnchor;\n                if (now - this.StateStartedAtMs >= TotemStaggerDurationMs)\n                    this.EnterDecision(now, 420);\n                break;\n            case VerdantGuardianState.PhaseTransition:\n                boss.Position = BossSpawnPosition();'''
s=s.replace(anchor,replacement,1)
# Spawn at encounter start.
s=s.replace('''        arena.characters.Add(proxy);\n        this.BossProxy = proxy;''','''        arena.characters.Add(proxy);\n        this.BossProxy = proxy;\n        this.SpawnTotems(arena);''',1)
s=s.replace('''        this.VictoryHandled = false;\n        this.RootTargets = Array.Empty<Point>();''','''        this.VictoryHandled = false;\n        this.LastLivingTotemCount = 4;\n        this.LastTotemHitAtMs = 0;\n        this.LastTotemHitIndex = -1;\n        this.RootTargets = Array.Empty<Point>();''',1)
# cooldown assignment
s=s.replace('''        this.CooldownUntil[selected] = now + CooldownMs(selected, this.Phase);''','''        this.CooldownUntil[selected] = now + this.GetAttackCooldownMs(selected, this.Phase);''',1)
# Begin defeat removes totems
s=s.replace('''        this.RemoveAdds();\n        Game1.playSound("thudStep");''','''        this.RemoveAdds();\n        this.RemoveTotems();\n        Game1.playSound("thudStep");''',1)
# reset totem runtime
s=s.replace('''        this.HeavyAnchor = Vector2.Zero;\n        this.CooldownUntil.Clear();''','''        this.HeavyAnchor = Vector2.Zero;\n        this.LastLivingTotemCount = 0;\n        this.LastTotemHitAtMs = 0;\n        this.LastTotemHitIndex = -1;\n        this.CooldownUntil.Clear();''',1)
# remove boss actors include totem
s=s.replace('''n.modData.ContainsKey(BossMarkerKey) || n.modData.ContainsKey(BossAddMarkerKey)''','''n.modData.ContainsKey(BossMarkerKey) || n.modData.ContainsKey(BossAddMarkerKey) || n.modData.ContainsKey(TotemMarkerKey)''',1)
# Insert totem methods before cooldown helper.
anchor='''    private static int CooldownMs(VerdantGuardianAttack attack, int phase) => attack switch\n'''
methods=r'''    private void SpawnTotems(GameLocation arena)
    {
        for (int i = 0; i < TotemTiles.Length; i++)
        {
            Point tile = TotemTiles[i];
            GreenSlime proxy = new(new Vector2(tile.X * 64f, tile.Y * 64f), 0)
            {
                MaxHealth = TotemMaxHealth,
                Health = TotemMaxHealth,
                Speed = 0
            };
            proxy.modData[TotemMarkerKey] = "verdant-seed-totem";
            proxy.modData[TotemIndexKey] = i.ToString();
            // Keep the proxy targetable for companions. Its vanilla draw is suppressed by Harmony.
            proxy.isInvisible.Value = false;
            arena.characters.Add(proxy);
        }
    }

    private void UpdateTotemAnchors()
    {
        GameLocation? arena = Game1.getLocationFromName(LocationName);
        if (arena is null) return;
        foreach (Monster totem in arena.characters.OfType<Monster>().Where(m => m.Health > 0 && m.modData.ContainsKey(TotemMarkerKey)))
        {
            if (!totem.modData.TryGetValue(TotemIndexKey, out string? raw) || !int.TryParse(raw, out int index)) index = 0;
            index = Math.Clamp(index, 0, TotemTiles.Length - 1);
            Point tile = TotemTiles[index];
            totem.Position = new Vector2(tile.X * 64f, tile.Y * 64f);
            totem.Speed = 0;
            totem.Halt();
        }
    }

    private void ObserveTotemBreaks(long now)
    {
        if (this.State is VerdantGuardianState.Dormant or VerdantGuardianState.Defeated or VerdantGuardianState.Victory)
            return;
        int living = this.GetLivingTotemCount();
        if (living < this.LastLivingTotemCount)
        {
            int broken = this.LastLivingTotemCount - living;
            Game1.playSound("woodWhack");
            Game1.showGlobalMessage(ModEntry.T("boss.verdant.totem.broken", new { remaining = living }));
            this.Monitor.Log($"Verdant Seed Totem broken x{broken}; remaining={living}; barrier={this.GetTotemDamageReductionPercent()}%.", LogLevel.Trace);
            if (living == 0)
            {
                this.State = VerdantGuardianState.TotemStagger;
                this.StateStartedAtMs = now;
                this.AttackApplied = false;
                this.RootTargets = Array.Empty<Point>();
                this.PendingSummonTiles = Array.Empty<Point>();
                this.PendingSummonKinds = Array.Empty<string>();
                Game1.playSound("explosion");
                Game1.showGlobalMessage(ModEntry.T("boss.verdant.totem.all-broken"));
            }
        }
        this.LastLivingTotemCount = living;
    }

    internal int ModifyBossIncomingDamage(int damage)
    {
        if (damage <= 0) return damage;
        int reduction = this.GetTotemDamageReductionPercent();
        return reduction <= 0 ? damage : Math.Max(1, (int)Math.Round(damage * (1d - reduction / 100d), MidpointRounding.AwayFromZero));
    }

    internal void NotifyTotemHit(Monster monster, int previousHealth)
    {
        if (!monster.modData.ContainsKey(TotemMarkerKey) || previousHealth <= monster.Health) return;
        this.LastTotemHitAtMs = Environment.TickCount64;
        if (monster.modData.TryGetValue(TotemIndexKey, out string? raw) && int.TryParse(raw, out int index))
            this.LastTotemHitIndex = Math.Clamp(index, 0, TotemTiles.Length - 1);
    }

    internal int GetLivingTotemCount()
        => Game1.getLocationFromName(LocationName)?.characters.OfType<Monster>()
            .Count(m => m.Health > 0 && m.modData.ContainsKey(TotemMarkerKey)) ?? 0;

    internal int GetTotemDamageReductionPercent()
        => this.GetLivingTotemCount() switch { >= 4 => 15, 3 => 10, 2 => 6, 1 => 3, _ => 0 };

    private int GetAttackCooldownMs(VerdantGuardianAttack attack, int phase)
    {
        int ms = CooldownMs(attack, phase);
        if (this.GetLivingTotemCount() >= 2 && attack is VerdantGuardianAttack.RootSpikes or VerdantGuardianAttack.VineTrap)
            ms = (int)Math.Round(ms * 0.92d);
        return ms;
    }

    private void RemoveTotems()
    {
        GameLocation? arena = Game1.getLocationFromName(LocationName);
        if (arena is null) return;
        foreach (NPC actor in arena.characters.Where(n => n.modData.ContainsKey(TotemMarkerKey)).ToList())
            arena.characters.Remove(actor);
    }

'''
if anchor not in s: raise RuntimeError('cooldown anchor missing')
s=s.replace(anchor,methods+anchor,1)
# describe balance
s=s.replace('$"HeavyRecoilCap={HeavyRecoilCapPixels:0}px Recenter={HeavyRecenterFactor:0.00} | AddsMax={MaxActiveAdds}";', '$"HeavyRecoilCap={HeavyRecoilCapPixels:0}px Recenter={HeavyRecenterFactor:0.00} | AddsMax={MaxActiveAdds} | Totems={this.GetLivingTotemCount()}/4 Barrier={this.GetTotemDamageReductionPercent()}% TotemHP={TotemMaxHealth}";',1)
p.write_text(s,encoding='utf-8')

# ---------- damage patch: barrier + targetable fixed totems ----------
p=ROOT/'Patches'/'MonsterDamagePatch.cs'; s=p.read_text(encoding='utf-8')
s=s.replace('    private static CardTestArenaService? TestArena;\n', '    private static CardTestArenaService? TestArena;\n    private static VerdantGuardianBossService? VerdantBoss;\n',1)
s=s.replace('public static void Apply(Harmony harmony, CombatService combat, MonsterDeathService deaths, CardTestArenaService? testArena = null)', 'public static void Apply(Harmony harmony, CombatService combat, MonsterDeathService deaths, CardTestArenaService? testArena, VerdantGuardianBossService verdantBoss)',1)
s=s.replace('        TestArena = testArena;\n', '        TestArena = testArena;\n        VerdantBoss = verdantBoss;\n',1)
s=s.replace('''            bool isVerdantGuardian = __instance.modData.ContainsKey(VerdantGuardianBossService.BossMarkerKey);\n''','''            bool isVerdantGuardian = __instance.modData.ContainsKey(VerdantGuardianBossService.BossMarkerKey);\n            bool isVerdantTotem = __instance.modData.ContainsKey(VerdantGuardianBossService.TotemMarkerKey);\n''',1)
s=s.replace('''            // 0665: receive 8% of final trajectory, then hard-cap it. The boss service recenters\n''','''            if (isVerdantGuardian && VerdantBoss is not null)\n                damage = VerdantBoss.ModifyBossIncomingDamage(damage);\n\n            if (isVerdantTotem)\n            {\n                xTrajectory = 0;\n                yTrajectory = 0;\n            }\n\n            // 0665: receive 8% of final trajectory, then hard-cap it. The boss service recenters\n''',1)
s=s.replace('''            Combat?.AfterMonsterTakesDamage(__instance, who, __state);\n            if (__state > 0 && __instance.Health <= 0)\n                Deaths?.HandleDeath(__instance, who, __instance.currentLocation);''','''            Combat?.AfterMonsterTakesDamage(__instance, who, __state);\n            VerdantBoss?.NotifyTotemHit(__instance, __state);\n            if (__state > 0 && __instance.Health <= 0 && !__instance.modData.ContainsKey(VerdantGuardianBossService.TotemMarkerKey))\n                Deaths?.HandleDeath(__instance, who, __instance.currentLocation);''',1)
p.write_text(s,encoding='utf-8')

# Suppress GreenSlime proxy art for boss + totems without setting them invisible (companions can target).
p=ROOT/'Patches'/'VerdantGuardianProxyDrawPatch.cs'; s=p.read_text(encoding='utf-8')
s=s.replace('''    private static bool Prefix(GreenSlime __instance)\n        => !__instance.modData.ContainsKey(VerdantGuardianBossService.BossMarkerKey);''','''    private static bool Prefix(GreenSlime __instance)\n        => !__instance.modData.ContainsKey(VerdantGuardianBossService.BossMarkerKey)\n           && !__instance.modData.ContainsKey(VerdantGuardianBossService.TotemMarkerKey);''',1)
p.write_text(s,encoding='utf-8')

# Skip Cardcha loot/material pipeline for support totems.
p=ROOT/'Services'/'MonsterDeathService.cs'; s=p.read_text(encoding='utf-8')
anchor='''        if (monster.modData.ContainsKey(DeathHandledKey))\n            return;\n\n        monster.modData[DeathHandledKey] = "1";'''
replacement='''        if (monster.modData.ContainsKey(DeathHandledKey))\n            return;\n\n        monster.modData[DeathHandledKey] = "1";\n        if (monster.modData.ContainsKey(VerdantGuardianBossService.TotemMarkerKey))\n            return;'''
if anchor not in s: raise RuntimeError('death anchor missing')
s=s.replace(anchor,replacement,1)
p.write_text(s,encoding='utf-8')

# ---------- arena polish: render actual destructible totems ----------
p=ROOT/'Services'/'VerdantGuardianArenaPolishService.cs'; s=p.read_text(encoding='utf-8')
# Replace old fixed obelisk drawing method body using regex through next method.
pattern=r'''    private void DrawObelisks\(SpriteBatch batch\)\n    \{.*?\n    \}\n\n    private void DrawRetreatGlyph'''
replacement=r'''    private void DrawObelisks(SpriteBatch batch)
    {
        Texture2D? texture = this.Load("verdant_seed_totem.png");
        if (texture is null || texture.Width < 128 || texture.Height < 48)
            return;

        Monster[] living = this.Boss.VisualTotems;
        HashSet<int> livingIndices = new();
        foreach (Monster totem in living)
        {
            if (!totem.modData.TryGetValue(VerdantGuardianBossService.TotemIndexKey, out string? raw) || !int.TryParse(raw, out int index))
                index = 0;
            index = Math.Clamp(index, 0, ObeliskTiles.Length - 1);
            livingIndices.Add(index);
            float hp = totem.MaxHealth <= 0 ? 0f : Math.Clamp(totem.Health / (float)totem.MaxHealth, 0f, 1f);
            int frame = hp > 0.66f ? 0 : hp > 0.33f ? 1 : 2;
            Rectangle src = new(frame * 32, 0, 32, 48);
            Point tile = ObeliskTiles[index];
            Vector2 world = new(tile.X * 64f + 32f, tile.Y * 64f + 64f);
            Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
            float pulse = 0.94f + 0.04f * (float)Math.Sin(Environment.TickCount64 / 240d + index);
            float flash = index == this.Boss.VisualLastTotemHitIndex && Environment.TickCount64 - this.Boss.VisualLastTotemHitAtMs < 130 ? 0.45f : 0f;
            Color tint = Color.Lerp(Color.White, new Color(255, 237, 156), flash);
            float layer = Math.Clamp((world.Y + 56f) / 10000f, 0f, 0.94f);
            batch.Draw(texture, local, src, tint, 0f, new Vector2(16f, 47f), 2.15f * pulse, SpriteEffects.None, layer);

            // visible HP strip makes it unmistakably destructible without a floating name label.
            int barW = 54;
            int barX = (int)local.X - barW / 2;
            int barY = (int)local.Y + 7;
            batch.Draw(Game1.staminaRect, new Rectangle(barX, barY, barW, 5), Color.Black * 0.65f);
            batch.Draw(Game1.staminaRect, new Rectangle(barX + 1, barY + 1, Math.Max(1, (int)((barW - 2) * hp)), 3), new Color(119, 211, 92) * 0.92f);
        }

        // Broken stumps remain so the arena still tells the story of what the party destroyed.
        Rectangle brokenSrc = new(3 * 32, 0, 32, 48);
        for (int i = 0; i < ObeliskTiles.Length; i++)
        {
            if (livingIndices.Contains(i)) continue;
            Point tile = ObeliskTiles[i];
            Vector2 world = new(tile.X * 64f + 32f, tile.Y * 64f + 64f);
            Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
            batch.Draw(texture, local, brokenSrc, Color.White * 0.76f, 0f, new Vector2(16f, 47f), 2.15f, SpriteEffects.None,
                Math.Clamp((world.Y + 56f) / 10000f, 0f, 0.94f));
        }
    }

    private void DrawRetreatGlyph'''
s2,n=re.subn(pattern,replacement,s,flags=re.S)
if n!=1: raise RuntimeError(f'obelisk replace count={n}')
s=s2
s=s.replace('ArenaSeal=ON | Obelisks=4 | Motes=ON | IntroBars=ON', 'ArenaSeal=ON | DestructibleTotems={this.Boss.GetLivingTotemCount()}/4 | Barrier={this.Boss.GetTotemDamageReductionPercent()}% | Motes=ON | IntroBars=ON',1)
p.write_text(s,encoding='utf-8')

# ---------- airship renderer: warm clutter, no floating lost-found label ----------
p=ROOT/'Services'/'AirshipInteriorStardewRenderer.cs'; s=p.read_text(encoding='utf-8')
s=s.replace('    private const string UpgradeAtlasPath = "assets/airship_upgrade_visuals.png";\n', '    private const string UpgradeAtlasPath = "assets/airship_upgrade_visuals.png";\n    private const string HubDecorAtlasPath = "assets/airship_hub_decor.png";\n',1)
s=s.replace('    private static bool AtlasLoadFailed;\n', '    private static bool AtlasLoadFailed;\n    private static Texture2D? HubDecorAtlas;\n    private static bool HubDecorLoadFailed;\n',1)
s=s.replace('''        float phase = (float)(Environment.TickCount64 / 1000.0);\n        DrawWindowMagic(batch, phase);''','''        float phase = (float)(Environment.TickCount64 / 1000.0);\n        DrawDeckStardewDecor(batch);\n        DrawWindowMagic(batch, phase);''',1)
s=s.replace('''        float phase = (float)(Environment.TickCount64 / 1000.0);\n        DrawDockMagic(batch, phase);''','''        float phase = (float)(Environment.TickCount64 / 1000.0);\n        DrawDockStardewDecor(batch);\n        DrawDockMagic(batch, phase);''',1)
# insert methods before DrawWindowMagic
anchor='''    private static void DrawWindowMagic(SpriteBatch batch, float phase)\n'''
decor_methods=r'''    private static void DrawDeckStardewDecor(SpriteBatch batch)
    {
        Texture2D? atlas = GetHubDecorAtlas();
        if (atlas is null) return;
        // Warm, asymmetrical lived-in clutter. Keep the center/upgrade sockets readable.
        DrawDecor(batch, atlas, 2,0, new Point(2,5), 2f);   // bookcase
        DrawDecor(batch, atlas, 0,1, new Point(11,3), 2f);  // wall map
        DrawDecor(batch, atlas, 3,0, new Point(6,7), 2f);   // work table
        DrawDecor(batch, atlas, 3,2, new Point(16,7), 2f);  // card shelf
        DrawDecor(batch, atlas, 0,0, new Point(2,10), 2f);  // crate
        DrawDecor(batch, atlas, 1,0, new Point(20,10), 2f); // barrel
        DrawDecor(batch, atlas, 2,2, new Point(18,4), 2f);  // sacks
        DrawDecor(batch, atlas, 1,2, new Point(4,4), 2f);   // fern
        DrawDecor(batch, atlas, 3,1, new Point(21,5), 2f);  // lamp
        DrawDecor(batch, atlas, 1,1, new Point(9,8), 4.1f, 112, 64); // broad rug
    }

    private static void DrawDockStardewDecor(SpriteBatch batch)
    {
        Texture2D? atlas = GetHubDecorAtlas();
        if (atlas is null) return;
        // Boarding deck gains cargo, rope and lanterns so it reads as a working airship gangway.
        DrawDecor(batch, atlas, 0,0, new Point(3,10), 2f);
        DrawDecor(batch, atlas, 2,1, new Point(5,11), 2f); // Lost & Found chest, no floating label.
        DrawDecor(batch, atlas, 0,2, new Point(7,12), 2f);
        DrawDecor(batch, atlas, 2,2, new Point(22,10), 2f);
        DrawDecor(batch, atlas, 1,0, new Point(24,11), 2f);
        DrawDecor(batch, atlas, 3,1, new Point(3,6), 2f);
        DrawDecor(batch, atlas, 3,1, new Point(26,6), 2f);
        DrawDecor(batch, atlas, 1,2, new Point(8,6), 2f);
    }

    private static void DrawDecor(SpriteBatch batch, Texture2D atlas, int col, int row, Point tile, float scale, int destW = 0, int destH = 0)
    {
        Rectangle src = new(col * 32, row * 32, 32, 32);
        Vector2 local = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 58f);
        if (destW > 0 && destH > 0)
        {
            batch.Draw(atlas, new Rectangle((int)local.X - destW/2, (int)local.Y - destH, destW, destH), src, Color.White);
            return;
        }
        batch.Draw(atlas, local, src, Color.White, 0f, new Vector2(16f, 31f), scale, SpriteEffects.None, 0.92f);
    }

    private static Texture2D? GetHubDecorAtlas()
    {
        if (HubDecorAtlas is not null && !HubDecorAtlas.IsDisposed) return HubDecorAtlas;
        HubDecorAtlas = null;
        if (HubDecorLoadFailed || ModEntry.StaticHelper is null) return null;
        try { HubDecorAtlas = ModEntry.StaticHelper.ModContent.Load<Texture2D>(HubDecorAtlasPath); return HubDecorAtlas; }
        catch { HubDecorLoadFailed = true; return null; }
    }

'''
if anchor not in s: raise RuntimeError('renderer anchor missing')
s=s.replace(anchor,decor_methods+anchor,1)
p.write_text(s,encoding='utf-8')

# ---------- Region I light forest edge decoration renderer ----------
region_renderer=r'''using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewValley;

namespace Cardcha.Services;

/// <summary>0668 light edge-decoration pass. It stays out of central combat lanes and does not alter collision/TMX.</summary>
internal static class Region1StardewDecorRenderer
{
    private const string AtlasPath = "assets/region1_environment_decor.png";
    private static Texture2D? Atlas;
    private static bool LoadFailed;

    public static void Draw(SpriteBatch batch, GameLocation room, int roomIndex)
    {
        Texture2D? atlas = GetAtlas();
        if (atlas is null) return;
        int width = room.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 28;
        int height = room.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 20;
        Point[] points =
        {
            new(3,4), new(width-4,4), new(4,height-5), new(width-5,height-5),
            new(7,3), new(width-8,3), new(6,height-3), new(width-7,height-3)
        };
        for (int i=0;i<points.Length;i++)
        {
            Point t=points[i];
            int sprite=(roomIndex*3+i)%4;
            Rectangle src=new(sprite*32,0,32,32);
            Vector2 world=new(t.X*64f+32f,t.Y*64f+58f);
            Vector2 local=Game1.GlobalToLocal(Game1.viewport,world);
            float scale = sprite==2 ? 1.35f : 1.65f;
            batch.Draw(atlas,local,src,Color.White,0f,new Vector2(16f,31f),scale,SpriteEffects.None,0.035f);
        }
    }

    private static Texture2D? GetAtlas()
    {
        if (Atlas is not null && !Atlas.IsDisposed) return Atlas;
        Atlas=null;
        if (LoadFailed || ModEntry.StaticHelper is null) return null;
        try { Atlas=ModEntry.StaticHelper.ModContent.Load<Texture2D>(AtlasPath); return Atlas; }
        catch { LoadFailed=true; return null; }
    }
}
'''
(ROOT/'Services'/'Region1StardewDecorRenderer.cs').write_text(region_renderer,encoding='utf-8')

# ---------- Airship service: Lost & Found interaction + forest decor ----------
p=ROOT/'Services'/'AirshipFoundationService.cs'; s=p.read_text(encoding='utf-8')
s=s.replace('''        if (location is not null && TryGetRegion1RunRoomIndex(location, out _))\n            this.DrawRegion1HuntRun2Overlay(e.SpriteBatch, location);''','''        if (location is not null && TryGetRegion1RunRoomIndex(location, out int activeRoomIndex))\n        {\n            Region1StardewDecorRenderer.Draw(e.SpriteBatch, location, activeRoomIndex);\n            this.DrawRegion1HuntRun2Overlay(e.SpriteBatch, location);\n        }''',1)
# Add lost-found point and interaction inside SkyDock interior branch.
s=s.replace('''            Point route = ResolveSkyDockInteriorRouteTile(location);\n            Point bay = ResolveSkyDockInteriorBayTile(location);\n            Point interiorExit = ResolveSkyDockInteriorExitTile(location);''','''            Point route = ResolveSkyDockInteriorRouteTile(location);\n            Point bay = ResolveSkyDockInteriorBayTile(location);\n            Point lostFound = ResolveSkyDockLostFoundTile(location);\n            Point interiorExit = ResolveSkyDockInteriorExitTile(location);\n\n            if (Touches(interiorAction, lostFound))\n            {\n                this.Helper.Input.Suppress(e.Button);\n                Game1.playSound("openBox");\n                Game1.drawObjectDialogue(ModEntry.T("airship.lostfound.empty"));\n                return;\n            }''',1)
# Add resolver after bay resolver.
anchor='''    private static Point ResolveRegion1ArrivalTile(GameLocation region)\n'''
resolver='''    private static Point ResolveSkyDockLostFoundTile(GameLocation interior)\n    {\n        int width = interior.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30;\n        int height = interior.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;\n        return new Point(Math.Clamp(5, 2, width - 3), Math.Clamp(11, 4, height - 3));\n    }\n\n'''
if anchor not in s: raise RuntimeError('lostfound resolver anchor missing')
s=s.replace(anchor,resolver+anchor,1)
# Existing furniture methods no longer claim empty physical rooms.
s=s.replace('deck.modData[InteriorDecorMarkerKey] = InteriorDecorVersion + "-physical-bridge-no-pickups";', 'deck.modData[InteriorDecorMarkerKey] = InteriorDecorVersion + "-0668-lived-in-stardew-decor";',1)
s=s.replace('dock.modData[InteriorDecorMarkerKey] = InteriorDecorVersion + "-physical-dock-no-pickups";', 'dock.modData[InteriorDecorMarkerKey] = InteriorDecorVersion + "-0668-lived-in-stardew-decor-lostfound";',1)
p.write_text(s,encoding='utf-8')

# ---------- ModEntry signature/version/debug ----------
p=ROOT/'ModEntry.cs'; s=p.read_text(encoding='utf-8')
s=s.replace('MonsterDamagePatch.Apply(harmony, this.Combat, this.Deaths, this.CardArena);', 'MonsterDamagePatch.Apply(harmony, this.Combat, this.Deaths, this.CardArena, this.VerdantGuardian);',1)
s=s.replace('0.3.0-alpha.28.0.4.14.4.5.12.34 HUNT RUN 2.0 ADVANCED LAYER TEST', '0.3.0-alpha.28.0.4.14.4.5.12.35 VERDANT TOTEM + AIRSHIP HUB CLEANUP TEST',1)
# if log string exact prior wording differs, normalize version occurrence too
s=s.replace('0.3.0-alpha.28.0.4.14.4.5.12.34 REGION I HUNT RUN 2.0 FOUNDATION TEST', '0.3.0-alpha.28.0.4.14.4.5.12.35 VERDANT TOTEM + AIRSHIP HUB CLEANUP TEST')
# add totem status command near boss balance
cmd_anchor='''        helper.ConsoleCommands.Add("cardcha_boss1_balance_status", "Show the 0665 Region I Boss balance profile.", (_, _) => this.Monitor.Log(this.VerdantGuardian.DescribeBalance() + "\\n" + this.BossCards.Describe() + "\\n" + this.ChaChaBossForm.Describe(), LogLevel.Alert));\n'''
if cmd_anchor in s:
    s=s.replace(cmd_anchor,cmd_anchor+'        helper.ConsoleCommands.Add("cardcha_boss1_totem_status", "Show destructible Verdant Seed Totem state.", (_, _) => this.Monitor.Log(this.VerdantGuardian.DescribeBalance(), LogLevel.Alert));\n',1)
p.write_text(s,encoding='utf-8')

# ---------- i18n ----------
def add_i18n(path, vals):
    data=json.loads(path.read_text(encoding='utf-8')); data.update(vals); path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
add_i18n(ROOT/'i18n'/'default.json',{
 'boss.verdant.totem.broken':'A Verdant Seed Totem shattered. {{remaining}} remain.',
 'boss.verdant.totem.all-broken':'VERDANT BARRIER BROKEN! The Guardian reels as the last seed totem collapses.',
 'airship.lostfound.empty':'LOST & FOUND\\nNothing has been returned here right now.'
})
add_i18n(ROOT/'i18n'/'vi.json',{
 'boss.verdant.totem.broken':'Một Verdant Seed Totem đã vỡ. Còn lại {{remaining}} trụ.',
 'boss.verdant.totem.all-broken':'LỚP CỘNG HƯỞNG VERDANT ĐÃ VỠ! Guardian khựng lại khi trụ cuối cùng sụp xuống.',
 'airship.lostfound.empty':'KHO ĐỒ THẤT LẠC\\nHiện chưa có vật phẩm nào được gửi về đây.'
})

# ---------- handoff ----------
h=Path('handoff/ALPHA28_0668_TOTEM_AIRSHIP_HUB_CLEANUP.md')
h.write_text(f'''# Alpha28 0668 - Verdant Totem + Airship/Hub Cleanup\n\nBuild: `{VERSION}`\nBranch: `cardcha-alpha28-0668-totem-airship-hub-cleanup`\nStatus: implementation candidate; in-game acceptance pending.\n\n## Verdant Seed Totems\n- Four former corner props are now real targetable stationary support totems.\n- 90 HP each; no knockback/movement. Companion AI can target the real GreenSlime proxy while Harmony suppresses vanilla slime art.\n- Boss barrier: 4/3/2/1/0 totems = 15/10/6/3/0% incoming damage reduction.\n- While >=2 survive, Root/Vine cooldown is 8% shorter.\n- Destroying the last totem interrupts the current attack and staggers Boss I for 1.2s.\n- Totems never enter Cardcha loot/material/death reward pipelines.\n- Visuals have intact/cracked/critical/broken states plus an HP strip. No floating name label.\n\n## Airship/Hub cleanup\n- Deck and Sky Dock receive warm asymmetrical pixel-art clutter: map board, shelf, workbench, crates, barrel, sacks, rug, lamps, rope and plants.\n- Boarding gangway receives cargo/rope/lamps so it reads as a working airship space rather than floating boards.\n- Lost & Found is now a physical chest visual at the Sky Dock. No floating label or right-click hint. Interacting with it shows the Lost & Found message.\n- Region I rooms receive a light edge-only forest decoration pass without touching TMX collision or central combat lanes.\n\n## Preserved\n- Airship visual asset/hash is untouched.\n- Hunt Run 2.0 7-10 nodes, mutations, rare rooms and Elite Affix stay intact.\n- Boss I 1600 HP balance, 0660-0667 presentation/gameplay, Save Schema 19, Guardian Rabbit 10s and Boss Energy x1/3 remain locked.\n''',encoding='utf-8')
Path('handoff/LATEST_CARDCHA_HANDOFF.md').write_text(f'''# Latest Cardcha handoff\n\nCurrent branch: `cardcha-alpha28-0668-totem-airship-hub-cleanup`\nCurrent build: `{VERSION}`\nContinue from `handoff/ALPHA28_0668_TOTEM_AIRSHIP_HUB_CLEANUP.md`.\nDo not resume from stale main. In-game acceptance is pending.\n''',encoding='utf-8')

print(json.dumps({'version':VERSION,'totemHP':90,'barrier':[15,10,6,3,0],'staggerMs':1200,'lostFoundFloatingHint':False,'regionDecor':'edge-only'},indent=2))
