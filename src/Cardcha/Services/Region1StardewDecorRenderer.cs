using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// 0669 foundation pass: room-specific organic edge clusters using an authored 8-cell forest atlas.
/// It intentionally avoids repeating the same staircase/grid silhouette in every Hunt Run room.
/// </summary>
internal static class Region1StardewDecorRenderer
{
    private const string AtlasPath = "assets/region1_environment_decor.png";
    private const int CellSize = 32;
    private const int CellCount = 8;
    private static Texture2D? Atlas;
    private static bool LoadFailed;

    public static void Draw(SpriteBatch batch, GameLocation room, int roomIndex)
    {
        Texture2D? atlas = GetAtlas();
        if (atlas is null) return;

        int width = room.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 28;
        int height = room.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 20;

        Point[] points = roomIndex switch
        {
            0 => new[] { new Point(3,4), new Point(7,3), new Point(width-5,5), new Point(5,height-4), new Point(width-8,height-3), new Point(width-3,height-6) },
            1 => new[] { new Point(2,5), new Point(6,3), new Point(width-4,4), new Point(width-7,7), new Point(4,height-5), new Point(width-5,height-4) },
            2 => new[] { new Point(4,3), new Point(9,4), new Point(width-6,3), new Point(width-3,8), new Point(3,height-4), new Point(width-9,height-3) },
            3 => new[] { new Point(3,6), new Point(6,3), new Point(10,5), new Point(width-4,5), new Point(width-7,height-4), new Point(5,height-3) },
            4 => new[] { new Point(2,4), new Point(8,3), new Point(width-5,3), new Point(width-3,7), new Point(6,height-4), new Point(width-8,height-3) },
            _ => new[] { new Point(4,4), new Point(8,3), new Point(width-6,4), new Point(3,height-5), new Point(width-4,height-5), new Point(width-9,height-3) },
        };

        for (int i = 0; i < points.Length; i++)
        {
            Point tile = points[i];
            int sprite = Math.Abs(roomIndex * 5 + i * 3) % CellCount;
            Rectangle src = new(sprite * CellSize, 0, CellSize, CellSize);
            Vector2 world = new(tile.X * 64f + 32f, tile.Y * 64f + 58f);
            Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
            float scale = 1.72f + (sprite % 3) * 0.14f;
            float layer = Math.Clamp((world.Y + 18f) / 10000f, 0.01f, 0.88f);
            batch.Draw(atlas, local, src, Color.White, 0f, new Vector2(16f,31f), scale, SpriteEffects.None, layer);
        }
    }

    private static Texture2D? GetAtlas()
    {
        if (Atlas is not null && !Atlas.IsDisposed) return Atlas;
        Atlas = null;
        if (LoadFailed || ModEntry.StaticHelper is null) return null;
        try
        {
            Atlas = ModEntry.StaticHelper.ModContent.Load<Texture2D>(AtlasPath);
            return Atlas;
        }
        catch
        {
            LoadFailed = true;
            return null;
        }
    }
}
