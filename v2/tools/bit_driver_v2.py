"""Compact 90 deg double-ended bit driver for the lid seam screws (v2) + a socket fit test.

One lever, two heads: a 1/4" hex bit socket at one end, a 4 mm hex (precision) bit socket at the other. The bits
sit at right angles to the lever, so you can turn screws where a straight screwdriver doesn't fit. The heads are
as small as the bits allow (1.6 mm wall round the hex): 1/4" head 10.7 mm, 4 mm head 8 mm.

Prints flat (lever on the bed, hex vertex up = self-supporting). Edit the sizes below and run with freecadcmd:
  "C:\\Users\\SK\\AppData\\Local\\Programs\\FreeCAD 1.1\\bin\\freecadcmd.exe" bit_driver_v2.py
Outputs: Tool_BitDriver_Dual.stl and Tool_BitSocket_FitTest.stl next to this script.
"""
import math
import os

import FreeCAD as App
import MeshPart
import Part

V = App.Vector
HERE = r"C:\Users\SK\Desktop\Personal\CerealFilamentLid\v2\tools"

# ---- sizes (mm)
Q_AF, Q_CLR, Q_DEPTH = 6.35, 0.15, 9.0       # 1/4" bit: across flats, socket clearance, socket depth
M_AF, M_CLR, M_DEPTH = 4.0, 0.12, 8.0        # 4 mm bit
WALL = 1.6                                   # wall round the hex
ARM_L, ARM_W, ARM_T = 72.0, 10.0, 8.0        # lever: centre-to-centre length, width, thickness
EDGE_R = 1.2                                 # rounding on the lever / head edges
FIT_TEST = {"Q": (0.08, 0.15, 0.22), "M": (0.06, 0.12, 0.18)}   # socket clearances in the fit-test coupon


def corner(af):
    return af * 2 / math.sqrt(3)             # hex across corners


def hex_socket(af, depth, x0=0.0, cy=0.0, cz=0.0):
    """Hex prism along +x from x0, vertex up (prints clean lying flat), with a 0.6 mm entry chamfer."""
    r = af / math.sqrt(3)
    pts = [V(x0 - 0.01, cy + r * math.cos(math.radians(90 + 60 * k)), cz + r * math.sin(math.radians(90 + 60 * k)))
           for k in range(6)]
    s = Part.Face(Part.makePolygon(pts + [pts[0]])).extrude(V(depth + 0.01, 0, 0))
    return s.fuse(Part.makeCone(r + 0.6, r, 0.6, V(x0 - 0.01, cy, cz), V(1, 0, 0)))


def rounded_box(lx, ly, lz, origin, r):
    b = Part.makeBox(lx, ly, lz, origin)
    try:
        return b.makeFillet(min(r, min(lx, ly, lz) / 2 - 0.05), b.Edges)
    except Exception:
        return b


def head(af, clr, depth, y):
    """Head block (socket opening at x = 0, pointing -x), centred on y, sitting on the bed."""
    h = max(corner(af + clr) + 2 * WALL, ARM_T)
    lx = depth + WALL
    blk = rounded_box(lx, h, h, V(0, y - h / 2, 0), EDGE_R)
    return blk, hex_socket(af + clr, depth, 0, y, h / 2), h, lx


def driver():
    hq, sq, Hq, Lq = head(Q_AF, Q_CLR, Q_DEPTH, 0.0)
    hm, sm, Hm, Lm = head(M_AF, M_CLR, M_DEPTH, ARM_L)
    x1 = max(Lq, Lm)
    arm = rounded_box(ARM_W, ARM_L, ARM_T, V(x1 - ARM_W, 0, 0), EDGE_R)
    tool = hq.fuse([hm, arm])
    for k in range(5):                                     # grip grooves across the top of the lever
        y = ARM_L * 0.3 + k * 6
        tool = tool.cut(Part.makeBox(ARM_W + 2, 1.2, 1.0, V(x1 - ARM_W - 1, y, ARM_T - 0.5)))
    tool = tool.cut(sq.fuse(sm)).removeSplitter()
    return tool, Hq, Hm


def fit_test():
    """Small bar with three 1/4" and three 4 mm sockets at different clearances (1-3 notches = loose -> tight
    order as listed in FIT_TEST). Try a bit in each and set Q_CLR / M_CLR to the one that holds best."""
    cells = [("Q", c) for c in FIT_TEST["Q"]] + [("M", c) for c in FIT_TEST["M"]]
    pitch, h = 13.0, corner(Q_AF + max(FIT_TEST["Q"])) + 2 * WALL
    bar = Part.makeBox(Q_DEPTH + WALL, pitch * len(cells), h, V(0, 0, 0))
    cuts = []
    for i, (kind, c) in enumerate(cells):
        af, depth = (Q_AF, Q_DEPTH) if kind == "Q" else (M_AF, M_DEPTH)
        cy = pitch * (i + 0.5)
        cuts.append(hex_socket(af + c, depth, 0, cy, h / 2))
        n = (i % 3) + 1                                     # 1..3 notches on the back = clearance order
        for k in range(n):
            cuts.append(Part.makeBox(1.0, 1.2, 1.5, V(Q_DEPTH + WALL - 1.0, cy - 3 + k * 2.2, h - 1.5)))
    return bar.cut(Part.makeCompound(cuts)).removeSplitter()


def write(shape, name):
    bb = shape.optimalBoundingBox()
    s = shape.copy()
    s.translate(V(-bb.XMin, -bb.YMin, -bb.ZMin))
    MeshPart.meshFromShape(Shape=s, LinearDeflection=0.03, AngularDeflection=0.25, Relative=False).write(
        os.path.join(HERE, name + ".stl"))
    print("TOOL %-24s %.1f x %.1f x %.1f mm  %.1f cm3  solids %d valid %s" % (
        name, bb.XLength, bb.YLength, bb.ZLength, shape.Volume / 1000, len(shape.Solids), shape.isValid()))


tool, Hq, Hm = driver()
write(tool, "Tool_BitDriver_Dual")
write(fit_test(), "Tool_BitSocket_FitTest")
print("TOOL head sizes: 1/4in %.1f mm, 4mm %.1f mm" % (Hq, Hm))
