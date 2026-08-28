using Cardcha.Services;
using Cardcha.UI;
using HarmonyLib;
using Microsoft.Xna.Framework.Input;
using StardewValley;
using StardewValley.Menus;
using System.Reflection;
using System.Runtime.CompilerServices;

namespace Cardcha.Patches;

/// <summary>
/// alpha26.5.2 controller compatibility hotfix.
/// Some Steam Input/native controller layouts send a face-button action which is not the
/// button resolved by ControllerProfileService.IsConfirm. While the reveal detail overlay is
/// open, treat any face button as the same one-button select/click action used by the mouse.
/// </summary>
internal static class RevealControllerOneButtonRuntimePatch
{
    private const double DebounceMs = 180d;
    private static readonly FieldInfo SelectedField = AccessTools.Field(typeof(CardchaRevealMenu), "SelectedResultIndex");
    private static readonly FieldInfo LastDetailField = AccessTools.Field(typeof(CardchaRevealMenu), "LastDetailResultIndex");
    private static readonly FieldInfo DetailOpenedField = AccessTools.Field(typeof(CardchaRevealMenu), "DetailOpenedAtMs");
    private static readonly FieldInfo ResultButtonsField = AccessTools.Field(typeof(CardchaRevealMenu), "ResultButtons");
    private static readonly FieldInfo ControllerField = AccessTools.Field(typeof(CardchaRevealMenu), "Controller");

    [ModuleInitializer]
    internal static void Initialize()
    {
        MethodInfo? target = AccessTools.Method(typeof(CardchaRevealMenu), nameof(CardchaRevealMenu.receiveGamePadButton));
        if (target is null)
            return;

        new Harmony("ronvotri.cardcha.reveal-one-button-alpha2652").Patch(
            target,
            prefix: new HarmonyMethod(typeof(RevealControllerOneButtonRuntimePatch), nameof(Prefix))
        );
    }

    private static bool Prefix(CardchaRevealMenu __instance, Buttons b)
    {
        int selected = (int)(SelectedField.GetValue(__instance) ?? -1);
        if (selected < 0)
            return true;

        ControllerProfileService? controller = ControllerField.GetValue(__instance) as ControllerProfileService;
        bool faceButton = b is Buttons.A or Buttons.B or Buttons.X or Buttons.Y;
        bool selectLike = faceButton || (controller?.IsConfirm(b) ?? false);

        // Keep the detail overlay modal for directions/shoulders/sticks. The player closes it
        // with the same physical face/select button, then navigates to another card.
        if (!selectLike)
            return false;

        double openedAt = (double)(DetailOpenedField.GetValue(__instance) ?? -10000d);
        if (Environment.TickCount64 - openedAt < DebounceMs)
            return false;

        LastDetailField.SetValue(__instance, selected);
        SelectedField.SetValue(__instance, -1);

        if (ResultButtonsField.GetValue(__instance) is List<ClickableComponent> buttons
            && selected >= 0 && selected < buttons.Count)
        {
            __instance.currentlySnappedComponent = buttons[selected];
            if (Game1.options.SnappyMenus)
                __instance.snapCursorToCurrentSnappedComponent();
        }

        Game1.playSound("bigDeSelect");
        return false;
    }
}
