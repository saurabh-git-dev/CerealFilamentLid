"""Build the v2 Bambu Studio projects from ../stl_cereal (run export_v2.py first) into ../print.

  CerealLid_v2_PETG_A1mini.3mf   Bambu PETG Basic, 6 plates (lid L, lid R, hangers + stub axles + retainers +
                                 clips + hygrometer cradle, hub halves + latches, silica boxes, covers + bolts + handle)
  CerealLid_v2_TPU_eSUN_A1mini.3mf   eSUN TPU 95A: seam strip, grommet, tethered cap

Run:  python make_v2_projects.py
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRINT = os.path.join(os.path.dirname(HERE), "print")
PETG = ("Lid_L:1|Lid_R:1|Hanger_A:1,Hanger_B:1,StubAxle_x2:2,HubRetainer_x2:2,StubClip_x2:4,HygroCradle_Mini:1|"
        "HubHalf_A:1,HubHalf_B:1,Latch_x4:4|"
        "SilicaBox_L:1,SilicaBox_R:1|SilicaBoxCover_L:1,SilicaBoxCover_R:1,SilicaLockBolt_x6:6,SilicaBoxHandle_v2:1")
TPU = "TPU_SeamStrip:1,TPU_Grommet:1,TPU_CapTether:1"


def run(script, out, items):
    r = subprocess.run([sys.executable, os.path.join(HERE, script), out, items], cwd=HERE)
    if r.returncode:
        sys.exit(r.returncode)
    os.makedirs(PRINT, exist_ok=True)
    shutil.move(os.path.join(HERE, out), os.path.join(PRINT, out))


run("make_latch_trial_petg.py", "CerealLid_v2_PETG_A1mini.3mf", PETG)
run("make_tpu_parts.py", "CerealLid_v2_TPU_eSUN_A1mini.3mf", TPU)
for w in ("work_latch_trial", "work_tpu_parts", "__pycache__"):
    shutil.rmtree(os.path.join(HERE, w), ignore_errors=True)
print("projects in", PRINT)
