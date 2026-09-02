from pathlib import Path

arena_path = Path('src/Cardcha/Services/CardTestArenaService.cs')
s = arena_path.read_text(encoding='utf-8')


def once(old: str, new: str):
    global s
    if new in s:
        return
    if old not in s:
        raise SystemExit(f'missing arena anchor: {old[:120]!r}')
    s = s.replace(old, new, 1)

once(
    '    public const string TestMonsterMarkerKey = "Ronvotri.Cardcha/CardTestArenaDummy";\n',
    '    public const string TestMonsterMarkerKey = "Ronvotri.Cardcha/CardTestArenaDummy";\n'
    '    public const string KillTargetMarkerKey = "Ronvotri.Cardcha/CardTestArenaKillTarget";\n'
    '    public const string KillTargetSlotKey = "Ronvotri.Cardcha/CardTestArenaKillSlot";\n'
)
once(
    '    private const int DummyMaxHealth = 500;\n    private const long RespawnDelayMs = 450L;\n    private static readonly Point PlayerArrivalTile = new(4, 6);\n    private static readonly Point DummySpawnTile = new(11, 6);\n',
    '    private const int DummyMaxHealth = 500;\n'
    '    private const int KillTargetCount = 4;\n'
    '    private const int KillTargetMaxHealth = 100;\n'
    '    private const long RespawnDelayMs = 450L;\n'
    '    private const long KillTargetRespawnDelayMs = 350L;\n'
    '    private static readonly Point PlayerArrivalTile = new(4, 6);\n'
    '    private static readonly Point DummySpawnTile = new(11, 6);\n'
    '    private static readonly Point[] KillTargetSpawnTiles =\n'
    '    {\n'
    '        new(8, 3),\n'
    '        new(11, 3),\n'
    '        new(14, 3),\n'
    '        new(14, 8)\n'
    '    };\n'
)
once(
    '    private long RespawnAtMs;\n',
    '    private long RespawnAtMs;\n    private readonly long[] KillTargetRespawnAtMs = new long[KillTargetCount];\n'
)

s = s.replace(
    '            this.EnsureDummy(forceRespawn: true);\n            return;',
    '            this.EnsureDummy(forceRespawn: true);\n            this.EnsureKillTargets(forceRespawn: true);\n            return;',
    1
)
s = s.replace(
    '        this.EnsureDummy(forceRespawn: false);\n    }',
    '        this.EnsureDummy(forceRespawn: false);\n        this.EnsureKillTargets(forceRespawn: false);\n    }',
    1
)
s = s.replace(
    '        this.EnsureDummy(forceRespawn: true);\n        Game1.showGlobalMessage("Card Test Arena: TIME FROZEN • raw hit 100 • dummy hit 10");',
    '        this.EnsureDummy(forceRespawn: true);\n        this.EnsureKillTargets(forceRespawn: true);\n        Game1.showGlobalMessage("Card Test Arena: TIME FROZEN • IMMORTAL DUMMY + 4 KILL TARGETS • raw hit 100 • dummy hit 10");',
    1
)

old_condition = '            || !monster.modData.ContainsKey(TestMonsterMarkerKey))\n'
new_condition = '            || (!monster.modData.ContainsKey(TestMonsterMarkerKey)\n                && !monster.modData.ContainsKey(KillTargetMarkerKey)))\n'
if new_condition not in s:
    if old_condition not in s:
        raise SystemExit('missing outgoing marker condition')
    s = s.replace(old_condition, new_condition, 1)

once(
    '    public bool TryOverrideIncomingDamage(ref int damage, Monster? damager)\n',
    '    public void ClampMainDummyDamage(Monster monster, ref int damage)\n'
    '    {\n'
    '        if (!this.IsInArena\n'
    '            || damage <= 0\n'
    '            || !monster.modData.ContainsKey(TestMonsterMarkerKey))\n'
    '        {\n'
    '            return;\n'
    '        }\n\n'
    '        // The main dummy is the non-lethal comparison target. Leave it at 1 HP at worst,\n'
    '        // then EnsureDummy refills it on the next update. Kill cards only fire from the four kill targets.\n'
    '        damage = Math.Min(damage, Math.Max(0, monster.Health - 1));\n'
    '    }\n\n'
    '    public bool TryOverrideIncomingDamage(ref int damage, Monster? damager)\n'
)

s = s.replace(
    '        string dummyStatus = dummy is null\n            ? "respawning"\n            : $"HP {Math.Max(0, dummy.Health)}/{Math.Max(1, dummy.MaxHealth)}";\n        return $"Arena={(this.IsInArena ? "ACTIVE" : "off")} | Time={(this.IsInArena ? "FROZEN" : "normal")} | Dummy={dummyStatus} | RawOutgoing={FixedOutgoingRawDamage} | RawIncoming={FixedIncomingRawDamage}";',
    '        string dummyStatus = dummy is null\n            ? "respawning"\n            : $"HP {Math.Max(0, dummy.Health)}/{Math.Max(1, dummy.MaxHealth)}";\n        int killTargets = this.GetLivingKillTargetCount();\n        return $"Arena={(this.IsInArena ? "ACTIVE" : "off")} | Time={(this.IsInArena ? "FROZEN" : "normal")} | ImmortalDummy={dummyStatus} | KillTargets={killTargets}/{KillTargetCount} | RawOutgoing={FixedOutgoingRawDamage} | RawIncoming={FixedIncomingRawDamage}";',
    1
)
s = s.replace(
    '        string line = $"CARD TEST ARENA   TIME FROZEN   DUMMY {hp}   RAW HIT 100   RAW HIT TO YOU 10";',
    '        int killTargets = this.GetLivingKillTargetCount();\n        string line = $"CARD TEST ARENA   TIME FROZEN   IMMORTAL DUMMY {hp}   KILL TARGETS {killTargets}/{KillTargetCount}   RAW HIT 100   RAW HIT TO YOU 10";',
    1
)

# Refill the immortal dummy after a clamped lethal hit.
s = s.replace(
    '        Monster? existing = this.GetDummy();\n        if (existing is not null && existing.Health > 0 && !forceRespawn)\n            return;\n',
    '        Monster? existing = this.GetDummy();\n        if (existing is not null && existing.Health == 1 && !forceRespawn)\n        {\n            existing.Health = existing.MaxHealth;\n            existing.Position = new Vector2(DummySpawnTile.X * 64f, DummySpawnTile.Y * 64f);\n            this.RespawnAtMs = 0;\n            return;\n        }\n        if (existing is not null && existing.Health > 0 && !forceRespawn)\n            return;\n',
    1
)

insert_anchor = '    private Monster? GetDummy()\n'
if '    private void EnsureKillTargets(bool forceRespawn)\n' not in s:
    block = '''    private void EnsureKillTargets(bool forceRespawn)\n    {\n        if (!this.IsInArena)\n            return;\n\n        GameLocation? arena = Game1.currentLocation;\n        if (arena is null)\n            return;\n\n        long now = Environment.TickCount64;\n        for (int slot = 0; slot < KillTargetCount; slot++)\n        {\n            Monster? existing = this.GetKillTarget(slot);\n            if (existing is not null && existing.Health > 0 && !forceRespawn)\n                continue;\n\n            if (existing is not null)\n                arena.characters.Remove(existing);\n\n            if (!forceRespawn)\n            {\n                if (this.KillTargetRespawnAtMs[slot] <= 0)\n                {\n                    this.KillTargetRespawnAtMs[slot] = now + KillTargetRespawnDelayMs;\n                    continue;\n                }\n                if (now < this.KillTargetRespawnAtMs[slot])\n                    continue;\n            }\n\n            Point spawn = KillTargetSpawnTiles[slot];\n            GreenSlime target = new(new Vector2(spawn.X * 64f, spawn.Y * 64f), 0)\n            {\n                MaxHealth = KillTargetMaxHealth,\n                Health = KillTargetMaxHealth,\n                Speed = 0\n            };\n            target.modData[KillTargetMarkerKey] = "1";\n            target.modData[KillTargetSlotKey] = slot.ToString();\n            arena.characters.Add(target);\n            this.KillTargetRespawnAtMs[slot] = 0;\n        }\n    }\n\n    private Monster? GetKillTarget(int slot)\n    {\n        string slotText = slot.ToString();\n        return Game1.currentLocation?.characters\n            .OfType<Monster>()\n            .FirstOrDefault(monster =>\n                monster.modData.ContainsKey(KillTargetMarkerKey)\n                && monster.modData.TryGetValue(KillTargetSlotKey, out string? value)\n                && value == slotText);\n    }\n\n    private int GetLivingKillTargetCount()\n        => Game1.currentLocation?.characters\n            .OfType<Monster>()\n            .Count(monster => monster.Health > 0 && monster.modData.ContainsKey(KillTargetMarkerKey)) ?? 0;\n\n'''
    if insert_anchor not in s:
        raise SystemExit('missing GetDummy insertion anchor')
    s = s.replace(insert_anchor, block + insert_anchor, 1)

s = s.replace(
    '        foreach (NPC actor in arena.characters.Where(actor => actor.modData.ContainsKey(TestMonsterMarkerKey)).ToList())\n            arena.characters.Remove(actor);',
    '        foreach (NPC actor in arena.characters.Where(actor =>\n                     actor.modData.ContainsKey(TestMonsterMarkerKey)\n                     || actor.modData.ContainsKey(KillTargetMarkerKey)).ToList())\n        {\n            arena.characters.Remove(actor);\n        }',
    1
)
s = s.replace(
    '        this.RespawnAtMs = 0;\n        this.ReturnLocationName = "";',
    '        this.RespawnAtMs = 0;\n        Array.Clear(this.KillTargetRespawnAtMs, 0, this.KillTargetRespawnAtMs.Length);\n        this.ReturnLocationName = "";',
    1
)

arena_path.write_text(s, encoding='utf-8')

patch_path = Path('src/Cardcha/Patches/MonsterDamagePatch.cs')
p = patch_path.read_text(encoding='utf-8')
needle = '                damage = Combat.ModifyMonsterDamage(__instance, damage, isBomb, who);\n                Combat.ModifyMonsterTrajectory(ref xTrajectory, ref yTrajectory, isBomb, who);\n'
replacement = '                damage = Combat.ModifyMonsterDamage(__instance, damage, isBomb, who);\n                TestArena?.ClampMainDummyDamage(__instance, ref damage);\n                Combat.ModifyMonsterTrajectory(ref xTrajectory, ref yTrajectory, isBomb, who);\n'
if replacement not in p:
    if needle not in p:
        raise SystemExit('missing MonsterDamagePatch clamp anchor')
    p = p.replace(needle, replacement, 1)
patch_path.write_text(p, encoding='utf-8')

print('Applied Card Test Arena immortal dummy + four respawning kill targets')
