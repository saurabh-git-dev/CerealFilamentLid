"""
Small Bambu Studio project for the TPU outlet parts on the A1 mini, in eSUN TPU 95A clear:
  TPU_CapTether (cap + strap + anchor) and TPU_Grommet.
Filament: the "eSUN TPU 95A Clear @BBL A1M" user preset (Generic TPU @BBL A1M, 230/235 C, 3.0 mm3/s).
The CLI only accepts system presets, so the project is sliced with Generic TPU + the same overrides and then
re-pointed at the user preset.

Run:  python make_tpu_parts.py [out.3mf "Part:qty,Part:qty"]   (after cereal_lid.py exported ../stl_cereal)
"""
import json
import os
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import profiles  # noqa: E402
from make_project import EXE, rc_of, plate_hours  # noqa: E402
from make_cereal_pla_test import TPU, TPU_OVERRIDES, TPU_USER_PRESET  # noqa: E402

STL = os.path.join(os.path.dirname(HERE), "stl_cereal")
OUT_3MF = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else "TPU_OutletParts_eSUN_A1mini.3mf")
WORK = os.path.join(HERE, "work_tpu_parts")
ITEMS = [("TPU_CapTether", 1), ("TPU_Grommet", 1)]
if len(sys.argv) > 2:
    ITEMS = [(a.split(":")[0], int(a.split(":")[1])) for a in sys.argv[2].split(",")]


def main():
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK)
    lst = {"plates": [{"plate_name": "TPU outlet parts (eSUN 95A)", "need_arrange": True,
                       "objects": [{"path": os.path.join(STL, p + ".stl"), "count": n, "filaments": [1]}
                                   for p, n in ITEMS]}]}
    fn = os.path.join(WORK, "assemble_list.json")
    json.dump(lst, open(fn, "w"), indent=1)
    m, p, _, _ = profiles.build_presets("0.20", 4, "15%")
    fil = profiles.write_preset("filament", TPU, TPU_OVERRIDES)
    r = subprocess.run([EXE, "--load-settings", m + ";" + p, "--load-filaments", fil, "--load-assemble-list", fn,
                        "--allow-rotations", "--outputdir", WORK, "--export-3mf", "tpu.3mf"],
                       capture_output=True, text=True)
    proj = os.path.join(WORK, "tpu.3mf")
    if rc_of(r) != 0 or not os.path.exists(proj):
        raise RuntimeError("export failed: rc=%s\n%s" % (rc_of(r), r.stdout[-2000:]))
    for retry in range(3):
        try:
            hours = plate_hours(proj, 1, WORK)
            break
        except RuntimeError as e:
            if "timeout" not in str(e) or retry == 2:
                raise
    zin = zipfile.ZipFile(proj)
    ps = json.loads(zin.read("Metadata/project_settings.config"))
    ps["filament_settings_id"][0] = TPU_USER_PRESET
    with zipfile.ZipFile(OUT_3MF, "w", zipfile.ZIP_DEFLATED) as zo:
        for n in zin.namelist():
            zo.writestr(n, json.dumps(ps, indent=4) if n == "Metadata/project_settings.config" else zin.read(n))
    print("Plate 1  %.2f h  %s" % (hours[0], ", ".join("%s x%d" % i for i in ITEMS)))
    print("Project:", OUT_3MF)


if __name__ == "__main__":
    main()
