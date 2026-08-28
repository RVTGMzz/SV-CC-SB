using System.Reflection;
using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.GameData.Characters;
using StardewValley.Menus;

namespace Cardcha.Services;

/// <summary>
/// Alpha.27 social layer for MiMi.
/// Keeps the pre-reveal mystery actor non-social, then promotes the same canonical NPC into
/// Stardew's real friendship/gifting systems after the Wizard meetup is complete.
/// </summary>
internal sealed class MimiSocialService
{
    private const string NpcId = MimiMysteryTownService.NpcId;
    private const string DialogueAsset = "Characters/Dialogue/Ronvotri.Cardcha_MiMi";
    private const float InteractionDistance = 190f;

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly WorldActorService WorldActors;
    private readonly Action OpenMimiShop;

    private bool LastUnlocked;
    private bool CacheInitialized;

    public MimiSocialService(
        IModHelper helper,
        IMonitor monitor,
        SaveService save,
        WorldActorService worldActors,
        Action openMimiShop)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.WorldActors = worldActors;
        this.OpenMimiShop = openMimiShop;
    }

    private bool IsUnlocked
        => Context.IsWorldReady && this.Save.Data.MimiMeetupCompleted;

    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)
    {
        if (e.NameWithoutLocale.IsEquivalentTo("Data/Characters"))
        {
            e.Edit(asset =>
            {
                IDictionary<string, CharacterData> data = asset.AsDictionary<string, CharacterData>().Data;
                if (!data.TryGetValue(NpcId, out CharacterData? mimi) || mimi is null)
                    return;

                bool unlocked = this.Save.Data.MimiMeetupCompleted;
                SetProperty(mimi, "DisplayName", unlocked ? "MiMi" : "???");
                SetProperty(mimi, "BirthSeason", "spring");
                SetProperty(mimi, "BirthDay", 17);
                SetProperty(mimi, "CanSocialize", unlocked ? "TRUE" : "FALSE");
                SetProperty(mimi, "CanReceiveGifts", unlocked);
                SetProperty(mimi, "Calendar", unlocked ? "AlwaysShown" : "HiddenAlways");
                SetProperty(mimi, "SocialTab", unlocked ? "AlwaysShown" : "HiddenAlways");

                // MiMi is a real friend NPC, but Cardcha shouldn't silently add her to unrelated
                // vanilla completion/quest requirements.
                SetProperty(mimi, "IntroductionsQuest", false);
                SetProperty(mimi, "ItemDeliveryQuests", "FALSE");
                SetProperty(mimi, "PerfectionScore", false);
                SetProperty(mimi, "CanVisitIsland", "FALSE");
            });
            return;
        }

        if (e.NameWithoutLocale.IsEquivalentTo("Data/NPCGiftTastes"))
        {
            e.Edit(asset =>
            {
                IDictionary<string, string> data = asset.AsDictionary<string, string>().Data;
                data[NpcId] = this.BuildGiftTasteRow();
            });
            return;
        }

        if (e.Name.IsEquivalentTo(DialogueAsset) && this.Save.Data.MimiMeetupCompleted)
        {
            e.Edit(asset =>
            {
                IDictionary<string, string> data = asset.AsDictionary<string, string>().Data;
                data["Introduction"] = this.T("mimi.social.introduction");
                data["Mon"] = this.T("mimi.social.mon");
                data["Tue"] = this.T("mimi.social.tue");
                data["Wed"] = this.T("mimi.social.wed");
                data["Thu"] = this.T("mimi.social.thu");
                data["Fri"] = this.T("mimi.social.fri");
                data["Sat"] = this.T("mimi.social.sat");
                data["Sun"] = this.T("mimi.social.sun");
                data["rain"] = this.T("mimi.social.rain");
                data["AcceptBirthdayGift"] = this.T("mimi.social.birthday");
            });
        }
    }

    public void OnSaveLoaded()
    {
        this.LastUnlocked = false;
        this.CacheInitialized = false;
        this.RefreshUnlockState(forceRefresh: true);
    }

    public void OnDayStarted()
        => this.RefreshUnlockState(forceRefresh: false);

    public void OnUpdateTicked(UpdateTickedEventArgs e)
    {
        if (!Context.IsWorldReady || !e.IsMultipleOf(30))
            return;

        this.RefreshUnlockState(forceRefresh: false);
    }

    public void OnReturnedToTitle()
    {
        this.LastUnlocked = false;
        this.CacheInitialized = false;
    }

    /// <summary>
    /// Controller/mouse-friendly coexistence between vanilla friendship and MiMi's shop:
    /// first empty-hand interaction each day is normal Stardew talk; held gifts use vanilla
    /// gifting; after daily talk is done, another empty-hand interaction opens MiMi's shop.
    /// </summary>
    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!this.IsUnlocked
            || !e.Button.IsActionButton()
            || Game1.activeClickableMenu is not null
            || Game1.dialogueUp
            || Game1.eventUp)
        {
            return;
        }

        NPC? mimi = this.WorldActors.FindMimiActor();
        if (mimi is null
            || mimi.isInvisible.Value
            || mimi.currentLocation is null
            || mimi.currentLocation != Game1.currentLocation)
        {
            return;
        }

        Vector2 playerCenter = Game1.player.Position + new Vector2(32f, 32f);
        Vector2 mimiCenter = mimi.Position + new Vector2(32f, 48f);
        if (Vector2.DistanceSquared(playerCenter, mimiCenter) > InteractionDistance * InteractionDistance)
            return;

        this.EnsureFriendshipEntry();
        if (!Game1.player.friendshipData.TryGetValue(NpcId, out Friendship? friendship) || friendship is null)
            return;

        this.Helper.Input.Suppress(e.Button);
        Game1.player.Halt();
        mimi.faceTowardFarmerForPeriod(1200, 3, false, Game1.player);

        // If the farmer is carrying a gift, always let Stardew's own NPC code process it.
        // Otherwise the first interaction of the day is normal friendship dialogue.
        if (Game1.player.ActiveObject is not null || !friendship.TalkedToToday)
        {
            try
            {
                mimi.checkAction(Game1.player, Game1.currentLocation);
            }
            catch (Exception ex)
            {
                this.Monitor.Log($"MiMi vanilla social interaction failed: {ex}", LogLevel.Error);
            }
            return;
        }

        // Once today's normal greeting is complete, the same simple action button becomes the
        // merchant interaction. This keeps controller UX one-button and doesn't steal gifting.
        this.OpenMimiShop();
    }

    public string Describe()
    {
        if (!Context.IsWorldReady)
            return "MiMiSocial=<no save>";

        bool exists = Game1.player.friendshipData.TryGetValue(NpcId, out Friendship? friendship);
        int points = exists && friendship is not null ? friendship.Points : 0;
        int hearts = Math.Max(0, points / 250);
        int giftsWeek = exists && friendship is not null ? friendship.GiftsThisWeek : 0;
        bool talked = exists && friendship is not null && friendship.TalkedToToday;
        return $"MiMiSocialUnlocked={this.IsUnlocked} | FriendshipEntry={exists} | Hearts={hearts} ({points} pts) | GiftsThisWeek={giftsWeek}/2 | TalkedToday={talked} | Birthday=Spring17";
    }

    private void RefreshUnlockState(bool forceRefresh)
    {
        if (!Context.IsWorldReady)
            return;

        bool unlocked = this.Save.Data.MimiMeetupCompleted;
        bool changed = !this.CacheInitialized || unlocked != this.LastUnlocked;
        this.CacheInitialized = true;
        this.LastUnlocked = unlocked;

        if (unlocked)
            this.EnsureFriendshipEntry();

        if (!forceRefresh && !changed)
            return;

        try
        {
            this.Helper.GameContent.InvalidateCache("Data/Characters");
            this.Helper.GameContent.InvalidateCache("Data/NPCGiftTastes");
            this.Helper.GameContent.InvalidateCache(DialogueAsset);
            this.Monitor.Log(
                unlocked
                    ? "MiMi promoted to Stardew social NPC: friendship, gifting, birthday, and social-tab data refreshed."
                    : "MiMi social data held behind the Wizard meetup.",
                LogLevel.Trace
            );
        }
        catch (Exception ex)
        {
            this.Monitor.Log($"Couldn't refresh MiMi social assets: {ex.Message}", LogLevel.Trace);
        }
    }

    private void EnsureFriendshipEntry()
    {
        if (!this.IsUnlocked || Game1.player.friendshipData.ContainsKey(NpcId))
            return;

        try
        {
            Game1.player.friendshipData.Add(NpcId, new Friendship());
            this.Monitor.Log("Created MiMi friendship entry after the Wizard meetup.", LogLevel.Info);
        }
        catch (Exception ex)
        {
            this.Monitor.Log($"Couldn't create MiMi friendship entry: {ex.Message}", LogLevel.Warn);
        }
    }

    private string BuildGiftTasteRow()
    {
        // Extra personal overrides sit on top of vanilla universal tastes.
        // MiMi loves odd/arcane technology, and likes elemental/mineral curiosities.
        string[] parts =
        {
            this.T("mimi.gift.love"),
            "74 122 422 769 787",
            this.T("mimi.gift.like"),
            "80 82 84 86 768",
            this.T("mimi.gift.dislike"),
            "",
            this.T("mimi.gift.hate"),
            "",
            this.T("mimi.gift.neutral"),
            ""
        };
        return string.Join('/', parts) + "/";
    }

    private string T(string key)
        => this.Helper.Translation.Get(key).ToString();

    private static void SetProperty(object target, string propertyName, object? value)
    {
        Type targetObjectType = target.GetType();
        PropertyInfo? property = targetObjectType.GetProperty(propertyName, BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
        FieldInfo? field = targetObjectType.GetField(propertyName, BindingFlags.Public | BindingFlags.Instance | BindingFlags.IgnoreCase);
        Type? memberType = property?.PropertyType ?? field?.FieldType;
        if (memberType is null)
            return;

        try
        {
            object? converted = null;
            if (value is not null)
            {
                Type targetType = Nullable.GetUnderlyingType(memberType) ?? memberType;
                if (targetType.IsInstanceOfType(value))
                    converted = value;
                else if (targetType.IsEnum && value is string enumText)
                    converted = Enum.Parse(targetType, enumText, ignoreCase: true);
                else if (targetType == typeof(string))
                    converted = value.ToString() ?? string.Empty;
                else
                    converted = Convert.ChangeType(value, targetType);
            }

            if (property is not null && property.CanWrite)
                property.SetValue(target, converted);
            else
                field?.SetValue(target, converted);
        }
        catch
        {
            // Optional cross-version member; ignore if the installed game model differs.
        }
    }
}
