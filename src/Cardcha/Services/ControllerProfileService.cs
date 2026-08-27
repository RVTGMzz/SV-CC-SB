using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Input;
using StardewModdingAPI;

namespace Cardcha.Services;

internal enum ControllerLayoutKind
{
    Xbox,
    Nintendo,
    PlayStation,
    Generic
}

internal enum ControllerAction
{
    Confirm,
    Favorite,
    Deselect,
    Exit,
    Skip
}

/// <summary>
/// Central controller semantic layer for every Cardcha menu.
/// Gameplay actions are described by intent (confirm/favorite/deselect/exit) instead of
/// scattering raw A/B/X/Y checks through individual menus.
/// </summary>
internal sealed class ControllerProfileService
{
    private readonly ModConfig Config;
    private readonly IMonitor Monitor;
    private string? LastIdentity;
    private ControllerLayoutKind? CachedAutoLayout;
    private bool LoggedAutoProfile;

    public ControllerProfileService(ModConfig config, IMonitor monitor)
    {
        this.Config = config;
        this.Monitor = monitor;
    }

    public ControllerLayoutKind Layout => this.ResolveLayout();

    public bool IsConfirm(Buttons button)
        => button == this.GetRawButton(ControllerAction.Confirm);

    public bool IsFavorite(Buttons button)
        => button == this.GetRawButton(ControllerAction.Favorite);

    public bool IsDeselect(Buttons button)
        => button == this.GetRawButton(ControllerAction.Deselect);

    public bool IsExit(Buttons button)
        => button == this.GetRawButton(ControllerAction.Exit);

    public bool IsSkip(Buttons button)
        => button == this.GetRawButton(ControllerAction.Skip);

    public string GetLabel(ControllerAction action)
    {
        ControllerLayoutKind layout = this.ResolveLayout();
        return layout switch
        {
            ControllerLayoutKind.Nintendo => action switch
            {
                ControllerAction.Confirm or ControllerAction.Skip => "B",
                ControllerAction.Favorite => "A",
                ControllerAction.Deselect => "Y",
                ControllerAction.Exit => "X",
                _ => "?"
            },
            ControllerLayoutKind.PlayStation => action switch
            {
                ControllerAction.Confirm or ControllerAction.Skip => "Cross",
                ControllerAction.Favorite => "Circle",
                ControllerAction.Deselect => "Square",
                ControllerAction.Exit => "Triangle",
                _ => "?"
            },
            ControllerLayoutKind.Generic => action switch
            {
                ControllerAction.Confirm or ControllerAction.Skip => "South",
                ControllerAction.Favorite => "East",
                ControllerAction.Deselect => "West",
                ControllerAction.Exit => "North",
                _ => "?"
            },
            _ => action switch
            {
                ControllerAction.Confirm or ControllerAction.Skip => "A",
                ControllerAction.Favorite => "B",
                ControllerAction.Deselect => "X",
                ControllerAction.Exit => "Y",
                _ => "?"
            }
        };
    }

    public string Describe()
        => $"Layout={this.ResolveLayout()} | Mapping={this.ResolveMappingMode()} | Identity={this.LastIdentity ?? "<unknown>"}";

    private Buttons GetRawButton(ControllerAction action)
    {
        string mapping = this.ResolveMappingMode();

        // Standard XInput/MonoGame positional order: A=south, B=east, X=west, Y=north.
        if (!mapping.Equals("NintendoNative", StringComparison.OrdinalIgnoreCase))
        {
            return action switch
            {
                ControllerAction.Confirm or ControllerAction.Skip => Buttons.A,
                ControllerAction.Favorite => Buttons.B,
                ControllerAction.Deselect => Buttons.X,
                ControllerAction.Exit => Buttons.Y,
                _ => Buttons.A
            };
        }

        // Some native Nintendo drivers preserve the printed labels instead of XInput positions.
        // In that mode B=south, A=east, Y=west, X=north.
        return action switch
        {
            ControllerAction.Confirm or ControllerAction.Skip => Buttons.B,
            ControllerAction.Favorite => Buttons.A,
            ControllerAction.Deselect => Buttons.Y,
            ControllerAction.Exit => Buttons.X,
            _ => Buttons.B
        };
    }

    private string ResolveMappingMode()
    {
        string configured = this.Config.ControllerMapping?.Trim() ?? "Auto";
        if (configured.Equals("Standard", StringComparison.OrdinalIgnoreCase))
            return "Standard";
        if (configured.Equals("NintendoNative", StringComparison.OrdinalIgnoreCase))
            return "NintendoNative";

        // Auto: only choose Nintendo-native label mapping when the runtime actually exposes
        // a Nintendo identity. Steam Input commonly hides the device as Xbox/XInput, in which
        // case Standard is the safe behavior.
        return this.ResolveLayout() == ControllerLayoutKind.Nintendo
            && this.IdentityLooksNintendo(this.LastIdentity)
                ? "NintendoNative"
                : "Standard";
    }

    private ControllerLayoutKind ResolveLayout()
    {
        string configured = this.Config.ControllerLayout?.Trim() ?? "Auto";
        if (!configured.Equals("Auto", StringComparison.OrdinalIgnoreCase))
        {
            return configured.ToLowerInvariant() switch
            {
                "nintendo" => ControllerLayoutKind.Nintendo,
                "playstation" => ControllerLayoutKind.PlayStation,
                "generic" => ControllerLayoutKind.Generic,
                _ => ControllerLayoutKind.Xbox
            };
        }

        string identity = this.TryReadControllerIdentity();
        if (this.CachedAutoLayout.HasValue && string.Equals(identity, this.LastIdentity, StringComparison.Ordinal))
            return this.CachedAutoLayout.Value;

        this.LastIdentity = identity;
        ControllerLayoutKind detected = this.IdentityLooksNintendo(identity)
            ? ControllerLayoutKind.Nintendo
            : IdentityLooksPlayStation(identity)
                ? ControllerLayoutKind.PlayStation
                : IdentityLooksGeneric(identity)
                    ? ControllerLayoutKind.Generic
                    : ControllerLayoutKind.Xbox;

        this.CachedAutoLayout = detected;
        if (!this.LoggedAutoProfile)
        {
            this.LoggedAutoProfile = true;
            this.Monitor.Log(
                $"Cardcha controller profile: {detected} (identity: {(string.IsNullOrWhiteSpace(identity) ? "unknown/XInput fallback" : identity)}).",
                LogLevel.Trace
            );
        }

        return detected;
    }

    private string TryReadControllerIdentity()
    {
        try
        {
            object capabilities = GamePad.GetCapabilities(PlayerIndex.One);
            Type type = capabilities.GetType();
            List<string> values = new();
            foreach (string propertyName in new[] { "DisplayName", "Identifier", "Name", "GamePadType" })
            {
                System.Reflection.PropertyInfo? property = type.GetProperty(propertyName);
                object? value = property?.GetValue(capabilities);
                if (value is not null && !string.IsNullOrWhiteSpace(value.ToString()))
                    values.Add(value.ToString()!);
            }

            return string.Join(" ", values.Distinct(StringComparer.OrdinalIgnoreCase));
        }
        catch
        {
            return string.Empty;
        }
    }

    private bool IdentityLooksNintendo(string? identity)
    {
        if (string.IsNullOrWhiteSpace(identity))
            return false;

        string value = identity.ToLowerInvariant();
        return value.Contains("nintendo")
            || value.Contains("switch")
            || value.Contains("joy-con")
            || value.Contains("joycon")
            || value.Contains("pro controller");
    }

    private static bool IdentityLooksPlayStation(string? identity)
    {
        if (string.IsNullOrWhiteSpace(identity))
            return false;

        string value = identity.ToLowerInvariant();
        return value.Contains("playstation")
            || value.Contains("dualshock")
            || value.Contains("dualsense")
            || value.Contains("sony")
            || value.Contains("ps4")
            || value.Contains("ps5");
    }

    private static bool IdentityLooksGeneric(string? identity)
    {
        if (string.IsNullOrWhiteSpace(identity))
            return false;

        string value = identity.ToLowerInvariant();
        return value.Contains("generic") || value.Contains("unknown");
    }
}
