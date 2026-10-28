"""
Small Bambu Studio project: longer-reach latch trial in PETG on the A1 mini.
  1 x Latch_long2.0 (lip 2 mm lower) - try it on the printed lid half
Bambu PETG Basic, 0.20 mm, 4 walls, 15% gyroid, 5 mm brim, Textured PEI plate.
Output: LatchTrial_PETG_A1mini.3mf

Run:  python make_latch_trial_petg.py [out.3mf "Part:qty,Part:qty"]   (after cereal_lid.py exported ../stl_cereal)
"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import profiles  # noqa: E402
from make_project import EXE, rc_of, plate_hours  # noqa: E402

STL = os.path.join(os.path.dirname(HERE), "stl_cereal")
OUT_3MF = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else "LatchTrial_PETG_A1mini.3mf")
WORK = os.path.join(HERE, "work_latch_trial")
PETG = "Bambu PETG Basic @BBL A1M 0.4 nozzle"
PLATES = [("Latch trial (PETG): 1x +2.0 mm",
           [("Latch_long2.0", 1)])]
if len(sys.argv) > 2:      # e.g.  LatchSet.3mf "Latch_long2.0_ridge2.0:2"   ("|" separates plates)
    PLATES = [("PETG: " + grp, [(a.split(":")[0], int(a.split(":")[1])) for a in grp.split(",")])
              for grp in sys.argv[2].split("|")]


def main():
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK)
    lst = {"plates": [{"plate_name": title, "need_arrange": True,
                       "objects": [{"path": os.path.join(STL, part + ".stl"), "count": n, "filaments": [1]}
                                   for part, n in items]} for title, items in PLATES]}
    fn = os.path.join(WORK, "assemble_list.json")
    json.dump(lst, open(fn, "w"), indent=1)
    m, p, _, _ = profiles.build_presets("0.20", 4, "15%")
    proc = json.load(open(p, encoding="utf-8"))
    proc.update({"brim_type": "outer_only", "brim_width": "5", "brim_object_gap": "0.1"})
    json.dump(proc, open(p, "w", encoding="utf-8"), indent=1)
    fil = profiles.write_preset("filament", PETG)
    r = subprocess.run([EXE, "--load-settings", m + ";" + p, "--load-filaments", fil, "--load-assemble-list", fn,
                        "--allow-rotations", "--outputdir", WORK, "--export-3mf", "latch.3mf"],
                       capture_output=True, text=True)
    proj = os.path.join(WORK, "latch.3mf")
    if rc_of(r) != 0 or not os.path.exists(proj):
        raise RuntimeError("export failed: rc=%s\n%s" % (rc_of(r), r.stdout[-2000:]))
    from make_cereal_pla_test import solidify     # axle -> 100% infill (per-object setting)
    solidify(proj)
    for retry in range(3):
        try:
            hours = plate_hours(proj, len(PLATES), WORK)
            break
        except RuntimeError as e:
            if "timeout" not in str(e) or retry == 2:
                raise
    shutil.copy(proj, OUT_3MF)
    for i, (h, (title, _)) in enumerate(zip(hours, PLATES), 1):
        print("Plate %d  %.2f h  %s" % (i, h, title))
    print("Project:", OUT_3MF)


if __name__ == "__main__":
    main()
