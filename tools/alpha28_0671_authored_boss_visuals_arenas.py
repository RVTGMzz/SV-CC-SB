from pathlib import Path
import base64, json, re, zipfile, io, xml.etree.ElementTree as ET

ROOT = Path("src/Cardcha")
VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.40"
PREV = "0.3.0-alpha.28.0.4.14.4.5.12.39"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"0671 anchor missing: {label}")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, replacement: str, label: str) -> str:
    out, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"0671 regex anchor missing: {label}")
    return out


# Version bump.
manifest_path = ROOT / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["Version"] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
for rel in ["Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
    p = ROOT / rel
    s = p.read_text(encoding="utf-8").replace(PREV, VERSION)
    if rel == "ModEntry.cs":
        s = s.replace("REMAINING BOSS FOUNDATION TEST", "AUTHORED BOSS VISUALS ARENAS TEST")
    p.write_text(s, encoding="utf-8")


# Decode authored 0671 PNG bundle.
bundle_b64 = Path("tools/0671_assets.zip.b64").read_text(encoding="utf-8").strip()
with zipfile.ZipFile(io.BytesIO(base64.b64decode(bundle_b64))) as z:
    for name in z.namelist():
        data = z.read(name)
        target = ROOT / "assets" / name if name.startswith("chacha_") else ROOT / "assets/bosses/milestone" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


# Build three separate arena TMX assets from the stable Boss I geometry while keeping only known-safe tile IDs.
base = ROOT / "assets/verdant_guardian_arena.tmx"

def make_arena(filename: str, role: str, theme: str) -> None:
    tree = ET.parse(base)
    root = tree.getroot()
    props = root.find("properties")
    for prop in props.findall("property"):
        if prop.attrib.get("name") == "CardchaRegionVersion":
            prop.set("value", VERSION)
        elif prop.attrib.get("name") == "CardchaRegionRole":
            prop.set("value", role)
    back = root.find("layer[@name='Back']/data")
    vals = [int(x.strip()) for x in (back.text or "").split(",") if x.strip()]
    w = 28
    for y in range(3, 17):
        for x in range(4, 24):
            i = y * w + x
            if vals[i] != 457:
                continue
            if theme == "curator" and (x in (8, 9, 18, 19) or y in (6, 12)):
                vals[i] = 382
            elif theme == "tricolor" and (((x-8)**2+(y-8)**2 <= 5) or ((x-14)**2+(y-6)**2 <= 5) or ((x-20)**2+(y-8)**2 <= 5)):
                vals[i] = 382
            elif theme == "mimi" and ((x + y) % 5 == 0 or x in (13, 14)):
                vals[i] = 382
    back.text = "\n" + ",".join(str(v) for v in vals) + "\n"
    tree.write(ROOT / "assets" / filename, encoding="UTF-8", xml_declaration=True)

make_arena("boss2_hollow_curator_arena.tmx", "boss2|hollow-curator|library-of-forgotten-cards", "curator")
make_arena("boss3_tricolor_resonance_arena.tmx", "boss3|tricolor-resonance|three-aspects-one-core", "tricolor")
make_arena("boss4_mimi_resonance_arena.tmx", "boss4|mimi|resonance-master|final-boss", "mimi")


# Milestone boss authored art and distinct arena routing.
p = ROOT / "Services/MilestoneBossService.cs"
s = p.read_text(encoding="utf-8")
s = s.replace("/// 0670 functional foundation for the 40/60/80-card milestone bosses.", "/// 0671 authored visual/arena pass for the 40/60/80-card milestone bosses.")
s = replace_once(
    s,
    '    private const string SharedArenaMapPath = "assets/verdant_guardian_arena.tmx";\n',
    '    private const string HollowCuratorMapPath = "assets/boss2_hollow_curator_arena.tmx";\n'
    '    private const string TricolorMapPath = "assets/boss3_tricolor_resonance_arena.tmx";\n'
    '    private const string MimiMapPath = "assets/boss4_mimi_resonance_arena.tmx";\n'
    '    private const string HollowCuratorTexturePath = "assets/bosses/milestone/hollow_curator.png";\n'
    '    private const string HollowArenaTexturePath = "assets/bosses/milestone/hollow_curator_arena_tiles.png";\n'
    '    private const string TricolorGuardiansTexturePath = "assets/bosses/milestone/tricolor_guardians.png";\n'
    '    private const string TricolorUnifiedTexturePath = "assets/bosses/milestone/tricolor_unified.png";\n'
    '    private const string TricolorArenaTexturePath = "assets/bosses/milestone/tricolor_arena_tiles.png";\n'
    '    private const string MimiTexturePath = "assets/bosses/milestone/mimi_resonance_master.png";\n'
    '    private const string MimiArenaTexturePath = "assets/bosses/milestone/mimi_arena_tiles.png";\n',
    "map/art constants",
)
old_asset = '        if (e.NameWithoutLocale.IsEquivalentTo(HollowCuratorMapAssetName)\n            || e.NameWithoutLocale.IsEquivalentTo(TricolorMapAssetName)\n            || e.NameWithoutLocale.IsEquivalentTo(MimiMapAssetName))\n        {\n            e.LoadFromModFile<xTile.Map>(SharedArenaMapPath, AssetLoadPriority.Exclusive);\n        }'
new_asset = '        if (e.NameWithoutLocale.IsEquivalentTo(HollowCuratorMapAssetName))\n        {\n            e.LoadFromModFile<xTile.Map>(HollowCuratorMapPath, AssetLoadPriority.Exclusive);\n            return;\n        }\n        if (e.NameWithoutLocale.IsEquivalentTo(TricolorMapAssetName))\n        {\n            e.LoadFromModFile<xTile.Map>(TricolorMapPath, AssetLoadPriority.Exclusive);\n            return;\n        }\n        if (e.NameWithoutLocale.IsEquivalentTo(MimiMapAssetName))\n            e.LoadFromModFile<xTile.Map>(MimiMapPath, AssetLoadPriority.Exclusive);'
s = replace_once(s, old_asset, new_asset, "distinct arena asset routing")

new_draw_actor = '''    private void DrawActor(SpriteBatch batch, Monster actor, MilestoneBossKind kind)
    {
        string role = this.Role(actor);
        Vector2 feet = Game1.GlobalToLocal(Game1.viewport, actor.Position + new Vector2(32f, 58f));
        Texture2D texture;
        Rectangle source;
        float scale;
        Vector2 offset = Vector2.Zero;
        if (role == "curator")
        {
            texture = this.Helper.ModContent.Load<Texture2D>(HollowCuratorTexturePath);
            int frame = this.State == MilestoneBossState.Telegraph || this.Phase >= 3 ? 1 : 0;
            source = new Rectangle(frame * 48, 0, 48, 64);
            scale = 2.35f;
            offset = new Vector2(0f, 10f);
        }
        else if (role is "ignis" or "vita" or "aether")
        {
            texture = this.Helper.ModContent.Load<Texture2D>(TricolorGuardiansTexturePath);
            int frame = role == "ignis" ? 0 : role == "vita" ? 1 : 2;
            source = new Rectangle(frame * 48, 0, 48, 48);
            scale = 2.3f;
        }
        else if (role == "unified")
        {
            texture = this.Helper.ModContent.Load<Texture2D>(TricolorUnifiedTexturePath);
            int frame = this.State == MilestoneBossState.Telegraph ? 1 : 0;
            source = new Rectangle(frame * 64, 0, 64, 64);
            scale = 2.2f;
        }
        else
        {
            texture = this.Helper.ModContent.Load<Texture2D>(MimiTexturePath);
            int frame = this.Phase >= 4 ? 2 : this.Phase >= 3 ? 1 : 0;
            source = new Rectangle(frame * 64, 0, 64, 64);
            scale = 2.18f;
            offset = new Vector2(0f, 6f);
        }
        float pulse = this.State == MilestoneBossState.PhaseTransition ? 0.88f + 0.12f * (float)Math.Abs(Math.Sin(Environment.TickCount64 / 75d)) : 1f;
        Color tint = this.State == MilestoneBossState.Defeated ? Color.White * 0.58f : Color.White;
        int shadowWidth = (int)(source.Width * scale * 0.62f);
        batch.Draw(Game1.staminaRect, new Rectangle((int)feet.X - shadowWidth / 2, (int)feet.Y - 7, shadowWidth, 9), Color.Black * 0.28f);
        batch.Draw(texture, feet + offset, source, tint, 0f, new Vector2(source.Width / 2f, source.Height), scale * pulse, SpriteEffects.None, 0.99f);
    }
'''
s = regex_once(s, r'    private void DrawActor\(SpriteBatch batch, Monster actor, MilestoneBossKind kind\)\n    \{.*?\n    \}\n\n    private void DrawAttackTelegraph', new_draw_actor + '\n    private void DrawAttackTelegraph', "DrawActor authored replacement")

new_arena = '''    private void DrawArenaIdentity(SpriteBatch batch, MilestoneBossKind kind)
    {
        string path = kind switch
        {
            MilestoneBossKind.HollowCurator => HollowArenaTexturePath,
            MilestoneBossKind.TricolorResonance => TricolorArenaTexturePath,
            _ => MimiArenaTexturePath,
        };
        Texture2D texture = this.Helper.ModContent.Load<Texture2D>(path);
        Point[] placements = kind switch
        {
            MilestoneBossKind.HollowCurator => new[] { new Point(6,5), new Point(21,5), new Point(6,13), new Point(21,13), new Point(10,4), new Point(17,4), new Point(10,15), new Point(17,15) },
            MilestoneBossKind.TricolorResonance => new[] { new Point(8,5), new Point(14,3), new Point(20,5), new Point(5,11), new Point(23,11), new Point(9,14), new Point(14,15), new Point(19,14) },
            _ => new[] { new Point(7,5), new Point(11,4), new Point(16,4), new Point(20,5), new Point(6,12), new Point(21,12), new Point(10,15), new Point(17,15) },
        };
        for (int i = 0; i < placements.Length; i++)
        {
            Point p = placements[i];
            Vector2 local = Game1.GlobalToLocal(Game1.viewport, new Vector2(p.X * 64f + 32, p.Y * 64f + 48));
            Rectangle src = new((i % 4) * 32, ((i / 4) % 2) * 32, 32, 32);
            float scale = kind == MilestoneBossKind.Mimi ? 1.75f : 1.9f;
            batch.Draw(texture, local, src, Color.White * 0.92f, 0f, new Vector2(16f, 32f), scale, SpriteEffects.None, 0.985f);
        }
    }
'''
s = regex_once(s, r'    private void DrawArenaIdentity\(SpriteBatch batch, MilestoneBossKind kind\)\n    \{.*?\n    \}\n\n    private void DrawRetreatGlyph', new_arena + '\n    private void DrawRetreatGlyph', "arena identity authored replacement")
s = s.replace("0670 Boss encounter started:", "0671 Boss encounter started:")
s = s.replace("0670 {this.CurrentKind} victory.", "0671 {this.CurrentKind} victory.")
s = s.replace("0670 MilestoneBoss |", "0671 MilestoneBoss |")
p.write_text(s, encoding="utf-8")


# WorldActorService: add Mirror / Trinity / Resonance ChaCha art and select the active form sheet.
p = ROOT / "Services/WorldActorService.cs"
s = p.read_text(encoding="utf-8")
s = replace_once(s, '    public const string ChaChaGuardianCharacterAsset = "Characters/Ronvotri.Cardcha_ChaCha_GuardianRabbit";\n', '    public const string ChaChaGuardianCharacterAsset = "Characters/Ronvotri.Cardcha_ChaCha_GuardianRabbit";\n    public const string ChaChaMirrorCharacterAsset = "Characters/Ronvotri.Cardcha_ChaCha_MirrorRabbit";\n    public const string ChaChaTrinityCharacterAsset = "Characters/Ronvotri.Cardcha_ChaCha_TrinityRabbit";\n    public const string ChaChaResonanceCharacterAsset = "Characters/Ronvotri.Cardcha_ChaCha_ResonanceRabbit";\n', "ChaCha form assets")
s = replace_once(s, '    private const string ChaChaGuardianSheetPath = "assets/chacha_guardian_rabbit.png";\n', '    private const string ChaChaGuardianSheetPath = "assets/chacha_guardian_rabbit.png";\n    private const string ChaChaMirrorSheetPath = "assets/chacha_mirror_rabbit.png";\n    private const string ChaChaTrinitySheetPath = "assets/chacha_trinity_rabbit.png";\n    private const string ChaChaResonanceSheetPath = "assets/chacha_resonance_rabbit.png";\n', "ChaCha form sheet paths")
s = replace_once(s, '    private bool ChaChaBossVisualActive;\n', '    private bool ChaChaBossVisualActive;\n    private string ChaChaBossVisualForm = "guardian_rabbit";\n', "ChaCha active form state")
s = replace_once(s, '        if (e.Name.IsEquivalentTo(ChaChaGuardianCharacterAsset))\n            e.LoadFromModFile<Texture2D>(ChaChaGuardianSheetPath, AssetLoadPriority.Medium);', '        if (e.Name.IsEquivalentTo(ChaChaGuardianCharacterAsset))\n        {\n            e.LoadFromModFile<Texture2D>(ChaChaGuardianSheetPath, AssetLoadPriority.Medium);\n            return;\n        }\n        if (e.Name.IsEquivalentTo(ChaChaMirrorCharacterAsset))\n        {\n            e.LoadFromModFile<Texture2D>(ChaChaMirrorSheetPath, AssetLoadPriority.Medium);\n            return;\n        }\n        if (e.Name.IsEquivalentTo(ChaChaTrinityCharacterAsset))\n        {\n            e.LoadFromModFile<Texture2D>(ChaChaTrinitySheetPath, AssetLoadPriority.Medium);\n            return;\n        }\n        if (e.Name.IsEquivalentTo(ChaChaResonanceCharacterAsset))\n            e.LoadFromModFile<Texture2D>(ChaChaResonanceSheetPath, AssetLoadPriority.Medium);', "ChaCha asset requests")
s = s.replace('(this.ChaChaBossVisualActive ? ChaChaGuardianCharacterAsset : ChaChaCharacterAsset)', '(this.ChaChaBossVisualActive ? this.GetChaChaBossCharacterAsset() : ChaChaCharacterAsset)')
old_set = '''    public void SetChaChaBossVisual(bool active)
    {
        this.ChaChaBossVisualActive = active;
        NPC? actor = this.FindChaChaActor();
        if (actor is null)
            return;

        bool machineVisual = actor.Sprite is not null
            && string.Equals(actor.Sprite.loadedTexture, ChaChaMachineCharacterAsset, StringComparison.OrdinalIgnoreCase);
        if (!machineVisual)
        {
            string desired = active ? ChaChaGuardianCharacterAsset : ChaChaCharacterAsset;
            int frame = actor.Sprite?.CurrentFrame ?? 0;
            if (actor.Sprite is null
                || actor.Sprite.SpriteWidth != 32
                || actor.Sprite.SpriteHeight != 32
                || !string.Equals(actor.Sprite.loadedTexture, desired, StringComparison.OrdinalIgnoreCase))
            {
                actor.Sprite = new AnimatedSprite(desired, Math.Clamp(frame, 0, 15), 32, 32);
            }
        }

        actor.Scale = active ? ChaChaBossNativeScale : ChaChaNativeScale;
    }'''
new_set = '''    public void SetChaChaBossVisual(bool active)
        => this.SetChaChaBossVisual(active, "guardian_rabbit");

    public void SetChaChaBossVisual(bool active, string formId)
    {
        this.ChaChaBossVisualActive = active;
        this.ChaChaBossVisualForm = active && !string.IsNullOrWhiteSpace(formId) ? formId : "guardian_rabbit";
        NPC? actor = this.FindChaChaActor();
        if (actor is null)
            return;

        bool machineVisual = actor.Sprite is not null
            && string.Equals(actor.Sprite.loadedTexture, ChaChaMachineCharacterAsset, StringComparison.OrdinalIgnoreCase);
        if (!machineVisual)
        {
            string desired = active ? this.GetChaChaBossCharacterAsset() : ChaChaCharacterAsset;
            int frame = actor.Sprite?.CurrentFrame ?? 0;
            if (actor.Sprite is null
                || actor.Sprite.SpriteWidth != 32
                || actor.Sprite.SpriteHeight != 32
                || !string.Equals(actor.Sprite.loadedTexture, desired, StringComparison.OrdinalIgnoreCase))
            {
                actor.Sprite = new AnimatedSprite(desired, Math.Clamp(frame, 0, 15), 32, 32);
            }
        }
        actor.Scale = active ? ChaChaBossNativeScale : ChaChaNativeScale;
    }

    private string GetChaChaBossCharacterAsset() => this.ChaChaBossVisualForm switch
    {
        "mirror_rabbit" => ChaChaMirrorCharacterAsset,
        "trinity_rabbit" => ChaChaTrinityCharacterAsset,
        "resonance_rabbit" => ChaChaResonanceCharacterAsset,
        _ => ChaChaGuardianCharacterAsset,
    };'''
s = replace_once(s, old_set, new_set, "ChaCha boss visual selector")
p.write_text(s, encoding="utf-8")


# ChaCha Boss Form chooses the highest unlocked visual evolution. Gameplay contract stays untouched in 0671.
p = ROOT / "Services/ChaChaBossFormService.cs"
s = p.read_text(encoding="utf-8")
s = replace_once(s, '    public const string GuardianRabbitFormId = "guardian_rabbit";\n', '    public const string GuardianRabbitFormId = "guardian_rabbit";\n    public const string MirrorRabbitFormId = "mirror_rabbit";\n    public const string TrinityRabbitFormId = "trinity_rabbit";\n    public const string ResonanceRabbitFormId = "resonance_rabbit";\n', "boss form ids")
s = replace_once(s, '    private bool DebugGuardianUnlock;\n', '    private bool DebugGuardianUnlock;\n    private string ActiveVisualFormId = GuardianRabbitFormId;\n', "active visual form field")
s = s.replace('    public string ActiveFormId => this.IsActive ? GuardianRabbitFormId : string.Empty;', '    public string ActiveFormId => this.IsActive ? this.ActiveVisualFormId : string.Empty;')
s = s.replace('            this.WorldActors.SetChaChaBossVisual(true);', '            this.WorldActors.SetChaChaBossVisual(true, this.ActiveVisualFormId);')
s = replace_once(s, '        this.ActiveUntil = now + BossFormDurationMs;\n', '        this.ActiveVisualFormId = this.ResolvePreferredFormId();\n        this.ActiveUntil = now + BossFormDurationMs;\n', "resolve form on activation")
s = s.replace('        this.WorldActors.SetChaChaBossVisual(true);', '        this.WorldActors.SetChaChaBossVisual(true, this.ActiveVisualFormId);')
s = s.replace('        Game1.showGlobalMessage(ModEntry.T("chacha.boss.guardian.activated"));', '        Game1.showGlobalMessage($"ChaCha • {this.DescribeFormName(this.ActiveVisualFormId)}!");')
s = s.replace('        this.Monitor.Log($"Guardian Rabbit activated via {source}; duration={BossFormDurationMs}ms, rootPulse={GuardianRootPulseDamage} every {GuardianRootPulseIntervalMs}ms.", LogLevel.Info);', '        this.Monitor.Log($"ChaCha Boss Form {this.ActiveVisualFormId} activated via {source}; duration={BossFormDurationMs}ms, rootPulse={GuardianRootPulseDamage} every {GuardianRootPulseIntervalMs}ms.", LogLevel.Info);')
s = replace_once(s, '    private void EmitGuardianRootPulse(long now)\n', '    private string ResolvePreferredFormId()\n    {\n        HashSet<string>? unlocked = this.Save.Data.BossCardsUnlocked;\n        if (unlocked?.Contains(MilestoneBossService.MimiBossCardId) == true) return ResonanceRabbitFormId;\n        if (unlocked?.Contains(MilestoneBossService.TricolorBossCardId) == true) return TrinityRabbitFormId;\n        if (unlocked?.Contains(MilestoneBossService.MirrorArchiveBossCardId) == true) return MirrorRabbitFormId;\n        return GuardianRabbitFormId;\n    }\n\n    private string DescribeFormName(string id) => id switch\n    {\n        MirrorRabbitFormId => "Mirror Rabbit",\n        TrinityRabbitFormId => "Trinity Rabbit",\n        ResonanceRabbitFormId => "Resonance Rabbit",\n        _ => "Guardian Rabbit",\n    };\n\n    private void EmitGuardianRootPulse(long now)\n', "form resolver methods")
s = replace_once(s, '        this.LastPulseTargets = 0;\n        if (clearDebugUnlock)\n', '        this.LastPulseTargets = 0;\n        this.ActiveVisualFormId = GuardianRabbitFormId;\n        if (clearDebugUnlock)\n', "reset active visual form")
p.write_text(s, encoding="utf-8")


# Handoff source of truth.
handoff = Path("handoff")
(handoff / "ALPHA28_0671_AUTHORED_BOSS_VISUALS_ARENAS.md").write_text(f'''# Alpha28 0671 - Authored Boss Visuals & Arenas

Build: `{VERSION}`
Branch: `cardcha-alpha28-0671-authored-boss-visuals-arenas`
Status: CI/package and in-game acceptance pending.

## Scope
- Boss II/III/IV use authored PNG sprite sheets instead of procedural rectangle/diamond silhouettes.
- Boss II/III/IV each route to a distinct TMX arena.
- Each arena receives authored world-space decorative tiles.
- ChaCha Boss Form visual evolves Guardian -> Mirror -> Trinity -> Resonance from unlocked boss cards.
- Boss Form duration remains 10 seconds and the current Root Pulse gameplay stays unchanged in 0671.

## Visual assets
- Hollow Curator: 2 frames at 48x64.
- Ignis/Vita/Aether: three 48x48 forms.
- Unified Resonance: 2 frames at 64x64.
- MiMi Resonance Master: 3 frames at 64x64.
- Mirror / Trinity / Resonance Rabbit: 32x32-frame 4-direction sheets.

## Regression guards
- 0670 HP/state/reward logic remains intact.
- Save schema remains 19.
- Boss I / 0669 code remains untouched while acceptance is pending.
- `mimi_walk.png` remains locked.
- Card audit remains 76 active / 80 source.
''', encoding="utf-8")
(handoff / "LATEST_CARDCHA_HANDOFF.md").write_text(f'''# Latest Cardcha Handoff

Current branch: `cardcha-alpha28-0671-authored-boss-visuals-arenas`
Current build: `{VERSION}`
Continue from: `handoff/ALPHA28_0671_AUTHORED_BOSS_VISUALS_ARENAS.md`

0669 and 0670 in-game acceptance are still pending. Do not resume from stale `main` or pre-0671 branches.
''', encoding="utf-8")
print("0671 authored boss visuals/arenas generated")
