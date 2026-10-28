"""Offset (90 deg) bit driver for the lid seam screws: holds a standard 1/4" hex bit, lever arm at right angles.
Built directly in print orientation (lying flat on the bed, z up)."""
import math
import FreeCAD as App
import Part
import MeshPart
V = App.Vector
import sys
VARIANT = "4mm" if sys.argv[-1] == "4mm" else "quarter"
OUT = r"C:\Users\SK\Desktop\Personal\CerealFilamentLid\v1\source\stl_cereal\Tool_OffsetBitDriver%s.stl" % (
    "" if VARIANT == "quarter" else "_4mm")

if VARIANT == "quarter":
    BODY_L, BODY_W, BODY_H = 18.0, 13.0, 13.0  # x (along the bit), y, z
    AF, DEPTH = 6.35 + 0.12, 11.0              # 1/4" hex bit, light friction fit
else:
    BODY_L, BODY_W, BODY_H = 16.0, 10.0, 10.0
    AF, DEPTH = 4.0 + 0.1, 10.0                # 4 mm precision bit, light friction fit
ARM_L, ARM_W, ARM_T = 70.0, 10.0, 10.0

body = Part.makeBox(BODY_L, BODY_W, BODY_H, V(0, -BODY_W / 2, 0))
body = body.makeFillet(1.5, [e for e in body.Edges if abs(e.tangentAt(e.FirstParameter).x) > 0.99])
arm = Part.makeBox(ARM_W, ARM_L, ARM_T, V(BODY_L - ARM_W - 2, BODY_W / 2 - 1, 0))
arm = arm.makeFillet(1.5, [e for e in arm.Edges if abs(e.tangentAt(e.FirstParameter).y) > 0.99])
knob = Part.makeCylinder(7.5, ARM_T, V(BODY_L - 2 - ARM_W / 2, BODY_W / 2 - 1 + ARM_L, 0))   # rounded grip end
tool = body.fuse([arm, knob])

# hex socket along X, centred in the body, a vertex pointing up (self-supporting when printed flat)
R = AF / math.sqrt(3)
cy, cz = 0.0, BODY_H / 2
pts = [V(-0.01, cy + R * math.cos(math.radians(90 + 60 * k)), cz + R * math.sin(math.radians(90 + 60 * k))) for k in range(6)]
hexface = Part.Face(Part.makePolygon(pts + [pts[0]]))
socket = hexface.extrude(V(DEPTH, 0, 0))
lead = Part.makeCone(R + 0.8, R, 0.8, V(-0.01, cy, cz), V(1, 0, 0))          # small entry chamfer
tool = tool.cut(socket.fuse(lead))
# grip ridges on the arm
for k in range(5):
    y = BODY_W / 2 + 30 + k * 7
    tool = tool.cut(Part.makeBox(ARM_W + 2, 1.2, 1.0, V(BODY_L - ARM_W - 3, y, ARM_T - 0.6)))
tool = tool.removeSplitter()
bb = tool.BoundBox
tool.translate(V(-bb.XMin, -bb.YMin, -bb.ZMin))
mesh = MeshPart.meshFromShape(Shape=tool, LinearDeflection=0.03, AngularDeflection=0.25, Relative=False)
mesh.write(OUT)
bb = tool.BoundBox
print("TOOL %.1f x %.1f x %.1f mm, %.1f cm3, solids %d, valid %s" % (bb.XLength, bb.YLength, bb.ZLength,
      tool.Volume / 1000, len(tool.Solids), tool.isValid()))
