"""Crop + caption the frames from make_spool_animation.py and encode renders/spool_change.mp4 (and a GIF)."""
import os
import subprocess
import sys
from PIL import Image, ImageChops, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = sys.argv[1] if len(sys.argv) > 1 else "anim"          # frames folder under renders/
OUTNAME = sys.argv[2] if len(sys.argv) > 2 else "spool_change"
SRC = os.path.join(HERE, "renders", NAME)
DST = os.path.join(SRC, "final")
FFMPEG = r"C:\ffmpeg-8.0-essentials_build\bin\ffmpeg.exe"
W, H, BAR = 1280, 720, 70

frames = sorted(f for f in os.listdir(SRC) if f.startswith("frame_") and f.endswith(".png"))
captions = open(os.path.join(SRC, "captions.txt")).read().split("\n")
# union of the non-white area over all frames -> one fixed crop
box = None
for f in frames:
    im = Image.open(os.path.join(SRC, f)).convert("RGB")
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    if bb:
        box = bb if box is None else (min(box[0], bb[0]), min(box[1], bb[1]), max(box[2], bb[2]), max(box[3], bb[3]))
m = 20
box = (max(box[0] - m, 0), max(box[1] - m, 0), box[2] + m, box[3] + m)
try:
    font = ImageFont.truetype("arialbd.ttf", 30)
    small = ImageFont.truetype("arial.ttf", 20)
except OSError:
    font = small = ImageFont.load_default()
os.makedirs(DST, exist_ok=True)
for f in os.listdir(DST):
    os.remove(os.path.join(DST, f))
for i, (f, cap) in enumerate(zip(frames, captions)):
    im = Image.open(os.path.join(SRC, f)).convert("RGB").crop(box)
    s = min(W / im.width, (H - BAR) / im.height)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    out = Image.new("RGB", (W, H), (255, 255, 255))
    out.paste(im, ((W - im.width) // 2, BAR + (H - BAR - im.height) // 2))
    d = ImageDraw.Draw(out)
    d.rectangle([0, 0, W, BAR], fill=(30, 40, 55))
    d.text((24, 17), cap, font=font, fill=(255, 255, 255))
    d.text((W - 330, H - 32), "Cereal-box dry lid - spool change", font=small, fill=(120, 120, 120))
    out.save(os.path.join(DST, "f_%04d.png" % i))
mp4 = os.path.join(HERE, "renders", OUTNAME + ".mp4")
subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-framerate", "15", "-i", os.path.join(DST, "f_%04d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", mp4], check=True)
gif = os.path.join(HERE, "renders", OUTNAME + ".gif")
subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-framerate", "15", "-i", os.path.join(DST, "f_%04d.png"),
                "-vf", "fps=12,scale=800:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse", gif], check=True)
print("crop", box, "| frames", len(frames), "|", mp4, os.path.getsize(mp4) // 1024, "KB |", gif, os.path.getsize(gif) // 1024, "KB")
