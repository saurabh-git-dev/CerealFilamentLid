"""
Smart lid + spool hanger for an EXISTING cereal box (fully printed: PETG + TPU seals),
split for the Bambu A1 mini (180 mm bed, every part <= 175 mm).

The box is not modelled for printing - only its rim (measured) as a reference:
    inner length 220, inner width 91..94 (walls bow a little), wall 2 mm,
    outside perimeter ~590 mm  ->  outer corner radius ~30 mm (computed, CHECK with Test_Corner),
    rim wall rises 7.5 mm above a horizontal flange that sticks out 3.5 mm and is 3.35 mm thick.

Lid features
    * inner locating lip drops 4.6 mm inside the box rim (fits the narrowest 91 mm width);
      gasket groove 3.5 wide x 4.8 deep, centred over the rim wall, takes the OLD LID's gasket
      (3.25 wide x 6 tall, standing on edge, cut to length) or the printed TPU copy
    * 4 over-centre latches (2 per long side) that hook under the box flange; NO pins: the latch hub
      has a C-shaped opening and snaps down onto two 4 mm stubs built into the lid's latch slot
    * deep lid (30 mm above the rim): two CLOSED silica boxes sit inside the hollow underside.
      Each box = slotted body + snap-on cover; it clicks into grooves in the lid walls.
      To refill: lid off, pull the box out by its tab, pop the cover, pour / refill, snap shut, push back.
    * filament outlet on TOP, near the front, sunk in a pocket so the lid stays flat for stacking:
      press-in TPU grommet (push a 4 mm PTFE tube straight down through it) + tethered TPU plug;
      when a tube is fitted the plug parks in its own hole at the other end of the pocket
    * front: hygrometer cradle hanging inside, display facing the box front wall (read through the box).
      Two interchangeable cradles on the same dovetails: the common black mini digital hygrometer
      (48 x 28.6 x 15.2, pushes straight in from the front, held by crush ribs) or a 50 x 50 x 10 one
    * two hanger arms carry an 8 mm axle; spool spins on 608 bearings in stepped hub adapters
      (lifting the lid lifts the spool out)
    * lid halves (split at x = 0, 1 mm TPU seam strip) are screwed together so the seam can be pulled
      airtight: 8 x M3 across the spine rib (brass inserts in the -X half)
    * no screws for the rest: hanger arms slide into dovetail sockets (they also bridge the seam),
      the hygrometer cradle slides onto two dovetails (towards the front wall, pull back to remove)

Run inside FreeCAD:  exec(open(r"<path>/cereal_lid.py").read())
Builds document "CerealLid" and exports print-oriented STLs to ./stl_cereal/.

Axes: X = long axis (front = +X end), Y = short axis (spool axis), Z = up, Z = 0 = top of box rim.
"""
import os
import math
import FreeCAD as App
import Part
import MeshPart
from FreeCAD import Vector as V

HERE = r"C:\Users\SK\Desktop\Personal\CerealFilamentLid\v1\source"

# ---------------- Measured box (mm) ----------------
BOX_IL = 220                   # inner length
BOX_IW_MIN, BOX_IW_MAX = 91, 94  # inner width varies along the length
WALL = 2
R_BOX = 30                     # OUTER corner radius of the rim (from 590 mm perimeter) - verify!
RIM_H = 7.5                    # rim wall height above the flange
FLANGE_OUT, FLANGE_T = 3.5, 3.35
BOX_DEPTH = 210                # measured inside depth below the rim top

# ---------------- Lid ----------------
SKIRT_T = 3.2                  # thick: walls print across layer lines (weakest direction)
SKIRT_BOT = -6.0               # skirt bottom (flange top is at -7.5)
ZT = 30.0                      # top of lid (deep: silica bay)
PLATE_T = 3.0
BAND_IN = 42                   # inner face of the perimeter band (long sides) -> 3 mm inner lip
BAND_IN_X = 105.5              # inner face of the band at the ends
# Gasket: 3.25 wide x 6 tall strip on edge (old lid's gasket, or printed TPU), stands 1.2 proud
G_W_STRIP, G_T = 3.25, 6.0
G_GROOVE_W, G_RECESS, G_SQUEEZE = 3.5, 4.8, 0.5
SEAT = G_T - G_RECESS - G_SQUEEZE      # underside of band when latched (z) -> 0.7
LIP_CLR = 0.5                  # inner lip clearance to the narrowest inner wall
LIP_BOT = -4.0                 # inner lip reaches this far down inside the rim
SEAM = 0.5                     # half of the TPU seam strip thickness
# Latches
LATCH_X = (-55, 55)
LW = 24                        # latch width
PY, PZ = 49.5, 12.0            # pivot (inboard of the flange contact -> over-centre, self locking)
HUB_R = 4.5
STUB_D, STUB_L = 4.0, 2.5      # pivot stubs on the lid slot walls (go 2.2 mm into each side of the hub)
C_OPEN = 3.4                   # hub C-opening (stub snaps through it, 0.6 mm interference)
ARM_I, ARM_T = 53.3, 3.5       # arm just outside the skirt (52.8) / flange (52.5)
LIP_TIP = 49.2                 # lip tip (rim wall outside is at 47.5..49)
LATCH_PRELOAD = 0.3            # lip top sits this much above the flange underside
# Locking bump on the lip top -> snaps into the groove under the rim flange
RIM_GROOVE_C = 1.75            # groove centre, measured in from the flange's outer edge (MEASURE at the latches)
RIM_GROOVE_D, RIM_GROOVE_W = 1.5, 2.0
BUMP_H, BUMP_BASE, BUMP_TIP = 2.0, 2.6, 1.0
LATCH_EXTRA = 2.0              # lip reaches 2 mm lower than the nominal design: tested 2026-10-23 with the old
                               # gasket - closes by hand, and the 2 mm ridge clicks into the flange groove
# Outlet on the lid top, sunk in a pocket (flush for stacking)
OUT_X, PARK_X = 76.0, 100.0    # outlet (grommet) and the cap tether anchor hole, both at y = 0
POCKET_R, POCKET_D = 10.0, 6.0 # stadium pocket in the lid top joining the two
GROM_L = 12.0                  # grommet body length
GROM_BORE = 10.0
GROM_CLEAR, GROM_LIP = 4.3, 3.4  # grommet bore (clearance on the 4.0 tube) and its two sealing lips
FIL_HOLE = 2.0                 # cap hole for 1.75 mm filament: prints ~1.8, filament slides, TPU closes around it
GROM_FL_R = 9.0                # grommet flange radius (sits on the pocket floor)
CAP_PEG_D = 4.3                # cap peg: a bit fatter than the 4.0 tube -> firmer seal in the grommet lips
ANCHOR_HOLE_D, ANCHOR_HOLE_L = 4.2, 9.0   # small hole at the far end of the pocket (tether anchor)
ANCHOR_D = 4.35                # anchor peg: light press + small barb (eSUN 95A is firm; 4.6 was too tight)
GROM_PRESS, GROM_RIB = 0.05, 0.25  # grommet body / grip-ring oversize per side in the 10 mm bore (was 0.2 / 0.5)
TETHER_L = 29.0                # cap centre to anchor centre along the strap (24 mm apart in the pocket: 5 mm slack)
# Silica boxes (closed: body + snap-on cover), clicked into the lid underside
SBOX_X = ((-105.6, -19.0), (19.0, 62.0))   # x ranges (left, right); right ends before the outlet zone
SBOX_SNAPS_X = ((-72, -40), (40,))   # on the straight part of the side walls (|x| < 80)
SBOX_CLR = 0.3                 # gap to the lid walls / ceiling (0.4 rattled)
SBOX_Z0 = 1.0                  # bottom of the box
SBOX_W = 2.4                   # wall (1.6 was flimsy)
SBOX_FLOOR = 2.0               # floor
SBOX_TAB_T = 1.0               # spring tab (outer skin of the double wall at each snap)
SBOX_TAB_GAP = 1.6             # air gap behind it (bump needs 1.4 of travel)
SBOX_SNAP_BOSS = 1.0           # inner wall bulges in this much at each snap -> 0.8 mm solid inner skin
SBOX_BUMP = 1.4                # snap bump reach past the wall face (-> ~1 mm into the lid groove; was 0.9)
# Slide-bolt locks (replace the spring snap at these grooves): bolt in a closed tunnel, switch tab under the floor
LOCK_X = (-72, -40, 40)        # slide-bolt locks (the long box had spring snaps at -72: they fought the pull-out)
LOCK_W, LOCK_Z0, LOCK_Z1 = 8.0, 5.9, 8.1      # bolt width (x) and height (z) - lid groove is z 5.5..8.5
LOCK_LEN, LOCK_REACH, LOCK_TRAVEL = 12.0, 1.3, 1.6   # tip 1.3 past the wall (1.0 into the groove); 1.6 throw
LOCK_CLR = 0.15
# clip-on D-handle at the rounded end of the long box (the spool is 15+ mm below there): two snap holes in the floor
HANDLE_X, HANDLE_Y, HANDLE_T = -95.1, 12.0, 6.0   # hole centre x (in place of the -95.7 slot), legs at +-y, thickness
HANDLE_HOLE = (HANDLE_T + 0.4, 3.2)               # hole x / y size
HBAR = 2.0                     # handle v2: square lock bar through both leg tips (inside the box)
HBAR_HOLE = 2.15
HBAR_Z = SBOX_FLOOR + 0.05 + HBAR_HOLE / 2       # bar hole bottom 0.05 over the floor's inner face -> ~0.2 total play
PULL_SLOT_X = {"L": -59.7, "R": 28.9}   # floor slot the puller clips into (mid box, clear of snaps / lock blocks)
SBOX_CRUSH = 0.4               # crush ribs on the long walls: 0.4 proud into the 0.3 gap -> snug, no rattle
SBOX_CRUSH_X = (-80, -56, -28, 26, 54)   # straight wall, away from the snap tabs
# Sliding cover (pencil-box style): tongues on its long edges run in grooves near the top of the box's long
# walls; it can only come out by sliding towards the box's inner end (seam side); a small bump clicks into a
# notch on the lowered inner end wall when closed.
SLIDE_T = 2.2                  # cover plate thickness
SLIDE_LIP = 1.0                # box wall left above the cover groove
SLIDE_GROOVE_D, SLIDE_GROOVE_H = 1.2, 1.8   # groove depth into the long walls / height at the mouth (45 deg roof)
SLIDE_CLR = 0.3                # cover to box clearance (sides); was 0.25 + 0.15 vertical: slid rough
SLIDE_VCLR = 0.3               # tongue clearance top and bottom
SLIDE_SNUG = 0.4               # groove floor rises this much under the tongue's front end for the last 4 mm -> snug when shut
SLIDE_TAB = 4.0                # finger tab sticking out past the inner end wall
BOX_SNAP_Z = 7.0               # box-to-lid snap bump / band groove height
BEAD_SLOT = 1.2                # beads >= 2 mm
# Mini digital hygrometer (black LCD) for the side-loading cradle, display facing +X
MH_L, MH_W, MH_D = 44.5, 25.5, 13.0     # hygrometer BODY (user-measured), behind the face
MH_FL, MH_FW, MH_FT = 47.5, 28.0, 2.0    # its face plate: rests on the cradle front, sits ~1 mm off the box wall
MH_DROP = 5.5                  # pocket lowered so the whole display sits below the box rim / flange band
# Hygrometer 50 x 50 x 10, display facing +X
HY_W, HY_H, HY_D = 50.0, 50.0, 10.0
HY_FACE_X = 107.0              # front of cradle (box inner wall at 110, corners curve in)
HY_TOP = -7.5
# Spool hanger
SPOOL_D = 200
SPOOL_W, SPOOL_HOLE = 67.0, 55.0   # width across the flanges (assumed), hub hole (user: ~55)
# hub adapter spigot: a bit under the hole, crush ribs take up the rest -> the flange sits flat on the spool face
HUB_SPIGOT_D, HUB_RIB_PROUD, HUB_RIBS = SPOOL_HOLE - 0.8, 0.6, 8
D_AXLE = BOX_DEPTH - SPOOL_D / 2 - 4   # 106: spool clears the floor by 4, top 6 below the rim
ARM_Y0, ARM_Y1 = 36.5, 41.25   # hanger arm plate (inside the band and the narrowest wall, 45.5)
# hanger dovetail: socket in a block under the lid, open towards -X, closed at the +X end
DT_Z0, DT_Z1 = 1.0, 7.0        # socket bottom (opening) / ceiling
# Full dovetail whose profile lies in the arm's own plane (XZ): the hanger prints flat with no overhang,
# both flanks lock. It slides OUTWARD (+Y) into a socket open towards the middle of the box, closed at the wall.
DT_HALF0, DT_HALF1 = 12.0, 15.0    # |x| at the socket opening (z = DT_Z0) / at the ceiling (z = DT_Z1)
DT_Y0, DT_OUT = 29.0, ARM_Y1 + 0.25    # socket y: open end (cavity side), closed end (towards the wall)
DT_TENON_Y0 = 33.25                # tenon starts here (extends 3.25 mm past the arm's inner face)
DT_CLR = 0.25                  # (only used as the "tenon" flag of dovetail())
# tenon flanks PARALLEL to the socket's, modelled DT_SEAT above them; the ribs on the top press it down that far, so
# both flanks seat over their full face (not just the top edge -> it rocked). Top gap DT_TOP_GAP before pressing.
DT_SEAT, DT_TOP_GAP = 0.3, 0.2
DT_RIB_GRIP, DT_RIB_X, DT_RIB_W, DT_RIB_RAMP = 0.35, (-8.0, 0.0, 8.0), 1.2, 2.5
CRADLE_Z1 = -4.5               # hygrometer cradle mounting face
# hygrometer cradle dovetails (one each side of the PTFE path): sockets open towards -X, closed at the front
CD_NARROW, CD_WIDE = (14.0, 22.0), (12.0, 24.0)   # |y| at the opening (z = CRADLE_Z1) / at the ceiling
CD_H = 6.0                                        # socket height
CD_X0, CD_X1 = 84.0, 95.0                         # socket x (open end, closed end)
CD_CLR = 0.15
AXLE_HOLE = 8.4                # pin mode: round hole for the full 8 mm axle
HANG_SLOT_DEG = 10.0           # hanger exit slot angle above horizontal
HOOK_STEP1, HOOK_STEP2, HOOK_EXIT, HOOK_RISE = 7.0, 16.0, 16.0, 5.0   # bayonet track (sideways, up, sideways, down, out)
AXLE_Y0 = -44.5                # axle tip (installed y); 8 mm shoulder at -Y, collar at +Y
AXLE_PLAY = 0.4                # neck gap to each face of the hanger plate
AXLE_NECK_R = 2.9              # neck where the axle sits in the hangers (flat underside kept at the bed)
AXLE_SLOT = 2 * AXLE_NECK_R + 0.4   # bayonet track width: the neck fits, the 8 mm body either side doesn't
AXLE_COLLAR_R, AXLE_COLLAR_T = 5.5, 2.0
AXLE_GRIP = 0.25               # grip ribs at the collar-end bearing seat: 0.25 proud on a 3.95 radius -> 0.2 into the 8 mm bore
AXLE_GRIP_Y = (21.6, 28.6)     # that bearing (installed y)
# snap-in hanger (test): sideways slot, snug on the neck, two spring lips at the mouth
SNAP_W = AXLE_NECK_R + 0.1     # slot half width
SNAP_LIP = 0.5                 # each lip narrows the mouth this much below the neck radius
SNAP_MOUTH_X = -24.0           # slot mouth (axle seat at x = 0)
# slide-lock hanger (test): sideways slot + a slider on the outer face that drops in front of the collar/shoulder
SL_XG, SL_GW, SL_TRAVEL = -8.5, 3.3, 12.0     # guide slot centre x / width, slider travel
SL_T, SL_TONGUE_T = 2.0, 1.2                  # slider / catch tongue thickness
SL_RIB = 0.25                                 # crush ribs on the slider back (0.2 air gap -> 0.05 preload)
# spring-return slide lock (test): user's spring 5.0 OD, 0.6 wire (3.8 ID), 10 free, ~5.5 fully squeezed
SP_OD, SP_ID, SP_FREE = 5.0, 3.8, 10.0
SP_STOP_R = 3.3                # small heads (6.6): 0.3 over the slot edge -> they hold the hangers from splaying apart
SP_TRAVEL = 4.0
SP_LOCKED = 9.8                # spring length locked (0.2 preload); open = 5.8
SP_PIN_R = 1.3                 # guide pins inside the coil (3.8 ID): teardrop, tip at 1.84
SP_Z0 = 5.0                    # spring channel bottom = stem rest (above the axle centre)
HANGER_STIFF = 2.2             # spring hangers: upper part thickened on the spool side (4.75 -> 6.95: ~3x stiffer sideways)
HANGER_STIFF_Z = 36.0          # ...down to this far above the axle (clear of the 66 mm adapter flanges)
HOOK_EXIT_RISE = 4.0           # exit climbs: an axle that ends up in the pocket before the exit can't slide out
HANG_MODE = "bayonet"          # "bayonet": open S-track, spool+axle+adapters come off as ONE unit (chosen) | "pin": pull-out axle
AXLE_TIP_Y = -43.0             # pin axle: tip just past the -Y arm (box wall at -45.5 stops it sliding further)
AXLE_HEAD_R, AXLE_HEAD_T = 6.0, 2.0
AXLE_R = 3.95                  # printed axle radius (bottom cut flat at 45 deg)
BEARING_D, BEARING_W = 22.15, 7.2
SPINE_Y = 20                   # full-height spine stops short of the hangers' slide-in path (tenons travel |y| 21..41)
SPINE_UPPER_Z0 = 7.5           # above the tenons' path the spine runs on to the hanger blocks (|y| 20..33)
BOLT_D = 3.4
M3_INSERT_D, M3_INSERT_L = 4.0, 5.0
# M3 across the spine (y, z): heads on the +X face, reachable from below with the silica boxes out
SEAM_BOLTS = ([(y, 5.0) for y in (-16.5, -8, 8, 16.5)] + [(y, 20.0) for y in (-12, 12)] +
              [(y, 13.0) for y in (-16.5, 16.5)] + [(y, 17.0) for y in (-27.0, 27.0)])   # last two: near the walls

# ---------------- Derived ----------------
OX = BOX_IL / 2 + WALL                 # 112   rim outside, ends
OY_MAX = BOX_IW_MAX / 2 + WALL         # 49    rim outside, long sides (widest)
OY_MIN = BOX_IW_MIN / 2 + WALL         # 47.5
R_BOX_IN = R_BOX - WALL
# gasket groove centred over the rim wall (its y position varies 46.5..48 with the 91..94 width)
GCX, GCY, GCR = OX - WALL / 2, (BOX_IW_MIN + BOX_IW_MAX) / 4 + WALL / 2, R_BOX - WALL / 2
h = G_GROOVE_W / 2
GIX, GIY, GIR = GCX - h, GCY - h, GCR - h              # groove inner edge
GOX, GOY, GOR = GCX + h, GCY + h, GCR + h              # groove outer edge
LIP_X = min(BOX_IL / 2 - LIP_CLR, GIX - 0.1)          # inner lip outer face (109.15, 45)
LIP_Y = min(BOX_IW_MIN / 2 - LIP_CLR, GIY - 0.1)
LIP_R = R_BOX_IN - LIP_CLR
SKX, SKY = max(OX + 0.6, GOX + 0.1), max(OY_MAX + 0.6, GOY + 0.1)   # skirt inner face
LX, LY = SKX + SKIRT_T, SKY + SKIRT_T  # lid outside
R_SK = max(R_BOX + 0.6, GOR + 0.1)
R_LID = R_SK + SKIRT_T
FLANGE_BOT = -RIM_H - FLANGE_T         # -10.85
LT = FLANGE_BOT + LATCH_PRELOAD        # latch lip top
OY_AVG = (OY_MAX + OY_MIN) / 2
BUMP_Y = OY_AVG + FLANGE_OUT - RIM_GROOVE_C   # bump centre (y), from the average box width
ARM_O = ARM_I + ARM_T
TAB_BOT = LT - 3 - 5
PLATE_Z0 = ZT - PLATE_T


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl_x(r, x0, x1, y, z):
    return Part.makeCylinder(r, x1 - x0, V(x0, y, z), V(1, 0, 0))


def cyl_y(r, y0, y1, x, z):
    return Part.makeCylinder(r, y1 - y0, V(x, y0, z), V(0, 1, 0))


def cyl_z(r, z0, z1, x, y):
    return Part.makeCylinder(r, z1 - z0, V(x, y, z0), V(0, 0, 1))


def vertical_edges(shape):
    return [e for e in shape.Edges
            if abs((e.Vertexes[-1].Point - e.Vertexes[0].Point).normalize().z) > 0.99]


def rrect(hx, hy, z0, z1, r):
    """Centred box (half sizes hx, hy) with rounded vertical edges."""
    b = box(-hx, hx, -hy, hy, z0, z1)
    return b.makeFillet(min(r, hy - 0.01), vertical_edges(b)) if r > 0 else b


def ring(hx0, hy0, r0, hx1, hy1, r1, z0, z1):
    return rrect(hx1, hy1, z0, z1, r1).cut(rrect(hx0, hy0, z0 - 1, z1 + 1, r0))


def prism_x(pts_yz, x0, x1):
    w = Part.makePolygon([V(x0, y, z) for y, z in pts_yz] + [V(x0, *pts_yz[0])])
    return Part.Face(w).extrude(V(x1 - x0, 0, 0))


def prism_y(pts_xz, y0, y1):
    w = Part.makePolygon([V(x, y0, z) for x, z in pts_xz] + [V(pts_xz[0][0], y0, pts_xz[0][1])])
    return Part.Face(w).extrude(V(0, y1 - y0, 0))


def clean(shape):
    try:
        r = shape.removeSplitter()
    except Exception:
        return shape
    return r if r.isValid() else shape


def fuse(shapes):
    return clean(shapes[0].fuse(shapes[1:])) if len(shapes) > 1 else shapes[0]


def mirror_y(s):
    return s.mirror(V(0, 0, 0), V(0, 1, 0))


# ---------------- Lid ----------------
def make_lid():
    shell = rrect(LX, LY, SKIRT_BOT, ZT, R_LID)
    cuts = [
        rrect(SKX, SKY, SKIRT_BOT - 1, SEAT, R_SK),                                     # over the rim
        rrect(BAND_IN_X, BAND_IN, SKIRT_BOT - 1, PLATE_Z0, R_BOX_IN - 4),              # cavity
    ]
    lid = shell.cut(fuse(cuts))

    parts = [box(-5.5, 5.5, -SPINE_Y, SPINE_Y, SEAT, PLATE_Z0 + 0.5)]                  # seam spine
    for sy in (1, -1):              # spine continues out to the hanger blocks ABOVE the hangers' slide path
        y0, y1 = sorted((sy * (SPINE_Y - 0.5), sy * 33))
        parts.append(box(-5.5, 5.5, y0, y1, SPINE_UPPER_Z0, PLATE_Z0 + 0.5))
    for sy in (1, -1):
        hb = box(-18.5, 18.5, 30, BAND_IN + 0.5, DT_Z0, PLATE_Z0 + 0.5)              # hanger socket block
        post = box(CD_X0, CD_X1 + 1.5, CD_WIDE[0] - 2, CD_WIDE[1] + 2, CRADLE_Z1, PLATE_Z0 + 0.5)  # cradle block
        parts += [hb, post] if sy > 0 else [mirror_y(hb), mirror_y(post)]
    ob = POCKET_R + 3                                          # pocket walls 3 mm thick all round
    parts.append(box(OUT_X - ob, BAND_IN_X + 0.5, -ob, ob, 2, PLATE_Z0 + 0.5))          # outlet block
    parts.append(ring(BAND_IN_X, BAND_IN, R_BOX_IN - 4, LIP_X, LIP_Y, LIP_R, LIP_BOT, SEAT + 0.5))  # inner lip
    lid = lid.fuse(parts)

    zp = ZT - POCKET_D                                       # pocket floor
    cuts = [
        # gasket recess
        ring(GIX, GIY, GIR, GOX, GOY, GOR, SEAT - 1, SEAT + G_RECESS),
        # outlet pocket (flush), grommet bore, PTFE passage, plug parking hole
        cyl_z(POCKET_R, zp, ZT + 1, OUT_X, 0), cyl_z(POCKET_R, zp, ZT + 1, PARK_X, 0),
        box(OUT_X, PARK_X, -POCKET_R, POCKET_R, zp, ZT + 1),
        cyl_z(GROM_BORE / 2, zp - GROM_L - 0.5, zp + 0.1, OUT_X, 0),
        cyl_z(ANCHOR_HOLE_D / 2, zp - ANCHOR_HOLE_L, zp + 0.1, PARK_X, 0),            # cap tether anchor
        cyl_z(3.0, -1, zp - GROM_L, OUT_X, 0),
        Part.makeCone(3.0, GROM_BORE / 2, GROM_BORE / 2 - 3.0,
                      V(OUT_X, 0, zp - GROM_L - 0.5 - (GROM_BORE / 2 - 3.0))),       # 45 deg step (prints clean)
    ]
    for sy in (1, -1):                                         # grooves the silica boxes click into
        for sx in [x for sn in SBOX_SNAPS_X for x in sn]:
            cuts.append(box(sx - 9, sx + 9, sy * BAND_IN - 1.2, sy * BAND_IN + 1.2, BOX_SNAP_Z - 1.5, BOX_SNAP_Z + 1.5))
    for sy in (1, -1):
        c = [prism_y(dovetail(0), DT_Y0, DT_OUT),                                      # hanger socket
             prism_x(cradle_dovetail(0), CD_X0 - 1, CD_X1)]                                # cradle socket
        cc = fuse(c)
        cuts.append(cc if sy > 0 else mirror_y(cc))
    for y, z in SEAM_BOLTS:                                    # insert in the -X half, bolt from +X
        cuts += [cyl_x(M3_INSERT_D / 2, -5.6, 0, y, z), cyl_x(BOLT_D / 2, 0, 5.6, y, z)]
    for lx in LATCH_X:
        for s in (1, -1):
            c = [box(lx - LW / 2 - 0.3, lx + LW / 2 + 0.3, PY - HUB_R - 0.5, LY + 1, PZ - HUB_R - 0.5, ZT + 1)]
            cc = fuse(c)
            cuts.append(cc if s > 0 else mirror_y(cc))
    lid = lid.cut(fuse(cuts))
    stubs = []                                                 # latch pivot stubs on the slot walls
    for lx in LATCH_X:
        w0, w1 = lx - LW / 2 - 0.3, lx + LW / 2 + 0.3
        for sy in (1, -1):
            stubs += [cyl_x(STUB_D / 2, w0 - 0.5, w0 + STUB_L, sy * PY, PZ),
                      cyl_x(STUB_D / 2, w1 - STUB_L, w1 + 0.5, sy * PY, PZ)]
    return clean(lid.fuse(stubs))


def dovetail(clr):
    """Hanger dovetail profile (x, z), shrunk by clr (socket: 0, tenon: DT_CLR): narrow at the opening
    (bottom), wide at the ceiling -> carries the spool, both flanks lock."""
    n0, n1 = -DT_HALF0, DT_HALF0
    if clr:                                        # tenon: flanks = socket flanks raised DT_SEAT; straight neck below
        k = (DT_HALF1 - DT_HALF0) / (DT_Z1 - DT_Z0)
        xb, zt = DT_HALF0 - k * DT_SEAT, DT_Z1 - DT_TOP_GAP
        xt = DT_HALF0 + k * (zt - DT_Z0 - DT_SEAT)
        return [(-xb, DT_Z0 - 0.5), (xb, DT_Z0 - 0.5), (xb, DT_Z0), (xt, zt), (-xt, zt), (-xb, DT_Z0)]
    return [(n0, DT_Z0), (n1, DT_Z0), (DT_HALF1, DT_Z1), (-DT_HALF1, DT_Z1)]


def cradle_dovetail(clr):
    """Cradle dovetail profile (y, z) for the +Y side, shrunk by clr."""
    z0, z1 = CRADLE_Z1, CRADLE_Z1 + CD_H
    n0, n1, w0, w1 = CD_NARROW[0] + clr, CD_NARROW[1] - clr, CD_WIDE[0] + clr, CD_WIDE[1] - clr
    if clr:                                        # tenon: straight neck down into the cradle flange
        return [(n0, z0 - 1), (n1, z0 - 1), (n1, z0), (w1, z1 - clr), (w0, z1 - clr), (n0, z0)]
    return [(n0, z0), (n1, z0), (w1, z1), (w0, z1)]


def make_pocket_support():
    """Breakaway support for the outlet pocket floor - the lid prints top-down, so that floor is a 20 mm bridge
    6 mm above the bed. Grid of 0.8 mm ribs standing on the bed (= the lid top plane), 0.4 mm clear of the
    pocket walls and stopping one layer (0.2 mm) under the floor. Exported with Lid_R only; snap it out after
    printing."""
    zp = ZT - POCKET_D
    gap, t, pitch = 0.2, 0.8, 5.0
    inside = cyl_z(POCKET_R - 0.4, zp + gap, ZT, OUT_X, 0).fuse([
        cyl_z(POCKET_R - 0.4, zp + gap, ZT, PARK_X, 0),
        box(OUT_X, PARK_X, -POCKET_R + 0.4, POCKET_R - 0.4, zp + gap, ZT)])
    ribs = []
    x = OUT_X - POCKET_R
    while x <= PARK_X + POCKET_R:
        ribs.append(box(x - t / 2, x + t / 2, -POCKET_R, POCKET_R, zp + gap, ZT))
        x += pitch
    for y in (-pitch, 0.0, pitch):
        ribs.append(box(OUT_X - POCKET_R, PARK_X + POCKET_R, y - t / 2, y + t / 2, zp + gap, ZT))
    return clean(fuse(ribs).common(inside))


def split_lid(lid):
    big = 1000
    return ({"L": clean(lid.common(box(-big, -SEAM, -big, big, -big, big))),
             "R": clean(lid.common(box(SEAM, big, -big, big, -big, big)))},
            clean(lid.common(box(-SEAM, SEAM, -big, big, -big, big))))


# ---------------- Latch (built at +Y side, x centred on 0) ----------------
def make_latch(extra=LATCH_EXTRA, bump_h=BUMP_H, bump_base=BUMP_BASE):
    """extra: reach the lip this much lower (longer latch) - less squeeze on the gasket when closing.
    bump_h / bump_base: locking ridge height / base width (tip stays BUMP_TIP wide)."""
    lt, tab = LT - extra, TAB_BOT - extra
    pts = [(LIP_TIP, lt - 3), (LIP_TIP, lt), (ARM_I, lt),
           (ARM_I, PZ - HUB_R), (PY, PZ - HUB_R), (PY, PZ + HUB_R), (ARM_O, PZ + HUB_R),
           (ARM_O, lt - 1), (ARM_O + 3, tab), (ARM_I + 1, tab), (ARM_I, lt - 3)]
    b0, t0 = BUMP_Y - bump_base / 2, BUMP_Y - BUMP_TIP / 2
    bump = [(max(b0, LIP_TIP), lt - 0.01), (BUMP_Y + bump_base / 2, lt - 0.01),
            (BUMP_Y + BUMP_TIP / 2, lt + bump_h), (max(t0, LIP_TIP), lt + bump_h)]   # tapered ridge
    body = prism_x(pts, -LW / 2, LW / 2).fuse([cyl_x(HUB_R, -LW / 2, LW / 2, PY, PZ),
                                               prism_x(bump, -LW / 2, LW / 2)])
    hole = cyl_x(STUB_D / 2 + 0.2, -LW, LW, PY, PZ)
    c_open = box(-LW, LW, PY - C_OPEN / 2, PY + C_OPEN / 2, PZ - HUB_R - 1, PZ)   # snaps down onto the stubs
    return clean(body.cut(hole.fuse(c_open)))


# ---------------- Spool hanger ----------------
def bayonet_path():
    """Axle-centre path out of a hanger hook, (dx, dz) relative to the seated position: sideways, UP, sideways,
    DOWN, out. Hanging, gravity can't do the first 'up'; upside down, it can't do the 'down' -> it can't
    fall out either way up. The lift (HOOK_RISE) fits in the gap between the spool and the lid."""
    a, b, e = HOOK_STEP1, HOOK_STEP1 + HOOK_STEP2, HOOK_STEP1 + HOOK_STEP2 + HOOK_EXIT
    return [(0, 0), (-a, 0), (-a, HOOK_RISE), (-b, HOOK_RISE), (-b, 0), (-e, HOOK_EXIT_RISE)]


def make_hanger():
    """+Y side arm; the -Y arm is the same part flipped. Dovetail on top; at the bottom either a closed
    flat-bottomed hole for the pull-out axle (HANG_MODE "pin") or the bayonet track."""
    if HANG_MODE == "pin":
        pts = [(-18, DT_Z0 - 0.3), (18, DT_Z0 - 0.3), (12, -D_AXLE), (12, -D_AXLE - 12), (-12, -D_AXLE - 12),
               (-12, -D_AXLE)]
        arm = prism_y(pts, ARM_Y0, ARM_Y1).fuse(prism_y(dovetail(DT_CLR), DT_TENON_Y0, ARM_Y1))
        h = AXLE_HOLE / 2
        flat = -D_AXLE - (AXLE_R * math.sqrt(0.5) + 0.25)
        hole = cyl_y(h, 0, 100, 0, -D_AXLE).cut(box(-10, 10, -1, 101, -D_AXLE - 10, flat))
        hole = hole.fuse(Part.makeCone(h + 1.0, h, 1.0, V(0, ARM_Y0 - 0.01, -D_AXLE), V(0, 1, 0)).cut(
            box(-10, 10, -1, 101, -D_AXLE - 10, flat)))           # lead-in chamfer on the spool side
        return clean(arm.cut(hole))
    e = HOOK_STEP1 + HOOK_STEP2 + HOOK_EXIT
    pts = [(-18, DT_Z0 - 0.3), (18, DT_Z0 - 0.3), (12, -D_AXLE), (12, -D_AXLE - 12), (-e + 1, -D_AXLE - 12),
           (-e + 1, -D_AXLE + HOOK_RISE + 9), (-18, -D_AXLE + 40)]
    tenon = prism_y(dovetail(DT_CLR), DT_TENON_Y0, ARM_Y1)   # slides outward (+Y) to the closed end
    zt, rh = DT_Z1 - DT_TOP_GAP, DT_TOP_GAP + DT_SEAT + DT_RIB_GRIP
    rib_yz = [(DT_TENON_Y0, zt - 0.01), (ARM_Y1, zt - 0.01), (ARM_Y1, zt + 0.05), (ARM_Y1 - DT_RIB_RAMP, zt + rh),
              (DT_TENON_Y0, zt + rh)]
    for x in DT_RIB_X:
        tenon = tenon.fuse(Part.Face(Part.makePolygon([V(x - DT_RIB_W / 2, y, z) for y, z in rib_yz + rib_yz[:1]]))
                           .extrude(V(DT_RIB_W, 0, 0)))
    arm = prism_y(pts, ARM_Y0, ARM_Y1).fuse(tenon)
    h = AXLE_SLOT / 2
    # track centre-line level: its flat floor carries the axle's flat underside at the axle's nominal height
    zc = -D_AXLE - (AXLE_R * math.sqrt(0.5) + 0.05) + h
    path = [V(dx, 0, zc + dz) for dx, dz in bayonet_path()]
    cuts = []
    segs = list(zip(path[:-1], path[1:]))
    for i, (p0, p1) in enumerate(segs):                           # track = chain of 8.4 mm wide stadiums
        hw = h + (0.8 if i == len(segs) - 1 else 0.0)             # sloped exit: wider so the axle's flat corners clear
        t = (p1 - p0)
        t.normalize()
        nrm = V(-t.z, 0, t.x) * hw
        quad = [p0 + nrm, p1 + nrm, p1 - nrm, p0 - nrm]
        cuts.append(prism_y([(q.x, q.z) for q in quad], 0, 100))
        cuts.append(cyl_y(hw, 0, 100, p1.x, p1.z))
    cuts.append(cyl_y(h, 0, 100, path[0].x, path[0].z))
    track = fuse(cuts)
    # keep the floors flat (no round pockets) so the axle stays flat side down wherever it rests
    floor0 = zc - h
    a, b = HOOK_STEP1, HOOK_STEP1 + HOOK_STEP2
    for x0, x1 in ((-a - h, h), (-b - h, -b + h)):         # flat floors only where the axle rests (not the exit)
        track = track.fuse(box(x0, x1, -1, 101, floor0, zc))
    hook = arm.cut(track)
    # rebuild the solid tooth between the two drops (the flat-floor fill above must not remove it)
    tooth = box(-b + h, -a - h, ARM_Y0, ARM_Y1, floor0, zc + HOOK_RISE - h)
    hook = hook.fuse(tooth)
    return clean(hook)


def slide_hanger_plate():
    """Hanger outline + dovetail with the plain sideways slot (snug on the neck) and lead-in funnel."""
    D, w, m = D_AXLE, SNAP_W, SNAP_MOUTH_X
    pts = [(-18, DT_Z0 - 0.3), (18, DT_Z0 - 0.3), (12, -D), (12, -D - 12), (m, -D - 12), (m, -D + 16), (-18, -D + 40)]
    arm = prism_y(pts, ARM_Y0, ARM_Y1).fuse(prism_y(dovetail(DT_CLR), DT_TENON_Y0, ARM_Y1))
    cut = [prism_y([(m - 6, -D - w), (0, -D - w), (0, -D + w), (m - 6, -D + w)], 0, 100), cyl_y(w, 0, 100, 0, -D),
           prism_y([(m - 1, -D - 4.5), (m + 5, -D - w), (m + 5, -D + w), (m - 1, -D + 4.5)], 0, 100)]
    return arm.cut(fuse(cut))


def make_slide_hanger():
    """+Y hanger with the slide lock (test). Through guide slot for the slider's stem, a pocket on the inner face
    for its barbs, and two square catch holes (locked / open) for the tooth on the slider's tongue. Prints flat."""
    D, g0 = D_AXLE, D_AXLE - 5.8
    h = slide_hanger_plate()
    cut = [box(SL_XG - SL_GW / 2, SL_XG + SL_GW / 2, 0, 100, -g0, -g0 + 3.0 + SL_TRAVEL + 0.1),        # guide slot
           box(SL_XG - 3.2, SL_XG + 3.2, ARM_Y0 - 1, ARM_Y0 + 1.3, -g0 - 1.5, -g0 + 3.0 + SL_TRAVEL + 1.5)]   # barb pocket
    cut.append(box(-14.2, -11.6, 0, 100, -D + 11.8, -D + 15.6))                                           # catch hole (locked)
    return clean(h.cut(fuse(cut)))


def make_slider(R):
    """Slider for the +Y slide-lock hanger, in the LOCKED position. R = radius of the axle part its curved nose hugs
    (collar on this side, 8 mm shoulder on the other). Stem with split barbs snaps through the guide slot once.
    A spring tongue (U-slot) carries a tooth on its back: square top face -> it can't slide up until you lift the
    tongue's tip (2 mm flap above the slider); ramped bottom -> it drops in by itself when you slide it down.
    Solid stem through the guide slot; a lock plate (make_slider_lockplate) presses onto its square tip on the
    hanger's back and clamps it - with the crush ribs on the slider's back: no rattle. Prints outer face down."""
    D, g0, S0 = D_AXLE, D_AXLE - 5.8, ARM_Y1 + 0.2
    body = prism_y([(-16.5, -D - 6), (-3, -D - 6), (-3, -D + 17), (-16.5, -D + 17)], S0, S0 + SL_T)
    body = body.cut(cyl_y(R + 0.1, 0, 100, 0, -D))                       # curved nose
    cuts = [box(-15.2, -14.4, 0, 100, -D + 2, -D + 30), box(-11.4, -10.6, 0, 100, -D + 2, -D + 30),   # U-slot sides
            box(-14.4, -11.4, S0 - 1, S0 + SL_T - SL_TONGUE_T, -D + 2, -D + 30)]                       # tongue thinner
    for k in range(3):                                                   # thumb grooves (outer face = bed face)
        z = -D - 4 + k * 2.2
        cuts.append(box(-10, -4, S0 + SL_T - 0.5, S0 + SL_T + 1, z, z + 1.0))
    body = body.cut(fuse(cuts))
    flap = box(-14.4, -11.4, S0 + SL_T - SL_TONGUE_T, S0 + SL_T, -D + 17 - 0.01, -D + 19)          # lift tab
    tooth = prism_x([(S0 + SL_T - SL_TONGUE_T + 0.01, -D + 12.0), (ARM_Y1 - 0.8, -D + 13.5), (ARM_Y1 - 0.8, -D + 15.5),
                     (S0 + SL_T - SL_TONGUE_T + 0.01, -D + 15.5)], -14.0, -11.8)
    ribs = [box(x - 0.4, x + 0.4, S0 - SL_RIB, S0 + 0.01, -D - 4, -D + 15) for x in (-16.0, -3.6)]
    stem = box(SL_XG - 1.6, SL_XG + 1.6, ARM_Y0 + 1.3, S0 + 0.01, -g0 + 0.05, -g0 + 2.95)
    tip = box(SL_XG - 1.1, SL_XG + 1.1, ARM_Y0 + 0.25, ARM_Y0 + 1.31, -g0 + 0.4, -g0 + 2.6)   # 2.2 square: lock plate goes on
    stem = stem.fuse(tip)
    return clean(fuse([body, flap, tooth, stem] + ribs).cut(cyl_y(R + 0.1, 0, 100, 0, -D)))   # ribs follow the nose too


def make_slider_lockplate():
    """Lock plate for the slider's stem tip (assembly position, slider locked): presses on for good from the hanger's
    back and sits recessed in the barb pocket, clamping the slider to the hanger. Prints flat."""
    g0 = D_AXLE - 5.8
    zc = -g0 + 1.5
    p = box(SL_XG - 3.0, SL_XG + 3.0, ARM_Y0 + 0.3, ARM_Y0 + 1.3, zc - 2.5, zc + 2.5)
    return clean(p.cut(box(SL_XG - 1.03, SL_XG + 1.03, 0, 100, -g0 + 0.47, -g0 + 2.53)))   # 0.07 press per side


def spring_pin(z0, z1, up):
    """Guide pin along Z inside the coil: teardrop section pointing +Y (towards the print bed, so no overhang),
    45 deg point at the free end (z1 if up, else z0)."""
    yc, r = (ARM_Y0 + ARM_Y1) / 2, SP_PIN_R
    t, c = r * math.sqrt(2), r * math.sqrt(0.5)
    sec = Part.Face(Part.Wire(Part.makeCircle(r, V(SL_XG, yc, 0)))).fuse(Part.Face(Part.makePolygon(
        [V(SL_XG - c, yc + c, 0), V(SL_XG, yc + t, 0), V(SL_XG + c, yc + c, 0), V(SL_XG, yc, 0), V(SL_XG - c, yc + c, 0)])))
    pin = sec.extrude(V(0, 0, z1 - z0)).translated(V(0, 0, z0))
    if up:
        env = cyl_z(t + 1, z0 - 1, z1 - t, SL_XG, yc).fuse(Part.makeCone(t, 0, t, V(SL_XG, yc, z1 - t), V(0, 0, 1)))
    else:
        env = cyl_z(t + 1, z0 + t, z1 + 1, SL_XG, yc).fuse(Part.makeCone(t, 0, t, V(SL_XG, yc, z0 + t), V(0, 0, -1)))
    return pin.common(env)


def make_spring_hanger():
    """+Y hanger with the SPRING slide lock (test). Spring channel through the plate (spring 5.0 OD in a 4.75 plate:
    the slider covers it outside, a pocket + the lock plate inside), a guide pin hanging into the coil from the top
    of the channel, the stem rests on the channel bottom when locked. Prints flat."""
    D = D_AXLE
    zc0, zt = -D + SP_Z0, -D + SP_Z0 + 3.0 + SP_LOCKED
    w = SP_OD + 0.4
    pts = [(-18, DT_Z0 - 0.3), (18, DT_Z0 - 0.3), (12, -D), (12, -D - 12), (SNAP_MOUTH_X, -D - 12), (SNAP_MOUTH_X, -D + 16),
           (-18, -D + 40)]
    stiff = prism_y(pts, ARM_Y0 - HANGER_STIFF, ARM_Y0 + 0.01).common(box(-50, 50, 0, 100, -D + HANGER_STIFF_Z, 50))
    stiff = stiff.cut(prism_y(dovetail(0), DT_Y0 - 50, DT_OUT))          # keep the dovetail tenon zone as is
    h = slide_hanger_plate().fuse(stiff).cut(fuse([box(SL_XG - w / 2, SL_XG + w / 2, 0, 100, zc0, zt),
                                       box(SL_XG - 3.4, SL_XG + 3.4, ARM_Y0 - 1, ARM_Y0 + 1.3, zc0 - 1.0, zt + 1.0)]))
    return clean(h.fuse(spring_pin(zt - 2.0, zt + 0.01, False)))


def make_spring_slider():
    """Slider for the spring lock, LOCKED position (+Y side; the -Y one is its mirror - both stops are SP_STOP_R).
    45 deg ramp on the mouth side: the incoming stop pushes it up, the spring snaps it back down behind it.
    Its bottom edge sits 0.2 below the axle centre, so pulling the spool out sideways pushes on a vertical face:
    it can't lift the slider. Stem in the channel with a guide pin up into the coil; square tip for the lock plate."""
    D, S0 = D_AXLE, ARM_Y1 + 0.2
    zc0 = -D + SP_Z0
    zt = zc0 + 3.0 + SP_LOCKED
    nose = cyl_y(SP_STOP_R + 0.1, 0, 100, 0, -D)
    body = prism_y([(-13, -D + 3.9), (-8.9, -D - 0.2), (-3, -D - 0.2), (-3, zt + 1.0), (-13, zt + 1.0)], S0, S0 + SL_T)
    body = body.cut(nose)
    for k in range(3):                                                   # thumb grooves (outer face = bed face)
        z = zt - 4.0 + k * 1.6
        body = body.cut(box(-12, -4, S0 + SL_T - 0.5, S0 + SL_T + 1, z, z + 0.8))
    ribs = [box(x - 0.4, x + 0.4, S0 - SL_RIB, S0 + 0.01, -D + 4.2, zt) for x in (-12.4, -3.6)]   # clear of the ramp
    w = SP_OD + 0.4 - 0.2
    stem = box(SL_XG - w / 2, SL_XG + w / 2, ARM_Y0 + 1.3, S0 + 0.01, zc0 + 0.02, zc0 + 3.0)
    tip = box(SL_XG - 1.1, SL_XG + 1.1, ARM_Y0 + 0.25, ARM_Y0 + 1.31, zc0 + 0.4, zc0 + 2.6)
    pin = spring_pin(zc0 + 2.99, zc0 + 3.0 + 2.5, True)
    return clean(fuse([body, stem, tip, pin] + ribs).cut(nose))


def make_spring_lockplate():
    """Lock plate for the spring slider's stem tip: presses on from the back, sits recessed in the pocket."""
    zc = -D_AXLE + SP_Z0 + 1.5
    p = box(SL_XG - 3.2, SL_XG + 3.2, ARM_Y0 + 0.3, ARM_Y0 + 1.3, zc - 2.4, zc + 1.4)     # in the pocket, below the spring
    return clean(p.cut(box(SL_XG - 1.03, SL_XG + 1.03, 0, 100, zc - 1.03, zc + 1.03)))


def make_snap_hanger():
    """+Y hanger, snap-in version (test): straight sideways slot (mouth towards -X), snug on the axle neck, seat at
    the same spot as the bayonet seat. Two spring beams (relief slots behind them) carry lips that narrow the mouth:
    push the spool unit in sideways, the lips flex and click shut behind the neck. Hanging or upside down the
    weight sits on the solid slot faces next to the seat, never on the lips. Same dovetail; prints flat."""
    D, w, m = D_AXLE, SNAP_W, SNAP_MOUTH_X
    pts = [(-18, DT_Z0 - 0.3), (18, DT_Z0 - 0.3), (12, -D), (12, -D - 12), (m, -D - 12), (m, -D + 12), (-18, -D + 40)]
    arm = prism_y(pts, ARM_Y0, ARM_Y1).fuse(prism_y(dovetail(DT_CLR), DT_TENON_Y0, ARM_Y1))
    cut = [prism_y([(m - 6, -D - w), (0, -D - w), (0, -D + w), (m - 6, -D + w)], 0, 100), cyl_y(w, 0, 100, 0, -D),
           prism_y([(m - 1, -D - 4.5), (m + 5, -D - w), (m + 5, -D + w), (m - 1, -D + 4.5)], 0, 100)]    # lead-in funnel
    # spring beams 1.6 thick, rooted near the mouth (x = -18), free tips right beside the seated neck (x = -1.6),
    # 0.8 gap to the solid seat block (x > -0.8); relief slots 1.2 behind them
    for s in (1, -1):
        cut.append(prism_y([(-18, -D + s * (w + 1.6)), (-0.8, -D + s * (w + 1.6)), (-0.8, -D + s * (w + 2.8)),
                            (-18, -D + s * (w + 2.8))], 0, 100))
        cut.append(prism_y([(-1.6, -D + s * (w - 0.01)), (-0.8, -D + s * (w - 0.01)), (-0.8, -D + s * (w + 1.61)),
                            (-1.6, -D + s * (w + 1.61))], 0, 100))
    h = arm.cut(fuse(cut))
    lw = AXLE_NECK_R - SNAP_LIP                  # half mouth at the lips
    for s in (1, -1):                            # lips at the beam tips: long gentle ramp in, steeper ramp out (firm pull)
        h = h.fuse(prism_y([(-9.0, -D + s * w), (-3.2, -D + s * lw), (-2.4, -D + s * lw), (-1.6, -D + s * w)], ARM_Y0, ARM_Y1))
    return clean(h)


def make_hanger_fit_test(grip, marks):
    """Top 20 mm of the +Y hanger (dovetail with crush ribs at this grip) for testing the fit in the printed lid.
    'marks' notches on the bottom edge tell the variants apart."""
    global DT_RIB_GRIP
    g0, DT_RIB_GRIP = DT_RIB_GRIP, grip
    try:
        t = make_hanger().common(box(-30, 30, 0, 60, -13, 20))
    finally:
        DT_RIB_GRIP = g0
    for i in range(marks):
        t = t.cut(box(-9 + 4 * i, -7.4 + 4 * i, 0, 60, -14, -11))
    return clean(t)


def make_axle_pin():
    """Pull-out axle (print lying along X, flat side down): pointed tip at x = 0, head at the far end.
    Installed along Y, tip at AXLE_TIP_Y, head outside the +Y hanger. Same 45 deg flat as the plain axle."""
    r = AXLE_R
    L = (ARM_Y1 + 0.1) - AXLE_TIP_Y               # head sits 0.1 mm off the +Y arm's outer face
    a = fuse([cyl_x(r, 2.0, L, 0, 0), Part.makeCone(2.6, r, 2.0, V(0, 0, 0), V(1, 0, 0)),
              cyl_x(AXLE_HEAD_R, L - 0.01, L + AXLE_HEAD_T, 0, 0)])
    return clean(a.cut(box(-1, L + AXLE_HEAD_T + 1, -AXLE_HEAD_R - 1, AXLE_HEAD_R + 1, -AXLE_HEAD_R - 1, -r * math.sqrt(0.5))))


def make_axle(grip=False, stop_r=None):
    """8 mm axle printed lying along X: round top (the bearings bear on it), bottom cut flat where the
    round surface reaches 45 deg -> no overhang steeper than 45 deg, no supports, stays inside 8 mm.
    Local x = installed y - AXLE_Y0. A neck where it sits in each hanger: the hanger plate rides in the
    neck between the 8 mm body (inside) and a shoulder (outside), so the axle can't slide in or out along
    its length - no clip. The -Y shoulder is 8 mm so the bearings slide on from that end; +Y is a collar."""
    r = AXLE_R
    lx = lambda y: y - AXLE_Y0
    n0, n1 = ARM_Y0 - AXLE_PLAY, ARM_Y1 + AXLE_PLAY               # neck span (installed |y|)
    cr = AXLE_COLLAR_R if stop_r is None else stop_r
    a = fuse([Part.makeCone(r - 0.6, r, 0.6, V(0, 0, 0), V(1, 0, 0)), cyl_x(r, 0.6, lx(n1) + 0.01, 0, 0),
              cyl_x(cr, lx(n1), lx(n1 + AXLE_COLLAR_T), 0, 0)])
    if stop_r is not None:                       # both ends stepped down to the same small stop radius
        a = a.cut(cyl_x(r + 1, -1, lx(-n1), 0, 0).cut(cyl_x(stop_r, -2, lx(-n1) + 1, 0, 0)))
        a = a.cut(cyl_x(r + 1, lx(n1), lx(n1 + AXLE_COLLAR_T) + 1, 0, 0).cut(cyl_x(stop_r, lx(n1) - 1, lx(n1 + AXLE_COLLAR_T) + 2, 0, 0)))
    for y0, y1 in ((-n1, -n0), (n0, n1)):
        a = a.cut(cyl_x(AXLE_COLLAR_R + 1, lx(y0), lx(y1), 0, 0).cut(cyl_x(AXLE_NECK_R, lx(y0) - 1, lx(y1) + 1, 0, 0)))
    if grip:                                     # ribs on the round part only (0..180 deg), 1.7 mm lead-in ramp
        xa, xb = lx(AXLE_GRIP_Y[0]) + 0.5, lx(AXLE_GRIP_Y[1]) - 0.2
        env = Part.makeCone(r, r + AXLE_GRIP, 1.7, V(xa - 1.7, 0, 0), V(1, 0, 0)).fuse(cyl_x(r + 1, xa, xb, 0, 0))
        for ang in (0, 45, 90, 135, 180):
            rib = Part.Face(Part.makePolygon([V(0, r - 0.3, -0.45), V(0, r + AXLE_GRIP, -0.12), V(0, r + AXLE_GRIP, 0.12),
                                              V(0, r - 0.3, 0.45), V(0, r - 0.3, -0.45)])).extrude(V(xb - xa + 1.7, 0, 0))
            rib.translate(V(xa - 1.7, 0, 0))
            rib.rotate(V(0, 0, 0), V(1, 0, 0), ang)
            a = a.fuse(rib.common(env))
    big = max(cr, r) + 1
    return clean(a.cut(box(-1, lx(n1 + AXLE_COLLAR_T) + 1, -big, big, -big, -r * math.sqrt(0.5))))


def make_hub_adapter():
    """Along +Z: 2 mm flange (OD 66) then a straight spigot (12 mm) that goes fully into the spool's hub hole, so
    the flange sits flat on the spool face. Crush ribs on the spigot centre it; chamfered tip for the lead-in.
    608 bearing pressed in from the spigot tip."""
    r, L = HUB_SPIGOT_D / 2, 12.0
    a = Part.makeCylinder(33, 2).fuse([Part.makeCylinder(r, L - 2 + 0.01, V(0, 0, 2)),
                                       Part.makeCone(r, r - 2, 2, V(0, 0, L))])
    rr = r + HUB_RIB_PROUD
    for i in range(HUB_RIBS):                             # ribs: full height up to z 9, ramp down to the spigot by z 12
        ang = i * 2 * math.pi / HUB_RIBS
        rib = prism_y([(r - 0.5, 1.9), (rr, 1.9), (rr, 9.0), (r - 0.5, L)], -0.75, 0.75)
        rib.rotate(V(0, 0, 0), V(0, 0, 1), math.degrees(ang))
        a = a.fuse(rib)
    cuts = [Part.makeCylinder(6, 20, V(0, 0, -1)),
            Part.makeCylinder(BEARING_D / 2, BEARING_W + 0.01, V(0, 0, 14 - BEARING_W))]
    for i in range(6):                                    # lightening pockets
        ang = i * math.pi / 3
        cuts.append(Part.makeCylinder(4.5, 20, V(18 * math.cos(ang), 18 * math.sin(ang), -1)))
    return clean(a.cut(fuse(cuts)))


# ---------------- Hygrometer cradle ----------------
def cradle_top(bx0, y0, y1):
    """Common top of a cradle: plate under the lid with the two dovetails, 45 deg wedge behind the back."""
    parts = [box(85, HY_FACE_X, y0, y1, HY_TOP, CRADLE_Z1)]
    for sy in (1, -1):                                  # dovetails slide forward into the lid sockets
        t = prism_x(cradle_dovetail(CD_CLR), 85, CD_X1 - CD_CLR)
        parts.append(t if sy > 0 else mirror_y(t))
    parts.append(prism_y([(bx0, HY_TOP), (85, HY_TOP), (bx0, HY_TOP - (bx0 - 85))], y0, y1))
    return parts


def make_hy_cradle():
    """50 x 50 x 10 hygrometer: drops in from the top before the cradle is slid on; front lips."""
    bx0 = HY_FACE_X - 1.2 - HY_D - 0.4 - 2
    hw = HY_W / 2 + 0.2
    zb = HY_TOP - HY_H - 1 - 2
    parts = [box(bx0, bx0 + 2, -hw - 2, hw + 2, zb, CRADLE_Z1),                         # back
             box(bx0, HY_FACE_X, -hw - 2, -hw, zb, CRADLE_Z1),                          # sides
             box(bx0, HY_FACE_X, hw, hw + 2, zb, CRADLE_Z1),
             box(bx0, HY_FACE_X, -hw - 2, hw + 2, zb, zb + 2),                        # bottom
             box(HY_FACE_X - 1.2, HY_FACE_X, -hw, -hw + 3, zb, CRADLE_Z1),              # front lips
             box(HY_FACE_X - 1.2, HY_FACE_X, hw - 3, hw, zb, CRADLE_Z1),
             box(HY_FACE_X - 1.2, HY_FACE_X, -hw, hw, zb, zb + 5)]
    top = cradle_top(bx0, -hw - 2, hw + 2)
    top[0] = box(85, bx0 + 2, -hw - 2, hw + 2, HY_TOP, CRADLE_Z1)                   # open top in front of the back
    c = fuse(parts + top)
    return clean(c.cut(box(bx0 - 1, bx0 + 3, -12, 12, zb + 8, HY_TOP - 8)))         # air window


def make_mini_cradle():
    """Mini digital hygrometer (body 44.5 x 25.5 x 13 + 47.5 x 28 x 2 face): open-front pocket, push the body
    straight in from the front until the face rests on the cradle front -> face 107..109, ~1 mm off the box wall
    (0.4 at its ends where the wall curves in). Crush ribs on the short side walls grip the body.
    Prints on its BACK (x = 85 face on the bed, open front up): every wall, the dovetails and the ribs stand
    vertical -> no bridges, no overhangs, no supports. The back plate sits flush with the dovetails' rear ends;
    two standoff ribs set the hygrometer's depth."""
    bx0 = 85.0                                   # back plate, flush with the tenons' rear ends
    hb = HY_FACE_X - MH_D - 0.3                  # hygrometer back stop (pocket 0.3 deeper than the hygrometer)
    hw, hh = MH_L / 2 + 0.25, MH_W + 0.5         # pocket half width / height (0.25 clearance per side)
    zt = HY_TOP - MH_DROP                        # pocket top (lowered below the rim band)
    zb = zt - hh - 2                             # bottom of the floor
    parts = [box(bx0, bx0 + 2, -hw - 2, hw + 2, zb, CRADLE_Z1),                         # back
             box(bx0, HY_FACE_X, -hw - 2, -hw, zb, CRADLE_Z1),                          # sides
             box(bx0, HY_FACE_X, hw, hw + 2, zb, CRADLE_Z1),
             box(bx0, HY_FACE_X, -hw - 2, hw + 2, zb, zb + 2),                        # floor
             box(bx0, HY_FACE_X, -hw - 2, hw + 2, zt, CRADLE_Z1)]                     # solid top: ceiling + plate
    for y in (-18.0, 18.0):                      # back-stop ribs
        parts.append(box(bx0 + 1, hb, y - 0.8, y + 0.8, zb + 1, zt + 1))
    for sy in (1, -1):                           # crush ribs: 0.45 mm proud -> 0.2 mm grip per side
        for z in (zb + 2 + hh * 0.3, zb + 2 + hh * 0.7):
            r = prism_x([(sy * hw, z - 1.0), (sy * (hw - 0.45), z), (sy * hw, z + 1.0)], bx0 + 1, HY_FACE_X - 1)
            parts.append(r)
    for sy in (1, -1):                           # dovetails slide forward into the lid sockets
        t = prism_x(cradle_dovetail(CD_CLR), bx0, CD_X1 - CD_CLR)
        parts.append(t if sy > 0 else mirror_y(t))
    c = fuse(parts)
    cuts = [box(bx0 - 1, bx0 + 3, -14, 14, zb + 6, zt - 5)]                              # air window (back)
    for sy in (1, -1):
        ya, yb = sorted((sy * (hw - 8), sy * (hw - 2)))
        cuts.append(box(hb + 2, HY_FACE_X + 1, ya, yb, zb - 1, zb + 2.1))      # floor vents (open at the front: no bridge)
    return clean(c.cut(fuse(cuts)))


def make_hygro_shim():
    """Glue-in sleeve for an ALREADY PRINTED cradle (its pocket was 48.5 x 29.1 x 15.5 deep for a 48 x 28.6 x 15.2
    unit): slide it in to the bottom of that pocket, front flush with the cradle front, and glue it. Inside it
    is the new body pocket (44.9 x 25.9 x 13.3, crush ribs on the short sides); the face rests on its front.
    Clears the old pocket's crush ribs (0.45) by 0.1. Windows in the back and floor keep the old vents open.
    Prints on its back (back wall on the bed)."""
    ohw, ohh, x0, x1 = 48.5 / 2, 29.1, 107.0 - 15.5, 107.0     # old pocket
    ozt = HY_TOP - MH_DROP                                      # old pocket top
    sw, st, sb = ohw - 0.45 - 0.1, ozt - 0.15, ozt - ohh + 0.15  # sleeve outer half width / top / bottom
    hw, hh = MH_L / 2 + 0.25, MH_W + 0.5
    it = st - (st - sb - hh) / 2                                 # inner pocket centred in the sleeve
    ib = it - hh
    s = box(x0, x1, -sw, sw, sb, st).cut(box(x1 - MH_D - 0.3, x1 + 1, -hw, hw, ib, it))
    ribs = []
    for sy in (1, -1):                                          # crush ribs: 0.45 proud -> 0.2 mm grip per side
        for z in (ib + hh * 0.3, ib + hh * 0.7):
            ribs.append(prism_x([(sy * hw, z - 1.0), (sy * (hw - 0.45), z), (sy * hw, z + 1.0)],
                                x1 - MH_D - 0.3 - 0.01, x1 - 1))
    cuts = [box(x0 - 1, x1 - MH_D, -12, 12, ib + 4, it - 4)]           # back window
    for sy in (1, -1):
        ya, yb = sorted((sy * (hw - 8), sy * (hw - 2)))
        cuts.append(box(x0 + 4, x1 + 1, ya, yb, sb - 1, ib + 0.01))     # floor vents, open at the front
    return clean(s.fuse(ribs).cut(fuse(cuts)))


# ---------------- TPU parts ----------------
def make_gasket():
    m = (G_GROOVE_W - G_W_STRIP) / 2
    g = ring(GIX + m, GIY + m, GIR + m, GOX - m, GOY - m, GOR - m, 0, G_T)
    big = 1000
    return {"L": clean(g.common(box(-big, 0, -big, big, -1, 10))),
            "R": clean(g.common(box(0, big, -big, big, -1, 10)))}


def revolve_rz(pts, x=0.0):
    """Solid of revolution about the vertical axis at (x, 0) from an (r, z) outline (closed automatically)."""
    w = Part.makePolygon([V(x + r, 0, z) for r, z in pts] + [V(x + pts[0][0], 0, pts[0][1])])
    return Part.Face(w).revolve(V(x, 0, 0), V(0, 0, 1), 360)


def make_grommet():
    """TPU grommet, print as is (flange on the bed). Body presses into the 10 mm bore in the lid-top pocket:
    3 mm tapered tip and two RAMPED grip rings (sloped on the leading side, square behind) so it pushes in
    easily and still holds. The PTFE tube - or the cap peg - enters through a long funnel and two angled
    sealing lips."""
    rb, rr = GROM_BORE / 2 + GROM_PRESS, GROM_BORE / 2 + GROM_RIB
    top = GROM_L + 1.5
    g = revolve_rz([(0, 0), (GROM_FL_R, 0), (GROM_FL_R, 1.5), (rb, 1.5),
                    (rb, 4.0), (rr, 4.0), (rb, 6.0),                      # grip ring 1 (ramp towards the tip)
                    (rb, 7.5), (rr, 7.5), (rb, 9.5),                      # grip ring 2
                    (rb, top - 3.0), (GROM_BORE / 2 - 0.6, top), (0, top)])  # 3 mm lead-in taper
    g = g.cut(fuse([Part.makeCylinder(GROM_CLEAR / 2, GROM_L + 10, V(0, 0, -1)),
                    Part.makeCone(3.6, GROM_CLEAR / 2, 3.5, V(0, 0, -0.01))]))   # 3.5 mm lead-in funnel
    # two sealing lips, angled in the push-in direction: the tube slides in easily and
    # each lip wipes tight around it (3.4 mm lip bore on a 4.0 mm PTFE tube)
    for z in (4.5, 9.5):
        ro, ri = GROM_CLEAR / 2 + 0.1, GROM_LIP / 2
        prof = Part.makePolygon([V(ri, 0, z + 0.9), V(ro, 0, z), V(ro, 0, z + 0.7), V(ri, 0, z + 1.5), V(ri, 0, z + 0.9)])
        g = g.fuse(Part.Face(prof).revolve(V(0, 0, 0), V(0, 0, 1), 360))
    return clean(g)


def make_cap_tether():
    """TPU cap on a strap, anchored in the small hole at the far end of the lid pocket. Print as is
    (discs on the bed, both pegs up). Installed, both pegs point down: the anchor peg is pressed in for good,
    the cap peg plugs the grommet (seals in its lips like a tube). Open, the cap just lies anywhere on its
    slack strap - no twisting. The filament can stay threaded through the hole in the cap.
    Long lead-ins everywhere: 3 mm taper on the cap peg, 3.5 mm pointed anchor tip with a ramped barb, and a
    funnel at both ends of the filament hole."""
    rp, tip = CAP_PEG_D / 2, 1.8 + 8 + 3.0
    cap = revolve_rz([(0, 0), (7, 0), (7, 1.8), (rp, 1.8), (rp, 9.8), (1.6, tip), (0, tip)])
    rf = FIL_HOLE / 2
    cap = cap.cut(fuse([Part.makeCylinder(rf, tip + 2, V(0, 0, -1)),
                        Part.makeCone(rf, 1.3, 2.5, V(0, 0, tip - 2.5 + 0.01)),        # funnel at the peg tip
                        Part.makeCone(1.5, rf, 1.2, V(0, 0, -0.01))]))                  # funnel on the outside face
    ax, ra = TETHER_L, ANCHOR_D / 2
    anchor = revolve_rz([(0, 0), (4.5, 0), (4.5, 1.2), (ra, 1.2), (ra, 5.5), (ra + 0.15, 5.5),
                         (1.3, ANCHOR_HOLE_L), (0, ANCHOR_HOLE_L)], ax)                 # ramped barb + 3.5 mm tip
    strap = box(6.5, ax - 4.0, -1.75, 1.75, 0, 1.0)
    return clean(fuse([cap, strap, anchor]))


def grommet_matrix():
    """Grommet flange on the pocket floor, body pointing down into the lid."""
    m = rot("X", 180)
    m.move(V(OUT_X, 0, ZT - POCKET_D + 1.5))
    return m

# ---------------- Silica box (closed) ----------------
SBOX_TOP = PLATE_Z0 - SBOX_CLR            # top of the box walls and of the sliding cover
SLIDE_G1 = SBOX_TOP - SLIDE_LIP           # groove roof
SLIDE_GF = SLIDE_G1 - SLIDE_GROOVE_H      # groove floor
SLIDE_CT = SLIDE_G1 - SLIDE_VCLR          # cover top face (tongues flush with it -> prints flat, top face down)
SLIDE_G0 = SLIDE_CT - SLIDE_T             # cover underside = top of the lowered inner end wall


def slide_groove(sy, x0, x1, extra=0.0):
    """Cover groove in a long wall: flat floor, roof sloping down 45 deg into the wall -> prints clean (a flat
    roof sagged and pinched the tongue). 'extra' raises the roof (lead-in head room)."""
    wi, D, g1 = BAND_IN - SBOX_CLR - SBOX_W, SLIDE_GROOVE_D, SLIDE_G1 + extra
    pts = [(wi - 0.01, SLIDE_GF), (wi + D, SLIDE_GF), (wi + D, g1 - D), (wi, g1), (wi - 0.01, g1)]
    g = prism_x(pts, x0, x1)
    return g if sy > 0 else mirror_y(g)


def sbox_outline(x0, x1, o, z0, z1, clr=None):
    """Lid cavity shape (less the clearance), limited to x0..x1, grown by o."""
    clr = SBOX_CLR if clr is None else clr
    r = R_BOX_IN - 4 - clr
    big = 1000
    return rrect(BAND_IN_X - clr + o, BAND_IN - clr + o, z0, z1, max(r + o, 0.5)).common(
        box(x0 - o, x1 + o, -big, big, -big, big))


def sbox_straight_x():
    """|x| up to which the lid cavity's long walls are straight (the outer ends are rounded)."""
    return BAND_IN_X - SBOX_CLR - (R_BOX_IN - 4 - SBOX_CLR)


def crush_rib(cx, sy, hy):
    """Vertical triangular rib on a long wall's outer face, SBOX_CRUSH proud, z 10..22 (clear of the lid grooves)."""
    pts = [V(cx - 0.75, sy * (hy - 0.1), 0), V(cx + 0.75, sy * (hy - 0.1), 0), V(cx, sy * (hy + SBOX_CRUSH), 0)]
    f = Part.Face(Part.makePolygon(pts + [pts[0]]))
    return f.extrude(V(0, 0, 12)).translated(V(0, 0, 10))


def make_sbox_body(x0, x1, snaps):
    """Silica box: slotted floor + slotted inner end wall, 2.4 mm walls, divider rib in the long one.
    Springy tabs on the long sides click into the lid grooves; pull tab at the inner end.
    Top: grooves for the sliding cover along the straight part of both long walls, open at the inner end
    (that end wall is lowered to the cover's underside, with a detent notch); in the rounded outer end of
    the long box a ledge carries the cover instead."""
    W, F, big = SBOX_W, SBOX_FLOOR, 1000
    hy = BAND_IN - SBOX_CLR
    wi = hy - W                                     # inner face of the long walls
    inner_end = x1 if x0 < 0 else x0                # end towards the seam
    sgn = 1 if x0 < 0 else -1                       # +1: inner end is the +X end
    body = sbox_outline(x0, x1, 0, SBOX_Z0, SBOX_TOP).cut(sbox_outline(x0, x1, -W, SBOX_Z0 + F, SBOX_TOP + 1))
    xs = sbox_straight_x()
    xa, xb = max(min(x0, x1), -xs), min(max(x0, x1), xs)
    if min(x0, x1) < -xs:                           # ledge round the rounded outer end
        ledge = sbox_outline(x0, x1, -W + 0.01, SLIDE_G0 - 1.5, SLIDE_G0).cut(
            sbox_outline(x0, x1, -W - SLIDE_GROOVE_D, SLIDE_G0 - 2, SLIDE_G0 + 1))
        body = body.fuse(ledge.common(box(-big, xa + 0.01, -big, big, -big, big)))
    zone = sbox_outline(x0, x1, -W - 2, SBOX_Z0 - 1, SBOX_Z0 + F + 1)
    slots, x = [], x0 + W + 3
    while x < x1 - W - 3:
        slots.append(box(x, x + BEAD_SLOT, -big, big, SBOX_Z0 - 1, SBOX_Z0 + F + 1))
        x += 4.5
    slots = fuse(slots).common(zone)
    if x0 < 0:                                      # long box: solid pads + snap holes for the end handle
        hx, hy_h = HANDLE_HOLE
        for sy in (1, -1):
            slots = slots.cut(box(HANDLE_X - 3.8, HANDLE_X + 3.8, sy * HANDLE_Y - 3.5, sy * HANDLE_Y + 3.5, -big, big))
            slots = slots.fuse(box(HANDLE_X - hx / 2, HANDLE_X + hx / 2, sy * HANDLE_Y - hy_h / 2, sy * HANDLE_Y + hy_h / 2,
                                   SBOX_Z0 - 1, SBOX_Z0 + F + 1))
    cuts = [slots]
    y = -hy + 6
    while y < hy - 6:                               # vent slots in the inner end wall
        cuts.append(box(inner_end - 3, inner_end + 3, y, y + BEAD_SLOT, SBOX_Z0 + F + 3, SLIDE_G0 - 4))
        y += 5
    ew0, ew1 = sorted((inner_end, inner_end - sgn * W))
    for sy in (1, -1):                              # cover grooves (+ extra 0.6 head room near the inner end)
        cuts.append(slide_groove(sy, xa - (1 if sgn < 0 else 0), xb + (1 if sgn > 0 else 0)))
        ra, rb = sorted((inner_end, inner_end - sgn * 10))
        cuts.append(slide_groove(sy, ra - 1, rb + 1, 0.6))
    cuts.append(box(ew0 - 0.01, ew1 + 0.01, -wi - SLIDE_GROOVE_D, wi + SLIDE_GROOVE_D, SLIDE_G0, SBOX_TOP + 1))  # lower end wall
    ec = (ew0 + ew1) / 2
    cuts.append(cyl_y(0.7, -wi, wi, ec, SLIDE_G0))                                     # detent notch
    cuts.append(prism_y([(inner_end, SLIDE_G0 + 0.01), (inner_end, SLIDE_G0 - 0.8),
                         (inner_end - sgn * 0.8, SLIDE_G0 + 0.01)], -wi, wi))            # chamfered top edge
    bumps = []
    zt0, zt1 = SBOX_Z0 + F + 0.5, 17.0             # spring tab: free bottom end, hangs from z 17
    for sx in [x for x in snaps if x not in LOCK_X]:   # lid snaps: spring tab in the OUTER skin of a double wall
        for sy in (1, -1):
            boss = sorted((sy * (wi - SBOX_SNAP_BOSS), sy * (wi + 0.01)))
            body = body.fuse(box(sx - 8.5, sx + 8.5, *boss, SBOX_Z0, zt1 + 1.5))      # inner wall bulges in locally
            gap = sorted((sy * (hy - SBOX_TAB_T - SBOX_TAB_GAP), sy * (hy - SBOX_TAB_T)))
            skin = sorted((sy * (hy - SBOX_TAB_T - 0.01), sy * (hy + 1)))
            cuts += [box(sx - 7, sx + 7, *gap, zt0, zt1),                                # air gap behind the tab
                     box(sx - 7, sx - 6, *skin, zt0, zt1),                               # side slits (outer skin only)
                     box(sx + 6, sx + 7, *skin, zt0, zt1),
                     box(sx - 7, sx + 7, *skin, zt0, zt0 + 1.0)]                         # bottom slit
            bumps.append(prism_x([(sy * (hy - 0.1), BOX_SNAP_Z - 1.8), (sy * (hy + SBOX_BUMP), BOX_SNAP_Z),
                                  (sy * (hy - 0.1), BOX_SNAP_Z + 1.8)], sx - 5.5, sx + 5.5))   # fits the 3 mm groove
    for sx in [x for x in snaps if x in LOCK_X]:   # slide-bolt locks: closed tunnel + floor slot for the switch
        for sy in (1, -1):
            yt = hy + LOCK_REACH                    # bolt tip when locked
            yin = yt - LOCK_LEN - LOCK_TRAVEL       # bolt inner end when unlocked
            hw, c = LOCK_W / 2, LOCK_CLR
            blk = sorted((sy * (yin - 1.5), sy * (wi + 0.01)))
            body = body.fuse(box(sx - hw - 1.4, sx + hw + 1.4, *blk, SBOX_Z0, LOCK_Z1 + c + 1.2))
            ch = sorted((sy * (yin - 0.3), sy * (hy + 1)))
            ps = sorted((sy * (yin - 0.2), sy * (hy + 1)))
            cuts += [box(sx - hw - c, sx + hw + c, *ch, LOCK_Z0 - c, LOCK_Z1 + c),             # bolt tunnel + wall slot
                     box(sx - 3 - c, sx + 3 + c, *ps, SBOX_Z0 - 1, LOCK_Z0 - c + 0.01)]         # switch slot (open to the wall for assembly)
            for yb in (yt - LOCK_LEN / 2, yt - LOCK_LEN / 2 - LOCK_TRAVEL):               # detent dimples (locked / unlocked)
                cuts.append(cyl_x(0.45, sx - 2, sx + 2, sy * yb, LOCK_Z1 + c))
    for cx in [c for c in SBOX_CRUSH_X if min(x0, x1) + 4 < c < max(x0, x1) - 4]:
        for sy in (1, -1):                          # crush ribs: light press against the lid's inner walls
            bumps.append(crush_rib(cx, sy, hy))
    body = body.cut(fuse(cuts)).fuse(bumps)
    # smooth, then snug: a ramped pad on each groove floor under the tongue's front end in the closed position
    lead = (max(min(x0, x1), -xs) + 0.5) if sgn > 0 else (max(x0, x1) - W - 0.5)
    pa, pb = lead - sgn * 1.0, lead + sgn * 4.0
    ramp = [(pa, SLIDE_GF - 0.01), (lead + sgn * 6.0, SLIDE_GF - 0.01), (pb, SLIDE_GF + SLIDE_SNUG), (pa, SLIDE_GF + SLIDE_SNUG)]
    for sy in (1, -1):
        pad = prism_y(ramp, *sorted((sy * (wi - 0.01), sy * (wi + SLIDE_GROOVE_D))))
        body = body.fuse(pad)
    tx0, tx1 = (11, x0 + 0.5) if x0 > 0 else (x1 - 0.5, -11)   # pull tab at the inner end (seam side)
    tab = box(tx0, tx1, -10, 10, SBOX_Z0, SBOX_Z0 + F)
    tab = tab.cut(box(min(tx0, tx1) + 3, min(tx0, tx1) + 8, -5, 5, SBOX_Z0 - 1, SBOX_Z0 + 3))   # finger hole
    return clean(body.fuse(tab))


def make_silica_puller():
    """Tweezer puller for the silica boxes: clips into ONE floor slot in the middle of a box, so the pull is
    central and the box comes out straight (the end tab tilts it and it jams on the far wall).
    Local frame: x along the slot, z out of the floor (floor = z -2..0), y = thickness (printed flat, y on
    the bed). The legs are 1.0 thick to pass the 1.2 slot; the feet have a ramped underside, so pushing in
    squeezes the arms and they spring out under the floor past the slot ends. Square tops on the feet hold
    under the pull. To take it off, squeeze the arms. Finger loop on top."""
    se = BAND_IN - SBOX_CLR - SBOX_W - 2            # slot end |x| (local) = 37.3
    lo, li = se - 0.3, se - 2.8                     # leg outer / inner face
    tip = se + 1.3                                  # foot tip (1.3 under the floor, wall at se + 2)
    half = [(li, 3.5), (li, -4.6), (lo - 1.0, -4.6), (tip, -2.9), (tip, -2.1), (lo, -2.1), (lo, 3.5)]
    legs = [prism_y(half, 0, 1.0), prism_y([(-x, z) for x, z in half], 0, 1.0)]
    ring = [(lo, 1.0), (lo, 10), (12, 48), (12, 68), (-12, 68), (-12, 48), (-lo, 10), (-lo, 1.0),
            (-li, 1.0), (-li, 9.5), (-9, 44), (9, 44), (li, 9.5), (li, 1.0)]
    body = prism_y(ring, 0, 4.0).cut(cyl_y(8, -1, 5, 0, 56))       # finger hole
    return clean(fuse([body] + legs))


def make_sbox_handle():
    """D-handle for the rounded end of the long box: clicks into the two floor holes for good (split prongs with
    barbs catch on the floor's inside face). Local frame: y across the box, z = 0 at the floor's outer face,
    +z into the box; HANDLE_T thick along x. Prints flat (profile on the bed)."""
    F = SBOX_FLOOR
    pts_bar = [(-16, -10), (16, -10), (16, -7), (-16, -7)]
    parts = [prism_x(pts_bar, -HANDLE_T / 2, HANDLE_T / 2)]
    for sy in (1, -1):
        yc = sy * HANDLE_Y
        parts.append(prism_x([(yc - 2.5, -7.01), (yc + 2.5, -7.01), (yc + 1.55, -4), (yc - 1.55, -4)], -HANDLE_T / 2, HANDLE_T / 2))
        for side in (1, -1):                        # two prongs, 1.0 gap (squeeze room), 0.5 barbs outward
            yo, yi = yc + side * 1.55, yc + side * 0.5
            prong = [(yi, -4.01), (yo, -4.01), (yo, F + 0.1), (yo + side * 0.5, F + 0.1), (yo, F + 1.9), (yi, F + 1.9)]
            parts.append(prism_x(prong, -HANDLE_T / 2, HANDLE_T / 2))
    return clean(fuse(parts))


def make_sbox_handle2():
    """D-handle v2 for the long box's two floor holes (same holes as v1). Solid legs; below the floor they are wider
    than the holes -> a ledge sits flat on the floor's underside (can't push in, can't wobble). The leg tips poke
    into the box with a square cross-hole each: a lock bar (make_handle_lockbar) slides through both from inside
    and lies on the floor -> it can't pull out. Same local frame as v1. Prints flat (profile on the bed)."""
    t = HANDLE_HOLE[0] - 0.2                             # 0.1 clearance per side in the hole (x)
    tip = HBAR_Z + HBAR_HOLE / 2 + 1.2
    parts = [prism_x([(-16, -10), (16, -10), (16, -7), (-16, -7)], -t / 2, t / 2)]
    for sy in (1, -1):
        yc = sy * HANDLE_Y
        parts.append(prism_x([(yc - 3.5, -7.01), (yc + 3.5, -7.01), (yc + 2.5, -3), (yc + 2.5, 0), (yc - 2.5, 0),
                              (yc - 2.5, -3)], -t / 2, t / 2))                                   # leg + ledge (5 wide)
        parts.append(prism_x([(yc - 1.5, -0.01), (yc + 1.5, -0.01), (yc + 1.5, tip - 0.8), (yc + 0.7, tip),
                              (yc - 0.7, tip), (yc - 1.5, tip - 0.8)], -t / 2, t / 2))           # through the hole
    h = fuse(parts)
    hb = HBAR_HOLE / 2
    return clean(h.cut(box(-hb, hb, -50, 50, HBAR_Z - hb, HBAR_Z + hb)))                       # bar holes (along y)


def make_handle_lockbar():
    """Lock bar for handle v2 (assembly position: along Y through both leg tips). Head on the +Y end; a small ramped
    bump near the -Y end clicks through the -Y leg so the bar can't slide back. Insert it -Y end first, from
    inside the box (cover off). Prints flat."""
    hb, L = HBAR / 2, HANDLE_Y + 4.0
    b = box(-hb, hb, -L, L, HBAR_Z - hb, HBAR_Z + hb)
    head = box(-1.8, 1.8, L - 0.01, L + 1.5, HBAR_Z - hb, HBAR_Z - hb + 3.6)
    yb = -(HANDLE_Y + 1.5) - 0.3                         # just past the -Y leg's outer face
    bump = prism_x([(yb - 2.0, HBAR_Z + hb - 0.01), (yb, HBAR_Z + hb + 0.5), (yb, HBAR_Z + hb - 0.01)], -0.6, 0.6)
    return clean(fuse([b, head, bump]))


def make_lock_bolt(sx, sy, locked=True):
    """Slide bolt (assembly position, +Y side if sy > 0): bar in the tunnel + switch post down through the floor,
    detent bump on top. Slide the switch outwards to lock."""
    hy = BAND_IN - SBOX_CLR
    yt = hy + LOCK_REACH - (0 if locked else LOCK_TRAVEL)
    hw = LOCK_W / 2
    bar = box(sx - hw, sx + hw, yt - LOCK_LEN, yt, LOCK_Z0, LOCK_Z1)
    post = box(sx - 3, sx + 3, yt - LOCK_LEN, yt - LOCK_LEN + 3, SBOX_Z0 - 2.0, LOCK_Z0 + 0.01)
    bump = cyl_x(0.35, sx - 1.5, sx + 1.5, yt - LOCK_LEN / 2, LOCK_Z1).common(
        box(sx - 2, sx + 2, yt - LOCK_LEN, yt, LOCK_Z1 - 0.01, LOCK_Z1 + 1))
    b = clean(fuse([bar, post, bump]))
    return b if sy > 0 else mirror_y(b)


def make_sbox_cover(x0, x1):
    """Sliding cover (assembly position, closed). Plate between the long walls, tongues in their grooves,
    reaches over the lowered inner end wall and sticks out SLIDE_TAB as a finger tab; detent bump underneath."""
    big = 1000
    hy = BAND_IN - SBOX_CLR
    wi = hy - SBOX_W
    inner_end = x1 if x0 < 0 else x0
    sgn = 1 if x0 < 0 else -1
    c = SLIDE_CLR
    plate = sbox_outline(x0, x1, -SBOX_W - c, SLIDE_G0, SLIDE_CT).common(
        box(min(x0, x1) - 1, max(x0, x1) + 1, -big, big, -big, big))
    ta, tb = sorted((inner_end, inner_end + sgn * SLIDE_TAB))
    oa, ob = sorted((inner_end, inner_end - sgn * (SBOX_W + 1)))
    over = box(oa, ob, -wi + c, wi - c, SLIDE_G0, SLIDE_CT)                      # over the lowered end wall
    tab = box(ta, tb, -25, 25, SLIDE_G0, SLIDE_CT)                               # finger tab (clear of the hanger blocks)
    xs = sbox_straight_x()
    if sgn > 0:                                     # long box: outer end rounded, inner end at +X
        g0, g1 = max(min(x0, x1), -xs) + 0.5, inner_end
    else:                                           # short box: both ends straight, inner end at -X
        g0, g1 = inner_end, max(x0, x1) - SBOX_W - 0.5
    # tongues: flat underside on the groove floor, top chamfered 45 deg to follow the groove roof (also takes the
    # first-layer squish off the edge, the cover prints top face down); leading end tapered in plan
    tip, zb = wi + SLIDE_GROOVE_D - c, SLIDE_GF + SLIDE_VCLR
    prof = [(wi - c - 0.01, zb), (tip, zb), (tip, SLIDE_CT - (tip - wi)), (wi, SLIDE_CT), (wi - c - 0.01, SLIDE_CT)]
    lead = g0 if sgn > 0 else g1                    # end that enters the groove first when closing
    taper = Part.Face(Part.makePolygon([V(lead, wi - c, -big), V(lead, tip + 1, -big), V(lead + sgn * 3, tip + 1, -big),
                                        V(lead, wi - c, -big)])).extrude(V(0, 0, 2 * big))
    tongues = []
    for sy in (1, -1):
        t = prism_x(prof, g0, g1).cut(taper)
        tongues.append(t if sy > 0 else mirror_y(t))
    ec = inner_end - sgn * SBOX_W / 2
    bump = cyl_y(0.6, -15, 15, ec, SLIDE_G0 + 0.1).common(box(ec - 1, ec + 1, -16, 16, SLIDE_G0 - 1, SLIDE_G0 + 0.01))
    return clean(fuse([plate, over, tab] + tongues + [bump]).cut(
        box(-big, big, -big, big, SLIDE_CT, SLIDE_CT + 5)))


# ---------------- Reference box rim & spool ----------------
def ref_box():
    oy = OY_AVG
    wall = ring(OX - WALL, oy - WALL, R_BOX_IN, OX, oy, R_BOX, -230, 0)
    fl = ring(OX - 0.5, oy - 0.5, R_BOX, OX + FLANGE_OUT, oy + FLANGE_OUT, R_BOX + FLANGE_OUT,
              FLANGE_BOT, -RIM_H)
    gc = FLANGE_OUT - RIM_GROOVE_C                 # groove under the flange (assumed position)
    groove = ring(OX + gc - RIM_GROOVE_W / 2, oy + gc - RIM_GROOVE_W / 2, R_BOX + gc - RIM_GROOVE_W / 2,
                  OX + gc + RIM_GROOVE_W / 2, oy + gc + RIM_GROOVE_W / 2, R_BOX + gc + RIM_GROOVE_W / 2,
                  FLANGE_BOT - 1, FLANGE_BOT + RIM_GROOVE_D)
    return wall.fuse(fl).cut(groove)


def print_mesh(shape, matrix=None):
    p = shape.transformGeometry(matrix) if matrix else shape.copy()
    bb = p.BoundBox
    p = p.transformGeometry(App.Matrix(1, 0, 0, -bb.XMin, 0, 1, 0, -bb.YMin, 0, 0, 1, -bb.ZMin, 0, 0, 0, 1))
    mesh = MeshPart.meshFromShape(Shape=p, LinearDeflection=0.03, AngularDeflection=0.25, Relative=False)
    mb = mesh.BoundBox
    mesh.translate(-mb.XMin, -mb.YMin, -mb.ZMin)
    return p, mesh


def rot(axis, deg):
    m = App.Matrix()
    getattr(m, "rotate" + axis)(math.radians(deg))
    return m


def add(doc, name, shape, color, transp=0):
    o = doc.addObject("Part::Feature", name)
    o.Shape = shape
    if App.GuiUp:
        o.ViewObject.ShapeColor = color
        o.ViewObject.Transparency = transp
    return o


def build(export=True):
    if "CerealLid" in App.listDocuments():
        App.closeDocument("CerealLid")
    doc = App.newDocument("CerealLid")

    lid_full = make_lid()
    lid, seam = split_lid(lid_full)
    latch, hanger, adapter = make_latch(), make_hanger(), make_hub_adapter()
    cradle, gasket, grommet = make_hy_cradle(), make_gasket(), make_grommet()
    cradle_mini = make_mini_cradle()
    bodies = {k: make_sbox_body(x0, x1, sn) for k, (x0, x1), sn in zip("LR", SBOX_X, SBOX_SNAPS_X)}
    covers = {k: make_sbox_cover(x0, x1) for k, (x0, x1) in zip("LR", SBOX_X)}
    bolts = [make_lock_bolt(sx, sy) for sn in SBOX_SNAPS_X for sx in sn if sx in LOCK_X for sy in (1, -1)]

    for k, s in lid.items():
        add(doc, "Lid_" + k, s, (0.55, 0.80, 0.90), 20)
    for i, lx in enumerate(LATCH_X):
        for side, sname in ((1, "B"), (-1, "A")):
            s = latch.translated(V(lx, 0, 0))
            add(doc, "Latch_%s%d" % (sname, i + 1), s if side > 0 else mirror_y(s), (0.2, 0.2, 0.2))
    add(doc, "Hanger_B", hanger, (0.95, 0.6, 0.15))
    add(doc, "Hanger_A", mirror_y(hanger), (0.95, 0.6, 0.15))
    add(doc, "HygroCradle_Mini", cradle_mini, (0.95, 0.6, 0.15))
    alt = add(doc, "Alt_HygroCradle_50x50", cradle, (0.95, 0.6, 0.15))              # same dovetails: either one
    if App.GuiUp:
        alt.ViewObject.Visibility = False
    for k in "LR":
        add(doc, "SilicaBox_" + k, bodies[k], (0.94, 0.75, 0.2))
        add(doc, "SilicaBoxCover_" + k, covers[k], (0.35, 0.55, 0.85))
    for i, bt in enumerate(bolts):
        add(doc, "SilicaLockBolt_%d" % (i + 1), bt, (0.2, 0.2, 0.2))
    add(doc, "SilicaBoxHandle", make_sbox_handle2().translated(V(HANDLE_X, 0, SBOX_Z0)), (0.2, 0.7, 0.3))
    add(doc, "SilicaHandleLockBar", make_handle_lockbar().translated(V(HANDLE_X, 0, SBOX_Z0)), (0.2, 0.2, 0.2))
    m = App.Matrix(0, 1, 0, PULL_SLOT_X["L"] + BEAD_SLOT / 2 - 0.5, 1, 0, 0, 0, 0, 0, -1, SBOX_Z0, 0, 0, 0, 1)
    pl = add(doc, "Alt_SilicaPuller", make_silica_puller().transformGeometry(m), (0.2, 0.7, 0.3))   # clipped in, L box
    if App.GuiUp:
        pl.ViewObject.Visibility = False
    for s in (-1, 1):
        a = adapter.copy()
        a.rotate(V(0, 0, 0), V(1, 0, 0), 90 if s > 0 else -90)   # flange outward, cone into hub
        a.translate(V(0, s * (SPOOL_W / 2 + 2), -D_AXLE))     # flange flat on the spool face
        add(doc, "HubAdapter_" + ("B" if s > 0 else "A"), a, (0.5, 0.5, 0.5))
    for s in (-1, 1):                                            # 608 bearings, pressed in from the cone tip
        y0 = 21.6 if s > 0 else -28.6                            # pocket: 6.8..14 mm from the flange
        add(doc, "Ref_Bearing_608_" + ("B" if s > 0 else "A"),
            cyl_y(11, y0, y0 + 7, 0, -D_AXLE).cut(cyl_y(4, y0 - 1, y0 + 8, 0, -D_AXLE)), (0.75, 0.75, 0.8))
    if HANG_MODE == "pin":                                       # tip at -Y, head outside the +Y hanger
        ax = make_axle_pin().transformGeometry(rot("Z", 90)).translated(V(0, AXLE_TIP_Y, -D_AXLE))
    else:
        ax = make_axle().transformGeometry(rot("Z", 90)).translated(V(0, AXLE_Y0, -D_AXLE))   # flat side down
    add(doc, "Axle_8mm_x88", ax, (0.3, 0.3, 0.3))
    add(doc, "Ref_Spool_200x67", cyl_y(SPOOL_D / 2, -SPOOL_W / 2, SPOOL_W / 2, 0, -D_AXLE).cut(
        cyl_y(SPOOL_HOLE / 2, -40, 40, 0, -D_AXLE)),
        (0.85, 0.35, 0.19), 30)
    hb = HY_FACE_X - MH_D
    zt = HY_TOP - MH_DROP
    zc = zt - 0.25 - MH_W / 2
    add(doc, "Ref_MiniHygrometer", box(hb, hb + MH_D, -MH_L / 2, MH_L / 2, zt - 0.25 - MH_W, zt - 0.25).fuse(
        box(HY_FACE_X, HY_FACE_X + MH_FT, -MH_FL / 2, MH_FL / 2, zc - MH_FW / 2, zc + MH_FW / 2)), (0.15, 0.15, 0.15))
    add(doc, "Ref_Box_Rim", ref_box(), (0.85, 0.85, 0.85), 70)
    add(doc, "Ref_PTFE", cyl_z(2, -40, ZT + 40, OUT_X, 0), (0.95, 0.95, 0.95))

    tpu = doc.addObject("App::DocumentObjectGroup", "TPU_Seals")
    pink = (0.85, 0.30, 0.55)
    for k, s in gasket.items():
        tpu.addObject(add(doc, "TPU_Gasket_" + k, s.translated(V(0, 0, SEAT + G_RECESS - G_T)), pink))
    tpu.addObject(add(doc, "TPU_SeamStrip", seam, pink))

    g = grommet.transformGeometry(grommet_matrix())                   # grommet flipped into place
    tpu.addObject(add(doc, "TPU_Grommet_installed", g, pink))
    doc.recompute()

    vols = [sbox_outline(x0, x1, -SBOX_W, SBOX_Z0 + SBOX_FLOOR, SLIDE_G0).cut(bodies[k]).Volume / 1000
            for k, (x0, x1) in zip("LR", SBOX_X)]
    glen = 2 * (2 * GCX + 2 * GCY) - (8 - 2 * math.pi) * GCR
    report = ["Gasket centreline length: %.0f mm (cut the old 680 mm gasket to this)" % glen] + ["Silica capacity: %s cm3 (~%.0f g beads)" % (" + ".join("%.0f" % v for v in vols), sum(vols) * 0.75)]
    if export:
        out = os.path.join(HERE, "stl_cereal")
        os.makedirs(out, exist_ok=True)
        for f in os.listdir(out):
            if f.endswith(".stl"):
                os.remove(os.path.join(out, f))
        big = 1000
        flip = rot("X", 180)
        prints = {
            "Lid_L": (lid["L"], flip),                             # flat top on the bed
            "Lid_R": (Part.makeCompound([lid["R"], make_pocket_support()]), flip),   # + breakaway support
            "Latch_x4": (latch, rot("Y", 90)),                     # profile flat on the bed
            "Hanger_B": (hanger, rot("X", -90)),                    # outer face of the arm on the bed
            "Hanger_A": (mirror_y(hanger), rot("X", 90)),           # the MIRRORED one for the other side
            "HubAdapter_x2": (adapter, None),
            # printed 8 mm axle (100% infill), lying down on its 45 deg flat
            "Axle_8mm_x88": (make_axle_pin() if HANG_MODE == "pin" else make_axle(), None),
            "HygroCradle_Mini": (cradle_mini, rot("Y", -90)),      # on its back, open front up (no bridges)
            "HygroCradle_50x50": (cradle, None),
            "SilicaBox_L": (bodies["L"], None),                    # floor on the bed
            "SilicaBox_R": (bodies["R"], None),
            "SilicaBoxCover_L": (covers["L"], flip),               # flat face on the bed
            "SilicaBoxCover_R": (covers["R"], flip),
            "SilicaLockBolt_x6": (make_lock_bolt(0, 1), rot("Y", 90)),     # on its side: L-profile flat on the bed
            "SilicaPuller": (make_silica_puller(), rot("X", 90)),           # flat, thin legs on the bed
            "SilicaBoxHandle": (make_sbox_handle(), rot("Y", 90)),          # v1 (snap prongs), flat, profile on the bed
            "SilicaBoxHandle_v2": (make_sbox_handle2(), rot("Y", 90)),       # ledge + lock bar, flat
            "SilicaHandleLockBar": (make_handle_lockbar(), None),
            # TEST: snap-in hangers + grip axle (try against the current bayonet set)
            "SnapHanger_B": (make_snap_hanger(), rot("X", -90)),
            "SnapHanger_A": (mirror_y(make_snap_hanger()), rot("X", 90)),
            "Axle_8mm_x88_Grip": (make_axle(grip=True), None),
            "SlideHanger_B": (make_slide_hanger(), rot("X", -90)),
            "SlideHanger_A": (mirror_y(make_slide_hanger()), rot("X", 90)),
            "Slider_B": (make_slider(AXLE_COLLAR_R), rot("X", -90)),         # outer face on the bed
            "Slider_A": (mirror_y(make_slider(AXLE_R)), rot("X", 90)),
            "SliderLockPlate_x2": (make_slider_lockplate(), rot("X", 90)),
            "SpringHanger_B": (make_spring_hanger(), rot("X", -90)),
            "SpringHanger_A": (mirror_y(make_spring_hanger()), rot("X", 90)),
            "SpringSlider_B": (make_spring_slider(), rot("X", -90)),           # outer face on the bed
            "SpringSlider_A": (mirror_y(make_spring_slider()), rot("X", 90)),   # mirrored: ramp must face the slot mouth
            "SpringLockPlate_x2": (make_spring_lockplate(), rot("X", 90)),
            "Axle_8mm_x88_SpringStops": (make_axle(grip=True, stop_r=SP_STOP_R), None),
            # spring-lock TEST pieces: hanger section (slot + spring channel, no dovetail) + a short axle-end stub
            "SpringTest_HangerSection": (make_spring_hanger().common(box(-30, 20, 0, 100, -D_AXLE - 13, -D_AXLE + SP_Z0 + 3 + SP_LOCKED + 3)),
                                         rot("X", -90)),
            "SpringTest_ChannelSlice": (make_spring_hanger().common(box(-17, 0, 0, 100, -D_AXLE + 3.6,
                                                                         -D_AXLE + SP_Z0 + 3 + SP_LOCKED + 3)), rot("X", -90)),
            "SpringTest_AxleStub": (make_axle(stop_r=SP_STOP_R).common(box(ARM_Y0 - 15 - AXLE_Y0, 200, -20, 20, -20, 20)), None),
            "HygroShim_OldCradle": (make_hygro_shim(), rot("Y", -90)),      # glue-in sleeve, back on the bed
            "TPU_Gasket_L": (gasket["L"], None),
            "TPU_Gasket_R": (gasket["R"], None),
            "TPU_SeamStrip": (seam, rot("Y", 90)),
            "TPU_Grommet": (grommet, None),
            "TPU_CapTether": (make_cap_tether(), None),
            # quick fit tests (print these first!)
            "Test_Corner": (lid_full.common(box(80, big, 30, big, SKIRT_BOT, SEAT + G_RECESS + 2)), flip),
            "Test_HangerFit2_g0.15_1notch": (make_hanger_fit_test(0.15, 1), rot("X", -90)),
            "Test_HangerFit2_g0.25_2notch": (make_hanger_fit_test(0.25, 2), rot("X", -90)),
            "Test_HangerFit2_g0.35_3notch": (make_hanger_fit_test(0.35, 3), rot("X", -90)),
            "Test_LatchSection": (lid_full.common(box(LATCH_X[1] - 20, LATCH_X[1] + 20, 25, big, -big, 16)), flip),
        }
        for name, (s, m) in prints.items():
            p, mesh = print_mesh(s, m)
            mesh.write(os.path.join(out, name + ".stl"))
            bb = p.BoundBox
            report.append("%-24s %6.1f x %6.1f x %6.1f mm  %6.1f cm3  solids=%d %s" % (
                name, bb.XLength, bb.YLength, bb.ZLength, p.Volume / 1000, len(p.Solids),
                "OK" if max(bb.XLength, bb.YLength) <= 175 and bb.ZLength <= 175 else "TOO BIG"))
        doc.saveAs(os.path.join(HERE, "CerealLid.FCStd"))
    if App.GuiUp:
        import FreeCADGui as Gui
        Gui.activeDocument().activeView().viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
    print("\n".join(report))
    return doc


if not globals().get("CEREAL_NO_BUILD"):
    build()
