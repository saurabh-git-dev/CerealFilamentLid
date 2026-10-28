"""
Merge a single-filament Bambu Studio project (TPU plates) into another project (PETG plates,
exported with both filaments loaded) -> one multi-plate project, TPU objects on filament 2.

Needed because the bambu-studio CLI crashes when an assemble list assigns objects to filament 2.
String-level edits only, so Bambu's own XML formatting / namespace prefixes are preserved.
"""
import json
import math
import re
import uuid
import zipfile

STRIDE = 180 * 1.2          # Bambu plate pitch on the virtual bed: plate width * (1 + 1/5)
OID, SID, FIDX, IDENT = 1000, 1000, 100, 100000


def cols_for(n):
    v = math.sqrt(n)
    r = round(v)
    return int(r + 1 if v > r else r)


def plate_origin(i, cols):                       # i: 0-based plate index
    return (i % cols) * STRIDE, -(i // cols) * STRIDE


def plate_of_objects(model_settings):
    """object_id -> 0-based plate index, from <plate> blocks."""
    out = {}
    for m in re.finditer(r"<plate>(.*?)</plate>", model_settings, re.S):
        pid = int(re.search(r'key="plater_id" value="(\d+)"', m.group(1)).group(1)) - 1
        for oid in re.findall(r'key="object_id" value="(\d+)"', m.group(1)):
            out[int(oid)] = pid
    return out


def move_items(model_xml, obj_plate, old_cols, new_cols, plate_offset=0, id_offset=0):
    """Re-anchor build items to the new plate grid (and optionally renumber)."""
    def fix(m):
        oid = int(m.group(1))
        t = [float(x) for x in m.group(3).split()]
        p_old = obj_plate[oid]
        ox, oy = plate_origin(p_old, old_cols)
        nx, ny = plate_origin(p_old + plate_offset, new_cols)
        t[9] = t[9] - ox + nx
        t[10] = t[10] - oy + ny
        uid = str(uuid.uuid4()) if id_offset else m.group(2)
        return '<item objectid="%d" p:UUID="%s" transform="%s"' % (
            oid + id_offset, uid, " ".join(repr(round(x, 6)) for x in t))
    return re.sub(r'<item objectid="(\d+)" p:UUID="([^"]+)" transform="([^"]+)"', fix, model_xml)


def new_uuids(s):
    return re.sub(r'p:UUID="[^"]+"', lambda m: 'p:UUID="%s"' % uuid.uuid4(), s)


def merge(base_path, add_path, out_path, filament_keys, add_extruder=2, add_colour="#F2F2F2"):
    """filament_keys: keys of a filament preset - only these are per-filament arrays to extend
    (per-extruder printer keys such as nozzle_diameter must stay single-valued)."""
    zb, za = zipfile.ZipFile(base_path), zipfile.ZipFile(add_path)
    rb = lambda n: zb.read(n).decode("utf-8")
    ra = lambda n: za.read(n).decode("utf-8")

    ms_b, ms_a = rb("Metadata/model_settings.config"), ra("Metadata/model_settings.config")
    nb = len(re.findall(r"<plate>", ms_b))
    na = len(re.findall(r"<plate>", ms_a))
    cols_b, cols_a, cols_n = cols_for(nb), cols_for(na), cols_for(nb + na)

    # ---- 3D/3dmodel.model
    mb, ma = rb("3D/3dmodel.model"), ra("3D/3dmodel.model")
    mb = move_items(mb, plate_of_objects(ms_b), cols_b, cols_n)
    res_a = ma[ma.index("<resources>") + len("<resources>"):ma.index("</resources>")]
    res_a = re.sub(r'<object id="(\d+)"', lambda m: '<object id="%d"' % (int(m.group(1)) + OID), res_a)
    res_a = re.sub(r'objectid="(\d+)"', lambda m: 'objectid="%d"' % (int(m.group(1)) + SID), res_a)
    res_a = re.sub(r'/3D/Objects/object_(\d+)\.model', lambda m: "/3D/Objects/object_%d.model" % (int(m.group(1)) + FIDX), res_a)
    res_a = new_uuids(res_a)
    mb = mb.replace("</resources>", res_a + "</resources>", 1)
    build_a = ma[ma.index("<build"):ma.index("</build>")]
    build_a = build_a[build_a.index(">") + 1:]
    build_a = move_items(build_a, plate_of_objects(ms_a), cols_a, cols_n, plate_offset=nb, id_offset=OID)
    mb = mb.replace("</build>", build_a + "</build>", 1)

    # ---- rels
    rels = rb("3D/_rels/3dmodel.model.rels")
    add_rels = ""
    for n in za.namelist():
        m = re.match(r"3D/Objects/object_(\d+)\.model$", n)
        if m:
            k = int(m.group(1)) + FIDX
            add_rels += ' <Relationship Target="/3D/Objects/object_%d.model" Id="rel-%d" ' \
                        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n' % (k, k)
    rels = rels.replace("</Relationships>", add_rels + "</Relationships>")

    # ---- model_settings.config
    objs_a = re.findall(r"  <object id=.*?</object>\n", ms_a, re.S)
    plates_a = re.findall(r"  <plate>.*?</plate>\n", ms_a, re.S)
    add_objs = ""
    for o in objs_a:
        o = re.sub(r'<object id="(\d+)"', lambda m: '<object id="%d"' % (int(m.group(1)) + OID), o)
        o = re.sub(r'<part id="(\d+)"', lambda m: '<part id="%d"' % (int(m.group(1)) + SID), o)
        o = re.sub(r'(<object id="\d+">\s*<metadata key="name" value="[^"]*"/>\s*<metadata key="extruder" value=")\d+',
                   lambda m: m.group(1) + str(add_extruder), o)
        add_objs += o
    add_plates = ""
    for p in plates_a:
        p = re.sub(r'key="plater_id" value="(\d+)"', lambda m: 'key="plater_id" value="%d"' % (int(m.group(1)) + nb), p)
        p = re.sub(r'key="object_id" value="(\d+)"', lambda m: 'key="object_id" value="%d"' % (int(m.group(1)) + OID), p)
        p = re.sub(r'key="identify_id" value="(\d+)"', lambda m: 'key="identify_id" value="%d"' % (int(m.group(1)) + IDENT), p)
        p = re.sub(r'(plate|plate_no_light|top|pick)_(\d+)(_small)?\.png',
                   lambda m: "%s_%d%s.png" % (m.group(1), int(m.group(2)) + nb, m.group(3) or ""), p)
        add_plates += p
    first_plate = ms_b.index("  <plate>")
    ms_b = ms_b[:first_plate] + add_objs + ms_b[first_plate:]
    ms_b = ms_b.replace("  <assemble>", add_plates + "  <assemble>", 1)

    # ---- project_settings.config: fill the 2nd filament's values where the base has only one
    ps_b = json.loads(rb("Metadata/project_settings.config"))
    ps_a = json.loads(ra("Metadata/project_settings.config"))
    n_fil = len(ps_b["filament_settings_id"])
    for k, v in ps_b.items():
        if k in filament_keys and isinstance(v, list) and len(v) == n_fil - 1 \
                and isinstance(ps_a.get(k), list) and len(ps_a[k]) == 1:
            ps_b[k] = v + ps_a[k]
    # per-filament lists the CLI leaves single-valued: all must have one entry per filament
    for k, v in ps_b.items():
        if isinstance(v, list) and len(v) == n_fil - 1 and (
                k.startswith("filament_") or k in ("default_filament_colour", "pre_start_fan_time")):
            extra = ps_a[k][0] if isinstance(ps_a.get(k), list) and len(ps_a[k]) == 1 else v[0]
            ps_b[k] = v + [extra]
    ps_b["filament_colour"] = (ps_b.get("filament_colour") or ["#00AE42"])[:1] + [add_colour]
    ps_b["filament_map"] = ["1"] * n_fil

    # ---- small bookkeeping files
    seq = json.loads(rb("Metadata/filament_sequence.json"))
    for k, v in json.loads(ra("Metadata/filament_sequence.json")).items():
        seq["plate_%d" % (int(k.split("_")[1]) + nb)] = v
    cut = rb("Metadata/cut_information.xml")
    n_obj_b = len(re.findall(r"<object id=", cut))
    n_obj_a = len(re.findall(r"<object id=", ra("Metadata/cut_information.xml")))
    extra = "".join(' <object id="%d">\n  <cut_id id="0" check_sum="1" connectors_cnt="0"/>\n </object>\n' % (n_obj_b + i + 1)
                    for i in range(n_obj_a))
    cut = cut.replace("</objects>", extra + "</objects>")

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zo:
        for n in zb.namelist():
            if n == "3D/3dmodel.model":
                zo.writestr(n, mb)
            elif n == "3D/_rels/3dmodel.model.rels":
                zo.writestr(n, rels)
            elif n == "Metadata/model_settings.config":
                zo.writestr(n, ms_b)
            elif n == "Metadata/project_settings.config":
                zo.writestr(n, json.dumps(ps_b, indent=4))
            elif n == "Metadata/filament_sequence.json":
                zo.writestr(n, json.dumps(seq))
            elif n == "Metadata/cut_information.xml":
                zo.writestr(n, cut)
            else:
                zo.writestr(n, zb.read(n))
        for n in za.namelist():
            m = re.match(r"3D/Objects/object_(\d+)\.model$", n)
            if m:
                s = ra(n)
                s = re.sub(r'<object id="(\d+)"', lambda mm: '<object id="%d"' % (int(mm.group(1)) + SID), s)
                zo.writestr("3D/Objects/object_%d.model" % (int(m.group(1)) + FIDX), new_uuids(s))
                continue
            m = re.match(r"Metadata/(plate|plate_no_light|top|pick)_(\d+)(_small)?\.png$", n)
            if m:
                zo.writestr("Metadata/%s_%d%s.png" % (m.group(1), int(m.group(2)) + nb, m.group(3) or ""), za.read(n))
    return nb, na
