namespace Cardcha.Patches;

/// <summary>
/// .5.12.4 regression marker only. Forest gate placement is owned exclusively by
/// AirshipFoundationService.ResolveSkyDockTile. No runtime relocation/flood-fill hook is installed.
/// </summary>
internal static class AirshipGateRelocationPatch
{
    internal const float CanonicalGateUseDistance = 160f;
    internal const string CollisionPolicy = "CollisionEdits=NONE";
}
