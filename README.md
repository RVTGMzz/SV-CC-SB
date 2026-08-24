# Cardcha: Shardbound v0.1.17-alpha.11.10 — MiMi Dialogue Compile Fix

This build keeps the alpha.11.8 visual pass, alpha.11.9 broom arrival/departure fixes, and corrects the Stardew 1.6 `Dialogue` constructor used by the portrait flow.

## Current test behavior
- Mystery MiMi appears in Town during the temporary 10:00–15:00 test window.
- MiMi arrives and departs by broom instead of disappearing instantly.
- ChaCha remains beside MiMi until he is lent to the player.
- MiMi world sprites have the +15% visual scale / clarity pass from alpha.11.8–11.9.
- Floating `???` above MiMi is removed.

## Portrait rule
Before MiMi reveals her identity, the dialogue name is still **`???`**, but the portrait must still be **MiMi's portrait**. The mystery is only in the displayed name; it does not hide or replace her face portrait.

## alpha.11.10 compile hotfix
- Fixed the Stardew 1.6 `Dialogue` constructor order from the invalid `new Dialogue(text, speaker)` to `new Dialogue(speaker, text)`.
- MiMi remains the actual NPC speaker even while her display name is `???`, allowing Stardew's NPC dialogue box to load `Portraits/Ronvotri.Cardcha_MiMi`.
- Keeps alpha.11.9 broom arrival/departure behavior and visual clarity pass.

## Full-source GitHub sync
The Windows Builder contains `SYNC_TO_GITHUB.bat`. Run it once on the Windows PC to push the complete source + runtime assets into this private repository while preserving repository history.
