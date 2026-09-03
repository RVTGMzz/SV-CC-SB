using System.Reflection;
using System.Runtime.CompilerServices;
using Cardcha.Models;
using Cardcha.Services;
using HarmonyLib;
using StardewModdingAPI;
using StardewValley;

namespace Cardcha.Patches;

/// <summary>
/// TEST-only convenience command for fast balancing/visual verification.
/// One command unlocks and maxes all 76 active cards plus all four ChaCha Support Cast modules.
/// It deliberately does not change story progression, Airship progression, money, dust, or equipment.
/// </summary>
internal static class DebugMaxAllCommandPatch
{
    private const string CommandName = "cardcha_max_all";

    private static readonly HashSet<string> HiddenLegacyCards = new(StringComparer.OrdinalIgnoreCase)
    {
        "endless_hunt",
        "fate_weaver",
        "immortal_echo",
        "worldbreaker"
    };

    [ModuleInitializer]
    internal static void Initialize()
    {
        Harmony harmony = new("Ronvotri.Cardcha.DebugMaxAllCommand");
        MethodInfo? entry = AccessTools.Method(typeof(ModEntry), nameof(ModEntry.Entry), new[] { typeof(IModHelper) });
        MethodInfo? postfix = AccessTools.Method(typeof(DebugMaxAllCommandPatch), nameof(AfterEntry));
        if (entry is not null && postfix is not null)
            harmony.Patch(entry, postfix: new HarmonyMethod(postfix));
    }

    private static void AfterEntry(ModEntry __instance, IModHelper helper)
    {
        helper.ConsoleCommands.Add(
            CommandName,
            "TEST ONLY: unlock + max all 76 active Cardcha cards and all four ChaCha skills.",
            (_, _) => Run(__instance)
        );
    }

    private static void Run(ModEntry instance)
    {
        if (!Context.IsWorldReady)
        {
            ModEntry.StaticMonitor?.Log("Load a save before using cardcha_max_all.", LogLevel.Warn);
            return;
        }

        SaveService? save = GetField<SaveService>(instance, "Save");
        CardRegistry? cards = GetField<CardRegistry>(instance, "Cards");
        CardUpgradeService? upgrades = GetField<CardUpgradeService>(instance, "Upgrades");
        if (save is null || cards is null || upgrades is null)
        {
            ModEntry.StaticMonitor?.Log("cardcha_max_all couldn't resolve Cardcha runtime services.", LogLevel.Error);
            return;
        }

        int cardCount = 0;
        foreach (CardDefinition card in cards.All)
        {
            if (string.IsNullOrWhiteSpace(card.Id) || HiddenLegacyCards.Contains(card.Id))
                continue;

            save.Data.OwnedCards.Add(card.Id);
            save.Data.CardLevels[card.Id] = upgrades.GetMaxLevel(card);
            save.Data.CardCopies[card.Id] = 0;
            cardCount++;
        }

        foreach (string skillId in ChaChaSkillService.SkillIds)
        {
            save.Data.ChaChaSkillsFound.Add(skillId);
            save.Data.ChaChaSkillLevels[skillId] = ChaChaSkillService.MaxSkillLevel;
        }

        if (string.IsNullOrWhiteSpace(save.Data.ActiveChaChaSkillId))
            save.Data.ActiveChaChaSkillId = ChaChaSkillService.VitalSkillId;

        save.Save();

        string progressionNote = !save.Data.BinderUnlocked || !save.Data.ChaChaLoaned
            ? " Progression flags were NOT changed; unlock Binder/ChaCha normally if they are not available yet."
            : string.Empty;

        ModEntry.StaticMonitor?.Log(
            $"TEST MAX complete: Cards={cardCount}/{CardRegistry.TargetBaseSetCount} at individual max stars; ChaCha=4/4 at Lv {ChaChaSkillService.MaxSkillLevel}.{progressionNote}",
            LogLevel.Alert
        );
    }

    private static T? GetField<T>(ModEntry instance, string fieldName) where T : class
        => AccessTools.Field(typeof(ModEntry), fieldName)?.GetValue(instance) as T;
}
