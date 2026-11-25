import subprocess, glob, os
from PIL import Image, ImageDraw

targets = [
    ("ZcmcHeWWAuI", 0.0, 3.6, 5.0),
    ("hRjZf_sg9GQ", 0.0, 3.6, 5.0),
    ("BU64zlrW1Ik", 0.0, 2.8, 6.0),
    ("L3HeXpHpxaY", 0.0, 10.8, 4.0),
    ("NyOTPC5aQog", 0.0, 3.2, 6.0),
]

for vid, t0, dur, fps in targets:
    d = f"references/text_motion_study/burst_{vid}"
    os.makedirs(d, exist_ok=True)
    for old in glob.glob(f"{d}/*.jpg"):
        os.remove(old)
    subprocess.run([
        "bin/ffmpeg.exe", "-y", "-ss", str(t0), "-t", str(dur),
        "-i", f"references/text_motion_study/{vid}.mp4",
        "-vf", f"fps={fps},scale=420:-1",
        f"{d}/b_%03d.jpg"
    ], capture_output=True)
    files = sorted(glob.glob(f"{d}/*.jpg"))[:18]
    if files:
        imgs = [Image.open(f) for f in files]
        w, h = imgs[0].size
        cols = 6
        rows = (len(imgs) + cols - 1) // cols
        sheet = Image.new("RGB", (cols*w, rows*h), (10,10,10))
        draw = ImageDraw.Draw(sheet)
        for i, im in enumerate(imgs):
            cx, cy = (i%cols)*w, (i//cols)*h
            sheet.paste(im, (cx, cy))
            draw.rectangle([cx+4, cy+4, cx+108, cy+28], fill=(0,0,0))
            draw.text((cx+8, cy+8), f"f{i+1} {(t0 + i/fps):.2f}s", fill=(100,255,150))
        out = f"references/text_motion_study/burst_{vid}.jpg"
        sheet.save(out, quality=92)
        print("Saved", out, len(imgs))
