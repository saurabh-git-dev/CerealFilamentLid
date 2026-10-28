"""
Bambu Studio project (.3mf) for TEST-FIT prints of the cereal-box lid on the A1 mini:
rigid parts in Generic PLA (filament 1), seals in TPU 95A (filament 2, one filament per plate).
PLA is only for checking fit; the final rigid parts are printed in PETG.

  - Generic PLA @BBL A1M, 0.20 mm layers, Textured PEI plate (presets flattened by profiles.py)
  - plate 1 = the quick fit tests; print and check it before the rest
  - every plate's time comes from slicing it with the bambu-studio CLI; plates over MAX_HOURS are split
  - axle and pins get 100% infill (per-object setting)
  - PLA and TPU plates are exported separately (the CLI can't do two filaments in one assemble list)
    and merged with merge3mf.py, as in make_project.py
  - output: CerealLid_PLA_test_A1mini.3mf + cereal_pla_plates.txt

Run:  python make_cereal_pla_test.py          PLA test-fit project
      python make_cereal_pla_test.py final    FINAL project: every current part, Bambu PETG Basic + eSUN TPU
(after cereal_lid.py has exported ../stl_cereal)
"""
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merge3mf  # noqa: E402
import profiles  # noqa: E402
from make_project import EXE, rc_of, plate_hours, split  # noqa: E402
import make_project  # noqa: E402

STL = os.path.join(os.path.dirname(HERE), "stl_cereal")
OUT_3MF = os.path.join(HERE, "CerealLid_PLA_test_A1mini.3mf")
WORK = os.path.join(HERE, "work_cereal_pla")
MAX_HOURS = 5.0
LAYER, WALLS, INFILL = "0.20", 4, "15%"
PLA = "Generic PLA @BBL A1M"
# eSUN TPU 95A (clear): Bambu Studio has no eSUN TPU preset -> Generic TPU tuned for it
TPU = "Generic TPU @BBL A1M"
TPU_OVERRIDES = {"nozzle_temperature": ["230"], "nozzle_temperature_initial_layer": ["235"],
                 "filament_max_volumetric_speed": ["3.0"], "filament_vendor": ["eSUN"]}
TPU_LABEL = "eSUN TPU 95A clear (Generic TPU @BBL A1M, 230/235 C, 3.0 mm3/s)"
# user preset of the same name lives in %APPDATA%/BambuStudio/user/default/filament (inherits Generic TPU);
# the CLI only takes system presets, so the project is re-pointed at it after the merge
TPU_USER_PRESET = "eSUN TPU 95A Clear @BBL A1M"
SOLID = ("Axle_8mm_x88", "Axle_8mm_x88_Grip", "Axle_8mm_x88_SpringStops")                     # printed 100% infill

TPU_PLAN = [
    ("TPU - Lid gasket L + outlet grommet + cap", [("TPU_Gasket_L", 1), ("TPU_Grommet", 1), ("TPU_CapTether", 1)]),
    ("TPU - Lid gasket R + seam strip", [("TPU_Gasket_R", 1), ("TPU_SeamStrip", 1)]),
]

PLAN = [
    ("Fit tests (print first)", [("Test_Corner", 1), ("Test_LatchSection", 1), ("Latch_x4", 1)]),
    ("Lid L", [("Lid_L", 1)]),
    ("Lid R", [("Lid_R", 1)]),
    ("Hangers (mirrored pair) + necked axle", [("Hanger_A", 1), ("Hanger_B", 1), ("Axle_8mm_x88", 1)]),
    ("Hub adapters + latches", [("HubAdapter_x2", 2), ("Latch_x4", 4)]),
    ("Hygrometer cradle + silica lock bolts + box handle", [("HygroCradle_Mini", 1), ("SilicaLockBolt_x6", 6), ("SilicaBoxHandle", 1)]),
    ("Silica boxes", [("SilicaBox_L", 1), ("SilicaBox_R", 1)]),
    ("Silica sliding covers", [("SilicaBoxCover_L", 1), ("SilicaBoxCover_R", 1)]),
]
FINAL = len(sys.argv) > 1 and sys.argv[1] == "final"
if FINAL:                                   # everything for real, in PETG (the fit tests are not needed any more)
    PLA = "Bambu PETG Basic @BBL A1M 0.4 nozzle"
    OUT_3MF = os.path.join(HERE, "CerealLid_FINAL_PETG_A1mini.3mf")
    WORK = os.path.join(HERE, "work_cereal_final")
    PLAN = PLAN[1:]


def export(plan, outdir, fil="PLA", both=False):
    os.makedirs(outdir, exist_ok=True)
    lst = {"plates": [{"plate_name": title, "need_arrange": True,
                       "objects": [{"path": os.path.join(STL, part + ".stl"), "count": n, "filaments": [1]}
                                   for part, n in items]} for title, items in plan]}
    fn = os.path.join(outdir, "assemble_list.json")
    json.dump(lst, open(fn, "w"), indent=1)
    m, p, _, _ = profiles.build_presets(LAYER, WALLS, INFILL)
    if fil == "PLA":                                      # 5 mm brim on the PLA parts (tall / narrow ones lifted);
        proc = json.load(open(p, encoding="utf-8"))       # TPU sticks well and its brim stalls the CLI slicer
        proc.update({"brim_type": "outer_only", "brim_width": "5", "brim_object_gap": "0.1"})
        json.dump(proc, open(p, "w", encoding="utf-8"), indent=1)
    pla = profiles.write_preset("filament", PLA)
    tpu = profiles.write_preset("filament", TPU, TPU_OVERRIDES)
    fils = pla + ";" + tpu if both else (pla if fil == "PLA" else tpu)
    name = fil.lower() + ".3mf"
    r = subprocess.run([EXE, "--load-settings", m + ";" + p, "--load-filaments", fils, "--load-assemble-list", fn,
                        "--allow-rotations", "--outputdir", outdir, "--export-3mf", name],
                       capture_output=True, text=True)
    path = os.path.join(outdir, name)
    if rc_of(r) != 0 or not os.path.exists(path):
        raise RuntimeError("export failed: rc=%s\n%s" % (rc_of(r), r.stdout[-2000:]))
    return solidify(path)


def solidify(path):
    """Per-object 100% infill for the axle and pins (object-level metadata in model_settings.config)."""
    tmp = path + ".tmp"
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zo:
        for n in zin.namelist():
            data = zin.read(n)
            if n == "Metadata/model_settings.config":
                s = data.decode("utf-8")

                def add(mo):
                    block = mo.group(0)
                    src = re.search(r'key="source_file" value="([^"]+)\.stl"', block)
                    if src and src.group(1) in SOLID:
                        block = block.replace('<metadata key="extruder" value="1"/>',
                                              '<metadata key="extruder" value="1"/>\n'
                                              '    <metadata key="sparse_infill_density" value="100%"/>', 1)
                    return block
                data = re.sub(r"<object id=.*?</object>", add, s, flags=re.S).encode("utf-8")
            zo.writestr(n, data)
    os.replace(tmp, path)
    return path


def timed(fil, plan):
    for attempt in range(6):
        d = os.path.join(WORK, "%s_try%d" % (fil, attempt))
        shutil.rmtree(d, ignore_errors=True)
        proj = export(plan, d, fil)
        for retry in range(3):                            # the CLI slicer hangs now and then: retry
            try:
                hours = plate_hours(proj, len(plan), d)
                break
            except RuntimeError as e:
                if "timeout" not in str(e) or retry == 2:
                    raise
                print("slicer timed out, retrying:", e)
        over = [i for i, h in enumerate(hours) if h > MAX_HOURS]
        if not over:
            return plan, hours
        print("splitting", [plan[i][0] for i in over])
        plan = [e for i, p in enumerate(plan) for e in (split(p) if i in over else [p])]
    raise RuntimeError("could not get %s plates under %.1f h" % (fil, MAX_HOURS))


def main():
    make_project.MAX_HOURS = MAX_HOURS
    plan, hours = timed("PLA", list(PLAN))
    tplan, thours = timed("TPU", list(TPU_PLAN))

    d = os.path.join(WORK, "final")
    shutil.rmtree(d, ignore_errors=True)
    base = export(plan, os.path.join(d, "pla"), "PLA", both=True)
    add = export(tplan, os.path.join(d, "tpu"), "TPU")
    fkeys = set(profiles.resolve("filament", TPU)) | set(profiles.resolve("filament", PLA))
    merged = os.path.join(d, "merged.3mf")
    merge3mf.merge(base, add, merged, fkeys, add_extruder=2)
    zin = zipfile.ZipFile(merged)
    ps = json.loads(zin.read("Metadata/project_settings.config"))
    ps["enable_prime_tower"] = "0"                 # one filament per plate
    ps["filament_settings_id"][1] = TPU_USER_PRESET
    if os.path.exists(OUT_3MF):
        os.remove(OUT_3MF)
    with zipfile.ZipFile(OUT_3MF, "w", zipfile.ZIP_DEFLATED) as zo:
        for n in zin.namelist():
            zo.writestr(n, json.dumps(ps, indent=4) if n == "Metadata/project_settings.config" else zin.read(n))
    plan, hours = plan + tplan, hours + thours

    lines = ["Cereal-box lid %s - Bambu Lab A1 mini, 0.4 nozzle, Textured PEI plate" % ("FINAL" if FINAL else "TEST FIT"),
             "%s mm layers, %d walls, %s gyroid (axle 100%%), 5 mm brim" % (LAYER, WALLS, INFILL),
             "Filament 1: %s (rigid parts) | Filament 2: %s (seals - feed from the external spool, not the AMS lite)"
             % (PLA, TPU_LABEL), ""]
    for i, ((title, items), h) in enumerate(zip(plan, hours), 1):
        lines.append("Plate %d  %5.2f h  %-36s %s" % (i, h, title,
                     ", ".join("%s x%d" % (p, n) if n > 1 else p for p, n in items)))
    lines += ["", "Total: %.1f h over %d plates" % (sum(hours), len(plan))]
    open(os.path.join(HERE, "cereal_final_plates.txt" if FINAL else "cereal_pla_plates.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("\nProject:", OUT_3MF, "%.1f MB" % (os.path.getsize(OUT_3MF) / 1e6))


if __name__ == "__main__":
    main()
