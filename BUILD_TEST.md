# Cardcha v0.1.17-alpha.11.41 — Circular HUD Test

1. Build/install with Stardew + SMAPI fully closed.
2. Run `cardcha_version`; it must report `v0.1.17-alpha.11.41 CIRCULAR HUD ACTIVE`.
3. Equip combat cards and verify the HUD appears as **circular icons in one horizontal row at top-center**.
4. Trigger more than three eligible states; the HUD must never show more than **3 circles**.
5. Verify priority remains `KÍCH HOẠT / ACTIVATED` > `SẴN SÀNG / READY` > normal `BUFF`.
6. Chain Hunter: verify the circle shows an integer countdown and the small timer ring shrinks as time runs out. Stack badge should show e.g. `3/5`.
7. Blood Fang cooldown: verify the circle shows the cooldown integer and depleting ring.
8. Phoenix Heart ready: verify green ring + check marker.
9. Trigger Blood Fang/Phoenix: verify purple pulsing ring + `!` marker for the activation toast.
10. Move the mouse over each circle. Tooltip should show name, state, effect description, and time/stacks when relevant.
11. Touch a circle if testing Android/touch input; the same tooltip should be readable.
12. Watch circles appear/disappear: fade/slide should remain soft, with no snapping.
13. Check 720p/1080p and UI scaling if convenient; the 3-circle group must remain centered and compact.
14. Regression: stationary Cardcha machine and portable machine + ChaCha fetch still open/pull normally.
