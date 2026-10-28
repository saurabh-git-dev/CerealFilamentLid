import os, subprocess, json, sys
EXE = r"C:\Program Files\Bambu Studio\bambu-studio.exe"
def check(path, od):
    r = subprocess.run([EXE, "--slice", "0", "--outputdir", od, path], capture_output=True, text=True)
    rc = r.returncode - 2**32 if r.returncode > 2**31 else r.returncode
    rj = os.path.join(od, "result.json")
    res = json.load(open(rj)) if os.path.exists(rj) else {}
    pls = res.get("sliced_plates", [])
    print(os.path.basename(path), "rc", rc, res.get("error_string"), len(pls), [round(p["main_predication"] / 3600, 2) for p in pls], flush=True)
    for p in pls:
        if p.get("warning_message"):
            print("   warn plate", p["id"], p["warning_message"][:200], flush=True)
    return rc, res
if __name__ == "__main__":
    check(sys.argv[1], sys.argv[2])
