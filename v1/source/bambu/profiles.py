"""
Resolve Bambu Studio system profiles (inherits / include chains) into self-contained JSON files
that the bambu-studio CLI applies fully, and write the dry box's custom process/filament presets.
"""
import json
import os

BBL = r"C:\Program Files\Bambu Studio\resources\profiles\BBL"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles")

_index = {}


def _load_index():
    if _index:
        return
    for sub in ("machine", "process", "filament"):
        for root, _, files in os.walk(os.path.join(BBL, sub)):
            for f in files:
                if f.endswith(".json"):
                    try:
                        d = json.load(open(os.path.join(root, f), encoding="utf-8"))
                    except Exception:
                        continue
                    if "name" in d:
                        _index[(sub, d["name"])] = d


def resolve(kind, name):
    """Merge a system preset with all of its parents and includes."""
    _load_index()
    d = _index[(kind, name)]
    merged = {}
    if d.get("inherits"):
        merged.update(resolve(kind, d["inherits"]))
    for inc in d.get("include", []):
        merged.update({k: v for k, v in resolve(kind, inc).items() if k not in ("name", "type")})
    merged.update({k: v for k, v in d.items() if k not in ("inherits", "include")})
    return merged


def write_preset(kind, base, overrides=None):
    """Flattened copy of a system preset. It keeps the system name and "from": "system" -
    the CLI only accepts presets it can match to the printer, and it does not resolve inherits."""
    d = resolve(kind, base)
    d.update(overrides or {})
    d.update({"name": base, "from": "system", "instantiation": "true", "type": kind})
    d.pop("inherits", None)
    os.makedirs(OUT, exist_ok=True)
    fn = os.path.join(OUT, kind + "_" + base.replace(" ", "_").replace("@", "") + ".json")
    json.dump(d, open(fn, "w", encoding="utf-8"), indent=1)
    return fn


MACHINE = "Bambu Lab A1 mini 0.4 nozzle"
PETG_BASE = "Bambu PETG HF @BBL A1M"
TPU_BASE = "Bambu TPU 95A @BBL A1M"     # regular 95A (works for non-HF TPU too)


def build_presets(layer="0.24", walls=3, infill="15%"):
    base = {"0.20": "0.20mm Standard @BBL A1M", "0.24": "0.24mm Draft @BBL A1M",
            "0.28": "0.28mm Extra Draft @BBL A1M"}[layer]
    machine = write_preset("machine", MACHINE)
    process = write_preset("process", base, {
        "wall_loops": str(walls),
        "top_shell_layers": "5",
        "bottom_shell_layers": "4",
        "sparse_infill_density": infill,
        "sparse_infill_pattern": "gyroid",
        "seam_position": "back",
        "enable_support": "0",
        "brim_type": "auto_brim",
        "curr_bed_type": "Textured PEI Plate",   # PETG/TPU: textured PEI (PETG has no cool-plate temp)
    })
    petg = write_preset("filament", PETG_BASE)
    tpu = write_preset("filament", TPU_BASE)
    return machine, process, petg, tpu


if __name__ == "__main__":
    for f in build_presets():
        d = json.load(open(f, encoding="utf-8"))
        print(os.path.basename(f), len(d), "keys", d.get("layer_height"), d.get("wall_loops"),
              d.get("filament_max_volumetric_speed"))
