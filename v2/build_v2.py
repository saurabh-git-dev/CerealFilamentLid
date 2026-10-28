"""Cereal-box filament lid v2 - builds a fully PARAMETRIC FreeCAD document (native PartDesign).

Every dimension lives in the "Params" spreadsheet; sketches are fully constrained and their dimensions are
expressions pointing at Params, pads/pockets take their lengths from Params as well. Edit a Params cell (or
override a sketch dimension by hand) and recompute - no Python needed to work on the result.

This script only GENERATES the starting document (geometry identical to v1, which fits the box). After that,
edit CerealLid_v2.FCStd directly; re-running this script overwrites it.

Run:  "C:\\Users\\SK\\AppData\\Local\\Programs\\FreeCAD 1.1\\bin\\freecadcmd.exe" build_v2.py
  or in the FreeCAD GUI Python console: exec(open(r"...\\v2\\build_v2.py").read())

Coordinates: origin at the box centre on the rim top; x along the length (+x = front: outlet, hygrometer, Lid_R),
y across (+y = Hanger_B side), z up (rim top z = 0, lid top z = ZT).
"""
import math
import os

import FreeCAD as App
import Part
import Sketcher

V = App.Vector
HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else \
    r"C:\Users\SK\Desktop\Personal\CerealFilamentLid\v2"
OUT = os.path.join(HERE, "CerealLid_v2.FCStd")

# ---------------------------------------------------------------- parameters
# (name, value or "=formula", comment).  Lengths in mm.  Formulas may use the other names.
PARAMS = [
    ("# BOX (measured 2026-10-07)", None, ""),
    ("BOX_IL", 220, "inner length"),
    ("BOX_IW_MIN", 91, "inner width, narrowest"),
    ("BOX_IW_MAX", 94, "inner width, widest"),
    ("WALL", 2, "box wall"),
    ("R_BOX", 30, "OUTER corner radius of the rim (computed from the 590 perimeter - MEASURE)"),
    ("RIM_H", 7.5, "rim wall height above the flange"),
    ("FLANGE_OUT", 3.5, "flange sticks out"),
    ("FLANGE_T", 3.35, "flange thickness"),
    ("BOX_DEPTH", 210, "inside depth below the rim top"),
    ("RIM_GROOVE_C", 1.75, "groove under the flange: centre in from the flange edge (ASSUMED - measure)"),
    ("RIM_GROOVE_D", 1.5, "groove depth"),
    ("RIM_GROOVE_W", 2.0, "groove width"),
    ("OX", "=BOX_IL / 2 + WALL", "rim outside half length (112)"),
    ("OY_MAX", "=BOX_IW_MAX / 2 + WALL", "rim outside half width, widest"),
    ("OY_MIN", "=BOX_IW_MIN / 2 + WALL", "rim outside half width, narrowest"),
    ("OY_AVG", "=(OY_MAX + OY_MIN) / 2", "rim outside half width, average"),
    ("R_BOX_IN", "=R_BOX - WALL", "inner corner radius"),
    ("FLANGE_BOT", "=-RIM_H - FLANGE_T", "flange underside z (-10.85)"),
    ("# GASKET", None, ""),
    ("G_W_STRIP", 3.25, "gasket strip width (old lid's gasket)"),
    ("G_T", 6.0, "gasket strip height (stands on edge)"),
    ("G_GROOVE_W", 3.5, "groove width"),
    ("G_RECESS", 4.8, "groove depth"),
    ("G_SQUEEZE", 0.5, "squeeze when latched"),
    ("SEAT", "=G_T - G_RECESS - G_SQUEEZE", "lid band underside z when latched (0.7)"),
    ("GCX", "=OX - WALL / 2", "groove centreline half length"),
    ("GCY", "=(BOX_IW_MIN + BOX_IW_MAX) / 4 + WALL / 2", "groove centreline half width"),
    ("GCR", "=R_BOX - WALL / 2", "groove centreline corner radius"),
    ("GIX", "=GCX - G_GROOVE_W / 2", ""), ("GIY", "=GCY - G_GROOVE_W / 2", ""), ("GIR", "=GCR - G_GROOVE_W / 2", ""),
    ("GOX", "=GCX + G_GROOVE_W / 2", ""), ("GOY", "=GCY + G_GROOVE_W / 2", ""), ("GOR", "=GCR + G_GROOVE_W / 2", ""),
    ("G_LEN", "=4 * (GCX - GCR) + 4 * (GCY - GCR) + 2 * pi * GCR", "GASKET LENGTH to cut (centreline)"),
    ("# LID", None, ""),
    ("ZT", 30, "lid top z"),
    ("PLATE_T", 3, "top plate thickness"),
    ("PLATE_Z0", "=ZT - PLATE_T", "top plate underside"),
    ("SKIRT_T", 3.2, "skirt thickness"),
    ("SKIRT_BOT", -6, "skirt bottom z"),
    ("SKIRT_CLR", 0.6, "skirt inner face clearance over the widest rim"),
    ("BAND_IN", 42, "inner face of the perimeter band, long sides (|y|)"),
    ("BAND_IN_X", 105.5, "inner face of the band, ends (|x|)"),
    ("CAV_R", "=R_BOX_IN - 4", "cavity corner radius"),
    ("LIP_CLR", 0.5, "inner lip clearance to the narrowest inner wall"),
    ("LIP_BOT", -4, "inner lip bottom z"),
    ("LIP_X", "=BOX_IL / 2 - LIP_CLR < GIX - 0.1 ? BOX_IL / 2 - LIP_CLR : GIX - 0.1", "inner lip outer face |x|"),
    ("LIP_Y", "=BOX_IW_MIN / 2 - LIP_CLR < GIY - 0.1 ? BOX_IW_MIN / 2 - LIP_CLR : GIY - 0.1", "inner lip outer face |y|"),
    ("LIP_R", "=R_BOX_IN - LIP_CLR", "inner lip corner radius"),
    ("SKX", "=OX + SKIRT_CLR > GOX + 0.1 ? OX + SKIRT_CLR : GOX + 0.1", "skirt inner face |x|"),
    ("SKY", "=OY_MAX + SKIRT_CLR > GOY + 0.1 ? OY_MAX + SKIRT_CLR : GOY + 0.1", "skirt inner face |y|"),
    ("R_SK", "=R_BOX + SKIRT_CLR > GOR + 0.1 ? R_BOX + SKIRT_CLR : GOR + 0.1", "skirt inner corner radius"),
    ("LX", "=SKX + SKIRT_T", "lid outside half length"),
    ("LY", "=SKY + SKIRT_T", "lid outside half width"),
    ("R_LID", "=R_SK + SKIRT_T", "lid outside corner radius"),
    ("LID_CH_TOP", 1.0, "45 deg chamfer on the lid's top outer edge (also the print bed edge: no elephant foot)"),
    ("LID_CH_BOT", 0.8, "45 deg chamfer on the skirt's bottom outer edge"),
    ("SEAM", 0.5, "half thickness of the TPU seam strip between the halves (x = 0)"),
    ("SPINE_HX", 5.5, "seam spine half thickness (x)"),
    ("SPINE_Y", 20, "full-height spine half length (|y|)"),
    ("SPINE_UPPER_Z0", 7.5, "upper spine (above the hanger slide path) bottom z"),
    ("SPINE_UPPER_Y", 33, "upper spine reaches the hanger blocks (|y|)"),
    ("BOLT_D", 3.4, "M3 clearance hole (+X half)"),
    ("M3_INSERT_D", 4.0, "M3 heat-set insert hole (-X half)"),
    ("BOLT_HOLE_L", 5.6, "hole depth each side of the seam"),
    ("# HANGER + CRADLE SOCKETS (in the lid)", None, ""),
    ("HB_HX", 18.5, "hanger socket block half length (x)"),
    ("HB_Y0", 30, "hanger socket block inner end (|y|)"),
    ("DT_Z0", 1.0, "dovetail socket bottom (opening) z"),
    ("DT_Z1", 7.0, "dovetail socket ceiling z"),
    ("DT_HALF0", 12.0, "socket half width at the opening"),
    ("DT_HALF1", 15.0, "socket half width at the ceiling"),
    ("DT_Y0", 29.0, "socket open end (|y|)"),
    ("DT_OUT", 41.5, "socket closed end (|y|)"),
    ("CRADLE_Z1", -4.5, "hygrometer cradle mounting face z"),
    ("CD_N0", 14.0, "cradle socket |y| at the opening, inner"),
    ("CD_N1", 22.0, "cradle socket |y| at the opening, outer"),
    ("CD_W0", 12.0, "cradle socket |y| at the ceiling, inner"),
    ("CD_W1", 24.0, "cradle socket |y| at the ceiling, outer"),
    ("CD_H", 6.0, "cradle socket height"),
    ("CD_X0", 84.0, "cradle socket open end x"),
    ("CD_X1", 95.0, "cradle socket closed end x"),
    ("# OUTLET (lid top pocket)", None, ""),
    ("OUT_X", 76.0, "grommet x"),
    ("PARK_X", 100.0, "cap tether anchor hole x"),
    ("POCKET_R", 10.0, "outlet block half width less its wall (block round the recesses)"),
    ("POCKET_WALL", 3.0, "outlet block wall"),
    ("GROM_BORE", 10.0, "grommet bore"),
    ("GROM_L", 12.0, "grommet bore depth below the cone recess"),
    ("GROM_CONE_D", 7.0, "45 deg cone recess (lid top -> bore): prints top-face-down with no bridge / support"),
    ("GROM_ZB", "=ZT - GROM_CONE_D", "cone recess bottom = bore top z"),
    ("CAP_RECESS", 2.5, "cap top below the lid top"),
    ("OUT_RND", 1.5, "rounding radius on the outlet cone rim (filament rubs here when pulled sideways)"),
    ("GROM_MOUTH_CH", 0.8, "45 deg chamfer on the grommet funnel mouth"),
    ("ANCHOR_CONE_D", 4.5, "anchor 45 deg cone recess depth"),
    ("ANCHOR_CONE_R0", 2.6, "anchor cone recess bottom radius"),
    ("STRAP_CH_W", 6.0, "strap channel width between the two recesses (6 mm bridge, fine)"),
    ("STRAP_CH_D", 4.5, "strap channel depth"),
    ("PTFE_R", 3.0, "PTFE passage radius below the grommet"),
    ("ANCHOR_HOLE_D", 4.2, "cap anchor hole"),
    ("ANCHOR_HOLE_L", 9.0, "cap anchor hole depth"),
    ("# SILICA BOX SNAP GROOVES (in the band)", None, ""),
    ("SNAP_X1", -72, "groove 1 x"), ("SNAP_X2", -40, "groove 2 x"), ("SNAP_X3", 40, "groove 3 x"),
    ("SNAP_HL", 9, "groove half length"),
    ("SNAP_DEPTH", 1.2, "groove depth into the band (each way of the face)"),
    ("BOX_SNAP_Z", 7.0, "groove centre z"),
    ("SNAP_HH", 1.5, "groove half height"),
    ("# LATCHES (4: x = +-LATCH_X both sides)", None, ""),
    ("LATCH_X", 55, "latch centre |x|"),
    ("LW", 24, "latch width"),
    ("SLOT_CLR", 0.3, "lid slot clearance each side of the latch"),
    ("PY", 49.5, "pivot |y|"),
    ("PZ", 12.0, "pivot z"),
    ("HUB_R", 4.5, "hub radius"),
    ("STUB_D", 4.0, "pivot stub diameter (on the lid slot walls)"),
    ("STUB_L", 2.5, "stub length into the hub"),
    ("C_OPEN", 3.4, "hub C-opening (snaps over the stubs)"),
    ("ARM_I", 53.3, "arm inner face |y|"),
    ("ARM_T", 3.5, "arm thickness"),
    ("ARM_O", "=ARM_I + ARM_T", "arm outer face |y|"),
    ("LIP_TIP", 49.2, "lip tip |y|"),
    ("LATCH_PRELOAD", 0.3, "nominal lip top above the flange underside"),
    ("LATCH_EXTRA", 2.0, "extra reach (tested: closes with the gasket, ridge clicks)"),
    ("LTE", "=FLANGE_BOT + LATCH_PRELOAD - LATCH_EXTRA", "lip top z"),
    ("TAB_BOT", "=LTE - 8", "finger tab bottom z"),
    ("LATCH_CH", 0.6, "45 deg chamfer on every edge of the latch's two side faces (finger-friendly)"),
    ("LATCH_EDGE_CH", 0.8, "chamfer on the latch's top outer corner and finger-tab bottom corners"),
    ("SLOT_CH", 0.8, "45 deg chamfer round the latch notches on the lid's outer skirt"),
    ("BUMP_H", 2.0, "locking ridge height"),
    ("BUMP_BASE", 2.6, "ridge base width"),
    ("BUMP_TIP", 1.0, "ridge tip width"),
    ("BUMP_Y", "=OY_AVG + FLANGE_OUT - RIM_GROOVE_C", "ridge centre |y|"),
    ("BUMP_Y0", "=BUMP_Y - BUMP_BASE / 2 > LIP_TIP ? BUMP_Y - BUMP_BASE / 2 : LIP_TIP", ""),
    ("BUMP_T0", "=BUMP_Y - BUMP_TIP / 2 > LIP_TIP ? BUMP_Y - BUMP_TIP / 2 : LIP_TIP", ""),
    ("# SPOOL + BAYONET HANGERS (Hanger_B = +Y, Hanger_A = its mirror)", None, ""),
    ("SPOOL_D", 200, "spool diameter"),
    ("SPOOL_W", 67, "spool width across the flanges (ASSUMED - measure)"),
    ("SPOOL_HOLE", 55, "spool hub hole"),
    ("D_AXLE", "=BOX_DEPTH - SPOOL_D / 2 - 4", "axle centre below the rim top (spool 4 above the floor)"),
    ("HG_Y0", 36.5, "hanger plate inner face |y|"),
    ("HG_Y1", 41.25, "hanger plate outer face |y|"),
    ("HG_TOP_HX", 18, "hanger top half width"),
    ("HG_KNEE_X", 12, "hanger right edge x at axle height"),
    ("HG_FOOT", 12, "hanger bottom below the axle"),
    ("HG_LEFT_Z", 40, "left edge kink above the axle"),
    ("DT_TENON_Y0", 33.25, "dovetail tenon inner end |y|"),
    ("DT_SEAT", 0.3, "tenon modelled this far above the socket flanks (ribs press it down)"),
    ("DT_TOP_GAP", 0.2, "tenon top gap to the socket ceiling before pressing"),
    ("DT_K", "=(DT_HALF1 - DT_HALF0) / (DT_Z1 - DT_Z0)", "flank slope"),
    ("TEN_ZT", "=DT_Z1 - DT_TOP_GAP", "tenon top z"),
    ("TEN_XB", "=DT_HALF0 - DT_K * DT_SEAT", "tenon half width at z DT_Z0"),
    ("TEN_XT", "=DT_HALF0 + DT_K * (TEN_ZT - DT_Z0 - DT_SEAT)", "tenon half width at the top"),
    ("DT_RIB_GRIP", 0.35, "dovetail crush-rib grip (tested: 3 notch = 0.35)"),
    ("DT_RIB_W", 1.2, "crush rib width"),
    ("DT_RIB_RAMP", 2.5, "rib lead-in ramp"),
    ("DT_RIB_PITCH", 8, "rib spacing (3 ribs)"),
    ("RIB_H", "=DT_TOP_GAP + DT_SEAT + DT_RIB_GRIP", "rib height above the tenon top"),
    ("AXLE_R", 3.95, "stub axle radius (8 mm bearing bore)"),
    ("AXLE_NECK_R", 2.9, "neck radius where the axle sits in the hangers"),
    ("AXLE_SLOT", "=2 * AXLE_NECK_R + 0.4", "bayonet track width"),
    ("HG_H", "=AXLE_SLOT / 2", "track half width"),
    ("HG_ZC", "=-D_AXLE - (AXLE_NECK_R + 0.05) + HG_H", "track centre-line z (round stub neck on the flat floor)"),
    ("HG_FLOOR", "=HG_ZC - HG_H", "track floor z"),
    ("HOOK_STEP1", 7, "track: sideways"), ("HOOK_RISE", 5, "track: up"), ("HOOK_STEP2", 16, "track: sideways"),
    ("HOOK_EXIT", 16, "track: exit sideways"), ("HOOK_EXIT_RISE", 4, "exit climbs this much (flip-safe)"),
    ("HOOK_EXIT_WIDEN", 0.8, "exit wider (axle flat corners clear)"),
    ("HOOK_B", "=HOOK_STEP1 + HOOK_STEP2", ""), ("HOOK_E", "=HOOK_B + HOOK_EXIT", ""),
    ("HOOK_EXIT_L", "=sqrt(HOOK_EXIT ^ 2 + HOOK_EXIT_RISE ^ 2)", ""),
    ("HW_EX", "=HG_H + HOOK_EXIT_WIDEN", "exit half width"),
    ("EXN_X", "=-HOOK_EXIT_RISE / HOOK_EXIT_L * HW_EX", "exit side offset x"),
    ("EXN_Z", "=-HOOK_EXIT / HOOK_EXIT_L * HW_EX", "exit side offset z"),
    ("# SCREW-TOGETHER HUB: 2 halves (2-start thread), 608 per half held by a screwed retainer, stub axle per side", None, ""),
    ("# local frame of every hub body: axis = z, z = |y| from the spool centre (B at +Y, A = rotated 180 deg)", None, ""),
    ("HUB_U", "=SPOOL_W / 2", "flange inner face (spool flange face)"),
    ("HUB_FL_R", 33, "flange radius"), ("HUB_FL_T", 2, "flange thickness"),
    ("HUB_KNURL_N", 24, "flange grip scallops"), ("HUB_KNURL_R", 1.4, "scallop radius"),
    ("HUB_SP_R", "=SPOOL_HOLE / 2 - 0.4", "spigot / sleeve outside radius"),
    ("HUB_LEAD", 8, "big thread lead (2 starts -> pitch 4)"), ("HUB_STARTS", 2, "thread starts"),
    ("HUB_TD", 1.5, "thread depth (45 deg flanks)"), ("HUB_CREST", 0.4, "thread crest width"),
    ("HUB_M_ROOT", 23.1, "male (A) thread root radius"),
    ("HUB_CLR", 0.25, "thread clearance (tested OK)"),
    ("HUB_BORE_A", 20, "A thread tube inside radius"),
    ("HUB_SLEEVE_END", -2, "B sleeve reaches past the centre to z"),
    ("HUB_A_SMOOTH", 8, "A smooth spigot ends at z (6 mm screw adjustment gap)"),
    ("HUB_A_END", 21, "A thread tube tip (|z| on the far side of the centre)"),
    ("HUB_SP_IN", 24.5, "A smooth spigot inside radius"),
    ("HUB_END_T", 3, "A end wall (spigot -> thread tube), 45 deg cone underneath"),
    ("HUB_THR_Z0", -18.5, "A male thread start (profile centre, A frame)"),
    ("HUB_THR_H", 23.5, "A male thread helix height"),
    ("HUB_GRV_Z0", "=-HUB_THR_Z0 - 6 * HUB_LEAD / HUB_STARTS", "B groove start (= -male start mod pitch -> the modelled halves mesh)"),
    ("HUB_GRV_H", 32, "B groove helix height (A can screw 6 mm past home for narrower spools)"),
    ("HUB_BOSS_R", 18.5, "bearing boss radius"),
    ("LIP_U", "=HUB_U - 11", "boss inner end (lip)"),
    ("POCKET_U", "=HUB_U - 9.5", "608 seat face"),
    ("RECESS_U", "=HUB_U - 2.5", "608 outer face = retainer inner face"),
    ("BRG_R", 11.075, "608 pocket radius"), ("SEAT_R", 10.6, "flat seat ring 10.6..11.075, 45 deg lip cone above"),
    ("RET_R", 14.0, "retainer thread major radius"), ("RET_P", 2.0, "retainer thread pitch"),
    ("RET_TD", 0.7, "retainer thread depth"), ("RET_CREST", 0.25, "retainer thread crest"),
    ("RET_HOLE", 8.25, "retainer hole radius (clears the inner race)"),
    ("RET_Z0", "=RECESS_U + 1", "retainer thread start (same in housing + retainer: they mesh)"),
    ("AXLE_PLAY", 0.4, "neck play each side of the hanger plate"),
    ("AXLE_N0", "=HG_Y0 - AXLE_PLAY", "neck inner end |y|"),
    ("AXLE_N1", "=HG_Y1 + AXLE_PLAY", "neck outer end |y|"),
    ("STUB_COL_R", 9.0, "big outer collar (sits against the hanger)"), ("STUB_COL_T", 2.5, "collar thickness"),
    ("AXLE_TIP_CH", 0.6, "stub tip chamfer"),
    ("STUB_TIP_U", "=POCKET_U - 3.5", "stub inner tip"),
    ("STUB_SH_R", 5.5, "shoulder on the inner race (outer face)"), ("STUB_SH_L", 1.5, "shoulder length"),
    ("CLIP_U", "=POCKET_U - 1.5", "clip on the inner race (inner face): start"),
    ("CLIP_T", 1.4, "clip thickness"), ("CLIP_GD", 0.6, "clip groove depth"), ("CLIP_R", 5.6, "clip outside radius"),
    ("CLIP_OPEN", 0.85, "clip opening / groove diameter (test clip 2)"),
    ("# SILICA BOXES (L = long/rounded, R = short) + sliding covers", None, ""),
    ("SBOX_L_X0", -105.6, "long box x range (its -X end follows the rounded lid cavity)"),
    ("SBOX_L_X1", -19, "long box inner (seam-side) end x"),
    ("SBOX_R_X0", 19, "short box inner (seam-side) end x"),
    ("SBOX_R_X1", 62, "short box outer end x (ends before the outlet block)"),
    ("SBOX_CLR", 0.3, "gap to the lid cavity walls / ceiling (0.4 rattled)"),
    ("SBOX_Z0", 1.0, "box bottom z"),
    ("SBOX_W", 2.4, "wall thickness"),
    ("SBOX_FLOOR", 2.0, "floor thickness"),
    ("SBOX_CRUSH", 0.3, "crush ribs proud (v1 0.4: rounded box was TIGHT in the lid)"),
    ("CRUSH_X1", -80, ""), ("CRUSH_X2", -56, ""), ("CRUSH_X3", -28, ""), ("CRUSH_X4", 26, ""), ("CRUSH_X5", 54, ""),
    ("BEAD_SLOT", 1.2, "floor / end-wall slot width (beads >= 2 mm)"),
    ("SLOT_PITCH", 4.5, "floor slot pitch"),
    ("SB_HX", "=BAND_IN_X - SBOX_CLR", "box outer half length (cavity less clearance)"),
    ("SB_HY", "=BAND_IN - SBOX_CLR", "box outer half width"),
    ("SB_R", "=CAV_R - SBOX_CLR", "box outer corner radius"),
    ("SB_WI", "=SB_HY - SBOX_W", "long wall inner face |y|"),
    ("SB_XS", "=SB_HX - SB_R", "|x| up to which the long walls are straight"),
    ("SBOX_TOP", "=PLATE_Z0 - SBOX_CLR", "box top z"),
    ("SLIDE_T", 2.2, "cover thickness"),
    ("SLIDE_LIP", 1.0, "wall left above the cover groove"),
    ("SLIDE_GROOVE_D", 1.2, "cover groove depth into the long walls"),
    ("SLIDE_GROOVE_H", 1.8, "groove height at the mouth (45 deg roof)"),
    ("SLIDE_CLR", 0.3, "cover side clearance"),
    ("SLIDE_VCLR", 0.3, "tongue clearance top and bottom"),
    ("SLIDE_SNUG", 0.4, "groove floor ramp under the tongue tip: snug for the last ~3 mm"),
    ("SLIDE_TAB", 4.0, "cover finger tab past the inner end"),
    ("SLIDE_G1", "=SBOX_TOP - SLIDE_LIP", "groove roof z (at the mouth)"),
    ("SLIDE_GF", "=SLIDE_G1 - SLIDE_GROOVE_H", "groove floor z"),
    ("SLIDE_CT", "=SLIDE_G1 - SLIDE_VCLR", "cover top z"),
    ("SLIDE_G0", "=SLIDE_CT - SLIDE_T", "cover underside z = lowered inner end wall top"),
    ("SLIDE_TIP", "=SB_WI + SLIDE_GROOVE_D - SLIDE_CLR", "tongue tip |y|"),
    ("LOCK_X1", -72, "slide lock x (long box)"), ("LOCK_X2", -40, "slide lock x (long box)"),
    ("LOCK_X3", 40, "slide lock x (short box)"),
    ("LOCK_W", 8.0, "bolt width"), ("LOCK_Z0", 5.9, "bolt bottom z"), ("LOCK_Z1", 8.1, "bolt top z"),
    ("LOCK_LEN", 12.0, "bolt length"), ("LOCK_REACH", 1.3, "bolt tip past the wall when locked"),
    ("LOCK_TRAVEL", 1.6, "bolt throw"), ("LOCK_CLR", 0.25, "tunnel clearance (was 0.15: too tight)"),
    ("LOCK_PEAK", "=LOCK_W / 2 + LOCK_CLR", "tunnel roof is a 45 deg gable this high (box prints floor-down: no bridge)"),
    ("LOCK_TIP_L", 1.8, "bolt's flat tip (fits the lid's snap groove); the rest of the bolt has a matching gable back"),
    ("LOCK_SLOT_CH", 0.5, "45 deg chamfer on the switch slot's bed edge (eats the elephant foot)"),
    ("LOCK_YT", "=SB_HY + LOCK_REACH", "bolt tip |y| locked"),
    ("LOCK_YIN", "=LOCK_YT - LOCK_LEN - LOCK_TRAVEL", "bolt inner end |y| unlocked"),
    ("HANDLE_X", -95.1, "long-box handle hole centre x"), ("HANDLE_Y", 12.0, "handle legs |y|"),
    ("HANDLE_T", 6.0, "handle thickness"),
    ("HANDLE_HOLE_X", "=HANDLE_T + 0.4", "handle hole x size"), ("HANDLE_HOLE_Y", 3.2, "handle hole y size"),
    ("HBAR_HOLE", 2.15, "lock hole in the handle legs (a piece of 1.75 filament locks it)"),
    ("HBAR_Z", "=SBOX_FLOOR + 0.05 + HBAR_HOLE / 2", "lock hole centre above the floor's outer face"),
    ("# OUTLET TPU (eSUN 95A): grommet in the 10 mm bore + tethered cap", None, ""),
    ("GROM_FL_R2", 7.5, "grommet 45 deg cone flange: wide radius (0.1 over the lid cone = light seal)"),
    ("GROM_PRESS", 0.2, "grommet body oversize per side in the bore (0.2 = the original TIGHT fit in use; 0.05 = loose)"),
    ("GROM_RIB", 0.5, "grip-ring oversize per side (0.5 original tight; 0.25 loose)"),
    ("GROM_CLEAR", 4.3, "grommet bore for the 4 mm PTFE tube"),
    ("GROM_LIP", 3.4, "sealing lip bore"),
    ("CAP_T", 2.0, "cap 45 deg cone disc height"),
    ("CAP_GAP", 1.2, "radial gap round the cap edge (room for a pick / small screwdriver to lever the cap out)"),
    ("CAP_R2", "=GROM_BORE / 2 + GROM_CONE_D - CAP_RECESS - CAP_GAP", "cap cone top radius"),
    ("CAP_R1", "=CAP_R2 - CAP_T", "cap cone bottom radius"),
    ("TAB_L", 11.5, "pull tab tip from the cap centre (opposite the strap)"),
    ("TAB_W", 5.0, "pull tab width (thickness = STRAP_T)"),
    ("TAB_SLOT_W", 6.5, "finger slot width in the lid past the tab tip"),
    ("TAB_SLOT_GAP", 1.0, "finger slot floor below the tab (room for a fingernail)"),
    ("TAB_SLOT_CH", 1.0, "45 deg flare on the finger slot at the lid top"),
    ("CAP_PEG_D", 4.3, "cap peg diameter (seals in the grommet lips)"), ("CAP_PEG_L", 8.0, "cap peg straight length"),
    ("FIL_HOLE", 2.0, "filament hole through the cap"),
    ("ANCHOR_D", 4.35, "tether anchor peg diameter (light press in ANCHOR_HOLE_D)"),
    ("TETHER_L", "=PARK_X - OUT_X", "cap centre to anchor centre (strap lies straight in its channel)"), ("STRAP_W", 3.5, "strap width"), ("STRAP_T", 1.0, "strap thickness"),
    ("# HYGROMETER CRADLE (no supports: prints on its back)", None, ""),
    ("MH_L", 44.5, "hygrometer body width"), ("MH_W", 25.5, "hygrometer body height"), ("MH_D", 13.0, "body depth"),
    ("MH_FL", 47.5, "face plate width"), ("MH_FW", 28.0, "face plate height"), ("MH_FT", 2.0, "face plate thickness"),
    ("MH_DROP", 5.5, "pocket lowered below the rim band"),
    ("HY_FACE_X", 107.0, "cradle front x (the face sits in front of it)"),
    ("HY_TOP", -7.5, "reference top of the hygrometer zone"),
    ("CR_BX0", 85.0, "cradle back plate x (flush with the dovetail ends)"),
    ("CD_CLR", 0.15, "cradle dovetail clearance"),
    ("CR_HB", "=HY_FACE_X - MH_D - 0.3", "hygrometer back stop x"),
    ("CR_HW", "=MH_L / 2 + 0.25", "pocket half width"),
    ("CR_HH", "=MH_W + 0.5", "pocket height"),
    ("CR_ZT", "=HY_TOP - MH_DROP", "pocket top z"),
    ("CR_ZB", "=CR_ZT - CR_HH - 2", "cradle bottom z"),
]
# M3 seam bolts (y, z) - edit directly in the sketches "InsertHoles" / "BoltHoles"
# 6 screws (user uses 6): ends moved in from 27 -> 23 and the lower pair spread 8 -> 10 / raised 5 -> 6, so a
# 90 deg driver head fits (hanger blocks start at |y| 30, band underside at z 0.7, top plate at z 27)
SEAM_BOLTS = [(-23.0, 17.0), (23.0, 17.0), (-12.0, 18.5), (12.0, 18.5), (-10.0, 6.0), (10.0, 6.0)]


MATHNS = {"pi": math.pi, "sqrt": math.sqrt, "floor": math.floor, "ceil": math.ceil, "abs": abs,
          "sin": lambda d: math.sin(math.radians(d)), "cos": lambda d: math.cos(math.radians(d))}


def py_values():
    """Evaluate PARAMS in Python (same formulas) -> initial numeric values for the sketch solver."""
    P = dict(MATHNS)
    for name, val, _ in PARAMS:
        if val is None:
            continue
        if isinstance(val, str):
            f = val[1:]
            if "?" in f:                                  # a < b ? c : d
                cond, rest = f.split("?")
                a, b = rest.split(":")
                f = "(%s) if (%s) else (%s)" % (a, cond, b)
            P[name] = float(eval(f.replace("^", "**"), {}, P))
        else:
            P[name] = float(val)
    return P


P = py_values()


def ev(expr):
    return float(eval(expr.replace("Params.", "").replace("^", "**"), dict(MATHNS), P))


def X(name):
    """'LX' -> 'Params.LX'; anything with an operator is used as written (with Params. prefixed names)."""
    return expr_of(name)


def expr_of(e):
    if isinstance(e, (int, float)):
        return str(e)
    out, tok = [], ""
    for ch in e + " ":
        if ch.isalnum() or ch == "_":
            tok += ch
        else:
            if tok:
                out.append("Params." + tok if tok in P and tok not in MATHNS else tok)
                tok = ""
            out.append(ch)
    return "".join(out).strip()


# ---------------------------------------------------------------- sketch builder
class SB:
    """Fully constrained sketch geometry whose dimensions are expressions on Params."""

    def __init__(self, sk):
        self.sk = sk

    def _dim(self, ctype, g, pos, e):
        """DistanceX / DistanceY from the sketch origin to (g, pos) = expression e (0 -> on the axis)."""
        sk = self.sk
        if isinstance(e, (int, float)) and e == 0:
            return sk.addConstraint(Sketcher.Constraint("PointOnObject", g, pos, -2 if ctype == "DistanceX" else -1))
        c = sk.addConstraint(Sketcher.Constraint(ctype, -1, 1, g, pos, ev(expr_of(e))))
        if not isinstance(e, (int, float)):
            sk.setExpression("Constraints[%d]" % c, expr_of(e))
        return c

    def _radius(self, g, e):
        c = self.sk.addConstraint(Sketcher.Constraint("Radius", g, ev(expr_of(e))))
        if not isinstance(e, (int, float)):
            self.sk.setExpression("Constraints[%d]" % c, expr_of(e))

    def rrect(self, hx, hy, r):
        """Centred rounded rectangle, half sizes hx, hy, corner radius r."""
        sk = self.sk
        HX, HY, R = ev(expr_of(hx)), ev(expr_of(hy)), ev(expr_of(r))
        a, b = HX - R, HY - R
        g = [sk.addGeometry(Part.LineSegment(V(-a, HY, 0), V(a, HY, 0))),
             sk.addGeometry(Part.LineSegment(V(HX, b, 0), V(HX, -b, 0))),
             sk.addGeometry(Part.LineSegment(V(a, -HY, 0), V(-a, -HY, 0))),
             sk.addGeometry(Part.LineSegment(V(-HX, -b, 0), V(-HX, b, 0)))]
        arc = lambda cx, cy, a0, a1: sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(cx, cy, 0), V(0, 0, 1), R),
                                                                     math.radians(a0), math.radians(a1)))
        A = [arc(a, b, 0, 90), arc(a, -b, 270, 360), arc(-a, -b, 180, 270), arc(-a, b, 90, 180)]
        T = lambda g1, p1, g2, p2: sk.addConstraint(Sketcher.Constraint("Tangent", g1, p1, g2, p2))
        T(g[0], 2, A[0], 2); T(A[0], 1, g[1], 1); T(g[1], 2, A[1], 2); T(A[1], 1, g[2], 1)
        T(g[2], 2, A[2], 2); T(A[2], 1, g[3], 1); T(g[3], 2, A[3], 2); T(A[3], 1, g[0], 1)
        sk.addConstraint(Sketcher.Constraint("Horizontal", g[0]))
        sk.addConstraint(Sketcher.Constraint("Horizontal", g[2]))
        sk.addConstraint(Sketcher.Constraint("Vertical", g[1]))
        sk.addConstraint(Sketcher.Constraint("Vertical", g[3]))
        for k in (1, 2, 3):
            sk.addConstraint(Sketcher.Constraint("Equal", A[0], A[k]))
        self._radius(A[0], r)
        sk.addConstraint(Sketcher.Constraint("Symmetric", A[0], 3, A[2], 3, -1, 1))
        self._dim("DistanceX", g[1], 1, hx)
        self._dim("DistanceY", g[0], 1, hy)

    def half_round(self, cx, cy, r, up):
        """Half disc on the line y = cy (bulging up if up, else down), centre cx, radius r."""
        sk = self.sk
        CX, CY, R = (ev(expr_of(e)) for e in (cx, cy, r))
        a0, a1 = (0, math.pi) if up else (math.pi, 2 * math.pi)
        arc = sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(CX, CY, 0), V(0, 0, 1), R), a0, a1))
        ln = sk.addGeometry(Part.LineSegment(V(CX - R, CY, 0), V(CX + R, CY, 0)))
        sk.addConstraint(Sketcher.Constraint("Coincident", arc, 1, ln, 2 if up else 1))
        sk.addConstraint(Sketcher.Constraint("Coincident", arc, 2, ln, 1 if up else 2))
        self._dim("DistanceX", arc, 3, cx)
        self._dim("DistanceY", arc, 3, cy)
        self._radius(arc, r)
        self._dim("DistanceY", arc, 1, cy)
        self._dim("DistanceY", arc, 2, cy)

    def rrect_cut(self, hx, hy, r, xc):
        """Centred rounded rectangle (half sizes hx, hy, radius r) with its +X end cut straight at x = xc."""
        sk = self.sk
        HX, HY, R, XC = (ev(expr_of(e)) for e in (hx, hy, r, xc))
        a, b = HX - R, HY - R
        L0 = sk.addGeometry(Part.LineSegment(V(XC, HY, 0), V(-a, HY, 0)))
        At = sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(-a, b, 0), V(0, 0, 1), R), math.pi / 2, math.pi))
        L1 = sk.addGeometry(Part.LineSegment(V(-HX, b, 0), V(-HX, -b, 0)))
        Ab = sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(-a, -b, 0), V(0, 0, 1), R), math.pi, 1.5 * math.pi))
        L2 = sk.addGeometry(Part.LineSegment(V(-a, -HY, 0), V(XC, -HY, 0)))
        L3 = sk.addGeometry(Part.LineSegment(V(XC, -HY, 0), V(XC, HY, 0)))
        T = lambda g1, q1, g2, q2: sk.addConstraint(Sketcher.Constraint("Tangent", g1, q1, g2, q2))
        T(L0, 2, At, 1); T(At, 2, L1, 1); T(L1, 2, Ab, 1); T(Ab, 2, L2, 1)
        sk.addConstraint(Sketcher.Constraint("Coincident", L2, 2, L3, 1))
        sk.addConstraint(Sketcher.Constraint("Coincident", L3, 2, L0, 1))
        sk.addConstraint(Sketcher.Constraint("Horizontal", L0))
        sk.addConstraint(Sketcher.Constraint("Horizontal", L2))
        sk.addConstraint(Sketcher.Constraint("Vertical", L1))
        sk.addConstraint(Sketcher.Constraint("Vertical", L3))
        sk.addConstraint(Sketcher.Constraint("Equal", At, Ab))
        self._radius(At, r)
        self._dim("DistanceX", L3, 1, xc)
        self._dim("DistanceX", L1, 1, "-(%s)" % hx if isinstance(hx, str) else -hx)
        self._dim("DistanceY", L0, 1, hy)
        self._dim("DistanceY", L2, 1, "-(%s)" % hy if isinstance(hy, str) else -hy)

    def rim_round(self, ax, rt, zt, f):
        """Groove profile rounding the rim where a 45 deg cone recess (radius rt at the top face z = zt, axis
        x = ax) meets the top face: radius f arc tangent to both, plus a construction axis line (Axis0)."""
        sk = self.sk
        rc = "%s + (%s) + (%s) * (sqrt(2) - 1)" % (ax, rt, f)          # arc centre x (tangent point on the top)
        t2 = "%s - (%s) / sqrt(2)" % (rc, f)                           # tangent point on the cone, x
        RC, T2, ZT, F, AX = (ev(expr_of(e)) for e in (rc, t2, zt, f, ax))
        arc = sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(RC, ZT - F, 0), V(0, 0, 1), F),
                                              math.pi / 2, 3 * math.pi / 4))
        L = [sk.addGeometry(Part.LineSegment(V(RC, ZT, 0), V(RC, ZT + 0.5, 0))),
             sk.addGeometry(Part.LineSegment(V(RC, ZT + 0.5, 0), V(T2, ZT + 0.5, 0))),
             sk.addGeometry(Part.LineSegment(V(T2, ZT + 0.5, 0), V(T2, ZT - F + F / math.sqrt(2), 0)))]
        C = lambda g1, p1, g2, p2: sk.addConstraint(Sketcher.Constraint("Coincident", g1, p1, g2, p2))
        C(arc, 1, L[0], 1); C(L[0], 2, L[1], 1); C(L[1], 2, L[2], 1); C(L[2], 2, arc, 2)
        sk.addConstraint(Sketcher.Constraint("Vertical", L[0]))
        sk.addConstraint(Sketcher.Constraint("Horizontal", L[1]))
        sk.addConstraint(Sketcher.Constraint("Vertical", L[2]))
        self._dim("DistanceX", arc, 3, rc)
        self._dim("DistanceY", arc, 3, "%s - (%s)" % (zt, f))
        self._radius(arc, f)
        self._dim("DistanceX", arc, 1, rc)
        self._dim("DistanceX", arc, 2, t2)
        self._dim("DistanceY", L[1], 1, "%s + 0.5" % zt)
        ax_ln = sk.addGeometry(Part.LineSegment(V(AX, 0, 0), V(AX, 10, 0)), True)
        sk.addConstraint(Sketcher.Constraint("Vertical", ax_ln))
        self._dim("DistanceX", ax_ln, 1, ax)
        self._dim("DistanceY", ax_ln, 1, 0)
        self._dim("DistanceY", ax_ln, 2, 10)

    def rect(self, x0, x1, y0, y1):
        sk = self.sk
        X0, X1, Y0, Y1 = (ev(expr_of(e)) for e in (x0, x1, y0, y1))
        g = [sk.addGeometry(Part.LineSegment(V(X0, Y0, 0), V(X1, Y0, 0))),
             sk.addGeometry(Part.LineSegment(V(X1, Y0, 0), V(X1, Y1, 0))),
             sk.addGeometry(Part.LineSegment(V(X1, Y1, 0), V(X0, Y1, 0))),
             sk.addGeometry(Part.LineSegment(V(X0, Y1, 0), V(X0, Y0, 0)))]
        for k in range(4):
            sk.addConstraint(Sketcher.Constraint("Coincident", g[k], 2, g[(k + 1) % 4], 1))
        sk.addConstraint(Sketcher.Constraint("Horizontal", g[0]))
        sk.addConstraint(Sketcher.Constraint("Horizontal", g[2]))
        sk.addConstraint(Sketcher.Constraint("Vertical", g[1]))
        sk.addConstraint(Sketcher.Constraint("Vertical", g[3]))
        self._dim("DistanceX", g[0], 1, x0)
        self._dim("DistanceY", g[0], 1, y0)
        self._dim("DistanceX", g[1], 2, x1)
        self._dim("DistanceY", g[1], 2, y1)

    def poly(self, pts):
        sk = self.sk
        num = [(ev(expr_of(x)), ev(expr_of(y))) for x, y in pts]
        n = len(pts)
        g = [sk.addGeometry(Part.LineSegment(V(*num[k], 0), V(*num[(k + 1) % n], 0))) for k in range(n)]
        for k in range(n):
            sk.addConstraint(Sketcher.Constraint("Coincident", g[k], 2, g[(k + 1) % n], 1))
        for k, (x, y) in enumerate(pts):
            self._dim("DistanceX", g[k], 1, x)
            self._dim("DistanceY", g[k], 1, y)

    def circle(self, cx, cy, r):
        sk = self.sk
        g = sk.addGeometry(Part.Circle(V(ev(expr_of(cx)), ev(expr_of(cy)), 0), V(0, 0, 1), ev(expr_of(r))))
        self._dim("DistanceX", g, 3, cx)
        self._dim("DistanceY", g, 3, cy)
        self._radius(g, r)

    def slot(self, p0, p1, r):
        """Stadium between two arbitrary centres p0, p1 (expressions), radius r."""
        sk = self.sk
        x0, y0, x1, y1, R = (ev(expr_of(e)) for e in (p0[0], p0[1], p1[0], p1[1], r))
        a = math.atan2(y1 - y0, x1 - x0)
        nx, ny = -math.sin(a) * R, math.cos(a) * R
        top = sk.addGeometry(Part.LineSegment(V(x0 + nx, y0 + ny, 0), V(x1 + nx, y1 + ny, 0)))
        bot = sk.addGeometry(Part.LineSegment(V(x1 - nx, y1 - ny, 0), V(x0 - nx, y0 - ny, 0)))
        a1 = sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(x1, y1, 0), V(0, 0, 1), R), a - math.pi / 2, a + math.pi / 2))
        a0 = sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(x0, y0, 0), V(0, 0, 1), R), a + math.pi / 2, a + 3 * math.pi / 2))
        T = lambda g1, q1, g2, q2: sk.addConstraint(Sketcher.Constraint("Tangent", g1, q1, g2, q2))
        T(top, 2, a1, 2); T(a1, 1, bot, 1); T(bot, 2, a0, 2); T(a0, 1, top, 1)
        sk.addConstraint(Sketcher.Constraint("Equal", a0, a1))
        self._radius(a1, r)
        self._dim("DistanceX", a0, 3, p0[0]); self._dim("DistanceY", a0, 3, p0[1])
        self._dim("DistanceX", a1, 3, p1[0]); self._dim("DistanceY", a1, 3, p1[1])

    def slot_x(self, x1, x2, r):
        """Stadium along the x axis (y = 0) between centres x1 < x2, radius r."""
        sk = self.sk
        X1, X2, R = ev(expr_of(x1)), ev(expr_of(x2)), ev(expr_of(r))
        top = sk.addGeometry(Part.LineSegment(V(X1, R, 0), V(X2, R, 0)))
        bot = sk.addGeometry(Part.LineSegment(V(X2, -R, 0), V(X1, -R, 0)))
        ar = sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(X2, 0, 0), V(0, 0, 1), R), -math.pi / 2, math.pi / 2))
        al = sk.addGeometry(Part.ArcOfCircle(Part.Circle(V(X1, 0, 0), V(0, 0, 1), R), math.pi / 2, 3 * math.pi / 2))
        T = lambda g1, p1, g2, p2: sk.addConstraint(Sketcher.Constraint("Tangent", g1, p1, g2, p2))
        T(top, 2, ar, 2); T(ar, 1, bot, 1); T(bot, 2, al, 2); T(al, 1, top, 1)
        sk.addConstraint(Sketcher.Constraint("Equal", ar, al))
        self._radius(ar, r)
        self._dim("DistanceX", al, 3, x1)
        self._dim("DistanceY", al, 3, 0)
        self._dim("DistanceX", ar, 3, x2)
        self._dim("DistanceY", ar, 3, 0)


# ---------------------------------------------------------------- feature helpers
def plane(body, which):
    return [o for o in body.Origin.OriginFeatures if o.Role == which][0]


def sketch(body, name, which, offset=None, label=None, yoff=None):
    """Sketch on an origin plane. offset = expression along the plane normal
    (XY: +z, XZ: -y, YZ: +x)."""
    sk = body.newObject("Sketcher::SketchObject", name)
    sk.AttachmentSupport = [(plane(body, which), "")]
    sk.MapMode = "FlatFace"
    if offset is not None:
        if isinstance(offset, (int, float)):
            sk.AttachmentOffset = App.Placement(V(0, 0, offset), App.Rotation())
        else:
            sk.AttachmentOffset = App.Placement(V(0, 0, ev(expr_of(offset))), App.Rotation())
            sk.setExpression(".AttachmentOffset.Base.z", expr_of(offset))
    if yoff is not None:                            # shift along the sketch's own y (e.g. axle axis at z = -D)
        b = sk.AttachmentOffset.Base
        sk.AttachmentOffset = App.Placement(V(b.x, ev(expr_of(yoff)), b.z), App.Rotation())
        sk.setExpression(".AttachmentOffset.Base.y", expr_of(yoff))
    if label:
        sk.Label = label
    return sk, SB(sk)


def pad(body, name, sk, length, reversed_=False, midplane=False):
    f = body.newObject("PartDesign::Pad", name)
    f.Profile = sk
    f.Length = ev(expr_of(length))
    f.setExpression("Length", expr_of(length))
    f.Reversed = reversed_
    side(f, midplane)
    sk.Visibility = False
    return f


def side(f, midplane):
    if hasattr(f, "SideType"):
        f.SideType = "Symmetric" if midplane else "One side"
    else:
        f.Midplane = midplane


def pocket(body, name, sk, length=None, midplane=False, reversed_=False, through=False):
    f = body.newObject("PartDesign::Pocket", name)
    f.Profile = sk
    if through:
        f.Type = "ThroughAll"
    else:
        f.Length = ev(expr_of(length))
        f.setExpression("Length", expr_of(length))
    side(f, midplane)
    f.Reversed = reversed_
    sk.Visibility = False
    return f


def taper(f, angle):
    """45 deg chamfer bands: + flares outward along the extrusion (pad) / widens with depth (pocket)."""
    f.TaperAngle = angle
    return f


def revolve(body, name, sk, axis="V_Axis", angle=360):
    f = body.newObject("PartDesign::Revolution", name)
    f.Profile = sk
    f.ReferenceAxis = (sk, [axis])
    f.Angle = angle
    sk.Visibility = False
    return f


def _count(f, count_expr):
    if isinstance(count_expr, int):
        f.Occurrences = count_expr
    else:
        f.Occurrences = int(round(ev(expr_of(count_expr))))
        f.setExpression("Occurrences", expr_of(count_expr))


def polar(body, name, feats, axis_ref, count_expr, angle=360):
    prev = body.Tip
    f = body.newObject("PartDesign::PolarPattern", name)
    f.Originals = feats
    f.Axis = axis_ref
    f.Angle = angle
    _count(f, count_expr)
    f.BaseFeature = prev                # keep it in the feature chain
    body.Tip = f
    return f


def linear(body, name, feats, dir_ref, length_expr, count_expr):
    prev = body.Tip
    f = body.newObject("PartDesign::LinearPattern", name)
    f.Originals = feats
    f.Direction = dir_ref
    f.Length = ev(expr_of(length_expr))
    f.setExpression("Length", expr_of(length_expr))
    _count(f, count_expr)
    f.BaseFeature = prev
    body.Tip = f
    return f


def mirrored(body, name, feats, which):
    prev = body.Tip
    m = body.newObject("PartDesign::Mirrored", name)
    m.Originals = feats
    m.MirrorPlane = (plane(body, which), [""])
    m.BaseFeature = prev               # keep it IN the feature chain (newObject doesn't advance the Tip for these)
    body.Tip = m
    return m


# ---------------------------------------------------------------- build
def build():
    if "CerealLid_v2" in App.listDocuments():
        App.closeDocument("CerealLid_v2")
    doc = App.newDocument("CerealLid_v2")

    sh = doc.addObject("Spreadsheet::Sheet", "Params")
    sh.set("A1", "Parameter"); sh.set("B1", "Value"); sh.set("C1", "Notes")
    row = 2
    for name, val, note in PARAMS:
        if val is None:
            sh.set("A%d" % row, name.lstrip("# "))
        else:
            sh.set("A%d" % row, name)
            sh.set("B%d" % row, val if isinstance(val, str) else "=%s" % val)     # unitless = mm
            sh.setAlias("B%d" % row, name)
            sh.set("C%d" % row, note)
        row += 1
    sh.setColumnWidth("A", 160); sh.setColumnWidth("C", 520)
    doc.recompute()

    # ---------------- box reference (what the lid sits on)
    box = doc.addObject("PartDesign::Body", "BoxRef")
    s, b = sketch(box, "BoxWallSketch", "XY_Plane", 0)
    b.rrect("OX", "OY_AVG", "R_BOX"); b.rrect("OX - WALL", "OY_AVG - WALL", "R_BOX_IN")
    pad(box, "BoxWall", s, "BOX_DEPTH", reversed_=True)
    s, b = sketch(box, "FlangeSketch", "XY_Plane", "-RIM_H")
    b.rrect("OX + FLANGE_OUT", "OY_AVG + FLANGE_OUT", "R_BOX + FLANGE_OUT"); b.rrect("OX - 0.5", "OY_AVG - 0.5", "R_BOX")
    pad(box, "Flange", s, "FLANGE_T", reversed_=True)
    gc = "(FLANGE_OUT - RIM_GROOVE_C)"
    s, b = sketch(box, "RimGrooveSketch", "XY_Plane", "FLANGE_BOT + RIM_GROOVE_D")
    b.rrect("OX + %s + RIM_GROOVE_W / 2" % gc, "OY_AVG + %s + RIM_GROOVE_W / 2" % gc, "R_BOX + %s + RIM_GROOVE_W / 2" % gc)
    b.rrect("OX + %s - RIM_GROOVE_W / 2" % gc, "OY_AVG + %s - RIM_GROOVE_W / 2" % gc, "R_BOX + %s - RIM_GROOVE_W / 2" % gc)
    pocket(box, "RimGroove", s, "RIM_GROOVE_D + 1")

    # ---------------- lid (one body, split into halves below)
    lid = doc.addObject("PartDesign::Body", "Lid")
    # outer shell in three pads: chamfered bottom band, straight middle, chamfered top band (taper = 45 deg)
    s, b = sketch(lid, "ShellBottomSketch", "XY_Plane", "SKIRT_BOT")
    b.rrect("LX - LID_CH_BOT", "LY - LID_CH_BOT", "R_LID - LID_CH_BOT")
    taper(pad(lid, "ShellBottomChamfer", s, "LID_CH_BOT"), 45)
    s, b = sketch(lid, "ShellSketch", "XY_Plane", "SKIRT_BOT + LID_CH_BOT")
    b.rrect("LX", "LY", "R_LID")
    pad(lid, "Shell", s, "ZT - LID_CH_TOP - SKIRT_BOT - LID_CH_BOT")
    s, b = sketch(lid, "ShellTopSketch", "XY_Plane", "ZT - LID_CH_TOP")
    b.rrect("LX", "LY", "R_LID")
    taper(pad(lid, "ShellTopChamfer", s, "LID_CH_TOP"), -45)
    s, b = sketch(lid, "OverRimSketch", "XY_Plane", "SEAT")
    b.rrect("SKX", "SKY", "R_SK")
    pocket(lid, "OverRim", s, "SEAT - SKIRT_BOT + 1")
    s, b = sketch(lid, "CavitySketch", "XY_Plane", "PLATE_Z0")
    b.rrect("BAND_IN_X", "BAND_IN", "CAV_R")
    pocket(lid, "Cavity", s, "PLATE_Z0 - SKIRT_BOT + 1")
    s, b = sketch(lid, "SpineSketch", "XY_Plane", "SEAT")
    b.rect("-SPINE_HX", "SPINE_HX", "-SPINE_Y", "SPINE_Y")
    pad(lid, "Spine", s, "PLATE_Z0 + 0.5 - SEAT")
    s, b = sketch(lid, "SpineUpperSketch", "XY_Plane", "SPINE_UPPER_Z0")
    b.rect("-SPINE_HX", "SPINE_HX", "SPINE_Y - 0.5", "SPINE_UPPER_Y")
    b.rect("-SPINE_HX", "SPINE_HX", "-SPINE_UPPER_Y", "-SPINE_Y + 0.5")
    pad(lid, "SpineUpper", s, "PLATE_Z0 + 0.5 - SPINE_UPPER_Z0")
    s, b = sketch(lid, "HangerBlocksSketch", "XY_Plane", "DT_Z0")
    b.rect("-HB_HX", "HB_HX", "HB_Y0", "BAND_IN + 0.5")
    b.rect("-HB_HX", "HB_HX", "-BAND_IN - 0.5", "-HB_Y0")
    pad(lid, "HangerBlocks", s, "PLATE_Z0 + 0.5 - DT_Z0")
    s, b = sketch(lid, "CradleBlocksSketch", "XY_Plane", "CRADLE_Z1")
    b.rect("CD_X0", "CD_X1 + 1.5", "CD_W0 - 2", "CD_W1 + 2")
    b.rect("CD_X0", "CD_X1 + 1.5", "-CD_W1 - 2", "-CD_W0 + 2")
    pad(lid, "CradleBlocks", s, "PLATE_Z0 + 0.5 - CRADLE_Z1")
    s, b = sketch(lid, "OutletBlockSketch", "XY_Plane", 2)
    b.rect("OUT_X - POCKET_R - POCKET_WALL", "BAND_IN_X + 0.5", "-POCKET_R - POCKET_WALL", "POCKET_R + POCKET_WALL")
    pad(lid, "OutletBlock", s, "PLATE_Z0 + 0.5 - 2")
    s, b = sketch(lid, "InnerLipSketch", "XY_Plane", "LIP_BOT")
    b.rrect("LIP_X", "LIP_Y", "LIP_R"); b.rrect("BAND_IN_X", "BAND_IN", "CAV_R")
    pad(lid, "InnerLip", s, "SEAT + 0.5 - LIP_BOT")
    s, b = sketch(lid, "GasketGrooveSketch", "XY_Plane", "SEAT + G_RECESS")
    b.rrect("GOX", "GOY", "GOR"); b.rrect("GIX", "GIY", "GIR")
    pocket(lid, "GasketGroove", s, "G_RECESS + 1")
    # outlet: 45 deg cone recesses (grommet + anchor) joined by a narrow strap channel - no bridge when printed
    for name, x, r0, h in (("GrommetCone", "OUT_X", "GROM_BORE / 2", "GROM_CONE_D"),
                           ("AnchorCone", "PARK_X", "ANCHOR_CONE_R0", "ANCHOR_CONE_D")):
        c = lid.newObject("PartDesign::SubtractiveCone", name)
        for prop, e in (("Radius1", r0), ("Radius2", "%s + %s + 0.5" % (r0, h)), ("Height", "%s + 0.5" % h),
                        (".Placement.Base.x", x), (".Placement.Base.z", "ZT - %s" % h)):
            c.setExpression(prop, expr_of(e))
    s, b = sketch(lid, "OutletRimRoundSketch", "XZ_Plane", 0)       # rounded rim: filament slides over it
    b.rim_round("OUT_X", "GROM_BORE / 2 + GROM_CONE_D", "ZT", "OUT_RND")
    gv = lid.newObject("PartDesign::Groove", "OutletRimRound")
    gv.Profile = s
    gv.ReferenceAxis = (s, ["Axis0"])
    gv.Angle = 360
    s.Visibility = False
    s, b = sketch(lid, "TabSlotSketch", "XY_Plane", "ZT + 0.5")          # finger slot under the cap's pull tab tip
    b.slot_x("OUT_X - TAB_L + TAB_W / 2", "OUT_X - CAP_R1", "TAB_SLOT_W / 2")
    pocket(lid, "TabSlot", s, "0.5 + CAP_RECESS + STRAP_T + TAB_SLOT_GAP")
    s, b = sketch(lid, "TabSlotFlareSketch", "XY_Plane", "ZT")
    b.slot_x("OUT_X - TAB_L + TAB_W / 2", "OUT_X - CAP_R1", "TAB_SLOT_W / 2 + TAB_SLOT_CH")
    taper(pocket(lid, "TabSlotFlare", s, "TAB_SLOT_CH"), -45)
    s, b = sketch(lid, "StrapChannelSketch", "XY_Plane", "ZT + 0.5")
    b.rect("OUT_X", "PARK_X", "-STRAP_CH_W / 2", "STRAP_CH_W / 2")
    pocket(lid, "StrapChannel", s, "STRAP_CH_D + 0.5")
    s, b = sketch(lid, "GrommetBoreSketch", "XY_Plane", "GROM_ZB + 0.1")
    b.circle("OUT_X", 0, "GROM_BORE / 2")
    pocket(lid, "GrommetBore", s, "GROM_L + 0.6")
    s, b = sketch(lid, "AnchorHoleSketch", "XY_Plane", "ZT - ANCHOR_CONE_D + 0.1")
    b.circle("PARK_X", 0, "ANCHOR_HOLE_D / 2")
    pocket(lid, "AnchorHole", s, "ANCHOR_HOLE_L + 0.1")
    s, b = sketch(lid, "PtfePassageSketch", "XY_Plane", "GROM_ZB - GROM_L")
    b.circle("OUT_X", 0, "PTFE_R")
    pocket(lid, "PtfePassage", s, "GROM_ZB - GROM_L + 1")
    cone = lid.newObject("PartDesign::SubtractiveCone", "GrommetStep45")      # 45 deg step: prints clean top-down
    for prop, e in (("Radius1", "PTFE_R"), ("Radius2", "GROM_BORE / 2"), ("Height", "GROM_BORE / 2 - PTFE_R"),
                    (".Placement.Base.x", "OUT_X"),
                    (".Placement.Base.z", "GROM_ZB - GROM_L - 0.5 - (GROM_BORE / 2 - PTFE_R)")):
        cone.setExpression(prop, expr_of(e))
    # silica-box snap grooves in the band (XZ plane: sketch x = x, sketch y = z, offset along -y)
    s, b = sketch(lid, "SnapGroovesSketch", "XZ_Plane", "-BAND_IN")
    for sx in ("SNAP_X1", "SNAP_X2", "SNAP_X3"):
        b.rect("%s - SNAP_HL" % sx, "%s + SNAP_HL" % sx, "BOX_SNAP_Z - SNAP_HH", "BOX_SNAP_Z + SNAP_HH")
    g = pocket(lid, "SnapGrooves", s, "2 * SNAP_DEPTH", midplane=True)
    mirrored(lid, "SnapGroovesMirror", [g], "XZ_Plane")
    # hanger dovetail sockets (open towards the middle, closed at the wall)
    s, b = sketch(lid, "HangerSocketSketch", "XZ_Plane", "-(DT_Y0 + DT_OUT) / 2")
    b.poly([("-DT_HALF0", "DT_Z0"), ("DT_HALF0", "DT_Z0"), ("DT_HALF1", "DT_Z1"), ("-DT_HALF1", "DT_Z1")])
    g = pocket(lid, "HangerSocket", s, "DT_OUT - DT_Y0", midplane=True)
    mirrored(lid, "HangerSocketMirror", [g], "XZ_Plane")
    # hygrometer cradle dovetail sockets (YZ plane: sketch x = y, sketch y = z, offset along +x)
    s, b = sketch(lid, "CradleSocketSketch", "YZ_Plane", "(CD_X0 - 1 + CD_X1) / 2")
    b.poly([("CD_N0", "CRADLE_Z1"), ("CD_N1", "CRADLE_Z1"), ("CD_W1", "CRADLE_Z1 + CD_H"), ("CD_W0", "CRADLE_Z1 + CD_H")])
    g = pocket(lid, "CradleSocket", s, "CD_X1 - CD_X0 + 1", midplane=True)
    mirrored(lid, "CradleSocketMirror", [g], "XZ_Plane")
    # seam screws: inserts in the -X half, clearance holes in the +X half (edit positions in these sketches)
    s, b = sketch(lid, "InsertHolesSketch", "YZ_Plane", "-BOLT_HOLE_L / 2")
    for y, z in SEAM_BOLTS:
        b.circle(y, z, "M3_INSERT_D / 2")
    pocket(lid, "InsertHoles", s, "BOLT_HOLE_L", midplane=True)
    s, b = sketch(lid, "BoltHolesSketch", "YZ_Plane", "BOLT_HOLE_L / 2")
    for y, z in SEAM_BOLTS:
        b.circle(y, z, "BOLT_D / 2")
    pocket(lid, "BoltHoles", s, "BOLT_HOLE_L", midplane=True)
    # latch slots (+y side, both x), mirrored to -y
    s, b = sketch(lid, "LatchSlotsSketch", "XY_Plane", "ZT + 1")
    for sx in ("LATCH_X", "-LATCH_X"):
        b.rect("%s - LW / 2 - SLOT_CLR" % sx, "%s + LW / 2 + SLOT_CLR" % sx, "PY - HUB_R - 0.5", "LY + 1")
    g = pocket(lid, "LatchSlots", s, "ZT + 1 - (PZ - HUB_R - 0.5)")
    mirrored(lid, "LatchSlotsMirror", [g], "XZ_Plane")
    # soften the notch edges on the outer skirt (XZ sketch at y = LY, cut inward with a 45 deg taper)
    s, b = sketch(lid, "LatchSlotChamferSketch", "XZ_Plane", "-LY")
    for sx in ("LATCH_X", "-LATCH_X"):
        b.rect("%s - LW / 2 - SLOT_CLR - SLOT_CH" % sx, "%s + LW / 2 + SLOT_CLR + SLOT_CH" % sx,
               "PZ - HUB_R - 0.5 - SLOT_CH", "ZT + 1")
    g = taper(pocket(lid, "LatchSlotChamfer", s, "SLOT_CH", reversed_=True), -45)
    mirrored(lid, "LatchSlotChamferMirror", [g], "XZ_Plane")
    s, b = sketch(lid, "LatchSlotTopChamferSketch", "XY_Plane", "ZT")   # ... and on the lid top
    for sx in ("LATCH_X", "-LATCH_X"):
        b.rect("%s - LW / 2 - SLOT_CLR - SLOT_CH" % sx, "%s + LW / 2 + SLOT_CLR + SLOT_CH" % sx,
               "PY - HUB_R - 0.5 - SLOT_CH", "LY + 1")
    g = taper(pocket(lid, "LatchSlotTopChamfer", s, "SLOT_CH"), -45)
    mirrored(lid, "LatchSlotTopChamferMirror", [g], "XZ_Plane")
    # latch pivot stubs on the slot walls (one latch's pair, then mirrored to all four)
    s, b = sketch(lid, "StubInnerSketch", "YZ_Plane", "LATCH_X - LW / 2 - SLOT_CLR - 0.5")
    b.circle("PY", "PZ", "STUB_D / 2")
    st1 = pad(lid, "StubInner", s, "STUB_L + 0.5")
    s, b = sketch(lid, "StubOuterSketch", "YZ_Plane", "LATCH_X + LW / 2 + SLOT_CLR - STUB_L")
    b.circle("PY", "PZ", "STUB_D / 2")
    st2 = pad(lid, "StubOuter", s, "STUB_L + 0.5")
    mt = lid.newObject("PartDesign::MultiTransform", "StubsAllLatches")
    mt.Originals = [st1, st2]
    m1 = lid.newObject("PartDesign::Mirrored", "StubsMirrorX")
    m1.MirrorPlane = (plane(lid, "YZ_Plane"), [""])
    m2 = lid.newObject("PartDesign::Mirrored", "StubsMirrorY")
    m2.MirrorPlane = (plane(lid, "XZ_Plane"), [""])
    mt.Transformations = [m1, m2]
    lid.Tip = mt

    # ---------------- latch (assembly position, +Y side, centred on x = 0)
    lat = doc.addObject("PartDesign::Body", "Latch")
    E = "LATCH_EDGE_CH"
    profile = [("LIP_TIP", "LTE - 3"), ("LIP_TIP", "LTE"), ("ARM_I", "LTE"), ("ARM_I", "PZ - HUB_R"), ("PY", "PZ - HUB_R"),
               ("PY", "PZ + HUB_R"), ("ARM_O - %s" % E, "PZ + HUB_R"), ("ARM_O", "PZ + HUB_R - %s" % E),
               ("ARM_O", "LTE - 1"),
               ("ARM_O + 3 - 3 * %s / (LTE - 1 - TAB_BOT)" % E, "TAB_BOT + %s" % E), ("ARM_O + 3 - %s" % E, "TAB_BOT"),
               ("ARM_I + 1 + %s" % E, "TAB_BOT"), ("ARM_I + 1 - %s / (LTE - 3 - TAB_BOT)" % E, "TAB_BOT + %s" % E),
               ("ARM_I", "LTE - 3")]
    # each latch solid = middle section + two 45 deg tapered side bands (chamfers every side-face edge).
    # The three sketches of a set are drawn from the same Params - edit Params (or all three sketches).
    def banded(name, draw):
        s, b = sketch(lat, name + "Sketch", "YZ_Plane", 0)
        draw(b)
        pad(lat, name, s, "LW - 2 * LATCH_CH", midplane=True)
        s, b = sketch(lat, name + "RightSketch", "YZ_Plane", "LW / 2 - LATCH_CH")
        draw(b)
        taper(pad(lat, name + "Right", s, "LATCH_CH"), -45)
        s, b = sketch(lat, name + "LeftSketch", "YZ_Plane", "-(LW / 2 - LATCH_CH)")
        draw(b)
        taper(pad(lat, name + "Left", s, "LATCH_CH", reversed_=True), -45)
    banded("LatchProfile", lambda b: b.poly(profile))
    banded("Hub", lambda b: b.circle("PY", "PZ", "HUB_R"))
    s, b = sketch(lat, "RidgeSketch", "YZ_Plane", 0)
    b.poly([("BUMP_Y0", "LTE - 0.01"), ("BUMP_Y + BUMP_BASE / 2", "LTE - 0.01"),
            ("BUMP_Y + BUMP_TIP / 2", "LTE + BUMP_H"), ("BUMP_T0", "LTE + BUMP_H")])
    pad(lat, "Ridge", s, "LW - 2 * LATCH_CH", midplane=True)
    s, b = sketch(lat, "PivotHoleSketch", "YZ_Plane", 0)
    b.circle("PY", "PZ", "STUB_D / 2 + 0.2")
    pocket(lat, "PivotHole", s, through=True, midplane=True)
    s, b = sketch(lat, "COpeningSketch", "YZ_Plane", 0)
    b.rect("PY - C_OPEN / 2", "PY + C_OPEN / 2", "PZ - HUB_R - 1", "PZ")
    pocket(lat, "COpening", s, through=True, midplane=True)
    # the four latches in place: links to the one Latch body
    for k, (sx, sy) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1))):
        ln = doc.addObject("App::Link", "Latch_%d" % (k + 1))
        ln.LinkedObject = lat
        ln.Placement = App.Placement(V(sx * P["LATCH_X"], 0, 0), App.Rotation(V(0, 0, 1), 0 if sy > 0 else 180))
        ln.setExpression(".Placement.Base.x", ("" if sx > 0 else "-") + "Params.LATCH_X")

    # ---------------- gasket (reference: the old lid's strip in the groove)
    gas = doc.addObject("PartDesign::Body", "Gasket")
    s, b = sketch(gas, "GasketSketch", "XY_Plane", "SEAT + G_RECESS - G_T")
    b.rrect("GCX + G_W_STRIP / 2", "GCY + G_W_STRIP / 2", "GCR + G_W_STRIP / 2")
    b.rrect("GCX - G_W_STRIP / 2", "GCY - G_W_STRIP / 2", "GCR - G_W_STRIP / 2")
    pad(gas, "GasketStrip", s, "G_T")

    # ---------------- lid halves + TPU seam strip (Part booleans on the Lid body, x split at +-SEAM)
    big = 400
    def cutter(name, x0_expr, len_expr):
        bx = doc.addObject("Part::Box", name)
        bx.Width, bx.Height = 2 * big, 2 * big
        bx.setExpression("Length", expr_of(len_expr))
        bx.Placement = App.Placement(V(0, -big, -big), App.Rotation())
        bx.setExpression(".Placement.Base.x", expr_of(x0_expr))
        return bx
    halves = {}
    for name, x0, ln_ in (("Lid_L", "-%d" % big, "%d - SEAM" % big), ("Lid_R", "SEAM", "%d - SEAM" % big),
                          ("SeamStrip", "-SEAM", "2 * SEAM")):
        c = doc.addObject("Part::Common", name)
        c.Base, c.Tool = lid, cutter(name + "_Cutter", x0, ln_)
        halves[name] = c
    doc.recompute()
    return doc


def build_spool(doc):
    """Bayonet hanger (+Y, Hanger_B; Hanger_A is its mirror), screw-together hub with 608s, stub axles (+ links)."""
    # ---- hanger B: plate in the XZ plane (sketch x = x, sketch y = z), offset along -y
    hg = doc.addObject("PartDesign::Body", "Hanger_B")
    s, b = sketch(hg, "HangerPlateSketch", "XZ_Plane", "-HG_Y0")
    b.poly([("-HG_TOP_HX", "DT_Z0 - 0.3"), ("HG_TOP_HX", "DT_Z0 - 0.3"), ("HG_KNEE_X", "-D_AXLE"),
            ("HG_KNEE_X", "-D_AXLE - HG_FOOT"), ("-HOOK_E + 1", "-D_AXLE - HG_FOOT"),
            ("-HOOK_E + 1", "-D_AXLE + HOOK_RISE + 9"), ("-HG_TOP_HX", "-D_AXLE + HG_LEFT_Z")])
    pad(hg, "HangerPlate", s, "HG_Y1 - HG_Y0", reversed_=True)
    s, b = sketch(hg, "TenonSketch", "XZ_Plane", "-DT_TENON_Y0")
    b.poly([("-TEN_XB", "DT_Z0 - 0.5"), ("TEN_XB", "DT_Z0 - 0.5"), ("TEN_XB", "DT_Z0"), ("TEN_XT", "TEN_ZT"),
            ("-TEN_XT", "TEN_ZT"), ("-TEN_XB", "DT_Z0")])
    pad(hg, "Tenon", s, "HG_Y1 - DT_TENON_Y0", reversed_=True)
    s, b = sketch(hg, "CrushRibSketch", "YZ_Plane", "-DT_RIB_PITCH")       # YZ: sketch x = y, sketch y = z
    b.poly([("DT_TENON_Y0", "TEN_ZT - 0.01"), ("HG_Y1", "TEN_ZT - 0.01"), ("HG_Y1", "TEN_ZT + 0.05"),
            ("HG_Y1 - DT_RIB_RAMP", "TEN_ZT + RIB_H"), ("DT_TENON_Y0", "TEN_ZT + RIB_H")])
    rib = pad(hg, "CrushRib", s, "DT_RIB_W", midplane=True)
    linear(hg, "CrushRibs", [rib], (plane(hg, "X_Axis"), [""]), "2 * DT_RIB_PITCH", 3)
    # bayonet track: sideways, up, sideways, down, climbing exit (centre line at HG_ZC)
    pts = [("0", "HG_ZC"), ("-HOOK_STEP1", "HG_ZC"), ("-HOOK_STEP1", "HG_ZC + HOOK_RISE"),
           ("-HOOK_B", "HG_ZC + HOOK_RISE"), ("-HOOK_B", "HG_ZC")]
    for i in range(4):
        s, b = sketch(hg, "TrackSeg%dSketch" % (i + 1), "XZ_Plane", 0)
        b.slot(pts[i], pts[i + 1], "HG_H")
        pocket(hg, "TrackSeg%d" % (i + 1), s, through=True, midplane=True)
    s, b = sketch(hg, "TrackExitSketch", "XZ_Plane", 0)
    b.poly([("-HOOK_B + EXN_X", "HG_ZC + EXN_Z"), ("-HOOK_E + EXN_X", "HG_ZC + HOOK_EXIT_RISE + EXN_Z"),
            ("-HOOK_E - EXN_X", "HG_ZC + HOOK_EXIT_RISE - EXN_Z"), ("-HOOK_B - EXN_X", "HG_ZC - EXN_Z")])
    pocket(hg, "TrackExit", s, through=True, midplane=True)
    s, b = sketch(hg, "TrackExitEndSketch", "XZ_Plane", 0)
    b.circle("-HOOK_E", "HG_ZC + HOOK_EXIT_RISE", "HW_EX")
    pocket(hg, "TrackExitEnd", s, through=True, midplane=True)
    s, b = sketch(hg, "TrackFloorsSketch", "XZ_Plane", 0)            # flat floors where the axle rests
    b.rect("-HOOK_STEP1 - HG_H", "HG_H", "HG_FLOOR", "HG_ZC")
    b.rect("-HOOK_B - HG_H", "-HOOK_B + HG_H", "HG_FLOOR", "HG_ZC")
    pocket(hg, "TrackFloors", s, through=True, midplane=True)
    s, b = sketch(hg, "ToothSketch", "XZ_Plane", "-HG_Y0")           # solid tooth between the two drops
    b.rect("-HOOK_B + HG_H", "-HOOK_STEP1 - HG_H", "HG_FLOOR", "HG_ZC + HOOK_RISE - HG_H")
    pad(hg, "Tooth", s, "HG_Y1 - HG_Y0", reversed_=True)
    ha = doc.addObject("Part::Mirroring", "Hanger_A")
    ha.Source = hg
    ha.Normal = V(0, 1, 0)

    # ---- screw-together hub. Every body is drawn in its own frame: axis = z, z = |y| from the spool centre
    # (XZ sketches: x = r, y = z). Links put them in place: B side z -> +Y, A side rotated 180 deg (z -> -Y).
    halves = {k: hub_half(doc, k) for k in ("A", "B")}
    ret = hub_retainer(doc)
    stub = stub_axle(doc)
    clip = stub_clip(doc)
    for side_, sy in (("B", 1), ("A", -1)):
        for name, body in (("HubHalf%s_Asm" % side_, halves[side_]), ("HubRetainer_%s" % side_, ret),
                           ("StubAxle_%s" % side_, stub), ("StubClip_%s" % side_, clip)):
            ln = doc.addObject("App::Link", name)
            ln.LinkedObject = body
            ln.Placement = App.Placement(V(0, 0, -P["D_AXLE"]), App.Rotation(V(1, 0, 0), -90 * sy))
            ln.setExpression(".Placement.Base.z", "-Params.D_AXLE")


def thread_profile(b, rb, depth, z0, crest, grow=0):
    """Trapezoid thread section (45 deg flanks) at radius rb, centred on z0; grow = clearance all round (groove).
    Reaches 0.3 into the root so the ridge fuses with its tube."""
    hw = "(%s) + (%s) / 2 + %s" % (depth, crest, grow)
    tip = "(%s) / 2 + %s" % (crest, grow)
    out = "%s + %s + %s" % (rb, depth, grow)
    b.poly([("%s - 0.3" % rb, "%s - (%s)" % (z0, hw)), (out, "%s - (%s)" % (z0, tip)),
            (out, "%s + %s" % (z0, tip)), ("%s - 0.3" % rb, "%s + %s" % (z0, hw))])


def helix(body, name, sk, pitch, height, sub=False):
    f = body.newObject("PartDesign::SubtractiveHelix" if sub else "PartDesign::AdditiveHelix", name)
    f.Profile = sk
    f.ReferenceAxis = (sk, ["V_Axis"])
    f.Mode = "pitch-height-angle"
    for prop, e in (("Pitch", pitch), ("Height", height)):
        setattr(f, prop, ev(expr_of(e)))
        f.setExpression(prop, expr_of(e))
    sk.Visibility = False
    return f


def hub_half(doc, k):
    """Hub half (print: flange on the bed). Both: flange + bearing boss (608 pocket, 45 deg lip cone, 45 deg
    shoulder, threaded retainer recess). B: long sleeve with the female 2-start thread. A: smooth spigot, 45 deg
    end cone, thread tube with the male thread reaching across the centre into B."""
    body = doc.addObject("PartDesign::Body", "HubHalf" + k)
    rm = "RET_R - RET_TD"
    boss = [(rm, "HUB_U + HUB_FL_T"), (rm, "RECESS_U"), ("BRG_R", "RECESS_U - (%s - BRG_R)" % rm),
            ("BRG_R", "POCKET_U"), ("SEAT_R", "POCKET_U"), ("SEAT_R - (POCKET_U - LIP_U)", "LIP_U"),
            ("HUB_BOSS_R", "LIP_U"), ("HUB_BOSS_R", "HUB_U")]
    if k == "B":
        tube = [("HUB_M_ROOT + HUB_CLR", "HUB_U"), ("HUB_M_ROOT + HUB_CLR", "HUB_SLEEVE_END"),
                ("HUB_SP_R", "HUB_SLEEVE_END"), ("HUB_SP_R", "HUB_U")]
    else:
        tube = [("HUB_SP_IN", "HUB_U"), ("HUB_SP_IN", "HUB_A_SMOOTH + HUB_END_T + HUB_SP_IN - HUB_BORE_A"),
                ("HUB_BORE_A", "HUB_A_SMOOTH + HUB_END_T"), ("HUB_BORE_A", "-HUB_A_END"),
                ("HUB_M_ROOT", "-HUB_A_END"), ("HUB_M_ROOT", "HUB_A_SMOOTH"), ("HUB_SP_R", "HUB_A_SMOOTH"),
                ("HUB_SP_R", "HUB_U")]
    s, b = sketch(body, "HalfProfileSketch", "XZ_Plane", 0)
    b.poly(boss + tube + [("HUB_FL_R", "HUB_U"), ("HUB_FL_R", "HUB_U + HUB_FL_T")])
    revolve(body, "HalfBody", s, "V_Axis")
    s, b = sketch(body, "MainThreadSketch", "XZ_Plane", 0)
    if k == "A":
        thread_profile(b, "HUB_M_ROOT", "HUB_TD", "HUB_THR_Z0", "HUB_CREST")
        t = helix(body, "MaleThread", s, "HUB_LEAD", "HUB_THR_H")
    else:
        thread_profile(b, "HUB_M_ROOT", "HUB_TD", "HUB_GRV_Z0", "HUB_CREST", "HUB_CLR")
        t = helix(body, "FemaleThread", s, "HUB_LEAD", "HUB_GRV_H", sub=True)
    polar(body, "ThreadStarts", [t], (plane(body, "Z_Axis"), [""]), "HUB_STARTS")
    s, b = sketch(body, "RetainerThreadSketch", "XZ_Plane", 0)
    thread_profile(b, rm, "RET_TD", "RET_Z0", "RET_CREST", "HUB_CLR / 2")
    helix(body, "RetainerThread", s, "RET_P", "HUB_U + HUB_FL_T + 1 - RET_Z0", sub=True)
    s, b = sketch(body, "GripScallopSketch", "XY_Plane", "HUB_U - 1")
    b.circle("HUB_FL_R", 0, "HUB_KNURL_R")
    g = pocket(body, "GripScallop", s, "HUB_FL_T + 2", reversed_=True)
    polar(body, "GripScallops", [g], (plane(body, "Z_Axis"), [""]), "HUB_KNURL_N")
    return body


def hub_retainer(doc):
    """Threaded ring clamping the 608 outer race (print: coin slots up, as modelled)."""
    body = doc.addObject("PartDesign::Body", "HubRetainer")
    rr = "RET_R - RET_TD - HUB_CLR / 2"
    s, b = sketch(body, "RetainerProfileSketch", "XZ_Plane", 0)
    b.rect("RET_HOLE", rr, "RECESS_U", "HUB_U + HUB_FL_T")
    revolve(body, "RetainerRing", s, "V_Axis")
    s, b = sketch(body, "RetainerMaleSketch", "XZ_Plane", 0)
    thread_profile(b, rr, "RET_TD", "RET_Z0", "RET_CREST")
    helix(body, "RetainerMale", s, "RET_P", "HUB_U + HUB_FL_T - RET_Z0 - 1.1")
    for n, (hx, hy) in enumerate((("RET_R", "0.7"), ("0.7", "RET_R"))):
        s, b = sketch(body, "CoinSlot%dSketch" % (n + 1), "XY_Plane", "HUB_U + HUB_FL_T")
        b.rect("-" + hx, hx, "-" + hy, hy)
        pocket(body, "CoinSlot%d" % (n + 1), s, 1)
    return body


def stub_axle(doc):
    """Stub axle pushed in from outside: collar outside the hanger, neck in the track, shoulder on the inner race,
    shaft through the 608, clip groove on the inside. Prints standing on its collar; 45 deg cones under the
    shoulder and at neck -> shaft."""
    body = doc.addObject("PartDesign::Body", "StubAxle")
    s, b = sketch(body, "StubProfileSketch", "XZ_Plane", 0)
    b.poly([(0, "STUB_TIP_U"), ("AXLE_R - AXLE_TIP_CH", "STUB_TIP_U"), ("AXLE_R", "STUB_TIP_U + AXLE_TIP_CH"),
            ("AXLE_R", "CLIP_U - 0.1"), ("AXLE_R - CLIP_GD", "CLIP_U - 0.1"), ("AXLE_R - CLIP_GD", "POCKET_U"),
            ("AXLE_R", "POCKET_U"), ("AXLE_R", "RECESS_U"), ("STUB_SH_R", "RECESS_U"),
            ("STUB_SH_R", "RECESS_U + STUB_SH_L"), ("AXLE_R", "RECESS_U + STUB_SH_L + STUB_SH_R - AXLE_R"),
            ("AXLE_R", "AXLE_N0 - (AXLE_R - AXLE_NECK_R)"), ("AXLE_NECK_R", "AXLE_N0"), ("AXLE_NECK_R", "AXLE_N1"),
            ("STUB_COL_R", "AXLE_N1"), ("STUB_COL_R", "AXLE_N1 + STUB_COL_T"), (0, "AXLE_N1 + STUB_COL_T")])
    revolve(body, "StubBody", s, "V_Axis")
    return body


def stub_clip(doc):
    """Printed C-clip: snaps sideways into the stub groove against the inner race (print flat)."""
    body = doc.addObject("PartDesign::Body", "StubClip")
    s, b = sketch(body, "ClipRingSketch", "XY_Plane", "CLIP_U")
    b.circle(0, 0, "CLIP_R")
    b.circle(0, 0, "AXLE_R - CLIP_GD + 0.05")
    pad(body, "ClipRing", s, "CLIP_T")
    s, b = sketch(body, "ClipOpeningSketch", "XY_Plane", "CLIP_U - 1")
    b.rect("-(AXLE_R - CLIP_GD) * CLIP_OPEN", "(AXLE_R - CLIP_GD) * CLIP_OPEN", -10, 0)
    pocket(body, "ClipOpening", s, "CLIP_T + 2", reversed_=True)
    return body


def silica_box(doc, side):
    """Silica box body (assembly position). side 'L': long box, rounded -X end, inner end at +X (x1);
    side 'R': short box, straight ends, inner end at -X (x0)."""
    L = side == "L"
    x0, x1 = ("SBOX_L_X0", "SBOX_L_X1") if L else ("SBOX_R_X0", "SBOX_R_X1")
    inner = x1 if L else x0
    sg = "" if L else "-"                                  # sign of +1 (L) / -1 (R) in expressions
    bx = doc.addObject("PartDesign::Body", "SilicaBox_" + side)
    W, F = "SBOX_W", "SBOX_FLOOR"

    def outline(b, o, cut):                                # box outline grown by o (expression string, e.g. "-SBOX_W")
        if L:
            b.rrect_cut("SB_HX + (%s)" % o, "SB_HY + (%s)" % o, "SB_R + (%s)" % o, cut)
        else:
            b.rect("%s - (%s)" % (x0, o), "%s + (%s)" % (x1, o), "-(SB_HY + (%s))" % o, "SB_HY + (%s)" % o)

    s, b = sketch(bx, "FloorSketch", "XY_Plane", "SBOX_Z0")
    outline(b, "0", x1)
    pad(bx, "Floor", s, F)
    # floor slots: full-width bars, then the rim / walls / pads are added back over them
    s, b = sketch(bx, "FloorSlotSketch", "XY_Plane", "SBOX_Z0 + %s + 0.5" % F)
    b.rect("%s + %s + 3" % (x0, W), "%s + %s + 3 + BEAD_SLOT" % (x0, W), "-SB_HY - 1", "SB_HY + 1")
    sl = pocket(bx, "FloorSlot", s, "%s + 1" % F)
    linear(bx, "FloorSlots", [sl], (plane(bx, "X_Axis"), [""]),
           "(floor((%s - %s - 2 * %s - 6) / SLOT_PITCH)) * SLOT_PITCH" % (x1, x0, W),
           "floor((%s - %s - 2 * %s - 6) / SLOT_PITCH) + 1" % (x1, x0, W))
    s, b = sketch(bx, "FloorRimSketch", "XY_Plane", "SBOX_Z0")            # 2 mm solid margin inside the walls
    outline(b, "0", x1)
    if L:
        b.rrect_cut("SB_HX - %s - 2" % W, "SB_HY - %s - 2" % W, "SB_R - %s - 2" % W, "%s - %s - 2" % (x1, W))
    else:
        b.rect("%s + %s + 2" % (x0, W), "%s - %s - 2" % (x1, W), "-(SB_WI - 2)", "SB_WI - 2")
    pad(bx, "FloorRim", s, F)
    s, b = sketch(bx, "WallsSketch", "XY_Plane", "SBOX_Z0")
    outline(b, "0", x1)
    if L:
        b.rrect_cut("SB_HX - %s" % W, "SB_WI", "SB_R - %s" % W, "%s - %s" % (x1, W))
    else:
        b.rect("%s + %s" % (x0, W), "%s - %s" % (x1, W), "-SB_WI", "SB_WI")
    pad(bx, "Walls", s, "SBOX_TOP - SBOX_Z0")
    if L:                                                                # handle: solid pads + 2 holes
        s, b = sketch(bx, "HandlePadsSketch", "XY_Plane", "SBOX_Z0")
        b.rect("HANDLE_X - 3.8", "HANDLE_X + 3.8", "HANDLE_Y - 3.5", "HANDLE_Y + 3.5")
        b.rect("HANDLE_X - 3.8", "HANDLE_X + 3.8", "-HANDLE_Y - 3.5", "-HANDLE_Y + 3.5")
        pad(bx, "HandlePads", s, F)
        s, b = sketch(bx, "HandleHolesSketch", "XY_Plane", "SBOX_Z0 + %s + 1" % F)
        for sy in ("", "-"):
            b.rect("HANDLE_X - HANDLE_HOLE_X / 2", "HANDLE_X + HANDLE_HOLE_X / 2",
                   "%sHANDLE_Y - HANDLE_HOLE_Y / 2" % sy, "%sHANDLE_Y + HANDLE_HOLE_Y / 2" % sy)
        pocket(bx, "HandleHoles", s, "%s + 2" % F)
        # cover ledge round the rounded end (carries the cover where there are no grooves)
        s, b = sketch(bx, "LedgeSketch", "XY_Plane", "SLIDE_G0 - 1.5")
        b.rrect_cut("SB_HX - %s + 0.01" % W, "SB_WI + 0.01", "SB_R - %s + 0.01" % W, "-SB_XS + 0.01")
        pad(bx, "Ledge", s, 1.5)
        s, b = sketch(bx, "LedgeInnerSketch", "XY_Plane", "SLIDE_G0 + 0.5")
        b.rrect_cut("SB_HX - %s - SLIDE_GROOVE_D" % W, "SB_WI - SLIDE_GROOVE_D", "SB_R - %s - SLIDE_GROOVE_D" % W,
                    "-SB_XS + 1")
        pocket(bx, "LedgeInner", s, 2.5)
    # vent slots in the inner end wall (YZ sketch: x = y, y = z)
    s, b = sketch(bx, "EndVentSketch", "YZ_Plane", inner)
    b.rect("-SB_HY + 6", "-SB_HY + 6 + BEAD_SLOT", "SBOX_Z0 + %s + 3" % F, "SLIDE_G0 - 4")
    ev_ = pocket(bx, "EndVent", s, 6, midplane=True)
    linear(bx, "EndVents", [ev_], (plane(bx, "Y_Axis"), [""]), "floor((2 * SB_HY - 12) / 5) * 5",
           "floor((2 * SB_HY - 12) / 5) + 1")
    # cover grooves (45 deg roof) along the straight long walls, + 0.6 head room near the inner end
    xa, xb = ("-SB_XS", "%s + 1" % x1) if L else ("%s - 1" % x0, x1)
    groove = [("SB_WI - 0.01", "SLIDE_GF"), ("SB_WI + SLIDE_GROOVE_D", "SLIDE_GF"),
              ("SB_WI + SLIDE_GROOVE_D", "SLIDE_G1 - SLIDE_GROOVE_D"), ("SB_WI", "SLIDE_G1"), ("SB_WI - 0.01", "SLIDE_G1")]
    s, b = sketch(bx, "CoverGrooveSketch", "YZ_Plane", "((%s) + (%s)) / 2" % (xa, xb))
    b.poly(groove)
    g1 = pocket(bx, "CoverGroove", s, "(%s) - (%s)" % (xb, xa), midplane=True)
    s, b = sketch(bx, "GrooveLeadInSketch", "YZ_Plane", "%s - %s5" % (inner, sg))
    b.poly([(y, z if "G1" not in str(z) else z + " + 0.6") for y, z in groove])
    g2 = pocket(bx, "GrooveLeadIn", s, 12, midplane=True)
    mirrored(bx, "CoverGroovesMirror", [g1, g2], "XZ_Plane")
    # lowered inner end wall (the cover slides over it), detent notch, chamfered top edge
    ew0, ew1 = (("%s - %s" % (x1, W), x1) if L else (x0, "%s + %s" % (x0, W)))
    s, b = sketch(bx, "EndWallDownSketch", "XY_Plane", "SBOX_TOP + 1")
    b.rect("%s - 0.01" % ew0, "%s + 0.01" % ew1, "-SB_WI - SLIDE_GROOVE_D", "SB_WI + SLIDE_GROOVE_D")
    pocket(bx, "EndWallDown", s, "SBOX_TOP + 1 - SLIDE_G0")
    s, b = sketch(bx, "DetentNotchSketch", "XZ_Plane", 0)              # XZ: x = x, y = z
    b.circle("(%s + %s) / 2" % (ew0, ew1), "SLIDE_G0", 0.7)
    pocket(bx, "DetentNotch", s, "2 * SB_WI", midplane=True)
    s, b = sketch(bx, "EndChamferSketch", "XZ_Plane", 0)
    b.poly([(inner, "SLIDE_G0 + 0.01"), (inner, "SLIDE_G0 - 0.8"), ("%s - %s0.8" % (inner, sg), "SLIDE_G0 + 0.01")])
    pocket(bx, "EndChamfer", s, "2 * SB_WI", midplane=True)
    # slide-bolt locks (+Y side, then mirrored): block inside the wall, tunnel, switch slot, detent dimples
    locks = ("LOCK_X1", "LOCK_X2") if L else ("LOCK_X3",)
    feats = []
    s, b = sketch(bx, "LockBlocksSketch", "XY_Plane", "SBOX_Z0")
    for lx in locks:
        b.rect("%s - LOCK_W / 2 - 1.4" % lx, "%s + LOCK_W / 2 + 1.4" % lx, "LOCK_YIN - 1.5", "SB_WI + 0.01")
    feats.append(pad(bx, "LockBlocks", s, "LOCK_Z1 + LOCK_CLR + LOCK_PEAK + 1.2 - SBOX_Z0"))
    s, b = sketch(bx, "LockTunnelsSketch", "XY_Plane", "LOCK_Z1 + LOCK_CLR")
    for lx in locks:
        b.rect("%s - LOCK_W / 2 - LOCK_CLR" % lx, "%s + LOCK_W / 2 + LOCK_CLR" % lx, "LOCK_YIN - 0.3", "SB_HY + 1")
    feats.append(pocket(bx, "LockTunnels", s, "LOCK_Z1 - LOCK_Z0 + 2 * LOCK_CLR"))
    s, b = sketch(bx, "LockSwitchSlotsSketch", "XY_Plane", "LOCK_Z0 - LOCK_CLR + 0.01")
    for lx in locks:
        b.rect("%s - 3 - LOCK_CLR" % lx, "%s + 3 + LOCK_CLR" % lx, "LOCK_YIN - 0.2", "SB_HY + 1")
    feats.append(pocket(bx, "LockSwitchSlots", s, "LOCK_Z0 - LOCK_CLR + 1.01 - SBOX_Z0"))
    s, b = sketch(bx, "LockSwitchSlotChamferSketch", "XY_Plane", "SBOX_Z0")
    for lx in locks:
        b.rect("%s - 3 - LOCK_CLR - LOCK_SLOT_CH" % lx, "%s + 3 + LOCK_CLR + LOCK_SLOT_CH" % lx,
               "LOCK_YIN - 0.2 - LOCK_SLOT_CH", "SB_HY + 1")
    feats.append(taper(pocket(bx, "LockSwitchSlotChamfer", s, "LOCK_SLOT_CH", reversed_=True), -45))
    # 45 deg gable roof over the tunnel (and through the wall)
    s, b = sketch(bx, "LockRoofGableSketch", "XZ_Plane", "-(LOCK_YIN - 0.3 + SB_HY + 1) / 2")
    zr = "LOCK_Z1 + LOCK_CLR"
    for lx in locks:
        b.poly([("%s - LOCK_W / 2 - LOCK_CLR" % lx, "%s - 0.01" % zr), ("%s + LOCK_W / 2 + LOCK_CLR" % lx, "%s - 0.01" % zr),
                (lx, "%s + LOCK_PEAK" % zr)])
    feats.append(pocket(bx, "LockRoofGable", s, "SB_HY + 1 - LOCK_YIN + 0.3", midplane=True))
    s, b = sketch(bx, "LockDimplesSketch", "XY_Plane", "LOCK_Z1 + LOCK_CLR")      # detent grooves in the side walls
    for lx in locks:
        for sd in ("-", "+"):
            for yd in ("LOCK_YT - LOCK_LEN / 2", "LOCK_YT - LOCK_LEN / 2 - LOCK_TRAVEL"):
                b.circle("%s %s (LOCK_W / 2 + LOCK_CLR)" % (lx, sd), yd, 0.5)
    feats.append(pocket(bx, "LockDimples", s, "LOCK_Z1 - LOCK_Z0 + 2 * LOCK_CLR"))
    mirrored(bx, "LocksMirror", feats, "XZ_Plane")
    # crush ribs on the long walls (z 10..22)
    cx = [c for c in ("CRUSH_X1", "CRUSH_X2", "CRUSH_X3", "CRUSH_X4", "CRUSH_X5")
          if ev("Params." + ("SBOX_L_X0" if L else "SBOX_R_X0")) + 4 < P[c] < ev("Params." + x1) - 4]
    s, b = sketch(bx, "CrushRibsSketch", "XY_Plane", 10)
    for c in cx:
        b.poly([("%s - 0.75" % c, "SB_HY - 0.1"), ("%s + 0.75" % c, "SB_HY - 0.1"), (c, "SB_HY + SBOX_CRUSH")])
    cr = pad(bx, "CrushRibs", s, 12)
    mirrored(bx, "CrushRibsMirror", [cr], "XZ_Plane")
    # snug ramp on each groove floor under the cover tongue's front end (closed position)
    lead = "-SB_XS + 0.5" if L else "%s - %s - 0.5" % (x1, W)
    s, b = sketch(bx, "SnugRampSketch", "XZ_Plane", "-(SB_WI - 0.01)")
    b.poly([("%s - %s1" % (lead, sg), "SLIDE_GF - 0.01"), ("%s + %s6" % (lead, sg), "SLIDE_GF - 0.01"),
            ("%s + %s4" % (lead, sg), "SLIDE_GF + SLIDE_SNUG"), ("%s - %s1" % (lead, sg), "SLIDE_GF + SLIDE_SNUG")])
    sr = pad(bx, "SnugRamp", s, "SLIDE_GROOVE_D + 0.01", reversed_=True)
    mirrored(bx, "SnugRampMirror", [sr], "XZ_Plane")
    # pull tab at the inner end (seam side) with a finger hole
    t0, t1 = ("%s - 0.5" % x1, -11) if L else (11, "%s + 0.5" % x0)
    s, b = sketch(bx, "PullTabSketch", "XY_Plane", "SBOX_Z0")
    b.rect(t0, t1, -10, 10)
    pad(bx, "PullTab", s, F)
    lo = t0 if L else 11
    s, b = sketch(bx, "PullTabHoleSketch", "XY_Plane", "SBOX_Z0 + %s + 1" % F)
    b.rect("%s + 3" % lo, "%s + 8" % lo, -5, 5)
    pocket(bx, "PullTabHole", s, "%s + 2" % F)
    return bx


def silica_cover(doc, side):
    """Sliding cover (assembly position, closed)."""
    L = side == "L"
    x0, x1 = ("SBOX_L_X0", "SBOX_L_X1") if L else ("SBOX_R_X0", "SBOX_R_X1")
    inner = x1 if L else x0
    sg = "" if L else "-"
    cv = doc.addObject("PartDesign::Body", "SilicaBoxCover_" + side)
    o = "SBOX_W + SLIDE_CLR"
    s, b = sketch(cv, "PlateSketch", "XY_Plane", "SLIDE_G0")
    if L:
        b.rrect_cut("SB_HX - (%s)" % o, "SB_HY - (%s)" % o, "SB_R - (%s)" % o, "%s - (%s)" % (x1, o))
    else:
        b.rect("%s + %s" % (x0, o), "%s - (%s)" % (x1, o), "-(SB_HY - (%s))" % o, "SB_HY - (%s)" % o)
    pad(cv, "Plate", s, "SLIDE_T")
    s, b = sketch(cv, "OverEndSketch", "XY_Plane", "SLIDE_G0")      # over the lowered end wall + finger tab
    if L:
        b.rect("%s - SBOX_W - 1" % x1, x1, "-(SB_WI - SLIDE_CLR)", "SB_WI - SLIDE_CLR")
    else:
        b.rect(x0, "%s + SBOX_W + 1" % x0, "-(SB_WI - SLIDE_CLR)", "SB_WI - SLIDE_CLR")
    pad(cv, "OverEnd", s, "SLIDE_T")
    s, b = sketch(cv, "TabSketch", "XY_Plane", "SLIDE_G0")
    if L:
        b.rect(x1, "%s + SLIDE_TAB" % x1, -25, 25)
    else:
        b.rect("%s - SLIDE_TAB" % x0, x0, -25, 25)
    pad(cv, "Tab", s, "SLIDE_T")
    g0, g1 = ("-SB_XS + 0.5", x1) if L else (x0, "%s - SBOX_W - 0.5" % x1)
    s, b = sketch(cv, "TongueSketch", "YZ_Plane", "((%s) + (%s)) / 2" % (g0, g1))
    b.poly([("SB_WI - SLIDE_CLR - 0.01", "SLIDE_GF + SLIDE_VCLR"), ("SLIDE_TIP", "SLIDE_GF + SLIDE_VCLR"),
            ("SLIDE_TIP", "SLIDE_CT - (SLIDE_TIP - SB_WI)"), ("SB_WI", "SLIDE_CT"), ("SB_WI - SLIDE_CLR - 0.01", "SLIDE_CT")])
    tg = pad(cv, "Tongue", s, "(%s) - (%s)" % (g1, g0), midplane=True)
    lead = g0 if L else g1
    s, b = sketch(cv, "TongueTaperSketch", "XY_Plane", "SLIDE_CT + 1")   # leading end tapered in plan
    b.poly([(lead, "SB_WI - SLIDE_CLR"), (lead, "SLIDE_TIP + 1"), ("%s + %s3" % (lead, sg), "SLIDE_TIP + 1")])
    tt = pocket(cv, "TongueTaper", s, 10)
    mirrored(cv, "TonguesMirror", [tg, tt], "XZ_Plane")
    ec = "%s - %sSBOX_W / 2" % (inner, sg)
    s, b = sketch(cv, "DetentBumpSketch", "XZ_Plane", 0)              # half-round bump under the cover
    b.half_round(ec, "SLIDE_G0 + 0.01", 0.5, False)                 # 0.5 proud, clicks into the 0.7 notch
    pad(cv, "DetentBump", s, 30, midplane=True)
    return cv


def build_silica(doc):
    for side in ("L", "R"):
        silica_box(doc, side)
        silica_cover(doc, side)
    # slide bolt (+Y side, at x = 0) and its 6 copies
    lb = doc.addObject("PartDesign::Body", "LockBolt")
    ys = "LOCK_YT - LOCK_TIP_L"                                  # gable back | flat tip
    hw = "LOCK_W / 2"
    s, b = sketch(lb, "BoltBarSketch", "XZ_Plane", "-(LOCK_YT - LOCK_LEN + %s) / 2" % ys)
    b.poly([("-%s + 0.4" % hw, "LOCK_Z0"), ("%s - 0.4" % hw, "LOCK_Z0"), (hw, "LOCK_Z0 + 0.4"), (hw, "LOCK_Z1"),
            (0, "LOCK_Z1 + %s" % hw), ("-" + hw, "LOCK_Z1"), ("-" + hw, "LOCK_Z0 + 0.4")])
    pad(lb, "BoltBar", s, "%s - (LOCK_YT - LOCK_LEN)" % ys, midplane=True)
    s, b = sketch(lb, "BoltTipSketch", "XZ_Plane", "-(LOCK_YT - LOCK_TIP_L / 2)")
    b.poly([("-%s + 0.4" % hw, "LOCK_Z0"), ("%s - 0.4" % hw, "LOCK_Z0"), (hw, "LOCK_Z0 + 0.4"), (hw, "LOCK_Z1 - 0.4"),
            ("%s - 0.4" % hw, "LOCK_Z1"), ("-%s + 0.4" % hw, "LOCK_Z1"), ("-" + hw, "LOCK_Z1 - 0.4"), ("-" + hw, "LOCK_Z0 + 0.4")])
    pad(lb, "BoltTip", s, "LOCK_TIP_L", midplane=True)
    s, b = sketch(lb, "BoltPostSketch", "XY_Plane", "SBOX_Z0 - 2")
    b.rect(-3, 3, "LOCK_YT - LOCK_LEN", "LOCK_YT - LOCK_LEN + 3")
    pad(lb, "BoltPost", s, "LOCK_Z0 + 0.01 - SBOX_Z0 + 2")
    s, b = sketch(lb, "BoltBumpSketch", "XY_Plane", "LOCK_Z0 + 0.4")      # detent ridges on both sides: 0.2 click
    for sg in ("-", ""):
        b.circle("%sLOCK_W / 2" % sg, "LOCK_YT - LOCK_LEN / 2", "LOCK_CLR + 0.2")
    pad(lb, "BoltBump", s, "LOCK_Z1 - LOCK_Z0 - 0.4")
    k = 0
    for lx in ("LOCK_X1", "LOCK_X2", "LOCK_X3"):
        for sy in (1, -1):
            k += 1
            ln = doc.addObject("App::Link", "LockBolt_%d" % k)
            ln.LinkedObject = lb
            ln.Placement = App.Placement(V(P[lx], 0, 0), App.Rotation(V(0, 0, 1), 0 if sy > 0 else 180))
            ln.setExpression(".Placement.Base.x", "Params." + lx)
    # handle v2 for the long box (legs through the floor holes, ledge under the floor, filament through the leg holes)
    hd = doc.addObject("PartDesign::Body", "SilicaBoxHandle")
    z = lambda e: "SBOX_Z0 + (%s)" % e
    s, b = sketch(hd, "HandleBarSketch", "YZ_Plane", "HANDLE_X")
    b.rect(-16, 16, z(-10), z(-7))
    pad(hd, "HandleBar", s, "HANDLE_HOLE_X - 0.2", midplane=True)
    s, b = sketch(hd, "HandleLegsSketch", "YZ_Plane", "HANDLE_X")
    for sy in ("", "-"):
        yc = "%sHANDLE_Y" % sy
        b.poly([("%s - 3.5" % yc, z(-7.01)), ("%s + 3.5" % yc, z(-7.01)), ("%s + 2.5" % yc, z(-3)), ("%s + 2.5" % yc, z(0)),
                ("%s - 2.5" % yc, z(0)), ("%s - 2.5" % yc, z(-3))])
    pad(hd, "HandleLegs", s, "HANDLE_HOLE_X - 0.2", midplane=True)
    s, b = sketch(hd, "HandleTipsSketch", "YZ_Plane", "HANDLE_X")
    tip = "HBAR_Z + HBAR_HOLE / 2 + 1.2"
    for sy in ("", "-"):
        yc = "%sHANDLE_Y" % sy
        b.poly([("%s - 1.5" % yc, z(-0.01)), ("%s + 1.5" % yc, z(-0.01)), ("%s + 1.5" % yc, z("%s - 0.8" % tip)),
                ("%s + 0.7" % yc, z(tip)), ("%s - 0.7" % yc, z(tip)), ("%s - 1.5" % yc, z("%s - 0.8" % tip))])
    pad(hd, "HandleTips", s, "HANDLE_HOLE_X - 0.2", midplane=True)
    s, b = sketch(hd, "HandleLockHoleSketch", "XZ_Plane", 0)
    b.rect("HANDLE_X - HBAR_HOLE / 2", "HANDLE_X + HBAR_HOLE / 2", z("HBAR_Z - HBAR_HOLE / 2"), z("HBAR_Z + HBAR_HOLE / 2"))
    pocket(hd, "HandleLockHole", s, through=True, midplane=True)


def build_outlet(doc):
    """Grommet and tethered cap (TPU, print orientation at the origin) + links in place."""
    gr = doc.addObject("PartDesign::Body", "Grommet")
    s, b = sketch(gr, "GrommetProfileSketch", "XZ_Plane", 0)          # XZ: x = r, y = z; flange on the bed
    rb, rr = "GROM_BORE / 2 + GROM_PRESS", "GROM_BORE / 2 + GROM_RIB"
    hf = "(GROM_FL_R2 - (%s))" % rb                                   # 45 deg cone flange height
    top = "%s + GROM_L" % hf
    z = lambda d: "%s + %s" % (hf, d)
    mouth = "3.6 - GROM_MOUTH_CH * 1.45 / 3.5"                      # funnel r at z = GROM_MOUTH_CH
    b.poly([(mouth, "GROM_MOUTH_CH"), ("3.6 + GROM_MOUTH_CH - GROM_MOUTH_CH * 1.45 / 3.5", 0), ("GROM_FL_R2", 0), (rb, hf), (rb, z(2.5)), (rr, z(2.5)), (rb, z(4.5)), (rb, z(6.0)),
            (rr, z(6.0)), (rb, z(8.0)), (rb, "%s - 3" % top), ("GROM_BORE / 2 - 0.6", top), ("GROM_CLEAR / 2", top),
            ("GROM_CLEAR / 2", 3.5)])
    revolve(gr, "GrommetBody", s, "V_Axis")
    s, b = sketch(gr, "SealingLipsSketch", "XZ_Plane", 0)              # two lips angled in the push-in direction
    for d in (3.0, 8.0):
        b.poly([("GROM_LIP / 2", z(d + 0.9)), ("GROM_CLEAR / 2 + 0.1", z(d)), ("GROM_CLEAR / 2 + 0.1", z(d + 0.7)),
                ("GROM_LIP / 2", z(d + 1.5))])
    revolve(gr, "SealingLips", s, "V_Axis")

    cp = doc.addObject("PartDesign::Body", "CapTether")
    s, b = sketch(cp, "CapProfileSketch", "XZ_Plane", 0)
    tip = "CAP_T + CAP_PEG_L + 3"
    b.poly([(1.5, 0), ("CAP_R2", 0), ("CAP_R1", "CAP_T"), ("CAP_PEG_D / 2", "CAP_T"), ("CAP_PEG_D / 2", "CAP_T + CAP_PEG_L"),
            (1.6, tip), (1.3, tip), ("FIL_HOLE / 2", "%s - 2.5" % tip), ("FIL_HOLE / 2", 1.2)])
    revolve(cp, "Cap", s, "V_Axis")
    s, b = sketch(cp, "StrapSketch", "XY_Plane", 0)
    b.rect(6.5, "TETHER_L - 4", "-STRAP_W / 2", "STRAP_W / 2")
    pad(cp, "Strap", s, "STRAP_T")
    s, b = sketch(cp, "PullTabSketch", "XY_Plane", 0)                 # lift this with a fingernail
    b.slot_x("-(TAB_L - TAB_W / 2)", "-(CAP_R2 - 2)", "TAB_W / 2")
    pad(cp, "PullTab", s, "STRAP_T")
    s, b = sketch(cp, "AnchorProfileSketch", "XZ_Plane", 0)
    sk = s
    sk.AttachmentOffset = App.Placement(V(P["TETHER_L"], 0, 0), App.Rotation())
    sk.setExpression(".AttachmentOffset.Base.x", "Params.TETHER_L")       # its V axis = the anchor axis
    # 45 deg cone head (wide end on the bed / at the top in the lid), 0.2 clear of the lid's anchor cone
    b.poly([(0, 0), ("ANCHOR_CONE_R0 + 2 - 0.2", 0), ("ANCHOR_CONE_R0 - 0.2", 2.0), ("ANCHOR_D / 2", 2.0),
            ("ANCHOR_D / 2", 6.3), ("ANCHOR_D / 2 + 0.15", 6.3), (1.3, "ANCHOR_HOLE_L + 0.8"), (0, "ANCHOR_HOLE_L + 0.8")])
    revolve(cp, "Anchor", s, "V_Axis")

    zf = "Params.GROM_ZB + Params.GROM_FL_R2 - 0.1 - Params.GROM_BORE / 2"   # flange wide end on the lid cone
    ln = doc.addObject("App::Link", "Grommet_InLid")
    ln.LinkedObject = gr
    ln.Placement = App.Placement(V(P["OUT_X"], 0, ev(zf)), App.Rotation(V(1, 0, 0), 180))
    ln.setExpression(".Placement.Base.x", "Params.OUT_X")
    ln.setExpression(".Placement.Base.z", zf)
    zc = "Params.ZT - Params.CAP_RECESS"                                   # cap top (its print bed face)
    ln = doc.addObject("App::Link", "Cap_InLid")
    ln.LinkedObject = cp
    ln.Placement = App.Placement(V(P["OUT_X"], 0, ev(zc)), App.Rotation(V(1, 0, 0), 180))
    ln.setExpression(".Placement.Base.x", "Params.OUT_X")
    ln.setExpression(".Placement.Base.z", zc)

    # (no pocket support: the 20 mm pocket floor prints as a bridge, the lid prints top-face-down)


def build_cradle(doc):
    """Mini hygrometer cradle (assembly position). YZ sketches: x = y, y = z, offset along +x."""
    cr = doc.addObject("PartDesign::Body", "HygroCradle")
    s, b = sketch(cr, "CradleShellSketch", "YZ_Plane", "CR_BX0")
    b.rect("-CR_HW - 2", "CR_HW + 2", "CR_ZB", "CRADLE_Z1")
    pad(cr, "CradleShell", s, "HY_FACE_X - CR_BX0")
    s, b = sketch(cr, "PocketSketch", "YZ_Plane", "HY_FACE_X + 1")
    b.rect("-CR_HW", "CR_HW", "CR_ZB + 2", "CR_ZT")
    pocket(cr, "HygroPocket", s, "HY_FACE_X + 1 - CR_BX0 - 2")
    s, b = sketch(cr, "BackStopsSketch", "YZ_Plane", "CR_BX0 + 1")
    b.rect(-18.8, -17.2, "CR_ZB + 1", "CR_ZT + 1")
    b.rect(17.2, 18.8, "CR_ZB + 1", "CR_ZT + 1")
    pad(cr, "BackStops", s, "CR_HB - CR_BX0 - 1")
    s, b = sketch(cr, "GripRibsSketch", "YZ_Plane", "CR_BX0 + 1")
    for sy in ("", "-"):
        for f in (0.3, 0.7):
            z = "CR_ZB + 2 + CR_HH * %s" % f
            b.poly([("%sCR_HW" % sy, "%s - 1" % z), ("%s(CR_HW - 0.45)" % sy, z), ("%sCR_HW" % sy, "%s + 1" % z)])
    pad(cr, "GripRibs", s, "HY_FACE_X - CR_BX0 - 2")
    s, b = sketch(cr, "TenonSketch", "YZ_Plane", "CR_BX0")
    z0, z1 = "CRADLE_Z1", "CRADLE_Z1 + CD_H"
    b.poly([("CD_N0 + CD_CLR", "%s - 1" % z0), ("CD_N1 - CD_CLR", "%s - 1" % z0), ("CD_N1 - CD_CLR", z0),
            ("CD_W1 - CD_CLR", "%s - CD_CLR" % z1), ("CD_W0 + CD_CLR", "%s - CD_CLR" % z1), ("CD_N0 + CD_CLR", z0)])
    t = pad(cr, "Tenon", s, "CD_X1 - CD_CLR - CR_BX0")
    mirrored(cr, "TenonMirror", [t], "XZ_Plane")
    s, b = sketch(cr, "BackWindowSketch", "YZ_Plane", "CR_BX0 + 3")
    b.rect(-14, 14, "CR_ZB + 6", "CR_ZT - 5")
    pocket(cr, "BackWindow", s, 4)
    s, b = sketch(cr, "FloorVentsSketch", "XY_Plane", "CR_ZB + 2.1")
    b.rect("CR_HB + 2", "HY_FACE_X + 1", "CR_HW - 8", "CR_HW - 2")
    b.rect("CR_HB + 2", "HY_FACE_X + 1", "-CR_HW + 2", "-CR_HW + 8")
    pocket(cr, "FloorVents", s, 3.1)


def report(doc):
    bad = []
    for o in doc.Objects:
        if o.TypeId == "Sketcher::SketchObject":
            if not o.FullyConstrained:
                bad.append(o.Name)
        if o.State and ("Invalid" in o.State or "Error" in o.State):
            bad.append("%s %s" % (o.Name, o.State))
    print("V2 sketches not fully constrained / errors:", bad or "none")
    for n in ("BoxRef", "Lid", "Latch", "Gasket", "Lid_L", "Lid_R", "SeamStrip", "Hanger_B", "Hanger_A", "HubHalfA",
              "HubHalfB", "HubRetainer", "StubAxle", "StubClip", "SilicaBox_L", "SilicaBox_R", "SilicaBoxCover_L", "SilicaBoxCover_R", "LockBolt",
              "SilicaBoxHandle", "Grommet", "CapTether", "HygroCradle"):
        s = doc.getObject(n).Shape
        print("V2 %-10s valid %s solids %d volume %.1f cm3" % (n, s.isValid(), len(s.Solids), s.Volume / 1000))
    print("V2 gasket length to cut: %.1f mm" % doc.Params.G_LEN.Value if hasattr(doc.Params.G_LEN, "Value") else doc.Params.G_LEN)


def style(doc):
    """Folders, colours, visibility (GUI only). A body shows its Tip feature, so only the Tip is left visible.
    Bodies used through links (one latch, one bolt, one adapter, grommet, cap) stay hidden; the links show them."""
    import FreeCADGui as Gui
    for b in doc.Objects:
        if b.TypeId == "PartDesign::Body":
            for o in b.Group:
                if o.TypeId.startswith(("PartDesign::", "Sketcher::")):
                    o.ViewObject.Visibility = (o == b.Tip)
    PETG1, PETG2, TPU, GREY, DARK, BLUE = ((0.95, 0.62, 0.2), (0.95, 0.72, 0.3), (0.85, 0.3, 0.55),
                                           (0.82, 0.82, 0.85), (0.25, 0.25, 0.28), (0.2, 0.45, 0.85))
    look = {"BoxRef": (GREY, 70, True), "Lid": (None, 0, False), "Lid_L": (PETG1, 0, True), "Lid_R": (PETG2, 0, True),
            "SeamStrip": (TPU, 0, True), "Gasket": (TPU, 0, True), "Latch": (BLUE, 0, False),
            "Hanger_B": (PETG1, 0, True), "Hanger_A": (PETG1, 0, True), "StubAxle": (DARK, 0, False),
            "HubHalfA": ((0.91, 0.62, 0.22), 0, False), "HubHalfB": ((0.2, 0.5, 0.8), 0, False),
            "HubRetainer": ((0.85, 0.3, 0.28), 0, False), "StubClip": ((0.95, 0.8, 0.15), 0, False),
            "SilicaBox_L": ((0.94, 0.8, 0.25), 0, True),
            "SilicaBox_R": ((0.94, 0.8, 0.25), 0, True), "SilicaBoxCover_L": ((0.4, 0.6, 0.9), 0, True),
            "SilicaBoxCover_R": ((0.4, 0.6, 0.9), 0, True), "LockBolt": (DARK, 0, False),
            "SilicaBoxHandle": ((0.2, 0.7, 0.35), 0, True), "Grommet": (TPU, 0, False), "CapTether": (TPU, 0, False),
            "HygroCradle": (PETG1, 0, True)}
    for n, (c, t, vis) in look.items():
        vo = doc.getObject(n).ViewObject
        if c:
            vo.ShapeColor = c
        vo.Transparency = t
        vo.Visibility = vis
    folders = {"1 Reference (box, gasket)": ["BoxRef", "Gasket"],
               "2 Lid": ["Lid", "Lid_L", "Lid_R", "SeamStrip", "Latch", "Latch_1", "Latch_2", "Latch_3", "Latch_4"],
               "3 Spool hanger": ["Hanger_B", "Hanger_A", "HubHalfA", "HubHalfB", "HubRetainer", "StubAxle", "StubClip",
                                 "HubHalfA_Asm", "HubHalfB_Asm"] +
                                ["%s_%s" % (n, k) for n in ("HubRetainer", "StubAxle", "StubClip") for k in "AB"],
               "4 Silica": ["SilicaBox_L", "SilicaBox_R", "SilicaBoxCover_L", "SilicaBoxCover_R", "LockBolt",
                            "SilicaBoxHandle"] + ["LockBolt_%d" % k for k in range(1, 7)],
               "5 Outlet (TPU)": ["Grommet", "CapTether", "Grommet_InLid", "Cap_InLid"],
               "6 Hygrometer": ["HygroCradle"],
               "7 Split cutters": ["Lid_L_Cutter", "Lid_R_Cutter", "SeamStrip_Cutter"]}
    for fname, names in folders.items():
        grp = doc.addObject("App::DocumentObjectGroup", fname.split(" ", 1)[1].replace(" ", "_").replace("(", "").replace(")", "").replace(",", ""))
        grp.Label = fname
        for n in names:
            grp.addObject(doc.getObject(n))
    for c in ("Lid_L_Cutter", "Lid_R_Cutter", "SeamStrip_Cutter"):
        doc.getObject(c).ViewObject.Visibility = False
    for o in doc.Objects:
        if o.TypeId == "App::Link":
            o.ViewObject.Visibility = True
    v = Gui.getDocument(doc.Name).activeView()
    v.viewIsometric()
    v.fitAll()


doc = build()
build_spool(doc)
build_silica(doc)
build_outlet(doc)
build_cradle(doc)
doc.recompute()
report(doc)
if App.GuiUp:
    style(doc)
doc.saveAs(OUT)
print("V2 saved", OUT)
