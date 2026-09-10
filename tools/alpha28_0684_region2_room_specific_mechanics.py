#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha"
OLD = "0.3.0-alpha.28.0.4.14.4.5.12.51"
NEW = "0.3.0-alpha.28.0.4.14.4.5.12.52"
SERVICE = SRC / "Services" / "Region2RoguelikeRunService.cs"


def need(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("0684 BUILD FAIL: " + msg)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    need(old in text, "missing anchor: " + label)
    return text.replace(old, new, 1)


manifest = json.loads((SRC / "manifest.json").read_text(encoding="utf-8"))
service_text = SERVICE.read_text(encoding="utf-8")
if manifest.get("Version") == NEW and "0684RoomMechanic" in service_text:
    print("0684 already materialized; generator is idempotent.")
    raise SystemExit(0)

need(manifest.get("Version") == OLD, f"expected {OLD}, found {manifest.get('Version')}")

# Exact build bump. Keep all gameplay/save contracts otherwise untouched.
for rel in ["manifest.json", "Cardcha.csproj", "Directory.Build.targets", "ModEntry.cs"]:
    p = SRC / rel
    text = p.read_text(encoding="utf-8")
    need(OLD in text, f"{rel} missing old build version")
    p.write_text(text.replace(OLD, NEW), encoding="utf-8")

p = SERVICE
t = p.read_text(encoding="utf-8")
t = replace_once(
    t,
    "using Microsoft.Xna.Framework;\n",
    "using Microsoft.Xna.Framework;\nusing Microsoft.Xna.Framework.Graphics;\n",
    "SpriteBatch namespace",
)

# Mechanic runtime state. The marker token is intentionally machine-auditable.
t = replace_once(
    t,
    '    private const string InteractionMarkerKey = "Ronvotri.Cardcha/0683Region2Interaction";\n    private const long ExtractConfirmWindowMs = 5000L;',
    '    private const string InteractionMarkerKey = "Ronvotri.Cardcha/0683Region2Interaction";\n    private const string RoomMechanicMarkerKey = "Ronvotri.Cardcha/0684RoomMechanic";\n    private const long ExtractConfirmWindowMs = 5000L;\n    private const long MirrorTelegraphMs = 1050L;\n    private const long InkTelegraphMs = 900L;\n    private const long VaultTelegraphMs = 950L;',
    "mechanic constants",
)
t = replace_once(
    t,
    '    private string LastCuratorRecord = "none";\n',
    '    private string LastCuratorRecord = "none";\n    private string ActiveRoomMechanic = "none";\n    private long RoomMechanicNextAtMs;\n    private long RoomMechanicResolveAtMs;\n    private Point[] RoomMechanicTiles = Array.Empty<Point>();\n    private int RoomMechanicCycles;\n    private int RoomMechanicHits;\n',
    "mechanic state",
)

# Room mechanics tick before normal node-clear resolution.
old_update = '''        if (this.RouteComplete || this.BossGateReady || this.ChoicePending || this.ChoiceDeferred)\n            return;\n        if (!IsCombatKind(this.CurrentKind) || !this.NodeSpawned)\n            return;\n        if (CountRunEnemies(Game1.currentLocation) > 0)\n            return;\n\n        this.NodeSpawned = false;\n        this.CompleteCurrentNode(Game1.currentLocation);'''
new_update = '''        if (this.RouteComplete || this.BossGateReady || this.ChoicePending || this.ChoiceDeferred)\n            return;\n        if (!IsCombatKind(this.CurrentKind) || !this.NodeSpawned)\n        {\n            this.ClearRoomMechanicTelegraph();\n            return;\n        }\n\n        this.UpdateRoomMechanic(Game1.currentLocation);\n        if (CountRunEnemies(Game1.currentLocation) > 0)\n            return;\n\n        this.ResetRoomMechanicState();\n        this.NodeSpawned = false;\n        this.CompleteCurrentNode(Game1.currentLocation);'''
t = replace_once(t, old_update, new_update, "room mechanic update hook")

# VFX-only hazard telegraphs. No physical object art is drawn here.
button_anchor = "    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)\n"
need(button_anchor in t, "button method anchor")
render_method = r'''    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        if (!Context.IsWorldReady || !this.Active || !IsRegion2(Game1.currentLocation)
            || this.RoomMechanicResolveAtMs <= Environment.TickCount64 || this.RoomMechanicTiles.Length == 0)
            return;

        Color color = this.ActiveRoomMechanic switch
        {
            "mirror_trace" => new Color(151, 191, 232),
            "ink_sweep" => new Color(136, 82, 142),
            "warden_seal" => new Color(222, 181, 86),
            _ => new Color(210, 210, 210),
        };
        long left = Math.Max(0L, this.RoomMechanicResolveAtMs - Environment.TickCount64);
        float pulse = 0.32f + 0.22f * (1f - Math.Min(1f, left / 1100f));
        foreach (Point tile in this.RoomMechanicTiles)
            DrawHazardOutline(e.SpriteBatch, tile, color * pulse);
    }

'''
t = t.replace(button_anchor, render_method + button_anchor, 1)

# Status exposes room-specific mechanic state without adding floating world labels.
t = t.replace(
    'return $"0683 Region II Rogue: active={this.Active}, room={this.CurrentRoom}, node={this.CurrentNode}/{this.TargetNodes}, kind={this.CurrentKind}, interaction={this.AwaitingRoomInteraction}, "',
    'return $"0684 Region II Rogue: active={this.Active}, room={this.CurrentRoom}, node={this.CurrentNode}/{this.TargetNodes}, kind={this.CurrentKind}, interaction={this.AwaitingRoomInteraction}, mechanic={this.ActiveRoomMechanic}[{this.RoomMechanicCycles} cycles/{this.RoomMechanicHits} hits], "',
    1,
)
describe_end = '            + "runLength=6-9 nodes; Boss Gate eligible from node 6 when Boss I + 40 cards are satisfied.";\n    }\n'
need(describe_end in t, "Describe end anchor")
t = t.replace(
    describe_end,
    describe_end + '''

    public string DescribeRoomMechanic()
    {
        long now = Environment.TickCount64;
        long telegraphMs = this.RoomMechanicResolveAtMs > now ? this.RoomMechanicResolveAtMs - now : 0L;
        long nextMs = this.RoomMechanicNextAtMs > now ? this.RoomMechanicNextAtMs - now : 0L;
        return $"0684 RoomMechanic: active={this.Active}, room={this.CurrentRoom}, kind={this.CurrentKind}, tag={this.ActiveRoomMechanic}, "
            + $"telegraph={telegraphMs}ms, next={nextMs}ms, tiles={this.RoomMechanicTiles.Length}, cycles={this.RoomMechanicCycles}, hits={this.RoomMechanicHits}.";
    }
''',
    1,
)

# Clear mechanic state at every node boundary.
t = replace_once(
    t,
    '        this.NodeSpawned = false;\n        this.AwaitingRoomInteraction = false;\n        this.ActiveInteractionTile = Point.Zero;\n        this.ClearInteractionObject(location);',
    '        this.NodeSpawned = false;\n        this.ResetRoomMechanicState();\n        this.AwaitingRoomInteraction = false;\n        this.ActiveInteractionTile = Point.Zero;\n        this.ClearInteractionObject(location);',
    "node boundary mechanic reset",
)
t = replace_once(
    t,
    '        if (IsCombatKind(kind))\n        {\n            this.SpawnNodeEnemies(location, kind);\n            this.NodeSpawned = true;\n            Game1.showGlobalMessage',
    '        if (IsCombatKind(kind))\n        {\n            this.SpawnNodeEnemies(location, kind);\n            this.NodeSpawned = true;\n            this.ArmRoomMechanicForCombat(location);\n            Game1.showGlobalMessage',
    "normal combat mechanic arm",
)

# Cursed Archive wakes combat and then arms Inkbound pressure.
t = replace_once(
    t,
    '        if (kind == Region2NodeKind.CursedArchive)\n        {\n            Game1.playSound("wand");\n            this.SpawnNodeEnemies(location, kind);\n            this.NodeSpawned = true;\n            Game1.drawObjectDialogue',
    '        if (kind == Region2NodeKind.CursedArchive)\n        {\n            Game1.playSound("wand");\n            this.SpawnNodeEnemies(location, kind);\n            this.NodeSpawned = true;\n            this.ArmRoomMechanicForCombat(location);\n            Game1.drawObjectDialogue',
    "cursed mechanic arm",
)

# Ensure mechanic telegraph is cleared before route/bank progression.
t = replace_once(
    t,
    '    private void CompleteCurrentNode(GameLocation location)\n    {\n        if (IsCombatKind(this.CurrentKind))',
    '    private void CompleteCurrentNode(GameLocation location)\n    {\n        this.ResetRoomMechanicState();\n        if (IsCombatKind(this.CurrentKind))',
    "complete-node mechanic reset",
)

# Insert complete room-specific mechanic runtime before combat-record accounting.
insert_anchor = '    private void UpdateCombatRecord()\n'
need(insert_anchor in t, "UpdateCombatRecord anchor")
mechanic_methods = r'''    private void ArmRoomMechanicForCombat(GameLocation location)
    {
        this.ResetRoomMechanicState();
        this.ActiveRoomMechanic = this.CurrentRoom switch
        {
            Region2RoomKind.MirrorGallery => "mirror_trace",
            Region2RoomKind.InkboundStacks => "ink_sweep",
            Region2RoomKind.WardenVault when this.CurrentKind == Region2NodeKind.Elite => "warden_seal",
            _ => "none",
        };
        if (this.ActiveRoomMechanic == "none")
            return;

        this.RoomMechanicNextAtMs = Environment.TickCount64 + 2200L;
        Game1.showGlobalMessage(ModEntry.T("airship.region2.mechanic.active", new
        {
            mechanic = ModEntry.T($"airship.region2.mechanic.{this.ActiveRoomMechanic}.name")
        }));
    }

    private void UpdateRoomMechanic(GameLocation location)
    {
        if (this.ActiveRoomMechanic == "none")
            return;
        if (CountRunEnemies(location) <= 0)
        {
            this.ClearRoomMechanicTelegraph();
            return;
        }

        long now = Environment.TickCount64;
        if (this.RoomMechanicResolveAtMs > 0)
        {
            if (now < this.RoomMechanicResolveAtMs)
                return;
            this.ResolveRoomMechanicHit();
            this.ClearRoomMechanicTelegraph();
            this.RoomMechanicNextAtMs = now + RoomMechanicCooldownMs(this.ActiveRoomMechanic, this.CurrentNode);
            return;
        }

        if (now < this.RoomMechanicNextAtMs)
            return;
        if (!this.TryArmRoomMechanicTelegraph(location, now))
            this.RoomMechanicNextAtMs = now + 700L;
    }

    private bool TryArmRoomMechanicTelegraph(GameLocation location, long now)
    {
        Point player = PlayerTile();
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 40;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 28;

        switch (this.ActiveRoomMechanic)
        {
            case "mirror_trace":
                Point origin = ClampArenaTile(player, width, height);
                Point reflected = ClampArenaTile(new Point(width - 1 - origin.X, origin.Y), width, height);
                this.RoomMechanicTiles = BuildSquareZone(origin, 1, width, height)
                    .Concat(BuildSquareZone(reflected, 1, width, height))
                    .Distinct()
                    .ToArray();
                this.RoomMechanicResolveAtMs = now + MirrorTelegraphMs;
                Game1.playSound("wand");
                break;

            case "ink_sweep":
                int row = Math.Clamp(player.Y, 4, Math.Max(4, height - 5));
                this.RoomMechanicTiles = Enumerable.Range(4, Math.Max(1, width - 8))
                    .Select(x => new Point(x, row))
                    .ToArray();
                this.RoomMechanicResolveAtMs = now + InkTelegraphMs;
                Game1.playSound("batScreech");
                break;

            case "warden_seal":
                Monster? warden = location.characters.OfType<Monster>().FirstOrDefault(m =>
                    m.Health > 0
                    && m.modData.TryGetValue(RegionExpeditionService.EnemyRoleKey, out string? role)
                    && role.Equals("archive_warden", StringComparison.OrdinalIgnoreCase));
                if (warden is null)
                    return false;
                Point center = ClampArenaTile(new Point((int)(warden.Position.X / 64f), (int)(warden.Position.Y / 64f)), width, height);
                this.RoomMechanicTiles = BuildSquareZone(center, 2, width, height)
                    .Where(p => p != center)
                    .ToArray();
                this.RoomMechanicResolveAtMs = now + VaultTelegraphMs;
                Game1.playSound("discoverMineral");
                break;

            default:
                return false;
        }

        this.RoomMechanicCycles++;
        return this.RoomMechanicTiles.Length > 0;
    }

    private void ResolveRoomMechanicHit()
    {
        if (this.RoomMechanicTiles.Length == 0)
            return;
        Point player = PlayerTile();
        if (!this.RoomMechanicTiles.Contains(player))
            return;

        int damage = this.ActiveRoomMechanic switch
        {
            "mirror_trace" => 8 + this.CurrentNode / 4,
            "ink_sweep" => 7 + this.CurrentNode / 4,
            "warden_seal" => 10 + this.CurrentNode / 3,
            _ => 0,
        };
        if (damage <= 0)
            return;

        this.RoomMechanicHits++;
        // Use the native Farmer damage pipeline so Cardcha defensive/revive effects remain authoritative.
        Game1.player.takeDamage(damage, false, null);
    }

    private void ResetRoomMechanicState()
    {
        this.ActiveRoomMechanic = "none";
        this.RoomMechanicNextAtMs = 0L;
        this.RoomMechanicResolveAtMs = 0L;
        this.RoomMechanicTiles = Array.Empty<Point>();
        this.RoomMechanicCycles = 0;
        this.RoomMechanicHits = 0;
    }

    private void ClearRoomMechanicTelegraph()
    {
        this.RoomMechanicResolveAtMs = 0L;
        this.RoomMechanicTiles = Array.Empty<Point>();
    }

    private static long RoomMechanicCooldownMs(string tag, int node)
    {
        int depthCut = Math.Min(900, Math.Max(0, node - 1) * 90);
        int baseline = tag switch
        {
            "mirror_trace" => 4500,
            "ink_sweep" => 4800,
            "warden_seal" => 4200,
            _ => 5000,
        };
        return Math.Max(3000, baseline - depthCut);
    }

    private static Point ClampArenaTile(Point tile, int width, int height)
        => new(Math.Clamp(tile.X, 2, Math.Max(2, width - 3)), Math.Clamp(tile.Y, 3, Math.Max(3, height - 4)));

    private static IEnumerable<Point> BuildSquareZone(Point center, int radius, int width, int height)
    {
        for (int y = center.Y - radius; y <= center.Y + radius; y++)
        for (int x = center.X - radius; x <= center.X + radius; x++)
        {
            if (x >= 1 && x < width - 1 && y >= 2 && y < height - 2)
                yield return new Point(x, y);
        }
    }

    private static void DrawHazardOutline(SpriteBatch batch, Point tile, Color color)
    {
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, new Vector2(tile.X * 64f, tile.Y * 64f));
        Rectangle r = new((int)local.X + 7, (int)local.Y + 7, 50, 50);
        const int edge = 4;
        batch.Draw(Game1.staminaRect, new Rectangle(r.X, r.Y, r.Width, edge), color);
        batch.Draw(Game1.staminaRect, new Rectangle(r.X, r.Bottom - edge, r.Width, edge), color);
        batch.Draw(Game1.staminaRect, new Rectangle(r.X, r.Y, edge, r.Height), color);
        batch.Draw(Game1.staminaRect, new Rectangle(r.Right - edge, r.Y, edge, r.Height), color);
    }

'''
t = t.replace(insert_anchor, mechanic_methods + insert_anchor, 1)

# Reset on save/day/title/exit so no telegraph or timer survives the run.
t = replace_once(
    t,
    '        this.NodeSpawned = false;\n        this.AwaitingRoomInteraction = false;\n        this.ActiveInteractionTile = Point.Zero;\n        this.PendingInternalRoomWarp = false;',
    '        this.NodeSpawned = false;\n        this.ResetRoomMechanicState();\n        this.AwaitingRoomInteraction = false;\n        this.ActiveInteractionTile = Point.Zero;\n        this.PendingInternalRoomWarp = false;',
    "ResetRuntime mechanic cleanup",
)

p.write_text(t, encoding="utf-8")

# ModEntry: only transient hazard outlines are allowed in RenderedWorld.
mod_path = SRC / "ModEntry.cs"
mod = mod_path.read_text(encoding="utf-8")
mod = replace_once(
    mod,
    '        helper.Events.Display.RenderedWorld += this.RegionExpeditions.OnRenderedWorld;\n',
    '        helper.Events.Display.RenderedWorld += this.RegionExpeditions.OnRenderedWorld;\n        helper.Events.Display.RenderedWorld += this.Region2Rogue.OnRenderedWorld;\n',
    "Region II mechanic VFX event wiring",
)
mod = replace_once(
    mod,
    '        helper.ConsoleCommands.Add("cardcha_region2_rogue_status", "Show Region II 6-9 node route, risk/reward and Curator observation state.", (_, _) => this.Monitor.Log(this.Region2Rogue.Describe(), LogLevel.Alert));\n',
    '        helper.ConsoleCommands.Add("cardcha_region2_rogue_status", "Show Region II 6-9 node route, risk/reward and Curator observation state.", (_, _) => this.Monitor.Log(this.Region2Rogue.Describe(), LogLevel.Alert));\n        helper.ConsoleCommands.Add("cardcha_region2_mechanic_status", "Show active Region II room-specific combat mechanic and telegraph state.", (_, _) => this.Monitor.Log(this.Region2Rogue.DescribeRoomMechanic(), LogLevel.Alert));\n',
    "room mechanic debug command",
)
mod = mod.replace("0683 REGION II ROOM INTERACTION TEST", "0684 REGION II ROOM-SPECIFIC MECHANICS TEST")
mod_path.write_text(mod, encoding="utf-8")

# EN/VI mechanic names. Keep world text minimal: one intro message per combat node, no floating labels.
for lang, values in {
    "default.json": {
        "airship.region2.mechanic.active": "The Archive shifts: {{mechanic}}.",
        "airship.region2.mechanic.mirror_trace.name": "Reflected Trace",
        "airship.region2.mechanic.ink_sweep.name": "Ink Sweep",
        "airship.region2.mechanic.warden_seal.name": "Warden Seal",
    },
    "vi.json": {
        "airship.region2.mechanic.active": "Kho Lưu Trữ chuyển động: {{mechanic}}.",
        "airship.region2.mechanic.mirror_trace.name": "Dấu Gương Phản Chiếu",
        "airship.region2.mechanic.ink_sweep.name": "Quét Mực",
        "airship.region2.mechanic.warden_seal.name": "Ấn Giám Ngục",
    },
}.items():
    ip = SRC / "i18n" / lang
    data = json.loads(ip.read_text(encoding="utf-8"))
    data.update(values)
    ip.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Machine-readable render-depth audit: this new subscriber is VFX-only by contract.
audit_path = ROOT / "render_depth_audit.json"
audit = json.loads(audit_path.read_text(encoding="utf-8"))
audit["branch"] = "cardcha-alpha28-0684-region2-room-specific-mechanics"
audit.setdefault("renderedWorldSubscribers", {})["Region2Rogue"] = {
    "classification": "0684-vfx-only-room-hazard-telegraphs",
    "physicalAllowed": False,
}
audit_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")

# Keep design reasoning current instead of leaving the old 0679 source-of-truth sentence stale.
design_path = ROOT / "handoff" / "REGION2_ROGUELIKE_DESIGN_DIRECTION.md"
design = design_path.read_text(encoding="utf-8")
design = design.replace(
    "0679 remains the current technical source-of-truth build and provides:",
    "0679 is the historical Region II ownership foundation. The current technical line has since evolved through 0680–0684 and preserves:",
)
note = '''\n\n### 0684 implementation note\n\nRoom identity must change tactics, not only scenery. Mirror Gallery uses a reflected-position strike, Inkbound Stacks uses a readable horizontal ink sweep, and Warden Vault Elite nodes use a seal pulse centered on the Archive Warden. Archive Vestibule intentionally remains a lower-pressure entry/breathing room. These are transient combat VFX/mechanics, never physical `RenderedWorld` props, and should be tuned by playtest rather than treated as permanent numeric law.\n'''
if "### 0684 implementation note" not in design:
    design += note
design_path.write_text(design, encoding="utf-8")

handoff = f'''# Alpha.28 0684 Region II Room-Specific Mechanics\n\nBranch: `cardcha-alpha28-0684-region2-room-specific-mechanics`\nBuild: `{NEW}`\nBase: 0683 Region II Room Interactions\n\n## Purpose\n\n0684 makes the four Forgotten Archive room identities change how combat is played instead of changing only geometry/art. The 6–9 node route, physical room interactions, Curator Records You, progression and rewards remain intact.\n\n## Room mechanics\n\n- **Archive Vestibule:** intentionally no extra repeating room hazard. It remains the lower-pressure entry/breathing space.\n- **Mirror Gallery / Reflected Trace:** periodically records the Farmer tile and its horizontal mirror position, telegraphs both 3x3 zones, then resolves damage through native `Farmer.takeDamage`.\n- **Inkbound Stacks / Ink Sweep:** periodically telegraphs a horizontal row through the current player Y position; stepping off the row avoids it. This applies to Ambush/Cursed combat after the cursed tome is actually activated.\n- **Warden Vault / Warden Seal:** Elite nodes pulse a telegraphed radius around the living Archive Warden. Killing/repositioning around the elite changes the pressure.\n\n## Rendering-depth contract\n\n`Region2Rogue.OnRenderedWorld` is newly wired **only for transient thin hazard outlines**. It draws no Chest, furniture, tree, rock, gate, station, boss body or other physical object. `render_depth_audit.json` marks the subscriber as `physicalAllowed=false`. Physical 0683 stations remain TMX/native objects.\n\n## Frozen contracts\n\n- Region II run target: 6–9 nodes.\n- Checkpoints: 3 and 6.\n- Region II fare: 250g.\n- Boss II: Hollow Curator, 2200 HP, 40-card milestone.\n- Curator Records You remains active.\n- Save schema stays 19.\n- Card audit stays 80 source / 76 active normal.\n- Region III/IV, Boss III/IV, Airship accepted assets and `mimi_walk.png` are untouched.\n\n## Debug\n\n- `cardcha_test_region2`\n- `cardcha_expedition_clear`\n- `cardcha_region2_rogue_status`\n- `cardcha_region2_mechanic_status`\n- `cardcha_test_region2_bossgate`\n\n## Acceptance\n\nCI proves static/compile/package contracts only. In-game acceptance is pending. Test especially whether telegraphs are readable without becoming visual clutter, whether Ink Sweep can be dodged comfortably, and whether Warden Seal feels like elite pressure rather than unavoidable chip damage.\n'''
(ROOT / "handoff" / "ALPHA28_0684_REGION2_ROOM_SPECIFIC_MECHANICS.md").write_text(handoff, encoding="utf-8")
latest = f'''# Latest Cardcha Handoff\n\nCurrent branch: `cardcha-alpha28-0684-region2-room-specific-mechanics`\nCurrent build: `{NEW}`\nContinue from: `handoff/ALPHA28_0684_REGION2_ROOM_SPECIFIC_MECHANICS.md`\nDesign direction: `handoff/REGION2_ROGUELIKE_DESIGN_DIRECTION.md`\n\n0684 preserves the 6–9 node multi-room run, 0683 physical room interactions and Curator Records You, while Mirror Gallery, Inkbound Stacks and Warden Vault now have distinct combat mechanics. In-game acceptance is pending.\n'''
(ROOT / "handoff" / "LATEST_CARDCHA_HANDOFF.md").write_text(latest, encoding="utf-8")

print("0684 generator complete: room-specific combat mechanics + VFX-only depth audit + docs.")
