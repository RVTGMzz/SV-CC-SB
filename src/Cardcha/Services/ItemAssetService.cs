using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley.GameData.BigCraftables;
using StardewValley.GameData.Objects;

namespace Cardcha.Services;

internal sealed class ItemAssetService
{
    public const string TextureAsset = "Mods/Ronvotri.Cardcha/Items";
    public const string MachineTextureAsset = "Mods/Ronvotri.Cardcha/Machine";
    public const string MachineUiTextureAsset = "Mods/Ronvotri.Cardcha/MachineUi";
    public const string CardchaMachineId = "Ronvotri.Cardcha_Machine";
    public const string MachineMarkerKey = "Ronvotri.Cardcha/MachineInstance";
    public const string SuspiciousDustId = "Ronvotri.Cardcha_SuspiciousDust";

    private readonly IModHelper Helper;

    public ItemAssetService(IModHelper helper)
    {
        this.Helper = helper;
    }

    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)
    {
        if (e.Name.IsEquivalentTo(TextureAsset))
        {
            e.LoadFromModFile<Texture2D>("assets/items.png", AssetLoadPriority.Medium);
            return;
        }

        if (e.Name.IsEquivalentTo(MachineTextureAsset))
        {
            e.LoadFromModFile<Texture2D>("assets/machine.png", AssetLoadPriority.Medium);
            return;
        }

        if (e.Name.IsEquivalentTo(MachineUiTextureAsset))
        {
            e.LoadFromModFile<Texture2D>("assets/machine_ui.png", AssetLoadPriority.Medium);
            return;
        }

        if (e.NameWithoutLocale.IsEquivalentTo("Data/Objects"))
        {
            e.Edit(asset =>
            {
                var data = asset.AsDictionary<string, ObjectData>().Data;
                data[DropService.CardboardScrapId] = MakeObject(
                    this.Helper.Translation.Get("item.cardboard.name").ToString(),
                    this.Helper.Translation.Get("item.cardboard.desc").ToString(),
                    0
                );
                data[DropService.ShinyScrapId] = MakeObject(
                    this.Helper.Translation.Get("item.shiny.name").ToString(),
                    this.Helper.Translation.Get("item.shiny.desc").ToString(),
                    1
                );
                data[SuspiciousDustId] = MakeObject(
                    this.Helper.Translation.Get("item.dust.name").ToString(),
                    this.Helper.Translation.Get("item.dust.desc").ToString(),
                    2
                );
            });
            return;
        }


        if (e.NameWithoutLocale.IsEquivalentTo("Data/BigCraftables"))
        {
            e.Edit(asset =>
            {
                var data = asset.AsDictionary<string, BigCraftableData>().Data;
                data[CardchaMachineId] = new BigCraftableData
                {
                    Name = "Cardcha! Machine",
                    DisplayName = this.Helper.Translation.Get("machine.name").ToString(),
                    Description = this.Helper.Translation.Get("machine.desc").ToString(),
                    Texture = MachineTextureAsset,
                    SpriteIndex = 0,
                    Price = 0,
                    Fragility = 0,
                    CanBePlacedIndoors = true,
                    CanBePlacedOutdoors = true,
                    IsLamp = false,
                    CustomFields = new Dictionary<string, string>
                    {
                        ["Ronvotri.Cardcha/Machine"] = "true"
                    }
                };
            });
        }
    }

    private static ObjectData MakeObject(string name, string description, int spriteIndex)
        => new()
        {
            Name = name,
            DisplayName = name,
            Description = description,
            Type = "Basic",
            Category = 0,
            Price = 0,
            Texture = TextureAsset,
            SpriteIndex = spriteIndex,
            Edibility = -300
        };
}
