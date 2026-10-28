# Cereal-box filament lid — v1 (as printed and in use, 2026-10-26)

Lid, spool hanger and silica boxes for an existing cereal box, holding one 200 mm spool. Printed on a Bambu Lab A1 mini
(0.4 nozzle, Textured PEI, no glue) in Bambu PETG Basic + eSUN TPU 95A Clear.
**This folder is the working home from now on.** v2 will be built from the learnings at the bottom.

```
v1/
  print/    CerealLid_v1_PETG_A1mini.3mf, CerealLid_v1_TPU_eSUN_A1mini.3mf   (ready to print)
  stl/      the 19 parts exactly as printed (frozen, validated - see "Validation")
  source/   cereal_lid.py (FreeCAD model), run_cereal_lid.py, CerealLid.FCStd, make_*.py
  source/bambu/   Bambu Studio CLI build scripts + profiles; outputs land here
  source/stl_cereal/   build area: run_cereal_lid.py writes ALL STLs here (wiped on every run)
  tools/    Tool_BitDriver_PETG_A1mini.3mf (90 deg bit driver for the seam screws)
  renders/  spool_change.mp4
```

## Parts in use

| Part (stl/) | Qty | Material | Version / notes |
|---|---|---|---|
| `Lid_L`, `Lid_R` | 1+1 | PETG | Two halves joined at x = 0 with 10 × M3 + heat-set inserts (4 × 5). Lid_R has a built-in breakaway support in the outlet pocket |
| `TPU_SeamStrip` | 1 | TPU | 1 mm gasket between the two halves |
| `TPU_Grommet` | 1 | TPU | The ORIGINAL (tighter) grommet, taken from the 2026-10-24 PLA-test project. It is NOT the later loosened one in cereal_lid.py |
| `TPU_CapTether` | 1 | TPU | Cap on a strap, with a tapered anchor peg pressed into the pocket hole |
| `Latch_x4` | 4 | PETG | +2 mm longer reach, 2 mm locking ridge, snaps onto printed pivot stubs |
| `Hanger_A`, `Hanger_B` | 1+1 | PETG | Mirrored pair. Bayonet S-track with a climbing exit. Dovetail with 3 crush ribs (0.35 grip, parallel flanks) |
| `Axle_8mm_x88_Grip` | 1 | PETG 100 % | Necks in both hangers, Ø11 collar (+Y), 8 mm shoulder (−Y), 5 grip ribs at the collar-end 608 |
| `HubAdapter_x2` | 2 | PETG | Straight spigot for a ~55 mm hole (Ø54.2 + 8 ribs, 0.6 mm proud), 608 bearing pocket |
| `SilicaBox_L` (rounded) / `_R` | 1+1 | PETG | Sliding covers (45 deg grooves, snug last 3 mm), slide-bolt locks, crush ribs, 2 handle holes (L) |
| `SilicaBoxCover_L/R` | 1+1 | PETG | |
| `SilicaLockBolt_x6` | 6 | PETG | 2 per side on L (x −72, −40), 1 per side on R (x 40) |
| `SilicaBoxHandle_v2` | 1 | PETG | Ledge legs through the L box holes, **locked with a piece of 1.75 filament** through the leg holes (the printed bar was too tight) |
| `HygroCradle_NoSupport` | 1 | PETG | Mini hygrometer mount, prints on its back with no supports. Pocket 44.9 × 25.9 × 13.3 for the user's hygrometer (body 44.5 × 25.5 × 13 + face 47.5 × 28 × 2). Its face sits ~1 mm off the box wall. Slides into the lid's cradle dovetails |
| `HygroCradle_Old_48x28` + `HygroShim_OldCradle` | 1+1 | PETG | The second hygrometer mount: the first (upright) cradle sized for 48 × 28.6, with the glue-in shim that resizes it to the same pocket |

Bought or reused parts: 2 × 608 bearings, 10 × M3 screws + inserts, and the old lid's gasket (3.25 × 6 mm, cut to **583 mm**).
Not part of v1: the test parts in cereal_lid.py (snap, slide and spring-lock hangers, puller).

## Print files

| File | Plates | Time |
|---|---|---|
| `print/CerealLid_v1_PETG_A1mini.3mf` | 1 Lid L · 2 Lid R · 3 Hangers + axle · 4 Adapters ×2 + latches ×4 · 5 Silica boxes · 6 Covers + bolts ×6 + handle · 7 Hygrometer cradle (no support) | ~13.0 h |
| `print/CerealLid_v1_Hygro_OldCradle_Shim_PETG_A1mini.3mf` | Old upright cradle + glue-in shim (the second mount) | ~0.6 h |
| `print/CerealLid_v1_TPU_eSUN_A1mini.3mf` | Seam strip + grommet + cap ("eSUN TPU 95A Clear @BBL A1M" user preset, 230/235 °C, 3 mm³/s, feed from the external spool) | ~0.5 h |

Settings: 0.20 mm layers, 4 walls, 15 % gyroid (the axle at 100 %), 5 mm brim on the PETG parts. Every part prints without supports.

## How to work here

```bash
# 1. rebuild the model + all STLs (-> source/stl_cereal, source/CerealLid.FCStd)
"C:\Users\SK\AppData\Local\Programs\FreeCAD 1.1\bin\freecadcmd.exe" C:\Users\SK\Desktop\Personal\CerealFilamentLid\v1\source\run_cereal_lid.py
# 2. Bambu projects (run inside source/bambu; 3MFs are written there). "|" separates plates
python make_latch_trial_petg.py MyParts_PETG_A1mini.3mf "PartA:1,PartB:2|PartC:1"
python make_tpu_parts.py MyTPU_A1mini.3mf "TPU_SeamStrip:1,TPU_CapTether:1"
```
To rebuild the v1 print files exactly, first copy `stl/TPU_Grommet.stl` to `source/stl_cereal/TPU_Grommet_v1old.stl` and
`stl/HygroCradle_Old_48x28.stl` into `source/stl_cereal/`, because step 1 wipes that folder. Both are old versions the
current source no longer generates. Then run:
`make_latch_trial_petg.py CerealLid_v1_PETG_A1mini.3mf "Lid_L:1|Lid_R:1|Hanger_A:1,Hanger_B:1,Axle_8mm_x88_Grip:1|HubAdapter_x2:2,Latch_x4:4|SilicaBox_L:1,SilicaBox_R:1|SilicaBoxCover_L:1,SilicaBoxCover_R:1,SilicaLockBolt_x6:6,SilicaBoxHandle_v2:1|HygroCradle_Mini:1"`,
`make_latch_trial_petg.py CerealLid_v1_Hygro_OldCradle_Shim_PETG_A1mini.3mf "HygroCradle_Old_48x28:1,HygroShim_OldCradle:1"`
and `make_tpu_parts.py CerealLid_v1_TPU_eSUN_A1mini.3mf "TPU_SeamStrip:1,TPU_Grommet_v1old:1,TPU_CapTether:1"`.
The axle gets 100 % infill through `SOLID` in make_cereal_pla_test.py.

Model settings for v1: `HANG_MODE = "bayonet"`, axle `make_axle(grip=True)`, handle `make_sbox_handle2()`.
Gotchas:
- Always run the model in a fresh namespace (the runner does). Stale globals can hide deleted constants.
- The FreeCAD GUI MCP can stall while a mouse button is held in the 3D view. If it does, use freecadcmd.
- The Bambu CLI only takes system presets. TPU is sliced as Generic TPU + overrides, then re-pointed at the eSUN user preset.
- Bambu Studio may switch the filament back when the 3MF is re-saved.

## Dimensions reference (all mm)

**Coordinates (as in cereal_lid.py):** origin at the box centre, on the top of the rim. x runs along the length (+x is the front, where the
outlet, hygrometer and Lid_R are). y runs across the width (+y is the side with Hanger_B). z points up (z = 0 is the rim top, the lid top is z = 30).

### Box (measured by the user, 2026-10-07)
| What | Value | Constant |
|---|---|---|
| Inner length | 220 | `BOX_IL` |
| Inner width | 91–94 (varies along the length) | `BOX_IW_MIN/MAX` |
| Wall | 2 | `WALL` |
| Outer corner radius of the rim | 30 (computed from the ~590 outer perimeter, **not measured**) | `R_BOX` |
| Rim wall above the flange | 7.5 | `RIM_H` |
| Flange: sticks out / thickness | 3.5 / 3.35 → flange underside at z = −10.85 | `FLANGE_OUT`, `FLANGE_T` |
| Groove under the flange (latch ridge seat) | centre 1.75 in from the flange edge, 1.5 deep, 2 wide (**assumed position**) | `RIM_GROOVE_*` |
| Inside depth below the rim top | 210 | `BOX_DEPTH` |
| Rim outside (half sizes) | x 112, y 47.5–49 (average 48.25) | `OX`, `OY_*` |

### Lid
| What | Value |
|---|---|
| Outside | 232.1 × 105.6 (±116.05 × ±52.8), corner R 34.05, z −6 … 30 (36 tall) |
| Top plate / skirt | 3.0 top plate (z 27–30), skirt 3.2 thick down to z −6 |
| Skirt inner face | x ±112.85, y ±49.6, R 30.85 (0.6 over the widest rim) |
| Inner locating lip | outer face x ±109.15, y ±45.0, R 27.5 (0.5 clearance to the narrowest wall), down to z −4 |
| Perimeter band inner face | y ±42 (long sides), x ±105.5 (ends) → lid cavity for the silica boxes |
| Seam | at x = 0. 1 mm TPU strip. 10 × M3 at (y, z): (±16.5, 5), (±8, 5), (±12, 20), (±16.5, 13), (±27, 17), heads on the +X face |
| Outlet | grommet bore Ø10 at x 76, cap anchor hole Ø4.2 × 9 at x 100, inside a stadium pocket R10 × 6 deep in the lid top |
| Hanger dovetail sockets | y 29 → 41.5 (open towards the middle, closed at the wall), \|x\| 12 → 15, z 1–7 |
| Hygrometer cradle sockets | x 84–95, \|y\| 12–24, 6 tall (dovetails, slide towards the front) |

### Gasket
| What | Value |
|---|---|
| Groove | 3.5 wide × 4.8 deep, centred over the rim wall |
| Groove centreline | rounded rectangle, half sizes 111 × 47.25, R 29 → **583 mm long** (`GCX/GCY/GCR`) |
| Groove edges | inner x 109.25 / y 45.5, outer x 112.75 / y 49.0 |
| Gasket | old lid's strip 3.25 wide × 6 tall, on edge, cut to 583. Stands 1.2 proud, squeezed 0.5 when latched (band underside at z 0.7 = `SEAT`) |

### Latches and rim
| What | Value |
|---|---|
| Positions | x = ±55 on both long sides (4 latches), 24 wide |
| Pivot | y 49.5, z 12 (over-centre, self-locking). Hub R4.5 with a 3.4 C-opening that snaps onto Ø4 × 2.5 stubs in the lid |
| Lip | tip at y 49.2. Lip top at z −10.55 (0.3 preload above the flange underside) **+2.0 extra reach** (`LATCH_EXTRA`) |
| Locking ridge | 2.0 tall, 2.6 base / 1.0 tip, centred at y 50.0 → into the flange groove |

### Spool, hanger, axle
| What | Value |
|---|---|
| Spool | Ø200 × 67 wide (**width assumed**, must be ≤ 69), hub hole ~55 (user) |
| Axle centre | z −106 (spool clears the floor by 4, top 6 below the rim) |
| Hanger plate | y 36.5–41.25 (4.75 thick) → 73.0 between the inner faces. Arm hangs to z −118 |
| Bayonet track | 6.2 wide. Path from the seat: −7 sideways, +5 up, −16 sideways, −5 down, −16 out climbing 4 |
| Axle | 88.2 long, Ø7.9 (D-flat), necks Ø5.8 × 5.55 at both hangers (0.4 play per side), Ø11 × 2 collar (+Y), grip ribs 0.25 at y 21.6–28.6 |
| Hub adapter | flange Ø66 × 2, spigot Ø54.2 × 12 + 8 ribs, 608 pocket 22.15 × 7.2 |

### Silica boxes
| What | Value |
|---|---|
| Boxes | L (rounded end) x −105.2 … −11, R x 11 … 62, y ±42.1, z 1 … 26.7. 0.3 gap to the lid. Capacity ~124 + 60 cm³ (~138 g beads) |
| Walls / floor | 2.4 / 2.0. Floor bead slots 1.2 wide at a 4.5 pitch |
| Locks | slide bolts reach 1.0 into the lid band groove (z 5.5–8.5) |
| Crush ribs | 0.4 proud at x −80, −56, −28, 26, 54 |
| Handle holes (L) | 6.4 × 3.2 at x −95.1, y ±12 |

## Validation (2026-10-26)
Every file in `stl/` and `print/` was checked against the 3MF it was actually printed from, by triangle count, volume and size.
All match exactly:

| Parts | Printed from |
|---|---|
| Lid_L/R, seam strip, grommet | `CerealLid_PLA_test_A1mini.saved-by-bambu.3mf` |
| Latches | `LatchSet_long2_ridge2_PETG_A1mini.3mf` |
| Cap | `TPU_OutletParts_eSUN_A1mini.3mf` |
| Hangers, adapters | `SpoolHolder_PETG_A1mini.3mf` |
| Axle | grip axle test |
| Silica boxes, covers, bolts | `SilicaSlideBoxes_PETG_A1mini.3mf` |
| Handle | `SilicaHandle_v2_LockBar_PETG_A1mini.3mf` |
| No-support hygrometer cradle | `HygroCradle_NoSupport_PETG_A1mini.3mf` |
| Shim | `HygroShim_OldCradle_PETG_A1mini.3mf` |
| Old cradle | extracted from the PLA-test project |

Rebuilding from `source/` reproduces all 17 model-generated parts identically. The grommet and the old cradle are extracted meshes.

## Learnings for v2
- **Spool change:** the bayonet works, but the spool wobbles when the lid is flipped, and the axle has to line up with both
  hangers at once (fiddly). Next idea: a spring-return slide lock with Ø6.6 axle heads (`make_spring_hanger`, the user's spring
  is 5 OD × 0.6 wire × 10 long, ~5.5 squeezed flat). It's in source/, untested.
- **Hangers** (4.75 thick, 106 long) bend sideways, ~0.6 mm/N. Thicken them (the spring version adds 2.2 on the spool
  side, ~2.7× stiffer). Axle heads that catch the outer faces tie the two hangers together.
- **Spool hub:** the first cone adapter (60 → 48) couldn't seat in a 55 hole, and the straight spigot fixed it. Measure the spool width.
- **Rounded silica box** is tight in the lid and hard to pull. Reduce its crush ribs or clearance. Size the handle lock holes for
  1.75 filament (~2.0).
- **TPU (eSUN 95A)** is firm, so use small press-fits and long lead-in tapers. The original tight grommet works.
- **Hygrometer** (body 44.5 × 25.5 × 13 + face 47.5 × 28 × 2): the first cradle was sized for a 48 × 28.6 unit, so it was loose.
  The fix was the resized no-support cradle, plus the shim for the old cradle. Measure parts before sizing pockets.
- **To measure for v2:** original latch-pocket position on the box, real rim corner radius, the flange-groove position at the
  latches, and the spool width.
