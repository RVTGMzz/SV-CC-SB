from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
TARGET = '0.3.0-alpha.27.0.7.8.6'


def set_versions() -> None:
    pattern = r'0\.3\.0-alpha\.27\.0\.7\.8\.\d+'
    for rel in ['Cardcha.csproj', 'Directory.Build.targets', 'ModEntry.cs']:
        path = ROOT / rel
        text = path.read_text()
        text, count = re.subn(pattern, TARGET, text)
        if count == 0 and TARGET not in text:
            raise AssertionError(f'Could not update version in {rel}')
        path.write_text(text)

    manifest = ROOT / 'manifest.json'
    data = json.loads(manifest.read_text())
    data['Version'] = TARGET
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def patch_item_asset_service() -> None:
    path = ROOT / 'Services/ItemAssetService.cs'
    text = path.read_text()

    old = '''                data[CardchaMachineId] = new BigCraftableData
                {
                    Name = "Cardcha! Machine",
                    DisplayName = this.Helper.Translation.Get("machine.name").ToString(),
                    Description = this.Helper.Translation.Get("machine.desc").ToString(),
                    Texture = MachineTextureAsset,
                    SpriteIndex = 0,
                    Price = 0,
                    Fragility = 0,
                    CanBePlacedIndoors = false,
                    CanBePlacedOutdoors = false,
                    IsLamp = false,'''
    new = '''                data[CardchaMachineId] = new BigCraftableData
                {
                    Name = "Cardcha! Machine",
                    DisplayName = this.Helper.Translation.Get("machine.name").ToString(),
                    Description = this.Helper.Translation.Get("machine.desc").ToString(),
                    Texture = MachineTextureAsset,
                    SpriteIndex = 0,
                    Price = 0,
                    Fragility = 0,
                    CanBePlacedIndoors = true,
                    CanBePlacedOutdoors = false,
                    IsLamp = false,'''

    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise AssertionError('Could not locate normal Cardcha Machine placement block')

    portable_anchor = '''                data[PortableMachineId] = new BigCraftableData'''
    if portable_anchor not in text:
        raise AssertionError('Portable machine block missing')
    portable = text[text.index(portable_anchor):]
    if 'CanBePlacedIndoors = false' not in portable or 'CanBePlacedOutdoors = false' not in portable:
        raise AssertionError('Portable machine must remain non-placeable')

    path.write_text(text)


def patch_machine_interaction() -> None:
    path = ROOT / 'Patches/MachineInteractionPatch.cs'
    text = path.read_text()

    text = text.replace(
        '''        // The story Machine is a menu key / home appliance entitlement, not a placeable
        // big-craftable. Returning false here also prevents Stardew from drawing the green
        // placement ghost while the player is holding it.''',
        '''        // Only the portable Cardcha machine is a handheld menu key and must never enter
        // Stardew's placement flow. The normal Cardcha Machine remains a real indoor big-craftable.'''
    )

    old = '''    private static void IsPlaceablePostfix(SObject __instance, ref bool __result)
    {
        if (__result && IsCardchaMachine(__instance))
            __result = false;
    }'''
    new = '''    private static void IsPlaceablePostfix(SObject __instance, ref bool __result)
    {
        if (ItemAssetService.IsPortableMachine(__instance))
            __result = false;
    }'''

    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise AssertionError('Could not locate machine isPlaceable postfix')

    path.write_text(text)


def validate() -> None:
    item = (ROOT / 'Services/ItemAssetService.cs').read_text()
    patch = (ROOT / 'Patches/MachineInteractionPatch.cs').read_text()

    normal_start = item.index('data[CardchaMachineId] = new BigCraftableData')
    portable_start = item.index('data[PortableMachineId] = new BigCraftableData')
    normal = item[normal_start:portable_start]
    portable = item[portable_start:]

    assert 'CanBePlacedIndoors = true' in normal
    assert 'CanBePlacedOutdoors = false' in normal
    assert 'CanBePlacedIndoors = false' in portable
    assert 'CanBePlacedOutdoors = false' in portable
    assert 'ItemAssetService.IsPortableMachine(__instance)' in patch
    assert 'if (__result && IsCardchaMachine(__instance))' not in patch
    assert 'public static bool IsCardchaMachine' in patch
    assert json.loads((ROOT / 'manifest.json').read_text())['Version'] == TARGET


def main() -> None:
    patch_item_asset_service()
    patch_machine_interaction()
    set_versions()
    validate()
    print('0.7.8.6 normal Cardcha Machine indoor placement restored; portable remains handheld-only')


if __name__ == '__main__':
    main()
