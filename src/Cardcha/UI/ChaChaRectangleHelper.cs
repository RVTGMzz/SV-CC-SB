global using static Cardcha.UI.ChaChaRectangleHelper;

using Microsoft.Xna.Framework;

namespace Cardcha.UI;

/// <summary>Small layout helper shared by ChaCha UI surfaces.</summary>
internal static class ChaChaRectangleHelper
{
    internal static Rectangle Inflate(Rectangle rect, int amount)
        => new(
            rect.X - amount,
            rect.Y - amount,
            Math.Max(1, rect.Width + amount * 2),
            Math.Max(1, rect.Height + amount * 2)
        );
}
