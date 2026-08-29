using Cardcha.Services;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Menus;

namespace Cardcha.UI;

internal sealed class CardchaBookTabService
{
    private const int BookTabId = 913407;

    private readonly IModHelper Helper;
    private readonly SaveService Save;
    private readonly Action<IClickableMenu> OpenBinderFromMenu;

    private readonly ClickableComponent BookTab =
        new(new Rectangle(0, 0, 64, 64), "cardcha-book-tab")
        {
            myID = BookTabId,
            fullyImmutable = true,
            leftNeighborImmutable = true,
            rightNeighborImmutable = true
        };

    private IClickableMenu? AttachedMenu;
    private IClickableMenu? AttachedGraphOwner;
    private int? LinkedNeighborId;
    private int? LastReturnNeighborId;
    private bool BookInsertedOnLeft;
    private bool BookFocusWasActive;
    private int PendingBookCursorFrames;
    private int PendingReturnCursorFrames;
    private int? PendingReturnTargetId;

    private string LayoutMode = "Detached";
    private string TabDetectionSource = "none";
    private string GraphOwnerState = "<none>";
    private string ComponentState = "unknown";
    private bool PopulateAttempted;
    private bool NativeTabsEnsuredForCurrentGraph;
    private int LastDuplicateCleanupCount;
    private Texture2D? BinderTabIcon;
    private bool BinderTabIconChecked;

    public CardchaBookTabService(
        IModHelper helper,
        SaveService save,
        Action<IClickableMenu> openBinderFromMenu)
    {
        this.Helper = helper;
        this.Save = save;
        this.OpenBinderFromMenu = openBinderFromMenu;
    }

    public void OnMenuChanged(object? sender, MenuChangedEventArgs e)
    {
        ResetAttachmentState();

        if (IsSupported(e.NewMenu))
            EnsureAttached(e.NewMenu!);
    }

    public void OnRenderedActiveMenu(
        object? sender,
        RenderedActiveMenuEventArgs e)
    {
        IClickableMenu? menu = Game1.activeClickableMenu;
        if (!IsSupported(menu) || !this.Save.Data.BinderUnlocked)
            return;

        EnsureAttached(menu!);

        IClickableMenu graphOwner = GetGraphOwner(menu!) ?? menu!;
        bool bookFocused =
            graphOwner.currentlySnappedComponent?.myID == BookTabId;

        // BIDIRECTIONAL FOCUS RACE FIX:
        // both LEFT -> Book and Book -> RIGHT can be overwritten later in the
        // same frame by InventoryPage/another menu mod. Hold either destination
        // for a few render frames after the transition.
        if (this.PendingBookCursorFrames > 0)
        {
            graphOwner.currentlySnappedComponent = this.BookTab;
            graphOwner.snapCursorToCurrentSnappedComponent();

            this.PendingBookCursorFrames--;
            this.PendingReturnCursorFrames = 0;
            this.PendingReturnTargetId = null;
            bookFocused = true;
        }
        else if (this.PendingReturnCursorFrames > 0
            && this.PendingReturnTargetId.HasValue)
        {
            ClickableComponent? returnTarget =
                graphOwner.allClickableComponents?
                    .FirstOrDefault(
                        p => p.myID
                            == this.PendingReturnTargetId.Value
                    );

            if (returnTarget is not null)
            {
                graphOwner.currentlySnappedComponent = returnTarget;
                graphOwner.snapCursorToCurrentSnappedComponent();
                bookFocused = false;
            }

            this.PendingReturnCursorFrames--;

            if (this.PendingReturnCursorFrames <= 0)
                this.PendingReturnTargetId = null;
        }
        else if (bookFocused && !this.BookFocusWasActive)
        {
            graphOwner.currentlySnappedComponent = this.BookTab;
            graphOwner.snapCursorToCurrentSnappedComponent();
            bookFocused = true;
        }

        this.BookFocusWasActive = bookFocused;
        DrawTab(e.SpriteBatch, graphOwner);
    }

    public void OnButtonPressed(
        object? sender,
        ButtonPressedEventArgs e)
    {
        IClickableMenu? menu = Game1.activeClickableMenu;
        if (!IsSupported(menu) || !this.Save.Data.BinderUnlocked)
            return;

        EnsureAttached(menu!);

        IClickableMenu graphOwner = GetGraphOwner(menu!) ?? menu!;
        int? currentId = graphOwner.currentlySnappedComponent?.myID;

        if (menu is GameMenu)
        {
            bool towardBook = IsControllerLeft(e.Button);
            bool awayFromBook = IsControllerRight(e.Button);

            // Any real LEFT-MOST component of its horizontal row can enter
            // Cardcha with exactly one LEFT press. This fixes the lower inventory
            // rows where vanilla previously kept moving the white hand elsewhere.
            if (currentId != BookTabId
                && towardBook
                && (
                    IsLeftEdgeComponent(graphOwner, currentId)
                    || CurrentComponentPointsToBook(graphOwner, currentId)
                ))
            {
                this.Helper.Input.Suppress(e.Button);

                this.LastReturnNeighborId = currentId;
                this.BookTab.rightNeighborID = currentId ?? -1;
                this.BookTab.rightNeighborImmutable = true;

                FocusBook(graphOwner);
                return;
            }

            if (currentId == BookTabId && awayFromBook)
            {
                this.Helper.Input.Suppress(e.Button);
                FocusReturnComponent(graphOwner);
                return;
            }
        }

        Point cursor = CardchaUi.GetUiMousePoint();

        bool mousePressed =
            e.Button == SButton.MouseLeft
            && this.BookTab.bounds.Contains(cursor.X, cursor.Y);

        bool controllerPressed =
            e.Button == SButton.ControllerA
            && currentId == BookTabId;

        if (!mousePressed && !controllerPressed)
            return;

        this.Helper.Input.Suppress(e.Button);
        Game1.playSound("bigSelect");
        this.OpenBinderFromMenu(menu!);
    }

    public string Describe()
    {
        IClickableMenu? menu = Game1.activeClickableMenu;
        IClickableMenu? graphOwner =
            menu is null ? null : GetGraphOwner(menu);

        int? focus =
            graphOwner?.currentlySnappedComponent?.myID
            ?? menu?.currentlySnappedComponent?.myID;

        return
            $"Menu={menu?.GetType().Name ?? "<none>"} | " +
            $"GraphOwner={this.GraphOwnerState} | " +
            $"Layout={this.LayoutMode} | " +
            $"Book=({this.BookTab.bounds.X},{this.BookTab.bounds.Y}," +
            $"{this.BookTab.bounds.Width}x{this.BookTab.bounds.Height}) | " +
            $"TabSource={this.TabDetectionSource} | " +
            $"Components={this.ComponentState} | " +
            $"PopulateAttempted={this.PopulateAttempted} | " +
            $"TabsEnsured={this.NativeTabsEnsuredForCurrentGraph} | " +
            $"DuplicatesCleaned={this.LastDuplicateCleanupCount} | " +
            $"Linked={this.LinkedNeighborId?.ToString() ?? "<none>"} | " +
            $"Return={this.LastReturnNeighborId?.ToString() ?? "<none>"} | " +
            $"BookCapture={this.PendingBookCursorFrames} | " +
            $"ReturnCapture={this.PendingReturnCursorFrames} | " +
            $"ReturnTarget={this.PendingReturnTargetId?.ToString() ?? "<none>"} | " +
            $"InsertedOnLeft={this.BookInsertedOnLeft} | " +
            $"Focus={focus?.ToString() ?? "<none>"}";
    }

    private static bool IsSupported(IClickableMenu? menu)
    {
        if (menu is not GameMenu gameMenu)
            return false;

        return GetGraphOwner(gameMenu) is InventoryPage;
    }

    private void ResetAttachmentState()
    {
        this.AttachedMenu = null;
        this.AttachedGraphOwner = null;
        this.LinkedNeighborId = null;
        this.LastReturnNeighborId = null;
        this.BookInsertedOnLeft = false;
        this.BookFocusWasActive = false;
        this.PendingBookCursorFrames = 0;
        this.PendingReturnCursorFrames = 0;
        this.PendingReturnTargetId = null;

        this.LayoutMode = "Detached";
        this.TabDetectionSource = "none";
        this.GraphOwnerState = "<none>";
        this.ComponentState = "unknown";
        this.PopulateAttempted = false;
        this.NativeTabsEnsuredForCurrentGraph = false;
        this.LastDuplicateCleanupCount = 0;
    }

    private void EnsureAttached(IClickableMenu menu)
    {
        IClickableMenu graphOwner = GetGraphOwner(menu) ?? menu;

        if (!ReferenceEquals(this.AttachedMenu, menu)
            || !ReferenceEquals(this.AttachedGraphOwner, graphOwner))
        {
            this.AttachedMenu = menu;
            this.AttachedGraphOwner = graphOwner;

            this.LinkedNeighborId = null;
            this.LastReturnNeighborId = null;
            this.BookInsertedOnLeft = false;
            this.BookFocusWasActive = false;
            this.PendingBookCursorFrames = 0;
            this.PendingReturnCursorFrames = 0;
            this.PendingReturnTargetId = null;

            this.LayoutMode = "Detached";
            this.TabDetectionSource = "none";
            this.PopulateAttempted = false;
            this.NativeTabsEnsuredForCurrentGraph = false;
            this.LastDuplicateCleanupCount = 0;
        }

        this.GraphOwnerState = graphOwner.GetType().Name;

        List<ClickableComponent>? components =
            graphOwner.allClickableComponents;

        if (components is null)
        {
            this.PopulateAttempted = true;

            try
            {
                graphOwner.populateClickableComponentList();
            }
            catch (Exception ex)
            {
                ModEntry.StaticMonitor?.LogOnce(
                    $"Cardcha couldn't populate clickable components for " +
                    $"{graphOwner.GetType().Name}: {ex.Message}",
                    LogLevel.Trace
                );
            }

            components = graphOwner.allClickableComponents;
        }

        // IMPORTANT:
        // Do NOT append GameMenu tabs every render. alpha.24 status exposed
        // Components=count:6842, which means the page graph had thousands of
        // duplicated tab controls. That makes SnappyMenus traversal unstable.
        //
        // Ensure native tabs once per PAGE graph, and clean old duplicates left
        // behind by earlier Cardcha builds before wiring our Book.
        if (menu is GameMenu gameMenu && components is not null)
        {
            this.LastDuplicateCleanupCount =
                CleanupDuplicateNativeTabs(gameMenu, components);

            if (!this.NativeTabsEnsuredForCurrentGraph)
            {
                EnsureNativeTabsPresentOnce(
                    gameMenu,
                    graphOwner,
                    components
                );

                this.NativeTabsEnsuredForCurrentGraph = true;
                components = graphOwner.allClickableComponents;
            }
        }

        this.ComponentState = components is null
            ? "null-after-populate"
            : $"count:{components.Count}";

        if (components is null)
        {
            if (menu is GameMenu)
                AttachBodyAnchorWithoutGraph((GameMenu)menu);
            else
                AttachDetachedTop(menu);

            return;
        }

        // Remove a stale Cardcha component instance if the page graph was rebuilt.
        foreach (ClickableComponent duplicate in components
            .Where(p =>
                p.myID == BookTabId
                && !ReferenceEquals(p, this.BookTab))
            .ToList())
        {
            components.Remove(duplicate);
        }

        if (menu is GameMenu gameMenuWithGraph)
        {
            AttachToCurrentGameMenuPage(
                gameMenuWithGraph,
                graphOwner,
                components
            );
        }
        else
        {
            AttachToItemGrabTop(
                menu,
                graphOwner,
                components
            );
        }

        if (!components.Contains(this.BookTab))
            components.Add(this.BookTab);
    }

    /// <summary>
    /// GameMenu delegates controller snapping to the current page.
    /// Retrieve that page without relying on a specific public/private shape.
    /// </summary>
    private static IClickableMenu? GetGraphOwner(IClickableMenu menu)
    {
        if (menu is not GameMenu gameMenu)
            return menu;

        const System.Reflection.BindingFlags flags =
            System.Reflection.BindingFlags.Instance
            | System.Reflection.BindingFlags.Public
            | System.Reflection.BindingFlags.NonPublic;

        Type type = gameMenu.GetType();

        try
        {
            System.Reflection.MethodInfo? method =
                type.GetMethod("GetCurrentPage", flags);

            if (method?.Invoke(gameMenu, null) is IClickableMenu page)
                return page;
        }
        catch
        {
        }

        try
        {
            object? pagesValue =
                type.GetField("pages", flags)?.GetValue(gameMenu)
                ?? type.GetProperty("pages", flags)?.GetValue(gameMenu);

            object? currentValue =
                type.GetField("currentTab", flags)?.GetValue(gameMenu)
                ?? type.GetProperty("currentTab", flags)?.GetValue(gameMenu);

            int currentTab =
                currentValue is int value ? value : 0;

            if (pagesValue is System.Collections.IList pages
                && currentTab >= 0
                && currentTab < pages.Count
                && pages[currentTab] is IClickableMenu page)
            {
                return page;
            }
        }
        catch
        {
        }

        return null;
    }

    private static void EnsureNativeTabsPresentOnce(
        GameMenu gameMenu,
        IClickableMenu page,
        List<ClickableComponent> pageComponents)
    {
        List<ClickableComponent> native =
            TryGetNativeGameMenuTabs(
                gameMenu,
                out _
            );

        HashSet<int> nativeIds =
            native
                .Where(p => p.myID >= 0)
                .Select(p => p.myID)
                .ToHashSet();

        bool alreadyHasTabs =
            nativeIds.Count >= 3
            && nativeIds.Count(id =>
                pageComponents.Any(p => p.myID == id)
            ) >= Math.Min(3, nativeIds.Count);

        if (alreadyHasTabs)
            return;

        const System.Reflection.BindingFlags flags =
            System.Reflection.BindingFlags.Instance
            | System.Reflection.BindingFlags.Public
            | System.Reflection.BindingFlags.NonPublic;

        try
        {
            System.Reflection.MethodInfo? addTabs =
                gameMenu.GetType().GetMethod(
                    "AddTabsToClickableComponents",
                    flags
                );

            addTabs?.Invoke(
                gameMenu,
                new object[] { page }
            );
        }
        catch
        {
            // Page may already own its tabs or a menu mod may use another path.
        }
    }

    private static int CleanupDuplicateNativeTabs(
        GameMenu gameMenu,
        List<ClickableComponent> components)
    {
        List<ClickableComponent> native =
            TryGetNativeGameMenuTabs(
                gameMenu,
                out _
            );

        HashSet<int> nativeIds =
            native
                .Where(p => p.myID >= 0)
                .Select(p => p.myID)
                .ToHashSet();

        if (nativeIds.Count == 0)
            return 0;

        int removed = 0;

        foreach (int id in nativeIds)
        {
            List<ClickableComponent> duplicates =
                components
                    .Where(p =>
                        p.myID == id
                        && p.myID != BookTabId)
                    .ToList();

            if (duplicates.Count <= 1)
                continue;

            // Keep the component whose bounds are closest to the visible GameMenu
            // body/tab area. Old repeated inserts usually have identical bounds,
            // so this simply retains one and removes the rest.
            ClickableComponent keep =
                duplicates[0];

            foreach (ClickableComponent duplicate in duplicates.Skip(1))
            {
                if (components.Remove(duplicate))
                    removed++;
            }
        }

        return removed;
    }

    private void AttachToCurrentGameMenuPage(
        GameMenu menu,
        IClickableMenu graphOwner,
        List<ClickableComponent> components)
    {
        int w = 64;
        int h = 64;
        int gap = 10;

        int x = Math.Clamp(
            menu.xPositionOnScreen - w - gap,
            6,
            Game1.uiViewport.Width - w - 6
        );

        // Align the left Book rail with an opposite/right-side utility button
        // when such a component is visible in the page graph. If no right-side
        // utility exists, line it up with the first real content row instead of
        // leaving it too high near the native top tabs.
        int y = ResolveLeftRailY(
            menu,
            graphOwner,
            components,
            h
        );

        this.BookTab.bounds =
            new Rectangle(x, y, w, h);

        this.BookInsertedOnLeft = true;
        this.LayoutMode = "GameMenuPageGraphLeftRail";
        this.TabDetectionSource = "page-graph-left-rail";

        List<ClickableComponent> leftEdge =
            FindLeftEdgeComponents(
                graphOwner,
                components
            );

        // Default return target = the left-edge component vertically nearest
        // the Book. LEFT from ANY left edge still works via both neighbor IDs
        // and the direct input fallback.
        ClickableComponent? candidate =
            leftEdge
                .OrderBy(p => Math.Abs(
                    p.bounds.Center.Y
                    - this.BookTab.bounds.Center.Y
                ))
                .ThenBy(p => p.bounds.Center.X)
                .FirstOrDefault();

        if (candidate is not null)
        {
            this.LinkedNeighborId = candidate.myID;

            if (!this.LastReturnNeighborId.HasValue)
                this.LastReturnNeighborId = candidate.myID;

            this.BookTab.leftNeighborID = -1;
            this.BookTab.rightNeighborID =
                this.LastReturnNeighborId
                ?? candidate.myID;

            this.BookTab.upNeighborID =
                candidate.upNeighborID;

            this.BookTab.downNeighborID =
                candidate.downNeighborID;

            // Native SnappyMenus linkage for EVERY horizontal row's true
            // left-most component.
            foreach (ClickableComponent edge in leftEdge)
            {
                edge.leftNeighborID = BookTabId;
                edge.leftNeighborImmutable = true;
            }
        }
        else
        {
            this.LinkedNeighborId = null;
            this.LastReturnNeighborId = null;

            this.BookTab.leftNeighborID = -1;
            this.BookTab.rightNeighborID = -1;
        }

        if (!components.Contains(this.BookTab))
            components.Add(this.BookTab);
    }

    private static int ResolveLeftRailY(
        GameMenu menu,
        IClickableMenu graphOwner,
        List<ClickableComponent> components,
        int bookHeight)
    {
        // 1) Best case: mirror a square utility control outside the RIGHT edge
        // of the GameMenu body. This makes both side rails visually level.
        ClickableComponent? oppositeRail =
            components
                .Where(p =>
                    p.myID >= 0
                    && p.myID != BookTabId
                    && p.bounds.Width >= 44
                    && p.bounds.Width <= 88
                    && p.bounds.Height >= 44
                    && p.bounds.Height <= 88
                    && p.bounds.Center.X
                        > menu.xPositionOnScreen
                            + menu.width
                    && p.bounds.Center.X
                        <= menu.xPositionOnScreen
                            + menu.width
                            + 180
                    && p.bounds.Y
                        >= menu.yPositionOnScreen
                    && p.bounds.Y
                        <= menu.yPositionOnScreen
                            + menu.height)
                .OrderBy(p => p.bounds.Y)
                .FirstOrDefault();

        if (oppositeRail is not null)
        {
            return Math.Clamp(
                oppositeRail.bounds.Center.Y
                    - bookHeight / 2,
                6,
                Game1.uiViewport.Height
                    - bookHeight
                    - 6
            );
        }

        // 2) Inventory-style fallback: use the first content row inside the
        // menu body. This is deliberately lower than the native top tabs and
        // matches the visual height of common right-side extension buttons.
        List<ClickableComponent> interior =
            components
                .Where(p =>
                    p.myID >= 0
                    && p.myID != BookTabId
                    && p.bounds.Width >= 40
                    && p.bounds.Width <= 96
                    && p.bounds.Height >= 40
                    && p.bounds.Height <= 96
                    && p.bounds.Center.X
                        >= menu.xPositionOnScreen
                    && p.bounds.Center.X
                        <= menu.xPositionOnScreen
                            + menu.width
                    && p.bounds.Center.Y
                        >= menu.yPositionOnScreen
                            + 72)
                .OrderBy(p => p.bounds.Center.Y)
                .ThenBy(p => p.bounds.Center.X)
                .ToList();

        if (interior.Count > 0)
        {
            int firstRowCenterY =
                interior[0].bounds.Center.Y;

            return Math.Clamp(
                firstRowCenterY
                    - bookHeight / 2,
                6,
                Game1.uiViewport.Height
                    - bookHeight
                    - 6
            );
        }

        // 3) Generic fallback: a little lower than alpha.22.
        return Math.Clamp(
            menu.yPositionOnScreen + 92,
            6,
            Game1.uiViewport.Height
                - bookHeight
                - 6
        );
    }

    private List<ClickableComponent> FindLiveGameMenuTabs(
        GameMenu menu,
        List<ClickableComponent> pageComponents,
        out string source)
    {
        // First use native tab IDs, but resolve them back into the CURRENT PAGE
        // clickable list. This preserves IDs while taking the live/moved bounds
        // used by UI mods.
        List<ClickableComponent> native =
            TryGetNativeGameMenuTabs(
                menu,
                out string nativeSource
            );

        HashSet<int> nativeIds =
            native
                .Where(p => p.myID >= 0)
                .Select(p => p.myID)
                .ToHashSet();

        List<ClickableComponent> liveById =
            pageComponents
                .Where(p =>
                    p.myID >= 0
                    && p.myID != BookTabId
                    && nativeIds.Contains(p.myID)
                    && IsPlausibleTab(p))
                .OrderBy(p => p.bounds.Center.X)
                .ToList();

        if (liveById.Count >= 3)
        {
            source =
                $"page-graph+{nativeSource}";
            return liveById;
        }

        // Geometry fallback is now run against the CURRENT PAGE graph,
        // which is where GameMenu's tab controls actually live for snapping.
        List<ClickableComponent> visible =
            FindVisibleTabRun(
                menu,
                pageComponents
            );

        if (visible.Count >= 3)
        {
            source = "page-graph-visible";
            return visible;
        }

        source = "page-graph-none";
        return new List<ClickableComponent>();
    }

    private static List<ClickableComponent> TryGetNativeGameMenuTabs(
        GameMenu menu,
        out string source)
    {
        const System.Reflection.BindingFlags flags =
            System.Reflection.BindingFlags.Instance
            | System.Reflection.BindingFlags.Public
            | System.Reflection.BindingFlags.NonPublic;

        source = "none";
        Type type = menu.GetType();

        try
        {
            System.Reflection.FieldInfo? exactField =
                type.GetField("tabs", flags);

            if (exactField is not null)
            {
                List<ClickableComponent> result =
                    ExtractClickableComponents(
                        exactField.GetValue(menu)
                    );

                if (result.Count >= 3)
                {
                    source = $"field:{exactField.Name}";
                    return result;
                }
            }
        }
        catch
        {
        }

        try
        {
            System.Reflection.PropertyInfo? exactProperty =
                type.GetProperty("tabs", flags);

            if (exactProperty is not null
                && exactProperty.GetIndexParameters().Length == 0)
            {
                List<ClickableComponent> result =
                    ExtractClickableComponents(
                        exactProperty.GetValue(menu)
                    );

                if (result.Count >= 3)
                {
                    source =
                        $"property:{exactProperty.Name}";
                    return result;
                }
            }
        }
        catch
        {
        }

        return new List<ClickableComponent>();
    }

    private static List<ClickableComponent> ExtractClickableComponents(
        object? value)
    {
        if (value is null)
            return new List<ClickableComponent>();

        if (value is IEnumerable<ClickableComponent> typed)
        {
            return typed
                .Where(p =>
                    p is not null
                    && p.myID != BookTabId)
                .ToList();
        }

        if (value is System.Collections.IEnumerable enumerable)
        {
            List<ClickableComponent> result = new();

            foreach (object? item in enumerable)
            {
                if (item is ClickableComponent component
                    && component.myID != BookTabId)
                {
                    result.Add(component);
                }
            }

            return result;
        }

        return new List<ClickableComponent>();
    }

    private static List<ClickableComponent> FindVisibleTabRun(
        IClickableMenu menu,
        List<ClickableComponent> components)
    {
        int expectedCenterY =
            menu.yPositionOnScreen - 34;

        int minCenterY =
            menu.yPositionOnScreen - 110;

        int maxCenterY =
            menu.yPositionOnScreen + 24;

        List<ClickableComponent> candidates =
            components
                .Where(p =>
                    p.myID >= 0
                    && p.myID != BookTabId
                    && IsPlausibleTab(p)
                    && p.bounds.Center.Y >= minCenterY
                    && p.bounds.Center.Y <= maxCenterY
                    && p.bounds.Center.X
                        >= menu.xPositionOnScreen - 180
                    && p.bounds.Center.X
                        <= menu.xPositionOnScreen
                            + menu.width
                            + 180)
                .ToList();

        if (candidates.Count < 3)
            return new List<ClickableComponent>();

        List<List<ClickableComponent>> runs = new();

        foreach (List<ClickableComponent> row in candidates
            .GroupBy(
                p => (int)Math.Round(
                    p.bounds.Center.Y / 10d
                )
            )
            .Select(
                g => g
                    .OrderBy(p => p.bounds.Center.X)
                    .ToList()
            )
            .Where(g => g.Count >= 3))
        {
            List<ClickableComponent> current = new();

            foreach (ClickableComponent component in row)
            {
                if (current.Count == 0)
                {
                    current.Add(component);
                    continue;
                }

                ClickableComponent previous =
                    current[^1];

                int gap =
                    component.bounds.X
                    - previous.bounds.Right;

                if (gap <= 32)
                {
                    current.Add(component);
                }
                else
                {
                    if (current.Count >= 3)
                        runs.Add(current);

                    current =
                        new List<ClickableComponent>
                        {
                            component
                        };
                }
            }

            if (current.Count >= 3)
                runs.Add(current);
        }

        if (runs.Count == 0)
            return new List<ClickableComponent>();

        return runs
            .OrderByDescending(r => r.Count)
            .ThenBy(
                r => Math.Abs(
                    r.Average(
                        p => p.bounds.Center.Y
                    )
                    - expectedCenterY
                )
            )
            .ThenBy(AverageGap)
            .First()
            .OrderBy(p => p.bounds.Center.X)
            .ToList();
    }

    private void AttachBodyAnchorWithGraph(
        GameMenu menu,
        IClickableMenu graphOwner,
        List<ClickableComponent> components)
    {
        int w = 64;
        int h = 64;

        this.BookTab.bounds = new Rectangle(
            Math.Clamp(
                menu.xPositionOnScreen + 2,
                6,
                Game1.uiViewport.Width - w - 6
            ),
            Math.Clamp(
                menu.yPositionOnScreen - h + 2,
                6,
                Game1.uiViewport.Height - h - 6
            ),
            w,
            h
        );

        this.BookInsertedOnLeft = true;
        this.LayoutMode = "GameMenuPageBodyAnchor";
        this.TabDetectionSource = "page-body-anchor";

        int expectedY =
            menu.yPositionOnScreen - h / 2;

        ClickableComponent? candidate =
            components
                .Where(p =>
                    p.myID >= 0
                    && p.myID != BookTabId
                    && IsPlausibleTab(p))
                .OrderBy(
                    p => Math.Abs(
                        p.bounds.Center.Y - expectedY
                    )
                )
                .ThenBy(p => p.bounds.Center.X)
                .FirstOrDefault();

        if (candidate is not null)
        {
            this.LinkedNeighborId = candidate.myID;

            this.BookTab.leftNeighborID = -1;
            this.BookTab.rightNeighborID =
                candidate.myID;

            candidate.leftNeighborID =
                BookTabId;
        }
        else
        {
            this.LinkedNeighborId = null;
        }

        if (!components.Contains(this.BookTab))
            components.Add(this.BookTab);
    }

    private void AttachBodyAnchorWithoutGraph(
        GameMenu menu)
    {
        int w = 64;
        int h = 64;

        this.BookTab.bounds = new Rectangle(
            Math.Clamp(
                menu.xPositionOnScreen + 2,
                6,
                Game1.uiViewport.Width - w - 6
            ),
            Math.Clamp(
                menu.yPositionOnScreen - h + 2,
                6,
                Game1.uiViewport.Height - h - 6
            ),
            w,
            h
        );

        this.BookInsertedOnLeft = true;
        this.LinkedNeighborId = null;
        this.LayoutMode = "GameMenuNoPageGraph";
        this.TabDetectionSource = "no-page-graph";
    }

    private void AttachToItemGrabTop(
        IClickableMenu menu,
        IClickableMenu graphOwner,
        List<ClickableComponent> components)
    {
        List<ClickableComponent> valid =
            components
                .Where(p =>
                    p.myID >= 0
                    && p.myID != BookTabId
                    && p.bounds.Width > 0
                    && p.bounds.Height > 0)
                .ToList();

        int w = 64;
        int h = 64;

        ClickableComponent? candidate =
            valid
                .OrderBy(p => p.bounds.Center.Y)
                .ThenBy(p => p.bounds.Center.X)
                .FirstOrDefault();

        if (candidate is not null)
        {
            int x = Math.Clamp(
                candidate.bounds.X,
                8,
                Game1.uiViewport.Width - w - 8
            );

            int y = Math.Clamp(
                candidate.bounds.Y - h - 6,
                8,
                Game1.uiViewport.Height - h - 8
            );

            this.BookTab.bounds =
                new Rectangle(x, y, w, h);

            this.LinkedNeighborId =
                candidate.myID;

            this.BookInsertedOnLeft = false;

            this.BookTab.leftNeighborID =
                candidate.leftNeighborID;

            this.BookTab.rightNeighborID =
                candidate.rightNeighborID;

            this.BookTab.upNeighborID = -1;
            this.BookTab.downNeighborID =
                candidate.myID;

            candidate.upNeighborID =
                BookTabId;

            this.LayoutMode = "ItemGrabGraphTop";
            this.TabDetectionSource =
                graphOwner.GetType().Name;
        }
        else
        {
            AttachDetachedTop(menu);
        }
    }

    private void AttachDetachedTop(
        IClickableMenu menu)
    {
        int w = 64;
        int h = 64;

        this.BookTab.bounds =
            new Rectangle(
                Math.Clamp(
                    menu.xPositionOnScreen + 18,
                    8,
                    Game1.uiViewport.Width - w - 8
                ),
                Math.Clamp(
                    menu.yPositionOnScreen - h - 8,
                    8,
                    Game1.uiViewport.Height - h - 8
                ),
                w,
                h
            );

        this.LinkedNeighborId = null;
        this.BookInsertedOnLeft = false;
        this.LayoutMode = "DetachedTop";
        this.TabDetectionSource = "no-graph";
    }

    internal bool TryHandleMovementKey(
        IClickableMenu graphOwner,
        int direction)
    {
        IClickableMenu? active = Game1.activeClickableMenu;
        if (active is not GameMenu gameMenu
            || !this.Save.Data.BinderUnlocked)
        {
            return false;
        }

        IClickableMenu? expectedOwner =
            GetGraphOwner(gameMenu);

        if (expectedOwner is null
            || !ReferenceEquals(expectedOwner, graphOwner))
        {
            return false;
        }

        EnsureAttached(gameMenu);

        int? currentId =
            graphOwner.currentlySnappedComponent?.myID;

        // Stardew movement directions:
        // 0 = up, 1 = right, 2 = down, 3 = left.
        //
        // This hook sits BELOW SMAPI ButtonPressed and catches D-pad,
        // keyboard arrows, and analog-stick navigation through the same
        // IClickableMenu.applyMovementKey path.
        if (currentId == BookTabId && direction == 1)
        {
            FocusReturnComponent(graphOwner);
            return true;
        }

        if (currentId != BookTabId
            && direction == 3
            && (
                IsLeftEdgeComponent(graphOwner, currentId)
                || CurrentComponentPointsToBook(
                    graphOwner,
                    currentId
                )
            ))
        {
            this.LastReturnNeighborId = currentId;
            this.BookTab.rightNeighborID =
                currentId ?? -1;
            this.BookTab.rightNeighborImmutable = true;

            FocusBook(graphOwner);
            return true;
        }

        return false;
    }

    private void FocusBook(
        IClickableMenu graphOwner)
    {
        graphOwner.currentlySnappedComponent =
            this.BookTab;

        this.BookFocusWasActive = false;
        this.PendingBookCursorFrames = 3;
        this.PendingReturnCursorFrames = 0;
        this.PendingReturnTargetId = null;

        graphOwner.snapCursorToCurrentSnappedComponent();
    }

    private void FocusReturnComponent(
        IClickableMenu graphOwner)
    {
        int? targetId =
            this.LastReturnNeighborId
            ?? this.LinkedNeighborId;

        if (!targetId.HasValue
            || graphOwner.allClickableComponents is null)
        {
            return;
        }

        ClickableComponent? target =
            graphOwner.allClickableComponents
                .FirstOrDefault(
                    p => p.myID
                        == targetId.Value
                );

        if (target is null)
            return;

        graphOwner.currentlySnappedComponent =
            target;

        this.BookFocusWasActive = false;
        this.PendingBookCursorFrames = 0;

        // Mirror LEFT -> Book behavior: keep the exact previous component
        // focused for a few frames so the page can't push the hand outside.
        this.PendingReturnTargetId = target.myID;
        this.PendingReturnCursorFrames = 3;

        graphOwner.snapCursorToCurrentSnappedComponent();
    }

    private static bool CurrentComponentPointsToBook(
        IClickableMenu graphOwner,
        int? currentId)
    {
        if (!currentId.HasValue
            || graphOwner.allClickableComponents is null)
        {
            return false;
        }

        ClickableComponent? current =
            graphOwner.allClickableComponents
                .FirstOrDefault(
                    p => p.myID == currentId.Value
                );

        return current?.leftNeighborID == BookTabId;
    }

    private static bool IsLeftEdgeComponent(
        IClickableMenu graphOwner,
        int? currentId)
    {
        if (!currentId.HasValue
            || graphOwner.allClickableComponents is null)
        {
            return false;
        }

        return FindLeftEdgeComponents(
                graphOwner,
                graphOwner.allClickableComponents
            )
            .Any(
                p => p.myID
                    == currentId.Value
            );
    }

    private static List<ClickableComponent> FindLeftEdgeComponents(
        IClickableMenu graphOwner,
        List<ClickableComponent> components)
    {
        Rectangle viewport =
            new(
                0,
                0,
                Game1.uiViewport.Width,
                Game1.uiViewport.Height
            );

        List<ClickableComponent> valid =
            components
                .Where(p =>
                    p.myID >= 0
                    && p.myID != BookTabId
                    && p.bounds.Width >= 28
                    && p.bounds.Width <= 120
                    && p.bounds.Height >= 28
                    && p.bounds.Height <= 120
                    && viewport.Intersects(p.bounds)
                    && p.bounds.Center.X
                        >= graphOwner.xPositionOnScreen - 24
                    && p.bounds.Center.X
                        <= graphOwner.xPositionOnScreen
                            + graphOwner.width
                            + 24
                    && p.bounds.Center.Y
                        >= graphOwner.yPositionOnScreen - 100
                    && p.bounds.Center.Y
                        <= graphOwner.yPositionOnScreen
                            + graphOwner.height
                            + 24)
                .GroupBy(p => new
                {
                    p.myID,
                    X = p.bounds.X,
                    Y = p.bounds.Y,
                    W = p.bounds.Width,
                    H = p.bounds.Height
                })
                .Select(g => g.First())
                .ToList();

        if (valid.Count == 0)
            return new List<ClickableComponent>();

        List<ClickableComponent> result = new();

        foreach (List<ClickableComponent> row in valid
            .GroupBy(
                p => (int)Math.Round(
                    p.bounds.Center.Y / 12d
                )
            )
            .Select(
                g => g
                    .OrderBy(p => p.bounds.Center.X)
                    .ToList()
            ))
        {
            if (row.Count == 0)
                continue;

            result.Add(row[0]);
        }

        return result
            .GroupBy(p => p.myID)
            .Select(g => g.First())
            .OrderBy(p => p.bounds.Center.Y)
            .ToList();
    }

    private static bool IsControllerLeft(
        SButton button)
    {
        string name = button.ToString();

        return
            name.Equals(
                "ControllerDPadLeft",
                StringComparison.OrdinalIgnoreCase
            )
            || name.Equals(
                "ControllerLeftStickLeft",
                StringComparison.OrdinalIgnoreCase
            )
            || name.Equals(
                "ControllerThumbstickLeft",
                StringComparison.OrdinalIgnoreCase
            )
            || name.Equals(
                "ControllerLeftShoulder",
                StringComparison.OrdinalIgnoreCase
            )
            || name.Equals(
                "ControllerLeftTrigger",
                StringComparison.OrdinalIgnoreCase
            );
    }

    private static bool IsControllerRight(
        SButton button)
    {
        string name = button.ToString();

        return
            name.Equals(
                "ControllerDPadRight",
                StringComparison.OrdinalIgnoreCase
            )
            || name.Equals(
                "ControllerLeftStickRight",
                StringComparison.OrdinalIgnoreCase
            )
            || name.Equals(
                "ControllerThumbstickRight",
                StringComparison.OrdinalIgnoreCase
            )
            || name.Equals(
                "ControllerRightShoulder",
                StringComparison.OrdinalIgnoreCase
            )
            || name.Equals(
                "ControllerRightTrigger",
                StringComparison.OrdinalIgnoreCase
            );
    }

    private static bool IsPlausibleTab(
        ClickableComponent component)
        => component.bounds.Width >= 44
            && component.bounds.Width <= 96
            && component.bounds.Height >= 44
            && component.bounds.Height <= 96
            && Math.Abs(
                component.bounds.Width
                - component.bounds.Height
            ) <= 24;

    private static double AverageGap(
        List<ClickableComponent> run)
    {
        if (run.Count < 2)
            return double.MaxValue;

        double total = 0;

        for (int i = 1; i < run.Count; i++)
        {
            total += Math.Abs(
                run[i].bounds.X
                - run[i - 1].bounds.Right
            );
        }

        return total / (run.Count - 1);
    }

    private void DrawTab(
        SpriteBatch b,
        IClickableMenu graphOwner)
    {
        bool focused =
            graphOwner.currentlySnappedComponent?.myID
            == BookTabId;

        Point cursor =
            CardchaUi.GetUiMousePoint();

        bool hovered =
            this.BookTab.bounds.Contains(
                cursor.X,
                cursor.Y
            );

        Rectangle r =
            this.BookTab.bounds;

        Rectangle shadow =
            new(
                r.X + 3,
                r.Y + 4,
                r.Width,
                r.Height
            );

        b.Draw(
            Game1.staminaRect,
            shadow,
            new Color(83, 49, 35) * 0.55f
        );

        Color outer =
            focused || hovered
                ? new Color(255, 198, 82)
                : new Color(183, 103, 47);

        Color inner =
            focused || hovered
                ? new Color(255, 239, 199)
                : new Color(247, 218, 171);

        b.Draw(
            Game1.staminaRect,
            r,
            outer
        );

        CardchaUi.DrawBorder(
            b,
            r,
            focused
                ? Color.White
                : new Color(111, 63, 38),
            focused ? 4 : 3
        );

        Rectangle face =
            new(
                r.X + 7,
                r.Y + 7,
                r.Width - 14,
                r.Height - 14
            );

        b.Draw(
            Game1.staminaRect,
            face,
            inner
        );

        CardchaUi.DrawBorder(
            b,
            face,
            new Color(205, 143, 77),
            2
        );

        if (!this.BinderTabIconChecked)
        {
            this.BinderTabIconChecked = true;
            try
            {
                // PNG is the reliable runtime asset path for SMAPI/XNA. Keep the JPG in the
                // package as the original source/reference, but prefer the PNG so the Book
                // tab never turns into a blank square on systems that reject JPG texture loads.
                this.BinderTabIcon = this.Helper.ModContent.Load<Texture2D>("assets/binder_tab_icon.png");
            }
            catch
            {
                try
                {
                    this.BinderTabIcon = this.Helper.ModContent.Load<Texture2D>("assets/binder_tab_icon.jpg");
                }
                catch
                {
                    this.BinderTabIcon = null;
                }
            }
        }

        if (this.BinderTabIcon is not null)
        {
            Rectangle icon = new(face.X + 2, face.Y + 2, face.Width - 4, face.Height - 4);
            b.Draw(
                this.BinderTabIcon,
                icon,
                new Rectangle(0, 0, this.BinderTabIcon.Width, this.BinderTabIcon.Height),
                Color.White
            );
            if (hovered)
                DrawTooltip(b, ModEntry.T("booktab.tooltip"));
            return;
        }

        int cx = face.Center.X;
        int cy = face.Center.Y;

        int pageW =
            Math.Max(12, face.Width / 3);

        int pageH =
            Math.Max(22, face.Height - 18);

        Rectangle leftPage =
            new(
                cx - pageW - 2,
                cy - pageH / 2,
                pageW,
                pageH
            );

        Rectangle rightPage =
            new(
                cx + 2,
                cy - pageH / 2,
                pageW,
                pageH
            );

        b.Draw(
            Game1.staminaRect,
            leftPage,
            new Color(255, 246, 215)
        );

        b.Draw(
            Game1.staminaRect,
            rightPage,
            new Color(255, 246, 215)
        );

        CardchaUi.DrawBorder(
            b,
            leftPage,
            new Color(108, 67, 48),
            2
        );

        CardchaUi.DrawBorder(
            b,
            rightPage,
            new Color(108, 67, 48),
            2
        );

        b.Draw(
            Game1.staminaRect,
            new Rectangle(
                cx - 1,
                cy - pageH / 2 - 1,
                2,
                pageH + 2
            ),
            new Color(118, 66, 46)
        );

        b.Draw(
            Game1.staminaRect,
            new Rectangle(
                cx + pageW / 2,
                cy + pageH / 4,
                5,
                Math.Max(8, pageH / 3)
            ),
            new Color(164, 52, 45)
        );

        if (hovered)
            DrawTooltip(
                b,
                ModEntry.T("booktab.tooltip")
            );
    }

    private void DrawTooltip(
        SpriteBatch b,
        string text)
    {
        Point cursor =
            CardchaUi.GetUiMousePoint();

        Vector2 size =
            Game1.smallFont.MeasureString(text);

        int pad = 8;

        int x = Math.Min(
            cursor.X + 16,
            Game1.uiViewport.Width
                - (int)size.X
                - pad * 2
                - 8
        );

        int y = Math.Max(
            8,
            cursor.Y
                - (int)size.Y
                - pad * 2
                - 10
        );

        Rectangle box =
            new(
                x,
                y,
                (int)size.X + pad * 2,
                (int)size.Y + pad * 2
            );

        b.Draw(
            Game1.staminaRect,
            box,
            new Color(45, 35, 31) * 0.96f
        );

        CardchaUi.DrawBorder(
            b,
            box,
            CardchaUi.Gold,
            2
        );

        b.DrawString(
            Game1.smallFont,
            text,
            new Vector2(
                box.X + pad,
                box.Y + pad
            ),
            Color.White
        );
    }
}
