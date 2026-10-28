"""
Render the spool-change animation from the CerealLid assembly (run inside the FreeCAD GUI after cereal_lid.py):
    exec(open(r"<path>/make_spool_animation.py").read())
Frames go to renders/anim/frame_NNNN.png; captions + MP4 are added afterwards by make_spool_video.py.
"""
import math
import os
import FreeCAD as App
import FreeCADGui as Gui

V = App.Vector
HERE = r"C:\\Users\\SK\\Desktop\\Personal\\CerealFilamentLid\\v1\\source"
OUT = os.path.join(HERE, "renders", "anim")
W_PX, H_PX = 1280, 720
doc = App.getDocument("CerealLid")

SPOOL = ["Ref_Spool_200x67", "HubAdapter_A", "HubAdapter_B", "Ref_Bearing_608_A", "Ref_Bearing_608_B", "Axle_8mm_x88"]
BOX = ["Ref_Box_Rim"]
LATCH = [o.Name for o in doc.Objects if o.Name.startswith("Latch_")]
SKIP = ("Alt_",)
objs = {o.Name: o for o in doc.Objects if o.TypeId == "Part::Feature"}
LID = [n for n in objs if n not in SPOOL + BOX + LATCH and not n.startswith(SKIP)]
for n, o in objs.items():
    o.ViewObject.Visibility = not n.startswith(SKIP)
objs["Ref_Box_Rim"].ViewObject.Transparency = 75
for n in ("Lid_L", "Lid_R"):
    objs[n].ViewObject.Transparency = 35
spool_color_old, spool_color_new = (0.85, 0.35, 0.19), (0.20, 0.45, 0.85)

ns = globals().get("CEREAL_NS") or {}
PY, PZ = ns.get("PY", 49.5), ns.get("PZ", 12.0)
ang = math.radians(ns.get("HANG_SLOT_DEG", 10.0))
SLOT_D = V(-math.cos(ang), 0, math.sin(ang))
LIFT = 250.0


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def spool_offset(u):
    """0 = hanging in the hooks, 1 = off to the side. Slide out along the slot, drop, then away."""
    a = smooth(u / 0.35) * 24
    p = SLOT_D * a
    p += V(0, 0, -45 * smooth((u - 0.35) / 0.3))
    p += V(-150 * smooth((u - 0.65) / 0.35), 0, 0)
    return p


def pose(latch_deg, lift, spool_u, new_spool):
    for n in LID:
        objs[n].Placement = App.Placement(V(0, 0, lift), App.Rotation())
    for n in LATCH:
        sy = -1 if "_A" in n else 1
        objs[n].Placement = App.Placement(V(0, 0, lift), App.Rotation(V(1, 0, 0), sy * latch_deg), V(0, sy * PY, PZ))
    off = V(0, 0, lift) + spool_offset(spool_u)
    for n in SPOOL:
        objs[n].Placement = App.Placement(off, App.Rotation())
    objs["Ref_Spool_200x67"].ViewObject.ShapeColor = spool_color_new if new_spool else spool_color_old


# timeline (15 fps): (frames, latch deg, lift, spool_u, new spool, caption)
STEPS = [
    (15, (0, 0), (0, 0), (0, 0), False, "Box closed and latched"),
    (22, (0, 110), (0, 0), (0, 0), False, "1. Open the 4 latches"),
    (40, (110, 110), (0, LIFT), (0, 0), False, "2. Lift the lid - the spool comes out with it"),
    (36, (110, 110), (LIFT, LIFT), (0, 1), False, "3. Slide the axle out of the hanger hooks, lower the spool"),
    (12, (110, 110), (LIFT, LIFT), (1, 1), True, "4. Fit adapters + axle into the new spool"),
    (36, (110, 110), (LIFT, LIFT), (1, 0), True, "5. Hang it: axle in, along the hooks, flat side down"),
    (40, (110, 110), (LIFT, 0), (0, 0), True, "6. Lower the lid onto the box"),
    (22, (110, 0), (0, 0), (0, 0), True, "7. Close the latches until they click"),
    (15, (0, 0), (0, 0), (0, 0), True, "Done - feed the filament through the outlet"),
]

os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    if f.endswith(".png"):
        os.remove(os.path.join(OUT, f))
v = Gui.activeDocument().activeView()
# frame the camera on the widest pose (lid lifted, spool off to the side), then keep it fixed
pose(110, LIFT, 1.0, False)
v.viewIsometric()
Gui.SendMsgToActiveView("ViewFit")
captions = []
k = 0
for n, (a0, a1), (l0, l1), (s0, s1), new, cap in STEPS:
    for i in range(n):
        u = smooth(i / max(n - 1, 1))
        pose(a0 + (a1 - a0) * u, l0 + (l1 - l0) * u, s0 + (s1 - s0) * u, new)
        Gui.updateGui()
        v.saveImage(os.path.join(OUT, "frame_%04d.png" % k), W_PX, H_PX, "White")
        captions.append(cap)
        k += 1
open(os.path.join(OUT, "captions.txt"), "w").write("\n".join(captions))
pose(0, 0, 0, False)
print("rendered %d frames" % k)
