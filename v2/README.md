# Cereal-box filament lid — v2 (fully parametric FreeCAD)

v2 is the **whole set** as native **PartDesign** with every dimension editable. Open `CerealLid_v2.FCStd` in FreeCAD 1.1;
no Python is needed to work on it. It starts from v1's proven geometry, checked part by part against v1 (see
"Validation"). The few deliberate differences are listed below. `../v1/README.md` has the box measurements, learnings and
the printed v1 set.

```
v2/
  CerealLid_v2.FCStd     THE MODEL: edit this
  build_v2.py            generator that created it (re-running OVERWRITES the .FCStd: only to start fresh)
  export_v2.py           model -> print-oriented STLs in stl_cereal/
  bambu/make_v2_projects.py   stl_cereal/ -> print/ (Bambu Studio 3MFs, same settings as v1)
  print/                 CerealLid_v2_PETG_A1mini.3mf (6 plates, ~14.3 h, ~447 g), CerealLid_v2_TPU_eSUN_A1mini.3mf (~0.5 h)
  stl_cereal/            last export
  tools/                 bit_driver_v2.py: compact 90° driver, 1/4" + 4 mm sockets (sizes at the top of the file)
                         Tool_BitDriver_Dual_FitTest_PETG_A1mini.3mf: plate 1 socket fit test, plate 2 driver
```

## What's in the model (tree folders)

| Folder | Objects | Notes |
|---|---|---|
| `Params` | spreadsheet | **all dimensions** (313 named values in 13 groups, with notes; derived values are formulas) |
| 1 Reference | `BoxRef`, `Gasket` | the cereal box rim, and the old lid's gasket strip in its groove (`Params.G_LEN` = length to cut) |
| 2 Lid | `Lid` (body) → `Lid_L`, `Lid_R`, `SeamStrip` (split at x = ±SEAM); `Latch` + `Latch_1..4` (links at ±LATCH_X) | |
| 3 Spool hanger | `Hanger_B` (body, +Y) → `Hanger_A` (mirror); `HubHalfA`, `HubHalfB`, `HubRetainer`, `StubAxle`, `StubClip` (bodies, hidden) + `HubHalfA/B_Asm`, `HubRetainer_A/B`, `StubAxle_A/B`, `StubClip_A/B` (links in place) | bayonet S-track with climbing exit, dovetail crush ribs 0.35, screw-together hub (see below) |
| 4 Silica | `SilicaBox_L` (rounded), `SilicaBox_R`, `SilicaBoxCover_L/R`, `LockBolt` + `LockBolt_1..6`, `SilicaBoxHandle` | sliding covers (45° grooves, snug ramp), slide-bolt locks, handle with a filament lock hole |
| 5 Outlet (TPU) | `Grommet`, `CapTether` (+ `*_InLid` links) | modelled at the origin in print orientation, linked into the lid's outlet recesses |
| 6 Hygrometer | `HygroCradle` | no-support cradle for the 44.5 × 25.5 × 13 hygrometer (+ 47.5 × 28 × 2 face) |
| 7 Split cutters | boxes used for the lid split | hidden |

Parts are modelled **in assembly position** (except the hub parts, grommet and cap, which are modelled in their own
frame and placed by links. Hub frame: axis = z, z = distance from the spool centre; the A side links are rotated 180°). `export_v2.py` rotates each part into its print orientation.

## How to edit

1. **A dimension:** open `Params`, change column B, then Recompute (Ctrl+R).
   - Derived rows such as `LX`, `SB_HX`, `HG_ZC`, `G_LEN` and `HOOK_E` are formulas: change their inputs instead.
   - Tested with box width/length/corner, latch x/width, groove width, outlet x, lid height, crush ribs, spool width,
     track rise, hygrometer width, grommet press and slot pitch. Each rebuilt with no errors and kept every sketch fully constrained.
2. **A shape:** double-click a sketch, e.g. `HangerPlateSketch`, `LatchProfileSketch` or `WallsSketch`.
   - The latch profile and hub come as sets of 3 sketches: the middle one plus `...RightSketch` and `...LeftSketch` for the chamfered side bands. Change all three if you edit by hand; Params edits apply to all three.
   - Dimensions bound to `Params` show as f(x). To override one, right-click → Expression → clear it.
   - The seam screw positions (`InsertHolesSketch` / `BoltHolesSketch`) are plain values.
3. **New features:** activate the body (double-click it) and use the PartDesign tools. In any input field, press `=` and type
   `Params.NAME` so the new feature stays parametric.
4. **Print:** run `export_v2.py` (freecadcmd), then `python bambu/make_v2_projects.py`.

```bash
"C:\Users\SK\AppData\Local\Programs\FreeCAD 1.1\bin\freecadcmd.exe" C:\Users\SK\Desktop\Personal\CerealFilamentLid\v2\export_v2.py
```
```bash
python C:\Users\SK\Desktop\Personal\CerealFilamentLid\v2\bambu\make_v2_projects.py
```

Coordinates: origin at the box centre on the rim top. x runs along the length (+x is the front: outlet, hygrometer, Lid_R),
y runs across (+y is the Hanger_B side), z points up (z = 0 is the rim top). Sketch offsets: XY sketches along +z, XZ
sketches along −y, YZ sketches along +x. Each sketch's `AttachmentOffset` is bound to Params.

## Print files (`print/`)

| File | Plates |
|---|---|
| `CerealLid_v2_PETG_A1mini.3mf` | 1 Lid L · 2 Lid R (45° outlet cones, no support) · 3 Hangers A+B + stub axles ×2 (100 %) + retainers ×2 + clips ×4 + hygrometer cradle · 4 Hub halves A+B + latches ×4 · 5 Silica boxes · 6 Covers + lock bolts ×6 + handle |
| `CerealLid_v2_Hub_only_PETG_A1mini.3mf` | just the new hub: halves A+B, retainers ×2, stub axles ×2 (100 %), clips ×4 (~2.9 h) |
| `CerealLid_v2_TPU_eSUN_A1mini.3mf` | Seam strip + grommet + tethered cap ("eSUN TPU 95A Clear @BBL A1M") |

Settings: A1 mini, 0.4 nozzle, Textured PEI, 0.20 mm layers, 4 walls, 15 % gyroid, PETG brim 5 mm. No supports
(Lid_R's outlet recesses are 45° cones that print top-face-down with no support; only the 6 mm strap channel
bridges. The v1 breakaway support grid is gone).
Finish: **scarf seams** (`seam_slope_type` all, seam at the back) hide the seam line and zit (set in `bambu/profiles.py`, v2 copy only).
The lid top prints face-down on the textured sheet, which is the best finish that face can get. Every part stays in its flat,
support-free orientation (strongest layers, best fits); 45° tilting was considered and not used.

## Differences from v1 (deliberate)

| What | v1 | v2 | Why |
|---|---|---|---|
| Silica box crush ribs `SBOX_CRUSH` | 0.4 | **0.3** | the rounded box was tight in the lid. 0.3 into the 0.3 gap = just touching |
| Silica box floor slots under the lock blocks | cut through the block bottoms | blocks solid | slightly stronger, no other change |
| Cover detent bump | 0.5 proud (round, centre 0.1 up) | 0.5 proud half-round | same click |
| Grommet | the original tight mesh (older profile) | current profile (long lead-in, ramped rings) at the **original tight fit**: `GROM_PRESS` 0.2 / `GROM_RIB` 0.5 | eSUN 95A: set 0.05 / 0.25 for an easy fit |
| Handle lock | printed bar | **a piece of 1.75 filament** through the 2.15 hole (what works) | |
| Box reference depth | 230 | `BOX_DEPTH` 210 | measured value |
| Seam screws | 10 × M3 | **6 × M3** at (y, z): (±23, 17), (±12, 18.5), (±10, 6) | the user uses 6. Ends moved in from ±27 (the bit shaft hit the hanger blocks there); every screw now clears a 90° driver head (checked) |
| Lid edge chamfers | sharp | 45° `LID_CH_TOP` 1.0 (top outer edge = print bed edge), `LID_CH_BOT` 0.8 (skirt bottom) | no sharp edges, no elephant foot. Built as tapered pads/pocket, so they follow every Params change |
| Latch + notch edges (finger / hand) | sharp | latch: 45° `LATCH_CH` 0.6 on every side-face edge (latch and hub = middle pad + 2 tapered side bands), `LATCH_EDGE_CH` 0.8 on the top outer corner and the finger tab's bottom corners; lid notches: 45° `SLOT_CH` 0.8 round the notch on the outer skirt **and on the lid top** | user: these scratched fingers. The latches still clear the lid, and the pivot stubs engage as before. The ridge is now `LW - 2*LATCH_CH` long |
| Silica slide-bolt locks | flat tunnel roof (8.3 mm bridge: sagged, bolt tight), top detent bump, `LOCK_CLR` 0.15 | tunnel roof is a 45° gable (`LOCK_PEAK`) through the block and the wall; bolt has a matching gable back and a flat 2.2 mm tip (`LOCK_TIP_L` 1.8) for the lid snap groove; `LOCK_CLR` 0.25; detent = vertical ridges on both bolt sides into grooves in the tunnel walls (0.2 click); switch slot bed edge chamfered `LOCK_SLOT_CH` 0.5 (elephant foot). Bolt prints standing on its inner end | no bridges anywhere in the lock; slides free at both ends, clicks between. **Reprint the silica boxes and the 6 bolts together** (old bolts don't fit the new tunnels) |
| Outlet recess | flat 20 mm stadium pocket, 6 mm deep (bridged floor, needed the support grid) | 45° cone recesses: grommet cone `GROM_CONE_D` 7 from the lid top to the bore top (`GROM_ZB`), anchor cone `ANCHOR_CONE_D` 4.5 / `ANCHOR_CONE_R0` 2.6, joined by a strap channel `STRAP_CH_W` 6 × `STRAP_CH_D` 4.5. Grommet cone rim rounded `OUT_RND` 1.5 (groove, true arc) | prints with no support and no flat bridge. The rounded rim and the grommet's chamfered funnel mouth (`GROM_MOUTH_CH` 0.8) stop the filament scraping when pulled sideways |
| Grommet / cap / anchor (TPU) | flat Ø18 flange, flat Ø14 cap disc, flat anchor head | grommet flange is a 45° cone (`GROM_FL_R2` 7.5, 0.1 press on the lid cone = light seal); cap disc a 45° cone (`CAP_R2` / `CAP_R1`, `CAP_T` 2.0) whose top sits `CAP_RECESS` 2.5 below the lid top; `CAP_GAP` 1.2 radial gap round the cap edge (lever it out with a pick / small screwdriver); pull tab `TAB_L` 11.5 × `TAB_W` 5 opposite the strap, over a finger slot (`TAB_SLOT_W` 6.5, `TAB_SLOT_GAP` 1 under the tab, `TAB_SLOT_CH` 1 flare); anchor head a 45° cone, 0.2 clear; `TETHER_L` = `PARK_X - OUT_X` (24), strap lies straight in its channel | **reprint the TPU grommet and cap**: the v1 ones don't fit the cone recesses |
| Spool hub (2026-10-27) | one-piece axle through the hangers with grip ribs; 2 push-in hub adapters with a 608 press pocket | **screw-together hub**: `HubHalfB` (sleeve, female) + `HubHalfA` (male tube) joined by a 2-start 45° thread (`HUB_LEAD` 8, `HUB_TD` 1.5, `HUB_CLR` 0.25) through the spool hole; screw them together to clamp the spool between the knurled flanges (6 mm of adjustment for narrower spools). Each half: 608 in a pocket with a 45° lip cone over a flat seat ring (`SEAT_R`), held by a threaded **retainer** ring (`RET_R` 14, pitch 2, coin slots) screwed in behind it; 45° cone from the retainer recess to the pocket. **Stub axle** per side, pushed in from outside: Ø18 collar (`STUB_COL_R`) against the hanger, neck in the track, shoulder on the inner race, clip groove inside; printed **C-clip** (`CLIP_OPEN` 0.85 = test clip 2) snaps on sideways. Pull on a stub → clip → inner race → balls → retainer → half: nothing slides out. Track floor lowered to the round neck (`HG_ZC`), 0.1 mm | user: adapters hard to pull out, axle slid out, bearings loose. Fits checked in PETG test prints (thread, retainer, clips, stub, bearing). Every flat overhang replaced by 45° after test 1. Halves print flange-down, stub on its collar |

## Validation (2026-10-26)

Each v2 body was compared with the v1 generator output by volume of v1-only and v2-only material:

| Result | Parts |
|---|---|
| **0.000 cm³ difference** (before the chamfers; they remove only the 3 chamfer bands, 0.49 cm³) | Lid, Latch, Gasket, Hanger_B, HubAdapter (since replaced), LockBolt, SilicaBoxHandle, SilicaBoxCover_L/R (up to 0.003), Grommet (at v1's tight fit), CapTether, HygroCradle |
| Within 0.001 cm³ | Axle (rib section; since replaced by the stub axles) |
| Differs as intended | SilicaBox_L/R: +0.21 / +0.04 cm³, the solid lock blocks |

Assembly check in place: the only contacts are the designed ones (dovetail crush ribs, cover snug ramps, grommet press fit).
The axle, adapters, latches, cradle, boxes, bolts and handle are all clear.
Hub (2026-10-27): no clashes between halves, retainers, 608s, stubs, clips and hangers in place; half A screws into B through a full turn in the tightening direction with 0 overlap (and clashes the other way: right-hand thread); retainers screw out cleanly.

## Still open / to measure
- Rim corner radius `R_BOX` (computed 30), flange-groove position `RIM_GROOVE_C` (assumed 1.75), and the original latch pockets
- Spool width `SPOOL_W` (assumed 67, must fit 73 − 2 × `HUB_FL_T`; the hub halves follow it via `HUB_U`)
- Ideas from v1 still to try: stiffer hangers (thicker on the spool side), a better flip-safe spool change
