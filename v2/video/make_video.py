"""Encode video/frames (rendered by anim_v2.py) into MP4s with step captions.

  python make_video.py      -> CerealLid_v2_assembly_1080p.mp4, CerealLid_v2_assembly_1440p.mp4
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(HERE, "captions.json")))
fps, dur = cfg["fps"], cfg["duration"]
os.makedirs(os.path.join(HERE, "captions"), exist_ok=True)

FONT = "C\\:/Windows/Fonts/segoeui.ttf"
FONT_B = "C\\:/Windows/Fonts/segoeuib.ttf" if os.path.exists(r"C:\Windows\Fonts\segoeuib.ttf") else FONT


def chain(scale_h):
    k = scale_h / 1440
    fs, fy = int(46 * k), int(70 * k)
    parts = []
    for n, (t0, t1, text) in enumerate(cfg["captions"]):
        tf = "captions/c%02d.txt" % n
        with open(os.path.join(HERE, tf), "w", encoding="utf-8") as f:
            f.write(text)
        fade = "if(lt(t,%.2f),(t-%.2f)/0.35,if(gt(t,%.2f),(%.2f-t)/0.35,1))" % (t0 + 0.35, t0, t1 - 0.35, t1)
        last = n == len(cfg["captions"]) - 1
        parts.append(
            "drawtext=fontfile='%s':textfile=%s:fontsize=%d:fontcolor=0x1d2733:x=(w-text_w)/2:y=h-%d-text_h:"
            "box=1:boxcolor=0xffffff@0.82:boxborderw=%d:enable='between(t,%.2f,%.2f)':alpha='%s'"
            % (FONT_B if last else FONT, tf, int(fs * (1.5 if last else 1)), fy, int(22 * k), t0, t1, fade))
    return ("scale=-2:%d:flags=lanczos," % scale_h + ",".join(parts) +
            ",fade=t=in:st=0:d=0.6,fade=t=out:st=%.2f:d=0.8,format=yuv420p" % (dur - 0.8))


for h, name in ((1080, "CerealLid_v2_assembly_1080p.mp4"), (1440, "CerealLid_v2_assembly_1440p.mp4")):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(fps), "-i", "frames/f_%05d.png",
           "-vf", chain(h), "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-profile:v", "high",
           "-movflags", "+faststart", name]
    subprocess.run(cmd, cwd=HERE, check=True)
    print("wrote", os.path.join(HERE, name), round(os.path.getsize(os.path.join(HERE, name)) / 1e6, 1), "MB")
