namespace Cardcha.Models;

internal sealed class SaveData
{
    public int SchemaVersion { get; set; } = 17;
    public HashSet<string> OwnedCards { get; set; } = new(StringComparer.OrdinalIgnoreCase);
    public List<string> EquippedCards { get; set; } = new();
    public Dictionary<string, int> CardLevels { get; set; } = new(StringComparer.OrdinalIgnoreCase);
    public Dictionary<string, int> CardCopies { get; set; } = new(StringComparer.OrdinalIgnoreCase);

    // v0.3 Binder: personal shortcut collection. IDs are stable string card IDs, never grid indexes.
    public HashSet<string> FavoriteCardIds { get; set; } = new(StringComparer.OrdinalIgnoreCase);

    public int ActiveCardSlotCount { get; set; } = 2;
    public int SuspiciousDust { get; set; }
    public long PullIndex { get; set; }
    public ulong GachaSeed { get; set; }
    public int StandardSinceRare { get; set; }
    public int StandardSinceEpic { get; set; }
    public int StandardSinceLegendary { get; set; }
    public int PremiumSinceEpic { get; set; }
    public int PremiumSinceLegendary { get; set; }
    // alpha.26.5 collection insurance: 20 duplicate pulls -> next eligible pull is NEW.
    public int DuplicatePullStreak { get; set; }
    public bool PhoenixHeartUsedToday { get; set; }
    public bool LifelineUsedToday { get; set; }
    public bool GuardianAngelUsedToday { get; set; }

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

    public int MimiMerchantUnlockedDay { get; set; } = -1;
    public bool MimiFirstMerchantPepTalkShown { get; set; }

    // v0.1.17-alpha.11.38 — first-pickup presentation + MiMi appointment deadline.
    public bool FirstScrapPickupNoticeShown { get; set; }
    public int MimiMeetupOfferedDay { get; set; } = -1;

    // v0.1.17-alpha.11.38 — portable machine entitlement.
    public bool PortableMachinePurchased { get; set; }
    public bool PortableMachineGifted { get; set; }

    // alpha.28 — Cardcha-owned Airship progression.
    public bool AirshipFlybySeen { get; set; }
    public bool AirshipUnlocked { get; set; }
    public int AirshipUnlockedDay { get; set; } = -1;
    public int AirshipHighestRegionUnlocked { get; set; }
    public int AirshipFlightsTaken { get; set; }
    public int AirshipTotalFarePaid { get; set; }

    // alpha.28.0.4.14: persistent Airship infrastructure levels. Gameplay bonuses are not
    // attached yet; this foundation validates Magic Dust economy, UI and persistence first.
    public int AirshipEngineLevel { get; set; }
    public int AirshipNavigationLevel { get; set; }
    public int AirshipHullLevel { get; set; }
    public int AirshipReactorLevel { get; set; }

    public string LastStateFingerprint { get; set; } = "";
}
