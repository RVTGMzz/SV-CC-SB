
namespace Cardcha.Models;

internal sealed class SaveData
{
    public int SchemaVersion { get; set; } = 11;
    public HashSet<string> OwnedCards { get; set; } = new(StringComparer.OrdinalIgnoreCase);
    public List<string> EquippedCards { get; set; } = new();
    public Dictionary<string, int> CardLevels { get; set; } = new(StringComparer.OrdinalIgnoreCase);
    public Dictionary<string, int> CardCopies { get; set; } = new(StringComparer.OrdinalIgnoreCase);
    public int ActiveCardSlotCount { get; set; } = 2;
    public int SuspiciousDust { get; set; }
    public long PullIndex { get; set; }
    public ulong GachaSeed { get; set; }
    public int StandardSinceRare { get; set; }
    public int StandardSinceEpic { get; set; }
    public int StandardSinceLegendary { get; set; }
    public int PremiumSinceEpic { get; set; }
    public int PremiumSinceLegendary { get; set; }
    public bool PhoenixHeartUsedToday { get; set; }

    // v0.1.17-alpha.11.6 — virtual Scrap wallet. These no longer occupy backpack slots.
    public int CardboardScraps { get; set; }
    public int ShinyScraps { get; set; }

    // v0.1.11 normal-gameplay onboarding.
    public bool FirstScrapTriggered { get; set; }
    public int FirstScrapDay { get; set; } = -1;
    public bool MachineLetterQueued { get; set; }
    public bool MachineDelivered { get; set; }
    public bool BinderUnlocked { get; set; }

    // v0.1.17 — MiMi / Wizard Cardcha Story Chapter 1.
    public bool MimiIntroSeen { get; set; }
    public bool MimiMeetupPending { get; set; }
    public bool MimiMeetupCompleted { get; set; }
    public bool ChaChaLoaned { get; set; }
    public bool FirstPullQuestActive { get; set; }
    public bool FirstPullCompleted { get; set; }
    public bool Chapter1Completed { get; set; }
    public int CardchaStoryChapter { get; set; } = 1;
    public int CardchaStoryStage { get; set; }

    // Day the Wizard-house handoff completed. MiMi merchant routine is available from this day onward.
    public int MimiMerchantUnlockedDay { get; set; } = -1;

    // v0.1.17-alpha.11.38 — first-pickup presentation + MiMi appointment deadline.
    public bool FirstScrapPickupNoticeShown { get; set; }
    public int MimiMeetupOfferedDay { get; set; } = -1;

    // v0.1.17-alpha.11.38 — portable machine entitlement.
    // Purchased and Gifted are separate so the 50-card milestone never gives a second device
    // to a player who already paid MiMi's deliberately painful 50,000g price.
    public bool PortableMachinePurchased { get; set; }
    public bool PortableMachineGifted { get; set; }

    public string LastStateFingerprint { get; set; } = "";
}
