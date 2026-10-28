"""
Build ONE Bambu Studio project (.3mf) for the acrylic dry box on the A1 mini:
  - complete PETG + TPU presets (see profiles.py), Textured PEI plate
  - parts grouped into plates (one filament per plate, no AMS needed)
  - each plate's print time predicted by the bambu-studio CLI; plates over MAX_HOURS are split
  - output: DryBox_Acrylic_A1mini.3mf (PETG = filament 1, TPU = filament 2) + plates_summary.txt

Why the detour: the CLI crashes when one assemble list uses two filaments and cannot slice
two-filament A1 mini projects, so PETG and TPU plates are exported separately (each sliceable on its
own for timing) and then merged with merge3mf.py.

Run:  python make_project.py
"""
import json
import os
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import merge3mf  # noqa: E402
import profiles  # noqa: E402

EXE = r"C:\Program Files\Bambu Studio\bambu-studio.exe"
STL = os.path.join(os.path.dirname(HERE), "stl_acrylic")
OUT_3MF = os.path.join(HERE, "DryBox_Acrylic_A1mini.3mf")
WORK = os.path.join(HERE, "work")
MAX_HOURS = 5.0
LAYER, WALLS, INFILL = "0.20", 3, "15%"

# Plate plan per filament: (plate title, [(part, count), ...])
PLAN = {
    "PETG": [
        ("Box lower L", [("Box_LowerL", 1)]),
        ("Box lower R", [("Box_LowerR", 1)]),
        ("Box upper L", [("Box_UpperL", 1)]),
        ("Box upper R", [("Box_UpperR", 1)]),
        ("Lid L", [("Lid_L", 1)]),
        ("Lid R", [("Lid_R", 1)]),
        ("Silica plate L + cradle L", [("SilicaPlate_L", 1), ("Cradle_L", 1)]),
        ("Silica plate R + cradle R", [("SilicaPlate_R", 1), ("Cradle_R", 1)]),
        ("Rollers + clasps + panel clamps", [("Roller", 2), ("Clasp", 4), ("PanelClamp", None)]),
    ],
    "TPU": [
        ("Seam gasket lower vertical", [("TPU_SeamGasket_LowerVertical", 1)]),
        ("Seam gasket upper vertical + small seals",
         [("TPU_SeamGasket_UpperVertical", 1), ("TPU_HygroSleeve", 1), ("TPU_OutletCap_Tethered", 1)]),
        ("Front sheet gasket + lid seam gasket", [("TPU_SheetGasket_Front", 1), ("TPU_SeamGasket_Lid", 1)]),
        ("Seam gasket middle L", [("TPU_SeamGasket_MiddleL", 1)]),
        ("Seam gasket middle R", [("TPU_SeamGasket_MiddleR", 1)]),
        ("Lid gasket L", [("TPU_LidGasket_L", 1)]),
        ("Lid gasket R", [("TPU_LidGasket_R", 1)]),
    ],
}


# counts of None come from stl_acrylic/parts.json (written by drybox_acrylic.py). The cereal-lid scripts only
# import the helpers below, so the dry-box plan is skipped when that file isn't here.
if os.path.exists(os.path.join(STL, "parts.json")):
    _COUNTS = {d["name"]: d["count"] for d in json.load(open(os.path.join(STL, "parts.json")))}
    PLAN = {fil: [(t, [(p, n if n is not None else _COUNTS[p]) for p, n in items]) for t, items in plates]
            for fil, plates in PLAN.items()}


def rc_of(r):
    return r.returncode - 2 ** 32 if r.returncode > 2 ** 31 else r.returncode


def export(fil, plan, outdir, both_filaments):
    """Unsliced single-filament project for one filament's plates."""
    os.makedirs(outdir, exist_ok=True)
    lst = {"plates": [{"plate_name": "%s - %s" % (fil, title), "need_arrange": True,
                       "objects": [{"path": os.path.join(STL, part + ".stl"), "count": n, "filaments": [1]}
                                   for part, n in items]} for title, items in plan]}
    fn = os.path.join(outdir, "assemble_list.json")
    json.dump(lst, open(fn, "w"), indent=1)
    m, p, petg, tpu = profiles.build_presets(LAYER, WALLS, INFILL)
    fils = (petg + ";" + tpu) if both_filaments else (petg if fil == "PETG" else tpu)
    name = fil + ".3mf"
    r = subprocess.run([EXE, "--load-settings", m + ";" + p, "--load-filaments", fils, "--load-assemble-list", fn,
                        "--allow-rotations", "--outputdir", outdir, "--export-3mf", name],
                       capture_output=True, text=True)
    path = os.path.join(outdir, name)
    if rc_of(r) != 0 or not os.path.exists(path):
        raise RuntimeError("export of %s plates failed: rc=%s" % (fil, rc_of(r)))
    return path


def plate_hours(project, n_plates, outdir):
    """Slice each plate on its own (slicing all plates in one call can hang) -> [hours]."""
    hours = []
    for n in range(1, n_plates + 1):
        od = os.path.join(outdir, "plate_%d" % n)
        try:
            r = subprocess.run([EXE, "--slice", str(n), "--outputdir", od, project],
                               capture_output=True, text=True, timeout=300)
            rc = rc_of(r)
        except subprocess.TimeoutExpired:
            rc = "timeout"
        rj = os.path.join(od, "result.json")
        res = json.load(open(rj)) if os.path.exists(rj) else {}
        pl = res.get("sliced_plates") or []
        if rc != 0 or not pl:
            raise RuntimeError("slicing plate %d of %s failed: rc=%s %s" % (n, project, rc, res.get("error_string")))
        hours.append(pl[0]["main_predication"] / 3600)
    return hours


def split(entry):
    title, items = entry
    inst = [part for part, n in items for _ in range(n)]
    if len(inst) < 2:
        raise RuntimeError("Plate '%s' is a single part over %.1f h - lower layer height or walls" % (title, MAX_HOURS))
    out = []
    for suffix, half in ((" (a)", inst[: len(inst) // 2]), (" (b)", inst[len(inst) // 2:])):
        grouped = []
        for part in half:
            if grouped and grouped[-1][0] == part:
                grouped[-1] = (part, grouped[-1][1] + 1)
            else:
                grouped.append((part, 1))
        out.append((title + suffix, grouped))
    return out


def timed_plan(fil):
    plan = list(PLAN[fil])
    for attempt in range(6):
        d = os.path.join(WORK, "%s_try%d" % (fil, attempt))
        shutil.rmtree(d, ignore_errors=True)
        proj = export(fil, plan, d, both_filaments=False)
        hours = plate_hours(proj, len(plan), d)
        over = [i for i, h in enumerate(hours) if h > MAX_HOURS]
        if not over:
            return plan, hours
        print("%s: splitting %s" % (fil, [plan[i][0] for i in over]))
        plan = [e for i, p in enumerate(plan) for e in (split(p) if i in over else [p])]
    raise RuntimeError("could not get %s plates under %.1f h" % (fil, MAX_HOURS))


def main():
    petg_plan, petg_h = timed_plan("PETG")
    tpu_plan, tpu_h = timed_plan("TPU")

    # final: PETG project carrying both filament presets + TPU project -> one file
    d = os.path.join(WORK, "final")
    shutil.rmtree(d, ignore_errors=True)
    base = export("PETG", petg_plan, os.path.join(d, "petg"), both_filaments=True)
    add = export("TPU", tpu_plan, os.path.join(d, "tpu"), both_filaments=False)
    fkeys = set(profiles.resolve("filament", profiles.TPU_BASE)) | set(profiles.resolve("filament", profiles.PETG_BASE))
    merged = os.path.join(d, "merged.3mf")
    merge3mf.merge(base, add, merged, fkeys, add_extruder=2)
    # one filament per plate: no prime tower needed
    zin = zipfile.ZipFile(merged)
    ps = json.loads(zin.read("Metadata/project_settings.config"))
    ps["enable_prime_tower"] = "0"
    if os.path.exists(OUT_3MF):
        os.remove(OUT_3MF)
    with zipfile.ZipFile(OUT_3MF, "w", zipfile.ZIP_DEFLATED) as zo:
        for n in zin.namelist():
            zo.writestr(n, json.dumps(ps, indent=4) if n == "Metadata/project_settings.config" else zin.read(n))

    rows = [("PETG", t, items, h) for (t, items), h in zip(petg_plan, petg_h)] + \
           [("TPU", t, items, h) for (t, items), h in zip(tpu_plan, tpu_h)]
    lines = ["DryBox (acrylic variant) - Bambu Lab A1 mini, 0.4 nozzle, Textured PEI plate",
             "Process: %s mm layers, %d walls, %s gyroid infill, 5 top / 4 bottom layers" % (LAYER, WALLS, INFILL),
             "Filament 1: Bambu PETG HF @BBL A1M (times assume HF flow; other PETG profiles print slower)",
             "Filament 2: Bambu TPU 95A @BBL A1M (feed from the external spool, not the AMS lite)", ""]
    for i, (fil, title, items, h) in enumerate(rows, 1):
        lines.append("Plate %2d  %-4s  %5.2f h  %-42s %s" % (i, fil, h, title,
                     ", ".join("%s x%d" % (p, n) if n > 1 else p for p, n in items)))
    lines += ["", "Total: %.1f h over %d plates (limit %.1f h per plate)" % (sum(r[3] for r in rows), len(rows), MAX_HOURS)]
    open(os.path.join(HERE, "plates_summary.txt"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("\nProject:", OUT_3MF, "%.1f MB" % (os.path.getsize(OUT_3MF) / 1e6))


if __name__ == "__main__":
    main()
