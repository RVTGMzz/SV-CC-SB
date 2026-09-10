#!/usr/bin/env python3
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'src/Cardcha'
BOSS=SRC/'Services/MilestoneBossService.cs'
OLD='0.3.0-alpha.28.0.4.14.4.5.12.55'
NEW='0.3.0-alpha.28.0.4.14.4.5.12.56'
OLD_BRANCH='cardcha-alpha28-0687-tmx-csv-runtime-load-fix'
BRANCH='cardcha-alpha28-0688-hollow-curator-visual-identity-rebuild'

def need(x,m):
    if not x:raise SystemExit('0688 BUILD FAIL: '+m)
def rep(t,a,b,m):
    if b in t:return t
    need(a in t,'missing anchor: '+m)
    return t.replace(a,b,1)

manifest=json.loads((SRC/'manifest.json').read_text(encoding='utf-8'))
if manifest.get('Version')==NEW:
    need('CuratorAnimationClip' in BOSS.read_text(encoding='utf-8'),'version .56 but runtime visual selector missing')
    print('0688 source already materialized.')
    raise SystemExit(0)
need(manifest.get('Version')==OLD,f'expected {OLD}, found {manifest.get("Version")}')
for rel in ['manifest.json','Cardcha.csproj','Directory.Build.targets','ModEntry.cs']:
    p=SRC/rel;t=p.read_text(encoding='utf-8');need(OLD in t,rel+' old version missing');p.write_text(t.replace(OLD,NEW),encoding='utf-8')

b=BOSS.read_text(encoding='utf-8')
b=rep(b,
'    private const string HollowCuratorTexturePath = "assets/bosses/milestone/hollow_curator.png";\n',
'''    private const string HollowCuratorIdleTexturePath = "assets/bosses/milestone/hollow_curator/idle.png";
    private const string HollowCuratorDriftTexturePath = "assets/bosses/milestone/hollow_curator/drift.png";
    private const string HollowCuratorObserveTexturePath = "assets/bosses/milestone/hollow_curator/observe.png";
    private const string HollowCuratorCastTexturePath = "assets/bosses/milestone/hollow_curator/cast.png";
    private const string HollowCuratorPageVolleyTexturePath = "assets/bosses/milestone/hollow_curator/page_volley.png";
    private const string HollowCuratorMirrorTexturePath = "assets/bosses/milestone/hollow_curator/mirror.png";
    private const string HollowCuratorAdaptTexturePath = "assets/bosses/milestone/hollow_curator/adapt.png";
    private const string HollowCuratorHurtTexturePath = "assets/bosses/milestone/hollow_curator/hurt.png";
    private const string HollowCuratorTransitionTexturePath = "assets/bosses/milestone/hollow_curator/transition.png";
    private const string HollowCuratorDefeatTexturePath = "assets/bosses/milestone/hollow_curator/defeat.png";
''','clip paths')
b=rep(b,'    private int TricolorMotionSerial;\n','    private int TricolorMotionSerial;\n    private int LastCuratorVisualHealth = -1;\n    private long CuratorHurtUntilMs;\n','visual fields')
b=rep(b,'        this.AnchorBossActors();\n\n        if (this.State == MilestoneBossState.Victory)\n','        this.AnchorBossActors();\n        this.UpdateCuratorVisualDamageState(now);\n\n        if (this.State == MilestoneBossState.Victory)\n','hurt update')
b=rep(b,'        this.MimiCadenceIndex = 0;\n        this.TricolorMotionSerial = 0;\n\n        switch (kind)\n','        this.MimiCadenceIndex = 0;\n        this.TricolorMotionSerial = 0;\n        this.LastCuratorVisualHealth = kind == MilestoneBossKind.HollowCurator ? HollowCuratorMaxHealth : -1;\n        this.CuratorHurtUntilMs = 0;\n\n        switch (kind)\n','start visual state')
old='''        if (role == "curator")
        {
            texture = this.Helper.ModContent.Load<Texture2D>(HollowCuratorTexturePath);
            int family = this.CuratorAnimationFamily();
            int anim = (int)((Environment.TickCount64 / 190L + this.DecisionSerial) & 1L);
            int frame = family * 2 + anim;
            source = new Rectangle(frame * 48, 0, 48, 64);
            scale = 1.95f;
            float hover = this.State is MilestoneBossState.Intro or MilestoneBossState.Decision
                ? (float)Math.Sin(Environment.TickCount64 / 240d) * 2f
                : 0f;
            offset = new Vector2(0f, 6f + hover);
        }
'''
new='''        if (role == "curator")
        {
            long now = Environment.TickCount64;
            (string Name, string Path, int Frames, int FrameTicks, bool Loop) clip = this.CuratorAnimationClip(now);
            texture = this.Helper.ModContent.Load<Texture2D>(clip.Path);
            long clock = clip.Loop ? now : Math.Max(0L, now - this.StateStartedAtMs);
            int frame = clip.Loop
                ? (int)((clock / clip.FrameTicks + this.DecisionSerial) % clip.Frames)
                : Math.Min(clip.Frames - 1, (int)(clock / clip.FrameTicks));
            source = new Rectangle(frame * 48, 0, 48, 64);
            scale = 1.95f;
            float hover = this.State is MilestoneBossState.Intro or MilestoneBossState.Decision
                ? (float)Math.Sin(now / 240d) * 2f
                : 0f;
            offset = new Vector2(0f, 6f + hover);
        }
'''
b=rep(b,old,new,'multi clip draw')
old='''    private int CuratorAnimationFamily()
    {
        if (this.State == MilestoneBossState.Defeated)
            return 8;
        if (this.State == MilestoneBossState.PhaseTransition || this.Phase >= 3 && this.State != MilestoneBossState.Telegraph)
            return 7;
        if (this.State != MilestoneBossState.Telegraph)
            return 0;
        return this.CurrentAttack switch
        {
            1 => 1,
            5 => 2,
            6 => 3,
            7 => 4,
            8 => 5,
            4 or 9 => 6,
            3 => 7,
            _ => 1,
        };
    }
'''
new='''    private (string Name, string Path, int Frames, int FrameTicks, bool Loop) CuratorAnimationClip(long now)
    {
        if (this.State == MilestoneBossState.Defeated)
            return ("defeat", HollowCuratorDefeatTexturePath, 12, 145, false);
        if (this.State == MilestoneBossState.PhaseTransition)
            return ("transition", HollowCuratorTransitionTexturePath, 12, 90, false);
        if (this.CuratorHurtUntilMs > now)
            return ("hurt", HollowCuratorHurtTexturePath, 6, 60, true);
        if (this.State == MilestoneBossState.Intro)
            return ("observe", HollowCuratorObserveTexturePath, 10, 120, false);
        if (this.State == MilestoneBossState.Decision)
            return this.Phase >= 2
                ? ("drift", HollowCuratorDriftTexturePath, 8, 105, true)
                : ("idle", HollowCuratorIdleTexturePath, 8, 120, true);
        if (this.State != MilestoneBossState.Telegraph)
            return ("idle", HollowCuratorIdleTexturePath, 8, 120, true);
        return this.CurrentAttack switch
        {
            2 or 4 => ("page_volley", HollowCuratorPageVolleyTexturePath, 10, 82, true),
            3 or 9 => ("mirror", HollowCuratorMirrorTexturePath, 10, 90, true),
            5 or 6 => ("observe", HollowCuratorObserveTexturePath, 10, 95, true),
            8 => ("adapt", HollowCuratorAdaptTexturePath, 10, 90, true),
            _ => ("cast", HollowCuratorCastTexturePath, 10, 86, true),
        };
    }

    private void UpdateCuratorVisualDamageState(long now)
    {
        if (this.CurrentKind != MilestoneBossKind.HollowCurator)
        {
            this.LastCuratorVisualHealth = -1;
            this.CuratorHurtUntilMs = 0;
            return;
        }
        Monster? curator = this.FindRole("curator", includeDead: true);
        if (curator is null)
            return;
        if (this.LastCuratorVisualHealth >= 0 && curator.Health < this.LastCuratorVisualHealth && curator.Health > 0)
            this.CuratorHurtUntilMs = now + 360L;
        this.LastCuratorVisualHealth = curator.Health;
    }
'''
b=rep(b,old,new,'behavior clip selector')
b=rep(b,'        this.MimiCadenceIndex = 0;\n        this.TricolorMotionSerial = 0;\n        this.CuratorAdaptationStacks = 0;\n','        this.MimiCadenceIndex = 0;\n        this.TricolorMotionSerial = 0;\n        this.LastCuratorVisualHealth = -1;\n        this.CuratorHurtUntilMs = 0;\n        this.CuratorAdaptationStacks = 0;\n','reset visual state')
b=rep(b,'$"CuratorAdapt={this.CuratorAdaptationStacks}/3 | CuratorRecord={this.ActiveCuratorRecord.Describe()} | ArchiveRule={this.ActiveCuratorArchiveRule} | BossCards=[{string.Join(\',\', this.Save.Data.BossCardsUnlocked ?? new HashSet<string>())}] | " +\n','$"CuratorAdapt={this.CuratorAdaptationStacks}/3 | CuratorRecord={this.ActiveCuratorRecord.Describe()} | ArchiveRule={this.ActiveCuratorArchiveRule} | CuratorVisual={this.CuratorAnimationClip(Environment.TickCount64).Name} | BossCards=[{string.Join(\',\', this.Save.Data.BossCardsUnlocked ?? new HashSet<string>())}] | " +\n','visual diagnostic')
need('HollowCuratorTexturePath' not in b and 'CuratorAnimationFamily' not in b,'legacy visual runtime remains')
BOSS.write_text(b,encoding='utf-8')

a=ROOT/'render_depth_audit.json'
if a.exists():a.write_text(a.read_text(encoding='utf-8').replace(OLD_BRANCH,BRANCH),encoding='utf-8')
d=ROOT/'handoff/REGION2_ROGUELIKE_DESIGN_DIRECTION.md';t=d.read_text(encoding='utf-8')
note='''\n### 0688 visual identity note\nBoss II is now visually independent from Boss III/IV. Hollow Curator uses a dedicated Forgotten Archive arena architecture and behavior-driven animation clips: idle, drift, observe, cast, page volley, mirror, adapt, hurt, phase transition and defeat. The arena keeps the 0687 collision footprint while replacing the previously shared Buildings shell. Gameplay, Archive Rule adaptation, save schema and actor-depth rendering ownership are unchanged.\n'''
if '### 0688 visual identity note' not in t:d.write_text(t.rstrip()+'\n'+note,encoding='utf-8')
(ROOT/'handoff/ALPHA28_0688_HOLLOW_CURATOR_VISUAL_IDENTITY_REBUILD.md').write_text(f'''# Alpha 28 0688: Hollow Curator Visual Identity Rebuild\n\nBranch: `{BRANCH}`  \nBuild: `{NEW}`\n\n## Why this pass exists\nAsset review found Boss II, III and IV shared the same 94-tile Buildings shell, while Hollow Curator had one 864x64 strip made of nine two-frame families. Boss I already used behavior-specific animation sheets, so Boss II was below the project visual bar.\n\n## Boss II separation\nBoss II now owns a dedicated 32-tile Forgotten Archive architecture sheet. The Buildings layer keeps the exact 0687 non-zero coordinates so collision/combat space stay frozen, but the generic shell is replaced by shelves, carved archive edges, mirrors, catalog drawers and seal props. Back receives non-collision record, paper, mirror-shard and central archive-seal motifs. Boss III/IV maps and visual assets are byte-frozen by CI.\n\n## Hollow Curator animation library\nRuntime no longer references the old two-frame-family strip. Ten dedicated 48x64-frame clips are used: idle 8, drift 8, observe 10, cast 10, page volley 10, mirror 10, adapt 10, hurt 6, phase transition 12, defeat 12. Damage creates a 360ms visual hurt window. Animation selection reads the existing state and attack IDs only.\n\n## Frozen contracts\nHollow Curator stays 2200 HP. Phase 1 stays `new[] {{ 0, 0, 1 }}`. 0686 Archive Rule adaptation, Region II 6-9 nodes/checkpoints 3/6/fare 250g, 40-card gate, save schema 19, 0683 interactions/Final Cache, 0684 room mechanics, 0685 modifiers and 0687 runtime-safe TMX remain unchanged.\n\n## Rendering\nArena identity remains TMX/native world art. Hollow Curator remains on its Monster actor draw slot. RenderedWorld remains transient VFX only.\n\n## Acceptance\nCI validates clip sizes/frame counts, Boss II separation, unchanged collision footprint, runtime-safe TMX, compile/package and Boss III/IV byte freeze. In-game visual acceptance is still required.\n''',encoding='utf-8')
(ROOT/'handoff/LATEST_CARDCHA_HANDOFF.md').write_text(f'''# Latest Cardcha Handoff\n\nCurrent branch: `{BRANCH}`\nCurrent build: `{NEW}`\nContinue from: `handoff/ALPHA28_0688_HOLLOW_CURATOR_VISUAL_IDENTITY_REBUILD.md`\nDesign direction: `handoff/REGION2_ROGUELIKE_DESIGN_DIRECTION.md`\n\n0688 rebuilds Hollow Curator visual identity with a dedicated Forgotten Archive arena, ten behavior-driven animation clips, hurt/transition/defeat feedback and a Boss III/IV visual byte-freeze. Gameplay and 0687 TMX runtime compatibility remain unchanged. In-game visual acceptance is pending.\n''',encoding='utf-8')
print('0688 source/runtime/handoff materialized.')
