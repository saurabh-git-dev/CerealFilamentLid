"""Assembly animation of CerealLid v2 (run inside the FreeCAD GUI with CerealLid_v2.FCStd open).

setup()            copies every part (global shapes) into a separate document "AssemblyAnim"
render(f0, f1)     renders frames f0..f1-1 to video/frames/f_00000.png ...
make_video.py      encodes the frames (captions from CAPTIONS below) with ffmpeg.
The parametric model is never touched.
"""
import json
import math
import os

import FreeCAD as App
import FreeCADGui as Gui
import Part

V = App.Vector
HERE = r"C:\Users\SK\Desktop\Personal\CerealFilamentLid\v2\video"
FRAMES = os.path.join(HERE, "frames")
FPS = 30
DURATION = 46.0
W, H = 2560, 1440
ZOOM = 0.6                                           # FreeCAD keeps a 45 deg lens
LIFT = 170.0                                         # lid assembly is built this high above the box

C = {  # colours
    "lid": (0.91, 0.62, 0.22), "tpu": (0.62, 0.86, 0.92), "latch": (0.18, 0.43, 0.84),
    "hanger": (0.33, 0.36, 0.40), "hub": (0.50, 0.58, 0.66), "axle": (0.25, 0.27, 0.30),
    "silica": (0.95, 0.95, 0.95), "cover": (0.80, 0.82, 0.85), "bolt": (0.84, 0.27, 0.25),
    "cradle": (0.23, 0.65, 0.42), "box": (0.80, 0.85, 0.88), "spool": (0.12, 0.12, 0.13),
    "fil": (0.0, 0.62, 0.62),
}

CAPTIONS = [
    (0.3, 4.8, "1  Join the lid halves  -  TPU seam strip between, 6 M3 screws"),
    (5.3, 8.0, "2  Press the TPU gasket into the groove (underside)"),
    (8.3, 11.9, "3  Hangers A + B: up, then slide out into the dovetail sockets"),
    (12.0, 13.9, "4  Hygrometer cradle"),
    (14.0, 20.6, "5  Silica boxes: slide the covers on, fit the handle, push in, slide the 6 bolts out to lock"),
    (21.0, 23.6, "6  Latches onto their pivot stubs"),
    (24.0, 27.4, "7  Outlet: TPU grommet into the cone, tethered cap on top"),
    (27.8, 33.3, "8  Spool: hub adapters in, axle through, drop it into the bayonet hangers"),
    (33.6, 37.8, "9  Lower the lid onto the cereal box"),
    (37.9, 40.0, "10  Close the 4 latches"),
    (40.3, 46.0, "Cereal box filament lid  -  v2"),
]

# camera keyframes: t, azimuth, elevation, target, distance, target follows the lid lift (1) or not (0)
CAM = [
    (0.0, -60, 28, (0, 0, 10), 680, 1), (4.6, -40, 26, (0, 0, 10), 560, 1),
    (5.6, -35, -32, (0, 0, 0), 520, 1), (8.2, -30, -32, (0, 0, -10), 560, 1),
    (11.6, -15, -30, (0, 0, -40), 640, 1), (12.4, 15, -28, (50, 0, -10), 470, 1),
    (13.8, 25, -30, (30, 0, -10), 520, 1), (20.6, 40, -30, (0, 0, 0), 580, 1),
    (21.4, 70, 10, (0, 0, 0), 560, 1), (23.6, 80, 14, (0, 0, 0), 560, 1),
    (24.4, 35, 50, (88, 0, 50), 360, 1), (27.4, 15, 46, (88, 0, 36), 270, 1),
    (28.4, -30, 4, (0, 0, -190), 1150, 1), (30.8, -35, 6, (0, 0, -180), 1150, 1), (33.0, -40, 8, (0, 0, -70), 760, 1),
    (34.2, -50, 16, (0, 0, -75), 980, 0), (37.6, -60, 18, (0, 0, -80), 940, 0),
    (40.0, -25, 14, (0, 0, -80), 820, 0), (46.0, 70, 22, (0, 0, -80), 900, 0),
]


def ease(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3 - 2 * u)


def lift(t):
    return LIFT * (1 - ease((t - 34.4) / 3.2))


class Item:
    def __init__(self, name, shape, colour, appear=0.0, moves=(), lid=True, alpha=0, rot=None):
        self.name, self.shape, self.colour, self.appear = name, shape, colour, appear
        self.moves, self.lid, self.alpha, self.rot = list(moves), lid, alpha, rot

    def placement(self, t):
        off = V(0, 0, lift(t) if self.lid else 0)
        for t0, t1, v in self.moves:
            off = off + v * (1 - ease((t - t0) / (t1 - t0)))
        pl = App.Placement(off, App.Rotation())
        if self.rot:
            pt, axis, ang = self.rot(t)
            pl = pl.multiply(App.Placement(V(), App.Rotation(axis, ang), pt))
        return pl.multiply(self.base)                 # the shape's own placement (links carry one)


def gshape(src, name):
    return src.getObject(name).Shape.copy()


def spool_shape(P):
    r, w, hole = P.SPOOL_D / 2, P.SPOOL_W, P.SPOOL_HOLE / 2
    c = V(0, -w / 2, -P.D_AXLE)
    ax = V(0, 1, 0)
    fl = Part.makeCylinder(r, 2.5, c, ax).fuse(Part.makeCylinder(r, 2.5, c + V(0, w - 2.5, 0), ax))
    core = Part.makeCylinder(hole + 6, w, c, ax)
    return fl.fuse(core).cut(Part.makeCylinder(hole, w + 2, c - V(0, 1, 0), ax)), \
        Part.makeCylinder(r - 14, w - 5, c + V(0, 2.5, 0), ax).cut(Part.makeCylinder(hole + 6, w, c, ax))


def build_items(src):
    P = src.getObject("Params")
    it = []
    lw = 0.8
    it.append(Item("Lid_L", gshape(src, "Lid_L"), C["lid"], 0, [(2.4, 4.4, V(-75, 0, 0))]))
    it.append(Item("Lid_R", gshape(src, "Lid_R"), C["lid"], 0, [(2.4, 4.4, V(75, 0, 0))]))
    it.append(Item("SeamStrip", gshape(src, "SeamStrip"), C["tpu"], 0, [(0.8, 2.4, V(0, 0, 90))], alpha=20))
    it.append(Item("Gasket", gshape(src, "Gasket"), C["tpu"], 5.5, [(5.5, 7.6, V(0, 0, -60))], alpha=20))
    for n, sy in (("Hanger_B", 1), ("Hanger_A", -1)):
        it.append(Item(n, gshape(src, n), C["hanger"], 8.4,
                       [(8.4, 10.2, V(0, 0, -110)), (10.2, 11.6, V(0, -sy * 22, 0))]))
    it.append(Item("HygroCradle", gshape(src, "HygroCradle"), C["cradle"], 12.0, [(12.0, 13.6, V(0, 0, -90))]))
    # silica boxes (group moves: spread in x, rise into the lid)
    for side, dx in (("L", -40), ("R", 40)):
        grp = [(17.0, 19.4, V(dx, 0, -120))]
        it.append(Item("SilicaBox_" + side, gshape(src, "SilicaBox_" + side), C["silica"], 14.0, grp))
        cov = (14.4, 15.6, V(60, 0, 0)) if side == "L" else (15.0, 16.2, V(-60, 0, 0))
        it.append(Item("SilicaBoxCover_" + side, gshape(src, "SilicaBoxCover_" + side), C["cover"], 14.0, grp + [cov]))
        if side == "L":
            it.append(Item("SilicaBoxHandle", gshape(src, "SilicaBoxHandle"), C["bolt"], 14.0,
                           grp + [(16.0, 16.9, V(0, 0, -40))]))
    for k in range(1, 7):
        o = src.getObject("LockBolt_%d" % k)
        s = o.Shape.copy()
        sy = 1 if s.BoundBox.YMax > 0 else -1
        dx = -40 if s.BoundBox.XMax < 0 else 40
        it.append(Item("Bolt%d" % k, s, C["bolt"], 14.0,
                       [(17.0, 19.4, V(dx, 0, -120)), (19.6 + 0.12 * k, 20.3 + 0.12 * k, V(0, -sy * P.LOCK_TRAVEL, 0))]))
    # latches: attach (open), close at the end
    for k in range(1, 5):
        o = src.getObject("Latch_%d" % k)
        s = o.Shape.copy()
        sy = 1 if s.BoundBox.YMax > 0 else -1
        x = o.Placement.Base.x
        t0 = 21.0 + 0.35 * (k - 1)

        def rot(t, sy=sy, x=x):
            return V(x, sy * P.PY, P.PZ), V(1, 0, 0), sy * 55 * (1 - ease((t - 38.0) / 1.6))
        it.append(Item("Latch%d" % k, s, C["latch"], t0, [(t0, t0 + 1.4, V(0, sy * 45, 0))], rot=rot))
    it.append(Item("Grommet", gshape(src, "Grommet_InLid"), C["tpu"], 24.0, [(24.0, 25.4, V(0, 0, 60))], alpha=15))
    it.append(Item("Cap", gshape(src, "Cap_InLid"), C["tpu"], 25.4, [(25.4, 26.9, V(0, 0, 60))], alpha=15))
    # spool group
    grp = [(31.0, 33.2, V(0, 0, -190))]
    sp, fil = spool_shape(P)
    it.append(Item("Spool", sp, C["spool"], 27.8, grp))
    it.append(Item("Filament", fil, C["fil"], 27.8, grp))
    for k, sy in (("A", -1), ("B", 1)):          # hub half + its retainer and clip, then the stub axle
        half = grp + [(28.3, 29.4, V(0, sy * 70, 0))]
        it.append(Item("Hub" + k, gshape(src, "HubHalf%s_Asm" % k), C["hub"], 27.8, half))
        it.append(Item("Retainer" + k, gshape(src, "HubRetainer_" + k), C["hub"], 27.8, half))
        it.append(Item("Clip" + k, gshape(src, "StubClip_" + k), C["axle"], 27.8, half))
        it.append(Item("Stub" + k, gshape(src, "StubAxle_" + k), C["axle"], 27.8,
                       grp + [(29.5, 30.8, V(0, sy * 90, 0))]))
    it.append(Item("CerealBox", gshape(src, "BoxRef"), C["box"], 33.4, [(33.4, 34.6, V(0, 0, -160))], lid=False, alpha=72))
    return it


def setup():
    src = App.getDocument("CerealLid_v2")
    if "AssemblyAnim" in App.listDocuments():
        App.closeDocument("AssemblyAnim")
    doc = App.newDocument("AssemblyAnim")
    items = build_items(src)
    for i in items:
        o = doc.addObject("Part::Feature", i.name)
        o.Shape = i.shape
        i.base = o.Placement
        vo = o.ViewObject
        vo.Deviation = 0.15
        vo.ShapeColor = i.colour
        vo.LineColor = tuple(c * 0.45 for c in i.colour)
        vo.LineWidth = 1.0
        vo.Transparency = i.alpha
        vo.DisplayMode = "Flat Lines"
        i.obj = o
    doc.recompute()
    App.ANIM = (doc, items)
    os.makedirs(FRAMES, exist_ok=True)
    with open(os.path.join(HERE, "captions.json"), "w") as f:
        json.dump({"fps": FPS, "duration": DURATION, "captions": CAPTIONS}, f)
    return len(items)


def camera(t):
    k = 0
    while k < len(CAM) - 2 and t > CAM[k + 1][0]:
        k += 1
    a, b = CAM[k], CAM[k + 1]
    u = ease((t - a[0]) / (b[0] - a[0])) if b[0] > a[0] else 1
    mix = lambda p, q: p + (q - p) * u
    az, el, dist, lf = mix(a[1], b[1]), mix(a[2], b[2]), mix(a[4], b[4]), mix(a[5], b[5])
    tg = V(*[mix(a[3][i], b[3][i]) for i in range(3)]) + V(0, 0, lift(t) * lf)
    ca, sa, ce, se = math.cos(math.radians(az)), math.sin(math.radians(az)), math.cos(math.radians(el)), math.sin(math.radians(el))
    fwd = V(-ce * ca, -ce * sa, -se)
    right = fwd.cross(V(0, 0, 1)); right.normalize()
    up = right.cross(fwd); up.normalize()
    m = App.Matrix(right.x, up.x, -fwd.x, 0, right.y, up.y, -fwd.y, 0, right.z, up.z, -fwd.z, 0, 0, 0, 0, 1)
    r = App.Rotation(m)
    dist *= ZOOM
    pos = tg - fwd * dist
    return ("#Inventor V2.1 ascii\nPerspectiveCamera { viewportMapping ADJUST_CAMERA position %f %f %f "
            "orientation %f %f %f %f nearDistance 5 farDistance 5000 aspectRatio 1 focalDistance %f heightAngle 0.6 }"
            % (pos.x, pos.y, pos.z, r.Axis.x, r.Axis.y, r.Axis.z, r.Angle, dist))


def pose(t):
    doc, items = App.ANIM
    for i in items:
        vis = t >= i.appear
        if i.obj.ViewObject.Visibility != vis:
            i.obj.ViewObject.Visibility = vis
        if vis:
            i.obj.Placement = i.placement(t)
    v = Gui.getDocument(doc.Name).ActiveView
    v.setCamera(camera(t))
    return v


def render(f0, f1, w=W, h=H):
    for f in range(f0, f1):
        v = pose(f / FPS)
        v.saveImage(os.path.join(FRAMES, "f_%05d.png" % f), w, h, "White")
    return f1


def still(t, path, w=1600, h=900):
    pose(t).saveImage(path, w, h, "White")
