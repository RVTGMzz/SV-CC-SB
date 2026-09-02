from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha"
VERSION_OLD = "0.3.0-alpha.28.0.4.14.4.5"
VERSION_NEW = "0.3.0-alpha.28.0.4.14.4.5.1"


def must_replace(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"Missing patch anchor: {label}")
    return text.replace(old, new, 1)


def update_version(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if VERSION_OLD not in text:
        raise SystemExit(f"Old version not found in {path}")
    path.write_text(text.replace(VERSION_OLD, VERSION_NEW), encoding="utf-8")


# Version bump only. Cardcha Binder/UI code is intentionally untouched by this hotfix.
for rel in ["Cardcha.csproj", "Directory.Build.targets", "manifest.json", "ModEntry.cs"]:
    update_version(SRC / rel)

path = SRC / "Services" / "AirshipFoundationService.cs"
text = path.read_text(encoding="utf-8")

text = must_replace(
    text,
    "    private const float BoardingUseDistance = 128f;\n",
    "    private const float BoardingUseDistance = 128f;\n    private const float ForestGateUseDistance = 320f;\n",
    "forest gate action radius",
)

text = must_replace(
    text,
    "            if (!PlayerIsNear(dock))\n                return;\n",
    "            // The Forest gate never edits collision. A wider action-only radius lets the player\n"
    "            // activate it from the reachable side of fences/foliage on modded Forest maps.\n"
    "            if (!PlayerIsNear(dock, ForestGateUseDistance))\n                return;\n",
    "forest gate interaction",
)

text = must_replace(
    text,
    "                Vector2 tile = new(p.X, p.Y);\n                if (location.IsTileBlockedBy(tile)\n",
    "                Vector2 tile = new(p.X, p.Y);\n                // Static map-overhaul fences, trunks, and canopy pieces can live on map layers\n"
    "                // without being represented as terrain features. Reject those anchors too.\n"
    "                var buildings = location.Map?.GetLayer(\"Buildings\");\n"
    "                var front = location.Map?.GetLayer(\"Front\");\n"
    "                if (buildings?.Tiles[p.X, p.Y] is not null || front?.Tiles[p.X, p.Y] is not null)\n"
    "                    return false;\n\n"
    "                if (location.IsTileBlockedBy(tile)\n",
    "static Forest layers in dock safety",
)

old_player_near = """    private static bool PlayerIsNear(Point tile)\n    {\n        Vector2 center = new(tile.X * 64f + 32f, tile.Y * 64f + 32f);\n        Vector2 player = Game1.player.Position + new Vector2(32f, 32f);\n        return Vector2.DistanceSquared(center, player) <= BoardingUseDistance * BoardingUseDistance;\n    }\n"""
new_player_near = """    private static bool PlayerIsNear(Point tile)\n        => PlayerIsNear(tile, BoardingUseDistance);\n\n    private static bool PlayerIsNear(Point tile, float useDistance)\n    {\n        Vector2 center = new(tile.X * 64f + 32f, tile.Y * 64f + 32f);\n        Vector2 player = Game1.player.Position + new Vector2(32f, 32f);\n        return Vector2.DistanceSquared(center, player) <= useDistance * useDistance;\n    }\n"""
text = must_replace(text, old_player_near, new_player_near, "PlayerIsNear overload")

old_portal_clouds = """            DrawRect(batch, new Rectangle(x, y, 96, 11), color * 0.56f);\n            DrawRect(batch, new Rectangle(x + 22, y - 9, 62, 13), color * 0.72f);\n            DrawRect(batch, new Rectangle(x + 48, y + 7, 82, 9), color * 0.44f);\n"""
new_portal_clouds = """            DrawClippedRect(batch, bounds, new Rectangle(x, y, 96, 11), color * 0.56f);\n            DrawClippedRect(batch, bounds, new Rectangle(x + 22, y - 9, 62, 13), color * 0.72f);\n            DrawClippedRect(batch, bounds, new Rectangle(x + 48, y + 7, 82, 9), color * 0.44f);\n"""
text = must_replace(text, old_portal_clouds, new_portal_clouds, "portal cloud clipping")

old_cloud_band = """            DrawRect(batch, new Rectangle(x, y, 118, 13), color * 0.72f);\n            DrawRect(batch, new Rectangle(x + 24, y - 11, 72, 15), color * 0.82f);\n            DrawRect(batch, new Rectangle(x + 57, y + 8, 96, 10), color * 0.58f);\n"""
new_cloud_band = """            DrawClippedRect(batch, bounds, new Rectangle(x, y, 118, 13), color * 0.72f);\n            DrawClippedRect(batch, bounds, new Rectangle(x + 24, y - 11, 72, 15), color * 0.82f);\n            DrawClippedRect(batch, bounds, new Rectangle(x + 57, y + 8, 96, 10), color * 0.58f);\n"""
text = must_replace(text, old_cloud_band, new_cloud_band, "bridge cloud clipping")

old_draw_rect = """    private static void DrawRect(SpriteBatch batch, Rectangle rectangle, Color color)\n    {\n        if (rectangle.Width <= 0 || rectangle.Height <= 0)\n            return;\n        batch.Draw(Game1.staminaRect, rectangle, color);\n    }\n"""
new_draw_rect = """    private static void DrawRect(SpriteBatch batch, Rectangle rectangle, Color color)\n    {\n        if (rectangle.Width <= 0 || rectangle.Height <= 0)\n            return;\n        batch.Draw(Game1.staminaRect, rectangle, color);\n    }\n\n    private static void DrawClippedRect(SpriteBatch batch, Rectangle bounds, Rectangle rectangle, Color color)\n    {\n        Rectangle clipped = Rectangle.Intersect(bounds, rectangle);\n        if (clipped.Width <= 0 || clipped.Height <= 0)\n            return;\n        DrawRect(batch, clipped, color);\n    }\n"""
text = must_replace(text, old_draw_rect, new_draw_rect, "clipped rectangle helper")

path.write_text(text, encoding="utf-8")
print("alpha28.0.4.14.4.5.1 gate visual hotfix applied")
