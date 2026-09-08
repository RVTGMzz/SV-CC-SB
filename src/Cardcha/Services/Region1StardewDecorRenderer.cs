using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewValley;

namespace Cardcha.Services;

internal static class Region1StardewDecorRenderer
{
    private const string AtlasPath = "assets/region1_environment_decor.png";
    private static Texture2D? Atlas;
    private static bool LoadFailed;
    public static void Draw(SpriteBatch batch, GameLocation room, int roomIndex)
    {
        Texture2D? atlas = GetAtlas(); if (atlas is null) return; int width = room.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 28; int height = room.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 20;
        Point[] points = { new(3,4), new(width-4,4), new(4,height-5), new(width-5,height-5), new(7,3), new(width-8,3), new(6,height-3), new(width-7,height-3) };
        for (int i=0;i<points.Length;i++) { Point t=points[i]; int sprite=(roomIndex*3+i)%4; Rectangle src=new(sprite*32,0,32,32); Vector2 world=new(t.X*64f+32f,t.Y*64f+58f); Vector2 local=Game1.GlobalToLocal(Game1.viewport,world); float scale=sprite==2?1.35f:1.65f; batch.Draw(atlas,local,src,Color.White,0f,new Vector2(16f,31f),scale,SpriteEffects.None,0.035f); }
    }
    private static Texture2D? GetAtlas() { if (Atlas is not null && !Atlas.IsDisposed) return Atlas; Atlas=null; if (LoadFailed || ModEntry.StaticHelper is null) return null; try { Atlas=ModEntry.StaticHelper.ModContent.Load<Texture2D>(AtlasPath); return Atlas; } catch { LoadFailed=true; return null; } }
}
