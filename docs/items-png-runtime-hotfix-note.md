# items.png runtime hotfix

The Airship Visual Polish artifact exposed a runtime SMAPI failure for `assets/items.png`: the PNG had a valid signature and dimensions but an invalid IDAT CRC. CI only checked the signature/dimensions/hash and therefore missed decoder validation.

Hotfix action: replace `src/Cardcha/assets/items.png` with a freshly re-encoded valid PNG preserving the 112x16 RGBA sheet content, then add a real decoder validation to future packaging checks.
