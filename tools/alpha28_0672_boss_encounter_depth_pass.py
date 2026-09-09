from pathlib import Path
import json, re

ROOT = Path("src/Cardcha")
VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.41"
PREV = "0.3.0-alpha.28.0.4.14.4.5.12.40"

def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"0672 anchor missing: {label}")
    return text.replace(old, new, 1)

def regex_once(text: str, pattern: str, replacement: str, label: str) -> str:
    out, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"0672 regex anchor missing: {label} ({count})")
    return out

manifest_path = ROOT / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["Version"] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

for rel in ["Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
    p = ROOT / rel
    s = p.read_text(encoding="utf-8").replace(PREV, VERSION)
    if rel == "ModEntry.cs":
        s = s.replace("AUTHORED BOSS VISUALS ARENAS TEST", "BOSS ENCOUNTER DEPTH PASS TEST")
    p.write_text(s, encoding="utf-8")

p = ROOT / "Services/MilestoneBossService.cs"
s = p.read_text(encoding="utf-8")
s = s.replace(
    "/// 0671 authored visual/arena pass for the 40/60/80-card milestone bosses.",
    "/// 0672 encounter-depth pass for the 40/60/80-card milestone bosses."
)
s = replace_once(
    s,
    "    private int CuratorAdaptationStacks;\n    private int DecisionSerial;\n",
    """    private int CuratorAdaptationStacks;
    private int DecisionSerial;
    private Point EchoTargetTile;
    private Point EchoTargetTile2;
    private int MimiCadenceIndex;
    private int TricolorMotionSerial;
""",
    "boss runtime depth fields"
)
s = replace_once(
    s,
    """        this.AttackTargetTile = PlayerTile();
        this.AttackTargetTile2 = this.AttackTargetTile;
""",
    """        this.AttackTargetTile = PlayerTile();
        this.AttackTargetTile2 = this.AttackTargetTile;
        this.EchoTargetTile = this.AttackTargetTile;
        this.EchoTargetTile2 = this.AttackTargetTile2;
        this.MimiCadenceIndex = 0;
        this.TricolorMotionSerial = 0;
""",
    "start encounter depth reset"
)
s = s.replace('this.Monitor.Log($"0671 Boss encounter started: {kind}.', 'this.Monitor.Log($"0672 Boss encounter started: {kind}.')
s = s.replace('this.Monitor.Log($"0671 {this.CurrentKind} victory.', 'this.Monitor.Log($"0672 {this.CurrentKind} victory.')
s = s.replace('return $"0671 MilestoneBoss |', 'return $"0672 MilestoneBoss |')

new_select = '''    private void SelectAttack(long now)
    {
        if (this.CurrentKind is null)
            return;

        this.DecisionSerial++;
        this.EchoTargetTile = this.AttackTargetTile;
        this.EchoTargetTile2 = this.AttackTargetTile2;
        this.AttackTargetTile = PlayerTile();
        this.AttackTargetTile2 = ClampArenaTile(new Point(
            this.AttackTargetTile.X + (this.DecisionSerial % 2 == 0 ? 2 : -2),
            this.AttackTargetTile.Y + (this.DecisionSerial % 3 == 0 ? 1 : 0)
        ));

        switch (this.CurrentKind.Value)
        {
            case MilestoneBossKind.HollowCurator:
            {
                int[] pool = this.Phase switch
                {
                    1 => new[] { 0, 0, 1 },
                    2 => new[] { 0, 1, 2, 4, 4 },
                    _ => new[] { 0, 2, 3, 4, 4 },
                };
                this.CurrentAttack = pool[this.Rng.Next(pool.Length)];
                this.MaybeTeleportPrimary("curator");
                break;
            }

            case MilestoneBossKind.TricolorResonance:
            {
                if (this.Phase >= 4)
                {
                    this.CurrentAttack = this.DecisionSerial % 3 switch
                    {
                        0 => 13,
                        1 => 14,
                        _ => 15,
                    };
                }
                else
                {
                    string[] roles = this.GetBossActors(false)
                        .Select(this.Role)
                        .Where(r => r is "ignis" or "vita" or "aether")
                        .Distinct(StringComparer.OrdinalIgnoreCase)
                        .ToArray();
                    if (roles.Length == 0)
                    {
                        this.BeginPhaseTransition(4, now);
                        return;
                    }

                    string role = roles[this.Rng.Next(roles.Length)];
                    this.RepositionTricolorGuardian(role);
                    this.CurrentAttack = role == "ignis" ? 10 : role == "vita" ? 11 : 12;
                    if (role == "aether")
                    {
                        this.AttackTargetTile2 = ClampArenaTile(new Point(
                            this.AttackTargetTile.X,
                            this.AttackTargetTile.Y + (this.DecisionSerial % 2 == 0 ? 2 : -2)
                        ));
                    }
                }
                break;
            }

            case MilestoneBossKind.Mimi:
            {
                int[] pool = this.Phase switch
                {
                    1 => new[] { 20, 20, 21 },
                    2 => new[] { 20, 22, 26, 26 },
                    3 => new[] { 22, 23, 27, 27 },
                    _ => new[] { 24, 25, 26, 27, 28, 28 },
                };
                this.CurrentAttack = pool[this.Rng.Next(pool.Length)];
                if (this.CurrentAttack == 27)
                    this.MimiCadenceIndex = (this.MimiCadenceIndex + 1) % 3;
                this.MaybeTeleportPrimary("mimi");
                break;
            }
        }

        this.State = MilestoneBossState.Telegraph;
        this.StateStartedAtMs = now;
        this.AttackApplied = false;
        Game1.playSound(this.CurrentAttack is 10 or 24 or 25 or 28 ? "thudStep" : "Cowboy_gunload");
    }

    private void ApplyCurrentAttack()'''
s = regex_once(
    s,
    r"    private void SelectAttack\(long now\)\n    \{.*?\n    \}\n\n    private void ApplyCurrentAttack\(\)",
    new_select,
    "SelectAttack"
)

new_apply = '''    private void ApplyCurrentAttack()
    {
        int extra = this.CuratorAdaptationStacks * 2;
        switch (this.CurrentAttack)
        {
            case 0:
                if (PlayerWithin(this.AttackTargetTile, 1.4f))
                    DamagePlayer(12 + this.Phase * 2 + extra);
                break;
            case 1:
                this.CuratorAdaptationStacks = Math.Min(3, this.CuratorAdaptationStacks + 1);
                Game1.showGlobalMessage($"Hollow Curator adapts • {this.CuratorAdaptationStacks}/3");
                break;
            case 2:
                if (PlayerWithin(this.AttackTargetTile, 2.0f) || PlayerWithin(this.AttackTargetTile2, 1.35f))
                    DamagePlayer(15 + this.Phase * 2 + extra);
                break;
            case 3:
                if (PlayerWithin(this.AttackTargetTile, 2.55f))
                    DamagePlayer(23 + extra);
                break;
            case 4:
                if (PlayerWithin(this.EchoTargetTile, 1.8f) || PlayerWithin(this.EchoTargetTile2, 1.25f))
                    DamagePlayer(17 + this.Phase * 2 + extra);
                Game1.playSound("wand");
                break;

            case 10:
                if (PlayerWithin(this.AttackTargetTile, 2.05f))
                    DamagePlayer(20);
                break;
            case 11:
                foreach (Monster guardian in this.GetBossActors(false).Where(a => this.Role(a) is "ignis" or "vita" or "aether"))
                    guardian.Health = Math.Min(guardian.MaxHealth, guardian.Health + 70);
                if (PlayerWithin(this.AttackTargetTile, 1.5f))
                    DamagePlayer(8);
                Game1.playSound("leafrustle");
                break;
            case 12:
                if (PlayerWithin(this.AttackTargetTile, 1.35f) || PlayerWithin(this.AttackTargetTile2, 1.35f))
                    DamagePlayer(16);
                break;
            case 13:
                if (PlayerWithin(this.AttackTargetTile, 2.35f) || PlayerWithin(this.AttackTargetTile2, 1.6f))
                    DamagePlayer(25);
                break;
            case 14:
                if (PlayerWithin(this.AttackTargetTile, 1.55f) || PlayerWithin(this.EchoTargetTile, 1.55f))
                    DamagePlayer(21);
                break;
            case 15:
                if (PlayerWithin(this.AttackTargetTile, 2.0f)
                    || PlayerWithin(this.AttackTargetTile2, 1.35f)
                    || PlayerWithin(this.EchoTargetTile, 1.35f))
                    DamagePlayer(23);
                break;

            case 20:
                if (PlayerWithin(this.AttackTargetTile, 1.35f))
                    DamagePlayer(15 + this.Phase * 2);
                break;
            case 21:
                if (PlayerWithin(this.AttackTargetTile, 1.8f))
                    DamagePlayer(14);
                break;
            case 22:
                if (PlayerWithin(this.AttackTargetTile, 1.9f) || PlayerWithin(this.AttackTargetTile2, 1.35f))
                    DamagePlayer(17 + this.Phase * 2);
                break;
            case 23:
                if (PlayerWithin(this.AttackTargetTile, 2.3f))
                    DamagePlayer(20 + this.Phase);
                break;
            case 24:
                if (PlayerWithin(this.AttackTargetTile, 2.55f) || PlayerWithin(this.AttackTargetTile2, 1.8f))
                    DamagePlayer(22 + this.Phase * 2);
                break;
            case 25:
                if (PlayerWithin(this.AttackTargetTile, 3.0f))
                    DamagePlayer(30);
                Game1.playSound("explosion");
                break;
            case 26:
                if (PlayerWithin(this.EchoTargetTile, 1.7f) || PlayerWithin(this.EchoTargetTile2, 1.2f))
                    DamagePlayer(18 + this.Phase * 2);
                Game1.playSound("wand");
                break;
            case 27:
            {
                if (this.MimiCadenceIndex == 0)
                {
                    if (PlayerWithin(this.AttackTargetTile, 2.2f))
                        DamagePlayer(24);
                    Game1.playSound("explosion");
                }
                else if (this.MimiCadenceIndex == 1)
                {
                    Monster? mimi = this.FindRole("mimi", false);
                    if (mimi is not null)
                        mimi.Health = Math.Min(mimi.MaxHealth, mimi.Health + 100);
                    if (PlayerWithin(this.AttackTargetTile, 1.4f))
                        DamagePlayer(10);
                    Game1.playSound("leafrustle");
                }
                else
                {
                    if (PlayerWithin(this.AttackTargetTile, 1.45f) || PlayerWithin(this.AttackTargetTile2, 1.45f))
                        DamagePlayer(18);
                    Game1.playSound("wand");
                }
                break;
            }
            case 28:
                if (PlayerWithin(this.AttackTargetTile, 2.75f)
                    || PlayerWithin(this.AttackTargetTile2, 1.75f)
                    || PlayerWithin(this.EchoTargetTile, 1.5f))
                    DamagePlayer(32);
                Game1.playSound("explosion");
                break;
        }
    }

    private void BeginPhaseTransition'''
s = regex_once(
    s,
    r"    private void ApplyCurrentAttack\(\)\n    \{.*?\n    \}\n\n    private void BeginPhaseTransition",
    new_apply,
    "ApplyCurrentAttack"
)

new_anchor = '''    private void AnchorBossActors()
    {
        foreach (Monster actor in this.GetBossActors(false))
        {
            actor.Speed = 0;
            actor.Halt();
        }
    }

    private void RepositionTricolorGuardian(string role)
    {
        Monster? actor = this.FindRole(role, false);
        if (actor is null)
            return;

        this.TricolorMotionSerial++;
        Point target;
        Point player = PlayerTile();
        if (role == "ignis")
        {
            int sx = player.X < 14 ? 1 : -1;
            int sy = this.TricolorMotionSerial % 2 == 0 ? 1 : -1;
            target = ClampArenaTile(new Point(player.X + sx * 2, player.Y + sy));
        }
        else if (role == "vita")
        {
            Point[] pads = { new(11, 5), new(14, 5), new(17, 5), new(14, 8) };
            target = pads[this.TricolorMotionSerial % pads.Length];
        }
        else
        {
            Point[] pads = { new(5, 5), new(22, 5), new(5, 12), new(22, 12), new(14, 4) };
            target = pads[this.TricolorMotionSerial % pads.Length];
        }

        actor.Position = new Vector2(target.X * 64f, target.Y * 64f);
        Game1.playSound(role == "ignis" ? "thudStep" : "wand");
    }

    private void MaybeTeleportPrimary'''
s = regex_once(
    s,
    r"    private void AnchorBossActors\(\)\n    \{.*?\n    \}\n\n    private void MaybeTeleportPrimary",
    new_anchor,
    "AnchorBossActors"
)

old_telegraph_ms = '''    private int CurrentAttackTelegraphMs() => this.CurrentAttack switch
    {
        1 => 900,
        3 => 1050,
        10 => 720,
        11 => 820,
        12 => 680,
        13 => 980,
        25 => 1150,
        24 => 900,
        _ => 760,
    };'''
new_telegraph_ms = '''    private int CurrentAttackTelegraphMs() => this.CurrentAttack switch
    {
        1 => 900,
        3 => 1050,
        4 => 880,
        10 => 720,
        11 => 820,
        12 => 760,
        13 => 980,
        14 => 900,
        15 => 960,
        24 => 900,
        25 => 1150,
        26 => 900,
        27 => 900,
        28 => 1180,
        _ => 760,
    };'''
s = replace_once(s, old_telegraph_ms, new_telegraph_ms, "telegraph durations")

new_draw_telegraph = '''    private void DrawAttackTelegraph(SpriteBatch batch)
    {
        if (this.State != MilestoneBossState.Telegraph || this.CurrentAttack < 0)
            return;

        Color c = this.CurrentKind is null ? Color.White : this.KindColor(this.CurrentKind.Value);
        float pulse = 0.28f + 0.16f * (float)Math.Abs(Math.Sin(Environment.TickCount64 / 90d));
        int radius = this.CurrentAttack switch
        {
            3 or 25 or 28 => 2,
            13 or 24 or 27 => 2,
            _ => 1,
        };

        if (this.CurrentAttack is 4 or 26)
        {
            Color mirror = new Color(190, 166, 255) * (pulse + 0.08f);
            DrawTileZone(batch, this.EchoTargetTile, 1, mirror);
            DrawTileZone(batch, this.EchoTargetTile2, 1, mirror * 0.72f);
            return;
        }

        if (this.CurrentAttack == 27)
            c = this.TricolorCycle(this.MimiCadenceIndex);

        DrawTileZone(batch, this.AttackTargetTile, radius, c * pulse);

        if (this.CurrentAttack is 2 or 12 or 13 or 15 or 22 or 24 or 27 or 28)
            DrawTileZone(batch, this.AttackTargetTile2, 1, new Color(238, 218, 255) * pulse);

        if (this.CurrentAttack is 14 or 28)
            DrawTileZone(batch, this.EchoTargetTile, 1, new Color(190, 166, 255) * pulse);

        if (this.CurrentAttack == 11)
            DrawTileZone(batch, this.AttackTargetTile, 1, new Color(102, 212, 118) * pulse);
    }

    private void DrawArenaIdentity'''
s = regex_once(
    s,
    r"    private void DrawAttackTelegraph\(SpriteBatch batch\)\n    \{.*?\n    \}\n\n    private void DrawArenaIdentity",
    new_draw_telegraph,
    "DrawAttackTelegraph"
)

s = replace_once(
    s,
    '''        this.CuratorAdaptationStacks = 0;
        this.DecisionSerial = 0;
    }
''',
    '''        this.CuratorAdaptationStacks = 0;
        this.DecisionSerial = 0;
        this.EchoTargetTile = Point.Zero;
        this.EchoTargetTile2 = Point.Zero;
        this.MimiCadenceIndex = 0;
        this.TricolorMotionSerial = 0;
    }
''',
    "reset runtime depth fields"
)

p_chacha = ROOT / "Services/ChaChaBossFormService.cs"
c = p_chacha.read_text(encoding="utf-8")
c = c.replace(
    "/// ChaCha Boss Form runtime. Boss I unlocks Guardian Rabbit, an actual Verdant transformation",
    "/// ChaCha Boss Form runtime. 0672 gives Guardian/Mirror/Trinity/Resonance distinct combat pulses"
)
c = replace_once(
    c,
    '''    public const int GuardianRootPulseDamage = 14;
    public const float GuardianRootPulseRadius = 176f;
''',
    '''    public const int GuardianRootPulseDamage = 14;
    public const float GuardianRootPulseRadius = 176f;
    public const int MirrorPulseDamage = 12;
    public const int TrinityPulseDamage = 13;
    public const int ResonancePulseDamage = 16;
''',
    "form pulse constants"
)
c = replace_once(
    c,
    '''    private bool DebugGuardianUnlock;
    private string ActiveVisualFormId = GuardianRabbitFormId;
''',
    '''    private bool DebugGuardianUnlock;
    private string ActiveVisualFormId = GuardianRabbitFormId;
    private int TrinityPulseIndex;
''',
    "trinity pulse state"
)
c = replace_once(
    c,
    '''            if (now >= this.NextRootPulseAt)
            {
                this.EmitGuardianRootPulse(now);
                this.NextRootPulseAt = now + GuardianRootPulseIntervalMs;
            }
''',
    '''            if (now >= this.NextRootPulseAt)
            {
                this.EmitGuardianRootPulse(now);
                this.NextRootPulseAt = now + this.CurrentPulseIntervalMs();
            }
''',
    "dynamic form pulse interval"
)
c = c.replace(
    'this.Monitor.Log("Guardian Rabbit READY: ChaCha Energy reached 100 and Boss I resonance is unlocked.", LogLevel.Info);',
    'this.Monitor.Log($"ChaCha Boss Form READY: next={this.ResolvePreferredFormId()}, Energy=100.", LogLevel.Info);'
)
c = c.replace(
    'this.Monitor.Log($"Guardian Rabbit ended ({reason}).", LogLevel.Trace);',
    'this.Monitor.Log($"ChaCha Boss Form {this.ActiveVisualFormId} ended ({reason}).", LogLevel.Trace);'
)
c = replace_once(
    c,
    '''        this.RootPulseVisualUntil = now + 520;
        this.BossEnergy.SetGainSuppressed(true);
''',
    '''        this.RootPulseVisualUntil = now + 520;
        this.TrinityPulseIndex = 0;
        this.BossEnergy.SetGainSuppressed(true);
''',
    "activation pulse reset"
)

new_describe = '''    public string Describe()
    {
        string chord = $"{this.Controller.GetLabel(ControllerAction.Confirm)}+{this.Controller.GetLabel(ControllerAction.Deselect)}";
        string preferred = this.ResolvePreferredFormId();
        return $"Form={preferred} | ActiveForm={this.ActiveFormId} | Unlocked={this.GuardianRabbitUnlocked} (debug={this.DebugGuardianUnlock}) | " +
               $"Ready={this.IsReady} | Active={this.IsActive} | Remaining={this.SecondsRemaining:0.0}s | " +
               $"Pulse={this.CurrentPulseDamage()} dmg/{this.CurrentPulseIntervalMs() / 1000d:0.##}s radius={this.CurrentPulseRadius():0}px | " +
               $"Pulses={this.GuardianPulseCount} Hits={this.GuardianPulseHits} LastTargets={this.LastPulseTargets} | " +
               $"AuraStage={this.EnergyAuraStage} | ControllerChord={chord} | Keyboard=LeftShift+A | {this.BossEnergy.Describe()}";
    }

    private string ResolvePreferredFormId()'''
c = regex_once(
    c,
    r"    public string Describe\(\)\n    \{.*?\n    \}\n\n    private string ResolvePreferredFormId\(\)",
    new_describe,
    "ChaCha Describe"
)

new_emit = '''    private void EmitGuardianRootPulse(long now)
    {
        this.LastRootPulseAt = now;
        this.RootPulseVisualUntil = now + 520;
        this.GuardianPulseCount++;
        this.LastPulseTargets = 0;

        NPC? actor = this.WorldActors.FindChaChaActor();
        Farmer? who = Game1.player;
        GameLocation? location = Game1.currentLocation;
        if (actor is null || who is null || location is null || actor.currentLocation != location)
            return;

        int damage = this.CurrentPulseDamage();
        float radius = this.CurrentPulseRadius();
        int bonusDamage = 0;
        int heal = 0;

        if (this.ActiveVisualFormId == MirrorRabbitFormId)
        {
            bonusDamage = 6;
        }
        else if (this.ActiveVisualFormId == TrinityRabbitFormId)
        {
            this.TrinityPulseIndex = (this.TrinityPulseIndex + 1) % 3;
            if (this.TrinityPulseIndex == 0)
                damage = 19;
            else if (this.TrinityPulseIndex == 1)
                heal = 5;
            else
                radius = 232f;
        }
        else if (this.ActiveVisualFormId == ResonanceRabbitFormId)
        {
            bonusDamage = 5;
            heal = 3;
            radius = 224f;
        }

        Vector2 center = actor.Position + new Vector2(16f, 16f);
        float radiusSq = radius * radius;
        List<Monster> targets = location.characters
            .OfType<Monster>()
            .Where(monster => monster.Health > 0
                              && Vector2.DistanceSquared(monster.Position + new Vector2(32f, 32f), center) <= radiusSq)
            .ToList();

        foreach (Monster monster in targets)
        {
            try
            {
                monster.takeDamage(damage, 0, 0, false, 0d, who);
                if (bonusDamage > 0 && monster.Health > 0)
                    monster.takeDamage(bonusDamage, 0, 0, false, 0d, who);
                this.GuardianPulseHits++;
                this.LastPulseTargets++;
            }
            catch (Exception ex)
            {
                ModEntry.LogOnce("chacha-boss-form-pulse", $"ChaCha Boss Form pulse couldn't damage a target: {ex.Message}");
            }
        }

        if (heal > 0 && who.health > 0)
            who.health = Math.Min(who.maxHealth, who.health + heal);

        Game1.playSound(this.ActiveVisualFormId switch
        {
            MirrorRabbitFormId => "wand",
            TrinityRabbitFormId when this.TrinityPulseIndex == 1 => "leafrustle",
            ResonanceRabbitFormId => "discoverMineral",
            _ => targets.Count > 0 ? "leafrustle" : "dirtyHit",
        });
    }

    private int CurrentPulseDamage() => this.ActiveVisualFormId switch
    {
        MirrorRabbitFormId => MirrorPulseDamage,
        TrinityRabbitFormId => TrinityPulseDamage,
        ResonanceRabbitFormId => ResonancePulseDamage,
        _ => GuardianRootPulseDamage,
    };

    private int CurrentPulseIntervalMs() => this.ActiveVisualFormId switch
    {
        MirrorRabbitFormId => 1900,
        TrinityRabbitFormId => 1800,
        ResonanceRabbitFormId => 1700,
        _ => GuardianRootPulseIntervalMs,
    };

    private float CurrentPulseRadius() => this.ActiveVisualFormId switch
    {
        MirrorRabbitFormId => 192f,
        TrinityRabbitFormId => 188f,
        ResonanceRabbitFormId => 224f,
        _ => GuardianRootPulseRadius,
    };

    private Color CurrentPulseColor() => this.ActiveVisualFormId switch
    {
        MirrorRabbitFormId => new Color(174, 154, 255),
        TrinityRabbitFormId => this.TricolorPulseColor(),
        ResonanceRabbitFormId => new Color(238, 171, 255),
        _ => new Color(108, 224, 103),
    };

    private Color TricolorPulseColor() => this.TrinityPulseIndex switch
    {
        0 => new Color(238, 92, 78),
        1 => new Color(99, 210, 118),
        _ => new Color(89, 148, 241),
    };

    private void ResetRuntime'''
c = regex_once(
    c,
    r"    private void EmitGuardianRootPulse\(long now\)\n    \{.*?\n    \}\n\n    private void ResetRuntime",
    new_emit,
    "ChaCha pulse identity"
)
c = replace_once(
    c,
    '''        this.LastPulseTargets = 0;
        this.ActiveVisualFormId = GuardianRabbitFormId;
''',
    '''        this.LastPulseTargets = 0;
        this.ActiveVisualFormId = GuardianRabbitFormId;
        this.TrinityPulseIndex = 0;
''',
    "reset trinity pulse"
)
c = replace_once(
    c,
    '''        if (this.IsActive)
            return new Color(105, 224, 100);
''',
    '''        if (this.IsActive)
            return this.CurrentPulseColor();
''',
    "active aura color"
)
c = replace_once(
    c,
    '''            Color pulseColor = new(108, 224, 103);
''',
    '''            Color pulseColor = this.CurrentPulseColor();
''',
    "root pulse color"
)

p.write_text(s, encoding="utf-8")
p_chacha.write_text(c, encoding="utf-8")

handoff = f'''# Alpha28 0672 - Boss Encounter Depth Pass

Build: `{VERSION}`
Branch: `cardcha-alpha28-0672-boss-encounter-depth-pass`
Status: CI/package and in-game acceptance pending.

## Scope
- Boss II Hollow Curator gains memory-based Mirror Echo attacks that replay prior danger tiles.
- Boss III Tricolor Guardians no longer snap to fixed spawn pads; Ignis, Vita and Aether reposition by role.
- Unified Resonance cycles three distinct attack patterns.
- Boss IV MiMi gains Mirror Echo, Tricolor Cadence and final Resonance Mix mechanics in later phases.
- ChaCha Guardian/Mirror/Trinity/Resonance forms now have distinct pulse gameplay identities.
- Boss Form duration remains 10 seconds. Boss Energy gain pacing remains unchanged.

## ChaCha form identity
- Guardian Rabbit: 14 damage, 176px pulse, 2.0s cadence.
- Mirror Rabbit: 12 + 6 echo damage, 192px, 1.9s cadence.
- Trinity Rabbit: rotating Ignis/Vita/Aether pulse identity, 1.8s cadence.
- Resonance Rabbit: 16 + 5 echo damage, 224px, small self-heal, 1.7s cadence.

## Regression guards
- 0671 authored PNG/TMX assets remain present and are not redrawn in 0672.
- 0670 milestone HP/reward thresholds remain unchanged.
- Boss I/0669 remains untouched while acceptance is pending.
- Save schema remains 19.
- `mimi_walk.png` remains locked.
- Card audit remains 76 active / 80 source.

## TEST
- `cardcha_test_boss2`
- `cardcha_test_boss3`
- `cardcha_test_boss4`
- `cardcha_boss_milestone_status`
- `cardcha_chacha_boss_status`
'''
Path("handoff/ALPHA28_0672_BOSS_ENCOUNTER_DEPTH_PASS.md").write_text(handoff, encoding="utf-8")
Path("handoff/LATEST_CARDCHA_HANDOFF.md").write_text(
    f'''# Latest Cardcha Handoff

Current branch: `cardcha-alpha28-0672-boss-encounter-depth-pass`
Current build: `{VERSION}`
Continue from: `handoff/ALPHA28_0672_BOSS_ENCOUNTER_DEPTH_PASS.md`

0669-0671 in-game acceptance is still pending. Do not resume from stale `main` or pre-0672 branches.
''',
    encoding="utf-8",
)

print("0672 generator complete")
