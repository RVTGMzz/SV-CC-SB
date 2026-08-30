using System.Reflection;
using System.Runtime.CompilerServices;
using HarmonyLib;
using StardewModdingAPI;
using StardewValley;

namespace Ronvotri.StardewSquadDialogueRecruit;

/// <summary>
/// Keeps recruitment reachable after Stardew Valley has exhausted an NPC's normal daily dialogue.
/// We deliberately do NOT reset NPC dialogue state or award extra friendship. If vanilla interaction
/// produces no menu, we open a neutral "..." dialogue shell; ModEntry's existing R/touch recruit hint
/// is then drawn over that shell exactly like it is over a normal conversation.
/// </summary>
internal static class DailyDialogueFallback
{
    private const string HarmonyId = "Ronvotri.StardewSquadDialogueRecruit.DailyDialogueFallback";
    private static readonly BindingFlags AnyStatic = BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic;
    private static readonly BindingFlags AnyInstance = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;

    private static FieldInfo? instanceField;
    private static MethodInfo? isRecruitedMethod;
    private static MethodInfo? isRecruitEligibleMethod;

    [ModuleInitializer]
    internal static void Initialize()
    {
        MethodInfo? checkAction = AccessTools.Method(
            typeof(NPC),
            nameof(NPC.checkAction),
            new[] { typeof(Farmer), typeof(GameLocation) }
        );

        if (checkAction is null)
            return;

        var harmony = new Harmony(HarmonyId);
        harmony.Patch(
            checkAction,
            postfix: new HarmonyMethod(typeof(DailyDialogueFallback), nameof(NpcCheckActionPostfix))
        );
    }

    private static void NpcCheckActionPostfix(NPC __instance, Farmer who, GameLocation l)
    {
        if (!Context.IsWorldReady
            || Game1.eventUp
            || Game1.isFestival()
            || Game1.activeClickableMenu is not null
            || !ReferenceEquals(who, Game1.player)
            || __instance.currentLocation != Game1.currentLocation)
        {
            return;
        }

        // Don't turn a failed gift/item interaction into a recruitment prompt.
        if (who.ActiveObject is not null)
            return;

        ModEntry? mod = GetModEntry();
        if (mod is null)
            return;

        try
        {
            bool recruited = InvokeBool(mod, ref isRecruitedMethod, "IsRecruited", __instance);
            if (recruited)
                return;

            bool eligible = InvokeBool(mod, ref isRecruitEligibleMethod, "IsRecruitEligible", __instance);
            if (!eligible)
                return;

            // This is intentionally only an interaction shell. It does not touch friendship,
            // dialogue queues, talk-to-NPC flags, or the NPC's normal per-day dialogue state.
            Game1.DrawDialogue(new Dialogue(__instance, null, "..."));
        }
        catch
        {
            // Fallback UI should never be able to break normal NPC interaction.
        }
    }

    private static ModEntry? GetModEntry()
    {
        instanceField ??= typeof(ModEntry).GetField("Instance", AnyStatic);
        return instanceField?.GetValue(null) as ModEntry;
    }

    private static bool InvokeBool(ModEntry mod, ref MethodInfo? cached, string name, NPC npc)
    {
        cached ??= typeof(ModEntry).GetMethod(name, AnyInstance, null, new[] { typeof(NPC) }, null);
        return cached?.Invoke(mod, new object?[] { npc }) as bool? ?? false;
    }
}
