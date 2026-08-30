from pathlib import Path
import runpy

# Apply the main candidate first, then repair two compile-only issues found by canonical CI.
runpy.run_path('build_assets/apply_alpha28_sky_dock_interior_flight.py', run_name='__main__')

path = Path('src/Cardcha/Services/AirshipFoundationService.cs')
s = path.read_text(encoding='utf-8')

# C# doesn't allow a nested local to reuse a name that is declared later in the enclosing scope.
s = s.replace('''            Point action = GetActionTile();\n            Point route = ResolveSkyDockInteriorRouteTile(location);\n            Point exit = ResolveSkyDockInteriorExitTile(location);\n\n            if (Touches(action, route) || PlayerIsNear(route))''', '''            Point interiorAction = GetActionTile();\n            Point route = ResolveSkyDockInteriorRouteTile(location);\n            Point interiorExit = ResolveSkyDockInteriorExitTile(location);\n\n            if (Touches(interiorAction, route) || PlayerIsNear(route))''', 1)
s = s.replace('''            if (Touches(action, exit) || PlayerIsNear(exit))''', '''            if (Touches(interiorAction, interiorExit) || PlayerIsNear(interiorExit))''', 1)

# The first patch used call-site presence as its sentinel, so the resolver definitions were skipped.
if 'private static Point ResolveSkyDockInteriorArrivalTile' not in s:
    marker = '    private static Point ResolveDeckArrivalTile(GameLocation deck)\n'
    block = '''    private static Point ResolveSkyDockInteriorArrivalTile(GameLocation interior)\n    {\n        int width = interior.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30;\n        int height = interior.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;\n        return FindClearTileNear(interior, new Point(width / 2, Math.Max(2, height - 4)));\n    }\n\n    private static Point ResolveSkyDockInteriorExitTile(GameLocation interior)\n    {\n        int width = interior.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30;\n        int height = interior.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;\n        return new Point(width / 2, Math.Max(1, height - 2));\n    }\n\n    private static Point ResolveSkyDockInteriorRouteTile(GameLocation interior)\n    {\n        int width = interior.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30;\n        int height = interior.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;\n        return new Point(Math.Clamp(width / 3, 3, width - 4), Math.Clamp(7, 3, height - 5));\n    }\n\n    private static Point ResolveSkyDockInteriorBayTile(GameLocation interior)\n    {\n        int width = interior.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30;\n        int height = interior.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;\n        return new Point(Math.Clamp(width - 6, 4, width - 3), Math.Clamp(7, 3, height - 5));\n    }\n\n'''
    if marker not in s:
        raise RuntimeError('ResolveDeckArrivalTile marker missing')
    s = s.replace(marker, block + marker, 1)

path.write_text(s, encoding='utf-8')
print('alpha.28.0.3.0 Sky Dock interior compile fix1 applied')
