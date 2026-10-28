"""Export the v2 model's printable parts as print-oriented STLs (v2/stl_cereal) and, with "3mf", build the Bambu
Studio projects (v2/print) with the same settings as v1 (A1 mini, 0.4, Bambu PETG Basic + eSUN TPU 95A).

Run:  "C:\\Users\\SK\\AppData\\Local\\Programs\\FreeCAD 1.1\\bin\\freecadcmd.exe" export_v2.py          (STLs only)
then: python bambu\\make_v2_projects.py                                                              (3MFs)
"""
import math
import os

import FreeCAD as App
import MeshPart
import Part

HERE = r"C:\Users\SK\Desktop\Personal\CerealFilamentLid\v2"
OUT = os.path.join(HERE, "stl_cereal")


def rot(axis, deg):
    m = App.Matrix()
    getattr(m, "rotate" + axis)(math.radians(deg))
    return m


FLIP = rot("X", 180)
# export name: (objects fused for printing, print orientation)
PRINTS = {
    "Lid_L": (["Lid_L"], FLIP),                                  # top face on the bed
    "Lid_R": (["Lid_R"], FLIP),                                  # pocket floor bridges (no support)
    "Latch_x4": (["Latch"], rot("Y", 90)),                       # profile flat on the bed
    "Hanger_B": (["Hanger_B"], rot("X", -90)),                   # outer face on the bed
    "Hanger_A": (["Hanger_A"], rot("X", 90)),
    "HubHalf_A": (["HubHalfA"], FLIP),                           # flange on the bed (45 deg cones inside)
    "HubHalf_B": (["HubHalfB"], FLIP),
    "HubRetainer_x2": (["HubRetainer"], None),                   # coin slots up
    "StubAxle_x2": (["StubAxle"], FLIP),                         # stands on its collar (100 % infill in the 3MF)
    "StubClip_x2": (["StubClip"], None),                         # flat (4 printed: 2 spares)
    "SilicaBox_L": (["SilicaBox_L"], None),
    "SilicaBox_R": (["SilicaBox_R"], None),
    "SilicaBoxCover_L": (["SilicaBoxCover_L"], FLIP),
    "SilicaBoxCover_R": (["SilicaBoxCover_R"], FLIP),
    "SilicaLockBolt_x6": (["LockBolt"], rot("X", 90)),               # stands on its inner end
    "SilicaBoxHandle_v2": (["SilicaBoxHandle"], rot("Y", 90)),
    "HygroCradle_Mini": (["HygroCradle"], rot("Y", -90)),        # on its back, no supports
    "TPU_SeamStrip": (["SeamStrip"], rot("Y", 90)),
    "TPU_Grommet": (["Grommet"], None),
    "TPU_CapTether": (["CapTether"], None),
}


def export():
    doc = App.openDocument(os.path.join(HERE, "CerealLid_v2.FCStd"))
    doc.recompute()
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".stl"):
            os.remove(os.path.join(OUT, f))
    for name, (objs, m) in PRINTS.items():
        shapes = [doc.getObject(o).Shape for o in objs]
        s = Part.makeCompound(shapes) if len(shapes) > 1 else shapes[0].copy()   # support stays a separate solid
        if m:
            s = s.transformGeometry(m)
        bb = s.optimalBoundingBox()                 # exact (BoundBox is loose on revolved/B-spline faces)
        s.translate(App.Vector(-bb.XMin, -bb.YMin, -bb.ZMin))
        mesh = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.03, AngularDeflection=0.25, Relative=False)
        mesh.write(os.path.join(OUT, name + ".stl"))
        print("EXPORT %-20s %6.1f x %6.1f x %6.1f mm  %6.1f cm3  solids=%d" % (
            name, bb.XLength, bb.YLength, bb.ZLength, s.Volume / 1000, len(s.Solids)))
    App.closeDocument(doc.Name)


export()
