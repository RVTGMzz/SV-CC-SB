# Alpha 28 / 0696D1S — Real Airship Motion Repair

## Status
- Branch: `cardcha-alpha28-0696d1s-airship-motion-repair`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.68`
- Visual acceptance: **PENDING-RON-VISUAL**

## Root cause
D1R incorrectly interpreted `observation_window_overlay_1..4.png` as four animation frames. They are not. Overlay 1 contains the visible sky/airship scene, while overlays 2–4 are window/transition slices. Cycling them therefore made vertical window columns appear to fly across the view.

## D1S correction
- legacy four-overlay cycling is completely disabled;
- the real airship is extracted from the approved `.67` Window source as one transparent sprite;
- the original static airship placement is patched out of the map-native Window source;
- runtime moves only that airship sprite across four center-pane positions;
- no window pillar, frame, plant, lamp, telescope or scenery slice is animated;
- D2 season/time/weather matrix is still deferred.

## Evidence
- extracted sprite size: **15x9**
- extracted opaque sprite pixels: **84**
- runtime positions: **[(62, 33), (71, 33), (80, 33), (89, 33)]**
- old overlay cycling active: **FALSE**

## Next gate
Ron checks the D1S preview/TEST. If the airship motion is visually accepted, proceed to D2 and apply the same independent-airship concept to the season/time/weather matrix.
