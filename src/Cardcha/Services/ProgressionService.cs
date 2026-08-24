using Cardcha.Models;
using StardewModdingAPI;
using StardewValley;
using SObject = StardewValley.Object;

namespace Cardcha.Services;

/// <summary>
/// Handles the normal Cardcha onboarding loop without requiring SMAPI commands:
/// first real Scrap drop -> MiMi visits the farm NEXT DAY -> 13:00–17:00 Wizard-house meetup -> Wizard hands over Machine + Binder.
/// </summary>
internal sealed class ProgressionService
{
    public const string MachineLetterId = "Ronvotri.Cardcha_MachineLetter";

    public bool HasFirstScrapTriggered => this.Save.Data.FirstScrapTriggered;

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
    }

    public void OnDayStarted()
    {
        ClearLegacyMachineMail();

        // Chapter 1 onboarding is fully in-person:
        // MiMi visits first, then the Wizard hands over the rewards at the meetup.
        // No Cardcha reward is delivered through the mailbox.
    }

    public void OnUpdate()
    {
        // Stardew can populate the visible mailbox after DayStarted.
        // Keep removing ONLY Cardcha's retired mail ID so the phantom "!" can't reappear.
        if (this.Save.Data.FirstScrapTriggered || this.Save.Data.MachineDelivered)
            ClearLegacyMachineMail();
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

        Game1.showGlobalMessage(this.Helper.Translation.Get("progress.scrap-found").ToString());
        this.Monitor.Log(
            "First natural Cardboard Scrap drop detected. MiMi's farm visit is armed for the NEXT day.",
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
        this.Save.Data.CardchaStoryChapter = 1;
        this.Save.Data.CardchaStoryStage = 2;
        this.Save.Save();

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
        this.Save.Data.ChaChaLoaned = true;
        this.Save.Data.FirstPullQuestActive = true;
        this.Save.Data.FirstPullCompleted = false;
        this.Save.Data.Chapter1Completed = false;
        this.Save.Data.CardchaStoryChapter = 1;
        this.Save.Data.CardchaStoryStage = 3;
        this.Save.Data.MimiMerchantUnlockedDay = Game1.Date.TotalDays;

        this.DeliverMachineDirectly();
        this.Save.Save();

        this.Monitor.Log(
            "Cardcha Story Chapter 1 handoff completed: MiMi introduced the player and the Wizard delivered the Machine + Binder.",
            LogLevel.Info
        );
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
