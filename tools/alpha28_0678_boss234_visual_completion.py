#!/usr/bin/env python3
from pathlib import Path
import json, re, xml.etree.ElementTree as ET
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src' / 'Cardcha'
OLD = '0.3.0-alpha.28.0.4.14.4.5.12.45.3.1'
NEW = '0.3.0-alpha.28.0.4.14.4.5.12.46'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'0678 generator: expected exactly one {label}, found {count}')
    return text.replace(old, new, 1)

# ---- version ----
manifest_path = SRC / 'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['Version'] = NEW
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

for rel in ['Cardcha.csproj', 'Directory.Build.targets']:
    p = SRC / rel
    t = p.read_text(encoding='utf-8')
    if OLD not in t:
        raise SystemExit(f'0678 generator: old version missing in {rel}')
    p.write_text(t.replace(OLD, NEW), encoding='utf-8')

entry_path = SRC / 'ModEntry.cs'
entry = entry_path.read_text(encoding='utf-8')
entry = entry.replace(OLD, NEW)
entry = entry.replace('AIRSHIP TWO-ROOM NATIVE DECOR REBUILD TEST', 'BOSS II-IV VISUAL COMPLETION + ACTOR DEPTH TEST')
anchor = '        VerdantGuardianProxyDrawPatch.Apply(harmony);\n        RegionExpeditionProxyDrawPatch.Apply(harmony);'
if anchor not in entry:
    raise SystemExit('0678 generator: Harmony anchor missing in ModEntry')
entry = entry.replace(anchor,
    '        VerdantGuardianProxyDrawPatch.Apply(harmony);\n'
    '        MilestoneBossActorDrawPatch.Apply(harmony, this.MilestoneBosses, this.Monitor);\n'
    '        RegionExpeditionProxyDrawPatch.Apply(harmony);', 1)
entry_path.write_text(entry, encoding='utf-8')

# ---- Boss actor renderer migration ----
svc_path = SRC / 'Services' / 'MilestoneBossService.cs'
svc = svc_path.read_text(encoding='utf-8')
old_rw = '''        this.DrawArenaIdentity(e.SpriteBatch, kind.Value);\n        foreach (Monster actor in this.GetBossActors(includeDead: true))\n            this.DrawActor(e.SpriteBatch, actor, kind.Value);\n        this.DrawAttackTelegraph(e.SpriteBatch);\n        this.DrawRetreatGlyph(e.SpriteBatch);'''
new_rw = '''        // 0678 depth contract: physical boss bodies and arena props are NOT drawn here.\n        // Boss bodies are injected at Monster.draw; arena identity lives in TMX ground layers.\n        this.DrawBossAuraVfx(e.SpriteBatch, kind.Value);\n        this.DrawAttackTelegraph(e.SpriteBatch);\n        this.DrawRetreatGlyph(e.SpriteBatch);'''
if old_rw not in svc:
    raise SystemExit('0678 generator: Milestone OnRenderedWorld body anchor missing')
svc = svc.replace(old_rw, new_rw, 1)

start = svc.index('    private void DrawActor(SpriteBatch batch, Monster actor, MilestoneBossKind kind)')
end = svc.index('    private void DrawAttackTelegraph(SpriteBatch batch)', start)
new_draw = r'''    internal void DrawActorAtMonsterDepth(SpriteBatch batch, Monster actor)
    {
        if (!actor.modData.ContainsKey(BossMarkerKey) || actor.Health <= 0)
            return;

        MilestoneBossKind kind = this.ResolveCurrentKind(actor.currentLocation ?? Game1.currentLocation)
            ?? this.CurrentKind
            ?? MilestoneBossKind.HollowCurator;
        string role = this.Role(actor);
        Vector2 feet = Game1.GlobalToLocal(Game1.viewport, actor.Position + new Vector2(32f, 58f));
        Texture2D texture;
        Rectangle source;
        float scale;
        Vector2 offset = Vector2.Zero;

        if (role == "curator")
        {
            texture = this.Helper.ModContent.Load<Texture2D>(HollowCuratorTexturePath);
            int frame = this.State == MilestoneBossState.PhaseTransition ? 2
                : this.Phase >= 3 ? 3
                : this.State == MilestoneBossState.Telegraph ? 1
                : 0;
            source = new Rectangle(frame * 48, 0, 48, 64);
            scale = 1.95f;
            offset = new Vector2(0f, 6f);
        }
        else if (role is "ignis" or "vita" or "aether")
        {
            texture = this.Helper.ModContent.Load<Texture2D>(TricolorGuardiansTexturePath);
            int roleIndex = role == "ignis" ? 0 : role == "vita" ? 1 : 2;
            int active = (this.State == MilestoneBossState.Telegraph || this.State == MilestoneBossState.PhaseTransition) ? 1 : 0;
            source = new Rectangle((roleIndex * 2 + active) * 48, 0, 48, 48);
            scale = 1.85f;
        }
        else if (role == "unified")
        {
            texture = this.Helper.ModContent.Load<Texture2D>(TricolorUnifiedTexturePath);
            int frame = this.State == MilestoneBossState.PhaseTransition ? 2
                : this.State == MilestoneBossState.Telegraph ? 1 + (this.DecisionSerial & 1)
                : this.Phase >= 4 ? 3
                : 0;
            source = new Rectangle(frame * 64, 0, 64, 64);
            scale = 1.85f;
        }
        else
        {
            texture = this.Helper.ModContent.Load<Texture2D>(MimiTexturePath);
            int frame = this.Phase >= 4 ? 3 : this.Phase >= 3 ? 2 : this.Phase >= 2 ? 1 : 0;
            source = new Rectangle(frame * 64, 0, 64, 64);
            scale = 1.80f;
            offset = new Vector2(0f, 4f);
        }

        float pulse = this.State == MilestoneBossState.PhaseTransition
            ? 0.96f + 0.04f * (float)Math.Abs(Math.Sin(Environment.TickCount64 / 75d))
            : 1f;
        Color tint = this.State == MilestoneBossState.Defeated ? Color.White * 0.58f : Color.White;
        float actorLayer = Math.Clamp(actor.getStandingY() / 10000f, 0.0002f, 0.995f);
        float shadowLayer = Math.Max(0.0001f, actorLayer - 0.0001f);
        int shadowWidth = (int)(source.Width * scale * 0.58f);
        batch.Draw(Game1.staminaRect,
            new Rectangle((int)feet.X - shadowWidth / 2, (int)feet.Y - 6, shadowWidth, 8),
            null, Color.Black * 0.24f, 0f, Vector2.Zero, SpriteEffects.None, shadowLayer);
        batch.Draw(texture, feet + offset, source, tint, 0f,
            new Vector2(source.Width / 2f, source.Height), scale * pulse,
            SpriteEffects.None, actorLayer);
    }

    private void DrawBossAuraVfx(SpriteBatch batch, MilestoneBossKind kind)
    {
        // VFX only. Low-alpha accents may overlap actors but never pretend to be solid scenery.
        long now = Environment.TickCount64;
        foreach (Monster actor in this.GetBossActors(includeDead: false))
        {
            string role = this.Role(actor);
            Vector2 world = actor.Position + new Vector2(32f, 50f);
            Vector2 c = Game1.GlobalToLocal(Game1.viewport, world);
            Color accent = role switch
            {
                "ignis" => new Color(235, 105, 74),
                "vita" => new Color(105, 205, 124),
                "aether" => new Color(105, 174, 235),
                "unified" => new Color(212, 161, 232),
                "mimi" => new Color(199, 139, 218),
                _ => new Color(166, 190, 232),
            };
            float pulse = 0.16f + 0.07f * (float)Math.Sin(now / 180d + actor.GetHashCode() * 0.01d);
            for (int i = 0; i < 4; i++)
            {
                float a = (float)(now / 520d + i * MathHelper.PiOver2);
                Vector2 p = c + new Vector2(MathF.Cos(a) * 34f, MathF.Sin(a) * 14f - 22f);
                batch.Draw(Game1.staminaRect, new Rectangle((int)p.X, (int)p.Y, 3, 3), accent * pulse);
            }
        }
    }

'''
svc = svc[:start] + new_draw + svc[end:]

# Remove legacy physical arena-prop renderer completely. Ground identity is authored into TMX below.
try:
    a = svc.index('    private void DrawArenaIdentity(SpriteBatch batch, MilestoneBossKind kind)')
    b = svc.index('    private void DrawRetreatGlyph(SpriteBatch batch)', a)
    svc = svc[:a] + svc[b:]
except ValueError:
    raise SystemExit('0678 generator: legacy DrawArenaIdentity block missing')

svc = svc.replace('/// 0672 encounter-depth pass for the 40/60/80-card milestone bosses.',
                  '/// 0678 visual-completion pass for the 40/60/80-card milestone bosses.')
svc_path.write_text(svc, encoding='utf-8')

# Existing Verdant suppression must no longer swallow milestone actors before the dedicated 0678 renderer runs.
vp_path = SRC / 'Patches' / 'VerdantGuardianProxyDrawPatch.cs'
vp = vp_path.read_text(encoding='utf-8')
vp = vp.replace('\n           && !__instance.modData.ContainsKey(MilestoneBossService.BossMarkerKey);', ';')
vp_path.write_text(vp, encoding='utf-8')

# ---- authored boss sprite expansion, preserving original pixel art as the base ----
def crop_frames(img: Image.Image, fw: int, fh: int):
    return [img.crop((x, 0, x + fw, fh)) for x in range(0, img.width, fw)]

def pixel_spark(frame: Image.Image, color, points):
    out = frame.copy().convert('RGBA')
    d = ImageDraw.Draw(out)
    for x,y in points:
        d.point((x,y), fill=color)
        if x+1 < out.width: d.point((x+1,y), fill=color)
    return out

def save_sheet(path: Path, frames):
    w = sum(f.width for f in frames); h = max(f.height for f in frames)
    out = Image.new('RGBA', (w,h), (0,0,0,0))
    x=0
    for f in frames:
        out.alpha_composite(f.convert('RGBA'), (x,0)); x += f.width
    out.save(path, optimize=False)

boss_dir = SRC / 'assets' / 'bosses' / 'milestone'
# Curator: idle / attack / mirror-focus / truth.
p = boss_dir/'hollow_curator.png'; f=crop_frames(Image.open(p).convert('RGBA'),48,64)
base0=f[0]; base1=f[min(1,len(f)-1)]
frame2=pixel_spark(base1,(181,222,255,255),[(10,11),(36,11),(8,26),(39,28),(23,6)])
frame3=pixel_spark(base1,(218,181,255,255),[(6,18),(41,18),(12,37),(35,37),(23,3),(24,3)])
save_sheet(p,[base0,base1,frame2,frame3])

# Tricolor guardians: two frames per identity.
p=boss_dir/'tricolor_guardians.png'; f=crop_frames(Image.open(p).convert('RGBA'),48,48)
cols=[(255,126,78,255),(111,224,124,255),(112,190,255,255)]
frames=[]
for i in range(3):
    base=f[min(i,len(f)-1)]
    frames.append(base)
    frames.append(pixel_spark(base,cols[i],[(7+i*2,9),(38-i*2,12),(10,34),(36,31),(23,4)]))
save_sheet(p,frames)

# Unified: four resonance states.
p=boss_dir/'tricolor_unified.png'; f=crop_frames(Image.open(p).convert('RGBA'),64,64)
b0=f[0]; b1=f[min(1,len(f)-1)]
b2=pixel_spark(b1,(123,214,255,255),[(10,12),(53,12),(14,45),(49,45),(31,5)])
b3=pixel_spark(b1,(238,186,104,255),[(6,28),(57,28),(18,9),(45,9),(31,2),(32,2)])
save_sheet(p,[b0,b1,b2,b3])

# MiMi boss art only. mimi_walk.png is intentionally untouched.
p=boss_dir/'mimi_resonance_master.png'; f=crop_frames(Image.open(p).convert('RGBA'),64,64)
b0=f[0]; b1=f[min(1,len(f)-1)]; b2=f[min(2,len(f)-1)]
b3=pixel_spark(b2,(240,203,124,255),[(8,15),(55,15),(13,39),(50,39),(31,3),(32,3),(22,7),(41,7)])
save_sheet(p,[b0,b1,b2,b3])

# ---- native TMX ground identity ----
def make_tiles(path: Path, palette, motif: str):
    img=Image.new('RGBA',(128,16),(0,0,0,0)); d=ImageDraw.Draw(img)
    for cell in range(8):
        ox=cell*16; c=palette[cell%len(palette)]
        if motif=='mirror':
            d.line((ox+3,8,ox+8,3,ox+12,8,ox+8,13,ox+3,8),fill=c,width=1)
            if cell%2: d.point((ox+8,8),fill=(245,245,255,210))
        elif motif=='tri':
            d.line((ox+8,2,ox+3,12,ox+13,12,ox+8,2),fill=c,width=1)
            d.point((ox+8,8),fill=(255,245,220,200))
        else:
            d.ellipse((ox+3,3,ox+12,12),outline=c,width=1)
            d.line((ox+8,1,ox+8,14),fill=c,width=1)
            if cell%2==0: d.line((ox+1,8,ox+14,8),fill=c,width=1)
    img.save(path, optimize=False)

make_tiles(boss_dir/'hollow_curator_ground_tiles.png',[(139,190,222,190),(185,157,222,190),(213,220,230,170)],'mirror')
make_tiles(boss_dir/'tricolor_ground_tiles.png',[(229,103,75,190),(98,194,112,190),(91,157,220,190)],'tri')
make_tiles(boss_dir/'mimi_ground_tiles.png',[(194,130,215,190),(93,190,192,190),(226,174,94,190)],'ring')


def parse_csv(text):
    return [int(x.strip()) for x in (text or '').replace('\n','').split(',') if x.strip()]

def csv_text(vals,w):
    return '\n' + '\n'.join(','.join(str(v) for v in vals[y*w:(y+1)*w]) + ',' for y in range(len(vals)//w)) + '\n'

def add_ground_layer(tmx_path: Path, tile_file: str, placements):
    tree=ET.parse(tmx_path); root=tree.getroot(); w=int(root.attrib['width']); h=int(root.attrib['height'])
    # remove prior 0678 layer/tileset if generator reruns
    for layer in list(root.findall('layer')):
        if layer.attrib.get('name')=='CardchaArenaGround': root.remove(layer)
    for ts in list(root.findall('tileset')):
        image=ts.find('image')
        if image is not None and image.attrib.get('source')==tile_file: root.remove(ts)
    max_gid=1
    for ts in root.findall('tileset'):
        first=int(ts.attrib.get('firstgid','1')); count=int(ts.attrib.get('tilecount','1')); max_gid=max(max_gid,first+count)
    firstgid=max_gid
    ts=ET.Element('tileset',{'firstgid':str(firstgid),'name':'CardchaArenaGround','tilewidth':'16','tileheight':'16','tilecount':'8','columns':'8'})
    ET.SubElement(ts,'image',{'source':tile_file,'width':'128','height':'16'})
    # insert after vanilla tileset(s), before layers
    insert_at=0
    for i,ch in enumerate(list(root)):
        if ch.tag in ('properties','tileset'): insert_at=i+1
    root.insert(insert_at,ts)
    vals=[0]*(w*h)
    for x,y,cell in placements:
        if 0<=x<w and 0<=y<h: vals[y*w+x]=firstgid+cell
    layer=ET.Element('layer',{'id':'4','name':'CardchaArenaGround','width':str(w),'height':str(h)})
    data=ET.SubElement(layer,'data',{'encoding':'csv'}); data.text=csv_text(vals,w)
    # layer must be directly after Back so it is guaranteed beneath actors.
    children=list(root); back_index=next(i for i,ch in enumerate(children) if ch.tag=='layer' and ch.attrib.get('name')=='Back')
    root.insert(back_index+1,layer)
    root.attrib['nextlayerid']='5'
    props=root.find('properties')
    if props is not None:
        for prop in props.findall('property'):
            if prop.attrib.get('name')=='CardchaRegionVersion': prop.set('value',NEW)
            if prop.attrib.get('name')=='CardchaAssetPolicy': prop.set('value','cardcha-owned-map|cardcha-owned-ground-tiles|no-third-party-assets')
    ET.indent(tree,space=' ')
    tree.write(tmx_path,encoding='UTF-8',xml_declaration=True)

ring2=[(14,3,0),(10,4,1),(18,4,1),(7,7,2),(21,7,2),(6,11,3),(22,11,3),(9,14,4),(19,14,4),(14,15,5),(11,10,6),(17,10,6)]
ring3=[(14,3,2),(8,5,0),(20,5,0),(5,9,1),(23,9,1),(8,14,2),(20,14,2),(14,15,1),(11,8,0),(17,8,2),(11,12,1),(17,12,0)]
ring4=[(14,3,0),(10,4,1),(18,4,2),(7,7,3),(21,7,4),(6,12,5),(22,12,6),(10,15,7),(18,15,7),(14,14,0),(11,10,1),(17,10,2)]
add_ground_layer(SRC/'assets'/'boss2_hollow_curator_arena.tmx','bosses/milestone/hollow_curator_ground_tiles.png',ring2)
add_ground_layer(SRC/'assets'/'boss3_tricolor_resonance_arena.tmx','bosses/milestone/tricolor_ground_tiles.png',ring3)
add_ground_layer(SRC/'assets'/'boss4_mimi_resonance_arena.tmx','bosses/milestone/mimi_ground_tiles.png',ring4)

# Handoff is materialized with source.
handoff = ROOT/'handoff'/'ALPHA28_0678_BOSS234_VISUAL_COMPLETION.md'
handoff.write_text(f'''# Alpha.28 0678 — Boss II-IV Visual Completion + Actor Depth\n\nBranch: `cardcha-alpha28-0678-boss234-visual-completion`\nBuild: `{NEW}`\n\n## Scope\n- Boss II/III/IV physical bodies now render from the declared `Monster.draw(SpriteBatch)` slot through `MilestoneBossActorDrawPatch`.\n- `MilestoneBossService.OnRenderedWorld` owns VFX only: aura, telegraphs, retreat cue.\n- Fixed 0.99/0.985 physical post-world depths removed from milestone boss rendering.\n- Hollow Curator expanded to 4 states; Ignis/Vita/Aether to 2 frames each; Unified to 4 states; MiMi Resonance Master to 4 states.\n- Boss scale reduced to 1.80-1.95x to avoid blown-up pixel art.\n- Three Cardcha-owned transparent 16px ground tile sheets are embedded into each arena TMX as `CardchaArenaGround`, under actors.\n- `mimi_walk.png` is untouched.\n- Gameplay values, HP, attack timings, rewards, 40/60/80 route gates, Boss Form pacing and save schema remain unchanged.\n\n## In-game acceptance\nRun `cardcha_test_boss2`, `cardcha_test_boss3`, `cardcha_test_boss4`. Screenshot each arena with Farmer standing both above and below the boss. Physical boss art must sort naturally and never swallow the Farmer. Boss III should show three distinct guardians and then Unified; Boss IV phase changes should visibly progress.\n''',encoding='utf-8')
(ROOT/'handoff'/'LATEST_CARDCHA_HANDOFF.md').write_text(f'''# Latest Cardcha Handoff\n\nCurrent branch: `cardcha-alpha28-0678-boss234-visual-completion`\nCurrent build: `{NEW}`\nContinue from: `handoff/ALPHA28_0678_BOSS234_VISUAL_COMPLETION.md`\n\n0678 is the Boss II-IV visual completion/depth migration pass. In-game visual acceptance is pending. `mimi_walk.png` remains locked.\n''',encoding='utf-8')

print('0678 generator complete')
