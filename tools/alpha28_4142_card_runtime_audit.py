from __future__ import annotations

from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "src" / "Cardcha"
VERSION = "0.3.0-alpha.28.0.4.14.2"


def replace_required(path: Path, old: str, new: str, count: int = 1) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"Required marker not found in {path}: {old[:220]!r}")
    path.write_text(text.replace(old, new, count), encoding="utf-8")


def patch_version() -> None:
    manifest = MOD / "manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["Version"] = VERSION
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    csproj = MOD / "Cardcha.csproj"
    text = csproj.read_text(encoding="utf-8")
    text = re.sub(r"<Version>[^<]+</Version>", f"<Version>{VERSION}</Version>", text, count=1)
    csproj.write_text(text, encoding="utf-8")

    targets = MOD / "Directory.Build.targets"
    text = targets.read_text(encoding="utf-8")
    text = text.replace("0.3.0-alpha.28.0.4.14.1", VERSION)
    text = text.replace(".4.14.1 workflow", ".4.14.2 workflow")
    text = text.replace("CardchaAlpha2804141Manifest", "CardchaAlpha2804142Manifest")
    targets.write_text(text, encoding="utf-8")

    entry = MOD / "ModEntry.cs"
    text = entry.read_text(encoding="utf-8")
    text = text.replace(
        "Cardcha! v0.3.0-alpha.28.0.4.14.1 AIRSHIP UX HOTFIX TEST with",
        f"Cardcha! v{VERSION} CARD RUNTIME AUDIT TEST with",
    )
    text = text.replace(
        '"Cardcha! v0.3.0-alpha.28.0.4.14.1 AIRSHIP UX HOTFIX TEST"',
        f'"Cardcha! v{VERSION} CARD RUNTIME AUDIT TEST"',
    )
    entry.write_text(text, encoding="utf-8")


def patch_save_model() -> None:
    path = MOD / "Models" / "SaveData.cs"
    text = path.read_text(encoding="utf-8")
    text = text.replace("public int SchemaVersion { get; set; } = 17;", "public int SchemaVersion { get; set; } = 18;")
    marker = "    // alpha.26.5 collection insurance: 20 duplicate pulls -> next eligible pull is NEW.\n    public int DuplicatePullStreak { get; set; }\n"
    block = """    // alpha.26.5 collection insurance: 20 duplicate pulls -> next eligible pull is NEW.
    public int DuplicatePullStreak { get; set; }

    // alpha.28.0.4.14.2 card-runtime audit.
    public long StandardPullIndex { get; set; }
    public HashSet<string> BattleScholarMonsterTypesToday { get; set; } =
        new(StringComparer.OrdinalIgnoreCase);
"""
    if "public long StandardPullIndex" not in text:
        if marker not in text:
            raise RuntimeError("SaveData duplicate streak marker missing")
        text = text.replace(marker, block, 1)
    path.write_text(text, encoding="utf-8")


def patch_save_service() -> None:
    path = MOD / "Services" / "SaveService.cs"
    text = path.read_text(encoding="utf-8")
    text = text.replace("private const int CurrentSchemaVersion = 17;", "private const int CurrentSchemaVersion = 18;")
    migration_marker = "        if (loadedSchema < CurrentSchemaVersion)\n"
    migration = """        // v18: full active-card runtime audit.
        if (loadedSchema < 18)
        {
            this.Data.StandardPullIndex = Math.Max(0, this.Data.StandardPullIndex);
            this.Data.BattleScholarMonsterTypesToday = new HashSet<string>(
                this.Data.BattleScholarMonsterTypesToday ?? new HashSet<string>(),
                StringComparer.OrdinalIgnoreCase
            );
        }

"""
    if migration.strip() not in text:
        if migration_marker not in text:
            raise RuntimeError("SaveService migration marker missing")
        text = text.replace(migration_marker, migration + migration_marker, 1)

    reset_old = """    public void ResetForNewDay()
    {
        this.Data.PhoenixHeartUsedToday = false;
        this.Data.LifelineUsedToday = false;
        this.Data.GuardianAngelUsedToday = false;
    }
"""
    reset_new = """    public void ResetForNewDay()
    {
        this.Data.PhoenixHeartUsedToday = false;
        this.Data.LifelineUsedToday = false;
        this.Data.GuardianAngelUsedToday = false;
        this.Data.BattleScholarMonsterTypesToday.Clear();
    }
"""
    if reset_new not in text:
        if reset_old not in text:
            raise RuntimeError("SaveService ResetForNewDay marker missing")
        text = text.replace(reset_old, reset_new, 1)

    norm_marker = "        this.Data.FavoriteCardIds ??= new HashSet<string>(StringComparer.OrdinalIgnoreCase);\n"
    norm_new = norm_marker + """        this.Data.BattleScholarMonsterTypesToday ??= new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        this.Data.BattleScholarMonsterTypesToday = new HashSet<string>(
            this.Data.BattleScholarMonsterTypesToday.Where(p => !string.IsNullOrWhiteSpace(p)),
            StringComparer.OrdinalIgnoreCase
        );
        this.Data.StandardPullIndex = Math.Max(0, this.Data.StandardPullIndex);
"""
    if "this.Data.StandardPullIndex = Math.Max(0, this.Data.StandardPullIndex);" not in text:
        if norm_marker not in text:
            raise RuntimeError("SaveService Normalize favorites marker missing")
        text = text.replace(norm_marker, norm_new, 1)

    copies_marker = """        string copies = string.Join(",", (data.CardCopies ?? new Dictionary<string, int>())
            .OrderBy(p => p.Key, StringComparer.OrdinalIgnoreCase)
            .Select(p => $"{p.Key}:{p.Value}"));

"""
    copies_new = copies_marker + """        string battleScholarTypes = string.Join(",", (data.BattleScholarMonsterTypesToday ?? new HashSet<string>())
            .Where(p => !string.IsNullOrWhiteSpace(p))
            .OrderBy(p => p, StringComparer.OrdinalIgnoreCase));

"""
    if "string battleScholarTypes =" not in text:
        if copies_marker not in text:
            raise RuntimeError("SaveService fingerprint copies marker missing")
        text = text.replace(copies_marker, copies_new, 1)

    text = text.replace("            data.PullIndex,\n            data.GachaSeed,\n", "            data.PullIndex,\n            data.StandardPullIndex,\n            data.GachaSeed,\n", 1)
    text = text.replace("            data.DuplicatePullStreak,\n            data.PhoenixHeartUsedToday ? 1 : 0,\n", "            data.DuplicatePullStreak,\n            battleScholarTypes,\n            data.PhoenixHeartUsedToday ? 1 : 0,\n", 1)
    path.write_text(text, encoding="utf-8")


def patch_upgrade_stats() -> None:
    path = MOD / "Services" / "CardUpgradeService.cs"
    text = path.read_text(encoding="utf-8")
    thick = """            "thick_hide" => new CardLevelStats
            {
                Primary = Pick(level, 1, 2, 3)
            },

"""
    vitality = thick + """            "vitality" => new CardLevelStats
            {
                Primary = Pick(level, 10, 15, 20, 25, 30)
            },

"""
    if '"vitality" => new CardLevelStats' not in text:
        if thick not in text:
            raise RuntimeError("CardUpgradeService thick_hide marker missing")
        text = text.replace(thick, vitality, 1)

    soul_old = """            "soul_eater" => new CardLevelStats
            {
                Primary = Pick(level, 0.08, 0.10, 0.12),
                Secondary = Pick(level, 7, 5, 5),
                DurationMs = PickInt(level, 5000, 6000, 7000),
                Threshold = Pick(level, 0.08, 0.10, 0.12)
            },
"""
    soul_new = """            "soul_eater" => new CardLevelStats
            {
                Primary = Pick(level, 0.10, 0.12, 0.15),
                Secondary = Pick(level, 6, 5, 4),
                DurationMs = 5000,
                Threshold = Pick(level, 0.10, 0.12, 0.15)
            },
"""
    if soul_new not in text:
        if soul_old not in text:
            raise RuntimeError("CardUpgradeService Soul Eater marker missing")
        text = text.replace(soul_old, soul_new, 1)

    last_old = """            "last_stand" => new CardLevelStats
            {
                Primary = Pick(level, 0.12, 0.16, 0.20),
                Secondary = Pick(level, 3, 4, 5),
                Threshold = 0.25
            },
"""
    last_new = """            "last_stand" => new CardLevelStats
            {
                Primary = Pick(level, 0.12, 0.16, 0.20),
                Secondary = Pick(level, 3, 4, 5),
                Threshold = 0.25,
                DurationMs = 6000
            },
"""
    if last_new not in text:
        if last_old not in text:
            raise RuntimeError("CardUpgradeService Last Stand marker missing")
        text = text.replace(last_old, last_new, 1)
    path.write_text(text, encoding="utf-8")


def patch_core_effects() -> None:
    path = MOD / "Services" / "CoreCardEffectsService.cs"
    text = path.read_text(encoding="utf-8")
    if "using System.Reflection;" not in text:
        text = text.replace("using StardewValley.Monsters;\n", "using StardewValley.Monsters;\nusing System.Reflection;\n", 1)

    old = """    private readonly HashSet<Monster> HitTargets = new();
    private readonly Dictionary<Monster, int> TargetHits = new();
    private readonly HashSet<string> MonsterTypesToday = new(StringComparer.OrdinalIgnoreCase);
"""
    new = """    private readonly HashSet<Monster> HitTargets = new();
    private readonly Dictionary<Monster, int> TargetHits = new();
    private readonly Dictionary<Monster, long> ReapersMarkUntil = new();
    private Monster? ComboTarget;
    private int ComboTargetHits;
"""
    if new not in text:
        if old not in text:
            raise RuntimeError("Core target fields marker missing")
        text = text.replace(old, new, 1)

    text = text.replace("    private double LifeStealThisWindow;\n", "    private double LifeStealThisWindow;\n    private double LifeStealFractionalCarry;\n", 1)

    old = """        int priorHits = this.TargetHits.TryGetValue(monster, out int hitCount) ? hitCount : 0;
        if (this.Loadout.IsEquipped("armor_breaker"))
            bonus += Math.Min(5, priorHits) * this.LevelValue("armor_breaker", .02, .025, .03, .035);

        if (this.Loadout.IsEquipped("relentless"))
        {
            int level = this.Level("relentless");
            int max = level switch { 1 => 5, 2 => 6, _ => 7 };
            bonus += Math.Min(max, priorHits) * this.LevelValue("relentless", .02, .025, .03);
        }
"""
    new = """        int priorComboHits = ReferenceEquals(this.ComboTarget, monster) ? this.ComboTargetHits : 0;
        if (this.Loadout.IsEquipped("armor_breaker"))
            bonus += Math.Min(5, priorComboHits) * this.LevelValue("armor_breaker", .02, .025, .03, .035);

        if (this.Loadout.IsEquipped("relentless"))
        {
            int level = this.Level("relentless");
            int max = level switch { 1 => 5, 2 => 6, _ => 7 };
            bonus += Math.Min(max, priorComboHits) * this.LevelValue("relentless", .02, .025, .03);
        }
"""
    if new not in text:
        if old not in text:
            raise RuntimeError("Core same-target marker missing")
        text = text.replace(old, new, 1)

    old = """        if (this.Loadout.IsEquipped("reapers_mark") && priorHits >= 4)
            bonus += this.LevelValue("reapers_mark", .08, .10, .12);
"""
    new = """        if (this.Loadout.IsEquipped("reapers_mark")
            && this.ReapersMarkUntil.TryGetValue(monster, out long reaperUntil)
            && now < reaperUntil)
            bonus += this.LevelValue("reapers_mark", .08, .10, .12);
"""
    if new not in text:
        if old not in text:
            raise RuntimeError("Core Reaper marker missing")
        text = text.replace(old, new, 1)

    old = """        if (this.Loadout.IsEquipped("void_walker") && now >= this.VoidReadyAt)
        {
            double proc = this.LevelValue("void_walker", .15, .20, .25);
            if (Game1.random.NextDouble() < proc)
            {
                multiplier *= 1d - this.LevelValue("void_walker", .40, .50, .60);
                this.VoidPhaseUntil = now + this.LevelInt("void_walker", 1500, 1750, 2000);
                this.VoidReadyAt = now + this.LevelInt("void_walker", 20000, 18000, 16000);
            }
        }
"""
    new = """        if (this.Loadout.IsEquipped("void_walker") && now < this.VoidPhaseUntil)
            multiplier *= 1d - this.LevelValue("void_walker", .40, .50, .60);
"""
    if new not in text:
        if old not in text:
            raise RuntimeError("Core Void incoming marker missing")
        text = text.replace(old, new, 1)

    guardian = """        if (this.Loadout.IsEquipped("guardian_angel")
            && !this.Save.Data.GuardianAngelUsedToday
            && modified >= player.health)
        {
            modified = Math.Max(0, player.health - 1);
            this.GuardianShield = Math.Max(this.GuardianShield,
                Math.Max(1, (int)Math.Ceiling(player.maxHealth * this.LevelValue("guardian_angel", .25, .35, .45))));
            this.Save.Data.GuardianAngelUsedToday = true;
            this.Save.Save();
            Game1.playSound("yoba");
        }

"""
    text = text.replace(guardian, "", 1)

    marker = """        if (critLike
            && this.Loadout.IsEquipped("time_breaker")
            && now >= this.TimeBreakerReadyAt)
        {
            double proc = this.LevelValue("time_breaker", .10, .12, .15);
            if (Game1.random.NextDouble() < proc)
            {
                this.TimeBreakerUntil = now + 3000;
                this.TimeBreakerReadyAt = now + this.LevelInt("time_breaker", 12000, 10000, 8000);
                Game1.playSound("crit");
            }
        }

"""
    replacement = marker + """        if (critLike && this.Loadout.IsEquipped("crushing_impact"))
            TryApplyMonsterStagger(monster, this.LevelInt("crushing_impact", 200, 250, 300, 350));

"""
    if "TryApplyMonsterStagger(monster" not in text:
        if marker not in text:
            raise RuntimeError("Core crit marker missing")
        text = text.replace(marker, replacement, 1)

    old = """        this.HitTargets.Add(monster);
        this.TargetHits[monster] = Math.Min(1000, (this.TargetHits.TryGetValue(monster, out int hits) ? hits : 0) + 1);
        this.LastOutgoingHitAt = now;
"""
    new = """        this.HitTargets.Add(monster);
        int targetHits = Math.Min(1000, (this.TargetHits.TryGetValue(monster, out int hits) ? hits : 0) + 1);
        this.TargetHits[monster] = targetHits;
        if (this.Loadout.IsEquipped("reapers_mark") && targetHits >= 4)
        {
            this.ReapersMarkUntil[monster] = now + 6000;
            this.TargetHits[monster] = 0;
        }
        if (!ReferenceEquals(this.ComboTarget, monster))
        {
            this.ComboTarget = monster;
            this.ComboTargetHits = 0;
        }
        this.ComboTargetHits = Math.Min(1000, this.ComboTargetHits + 1);
        this.LastOutgoingHitAt = now;
"""
    if new not in text:
        if old not in text:
            raise RuntimeError("Core post-hit marker missing")
        text = text.replace(old, new, 1)

    old = """        if (this.Loadout.IsEquipped("soul_siphon") && who.health > 0 && who.health < who.maxHealth)
        {
            if (now - this.LifeStealWindowAt >= 1000)
            {
                this.LifeStealWindowAt = now;
                this.LifeStealThisWindow = 0;
            }

            double cap = this.LevelValue("soul_siphon", 3, 4, 5);
            double healFraction = this.LevelValue("soul_siphon", .010, .0125, .015);
            double room = Math.Max(0, cap - this.LifeStealThisWindow);
            int heal = Math.Max(0, (int)Math.Floor(Math.Min(room, actual * healFraction)));
            if (heal > 0)
            {
                who.health = Math.Min(who.maxHealth, who.health + heal);
                this.LifeStealThisWindow += heal;
            }
        }
"""
    new = """        if (this.Loadout.IsEquipped("soul_siphon") && who.health > 0 && who.health < who.maxHealth)
        {
            if (now - this.LifeStealWindowAt >= 1000)
            {
                this.LifeStealWindowAt = now;
                this.LifeStealThisWindow = 0;
            }
            double cap = this.LevelValue("soul_siphon", 3, 4, 5);
            double healFraction = this.LevelValue("soul_siphon", .010, .0125, .015);
            double room = Math.Max(0, cap - this.LifeStealThisWindow);
            if (room > 0)
            {
                double earned = this.LifeStealFractionalCarry + actual * healFraction;
                int whole = Math.Max(0, (int)Math.Floor(earned));
                int heal = Math.Min((int)Math.Floor(room), whole);
                if (heal > 0)
                {
                    who.health = Math.Min(who.maxHealth, who.health + heal);
                    this.LifeStealThisWindow += heal;
                }
                this.LifeStealFractionalCarry = whole > heal && this.LifeStealThisWindow >= cap
                    ? 0
                    : Math.Clamp(earned - whole, 0d, 0.999999d);
            }
        }
        else if (!this.Loadout.IsEquipped("soul_siphon"))
            this.LifeStealFractionalCarry = 0;
"""
    if new not in text:
        if old not in text:
            raise RuntimeError("Core Soul Siphon marker missing")
        text = text.replace(old, new, 1)

    old = """        if (this.Loadout.IsEquipped("mirror_guard") && player.maxHealth > 0 && lost >= player.maxHealth * .25)
            this.MirrorGuardArmed = true;

        if (this.Loadout.IsEquipped("lifeline")
"""
    new = """        if (this.Loadout.IsEquipped("mirror_guard")
            && now >= this.MirrorGuardReadyAt
            && player.maxHealth > 0
            && lost >= player.maxHealth * .25)
            this.MirrorGuardArmed = true;

        if (this.Loadout.IsEquipped("guardian_angel")
            && !this.Save.Data.GuardianAngelUsedToday
            && player.health > 0
            && player.maxHealth > 0
            && player.health <= player.maxHealth * .20)
        {
            this.GuardianShield = Math.Max(this.GuardianShield,
                Math.Max(1, (int)Math.Ceiling(player.maxHealth * this.LevelValue("guardian_angel", .25, .35, .45))));
            this.Save.Data.GuardianAngelUsedToday = true;
            this.Save.Save();
            Game1.playSound("yoba");
        }

        if (this.Loadout.IsEquipped("void_walker") && now >= this.VoidReadyAt)
        {
            double proc = this.LevelValue("void_walker", .15, .20, .25);
            if (Game1.random.NextDouble() < proc)
            {
                this.VoidPhaseUntil = now + this.LevelInt("void_walker", 1500, 1750, 2000);
                this.VoidReadyAt = now + this.LevelInt("void_walker", 20000, 18000, 16000);
                Game1.playSound("wand");
            }
        }

        if (this.Loadout.IsEquipped("lifeline")
"""
    if new not in text:
        if old not in text:
            raise RuntimeError("Core post-hit protection marker missing")
        text = text.replace(old, new, 1)

    old = """        string monsterType = monster.GetType().FullName ?? monster.GetType().Name;
        this.MonsterTypesToday.Add(monsterType);

        if (!this.TookHitSinceLastKill)
"""
    new = """        string monsterType = monster.GetType().FullName ?? monster.GetType().Name;
        this.HandleKillProgress(monsterType, player, IsBossLike(monster), now);
        this.HitTargets.Remove(monster);
        this.TargetHits.Remove(monster);
        this.ReapersMarkUntil.Remove(monster);
        if (ReferenceEquals(this.ComboTarget, monster))
        {
            this.ComboTarget = null;
            this.ComboTargetHits = 0;
        }
        if (ReferenceEquals(this.MarkedPreyTarget, monster))
        {
            this.MarkedPreyTarget = null;
            this.MarkedPreyUntil = 0;
        }
    }

    public void OnCustomMonsterKilled(string sourceType, Farmer player, bool bossLike)
    {
        if (!this.Loadout.CardEffectsActive)
            return;
        this.HandleKillProgress(string.IsNullOrWhiteSpace(sourceType) ? "custom-enemy" : sourceType, player, bossLike, Environment.TickCount64);
    }

    private void HandleKillProgress(string monsterType, Farmer player, bool bossLike, long now)
    {
        this.Save.Data.BattleScholarMonsterTypesToday.Add(monsterType);

        if (!this.TookHitSinceLastKill)
"""
    if "public void OnCustomMonsterKilled" not in text:
        if old not in text:
            raise RuntimeError("Core OnMonsterKilled start marker missing")
        text = text.replace(old, new, 1)
        cleanup_old = """        if (IsBossLike(monster))
        {
            if (this.Loadout.IsEquipped("overclock"))
                this.OverclockUntil = now + 5000;
            if (this.Loadout.IsEquipped("apex_predator"))
                this.ApexPredatorBuffUntil = now + 6000;
        }

        this.HitTargets.Remove(monster);
        this.TargetHits.Remove(monster);
        if (ReferenceEquals(this.MarkedPreyTarget, monster))
        {
            this.MarkedPreyTarget = null;
            this.MarkedPreyUntil = 0;
        }
    }

    public void Sync(Farmer player, bool hasLivingMonster)
"""
        cleanup_new = """        if (bossLike)
        {
            if (this.Loadout.IsEquipped("overclock"))
                this.OverclockUntil = now + 5000;
            if (this.Loadout.IsEquipped("apex_predator"))
                this.ApexPredatorBuffUntil = now + 6000;
        }
    }

    public void Sync(Farmer player, bool hasLivingMonster)
"""
        if cleanup_old not in text:
            raise RuntimeError("Core OnMonsterKilled cleanup marker missing")
        text = text.replace(cleanup_old, cleanup_new, 1)

    text = text.replace("this.MonsterTypesToday.Count", "this.Save.Data.BattleScholarMonsterTypesToday.Count")
    text = text.replace("        this.HitTargets.Clear();\n        this.TargetHits.Clear();\n        this.MonsterTypesToday.Clear();\n", "        this.HitTargets.Clear();\n        this.TargetHits.Clear();\n        this.ReapersMarkUntil.Clear();\n        this.ComboTarget = null;\n        this.ComboTargetHits = 0;\n", 1)
    text = text.replace("        this.LifeStealWindowAt = 0;\n        this.LifeStealThisWindow = 0;\n", "        this.LifeStealWindowAt = 0;\n        this.LifeStealThisWindow = 0;\n        this.LifeStealFractionalCarry = 0;\n", 1)

    helper_marker = "    private static void TryRemoveBuff(Farmer player, string id)\n"
    helper = """    private static void TryApplyMonsterStagger(Monster monster, int durationMs)
    {
        if (durationMs <= 0)
            return;
        try
        {
            FieldInfo? field = typeof(Monster).GetField("stunTime", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
            if (field is null)
                return;
            object? current = field.GetValue(monster);
            if (field.FieldType == typeof(int))
            {
                int existing = current is int value ? value : 0;
                field.SetValue(monster, Math.Max(existing, durationMs));
                return;
            }
            PropertyInfo? valueProperty = current?.GetType().GetProperty("Value");
            if (valueProperty?.CanRead == true && valueProperty.CanWrite && valueProperty.PropertyType == typeof(int))
            {
                int existing = valueProperty.GetValue(current) is int value ? value : 0;
                valueProperty.SetValue(current, Math.Max(existing, durationMs));
            }
        }
        catch { }
    }

"""
    if "private static void TryApplyMonsterStagger" not in text:
        if helper_marker not in text:
            raise RuntimeError("Core helper marker missing")
        text = text.replace(helper_marker, helper + helper_marker, 1)
    path.write_text(text, encoding="utf-8")


def patch_combat_service() -> None:
    path = MOD / "Services" / "CombatService.cs"
    text = path.read_text(encoding="utf-8")
    marker = """    private int SoulEaterKills;
    private long SoulEaterBuffExpiresAt;
    private double SoulEaterDamageBonus;
"""
    new = marker + """
    private int VitalityAppliedBonus;
    private long LastStandUntil;
    private string LastStandLocation = "";
    private bool LastStandSawMonsters;
    private bool LastStandReady;
"""
    if "private int VitalityAppliedBonus;" not in text:
        if marker not in text:
            raise RuntimeError("Combat state marker missing")
        text = text.replace(marker, new, 1)

    old = """        CardLevelStats lastStand = this.GetStats("last_stand");
        if (this.Loadout.IsEquipped("last_stand")
            && IsLowHealth(who!, Math.Max(0.01, lastStand.Threshold)))
        {
            bonus += lastStand.Primary;
        }
"""
    new = """        CardLevelStats lastStand = this.GetStats("last_stand");
        if (this.IsLastStandRuntimeActive)
            bonus += lastStand.Primary;
"""
    if new not in text:
        if old not in text:
            raise RuntimeError("Combat Last Stand damage marker missing")
        text = text.replace(old, new, 1)

    marker = """    public void OnMonsterKilled(Monster monster, Farmer? who)
    {
        if (who?.IsLocalPlayer == true)
            this.Completion.OnMonsterKilled(monster, who);
        this.OnEnemyKilled(who);
    }

"""
    if "public void OnCustomEnemyKilled" not in text:
        if marker not in text:
            raise RuntimeError("Combat OnMonsterKilled marker missing")
        text = text.replace(marker, marker + """    public void OnCustomEnemyKilled(Farmer? who, string sourceType, bool bossLike)
    {
        if (who?.IsLocalPlayer == true)
            this.Completion.OnCustomMonsterKilled(sourceType, who, bossLike);
        this.OnEnemyKilled(who);
    }

""", 1)

    old = """        if (!this.Loadout.CardEffectsActive)
        {
            TryRemoveBuff(player, ThickHideBuffId);
"""
    new = """        if (!this.Loadout.CardEffectsActive)
        {
            this.RemoveVitalityBonus(player);
            this.ResetLastStandRuntime();
            TryRemoveBuff(player, ThickHideBuffId);
"""
    if new not in text:
        if old not in text:
            raise RuntimeError("Combat inactive marker missing")
        text = text.replace(old, new, 1)

    old = """        bool hasLivingMonster = Game1.currentLocation?.characters
            .OfType<Monster>()
            .Any(m => m.IsMonster && m.Health > 0) == true;

        CardLevelStats swift = this.GetStats("swift_feet");
        long now = Environment.TickCount64;
"""
    new = """        this.SyncVitality(player);

        bool hasLivingMonster = Game1.currentLocation?.characters
            .OfType<Monster>()
            .Any(m => m.IsMonster && m.Health > 0) == true;

        CardLevelStats swift = this.GetStats("swift_feet");
        long now = Environment.TickCount64;
        this.UpdateLastStandRuntime(player, hasLivingMonster, now);
"""
    if new not in text:
        if old not in text:
            raise RuntimeError("Combat passive marker missing")
        text = text.replace(old, new, 1)

    old = """        CardLevelStats lastStand = this.GetStats("last_stand");
        if (this.Loadout.IsEquipped("last_stand")
            && IsLowHealth(player, Math.Max(0.01, lastStand.Threshold)))
        {
            ApplyHiddenBuff(
                player,
                LastStandBuffId,
                defense: Math.Max(0, (int)Math.Round(lastStand.Secondary)),
                speed: 0
            );
        }
        else
        {
            TryRemoveBuff(player, LastStandBuffId);
        }
"""
    new = """        CardLevelStats lastStand = this.GetStats("last_stand");
        if (this.IsLastStandRuntimeActive)
        {
            ApplyHiddenBuff(player, LastStandBuffId, defense: Math.Max(0, (int)Math.Round(lastStand.Secondary)), speed: 0);
        }
        else
            TryRemoveBuff(player, LastStandBuffId);
"""
    if new not in text:
        if old not in text:
            raise RuntimeError("Combat Last Stand buff marker missing")
        text = text.replace(old, new, 1)

    old = """    public void ResetRuntime()
    {
        this.Completion.ResetRuntime();
"""
    new = """    public void ResetRuntime()
    {
        if (Context.IsWorldReady && Game1.player is not null)
            this.RemoveVitalityBonus(Game1.player);
        this.ResetLastStandRuntime();
        this.Completion.ResetRuntime();
"""
    if new not in text:
        if old not in text:
            raise RuntimeError("Combat ResetRuntime marker missing")
        text = text.replace(old, new, 1)

    marker = "    private CardLevelStats GetStats(string id)\n"
    helpers = """    public void PrepareForGameSave()
    {
        if (Context.IsWorldReady && Game1.player is not null)
            this.RemoveVitalityBonus(Game1.player);
    }

    private bool IsLastStandRuntimeActive
        => this.Loadout.CardEffectsActive && this.Loadout.IsEquipped("last_stand") && Environment.TickCount64 < this.LastStandUntil;

    private void SyncVitality(Farmer player)
    {
        int desired = this.Loadout.CardEffectsActive && this.Loadout.IsEquipped("vitality")
            ? Math.Max(0, (int)Math.Round(this.GetStats("vitality").Primary))
            : 0;
        int delta = desired - this.VitalityAppliedBonus;
        if (delta == 0)
            return;
        player.maxHealth = Math.Max(1, player.maxHealth + delta);
        this.VitalityAppliedBonus = desired;
        if (player.health > player.maxHealth)
            player.health = player.maxHealth;
    }

    private void RemoveVitalityBonus(Farmer player)
    {
        if (this.VitalityAppliedBonus <= 0)
            return;
        player.maxHealth = Math.Max(1, player.maxHealth - this.VitalityAppliedBonus);
        this.VitalityAppliedBonus = 0;
        if (player.health > player.maxHealth)
            player.health = player.maxHealth;
    }

    private void UpdateLastStandRuntime(Farmer player, bool hasLivingMonster, long now)
    {
        string location = Game1.currentLocation?.NameOrUniqueName ?? "";
        if (!string.Equals(location, this.LastStandLocation, StringComparison.OrdinalIgnoreCase))
        {
            this.LastStandLocation = location;
            this.LastStandSawMonsters = false;
            this.LastStandReady = false;
            this.LastStandUntil = 0;
        }
        if (!this.Loadout.IsEquipped("last_stand") || !hasLivingMonster)
        {
            this.LastStandSawMonsters = false;
            this.LastStandReady = false;
            this.LastStandUntil = 0;
            return;
        }
        if (!this.LastStandSawMonsters)
        {
            this.LastStandSawMonsters = true;
            this.LastStandReady = true;
            this.LastStandUntil = 0;
        }
        CardLevelStats stats = this.GetStats("last_stand");
        if (this.LastStandReady && IsLowHealth(player, Math.Max(0.01, stats.Threshold)))
        {
            this.LastStandReady = false;
            this.LastStandUntil = now + Math.Max(500, stats.DurationMs);
            Game1.playSound("yoba");
        }
    }

    private void ResetLastStandRuntime()
    {
        this.LastStandUntil = 0;
        this.LastStandLocation = "";
        this.LastStandSawMonsters = false;
        this.LastStandReady = false;
    }

"""
    if "public void PrepareForGameSave()" not in text:
        if marker not in text:
            raise RuntimeError("Combat GetStats marker missing")
        text = text.replace(marker, helpers + marker, 1)
    path.write_text(text, encoding="utf-8")


def patch_custom_death() -> None:
    path = MOD / "Services" / "MonsterDeathService.cs"
    text = path.read_text(encoding="utf-8")
    old = """        this.Combat.OnEnemyKilled(who);
        EnemyLootScale scale = DropService.ClassifyEnemy(
            this.LastMonsterName,
            sourceType
        );

        this.Drops.TryDrop(
"""
    new = """        EnemyLootScale scale = DropService.ClassifyEnemy(this.LastMonsterName, sourceType);
        string coreType = sourceType.Split(" [observer", StringSplitOptions.None)[0];
        this.Combat.OnCustomEnemyKilled(who, coreType, scale == EnemyLootScale.BossLike);

        this.Drops.TryDrop(
"""
    if new not in text:
        if old not in text:
            raise RuntimeError("MonsterDeath custom marker missing")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def patch_gacha() -> None:
    path = MOD / "Services" / "GachaService.cs"
    text = path.read_text(encoding="utf-8")
    old = """        SaveData data = this.Save.Data;
        long pullIndex = data.PullIndex;

        // Keep save-seed continuity while ensuring reloads don't replay the exact same result.
"""
    new = """        SaveData data = this.Save.Data;
        long pullIndex = data.PullIndex;
        double cardmasterRareBoost = 0d;
        if (type == PullType.Standard
            && data.StandardPullIndex > 0
            && data.StandardPullIndex % 10 == 0
            && data.EquippedCards.Contains("cardmaster", StringComparer.OrdinalIgnoreCase))
        {
            int cardmasterLevel = data.CardLevels.TryGetValue("cardmaster", out int cl) ? Math.Clamp(cl, 1, 3) : 1;
            cardmasterRareBoost = cardmasterLevel switch { 1 => 0.010, 2 => 0.015, _ => 0.020 };
        }

        // Keep save-seed continuity while ensuring reloads don't replay the exact same result.
"""
    if new not in text:
        if old not in text:
            raise RuntimeError("Gacha start marker missing")
        text = text.replace(old, new, 1)

    text = text.replace("? RollStandardRarity(rng, data)\n", "? RollStandardRarity(rng, data, cardmasterRareBoost)\n", 1)
    text = text.replace("        data.PullIndex++;\n\n        // Golden Hand", "        data.PullIndex++;\n        if (type == PullType.Standard)\n            data.StandardPullIndex++;\n\n        // Golden Hand", 1)

    old = """        // Cardmaster (#74): approved periodic Dust component. Its small Rare+ weighting bonus
        // is intentionally conservative and applied only to Standard by nudging the next roll
        // through the persisted duplicate insurance/pity systems rather than bypassing either.
        if (type == PullType.Standard
            && data.EquippedCards.Contains("cardmaster", StringComparer.OrdinalIgnoreCase)
            && data.PullIndex > 0
            && data.PullIndex % 10 == 0)
        {
            int level = data.CardLevels.TryGetValue("cardmaster", out int cl) ? Math.Clamp(cl, 1, 3) : 1;
            int bonusDust = level switch { 1 => 5, 2 => 7, _ => 10 };
            data.SuspiciousDust = checked(Math.Max(0, data.SuspiciousDust) + bonusDust);
            dustAwarded += bonusDust;
        }
"""
    new = """        // Cardmaster (#74): every 10 STANDARD pulls grants Dust; the next Standard
        // pull receives the small Rare+ nudge computed at the start of Pull().
        if (type == PullType.Standard
            && data.EquippedCards.Contains("cardmaster", StringComparer.OrdinalIgnoreCase)
            && data.StandardPullIndex > 0
            && data.StandardPullIndex % 10 == 0)
        {
            int level = data.CardLevels.TryGetValue("cardmaster", out int cl) ? Math.Clamp(cl, 1, 3) : 1;
            int bonusDust = level switch { 1 => 5, 2 => 7, _ => 10 };
            data.SuspiciousDust = checked(Math.Max(0, data.SuspiciousDust) + bonusDust);
            dustAwarded += bonusDust;
        }
"""
    if new not in text:
        if old not in text:
            raise RuntimeError("Gacha Cardmaster marker missing")
        text = text.replace(old, new, 1)

    text = text.replace("    private CardRarity RollStandardRarity(DeterministicRng rng, SaveData data)\n", "    private CardRarity RollStandardRarity(DeterministicRng rng, SaveData data, double rarePlusBonus = 0d)\n", 1)
    old = """        double roll = rng.NextDouble();
        if (roll < 0.03) return CardRarity.Legendary;
        if (roll < 0.15) return CardRarity.Epic;
        if (roll < 0.45) return CardRarity.Rare;
        return CardRarity.Common;
"""
    new = """        double roll = rng.NextDouble();
        double rareThreshold = Math.Clamp(0.45 + Math.Max(0d, rarePlusBonus), 0.45, 0.95);
        if (roll < 0.03) return CardRarity.Legendary;
        if (roll < 0.15) return CardRarity.Epic;
        if (roll < rareThreshold) return CardRarity.Rare;
        return CardRarity.Common;
"""
    if new not in text:
        if old not in text:
            raise RuntimeError("Gacha probability marker missing")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def patch_mod_entry() -> None:
    path = MOD / "ModEntry.cs"
    text = path.read_text(encoding="utf-8")
    text = text.replace("        helper.Events.GameLoop.Saving += this.OnSaving;\n", "        helper.Events.GameLoop.Saving += this.OnSaving;\n        helper.Events.GameLoop.Saved += this.OnSaved;\n", 1)
    old = """    private void OnSaving(object? sender, SavingEventArgs e)
    {
        // ChaCha is a runtime-only world actor; remove it before Stardew serializes locations.
        this.Story.OnSaving();
        this.Save.Save();
    }

"""
    new = """    private void OnSaving(object? sender, SavingEventArgs e)
    {
        this.Combat.PrepareForGameSave();
        // ChaCha is a runtime-only world actor; remove it before Stardew serializes locations.
        this.Story.OnSaving();
        this.Save.Save();
    }

    private void OnSaved(object? sender, SavedEventArgs e)
    {
        this.Combat.SyncPassiveBuffs();
    }

"""
    if new not in text:
        if old not in text:
            raise RuntimeError("ModEntry OnSaving marker missing")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def patch_text() -> None:
    vi_path = MOD / "i18n" / "vi.json"
    en_path = MOD / "i18n" / "default.json"
    vi = json.loads(vi_path.read_text(encoding="utf-8"))
    en = json.loads(en_path.read_text(encoding="utf-8"))

    def set_card(data: dict, cid: str, desc: str, stars: list[str]) -> None:
        data[f"card.{cid}.desc"] = desc
        for i, value in enumerate(stars, 1):
            data[f"card.{cid}.star.{i}"] = value

    set_card(vi, "steady_grip", "Ổn định sát thương đòn thường theo mức sát thương gần đây; đòn có dấu hiệu chí mạng không bị làm phẳng.", [f"Giảm {p}% phần dao động so với mức sát thương thường gần đây." for p in [15,22,30,38,45]])
    set_card(en, "steady_grip", "Stabilizes ordinary-hit damage around your recent normal-hit baseline; crit-like hits are left untouched.", [f"Reduces {p}% of ordinary-hit variance from the recent baseline." for p in [15,22,30,38,45]])

    set_card(vi, "victory_charge", "TẠM CHƯA HOẠT ĐỘNG TRONG BẢN TEST: lá này cần hệ Năng lượng Trùm, nhưng hệ đó chưa được triển khai. Không cộng chỉ số ẩn.", ["Chờ hệ Năng lượng Trùm."] * 5)
    set_card(en, "victory_charge", "TEMPORARILY INACTIVE IN THIS TEST BUILD: this card requires the Boss Energy system, which does not exist yet. It grants no hidden substitute bonus.", ["Pending Boss Energy system."] * 5)

    set_card(vi, "lucky_pocket", "Khi hạ quái, có xác suất nhỏ nhận thêm 25g.", [f"Hạ quái: +{p}% cơ hội nhận thêm 25g." for p in [2,3,4,5,6]])
    set_card(en, "lucky_pocket", "Defeating a monster has a small chance to grant an extra 25g.", [f"Kill: +{p}% chance to gain an extra 25g." for p in [2,3,4,5,6]])

    set_card(vi, "bruiser", "Gây thêm sát thương lên quái có ít nhất 300 HP tối đa.", [f"Lên quái có ≥300 HP tối đa: +{p}% sát thương." for p in [4,5,6,7,8]])
    set_card(en, "bruiser", "Deal extra damage to monsters with at least 300 max HP.", [f"Against monsters with ≥300 max HP: +{p}% damage." for p in [4,5,6,7,8]])

    set_card(vi, "treasure_eye", "Khi hạ quái, có xác suất nhỏ nhận thêm 1 Mảnh Bìa Cardcha.", [f"Hạ quái: {p}% cơ hội nhận thêm 1 Mảnh Bìa Cardcha." for p in [4,5,6,7]])
    set_card(en, "treasure_eye", "Defeating a monster has a small chance to grant +1 Cardboard Scrap.", [f"Kill: {p}% chance for +1 Cardboard Scrap." for p in [4,5,6,7]])

    set_card(vi, "card_seeker", "Nhân cơ hội rơi Mảnh Bìa Cardcha thường; không tăng Mảnh Bìa Lấp Lánh hay vật phẩm độc quyền của Trùm.", [f"Cơ hội Mảnh Bìa thường ×{m:.2f}; Mảnh Lấp Lánh không đổi." for m in [1.15,1.18,1.21,1.24]])
    set_card(en, "card_seeker", "Multiplies NORMAL Cardboard Scrap drop chance only; it never boosts Shiny Scrap or boss-exclusive drops.", [f"Normal Cardboard Scrap chance ×{m:.2f}; Shiny Scrap unchanged." for m in [1.15,1.18,1.21,1.24]])

    set_card(vi, "dust_collector", "Khi lá tối đa sao bị quay trùng và chuyển thành Bụi Ma Thuật, có cơ hội nhận thêm +1 Bụi.", [f"Trùng lá tối đa sao: {p}% cơ hội nhận thêm +1 Bụi Ma Thuật." for p in [15,20,25,30]])
    set_card(en, "dust_collector", "When a max-star duplicate converts into Magic Dust, it has a chance to grant +1 extra Dust.", [f"Max-star duplicate: {p}% chance for +1 extra Magic Dust." for p in [15,20,25,30]])

    set_card(vi, "fortune_chain", "Sau chuỗi 5 lần hạ quái không bị đánh, mỗi lần hạ tiếp theo có cơ hội nhận +1 Mảnh Bìa Cardcha cho tới khi trúng đòn.", [f"Chuỗi không trúng đòn ≥5: mỗi lần hạ quái có {p}% cơ hội +1 Mảnh Bìa Cardcha." for p in [5,7,9,11]])
    set_card(en, "fortune_chain", "After a 5-kill no-hit streak, each further kill can grant +1 Cardboard Scrap until you take a hit.", [f"No-hit streak ≥5: each kill has {p}% chance for +1 Cardboard Scrap." for p in [5,7,9,11]])

    set_card(vi, "vanguard", "Khi một đợt giao tranh bắt đầu trong khu vực có quái, nhận lá chắn nhỏ một lần cho đợt đó.", [f"Bắt đầu đợt giao tranh: nhận lá chắn {v} HP một lần." for v in [5,8,11,14]])
    set_card(en, "vanguard", "When a monster encounter begins, gain a small shield once for that encounter.", [f"Encounter start: gain a {v} HP shield once." for v in [5,8,11,14]])

    set_card(vi, "collectors_instinct", "Hạ quái Tinh Anh/Đỉnh Cấp/Trùm có thêm cơ hội nhận +1 Mảnh Bìa Cardcha.", [f"Tinh Anh/Đỉnh Cấp/Trùm: {p}% cơ hội +1 Mảnh Bìa Cardcha." for p in [5,7,9,11]])
    set_card(en, "collectors_instinct", "Defeating an Elite/Apex/Boss has an extra chance to grant +1 Cardboard Scrap.", [f"Elite/Apex/Boss: {p}% chance for +1 Cardboard Scrap." for p in [5,7,9,11]])

    set_card(vi, "phantom_step", "Trong lúc có quái, một pha di chuyển né nhanh khi bạn không vừa nhận sát thương sẽ chuẩn bị đòn kế tiếp có tỉ lệ chí mạng cao hơn; có hồi chiêu.", ["Né nhanh bằng di chuyển: đòn kế tiếp +15% tỉ lệ chí mạng; hồi chiêu 8 giây.", "Né nhanh bằng di chuyển: đòn kế tiếp +20% tỉ lệ chí mạng; hồi chiêu 7 giây.", "Né nhanh bằng di chuyển: đòn kế tiếp +25% tỉ lệ chí mạng; hồi chiêu 6 giây."])
    set_card(en, "phantom_step", "While monsters are present, a quick evasive movement when you haven't just taken damage primes bonus crit chance for the next hit; has a cooldown.", ["Quick evasive movement: next hit +15% crit chance; 8s cooldown.", "Quick evasive movement: next hit +20% crit chance; 7s cooldown.", "Quick evasive movement: next hit +25% crit chance; 6s cooldown."])

    set_card(vi, "treasure_hunter", "Hạ quái Tinh Anh/Đỉnh Cấp/Trùm có cơ hội nhận thêm +1 Mảnh Bìa Cardcha.", [f"Tinh Anh/Đỉnh Cấp/Trùm: {p}% cơ hội +1 Mảnh Bìa Cardcha." for p in [10,13,16]])
    set_card(en, "treasure_hunter", "Defeating an Elite/Apex/Boss has a higher chance to grant +1 Cardboard Scrap.", [f"Elite/Apex/Boss: {p}% chance for +1 Cardboard Scrap." for p in [10,13,16]])

    set_card(vi, "mirror_guard", "Sau khi mất ít nhất 25% HP tối đa từ một đòn, đòn kế tiếp nhận vào được giảm mạnh sát thương nếu lá đang sẵn sàng.", ["Mất ≥25% HP tối đa từ một đòn: đòn kế tiếp giảm 30% sát thương; hồi chiêu 12 giây.", "Mất ≥25% HP tối đa từ một đòn: đòn kế tiếp giảm 40% sát thương; hồi chiêu 10 giây.", "Mất ≥25% HP tối đa từ một đòn: đòn kế tiếp giảm 50% sát thương; hồi chiêu 8 giây."])
    set_card(en, "mirror_guard", "After one hit removes at least 25% of max HP, the next incoming hit is heavily reduced if the card is ready.", ["Lose ≥25% max HP to one hit: next hit -30% damage; 12s cooldown.", "Lose ≥25% max HP to one hit: next hit -40% damage; 10s cooldown.", "Lose ≥25% max HP to one hit: next hit -50% damage; 8s cooldown."])

    set_card(vi, "relentless", "Đánh liên tục cùng một mục tiêu sẽ tăng sát thương tới giới hạn; đổi mục tiêu sẽ đặt lại cộng dồn.", ["Cùng mục tiêu: +2% sát thương mỗi đòn, tối đa 5; đổi mục tiêu đặt lại.", "Cùng mục tiêu: +2.5% sát thương mỗi đòn, tối đa 6; đổi mục tiêu đặt lại.", "Cùng mục tiêu: +3% sát thương mỗi đòn, tối đa 7; đổi mục tiêu đặt lại."])
    set_card(en, "relentless", "Repeatedly hitting the same target builds damage up to a cap; switching targets resets the stacks.", ["Same target: +2% damage per hit, max 5; switching targets resets.", "Same target: +2.5% damage per hit, max 6; switching targets resets.", "Same target: +3% damage per hit, max 7; switching targets resets."])

    set_card(vi, "time_breaker", "Đòn có mức sát thương được Cardcha nhận diện như một cú chí mạng có cơ hội tạo đợt tăng tốc đánh mạnh; có hồi chiêu.", ["Đòn được nhận diện như chí mạng: 10% cơ hội +30% tốc độ đánh 3 giây; hồi chiêu 12 giây.", "Đòn được nhận diện như chí mạng: 12% cơ hội +35% tốc độ đánh 3 giây; hồi chiêu 10 giây.", "Đòn được nhận diện như chí mạng: 15% cơ hội +40% tốc độ đánh 3 giây; hồi chiêu 8 giây."])
    set_card(en, "time_breaker", "A hit Cardcha identifies as crit-like can trigger a large attack-speed burst; has an internal cooldown.", ["Crit-like hit: 10% chance for +30% attack speed for 3s; 12s cooldown.", "Crit-like hit: 12% chance for +35% attack speed for 3s; 10s cooldown.", "Crit-like hit: 15% chance for +40% attack speed for 3s; 8s cooldown."])

    set_card(vi, "cardmaster", "Mỗi 10 lượt quay Thường nhận thêm Bụi Ma Thuật; lượt quay Thường kế tiếp tăng rất nhẹ cơ hội Hiếm+ mà không vượt qua bảo hiểm.", ["Mỗi 10 lượt quay Thường: +5 Bụi; lượt Thường kế tiếp +1 điểm % cơ hội Hiếm+.", "Mỗi 10 lượt quay Thường: +7 Bụi; lượt Thường kế tiếp +1.5 điểm % cơ hội Hiếm+.", "Mỗi 10 lượt quay Thường: +10 Bụi; lượt Thường kế tiếp +2 điểm % cơ hội Hiếm+."])
    set_card(en, "cardmaster", "Every 10 Standard pulls grants Magic Dust; the next Standard pull gets a tiny Rare+ chance boost without bypassing pity/insurance.", ["Every 10 Standard pulls: +5 Dust; next Standard +1 percentage point Rare+ chance.", "Every 10 Standard pulls: +7 Dust; next Standard +1.5 percentage points Rare+ chance.", "Every 10 Standard pulls: +10 Dust; next Standard +2 percentage points Rare+ chance."])

    vi_path.write_text(json.dumps(vi, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    en_path.write_text(json.dumps(en, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    cards_path = MOD / "assets" / "cards.json"
    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    for card in cards:
        cid = card.get("Id", "")
        if f"card.{cid}.desc" in vi:
            card["Description"] = vi[f"card.{cid}.desc"]
        rules = []
        for level in range(1, int(card.get("MaxLevel", 1)) + 1):
            key = f"card.{cid}.star.{level}"
            if key in vi:
                rules.append(vi[key])
        if rules:
            card["StarRules"] = rules
    cards_path.write_text(json.dumps(cards, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def patch_audit_doc() -> None:
    path = ROOT / "docs" / "CARD_RUNTIME_AUDIT_ALPHA28_055.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    note = """

## `.4.14.2` remediation pass

The `.4.14.2` finalizer fixes or aligns every unambiguous audit finding except **#20 Victory Charge**, which remains an explicit design blocker because the repository has no Boss Energy subsystem to attach it to.

This pass adds a real Vitality max-HP runtime with save-safe removal/reapply; fixes same-target stacks, Reaper's Mark duration, Last Stand duration/encounter limit, Soul Siphon fractional lifesteal, Mirror Guard cooldown arming, Battle Scholar daily persistence, Void Walker phase semantics, Soul Eater values, Cardmaster Standard-pull counting/next-pull Rare+ nudge, Guardian Angel threshold semantics, Crushing Impact stagger where the Monster exposes a compatible stun timer, and observer-only custom-enemy Core kill progression. Ambiguous loot/heuristic card text is made exact instead of promising a broader mechanic than runtime provides.

Victory Charge deliberately receives no secret substitute buff. In this TEST build its card text explicitly marks the missing Boss Energy dependency.
"""
    if "## `.4.14.2` remediation pass" not in text:
        path.write_text(text + note, encoding="utf-8")


def main() -> None:
    patch_version()
    patch_save_model()
    patch_save_service()
    patch_upgrade_stats()
    patch_core_effects()
    patch_combat_service()
    patch_custom_death()
    patch_gacha()
    patch_mod_entry()
    patch_text()
    patch_audit_doc()
    print(f"Applied Cardcha {VERSION} full active-card runtime audit remediation.")


if __name__ == "__main__":
    main()
