using Cardcha.Models;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley;
using StardewValley.Menus;
using StardewValley.Quests;
using SObject = StardewValley.Object;

namespace Cardcha.Services;

/// <summary>
/// Handles the normal Cardcha onboarding loop without requiring SMAPI commands:
/// first real Scrap drop -> MiMi visits the farm NEXT DAY -> 13:00–17:00 Wizard-house meetup -> Wizard hands over Machine + Binder.
/// </summary>
internal sealed class ProgressionService
{
    public const string MachineLetterId = "Ronvotri.Cardcha_MachineLetter";
    public const string MimiMeetupQuestId = "Ronvotri.Cardcha_MimiMeetupQuest";
    private const string MimiMeetupQuestMarker = "Ronvotri.Cardcha/MimiMeetupQuest";

    public bool HasFirstScrapTriggered => this.Save.Data.FirstScrapTriggered;

    private string CenterNoticeText = "";
    private long CenterNoticeUntilMs;

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;


    public ProgressionService(IModHelper helper, IMonitor monitor, SaveService save)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
    }

    public void OnSaveLoaded()
    {
        ClearLegacyMachineMail();

        // Migration friendliness: if a previous prototype already gave the player a machine,
        // don't send a second onboarding package.
        if (!this.Save.Data.MachineDelivered && HasMachineNearbyOrInInventory())
        {
            this.Save.Data.FirstScrapTriggered = true;
            this.Save.Data.MachineDelivered = true;
            this.Save.Data.BinderUnlocked = true;
            this.Save.Data.MachineLetterQueued = false;
            this.Save.Data.MimiIntroSeen = true;
            this.Save.Data.MimiMeetupPending = false;
            this.Save.Data.MimiMeetupCompleted = true;
            this.Save.Data.ChaChaLoaned = true;
            this.Save.Data.AirshipUnlocked = true;
            this.Save.Data.AirshipHighestRegionUnlocked = Math.Max(1, this.Save.Data.AirshipHighestRegionUnlocked);
            if (this.Save.Data.AirshipUnlockedDay < 0)
                this.Save.Data.AirshipUnlockedDay = Game1.Date.TotalDays;
            this.Save.Data.FirstPullQuestActive = this.Save.Data.PullIndex <= 0;
            this.Save.Data.FirstPullCompleted = this.Save.Data.PullIndex > 0;
            this.Save.Data.Chapter1Completed = this.Save.Data.PullIndex > 0;
            this.Save.Data.CardchaStoryChapter = 1;
            this.Save.Data.CardchaStoryStage = this.Save.Data.PullIndex > 0 ? 4 : 3;
            this.Save.Save();

            this.Monitor.Log(
                "Normal-play onboarding detected an existing Cardcha! Machine; Chapter 1 marked complete and duplicate delivery suppressed.",
                LogLevel.Trace
            );
        }

        // If the letter was already read somehow but delivery didn't happen (e.g. upgrade edge case),
        // make the reward self-healing.
        TryDeliverMachineAfterLetter();

        if (this.Save.Data.MimiMeetupPending && !this.Save.Data.MimiMeetupCompleted)
            this.EnsureMimiMeetupQuest();
        else
            this.RemoveMimiMeetupQuest();

        this.TryShowFirstScrapPickupNotice();
    }

    public void OnDayStarted()
    {
        ClearLegacyMachineMail();

        // Chapter 1 onboarding is fully in-person:
        // MiMi visits first, then the Wizard hands over the rewards at the meetup.
        // No Cardcha reward is delivered through the mailbox.
        if (this.Save.Data.MimiMeetupPending && !this.Save.Data.MimiMeetupCompleted)
            this.EnsureMimiMeetupQuest();
        else
            this.RemoveMimiMeetupQuest();
    }

    public void OnReturnedToTitle()
    {
        this.CenterNoticeText = "";
        this.CenterNoticeUntilMs = 0;
    }

    public void OnUpdate()
    {
        // Stardew can populate the visible mailbox after DayStarted.
        // Keep removing ONLY Cardcha's retired mail ID so the phantom "!" can't reappear.
        if (this.Save.Data.FirstScrapTriggered || this.Save.Data.MachineDelivered)
            ClearLegacyMachineMail();

        this.TryShowFirstScrapPickupNotice();

        if (this.Save.Data.MimiMeetupPending && !this.Save.Data.MimiMeetupCompleted)
            this.EnsureMimiMeetupQuest();
    }

    public void OnFirstCardboardScrapDropped()
    {
        if (!Context.IsWorldReady || this.Save.Data.FirstScrapTriggered)
            return;

        this.Save.Data.FirstScrapTriggered = true;
        this.Save.Data.FirstScrapDay = Game1.Date.TotalDays;

        ClearLegacyMachineMail();
        this.Save.Data.MachineLetterQueued = true; // compatibility field; now means "Cardcha story pending"
        this.Save.Data.CardchaStoryChapter = 1;
        this.Save.Data.CardchaStoryStage = 1;
        this.Save.Data.MimiIntroSeen = false;
        this.Save.Data.MimiMeetupPending = false;
        this.Save.Data.MimiMeetupCompleted = false;
        this.Save.Data.ChaChaLoaned = false;
        this.Save.Data.FirstPullQuestActive = false;
        this.Save.Data.FirstPullCompleted = false;
        this.Save.Data.Chapter1Completed = false;
        this.Save.Save();

        this.Monitor.Log(
            "First natural Cardboard Scrap drop detected. MiMi's farm visit is armed for the NEXT day; the centered discovery notice waits until the player actually picks a Scrap up.",
            LogLevel.Info
        );
    }


    public bool ShouldStartMimiIntro()
    {
        if (!Context.IsWorldReady)
            return false;

        bool nextDayReached = this.Save.Data.FirstScrapDay < 0
            || Game1.Date.TotalDays > this.Save.Data.FirstScrapDay;

        return this.Save.Data.FirstScrapTriggered
            && nextDayReached
            && !this.Save.Data.MimiIntroSeen
            && !this.Save.Data.MachineDelivered;
    }

    public bool ShouldStartMimiMeetup()
    {
        if (!Context.IsWorldReady)
            return false;

        return this.Save.Data.MimiIntroSeen
            && this.Save.Data.MimiMeetupPending
            && !this.Save.Data.MimiMeetupCompleted
            && !this.Save.Data.MachineDelivered;
    }

    public void CompleteMimiIntro()
    {
        if (this.Save.Data.MimiIntroSeen)
            return;

        this.Save.Data.MimiIntroSeen = true;
        this.Save.Data.MimiMeetupPending = true;
        this.Save.Data.MimiMeetupOfferedDay = Game1.Date.TotalDays;
        this.Save.Data.CardchaStoryChapter = 1;
        this.Save.Data.CardchaStoryStage = 2;
        this.Save.Save();
        this.EnsureMimiMeetupQuest();

        Game1.showGlobalMessage(
            this.Helper.Translation.Get("story.mimi.objective").ToString()
        );

        this.Monitor.Log(
            "MiMi intro completed. Wizard-house meetup is pending for 13:00–17:00.",
            LogLevel.Info
        );
    }

    public void CompleteWizardMeetup()
    {
        if (this.Save.Data.MimiMeetupCompleted)
            return;

        this.Save.Data.MimiMeetupPending = false;
        this.Save.Data.MimiMeetupCompleted = true;
        this.Save.Data.MimiMeetupOfferedDay = -1;
        this.Save.Data.ChaChaLoaned = true;
        this.Save.Data.FirstPullQuestActive = true;
        this.Save.Data.FirstPullCompleted = false;
        this.Save.Data.Chapter1Completed = false;
        this.Save.Data.CardchaStoryChapter = 1;
        this.Save.Data.CardchaStoryStage = 3;
        this.Save.Data.MimiMerchantUnlockedDay = Game1.Date.TotalDays;

        this.Save.Data.AirshipUnlocked = true;
        this.Save.Data.AirshipHighestRegionUnlocked = Math.Max(1, this.Save.Data.AirshipHighestRegionUnlocked);
        this.Save.Data.AirshipUnlockedDay = Game1.Date.TotalDays;

        this.DeliverMachineDirectly();
        this.RemoveMimiMeetupQuest();
        this.Save.Save();
        Game1.showGlobalMessage(this.Helper.Translation.Get("airship.unlocked").ToString());

        this.Monitor.Log(
            "Cardcha Story Chapter 1 handoff completed: MiMi introduced the player, the Wizard delivered the Machine + Binder, and Region I Airship access was unlocked.",
            LogLevel.Info
        );
    }

    public bool ShouldForceMimiHomeVisit()
    {
        if (!Context.IsWorldReady
            || !this.Save.Data.MimiMeetupPending
            || this.Save.Data.MimiMeetupCompleted
            || this.Save.Data.MachineDelivered)
        {
            return false;
        }

        int offeredDay = this.Save.Data.MimiMeetupOfferedDay;
        if (offeredDay < 0)
            return false;

        // The appointment day is day 1. If the player also ignores day 2, MiMi and
        // the Wizard arrive at the start of day 3: offeredDay + 2.
        return Game1.Date.TotalDays >= offeredDay + 2;
    }

    public bool OnPullResolved(PullType type, int count)
    {
        if (!Context.IsWorldReady
            || !this.Save.Data.FirstPullQuestActive
            || this.Save.Data.FirstPullCompleted
            || count <= 0)
        {
            return false;
        }

        this.Save.Data.FirstPullQuestActive = false;
        this.Save.Data.FirstPullCompleted = true;
        this.Save.Data.Chapter1Completed = true;
        this.Save.Data.CardchaStoryChapter = 1;
        this.Save.Data.CardchaStoryStage = 4;
        this.Save.Save();

        this.Monitor.Log(
            $"Cardcha Chapter 1 completed by first {type} pull (count={count}).",
            LogLevel.Info
        );

        return true;
    }

    public void DeliverMachineDirectly()
    {
        if (this.Save.Data.MachineDelivered)
            return;

        if (HasMachineNearbyOrInInventory())
        {
            this.Save.Data.MachineDelivered = true;
            this.Save.Data.BinderUnlocked = true;
            this.Save.Save();
            return;
        }

        Item machine = ItemRegistry.Create($"(BC){ItemAssetService.CardchaMachineId}");
        if (machine is SObject machineObject)
            machineObject.modData[ItemAssetService.MachineMarkerKey] = "1";

        Item? leftover = Game1.player.addItemToInventory(machine);

        if (leftover is not null)
            Game1.createItemDebris(leftover, Game1.player.Position, -1, Game1.currentLocation);

        this.Save.Data.MachineDelivered = true;
        this.Save.Data.BinderUnlocked = true;
        this.Save.Data.MachineLetterQueued = false;
        this.Save.Data.MimiIntroSeen = true;
        ClearLegacyMachineMail();
        this.Save.Save();

        Game1.showGlobalMessage(this.Helper.Translation.Get("progress.machine-delivered").ToString());

        this.Monitor.Log(
            "The Wizard personally delivered the Cardcha Machine + Binder during the Chapter 1 meetup.",
            LogLevel.Info
        );
    }

    public void DrawCenteredNotice(SpriteBatch b)
    {
        if (string.IsNullOrWhiteSpace(this.CenterNoticeText)
            || Environment.TickCount64 >= this.CenterNoticeUntilMs
            || Game1.activeClickableMenu is not null)
        {
            return;
        }

        const int maxTextWidth = 620;
        string wrapped = Game1.parseText(this.CenterNoticeText, Game1.dialogueFont, maxTextWidth);
        Vector2 measured = Game1.dialogueFont.MeasureString(wrapped);
        int width = Math.Max(420, Math.Min(maxTextWidth + 64, (int)measured.X + 64));
        int height = Math.Max(116, (int)measured.Y + 54);
        int x = (Game1.uiViewport.Width - width) / 2;
        int y = Math.Max(80, (Game1.uiViewport.Height - height) / 2 - 80);

        IClickableMenu.drawTextureBox(
            b,
            Game1.menuTexture,
            new Rectangle(0, 256, 60, 60),
            x,
            y,
            width,
            height,
            Color.White,
            1f,
            true
        );
        Utility.drawTextWithShadow(
            b,
            wrapped,
            Game1.dialogueFont,
            new Vector2(x + 32, y + 24),
            Game1.textColor
        );
    }

    private void TryShowFirstScrapPickupNotice()
    {
        if (!Context.IsWorldReady
            || !this.Save.Data.FirstScrapTriggered
            || this.Save.Data.FirstScrapPickupNoticeShown
            || !PlayerHasCardboardScrap())
        {
            return;
        }

        this.Save.Data.FirstScrapPickupNoticeShown = true;
        this.CenterNoticeText = this.Helper.Translation.Get("progress.scrap-found").ToString();
        this.CenterNoticeUntilMs = Environment.TickCount64 + 6000;
        this.Save.Save();
        Game1.playSound("discoverMineral");
    }

    private static bool PlayerHasCardboardScrap()
    {
        if (!Context.IsWorldReady || Game1.player is null)
            return false;

        string qualified = $"(O){DropService.CardboardScrapId}";
        foreach (Item? item in Game1.player.Items)
        {
            if (item is not null
                && (string.Equals(item.QualifiedItemId, qualified, StringComparison.OrdinalIgnoreCase)
                    || string.Equals(item.ItemId, DropService.CardboardScrapId, StringComparison.OrdinalIgnoreCase)))
            {
                return true;
            }
        }

        return false;
    }

    private void EnsureMimiMeetupQuest()
    {
        if (!Context.IsWorldReady
            || !this.Save.Data.MimiMeetupPending
            || this.Save.Data.MimiMeetupCompleted
            || this.Save.Data.MachineDelivered)
        {
            return;
        }

        foreach (Quest existing in Game1.player.questLog)
        {
            if (string.Equals(existing.id.Value, MimiMeetupQuestId, StringComparison.OrdinalIgnoreCase)
                || existing.modData.ContainsKey(MimiMeetupQuestMarker))
            {
                existing.questTitle = this.Helper.Translation.Get("story.mimi.quest-title").ToString();
                existing.questDescription = this.Helper.Translation.Get("story.mimi.quest-description").ToString();
                existing.currentObjective = this.Helper.Translation.Get("story.mimi.quest-objective").ToString();
                existing.canBeCancelled.Value = false;
                return;
            }
        }

        Quest quest = new Quest();
        quest.id.Value = MimiMeetupQuestId;
        quest.questType.Value = Quest.type_basic;
        quest.questTitle = this.Helper.Translation.Get("story.mimi.quest-title").ToString();
        quest.questDescription = this.Helper.Translation.Get("story.mimi.quest-description").ToString();
        quest.currentObjective = this.Helper.Translation.Get("story.mimi.quest-objective").ToString();
        quest.accepted.Value = true;
        quest.showNew.Value = true;
        quest.dailyQuest.Value = false;
        quest.canBeCancelled.Value = false;
        quest.modData[MimiMeetupQuestMarker] = "1";
        Game1.player.questLog.Add(quest);
        Game1.dayTimeMoneyBox.questsDirty = true;
    }

    private void RemoveMimiMeetupQuest()
    {
        if (!Context.IsWorldReady)
            return;

        List<Quest> remove = new();
        foreach (Quest quest in Game1.player.questLog)
        {
            if (string.Equals(quest.id.Value, MimiMeetupQuestId, StringComparison.OrdinalIgnoreCase)
                || quest.modData.ContainsKey(MimiMeetupQuestMarker))
            {
                remove.Add(quest);
            }
        }

        foreach (Quest quest in remove)
            Game1.player.questLog.Remove(quest);

        if (remove.Count > 0)
            Game1.dayTimeMoneyBox.questsDirty = true;
    }

    public string DescribeState()
    {
        bool read = Context.IsWorldReady && Game1.player.mailReceived.Contains(MachineLetterId);
        return
            $"FirstScrap={this.Save.Data.FirstScrapTriggered} | " +
            $"FirstScrapDay={this.Save.Data.FirstScrapDay} | " +
            $"VisitPending={this.Save.Data.MachineLetterQueued && !this.Save.Data.MachineDelivered} | " +
            $"LegacyLetterRead={read} | " +
            $"MachineDelivered={this.Save.Data.MachineDelivered} | " +
            $"BinderUnlocked={this.Save.Data.BinderUnlocked} | " +
            $"Chapter={this.Save.Data.CardchaStoryChapter} | " +
            $"Stage={this.Save.Data.CardchaStoryStage} | " +
            $"MiMiIntro={this.Save.Data.MimiIntroSeen} | " +
            $"MeetupPending={this.Save.Data.MimiMeetupPending} | " +
            $"MeetupOfferedDay={this.Save.Data.MimiMeetupOfferedDay} | ForceHome={this.ShouldForceMimiHomeVisit()} | " +
            $"MeetupDone={this.Save.Data.MimiMeetupCompleted} | " +
            $"ChaChaLoaned={this.Save.Data.ChaChaLoaned} | " +
            $"FirstPullQuest={this.Save.Data.FirstPullQuestActive} | " +
            $"FirstPullDone={this.Save.Data.FirstPullCompleted} | " +
            $"Chapter1Done={this.Save.Data.Chapter1Completed}";
    }

    private void EnsureLetterQueuedIfNeeded()
    {
        // Legacy stub retained for source compatibility after the shift to Wizard in-person delivery.
    }

    private void QueueLetterForTomorrow()
    {
        // Legacy stub retained for source compatibility after the shift to Wizard in-person delivery.
    }

    private void TryDeliverMachineAfterLetter()
    {
        // Legacy stub retained for source compatibility after the shift to Wizard in-person delivery.
    }

    private static void ClearLegacyMachineMail()
    {
        if (!Context.IsWorldReady)
            return;

        RemoveLegacyEntries(Game1.player.mailForTomorrow);
        RemoveLegacyEntries(Game1.player.mailReceived);

        // Different Stardew builds expose the visible mailbox through slightly
        // different static/instance members. Search only members whose names contain
        // "mailbox", and remove ONLY Cardcha's retired mail ID.
        ScrubMailboxMembers(typeof(Game1), null);
        ScrubMailboxMembers(Game1.player.GetType(), Game1.player);
    }

    private static void ScrubMailboxMembers(Type ownerType, object? instance)
    {
        const System.Reflection.BindingFlags flags =
            System.Reflection.BindingFlags.Public
            | System.Reflection.BindingFlags.NonPublic
            | System.Reflection.BindingFlags.Static
            | System.Reflection.BindingFlags.Instance;

        try
        {
            foreach (System.Reflection.FieldInfo field in ownerType.GetFields(flags))
            {
                if (!field.Name.Contains("mailbox", StringComparison.OrdinalIgnoreCase))
                    continue;

                if (field.IsStatic != (instance is null))
                    continue;

                TryScrubMailboxValue(field.GetValue(instance));
            }

            foreach (System.Reflection.PropertyInfo property in ownerType.GetProperties(flags))
            {
                if (!property.Name.Contains("mailbox", StringComparison.OrdinalIgnoreCase)
                    || property.GetIndexParameters().Length > 0
                    || !property.CanRead)
                {
                    continue;
                }

                System.Reflection.MethodInfo? getter = property.GetGetMethod(nonPublic: true);
                if (getter is null || getter.IsStatic != (instance is null))
                    continue;

                TryScrubMailboxValue(property.GetValue(instance));
            }
        }
        catch
        {
            // Legacy cleanup must never interfere with normal gameplay.
        }
    }

    private static void TryScrubMailboxValue(object? value)
    {
        if (value is System.Collections.IList list)
        {
            for (int i = list.Count - 1; i >= 0; i--)
            {
                if (IsLegacyMachineMailEntry(list[i]?.ToString()))
                    list.RemoveAt(i);
            }
            return;
        }

        if (value is ICollection<string> strings)
            RemoveLegacyEntries(strings);
    }

    private static void RemoveLegacyEntries(ICollection<string> collection)
    {
        foreach (string entry in collection.ToList())
        {
            if (IsLegacyMachineMailEntry(entry))
                collection.Remove(entry);
        }
    }

    private static bool IsLegacyMachineMailEntry(string? entry)
    {
        if (string.IsNullOrWhiteSpace(entry))
            return false;

        return entry.Equals(MachineLetterId, StringComparison.OrdinalIgnoreCase)
            || entry.StartsWith(MachineLetterId + "%", StringComparison.OrdinalIgnoreCase)
            || entry.StartsWith(MachineLetterId + " ", StringComparison.OrdinalIgnoreCase);
    }

    private static bool HasMachineNearbyOrInInventory()
    {
        string qualified = $"(BC){ItemAssetService.CardchaMachineId}";

        foreach (Item? item in Game1.player.Items)
        {
            if (item?.QualifiedItemId.Equals(qualified, StringComparison.OrdinalIgnoreCase) == true)
                return true;
        }

        if (Game1.currentLocation is not null)
        {
            foreach (SObject obj in Game1.currentLocation.Objects.Values)
            {
                if (obj.QualifiedItemId.Equals(qualified, StringComparison.OrdinalIgnoreCase))
                    return true;
            }
        }

        return false;
    }
}
