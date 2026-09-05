from pathlib import Path
p=Path('src/Cardcha/Services/AirshipInteriorStardewRenderer.cs')
s=p.read_text()
old='''            Vector2 center = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 34f);
            Rectangle src = new(column * CellSize, level * CellSize, CellSize, CellSize);
            Rectangle shadow = new((int)center.X - 55, (int)center.Y + 30, 110, 13);
            DrawRect(batch, shadow, new Color(34, 25, 25) * 0.34f);

            Rectangle dst = new((int)center.X - 56, (int)center.Y - 76, 112, 112);
            batch.Draw(atlas, dst, src, Color.White);

            float pulse = 0.40f + 0.12f * MathF.Sin(phase * 1.7f + column * 1.2f);
            DrawRect(batch, new Rectangle((int)center.X - 15, (int)center.Y + 28, 30, 3), new Color(199, 148, 78) * 0.48f);
            if (level > 0)
                DrawRect(batch, new Rectangle((int)center.X - 9, (int)center.Y + 24, 18, 2), accent * pulse);
            if (level >= 3)
            {
                DrawRect(batch, new Rectangle((int)center.X - 2, (int)center.Y - 54, 4, 6), accent * (pulse + 0.08f));
                DrawRect(batch, new Rectangle((int)center.X - 12, (int)center.Y - 45, 3, 3), accent * pulse);
                DrawRect(batch, new Rectangle((int)center.X + 9, (int)center.Y - 40, 3, 3), accent * pulse);
            }
'''
new='''            Vector2 center = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 34f);
            Rectangle src = new(column * CellSize, level * CellSize, CellSize, CellSize);
            Rectangle shadow = new((int)center.X - 56, (int)center.Y + 31, 112, 15);
            DrawRect(batch, shadow, new Color(28, 21, 28) * 0.42f);

            Rectangle dst = new((int)center.X - 56, (int)center.Y - 76, 112, 112);
            batch.Draw(atlas, dst, src, Color.White);

            if (level > 0)
            {
                float pulse = 0.55f + 0.20f * MathF.Sin(phase * 2.0f + column * 1.3f);
                DrawRect(batch, new Rectangle((int)center.X - 16, (int)center.Y + 28, 32, 3), accent * pulse);
                if (level >= 3)
                {
                    DrawRect(batch, new Rectangle((int)center.X - 2, (int)center.Y - 54, 4, 7), accent * (pulse + 0.12f));
                    DrawRect(batch, new Rectangle((int)center.X - 13, (int)center.Y - 46, 3, 3), accent * pulse);
                    DrawRect(batch, new Rectangle((int)center.X + 10, (int)center.Y - 40, 3, 3), accent * pulse);
                }
            }
'''
if old not in s:
    raise SystemExit('0648 renderer station block not found')
s=s.replace(old,new,1)
p.write_text(s)
print('0648 renderer normalized for 0648A generator')
