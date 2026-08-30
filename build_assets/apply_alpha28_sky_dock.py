from pathlib import Path

ROOT = Path('src/Cardcha')
OLD = '0.3.0-alpha.28.0.1.0'
NEW = '0.3.0-alpha.28.0.2.0'

# Version sync without touching any locked visual asset.
for rel in ['Cardcha.csproj', 'Directory.Build.targets', 'manifest.json', 'ModEntry.cs']:
    p = ROOT / rel
    text = p.read_text(encoding='utf-8')
    if OLD in text:
        text = text.replace(OLD, NEW)
    text = text.replace('AIRSHIP FOUNDATION TEST', 'SKY DOCK ACCESS TEST')
    p.write_text(text, encoding='utf-8')

service = r'''using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// Alpha.28 Airship foundation with the conflict-safe Sky Dock entrance.
///
/// Compatibility contract:
/// - The Dock is anchored dynamically from Forest's existing Farm warp instead of hard-coded
///   vanilla coordinates, so custom farm layouts don't move the access point into nonsense.
/// - It does NOT replace Forest map tiles, add objects, change collision, or reserve NPC paths.
/// - The visible dock is a lightweight Cardcha overlay only; base-game NPC movement/gameplay
///   remains authoritative. At worst a map overhaul may make the cosmetic marker less ideal,
///   but it should not break the Forest or block an NPC.
/// </summary>
internal sealed class AirshipFoundationService
{
    public const string DeckLocationName = "Cardcha_AirshipDeck";
    public const string DeckMapAssetName = "Maps/Cardcha_AirshipDeck";
    public const string SkyDockLocationName = "Forest";

    private const string DeckMapPath = "assets/airship_deck.tmx";
    private const long FlybyDurationMs = 4600L;
    private const long FlybyArmDelayMs = 2200L;
    private const float BoardingUseDistance = 128f;

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;

    private bool FlybyActive;
    private long FlybyStartedAtMs;
    private long FlybyArmAfterMs;
    private bool DeckCreationFailed;
    private bool LoggedDeckFailure;
    private bool LoggedDeckCreation;
    private Point? CachedSkyDockTile;
    private Point? CachedForestFarmWarpTile;
    private long WarpGraceUntilMs;

    public AirshipFoundationService(IModHelper helper, IMonitor monitor, SaveService save)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
    }

    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)
    {
        if (!e.NameWithoutLocale.IsEquivalentTo(DeckMapAssetName))
            return;

        e.LoadFromModFile<xTile.Map>(DeckMapPath, AssetLoadPriority.Exclusive);
    }

    public void OnSaveLoaded()
    {
        this.ResetRuntime();
        this.EnsureDeckLocation();
        this.MigrateUnlockFromExistingStory();
        this.FlybyArmAfterMs = Environment.TickCount64 + FlybyArmDelayMs;
    }

    public void OnDayStarted()
    {
        this.FlybyActive = false;
        this.FlybyStartedAtMs = 0;
        this.CachedSkyDockTile = null;
        this.CachedForestFarmWarpTile = null;
        this.DeckCreationFailed = false;
        this.LoggedDeckFailure = false;
        this.EnsureDeckLocation();
        this.MigrateUnlockFromExistingStory();
        this.FlybyArmAfterMs = Environment.TickCount64 + 1500L;
    }

    public void OnReturnedToTitle()
    {
        this.ResetRuntime();
        this.LoggedDeckCreation = false;
    }

    public void OnUpdateTicked(UpdateTickedEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        long now = Environment.TickCount64;
        if (this.FlybyActive)
        {
            if (now - this.FlybyStartedAtMs >= FlybyDurationMs)
            {
                this.FlybyActive = false;
                this.FlybyStartedAtMs = 0;
            }
            return;
        }

        if (!this.Save.Data.AirshipFlybySeen
            && !this.Save.Data.FirstScrapTriggered
            && now >= this.FlybyArmAfterMs
            && Game1.currentLocation == Game1.getFarm()
            && Game1.timeOfDay >= 700
            && Game1.timeOfDay < 1900
            && Game1.activeClickableMenu is null
            && !Game1.dialogueUp
            && !Game1.eventUp)
        {
            this.StartFlyby(persistSeen: true);
        }
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        if (this.FlybyActive && Game1.currentLocation == Game1.getFarm())
            this.DrawFlyby(e.SpriteBatch);

        GameLocation? location = Game1.currentLocation;
        if (this.Save.Data.AirshipUnlocked && IsSkyDockLocation(location))
            this.DrawSkyDock(e.SpriteBatch, this.ResolveSkyDockTile());

        if (location?.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase) == true)
            this.DrawDeckMarkers(e.SpriteBatch, location);
    }

    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady
            || !e.Button.IsActionButton()
            || Game1.activeClickableMenu is not null
            || Game1.dialogueUp
            || Game1.eventUp
            || Environment.TickCount64 < this.WarpGraceUntilMs)
        {
            return;
        }

        GameLocation? location = Game1.currentLocation;
        if (location is null)
            return;

        // Sky Dock is the normal gameplay entrance. It never edits Forest collision/pathing.
        if (IsSkyDockLocation(location) && this.Save.Data.AirshipUnlocked)
        {
            Point dock = this.ResolveSkyDockTile();
            if (!PlayerIsNear(dock))
                return;

            GameLocation? deck = this.EnsureDeckLocation();
            if (deck is null)
            {
                this.Helper.Input.Suppress(e.Button);
                Game1.drawObjectDialogue(ModEntry.T("airship.deck.unavailable"));
                return;
            }

            this.Helper.Input.Suppress(e.Button);
            Point arrival = ResolveDeckArrivalTile(deck);
            this.WarpGraceUntilMs = Environment.TickCount64 + 850L;
            Game1.warpFarmer(DeckLocationName, arrival.X, arrival.Y, 0);
            return;
        }

        if (!location.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))
            return;

        Point action = GetActionTile();
        Point helm = ResolveDeckHelmTile(location);
        Point exit = ResolveDeckExitTile(location);

        if (Touches(action, helm))
        {
            this.Helper.Input.Suppress(e.Button);
            int owned = this.Save.Data.OwnedCards?.Count ?? 0;
            Game1.drawObjectDialogue(
                this.Save.Data.AirshipHighestRegionUnlocked >= 1
                    ? ModEntry.T("airship.route.region1.foundation", new { cards = owned })
                    : ModEntry.T("airship.route.locked")
            );
            return;
        }

        if (!Touches(action, exit) && !PlayerIsNear(exit))
            return;

        this.Helper.Input.Suppress(e.Button);
        this.ReturnToSkyDock();
    }

    /// <summary>TEST-only direct deck access; does not unlock the Airship or alter story flags.</summary>
    public string DebugToggleDeck()
    {
        if (!Context.IsWorldReady)
            return "Airship TEST unavailable: load a save first.";

        if (Game1.currentLocation?.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase) == true)
        {
            this.ReturnToSkyDock();
            return "Airship TEST: returned to Sky Dock. Story/unlock state was not changed.";
        }

        GameLocation? deck = this.EnsureDeckLocation();
        if (deck is null)
            return "Airship TEST couldn't create Cardcha_AirshipDeck.";

        Point arrival = ResolveDeckArrivalTile(deck);
        this.WarpGraceUntilMs = Environment.TickCount64 + 850L;
        Game1.warpFarmer(DeckLocationName, arrival.X, arrival.Y, 0);
        return "Airship TEST: warped to Cardcha_AirshipDeck. Run cardcha_test_airship again to return to Sky Dock. Story/unlock state was not changed.";
    }

    /// <summary>TEST-only replay of the distant Farm flyby without changing the persisted seen flag.</summary>
    public string DebugReplayFlyby()
    {
        if (!Context.IsWorldReady)
            return "Airship flyby TEST unavailable: load a save first.";

        if (Game1.currentLocation != Game1.getFarm())
            return "Airship flyby TEST: go to the Farm first.";

        this.StartFlyby(persistSeen: false);
        return "Airship flyby TEST started. The persisted flyby/story state was not changed.";
    }

    public string Describe()
    {
        if (!Context.IsWorldReady)
            return "Airship=<no save>";

        Point dock = this.ResolveSkyDockTile();
        Point farmWarp = this.ResolveForestFarmWarpTile();
        bool deckExists = Game1.getLocationFromName(DeckLocationName) is not null;
        return $"AirshipFlybySeen={this.Save.Data.AirshipFlybySeen} | " +
               $"FlybyActive={this.FlybyActive} | " +
               $"Unlocked={this.Save.Data.AirshipUnlocked} | " +
               $"HighestRegion={this.Save.Data.AirshipHighestRegionUnlocked} | " +
               $"UnlockDay={this.Save.Data.AirshipUnlockedDay} | " +
               $"DeckExists={deckExists} | SkyDock={SkyDockLocationName}({dock.X},{dock.Y}) | " +
               $"ForestFarmWarp={farmWarp.X},{farmWarp.Y} | CollisionEdits=NONE";
    }

    private void MigrateUnlockFromExistingStory()
    {
        if (!Context.IsWorldReady || !this.Save.Data.MimiMeetupCompleted)
            return;

        bool changed = false;
        if (!this.Save.Data.AirshipUnlocked)
        {
            this.Save.Data.AirshipUnlocked = true;
            changed = true;
        }

        if (this.Save.Data.AirshipHighestRegionUnlocked < 1)
        {
            this.Save.Data.AirshipHighestRegionUnlocked = 1;
            changed = true;
        }

        if (this.Save.Data.AirshipUnlockedDay < 0)
        {
            this.Save.Data.AirshipUnlockedDay = Game1.Date.TotalDays;
            changed = true;
        }

        if (!changed)
            return;

        this.Save.Save();
        this.Monitor.Log(
            "Alpha.28 Airship migration: existing completed MiMi/Wizard handoff now owns Region I access through Sky Dock.",
            LogLevel.Info
        );
    }

    private void StartFlyby(bool persistSeen)
    {
        this.FlybyActive = true;
        this.FlybyStartedAtMs = Environment.TickCount64;

        if (persistSeen && !this.Save.Data.AirshipFlybySeen)
        {
            this.Save.Data.AirshipFlybySeen = true;
            this.Save.Save();
        }

        Game1.playSound("wand");
        this.Monitor.Log(
            persistSeen
                ? "Alpha.28 pre-MiMi Airship flyby played and was persisted as seen."
                : "Alpha.28 TEST replay of the pre-MiMi Airship flyby started.",
            LogLevel.Trace
        );
    }

    private GameLocation? EnsureDeckLocation()
    {
        if (!Context.IsWorldReady || this.DeckCreationFailed)
            return null;

        GameLocation? existing = Game1.getLocationFromName(DeckLocationName);
        if (existing is not null)
            return existing;

        try
        {
            GameLocation deck = new(DeckMapAssetName, DeckLocationName);
            Game1.locations.Add(deck);
            if (!this.LoggedDeckCreation)
            {
                this.LoggedDeckCreation = true;
                this.Monitor.Log(
                    "Created Cardcha_AirshipDeck from Cardcha-owned alpha.28 foundation map.",
                    LogLevel.Info
                );
            }
            return deck;
        }
        catch (Exception ex)
        {
            this.DeckCreationFailed = true;
            if (!this.LoggedDeckFailure)
            {
                this.LoggedDeckFailure = true;
                this.Monitor.Log(
                    $"Couldn't create Cardcha Airship deck; retries suppressed until next save/day. {ex.GetType().Name}: {ex.Message}",
                    LogLevel.Error
                );
            }
            return null;
        }
    }

    private void ReturnToSkyDock()
    {
        GameLocation? forest = Game1.getLocationFromName(SkyDockLocationName);
        if (forest is null)
        {
            GameLocation? farm = Game1.getFarm();
            if (farm is null)
                return;

            Point fallback = FindClearTileNear(farm, new Point(8, 8));
            this.WarpGraceUntilMs = Environment.TickCount64 + 850L;
            Game1.warpFarmer(farm.NameOrUniqueName, fallback.X, fallback.Y, 2);
            return;
        }

        Point dock = this.ResolveSkyDockTile();
        Point landing = FindClearTileNear(forest, new Point(dock.X + 1, dock.Y + 1));
        this.WarpGraceUntilMs = Environment.TickCount64 + 850L;
        Game1.warpFarmer(forest.NameOrUniqueName, landing.X, landing.Y, 2);
    }

    private Point ResolveSkyDockTile()
    {
        if (this.CachedSkyDockTile is Point cached)
            return cached;

        GameLocation? forest = Game1.getLocationFromName(SkyDockLocationName);
        if (forest is null)
        {
            this.CachedSkyDockTile = new Point(6, 6);
            return this.CachedSkyDockTile.Value;
        }

        Point farmWarp = this.ResolveForestFarmWarpTile();
        int width = forest.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 120;
        int height = forest.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 120;

        // Player exits the Farm into Forest; the dock should be visible immediately to the left.
        // Search a compact left-side band instead of claiming a fixed vanilla tile.
        Point preferred = new(
            Math.Clamp(farmWarp.X - 7, 2, Math.Max(2, width - 3)),
            Math.Clamp(farmWarp.Y + 2, 2, Math.Max(2, height - 3))
        );

        Point? safe = FindSafeDockTile(forest, preferred, farmWarp);
        this.CachedSkyDockTile = safe ?? preferred;
        return this.CachedSkyDockTile.Value;
    }

    private Point ResolveForestFarmWarpTile()
    {
        if (this.CachedForestFarmWarpTile is Point cached)
            return cached;

        GameLocation? forest = Game1.getLocationFromName(SkyDockLocationName);
        if (forest is null)
        {
            this.CachedForestFarmWarpTile = new Point(20, 2);
            return this.CachedForestFarmWarpTile.Value;
        }

        try
        {
            foreach (Warp warp in forest.warps)
            {
                if (!string.IsNullOrWhiteSpace(warp.TargetName)
                    && warp.TargetName.Contains("Farm", StringComparison.OrdinalIgnoreCase))
                {
                    this.CachedForestFarmWarpTile = new Point(warp.X, warp.Y);
                    return this.CachedForestFarmWarpTile.Value;
                }
            }
        }
        catch
        {
            // A heavily rewritten Forest may expose warps differently. Fall back to upper-middle.
        }

        int width = forest.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 120;
        this.CachedForestFarmWarpTile = new Point(Math.Clamp(width / 2, 3, Math.Max(3, width - 4)), 2);
        return this.CachedForestFarmWarpTile.Value;
    }

    private static Point? FindSafeDockTile(GameLocation forest, Point preferred, Point farmWarp)
    {
        int width = forest.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 120;
        int height = forest.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 120;

        for (int radius = 0; radius <= 7; radius++)
        {
            for (int y = Math.Max(2, preferred.Y - radius); y <= Math.Min(height - 3, preferred.Y + radius); y++)
            {
                // Keep every candidate visibly left of the Farm entrance and out of its warp lane.
                for (int x = Math.Max(2, preferred.X - radius); x <= Math.Min(farmWarp.X - 4, preferred.X + radius); x++)
                {
                    Point candidate = new(x, y);
                    if (IsDockFootprintSafe(forest, candidate, farmWarp))
                        return candidate;
                }
            }
        }

        return null;
    }

    private static bool IsDockFootprintSafe(GameLocation location, Point anchor, Point farmWarp)
    {
        Point[] footprint =
        {
            anchor,
            new(anchor.X - 1, anchor.Y),
            new(anchor.X + 1, anchor.Y),
            new(anchor.X - 1, anchor.Y + 1),
            new(anchor.X, anchor.Y + 1),
            new(anchor.X + 1, anchor.Y + 1)
        };

        foreach (Point p in footprint)
        {
            if (Math.Abs(p.X - farmWarp.X) <= 3 && Math.Abs(p.Y - farmWarp.Y) <= 3)
                return false;

            try
            {
                Vector2 tile = new(p.X, p.Y);
                if (location.IsTileBlockedBy(tile) || location.Objects.ContainsKey(tile))
                    return false;
            }
            catch
            {
                return false;
            }

            try
            {
                foreach (Warp warp in location.warps)
                {
                    if (Math.Abs(warp.X - p.X) <= 2 && Math.Abs(warp.Y - p.Y) <= 2)
                        return false;
                }
            }
            catch
            {
                // Don't reject the candidate solely because a map overhaul hides warp metadata.
            }
        }

        return true;
    }

    private static Point ResolveDeckArrivalTile(GameLocation deck)
    {
        int width = deck.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 24;
        int height = deck.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 14;
        Point preferred = new(width / 2, Math.Max(2, height - 4));
        return FindClearTileNear(deck, preferred);
    }

    private static Point ResolveDeckExitTile(GameLocation deck)
    {
        int width = deck.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 24;
        int height = deck.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 14;
        return new Point(Math.Clamp(width / 2, 1, width - 2), Math.Clamp(height - 2, 1, height - 2));
    }

    private static Point ResolveDeckHelmTile(GameLocation deck)
    {
        int width = deck.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 24;
        int height = deck.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 14;
        return new Point(Math.Clamp(width / 2, 2, width - 3), Math.Clamp(4, 2, height - 3));
    }

    private void DrawFlyby(SpriteBatch batch)
    {
        float progress = Math.Clamp(
            (Environment.TickCount64 - this.FlybyStartedAtMs) / (float)FlybyDurationMs,
            0f,
            1f
        );

        float screenX = MathHelper.Lerp(-240f, Game1.viewport.Width + 240f, progress);
        float screenY = 92f - (float)Math.Sin(progress * Math.PI) * 18f;
        Vector2 world = new(Game1.viewport.X + screenX, Game1.viewport.Y + screenY);
        Vector2 p = Game1.GlobalToLocal(Game1.viewport, world);

        Color silhouette = new Color(48, 38, 68) * 0.82f;
        Color gondola = new Color(66, 47, 49) * 0.88f;
        Color glint = new Color(190, 225, 255) * 0.55f;

        DrawRect(batch, new Rectangle((int)p.X - 74, (int)p.Y - 20, 148, 10), silhouette);
        DrawRect(batch, new Rectangle((int)p.X - 88, (int)p.Y - 10, 176, 12), silhouette);
        DrawRect(batch, new Rectangle((int)p.X - 94, (int)p.Y + 2, 188, 14), silhouette);
        DrawRect(batch, new Rectangle((int)p.X - 82, (int)p.Y + 16, 164, 10), silhouette);
        DrawRect(batch, new Rectangle((int)p.X - 50, (int)p.Y + 26, 100, 6), silhouette);

        DrawRect(batch, new Rectangle((int)p.X - 46, (int)p.Y + 42, 92, 16), gondola);
        DrawRect(batch, new Rectangle((int)p.X - 30, (int)p.Y + 34, 4, 10), silhouette);
        DrawRect(batch, new Rectangle((int)p.X + 26, (int)p.Y + 34, 4, 10), silhouette);
        DrawRect(batch, new Rectangle((int)p.X + 45, (int)p.Y + 46, 24, 5), gondola);
        DrawRect(batch, new Rectangle((int)p.X - 67, (int)p.Y + 47, 22, 4), gondola);
        DrawRect(batch, new Rectangle((int)p.X + 12, (int)p.Y + 47, 5, 4), glint);
    }

    private void DrawSkyDock(SpriteBatch batch, Point tile)
    {
        Vector2 screen = Game1.GlobalToLocal(
            Game1.viewport,
            new Vector2((tile.X - 1) * 64f, tile.Y * 64f)
        );

        // Small, non-blocking Stardew-scale foundation: weathered planks + two rope posts +
        // MiMi's restrained cyan route glow. This is intentionally lightweight until final art.
        Color plankDark = new Color(96, 63, 38) * 0.86f;
        Color plank = new Color(145, 98, 57) * 0.90f;
        Color edge = new Color(69, 47, 31) * 0.92f;
        Color rope = new Color(205, 174, 112) * 0.82f;
        float pulse = 0.42f + 0.18f * (float)Math.Sin(Environment.TickCount64 / 260.0);
        Color glow = new Color(105, 214, 236) * pulse;

        for (int row = 0; row < 2; row++)
        {
            int y = (int)screen.Y + 18 + row * 25;
            DrawRect(batch, new Rectangle((int)screen.X + 5, y, 182, 22), plank);
            DrawRect(batch, new Rectangle((int)screen.X + 5, y + 19, 182, 3), plankDark);
            for (int seam = 1; seam <= 5; seam++)
                DrawRect(batch, new Rectangle((int)screen.X + seam * 30, y, 2, 22), edge * 0.62f);
        }

        DrawRect(batch, new Rectangle((int)screen.X + 9, (int)screen.Y - 16, 9, 78), edge);
        DrawRect(batch, new Rectangle((int)screen.X + 174, (int)screen.Y - 16, 9, 78), edge);
        DrawRect(batch, new Rectangle((int)screen.X + 18, (int)screen.Y - 5, 156, 3), rope);
        DrawRect(batch, new Rectangle((int)screen.X + 78, (int)screen.Y + 31, 38, 5), glow);
        DrawRect(batch, new Rectangle((int)screen.X + 94, (int)screen.Y + 15, 6, 37), glow);
    }

    private void DrawDeckMarkers(SpriteBatch batch, GameLocation deck)
    {
        Point helm = ResolveDeckHelmTile(deck);
        Point exit = ResolveDeckExitTile(deck);
        DrawWorldMarker(batch, helm, new Color(255, 220, 120) * 0.58f);
        DrawWorldMarker(batch, exit, new Color(120, 220, 255) * 0.52f);
    }

    private static void DrawWorldMarker(SpriteBatch batch, Point tile, Color color)
    {
        Vector2 screen = Game1.GlobalToLocal(Game1.viewport, new Vector2(tile.X * 64f, tile.Y * 64f));
        DrawRect(batch, new Rectangle((int)screen.X + 14, (int)screen.Y + 48, 36, 5), color);
        DrawRect(batch, new Rectangle((int)screen.X + 29, (int)screen.Y + 34, 6, 24), color);
    }

    private static void DrawRect(SpriteBatch batch, Rectangle rectangle, Color color)
    {
        if (rectangle.Width <= 0 || rectangle.Height <= 0)
            return;
        batch.Draw(Game1.staminaRect, rectangle, color);
    }

    private static Point GetActionTile()
    {
        Point p = new((int)(Game1.player.Position.X / 64f), (int)(Game1.player.Position.Y / 64f));
        return Game1.player.FacingDirection switch
        {
            0 => new Point(p.X, p.Y - 1),
            1 => new Point(p.X + 1, p.Y),
            2 => new Point(p.X, p.Y + 1),
            3 => new Point(p.X - 1, p.Y),
            _ => p
        };
    }

    private static bool IsSkyDockLocation(GameLocation? location)
        => location?.NameOrUniqueName.Equals(SkyDockLocationName, StringComparison.OrdinalIgnoreCase) == true;

    private static bool PlayerIsNear(Point tile)
    {
        Vector2 center = new(tile.X * 64f + 32f, tile.Y * 64f + 32f);
        Vector2 player = Game1.player.Position + new Vector2(32f, 32f);
        return Vector2.DistanceSquared(center, player) <= BoardingUseDistance * BoardingUseDistance;
    }

    private static bool Touches(Point actionTile, Point tile)
        => Math.Abs(actionTile.X - tile.X) <= 1 && Math.Abs(actionTile.Y - tile.Y) <= 1;

    private static Point FindClearTileNear(GameLocation location, Point preferred)
    {
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 24;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 14;
        int centerX = Math.Clamp(preferred.X, 1, Math.Max(1, width - 2));
        int centerY = Math.Clamp(preferred.Y, 1, Math.Max(1, height - 2));

        for (int radius = 0; radius < Math.Max(width, height); radius++)
        {
            for (int y = Math.Max(1, centerY - radius); y <= Math.Min(height - 2, centerY + radius); y++)
            {
                for (int x = Math.Max(1, centerX - radius); x <= Math.Min(width - 2, centerX + radius); x++)
                {
                    if (Math.Abs(x - centerX) != radius && Math.Abs(y - centerY) != radius)
                        continue;

                    Point candidate = new(x, y);
                    try
                    {
                        Vector2 tile = new(candidate.X, candidate.Y);
                        if (!location.IsTileBlockedBy(tile) && !location.Objects.ContainsKey(tile))
                            return candidate;
                    }
                    catch
                    {
                        return candidate;
                    }
                }
            }
        }

        return new Point(centerX, centerY);
    }

    private void ResetRuntime()
    {
        this.FlybyActive = false;
        this.FlybyStartedAtMs = 0;
        this.FlybyArmAfterMs = 0;
        this.DeckCreationFailed = false;
        this.LoggedDeckFailure = false;
        this.CachedSkyDockTile = null;
        this.CachedForestFarmWarpTile = null;
        this.WarpGraceUntilMs = 0;
    }
}
'''
(ROOT / 'Services/AirshipFoundationService.cs').write_text(service, encoding='utf-8')

print('alpha.28.0.2.0 conflict-safe Sky Dock patch applied')
