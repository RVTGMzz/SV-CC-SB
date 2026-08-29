using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using System.Reflection;

namespace Cardcha.Services;

/// <summary>
/// Owns Cardcha's in-world visual actors. These actors live in GameLocation.characters,
/// so Stardew's own world SpriteBatch sorts them with the player, NPCs, trees, bushes,
/// furniture, and other world layers. This intentionally replaces the old RenderedWorld
/// overlay approach which could never depth-sort correctly against already-drawn vanilla actors.
/// </summary>
internal sealed class WorldActorService
{
    public const string MimiNpcId = MimiMysteryTownService.NpcId;
    public const string MimiCharacterAsset = "Characters/Ronvotri.Cardcha_MiMi";
    public const string MimiBroomCharacterAsset = "Characters/Ronvotri.Cardcha_MiMi_Broom";
    public const string MimiProfileCharacterAsset = "Characters/Ronvotri.Cardcha_MiMi_Profile";
    public const string ChaChaNpcId = "Ronvotri.Cardcha_ChaCha";
    public const string ChaChaCharacterAsset = "Characters/Ronvotri.Cardcha_ChaCha";
    public const string ChaChaMachineCharacterAsset = "Characters/Ronvotri.Cardcha_ChaCha_Machine";

    private const string MimiBroomSheetPath = "assets/mimi_broom.png";
    private const string MimiProfileSheetPath = "assets/mimi_profile.png";
    private const string MimiPortraitAsset = "Portraits/Ronvotri.Cardcha_MiMi";
    private const string MimiPortraitSheetPath = "assets/mimi_portraits_runtime64.png";
    private const string ChaChaFollowSheetPath = "assets/chacha_follow.png";
    private const string ChaChaMachineSheetPath = "assets/chacha_machine.png";

    // Native NPC draw multiplies Character.Scale by 4. These values reproduce the previous
    // approved visual sizes: MiMi 32x48 @ 2.3x, ChaCha 32x32 @ 1.8x.
    private const float MimiNativeScale = 0.575f;
    // The approved alpha.22 broom sheet intentionally draws MiMi/??? about 10% smaller inside
    // the same 32x48 frame. Compensate at runtime so mounting the broom doesn't shrink her body.
    private const float MimiBroomNativeScale = MimiNativeScale * 1.10f;
    private const float ChaChaNativeScale = 0.5625f;

    private static readonly int[] ChaChaEmotePool = { 32, 16, 20, 56, 60, 8, 40 };

    private readonly IMonitor Monitor;
    private NPC? ChaChaActor;
    private Texture2D? MimiPortraitTexture;
    private long NextChaChaEmoteAtMs;
    private int LastChaChaEmote = -1;

    public WorldActorService(IMonitor monitor)
    {
        this.Monitor = monitor;
    }

    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)
    {
        if (e.Name.IsEquivalentTo(MimiProfileCharacterAsset))
        {
            e.LoadFromModFile<Texture2D>(MimiProfileSheetPath, AssetLoadPriority.Medium);
            return;
        }

        if (e.Name.IsEquivalentTo(MimiBroomCharacterAsset))
        {
            e.LoadFromModFile<Texture2D>(MimiBroomSheetPath, AssetLoadPriority.Medium);
            return;
        }

        if (e.Name.IsEquivalentTo(MimiPortraitAsset))
        {
            e.LoadFromModFile<Texture2D>(MimiPortraitSheetPath, AssetLoadPriority.Medium);
            return;
        }

        if (e.Name.IsEquivalentTo(ChaChaCharacterAsset))
        {
            e.LoadFromModFile<Texture2D>(ChaChaFollowSheetPath, AssetLoadPriority.Medium);
            return;
        }

        if (e.Name.IsEquivalentTo(ChaChaMachineCharacterAsset))
            e.LoadFromModFile<Texture2D>(ChaChaMachineSheetPath, AssetLoadPriority.Medium);
    }

    public NPC? FindMimiActor()
    {
        if (!Context.IsWorldReady)
            return null;

        NPC? found = null;
        foreach (GameLocation location in Game1.locations)
        {
            foreach (NPC npc in location.characters
                         .Where(p => string.Equals(p.Name, MimiNpcId, StringComparison.OrdinalIgnoreCase))
                         .ToList())
            {
                if (found is null)
                {
                    found = npc;
                    continue;
                }

                // Old experimental builds could leave a duplicate MiMi in another location.
                // Keep one canonical native actor so depth/collision state can never split.
                location.characters.Remove(npc);
            }
        }

        return found;
    }

    public NPC? EnsureMimiActor()
    {
        NPC? existing = this.FindMimiActor();
        if (existing is not null)
            return existing;

        if (!Context.IsWorldReady)
            return null;

        GameLocation? wizardHouse = Game1.getLocationFromName("WizardHouse");
        if (wizardHouse is null)
            return null;

        try
        {
            NPC created = new(
                new AnimatedSprite(MimiCharacterAsset, 0, 32, 48),
                new Vector2(-6400f, -6400f),
                2,
                MimiNpcId
            );
            created.displayName = "???";
            created.currentLocation = wizardHouse;
            wizardHouse.characters.Add(created);
            this.ConfigureMimiActor(created, broom: false, visible: false);
            return created;
        }
        catch (Exception ex)
        {
            this.Monitor.Log($"Couldn't create MiMi native world actor: {ex}", LogLevel.Error);
            return null;
        }
    }


    /// <summary>Move MiMi to the canonical hidden holding position so no story scene can leave her behind.</summary>
    public void HideMimiActor()
    {
        if (!Context.IsWorldReady)
            return;

        NPC? actor = this.FindMimiActor();
        if (actor is null)
            return;

        GameLocation? wizardHouse = Game1.getLocationFromName("WizardHouse");
        if (wizardHouse is null)
        {
            actor.Halt();
            actor.isInvisible.Value = true;
            return;
        }

        this.MoveMimiActor(
            actor,
            wizardHouse,
            new Vector2(-6400f, -6400f),
            2,
            broom: false,
            visible: false
        );
    }

    public void MoveMimiActor(NPC actor, GameLocation target, Vector2 position, int facing, bool broom = false, bool visible = true)
    {
        if (actor.currentLocation != target)
        {
            actor.currentLocation?.characters.Remove(actor);
            if (!target.characters.Contains(actor))
                target.characters.Add(actor);
            actor.currentLocation = target;
        }

        actor.Halt();
        actor.Position = position;
        actor.FacingDirection = facing;
        this.ConfigureMimiActor(actor, broom, visible);
        this.SetMimiFrame(actor, facing, 0);
    }

    public void ConfigureMimiActor(NPC actor, bool broom, bool visible)
    {
        string asset = broom ? MimiBroomCharacterAsset : MimiCharacterAsset;
        int spriteWidth = broom ? 48 : 32;
        const int spriteHeight = 48;
        if (actor.Sprite is null
            || actor.Sprite.SpriteWidth != spriteWidth
            || actor.Sprite.SpriteHeight != spriteHeight
            || !string.Equals(actor.Sprite.loadedTexture, asset, StringComparison.OrdinalIgnoreCase))
        {
            actor.Sprite = new AnimatedSprite(asset, 0, spriteWidth, spriteHeight);
        }

        actor.Scale = broom ? MimiBroomNativeScale : MimiNativeScale;
        actor.forceOneTileWide.Value = true;
        actor.farmerPassesThrough = false;
        actor.collidesWithOtherCharacters.Value = true;
        actor.willDestroyObjectsUnderfoot = false;
        actor.followSchedule = false;
        actor.ignoreScheduleToday = true;
        actor.drawOnTop = false;
        actor.drawOffset = Vector2.Zero;
        actor.shouldShadowBeOffset = false;
        actor.rotation = 0f;
        actor.breather.Value = false;
        actor.hideShadow.Value = false;
        actor.isInvisible.Value = !visible;
        AssignPortraitTexture(actor, this.LoadMimiPortraitTexture());
    }

    public void SetMimiFrame(NPC actor, int facing, int stepFrame)
    {
        if (actor.Sprite is null)
            return;

        int row = facing switch
        {
            2 => 0, // down/front
            1 => 1, // right
            0 => 2, // up/back
            3 => 3, // left
            _ => 0
        };

        actor.FacingDirection = facing;
        int step = Math.Clamp(stepFrame, 0, 3);

        // alpha.22: NPC Map Locations Custom mode always crops a 16x15 marker from
        // the top-left of the NPC texture. MiMi uses 32x48 frames, so that crop used
        // to show only part of her head. Reserve normal front frame 0 for the marker
        // and never render that reserved frame in the actual world.
        bool normalMimi = string.Equals(actor.Sprite.loadedTexture, MimiCharacterAsset, StringComparison.OrdinalIgnoreCase);
        if (normalMimi && row == 0)
        {
            step = step switch
            {
                0 => 1,
                1 => 2,
                2 => 3,
                _ => 1
            };
        }

        actor.Sprite.CurrentFrame = row * 4 + step;
    }

    public NPC? EnsureChaChaActor(GameLocation location, Vector2 position, int direction, int frame, bool machine = false)
    {
        NPC? actor = this.FindChaChaActor();
        string asset = machine ? ChaChaMachineCharacterAsset : ChaChaCharacterAsset;

        if (actor is null)
        {
            try
            {
                actor = new NPC(
                    new AnimatedSprite(asset, 0, 32, 32),
                    position,
                    direction,
                    ChaChaNpcId
                )
                {
                    SimpleNonVillagerNPC = true,
                    displayName = "ChaCha",
                    currentLocation = location
                };
                location.characters.Add(actor);
                this.ChaChaActor = actor;
            }
            catch (Exception ex)
            {
                this.Monitor.Log($"Couldn't create ChaCha native world actor: {ex}", LogLevel.Error);
                return null;
            }
        }
        else if (actor.currentLocation != location)
        {
            actor.currentLocation?.characters.Remove(actor);
            if (!location.characters.Contains(actor))
                location.characters.Add(actor);
            actor.currentLocation = location;
        }

        if (actor.Sprite is null
            || actor.Sprite.SpriteWidth != 32
            || actor.Sprite.SpriteHeight != 32
            || !string.Equals(actor.Sprite.loadedTexture, asset, StringComparison.OrdinalIgnoreCase))
        {
            actor.Sprite = new AnimatedSprite(asset, 0, 32, 32);
        }

        actor.SimpleNonVillagerNPC = true;
        actor.displayName = "ChaCha";
        actor.Halt();
        actor.Position = position;
        actor.FacingDirection = direction;
        actor.Scale = ChaChaNativeScale;
        actor.forceOneTileWide.Value = true;
        actor.farmerPassesThrough = true;
        actor.collidesWithOtherCharacters.Value = false;
        actor.willDestroyObjectsUnderfoot = false;
        actor.followSchedule = false;
        actor.ignoreScheduleToday = true;
        actor.drawOnTop = false;
        actor.drawOffset = Vector2.Zero;
        actor.shouldShadowBeOffset = false;
        actor.breather.Value = false;
        actor.hideShadow.Value = false;
        actor.isInvisible.Value = false;
        actor.Sprite.CurrentFrame = machine
            ? Math.Clamp(direction, 0, 2) * 6 + Math.Clamp(frame, 0, 5)
            : Math.Clamp(direction, 0, 3) * 4 + Math.Clamp(frame, 0, 3);
        this.ChaChaActor = actor;
        return actor;
    }

    public NPC? FindChaChaActor()
    {
        if (this.ChaChaActor is not null
            && this.ChaChaActor.currentLocation is not null
            && this.ChaChaActor.currentLocation.characters.Contains(this.ChaChaActor))
        {
            return this.ChaChaActor;
        }

        if (!Context.IsWorldReady)
            return null;

        NPC? found = null;
        foreach (GameLocation location in Game1.locations)
        {
            foreach (NPC npc in location.characters
                         .Where(p => string.Equals(p.Name, ChaChaNpcId, StringComparison.OrdinalIgnoreCase))
                         .ToList())
            {
                if (found is null)
                {
                    found = npc;
                    continue;
                }

                location.characters.Remove(npc);
            }
        }

        this.ChaChaActor = found;
        return found;
    }

    public void HideChaChaActor()
    {
        if (!Context.IsWorldReady)
        {
            this.ChaChaActor = null;
            this.NextChaChaEmoteAtMs = 0;
            this.LastChaChaEmote = -1;
            return;
        }

        foreach (GameLocation location in Game1.locations)
        {
            foreach (NPC npc in location.characters
                         .Where(p => string.Equals(p.Name, ChaChaNpcId, StringComparison.OrdinalIgnoreCase))
                         .ToList())
            {
                location.characters.Remove(npc);
            }
        }

        this.ChaChaActor = null;
        this.NextChaChaEmoteAtMs = 0;
        this.LastChaChaEmote = -1;
    }

    /// <summary>
    /// Give ChaCha occasional Stardew overhead reactions so the companion feels expressive
    /// even when ChaCha isn't speaking. Dialogue uses a shorter cooldown; normal wandering stays subtle.
    /// </summary>
    public void UpdateChaChaEmotes(bool dialogueActive = false)
    {
        if (!Context.IsWorldReady)
            return;

        NPC? actor = this.FindChaChaActor();
        if (actor is null
            || actor.isInvisible.Value
            || actor.currentLocation != Game1.currentLocation)
        {
            return;
        }

        long now = Environment.TickCount64;
        if (now < this.NextChaChaEmoteAtMs)
            return;

        int emote = ChaChaEmotePool[Game1.random.Next(ChaChaEmotePool.Length)];
        if (ChaChaEmotePool.Length > 1 && emote == this.LastChaChaEmote)
            emote = ChaChaEmotePool[(Array.IndexOf(ChaChaEmotePool, emote) + 1 + Game1.random.Next(ChaChaEmotePool.Length - 1)) % ChaChaEmotePool.Length];

        // false/false = no extra sound and never advance an Event command.
        actor.doEmote(emote, false, false);
        this.LastChaChaEmote = emote;

        int minDelay = dialogueActive ? 3300 : 7000;
        int maxDelay = dialogueActive ? 6200 : 12500;
        this.NextChaChaEmoteAtMs = now + Game1.random.Next(minDelay, maxDelay + 1);
    }

    public void TriggerChaChaEmote(int emote)
    {
        if (!Context.IsWorldReady)
            return;

        NPC? actor = this.FindChaChaActor();
        if (actor is null || actor.isInvisible.Value || actor.currentLocation != Game1.currentLocation)
            return;

        actor.doEmote(emote, false, false);
        this.LastChaChaEmote = emote;
        this.NextChaChaEmoteAtMs = Environment.TickCount64 + 3200;
    }

    private Texture2D? LoadMimiPortraitTexture()
    {
        if (this.MimiPortraitTexture is not null)
            return this.MimiPortraitTexture;

        try
        {
            this.MimiPortraitTexture = Game1.content.Load<Texture2D>(MimiPortraitAsset);
        }
        catch
        {
            this.MimiPortraitTexture = null;
        }

        return this.MimiPortraitTexture;
    }

    private static void AssignPortraitTexture(NPC npc, Texture2D? portraitTexture)
    {
        if (portraitTexture is null)
            return;

        const BindingFlags flags = BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;

        foreach (string propertyName in new[] { "Portrait", "portrait", "portraitTexture", "PortraitTexture" })
        {
            try
            {
                PropertyInfo? prop = typeof(NPC).GetProperty(propertyName, flags);
                if (prop is not null && prop.CanWrite && prop.PropertyType.IsAssignableFrom(typeof(Texture2D)))
                {
                    prop.SetValue(npc, portraitTexture);
                    return;
                }
            }
            catch
            {
            }
        }

        foreach (string fieldName in new[] { "Portrait", "portrait", "portraitTexture", "PortraitTexture" })
        {
            try
            {
                FieldInfo? field = typeof(NPC).GetField(fieldName, flags);
                if (field is not null && field.FieldType.IsAssignableFrom(typeof(Texture2D)))
                {
                    field.SetValue(npc, portraitTexture);
                    return;
                }
            }
            catch
            {
            }
        }
    }

    public void OnReturnedToTitle()
    {
        this.ChaChaActor = null;
        this.NextChaChaEmoteAtMs = 0;
        this.LastChaChaEmote = -1;
    }
}
