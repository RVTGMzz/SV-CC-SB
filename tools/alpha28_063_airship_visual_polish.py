#!/usr/bin/env python3
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "Cardcha"
AIRSHIP = SRC / "Services" / "AirshipFoundationService.cs"
VERSION = "0.3.0-alpha.28.0.4.14.4.5"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.4"

DRAW_SKY_DOCK = r'''    private void DrawSkyDock(SpriteBatch batch, Point tile)
    {
        Vector2 center = Game1.GlobalToLocal(
            Game1.viewport,
            new Vector2(tile.X * 64f + 32f, tile.Y * 64f + 30f)
        );

        float phase = (float)(Environment.TickCount64 / 920.0);
        float pulse = 0.62f + 0.16f * (float)Math.Sin(Environment.TickCount64 / 260.0);
        Color violet = new Color(176, 105, 255) * pulse;
        Color cyan = new Color(87, 222, 246) * (pulse * 0.94f);
        Color gold = new Color(224, 171, 82) * 0.96f;
        Color stoneDark = new Color(47, 43, 56) * 0.98f;
        Color stone = new Color(82, 76, 91) * 0.98f;
        Color stoneLight = new Color(118, 108, 119) * 0.88f;

        // Ground shadow and three-step dais. Presentation only, never Forest collision.
        DrawRect(batch, new Rectangle((int)center.X - 104, (int)center.Y + 63, 208, 18), new Color(20, 20, 27) * 0.50f);
        DrawRect(batch, new Rectangle((int)center.X - 92, (int)center.Y + 49, 184, 18), stoneDark * 0.84f);
        DrawRect(batch, new Rectangle((int)center.X - 82, (int)center.Y + 40, 164, 13), stone * 0.86f);
        DrawRect(batch, new Rectangle((int)center.X - 70, (int)center.Y + 32, 140, 10), stoneLight * 0.72f);
        DrawRect(batch, new Rectangle((int)center.X - 76, (int)center.Y + 41, 152, 3), gold * 0.58f);

        // Deep portal vista: violet edge, cyan depth, then moving sky/cloud parallax.
        Rectangle aperture = new((int)center.X - 57, (int)center.Y - 105, 114, 143);
        DrawRect(batch, new Rectangle(aperture.X - 7, aperture.Y - 7, aperture.Width + 14, aperture.Height + 14), new Color(48, 27, 72) * 0.94f);
        DrawVerticalGradient(batch, aperture,
            new Color(84, 72, 171) * 0.92f,
            new Color(85, 159, 218) * 0.90f,
            new Color(226, 175, 197) * 0.78f);
        DrawPortalClouds(batch, aperture, phase, Color.White * 0.48f);
        DrawRect(batch, new Rectangle(aperture.X + 9, aperture.Y + 8, aperture.Width - 18, aperture.Height - 16), violet * 0.18f);
        DrawRect(batch, new Rectangle(aperture.X + 18, aperture.Y + 15, aperture.Width - 36, aperture.Height - 30), cyan * 0.10f);

        // Heavy stone arch with brass inlay.
        DrawRect(batch, new Rectangle((int)center.X - 81, (int)center.Y - 77, 24, 127), stoneDark);
        DrawRect(batch, new Rectangle((int)center.X + 57, (int)center.Y - 77, 24, 127), stoneDark);
        DrawRect(batch, new Rectangle((int)center.X - 74, (int)center.Y - 73, 14, 119), stone);
        DrawRect(batch, new Rectangle((int)center.X + 60, (int)center.Y - 73, 14, 119), stone);
        DrawEllipticArc(batch, new Vector2(center.X, center.Y - 74f), 69f, 65f, MathHelper.Pi, MathHelper.TwoPi, 18, 17f, stoneDark);
        DrawEllipticArc(batch, new Vector2(center.X, center.Y - 74f), 61f, 58f, MathHelper.Pi, MathHelper.TwoPi, 18, 9f, stone);
        DrawEllipticArc(batch, new Vector2(center.X, center.Y - 74f), 53f, 51f, MathHelper.Pi, MathHelper.TwoPi, 18, 4f, gold * 0.82f);
        DrawRect(batch, new Rectangle((int)center.X - 72, (int)center.Y + 43, 144, 6), gold * 0.72f);

        DrawArcaneSigil(batch, new Vector2(center.X, center.Y - 25f), 56f, violet * 0.78f, phase);
        DrawArcaneSigil(batch, new Vector2(center.X, center.Y - 25f), 42f, cyan * 0.70f, -phase * 0.74f);
        DrawArcaneSparkles(batch, new Vector2(center.X, center.Y - 24f), 73f, 14, phase, Color.White * 0.62f);

        DrawDiamondRune(batch, new Vector2(center.X, center.Y - 147f), 18f, gold);
        DrawCrystalPylon(batch, new Vector2(center.X - 104f, center.Y + 48f), 58f, cyan, gold);
        DrawCrystalPylon(batch, new Vector2(center.X + 104f, center.Y + 48f), 58f, violet, gold);
        DrawBrassLamp(batch, new Vector2(center.X - 137f, center.Y + 55f), phase, gold, cyan);
        DrawBrassLamp(batch, new Vector2(center.X + 137f, center.Y + 55f), -phase, gold, violet);

        DrawArcaneSigil(batch, new Vector2(center.X, center.Y + 59f), 47f, violet * 0.55f, phase * 0.44f);
        DrawDiamondRune(batch, new Vector2(center.X, center.Y + 59f), 12f, cyan * 0.74f);
    }'''

DRAW_SKY_DOCK_INTERIOR = r'''    private void DrawSkyDockInteriorDetails(SpriteBatch batch, GameLocation interior)
    {
        Point route = ResolveSkyDockInteriorRouteTile(interior);
        Point exit = ResolveSkyDockInteriorExitTile(interior);
        Point bay = ResolveSkyDockInteriorBayTile(interior);
        Point arrival = ResolveSkyDockInteriorArrivalTile(interior);

        float phase = (float)(Environment.TickCount64 / 980.0);
        float pulse = 0.58f + 0.16f * (float)Math.Sin(Environment.TickCount64 / 275.0);
        Color violet = new Color(180, 108, 255) * pulse;
        Color cyan = new Color(86, 221, 244) * (pulse * 0.96f);
        Color gold = new Color(226, 171, 81) * 0.94f;
        Color woodDark = new Color(66, 43, 35) * 0.96f;
        Color wood = new Color(108, 67, 46) * 0.94f;
        Color brass = new Color(158, 100, 54) * 0.94f;
        Color frame = new Color(42, 35, 49) * 0.98f;

        Vector2 arrivalCenter = Game1.GlobalToLocal(Game1.viewport, new Vector2(arrival.X * 64f + 32f, arrival.Y * 64f + 40f));
        Vector2 routeCenter = Game1.GlobalToLocal(Game1.viewport, new Vector2(route.X * 64f + 32f, route.Y * 64f + 36f));
        Vector2 bayCenter = Game1.GlobalToLocal(Game1.viewport, new Vector2(bay.X * 64f + 32f, bay.Y * 64f + 36f));

        // Open-sky mooring aperture, with the real locked Airship outside the room.
        Vector2 skyOrigin = Game1.GlobalToLocal(Game1.viewport, new Vector2((bay.X - 5) * 64f, (bay.Y - 5) * 64f));
        Rectangle sky = new((int)skyOrigin.X, (int)skyOrigin.Y, 8 * 64, 6 * 64);
        DrawVerticalGradient(batch, sky,
            new Color(71, 133, 199) * 0.93f,
            new Color(113, 178, 220) * 0.92f,
            new Color(231, 188, 205) * 0.78f);
        DrawPortalClouds(batch, sky, phase * 0.72f, Color.White * 0.56f);

        Vector2 dockedShip = new(sky.X + sky.Width * 0.66f, sky.Y + sky.Height * 0.46f);
        float shipBob = (float)Math.Sin(Environment.TickCount64 / 520.0) * 3.5f;
        if (this.TryDrawAirshipSprite(batch, dockedShip + new Vector2(0f, shipBob), 520f, Color.White * 0.88f, SpriteEffects.None, 0.006f, 1f))
        {
            this.DrawAirshipPropellerMotion(batch, dockedShip + new Vector2(0f, shipBob), 520f, SpriteEffects.None, 0.006f, 1f, spinDirection: 0.32f);
        }

        DrawRect(batch, new Rectangle(sky.X - 13, sky.Y - 13, sky.Width + 26, 16), frame);
        DrawRect(batch, new Rectangle(sky.X - 13, sky.Bottom - 2, sky.Width + 26, 16), frame);
        DrawRect(batch, new Rectangle(sky.X - 13, sky.Y, 16, sky.Height), frame);
        DrawRect(batch, new Rectangle(sky.Right - 2, sky.Y, 16, sky.Height), frame);
        for (int i = 1; i < 4; i++)
        {
            int x = sky.X + i * sky.Width / 4;
            DrawRect(batch, new Rectangle(x - 4, sky.Y, 8, sky.Height), brass * 0.70f);
        }
        DrawEllipticArc(batch, new Vector2(sky.Center.X, sky.Y + 22f), sky.Width * 0.50f, 90f, MathHelper.Pi, MathHelper.TwoPi, 22, 9f, brass * 0.82f);

        // Boarding deck projects toward the moored ship. Low-alpha planks preserve farmer readability.
        Vector2 bridgeStart = Game1.GlobalToLocal(Game1.viewport, new Vector2((arrival.X + 1) * 64f, (bay.Y + 1) * 64f));
        Rectangle deckRect = new(
            (int)Math.Min(bridgeStart.X, bayCenter.X - 90f),
            (int)bayCenter.Y + 34,
            Math.Max(180, (int)Math.Abs(bayCenter.X - bridgeStart.X) + 170),
            118
        );
        DrawRect(batch, deckRect, woodDark * 0.42f);
        for (int y = deckRect.Y + 10; y < deckRect.Bottom; y += 24)
            DrawRect(batch, new Rectangle(deckRect.X + 8, y, deckRect.Width - 16, 4), wood * 0.36f);
        DrawRect(batch, new Rectangle(deckRect.X + 10, deckRect.Y + 8, deckRect.Width - 20, 4), gold * 0.44f);
        DrawRect(batch, new Rectangle(deckRect.X + 10, deckRect.Bottom - 14, deckRect.Width - 20, 4), gold * 0.38f);
        DrawRailing(batch, new Vector2(deckRect.X + 16f, deckRect.Y + 12f), new Vector2(deckRect.Right - 16f, deckRect.Y + 12f), brass, cyan * 0.42f);

        DrawManaLane(batch, arrivalCenter, routeCenter, violet * 0.40f, phase);
        DrawManaLane(batch, arrivalCenter, bayCenter, cyan * 0.46f, -phase * 0.82f);
        DrawArcaneSigil(batch, arrivalCenter, 72f, violet, phase);
        DrawArcaneSigil(batch, arrivalCenter, 48f, cyan, -phase * 0.67f);
        DrawDiamondRune(batch, arrivalCenter, 18f, gold * 0.78f);

        // Brass navigator console.
        Vector2 board = Game1.GlobalToLocal(Game1.viewport, new Vector2((route.X - 1) * 64f, (route.Y - 2) * 64f));
        DrawRect(batch, new Rectangle((int)board.X - 12, (int)board.Y + 14, 180, 88), new Color(24, 21, 31) * 0.66f);
        DrawRect(batch, new Rectangle((int)board.X, (int)board.Y, 156, 84), woodDark);
        DrawRect(batch, new Rectangle((int)board.X + 9, (int)board.Y + 9, 138, 60), wood);
        DrawRect(batch, new Rectangle((int)board.X + 18, (int)board.Y + 16, 120, 5), gold * 0.72f);
        DrawArcaneSigil(batch, new Vector2(board.X + 78f, board.Y + 43f), 27f, violet * 0.72f, -phase * 1.1f);
        DrawDiamondRune(batch, new Vector2(board.X + 78f, board.Y + 43f), 11f, cyan * 0.82f);
        DrawRect(batch, new Rectangle((int)board.X + 22, (int)board.Y + 74, 10, 38), brass);
        DrawRect(batch, new Rectangle((int)board.X + 124, (int)board.Y + 74, 10, 38), brass);
        DrawBrassLamp(batch, new Vector2(board.X - 26f, board.Y + 78f), phase, gold, violet);

        // Physical boarding arch in front of the ship instead of a second portal chamber.
        Vector2 gate = Game1.GlobalToLocal(Game1.viewport, new Vector2((bay.X - 1) * 64f, (bay.Y - 2) * 64f));
        Vector2 gateCenter = new(gate.X + 64f, gate.Y + 86f);
        DrawRect(batch, new Rectangle((int)gate.X - 12, (int)gate.Y + 17, 22, 142), frame);
        DrawRect(batch, new Rectangle((int)gate.X + 118, (int)gate.Y + 17, 22, 142), frame);
        DrawEllipticArc(batch, new Vector2(gateCenter.X, gate.Y + 24f), 66f, 62f, MathHelper.Pi, MathHelper.TwoPi, 18, 15f, frame);
        DrawEllipticArc(batch, new Vector2(gateCenter.X, gate.Y + 24f), 57f, 54f, MathHelper.Pi, MathHelper.TwoPi, 18, 5f, gold * 0.78f);
        DrawRect(batch, new Rectangle((int)gate.X + 10, (int)gate.Y + 146, 108, 8), brass * 0.90f);
        DrawArcaneSigil(batch, new Vector2(gateCenter.X, gate.Y + 112f), 30f, cyan * 0.58f, phase * 0.70f);
        DrawCrystalPylon(batch, new Vector2(gate.X - 6f, gate.Y + 161f), 43f, cyan, gold);
        DrawCrystalPylon(batch, new Vector2(gate.X + 134f, gate.Y + 161f), 43f, violet, gold);

        Vector2 exitCenter = Game1.GlobalToLocal(Game1.viewport, new Vector2(exit.X * 64f + 32f, exit.Y * 64f + 38f));
        DrawArcaneSigil(batch, exitCenter, 27f, cyan * 0.48f, -phase * 0.4f);
        DrawWorldMarker(batch, route, gold * 0.68f);
        DrawWorldMarker(batch, bay, violet * 0.76f);
        DrawWorldMarker(batch, exit, cyan * 0.60f);
    }'''

DRAW_DECK = r'''    private void DrawDeckMarkers(SpriteBatch batch, GameLocation deck)
    {
        Point helm = ResolveDeckHelmTile(deck);
        Point exit = ResolveDeckExitTile(deck);
        int width = deck.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 24;
        float phase = (float)(Environment.TickCount64 / 1020.0);
        float pulse = 0.58f + 0.15f * (float)Math.Sin(Environment.TickCount64 / 270.0);
        Color violet = new Color(181, 108, 255) * pulse;
        Color cyan = new Color(87, 220, 244) * (pulse * 0.96f);
        Color gold = new Color(226, 171, 81) * 0.94f;
        Color brass = new Color(151, 93, 50) * 0.96f;
        Color woodDark = new Color(61, 39, 34) * 0.96f;
        Color wood = new Color(101, 62, 45) * 0.94f;
        Color frame = new Color(40, 33, 45) * 0.99f;
        bool night = Game1.timeOfDay >= 1800 || Game1.timeOfDay < 600;

        // Grand panoramic forward canopy.
        Vector2 window = Game1.GlobalToLocal(Game1.viewport, new Vector2(2f * 64f, 0.65f * 64f));
        int windowTiles = Math.Max(12, width - 4);
        Rectangle windowRect = new((int)window.X, (int)window.Y, windowTiles * 64, 5 * 64);
        Color skyTop = night ? new Color(23, 34, 73) : new Color(74, 137, 201);
        Color skyMid = night ? new Color(45, 49, 95) : new Color(114, 178, 220);
        Color skyLow = night ? new Color(76, 59, 108) : new Color(236, 188, 201);
        DrawVerticalGradient(batch, windowRect, skyTop * 0.98f, skyMid * 0.97f, skyLow * 0.90f);

        if (night)
            DrawStarfield(batch, windowRect, 46, phase, new Color(244, 235, 202) * 0.78f);
        else
        {
            DrawCloudBand(batch, windowRect, 46, phase * 22f, Color.White * 0.64f);
            DrawCloudBand(batch, windowRect, 132, -phase * 15f, Color.White * 0.46f);
            DrawFloatingIslands(batch, windowRect, phase);
        }

        // Curved ship-frame architecture around the panoramic glass.
        DrawRect(batch, new Rectangle(windowRect.X - 18, windowRect.Y - 18, windowRect.Width + 36, 20), frame);
        DrawRect(batch, new Rectangle(windowRect.X - 18, windowRect.Bottom - 6, windowRect.Width + 36, 21), frame);
        DrawRect(batch, new Rectangle(windowRect.X - 18, windowRect.Y, 20, windowRect.Height), frame);
        DrawRect(batch, new Rectangle(windowRect.Right - 2, windowRect.Y, 20, windowRect.Height), frame);
        DrawEllipticArc(batch, new Vector2(windowRect.Center.X, windowRect.Y + 34f), windowRect.Width * 0.50f, 108f, MathHelper.Pi, MathHelper.TwoPi, 30, 13f, frame);
        DrawEllipticArc(batch, new Vector2(windowRect.Center.X, windowRect.Y + 34f), windowRect.Width * 0.48f, 100f, MathHelper.Pi, MathHelper.TwoPi, 30, 5f, brass * 0.84f);

        for (int i = 1; i <= 5; i++)
        {
            float t = i / 6f;
            int x = (int)MathHelper.Lerp(windowRect.X + 60f, windowRect.Right - 60f, t);
            DrawRect(batch, new Rectangle(x - 5, windowRect.Y + 10, 10, windowRect.Height - 20), frame * 0.90f);
            DrawRect(batch, new Rectangle(x - 2, windowRect.Y + 14, 4, windowRect.Height - 28), brass * 0.62f);
        }

        Vector2 helmCenter = Game1.GlobalToLocal(Game1.viewport, new Vector2(helm.X * 64f + 32f, helm.Y * 64f + 42f));
        Vector2 exitCenter = Game1.GlobalToLocal(Game1.viewport, new Vector2(exit.X * 64f + 32f, exit.Y * 64f + 36f));

        // Purple runner and brass rails join boarding door to helm.
        Vector2 laneTop = new(helmCenter.X, helmCenter.Y + 54f);
        Vector2 laneBottom = new(exitCenter.X, exitCenter.Y - 14f);
        float laneY = Math.Min(laneTop.Y, laneBottom.Y);
        float laneHeight = Math.Max(96f, Math.Abs(laneBottom.Y - laneTop.Y));
        Rectangle runner = new((int)helmCenter.X - 72, (int)laneY, 144, (int)laneHeight);
        DrawRect(batch, runner, new Color(78, 45, 83) * 0.34f);
        DrawRect(batch, new Rectangle(runner.X + 11, runner.Y, 4, runner.Height), gold * 0.38f);
        DrawRect(batch, new Rectangle(runner.Right - 15, runner.Y, 4, runner.Height), gold * 0.38f);
        for (int y = runner.Y + 28; y < runner.Bottom; y += 54)
            DrawDiamondRune(batch, new Vector2(runner.Center.X, y), 9f, gold * 0.30f);
        DrawManaLane(batch, exitCenter, helmCenter, cyan * 0.38f, phase);

        // Multi-level navigation dais and suspended astrolabe core.
        DrawRect(batch, new Rectangle((int)helmCenter.X - 132, (int)helmCenter.Y + 41, 264, 26), new Color(25, 22, 31) * 0.66f);
        DrawRect(batch, new Rectangle((int)helmCenter.X - 116, (int)helmCenter.Y + 24, 232, 32), woodDark);
        DrawRect(batch, new Rectangle((int)helmCenter.X - 98, (int)helmCenter.Y + 12, 196, 31), wood);
        DrawRect(batch, new Rectangle((int)helmCenter.X - 84, (int)helmCenter.Y + 5, 168, 10), brass);
        DrawEllipticArc(batch, new Vector2(helmCenter.X, helmCenter.Y - 58f), 82f, 76f, 0f, MathHelper.TwoPi, 24, 7f, brass * 0.88f);
        DrawEllipticArc(batch, new Vector2(helmCenter.X, helmCenter.Y - 58f), 61f, 55f, 0f, MathHelper.TwoPi, 22, 4f, violet * 0.76f);
        DrawEllipticArc(batch, new Vector2(helmCenter.X, helmCenter.Y - 58f), 39f, 34f, 0f, MathHelper.TwoPi, 18, 3f, cyan * 0.82f);
        DrawRotorStroke(batch, new Vector2(helmCenter.X, helmCenter.Y - 58f), phase * 0.42f, 78f, 3f, gold * 0.62f);
        DrawRotorStroke(batch, new Vector2(helmCenter.X, helmCenter.Y - 58f), -phase * 0.55f + MathHelper.PiOver2, 62f, 3f, cyan * 0.52f);
        DrawDiamondRune(batch, new Vector2(helmCenter.X, helmCenter.Y - 58f), 24f, cyan);
        DrawRect(batch, new Rectangle((int)helmCenter.X - 5, (int)helmCenter.Y - 31, 10, 38), gold * 0.58f);
        DrawArcaneSigil(batch, new Vector2(helmCenter.X, helmCenter.Y + 18f), 46f, violet * 0.64f, phase);
        DrawArcaneSparkles(batch, new Vector2(helmCenter.X, helmCenter.Y - 48f), 88f, 12, phase, Color.White * 0.52f);

        Vector2 leftConsole = Game1.GlobalToLocal(Game1.viewport, new Vector2(5f * 64f, 7.25f * 64f));
        Vector2 rightConsole = Game1.GlobalToLocal(Game1.viewport, new Vector2((width - 7f) * 64f, 7.25f * 64f));
        DrawBridgeConsole(batch, leftConsole, violet, cyan, gold, phase);
        DrawBridgeConsole(batch, rightConsole, cyan, violet, gold, -phase);
        DrawInstrumentCluster(batch, leftConsole + new Vector2(-88f, -10f), phase, gold, cyan);
        DrawInstrumentCluster(batch, rightConsole + new Vector2(88f, -10f), -phase, gold, violet);

        Vector2 leftBanner = Game1.GlobalToLocal(Game1.viewport, new Vector2(2.6f * 64f, 5.4f * 64f));
        Vector2 rightBanner = Game1.GlobalToLocal(Game1.viewport, new Vector2((width - 4.3f) * 64f, 5.4f * 64f));
        DrawCardchaBanner(batch, leftBanner, gold, violet);
        DrawCardchaBanner(batch, rightBanner, gold, violet);

        foreach ((AirshipUpgradeSystem system, Point socket) in ResolveDeckUpgradeSockets())
        {
            Vector2 s = Game1.GlobalToLocal(Game1.viewport, new Vector2(socket.X * 64f + 32f, socket.Y * 64f + 38f));
            DrawUpgradeSocket(batch, s, system, this.GetAirshipUpgradeLevel(system), phase, gold);
        }

        // Architectural alcove around the existing ChaCha station. The station runtime remains authoritative.
        Vector2 chachaAlcove = Game1.GlobalToLocal(Game1.viewport, new Vector2(19f * 64f + 32f, 5f * 64f + 32f));
        DrawEllipticArc(batch, chachaAlcove + new Vector2(0f, -22f), 54f, 46f, MathHelper.Pi, MathHelper.TwoPi, 16, 7f, brass * 0.68f);
        DrawCrystalPylon(batch, chachaAlcove + new Vector2(-58f, 28f), 28f, violet * 0.62f, gold * 0.58f);
        DrawCrystalPylon(batch, chachaAlcove + new Vector2(58f, 28f), 28f, cyan * 0.62f, gold * 0.58f);

        DrawArcaneSigil(batch, exitCenter, 29f, cyan * 0.48f, -phase * 0.42f);
        DrawWorldMarker(batch, helm, gold * 0.70f);
        DrawWorldMarker(batch, exit, cyan * 0.60f);
    }'''

HELPERS = r'''    private static void DrawVerticalGradient(SpriteBatch batch, Rectangle rect, Color top, Color middle, Color bottom)
    {
        if (rect.Width <= 0 || rect.Height <= 0)
            return;
        int h1 = Math.Max(1, rect.Height / 3);
        int h2 = Math.Max(1, rect.Height / 3);
        int h3 = Math.Max(1, rect.Height - h1 - h2);
        DrawRect(batch, new Rectangle(rect.X, rect.Y, rect.Width, h1), top);
        DrawRect(batch, new Rectangle(rect.X, rect.Y + h1, rect.Width, h2), middle);
        DrawRect(batch, new Rectangle(rect.X, rect.Y + h1 + h2, rect.Width, h3), bottom);
    }

    private static void DrawPortalClouds(SpriteBatch batch, Rectangle bounds, float phase, Color color)
    {
        int period = Math.Max(180, bounds.Width / 2);
        int shift = ((int)(phase * 29f) % period + period) % period;
        for (int i = -2; i < 6; i++)
        {
            int x = bounds.X + i * period + shift - 70;
            int y = bounds.Y + bounds.Height / 3 + (i % 3) * 31;
            DrawRect(batch, new Rectangle(x, y, 96, 11), color * 0.56f);
            DrawRect(batch, new Rectangle(x + 22, y - 9, 62, 13), color * 0.72f);
            DrawRect(batch, new Rectangle(x + 48, y + 7, 82, 9), color * 0.44f);
        }
    }

    private static void DrawEllipticArc(SpriteBatch batch, Vector2 center, float radiusX, float radiusY, float startAngle, float endAngle, int segments, float width, Color color)
    {
        segments = Math.Max(3, segments);
        Vector2 previous = new(center.X + MathF.Cos(startAngle) * radiusX, center.Y + MathF.Sin(startAngle) * radiusY);
        for (int i = 1; i <= segments; i++)
        {
            float t = i / (float)segments;
            float angle = MathHelper.Lerp(startAngle, endAngle, t);
            Vector2 current = new(center.X + MathF.Cos(angle) * radiusX, center.Y + MathF.Sin(angle) * radiusY);
            DrawLine(batch, previous, current, width, color);
            previous = current;
        }
    }

    private static void DrawLine(SpriteBatch batch, Vector2 start, Vector2 end, float width, Color color)
    {
        Vector2 delta = end - start;
        float length = delta.Length();
        if (length < 0.5f)
            return;
        DrawRotorStroke(batch, start, MathF.Atan2(delta.Y, delta.X), length, width, color);
    }

    private static void DrawBrassLamp(SpriteBatch batch, Vector2 baseCenter, float phase, Color brass, Color glow)
    {
        int x = (int)baseCenter.X;
        int y = (int)baseCenter.Y;
        DrawRect(batch, new Rectangle(x - 3, y - 37, 6, 37), brass * 0.86f);
        DrawRect(batch, new Rectangle(x - 12, y - 43, 24, 7), brass * 0.92f);
        DrawRect(batch, new Rectangle(x - 9, y - 63, 18, 20), new Color(39, 33, 43) * 0.92f);
        float flicker = 0.64f + 0.20f * MathF.Sin(phase * 2.4f + x * 0.01f);
        DrawRect(batch, new Rectangle(x - 6, y - 59, 12, 12), glow * flicker);
        DrawRect(batch, new Rectangle(x - 13, y - 66, 26, 4), brass * 0.82f);
    }

    private static void DrawRailing(SpriteBatch batch, Vector2 start, Vector2 end, Color brass, Color glow)
    {
        DrawLine(batch, start, end, 4f, brass * 0.86f);
        Vector2 delta = end - start;
        float length = delta.Length();
        if (length < 1f)
            return;
        Vector2 direction = delta / length;
        for (float d = 0f; d <= length; d += 72f)
        {
            Vector2 p = start + direction * d;
            DrawRect(batch, new Rectangle((int)p.X - 3, (int)p.Y - 28, 6, 31), brass * 0.84f);
            DrawDiamondRune(batch, new Vector2(p.X, p.Y - 30f), 6f, glow * 0.44f);
        }
    }

    private static void DrawFloatingIslands(SpriteBatch batch, Rectangle bounds, float phase)
    {
        Color far = new Color(74, 82, 91) * 0.24f;
        Color near = new Color(83, 91, 96) * 0.31f;
        int drift = (int)(phase * 7f);
        for (int i = 0; i < 4; i++)
        {
            int x = bounds.X + ((i * 283 + drift) % Math.Max(1, bounds.Width));
            int y = bounds.Y + 66 + (i % 3) * 46;
            int w = 54 + (i % 2) * 24;
            Color c = i % 2 == 0 ? far : near;
            DrawRect(batch, new Rectangle(x, y, w, 8), c);
            DrawRect(batch, new Rectangle(x + 9, y + 8, w - 18, 7), c * 0.82f);
            DrawRect(batch, new Rectangle(x + 19, y + 15, Math.Max(8, w - 38), 8), c * 0.64f);
            DrawRect(batch, new Rectangle(x + w / 2 - 2, y - 19, 4, 19), c * 0.80f);
        }
    }

    private static void DrawInstrumentCluster(SpriteBatch batch, Vector2 origin, float phase, Color gold, Color accent)
    {
        DrawRect(batch, new Rectangle((int)origin.X - 36, (int)origin.Y - 20, 72, 42), new Color(51, 40, 47) * 0.94f);
        DrawRect(batch, new Rectangle((int)origin.X - 30, (int)origin.Y - 14, 60, 29), new Color(92, 63, 50) * 0.88f);
        DrawEllipticArc(batch, origin + new Vector2(-14f, 0f), 10f, 10f, 0f, MathHelper.TwoPi, 12, 3f, gold * 0.72f);
        DrawEllipticArc(batch, origin + new Vector2(14f, 0f), 10f, 10f, 0f, MathHelper.TwoPi, 12, 3f, gold * 0.72f);
        DrawRotorStroke(batch, origin + new Vector2(-14f, 0f), phase * 0.33f, 8f, 2f, accent * 0.70f);
        DrawRotorStroke(batch, origin + new Vector2(14f, 0f), -phase * 0.41f, 8f, 2f, accent * 0.70f);
    }

    private static void DrawCardchaBanner(SpriteBatch batch, Vector2 origin, Color gold, Color violet)
    {
        Rectangle cloth = new((int)origin.X, (int)origin.Y, 94, 116);
        DrawRect(batch, cloth, new Color(72, 39, 91) * 0.82f);
        DrawRect(batch, new Rectangle(cloth.X + 7, cloth.Y + 7, cloth.Width - 14, 4), gold * 0.60f);
        DrawRect(batch, new Rectangle(cloth.X + 7, cloth.Bottom - 12, cloth.Width - 14, 4), gold * 0.48f);
        DrawDiamondRune(batch, new Vector2(cloth.Center.X, cloth.Y + 38f), 14f, violet * 0.72f);
        string text = "CARDCHA";
        Vector2 size = Game1.smallFont.MeasureString(text);
        batch.DrawString(Game1.smallFont, text, new Vector2(cloth.Center.X - size.X * 0.36f, cloth.Y + 61f), gold * 0.84f, 0f, Vector2.Zero, 0.72f, SpriteEffects.None, 1f);
    }'''


def replace_method(source: str, signature: str, replacement: str) -> str:
    start = source.find(signature)
    if start < 0:
        raise RuntimeError(f"method signature not found: {signature}")
    brace = source.find("{", start)
    if brace < 0:
        raise RuntimeError(f"method body not found: {signature}")
    depth = 0
    in_string = False
    escape = False
    i = brace
    while i < len(source):
        ch = source[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return source[:start] + replacement + source[i + 1:]
        i += 1
    raise RuntimeError(f"unterminated method: {signature}")


def write_if_changed(path: Path, text: str):
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old != text:
        path.write_text(text, encoding="utf-8")
        print(f"updated {path.relative_to(ROOT)}")
    else:
        print(f"unchanged {path.relative_to(ROOT)}")


airship = AIRSHIP.read_text(encoding="utf-8")
airship = replace_method(airship, "    private void DrawSkyDock(SpriteBatch batch, Point tile)", DRAW_SKY_DOCK)
airship = replace_method(airship, "    private void DrawSkyDockInteriorDetails(SpriteBatch batch, GameLocation interior)", DRAW_SKY_DOCK_INTERIOR)
airship = replace_method(airship, "    private void DrawDeckMarkers(SpriteBatch batch, GameLocation deck)", DRAW_DECK)

if "    private static void DrawVerticalGradient(" not in airship:
    insert_at = airship.find("    private static void DrawUpgradeSocket(")
    if insert_at < 0:
        raise RuntimeError("DrawUpgradeSocket insertion point not found")
    airship = airship[:insert_at] + HELPERS + "\n\n" + airship[insert_at:]

if "CollisionEdits=NONE" not in airship:
    raise RuntimeError("Airship collision compatibility contract missing")
write_if_changed(AIRSHIP, airship)

manifest_path = SRC / "manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["Version"] = VERSION
write_if_changed(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

csproj_path = SRC / "Cardcha.csproj"
csproj = csproj_path.read_text(encoding="utf-8")
csproj = re.sub(r"<Version>[^<]+</Version>", f"<Version>{VERSION}</Version>", csproj, count=1)
write_if_changed(csproj_path, csproj)

targets_path = SRC / "Directory.Build.targets"
targets = targets_path.read_text(encoding="utf-8")
targets = targets.replace(OLD_VERSION, VERSION)
targets = targets.replace(".4.14.4.3 ChaCha skill materials + Airship Resonance Pedestal.", ".4.14.4.5 Airship Visual Polish: Forest Gate + Sky Dock + Bridge.")
write_if_changed(targets_path, targets)

entry_path = SRC / "ModEntry.cs"
entry = entry_path.read_text(encoding="utf-8")
entry = entry.replace(OLD_VERSION, VERSION)
entry = entry.replace("CHACHA SUPPORT CAST RUNTIME TEST with {this.Cards.All.Count} cards.", "AIRSHIP VISUAL POLISH TEST with {this.Cards.All.Count} cards.")
write_if_changed(entry_path, entry)

doc_path = ROOT / "docs" / "alpha28-063-airship-visual-polish.md"
doc = """# Cardcha alpha28.0.4.14.4.5 — Airship Visual Polish

This pass translates the approved visual direction into the real in-game runtime overlays.

## Forest Arcane Gate
- deeper portal aperture with moving sky/cloud parallax
- heavy stone arch and brass inlay
- cyan/violet crystal pylons and Cardcha rune language
- stepped ground dais and readable walk-up seal
- **no Forest collision or tile edits**

## Sky Dock / Boarding Bay
- open-sky mooring aperture instead of a second abstract portal room
- the locked official Airship sprite is shown at full docked scale outside the bay
- boarding deck, rails, mooring arch and navigator console
- no miniature decorative ship inside the room
- existing arrival/bay/return transitions remain unchanged

## Airship Bridge
- grand panoramic forward canopy with moving sky/star field
- curved ship-frame architecture and brass ribs
- central multi-level navigation dais with suspended astrolabe crystal
- richer side consoles, instruments and Cardcha banners
- ChaCha Resonance Pedestal remains at its existing station neighborhood
- upgrade sockets retain their persistent visual feedback

## Locked regressions
- Save schema: 19
- Boss Form duration: 10s
- Support Cast rules/balance unchanged
- airship_visual.png unchanged
- Cardcha/MiMi locked visual hashes unchanged
- Forest collision contract: NONE
"""
write_if_changed(doc_path, doc)

print("alpha28-063 Airship Visual Polish finalizer complete")
