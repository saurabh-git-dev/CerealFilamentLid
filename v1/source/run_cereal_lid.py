"""Headless runner: rebuilds the model and exports every STL to source/stl_cereal (and saves CerealLid.FCStd).
Run:  "C:\\Users\\SK\\AppData\\Local\\Programs\\FreeCAD 1.1\\bin\\freecadcmd.exe" run_cereal_lid.py
cereal_lid.py is executed in a fresh namespace so stale globals from an earlier run can't hide deleted constants."""
import os

HERE = r"C:\Users\SK\Desktop\Personal\CerealFilamentLid\v1\source"
ns = {"__name__": "cereal"}
exec(open(os.path.join(HERE, "cereal_lid.py"), encoding="utf-8").read(), ns)
